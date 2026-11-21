"""Asking the models about one page: the requests, the runs and their errors.

Each request carries one page image and no PDF: one text part about the page, the
upright page image, and a cache point after them, so retries read both from the
provider's prompt cache. Anthropic requests also cache the instructions, which are the
same for every page of a run; OpenAI caches such prefixes itself.
"""

# Standard Library
from collections.abc import Mapping
from dataclasses import dataclass

# Third Party Library
from pydantic_ai import Agent, AgentRunResult
from pydantic_ai.exceptions import (
    ContentFilterError,
    OutputTokenLimitExceeded,
    UnexpectedModelBehavior,
)
from pydantic_ai.messages import BinaryContent, CachePoint, UserContent
from pydantic_ai.models.anthropic import AnthropicModelSettings
from pydantic_ai.settings import ModelSettings

# Package Library
from pydelity.config.schemas import ExtractionConfig
from pydelity.errors import ExtractionError
from pydelity.extracting.agents import create_extraction_agent, create_verifier_agent
from pydelity.extracting.prompts import extract_page, verify_page
from pydelity.extracting.rendering import UprightImage
from pydelity.extracting.schemas import PageAnswer, PageContext, VerifierVerdict
from pydelity.extracting.text_layer import PageText
from pydelity.extracting.validators import run_checks
from pydelity.providers.ledger_model import LedgerModel
from pydelity.providers.profiles import ModelChoice
from pydelity.review import CheckFailure, ExtractionCheckName

# The name of each of page extraction's agents, in the ledger and in errors.
EXTRACTOR = "extractor"
VERIFIER = "verifier"


def _content(*, choice: ModelChoice, page: "PageInput", text: str) -> list[UserContent]:
    """Put together a request's content: the page text, the image, a cache point.

    Parameters
    ----------
    choice
        The step's model, whose provider decides the image's detail value.
    page
        The page, for its upright image.
    text
        The text about the page.

    Returns
    -------
    list[UserContent]
        The text, the image (with the provider's detail value, if it takes one) and
        a cache point.
    """

    detail = choice.profile.image_detail
    picture = BinaryContent(
        data=page.image.data,
        media_type="image/jpeg",
        vendor_metadata=None if detail is None else {"detail": detail},
    )
    return [text, picture, CachePoint()]


def _model_settings(choice: ModelChoice) -> ModelSettings | None:
    """Return the request settings that cache the instructions, where needed.

    Parameters
    ----------
    choice
        The step's model.

    Returns
    -------
    ModelSettings | None
        Anthropic's instruction caching for Anthropic models; ``None`` for OpenAI,
        which caches such prefixes itself.
    """

    if choice.provider != "anthropic":
        return None
    settings: AnthropicModelSettings = {"anthropic_cache_instructions": True}
    return settings


async def _run[OutputT](
    agent: Agent[None, OutputT],
    *,
    agent_name: str,
    content: list[UserContent],
    model: "StepModel",
    page: "PageInput",
) -> AgentRunResult[OutputT]:
    """Run an agent once, turning a failed answer into an `ExtractionError`.

    Parameters
    ----------
    agent
        The extraction agent or the verifier.
    agent_name
        `EXTRACTOR` or `VERIFIER`, for the error message.
    content
        The request's content.
    model
        The step's model and settings.
    page
        The page, for the error message.

    Returns
    -------
    AgentRunResult[OutputT]
        The run's result, whose output is the accepted answer.

    Raises
    ------
    ExtractionError
        If the model refuses, runs out of output tokens, or never gives an answer
        that matches the answer format. The message names the page and the agent.
    ProviderError
        If a request fails after the provider retries.
    """

    index = page.context.page_index
    where = f"Page {index + 1} (index {index}), {agent_name}"
    try:
        return await agent.run(content, model_settings=_model_settings(model.choice))
    except ContentFilterError as error:
        raise ExtractionError(f"{where}: the model refused. {error.message}") from error
    except OutputTokenLimitExceeded as error:
        raise ExtractionError(
            f"{where}: the model used all {model.settings.max_output_tokens:,} output "
            "tokens before finishing its answer. Raise "
            "advanced.extraction.max_output_tokens, or lower "
            "advanced.extraction.effort."
        ) from error
    except UnexpectedModelBehavior as error:
        raise ExtractionError(
            f"{where}: the model gave no usable answer: {error.message}"
        ) from error


@dataclass(frozen=True)
class ModelPage:
    """The extraction model's kept answer for a page, and how it was obtained.

    Attributes
    ----------
    answer
        The kept answer.
    attempts
        How many answers the model gave: 1 plus the retries used.
    failures
        Each check's failures on the kept answer, in the order the checks run.
    """

    answer: PageAnswer
    attempts: int
    failures: dict[ExtractionCheckName, list[CheckFailure]]


@dataclass(frozen=True)
class ModelVerdict:
    """The verifier's verdict on a page's extraction, and how it was obtained.

    Attributes
    ----------
    attempts
        How many verdicts the verifier gave: 1 plus the retries used.
    correction_failures
        Each check's failures on the verdict's correction, or ``None`` when it has
        no correction.
    verdict
        The verdict as the verifier gave it.
    """

    attempts: int
    correction_failures: dict[ExtractionCheckName, list[CheckFailure]] | None
    verdict: VerifierVerdict


@dataclass(frozen=True)
class PageInput:
    """What the models are given about one page.

    Attributes
    ----------
    context
        The page's context.
    image
        The upright page image.
    page_text
        The page's text layer.
    """

    context: PageContext
    image: UprightImage
    page_text: PageText


@dataclass(frozen=True)
class StepModel:
    """Page extraction's model and settings, shared by every page of a run.

    Attributes
    ----------
    choice
        The model setting, split into its provider and model ID.
    model
        The model from `pydelity.providers.factory.build_model`; each page and agent
        gets its own ledger wrapper of it.
    settings
        Page extraction's settings.
    """

    choice: ModelChoice
    model: LedgerModel
    settings: ExtractionConfig


async def ask_extractor(*, model: StepModel, page: PageInput) -> ModelPage:
    """Ask the extraction model to read a page, with the checks enforced.

    Parameters
    ----------
    model
        The step's model and settings; requests are recorded for this page and the
        extractor.
    page
        The page.

    Returns
    -------
    ModelPage
        The kept answer, the number of answers and the checks it still fails.

    Raises
    ------
    ExtractionError
        If the model refuses, runs out of output tokens, or never gives an answer
        that matches the answer format.
    ProviderError
        If a request fails after the provider retries.
    """

    context, page_text = page.context, page.page_text
    prompts = extract_page(context)
    agent = create_extraction_agent(
        check_retries=model.settings.check_retries,
        context=context,
        instructions=prompts.system_message,
        model=model.model.for_page(agent=EXTRACTOR, page_index=context.page_index),
        page_text=page_text,
    )
    result = await _run(
        agent,
        agent_name=EXTRACTOR,
        content=_content(choice=model.choice, page=page, text=prompts.user_message),
        model=model,
        page=page,
    )
    return ModelPage(
        answer=result.output,
        attempts=result.usage.requests,
        failures=run_checks(result.output, context, page_text),
    )


async def ask_verifier(
    *,
    answer: PageAnswer,
    failures: Mapping[ExtractionCheckName, list[CheckFailure]],
    model: StepModel,
    page: PageInput,
) -> ModelVerdict:
    """Ask the verifier to review a page's extraction, with the checks enforced.

    Parameters
    ----------
    answer
        The extraction model's kept answer.
    failures
        The checks the answer still fails.
    model
        The step's model and settings; requests are recorded for this page and the
        verifier.
    page
        The page.

    Returns
    -------
    ModelVerdict
        The verdict, the number of verdicts and the checks its correction fails.

    Raises
    ------
    ExtractionError
        If the verifier refuses, runs out of output tokens, or never gives a verdict
        that matches the verdict format.
    ProviderError
        If a request fails after the provider retries.
    """

    context, page_text = page.context, page.page_text
    prompts = verify_page(context, answer=answer, failures=failures)
    agent = create_verifier_agent(
        check_retries=model.settings.check_retries,
        context=context,
        instructions=prompts.system_message,
        model=model.model.for_page(agent=VERIFIER, page_index=context.page_index),
        page_text=page_text,
    )
    result = await _run(
        agent,
        agent_name=VERIFIER,
        content=_content(choice=model.choice, page=page, text=prompts.user_message),
        model=model,
        page=page,
    )
    verdict = result.output
    correction_failures = (
        None
        if verdict.corrected is None
        else run_checks(verdict.corrected, context, page_text)
    )
    return ModelVerdict(
        attempts=result.usage.requests,
        correction_failures=correction_failures,
        verdict=verdict,
    )

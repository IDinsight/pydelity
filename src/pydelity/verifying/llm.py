"""Asking the models about one break: the requests, the runs and their errors.

Each request carries the two pages of the break and no PDF: a text part about the
page before the break, its upright image, a text part about the page after it, its
upright image, and a cache point after them, so retries and the verifier's request
read all of it from the provider's prompt cache. The judge and the verifier send the
same request, so the verifier judges the break without seeing the judge's verdict.
Anthropic requests also cache the instructions, which are the same for every break
of a run. OpenAI caches such prefixes itself.
"""

# Standard Library
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
from pydelity.config.schemas import PageBreaksConfig
from pydelity.errors import PageBreakError
from pydelity.extracting.rendering import UprightImage
from pydelity.extracting.schemas import PageFile
from pydelity.providers.ledger_model import LedgerModel
from pydelity.providers.profiles import ModelChoice
from pydelity.review import BreakCheckName, CheckFailure
from pydelity.verifying.agents import create_break_agent
from pydelity.verifying.prompts import BreakPrompts, judge_break
from pydelity.verifying.schemas import BreakContext, BreakVerdict
from pydelity.verifying.validators import run_checks

# The name of each of page-break verification's agents, in the ledger and in errors.
JUDGE = "judge"
VERIFIER = "verifier"


def _content(
    *, choice: ModelChoice, prompts: BreakPrompts, request: "BreakInput"
) -> list[UserContent]:
    """Put together a request's content: both pages' texts and images, a cache point.

    Parameters
    ----------
    choice
        The step's model, whose provider decides the images' detail value.
    prompts
        The request's prompts, for its text parts.
    request
        The break, for its two upright images.

    Returns
    -------
    list[UserContent]
        The earlier page's text and image, the later page's text and image, and a
        cache point. Each image carries the provider's detail value, if it takes
        one.
    """

    detail = choice.profile.image_detail
    metadata = None if detail is None else {"detail": detail}
    return [
        prompts.earlier_text,
        BinaryContent(
            data=request.earlier_image.data,
            media_type="image/jpeg",
            vendor_metadata=metadata,
        ),
        prompts.later_text,
        BinaryContent(
            data=request.later_image.data,
            media_type="image/jpeg",
            vendor_metadata=metadata,
        ),
        CachePoint(),
    ]


def _model_settings(choice: ModelChoice) -> ModelSettings | None:
    """Return the request settings that cache the instructions, where needed.

    Parameters
    ----------
    choice
        The step's model.

    Returns
    -------
    ModelSettings | None
        Anthropic's instruction caching for Anthropic models, and ``None`` for
        OpenAI, which caches such prefixes itself.
    """

    if choice.provider != "anthropic":
        return None
    settings: AnthropicModelSettings = {"anthropic_cache_instructions": True}
    return settings


async def _run(
    agent: Agent[None, BreakVerdict],
    *,
    agent_name: str,
    content: list[UserContent],
    model: "StepModel",
    request: "BreakInput",
) -> AgentRunResult[BreakVerdict]:
    """Run an agent once, turning a failed answer into a `PageBreakError`.

    Parameters
    ----------
    agent
        The judge's or the verifier's agent.
    agent_name
        `JUDGE` or `VERIFIER`, for the error message.
    content
        The request's content.
    model
        The step's model and settings.
    request
        The break, for the error message.

    Returns
    -------
    AgentRunResult[BreakVerdict]
        The run's result, whose output is the accepted verdict.

    Raises
    ------
    PageBreakError
        If the model refuses, runs out of output tokens, or never gives an answer
        that matches the answer format. The message names the break and the agent.
    ProviderError
        If a request fails after the provider retries.
    """

    number = request.earlier.page_index + 1
    where = f"Break after page {number} (pages {number} and {number + 1}), {agent_name}"
    try:
        return await agent.run(content, model_settings=_model_settings(model.choice))
    except ContentFilterError as error:
        raise PageBreakError(f"{where}: the model refused. {error.message}") from error
    except OutputTokenLimitExceeded as error:
        raise PageBreakError(
            f"{where}: the model used all {model.settings.max_output_tokens:,} output "
            "tokens before finishing its answer. Raise "
            "advanced.page_breaks.max_output_tokens, or lower "
            "advanced.page_breaks.effort."
        ) from error
    except UnexpectedModelBehavior as error:
        raise PageBreakError(
            f"{where}: the model gave no usable answer: {error.message}"
        ) from error


@dataclass(frozen=True)
class BreakAnswer:
    """A model's accepted verdict on a break, as the judge or the verifier.

    Attributes
    ----------
    attempts
        How many verdicts the model gave: 1 plus the retries used.
    failures
        Each check's failures on the accepted verdict, in the order the checks run.
    verdict
        The accepted verdict.
    """

    attempts: int
    failures: dict[BreakCheckName, list[CheckFailure]]
    verdict: BreakVerdict


@dataclass(frozen=True)
class BreakInput:
    """What the models are given about one break.

    Attributes
    ----------
    context
        The break's context.
    earlier
        The page file of the page before the break.
    earlier_image
        The upright image of the page before the break.
    later
        The page file of the page after the break.
    later_image
        The upright image of the page after the break.
    """

    context: BreakContext
    earlier: PageFile
    earlier_image: UprightImage
    later: PageFile
    later_image: UprightImage


@dataclass(frozen=True)
class StepModel:
    """Page-break verification's model and settings, shared by every break of a run.

    Attributes
    ----------
    choice
        The model setting, split into its provider and model ID.
    model
        The model from `pydelity.providers.factory.build_model`. Each break and
        agent gets its own ledger wrapper of it.
    settings
        Page-break verification's settings.
    verify
        Whether the verifier judges each break a second time.
    """

    choice: ModelChoice
    model: LedgerModel
    settings: PageBreaksConfig
    verify: bool


async def ask_model(
    *, agent: str, model: StepModel, request: BreakInput
) -> BreakAnswer:
    """Ask the model for a verdict on a break, as one agent, with the checks enforced.

    The judge and the verifier send the same request, built from the break alone, so
    the verifier never sees the judge's verdict.

    Parameters
    ----------
    agent
        `JUDGE` or `VERIFIER`. Requests are recorded for the break's earlier page
        and this agent, and errors name it.
    model
        The step's model and settings.
    request
        The break.

    Returns
    -------
    BreakAnswer
        The accepted verdict, the number of verdicts and the checks it still fails.

    Raises
    ------
    PageBreakError
        If the model refuses, runs out of output tokens, or never gives a verdict
        that matches the verdict format.
    ProviderError
        If a request fails after the provider retries.
    """

    earlier, later = request.earlier, request.later
    prompts = judge_break(request.context, earlier=earlier, later=later)
    created = create_break_agent(
        agent=agent,
        check_retries=model.settings.check_retries,
        earlier=earlier,
        instructions=prompts.system_message,
        later=later,
        model=model.model.for_page(agent=agent, page_index=earlier.page_index),
    )
    result = await _run(
        created,
        agent_name=agent,
        content=_content(choice=model.choice, prompts=prompts, request=request),
        model=model,
        request=request,
    )
    return BreakAnswer(
        attempts=result.usage.requests,
        failures=run_checks(result.output, earlier, later),
        verdict=result.output,
    )

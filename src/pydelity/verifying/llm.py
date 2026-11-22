"""Asking the models about one break: the requests, the runs and their errors.

Each request carries the two pages of the break and no PDF: a text part about the
page before the break, its upright image, a text part about the page after it, its
upright image, for the verifier a text part with the verdict to review, and a cache
point after them, so retries read all of it from the provider's prompt cache.
Anthropic requests also cache the instructions, which are the same for every break
of a run. OpenAI caches such prefixes itself.
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
from pydelity.config.schemas import PageBreaksConfig
from pydelity.errors import PageBreakError
from pydelity.extracting.rendering import UprightImage
from pydelity.extracting.schemas import PageFile
from pydelity.providers.ledger_model import LedgerModel
from pydelity.providers.profiles import ModelChoice
from pydelity.review import BreakCheckName, BreakHintName, CheckFailure
from pydelity.verifying.agents import create_judge_agent, create_verifier_agent
from pydelity.verifying.prompts import BreakPrompts, judge_break, verify_break
from pydelity.verifying.schemas import BreakContext, BreakVerdict, BreakVerifierVerdict
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
        The earlier page's text and image, the later page's text and image, the
        review text when there is one, and a cache point. Each image carries the
        provider's detail value, if it takes one.
    """

    detail = choice.profile.image_detail
    metadata = None if detail is None else {"detail": detail}
    content: list[UserContent] = [
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
    ]
    if prompts.review_text is not None:
        content.append(prompts.review_text)
    content.append(CachePoint())
    return content


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


async def _run[OutputT](
    agent: Agent[None, OutputT],
    *,
    agent_name: str,
    content: list[UserContent],
    model: "StepModel",
    request: "BreakInput",
) -> AgentRunResult[OutputT]:
    """Run an agent once, turning a failed answer into a `PageBreakError`.

    Parameters
    ----------
    agent
        The judge or the verifier.
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
    AgentRunResult[OutputT]
        The run's result, whose output is the accepted answer.

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
class JudgeAnswer:
    """The judge's kept verdict on a break, and how it was obtained.

    Attributes
    ----------
    attempts
        How many verdicts the judge gave: 1 plus the retries used.
    failures
        Each check's failures on the kept verdict, in the order the checks run.
    verdict
        The kept verdict.
    """

    attempts: int
    failures: dict[BreakCheckName, list[CheckFailure]]
    verdict: BreakVerdict


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
        Whether the verifier reviews each break's verdict.
    """

    choice: ModelChoice
    model: LedgerModel
    settings: PageBreaksConfig
    verify: bool


@dataclass(frozen=True)
class VerifierAnswer:
    """The verifier's answer on a break's verdict, and how it was obtained.

    Attributes
    ----------
    attempts
        How many answers the verifier gave: 1 plus the retries used.
    correction_failures
        Each check's failures on the answer's corrected verdict, or ``None`` when it
        has no correction.
    review
        The answer as the verifier gave it.
    """

    attempts: int
    correction_failures: dict[BreakCheckName, list[CheckFailure]] | None
    review: BreakVerifierVerdict


async def ask_judge(*, model: StepModel, request: BreakInput) -> JudgeAnswer:
    """Ask the judge for a verdict on a break, with the checks enforced.

    Parameters
    ----------
    model
        The step's model and settings. Requests are recorded for the break's
        earlier page and the judge.
    request
        The break.

    Returns
    -------
    JudgeAnswer
        The kept verdict, the number of verdicts and the checks it still fails.

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
    agent = create_judge_agent(
        check_retries=model.settings.check_retries,
        earlier=earlier,
        instructions=prompts.system_message,
        later=later,
        model=model.model.for_page(agent=JUDGE, page_index=earlier.page_index),
    )
    result = await _run(
        agent,
        agent_name=JUDGE,
        content=_content(choice=model.choice, prompts=prompts, request=request),
        model=model,
        request=request,
    )
    return JudgeAnswer(
        attempts=result.usage.requests,
        failures=run_checks(result.output, earlier, later),
        verdict=result.output,
    )


async def ask_verifier(
    *,
    differences: Mapping[BreakHintName, list[CheckFailure]],
    failures: Mapping[BreakCheckName, list[CheckFailure]],
    model: StepModel,
    request: BreakInput,
    verdict: BreakVerdict,
) -> VerifierAnswer:
    """Ask the verifier to review a break's verdict, with the checks enforced.

    The verifier's correction is checked, and sent back while retries remain when it
    fails a check. Its hint differences never send it back.

    Parameters
    ----------
    differences
        The verdict's differences from the hints.
    failures
        The checks the verdict still fails.
    model
        The step's model and settings. Requests are recorded for the break's
        earlier page and the verifier.
    request
        The break.
    verdict
        The judge's kept verdict.

    Returns
    -------
    VerifierAnswer
        The verifier's answer, the number of answers and the checks its correction
        fails.

    Raises
    ------
    PageBreakError
        If the verifier refuses, runs out of output tokens, or never gives an answer
        that matches the answer format.
    ProviderError
        If a request fails after the provider retries.
    """

    context, earlier, later = request.context, request.earlier, request.later
    prompts = verify_break(
        context,
        differences=differences,
        failures=failures,
        judged=judge_break(context, earlier=earlier, later=later),
        verdict=verdict,
    )
    agent = create_verifier_agent(
        check_retries=model.settings.check_retries,
        earlier=earlier,
        instructions=prompts.system_message,
        later=later,
        model=model.model.for_page(agent=VERIFIER, page_index=earlier.page_index),
    )
    result = await _run(
        agent,
        agent_name=VERIFIER,
        content=_content(choice=model.choice, prompts=prompts, request=request),
        model=model,
        request=request,
    )
    review = result.output
    correction_failures = (
        None
        if review.corrected is None
        else run_checks(review.corrected, earlier, later)
    )
    return VerifierAnswer(
        attempts=result.usage.requests,
        correction_failures=correction_failures,
        review=review,
    )

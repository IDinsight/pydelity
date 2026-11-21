"""Asking the models to survey a PDF and to review the survey, and their errors.

Each request carries the PDF, the text sent with it and a cache point after them. The
verifier's requests carry the PDF as the survey's last request did, so they make no
upload of their own unless the provider no longer has the file.
"""

# Standard Library
from collections.abc import Callable
from dataclasses import dataclass

# Third Party Library
from pydantic_ai import Agent, AgentRunResult
from pydantic_ai.exceptions import (
    ContentFilterError,
    OutputTokenLimitExceeded,
    UnexpectedModelBehavior,
)
from pydantic_ai.messages import CachePoint, UserContent

# Package Library
from pydelity.config.schemas import Config
from pydelity.errors import ProviderError, SurveyError
from pydelity.providers.ledger_model import LedgerModel
from pydelity.providers.profiles import PdfTransport
from pydelity.providers.uploads import (
    PdfAttachment,
    attach_pdf,
    is_missing_file,
    replace_missing_upload,
    with_upload_error,
)
from pydelity.review import CheckFailure, SurveyCheckName
from pydelity.surveying.agents import create_survey_agent, create_verifier_agent
from pydelity.surveying.prompts import survey_pdf, verify_survey
from pydelity.surveying.schemas import PdfFacts, SurveyAnswer, SurveyVerdict
from pydelity.surveying.validators import compare_with_facts, run_checks
from pydelity.utils.pdf import PdfInfo
from pydelity.utils.prompts import PromptPair

# The name of each of the survey's agents, in the ledger and in errors.
SURVEYOR = "surveyor"
VERIFIER = "verifier"


async def _run_agent[OutputT](
    *,
    agent: Agent[None, OutputT],
    agent_name: str,
    attachment: PdfAttachment,
    config: Config,
    prompts: PromptPair,
) -> AgentRunResult[OutputT]:
    """Run an agent once, with the PDF, the text and a cache point after them.

    Parameters
    ----------
    agent
        The survey agent or the verifier.
    agent_name
        `SURVEYOR` or `VERIFIER`, for the error message.
    attachment
        How the request carries the PDF.
    config
        The run's settings, for the output token limit.
    prompts
        The agent's messages.

    Returns
    -------
    AgentRunResult[OutputT]
        The run's result, whose output is the accepted answer.

    Raises
    ------
    ProviderError
        If a request fails after the provider retries. After a fallback to sending
        the PDF in the request, the error also gives the upload error.
    SurveyError
        If the model refuses, runs out of output tokens, or never gives an answer that
        matches the agent's answer format. The message names the verifier for the
        verifier's requests.
    """

    if agent_name == VERIFIER:
        who, task, answer = "The verifier", "review the survey", "verdict on the survey"
    else:
        who, task, answer = "The model", "survey the PDF", "survey answer"
    # The cache point makes Anthropic cache the instructions, the PDF and the text, so
    # each retry reads them from the cache.
    content: list[UserContent] = [
        attachment.content,
        prompts.user_message,
        CachePoint(),
    ]
    try:
        return await agent.run(content)
    except ProviderError as error:
        if attachment.upload_error is None:
            raise
        raise with_upload_error(error, attachment.upload_error) from error.__cause__
    except ContentFilterError as error:
        raise SurveyError(f"{who} refused to {task}. {error.message}") from error
    except OutputTokenLimitExceeded as error:
        raise SurveyError(
            f"{who} used all "
            f"{config.advanced.survey.max_output_tokens:,} output tokens before "
            "finishing its answer. Raise advanced.survey.max_output_tokens, or lower "
            "advanced.survey.effort."
        ) from error
    except UnexpectedModelBehavior as error:
        raise SurveyError(f"{who} gave no usable {answer}: {error.message}") from error


async def _run_with_upload[OutputT](
    *,
    agent: Agent[None, OutputT],
    agent_name: str,
    attachment: PdfAttachment,
    prompts: PromptPair,
    step: "SurveyStep",
) -> tuple[AgentRunResult[OutputT], PdfAttachment]:
    """Run an agent once, and again after a new upload if the provider lost the PDF.

    Parameters
    ----------
    agent
        The survey agent or the verifier.
    agent_name
        `SURVEYOR` or `VERIFIER`, for the error message.
    attachment
        How the requests carry the PDF.
    prompts
        The agent's messages.
    step
        The survey's settings, model and PDF.

    Returns
    -------
    tuple[AgentRunResult[OutputT], PdfAttachment]
        The run's result, and how its last request carried the PDF.

    Raises
    ------
    ProviderError
        If the provider rejects the new upload for an invalid API key or as too
        large, or a request fails after the provider retries.
    SurveyError
        If the model refuses, runs out of output tokens, or never gives an answer that
        matches the agent's answer format.
    """

    try:
        result = await _run_agent(
            agent=agent,
            agent_name=agent_name,
            attachment=attachment,
            config=step.config,
            prompts=prompts,
        )
    except ProviderError as error:
        if not is_missing_file(error, attachment):
            raise
        attachment = await replace_missing_upload(
            attachment=attachment,
            config=step.config,
            model=step.model,
            output_folder=step.config.output_folder,
            pdf=step.pdf,
        )
        step.on_attached(attachment.transport)
        result = await _run_agent(
            agent=agent,
            agent_name=agent_name,
            attachment=attachment,
            config=step.config,
            prompts=prompts,
        )
    return result, attachment


@dataclass(frozen=True)
class ModelSurvey:
    """The model's accepted survey answer and how it was obtained.

    Attributes
    ----------
    answer
        The accepted answer.
    attachment
        How the last request carried the PDF.
    attempts
        How many answers the model gave: 1 plus the retries used.
    prompts
        The survey's messages, whose user message the verifier's request repeats.
    """

    answer: SurveyAnswer
    attachment: PdfAttachment
    attempts: int
    prompts: PromptPair


@dataclass(frozen=True)
class ModelVerdict:
    """The verifier's verdict on the survey, and how it was obtained.

    Attributes
    ----------
    attachment
        How the verifier's last request carried the PDF.
    attempts
        How many verdicts the verifier gave: 1 plus the retries used.
    correction_failures
        Each check's failures on the verdict's correction, C1 to C7 in order, or
        ``None`` when it has no correction.
    verdict
        The verdict as the verifier gave it.
    """

    attachment: PdfAttachment
    attempts: int
    correction_failures: dict[SurveyCheckName, list[CheckFailure]] | None
    verdict: SurveyVerdict


@dataclass(frozen=True)
class SurveyStep:
    """What every request of one survey needs: the settings, facts, model and PDF.

    Attributes
    ----------
    config
        The run's settings.
    facts
        The measured facts, sent as a summary and used by the checks.
    model
        The step's model; each agent's requests go through its own ledger wrapper of
        it.
    on_attached
        Called with how requests will carry the PDF, each time the PDF is attached,
        before any request with it is sent, so a failed survey can still say how it
        sent the PDF.
    pdf
        The PDF.
    """

    config: Config
    facts: PdfFacts
    model: LedgerModel
    on_attached: Callable[[PdfTransport], None]
    pdf: PdfInfo


async def ask_model(step: SurveyStep) -> ModelSurvey:
    """Attach the PDF and ask the model to survey it.

    The PDF's upload is reused or made, or the PDF goes inside each request when the
    upload fails. If the provider answers that it no longer has the uploaded file, the
    PDF is uploaded again once and the survey starts over.

    Parameters
    ----------
    step
        The survey's settings, facts, model and PDF; requests are recorded for the
        surveyor.

    Returns
    -------
    ModelSurvey
        The accepted answer, the attachment, the number of answers and the survey's
        messages.

    Raises
    ------
    ProviderError
        If the provider rejects the upload for an invalid API key or as too large, or
        a request fails after the provider retries.
    SurveyError
        If the model refuses, runs out of output tokens, or never gives an answer that
        matches the survey's answer format.
    """

    config, facts, pdf = step.config, step.facts, step.pdf
    prompts = survey_pdf(
        facts_summary=facts.summary,
        instructions=config.advanced.survey.instructions,
        languages=config.languages,
        page_count=pdf.page_count,
        repeated_lines=facts.facts.repeated_lines,
    )
    agent = create_survey_agent(
        check_retries=config.advanced.survey.check_retries,
        facts=facts.facts,
        instructions=prompts.system_message,
        model=step.model.for_agent(agent=SURVEYOR),
    )
    attachment = await attach_pdf(
        config=config, model=step.model, output_folder=config.output_folder, pdf=pdf
    )
    step.on_attached(attachment.transport)
    result, attachment = await _run_with_upload(
        agent=agent,
        agent_name=SURVEYOR,
        attachment=attachment,
        prompts=prompts,
        step=step,
    )
    return ModelSurvey(
        answer=result.output,
        attachment=attachment,
        attempts=result.usage.requests,
        prompts=prompts,
    )


async def ask_verifier(step: SurveyStep, *, surveyed: ModelSurvey) -> ModelVerdict:
    """Ask the verifier to review the survey's answer, with the checks enforced.

    The requests carry the PDF as the survey's last request did, so no new upload is
    made. If the provider answers that it no longer has the uploaded file, the PDF is
    uploaded again once and the review starts over.

    Parameters
    ----------
    step
        The survey's settings, facts, model and PDF; requests are recorded for the
        verifier.
    surveyed
        The survey's accepted answer, its attachment and its messages.

    Returns
    -------
    ModelVerdict
        The verdict, the attachment, the number of verdicts and the checks its
        correction fails.

    Raises
    ------
    ProviderError
        If the provider rejects a new upload for an invalid API key or as too large,
        or a request fails after the provider retries.
    SurveyError
        If the verifier refuses, runs out of output tokens, or never gives a verdict
        that matches the verdict format.
    """

    answer, facts = surveyed.answer, step.facts.facts
    prompts = verify_survey(
        answer=answer,
        differences=compare_with_facts(answer, facts),
        failures=run_checks(answer, facts),
        instructions=step.config.advanced.survey.instructions,
        survey_message=surveyed.prompts.user_message,
    )
    agent = create_verifier_agent(
        check_retries=step.config.advanced.survey.check_retries,
        facts=facts,
        instructions=prompts.system_message,
        model=step.model.for_agent(agent=VERIFIER),
    )
    result, attachment = await _run_with_upload(
        agent=agent,
        agent_name=VERIFIER,
        attachment=surveyed.attachment,
        prompts=prompts,
        step=step,
    )
    verdict = result.output
    correction_failures = (
        None if verdict.corrected is None else run_checks(verdict.corrected, facts)
    )
    return ModelVerdict(
        attachment=attachment,
        attempts=result.usage.requests,
        correction_failures=correction_failures,
        verdict=verdict,
    )

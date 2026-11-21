"""Asking the model to survey a PDF: the request, the run and its errors."""

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
from pydelity.surveying.agents import create_survey_agent
from pydelity.surveying.prompts import survey_pdf
from pydelity.surveying.schemas import PdfFacts, SurveyAnswer
from pydelity.utils.pdf import PdfInfo
from pydelity.utils.prompts import PromptPair

# The name of the survey's agent, in the ledger.
SURVEYOR = "surveyor"


async def _run_agent(
    *,
    agent: Agent[None, SurveyAnswer],
    attachment: PdfAttachment,
    config: Config,
    prompts: PromptPair,
) -> AgentRunResult[SurveyAnswer]:
    """Run the survey agent once, with the PDF, the text and a cache point after them.

    Parameters
    ----------
    agent
        The survey agent.
    attachment
        How the request carries the PDF.
    config
        The run's settings, for the output token limit.
    prompts
        The survey's messages.

    Returns
    -------
    AgentRunResult[SurveyAnswer]
        The run's result, whose output is the accepted answer.

    Raises
    ------
    ProviderError
        If a request fails after the provider retries. After a fallback to sending
        the PDF in the request, the error also gives the upload error.
    SurveyError
        If the model refuses, runs out of output tokens, or never gives an answer that
        matches the survey's answer format.
    """

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
        raise SurveyError(
            f"The model refused to survey the PDF. {error.message}"
        ) from error
    except OutputTokenLimitExceeded as error:
        raise SurveyError(
            "The model used all "
            f"{config.advanced.survey.max_output_tokens:,} output tokens before "
            "finishing its answer. Raise advanced.survey.max_output_tokens, or lower "
            "advanced.survey.effort."
        ) from error
    except UnexpectedModelBehavior as error:
        raise SurveyError(
            f"The model gave no usable survey answer: {error.message}"
        ) from error


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
    """

    answer: SurveyAnswer
    attachment: PdfAttachment
    attempts: int


async def ask_model(
    *,
    config: Config,
    facts: PdfFacts,
    model: LedgerModel,
    on_attached: Callable[[PdfTransport], None],
    pdf: PdfInfo,
) -> ModelSurvey:
    """Attach the PDF and ask the model to survey it.

    The PDF's upload is reused or made, or the PDF goes inside each request when the
    upload fails. If the provider answers that it no longer has the uploaded file, the
    PDF is uploaded again once and the survey starts over.

    Parameters
    ----------
    config
        The run's settings.
    facts
        The measured facts, sent as a summary and used by the checks.
    model
        The step's model; requests are recorded for the surveyor.
    on_attached
        Called with how requests will carry the PDF, each time the PDF is attached,
        before any request is sent, so a failed survey can still say how it sent the
        PDF.
    pdf
        The PDF.

    Returns
    -------
    ModelSurvey
        The accepted answer, the attachment and the number of answers.

    Raises
    ------
    ProviderError
        If the provider rejects the upload for an invalid API key or as too large, or
        a request fails after the provider retries.
    SurveyError
        If the model refuses, runs out of output tokens, or never gives an answer that
        matches the survey's answer format.
    """

    prompts = survey_pdf(
        facts_summary=facts.summary,
        instructions=config.advanced.survey.instructions,
        languages=config.languages,
        page_count=pdf.page_count,
        repeated_lines=facts.facts.repeated_lines,
    )
    survey_settings = config.advanced.survey
    agent = create_survey_agent(
        check_retries=survey_settings.check_retries,
        facts=facts.facts,
        instructions=prompts.system_message,
        model=model.for_agent(agent=SURVEYOR),
    )
    attachment = await attach_pdf(
        config=config, model=model, output_folder=config.output_folder, pdf=pdf
    )
    on_attached(attachment.transport)
    try:
        result = await _run_agent(
            agent=agent, attachment=attachment, config=config, prompts=prompts
        )
    except ProviderError as error:
        if not is_missing_file(error, attachment):
            raise
        attachment = await replace_missing_upload(
            attachment=attachment,
            config=config,
            model=model,
            output_folder=config.output_folder,
            pdf=pdf,
        )
        on_attached(attachment.transport)
        result = await _run_agent(
            agent=agent, attachment=attachment, config=config, prompts=prompts
        )

    return ModelSurvey(
        answer=result.output,
        attachment=attachment,
        attempts=result.usage.requests,
    )

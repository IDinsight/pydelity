"""Building the models that pydelity's steps send requests to.

`build_model` builds the provider's SDK client itself, with the run's retry count and
request timeout, so one setting governs every retry and pydelity adds none of its own.
It also closes the client when the step is done with the model. The SDKs read
``ANTHROPIC_BASE_URL`` and ``OPENAI_BASE_URL`` when set. Every model is wrapped in
`pydelity.providers.ledger_model.LedgerModel`.
"""

# Standard Library
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

# Third Party Library
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from pydantic_ai import NativeOutput, PromptedOutput
from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

# Package Library
from pydelity.config.loading import read_api_key
from pydelity.config.schemas import (
    Config,
    ExtractionConfig,
    PageBreaksConfig,
    SurveyConfig,
)
from pydelity.providers.ledger_model import LedgerContext, LedgerModel
from pydelity.providers.profiles import PROFILES, ModelChoice, OutputMode


def _provider_model(
    *,
    choice: ModelChoice,
    client: AsyncAnthropic | AsyncOpenAI,
    settings: ModelSettings,
) -> Model:
    """Build the provider's model on its SDK client.

    Parameters
    ----------
    choice
        The provider and model ID.
    client
        The provider's SDK client, from `_sdk_client`.
    settings
        The model's request settings.

    Returns
    -------
    Model
        The Anthropic model, or the OpenAI Responses model.
    """

    if isinstance(client, AsyncAnthropic):
        return AnthropicModel(
            choice.model_id,
            provider=AnthropicProvider(anthropic_client=client),
            settings=settings,
        )
    return OpenAIResponsesModel(
        choice.model_id,
        provider=OpenAIProvider(openai_client=client),
        settings=settings,
    )


def _sdk_client(
    *, choice: ModelChoice, config: Config, request_timeout_seconds: float
) -> AsyncAnthropic | AsyncOpenAI:
    """Build the provider's SDK client with the run's retry count and timeout.

    Parameters
    ----------
    choice
        The provider and model ID.
    config
        The run's settings, for the retry count.
    request_timeout_seconds
        How long one attempt at a request may take.

    Returns
    -------
    AsyncAnthropic | AsyncOpenAI
        The client. The caller closes it.

    Raises
    ------
    MissingApiKeyError
        If the provider's API key is not set.
    """

    api_key = read_api_key(choice.provider).get_secret_value()
    retries = config.advanced.provider_retries
    if choice.provider == "anthropic":
        return AsyncAnthropic(
            api_key=api_key, max_retries=retries, timeout=request_timeout_seconds
        )
    return AsyncOpenAI(
        api_key=api_key, max_retries=retries, timeout=request_timeout_seconds
    )


@asynccontextmanager
async def build_model(
    *,
    choice: ModelChoice,
    config: Config,
    context: LedgerContext,
    step_settings: ExtractionConfig | PageBreaksConfig | SurveyConfig,
) -> AsyncGenerator[LedgerModel]:
    """Build one step's model, wrapped to check and record requests.

    Use it in an ``async with`` block. The step uses one SDK client, which uploads
    use too, and which is closed when the block ends, also when it ends with an error
    or is canceled. PydanticAI closes only the clients it creates itself. A step that
    sends requests about single pages makes a wrapper for each page and agent with
    `LedgerModel.for_page`, on the same client.

    Parameters
    ----------
    choice
        The step's model.
    config
        The run's settings: the retry count and any price overrides.
    context
        The guard, ledger, PDF, run and step the requests belong to.
    step_settings
        The step's settings: its effort (Anthropic's adaptive-thinking effort, or
        OpenAI's reasoning effort), the most tokens one answer may contain, thinking
        included, and how long one attempt at a request may take.

    Yields
    ------
    LedgerModel
        The model, ready for a PydanticAI agent. No request has been sent.

    Raises
    ------
    MissingApiKeyError
        If the provider's API key is not set.

    Examples
    --------
    ::

        async with build_model(choice=config.survey_model, config=config,
                               context=context,
                               step_settings=config.advanced.survey) as model:
            survey, transport = await run_survey(model=model, ...)
    """

    settings = choice.profile.effort_settings(step_settings.effort)
    settings["max_tokens"] = step_settings.max_output_tokens
    client = _sdk_client(
        choice=choice,
        config=config,
        request_timeout_seconds=step_settings.request_timeout_seconds,
    )
    async with client:
        model = _provider_model(choice=choice, client=client, settings=settings)
        yield LedgerModel(model, choice=choice, config=config, context=context)


def output_mode(model: Model) -> OutputMode:
    """Return how a model gives structured output.

    Parameters
    ----------
    model
        The model.

    Returns
    -------
    OutputMode
        ``prompted`` when the provider's profile asks for it (Anthropic) or the model
        has no JSON-schema output, otherwise ``native``.
    """

    provider = PROFILES.get(model.system)
    if provider is not None and provider.output_mode == "prompted":
        return "prompted"
    return "native" if model.profile.get("supports_json_schema_output") else "prompted"


def structured_output[OutputT](
    model: Model, output_type: type[OutputT]
) -> NativeOutput[OutputT] | PromptedOutput[OutputT]:
    """Ask a model for structured output in its `output_mode`.

    Parameters
    ----------
    model
        The model.
    output_type
        The Pydantic model the answer must match.

    Returns
    -------
    NativeOutput[OutputT] | PromptedOutput[OutputT]
        The agent's ``output_type``.
    """

    if output_mode(model) == "native":
        return NativeOutput(output_type)
    return PromptedOutput(output_type)

"""Building the models that pydelity's steps send requests to.

`build_model` builds the provider's SDK client itself, with the run's retry count and
request timeout, so one setting governs every retry and pydelity adds none of its own.
The SDKs read ``ANTHROPIC_BASE_URL`` and ``OPENAI_BASE_URL`` when set. Every model is
wrapped in `pydelity.providers.ledger_model.LedgerModel`.
"""

# Standard Library
from typing import Literal

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
from pydelity.config.schemas import Config
from pydelity.providers.ledger_model import LedgerContext, LedgerModel
from pydelity.providers.profiles import Effort, ModelChoice

# How a model gives structured output: the provider's own structured output, or a
# schema in the prompt. Forced tool choice is never used, since some models reject it.
type OutputMode = Literal["native", "prompted"]


def _provider_model(
    *,
    choice: ModelChoice,
    config: Config,
    request_timeout_seconds: float,
    settings: ModelSettings,
) -> Model:
    """Build the provider's model with its SDK client.

    Parameters
    ----------
    choice
        The provider and model ID.
    config
        The run's settings, for the retry count.
    request_timeout_seconds
        How long one attempt at a request may take.
    settings
        The model's request settings.

    Returns
    -------
    Model
        The Anthropic model, or the OpenAI Responses model.

    Raises
    ------
    MissingApiKeyError
        If the provider's API key is not set.
    """

    api_key = read_api_key(choice.provider).get_secret_value()
    retries = config.advanced.provider_retries
    if choice.provider == "anthropic":
        anthropic_client = AsyncAnthropic(
            api_key=api_key, max_retries=retries, timeout=request_timeout_seconds
        )
        return AnthropicModel(
            choice.model_id,
            provider=AnthropicProvider(anthropic_client=anthropic_client),
            settings=settings,
        )
    openai_client = AsyncOpenAI(
        api_key=api_key, max_retries=retries, timeout=request_timeout_seconds
    )
    return OpenAIResponsesModel(
        choice.model_id,
        provider=OpenAIProvider(openai_client=openai_client),
        settings=settings,
    )


def build_model(
    *,
    config: Config,
    context: LedgerContext,
    effort: Effort,
    max_output_tokens: int,
    request_timeout_seconds: float,
) -> LedgerModel:
    """Build the selected model for one step, wrapped to check and record requests.

    Parameters
    ----------
    config
        The run's settings: the model, the retry count and any price overrides.
    context
        The guard, ledger, PDF, run and step the requests belong to.
    effort
        How hard the model thinks: Anthropic's adaptive-thinking effort, or OpenAI's
        reasoning effort.
    max_output_tokens
        The most tokens one answer may contain, thinking included.
    request_timeout_seconds
        How long one attempt at a request may take.

    Returns
    -------
    LedgerModel
        The model, ready for a PydanticAI agent. No request has been sent.

    Raises
    ------
    MissingApiKeyError
        If the provider's API key is not set.
    """

    choice = config.model_choice
    settings = choice.profile.effort_settings(effort)
    settings["max_tokens"] = max_output_tokens
    model = _provider_model(
        choice=choice,
        config=config,
        request_timeout_seconds=request_timeout_seconds,
        settings=settings,
    )
    return LedgerModel(model, config=config, context=context)


def output_mode(model: Model) -> OutputMode:
    """Return how a model gives structured output, from its PydanticAI profile.

    Parameters
    ----------
    model
        The model.

    Returns
    -------
    OutputMode
        ``native`` when the model supports the provider's structured output,
        otherwise ``prompted``.
    """

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

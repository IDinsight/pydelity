"""Provider profiles: the few provider-level facts pydelity needs, and model settings.

pydelity keeps no per-model data (no page, size or context-window limits and no list
of models), because none of it could be kept current. It keeps only facts that hold
for every model of a provider, and sends any model ID as given: the provider decides
whether the model exists and accepts the PDF and the settings.
"""

# Future Library
from __future__ import annotations

# Standard Library
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    # Standard Library
    from collections.abc import Callable

    # Third Party Library
    from pydantic_ai.models.anthropic import AnthropicModelSettings
    from pydantic_ai.models.openai import OpenAIResponsesModelSettings
    from pydantic_ai.settings import ModelSettings

# How hard the model thinks before answering.
type Effort = Literal["low", "medium", "high"]

# How a PDF reaches the provider: uploaded through its Files API, or sent inside the
# request itself.
type PdfTransport = Literal["upload", "request"]

# The providers pydelity supports.
type ProviderName = Literal["anthropic", "openai"]

# Estimated input tokens for one PDF page sent to Anthropic. Anthropic's PDF support
# page gives 1,500-3,000 text tokens per page, plus each page billed as an image; its
# vision page caps an image at 4,784 tokens on Claude 4.7 and later models. The
# estimate takes the top of both, so cost estimates err high.
_ANTHROPIC_PDF_IMAGE_TOKENS = 4_784
_ANTHROPIC_PDF_TEXT_TOKENS = 3_000

# Anthropic's Files API keeps an upload for 1 hour to 90 days (3,600 to 7,776,000
# seconds).
_ANTHROPIC_UPLOAD_EXPIRY_HOURS = (1, 2_160)

# Estimated input tokens for one PDF page sent to OpenAI, which reads both the page's
# extracted text and an image of the page. OpenAI gives no per-page figure, so the text
# share uses Anthropic's documented upper bound (the same page text), and the image
# share is OpenAI's high-detail cap of 2,500 patches times its 1.2 token multiplier.
_OPENAI_PDF_IMAGE_TOKENS = 3_000
_OPENAI_PDF_TEXT_TOKENS = 3_000

# OpenAI's Files API keeps an upload for 1 hour to 30 days (3,600 to 2,592,000 seconds)
# when given an expiry.
_OPENAI_UPLOAD_EXPIRY_HOURS = (1, 720)


def _anthropic_effort_settings(effort: Effort) -> ModelSettings:
    """Return the Anthropic request settings for an effort level.

    Anthropic models think adaptively, with the effort level setting how much.

    Parameters
    ----------
    effort
        pydelity's effort level.

    Returns
    -------
    ModelSettings
        PydanticAI model settings for Anthropic.
    """

    settings: AnthropicModelSettings = {
        "anthropic_effort": effort,
        "anthropic_thinking": {"type": "adaptive"},
    }
    return settings


def _openai_effort_settings(effort: Effort) -> ModelSettings:
    """Return the OpenAI request settings for an effort level.

    Parameters
    ----------
    effort
        pydelity's effort level, sent as OpenAI's reasoning effort.

    Returns
    -------
    ModelSettings
        PydanticAI model settings for the OpenAI Responses API.
    """

    settings: OpenAIResponsesModelSettings = {"openai_reasoning_effort": effort}
    return settings


@dataclass(frozen=True)
class ModelChoice:
    """A model setting split into its provider and model ID.

    Attributes
    ----------
    model_id
        The provider's model ID, sent as given.
    provider
        The provider the model belongs to.
    """

    model_id: str
    provider: ProviderName

    @property
    def profile(self) -> ProviderProfile:
        """The profile of the model's provider."""

        return PROFILES[self.provider]

    @property
    def setting(self) -> str:
        """The model setting, as ``<provider>:<model-id>``."""

        return f"{self.provider}:{self.model_id}"


@dataclass(frozen=True)
class ProviderProfile:
    """The facts pydelity needs about a provider, the same for all its models.

    Attributes
    ----------
    effort_settings
        Turns pydelity's effort level into the provider's request settings.
    max_upload_expiry_hours
        The longest upload expiry the provider allows, and pydelity's default.
    min_upload_expiry_hours
        The shortest upload expiry the provider allows.
    name
        The provider's name, as written in a model setting.
    pdf_image_tokens_per_page
        Estimated input tokens for the image of one PDF page.
    pdf_text_tokens_per_page
        Estimated input tokens for the text of one PDF page.
    pdf_transports
        How a PDF can reach the provider, in the order pydelity tries them.
    upload_purpose
        The purpose the provider's Files API needs for an uploaded PDF, if any.
    """

    effort_settings: Callable[[Effort], ModelSettings]
    max_upload_expiry_hours: int
    min_upload_expiry_hours: int
    name: ProviderName
    pdf_image_tokens_per_page: int
    pdf_text_tokens_per_page: int
    pdf_transports: tuple[PdfTransport, ...]
    upload_purpose: str | None

    @property
    def pdf_tokens_per_page(self) -> int:
        """Estimated input tokens for one PDF page: its text plus its image."""

        return self.pdf_image_tokens_per_page + self.pdf_text_tokens_per_page


# The model pydelity uses unless told otherwise.
DEFAULT_MODEL = "anthropic:claude-opus-5-5"

PROFILES: dict[ProviderName, ProviderProfile] = {
    "anthropic": ProviderProfile(
        effort_settings=_anthropic_effort_settings,
        max_upload_expiry_hours=_ANTHROPIC_UPLOAD_EXPIRY_HOURS[1],
        min_upload_expiry_hours=_ANTHROPIC_UPLOAD_EXPIRY_HOURS[0],
        name="anthropic",
        pdf_image_tokens_per_page=_ANTHROPIC_PDF_IMAGE_TOKENS,
        pdf_text_tokens_per_page=_ANTHROPIC_PDF_TEXT_TOKENS,
        pdf_transports=("upload", "request"),
        upload_purpose=None,
    ),
    "openai": ProviderProfile(
        effort_settings=_openai_effort_settings,
        max_upload_expiry_hours=_OPENAI_UPLOAD_EXPIRY_HOURS[1],
        min_upload_expiry_hours=_OPENAI_UPLOAD_EXPIRY_HOURS[0],
        name="openai",
        pdf_image_tokens_per_page=_OPENAI_PDF_IMAGE_TOKENS,
        pdf_text_tokens_per_page=_OPENAI_PDF_TEXT_TOKENS,
        pdf_transports=("upload", "request"),
        upload_purpose="user_data",
    ),
}


def parse_model(setting: str) -> ModelChoice:
    """Split a model setting into its provider and model ID.

    Parameters
    ----------
    setting
        The model setting, ``<provider>:<model-id>``, with provider ``anthropic`` or
        ``openai``. The model ID is sent to the provider as given.

    Returns
    -------
    ModelChoice
        The provider and the model ID.

    Raises
    ------
    ValueError
        If the setting has no ``:``, an empty provider or model ID, or a provider
        pydelity does not support. The configuration reports it as an invalid
        ``model`` setting.

    Examples
    --------
    >>> parse_model("openai:gpt-6.2-astra")
    ModelChoice(model_id='gpt-6.2-astra', provider='openai')
    """

    provider, separator, model_id = setting.partition(":")
    if not separator or not provider or not model_id:
        raise ValueError(
            f"{setting!r} is not <provider>:<model-id>, such as {DEFAULT_MODEL!r}"
        )
    if provider == "anthropic":
        return ModelChoice(model_id=model_id, provider="anthropic")
    if provider == "openai":
        return ModelChoice(model_id=model_id, provider="openai")

    supported = " or ".join(repr(name) for name in PROFILES)
    raise ValueError(f"provider {provider!r} is not supported; use {supported}")

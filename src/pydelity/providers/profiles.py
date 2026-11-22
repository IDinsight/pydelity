"""Provider profiles and model settings.

pydelity stores no per-model data, such as page, size or context-window limits or a
list of models, because it would go out of date. A profile holds only facts about a
provider, such as the largest image its current models read without shrinking it.
Model IDs are sent to the provider unchanged, and the provider decides whether the
model exists and accepts the PDF, the images and the settings.
"""

# Future Library
from __future__ import annotations

# Standard Library
import math

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    # Standard Library
    from collections.abc import Callable

    # Third Party Library
    from pydantic_ai.models.anthropic import AnthropicModelSettings
    from pydantic_ai.models.openai import OpenAIResponsesModelSettings
    from pydantic_ai.settings import ModelSettings

# Images Anthropic reads without shrinking them, on Claude 4.7 and later models: at most
# 2,576 px on the long edge and 4,784 patches of 28 x 28 px, each one input token
# (Anthropic's vision guide). Older models shrink larger images to their own limit.
_ANTHROPIC_IMAGE_MAX_LONG_EDGE_PX = 2_576
_ANTHROPIC_IMAGE_MAX_PATCHES = 4_784
_ANTHROPIC_IMAGE_PATCH_PX = 28

# Estimated input tokens for one PDF page sent to Anthropic. Anthropic's PDF support
# page gives 1,500-3,000 text tokens per page, plus each page billed as an image; its
# vision page caps an image at 4,784 tokens on Claude 4.7 and later models. The
# estimate takes the top of both, so cost estimates err high.
_ANTHROPIC_PDF_IMAGE_TOKENS = 4_784
_ANTHROPIC_PDF_TEXT_TOKENS = 3_000

# Anthropic's Files API keeps an upload for 1 hour to 90 days (3,600 to 7,776,000
# seconds).
_ANTHROPIC_UPLOAD_EXPIRY_HOURS = (1, 2_160)

# Images OpenAI reads at their own size with detail "original": at most 6,000 px on the
# long edge and 10,000 patches of 32 x 32 px on the GPT-5.4 and GPT-5.5 models, the
# lowest limits of the models that take "original" (OpenAI's images guide). Their image
# tokens are the patches times 1.2.
_OPENAI_IMAGE_DETAIL = "original"
_OPENAI_IMAGE_MAX_LONG_EDGE_PX = 6_000
_OPENAI_IMAGE_MAX_PATCHES = 10_000
_OPENAI_IMAGE_PATCH_PX = 32
_OPENAI_IMAGE_TOKENS_PER_PATCH = 1.2

# Estimated input tokens for one PDF page sent to OpenAI, which reads both the page's
# extracted text and an image of the page. OpenAI gives no per-page figure, so the text
# share uses Anthropic's documented upper bound (the same page text), and the image
# share is OpenAI's high-detail cap of 2,500 patches times its 1.2 token multiplier.
_OPENAI_PDF_IMAGE_TOKENS = 3_000
_OPENAI_PDF_TEXT_TOKENS = 3_000

# OpenAI's Files API keeps an upload for 1 hour to 30 days (3,600 to 2,592,000 seconds)
# when given an expiry.
_OPENAI_UPLOAD_EXPIRY_HOURS = (1, 720)

# The page extraction model used when neither ``advanced.extraction.model`` nor
# ``model`` is set.
DEFAULT_EXTRACTION_MODEL = "anthropic:claude-opus-5-5"

# The page-break verification model used when neither ``advanced.page_breaks.model``
# nor ``model`` is set.
DEFAULT_PAGE_BREAKS_MODEL = "anthropic:claude-opus-5-5"

# The survey model used when ``model`` is not set.
DEFAULT_SURVEY_MODEL = "anthropic:claude-opus-5-5"

# How hard the model thinks before answering.
type Effort = Literal["low", "medium", "high"]

# How a model gives structured output: the provider's own structured output, or a
# schema in the prompt. Forced tool choice is never used, since some models reject it.
type OutputMode = Literal["native", "prompted"]

# How a PDF reaches the provider: uploaded through its Files API, or sent inside the
# request itself.
type PdfTransport = Literal["upload", "request"]

# The providers pydelity supports.
type ProviderName = Literal["anthropic", "openai"]


def _anthropic_effort_settings(effort: Effort) -> ModelSettings:
    """Return the Anthropic request settings for an effort level.

    Anthropic models use adaptive thinking, and the effort level sets how much.

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
    """Facts about a provider that apply to all of its models.

    Attributes
    ----------
    effort_settings
        Turns pydelity's effort level into the provider's request settings.
    image_detail
        The detail value sent with each image so the provider reads it at its own
        size, or ``None`` when the provider takes no such value.
    image_max_long_edge_px
        The longest edge, in pixels, of an image the provider reads without shrinking
        it.
    image_max_patches
        The most patches an image the provider reads without shrinking it may have.
    image_patch_px
        The side of the square patches, in pixels, that the provider counts an image
        in (see `image_patches`).
    image_tokens
        The most input tokens one image within these limits can cost.
    max_upload_expiry_hours
        The longest upload expiry the provider allows, and pydelity's default.
    min_upload_expiry_hours
        The shortest upload expiry the provider allows.
    name
        The provider's name, as written in a model setting.
    output_mode
        How every step asks the provider for structured output. ``prompted`` puts
        the answer's JSON schema in the instructions and checks the answer after it
        arrives; ``native`` uses the provider's own structured output where the
        model supports it.
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
    image_detail: str | None
    image_max_long_edge_px: int
    image_max_patches: int
    image_patch_px: int
    image_tokens: int
    max_upload_expiry_hours: int
    min_upload_expiry_hours: int
    name: ProviderName
    output_mode: OutputMode
    pdf_image_tokens_per_page: int
    pdf_text_tokens_per_page: int
    pdf_transports: tuple[PdfTransport, ...]
    upload_purpose: str | None

    def image_patches(self, *, height_px: int, width_px: int) -> int:
        """Count the patches the provider divides an image into.

        Parameters
        ----------
        height_px
            The image's height in pixels.
        width_px
            The image's width in pixels.

        Returns
        -------
        int
            The patches across times the patches down, counting part of a patch as a
            whole one.

        Examples
        --------
        >>> PROFILES["anthropic"].image_patches(height_px=1000, width_px=1000)
        1296
        """

        side = self.image_patch_px
        return math.ceil(width_px / side) * math.ceil(height_px / side)

    @property
    def pdf_tokens_per_page(self) -> int:
        """Estimated input tokens for one PDF page: its text plus its image."""

        return self.pdf_image_tokens_per_page + self.pdf_text_tokens_per_page


PROFILES: dict[ProviderName, ProviderProfile] = {
    "anthropic": ProviderProfile(
        effort_settings=_anthropic_effort_settings,
        image_detail=None,
        image_max_long_edge_px=_ANTHROPIC_IMAGE_MAX_LONG_EDGE_PX,
        image_max_patches=_ANTHROPIC_IMAGE_MAX_PATCHES,
        image_patch_px=_ANTHROPIC_IMAGE_PATCH_PX,
        image_tokens=_ANTHROPIC_IMAGE_MAX_PATCHES,
        max_upload_expiry_hours=_ANTHROPIC_UPLOAD_EXPIRY_HOURS[1],
        min_upload_expiry_hours=_ANTHROPIC_UPLOAD_EXPIRY_HOURS[0],
        name="anthropic",
        # Anthropic compiles a native output schema into a grammar whose limits the
        # page answer exceeds, and those limits can change.
        output_mode="prompted",
        pdf_image_tokens_per_page=_ANTHROPIC_PDF_IMAGE_TOKENS,
        pdf_text_tokens_per_page=_ANTHROPIC_PDF_TEXT_TOKENS,
        pdf_transports=("upload", "request"),
        upload_purpose=None,
    ),
    "openai": ProviderProfile(
        effort_settings=_openai_effort_settings,
        image_detail=_OPENAI_IMAGE_DETAIL,
        image_max_long_edge_px=_OPENAI_IMAGE_MAX_LONG_EDGE_PX,
        image_max_patches=_OPENAI_IMAGE_MAX_PATCHES,
        image_patch_px=_OPENAI_IMAGE_PATCH_PX,
        image_tokens=math.ceil(
            _OPENAI_IMAGE_MAX_PATCHES * _OPENAI_IMAGE_TOKENS_PER_PATCH
        ),
        max_upload_expiry_hours=_OPENAI_UPLOAD_EXPIRY_HOURS[1],
        min_upload_expiry_hours=_OPENAI_UPLOAD_EXPIRY_HOURS[0],
        name="openai",
        output_mode="native",
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
            f"{setting!r} is not <provider>:<model-id>, such as "
            f"{DEFAULT_SURVEY_MODEL!r}"
        )
    if provider == "anthropic":
        return ModelChoice(model_id=model_id, provider="anthropic")
    if provider == "openai":
        return ModelChoice(model_id=model_id, provider="openai")

    supported = " or ".join(repr(name) for name in PROFILES)
    raise ValueError(f"provider {provider!r} is not supported; use {supported}")

"""The settings pydelity accepts, with their defaults and bounds.

Every model forbids unknown keys, so a misspelled setting is an error rather than
being silently ignored. The API keys are not settings: `ProviderEnv` reads them from
the environment only when a run needs a provider.
"""

# Standard Library
import re

from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal

# Third Party Library
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Package Library
from pydelity.providers.profiles import DEFAULT_MODEL, ModelChoice, parse_model

# Where outputs go when no output folder is set: this folder in the current
# directory, then one folder per PDF, named after the PDF.
_DEFAULT_OUTPUT_PARENT = "pydelity-output"

# A well-formed BCP-47 language tag (RFC 5646, section 2.1): language with up to
# three extended subtags, then optional script, region, variants, extensions and
# private use; or a private-use tag on its own. Grandfathered tags are not accepted.
_LANGUAGE_TAG = re.compile(
    r"(?:"
    r"(?:[A-Za-z]{2,3}(?:-[A-Za-z]{3}){0,3}|[A-Za-z]{4}|[A-Za-z]{5,8})"
    r"(?:-[A-Za-z]{4})?"
    r"(?:-(?:[A-Za-z]{2}|[0-9]{3}))?"
    r"(?:-(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*"
    r"(?:-[0-9A-WY-Za-wy-z](?:-[A-Za-z0-9]{2,8})+)*"
    r"(?:-[Xx](?:-[A-Za-z0-9]{1,8})+)?"
    r"|[Xx](?:-[A-Za-z0-9]{1,8})+"
    r")"
)


def _absolute(path: Path) -> Path:
    """Make a path absolute against the current directory, expanding ``~``.

    Symbolic links are not resolved.

    Parameters
    ----------
    path
        The path as given.

    Returns
    -------
    Path
        The absolute path.
    """

    return path.expanduser().absolute()


def _check_language_tag(tag: str) -> str:
    """Accept a well-formed BCP-47 language tag.

    Parameters
    ----------
    tag
        The tag to check.

    Returns
    -------
    str
        The tag, unchanged.

    Raises
    ------
    ValueError
        If the tag is not well-formed.
    """

    if not is_language_tag(tag):
        raise ValueError(f"{tag!r} is not a BCP-47 language tag, such as 'en' or 'ar'")
    return tag


def _check_model_setting(setting: str) -> str:
    """Accept a ``<provider>:<model-id>`` model setting for a supported provider.

    Parameters
    ----------
    setting
        The model setting to check.

    Returns
    -------
    str
        The setting, unchanged.
    """

    parse_model(setting)
    return setting


def _check_output_dir(path: Path) -> Path:
    """Accept an output folder that is not an existing file, made absolute.

    Parameters
    ----------
    path
        The output folder as given; it need not exist yet.

    Returns
    -------
    Path
        The absolute path.

    Raises
    ------
    ValueError
        If a file (not a folder) already exists at the path.
    """

    absolute = _absolute(path)
    if absolute.exists() and not absolute.is_dir():
        raise ValueError(f"not a folder: {path}")
    return absolute


def _check_pdf(path: Path) -> Path:
    """Accept a PDF path that exists and is a file, made absolute.

    Parameters
    ----------
    path
        The PDF path as given.

    Returns
    -------
    Path
        The absolute path.

    Raises
    ------
    ValueError
        If nothing exists at the path, or it is not a file.
    """

    absolute = _absolute(path)
    if not absolute.exists():
        raise ValueError(f"no such file: {path}")
    if not absolute.is_file():
        raise ValueError(f"not a file: {path}")
    return absolute


class ModelPrices(BaseModel):
    """Prices for one model, in US dollars per million tokens.

    They replace the prices pydelity would otherwise look up for the model.
    """

    model_config = ConfigDict(extra="forbid", use_attribute_docstrings=True)

    cache_read_usd_per_mtok: Annotated[Decimal, Field(ge=0)] | None = None
    """Price of input tokens read from the prompt cache; the input price if unset."""

    cache_write_usd_per_mtok: Annotated[Decimal, Field(ge=0)] | None = None
    """Price of input tokens written to the prompt cache; the input price if unset."""

    input_usd_per_mtok: Annotated[Decimal, Field(ge=0)]
    """Price of input tokens."""

    output_usd_per_mtok: Annotated[Decimal, Field(ge=0)]
    """Price of output tokens."""


class SurveyConfig(BaseModel):
    """Settings for the survey step."""

    model_config = ConfigDict(extra="forbid", use_attribute_docstrings=True)

    check_retries: Annotated[int, Field(ge=0, le=5)] = 2
    """How many times the model may answer again after failing the survey's checks."""

    effort: Literal["low", "medium", "high"] = "high"
    """How hard the model thinks before answering."""

    max_output_tokens: Annotated[int, Field(gt=0)] = 32_000
    """The most tokens one model answer may contain, thinking included."""

    request_timeout_seconds: Annotated[float, Field(gt=0)] = 900
    """How long to wait for one model request before it counts as failed."""


class UploadsConfig(BaseModel):
    """Settings for PDFs uploaded to the provider."""

    model_config = ConfigDict(extra="forbid", use_attribute_docstrings=True)

    expiry_hours: Annotated[int, Field(ge=1)] | None = None
    """How long the provider keeps an uploaded PDF; the provider's maximum if unset."""


class AdvancedConfig(BaseModel):
    """Settings most runs never need to change."""

    model_config = ConfigDict(extra="forbid", use_attribute_docstrings=True)

    models: dict[Annotated[str, AfterValidator(_check_model_setting)], ModelPrices] = (
        Field(default_factory=dict)
    )
    """Prices for models, by ``<provider>:<model-id>``."""

    provider_retries: Annotated[int, Field(ge=0, le=10)] = 2
    """How many times a request to the provider is retried after a temporary failure."""

    survey: SurveyConfig = Field(default_factory=SurveyConfig)
    """Settings for the survey step."""

    uploads: UploadsConfig = Field(default_factory=UploadsConfig)
    """Settings for PDFs uploaded to the provider."""


class Config(BaseModel):
    """Everything a pydelity run is set up with.

    Settings come from keywords (or command-line options), then an optional JSON or
    YAML file, then these defaults; `pydelity.config.loading.resolve_config` combines
    them and checks the result.
    """

    model_config = ConfigDict(extra="forbid", use_attribute_docstrings=True)

    advanced: AdvancedConfig = Field(default_factory=AdvancedConfig)
    """Settings most runs never need to change."""

    instructions: str | None = None
    """Extra instructions for the model about this PDF."""

    languages: list[Annotated[str, AfterValidator(_check_language_tag)]] = Field(
        default_factory=list
    )
    """The PDF's languages as BCP-47 tags, such as ``en`` or ``ar``."""

    max_cost: Annotated[Decimal, Field(gt=0)] | None = None
    """The most the output folder's model requests may cost, in US dollars."""

    model: Annotated[str, AfterValidator(_check_model_setting)] = DEFAULT_MODEL
    """The model, as ``<provider>:<model-id>``; provider ``anthropic`` or ``openai``.

    The model ID is sent to the provider as given.
    """

    output_dir: Annotated[Path, AfterValidator(_check_output_dir)] | None = None
    """The output folder; ``pydelity-output/<PDF name>`` in the current folder if unset.
    """

    overwrite: bool = False
    """Whether to redo steps whose outputs could be reused."""

    pdf: Annotated[Path, AfterValidator(_check_pdf)]
    """The PDF to process."""

    @property
    def model_choice(self) -> ModelChoice:
        """The model setting split into its provider and model ID."""

        return parse_model(self.model)

    @property
    def output_folder(self) -> Path:
        """The output folder, with the default applied when none is set."""

        if self.output_dir is not None:
            return self.output_dir
        return Path(_DEFAULT_OUTPUT_PARENT).absolute() / self.pdf.stem


class ProviderEnv(BaseSettings):
    """The provider API keys, read from environment variables only.

    No ``.env`` file is loaded. Built only when a run needs a provider, never at
    import.
    """

    model_config = SettingsConfigDict(
        env_file=None, extra="ignore", use_attribute_docstrings=True
    )

    anthropic_api_key: SecretStr | None = None
    """``ANTHROPIC_API_KEY``: the key for Anthropic models."""

    openai_api_key: SecretStr | None = None
    """``OPENAI_API_KEY``: the key for OpenAI models."""


def is_language_tag(tag: str) -> bool:
    """Tell whether a string is a well-formed BCP-47 language tag.

    Only the syntax is checked (RFC 5646, section 2.1): ``en``, ``zh-Hant-TW`` and
    ``zxx`` pass; ``en_US`` and ``e`` do not. Grandfathered tags such as
    ``i-klingon`` are not accepted.

    Parameters
    ----------
    tag
        The string to check.

    Returns
    -------
    bool
        Whether the tag is well-formed.

    Examples
    --------
    >>> is_language_tag("zh-Hant-TW"), is_language_tag("en_US")
    (True, False)
    """

    return _LANGUAGE_TAG.fullmatch(tag) is not None

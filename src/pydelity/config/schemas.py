"""The settings pydelity accepts, with their defaults and bounds.

Every model rejects unknown keys, so a misspelled setting raises an error. API keys
are not settings. `ProviderEnv` reads them from environment variables when a run
needs a provider.
"""

# Standard Library
import json

from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal

# Third Party Library
import langcodes

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Package Library
from pydelity.providers.profiles import DEFAULT_MODEL, ModelChoice, parse_model

# The default parent of the output folders, in the current directory. Each PDF gets
# its own folder inside it, named after the PDF.
_DEFAULT_OUTPUT_PARENT = "pydelity-output"


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
    """Accept a registered BCP-47 language tag, in its standard form.

    Parameters
    ----------
    tag
        The tag to check.

    Returns
    -------
    str
        The tag in standard form (see `standard_language_tag`).

    Raises
    ------
    ValueError
        If the tag is not a valid BCP-47 language tag.
    """

    if not is_language_tag(tag):
        raise ValueError(
            f"{json.dumps(tag, ensure_ascii=False)} is not a valid BCP-47 language "
            'tag, such as "en" or "ar"'
        )
    return standard_language_tag(tag)


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
    """All the settings for a pydelity run.

    Keywords (or command-line options) override an optional JSON or YAML file, which
    overrides these defaults. `pydelity.config.loading.resolve_config` merges and
    validates them.
    """

    model_config = ConfigDict(extra="forbid", use_attribute_docstrings=True)

    advanced: AdvancedConfig = Field(default_factory=AdvancedConfig)
    """Settings most runs never need to change."""

    instructions: str | None = None
    """Extra instructions for the model about this PDF."""

    languages: list[Annotated[str, AfterValidator(_check_language_tag)]] = Field(
        default_factory=list
    )
    """The PDF's languages as BCP-47 tags such as ``en`` or ``ar``, in standard form."""

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

    No ``.env`` file is loaded. pydelity creates this only when a run needs a
    provider, not at import time.
    """

    model_config = SettingsConfigDict(
        env_file=None, extra="ignore", use_attribute_docstrings=True
    )

    anthropic_api_key: SecretStr | None = None
    """``ANTHROPIC_API_KEY``: the key for Anthropic models."""

    openai_api_key: SecretStr | None = None
    """``OPENAI_API_KEY``: the key for OpenAI models."""


def is_language_tag(tag: str) -> bool:
    """Tell whether a string is a valid BCP-47 language tag.

    The tag must be well-formed and every subtag must be in the IANA language subtag
    registry that `langcodes` bundles. Special and private-use tags (``zxx``,
    ``und``, ``mul``, ``qaa``, ``x-...``) are valid; spelling variants such as
    ``en_US`` are valid and become ``en-US`` in standard form.

    Parameters
    ----------
    tag
        The string to check.

    Returns
    -------
    bool
        Whether the tag is valid.

    Examples
    --------
    >>> is_language_tag("zh-Hant-TW"), is_language_tag("zz")
    (True, False)
    """

    return langcodes.tag_is_valid(tag)


def standard_language_tag(tag: str) -> str:
    """Return a valid language tag in its standard form.

    Case and separators are normalized, deprecated codes become their replacements
    and three-letter codes with a two-letter equivalent become two-letter, so two
    spellings of one language compare equal.

    Parameters
    ----------
    tag
        A tag that `is_language_tag` accepts.

    Returns
    -------
    str
        The tag in standard form.

    Examples
    --------
    >>> standard_language_tag("EN_us"), standard_language_tag("iw")
    ('en-US', 'he')
    """

    return langcodes.standardize_tag(tag)

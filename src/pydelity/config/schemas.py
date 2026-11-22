"""The settings pydelity accepts, with their defaults and bounds.

Every model rejects unknown keys, so a misspelled setting raises an error. API keys
are not settings. `ProviderEnv` reads them from environment variables when a run
needs a provider.
"""

# Standard Library
import json
import re

from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal

# Third Party Library
import langcodes

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    SecretStr,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

# Package Library
from pydelity.providers.profiles import (
    DEFAULT_EXTRACTION_MODEL,
    DEFAULT_PAGE_BREAKS_MODEL,
    DEFAULT_SURVEY_MODEL,
    ModelChoice,
    parse_model,
)

# The default parent of the output folders, in the current directory. Each PDF gets
# its own folder inside it, named after the PDF.
_DEFAULT_OUTPUT_PARENT = "pydelity-output"

# One item of a page list: a page number or a range of page numbers, such as ``8`` or
# ``1-5``. Only ASCII digits count.
_PAGE_ITEM = re.compile(r"([0-9]+)(?:-([0-9]+))?")


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


def _blank_as_unset(text: str) -> str | None:
    """Treat text that is empty or only whitespace as unset.

    Parameters
    ----------
    text
        The text as given.

    Returns
    -------
    str | None
        The text, unchanged, or ``None`` when it is blank.
    """

    return text if text.strip() else None


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


def _check_pages(text: str) -> str:
    """Accept a page list, in its canonical form.

    Parameters
    ----------
    text
        The page list as given, such as ``"8, 1-5"``.

    Returns
    -------
    str
        The page list sorted and merged, such as ``"1-5,8"``.
    """

    ranges = parse_pages(text)
    return ",".join(
        str(first) if first == last else f"{first}-{last}" for first, last in ranges
    )


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


def _int_as_page(value: object) -> object:
    """Turn a whole number given for ``pages`` into the page list of that one page.

    Parameters
    ----------
    value
        The ``pages`` value as given.

    Returns
    -------
    object
        The number as text, or any other value unchanged.
    """

    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return value


class ExtractionConfig(BaseModel):
    """Settings for page extraction.

    They apply to page extraction's requests and to its verifier's requests alike.
    """

    model_config = ConfigDict(extra="forbid", use_attribute_docstrings=True)

    check_retries: Annotated[int, Field(ge=0, le=5)] = 2
    """How many times a model may answer again after failing page extraction's
    checks."""

    concurrent_pages: Annotated[int, Field(ge=1, le=32)] = 8
    """How many pages are extracted at the same time."""

    effort: Literal["low", "medium", "high"] = "high"
    """How hard the model thinks before answering."""

    instructions: Annotated[str, AfterValidator(_blank_as_unset)] | None = None
    """What is particular, different or nuanced about this PDF, in your own words, for
    page extraction's model and its verifier. Blank text counts as unset."""

    max_output_tokens: Annotated[int, Field(gt=0)] = 32_000
    """The most tokens one model answer may contain, thinking included."""

    model: Annotated[str, AfterValidator(_check_model_setting)] | None = None
    """The model for page extraction, as ``<provider>:<model-id>``; ``model``, or else
    page extraction's default, if unset."""

    request_timeout_seconds: Annotated[float, Field(gt=0)] = 600
    """How long to wait for one model request before it counts as failed."""

    verify: bool | None = None
    """Whether a verifier reviews each page's extraction; ``verify`` if unset."""


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


class PageBreaksConfig(BaseModel):
    """Settings for page-break verification.

    They apply to page-break verification's requests and to its verifier's requests
    alike.
    """

    model_config = ConfigDict(extra="forbid", use_attribute_docstrings=True)

    check_retries: Annotated[int, Field(ge=0, le=5)] = 2
    """How many times a model may answer again after failing page-break
    verification's checks."""

    concurrent_breaks: Annotated[int, Field(ge=1, le=32)] = 8
    """How many page breaks are judged at the same time."""

    effort: Literal["low", "medium", "high"] = "high"
    """How hard the model thinks before answering."""

    instructions: Annotated[str, AfterValidator(_blank_as_unset)] | None = None
    """What is particular, different or nuanced about this PDF's page breaks, in your
    own words, for page-break verification's model and its verifier. Blank text counts
    as unset."""

    max_output_tokens: Annotated[int, Field(gt=0)] = 32_000
    """The most tokens one model answer may contain, thinking included."""

    model: Annotated[str, AfterValidator(_check_model_setting)] | None = None
    """The model for page-break verification, as ``<provider>:<model-id>``; ``model``,
    or else page-break verification's default, if unset."""

    request_timeout_seconds: Annotated[float, Field(gt=0)] = 600
    """How long to wait for one model request before it counts as failed."""

    verify: bool | None = None
    """Whether a verifier reviews each page break's verdict; ``verify`` if unset."""


class SurveyConfig(BaseModel):
    """Settings for the survey step.

    They apply to the survey's requests and to its verifier's requests alike.
    """

    model_config = ConfigDict(extra="forbid", use_attribute_docstrings=True)

    check_retries: Annotated[int, Field(ge=0, le=5)] = 2
    """How many times the model may answer again after failing the survey's checks."""

    effort: Literal["low", "medium", "high"] = "high"
    """How hard the model thinks before answering."""

    instructions: Annotated[str, AfterValidator(_blank_as_unset)] | None = None
    """What is particular, different or nuanced about this PDF, in your own words, for
    the survey's model and its verifier. Blank text counts as unset."""

    max_output_tokens: Annotated[int, Field(gt=0)] = 32_000
    """The most tokens one model answer may contain, thinking included."""

    request_timeout_seconds: Annotated[float, Field(gt=0)] = 900
    """How long to wait for one model request before it counts as failed."""

    verify: bool | None = None
    """Whether a verifier reviews the survey's answer; ``verify`` if unset."""


class UploadsConfig(BaseModel):
    """Settings for PDFs uploaded to the provider."""

    model_config = ConfigDict(extra="forbid", use_attribute_docstrings=True)

    expiry_hours: Annotated[int, Field(ge=1)] | None = None
    """How long the provider keeps an uploaded PDF; the provider's maximum if unset."""


class AdvancedConfig(BaseModel):
    """Settings most runs never need to change."""

    model_config = ConfigDict(extra="forbid", use_attribute_docstrings=True)

    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    """Settings for page extraction."""

    models: dict[Annotated[str, AfterValidator(_check_model_setting)], ModelPrices] = (
        Field(default_factory=dict)
    )
    """Prices for models, by ``<provider>:<model-id>``."""

    page_breaks: PageBreaksConfig = Field(default_factory=PageBreaksConfig)
    """Settings for page-break verification."""

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

    languages: list[Annotated[str, AfterValidator(_check_language_tag)]] = Field(
        default_factory=list
    )
    """The PDF's languages as BCP-47 tags such as ``en`` or ``ar``, in standard form."""

    max_cost: Annotated[Decimal, Field(gt=0)] | None = None
    """The most the output folder's model requests may cost, in US dollars."""

    model: Annotated[str, AfterValidator(_check_model_setting)] | None = None
    """The model for every step, as ``<provider>:<model-id>``; each step's default if
    unset.

    The provider is ``anthropic`` or ``openai``, and the model ID is sent to the
    provider as given.
    """

    output_dir: Annotated[Path, AfterValidator(_check_output_dir)] | None = None
    """The output folder; ``pydelity-output/<PDF name>`` in the current folder if unset.
    """

    overwrite: bool = False
    """Whether to redo steps whose outputs could be reused."""

    pages: (
        Annotated[str, BeforeValidator(_int_as_page), AfterValidator(_check_pages)]
        | None
    ) = None
    """The pages to extract, numbered from 1 as a PDF viewer shows them, such as
    ``1-5,8``; every page if unset. The survey always reads every page.

    Page-break verification runs only when every page has an up-to-date page file,
    from this run or an earlier one.
    """

    pause: bool = True
    """Whether to stop after a step that wrote new output, so it can be checked before
    the next step is paid for."""

    pdf: Annotated[Path, AfterValidator(_check_pdf)]
    """The PDF to process."""

    verify: bool = False
    """Whether a verifier reviews each step's answer.

    The verifier is a second request to the step's model, which checks the answer
    against the PDF and may correct it. Each verifier request adds cost.
    """

    @property
    def extraction_model(self) -> ModelChoice:
        """The page extraction model.

        It is ``advanced.extraction.model``, else ``model``, else page extraction's
        default.
        """

        setting = (
            self.advanced.extraction.model or self.model or DEFAULT_EXTRACTION_MODEL
        )
        return parse_model(setting)

    @property
    def output_folder(self) -> Path:
        """The output folder, with the default applied when none is set."""

        if self.output_dir is not None:
            return self.output_dir
        return Path(_DEFAULT_OUTPUT_PARENT).absolute() / self.pdf.stem

    @property
    def page_breaks_model(self) -> ModelChoice:
        """The page-break verification model.

        It is ``advanced.page_breaks.model``, else ``model``, else page-break
        verification's default.
        """

        setting = (
            self.advanced.page_breaks.model or self.model or DEFAULT_PAGE_BREAKS_MODEL
        )
        return parse_model(setting)

    @property
    def survey_model(self) -> ModelChoice:
        """The survey model: ``model``, else the survey's default."""

        return parse_model(self.model or DEFAULT_SURVEY_MODEL)

    @property
    def verify_extraction(self) -> bool:
        """Whether page extraction's verifier runs.

        It is ``advanced.extraction.verify`` when set, else ``verify``.
        """

        override = self.advanced.extraction.verify
        return self.verify if override is None else override

    @property
    def verify_page_breaks(self) -> bool:
        """Whether page-break verification's verifier runs.

        It is ``advanced.page_breaks.verify`` when set, else ``verify``.
        """

        override = self.advanced.page_breaks.verify
        return self.verify if override is None else override

    @property
    def verify_survey(self) -> bool:
        """Whether the survey's verifier runs.

        It is ``advanced.survey.verify`` when set, else ``verify``.
        """

        override = self.advanced.survey.verify
        return self.verify if override is None else override


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


def parse_pages(text: str) -> list[tuple[int, int]]:
    """Read a page list into sorted, merged ranges of page numbers.

    Pages are numbered from 1, as a PDF viewer shows them. Items are separated by
    commas, and each is a page (``8``) or a range of pages (``1-5``), with spaces
    allowed around it. Overlapping, repeated and adjacent items merge.

    Parameters
    ----------
    text
        The page list, such as ``"1-5,8"``.

    Returns
    -------
    list[tuple[int, int]]
        The first and last page of each range, in ascending order.

    Raises
    ------
    ValueError
        If the list is empty, an item is not a page or a range of pages, a page is
        0, or a range ends before it starts.

    Examples
    --------
    >>> parse_pages("8, 1-5, 4-6")
    [(1, 6), (8, 8)]
    """

    if not text.strip():
        raise ValueError(
            "empty; give pages such as 1-5,8, or leave it unset to extract every page"
        )

    ranges = []
    for item in text.split(","):
        match = _PAGE_ITEM.fullmatch(item.strip())
        if match is None:
            shown = json.dumps(item.strip(), ensure_ascii=False)
            raise ValueError(
                f"{shown} is not a page or a range of pages, such as 8 or 1-5"
            )
        first = int(match[1])
        last = int(match[2] or match[1])
        if first < 1:
            raise ValueError("pages are numbered from 1")
        if last < first:
            raise ValueError(f"the range {first}-{last} ends before it starts")
        ranges.append((first, last))

    # Sort, then join each range into the one before it when they overlap or touch.
    ranges.sort()
    merged = [ranges[0]]
    for first, last in ranges[1:]:
        previous_first, previous_last = merged[-1]
        if first <= previous_last + 1:
            merged[-1] = (previous_first, max(previous_last, last))
        else:
            merged.append((first, last))
    return merged


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

"""The survey's data: facts (``pdf_facts.json``), the survey (``pdf_survey.json``).

The item vocabulary (`ItemKind`, `ItemRole`) is the contract later steps build on.

Page indexes are 0-based. Boxes are PDF points in the displayed page space (page
rotation applied), origin top-left, as ``[x0, y0, x1, y1]``. Output models accept
fields they do not know, so a file written by a newer pydelity with the same major
``schema_version`` still loads.

`SurveyAnswer` is what the model answers. It uses only strings, integers, booleans,
enums, lists and objects, with no patterns or bounds, so it fits both providers'
structured output; Python checks the values instead. Its region boxes are fractions of
the displayed page, which Python converts to points.
"""

# Standard Library
from datetime import datetime
from enum import StrEnum
from typing import Literal

# Third Party Library
from pydantic import BaseModel, ConfigDict

# Package Library
from pydelity.providers.profiles import Effort

# The version of the facts' schema. Additive changes bump the minor version, breaking
# changes the major version.
FACTS_SCHEMA_VERSION = "1.0"

# The version of the survey's schema, versioned the same way.
SURVEY_SCHEMA_VERSION = "1.0"

# A page angle in degrees, counterclockwise.
type Angle = Literal[0, 90, 180, 270]

# Where an artifact sits on the displayed page; ``middle`` covers marks over the
# content, such as watermarks and stamps.
type ArtifactPosition = Literal["top", "bottom", "left", "right", "middle"]

# Where a line sits on the displayed page: the top or bottom band, or between them.
type Band = Literal["top", "bottom", "middle"]

# The survey's checks, C1 to C7 in order. The names are part of the ``run.json``
# contract.
type CheckName = Literal[
    "labels",
    "regions",
    "rotation",
    "page_numbering",
    "artifacts",
    "writing_direction",
    "languages",
]

# A writing direction: left to right, right to left, or top to bottom.
type Direction = Literal["ltr", "rtl", "ttb"]

# The type of an interactive form field.
type FieldType = Literal[
    "text", "checkbox", "radio", "combobox", "listbox", "signature", "button"
]

# A page's inline writing direction.
type InlineDirection = Literal["ltr", "rtl", "mixed", "none"]

# How printed page numbers are written in a range of pages.
type NumberingStyle = Literal["arabic", "roman", "other", "none"]

# A fact the probe may fail to read on a malformed PDF.
type ProbeFact = Literal["bookmarks", "form", "structure"]

# How well the structure tags cover the PDF.
type StructureQuality = Literal["none", "poor", "partial", "good"]

# Whether a page's text layer is readable.
type TextQuality = Literal["none", "good", "garbled"]


class _Output(BaseModel):
    """Base for the models stored in output files."""

    model_config = ConfigDict(use_attribute_docstrings=True)


class Bookmark(_Output):
    """One entry of the PDF's bookmarks (outline)."""

    level: int
    """Nesting level, 1 for top-level bookmarks."""

    page_index: int | None
    """The page the bookmark points to, or ``None`` when it points nowhere."""

    title: str
    """The bookmark's title."""


class DirectionFacts(_Output):
    """The writing direction measured on a page."""

    inline: InlineDirection
    """``rtl`` or ``ltr`` when right-to-left or left-to-right letters reach the
    dominant share of the page's letters, ``mixed`` when neither does, ``none``
    without letters."""

    vertical_share: float
    """The share of the page's characters on lines in vertical writing mode."""


class FormField(_Output):
    """One interactive form field."""

    bbox: tuple[float, float, float, float]
    """The field's box on the displayed page."""

    checked: bool | None
    """Whether a checkbox or radio button is on; ``None`` for other fields."""

    name: str
    """The field's fully qualified name."""

    options: list[str]
    """The choices of a combobox or listbox; empty for other fields."""

    page_index: int
    """The page the field is on."""

    type: FieldType
    """The field's type."""

    value: str | None
    """The field's current value, if it has one."""


class FormInfo(_Output):
    """Which kinds of form the PDF holds."""

    has_acroform: bool
    """Whether the PDF has an AcroForm (interactive form) dictionary."""

    has_xfa: bool
    """Whether the form also carries an XFA form."""


class ItemKind(StrEnum):
    """The kind of content an item holds. Later steps handle each kind differently."""

    CODE = "code"
    """Code and other preformatted text, whose whitespace and line breaks matter."""

    FIELD = "field"
    """A form field with its label and value."""

    FIGURE = "figure"
    """An image, chart or diagram."""

    FORMULA = "formula"
    """A mathematical or chemical formula."""

    LIST = "list"
    """A list of items."""

    TABLE = "table"
    """A table."""

    TEXT = "text"
    """Running text."""


class ItemRole(StrEnum):
    """The role an item plays in the document. Later steps handle each differently."""

    ARTIFACT = "artifact"
    """Page furniture, such as running headers, footers and page numbers."""

    ASIDE = "aside"
    """Content beside the main flow, such as a sidebar or callout."""

    BODY = "body"
    """The main content."""

    CAPTION = "caption"
    """A caption of a figure or table."""

    FOOTNOTE = "footnote"
    """A footnote or endnote."""

    HEADING = "heading"
    """A heading."""

    NAVIGATION = "navigation"
    """A table of contents, index or other navigation aid."""


class NumberingRange(_Output):
    """Consecutive measured pages whose printed numbers follow their page indexes."""

    first_page_index: int
    """The first page of the range."""

    last_page_index: int
    """The last page of the range, inclusive."""

    offset: int
    """The printed number minus the page index, the same on every page measured."""

    pages_measured: int
    """How many pages in the range have a printed number."""

    style: Literal["arabic", "roman"]
    """How the numbers are written."""


class OrientationFacts(_Output):
    """Which way the text runs on the displayed page."""

    chars_by_angle: dict[str, int]
    """Characters on horizontal-mode lines, by baseline angle (``"0"``, ``"90"``,
    ``"180"``, ``"270"``, counterclockwise on the displayed page)."""

    confident: bool
    """Whether there are enough characters and the dominant angle has a large enough
    share for the measurement to be relied on."""

    dominant: Angle | None
    """The angle most characters run at, or ``None`` without horizontal text."""


class PdfIdentity(_Output):
    """Which PDF the facts describe."""

    bytes: int
    """The file's size in bytes."""

    name: str
    """The file name."""

    page_count: int
    """The number of pages."""

    sha256: str
    """The SHA-256 hex digest of the file."""


class PrintedNumber(_Output):
    """The page number printed on a page, or its page label."""

    source: Literal["page_label", "text"]
    """``page_label`` from the PDF's page labels, or ``text`` from a line near the top
    or bottom of the page."""

    style: Literal["arabic", "roman", "label"]
    """``arabic`` or ``roman`` numerals, or ``label`` for any other page label."""

    text: str
    """The number or label as printed."""

    value: int | None
    """The number's value, or ``None`` for a label that is not a number."""


class ProbeError(_Output):
    """A fact the probe could not read, because reading it failed."""

    fact: ProbeFact
    """Which fact could not be read."""

    message: str
    """What went wrong."""


class RepeatedLine(_Output):
    """A line that repeats across pages, such as a running header or footer."""

    band: Band
    """Where the line usually sits on its pages."""

    id: str
    """The line's identifier, ``R1``, ``R2`` and so on, most frequent first."""

    normalized: str
    """The form lines are compared in: Unicode NFKC, case-folded, whitespace
    collapsed, each run of digits written as ``#``."""

    pages: list[int]
    """The pages the line appears on."""

    text: str
    """The line as printed where it first appears."""


class StructureFacts(_Output):
    """What the PDF's structure tags (the tagged-PDF tree) cover."""

    element_count: int
    """How many structure elements the tree has (up to the probe's cap)."""

    marked: bool
    """Whether the PDF declares itself a tagged PDF."""

    pages_with_tagged_content: int
    """How many pages have content linked to the tree."""

    quality: StructureQuality
    """``none`` without a tree; ``poor`` with only grouping elements or very few;
    ``partial`` when tagged content covers too few of the pages with text;
    ``good`` otherwise."""

    tagged: bool
    """Whether the PDF has a structure tree."""

    truncated: bool
    """Whether the probe stopped counting at its element cap."""

    type_counts: dict[str, int]
    """Elements by standard type, after the tree's role map is applied."""


class TextFacts(_Output):
    """How much text a page's text layer holds, and whether it is readable."""

    chars: int
    """Characters other than whitespace."""

    control_chars: int
    """Control characters among them."""

    private_use_chars: int
    """Private-use characters among them."""

    quality: TextQuality
    """``none`` without characters; ``garbled`` when control, private-use,
    unassigned and replacement characters reach the garbled share; ``good``
    otherwise."""

    replacement_chars: int
    """Replacement characters (U+FFFD) among them, for glyphs with no known
    character."""

    unassigned_chars: int
    """Characters Unicode does not assign, among them."""


class PageFacts(_Output):
    """What the probe measured on one page."""

    direction: DirectionFacts
    """The writing direction."""

    height_pt: float
    """The displayed page's height in points."""

    index: int
    """The page's index."""

    orientation: OrientationFacts
    """Which way the text runs."""

    printed_number: PrintedNumber | None
    """The page number printed on the page, if one was found."""

    rotation_attribute: int
    """The page's rotation attribute in degrees, clockwise."""

    text: TextFacts
    """The text layer."""

    width_pt: float
    """The displayed page's width in points."""


class Facts(_Output):
    """Everything the probe measured.

    A fact that could not be read is ``None`` and has a ``probe_errors`` item; an
    empty list means the PDF has none.
    """

    bookmarks: list[Bookmark] | None
    """The bookmarks (outline)."""

    form: FormInfo | None
    """Which kinds of form the PDF holds."""

    form_fields: list[FormField] | None
    """The interactive form fields."""

    page_numbering: list[NumberingRange]
    """Ranges of pages whose printed numbers follow their indexes."""

    pages: list[PageFacts]
    """What was measured on each page."""

    probe_errors: list[ProbeError]
    """The facts that could not be read."""

    repeated_lines: list[RepeatedLine]
    """Lines that repeat across pages, most frequent first."""

    repeated_lines_truncated: bool
    """Whether more repeated lines were found than are kept."""

    structure: StructureFacts | None
    """What the structure tags cover."""


class PdfFacts(_Output):
    """The contents of ``pdf_facts.json``: the measured facts and their summary."""

    facts: Facts
    """The measured facts."""

    fingerprint: str
    """``sha256:`` fingerprint of what the facts depend on; a matching file is
    reused."""

    measured_at: datetime
    """When the PDF was measured (UTC)."""

    pdf: PdfIdentity
    """Which PDF was measured."""

    probe_version: int
    """The version of the measurement rules."""

    pydelity_version: str
    """The pydelity version that measured the PDF."""

    schema_version: str
    """The version of this file's schema, ``"MAJOR.MINOR"``."""

    summary: list[str]
    """The facts as plain-text lines, for people and for the model."""


class Artifact(_Output):
    """Page furniture the model identified, such as a running header or a stamp."""

    description: str
    """What the artifact is, in a few words."""

    id: str
    """The artifact's identifier, such as ``A1``."""

    position: ArtifactPosition
    """Where the artifact sits on the displayed page."""

    repeated_line_ids: list[str]
    """The IDs of the measured repeated lines (``R1``, ``R2`` and so on) that are this
    artifact; empty when no repeated line is."""


class CheckFailure(_Output):
    """One problem a check found in the model's answer."""

    details: dict[str, object]
    """The proposed and measured values, such as ``{"proposed": 0, "measured": 90}``."""

    message: str
    """What is wrong, naming the check and the proposed and measured values."""

    page_index: int | None
    """The page the problem is on, or ``None`` when no single page applies."""


class CheckResult(_Output):
    """The result of one check on the accepted answer."""

    attempts: int
    """How many model answers were checked: 1 plus the retries used."""

    failures: list[CheckFailure]
    """The problems the check found in the accepted answer."""

    name: CheckName
    """The check."""

    passed: bool
    """Whether the accepted answer passed: ``failures`` is empty."""


class DirectionRange(_Output):
    """Consecutive pages written in one direction."""

    direction: Direction
    """The writing direction on these pages."""

    first_page_index: int
    """The first page of the range (0-based)."""

    last_page_index: int
    """The last page of the range, inclusive."""


class FractionBox(_Output):
    """A box on the displayed page, in fractions of its size from the top left."""

    x0: float
    """The left edge, from 0 (the page's left) to 1 (its right)."""

    x1: float
    """The right edge."""

    y0: float
    """The top edge, from 0 (the page's top) to 1 (its bottom)."""

    y1: float
    """The bottom edge."""


class Label(_Output):
    """A name for one kind of content in this PDF, with its role and allowed kinds."""

    description: str
    """What content gets this label."""

    kinds: list[ItemKind]
    """The kinds of item this label may be given to; at least one."""

    name: str
    """The label's name, unique in the PDF regardless of case."""

    role: ItemRole
    """The role content with this label plays."""


class NonArtifactLine(_Output):
    """A measured repeated line that is not page furniture."""

    reason: str
    """Why the line is content rather than page furniture."""

    repeated_line_id: str
    """The repeated line's ID, such as ``R3``."""


class PageNumberingRange(_Output):
    """Consecutive pages whose printed numbers follow one style and offset."""

    first_page_index: int
    """The first page of the range (0-based)."""

    last_page_index: int
    """The last page of the range, inclusive."""

    offset: int | None
    """The printed number minus the page index, or ``None`` when the pages print no
    numbers that follow the page index."""

    style: NumberingStyle
    """How the numbers are written."""


class ProposedRegion(_Output):
    """An area of one page the model labels, with its box as page fractions."""

    bbox: FractionBox
    """The area on the displayed page."""

    label: str
    """The label of the area's content."""

    note: str
    """Why the area is worth marking; may be empty."""

    page_index: int
    """The page (0-based)."""


class Region(_Output):
    """An area of one page the model labeled, with its box in points."""

    bbox: tuple[float, float, float, float]
    """The area on the displayed page, as ``[x0, y0, x1, y1]`` in points."""

    label: str
    """The label of the area's content."""

    note: str
    """Why the area is worth marking; may be empty."""

    page_index: int
    """The page (0-based)."""


class ReviewIssue(_Output):
    """A problem a person should review, from a check that still failed."""

    check: CheckName
    """The check that found the problem."""

    details: dict[str, object]
    """The proposed and measured values."""

    message: str
    """What is wrong."""

    page_index: int | None
    """The page the problem is on, or ``None`` when no single page applies."""

    step: Literal["survey"]
    """The step whose check found the problem."""


class RotationRange(_Output):
    """Consecutive pages whose content needs the same rotation to be upright."""

    degrees: Angle
    """The clockwise rotation that makes the displayed page's content upright."""

    first_page_index: int
    """The first page of the range (0-based)."""

    last_page_index: int
    """The last page of the range, inclusive."""


class StartMarker(_Output):
    """Text that marks where a new unit of content starts."""

    description: str
    """What starts where the text appears."""

    text: str
    """The text, as printed."""


class SurveySettings(_Output):
    """The survey settings a survey's result depends on."""

    check_retries: int
    """How many times the model could answer again after failing the checks."""

    effort: Effort
    """How hard the model thought before answering."""

    max_output_tokens: int
    """The most tokens one model answer could contain, thinking included."""


class WritingDirection(_Output):
    """The writing direction of the PDF's pages."""

    default: Direction
    """The direction of every page no range covers."""

    ranges: list[DirectionRange]
    """Ranges of pages whose direction differs from ``default``."""


class Profile(_Output):
    """What later steps depend on: how the PDF's pages are laid out."""

    continuation_notes: list[str]
    """How content continues from one page to the next."""

    labels: list[Label]
    """The labels for this PDF's content; always includes ``other``."""

    languages: list[str]
    """BCP-47 tags in standard form: the user's languages, then the model's."""

    page_numbering: list[PageNumberingRange]
    """How printed page numbers relate to page indexes, by range of pages."""

    rotation: list[RotationRange]
    """The rotation that makes each range of pages upright; other pages need none."""

    start_markers: list[StartMarker]
    """Text that marks where a new unit of content starts."""

    user_instructions: str | None
    """The user's instructions for this PDF, if any."""

    writing_direction: WritingDirection
    """The writing direction of the pages."""


class Proposal(_Output):
    """The model's answer that is not part of the profile."""

    artifacts: list[Artifact]
    """Page furniture, with the repeated lines it accounts for."""

    non_artifact_lines: list[NonArtifactLine]
    """Repeated lines that are content rather than page furniture."""

    notes: list[str]
    """Anything else the model noticed about the layout."""

    regions: list[Region]
    """Areas of single pages the model labeled."""


class SurveyAnswer(_Output):
    """The model's answer to the survey: the profile and the rest of the proposal."""

    artifacts: list[Artifact]
    """Page furniture. Every measured repeated line ID appears exactly once, here or
    in ``non_artifact_lines``."""

    continuation_notes: list[str]
    """How content continues from one page to the next, such as text or tables that
    run across a page break."""

    labels: list[Label]
    """Names for the kinds of content in this PDF, each with one role."""

    languages: list[str]
    """BCP-47 tags of the languages the PDF's text is written in; at least one."""

    non_artifact_lines: list[NonArtifactLine]
    """Measured repeated lines that are content rather than page furniture."""

    notes: list[str]
    """Anything else about the layout that later steps should know."""

    page_numbering: list[PageNumberingRange]
    """Ranges of pages with their printed page numbers' style and offset."""

    regions: list[ProposedRegion]
    """Areas of single pages worth labeling."""

    rotation: list[RotationRange]
    """Ranges of pages whose content is not upright; other pages need no rotation."""

    start_markers: list[StartMarker]
    """Text that marks where a new unit of content starts."""

    writing_direction: WritingDirection
    """The writing direction of the pages."""


class SurveyInputs(_Output):
    """What a survey was made from."""

    facts_fingerprint: str
    """The fingerprint of the ``pdf_facts.json`` the survey used."""

    instructions: str | None
    """The user's instructions, if any."""

    languages: list[str]
    """The user's languages, in standard form."""

    model: str
    """The model, as ``<provider>:<model-id>``."""

    page_count: int
    """The PDF's number of pages."""

    pdf_bytes: int
    """The PDF's size in bytes."""

    pdf_name: str
    """The PDF's file name."""

    pdf_sha256: str
    """The PDF's SHA-256 hex digest."""

    prompt_version: int
    """The version of the survey prompt."""

    settings: SurveySettings
    """The survey settings used."""


class PdfSurvey(_Output):
    """The contents of ``pdf_survey.json``: the checked survey of one PDF."""

    checks: list[CheckResult]
    """The result of each check, C1 to C7 in order."""

    facts: Facts
    """A copy of the measured facts the survey used."""

    fingerprint: str
    """``sha256:`` fingerprint of what the survey depends on; a matching file is
    reused."""

    inputs: SurveyInputs
    """What the survey was made from."""

    issues: list[ReviewIssue]
    """One review issue per failure on the accepted answer."""

    profile: Profile
    """How the PDF's pages are laid out, for later steps."""

    proposal: Proposal
    """The rest of the model's answer."""

    schema_version: str
    """The version of this file's schema, ``"MAJOR.MINOR"``."""

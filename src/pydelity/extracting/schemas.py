"""Page extraction's data: the model's answer, the verifier's verdict, the page file.

`PageAnswer` is what the extraction model answers for one page, and `VerifierVerdict`
what the verifier model answers about it. Like the survey's answer, they use only
strings, integers, booleans, enums, lists and objects, with no patterns or bounds, so
they fit both providers' structured output. Every item has the same fields, with the
fields its kind does not use set to null; `pydelity.extracting.validators` checks
which fields go with which kind, and everything else an answer could get partly
wrong.

The model gives boxes as ``[x0, y0, x1, y1]`` on a grid of 1000 units across and down
the upright page image, from its top-left corner, and names items with refs of its
own. The page file (``pages/<NNNN>.json``, `PageFile`) holds the items with IDs
pydelity assigns and boxes in PDF points on the displayed page, origin top left, as
the survey's regions and form fields are.

Output models accept fields they do not know, so a file written by a newer pydelity
with the same major ``schema_version`` still loads.
"""

# Standard Library
from datetime import datetime
from typing import Literal, Self

# Third Party Library
from pydantic import BaseModel, ConfigDict, model_validator

# Package Library
from pydelity.providers.profiles import Effort
from pydelity.review import CheckFailure, ExtractionCheckName, ReviewIssue
from pydelity.surveying.schemas import (
    Angle,
    Direction,
    FormField,
    ItemKind,
    ItemRole,
    Label,
    TextQuality,
)

# The order in which a page's columns of vertical text are read.
type ColumnOrder = Literal["left_to_right", "right_to_left"]

# The type of a field item: a text box or line, a checkbox, a radio button, a choice
# among options, or a signature.
type FieldItemType = Literal["text", "checkbox", "radio", "choice", "signature"]

# What kind of problem the verifier found.
type ProblemCategory = Literal[
    "missing",
    "extra",
    "merged",
    "split",
    "kind_or_role",
    "label",
    "reading_order",
    "box",
    "text",
    "table",
    "field",
    "container",
    "caption",
    "other",
]

# What the survey decided a repeated line is on a page: page furniture, content, or
# neither, when its answer did not say.
type RepeatedLineUse = Literal["artifact", "content", "unclassified"]

# Whether the items' text was compared with the page's text layer, and if not, why:
# the page has no text layer, its text layer is garbled, or the text layer and the
# items' text share too little to be relied on.
type TextComparison = Literal[
    "compared", "no_text_layer", "garbled_text_layer", "text_layer_mismatch"
]


class _Output(BaseModel):
    """Base for the models the model answers and the files pydelity writes."""

    model_config = ConfigDict(use_attribute_docstrings=True)


class AnswerContainer(_Output):
    """A bordered or shaded box on the page that holds items."""

    box: list[int]
    """The box's ``[x0, y0, x1, y1]`` on the 0-1000 grid of the page image."""

    container: str | None
    """The ref of the container this box sits inside, or null."""

    label: str
    """A label from the profile for the box."""

    ref: str
    """A short name of your own for the box, unique on the page, such as ``c1``."""


class AnswerEntry(_Output):
    """One item of a list."""

    level: int
    """How deeply the entry is nested: 0 for the top level."""

    marker: str | None
    """The entry's bullet or number as printed, such as ``3.`` or ``b)``; null when
    there is none."""

    text: str
    """The entry's text as printed."""


class AnswerFigure(_Output):
    """A picture, chart, diagram, photo or other image on the page."""

    description: str
    """What the figure shows, in the language of the page's text."""

    text: str | None
    """Any text inside the figure, as printed; null when there is none."""


class FieldContent(_Output):
    """A form field: a place on a form for a value, a mark or a signature."""

    checked: bool | None
    """Whether a checkbox or radio button is marked; null for other fields."""

    field_type: FieldItemType
    """The field's type."""

    fillable_name: str | None
    """The name of the PDF's fillable form field this is, as listed with the page;
    null on a form that is only printed or scanned."""

    options: list[str]
    """The choices of a choice field, as printed; empty for other fields."""

    prompt: str | None
    """The field's printed label or question, such as ``Name``; null when it has
    none."""

    value: str | None
    """The value filled in or written on the field, as it appears; null when it is
    empty."""


class TableCell(_Output):
    """One cell of a table. A cell covered by another cell's span is left out."""

    col_span: int
    """How many columns the cell spans: 1 for one column."""

    row_span: int
    """How many rows the cell spans: 1 for one row."""

    text: str | None
    """The cell's text as printed; null when the cell is empty."""


class Table(_Output):
    """A table: rows of cells, with spans as in HTML."""

    header_rows: int
    """How many rows at the top are header rows."""

    rows: list[list[TableCell]]
    """The rows from top to bottom, each with its cells in reading order."""


class AnswerItem(_Output):
    """One item on the page, such as a paragraph, a heading, a list or a table."""

    box: list[int]
    """The item's ``[x0, y0, x1, y1]`` on the 0-1000 grid of the page image."""

    caption_of: str | None
    """For a caption, the ref of the item it captions; null for every other item."""

    container: str | None
    """The ref of the container the item sits inside, or null."""

    entries: list[AnswerEntry] | None
    """A list's entries in reading order; null for other kinds."""

    field: FieldContent | None
    """A field's content; null for other kinds."""

    figure: AnswerFigure | None
    """A figure's content; null for other kinds."""

    kind: ItemKind
    """What kind of content the item holds."""

    label: str
    """A label from the profile whose role and kinds match the item."""

    language: str | None
    """The BCP-47 tag of the language of the item's text, such as ``en`` or ``ar``;
    null when the item has no text."""

    latex: str | None
    """A formula in LaTeX; null for other kinds."""

    ref: str
    """A short name of your own for the item, unique on the page, such as ``t1``."""

    role: ItemRole
    """The role the item plays on the page."""

    table: Table | None
    """A table's content; null for other kinds."""

    text: str | None
    """The text of a text, code or formula item, as printed; null for other kinds."""


class Container(_Output):
    """A bordered or shaded box on the page that holds items."""

    bbox: list[float]
    """The box's ``[x0, y0, x1, y1]`` in points on the displayed page."""

    container: str | None
    """The ID of the container this box sits inside, or ``None``."""

    id: str
    """The container's ID, such as ``p0003-c01``: the page index and its position
    among the page's containers."""

    label: str
    """The container's label from the profile."""


class Entry(_Output):
    """One item of a list."""

    id: str
    """The entry's ID: its list's ID and its position in the list from 1, such as
    ``p0003-007.2``."""

    level: int
    """How deeply the entry is nested: 0 for the top level."""

    marker: str | None
    """The entry's bullet or number as printed, or ``None``."""

    text: str
    """The entry's text as printed."""


class ExtractionCheckResult(_Output):
    """The result of one check on the page's kept answer."""

    attempts: int
    """How many answers were checked: 1 plus the retries used."""

    failures: list[CheckFailure]
    """The problems the check found in the kept answer. A failure about one item
    names it in ``details``."""

    name: ExtractionCheckName
    """The check."""

    passed: bool
    """Whether the kept answer passed: ``failures`` is empty."""


class ExtractionSettings(_Output):
    """The page extraction settings a page's result depends on."""

    check_retries: int
    """How many times a model could answer again after failing the checks."""

    effort: Effort
    """How hard the models thought before answering."""

    max_output_tokens: int
    """The most tokens one model answer could contain, thinking included."""


class Figure(_Output):
    """A picture, chart, diagram, photo or other image."""

    crop: str
    """The figure's image, cut from the page: its path relative to the output folder,
    such as ``figures/p0003-004.png``."""

    description: str
    """What the figure shows."""

    text: str | None
    """Any text inside the figure, as printed, or ``None``."""


class Item(_Output):
    """One item on the page, in the page file."""

    bbox: list[float]
    """The item's ``[x0, y0, x1, y1]`` in points on the displayed page."""

    caption_of: str | None
    """For a caption, the ID of the item it captions; ``None`` for other items."""

    container: str | None
    """The ID of the container the item sits inside, or ``None``."""

    entries: list[Entry] | None
    """A list's entries in reading order; ``None`` for other kinds."""

    field: FieldContent | None
    """A field's content; ``None`` for other kinds."""

    figure: Figure | None
    """A figure's content; ``None`` for other kinds."""

    id: str
    """The item's ID, such as ``p0003-007``: the page index and its position in
    reading order from 1. The same extraction always gives the same IDs."""

    kind: ItemKind
    """What kind of content the item holds."""

    label: str
    """The item's label from the profile."""

    language: str | None
    """The BCP-47 tag of the item's text, in standard form; ``None`` when the item has
    no text."""

    latex: str | None
    """A formula in LaTeX; ``None`` for other kinds."""

    role: ItemRole
    """The role the item plays on the page."""

    table: Table | None
    """A table's content; ``None`` for other kinds."""

    text: str | None
    """The text of a text, code or formula item, as printed; ``None`` for other
    kinds."""


class PageAnswer(_Output):
    """The model's reading of one page: its items in reading order."""

    column_order: ColumnOrder | None
    """On a page written top to bottom, the order its columns are read in; null on
    other pages."""

    containers: list[AnswerContainer]
    """The bordered or shaded boxes on the page; empty when there are none."""

    items: list[AnswerItem]
    """Every item on the page, in reading order."""


class PageRepeatedLine(_Output):
    """A repeated line that appears on the page, with what the survey decided it is."""

    id: str
    """The line's ID in ``pdf_facts.json``, such as ``R1``."""

    normalized: str
    """The form the line is compared in: Unicode NFKC, case-folded, whitespace
    collapsed, each run of digits written as ``#``."""

    text: str
    """The line as printed where it first appears in the PDF."""

    use: RepeatedLineUse
    """Whether the survey decided the line is page furniture (``artifact``), content
    (``content``), or neither (``unclassified``)."""


class PageContext(_Output):
    """What one page's requests are made from and its answers are checked against."""

    form_fields: list[FormField]
    """The PDF's fillable form fields on the page, with boxes in points on the
    displayed page; empty when there are none or the form could not be read."""

    height_pt: float
    """The displayed page's height in points."""

    instructions: str | None
    """The user's page extraction instructions, if any."""

    labels: list[Label]
    """The profile's labels."""

    languages: list[str]
    """The profile's languages, as BCP-47 tags in standard form."""

    page_count: int
    """The PDF's number of pages."""

    page_index: int
    """The page (0-based)."""

    repeated_lines: list[PageRepeatedLine]
    """The repeated lines that appear on the page."""

    rotation: Angle
    """The clockwise rotation, from the profile, that makes the page upright."""

    rotation_attribute: int
    """The page's rotation attribute in the PDF, in degrees."""

    text_quality: TextQuality
    """Whether the page's text layer is readable, as measured."""

    width_pt: float
    """The displayed page's width in points."""

    writing_direction: Direction
    """The page's writing direction, from the profile."""


class PageImageSize(_Output):
    """The size of the page image the models were sent."""

    height_px: int
    """Its height in pixels."""

    width_px: int
    """Its width in pixels."""


class RenderingSettings(_Output):
    """How page images and figure crops are made."""

    crop_dpi: int
    """The resolution of figure crops, in dots per inch."""

    jpeg_quality: int
    """The JPEG quality of page images, from 0 to 100."""

    max_dpi: int
    """The highest resolution of a page image, in dots per inch."""


class PageInputs(_Output):
    """What a page's extraction depends on, which its fingerprint covers."""

    context: PageContext
    """The page's context."""

    model: str
    """The model, as ``<provider>:<model-id>``."""

    pdf_sha256: str
    """The PDF's SHA-256 hex digest."""

    prompt_version: int
    """The version of the extraction and verifier prompts."""

    rendering: RenderingSettings
    """How the page image and the figure crops were made."""

    settings: ExtractionSettings
    """The page extraction settings used."""


class VerifierProblem(_Output):
    """A problem the verifier found in the extraction."""

    category: ProblemCategory
    """What kind of problem it is."""

    description: str
    """What is wrong and where, so that a person can find it."""

    item_ref: str | None
    """The ref of the item or container the problem is about; null when it is about
    no single one, such as a missing item."""


class VerifierVerdict(_Output):
    """The verifier's verdict on one page's extraction."""

    corrected: PageAnswer | None
    """The whole page extracted again with the problems fixed; null when the
    extraction passed or cannot be corrected."""

    passed: bool
    """Whether the extraction is faithful to the page, with nothing to fix."""

    problems: list[VerifierProblem]
    """The problems found; empty when the extraction passed."""

    @model_validator(mode="after")
    def _agree(self) -> Self:
        """Check that ``passed`` agrees with the problems and the correction.

        Returns
        -------
        Self
            The verdict.

        Raises
        ------
        ValueError
            If a passed verdict lists problems or a correction, or a failed verdict
            lists no problem.
        """

        if self.passed and (self.problems or self.corrected is not None):
            raise ValueError(
                "a verdict that passed has no problems and no corrected extraction"
            )
        if not self.passed and not self.problems:
            raise ValueError("a verdict that did not pass names at least one problem")
        return self


class PageVerification(_Output):
    """The verifier's review of the page's extraction."""

    attempts: int
    """How many verdicts the verifier gave: 1 plus the retries its correction used."""

    correction_applied: bool
    """Whether the verifier's corrected extraction replaced the extraction model's.
    A correction replaces it when it passes every check other than ``text_dropped``
    and ``text_added``."""

    correction_failures: list[ExtractionCheckResult]
    """The checks a correction that was not applied still failed; empty when it was
    applied or there was none."""

    verdict: VerifierVerdict
    """The verdict as the verifier gave it."""


class PageFile(_Output):
    """The contents of ``pages/<NNNN>.json``: one page's items and their checks."""

    checks: list[ExtractionCheckResult]
    """The result of each check on the kept answer, in the order the checks run."""

    column_order: ColumnOrder | None
    """On a page written top to bottom, the order its columns are read in; ``None``
    on other pages."""

    containers: list[Container]
    """The bordered or shaded boxes on the page."""

    extracted_at: datetime
    """When the page file was written (UTC)."""

    fingerprint: str
    """``sha256:`` fingerprint of ``inputs``; a matching file is reused."""

    height_pt: float
    """The displayed page's height in points."""

    image: PageImageSize
    """The size of the page image the models were sent."""

    inputs: PageInputs
    """What the page's extraction depends on."""

    issues: list[ReviewIssue]
    """The page's review issues: checks still failing on the kept answer, content no
    label fits, and verifier problems that were not corrected. Text differences
    from the stored text are listed unless the verifier passed the page or its
    correction was kept, so on a page no verifier reviewed every one is listed. The
    ``checks`` list keeps them either way."""

    items: list[Item]
    """The page's items, in reading order."""

    page_index: int
    """The page (0-based)."""

    page_number: int
    """The page's number from 1, as a PDF viewer shows it."""

    pydelity_version: str
    """The pydelity version that wrote the file."""

    rotation: Angle
    """The clockwise rotation applied to make the page upright for the models."""

    schema_version: str
    """The version of this file's schema, ``"MAJOR.MINOR"``."""

    text_comparison: TextComparison
    """Whether the items' text was compared with the page's text layer, and if not,
    why."""

    verification: PageVerification | None
    """The verifier's review; ``None`` when no verifier reviewed the page."""

    width_pt: float
    """The displayed page's width in points."""

    writing_direction: Direction
    """The page's writing direction."""

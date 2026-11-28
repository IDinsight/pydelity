"""Page-break verification's data: the verdicts and the verdict file.

`BreakVerdict` is what the judge, page-break verification's model, answers for the
break between two consecutive pages, and `BreakVerifierVerdict` what the verifier
answers about that verdict. Like the other steps' answers, they use only strings,
integers, booleans, enums, lists and objects, with no patterns or bounds, so they fit
both providers' structured output. Every piece has the same fields, with the fields
its join does not use set to null. `pydelity.verifying.validators` checks which
fields go with which join, and what else code can decide about a verdict.

A verdict names items, list entries and containers by the IDs in the two pages' page
files. The verdict file (``page_breaks/<NNNN>-<NNNN>.json``, `BreakFile`) keeps the
verdict with its checks, hints, review issues and what it was made from.

Output models accept fields they do not know, so a file written by a newer pydelity
with the same major ``schema_version`` still loads.
"""

# Standard Library
from datetime import datetime
from typing import Literal, Self

# Third Party Library
from pydantic import BaseModel, ConfigDict, model_validator

# Package Library
from pydelity.extracting.schemas import RenderingSettings
from pydelity.providers.profiles import Effort
from pydelity.review import BreakCheckName, BreakHintName, CheckFailure, ReviewIssue
from pydelity.surveying.schemas import StartMarker

# What kind of problem the verifier found in a verdict.
type BreakProblemCategory = Literal[
    "continues",
    "piece",
    "join",
    "header_rows",
    "repeated_items",
    "markers",
    "containers",
    "other",
]

# How a continuing piece joins the later page's content to the earlier page's.
# ``continue_text`` joins a text item to a text item, or a code item to a code item.
# ``continue_entry`` joins text where at least one end is a list entry. ``new_entry``
# continues a list with a new entry, from the list on the earlier page, or from a text
# item when page extraction read the list's part on that page as text.
# ``append_rows`` continues a table with new rows. ``merge_split_row`` merges the row
# the break cuts with the later page's first row after any repeated header rows.
type Join = Literal[
    "continue_text",
    "continue_entry",
    "new_entry",
    "append_rows",
    "merge_split_row",
]

# How a verdict was made: by a model, or without a request because a page of the
# break has no content items, so nothing can continue.
type Judgment = Literal["model", "no_content"]

# How two pieces of text join across the break: with a space, with nothing between
# them, by removing the hyphen at the end of the earlier piece, or, for code, with a
# line break. ``repeat`` is only for the cells of a split row: the later cell only
# repeats the text of the cell above it, so the text is kept once.
type TextJoin = Literal["space", "no_space", "dehyphenate", "newline", "repeat"]


class _Output(BaseModel):
    """Base for the models the model answers and the files pydelity writes."""

    model_config = ConfigDict(use_attribute_docstrings=True)


class BreakCheckResult(_Output):
    """The result of one check on the break's kept verdict."""

    attempts: int
    """How many verdicts were checked: 1 plus the retries used."""

    failures: list[CheckFailure]
    """The problems the check found in the kept verdict. A review issue made from a
    failure names its item by ID in ``item_id``."""

    name: BreakCheckName
    """The check."""

    passed: bool
    """Whether the kept verdict passed: ``failures`` is empty."""


class BreakContext(_Output):
    """What a break's requests are made from besides its two pages."""

    continuation_notes: list[str]
    """The survey's notes on how content continues from one page to the next."""

    instructions: str | None
    """The user's page-break verification instructions, if any."""

    page_count: int
    """The PDF's number of pages."""

    start_markers: list[StartMarker]
    """The survey's start markers: text that marks where a new unit of content
    starts."""


class BreakHintResult(_Output):
    """How the break's kept verdict compares with one hint."""

    differences: list[CheckFailure]
    """Where the kept verdict differs from what the survey found; empty when it
    agrees. A review issue made from a difference names its item by ID in
    ``item_id``."""

    name: BreakHintName
    """The hint."""


class BreakPage(_Output):
    """One page of a break and the page file the verdict was made from."""

    page_file_sha256: str
    """``sha256:`` digest of the page file's bytes, as written."""

    page_index: int
    """The page (0-based)."""


class BreakProblem(_Output):
    """A problem the verifier found in a verdict."""

    category: BreakProblemCategory
    """What kind of problem it is."""

    description: str
    """What is wrong and where, so that a person can find it."""

    item: str | None
    """The ID of the item or container on either page the problem is about; null
    when it is about no single one, such as content that continues but is missing
    from the verdict."""


class BreakSettings(_Output):
    """The page-break verification settings a verdict depends on."""

    check_retries: int
    """How many times a model could answer again after failing the checks."""

    effort: Effort
    """How hard the models thought before answering."""

    max_output_tokens: int
    """The most tokens one model answer could contain, thinking included."""


class BreakInputs(_Output):
    """What a break's verdict depends on, which its fingerprint covers."""

    context: BreakContext
    """What the break's requests are made from besides its two pages."""

    earlier: BreakPage
    """The page before the break and its page file."""

    later: BreakPage
    """The page after the break and its page file."""

    model: str
    """The model, as ``<provider>:<model-id>``."""

    pdf_sha256: str
    """The PDF's SHA-256 hex digest."""

    prompt_version: int
    """The version of page-break verification's prompts."""

    rendering: RenderingSettings
    """How the page images were made."""

    settings: BreakSettings
    """The page-break verification settings used."""


class ContinuationMarker(_Output):
    """Words or symbols on the continued unit that say it continues."""

    cell: int | None
    """When a table cell carries the marker, the cell's position in its row, from 0;
    null otherwise."""

    item: str
    """The ID of the item on the later page that carries the marker."""

    row: int | None
    """When a table cell carries the marker, the row's position among the table's
    rows, from 0; null otherwise."""

    text: str
    """The marker, as printed."""


class ContinuingContainer(_Output):
    """A bordered or shaded box that continues across the break."""

    earlier: str
    """The box's container ID on the earlier page."""

    later: str
    """The box's container ID on the later page."""


class ContinuingPiece(_Output):
    """A piece of content that carries on from the earlier page to the later page."""

    cell_joins: list[TextJoin | None] | None
    """For ``merge_split_row``, one value per cell of the later page's merged row
    (its first row after the repeated header rows), in the row's cell order: how that
    cell's text joins the text of the cell above it on the earlier page (``space``,
    ``no_space`` or ``dehyphenate``), ``repeat`` when the later cell only repeats the
    earlier cell's text, such as a row label printed again, so that the text is kept
    once, or null when either cell has no text. Null for every other join."""

    earlier_entry: str | None
    """When the piece ends in a list entry on the earlier page, that entry's ID; null
    otherwise."""

    earlier_item: str
    """The ID of the item where the piece ends on the earlier page."""

    join: Join
    """How the piece joins across the break."""

    later_entry: str | None
    """When the piece starts in a list entry on the later page, that entry's ID; null
    otherwise."""

    later_item: str
    """The ID of the item where the piece starts on the later page."""

    markers: list[ContinuationMarker]
    """Words or symbols on the continued unit on the later page that say it
    continues; empty when there are none."""

    repeated_header_rows: int | None
    """For ``append_rows`` and ``merge_split_row``, how many rows at the top of the
    later page's table repeat the earlier table's header, 0 when none do; null for
    every other join."""

    repeated_items: list[str]
    """The IDs of items on the later page, before the continued unit, that repeat
    what the earlier page printed for it, such as a repeated title; empty when there
    are none."""

    text_join: TextJoin | None
    """For ``continue_text`` and ``continue_entry``, how the two pieces of text join:
    ``space``, ``no_space`` or ``dehyphenate``, or ``newline`` between code items.
    Null for every other join."""


class BreakVerdict(_Output):
    """A verdict on one break: whether content continues across it, and how."""

    containers: list[ContinuingContainer]
    """Each bordered or shaded box that continues across the break, also when the
    content inside it starts a new unit on the later page; empty when none does."""

    continues: bool
    """Whether any content carries on from the earlier page to the later page."""

    pieces: list[ContinuingPiece]
    """Each piece of content that carries on across the break; empty when nothing
    continues."""

    reason: str
    """Why, in a sentence or two, quoting the text that decides it."""


class BreakVerifierVerdict(_Output):
    """The verifier's verdict on one break's verdict."""

    corrected: BreakVerdict | None
    """The whole verdict given again with the problems fixed; null when the verdict
    passed or cannot be corrected."""

    passed: bool
    """Whether the verdict is right, with nothing to fix."""

    problems: list[BreakProblem]
    """The problems found; empty when the verdict passed."""

    @model_validator(mode="after")
    def _agree(self) -> Self:
        """Check that ``passed`` agrees with the problems and the correction.

        Returns
        -------
        Self
            The verifier's verdict.

        Raises
        ------
        ValueError
            If a passed verdict lists problems or a correction, or a failed verdict
            lists no problem.
        """

        if self.passed and (self.problems or self.corrected is not None):
            raise ValueError(
                "a verdict that passed has no problems and no corrected verdict"
            )
        if not self.passed and not self.problems:
            raise ValueError("a verdict that did not pass names at least one problem")
        return self


class BreakVerification(_Output):
    """The verifier's review of the break's verdict."""

    attempts: int
    """How many verdicts the verifier gave: 1 plus the retries its correction used."""

    correction_applied: bool
    """Whether the verifier's corrected verdict replaced the judge's. A correction
    replaces it when it passes every check, whatever its hint differences."""

    correction_failures: list[BreakCheckResult]
    """The checks a correction that was not applied still failed; empty when it was
    applied or there was none."""

    verdict: BreakVerifierVerdict
    """The verdict as the verifier gave it."""


class BreakFile(_Output):
    """The contents of ``page_breaks/<NNNN>-<NNNN>.json``: one break's verdict."""

    checks: list[BreakCheckResult]
    """The result of each check on the kept verdict, in the order the checks run."""

    earlier_page_index: int
    """The page before the break (0-based)."""

    fingerprint: str
    """``sha256:`` fingerprint of ``inputs``; a matching file is reused."""

    hints: list[BreakHintResult]
    """Each hint's differences on the kept verdict, in the order the hints run,
    whether or not the review list shows them."""

    inputs: BreakInputs
    """What the verdict depends on."""

    issues: list[ReviewIssue]
    """The break's review issues: checks still failing on the kept verdict, hint
    differences, and verifier problems that were not corrected. Hint differences are
    listed unless the verifier passed the verdict or its correction was kept, so on a
    break no verifier reviewed every one is listed. The ``hints`` list keeps them
    either way."""

    judged_at: datetime
    """When the verdict file was written (UTC)."""

    judgment: Judgment
    """How the verdict was made: ``model`` when a model judged the break, or
    ``no_content`` when a page of the break has no content items, so nothing can
    continue and no request was made."""

    later_page_index: int
    """The page after the break (0-based): ``earlier_page_index`` plus 1."""

    pydelity_version: str
    """The pydelity version that wrote the file."""

    schema_version: str
    """The version of this file's schema, ``"MAJOR.MINOR"``."""

    verdict: BreakVerdict
    """The kept verdict: the judge's, or the verifier's correction when it was
    kept."""

    verification: BreakVerification | None
    """The verifier's review; ``None`` when no verifier reviewed the verdict."""

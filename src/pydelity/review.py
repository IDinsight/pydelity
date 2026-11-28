"""The review list: problems a person should check, from every step.

A step's checks find problems in a model's answer, and its hints compare the answer
with what pydelity measured or the survey found. Checks still failing on the kept
answer, and hint differences that no verifier accepted, become review issues. Each
step saves its own issues with its output, and ``run.json`` lists them all. The check
and hint names are part of the ``run.json`` contract.
"""

# Standard Library
from typing import Literal

# Third Party Library
from pydantic import BaseModel, ConfigDict

# Page-break verification's checks on each verdict, in the order they run. A failure
# may send the verdict back.
type BreakCheckName = Literal[
    "ids",
    "continues",
    "duplicates",
    "joins",
    "furniture",
    "header_rows",
    "repeats",
    "markers",
]

# Page-break verification's comparison of the verifier's verdict for a break with the
# kept verdict. Each difference between the two is a review issue.
type BreakComparisonName = Literal["verdicts_differ"]

# Page-break verification's hints, the comparisons of each verdict with what the
# survey found. A difference never sends the verdict back.
type BreakHintName = Literal["start_markers"]

# Page extraction's checks on each answer, in the order they run. A failure may send
# the answer back.
type ExtractionCheckName = Literal[
    "labels",
    "content",
    "languages",
    "boxes",
    "containers",
    "captions",
]

# Page extraction's hints, the comparisons of each answer with what code measured or
# the survey found about the page, in the order they run. A difference never sends
# the answer back.
type ExtractionHintName = Literal[
    "reading_order",
    "artifacts",
    "form_fields",
    "text_dropped",
    "text_added",
]

# Page extraction's other review issue, which is recorded without sending the answer
# back: content that no label in the profile fits.
type ExtractionIssueName = Literal["no_matching_label"]

# The name of what found a review issue, in any step.
type IssueName = (
    BreakCheckName
    | BreakComparisonName
    | BreakHintName
    | ExtractionCheckName
    | ExtractionHintName
    | ExtractionIssueName
    | SurveyCheckName
    | SurveyHintName
    | VerifierIssueName
)

# The steps whose problems go on the review list.
type StepName = Literal["survey", "extraction", "page_breaks"]

# The survey's checks, C1 to C7 in order.
type SurveyCheckName = Literal[
    "labels",
    "regions",
    "rotation",
    "page_numbering",
    "artifacts",
    "writing_direction",
    "languages",
]

# The survey's hints, the comparisons of each answer with what the probe measured, in
# the order they run. A difference never sends the answer back.
type SurveyHintName = Literal["rotation_differs", "page_number_differs"]

# A problem a step's verifier found whose correction was not kept, in any step.
type VerifierIssueName = Literal["verifier"]


class _Output(BaseModel):
    """Base for the models stored in output files."""

    model_config = ConfigDict(use_attribute_docstrings=True)


class CheckFailure(_Output):
    """A problem a check found in a model's answer, or a difference from a hint."""

    details: dict[str, object]
    """The values the problem is about. A survey check gives the proposed value and,
    where it applies, what it was checked against, such as
    ``{"proposed": 9, "page_count": 6}``, and a survey hint gives the measured value
    and the profile's, such as ``{"measured": 90, "profile": 0}``. A page extraction
    check or hint gives the ref that the model's answer gave the item or container,
    or ``None`` when no single one applies, such as ``{"item_ref": "t3"}``. That ref
    comes from the answer, and the page file's items have IDs instead. A page-break
    verification check or hint gives the IDs of the item, list entry or container it
    is about, and the row and cell of a table cell, such as ``{"item": "p0004-002"}``
    or ``{"cell": 1, "item": "p0004-002", "row": 0}``. A difference between two
    verdicts for the same break gives the ``field`` that differs, each verdict's value
    as ``kept`` and ``verifier``, the ``item`` and ``entry`` where the piece ends on
    the earlier page, and the ``cell`` of a cell join, such as
    ``{"entry": "p0004-002.3", "field": "join", "item": "p0004-002", "kept":
    "continue_entry", "verifier": "new_entry"}``."""

    message: str
    """What is wrong or differs, starting with the name of the check, hint or
    comparison."""

    page_index: int | None
    """The page the problem is on, or ``None`` when no single page applies."""


class ReviewIssue(_Output):
    """A problem a person should review.

    It comes from a check that still failed on a step's kept answer, from a
    difference between the kept answer and a hint, or from a problem found another
    way, such as by a step's verifier.
    """

    check: IssueName
    """What found the problem: a check, a hint or another source. ``step`` says
    whose, since two steps can have checks and hints of the same name."""

    details: dict[str, object]
    """The values the problem is about. A survey hint gives values such as
    ``{"measured": 90, "profile": 0}``, and a check gives its failure's ``details``,
    such as ``{"item_ref": "t3"}`` on a page or ``{"item": "p0004-002"}`` on a page
    break. A ``no_matching_label`` issue gives the ``kind`` and ``role`` that no
    label fits, with the items' refs and IDs (``item_refs``, ``item_ids``). A
    ``verifier`` issue gives the problem's ``category``, with its ``item_ref`` on a
    page and its ``item`` on a page break. A ``verdicts_differ`` issue gives the
    difference's ``details``, with the ``field``, the ``kept`` and ``verifier``
    values, and the ``item``, ``entry`` and ``cell`` where they apply."""

    item_id: str | None
    """The item the problem is about, or ``None`` when no single item applies."""

    message: str
    """What is wrong."""

    page_index: int | None
    """The page the problem is on, or ``None`` when no single page applies. For
    page-break verification, it is the page before the break."""

    step: StepName
    """The step whose check found the problem."""

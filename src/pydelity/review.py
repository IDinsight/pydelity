"""The review list: problems a person should check, from every step.

A step's checks find problems in a model's answer. Problems still left in the accepted
answer, and differences between the answer and what pydelity measured, become review
issues. Each step saves its own issues with its output, and ``run.json`` lists them
all. The check names are part of the ``run.json`` contract.
"""

# Standard Library
from typing import Literal

# Third Party Library
from pydantic import BaseModel, ConfigDict

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
    ExtractionCheckName
    | ExtractionHintName
    | ExtractionIssueName
    | SurveyCheckName
    | SurveyComparisonName
    | VerifierIssueName
)

# The steps whose problems go on the review list.
type StepName = Literal["survey", "extraction"]

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

# The survey's comparisons of the accepted answer with the facts, whose differences
# are review issues.
type SurveyComparisonName = Literal["rotation_differs", "page_number_differs"]

# A problem a step's verifier found whose correction was not kept, in either step.
type VerifierIssueName = Literal["verifier"]


class _Output(BaseModel):
    """Base for the models stored in output files."""

    model_config = ConfigDict(use_attribute_docstrings=True)


class CheckFailure(_Output):
    """One problem a check found in a model's answer."""

    details: dict[str, object]
    """The values the problem is about. A survey check gives the proposed value and,
    where it applies, what it was checked against, such as
    ``{"proposed": 9, "page_count": 6}``. A page extraction check gives the ref that
    the model's answer gave the item or container, or ``None`` when no single one
    applies, such as ``{"item_ref": "t3"}``. That ref comes from the answer, and the
    page file's items have IDs instead."""

    message: str
    """What is wrong, starting with the check's name."""

    page_index: int | None
    """The page the problem is on, or ``None`` when no single page applies."""


class ReviewIssue(_Output):
    """A problem a person should review.

    It comes from a check that still failed on a step's accepted answer, from a
    difference between the accepted answer and what pydelity measured, or from a
    problem found another way, such as by a step's verifier.
    """

    check: IssueName
    """What found the problem: a check, a comparison or another source. ``step`` says
    whose, since two steps can have checks of the same name."""

    details: dict[str, object]
    """The values the problem is about. A survey comparison gives values such as
    ``{"measured": 90, "profile": 0}``, and a check gives its failure's ``details``,
    such as ``{"item_ref": "t3"}`` on a page. A ``no_matching_label`` issue gives the
    ``kind`` and ``role`` that no label fits, with the items' refs and IDs
    (``item_refs``, ``item_ids``). A ``verifier`` issue gives the problem's
    ``category``, and on a page its ``item_ref``."""

    item_id: str | None
    """The item the problem is about, or ``None`` when no single item applies."""

    message: str
    """What is wrong."""

    page_index: int | None
    """The page the problem is on, or ``None`` when no single page applies."""

    step: StepName
    """The step whose check found the problem."""

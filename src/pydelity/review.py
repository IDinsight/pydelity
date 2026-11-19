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


class _Output(BaseModel):
    """Base for the models stored in output files."""

    model_config = ConfigDict(use_attribute_docstrings=True)


class CheckFailure(_Output):
    """One problem a check found in a model's answer."""

    details: dict[str, object]
    """The proposed value and, where it applies, what it was checked against, such as
    ``{"proposed": 9, "page_count": 6}``."""

    message: str
    """What is wrong, starting with the check's name."""

    page_index: int | None
    """The page the problem is on, or ``None`` when no single page applies."""


class ReviewIssue(_Output):
    """A problem a person should review.

    It comes from a check that still failed on a step's accepted answer, or from a
    difference between the accepted answer and what pydelity measured.
    """

    check: SurveyCheckName | SurveyComparisonName
    """The check or comparison that found the problem."""

    details: dict[str, object]
    """The values the problem is about, such as ``{"measured": 90, "profile": 0}``."""

    item_id: str | None
    """The item the problem is about, or ``None`` when no single item applies."""

    message: str
    """What is wrong."""

    page_index: int | None
    """The page the problem is on, or ``None`` when no single page applies."""

    step: StepName
    """The step whose check found the problem."""

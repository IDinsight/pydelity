"""The survey's checks on the model's answer, and its comparison with the facts.

Pydantic checks the answer's shape. Checks C1 to C7 test that the answer is well
formed and complete: labels and regions fit together, page ranges lie inside the PDF
without overlapping, every repeated line is accounted for and every language tag is
valid. They use the facts only for the page count and the repeated-line IDs. Each
check returns every failure it finds, one per affected page, so one retry message can
name every problem and the last attempt can record them all.

The model's reading of the PDF takes precedence over the measured facts, so no check
compares the answer with a measured value. Instead, `compare_with_facts` runs once on
the accepted answer and records each page whose rotation or page number differs from
what the probe measured, for a person to review. The checks and the comparison use
page indexes, values and IDs only, never word lists.
"""

# Standard Library
from collections import Counter
from collections.abc import Callable, Sequence
from typing import Protocol

# Package Library
from pydelity.config.schemas import is_language_tag
from pydelity.review import (
    CheckFailure,
    ReviewIssue,
    SurveyCheckName,
    SurveyComparisonName,
)
from pydelity.surveying.schemas import (
    CheckResult,
    Facts,
    PageNumberingRange,
    RotationRange,
    SurveyAnswer,
)

# Checks the answer against the facts and returns every failure found.
type Check = Callable[[SurveyAnswer, Facts], list[CheckFailure]]


class _PageRange(Protocol):
    """A range of pages, from its first to its last index, inclusive."""

    @property
    def first_page_index(self) -> int:
        """The first page of the range."""

    @property
    def last_page_index(self) -> int:
        """The last page of the range, inclusive."""


def _covering[RangeT: _PageRange](
    ranges: Sequence[RangeT], *, page: int, page_count: int
) -> RangeT | None:
    """Find the first range that covers a page, ignoring ranges outside the PDF.

    Parameters
    ----------
    ranges
        The answer's ranges, in its order.
    page
        The page index.
    page_count
        The PDF's number of pages.

    Returns
    -------
    RangeT | None
        The range, or ``None`` when no range inside the PDF covers the page.
    """

    for page_range in ranges:
        first, last = page_range.first_page_index, page_range.last_page_index
        if 0 <= first <= last < page_count and first <= page <= last:
            return page_range
    return None


def _failure(
    check: SurveyCheckName,
    message: str,
    *,
    details: dict[str, object],
    page_index: int | None,
) -> CheckFailure:
    """Make a failure whose message starts with the check's name.

    Parameters
    ----------
    check
        The check that failed.
    message
        What is wrong.
    details
        The proposed value and, where it applies, what it was checked against.
    page_index
        The page the problem is on, or ``None``.

    Returns
    -------
    CheckFailure
        The failure.
    """

    return CheckFailure(
        details=details, message=f"{check}: {message}", page_index=page_index
    )


def _issue(
    comparison: SurveyComparisonName,
    message: str,
    *,
    details: dict[str, object],
    page_index: int,
) -> ReviewIssue:
    """Make a review issue for a difference from the facts.

    Parameters
    ----------
    comparison
        The comparison that found the difference.
    message
        The page, the measured value and the profile's value.
    details
        The measured and profile values.
    page_index
        The page that differs.

    Returns
    -------
    ReviewIssue
        The issue, with its message starting with the comparison's name.
    """

    return ReviewIssue(
        check=comparison,
        details=details,
        item_id=None,
        message=f"{comparison}: {message}",
        page_index=page_index,
        step="survey",
    )


def _page_number_issues(answer: SurveyAnswer, facts: Facts) -> list[ReviewIssue]:
    """List the pages whose measured printed number the profile does not give.

    Parameters
    ----------
    answer
        The accepted answer.
    facts
        The measured facts.

    Returns
    -------
    list[ReviewIssue]
        One ``page_number_differs`` issue per differing page.
    """

    issues = []
    page_count = len(facts.pages)
    for page in facts.pages:
        measured = page.printed_number
        if measured is None or measured.value is None:
            continue
        numbering = _covering(
            answer.page_numbering, page=page.index, page_count=page_count
        )
        profile = _profile_number(numbering, page=page.index)
        if profile == measured.value:
            continue
        where = (
            f"page label {measured.text!r}"
            if measured.source == "page_label"
            else f"page text {measured.text!r}"
        )
        gives = "no number" if profile is None else f"{profile}"
        issues.append(
            _issue(
                "page_number_differs",
                f"page {page.index} has the number {measured.value} in its {where}, "
                f"but the profile gives {gives}",
                details={
                    "measured": measured.value,
                    "profile": profile,
                    "source": measured.source,
                },
                page_index=page.index,
            )
        )
    return issues


def _pages(page_range: _PageRange) -> range:
    """Return the page indexes a range covers.

    Parameters
    ----------
    page_range
        The range.

    Returns
    -------
    range
        From the first page to the last, inclusive.
    """

    return range(page_range.first_page_index, page_range.last_page_index + 1)


def _profile_number(numbering: PageNumberingRange | None, *, page: int) -> int | None:
    """Return the number the profile gives a page.

    Parameters
    ----------
    numbering
        The range that covers the page, if any.
    page
        The page index.

    Returns
    -------
    int | None
        The page index plus the range's offset for an arabic or roman range with an
        offset, otherwise ``None``.
    """

    if (
        numbering is None
        or numbering.style not in {"arabic", "roman"}
        or numbering.offset is None
    ):
        return None
    return page + numbering.offset


def _range_failures(
    check: SurveyCheckName, ranges: Sequence[_PageRange], page_count: int
) -> list[CheckFailure]:
    """Check that page ranges lie inside the PDF and do not overlap.

    Parameters
    ----------
    check
        The check the ranges belong to.
    ranges
        The answer's ranges.
    page_count
        The PDF's number of pages.

    Returns
    -------
    list[CheckFailure]
        One failure per range outside the PDF, and one per page that several ranges
        cover.
    """

    failures = []
    inside = []
    for page_range in ranges:
        first = page_range.first_page_index
        last = page_range.last_page_index
        if 0 <= first <= last < page_count:
            inside.append(page_range)
            continue
        failures.append(
            _failure(
                check,
                f"range {first}-{last} is not inside the PDF's pages 0-"
                f"{page_count - 1}, or ends before it starts",
                details={
                    "page_count": page_count,
                    "proposed": {"first_page_index": first, "last_page_index": last},
                },
                page_index=None,
            )
        )

    covering = Counter(page for page_range in inside for page in _pages(page_range))
    for page, count in sorted(covering.items()):
        if count > 1:
            failures.append(
                _failure(
                    check,
                    f"page {page} is in {count} ranges; ranges must not overlap",
                    details={"proposed": count},
                    page_index=page,
                )
            )
    return failures


def _rotation_issues(answer: SurveyAnswer, facts: Facts) -> list[ReviewIssue]:
    """List the pages whose confident measured rotation the profile does not give.

    Parameters
    ----------
    answer
        The accepted answer.
    facts
        The measured facts.

    Returns
    -------
    list[ReviewIssue]
        One ``rotation_differs`` issue per differing page.
    """

    issues = []
    page_count = len(facts.pages)
    for page in facts.pages:
        measured = page.orientation.dominant
        if not page.orientation.confident or measured is None:
            continue
        turn: RotationRange | None = _covering(
            answer.rotation, page=page.index, page_count=page_count
        )
        profile = 0 if turn is None else turn.degrees
        if profile == measured:
            continue
        issues.append(
            _issue(
                "rotation_differs",
                f"page {page.index} needs {measured} degrees by its measured text "
                f"angle, but the profile gives {profile}",
                details={"measured": measured, "profile": profile},
                page_index=page.index,
            )
        )
    return issues


def check_artifacts(answer: SurveyAnswer, facts: Facts) -> list[CheckFailure]:
    """C5: every repeated line is accounted for exactly once.

    Each repeated line ID appears once, in an artifact or in ``non_artifact_lines``,
    and no other ID appears.

    Parameters
    ----------
    answer
        The model's answer.
    facts
        The measured facts, for the repeated lines.

    Returns
    -------
    list[CheckFailure]
        One failure per missing, repeated or unknown ID.
    """

    proposed = [i for artifact in answer.artifacts for i in artifact.repeated_line_ids]
    proposed += [line.repeated_line_id for line in answer.non_artifact_lines]
    counts = Counter(proposed)
    failures = []
    for line in facts.repeated_lines:
        count = counts[line.id]
        if count == 1:
            continue
        message = (
            f"repeated line {line.id} ({line.text!r}) is in no artifact and not in "
            "non_artifact_lines"
            if count == 0
            else f"repeated line {line.id} is listed {count} times; list it once"
        )
        failures.append(
            _failure(
                "artifacts",
                message,
                details={"proposed": count, "repeated_line_id": line.id},
                page_index=None,
            )
        )

    known = {line.id for line in facts.repeated_lines}
    for unknown in sorted(set(proposed) - known):
        failures.append(
            _failure(
                "artifacts",
                f"{unknown} is not a repeated line the facts list",
                details={"proposed": unknown},
                page_index=None,
            )
        )
    return failures


def check_labels(answer: SurveyAnswer, facts: Facts) -> list[CheckFailure]:
    """C1: label names are present and unique, labels have kinds, regions use them.

    Names compare regardless of case. A region may also use ``other``, which pydelity
    adds to every profile.

    Parameters
    ----------
    answer
        The model's answer.
    facts
        The measured facts, for the page count.

    Returns
    -------
    list[CheckFailure]
        One failure per empty name, repeated name, label without kinds, and region
        whose label does not exist.
    """

    failures = []
    names = Counter(label.name.strip().casefold() for label in answer.labels)
    for name, count in names.items():
        if not name:
            failures.append(
                _failure(
                    "labels",
                    f"{count} label(s) have an empty name",
                    details={"proposed": ""},
                    page_index=None,
                )
            )
        elif count > 1:
            failures.append(
                _failure(
                    "labels",
                    f"the name {name!r} is used by {count} labels; names must be "
                    "unique regardless of case",
                    details={"proposed": name},
                    page_index=None,
                )
            )
    for label in answer.labels:
        if not label.kinds:
            failures.append(
                _failure(
                    "labels",
                    f"label {label.name!r} has no kinds; give it at least one",
                    details={"proposed": label.name},
                    page_index=None,
                )
            )

    known = set(names) | {"other"}
    page_count = len(facts.pages)
    for region in answer.regions:
        if region.label.strip().casefold() in known:
            continue
        page = region.page_index
        failures.append(
            _failure(
                "labels",
                f"a region on page {page} uses label {region.label!r}, which is not "
                "one of the labels",
                details={"proposed": region.label},
                page_index=page if 0 <= page < page_count else None,
            )
        )
    return failures


def check_languages(answer: SurveyAnswer, facts: Facts) -> list[CheckFailure]:
    """C7: the answer lists at least one language, as valid BCP-47 tags.

    A tag is valid when ``langcodes`` finds every part of it in the IANA language
    subtag registry; special tags such as ``zxx`` are valid.

    Parameters
    ----------
    answer
        The model's answer.
    facts
        The measured facts (not used).

    Returns
    -------
    list[CheckFailure]
        One failure per invalid tag, or one for an empty list.
    """

    if not answer.languages:
        return [
            _failure(
                "languages",
                "no language is listed; list at least one BCP-47 tag (zxx when the "
                "PDF has no text in any language)",
                details={"proposed": []},
                page_index=None,
            )
        ]
    return [
        _failure(
            "languages",
            f"{tag!r} is not a valid BCP-47 language tag",
            details={"proposed": tag},
            page_index=None,
        )
        for tag in answer.languages
        if not is_language_tag(tag)
    ]


def check_page_numbering(answer: SurveyAnswer, facts: Facts) -> list[CheckFailure]:
    """C4: page-numbering ranges lie inside the PDF and do not overlap.

    Parameters
    ----------
    answer
        The model's answer.
    facts
        The measured facts, for the page count.

    Returns
    -------
    list[CheckFailure]
        The failures, one per affected page where a page applies.
    """

    return _range_failures("page_numbering", answer.page_numbering, len(facts.pages))


def check_regions(answer: SurveyAnswer, facts: Facts) -> list[CheckFailure]:
    """C2: each region is on a page of the PDF, with a box inside the page.

    Parameters
    ----------
    answer
        The model's answer.
    facts
        The measured facts, for the page count.

    Returns
    -------
    list[CheckFailure]
        One failure per region on a page the PDF does not have, and one per region
        whose box is not ``0 <= x0 < x1 <= 1`` and ``0 <= y0 < y1 <= 1``.
    """

    page_count = len(facts.pages)
    failures = []
    for region in answer.regions:
        page = region.page_index
        if not 0 <= page < page_count:
            failures.append(
                _failure(
                    "regions",
                    f"a region is on page {page}, but the PDF has pages 0-"
                    f"{page_count - 1}",
                    details={"page_count": page_count, "proposed": page},
                    page_index=None,
                )
            )
            continue
        box = region.bbox
        if 0 <= box.x0 < box.x1 <= 1 and 0 <= box.y0 < box.y1 <= 1:
            continue
        values = [box.x0, box.y0, box.x1, box.y1]
        failures.append(
            _failure(
                "regions",
                f"a region on page {page} has the box {values}; a box needs "
                "0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1",
                details={"proposed": values},
                page_index=page,
            )
        )
    return failures


def check_results(
    failures: dict[SurveyCheckName, list[CheckFailure]], *, attempts: int
) -> list[CheckResult]:
    """Record each check's result on the accepted answer, C1 to C7 in order.

    Parameters
    ----------
    failures
        Each check's failures on the accepted answer, from `run_checks`.
    attempts
        How many model answers were checked.

    Returns
    -------
    list[CheckResult]
        The results for ``pdf_survey.json`` ``checks``.
    """

    return [
        CheckResult(
            attempts=attempts,
            failures=failures[name],
            name=name,
            passed=not failures[name],
        )
        for name in CHECKS
    ]


def check_rotation(answer: SurveyAnswer, facts: Facts) -> list[CheckFailure]:
    """C3: rotation ranges lie inside the PDF and do not overlap.

    Parameters
    ----------
    answer
        The model's answer.
    facts
        The measured facts, for the page count.

    Returns
    -------
    list[CheckFailure]
        The failures, one per affected page where a page applies.
    """

    return _range_failures("rotation", answer.rotation, len(facts.pages))


def check_writing_direction(answer: SurveyAnswer, facts: Facts) -> list[CheckFailure]:
    """C6: writing-direction ranges lie inside the PDF and do not overlap.

    Parameters
    ----------
    answer
        The model's answer.
    facts
        The measured facts, for the page count.

    Returns
    -------
    list[CheckFailure]
        The failures, one per affected page where a page applies.
    """

    return _range_failures(
        "writing_direction", answer.writing_direction.ranges, len(facts.pages)
    )


def compare_with_facts(answer: SurveyAnswer, facts: Facts) -> list[ReviewIssue]:
    """Record where the accepted answer differs from the measured facts.

    A page can differ only where the probe measured a value: a confident text angle
    for rotation, or a printed number with a value for page numbering. The profile's
    value for a page comes from the first range inside the PDF that covers it. The
    comparison never changes the answer and never sends it back to the model.

    Parameters
    ----------
    answer
        The accepted answer.
    facts
        The measured facts.

    Returns
    -------
    list[ReviewIssue]
        One ``rotation_differs`` issue per page whose rotation differs, then one
        ``page_number_differs`` issue per page whose number differs.
    """

    return _rotation_issues(answer, facts) + _page_number_issues(answer, facts)


def retry_message(failures: dict[SurveyCheckName, list[CheckFailure]]) -> str:
    """Write the message that asks the model to fix its answer.

    Parameters
    ----------
    failures
        Each check's failures, from `run_checks`.

    Returns
    -------
    str
        Every failure, one per line, after a line asking for a corrected answer.
    """

    lines = [f"- {failure.message}" for name in CHECKS for failure in failures[name]]
    return (
        "Your answer is not yet well formed and complete. Fix each problem below and "
        "answer again:\n" + "\n".join(lines)
    )


def review_issues(results: list[CheckResult]) -> list[ReviewIssue]:
    """Turn the failures still on the accepted answer into review issues.

    Parameters
    ----------
    results
        The check results, from `check_results`.

    Returns
    -------
    list[ReviewIssue]
        One issue per failure, C1 to C7 in order.
    """

    return [
        ReviewIssue(
            check=result.name,
            details=failure.details,
            item_id=None,
            message=failure.message,
            page_index=failure.page_index,
            step="survey",
        )
        for result in results
        for failure in result.failures
    ]


def run_checks(
    answer: SurveyAnswer, facts: Facts
) -> dict[SurveyCheckName, list[CheckFailure]]:
    """Run checks C1 to C7 on an answer.

    Parameters
    ----------
    answer
        The model's answer.
    facts
        The measured facts, for the page count and the repeated-line IDs.

    Returns
    -------
    dict[SurveyCheckName, list[CheckFailure]]
        Each check's failures, C1 to C7 in order; an empty list when it passed.
    """

    return {name: check(answer, facts) for name, check in CHECKS.items()}


# The checks, C1 to C7 in order.
CHECKS: dict[SurveyCheckName, Check] = {
    "labels": check_labels,
    "regions": check_regions,
    "rotation": check_rotation,
    "page_numbering": check_page_numbering,
    "artifacts": check_artifacts,
    "writing_direction": check_writing_direction,
    "languages": check_languages,
}

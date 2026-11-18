"""The survey's checks, C1 to C7: what Pydantic cannot check in the model's answer.

Pydantic checks the answer's shape. These checks compare the answer with itself and
with the measured facts. Each check returns every failure it finds, one per affected
page, so one retry message can name every problem and the last attempt can record them
all. The checks use page indexes, measured values and IDs only, never word lists.
"""

# Standard Library
from collections import Counter
from collections.abc import Callable, Sequence
from typing import Protocol

# Package Library
from pydelity.config.schemas import is_language_tag
from pydelity.surveying.schemas import (
    CheckFailure,
    CheckName,
    CheckResult,
    Facts,
    PageNumberingRange,
    ReviewIssue,
    SurveyAnswer,
)

# Checks the answer against the facts and returns every failure found.
type Check = Callable[[SurveyAnswer, Facts], list[CheckFailure]]

# In a page-numbering range, at least this share of the pages with a measured arabic
# number must print the page index plus the range's offset.
PAGE_NUMBERING_MATCH_SHARE = 0.8

# Each page of a measured numbering range of at least this many pages must be in a
# page-numbering range with the same offset.
PAGE_NUMBERING_MIN_RANGE_PAGES = 3


class _PageRange(Protocol):
    """A range of pages, from its first to its last index, inclusive."""

    @property
    def first_page_index(self) -> int:
        """The first page of the range."""

    @property
    def last_page_index(self) -> int:
        """The last page of the range, inclusive."""


def _failure(
    check: CheckName,
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
        What is wrong, with the proposed and measured values.
    details
        The proposed and measured values.
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


def _offset_failures(
    *, facts: Facts, measured: dict[int, int], ranges: Sequence[PageNumberingRange]
) -> list[CheckFailure]:
    """Check the printed numbers in each page-numbering range against its offset.

    Parameters
    ----------
    facts
        The measured facts, for the measured numbering ranges.
    measured
        Each page's measured arabic number, by page index.
    ranges
        The answer's valid page-numbering ranges.

    Returns
    -------
    list[CheckFailure]
        One failure per page that breaks a range's offset, in a range where fewer
        than `PAGE_NUMBERING_MATCH_SHARE` of the numbered pages match, and one per
        page of a long measured range that no range with its offset covers.
    """

    failures = []
    for numbering in ranges:
        numbered = [page for page in _pages(numbering) if page in measured]
        offset = numbering.offset
        wrong = [
            page
            for page in numbered
            if offset is None or measured[page] != page + offset
        ]
        if len(numbered) - len(wrong) >= PAGE_NUMBERING_MATCH_SHARE * len(numbered):
            continue
        for page in wrong:
            expected = "no number" if offset is None else str(page + offset)
            failures.append(
                _failure(
                    "page_numbering",
                    f"page {page} prints {measured[page]}, but the range of pages "
                    f"{numbering.first_page_index}-{numbering.last_page_index} with "
                    f"offset {offset} gives {expected}",
                    details={"measured": measured[page] - page, "proposed": offset},
                    page_index=page,
                )
            )

    for measured_range in facts.page_numbering:
        if len(_pages(measured_range)) < PAGE_NUMBERING_MIN_RANGE_PAGES:
            continue
        offset = measured_range.offset
        for page in _pages(measured_range):
            if any(page in _pages(r) and r.offset == offset for r in ranges):
                continue
            failures.append(
                _failure(
                    "page_numbering",
                    f"page {page} is in measured pages "
                    f"{measured_range.first_page_index}-"
                    f"{measured_range.last_page_index}, whose numbers have offset "
                    f"{offset}, but no range with that offset covers it",
                    details={
                        "measured": offset,
                        "proposed": next(
                            (r.offset for r in ranges if page in _pages(r)), None
                        ),
                    },
                    page_index=page,
                )
            )
    return failures


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


def _range_failures(
    check: CheckName, ranges: Sequence[_PageRange], page_count: int
) -> tuple[list[CheckFailure], list[int]]:
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
    tuple[list[CheckFailure], list[int]]
        One failure per range outside the PDF and one per page that several ranges
        cover; and the positions of the ranges inside the PDF.
    """

    failures = []
    valid = []
    for position, page_range in enumerate(ranges):
        first = page_range.first_page_index
        last = page_range.last_page_index
        if 0 <= first <= last < page_count:
            valid.append(position)
            continue
        failures.append(
            _failure(
                check,
                f"range {first}-{last} is not inside the PDF's pages 0-"
                f"{page_count - 1}, or ends before it starts",
                details={
                    "measured": {"page_count": page_count},
                    "proposed": {"first_page_index": first, "last_page_index": last},
                },
                page_index=None,
            )
        )

    covering = Counter(page for position in valid for page in _pages(ranges[position]))
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
    return failures, valid


def check_artifacts(answer: SurveyAnswer, facts: Facts) -> list[CheckFailure]:
    """C5: every measured repeated line is accounted for exactly once.

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
                details={"measured": line.id, "proposed": count},
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
    """C4: page-numbering ranges lie inside the PDF and agree with the printed numbers.

    Ranges must not overlap. In each range, at least `PAGE_NUMBERING_MATCH_SHARE` of
    the pages with a measured arabic number must print the page index plus the
    range's offset. Each page of a measured numbering range of at least
    `PAGE_NUMBERING_MIN_RANGE_PAGES` pages must be in a range with the same offset.

    Parameters
    ----------
    answer
        The model's answer.
    facts
        The measured facts, for the printed numbers.

    Returns
    -------
    list[CheckFailure]
        The failures, one per affected page where a page applies.
    """

    failures, valid = _range_failures(
        "page_numbering", answer.page_numbering, len(facts.pages)
    )
    measured = {
        page.index: page.printed_number.value
        for page in facts.pages
        if page.printed_number is not None
        and page.printed_number.style == "arabic"
        and page.printed_number.value is not None
    }
    ranges = [answer.page_numbering[position] for position in valid]
    return failures + _offset_failures(facts=facts, measured=measured, ranges=ranges)


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
                    details={"measured": {"page_count": page_count}, "proposed": page},
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


def check_rotation(answer: SurveyAnswer, facts: Facts) -> list[CheckFailure]:
    """C3: rotation ranges lie inside the PDF and agree with the measured text angle.

    Ranges must not overlap. On every page whose orientation is measured with
    confidence, the rotation (0 for pages no range covers) must equal the measured
    angle of the text: text that runs at 90 degrees counterclockwise needs a
    90-degree clockwise rotation.

    Parameters
    ----------
    answer
        The model's answer.
    facts
        The measured facts, for each page's orientation.

    Returns
    -------
    list[CheckFailure]
        The failures, one per affected page where a page applies.
    """

    failures, valid = _range_failures("rotation", answer.rotation, len(facts.pages))
    degrees_by_page = {
        page: answer.rotation[position].degrees
        for position in valid
        for page in _pages(answer.rotation[position])
    }
    for page in facts.pages:
        measured = page.orientation.dominant
        if not page.orientation.confident or measured is None:
            continue
        proposed = degrees_by_page.get(page.index, 0)
        if proposed == measured:
            continue
        failures.append(
            _failure(
                "rotation",
                f"page {page.index} gets {proposed} degrees, but its text runs at "
                f"{measured} degrees counterclockwise, which needs {measured}",
                details={"measured": measured, "proposed": proposed},
                page_index=page.index,
            )
        )
    return failures


def check_results(
    failures: dict[CheckName, list[CheckFailure]], *, attempts: int
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

    failures, _ = _range_failures(
        "writing_direction", answer.writing_direction.ranges, len(facts.pages)
    )
    return failures


def retry_message(failures: dict[CheckName, list[CheckFailure]]) -> str:
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
        "Your answer does not match the measured facts. Fix each problem below and "
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
            message=failure.message,
            page_index=failure.page_index,
            step="survey",
        )
        for result in results
        for failure in result.failures
    ]


def run_checks(
    answer: SurveyAnswer, facts: Facts
) -> dict[CheckName, list[CheckFailure]]:
    """Run checks C1 to C7 on an answer.

    Parameters
    ----------
    answer
        The model's answer.
    facts
        The measured facts.

    Returns
    -------
    dict[CheckName, list[CheckFailure]]
        Each check's failures, C1 to C7 in order; an empty list when it passed.
    """

    return {name: check(answer, facts) for name, check in CHECKS.items()}


# The checks, C1 to C7 in order.
CHECKS: dict[CheckName, Check] = {
    "labels": check_labels,
    "regions": check_regions,
    "rotation": check_rotation,
    "page_numbering": check_page_numbering,
    "artifacts": check_artifacts,
    "writing_direction": check_writing_direction,
    "languages": check_languages,
}

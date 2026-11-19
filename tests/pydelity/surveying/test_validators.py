"""Tests for the survey's checks C1 to C7 on a model answer.

Each check must find every problem of its kind, one failure per affected page where
a page applies, and none in a well-formed answer. The facts come from the 8-page
CAPS excerpt, which has 8 repeated lines.
"""

# Standard Library
from collections.abc import Callable

# Package Library
from pydelity.surveying.schemas import CheckFailure, Facts, SurveyAnswer
from pydelity.surveying.validators import run_checks

# The 8-page test PDF the answers describe.
_PDF = "caps_english_hl_pages_28_35.pdf"


def _region(*, label: str, page: int, x0: float = 0.1, x1: float = 0.9) -> dict:
    """Write one proposed region for an answer.

    Parameters
    ----------
    label
        The region's label.
    page
        Its page index.
    x0
        Its left edge, as a page fraction.
    x1
        Its right edge, as a page fraction.

    Returns
    -------
    dict
        The region, as the model would send it.
    """

    return {
        "bbox": {"x0": x0, "x1": x1, "y0": 0.1, "y1": 0.5},
        "label": label,
        "note": "",
        "page_index": page,
    }


def _pages_and_messages(failures: list[CheckFailure]) -> list[tuple[int | None, str]]:
    """Reduce failures to their page and message, for comparing.

    Parameters
    ----------
    failures
        One check's failures.

    Returns
    -------
    list[tuple[int | None, str]]
        Each failure's page index and message.
    """

    return [(failure.page_index, failure.message) for failure in failures]


def _starts(
    found: list[tuple[int | None, str]], expected: list[tuple[int | None, str]]
) -> bool:
    """Tell whether failures match expected pages and message beginnings, in order.

    Parameters
    ----------
    found
        Each failure's page index and message.
    expected
        Each expected failure's page index and the start of its message.

    Returns
    -------
    bool
        Whether both lists have the same length and each pair matches.
    """

    return len(found) == len(expected) and all(
        page == want_page and message.startswith(start)
        for (page, message), (want_page, start) in zip(found, expected, strict=True)
    )


def test_a_well_formed_answer_passes_every_check(
    facts_of: Callable[[str], Facts], survey_answer: Callable[..., dict]
) -> None:
    """An answer with valid labels, regions, ranges, lines and tags has no failures."""

    facts = facts_of(_PDF)
    answer = SurveyAnswer.model_validate(
        survey_answer(
            facts,
            languages=["en", "zxx"],
            page_numbering=[
                {
                    "first_page_index": 0,
                    "last_page_index": 7,
                    "offset": 23,
                    "style": "arabic",
                }
            ],
            regions=[_region(label="body", page=0), _region(label="other", page=7)],
            rotation=[{"degrees": 90, "first_page_index": 0, "last_page_index": 7}],
            writing_direction={
                "default": "ltr",
                "ranges": [
                    {"direction": "rtl", "first_page_index": 2, "last_page_index": 3}
                ],
            },
        )
    )

    failures = run_checks(answer, facts)

    assert list(failures) == [
        "labels",
        "regions",
        "rotation",
        "page_numbering",
        "artifacts",
        "writing_direction",
        "languages",
    ]
    assert all(found == [] for found in failures.values())


def test_labels_check_finds_empty_repeated_kindless_and_unknown_labels(
    facts_of: Callable[[str], Facts], survey_answer: Callable[..., dict]
) -> None:
    """C1 reports an empty name, a name used twice, no kinds and an unknown label."""

    facts = facts_of(_PDF)
    labels = [
        {"description": "", "kinds": ["text"], "name": "Body", "role": "body"},
        {"description": "", "kinds": ["list"], "name": " BODY ", "role": "body"},
        {"description": "", "kinds": ["text"], "name": "  ", "role": "aside"},
        {"description": "", "kinds": [], "name": "Table", "role": "body"},
    ]
    regions = [
        _region(label="Missing", page=1),
        _region(label="OTHER", page=2),
        _region(label="table", page=3),
    ]
    answer = SurveyAnswer.model_validate(
        survey_answer(facts, labels=labels, regions=regions)
    )

    failures = run_checks(answer, facts)["labels"]

    found = _pages_and_messages(failures)
    assert _starts(
        found,
        [
            (None, "labels: the name 'body' is used by 2 lab"),
            (None, "labels: 1 label(s) have an empty name"),
            (None, "labels: label 'Table' has no kinds; give"),
            (1, "labels: a region on page 1 uses label 'Mi"),
        ],
    ), found


def test_regions_check_finds_pages_outside_the_pdf_and_bad_boxes(
    facts_of: Callable[[str], Facts], survey_answer: Callable[..., dict]
) -> None:
    """C2 reports a region on a missing page and a box that is not inside the page."""

    facts = facts_of(_PDF)
    regions = [
        _region(label="Body", page=8),
        _region(label="Body", page=2, x0=0.6, x1=0.4),
        _region(label="Body", page=3, x1=1.2),
        _region(label="Body", page=4),
    ]
    answer = SurveyAnswer.model_validate(survey_answer(facts, regions=regions))

    failures = run_checks(answer, facts)["regions"]

    assert [failure.page_index for failure in failures] == [None, 2, 3]
    assert failures[0].details == {"page_count": 8, "proposed": 8}
    assert failures[1].details == {"proposed": [0.6, 0.1, 0.4, 0.5]}


def test_rotation_check_finds_ranges_outside_the_pdf_and_overlaps(
    facts_of: Callable[[str], Facts], survey_answer: Callable[..., dict]
) -> None:
    """C3 reports a range past the last page and each page two ranges cover."""

    facts = facts_of(_PDF)
    rotation = [
        {"degrees": 90, "first_page_index": 0, "last_page_index": 3},
        {"degrees": 90, "first_page_index": 2, "last_page_index": 4},
        {"degrees": 180, "first_page_index": 6, "last_page_index": 9},
        {"degrees": 270, "first_page_index": 5, "last_page_index": 4},
    ]
    answer = SurveyAnswer.model_validate(survey_answer(facts, rotation=rotation))

    failures = run_checks(answer, facts)["rotation"]

    found = _pages_and_messages(failures)
    assert _starts(
        found,
        [
            (None, "rotation: range 6-9 is not inside the PD"),
            (None, "rotation: range 5-4 is not inside the PD"),
            (2, "rotation: page 2 is in 2 ranges; ranges"),
            (3, "rotation: page 3 is in 2 ranges; ranges"),
        ],
    ), found


def test_page_numbering_check_finds_ranges_outside_the_pdf_and_overlaps(
    facts_of: Callable[[str], Facts], survey_answer: Callable[..., dict]
) -> None:
    """C4 reports a range before the first page and each page two ranges cover."""

    facts = facts_of(_PDF)
    numbering = [
        {"first_page_index": -1, "last_page_index": 2, "offset": 1, "style": "roman"},
        {"first_page_index": 3, "last_page_index": 7, "offset": 23, "style": "arabic"},
        {"first_page_index": 7, "last_page_index": 7, "offset": None, "style": "none"},
    ]
    answer = SurveyAnswer.model_validate(survey_answer(facts, page_numbering=numbering))

    failures = run_checks(answer, facts)["page_numbering"]

    found = _pages_and_messages(failures)
    assert _starts(
        found,
        [
            (None, "page_numbering: range -1-2 is not inside"),
            (7, "page_numbering: page 7 is in 2 ranges"),
        ],
    ), found


def test_artifacts_check_finds_missing_repeated_and_unknown_line_ids(
    facts_of: Callable[[str], Facts], survey_answer: Callable[..., dict]
) -> None:
    """C5 needs every repeated line ID exactly once, and no ID the facts lack."""

    facts = facts_of(_PDF)
    assert [line.id for line in facts.repeated_lines] == [f"R{n}" for n in range(1, 9)]
    artifacts = [
        {
            "description": "Running header",
            "id": "A1",
            "position": "top",
            "repeated_line_ids": ["R1", "R2", "R9"],
        }
    ]
    content = [
        {"reason": "Heading", "repeated_line_id": line_id}
        for line_id in ["R2", "R3", "R4", "R5", "R6", "R7"]
    ]
    answer = SurveyAnswer.model_validate(
        survey_answer(facts, artifacts=artifacts, non_artifact_lines=content)
    )

    failures = run_checks(answer, facts)["artifacts"]

    assert [failure.details for failure in failures] == [
        {"proposed": 2, "repeated_line_id": "R2"},
        {"proposed": 0, "repeated_line_id": "R8"},
        {"proposed": "R9"},
    ]
    assert "R8" in failures[1].message
    assert facts.repeated_lines[7].text in failures[1].message


def test_writing_direction_check_finds_ranges_outside_the_pdf_and_overlaps(
    facts_of: Callable[[str], Facts], survey_answer: Callable[..., dict]
) -> None:
    """C6 reports a range past the last page and each page two ranges cover."""

    facts = facts_of(_PDF)
    direction = {
        "default": "ltr",
        "ranges": [
            {"direction": "rtl", "first_page_index": 0, "last_page_index": 1},
            {"direction": "ttb", "first_page_index": 1, "last_page_index": 1},
            {"direction": "rtl", "first_page_index": 8, "last_page_index": 8},
        ],
    }
    answer = SurveyAnswer.model_validate(
        survey_answer(facts, writing_direction=direction)
    )

    failures = run_checks(answer, facts)["writing_direction"]

    found = _pages_and_messages(failures)
    assert _starts(
        found,
        [
            (None, "writing_direction: range 8-8 is not insi"),
            (1, "writing_direction: page 1 is in 2 ranges"),
        ],
    ), found


def test_languages_check_needs_registered_tags_and_at_least_one(
    facts_of: Callable[[str], Facts], survey_answer: Callable[..., dict]
) -> None:
    """C7 rejects unregistered or malformed tags one by one, and an empty list."""

    facts = facts_of(_PDF)
    tagged = SurveyAnswer.model_validate(
        survey_answer(facts, languages=["en_US", "zz", "en-", "zxx", "ar"])
    )
    empty = SurveyAnswer.model_validate(survey_answer(facts, languages=[]))

    failures = run_checks(tagged, facts)["languages"]
    none_listed = run_checks(empty, facts)["languages"]

    assert [failure.details for failure in failures] == [
        {"proposed": "zz"},
        {"proposed": "en-"},
    ]
    assert {failure.page_index for failure in failures} == {None}
    assert [failure.details for failure in none_listed] == [{"proposed": []}]

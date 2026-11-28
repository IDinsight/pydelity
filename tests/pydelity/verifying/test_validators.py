"""Tests for page-break verification's checks and hint on a verdict for one break.

Most tests use one break between two pages of a statistics report: a running header
and a page number on each page, a Chinese table whose title repeats with a
continuation marker on the later page, and an Arabic sentence that carries on. Each
check must pass a right verdict and find the problems of its kind, naming the item
they are about. The hint must find a piece that starts with a start marker and never
reach a retry message.

Other tests use a break in a school's weekly plan: a table whose "PHONICS" row is cut
by the break and printed again as "PHONICS (contd)", and a list whose first entry page
extraction read as text. The comparison of two verdicts needs no pages.
"""

# Standard Library
from collections.abc import Callable

# Third Party Library
import pytest

# Package Library
from pydelity.extracting.schemas import Item, PageFile
from pydelity.review import CheckFailure
from pydelity.verifying.prompts import judge_break
from pydelity.verifying.schemas import BreakContext, BreakVerdict, BreakVerification
from pydelity.verifying.validators import (
    CHECKS,
    check_ids,
    check_joins,
    check_results,
    compare_verdicts,
    compare_with_hints,
    hint_results,
    retry_message,
    review_issues,
    run_checks,
)

# What every check finds in a verdict that passes them all.
_NO_FAILURES = {name: [] for name in CHECKS}


def _code_and_list_pages(
    page_file: Callable[..., PageFile], page_item: Callable[..., Item]
) -> tuple[PageFile, PageFile]:
    """Build the pages on either side of a break in a manual with code and steps.

    Parameters
    ----------
    page_file
        The fixture that builds a page file.
    page_item
        The fixture that builds an item.

    Returns
    -------
    tuple[PageFile, PageFile]
        Page index 5, ending in a code listing and a list of two steps, and page
        index 6, starting with the rest of the listing and a list of one step. Each
        page has one container.
    """

    earlier = page_file(
        5,
        page_item("p0005-001", kind="code", language=None, text="total = sum(val"),
        page_item("p0005-002", entries=["Open the file.", "Read each row."]),
        containers=[("p0005-c01", "Note box")],
    )
    later = page_file(
        6,
        page_item("p0006-001", kind="code", language=None, text="ues)"),
        page_item("p0006-002", entries=["Close the file."]),
        containers=[("p0006-c01", "Note box")],
    )
    return earlier, later


def _curriculum_pages(
    page_file: Callable[..., PageFile],
    page_item: Callable[..., Item],
    *,
    later_rows: list[list[str | None]] | None = None,
) -> tuple[PageFile, PageFile]:
    """Build the pages on either side of a break in a school's weekly plan.

    Parameters
    ----------
    page_file
        The fixture that builds a page file.
    page_item
        The fixture that builds an item.
    later_rows
        The later table's rows, to replace the default ones.

    Returns
    -------
    tuple[PageFile, PageFile]
        Page index 7, ending in a table whose last row "PHONICS" is cut by the break
        and in a list's first entry, which page extraction read as text. Page index
        8, starting with the table's header row again and the split row's later part
        under "PHONICS (contd)", then the list's later entries as a list item, then
        a paragraph that starts "Part 2".
    """

    earlier = page_file(
        7,
        page_item(
            "p0007-001",
            header_rows=1,
            rows=[["Subject", "Activity"], ["PHONICS", "Blend the short"]],
        ),
        page_item("p0007-002", text="1. Bring a pencil."),
    )
    later = page_file(
        8,
        page_item(
            "p0008-001",
            header_rows=1,
            rows=later_rows
            or [
                ["Subject", "Activity"],
                ["PHONICS (contd)", "vowel sounds"],
                ["WRITING (contd)", "Copy the letters"],
            ],
        ),
        page_item("p0008-002", entries=["Bring a ruler.", "Bring paper."]),
        page_item("p0008-003", text="Part 2 (continued) of the plan."),
    )
    return earlier, later


def _piece(
    earlier_item: str, later_item: str, join: str, **changes: object
) -> dict[str, object]:
    """Write one continuing piece as a model would answer it.

    Parameters
    ----------
    earlier_item
        The item where the piece ends on the earlier page.
    later_item
        The item where the piece starts on the later page.
    join
        The piece's join.
    **changes
        Other fields to set; the rest are null or empty.

    Returns
    -------
    dict[str, object]
        The piece, as JSON-ready data.
    """

    piece: dict[str, object] = {
        "cell_joins": None,
        "earlier_entry": None,
        "earlier_item": earlier_item,
        "join": join,
        "later_entry": None,
        "later_item": later_item,
        "markers": [],
        "repeated_header_rows": None,
        "repeated_items": [],
        "text_join": None,
    }
    piece.update(changes)
    return piece


def _statistics_pages(
    page_file: Callable[..., PageFile], page_item: Callable[..., Item]
) -> tuple[PageFile, PageFile]:
    """Build the pages on either side of a break in a statistics report.

    Parameters
    ----------
    page_file
        The fixture that builds a page file.
    page_item
        The fixture that builds an item.

    Returns
    -------
    tuple[PageFile, PageFile]
        Page index 3 and page index 4. Each has a running header, a table title, a
        table with one header row, a sentence in Arabic and a page number, in that
        order, inside one shaded box. The earlier table's last row is cut by the
        break, and the later page repeats the title after "续表" (continued table)
        and the header row.
    """

    header = "Annual Statistics 2025"
    earlier = page_file(
        3,
        page_item("p0003-001", label="other", role="artifact", text=header),
        page_item(
            "p0003-002", language="zh-Hans", role="heading", text="表 3-1 各地区人口"
        ),
        page_item(
            "p0003-003",
            header_rows=1,
            language="zh-Hans",
            rows=[["地区", "人口"], ["北京", "2189"], ["上海", "24"]],
        ),
        page_item("p0003-004", language="ar", text="وتستمر الجملة التي تبدأ هنا"),
        page_item("p0003-005", role="artifact", text="4"),
        containers=[("p0003-c01", "Shaded box")],
    )
    later = page_file(
        4,
        page_item("p0004-001", role="artifact", text=header),
        page_item(
            "p0004-002",
            language="zh-Hans",
            role="heading",
            text="续表 3-1 各地区人口",
        ),
        page_item(
            "p0004-003",
            header_rows=1,
            language="zh-Hans",
            rows=[["地区", "人口"], [None, "87"], ["广州", "1868"]],
        ),
        page_item("p0004-004", language="ar", text="في الصفحة التالية دون انقطاع."),
        page_item("p0004-005", role="artifact", text="5"),
        containers=[("p0004-c01", "Shaded box")],
    )
    return earlier, later


def _table_piece(**changes: object) -> dict[str, object]:
    """Write the right piece for the statistics report's table.

    Parameters
    ----------
    **changes
        Fields to replace.

    Returns
    -------
    dict[str, object]
        The table's split row merged after one repeated header row, with the
        repeated title and its "续表" marker.
    """

    return _piece(
        "p0003-003",
        "p0004-003",
        "merge_split_row",
        cell_joins=[None, "no_space"],
        markers=[{"cell": None, "item": "p0004-002", "row": None, "text": "续表"}],
        repeated_header_rows=1,
        repeated_items=["p0004-002"],
    ) | dict(changes)


def _verdict(
    *pieces: dict[str, object], containers: list[tuple[str, str]] | None = None
) -> BreakVerdict:
    """Write a verdict with these pieces and containers.

    Parameters
    ----------
    *pieces
        The continuing pieces, from `_piece`.
    containers
        The continuing containers, as ``(earlier, later)`` ID pairs.

    Returns
    -------
    BreakVerdict
        The verdict, with ``continues`` true when it has a piece.
    """

    return BreakVerdict.model_validate(
        {
            "containers": [
                {"earlier": earlier, "later": later}
                for earlier, later in containers or []
            ],
            "continues": bool(pieces),
            "pieces": list(pieces),
            "reason": "The table and the sentence carry on.",
        }
    )


def test_a_right_verdict_with_several_pieces_passes_every_check_and_hint(
    break_context: Callable[..., BreakContext],
    page_file: Callable[..., PageFile],
    page_item: Callable[..., Item],
) -> None:
    """A right verdict with a split Chinese table and an Arabic sentence passes.

    The table piece repeats one header row, drops the repeated title and folds its
    "续表" marker, and the shaded box continues. Page furniture sits between the
    pieces on both pages. No check fails, no start marker begins a piece, and the
    break has no review issue.
    """

    earlier, later = _statistics_pages(page_file, page_item)
    verdict = _verdict(
        _table_piece(),
        _piece("p0003-004", "p0004-004", "continue_text", text_join="space"),
        containers=[("p0003-c01", "p0004-c01")],
    )
    context = break_context(
        start_markers=[("الفصل", "Starts a chapter."), ("第", "Starts a chapter.")]
    )

    failures = run_checks(verdict, earlier, later)
    differences = compare_with_hints(verdict, earlier, later, context)

    assert failures == _NO_FAILURES
    assert differences == {"start_markers": []}
    assert (
        review_issues(
            checks=check_results(failures, attempts=1),
            earlier=earlier,
            hints=hint_results(differences),
            later=later,
            verification=None,
        )
        == []
    )


def test_a_join_that_breaks_its_rules_fails_the_joins_check(
    page_file: Callable[..., PageFile], page_item: Callable[..., Item]
) -> None:
    """Code that is dehyphenated and a new entry with a text join fail ``joins``.

    Code joins only with a newline, and ``new_entry`` sets no text join. Every
    other check passes.
    """

    earlier, later = _code_and_list_pages(page_file, page_item)
    verdict = _verdict(
        _piece("p0005-001", "p0006-001", "continue_text", text_join="dehyphenate"),
        _piece("p0005-002", "p0006-002", "new_entry", text_join="space"),
    )

    failures = run_checks(verdict, earlier, later)

    assert failures == _NO_FAILURES | {
        "joins": [
            CheckFailure(
                details={"item": "p0005-001"},
                message="joins: piece 1 (p0005-001 to p0006-001) joins code with "
                "text_join dehyphenate, but code joins with newline",
                page_index=5,
            ),
            CheckFailure(
                details={"item": "p0005-002"},
                message="joins: piece 2 (p0005-002 to p0006-002) uses new_entry, so "
                "text_join must be null",
                page_index=None,
            ),
        ]
    }


def test_a_new_entry_from_a_text_item_and_a_repeated_row_label_pass_every_check(
    page_file: Callable[..., PageFile], page_item: Callable[..., Item]
) -> None:
    """A list read as text on the earlier page can start a new entry on the later one.

    The second piece starts a new entry from the text item "1. Bring a pencil." The
    first piece merges the split row, whose label is printed again as "PHONICS
    (contd)", so that cell only repeats the cell above it and its cell join is
    ``repeat``, with the marker folded. No check fails.
    """

    earlier, later = _curriculum_pages(page_file, page_item)
    verdict = _verdict(
        _piece(
            "p0007-001",
            "p0008-001",
            "merge_split_row",
            cell_joins=["repeat", "space"],
            markers=[{"cell": 0, "item": "p0008-001", "row": 1, "text": "(contd)"}],
            repeated_header_rows=1,
        ),
        _piece("p0007-002", "p0008-002", "new_entry"),
    )

    assert run_checks(verdict, earlier, later) == _NO_FAILURES


def test_a_new_entry_into_text_and_a_repeat_text_join_fail_the_joins_check(
    page_file: Callable[..., PageFile], page_item: Callable[..., Item]
) -> None:
    """``new_entry`` must start in a list item, and ``repeat`` is for cells only.

    The first piece starts a new entry in the paragraph "Part 2 (continued) of the
    plan.", and the second joins that paragraph's text with ``repeat``. Each fails
    ``joins`` and nothing else.
    """

    earlier, later = _curriculum_pages(page_file, page_item)
    new_entry = _verdict(_piece("p0007-002", "p0008-003", "new_entry"))
    repeat = _verdict(
        _piece("p0007-002", "p0008-003", "continue_text", text_join="repeat")
    )

    assert [run_checks(verdict, earlier, later) for verdict in (new_entry, repeat)] == [
        _NO_FAILURES
        | {
            "joins": [
                CheckFailure(
                    details={"item": "p0008-003"},
                    message="joins: piece 1 (p0007-002 to p0008-003) uses new_entry, "
                    "which starts in list items, but it starts in p0008-003, a text "
                    "item",
                    page_index=8,
                )
            ]
        },
        _NO_FAILURES
        | {
            "joins": [
                CheckFailure(
                    details={"item": "p0007-002"},
                    message="joins: piece 1 (p0007-002 to p0008-003) joins text with "
                    "text_join repeat, but text joins with space, no_space or "
                    "dehyphenate. repeat is only for the cell_joins of "
                    "merge_split_row",
                    page_index=7,
                )
            ]
        },
    ]


def test_a_piece_that_ends_in_page_furniture_fails_the_furniture_check(
    page_file: Callable[..., PageFile], page_item: Callable[..., Item]
) -> None:
    """A sentence joined from the page number fails ``furniture`` and nothing else."""

    earlier, later = _statistics_pages(page_file, page_item)
    verdict = _verdict(
        _piece("p0003-005", "p0004-004", "continue_text", text_join="space")
    )

    failures = run_checks(verdict, earlier, later)

    assert failures == _NO_FAILURES | {
        "furniture": [
            CheckFailure(
                details={"item": "p0003-005"},
                message="furniture: piece 1 (p0003-005 to p0004-004) ends in "
                "p0003-005, which is page furniture (role artifact). Page furniture "
                "does not continue across a break",
                page_index=3,
            )
        ]
    }


def test_header_rows_that_do_not_repeat_the_earlier_header_fail_header_rows(
    page_file: Callable[..., PageFile], page_item: Callable[..., Item]
) -> None:
    """Counting the merged row as a second header row fails ``header_rows``.

    The later table's second row matches none of the earlier table's first three
    rows after the one its first row matched.
    """

    earlier, later = _statistics_pages(page_file, page_item)
    verdict = _verdict(
        _piece("p0003-003", "p0004-003", "append_rows", repeated_header_rows=2)
    )

    failures = run_checks(verdict, earlier, later)

    assert failures == _NO_FAILURES | {
        "header_rows": [
            CheckFailure(
                details={"item": "p0004-003", "row": 1},
                message="header_rows: piece 1 (p0003-003 to p0004-003) says the first "
                "2 rows of p0004-003 repeat the header of p0003-003, but row 1 of "
                "p0004-003 matches none of the first 3 rows of p0003-003, in order",
                page_index=4,
            )
        ]
    }


def test_a_repeated_item_the_earlier_page_did_not_print_fails_repeats(
    page_file: Callable[..., PageFile], page_item: Callable[..., Item]
) -> None:
    """Naming the Arabic sentence as a repeat of the table's title fails ``repeats``.

    The repeated title itself, whose text holds the earlier title, passes.
    """

    earlier, later = _statistics_pages(page_file, page_item)
    verdict = _verdict(_table_piece(repeated_items=["p0004-002", "p0004-004"]))

    failures = run_checks(verdict, earlier, later)

    assert failures == _NO_FAILURES | {
        "repeats": [
            CheckFailure(
                details={"item": "p0004-004"},
                message="repeats: piece 1 (p0003-003 to p0004-003) names p0004-004 as "
                "a repeated item, but its text matches no text printed on the earlier "
                "page",
                page_index=4,
            )
        ]
    }


def test_repeat_cells_with_no_text_or_another_text_fail_the_repeats_check(
    page_file: Callable[..., PageFile], page_item: Callable[..., Item]
) -> None:
    """A ``repeat`` cell must hold text that some cell of the split row printed.

    The merged row's first cell is empty and its second holds "vowel sounds", which
    neither "PHONICS" nor "Blend the short" holds. Both cells' ``repeat`` fail
    ``repeats``.
    """

    earlier, later = _curriculum_pages(
        page_file,
        page_item,
        later_rows=[["Subject", "Activity"], [None, "vowel sounds"]],
    )
    verdict = _verdict(
        _piece(
            "p0007-001",
            "p0008-001",
            "merge_split_row",
            cell_joins=["repeat", "repeat"],
            repeated_header_rows=1,
        )
    )

    failures = run_checks(verdict, earlier, later)

    assert failures == _NO_FAILURES | {
        "repeats": [
            CheckFailure(
                details={"cell": 0, "item": "p0008-001", "row": 1},
                message="repeats: piece 1 (p0007-001 to p0008-001) gives cell 0 of "
                "row 1 of p0008-001 the cell join repeat, but that cell has no text",
                page_index=8,
            ),
            CheckFailure(
                details={"cell": 1, "item": "p0008-001", "row": 1},
                message="repeats: piece 1 (p0007-001 to p0008-001) gives cell 1 of "
                "row 1 of p0008-001 the cell join repeat, but its text matches no "
                "cell of the split row, the last row of p0007-001",
                page_index=8,
            ),
        ]
    }


def test_a_marker_its_table_cell_does_not_hold_fails_the_markers_check(
    page_file: Callable[..., PageFile], page_item: Callable[..., Item]
) -> None:
    """A "续" marker put on the cell "广州" fails ``markers``; the title's passes."""

    earlier, later = _statistics_pages(page_file, page_item)
    verdict = _verdict(
        _table_piece(
            markers=[
                {"cell": None, "item": "p0004-002", "row": None, "text": "续表"},
                {"cell": 0, "item": "p0004-003", "row": 2, "text": "续"},
            ]
        )
    )

    failures = run_checks(verdict, earlier, later)

    assert failures == _NO_FAILURES | {
        "markers": [
            CheckFailure(
                details={"cell": 0, "item": "p0004-003", "row": 2},
                message="markers: piece 1 (p0003-003 to p0004-003) has the marker "
                "'续' on row 2, cell 0 of p0004-003, but the text of row 2, cell 0 "
                "of p0004-003 does not contain it",
                page_index=4,
            )
        ]
    }


def test_an_unknown_item_an_entry_of_another_item_and_a_container_fail_ids(
    page_file: Callable[..., PageFile], page_item: Callable[..., Item]
) -> None:
    """``ids`` names each ID that is not where the verdict puts it.

    The first piece ends in an item the earlier page does not have, the second ends
    in an entry of the later page's list, and the container named on the later page
    does not exist there.
    """

    earlier, later = _code_and_list_pages(page_file, page_item)
    verdict = _verdict(
        _piece("p0005-007", "p0006-001", "continue_text", text_join="newline"),
        _piece(
            "p0005-002",
            "p0006-002",
            "continue_entry",
            earlier_entry="p0006-002.1",
            later_entry="p0006-002.1",
            text_join="space",
        ),
        containers=[("p0005-c01", "p0006-c02")],
    )

    assert check_ids(verdict, earlier, later) == [
        CheckFailure(
            details={"item": "p0005-007"},
            message="ids: piece 1 (p0005-007 to p0006-001) ends in p0005-007, which "
            "is not an item on the earlier page",
            page_index=5,
        ),
        CheckFailure(
            details={"entry": "p0006-002.1", "item": "p0005-002"},
            message="ids: piece 2 (p0005-002 to p0006-002) ends in the entry "
            "p0006-002.1, which is not an entry of p0005-002",
            page_index=5,
        ),
        CheckFailure(
            details={"container": "p0006-c02"},
            message="ids: containers names p0006-c02, which is not a container on "
            "the later page",
            page_index=6,
        ),
    ]


def test_page_files_that_break_their_own_rules_go_through_every_check_and_prompt(
    break_context: Callable[..., BreakContext],
    page_file: Callable[..., PageFile],
    page_item: Callable[..., Item],
) -> None:
    """Page files page extraction could not fix are checked and sent without error.

    The pages have a failed check of their own, a column order that does not fit
    their direction, items in a container that does not exist or captioning one that
    does not, a table item with no table, list items with no entries or none at all,
    a figure with no figure, a repeated ID and a ragged table with more header rows
    than rows. Start markers with no letters or digits are skipped. The checks
    report what they can, and the prompt lists every item.
    """

    failed_check = {
        "attempts": 3,
        "failures": [{"details": {}, "message": "boxes: overlap", "page_index": 1}],
        "name": "boxes",
        "passed": False,
    }
    earlier = page_file(
        1,
        page_item("p0001-001", caption_of="p0001-099", container="p0001-c07"),
        page_item("p0001-002", kind="table", table=None, text=None),
        page_item("p0001-003", entries=None, kind="list", text=None),
        page_item("p0001-001", text="The same ID again."),
        page_item("p0001-005", figure=None, kind="figure", text=None),
        column_order="right_to_left",
    ).model_copy(update={"checks": [failed_check]})
    later = page_file(
        2,
        page_item("p0002-001", header_rows=5, rows=[["a", "b"], ["c"]]),
        page_item("p0002-002", entries=[]),
    )
    verdict = _verdict(
        _piece("p0001-002", "p0002-001", "append_rows", repeated_header_rows=1),
        _piece(
            "p0001-003",
            "p0002-002",
            "continue_entry",
            earlier_entry="p0001-003.1",
            markers=[{"cell": 1, "item": "p0002-001", "row": 1, "text": "x"}],
            text_join="space",
        ),
    )
    context = break_context(start_markers=[("", "Nothing."), ("—", "A dash.")])

    failures = run_checks(verdict, earlier, later)
    differences = compare_with_hints(verdict, earlier, later, context)
    issues = review_issues(
        checks=check_results(failures, attempts=3),
        earlier=earlier,
        hints=hint_results(differences),
        later=later,
        verification=None,
    )
    judged = judge_break(context, earlier=earlier, later=later)

    messages = [failure.message for found in failures.values() for failure in found]
    assert messages == [
        "ids: piece 2 (p0001-003 to p0002-002) ends in the entry p0001-003.1, which "
        "is not an entry of p0001-003",
        "ids: piece 2 (p0001-003 to p0002-002) has the marker 'x' on row 1, cell 1 "
        "of p0002-001, but row 1 of p0002-001 has no cell 1",
        "joins: piece 2 (p0001-003 to p0002-002) uses continue_entry, but p0001-003 "
        "is a list item with no entries",
        "joins: piece 2 (p0001-003 to p0002-002) uses continue_entry, but p0002-002 "
        "is a list item with no entries",
        "header_rows: piece 1 (p0001-002 to p0002-001) says the first 1 rows of "
        "p0002-001 repeat the header of p0001-002, but p0001-002 has no table",
    ]
    assert differences == {"start_markers": []}
    assert len(issues) == len(messages)
    for item_id in ("p0001-002", "p0001-003", "p0001-005"):
        assert f'"id": "{item_id}"' in judged.earlier_text
    assert '"id": "p0002-002", "kind": "list"' in judged.later_text


def test_a_piece_that_starts_with_a_start_marker_is_a_hint_difference_only(
    break_context: Callable[..., BreakContext],
    page_file: Callable[..., PageFile],
    page_item: Callable[..., Item],
) -> None:
    """A start marker at a piece's start is a difference, never a retry message.

    The Arabic sentence on the later page begins with the survey's start marker
    "في". The difference names the piece's start, and the retry message for the
    verdict's check failure leaves it out. The difference is a review issue when no
    verifier ran or the verifier's verdict differs, and not when it matches.
    """

    earlier, later = _statistics_pages(page_file, page_item)
    verdict = BreakVerdict.model_validate(
        {
            "containers": [],
            "continues": False,
            "pieces": [
                _piece("p0003-004", "p0004-004", "continue_text", text_join="space")
            ],
            "reason": "The sentence carries on.",
        }
    )
    context = break_context(start_markers=[("في", "Starts a new section.")])

    failures = run_checks(verdict, earlier, later)
    differences = compare_with_hints(verdict, earlier, later, context)
    message = retry_message(failures)
    checks = check_results(failures, attempts=3)
    hints = hint_results(differences)
    continuing = verdict.model_copy(update={"continues": True})
    matched, differed = (
        BreakVerification(
            attempts=1,
            checks=check_results(run_checks(other, earlier, later), attempts=1),
            differences=compare_verdicts(verdict, other, page_index=3),
            verdict=other,
        )
        for other in (verdict, continuing)
    )

    assert differences == {
        "start_markers": [
            CheckFailure(
                details={"entry": None, "item": "p0004-004", "marker": "في"},
                message="start_markers: piece 1 (p0003-004 to p0004-004) starts with "
                "'في', which the survey found marks where a new unit of content "
                "starts, and the verdict joins it to the earlier page",
                page_index=4,
            )
        ]
    }
    assert [name for name, found in failures.items() if found] == ["continues"]
    assert "continues is false" in message
    assert "start_markers" not in message
    assert "في" not in message
    assert [
        issue.check
        for issue in review_issues(
            checks=checks, earlier=earlier, hints=hints, later=later, verification=None
        )
    ] == ["continues", "start_markers"]
    assert [
        [
            issue.check
            for issue in review_issues(
                checks=checks,
                earlier=earlier,
                hints=hints,
                later=later,
                verification=verification,
            )
        ]
        for verification in (matched, differed)
    ] == [["continues"], ["continues", "start_markers", "verdicts_differ"]]
    assert check_joins(verdict, earlier, later) == []


@pytest.mark.parametrize(
    ("piece", "differs"),
    [
        (
            _piece("p0007-001", "p0008-001", "append_rows", repeated_header_rows=1),
            False,
        ),
        (
            _piece(
                "p0007-002",
                "p0008-003",
                "continue_text",
                markers=[
                    {
                        "cell": None,
                        "item": "p0008-003",
                        "row": None,
                        "text": "continued",
                    }
                ],
                text_join="space",
            ),
            False,
        ),
        (
            _piece(
                "p0007-001",
                "p0008-001",
                "merge_split_row",
                cell_joins=["repeat", "space"],
                markers=[{"cell": 0, "item": "p0008-001", "row": 1, "text": "(contd)"}],
                repeated_header_rows=1,
            ),
            False,
        ),
        (
            _piece(
                "p0007-001",
                "p0008-001",
                "merge_split_row",
                cell_joins=["repeat", "space"],
                markers=[{"cell": 0, "item": "p0008-001", "row": 2, "text": "(contd)"}],
                repeated_header_rows=1,
            ),
            True,
        ),
    ],
    ids=[
        "append-rows",
        "marker-on-start-item",
        "marker-on-start-row",
        "marker-on-other-row",
    ],
)
def test_appended_rows_and_a_marked_start_are_no_start_marker_difference(
    break_context: Callable[..., BreakContext],
    differs: bool,
    page_file: Callable[..., PageFile],
    page_item: Callable[..., Item],
    piece: dict[str, object],
) -> None:
    """A start that begins with a start marker is no difference in two cases.

    The survey's start markers are "PHONICS" and "Part". An ``append_rows`` piece is
    skipped, since new rows can begin with a start marker while the table carries
    on. So is a piece whose verdict names a continuation marker on its start item
    and, for a table, on the row its start text comes from. A marker on another
    row of the table leaves the difference.
    """

    earlier, later = _curriculum_pages(page_file, page_item)
    context = break_context(
        start_markers=[("PHONICS", "Starts a subject."), ("Part", "Starts a part.")]
    )

    differences = compare_with_hints(_verdict(piece), earlier, later, context)

    assert [difference.details for difference in differences["start_markers"]] == (
        [{"entry": None, "item": "p0008-001", "marker": "PHONICS"}] if differs else []
    )


def test_verdicts_that_differ_only_in_what_is_not_compared_match() -> None:
    """Repeated items, markers, containers, the reason and piece order are not compared.

    The verifier's verdict names the same two pieces in the other order, with no
    repeated item, marker or container and another reason.
    """

    kept = _verdict(
        _table_piece(),
        _piece("p0003-004", "p0004-004", "continue_text", text_join="space"),
        containers=[("p0003-c01", "p0004-c01")],
    )
    verifier = _verdict(
        _piece("p0003-004", "p0004-004", "continue_text", text_join="space"),
        _table_piece(markers=[], repeated_items=[]),
    ).model_copy(update={"reason": "Both carry on."})

    assert compare_verdicts(kept, verifier, page_index=3) == []


def test_only_one_verdict_continuing_is_the_one_difference() -> None:
    """When only the kept verdict continues, that alone is the difference.

    The difference names both of the kept verdict's pieces and points at the first
    one's end.
    """

    kept = _verdict(
        _table_piece(),
        _piece("p0003-004", "p0004-004", "continue_text", text_join="space"),
    )

    assert compare_verdicts(kept, _verdict(), page_index=3) == [
        CheckFailure(
            details={
                "entry": None,
                "field": "continues",
                "item": "p0003-003",
                "kept": True,
                "verifier": False,
            },
            message="verdicts_differ: the kept verdict says content continues, in "
            "piece 1 (p0003-003 to p0004-003) and piece 2 (p0003-004 to p0004-004), "
            "and the verifier's says nothing continues",
            page_index=3,
        )
    ]


def test_pieces_pair_by_end_then_by_start_and_unpaired_pieces_come_first() -> None:
    """Pieces pair by where they end, then by where they start.

    The kept verdict's first piece pairs by its start only, its second by its end
    only, and its third with nothing. The verifier's third piece pairs with
    nothing. The unpaired pieces come first, the kept verdict's before the
    verifier's, then each pair's differences in the kept verdict's order.
    """

    kept = _verdict(
        _piece("p0003-001", "p0004-001", "continue_text", text_join="space"),
        _piece("p0003-002", "p0004-002", "continue_text", text_join="space"),
        _piece("p0003-003", "p0004-003", "continue_text", text_join="space"),
    )
    verifier = _verdict(
        _piece("p0003-002", "p0004-009", "continue_text", text_join="space"),
        _piece("p0003-008", "p0004-001", "continue_text", text_join="space"),
        _piece("p0003-007", "p0004-007", "continue_text", text_join="space"),
    )

    differences = compare_verdicts(kept, verifier, page_index=3)

    assert [
        (
            difference.details["field"],
            difference.details["kept"],
            difference.details["verifier"],
            difference.details["item"],
        )
        for difference in differences
    ] == [
        ("piece", "p0003-003 to p0004-003", None, "p0003-003"),
        ("piece", None, "p0003-007 to p0004-007", "p0003-007"),
        ("end", "p0003-001", "p0003-008", "p0003-001"),
        ("start", "p0004-002", "p0004-009", "p0003-002"),
    ]
    assert differences[1].message == (
        "verdicts_differ: the verifier's piece 3 (p0003-007 to p0004-007), joined "
        "with continue_text, matches no piece of the kept verdict"
    )


def test_a_pair_with_the_same_join_differs_in_each_text_join_cell_and_header_row() -> (
    None
):
    """With the same join, the text join, each cell join and the header rows count.

    The table pieces differ in both cell joins and in the number of repeated header
    rows, and the text pieces in their text join. Each is one difference, and a
    cell's difference names the cell.
    """

    kept = _verdict(
        _table_piece(),
        _piece("p0003-004", "p0004-004", "continue_text", text_join="space"),
    )
    verifier = _verdict(
        _table_piece(cell_joins=["repeat", "space"], repeated_header_rows=0),
        _piece("p0003-004", "p0004-004", "continue_text", text_join="no_space"),
    )

    differences = compare_verdicts(kept, verifier, page_index=3)

    assert [difference.details for difference in differences] == [
        {
            "cell": 0,
            "entry": None,
            "field": "cell_joins",
            "item": "p0003-003",
            "kept": None,
            "verifier": "repeat",
        },
        {
            "cell": 1,
            "entry": None,
            "field": "cell_joins",
            "item": "p0003-003",
            "kept": "no_space",
            "verifier": "space",
        },
        {
            "entry": None,
            "field": "repeated_header_rows",
            "item": "p0003-003",
            "kept": 1,
            "verifier": 0,
        },
        {
            "entry": None,
            "field": "text_join",
            "item": "p0003-004",
            "kept": "space",
            "verifier": "no_space",
        },
    ]
    assert differences[0].message == (
        "verdicts_differ: in piece 1 (p0003-003 to p0004-003), the join of cell 0 is "
        "null in the kept verdict and repeat in the verifier's"
    )


def test_a_pair_with_different_joins_differs_in_the_join_alone() -> None:
    """A different join is the pair's one difference, since the rest follows from it.

    The verifier appends the table's rows instead of merging the split row, so it
    has no cell joins.
    """

    kept = _verdict(_table_piece())
    verifier = _verdict(_table_piece(cell_joins=None, join="append_rows"))

    assert compare_verdicts(kept, verifier, page_index=3) == [
        CheckFailure(
            details={
                "entry": None,
                "field": "join",
                "item": "p0003-003",
                "kept": "merge_split_row",
                "verifier": "append_rows",
            },
            message="verdicts_differ: in piece 1 (p0003-003 to p0004-003), the join "
            "is merge_split_row in the kept verdict and append_rows in the verifier's",
            page_index=3,
        )
    ]


def test_cell_joins_of_another_length_are_one_difference() -> None:
    """Cell-join lists of different lengths differ once, as whole lists."""

    kept = _verdict(_table_piece())
    verifier = _verdict(_table_piece(cell_joins=[None, "no_space", "space"]))

    (difference,) = compare_verdicts(kept, verifier, page_index=3)

    assert difference.details == {
        "entry": None,
        "field": "cell_joins",
        "item": "p0003-003",
        "kept": [None, "no_space"],
        "verifier": [None, "no_space", "space"],
    }

"""Page-break verification's checks and hint on a verdict for one break.

Pydantic checks only the verdict's shape. The checks test the verdict against the
page files of the two pages. Every item, entry and container it names is on the page
it names, ``continues`` agrees with the pieces, no item ends or starts two pieces,
each join fits the kinds of the items it joins and sets only the fields it uses, no
piece ends or starts in page furniture, and repeated header rows, repeated items and
continuation markers match text printed on the pages. While retries remain, a
verdict that fails a check is sent back to the model.

The hint compares the verdict with the survey's start markers, text that marks where
a new unit of content starts. A piece whose start on the later page begins with one
may join content that does not continue, unless it appends table rows or the verdict
names a continuation marker in that start. The survey can be wrong, and the model's
reading of the pages decides. A hint difference never sends a verdict back. The
verdict file records it, and the review list shows it unless the verifier's own
verdict for the break matches the kept verdict.

The comparison of the kept verdict for a break with the verifier's gives one
difference when only one of them says content continues, one for each piece only one
of them gives, and one for each compared field that differs in a piece both give.
Repeated items, markers, containers and the reason are not compared.

Text is compared in `comparison_form` and as runs of three characters, so the checks
hold in any script and assume no writing direction. Each check returns every failure
it finds, so one retry message can name every failure and the verdict file can
record them all. A failure names the item, list entry, container or table cell it is
about in ``details``, and the page it is on in ``page_index``.
"""

# Standard Library
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from operator import attrgetter
from typing import Literal

# Package Library
from pydelity.extracting.schemas import Item, PageFile, TableCell
from pydelity.extracting.text_layer import comparison_form, trigrams
from pydelity.review import (
    BreakCheckName,
    BreakComparisonName,
    BreakHintName,
    CheckFailure,
    ReviewIssue,
)
from pydelity.surveying.schemas import ItemKind, ItemRole
from pydelity.verifying.schemas import (
    BreakCheckResult,
    BreakContext,
    BreakHintResult,
    BreakVerdict,
    BreakVerification,
    ContinuationMarker,
    ContinuingPiece,
    Join,
    TextJoin,
)

# How the cells of a merged row join the cells above them, besides null.
_CELL_JOINS: tuple[TextJoin, ...] = ("space", "no_space", "dehyphenate", "repeat")

# The kinds of item each join can end in on the earlier page.
_JOIN_END_KINDS: dict[Join, frozenset[ItemKind]] = {
    "append_rows": frozenset({ItemKind.TABLE}),
    "continue_entry": frozenset({ItemKind.LIST, ItemKind.TEXT}),
    "continue_text": frozenset({ItemKind.CODE, ItemKind.TEXT}),
    "merge_split_row": frozenset({ItemKind.TABLE}),
    "new_entry": frozenset({ItemKind.LIST, ItemKind.TEXT}),
}

# Which of `_JOIN_ONLY_FIELDS` each join sets. A join leaves the others null, apart
# from ``continue_entry``, which sets each entry whose end is a list item.
_JOIN_FIELDS: dict[Join, frozenset[str]] = {
    "append_rows": frozenset({"repeated_header_rows"}),
    "continue_entry": frozenset({"text_join"}),
    "continue_text": frozenset({"text_join"}),
    "merge_split_row": frozenset({"cell_joins", "repeated_header_rows"}),
    "new_entry": frozenset(),
}

# The piece fields that only some joins use.
_JOIN_ONLY_FIELDS = (
    "cell_joins",
    "earlier_entry",
    "later_entry",
    "repeated_header_rows",
    "text_join",
)

# The kinds of item each join can start in on the later page.
_JOIN_START_KINDS: dict[Join, frozenset[ItemKind]] = {
    "append_rows": frozenset({ItemKind.TABLE}),
    "continue_entry": frozenset({ItemKind.LIST, ItemKind.TEXT}),
    "continue_text": frozenset({ItemKind.CODE, ItemKind.TEXT}),
    "merge_split_row": frozenset({ItemKind.TABLE}),
    "new_entry": frozenset({ItemKind.LIST}),
}

# How alike two texts whose comparison forms differ must be to match, as the Dice
# coefficient of their runs of three characters.
_MATCH_DICE = 0.8

# How many characters each of two different comparison forms needs before they can
# match.
_MIN_MATCH_CHARS = 3

# How text that is not code joins across the break.
_PROSE_JOINS: tuple[TextJoin, ...] = ("space", "no_space", "dehyphenate")

# The joins that continue a table.
_TABLE_JOINS: tuple[Join, ...] = ("append_rows", "merge_split_row")

# A check on one piece for one join, after the checks every join gets.
type _JoinRule = Callable[[_Piece], list[CheckFailure]]

# The fields of two verdicts that a difference between them can be about.
type _VerdictField = Literal[
    "cell_joins",
    "continues",
    "end",
    "join",
    "piece",
    "repeated_header_rows",
    "start",
    "text_join",
]

# A check on a verdict, given the page files of the pages before and after the break.
type Check = Callable[[BreakVerdict, PageFile, PageFile], list[CheckFailure]]

# A hint on a verdict, given the page files and the break's context.
type Hint = Callable[
    [BreakVerdict, PageFile, PageFile, BreakContext], list[CheckFailure]
]


@dataclass(frozen=True, kw_only=True)
class _Compared:
    """One compared field of two paired pieces, with each verdict's value.

    Attributes
    ----------
    cell
        The cell's position in the merged row, from 0, for one cell's join, else
        ``None``.
    field
        The field.
    kept
        The kept verdict's value.
    label
        How messages name the field, such as ``the text join``.
    verifier
        The verifier's value.
    """

    cell: int | None = None
    field: _VerdictField
    kept: object
    label: str
    verifier: object


@dataclass(frozen=True)
class _Piece:
    """A continuing piece with the items it joins and the page files they are on.

    Attributes
    ----------
    earlier
        The page file of the page before the break.
    earlier_items
        The earlier page's items by ID.
    end
        The item the piece ends in, or ``None`` when the earlier page has no item
        with its ID.
    later
        The page file of the page after the break.
    later_items
        The later page's items by ID.
    name
        How messages name the piece, such as ``piece 2 (p0003-007 to p0004-001)``.
    piece
        The piece as the verdict gives it.
    start
        The item the piece starts in, or ``None`` when the later page has no item
        with its ID.
    """

    earlier: PageFile
    earlier_items: Mapping[str, Item]
    end: Item | None
    later: PageFile
    later_items: Mapping[str, Item]
    name: str
    piece: ContinuingPiece
    start: Item | None


def _all_of(values: Sequence[str]) -> str:
    """List values for a message, all of them together.

    Parameters
    ----------
    values
        The values, at least one.

    Returns
    -------
    str
        The values separated by commas, with ``and`` before the last.

    Examples
    --------
    >>> _all_of(["piece 1", "piece 2", "piece 3"])
    'piece 1, piece 2 and piece 3'
    """

    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + " and " + values[-1]


def _alternatives(values: Sequence[str]) -> str:
    """List values as alternatives for a message.

    Parameters
    ----------
    values
        The values, at least one.

    Returns
    -------
    str
        The values separated by commas, with ``or`` before the last.

    Examples
    --------
    >>> _alternatives(["space", "no_space", "dehyphenate"])
    'space, no_space or dehyphenate'
    """

    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + " or " + values[-1]


def _append_rows_problems(piece: _Piece) -> list[CheckFailure]:
    """Check that ``repeated_header_rows`` fits the later table of ``append_rows``.

    Parameters
    ----------
    piece
        The piece.

    Returns
    -------
    list[CheckFailure]
        A ``joins`` failure when the later table item has no table, or when
        ``repeated_header_rows`` is below 0 or above its number of rows.
    """

    start = piece.start
    if start is None or start.kind != ItemKind.TABLE:
        return []

    rows = _table_rows(start)
    count = piece.piece.repeated_header_rows
    if rows is None:
        return [
            _failure(
                "joins",
                f"{piece.name} appends rows to {start.id}, a table item with no table",
                details={"item": start.id},
                page=piece.later,
            )
        ]
    if count is not None and not 0 <= count <= len(rows):
        return [
            _failure(
                "joins",
                f"{piece.name} has repeated_header_rows {count}, but it must be from 0 "
                f"to {len(rows)}, the number of rows in {start.id}",
                details={"item": start.id},
                page=piece.later,
            )
        ]
    return []


def _cell_join_problems(
    piece: _Piece, *, cells: Sequence[TableCell], row: int
) -> list[CheckFailure]:
    """Check ``cell_joins`` against the merged row of ``merge_split_row``.

    Parameters
    ----------
    piece
        The piece.
    cells
        The merged row's cells.
    row
        The merged row's position among the later table's rows, from 0.

    Returns
    -------
    list[CheckFailure]
        A ``joins`` failure when ``cell_joins`` does not have one value per cell,
        and one when it uses ``newline``, which only joins code.
    """

    cell_joins = piece.piece.cell_joins
    if cell_joins is None:
        return []

    failures = []
    item = piece.piece.later_item
    if len(cell_joins) != len(cells):
        failures.append(
            _failure(
                "joins",
                f"{piece.name} gives {len(cell_joins)} cell_joins, but the merged row, "
                f"row {row} of {item}, has {len(cells)} cells. Give one value per cell",
                details={"item": item, "row": row},
                page=piece.later,
            )
        )
    if "newline" in cell_joins:
        failures.append(
            _failure(
                "joins",
                f"{piece.name} uses newline in cell_joins, but table cells join with "
                f"{_alternatives(_CELL_JOINS)}, or null when a cell has no text to "
                "join",
                details={"item": item, "row": row},
                page=piece.later,
            )
        )
    return failures


def _cell_join_values(
    kept: list[TextJoin | None] | None, verifier: list[TextJoin | None] | None
) -> list[_Compared]:
    """Pair the cell joins of two paired pieces for comparison.

    Parameters
    ----------
    kept
        The kept verdict's piece's ``cell_joins``.
    verifier
        The verifier's piece's ``cell_joins``.

    Returns
    -------
    list[_Compared]
        One value per cell when both lists have the same length, else one for the
        whole list.
    """

    if kept is None or verifier is None or len(kept) != len(verifier):
        return [
            _Compared(
                field="cell_joins",
                kept=kept,
                label="the cell_joins list",
                verifier=verifier,
            )
        ]
    return [
        _Compared(
            cell=cell,
            field="cell_joins",
            kept=kept_join,
            label=f"the join of cell {cell}",
            verifier=verifier_join,
        )
        for cell, (kept_join, verifier_join) in enumerate(
            zip(kept, verifier, strict=True)
        )
    ]


def _container_id_problems(
    verdict: BreakVerdict, *, earlier: PageFile, later: PageFile
) -> list[CheckFailure]:
    """Check that each continuing container is on the page it is named for.

    Parameters
    ----------
    verdict
        The verdict.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.

    Returns
    -------
    list[CheckFailure]
        An ``ids`` failure for each container ID the page it is named for does not
        have.
    """

    failures = []
    for page, side, ids in (
        (earlier, "earlier", [container.earlier for container in verdict.containers]),
        (later, "later", [container.later for container in verdict.containers]),
    ):
        known = {container.id for container in page.containers}
        failures += [
            _failure(
                "ids",
                f"containers names {container}, which is not a container on the "
                f"{side} page",
                details={"container": container},
                page=page,
            )
            for container in ids
            if container not in known
        ]
    return failures


def _continue_entry_problems(piece: _Piece) -> list[CheckFailure]:
    """Check the text join and entries of ``continue_entry``.

    Parameters
    ----------
    piece
        The piece.

    Returns
    -------
    list[CheckFailure]
        A ``joins`` failure when the text join is ``newline`` or ``repeat``, when no
        entry is named, when an end in a list item is not its last or first entry,
        and when an end in a text item names an entry.
    """

    failures = []
    text_join = piece.piece.text_join
    if text_join is not None and text_join not in _PROSE_JOINS:
        failures.append(
            _failure(
                "joins",
                f"{piece.name} uses continue_entry with text_join {text_join}, but a "
                f"list entry joins with {_alternatives(_PROSE_JOINS)}"
                f"{_repeat_note(text_join)}",
                details={"item": piece.piece.earlier_item},
                page=None,
            )
        )
    if piece.piece.earlier_entry is None and piece.piece.later_entry is None:
        failures.append(
            _failure(
                "joins",
                f"{piece.name} uses continue_entry but names no list entry. "
                "continue_entry joins text where at least one end is a list entry, "
                "and continue_text joins two text items",
                details={"item": piece.piece.earlier_item},
                page=None,
            )
        )
    for failure in (
        _entry_end_problem(piece, last=True),
        _entry_end_problem(piece, last=False),
    ):
        if failure is not None:
            failures.append(failure)
    return failures


def _continue_text_problems(piece: _Piece) -> list[CheckFailure]:
    """Check that ``continue_text`` joins two items of one kind with a fitting join.

    Parameters
    ----------
    piece
        The piece.

    Returns
    -------
    list[CheckFailure]
        A ``joins`` failure when the two items are of different kinds, and one when
        the text join does not fit the earlier item's kind: ``newline`` for code,
        and ``space``, ``no_space`` or ``dehyphenate`` for text.
    """

    end, start = piece.end, piece.start
    kinds = _JOIN_END_KINDS["continue_text"]
    if end is None or end.kind not in kinds:
        return []

    failures = []
    if start is not None and start.kind in kinds and start.kind != end.kind:
        failures.append(
            _failure(
                "joins",
                f"{piece.name} joins {end.id}, a {end.kind} item, to {start.id}, a "
                f"{start.kind} item, but continue_text joins two items of one kind",
                details={"item": start.id},
                page=piece.later,
            )
        )
    fitting = ("newline",) if end.kind == ItemKind.CODE else _PROSE_JOINS
    text_join = piece.piece.text_join
    if text_join is not None and text_join not in fitting:
        failures.append(
            _failure(
                "joins",
                f"{piece.name} joins {end.kind} with text_join {text_join}, but "
                f"{end.kind} joins with {_alternatives(fitting)}"
                f"{_repeat_note(text_join)}",
                details={"item": end.id},
                page=piece.earlier,
            )
        )
    return failures


def _continues_difference(
    kept: BreakVerdict, verifier: BreakVerdict, *, page_index: int
) -> CheckFailure:
    """Describe two verdicts of which only one says content continues.

    Parameters
    ----------
    kept
        The kept verdict.
    verifier
        The verifier's verdict.
    page_index
        The page before the break.

    Returns
    -------
    CheckFailure
        The difference, naming the pieces of the verdict that continues and pointing
        at the first of them.
    """

    if kept.continues:
        continuing, owner, other = kept, "kept verdict", "verifier's"
    else:
        continuing, owner, other = verifier, "verifier's verdict", "kept verdict"
    names = [
        _piece_name(position, piece)
        for position, piece in enumerate(continuing.pieces, start=1)
    ]
    pieces = f", in {_all_of(names)}, and" if names else " but names no piece, and"
    return _difference(
        _Compared(
            field="continues",
            kept=kept.continues,
            label="whether content continues",
            verifier=verifier.continues,
        ),
        f"the {owner} says content continues{pieces} the {other} says nothing "
        "continues",
        page_index=page_index,
        where=continuing.pieces[0] if continuing.pieces else None,
    )


def _dice(first: str, second: str) -> float:
    """Measure how alike two texts are by their runs of three characters.

    Parameters
    ----------
    first
        One text, in comparison form.
    second
        The other text, in comparison form.

    Returns
    -------
    float
        Twice the number of runs the two share, divided by the number of runs in
        both, from 0 to 1. It is 0 when neither has a run.
    """

    first_runs = trigrams(first)
    second_runs = trigrams(second)
    total = first_runs.total() + second_runs.total()
    if total == 0:
        return 0.0
    return 2 * (first_runs & second_runs).total() / total


def _difference(
    value: _Compared,
    message: str,
    *,
    page_index: int,
    where: ContinuingPiece | None,
) -> CheckFailure:
    """Make a difference between two verdicts, with a message naming the comparison.

    Parameters
    ----------
    value
        The field that differs, with each verdict's value.
    message
        What differs.
    page_index
        The page before the break.
    where
        The piece whose end on the earlier page the difference points at, or
        ``None`` when it points at no piece.

    Returns
    -------
    CheckFailure
        The difference.
    """

    details: dict[str, object] = {} if value.cell is None else {"cell": value.cell}
    details |= {
        "entry": None if where is None else where.earlier_entry,
        "field": value.field,
        "item": None if where is None else where.earlier_item,
        "kept": value.kept,
        "verifier": value.verifier,
    }
    return CheckFailure(
        details=details,
        message=f"verdicts_differ: {message}",
        page_index=page_index,
    )


def _duplicates(
    names: Iterable[str | None], *, key: str, message: str, page: PageFile
) -> list[CheckFailure]:
    """Find the IDs named more than once.

    Parameters
    ----------
    names
        The IDs, with ``None`` for a field left null.
    key
        The ``details`` key for the ID.
    message
        The failure's message, with ``{name}`` where the ID goes.
    page
        The page the IDs are on.

    Returns
    -------
    list[CheckFailure]
        A ``duplicates`` failure for each ID named more than once, in the order of
        their first mention.
    """

    counts = Counter(name for name in names if name is not None)
    return [
        _failure(
            "duplicates", message.format(name=name), details={key: name}, page=page
        )
        for name, count in counts.items()
        if count > 1
    ]


def _end_id_problems(piece: _Piece) -> list[CheckFailure]:
    """Check that a piece's ends are items and entries on the pages they are named for.

    Parameters
    ----------
    piece
        The piece.

    Returns
    -------
    list[CheckFailure]
        An ``ids`` failure for an end that is not an item on its page, and for an
        entry that is not one of its item's entries.
    """

    failures = []
    for item, item_id, entry, page, side, verb in (
        (
            piece.end,
            piece.piece.earlier_item,
            piece.piece.earlier_entry,
            piece.earlier,
            "earlier",
            "ends",
        ),
        (
            piece.start,
            piece.piece.later_item,
            piece.piece.later_entry,
            piece.later,
            "later",
            "starts",
        ),
    ):
        if item is None:
            failures.append(
                _failure(
                    "ids",
                    f"{piece.name} {verb} in {item_id}, which is not an item on the "
                    f"{side} page",
                    details={"item": item_id},
                    page=page,
                )
            )
        elif entry is not None and entry not in _entry_ids(item):
            failures.append(
                _failure(
                    "ids",
                    f"{piece.name} {verb} in the entry {entry}, which is not an entry "
                    f"of {item_id}",
                    details={"entry": entry, "item": item_id},
                    page=page,
                )
            )
    return failures


def _entry_end_message(
    *, entry: str | None, field: str, item: Item, last: bool
) -> str | None:
    """Say what is wrong with one end of ``continue_entry``, given its item's kind.

    Parameters
    ----------
    entry
        The entry the piece names at this end, if any.
    field
        The piece's field for the entry, ``earlier_entry`` or ``later_entry``.
    item
        The item at this end.
    last
        Whether the end is on the earlier page, where a list ends in its last entry.
        On the later page a list starts in its first entry.

    Returns
    -------
    str | None
        The problem when a text item's end names an entry, when a list item has no
        entries, or when a list item's end is not its last or first entry, and
        otherwise ``None``.
    """

    if item.kind == ItemKind.TEXT:
        if entry is None:
            return None
        return f"{item.id} is a text item, so {field} must be null"
    if item.kind != ItemKind.LIST:
        return None

    entries = _entry_ids(item)
    if not entries:
        return f"{item.id} is a list item with no entries"
    wanted = entries[-1] if last else entries[0]
    if entry == wanted:
        return None
    return (
        f"{item.id} is a list item, so {field} must be its "
        f"{'last' if last else 'first'} entry, {wanted}"
    )


def _entry_end_problem(piece: _Piece, *, last: bool) -> CheckFailure | None:
    """Check one end of ``continue_entry`` against the kind of its item.

    Parameters
    ----------
    piece
        The piece.
    last
        Whether to check the end on the earlier page, rather than the start on the
        later page.

    Returns
    -------
    CheckFailure | None
        A ``joins`` failure for the problem `_entry_end_message` finds, if any.
    """

    if last:
        entry, field, item, page = (
            piece.piece.earlier_entry,
            "earlier_entry",
            piece.end,
            piece.earlier,
        )
    else:
        entry, field, item, page = (
            piece.piece.later_entry,
            "later_entry",
            piece.start,
            piece.later,
        )
    if item is None:
        return None

    message = _entry_end_message(entry=entry, field=field, item=item, last=last)
    if message is None:
        return None
    return _failure(
        "joins",
        f"{piece.name} uses continue_entry, but {message}",
        details={"entry": entry, "item": item.id},
        page=page,
    )


def _entry_ids(item: Item) -> list[str]:
    """List the IDs of a list item's entries.

    Parameters
    ----------
    item
        The item.

    Returns
    -------
    list[str]
        The entries' IDs in order; empty when the item has no entries.
    """

    return [entry.id for entry in item.entries or []]


def _entry_text(item: Item, entry_id: str) -> str | None:
    """Find the text of one of a list item's entries.

    Parameters
    ----------
    item
        The list item.
    entry_id
        The entry's ID.

    Returns
    -------
    str | None
        The entry's text, or ``None`` when the item has no entry with that ID.
    """

    return next(
        (entry.text for entry in item.entries or [] if entry.id == entry_id), None
    )


def _failure(
    check: BreakCheckName | BreakHintName,
    message: str,
    *,
    details: dict[str, object],
    page: PageFile | None,
) -> CheckFailure:
    """Make a failure or difference whose message starts with the check's name.

    Parameters
    ----------
    check
        The check that failed, or the hint the verdict differs from.
    message
        What is wrong, or what differs.
    details
        The IDs of the item, entry, container or cell the problem is about.
    page
        The page the problem is on, or ``None`` when it is about the verdict as a
        whole or a piece across both pages.

    Returns
    -------
    CheckFailure
        The failure.
    """

    return CheckFailure(
        details=details,
        message=f"{check}: {message}",
        page_index=None if page is None else page.page_index,
    )


def _first_unmatched_row(*, earlier: Sequence[str], later: Sequence[str]) -> int | None:
    """Match rows of the later table, in order, to distinct rows of the earlier one.

    Parameters
    ----------
    earlier
        The earlier table's rows that may be repeated, as comparison forms.
    later
        The later table's repeated header rows, as comparison forms.

    Returns
    -------
    int | None
        The position of the first later row that has no match among the earlier
        rows after the one the row before it matched, or ``None`` when every row
        matches.

    Examples
    --------
    >>> _first_unmatched_row(earlier=["title", "nameage"], later=["nameage"])
    >>> _first_unmatched_row(earlier=["nameage", "title"], later=["title", "nameage"])
    1
    """

    position = 0
    for index, row in enumerate(later):
        while position < len(earlier) and not _forms_match(row, earlier[position]):
            position += 1
        if position == len(earlier):
            return index
        position += 1
    return None


def _forms_match(first: str, second: str) -> bool:
    """Decide whether two texts in comparison form match.

    Parameters
    ----------
    first
        One text, in comparison form.
    second
        The other text, in comparison form.

    Returns
    -------
    bool
        Whether they are equal, or both have at least `_MIN_MATCH_CHARS` characters
        and a `_dice` coefficient of at least `_MATCH_DICE`. Two empty texts match.

    Examples
    --------
    >>> _forms_match("chapter3generalprovisions", "chapter3generalprovisons")
    True
    >>> _forms_match("ab", "abc")
    False
    """

    if first == second:
        return True
    if min(len(first), len(second)) < _MIN_MATCH_CHARS:
        return False
    return _dice(first, second) >= _MATCH_DICE


def _header_row_problems(piece: _Piece, *, count: int) -> list[CheckFailure]:
    """Check that a piece's repeated header rows repeat rows of the earlier table.

    Parameters
    ----------
    piece
        The piece.
    count
        Its ``repeated_header_rows``, above 0.

    Returns
    -------
    list[CheckFailure]
        A ``header_rows`` failure when either table is missing, when the later table
        has fewer rows, or when one of its first ``count`` rows matches none of the
        earlier table's rows left in order.
    """

    end, start = piece.end, piece.start
    if end is None or start is None:
        return []

    claim = (
        f"{piece.name} says the first {count} rows of {start.id} repeat the header "
        f"of {end.id}"
    )
    later_rows = _table_rows(start)
    if later_rows is None or len(later_rows) < count:
        return [
            _failure(
                "header_rows",
                f"{claim}, but {start.id} has {len(later_rows or [])} table rows",
                details={"item": start.id},
                page=piece.later,
            )
        ]
    if end.table is None:
        return [
            _failure(
                "header_rows",
                f"{claim}, but {end.id} has no table",
                details={"item": end.id},
                page=piece.earlier,
            )
        ]

    candidates = end.table.rows[: count + max(end.table.header_rows, 0)]
    unmatched = _first_unmatched_row(
        earlier=[comparison_form(_row_text(row)) for row in candidates],
        later=[comparison_form(_row_text(row)) for row in later_rows[:count]],
    )
    if unmatched is None:
        return []
    return [
        _failure(
            "header_rows",
            f"{claim}, but row {unmatched} of {start.id} matches none of the first "
            f"{len(candidates)} rows of {end.id}, in order",
            details={"item": start.id, "row": unmatched},
            page=piece.later,
        )
    ]


def _issue(
    failure: CheckFailure,
    *,
    ids: frozenset[str],
    name: BreakCheckName | BreakComparisonName | BreakHintName,
    page_index: int,
) -> ReviewIssue:
    """Turn a check failure, hint difference or verdict difference into a review issue.

    Parameters
    ----------
    failure
        The failure or difference.
    ids
        The IDs of the items and containers on both pages of the break.
    name
        The check, hint or comparison that found it.
    page_index
        The page before the break.

    Returns
    -------
    ReviewIssue
        The issue, naming both pages in its message and its item or container when
        one of the pages has it.
    """

    return ReviewIssue(
        check=name,
        details=failure.details,
        item_id=_issue_item(failure.details, ids=ids),
        message=f"{_pages(page_index)}: {failure.message}",
        page_index=page_index,
        step="page_breaks",
    )


def _issue_item(details: Mapping[str, object], *, ids: frozenset[str]) -> str | None:
    """Find the item or container a failure names, when the break's pages have it.

    Parameters
    ----------
    details
        The failure's ``details``.
    ids
        The IDs of the items and containers on both pages of the break.

    Returns
    -------
    str | None
        The ``item`` the failure names, or else its ``container``, when one of the
        pages has it, and otherwise ``None``.
    """

    for key in ("item", "container"):
        value = details.get(key)
        if isinstance(value, str) and value in ids:
            return value
    return None


def _items(page: PageFile) -> dict[str, Item]:
    """Index a page's items by ID.

    Parameters
    ----------
    page
        The page file.

    Returns
    -------
    dict[str, Item]
        The items by ID, in reading order.
    """

    return {item.id: item for item in page.items}


def _join_field_problems(piece: _Piece) -> list[CheckFailure]:
    """Check that a piece sets the fields its join uses and leaves the others null.

    Parameters
    ----------
    piece
        The piece.

    Returns
    -------
    list[CheckFailure]
        A ``joins`` failure for each field that should be set and is null, or
        should be null and is set. The entries of ``continue_entry`` are left to
        `_continue_entry_problems`.
    """

    join = piece.piece.join
    used = _JOIN_FIELDS[join]
    failures = []
    for field in _JOIN_ONLY_FIELDS:
        if join == "continue_entry" and field in ("earlier_entry", "later_entry"):
            continue
        is_set = getattr(piece.piece, field) is not None
        if is_set != (field in used):
            failures.append(
                _failure(
                    "joins",
                    f"{piece.name} uses {join}, so {field} must be "
                    f"{'set' if field in used else 'null'}",
                    details={"item": piece.piece.earlier_item},
                    page=None,
                )
            )
    return failures


def _join_kind_problems(piece: _Piece) -> list[CheckFailure]:
    """Check that a piece's ends are of kinds its join joins.

    Parameters
    ----------
    piece
        The piece.

    Returns
    -------
    list[CheckFailure]
        A ``joins`` failure for each end whose item is of a kind the join does not
        end or start in. Figures, fields and formulas fit no join.
    """

    join = piece.piece.join
    return [
        _failure(
            "joins",
            f"{piece.name} uses {join}, which {verb} in "
            f"{_alternatives(sorted(kinds))} items, but it {verb} in {item.id}, a "
            f"{item.kind} item",
            details={"item": item.id},
            page=page,
        )
        for item, page, verb, kinds in (
            (piece.end, piece.earlier, "ends", _JOIN_END_KINDS[join]),
            (piece.start, piece.later, "starts", _JOIN_START_KINDS[join]),
        )
        if item is not None and item.kind not in kinds
    ]


def _marker_carrier(marker: ContinuationMarker, item: Item | None) -> str | None:
    """Find the text of the item, row or cell that carries a continuation marker.

    Parameters
    ----------
    marker
        The marker.
    item
        The item it names, if it is on the later page.

    Returns
    -------
    str | None
        The cell's text when the marker names a cell, the row's cell texts joined
        when it names only a row, and otherwise the item's printed text. ``None``
        when the item, row or cell is missing.
    """

    if item is None:
        return None
    if marker.row is None:
        return _printed_text(item) if marker.cell is None else None

    rows = _table_rows(item)
    if rows is None or not 0 <= marker.row < len(rows):
        return None
    cells = rows[marker.row]
    if marker.cell is None:
        return _row_text(cells)
    if not 0 <= marker.cell < len(cells):
        return None
    return cells[marker.cell].text or ""


def _marker_details(marker: ContinuationMarker) -> dict[str, object]:
    """Name the item, row and cell of a continuation marker for a failure.

    Parameters
    ----------
    marker
        The marker.

    Returns
    -------
    dict[str, object]
        The marker's ``cell``, ``item`` and ``row``.
    """

    return {"cell": marker.cell, "item": marker.item, "row": marker.row}


def _marker_id_problems(piece: _Piece) -> list[CheckFailure]:
    """Check that each of a piece's markers is on an item, row and cell that exist.

    Parameters
    ----------
    piece
        The piece.

    Returns
    -------
    list[CheckFailure]
        An ``ids`` failure for each marker whose item is not on the later page,
        whose row or cell the item's table does not have, or that names a cell
        without a row.
    """

    failures = []
    for marker in piece.piece.markers:
        problem = _marker_place_problem(marker, piece.later_items.get(marker.item))
        if problem is not None:
            failures.append(
                _failure(
                    "ids",
                    f"{piece.name} has the marker {marker.text!r} on "
                    f"{_marker_place(marker)}, but {problem}",
                    details=_marker_details(marker),
                    page=piece.later,
                )
            )
    return failures


def _marker_place(marker: ContinuationMarker) -> str:
    """Describe where a continuation marker is, for a message.

    Parameters
    ----------
    marker
        The marker.

    Returns
    -------
    str
        Such as ``p0004-002``, ``row 0 of p0004-002`` or
        ``row 0, cell 2 of p0004-002``.
    """

    if marker.row is None:
        return marker.item
    if marker.cell is None:
        return f"row {marker.row} of {marker.item}"
    return f"row {marker.row}, cell {marker.cell} of {marker.item}"


def _marker_place_problem(marker: ContinuationMarker, item: Item | None) -> str | None:
    """Say what is wrong with where a continuation marker is.

    Parameters
    ----------
    marker
        The marker.
    item
        The item it names, if it is on the later page.

    Returns
    -------
    str | None
        Why the item, row or cell the marker names does not exist, or ``None`` when
        it does.
    """

    if item is None:
        return f"{marker.item} is not an item on the later page"
    if marker.row is None:
        return None if marker.cell is None else "the marker gives a cell and no row"

    rows = _table_rows(item)
    if rows is None:
        return f"{item.id} has no table rows"
    if not 0 <= marker.row < len(rows):
        return f"{item.id} has no row {marker.row}"
    if marker.cell is not None and not 0 <= marker.cell < len(rows[marker.row]):
        return f"row {marker.row} of {item.id} has no cell {marker.cell}"
    return None


def _merge_split_row_problems(piece: _Piece) -> list[CheckFailure]:
    """Check the tables, header rows and cell joins of ``merge_split_row``.

    Parameters
    ----------
    piece
        The piece.

    Returns
    -------
    list[CheckFailure]
        A ``joins`` failure when either table has no rows, when
        ``repeated_header_rows`` leaves no row of the later table to merge, and for
        each problem with ``cell_joins``.
    """

    failures = []
    for item, page in ((piece.end, piece.earlier), (piece.start, piece.later)):
        if item is not None and item.kind == ItemKind.TABLE and not _table_rows(item):
            failures.append(
                _failure(
                    "joins",
                    f"{piece.name} merges a split row, but {item.id} has no table rows",
                    details={"item": item.id},
                    page=page,
                )
            )

    rows = _table_rows(piece.start)
    count = piece.piece.repeated_header_rows
    if not rows or count is None:
        return failures
    if not 0 <= count < len(rows):
        return [
            *failures,
            _failure(
                "joins",
                f"{piece.name} has repeated_header_rows {count}, but it must be from 0 "
                f"to {len(rows) - 1} so that a row of {piece.piece.later_item} is "
                "left to merge",
                details={"item": piece.piece.later_item},
                page=piece.later,
            ),
        ]
    return failures + _cell_join_problems(piece, cells=rows[count], row=count)


# The checks of the joins that need more than the checks every join gets.
_JOIN_RULES: dict[Join, _JoinRule] = {
    "append_rows": _append_rows_problems,
    "continue_entry": _continue_entry_problems,
    "continue_text": _continue_text_problems,
    "merge_split_row": _merge_split_row_problems,
}


def _page_ids(page: PageFile) -> frozenset[str]:
    """Collect the IDs of a page's items and containers.

    Parameters
    ----------
    page
        The page file.

    Returns
    -------
    frozenset[str]
        The IDs.
    """

    return frozenset(item.id for item in page.items) | frozenset(
        container.id for container in page.containers
    )


def _pages(page_index: int) -> str:
    """Name a break's two pages by number, for a review issue's message.

    Parameters
    ----------
    page_index
        The page before the break (0-based).

    Returns
    -------
    str
        Such as ``pages 4 and 5``, numbered from 1 as a PDF viewer shows them.

    Examples
    --------
    >>> _pages(3)
    'pages 4 and 5'
    """

    return f"pages {page_index + 1} and {page_index + 2}"


def _pair_differences(
    kept: ContinuingPiece, verifier: ContinuingPiece, *, name: str, page_index: int
) -> list[CheckFailure]:
    """Compare two paired pieces field by field.

    The end, the start and the join are compared first. When the joins are the
    same, the text join, the cell joins and the number of repeated header rows are
    compared too. When they differ, the other fields follow from the join and are
    not compared.

    Parameters
    ----------
    kept
        The kept verdict's piece.
    verifier
        The verifier's piece.
    name
        How messages name the kept verdict's piece.
    page_index
        The page before the break.

    Returns
    -------
    list[CheckFailure]
        A difference for each compared field that differs, and for each cell whose
        join differs.
    """

    compared = [
        _Compared(
            field="end",
            kept=_point(kept.earlier_item, kept.earlier_entry),
            label="the end",
            verifier=_point(verifier.earlier_item, verifier.earlier_entry),
        ),
        _Compared(
            field="start",
            kept=_point(kept.later_item, kept.later_entry),
            label="the start",
            verifier=_point(verifier.later_item, verifier.later_entry),
        ),
        _Compared(
            field="join", kept=kept.join, label="the join", verifier=verifier.join
        ),
    ]
    if kept.join == verifier.join:
        compared.append(
            _Compared(
                field="text_join",
                kept=kept.text_join,
                label="the text join",
                verifier=verifier.text_join,
            )
        )
        compared += _cell_join_values(kept.cell_joins, verifier.cell_joins)
        compared.append(
            _Compared(
                field="repeated_header_rows",
                kept=kept.repeated_header_rows,
                label="the number of repeated header rows",
                verifier=verifier.repeated_header_rows,
            )
        )
    return [
        _difference(
            value,
            f"in {name}, {value.label} is {_value(value.kept)} in the kept verdict "
            f"and {_value(value.verifier)} in the verifier's",
            page_index=page_index,
            where=kept,
        )
        for value in compared
        if value.kept != value.verifier
    ]


def _pair_pieces(
    kept: Sequence[ContinuingPiece], verifier: Sequence[ContinuingPiece]
) -> dict[int, int]:
    """Pair the pieces of two verdicts that are about the same content.

    Each kept piece is paired with the first unpaired verifier piece with the same
    end, the earlier item and entry. Then each kept piece still unpaired is paired
    with the first unpaired verifier piece with the same start, the later item and
    entry.

    Parameters
    ----------
    kept
        The kept verdict's pieces.
    verifier
        The verifier's pieces.

    Returns
    -------
    dict[int, int]
        The position of each paired verifier piece by the position of its kept
        piece, both from 0, in the kept verdict's order.
    """

    pairs: dict[int, int] = {}
    for same in (
        attrgetter("earlier_item", "earlier_entry"),
        attrgetter("later_item", "later_entry"),
    ):
        for position, piece in enumerate(kept):
            if position in pairs:
                continue
            match = next(
                (
                    other_position
                    for other_position, other in enumerate(verifier)
                    if other_position not in pairs.values()
                    and same(other) == same(piece)
                ),
                None,
            )
            if match is not None:
                pairs[position] = match
    return dict(sorted(pairs.items()))


def _piece_difference(
    piece: ContinuingPiece, *, kept: bool, page_index: int, position: int
) -> CheckFailure:
    """Describe a piece that only one of two verdicts gives.

    Parameters
    ----------
    piece
        The piece.
    kept
        Whether the piece is the kept verdict's, rather than the verifier's.
    page_index
        The page before the break.
    position
        The piece's position in its verdict, from 1.

    Returns
    -------
    CheckFailure
        The difference, with the piece's ends as its verdict's value and ``None`` as
        the other's.
    """

    ends = (
        f"{_point(piece.earlier_item, piece.earlier_entry)} to "
        f"{_point(piece.later_item, piece.later_entry)}"
    )
    owner, other = ("kept verdict", "verifier's") if kept else ("verifier", "kept")
    return _difference(
        _Compared(
            field="piece",
            kept=ends if kept else None,
            label="the piece",
            verifier=None if kept else ends,
        ),
        f"the {owner}'s {_piece_name(position, piece)}, joined with {piece.join}, "
        f"matches no piece of the {other} verdict",
        page_index=page_index,
        where=piece,
    )


def _piece_name(position: int, piece: ContinuingPiece) -> str:
    """Name a piece for a message by its position and the items it joins.

    Parameters
    ----------
    position
        The piece's position in its verdict, from 1.
    piece
        The piece.

    Returns
    -------
    str
        Such as ``piece 2 (p0003-007 to p0004-001)``.
    """

    return f"piece {position} ({piece.earlier_item} to {piece.later_item})"


def _pieces(
    verdict: BreakVerdict, *, earlier: PageFile, later: PageFile
) -> list[_Piece]:
    """Pair each of a verdict's pieces with the items it joins.

    Parameters
    ----------
    verdict
        The verdict.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.

    Returns
    -------
    list[_Piece]
        The pieces in the verdict's order, numbered from 1 in their names.
    """

    earlier_items = _items(earlier)
    later_items = _items(later)
    return [
        _Piece(
            earlier=earlier,
            earlier_items=earlier_items,
            end=earlier_items.get(piece.earlier_item),
            later=later,
            later_items=later_items,
            name=_piece_name(position, piece),
            piece=piece,
            start=later_items.get(piece.later_item),
        )
        for position, piece in enumerate(verdict.pieces, start=1)
    ]


def _point(item: str, entry: str | None) -> str:
    """Name where a piece ends or starts, for a difference between two verdicts.

    Parameters
    ----------
    item
        The item's ID.
    entry
        The list entry's ID, or ``None`` when the piece names no entry.

    Returns
    -------
    str
        The entry's ID when the piece names one, else the item's. An entry's ID
        starts with its item's.

    Examples
    --------
    >>> _point("p0004-002", "p0004-002.3")
    'p0004-002.3'
    >>> _point("p0004-002", None)
    'p0004-002'
    """

    return item if entry is None else entry


def _printed_forms(page: PageFile) -> list[str]:
    """List the texts printed on a page that a repeated item can repeat.

    Parameters
    ----------
    page
        The page file.

    Returns
    -------
    list[str]
        In comparison form, leaving out empty ones, each item's text, each list
        entry's text and each table row's cell texts joined in order.
    """

    forms = (
        comparison_form(part) for item in page.items for part in _printed_parts(item)
    )
    return [form for form in forms if form]


def _printed_parts(item: Item) -> list[str]:
    """List the texts an item prints.

    Parameters
    ----------
    item
        The item.

    Returns
    -------
    list[str]
        Its text, each list entry's text and each table row's cell texts joined in
        order, leaving out empty ones.
    """

    parts = [item.text or ""]
    parts += [entry.text for entry in item.entries or []]
    parts += [_row_text(row) for row in _table_rows(item) or []]
    return [part for part in parts if part]


def _printed_text(item: Item) -> str:
    """Join the texts an item prints.

    Parameters
    ----------
    item
        The item.

    Returns
    -------
    str
        The parts from `_printed_parts`, joined with spaces.
    """

    return " ".join(_printed_parts(item))


def _repeat_cell_problems(piece: _Piece) -> list[CheckFailure]:
    """Check that each ``repeat`` cell of a merged row repeats a cell above it.

    Parameters
    ----------
    piece
        The piece.

    Returns
    -------
    list[CheckFailure]
        A ``repeats`` failure for each cell of the merged row whose cell join is
        ``repeat`` and that has no text, or whose text matches the text of no cell
        in the split row on the earlier page, the earlier table's last row. A cell
        join with no cell in the merged row, and missing tables or rows, are left to
        the ``joins`` check.
    """

    cell_joins = piece.piece.cell_joins
    count = piece.piece.repeated_header_rows
    earlier_rows, later_rows = _table_rows(piece.end), _table_rows(piece.start)
    if (
        piece.piece.join != "merge_split_row"
        or cell_joins is None
        or count is None
        or not earlier_rows
        or not later_rows
        or not 0 <= count < len(later_rows)
    ):
        return []

    # Any cell of the split row counts, so cells that span differently on the two
    # pages still match.
    split_row = [
        form for cell in earlier_rows[-1] if (form := comparison_form(cell.text or ""))
    ]
    item = piece.piece.later_item
    failures = []
    for position, (cell_join, cell) in enumerate(
        zip(cell_joins, later_rows[count], strict=False)
    ):
        form = comparison_form(cell.text or "")
        if cell_join != "repeat" or (
            form and any(_repeat_matches(form, text) for text in split_row)
        ):
            continue
        problem = (
            f"its text matches no cell of the split row, the last row of "
            f"{piece.piece.earlier_item}"
            if form
            else "that cell has no text"
        )
        failures.append(
            _failure(
                "repeats",
                f"{piece.name} gives cell {position} of row {count} of {item} the cell "
                f"join repeat, but {problem}",
                details={"cell": position, "item": item, "row": count},
                page=piece.later,
            )
        )
    return failures


def _repeat_matches(form: str, printed: str) -> bool:
    """Decide whether a repeated item's text matches a text on the earlier page.

    Parameters
    ----------
    form
        The repeated item's text, in comparison form and not empty.
    printed
        A text on the earlier page, in comparison form and not empty.

    Returns
    -------
    bool
        Whether the two match by `_forms_match`, or either contains the other.

    Examples
    --------
    >>> _repeat_matches("chapter3continued", "chapter3")
    True
    """

    return _forms_match(form, printed) or form in printed or printed in form


def _repeat_note(text_join: TextJoin | None) -> str:
    """Say where ``repeat`` belongs, for a message about a piece's text join.

    Parameters
    ----------
    text_join
        The piece's text join.

    Returns
    -------
    str
        A sentence to end the message with when the text join is ``repeat``, and an
        empty string otherwise.
    """

    if text_join != "repeat":
        return ""
    return ". repeat is only for the cell_joins of merge_split_row"


def _repeat_problems(piece: _Piece, *, printed: Sequence[str]) -> list[CheckFailure]:
    """Check that each of a piece's repeated items repeats text on the earlier page.

    Parameters
    ----------
    piece
        The piece.
    printed
        The texts printed on the earlier page, from `_printed_forms`.

    Returns
    -------
    list[CheckFailure]
        A ``repeats`` failure for each repeated item with text that matches none of
        them. Items that are not on the later page or have no text are left out.
    """

    failures = []
    for item_id in piece.piece.repeated_items:
        item = piece.later_items.get(item_id)
        form = comparison_form(item.text or "") if item is not None else ""
        if form and not any(_repeat_matches(form, text) for text in printed):
            failures.append(
                _failure(
                    "repeats",
                    f"{piece.name} names {item_id} as a repeated item, but its text "
                    "matches no text printed on the earlier page",
                    details={"item": item_id},
                    page=piece.later,
                )
            )
    return failures


def _repeated_id_problems(piece: _Piece) -> list[CheckFailure]:
    """Check that a piece's repeated items are on the later page.

    Parameters
    ----------
    piece
        The piece.

    Returns
    -------
    list[CheckFailure]
        An ``ids`` failure for each repeated item the later page does not have.
    """

    return [
        _failure(
            "ids",
            f"{piece.name} names {item_id} as a repeated item, but it is not an item "
            "on the later page",
            details={"item": item_id},
            page=piece.later,
        )
        for item_id in piece.piece.repeated_items
        if item_id not in piece.later_items
    ]


def _repeated_start_problems(
    verdict: BreakVerdict, *, later: PageFile
) -> list[CheckFailure]:
    """Check that no repeated item is also where a piece starts.

    Parameters
    ----------
    verdict
        The verdict.
    later
        The page file of the page after the break.

    Returns
    -------
    list[CheckFailure]
        A ``duplicates`` failure for each such item, once each.
    """

    starts = {piece.later_item for piece in verdict.pieces}
    repeated = dict.fromkeys(
        item_id for piece in verdict.pieces for item_id in piece.repeated_items
    )
    return [
        _failure(
            "duplicates",
            f"{item_id} is both a repeated item and where a piece starts",
            details={"item": item_id},
            page=later,
        )
        for item_id in repeated
        if item_id in starts
    ]


def _row_text(cells: Sequence[TableCell]) -> str:
    """Join a table row's cell texts in order.

    Parameters
    ----------
    cells
        The row's cells.

    Returns
    -------
    str
        The texts of the cells that have text, joined with spaces.
    """

    return " ".join(cell.text for cell in cells if cell.text)


def _start_has_marker(piece: _Piece) -> bool:
    """Tell whether the verdict names a continuation marker in a piece's start.

    Parameters
    ----------
    piece
        The piece.

    Returns
    -------
    bool
        Whether one of the piece's markers is on its start item and, when that item
        is a table, on the row its start text comes from, the first row after the
        repeated header rows.
    """

    start = piece.start
    if start is None:
        return False
    row = (
        (piece.piece.repeated_header_rows or 0)
        if start.kind == ItemKind.TABLE
        else None
    )
    return any(
        marker.item == start.id and (row is None or marker.row == row)
        for marker in piece.piece.markers
    )


def _start_text(piece: _Piece) -> str | None:
    """Find the text a piece starts with on the later page.

    Parameters
    ----------
    piece
        The piece.

    Returns
    -------
    str | None
        The start entry's text when the piece names one, a list item's first entry
        otherwise, the cell texts of a table's first row after the repeated header
        rows, or the item's text. ``None`` when there is no such text.
    """

    start = piece.start
    if start is None:
        return None
    if piece.piece.later_entry is not None:
        return _entry_text(start, piece.piece.later_entry)
    if start.kind == ItemKind.LIST:
        return next((entry.text for entry in start.entries or []), None)
    if start.kind == ItemKind.TABLE:
        rows = _table_rows(start) or []
        count = piece.piece.repeated_header_rows or 0
        return _row_text(rows[count]) if 0 <= count < len(rows) else None
    return start.text


def _table_rows(item: Item | None) -> list[list[TableCell]] | None:
    """Get an item's table rows.

    Parameters
    ----------
    item
        The item, if any.

    Returns
    -------
    list[list[TableCell]] | None
        The rows, or ``None`` when there is no item or it has no table.
    """

    if item is None or item.table is None:
        return None
    return item.table.rows


def _value(value: object) -> str:
    """Write a verdict's value for a message, with ``null`` for a missing value.

    Parameters
    ----------
    value
        The value.

    Returns
    -------
    str
        The value as text, with a list's values in brackets.

    Examples
    --------
    >>> _value(None)
    'null'
    >>> _value(["space", None, "repeat"])
    '[space, null, repeat]'
    >>> _value(1)
    '1'
    """

    if value is None:
        return "null"
    if isinstance(value, list):
        return "[" + ", ".join(_value(part) for part in value) + "]"
    return str(value)


def check_continues(
    verdict: BreakVerdict, earlier: PageFile, later: PageFile
) -> list[CheckFailure]:
    """Check that ``continues`` is true when the verdict names pieces, and only then.

    Parameters
    ----------
    verdict
        The verdict.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.

    Returns
    -------
    list[CheckFailure]
        A failure when ``continues`` and ``pieces`` disagree.
    """

    count = len(verdict.pieces)
    if verdict.continues and count == 0:
        message = (
            "continues is true, but pieces is empty. Name each piece that continues, "
            "or set continues to false"
        )
    elif not verdict.continues and count > 0:
        message = (
            f"continues is false, but pieces lists {count} "
            f"piece{'' if count == 1 else 's'}. Set continues to true, or leave "
            "pieces empty"
        )
    else:
        return []
    return [_failure("continues", message, details={}, page=None)]


def check_duplicates(
    verdict: BreakVerdict, earlier: PageFile, later: PageFile
) -> list[CheckFailure]:
    """Check that no item, entry or container is named twice where once is allowed.

    Parameters
    ----------
    verdict
        The verdict.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.

    Returns
    -------
    list[CheckFailure]
        A failure for each item or entry on the earlier page that ends more than one
        piece, each on the later page that starts more than one, each container
        named more than once on one page, and each repeated item that is also where
        a piece starts.
    """

    pieces = verdict.pieces
    containers = verdict.containers
    return (
        _duplicates(
            (piece.earlier_item for piece in pieces),
            key="item",
            message=(
                "more than one piece ends in {name}. An item ends at most one piece"
            ),
            page=earlier,
        )
        + _duplicates(
            (piece.earlier_entry for piece in pieces),
            key="entry",
            message="more than one piece ends in the entry {name}",
            page=earlier,
        )
        + _duplicates(
            (piece.later_item for piece in pieces),
            key="item",
            message=(
                "more than one piece starts in {name}. An item starts at most one piece"
            ),
            page=later,
        )
        + _duplicates(
            (piece.later_entry for piece in pieces),
            key="entry",
            message="more than one piece starts in the entry {name}",
            page=later,
        )
        + _duplicates(
            (container.earlier for container in containers),
            key="container",
            message="containers names {name} on the earlier page more than once",
            page=earlier,
        )
        + _duplicates(
            (container.later for container in containers),
            key="container",
            message="containers names {name} on the later page more than once",
            page=later,
        )
        + _repeated_start_problems(verdict, later=later)
    )


def check_furniture(
    verdict: BreakVerdict, earlier: PageFile, later: PageFile
) -> list[CheckFailure]:
    """Check that no piece ends or starts in page furniture.

    Parameters
    ----------
    verdict
        The verdict.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.

    Returns
    -------
    list[CheckFailure]
        A failure for each end in an item with role ``artifact``.
    """

    return [
        _failure(
            "furniture",
            f"{piece.name} {verb} in {item.id}, which is page furniture (role "
            "artifact). Page furniture does not continue across a break",
            details={"item": item.id},
            page=page,
        )
        for piece in _pieces(verdict, earlier=earlier, later=later)
        for item, page, verb in (
            (piece.end, earlier, "ends"),
            (piece.start, later, "starts"),
        )
        if item is not None and item.role == ItemRole.ARTIFACT
    ]


def check_header_rows(
    verdict: BreakVerdict, earlier: PageFile, later: PageFile
) -> list[CheckFailure]:
    """Check that repeated header rows repeat rows of the earlier table.

    For each table piece with ``repeated_header_rows`` n above 0, the later table's
    first n rows must match, in order, n different rows among the earlier table's
    first n + h rows, where h is the earlier table's ``header_rows``. Rows match by
    their cell texts joined in order, and two empty rows match.

    Parameters
    ----------
    verdict
        The verdict.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.

    Returns
    -------
    list[CheckFailure]
        A failure for each table piece whose repeated header rows do not match, or
        whose tables are missing.
    """

    failures = []
    for piece in _pieces(verdict, earlier=earlier, later=later):
        count = piece.piece.repeated_header_rows
        if piece.piece.join in _TABLE_JOINS and count is not None and count > 0:
            failures += _header_row_problems(piece, count=count)
    return failures


def check_ids(
    verdict: BreakVerdict, earlier: PageFile, later: PageFile
) -> list[CheckFailure]:
    """Check that every ID the verdict names exists on the page it is named for.

    Ends and earlier containers are on the earlier page. Starts, later containers,
    repeated items and the items carrying markers are on the later page. Each entry
    belongs to the item named with it, and each marker's row and cell exist in its
    item's table.

    Parameters
    ----------
    verdict
        The verdict.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.

    Returns
    -------
    list[CheckFailure]
        A failure for each item, entry, container, row or cell that does not exist
        where the verdict puts it.
    """

    failures = []
    for piece in _pieces(verdict, earlier=earlier, later=later):
        failures += _end_id_problems(piece)
        failures += _repeated_id_problems(piece)
        failures += _marker_id_problems(piece)
    return failures + _container_id_problems(verdict, earlier=earlier, later=later)


def check_joins(
    verdict: BreakVerdict, earlier: PageFile, later: PageFile
) -> list[CheckFailure]:
    """Check each piece against the rules of its join.

    Each join ends and starts in items of the kinds it joins, sets the fields it
    uses and leaves the others null. ``continue_text`` joins two items of one kind,
    ``continue_entry`` joins the last or first entry of a list, and the table joins
    keep ``repeated_header_rows`` and ``cell_joins`` within the later table.
    ``new_entry`` starts in a list, and ends in a list or in a text item, for a list
    whose part on the earlier page was extracted as text. ``repeat`` joins only the
    cells of a merged row, and ``newline`` only code.

    Parameters
    ----------
    verdict
        The verdict.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.

    Returns
    -------
    list[CheckFailure]
        A failure for each rule a piece breaks.
    """

    failures = []
    for piece in _pieces(verdict, earlier=earlier, later=later):
        failures += _join_field_problems(piece)
        failures += _join_kind_problems(piece)
        rule = _JOIN_RULES.get(piece.piece.join)
        if rule is not None:
            failures += rule(piece)
    return failures


def check_markers(
    verdict: BreakVerdict, earlier: PageFile, later: PageFile
) -> list[CheckFailure]:
    """Check that each continuation marker is in the text that carries it.

    Parameters
    ----------
    verdict
        The verdict.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.

    Returns
    -------
    list[CheckFailure]
        A failure for each marker whose comparison form is not in the comparison
        form of its cell, row or item. Markers whose item, row or cell is missing
        are left to the ``ids`` check.
    """

    failures = []
    for piece in _pieces(verdict, earlier=earlier, later=later):
        for marker in piece.piece.markers:
            carrier = _marker_carrier(marker, piece.later_items.get(marker.item))
            if carrier is None:
                continue
            if comparison_form(marker.text) not in comparison_form(carrier):
                place = _marker_place(marker)
                failures.append(
                    _failure(
                        "markers",
                        f"{piece.name} has the marker {marker.text!r} on {place}, "
                        f"but the text of {place} does not contain it",
                        details=_marker_details(marker),
                        page=later,
                    )
                )
    return failures


def check_repeats(
    verdict: BreakVerdict, earlier: PageFile, later: PageFile
) -> list[CheckFailure]:
    """Check that repeated items and ``repeat`` cells repeat text on the earlier page.

    A repeated item with text matches when its text matches an item's text, a list
    entry's text, or a table row's cell texts joined in order, or when either
    contains the other in comparison form. A cell of a merged row whose cell join is
    ``repeat`` must have text, and that text must match the text of a cell in the
    split row on the earlier page, the earlier table's last row, in the same way.
    Any cell of that row counts, so cells that span differently on the two pages
    still match.

    Parameters
    ----------
    verdict
        The verdict.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.

    Returns
    -------
    list[CheckFailure]
        A failure for each repeated item whose text matches no text on the earlier
        page, and for each ``repeat`` cell with no text or no matching cell.
    """

    printed = _printed_forms(earlier)
    failures = []
    for piece in _pieces(verdict, earlier=earlier, later=later):
        failures += _repeat_problems(piece, printed=printed)
        failures += _repeat_cell_problems(piece)
    return failures


# The checks, in the order they run.
CHECKS: dict[BreakCheckName, Check] = {
    "ids": check_ids,
    "continues": check_continues,
    "duplicates": check_duplicates,
    "joins": check_joins,
    "furniture": check_furniture,
    "header_rows": check_header_rows,
    "repeats": check_repeats,
    "markers": check_markers,
}


def check_results(
    failures: Mapping[BreakCheckName, list[CheckFailure]], *, attempts: int
) -> list[BreakCheckResult]:
    """Record each check's result on the kept verdict, in the order the checks run.

    Parameters
    ----------
    failures
        Each check's failures on the kept verdict, from `run_checks`.
    attempts
        How many verdicts were checked from the model that gave it.

    Returns
    -------
    list[BreakCheckResult]
        The results for the verdict file's ``checks``.
    """

    return [
        BreakCheckResult(
            attempts=attempts,
            failures=failures[name],
            name=name,
            passed=not failures[name],
        )
        for name in failures
    ]


def check_start_markers(
    verdict: BreakVerdict, earlier: PageFile, later: PageFile, context: BreakContext
) -> list[CheckFailure]:
    """Compare where pieces start with the survey's start markers.

    A piece starts with the start entry's text, a list's first entry, the cell texts
    of a table's first row after the repeated header rows, or the start item's text.
    A start marker whose comparison form is empty is skipped. Two kinds of piece are
    skipped too: an ``append_rows`` piece, whose new rows can begin with a start
    marker while the table carries on, and a piece whose verdict names a
    continuation marker in its start, on its start item and, for a table, on the
    row its start text comes from.

    Parameters
    ----------
    verdict
        The verdict.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.
    context
        The break's context, with the survey's start markers.

    Returns
    -------
    list[CheckFailure]
        A difference for each piece that is not skipped and whose start begins with
        a start marker in comparison form, naming the first such marker.
    """

    markers = [
        (marker, form)
        for marker in context.start_markers
        if (form := comparison_form(marker.text))
    ]
    differences = []
    for piece in _pieces(verdict, earlier=earlier, later=later):
        if piece.piece.join == "append_rows" or _start_has_marker(piece):
            continue
        start = comparison_form(_start_text(piece) or "")
        found = next(
            (marker for marker, form in markers if start.startswith(form)), None
        )
        if found is not None:
            differences.append(
                _failure(
                    "start_markers",
                    f"{piece.name} starts with {found.text!r}, which the survey found "
                    "marks where a new unit of content starts, and the verdict joins "
                    "it to the earlier page",
                    details={
                        "entry": piece.piece.later_entry,
                        "item": piece.piece.later_item,
                        "marker": found.text,
                    },
                    page=later,
                )
            )
    return differences


# The hints, in the order they run.
HINTS: dict[BreakHintName, Hint] = {"start_markers": check_start_markers}


def compare_verdicts(
    kept: BreakVerdict, verifier: BreakVerdict, *, page_index: int
) -> list[CheckFailure]:
    """Compare the kept verdict for a break with the verifier's.

    When only one verdict says content continues, that is the one difference, and
    when neither does, nothing else is compared. Otherwise the pieces are paired by
    their end, then by their start. Each piece left unpaired is a difference, the
    kept verdict's first, and each pair is compared field by field in the kept
    verdict's order. Repeated items, markers, containers and the reason are not
    compared.

    Parameters
    ----------
    kept
        The kept verdict.
    verifier
        The verifier's verdict.
    page_index
        The page before the break, where every difference is recorded.

    Returns
    -------
    list[CheckFailure]
        One ``verdicts_differ`` difference per way the verdicts differ, empty when
        they match. Each names the field, both values and the piece's end on the
        earlier page in its ``details``.
    """

    if kept.continues != verifier.continues:
        return [_continues_difference(kept, verifier, page_index=page_index)]
    if not kept.continues:
        return []

    pairs = _pair_pieces(kept.pieces, verifier.pieces)
    paired = set(pairs.values())
    differences = [
        _piece_difference(piece, kept=True, page_index=page_index, position=index + 1)
        for index, piece in enumerate(kept.pieces)
        if index not in pairs
    ]
    differences += [
        _piece_difference(piece, kept=False, page_index=page_index, position=index + 1)
        for index, piece in enumerate(verifier.pieces)
        if index not in paired
    ]
    for index, other in pairs.items():
        piece = kept.pieces[index]
        differences += _pair_differences(
            piece,
            verifier.pieces[other],
            name=_piece_name(index + 1, piece),
            page_index=page_index,
        )
    return differences


def compare_with_hints(
    verdict: BreakVerdict, earlier: PageFile, later: PageFile, context: BreakContext
) -> dict[BreakHintName, list[CheckFailure]]:
    """Compare a verdict with every hint, in order.

    Parameters
    ----------
    verdict
        The verdict.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.
    context
        The break's context.

    Returns
    -------
    dict[BreakHintName, list[CheckFailure]]
        Each hint's differences, in the order the hints run, with an empty list for
        a hint the verdict agrees with.
    """

    return {
        name: hint(verdict, earlier, later, context) for name, hint in HINTS.items()
    }


def hint_results(
    differences: Mapping[BreakHintName, list[CheckFailure]],
) -> list[BreakHintResult]:
    """Record each hint's differences on the kept verdict, in the order the hints run.

    Parameters
    ----------
    differences
        Each hint's differences on the kept verdict, from `compare_with_hints`.

    Returns
    -------
    list[BreakHintResult]
        The results for the verdict file's ``hints``.
    """

    return [
        BreakHintResult(differences=found, name=name)
        for name, found in differences.items()
    ]


def retry_message(failures: Mapping[BreakCheckName, list[CheckFailure]]) -> str:
    """Write the message that asks the model to fix its verdict.

    Parameters
    ----------
    failures
        Each check's failures, from `run_checks`.

    Returns
    -------
    str
        Every check failure, one per line, after a line asking for a corrected
        verdict. Hint differences are never part of it.
    """

    lines = [f"- {failure.message}" for found in failures.values() for failure in found]
    return (
        "Your verdict has problems that can be checked without reading the pages. "
        "Fix each problem below and answer again with the whole verdict:\n"
        + "\n".join(lines)
    )


def review_issues(
    *,
    checks: Sequence[BreakCheckResult],
    earlier: PageFile,
    hints: Sequence[BreakHintResult],
    later: PageFile,
    verification: BreakVerification | None,
) -> list[ReviewIssue]:
    """Collect a break's review issues.

    Parameters
    ----------
    checks
        The check results on the kept verdict, from `check_results`.
    earlier
        The page file of the page before the break.
    hints
        The hint results on the kept verdict, from `hint_results`.
    later
        The page file of the page after the break.
    verification
        The verifier's second judgment, or ``None`` when no verifier ran.

    Returns
    -------
    list[ReviewIssue]
        The checks still failing on the kept verdict, then its hint differences,
        then each way the verifier's verdict differs from it. Hint differences are
        left out when the verifier's verdict matches the kept verdict, since two
        judgments of the page images agree. The checks the verifier's verdict fails
        are not listed. Each issue is on the page before the break and names both
        pages in its message.
    """

    ids = _page_ids(earlier) | _page_ids(later)
    found: list[
        tuple[BreakCheckName | BreakComparisonName | BreakHintName, CheckFailure]
    ] = [(result.name, failure) for result in checks for failure in result.failures]
    if verification is None or verification.differences:
        found += [
            (result.name, difference)
            for result in hints
            for difference in result.differences
        ]
    if verification is not None:
        found += [
            ("verdicts_differ", difference) for difference in verification.differences
        ]
    return [
        _issue(failure, ids=ids, name=name, page_index=earlier.page_index)
        for name, failure in found
    ]


def run_checks(
    verdict: BreakVerdict, earlier: PageFile, later: PageFile
) -> dict[BreakCheckName, list[CheckFailure]]:
    """Run every check on a verdict, in order.

    Parameters
    ----------
    verdict
        The verdict.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.

    Returns
    -------
    dict[BreakCheckName, list[CheckFailure]]
        Each check's failures, in the order the checks run, with an empty list for
        a check that passed.
    """

    return {name: check(verdict, earlier, later) for name, check in CHECKS.items()}

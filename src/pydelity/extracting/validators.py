"""Page extraction's checks on a model's answer for one page.

Pydantic checks only the answer's shape. These checks test what code can decide from
the answer and the page's context alone: labels fit the profile, each item holds the
content its kind needs, boxes lie on the page, containers and captions point at real
items, the reading order fits the page's writing direction, page furniture the survey
found is kept, and fillable form fields carry their values. They use positions,
names, Unicode forms and values only, never word lists, and assume no writing
direction other than the page's own.

On a page with a readable text layer, two more checks compare the items' text with
it, as runs of three characters, to find text the answer dropped or added in any
script. The model's reading wins over the text layer: a difference only sends the
answer back, saying the model may keep text that is not visible on the page or that
it read from an image.

Each check returns every failure it finds, so one retry message can name every
problem and the kept answer can record them all. A failure about one item names the
item's ref in its message and in ``details["item_ref"]``.
"""

# Standard Library
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from itertools import pairwise

# Package Library
from pydelity.config.schemas import is_language_tag
from pydelity.extracting.schemas import (
    AnswerContainer,
    AnswerItem,
    ColumnOrder,
    ExtractionCheckResult,
    PageAnswer,
    PageContext,
    Table,
    TextComparison,
)
from pydelity.extracting.text_layer import comparison_form, trigrams
from pydelity.review import CheckFailure, ExtractionCheckName, ReviewIssue
from pydelity.surveying.schemas import Direction, FormField, ItemKind, ItemRole, Label
from pydelity.utils.text import normalize_line

# How far outside the 0-1000 grid a box may reach, in grid units, before it counts as
# off the page.
_BOX_TOLERANCE = 5

# How far, in grid units, an item must move across (or down, on a page written top to
# bottom) for a jump back against the reading flow to count as a new column or band.
_COLUMN_MOVE = 200

# How far, in grid units, an item or container may reach outside its container's box.
_CONTAINER_TOLERANCE = 20

# The content fields an item may fill; its kind decides which (see `_KIND_FIELDS`).
_CONTENT_FIELDS = ("entries", "field", "figure", "latex", "table", "text")

# The roles whose items make up the page's reading flow, which the reading-order check
# follows. Asides, captions, footnotes and page furniture may sit anywhere.
_FLOW_ROLES = frozenset({ItemRole.BODY, ItemRole.HEADING, ItemRole.NAVIGATION})

# The share of a line's three-character runs that must be found for the line to count
# as present; a line with fewer found fails a text check.
_FOUND_SHARE = 0.5

# How far, in grid units, the next item in the flow may jump back against the reading
# direction without starting a new column or band.
_JUMP_BACK = 150

# The content fields each kind of item fills; every other content field is null.
_KIND_FIELDS: dict[ItemKind, frozenset[str]] = {
    ItemKind.CODE: frozenset({"text"}),
    ItemKind.FIELD: frozenset({"field"}),
    ItemKind.FIGURE: frozenset({"figure"}),
    ItemKind.FORMULA: frozenset({"latex", "text"}),
    ItemKind.LIST: frozenset({"entries"}),
    ItemKind.TABLE: frozenset({"table"}),
    ItemKind.TEXT: frozenset({"text"}),
}

# How much of a line a text failure quotes, in characters.
_LINE_SHOWN_CHARS = 100

# The field item types that are marked or not, so they need ``checked``.
_MARKED_FIELD_TYPES = frozenset({"checkbox", "radio"})

# The fewest three-character runs a line must have for a text check to judge it: a
# line of five letters or digits has three.
_MIN_TRIGRAMS = 3

# The profile's catch-all label, which every profile has.
_OTHER_LABEL = "other"

# What the model may keep when a text check sends its answer back.
_TEXT_NOTE = (
    "The page's text layer can hold text that is not visible on the page and lacks "
    "text inside images. Where a line above is not visible on the page, or you read "
    "it from an image, keep your reading."
)

# Checks an answer against the page's context and returns every failure found.
type Check = Callable[[PageAnswer, PageContext], list[CheckFailure]]

# Checks an answer against the page's context and its text-layer lines.
type TextCheck = Callable[[PageAnswer, PageContext, Sequence[str]], list[CheckFailure]]


def _answer_lines(answer: PageAnswer) -> list[tuple[str, str]]:
    """List the answer's lines of text that the text layer should hold.

    Each item's text, list entries, table cells and field prompts are split at line
    breaks. Figure text, field values and formula text are left out, since they can
    come from images or form data rather than the text layer.

    Parameters
    ----------
    answer
        The model's answer.

    Returns
    -------
    list[tuple[str, str]]
        Each line with its item's ref, in reading order.
    """

    lines = []
    for item in answer.items:
        pieces = [item.text] if item.kind != ItemKind.FORMULA else []
        pieces += [entry.text for entry in item.entries or []]
        if item.table is not None:
            pieces += [cell.text for row in item.table.rows for cell in row]
        if item.field is not None:
            pieces.append(item.field.prompt)
        lines += [
            (item.ref, line) for piece in pieces if piece for line in piece.splitlines()
        ]
    return lines


def _answer_trigrams(answer: PageAnswer) -> Counter[str]:
    """Count the three-character runs of all of the answer's text.

    Parameters
    ----------
    answer
        The model's answer.

    Returns
    -------
    Counter[str]
        The runs of every item's text, entries, cells, field prompts and values,
        figure text and formula text, each piece compared on its own.
    """

    total: Counter[str] = Counter()
    for item in answer.items:
        for piece in _item_text(item).split("\n"):
            total += trigrams(comparison_form(piece))
    return total


def _backward_jump(
    previous: AnswerItem,
    item: AnswerItem,
    *,
    column_order: ColumnOrder | None,
    direction: Direction,
) -> str | None:
    """Tell whether the next item jumps back against the flow without a new column.

    Parameters
    ----------
    previous
        The item before, in the reading flow.
    item
        The next item in the flow.
    column_order
        The order the page's columns of vertical text are read in, for ``ttb``.
    direction
        The page's writing direction.

    Returns
    -------
    str | None
        What is wrong, or ``None`` when the step from one item to the next fits.
    """

    (px0, py0, px1, _), (x0, y0, x1, _) = previous.box, item.box
    if direction in {"ltr", "rtl"}:
        up = py0 - y0
        # A new column starts to the right of the last one on ltr pages, to its left
        # on rtl pages; right-to-left columns line up on their right edges.
        across = x0 - px0 if direction == "ltr" else px1 - x1
        side = "right" if direction == "ltr" else "left"
        if up > _JUMP_BACK and across < _COLUMN_MOVE:
            return (
                f"it starts {up} units above item {previous.ref!r}, which comes before "
                f"it, without moving {_COLUMN_MOVE} units to the {side} to a new column"
            )
        return None

    if column_order is None:
        return None
    # Vertical columns run right to left or left to right; a new band starts lower.
    against = x1 - px1 if column_order == "right_to_left" else px0 - x0
    side = "right" if column_order == "right_to_left" else "left"
    down = y0 - py0
    if against > _JUMP_BACK and down < _COLUMN_MOVE:
        return (
            f"it lies {against} units to the {side} of item {previous.ref!r}, which "
            f"comes before it, without moving {_COLUMN_MOVE} units down to a new band"
        )
    return None


def _box_problem(box: Sequence[int]) -> str | None:
    """Tell what is wrong with a box on the 0-1000 grid, if anything.

    Parameters
    ----------
    box
        The box as answered.

    Returns
    -------
    str | None
        What is wrong, or ``None`` for four values with ``x0 < x1`` and ``y0 < y1``
        inside the grid, within `_BOX_TOLERANCE`.
    """

    if len(box) != 4:  # noqa: PLR2004 - a box has four values
        return f"has {len(box)} values instead of 4"
    x0, y0, x1, y1 = box
    if not (x0 < x1 and y0 < y1):
        return "needs x0 < x1 and y0 < y1"
    low, high = -_BOX_TOLERANCE, 1000 + _BOX_TOLERANCE
    if any(not low <= value <= high for value in box):
        return "reaches outside the page; values run from 0 to 1000"
    return None


def _collapse(text: str | None) -> str:
    """Collapse whitespace, so values that differ only in spacing compare equal.

    Parameters
    ----------
    text
        The text, or ``None``.

    Returns
    -------
    str
        The words joined by single spaces; empty for ``None``.
    """

    return " ".join((text or "").split())


def _container_cycles(containers: Sequence[AnswerContainer]) -> list[str]:
    """Find the containers that sit, directly or not, inside themselves.

    Parameters
    ----------
    containers
        The answer's containers.

    Returns
    -------
    list[str]
        The refs of the containers on a cycle, in answer order.
    """

    parents = {container.ref: container.container for container in containers}
    looped = []
    for container in containers:
        seen = {container.ref}
        parent = container.container
        while parent is not None and parent in parents and parent not in seen:
            seen.add(parent)
            parent = parents[parent]
        if parent == container.ref:
            looped.append(container.ref)
    return looped


def _failure(
    check: ExtractionCheckName,
    message: str,
    *,
    context: PageContext,
    item_ref: str | None = None,
) -> CheckFailure:
    """Make a failure whose message starts with the check's name.

    Parameters
    ----------
    check
        The check that failed.
    message
        What is wrong.
    context
        The page's context, for its index.
    item_ref
        The ref of the item or container the problem is about, if one.

    Returns
    -------
    CheckFailure
        The failure, with the ref in ``details["item_ref"]``.
    """

    return CheckFailure(
        details={"item_ref": item_ref},
        message=f"{check}: {message}",
        page_index=context.page_index,
    )


def _field_mismatch(
    name: str, fields: Sequence[FormField], items: Sequence[AnswerItem]
) -> str | None:
    """Compare a form field's widgets on the page with the field items naming it.

    Parameters
    ----------
    name
        The form field's name.
    fields
        Its widgets on the page, such as each button of a radio group.
    items
        The field items whose ``fillable_name`` is the field's name.

    Returns
    -------
    str | None
        What differs, or ``None`` when there are as many items as widgets with the
        same checked states, or the same values with whitespace collapsed.
    """

    if len(items) != len(fields):
        return (
            f"the form field {name!r} is on the page {len(fields)} time(s), but "
            f"{len(items)} field item(s) name it in fillable_name"
        )
    answered = [item.field for item in items if item.field is not None]
    if fields[0].type in {"checkbox", "radio"}:
        expected = sorted(bool(field.checked) for field in fields)
        got = sorted(bool(field.checked) for field in answered)
        what = "is checked"
    else:
        expected = sorted(_collapse(field.value) for field in fields)
        got = sorted(_collapse(field.value) for field in answered)
        what = "holds"
    if expected == got:
        return None
    return f"the form field {name!r} {what} {expected}, but its field items say {got}"


def _has_text(item: AnswerItem) -> bool:
    """Tell whether an item holds any text, and so needs a language.

    Parameters
    ----------
    item
        The item.

    Returns
    -------
    bool
        Whether any of its text, entries, cells, figure text or field text is not
        blank.
    """

    return bool(_item_text(item).strip())


def _inside(inner: Sequence[int], outer: Sequence[int]) -> bool:
    """Tell whether a box lies inside another, within `_CONTAINER_TOLERANCE`.

    Parameters
    ----------
    inner
        The box that should be inside.
    outer
        The container's box.

    Returns
    -------
    bool
        Whether every edge of ``inner`` is inside ``outer`` or past it by at most the
        tolerance.
    """

    reach = _CONTAINER_TOLERANCE
    return (
        inner[0] >= outer[0] - reach
        and inner[1] >= outer[1] - reach
        and inner[2] <= outer[2] + reach
        and inner[3] <= outer[3] + reach
    )


def _item_content_problems(item: AnswerItem) -> list[str]:
    """List what is wrong with an item's content for its kind.

    Parameters
    ----------
    item
        The item.

    Returns
    -------
    list[str]
        What is wrong, such as a field its kind does not use being set.
    """

    used = _KIND_FIELDS[item.kind]
    problems = [
        f"sets {name}, which a {item.kind} item does not use"
        for name in _CONTENT_FIELDS
        if name not in used and getattr(item, name) is not None
    ]
    problems += [
        f"has no {name}, which a {item.kind} item needs"
        for name in sorted(used)
        if getattr(item, name) is None
    ]
    if "text" in used and item.text is not None and not item.text.strip():
        problems.append("has blank text")
    if item.latex is not None and not item.latex.strip():
        problems.append("has blank latex")
    if item.entries is not None:
        if not item.entries:
            problems.append("is a list with no entries")
        if any(not entry.text.strip() or entry.level < 0 for entry in item.entries):
            problems.append("has a list entry with blank text or a level below 0")
    if item.table is not None:
        problems += [
            f"has a table that {problem}" for problem in _table_problems(item.table)
        ]
    if item.figure is not None and not item.figure.description.strip():
        problems.append("is a figure with a blank description")
    if (
        item.field is not None
        and item.field.field_type in _MARKED_FIELD_TYPES
        and item.field.checked is None
    ):
        problems.append(f"is a {item.field.field_type} field without checked")
    return problems


def _item_text(item: AnswerItem) -> str:
    """Join all of an item's text: text, entries, cells, figure and field text.

    Parameters
    ----------
    item
        The item.

    Returns
    -------
    str
        Each piece of text on its own line.
    """

    parts = [item.text, item.latex]
    parts += [entry.text for entry in item.entries or []]
    if item.table is not None:
        parts += [cell.text for row in item.table.rows for cell in row]
    if item.figure is not None:
        parts.append(item.figure.text)
    if item.field is not None:
        parts += [item.field.prompt, item.field.value]
    return "\n".join(part for part in parts if part)


def _label_fits(item: AnswerItem, label: Label, labels: Sequence[Label]) -> bool:
    """Tell whether a label from the profile fits an item.

    Parameters
    ----------
    item
        The item.
    label
        The item's label, found in the profile.
    labels
        The profile's labels.

    Returns
    -------
    bool
        Whether the label's role is the item's role and its kinds include the item's
        kind, or the label is ``other`` and no other label fits the item.
    """

    if label.role == item.role and item.kind in label.kinds:
        return True
    return label.name.casefold() == _OTHER_LABEL and not _matching_labels(item, labels)


def _layer_trigrams(
    text_lines: Sequence[str], answer_trigrams: Counter[str]
) -> list[Counter[str]]:
    """Count each text-layer line's three-character runs, read the way that matches.

    Some PDFs store right-to-left text in visual order, reversed. A line counts in
    reverse when its reversed text shares more runs with the answer than its stored
    text does.

    Parameters
    ----------
    text_lines
        The page's text-layer lines.
    answer_trigrams
        The runs of the answer's text, from `_answer_trigrams`.

    Returns
    -------
    list[Counter[str]]
        Each line's runs, in the line's order.
    """

    counted = []
    for line in text_lines:
        form = comparison_form(line)
        forward, backward = trigrams(form), trigrams(form[::-1])
        found_forward = sum((forward & answer_trigrams).values())
        found_backward = sum((backward & answer_trigrams).values())
        counted.append(backward if found_backward > found_forward else forward)
    return counted


def _matching_labels(item: AnswerItem, labels: Sequence[Label]) -> list[Label]:
    """List the profile's labels, other than ``other``, that fit an item.

    Parameters
    ----------
    item
        The item.
    labels
        The profile's labels.

    Returns
    -------
    list[Label]
        The labels whose role is the item's role and whose kinds include its kind.
    """

    return [
        label
        for label in labels
        if label.name.casefold() != _OTHER_LABEL
        and label.role == item.role
        and item.kind in label.kinds
    ]


def _place_cells(table: Table) -> tuple[list[int], list[str]]:
    """Lay a table's cells on a grid, as HTML does, and measure each row.

    Each cell takes the first column in its row that no cell above covers with its
    row span, then covers ``row_span`` rows and ``col_span`` columns.

    Parameters
    ----------
    table
        The table.

    Returns
    -------
    tuple[list[int], list[str]]
        How many columns each row covers, and what is wrong: a span below 1, a cell
        that overlaps another, or a row span past the last row.
    """

    rows = len(table.rows)
    covered: set[tuple[int, int]] = set()
    problems: list[str] = []
    for row_index, row in enumerate(table.rows):
        column = 0
        for cell in row:
            if cell.row_span < 1 or cell.col_span < 1:
                problems.append(f"has a span below 1 in row {row_index + 1}")
                continue
            while (row_index, column) in covered:
                column += 1
            if row_index + cell.row_span > rows:
                problems.append(
                    f"has a cell in row {row_index + 1} that spans past the last row"
                )
            spots = {
                (row_index + down, column + across)
                for down in range(cell.row_span)
                for across in range(cell.col_span)
            }
            if spots & covered:
                problems.append(
                    f"has a cell in row {row_index + 1} that overlaps another"
                )
            covered |= spots
            column += cell.col_span
    widths = [
        max((spot[1] + 1 for spot in covered if spot[0] == row_index), default=0)
        for row_index in range(rows)
    ]
    return widths, problems


def _shorten(text: str) -> str:
    """Cut a line to `_LINE_SHOWN_CHARS` characters for a failure message.

    Parameters
    ----------
    text
        The line.

    Returns
    -------
    str
        The line, with spaces collapsed, ending in ``...`` when it was cut.
    """

    line = " ".join(text.split())
    if len(line) <= _LINE_SHOWN_CHARS:
        return line
    return line[: _LINE_SHOWN_CHARS - 3] + "..."


def _table_problems(table: Table) -> list[str]:
    """List what is wrong with a table's grid.

    Parameters
    ----------
    table
        The table.

    Returns
    -------
    list[str]
        What is wrong: no rows, bad spans, rows of different widths, header rows
        out of range, or no text in any cell.
    """

    if not table.rows:
        return ["has no rows"]
    widths, problems = _place_cells(table)
    if len(set(widths)) > 1:
        problems.append(f"has rows covering different numbers of columns, {widths}")
    if not 0 <= table.header_rows <= len(table.rows):
        problems.append(
            f"has header_rows {table.header_rows}, outside 0 to {len(table.rows)}"
        )
    if not any(cell.text and cell.text.strip() for row in table.rows for cell in row):
        problems.append("has no text in any cell")
    return problems


def _unmatched(lines: Sequence[Counter[str]], available: Counter[str]) -> list[int]:
    """Find the lines that fewer than half of their runs are found for.

    The runs the lines hold beyond what is available are missing. They are handed
    out one line at a time, each time to the line that misses the largest share of
    its own runs, so a line that was removed takes its missing runs even when other
    lines share them. Ties go to the later line, so a repeated line counts against
    its last copy.

    Parameters
    ----------
    lines
        Each line's three-character runs.
    available
        The runs the other side holds.

    Returns
    -------
    list[int]
        The positions of the lines with fewer than half of their runs found, in
        order. Lines with fewer than `_MIN_TRIGRAMS` runs are never listed.
    """

    missing = sum(lines, Counter()) - available
    candidates = [
        index for index, line in enumerate(lines) if line.total() >= _MIN_TRIGRAMS
    ]
    flagged = []
    while candidates:
        worst, worst_share = None, 0.0
        for index in candidates:
            share = (lines[index] & missing).total() / lines[index].total()
            if share >= worst_share:
                worst, worst_share = index, share
        if worst is None or worst_share <= 1 - _FOUND_SHARE:
            break
        flagged.append(worst)
        missing -= lines[worst]
        candidates.remove(worst)
    return sorted(flagged)


def check_artifacts(answer: PageAnswer, context: PageContext) -> list[CheckFailure]:
    """Keep the page furniture the survey found: each such line is in an artifact.

    Parameters
    ----------
    answer
        The model's answer.
    context
        The page's context, for its repeated lines and what the survey decided they
        are.

    Returns
    -------
    list[CheckFailure]
        One failure per repeated line the survey classified as page furniture whose
        compared form is in no item with role ``artifact``.
    """

    held = [
        normalize_line(_item_text(item))
        for item in answer.items
        if item.role == ItemRole.ARTIFACT
    ]
    return [
        _failure(
            "artifacts",
            f"the repeated line {line.id}, {line.text!r}, is page furniture on this "
            "page, but no item with role artifact holds it",
            context=context,
        )
        for line in context.repeated_lines
        if line.use == "artifact"
        and line.normalized
        and not any(line.normalized in text for text in held)
    ]


def check_boxes(answer: PageAnswer, context: PageContext) -> list[CheckFailure]:
    """Check that every box is well formed and on the page, and no two items share one.

    Parameters
    ----------
    answer
        The model's answer.
    context
        The page's context, for its index.

    Returns
    -------
    list[CheckFailure]
        One failure per bad box, then one per group of items with the same box.
    """

    failures = []
    for thing, ref, box in [
        *(("item", item.ref, item.box) for item in answer.items),
        *(
            ("container", container.ref, container.box)
            for container in answer.containers
        ),
    ]:
        problem = _box_problem(box)
        if problem is not None:
            failures.append(
                _failure(
                    "boxes",
                    f"{thing} {ref!r} has the box {box}, which {problem}",
                    context=context,
                    item_ref=ref,
                )
            )

    by_box: defaultdict[tuple[int, ...], list[str]] = defaultdict(list)
    for item in answer.items:
        by_box[tuple(item.box)].append(item.ref)
    failures += [
        _failure(
            "boxes",
            f"items {', '.join(repr(ref) for ref in refs)} have the same box "
            f"{list(box)}; give each item its own box",
            context=context,
            item_ref=refs[1],
        )
        for box, refs in by_box.items()
        if len(refs) > 1
    ]
    return failures


def check_captions(answer: PageAnswer, context: PageContext) -> list[CheckFailure]:
    """Check that each caption names the item it captions, and only captions do.

    Parameters
    ----------
    answer
        The model's answer.
    context
        The page's context, for its index.

    Returns
    -------
    list[CheckFailure]
        One failure per caption without a captioned item on the page, and per other
        item that sets ``caption_of``.
    """

    roles = {item.ref: item.role for item in answer.items}
    failures = []
    for item in answer.items:
        target = item.caption_of
        if item.role != ItemRole.CAPTION:
            if target is not None:
                failures.append(
                    _failure(
                        "captions",
                        f"item {item.ref!r} sets caption_of but its role is "
                        f"{item.role}; only captions set it",
                        context=context,
                        item_ref=item.ref,
                    )
                )
            continue
        if (
            target is None
            or target == item.ref
            or roles.get(target) in {None, ItemRole.CAPTION}
        ):
            failures.append(
                _failure(
                    "captions",
                    f"caption {item.ref!r} has caption_of {target!r}; it needs the ref "
                    "of the item on this page it captions, which is not a caption",
                    context=context,
                    item_ref=item.ref,
                )
            )
    return failures


def check_containers(answer: PageAnswer, context: PageContext) -> list[CheckFailure]:
    """Check that containers exist, do not nest in a loop, and hold what names them.

    Parameters
    ----------
    answer
        The model's answer.
    context
        The page's context, for its index.

    Returns
    -------
    list[CheckFailure]
        One failure per unknown container ref, per container on a nesting loop, and
        per item or container that lies outside its container's box.
    """

    boxes = {container.ref: container.box for container in answer.containers}
    members = [
        *(("item", item.ref, item.box, item.container) for item in answer.items),
        *(
            ("container", container.ref, container.box, container.container)
            for container in answer.containers
        ),
    ]
    failures = []
    for thing, ref, box, parent in members:
        if parent is None:
            continue
        if parent not in boxes:
            message = (
                f"{thing} {ref!r} names the container {parent!r}, which does not exist"
            )
        elif (
            _box_problem(box) is None
            and _box_problem(boxes[parent]) is None
            and not _inside(box, boxes[parent])
        ):
            message = f"{thing} {ref!r} lies outside its container {parent!r}"
        else:
            continue
        failures.append(_failure("containers", message, context=context, item_ref=ref))
    failures += [
        _failure(
            "containers",
            f"container {ref!r} sits inside itself through its containers",
            context=context,
            item_ref=ref,
        )
        for ref in _container_cycles(answer.containers)
    ]
    return failures


def check_content(answer: PageAnswer, context: PageContext) -> list[CheckFailure]:
    """Check that refs are unique and each item holds the content its kind needs.

    Parameters
    ----------
    answer
        The model's answer.
    context
        The page's context, for its index.

    Returns
    -------
    list[CheckFailure]
        One failure per ref used more than once, then one per problem with an
        item's content.
    """

    counts = Counter(
        [item.ref for item in answer.items]
        + [container.ref for container in answer.containers]
    )
    failures = [
        _failure(
            "content",
            f"the ref {ref!r} is used {count} times; give each item and container "
            "its own ref",
            context=context,
            item_ref=ref,
        )
        for ref, count in counts.items()
        if count > 1
    ]
    failures += [
        _failure(
            "content",
            f"item {item.ref!r} {problem}",
            context=context,
            item_ref=item.ref,
        )
        for item in answer.items
        for problem in _item_content_problems(item)
    ]
    return failures


def check_form_fields(answer: PageAnswer, context: PageContext) -> list[CheckFailure]:
    """Check that the page's fillable fields are field items with the same values.

    A field the PDF has more than once on the page, such as a group of radio
    buttons, needs as many field items naming it, with the same checked states or
    values. Values are compared with whitespace collapsed.

    Parameters
    ----------
    answer
        The model's answer.
    context
        The page's context, for its fillable form fields.

    Returns
    -------
    list[CheckFailure]
        One failure per form field named by the wrong number of field items or with
        other values, and per field item naming a form field the page lacks.
    """

    widgets = defaultdict(list)
    for field in context.form_fields:
        if field.type != "button":
            widgets[field.name].append(field)
    named = defaultdict(list)
    for item in answer.items:
        if item.field is not None and item.field.fillable_name is not None:
            named[item.field.fillable_name].append(item)

    failures = []
    for name, fields in widgets.items():
        items = named.get(name, [])
        message = _field_mismatch(name, fields, items)
        if message is not None:
            failures.append(
                _failure(
                    "form_fields",
                    message,
                    context=context,
                    item_ref=items[0].ref if items else None,
                )
            )
    failures += [
        _failure(
            "form_fields",
            f"item {item.ref!r} names the form field {name!r}, which is not on "
            "this page",
            context=context,
            item_ref=item.ref,
        )
        for name, items in named.items()
        if name not in widgets
        for item in items
    ]
    return failures


def check_labels(answer: PageAnswer, context: PageContext) -> list[CheckFailure]:
    """Check that each label is in the profile and fits its item's role and kind.

    The label ``other`` fits any item that no other label in the profile fits;
    `unmatched_labels` records those items for review instead.

    Parameters
    ----------
    answer
        The model's answer.
    context
        The page's context, for the profile's labels.

    Returns
    -------
    list[CheckFailure]
        One failure per item or container whose label is not in the profile, and per
        item whose label is for another role or other kinds.
    """

    labels = {label.name.casefold(): label for label in context.labels}
    names = ", ".join(repr(label.name) for label in context.labels)
    failures = []
    for item in answer.items:
        label = labels.get(item.label.casefold())
        if label is None:
            message = (
                f"item {item.ref!r} has the label {item.label!r}, which is not in the "
                f"profile; use one of {names}"
            )
        elif _label_fits(item, label, context.labels):
            continue
        else:
            kinds = ", ".join(label.kinds)
            message = (
                f"item {item.ref!r} is a {item.kind} item with role {item.role}, but "
                f"the label {label.name!r} is for role {label.role} and kinds {kinds}"
            )
        failures.append(_failure("labels", message, context=context, item_ref=item.ref))
    failures += [
        _failure(
            "labels",
            f"container {container.ref!r} has the label {container.label!r}, which "
            f"is not in the profile; use one of {names}",
            context=context,
            item_ref=container.ref,
        )
        for container in answer.containers
        if container.label.casefold() not in labels
    ]
    return failures


def check_languages(answer: PageAnswer, context: PageContext) -> list[CheckFailure]:
    """Check that each language tag is valid and every item with text has one.

    Parameters
    ----------
    answer
        The model's answer.
    context
        The page's context, for its index.

    Returns
    -------
    list[CheckFailure]
        One failure per invalid tag and per item with text but no language.
    """

    failures = []
    for item in answer.items:
        if item.language is not None and not is_language_tag(item.language):
            message = (
                f"item {item.ref!r} has the language {item.language!r}, which is not "
                'a valid BCP-47 tag, such as "en" or "ar"'
            )
        elif item.language is None and _has_text(item):
            message = f"item {item.ref!r} has text but no language"
        else:
            continue
        failures.append(
            _failure("languages", message, context=context, item_ref=item.ref)
        )
    return failures


def check_reading_order(answer: PageAnswer, context: PageContext) -> list[CheckFailure]:
    """Check that the reading order follows the page's writing direction.

    Over consecutive items of the page's flow (headings, body text and navigation),
    a jump back against the direction is allowed only with a move to a new column,
    or to a new band on a page written top to bottom.

    Parameters
    ----------
    answer
        The model's answer.
    context
        The page's context, for its writing direction.

    Returns
    -------
    list[CheckFailure]
        A failure when ``column_order`` does not fit the direction, then one per
        backward jump without a new column or band.
    """

    direction = context.writing_direction
    failures = []
    if direction == "ttb" and answer.column_order is None:
        failures.append(
            _failure(
                "reading_order",
                "the page is written top to bottom, so column_order must say which "
                "way its columns are read",
                context=context,
            )
        )
    elif direction != "ttb" and answer.column_order is not None:
        failures.append(
            _failure(
                "reading_order",
                "column_order is only for pages written top to bottom; set it to null",
                context=context,
            )
        )

    flow = [
        item
        for item in answer.items
        if item.role in _FLOW_ROLES and _box_problem(item.box) is None
    ]
    for previous, item in pairwise(flow):
        problem = _backward_jump(
            previous, item, column_order=answer.column_order, direction=direction
        )
        if problem is not None:
            failures.append(
                _failure(
                    "reading_order",
                    f"item {item.ref!r} is out of reading order: {problem}",
                    context=context,
                    item_ref=item.ref,
                )
            )
    return failures


def check_results(
    failures: Mapping[ExtractionCheckName, list[CheckFailure]], *, attempts: int
) -> list[ExtractionCheckResult]:
    """Record each check's result on the kept answer, in the order the checks run.

    Parameters
    ----------
    failures
        Each check's failures on the kept answer, from `run_checks`.
    attempts
        How many answers were checked.

    Returns
    -------
    list[ExtractionCheckResult]
        The results for the page file's ``checks``.
    """

    return [
        ExtractionCheckResult(
            attempts=attempts,
            failures=failures[name],
            name=name,
            passed=not failures[name],
        )
        for name in failures
    ]


def check_text_added(
    answer: PageAnswer, context: PageContext, text_lines: Sequence[str]
) -> list[CheckFailure]:
    """Find lines the answer has that the page's text layer does not.

    It runs only when `comparison_status` is ``compared``.

    Parameters
    ----------
    answer
        The model's answer.
    context
        The page's context, for its text quality.
    text_lines
        The page's text-layer lines.

    Returns
    -------
    list[CheckFailure]
        One failure per answer line of at least three runs with fewer than half of
        them in the text layer, naming the line's item.
    """

    if comparison_status(answer, context, text_lines) != "compared":
        return []
    answer_lines = _answer_lines(answer)
    layer = sum(_layer_trigrams(text_lines, _answer_trigrams(answer)), Counter())
    counted = [trigrams(comparison_form(line)) for _, line in answer_lines]
    failures = []
    for index in _unmatched(counted, layer):
        ref, line = answer_lines[index]
        failure = _failure(
            "text_added",
            f"item {ref!r} has the line {_shorten(line)!r}, which is not in the "
            "page's text layer",
            context=context,
            item_ref=ref,
        )
        failure.details["line"] = line
        failures.append(failure)
    return failures


def check_text_dropped(
    answer: PageAnswer, context: PageContext, text_lines: Sequence[str]
) -> list[CheckFailure]:
    """Find lines the page's text layer has that the answer does not.

    It runs only when `comparison_status` is ``compared``. A line also counts as
    found when its reversed text is in the answer.

    Parameters
    ----------
    answer
        The model's answer.
    context
        The page's context, for its text quality.
    text_lines
        The page's text-layer lines.

    Returns
    -------
    list[CheckFailure]
        One failure per text-layer line of at least three runs with fewer than half
        of them in the answer.
    """

    if comparison_status(answer, context, text_lines) != "compared":
        return []
    answer_trigrams = _answer_trigrams(answer)
    layer = _layer_trigrams(text_lines, answer_trigrams)
    failures = []
    for index in _unmatched(layer, answer_trigrams):
        failure = _failure(
            "text_dropped",
            f"the page's text layer has the line {_shorten(text_lines[index])!r}, "
            "which is not in your answer",
            context=context,
        )
        failure.details["line"] = text_lines[index]
        failures.append(failure)
    return failures


def comparison_status(
    answer: PageAnswer, context: PageContext, text_lines: Sequence[str]
) -> TextComparison:
    """Decide whether the answer's text can be compared with the text layer.

    Parameters
    ----------
    answer
        The model's answer.
    context
        The page's context, for its measured text quality.
    text_lines
        The page's text-layer lines.

    Returns
    -------
    TextComparison
        ``no_text_layer`` when the page has no text layer, ``garbled_text_layer``
        when it is garbled, ``text_layer_mismatch`` when fewer than half of the
        answer's three-character runs are in the text layer, so it cannot be relied
        on, and otherwise ``compared``.
    """

    if context.text_quality == "garbled":
        return "garbled_text_layer"
    if context.text_quality == "none" or not any(
        comparison_form(line) for line in text_lines
    ):
        return "no_text_layer"
    answer_trigrams = _answer_trigrams(answer)
    layer = sum(_layer_trigrams(text_lines, answer_trigrams), Counter())
    found = (answer_trigrams & layer).total()
    if found < _FOUND_SHARE * answer_trigrams.total():
        return "text_layer_mismatch"
    return "compared"


def retry_message(failures: Mapping[ExtractionCheckName, list[CheckFailure]]) -> str:
    """Write the message that asks the model to fix its answer.

    Parameters
    ----------
    failures
        Each check's failures, from `run_checks`.

    Returns
    -------
    str
        Every failure, one per line, after a line asking for a corrected answer,
        and, when a text check failed, that the model may keep text it read that
        the text layer cannot show.
    """

    lines = [f"- {failure.message}" for found in failures.values() for failure in found]
    message = (
        "Your answer has problems that can be checked without reading the page. Fix "
        "each problem below and answer again with the whole page:\n" + "\n".join(lines)
    )
    if failures.get("text_dropped") or failures.get("text_added"):
        message += "\n" + _TEXT_NOTE
    return message


def review_issues(
    results: Sequence[ExtractionCheckResult], *, item_ids: Mapping[str, str]
) -> list[ReviewIssue]:
    """Turn the failures still on the kept answer into review issues.

    Parameters
    ----------
    results
        The check results, from `check_results`.
    item_ids
        The ID of each item and container, by the ref the answer gave it.

    Returns
    -------
    list[ReviewIssue]
        One issue per failure, in the order the checks run, naming its item's ID
        where one applies.
    """

    issues = []
    for result in results:
        for failure in result.failures:
            ref = failure.details.get("item_ref")
            issues.append(
                ReviewIssue(
                    check=result.name,
                    details=failure.details,
                    item_id=item_ids.get(ref) if isinstance(ref, str) else None,
                    message=failure.message,
                    page_index=failure.page_index,
                    step="extraction",
                )
            )
    return issues


def run_checks(
    answer: PageAnswer, context: PageContext, text_lines: Sequence[str]
) -> dict[ExtractionCheckName, list[CheckFailure]]:
    """Run every check on an answer, in order, the text checks last.

    Parameters
    ----------
    answer
        The model's answer.
    context
        The page's context.
    text_lines
        The page's text-layer lines, from
        `pydelity.extracting.text_layer.read_lines`.

    Returns
    -------
    dict[ExtractionCheckName, list[CheckFailure]]
        Each check's failures, in the order the checks run; an empty list when it
        passed or, for a text check, did not run.
    """

    failures = {name: check(answer, context) for name, check in CHECKS.items()}
    for name, text_check in TEXT_CHECKS.items():
        failures[name] = text_check(answer, context, text_lines)
    return failures


def unmatched_labels(answer: PageAnswer, context: PageContext) -> list[ReviewIssue]:
    """Record content that no label in the profile fits, once per role and kind.

    An item with the label ``other`` passes `check_labels` when no other label fits
    its role and kind. Sending the answer back cannot fix the profile, so such
    content goes on the review list instead.

    Parameters
    ----------
    answer
        The kept answer.
    context
        The page's context, for the profile's labels.

    Returns
    -------
    list[ReviewIssue]
        One ``no_matching_label`` issue per role and kind, in answer order.
    """

    pairs: dict[tuple[ItemRole, ItemKind], list[str]] = {}
    for item in answer.items:
        if item.label.casefold() == _OTHER_LABEL and not _matching_labels(
            item, context.labels
        ):
            pairs.setdefault((item.role, item.kind), []).append(item.ref)
    return [
        ReviewIssue(
            check="no_matching_label",
            details={"item_refs": refs, "kind": kind, "role": role},
            item_id=None,
            message=(
                f"no_matching_label: no label in the profile is for {kind} items with "
                f"role {role}, so {len(refs)} item(s) on the page have the label other"
            ),
            page_index=context.page_index,
            step="extraction",
        )
        for (role, kind), refs in pairs.items()
    ]


# The checks on the content of an answer, in the order they run.
CHECKS: dict[ExtractionCheckName, Check] = {
    "labels": check_labels,
    "content": check_content,
    "languages": check_languages,
    "boxes": check_boxes,
    "containers": check_containers,
    "captions": check_captions,
    "reading_order": check_reading_order,
    "artifacts": check_artifacts,
    "form_fields": check_form_fields,
}

# The checks that compare the answer's text with the page's text layer, in the order
# they run, after `CHECKS`.
TEXT_CHECKS: dict[ExtractionCheckName, TextCheck] = {
    "text_dropped": check_text_dropped,
    "text_added": check_text_added,
}

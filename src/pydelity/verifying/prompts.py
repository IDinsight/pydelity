"""Page-break verification's prompts: one for the judge, one for the verifier.

Each prompt's instructions (the system message) are the same for every break of a
run, so providers can cache them: the task, the rules a verdict follows, the survey's
continuation notes and start markers as hints the pages override and, last, the
user's page-break verification instructions. The text sent before each page image
says which page it is and lists the page's containers and items, as page extraction
recorded them, as JSON, one per line, with boxes on the upright image's grid and
numbered table rows and cells. The verifier's request adds the verdict to review,
the checks it still fails and its differences from the hints. No message asks a
model to change its verdict to match a hint.

No prompt names a language, a document type or a writing direction as a default.
"""

# Standard Library
import json

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

# Package Library
from pydelity.extracting.rendering import GRID, points_box_to_grid
from pydelity.extracting.schemas import Container, Entry, Item, PageFile, Table
from pydelity.review import BreakCheckName, BreakHintName, CheckFailure
from pydelity.surveying.schemas import ItemKind, ItemRole
from pydelity.verifying.schemas import BreakContext, BreakVerdict

# How a page's column order, set on pages written in vertical columns, is given.
_COLUMN_ORDERS = {
    "left_to_right": "Page extraction read its vertical columns from left to right.",
    "right_to_left": "Page extraction read its vertical columns from right to left.",
}

# The content fields each kind of item fills. The page text always lists these for
# an item, and lists any other content field only when it is set.
_CONTENT_FIELDS: dict[ItemKind, tuple[str, ...]] = {
    ItemKind.CODE: ("text",),
    ItemKind.FIELD: ("field",),
    ItemKind.FIGURE: ("figure",),
    ItemKind.FORMULA: ("text", "latex"),
    ItemKind.LIST: ("entries",),
    ItemKind.TABLE: ("table",),
    ItemKind.TEXT: ("text",),
}

# How the writing direction the survey found is given to the models.
_DIRECTIONS = {
    "ltr": "The survey found the page written left to right.",
    "rtl": "The survey found the page written right to left.",
    "ttb": "The survey found the page written top to bottom, in vertical columns.",
}

# The verifier's review list.
_REVIEW = """\
Review the verdict against the page images for:
1. Content that carries on across the break and is missing from the verdict.
2. Pieces that do not carry on.
3. Pieces that end or start in the wrong item or list entry.
4. Wrong joins or text joins.
5. A wrong count of repeated header rows.
6. Repeated items or continuation markers that are missing or wrong.
7. Continuing containers that are missing or wrong."""

# The rules a verdict follows, which both models get.
_RULES = f"""\
What you get. Each of the two pages comes as an upright image, after a text that \
lists the page's containers and items as another model extracted them, in reading \
order, each with its ID. Boxes are [x0, y0, x1, y1] on a grid of {GRID} units across \
and {GRID} down the page image, from its top-left corner. Table rows and the cells in \
each row are numbered from 0. The items help you name and find content, and they can \
be wrong in places. The images decide what carries on. Name items, list entries and \
containers by the IDs listed.

Where a page ends and starts. The end of the page before the break is where its \
reading order ends, and the start of the page after the break is where its reading \
order starts. Follow each page's writing direction and columns, not its top and \
bottom edges. The last content in reading order can sit anywhere on a page, and so \
can the first.

Page furniture. Items with role {ItemRole.ARTIFACT.value}, such as running headers, \
footers and page numbers, never carry on and are never part of a piece. Page \
furniture between the end of one page and the start of the next does not stop \
content from carrying on.

Pieces. A piece is content that carries on across the break. Give each piece the \
item where it ends on the page before the break in earlier_item, and the item where \
it starts on the page after the break in later_item. When an end or a start is a \
list entry, give the entry's ID in earlier_entry or later_entry, and otherwise set \
them to null. Several pieces can carry on at one break, such as the main text and a \
footnote. An item or entry ends at most one piece and starts at most one.

Joins. Give each piece the join that says how it carries on:
- continue_text: a text item carries on in a text item, or a code item in a code \
item. Set text_join.
- continue_entry: text carries on where at least one end is a list entry, from the \
last entry of a list or a text item to the first entry of a list or a text item. Set \
text_join, and the entry at each end that is a list.
- new_entry: a list carries on with a new entry.
- append_rows: a table carries on with new rows. Set repeated_header_rows.
- merge_split_row: a table carries on, and the break cuts its last row on the page \
before the break, which goes on in the first row on the page after the break after \
any repeated header rows. Set repeated_header_rows and cell_joins.
Figures, form fields and formulas never carry on. Set to null every field that a \
piece's join does not use.

Text joins. text_join, and each value of cell_joins, says how two pieces of text \
join:
- space: the script separates the two pieces with a space.
- no_space: the script writes nothing between them, or the break falls inside a word \
that has no hyphen at the end of the earlier piece.
- dehyphenate: a word broken with a hyphen at the end of the earlier piece carries \
on, and the hyphen is removed.
- newline: code carries on, on a new line. Use it for code only.
For merge_split_row, give cell_joins one value per cell of the merged row on the page \
after the break, in the row's cell order: how that cell's text joins the text of the \
cell it continues in the split row, or null when either cell has no text to join.

Tables. A table on the page after the break is the same table when its columns \
match, nothing outside the grid announces a new table between the start of the page \
and the table, and no header row sets out different columns. A border or a closed \
box around each page's part of the table is no sign of a new table. The first rows \
of the later table that repeat the earlier table's header are repeated header rows. \
Count them in repeated_header_rows, 0 when there are none. A split row is a row whose \
cells the break cuts, and which resumes in the first row after the repeated header \
rows.

Repeated items. Items on the page after the break, before the content that carries \
on, that repeat what the page before the break printed for that content, such as a \
repeated title, go in the piece's repeated_items.

Continuation markers. Words or symbols on the content that carries on, on the page \
after the break, that say it continues go in the piece's markers: the item that \
carries each one, the row and cell when a table cell carries it (null otherwise), \
and its text as printed.

Containers. Each bordered or shaded box that carries on across the break goes in \
containers, with its container ID on each page, also when the content inside it \
starts something new on the page after the break.

Nothing carrying on is a valid answer. Set continues to true when you list at least \
one piece, and to false with no pieces when nothing carries on. Decide from what the \
pages show, and in reason quote the text that decides it."""

# The verifier's verdict rules.
_VERDICT = """\
Give a verdict. When the verdict is right and nothing material is wrong, set passed \
to true, with no problems and corrected null. Otherwise set passed to false and list \
each problem: its category, the ID of the item or container on either page it is \
about (null when it is about no single one, such as content missing from the \
verdict), and a description that quotes the text concerned so that a person can find \
it. Then give corrected: the whole verdict again with every problem fixed, following \
the same rules. Start from the verdict, fix what is wrong and keep what is right. \
List only problems that change what the verdict says about the break, not matters of \
taste. Set corrected to null only when you cannot correct the verdict.

The checks the verdict still fails and its differences from the hints are given \
after the pages. The checks come from code that tests the verdict's consistency, and \
a correction must pass them. The hint differences come from the survey, which can be \
wrong. A difference is a problem only when the pages show that the verdict is wrong, \
and a correction need not agree with the hints."""

# The version of the prompts. Increase it whenever the text of either prompt or of
# the page text changes, so a saved verdict file made with the older prompts is made
# again.
PROMPT_VERSION = 1


def _box(bbox: Sequence[float], page: PageFile) -> list[int]:
    """Map a box in points on the displayed page to the upright image's grid.

    Parameters
    ----------
    bbox
        ``[x0, y0, x1, y1]`` in points on the displayed page.
    page
        The page file, for the page's size and the turn applied to its image.

    Returns
    -------
    list[int]
        The box on the grid, from `points_box_to_grid`.
    """

    return points_box_to_grid(
        bbox, height_pt=page.height_pt, rotation=page.rotation, width_pt=page.width_pt
    )


def _container_line(container: Container, page: PageFile) -> str:
    """Write one container as a line of JSON.

    Parameters
    ----------
    container
        The container.
    page
        Its page file.

    Returns
    -------
    str
        Its ID, label, outer container and box on the grid.
    """

    return _json(
        {
            "id": container.id,
            "label": container.label,
            "container": container.container,
            "box": _box(container.bbox, page),
        }
    )


def _entry(entry: Entry) -> dict[str, object]:
    """Write one list entry for an item's line.

    Parameters
    ----------
    entry
        The entry.

    Returns
    -------
    dict[str, object]
        Its ID, nesting level, marker and text.
    """

    return {
        "id": entry.id,
        "level": entry.level,
        "marker": entry.marker,
        "text": entry.text,
    }


def _hints(context: BreakContext) -> str:
    """Write the survey's hints about how content continues across pages.

    Parameters
    ----------
    context
        The break's context.

    Returns
    -------
    str
        The heading, the continuation notes and the start markers, each list being
        ``none`` when the survey gave none.
    """

    notes = [f"- {note}" for note in context.continuation_notes]
    markers = [
        f"- {_json(marker.text)}: {marker.description}"
        for marker in context.start_markers
    ]
    return (
        "Hints from the survey, which read the whole PDF. They describe the whole PDF, "
        "can be wrong, and the pages override them.\n"
        "How content continues from one page to the next:\n"
        + ("\n".join(notes) or "none")
        + "\nStart markers, text that marks where a new unit of content starts:\n"
        + ("\n".join(markers) or "none")
    )


def _item_line(item: Item, page: PageFile) -> str:
    """Write one item as a line of JSON.

    Parameters
    ----------
    item
        The item.
    page
        Its page file.

    Returns
    -------
    str
        Its ID, kind, role, label, container, caption target and box on the grid,
        then the content fields its kind fills, and any other content field that is
        set, as the page file has them.
    """

    line: dict[str, object] = {
        "id": item.id,
        "kind": item.kind.value,
        "role": item.role.value,
        "label": item.label,
        "container": item.container,
        "caption_of": item.caption_of,
        "box": _box(item.bbox, page),
    }
    content: dict[str, object] = {
        "text": item.text,
        "latex": item.latex,
        "entries": None
        if item.entries is None
        else [_entry(entry) for entry in item.entries],
        "table": None if item.table is None else _table(item.table),
        "figure": None
        if item.figure is None
        else {"description": item.figure.description, "text": item.figure.text},
        "field": None if item.field is None else item.field.model_dump(mode="json"),
    }
    kind_fields = _CONTENT_FIELDS.get(item.kind, ())
    for name, value in content.items():
        if value is not None or name in kind_fields:
            line[name] = value
    return _json(line)


def _json(value: object) -> str:
    """Write a value as one line of JSON, keeping every script as it is.

    Parameters
    ----------
    value
        The value.

    Returns
    -------
    str
        The JSON.
    """

    return json.dumps(value, ensure_ascii=False)


def _listed(found: Iterable[Sequence[CheckFailure]]) -> str:
    """List check failures or hint differences for the verifier's review text.

    Parameters
    ----------
    found
        Each check's failures, or each hint's differences.

    Returns
    -------
    str
        One line per failure or difference, or ``none``.
    """

    lines = [f"- {failure.message}" for failures in found for failure in failures]
    return "\n".join(lines) if lines else "none"


def _page_text(page: PageFile, *, side: str) -> str:
    """Write what is sent about one page of the break before its image.

    Parameters
    ----------
    page
        The page file.
    side
        ``before`` or ``after``, the page's side of the break.

    Returns
    -------
    str
        The page's index and number, the turn applied to its image, the writing
        direction the survey found, its column order when set, and its containers
        and items, one per line.
    """

    rotation = (
        f"The image was turned {page.rotation} degrees clockwise to show the page "
        "upright."
        if page.rotation
        else "The image shows the page as it is displayed."
    )
    about = [rotation, _DIRECTIONS[page.inputs.context.writing_direction]]
    if page.column_order is not None:
        about.append(_COLUMN_ORDERS[page.column_order])
    containers = [_container_line(container, page) for container in page.containers]
    items = [_item_line(item, page) for item in page.items]
    return (
        f"The page {side} the break: page index {page.page_index}, page "
        f"{page.page_number}. Its image follows this text.\n"
        + " ".join(about)
        + "\nContainers, one per line:\n"
        + ("\n".join(containers) or "none")
        + "\nItems in reading order, one per line:\n"
        + ("\n".join(items) or "none")
    )


def _table(table: Table) -> dict[str, object]:
    """Write a table for an item's line, with its rows and cells numbered.

    Parameters
    ----------
    table
        The table.

    Returns
    -------
    dict[str, object]
        Its header row count and its rows, each with its number and its cells, each
        cell with its number, its text and any span other than 1.
    """

    rows = []
    for row_number, cells in enumerate(table.rows):
        listed = []
        for cell_number, cell in enumerate(cells):
            entry: dict[str, object] = {"cell": cell_number, "text": cell.text}
            if cell.col_span != 1:
                entry["col_span"] = cell.col_span
            if cell.row_span != 1:
                entry["row_span"] = cell.row_span
            listed.append(entry)
        rows.append({"row": row_number, "cells": listed})
    return {"header_rows": table.header_rows, "rows": rows}


def _with_user_instructions(system_message: str, instructions: str | None) -> str:
    """Add the user's instructions at the end of a system message, when there are any.

    Parameters
    ----------
    system_message
        pydelity's instructions.
    instructions
        The user's page-break verification instructions, or ``None``.

    Returns
    -------
    str
        The system message, ending with the user's instructions under a heading
        that says they add to pydelity's rules.
    """

    if not instructions:
        return system_message
    return (
        system_message
        + "\n\nThe user's instructions for this PDF's page breaks follow. They add to "
        f"the rules above and do not replace them.\n{instructions}"
    )


@dataclass(frozen=True)
class BreakPrompts:
    """The instructions and text parts of one page-break request.

    Attributes
    ----------
    earlier_text
        The text sent before the earlier page's image. Its first line names the
        break.
    later_text
        The text sent before the later page's image.
    review_text
        For the verifier, the text sent after both images: the verdict to review,
        the checks it still fails and its differences from the hints. ``None`` for
        the judge.
    system_message
        The instructions, the same for every break of a run.
    """

    earlier_text: str
    later_text: str
    review_text: str | None
    system_message: str


def judge_break(
    context: BreakContext, *, earlier: PageFile, later: PageFile
) -> BreakPrompts:
    """Write the judge's messages for one break.

    Parameters
    ----------
    context
        The break's context.
    earlier
        The page file of the page before the break.
    later
        The page file of the page after the break.

    Returns
    -------
    BreakPrompts
        The instructions, the same for every break of a run, and the text sent
        before each page image.
    """

    first, second = earlier.page_index, later.page_index
    return BreakPrompts(
        earlier_text=(
            f"Page break between page indexes {first} and {second} (pages {first + 1} "
            f"and {second + 1} of {context.page_count})\n\n"
            + _page_text(earlier, side="before")
        ),
        later_text=_page_text(later, side="after"),
        review_text=None,
        system_message=judge_instructions(context),
    )


def judge_instructions(context: BreakContext) -> str:
    """Write the judge's instructions, the same for every break of a run.

    Parameters
    ----------
    context
        The context every break of the PDF shares.

    Returns
    -------
    str
        The rules, the survey's hints, and the user's instructions when set.
    """

    system_message = (
        "You judge one page break, the break between two consecutive pages of a PDF. "
        "Say whether any content carries on from the page before the break to the "
        "page after it, and how each piece joins. A program joins the two pages' "
        "items from your verdict. It knows no language, so your verdict must say "
        "everything it needs.\n\n"
        f"{_RULES}\n\n"
        "Your answer is checked by code for consistency, and you will be told what "
        "to fix if a check fails.\n\n"
        f"{_hints(context)}"
    )
    return _with_user_instructions(system_message, context.instructions)


def verify_break(
    context: BreakContext,
    *,
    differences: Mapping[BreakHintName, list[CheckFailure]],
    failures: Mapping[BreakCheckName, list[CheckFailure]],
    judged: BreakPrompts,
    verdict: BreakVerdict,
) -> BreakPrompts:
    """Write the verifier's messages for one break's verdict.

    Parameters
    ----------
    context
        The break's context.
    differences
        The verdict's differences from the hints, from
        `pydelity.verifying.validators.compare_with_hints`.
    failures
        The checks the verdict still fails, from
        `pydelity.verifying.validators.run_checks`.
    judged
        The judge's prompts for the break, from `judge_break`. The verifier's
        request repeats their page texts.
    verdict
        The judge's verdict to review.

    Returns
    -------
    BreakPrompts
        The instructions, the same for every break of a run, the judge's page texts,
        and the review text with the verdict, the checks it still fails and its
        differences from the hints.
    """

    system_message = (
        "You review another model's verdict on one page break, the break between two "
        "consecutive pages of a PDF, against images of both pages. You are not "
        "judging the break from scratch. You are checking someone else's work and "
        "correcting it where it is wrong.\n\n"
        f"{_REVIEW}\n\n{_VERDICT}\n\n"
        "The rules the verdict follows, which a correction follows too:\n\n"
        f"{_RULES}\n\n{_hints(context)}"
    )
    review_text = "\n\n".join(
        [
            "The page-break verdict to review:\n"
            + _json(verdict.model_dump(mode="json")),
            "Checks it still fails, which a correction must pass:\n"
            + _listed(failures.values()),
            "Differences from the hints, which the pages override:\n"
            + _listed(differences.values()),
        ]
    )
    return BreakPrompts(
        earlier_text=judged.earlier_text,
        later_text=judged.later_text,
        review_text=review_text,
        system_message=_with_user_instructions(system_message, context.instructions),
    )

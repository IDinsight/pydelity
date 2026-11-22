"""Tests for page extraction's checks and hints on a model's answer for one page.

Each check must find every problem of its kind, name the item it is about, and pass a
well-formed answer. Each hint must find every difference of its kind and describe it
without telling the model what to change, and a hint difference is never a check
failure. The text hints also run on the first page of four committed PDFs, in Arabic,
Chinese, Japanese and English, against an answer built from the page's own text
layer.
"""

# Standard Library
import re

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import NamedTuple

# Third Party Library
import pymupdf
import pytest

# Package Library
from pydelity.extracting.schemas import (
    AnswerContainer,
    AnswerItem,
    ColumnOrder,
    PageAnswer,
    PageContext,
    PageRepeatedLine,
)
from pydelity.extracting.text_layer import PageText, read_page_text
from pydelity.extracting.validators import (
    check_artifacts,
    check_boxes,
    check_captions,
    check_containers,
    check_content,
    check_form_fields,
    check_labels,
    check_languages,
    check_reading_order,
    check_text_added,
    check_text_dropped,
    compare_with_hints,
    comparison_status,
    hint_issues,
    hint_results,
    retry_message,
    run_checks,
    unmatched_labels,
)
from pydelity.review import CheckFailure
from pydelity.surveying.schemas import Direction, FormField

# Item boxes on the upright image's grid. Horizontal text in two columns, each with a
# top and a bottom item, and vertical text in two bands, each with a left and a right
# column.
_BOXES = {
    "left_bottom": [50, 400, 450, 900],
    "left_top": [50, 100, 450, 300],
    "lower_left": [600, 550, 750, 950],
    "lower_right": [800, 550, 950, 950],
    "right_bottom": [550, 600, 950, 900],
    "right_top": [550, 100, 950, 500],
    "upper_left": [600, 50, 750, 450],
    "upper_right": [800, 50, 950, 450],
}

# Words that tell a model what to change, which no hint difference may hold.
_ORDER_WORDS = re.compile(r"\b(fix|must|need|needs|set it|should)\b", re.IGNORECASE)


class _ReadingOrder(NamedTuple):
    """Items in and out of reading order on a page with one writing direction."""

    bad_column_order: ColumnOrder | None
    """A ``column_order`` that does not fit the page's direction."""

    bad_column_order_words: str
    """Words the difference for `bad_column_order` holds."""

    column_order: ColumnOrder | None
    """The answer's ``column_order`` that fits the page."""

    direction: Direction
    """The page's writing direction."""

    in_order: tuple[str, ...]
    """Refs from `_BOXES`, in an order that reads the page column by column."""

    jumps_back: tuple[tuple[str, str], ...]
    """Each item of `out_of_order` that jumps back, with words its difference
    holds."""

    out_of_order: tuple[str, ...]
    """Refs from `_BOXES`, in an order that reads the columns the wrong way."""


class _ScriptLine(NamedTuple):
    """The first page of a committed PDF in one script, and a line to remove or add."""

    direction: Direction
    """The page's writing direction."""

    language: str
    """The BCP-47 tag of the page's text."""

    line: str
    """A line of text on the page to remove, or a line not on it to add."""

    name: str
    """The PDF's file name."""


def _answer(
    *items: AnswerItem,
    column_order: ColumnOrder | None = None,
    containers: Sequence[AnswerContainer] = (),
) -> PageAnswer:
    """Put items and containers together into a page answer.

    Parameters
    ----------
    *items
        The items, in reading order.
    column_order
        The order the page's columns of vertical text are read in.
    containers
        The containers.

    Returns
    -------
    PageAnswer
        The answer.
    """

    return PageAnswer(
        column_order=column_order, containers=list(containers), items=list(items)
    )


def _cell(text: str | None, *, col_span: int = 1, row_span: int = 1) -> dict:
    """Write one table cell, as the model would send it.

    Parameters
    ----------
    text
        The cell's text.
    col_span
        How many columns it covers.
    row_span
        How many rows it covers.

    Returns
    -------
    dict
        The cell.
    """

    return {"col_span": col_span, "row_span": row_span, "text": text}


def _container(
    *, box: list[int], container: str | None = None, ref: str
) -> AnswerContainer:
    """Make a container with the label ``Body``.

    Parameters
    ----------
    box
        Its box on the grid.
    container
        The ref of the container it sits in, if any.
    ref
        Its ref.

    Returns
    -------
    AnswerContainer
        The container.
    """

    return AnswerContainer(box=box, container=container, label="Body", ref=ref)


def _correct_answer(
    lines: Sequence[str],
    *,
    answer_item: Callable[..., AnswerItem],
    script: _ScriptLine,
) -> PageAnswer:
    """Write a correct answer for a page, with one text item per text-layer line.

    The text checks read only the items' text, so every item keeps the default box.

    Parameters
    ----------
    lines
        The page's text-layer lines.
    answer_item
        The fixture that builds an item.
    script
        The page, for its language and direction.

    Returns
    -------
    PageAnswer
        The answer, with items ``t1``, ``t2`` and so on in the lines' order.
    """

    return _answer(
        *(
            answer_item(language=script.language, ref=f"t{number}", text=line)
            for number, line in enumerate(lines, start=1)
        ),
        column_order="right_to_left" if script.direction == "ttb" else None,
    )


def _field(
    *,
    checked: bool | None = None,
    field_type: str = "text",
    fillable_name: str | None,
    value: str | None = None,
) -> dict:
    """Write the content of a field item, as the model would send it.

    Parameters
    ----------
    checked
        Whether a checkbox or radio button is marked.
    field_type
        The field item's type.
    fillable_name
        The name of the PDF form field it shows.
    value
        Its value.

    Returns
    -------
    dict
        The field content.
    """

    return {
        "checked": checked,
        "field_type": field_type,
        "fillable_name": fillable_name,
        "options": [],
        "prompt": None,
        "value": value,
    }


def _form_field(
    *,
    checked: bool | None = None,
    field_type: str = "text",
    name: str,
    value: str | None = None,
) -> FormField:
    """Make one of the PDF's fillable form fields on the first page.

    Parameters
    ----------
    checked
        Whether a checkbox is on.
    field_type
        The form field's type.
    name
        Its name.
    value
        Its value.

    Returns
    -------
    FormField
        The form field.
    """

    return FormField.model_validate(
        {
            "bbox": (100.0, 100.0, 300.0, 120.0),
            "checked": checked,
            "name": name,
            "options": [],
            "page_index": 0,
            "type": field_type,
            "value": value,
        }
    )


def _found(failures: list[CheckFailure]) -> list[tuple[object, str]]:
    """Reduce failures or differences to the ref they name and their message.

    Parameters
    ----------
    failures
        One check's failures, or one hint's differences.

    Returns
    -------
    list[tuple[object, str]]
        Each one's item ref and message.
    """

    return [(failure.details.get("item_ref"), failure.message) for failure in failures]


def _items(
    refs: Sequence[str], *, answer_item: Callable[..., AnswerItem]
) -> list[AnswerItem]:
    """Make body text items with boxes from `_BOXES`, in the given order.

    Parameters
    ----------
    refs
        The items' refs, which are keys of `_BOXES`.
    answer_item
        The fixture that builds an item.

    Returns
    -------
    list[AnswerItem]
        The items.
    """

    return [answer_item(box=_BOXES[ref], ref=ref) for ref in refs]


def _matches(
    found: list[tuple[object, str]], expected: list[tuple[str | None, str]]
) -> bool:
    """Tell whether failures or differences name the expected refs and words.

    Parameters
    ----------
    found
        Each one's item ref and message, from `_found`.
    expected
        Each expected one's item ref and words its message holds, in order.

    Returns
    -------
    bool
        Whether both lists have the same length and each pair matches.
    """

    return len(found) == len(expected) and all(
        ref == want_ref and words in message
        for (ref, message), (want_ref, words) in zip(found, expected, strict=True)
    )


def _read_page(
    script: _ScriptLine,
    *,
    page_context: Callable[..., PageContext],
    pdf_path: Callable[[str], Path],
) -> tuple[PageContext, PageText]:
    """Read the first page's text layer, with a context that calls it good.

    Parameters
    ----------
    script
        The page's PDF, language and direction.
    page_context
        The fixture that builds a page context.
    pdf_path
        The fixture that finds a committed test PDF.

    Returns
    -------
    tuple[PageContext, PageText]
        The page's context and its text layer.
    """

    with pymupdf.open(pdf_path(script.name)) as document:
        page = document[0]
        context = page_context(
            height_pt=page.rect.height,
            languages=[script.language],
            page_count=len(document),
            text_quality="good",
            width_pt=page.rect.width,
            writing_direction=script.direction,
        )
        return context, read_page_text(document, context=context)


def test_a_page_answered_as_one_full_page_figure_passes_every_check_and_hint(
    answer_item: Callable[..., AnswerItem],
    no_page_text: PageText,
    page_context: Callable[..., PageContext],
) -> None:
    """A page that is one picture may be answered as one figure covering the page.

    The six checks run, each passing, and the five hints run, each agreeing.
    """

    figure = answer_item(
        box=[0, 0, 1000, 1000],
        figure={"description": "A photograph of a harbor at dawn.", "text": None},
        kind="figure",
        label="Figure",
        language=None,
        text=None,
    )

    failures = run_checks(_answer(figure), page_context(), no_page_text)
    differences = compare_with_hints(_answer(figure), page_context(), no_page_text)

    assert failures == {
        "labels": [],
        "content": [],
        "languages": [],
        "boxes": [],
        "containers": [],
        "captions": [],
    }
    assert differences == {
        "reading_order": [],
        "artifacts": [],
        "form_fields": [],
        "text_dropped": [],
        "text_added": [],
    }


@pytest.mark.parametrize(
    "script",
    [
        _ScriptLine(
            direction="rtl",
            language="ar",
            line="القطط تنام في الحديقة",
            name="irs_pub1_arabic.pdf",
        ),
        _ScriptLine(
            direction="ltr",
            language="zh-Hans",
            line="今天天气很好我们去公园散步",
            name="irs_pub1_chinese_simplified.pdf",
        ),
        _ScriptLine(
            direction="ttb",
            language="ja",
            line="桜の花が満開になりました",
            name="japan_official_gazette_2019_extra_9.pdf",
        ),
        _ScriptLine(
            direction="ltr",
            language="en",
            line="Bring a packed lunch on Thursday",
            name="irs_w9_instructions.pdf",
        ),
    ],
    ids=["arabic", "chinese", "japanese", "english"],
)
def test_adding_a_line_is_an_added_text_difference(
    answer_item: Callable[..., AnswerItem],
    page_context: Callable[..., PageContext],
    pdf_path: Callable[[str], Path],
    script: _ScriptLine,
) -> None:
    """A line in the page's script that the page does not hold differs as added."""

    context, page_text = _read_page(
        script, page_context=page_context, pdf_path=pdf_path
    )
    correct = _correct_answer(page_text.lines, answer_item=answer_item, script=script)
    answer = _answer(
        *correct.items,
        answer_item(language=script.language, ref="added", text=script.line),
        column_order=correct.column_order,
    )

    added = check_text_added(answer, context, page_text)

    assert check_text_dropped(correct, context, page_text) == []
    assert check_text_added(correct, context, page_text) == []
    assert [
        (failure.details["item_ref"], failure.details["line"]) for failure in added
    ] == [("added", script.line)]
    assert script.line in added[0].message
    assert check_text_dropped(answer, context, page_text) == []


def test_artifacts_hint_agrees_when_furniture_is_covered_at_one_of_its_places(
    answer_item: Callable[..., AnswerItem],
    page_context: Callable[..., PageContext],
) -> None:
    """One covered place is enough, and the item's text is never compared.

    The furniture line sits at three places. An artifact item whose box reaches
    within 20 grid units of one place's center covers it, though its text shares
    nothing with the stored line.
    """

    context = page_context(
        repeated_lines=[
            PageRepeatedLine(
                id="R1",
                normalized="annual report #",
                text="Annual Report 2024",
                use="artifact",
            )
        ]
    )
    page_text = PageText(
        furniture={
            "R1": ((100, 30, 300, 45), (420, 480, 580, 495), (700, 955, 900, 970))
        },
        lines=(),
    )
    answer = _answer(
        answer_item(
            box=[700, 930, 900, 945],
            label="Page furniture",
            language="fr",
            ref="footer",
            role="artifact",
            text="Bulletin officiel",
        )
    )

    assert check_artifacts(answer, context, page_text) == []


def test_artifacts_hint_names_uncovered_furniture_and_skips_what_it_cannot_judge(
    answer_item: Callable[..., AnswerItem],
    page_context: Callable[..., PageContext],
) -> None:
    """Furniture no artifact item covers differs, naming the line and its places.

    Body text over the furniture's places does not count. An artifact item with a
    malformed box is left out without an error, even when its first four values
    would cover a place, and a furniture line the text layer does not hold is
    skipped.
    """

    context = page_context(
        repeated_lines=[
            PageRepeatedLine(id="R1", normalized="#", text="2", use="artifact"),
            PageRepeatedLine(
                id="R2",
                normalized="annual report #",
                text="Annual Report 2024",
                use="artifact",
            ),
        ]
    )
    page_text = PageText(
        furniture={
            "R1": (
                (480, 960, 520, 975),
                (120, 300, 140, 315),
                (120, 340, 140, 355),
                (120, 380, 140, 395),
            )
        },
        lines=(),
    )
    answer = _answer(
        answer_item(box=[100, 280, 900, 420], ref="numbers"),
        answer_item(
            box=[100, 20, 900, 60],
            label="Page furniture",
            ref="header",
            role="artifact",
            text="Annual Report 2024",
        ),
        answer_item(
            box=[500, 960], label="Page furniture", ref="short", role="artifact"
        ),
        answer_item(
            box=[470, 950, 530, 985, 0],
            label="Page furniture",
            ref="long",
            role="artifact",
        ),
    )

    failures = check_artifacts(answer, context, page_text)

    found = _found(failures)
    assert _matches(
        found,
        [
            (
                None,
                "artifacts: the survey found the repeated line R1, '2', to be page "
                "furniture, at [480, 960, 520, 975], [120, 300, 140, 315], "
                "[120, 340, 140, 355] and 1 more on the grid, and no item with role "
                "artifact covers it",
            )
        ],
    ), found


def test_boxes_check_finds_malformed_off_page_and_shared_boxes(
    answer_item: Callable[..., AnswerItem],
    no_page_text: PageText,
    page_context: Callable[..., PageContext],
) -> None:
    """Each box has four ordered values on the grid within 5 units, and is unique.

    A full-page box and one at the edge of the tolerance pass.
    """

    answer = _answer(
        answer_item(box=[100, 100, 900], ref="three"),
        answer_item(box=[400, 200, 400, 300], ref="flat"),
        answer_item(box=[100, 300, 1006, 350], ref="outside"),
        answer_item(box=[-5, 400, 1005, 450], ref="edge"),
        answer_item(box=[0, 0, 1000, 1000], ref="full"),
        answer_item(box=[100, 500, 900, 550], ref="first"),
        answer_item(box=[100, 500, 900, 550], ref="second"),
    )

    failures = check_boxes(answer, page_context(), no_page_text)

    found = _found(failures)
    assert _matches(
        found,
        [
            ("three", "has the box [100, 100, 900], which has 3 values instead of 4"),
            ("flat", "which needs x0 < x1 and y0 < y1"),
            ("outside", "which reaches outside the page"),
            ("second", "items 'first', 'second' have the same box [100, 500, 900"),
        ],
    ), found


def test_captions_check_needs_each_caption_to_name_a_non_caption_item(
    answer_item: Callable[..., AnswerItem],
    no_page_text: PageText,
    page_context: Callable[..., PageContext],
) -> None:
    """Each caption names a non-caption item, and only captions set caption_of.

    A caption that names a figure on the page passes.
    """

    answer = _answer(
        answer_item(
            box=[100, 100, 900, 500],
            figure={"description": "A bar chart of rainfall by month.", "text": None},
            kind="figure",
            label="Figure",
            language=None,
            ref="chart",
            text=None,
        ),
        answer_item(
            box=[100, 510, 900, 530],
            caption_of="chart",
            label="Caption",
            ref="good",
            role="caption",
        ),
        answer_item(
            box=[100, 540, 900, 560], label="Caption", ref="bare", role="caption"
        ),
        answer_item(
            box=[100, 570, 900, 590],
            caption_of="good",
            label="Caption",
            ref="of_caption",
            role="caption",
        ),
        answer_item(box=[100, 600, 900, 650], caption_of="chart", ref="body_text"),
    )

    failures = check_captions(answer, page_context(), no_page_text)

    found = _found(failures)
    assert _matches(
        found,
        [
            ("bare", "caption 'bare' has caption_of None; it needs the ref"),
            ("of_caption", "caption 'of_caption' has caption_of 'good'; it needs"),
            ("body_text", "item 'body_text' sets caption_of but its role is body"),
        ],
    ), found


def test_containers_check_finds_unknown_refs_items_outside_and_nesting_loops(
    answer_item: Callable[..., AnswerItem],
    no_page_text: PageText,
    page_context: Callable[..., PageContext],
) -> None:
    """Containers must exist, hold what names them within 20 units, and not loop.

    An item inside its container, and one past its edges by exactly 20 units, pass.
    """

    answer = _answer(
        answer_item(box=[100, 100, 400, 400], container="panel", ref="inside"),
        answer_item(box=[30, 30, 520, 520], container="panel", ref="edge"),
        answer_item(box=[100, 100, 521, 400], container="panel", ref="outside"),
        answer_item(box=[100, 700, 400, 750], container="nowhere", ref="lost"),
        containers=[
            _container(box=[50, 50, 500, 500], ref="panel"),
            _container(box=[600, 600, 900, 900], container="loop_2", ref="loop_1"),
            _container(box=[610, 610, 890, 890], container="loop_1", ref="loop_2"),
        ],
    )

    failures = check_containers(answer, page_context(), no_page_text)

    found = _found(failures)
    assert _matches(
        found,
        [
            ("outside", "item 'outside' lies outside its container 'panel'"),
            ("lost", "item 'lost' names the container 'nowhere', which does not"),
            ("loop_1", "container 'loop_1' sits inside itself through its"),
            ("loop_2", "container 'loop_2' sits inside itself through its"),
        ],
    ), found


def test_content_check_finds_wrong_fields_for_the_kind_and_bad_table_grids(
    answer_item: Callable[..., AnswerItem],
    no_page_text: PageText,
    page_context: Callable[..., PageContext],
) -> None:
    """Each kind fills its own fields, and tables lay out on a whole grid.

    A table with a row span, a column span and two header rows passes.
    """

    answer = _answer(
        answer_item(
            ref="text_with_table",
            table={"header_rows": 0, "rows": [[_cell("12")]]},
        ),
        answer_item(entries=[], kind="list", ref="empty_list", text=None),
        answer_item(
            figure={"description": "  ", "text": None},
            kind="figure",
            label="Figure",
            ref="blank_figure",
            text=None,
        ),
        answer_item(
            field=_field(field_type="checkbox", fillable_name=None),
            kind="field",
            label="Form item",
            ref="unmarked",
            text=None,
        ),
        answer_item(
            kind="table",
            ref="overlapping",
            table={
                "header_rows": 0,
                "rows": [
                    [_cell("a"), _cell("b", row_span=2)],
                    [_cell("c", col_span=2)],
                ],
            },
            text=None,
        ),
        answer_item(
            kind="table",
            ref="ragged",
            table={"header_rows": 1, "rows": [[_cell("a"), _cell("b")], [_cell("c")]]},
            text=None,
        ),
        answer_item(
            kind="table",
            ref="good_table",
            table={
                "header_rows": 2,
                "rows": [
                    [_cell("Region", row_span=2), _cell("Rainfall", col_span=2)],
                    [_cell("2023"), _cell("2024")],
                    [_cell("North"), _cell("410"), _cell("455")],
                    [_cell("Total", col_span=2), _cell("865")],
                ],
            },
            text=None,
        ),
    )

    failures = check_content(answer, page_context(), no_page_text)

    found = _found(failures)
    assert _matches(
        found,
        [
            ("text_with_table", "sets table, which a text item does not use"),
            ("empty_list", "item 'empty_list' is a list with no entries"),
            ("blank_figure", "item 'blank_figure' is a figure with a blank descr"),
            ("unmarked", "item 'unmarked' is a checkbox field without checked"),
            ("overlapping", "has a table that has a cell in row 2 that overlaps"),
            ("ragged", "has rows covering different numbers of columns, [2, 1]"),
        ],
    ), found


def test_every_hint_difference_is_a_review_issue_and_never_a_check_failure(
    answer_item: Callable[..., AnswerItem],
    page_context: Callable[..., PageContext],
) -> None:
    """An answer that differs from all five hints passes every check.

    The answer reads an item against the page's direction, gives the running header
    as body text, gives a fillable field another value, leaves out a stored line and
    adds one. Each hint finds its difference, in the order the hints run, and each
    difference becomes a review issue naming its item's ID where it is about one
    item. No difference tells the model what to change.
    """

    header = "Quarterly Notice Header"
    stored = (
        header,
        "Payments are due by the end of March.",
        "Late payments add a penalty of five percent.",
        "Ask the office for a form.",
    )
    context = page_context(
        form_fields=[_form_field(name="city", value="Springfield")],
        repeated_lines=[
            PageRepeatedLine(
                id="R1",
                normalized="quarterly notice header",
                text=header,
                use="artifact",
            )
        ],
    )
    page_text = PageText(furniture={"R1": ((100, 20, 600, 60),)}, lines=stored)
    answer = _answer(
        answer_item(box=[100, 20, 600, 60], ref="h", text=header),
        answer_item(box=[100, 400, 900, 440], ref="t2", text=stored[2]),
        answer_item(box=[100, 200, 900, 240], ref="t1", text=stored[1]),
        answer_item(
            box=[100, 500, 900, 540], ref="added", text="Bring a packed lunch today."
        ),
        answer_item(
            box=[100, 600, 900, 640],
            field=_field(fillable_name="city", value="Shelbyville"),
            kind="field",
            label="Form item",
            ref="city",
            text=None,
        ),
    )
    item_ids = {
        "added": "p0000-004",
        "city": "p0000-005",
        "h": "p0000-001",
        "t1": "p0000-003",
        "t2": "p0000-002",
    }

    failures = run_checks(answer, context, page_text)
    results = hint_results(compare_with_hints(answer, context, page_text))
    issues = hint_issues(results, item_ids=item_ids)

    assert not any(failures.values()), failures
    assert [(result.name, len(result.differences)) for result in results] == [
        ("reading_order", 1),
        ("artifacts", 1),
        ("form_fields", 1),
        ("text_dropped", 1),
        ("text_added", 1),
    ]
    assert [(issue.check, issue.item_id) for issue in issues] == [
        ("reading_order", "p0000-003"),
        ("artifacts", None),
        ("form_fields", "p0000-005"),
        ("text_dropped", None),
        ("text_added", "p0000-004"),
    ]
    assert all(
        (issue.page_index, issue.step) == (0, "extraction")
        and issue.message.startswith(f"{issue.check}: ")
        for issue in issues
    )
    assert stored[3] in issues[3].message
    assert [
        issue.message for issue in issues if _ORDER_WORDS.search(issue.message)
    ] == []


def test_form_fields_hint_compares_fillable_fields_with_field_items(
    answer_item: Callable[..., AnswerItem],
    no_page_text: PageText,
    page_context: Callable[..., PageContext],
) -> None:
    """Each fillable field agrees when named once, with its value or checked state.

    A value that differs only in spacing agrees. No item has to name the push button.
    """

    context = page_context(
        form_fields=[
            _form_field(name="full_name", value="Jane   Q.\nPublic"),
            _form_field(field_type="button", name="submit"),
            _form_field(name="city", value="Springfield"),
            _form_field(checked=True, field_type="checkbox", name="agree", value="Yes"),
            _form_field(name="zip", value="62704"),
        ]
    )
    fields = {
        "full_name": _field(fillable_name="full_name", value="Jane Q. Public"),
        "city": _field(fillable_name="city", value="Shelbyville"),
        "agree": _field(checked=False, field_type="checkbox", fillable_name="agree"),
        "zip_1": _field(fillable_name="zip", value="62704"),
        "zip_2": _field(fillable_name="zip", value="62704"),
        "extra": _field(fillable_name="fax", value="555-0100"),
    }
    answer = _answer(
        *(
            answer_item(
                box=[100, 100 + 60 * index, 900, 150 + 60 * index],
                field=field,
                kind="field",
                label="Form item",
                ref=ref,
                text=None,
            )
            for index, (ref, field) in enumerate(fields.items())
        )
    )

    failures = check_form_fields(answer, context, no_page_text)

    found = _found(failures)
    assert _matches(
        found,
        [
            (
                "city",
                "form_fields: the PDF stores the values ['Springfield'] for the form "
                "field 'city', but its field items say ['Shelbyville']",
            ),
            (
                "agree",
                "form_fields: the PDF stores the checked states [True] for the form "
                "field 'agree', but its field items say [False]",
            ),
            (
                "zip_1",
                "the form field 'zip' is on the page 1 time(s), but 2 field item(s) "
                "name it",
            ),
            (
                "extra",
                "item 'extra' names the form field 'fax', which the PDF does not "
                "have on this page",
            ),
        ],
    ), found


def test_labels_check_names_misfit_labels_and_lets_other_stand_in_for_missing_ones(
    answer_item: Callable[..., AnswerItem],
    no_page_text: PageText,
    page_context: Callable[..., PageContext],
) -> None:
    """Labels must be in the profile and fit the item's role and kind.

    The label ``other``, in any case, passes for content that no profile label fits.
    Each such role and kind is recorded once for review. ``other`` fails where a
    label fits.
    """

    context = page_context()
    answer = _answer(
        answer_item(box=[100, 100, 900, 150], label="Body", ref="body"),
        answer_item(box=[100, 160, 900, 210], label="Sidebar", ref="unknown"),
        answer_item(box=[100, 220, 900, 270], label="Heading", ref="wrong_role"),
        answer_item(box=[100, 280, 900, 330], label="Figure", ref="wrong_kind"),
        answer_item(
            box=[100, 340, 900, 390],
            entries=[{"level": 0, "marker": "-", "text": "Bring water."}],
            kind="list",
            label="other",
            ref="other_list",
            text=None,
        ),
        answer_item(
            box=[100, 400, 900, 450], label="other", ref="aside_1", role="aside"
        ),
        answer_item(
            box=[100, 460, 900, 510], label="OTHER", ref="aside_2", role="aside"
        ),
        answer_item(
            box=[100, 900, 900, 950], label="other", ref="note", role="footnote"
        ),
    )

    failures = check_labels(answer, context, no_page_text)
    issues = unmatched_labels(answer, context)

    found = _found(failures)
    assert _matches(
        found,
        [
            ("unknown", "item 'unknown' has the label 'Sidebar', which is not in the"),
            (
                "wrong_role",
                "but the label 'Heading' is for role heading and kinds text",
            ),
            ("wrong_kind", "but the label 'Figure' is for role body and kinds figure"),
            ("other_list", "but the label 'other' is for role body and kinds text"),
        ],
    ), found
    assert [(issue.check, issue.item_id, issue.details) for issue in issues] == [
        (
            "no_matching_label",
            None,
            {"item_refs": ["aside_1", "aside_2"], "kind": "text", "role": "aside"},
        ),
        (
            "no_matching_label",
            None,
            {"item_refs": ["note"], "kind": "text", "role": "footnote"},
        ),
    ]


def test_languages_check_finds_invalid_tags_and_text_without_a_language(
    answer_item: Callable[..., AnswerItem],
    no_page_text: PageText,
    page_context: Callable[..., PageContext],
) -> None:
    """Each item with text needs a valid BCP-47 tag.

    A figure without text needs no language.
    """

    answer = _answer(
        answer_item(box=[100, 100, 900, 150], language="en", ref="english"),
        answer_item(box=[100, 160, 900, 210], language="not a tag", ref="bad_tag"),
        answer_item(box=[100, 220, 900, 270], language=None, ref="untagged"),
        answer_item(
            box=[100, 300, 900, 700],
            figure={"description": "A map of the river.", "text": None},
            kind="figure",
            label="Figure",
            language=None,
            ref="map",
            text=None,
        ),
    )

    failures = check_languages(answer, page_context(), no_page_text)

    found = _found(failures)
    assert _matches(
        found,
        [
            ("bad_tag", "has the language 'not a tag', which is not a valid BCP-47"),
            ("untagged", "item 'untagged' has text but no language"),
        ],
    ), found


@pytest.mark.parametrize(
    "case",
    [
        _ReadingOrder(
            bad_column_order="left_to_right",
            bad_column_order_words=(
                "column_order is left_to_right, but the survey found the page "
                "written left to right"
            ),
            column_order=None,
            direction="ltr",
            in_order=("left_top", "left_bottom", "right_top", "right_bottom"),
            jumps_back=(
                (
                    "left_top",
                    "starts 300 units above item 'left_bottom', which comes before "
                    "it, without a move of 200 units to the right to a new column, "
                    "for the direction the survey found",
                ),
            ),
            out_of_order=("left_bottom", "left_top", "right_top", "right_bottom"),
        ),
        _ReadingOrder(
            bad_column_order="right_to_left",
            bad_column_order_words=(
                "column_order is right_to_left, but the survey found the page "
                "written right to left"
            ),
            column_order=None,
            direction="rtl",
            in_order=("right_top", "right_bottom", "left_top", "left_bottom"),
            jumps_back=(
                (
                    "right_top",
                    "starts 300 units above item 'left_bottom', which comes before "
                    "it, without a move of 200 units to the left to a new column, "
                    "for the direction the survey found",
                ),
            ),
            out_of_order=("left_top", "left_bottom", "right_top", "right_bottom"),
        ),
        _ReadingOrder(
            bad_column_order=None,
            bad_column_order_words=(
                "the survey found the page written top to bottom, but column_order "
                "is null"
            ),
            column_order="right_to_left",
            direction="ttb",
            in_order=("upper_right", "upper_left", "lower_right", "lower_left"),
            jumps_back=(
                (
                    "upper_right",
                    "lies 200 units to the right of item 'upper_left', which comes "
                    "before it, without a move of 200 units down to a new band, for "
                    "the direction the survey found",
                ),
                (
                    "lower_right",
                    "lies 200 units to the right of item 'lower_left', which comes "
                    "before it, without a move of 200 units down to a new band, for "
                    "the direction the survey found",
                ),
            ),
            out_of_order=("upper_left", "upper_right", "lower_left", "lower_right"),
        ),
        _ReadingOrder(
            bad_column_order=None,
            bad_column_order_words=(
                "the survey found the page written top to bottom, but column_order "
                "is null"
            ),
            column_order="left_to_right",
            direction="ttb",
            in_order=("upper_left", "upper_right", "lower_left", "lower_right"),
            jumps_back=(
                (
                    "upper_left",
                    "lies 200 units to the left of item 'upper_right', which comes "
                    "before it, without a move of 200 units down to a new band, for "
                    "the direction the survey found",
                ),
                (
                    "lower_left",
                    "lies 200 units to the left of item 'lower_right', which comes "
                    "before it, without a move of 200 units down to a new band, for "
                    "the direction the survey found",
                ),
            ),
            out_of_order=("upper_right", "upper_left", "lower_right", "lower_left"),
        ),
    ],
    ids=["ltr", "rtl", "ttb-right-to-left", "ttb-left-to-right"],
)
def test_reading_order_hint_allows_new_columns_but_not_jumps_back(
    answer_item: Callable[..., AnswerItem],
    case: _ReadingOrder,
    no_page_text: PageText,
    page_context: Callable[..., PageContext],
) -> None:
    """Reading column by column agrees, and reading the columns the wrong way differs.

    A jump back against the direction the survey found agrees with it only with a
    move to the next column, or down to the next band on a page written top to
    bottom. ``column_order`` agrees when it is set on such a page and only there.
    """

    context = page_context(writing_direction=case.direction)
    in_order = _answer(
        *_items(case.in_order, answer_item=answer_item),
        column_order=case.column_order,
    )
    out_of_order = _answer(
        *_items(case.out_of_order, answer_item=answer_item),
        column_order=case.column_order,
    )
    bad_column_order = _answer(
        *_items(case.in_order, answer_item=answer_item),
        column_order=case.bad_column_order,
    )

    jumps = _found(check_reading_order(out_of_order, context, no_page_text))
    wrong = _found(check_reading_order(bad_column_order, context, no_page_text))

    assert check_reading_order(in_order, context, no_page_text) == []
    assert _matches(jumps, list(case.jumps_back)), jumps
    assert _matches(wrong, [(None, case.bad_column_order_words)]), wrong


@pytest.mark.parametrize(
    "script",
    [
        _ScriptLine(
            direction="rtl",
            language="ar",
            line="خاطئ أو يكشفون عنها.",
            name="irs_pub1_arabic.pdf",
        ),
        _ScriptLine(
            direction="ltr",
            language="zh-Hans",
            line="《纳税人权利法案》",
            name="irs_pub1_chinese_simplified.pdf",
        ),
        _ScriptLine(
            direction="ttb",
            language="ja",
            line="元号を令和に改める。",
            name="japan_official_gazette_2019_extra_9.pdf",
        ),
        _ScriptLine(
            direction="ltr",
            language="en",
            line="Future Developments",
            name="irs_w9_instructions.pdf",
        ),
    ],
    ids=["arabic", "chinese", "japanese", "english"],
)
def test_removing_a_line_is_a_dropped_text_difference(
    answer_item: Callable[..., AnswerItem],
    page_context: Callable[..., PageContext],
    pdf_path: Callable[[str], Path],
    script: _ScriptLine,
) -> None:
    """A text-layer line left out of an otherwise correct answer differs as dropped."""

    context, page_text = _read_page(
        script, page_context=page_context, pdf_path=pdf_path
    )
    correct = _correct_answer(page_text.lines, answer_item=answer_item, script=script)
    answer = _answer(
        *(item for item in correct.items if item.text != script.line),
        column_order=correct.column_order,
    )

    dropped = check_text_dropped(answer, context, page_text)

    assert page_text.lines.count(script.line) == 1
    assert check_text_dropped(correct, context, page_text) == []
    assert check_text_added(correct, context, page_text) == []
    assert [failure.details["line"] for failure in dropped] == [script.line]
    assert script.line in dropped[0].message
    assert check_text_added(answer, context, page_text) == []


def test_text_hints_are_skipped_when_the_text_layer_cannot_be_compared(
    answer_item: Callable[..., AnswerItem],
    page_context: Callable[..., PageContext],
) -> None:
    """Without a text layer that can be relied on, neither text hint differs.

    The same answer, which leaves out a line of a good text layer, differs there but
    not when the layer is measured as none or garbled, or holds only blank lines; an
    answer whose text is mostly not in a good layer finds it mismatched. The checks
    never compare text, so the retry message for an answer that both fails a check
    and leaves out the line names the check failure and quotes no stored line.
    """

    layer = PageText(
        furniture={},
        lines=(
            "Payments are due by the end of March.",
            "Late payments add a penalty of five percent.",
        ),
    )
    blank = PageText(furniture={}, lines=("   ", "* * *"))
    partial = _answer(answer_item(text="Payments are due by the end of March."))
    unrelated = _answer(answer_item(text="Bring a packed lunch on Thursday."))
    pages = [
        (partial, page_context(text_quality="good"), layer),
        (partial, page_context(text_quality="none"), layer),
        (partial, page_context(text_quality="good"), blank),
        (partial, page_context(text_quality="garbled"), layer),
        (unrelated, page_context(text_quality="good"), layer),
    ]
    dropped = check_text_dropped(partial, page_context(), layer)
    mislabeled = _answer(
        answer_item(label="Sidebar", text="Payments are due by the end of March.")
    )
    failures = run_checks(mislabeled, page_context(), layer)

    found = [
        (
            comparison_status(answer, context, page_text.lines),
            check_text_dropped(answer, context, page_text),
            check_text_added(answer, context, page_text),
        )
        for answer, context, page_text in pages
    ]
    retry = retry_message(failures)

    assert found == [
        ("compared", dropped, []),
        ("no_text_layer", [], []),
        ("no_text_layer", [], []),
        ("garbled_text_layer", [], []),
        ("text_layer_mismatch", [], []),
    ]
    assert [failure.details["line"] for failure in dropped] == [layer.lines[1]]
    assert [failure.details["line"] for failure in dropped] == [
        failure.details["line"]
        for failure in compare_with_hints(mislabeled, page_context(), layer)[
            "text_dropped"
        ]
    ]
    (labeled,) = failures["labels"]
    assert f"- {labeled.message}" in retry
    assert layer.lines[1] not in retry
    assert "text_dropped" not in retry

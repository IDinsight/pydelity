"""Tests for the HTML report written at the end of each run."""

# Standard Library
import html as html_text
import os
import re

from collections.abc import Callable
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

# Package Library
import pydelity

from pydelity.surveying.schemas import Facts
from tests.fixtures.mock_providers import MockProviders

# The survey's labels in the tests of break cards: tables and titles.
_BREAK_LABELS = [
    {
        "description": "Running text and tables.",
        "kinds": ["table", "text"],
        "name": "Body",
        "role": "body",
    },
    {
        "description": "Titles of tables.",
        "kinds": ["text"],
        "name": "Heading",
        "role": "heading",
    },
]

# The 6-page fillable test form, with form fields and two repeated lines.
_FORM = "irs_form_w9.pdf"

# HTML elements that have no end tag.
_VOID_TAGS = frozenset({"br", "hr", "img", "input", "link", "meta", "source", "wbr"})


class _Ancestry(HTMLParser):
    """Find an element by its ID, with its tag and classes and those of its parents."""

    def __init__(self, element_id: str) -> None:
        """Look for the element with this ID.

        Parameters
        ----------
        element_id
            The element's ``id``.
        """

        super().__init__()
        self._element_id = element_id
        self._open: list[tuple[str, frozenset[str]]] = []
        self.chain: list[tuple[str, frozenset[str]]] = []

    def handle_endtag(self, tag: str) -> None:
        """Close the most recent element with this tag.

        Parameters
        ----------
        tag
            The tag's name.
        """

        for index in range(len(self._open) - 1, -1, -1):
            if self._open[index][0] == tag:
                del self._open[index:]
                return

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Open an element, and keep the chain when it is the one looked for.

        Parameters
        ----------
        tag
            The tag's name.
        attrs
            Its attributes.
        """

        values = dict(attrs)
        element = (tag, frozenset((values.get("class") or "").split()))
        if values.get("id") == self._element_id:
            self.chain = [*self._open, element]
        if tag not in _VOID_TAGS:
            self._open.append(element)


@dataclass
class _Cell:
    """One cell of an HTML table, as written."""

    col_span: int
    row_span: int
    tag: str
    text: str = ""


class _Links(HTMLParser):
    """Collect the image sources, link targets and tags of an HTML page."""

    def __init__(self) -> None:
        """Start with nothing collected."""

        super().__init__()
        self.images: list[str] = []
        self.links: list[str] = []
        self.tags: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record the tag and any ``src`` or ``href`` it carries.

        Parameters
        ----------
        tag
            The tag's name.
        attrs
            Its attributes.
        """

        self.tags.add(tag)
        for name, value in attrs:
            if name == "src" and value is not None:
                self.images.append(value)
            elif name == "href" and value is not None:
                self.links.append(value)


class _TableCells(HTMLParser):
    """Collect the cells of a page's item tables, by row group and row."""

    def __init__(self) -> None:
        """Start with no cell read."""

        super().__init__()
        self._cell: _Cell | None = None
        self._in_table = False
        self.groups: list[list[list[_Cell]]] = []

    def handle_data(self, data: str) -> None:
        """Add text to the cell being read.

        Parameters
        ----------
        data
            The text.
        """

        if self._cell is not None:
            self._cell.text += data

    def handle_endtag(self, tag: str) -> None:
        """Finish a cell or an item table.

        Parameters
        ----------
        tag
            The tag's name.
        """

        if tag in {"td", "th"}:
            self._cell = None
        elif tag == "table":
            self._in_table = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Start an item table, a row group, a row or a cell.

        Parameters
        ----------
        tag
            The tag's name.
        attrs
            Its attributes.
        """

        values = dict(attrs)
        if tag == "table":
            self._in_table = "item-table" in (values.get("class") or "").split()
        elif not self._in_table:
            return
        elif tag in {"tbody", "tfoot", "thead"}:
            self.groups.append([])
        elif tag == "tr":
            if not self.groups:
                self.groups.append([])
            self.groups[-1].append([])
        elif tag in {"td", "th"}:
            self._cell = _Cell(
                col_span=int(values.get("colspan") or 1),
                row_span=int(values.get("rowspan") or 1),
                tag=tag,
            )
            self.groups[-1][-1].append(self._cell)


def _break_answers_page(title: str, rows: list[list[str]]) -> dict[str, object]:
    """Write a page answer with a title and a table, inside one shaded box.

    Parameters
    ----------
    title
        The title's text, item ``t1``.
    rows
        The table's rows of cell texts, item ``t2``, whose first row is its header.

    Returns
    -------
    dict[str, object]
        The answer, as JSON-ready data.
    """

    item: dict[str, object] = {
        "caption_of": None,
        "container": "c1",
        "entries": None,
        "field": None,
        "figure": None,
        "language": "en",
        "latex": None,
        "table": None,
        "text": None,
    }
    table = {
        "header_rows": 1,
        "rows": [
            [{"col_span": 1, "row_span": 1, "text": text} for text in row]
            for row in rows
        ],
    }
    return {
        "column_order": None,
        "containers": [
            {"box": [50, 50, 950, 950], "container": None, "label": "Body", "ref": "c1"}
        ],
        "items": [
            item
            | {
                "box": [100, 100, 900, 150],
                "kind": "text",
                "label": "Heading",
                "ref": "t1",
                "role": "heading",
                "text": title,
            },
            item
            | {
                "box": [100, 200, 900, 600],
                "kind": "table",
                "label": "Body",
                "ref": "t2",
                "role": "body",
                "table": table,
            },
        ],
    }


def _columns(groups: list[list[list[_Cell]]]) -> dict[str, int]:
    """Place each cell in its column, as HTML does.

    Cells fill each row from the left, skipping places that a cell above still
    spans. A row span ends at the end of its row group.

    Parameters
    ----------
    groups
        The table's row groups, each a list of rows of cells.

    Returns
    -------
    dict[str, int]
        Each cell's text and its first column, counted from 0.
    """

    columns = {}
    for rows in groups:
        taken: set[tuple[int, int]] = set()
        for row_number, cells in enumerate(rows):
            column = 0
            for cell in cells:
                while (row_number, column) in taken:
                    column += 1
                columns[cell.text] = column
                taken.update(
                    (row, place)
                    for row in range(row_number, row_number + cell.row_span)
                    for place in range(column, column + cell.col_span)
                )
                column += cell.col_span
    return columns


def _css_rules(stylesheet: str) -> list[tuple[str, dict[str, str]]]:
    """Read a stylesheet's rules, counting rules inside media queries as always on.

    Parameters
    ----------
    stylesheet
        The CSS.

    Returns
    -------
    list[tuple[str, dict[str, str]]]
        Each rule's selector list and its declarations by property.
    """

    text = re.sub(r"/\*.*?\*/", "", stylesheet, flags=re.DOTALL)
    # Drop each media query's wrapper and keep the rules inside it.
    text = re.sub(r"@media[^{]*\{((?:[^{}]*\{[^{}]*\})*)\s*\}", r"\1", text)
    rules = []
    for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", text):
        declarations = {
            name.strip(): value.strip()
            for name, value in (
                part.split(":", 1) for part in body.split(";") if ":" in part
            )
        }
        rules.append((" ".join(selectors.split()), declarations))
    return rules


def _matches(selector: str, chain: list[tuple[str, frozenset[str]]]) -> bool:
    """Tell whether a selector can apply to the last element of a chain.

    Only tags, classes, and the descendant and child combinators are judged;
    pseudo-classes, IDs and attribute selectors count as matching, so the answer
    errs toward a rule applying.

    Parameters
    ----------
    selector
        One selector, such as ``.items > .item:target``.
    chain
        The element's tag and classes, after those of its parents from the root.

    Returns
    -------
    bool
        Whether the selector matches.
    """

    parts = re.split(r"\s*(>)\s*|\s+", selector.strip())
    tokens = [part for part in parts if part]

    def compound_fits(compound: str, element: tuple[str, frozenset[str]]) -> bool:
        """Tell whether one compound selector fits one element."""

        bare = re.sub(r"::?[\w-]+(\([^)]*\))?|\[[^]]*\]|#[\w-]+", "", compound)
        tag = re.match(r"[a-z][\w-]*|\*", bare)
        classes = set(re.findall(r"\.([\w-]+)", bare))
        tag_fits = tag is None or tag[0] in {"*", element[0]}
        return tag_fits and classes <= element[1]

    def fits(position: int, depth: int) -> bool:
        """Match the tokens up to a position against the chain up to a depth."""

        if not compound_fits(tokens[position], chain[depth]):
            return False
        if position == 0:
            return True
        if tokens[position - 1] == ">":
            return depth > 0 and fits(position - 2, depth - 1)
        return any(fits(position - 1, above) for above in range(depth))

    return fits(len(tokens) - 1, len(chain) - 1)


def _parse(path: Path) -> _Links:
    """Parse an HTML file.

    Parameters
    ----------
    path
        The file.

    Returns
    -------
    _Links
        What it holds.
    """

    parser = _Links()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def test_a_break_card_shows_its_pieces_beside_both_pages_with_links_from_issues(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict],
) -> None:
    """A break's card draws what its verdict names and lists every verdict field.

    A table carries on with its header repeated, below a repeated title marked
    "(continued)", in a box that carries on. The verifier's verdict counts no
    repeated header row. That difference is flagged on the table's end, given in
    the card's verifier line, listed on the card, and linked to the card from the
    review section.
    """

    piece = {
        "cell_joins": None,
        "earlier_entry": None,
        "earlier_item": "p0000-002",
        "join": "append_rows",
        "later_entry": None,
        "later_item": "p0001-002",
        "markers": [
            {"cell": None, "item": "p0001-001", "row": None, "text": "(continued)"}
        ],
        "repeated_header_rows": 1,
        "repeated_items": ["p0001-001"],
        "text_join": None,
    }
    verdict = {
        "containers": [{"earlier": "p0000-c01", "later": "p0001-c01"}],
        "continues": True,
        "pieces": [piece],
        "reason": "Table 4 carries on.",
    }
    second = verdict | {"pieces": [piece | {"repeated_header_rows": 0}]}
    difference = (
        "in piece 1 (p0000-002 to p0001-002), the number of repeated header rows is "
        "1 in the kept verdict and 0 in the verifier's"
    )
    mock_providers(
        answers=[survey_answer(labels=_BREAK_LABELS)],
        break_answers={0: [verdict, second]},
        page_answers={
            0: {
                "extractor": _break_answers_page(
                    "Table 4. Results", [["Name", "Score"], ["Ana", "9"]]
                )
            },
            1: {
                "extractor": _break_answers_page(
                    "Table 4. Results (continued)", [["Name", "Score"], ["Ben", "7"]]
                )
            },
        },
    )

    pydelity.run(
        blank_pdf(2),
        advanced={"page_breaks": {"verify": True}},
        output_dir="out",
        pause=False,
    )

    html = Path("out/report.html").read_text(encoding="utf-8")
    parsed = _parse(Path("out/report.html"))
    card = html[html.index('<article class="break" id="break-0000">') :]
    card = card[: card.index("</article>")]
    assert "<h3>Pages 1 and 2</h3>" in card
    for label in ("end 1 !", "container 1", "repeat 1, marker 1", "start 1"):
        assert f'<span class="box-label">{label}</span>' in card
    for term, value in (
        ("Content continues", "yes"),
        ("Verifier", html_text.escape(f"its verdict differs in 1 place: {difference}")),
        ("Join", "append_rows"),
        ("Ends in", "p0000-002"),
        ("Starts in", "p0001-002"),
        ("Repeated header rows", "1"),
        ("Repeated items", "p0001-001"),
        ("Markers", html_text.escape('"(continued)" on p0001-001')),
    ):
        assert f"<dt>{term}</dt><dd>{value}</dd>" in card
    assert "container 1: p0000-c01 on page 1 carries on as p0001-c01 on page 2" in card
    assert html_text.escape(f"pages 1 and 2: verdicts_differ: {difference}") in card
    assert "#break-0000" in parsed.links


def test_a_break_with_an_empty_page_and_markup_in_a_verdict_show_safely(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict],
) -> None:
    """A ``no_content`` break says no request was made; a verdict's markup is shown.

    The first break's verdict quotes markup, which its card shows as text. The
    third page has no items, so the second break is judged without a request.
    """

    reason = "<script>alert(1)</script> The title <b>Notes</b> starts a new part."
    mock_providers(
        answers=[survey_answer(labels=_BREAK_LABELS)],
        break_answers={
            0: {"containers": [], "continues": False, "pieces": [], "reason": reason}
        },
        page_answers={
            0: {
                "extractor": _break_answers_page(
                    "Table 4. Results", [["Name", "Score"], ["Ana", "9"]]
                )
            },
            1: {
                "extractor": _break_answers_page(
                    "Notes", [["Name", "Note"], ["Ben", "Late"]]
                )
            },
            2: {"extractor": {"column_order": None, "containers": [], "items": []}},
        },
    )

    pydelity.run(blank_pdf(3), output_dir="out", pause=False)

    html = Path("out/report.html").read_text(encoding="utf-8")
    parsed = _parse(Path("out/report.html"))
    second = html[html.index('id="break-0001"') :]
    second = second[: second.index("</article>")]
    assert (
        "<dt>Requests</dt><dd>none, because a page of the break has no content "
        "items</dd>" in second
    )
    assert "<dt>Content continues</dt><dd>no</dd>" in second
    assert "The verdict names no items or containers on these pages." in second
    assert "Page 3 has no content items, so nothing can carry on" in second
    assert "<script>alert(1)</script>" not in html
    assert "<b>Notes</b>" not in html
    assert html_text.escape(reason) in html
    assert "script" not in parsed.tags


def test_a_header_cell_spanning_into_the_body_keeps_each_body_cell_in_its_column(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """A table's rows share one row group, so a header cell can span the body.

    The header row's first cell spans all three rows. Placed as a browser places
    them, the report's cells land in the columns the page file gives them, header
    cells as ``th`` and body cells as ``td``.
    """

    def cell(text: str, row_span: int = 1) -> dict[str, object]:
        """Write one table cell."""

        return {"col_span": 1, "row_span": row_span, "text": text}

    table = {
        "header_rows": 1,
        "rows": [
            [cell("Section", row_span=3), cell("Item"), cell("Amount")],
            [cell("b1"), cell("c1")],
            [cell("b2"), cell("c2")],
        ],
    }
    item = dict.fromkeys(
        ["caption_of", "container", "entries", "field", "figure", "latex", "text"]
    ) | {
        "box": [100, 100, 900, 400],
        "kind": "table",
        "label": "Table",
        "language": "en",
        "ref": "tab",
        "role": "body",
        "table": table,
    }
    labels = [
        {"description": "Text.", "kinds": ["text"], "name": "Body", "role": "body"},
        {"description": "Grid.", "kinds": ["table"], "name": "Table", "role": "body"},
    ]
    mock_providers(
        answers=[survey_answer(labels=labels)],
        page_answers={
            0: {
                "extractor": {
                    "column_order": None,
                    "containers": [],
                    "items": [item],
                }
            }
        },
    )

    pydelity.run(
        pdf_path("irs_form_1040a_1965_scan.pdf"),
        output_dir="out",
        pages="1",
        pause=False,
    )

    (page,) = pydelity.load("out").pages
    (saved,) = [item.table for item in page.items if item.table is not None]
    rows = [
        [
            _Cell(col_span=c.col_span, row_span=c.row_span, tag="", text=c.text or "")
            for c in row
        ]
        for row in saved.rows
    ]
    parser = _TableCells()
    parser.feed(Path("out/report.html").read_text(encoding="utf-8"))
    assert _columns([rows]) == {
        "Section": 0,
        "Item": 1,
        "Amount": 2,
        "b1": 1,
        "c1": 2,
        "b2": 1,
        "c2": 2,
    }
    assert _columns(parser.groups) == _columns([rows])
    cells = [cell for group in parser.groups for row in group for cell in row]
    assert [(cell.text, cell.tag) for cell in cells] == [
        ("Section", "th"),
        ("Item", "th"),
        ("Amount", "th"),
        ("b1", "td"),
        ("c1", "td"),
        ("b2", "td"),
        ("c2", "td"),
    ]


def test_a_page_no_verifier_reviewed_says_so_in_the_report(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
) -> None:
    """With the verifiers off, the survey's, the pages' and the break's cards say so.

    The scan has two pages and one break, so four cards say no verifier ran.
    """

    answers = canned_answers("irs_form_1040a_1965_scan.pdf")
    page_answers = answers["page_answers"]
    break_answers = answers["break_answers"]
    assert isinstance(page_answers, dict)
    assert isinstance(break_answers, dict)
    mock_providers(
        answers=answers["answers"],
        break_answers=break_answers,
        page_answers={
            index: {"extractor": by_agent["extractor"]}
            for index, by_agent in page_answers.items()
        },
    )

    pydelity.run(
        pdf_path("irs_form_1040a_1965_scan.pdf"), output_dir="out", pause=False
    )

    html = Path("out/report.html").read_text(encoding="utf-8")
    assert html.count("<dt>Verifier</dt><dd>no verifier ran</dd>") == 4


def test_item_boxes_take_only_the_box_styles_and_the_item_list_keeps_its_own(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
) -> None:
    """The item list's styles stay off the boxes drawn over the page image.

    No rule that can apply to an item's box gives it padding, which would draw a
    short item taller than its box, and the box a review issue links to is shaded
    with the see-through target color. The item's entry in the list keeps its
    padding and its own highlight.
    """

    mock_providers(**canned_answers("irs_form_1040a_1965_scan.pdf"))
    pydelity.run(
        pdf_path("irs_form_1040a_1965_scan.pdf"),
        output_dir="out",
        pages="1",
        pause=False,
    )
    html = Path("out/report.html").read_text(encoding="utf-8")
    stylesheet = html[html.index("<style>") + 7 : html.index("</style>")]
    rules = _css_rules(stylesheet)

    def applied(element_id: str) -> list[tuple[str, dict[str, str]]]:
        """List the rules with a selector that can apply to an element."""

        finder = _Ancestry(element_id)
        finder.feed(html)
        assert finder.chain, element_id
        return [
            (selectors, declarations)
            for selectors, declarations in rules
            if any(_matches(one, finder.chain) for one in selectors.split(","))
        ]

    box = applied("box-p0000-001")
    entry = applied("item-p0000-001")

    assert any(".box.item" in selectors for selectors, _ in box)
    assert [
        (selectors, name)
        for selectors, declarations in box
        for name in declarations
        if name.startswith("padding")
    ] == []
    assert [
        declarations.get("background")
        for selectors, declarations in box
        if ":target" in selectors
    ] == ["var(--target)"]
    assert any("padding-block" in declarations for _, declarations in entry)
    assert "var(--highlight)" in [
        declarations.get("background")
        for selectors, declarations in entry
        if ":target" in selectors
    ]


def test_page_images_are_rendered_only_when_missing(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
) -> None:
    """A rerun keeps the page images it has and renders only a missing one.

    The rerun reuses the survey and goes on to extract the pages.
    """

    mock_providers(**canned_answers("irs_form_1040a_1965_scan.pdf"))
    pydelity.run(pdf_path("irs_form_1040a_1965_scan.pdf"), output_dir="out")
    first, second = Path("out/report/pages/0000.jpg"), Path("out/report/pages/0001.jpg")
    os.utime(first, (1_000_000_000, 1_000_000_000))
    os.utime(second, (1_000_000_000, 1_000_000_000))
    second.unlink()

    pydelity.run(pdf_path("irs_form_1040a_1965_scan.pdf"), output_dir="out")

    assert first.stat().st_mtime == 1_000_000_000
    assert second.is_file()
    assert second.stat().st_mtime > 1_000_000_000


def test_report_draws_extracted_items_numbered_with_links_from_their_issues(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """An extracted page shows its items' numbered boxes, containers and item list.

    Each box links to the item's entry, which shows its content and, for a figure,
    the crop. A review issue about an item, here the verifier's, marks its box and
    links to it, and the page's details give the verifier's outcome.
    """

    def item(**fields: object) -> dict[str, object]:
        """Write one answer item: body text unless the fields say otherwise."""

        empty = dict.fromkeys(
            ["caption_of", "container", "entries", "field", "figure", "latex", "table"]
        )
        return (
            empty
            | {
                "kind": "text",
                "label": "Body",
                "language": "en",
                "role": "body",
                "text": None,
            }
            | fields
        )

    labels = [
        {"description": "Text.", "kinds": ["text"], "name": "Body", "role": "body"},
        {"description": "Art.", "kinds": ["figure"], "name": "Figure", "role": "body"},
        {"description": "Other.", "kinds": ["text"], "name": "other", "role": "body"},
    ]
    answer = {
        "column_order": None,
        "containers": [
            {
                "box": [50, 150, 950, 700],
                "container": None,
                "label": "Body",
                "ref": "c1",
            }
        ],
        "items": [
            item(box=[100, 50, 900, 100], ref="t1", text="<i>Income</i> & tax"),
            item(
                box=[100, 200, 900, 650],
                container="c1",
                figure={"description": "A seal.", "text": None},
                kind="figure",
                label="Figure",
                language=None,
                ref="pic",
            ),
        ],
    }
    verdict = {
        "corrected": None,
        "passed": False,
        "problems": [
            {"category": "box", "description": "The seal is larger.", "item_ref": "pic"}
        ],
    }
    mock_providers(
        answers=[survey_answer(labels=labels)],
        page_answers={0: {"extractor": answer, "verifier": verdict}},
    )

    pydelity.run(
        pdf_path("irs_form_1040a_1965_scan.pdf"),
        advanced={"extraction": {"verify": True}},
        output_dir="out",
        pages="1",
        pause=False,
    )

    report = Path("out/report.html")
    html = report.read_text(encoding="utf-8")
    parsed = _parse(report)
    assert 'class="box item" id="box-p0000-001" href="#item-p0000-001"' in html
    assert '<span class="box-label">1</span>' in html
    assert 'class="box item flagged" id="box-p0000-002" href="#item-p0000-002"' in html
    assert '<span class="box-label">2 !</span>' in html
    assert 'class="box container" id="box-p0000-c01"' in html
    assert '<li class="item" id="item-p0000-002">' in html
    assert "in container" in html
    assert "figures/p0000-002.png" in parsed.images
    assert Path("out/figures/p0000-002.png").is_file()
    assert "&lt;i&gt;Income&lt;/i&gt; &amp; tax" in html
    assert "verifier: The seal is larger." in html
    assert "#box-p0000-002" in parsed.links
    assert "found 1 problem, listed for review" in html
    assert "box-p0001-001" not in html


def test_report_escapes_text_from_the_pdf_the_user_and_the_model(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Markup in instructions and in the model's labels is shown, never run."""

    labels = [
        {
            "description": "<img src=x onerror=alert(2)>",
            "kinds": ["text"],
            "name": "<b>Bold</b>",
            "role": "body",
        }
    ]
    mock_providers(answers=[survey_answer(labels=labels)])

    pydelity.run(
        pdf_path("irs_form_1040a_1965_scan.pdf"),
        advanced={"survey": {"instructions": "<script>alert(1)</script>"}},
        output_dir="out",
    )

    html = Path("out/report.html").read_text(encoding="utf-8")
    parsed = _parse(Path("out/report.html"))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<b>Bold</b>" not in html
    assert "&lt;b&gt;Bold&lt;/b&gt;" in html
    assert "x" not in parsed.images
    assert "script" not in parsed.tags


def test_report_shows_every_page_with_findings_and_needs_no_network(
    facts_of: Callable[[str], Facts],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """The report shows each page with its boxes, plus the profile, cost and issues.

    It has no script and no outside address, so it opens from disk offline.
    """

    region = {
        "bbox": {"x0": 0.05, "x1": 0.95, "y0": 0.1, "y1": 0.3},
        "label": "Body",
        "note": "Name and address lines.",
        "page_index": 0,
    }
    answer = survey_answer(facts_of(_FORM), languages=["en", "zz"], regions=[region])
    mock_providers(answers=[answer])

    result = pydelity.run(
        pdf_path(_FORM), advanced={"survey": {"check_retries": 0}}, output_dir="out"
    )

    report = Path("out/report.html")
    html = report.read_text(encoding="utf-8")
    parsed = _parse(report)
    assert "script" not in parsed.tags
    assert not [
        target
        for target in parsed.images + parsed.links
        if target.startswith(("http:", "https:", "//"))
    ]
    assert parsed.images == [f"report/pages/{index:04d}.jpg" for index in range(6)]
    for image in parsed.images:
        assert (Path("out") / image).is_file()
    assert '<div class="box region"' in html
    assert '<span class="box-label">Body</span>' in html
    assert html.count('<div class="box field"') == 23
    assert result.record is not None
    (issue,) = result.record.review
    assert html_text.escape(issue.message) in html
    assert "$0.02" in html
    assert result.survey is not None
    for label in result.survey.profile.labels:
        assert html_text.escape(label.name) in html
    assert result.facts is not None
    for line in result.facts.summary:
        assert html_text.escape(line) in html

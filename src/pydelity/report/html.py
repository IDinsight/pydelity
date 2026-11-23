"""``report.html``, the page that shows a run's results.

It shows the run, its cost and review issues, the profile, the facts, the pages and
the page breaks. Each extracted page shows its items and containers drawn over the
page image, beside a list of its items. Other pages show the survey's regions and the
form fields. Each page break shows its two pages with the items and containers its
verdict names drawn over them, and the verdict below. It is static HTML with its
stylesheet inlined, so it runs no JavaScript and loads nothing from elsewhere. Every
string taken from the PDF, the settings or the model is HTML-escaped.
"""

# Standard Library
import html
import re

from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

# Package Library
from pydelity.costs.budget import format_usd
from pydelity.extracting.schemas import (
    Container,
    Entry,
    FieldContent,
    Figure,
    Item,
    PageFile,
    PageVerification,
    Table,
    TableCell,
)
from pydelity.pipeline.schemas import RunRecord
from pydelity.report.schemas import PageImage, ReportManifest
from pydelity.review import ReviewIssue
from pydelity.surveying.schemas import (
    Facts,
    ItemKind,
    PageFacts,
    PdfFacts,
    PdfSurvey,
    SurveyVerification,
)
from pydelity.surveying.validators import covering_range
from pydelity.utils.files import write_text_atomic
from pydelity.verifying.schemas import (
    BreakFile,
    BreakVerdict,
    BreakVerification,
    ContinuationMarker,
    ContinuingPiece,
)

# Page-break verification's name in the review issues.
_BREAKS_STEP = "page_breaks"

# Each step's heading in the review section, by the step's name in the review issues.
_STEP_TITLES = {
    _BREAKS_STEP: "Page-break verification",
    "extraction": "Page extraction",
    "survey": "Survey",
}

# What a page file's text comparison status means, for the page's findings.
_TEXT_COMPARISON = {
    "compared": "yes",
    "garbled_text_layer": "no, the stored text is garbled",
    "no_text_layer": "no, the page has no stored text",
    "text_layer_mismatch": "no, the stored text shares too little with the items' text",
}

# The report's file name in the output folder.
REPORT_FILE_NAME = "report.html"


class _Html(str):
    """Markup built in this module, which `_table` puts in a cell as it is."""

    __slots__ = ()


def _box(*, bbox: Sequence[float], kind: str, label: str, page: PageFacts) -> str:
    """Draw a survey region or a form field over a page image.

    Parameters
    ----------
    bbox
        The box in points on the displayed page, as ``(x0, y0, x1, y1)``.
    kind
        ``region`` or ``field``, which sets the box's style.
    label
        The text shown in the box.
    page
        The page's facts, for its size.

    Returns
    -------
    str
        The box's HTML.
    """

    style = _box_style(bbox, height_pt=page.height_pt, width_pt=page.width_pt)
    return (
        f'<div class="box {kind}" style="{style}">'
        f'<span class="box-label">{_escape(label)}</span></div>'
    )


def _box_style(bbox: Sequence[float], *, height_pt: float, width_pt: float) -> str:
    """Position a box over a page image, in percent of the page.

    Parameters
    ----------
    bbox
        The box in points on the displayed page, as ``(x0, y0, x1, y1)``.
    height_pt
        The displayed page's height in points.
    width_pt
        The displayed page's width in points.

    Returns
    -------
    str
        The box's ``style`` attribute, kept on the page.

    Examples
    --------
    >>> _box_style([61.2, 79.2, 306.0, 396.0], height_pt=792.0, width_pt=612.0)
    'left:10.00%;top:10.00%;width:40.00%;height:40.00%'
    """

    def percent(value: float, size: float) -> float:
        """Turn a coordinate into a percentage of the page, kept on the page."""

        return min(max(value / size * 100, 0), 100)

    left = percent(bbox[0], width_pt)
    top = percent(bbox[1], height_pt)
    width = percent(bbox[2], width_pt) - left
    height = percent(bbox[3], height_pt) - top
    return f"left:{left:.2f}%;top:{top:.2f}%;width:{width:.2f}%;height:{height:.2f}%"


def _break_anchor(earlier_page_index: int) -> str:
    """Name a break's card, for the links to it.

    Parameters
    ----------
    earlier_page_index
        The page before the break.

    Returns
    -------
    str
        The card's ID.

    Examples
    --------
    >>> _break_anchor(3)
    'break-0003'
    """

    return f"break-{earlier_page_index:04d}"


def _break_card(
    break_file: BreakFile,
    *,
    images: dict[int, PageImage],
    pages: dict[int, PageFile],
) -> str:
    """Show a break's two pages with what its verdict names, then the verdict.

    Parameters
    ----------
    break_file
        The break's verdict file.
    images
        The page images by page index, with both of the break's pages.
    pages
        The page files the verdict was judged from, by page index, with both of the
        break's pages.

    Returns
    -------
    str
        An ``article`` element, with the anchor the break's review issues link to.
    """

    verdict = break_file.verdict
    earlier, later = break_file.earlier_page_index, break_file.later_page_index
    flagged = {issue.item_id for issue in break_file.issues if issue.item_id}
    earlier_labels, later_labels = _break_labels(verdict)
    figures = _break_page(
        pages[earlier], flagged=flagged, image=images[earlier], labels=earlier_labels
    ) + _break_page(
        pages[later], flagged=flagged, image=images[later], labels=later_labels
    )
    pieces = "".join(
        _piece_entry(piece, number=number)
        for number, piece in enumerate(verdict.pieces, start=1)
    )
    containers = [
        f"container {number}: {container.earlier} on page {earlier + 1} carries on "
        f"as {container.later} on page {later + 1}"
        for number, container in enumerate(verdict.containers, start=1)
    ]
    issues = (
        "<h4>Review issues</h4>" + _list([issue.message for issue in break_file.issues])
        if break_file.issues
        else ""
    )
    details = (
        f"{_definitions(_break_findings(break_file))}<h4>Pieces</h4>"
        + (f'<ol class="pieces">{pieces}</ol>' if pieces else "<p>None.</p>")
        + f"<h4>Containers</h4>{_list(containers)}<h4>Reason</h4>"
        f'<p class="item-text" dir="auto">{_escape(verdict.reason)}</p>{issues}'
    )
    caption = (
        "Boxes show where each piece ends and starts, the items that repeat it or mark "
        "it as continued, and the containers that carry on. Solid boxes are items and "
        "dotted boxes containers. A box marked ! has review issues."
        if verdict.pieces or verdict.containers
        else "The verdict names no items or containers on these pages."
    )
    return (
        f'<article class="break" id="{_break_anchor(earlier)}">'
        f"<h3>Pages {earlier + 1} and {later + 1}</h3>"
        f'<figure><div class="break-pages">{figures}</div>'
        f"<figcaption>{caption}</figcaption></figure>"
        f'<div class="break-details">{details}</div></article>'
    )


def _break_findings(break_file: BreakFile) -> list[tuple[str, str]]:
    """List whether content carries on across a break and how its verdict was made.

    Parameters
    ----------
    break_file
        The break's verdict file.

    Returns
    -------
    list[tuple[str, str]]
        Each finding's name and value.
    """

    findings = [("Content continues", "yes" if break_file.verdict.continues else "no")]
    if break_file.judgment == "no_content":
        findings.append(
            ("Requests", "none, because a page of the break has no content items")
        )
    else:
        findings.append(("Verifier", _verifier_text(break_file.verification)))
    return findings


def _break_labels(
    verdict: BreakVerdict,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Name what a verdict marks on each page of its break, by item or container ID.

    Parameters
    ----------
    verdict
        The verdict.

    Returns
    -------
    tuple[dict[str, list[str]], dict[str, list[str]]]
        The labels on the earlier page and on the later page, such as
        ``{"p0001-001": ["start 1", "marker 1"]}``. Pieces and containers are
        numbered from 1 in the verdict's order.

    Examples
    --------
    >>> from pydelity.verifying.schemas import ContinuingContainer
    >>> verdict = BreakVerdict(
    ...     containers=[ContinuingContainer(earlier="p0000-c01", later="p0001-c01")],
    ...     continues=True,
    ...     pieces=[
    ...         ContinuingPiece(
    ...             cell_joins=None,
    ...             earlier_entry=None,
    ...             earlier_item="p0000-009",
    ...             join="continue_text",
    ...             later_entry=None,
    ...             later_item="p0001-002",
    ...             markers=[],
    ...             repeated_header_rows=None,
    ...             repeated_items=["p0001-001"],
    ...             text_join="space",
    ...         )
    ...     ],
    ...     reason="The sentence carries on.",
    ... )
    >>> earlier, later = _break_labels(verdict)
    >>> earlier
    {'p0000-009': ['end 1'], 'p0000-c01': ['container 1']}
    >>> later
    {'p0001-002': ['start 1'], 'p0001-001': ['repeat 1'], 'p0001-c01': ['container 1']}
    """

    earlier: defaultdict[str, list[str]] = defaultdict(list)
    later: defaultdict[str, list[str]] = defaultdict(list)
    for number, piece in enumerate(verdict.pieces, start=1):
        earlier[piece.earlier_item].append(f"end {number}")
        later[piece.later_item].append(f"start {number}")
        for item_id in piece.repeated_items:
            later[item_id].append(f"repeat {number}")
        for marker in piece.markers:
            later[marker.item].append(f"marker {number}")
    for number, container in enumerate(verdict.containers, start=1):
        earlier[container.earlier].append(f"container {number}")
        later[container.later].append(f"container {number}")
    return dict(earlier), dict(later)


def _break_page(
    page_file: PageFile,
    *,
    flagged: set[str],
    image: PageImage,
    labels: dict[str, list[str]],
) -> str:
    """Show one page of a break, with the items and containers its verdict names.

    Parameters
    ----------
    page_file
        The page file the verdict was judged from.
    flagged
        The IDs the break's review issues name, whose boxes are marked.
    image
        The page's image.
    labels
        What the verdict names each item or container on this page for, by its ID.
        An ID the page does not have gets no box.

    Returns
    -------
    str
        A ``figure`` element.
    """

    boxes = []
    for shape in [*page_file.containers, *page_file.items]:
        if shape.id not in labels:
            continue
        style = _box_style(
            shape.bbox, height_pt=page_file.height_pt, width_pt=page_file.width_pt
        )
        kind = "container" if isinstance(shape, Container) else "item"
        flag, mark = (" flagged", " !") if shape.id in flagged else ("", "")
        label = ", ".join(dict.fromkeys(labels[shape.id]))
        boxes.append(
            f'<div class="box {kind}{flag}" style="{style}">'
            f'<span class="box-label">{_escape(label)}{mark}</span></div>'
        )
    heading = _page_heading(page_file.page_index)
    return (
        f'<figure><div class="page-image"><img src="{_escape(image.file)}" '
        f'alt="{heading} as displayed" width="{image.width_px}" '
        f'height="{image.height_px}">{"".join(boxes)}</div>'
        f"<figcaption>{heading}</figcaption></figure>"
    )


def _breaks_section(
    breaks: list[BreakFile],
    *,
    manifest: ReportManifest,
    pages: dict[int, PageFile],
) -> str:
    """Show every verdict as a card, in break order.

    Parameters
    ----------
    breaks
        The verdicts, in break order.
    manifest
        The page images.
    pages
        The page files the verdicts were judged from, by page index.

    Returns
    -------
    str
        The section's HTML, or nothing when there are no verdicts.
    """

    if not breaks:
        return ""
    images = {image.index: image for image in manifest.pages}
    shown = images.keys() & pages.keys()
    cards = [
        _break_card(break_file, images=images, pages=pages)
        for break_file in breaks
        if {break_file.earlier_page_index, break_file.later_page_index} <= shown
    ]
    return _section("page-breaks", "Page breaks", "".join(cards))


def _container_box(container: Container, *, flagged: bool, page_file: PageFile) -> str:
    """Draw a container over its page image, named by its number on the page.

    Parameters
    ----------
    container
        The container.
    flagged
        Whether a review issue names the container, which marks its box.
    page_file
        The container's page file, for the page's size.

    Returns
    -------
    str
        The box's HTML, with an anchor that review issues link to.
    """

    style = _box_style(
        container.bbox, height_pt=page_file.height_pt, width_pt=page_file.width_pt
    )
    number = container.id.rsplit("-", 1)[-1]
    flag = " flagged" if flagged else ""
    mark = " !" if flagged else ""
    return (
        f'<div class="box container{flag}" id="box-{_escape(container.id)}" '
        f'style="{style}"><span class="box-label">{_escape(number)}{mark}</span></div>'
    )


def _cost_section(record: RunRecord) -> str:
    """Show what the run cost, by step, and what the output folder has spent.

    Parameters
    ----------
    record
        The run's record.

    Returns
    -------
    str
        The section's HTML.
    """

    cost = record.cost
    rows = [
        [step.name, step.status, str(step.requests), format_usd(step.cost_usd)]
        for step in record.steps
    ]
    lines = [
        ("This run", format_usd(cost.run_usd)),
        ("Output folder, every run", format_usd(cost.output_folder_usd)),
    ]
    if cost.unpriced_requests:
        lines.append(("Requests without a known price", str(cost.unpriced_requests)))
    return _section(
        "cost",
        "Cost",
        _table(
            caption="Steps of this run",
            headers=["Step", "Status", "Requests", "Cost"],
            rows=rows,
        )
        + _definitions(lines),
    )


def _definitions(items: list[tuple[str, str]]) -> str:
    """List terms and their values.

    Parameters
    ----------
    items
        Each term and its value, as plain text.

    Returns
    -------
    str
        A ``dl`` element.
    """

    body = "".join(
        f"<dt>{_escape(term)}</dt><dd>{_escape(value)}</dd>" for term, value in items
    )
    return f"<dl>{body}</dl>"


def _entries_list(entries: list[Entry], *, attributes: str) -> str:
    """Show a list item's entries, each with its printed marker and its nesting.

    Parameters
    ----------
    entries
        The entries, in reading order.
    attributes
        The direction and language attributes for the list.

    Returns
    -------
    str
        A ``ul`` element.
    """

    rows = "".join(
        f'<li style="--level:{entry.level}">'
        + (
            f'<span class="marker">{_escape(entry.marker)}</span> '
            if entry.marker
            else ""
        )
        + f"{_escape(entry.text)}</li>"
        for entry in entries
    )
    return f'<ul class="entries"{attributes}>{rows}</ul>'


def _escape(value: object) -> str:
    """Escape text for HTML, quotes included.

    Parameters
    ----------
    value
        The value, written as text.

    Returns
    -------
    str
        The escaped text.
    """

    return html.escape(str(value), quote=True)


def _extracted_page_card(
    page_file: PageFile,
    *,
    findings: list[tuple[str, str]],
    image: PageImage,
    issues: list[ReviewIssue],
) -> str:
    """Show an extracted page: its items drawn over its image, beside the item list.

    Parameters
    ----------
    page_file
        The page's page file.
    findings
        What was measured and found on the page.
    image
        The page's image.
    issues
        The review issues on this page, from the survey and page extraction.

    Returns
    -------
    str
        An ``article`` element.
    """

    by_item: defaultdict[str, list[ReviewIssue]] = defaultdict(list)
    for issue in issues:
        if issue.item_id is not None:
            by_item[issue.item_id].append(issue)
    boxes = [
        _container_box(container, flagged=container.id in by_item, page_file=page_file)
        for container in page_file.containers
    ] + [
        _item_box(item, flagged=item.id in by_item, number=number, page_file=page_file)
        for number, item in enumerate(page_file.items, start=1)
    ]
    heading = _page_heading(page_file.page_index)
    figure = (
        f'<figure><div class="page-image"><img src="{_escape(image.file)}" '
        f'alt="{heading} as displayed" width="{image.width_px}" '
        f'height="{image.height_px}">{"".join(boxes)}</div>'
        "<figcaption>Numbered boxes show the items in reading order, where the model "
        "placed them. Dotted boxes show the containers. A box marked ! has review "
        "issues. Select a box to go to its item.</figcaption></figure>"
    )
    entries = "".join(
        _item_entry(item, issues=by_item.get(item.id, [])) for item in page_file.items
    )
    items = f'<ol class="items">{entries}</ol>' if entries else "<p>None.</p>"
    item_ids = {item.id for item in page_file.items}
    others = [issue for issue in issues if issue.item_id not in item_ids]
    other_list = (
        "<h4>Review issues about the page</h4>" + _issue_list(others) if others else ""
    )
    details = f"{_definitions(findings)}<h4>Items</h4>{items}{other_list}"
    return (
        f'<article class="page" id="page-{page_file.page_index}"><h3>{heading}</h3>'
        f'<div class="page-layout">{figure}<div class="page-details">{details}</div>'
        "</div></article>"
    )


def _extraction_findings(page_file: PageFile) -> list[tuple[str, str]]:
    """List what page extraction found on a page.

    Parameters
    ----------
    page_file
        The page's page file.

    Returns
    -------
    list[tuple[str, str]]
        Each finding's name and value.
    """

    findings = [
        ("Items", str(len(page_file.items))),
        ("Containers", str(len(page_file.containers))),
        ("Verifier", _verifier_text(page_file.verification)),
        (
            "Text compared with the stored text",
            _TEXT_COMPARISON.get(page_file.text_comparison, page_file.text_comparison),
        ),
    ]
    if page_file.column_order is not None:
        findings.append(("Column order", page_file.column_order.replace("_", " ")))
    return findings


def _facts_section(
    facts: Facts, *, summary: list[str], survey: PdfSurvey | None
) -> str:
    """Show the measured facts: the summary lines first, then the details.

    Parameters
    ----------
    facts
        The measured facts.
    summary
        The facts summary lines from ``pdf_facts.json``.
    survey
        The survey, if any, for which repeated lines are artifacts.

    Returns
    -------
    str
        The section's HTML.
    """

    parts = [_list(summary)]
    if facts.bookmarks:
        parts.append(
            _table(
                caption="Bookmarks",
                headers=["Level", "Title", "Page"],
                rows=[
                    [str(mark.level), mark.title, _page_text(mark.page_index)]
                    for mark in facts.bookmarks
                ],
            )
        )
    if facts.form_fields:
        parts.append(
            _table(
                caption="Form fields",
                headers=["Page", "Name", "Type", "Value"],
                rows=[
                    [str(field.page_index), field.name, field.type, field.value or ""]
                    for field in facts.form_fields
                ],
            )
        )
    if facts.structure is not None:
        parts.append(_definitions([("Structure tags", facts.structure.quality)]))
    if facts.repeated_lines:
        parts.append(_repeated_lines_table(facts, survey=survey))
    return _section("facts", "Measured facts", "".join(parts))


def _field_content(field: FieldContent) -> str:
    """Show a form field's type, prompt and value.

    Parameters
    ----------
    field
        The field's content.

    Returns
    -------
    str
        A ``dl`` element.
    """

    lines = [("Field type", str(field.field_type))]
    if field.prompt is not None:
        lines.append(("Prompt", field.prompt))
    if field.checked is not None:
        lines.append(("Marked", "yes" if field.checked else "no"))
    if field.value is not None or field.checked is None:
        lines.append(("Value", "empty" if field.value is None else field.value))
    if field.options:
        lines.append(("Options", ", ".join(field.options)))
    if field.fillable_name is not None:
        lines.append(("Fillable field", field.fillable_name))
    return _definitions(lines)


def _figure_content(figure: Figure) -> str:
    """Show a figure's crop, its description and any text inside it.

    Parameters
    ----------
    figure
        The figure's content.

    Returns
    -------
    str
        The figure's HTML.
    """

    text = (
        f'<p class="item-text" dir="auto">{_escape(figure.text)}</p>'
        if figure.text
        else ""
    )
    return (
        f'<img class="crop" src="{_escape(figure.crop)}" '
        f'alt="{_escape(figure.description)}" loading="lazy">'
        f'<p dir="auto">{_escape(figure.description)}</p>{text}'
    )


def _issue_list(issues: list[ReviewIssue]) -> str:
    """List review issues, each linked to the box it names when it names one.

    Parameters
    ----------
    issues
        The issues.

    Returns
    -------
    str
        A ``ul`` element.
    """

    rows = "".join(
        f"<li>{_escape(issue.message)}"
        + (f" ({_item_link(issue.item_id)})" if issue.item_id is not None else "")
        + "</li>"
        for issue in issues
    )
    return f"<ul>{rows}</ul>"


def _item_box(item: Item, *, flagged: bool, number: int, page_file: PageFile) -> str:
    """Draw an item's box over its page image, numbered in reading order.

    Parameters
    ----------
    item
        The item.
    flagged
        Whether a review issue names the item, which marks its box.
    number
        The item's position in reading order, from 1.
    page_file
        The item's page file, for the page's size.

    Returns
    -------
    str
        A link to the item's entry in the item list, drawn as the box, with an
        anchor that review issues link to.
    """

    style = _box_style(
        item.bbox, height_pt=page_file.height_pt, width_pt=page_file.width_pt
    )
    flag = " flagged" if flagged else ""
    mark = " !" if flagged else ""
    item_id = _escape(item.id)
    return (
        f'<a class="box item{flag}" id="box-{item_id}" href="#item-{item_id}" '
        f'style="{style}" aria-label="Item {number}, {item_id}">'
        f'<span class="box-label">{number}{mark}</span></a>'
    )


def _item_content(item: Item) -> str:
    """Show an item's content: its text, entries, table, field or figure.

    Parameters
    ----------
    item
        The item.

    Returns
    -------
    str
        The content's HTML, with the item's language and its own writing direction
        on text from the page.
    """

    language = "" if item.language is None else f' lang="{_escape(item.language)}"'
    attributes = f' dir="auto"{language}'
    parts: list[str] = []
    if item.text is not None and item.kind == ItemKind.CODE:
        parts.append(f"<pre{attributes}><code>{_escape(item.text)}</code></pre>")
    elif item.text is not None:
        parts.append(f'<p class="item-text"{attributes}>{_escape(item.text)}</p>')
    if item.latex is not None:
        parts.append(f'<p><code dir="ltr">{_escape(item.latex)}</code></p>')
    if item.entries:
        parts.append(_entries_list(item.entries, attributes=attributes))
    if item.table is not None:
        parts.append(_item_table(item.table, attributes=attributes))
    if item.field is not None:
        parts.append(_field_content(item.field))
    if item.figure is not None:
        parts.append(_figure_content(item.figure))
    return "".join(parts)


def _item_entry(item: Item, *, issues: list[ReviewIssue]) -> str:
    """Show one item in the page's item list.

    Parameters
    ----------
    item
        The item.
    issues
        The review issues that name the item.

    Returns
    -------
    str
        An ``li`` element, with an anchor that the item's box links to.
    """

    item_id = _escape(item.id)
    about = [str(item.kind), str(item.role), item.label]
    if item.language is not None:
        about.append(item.language)
    meta = f'<a href="#box-{item_id}">{item_id}</a>, {_escape(", ".join(about))}'
    if item.container is not None:
        meta += f", in container {_item_link(item.container)}"
    if item.caption_of is not None:
        meta += f", caption of {_item_link(item.caption_of)}"
    flags = (
        '<div class="item-issues"><p>Review issues:</p>'
        + _list([issue.message for issue in issues])
        + "</div>"
        if issues
        else ""
    )
    return (
        f'<li class="item" id="item-{item_id}"><p class="item-meta">{meta}</p>'
        f"{_item_content(item)}{flags}</li>"
    )


def _item_link(item_id: str) -> str:
    """Link to the box of an item or container.

    Parameters
    ----------
    item_id
        The item's or container's ID.

    Returns
    -------
    str
        An ``a`` element showing the ID.
    """

    escaped = _escape(item_id)
    return f'<a class="ref" href="#box-{escaped}">{escaped}</a>'


def _item_table(table: Table, *, attributes: str) -> str:
    """Show a table item as an HTML table, with its spans and header rows.

    Every row goes in one row group, with header-row cells as ``th``. HTML ends a
    cell's row span at the end of its row group, so a header cell that spans into
    the body would otherwise stop short and push the body's cells into the wrong
    columns.

    Parameters
    ----------
    table
        The table's content.
    attributes
        The direction and language attributes for the table.

    Returns
    -------
    str
        A ``table`` element.
    """

    def cell_html(cell: TableCell, *, header: bool) -> str:
        """Write one cell, with its spans."""

        tag = "th" if header else "td"
        spans = (f' colspan="{cell.col_span}"' if cell.col_span > 1 else "") + (
            f' rowspan="{cell.row_span}"' if cell.row_span > 1 else ""
        )
        scope = ' scope="col"' if header else ""
        return f"<{tag}{scope}{spans}>{_escape(cell.text or '')}</{tag}>"

    rows = [
        "<tr>"
        + "".join(cell_html(cell, header=number < table.header_rows) for cell in row)
        + "</tr>"
        for number, row in enumerate(table.rows)
    ]
    return (
        f'<table class="item-table"{attributes}><tbody>{"".join(rows)}</tbody></table>'
    )


def _list(items: list[str]) -> str:
    """List plain-text items.

    Parameters
    ----------
    items
        The items.

    Returns
    -------
    str
        A ``ul`` element, or a paragraph saying there are none.
    """

    if not items:
        return "<p>None.</p>"
    return "<ul>" + "".join(f"<li>{_escape(item)}</li>" for item in items) + "</ul>"


def _marker_text(marker: ContinuationMarker) -> str:
    """Describe a continuation marker and where it is printed.

    Parameters
    ----------
    marker
        The marker.

    Returns
    -------
    str
        Such as ``"cont." on p0004-001`` or ``"(continued)" on row 0 of p0004-002``.

    Examples
    --------
    >>> _marker_text(
    ...     ContinuationMarker(cell=2, item="p0004-002", row=0, text="(continued)")
    ... )
    '"(continued)" on row 0, cell 2 of p0004-002'
    """

    place = marker.item
    if marker.row is not None:
        cell = "" if marker.cell is None else f", cell {marker.cell}"
        place = f"row {marker.row}{cell} of {marker.item}"
    return f'"{marker.text}" on {place}'


def _page_card(
    page: PageFacts,
    *,
    facts: Facts,
    image: PageImage,
    issues: list[ReviewIssue],
    survey: PdfSurvey | None,
) -> str:
    """Show a page with no page file: its image with the survey's boxes drawn over it.

    Parameters
    ----------
    page
        The page's facts.
    facts
        All the measured facts, for the form fields and repeated lines.
    image
        The page's image.
    issues
        The review issues on this page.
    survey
        The survey, if any, for the regions and the rotation.

    Returns
    -------
    str
        An ``article`` element.
    """

    regions = [] if survey is None else survey.proposal.regions
    boxes = [
        _box(bbox=region.bbox, kind="region", label=region.label, page=page)
        for region in regions
        if region.page_index == page.index
    ] + [
        _box(bbox=field.bbox, kind="field", label=_short_name(field.name), page=page)
        for field in facts.form_fields or []
        if field.page_index == page.index
    ]
    heading = _page_heading(page.index)
    figure = (
        f'<figure><div class="page-image"><img src="{_escape(image.file)}" '
        f'alt="{heading} as displayed" width="{image.width_px}" '
        f'height="{image.height_px}">{"".join(boxes)}</div>'
        "<figcaption>Solid boxes show the survey's regions where the model placed "
        "them, which can be off. Dashed boxes show the form fields, measured from the "
        "PDF.</figcaption></figure>"
    )
    findings = _definitions(_page_findings(page, facts=facts, survey=survey))
    issue_list = (
        "<h4>Review issues</h4>" + _list([issue.message for issue in issues])
        if issues
        else ""
    )
    return (
        f'<article class="page" id="page-{page.index}"><h3>{heading}</h3>'
        f"{figure}{findings}{issue_list}</article>"
    )


def _page_findings(
    page: PageFacts, *, facts: Facts, survey: PdfSurvey | None
) -> list[tuple[str, str]]:
    """List what was measured on a page and how the survey treats it.

    Parameters
    ----------
    page
        The page's facts.
    facts
        All the measured facts, for the repeated lines and the page count.
    survey
        The survey, if any, for the rotation and the regions.

    Returns
    -------
    list[tuple[str, str]]
        Each finding's name and value.
    """

    orientation = page.orientation
    angle = "unknown" if orientation.dominant is None else f"{orientation.dominant}"
    sureness = "measured with confidence" if orientation.confident else "uncertain"
    findings = [
        ("Text layer", f"{page.text.quality}, {page.text.chars:,} characters"),
        ("Text angle", f"{angle} degrees counterclockwise ({sureness})"),
        ("Writing direction", page.direction.inline),
        (
            "Printed page number",
            page.printed_number.text if page.printed_number else "none found",
        ),
    ]
    if survey is not None:
        turn = covering_range(
            survey.profile.rotation,
            page_count=len(facts.pages),
            page_index=page.index,
        )
        degrees = 0 if turn is None else turn.degrees
        findings.append(("Rotation to make it upright", f"{degrees} degrees clockwise"))
        labels = [
            r.label for r in survey.proposal.regions if r.page_index == page.index
        ]
        findings.append(("Regions", ", ".join(labels) or "none"))
    repeated = [line.id for line in facts.repeated_lines if page.index in line.pages]
    findings.append(("Repeated lines", ", ".join(repeated) or "none"))
    return findings


def _page_heading(index: int) -> str:
    """Name a page by its number and its index.

    Parameters
    ----------
    index
        The page's index.

    Returns
    -------
    str
        The page's name.

    Examples
    --------
    >>> _page_heading(0)
    'Page 1 (index 0)'
    """

    return f"Page {index + 1} (index {index})"


def _page_text(index: int | None) -> str:
    """Write a page index, or a dash when there is none.

    Parameters
    ----------
    index
        The page index.

    Returns
    -------
    str
        The index, or ``-``.
    """

    return "-" if index is None else str(index)


def _pages_section(
    *,
    facts: Facts,
    manifest: ReportManifest,
    pages: list[PageFile],
    review: list[ReviewIssue],
    survey: PdfSurvey | None,
) -> str:
    """Show every page as a card, with its items when it was extracted.

    Parameters
    ----------
    facts
        The measured facts.
    manifest
        The page images.
    pages
        The page files of the selected pages.
    review
        The run's review issues. A break's issues go on its own card, not on its
        pages' cards.
    survey
        The survey, if any.

    Returns
    -------
    str
        The section's HTML.
    """

    images = {image.index: image for image in manifest.pages}
    extracted = {page_file.page_index: page_file for page_file in pages}
    cards = []
    for page in facts.pages:
        if page.index not in images:
            continue
        issues = [
            issue
            for issue in review
            if issue.page_index == page.index and issue.step != _BREAKS_STEP
        ]
        page_file = extracted.get(page.index)
        if page_file is None:
            cards.append(
                _page_card(
                    page,
                    facts=facts,
                    image=images[page.index],
                    issues=issues,
                    survey=survey,
                )
            )
            continue
        findings = _page_findings(page, facts=facts, survey=survey)
        cards.append(
            _extracted_page_card(
                page_file,
                findings=findings + _extraction_findings(page_file),
                image=images[page.index],
                issues=issues,
            )
        )
    return _section("pages", "Pages", "".join(cards))


def _piece_entry(piece: ContinuingPiece, *, number: int) -> str:
    """Show one piece of a verdict: where it ends and starts, and how it joins.

    Parameters
    ----------
    piece
        The piece.
    number
        The piece's position in the verdict, from 1, which its boxes are labeled
        with.

    Returns
    -------
    str
        An ``li`` element.
    """

    def place(item_id: str, entry_id: str | None) -> str:
        """Name an item, and the entry in it when there is one."""

        return item_id if entry_id is None else f"{item_id}, entry {entry_id}"

    lines = [
        ("Join", str(piece.join)),
        ("Ends in", place(piece.earlier_item, piece.earlier_entry)),
        ("Starts in", place(piece.later_item, piece.later_entry)),
    ]
    if piece.text_join is not None:
        lines.append(("Text join", str(piece.text_join)))
    if piece.cell_joins is not None:
        joins = ", ".join(str(join or "none") for join in piece.cell_joins)
        lines.append(("Cell joins", joins or "none"))
    if piece.repeated_header_rows is not None:
        lines.append(("Repeated header rows", str(piece.repeated_header_rows)))
    lines += [
        ("Repeated items", ", ".join(piece.repeated_items) or "none"),
        ("Markers", "; ".join(map(_marker_text, piece.markers)) or "none"),
    ]
    return f"<li><h5>Piece {number}</h5>{_definitions(lines)}</li>"


def _profile_section(survey: PdfSurvey) -> str:
    """Show the profile later steps rely on.

    Parameters
    ----------
    survey
        The survey.

    Returns
    -------
    str
        The section's HTML.
    """

    profile = survey.profile
    labels = _table(
        caption="Labels",
        headers=["Name", "Role", "Kinds", "Description"],
        rows=[
            [label.name, label.role, ", ".join(label.kinds), label.description]
            for label in profile.labels
        ],
    )
    direction = profile.writing_direction
    ranges = [
        f"pages {r.first_page_index}-{r.last_page_index}: {r.direction}"
        for r in direction.ranges
    ]
    details = _definitions(
        [
            ("Languages", ", ".join(profile.languages) or "none"),
            ("Writing direction", ", ".join([f"default {direction.default}", *ranges])),
            (
                "Rotation",
                ", ".join(
                    f"pages {r.first_page_index}-{r.last_page_index}: {r.degrees} "
                    "degrees clockwise"
                    for r in profile.rotation
                )
                or "none",
            ),
            (
                "Page numbering",
                ", ".join(
                    f"pages {r.first_page_index}-{r.last_page_index}: {r.style}, "
                    f"offset {r.offset}"
                    for r in profile.page_numbering
                )
                or "none",
            ),
            ("Your survey instructions", survey.inputs.instructions or "none"),
            ("Verifier", _verifier_text(survey.verification)),
        ]
    )
    notes = "<h3>Continuation notes</h3>" + _list(profile.continuation_notes)
    markers = "<h3>Start markers</h3>" + _list(
        [f"{marker.text}: {marker.description}" for marker in profile.start_markers]
    )
    other = "<h3>Other notes</h3>" + _list(survey.proposal.notes)
    return _section("profile", "Profile", labels + details + notes + markers + other)


def _repeated_lines_table(facts: Facts, *, survey: PdfSurvey | None) -> str:
    """List the repeated lines and what the survey made of each.

    Parameters
    ----------
    facts
        The measured facts.
    survey
        The survey, if any.

    Returns
    -------
    str
        A ``table`` element.
    """

    meaning: dict[str, str] = {}
    if survey is not None:
        for artifact in survey.proposal.artifacts:
            for line_id in artifact.repeated_line_ids:
                meaning[line_id] = f"artifact {artifact.id}: {artifact.description}"
        for line in survey.proposal.non_artifact_lines:
            meaning[line.repeated_line_id] = f"content: {line.reason}"
    return _table(
        caption="Repeated lines",
        headers=["ID", "Text", "Pages", "Band", "Survey"],
        rows=[
            [
                line.id,
                line.text,
                str(len(line.pages)),
                line.band,
                meaning.get(line.id, "-"),
            ]
            for line in facts.repeated_lines
        ],
    )


def _review_row(issue: ReviewIssue) -> list[str]:
    """Write a review issue's row in the review section, linked to where it is.

    A break's issue links to the break's card. Any other issue links to its page and
    to the box it names.

    Parameters
    ----------
    issue
        The issue.

    Returns
    -------
    list[str]
        The issue's check, page or pages, item and message.
    """

    index, item_id = issue.page_index, issue.item_id
    if issue.step == _BREAKS_STEP and index is not None:
        place = _Html(
            f'<a class="ref" href="#{_break_anchor(index)}">{index + 1} and '
            f"{index + 2}</a>"
        )
        return [issue.check, place, item_id or "-", issue.message]
    page = _Html(
        "-"
        if index is None
        else f'<a class="ref" href="#page-{index}">{index + 1} (index {index})</a>'
    )
    item = _Html("-" if item_id is None else _item_link(item_id))
    return [issue.check, page, item, issue.message]


def _review_section(review: list[ReviewIssue]) -> str:
    """Show the review issues, counted by check, then by step and page.

    Parameters
    ----------
    review
        The run's review issues.

    Returns
    -------
    str
        The section's HTML, with a heading for each step that has issues.
    """

    if not review:
        return _section("review", "Review issues", "<p>None.</p>")
    counts = Counter(issue.check for issue in review)
    parts = [_definitions([(check, str(count)) for check, count in counts.items()])]
    for step in dict.fromkeys(issue.step for issue in review):
        # Issues about the whole PDF come first, then by page; the order is otherwise
        # kept.
        issues = sorted(
            (issue for issue in review if issue.step == step),
            key=lambda issue: -1 if issue.page_index is None else issue.page_index,
        )
        place = "Pages" if step == _BREAKS_STEP else "Page"
        parts.append(
            f"<h3>{_escape(_STEP_TITLES.get(step, step))}</h3>"
            + _table(
                caption=None,
                headers=["Check", place, "Item", "Issue"],
                rows=[_review_row(issue) for issue in issues],
            )
        )
    return _section("review", "Review issues", "".join(parts))


def _run_header(
    record: RunRecord,
    *,
    breaks: list[BreakFile],
    pages: list[PageFile],
    survey: PdfSurvey | None,
) -> str:
    """Show which PDF the run processed, how it ended and with which models.

    Parameters
    ----------
    record
        The run's record.
    breaks
        The verdicts, for the page-break verification model.
    pages
        The page files of the selected pages, for the page extraction model.
    survey
        The survey, if any, for its model.

    Returns
    -------
    str
        A ``header`` element.
    """

    pdf = record.pdf
    items = [("Status", record.status)]
    if survey is not None:
        items.append(("Survey model", survey.inputs.model))
    if pages:
        items.append(("Page extraction model", pages[0].inputs.model))
    if breaks:
        items.append(("Page-break verification model", breaks[0].inputs.model))
    items += [
        ("PDF", f"{pdf.path} ({pdf.page_count} pages, {pdf.bytes:,} bytes)"),
        ("SHA-256", pdf.sha256),
        ("Run", record.run_id),
        ("Started", f"{record.started_at:%Y-%m-%d %H:%M:%S} UTC"),
    ]
    if record.ended_at is not None:
        items.append(("Ended", f"{record.ended_at:%Y-%m-%d %H:%M:%S} UTC"))
    if record.error is not None:
        items.append(("Error", record.error))
    name = Path(pdf.path).name
    return f"<header><h1>{_escape(name)}</h1>{_definitions(items)}</header>"


def _section(anchor: str, title: str, body: str) -> str:
    """Wrap HTML in a section with a heading.

    Parameters
    ----------
    anchor
        The section's ID, for links and its heading.
    title
        The heading's text.
    body
        The section's HTML.

    Returns
    -------
    str
        A ``section`` element labeled by its heading.
    """

    return (
        f'<section aria-labelledby="{anchor}-title"><h2 id="{anchor}-title">'
        f"{_escape(title)}</h2>{body}</section>"
    )


def _short_name(name: str) -> str:
    """Shorten a form field's full name to its last part, for a box on the page.

    Parameters
    ----------
    name
        The field's fully qualified name.

    Returns
    -------
    str
        The last part of the name, without a trailing index.

    Examples
    --------
    >>> _short_name("topmostSubform[0].Page1[0].f1_01[0]")
    'f1_01'
    """

    return re.sub(r"\[\d+\]$", "", name.rsplit(".", 1)[-1])


def _table(*, caption: str | None, headers: list[str], rows: list[list[str]]) -> str:
    """Build a table of plain-text cells.

    Parameters
    ----------
    caption
        The table's caption, or ``None`` for a table under its own heading.
    headers
        The column headings.
    rows
        The cells, row by row. A cell given as `_Html` is put in as it is; any other
        cell is escaped.

    Returns
    -------
    str
        A ``table`` element.
    """

    head = "".join(f'<th scope="col">{_escape(header)}</th>' for header in headers)
    body = "".join(
        "<tr>"
        + "".join(
            f"<td>{cell if isinstance(cell, _Html) else _escape(cell)}</td>"
            for cell in row
        )
        + "</tr>"
        for row in rows
    )
    title = "" if caption is None else f"<caption>{_escape(caption)}</caption>"
    return f"<table>{title}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _verifier_text(
    verification: BreakVerification | PageVerification | SurveyVerification | None,
) -> str:
    """Say what the verifier made of the survey, a page or a break's verdict.

    Parameters
    ----------
    verification
        The verifier's review of the survey, the page or the verdict, or ``None``
        when no verifier ran.

    Returns
    -------
    str
        ``passed``, the problems it found and whether its correction was kept, or
        ``no verifier ran``.
    """

    if verification is None:
        return "no verifier ran"
    verdict = verification.verdict
    if verdict.passed:
        return "passed"
    count = len(verdict.problems)
    problems = f"{count} problem{'' if count == 1 else 's'}"
    if verification.correction_applied:
        return f"found {problems} and its correction was kept"
    return f"found {problems}, listed for review"


def _warnings_section(record: RunRecord) -> str:
    """Show the run's warnings.

    Parameters
    ----------
    record
        The run's record.

    Returns
    -------
    str
        The section's HTML, or nothing when the run gave no warnings.
    """

    if not record.warnings:
        return ""
    return _section(
        "warnings",
        "Warnings",
        _list([f"{warning.code}: {warning.message}" for warning in record.warnings]),
    )


@dataclass(frozen=True)
class ReportInputs:
    """What a report is written from: the run's record and the files it has."""

    break_pages: dict[int, PageFile]
    """The page files the verdicts were judged from, by page index. They can include
    pages the run did not select."""

    breaks: list[BreakFile]
    """The verdicts, in break order."""

    facts: PdfFacts | None
    """The facts, if the run measured or reused them."""

    manifest: ReportManifest
    """The page images."""

    output_folder: Path
    """The output folder, where the report is written."""

    pages: list[PageFile]
    """The page files of the selected pages, in page order."""

    record: RunRecord
    """The run's record, as written to ``run.json``."""

    survey: PdfSurvey | None
    """The survey, if the run made or reused one."""


def write_report(inputs: ReportInputs) -> Path:
    """Write ``report.html`` atomically, with the data the run has.

    Parameters
    ----------
    inputs
        The run's record, its files and the output folder.

    Returns
    -------
    Path
        The report's path.
    """

    record, survey = inputs.record, inputs.survey
    parts = [
        _run_header(record, breaks=inputs.breaks, pages=inputs.pages, survey=survey),
        "<main>",
        _cost_section(record),
        _warnings_section(record),
        _review_section(record.review),
    ]
    if survey is not None:
        parts.append(_profile_section(survey))
    if inputs.facts is not None:
        facts = inputs.facts
        parts.append(_facts_section(facts.facts, summary=facts.summary, survey=survey))
        parts.append(
            _pages_section(
                facts=facts.facts,
                manifest=inputs.manifest,
                pages=inputs.pages,
                review=record.review,
                survey=survey,
            )
        )
    parts.append(
        _breaks_section(
            inputs.breaks, manifest=inputs.manifest, pages=inputs.break_pages
        )
    )
    parts.append("</main>")

    stylesheet = files("pydelity.report").joinpath("report.css").read_text("utf-8")
    title = f"pydelity report: {Path(record.pdf.path).name}"
    document = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_escape(title)}</title>\n<style>\n{stylesheet}</style>\n</head>\n"
        f"<body>\n{''.join(parts)}\n</body>\n</html>\n"
    )
    path = inputs.output_folder / REPORT_FILE_NAME
    write_text_atomic(path=path, text=document)
    return path

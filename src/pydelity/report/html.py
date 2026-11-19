"""``report.html``, the page that shows a run's results.

It shows the run, its cost and review issues, the profile, the facts and the pages,
with the survey's regions and the form fields drawn over each page image. It is static
HTML with its stylesheet inlined, so it runs no JavaScript and loads nothing from
elsewhere. Every string taken from the PDF, the settings or the model is HTML-escaped.
"""

# Standard Library
import html
import re

from collections import Counter
from importlib.resources import files
from pathlib import Path

# Package Library
from pydelity.costs.budget import format_usd
from pydelity.pipeline.schemas import RunRecord
from pydelity.report.schemas import PageImage, ReportManifest
from pydelity.surveying.schemas import (
    Facts,
    PageFacts,
    PdfFacts,
    PdfSurvey,
    ReviewIssue,
)
from pydelity.utils.files import write_text_atomic

# The report's file name in the output folder.
REPORT_FILE_NAME = "report.html"


def _box(
    *, bbox: tuple[float, float, float, float], kind: str, label: str, page: PageFacts
) -> str:
    """Draw a box over a page image, positioned in percent of the page.

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

    def percent(value: float, size: float) -> float:
        """Turn a coordinate into a percentage of the page, kept on the page."""

        return min(max(value / size * 100, 0), 100)

    left = percent(bbox[0], page.width_pt)
    top = percent(bbox[1], page.height_pt)
    width = percent(bbox[2], page.width_pt) - left
    height = percent(bbox[3], page.height_pt) - top
    style = f"left:{left:.2f}%;top:{top:.2f}%;width:{width:.2f}%;height:{height:.2f}%"
    return (
        f'<div class="box {kind}" style="{style}">'
        f'<span class="box-label">{_escape(label)}</span></div>'
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


def _page_card(
    page: PageFacts,
    *,
    facts: Facts,
    image: PageImage,
    issues: list[ReviewIssue],
    survey: PdfSurvey | None,
) -> str:
    """Show one page: its image with boxes drawn over it, and what was found on it.

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
    figure = (
        f'<figure><div class="page-image"><img src="{_escape(image.file)}" '
        f'alt="Page {page.index} as displayed" width="{image.width_px}" '
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
        f'<article class="page" id="page-{page.index}"><h3>Page {page.index}</h3>'
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
        All the measured facts, for the repeated lines.
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
        degrees = next(
            (
                turn.degrees
                for turn in survey.profile.rotation
                if turn.first_page_index <= page.index <= turn.last_page_index
            ),
            0,
        )
        findings.append(("Rotation to make it upright", f"{degrees} degrees clockwise"))
        labels = [
            r.label for r in survey.proposal.regions if r.page_index == page.index
        ]
        findings.append(("Regions", ", ".join(labels) or "none"))
    repeated = [line.id for line in facts.repeated_lines if page.index in line.pages]
    findings.append(("Repeated lines", ", ".join(repeated) or "none"))
    return findings


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
    review: list[ReviewIssue],
    survey: PdfSurvey | None,
) -> str:
    """Show every page as a card.

    Parameters
    ----------
    facts
        The measured facts.
    manifest
        The page images.
    review
        The run's review issues.
    survey
        The survey, if any.

    Returns
    -------
    str
        The section's HTML.
    """

    images = {image.index: image for image in manifest.pages}
    cards = [
        _page_card(
            page,
            facts=facts,
            image=images[page.index],
            issues=[issue for issue in review if issue.page_index == page.index],
            survey=survey,
        )
        for page in facts.pages
        if page.index in images
    ]
    return _section("pages", "Pages", "".join(cards))


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


def _review_section(review: list[ReviewIssue]) -> str:
    """Show the review issues, counted by check, then one by one.

    Parameters
    ----------
    review
        The run's review issues.

    Returns
    -------
    str
        The section's HTML.
    """

    if not review:
        return _section("review", "Review issues", "<p>None.</p>")
    counts = Counter(issue.check for issue in review)
    by_check = _definitions([(check, str(count)) for check, count in counts.items()])
    issues = _table(
        caption="Every issue",
        headers=["Step", "Check", "Page", "Issue"],
        rows=[
            [issue.step, issue.check, _page_text(issue.page_index), issue.message]
            for issue in review
        ],
    )
    return _section("review", "Review issues", by_check + issues)


def _run_header(record: RunRecord) -> str:
    """Show which PDF the run processed, how it ended and with which model.

    Parameters
    ----------
    record
        The run's record.

    Returns
    -------
    str
        A ``header`` element.
    """

    pdf = record.pdf
    items = [
        ("Status", record.status),
        ("Model", str(record.settings.get("model", "-"))),
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


def _table(*, caption: str, headers: list[str], rows: list[list[str]]) -> str:
    """Build a table of plain-text cells.

    Parameters
    ----------
    caption
        The table's caption.
    headers
        The column headings.
    rows
        The cells, row by row.

    Returns
    -------
    str
        A ``table`` element.
    """

    head = "".join(f'<th scope="col">{_escape(header)}</th>' for header in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{_escape(cell)}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return (
        f"<table><caption>{_escape(caption)}</caption><thead><tr>{head}</tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


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


def write_report(
    *,
    facts: PdfFacts | None,
    manifest: ReportManifest,
    output_folder: Path,
    record: RunRecord,
    survey: PdfSurvey | None,
) -> Path:
    """Write ``report.html`` atomically, with the data the run has.

    Parameters
    ----------
    facts
        The facts, if the run measured or reused them.
    manifest
        The page images.
    output_folder
        The output folder.
    record
        The run's record, as written to ``run.json``.
    survey
        The survey, if the run made or reused one.

    Returns
    -------
    Path
        The report's path.
    """

    parts = [
        _run_header(record),
        "<main>",
        _cost_section(record),
        _warnings_section(record),
        _review_section(record.review),
    ]
    if survey is not None:
        parts.append(_profile_section(survey))
    if facts is not None:
        parts.append(_facts_section(facts.facts, summary=facts.summary, survey=survey))
        parts.append(
            _pages_section(
                facts=facts.facts,
                manifest=manifest,
                review=record.review,
                survey=survey,
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
    path = output_folder / REPORT_FILE_NAME
    write_text_atomic(path=path, text=document)
    return path

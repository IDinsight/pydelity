"""``pdf_facts.json``: the measured facts and their summary, saved before model calls.

The facts are measured right after the PDF is opened, before any API key check, cost
question or model call, so a run that is declined, fails or has no API key still
leaves them on disk. A valid file with a matching fingerprint is reused.
"""

# Standard Library
import asyncio
import json

from collections import Counter
from datetime import UTC, datetime
from functools import cache
from importlib.metadata import version
from pathlib import Path

# Third Party Library
from loguru import logger

# Package Library
from pydelity.schema_versions import FACTS_SCHEMA_VERSION
from pydelity.surveying.probe import PROBE_VERSION, probe_pdf
from pydelity.surveying.schemas import (
    Facts,
    PageFacts,
    PdfFacts,
    PdfIdentity,
)
from pydelity.utils.coroutines import warn
from pydelity.utils.files import load_model, write_model_atomic
from pydelity.utils.fingerprints import fingerprint
from pydelity.utils.pdf import PdfInfo

# The facts file's name in the output folder.
FACTS_FILE_NAME = "pdf_facts.json"

# How many of the most frequent repeated lines the summary names.
_REPEATED_LINES_NAMED = 3

# How much of a repeated line the summary quotes.
_QUOTED_CHARS = 60

# A page counts as mostly vertical writing from this share of vertical characters.
_VERTICAL_PAGE_SHARE = 0.5


def _bookmarks_line(facts: Facts) -> list[str]:
    """Summarize the bookmarks.

    Parameters
    ----------
    facts
        The measured facts.

    Returns
    -------
    list[str]
        One line, or none when the bookmarks could not be read.
    """

    if facts.bookmarks is None:
        return []
    if not facts.bookmarks:
        return ["Bookmarks: none."]
    top = sum(1 for bookmark in facts.bookmarks if bookmark.level == 1)
    return [f"Bookmarks: {len(facts.bookmarks)}, {top} at the top level."]


def _count(number: int, noun: str) -> str:
    """Write a count with its noun, plural when needed.

    Parameters
    ----------
    number
        The count.
    noun
        The noun in the singular.

    Returns
    -------
    str
        Such as ``1 page`` or ``3 pages``.
    """

    return f"{number:,} {noun}" + ("" if number == 1 else "s")


def _direction_lines(pages: list[PageFacts]) -> list[str]:
    """Summarize the writing direction.

    Parameters
    ----------
    pages
        The page facts.

    Returns
    -------
    list[str]
        The inline direction by page count, and the pages with vertical writing.
    """

    counts = Counter(page.direction.inline for page in pages)
    parts = [
        f"{label} on {_count(counts[name], 'page')}"
        for name, label in (
            ("ltr", "left to right"),
            ("rtl", "right to left"),
            ("mixed", "mixed"),
            ("none", "no letters"),
        )
        if counts[name]
    ]
    lines = [f"Inline direction: {', '.join(parts)}."]
    vertical = [
        page.index
        for page in pages
        if page.direction.vertical_share >= _VERTICAL_PAGE_SHARE
    ]
    if vertical:
        lines.append(
            f"Mostly vertical (top-to-bottom) writing on pages {_ranges(vertical)}."
        )
    return lines


def _form_line(facts: Facts) -> list[str]:
    """Summarize the form fields.

    Parameters
    ----------
    facts
        The measured facts.

    Returns
    -------
    list[str]
        One line, or none when the form could not be read.
    """

    if facts.form_fields is None or facts.form is None:
        return []
    flags = (
        f"AcroForm {'yes' if facts.form.has_acroform else 'no'}, "
        f"XFA {'yes' if facts.form.has_xfa else 'no'}"
    )
    if not facts.form_fields:
        return [f"Form fields: none ({flags})."]
    types = Counter(form_field.type for form_field in facts.form_fields)
    kinds = ", ".join(f"{count} {name}" for name, count in sorted(types.items()))
    return [f"Form fields: {len(facts.form_fields)} ({kinds}); {flags}."]


def _numbering_lines(facts: Facts) -> list[str]:
    """Summarize the printed page numbers.

    Parameters
    ----------
    facts
        The measured facts.

    Returns
    -------
    list[str]
        One line per numbering range, or one saying none were found.
    """

    if not facts.page_numbering:
        return ["Printed page numbers: none found."]
    return [
        f"Printed page numbers ({numbering.style}) on pages "
        f"{numbering.first_page_index}-{numbering.last_page_index}: printed number = "
        f"page index {numbering.offset:+d} ({_count(numbering.pages_measured, 'page')} "
        "measured)."
        for numbering in facts.page_numbering
    ]


def _orientation_lines(pages: list[PageFacts]) -> list[str]:
    """Summarize which pages are turned, by rotation attribute and by measured text.

    Parameters
    ----------
    pages
        The page facts.

    Returns
    -------
    list[str]
        A line per measured angle other than 0, and one for rotation attributes.
    """

    lines = []
    for angle in (90, 180, 270):
        turned = [page.index for page in pages if page.orientation.dominant == angle]
        if turned:
            lines.append(
                f"Text runs {angle} degrees counterclockwise on pages "
                f"{_ranges(turned)}."
            )
    if not lines:
        lines.append("Text runs upright on every page with horizontal text.")
    for attribute in (90, 180, 270):
        rotated = [page.index for page in pages if page.rotation_attribute == attribute]
        if rotated:
            lines.append(
                f"Rotation attribute {attribute} degrees on pages {_ranges(rotated)}."
            )
    return lines


def _page_line(page: PageFacts) -> str:
    """Describe one page's facts on one line, for detailed logs.

    Parameters
    ----------
    page
        The page's facts.

    Returns
    -------
    str
        The page's text quality, orientation, direction and printed number.
    """

    orientation = page.orientation
    angle = "-" if orientation.dominant is None else str(orientation.dominant)
    sure = "" if orientation.confident else "?"
    number = page.printed_number.text if page.printed_number else "-"
    return (
        f"page {page.index}: {page.text.chars} characters ({page.text.quality}), "
        f"orientation {angle}{sure}, direction {page.direction.inline}, "
        f"vertical {page.direction.vertical_share:.0%}, printed number {number}"
    )


@cache
def _pydelity_version() -> str:
    """Return the installed pydelity's version.

    Returns
    -------
    str
        The version, read from the package metadata once.
    """

    return version("pydelity")


def _ranges(indexes: list[int]) -> str:
    """Write page indexes as ranges.

    Parameters
    ----------
    indexes
        Page indexes in increasing order.

    Returns
    -------
    str
        Such as ``0-3, 7, 9-10``.

    Examples
    --------
    >>> _ranges([0, 1, 2, 3, 7, 9, 10])
    '0-3, 7, 9-10'
    """

    parts = []
    start = previous = indexes[0]
    for index in [*indexes[1:], None]:
        if index is not None and index == previous + 1:
            previous = index
            continue
        parts.append(str(start) if start == previous else f"{start}-{previous}")
        if index is not None:
            start = previous = index
    return ", ".join(parts)


def _repeated_line_lines(facts: Facts) -> list[str]:
    """Summarize the repeated lines: how many, and the most frequent.

    Parameters
    ----------
    facts
        The measured facts.

    Returns
    -------
    list[str]
        The count, then the most frequent lines with their IDs.
    """

    if not facts.repeated_lines:
        return ["Repeated lines: none."]
    more = (
        " (more were found; only these are kept)"
        if facts.repeated_lines_truncated
        else ""
    )
    lines = [f"Repeated lines: {len(facts.repeated_lines)}{more}."]
    for line in facts.repeated_lines[:_REPEATED_LINES_NAMED]:
        quoted = line.text
        if len(quoted) > _QUOTED_CHARS:
            quoted = quoted[: _QUOTED_CHARS - 3] + "..."
        lines.append(
            f"{line.id} {json.dumps(quoted, ensure_ascii=False)} on "
            f"{_count(len(line.pages), 'page')}, "
            f"usually in the {line.band} band."
        )
    return lines


def _structure_line(facts: Facts) -> list[str]:
    """Summarize the structure tags.

    Parameters
    ----------
    facts
        The measured facts.

    Returns
    -------
    list[str]
        One line, or none when the structure tree could not be read.
    """

    structure = facts.structure
    if structure is None:
        return []
    if not structure.tagged:
        return ["Structure tags: none."]
    capped = ", count capped" if structure.truncated else ""
    return [
        f"Structure tags: {structure.quality}, "
        f"{_count(structure.element_count, 'element')} covering "
        f"{_count(structure.pages_with_tagged_content, 'page')}{capped}."
    ]


def _text_lines(pages: list[PageFacts]) -> list[str]:
    """Summarize the text layer: pages without text and pages with garbled text.

    Parameters
    ----------
    pages
        The page facts.

    Returns
    -------
    list[str]
        One or two lines.
    """

    empty = [page.index for page in pages if page.text.quality == "none"]
    garbled = [page.index for page in pages if page.text.quality == "garbled"]
    lines = []
    if empty:
        lines.append(f"No text layer on pages {_ranges(empty)}.")
    else:
        lines.append("Every page has a text layer.")
    if garbled:
        lines.append(f"Garbled text on pages {_ranges(garbled)}.")
    return lines


def _unreadable_lines(facts: Facts) -> list[str]:
    """Name the facts that could not be read.

    Parameters
    ----------
    facts
        The measured facts.

    Returns
    -------
    list[str]
        One line per unreadable fact.
    """

    return [
        f"Could not read the {error.fact}: {error.message}"
        for error in facts.probe_errors
    ]


def facts_fingerprint(pdf_sha256: str) -> str:
    """Return the fingerprint of what the facts depend on.

    Parameters
    ----------
    pdf_sha256
        The PDF's SHA-256.

    Returns
    -------
    str
        The ``sha256:`` fingerprint of the PDF's SHA-256, `PROBE_VERSION` and the
        facts schema version.
    """

    return fingerprint(
        {
            "pdf_sha256": pdf_sha256,
            "probe_version": PROBE_VERSION,
            "schema_version": FACTS_SCHEMA_VERSION,
        }
    )


async def measure_facts(
    *, output_folder: Path, overwrite: bool, pdf: PdfInfo, save: bool = True
) -> PdfFacts:
    """Measure the PDF, or reuse its saved facts, and log the summary.

    A valid ``pdf_facts.json`` with a matching fingerprint is reused unless
    ``overwrite`` is set. A damaged one is measured again, with a warning. New facts
    are written atomically, unless ``save`` is false. Each fact the probe could not
    read gives a warning.

    Parameters
    ----------
    output_folder
        The output folder. It must exist when ``save`` is true.
    overwrite
        Whether to measure again even when the saved facts match.
    pdf
        The PDF, already opened and checked.
    save
        Whether to write new facts to ``pdf_facts.json``. A cost estimate measures
        the PDF without writing anything.

    Returns
    -------
    PdfFacts
        The facts, as saved in ``pdf_facts.json`` or as they would be.
    """

    path = output_folder / FACTS_FILE_NAME
    expected = facts_fingerprint(pdf.sha256)
    saved = load_model(model_type=PdfFacts, path=path)
    if saved.damage is not None:
        warn(
            f"{saved.damage}; measuring the PDF again",
            code="damaged_output",
            details={"file": FACTS_FILE_NAME},
        )

    if (
        saved.model is not None
        and saved.model.fingerprint == expected
        and not overwrite
    ):
        result = saved.model
        logger.info("Facts reused from {path}", path=path)
    else:
        facts = await asyncio.to_thread(probe_pdf, pdf.path)
        result = PdfFacts(
            facts=facts,
            fingerprint=expected,
            measured_at=datetime.now(UTC),
            pdf=PdfIdentity(
                bytes=pdf.bytes,
                name=pdf.name,
                page_count=pdf.page_count,
                sha256=pdf.sha256,
            ),
            probe_version=PROBE_VERSION,
            pydelity_version=_pydelity_version(),
            schema_version=FACTS_SCHEMA_VERSION,
            summary=summarize(facts),
        )
        if save:
            write_model_atomic(model=result, path=path)
            logger.info("Facts measured and saved to {path}", path=path)
        else:
            logger.info("Facts measured, not saved")

    for line in result.summary:
        logger.info("  {line}", line=line)
    for error in result.facts.probe_errors:
        warn(
            f"Could not read the PDF's {error.fact}: {error.message}",
            code="probe_unavailable",
            details={"fact": error.fact},
        )
    for page in result.facts.pages:
        logger.debug("  {page}", page=_page_line(page))
    return result


def summarize(facts: Facts) -> list[str]:
    """Describe the facts as plain-text lines.

    The same facts always give the same lines. They are logged, sent to the model with
    the survey request and placed at the top of the report's facts section.

    Parameters
    ----------
    facts
        The measured facts.

    Returns
    -------
    list[str]
        The summary lines.
    """

    pages = facts.pages
    last = f" (indexes 0-{len(pages) - 1})" if pages else ""
    return [
        f"{_count(len(pages), 'page')}{last}; page indexes start at 0.",
        *_text_lines(pages),
        *_direction_lines(pages),
        *_orientation_lines(pages),
        *_numbering_lines(facts),
        *_repeated_line_lines(facts),
        *_bookmarks_line(facts),
        *_form_line(facts),
        *_structure_line(facts),
        *_unreadable_lines(facts),
    ]

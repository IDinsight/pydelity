"""A page's text layer, and the form text is compared in.

The text layer is the text a PDF stores for a page. The models read the page image.
Of the stored text, a page request carries only the page's repeated lines, and a
retry message for a failed text check quotes the lines it is about. Page extraction
compares the text layer's lines with the items' text to find text the answer dropped
or added. It also finds where the page furniture the survey found sits on the page,
from the stored text alone, so the furniture check compares boxes rather than text.

Text is compared as overlapping runs of three characters, after Unicode NFKC
normalization and case folding, keeping only letters, marks and digits. Spaces,
punctuation and line breaks drop out, so scripts written without spaces between words
compare the same way as others, and no word list or tokenizer is needed.
"""

# Standard Library
import unicodedata

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

# Third Party Library
import pymupdf

# Package Library
from pydelity.extracting.rendering import points_box_to_grid
from pydelity.extracting.schemas import PageContext
from pydelity.surveying.probe import line_boxes
from pydelity.utils.pdf import TEXT_FLAGS
from pydelity.utils.text import normalize_line

# The Unicode categories kept for comparison: letters, marks and numbers.
_KEPT_CATEGORIES = ("L", "M", "N")

# How far apart, in line thicknesses, two pieces of text along one writing direction
# may be and still count as one line.
_MAX_GAP_THICKNESSES = 2


def _continues(previous: dict[str, Any], line: dict[str, Any]) -> bool:
    """Tell whether a stored line continues the one before it along its direction.

    PyMuPDF can store one visual line as several lines: each character of a column
    of vertical text, or the pieces of a horizontal line with gaps in it. A piece
    continues the line before it when both run the same way, they line up across
    the direction, and the gap between them along it is at most
    `_MAX_GAP_THICKNESSES` line thicknesses.

    Parameters
    ----------
    previous
        The line before, from ``page.get_text("dict")``.
    line
        The line after it.

    Returns
    -------
    bool
        Whether the two are pieces of one line.
    """

    direction = tuple(round(value) for value in line["dir"])
    if direction != tuple(round(value) for value in previous["dir"]):
        return False
    px0, py0, px1, py1 = previous["bbox"]
    x0, y0, x1, y1 = line["bbox"]
    if direction[0] != 0:
        thickness = min(py1 - py0, y1 - y0)
        overlap = min(py1, y1) - max(py0, y0)
        gap = x0 - px1 if direction[0] > 0 else px0 - x1
    else:
        thickness = min(px1 - px0, x1 - x0)
        overlap = min(px1, x1) - max(px0, x0)
        gap = y0 - py1 if direction[1] > 0 else py0 - y1
    return (
        thickness > 0
        and overlap > thickness / 2
        and -thickness / 2 <= gap <= _MAX_GAP_THICKNESSES * thickness
    )


def _joined_lines(lines: Sequence[dict[str, Any]]) -> list[str]:
    """Join the stored lines of one block that are pieces of one visual line.

    Parameters
    ----------
    lines
        A block's lines, from ``page.get_text("dict")``, in stored order.

    Returns
    -------
    list[str]
        The visual lines' text.
    """

    texts: list[str] = []
    previous = None
    for line in lines:
        text = "".join(span["text"] for span in line["spans"])
        if previous is not None and texts and _continues(previous, line):
            texts[-1] += text
        else:
            texts.append(text)
        previous = line
    return texts


@dataclass(frozen=True)
class PageText:
    """What a page's text layer gives the checks."""

    furniture: Mapping[str, tuple[tuple[int, ...], ...]]
    """Where the page furniture the survey found sits on the upright image's grid:
    the box of each line that holds it, by repeated line ID. A furniture line the
    page's stored text does not hold is absent."""

    lines: tuple[str, ...]
    """The page's text-layer lines, from `read_lines`."""


def comparison_form(text: str) -> str:
    """Write text in the form it is compared in.

    Parameters
    ----------
    text
        The text as printed or stored.

    Returns
    -------
    str
        The text NFKC-normalized and case-folded, with only its letters, marks and
        digits (Unicode categories L, M and N).

    Examples
    --------
    >>> comparison_form("Section 3 \u2014 Notes (draft)")
    'section3notesdraft'
    """

    folded = unicodedata.normalize("NFKC", text).casefold()
    return "".join(
        char
        for char in folded
        if unicodedata.category(char).startswith(_KEPT_CATEGORIES)
    )


def read_lines(document: pymupdf.Document, *, page_index: int) -> list[str]:
    """Read a page's text-layer lines, in the order the PDF stores them.

    Pieces of one visual line that the PDF stores apart, such as each character of
    a column of vertical text, are joined into one line. Run it on the PyMuPDF
    worker (`pydelity.extracting.rendering.PdfWorker.call`).

    Parameters
    ----------
    document
        The open PDF.
    page_index
        The page (0-based).

    Returns
    -------
    list[str]
        Each line's text, its spans joined, without lines that are only whitespace.
    """

    page = document[page_index]
    lines = []
    for block in page.get_text("dict", flags=TEXT_FLAGS)["blocks"]:
        lines += [
            text for text in _joined_lines(block.get("lines", [])) if text.strip()
        ]
    return lines


def read_page_text(document: pymupdf.Document, *, context: PageContext) -> PageText:
    """Read a page's text-layer lines and find where its page furniture sits.

    Each line the survey classed as page furniture is looked for among the page's
    lines as the survey's probe reads them, by the same normalized form, so stored
    text is only ever matched with stored text. Run it on the PyMuPDF worker
    (`pydelity.extracting.rendering.PdfWorker.call`).

    Parameters
    ----------
    document
        The open PDF.
    context
        The page's context: its index, size, rotation and repeated lines.

    Returns
    -------
    PageText
        The page's lines and the grid boxes of its furniture lines.
    """

    wanted = {
        line.normalized: line.id
        for line in context.repeated_lines
        if line.use == "artifact" and line.normalized
    }
    furniture: defaultdict[str, list[tuple[int, ...]]] = defaultdict(list)
    if wanted:
        for text, rect in line_boxes(document[context.page_index]):
            line_id = wanted.get(normalize_line(text))
            if line_id is not None:
                box = points_box_to_grid(
                    [rect.x0, rect.y0, rect.x1, rect.y1],
                    height_pt=context.height_pt,
                    rotation=context.rotation,
                    width_pt=context.width_pt,
                )
                furniture[line_id].append(tuple(box))
    return PageText(
        furniture={line_id: tuple(boxes) for line_id, boxes in furniture.items()},
        lines=tuple(read_lines(document, page_index=context.page_index)),
    )


def trigrams(form: str) -> Counter[str]:
    """Count the runs of three characters in text already in comparison form.

    Parameters
    ----------
    form
        Text from `comparison_form`.

    Returns
    -------
    Counter[str]
        Each run of three consecutive characters, with how often it occurs; empty
        for text shorter than three characters.

    Examples
    --------
    >>> sorted(trigrams("abcab").items())
    [('abc', 1), ('bca', 1), ('cab', 1)]
    """

    return Counter(form[start : start + 3] for start in range(len(form) - 2))

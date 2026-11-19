"""A page's text layer, and the form text is compared in.

The text layer is the text a PDF stores for a page, which a model never sees: it reads
the page image. Its lines go to the model as hints, and page extraction compares them
with the items' text to find text the answer dropped or added.

Text is compared as overlapping runs of three characters, after Unicode NFKC
normalization and case folding, keeping only letters, marks and digits. Spaces,
punctuation and line breaks drop out, so scripts written without spaces between words
compare the same way as others, and no word list or tokenizer is needed.
"""

# Standard Library
import unicodedata

from collections import Counter
from collections.abc import Sequence
from typing import Any

# Third Party Library
import pymupdf

# How text is read: ligatures and whitespace as stored, and only text inside the page's
# media box, as the survey's probe reads it.
_TEXT_FLAGS = (
    pymupdf.TEXT_PRESERVE_LIGATURES
    | pymupdf.TEXT_PRESERVE_WHITESPACE
    | pymupdf.TEXT_MEDIABOX_CLIP
)

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
    for block in page.get_text("dict", flags=_TEXT_FLAGS)["blocks"]:
        lines += [
            text for text in _joined_lines(block.get("lines", [])) if text.strip()
        ]
    return lines


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

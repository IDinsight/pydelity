"""Tests for reading a page's text layer and finding its page furniture.

Page furniture is found on the upright image's grid, so a page the PDF shows turned
must give the same places as the same page shown upright. The test PDFs are the
W-9 instructions and a copy whose second page has the rotation attribute 90.
"""

# Standard Library
from collections.abc import Callable, Mapping
from pathlib import Path

# Third Party Library
import pymupdf

# Package Library
from pydelity.extracting.schemas import PageContext, PageRepeatedLine
from pydelity.extracting.text_layer import read_page_text
from pydelity.surveying.schemas import Angle, Facts

# The copy of `_UPRIGHT` whose second page the PDF shows a quarter turn clockwise.
_TURNED = "irs_w9_instructions_rotated.pdf"

# The W-9 instructions, every page shown upright.
_UPRIGHT = "irs_w9_instructions.pdf"


def _furniture(
    path: Path,
    *,
    line: PageRepeatedLine,
    page_context: Callable[..., PageContext],
    rotation: Angle,
) -> tuple[PageContext, Mapping[str, tuple[tuple[int, ...], ...]]]:
    """Find where a furniture line sits on the second page of a PDF.

    Parameters
    ----------
    path
        The PDF.
    line
        The furniture line.
    page_context
        The fixture that builds a page context.
    rotation
        The clockwise turn that makes the displayed page upright.

    Returns
    -------
    tuple[PageContext, Mapping[str, tuple[tuple[int, ...], ...]]]
        The page's context, with its displayed size and rotation attribute, and
        the line's places on the upright image's grid.
    """

    with pymupdf.open(path) as document:
        page = document[1]
        context = page_context(
            height_pt=page.rect.height,
            page_count=len(document),
            page_index=1,
            repeated_lines=[line],
            rotation=rotation,
            rotation_attribute=page.rotation,
            width_pt=page.rect.width,
        )
        return context, read_page_text(document, context=context).furniture


def test_furniture_on_a_turned_page_is_found_at_its_upright_place(
    facts_of: Callable[[str], Facts],
    page_context: Callable[..., PageContext],
    pdf_path: Callable[[str], Path],
) -> None:
    """A running footer on a page shown turned is found where the upright page has it.

    The PDF shows the page a quarter turn clockwise, so a turn of 270 degrees
    clockwise makes it upright. On the upright image the footer sits at the bottom
    of the page, at the same grid place as on the copy shown upright.
    """

    footer = next(
        line
        for line in facts_of(_TURNED).repeated_lines
        if line.text.startswith("Instr. for Req. of Form W-9")
    )
    line = PageRepeatedLine(
        id=footer.id, normalized=footer.normalized, text=footer.text, use="artifact"
    )

    turned, found = _furniture(
        pdf_path(_TURNED), line=line, page_context=page_context, rotation=270
    )
    upright, expected = _furniture(
        pdf_path(_UPRIGHT), line=line, page_context=page_context, rotation=0
    )

    assert 1 in footer.pages
    assert (turned.rotation_attribute, upright.rotation_attribute) == (90, 0)
    assert (turned.width_pt, turned.height_pt) == (upright.height_pt, upright.width_pt)
    assert len(found[line.id]) == 1
    assert found[line.id][0][1] > 900
    assert found == expected

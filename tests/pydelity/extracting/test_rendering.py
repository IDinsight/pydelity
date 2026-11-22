"""Tests for page images, figure crops, box coordinates and the PyMuPDF worker.

Page images are checked against their content. A page whose rotation attribute
turns it must render like the same page of the unturned original, and boxes found
in the text layer must land where that text is drawn.
"""

# Standard Library
import asyncio
import math
import threading
import time

from collections.abc import Callable
from pathlib import Path

# Third Party Library
import pymupdf
import pytest

# Package Library
from pydelity.extracting.rendering import (
    GRID,
    PdfWorker,
    UprightImage,
    grid_box_to_points,
    points_box_to_grid,
)
from pydelity.providers.profiles import PROFILES, ProviderProfile
from pydelity.surveying.schemas import Angle, Facts

# The CAPS pages, with landscape tables printed sideways on unrotated portrait pages.
_CAPS = "caps_english_hl_pages_28_35.pdf"

# The W-9 instructions, every page upright and unrotated.
_ORIGINAL = "irs_w9_instructions.pdf"

# The same pages with rotation attributes of 90, 180 and 270 on pages 2, 3 and 4.
_ROTATED = "irs_w9_instructions_rotated.pdf"

# The width, in pixels, both images are shrunk to before they are compared, small
# enough that slight differences in how letters are drawn even out.
_THUMBNAIL_WIDTH = 100


def _displayed_line(
    page: pymupdf.Page, *, start: str
) -> tuple[list[float], list[list[float]]]:
    """Find a text line and give its boxes on the displayed page.

    Parameters
    ----------
    page
        The page.
    start
        The first characters of the line's text.

    Returns
    -------
    tuple[list[float], list[list[float]]]
        The line's box and the boxes of its letters in reading order, each
        ``[x0, y0, x1, y1]`` in points on the displayed page (after the page's
        rotation attribute, origin top left).
    """

    # PyMuPDF gives text boxes on the unrotated page, and its rotation matrix turns
    # them to the displayed page.
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            chars = [char for span in line["spans"] for char in span["chars"]]
            if "".join(char["c"] for char in chars).startswith(start):
                letters = [
                    list(pymupdf.Rect(char["bbox"]) * page.rotation_matrix)
                    for char in chars
                    if char["c"].strip()
                ]
                return list(pymupdf.Rect(line["bbox"]) * page.rotation_matrix), letters
    raise AssertionError(f"no line starts with {start!r}")


def _fits(profile: ProviderProfile, *, height_px: int, width_px: int) -> bool:
    """Tell whether a provider reads an image of this size without shrinking it.

    Parameters
    ----------
    profile
        The provider's limits.
    height_px
        The image's height in pixels.
    width_px
        The image's width in pixels.

    Returns
    -------
    bool
        Whether the long edge and the count of square patches, part patches counted
        whole, are within the provider's limits.
    """

    side = profile.image_patch_px
    patches = math.ceil(width_px / side) * math.ceil(height_px / side)
    return (
        max(height_px, width_px) <= profile.image_max_long_edge_px
        and patches <= profile.image_max_patches
    )


def _gray(data: bytes, *, clip: pymupdf.IRect | None = None) -> pymupdf.Pixmap:
    """Decode a JPEG or PNG image to gray levels, keeping only part of it if asked.

    Parameters
    ----------
    data
        The image file's bytes.
    clip
        The part to keep, in the image's pixels, or ``None`` for all of it.

    Returns
    -------
    pymupdf.Pixmap
        One byte per pixel, 0 for black and 255 for white.
    """

    pixmap = pymupdf.Pixmap(pymupdf.csGRAY, pymupdf.Pixmap(data))
    if clip is None:
        return pixmap
    return pymupdf.Pixmap(pixmap, pixmap.width, pixmap.height, clip)


def _grid_to_pixels(box: list[int], *, image: UprightImage) -> pymupdf.IRect:
    """Turn a box on the grid into the pixels it covers on the page image.

    Parameters
    ----------
    box
        ``[x0, y0, x1, y1]`` in `GRID` units across and down the image.
    image
        The page image.

    Returns
    -------
    pymupdf.IRect
        The box in the image's pixels.
    """

    x0, y0, x1, y1 = box
    return pymupdf.IRect(
        round(x0 * image.width_px / GRID),
        round(y0 * image.height_px / GRID),
        round(x1 * image.width_px / GRID),
        round(y1 * image.height_px / GRID),
    )


def _mean_difference(first: pymupdf.Pixmap, second: pymupdf.Pixmap) -> float:
    """Measure how far apart two gray images are, after shrinking both alike.

    Parameters
    ----------
    first
        One image. Its shape sets the shape both are shrunk to.
    second
        The other image.

    Returns
    -------
    float
        The mean difference in gray level per pixel, from 0 (the same) to 255.
    """

    height = max(1, round(_THUMBNAIL_WIDTH * first.height / first.width))
    one, two = (
        pymupdf.Pixmap(pixmap, _THUMBNAIL_WIDTH, height) for pixmap in (first, second)
    )
    differences = [abs(a - b) for a, b in zip(one.samples, two.samples, strict=True)]
    return sum(differences) / len(differences)


def _mean_gray(pixmap: pymupdf.Pixmap) -> float:
    """Average a gray image's pixels.

    Parameters
    ----------
    pixmap
        The gray image.

    Returns
    -------
    float
        The mean gray level, from 0 (black) to 255 (white).
    """

    return sum(pixmap.samples) / len(pixmap.samples)


def _page_image(path: Path, *, page_index: int, rotation: Angle) -> UprightImage:
    """Render one page upright with a worker of its own.

    Parameters
    ----------
    path
        The PDF.
    page_index
        The page (0-based).
    rotation
        The clockwise turn that makes the page's content upright.

    Returns
    -------
    UprightImage
        The page image.
    """

    async def render() -> UprightImage:
        """Open the PDF in a worker and render the page."""

        async with PdfWorker(path) as worker:
            return await worker.page_image(page_index=page_index, rotation=rotation)

    return asyncio.run(render())


def test_crop_of_a_rotated_page_is_upright_and_matches_the_page_image(
    pdf_path: Callable[[str], Path],
) -> None:
    """A crop is a 200 DPI PNG of the displayed-points box, turned upright.

    On a page shown a quarter turn clockwise, a wide block of text stands tall on the
    displayed page. Its crop is wide again and looks like the same part of the
    upright page image.
    """

    path = pdf_path(_ROTATED)
    with pymupdf.open(path) as document:
        page = document[1]
        # The first three paragraphs of the left column, on the unrotated page.
        box = list(pymupdf.Rect(42, 25, 298, 110) * page.rotation_matrix)
        height_pt, width_pt = page.rect.height, page.rect.width

    async def render() -> tuple[UprightImage, bytes]:
        """Render the upright page and the crop with one worker."""

        async with PdfWorker(path) as worker:
            image = await worker.page_image(page_index=1, rotation=270)
            crop = await worker.crop(box_pt=box, page_index=1, rotation=270)
            return image, crop

    image, crop = asyncio.run(render())
    cropped = _gray(crop)
    region = points_box_to_grid(
        box, height_pt=height_pt, rotation=270, width_pt=width_pt
    )
    expected = _gray(image.data, clip=_grid_to_pixels(region, image=image))

    assert crop.startswith(b"\x89PNG\r\n\x1a\n")
    assert box[3] - box[1] > box[2] - box[0]
    # Upright, the displayed box's height runs across the crop.
    assert cropped.width == pytest.approx((box[3] - box[1]) * 200 / 72, abs=2)
    assert cropped.height == pytest.approx((box[2] - box[0]) * 200 / 72, abs=2)
    # Letters drawn at slightly different sizes differ by a few gray levels, and
    # text turned the wrong way by over 30.
    assert _mean_difference(cropped, expected) <= 8


def test_page_image_is_the_largest_every_provider_reads_and_at_most_300_dpi(
    pdf_path: Callable[[str], Path], tmp_path: Path
) -> None:
    """A Letter page renders as large as every provider reads it without shrinking.

    An image one percent larger would be shrunk by Anthropic. A page small enough
    to fit at any size renders at 300 DPI.
    """

    small = tmp_path / "small.pdf"
    with pymupdf.open() as document:
        # A page 3 inches square.
        document.new_page(height=216, width=216)
        document.save(small)

    letter = _page_image(pdf_path(_ORIGINAL), page_index=0, rotation=0)
    square = _page_image(small, page_index=0, rotation=0)
    decoded = pymupdf.Pixmap(letter.data)

    assert letter.data.startswith(b"\xff\xd8")
    assert (decoded.width, decoded.height) == (letter.width_px, letter.height_px)
    assert letter.width_px / letter.height_px == pytest.approx(612 / 792, abs=0.002)
    assert letter.height_px == pytest.approx(11 * letter.dpi, abs=1)
    assert letter.dpi <= 300
    for profile in PROFILES.values():
        assert _fits(profile, height_px=letter.height_px, width_px=letter.width_px)
    assert not _fits(
        PROFILES["anthropic"],
        height_px=math.ceil(letter.height_px * 1.01),
        width_px=math.ceil(letter.width_px * 1.01),
    )
    assert square.dpi == 300
    assert (square.width_px, square.height_px) == (900, 900)


def test_pymupdf_calls_run_one_at_a_time_on_one_worker_thread_off_the_loop(
    monkeypatch: pytest.MonkeyPatch, pdf_path: Callable[[str], Path]
) -> None:
    """Calls gathered at once, renders and crops included, run one after another.

    They all run on one thread that is not the event loop's. The worker refuses
    calls before its ``async with`` block starts and after it ends.
    """

    lock = threading.Lock()
    threads: list[int] = []
    already_running: list[int] = []
    running = 0

    def tracked(function: Callable[..., object]) -> Callable[..., object]:
        """Wrap a function to record its thread and the calls running beside it."""

        def run(*args: object, **kwargs: object) -> object:
            """Record the call, hold on briefly, then run the function."""

            nonlocal running
            with lock:
                threads.append(threading.get_ident())
                already_running.append(running)
                running += 1
            try:
                # Holding on makes calls that ran at the same time overlap.
                time.sleep(0.01)
                return function(*args, **kwargs)
            finally:
                with lock:
                    running -= 1

        return run

    monkeypatch.setattr(pymupdf.Page, "get_pixmap", tracked(pymupdf.Page.get_pixmap))
    page_count = tracked(lambda document: document.page_count)
    worker = PdfWorker(pdf_path(_ORIGINAL))

    async def use_worker() -> tuple[int, list[object]]:
        """Call the worker outside its block, then gather calls inside it."""

        with pytest.raises(RuntimeError, match="outside its async with block"):
            await worker.call(page_count)
        async with worker:
            results = await asyncio.gather(
                *(worker.call(page_count) for _ in range(4)),
                worker.page_image(page_index=0, rotation=0),
                worker.crop(box_pt=[0, 0, 100, 100], page_index=0, rotation=90),
            )
        with pytest.raises(RuntimeError, match="outside its async with block"):
            await worker.call(page_count)
        return threading.get_ident(), list(results)

    loop_thread, results = asyncio.run(use_worker())

    assert results[:4] == [7, 7, 7, 7]
    assert len(threads) == 6
    assert len(set(threads)) == 1
    assert loop_thread not in threads
    assert already_running == [0] * 6


@pytest.mark.parametrize(
    ("attribute", "page_index", "rotation", "start"),
    [
        (90, 1, 270, "A payee fails to furnish"),
        (180, 2, 180, "must clearly state"),
        (270, 3, 90, "Generally, if a Form W-9"),
    ],
    ids=["attribute-90", "attribute-180", "attribute-270"],
)
def test_rotated_page_renders_upright_and_its_boxes_land_on_their_content(
    attribute: int,
    page_index: int,
    pdf_path: Callable[[str], Path],
    rotation: Angle,
    start: str,
) -> None:
    """A page turned by its rotation attribute renders like the unturned original.

    The turn that undoes the attribute gives an image of the original page's shape
    and look. A text line's box on the displayed page maps to the grid where the
    original page has that line, and maps back to the same box.
    """

    with pymupdf.open(pdf_path(_ORIGINAL)) as document:
        page = document[page_index]
        original_box, _ = _displayed_line(page, start=start)
        original_rotation = page.rotation
        original_size = (page.rect.width, page.rect.height)
    with pymupdf.open(pdf_path(_ROTATED)) as document:
        page = document[page_index]
        box, _ = _displayed_line(page, start=start)
        height_pt, width_pt = page.rect.height, page.rect.width
        turned_rotation = page.rotation

    original = _page_image(pdf_path(_ORIGINAL), page_index=page_index, rotation=0)
    upright = _page_image(pdf_path(_ROTATED), page_index=page_index, rotation=rotation)
    grid = points_box_to_grid(
        box, height_pt=height_pt, rotation=rotation, width_pt=width_pt
    )
    # On the unturned page, the grid is the page scaled to `GRID` units each way.
    original_grid = [
        round(GRID * value / size)
        for value, size in zip(original_box, original_size * 2, strict=True)
    ]

    assert (original_rotation, turned_rotation) == (0, attribute)
    assert upright.width_px == pytest.approx(original.width_px, abs=1)
    assert upright.height_px == pytest.approx(original.height_px, abs=1)
    # The right turn differs by under 1 gray level, a wrong one by about 20.
    assert _mean_difference(_gray(original.data), _gray(upright.data)) <= 3
    assert grid == pytest.approx(original_grid, abs=1)
    assert grid_box_to_points(
        grid, height_pt=height_pt, rotation=rotation, width_pt=width_pt
    ) == pytest.approx(box, abs=max(height_pt, width_pt) / GRID)


def test_sideways_text_on_an_unrotated_page_renders_landscape_and_reads_across(
    facts_of: Callable[[str], Facts], pdf_path: Callable[[str], Path]
) -> None:
    """Text printed sideways on a page with rotation 0 reads across the upright image.

    The text runs bottom to top, so a quarter turn clockwise makes it upright. The
    portrait page then renders landscape, and a sideways line's box maps to a wide
    grid box over the line's ink, with its first letter left of its last.
    """

    facts = facts_of(_CAPS)
    with pymupdf.open(pdf_path(_CAPS)) as document:
        page = document[0]
        height_pt, width_pt = page.rect.height, page.rect.width
        box, letters = _displayed_line(page, start="OVERVIEW OF THE LANGUAGE SKILLS")

    image = _page_image(pdf_path(_CAPS), page_index=0, rotation=90)
    grid = points_box_to_grid(box, height_pt=height_pt, rotation=90, width_pt=width_pt)
    first, last = (
        points_box_to_grid(letter, height_pt=height_pt, rotation=90, width_pt=width_pt)
        for letter in (letters[0], letters[-1])
    )
    ink = _gray(image.data, clip=_grid_to_pixels(grid, image=image))

    assert facts.pages[0].rotation_attribute == 0
    assert facts.pages[0].orientation.dominant == 90
    assert height_pt > width_pt
    assert image.width_px > image.height_px
    assert grid[2] - grid[0] > 10 * (grid[3] - grid[1])
    assert first[0] < last[0]
    assert _mean_gray(ink) < _mean_gray(_gray(image.data)) - 30

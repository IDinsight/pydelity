"""Page images for the models, figure crops, and box coordinates.

Each page request carries one image of the page, turned upright by the clockwise
rotation the survey's profile gives for the page. The image is as large as every
supported provider reads without shrinking it, and at most `_MAX_DPI`.

The model gives boxes on a grid of `GRID` units across and down the upright image,
from its top-left corner, whatever size the provider resizes the image to.
`grid_box_to_points` maps such a box to PDF points on the displayed page (the page
after its rotation attribute, origin top left), the coordinates the survey uses.
`points_box_to_grid` maps the other way, for boxes sent to the model as hints.

PyMuPDF is not safe to use from several threads at once, and page extraction works
on several pages at the same time. `PdfWorker` runs every PyMuPDF call of the step on
one thread, one call at a time, off the event loop.
"""

# Standard Library
import asyncio
import math

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Self

# Third Party Library
import pymupdf

# Package Library
from pydelity.providers.profiles import PROFILES
from pydelity.surveying.schemas import Angle

# The resolution of figure crops, in dots per inch.
_CROP_DPI = 200

# The JPEG quality of page images, from 0 to 100.
_JPEG_QUALITY = 90

# The highest resolution of a page image, in dots per inch. Beyond it a page image
# shows no more detail.
_MAX_DPI = 300

# PDF points per inch.
_POINTS_PER_INCH = 72

# How many halvings the search for the largest zoom makes; enough to settle on a
# zoom well under one pixel from the largest.
_ZOOM_SEARCH_STEPS = 40

# The units across and down the upright page image in which the model gives boxes.
GRID = 1000


def _clamp(value: float, *, high: float, low: float) -> float:
    """Limit a value to a range.

    Parameters
    ----------
    value
        The value.
    high
        The highest value allowed.
    low
        The lowest value allowed.

    Returns
    -------
    float
        The value, or the nearer end of the range when it is outside it.
    """

    return float(max(low, min(high, value)))


def _fits_every_provider(*, height_px: int, width_px: int) -> bool:
    """Tell whether every supported provider reads an image without shrinking it.

    Parameters
    ----------
    height_px
        The image's height in pixels.
    width_px
        The image's width in pixels.

    Returns
    -------
    bool
        Whether the image is within every provider profile's long-edge and patch
        limits.
    """

    return all(
        max(height_px, width_px) <= profile.image_max_long_edge_px
        and profile.image_patches(height_px=height_px, width_px=width_px)
        <= profile.image_max_patches
        for profile in PROFILES.values()
    )


def _render_crop(
    document: pymupdf.Document,
    *,
    box_pt: Sequence[float],
    page_index: int,
    rotation: Angle,
) -> bytes:
    """Render part of a page as an upright PNG image.

    Parameters
    ----------
    document
        The open PDF.
    box_pt
        The part to render, ``[x0, y0, x1, y1]`` in points on the displayed page.
    page_index
        The page (0-based).
    rotation
        The clockwise rotation that makes the page's content upright.

    Returns
    -------
    bytes
        The PNG image, at `_CROP_DPI`.

    Raises
    ------
    ValueError
        If the box does not overlap the page.
    """

    page = document[page_index]
    # PyMuPDF takes the clip in the displayed page's coordinates.
    clip = pymupdf.Rect(box_pt) & page.rect
    if clip.is_empty:
        raise ValueError(f"the box {list(box_pt)} does not overlap page {page_index}")
    zoom = _CROP_DPI / _POINTS_PER_INCH
    matrix = pymupdf.Matrix(zoom, zoom).prerotate(rotation)
    pixmap = page.get_pixmap(alpha=False, clip=clip, matrix=matrix)
    return pixmap.tobytes("png")


def _render_upright(
    document: pymupdf.Document, *, page_index: int, rotation: Angle
) -> "UprightImage":
    """Render a page turned upright, as large as every provider reads it.

    Parameters
    ----------
    document
        The open PDF.
    page_index
        The page (0-based).
    rotation
        The clockwise rotation that makes the page's content upright.

    Returns
    -------
    UprightImage
        The page image.
    """

    page = document[page_index]
    zoom = _upright_zoom(
        height_pt=page.rect.height, rotation=rotation, width_pt=page.rect.width
    )
    # PyMuPDF renders the displayed page, and prerotate turns the image clockwise.
    matrix = pymupdf.Matrix(zoom, zoom).prerotate(rotation)
    pixmap = page.get_pixmap(alpha=False, matrix=matrix)
    return UprightImage(
        data=pixmap.tobytes("jpeg", jpg_quality=_JPEG_QUALITY),
        dpi=zoom * _POINTS_PER_INCH,
        height_px=pixmap.height,
        width_px=pixmap.width,
    )


def _to_displayed(*, rotation: Angle, u: float, v: float) -> tuple[float, float]:
    """Map a point on the upright image to the displayed page, as fractions.

    Parameters
    ----------
    rotation
        The clockwise rotation that turned the displayed page upright.
    u
        The point's distance from the upright image's left edge, as a fraction of
        its width.
    v
        The point's distance from its top edge, as a fraction of its height.

    Returns
    -------
    tuple[float, float]
        The point's distance from the displayed page's left edge and from its top
        edge, as fractions of its width and height.
    """

    if rotation == 0:
        return u, v
    if rotation == 90:  # noqa: PLR2004 - a rotation in degrees
        return v, 1 - u
    if rotation == 180:  # noqa: PLR2004 - a rotation in degrees
        return 1 - u, 1 - v
    return 1 - v, u


def _to_upright(*, rotation: Angle, s: float, t: float) -> tuple[float, float]:
    """Map a point on the displayed page to the upright image, as fractions.

    The reverse of `_to_displayed`.

    Parameters
    ----------
    rotation
        The clockwise rotation that turns the displayed page upright.
    s
        The point's distance from the displayed page's left edge, as a fraction of
        its width.
    t
        The point's distance from its top edge, as a fraction of its height.

    Returns
    -------
    tuple[float, float]
        The point's distance from the upright image's left edge and from its top
        edge, as fractions of its width and height.
    """

    if rotation == 0:
        return s, t
    if rotation == 90:  # noqa: PLR2004 - a rotation in degrees
        return 1 - t, s
    if rotation == 180:  # noqa: PLR2004 - a rotation in degrees
        return 1 - s, 1 - t
    return t, 1 - s


def _upright_zoom(*, height_pt: float, rotation: Angle, width_pt: float) -> float:
    """Find the largest zoom whose upright image every provider reads unshrunk.

    Parameters
    ----------
    height_pt
        The displayed page's height in points.
    rotation
        The clockwise rotation that makes the page's content upright.
    width_pt
        The displayed page's width in points.

    Returns
    -------
    float
        Pixels per point, at most `_MAX_DPI` / 72.
    """

    across, down = (
        (width_pt, height_pt) if rotation in {0, 180} else (height_pt, width_pt)
    )

    def fits(zoom: float) -> bool:
        """Tell whether the image at this zoom fits, counting part pixels as whole."""

        return _fits_every_provider(
            height_px=math.ceil(down * zoom), width_px=math.ceil(across * zoom)
        )

    highest = _MAX_DPI / _POINTS_PER_INCH
    if fits(highest):
        return highest
    # The image only grows with the zoom, so halve the range that holds the largest
    # zoom that fits.
    low, high = 0.0, highest
    for _ in range(_ZOOM_SEARCH_STEPS):
        middle = (low + high) / 2
        if fits(middle):
            low = middle
        else:
            high = middle
    return low


@dataclass(frozen=True)
class UprightImage:
    """A page image turned upright, as sent to the models.

    Attributes
    ----------
    data
        The JPEG image.
    dpi
        Its resolution, in pixels per inch of the page.
    height_px
        Its height in pixels.
    width_px
        Its width in pixels.
    """

    data: bytes
    dpi: float
    height_px: int
    width_px: int


class PdfWorker:
    """Run every PyMuPDF call of page extraction on one thread, one at a time.

    Use it in an ``async with`` block, which opens the PDF on the worker's thread and
    closes it when the block ends.

    Parameters
    ----------
    path
        The PDF.

    Examples
    --------
    ::

        async with PdfWorker(pdf.path) as worker:
            image = await worker.page_image(page_index=0, rotation=90)
    """

    def __init__(self, path: Path) -> None:
        """Hold the PDF's path; nothing is opened until the block starts."""

        self._document: pymupdf.Document | None = None
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="pydelity-pymupdf"
        )
        self._path = path

    async def __aenter__(self) -> Self:
        """Open the PDF on the worker's thread.

        Returns
        -------
        Self
            The worker.
        """

        loop = asyncio.get_running_loop()
        self._document = await loop.run_in_executor(
            self._executor, pymupdf.open, self._path
        )
        return self

    async def __aexit__(
        self,
        error_type: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the PDF on the worker's thread, after any call still running.

        Parameters
        ----------
        error_type
            The type of the error that ended the block, if one did.
        error
            The error, if one did.
        traceback
            Its traceback, if one did.
        """

        document, self._document = self._document, None
        try:
            if document is not None:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(self._executor, document.close)
        finally:
            self._executor.shutdown(wait=False)

    async def call[ResultT](
        self, function: Callable[[pymupdf.Document], ResultT]
    ) -> ResultT:
        """Run a function of the open PDF on the worker's thread.

        Parameters
        ----------
        function
            Takes the open PDF and returns a result. It must not keep PyMuPDF
            objects for use outside the worker.

        Returns
        -------
        ResultT
            What the function returned.

        Raises
        ------
        RuntimeError
            If the PDF is not open, outside the ``async with`` block.
        """

        document = self._document
        if document is None:
            raise RuntimeError("PdfWorker is used outside its async with block")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, function, document)

    async def crop(
        self, *, box_pt: Sequence[float], page_index: int, rotation: Angle
    ) -> bytes:
        """Render part of a page, such as a figure, as an upright PNG image.

        Parameters
        ----------
        box_pt
            The part to render, ``[x0, y0, x1, y1]`` in points on the displayed page.
        page_index
            The page (0-based).
        rotation
            The clockwise rotation that makes the page's content upright.

        Returns
        -------
        bytes
            The PNG image, at 200 DPI.
        """

        return await self.call(
            lambda document: _render_crop(
                document, box_pt=box_pt, page_index=page_index, rotation=rotation
            )
        )

    async def page_image(self, *, page_index: int, rotation: Angle) -> UprightImage:
        """Render a page turned upright, as large as every provider reads it.

        Parameters
        ----------
        page_index
            The page (0-based).
        rotation
            The clockwise rotation that makes the page's content upright.

        Returns
        -------
        UprightImage
            The JPEG image and its size.
        """

        return await self.call(
            lambda document: _render_upright(
                document, page_index=page_index, rotation=rotation
            )
        )


def grid_box_to_points(
    box: Sequence[int], *, height_pt: float, rotation: Angle, width_pt: float
) -> list[float]:
    """Map a box on the upright image's grid to points on the displayed page.

    Parameters
    ----------
    box
        ``[x0, y0, x1, y1]`` in `GRID` units across and down the upright image.
    height_pt
        The displayed page's height in points.
    rotation
        The clockwise rotation that turned the displayed page upright.
    width_pt
        The displayed page's width in points.

    Returns
    -------
    list[float]
        ``[x0, y0, x1, y1]`` in points on the displayed page, origin top left,
        inside the page and rounded to 0.01.

    Examples
    --------
    On a page whose content a quarter turn clockwise makes upright, a box in the
    upright image's top-left corner lies in the displayed page's bottom-left corner:

    >>> grid_box_to_points([0, 0, 100, 250], height_pt=792, rotation=90, width_pt=612)
    [0.0, 712.8, 153.0, 792.0]
    """

    corners = [
        _to_displayed(rotation=rotation, u=box[0] / GRID, v=box[1] / GRID),
        _to_displayed(rotation=rotation, u=box[2] / GRID, v=box[3] / GRID),
    ]
    xs = [_clamp(s * width_pt, high=width_pt, low=0) for s, _ in corners]
    ys = [_clamp(t * height_pt, high=height_pt, low=0) for _, t in corners]
    return [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)]


def points_box_to_grid(
    box_pt: Sequence[float], *, height_pt: float, rotation: Angle, width_pt: float
) -> list[int]:
    """Map a box in points on the displayed page to the upright image's grid.

    The reverse of `grid_box_to_points`, rounded to whole grid units.

    Parameters
    ----------
    box_pt
        ``[x0, y0, x1, y1]`` in points on the displayed page, origin top left.
    height_pt
        The displayed page's height in points.
    rotation
        The clockwise rotation that turns the displayed page upright.
    width_pt
        The displayed page's width in points.

    Returns
    -------
    list[int]
        ``[x0, y0, x1, y1]`` in `GRID` units across and down the upright image,
        from 0 to `GRID`.

    Examples
    --------
    >>> points_box_to_grid([0, 712.8, 153, 792], height_pt=792, rotation=90,
    ...     width_pt=612)
    [0, 0, 100, 250]
    """

    corners = [
        _to_upright(rotation=rotation, s=box_pt[0] / width_pt, t=box_pt[1] / height_pt),
        _to_upright(rotation=rotation, s=box_pt[2] / width_pt, t=box_pt[3] / height_pt),
    ]
    us = [round(_clamp(u * GRID, high=GRID, low=0)) for u, _ in corners]
    vs = [round(_clamp(v * GRID, high=GRID, low=0)) for _, v in corners]
    return [min(us), min(vs), max(us), max(vs)]

"""The report's page images: ``report/pages/<NNNN>.jpg``, about 1000 pixels wide.

An image is rendered only when it is missing. All of them are rendered again when
``report/manifest.json`` names another PDF, is missing or cannot be read. Rendering
reads the whole PDF, so async code calls `render_pages` with `asyncio.to_thread`.
"""

# Standard Library
import os
import secrets

from pathlib import Path

# Third Party Library
import pymupdf

from loguru import logger

# Package Library
from pydelity.report.schemas import PageImage, ReportManifest
from pydelity.schema_versions import MANIFEST_SCHEMA_VERSION
from pydelity.utils.files import (
    load_model,
    remove_stale_temp_files,
    write_model_atomic,
)

# The JPEG quality of the page images, from 0 to 100.
_JPEG_QUALITY = 80

# How wide each page image is, in pixels.
_PAGE_WIDTH_PX = 1000

# The manifest's file name in the report folder.
MANIFEST_FILE_NAME = "manifest.json"

# The report folder's name in the output folder.
REPORT_FOLDER_NAME = "report"


def _image_path(index: int) -> str:
    """Return a page image's path, relative to the output folder.

    Parameters
    ----------
    index
        The page's index.

    Returns
    -------
    str
        Such as ``report/pages/0007.jpg``.
    """

    return f"{REPORT_FOLDER_NAME}/pages/{index:04d}.jpg"


def _render_page(*, document: pymupdf.Document, index: int, path: Path) -> PageImage:
    """Render one displayed page as a JPEG image and save it atomically.

    Parameters
    ----------
    document
        The open PDF.
    index
        The page's index.
    path
        The image file to write.

    Returns
    -------
    PageImage
        The image's entry in the manifest.
    """

    page = document[index]
    # page.rect is the displayed page, with its rotation applied, as is the pixmap.
    zoom = _PAGE_WIDTH_PX / page.rect.width
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    temp_path = path.with_name(f"{path.name}.tmp-{secrets.token_hex(8)}")
    temp_path.write_bytes(pixmap.tobytes(jpg_quality=_JPEG_QUALITY, output="jpg"))
    os.replace(temp_path, path)
    return PageImage(
        file=_image_path(index),
        height_px=pixmap.height,
        index=index,
        width_px=pixmap.width,
    )


def render_pages(
    *, output_folder: Path, pdf_path: Path, pdf_sha256: str
) -> ReportManifest:
    """Render the page images that are missing, or all of them for another PDF.

    Parameters
    ----------
    output_folder
        The output folder.
    pdf_path
        The PDF.
    pdf_sha256
        The PDF's SHA-256, which the manifest records.

    Returns
    -------
    ReportManifest
        The manifest, as written to ``report/manifest.json``.
    """

    pages_folder = output_folder / REPORT_FOLDER_NAME / "pages"
    pages_folder.mkdir(exist_ok=True, parents=True)
    remove_stale_temp_files(pages_folder)
    manifest_path = output_folder / REPORT_FOLDER_NAME / MANIFEST_FILE_NAME
    saved = load_model(model_type=ReportManifest, path=manifest_path).model
    known = (
        {page.index: page for page in saved.pages}
        if saved is not None and saved.pdf_sha256 == pdf_sha256
        else {}
    )
    if not known:
        # Images of another PDF, or of a rendering that never finished, go first.
        for old in pages_folder.glob("*.jpg"):
            old.unlink()

    images = []
    rendered = 0
    with pymupdf.open(pdf_path) as document:
        for index in range(document.page_count):
            image = known.get(index)
            if image is None or not (output_folder / image.file).is_file():
                image = _render_page(
                    document=document,
                    index=index,
                    path=output_folder / _image_path(index),
                )
                rendered += 1
            images.append(image)

    manifest = ReportManifest(
        pages=images, pdf_sha256=pdf_sha256, schema_version=MANIFEST_SCHEMA_VERSION
    )
    write_model_atomic(model=manifest, path=manifest_path)
    logger.debug(
        "Page images: {rendered} rendered, {kept} kept",
        kept=len(images) - rendered,
        rendered=rendered,
    )
    return manifest

"""The report's data: ``report/manifest.json``, which lists the rendered page images."""

# Third Party Library
from pydantic import BaseModel, ConfigDict


class _Output(BaseModel):
    """Base for the models stored in output files."""

    model_config = ConfigDict(use_attribute_docstrings=True)


class PageImage(_Output):
    """One rendered page image."""

    file: str
    """The image's path, relative to the output folder."""

    height_px: int
    """The image's height in pixels."""

    index: int
    """The page's index."""

    width_px: int
    """The image's width in pixels."""


class ReportManifest(_Output):
    """The contents of ``report/manifest.json``: the page images of one PDF."""

    pages: list[PageImage]
    """Every page's image, in page order."""

    pdf_sha256: str
    """The SHA-256 of the PDF the images show."""

    schema_version: str
    """The version of this file's schema, ``"MAJOR.MINOR"``."""

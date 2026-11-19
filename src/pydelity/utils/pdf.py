"""Opening a PDF: checking that it can be read and measuring its identity."""

# Standard Library
import hashlib

from dataclasses import dataclass
from pathlib import Path

# Third Party Library
import pymupdf

# Package Library
from pydelity.errors import PdfError


def _count_pages(path: Path) -> int:
    """Open a file as a PDF with PyMuPDF and count its pages.

    Parameters
    ----------
    path
        The file to open.

    Returns
    -------
    int
        The page count, at least 1.

    Raises
    ------
    PdfError
        If PyMuPDF cannot open the file as a PDF, or the PDF needs a password or has no
        pages.
    """

    try:
        # filetype="pdf" parses the file as a PDF whatever its extension, instead of
        # letting PyMuPDF open images, e-books or text files as documents.
        document = pymupdf.open(path, filetype="pdf")
    except (pymupdf.FileDataError, pymupdf.FileNotFoundError) as error:
        raise PdfError(f"{path}: cannot be opened as a PDF ({error})") from error

    with document:
        if document.needs_pass:
            raise PdfError(f"{path}: the PDF is password-protected")
        if document.page_count == 0:
            raise PdfError(f"{path}: the PDF has no pages")
        return document.page_count


def _sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file, read in chunks.

    Parameters
    ----------
    path
        The file to hash.

    Returns
    -------
    str
        The 64-character lowercase hex digest.
    """

    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


@dataclass(frozen=True)
class PdfInfo:
    """A PDF's identity and size, read when it is opened.

    Attributes
    ----------
    bytes
        The file's size in bytes.
    page_count
        The number of pages, at least 1.
    path
        The path the PDF was opened from, as given.
    sha256
        The full SHA-256 hex digest of the file (64 characters), which identifies the
        PDF in every output.
    """

    bytes: int
    page_count: int
    path: Path
    sha256: str

    @property
    def name(self) -> str:
        """The PDF's file name, without its folder."""

        return self.path.name


def open_pdf(path: Path) -> PdfInfo:
    """Open a PDF and return its size, page count and SHA-256.

    This reads the whole file, so async code should call it with `asyncio.to_thread`.

    Parameters
    ----------
    path
        The PDF to open.

    Returns
    -------
    PdfInfo
        The PDF's identity and size.

    Raises
    ------
    PdfError
        If the file is missing, not a file, empty, not a readable PDF,
        password-protected or without pages. The message names the file and the
        reason.

    Examples
    --------
    >>> info = open_pdf(Path("report.pdf"))  # doctest: +SKIP
    >>> info.page_count, info.sha256[:12]  # doctest: +SKIP
    (42, '9f86d081884c')
    """

    if not path.exists():
        raise PdfError(f"{path}: no such file")
    if not path.is_file():
        raise PdfError(f"{path}: not a file")

    size = path.stat().st_size
    if size == 0:
        raise PdfError(f"{path}: the file is empty")

    return PdfInfo(
        bytes=size, page_count=_count_pages(path), path=path, sha256=_sha256(path)
    )

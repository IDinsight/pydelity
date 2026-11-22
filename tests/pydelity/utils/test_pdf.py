"""Tests for opening a PDF before anything else happens."""

# Standard Library
from collections.abc import Callable
from pathlib import Path

# Third Party Library
import pymupdf
import pytest

# Package Library
from pydelity.errors import PdfError
from pydelity.utils.pdf import open_pdf


def test_a_password_protected_pdf_is_refused(
    pdf_path: Callable[[str], Path], tmp_path: Path
) -> None:
    """A PDF that needs a password to open raises `PdfError` saying so."""

    path = tmp_path / "locked.pdf"
    with pymupdf.open(pdf_path("irs_form_1040a_1965_scan.pdf")) as document:
        document.save(
            path,
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw="owner-secret",
            user_pw="user-secret",
        )

    with pytest.raises(PdfError, match=r"locked\.pdf: .*password-protected"):
        open_pdf(path)


def test_a_text_file_named_pdf_cannot_be_opened(tmp_path: Path) -> None:
    """A file that is not a PDF raises `PdfError` naming the file and the reason."""

    path = tmp_path / "notes.pdf"
    path.write_text("These are notes, not a PDF.\n", encoding="utf-8")

    with pytest.raises(PdfError, match=r"notes\.pdf: cannot be opened as a PDF"):
        open_pdf(path)


def test_an_empty_file_is_not_a_pdf(tmp_path: Path) -> None:
    """An empty file raises `PdfError` naming the file and the reason."""

    path = tmp_path / "empty.pdf"
    path.touch()

    with pytest.raises(PdfError, match=r"empty\.pdf: the file is empty"):
        open_pdf(path)

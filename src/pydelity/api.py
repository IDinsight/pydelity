"""pydelity's Python API.

Each function is written once as a coroutine (``arun``); its sync version has the same
name without the ``a`` (``run``), takes the same arguments and runs the coroutine with
`pydelity.utils.coroutines.run_coroutine`.
"""

# Standard Library
import asyncio
import os

from pathlib import Path

# Third Party Library
from loguru import logger

# Package Library
from pydelity.utils.coroutines import run_coroutine
from pydelity.utils.pdf import open_pdf


async def arun(pdf: str | os.PathLike[str]) -> None:
    """Run pydelity on a PDF.

    So far the run opens the PDF and logs its name, page count, size and SHA-256; the
    survey and the rest of the run come in later versions.

    Parameters
    ----------
    pdf
        The PDF to process.

    Raises
    ------
    PdfError
        If the PDF is missing, empty, password-protected or cannot be opened.
    """

    path = Path(pdf)
    logger.info("Opening {path}", path=path)
    info = await asyncio.to_thread(open_pdf, path)
    logger.info(
        "Opened {name}: {pages}, {size:,} bytes, SHA-256 {sha256}",
        name=info.name,
        pages=f"{info.page_count} page" + ("" if info.page_count == 1 else "s"),
        sha256=info.sha256,
        size=info.bytes,
    )
    logger.info("Run finished")


def run(pdf: str | os.PathLike[str]) -> None:
    """Run pydelity on a PDF; the sync version of `arun`.

    Parameters
    ----------
    pdf
        The PDF to process.

    Raises
    ------
    PdfError
        If the PDF is missing, empty, password-protected or cannot be opened.
    """

    run_coroutine(arun(pdf))

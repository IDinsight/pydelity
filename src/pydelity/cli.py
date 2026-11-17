"""The ``pydelity`` command.

The command only parses its options, turns on logging and calls the Python API; all
behavior lives in the library.
"""

# Standard Library
import sys

from pathlib import Path
from typing import Annotated

# Third Party Library
import typer

from loguru import logger

# Package Library
from pydelity import __version__
from pydelity.api import run
from pydelity.errors import PdfError, PydelityError

# Exit codes: the run failed; the input (settings, API key or PDF) is invalid.
_EXIT_FAILED = 1
_EXIT_INVALID_INPUT = 2

_LOG_FORMAT = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}"

# Local variables are never shown in tracebacks: they can hold API keys.
app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


def _enable_logging() -> None:
    """Send pydelity's log messages to stderr at INFO level."""

    logger.remove()
    logger.add(sys.stderr, format=_LOG_FORMAT, level="INFO")
    logger.enable("pydelity")


def _show_version(value: bool) -> None:
    """Print the version and stop, when ``--version`` is given.

    Parameters
    ----------
    value
        Whether ``--version`` was given.

    Raises
    ------
    typer.Exit
        After printing the version.
    """

    if value:
        typer.echo(f"pydelity {__version__}")
        raise typer.Exit


@app.command(help="Turn a PDF into faithful, structured JSON.")
def _pydelity(
    pdf: Annotated[
        Path, typer.Argument(help="The PDF to process.", show_default=False)
    ],
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_show_version,
            help="Show the version and exit.",
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Run pydelity on a PDF from the command line.

    Parameters
    ----------
    pdf
        The PDF to process.
    version
        Whether to print the version and exit instead (handled by `_show_version`).

    Raises
    ------
    typer.Exit
        With exit code 2 when the PDF cannot be opened, or 1 when the run fails.
    """

    _enable_logging()
    try:
        run(pdf)
    except PdfError as error:
        logger.error(str(error))
        raise typer.Exit(code=_EXIT_INVALID_INPUT) from error
    except PydelityError as error:
        logger.error(str(error))
        raise typer.Exit(code=_EXIT_FAILED) from error


def main() -> None:
    """Run the ``pydelity`` command (the console script's entry point)."""

    app(prog_name="pydelity")

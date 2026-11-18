"""The ``pydelity`` command.

The command parses its options, sets up logging and calls the Python API. The
library does the rest.
"""

# Standard Library
import sys

from functools import partial
from pathlib import Path
from typing import Annotated

# Third Party Library
import typer

from loguru import logger

# Package Library
from pydelity import __version__
from pydelity.api import arun_with_questions
from pydelity.costs.budget import SpendDeclinedError
from pydelity.costs.schemas import CostEstimate, MaxCostWarning
from pydelity.errors import (
    BudgetExceededError,
    ConfigError,
    MissingApiKeyError,
    PdfError,
    PydelityError,
)
from pydelity.utils.coroutines import run_coroutine

# Exit code for a run that failed.
_EXIT_FAILED = 1

# Exit code for an invalid setting, API key or PDF.
_EXIT_INVALID_INPUT = 2

# Exit code for a run the user declined, or that could not ask because input is not a
# terminal and --yes was not given.
_EXIT_STOPPED = 3

_LOG_FORMAT = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}"

# Hide local variables in tracebacks because they can hold API keys.
app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


def _ask(*, question: str, yes: bool) -> bool:
    """Ask a yes-or-no question on the terminal, with no as the default.

    Parameters
    ----------
    question
        The question.
    yes
        Whether ``--yes`` was given, which answers yes without asking.

    Returns
    -------
    bool
        The answer. ``False`` without asking when input is not a terminal and
        ``--yes`` was not given.
    """

    if yes:
        return True
    if not sys.stdin.isatty():
        logger.error(
            "Input is not a terminal, so pydelity cannot ask; pass --yes to go ahead "
            "without asking"
        )
        return False
    return typer.confirm(question, default=False, err=True)


def _confirm_spend(estimate: CostEstimate, *, yes: bool) -> bool:
    """Ask whether to go ahead and spend, after the estimate has been logged.

    Parameters
    ----------
    estimate
        The cost estimate, already shown in the log.
    yes
        Whether ``--yes`` was given.

    Returns
    -------
    bool
        Whether to go ahead.
    """

    return _ask(question="Go ahead with the model requests?", yes=yes)


def _decide_over_max_cost(warning: MaxCostWarning, *, yes: bool) -> bool:
    """Ask whether to go over ``max_cost``, after the warning has been logged.

    Parameters
    ----------
    warning
        The warning's details, already shown in the log.
    yes
        Whether ``--yes`` was given.

    Returns
    -------
    bool
        Whether the run may go over ``max_cost``.
    """

    return _ask(
        question="Go ahead, even though this run could go over max_cost?", yes=yes
    )


def _enable_logging(*, verbose: bool) -> None:
    """Send pydelity's log messages to stderr.

    Parameters
    ----------
    verbose
        Whether to log details (DEBUG level) as well as progress (INFO level).
    """

    logger.remove()
    logger.add(sys.stderr, format=_LOG_FORMAT, level="DEBUG" if verbose else "INFO")
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
def _pydelity(  # noqa: PLR0913, PLR0917 - Typer makes each parameter an option
    pdf: Annotated[
        Path | None,
        typer.Argument(
            help="The PDF to process. Overrides pdf in the config file.",
            show_default=False,
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="A JSON or YAML file of settings.",
            metavar="FILE",
            show_default=False,
        ),
    ] = None,
    instructions: Annotated[
        str | None,
        typer.Option(
            help="Extra instructions for the model about this PDF.",
            metavar="TEXT",
            show_default=False,
        ),
    ] = None,
    language: Annotated[
        list[str] | None,
        typer.Option(
            help="A language of the PDF as a BCP-47 tag, such as en; repeat for more.",
            metavar="TAG",
            show_default=False,
        ),
    ] = None,
    output_dir: Annotated[
        Path | None,
        typer.Option(
            help="The output folder [default: pydelity-output/<PDF name>].",
            metavar="DIR",
            show_default=False,
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            help="The model, as <provider>:<model-id> with provider anthropic or "
            "openai [default: anthropic:claude-opus-5-5].",
            metavar="MODEL",
            show_default=False,
        ),
    ] = None,
    max_cost: Annotated[
        str | None,
        typer.Option(
            help="The most the output folder's model requests may cost, in US dollars.",
            metavar="USD",
            show_default=False,
        ),
    ] = None,
    overwrite: Annotated[
        bool | None,
        typer.Option(
            "--overwrite",
            help="Redo steps whose outputs could be reused.",
            show_default=False,
        ),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Go ahead without asking, even over max_cost (after its warning).",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose", "-v", help="Also log details, such as the settings in use."
        ),
    ] = False,
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

    Options left out fall back to the config file, then to the defaults.

    Parameters
    ----------
    pdf
        The PDF to process.
    config
        A JSON or YAML file of settings.
    instructions
        Extra instructions for the model.
    language
        The PDF's languages as BCP-47 tags.
    output_dir
        The output folder.
    model
        The model, as ``<provider>:<model-id>``.
    max_cost
        The spending limit in US dollars, checked when settings are validated.
    overwrite
        Whether to redo steps whose outputs could be reused.
    yes
        Whether to go ahead without asking.
    verbose
        Whether to log details as well as progress.
    version
        Whether to print the version and exit instead (handled by `_show_version`).

    Raises
    ------
    typer.Exit
        With exit code 2 when a setting, the API key or the PDF is invalid, 3 when the
        run stops at an answer or because it cannot ask, or 1 when the run fails.
    """

    _enable_logging(verbose=verbose)
    given = {
        "instructions": instructions,
        "languages": language or None,
        "max_cost": max_cost,
        "model": model,
        "output_dir": output_dir,
        "overwrite": overwrite,
    }
    settings = {name: value for name, value in given.items() if value is not None}
    try:
        run_coroutine(
            arun_with_questions(
                pdf,
                config=config,
                confirm=partial(_confirm_spend, yes=yes),
                decide_over_max_cost=partial(_decide_over_max_cost, yes=yes),
                **settings,
            )
        )
    except (ConfigError, MissingApiKeyError, PdfError) as error:
        logger.error(str(error))
        raise typer.Exit(code=_EXIT_INVALID_INPUT) from error
    except (BudgetExceededError, SpendDeclinedError) as error:
        logger.error(str(error))
        raise typer.Exit(code=_EXIT_STOPPED) from error
    except PydelityError as error:
        logger.error(str(error))
        raise typer.Exit(code=_EXIT_FAILED) from error


def main() -> None:
    """Run the ``pydelity`` command (the console script's entry point)."""

    app(prog_name="pydelity")

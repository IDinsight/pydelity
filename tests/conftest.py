"""Shared pytest fixtures for the pydelity test suite.

Every test runs with dummy provider API keys and with both provider base URLs pointed
at a closed loopback port, so no test can reach a real provider or spend money. Tests
that need a provider start the stand-in server from `tests.fixtures.mock_providers`
with the ``mock_providers`` fixture, which points the base URLs at it instead.
"""

# Standard Library
import json
import socket
import sys

from collections.abc import Callable, Iterator, Sequence
from functools import cache
from pathlib import Path

# Third Party Library
import pytest
import typer.testing

from loguru import logger
from typer.testing import CliRunner, Result

# Package Library
from pydelity.cli import app
from pydelity.surveying.probe import probe_pdf
from pydelity.surveying.schemas import Facts
from tests.fixtures.mock_providers import MockProviders, read_page_answers

# The canned answers for committed test PDFs, in files named after the PDF: the
# survey's answer, and page extraction's answers by page and agent.
_FIXTURES_DIR = Path(__file__).absolute().parent / "fixtures"

# The committed test PDFs (see SOURCES.md there).
_PDF_DIR = _FIXTURES_DIR / "pdfs"

# The provider environment variables every test controls.
_PROVIDER_VARIABLES = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_ORG_ID",
    "OPENAI_PROJECT_ID",
)

# The API key every test gets unless it removes it. No provider accepts it.
DUMMY_API_KEY = "dummy-key-for-tests"  # pragma: allowlist secret


def _closed_port() -> int:
    """Find a loopback port that nothing listens on.

    Returns
    -------
    int
        The port; a connection to it is refused.
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(autouse=True)
def _no_provider_access(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[None]:
    """Keep every test away from real providers, the repo folder and stray logs.

    Real provider keys are replaced by a dummy one, both base URLs point at a closed
    loopback port, and the current folder is the test's temporary folder, so the
    default output folder never lands in the repo. PydanticAI's first-run banner is
    turned off. pydelity's logging is turned off again afterwards.
    """

    for name in _PROVIDER_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    port = _closed_port()
    monkeypatch.setenv("ANTHROPIC_API_KEY", DUMMY_API_KEY)
    monkeypatch.setenv("ANTHROPIC_BASE_URL", f"http://127.0.0.1:{port}")
    monkeypatch.setenv("OPENAI_API_KEY", DUMMY_API_KEY)
    monkeypatch.setenv("OPENAI_BASE_URL", f"http://127.0.0.1:{port}/v1")
    monkeypatch.setenv("PYDANTIC_AI_NO_BANNER", "1")
    monkeypatch.chdir(tmp_path)
    yield
    logger.disable("pydelity")


@cache
def _probed(name: str) -> Facts:
    """Measure a committed test PDF once per test session.

    Parameters
    ----------
    name
        The PDF's file name in ``tests/fixtures/pdfs``.

    Returns
    -------
    Facts
        The probe's facts.
    """

    return probe_pdf(_PDF_DIR / name)


@pytest.fixture
def canned_answers() -> Callable[[str], dict[str, object]]:
    """Return a function that gives a test PDF's canned answers for the stand-in.

    The survey's answer gives the profile whose labels the page answers use, and
    every page answer passes page extraction's checks against it.

    Returns
    -------
    Callable[[str], dict[str, object]]
        Takes the PDF's file name in ``tests/fixtures/pdfs`` and returns
        `MockProviders`' ``answers`` (the survey's answer) and ``page_answers`` (the
        extraction and verifier answers for each page), as keyword arguments.
    """

    def answers(name: str) -> dict[str, object]:
        """Read the canned answers for one committed test PDF."""

        file_name = f"{Path(name).stem}.json"
        survey = json.loads(
            (_FIXTURES_DIR / "survey_answers" / file_name).read_text(encoding="utf-8")
        )
        pages = read_page_answers(_FIXTURES_DIR / "extraction_answers" / file_name)
        return {"answers": [survey], "page_answers": pages}

    return answers


@pytest.fixture
def facts_of() -> Callable[[str], Facts]:
    """Return a function that gives a committed test PDF's measured facts.

    Returns
    -------
    Callable[[str], Facts]
        Takes the PDF's file name; measures each PDF once per session.
    """

    return _probed


@pytest.fixture
def log_messages() -> Iterator[list[tuple[str, str]]]:
    """Capture pydelity's log messages, as the caller would after enabling them.

    Yields
    ------
    list[tuple[str, str]]
        Each message's level name and text, in order.
    """

    captured: list[tuple[str, str]] = []
    handler = logger.add(
        lambda message: captured.append(
            (message.record["level"].name, message.record["message"])
        ),
        level="DEBUG",
    )
    logger.enable("pydelity")
    yield captured
    logger.remove(handler)
    logger.disable("pydelity")


@pytest.fixture
def mock_providers(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Callable[..., MockProviders]]:
    """Return a function that starts the stand-in provider server for the test.

    The function takes `MockProviders`' keyword arguments, starts the server, points
    both providers' base URLs and keys at it, and returns it. Every server started is
    stopped after the test.

    Yields
    ------
    Callable[..., MockProviders]
        Starts a server.
    """

    started: list[MockProviders] = []

    def start(**options: object) -> MockProviders:
        """Start a stand-in server with these options and send both SDKs to it."""

        mock = MockProviders(**options)  # ty: ignore[invalid-argument-type]
        mock.start()
        started.append(mock)
        for name, value in mock.environment().items():
            monkeypatch.setenv(name, value)
        return mock

    yield start
    for mock in started:
        mock.stop()


@pytest.fixture
def pdf_path() -> Callable[[str], Path]:
    """Return a function that gives a committed test PDF's absolute path.

    Returns
    -------
    Callable[[str], Path]
        Takes the PDF's file name in ``tests/fixtures/pdfs``.
    """

    def path(name: str) -> Path:
        """Return the absolute path of one committed test PDF."""

        return _PDF_DIR / name

    return path


@pytest.fixture
def run_cli(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[..., Result]]:
    """Return a function that runs the ``pydelity`` command in-process.

    The function takes the command's arguments, the text to type at its questions
    (``input``) and whether input should look like a terminal (``terminal``). The
    command replaces loguru's handlers with its own, so they are reset afterwards.

    Yields
    ------
    Callable[..., Result]
        Runs the command and returns its result, with stdout and stderr apart.
    """

    def invoke(
        arguments: Sequence[str], *, input: str | None = None, terminal: bool = False
    ) -> Result:
        """Run the command with these arguments and this input."""

        # CliRunner's stdin is never a terminal. The command asks its questions only
        # on a terminal, so a test of the questions makes CliRunner's stdin claim to
        # be one.
        monkeypatch.setattr(
            typer.testing._NamedTextIOWrapper,
            "isatty",
            lambda self: terminal,
        )
        return CliRunner().invoke(app, list(arguments), input=input)

    yield invoke
    logger.remove()
    logger.add(sys.stderr)
    logger.disable("pydelity")


@pytest.fixture
def survey_answer() -> Callable[..., dict[str, object]]:
    """Return a function that writes a well-formed survey answer for some facts.

    The answer passes checks C1 to C7: one label, ``en`` as its language, no ranges,
    and every repeated line of the facts listed once as a content line. Keyword
    arguments replace its top-level keys.

    Returns
    -------
    Callable[..., dict[str, object]]
        Takes the facts (or ``None`` for a PDF with no repeated lines) and any keys
        to replace, and returns the answer as JSON-ready data.
    """

    def answer(facts: Facts | None = None, **changes: object) -> dict[str, object]:
        """Write a well-formed answer for the facts, with some keys replaced."""

        lines = [] if facts is None else facts.repeated_lines
        data: dict[str, object] = {
            "artifacts": [],
            "continuation_notes": [],
            "labels": [
                {
                    "description": "Running text.",
                    "kinds": ["text"],
                    "name": "Body",
                    "role": "body",
                }
            ],
            "languages": ["en"],
            "non_artifact_lines": [
                {"reason": "Part of the content.", "repeated_line_id": line.id}
                for line in lines
            ],
            "notes": [],
            "page_numbering": [],
            "regions": [],
            "rotation": [],
            "start_markers": [],
            "writing_direction": {"default": "ltr", "ranges": []},
        }
        data.update(changes)
        return data

    return answer

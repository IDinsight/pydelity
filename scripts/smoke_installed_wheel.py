#!/usr/bin/env python3
"""Install the built wheel in a fresh virtual environment and run both steps with it.

The script makes a new virtual environment with ``venv`` and installs the wheel with
pip, taking pydelity's dependencies from PyPI. It then starts the stand-in provider
server from ``tests/fixtures/mock_providers.py`` and, for each provider, runs the
``pydelity`` command and the Python API on a committed test PDF, through the survey
and page extraction without a pause. Every run must complete with a page file for each
page, its output folder must load, and the stand-in must have received exactly the
requests listed in `EXPECTED_REQUESTS`, so no run can reach a real provider or spend
money.

It uses the standard library only, so any Python 3.13 or later can run it, on Windows,
macOS or Linux. Run it from anywhere after ``just build``::

    python scripts/smoke_installed_wheel.py [--wheel <wheel file>]

It prints one line per check and exits with 1 if any check fails.
"""

# Standard Library
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

# The stand-in server is a test fixture. Make the repository root importable so the
# script works from any working folder.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Package Library
from tests.fixtures.mock_providers import MockProviders  # noqa: E402

# Python code the installed pydelity runs to check an output folder written by the
# command: every file must load, figure crops included, and the run must have completed
# with a survey and a page file for each page.
_LOAD_CHECK = """
import sys
import pydelity
result = pydelity.load(sys.argv[1])
status = result.record.status if result.record else None
if status != "completed" or result.facts is None or result.survey is None:
    sys.exit(f"run.json status {status!r}; survey saved: {result.survey is not None}")
pages = [page.page_index for page in result.pages]
if pages != list(range(result.record.pdf.page_count)) or not all(
    page.items for page in result.pages
):
    sys.exit(f"page files for page indexes {pages}, some without items")
"""

# The model each provider's runs use.
_MODELS = {"anthropic": "anthropic:claude-opus-5-5", "openai": "openai:gpt-6.2-astra"}

# Environment variables removed before the child processes start, so that only the
# stand-in's base URLs and placeholder keys reach them.
_PROVIDER_VARIABLES = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_BASE_URL",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
)

# Python code the installed pydelity runs to survey the PDF and extract its pages
# through its Python API. It first prints where pydelity was imported from, so the
# script can tell it is the installed copy.
_RUN_CHECK = """
import sys
import pydelity
print(pydelity.__file__, flush=True)
pdf, model, output_dir = sys.argv[1:4]
result = pydelity.run(pdf, model=model, output_dir=output_dir, pause=False)
status = result.record.status if result.record else None
if status != "completed" or result.survey is None:
    sys.exit(f"run() ended with status {status!r}")
pages = [page.page_index for page in result.pages]
if pages != list(range(result.record.pdf.page_count)):
    sys.exit(f"run() returned page files for page indexes {pages}")
if pydelity.load(output_dir) != result:
    sys.exit("load() of the output folder differs from what run() returned")
"""

# The survey answer the stand-in gives, written for the test PDF below.
ANSWER_PATH = REPO_ROOT / "tests/fixtures/survey_answers/irs_form_1040a_1965_scan.json"

# The requests each run sends with the default settings, which run no verifier, as
# (route, status): the survey's upload and its model request, then an extractor request
# for each of the PDF's 2 pages.
EXPECTED_REQUESTS = [("upload", 200)] + [("model", 200)] * 3

# The most seconds the wheel's installation may take, downloads included.
INSTALL_TIMEOUT_SECONDS = 1800

# The extractor and verifier answers the stand-in gives for each page of the test PDF.
PAGE_ANSWERS_PATH = (
    REPO_ROOT / "tests/fixtures/extraction_answers/irs_form_1040a_1965_scan.json"
)

# The test PDF every run surveys and extracts: 2 scanned pages, 85,909 bytes.
PDF_PATH = REPO_ROOT / "tests/fixtures/pdfs/irs_form_1040a_1965_scan.pdf"

# The most seconds one run or check may take.
RUN_TIMEOUT_SECONDS = 300


@dataclass
class _Checks:
    """The checks made so far, printed as they are added."""

    failed: list[str] = field(default_factory=list)
    """The names of the checks that failed."""

    passed: int = 0
    """How many checks passed."""

    def add(self, *, detail: str = "", name: str, ok: bool) -> None:
        """Record and print one check.

        Parameters
        ----------
        detail
            What went wrong, printed under a failed check.
        name
            What was checked.
        ok
            Whether the check passed.
        """

        if ok:
            self.passed += 1
            print(f"PASS {name}", flush=True)
            return
        self.failed.append(name)
        print(f"FAIL {name}", flush=True)
        if detail:
            print("  " + detail.strip().replace("\n", "\n  "), flush=True)


@dataclass(frozen=True)
class _Venv:
    """A virtual environment."""

    path: Path
    """Its folder."""

    def program(self, name: str) -> str:
        """Find a program in the environment, such as ``python`` or ``pydelity``.

        Parameters
        ----------
        name
            The program's name, without ``.exe``.

        Returns
        -------
        str
            The program's full path.

        Raises
        ------
        SystemExit
            If the environment has no such program.
        """

        # Windows puts programs in Scripts\ as .exe files; `which` adds the extension.
        folder = self.path / ("Scripts" if os.name == "nt" else "bin")
        found = shutil.which(name, path=str(folder))
        if found is None:
            raise SystemExit(f"{name} is not in {folder}")
        return found


@dataclass(frozen=True)
class _Smoke:
    """What the runs share."""

    checks: _Checks
    """Where the results go."""

    env: dict[str, str]
    """The child processes' environment, with the stand-in's variables."""

    folder: Path
    """The temporary folder, which holds the output folders."""

    mock: MockProviders
    """The running stand-in server."""

    venv: _Venv
    """The environment pydelity is installed in."""


def _check_api(*, provider: str, smoke: _Smoke) -> None:
    """Survey the PDF and extract its pages through the installed Python API.

    Parameters
    ----------
    provider
        ``anthropic`` or ``openai``.
    smoke
        The environment, folder, stand-in and results the runs share.
    """

    output_dir = smoke.folder / f"api-{provider}"
    before = len(smoke.mock.requests)
    result = _run(
        [
            smoke.venv.program("python"),
            "-c",
            _RUN_CHECK,
            str(PDF_PATH),
            _MODELS[provider],
            str(output_dir),
        ],
        cwd=smoke.folder,
        env=smoke.env,
    )
    lines = result.stdout.splitlines()
    # The child reports its real path. On macOS the temporary folder is a symbolic
    # link (/var to /private/var), so both paths are resolved before comparing.
    imported = Path(lines[0]).resolve() if lines else None
    smoke.checks.add(
        detail=result.stdout + result.stderr,
        name=f"Python API with {provider}: both steps complete and load() matches",
        ok=result.returncode == 0,
    )
    smoke.checks.add(
        detail=f"pydelity was imported from {imported}",
        name=f"Python API with {provider}: pydelity is the installed copy",
        ok=imported is not None and imported.is_relative_to(smoke.venv.path.resolve()),
    )
    _check_requests(name=f"Python API with {provider}", smoke=smoke, start=before)


def _check_command(*, provider: str, smoke: _Smoke) -> None:
    """Survey the PDF and extract its pages with the installed ``pydelity`` command.

    Parameters
    ----------
    provider
        ``anthropic`` or ``openai``.
    smoke
        The environment, folder, stand-in and results the runs share.
    """

    output_dir = smoke.folder / f"command-{provider}"
    before = len(smoke.mock.requests)
    name = f"pydelity --yes --no-pause with {provider}"
    command = [
        smoke.venv.program("pydelity"),
        str(PDF_PATH),
        "--yes",
        "--no-pause",
        "--output-dir",
        str(output_dir),
        "--model",
        _MODELS[provider],
    ]
    result = _run(command, cwd=smoke.folder, env=smoke.env)
    smoke.checks.add(
        detail=result.stdout + result.stderr,
        name=f"{name}: exit code 0",
        ok=result.returncode == 0,
    )

    loaded = _run(
        [smoke.venv.program("python"), "-c", _LOAD_CHECK, str(output_dir)],
        cwd=smoke.folder,
        env=smoke.env,
    )
    smoke.checks.add(
        detail=loaded.stdout + loaded.stderr,
        name=f"{name}: every output file loads, both steps completed",
        ok=loaded.returncode == 0,
    )
    _check_requests(name=name, smoke=smoke, start=before)


def _check_requests(*, name: str, smoke: _Smoke, start: int) -> None:
    """Check that a run sent the stand-in exactly the requests it should.

    Parameters
    ----------
    name
        The run's name, for the check's name.
    smoke
        The stand-in and the results.
    start
        How many requests the stand-in had received before the run.
    """

    seen = [(request.route, request.status) for request in smoke.mock.requests[start:]]
    smoke.checks.add(
        detail=f"requests (route, status): {seen}",
        name=f"{name}: one upload and 5 model requests, all to the stand-in",
        ok=seen == EXPECTED_REQUESTS,
    )


def _check_version(
    *, checks: _Checks, env: dict[str, str], venv: _Venv, wheel: Path
) -> None:
    """Check that ``pydelity --version`` prints the wheel's version.

    Parameters
    ----------
    checks
        Where the result goes.
    env
        The child process's environment.
    venv
        The environment pydelity is installed in.
    wheel
        The installed wheel, whose name holds its version.
    """

    version = wheel.name.split("-")[1]
    result = _run([venv.program("pydelity"), "--version"], cwd=venv.path, env=env)
    checks.add(
        detail=result.stdout + result.stderr,
        name=f"pydelity --version prints {version}",
        ok=result.returncode == 0 and result.stdout.strip() == f"pydelity {version}",
    )


def _child_environment() -> dict[str, str]:
    """Copy this process's environment without any provider key or base URL.

    Returns
    -------
    dict[str, str]
        The environment for the child processes, before the stand-in's variables.
    """

    env = {
        name: value
        for name, value in os.environ.items()
        if name not in _PROVIDER_VARIABLES
    }
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    return env


def _find_wheel(wheel: Path | None) -> Path:
    """Return the wheel to install: the one given, or the only one in ``dist/``.

    Parameters
    ----------
    wheel
        The wheel given on the command line, if any.

    Returns
    -------
    Path
        The wheel's absolute path.

    Raises
    ------
    SystemExit
        If the given wheel does not exist, or ``dist/`` does not hold exactly one.
    """

    if wheel is not None:
        if not wheel.is_file():
            raise SystemExit(f"No such wheel: {wheel}")
        return wheel.resolve()

    found = sorted((REPO_ROOT / "dist").glob("pydelity-*.whl"))
    if len(found) != 1:
        names = ", ".join(path.name for path in found) or "none"
        raise SystemExit(
            f"Expected one pydelity wheel in dist/, found {names}. Run `just build` "
            "or pass --wheel."
        )
    return found[0]


def _install(*, env: dict[str, str], folder: Path, wheel: Path) -> _Venv:
    """Create a virtual environment and install the wheel in it with pip.

    Parameters
    ----------
    env
        The child processes' environment.
    folder
        Where to create the environment.
    wheel
        The wheel to install.

    Returns
    -------
    _Venv
        The environment, with pydelity installed.

    Raises
    ------
    SystemExit
        If the environment cannot be created or the installation fails.
    """

    print(f"Creating a virtual environment in {folder}", flush=True)
    created = _run(
        [sys.executable, "-m", "venv", str(folder)], cwd=folder.parent, env=env
    )
    if created.returncode != 0:
        raise SystemExit(f"venv failed:\n{created.stdout}{created.stderr}")
    venv = _Venv(path=folder)

    print(f"Installing {wheel.name} with pip", flush=True)
    installed = _run(
        [venv.program("python"), "-m", "pip", "install", "--no-input", str(wheel)],
        cwd=folder.parent,
        env=env,
        timeout=INSTALL_TIMEOUT_SECONDS,
    )
    if installed.returncode != 0:
        raise SystemExit(f"pip install failed:\n{installed.stdout}{installed.stderr}")
    return venv


def _run(
    command: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: float = RUN_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    """Run a program without a shell and capture its output.

    Parameters
    ----------
    command
        The program and its arguments.
    cwd
        The working folder.
    env
        The environment.
    timeout
        The most seconds it may take.

    Returns
    -------
    subprocess.CompletedProcess[str]
        The exit code and output. Output that is not UTF-8, such as a Windows code
        page, is decoded with replacement characters rather than failing.
    """

    return subprocess.run(  # noqa: S603 - the programs come from this script
        command,
        capture_output=True,
        check=False,
        cwd=cwd,
        encoding="utf-8",
        env=env,
        errors="replace",
        stdin=subprocess.DEVNULL,
        timeout=timeout,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Install the wheel, run the smoke checks and print their results.

    Parameters
    ----------
    argv
        The command-line arguments, or ``None`` to read them from ``sys.argv``.

    Returns
    -------
    int
        0 when every check passes, 1 otherwise.
    """

    parser = argparse.ArgumentParser(
        description="Install a pydelity wheel in a fresh environment and run the "
        "survey and page extraction on a PDF with it against a stand-in provider "
        "server."
    )
    parser.add_argument(
        "--wheel",
        help="the wheel to install (default: the only pydelity wheel in dist/)",
        type=Path,
    )
    arguments = parser.parse_args(argv)
    wheel = _find_wheel(arguments.wheel)
    answer = json.loads(ANSWER_PATH.read_text(encoding="utf-8"))
    page_answers = json.loads(PAGE_ANSWERS_PATH.read_text(encoding="utf-8"))
    checks = _Checks()

    with tempfile.TemporaryDirectory(
        ignore_cleanup_errors=True, prefix="pydelity-smoke-"
    ) as temporary:
        folder = Path(temporary)
        base_env = _child_environment()
        venv = _install(env=base_env, folder=folder / "venv", wheel=wheel)
        _check_version(checks=checks, env=base_env, venv=venv, wheel=wheel)
        with MockProviders(answers=[answer], page_answers=page_answers) as mock:
            smoke = _Smoke(
                checks=checks,
                env={**base_env, **mock.environment()},
                folder=folder,
                mock=mock,
                venv=venv,
            )
            for provider in _MODELS:
                _check_command(provider=provider, smoke=smoke)
                _check_api(provider=provider, smoke=smoke)

    total = checks.passed + len(checks.failed)
    print(f"{checks.passed} of {total} checks passed", flush=True)
    return 1 if checks.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

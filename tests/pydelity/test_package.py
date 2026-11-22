"""Smoke tests for the installed ``pydelity`` distribution."""

# Standard Library
import json
import os
import subprocess
import sys
import tomllib

from importlib.metadata import version
from pathlib import Path

# Package Library
import pydelity

# Python code that imports pydelity while an audit hook records every file it opens
# in the current folder and every network connection, then prints what was recorded.
_IMPORT_WATCH = """
import json, os, sys
here = os.getcwd()
seen = []
def watch(event, args):
    if event == "open" and isinstance(args[0], str):
        if os.path.abspath(args[0]).startswith(here):
            seen.append(["open", args[0]])
    elif event.startswith("socket.") and event != "socket.__new__":
        seen.append([event, repr(args)[:80]])
sys.addaudithook(watch)
import pydelity
sys.stdout.write("RECORDED " + json.dumps(seen))
"""

# The repo root, two levels above this file's folder (tests/pydelity/).
_REPO_ROOT = Path(__file__).absolute().parents[2]


def test_import_reads_no_settings_opens_no_connection_and_prints_nothing(
    tmp_path: Path,
) -> None:
    """``import pydelity`` in an empty environment prints nothing and touches nothing.

    A ``.env`` file and a config file in the current folder stay unread, and no
    network connection is opened.
    """

    dot_env = "ANTHROPIC_API_KEY=unused\n"  # pragma: allowlist secret
    (tmp_path / ".env").write_text(dot_env, "utf-8")
    (tmp_path / "pydelity.yaml").write_text("model: openai:gpt-6.2-astra\n", "utf-8")
    environment = {
        name: os.environ[name] for name in ("SYSTEMROOT",) if name in os.environ
    }

    done = subprocess.run(  # noqa: S603 - runs this interpreter on fixed code
        [sys.executable, "-c", _IMPORT_WATCH],
        capture_output=True,
        check=True,
        cwd=tmp_path,
        env=environment,
        text=True,
        timeout=120,
    )

    output, recorded = done.stdout.split("RECORDED ")
    assert (output, done.stderr) == ("", "")
    assert json.loads(recorded) == []


def test_installed_package_imports_with_metadata() -> None:
    """``pydelity`` imports, ships ``py.typed`` and has this project's metadata."""

    package_dir = Path(pydelity.__file__).parent
    with (_REPO_ROOT / "pyproject.toml").open("rb") as pyproject:
        project = tomllib.load(pyproject)["project"]

    assert package_dir.name == "pydelity"
    assert (package_dir / "py.typed").is_file()
    assert version("pydelity") == project["version"]


def test_package_loads_from_installed_tree_not_src() -> None:
    """``pydelity`` loads from its installed tree, and ``src`` is not on the path.

    The strict editable install exposes only the files a wheel would contain, so a
    packaging mistake fails the tests. Putting ``src`` on ``sys.path`` (a plain
    editable install, ``PYTHONPATH`` or a pytest ``pythonpath`` setting) would hide
    such mistakes, so this test fails if that happens.
    """

    src_dir = _REPO_ROOT / "src"
    # Not resolved: the strict editable tree links each file back to src/, so
    # resolving symlinks would always point there.
    package_file = Path(pydelity.__file__).absolute()
    path_entries = {Path(entry).absolute() for entry in sys.path if entry}

    assert not package_file.is_relative_to(src_dir)
    assert src_dir not in path_entries


def test_python_dash_m_pydelity_runs_the_command() -> None:
    """``python -m pydelity --version`` prints the installed version."""

    done = subprocess.run(
        [sys.executable, "-m", "pydelity", "--version"],
        capture_output=True,
        check=True,
        text=True,
        timeout=120,
    )

    assert done.stdout == f"pydelity {version('pydelity')}\n"

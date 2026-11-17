"""Smoke tests for the installed ``pydelity`` distribution."""

# Standard Library
import sys
import tomllib

from importlib.metadata import version
from pathlib import Path

# Package Library
import pydelity

# The repo root, two levels above this file's folder (tests/pydelity/).
_REPO_ROOT = Path(__file__).absolute().parents[2]


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

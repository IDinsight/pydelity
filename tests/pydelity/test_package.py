"""Smoke test for the installed ``pydelity`` distribution."""

# Standard Library
from importlib.metadata import version
from pathlib import Path

# Package Library
import pydelity


def test_installed_package_imports_with_metadata() -> None:
    """``pydelity`` imports, ships ``py.typed`` and has installed metadata."""

    package_dir = Path(pydelity.__file__).parent

    assert package_dir.name == "pydelity"
    assert (package_dir / "py.typed").is_file()
    assert version("pydelity")

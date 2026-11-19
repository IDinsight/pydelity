"""Tests for writing output files so that no file is ever left half-written."""

# Standard Library
import os

from pathlib import Path

# Third Party Library
import pytest

# Package Library
from pydelity.utils.files import write_text_atomic


def test_a_write_interrupted_before_the_rename_keeps_the_old_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """If writing fails before the file is replaced, the old content stays.

    No temporary file is left behind, so the folder holds only whole files.
    """

    target = tmp_path / "run.json"
    target.write_text('{"status": "completed"}\n', encoding="utf-8")

    def interrupted(descriptor: int) -> None:
        """Stand in for a write cut short by Ctrl+C before it reaches the disk."""

        raise KeyboardInterrupt

    monkeypatch.setattr(os, "fsync", interrupted)

    with pytest.raises(KeyboardInterrupt):
        write_text_atomic(path=target, text='{"status": "running"}\n')

    assert target.read_text(encoding="utf-8") == '{"status": "completed"}\n'
    assert sorted(path.name for path in tmp_path.iterdir()) == ["run.json"]

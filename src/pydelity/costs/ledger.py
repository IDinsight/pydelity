"""The ``cost.jsonl`` ledger, with one line per model request that returned a response.

pydelity only appends to the file and syncs each line to disk before writing the next,
so an interruption can damage only the last line. Reading skips a damaged last line,
and the next append removes it. A damaged line anywhere else means something else
changed the file, and reading it raises `OutputError`.
"""

# Standard Library
import os
import threading

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO

# Third Party Library
from pydantic import ValidationError

# Package Library
from pydelity.costs.schemas import LedgerEntry
from pydelity.errors import OutputError

# The ledger's name in the output folder.
LEDGER_FILE_NAME = "cost.jsonl"

# Requests can finish at the same time, so appends hold this lock.
_APPEND_LOCK = threading.Lock()

# How much of the file's end is read at a time when looking for the last line break.
_TAIL_CHUNK_BYTES = 4096


@dataclass(frozen=True)
class Ledger:
    """The lines read from ``cost.jsonl``.

    Attributes
    ----------
    damage
        Why the last line was skipped, if it was damaged.
    entries
        The valid lines, in order.
    """

    damage: str | None
    entries: list[LedgerEntry]

    @property
    def spent_usd(self) -> Decimal:
        """The total cost of the priced requests, in US dollars."""

        return sum(
            (entry.cost_usd for entry in self.entries if entry.cost_usd is not None),
            start=Decimal(0),
        )

    @property
    def unpriced_requests(self) -> int:
        """How many requests have no known cost."""

        return sum(1 for entry in self.entries if entry.cost_usd is None)


def _drop_unfinished_line(handle: BinaryIO) -> None:
    """Remove a last line that an interrupted append left without its line break.

    Parameters
    ----------
    handle
        The ledger file, open for reading and writing in binary mode.
    """

    end = handle.seek(0, os.SEEK_END)
    if end == 0:
        return
    handle.seek(end - 1)
    if handle.read(1) == b"\n":
        return

    # Look backwards for the last line break; everything after it is unfinished.
    position = end
    while position > 0:
        start = max(position - _TAIL_CHUNK_BYTES, 0)
        handle.seek(start)
        found = handle.read(position - start).rfind(b"\n")
        if found >= 0:
            handle.truncate(start + found + 1)
            return
        position = start
    handle.truncate(0)


def append_entry(*, entry: LedgerEntry, path: Path) -> None:
    """Append one line to ``cost.jsonl``, flushed and synced to disk.

    If an interrupted append left the last line unfinished, that line is removed
    first. This keeps any damaged line at the end of the file.

    Parameters
    ----------
    entry
        The request to record.
    path
        The ledger file; created if missing. Its folder must exist.
    """

    line = entry.model_dump_json() + "\n"
    with _APPEND_LOCK, path.open("a+b") as handle:
        _drop_unfinished_line(handle)
        handle.write(line.encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())


def read_ledger(path: Path) -> Ledger:
    """Read ``cost.jsonl``, skipping a damaged last line.

    Parameters
    ----------
    path
        The ledger file. A missing file counts as an empty ledger.

    Returns
    -------
    Ledger
        The valid lines, and why the last line was skipped if it was.

    Raises
    ------
    OutputError
        If a line other than the last is damaged, or the file is not UTF-8.
    """

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return Ledger(damage=None, entries=[])
    except UnicodeDecodeError as error:
        raise OutputError(f"{path}: not UTF-8 text ({error.reason})") from error

    lines = [(number, line) for number, line in enumerate(text.splitlines(), 1) if line]
    entries = []
    damage = None
    for position, (number, line) in enumerate(lines):
        try:
            entries.append(LedgerEntry.model_validate_json(line))
        except ValidationError as error:
            if position < len(lines) - 1:
                raise OutputError(
                    f"{path}: line {number} is damaged, and it is not the last line"
                ) from error
            damage = f"{path.name}: skipped its damaged last line (line {number})"
    return Ledger(damage=damage, entries=entries)

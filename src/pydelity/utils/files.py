"""Atomic writes, validated loads and temp-file cleanup for pydelity's output files.

Every text file is read and written as UTF-8. A file is written to a temporary file in
the same folder and then moved over the target, so readers never see a partly written
file.
"""

# Standard Library
import os
import re
import secrets

from dataclasses import dataclass
from pathlib import Path

# Third Party Library
from pydantic import BaseModel, ValidationError

# How many validation problems a damage message names before counting the rest.
_MAX_PROBLEMS_SHOWN = 3

# A temporary file is named `<target name>.tmp-<16 hex digits>`.
_TEMP_INFIX = ".tmp-"

# Matches only the temporary files that `write_bytes_atomic` creates, so cleanup does
# not delete a user's file that happens to have ".tmp-" in its name.
_TEMP_NAME = re.compile(rf"{re.escape(_TEMP_INFIX)}[0-9a-f]{{16}}$")


def _describe(error: ValidationError) -> str:
    """Summarize a validation error without repeating any of the file's contents.

    Parameters
    ----------
    error
        The error Pydantic raised.

    Returns
    -------
    str
        Up to `_MAX_PROBLEMS_SHOWN` problems as ``location: message``, separated by
        semicolons, then how many more there are.
    """

    problems = error.errors(include_input=False, include_url=False)
    parts = [
        f"{'.'.join(str(key) for key in problem['loc']) or '(file)'}: {problem['msg']}"
        for problem in problems[:_MAX_PROBLEMS_SHOWN]
    ]
    if len(problems) > _MAX_PROBLEMS_SHOWN:
        parts.append(f"and {len(problems) - _MAX_PROBLEMS_SHOWN} more")
    return "; ".join(parts)


@dataclass(frozen=True)
class LoadResult[ModelT: BaseModel]:
    """The outcome of loading an output file into a Pydantic model.

    A missing file gives neither a model nor damage.

    Attributes
    ----------
    damage
        Why the file cannot be used (not UTF-8, not JSON, or not the expected schema),
        without any of its contents; ``None`` when the file is absent or valid.
    model
        The validated model; ``None`` when the file is absent or damaged.
    """

    damage: str | None = None
    model: ModelT | None = None


def load_model[ModelT: BaseModel](
    *, model_type: type[ModelT], path: Path
) -> LoadResult[ModelT]:
    """Load a JSON file into a Pydantic model, reporting damage instead of raising.

    Parameters
    ----------
    model_type
        The Pydantic model the file must validate against.
    path
        The JSON file to load.

    Returns
    -------
    LoadResult[ModelT]
        The model, or why the file is damaged, or neither when the file is absent.

    Raises
    ------
    OSError
        If the file exists but cannot be read (for example, permission denied).
    """

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return LoadResult()
    except UnicodeDecodeError as error:
        return LoadResult(damage=f"{path.name} is not UTF-8 text ({error.reason})")

    try:
        model = model_type.model_validate_json(text)
    except ValidationError as error:
        return LoadResult(damage=f"{path.name} is not valid: {_describe(error)}")
    return LoadResult(model=model)


def remove_stale_temp_files(folder: Path) -> list[Path]:
    """Delete temporary files that an interrupted write left in a folder.

    Only the folder itself is searched, not its subfolders, and only names that
    `write_bytes_atomic` creates are removed.

    Parameters
    ----------
    folder
        The folder to clean. A folder that does not exist has nothing to clean.

    Returns
    -------
    list[Path]
        The files removed, sorted by path.
    """

    if not folder.is_dir():
        return []

    removed = []
    for candidate in sorted(folder.iterdir()):
        if _TEMP_NAME.search(candidate.name) and candidate.is_file():
            candidate.unlink(missing_ok=True)
            removed.append(candidate)
    return removed


def write_bytes_atomic(*, data: bytes, path: Path) -> None:
    """Write bytes to a file atomically.

    The bytes go to a temporary file in the same folder, which is flushed, synced to
    disk and then moved over the target with `os.replace`. If anything fails, the
    temporary file is removed and the target is left as it was.

    Parameters
    ----------
    data
        The bytes to write.
    path
        The file to write; its folder must exist.
    """

    temp_path = path.with_name(f"{path.name}{_TEMP_INFIX}{secrets.token_hex(8)}")
    # O_EXCL never reuses an existing file; O_BINARY (Windows only) stops the C runtime
    # from turning "\n" into "\r\n". Mode 0o666 lets the umask set the permissions, as
    # for any newly created file.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    descriptor = os.open(temp_path, flags, 0o666)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def write_model_atomic(*, model: BaseModel, path: Path) -> None:
    """Write a Pydantic model to a JSON file atomically.

    Parameters
    ----------
    model
        The model to write, as indented JSON with a final newline.
    path
        The file to write; its folder must exist.
    """

    write_text_atomic(path=path, text=model.model_dump_json(indent=2) + "\n")


def write_text_atomic(*, path: Path, text: str) -> None:
    """Write text to a file atomically, as UTF-8 with its line endings unchanged.

    See `write_bytes_atomic`.

    Parameters
    ----------
    path
        The file to write; its folder must exist.
    text
        The text to write.
    """

    write_bytes_atomic(data=text.encode("utf-8"), path=path)

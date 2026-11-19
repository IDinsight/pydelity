"""Running pydelity's async functions from sync code, and issuing its warnings.

pydelity's functions are written as coroutines, such as ``arun``. Each sync function,
such as ``run``, runs its async version through `run_sync`, which uses `asyncio.run`.
Code that already runs an event loop, such as a Jupyter cell, awaits the async version
instead.

Blocking calls that wait for a person, such as a question on the terminal, go through
`run_in_daemon_thread`. This keeps the event loop free and lets Ctrl+C end the program
immediately.

Each user-facing warning goes through `warn`, which logs it, issues it as a
`PydelityWarning` and, inside `collect_warnings`, keeps it for ``run.json``, with the
step that was running when it was issued (see `running_step`).
"""

# Standard Library
import asyncio
import contextlib
import os
import threading
import warnings

from collections.abc import Callable, Coroutine, Generator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

# Third Party Library
import anyio
import pydantic_ai
import pydantic_graph

from loguru import logger

# Package Library
from pydelity.errors import PydelityWarning, WarningCode

# The list that keeps the warnings issued in this context, inside `collect_warnings`.
_COLLECTED: ContextVar["list[IssuedWarning] | None"] = ContextVar(
    "pydelity_warnings", default=None
)

# The step running in this context, inside `running_step`.
_CURRENT_STEP: ContextVar[str | None] = ContextVar("pydelity_step", default=None)

# Warnings point at the first stack frame outside this package, asyncio, PydanticAI and
# the libraries PydanticAI runs its agent with (pydantic_graph and anyio). Model
# requests inside the agent can issue warnings, such as the max_cost warning.
_SKIPPED_PREFIXES = (
    str(Path(__file__).parent.parent) + os.sep,
    *(
        str(Path(module.__file__).parent) + os.sep
        for module in (anyio, asyncio, pydantic_ai, pydantic_graph)
        if module.__file__ is not None
    ),
)


def _settle[ResultT](
    *,
    error: BaseException | None,
    future: asyncio.Future[ResultT],
    result: ResultT | None,
) -> None:
    """Give a future its result or exception, unless it was canceled meanwhile.

    Parameters
    ----------
    error
        The exception to set, or ``None`` to set the result.
    future
        The future to settle.
    result
        The result to set when there is no error.
    """

    if future.done():
        return
    if error is not None:
        future.set_exception(error)
    else:
        future.set_result(cast("ResultT", result))


@dataclass(frozen=True)
class IssuedWarning:
    """A user-facing warning pydelity issued.

    Attributes
    ----------
    code
        The kind of warning.
    details
        The values the warning is about, such as the damaged file's name.
    message
        The warning's text.
    step
        The step that was running when the warning was issued, or ``None`` when no
        step was.
    """

    code: WarningCode
    message: str
    details: dict[str, object] = field(default_factory=dict)
    step: str | None = None


@contextmanager
def collect_warnings() -> Generator[list[IssuedWarning]]:
    """Keep every warning that `warn` issues in this context, such as during a run.

    Tasks started inside the context, such as those PydanticAI starts, add their
    warnings to the same list.

    Yields
    ------
    list[IssuedWarning]
        The warnings issued so far, in order. The list grows while the context lasts.
    """

    collected: list[IssuedWarning] = []
    token = _COLLECTED.set(collected)
    try:
        yield collected
    finally:
        _COLLECTED.reset(token)


async def run_in_daemon_thread[ResultT](function: Callable[[], ResultT]) -> ResultT:
    """Run a blocking call, such as a question on the terminal, on a daemon thread.

    Unlike with `asyncio.to_thread`, the thread does not keep the program from
    exiting, so Ctrl+C during a question on the terminal ends the run immediately.

    Parameters
    ----------
    function
        The call to run, with no arguments.

    Returns
    -------
    ResultT
        What the call returned.
    """

    loop = asyncio.get_running_loop()
    future: asyncio.Future[ResultT] = loop.create_future()

    def target() -> None:
        """Run the call and hand its outcome back to the event loop."""

        error: BaseException | None = None
        result: ResultT | None = None
        try:
            result = function()
        except BaseException as caught:  # the awaiting coroutine re-raises it
            error = caught
        # If the run already ended, its loop is closed and nothing awaits the result.
        with contextlib.suppress(RuntimeError):
            loop.call_soon_threadsafe(
                lambda: _settle(error=error, future=future, result=result)
            )

    threading.Thread(daemon=True, name="pydelity-question", target=target).start()
    return await future


def run_sync[**ParamsT, ResultT](
    function: Callable[ParamsT, Coroutine[Any, Any, ResultT]],
    /,
    *args: ParamsT.args,
    **kwargs: ParamsT.kwargs,
) -> ResultT:
    """Run one of pydelity's async functions from sync code, with `asyncio.run`.

    The result, exceptions and warnings reach the caller as if it had awaited the
    function. Ctrl+C cancels the function, lets it finish cleaning up, then raises
    `KeyboardInterrupt`.

    Parameters
    ----------
    function
        The async function, such as `pydelity.api.arun`. Its name starts with ``a``,
        and its sync version has the same name without the ``a``.
    *args
        Positional arguments for ``function``.
    **kwargs
        Keyword arguments for ``function``.

    Returns
    -------
    ResultT
        What ``function`` returned.

    Raises
    ------
    RuntimeError
        If an event loop is already running in this thread, as in Jupyter or async
        code. ``function`` is not called, so nothing runs and no coroutine is left
        unawaited.

    Examples
    --------
    >>> async def adouble(number: int) -> int:
    ...     return 2 * number
    >>> run_sync(adouble, 21)
    42
    """

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No event loop runs in this thread, so asyncio.run can start one.
        return asyncio.run(function(*args, **kwargs))

    # pydelity passes its own async functions, which always have a name.
    name = getattr(function, "__name__", repr(function))
    raise RuntimeError(
        f"pydelity.{name.removeprefix('a')}() cannot be called while an event loop is "
        f"running, as in Jupyter or async code. Use `await pydelity.{name}(...)` "
        "instead."
    )


@contextmanager
def running_step(name: str) -> Generator[None]:
    """Mark the warnings issued in this context as issued by a step.

    Tasks started inside the context, such as those PydanticAI starts, belong to the
    same step.

    Parameters
    ----------
    name
        The step, such as ``survey``.

    Yields
    ------
    None
        Nothing; the step lasts while the context does.
    """

    token = _CURRENT_STEP.set(name)
    try:
        yield
    finally:
        _CURRENT_STEP.reset(token)


def warn(
    message: str,
    *,
    code: WarningCode,
    details: Mapping[str, object] | None = None,
) -> IssuedWarning:
    """Log a warning, issue it as a `PydelityWarning`, and keep it for the run.

    The kept warning names the step running in this context (see `running_step`).

    The `PydelityWarning` is attributed to the caller's code.

    Parameters
    ----------
    message
        The warning's text.
    code
        The kind of warning.
    details
        The values the warning is about.

    Returns
    -------
    IssuedWarning
        The warning as kept, whose ``details`` the caller may still complete.
    """

    issued = IssuedWarning(
        code=code,
        details=dict(details or {}),
        message=message,
        step=_CURRENT_STEP.get(),
    )
    logger.warning(message)
    collected = _COLLECTED.get()
    if collected is not None:
        collected.append(issued)
    warnings.warn(
        category=PydelityWarning,
        message=message,
        skip_file_prefixes=_SKIPPED_PREFIXES,
    )
    return issued

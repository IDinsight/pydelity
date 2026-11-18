"""Running pydelity's coroutines from synchronous code, and issuing its warnings.

pydelity's functions are written as coroutines, such as ``arun``. The sync API
functions call them through `run_coroutine`. It uses `asyncio.run` when the calling
thread has no running event loop, as in a script. Otherwise, as in a Jupyter cell or
async code that calls a sync function, it runs the coroutine on a worker thread with
its own event loop.

Blocking calls that wait for a person, such as a question on the terminal, go through
`run_in_daemon_thread`. This keeps the event loop free and lets Ctrl+C end the program
immediately.

pydelity issues warnings through `warn`. On a worker thread, `warn` records them
instead, and `run_coroutine` issues them again in the calling thread when the
coroutine ends. The caller's warning filters and ``warnings.catch_warnings`` blocks
then handle them the same way as warnings from the async function.
"""

# Standard Library
import asyncio
import contextlib
import os
import threading
import warnings

from collections.abc import Callable, Coroutine
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

# Package Library
from pydelity.errors import PydelityWarning

# How long the calling thread waits for the worker thread between checks, so Ctrl+C
# reaches it on every platform (an unbounded join is not interruptible everywhere).
_JOIN_POLL_SECONDS = 0.2

# Warnings point at the first stack frame outside this package, in the caller's code.
_PACKAGE_PREFIX = str(Path(__file__).parent.parent) + os.sep

# On a worker thread, the list that `warn` appends to instead of issuing warnings.
_recorded_warnings: ContextVar[list[str] | None] = ContextVar(
    "_recorded_warnings", default=None
)


@dataclass
class _WorkerState[ResultT]:
    """What the worker thread shares with the thread that waits for it.

    Attributes
    ----------
    error
        The exception the coroutine raised, if any.
    loop
        The worker's event loop, once the coroutine has started.
    result
        The coroutine's result, once it has returned.
    started
        Set once ``loop`` and ``task`` are known, or once the worker gave up before
        starting the coroutine.
    task
        The task running the coroutine, once it has started.
    warnings
        The messages `warn` recorded on the worker thread, in order.
    """

    error: BaseException | None = None
    loop: asyncio.AbstractEventLoop | None = None
    result: ResultT | None = None
    started: threading.Event = field(default_factory=threading.Event)
    task: asyncio.Task[ResultT] | None = None
    warnings: list[str] = field(default_factory=list)


def _cancel(state: _WorkerState[Any]) -> None:
    """Ask the worker's event loop to cancel the coroutine.

    Parameters
    ----------
    state
        The state shared with the worker thread.
    """

    state.started.wait()
    if state.loop is None or state.task is None:
        return
    # If the coroutine already finished, its loop is closed and there is nothing to
    # cancel.
    with contextlib.suppress(RuntimeError):
        state.loop.call_soon_threadsafe(state.task.cancel)


def _issue(message: str) -> None:
    """Issue a `PydelityWarning` attributed to the caller's code.

    Parameters
    ----------
    message
        The warning's text.
    """

    warnings.warn(
        category=PydelityWarning,
        message=message,
        skip_file_prefixes=(_PACKAGE_PREFIX,),
    )


def _run_on_worker_thread[ResultT](
    coroutine: Coroutine[Any, Any, ResultT],
) -> ResultT:
    """Run a coroutine on a new thread with its own event loop, and wait for it.

    Parameters
    ----------
    coroutine
        The coroutine to run.

    Returns
    -------
    ResultT
        What the coroutine returned.
    """

    state: _WorkerState[ResultT] = _WorkerState()
    thread = threading.Thread(
        args=(coroutine, state), daemon=True, name="pydelity", target=_worker_main
    )
    thread.start()
    try:
        _wait_for(caller=asyncio.current_task(), state=state, thread=thread)
    except BaseException:
        # On Ctrl+C in the calling thread, cancel the coroutine so it can record the
        # interruption and leave its files valid. Wait for it to finish, then re-raise.
        _cancel(state)
        _wait_for(caller=None, state=state, thread=thread)
        raise
    finally:
        for message in state.warnings:
            _issue(message)

    if state.error is not None:
        raise state.error
    return cast("ResultT", state.result)


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


async def _track[ResultT](
    coroutine: Coroutine[Any, Any, ResultT], state: _WorkerState[ResultT]
) -> ResultT:
    """Record the worker's loop and task for canceling, then run the coroutine.

    Parameters
    ----------
    coroutine
        The coroutine to run.
    state
        The state shared with the calling thread.

    Returns
    -------
    ResultT
        What the coroutine returned.
    """

    state.loop = asyncio.get_running_loop()
    state.task = asyncio.current_task()
    state.started.set()
    return await coroutine


def _wait_for(
    *,
    caller: asyncio.Task[Any] | None,
    state: _WorkerState[Any],
    thread: threading.Thread,
) -> None:
    """Wait for the worker thread, in short joins that Ctrl+C can interrupt.

    While the calling thread waits, its event loop cannot run, so a cancellation of
    the calling task cannot take effect. Under `asyncio.run`, the first Ctrl+C arrives
    as a cancellation of the main task. When the calling task gets a new cancellation
    request, this function cancels the coroutine too. The coroutine's
    `CancelledError` then reaches the caller like any other exception it raises.

    Parameters
    ----------
    caller
        The task that made the sync call, or ``None`` to ignore cancellations.
    state
        The state shared with the worker thread.
    thread
        The worker thread.
    """

    # Ignore cancellation requests made before the call, for example in a cleanup
    # handler.
    requests_before = caller.cancelling() if caller is not None else 0
    forwarded = False
    while thread.is_alive():
        thread.join(timeout=_JOIN_POLL_SECONDS)
        if (
            not forwarded
            and caller is not None
            and caller.cancelling() > requests_before
        ):
            _cancel(state)
            forwarded = True


def _worker_main[ResultT](
    coroutine: Coroutine[Any, Any, ResultT], state: _WorkerState[ResultT]
) -> None:
    """Run the coroutine in the worker thread and keep its outcome for the caller.

    Parameters
    ----------
    coroutine
        The coroutine to run.
    state
        The state shared with the calling thread.
    """

    _recorded_warnings.set(state.warnings)
    try:
        state.result = asyncio.run(_track(coroutine, state))
    except BaseException as error:  # the calling thread re-raises it
        state.error = error
    finally:
        state.started.set()


def run_coroutine[ResultT](coroutine: Coroutine[Any, Any, ResultT]) -> ResultT:
    """Run a coroutine to completion from synchronous code and return its result.

    Without a running event loop in the calling thread, this is `asyncio.run`. With one
    (inside Jupyter or async code), the coroutine runs on a worker thread with its own
    event loop while the calling thread waits; that blocks the caller's loop until the
    coroutine ends, as any sync call would. Either way the result, the exception and
    pydelity's warnings reach the caller as if it had awaited the coroutine. Ctrl+C,
    or a cancellation of the calling task, cancels the coroutine and waits for it to
    finish before the interruption propagates.

    Parameters
    ----------
    coroutine
        The coroutine to run. It must not have been started.

    Returns
    -------
    ResultT
        What the coroutine returned.

    Examples
    --------
    >>> async def double(number: int) -> int:
    ...     return 2 * number
    >>> run_coroutine(double(21))
    42
    """

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)
    return _run_on_worker_thread(coroutine)


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


def warn(message: str) -> None:
    """Issue a `PydelityWarning`, or record it when running on a worker thread.

    Parameters
    ----------
    message
        The warning's text.
    """

    recorded = _recorded_warnings.get()
    if recorded is not None:
        recorded.append(message)
        return
    _issue(message)

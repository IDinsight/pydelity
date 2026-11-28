"""A stand-in for the Anthropic and OpenAI APIs, served on the loopback interface.

The provider SDKs read ``ANTHROPIC_BASE_URL`` and ``OPENAI_BASE_URL``. With both
pointed at this server, pydelity sends its uploads and model requests here instead of
to a provider, so a run needs no real API key and costs nothing. The server answers:

- Anthropic: ``POST /v1/messages`` (Messages API) and ``POST /v1/files`` (Files API);
- OpenAI: ``POST /v1/responses`` (Responses API) and ``POST /v1/files`` (Files API).

A model request gets the next survey answer the caller gave, as the reply's text, with
the caller's usage figures. A request whose text holds the survey answer to review gets
the next survey verdict the caller gave. A page extraction request, whose text names
its page with ``Page index N (``, gets that page's answer for the extraction model or,
when its text holds the extraction to review, for the verifier. A page-break request,
whose text names its break with ``Page break between page indexes N and``, gets that
break's next answer, since the judge's and the verifier's requests are the same. A
page's or break's answers do not depend on how its requests interleave with other
pages' and breaks'. The answer `REFUSAL` makes the reply a refusal with no text, and
`OUTPUT_LIMIT` a reply cut off at the output token limit. An upload succeeds and gets
a new file ID. A model
request that names a file ID the server does not hold gets HTTP 404 naming that ID,
which is how the providers answer once an upload has expired. Faults the caller adds
make requests fail; temporary ones (408, 409, 429 and 5xx) carry a ``retry-after-ms``
header of one millisecond, which both SDKs honor, so retries do not wait. Every request
is logged without its headers, so no key is ever recorded.

The bodies follow the response types of the installed ``anthropic`` and ``openai``
SDKs (``Message``, ``FileMetadata``, ``Response`` and ``FileObject``) and their error
format. The module uses the standard library only, so a script can start the server
with any Python, before pydelity is installed.

Examples
--------
In Python::

    with MockProviders(answers=[answer]) as mock:
        os.environ.update(mock.environment())
        pydelity.run(pdf, model="openai:gpt-6.2-astra", yes=True)
        statuses = [request.status for request in mock.requests]

From the command line, at the repository root, with an answer file such as
``tests/fixtures/survey_answers/irs_form_1040a_1965_scan.json``, for page
extraction a page answers file such as
``tests/fixtures/extraction_answers/irs_form_1040a_1965_scan.json`` and, for
page-break verification, a break answers file such as
``tests/fixtures/break_answers/irs_form_1040a_1965_scan.json``::

    python -m tests.fixtures.mock_providers --answer <answer JSON file> \
        --page-answers <page answers JSON file> \
        --break-answers <break answers JSON file>
"""

# Standard Library
import argparse
import json
import re
import sys
import threading
import time
import uuid

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from email import policy
from email.parser import BytesParser
from http.client import responses
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import TracebackType
from typing import Literal, Self, cast
from urllib.parse import urlsplit

# Anthropic's error type for each HTTP status that has its own type in the SDK. Other
# statuses get ``invalid_request_error`` below 500 and ``api_error`` from 500.
_ANTHROPIC_ERROR_TYPES = {
    401: "authentication_error",
    402: "billing_error",
    403: "permission_error",
    404: "not_found_error",
    429: "rate_limit_error",
    504: "timeout_error",
    529: "overloaded_error",
}

# The line that starts the text of each page-break request, naming the page before
# its break.
_BREAK_LINE = re.compile(r"Page break between page indexes (\d+) and ")

# The lowest HTTP status code of a server error, which the SDKs retry.
_FIRST_SERVER_ERROR_CODE = 500

# The interface the server listens on.
_HOST = "127.0.0.1"

# The line that starts the text of each page extraction request, naming its page.
_PAGE_LINE = re.compile(r"Page index (\d+) \(")

# How often the server checks whether it was asked to stop, so stopping takes at most
# this long.
_POLL_INTERVAL_SECONDS = 0.05

# Text that only the survey verifier's requests hold: the heading of the survey answer
# it reviews.
_SURVEY_VERIFIER_TEXT = "The survey answer to review:"

# HTTP status codes below 500 that the SDKs treat as temporary and retry.
_TEMPORARY_STATUS_CODES = frozenset({408, 409, 429})

# Text that only page extraction's verifier requests hold: the heading of the
# extraction it reviews.
_VERIFIER_TEXT = "The extraction to review:"

# The input tokens each model reply reports, unless the caller gives another figure.
DEFAULT_INPUT_TOKENS = 3_000

# The output tokens each model reply reports, unless the caller gives another figure.
DEFAULT_OUTPUT_TOKENS = 600

# An answer that makes the reply stop with no text because the model used all its
# output tokens: Anthropic's ``max_tokens`` stop reason, or an OpenAI response left
# incomplete at ``max_output_tokens``.
OUTPUT_LIMIT = "<mock provider: output limit>"

# The value `MockProviders.environment` gives both API keys. pydelity refuses to start
# a run without a key, and the server never looks at it.
PLACEHOLDER_KEY = "mock-provider-placeholder"

# An answer that makes the reply a refusal with no text: Anthropic's ``refusal`` stop
# reason, or an OpenAI response left incomplete by its content filter.
REFUSAL = "<mock provider: refusal>"

# Which agent a model request of the survey or page extraction comes from:
# ``surveyor`` or ``verifier`` for the survey, ``extractor`` or ``verifier`` for page
# extraction. Page-break verification's judge and verifier send the same request, so
# its requests have no agent here.
type Agent = Literal["extractor", "surveyor", "verifier"]

# An answer to a model request: JSON data, sent as JSON, or text, sent as it is.
type Answer = Mapping[str, object] | str

# Which provider's API a request is for.
type Provider = Literal["anthropic", "openai"]

# What a request does: ask the model, or upload a file.
type Route = Literal["model", "upload"]

# The provider and route of each path the server answers, after the base URL.
_ROUTES: dict[str, tuple[Provider, Route]] = {
    "/anthropic/v1/files": ("anthropic", "upload"),
    "/anthropic/v1/messages": ("anthropic", "model"),
    "/openai/v1/files": ("openai", "upload"),
    "/openai/v1/responses": ("openai", "model"),
}


@dataclass
class _Fault:
    """A failure the server gives requests on one route."""

    message: str | None
    """The error message, or ``None`` for one made from the status."""

    remaining: int | None
    """How many more requests get the failure, or ``None`` for every request."""

    route: Route
    """The route whose requests fail."""

    status: int
    """The HTTP status of the failure."""


class _Handler(BaseHTTPRequestHandler):
    """Answers one HTTP connection's requests from the `MockProviders` state."""

    protocol_version = "HTTP/1.1"

    def do_POST(self) -> None:
        """Read a POST request, get the stand-in's reply and send it."""

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        mock = cast("_Server", self.server).mock
        reply = mock._answer(
            body=body,
            content_type=self.headers.get("Content-Type", ""),
            path=self.path,
        )

        data = json.dumps(reply.payload).encode()
        self.send_response(reply.status)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Type", "application/json")
        for name, value in reply.headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        """Print the request line to stderr only when the stand-in is verbose.

        Parameters
        ----------
        format
            The message's format string.
        *args
            The values to put into it.
        """

        if cast("_Server", self.server).mock.verbose:
            super().log_message(format, *args)


@dataclass(frozen=True)
class _Reply:
    """What the server sends back for one request."""

    payload: dict[str, object]
    """The JSON body."""

    status: int
    """The HTTP status."""

    headers: dict[str, str] = field(default_factory=dict)
    """Headers besides ``Content-Type`` and ``Content-Length``."""


class _Server(ThreadingHTTPServer):
    """The HTTP server, which holds the `MockProviders` its handler answers for."""

    daemon_threads = True

    def __init__(self, *, mock: "MockProviders", port: int) -> None:
        """Bind the server to the loopback interface.

        Parameters
        ----------
        mock
            The stand-in whose state the handler uses.
        port
            The port, or 0 for any free port.
        """

        super().__init__(RequestHandlerClass=_Handler, server_address=(_HOST, port))
        self.mock = mock

    def handle_error(self, request: object, client_address: object) -> None:
        """Ignore a client that went away mid-request; report any other error.

        A test that cancels a run closes its connection while the server still waits
        to answer, so writing the reply then fails. That is expected, not a failure.

        Parameters
        ----------
        request
            The request's socket.
        client_address
            The client's address.
        """

        if isinstance(sys.exc_info()[1], ConnectionError):
            return
        super().handle_error(request, client_address)  # ty: ignore[invalid-argument-type]


@dataclass(frozen=True)
class _Target:
    """Which step's request a model request is, and which agent and page it is for."""

    agent: Agent | None
    """The agent the request came from, or ``None`` for a page-break request."""

    break_index: int | None
    """For a page-break request, the page before its break; otherwise ``None``."""

    page_index: int | None
    """For a page extraction request, the page it is about; otherwise ``None``."""


def _answer_list(given: Answer | Sequence[Answer]) -> list[str]:
    """Write one answer, or a list of answers, as the texts replies carry.

    Parameters
    ----------
    given
        An answer, or a sequence of answers.

    Returns
    -------
    list[str]
        Each answer's text, in order.
    """

    if isinstance(given, str | Mapping):
        return [_answer_text(given)]
    return [_answer_text(item) for item in given]


def _answer_text(answer: Answer) -> str:
    """Write an answer as the text a reply carries.

    Parameters
    ----------
    answer
        JSON data or text.

    Returns
    -------
    str
        The data as JSON, or the text as it is.
    """

    return answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False)


def _anthropic_file(*, fields: dict[str, str], upload: dict[str, object]) -> _Reply:
    """Make the reply to an Anthropic upload: a ``FileMetadata`` body.

    Parameters
    ----------
    fields
        The upload's form fields; ``expires_in_seconds`` sets the expiry.
    upload
        The uploaded file's name, media type and size.

    Returns
    -------
    _Reply
        The reply, with a new file ID.
    """

    now = datetime.now(UTC)
    seconds = fields.get("expires_in_seconds")
    expires_at = (
        (now + timedelta(seconds=int(seconds))).isoformat() if seconds else None
    )
    payload: dict[str, object] = {
        "created_at": now.isoformat(),
        "downloadable": False,
        "expires_at": expires_at,
        "filename": upload["filename"],
        "id": _new_id("file_"),
        "mime_type": upload["content_type"],
        "size_bytes": upload["bytes"],
        "type": "file",
    }
    return _Reply(payload=payload, status=200)


def _anthropic_message(*, answer: str, model: str, usage: tuple[int, int]) -> _Reply:
    """Make the reply to an Anthropic model request: a ``Message`` body.

    Parameters
    ----------
    answer
        The reply's text, or `REFUSAL` or `OUTPUT_LIMIT` for a reply that stops with
        no text.
    model
        The model the request named.
    usage
        The input and output tokens to report.

    Returns
    -------
    _Reply
        The reply.
    """

    input_tokens, output_tokens = usage
    stop_reason = {REFUSAL: "refusal", OUTPUT_LIMIT: "max_tokens"}.get(answer)
    content = (
        [] if stop_reason else [{"citations": None, "text": answer, "type": "text"}]
    )
    payload: dict[str, object] = {
        "content": content,
        "id": _new_id("msg_"),
        "model": model,
        "role": "assistant",
        "stop_reason": stop_reason or "end_turn",
        "stop_sequence": None,
        "type": "message",
        "usage": {
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "server_tool_use": None,
            "service_tier": "standard",
        },
    }
    return _Reply(payload=payload, status=200)


def _error(*, message: str, provider: Provider, status: int) -> _Reply:
    """Make an error reply in the provider's error format.

    Parameters
    ----------
    message
        The error message.
    provider
        The provider whose format to use.
    status
        The HTTP status.

    Returns
    -------
    _Reply
        The reply, with a ``retry-after-ms`` header when the SDKs retry the status.
    """

    server_error = status >= _FIRST_SERVER_ERROR_CODE
    if provider == "anthropic":
        default_type = "api_error" if server_error else "invalid_request_error"
        error_type = _ANTHROPIC_ERROR_TYPES.get(status, default_type)
        payload: dict[str, object] = {
            "error": {"message": message, "type": error_type},
            "type": "error",
        }
    else:
        error_type = "server_error" if server_error else "invalid_request_error"
        payload = {
            "error": {
                "code": None,
                "message": message,
                "param": None,
                "type": error_type,
            }
        }

    temporary = server_error or status in _TEMPORARY_STATUS_CODES
    headers = {"retry-after-ms": "1"} if temporary else {}
    return _Reply(headers=headers, payload=payload, status=status)


def _file_ids(value: object) -> list[str]:
    """Find every ``file_id`` value in a request body, at any depth.

    Parameters
    ----------
    value
        The parsed JSON body, or any part of it.

    Returns
    -------
    list[str]
        The file IDs, in the order they appear.

    Examples
    --------
    ``_file_ids({"input": [{"content": [{"file_id": "file-1"}]}]})`` returns
    ``["file-1"]``.
    """

    if isinstance(value, dict):
        found = [value["file_id"]] if isinstance(value.get("file_id"), str) else []
        return found + [
            file_id for item in value.values() for file_id in _file_ids(item)
        ]
    if isinstance(value, list):
        return [file_id for item in value for file_id in _file_ids(item)]
    return []


def _new_id(prefix: str) -> str:
    """Make a new ID in the providers' style, such as ``file_`` and 24 characters.

    Parameters
    ----------
    prefix
        The ID's prefix.

    Returns
    -------
    str
        The ID.
    """

    return f"{prefix}mock{uuid.uuid4().hex[:20]}"


def _next_answer[Key](
    *, answers: Mapping[Key, list[str]], key: Key, sent: Counter[Key]
) -> str | None:
    """Take the next answer for a page and agent, or a break. Call with the lock held.

    Parameters
    ----------
    answers
        The answers, by page index and agent, or by break index.
    key
        The page index and the agent, or the break index.
    sent
        How many answers each key has had, which this adds one to.

    Returns
    -------
    str | None
        The answer, the last one repeating, or ``None`` when there is none.
    """

    given = answers.get(key)
    if not given:
        return None
    count = sent[key]
    sent[key] += 1
    return given[min(count, len(given) - 1)]


def _openai_file(*, fields: dict[str, str], upload: dict[str, object]) -> _Reply:
    """Make the reply to an OpenAI upload: a ``FileObject`` body.

    Parameters
    ----------
    fields
        The upload's form fields; ``purpose`` and ``expires_after[seconds]`` are used.
    upload
        The uploaded file's name and size.

    Returns
    -------
    _Reply
        The reply, with a new file ID.
    """

    now = int(time.time())
    seconds = fields.get("expires_after[seconds]")
    payload: dict[str, object] = {
        "bytes": upload["bytes"],
        "created_at": now,
        "expires_at": now + int(seconds) if seconds else None,
        "filename": upload["filename"],
        "id": _new_id("file-"),
        "object": "file",
        "purpose": fields.get("purpose", "user_data"),
        "status": "processed",
    }
    return _Reply(payload=payload, status=200)


def _openai_response(*, answer: str, model: str, usage: tuple[int, int]) -> _Reply:
    """Make the reply to an OpenAI model request: a Responses API ``Response`` body.

    Parameters
    ----------
    answer
        The reply's text, or `REFUSAL` or `OUTPUT_LIMIT` for a response left
        incomplete with no text.
    model
        The model the request named.
    usage
        The input and output tokens to report.

    Returns
    -------
    _Reply
        The reply.
    """

    input_tokens, output_tokens = usage
    incomplete = {REFUSAL: "content_filter", OUTPUT_LIMIT: "max_output_tokens"}.get(
        answer
    )
    message = {
        "content": [{"annotations": [], "text": answer, "type": "output_text"}],
        "id": _new_id("msg_"),
        "role": "assistant",
        "status": "completed",
        "type": "message",
    }
    payload: dict[str, object] = {
        "created_at": time.time(),
        "error": None,
        "id": _new_id("resp_"),
        "incomplete_details": None if incomplete is None else {"reason": incomplete},
        "model": model,
        "object": "response",
        "output": [] if incomplete else [message],
        "parallel_tool_calls": True,
        "status": "incomplete" if incomplete else "completed",
        "tool_choice": "auto",
        "tools": [],
        "usage": {
            "input_tokens": input_tokens,
            "input_tokens_details": {"cache_write_tokens": 0, "cached_tokens": 0},
            "output_tokens": output_tokens,
            "output_tokens_details": {"reasoning_tokens": 0},
            "total_tokens": input_tokens + output_tokens,
        },
    }
    return _Reply(payload=payload, status=200)


def _parse_json(body: bytes) -> dict[str, object]:
    """Read a JSON request body.

    Parameters
    ----------
    body
        The body's bytes.

    Returns
    -------
    dict[str, object]
        The body, or an empty dict when it is not a JSON object.
    """

    try:
        parsed = json.loads(body or b"{}")
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _parse_upload(*, body: bytes, content_type: str) -> dict[str, object]:
    """Read a multipart upload into its form fields and a summary of the file.

    Parameters
    ----------
    body
        The body's bytes.
    content_type
        The request's ``Content-Type``, which names the multipart boundary.

    Returns
    -------
    dict[str, object]
        ``fields`` (the text fields), and the file's ``filename``, ``content_type``
        and size in ``bytes``. The file's contents are not kept.
    """

    header = f"Content-Type: {content_type}\r\n\r\n".encode()
    message = BytesParser(policy=policy.HTTP).parsebytes(header + body)
    fields: dict[str, str] = {}
    summary: dict[str, object] = {"bytes": 0, "content_type": None, "filename": None}
    for part in message.iter_parts():
        payload = part.get_payload(decode=True)
        data = payload if isinstance(payload, bytes) else b""
        filename = part.get_filename()
        if filename is None:
            name = part.get_param("name", header="content-disposition")
            fields[str(name)] = data.decode()
        else:
            summary = {
                "bytes": len(data),
                "content_type": part.get_content_type(),
                "filename": filename,
            }
    return {"fields": fields, **summary}


def _request_target(body: Mapping[str, object]) -> _Target:
    """Tell which step, agent and page a model request is for.

    Parameters
    ----------
    body
        The model request's JSON body.

    Returns
    -------
    _Target
        The break's earlier page for a page-break request, the agent and the page for
        a page extraction request, and the agent alone for one of the survey's
        requests.
    """

    text = json.dumps(body, ensure_ascii=False)
    match = _BREAK_LINE.search(text)
    if match is not None:
        return _Target(agent=None, break_index=int(match[1]), page_index=None)
    match = _PAGE_LINE.search(text)
    if match is not None:
        agent: Agent = "verifier" if _VERIFIER_TEXT in text else "extractor"
        return _Target(agent=agent, break_index=None, page_index=int(match[1]))
    agent = "verifier" if _SURVEY_VERIFIER_TEXT in text else "surveyor"
    return _Target(agent=agent, break_index=None, page_index=None)


@dataclass(frozen=True)
class RecordedRequest:
    """One request the server received, without its headers."""

    agent: Agent | None
    """For a model request of the survey or page extraction, the agent it came from;
    otherwise ``None``."""

    body: dict[str, object]
    """The JSON body of a model request. For an upload, its ``fields`` and the file's
    ``filename``, ``content_type`` and size in ``bytes``."""

    break_index: int | None
    """For a page-break request, the page before its break; otherwise ``None``."""

    page_index: int | None
    """For a page extraction request, the page it is about; otherwise ``None``."""

    path: str
    """The request's path, after the host."""

    provider: Provider | None
    """The provider the path belongs to, or ``None`` for a path the server does not
    answer."""

    route: Route | None
    """What the request did, or ``None`` for a path the server does not answer."""

    status: int
    """The HTTP status the server replied with."""

    @property
    def file_ids(self) -> list[str]:
        """The file IDs a model request names, in order."""

        return _file_ids(self.body) if self.route == "model" else []


class MockProviders:
    """A stand-in for both providers' APIs, run on a loopback port in a thread.

    Parameters
    ----------
    answers
        The survey answers, as dicts (sent as JSON) or as text (sent as it is). Each
        model request that names no page or break gets the next one; once they run
        out, the last one repeats.
    page_answers
        Page extraction's answers, by page index and then agent (``extractor`` or
        ``verifier``): one answer, or a list whose next item each request for that
        page and agent gets, the last one repeating. A page request without an
        answer here gets HTTP 400.
    break_answers
        Page-break verification's answers, by the index of the page before the
        break: one answer, or a list whose next item each request for that break
        gets, whichever agent sent it, the last one repeating. A page-break request
        without an answer here gets HTTP 400.
    survey_verdicts
        The survey verifier's verdicts. Each survey verifier request gets the next
        one; once they run out, the last one repeats. A survey verifier request with
        none here gets HTTP 400.
    input_tokens
        The input tokens each model reply reports.
    output_tokens
        The output tokens each model reply reports.
    port
        The port to listen on, or 0 for any free port.
    verbose
        Whether to print each request line to stderr.
    delay_seconds
        How long to wait before answering each model request, so a test can act while
        a request is in flight.

    Raises
    ------
    ValueError
        If no answers, page answers or break answers are given.
    """

    def __init__(  # noqa: PLR0913 - one argument per option of the stand-in
        self,
        *,
        answers: Sequence[Answer],
        break_answers: Mapping[int, Answer | Sequence[Answer]] | None = None,
        delay_seconds: float = 0.0,
        input_tokens: int = DEFAULT_INPUT_TOKENS,
        output_tokens: int = DEFAULT_OUTPUT_TOKENS,
        page_answers: Mapping[int, Mapping[str, Answer | Sequence[Answer]]]
        | None = None,
        port: int = 0,
        survey_verdicts: Sequence[Answer] = (),
        verbose: bool = False,
    ) -> None:
        """Hold the answers and settings; nothing listens until `start`."""

        if not answers and not page_answers and not break_answers:
            raise ValueError("MockProviders needs at least one answer")
        self._answers = [_answer_text(item) for item in answers]
        self._answers_sent = 0
        self._break_answers: dict[int, list[str]] = {
            int(index): _answer_list(given)
            for index, given in (break_answers or {}).items()
        }
        self._break_answers_sent: Counter[int] = Counter()
        self._in_flight = 0
        self._max_in_flight = 0
        self._page_answers: dict[tuple[int, str], list[str]] = {
            (int(page), agent): _answer_list(given)
            for page, by_agent in (page_answers or {}).items()
            for agent, given in by_agent.items()
        }
        self._page_answers_sent: Counter[tuple[int, str]] = Counter()
        self._delay_seconds = delay_seconds
        self._faults: list[_Fault] = []
        self._files: dict[Provider, set[str]] = {"anthropic": set(), "openai": set()}
        self._lock = threading.Lock()
        self._model_request_seen = threading.Event()
        self._port = port
        self._requests: list[RecordedRequest] = []
        self._server: _Server | None = None
        self._survey_verdicts = [_answer_text(item) for item in survey_verdicts]
        self._survey_verdicts_sent = 0
        self._thread: threading.Thread | None = None
        self._usage = (input_tokens, output_tokens)
        self.verbose = verbose

    def __enter__(self) -> Self:
        """Start the server.

        Returns
        -------
        Self
            The started stand-in.
        """

        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop the server.

        Parameters
        ----------
        exc_type
            The type of the exception that ended the block, if any.
        exc
            The exception, if any.
        traceback
            Its traceback, if any.
        """

        self.stop()

    def _answer(self, *, body: bytes, content_type: str, path: str) -> _Reply:
        """Answer one POST request and log it; the handler calls this for each request.

        Parameters
        ----------
        body
            The request body.
        content_type
            The request's ``Content-Type``.
        path
            The request's path, with any query string.

        Returns
        -------
        _Reply
            The reply to send.
        """

        target = _ROUTES.get(urlsplit(path).path)
        if target is None:
            reply = _Reply(
                payload={"error": {"message": f"No such path: {path}"}}, status=404
            )
            with self._lock:
                self._requests.append(
                    RecordedRequest(
                        agent=None,
                        body={},
                        break_index=None,
                        page_index=None,
                        path=path,
                        provider=None,
                        route=None,
                        status=404,
                    )
                )
            return reply

        provider, route = target
        if route == "model":
            self._model_request_seen.set()
            with self._lock:
                self._in_flight += 1
                self._max_in_flight = max(self._max_in_flight, self._in_flight)
            if self._delay_seconds:
                time.sleep(self._delay_seconds)
        parsed = (
            _parse_upload(body=body, content_type=content_type)
            if route == "upload"
            else _parse_json(body)
        )
        target = _request_target(parsed) if route == "model" else None
        with self._lock:
            if route == "model":
                self._in_flight -= 1
            fault = self._take_fault(route)
            if fault is not None:
                default = f"{responses.get(fault.status, 'Error')} (mock provider)"
                reply = _error(
                    message=fault.message or default,
                    provider=provider,
                    status=fault.status,
                )
            elif route == "upload":
                reply = self._upload_reply(body=parsed, provider=provider)
            else:
                reply = self._model_reply(body=parsed, provider=provider)
            self._requests.append(
                RecordedRequest(
                    agent=None if target is None else target.agent,
                    body=parsed,
                    break_index=None if target is None else target.break_index,
                    page_index=None if target is None else target.page_index,
                    path=path,
                    provider=provider,
                    route=route,
                    status=reply.status,
                )
            )
        return reply

    def _model_reply(self, *, body: dict[str, object], provider: Provider) -> _Reply:
        """Answer a model request that no fault stops. Call with the lock held.

        Parameters
        ----------
        body
            The request's JSON body.
        provider
            The provider the request is for.

        Returns
        -------
        _Reply
            HTTP 404 naming the first file ID the server does not hold, or else the
            break's next answer for a page-break request, the page's answer for a page
            extraction request, the next survey verdict for a survey verifier
            request, or the next survey answer. HTTP 400 when there is no such
            answer.
        """

        missing = [
            file_id
            for file_id in _file_ids(body)
            if file_id not in self._files[provider]
        ]
        if missing:
            return _error(
                message=f"File not found: {missing[0]}", provider=provider, status=404
            )

        target = _request_target(body)
        agent = target.agent
        if target.break_index is not None:
            answer = _next_answer(
                answers=self._break_answers,
                key=target.break_index,
                sent=self._break_answers_sent,
            )
            wanted = f"answer for the break after page index {target.break_index}"
        elif target.page_index is not None and agent is not None:
            answer = _next_answer(
                answers=self._page_answers,
                key=(target.page_index, agent),
                sent=self._page_answers_sent,
            )
            wanted = f"{agent} answer for page index {target.page_index}"
        elif agent == "verifier":
            answer = self._survey_verdict()
            wanted = "survey verdict"
        else:
            answer = self._survey_answer()
            wanted = "survey answer"
        if answer is None:
            return _error(
                message=f"No {wanted} (mock provider)", provider=provider, status=400
            )
        model = str(body.get("model", "mock-model"))
        if provider == "anthropic":
            return _anthropic_message(answer=answer, model=model, usage=self._usage)
        return _openai_response(answer=answer, model=model, usage=self._usage)

    def _survey_answer(self) -> str | None:
        """Take the next survey answer. Call with the lock held.

        Returns
        -------
        str | None
            The answer, the last one repeating, or ``None`` when there is none.
        """

        if not self._answers:
            return None
        answer = self._answers[min(self._answers_sent, len(self._answers) - 1)]
        self._answers_sent += 1
        return answer

    def _survey_verdict(self) -> str | None:
        """Take the next survey verdict. Call with the lock held.

        Returns
        -------
        str | None
            The verdict, the last one repeating, or ``None`` when there is none.
        """

        if not self._survey_verdicts:
            return None
        verdicts = self._survey_verdicts
        verdict = verdicts[min(self._survey_verdicts_sent, len(verdicts) - 1)]
        self._survey_verdicts_sent += 1
        return verdict

    def _take_fault(self, route: Route) -> _Fault | None:
        """Use up one request of the first fault on a route. Call with the lock held.

        Parameters
        ----------
        route
            The request's route.

        Returns
        -------
        _Fault | None
            The fault the request gets, or ``None``.
        """

        for fault in self._faults:
            if fault.route != route or fault.remaining == 0:
                continue
            if fault.remaining is not None:
                fault.remaining -= 1
            return fault
        return None

    def _upload_reply(self, *, body: dict[str, object], provider: Provider) -> _Reply:
        """Accept an upload that no fault stops. Call with the lock held.

        Parameters
        ----------
        body
            The upload's fields and file summary, from `_parse_upload`.
        provider
            The provider the upload is for.

        Returns
        -------
        _Reply
            The provider's file object, whose ID the server now holds.
        """

        fields = cast("dict[str, str]", body["fields"])
        make = _anthropic_file if provider == "anthropic" else _openai_file
        reply = make(fields=fields, upload=body)
        self._files[provider].add(str(reply.payload["id"]))
        return reply

    def add_fault(
        self,
        *,
        message: str | None = None,
        route: Route,
        status: int,
        times: int | None = 1,
    ) -> None:
        """Make requests on a route fail with an HTTP error.

        Faults apply in the order they were added. A model request that a fault does
        not stop is answered normally.

        Parameters
        ----------
        message
            The error message the provider gives, such as a message that rejects the
            PDF. ``None`` gives one made from the status, such as "Too Many Requests
            (mock provider)".
        route
            ``model`` for model requests, ``upload`` for uploads.
        status
            The HTTP status, such as 429 or 503 (temporary, so the SDKs retry), 401,
            413 or 400.
        times
            How many requests fail, or ``None`` for every request from now on.

        Examples
        --------
        Fail the first three attempts at a model request, so that with two retries
        the request fails for good::

            mock.add_fault(route="model", status=429, times=3)

        Reject the PDF on every model request::

            mock.add_fault(message="The PDF is too large.", route="model",
                           status=400, times=None)
        """

        fault = _Fault(message=message, remaining=times, route=route, status=status)
        with self._lock:
            self._faults.append(fault)

    @property
    def anthropic_base_url(self) -> str:
        """The value for ``ANTHROPIC_BASE_URL``."""

        return f"{self.url}/anthropic"

    def environment(self) -> dict[str, str]:
        """Environment variables that send both SDKs to this server.

        Returns
        -------
        dict[str, str]
            Both base URLs, and `PLACEHOLDER_KEY` as both API keys.
        """

        return {
            "ANTHROPIC_API_KEY": PLACEHOLDER_KEY,
            "ANTHROPIC_BASE_URL": self.anthropic_base_url,
            "OPENAI_API_KEY": PLACEHOLDER_KEY,
            "OPENAI_BASE_URL": self.openai_base_url,
        }

    def forget_uploads(self) -> None:
        """Drop every uploaded file, as if each upload had expired.

        A later model request that names one of them gets HTTP 404 naming its ID.
        """

        with self._lock:
            for file_ids in self._files.values():
                file_ids.clear()

    @property
    def max_in_flight(self) -> int:
        """The most model requests the server has been answering at the same time."""

        return self._max_in_flight

    @property
    def openai_base_url(self) -> str:
        """The value for ``OPENAI_BASE_URL``."""

        return f"{self.url}/openai/v1"

    @property
    def requests(self) -> list[RecordedRequest]:
        """Every request received so far, oldest first."""

        with self._lock:
            return list(self._requests)

    def start(self) -> None:
        """Start listening, in a background thread.

        Raises
        ------
        RuntimeError
            If the server is already running.
        """

        if self._server is not None:
            raise RuntimeError("The mock provider server is already running")
        self._server = _Server(mock=self, port=self._port)
        self._thread = threading.Thread(
            daemon=True,
            kwargs={"poll_interval": _POLL_INTERVAL_SECONDS},
            name="mock-providers",
            target=self._server.serve_forever,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop listening and wait for the background thread to end."""

        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join()
        self._server = None
        self._thread = None

    @property
    def url(self) -> str:
        """The server's address, such as ``http://127.0.0.1:50123``.

        Raises
        ------
        RuntimeError
            If the server is not running.
        """

        if self._server is None:
            raise RuntimeError("The mock provider server is not running")
        return f"http://{_HOST}:{self._server.server_address[1]}"

    def wait_for_model_request(self, timeout: float) -> bool:
        """Wait until the first model request arrives, or the timeout passes.

        Parameters
        ----------
        timeout
            The most seconds to wait.

        Returns
        -------
        bool
            Whether a model request arrived.
        """

        return self._model_request_seen.wait(timeout)


def main(argv: Sequence[str] | None = None) -> None:
    """Serve the stand-in until interrupted, printing the base URLs to use.

    Parameters
    ----------
    argv
        The command-line arguments, or ``None`` to read them from ``sys.argv``.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Serve stand-ins for the Anthropic and OpenAI APIs on 127.0.0.1 until "
            "interrupted. Set any non-empty ANTHROPIC_API_KEY or OPENAI_API_KEY."
        ),
        prog="python -m tests.fixtures.mock_providers",
    )
    parser.add_argument(
        "--answer",
        help=(
            "JSON file with the survey answer each model request that names no "
            "page or break gets"
        ),
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--break-answers",
        help=(
            "JSON file with page-break verification's answers, by the index of the "
            "page before the break"
        ),
        type=Path,
    )
    parser.add_argument(
        "--page-answers",
        help="JSON file with page extraction's answers, by page index and agent",
        type=Path,
    )
    parser.add_argument(
        "--port", default=0, help="port to listen on (default: any free port)", type=int
    )
    arguments = parser.parse_args(argv)

    answer = json.loads(arguments.answer.read_text(encoding="utf-8"))
    page_answers = (
        read_page_answers(arguments.page_answers)
        if arguments.page_answers is not None
        else None
    )
    break_answers = (
        read_break_answers(arguments.break_answers)
        if arguments.break_answers is not None
        else None
    )
    with MockProviders(
        answers=[answer],
        break_answers=break_answers,
        page_answers=page_answers,
        port=arguments.port,
        verbose=True,
    ) as mock:
        print(f"ANTHROPIC_BASE_URL={mock.anthropic_base_url}")
        print(f"OPENAI_BASE_URL={mock.openai_base_url}")
        print("Serving; press Ctrl+C to stop.", flush=True)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


def read_break_answers(path: Path) -> dict[int, Answer | list[Answer]]:
    """Read a break answers file: answers by the page before the break.

    Parameters
    ----------
    path
        A JSON file whose keys are the indexes of the pages before the breaks and
        whose values are an answer or a list of answers, which the break's requests
        get in the order they arrive.

    Returns
    -------
    dict[int, Answer | list[Answer]]
        The answers, for `MockProviders`' ``break_answers``.
    """

    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        int(index): cast("Answer | list[Answer]", given)
        for index, given in data.items()
    }


def read_page_answers(path: Path) -> dict[int, dict[str, Answer | list[Answer]]]:
    """Read a page answers file: answers by page index, then agent.

    Parameters
    ----------
    path
        A JSON file whose keys are page indexes and whose values map ``extractor``
        and ``verifier`` to an answer or a list of answers.

    Returns
    -------
    dict[int, dict[str, Answer | list[Answer]]]
        The answers, for `MockProviders`' ``page_answers``.
    """

    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        int(index): cast("dict[str, Answer | list[Answer]]", by_agent)
        for index, by_agent in data.items()
    }


if __name__ == "__main__":
    main()

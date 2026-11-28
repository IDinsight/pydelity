"""Tests for the page-break verification step: verdict files, reuse, the verifier.

Each test makes a small PDF of blank pages, surveys it and extracts its pages against
the stand-in provider server, then judges the breaks between the pages. Each page's
answer is one line of text, so its page file has one item, ``p<NNNN>-001``; a page
answer can also have no items, which gives a page with no content items. Blank pages
have no text layer, so page extraction compares no text.
"""

# Standard Library
import asyncio
import base64
import json
import re
import warnings

from collections.abc import Callable, Sequence
from decimal import Decimal
from pathlib import Path

# Third Party Library
import pymupdf
import pytest

from typer.testing import Result

# Package Library
import pydelity

from pydelity.cli import ExitCode
from pydelity.errors import (
    BudgetExceededError,
    PageBreakError,
    ProviderError,
    PydelityWarning,
)
from pydelity.pipeline.schemas import BreakCounts
from tests.fixtures.mock_providers import (
    OUTPUT_LIMIT,
    REFUSAL,
    MockProviders,
    RecordedRequest,
)

# The survey's labels: one for content of every kind that can continue, and one for
# page furniture.
_LABELS = [
    {
        "description": "Running text, code, lists and tables.",
        "kinds": ["code", "list", "table", "text"],
        "name": "Body",
        "role": "body",
    },
    {
        "description": "Running headers and page numbers.",
        "kinds": ["text"],
        "name": "Page furniture",
        "role": "artifact",
    },
]

# A verdict that nothing continues.
_NOTHING_CONTINUES = {
    "containers": [],
    "continues": False,
    "pieces": [],
    "reason": "Each page ends with a whole line.",
}

# What PydanticAI puts around a retry message in the request that follows it.
_RETRY_FEEDBACK = re.compile(
    r"<pyai:retry_feedback>(.*?)</pyai:retry_feedback>", flags=re.DOTALL
)

# The survey's start marker in tests of hints: each page after the first starts
# with it.
_START_MARKER = {"description": "Starts a new part.", "text": "Part"}


def _break_agents(*, start: int = 0) -> list[tuple[str, int | None]]:
    """List the agent and break of each page-break line in the cost ledger.

    The judge's and the verifier's requests are the same, so the stand-in cannot
    tell them apart. The ledger in ``out`` says which agent sent each request.

    Parameters
    ----------
    start
        How many of the ledger's lines to skip, such as the count before a run.

    Returns
    -------
    list[tuple[str, int | None]]
        Each page-break request's agent and the page before its break, in the order
        the ledger has them.
    """

    return [
        (entry.agent, entry.page_index)
        for entry in pydelity.load("out").ledger[start:]
        if entry.step == "page_breaks"
    ]


def _break_requests(mock: MockProviders, *, start: int = 0) -> list[RecordedRequest]:
    """List the page-break requests the stand-in got, in the order they arrived.

    Parameters
    ----------
    mock
        The stand-in server.
    start
        How many of its requests to skip, such as the count before a run.

    Returns
    -------
    list[RecordedRequest]
        Each request that names a break.
    """

    return [
        request for request in mock.requests[start:] if request.break_index is not None
    ]


def _image_sizes(request: RecordedRequest) -> list[tuple[int, int]]:
    """Measure the images an Anthropic model request sent.

    Parameters
    ----------
    request
        The recorded request.

    Returns
    -------
    list[tuple[int, int]]
        Each image's width and height in pixels, in the order sent.
    """

    messages = request.body["messages"]
    assert isinstance(messages, list)
    sizes = []
    for part in messages[0]["content"]:
        if part.get("type") == "image":
            data = base64.b64decode(part["source"]["data"])
            pixmap = pymupdf.Pixmap(data)
            sizes.append((pixmap.width, pixmap.height))
    return sizes


def _joined(earlier_page_index: int, **changes: object) -> dict[str, object]:
    """Write a verdict whose one piece joins the line of a page to the next page's.

    Parameters
    ----------
    earlier_page_index
        The page before the break.
    **changes
        Fields of the piece to replace.

    Returns
    -------
    dict[str, object]
        The verdict, as JSON-ready data, joining the two items with a space.
    """

    piece: dict[str, object] = {
        "cell_joins": None,
        "earlier_entry": None,
        "earlier_item": f"p{earlier_page_index:04d}-001",
        "join": "continue_text",
        "later_entry": None,
        "later_item": f"p{earlier_page_index + 1:04d}-001",
        "markers": [],
        "repeated_header_rows": None,
        "repeated_items": [],
        "text_join": "space",
    }
    piece.update(changes)
    return {
        "containers": [],
        "continues": True,
        "pieces": [piece],
        "reason": "The sentence carries on to the next page.",
    }


def _page_answer(*texts: str) -> dict[str, object]:
    """Write a page answer with one item of body text per line.

    Parameters
    ----------
    *texts
        The lines, top to bottom; none gives a page with no items.

    Returns
    -------
    dict[str, object]
        The answer, as JSON-ready data.
    """

    items = [
        {
            "box": [100, 100 + 100 * index, 900, 150 + 100 * index],
            "caption_of": None,
            "container": None,
            "entries": None,
            "field": None,
            "figure": None,
            "kind": "text",
            "label": "Body",
            "language": "en",
            "latex": None,
            "ref": f"t{index + 1}",
            "role": "body",
            "table": None,
            "text": text,
        }
        for index, text in enumerate(texts)
    ]
    return {"column_order": None, "containers": [], "items": items}


def _sent(mock: MockProviders, *, start: int = 0) -> list[tuple[str, int]]:
    """List the sender and page or break of each model request after the survey's.

    Parameters
    ----------
    mock
        The stand-in server.
    start
        How many of its requests to skip, such as the count before a run.

    Returns
    -------
    list[tuple[str, int]]
        Each page request's agent and page index, and ``break`` with the break's
        earlier page index for each page-break request, sorted, so the order
        concurrent requests arrive in does not matter. A page-break request does not
        say which agent sent it, and `_break_agents` reads that from the ledger.
    """

    return sorted(
        (request.agent or "break", request.page_index or request.break_index or 0)
        for request in mock.requests[start:]
        if request.route == "model"
        and (request.page_index is not None or request.break_index is not None)
    )


def _start(
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
    *,
    break_answers: dict[int, object],
    pages: Sequence[Sequence[str]],
    **options: object,
) -> MockProviders:
    """Start the stand-in with a survey answer, page answers and break answers.

    Parameters
    ----------
    mock_providers
        The fixture that starts the stand-in.
    survey_answer
        The fixture that writes a survey answer.
    break_answers
        The answers by the break's earlier page: one answer, or a list whose next
        item each of the break's requests gets, the judge's first, the last one
        repeating.
    pages
        Each page's lines, in page order.
    **options
        Other options of the stand-in, and ``survey`` for survey answer keys to
        replace.

    Returns
    -------
    MockProviders
        The started stand-in.
    """

    survey = options.pop("survey", {})
    assert isinstance(survey, dict)
    return mock_providers(
        answers=[survey_answer(labels=_LABELS, **survey)],
        break_answers=break_answers,
        page_answers={
            index: {"extractor": _page_answer(*lines)}
            for index, lines in enumerate(pages)
        },
        **options,
    )


def _text(page_count: int) -> list[list[str]]:
    """Write each page's one line for a PDF of this many pages.

    Parameters
    ----------
    page_count
        How many pages.

    Returns
    -------
    list[list[str]]
        Each page's lines: the first page starts a sentence and each later page
        starts with the survey's start marker.
    """

    return [["The notice starts here and"]] + [
        [f"Part {index + 1} goes on from the page before."]
        for index in range(1, page_count)
    ]


def test_a_damaged_verdict_file_warns_and_its_break_is_judged_again(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """A verdict file that does not load gives ``damaged_output`` and is rewritten."""

    pdf = blank_pdf(2)
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers={0: _NOTHING_CONTINUES},
        pages=_text(2),
    )
    pydelity.run(pdf, output_dir="out", pause=False)
    Path("out/page_breaks/0000-0001.json").write_text("{not json", encoding="utf-8")
    before = len(mock.requests)

    with pytest.warns(
        PydelityWarning,
        match=r"judging the break after page 1 \(pages 1 and 2\) again",
    ):
        result = pydelity.run(pdf, output_dir="out", pause=False)

    assert _sent(mock, start=before) == [("break", 0)]
    assert result.record is not None
    (warning,) = result.record.warnings
    assert (warning.code, warning.step) == ("damaged_output", "page_breaks")
    assert [break_file.earlier_page_index for break_file in result.breaks] == [0]


def test_a_failed_check_is_sent_back_then_the_last_verdict_is_kept_for_review(
    blank_pdf: Callable[..., Path],
    log_messages: list[tuple[str, str]],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """A verdict failing a check is sent back once, then kept with its failure.

    With one retry, the judge says twice that content continues but names no
    piece. The second request carries the retry message, the run completes, and
    the failure is on the verdict file, in ``run.json``'s review list and in the
    summary's lines.
    """

    pdf = blank_pdf(2)
    wrong = _NOTHING_CONTINUES | {"continues": True}
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers={0: [wrong, wrong]},
        pages=_text(2),
    )

    result = pydelity.run(
        pdf,
        advanced={"page_breaks": {"check_retries": 1}},
        output_dir="out",
        pause=False,
    )

    judge = _break_requests(mock)
    assert len(judge) == 2
    assert _break_agents() == [("judge", 0), ("judge", 0)]
    (retry,) = _RETRY_FEEDBACK.findall(json.dumps(judge[1].body, ensure_ascii=False))
    assert "continues: continues is true, but pieces is empty" in retry
    (break_file,) = result.breaks
    assert break_file.verdict.continues is True
    checks = {check.name: check for check in break_file.checks}
    assert (checks["continues"].passed, checks["continues"].attempts) == (False, 2)
    message = (
        "pages 1 and 2: continues: continues is true, but pieces is empty. Name "
        "each piece that continues, or set continues to false"
    )
    assert result.record is not None
    assert result.record.status == "completed"
    assert [
        (issue.step, issue.check, issue.message) for issue in result.record.review
    ] == [("page_breaks", "continues", message)]
    assert ("INFO", f"  page_breaks: {message}") in log_messages


def test_a_failed_request_stops_the_run_and_the_next_run_judges_only_the_rest(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """A request the provider rejects stops the run; written verdicts stay.

    One break at a time, the first break is judged and written, and the second
    break's request is rejected. The run ends ``failed`` with `ProviderError`.
    The next run makes one request, for the second break.
    """

    pdf = blank_pdf(3)
    settings = {"concurrent_breaks": 1}
    _start(
        mock_providers,
        survey_answer,
        break_answers={0: _NOTHING_CONTINUES},
        pages=_text(3),
    )

    with pytest.raises(
        ProviderError, match=r"No answer for the break after page index 1"
    ):
        pydelity.run(
            pdf, advanced={"page_breaks": settings}, output_dir="out", pause=False
        )

    assert Path("out/page_breaks/0000-0001.json").is_file()
    assert not Path("out/page_breaks/0001-0002.json").exists()
    record = pydelity.load("out").record
    assert record is not None
    assert (record.status, record.steps[2].status) == ("failed", "failed")

    retry = _start(
        mock_providers,
        survey_answer,
        break_answers={1: _NOTHING_CONTINUES},
        pages=_text(3),
    )
    result = pydelity.run(
        pdf, advanced={"page_breaks": settings}, output_dir="out", pause=False
    )

    assert _sent(retry) == [("break", 1)]
    assert [break_file.earlier_page_index for break_file in result.breaks] == [0, 1]
    assert result.record is not None
    assert result.record.steps[2].breaks == BreakCounts(judged=1, reused=1, total=2)


def test_a_narrowed_pages_judges_every_break_once_the_other_pages_are_current(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """A run on the second page judges the break once the first page is current.

    The first run, on page 1, leaves page 2 without a page file, so it judges no
    break. Then the estimate for page 2 without the pause covers page-break
    verification, and the run on page 2 extracts it and judges the PDF's one
    break.
    """

    pdf = blank_pdf(2)
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers={0: _NOTHING_CONTINUES},
        pages=_text(2),
    )

    with pytest.warns(PydelityWarning, match="page 2 has none"):
        first = pydelity.run(pdf, output_dir="out", pages="1", pause=False)
    estimate = pydelity.estimate(pdf, output_dir="out", pages="2", pause=False)
    second = pydelity.run(pdf, output_dir="out", pages="2", pause=False)

    assert first.breaks == []
    assert [step.name for step in estimate.steps] == [
        "survey",
        "extraction",
        "page_breaks",
    ]
    assert (estimate.steps[2].breaks, estimate.steps[2].reused) == (1, False)
    assert _sent(mock) == [("break", 0), ("extractor", 0), ("extractor", 1)]
    assert second.record is not None
    assert [step.status for step in second.record.steps] == [
        "reused",
        "completed",
        "completed",
    ]
    assert second.record.warnings == []
    assert [break_file.earlier_page_index for break_file in second.breaks] == [0]


def test_a_one_page_pdf_makes_no_page_break_request_and_completes(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """A PDF with one page has no break: the step is skipped and the run completes."""

    pdf = blank_pdf(1)
    mock = _start(mock_providers, survey_answer, break_answers={}, pages=_text(1))

    result = pydelity.run(pdf, output_dir="out", pause=False)

    assert _sent(mock) == [("extractor", 0)]
    assert result.record is not None
    assert result.record.status == "completed"
    assert result.record.steps[2].status == "skipped"
    assert result.breaks == []
    assert not Path("out/page_breaks").exists()


def test_a_page_break_request_first_shows_the_estimate_and_a_no_stops_it_unsent(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """With every page file current, the CLI estimates and asks before judging.

    The survey and page extraction are reused, so the first request of the run
    would be a page-break request. Answering no stops the run with nothing sent.
    """

    pdf = blank_pdf(3)
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers={0: _NOTHING_CONTINUES},
        pages=_text(3),
    )
    pydelity.extract(pdf, output_dir="out")
    before = len(mock.requests)

    result = run_cli([str(pdf), "-d", "out"], input="n\n", terminal=True)

    assert result.exit_code == ExitCode.STOPPED, result.output
    assert "Page-break verification cost estimate" in result.stderr
    assert "(2 breaks, up to 6 requests to anthropic:claude-opus-5-5)" in result.stderr
    assert result.stderr.index("Page-break verification cost estimate") < (
        result.stderr.index("Go ahead with the model requests?")
    )
    assert len(mock.requests) == before
    record = pydelity.load("out").record
    assert record is not None
    assert record.status == "stopped"


def test_a_page_with_no_content_items_and_turning_on_the_step_s_verifier(
    blank_pdf: Callable[..., Path],
    log_messages: list[tuple[str, str]],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """A page with no items gives ``no_content`` verdicts, which the verifier skips.

    The third page has no items, so its break gets a verdict that nothing
    continues with no request. Turning on page-break verification's verifier then
    sends the verifier's request alone for the first break, and the estimate
    prices that request alone. The judge's verdict, checks and start-marker hint
    difference are kept, the file gains the verifier's judgment, and the second
    break is reused. A run after that sends no request.
    """

    pdf = blank_pdf(3)
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers={0: _joined(0)},
        pages=[*_text(2), []],
        survey={"start_markers": [_START_MARKER]},
    )
    verify = {"page_breaks": {"verify": True}}

    first = pydelity.run(pdf, output_dir="out", pause=False)
    before = len(mock.requests)
    estimate = pydelity.estimate(pdf, advanced=verify, output_dir="out", pause=False)
    second = pydelity.run(pdf, advanced=verify, output_dir="out", pause=False)
    after = len(mock.requests)
    third = pydelity.run(pdf, advanced=verify, output_dir="out", pause=False)

    assert _break_agents() == [("judge", 0), ("verifier", 0)]
    assert [request.break_index for request in mock.requests[before:]] == [0]
    assert len(mock.requests) == after
    step = estimate.steps[2]
    assert (step.name, step.breaks, step.verifier, step.requests_max) == (
        "page_breaks",
        1,
        True,
        3,
    )
    kept, verified = first.breaks[0], second.breaks[0]
    assert kept.verification is None
    assert [issue.check for issue in kept.issues] == ["start_markers"]
    assert verified.model_dump(
        include={"checks", "fingerprint", "hints", "inputs", "judgment", "verdict"}
    ) == kept.model_dump(
        include={"checks", "fingerprint", "hints", "inputs", "judgment", "verdict"}
    )
    assert verified.judged_at > kept.judged_at
    assert verified.verification is not None
    assert verified.verification.differences == []
    assert verified.verification.verdict == kept.verdict
    assert verified.issues == []
    assert (
        "INFO",
        "Break after page 1 (pages 1 and 2): no verifier judged it, so the verifier "
        "judges it now and the judge's verdict is kept",
    ) in log_messages
    assert third.record is not None
    assert third.record.steps[2].status == "reused"
    no_content = first.breaks[1]
    assert (no_content.judgment, no_content.verification) == ("no_content", None)
    assert no_content.verdict.model_dump() == {
        "containers": [],
        "continues": False,
        "pieces": [],
        "reason": "Page 3 has no content items, so nothing can carry on across the "
        "break.",
    }
    assert {(check.attempts, check.passed) for check in no_content.checks} == {
        (0, True)
    }
    assert second.breaks[1] == no_content
    assert second.record is not None
    assert second.record.steps[2].breaks == BreakCounts(judged=1, reused=1, total=2)


@pytest.mark.parametrize(
    ("model", "answer", "message"),
    [
        ("anthropic:claude-opus-5-5", REFUSAL, "judge: the model refused."),
        (
            "openai:gpt-6.2-astra",
            OUTPUT_LIMIT,
            "judge: the model used all 32,000 output tokens before finishing its "
            "answer. Raise advanced.page_breaks.max_output_tokens, or lower "
            "advanced.page_breaks.effort.",
        ),
    ],
    ids=["refusal", "output-limit"],
)
def test_a_refusal_or_used_up_output_tokens_stops_the_run_unretried(  # noqa: PLR0913, PLR0917 - fixtures and parameters
    answer: str,
    blank_pdf: Callable[..., Path],
    message: str,
    mock_providers: Callable[..., MockProviders],
    model: str,
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """A judge reply with no verdict raises `PageBreakError` naming the break.

    Asking again would get the same reply, so the judge is asked once, and the run
    is recorded ``failed``.
    """

    pdf = blank_pdf(2)
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers={0: answer},
        pages=_text(2),
    )

    with pytest.raises(PageBreakError) as raised:
        pydelity.run(pdf, model=model, output_dir="out", pause=False)

    assert str(raised.value).startswith(
        f"Break after page 1 (pages 1 and 2), {message}"
    )
    assert len(_break_requests(mock)) == 1
    record = pydelity.load("out").record
    assert record is not None
    assert record.status == "failed"


def test_a_refused_verifier_request_keeps_the_judge_s_verdict_for_the_next_run(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """A failed verifier request stops the run after the judge's verdict is saved.

    The verifier's request is refused, so the run fails with `PageBreakError`
    naming the verifier, and the verdict file keeps the judge's verdict with no
    verification. The next run with the verifier on sends the verifier's request
    alone and keeps the judge's verdict and checks.
    """

    pdf = blank_pdf(2)
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers={0: [_joined(0), REFUSAL, _joined(0)]},
        pages=_text(2),
    )
    verify = {"page_breaks": {"verify": True}}

    with pytest.raises(
        PageBreakError,
        match=r"^Break after page 1 \(pages 1 and 2\), verifier: the model refused\.",
    ):
        pydelity.run(pdf, advanced=verify, output_dir="out", pause=False)

    loaded = pydelity.load("out")
    assert loaded.record is not None
    assert (loaded.record.status, loaded.record.steps[2].status) == (
        "failed",
        "failed",
    )
    (saved,) = loaded.breaks
    assert saved.verdict.model_dump(mode="json") == _joined(0)
    assert saved.verification is None
    before, ledger = len(mock.requests), len(loaded.ledger)

    result = pydelity.run(pdf, advanced=verify, output_dir="out", pause=False)

    assert len(_break_requests(mock, start=before)) == 1
    assert _break_agents(start=ledger) == [("verifier", 0)]
    (break_file,) = result.breaks
    assert (break_file.verdict, break_file.checks) == (saved.verdict, saved.checks)
    assert break_file.verification is not None
    assert break_file.verification.differences == []


def test_a_verifier_verdict_that_fails_a_check_is_sent_back_then_compared_as_it_is(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """The verifier's verdict is sent back for a failed check, as the judge's is.

    With one retry, the verifier twice starts the piece in an item the later page
    does not have. Its first request carries no retry message and its second one
    does. The judge's verdict is kept. The verifier's last verdict is saved with
    its failed check and compared as it is, and only the difference is a review
    issue.
    """

    pdf = blank_pdf(2)
    wrong = _joined(0, later_item="p0001-009")
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers={0: [_joined(0), wrong, wrong]},
        pages=_text(2),
    )

    result = pydelity.run(
        pdf,
        advanced={"page_breaks": {"check_retries": 1, "verify": True}},
        output_dir="out",
        pause=False,
    )

    _, first, second = _break_requests(mock)
    assert _break_agents() == [("judge", 0), ("verifier", 0), ("verifier", 0)]
    assert _RETRY_FEEDBACK.findall(json.dumps(first.body, ensure_ascii=False)) == []
    (retry,) = _RETRY_FEEDBACK.findall(json.dumps(second.body, ensure_ascii=False))
    assert "p0001-009, which is not an item on the later page" in retry
    (break_file,) = result.breaks
    assert break_file.verdict.model_dump(mode="json") == _joined(0)
    assert all(check.passed for check in break_file.checks)
    verification = break_file.verification
    assert verification is not None
    assert verification.attempts == 2
    assert verification.verdict.model_dump(mode="json") == wrong
    assert [
        (check.name, check.attempts)
        for check in verification.checks
        if not check.passed
    ] == [("ids", 2)]
    assert [difference.details["field"] for difference in verification.differences] == [
        "start"
    ]
    assert [issue.check for issue in break_file.issues] == ["verdicts_differ"]


def test_an_unusable_judge_answer_stops_the_cli_with_exit_code_1(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """A judge that never answers in the verdict format stops the command.

    The judge is asked once and again for each of the two check retries. The CLI
    shows the error and exits 1, and no verdict file is written.
    """

    pdf = blank_pdf(2)
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers={0: "I cannot tell from these pages."},
        pages=_text(2),
    )

    result = run_cli([str(pdf), "-d", "out", "-y", "-np"])

    assert result.exit_code == ExitCode.FAILED, result.output
    assert (
        "Break after page 1 (pages 1 and 2), judge: the model gave no usable answer"
        in result.stderr
    )
    assert len(_break_requests(mock)) == 3
    assert not Path("out/page_breaks/0000-0001.json").exists()
    record = pydelity.load("out").record
    assert record is not None
    assert (record.status, record.steps[2].status) == ("failed", "failed")


def test_break_requests_sent_at_once_are_held_to_max_cost_together(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """Page-break requests in flight count toward ``max_cost`` together.

    Output is priced so that one request's highest cost fits what is left of
    ``max_cost`` and two do not. The stand-in holds each break request for a
    second, so the first is still in flight when the next is checked. Three breaks
    at once stop with the warning, which counts the request in flight and the
    next, before the second is sent. One break at a time completes with no
    warning.
    """

    pdf = blank_pdf(4)
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers=dict.fromkeys(range(3), _NOTHING_CONTINUES),
        pages=_text(4),
    )
    pydelity.extract(pdf, output_dir="out")
    spent = sum(
        (entry.cost_usd or Decimal(0) for entry in pydelity.load("out").ledger),
        start=Decimal(0),
    )
    prices = {
        "anthropic:claude-opus-5-5": {
            "input_usd_per_mtok": "0",
            "output_usd_per_mtok": "1000",
        }
    }
    before = len(mock.requests)
    mock.delay_seconds = 1.0

    with (
        pytest.raises(BudgetExceededError),
        pytest.warns(PydelityWarning, match="could go over max_cost") as issued,
    ):
        pydelity.verify_breaks(
            pdf,
            advanced={"models": prices, "page_breaks": {"concurrent_breaks": 3}},
            max_cost=spent + 40,
            output_dir="out",
        )
    held = len(_sent(mock, start=before))
    mock.delay_seconds = 0
    with warnings.catch_warnings():
        warnings.simplefilter("error", PydelityWarning)
        verdicts = pydelity.verify_breaks(
            pdf,
            advanced={"models": prices, "page_breaks": {"concurrent_breaks": 1}},
            max_cost=spent + 40,
            output_dir="out",
        )

    # Each request's highest cost is its 32,000 output tokens at $1,000 per
    # million: $32. The warning counts the request in flight and the next one on
    # top of what is already spent.
    (warning,) = issued
    found = re.search(
        r"\$([0-9.,]+) already spent .* makes \$([0-9.,]+)", str(warning.message)
    )
    assert found is not None
    already, projected = (
        Decimal(found[group].rstrip(",").replace(",", "")) for group in (1, 2)
    )
    assert abs(already - spent) < Decimal("0.01")
    assert abs(projected - already - 64) < Decimal("0.01")
    assert held <= 1
    assert [verdict.earlier_page_index for verdict in verdicts] == [0, 1, 2]


def test_extracting_one_page_again_judges_only_the_two_breaks_beside_it(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """A new page file for the second of four pages re-judges breaks 1 and 2 only.

    The third break's verdict is reused, and the survey is not asked again.
    """

    pdf = blank_pdf(4)
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers={index: _joined(index) for index in range(3)},
        pages=_text(4),
    )
    first = pydelity.run(pdf, output_dir="out", pause=False)
    Path("out/pages/0001.json").unlink()
    before = len(mock.requests)

    second = pydelity.run(pdf, output_dir="out", pause=False)

    assert _sent(mock, start=before) == [("break", 0), ("break", 1), ("extractor", 1)]
    assert second.record is not None
    assert second.record.steps[2].breaks == BreakCounts(judged=2, reused=1, total=3)
    assert second.breaks[2] == first.breaks[2]
    assert second.breaks[0].judged_at > first.breaks[0].judged_at


def test_load_leaves_out_a_verdict_whose_page_file_changed(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """After page 2 is extracted again, ``load`` gives the pages but not the verdict."""

    pdf = blank_pdf(2)
    _start(
        mock_providers,
        survey_answer,
        break_answers={0: _NOTHING_CONTINUES},
        pages=_text(2),
    )
    pydelity.run(pdf, output_dir="out", pause=False)
    Path("out/pages/0001.json").unlink()
    pydelity.extract(pdf, output_dir="out", pages="2")

    loaded = pydelity.load("out")

    assert [page.page_index for page in loaded.pages] == [0, 1]
    assert loaded.breaks == []
    assert Path("out/page_breaks/0000-0001.json").is_file()


def test_rotated_pages_are_sent_upright_with_boxes_on_the_upright_grid(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """Each page of a break is sent as its page file's upright image.

    The first page is displayed upright but its content is turned sideways, and
    the second page's rotation attribute is 90. The survey's turns make the first
    image landscape and the second portrait, each request says how the image was
    turned, and each item's box comes back on the grid page extraction gave it.
    """

    pdf = blank_pdf(2, rotations=[0, 90])
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers={0: _NOTHING_CONTINUES},
        pages=_text(2),
        survey={
            "rotation": [
                {"degrees": 90, "first_page_index": 0, "last_page_index": 0},
                {"degrees": 270, "first_page_index": 1, "last_page_index": 1},
            ]
        },
    )

    result = pydelity.run(pdf, output_dir="out", pause=False)

    assert [page.rotation for page in result.pages] == [90, 270]
    (judge,) = _break_requests(mock)
    (earlier, later) = _image_sizes(judge)
    assert earlier[0] > earlier[1]
    assert later[0] < later[1]
    messages = judge.body["messages"]
    assert isinstance(messages, list)
    earlier_text, later_text = [
        part["text"] for part in messages[0]["content"] if part["type"] == "text"
    ][:2]
    for text, degrees in ((earlier_text, 90), (later_text, 270)):
        assert (
            f"The image was turned {degrees} degrees clockwise to show the page "
            "upright." in text
        )
        assert '"box": [100, 100, 900, 150]' in text


def test_run_pauses_after_the_survey_and_page_extraction_then_judges(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """With default settings, three runs survey, extract, then judge the breaks.

    Each run records every step. No verifier runs, so no ledger line is a
    page-break verifier's and the verdict file has no verification.
    """

    pdf = blank_pdf(2)
    _start(
        mock_providers,
        survey_answer,
        break_answers={0: _NOTHING_CONTINUES},
        pages=_text(2),
    )

    runs = [pydelity.run(pdf, output_dir="out") for _ in range(3)]

    records = [run.record for run in runs]
    assert all(record is not None for record in records)
    assert [
        (record.status, [step.status for step in record.steps])
        for record in records
        if record is not None
    ] == [
        ("paused", ["completed", "skipped", "skipped"]),
        ("paused", ["reused", "completed", "skipped"]),
        ("completed", ["reused", "reused", "completed"]),
    ]
    (break_file,) = runs[2].breaks
    assert break_file.verification is None
    assert [
        (entry.step, entry.agent)
        for entry in runs[2].ledger
        if entry.step == "page_breaks"
    ] == [("page_breaks", "judge")]


def test_the_api_judges_what_is_missing_without_pausing_and_reuses_it(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """``averify_breaks`` surveys, extracts and judges in one call, in break order.

    It writes no run record or report. Called again, it reuses every verdict.
    """

    pdf = blank_pdf(3)
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers=dict.fromkeys(range(2), _NOTHING_CONTINUES),
        pages=_text(3),
    )

    first = asyncio.run(pydelity.averify_breaks(pdf, output_dir="out"))
    before = len(mock.requests)
    second = pydelity.verify_breaks(pdf, output_dir="out")

    assert _sent(mock) == [
        ("break", 0),
        ("break", 1),
        ("extractor", 0),
        ("extractor", 1),
        ("extractor", 2),
    ]
    assert sorted(_break_agents()) == [("judge", 0), ("judge", 1)]
    assert [verdict.earlier_page_index for verdict in first] == [0, 1]
    assert not Path("out/run.json").exists()
    assert not Path("out/report.html").exists()
    assert len(mock.requests) == before
    assert second == first


def test_the_api_with_a_narrowed_pages_returns_no_verdict_and_warns(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """``verify_breaks`` on page 1 alone extracts it, judges nothing and warns."""

    pdf = blank_pdf(2)
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers={0: _NOTHING_CONTINUES},
        pages=_text(2),
    )

    with pytest.warns(PydelityWarning, match="page 2 has none") as issued:
        verdicts = pydelity.verify_breaks(pdf, output_dir="out", pages="1")

    assert verdicts == []
    assert _sent(mock) == [("extractor", 0)]
    assert [str(warning.message) for warning in issued] == [
        "Page-break verification needs a current page file for every page, and "
        "page 2 has none. Run pydelity again without --pages (pages in the config "
        "file), or with pages that include it, to verify the page breaks."
    ]


def test_the_step_s_instructions_reach_only_its_requests_and_rerun_only_it(
    blank_pdf: Callable[..., Path],
    mock_providers: Callable[..., MockProviders],
    survey_answer: Callable[..., dict[str, object]],
) -> None:
    """Page-break instructions go last to the judge and verifier, and nowhere else.

    The survey's and page extraction's instructions are set for both runs. The
    first run's break requests carry neither, and no page file's inputs. Setting
    page-break verification's instructions then re-judges every break and reruns
    neither earlier step. Both break requests hold the survey's continuation notes
    and start markers and end with the new instructions, which no other request
    holds.
    """

    pdf = blank_pdf(3)
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers=dict.fromkeys(range(2), _NOTHING_CONTINUES),
        pages=_text(3),
        survey={
            "continuation_notes": ["Sentences often carry on to the next page."],
            "start_markers": [_START_MARKER],
        },
    )
    advanced: dict[str, dict[str, object]] = {
        "extraction": {"instructions": "Stamps are content."},
        "page_breaks": {"verify": True},
        "survey": {"instructions": "Margin notes are content."},
    }
    model = "openai:gpt-6.2-astra"
    pydelity.run(pdf, advanced=advanced, model=model, output_dir="out", pause=False)
    before = len(mock.requests)
    ledger = len(pydelity.load("out").ledger)
    advanced["page_breaks"]["instructions"] = "Footnotes carry on."

    result = pydelity.run(
        pdf, advanced=advanced, model=model, output_dir="out", pause=False
    )

    assert result.record is not None
    assert [step.status for step in result.record.steps] == [
        "reused",
        "reused",
        "completed",
    ]
    assert _sent(mock, start=before) == [
        ("break", 0),
        ("break", 0),
        ("break", 1),
        ("break", 1),
    ]
    assert sorted(_break_agents(start=ledger)) == [
        ("judge", 0),
        ("judge", 1),
        ("verifier", 0),
        ("verifier", 1),
    ]
    for position, request in enumerate(mock.requests):
        sent = json.dumps(request.body, ensure_ascii=False)
        if request.break_index is None:
            assert "Footnotes carry on." not in sent
            continue
        assert "Stamps are content." not in sent
        assert "Margin notes are content." not in sent
        assert "pdf_sha256" not in sent
        instructions = str(request.body["instructions"])
        assert "Sentences often carry on to the next page." in instructions
        assert '- "Part": Starts a new part.' in instructions
        if position >= before:
            assert instructions.endswith("\nFootnotes carry on.")
        else:
            assert "The user's instructions" not in instructions


@pytest.mark.parametrize(
    ("verifier", "fields", "issue_checks", "report_line"),
    [
        (_joined(0), [], [], "its verdict matches"),
        (
            _joined(0, text_join="no_space"),
            ["text_join"],
            ["start_markers", "verdicts_differ"],
            "its verdict differs in 1 place: in piece 1 (p0000-001 to p0001-001), "
            "the text join is space in the kept verdict and no_space in the "
            "verifier&#x27;s",
        ),
    ],
    ids=["agrees", "differs"],
)
def test_the_verifier_judges_the_break_again_unseen_and_lists_each_difference(  # noqa: PLR0913, PLR0917 - fixtures and parameters
    blank_pdf: Callable[..., Path],
    fields: list[str],
    issue_checks: list[str],
    mock_providers: Callable[..., MockProviders],
    report_line: str,
    survey_answer: Callable[..., dict[str, object]],
    verifier: dict[str, object],
) -> None:
    """The verifier sends the judge's request again, and code compares the verdicts.

    The second page starts with the survey's start marker, so the judge's verdict
    differs from the hint. The verifier's request equals the judge's, so it never
    sees the judge's verdict. When the verifier's verdict matches, nothing is
    listed, not even the hint difference, and the report says so. When its text
    join differs, the hint difference and the difference are review issues, and no
    third request is made. The verdict file keeps the hint difference and the
    verifier's verdict either way, and ``run.json`` lists the same issues.
    """

    pdf = blank_pdf(2)
    mock = _start(
        mock_providers,
        survey_answer,
        break_answers={0: [_joined(0), verifier]},
        pages=_text(2),
        survey={"start_markers": [_START_MARKER]},
    )

    result = pydelity.run(
        pdf,
        advanced={"page_breaks": {"verify": True}},
        output_dir="out",
        pause=False,
    )

    judge, again = _break_requests(mock)
    assert again.body == judge.body
    assert _break_agents() == [("judge", 0), ("verifier", 0)]
    (break_file,) = result.breaks
    assert break_file.verdict.model_dump(mode="json") == _joined(0)
    verification = break_file.verification
    assert verification is not None
    assert verification.attempts == 1
    assert all(check.passed for check in verification.checks)
    assert verification.verdict.model_dump(mode="json") == verifier
    assert [
        difference.details["field"] for difference in verification.differences
    ] == fields
    (hint,) = break_file.hints
    assert [difference.details for difference in hint.differences] == [
        {"entry": None, "item": "p0001-001", "marker": "Part"}
    ]
    assert [issue.check for issue in break_file.issues] == issue_checks
    if fields:
        issue = break_file.issues[-1]
        assert (issue.item_id, issue.page_index) == ("p0000-001", 0)
        assert issue.message == (
            "pages 1 and 2: verdicts_differ: in piece 1 (p0000-001 to p0001-001), "
            "the text join is space in the kept verdict and no_space in the "
            "verifier's"
        )
        assert issue.details == {
            "entry": None,
            "field": "text_join",
            "item": "p0000-001",
            "kept": "space",
            "verifier": "no_space",
        }
    assert result.record is not None
    assert result.record.review == break_file.issues
    report = Path("out/report.html").read_text(encoding="utf-8")
    assert f"<dt>Verifier</dt><dd>{report_line}</dd>" in report

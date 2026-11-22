"""Tests for the page extraction step: page files, the verifier, reuse and failures.

Each test makes a small PDF of its own, surveys it and extracts its pages against the
stand-in provider server, whose answers the test writes. Blank pages have no text
layer, so their text is not compared; the text pages have a running header on every
page and three lines of their own.
"""

# Standard Library
import json
import re

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal

# Third Party Library
import pymupdf
import pytest

# Package Library
import pydelity

from pydelity.errors import ExtractionError, ProviderError, PydelityWarning
from pydelity.extracting.prompts import extract_page, verify_page
from pydelity.extracting.schemas import (
    AnswerItem,
    PageAnswer,
    PageContext,
    PageFile,
    PageRepeatedLine,
)
from pydelity.surveying.schemas import FormField
from tests.fixtures.mock_providers import MockProviders, RecordedRequest

# A code item's text, with indentation and a line break to keep.
_CODE = "def total(values):\n    return sum(values)  # all of them"

# The running header at the top of every text page.
_HEADER = "Quarterly Notice Header"

# The verdict of a verifier that finds nothing wrong.
_PASSED = {"corrected": None, "passed": True, "problems": []}

# What PydanticAI puts around a retry message in the request that follows it.
_RETRY_FEEDBACK = re.compile(
    r"<pyai:retry_feedback>(.*?)</pyai:retry_feedback>", flags=re.DOTALL
)

# The lines of each text page, below its header.
_TEXT_LINES = (
    (
        "Payments are due by the end of March.",
        "Late payments add a penalty of five percent.",
        "Ask the office for a form.",
    ),
    (
        "Refunds arrive within six weeks.",
        "Keep copies of every receipt.",
        "Write to the office with questions.",
    ),
    (
        "Sign the return before mailing it.",
        "Mail it to the address shown below.",
        "Attach every page of the return.",
    ),
)

# The heading of the checks section in a page verifier's request.
_VERIFIER_CHECKS = "Checks it still fails, which a correction must pass:\n"

# The heading of the hint differences section in a page verifier's request.
_VERIFIER_HINTS = "Differences from the hints, which the page image overrides:\n"


def _answer(
    *items: AnswerItem, containers: Sequence[dict[str, object]] = ()
) -> dict[str, object]:
    """Write a page answer as the model would send it.

    Parameters
    ----------
    *items
        The items, in reading order.
    containers
        The containers.

    Returns
    -------
    dict[str, object]
        The answer, as JSON-ready data.
    """

    return {
        "column_order": None,
        "containers": list(containers),
        "items": [item.model_dump(mode="json") for item in items],
    }


def _blank_pdf(*, pages: int) -> Path:
    """Write a PDF of blank US Letter pages, with no text layer.

    Parameters
    ----------
    pages
        How many pages.

    Returns
    -------
    Path
        The PDF, ``blank.pdf`` in the current folder.
    """

    path = Path("blank.pdf")
    with pymupdf.open() as document:
        for _ in range(pages):
            document.new_page(height=792, width=612)
        document.save(path)
    return path


def _figure_page(answer_item: Callable[..., AnswerItem]) -> dict[str, object]:
    """Write the answer for a page that is one picture.

    Parameters
    ----------
    answer_item
        The fixture that builds an item.

    Returns
    -------
    dict[str, object]
        One figure item covering the page.
    """

    return _answer(
        answer_item(
            box=[0, 0, 1000, 1000],
            figure={"description": "A photograph.", "text": None},
            kind="figure",
            label="Figure",
            language=None,
            ref="f1",
            text=None,
        )
    )


def _instructions(request: RecordedRequest, *, provider: str) -> str:
    """Give the instructions a model request sent, as one text.

    Parameters
    ----------
    request
        The recorded request.
    provider
        ``anthropic`` (a ``system`` list of text blocks) or ``openai``
        (``instructions``).

    Returns
    -------
    str
        The instructions.
    """

    if provider == "anthropic":
        return json.dumps(request.body["system"], ensure_ascii=False)
    return str(request.body["instructions"])


def _page_requests(mock: MockProviders) -> list[tuple[int | None, str | None]]:
    """List the page and agent of each model request the stand-in received.

    Parameters
    ----------
    mock
        The stand-in server.

    Returns
    -------
    list[tuple[int | None, str | None]]
        Each model request's page index and agent, ``None`` and ``surveyor`` for the
        survey's.
    """

    return [
        (request.page_index, request.agent)
        for request in mock.requests
        if request.route == "model"
    ]


def _retry_messages(request: RecordedRequest) -> list[str]:
    """Give the retry messages a model request sends after earlier answers.

    Parameters
    ----------
    request
        The recorded request.

    Returns
    -------
    list[str]
        The text of each retry message, oldest first, as the request's JSON holds
        it.
    """

    return _RETRY_FEEDBACK.findall(json.dumps(request.body, ensure_ascii=False))


def _survey_answer(
    profile_labels: list[dict[str, object]], **changes: object
) -> dict[str, object]:
    """Write a survey answer whose labels are the test profile's.

    The running header of the text pages, the PDF's only repeated line, is page
    furniture.

    Parameters
    ----------
    profile_labels
        The labels.
    **changes
        Top-level keys to replace.

    Returns
    -------
    dict[str, object]
        The answer, as JSON-ready data.
    """

    answer: dict[str, object] = {
        "artifacts": [
            {
                "description": "The running header.",
                "id": "A1",
                "position": "top",
                "repeated_line_ids": ["R1"],
            }
        ],
        "continuation_notes": [],
        "labels": profile_labels,
        "languages": ["en"],
        "non_artifact_lines": [],
        "notes": [],
        "page_numbering": [],
        "regions": [],
        "rotation": [],
        "start_markers": [],
        "writing_direction": {"default": "ltr", "ranges": []},
    }
    answer.update(changes)
    return answer


def _text_answer(
    answer_item: Callable[..., AnswerItem], *, lines: Sequence[str]
) -> dict[str, object]:
    """Write a text page's answer: its header as page furniture, then its lines.

    Parameters
    ----------
    answer_item
        The fixture that builds an item.
    lines
        The lines to give as body text, one item each, ``t0``, ``t1`` and so on.

    Returns
    -------
    dict[str, object]
        The answer, with the header covering where the page prints it.
    """

    header = answer_item(
        box=[80, 20, 600, 70],
        label="Page furniture",
        ref="h",
        role="artifact",
        text=_HEADER,
    )
    body = [
        answer_item(
            box=[100, 120 + 50 * index, 900, 160 + 50 * index], ref=f"t{index}"
        ).model_copy(update={"text": line})
        for index, line in enumerate(lines)
    ]
    return _answer(header, *body)


def _text_pdf() -> Path:
    """Write a 3-page PDF of text: a running header and three lines on each page.

    Returns
    -------
    Path
        The PDF, ``text.pdf`` in the current folder; its text layer is good.
    """

    path = Path("text.pdf")
    with pymupdf.open() as document:
        for lines in _TEXT_LINES:
            page = document.new_page(height=792, width=612)
            page.insert_text((72, 40), _HEADER, fontsize=10)
            for index, line in enumerate(lines):
                page.insert_text((72, 120 + 30 * index), line, fontsize=12)
        document.save(path)
    return path


def _user_text(request: RecordedRequest, *, provider: str) -> str:
    """Give the text a model request sent with the page image.

    Parameters
    ----------
    request
        The recorded request.
    provider
        ``anthropic`` or ``openai``.

    Returns
    -------
    str
        The text part of the request's first user message.
    """

    messages = request.body["messages" if provider == "anthropic" else "input"]
    assert isinstance(messages, list)
    return str(messages[0]["content"][0]["text"])


def _verifier_sections(mock: MockProviders) -> tuple[list[str], list[str]]:
    """Give the checks and hint differences of the first page verifier request.

    Parameters
    ----------
    mock
        The Anthropic stand-in server.

    Returns
    -------
    tuple[list[str], list[str]]
        The lines under the checks heading and under the hint differences heading.
    """

    request = next(r for r in mock.requests if r.agent == "verifier")
    checks, hints = (
        _user_text(request, provider="anthropic")
        .split(_VERIFIER_CHECKS)[1]
        .split(f"\n\n{_VERIFIER_HINTS}")
    )
    return checks.splitlines(), hints.splitlines()


def test_a_failed_page_stops_the_run_and_the_next_run_extracts_only_what_is_missing(
    answer_item: Callable[..., AnswerItem],
    mock_providers: Callable[..., MockProviders],
    profile_labels: list[dict[str, object]],
) -> None:
    """A page whose request fails stops the run; written page files stay valid.

    With one page at a time, the first page is written, the second fails with the
    provider's error, and the third never starts. The run is recorded as failed
    and its report is written. The next run reuses the survey and the first page,
    and asks only for the other two.
    """

    pdf = _blank_pdf(pages=3)
    figure = _figure_page(answer_item)
    page_answers = {index: {"extractor": figure} for index in range(3)}
    survey = _survey_answer(profile_labels, artifacts=[])
    mock_providers(
        answers=[survey],
        page_answers={0: page_answers[0], 2: page_answers[2]},
    )
    advanced = {"extraction": {"concurrent_pages": 1}}

    with pytest.raises(ProviderError, match="No extractor answer for page index 1"):
        pydelity.run(pdf, advanced=advanced, output_dir="out", pause=False)

    failed = pydelity.load("out")
    assert failed.record is not None
    assert failed.record.status == "failed"
    assert failed.record.error is not None
    assert "page 2 (index 1)" in failed.record.error
    assert [step.status for step in failed.record.steps] == ["completed", "failed"]
    assert [page.page_index for page in failed.pages] == [0]
    assert Path("out/report.html").is_file()

    retry = mock_providers(answers=[survey], page_answers=page_answers)
    result = pydelity.run(pdf, advanced=advanced, output_dir="out")

    assert result.record is not None
    assert result.record.status == "completed"
    assert sorted(_page_requests(retry)) == [(1, "extractor"), (2, "extractor")]
    assert [page.page_index for page in result.pages] == [0, 1, 2]


def test_a_model_that_never_answers_in_the_format_fails_its_page(
    mock_providers: Callable[..., MockProviders],
    profile_labels: list[dict[str, object]],
) -> None:
    """An extraction model that never gives an answer raises `ExtractionError`.

    The error names the page and the model's role, after every check retry.
    """

    pdf = _blank_pdf(pages=1)
    mock = mock_providers(
        answers=[_survey_answer(profile_labels, artifacts=[])],
        page_answers={0: {"extractor": "I cannot read this page."}},
    )

    with pytest.raises(ExtractionError) as raised:
        pydelity.extract(pdf, output_dir="out")

    assert str(raised.value).startswith(
        "Page 1 (index 0), extractor: the model gave no usable answer"
    )
    assert _page_requests(mock)[1:] == [(0, "extractor")] * 3
    assert not Path("out/pages/0000.json").exists()


def test_a_page_file_naming_a_missing_crop_is_extracted_again(
    answer_item: Callable[..., AnswerItem],
    mock_providers: Callable[..., MockProviders],
    profile_labels: list[dict[str, object]],
) -> None:
    """A page file whose figure image is gone is damaged; the page is extracted again.

    The warning names the missing image, and the page's crop is written again.
    Temporary files that an interrupted write left beside the page files and the
    crops are removed.
    """

    pdf = _blank_pdf(pages=1)
    mock = mock_providers(
        answers=[_survey_answer(profile_labels, artifacts=[])],
        page_answers={0: {"extractor": _figure_page(answer_item)}},
    )
    pydelity.extract(pdf, output_dir="out")
    crop = Path("out/figures/p0000-001.png")
    crop.unlink()
    leftovers = [
        Path("out/pages/0000.json.tmp-0123456789abcdef"),
        Path("out/figures/p0000-001.png.tmp-0123456789abcdef"),
    ]
    for leftover in leftovers:
        leftover.write_bytes(b"partial")

    with pytest.warns(PydelityWarning, match=r"figures/p0000-001\.png, which is miss"):
        pydelity.extract(pdf, output_dir="out")

    assert _page_requests(mock)[2:] == [(0, "extractor")]
    assert crop.read_bytes().startswith(b"\x89PNG")
    assert not any(leftover.exists() for leftover in leftovers)


def test_a_page_no_verifier_reviewed_keeps_its_extraction_and_lists_each_difference(
    answer_item: Callable[..., AnswerItem],
    log_messages: list[tuple[str, str]],
    mock_providers: Callable[..., MockProviders],
    profile_labels: list[dict[str, object]],
) -> None:
    """With the verifier off, a page keeps its extraction and lists each difference.

    The extraction leaves out the page's last line and adds a line the page does not
    have, so it differs from both text hints but passes every check. It is kept at
    once, with no retry and no verifier request. Both differences are in the page
    file's hints and are review issues, the page file holds no verification, the
    ledger has one extractor line, and the page's log line says no verifier ran.
    """

    lines = _TEXT_LINES[0]
    added = "Bring a packed lunch."
    pdf = _text_pdf()
    mock = mock_providers(
        answers=[_survey_answer(profile_labels)],
        page_answers={
            0: {"extractor": _text_answer(answer_item, lines=[*lines[:2], added])}
        },
    )

    (page,) = pydelity.extract(pdf, output_dir="out", pages="1")

    assert _page_requests(mock)[1:] == [(0, "extractor")]
    assert [item.text for item in page.items] == [_HEADER, *lines[:2], added]
    assert all(check.passed and check.attempts == 1 for check in page.checks)
    assert [(hint.name, len(hint.differences)) for hint in page.hints] == [
        ("reading_order", 0),
        ("artifacts", 0),
        ("form_fields", 0),
        ("text_dropped", 1),
        ("text_added", 1),
    ]
    assert [(issue.check, issue.message) for issue in page.issues] == [
        (hint.name, difference.message)
        for hint in page.hints
        for difference in hint.differences
    ]
    issues = {issue.check: issue.message for issue in page.issues}
    assert added in issues["text_added"]
    assert lines[2] in issues["text_dropped"]
    assert page.verification is None
    stored = json.loads(Path("out/pages/0000.json").read_text(encoding="utf-8"))
    assert stored["verification"] is None
    ledger = pydelity.load("out").ledger
    assert [line.agent for line in ledger if line.step == "extraction"] == ["extractor"]
    (logged,) = [
        text
        for _, text in log_messages
        if "review issues" in text and "index 0" in text
    ]
    assert ", 2 review issues, no verifier; " in logged


def test_an_answer_becomes_a_page_file_with_ids_points_and_links(
    answer_item: Callable[..., AnswerItem],
    mock_providers: Callable[..., MockProviders],
    profile_labels: list[dict[str, object]],
) -> None:
    """Items get IDs by reading order, boxes in points, and the IDs they refer to.

    List entries get their list's ID and their position; a caption names its
    figure's ID, an item in a box names the container's ID, and a language tag is
    stored in standard form. Code keeps its whitespace and line breaks, a formula
    its LaTeX, and a field on a printed form its value.
    """

    items = [
        answer_item(
            box=[100, 50, 900, 100],
            label="Heading",
            language="en-us",
            ref="h1",
            role="heading",
        ),
        answer_item(
            box=[100, 120, 900, 200],
            entries=[
                {"level": 0, "marker": "1.", "text": "First point"},
                {"level": 1, "marker": "a)", "text": "Second point"},
            ],
            kind="list",
            ref="l1",
            text=None,
        ),
        answer_item(
            box=[150, 250, 850, 600],
            container="c1",
            figure={"description": "A bar chart.", "text": None},
            kind="figure",
            label="Figure",
            language=None,
            ref="f1",
            text=None,
        ),
        answer_item(
            box=[150, 610, 850, 650],
            caption_of="f1",
            container="c1",
            label="Caption",
            ref="cap",
            role="caption",
            text="Sales by year.",
        ),
        answer_item(
            box=[100, 700, 900, 900],
            kind="table",
            ref="tb",
            table={
                "header_rows": 1,
                "rows": [
                    [
                        {"col_span": 1, "row_span": 2, "text": "Year"},
                        {"col_span": 1, "row_span": 1, "text": "Sales"},
                    ],
                    [{"col_span": 1, "row_span": 1, "text": "10"}],
                ],
            },
            text=None,
        ),
        answer_item(box=[100, 910, 500, 940], kind="code", ref="code", text=_CODE),
        answer_item(
            box=[520, 910, 700, 940],
            kind="formula",
            latex=r"a^2 + b^2 = c^2",
            ref="eq",
            text="a2 + b2 = c2",
        ),
        answer_item(
            box=[720, 910, 900, 990],
            field={
                "checked": None,
                "field_type": "text",
                "fillable_name": None,
                "options": [],
                "prompt": "Name",
                "value": "Ana Ruiz",
            },
            kind="field",
            label="Form item",
            ref="name",
            text=None,
        ),
    ]
    container: dict[str, object] = {
        "box": [120, 230, 880, 670],
        "container": None,
        "label": "Body",
        "ref": "c1",
    }
    pdf = _blank_pdf(pages=1)
    mock_providers(
        answers=[_survey_answer(profile_labels, artifacts=[])],
        page_answers={0: {"extractor": _answer(*items, containers=[container])}},
    )

    (page,) = pydelity.extract(pdf, output_dir="out")

    assert [item.id for item in page.items] == [f"p0000-00{n}" for n in range(1, 9)]
    heading, listed, figure, caption, table, code, formula, field = page.items
    assert heading.bbox == [61.2, 39.6, 550.8, 79.2]
    assert heading.language == "en-US"
    assert listed.entries is not None
    assert [(entry.id, entry.text) for entry in listed.entries] == [
        ("p0000-002.1", "First point"),
        ("p0000-002.2", "Second point"),
    ]
    assert [(c.id, c.bbox) for c in page.containers] == [
        ("p0000-c01", [73.44, 182.16, 538.56, 530.64])
    ]
    assert (figure.container, caption.container) == ("p0000-c01", "p0000-c01")
    assert caption.caption_of == figure.id
    assert table.table is not None
    assert table.table.rows[0][0].row_span == 2
    assert code.text == _CODE
    assert (formula.latex, formula.text) == (r"a^2 + b^2 = c^2", "a2 + b2 = c2")
    assert field.field is not None
    assert (field.field.value, field.field.fillable_name) == ("Ana Ruiz", None)
    assert page.text_comparison == "no_text_layer"
    assert page.issues == []
    assert all(check.passed for check in page.checks)


@pytest.mark.parametrize("verify", [False, True], ids=["no_verifier", "passed"])
def test_an_answer_failing_a_check_is_sent_back_then_kept_with_its_failure_listed(
    answer_item: Callable[..., AnswerItem],
    mock_providers: Callable[..., MockProviders],
    profile_labels: list[dict[str, object]],
    verify: bool,
) -> None:
    """Only a check failure sends an answer back, and the last answer is kept.

    The extraction gives an item a label not in the profile and leaves out the
    page's last line, on every attempt. Each retry message names the label failure
    and nothing of the hint difference or the page's stored text. After the check
    retries the extraction is kept and the run completes. The label failure is a
    review issue with or without the verifier. The left-out line is one only when no
    verifier passed the page, and the page file's hints keep it either way.
    """

    lines = _TEXT_LINES[0]
    extraction = _text_answer(answer_item, lines=lines[:2])
    items = extraction["items"]
    assert isinstance(items, list)
    items[2]["label"] = "Sidebar"
    pdf = _text_pdf()
    mock = mock_providers(
        answers=[_survey_answer(profile_labels)],
        page_answers={0: {"extractor": extraction, "verifier": _PASSED}},
    )

    result = pydelity.run(
        pdf,
        advanced={"extraction": {"verify": verify}},
        output_dir="out",
        pages="1",
        pause=False,
    )

    agents = [agent for _, agent in _page_requests(mock)[1:]]
    assert agents == ["extractor"] * 3 + ["verifier"] * verify
    extractor_requests = [r for r in mock.requests if r.agent == "extractor"]
    retries = _retry_messages(extractor_requests[-1])
    assert len(retries) == 2
    assert all(
        "labels: item 't1' has the label 'Sidebar'" in message
        and "text_dropped" not in message
        and all(line not in message for line in [_HEADER, *lines])
        for message in retries
    )
    assert result.record is not None
    assert result.record.status == "completed"
    (page,) = result.pages
    assert page == PageFile.model_validate_json(
        Path("out/pages/0000.json").read_text(encoding="utf-8")
    )
    assert [item.text for item in page.items] == [_HEADER, *lines[:2]]
    assert [
        (check.name, check.passed, check.attempts)
        for check in page.checks
        if not check.passed
    ] == [("labels", False, 3)]
    assert [hint.name for hint in page.hints if hint.differences] == ["text_dropped"]
    listed = [issue.check for issue in page.issues]
    assert listed == (["labels"] if verify else ["labels", "text_dropped"])
    assert page.issues[0].item_id == "p0000-003"
    assert result.record.review == page.issues
    if verify:
        checks, hints = _verifier_sections(mock)
        assert [line.split(":")[0] for line in checks] == ["- labels"]
        assert [line.split(":")[0] for line in hints] == ["- text_dropped"]


def test_an_inconsistent_survey_still_gives_every_page_a_context(
    answer_item: Callable[..., AnswerItem],
    mock_providers: Callable[..., MockProviders],
    profile_labels: list[dict[str, object]],
) -> None:
    """Page extraction runs on a survey whose ranges and artifact lists disagree.

    Each page takes the first range inside the PDF that covers it, else the
    profile's default; a range past the PDF is ignored, and overlapping ranges
    give the earlier one. A repeated line listed as page furniture is furniture
    even when it is also listed twice, or as content, and an unknown line ID is
    ignored.
    """

    pdf = _text_pdf()
    survey = _survey_answer(
        profile_labels,
        artifacts=[
            {
                "description": "The running header.",
                "id": "A1",
                "position": "top",
                "repeated_line_ids": ["R1", "R1", "R9"],
            }
        ],
        non_artifact_lines=[{"reason": "It is a title.", "repeated_line_id": "R1"}],
        rotation=[
            {"degrees": 90, "first_page_index": 2, "last_page_index": 2},
            {"degrees": 180, "first_page_index": 2, "last_page_index": 2},
        ],
        writing_direction={
            "default": "ltr",
            "ranges": [
                {"direction": "rtl", "first_page_index": 0, "last_page_index": 1},
                {"direction": "ttb", "first_page_index": 1, "last_page_index": 5},
            ],
        },
    )
    mock_providers(
        answers=[survey],
        page_answers={
            index: {"extractor": _figure_page(answer_item)} for index in range(3)
        },
    )

    pages = pydelity.extract(
        pdf,
        advanced={
            "extraction": {"check_retries": 0},
            "survey": {"check_retries": 0},
        },
        output_dir="out",
    )

    assert [(page.writing_direction, page.rotation) for page in pages] == [
        ("rtl", 0),
        ("rtl", 0),
        ("ltr", 90),
    ]
    for page in pages:
        assert [(line.id, line.use) for line in page.inputs.context.repeated_lines] == [
            ("R1", "artifact")
        ]


@pytest.mark.parametrize("provider", ["anthropic", "openai"])
def test_each_page_request_carries_one_upright_image_and_only_its_own_instructions(
    answer_item: Callable[..., AnswerItem],
    mock_providers: Callable[..., MockProviders],
    profile_labels: list[dict[str, object]],
    provider: Literal["anthropic", "openai"],
) -> None:
    """Each page request sends one page image, no PDF and no stored text lines.

    With the verifier on, both of the page's requests give the writing direction as
    what the survey found, and the running header, with the survey's finding that it
    is page furniture, under a heading that calls it a hint the image overrides.
    Page extraction's instructions go to the extraction model and the verifier only,
    and the survey's to the survey only.
    Anthropic requests ask for the answer as JSON in the instructions; OpenAI
    requests ask for a JSON-schema answer and send the image at its original
    detail.
    """

    model = {"anthropic": "anthropic:claude-opus-5-5", "openai": "openai:gpt-6.2-astra"}
    pdf = _text_pdf()
    mock = mock_providers(
        answers=[_survey_answer(profile_labels)],
        page_answers={
            0: {
                "extractor": _text_answer(answer_item, lines=_TEXT_LINES[0]),
                "verifier": _PASSED,
            }
        },
    )

    (page,) = pydelity.extract(
        pdf,
        advanced={
            "extraction": {"instructions": "Stamps are content.", "verify": True},
            "survey": {"instructions": "Margin notes are content."},
        },
        model=model[provider],
        output_dir="out",
        pages="1",
    )

    survey, extractor, verifier = [
        request for request in mock.requests if request.route == "model"
    ]
    assert (extractor.agent, verifier.agent) == ("extractor", "verifier")
    assert page.text_comparison == "compared"
    assert all(check.passed for check in page.checks)
    for request in (extractor, verifier):
        sent = json.dumps(request.body, ensure_ascii=False)
        image_type = "image" if provider == "anthropic" else "input_image"
        assert sent.count(f'"type": "{image_type}"') == 1
        assert "application/pdf" not in sent
        assert request.file_ids == []
        assert "Page index 0 (page 1 of 3)" in sent
        text = _user_text(request, provider=provider)
        assert "The survey found the page written left to right." in text
        hints = text.split(
            "Hints from the PDF's stored text and the survey, which the image "
            "overrides."
        )[1]
        assert f'- R1: "{_HEADER}", page furniture' in hints
        assert "Stamps are content." in _instructions(request, provider=provider)
        assert "Margin notes are content." not in sent
    for line in _TEXT_LINES[0]:
        assert line not in json.dumps(extractor.body, ensure_ascii=False)
        assert (
            line
            not in _user_text(verifier, provider=provider).split(
                "The extraction to review:"
            )[0]
        )
    survey_instructions = _instructions(survey, provider=provider)
    assert "Margin notes are content." in survey_instructions
    assert "Stamps are content." not in json.dumps(survey.body)

    for request, answer_name in (
        (survey, "SurveyAnswer"),
        (extractor, "PageAnswer"),
        (verifier, "VerifierVerdict"),
    ):
        if provider == "anthropic":
            output_config = request.body.get("output_config", {})
            assert isinstance(output_config, dict)
            assert "format" not in output_config
            assert "Always respond with a JSON object" in _instructions(
                request, provider=provider
            )
        else:
            text = request.body["text"]
            assert isinstance(text, dict)
            assert (text["format"]["type"], text["format"]["name"]) == (
                "json_schema",
                answer_name,
            )
    if provider == "openai":
        assert '"detail": "original"' in json.dumps(extractor.body)


def test_no_more_pages_run_at_once_than_the_limit(
    answer_item: Callable[..., AnswerItem],
    mock_providers: Callable[..., MockProviders],
    profile_labels: list[dict[str, object]],
) -> None:
    """``advanced.extraction.concurrent_pages`` bounds the page requests in flight.

    With five pages and a limit of two, two pages run at once, and never more.
    """

    pdf = _blank_pdf(pages=5)
    mock = mock_providers(
        answers=[_survey_answer(profile_labels, artifacts=[])],
        delay_seconds=0.2,
        page_answers={
            index: {"extractor": _figure_page(answer_item)} for index in range(5)
        },
    )

    pages = pydelity.extract(
        pdf, advanced={"extraction": {"concurrent_pages": 2}}, output_dir="out"
    )

    assert [page.page_index for page in pages] == [0, 1, 2, 3, 4]
    assert mock.max_in_flight == 2
    assert all(page.issues == [] for page in pages)


def test_page_files_rerun_only_when_their_inputs_change(
    answer_item: Callable[..., AnswerItem],
    mock_providers: Callable[..., MockProviders],
    profile_labels: list[dict[str, object]],
) -> None:
    """A page is extracted again only when what its requests are made from changes.

    Blank instructions count as none, so no instructions are sent. New page
    extraction instructions rerun the selected pages but not the survey;
    selecting more pages extracts only the new ones; ``overwrite`` redoes the
    survey and every selected page.
    """

    pdf = _blank_pdf(pages=3)
    mock = mock_providers(
        answers=[_survey_answer(profile_labels, artifacts=[])],
        page_answers={
            index: {"extractor": _figure_page(answer_item)} for index in range(3)
        },
    )
    instructions: dict[str, object] = {
        "extraction": {"instructions": "Stamps are content."}
    }

    def requests_for(
        *, advanced: dict[str, object], overwrite: bool = False, pages: str
    ) -> list[tuple[int | None, str | None]]:
        """Extract with these settings and list the model requests it sent."""

        before = len(_page_requests(mock))
        pydelity.extract(
            pdf, advanced=advanced, output_dir="out", overwrite=overwrite, pages=pages
        )
        return sorted(_page_requests(mock)[before:], key=str)

    blank: dict[str, object] = {"extraction": {"instructions": "  "}}
    first = requests_for(advanced=blank, pages="1-2")
    extractor = next(r for r in mock.requests if r.agent == "extractor")
    assert "The user's instructions for this PDF follow" not in json.dumps(
        extractor.body
    )
    instructions_changed = requests_for(advanced=instructions, pages="1-2")
    unchanged = requests_for(advanced=instructions, pages="1-2")
    widened = requests_for(advanced=instructions, pages="1-3")
    overwritten = requests_for(advanced=instructions, overwrite=True, pages="1-3")

    both_pages = [(0, "extractor"), (1, "extractor")]
    assert first == [*both_pages, (None, "surveyor")]
    assert instructions_changed == both_pages
    assert unchanged == []
    assert widened == [(2, "extractor")]
    assert overwritten == [*both_pages, (2, "extractor"), (None, "surveyor")]


def test_page_prompts_give_what_the_pdf_and_the_survey_say_as_hints(
    page_context: Callable[..., PageContext],
) -> None:
    """Both page prompts give the survey's findings and the PDF's data as hints.

    The writing direction is what the survey found. Each repeated line comes with
    its stored text and the survey's finding, and each fillable field with its
    stored value, under headings that call them hints the image overrides. Both
    prompts' rules say the image decides, and no sentence in them tells the model to
    put a repeated line in an item with role artifact. The extraction model is told
    that code checks form and consistency, and the verifier that a correction need
    not agree with the hints.
    """

    lines = [
        PageRepeatedLine(id="R1", normalized="#", text="12", use="artifact"),
        PageRepeatedLine(
            id="R2", normalized="chapter notes", text="Chapter notes", use="content"
        ),
        PageRepeatedLine(
            id="R3", normalized="draft copy", text="Draft copy", use="unclassified"
        ),
    ]
    field = FormField.model_validate(
        {
            "bbox": (100.0, 100.0, 300.0, 120.0),
            "checked": None,
            "name": "city",
            "options": [],
            "page_index": 0,
            "type": "text",
            "value": "Springfield",
        }
    )
    context = page_context(
        form_fields=[field], repeated_lines=lines, writing_direction="rtl"
    )
    empty = PageAnswer(column_order=None, containers=[], items=[])

    extractor = extract_page(context)
    verifier = verify_page(context, answer=empty, differences={}, failures={})

    page, repeated, fields = extractor.user_message.split("\n\n")
    assert page == (
        "Page index 0 (page 1 of 1)\nThe survey found the page written right to "
        "left. The image shows the page as it is displayed."
    )
    assert repeated.splitlines() == [
        "Hints from the PDF's stored text and the survey, which the image overrides. "
        "Repeated lines on this page, with the text the PDF stores and what the "
        "survey found each one to be:",
        '- R1: "12", page furniture',
        '- R2: "Chapter notes", content',
        '- R3: "Draft copy", not decided',
    ]
    assert fields.splitlines()[0] == (
        "Hints from the PDF's stored form data, which the image overrides. Fillable "
        "form fields on this page, with the values the PDF stores:"
    )
    assert fields.splitlines()[1].startswith('- "city", text, value "Springfield", ')
    assert verifier.user_message.startswith(extractor.user_message + "\n\n")
    for prompts in (extractor, verifier):
        assert "Where a hint and the image disagree, give what the image shows." in (
            prompts.system_message
        )
        sentences = re.split(r"(?<=\.)\s+", prompts.system_message)
        assert [
            sentence
            for sentence in sentences
            if "repeated line" in sentence and "artifact" in sentence
        ] == []
    assert extractor.system_message.endswith(
        "Your answer is checked by code for form and consistency, and you will be "
        "told what to fix if a check fails."
    )
    assert "a correction need not agree with the hints" in verifier.system_message


def test_the_same_answer_gives_the_same_items_and_containers_again(
    answer_item: Callable[..., AnswerItem],
    mock_providers: Callable[..., MockProviders],
    profile_labels: list[dict[str, object]],
) -> None:
    """Extracting a page again from the same answer writes the same items exactly.

    The figure's crop is cut from the page each time and named after its item.
    """

    pdf = _blank_pdf(pages=1)
    answer = _answer(
        answer_item(box=[100, 50, 900, 100], ref="t1"),
        answer_item(
            box=[150, 250, 850, 600],
            container="c1",
            figure={"description": "A seal.", "text": "OFFICIAL"},
            kind="figure",
            label="Figure",
            ref="f1",
            text=None,
        ),
        containers=[
            {
                "box": [120, 230, 880, 670],
                "container": None,
                "label": "Body",
                "ref": "c1",
            }
        ],
    )
    mock_providers(
        answers=[_survey_answer(profile_labels, artifacts=[])],
        page_answers={0: {"extractor": answer}},
    )

    def written() -> tuple[str, bytes]:
        """Extract the page anew and read back its items, containers and crop."""

        pydelity.extract(pdf, output_dir="out", overwrite=True)
        stored = json.loads(Path("out/pages/0000.json").read_text(encoding="utf-8"))
        parts = json.dumps([stored["items"], stored["containers"]], sort_keys=True)
        return parts, Path("out/figures/p0000-002.png").read_bytes()

    first, second = written(), written()

    assert first == second
    assert sorted(path.name for path in Path("out/figures").iterdir()) == [
        "p0000-002.png"
    ]
    crop = pymupdf.Pixmap(first[1])
    assert crop.width == pytest.approx(700 / 1000 * 612 * 200 / 72, abs=2)


@pytest.mark.parametrize(
    "outcome", ["passed", "correction_kept", "correction_rejected"]
)
def test_the_verifier_s_verdict_decides_the_kept_answer_and_its_issues(
    answer_item: Callable[..., AnswerItem],
    mock_providers: Callable[..., MockProviders],
    outcome: str,
    profile_labels: list[dict[str, object]],
) -> None:
    """A verdict keeps the extraction or its correction, and decides what is listed.

    With the verifier on, the extraction leaves out the page's last line. That is a
    hint difference, so the extraction is kept at once, and the verifier's request
    gives no check failure and quotes the left-out line under the hints heading. A
    passing verdict keeps the extraction and lists no hint difference. A correction
    that adds a line and gives the running header as body text differs from two
    hints but passes every check, so it is kept on the verifier's first answer, with
    nothing listed. A correction with a label not in the profile is sent back with
    the label failure alone and then rejected: the extraction is kept, and its hint
    difference and the verifier's problem, naming the item's ID, are listed. The
    page file's hints keep every difference on the kept answer either way.
    """

    lines = _TEXT_LINES[0]
    added = "Bring a packed lunch."
    extraction = _text_answer(answer_item, lines=lines[:2])
    corrected = _text_answer(answer_item, lines=[*lines, added])
    corrected_items = corrected["items"]
    assert isinstance(corrected_items, list)
    corrected_items[0].update({"label": "Body", "role": "body"})
    problem = {
        "category": "missing",
        "description": "A line is left out.",
        "item_ref": None,
    }
    if outcome == "correction_rejected":
        corrected = _text_answer(answer_item, lines=lines)
        corrected_items = corrected["items"]
        assert isinstance(corrected_items, list)
        corrected_items[2]["label"] = "Sidebar"
        problem = {
            "category": "label",
            "description": "It is a note.",
            "item_ref": "t1",
        }
    verdict = (
        _PASSED
        if outcome == "passed"
        else {"corrected": corrected, "passed": False, "problems": [problem]}
    )
    pdf = _text_pdf()
    mock = mock_providers(
        answers=[_survey_answer(profile_labels)],
        page_answers={0: {"extractor": extraction, "verifier": verdict}},
    )

    (page,) = pydelity.extract(
        pdf, advanced={"extraction": {"verify": True}}, output_dir="out", pages="1"
    )

    agents = [agent for _, agent in _page_requests(mock)[1:]]
    assert agents == ["extractor"] + ["verifier"] * (
        3 if outcome == "correction_rejected" else 1
    )
    checks, differences = _verifier_sections(mock)
    assert (checks, [line.split(":")[0] for line in differences]) == (
        ["none"],
        ["- text_dropped"],
    )
    assert lines[2] in differences[0]
    assert all(check.passed for check in page.checks)
    hints = {hint.name: hint.differences for hint in page.hints if hint.differences}
    verification = page.verification
    assert verification is not None
    if outcome == "passed":
        assert page.items[-1].text == lines[1]
        assert list(hints) == ["text_dropped"]
        assert verification.correction_applied is False
        assert page.issues == []
    elif outcome == "correction_kept":
        assert [(item.text, item.role) for item in page.items] == [
            (_HEADER, "body"),
            *((line, "body") for line in [*lines, added]),
        ]
        assert list(hints) == ["artifacts", "text_added"]
        assert added in hints["text_added"][0].message
        assert verification.correction_applied is True
        assert verification.correction_failures == []
        assert verification.verdict.problems[0].description == "A line is left out."
        assert page.issues == []
    else:
        assert page.items[-1].text == lines[1]
        assert list(hints) == ["text_dropped"]
        assert verification.correction_applied is False
        assert [result.name for result in verification.correction_failures] == [
            "labels"
        ]
        assert [(issue.check, issue.item_id) for issue in page.issues] == [
            ("text_dropped", None),
            ("verifier", "p0000-003"),
        ]
        assert lines[2] in page.issues[0].message
        last = [request for request in mock.requests if request.agent == "verifier"]
        assert [
            (
                "labels: item 't1' has the label 'Sidebar'" in message,
                "text_dropped" in message,
                lines[2] in message,
            )
            for message in _retry_messages(last[-1])
        ] == [(True, False, False)] * 2


def test_turning_the_verifier_on_extracts_again_only_pages_it_has_not_reviewed(
    answer_item: Callable[..., AnswerItem],
    log_messages: list[tuple[str, str]],
    mock_providers: Callable[..., MockProviders],
    profile_labels: list[dict[str, object]],
) -> None:
    """Page files made without the verifier are made again once it is turned on.

    The survey is reused, and a log line says why each page is extracted again.
    Turning the verifier off keeps the reviewed page files, and turning it on again
    sends nothing. The page files' fingerprints stay the same throughout.
    """

    pdf = _blank_pdf(pages=2)
    mock = mock_providers(
        answers=[_survey_answer(profile_labels, artifacts=[])],
        page_answers={
            index: {"extractor": _figure_page(answer_item), "verifier": _PASSED}
            for index in range(2)
        },
    )
    verified: dict[str, object] = {"extraction": {"verify": True}}

    def extract(
        advanced: dict[str, object],
    ) -> tuple[list[PageFile], list[tuple[int | None, str | None]]]:
        """Extract with these settings; return the pages and the model requests."""

        before = len(_page_requests(mock))
        pages = pydelity.extract(pdf, advanced=advanced, output_dir="out")
        return pages, sorted(_page_requests(mock)[before:], key=str)

    unreviewed, first = extract({})
    reviewed, turned_on = extract(verified)
    kept, turned_off = extract({})
    _, turned_on_again = extract(verified)

    assert first == [(0, "extractor"), (1, "extractor"), (None, "surveyor")]
    assert turned_on == [
        (0, "extractor"),
        (0, "verifier"),
        (1, "extractor"),
        (1, "verifier"),
    ]
    assert (turned_off, turned_on_again) == ([], [])
    assert [page.verification for page in unreviewed] == [None, None]
    assert all(page.verification is not None for page in reviewed)
    assert kept == reviewed
    assert [page.fingerprint for page in reviewed] == [
        page.fingerprint for page in unreviewed
    ]
    assert [text for _, text in log_messages if "no verifier reviewed" in text] == [
        f"Page {index + 1} (index {index}): no verifier reviewed its page file, so "
        "the page is extracted again with the verifier"
        for index in range(2)
    ]

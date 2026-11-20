"""Tests for the page extraction step: page files, the verifier, reuse and failures.

Each test makes a small PDF of its own, surveys it and extracts its pages against the
stand-in provider server, whose answers the test writes. Blank pages have no text
layer, so their text is not compared; the text pages have a running header on every
page and three lines of their own.
"""

# Standard Library
import json

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal

# Third Party Library
import pymupdf
import pytest

# Package Library
import pydelity

from pydelity.errors import ExtractionError, ProviderError, PydelityWarning
from pydelity.extracting.schemas import AnswerItem
from tests.fixtures.mock_providers import MockProviders, RecordedRequest

# A code item's text, with indentation and a line break to keep.
_CODE = "def total(values):\n    return sum(values)  # all of them"

# The running header at the top of every text page.
_HEADER = "Quarterly Notice Header"

# The verdict of a verifier that finds nothing wrong.
_PASSED = {"corrected": None, "passed": True, "problems": []}

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

# Words the message holds that sends an answer back for a text difference.
_TEXT_NOTE = "keep what the image shows"


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
        Each model request's page index and agent, both ``None`` for the survey's.
    """

    return [
        (request.page_index, request.agent)
        for request in mock.requests
        if request.route == "model"
    ]


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
    page_answers = {
        index: {"extractor": figure, "verifier": _PASSED} for index in range(3)
    }
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
    assert sorted(_page_requests(retry)) == [
        (1, "extractor"),
        (1, "verifier"),
        (2, "extractor"),
        (2, "verifier"),
    ]
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
        page_answers={0: {"extractor": _figure_page(answer_item), "verifier": _PASSED}},
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

    assert _page_requests(mock)[3:] == [(0, "extractor"), (0, "verifier")]
    assert crop.read_bytes().startswith(b"\x89PNG")
    assert not any(leftover.exists() for leftover in leftovers)


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
        page_answers={
            0: {
                "extractor": _answer(*items, containers=[container]),
                "verifier": _PASSED,
            }
        },
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
            index: {"extractor": _figure_page(answer_item), "verifier": _PASSED}
            for index in range(3)
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

    The page's running header is named as page furniture. Page extraction's
    instructions go to the extraction model and the verifier only, and the
    survey's to the survey only. Anthropic requests ask for the answer as JSON in
    the instructions; OpenAI requests ask for a JSON-schema answer and send the
    image at its original detail.
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
            "extraction": {"instructions": "Stamps are content."},
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
        assert "The page is written left to right." in sent
        assert _HEADER in sent
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
            index: {"extractor": _figure_page(answer_item), "verifier": _PASSED}
            for index in range(5)
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
            index: {"extractor": _figure_page(answer_item), "verifier": _PASSED}
            for index in range(3)
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

    both_pages = [(0, "extractor"), (0, "verifier"), (1, "extractor"), (1, "verifier")]
    assert first == [*both_pages, (None, None)]
    assert instructions_changed == both_pages
    assert unchanged == []
    assert widened == [(2, "extractor"), (2, "verifier")]
    assert overwritten == [*both_pages, (2, "extractor"), (2, "verifier"), (None, None)]


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
        page_answers={0: {"extractor": answer, "verifier": _PASSED}},
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

    The extraction leaves out the page's last line, so it fails the dropped-text
    check on every attempt, each retry saying the model may keep what the image
    shows. A passing verdict keeps it and lists no text difference. A correction
    that fails only a text check, here by adding a line, is sent back to the
    verifier with the same note and then kept, with nothing listed. A correction
    with a label not in the profile is rejected: the extraction is kept, and its
    text difference and the verifier's problem, naming the item's ID, are listed.
    The check results keep every failure either way.
    """

    lines = _TEXT_LINES[0]
    extraction = _text_answer(answer_item, lines=lines[:2])
    corrected = _text_answer(answer_item, lines=[*lines, "Bring a packed lunch."])
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

    (page,) = pydelity.extract(pdf, output_dir="out", pages="1")

    agents = [agent for _, agent in _page_requests(mock)[1:]]
    verifier_requests = 1 if outcome == "passed" else 3
    assert agents == ["extractor"] * 3 + ["verifier"] * verifier_requests
    extractor_retries = [r for r in mock.requests if r.agent == "extractor"][1:]
    assert all(_TEXT_NOTE in json.dumps(r.body) for r in extractor_retries)
    failed = {check.name for check in page.checks if not check.passed}
    verification = page.verification
    if outcome == "passed":
        assert (page.items[-1].text, failed) == (lines[1], {"text_dropped"})
        assert verification.correction_applied is False
        assert page.issues == []
    elif outcome == "correction_kept":
        assert [item.text for item in page.items] == [
            _HEADER,
            *lines,
            "Bring a packed lunch.",
        ]
        assert failed == {"text_added"}
        assert verification.correction_applied is True
        assert verification.correction_failures == []
        assert verification.verdict.problems[0].description == "A line is left out."
        assert page.issues == []
        retries = [r for r in mock.requests if r.agent == "verifier"][1:]
        assert all(_TEXT_NOTE in json.dumps(r.body) for r in retries)
    else:
        assert page.items[-1].text == lines[1]
        assert failed == {"text_dropped"}
        assert verification.correction_applied is False
        assert [result.name for result in verification.correction_failures] == [
            "labels"
        ]
        assert [(issue.check, issue.item_id) for issue in page.issues] == [
            ("text_dropped", None),
            ("verifier", "p0000-003"),
        ]
        assert lines[2] in page.issues[0].message

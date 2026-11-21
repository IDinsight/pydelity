"""Tests for runs over time: reuse, reruns, damaged outputs, failures and safety.

Each test runs pydelity more than once on one output folder, against the stand-in
provider server, and checks what the later run reuses or redoes.
"""

# Standard Library
from collections.abc import Callable
from pathlib import Path

# Third Party Library
import pytest

# Package Library
import pydelity

from pydelity.errors import PydelityWarning, SurveyError
from tests.fixtures.mock_providers import MockProviders

# The 2-page scanned test PDF, with no text layer.
_SCAN = "irs_form_1040a_1965_scan.pdf"


def _model_requests(mock: MockProviders) -> int:
    """Count the model requests the stand-in received.

    Parameters
    ----------
    mock
        The stand-in server.

    Returns
    -------
    int
        How many model requests it received.
    """

    return sum(1 for request in mock.requests if request.route == "model")


def test_a_failed_survey_saves_no_survey_and_its_spend_counts_next_time(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """A survey that fails leaves valid files, no ``pdf_survey.json`` and its spend.

    The next run surveys again, and the folder's total includes the failed run's
    requests.
    """

    mock_providers(
        answers=[survey_answer(languages=[]), "not an answer", survey_answer()]
    )
    advanced = {"survey": {"check_retries": 1}}

    with pytest.raises(SurveyError):
        pydelity.run(pdf_path(_SCAN), advanced=advanced, output_dir="out")

    failed = pydelity.load("out")
    assert failed.record is not None
    assert failed.record.status == "failed"
    assert failed.survey is None
    assert failed.facts is not None
    assert len(failed.ledger) == 2
    assert Path("out/report.html").is_file()

    retried = pydelity.run(pdf_path(_SCAN), advanced=advanced, output_dir="out")

    assert retried.record is not None
    assert retried.record.status == "paused"
    assert len(retried.ledger) == 3
    cost = retried.record.cost
    assert cost.output_folder_usd == sum(
        entry.cost_usd for entry in retried.ledger if entry.cost_usd is not None
    )
    assert cost.run_usd < cost.output_folder_usd


def test_a_folder_holding_another_pdfs_results_gives_a_warning(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Running a second PDF into a folder warns that it holds the first PDF's files."""

    mock_providers(answers=[survey_answer()])
    pydelity.run(pdf_path(_SCAN), output_dir="out")

    with pytest.warns(PydelityWarning, match="for another PDF"):
        result = pydelity.run(pdf_path("irs_pub1_arabic.pdf"), output_dir="out")

    assert result.record is not None
    (warning,) = result.record.warnings
    assert warning.code == "other_pdf_in_folder"
    assert warning.step is None
    files = warning.details["files"]
    assert isinstance(files, dict)
    assert set(files) == {"run.json", "pdf_facts.json"}


def test_a_new_probe_version_measures_again_and_reruns_the_survey(
    mock_providers: Callable[..., MockProviders],
    monkeypatch: pytest.MonkeyPatch,
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Saved facts from another probe version are measured again; the survey reruns."""

    mock = mock_providers(answers=[survey_answer()])
    first = pydelity.run(pdf_path(_SCAN), output_dir="out")
    monkeypatch.setattr("pydelity.surveying.facts.PROBE_VERSION", 2)

    second = pydelity.run(pdf_path(_SCAN), output_dir="out")

    assert first.facts is not None
    assert second.facts is not None
    assert second.facts.fingerprint != first.facts.fingerprint
    assert second.facts.probe_version == 2
    assert _model_requests(mock) == 2
    assert second.survey is not None
    assert second.survey.inputs.facts_fingerprint == second.facts.fingerprint


def test_a_rerun_with_unchanged_inputs_reuses_everything(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
) -> None:
    """A rerun whose inputs match measures nothing and sends nothing.

    The survey and every page file are reused. Settings outside their inputs, such
    as ``max_cost``, the provider retries, the request timeouts and how many pages
    run at once, may change without a rerun.
    """

    mock = mock_providers(**canned_answers(_SCAN))
    first = pydelity.run(pdf_path(_SCAN), output_dir="out", pause=False)
    requests_after_first = _model_requests(mock)

    second = pydelity.run(
        pdf_path(_SCAN),
        advanced={
            "extraction": {"concurrent_pages": 1, "request_timeout_seconds": 60},
            "provider_retries": 5,
            "survey": {"request_timeout_seconds": 60},
        },
        max_cost="50",
        output_dir="out",
    )

    assert requests_after_first == 5
    assert _model_requests(mock) == requests_after_first
    assert first.facts is not None
    assert second.facts is not None
    assert second.facts.measured_at == first.facts.measured_at
    assert second.survey == first.survey
    assert second.pages == first.pages
    assert second.record is not None
    survey_step, extraction_step = second.record.steps
    assert (
        survey_step.status,
        survey_step.requests,
        survey_step.pdf_transport,
    ) == ("reused", 0, None)
    assert survey_step.outputs == ["pdf_facts.json", "pdf_survey.json"]
    assert (extraction_step.status, extraction_step.requests) == ("reused", 0)
    assert extraction_step.pages is not None
    assert extraction_step.pages.model_dump() == {
        "extracted": 0,
        "reused": 2,
        "selected": 2,
    }
    assert second.record.cost.run_usd == 0


@pytest.mark.parametrize(
    "change",
    [
        {"advanced": {"survey": {"instructions": "Stamps are content."}}},
        {"languages": ["en"]},
        {"model": "openai:gpt-6.2-astra"},
        {"advanced": {"survey": {"effort": "low"}}},
        {"overwrite": True},
    ],
    ids=["instructions", "languages", "model", "survey-setting", "overwrite"],
)
def test_changing_a_survey_input_or_overwrite_reruns_the_survey(
    change: dict[str, object],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """A changed survey input, or ``overwrite``, sends a new request."""

    mock = mock_providers(answers=[survey_answer()])
    pydelity.run(pdf_path(_SCAN), output_dir="out")

    rerun = pydelity.run(pdf_path(_SCAN), config=change, output_dir="out")

    assert _model_requests(mock) == 2
    assert rerun.record is not None
    assert rerun.record.steps[0].status == "completed"


def test_damaged_outputs_and_leftover_temp_files_are_replaced(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Corrupt facts and survey files are regenerated with a warning each.

    A temporary file left by an interrupted write is removed.
    """

    mock = mock_providers(answers=[survey_answer()])
    pydelity.run(pdf_path(_SCAN), output_dir="out")
    Path("out/pdf_facts.json").write_text("{", encoding="utf-8")
    Path("out/pdf_survey.json").write_text('{"schema_version": "1.0"}', "utf-8")
    leftover = Path("out/pdf_survey.json.tmp-0123456789abcdef")
    leftover.write_text("partial", encoding="utf-8")

    with pytest.warns(PydelityWarning, match="again"):
        result = pydelity.run(pdf_path(_SCAN), output_dir="out")

    assert not leftover.exists()
    assert _model_requests(mock) == 2
    assert result.record is not None
    damaged = [w.details for w in result.record.warnings if w.code == "damaged_output"]
    assert damaged == [{"file": "pdf_facts.json"}, {"file": "pdf_survey.json"}]
    assert pydelity.load("out") == result


def test_no_output_file_holds_the_api_key(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    monkeypatch: pytest.MonkeyPatch,
    pdf_path: Callable[[str], Path],
) -> None:
    """The provider's API key appears in no file of the output folder.

    The run goes through the survey and page extraction, so the page files and the
    report's extracted pages are checked too.
    """

    mock_providers(**canned_answers(_SCAN))
    secret = "sk-test-not-a-real-key"  # noqa: S105  # pragma: allowlist secret
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)

    result = pydelity.run(pdf_path(_SCAN), output_dir="out", pause=False)

    assert result.record is not None
    assert result.record.status == "completed"
    assert sorted(path.name for path in Path("out/pages").iterdir()) == [
        "0000.json",
        "0001.json",
    ]
    for path in Path("out").rglob("*"):
        if path.is_file():
            assert secret.encode() not in path.read_bytes(), path


def test_run_json_records_each_step_its_pages_cost_and_review_issues(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
) -> None:
    """``run.json`` holds a record per step, its pages, its cost and its issues.

    A verifier problem about an item is a review issue naming the step, the page
    and the item's ID. Each page request is a ledger line with its page and agent,
    and a warning issued during page extraction names that step.
    """

    answers = canned_answers(_SCAN)
    page_answers = answers["page_answers"]
    assert isinstance(page_answers, dict)
    problem = {
        "category": "field",
        "description": "The first box is ticked on the page.",
        "item_ref": "f1",
    }
    page_answers[1] = page_answers[1] | {
        "verifier": {"corrected": None, "passed": False, "problems": [problem]}
    }
    mock_providers(answers=answers["answers"], page_answers=page_answers)

    first = pydelity.run(pdf_path(_SCAN), output_dir="out", pause=False)

    assert first.record is not None
    (issue,) = first.record.review
    assert (issue.step, issue.check, issue.page_index, issue.item_id) == (
        "extraction",
        "verifier",
        1,
        "p0001-001",
    )
    assert issue.message == "verifier: The first box is ticked on the page."
    # Pages run at the same time, so their ledger lines can come in any order.
    assert sorted(
        (entry.step, entry.page_index, entry.agent) for entry in first.ledger[1:]
    ) == [
        ("extraction", 0, "extractor"),
        ("extraction", 0, "verifier"),
        ("extraction", 1, "extractor"),
        ("extraction", 1, "verifier"),
    ]
    cost = first.record.cost
    assert set(cost.by_step) == {"survey", "extraction"}
    assert cost.by_step["survey"] + cost.by_step["extraction"] == cost.run_usd
    assert [step.cost_usd for step in first.record.steps] == [
        cost.by_step["survey"],
        cost.by_step["extraction"],
    ]
    extraction = first.record.steps[1]
    assert extraction.outputs == ["pages/", "figures/"]
    assert extraction.pdf_transport is None
    Path("out/pages/0000.json").write_text("{", encoding="utf-8")

    with pytest.warns(PydelityWarning, match="extracting page 1"):
        second = pydelity.run(pdf_path(_SCAN), output_dir="out")

    assert second.record is not None
    (warning,) = second.record.warnings
    assert (warning.code, warning.step) == ("damaged_output", "extraction")
    survey_step, extraction_step = second.record.steps
    assert survey_step.status == "reused"
    assert extraction_step.pages is not None
    assert extraction_step.pages.model_dump() == {
        "extracted": 1,
        "reused": 1,
        "selected": 2,
    }
    assert second.record.review == first.record.review

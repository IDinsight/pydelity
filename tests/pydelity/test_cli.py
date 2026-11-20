"""Tests for the ``pydelity`` command: options, questions, exit codes and output.

The command runs in-process with Typer's test runner, against the stand-in provider
server. Questions on the terminal are answered through the runner's input.
"""

# Standard Library
import json

from collections.abc import Callable
from pathlib import Path

# Third Party Library
import click
import pytest
import typer

from typer.testing import Result

# Package Library
import pydelity

from pydelity.errors import ExitCode
from tests.fixtures.mock_providers import MockProviders

# The question asked before spending, when max_cost is not in the way.
_CONFIRM = "Go ahead with the model requests?"

# The question asked when the run could go over max_cost.
_OVER = "Go ahead, even though this run could go over max_cost?"

# The 2-page scanned test PDF, with no text layer.
_SCAN = "irs_form_1040a_1965_scan.pdf"


def _record(folder: str = "out") -> pydelity.RunRecord:
    """Read the run record an output folder holds.

    Parameters
    ----------
    folder
        The output folder.

    Returns
    -------
    pydelity.RunRecord
        Its ``run.json``.
    """

    record = pydelity.load(folder).record
    assert record is not None
    return record


def _sent(mock: MockProviders) -> list[str]:
    """List the routes of the requests the stand-in received.

    Parameters
    ----------
    mock
        The stand-in server.

    Returns
    -------
    list[str]
        ``upload`` or ``model`` for each request, in order.
    """

    return [str(request.route) for request in mock.requests]


def test_a_pdf_alone_runs_the_survey_with_keys_from_the_environment(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
) -> None:
    """``pydelity <pdf> --yes`` with no config file surveys, pauses and says so.

    The output goes to the default folder, named after the PDF. The run stops after
    the new survey and tells how to go on; the same command again reuses the survey
    and extracts the pages.
    """

    mock = mock_providers(**canned_answers(_SCAN))

    result = run_cli([str(pdf_path(_SCAN)), "--yes"])

    assert result.exit_code == ExitCode.COMPLETED, result.output
    assert _sent(mock) == ["upload", "model"]
    folder = Path("pydelity-output") / Path(_SCAN).stem
    record = _record(str(folder))
    assert record.status == "paused"
    assert [(step.name, step.status) for step in record.steps] == [
        ("survey", "completed"),
        ("extraction", "skipped"),
    ]
    assert "Survey cost estimate: about $" in result.stderr
    assert "Extraction cost estimate" not in result.stderr
    assert (
        "Run paused: survey completed, extraction skipped; cost $0.02 this run "
        "(survey $0.02), $0.02 in the output folder; 0 review issues" in result.stderr
    )
    assert "Paused after the new survey." in result.stderr
    assert "run pydelity again to extract the pages" in result.stderr
    assert "--no-pause" in result.stderr
    assert "pdf_facts.json, pdf_survey.json, report.html" in result.stderr

    resumed = run_cli([str(pdf_path(_SCAN)), "--yes"])

    assert resumed.exit_code == ExitCode.COMPLETED, resumed.output
    assert _sent(mock) == ["upload"] + ["model"] * 5
    record = _record(str(folder))
    assert record.status == "completed"
    assert [(step.name, step.status) for step in record.steps] == [
        ("survey", "reused"),
        ("extraction", "completed"),
    ]
    assert "Extraction cost estimate: about $" in resumed.stderr
    assert "Paused" not in resumed.stderr


def test_the_pdf_argument_wins_over_the_config_file(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
    tmp_path: Path,
) -> None:
    """A PDF given on the command line replaces the config file's ``pdf``."""

    mock_providers(answers=[survey_answer()])
    config_file = tmp_path / "settings.json"
    config_file.write_text(
        json.dumps({"output_dir": "from-file", "pdf": str(pdf_path("irs_form_w9.pdf"))})
    )

    result = run_cli([str(pdf_path(_SCAN)), "-c", str(config_file), "-y"])

    assert result.exit_code == ExitCode.COMPLETED, result.output
    record = _record(str(tmp_path / "from-file"))
    assert Path(record.pdf.path) == pdf_path(_SCAN)


def test_without_a_terminal_or_yes_it_stops_before_spending(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
) -> None:
    """Without a terminal or ``--yes`` the command stops with exit code 3.

    Nothing is sent and the run is recorded as stopped. The facts were saved and
    their summary logged before the estimate and the attempt to ask.
    """

    mock = mock_providers(answers=[survey_answer()])

    result = run_cli([str(pdf_path(_SCAN)), "-d", "out", "--verbose"])

    assert result.exit_code == ExitCode.STOPPED, result.output
    log = result.stderr
    saved = log.index("Facts measured and saved to ")
    summary = log.index("No text layer on pages 0-1.")
    assert saved < summary < log.index("Survey cost estimate") < log.index("pass --yes")
    assert mock.requests == []
    assert pydelity.load("out").facts is not None
    assert _record().status == "stopped"


def test_answering_no_at_the_terminal_stops_before_spending(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
) -> None:
    """After the estimate, answering no stops the run with exit code 3."""

    mock = mock_providers(answers=[survey_answer()])

    result = run_cli([str(pdf_path(_SCAN)), "-d", "out"], input="n\n", terminal=True)

    assert result.exit_code == ExitCode.STOPPED, result.output
    assert _CONFIRM in result.output
    assert mock.requests == []
    assert _record().status == "stopped"


def test_answering_yes_at_the_terminal_runs_the_survey(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
) -> None:
    """After the estimate, answering yes runs the survey."""

    mock = mock_providers(answers=[survey_answer()])

    result = run_cli([str(pdf_path(_SCAN)), "-d", "out"], input="y\n", terminal=True)

    assert result.exit_code == ExitCode.COMPLETED, result.output
    assert result.output.count(_CONFIRM) == 1
    assert _sent(mock) == ["upload", "model"]


def test_over_max_cost_warns_then_a_yes_completes_with_one_question(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
) -> None:
    """A run that could go over ``max_cost`` warns, asks once, and a yes completes."""

    mock = mock_providers(answers=[survey_answer()])

    result = run_cli(
        [str(pdf_path(_SCAN)), "-d", "out", "--max-cost", "0.0001"],
        input="y\n",
        terminal=True,
    )

    assert result.exit_code == ExitCode.COMPLETED, result.output
    assert "over max_cost $0.0001" in result.stderr
    assert "plus what this run may still spend makes $" in result.stderr
    assert result.output.count(_OVER) == 1
    assert _CONFIRM not in result.output
    assert _sent(mock) == ["upload", "model"]
    (warning,) = _record().warnings
    assert warning.code == "max_cost_exceeded"
    assert (warning.details["check"], warning.details["allowed"]) == ("plan", True)


def test_over_max_cost_and_a_no_stops_with_nothing_sent(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
) -> None:
    """Answering no to the ``max_cost`` question stops before any upload or request."""

    mock = mock_providers(answers=[survey_answer()])

    result = run_cli(
        [str(pdf_path(_SCAN)), "-d", "out", "-mc", "0.0001"], input="n\n", terminal=True
    )

    assert result.exit_code == ExitCode.STOPPED, result.output
    assert mock.requests == []
    record = _record()
    assert record.status == "stopped"
    assert record.warnings[0].details["allowed"] is False


def test_over_max_cost_with_yes_completes_without_asking(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
) -> None:
    """``--yes`` goes over ``max_cost`` after the warning, with no question."""

    mock = mock_providers(answers=[survey_answer()])

    result = run_cli(
        [str(pdf_path(_SCAN)), "-d", "out", "--max-cost", "0.0001", "--yes"],
        terminal=True,
    )

    assert result.exit_code == ExitCode.COMPLETED, result.output
    assert "could go over max_cost" in result.stderr
    assert _OVER not in result.output
    assert _sent(mock) == ["upload", "model"]


def test_over_max_cost_without_a_terminal_or_yes_stops(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
) -> None:
    """Over ``max_cost`` with no terminal and no ``--yes``, the run stops resumably."""

    mock = mock_providers(answers=[survey_answer()])

    result = run_cli([str(pdf_path(_SCAN)), "-d", "out", "--max-cost", "0.0001"])

    assert result.exit_code == ExitCode.STOPPED, result.output
    assert mock.requests == []
    assert _record().status == "stopped"
    assert "Run pydelity again to continue" in result.stderr


def test_a_request_that_would_go_over_max_cost_asks_before_it_is_sent(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
    tmp_path: Path,
) -> None:
    """When real usage beats the estimate, the next request's check asks again.

    The first answer fails a check and costs far more than estimated, so the
    retry's check trips; answering no stops before the retry is sent.
    """

    estimate = pydelity.estimate(
        pdf_path(_SCAN), advanced={"survey": {"check_retries": 1}}, output_dir="out"
    )
    assert estimate.max_usd is not None
    max_cost = estimate.max_usd * 2
    mock = mock_providers(
        answers=[survey_answer(languages=[]), survey_answer()],
        input_tokens=5_000_000,
    )
    config_file = tmp_path / "settings.yaml"
    config_file.write_text("advanced:\n  survey:\n    check_retries: 1\n")

    result = run_cli(
        [
            str(pdf_path(_SCAN)),
            "-c",
            str(config_file),
            "-d",
            "out",
            "-mc",
            f"{max_cost}",
        ],
        input="y\nn\n",
        terminal=True,
    )

    assert result.exit_code == ExitCode.STOPPED, result.output
    assert result.output.index(_CONFIRM) < result.output.index(_OVER)
    assert _sent(mock) == ["upload", "model"]
    record = _record()
    assert record.status == "stopped"
    (warning,) = record.warnings
    assert (warning.details["check"], warning.details["allowed"]) == ("request", False)


def test_a_pdf_the_provider_rejects_ends_with_its_message(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
) -> None:
    """A provider rejecting the PDF ends the run with exit code 1 and its message."""

    mock = mock_providers(answers=[survey_answer()])
    rejection = "The PDF has more pages than this model accepts."
    mock.add_fault(message=rejection, route="model", status=400, times=None)

    result = run_cli([str(pdf_path(_SCAN)), "-d", "out", "-y"])

    assert result.exit_code == ExitCode.FAILED, result.output
    assert (
        f"anthropic:claude-opus-5-5: {rejection} The request carried {_SCAN} "
        "(2 pages, 85,909 bytes)." in result.stderr
    )
    assert _record().status == "failed"


def test_temporary_failures_past_the_retries_end_with_the_providers_message(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
    tmp_path: Path,
) -> None:
    """A request failing more times than the retry setting ends with exit code 1."""

    mock = mock_providers(answers=[survey_answer()])
    mock.add_fault(
        message="Overloaded right now.", route="model", status=529, times=None
    )
    config_file = tmp_path / "settings.yaml"
    config_file.write_text("advanced:\n  provider_retries: 1\n")

    result = run_cli([str(pdf_path(_SCAN)), "-c", str(config_file), "-d", "out", "-y"])

    assert result.exit_code == ExitCode.FAILED, result.output
    assert _sent(mock) == ["upload", "model", "model"]
    assert "Overloaded right now." in result.stderr
    assert "It still failed after 1 retry (advanced.provider_retries)." in result.stderr


def test_invalid_options_are_all_named_and_nothing_runs(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
) -> None:
    """Invalid options end with exit code 2, naming each, before anything is written."""

    mock = mock_providers(answers=[survey_answer()])

    options = [
        "-y",
        "-d",
        "out",
        "-m",
        "gemini:pro",
        "-mc",
        "-1",
        "-l",
        "en",
        "-l",
        "zz",
        "-p",
        "1,4-2",
    ]

    result = run_cli([str(pdf_path(_SCAN)), *options])

    assert result.exit_code == ExitCode.INVALID_INPUT, result.output
    assert "4 invalid settings:" in result.stderr
    for setting in ("- languages[1]:", "- max_cost:", "- model:", "- pages:"):
        assert setting in result.stderr
    assert mock.requests == []
    assert not Path("out").exists()


def test_a_missing_api_key_stops_after_saving_the_facts(
    monkeypatch: pytest.MonkeyPatch,
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
) -> None:
    """Without the provider's key the run ends with exit code 2; the facts stay."""

    monkeypatch.delenv("ANTHROPIC_API_KEY")

    result = run_cli([str(pdf_path(_SCAN)), "-d", "out", "-y"])

    assert result.exit_code == ExitCode.INVALID_INPUT, result.output
    assert "ANTHROPIC_API_KEY is not set" in result.stderr
    loaded = pydelity.load("out")
    assert loaded.facts is not None
    assert loaded.record is not None
    assert loaded.record.status == "failed"


def test_ctrl_c_at_the_question_records_an_interrupted_run(
    mock_providers: Callable[..., MockProviders],
    monkeypatch: pytest.MonkeyPatch,
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
) -> None:
    """Ctrl+C while the command waits for an answer exits with 130.

    ``run.json`` says the run was interrupted, and every file in the folder loads.
    """

    def interrupted(*args: object, **kwargs: object) -> bool:
        """Stand in for a question that the user answers with Ctrl+C."""

        raise KeyboardInterrupt

    mock = mock_providers(answers=[survey_answer()])
    monkeypatch.setattr(typer, "confirm", interrupted)

    result = run_cli([str(pdf_path(_SCAN)), "-d", "out"], terminal=True)

    assert result.exit_code == ExitCode.INTERRUPTED, result.output
    assert mock.requests == []
    assert _record().status == "interrupted"
    assert not list(Path("out").glob("*.tmp-*"))


def test_pages_and_no_pause_extract_only_those_pages_in_one_run(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
) -> None:
    """``-p 2 -np`` surveys the PDF and extracts only page 2 in the same run.

    The estimate before spending covers both steps. The summary gives each step's
    status, page counts and cost, and lists the page's review issue with its step,
    its page numbered from 1 and its item.
    """

    answers = canned_answers(_SCAN)
    page_answers = answers["page_answers"]
    assert isinstance(page_answers, dict)
    flawed = json.loads(json.dumps(page_answers[1]["extractor"]))
    flawed["items"][0]["label"] = "Not a label"
    mock = mock_providers(
        answers=answers["answers"],
        page_answers={
            1: {"extractor": flawed, "verifier": page_answers[1]["verifier"]}
        },
    )

    result = run_cli([str(pdf_path(_SCAN)), "-y", "-d", "out", "-p", "2", "-np"])

    assert result.exit_code == ExitCode.COMPLETED, result.output
    agents = [(r.page_index, r.agent) for r in mock.requests if r.route == "model"]
    assert agents == [(None, None)] + [(1, "extractor")] * 3 + [(1, "verifier")]
    record = _record()
    assert record.status == "completed"
    assert [(step.name, step.status) for step in record.steps] == [
        ("survey", "completed"),
        ("extraction", "completed"),
    ]
    assert "Paused" not in result.stderr
    assert "Extraction cost estimate: about $" in result.stderr
    assert "(1 page, up to 6 requests to anthropic:claude-opus-5-5)" in result.stderr
    assert (
        "Run completed: survey completed, extraction completed (1 page selected: 1 "
        "extracted, 0 reused); cost $0.12 this run (survey $0.02, extraction $0.10)"
    ) in result.stderr
    assert (
        "extraction, page 2, item p0001-001: labels: item 'f1' has the label "
        "'Not a label'"
    ) in result.stderr
    assert [path.name for path in Path("out/pages").iterdir()] == ["0001.json"]


@pytest.mark.parametrize("option", ["-i", "--instructions"])
def test_the_removed_instructions_option_is_an_unknown_option(
    mock_providers: Callable[..., MockProviders],
    option: str,
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
) -> None:
    """Instructions have no option, so either spelling is a usage error, exit 2.

    The message is compared without its colors, which the error panel has when
    the environment asks for them, as on CI.
    """

    mock = mock_providers(answers=[survey_answer()])

    result = run_cli([str(pdf_path(_SCAN)), "-y", "-d", "out", option, "Read it."])

    output = click.unstyle(result.output)
    assert result.exit_code == ExitCode.INVALID_INPUT, output
    assert f"No such option: {option}" in output
    assert mock.requests == []
    assert not Path("out").exists()

"""Tests for spend control from Python: ``max_cost``, unpriced models and estimates.

The Python API never prompts. A run that could go over ``max_cost`` warns, then
continues only when the caller passed ``allow_over_max_cost=True``.
"""

# Standard Library
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

# Third Party Library
import pytest

# Package Library
import pydelity

from pydelity.errors import BudgetExceededError, PydelityWarning
from tests.fixtures.mock_providers import MockProviders

# The 2-page scanned test PDF, with no text layer.
_SCAN = "irs_form_1040a_1965_scan.pdf"

# A model ID that genai-prices does not know, so its requests are unpriced.
_UNPRICED_MODEL = "anthropic:claude-not-a-real-model-1"


class _NoStdin:
    """A stand-in for ``sys.stdin`` that fails the test if anything reads it."""

    def isatty(self) -> bool:
        """Claim to be a terminal, so a prompt would be tempted to read."""

        return True

    def read(self, *args: object) -> str:
        """Fail: the Python API must never read input."""

        raise AssertionError("the Python API read stdin")

    def readline(self, *args: object) -> str:
        """Fail: the Python API must never read input."""

        raise AssertionError("the Python API read stdin")


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


def test_earlier_spend_counts_and_a_disallowed_run_stops_resumably(
    mock_providers: Callable[..., MockProviders],
    monkeypatch: pytest.MonkeyPatch,
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Spend from earlier runs counts toward ``max_cost``.

    Without ``allow_over_max_cost`` the run raises `BudgetExceededError` before
    any upload or request, records ``stopped`` and never reads stdin. The same call
    with ``allow_over_max_cost=True`` then completes and keeps the earlier spend.
    """

    mock = mock_providers(answers=[survey_answer()], input_tokens=1_000_000)
    first = pydelity.run(pdf_path(_SCAN), output_dir="out")
    assert first.record is not None
    spent = first.record.cost.run_usd
    estimate = pydelity.estimate(pdf_path(_SCAN), output_dir="out", overwrite=True)
    assert estimate.max_usd is not None
    assert estimate.max_usd < spent
    max_cost = spent + estimate.max_usd / 2
    monkeypatch.setattr("sys.stdin", _NoStdin())
    requests_before = len(mock.requests)

    with (
        pytest.raises(BudgetExceededError, match="allow_over_max_cost=True"),
        pytest.warns(PydelityWarning, match="could go over max_cost"),
    ):
        pydelity.run(
            pdf_path(_SCAN), max_cost=max_cost, output_dir="out", overwrite=True
        )

    assert len(mock.requests) == requests_before
    stopped = pydelity.load("out").record
    assert stopped is not None
    assert stopped.status == "stopped"
    (warning,) = stopped.warnings
    assert Decimal(str(warning.details["spent_usd"])) == spent
    assert Decimal(str(warning.details["projected_usd"])) == spent + estimate.max_usd
    assert warning.details["allowed"] is False

    with pytest.warns(PydelityWarning, match="could go over max_cost"):
        allowed = pydelity.run(
            pdf_path(_SCAN),
            allow_over_max_cost=True,
            max_cost=max_cost,
            output_dir="out",
            overwrite=True,
        )

    assert allowed.record is not None
    assert allowed.record.status == "completed"
    assert len(allowed.ledger) == 2
    assert allowed.record.cost.output_folder_usd == spent * 2
    assert allowed.record.warnings[0].details["allowed"] is True


def test_an_allowed_run_logs_and_records_the_max_cost_warning(
    log_messages: list[tuple[str, str]],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """With ``allow_over_max_cost=True`` the warning is logged, issued and recorded.

    The record names ``max_cost``, the spend so far, the projected spend, the check
    and the decision.
    """

    mock = mock_providers(answers=[survey_answer()])

    with pytest.warns(PydelityWarning) as issued:
        result = pydelity.run(
            pdf_path(_SCAN), allow_over_max_cost=True, max_cost="0.01", output_dir="out"
        )

    assert _sent(mock) == ["upload", "model"]
    assert result.record is not None
    (warning,) = result.record.warnings
    assert warning.code == "max_cost_exceeded"
    assert set(warning.details) == {
        "allowed",
        "check",
        "max_cost",
        "projected_usd",
        "spent_usd",
    }
    assert Decimal(str(warning.details["max_cost"])) == Decimal("0.01")
    assert warning.details["check"] == "plan"
    assert [str(item.message) for item in issued] == [warning.message]
    assert ("WARNING", warning.message) in log_messages


def test_an_unpriced_model_trips_max_cost_with_no_projection(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """With ``max_cost`` set, a model with no known price counts as going over it."""

    mock = mock_providers(answers=[survey_answer()])

    with (
        pytest.raises(BudgetExceededError),
        pytest.warns(PydelityWarning, match="(?i)no price is known"),
    ):
        pydelity.run(
            pdf_path(_SCAN), max_cost="100", model=_UNPRICED_MODEL, output_dir="out"
        )

    assert mock.requests == []
    record = pydelity.load("out").record
    assert record is not None
    warnings = {warning.code: warning for warning in record.warnings}
    assert warnings["max_cost_exceeded"].details["projected_usd"] is None


def test_an_unpriced_model_without_max_cost_runs_and_records_no_price(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Without ``max_cost`` nothing is checked; unpriced requests have null cost."""

    mock_providers(answers=[survey_answer()])

    with pytest.warns(PydelityWarning, match="No price is known"):
        result = pydelity.run(pdf_path(_SCAN), model=_UNPRICED_MODEL, output_dir="out")

    assert result.record is not None
    assert result.record.status == "completed"
    (entry,) = result.ledger
    assert (entry.cost_usd, entry.price_source) == (None, None)
    assert result.record.cost.unpriced_requests == 1
    assert result.record.cost.run_usd == Decimal(0)
    assert [w.code for w in result.record.warnings] == ["unpriced_model"]


def test_a_request_that_would_go_over_max_cost_stops_before_it_is_sent(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """When real usage beats the estimate, the next request is checked and stopped.

    The first answer fails a check and costs far more than estimated, so the
    retry's check trips and raises before the retry is sent.
    """

    advanced = {"survey": {"check_retries": 1}}
    estimate = pydelity.estimate(pdf_path(_SCAN), advanced=advanced, output_dir="out")
    assert estimate.max_usd is not None
    mock = mock_providers(
        answers=[survey_answer(languages=[]), survey_answer()], input_tokens=5_000_000
    )

    with (
        pytest.raises(BudgetExceededError),
        pytest.warns(PydelityWarning, match="could go over max_cost"),
    ):
        pydelity.run(
            pdf_path(_SCAN),
            advanced=advanced,
            max_cost=estimate.max_usd * 2,
            output_dir="out",
        )

    assert _sent(mock) == ["upload", "model"]
    record = pydelity.load("out").record
    assert record is not None
    assert record.status == "stopped"
    assert record.warnings[0].details["check"] == "request"


def test_prices_set_for_a_model_replace_the_looked_up_price(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Prices under ``advanced.models`` price the model's requests instead."""

    mock_providers(answers=[survey_answer()], input_tokens=3_000, output_tokens=600)
    prices = {"input_usd_per_mtok": "1", "output_usd_per_mtok": "5"}

    result = pydelity.run(
        pdf_path(_SCAN),
        advanced={"models": {"anthropic:claude-opus-5-5": prices}},
        output_dir="out",
    )

    (entry,) = result.ledger
    assert entry.cost_usd == Decimal("0.006")
    assert entry.price_source == "config"


def test_estimate_writes_nothing_and_a_reusable_survey_costs_nothing(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """`estimate` sends nothing and writes nothing; after a run it costs zero.

    The estimate also reports the folder's spend so far.
    """

    mock = mock_providers(answers=[survey_answer()])

    before = pydelity.estimate(pdf_path(_SCAN), max_cost="0.0001", output_dir="out")

    assert not Path("out").exists()
    assert mock.requests == []
    assert before.over_max_cost is True
    assert before.steps[0].requests_max == 3
    assert before.expected_usd is not None
    assert before.max_usd is not None
    assert 0 < before.expected_usd < before.max_usd

    run = pydelity.run(pdf_path(_SCAN), output_dir="out")
    requests_after_run = len(mock.requests)
    after = pydelity.estimate(pdf_path(_SCAN), max_cost="0.0001", output_dir="out")

    assert len(mock.requests) == requests_after_run
    assert after.steps[0].reused is True
    assert (after.expected_usd, after.max_usd, after.over_max_cost) == (0, 0, False)
    assert run.record is not None
    assert after.spent_usd == run.record.cost.output_folder_usd

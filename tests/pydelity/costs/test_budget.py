"""Tests for spend control from Python: ``max_cost``, unpriced models and estimates.

The Python API never prompts. A run that could go over ``max_cost`` warns, then
continues only when the caller passed ``allow_over_max_cost=True``.
"""

# Standard Library
import asyncio
import dataclasses
import re

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

# Third Party Library
import pytest

from pydantic_ai.messages import ModelResponse
from pydantic_ai.usage import RequestUsage

# Package Library
import pydelity

from pydelity.config.schemas import ModelPrices
from pydelity.costs.budget import SpendGuard
from pydelity.costs.pricing import price_response
from pydelity.costs.schemas import MaxCostWarning
from pydelity.errors import BudgetExceededError, PydelityWarning
from pydelity.providers.profiles import PROFILES
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


def test_a_cache_price_of_zero_is_priced_as_zero() -> None:
    """A cache price of 0 under ``advanced.models`` makes cached tokens free.

    An unset cache price still prices them at the input price.
    """

    response = ModelResponse(
        model_name="claude-opus-5-5",
        parts=[],
        usage=RequestUsage(
            cache_read_tokens=1_000_000,
            cache_write_tokens=1_000_000,
            input_tokens=3_000_000,
            output_tokens=0,
        ),
    )
    free = ModelPrices(
        cache_read_usd_per_mtok=Decimal(0),
        cache_write_usd_per_mtok=Decimal(0),
        input_usd_per_mtok=Decimal(2),
        output_usd_per_mtok=Decimal(10),
    )
    unset = ModelPrices(input_usd_per_mtok=Decimal(2), output_usd_per_mtok=Decimal(10))

    priced = {
        name: price_response(
            model="anthropic:claude-opus-5-5",
            overrides={"anthropic:claude-opus-5-5": prices},
            response=response,
        )
        for name, prices in (("free", free), ("unset", unset))
    }

    assert priced["free"] == (Decimal(2), "config")
    assert priced["unset"] == (Decimal(6), "config")


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
    assert result.record.status == "paused"
    (entry,) = result.ledger
    assert (entry.cost_usd, entry.price_source) == (None, None)
    assert result.record.cost.unpriced_requests == 1
    assert result.record.cost.run_usd == Decimal(0)
    assert [w.code for w in result.record.warnings] == ["unpriced_model"]


def test_each_page_image_counts_toward_a_request_s_highest_cost(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    monkeypatch: pytest.MonkeyPatch,
    pdf_path: Callable[[str], Path],
) -> None:
    """A page request's highest cost counts its image at the provider's image tokens.

    With an image priced far above the page's text, the run's expected cost passes
    the check before spending, but the check before the first page request projects
    the image's cost on top of the longest answer, and stops the run unsent.
    """

    mock = mock_providers(**canned_answers(_SCAN))
    pydelity.survey(pdf_path(_SCAN), output_dir="out")
    spent = pydelity.load("out").ledger[0].cost_usd
    assert spent is not None
    monkeypatch.setitem(
        PROFILES,
        "anthropic",
        dataclasses.replace(PROFILES["anthropic"], image_tokens=1_000_000),
    )
    settings: dict[str, object] = {
        "advanced": {
            "models": {
                "anthropic:claude-opus-5-5": {
                    "input_usd_per_mtok": "1",
                    "output_usd_per_mtok": "100",
                }
            }
        },
        "output_dir": "out",
        "pages": "1",
    }
    estimate = pydelity.estimate(pdf_path(_SCAN), config=settings)
    requests_before = len(mock.requests)

    with (
        pytest.raises(BudgetExceededError),
        pytest.warns(PydelityWarning, match="could go over max_cost") as issued,
    ):
        pydelity.extract(pdf_path(_SCAN), config=settings, max_cost=spent + 3)

    assert estimate.expected_usd is not None
    assert estimate.expected_usd < 3
    assert len(mock.requests) == requests_before
    (warning,) = issued
    projected = re.search(r"makes \$([0-9.,]+)", str(warning.message))
    assert projected is not None
    # The longest answer alone costs $3.20; the image adds at least $1.00.
    assert Decimal(projected[1].replace(",", "")) >= spent + Decimal("4.20")


def test_earlier_spend_counts_and_a_disallowed_run_stops_resumably(
    mock_providers: Callable[..., MockProviders],
    monkeypatch: pytest.MonkeyPatch,
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Spend from earlier runs counts toward ``max_cost``.

    Before the run, the spend so far plus the run's expected cost is compared with
    ``max_cost``. Without ``allow_over_max_cost`` the run raises
    `BudgetExceededError` before any upload or request, records ``stopped`` and
    never reads stdin. The same call with ``allow_over_max_cost=True`` then runs
    the survey, pauses after it as usual, and keeps the earlier spend.
    """

    mock = mock_providers(answers=[survey_answer()], input_tokens=1_000_000)
    first = pydelity.run(pdf_path(_SCAN), output_dir="out")
    assert first.record is not None
    spent = first.record.cost.run_usd
    estimate = pydelity.estimate(pdf_path(_SCAN), output_dir="out", overwrite=True)
    assert estimate.expected_usd is not None
    assert estimate.expected_usd < spent
    max_cost = spent + estimate.expected_usd / 2
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
    assert (
        Decimal(str(warning.details["projected_usd"])) == spent + estimate.expected_usd
    )
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
    assert allowed.record.status == "paused"
    assert len(allowed.ledger) == 2
    assert allowed.record.cost.output_folder_usd == spent * 2
    assert allowed.record.warnings[0].details["allowed"] is True


def test_estimate_writes_nothing_and_a_reusable_survey_costs_nothing(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
) -> None:
    """`estimate` sends nothing and writes nothing; after a full run it costs zero.

    Before the first run, the survey would pause the run, so only the survey is
    estimated. After a run through both steps with the verifier on, the survey and
    every page file are reused, so no step's figures include a verifier. The
    estimate also reports the folder's spend so far.
    """

    mock = mock_providers(**canned_answers(_SCAN))

    before = pydelity.estimate(pdf_path(_SCAN), max_cost="0.0001", output_dir="out")

    assert not Path("out").exists()
    assert mock.requests == []
    assert before.over_max_cost is True
    assert [step.name for step in before.steps] == ["survey"]
    assert before.steps[0].requests_max == 3
    assert before.expected_usd is not None
    assert before.max_usd is not None
    assert 0 < before.expected_usd < before.max_usd

    run = pydelity.run(pdf_path(_SCAN), output_dir="out", pause=False, verify=True)
    requests_after_run = len(mock.requests)
    after = pydelity.estimate(
        pdf_path(_SCAN), max_cost="0.0001", output_dir="out", verify=True
    )

    assert len(mock.requests) == requests_after_run
    assert [(step.name, step.reused, step.verifier) for step in after.steps] == [
        ("survey", True, False),
        ("extraction", True, False),
    ]
    assert (after.expected_usd, after.max_usd, after.over_max_cost) == (0, 0, False)
    assert run.record is not None
    assert after.spent_usd == run.record.cost.output_folder_usd


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


def test_requests_running_at_once_are_held_to_max_cost_together(
    tmp_path: Path,
) -> None:
    """Costs held by requests still running count toward ``max_cost``.

    Two requests of $0.40 and one of $0.20 fit a $1.00 limit together; a fourth
    request of $0.01 sent while they run gets the warning and, with a no, stops.
    The question is asked once.
    """

    asked: list[MaxCostWarning] = []

    def decide(warning: MaxCostWarning) -> bool:
        """Record the question and answer no."""

        asked.append(warning)
        return False

    guard = SpendGuard(
        decide=decide, ledger_path=tmp_path / "cost.jsonl", max_cost=Decimal("1.00")
    )

    async def send_at_once() -> None:
        """Hold three requests' costs, then try a fourth while they run."""

        release = asyncio.Event()
        holding = [asyncio.Event() for _ in range(3)]

        async def hold(cost: str, held: asyncio.Event) -> None:
            """Reserve a request's cost until released."""

            async with guard.reserve(Decimal(cost)):
                held.set()
                await release.wait()

        tasks = [
            asyncio.create_task(hold(cost, held))
            for cost, held in zip(("0.40", "0.40", "0.20"), holding, strict=True)
        ]
        for held in holding:
            await held.wait()
        with pytest.raises(BudgetExceededError):
            async with guard.reserve(Decimal("0.01")):
                pass
        release.set()
        await asyncio.gather(*tasks)

    with pytest.warns(PydelityWarning, match="could go over max_cost"):
        asyncio.run(send_at_once())

    (warning,) = asked
    assert (warning.check, warning.projected_usd) == ("request", Decimal("1.01"))
    assert warning.spent_usd == 0


def test_the_check_before_spending_counts_the_verifier_only_when_it_runs(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """The run's check against ``max_cost`` uses the estimate it would run with.

    A run through both steps projects the estimate without the verifier's requests,
    and the same run with the verifier on projects the estimate with them. Both
    stop before any upload or request.
    """

    mock = mock_providers(answers=[survey_answer()])
    projected: list[Decimal] = []
    estimated: list[Decimal | None] = []

    for verify in (False, True):
        estimate = pydelity.estimate(
            pdf_path(_SCAN), output_dir="out", pause=False, verify=verify
        )
        with (
            pytest.raises(BudgetExceededError),
            pytest.warns(PydelityWarning, match="could go over max_cost"),
        ):
            pydelity.run(
                pdf_path(_SCAN),
                max_cost="0.0001",
                output_dir="out",
                pause=False,
                verify=verify,
            )
        record = pydelity.load("out").record
        assert record is not None
        (warning,) = record.warnings
        projected.append(Decimal(str(warning.details["projected_usd"])))
        estimated.append(estimate.expected_usd)

    assert mock.requests == []
    assert projected == estimated
    assert projected[0] < projected[1]


def test_the_estimate_covers_page_extraction_and_its_verifier_only_when_it_runs(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Without the pause, the estimate adds the selected pages' extraction.

    Each page counts its extraction requests with their check retries, and its
    verifier requests only when the verifier is on, which the step's estimate
    says. The run's figures are the two steps' sums.
    """

    mock = mock_providers(answers=[survey_answer()])

    estimates = [
        pydelity.estimate(pdf_path(_SCAN), output_dir="out", pause=False),
        pydelity.estimate(pdf_path(_SCAN), output_dir="out", pause=False, verify=True),
        pydelity.estimate(pdf_path(_SCAN), output_dir="out", pages=2, pause=False),
        pydelity.estimate(
            pdf_path(_SCAN), output_dir="out", pages=2, pause=False, verify=True
        ),
    ]

    assert mock.requests == []
    for estimate in estimates:
        survey, extraction = estimate.steps
        assert (survey.name, extraction.name) == ("survey", "extraction")
        assert extraction.model == "anthropic:claude-opus-5-5"
        assert extraction.expected_usd is not None
        assert extraction.max_usd is not None
        assert 0 < extraction.expected_usd < extraction.max_usd
        assert survey.expected_usd is not None
        assert survey.max_usd is not None
        assert estimate.expected_usd == survey.expected_usd + extraction.expected_usd
        assert estimate.max_usd == survey.max_usd + extraction.max_usd
    steps = [estimate.steps[1] for estimate in estimates]
    assert [(step.pages, step.requests_max, step.verifier) for step in steps] == [
        (2, 6, False),
        (2, 12, True),
        (1, 3, False),
        (1, 6, True),
    ]
    for without, with_verifier in (steps[:2], steps[2:]):
        assert without.expected_usd is not None
        assert without.max_usd is not None
        assert with_verifier.expected_usd is not None
        assert with_verifier.max_usd is not None
        assert without.expected_usd < with_verifier.expected_usd
        assert without.max_usd < with_verifier.max_usd

"""Cost estimates and the ``max_cost`` check.

A run could exceed ``max_cost`` when the output folder's recorded spend plus what the
run may still spend is more than ``max_cost``. pydelity checks this before the run
spends anything, using the estimate's maximum, and before each model request, using
that request's highest possible cost. A model with no known price always fails the
check, because its cost cannot be known.

When a check fails, the run logs a warning and asks for a decision, once per run. Yes
lets the rest of the run exceed ``max_cost`` without asking again. No raises
`BudgetExceededError` before anything is sent.
"""

# Standard Library
import asyncio
import math

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

# Third Party Library
from loguru import logger

# Package Library
from pydelity.config.schemas import Config
from pydelity.costs.ledger import read_ledger
from pydelity.costs.pricing import price_usage
from pydelity.costs.schemas import (
    CostEstimate,
    MaxCostCheck,
    MaxCostWarning,
    StepEstimate,
)
from pydelity.errors import BudgetExceededError, PydelityError
from pydelity.utils.coroutines import run_in_daemon_thread, warn

# Characters of prompt text per input token, for the estimate.
PROMPT_CHARS_PER_TOKEN = 4

# The output tokens of a typical survey answer, thinking included, for the estimate.
TYPICAL_OUTPUT_TOKENS = 8_000

# Returns whether a run may exceed max_cost, given the warning's details.
type OverMaxCostDecision = Callable[[MaxCostWarning], bool]


def _over_message(
    *, max_cost: Decimal, projected: Decimal | None, spent: Decimal
) -> str:
    """Write the ``max_cost_exceeded`` warning.

    Parameters
    ----------
    max_cost
        The ``max_cost`` setting.
    projected
        The spend the run could reach, or ``None`` when the model is unpriced.
    spent
        What the output folder has recorded so far.

    Returns
    -------
    str
        The warning's text.
    """

    if projected is None:
        return (
            f"max_cost is {format_usd(max_cost)}, but no price is known for the model, "
            "so this run's spend cannot be held to it"
        )
    return (
        f"This run could go over max_cost: {format_usd(spent)} already spent in the "
        f"output folder plus this run's maximum makes {format_usd(projected)}, over "
        f"max_cost {format_usd(max_cost)}"
    )


class SpendDeclinedError(PydelityError):
    """The user chose not to start spending on model requests."""


class SpendGuard:
    """Enforce ``max_cost`` for one run, asking for a decision at most once.

    Parameters
    ----------
    decide
        Returns whether the run may exceed ``max_cost``. It runs on a daemon thread,
        off the event loop, because it may wait for an answer on the terminal.
    ledger_path
        The output folder's ``cost.jsonl``. Its total, from every run, counts
        toward ``max_cost``.
    max_cost
        The ``max_cost`` setting. ``None`` turns the checks off.

    Attributes
    ----------
    allowed
        Whether the run may exceed ``max_cost``, after a yes decision.
    warnings
        The ``max_cost_exceeded`` warnings so far, with their decisions.
    """

    def __init__(
        self,
        *,
        decide: OverMaxCostDecision,
        ledger_path: Path,
        max_cost: Decimal | None,
    ) -> None:
        """Set up the guard for one run."""

        self._decide = decide
        self._ledger_path = ledger_path
        self._lock = asyncio.Lock()
        self._max_cost = max_cost
        self.allowed = False
        self.warnings: list[MaxCostWarning] = []

    async def check(
        self, *, check: MaxCostCheck, upper_bound_usd: Decimal | None
    ) -> None:
        """Check that spending up to ``upper_bound_usd`` stays within ``max_cost``.

        Checks run one at a time, so concurrent requests ask for a decision only once.

        Parameters
        ----------
        check
            ``plan`` before the run spends anything, or ``request`` before a request.
        upper_bound_usd
            The most the run (``plan``) or the request (``request``) can cost;
            ``None`` when no price is known for the model.

        Raises
        ------
        BudgetExceededError
            If the check fails and the decision is no.
        """

        if self._max_cost is None or self.allowed:
            return
        async with self._lock:
            if self.allowed:
                return
            spent = read_ledger(self._ledger_path).spent_usd
            projected = None if upper_bound_usd is None else spent + upper_bound_usd
            if projected is not None and projected <= self._max_cost:
                return

            message = _over_message(
                max_cost=self._max_cost, projected=projected, spent=spent
            )
            logger.warning(message)
            warn(message)
            warning = MaxCostWarning(
                allowed=None,
                check=check,
                max_cost=self._max_cost,
                projected_usd=projected,
                spent_usd=spent,
            )
            allowed = await run_in_daemon_thread(lambda: self._decide(warning))
            self.warnings.append(warning.model_copy(update={"allowed": allowed}))
            if not allowed:
                raise BudgetExceededError(
                    f"Stopped before spending more: this run could go over max_cost "
                    f"({format_usd(self._max_cost)}). To continue, raise max_cost, "
                    "pass --yes on the command line, or call with "
                    "allow_over_max_cost=True."
                )
            self.allowed = True


def estimate_survey(
    *,
    config: Config,
    page_count: int,
    prompt_chars: int,
    reused: bool,
    spent_usd: Decimal,
) -> CostEstimate:
    """Estimate what the survey will cost, before anything is spent.

    Input tokens per request are the page count times the provider's tokens per PDF
    page, plus the prompt's characters divided by `PROMPT_CHARS_PER_TOKEN`. The
    expected cost is one request with `TYPICAL_OUTPUT_TOKENS` of output. The maximum
    is the first request and every check retry, each with ``max_output_tokens`` of
    output and the earlier answers added to its input. Both ignore prompt caching, so
    they overestimate.

    Parameters
    ----------
    config
        The run's settings.
    page_count
        The PDF's page count.
    prompt_chars
        The prompt's length in characters, without the PDF.
    reused
        Whether the saved survey will be reused, so nothing is sent.
    spent_usd
        What the output folder has recorded so far.

    Returns
    -------
    CostEstimate
        The expected and maximum cost, the folder's spend, and whether the run would
        go over ``max_cost``.
    """

    model = config.model
    survey = config.advanced.survey
    requests_max = 0 if reused else survey.check_retries + 1
    input_tokens = page_count * config.model_choice.profile.pdf_tokens_per_page
    input_tokens += math.ceil(prompt_chars / PROMPT_CHARS_PER_TOKEN)

    def price(*, input_count: int, output_count: int) -> Decimal | None:
        """Price token counts for the run's model."""

        return price_usage(
            input_tokens=input_count,
            model=model,
            output_tokens=output_count,
            overrides=config.advanced.models,
        )

    expected = price(input_count=input_tokens, output_count=TYPICAL_OUTPUT_TOKENS)
    attempts = [
        price(
            input_count=input_tokens + attempt * survey.max_output_tokens,
            output_count=survey.max_output_tokens,
        )
        for attempt in range(requests_max)
    ]
    priced = expected is not None and all(cost is not None for cost in attempts)
    if reused:
        expected, maximum = Decimal(0), Decimal(0)
    elif priced:
        maximum = sum((cost for cost in attempts if cost is not None), Decimal(0))
    else:
        expected = maximum = None

    step = StepEstimate(
        expected_usd=expected,
        max_usd=maximum,
        model=model,
        name="survey",
        requests_max=requests_max,
        reused=reused,
    )
    warnings = []
    if not priced and not reused:
        warnings.append(
            f"No price is known for {model}, so its cost will not be recorded; set its "
            f'prices under advanced.models."{model}" to track it'
        )
    over = config.max_cost is not None and (
        maximum is None or spent_usd + maximum > config.max_cost
    )
    return CostEstimate(
        expected_usd=expected,
        max_cost=config.max_cost,
        max_usd=maximum,
        over_max_cost=over and not reused,
        priced=priced or reused,
        spent_usd=spent_usd,
        steps=[step],
        warnings=warnings,
    )


def format_usd(amount: Decimal) -> str:
    """Format an amount of US dollars for display.

    Parameters
    ----------
    amount
        The amount.

    Returns
    -------
    str
        Cents for amounts from one cent up, four decimals below that.

    Examples
    --------
    >>> format_usd(Decimal("1.2345")), format_usd(Decimal("0.00412"))
    ('$1.23', '$0.0041')
    """

    if 0 < amount < Decimal("0.01"):
        return f"${amount:.4f}"
    return f"${amount:,.2f}"

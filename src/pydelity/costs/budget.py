"""Cost estimates and the ``max_cost`` check.

A run could exceed ``max_cost`` when the output folder's recorded spend plus what the
run may still spend is more than ``max_cost``. pydelity checks this before the run
spends anything, using the estimate's expected cost, and before each model request,
using that request's highest possible cost. Each request holds its highest possible
cost until its answer is recorded or it ends without one, and later checks count what
is held, so requests sent at the same time cannot go over ``max_cost`` together. A
model with no known price always fails the check, because its cost cannot be known.

When a check fails, the run logs a warning and asks for a decision, once per run. Yes
lets the rest of the run exceed ``max_cost`` without asking again. No raises
`BudgetExceededError` before anything is sent, and every later check in the run
raises it too, without asking.
"""

# Standard Library
import asyncio
import math

from collections.abc import AsyncGenerator, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

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

# Characters of a page's text layer per output token of its extraction, beyond
# `TYPICAL_PAGE_OUTPUT_TOKENS`, for the estimate. The answer repeats the text with an
# item's fields around it.
TEXT_CHARS_PER_OUTPUT_TOKEN = 2

# The output tokens of a typical page-break verdict, thinking included, for the
# estimate. The judge's and the verifier's verdicts are alike.
TYPICAL_BREAK_OUTPUT_TOKENS = 4_000

# The output tokens of a typical survey answer, thinking included, for the estimate.
TYPICAL_OUTPUT_TOKENS = 8_000

# The output tokens of a typical page extraction, thinking included, before the
# page's text is counted, for the estimate.
TYPICAL_PAGE_OUTPUT_TOKENS = 4_000

# The output tokens of a typical verdict on the survey, thinking included, for the
# estimate: three quarters of a typical survey answer, as for a page.
TYPICAL_SURVEY_VERDICT_OUTPUT_TOKENS = 6_000

# The output tokens of a typical verdict on a page, thinking included, for the
# estimate.
TYPICAL_VERDICT_OUTPUT_TOKENS = 3_000

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
        f"output folder plus what this run may still spend makes "
        f"{format_usd(projected)}, over max_cost {format_usd(max_cost)}"
    )


def _price(
    *, config: Config, input_tokens: int, model: str, output_tokens: int
) -> Decimal | None:
    """Price one request's token counts.

    Parameters
    ----------
    config
        The run's settings, for any price overrides.
    input_tokens
        The request's input tokens.
    model
        The model, as ``<provider>:<model-id>``.
    output_tokens
        The answer's output tokens.

    Returns
    -------
    Decimal | None
        The cost in US dollars, or ``None`` when no price is known for the model.
    """

    return price_usage(
        input_tokens=input_tokens,
        model=model,
        output_tokens=output_tokens,
        overrides=config.advanced.models,
    )


def _stopped_error(max_cost: Decimal) -> BudgetExceededError:
    """Make the error that stops a run whose spend may not exceed ``max_cost``.

    Parameters
    ----------
    max_cost
        The ``max_cost`` setting.

    Returns
    -------
    BudgetExceededError
        The error, saying how to continue.
    """

    return BudgetExceededError(
        f"Stopped before spending more: this run could go over max_cost "
        f"({format_usd(max_cost)}). To continue, raise max_cost, pass --yes on the "
        "command line, or call with allow_over_max_cost=True."
    )


def _sum_or_none(costs: Sequence[Decimal | None]) -> Decimal | None:
    """Add costs, unless one is unknown.

    Parameters
    ----------
    costs
        The costs; ``None`` where no price is known.

    Returns
    -------
    Decimal | None
        Their sum, or ``None`` when any is ``None``.
    """

    if any(cost is None for cost in costs):
        return None
    return sum((cost for cost in costs if cost is not None), Decimal(0))


def _unpriced_message(model: str) -> str:
    """Write the warning for a model with no known price.

    Parameters
    ----------
    model
        The model, as ``<provider>:<model-id>``.

    Returns
    -------
    str
        The warning's text, saying how to set a price.
    """

    return (
        f"No price is known for {model}, so its cost will not be recorded; set its "
        f'prices under advanced.models."{model}" to track it'
    )


@dataclass(frozen=True)
class BreakRequestSize:
    """How large one break's request is, for the page-break verification estimate.

    Attributes
    ----------
    chars
        The request's instructions, both pages' details and the verdict format, in
        characters, without the images. The judge and the verifier send the same
        request.
    """

    chars: int


@dataclass(frozen=True)
class PageRequestSize:
    """How large one page's requests are, for the page extraction estimate.

    Attributes
    ----------
    extractor_chars
        The extraction model's instructions, the page's details and the answer
        format, in characters, without the image.
    text_chars
        The page's measured text-layer characters, which an answer's text roughly
        matches.
    verifier_chars
        The verifier's instructions, the page's details and the verdict format, in
        characters, without the image and the answer it reviews.
    """

    extractor_chars: int
    text_chars: int
    verifier_chars: int


class SpendDeclinedError(PydelityError):
    """The user chose not to start spending on model requests."""


class SpendGuard:
    """Enforce ``max_cost`` for one run, asking for a decision at most once.

    Each model request goes through `reserve`, which holds the request's highest
    possible cost while it runs, so requests sent at the same time are checked
    together.

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
        self._declined = False
        self._ledger_path = ledger_path
        self._lock = asyncio.Lock()
        self._max_cost = max_cost
        self._reserved = Decimal(0)
        self.allowed = False
        self.warnings: list[MaxCostWarning] = []

    async def _pass_or_ask(
        self, *, check: MaxCostCheck, max_cost: Decimal, upper_bound_usd: Decimal | None
    ) -> None:
        """Pass when the spend stays within ``max_cost``; otherwise warn and ask.

        Call it while holding the lock, so only one question is asked.

        Parameters
        ----------
        check
            ``plan`` before the run spends anything, or ``request`` before a request.
        max_cost
            The ``max_cost`` setting.
        upper_bound_usd
            The run's expected cost (``plan``) or the request's maximum
            (``request``); ``None`` when no price is known for the model.

        Raises
        ------
        BudgetExceededError
            If the spend could exceed ``max_cost`` and the decision is no, or an
            earlier decision in the run was no.
        """

        if self._declined:
            raise _stopped_error(max_cost)
        spent = read_ledger(self._ledger_path).spent_usd
        projected = (
            None
            if upper_bound_usd is None
            else spent + self._reserved + upper_bound_usd
        )
        if projected is not None and projected <= max_cost:
            return

        message = _over_message(max_cost=max_cost, projected=projected, spent=spent)
        warning = MaxCostWarning(
            allowed=None,
            check=check,
            max_cost=max_cost,
            projected_usd=projected,
            spent_usd=spent,
        )
        issued = warn(
            message,
            code="max_cost_exceeded",
            details=warning.model_dump(mode="json"),
        )
        allowed = await run_in_daemon_thread(lambda: self._decide(warning))
        issued.details["allowed"] = allowed
        self.warnings.append(warning.model_copy(update={"allowed": allowed}))
        if not allowed:
            self._declined = True
            raise _stopped_error(max_cost)
        self.allowed = True

    async def check(
        self, *, check: MaxCostCheck, upper_bound_usd: Decimal | None
    ) -> None:
        """Check that spending ``upper_bound_usd`` more stays within ``max_cost``.

        The output folder's recorded spend and the costs held by requests still
        running count too. Checks run one at a time, so concurrent checks ask for a
        decision only once.

        Parameters
        ----------
        check
            ``plan`` before the run spends anything, or ``request`` before a request.
        upper_bound_usd
            The run's expected cost (``plan``) or the request's maximum
            (``request``); ``None`` when no price is known for the model.

        Raises
        ------
        BudgetExceededError
            If the check fails and the decision is no.
        """

        if self._max_cost is None or self.allowed:
            return
        async with self._lock:
            if not self.allowed:
                await self._pass_or_ask(
                    check=check,
                    max_cost=self._max_cost,
                    upper_bound_usd=upper_bound_usd,
                )

    @asynccontextmanager
    async def reserve(self, upper_bound_usd: Decimal | None) -> AsyncGenerator[None]:
        """Check one model request and hold its highest cost while it runs.

        Use it in an ``async with`` block around sending the request and recording
        its answer. The cost is released when the block ends, also with an error or
        when the request is canceled.

        Parameters
        ----------
        upper_bound_usd
            The most the request can cost; ``None`` when no price is known for the
            model.

        Yields
        ------
        None
            Nothing; the cost is held while the block runs.

        Raises
        ------
        BudgetExceededError
            If the request could take the spend over ``max_cost`` and the decision is
            no; nothing is held.
        """

        held = Decimal(0)
        if self._max_cost is not None and not self.allowed:
            # Check and hold under one lock, so a request sent at the same time sees
            # this one's cost.
            async with self._lock:
                if not self.allowed:
                    await self._pass_or_ask(
                        check="request",
                        max_cost=self._max_cost,
                        upper_bound_usd=upper_bound_usd,
                    )
                held = upper_bound_usd or Decimal(0)
                self._reserved += held
        try:
            yield
        finally:
            self._reserved -= held


def estimate_extraction(
    *, config: Config, pages: Sequence[PageRequestSize]
) -> StepEstimate:
    """Estimate what page extraction will cost, before anything is spent.

    Each page's input tokens are its request size divided by
    `PROMPT_CHARS_PER_TOKEN`, plus the provider's tokens per image. The expected cost
    is one extractor request, whose answer is `TYPICAL_PAGE_OUTPUT_TOKENS` plus the
    page's text-layer characters divided by `TEXT_CHARS_PER_OUTPUT_TOKEN`, and, when
    page extraction's verifier is on, one verifier request, which reads that answer
    and gives `TYPICAL_VERDICT_OUTPUT_TOKENS`. The maximum is the first request and
    every check retry of each agent that runs, each with ``max_output_tokens`` of
    output and the earlier answers added to its input. Both ignore prompt caching, so
    they overestimate.

    Parameters
    ----------
    config
        The run's settings.
    pages
        The size of each page's requests, for the pages to extract.

    Returns
    -------
    StepEstimate
        The step's expected and maximum cost; reused when no page is to be
        extracted.
    """

    model = config.extraction_model.setting
    settings = config.advanced.extraction
    longest = settings.max_output_tokens
    attempts = settings.check_retries + 1
    image_tokens = config.extraction_model.profile.image_tokens
    verify = config.verify_extraction

    expected: list[Decimal | None] = []
    maximum: list[Decimal | None] = []
    for page in pages:
        extractor_input = (
            math.ceil(page.extractor_chars / PROMPT_CHARS_PER_TOKEN) + image_tokens
        )
        answer = min(
            longest,
            TYPICAL_PAGE_OUTPUT_TOKENS
            + math.ceil(page.text_chars / TEXT_CHARS_PER_OUTPUT_TOKEN),
        )
        expected.append(
            _price(
                config=config,
                input_tokens=extractor_input,
                model=model,
                output_tokens=answer,
            )
        )
        maximum += [
            _price(
                config=config,
                input_tokens=extractor_input + attempt * longest,
                model=model,
                output_tokens=longest,
            )
            for attempt in range(attempts)
        ]
        if not verify:
            continue

        verifier_input = (
            math.ceil(page.verifier_chars / PROMPT_CHARS_PER_TOKEN) + image_tokens
        )
        expected.append(
            _price(
                config=config,
                input_tokens=verifier_input + answer,
                model=model,
                output_tokens=min(longest, TYPICAL_VERDICT_OUTPUT_TOKENS),
            )
        )
        # The verifier also reads the extraction, at most one longest answer.
        maximum += [
            _price(
                config=config,
                input_tokens=verifier_input + (attempt + 1) * longest,
                model=model,
                output_tokens=longest,
            )
            for attempt in range(attempts)
        ]

    expected_usd, max_usd = _sum_or_none(expected), _sum_or_none(maximum)
    priced = expected_usd is not None and max_usd is not None
    agents = 2 if verify else 1
    return StepEstimate(
        breaks=None,
        expected_usd=expected_usd if priced else None,
        max_usd=max_usd if priced else None,
        model=model,
        name="extraction",
        pages=len(pages),
        requests_max=agents * attempts * len(pages),
        reused=not pages,
        verifier=verify and bool(pages),
    )


def estimate_page_breaks(
    *, breaks: Sequence[BreakRequestSize], config: Config
) -> StepEstimate:
    """Estimate what page-break verification will cost, before anything is spent.

    Each break's input tokens are its request size divided by
    `PROMPT_CHARS_PER_TOKEN`, plus the provider's tokens per image for each of its
    two page images. The expected cost is one judge request and, when page-break
    verification's verifier is on, one verifier request, the same request sent
    again, each with `TYPICAL_BREAK_OUTPUT_TOKENS` of output. The maximum is the
    first request and every check retry of each agent that runs, each with
    ``max_output_tokens`` of output and the earlier answers added to its input. Both
    ignore prompt caching, so they overestimate.

    Parameters
    ----------
    breaks
        The size of each break's request, for the breaks the models would judge.
        A break with a page that has no content items needs no request and is not
        among them.
    config
        The run's settings.

    Returns
    -------
    StepEstimate
        The step's expected and maximum cost; reused when no break is to be judged.
    """

    choice = config.page_breaks_model
    model = choice.setting
    settings = config.advanced.page_breaks
    longest = settings.max_output_tokens
    attempts = settings.check_retries + 1
    image_tokens = 2 * choice.profile.image_tokens
    verify = config.verify_page_breaks
    agents = 2 if verify else 1

    expected: list[Decimal | None] = []
    maximum: list[Decimal | None] = []
    for size in breaks:
        input_tokens = math.ceil(size.chars / PROMPT_CHARS_PER_TOKEN) + image_tokens
        # Each agent that runs sends the same request, with its own retries.
        expected += agents * [
            _price(
                config=config,
                input_tokens=input_tokens,
                model=model,
                output_tokens=min(longest, TYPICAL_BREAK_OUTPUT_TOKENS),
            )
        ]
        maximum += agents * [
            _price(
                config=config,
                input_tokens=input_tokens + attempt * longest,
                model=model,
                output_tokens=longest,
            )
            for attempt in range(attempts)
        ]

    expected_usd, max_usd = _sum_or_none(expected), _sum_or_none(maximum)
    priced = expected_usd is not None and max_usd is not None
    return StepEstimate(
        breaks=len(breaks),
        expected_usd=expected_usd if priced else None,
        max_usd=max_usd if priced else None,
        model=model,
        name="page_breaks",
        pages=None,
        requests_max=agents * attempts * len(breaks),
        reused=not breaks,
        verifier=verify and bool(breaks),
    )


def estimate_run(
    *, config: Config, spent_usd: Decimal, steps: Sequence[StepEstimate]
) -> CostEstimate:
    """Add up the estimates of the steps a run will perform.

    The run is over ``max_cost`` when it is set and the folder's spend plus the
    expected cost exceeds it, or a step that will send requests has no known price.

    Parameters
    ----------
    config
        The run's settings.
    spent_usd
        What the output folder has recorded so far.
    steps
        Each step's estimate, in the order the steps run.

    Returns
    -------
    CostEstimate
        The steps, their expected and maximum cost, the folder's spend, whether the
        run would go over ``max_cost``, and one warning per model with no known
        price, in step order.
    """

    sending = [step for step in steps if not step.reused]
    unpriced = list(
        dict.fromkeys(step.model for step in sending if step.expected_usd is None)
    )
    expected = _sum_or_none([step.expected_usd for step in sending])
    maximum = _sum_or_none([step.max_usd for step in sending])
    over = (
        config.max_cost is not None
        and bool(sending)
        and (expected is None or spent_usd + expected > config.max_cost)
    )
    return CostEstimate(
        expected_usd=expected,
        max_cost=config.max_cost,
        max_usd=maximum,
        over_max_cost=over,
        priced=not unpriced,
        spent_usd=spent_usd,
        steps=list(steps),
        warnings=[_unpriced_message(model) for model in unpriced],
    )


def estimate_survey(
    *,
    config: Config,
    page_count: int,
    prompt_chars: int,
    reused: bool,
    verifier_chars: int,
) -> StepEstimate:
    """Estimate what the survey will cost, before anything is spent.

    Each request's input tokens are the page count times the provider's tokens per
    PDF page, plus its prompt's characters divided by `PROMPT_CHARS_PER_TOKEN`. The
    expected cost is one survey request with `TYPICAL_OUTPUT_TOKENS` of output and,
    when the survey's verifier is on, one verifier request, which reads that answer
    and gives `TYPICAL_SURVEY_VERDICT_OUTPUT_TOKENS`. The maximum is the first request
    and every check retry of each agent that runs, each with ``max_output_tokens`` of
    output and the earlier answers added to its input. Both ignore prompt caching, so
    they overestimate.

    Parameters
    ----------
    config
        The run's settings.
    page_count
        The PDF's page count.
    prompt_chars
        The survey prompt's length in characters, without the PDF.
    reused
        Whether the saved survey will be reused, so nothing is sent.
    verifier_chars
        The verifier prompt's length in characters, without the PDF and the answer it
        reviews.

    Returns
    -------
    StepEstimate
        The step's expected and maximum cost.
    """

    model = config.survey_model.setting
    if reused:
        return StepEstimate(
            breaks=None,
            expected_usd=Decimal(0),
            max_usd=Decimal(0),
            model=model,
            name="survey",
            pages=None,
            requests_max=0,
            reused=True,
            verifier=False,
        )

    settings = config.advanced.survey
    longest = settings.max_output_tokens
    attempts = settings.check_retries + 1
    verify = config.verify_survey
    pdf_tokens = page_count * config.survey_model.profile.pdf_tokens_per_page
    survey_input = pdf_tokens + math.ceil(prompt_chars / PROMPT_CHARS_PER_TOKEN)
    expected = [
        _price(
            config=config,
            input_tokens=survey_input,
            model=model,
            output_tokens=TYPICAL_OUTPUT_TOKENS,
        )
    ]
    maximum = [
        _price(
            config=config,
            input_tokens=survey_input + attempt * longest,
            model=model,
            output_tokens=longest,
        )
        for attempt in range(attempts)
    ]
    if verify:
        verifier_input = pdf_tokens + math.ceil(verifier_chars / PROMPT_CHARS_PER_TOKEN)
        expected.append(
            _price(
                config=config,
                input_tokens=verifier_input + min(longest, TYPICAL_OUTPUT_TOKENS),
                model=model,
                output_tokens=min(longest, TYPICAL_SURVEY_VERDICT_OUTPUT_TOKENS),
            )
        )
        # The verifier also reads the survey's answer, at most one longest answer.
        maximum += [
            _price(
                config=config,
                input_tokens=verifier_input + (attempt + 1) * longest,
                model=model,
                output_tokens=longest,
            )
            for attempt in range(attempts)
        ]

    expected_usd, max_usd = _sum_or_none(expected), _sum_or_none(maximum)
    priced = expected_usd is not None and max_usd is not None
    agents = 2 if verify else 1
    return StepEstimate(
        breaks=None,
        expected_usd=expected_usd if priced else None,
        max_usd=max_usd if priced else None,
        model=model,
        name="survey",
        pages=None,
        requests_max=agents * attempts,
        reused=False,
        verifier=verify,
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

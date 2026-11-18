"""pydelity's Python API.

Each function has an async version whose name starts with ``a``, such as `arun`, and a
sync version without the ``a``, such as `run`. Both take the same arguments and give
the same results, errors and warnings. The sync version runs the async one with
`asyncio.run`, so it cannot be called while an event loop is running, as in a Jupyter
cell or async code. Await the async version there instead.

`arun` and `run` do not prompt for input. The ``pydelity`` command calls
`arun_with_questions` instead, which can ask for confirmation on the terminal before
spending money on model requests.
"""

# Standard Library
import asyncio
import json
import os

from collections.abc import Callable
from pathlib import Path

# Third Party Library
from loguru import logger

# Package Library
from pydelity.config.loading import ConfigSource, resolve_config
from pydelity.config.schemas import Config
from pydelity.costs.budget import (
    OverMaxCostDecision,
    SpendDeclinedError,
    SpendGuard,
    estimate_survey,
    format_usd,
)
from pydelity.costs.ledger import LEDGER_FILE_NAME, read_ledger
from pydelity.costs.schemas import CostEstimate, MaxCostWarning
from pydelity.surveying.facts import measure_facts
from pydelity.surveying.schemas import PdfFacts
from pydelity.utils.coroutines import run_in_daemon_thread, run_sync, warn
from pydelity.utils.files import remove_stale_temp_files
from pydelity.utils.pdf import open_pdf

# Asks whether to go ahead and spend, given the cost estimate.
type SpendConfirmation = Callable[[CostEstimate], bool]


async def _ask_before_spending(
    *, confirm: SpendConfirmation | None, estimate: CostEstimate, guard: SpendGuard
) -> None:
    """Check the estimate against ``max_cost`` and ask whether to continue.

    If the estimate exceeds ``max_cost``, only the guard's over-``max_cost`` question
    is asked. Otherwise ``confirm`` is called, if given.

    Parameters
    ----------
    confirm
        Returns whether to continue. ``None`` continues without asking.
    estimate
        The cost estimate, already logged.
    guard
        The run's ``max_cost`` guard.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and the decision is no.
    SpendDeclinedError
        If ``confirm`` answers no.
    """

    if estimate.over_max_cost:
        await guard.check(check="plan", upper_bound_usd=estimate.max_usd)
    elif confirm is not None and not await run_in_daemon_thread(
        lambda: confirm(estimate)
    ):
        raise SpendDeclinedError(
            "Stopped before any model request, so nothing was spent. The measured "
            "facts are saved and will be reused next time."
        )


def _estimate_cost(
    *, config: Config, facts: PdfFacts, ledger_path: Path, page_count: int
) -> CostEstimate:
    """Estimate the run's cost, counting what the output folder has already spent.

    Parameters
    ----------
    config
        The run's settings.
    facts
        The measured facts.
    ledger_path
        The output folder's ``cost.jsonl``.
    page_count
        The PDF's page count.

    Returns
    -------
    CostEstimate
        The estimate, also logged with any warnings.
    """

    ledger = read_ledger(ledger_path)
    if ledger.damage is not None:
        _warn(ledger.damage)

    # Approximate the prompt's length by the facts summary plus the user's instructions.
    prompt_chars = sum(len(line) + 1 for line in facts.summary)
    prompt_chars += len(config.instructions or "")
    estimate = estimate_survey(
        config=config,
        page_count=page_count,
        prompt_chars=prompt_chars,
        reused=False,
        spent_usd=ledger.spent_usd,
    )
    for message in estimate.warnings:
        _warn(message)
    _log_estimate(estimate)
    return estimate


def _fixed_decision(allowed: bool) -> OverMaxCostDecision:
    """Return an over-``max_cost`` decision that gives a fixed answer without asking.

    Parameters
    ----------
    allowed
        Whether a run may go over ``max_cost``.

    Returns
    -------
    OverMaxCostDecision
        The decision.
    """

    def decide(warning: MaxCostWarning) -> bool:
        """Return ``allowed``, whatever the warning says."""

        return allowed

    return decide


def _log_estimate(estimate: CostEstimate) -> None:
    """Log the cost estimate, the folder's spend so far and ``max_cost``.

    Parameters
    ----------
    estimate
        The estimate.
    """

    for step in estimate.steps:
        if step.reused:
            logger.info(
                "{name}: reusing the saved output, nothing to spend", name=step.name
            )
        elif step.expected_usd is None or step.max_usd is None:
            logger.info(
                "{name} cost estimate: unknown, no price is known for {model} "
                "(at most {requests} requests)",
                model=step.model,
                name=step.name.capitalize(),
                requests=step.requests_max,
            )
        else:
            logger.info(
                "{name} cost estimate: about {expected}, at most {maximum} "
                "(up to {requests} requests to {model})",
                expected=format_usd(step.expected_usd),
                maximum=format_usd(step.max_usd),
                model=step.model,
                name=step.name.capitalize(),
                requests=step.requests_max,
            )
    limit = "not set" if estimate.max_cost is None else format_usd(estimate.max_cost)
    logger.info(
        "Spent so far in this output folder: {spent}; max_cost: {limit}",
        limit=limit,
        spent=format_usd(estimate.spent_usd),
    )


def _warn(message: str) -> None:
    """Log a warning and issue it as a `pydelity.errors.PydelityWarning`.

    Parameters
    ----------
    message
        The warning's text.
    """

    logger.warning(message)
    warn(message)


async def arun(
    pdf: str | os.PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> None:
    """Run pydelity on a PDF.

    The run validates the settings, opens the PDF, measures it (or reuses the facts
    saved in ``pdf_facts.json`` in the output folder) and checks the cost estimate
    against ``max_cost``. It does not prompt for input.

    Parameters
    ----------
    pdf
        The PDF to process. Overrides a ``pdf`` in ``config``.
    allow_over_max_cost
        Whether to continue, with a warning, when the run could exceed ``max_cost``.
        If false, such a run raises `BudgetExceededError` instead.
    config
        A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a mapping
        of settings.
    **settings
        Settings by name, such as ``model="openai:gpt-6.2-astra"`` or
        ``advanced={"survey": {"effort": "medium"}}``. They override ``config``.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and ``allow_over_max_cost`` is not set.
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    """

    await arun_with_questions(
        pdf,
        config=config,
        confirm=None,
        decide_over_max_cost=_fixed_decision(allow_over_max_cost),
        **settings,
    )


async def arun_with_questions(
    pdf: str | os.PathLike[str] | None = None,
    *,
    config: ConfigSource | None = None,
    confirm: SpendConfirmation | None,
    decide_over_max_cost: OverMaxCostDecision,
    **settings: object,
) -> None:
    """Run pydelity on a PDF, calling the given functions to ask before spending.

    The ``pydelity`` command uses this to ask its questions on the terminal. `arun`
    calls it with a fixed answer instead.

    Parameters
    ----------
    pdf
        The PDF to process. Overrides a ``pdf`` in ``config``.
    config
        A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a mapping
        of settings.
    confirm
        Called with the cost estimate; returns whether to continue. ``None``
        continues without asking.
    decide_over_max_cost
        Called with the warning's details when the run could exceed ``max_cost``;
        returns whether to continue.
    **settings
        Settings by name. They override ``config``.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and the decision is no.
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    SpendDeclinedError
        If ``confirm`` answers no.
    """

    resolved = resolve_config(config=config, pdf=pdf, settings=settings)
    logger.info("Settings OK")
    logger.debug(
        "Settings: {settings}",
        settings=json.dumps(
            resolved.model_dump(mode="json")
            | {"output_folder": str(resolved.output_folder)},
            indent=2,
        ),
    )

    info = await asyncio.to_thread(open_pdf, resolved.pdf)
    logger.info(
        "Opened {name}: {pages}, {size:,} bytes, SHA-256 {sha256}",
        name=info.name,
        pages=f"{info.page_count} page" + ("" if info.page_count == 1 else "s"),
        sha256=info.sha256,
        size=info.bytes,
    )
    output_folder = resolved.output_folder
    output_folder.mkdir(exist_ok=True, parents=True)
    for leftover in remove_stale_temp_files(output_folder):
        logger.debug("Removed {path}, left by an interrupted write", path=leftover)

    facts = await measure_facts(
        output_folder=output_folder, overwrite=resolved.overwrite, pdf=info
    )

    choice = resolved.model_choice
    logger.info(
        "Model: {model_id} from provider {provider}",
        model_id=choice.model_id,
        provider=choice.provider,
    )
    ledger_path = output_folder / LEDGER_FILE_NAME
    estimate = _estimate_cost(
        config=resolved,
        facts=facts,
        ledger_path=ledger_path,
        page_count=info.page_count,
    )
    guard = SpendGuard(
        decide=decide_over_max_cost, ledger_path=ledger_path, max_cost=resolved.max_cost
    )
    await _ask_before_spending(confirm=confirm, estimate=estimate, guard=guard)
    logger.info("Run finished")


def run(
    pdf: str | os.PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> None:
    """Run pydelity on a PDF (the sync version of `arun`).

    Parameters
    ----------
    pdf
        The PDF to process. Overrides a ``pdf`` in ``config``.
    allow_over_max_cost
        Whether to continue, with a warning, when the run could exceed ``max_cost``.
        If false, such a run raises `BudgetExceededError` instead.
    config
        A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a mapping
        of settings.
    **settings
        Settings by name, such as ``model="openai:gpt-6.2-astra"`` or
        ``advanced={"survey": {"effort": "medium"}}``. They override ``config``.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and ``allow_over_max_cost`` is not set.
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    RuntimeError
        If called while an event loop is running, as in Jupyter or async code. Use
        ``await pydelity.arun(...)`` there instead.
    """

    run_sync(
        arun,
        allow_over_max_cost=allow_over_max_cost,
        config=config,
        pdf=pdf,
        **settings,
    )

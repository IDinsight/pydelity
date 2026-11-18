"""The run: open the PDF, prepare the output folder, run the steps, write ``run.json``.

``run.json`` is written when the run starts, with status ``running``, and again when
it ends: ``completed``, ``failed``, ``stopped`` (a ``max_cost`` no or a declined
confirmation) or ``interrupted`` (Ctrl+C, or a cancelled ``arun``). The run writes it
before the error goes on to the caller, so every file in the folder stays valid. The
run then logs a summary: how it ended, what it cost and the review issues.
"""

# Standard Library
import asyncio
import json
import secrets

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from importlib.metadata import version

# Third Party Library
from loguru import logger

# Package Library
from pydelity.config.schemas import Config
from pydelity.costs.budget import (
    OverMaxCostDecision,
    SpendDeclinedError,
    SpendGuard,
    estimate_survey,
    format_usd,
)
from pydelity.costs.ledger import LEDGER_FILE_NAME, Ledger, read_ledger
from pydelity.costs.schemas import CostEstimate
from pydelity.errors import BudgetExceededError
from pydelity.pipeline.schemas import (
    RUN_SCHEMA_VERSION,
    PdfRecord,
    RunCost,
    RunRecord,
    RunResult,
    RunStatus,
    StepRecord,
    StepStatus,
    WarningItem,
)
from pydelity.providers.factory import build_model, output_mode
from pydelity.providers.ledger_model import LedgerContext
from pydelity.providers.profiles import PdfTransport
from pydelity.surveying.facts import FACTS_FILE_NAME, measure_facts
from pydelity.surveying.prompts import PROMPT_VERSION, survey_pdf
from pydelity.surveying.schemas import PdfFacts, PdfSurvey, SurveyAnswer
from pydelity.surveying.survey import SURVEY_FILE_NAME, run_survey, saved_survey
from pydelity.utils.coroutines import (
    IssuedWarning,
    collect_warnings,
    run_in_daemon_thread,
    warn,
)
from pydelity.utils.files import load_model, remove_stale_temp_files, write_model_atomic
from pydelity.utils.pdf import PdfInfo, open_pdf

# How many review issues the summary lists; ``run.json`` holds them all.
_REVIEW_ISSUES_LISTED = 10

# The step this cycle's pipeline runs.
_SURVEY_STEP = "survey"

# The run record's file name in the output folder.
RUN_FILE_NAME = "run.json"

# Asks whether to go ahead and spend, given the cost estimate.
type SpendConfirmation = Callable[[CostEstimate], bool]


@dataclass
class _Run:
    """What a run has done so far, for ``run.json``.

    Attributes
    ----------
    config
        The run's settings.
    pdf
        The PDF.
    run_id
        The run's ID.
    started_at
        When the run started (UTC).
    warnings
        The warnings issued so far, in order.
    facts
        The facts, once measured or reused.
    step_started_at
        When the survey step started.
    step_status
        How the survey step ended, once it has.
    step_warnings_from
        The position in ``warnings`` from which warnings belong to the survey step.
    survey
        The survey, once made or reused.
    transport
        How the survey's last request carried the PDF, when one did.
    """

    config: Config
    pdf: PdfInfo
    run_id: str
    started_at: datetime
    warnings: list[IssuedWarning] = field(default_factory=list)
    facts: PdfFacts | None = None
    step_started_at: datetime | None = None
    step_status: StepStatus = "completed"
    step_warnings_from: int = 0
    survey: PdfSurvey | None = None
    transport: PdfTransport | None = None


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


def _cost(*, ledger: Ledger, run_id: str) -> tuple[RunCost, list[int]]:
    """Sum what the run's requests cost, from ``cost.jsonl``.

    Parameters
    ----------
    ledger
        The output folder's ledger.
    run_id
        The run's ID.

    Returns
    -------
    tuple[RunCost, list[int]]
        The run's cost, and the positions of its entries in the ledger.
    """

    mine = [
        position
        for position, entry in enumerate(ledger.entries)
        if entry.run_id == run_id
    ]
    by_step: dict[str, Decimal] = {}
    unpriced = 0
    for position in mine:
        entry = ledger.entries[position]
        if entry.cost_usd is None:
            unpriced += 1
            continue
        by_step[entry.step] = by_step.get(entry.step, Decimal(0)) + entry.cost_usd
    cost = RunCost(
        by_step=by_step,
        output_folder_usd=ledger.spent_usd,
        run_usd=sum(by_step.values(), start=Decimal(0)),
        unpriced_requests=unpriced,
    )
    return cost, mine


def _describe_error(error: BaseException) -> str:
    """Describe an error for ``run.json``: its type and, when it has one, its message.

    Parameters
    ----------
    error
        The error.

    Returns
    -------
    str
        Such as ``ProviderError: anthropic:claude-opus-5-5: ...``.
    """

    text = str(error)
    return f"{type(error).__name__}: {text}" if text else type(error).__name__


def _estimate_cost(
    *, config: Config, page_count: int, prompt_chars: int
) -> CostEstimate:
    """Estimate the survey's cost, counting what the output folder has already spent.

    Parameters
    ----------
    config
        The run's settings.
    page_count
        The PDF's page count.
    prompt_chars
        The survey prompt's length in characters, without the PDF.

    Returns
    -------
    CostEstimate
        The estimate, also logged with any warnings.
    """

    ledger = read_ledger(config.output_folder / LEDGER_FILE_NAME)
    if ledger.damage is not None:
        warn(ledger.damage, code="damaged_output", details={"file": LEDGER_FILE_NAME})

    estimate = estimate_survey(
        config=config,
        page_count=page_count,
        prompt_chars=prompt_chars,
        reused=False,
        spent_usd=ledger.spent_usd,
    )
    for message in estimate.warnings:
        warn(message, code="unpriced_model", details={"model": config.model})
    _log_estimate(estimate)
    return estimate


def _finish(
    run: _Run,
    *,
    error: BaseException | None,
    status: RunStatus,
    step_status: StepStatus,
) -> RunRecord:
    """Write the run's final ``run.json`` and log its summary.

    Parameters
    ----------
    run
        What the run has done.
    error
        Why the run did not complete, if it did not.
    status
        How the run ended.
    step_status
        How the survey step ended.

    Returns
    -------
    RunRecord
        The record, as written.
    """

    record = _record(run, error=error, status=status, step_status=step_status)
    write_model_atomic(model=record, path=run.config.output_folder / RUN_FILE_NAME)
    _log_summary(record, run=run)
    return record


def _log_estimate(estimate: CostEstimate) -> None:
    """Log the cost estimate, the folder's spend so far and ``max_cost``.

    Parameters
    ----------
    estimate
        The estimate.
    """

    for step in estimate.steps:
        if step.expected_usd is None or step.max_usd is None:
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


def _log_summary(record: RunRecord, *, run: _Run) -> None:
    """Log how the run ended, what it cost, its review issues and its files.

    Parameters
    ----------
    record
        The run's final record.
    run
        What the run has done, for the output folder.
    """

    cost = record.cost
    steps = ", ".join(f"{step.name} {step.status}" for step in record.steps)
    by_step = ", ".join(
        f"{name} {format_usd(usd)}" for name, usd in cost.by_step.items()
    )
    unpriced = (
        f", plus {cost.unpriced_requests} requests without a known price"
        if cost.unpriced_requests
        else ""
    )
    issues = len(record.review)
    logger.info(
        "Run {status}: {steps}; cost {run_usd} this run{by_step}{unpriced}, "
        "{folder} in the output folder; {issues} review issue{plural}",
        by_step=f" ({by_step})" if by_step else "",
        folder=format_usd(cost.output_folder_usd),
        issues=issues,
        plural="" if issues == 1 else "s",
        run_usd=format_usd(cost.run_usd),
        status=record.status,
        steps=steps,
        unpriced=unpriced,
    )
    if record.review:
        counts = Counter(issue.check for issue in record.review)
        logger.info(
            "Review issues by check: {counts}",
            counts=", ".join(f"{check} {count}" for check, count in counts.items()),
        )
        for issue in record.review[:_REVIEW_ISSUES_LISTED]:
            page = "-" if issue.page_index is None else str(issue.page_index)
            logger.info(
                "  {step}, page {page}: {message}",
                message=issue.message,
                page=page,
                step=issue.step,
            )
        if issues > _REVIEW_ISSUES_LISTED:
            logger.info(
                "  ...and {more} more in run.json", more=issues - _REVIEW_ISSUES_LISTED
            )
    if record.status == "stopped":
        logger.info(
            "Run pydelity again to continue. The saved files are reused, and the "
            "spend so far still counts toward max_cost."
        )
    files = [RUN_FILE_NAME, *record.steps[0].outputs] if record.steps else []
    logger.info(
        "Output folder: {folder} ({files})",
        files=", ".join(files),
        folder=run.config.output_folder,
    )


def _new_run_id() -> str:
    """Return a new run ID: the UTC time and a random suffix.

    Returns
    -------
    str
        Such as ``20261118T141500Z-9f86d081``.
    """

    return f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{secrets.token_hex(4)}"


def _record(
    run: _Run,
    *,
    error: BaseException | None,
    status: RunStatus,
    step_status: StepStatus | None,
) -> RunRecord:
    """Build the run's record from what it has done.

    Parameters
    ----------
    run
        What the run has done.
    error
        Why the run did not complete, if it did not.
    status
        The run's status.
    step_status
        How the survey step ended, or ``None`` while the run starts.

    Returns
    -------
    RunRecord
        The record for ``run.json``.
    """

    ended_at = None if status == "running" else datetime.now(UTC)
    ledger = read_ledger(run.config.output_folder / LEDGER_FILE_NAME)
    cost, mine = _cost(ledger=ledger, run_id=run.run_id)
    steps = []
    if step_status is not None:
        outputs = [FACTS_FILE_NAME] if run.facts is not None else []
        outputs += [SURVEY_FILE_NAME] if run.survey is not None else []
        steps.append(
            StepRecord(
                cost_usd=cost.by_step.get(_SURVEY_STEP, Decimal(0)),
                ended_at=ended_at,
                error=None if error is None else _describe_error(error),
                name=_SURVEY_STEP,
                outputs=outputs,
                pdf_transport=run.transport,
                requests=sum(1 for p in mine if ledger.entries[p].step == _SURVEY_STEP),
                started_at=run.step_started_at or run.started_at,
                status=step_status,
            )
        )
    warnings = [
        WarningItem(
            code=issued.code,
            details=issued.details,
            message=issued.message,
            step=_SURVEY_STEP if position >= run.step_warnings_from else None,
        )
        for position, issued in enumerate(run.warnings)
    ]
    return RunRecord(
        cost=cost,
        ended_at=ended_at,
        error=None if error is None else _describe_error(error),
        pdf=PdfRecord(
            bytes=run.pdf.bytes,
            page_count=run.pdf.page_count,
            path=str(run.pdf.path),
            sha256=run.pdf.sha256,
        ),
        pydelity_version=version("pydelity"),
        review=[] if run.survey is None else run.survey.issues,
        run_id=run.run_id,
        schema_version=RUN_SCHEMA_VERSION,
        settings=run.config.model_dump(mode="json"),
        started_at=run.started_at,
        status=status,
        steps=steps,
        warnings=warnings,
    )


async def _survey(
    run: _Run,
    *,
    confirm: SpendConfirmation | None,
    decide_over_max_cost: OverMaxCostDecision,
) -> None:
    """Run the survey step: measure the PDF, then reuse or make the survey.

    A new survey first checks the API key and the cost estimate, and asks before
    spending.

    Parameters
    ----------
    run
        The run, which the step updates.
    confirm
        Called with the cost estimate; returns whether to continue. ``None``
        continues without asking.
    decide_over_max_cost
        Called with the warning's details when the run could exceed ``max_cost``;
        returns whether to continue.
    """

    config = run.config
    run.step_started_at = datetime.now(UTC)
    run.facts = await measure_facts(
        output_folder=config.output_folder, overwrite=config.overwrite, pdf=run.pdf
    )
    run.survey = saved_survey(
        config=config, facts=run.facts, output_folder=config.output_folder
    )
    if run.survey is not None:
        run.step_status = "reused"
        return

    ledger_path = config.output_folder / LEDGER_FILE_NAME
    guard = SpendGuard(
        decide=decide_over_max_cost, ledger_path=ledger_path, max_cost=config.max_cost
    )
    survey_settings = config.advanced.survey
    model = build_model(
        config=config,
        context=LedgerContext(
            guard=guard,
            ledger_path=ledger_path,
            pdf=run.pdf,
            run_id=run.run_id,
            step=_SURVEY_STEP,
        ),
        effort=survey_settings.effort,
        max_output_tokens=survey_settings.max_output_tokens,
        request_timeout_seconds=survey_settings.request_timeout_seconds,
    )
    logger.info(
        "Model ready: {model_id} from {provider}, effort {effort}, {mode} structured "
        "output",
        effort=survey_settings.effort,
        mode=output_mode(model),
        model_id=config.model_choice.model_id,
        provider=config.model_choice.provider,
    )

    prompts = survey_pdf(
        facts_summary=run.facts.summary,
        instructions=config.instructions,
        languages=config.languages,
        page_count=run.pdf.page_count,
    )
    logger.debug(
        "Survey instructions (prompt version {version}):\n{instructions}",
        instructions=prompts.system_message,
        version=PROMPT_VERSION,
    )
    logger.debug("Survey text sent with the PDF:\n{text}", text=prompts.user_message)
    # The prompt is the two messages and the answer's JSON schema.
    schema = json.dumps(SurveyAnswer.model_json_schema())
    prompt_chars = len(prompts.system_message) + len(prompts.user_message)
    estimate = _estimate_cost(
        config=config,
        page_count=run.pdf.page_count,
        prompt_chars=prompt_chars + len(schema),
    )
    await _ask_before_spending(confirm=confirm, estimate=estimate, guard=guard)
    run.survey, run.transport = await run_survey(
        config=config,
        facts=run.facts,
        model=model,
        output_folder=config.output_folder,
        pdf=run.pdf,
    )


def _warn_other_pdf(run: _Run) -> None:
    """Warn when the output folder holds results for another PDF.

    Parameters
    ----------
    run
        The run, for the output folder and the PDF's SHA-256.
    """

    folder = run.config.output_folder
    others = {}
    record = load_model(model_type=RunRecord, path=folder / RUN_FILE_NAME).model
    if record is not None and record.pdf.sha256 != run.pdf.sha256:
        others[RUN_FILE_NAME] = record.pdf.sha256
    facts = load_model(model_type=PdfFacts, path=folder / FACTS_FILE_NAME).model
    if facts is not None and facts.pdf.sha256 != run.pdf.sha256:
        others[FACTS_FILE_NAME] = facts.pdf.sha256
    if others:
        warn(
            f"{folder} holds {' and '.join(others)} for another PDF. This run "
            "replaces them, and the folder's earlier spend still counts toward "
            "max_cost.",
            code="other_pdf_in_folder",
            details={"files": others},
        )


async def run_pipeline(
    *,
    config: Config,
    confirm: SpendConfirmation | None,
    decide_over_max_cost: OverMaxCostDecision,
) -> RunResult:
    """Run the pipeline on the PDF and record the run in ``run.json``.

    The PDF is opened before anything is written. Then the output folder is
    prepared: created, cleared of temporary files left by interrupted writes, and
    checked for results of another PDF.

    Parameters
    ----------
    config
        The run's settings, already checked.
    confirm
        Called with the cost estimate; returns whether to continue. ``None``
        continues without asking.
    decide_over_max_cost
        Called with the warning's details when the run could exceed ``max_cost``;
        returns whether to continue.

    Returns
    -------
    RunResult
        The run's record, facts, survey and the folder's ledger.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and the decision is no.
    MissingApiKeyError
        If the selected provider's API key is not set.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    ProviderError
        If the provider rejects the upload for an invalid API key or as too large, or
        a request fails after the provider retries.
    SpendDeclinedError
        If ``confirm`` answers no.
    SurveyError
        If the model refuses, runs out of output tokens, or never gives an answer that
        matches the survey's answer format.
    """

    pdf = await asyncio.to_thread(open_pdf, config.pdf)
    logger.info(
        "Opened {name}: {pages}, {size:,} bytes, SHA-256 {sha256}",
        name=pdf.name,
        pages=f"{pdf.page_count} page" + ("" if pdf.page_count == 1 else "s"),
        sha256=pdf.sha256,
        size=pdf.bytes,
    )
    folder = config.output_folder
    folder.mkdir(exist_ok=True, parents=True)
    for leftover in remove_stale_temp_files(folder):
        logger.debug("Removed {path}, left by an interrupted write", path=leftover)

    run = _Run(
        config=config, pdf=pdf, run_id=_new_run_id(), started_at=datetime.now(UTC)
    )
    with collect_warnings() as collected:
        run.warnings = collected
        _warn_other_pdf(run)
        run.step_warnings_from = len(collected)
        write_model_atomic(
            model=_record(run, error=None, status="running", step_status=None),
            path=folder / RUN_FILE_NAME,
        )
        try:
            await _survey(
                run, confirm=confirm, decide_over_max_cost=decide_over_max_cost
            )
        except (BudgetExceededError, SpendDeclinedError) as error:
            _finish(run, error=error, status="stopped", step_status="stopped")
            raise
        except (KeyboardInterrupt, asyncio.CancelledError) as error:
            _finish(run, error=error, status="interrupted", step_status="stopped")
            raise
        except Exception as error:
            _finish(run, error=error, status="failed", step_status="failed")
            raise
        record = _finish(
            run, error=None, status="completed", step_status=run.step_status
        )

    return RunResult(
        facts=run.facts,
        ledger=read_ledger(folder / LEDGER_FILE_NAME).entries,
        output_dir=folder,
        record=record,
        survey=run.survey,
    )

"""The run: open the PDF, prepare the output folder, run the steps, write ``run.json``.

`run_pipeline` is the whole run: the survey, then page extraction. With ``pause`` on,
a run that made a new survey stops after it, so the survey can be checked before the
pages are paid for. `run_measure`, `run_estimate`, `run_survey_step` and
`run_extraction_step` do parts of it for the Python API's ``measure``, ``estimate``,
``survey`` and ``extract``, which write no ``run.json`` and no report and never pause.
`load_run` reads a folder back.

The cost estimate, the question before spending, the ``max_cost`` check on it and the
API-key checks cover every step the run will perform, once, before its first model
request: in the survey step when the survey runs, otherwise in page extraction.

``run.json`` is written when the run starts, with status ``running``, and again when
it ends: ``completed``, ``paused`` (after a new survey), ``failed``, ``stopped`` (a
``max_cost`` no or a declined confirmation) or ``interrupted`` (Ctrl+C, or a
cancelled ``arun``). The run writes it, and then ``report.html``, before the error
goes on to the caller, so every file in the folder stays valid. The run then logs a
summary of how it ended, what it cost and the review issues.
"""

# Standard Library
import asyncio
import json
import secrets

from collections import Counter
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path

# Third Party Library
from loguru import logger
from pydantic import BaseModel

# Package Library
from pydelity.config.loading import read_api_key
from pydelity.config.schemas import Config, ExtractionConfig, SurveyConfig, parse_pages
from pydelity.costs.budget import (
    OverMaxCostDecision,
    SpendDeclinedError,
    SpendGuard,
    estimate_extraction,
    estimate_run,
    estimate_survey,
    format_usd,
)
from pydelity.costs.ledger import LEDGER_FILE_NAME, Ledger, read_ledger
from pydelity.costs.schemas import CostEstimate, StepEstimate
from pydelity.errors import BudgetExceededError, ConfigError, OutputError
from pydelity.extracting.extraction import (
    FIGURES_FOLDER_NAME,
    PAGES_FOLDER_NAME,
    extract_pages,
    page_file_path,
    plan_pages,
    request_sizes,
    request_sizes_before_survey,
)
from pydelity.extracting.llm import StepModel
from pydelity.extracting.schemas import PageFile
from pydelity.pipeline.schemas import (
    PageCounts,
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
from pydelity.providers.ledger_model import LedgerContext, LedgerModel
from pydelity.providers.profiles import ModelChoice, PdfTransport
from pydelity.report.html import REPORT_FILE_NAME, ReportInputs, write_report
from pydelity.report.images import REPORT_FOLDER_NAME, render_pages
from pydelity.review import ReviewIssue
from pydelity.schema_versions import (
    FACTS_SCHEMA_VERSION,
    PAGE_SCHEMA_VERSION,
    RUN_SCHEMA_VERSION,
    SURVEY_SCHEMA_VERSION,
)
from pydelity.surveying.facts import FACTS_FILE_NAME, measure_facts
from pydelity.surveying.prompts import PROMPT_VERSION, survey_pdf
from pydelity.surveying.schemas import PdfFacts, PdfSurvey, SurveyAnswer
from pydelity.surveying.survey import (
    SURVEY_FILE_NAME,
    run_survey,
    saved_survey,
    survey_fingerprint,
    survey_inputs,
)
from pydelity.utils.coroutines import (
    IssuedWarning,
    collect_warnings,
    run_in_daemon_thread,
    running_step,
    warn,
)
from pydelity.utils.files import load_model, remove_stale_temp_files, write_model_atomic
from pydelity.utils.pdf import PdfInfo, open_pdf

# Page extraction's name in ``run.json``, ``cost.jsonl`` and the review list.
_EXTRACTION_STEP = "extraction"

# How many review issues the summary lists; ``run.json`` holds them all.
_REVIEW_ISSUES_LISTED = 10

# The survey step's name in ``run.json``, ``cost.jsonl`` and the review list.
_SURVEY_STEP = "survey"

# The run record's file name in the output folder.
RUN_FILE_NAME = "run.json"

# The loguru ``extra`` key that marks the cost estimate and the end-of-run summary,
# which the ``pydelity`` command shows even when it hides other progress.
SUMMARY_LOG_KEY = "summary"

# Asks whether to go ahead and spend, given the cost estimate.
type SpendConfirmation = Callable[[CostEstimate], bool]


@dataclass
class _Step:
    """What one step of a run has done, for ``run.json``.

    Attributes
    ----------
    name
        The step, such as ``survey``.
    started_at
        When the step started (UTC).
    ended_at
        When the step ended (UTC), once it has.
    error
        Why the step failed or stopped, if it did.
    outputs
        The files and folders the step wrote or reused, by name.
    pages
        How many pages the step selected, extracted and reused, for a step that
        works page by page.
    status
        How the step ended, or ``None`` while it runs.
    transport
        How the step's last request carried the PDF, when one did.
    """

    name: str
    started_at: datetime
    ended_at: datetime | None = None
    error: str | None = None
    outputs: list[str] = field(default_factory=list)
    pages: PageCounts | None = None
    status: StepStatus | None = None
    transport: PdfTransport | None = None

    def end(self, status: StepStatus, *, error: BaseException | None = None) -> None:
        """Record how the step ended, and when.

        Parameters
        ----------
        status
            How the step ended.
        error
            Why the step failed or stopped, if it did.
        """

        self.ended_at = datetime.now(UTC)
        self.error = None if error is None else _describe_error(error)
        self.status = status

    def record_transport(self, transport: PdfTransport) -> None:
        """Record how the step's requests carry the PDF, as soon as it is attached.

        Parameters
        ----------
        transport
            ``upload`` or ``request``.
        """

        self.transport = transport


@dataclass
class _Run:
    """What a run has done so far, for ``run.json``.

    Attributes
    ----------
    config
        The run's settings.
    guard
        The run's ``max_cost`` guard, which every step's requests share, so the run
        asks for a decision at most once.
    pdf
        The PDF.
    run_id
        The run's ID.
    started_at
        When the run started (UTC).
    warnings
        The warnings issued so far, in order, each with the step that issued it.
    facts
        The facts, once measured or reused.
    pages
        The selected pages' page files by page index, reused or written so far.
    selected
        The selected pages' indexes, in order.
    steps
        The steps that started, in the order they started.
    survey
        The survey, once made or reused.
    """

    config: Config
    guard: SpendGuard
    pdf: PdfInfo
    run_id: str
    started_at: datetime
    warnings: list[IssuedWarning] = field(default_factory=list)
    facts: PdfFacts | None = None
    pages: dict[int, PageFile] = field(default_factory=dict)
    selected: list[int] = field(default_factory=list)
    steps: list[_Step] = field(default_factory=list)
    survey: PdfSurvey | None = None


async def _ask_before_spending(
    *, confirm: SpendConfirmation | None, estimate: CostEstimate, guard: SpendGuard
) -> None:
    """Check the estimate against ``max_cost`` and ask whether to continue.

    If the expected cost would take the folder over ``max_cost``, only the guard's
    over-``max_cost`` question is asked. Otherwise ``confirm`` is called, if given.

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
        await guard.check(check="plan", upper_bound_usd=estimate.expected_usd)
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


def _estimate_cost(*, config: Config, steps: list[StepEstimate]) -> CostEstimate:
    """Add up the steps' estimates, counting what the output folder has already spent.

    Parameters
    ----------
    config
        The run's settings.
    steps
        The estimate of each step the run will perform, in order.

    Returns
    -------
    CostEstimate
        The estimate, also logged with any warnings.
    """

    ledger = read_ledger(config.output_folder / LEDGER_FILE_NAME)
    if ledger.damage is not None:
        warn(ledger.damage, code="damaged_output", details={"file": LEDGER_FILE_NAME})

    estimate = estimate_run(config=config, spent_usd=ledger.spent_usd, steps=steps)
    # One warning per model with no known price, in step order.
    unpriced = dict.fromkeys(
        step.model for step in steps if not step.reused and step.expected_usd is None
    )
    for model, message in zip(unpriced, estimate.warnings, strict=True):
        warn(message, code="unpriced_model", details={"model": model})
    _log_estimate(estimate)
    return estimate


async def _extraction(
    run: _Run, *, confirm: SpendConfirmation | None, estimate: bool
) -> None:
    """Run page extraction: reuse page files, or extract the selected pages.

    The step is added to ``run.steps`` when it starts and ended when every page file
    is reused or written; a step that raises is ended by the caller. Its page counts
    and ``run.pages`` follow each page written, so they stay right when a page
    fails.

    Parameters
    ----------
    run
        The run, which the step updates. Its survey is set.
    confirm
        Called with the cost estimate; returns whether to continue. ``None``
        continues without asking.
    estimate
        Whether the cost estimate, the question and the ``max_cost`` check happen
        here, because the survey was reused; otherwise the survey step made them.
    """

    config, survey = run.config, run.survey
    if survey is None:
        raise RuntimeError("page extraction needs the survey")
    step = _Step(
        name=_EXTRACTION_STEP,
        outputs=[f"{PAGES_FOLDER_NAME}/", f"{FIGURES_FOLDER_NAME}/"],
        started_at=datetime.now(UTC),
    )
    run.steps.append(step)
    with running_step(_EXTRACTION_STEP):
        plan = plan_pages(
            config=config,
            output_folder=config.output_folder,
            page_indexes=run.selected,
            survey=survey,
        )
        run.pages = {
            page.page_index: page.saved for page in plan if page.saved is not None
        }
        to_extract = [page for page in plan if page.saved is None]
        counts = PageCounts(
            extracted=0, reused=len(plan) - len(to_extract), selected=len(plan)
        )
        step.pages = counts
        if not to_extract:
            step.end("reused")
            return

        def written(page_file: PageFile) -> None:
            """Count a page file once it is written."""

            run.pages[page_file.page_index] = page_file
            counts.extracted += 1

        settings = config.advanced.extraction
        # Page requests carry an image of the page, never the PDF.
        async with _step_model(
            choice=config.extraction_model,
            pdf=None,
            run=run,
            step=_EXTRACTION_STEP,
            step_settings=settings,
        ) as model:
            if estimate:
                cost = _estimate_cost(
                    config=config,
                    steps=[
                        estimate_extraction(
                            config=config,
                            pages=request_sizes(to_extract, survey=survey),
                        )
                    ],
                )
                await _ask_before_spending(
                    confirm=confirm, estimate=cost, guard=run.guard
                )
            await extract_pages(
                model=StepModel(
                    choice=config.extraction_model, model=model, settings=settings
                ),
                on_written=written,
                output_folder=config.output_folder,
                pages=plan,
                pdf_path=run.pdf.path,
            )
    step.end("completed")


async def _finish(
    run: _Run, *, error: BaseException | None, status: RunStatus
) -> RunRecord:
    """Write the run's final ``run.json`` and the report, and log the summary.

    A step still running when the run ends is recorded as ``failed`` when the run
    failed, and as ``stopped`` otherwise.

    Parameters
    ----------
    run
        What the run has done.
    error
        Why the run did not complete, if it did not.
    status
        How the run ended.

    Returns
    -------
    RunRecord
        The record, as written.
    """

    for step in run.steps:
        if step.status is None:
            step.end("failed" if status == "failed" else "stopped", error=error)
    record = _record(run, error=error, status=status)
    write_model_atomic(model=record, path=run.config.output_folder / RUN_FILE_NAME)
    report = await _write_report(record, run=run)
    _log_summary(record, report=report, run=run)
    return record


def _load_pages(folder: Path) -> list[PageFile]:
    """Read every page file in an output folder for `load_run`.

    Parameters
    ----------
    folder
        The output folder.

    Returns
    -------
    list[PageFile]
        The page files in ``pages/``, in page order; empty when there are none.

    Raises
    ------
    OutputError
        If a page file is not valid JSON, does not match its schema, has another
        major schema version, or names a figure image that is missing.
    """

    indexes = sorted(
        int(path.stem)
        for path in (folder / PAGES_FOLDER_NAME).glob("*.json")
        if path.stem.isdigit()
    )
    pages = []
    for index in indexes:
        path = page_file_path(output_folder=folder, page_index=index)
        page = _load_part(model_type=PageFile, path=path, version=PAGE_SCHEMA_VERSION)
        if page is None:
            continue
        for item in page.items:
            if item.figure is not None and not (folder / item.figure.crop).is_file():
                raise OutputError(
                    f"{PAGES_FOLDER_NAME}/{path.name} names the figure image "
                    f"{item.figure.crop}, which is missing; it cannot be read back"
                )
        pages.append(page)
    return pages


def _load_part[ModelT: BaseModel](
    *, model_type: type[ModelT], path: Path, version: str
) -> ModelT | None:
    """Read one output file for `load_run`, raising instead of reporting damage.

    Parameters
    ----------
    model_type
        The model the file must validate against. It has a ``schema_version``.
    path
        The file.
    version
        The schema version this pydelity writes; the file's major version must match.

    Returns
    -------
    ModelT | None
        The file's contents, or ``None`` when it does not exist.

    Raises
    ------
    OutputError
        If the file is not valid JSON, does not match its schema, or has another
        major schema version.
    """

    loaded = load_model(model_type=model_type, path=path)
    if loaded.damage is not None:
        raise OutputError(f"{loaded.damage}; it cannot be read back")
    found = getattr(loaded.model, "schema_version", None)
    major = version.split(".", maxsplit=1)[0]
    if found is not None and found.split(".", maxsplit=1)[0] != major:
        raise OutputError(
            f"{path.name} has schema version {found}, but this pydelity reads only "
            f"version {major}.x"
        )
    return loaded.model


def _log_estimate(estimate: CostEstimate) -> None:
    """Log the cost estimate, the folder's spend so far and ``max_cost``.

    The lines are marked with `SUMMARY_LOG_KEY`.

    Parameters
    ----------
    estimate
        The estimate.
    """

    summary = logger.bind(**{SUMMARY_LOG_KEY: True})
    for step in estimate.steps:
        if step.reused:
            summary.info(
                "{name}: the saved output would be reused, nothing to spend",
                name=step.name.capitalize(),
            )
        elif step.expected_usd is None or step.max_usd is None:
            summary.info(
                "{name} cost estimate: unknown, no price is known for {model} "
                "(at most {requests} requests)",
                model=step.model,
                name=step.name.capitalize(),
                requests=step.requests_max,
            )
        else:
            pages = "" if step.pages is None else f"{_pages_text(step.pages)}, "
            summary.info(
                "{name} cost estimate: about {expected}, at most {maximum} "
                "({pages}up to {requests} requests to {model})",
                expected=format_usd(step.expected_usd),
                maximum=format_usd(step.max_usd),
                model=step.model,
                name=step.name.capitalize(),
                pages=pages,
                requests=step.requests_max,
            )
    limit = "not set" if estimate.max_cost is None else format_usd(estimate.max_cost)
    summary.info(
        "Spent so far in this output folder: {spent}; max_cost: {limit}",
        limit=limit,
        spent=format_usd(estimate.spent_usd),
    )


def _log_summary(record: RunRecord, *, report: Path | None, run: _Run) -> None:
    """Log how the run ended, what it cost, its review issues and its files.

    The lines are marked with `SUMMARY_LOG_KEY`.

    Parameters
    ----------
    record
        The run's final record.
    report
        The report, if it was written.
    run
        What the run has done, for the output folder.
    """

    summary = logger.bind(**{SUMMARY_LOG_KEY: True})
    cost = record.cost
    steps = ", ".join(_step_summary(step) for step in record.steps)
    by_step = ", ".join(
        f"{name} {format_usd(usd)}" for name, usd in cost.by_step.items()
    )
    count = cost.unpriced_requests
    unpriced = (
        f", plus {count} request{'' if count == 1 else 's'} without a known price"
        if count
        else ""
    )
    issues = len(record.review)
    summary.info(
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
        summary.info(
            "Review issues by check: {counts}",
            counts=", ".join(f"{check} {count}" for check, count in counts.items()),
        )
        for issue in record.review[:_REVIEW_ISSUES_LISTED]:
            where = [issue.step]
            if issue.page_index is not None:
                where.append(f"page {issue.page_index + 1}")
            if issue.item_id is not None:
                where.append(f"item {issue.item_id}")
            summary.info(
                "  {where}: {message}", message=issue.message, where=", ".join(where)
            )
        if issues > _REVIEW_ISSUES_LISTED:
            summary.info(
                "  ...and {more} more in run.json", more=issues - _REVIEW_ISSUES_LISTED
            )
    if record.status == "stopped":
        summary.info(
            "Run pydelity again to continue. The saved files are reused, and the "
            "spend so far still counts toward max_cost."
        )
    if record.status == "paused":
        summary.info(
            "Paused after the new survey. Check {survey} and {report}, then run "
            "pydelity again to extract the pages, or pass --no-pause (pause=False in "
            "Python) to run every step at once.",
            report=REPORT_FILE_NAME,
            survey=SURVEY_FILE_NAME,
        )
        if run.config.overwrite:
            summary.info(
                "Leave --overwrite off next time, or the survey runs again; "
                "--overwrite --no-pause redoes every step in one run."
            )
    outputs = [name for step in record.steps for name in step.outputs]
    files = [RUN_FILE_NAME, *dict.fromkeys(outputs)]
    if report is not None:
        files.append(report.name)
    summary.info(
        "Output folder: {folder} ({files})",
        files=", ".join(files),
        folder=run.config.output_folder,
    )


def _new_run(
    *,
    config: Config,
    decide_over_max_cost: OverMaxCostDecision,
    pdf: PdfInfo,
    selected: list[int],
) -> _Run:
    """Start a run's record, with a new run ID and its ``max_cost`` guard.

    Parameters
    ----------
    config
        The run's settings.
    decide_over_max_cost
        Called with the warning's details when the run could exceed ``max_cost``;
        returns whether to continue.
    pdf
        The opened PDF.
    selected
        The selected pages' indexes.

    Returns
    -------
    _Run
        The run, with nothing done yet. Its ID is the UTC time and a random suffix,
        such as ``20261118T141500Z-9f86d081``.
    """

    return _Run(
        config=config,
        guard=SpendGuard(
            decide=decide_over_max_cost,
            ledger_path=config.output_folder / LEDGER_FILE_NAME,
            max_cost=config.max_cost,
        ),
        pdf=pdf,
        run_id=f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{secrets.token_hex(4)}",
        selected=selected,
        started_at=datetime.now(UTC),
    )


async def _open(config: Config) -> PdfInfo:
    """Open the PDF off the event loop and log its size, pages and SHA-256.

    Parameters
    ----------
    config
        The run's settings, for the PDF's path.

    Returns
    -------
    PdfInfo
        The opened PDF.

    Raises
    ------
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    """

    pdf = await asyncio.to_thread(open_pdf, config.pdf)
    logger.info(
        "Opened {name}: {pages}, {size:,} bytes, SHA-256 {sha256}",
        name=pdf.name,
        pages=f"{pdf.page_count} page" + ("" if pdf.page_count == 1 else "s"),
        sha256=pdf.sha256,
        size=pdf.bytes,
    )
    return pdf


def _pages_text(count: int) -> str:
    """Write a number of pages.

    Parameters
    ----------
    count
        How many pages.

    Returns
    -------
    str
        Such as ``1 page`` or ``8 pages``.
    """

    return f"{count} page{'' if count == 1 else 's'}"


def _prepare_folder(folder: Path) -> None:
    """Create the output folder and remove files left by interrupted writes.

    Temporary files are removed from the output folder and from the report's page
    images; page extraction clears its own folders when it starts.

    Parameters
    ----------
    folder
        The output folder.
    """

    folder.mkdir(exist_ok=True, parents=True)
    for place in (folder, folder / REPORT_FOLDER_NAME / "pages"):
        for leftover in remove_stale_temp_files(place):
            logger.debug("Removed {path}, left by an interrupted write", path=leftover)


def _prompt_chars(*, config: Config, facts: PdfFacts) -> int:
    """Measure the survey prompt, logging it in detail, for the cost estimate.

    Parameters
    ----------
    config
        The run's settings, for the user's instructions and languages.
    facts
        The facts, whose summary goes into the prompt.

    Returns
    -------
    int
        The prompt's length in characters: both messages and the answer's JSON
        schema, without the PDF.
    """

    prompts = survey_pdf(
        facts_summary=facts.summary,
        instructions=config.advanced.survey.instructions,
        languages=config.languages,
        page_count=facts.pdf.page_count,
        repeated_lines=facts.facts.repeated_lines,
    )
    logger.debug(
        "Survey instructions (prompt version {version}):\n{instructions}",
        instructions=prompts.system_message,
        version=PROMPT_VERSION,
    )
    logger.debug("Survey text sent with the PDF:\n{text}", text=prompts.user_message)
    schema = json.dumps(SurveyAnswer.model_json_schema())
    return len(prompts.system_message) + len(prompts.user_message) + len(schema)


def _record(run: _Run, *, error: BaseException | None, status: RunStatus) -> RunRecord:
    """Build the run's record from what it has done.

    Parameters
    ----------
    run
        What the run has done.
    error
        Why the run did not complete, if it did not.
    status
        The run's status.

    Returns
    -------
    RunRecord
        The record for ``run.json``, with a record for each step that has ended.
    """

    ended_at = None if status == "running" else datetime.now(UTC)
    ledger = read_ledger(run.config.output_folder / LEDGER_FILE_NAME)
    cost, mine = _cost(ledger=ledger, run_id=run.run_id)
    steps = [
        StepRecord(
            cost_usd=cost.by_step.get(step.name, Decimal(0)),
            ended_at=step.ended_at,
            error=step.error,
            name=step.name,
            outputs=step.outputs,
            pages=step.pages,
            pdf_transport=step.transport,
            requests=sum(1 for p in mine if ledger.entries[p].step == step.name),
            started_at=step.started_at,
            status=step.status,
        )
        for step in run.steps
        if step.status is not None
    ]
    warnings = [
        WarningItem(
            code=issued.code,
            details=issued.details,
            message=issued.message,
            step=issued.step,
        )
        for issued in run.warnings
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
        review=_review(run),
        run_id=run.run_id,
        schema_version=RUN_SCHEMA_VERSION,
        settings=run.config.model_dump(mode="json"),
        started_at=run.started_at,
        status=status,
        steps=steps,
        warnings=warnings,
    )


def _report_files(record: RunRecord, *, run: _Run) -> Path:
    """Render the page images that are missing and write ``report.html``.

    Parameters
    ----------
    record
        The run's final record.
    run
        What the run has done.

    Returns
    -------
    Path
        The report's path.
    """

    manifest = render_pages(
        output_folder=run.config.output_folder,
        pdf_path=run.pdf.path,
        pdf_sha256=run.pdf.sha256,
    )
    return write_report(
        ReportInputs(
            facts=run.facts,
            manifest=manifest,
            output_folder=run.config.output_folder,
            pages=[run.pages[index] for index in run.selected if index in run.pages],
            record=record,
            survey=run.survey,
        )
    )


def _reusable_survey(*, config: Config, facts: PdfFacts) -> PdfSurvey | None:
    """Return the saved survey if the run would reuse it, without logging it.

    Parameters
    ----------
    config
        The run's settings.
    facts
        The facts the survey would use.

    Returns
    -------
    PdfSurvey | None
        The saved survey when ``pdf_survey.json`` is valid, matches the inputs and
        ``overwrite`` is not set; otherwise ``None``.
    """

    path = config.output_folder / SURVEY_FILE_NAME
    saved = load_model(model_type=PdfSurvey, path=path).model
    expected = survey_fingerprint(survey_inputs(config=config, facts=facts))
    if saved is None or saved.fingerprint != expected or config.overwrite:
        return None
    return saved


def _review(run: _Run) -> list[ReviewIssue]:
    """List the run's review issues: the survey's, then each selected page's.

    Parameters
    ----------
    run
        What the run has done.

    Returns
    -------
    list[ReviewIssue]
        The survey's issues, then the issues of each selected page that has a page
        file, in page order.
    """

    issues = [] if run.survey is None else list(run.survey.issues)
    for page_index in sorted(run.pages):
        issues += run.pages[page_index].issues
    return issues


def _selected_pages(*, config: Config, pdf: PdfInfo) -> list[int]:
    """Turn the ``pages`` setting into the indexes of the selected pages.

    Parameters
    ----------
    config
        The run's settings.
    pdf
        The opened PDF, for its page count.

    Returns
    -------
    list[int]
        The selected pages' 0-based indexes, in order; every page when ``pages`` is
        unset.

    Raises
    ------
    ConfigError
        If ``pages`` names a page past the PDF's last page.
    """

    count = pdf.page_count
    if config.pages is None:
        return list(range(count))

    ranges = parse_pages(config.pages)
    if ranges[-1][1] > count:
        noun = "page" if count == 1 else "pages"
        raise ConfigError(
            f"1 invalid setting:\n- pages: {config.pages} goes past the last page; "
            f"{pdf.name} has {count} {noun}"
        )
    return [index for first, last in ranges for index in range(first - 1, last)]


@asynccontextmanager
async def _step_model(
    *,
    choice: ModelChoice,
    pdf: PdfInfo | None,
    run: _Run,
    step: str,
    step_settings: ExtractionConfig | SurveyConfig,
) -> AsyncGenerator[LedgerModel]:
    """Build a step's model on the run's guard and ledger, and log it.

    Parameters
    ----------
    choice
        The step's model.
    pdf
        The PDF the step's requests carry, or ``None`` when they carry none.
    run
        The run.
    step
        The step's name.
    step_settings
        The step's settings.

    Yields
    ------
    LedgerModel
        The model, until the block ends.
    """

    context = LedgerContext(
        agent=None,
        guard=run.guard,
        ledger_path=run.config.output_folder / LEDGER_FILE_NAME,
        page_index=None,
        pdf=pdf,
        run_id=run.run_id,
        step=step,
    )
    async with build_model(
        choice=choice, config=run.config, context=context, step_settings=step_settings
    ) as model:
        logger.info(
            "Model ready: {model_id} from {provider}, effort {effort}, {mode} "
            "structured output",
            effort=step_settings.effort,
            mode=output_mode(model),
            model_id=choice.model_id,
            provider=choice.provider,
        )
        yield model


def _step_summary(step: StepRecord) -> str:
    """Describe how a step ended, for the summary.

    Parameters
    ----------
    step
        The step's record.

    Returns
    -------
    str
        Such as ``survey reused`` or ``extraction completed (8 pages selected: 6
        extracted, 2 reused)``.
    """

    text = f"{step.name} {step.status}"
    if step.pages is not None:
        counts = step.pages
        text += (
            f" ({_pages_text(counts.selected)} selected: {counts.extracted} "
            f"extracted, {counts.reused} reused)"
        )
    return text


async def _steps(
    run: _Run, *, confirm: SpendConfirmation | None, pause: bool
) -> RunStatus:
    """Run the survey, then page extraction unless the run pauses.

    Parameters
    ----------
    run
        The run, which the steps update.
    confirm
        Called with the cost estimate; returns whether to continue. ``None``
        continues without asking.
    pause
        Whether to stop after a new survey.

    Returns
    -------
    RunStatus
        ``paused`` when the survey is new and ``pause`` is set, otherwise
        ``completed``.
    """

    await _survey(run, confirm=confirm, extraction_follows=not pause)
    new_survey = run.steps[-1].status == "completed"
    if new_survey and pause:
        skipped = _Step(name=_EXTRACTION_STEP, started_at=datetime.now(UTC))
        skipped.end("skipped")
        run.steps.append(skipped)
        return "paused"
    await _extraction(run, confirm=confirm, estimate=not new_survey)
    return "completed"


async def _survey(
    run: _Run, *, confirm: SpendConfirmation | None, extraction_follows: bool
) -> PdfSurvey:
    """Run the survey step: measure the PDF, then reuse or make the survey.

    A new survey first checks the API keys and the cost estimate of every step the
    run will perform, and asks before spending. The step is added to ``run.steps``
    when it starts and ended when it reuses or makes the survey; a step that raises
    is ended by the caller.

    Parameters
    ----------
    run
        The run, which the step updates.
    confirm
        Called with the cost estimate; returns whether to continue. ``None``
        continues without asking.
    extraction_follows
        Whether page extraction runs after a new survey in this run, so the
        estimate covers every selected page and page extraction's API key is
        checked before the survey spends anything.

    Returns
    -------
    PdfSurvey
        The survey, reused or new.
    """

    config = run.config
    step = _Step(name=_SURVEY_STEP, started_at=datetime.now(UTC))
    run.steps.append(step)
    with running_step(_SURVEY_STEP):
        run.facts = await measure_facts(
            output_folder=config.output_folder, overwrite=config.overwrite, pdf=run.pdf
        )
        step.outputs.append(FACTS_FILE_NAME)
        run.survey = saved_survey(
            config=config, facts=run.facts, output_folder=config.output_folder
        )
        if run.survey is not None:
            step.outputs.append(SURVEY_FILE_NAME)
            step.end("reused")
            return run.survey

        async with _step_model(
            choice=config.survey_model,
            pdf=run.pdf,
            run=run,
            step=_SURVEY_STEP,
            step_settings=config.advanced.survey,
        ) as model:
            steps = [_survey_estimate(config=config, facts=run.facts, reused=False)]
            if extraction_follows:
                read_api_key(config.extraction_model.provider)
                steps.append(
                    estimate_extraction(
                        config=config,
                        pages=request_sizes_before_survey(
                            facts=run.facts.facts, page_indexes=run.selected
                        ),
                    )
                )
            estimate = _estimate_cost(config=config, steps=steps)
            await _ask_before_spending(
                confirm=confirm, estimate=estimate, guard=run.guard
            )
            run.survey, step.transport = await run_survey(
                config=config,
                facts=run.facts,
                model=model,
                on_attached=step.record_transport,
                pdf=run.pdf,
            )
    step.outputs.append(SURVEY_FILE_NAME)
    step.end("completed")
    return run.survey


def _survey_estimate(*, config: Config, facts: PdfFacts, reused: bool) -> StepEstimate:
    """Estimate the survey, measuring its prompt when it would run.

    Parameters
    ----------
    config
        The run's settings.
    facts
        The facts the survey would use.
    reused
        Whether the saved survey would be reused, so nothing is sent.

    Returns
    -------
    StepEstimate
        The survey's estimate.
    """

    return estimate_survey(
        config=config,
        page_count=facts.pdf.page_count,
        prompt_chars=0 if reused else _prompt_chars(config=config, facts=facts),
        reused=reused,
    )


def _warn_other_pdf(*, folder: Path, sha256: str) -> None:
    """Warn when the output folder holds results for another PDF.

    Parameters
    ----------
    folder
        The output folder.
    sha256
        The SHA-256 of this run's PDF.
    """

    others = {}
    record = load_model(model_type=RunRecord, path=folder / RUN_FILE_NAME).model
    if record is not None and record.pdf.sha256 != sha256:
        others[RUN_FILE_NAME] = record.pdf.sha256
    facts = load_model(model_type=PdfFacts, path=folder / FACTS_FILE_NAME).model
    if facts is not None and facts.pdf.sha256 != sha256:
        others[FACTS_FILE_NAME] = facts.pdf.sha256
    if others:
        warn(
            f"{folder} holds {' and '.join(others)} for another PDF. This run "
            "replaces them, and the folder's earlier spend still counts toward "
            "max_cost.",
            code="other_pdf_in_folder",
            details={"files": others},
        )


async def _write_report(record: RunRecord, *, run: _Run) -> Path | None:
    """Write the report off the event loop, logging an error instead of raising.

    A report that cannot be written does not change how the run ended.

    Parameters
    ----------
    record
        The run's final record.
    run
        What the run has done.

    Returns
    -------
    Path | None
        The report's path, or ``None`` when it could not be written.
    """

    try:
        path = await asyncio.to_thread(_report_files, record, run=run)
    except (OSError, RuntimeError, ValueError) as error:
        logger.error("The report could not be written: {error}", error=error)
        return None
    logger.info("Report written: {path}", path=path)
    return path


def load_run(output_dir: Path) -> RunResult:
    """Read an output folder back as Python objects, with no model call.

    Parameters
    ----------
    output_dir
        The output folder.

    Returns
    -------
    RunResult
        The folder's ``run.json``, ``pdf_facts.json``, ``pdf_survey.json``,
        ``cost.jsonl`` and every page file in ``pages/``, in page order. A part is
        ``None``, or empty, when its files are absent.

    Raises
    ------
    OutputError
        If the folder does not exist, holds none of those files, or holds one that
        is not valid JSON, does not match its schema or has another major schema
        version, or a page file names a figure image that is missing.
    """

    folder = output_dir.resolve()
    if not folder.is_dir():
        raise OutputError(f"{folder} does not exist or is not a folder")

    record = _load_part(
        model_type=RunRecord, path=folder / RUN_FILE_NAME, version=RUN_SCHEMA_VERSION
    )
    facts = _load_part(
        model_type=PdfFacts,
        path=folder / FACTS_FILE_NAME,
        version=FACTS_SCHEMA_VERSION,
    )
    survey = _load_part(
        model_type=PdfSurvey,
        path=folder / SURVEY_FILE_NAME,
        version=SURVEY_SCHEMA_VERSION,
    )
    ledger_path = folder / LEDGER_FILE_NAME
    ledger = read_ledger(ledger_path)
    if ledger.damage is not None:
        warn(ledger.damage, code="damaged_output", details={"file": LEDGER_FILE_NAME})
    if record is None and facts is None and survey is None and not ledger_path.exists():
        raise OutputError(
            f"{folder} holds none of {RUN_FILE_NAME}, {FACTS_FILE_NAME}, "
            f"{SURVEY_FILE_NAME} and {LEDGER_FILE_NAME}"
        )
    return RunResult(
        facts=facts,
        ledger=ledger.entries,
        output_dir=folder,
        pages=_load_pages(folder),
        record=record,
        survey=survey,
    )


async def run_estimate(*, config: Config) -> CostEstimate:
    """Estimate what a run would cost, writing nothing and calling no model.

    The saved facts are used when they match; otherwise the PDF is measured without
    saving the facts. A survey or page file that would be reused costs nothing. When
    the survey would be reused, the estimate covers the selected pages that have no
    page file to reuse. When it would run, it covers every selected page too, unless
    the run would pause after it.

    Parameters
    ----------
    config
        The run's settings, already checked.

    Returns
    -------
    CostEstimate
        The estimate, also logged.

    Raises
    ------
    ConfigError
        If ``pages`` names a page past the PDF's last page.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    """

    pdf = await _open(config)
    selected = _selected_pages(config=config, pdf=pdf)
    facts = await measure_facts(
        output_folder=config.output_folder,
        overwrite=config.overwrite,
        pdf=pdf,
        save=False,
    )
    survey = _reusable_survey(config=config, facts=facts)
    steps = [_survey_estimate(config=config, facts=facts, reused=survey is not None)]
    if survey is not None:
        plan = plan_pages(
            config=config,
            output_folder=config.output_folder,
            page_indexes=selected,
            quiet=True,
            survey=survey,
        )
        to_extract = [page for page in plan if page.saved is None]
        steps.append(
            estimate_extraction(
                config=config, pages=request_sizes(to_extract, survey=survey)
            )
        )
    elif not config.pause:
        steps.append(
            estimate_extraction(
                config=config,
                pages=request_sizes_before_survey(
                    facts=facts.facts, page_indexes=selected
                ),
            )
        )
    return _estimate_cost(config=config, steps=steps)


async def run_extraction_step(
    *, config: Config, decide_over_max_cost: OverMaxCostDecision
) -> list[PageFile]:
    """Extract the selected pages, running or reusing the survey first.

    No ``run.json`` and no report are written, and the run never pauses: the caller
    asked for page extraction. The estimate, the ``max_cost`` check on it and the
    API-key checks cover both steps before the first request, as in a full run.

    Parameters
    ----------
    config
        The run's settings, already checked.
    decide_over_max_cost
        Called with the warning's details when the run could exceed ``max_cost``;
        returns whether to continue.

    Returns
    -------
    list[PageFile]
        The selected pages' page files, reused or new, in page order.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and the decision is no.
    ConfigError
        If ``pages`` names a page past the PDF's last page.
    ExtractionError
        If a model refuses, runs out of output tokens, or never gives a usable
        answer for a page.
    MissingApiKeyError
        If the API key of a step's provider is not set.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    ProviderError
        If a request fails after the provider retries.
    SurveyError
        If the survey's model refuses, runs out of output tokens, or never gives an
        answer that matches the survey's answer format.
    """

    pdf = await _open(config)
    selected = _selected_pages(config=config, pdf=pdf)
    _prepare_folder(config.output_folder)
    _warn_other_pdf(folder=config.output_folder, sha256=pdf.sha256)
    run = _new_run(
        config=config,
        decide_over_max_cost=decide_over_max_cost,
        pdf=pdf,
        selected=selected,
    )
    await _steps(run, confirm=None, pause=False)
    return [run.pages[index] for index in selected]


async def run_measure(*, config: Config) -> PdfFacts:
    """Prepare the output folder, then measure the PDF or reuse its saved facts.

    No API key is needed and no model is called.

    Parameters
    ----------
    config
        The run's settings, already checked.

    Returns
    -------
    PdfFacts
        The facts, as saved in ``pdf_facts.json``.

    Raises
    ------
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    """

    pdf = await _open(config)
    _prepare_folder(config.output_folder)
    _warn_other_pdf(folder=config.output_folder, sha256=pdf.sha256)
    return await measure_facts(
        output_folder=config.output_folder, overwrite=config.overwrite, pdf=pdf
    )


async def run_pipeline(
    *,
    config: Config,
    confirm: SpendConfirmation | None,
    decide_over_max_cost: OverMaxCostDecision,
) -> RunResult:
    """Run the pipeline on the PDF and record the run in ``run.json``.

    The PDF is opened, and ``pages`` checked against it, before anything is written.
    Then the output folder is prepared: created, cleared of temporary files left by
    interrupted writes, and checked for results of another PDF. The survey runs, and
    then page extraction, unless ``pause`` is on and the survey is new; the run then
    ends ``paused``.

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
        The run's record, facts, survey, selected pages' page files and the
        folder's ledger.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and the decision is no.
    ConfigError
        If ``pages`` names a page past the PDF's last page.
    ExtractionError
        If a model refuses, runs out of output tokens, or never gives a usable
        answer for a page.
    MissingApiKeyError
        If the API key of a step's provider is not set.
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

    pdf = await _open(config)
    selected = _selected_pages(config=config, pdf=pdf)
    folder = config.output_folder
    _prepare_folder(folder)

    run = _new_run(
        config=config,
        decide_over_max_cost=decide_over_max_cost,
        pdf=pdf,
        selected=selected,
    )
    with collect_warnings() as collected:
        run.warnings = collected
        _warn_other_pdf(folder=folder, sha256=pdf.sha256)
        write_model_atomic(
            model=_record(run, error=None, status="running"),
            path=folder / RUN_FILE_NAME,
        )
        try:
            status = await _steps(run, confirm=confirm, pause=config.pause)
        except (BudgetExceededError, SpendDeclinedError) as error:
            await _finish(run, error=error, status="stopped")
            raise
        except (KeyboardInterrupt, asyncio.CancelledError) as error:
            await _finish(run, error=error, status="interrupted")
            raise
        except Exception as error:
            await _finish(run, error=error, status="failed")
            raise
        record = await _finish(run, error=None, status=status)

    return RunResult(
        facts=run.facts,
        ledger=read_ledger(folder / LEDGER_FILE_NAME).entries,
        output_dir=folder.resolve(),
        pages=[run.pages[index] for index in sorted(run.pages)],
        record=record,
        survey=run.survey,
    )


async def run_survey_step(
    *, config: Config, decide_over_max_cost: OverMaxCostDecision
) -> PdfSurvey:
    """Run the survey step alone: no ``run.json`` and no report.

    It writes ``pdf_facts.json``, ``pdf_survey.json`` and the ledger lines of its
    requests, as the survey does in a full run.

    Parameters
    ----------
    config
        The run's settings, already checked.
    decide_over_max_cost
        Called with the warning's details when the survey could exceed
        ``max_cost``; returns whether to continue.

    Returns
    -------
    PdfSurvey
        The survey, reused or new.

    Raises
    ------
    BudgetExceededError
        If the survey could go over ``max_cost`` and the decision is no.
    MissingApiKeyError
        If the selected provider's API key is not set.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    ProviderError
        If the provider rejects the upload for an invalid API key or as too large, or
        a request fails after the provider retries.
    SurveyError
        If the model refuses, runs out of output tokens, or never gives an answer that
        matches the survey's answer format.
    """

    pdf = await _open(config)
    _prepare_folder(config.output_folder)
    _warn_other_pdf(folder=config.output_folder, sha256=pdf.sha256)
    run = _new_run(
        config=config, decide_over_max_cost=decide_over_max_cost, pdf=pdf, selected=[]
    )
    return await _survey(run, confirm=None, extraction_follows=False)

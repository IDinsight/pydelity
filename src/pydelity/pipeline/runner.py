"""The run: open the PDF, prepare the output folder, run the steps, write ``run.json``.

`run_pipeline` is the whole run: the survey, page extraction, then page-break
verification. With ``pause`` on, a run stops after a step that wrote new output, a new
survey or new page files, so that output can be checked before the next step is paid
for. Page-break verification runs only when every page of the PDF has a current page
file, and a PDF of one page has no breaks to verify. `run_measure`, `run_estimate`,
`run_survey_step` and `run_extraction_step` do parts of it for the Python API's
``measure``, ``estimate``, ``survey`` and ``extract``, which write no ``run.json`` and
no report and never pause. `load_run` reads a folder back.

The cost estimate, the question before spending, the ``max_cost`` check on it and the
API-key checks cover every step the run will reach, once, before its first model
request: in the survey step when the survey runs, otherwise in page extraction when it
has pages to extract, otherwise in page-break verification.

``run.json`` is written when the run starts, with status ``running``, and again when
it ends: ``completed``, ``paused`` (after a new survey or new page files), ``failed``,
``stopped`` (a ``max_cost`` no or a declined confirmation) or ``interrupted`` (Ctrl+C,
or a canceled ``arun``). The run writes it, and then ``report.html``, before the error
goes on to the caller, so every file in the folder stays valid. The run then logs a
summary of how it ended, what it cost and the review issues.
"""

# Standard Library
import asyncio
import hashlib
import json
import secrets

from collections import Counter
from collections.abc import AsyncGenerator, Callable, Collection, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from importlib.metadata import version
from itertools import groupby
from pathlib import Path

# Third Party Library
from loguru import logger
from pydantic import BaseModel

# Package Library
from pydelity.config.loading import read_api_key
from pydelity.config.schemas import (
    Config,
    ExtractionConfig,
    PageBreaksConfig,
    SurveyConfig,
    parse_pages,
)
from pydelity.costs.budget import (
    OverMaxCostDecision,
    SpendDeclinedError,
    SpendGuard,
    estimate_extraction,
    estimate_page_breaks,
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
    BreakCounts,
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
    BREAK_SCHEMA_VERSION,
    FACTS_SCHEMA_VERSION,
    PAGE_SCHEMA_VERSION,
    RUN_SCHEMA_VERSION,
    SURVEY_SCHEMA_VERSION,
)
from pydelity.surveying.facts import FACTS_FILE_NAME, measure_facts
from pydelity.surveying.prompts import PROMPT_VERSION, survey_pdf, verify_survey
from pydelity.surveying.schemas import (
    PdfFacts,
    PdfSurvey,
    SurveyAnswer,
    SurveyVerdict,
    WritingDirection,
)
from pydelity.surveying.survey import (
    SURVEY_FILE_NAME,
    run_survey,
    saved_survey,
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
from pydelity.verifying.llm import StepModel as BreakStepModel
from pydelity.verifying.schemas import BreakFile
from pydelity.verifying.verification import (
    BREAKS_FOLDER_NAME,
    CurrentPage,
    PlannedBreak,
    current_pages,
    plan_breaks,
    request_sizes_before_pages,
    verify_breaks,
)
from pydelity.verifying.verification import request_sizes as break_request_sizes

# Page-break verification's name in ``run.json``, ``cost.jsonl`` and the review list.
_BREAKS_STEP = "page_breaks"

# Page extraction's name in ``run.json``, ``cost.jsonl`` and the review list.
_EXTRACTION_STEP = "extraction"

# How many review issues the summary lists; ``run.json`` holds them all.
_REVIEW_ISSUES_LISTED = 10

# The survey step's name in ``run.json``, ``cost.jsonl`` and the review list.
_SURVEY_STEP = "survey"

# Each step's title in the cost estimate's lines.
_TITLES = {
    _BREAKS_STEP: "Page-break verification",
    _EXTRACTION_STEP: "Extraction",
    _SURVEY_STEP: "Survey",
}

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
    breaks
        How many breaks the step judged and reused, for page-break verification.
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
    breaks: BreakCounts | None = None
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
    breaks
        The verdict files by the page before each break, reused or written so far.
    extracted
        The pages page extraction wrote a page file for in this run.
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
    breaks: dict[int, BreakFile] = field(default_factory=dict)
    extracted: set[int] = field(default_factory=set)
    facts: PdfFacts | None = None
    pages: dict[int, PageFile] = field(default_factory=dict)
    selected: list[int] = field(default_factory=list)
    steps: list[_Step] = field(default_factory=list)
    survey: PdfSurvey | None = None


def _amount_text(step: StepEstimate) -> str:
    """Write how many pages or breaks a step's estimate covers, for its line.

    Parameters
    ----------
    step
        The step's estimate.

    Returns
    -------
    str
        Such as ``8 pages, `` or ``7 breaks, ``, or nothing for the survey.
    """

    if step.pages is not None:
        return f"{_pages_text(step.pages)}, "
    if step.breaks is not None:
        return f"{_breaks_text(step.breaks)}, "
    return ""


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


def _breaks_ahead(
    *,
    config: Config,
    facts: PdfFacts,
    survey: PdfSurvey | None,
    to_extract: Collection[int],
) -> list[StepEstimate]:
    """Estimate page-break verification in an earlier step, and check its API key.

    Parameters
    ----------
    config
        The run's settings.
    facts
        The facts.
    survey
        The survey, or ``None`` when the survey is about to run.
    to_extract
        The pages (0-based) page extraction will extract in this run.

    Returns
    -------
    list[StepEstimate]
        The step's estimate, or nothing when the run will not reach the step.

    Raises
    ------
    MissingApiKeyError
        If the models would judge a break and the API key of the step's provider is
        not set.
    """

    estimates = _breaks_estimate(
        config=config, facts=facts, survey=survey, to_extract=to_extract
    )
    if any(estimate.breaks for estimate in estimates):
        read_api_key(config.page_breaks_model.provider)
    return estimates


def _breaks_estimate(
    *,
    config: Config,
    facts: PdfFacts,
    survey: PdfSurvey | None,
    to_extract: Collection[int],
) -> list[StepEstimate]:
    """Estimate page-break verification before page extraction runs.

    A break with a page to extract is always judged. A break between two page files
    that are current now is judged unless its verdict file would be reused.

    Parameters
    ----------
    config
        The run's settings.
    facts
        The facts, for the page count and each page's text-layer characters.
    survey
        The survey, or ``None`` when it has not run yet.
    to_extract
        The pages (0-based) page extraction will extract.

    Returns
    -------
    list[StepEstimate]
        The step's estimate, or nothing when the run will not reach the step because
        the PDF has one page or a page would have no current page file.
    """

    count = facts.pdf.page_count
    if count == 1:
        return []
    if survey is None:
        return _breaks_estimate_before_survey(
            config=config, facts=facts, to_extract=to_extract
        )

    extracting = set(to_extract)
    current = current_pages(
        config=config, extracted=(), output_folder=config.output_folder, survey=survey
    )
    if any(index not in current and index not in extracting for index in range(count)):
        return []
    touched = [index for index in range(count - 1) if {index, index + 1} & extracting]
    unchanged = [
        planned
        for index in range(count - 1)
        if not {index, index + 1} & extracting
        for planned in plan_breaks(
            config=config,
            output_folder=config.output_folder,
            pages=[current[index], current[index + 1]],
            quiet=True,
            survey=survey,
        )
    ]
    sizes = break_request_sizes(
        [planned for planned in unchanged if planned.saved is None]
    ) + request_sizes_before_pages(
        config=config, earlier_page_indexes=touched, facts=facts.facts, survey=survey
    )
    return [estimate_page_breaks(breaks=sizes, config=config)]


def _breaks_estimate_before_survey(
    *, config: Config, facts: PdfFacts, to_extract: Collection[int]
) -> list[StepEstimate]:
    """Estimate page-break verification before the survey runs.

    A new survey has page extraction redo the selected pages, so every break is
    counted when each other page has a page file made from this PDF, which page
    extraction might reuse. With ``overwrite`` set, it reuses none.

    Parameters
    ----------
    config
        The run's settings.
    facts
        The facts, for the PDF's hash, the page count and each page's text-layer
        characters.
    to_extract
        The pages (0-based) page extraction will extract: the selected pages.

    Returns
    -------
    list[StepEstimate]
        The step's estimate, or nothing when a page that is not selected would have
        no page file to reuse.
    """

    extracting = set(to_extract)
    others = [index for index in range(facts.pdf.page_count) if index not in extracting]
    if others and (
        config.overwrite
        or not all(
            _has_page_file(
                output_folder=config.output_folder,
                page_index=index,
                sha256=facts.pdf.sha256,
            )
            for index in others
        )
    ):
        return []
    sizes = request_sizes_before_pages(
        config=config,
        earlier_page_indexes=range(facts.pdf.page_count - 1),
        facts=facts.facts,
        survey=None,
    )
    return [estimate_page_breaks(breaks=sizes, config=config)]


def _breaks_text(count: int) -> str:
    """Write a number of breaks between pages.

    Parameters
    ----------
    count
        How many breaks.

    Returns
    -------
    str
        Such as ``1 break`` or ``7 breaks``.
    """

    return f"{count} break{'' if count == 1 else 's'}"


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


def _current_page_files(run: _Run, *, survey: PdfSurvey) -> list[CurrentPage] | None:
    """Read every page's current page file, for page-break verification.

    A PDF of one page gets an info line, and a page without a current page file the
    ``missing_page_files`` warning.

    Parameters
    ----------
    run
        The run, for its settings, the PDF and the pages it extracted.
    survey
        The survey.

    Returns
    -------
    list[CurrentPage] | None
        Every page's current page file, in page order, or ``None`` when the PDF has
        one page or a page has no current page file.
    """

    count = run.pdf.page_count
    if count == 1:
        logger.info("The PDF has one page and so no page breaks to verify")
        return None
    current = current_pages(
        config=run.config,
        extracted=run.extracted,
        output_folder=run.config.output_folder,
        survey=survey,
    )
    missing = [index for index in range(count) if index not in current]
    if missing:
        ranges = _page_ranges(missing)
        subject, them = (
            (f"page {ranges} has", "it")
            if len(missing) == 1
            else (f"pages {ranges} have", "them")
        )
        warn(
            "Page-break verification needs a current page file for every page, and "
            f"{subject} none. Run pydelity again without --pages (pages in the config "
            f"file), or with pages that include {them}, to verify the page breaks.",
            code="missing_page_files",
            details={"page_indexes": missing},
        )
        return None
    return [current[index] for index in range(count)]


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
    run: _Run,
    *,
    breaks_follow: bool,
    confirm: SpendConfirmation | None,
    estimate: bool,
) -> None:
    """Run page extraction: reuse page files, or extract the selected pages.

    The step is added to ``run.steps`` when it starts and ended when every page file
    is reused or written; a step that raises is ended by the caller. Its page counts,
    ``run.pages`` and ``run.extracted`` follow each page written, so they stay right
    when a page fails.

    Parameters
    ----------
    run
        The run, which the step updates. Its facts and survey are set.
    breaks_follow
        Whether page-break verification follows in this run without a pause, so an
        estimate made here covers it and checks its API key.
    confirm
        Called with the cost estimate; returns whether to continue. ``None``
        continues without asking.
    estimate
        Whether the cost estimate, the question and the ``max_cost`` check happen
        here, because the survey was reused; otherwise the survey step made them.
    """

    config, facts, survey = run.config, run.facts, run.survey
    if facts is None or survey is None:
        raise RuntimeError("page extraction needs the facts and the survey")
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

            run.extracted.add(page_file.page_index)
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
                steps = [
                    estimate_extraction(
                        config=config, pages=request_sizes(to_extract, survey=survey)
                    )
                ]
                if breaks_follow:
                    steps += _breaks_ahead(
                        config=config,
                        facts=facts,
                        survey=survey,
                        to_extract={page.page_index for page in to_extract},
                    )
                cost = _estimate_cost(config=config, steps=steps)
                await _ask_before_spending(
                    confirm=confirm, estimate=cost, guard=run.guard
                )
            await extract_pages(
                model=StepModel(
                    choice=config.extraction_model,
                    model=model,
                    settings=settings,
                    verify=config.verify_extraction,
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


def _has_page_file(*, output_folder: Path, page_index: int, sha256: str) -> bool:
    """Tell whether a page has a valid page file made from the PDF.

    Parameters
    ----------
    output_folder
        The output folder.
    page_index
        The page (0-based).
    sha256
        The PDF's SHA-256 hex digest.

    Returns
    -------
    bool
        Whether the page's page file validates and was made from that PDF.
    """

    page_file = load_model(
        model_type=PageFile,
        path=page_file_path(output_folder=output_folder, page_index=page_index),
    ).model
    return page_file is not None and page_file.inputs.pdf_sha256 == sha256


def _issue_place(issue: ReviewIssue) -> str:
    """Name where a review issue is, for the summary.

    A break issue's message already names both pages of the break, so its place
    leaves them out.

    Parameters
    ----------
    issue
        The review issue.

    Returns
    -------
    str
        Such as ``extraction, page 4, item p0003-012`` or ``page_breaks, item
        p0003-012``.
    """

    where = [issue.step]
    if issue.page_index is not None and issue.step != _BREAKS_STEP:
        where.append(f"page {issue.page_index + 1}")
    if issue.item_id is not None:
        where.append(f"item {issue.item_id}")
    return ", ".join(where)


async def _judge_breaks(
    planned: Sequence[PlannedBreak],
    *,
    confirm: SpendConfirmation | None,
    counts: BreakCounts,
    estimate: bool,
    run: _Run,
) -> None:
    """Judge the breaks that have no verdict file to reuse.

    Parameters
    ----------
    planned
        Every break, from `plan_breaks`.
    confirm
        Called with the cost estimate; returns whether to continue. ``None``
        continues without asking.
    counts
        The step's break counts, which follow each verdict file written.
    estimate
        Whether the cost estimate, the question and the ``max_cost`` check happen
        here, because no earlier step of the run made a request.
    run
        The run, whose verdict files follow each one written.
    """

    config = run.config

    def written(break_file: BreakFile) -> None:
        """Count a verdict file once it is written."""

        run.breaks[break_file.earlier_page_index] = break_file
        counts.judged += 1

    settings = config.advanced.page_breaks
    # Page-break requests carry images of two pages, never the PDF.
    async with _step_model(
        choice=config.page_breaks_model,
        pdf=None,
        run=run,
        step=_BREAKS_STEP,
        step_settings=settings,
    ) as model:
        to_judge = [one for one in planned if one.saved is None]
        sizes = break_request_sizes(to_judge) if estimate else []
        if sizes:
            cost = _estimate_cost(
                config=config,
                steps=[estimate_page_breaks(breaks=sizes, config=config)],
            )
            await _ask_before_spending(confirm=confirm, estimate=cost, guard=run.guard)
        await verify_breaks(
            breaks=planned,
            model=BreakStepModel(
                choice=config.page_breaks_model,
                model=model,
                settings=settings,
                verify=config.verify_page_breaks,
            ),
            on_written=written,
            output_folder=config.output_folder,
            pdf_path=run.pdf.path,
        )


def _load_breaks(
    folder: Path, *, pages: Sequence[PageFile], sha256: str | None
) -> list[BreakFile]:
    """Read the verdict files made from the folder's PDF and page files for `load_run`.

    Parameters
    ----------
    folder
        The output folder.
    pages
        The page files `load_run` returns.
    sha256
        The SHA-256 of the PDF in ``pdf_facts.json``, or ``None`` when the folder has
        no facts, so which PDF it holds is unknown.

    Returns
    -------
    list[BreakFile]
        The verdict files in ``page_breaks/`` whose PDF hash is ``sha256`` and whose
        two page-file hashes are those of the files of ``pages``, in break order,
        or none when ``sha256`` is ``None``.

    Raises
    ------
    OutputError
        If a verdict file is not valid JSON, does not match its schema or has another
        major schema version.
    """

    if sha256 is None:
        return []
    hashes = {
        page.page_index: "sha256:"
        + hashlib.sha256(
            page_file_path(
                output_folder=folder, page_index=page.page_index
            ).read_bytes()
        ).hexdigest()
        for page in pages
    }
    breaks = []
    for path in (folder / BREAKS_FOLDER_NAME).glob("*-*.json"):
        earlier, _, later = path.stem.partition("-")
        if not (earlier.isdigit() and later.isdigit()):
            continue
        break_file = _load_part(
            model_type=BreakFile, path=path, version=BREAK_SCHEMA_VERSION
        )
        if break_file is None:
            continue
        inputs = break_file.inputs
        if (
            inputs.pdf_sha256 == sha256
            and hashes.get(inputs.earlier.page_index) == inputs.earlier.page_file_sha256
            and hashes.get(inputs.later.page_index) == inputs.later.page_file_sha256
        ):
            breaks.append(break_file)
    return sorted(breaks, key=lambda break_file: break_file.earlier_page_index)


def _load_pages(folder: Path, *, sha256: str | None) -> list[PageFile]:
    """Read the page files of the folder's PDF for `load_run`.

    A page file made from another PDF is left out before its figure images are
    checked.

    Parameters
    ----------
    folder
        The output folder.
    sha256
        The SHA-256 of the PDF in ``pdf_facts.json``, or ``None`` when the folder has
        no facts, so which PDF it holds is unknown.

    Returns
    -------
    list[PageFile]
        The page files in ``pages/`` made from that PDF, in page order; empty when
        there are none or ``sha256`` is ``None``.

    Raises
    ------
    OutputError
        If a page file is not valid JSON, does not match its schema or has another
        major schema version, or a page file of that PDF names a figure image that
        is missing.
    """

    if sha256 is None:
        return []
    indexes = sorted(
        int(path.stem)
        for path in (folder / PAGES_FOLDER_NAME).glob("*.json")
        if path.stem.isdigit()
    )
    pages = []
    for index in indexes:
        path = page_file_path(output_folder=folder, page_index=index)
        page = _load_part(model_type=PageFile, path=path, version=PAGE_SCHEMA_VERSION)
        if page is None or page.inputs.pdf_sha256 != sha256:
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

    The lines are marked with `SUMMARY_LOG_KEY`. Each step is named by its title, and
    a step whose figures include its verifier's requests is named with it, such as
    ``Extraction with its verifier``.

    Parameters
    ----------
    estimate
        The estimate.
    """

    summary = logger.bind(**{SUMMARY_LOG_KEY: True})
    for step in estimate.steps:
        name = _TITLES[step.name] + (" with its verifier" if step.verifier else "")
        if step.reused:
            summary.info(
                "{name}: the saved output would be reused, nothing to spend", name=name
            )
        elif step.expected_usd is None or step.max_usd is None:
            summary.info(
                "{name} cost estimate: unknown, no price is known for {model} "
                "(at most {requests} requests)",
                model=step.model,
                name=name,
                requests=step.requests_max,
            )
        else:
            summary.info(
                "{name} cost estimate: about {expected}, at most {maximum} "
                "({amount}up to {requests} requests to {model})",
                amount=_amount_text(step),
                expected=format_usd(step.expected_usd),
                maximum=format_usd(step.max_usd),
                model=step.model,
                name=name,
                requests=step.requests_max,
            )
    limit = "not set" if estimate.max_cost is None else format_usd(estimate.max_cost)
    summary.info(
        "Spent so far in this output folder: {spent}; max_cost: {limit}",
        limit=limit,
        spent=format_usd(estimate.spent_usd),
    )


def _log_pause(record: RunRecord, *, overwrite: bool) -> None:
    """Log why the run paused and how to go on.

    The step the run paused after is the last one that was not skipped. The lines
    are marked with `SUMMARY_LOG_KEY`.

    Parameters
    ----------
    record
        The run's final record.
    overwrite
        Whether the run had ``overwrite`` set.
    """

    summary = logger.bind(**{SUMMARY_LOG_KEY: True})
    ran = [step.name for step in record.steps if step.status != "skipped"]
    if ran[-1] == _EXTRACTION_STEP:
        summary.info(
            "Paused after page extraction wrote new page files. Check {pages}/ and "
            "{report}, then run pydelity again to verify the page breaks, or pass "
            "--no-pause (pause=False in Python) to run every step at once.",
            pages=PAGES_FOLDER_NAME,
            report=REPORT_FILE_NAME,
        )
        return
    summary.info(
        "Paused after the new survey. Check {survey} and {report}, then run "
        "pydelity again to extract the pages, or pass --no-pause (pause=False in "
        "Python) to run every step at once.",
        report=REPORT_FILE_NAME,
        survey=SURVEY_FILE_NAME,
    )
    # With overwrite set the survey always runs, so a run that pauses pauses here.
    if overwrite:
        summary.info(
            "Leave --overwrite off next time, or the survey runs again; "
            "--overwrite --no-pause redoes every step in one run."
        )


def _log_review(issues: Sequence[ReviewIssue]) -> None:
    """Log the review issues by check, and the first of them.

    The lines are marked with `SUMMARY_LOG_KEY`.

    Parameters
    ----------
    issues
        The run's review issues, in order.
    """

    if not issues:
        return
    summary = logger.bind(**{SUMMARY_LOG_KEY: True})
    counts = Counter(issue.check for issue in issues)
    summary.info(
        "Review issues by check: {counts}",
        counts=", ".join(f"{check} {count}" for check, count in counts.items()),
    )
    for issue in issues[:_REVIEW_ISSUES_LISTED]:
        summary.info(
            "  {where}: {message}", message=issue.message, where=_issue_place(issue)
        )
    if len(issues) > _REVIEW_ISSUES_LISTED:
        summary.info(
            "  ...and {more} more in run.json",
            more=len(issues) - _REVIEW_ISSUES_LISTED,
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
    _log_review(record.review)
    if record.status == "stopped":
        summary.info(
            "Run pydelity again to continue. The saved files are reused, and the "
            "spend so far still counts toward max_cost."
        )
    if record.status == "paused":
        _log_pause(record, overwrite=run.config.overwrite)
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


async def _page_breaks(
    run: _Run, *, confirm: SpendConfirmation | None, estimate: bool, pause: bool
) -> RunStatus:
    """Run page-break verification: reuse verdict files, or judge the breaks.

    The step is skipped for a PDF of one page, for a page without a current page
    file, and when the run pauses after new page files, in that order. It is added
    to ``run.steps`` when it starts and ended when every verdict file is reused or
    written; a step that raises is ended by the caller. Its break counts and
    ``run.breaks`` follow each verdict file written, so they stay right when a break
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
        here, because no earlier step of the run made a request.
    pause
        Whether the run pauses before judging, because page extraction wrote new
        page files and ``pause`` is on.

    Returns
    -------
    RunStatus
        ``paused`` when the run pauses here, otherwise ``completed``.
    """

    config, survey = run.config, run.survey
    if survey is None:
        raise RuntimeError("page-break verification needs the survey")
    step = _Step(name=_BREAKS_STEP, started_at=datetime.now(UTC))
    run.steps.append(step)
    with running_step(_BREAKS_STEP):
        pages = _current_page_files(run, survey=survey)
        if pages is None or pause:
            step.end("skipped")
            return "completed" if pages is None else "paused"

        step.outputs.append(f"{BREAKS_FOLDER_NAME}/")
        planned = plan_breaks(
            config=config,
            output_folder=config.output_folder,
            pages=pages,
            survey=survey,
        )
        run.breaks = {
            one.earlier_page_index: one.saved
            for one in planned
            if one.saved is not None
        }
        counts = BreakCounts(judged=0, reused=len(run.breaks), total=len(planned))
        step.breaks = counts
        if len(run.breaks) == len(planned):
            step.end("reused")
            return "completed"
        await _judge_breaks(
            planned, confirm=confirm, counts=counts, estimate=estimate, run=run
        )
    step.end("completed")
    return "completed"


def _page_ranges(page_indexes: Sequence[int]) -> str:
    """Write pages as ranges of page numbers.

    Parameters
    ----------
    page_indexes
        The pages (0-based), in increasing order.

    Returns
    -------
    str
        Such as ``1-3, 7, 9-10``.

    Examples
    --------
    >>> _page_ranges([0, 1, 2, 6, 8, 9])
    '1-3, 7, 9-10'
    """

    parts = []
    for _, group in groupby(
        enumerate(page_indexes), key=lambda pair: pair[1] - pair[0]
    ):
        numbers = [index + 1 for _, index in group]
        parts.append(
            str(numbers[0]) if len(numbers) == 1 else f"{numbers[0]}-{numbers[-1]}"
        )
    return ", ".join(parts)


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


def _prompt_chars(*, config: Config, facts: PdfFacts) -> tuple[int, int]:
    """Measure the survey's prompt and its verifier's, for the cost estimate.

    The survey's prompt is logged in detail.

    Parameters
    ----------
    config
        The run's settings, for the user's instructions and languages.
    facts
        The facts, whose summary goes into the prompts.

    Returns
    -------
    tuple[int, int]
        Each prompt's length in characters: its messages and its answer's JSON
        schema, without the PDF. The verifier's leaves out the answer it reviews,
        which the estimate counts as the survey's answer.
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
    empty = SurveyAnswer(
        artifacts=[],
        continuation_notes=[],
        labels=[],
        languages=[],
        non_artifact_lines=[],
        notes=[],
        page_numbering=[],
        regions=[],
        rotation=[],
        start_markers=[],
        writing_direction=WritingDirection(default="ltr", ranges=[]),
    )
    verifier = verify_survey(
        answer=empty,
        differences={},
        failures={},
        instructions=config.advanced.survey.instructions,
        survey_message=prompts.user_message,
    )
    survey_chars = (
        len(prompts.system_message)
        + len(prompts.user_message)
        + len(json.dumps(SurveyAnswer.model_json_schema()))
    )
    verifier_chars = (
        len(verifier.system_message)
        + len(verifier.user_message)
        + len(json.dumps(SurveyVerdict.model_json_schema()))
    )
    return survey_chars, verifier_chars


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
            breaks=step.breaks,
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


def _review(run: _Run) -> list[ReviewIssue]:
    """List the run's review issues: the survey's, each selected page's, each break's.

    Parameters
    ----------
    run
        What the run has done.

    Returns
    -------
    list[ReviewIssue]
        The survey's issues, then the issues of each selected page that has a page
        file, in page order, then those of each break that has a verdict file, in
        break order.
    """

    issues = [] if run.survey is None else list(run.survey.issues)
    for page_index in sorted(run.pages):
        issues += run.pages[page_index].issues
    for page_index in sorted(run.breaks):
        issues += run.breaks[page_index].issues
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


def _skip_steps(run: _Run, names: Sequence[str]) -> None:
    """Record steps the run will not reach as skipped.

    Parameters
    ----------
    run
        The run.
    names
        The steps, in order.
    """

    for name in names:
        step = _Step(name=name, started_at=datetime.now(UTC))
        step.end("skipped")
        run.steps.append(step)


@asynccontextmanager
async def _step_model(
    *,
    choice: ModelChoice,
    pdf: PdfInfo | None,
    run: _Run,
    step: str,
    step_settings: ExtractionConfig | PageBreaksConfig | SurveyConfig,
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
        Such as ``survey reused``, ``extraction completed (8 pages selected: 6
        extracted, 2 reused)`` or ``page_breaks completed (7 breaks: 5 judged, 2
        reused)``.
    """

    text = f"{step.name} {step.status}"
    if step.pages is not None:
        pages = step.pages
        text += (
            f" ({_pages_text(pages.selected)} selected: {pages.extracted} "
            f"extracted, {pages.reused} reused)"
        )
    if step.breaks is not None:
        breaks = step.breaks
        text += (
            f" ({_breaks_text(breaks.total)}: {breaks.judged} judged, "
            f"{breaks.reused} reused)"
        )
    return text


async def _steps(
    run: _Run, *, confirm: SpendConfirmation | None, page_breaks: bool, pause: bool
) -> RunStatus:
    """Run the survey, page extraction and page-break verification, or pause.

    The step that makes the run's first request makes the cost estimate first: the
    survey when it runs, otherwise page extraction when it has pages to extract,
    otherwise page-break verification. Each step the run does not reach after a
    pause is recorded as skipped.

    Parameters
    ----------
    run
        The run, which the steps update.
    confirm
        Called with the cost estimate; returns whether to continue. ``None``
        continues without asking.
    page_breaks
        Whether page-break verification follows page extraction.
    pause
        Whether to stop after a step that wrote new output, a new survey or new page
        files, before the next step.

    Returns
    -------
    RunStatus
        ``paused`` when the run paused, otherwise ``completed``.
    """

    breaks_follow = page_breaks and not pause
    await _survey(
        run,
        breaks_follow=breaks_follow,
        confirm=confirm,
        extraction_follows=not pause,
    )
    new_survey = run.steps[-1].status == "completed"
    if new_survey and pause:
        _skip_steps(
            run, [_EXTRACTION_STEP, _BREAKS_STEP] if page_breaks else [_EXTRACTION_STEP]
        )
        return "paused"
    await _extraction(
        run, breaks_follow=breaks_follow, confirm=confirm, estimate=not new_survey
    )
    if not page_breaks:
        return "completed"
    new_pages = run.steps[-1].status == "completed"
    return await _page_breaks(
        run,
        confirm=confirm,
        estimate=not (new_survey or new_pages),
        pause=pause and new_pages,
    )


async def _survey(
    run: _Run,
    *,
    breaks_follow: bool,
    confirm: SpendConfirmation | None,
    extraction_follows: bool,
) -> PdfSurvey:
    """Run the survey step: measure the PDF, then reuse or make the survey.

    A new survey first checks the API keys and the cost estimate of every step the
    run will reach, and asks before spending. The step is added to ``run.steps``
    when it starts and ended when it reuses or makes the survey; a step that raises
    is ended by the caller.

    Parameters
    ----------
    run
        The run, which the step updates.
    breaks_follow
        Whether page-break verification runs after a new survey in this run without
        a pause, so the estimate covers the breaks the run would judge and the step's
        API key is checked before the survey spends anything.
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
            if breaks_follow:
                steps += _breaks_ahead(
                    config=config, facts=run.facts, survey=None, to_extract=run.selected
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

    survey_chars, verifier_chars = (
        (0, 0) if reused else _prompt_chars(config=config, facts=facts)
    )
    return estimate_survey(
        config=config,
        page_count=facts.pdf.page_count,
        prompt_chars=survey_chars,
        reused=reused,
        verifier_chars=verifier_chars,
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
        ``cost.jsonl``, the page files in ``pages/`` made from the PDF in
        ``pdf_facts.json``, in page order, and the verdict files in ``page_breaks/``
        made from that PDF and from two of those page files as written, in break
        order. A part is ``None``, or empty, when its files are absent; the pages
        and verdicts are empty without ``pdf_facts.json``.

    Raises
    ------
    OutputError
        If the folder does not exist, holds none of those files, or holds one that
        is not valid JSON, does not match its schema or has another major schema
        version, verdict files included, or a page file of the folder's PDF names a
        figure image that is missing.
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
    sha256 = None if facts is None else facts.pdf.sha256
    pages = _load_pages(folder, sha256=sha256)
    return RunResult(
        breaks=_load_breaks(folder, pages=pages, sha256=sha256),
        facts=facts,
        ledger=ledger.entries,
        output_dir=folder,
        pages=pages,
        record=record,
        survey=survey,
    )


async def run_estimate(*, config: Config) -> CostEstimate:
    """Estimate what a run would cost, writing nothing and calling no model.

    The saved facts are used when they match; otherwise the PDF is measured without
    saving the facts. A survey, page file or verdict file that would be reused costs
    nothing. When the survey would be reused, the estimate covers the selected pages
    that have no page file to reuse and the breaks whose verdict would not be
    reused. When it would run, it covers every selected page and every break too,
    unless the run would pause after it. Page-break verification is left out when
    the run would not reach it, because the PDF has one page, the run would pause
    before it, or a page would have no current page file.

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
    survey = saved_survey(
        config=config, facts=facts, output_folder=config.output_folder, quiet=True
    )
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
        if not (config.pause and to_extract):
            steps += _breaks_estimate(
                config=config,
                facts=facts,
                survey=survey,
                to_extract={page.page_index for page in to_extract},
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
        steps += _breaks_estimate(
            config=config, facts=facts, survey=None, to_extract=selected
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
    await _steps(run, confirm=None, page_breaks=False, pause=False)
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
    interrupted writes, and checked for results of another PDF. The survey runs,
    then page extraction, then page-break verification. With ``pause`` on, the run
    ends ``paused`` after a new survey, or after page extraction wrote new page files.

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
        The run's record, facts, survey, selected pages' page files, verdict files
        and the folder's ledger.

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
    PageBreakError
        If a model refuses, runs out of output tokens, or never gives a usable
        answer for a break.
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
            status = await _steps(
                run, confirm=confirm, page_breaks=True, pause=config.pause
            )
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
        breaks=[run.breaks[index] for index in sorted(run.breaks)],
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
    return await _survey(
        run, breaks_follow=False, confirm=None, extraction_follows=False
    )

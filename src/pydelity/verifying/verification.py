"""Page-break verification: reuse verdict files, or judge breaks and write new ones.

Each break between two consecutive pages has its own verdict file,
``page_breaks/<NNNN>-<NNNN>.json``, whose fingerprint covers the bytes of its two
page files and what its requests are made from. A valid verdict file whose
fingerprint matches is reused unless ``overwrite`` is set. A damaged one gives a
warning and the break is judged again.

When a page of a break has no item outside the page furniture, nothing can continue,
so the verdict is written without a request. The other breaks to judge run several
at a time, at most ``advanced.page_breaks.concurrent_breaks`` at once. The judge
reads both pages and gives a verdict, and when page-break verification's verifier is
on, a second request to the same model reviews it. When one break fails, the others
are canceled and the first error ends the step. Verdict files already written stay
valid.
"""

# Standard Library
import asyncio
import hashlib
import json

from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from importlib.metadata import version
from itertools import pairwise
from pathlib import Path

# Third Party Library
from loguru import logger
from pydantic import ValidationError

# Package Library
from pydelity.config.schemas import Config
from pydelity.costs.budget import BreakRequestSize, format_usd
from pydelity.costs.ledger import LEDGER_FILE_NAME, read_ledger
from pydelity.extracting.extraction import page_file_path, plan_pages
from pydelity.extracting.rendering import RENDERING_SETTINGS, PdfWorker
from pydelity.extracting.schemas import PageFile
from pydelity.review import BreakCheckName, CheckFailure
from pydelity.schema_versions import BREAK_SCHEMA_VERSION
from pydelity.surveying.schemas import Facts, PdfSurvey
from pydelity.utils.coroutines import warn
from pydelity.utils.files import load_model, remove_stale_temp_files, write_model_atomic
from pydelity.utils.fingerprints import fingerprint
from pydelity.verifying.llm import (
    BreakInput,
    JudgeAnswer,
    StepModel,
    VerifierAnswer,
    ask_judge,
    ask_verifier,
)
from pydelity.verifying.prompts import (
    PROMPT_VERSION,
    BreakPrompts,
    judge_break,
    judge_instructions,
    verify_break,
)
from pydelity.verifying.schemas import (
    BreakContext,
    BreakFile,
    BreakInputs,
    BreakPage,
    BreakSettings,
    BreakVerdict,
    BreakVerification,
    BreakVerifierVerdict,
    Judgment,
)
from pydelity.verifying.validators import (
    check_results,
    compare_with_hints,
    hint_results,
    review_issues,
    run_checks,
)

# A verdict with nothing in it, for measuring the verifier's own text without the
# verdict it reviews, which the estimate counts as the judge's answer.
_EMPTY_VERDICT = BreakVerdict(containers=[], continues=False, pieces=[], reason="")

# The size of a break's judge and verifier requests before the survey has made the
# hints their instructions hold, in characters, without the pages: the instructions
# with the hints and, for the verifier, its review text, plus the answer format.
# Rounded up from the largest measured on real surveys, 13,967 and 17,143.
_JUDGE_ALLOWANCE_CHARS = 14_000
_VERIFIER_ALLOWANCE_CHARS = 18_000

# The size of one page's details in a break's requests before its page file exists,
# in characters, beyond twice its text-layer characters. Rounded up from real runs
# of 2 to 257 pages and the test answers for the 1965 scan, so that no run's breaks
# together come out smaller than measured. The scan's form pages, which have no
# text layer, needed the most, 5,353.
_PAGE_ALLOWANCE_CHARS = 6_000

# The folder in the output folder that holds the verdict files,
# ``page_breaks/<NNNN>-<NNNN>.json``.
BREAKS_FOLDER_NAME = "page_breaks"


@dataclass(frozen=True)
class _KeptVerdict:
    """The verdict a verdict file keeps, after the verifier's review if one ran.

    Attributes
    ----------
    attempts
        How many verdicts were checked from the model that gave it, or 0 when no
        model was asked.
    failures
        Each check's failures on it, in the order the checks run.
    verdict
        The judge's verdict, or the verifier's correction when it replaced it.
    verification
        The verifier's review, for the verdict file; ``None`` when no verifier ran.
    """

    attempts: int
    failures: Mapping[BreakCheckName, list[CheckFailure]]
    verdict: BreakVerdict
    verification: BreakVerification | None


@dataclass(frozen=True)
class _StepRun:
    """What the break tasks of one call to `verify_breaks` share.

    Attributes
    ----------
    entries_before
        How many entries ``cost.jsonl`` held when the step started, so a break's
        cost counts only this step's requests.
    model
        The step's model and settings.
    output_folder
        The output folder.
    worker
        The PyMuPDF worker, with the PDF open.
    """

    entries_before: int
    model: StepModel
    output_folder: Path
    worker: PdfWorker


async def _ask_models(planned: "PlannedBreak", *, run: _StepRun) -> _KeptVerdict:
    """Ask the judge for a break's verdict, and the verifier to review it when on.

    Parameters
    ----------
    planned
        The break.
    run
        The step's shared state.

    Returns
    -------
    _KeptVerdict
        The verdict to keep, with its check failures and the verifier's review.
    """

    earlier, later = planned.earlier.page_file, planned.later.page_file
    request = BreakInput(
        context=planned.inputs.context,
        earlier=earlier,
        earlier_image=await run.worker.page_image(
            page_index=earlier.page_index, rotation=earlier.rotation
        ),
        later=later,
        later_image=await run.worker.page_image(
            page_index=later.page_index, rotation=later.rotation
        ),
    )
    judged = await ask_judge(model=run.model, request=request)
    verified = None
    if run.model.verify:
        verified = await ask_verifier(
            differences=compare_with_hints(
                judged.verdict, earlier, later, request.context
            ),
            failures=judged.failures,
            model=run.model,
            request=request,
            verdict=judged.verdict,
        )
    return _kept_verdict(judged=judged, verified=verified)


def _break_context(*, config: Config, survey: PdfSurvey) -> BreakContext:
    """Collect what every break's requests share: the survey's hints and settings.

    Parameters
    ----------
    config
        The run's settings, for page-break verification's instructions.
    survey
        The survey, for its continuation notes, its start markers and the page
        count.

    Returns
    -------
    BreakContext
        The context, the same for every break of the PDF.
    """

    return BreakContext(
        continuation_notes=survey.profile.continuation_notes,
        instructions=config.advanced.page_breaks.instructions,
        page_count=len(survey.facts.pages),
        start_markers=survey.profile.start_markers,
    )


def _break_file(
    planned: "PlannedBreak", *, judgment: Judgment, kept: _KeptVerdict
) -> BreakFile:
    """Build a break's verdict file from the kept verdict.

    Parameters
    ----------
    planned
        The break.
    judgment
        ``model`` when a model judged the break, ``no_content`` when no request was
        made.
    kept
        The kept verdict, its check failures and the verifier's review.

    Returns
    -------
    BreakFile
        The verdict file, with its checks, hints and review issues.
    """

    earlier, later = planned.earlier.page_file, planned.later.page_file
    checks = check_results(kept.failures, attempts=kept.attempts)
    hints = hint_results(
        compare_with_hints(kept.verdict, earlier, later, planned.inputs.context)
    )
    return BreakFile(
        checks=checks,
        earlier_page_index=earlier.page_index,
        fingerprint=planned.fingerprint,
        hints=hints,
        inputs=planned.inputs,
        issues=review_issues(
            checks=checks,
            earlier=earlier,
            hints=hints,
            later=later,
            verification=kept.verification,
        ),
        judged_at=datetime.now(UTC),
        judgment=judgment,
        later_page_index=later.page_index,
        pydelity_version=version("pydelity"),
        schema_version=BREAK_SCHEMA_VERSION,
        verdict=kept.verdict,
        verification=kept.verification,
    )


def _break_file_name(earlier_page_index: int) -> str:
    """Name a break's verdict file relative to the output folder.

    Parameters
    ----------
    earlier_page_index
        The page before the break (0-based).

    Returns
    -------
    str
        Such as ``page_breaks/0003-0004.json``.
    """

    return (
        f"{BREAKS_FOLDER_NAME}/{earlier_page_index:04d}-{earlier_page_index + 1:04d}"
        ".json"
    )


def _break_fingerprint(inputs: BreakInputs) -> str:
    """Return the fingerprint of what a break's verdict depends on.

    Parameters
    ----------
    inputs
        The break's inputs.

    Returns
    -------
    str
        The ``sha256:`` fingerprint of the inputs and the verdict file's schema
        version.
    """

    return fingerprint(
        inputs.model_dump(mode="json") | {"schema_version": BREAK_SCHEMA_VERSION}
    )


def _break_inputs(
    *,
    config: Config,
    context: BreakContext,
    earlier: "CurrentPage",
    later: "CurrentPage",
    survey: PdfSurvey,
) -> BreakInputs:
    """Collect what a break's verdict with these settings depends on.

    Parameters
    ----------
    config
        The run's settings.
    context
        The context every break of the PDF shares.
    earlier
        The page before the break, with the hash of its page file.
    later
        The page after the break, with the hash of its page file.
    survey
        The survey, which identifies the PDF.

    Returns
    -------
    BreakInputs
        The inputs, as stored in the verdict file.
    """

    settings = config.advanced.page_breaks
    return BreakInputs(
        context=context,
        earlier=BreakPage(
            page_file_sha256=earlier.sha256, page_index=earlier.page_index
        ),
        later=BreakPage(page_file_sha256=later.sha256, page_index=later.page_index),
        model=config.page_breaks_model.setting,
        pdf_sha256=survey.inputs.pdf_sha256,
        prompt_version=PROMPT_VERSION,
        rendering=RENDERING_SETTINGS,
        settings=BreakSettings(
            check_retries=settings.check_retries,
            effort=settings.effort,
            max_output_tokens=settings.max_output_tokens,
        ),
    )


def _break_label(earlier_page_index: int) -> str:
    """Name a break for log lines and warnings.

    Parameters
    ----------
    earlier_page_index
        The page before the break (0-based).

    Returns
    -------
    str
        Such as ``Break after page 4 (pages 4 and 5)``.
    """

    number = earlier_page_index + 1
    return f"Break after page {number} (pages {number} and {number + 1})"


def _cost_of_break(*, page_index: int, run: _StepRun) -> str:
    """Describe what this step's requests for one break cost.

    Parameters
    ----------
    page_index
        The page before the break (0-based), which the break's ledger lines carry.
    run
        The step's shared state, for the output folder and where this step's
        entries in ``cost.jsonl`` start.

    Returns
    -------
    str
        Such as ``$0.06 for 2 requests``, or ``unknown`` when a request's price is
        not known.
    """

    ledger = read_ledger(run.output_folder / LEDGER_FILE_NAME)
    entries = [
        entry
        for entry in ledger.entries[run.entries_before :]
        if entry.step == "page_breaks" and entry.page_index == page_index
    ]
    count = f"{len(entries)} request{'' if len(entries) == 1 else 's'}"
    costs = [entry.cost_usd for entry in entries]
    if any(cost is None for cost in costs):
        return f"unknown for {count}"
    total = sum((cost for cost in costs if cost is not None), start=Decimal(0))
    return f"{format_usd(total)} for {count}"


def _damage(break_file: BreakFile) -> str | None:
    """Tell why a verdict file that loaded cannot be used, if it cannot.

    Parameters
    ----------
    break_file
        The loaded verdict file.

    Returns
    -------
    str | None
        Why the file is damaged, or ``None`` when it is not.
    """

    found_major = break_file.schema_version.split(".", maxsplit=1)[0]
    major = BREAK_SCHEMA_VERSION.split(".", maxsplit=1)[0]
    if found_major == major:
        return None
    name = _break_file_name(break_file.earlier_page_index)
    return (
        f"{name} has schema version {break_file.schema_version}; this pydelity "
        f"reads version {major}.x"
    )


async def _judge_break(planned: "PlannedBreak", *, run: _StepRun) -> BreakFile:
    """Ask the models about one break, then write and log its verdict file.

    Parameters
    ----------
    planned
        The break to judge, whose two pages both have content items.
    run
        The step's shared state.

    Returns
    -------
    BreakFile
        The verdict file, as written.
    """

    kept = await _ask_models(planned, run=run)
    break_file = _break_file(planned, judgment="model", kept=kept)
    _write_break(
        break_file,
        outcome=f"{len(break_file.issues)} review issues, "
        f"{_verifier_outcome(break_file.verification)}; "
        f"{_cost_of_break(page_index=planned.earlier_page_index, run=run)}",
        output_folder=run.output_folder,
    )
    return break_file


async def _judge_concurrently(
    breaks: Sequence["PlannedBreak"],
    *,
    model: StepModel,
    on_judged: Callable[[BreakFile], None],
    output_folder: Path,
    pdf_path: Path,
) -> None:
    """Judge breaks with the models, at most ``concurrent_breaks`` at once.

    Parameters
    ----------
    breaks
        The breaks to judge, whose pages all have content items.
    model
        The step's model and settings.
    on_judged
        Called with each verdict file once it is written.
    output_folder
        The output folder.
    pdf_path
        The PDF, for the page images.
    """

    limit = asyncio.Semaphore(model.settings.concurrent_breaks)
    async with PdfWorker(pdf_path) as worker:
        run = _StepRun(
            entries_before=len(read_ledger(output_folder / LEDGER_FILE_NAME).entries),
            model=model,
            output_folder=output_folder,
            worker=worker,
        )

        async def limited(planned: PlannedBreak) -> None:
            """Judge a break once fewer than the limit are running."""

            async with limit:
                break_file = await _judge_break(planned, run=run)
            on_judged(break_file)

        try:
            async with asyncio.TaskGroup() as group:
                for planned in breaks:
                    group.create_task(limited(planned))
        except ExceptionGroup as errors:
            # The task group cancels the other breaks after the first error, which is
            # the one the step reports.
            first = errors.exceptions[0]
            raise first from first.__cause__


def _kept_verdict(
    *, judged: JudgeAnswer, verified: VerifierAnswer | None
) -> _KeptVerdict:
    """Apply the verifier's answer, keeping its correction when the checks allow.

    A correction is kept when it passes every check, whatever its hint differences,
    since the hints come from the survey, which can be wrong.

    Parameters
    ----------
    judged
        The judge's kept verdict.
    verified
        The verifier's answer on it, or ``None`` when no verifier ran.

    Returns
    -------
    _KeptVerdict
        The correction, with its check failures, when the answer has one that is
        kept, and otherwise the judge's verdict, with the verifier's review when one
        ran.
    """

    if verified is None:
        return _KeptVerdict(
            attempts=judged.attempts,
            failures=judged.failures,
            verdict=judged.verdict,
            verification=None,
        )

    corrected = verified.review.corrected
    correction_failures = verified.correction_failures
    if (
        corrected is not None
        and correction_failures is not None
        and not any(correction_failures.values())
    ):
        return _KeptVerdict(
            attempts=verified.attempts,
            failures=correction_failures,
            verdict=corrected,
            verification=BreakVerification(
                attempts=verified.attempts,
                correction_applied=True,
                correction_failures=[],
                verdict=verified.review,
            ),
        )

    rejected = []
    if correction_failures is not None:
        results = check_results(correction_failures, attempts=verified.attempts)
        rejected = [result for result in results if not result.passed]
    return _KeptVerdict(
        attempts=judged.attempts,
        failures=judged.failures,
        verdict=judged.verdict,
        verification=BreakVerification(
            attempts=verified.attempts,
            correction_applied=False,
            correction_failures=rejected,
            verdict=verified.review,
        ),
    )


def _no_content_break(
    planned: "PlannedBreak", *, empty: Sequence[int], output_folder: Path
) -> BreakFile:
    """Write and log the verdict of a break with a page that has no content items.

    Nothing can carry on across such a break, so no request is made.

    Parameters
    ----------
    planned
        The break.
    empty
        Its pages (0-based) that have no content items, in page order.
    output_folder
        The output folder.

    Returns
    -------
    BreakFile
        The verdict file, as written, with every check passed after 0 attempts.
    """

    verdict = BreakVerdict(
        containers=[],
        continues=False,
        pieces=[],
        reason=f"{_pages_phrase(empty)} no content items, so nothing can carry on "
        "across the break.",
    )
    kept = _KeptVerdict(
        attempts=0,
        failures=run_checks(
            verdict, planned.earlier.page_file, planned.later.page_file
        ),
        verdict=verdict,
        verification=None,
    )
    break_file = _break_file(planned, judgment="no_content", kept=kept)
    _write_break(
        break_file,
        outcome=f"no request, {_pages_phrase(empty).lower()} no content items",
        output_folder=output_folder,
    )
    return break_file


def _pages_phrase(page_indexes: Sequence[int]) -> str:
    """Name one or two pages as the subject of a sentence about them.

    Parameters
    ----------
    page_indexes
        One or two pages (0-based), in page order.

    Returns
    -------
    str
        Such as ``Page 5 has`` or ``Pages 4 and 5 have``.
    """

    numbers = [index + 1 for index in page_indexes]
    if len(numbers) == 1:
        return f"Page {numbers[0]} has"
    return f"Pages {numbers[0]} and {numbers[1]} have"


def _pages_without_content(planned: "PlannedBreak") -> list[int]:
    """Find the pages of a break that have no item outside the page furniture.

    Parameters
    ----------
    planned
        The break.

    Returns
    -------
    list[int]
        Those pages (0-based), in page order; empty when both pages have content.
    """

    return [
        page.page_index
        for page in (planned.earlier.page_file, planned.later.page_file)
        if all(item.role == "artifact" for item in page.items)
    ]


def _read_current(path: Path) -> "CurrentPage | None":
    """Read a page file with the SHA-256 of its bytes.

    Parameters
    ----------
    path
        The page file.

    Returns
    -------
    CurrentPage | None
        The page file and its hash, or ``None`` when the file is absent or does not
        validate.
    """

    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return None
    try:
        page_file = PageFile.model_validate_json(data)
    except ValidationError:
        return None
    return CurrentPage(
        page_file=page_file, sha256=f"sha256:{hashlib.sha256(data).hexdigest()}"
    )


def _reusable_break(
    saved: BreakFile | None, *, config: Config, expected: str, quiet: bool
) -> BreakFile | None:
    """Return a break's saved verdict file when it can be reused.

    It can be reused when its fingerprint matches, ``overwrite`` is not set, and it
    was made without a request, holds a verifier's review, or page-break
    verification's verifier is off. So a break judged without the verifier is
    judged again once the verifier is turned on, while a break the verifier
    reviewed is still reused after it is turned off.

    Parameters
    ----------
    saved
        The break's valid verdict file, or ``None`` when it has none.
    config
        The run's settings.
    expected
        The fingerprint of the break's current inputs.
    quiet
        Whether to leave out the log line for a verdict file passed over only
        because no verifier reviewed it.

    Returns
    -------
    BreakFile | None
        The verdict file to reuse, or ``None`` when the break is to be judged.
    """

    if saved is None or saved.fingerprint != expected or config.overwrite:
        return None
    if (
        saved.judgment == "model"
        and saved.verification is None
        and config.verify_page_breaks
    ):
        if not quiet:
            logger.info(
                "{label}: no verifier reviewed its verdict, so the break is judged "
                "again with the verifier",
                label=_break_label(saved.earlier_page_index),
            )
        return None
    return saved


def _saved_break(
    *, earlier_page_index: int, output_folder: Path, quiet: bool
) -> BreakFile | None:
    """Load a break's verdict file, warning when it is damaged.

    Parameters
    ----------
    earlier_page_index
        The page before the break (0-based).
    output_folder
        The output folder.
    quiet
        Whether to leave out the warning.

    Returns
    -------
    BreakFile | None
        The verdict file, or ``None`` when it is absent or damaged.
    """

    name = _break_file_name(earlier_page_index)
    loaded = load_model(model_type=BreakFile, path=output_folder / name)
    damage = loaded.damage
    if loaded.model is not None:
        damage = _damage(loaded.model)
    if damage is not None and not quiet:
        number = earlier_page_index + 1
        warn(
            f"{damage}; judging the break after page {number} (pages {number} and "
            f"{number + 1}) again",
            code="damaged_output",
            details={"file": name},
        )
    return None if damage is not None else loaded.model


def _text_chars(prompts: BreakPrompts) -> int:
    """Count the characters of a request's instructions and text parts.

    Parameters
    ----------
    prompts
        The request's prompts.

    Returns
    -------
    int
        The length of the instructions, both page texts and the review text.
    """

    return (
        len(prompts.system_message)
        + len(prompts.earlier_text)
        + len(prompts.later_text)
        + len(prompts.review_text or "")
    )


def _verifier_outcome(verification: BreakVerification | None) -> str:
    """Describe the verifier's review for the break's log line.

    Parameters
    ----------
    verification
        The verifier's review, or ``None`` when no verifier ran.

    Returns
    -------
    str
        ``verifier passed``, ``verifier corrected the verdict``, such as
        ``verifier found 2 problems``, or ``no verifier``.
    """

    if verification is None:
        return "no verifier"
    if verification.verdict.passed:
        return "verifier passed"
    if verification.correction_applied:
        return "verifier corrected the verdict"
    count = len(verification.verdict.problems)
    return f"verifier found {count} problem{'' if count == 1 else 's'}"


def _write_break(break_file: BreakFile, *, outcome: str, output_folder: Path) -> None:
    """Write a break's verdict file atomically and log the break's line.

    Parameters
    ----------
    break_file
        The verdict file.
    outcome
        How the verdict was made, for the log line, such as ``0 review issues, no
        verifier; $0.06 for 2 requests``.
    output_folder
        The output folder.
    """

    page_index = break_file.earlier_page_index
    write_model_atomic(
        model=break_file, path=output_folder / _break_file_name(page_index)
    )
    pieces = len(break_file.verdict.pieces)
    logger.info(
        "{label}: {continuation}, {outcome}",
        continuation=f"continues, {pieces} piece{'' if pieces == 1 else 's'}"
        if break_file.verdict.continues
        else "nothing continues",
        label=_break_label(page_index),
        outcome=outcome,
    )


@dataclass(frozen=True)
class CurrentPage:
    """A current page file, as written, with the SHA-256 of its bytes.

    Attributes
    ----------
    page_file
        The page file.
    sha256
        ``sha256:`` digest of the page file's bytes on disk.
    """

    page_file: PageFile
    sha256: str

    @property
    def page_index(self) -> int:
        """The page (0-based)."""

        return self.page_file.page_index


@dataclass(frozen=True)
class PlannedBreak:
    """A break: what its verdict depends on, and its verdict file if reused.

    Attributes
    ----------
    earlier
        The page before the break.
    fingerprint
        The fingerprint of ``inputs``.
    inputs
        What the break's verdict depends on, its context included.
    later
        The page after the break.
    saved
        The verdict file to reuse, or ``None`` when the break is to be judged.
    """

    earlier: CurrentPage
    fingerprint: str
    inputs: BreakInputs
    later: CurrentPage
    saved: BreakFile | None

    @property
    def earlier_page_index(self) -> int:
        """The page before the break (0-based), which names the break."""

        return self.earlier.page_index


def break_file_path(*, earlier_page_index: int, output_folder: Path) -> Path:
    """Return the path of a break's verdict file.

    Parameters
    ----------
    earlier_page_index
        The page before the break (0-based).
    output_folder
        The output folder.

    Returns
    -------
    Path
        ``<output folder>/page_breaks/<NNNN>-<NNNN>.json``, with both page indexes
        in four or more digits.
    """

    return output_folder / _break_file_name(earlier_page_index)


def current_pages(
    *,
    config: Config,
    extracted: Collection[int],
    output_folder: Path,
    survey: PdfSurvey,
) -> dict[int, CurrentPage]:
    """Read the page files page-break verification may judge breaks from.

    A page's page file is current when page extraction wrote it in this run, or
    when page extraction would reuse it now without a request. Each is read from
    disk with the hash of its bytes, so a page extracted again has a new hash.

    Parameters
    ----------
    config
        The run's settings.
    extracted
        The pages (0-based) page extraction wrote a page file for in this run.
    output_folder
        The output folder.
    survey
        The survey.

    Returns
    -------
    dict[int, CurrentPage]
        The current page files by page index. A page missing from it lacks a
        current page file.
    """

    others = [
        page_index
        for page_index in range(len(survey.facts.pages))
        if page_index not in extracted
    ]
    reusable = {
        page.page_index
        for page in plan_pages(
            config=config,
            output_folder=output_folder,
            page_indexes=others,
            quiet=True,
            survey=survey,
        )
        if page.saved is not None
    }

    current = {}
    for page_index in range(len(survey.facts.pages)):
        if page_index not in extracted and page_index not in reusable:
            continue
        read = _read_current(
            page_file_path(output_folder=output_folder, page_index=page_index)
        )
        if read is not None:
            current[page_index] = read
    return current


def plan_breaks(
    *,
    config: Config,
    output_folder: Path,
    pages: Sequence[CurrentPage],
    quiet: bool = False,
    survey: PdfSurvey,
) -> list[PlannedBreak]:
    """Decide which breaks to judge and which verdict files to reuse.

    A verdict file is reused when it is valid, its fingerprint matches the break's
    inputs, ``overwrite`` is not set, and it was made without a request, holds a
    verifier's review, or page-break verification's verifier is off. A damaged
    verdict file gives a warning, and the plan is logged.

    Parameters
    ----------
    config
        The run's settings.
    output_folder
        The output folder.
    pages
        The current page file of every page of the PDF, in page order.
    quiet
        Whether to plan without the warnings and the log lines, as an estimate does.
    survey
        The survey.

    Returns
    -------
    list[PlannedBreak]
        One entry per break, in page order.
    """

    context = _break_context(config=config, survey=survey)
    planned = []
    for earlier, later in pairwise(pages):
        inputs = _break_inputs(
            config=config, context=context, earlier=earlier, later=later, survey=survey
        )
        expected = _break_fingerprint(inputs)
        saved = _saved_break(
            earlier_page_index=earlier.page_index,
            output_folder=output_folder,
            quiet=quiet,
        )
        planned.append(
            PlannedBreak(
                earlier=earlier,
                fingerprint=expected,
                inputs=inputs,
                later=later,
                saved=_reusable_break(
                    saved, config=config, expected=expected, quiet=quiet
                ),
            )
        )

    reused = sum(planned_break.saved is not None for planned_break in planned)
    if quiet:
        return planned
    logger.info(
        "Page-break verification: {breaks}, {reused} reused, {judge} to judge",
        breaks=f"{len(planned)} break" + ("" if len(planned) == 1 else "s"),
        judge=len(planned) - reused,
        reused=reused,
    )
    return planned


def request_sizes(breaks: Sequence[PlannedBreak]) -> list[BreakRequestSize]:
    """Measure the requests of the breaks to judge, for the cost estimate.

    Parameters
    ----------
    breaks
        The breaks to judge, from `plan_breaks`. A break with a page that has no
        content items needs no request and is left out.

    Returns
    -------
    list[BreakRequestSize]
        The request sizes of each break the models would judge, in the order of
        ``breaks``.
    """

    verdict_format = len(json.dumps(BreakVerdict.model_json_schema()))
    review_format = len(json.dumps(BreakVerifierVerdict.model_json_schema()))
    sizes = []
    for planned in breaks:
        if _pages_without_content(planned):
            continue
        context = planned.inputs.context
        judged = judge_break(
            context, earlier=planned.earlier.page_file, later=planned.later.page_file
        )
        verifier = verify_break(
            context, differences={}, failures={}, judged=judged, verdict=_EMPTY_VERDICT
        )
        sizes.append(
            BreakRequestSize(
                judge_chars=_text_chars(judged) + verdict_format,
                verifier_chars=_text_chars(verifier) + review_format,
            )
        )
    return sizes


def request_sizes_before_pages(
    *,
    config: Config,
    earlier_page_indexes: Sequence[int],
    facts: Facts,
    survey: PdfSurvey | None,
) -> list[BreakRequestSize]:
    """Size the requests of breaks whose page files do not exist yet.

    The instructions are measured from the survey when it exists, and are otherwise
    an allowance with the user's instructions added. Each page adds an allowance
    plus twice its text-layer characters.

    Parameters
    ----------
    config
        The run's settings.
    earlier_page_indexes
        The breaks, each by the page before it (0-based).
    facts
        The measured facts, for each page's text-layer characters.
    survey
        The survey, or ``None`` before it has run.

    Returns
    -------
    list[BreakRequestSize]
        Each break's request sizes, in the order of ``earlier_page_indexes``.
    """

    if survey is None:
        instructions = len(config.advanced.page_breaks.instructions or "")
        judge = _JUDGE_ALLOWANCE_CHARS + instructions
        verifier = _VERIFIER_ALLOWANCE_CHARS + instructions
    else:
        context = _break_context(config=config, survey=survey)
        judge = len(judge_instructions(context)) + len(
            json.dumps(BreakVerdict.model_json_schema())
        )
        # The verifier's instructions and review text, without page texts.
        blank = BreakPrompts(
            earlier_text="", later_text="", review_text=None, system_message=""
        )
        verifier = _text_chars(
            verify_break(
                context,
                differences={},
                failures={},
                judged=blank,
                verdict=_EMPTY_VERDICT,
            )
        ) + len(json.dumps(BreakVerifierVerdict.model_json_schema()))

    sizes = []
    for index in earlier_page_indexes:
        pages = sum(
            _PAGE_ALLOWANCE_CHARS + 2 * facts.pages[page_index].text.chars
            for page_index in (index, index + 1)
        )
        sizes.append(
            BreakRequestSize(judge_chars=judge + pages, verifier_chars=verifier + pages)
        )
    return sizes


async def verify_breaks(
    *,
    breaks: Sequence[PlannedBreak],
    model: StepModel,
    on_written: Callable[[BreakFile], None] | None = None,
    output_folder: Path,
    pdf_path: Path,
) -> list[BreakFile]:
    """Judge the planned breaks that have no verdict file to reuse.

    The ``page_breaks/`` folder is created if needed, and temporary files that an
    interrupted write left in it are removed first. Then each break with a page
    that has no content items gets its verdict file without a request. The other
    breaks are judged by the models, at most
    ``advanced.page_breaks.concurrent_breaks`` at once. When one of them fails, the
    breaks still running are canceled, no other break starts, and its error is
    raised. Verdict files already written stay valid.

    Parameters
    ----------
    breaks
        Every break, from `plan_breaks`.
    model
        The step's model and settings, from
        `pydelity.providers.factory.build_model`.
    on_written
        Called with each new verdict file once it is written, so a caller can count
        the breaks done even when a later break fails.
    output_folder
        The output folder.
    pdf_path
        The PDF, for the page images.

    Returns
    -------
    list[BreakFile]
        Every break's verdict file, reused or new, in the order of ``breaks``.

    Raises
    ------
    BudgetExceededError
        If a request would go over ``max_cost`` and the run was not allowed to.
    PageBreakError
        If a model refuses, runs out of output tokens, or never gives a usable
        answer for a break.
    ProviderError
        If a request fails after the provider retries.
    """

    folder = output_folder / BREAKS_FOLDER_NAME
    folder.mkdir(exist_ok=True, parents=True)
    for leftover in remove_stale_temp_files(folder):
        logger.debug("Removed {path}, left by an interrupted write", path=leftover)

    new: dict[int, BreakFile] = {}

    def written(break_file: BreakFile) -> None:
        """Keep a new verdict file and tell the caller."""

        new[break_file.earlier_page_index] = break_file
        if on_written is not None:
            on_written(break_file)

    # Breaks that need no request are written first, so a failure among the others
    # never leaves them out.
    to_ask = []
    for planned in breaks:
        if planned.saved is not None:
            continue
        empty = _pages_without_content(planned)
        if empty:
            written(
                _no_content_break(planned, empty=empty, output_folder=output_folder)
            )
        else:
            to_ask.append(planned)
    if to_ask:
        await _judge_concurrently(
            to_ask,
            model=model,
            on_judged=written,
            output_folder=output_folder,
            pdf_path=pdf_path,
        )

    return [
        planned.saved if planned.saved is not None else new[planned.earlier_page_index]
        for planned in breaks
    ]

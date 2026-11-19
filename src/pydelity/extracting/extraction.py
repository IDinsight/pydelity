"""The page extraction step: reuse page files, or extract pages and write new ones.

Each selected page has its own page file, ``pages/<NNNN>.json``, whose fingerprint
covers only what that page's requests are made from. A valid page file whose
fingerprint matches is reused unless ``overwrite`` is set. A damaged one gives a
warning and the page is extracted again.

Pages to extract run several at a time, at most
``advanced.extraction.concurrent_pages`` at once. For each page, the extraction model
reads the page, the verifier model reviews the reading, and Python assigns item IDs,
maps boxes to points, and writes the figure crops and then the page file. When one page
fails, the others are canceled and the first error ends the step; page files already
written stay valid.
"""

# Standard Library
import asyncio

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path

# Third Party Library
from loguru import logger

# Package Library
from pydelity.config.schemas import Config, is_language_tag, standard_language_tag
from pydelity.costs.budget import format_usd
from pydelity.costs.ledger import LEDGER_FILE_NAME, read_ledger
from pydelity.extracting.llm import (
    ModelPage,
    ModelVerdict,
    PageInput,
    StepModel,
    ask_extractor,
    ask_verifier,
)
from pydelity.extracting.prompts import PROMPT_VERSION
from pydelity.extracting.rendering import (
    RENDERING_SETTINGS,
    PdfWorker,
    grid_box_to_points,
)
from pydelity.extracting.schemas import (
    AnswerItem,
    Container,
    Entry,
    ExtractionCheckResult,
    ExtractionSettings,
    Figure,
    Item,
    PageAnswer,
    PageContext,
    PageFile,
    PageImageSize,
    PageInputs,
    PageRepeatedLine,
    PageVerification,
    RepeatedLineUse,
    VerifierProblem,
)
from pydelity.extracting.text_layer import read_lines
from pydelity.extracting.validators import (
    check_results,
    comparison_status,
    review_issues,
    unmatched_labels,
)
from pydelity.review import CheckFailure, ExtractionCheckName, ReviewIssue
from pydelity.schema_versions import PAGE_SCHEMA_VERSION
from pydelity.surveying.schemas import PdfSurvey
from pydelity.surveying.validators import covering_range
from pydelity.utils.coroutines import warn
from pydelity.utils.files import (
    load_model,
    remove_stale_temp_files,
    write_bytes_atomic,
    write_model_atomic,
)
from pydelity.utils.fingerprints import fingerprint


@dataclass(frozen=True)
class _KeptAnswer:
    """The answer a page file is built from, after the verifier's review.

    Attributes
    ----------
    answer
        The extraction model's answer, or the verifier's correction when it replaced
        it.
    attempts
        How many answers were checked from the model that gave it.
    failures
        Each check's failures on it, in the order the checks run.
    verification
        The verifier's review, for the page file.
    """

    answer: PageAnswer
    attempts: int
    failures: Mapping[ExtractionCheckName, list[CheckFailure]]
    verification: PageVerification


@dataclass(frozen=True)
class _PageItems:
    """A page's items and containers with the IDs and boxes pydelity gives them.

    Attributes
    ----------
    containers
        The containers, in the answer's order.
    ids
        The ID of each item and container by the ref the answer gave it, for the
        review issues. A ref used more than once names the first item that has it,
        or else the first container.
    items
        The items, in reading order.
    """

    containers: list[Container]
    ids: dict[str, str]
    items: list[Item]


@dataclass(frozen=True)
class _StepRun:
    """What the page tasks of one call to `extract_pages` share.

    Attributes
    ----------
    entries_before
        How many entries ``cost.jsonl`` held when the step started, so a page's cost
        counts only this step's requests.
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


def _cost_of_page(*, page_index: int, run: _StepRun) -> str:
    """Describe what this step's requests for one page cost.

    Parameters
    ----------
    page_index
        The page (0-based).
    run
        The step's shared state, for the output folder and where this step's
        entries in ``cost.jsonl`` start.

    Returns
    -------
    str
        Such as ``$0.31 for 2 requests``, or ``unknown`` when a request's price is not
        known.
    """

    ledger = read_ledger(run.output_folder / LEDGER_FILE_NAME)
    entries = [
        entry
        for entry in ledger.entries[run.entries_before :]
        if entry.step == "extraction" and entry.page_index == page_index
    ]
    count = f"{len(entries)} request{'' if len(entries) == 1 else 's'}"
    costs = [entry.cost_usd for entry in entries]
    if any(cost is None for cost in costs):
        return f"unknown for {count}"
    total = sum((cost for cost in costs if cost is not None), start=Decimal(0))
    return f"{format_usd(total)} for {count}"


def _crop_box(bbox: Sequence[float], *, context: PageContext) -> list[float]:
    """Choose the part of the page to cut a figure's image from.

    Parameters
    ----------
    bbox
        The figure's box in points on the displayed page.
    context
        The page's context, for its size.

    Returns
    -------
    list[float]
        The box, or the whole page when the box has no width or height, as a box
        given outside the page has once it is kept inside it.
    """

    if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
        return list(bbox)
    return [0.0, 0.0, context.width_pt, context.height_pt]


def _damage(page_file: PageFile, *, output_folder: Path) -> str | None:
    """Tell why a page file that loaded cannot be used, if it cannot.

    Parameters
    ----------
    page_file
        The loaded page file.
    output_folder
        The output folder, which the figure crops' paths are relative to.

    Returns
    -------
    str | None
        Why the file is damaged, or ``None`` when it is not.
    """

    name = _page_file_name(page_file.page_index)
    found_major = page_file.schema_version.split(".", maxsplit=1)[0]
    major = PAGE_SCHEMA_VERSION.split(".", maxsplit=1)[0]
    if found_major != major:
        return (
            f"{name} has schema version {page_file.schema_version}; this pydelity "
            f"reads version {major}.x"
        )
    for item in page_file.items:
        if item.figure is not None and not (output_folder / item.figure.crop).is_file():
            return f"{name} names the figure image {item.figure.crop}, which is missing"
    return None


async def _extract_page(page: "PlannedPage", *, run: _StepRun) -> PageFile:
    """Extract one page and write its figure crops and page file.

    Parameters
    ----------
    page
        The page to extract.
    run
        The step's shared state.

    Returns
    -------
    PageFile
        The page file, as written.
    """

    context = page.inputs.context
    page_index = context.page_index
    image = await run.worker.page_image(
        page_index=page_index, rotation=context.rotation
    )
    text_lines = await run.worker.call(
        lambda document: read_lines(document, page_index=page_index)
    )
    page_input = PageInput(context=context, image=image, text_lines=text_lines)

    extracted = await ask_extractor(model=run.model, page=page_input)
    verified = await ask_verifier(
        answer=extracted.answer,
        failures=extracted.failures,
        model=run.model,
        page=page_input,
    )
    kept = _kept_answer(extracted=extracted, verified=verified)

    built = _page_items(kept.answer, context)
    checks = check_results(kept.failures, attempts=kept.attempts)
    page_file = PageFile(
        checks=checks,
        column_order=kept.answer.column_order,
        containers=built.containers,
        extracted_at=datetime.now(UTC),
        fingerprint=page.fingerprint,
        height_pt=context.height_pt,
        image=PageImageSize(height_px=image.height_px, width_px=image.width_px),
        inputs=page.inputs,
        issues=_page_issues(built=built, checks=checks, context=context, kept=kept),
        items=built.items,
        page_index=page_index,
        page_number=page_index + 1,
        pydelity_version=version("pydelity"),
        rotation=context.rotation,
        schema_version=PAGE_SCHEMA_VERSION,
        text_comparison=comparison_status(kept.answer, context, text_lines),
        verification=kept.verification,
        width_pt=context.width_pt,
        writing_direction=context.writing_direction,
    )
    await _write_page(page_file, context=context, run=run)

    logger.info(
        "Page {number} (index {index}): {items} items, {issues} review issues, "
        "verifier {outcome}; {cost}",
        cost=_cost_of_page(page_index=page_index, run=run),
        index=page_index,
        issues=len(page_file.issues),
        items=len(page_file.items),
        number=page_index + 1,
        outcome=_verifier_outcome(page_file.verification),
    )
    return page_file


def _item(
    item: AnswerItem,
    *,
    container_ids: Mapping[str, str],
    context: PageContext,
    item_id: str,
    item_ids: Mapping[str, str],
) -> Item:
    """Turn one answer item into a page file item.

    Parameters
    ----------
    item
        The answer item.
    container_ids
        The page's container IDs by ref.
    context
        The page's context, for mapping the item's box to points.
    item_id
        The item's ID.
    item_ids
        The page's item IDs by ref, for ``caption_of``.

    Returns
    -------
    Item
        The item, with its ID, its box in points, the IDs it refers to, its
        language tag in standard form and, for a figure, its crop's path.
    """

    entries = (
        None
        if item.entries is None
        else [
            Entry(
                id=f"{item_id}.{position}",
                level=entry.level,
                marker=entry.marker,
                text=entry.text,
            )
            for position, entry in enumerate(item.entries, start=1)
        ]
    )
    figure = (
        None
        if item.figure is None
        else Figure(
            crop=f"{FIGURES_FOLDER_NAME}/{item_id}.png",
            description=item.figure.description,
            text=item.figure.text,
        )
    )
    language = item.language
    if language is not None and is_language_tag(language):
        language = standard_language_tag(language)
    return Item(
        bbox=_points_box(item.box, context=context),
        caption_of=None if item.caption_of is None else item_ids.get(item.caption_of),
        container=None if item.container is None else container_ids.get(item.container),
        entries=entries,
        field=item.field,
        figure=figure,
        id=item_id,
        kind=item.kind,
        label=item.label,
        language=language,
        latex=item.latex,
        role=item.role,
        table=item.table,
        text=item.text,
    )


def _kept_answer(*, extracted: ModelPage, verified: ModelVerdict) -> _KeptAnswer:
    """Apply the verifier's verdict, keeping its correction only if it passes.

    Parameters
    ----------
    extracted
        The extraction model's kept answer.
    verified
        The verifier's verdict on it.

    Returns
    -------
    _KeptAnswer
        The correction, when the verdict has one that passes every check, and
        otherwise the extraction model's answer, with the verifier's review.
    """

    corrected = verified.verdict.corrected
    correction_failures = verified.correction_failures
    if (
        corrected is not None
        and correction_failures is not None
        and not any(correction_failures.values())
    ):
        return _KeptAnswer(
            answer=corrected,
            attempts=verified.attempts,
            failures=correction_failures,
            verification=PageVerification(
                attempts=verified.attempts,
                correction_applied=True,
                correction_failures=[],
                verdict=verified.verdict,
            ),
        )

    rejected = []
    if correction_failures is not None:
        results = check_results(correction_failures, attempts=verified.attempts)
        rejected = [result for result in results if not result.passed]
    return _KeptAnswer(
        answer=extracted.answer,
        attempts=extracted.attempts,
        failures=extracted.failures,
        verification=PageVerification(
            attempts=verified.attempts,
            correction_applied=False,
            correction_failures=rejected,
            verdict=verified.verdict,
        ),
    )


def _page_file_name(page_index: int) -> str:
    """Name a page's page file relative to the output folder.

    Parameters
    ----------
    page_index
        The page (0-based).

    Returns
    -------
    str
        Such as ``pages/0003.json``.
    """

    return f"{PAGES_FOLDER_NAME}/{page_index:04d}.json"


def _page_issues(
    *,
    built: _PageItems,
    checks: Sequence[ExtractionCheckResult],
    context: PageContext,
    kept: _KeptAnswer,
) -> list[ReviewIssue]:
    """Collect a page's review issues.

    Parameters
    ----------
    built
        The page's items, for the IDs the issues name.
    checks
        The check results on the kept answer.
    context
        The page's context.
    kept
        The kept answer and the verifier's review.

    Returns
    -------
    list[ReviewIssue]
        The checks still failing on the kept answer, then content no label fits,
        with its items' IDs added, then the verifier's problems when its correction
        was not kept.
    """

    issues = review_issues(checks, item_ids=built.ids)
    for issue in unmatched_labels(kept.answer, context):
        refs = issue.details.get("item_refs")
        item_ids = (
            [built.ids.get(str(ref)) for ref in refs] if isinstance(refs, list) else []
        )
        issues.append(
            issue.model_copy(update={"details": issue.details | {"item_ids": item_ids}})
        )
    if not kept.verification.correction_applied:
        issues += [
            _verifier_issue(problem, context=context, ids=built.ids)
            for problem in kept.verification.verdict.problems
        ]
    return issues


def _page_items(answer: PageAnswer, context: PageContext) -> _PageItems:
    """Give an answer's items and containers their IDs and their boxes in points.

    Items are numbered in reading order and containers in the answer's order, from
    1, so the same answer always gives the same IDs. On page index 3, the seventh
    item is ``p0003-007``, the second entry of that item's list is
    ``p0003-007.2``, and the first container is ``p0003-c01``.

    Parameters
    ----------
    answer
        The kept answer.
    context
        The page's context.

    Returns
    -------
    _PageItems
        The items, the containers and the IDs by ref.
    """

    prefix = f"p{context.page_index:04d}"
    item_ids = [
        f"{prefix}-{position:03d}" for position in range(1, len(answer.items) + 1)
    ]
    container_ids = [
        f"{prefix}-c{position:02d}" for position in range(1, len(answer.containers) + 1)
    ]

    # When a ref is used more than once, which the checks report, the first one
    # that has it keeps it.
    item_by_ref: dict[str, str] = {}
    for item, item_id in zip(answer.items, item_ids, strict=True):
        item_by_ref.setdefault(item.ref, item_id)
    container_by_ref: dict[str, str] = {}
    for container, container_id in zip(answer.containers, container_ids, strict=True):
        container_by_ref.setdefault(container.ref, container_id)

    containers = [
        Container(
            bbox=_points_box(container.box, context=context),
            container=(
                None
                if container.container is None
                else container_by_ref.get(container.container)
            ),
            id=container_id,
            label=container.label,
        )
        for container, container_id in zip(
            answer.containers, container_ids, strict=True
        )
    ]
    items = [
        _item(
            item,
            container_ids=container_by_ref,
            context=context,
            item_id=item_id,
            item_ids=item_by_ref,
        )
        for item, item_id in zip(answer.items, item_ids, strict=True)
    ]
    return _PageItems(
        containers=containers, ids=container_by_ref | item_by_ref, items=items
    )


def _points_box(box: Sequence[int], *, context: PageContext) -> list[float]:
    """Map a box on the upright image's grid to points on the displayed page.

    Parameters
    ----------
    box
        The answer's ``[x0, y0, x1, y1]`` on the grid.
    context
        The page's context, for its size and rotation.

    Returns
    -------
    list[float]
        The box in points, inside the page; the whole page when the answer's box
        does not have four values, which the checks report.
    """

    if len(box) != 4:  # noqa: PLR2004 - a box has four values
        return [0.0, 0.0, round(context.width_pt, 2), round(context.height_pt, 2)]
    return grid_box_to_points(
        box,
        height_pt=context.height_pt,
        rotation=context.rotation,
        width_pt=context.width_pt,
    )


def _saved_page(*, output_folder: Path, page_index: int) -> PageFile | None:
    """Load a page's page file, warning when it is damaged.

    Parameters
    ----------
    output_folder
        The output folder.
    page_index
        The page (0-based).

    Returns
    -------
    PageFile | None
        The page file, or ``None`` when it is absent or damaged.
    """

    name = _page_file_name(page_index)
    loaded = load_model(model_type=PageFile, path=output_folder / name)
    damage = loaded.damage
    if loaded.model is not None:
        damage = _damage(loaded.model, output_folder=output_folder)
    if damage is not None:
        warn(
            f"{damage}; extracting page {page_index + 1} (index {page_index}) again",
            code="damaged_output",
            details={"file": name},
        )
        return None
    return loaded.model


def _verifier_issue(
    problem: VerifierProblem, *, context: PageContext, ids: Mapping[str, str]
) -> ReviewIssue:
    """Turn a problem the verifier found into a review issue.

    Parameters
    ----------
    problem
        The problem.
    context
        The page's context, for its index.
    ids
        The page's item and container IDs by ref.

    Returns
    -------
    ReviewIssue
        A ``verifier`` issue naming the problem's item when it names one the page
        has.
    """

    item_id = None if problem.item_ref is None else ids.get(problem.item_ref)
    return ReviewIssue(
        check="verifier",
        details={"category": problem.category, "item_ref": problem.item_ref},
        item_id=item_id,
        message=f"verifier: {problem.description}",
        page_index=context.page_index,
        step="extraction",
    )


def _verifier_outcome(verification: PageVerification) -> str:
    """Describe the verifier's review for the page's log line.

    Parameters
    ----------
    verification
        The verifier's review.

    Returns
    -------
    str
        ``passed``, ``corrected the extraction`` or such as ``found 2 problems``.
    """

    if verification.verdict.passed:
        return "passed"
    if verification.correction_applied:
        return "corrected the extraction"
    count = len(verification.verdict.problems)
    return f"found {count} problem{'' if count == 1 else 's'}"


async def _write_page(
    page_file: PageFile, *, context: PageContext, run: _StepRun
) -> None:
    """Write a page's figure crops, then its page file, then remove its old crops.

    Every file is written atomically, so a run stopped at any point leaves no
    partly written file, and a page file is written only after the crops it names.

    Parameters
    ----------
    page_file
        The page file.
    context
        The page's context, for cutting the crops.
    run
        The step's shared state.
    """

    named = set()
    for item in page_file.items:
        if item.figure is None:
            continue
        data = await run.worker.crop(
            box_pt=_crop_box(item.bbox, context=context),
            page_index=page_file.page_index,
            rotation=context.rotation,
        )
        write_bytes_atomic(data=data, path=run.output_folder / item.figure.crop)
        named.add(Path(item.figure.crop).name)

    write_model_atomic(
        model=page_file,
        path=run.output_folder / _page_file_name(page_file.page_index),
    )

    figures_folder = run.output_folder / FIGURES_FOLDER_NAME
    for old in figures_folder.glob(f"p{page_file.page_index:04d}-*.png"):
        if old.name not in named:
            old.unlink(missing_ok=True)
            logger.debug("Removed {path}, which the page no longer has", path=old)


# The folder in the output folder that holds the figure crops,
# ``figures/<item ID>.png``.
FIGURES_FOLDER_NAME = "figures"

# The folder in the output folder that holds the page files, ``pages/<NNNN>.json``.
PAGES_FOLDER_NAME = "pages"


@dataclass(frozen=True)
class PlannedPage:
    """A selected page: what its extraction depends on, and its page file if reused.

    Attributes
    ----------
    fingerprint
        The fingerprint of ``inputs``.
    inputs
        What the page's extraction depends on, its context included.
    saved
        The page file to reuse, or ``None`` when the page is to be extracted.
    """

    fingerprint: str
    inputs: PageInputs
    saved: PageFile | None

    @property
    def page_index(self) -> int:
        """The page (0-based)."""

        return self.inputs.context.page_index


async def extract_pages(
    *,
    model: StepModel,
    output_folder: Path,
    pages: Sequence[PlannedPage],
    pdf_path: Path,
) -> list[PageFile]:
    """Extract the planned pages that have no page file to reuse.

    The ``pages/`` and ``figures/`` folders are created if needed, and temporary
    files that an interrupted write left in them are removed first. At most
    ``advanced.extraction.concurrent_pages`` pages are extracted at once. When a page
    fails, the pages still running are canceled, no other page starts, and its
    error is raised; page files already written stay valid.

    Parameters
    ----------
    model
        The step's model and settings, from
        `pydelity.providers.factory.build_model`.
    output_folder
        The output folder.
    pages
        The selected pages, from `plan_pages`.
    pdf_path
        The PDF.

    Returns
    -------
    list[PageFile]
        Every selected page's page file, reused or new, in the order of ``pages``.

    Raises
    ------
    BudgetExceededError
        If a request would go over ``max_cost`` and the run was not allowed to.
    ExtractionError
        If a model refuses, runs out of output tokens, or never gives a usable
        answer for a page.
    ProviderError
        If a request fails after the provider retries.
    """

    for folder in (
        output_folder / PAGES_FOLDER_NAME,
        output_folder / FIGURES_FOLDER_NAME,
    ):
        folder.mkdir(exist_ok=True, parents=True)
        for leftover in remove_stale_temp_files(folder):
            logger.debug("Removed {path}, left by an interrupted write", path=leftover)

    to_extract = [page for page in pages if page.saved is None]
    extracted: dict[int, PageFile] = {}
    if to_extract:
        limit = asyncio.Semaphore(model.settings.concurrent_pages)
        async with PdfWorker(pdf_path) as worker:
            run = _StepRun(
                entries_before=len(
                    read_ledger(output_folder / LEDGER_FILE_NAME).entries
                ),
                model=model,
                output_folder=output_folder,
                worker=worker,
            )

            async def limited(page: PlannedPage) -> None:
                """Extract a page once fewer than the limit are running."""

                async with limit:
                    extracted[page.page_index] = await _extract_page(page, run=run)

            try:
                async with asyncio.TaskGroup() as group:
                    for page in to_extract:
                        group.create_task(limited(page))
            except ExceptionGroup as errors:
                # The task group cancels the other pages after the first error, which
                # is the one the step reports.
                first = errors.exceptions[0]
                raise first from first.__cause__

    return [
        page.saved if page.saved is not None else extracted[page.page_index]
        for page in pages
    ]


def page_context(*, config: Config, page_index: int, survey: PdfSurvey) -> PageContext:
    """Resolve what one page's requests are made from and its answers checked against.

    It never fails on a survey the survey step accepted. A page takes its direction
    and rotation from the first range inside the PDF that covers it, else the
    profile's default direction and no rotation. A repeated line on the page is
    page furniture when an artifact lists it, else content when the survey said so,
    else unclassified; IDs the facts do not have are ignored.

    Parameters
    ----------
    config
        The run's settings, for page extraction's instructions.
    page_index
        The page (0-based), which must be in the PDF.
    survey
        The survey, with its profile, its proposal and the facts it used.

    Returns
    -------
    PageContext
        The page's context.
    """

    facts, profile = survey.facts, survey.profile
    page_count = len(facts.pages)
    page = facts.pages[page_index]

    direction = covering_range(
        profile.writing_direction.ranges, page_count=page_count, page_index=page_index
    )
    rotation = covering_range(
        profile.rotation, page_count=page_count, page_index=page_index
    )

    # Being listed in an artifact wins over being listed as content.
    uses: dict[str, RepeatedLineUse] = {
        line.repeated_line_id: "content" for line in survey.proposal.non_artifact_lines
    }
    for artifact in survey.proposal.artifacts:
        uses.update(dict.fromkeys(artifact.repeated_line_ids, "artifact"))
    repeated_lines = [
        PageRepeatedLine(
            id=line.id,
            normalized=line.normalized,
            text=line.text,
            use=uses.get(line.id, "unclassified"),
        )
        for line in facts.repeated_lines
        if page_index in line.pages
    ]

    return PageContext(
        form_fields=[
            field for field in facts.form_fields or [] if field.page_index == page_index
        ],
        height_pt=page.height_pt,
        instructions=config.advanced.extraction.instructions,
        labels=profile.labels,
        languages=profile.languages,
        page_count=page_count,
        page_index=page_index,
        repeated_lines=repeated_lines,
        rotation=0 if rotation is None else rotation.degrees,
        rotation_attribute=page.rotation_attribute,
        text_quality=page.text.quality,
        width_pt=page.width_pt,
        writing_direction=(
            profile.writing_direction.default
            if direction is None
            else direction.direction
        ),
    )


def page_file_path(*, output_folder: Path, page_index: int) -> Path:
    """Return the path of a page's page file.

    Parameters
    ----------
    output_folder
        The output folder.
    page_index
        The page (0-based).

    Returns
    -------
    Path
        ``<output folder>/pages/<NNNN>.json``, with the page index in four or more
        digits.
    """

    return output_folder / _page_file_name(page_index)


def page_fingerprint(inputs: PageInputs) -> str:
    """Return the fingerprint of what a page's extraction depends on.

    Parameters
    ----------
    inputs
        The page's inputs.

    Returns
    -------
    str
        The ``sha256:`` fingerprint of the inputs and the page file's schema
        version.
    """

    return fingerprint(
        inputs.model_dump(mode="json") | {"schema_version": PAGE_SCHEMA_VERSION}
    )


def page_inputs(*, config: Config, page_index: int, survey: PdfSurvey) -> PageInputs:
    """Collect what a page's extraction with these settings depends on.

    Parameters
    ----------
    config
        The run's settings.
    page_index
        The page (0-based), which must be in the PDF.
    survey
        The survey, which also identifies the PDF.

    Returns
    -------
    PageInputs
        The inputs, as stored in the page file.
    """

    settings = config.advanced.extraction
    return PageInputs(
        context=page_context(config=config, page_index=page_index, survey=survey),
        model=config.extraction_model.setting,
        pdf_sha256=survey.inputs.pdf_sha256,
        prompt_version=PROMPT_VERSION,
        rendering=RENDERING_SETTINGS,
        settings=ExtractionSettings(
            check_retries=settings.check_retries,
            effort=settings.effort,
            max_output_tokens=settings.max_output_tokens,
        ),
    )


def plan_pages(
    *,
    config: Config,
    output_folder: Path,
    page_indexes: Sequence[int],
    survey: PdfSurvey,
) -> list[PlannedPage]:
    """Decide which selected pages to extract and which page files to reuse.

    A page file is reused when it is valid, its fingerprint matches the page's
    inputs and ``overwrite`` is not set. A damaged page file gives a warning.

    Parameters
    ----------
    config
        The run's settings.
    output_folder
        The output folder.
    page_indexes
        The selected pages (0-based), in page order.
    survey
        The survey.

    Returns
    -------
    list[PlannedPage]
        One entry per selected page, in the order of ``page_indexes``.
    """

    planned = []
    for page_index in page_indexes:
        inputs = page_inputs(config=config, page_index=page_index, survey=survey)
        expected = page_fingerprint(inputs)
        saved = _saved_page(output_folder=output_folder, page_index=page_index)
        reusable = (
            saved
            if saved is not None
            and saved.fingerprint == expected
            and not config.overwrite
            else None
        )
        planned.append(PlannedPage(fingerprint=expected, inputs=inputs, saved=reusable))

    reused = sum(page.saved is not None for page in planned)
    logger.info(
        "Page extraction: {selected} selected, {reused} reused, {extract} to extract",
        extract=len(planned) - reused,
        reused=reused,
        selected=f"{len(planned)} page" + ("" if len(planned) == 1 else "s"),
    )
    return planned

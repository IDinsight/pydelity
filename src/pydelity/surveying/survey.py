"""The survey step: reuse ``pdf_survey.json``, or ask the model and write a new one.

A valid ``pdf_survey.json`` whose fingerprint matches the survey's inputs is reused
unless ``overwrite`` is set. Otherwise the model surveys the PDF, and Python builds the
profile from its accepted answer. It adds the ``other`` label, merges the languages,
keeps the user's instructions and converts region boxes to points.
"""

# Standard Library
from decimal import Decimal
from pathlib import Path

# Third Party Library
from loguru import logger

# Package Library
from pydelity.config.schemas import Config, is_language_tag, standard_language_tag
from pydelity.costs.budget import format_usd
from pydelity.costs.ledger import LEDGER_FILE_NAME, read_ledger
from pydelity.providers.ledger_model import LedgerModel
from pydelity.providers.profiles import PdfTransport
from pydelity.schema_versions import SURVEY_SCHEMA_VERSION
from pydelity.surveying.llm import ask_model
from pydelity.surveying.prompts import PROMPT_VERSION
from pydelity.surveying.schemas import (
    Facts,
    ItemKind,
    ItemRole,
    Label,
    PdfFacts,
    PdfSurvey,
    Profile,
    Proposal,
    Region,
    SurveyAnswer,
    SurveyInputs,
    SurveySettings,
)
from pydelity.surveying.validators import check_results, review_issues, run_checks
from pydelity.utils.coroutines import warn
from pydelity.utils.files import load_model, write_model_atomic
from pydelity.utils.fingerprints import fingerprint
from pydelity.utils.pdf import PdfInfo

# The label for content that no other label fits, which every profile has.
_OTHER_LABEL = Label(
    description="Content that no other label fits.",
    kinds=list(ItemKind),
    name="other",
    role=ItemRole.BODY,
)

# The survey's file name in the output folder.
SURVEY_FILE_NAME = "pdf_survey.json"


def _describe(survey: PdfSurvey) -> str:
    """Describe a survey's labels, languages, rotation and review issues on one line.

    Parameters
    ----------
    survey
        The survey.

    Returns
    -------
    str
        Such as ``labels heading, body, other; languages en; rotation none; 0 review
        issues``.
    """

    profile = survey.profile
    labels = ", ".join(label.name for label in profile.labels)
    languages = ", ".join(profile.languages) or "none"
    rotation = (
        ", ".join(
            f"pages {turn.first_page_index}-{turn.last_page_index} by {turn.degrees} "
            "degrees"
            for turn in profile.rotation
        )
        or "none"
    )
    issues = len(survey.issues)
    return (
        f"labels {labels}; languages {languages}; rotation {rotation}; {issues} review "
        f"issue{'' if issues == 1 else 's'}"
    )


def _labels(answer: SurveyAnswer) -> list[Label]:
    """Build the profile's labels from the model's, with ``other`` last.

    A label with an empty name, or whose name an earlier label already uses regardless
    of case, is left out, and so is a model-made ``other``. A label without kinds may
    be given to every kind. Check C1 reports each of these as a review issue.

    Parameters
    ----------
    answer
        The accepted answer.

    Returns
    -------
    list[Label]
        The labels, names trimmed, each kind listed once.
    """

    labels = []
    seen = {_OTHER_LABEL.name}
    for label in answer.labels:
        name = label.name.strip()
        if not name or name.casefold() in seen:
            continue
        seen.add(name.casefold())
        kinds = list(dict.fromkeys(label.kinds)) or list(ItemKind)
        labels.append(label.model_copy(update={"kinds": kinds, "name": name}))
    return [*labels, _OTHER_LABEL]


def _languages(answer: SurveyAnswer, user_languages: list[str]) -> list[str]:
    """Merge the user's languages with the model's, all in standard form.

    Parameters
    ----------
    answer
        The accepted answer.
    user_languages
        The user's languages, already in standard form.

    Returns
    -------
    list[str]
        The user's languages, then the model's valid tags not already listed. Tags
        that check C7 rejects are left out.
    """

    languages = list(user_languages)
    for tag in answer.languages:
        if not is_language_tag(tag):
            continue
        standard = standard_language_tag(tag)
        if standard not in languages:
            languages.append(standard)
    return languages


def _regions(
    *, answer: SurveyAnswer, facts: Facts, labels: list[Label]
) -> list[Region]:
    """Convert the answer's region boxes from page fractions to points.

    A region on a page the PDF does not have is left out, since its box cannot be
    converted; check C2 reports it. A region's label takes the spelling of the
    profile label it names regardless of case.

    Parameters
    ----------
    answer
        The accepted answer.
    facts
        The measured facts, for each displayed page's size.
    labels
        The profile's labels.

    Returns
    -------
    list[Region]
        The regions, with boxes in points rounded to 0.01.
    """

    names = {label.name.casefold(): label.name for label in labels}
    regions = []
    for region in answer.regions:
        if not 0 <= region.page_index < len(facts.pages):
            continue
        page = facts.pages[region.page_index]
        box = region.bbox
        regions.append(
            Region(
                bbox=(
                    round(box.x0 * page.width_pt, 2),
                    round(box.y0 * page.height_pt, 2),
                    round(box.x1 * page.width_pt, 2),
                    round(box.y1 * page.height_pt, 2),
                ),
                label=names.get(region.label.strip().casefold(), region.label),
                note=region.note,
                page_index=region.page_index,
            )
        )
    return regions


def _spent_since(*, entries_before: int, ledger_path: Path) -> str:
    """Describe what the requests recorded after a point in ``cost.jsonl`` cost.

    Parameters
    ----------
    entries_before
        How many entries ``cost.jsonl`` held before the requests.
    ledger_path
        The output folder's ``cost.jsonl``.

    Returns
    -------
    str
        Such as ``$0.31 for 2 requests``, or ``unknown`` when a request's price is not
        known.
    """

    entries = read_ledger(ledger_path).entries[entries_before:]
    count = f"{len(entries)} request{'' if len(entries) == 1 else 's'}"
    costs = [entry.cost_usd for entry in entries]
    if any(cost is None for cost in costs):
        return f"unknown for {count}"
    total = sum((cost for cost in costs if cost is not None), start=Decimal(0))
    return f"{format_usd(total)} for {count}"


def build_survey(
    *, answer: SurveyAnswer, attempts: int, config: Config, facts: PdfFacts
) -> PdfSurvey:
    """Build ``pdf_survey.json`` from the model's accepted answer.

    Parameters
    ----------
    answer
        The accepted answer.
    attempts
        How many answers the model gave.
    config
        The run's settings.
    facts
        The measured facts the answer was checked against.

    Returns
    -------
    PdfSurvey
        The survey, with the checks' results on the answer and a review issue for each
        failure.
    """

    checks = check_results(run_checks(answer, facts.facts), attempts=attempts)
    labels = _labels(answer)
    inputs = survey_inputs(config=config, facts=facts)
    return PdfSurvey(
        checks=checks,
        facts=facts.facts,
        fingerprint=survey_fingerprint(inputs),
        inputs=inputs,
        issues=review_issues(checks),
        profile=Profile(
            continuation_notes=answer.continuation_notes,
            labels=labels,
            languages=_languages(answer, config.languages),
            page_numbering=answer.page_numbering,
            rotation=answer.rotation,
            start_markers=answer.start_markers,
            user_instructions=config.instructions,
            writing_direction=answer.writing_direction,
        ),
        proposal=Proposal(
            artifacts=answer.artifacts,
            non_artifact_lines=answer.non_artifact_lines,
            notes=answer.notes,
            regions=_regions(answer=answer, facts=facts.facts, labels=labels),
        ),
        schema_version=SURVEY_SCHEMA_VERSION,
    )


async def run_survey(
    *,
    config: Config,
    facts: PdfFacts,
    model: LedgerModel,
    output_folder: Path,
    pdf: PdfInfo,
) -> tuple[PdfSurvey, PdfTransport]:
    """Ask the model to survey the PDF and write ``pdf_survey.json`` atomically.

    Parameters
    ----------
    config
        The run's settings.
    facts
        The measured facts.
    model
        The step's model.
    output_folder
        The output folder.
    pdf
        The PDF.

    Returns
    -------
    tuple[PdfSurvey, PdfTransport]
        The survey, as written to ``pdf_survey.json``, and how the last request
        carried the PDF.

    Raises
    ------
    BudgetExceededError
        If a request could go over ``max_cost`` and the decision is no.
    ProviderError
        If the provider rejects the upload for an invalid API key or as too large, or
        a request fails after the provider retries.
    SurveyError
        If the model refuses, runs out of output tokens, or never gives an answer that
        matches the survey's answer format.
    """

    ledger_path = output_folder / LEDGER_FILE_NAME
    entries_before = len(read_ledger(ledger_path).entries)
    surveyed = await ask_model(
        config=config, facts=facts, model=model, output_folder=output_folder, pdf=pdf
    )
    survey = build_survey(
        answer=surveyed.answer,
        attempts=surveyed.attempts,
        config=config,
        facts=facts,
    )
    path = output_folder / SURVEY_FILE_NAME
    write_model_atomic(model=survey, path=path)
    logger.info(
        "Survey finished: {description}; cost {cost}. Saved to {path}",
        cost=_spent_since(entries_before=entries_before, ledger_path=ledger_path),
        description=_describe(survey),
        path=path,
    )
    return survey, surveyed.attachment.transport


def saved_survey(
    *, config: Config, facts: PdfFacts, output_folder: Path
) -> PdfSurvey | None:
    """Return the saved survey if it can be reused.

    It can be reused when ``pdf_survey.json`` is valid, its fingerprint matches the
    survey's inputs and ``overwrite`` is not set. A damaged file gives a warning.

    Parameters
    ----------
    config
        The run's settings.
    facts
        The measured facts the survey would use.
    output_folder
        The output folder.

    Returns
    -------
    PdfSurvey | None
        The saved survey, or ``None`` when the survey must run.
    """

    path = output_folder / SURVEY_FILE_NAME
    saved = load_model(model_type=PdfSurvey, path=path)
    if saved.damage is not None:
        warn(
            f"{saved.damage}; running the survey again",
            code="damaged_output",
            details={"file": SURVEY_FILE_NAME},
        )
    expected = survey_fingerprint(survey_inputs(config=config, facts=facts))
    if saved.model is None or saved.model.fingerprint != expected or config.overwrite:
        return None

    logger.info(
        "Survey reused from {path}: {description}",
        description=_describe(saved.model),
        path=path,
    )
    return saved.model


def survey_fingerprint(inputs: SurveyInputs) -> str:
    """Return the fingerprint of what a survey depends on.

    Parameters
    ----------
    inputs
        The survey's inputs.

    Returns
    -------
    str
        The ``sha256:`` fingerprint of the PDF's SHA-256, the facts' fingerprint, the
        model, the user's instructions and languages, the survey settings, the prompt
        version and the survey schema version.
    """

    return fingerprint(
        inputs.model_dump(
            include={
                "facts_fingerprint",
                "instructions",
                "languages",
                "model",
                "pdf_sha256",
                "prompt_version",
                "settings",
            },
            mode="json",
        )
        | {"schema_version": SURVEY_SCHEMA_VERSION}
    )


def survey_inputs(*, config: Config, facts: PdfFacts) -> SurveyInputs:
    """Collect what a survey of the PDF with these settings is made from.

    Parameters
    ----------
    config
        The run's settings.
    facts
        The measured facts, which also identify the PDF.

    Returns
    -------
    SurveyInputs
        The inputs, as stored in ``pdf_survey.json``.
    """

    survey_settings = config.advanced.survey
    return SurveyInputs(
        facts_fingerprint=facts.fingerprint,
        instructions=config.instructions,
        languages=config.languages,
        model=config.model_choice.setting,
        page_count=facts.pdf.page_count,
        pdf_bytes=facts.pdf.bytes,
        pdf_name=facts.pdf.name,
        pdf_sha256=facts.pdf.sha256,
        prompt_version=PROMPT_VERSION,
        settings=SurveySettings(
            check_retries=survey_settings.check_retries,
            effort=survey_settings.effort,
            max_output_tokens=survey_settings.max_output_tokens,
        ),
    )

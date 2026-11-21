"""pydelity's Python API.

Each function has an async version whose name starts with ``a``, such as `arun`, and a
sync version without the ``a``, such as `run`. Both take the same arguments and give
the same results, errors and warnings. The sync version runs the async one with
`asyncio.run`, so it cannot be called while an event loop is running, as in a Jupyter
cell or async code. Await the async version there instead. `load` is sync only and
works anywhere.

- `measure` measures the PDF and saves ``pdf_facts.json``, with no API key or model.
- `estimate` estimates the cost of a run and writes nothing.
- `survey` runs the survey step alone and saves ``pdf_survey.json``.
- `extract` extracts the selected pages, running or reusing the survey first, and
  saves a page file for each in ``pages/``.
- `run` runs the whole pipeline and records it in ``run.json`` and ``report.html``.
- `load` reads an output folder back.

None of them prompts for input. The ``pydelity`` command calls `arun_with_questions`
instead, which can ask for confirmation on the terminal before spending money on model
requests. Every function except `load` turns PydanticAI's first-run banner off before
any model is asked, since pydelity's agents are its own.
"""

# Standard Library
import json
import os

from pathlib import Path

# Third Party Library
import pydantic_ai

from loguru import logger

# Package Library
from pydelity.config.loading import ConfigSource, resolve_config
from pydelity.config.schemas import Config
from pydelity.costs.budget import OverMaxCostDecision
from pydelity.costs.schemas import CostEstimate, MaxCostWarning
from pydelity.extracting.schemas import PageFile
from pydelity.pipeline.runner import (
    SpendConfirmation,
    load_run,
    run_estimate,
    run_extraction_step,
    run_measure,
    run_pipeline,
    run_survey_step,
)
from pydelity.pipeline.schemas import RunResult
from pydelity.surveying.schemas import PdfFacts, PdfSurvey
from pydelity.utils.coroutines import run_sync


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


def _resolve(
    *,
    config: ConfigSource | None,
    pdf: str | os.PathLike[str] | None,
    settings: dict[str, object],
) -> Config:
    """Turn PydanticAI's banner off, then combine and check the settings, and log them.

    Parameters
    ----------
    config
        A config file, a `pydelity.config.schemas.Config`, or a mapping of settings.
    pdf
        The PDF, which overrides a ``pdf`` in ``config``.
    settings
        Settings by name, which override ``config``.

    Returns
    -------
    Config
        The checked settings.

    Raises
    ------
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read.
    """

    # PydanticAI documents setting this flag, but declares it without a type, so ty
    # reads it as always true.
    pydantic_ai.BANNER_ENABLED = False  # ty: ignore[invalid-assignment]
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
    return resolved


async def aestimate(
    pdf: str | os.PathLike[str] | None = None,
    *,
    config: ConfigSource | None = None,
    **settings: object,
) -> CostEstimate:
    """Estimate what a run on a PDF would cost, writing nothing and calling no model.

    The saved facts are used when they match, and otherwise the PDF is measured
    without saving them. A survey or page file that would be reused costs nothing.
    The estimate covers page extraction whenever the run would extract pages: the
    selected pages without a page file to reuse, or every selected page when the
    survey runs first and the run would not pause. No API key is needed.

    Parameters
    ----------
    pdf
        The PDF. Overrides a ``pdf`` in ``config``.
    config
        A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a mapping
        of settings.
    **settings
        Settings by name, such as ``model="openai:gpt-6.2-astra"``. They override
        ``config``.

    Returns
    -------
    CostEstimate
        The expected and largest cost, the output folder's spend so far, and whether
        the run would go over ``max_cost``.

    Raises
    ------
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read,
        or ``pages`` naming a page past the PDF's last page.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    """

    resolved = _resolve(config=config, pdf=pdf, settings=settings)
    return await run_estimate(config=resolved)


async def aextract(
    pdf: str | os.PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> list[PageFile]:
    """Extract a PDF's selected pages, running or reusing the survey first.

    The survey saved in ``pdf_survey.json`` is reused when its inputs are unchanged;
    otherwise the survey runs. Then each selected page's page file is reused when
    its inputs are unchanged, and the other pages are extracted, several at a time,
    and saved in ``pages/``, with figure images in ``figures/``. It never pauses,
    writes no ``run.json`` and no report, and does not prompt for input.

    Parameters
    ----------
    pdf
        The PDF. Overrides a ``pdf`` in ``config``.
    allow_over_max_cost
        Whether to continue, with a warning, when the run could exceed ``max_cost``.
        If false, such a run raises `BudgetExceededError` instead.
    config
        A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a mapping
        of settings.
    **settings
        Settings by name, such as ``pages="1-5,8"`` or
        ``advanced={"extraction": {"concurrent_pages": 4}}``. They override
        ``config``.

    Returns
    -------
    list[PageFile]
        The selected pages' page files, in page order.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and ``allow_over_max_cost`` is not set.
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read,
        or ``pages`` naming a page past the PDF's last page.
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
    SurveyError
        If the survey's model refuses, runs out of output tokens, or never gives an
        answer that matches the survey's answer format.
    """

    resolved = _resolve(config=config, pdf=pdf, settings=settings)
    return await run_extraction_step(
        config=resolved, decide_over_max_cost=_fixed_decision(allow_over_max_cost)
    )


async def ameasure(
    pdf: str | os.PathLike[str] | None = None,
    *,
    config: ConfigSource | None = None,
    **settings: object,
) -> PdfFacts:
    """Measure a PDF and save ``pdf_facts.json``, or reuse the saved facts.

    No API key is needed and no model is called. Only the ``pdf``, ``output_dir``
    and ``overwrite`` settings matter, though every setting is checked.

    Parameters
    ----------
    pdf
        The PDF. Overrides a ``pdf`` in ``config``.
    config
        A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a mapping
        of settings.
    **settings
        Settings by name, such as ``output_dir="out/w9"``. They override ``config``.

    Returns
    -------
    PdfFacts
        The facts, as saved in ``pdf_facts.json``.

    Raises
    ------
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    """

    resolved = _resolve(config=config, pdf=pdf, settings=settings)
    return await run_measure(config=resolved)


async def arun(
    pdf: str | os.PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> RunResult:
    """Run pydelity on a PDF.

    The run validates the settings, opens the PDF and measures it, or reuses the facts
    saved in ``pdf_facts.json`` in the output folder. It then reuses the survey saved
    in ``pdf_survey.json`` when its inputs are unchanged. Otherwise it checks the
    providers' API keys and the cost estimate against ``max_cost``, uploads the PDF
    (or reuses its upload from ``uploads.json``), asks the model to survey it and saves
    ``pdf_survey.json``. With ``pause`` on, the default, a run that made a new survey
    ends there with status ``paused``, so the survey can be checked first; the next
    run goes on. Page extraction then reuses or writes a page file in ``pages/`` for
    each selected page. The run is recorded in ``run.json`` and ``report.html``, also
    when it fails, stops or pauses, and does not prompt for input.

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
        Settings by name, such as ``model="openai:gpt-6.2-astra"``, ``pages="1-5"``,
        ``pause=False`` or ``advanced={"survey": {"effort": "medium"}}``. They
        override ``config``.

    Returns
    -------
    RunResult
        The run's record, facts, survey, selected pages' page files and the output
        folder's ledger.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and ``allow_over_max_cost`` is not set.
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read,
        or ``pages`` naming a page past the PDF's last page.
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
    SurveyError
        If the model refuses, runs out of output tokens, or never gives an answer that
        matches the survey's answer format.
    """

    return await arun_with_questions(
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
) -> RunResult:
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

    Returns
    -------
    RunResult
        The run's record, facts, survey, selected pages' page files and the output
        folder's ledger.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and the decision is no.
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read,
        or ``pages`` naming a page past the PDF's last page.
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

    resolved = _resolve(config=config, pdf=pdf, settings=settings)
    return await run_pipeline(
        config=resolved, confirm=confirm, decide_over_max_cost=decide_over_max_cost
    )


async def asurvey(
    pdf: str | os.PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> PdfSurvey:
    """Run the survey step alone and save ``pdf_survey.json``, or reuse the saved one.

    It writes ``pdf_facts.json``, ``pdf_survey.json`` and the ledger lines of its
    requests, but no ``run.json`` and no report. It does not prompt for input.

    Parameters
    ----------
    pdf
        The PDF. Overrides a ``pdf`` in ``config``.
    allow_over_max_cost
        Whether to continue, with a warning, when the survey could exceed
        ``max_cost``. If false, such a survey raises `BudgetExceededError` instead.
    config
        A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a mapping
        of settings.
    **settings
        Settings by name, such as ``model="openai:gpt-6.2-astra"``. They override
        ``config``.

    Returns
    -------
    PdfSurvey
        The survey, as saved in ``pdf_survey.json``.

    Raises
    ------
    BudgetExceededError
        If the survey could go over ``max_cost`` and ``allow_over_max_cost`` is not
        set.
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read.
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

    resolved = _resolve(config=config, pdf=pdf, settings=settings)
    return await run_survey_step(
        config=resolved, decide_over_max_cost=_fixed_decision(allow_over_max_cost)
    )


def estimate(
    pdf: str | os.PathLike[str] | None = None,
    *,
    config: ConfigSource | None = None,
    **settings: object,
) -> CostEstimate:
    """Estimate what a run on a PDF would cost (the sync version of `aestimate`).

    Parameters
    ----------
    pdf
        The PDF. Overrides a ``pdf`` in ``config``.
    config
        A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a mapping
        of settings.
    **settings
        Settings by name. They override ``config``.

    Returns
    -------
    CostEstimate
        The expected and largest cost, the output folder's spend so far, and whether
        the run would go over ``max_cost``.

    Raises
    ------
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read,
        or ``pages`` naming a page past the PDF's last page.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    RuntimeError
        If called while an event loop is running, as in Jupyter or async code. Use
        ``await pydelity.aestimate(...)`` there instead.
    """

    return run_sync(aestimate, config=config, pdf=pdf, **settings)


def extract(
    pdf: str | os.PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> list[PageFile]:
    """Extract a PDF's selected pages (the sync version of `aextract`).

    Parameters
    ----------
    pdf
        The PDF. Overrides a ``pdf`` in ``config``.
    allow_over_max_cost
        Whether to continue, with a warning, when the run could exceed ``max_cost``.
        If false, such a run raises `BudgetExceededError` instead.
    config
        A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a mapping
        of settings.
    **settings
        Settings by name. They override ``config``.

    Returns
    -------
    list[PageFile]
        The selected pages' page files, in page order.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and ``allow_over_max_cost`` is not set.
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read,
        or ``pages`` naming a page past the PDF's last page.
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
    RuntimeError
        If called while an event loop is running, as in Jupyter or async code. Use
        ``await pydelity.aextract(...)`` there instead.
    SurveyError
        If the survey's model refuses, runs out of output tokens, or never gives an
        answer that matches the survey's answer format.
    """

    return run_sync(
        aextract,
        allow_over_max_cost=allow_over_max_cost,
        config=config,
        pdf=pdf,
        **settings,
    )


def load(output_dir: str | os.PathLike[str]) -> RunResult:
    """Read an output folder back as Python objects.

    It calls no model, needs no API key and writes nothing, so it works anywhere,
    including in a running event loop.

    Parameters
    ----------
    output_dir
        The output folder of an earlier `run`, `survey` or `measure`.

    Returns
    -------
    RunResult
        The folder's ``run.json``, ``pdf_facts.json``, ``pdf_survey.json``,
        ``cost.jsonl``, and the page files in ``pages/`` made from the PDF in
        ``pdf_facts.json``, in page order. A part is ``None``, or empty, when its
        files are absent; the pages are empty without ``pdf_facts.json``.

    Raises
    ------
    OutputError
        If the folder does not exist, holds none of those files, or holds one that
        is not valid JSON, does not match its schema or has another major schema
        version, or a page file of the folder's PDF names a figure image that is
        missing.
    """

    return load_run(Path(output_dir))


def measure(
    pdf: str | os.PathLike[str] | None = None,
    *,
    config: ConfigSource | None = None,
    **settings: object,
) -> PdfFacts:
    """Measure a PDF and save ``pdf_facts.json`` (the sync version of `ameasure`).

    Parameters
    ----------
    pdf
        The PDF. Overrides a ``pdf`` in ``config``.
    config
        A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a mapping
        of settings.
    **settings
        Settings by name. They override ``config``.

    Returns
    -------
    PdfFacts
        The facts, as saved in ``pdf_facts.json``.

    Raises
    ------
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    RuntimeError
        If called while an event loop is running, as in Jupyter or async code. Use
        ``await pydelity.ameasure(...)`` there instead.
    """

    return run_sync(ameasure, config=config, pdf=pdf, **settings)


def run(
    pdf: str | os.PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> RunResult:
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
        Settings by name, such as ``model="openai:gpt-6.2-astra"``, ``pages="1-5"``,
        ``pause=False`` or ``advanced={"survey": {"effort": "medium"}}``. They
        override ``config``.

    Returns
    -------
    RunResult
        The run's record, facts, survey, selected pages' page files and the output
        folder's ledger.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and ``allow_over_max_cost`` is not set.
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read,
        or ``pages`` naming a page past the PDF's last page.
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
    RuntimeError
        If called while an event loop is running, as in Jupyter or async code. Use
        ``await pydelity.arun(...)`` there instead.
    SurveyError
        If the model refuses, runs out of output tokens, or never gives an answer that
        matches the survey's answer format.
    """

    return run_sync(
        arun,
        allow_over_max_cost=allow_over_max_cost,
        config=config,
        pdf=pdf,
        **settings,
    )


def survey(
    pdf: str | os.PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> PdfSurvey:
    """Run the survey step alone (the sync version of `asurvey`).

    Parameters
    ----------
    pdf
        The PDF. Overrides a ``pdf`` in ``config``.
    allow_over_max_cost
        Whether to continue, with a warning, when the survey could exceed
        ``max_cost``. If false, such a survey raises `BudgetExceededError` instead.
    config
        A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a mapping
        of settings.
    **settings
        Settings by name. They override ``config``.

    Returns
    -------
    PdfSurvey
        The survey, as saved in ``pdf_survey.json``.

    Raises
    ------
    BudgetExceededError
        If the survey could go over ``max_cost`` and ``allow_over_max_cost`` is not
        set.
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read.
    MissingApiKeyError
        If the selected provider's API key is not set.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    ProviderError
        If the provider rejects the upload for an invalid API key or as too large, or
        a request fails after the provider retries.
    RuntimeError
        If called while an event loop is running, as in Jupyter or async code. Use
        ``await pydelity.asurvey(...)`` there instead.
    SurveyError
        If the model refuses, runs out of output tokens, or never gives an answer that
        matches the survey's answer format.
    """

    return run_sync(
        asurvey,
        allow_over_max_cost=allow_over_max_cost,
        config=config,
        pdf=pdf,
        **settings,
    )

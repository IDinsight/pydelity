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
- `run` runs the whole pipeline and records it in ``run.json`` and ``report.html``.
- `load` reads an output folder back.

None of them prompts for input. The ``pydelity`` command calls `arun_with_questions`
instead, which can ask for confirmation on the terminal before spending money on model
requests.
"""

# Standard Library
import json
import os

from pathlib import Path

# Third Party Library
from loguru import logger

# Package Library
from pydelity.config.loading import ConfigSource, resolve_config
from pydelity.config.schemas import Config
from pydelity.costs.budget import OverMaxCostDecision
from pydelity.costs.schemas import CostEstimate, MaxCostWarning
from pydelity.pipeline.runner import (
    SpendConfirmation,
    load_run,
    run_estimate,
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
    """Combine and check the settings, and log them.

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
    without saving them. A survey that would be reused costs nothing. No API key is
    needed.

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
        Listing every invalid setting, or naming a config file that cannot be read.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    """

    resolved = _resolve(config=config, pdf=pdf, settings=settings)
    return await run_estimate(config=resolved)


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
    provider's API key and the cost estimate against ``max_cost``, uploads the PDF (or
    reuses its upload from ``uploads.json``), asks the model to survey it and saves
    ``pdf_survey.json``. It records the run in ``run.json`` and ``report.html``, also
    when it fails or stops, and does not prompt for input.

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

    Returns
    -------
    RunResult
        The run's record, facts, survey and the output folder's ledger.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and ``allow_over_max_cost`` is not set.
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
        The run's record, facts, survey and the output folder's ledger.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and the decision is no.
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read.
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
        Listing every invalid setting, or naming a config file that cannot be read.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    RuntimeError
        If called while an event loop is running, as in Jupyter or async code. Use
        ``await pydelity.aestimate(...)`` there instead.
    """

    return run_sync(aestimate, config=config, pdf=pdf, **settings)


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
        The folder's ``run.json``, ``pdf_facts.json``, ``pdf_survey.json`` and
        ``cost.jsonl``. A part is ``None``, or an empty ledger, when its file is
        absent.

    Raises
    ------
    OutputError
        If the folder does not exist, holds none of those files, or holds one that
        is not valid JSON, does not match its schema or has another major schema
        version.
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
        Settings by name, such as ``model="openai:gpt-6.2-astra"`` or
        ``advanced={"survey": {"effort": "medium"}}``. They override ``config``.

    Returns
    -------
    RunResult
        The run's record, facts, survey and the output folder's ledger.

    Raises
    ------
    BudgetExceededError
        If the run could go over ``max_cost`` and ``allow_over_max_cost`` is not set.
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

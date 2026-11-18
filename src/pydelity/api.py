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
import json
import os

# Third Party Library
from loguru import logger

# Package Library
from pydelity.config.loading import ConfigSource, resolve_config
from pydelity.costs.budget import OverMaxCostDecision
from pydelity.costs.schemas import MaxCostWarning
from pydelity.pipeline.runner import SpendConfirmation, run_pipeline
from pydelity.pipeline.schemas import RunResult
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
    ``pdf_survey.json``. It records the run in ``run.json``, also when it fails or
    stops, and does not prompt for input.

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

    return await run_pipeline(
        config=resolved, confirm=confirm, decide_over_max_cost=decide_over_max_cost
    )


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

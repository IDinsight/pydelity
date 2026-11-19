"""pydelity: PDF to structured JSON, faithfully.

Importing pydelity does not read settings or environment variables, and does not log.
pydelity logs through loguru, with its messages disabled by default. Call
``loguru.logger.enable("pydelity")`` to see them. The ``pydelity`` command enables
them itself.
"""

# Standard Library
from importlib.metadata import version as _distribution_version

# Third Party Library
from loguru import logger as _logger

# Package Library
from pydelity.api import (
    aestimate,
    ameasure,
    arun,
    asurvey,
    estimate,
    load,
    measure,
    run,
    survey,
)
from pydelity.config.schemas import Config
from pydelity.costs.schemas import CostEstimate
from pydelity.errors import (
    BudgetExceededError,
    ConfigError,
    MissingApiKeyError,
    OutputError,
    PdfError,
    ProviderError,
    PydelityError,
    PydelityWarning,
    SurveyError,
)
from pydelity.pipeline.schemas import RunRecord, RunResult
from pydelity.surveying.schemas import PdfFacts, PdfSurvey

__all__ = [
    "BudgetExceededError",
    "Config",
    "ConfigError",
    "CostEstimate",
    "MissingApiKeyError",
    "OutputError",
    "PdfError",
    "PdfFacts",
    "PdfSurvey",
    "ProviderError",
    "PydelityError",
    "PydelityWarning",
    "RunRecord",
    "RunResult",
    "SurveyError",
    "__version__",
    "aestimate",
    "ameasure",
    "arun",
    "asurvey",
    "estimate",
    "load",
    "measure",
    "run",
    "survey",
]

__version__ = _distribution_version("pydelity")

# Keep pydelity's log messages off until the caller enables them.
_logger.disable("pydelity")

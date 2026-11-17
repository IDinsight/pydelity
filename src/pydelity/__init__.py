"""pydelity: PDF to structured JSON, faithfully.

Importing pydelity builds no settings, reads no environment variables and logs nothing.
Its log messages go through loguru and stay off until the caller turns them on with
``loguru.logger.enable("pydelity")``; the ``pydelity`` command turns them on itself.
"""

# Standard Library
from importlib.metadata import version as _distribution_version

# Third Party Library
from loguru import logger as _logger

# Package Library
from pydelity.api import arun, run
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

__all__ = [
    "BudgetExceededError",
    "ConfigError",
    "MissingApiKeyError",
    "OutputError",
    "PdfError",
    "ProviderError",
    "PydelityError",
    "PydelityWarning",
    "SurveyError",
    "__version__",
    "arun",
    "run",
]

__version__ = _distribution_version("pydelity")

# A library logs nothing unless its caller asks.
_logger.disable("pydelity")

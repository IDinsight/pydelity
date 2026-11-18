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

# Keep pydelity's log messages off until the caller enables them.
_logger.disable("pydelity")

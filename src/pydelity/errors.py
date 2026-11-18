"""Exceptions and the warning category that pydelity raises.

Every error pydelity raises deliberately is a `PydelityError`, so callers can catch
all of them with one ``except`` clause, or each kind separately.
"""


class PydelityError(Exception):
    """Base class for every error pydelity raises deliberately."""


class BudgetExceededError(PydelityError):
    """A run would go over ``max_cost`` and the caller did not allow it."""


class ConfigError(PydelityError):
    """One or more settings are invalid."""


class MissingApiKeyError(PydelityError):
    """The API key for the selected model provider is missing or empty."""


class OutputError(PydelityError):
    """An output folder, or a file in it, cannot be read back."""


class PdfError(PydelityError):
    """The PDF is missing, empty, password-protected or cannot be opened."""


class ProviderError(PydelityError):
    """A model provider failed or rejected a request after its retries."""


class SurveyError(PydelityError):
    """The survey step could not produce a usable answer."""


class PydelityWarning(UserWarning):
    """A problem the user should know about that does not stop the run."""

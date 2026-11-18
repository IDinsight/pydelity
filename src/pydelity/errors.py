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
    """A model provider failed or rejected a request after its retries.

    Parameters
    ----------
    message
        The error's text: the provider and model, then the provider's message.
    model
        The model ID the request was for.
    provider
        The provider, ``anthropic`` or ``openai``.
    provider_message
        The provider's own error message, unchanged, or the exception's text when the
        provider sent none.
    status_code
        The HTTP status code, or ``None`` for a connection error or timeout.
    temporary
        Whether the failure is of a kind the provider's SDK retries: a connection
        error, a timeout, or HTTP 408, 409, 429 or 5xx.
    upload_error
        The earlier upload error, when the request fell back to sending the PDF in
        the request itself; otherwise ``None``.
    """

    def __init__(  # noqa: PLR0913 - one argument per field the error carries
        self,
        message: str,
        *,
        model: str,
        provider: str,
        provider_message: str,
        status_code: int | None,
        temporary: bool,
        upload_error: str | None = None,
    ) -> None:
        """Set the error's message and fields."""

        super().__init__(message)
        self.model = model
        self.provider = provider
        self.provider_message = provider_message
        self.status_code = status_code
        self.temporary = temporary
        self.upload_error = upload_error


class SurveyError(PydelityError):
    """The survey step could not produce a usable answer."""


class PydelityWarning(UserWarning):
    """A problem the user should know about that does not stop the run."""

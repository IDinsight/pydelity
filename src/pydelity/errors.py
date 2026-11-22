"""Exceptions, the warning category, and the codes for warnings and exit status.

Every error pydelity raises deliberately is a `PydelityError`, so callers can catch
all of them with one ``except`` clause, or each kind separately. `WarningCode` names
each kind of `PydelityWarning` as ``run.json`` records it, and `ExitCode` gives the
``pydelity`` command's exit status.
"""

# Standard Library
from enum import IntEnum
from typing import Literal

# The kinds of user-facing warning, as ``run.json`` records them.
type WarningCode = Literal[
    "damaged_output",
    "max_cost_exceeded",
    "missing_page_files",
    "other_pdf_in_folder",
    "probe_unavailable",
    "unpriced_model",
    "upload_fallback",
]


class PydelityError(Exception):
    """Base class for every error pydelity raises deliberately."""


class BudgetExceededError(PydelityError):
    """A run would go over ``max_cost`` and the caller did not allow it."""


class ConfigError(PydelityError):
    """One or more settings are invalid."""


class ExitCode(IntEnum):
    """The ``pydelity`` command's exit status."""

    COMPLETED = 0
    """The run completed, with or without review issues."""

    FAILED = 1
    """The run failed: a provider error, a survey, page extraction or page-break
    verification error, or an unexpected error."""

    INTERRUPTED = 130
    """The run was interrupted with Ctrl+C."""

    INVALID_INPUT = 2
    """A setting, the API key or the PDF is invalid."""

    STOPPED = 3
    """The run stopped at the user's answer, or because input is not a terminal and
    ``--yes`` was not given."""


class ExtractionError(PydelityError):
    """Page extraction could not get a usable answer for a page.

    The model refused, ran out of output tokens, or never gave an answer that matches
    the answer format. The message names the page and the model's role in it, the
    extraction model or the verifier.
    """


class MissingApiKeyError(PydelityError):
    """The API key for the selected model provider is missing or empty."""


class OutputError(PydelityError):
    """An output folder, or a file in it, cannot be read back."""


class PageBreakError(PydelityError):
    """Page-break verification could not get a usable verdict for a page break.

    The model refused, ran out of output tokens, or never gave a verdict that matches
    the answer format. The message names the break's two pages and the model's role
    in it, the judge or the verifier.
    """


class PdfError(PydelityError):
    """The PDF is empty, password-protected or cannot be opened."""


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


class PydelityWarning(UserWarning):
    """A problem the user should know about that does not stop the run."""


class SurveyError(PydelityError):
    """The survey step could not produce a usable answer."""

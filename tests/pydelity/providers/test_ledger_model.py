"""Tests for model requests: provider retries, provider errors and the ledger.

The stand-in provider server fails model requests on demand. Temporary failures
carry a 1-millisecond ``retry-after-ms`` header, so retries do not wait.
"""

# Standard Library
from collections.abc import Callable
from pathlib import Path

# Third Party Library
import pytest

from pydantic_ai.exceptions import ModelHTTPError

# Package Library
import pydelity

from pydelity.errors import ProviderError
from tests.fixtures.mock_providers import MockProviders

# The 2-page scanned test PDF, with no text layer.
_SCAN = "irs_form_1040a_1965_scan.pdf"


def _model_statuses(mock: MockProviders) -> list[int]:
    """List the reply statuses of the model requests the stand-in received.

    Parameters
    ----------
    mock
        The stand-in server.

    Returns
    -------
    list[int]
        Each model request's HTTP status, in order.
    """

    return [request.status for request in mock.requests if request.route == "model"]


@pytest.mark.parametrize(("retries", "status"), [(0, 429), (3, 503)])
def test_a_request_is_sent_at_most_one_plus_the_retry_setting_times(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    retries: int,
    status: int,
    survey_answer: Callable[..., dict],
) -> None:
    """With every attempt failing, the request goes out ``1 + retries`` times.

    The run then raises a temporary `ProviderError` that names the retry count.
    """

    mock = mock_providers(answers=[survey_answer()])
    mock.add_fault(route="model", status=status, times=None)

    with pytest.raises(ProviderError) as raised:
        pydelity.run(
            pdf_path(_SCAN), advanced={"provider_retries": retries}, output_dir="out"
        )

    assert _model_statuses(mock) == [status] * (1 + retries)
    error = raised.value
    assert (error.status_code, error.temporary) == (status, True)
    word = "retry" if retries == 1 else "retries"
    assert f"It still failed after {retries} {word} (advanced.provider_retries)." in (
        str(error)
    )
    assert pydelity.load("out").ledger == []


def test_a_request_the_provider_rejects_is_sent_once_and_raises_its_message(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """A 400 is not retried; `ProviderError` keeps the message and the SDK error.

    The run is recorded as failed and every file in the folder still loads.
    """

    mock = mock_providers(answers=[survey_answer()])
    rejection = "The PDF exceeds the model's context window."
    mock.add_fault(message=rejection, route="model", status=400, times=None)

    with pytest.raises(ProviderError) as raised:
        pydelity.run(pdf_path(_SCAN), output_dir="out")

    assert _model_statuses(mock) == [400]
    error = raised.value
    assert error.provider_message == rejection
    assert (error.status_code, error.temporary, error.upload_error) == (
        400,
        False,
        None,
    )
    assert (error.provider, error.model) == ("anthropic", "claude-opus-5-5")
    assert isinstance(error.__cause__, ModelHTTPError)
    loaded = pydelity.load("out")
    assert loaded.record is not None
    assert loaded.record.status == "failed"
    assert loaded.record.error is not None
    assert rejection in loaded.record.error


def test_fewer_temporary_failures_than_the_retries_still_complete(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Two temporary failures with the default two retries end in a survey.

    Failed attempts return no usage, so only the answered request is a ledger line.
    The run then pauses after the new survey, as every run does by default.
    """

    mock = mock_providers(answers=[survey_answer()])
    mock.add_fault(route="model", status=429, times=2)

    result = pydelity.run(pdf_path(_SCAN), output_dir="out")

    assert _model_statuses(mock) == [429, 429, 200]
    assert result.record is not None
    assert result.record.status == "paused"
    assert len(result.ledger) == 1
    assert result.record.steps[0].requests == 1

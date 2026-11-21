"""Tests for how the PDF reaches the provider: uploads, reuse and the fallback.

The stand-in provider server holds uploaded files, answers 404 for a file it no
longer has, and fails requests on demand.
"""

# Standard Library
import hashlib
import json

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Third Party Library
import pytest

from pydantic_ai.exceptions import ModelHTTPError

# Package Library
import pydelity

from pydelity.errors import ProviderError, PydelityWarning
from pydelity.providers.schemas import Uploads
from tests.fixtures.mock_providers import MockProviders, RecordedRequest

# The 2-page scanned test PDF, with no text layer.
_SCAN = "irs_form_1040a_1965_scan.pdf"


def _routes(mock: MockProviders) -> list[tuple[str, int]]:
    """List each request the stand-in received as its route and reply status.

    Parameters
    ----------
    mock
        The stand-in server.

    Returns
    -------
    list[tuple[str, int]]
        ``(route, status)`` for each request, in order.
    """

    return [(str(request.route), request.status) for request in mock.requests]


def _uploads(folder: str = "out") -> Uploads:
    """Read an output folder's ``uploads.json``.

    Parameters
    ----------
    folder
        The output folder.

    Returns
    -------
    Uploads
        The upload records.
    """

    text = Path(folder, "uploads.json").read_text(encoding="utf-8")
    return Uploads.model_validate_json(text)


def _uploads_of(mock: MockProviders) -> list[RecordedRequest]:
    """Return the upload requests the stand-in answered successfully.

    Parameters
    ----------
    mock
        The stand-in server.

    Returns
    -------
    list[RecordedRequest]
        The successful uploads, in order.
    """

    return [r for r in mock.requests if r.route == "upload" and r.status == 200]


def test_a_damaged_uploads_file_counts_as_empty(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """A damaged ``uploads.json`` is ignored with a warning; the PDF is uploaded."""

    mock = mock_providers(answers=[survey_answer()])
    Path("out").mkdir()
    Path("out/uploads.json").write_text("{not json", encoding="utf-8")

    with pytest.warns(PydelityWarning, match="uploading the PDF again"):
        result = pydelity.run(pdf_path(_SCAN), output_dir="out")

    assert len(_uploads_of(mock)) == 1
    assert len(_uploads().uploads) == 1
    assert result.record is not None
    assert [w.code for w in result.record.warnings] == ["damaged_output"]
    assert result.record.warnings[0].details == {"file": "uploads.json"}


def test_a_failed_upload_falls_back_to_sending_the_pdf_in_the_request(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Uploads failing after the retries send the PDF inside the request instead.

    The upload is tried ``1 + provider_retries`` times. ``run.json`` records a
    warning and the request transport, and nothing is written to ``uploads.json``.
    """

    mock = mock_providers(answers=[survey_answer()])
    mock.add_fault(route="upload", status=503, times=None)

    with pytest.warns(PydelityWarning, match="sent inside each request instead"):
        result = pydelity.run(
            pdf_path(_SCAN), advanced={"provider_retries": 1}, output_dir="out"
        )

    assert _routes(mock) == [("upload", 503), ("upload", 503), ("model", 200)]
    request = json.dumps(mock.requests[-1].body)
    assert mock.requests[-1].file_ids == []
    assert '"media_type": "application/pdf"' in request
    assert '"type": "base64"' in request
    assert result.record is not None
    assert result.record.status == "paused"
    assert result.record.steps[0].pdf_transport == "request"
    (warning,) = result.record.warnings
    assert warning.code == "upload_fallback"
    assert "Service Unavailable" in str(warning.details["upload_error"])
    assert not Path("out/uploads.json").exists()


def test_a_fallback_request_the_provider_rejects_reports_both_errors(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """When the in-request PDF is rejected too, the error carries both messages."""

    mock = mock_providers(answers=[survey_answer()])
    mock.add_fault(route="upload", status=500, times=None)
    rejection = "The PDF is too large to read."
    mock.add_fault(message=rejection, route="model", status=400, times=None)

    with (
        pytest.raises(ProviderError) as raised,
        pytest.warns(PydelityWarning, match="sent inside each request instead"),
    ):
        pydelity.run(pdf_path(_SCAN), output_dir="out")

    error = raised.value
    assert error.provider_message == rejection
    assert error.upload_error is not None
    assert "Internal Server Error" in error.upload_error
    assert rejection in str(error)
    assert error.upload_error in str(error)
    assert isinstance(error.__cause__, ModelHTTPError)
    assert sum(1 for r in mock.requests if r.route == "model") == 1


def test_a_file_the_provider_no_longer_has_is_uploaded_again_once(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """A 404 naming the recorded file leads to one new upload, recorded in its place."""

    mock = mock_providers(answers=[survey_answer()])
    pydelity.run(pdf_path(_SCAN), output_dir="out")
    (old,) = _uploads().uploads
    mock.forget_uploads()

    result = pydelity.run(pdf_path(_SCAN), output_dir="out", overwrite=True)

    assert _routes(mock)[2:] == [("model", 404), ("upload", 200), ("model", 200)]
    (new,) = _uploads().uploads
    assert new.file_id != old.file_id
    assert mock.requests[-1].file_ids == [new.file_id]
    assert result.record is not None
    assert result.record.status == "paused"


def test_a_recorded_upload_is_reused_by_a_rerun(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """A rerun of the survey refers to the recorded upload instead of uploading."""

    mock = mock_providers(answers=[survey_answer()])
    pydelity.run(pdf_path(_SCAN), output_dir="out")

    pydelity.run(pdf_path(_SCAN), output_dir="out", overwrite=True)

    (record,) = _uploads().uploads
    assert len(_uploads_of(mock)) == 1
    model_requests = [r for r in mock.requests if r.route == "model"]
    assert [r.file_ids for r in model_requests] == [[record.file_id]] * 2


@pytest.mark.parametrize("status", [401, 413])
def test_an_upload_refused_for_its_key_or_size_stops_the_run(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    status: int,
    survey_answer: Callable[..., dict],
) -> None:
    """An upload refused as unauthorized or too large stops with `ProviderError`.

    No fallback request follows, since it would fail the same way.
    """

    mock = mock_providers(answers=[survey_answer()])
    mock.add_fault(message="Refused by the provider.", route="upload", status=status)

    with pytest.raises(ProviderError) as raised:
        pydelity.run(pdf_path(_SCAN), output_dir="out")

    assert _routes(mock) == [("upload", status)]
    error = raised.value
    assert (error.status_code, error.temporary) == (status, False)
    assert error.provider_message == "Refused by the provider."
    record = pydelity.load("out").record
    assert record is not None
    assert record.status == "failed"


@pytest.mark.parametrize(
    ("model", "expiry", "seconds_field", "purpose"),
    [
        ("anthropic:claude-opus-5-5", None, "expires_in_seconds", None),
        ("openai:gpt-6.2-astra", 24, "expires_after[seconds]", "user_data"),
    ],
    ids=["anthropic", "openai"],
)
def test_the_pdf_is_uploaded_once_recorded_and_referenced(  # noqa: PLR0913, PLR0917 - fixtures and parameters
    expiry: int | None,
    mock_providers: Callable[..., MockProviders],
    model: str,
    pdf_path: Callable[[str], Path],
    purpose: str | None,
    seconds_field: str,
    survey_answer: Callable[..., dict],
) -> None:
    """Each provider gets one upload with its expiry; the request names the file.

    ``uploads.json`` records the upload, and ``run.json`` says the PDF went by upload.
    The default expiry is the provider's maximum.
    """

    mock = mock_providers(answers=[survey_answer()])
    advanced = {"uploads": {"expiry_hours": expiry}}

    result = pydelity.run(
        pdf_path(_SCAN), advanced=advanced, model=model, output_dir="out"
    )

    (upload,) = _uploads_of(mock)
    fields = upload.body["fields"]
    assert isinstance(fields, dict)
    hours = expiry or 2160
    assert fields[seconds_field] == str(hours * 3600)
    assert fields.get("purpose") == purpose
    (record,) = _uploads().uploads
    provider = model.split(":", maxsplit=1)[0]
    sha256 = hashlib.sha256(pdf_path(_SCAN).read_bytes()).hexdigest()
    assert (record.provider, record.pdf_sha256) == (provider, sha256)
    assert record.expires_at is not None
    expected = datetime.now(UTC) + timedelta(hours=hours)
    assert abs(record.expires_at - expected) < timedelta(minutes=5)
    model_request = next(r for r in mock.requests if r.route == "model")
    assert model_request.file_ids == [record.file_id]
    assert result.record is not None
    assert result.record.steps[0].pdf_transport == "upload"

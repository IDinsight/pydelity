"""Uploading the PDF to the provider, reusing the upload, and the in-request fallback.

The PDF is uploaded once through the provider's Files API and kept there until the
provider's expiry (``advanced.uploads.expiry_hours``, or the provider's maximum).
``uploads.json`` in the output folder records each upload, and a later run reuses it
while at least an hour is left. Uploads are free, so they are not in ``cost.jsonl``.

When the upload fails, the PDF is sent inside each request instead, for the rest of the
step. Two upload errors stop the run instead, because the request would fail the same
way: an authentication failure, and a PDF rejected as too large (HTTP 413).
"""

# Standard Library
import asyncio

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import cache
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING, cast

# Third Party Library
import anthropic
import openai

from loguru import logger
from pydantic_ai.messages import BinaryContent, UploadedFile
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIResponsesModel

# Package Library
from pydelity.config.schemas import Config
from pydelity.errors import ProviderError
from pydelity.providers.ledger_model import LedgerModel
from pydelity.providers.profiles import PdfTransport
from pydelity.providers.schemas import Upload, Uploads
from pydelity.schema_versions import UPLOADS_SCHEMA_VERSION
from pydelity.utils.coroutines import warn
from pydelity.utils.files import load_model, write_model_atomic
from pydelity.utils.pdf import PdfInfo

if TYPE_CHECKING:
    # Third Party Library
    from openai.types import FilePurpose

# The lowest HTTP status code of a server error, which the SDKs retry.
_FIRST_SERVER_ERROR_CODE = 500

# The PDF's media type, for uploads and for the in-request fallback.
_PDF_MEDIA_TYPE = "application/pdf"

# Upload errors that stop the run instead of falling back: an authentication failure,
# and a PDF the provider rejects as too large.
_STOP_STATUS_CODES = frozenset({401, 413})

# HTTP status codes below 500 that the SDKs treat as temporary and retry.
_TEMPORARY_STATUS_CODES = frozenset({408, 409, 429})

# A recorded upload is reused only while at least this much time is left before it
# expires.
REUSE_MIN_REMAINING = timedelta(hours=1)

# The uploads file's name in the output folder.
UPLOADS_FILE_NAME = "uploads.json"


def _client(model: LedgerModel) -> anthropic.AsyncAnthropic | openai.AsyncOpenAI:
    """Return the SDK client of a model that `build_model` built.

    Uploads go through the same client as the model's requests, so they get the same
    retry count and timeout.

    Parameters
    ----------
    model
        The model.

    Returns
    -------
    anthropic.AsyncAnthropic | openai.AsyncOpenAI
        The client.

    Raises
    ------
    TypeError
        If the model was not built by `build_model`.
    """

    wrapped = model.wrapped
    if isinstance(wrapped, AnthropicModel) and isinstance(
        wrapped.client, anthropic.AsyncAnthropic
    ):
        return wrapped.client
    if isinstance(wrapped, OpenAIResponsesModel):
        return wrapped.client
    raise TypeError(f"{type(wrapped).__name__} is not a model build_model makes")


def _describe_expiry(expires_at: datetime | None) -> str:
    """Write an upload's expiry for the log.

    Parameters
    ----------
    expires_at
        When the upload expires, or ``None``.

    Returns
    -------
    str
        Such as ``expires 2027-02-16 14:15 UTC`` or ``no expiry``.
    """

    if expires_at is None:
        return "no expiry"
    return f"expires {expires_at.astimezone(UTC):%Y-%m-%d %H:%M} UTC"


def _provider_error(
    error: anthropic.APIError | openai.APIError, *, config: Config, pdf: PdfInfo
) -> ProviderError:
    """Turn a failed upload's SDK error into a `ProviderError`.

    Parameters
    ----------
    error
        The SDK's error, after its retries.
    config
        The run's settings, for the model and the retry count.
    pdf
        The PDF the upload carried.

    Returns
    -------
    ProviderError
        The error, naming the provider and model, the provider's message, the PDF
        and, for a temporary failure, the retries made.
    """

    choice = config.model_choice
    provider_message = error.message
    body = error.body
    if isinstance(body, dict):
        detail = body.get("error", body)
        if isinstance(detail, dict) and isinstance(detail.get("message"), str):
            provider_message = detail["message"]

    status_code = getattr(error, "status_code", None)
    temporary = isinstance(
        error, anthropic.APIConnectionError | openai.APIConnectionError
    ) or (
        status_code is not None
        and (
            status_code in _TEMPORARY_STATUS_CODES
            or status_code >= _FIRST_SERVER_ERROR_CODE
        )
    )

    ending = "" if provider_message.endswith((".", "!", "?")) else "."
    pages = f"{pdf.page_count} page" + ("" if pdf.page_count == 1 else "s")
    sentences = [
        f"{choice.setting}: {provider_message}{ending}",
        f"The upload of {pdf.name} ({pages}, {pdf.bytes:,} bytes) failed.",
    ]
    if temporary:
        retries = config.advanced.provider_retries
        word = "retry" if retries == 1 else "retries"
        sentences.append(
            f"It still failed after {retries} {word} (advanced.provider_retries)."
        )
    return ProviderError(
        " ".join(sentences),
        model=choice.model_id,
        provider=choice.provider,
        provider_message=provider_message,
        status_code=status_code,
        temporary=temporary,
    )


@cache
def _pydelity_version() -> str:
    """Return the installed pydelity's version.

    Returns
    -------
    str
        The version, read from the package metadata once.
    """

    return version("pydelity")


def _read_uploads(path: Path) -> tuple[list[Upload], str | None]:
    """Read ``uploads.json``, treating a damaged or incompatible file as empty.

    Parameters
    ----------
    path
        The uploads file. A missing file holds no uploads.

    Returns
    -------
    tuple[list[Upload], str | None]
        The recorded uploads, and why the file was ignored, if it was.
    """

    loaded = load_model(model_type=Uploads, path=path)
    if loaded.damage is not None:
        return [], loaded.damage
    if loaded.model is None:
        return [], None
    major = loaded.model.schema_version.split(".")[0]
    if major != UPLOADS_SCHEMA_VERSION.split(".")[0]:
        return [], (
            f"{path.name}: schema_version {loaded.model.schema_version} is not "
            f"compatible with {UPLOADS_SCHEMA_VERSION}"
        )
    return loaded.model.uploads, None


def _record_upload(path: Path, upload: Upload) -> None:
    """Write an upload to ``uploads.json``, replacing the PDF's earlier record.

    Parameters
    ----------
    path
        The uploads file.
    upload
        The new upload.
    """

    records, _ = _read_uploads(path)
    kept = [
        record
        for record in records
        if (record.provider, record.pdf_sha256) != (upload.provider, upload.pdf_sha256)
    ]
    uploads = Uploads(
        pydelity_version=_pydelity_version(),
        schema_version=UPLOADS_SCHEMA_VERSION,
        uploads=[*kept, upload],
    )
    write_model_atomic(model=uploads, path=path)


async def _upload(
    *,
    client: anthropic.AsyncAnthropic | openai.AsyncOpenAI,
    data: bytes,
    config: Config,
    pdf: PdfInfo,
) -> tuple[str, datetime | None]:
    """Upload the PDF through the provider's Files API.

    Parameters
    ----------
    client
        The provider's SDK client.
    data
        The PDF's bytes.
    config
        The run's settings, for the expiry.
    pdf
        The PDF.

    Returns
    -------
    tuple[str, datetime | None]
        The provider's file ID, and when the file expires.
    """

    profile = config.model_choice.profile
    hours = config.advanced.uploads.expiry_hours or profile.max_upload_expiry_hours
    seconds = hours * 3600
    file = (pdf.name, data, _PDF_MEDIA_TYPE)
    if isinstance(client, anthropic.AsyncAnthropic):
        metadata = await client.files.upload(expires_in_seconds=seconds, file=file)
        return metadata.id, metadata.expires_at

    created = await client.files.create(
        expires_after={"anchor": "created_at", "seconds": seconds},
        file=file,
        purpose=cast("FilePurpose", profile.upload_purpose),
    )
    if created.expires_at is None:
        return created.id, None
    return created.id, datetime.fromtimestamp(created.expires_at, UTC)


async def _upload_or_fall_back(
    *, config: Config, model: LedgerModel, output_folder: Path, pdf: PdfInfo
) -> "PdfAttachment":
    """Upload the PDF and record it, or fall back to sending it in each request.

    Parameters
    ----------
    config
        The run's settings.
    model
        The step's model, whose SDK client uploads the PDF.
    output_folder
        The output folder, which holds ``uploads.json``.
    pdf
        The PDF.

    Returns
    -------
    PdfAttachment
        The uploaded file, or the PDF itself when the upload failed.

    Raises
    ------
    ProviderError
        If the provider rejects the upload for an invalid API key or as too large.
    """

    choice = config.model_choice
    data = await asyncio.to_thread(pdf.path.read_bytes)
    try:
        file_id, expires_at = await _upload(
            client=_client(model), config=config, data=data, pdf=pdf
        )
    except (anthropic.APIError, openai.APIError) as error:
        failure = _provider_error(error, config=config, pdf=pdf)
        if failure.status_code in _STOP_STATUS_CODES:
            raise failure from error
        warn(
            f"Uploading {pdf.name} to {choice.provider} failed, so the PDF is sent "
            f"inside each request instead. {failure}",
            code="upload_fallback",
            details={"provider": choice.provider, "upload_error": str(failure)},
        )
        return PdfAttachment(
            content=BinaryContent(data=data, media_type=_PDF_MEDIA_TYPE),
            transport="request",
            upload_error=str(failure),
        )

    upload = Upload(
        bytes=pdf.bytes,
        expires_at=expires_at,
        file_id=file_id,
        pdf_name=pdf.name,
        pdf_sha256=pdf.sha256,
        provider=choice.provider,
        uploaded_at=datetime.now(UTC),
    )
    _record_upload(output_folder / UPLOADS_FILE_NAME, upload)
    logger.info(
        "Uploaded {name} to {provider}: file {file_id}, {expiry}",
        expiry=_describe_expiry(expires_at),
        file_id=file_id,
        name=pdf.name,
        provider=choice.provider,
    )
    return PdfAttachment.uploaded(upload)


@dataclass(frozen=True)
class PdfAttachment:
    """How the PDF goes into a step's requests.

    Attributes
    ----------
    content
        The uploaded file, or the PDF's bytes when it is sent inside each request.
    transport
        ``upload`` or ``request``.
    upload_error
        Why the upload failed, when the PDF is sent inside each request.
    """

    content: UploadedFile | BinaryContent
    transport: PdfTransport
    upload_error: str | None

    @classmethod
    def uploaded(cls, upload: Upload) -> "PdfAttachment":
        """Refer to a PDF the provider already has.

        Parameters
        ----------
        upload
            The upload's record.

        Returns
        -------
        PdfAttachment
            The attachment, referring to the uploaded file.
        """

        content = UploadedFile(
            file_id=upload.file_id,
            media_type=_PDF_MEDIA_TYPE,
            provider_name=upload.provider,
        )
        return cls(content=content, transport="upload", upload_error=None)


async def attach_pdf(
    *, config: Config, model: LedgerModel, output_folder: Path, pdf: PdfInfo
) -> PdfAttachment:
    """Reuse the PDF's upload, upload it, or fall back to sending it in each request.

    A recorded upload of the same PDF on the same provider is reused while at least
    `REUSE_MIN_REMAINING` is left before it expires. A damaged ``uploads.json`` is
    treated as empty, with a warning.

    Parameters
    ----------
    config
        The run's settings.
    model
        The step's model, whose SDK client uploads the PDF.
    output_folder
        The output folder, which holds ``uploads.json``.
    pdf
        The PDF.

    Returns
    -------
    PdfAttachment
        What to put in the step's requests.

    Raises
    ------
    ProviderError
        If the provider rejects the upload for an invalid API key or as too large.
    """

    records, damage = _read_uploads(output_folder / UPLOADS_FILE_NAME)
    if damage is not None:
        warn(
            f"{damage}; uploading the PDF again",
            code="damaged_output",
            details={"file": UPLOADS_FILE_NAME},
        )
    provider = config.model_choice.provider
    now = datetime.now(UTC)
    for record in records:
        if (record.provider, record.pdf_sha256) != (provider, pdf.sha256):
            continue
        if record.expires_at is None or record.expires_at - now >= REUSE_MIN_REMAINING:
            logger.info(
                "Reusing upload {file_id} of {name} on {provider}, {expiry}",
                expiry=_describe_expiry(record.expires_at),
                file_id=record.file_id,
                name=pdf.name,
                provider=provider,
            )
            return PdfAttachment.uploaded(record)
    return await _upload_or_fall_back(
        config=config, model=model, output_folder=output_folder, pdf=pdf
    )


def is_missing_file(error: ProviderError, attachment: PdfAttachment) -> bool:
    """Tell whether a request failed because the provider no longer has the upload.

    Both providers answer such a request with HTTP 404 and a message that names the
    file ID; a model that does not exist also gets 404, but without the file ID.

    Parameters
    ----------
    error
        The request's error.
    attachment
        How the request carried the PDF.

    Returns
    -------
    bool
        Whether the request referred to an uploaded file the provider does not have.
    """

    content = attachment.content
    return (
        isinstance(content, UploadedFile)
        and error.status_code == 404  # noqa: PLR2004 - HTTP Not Found
        and content.file_id in error.provider_message
    )


async def replace_missing_upload(
    *,
    attachment: PdfAttachment,
    config: Config,
    model: LedgerModel,
    output_folder: Path,
    pdf: PdfInfo,
) -> PdfAttachment:
    """Upload the PDF again after the provider answered that it no longer has it.

    This is done once per step run. If the new upload fails, the PDF is sent inside
    each request instead, as for a first upload.

    Parameters
    ----------
    attachment
        The attachment whose file the provider no longer has.
    config
        The run's settings.
    model
        The step's model, whose SDK client uploads the PDF.
    output_folder
        The output folder, which holds ``uploads.json``.
    pdf
        The PDF.

    Returns
    -------
    PdfAttachment
        The new upload, or the PDF itself when the upload failed.

    Raises
    ------
    ProviderError
        If the provider rejects the upload for an invalid API key or as too large.
    """

    file_id = getattr(attachment.content, "file_id", "the uploaded file")
    logger.info(
        "{provider} no longer has {file_id}; uploading {name} again",
        file_id=file_id,
        name=pdf.name,
        provider=config.model_choice.provider,
    )
    return await _upload_or_fall_back(
        config=config, model=model, output_folder=output_folder, pdf=pdf
    )


def with_upload_error(error: ProviderError, upload_error: str) -> ProviderError:
    """Add the earlier upload error to a request error after the fallback.

    Parameters
    ----------
    error
        The error of the request that carried the PDF inside it.
    upload_error
        Why the upload failed before the fallback.

    Returns
    -------
    ProviderError
        A copy of ``error`` whose message also gives the upload error, with
        ``upload_error`` set.
    """

    return ProviderError(
        f"{error} The upload had failed before: {upload_error}",
        model=error.model,
        provider=error.provider,
        provider_message=error.provider_message,
        status_code=error.status_code,
        temporary=error.temporary,
        upload_error=upload_error,
    )

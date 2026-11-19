"""The providers' records: ``uploads.json``, the PDFs uploaded to each provider.

Output models accept fields they do not know, so a file written by a newer pydelity
with the same major ``schema_version`` still loads. The file holds no secrets.
"""

# Standard Library
from datetime import datetime

# Third Party Library
from pydantic import BaseModel, ConfigDict

# Package Library
from pydelity.providers.profiles import ProviderName


class _Output(BaseModel):
    """Base for the models stored in output files."""

    model_config = ConfigDict(use_attribute_docstrings=True)


class Upload(_Output):
    """One PDF uploaded to one provider."""

    bytes: int
    """The PDF's size in bytes."""

    expires_at: datetime | None
    """When the provider deletes the file (UTC), or ``None`` when it sets no expiry."""

    file_id: str
    """The provider's ID for the file."""

    pdf_name: str
    """The PDF's file name."""

    pdf_sha256: str
    """The PDF's SHA-256 hex digest."""

    provider: ProviderName
    """The provider, ``anthropic`` or ``openai``."""

    uploaded_at: datetime
    """When the upload finished (UTC)."""


class Uploads(_Output):
    """The contents of ``uploads.json``: at most one upload per provider and PDF."""

    pydelity_version: str
    """The pydelity version that last wrote the file."""

    schema_version: str
    """The version of this file's schema, ``"MAJOR.MINOR"``."""

    uploads: list[Upload]
    """The uploads, one per provider and PDF SHA-256."""

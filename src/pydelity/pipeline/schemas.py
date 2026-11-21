"""The run's data: ``run.json`` and the result a run returns.

Output models accept fields they do not know, so a ``run.json`` written by a newer
pydelity with the same major ``schema_version`` still loads.
"""

# Standard Library
from datetime import datetime
from pathlib import Path
from typing import Literal

# Third Party Library
from pydantic import BaseModel, ConfigDict

# Package Library
from pydelity.costs.schemas import LedgerEntry, Money
from pydelity.errors import WarningCode
from pydelity.extracting.schemas import PageFile
from pydelity.providers.profiles import PdfTransport
from pydelity.review import ReviewIssue
from pydelity.surveying.schemas import PdfFacts, PdfSurvey

# How a run ended, or ``running`` while it lasts. A ``paused`` run stopped after a step
# that wrote new output, so it can be checked before the next step.
type RunStatus = Literal[
    "running", "completed", "paused", "failed", "stopped", "interrupted"
]

# How a step ended.
type StepStatus = Literal["completed", "reused", "failed", "stopped", "skipped"]


class _Output(BaseModel):
    """Base for the models stored in output files."""

    model_config = ConfigDict(use_attribute_docstrings=True)


class PageCounts(_Output):
    """How many pages a page step selected, extracted and reused."""

    extracted: int
    """The selected pages extracted in this run."""

    reused: int
    """The selected pages whose saved output was reused."""

    selected: int
    """The pages selected with ``pages``; every page when it is unset."""


class PdfRecord(_Output):
    """The PDF a run processed."""

    bytes: int
    """The PDF's size in bytes."""

    page_count: int
    """The PDF's number of pages."""

    path: str
    """The PDF's path, as given."""

    sha256: str
    """The PDF's SHA-256 hex digest."""


class RunCost(_Output):
    """What a run's model requests cost, from ``cost.jsonl``."""

    by_step: dict[str, Money]
    """This run's priced requests, summed by step."""

    output_folder_usd: Money
    """Every priced request recorded in the output folder, from every run."""

    run_usd: Money
    """This run's priced requests."""

    unpriced_requests: int
    """How many of this run's requests have no known price."""


class StepRecord(_Output):
    """What one step of a run did."""

    cost_usd: Money
    """What the step's priced requests in this run cost."""

    ended_at: datetime | None
    """When the step ended (UTC)."""

    error: str | None
    """Why the step failed or stopped, if it did."""

    name: str
    """The step, such as ``survey``."""

    outputs: list[str]
    """The files the step wrote or reused, by name."""

    pages: PageCounts | None
    """How many pages the step selected, extracted and reused; ``None`` for a step
    that reads the whole PDF at once, such as the survey."""

    pdf_transport: PdfTransport | None
    """How the PDF went to the model: ``upload`` or ``request``; ``None`` when no
    request carried it."""

    requests: int
    """How many model requests the step made in this run."""

    started_at: datetime
    """When the step started (UTC)."""

    status: StepStatus
    """How the step ended."""


class WarningItem(_Output):
    """A user-facing warning the run issued."""

    code: WarningCode
    """The kind of warning."""

    details: dict[str, object]
    """The values the warning is about."""

    message: str
    """The warning's text."""

    step: str | None
    """The step that issued it, or ``None`` when no step was running."""


class RunRecord(_Output):
    """The contents of ``run.json``: one run on one PDF."""

    cost: RunCost
    """What the run's model requests cost."""

    ended_at: datetime | None
    """When the run ended (UTC); ``None`` while it runs."""

    error: str | None
    """Why the run failed, stopped or was interrupted, if it was."""

    pdf: PdfRecord
    """The PDF."""

    pydelity_version: str
    """The pydelity version that ran."""

    review: list[ReviewIssue]
    """The review issues of every step output the run used, reused ones included."""

    run_id: str
    """The run's ID: its start time (UTC) and a random suffix."""

    schema_version: str
    """The version of this file's schema, ``"MAJOR.MINOR"``."""

    settings: dict[str, object]
    """The resolved settings, which hold no API keys."""

    started_at: datetime
    """When the run started (UTC)."""

    status: RunStatus
    """How the run ended, or ``running``."""

    steps: list[StepRecord]
    """What each step did."""

    warnings: list[WarningItem]
    """The user-facing warnings, in the order they were issued."""


class RunResult(BaseModel):
    """What a run left in its output folder, read back as Python objects.

    A part is ``None``, or an empty ledger, when its file is absent.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    facts: PdfFacts | None
    """The contents of ``pdf_facts.json``."""

    ledger: list[LedgerEntry]
    """The lines of ``cost.jsonl``, in order."""

    output_dir: Path
    """The output folder."""

    pages: list[PageFile]
    """Page files, in page order. A run returns its selected pages that have one.
    `pydelity.load` returns the page files made from the PDF in ``pdf_facts.json``,
    and none when the folder has no ``pdf_facts.json``."""

    record: RunRecord | None
    """The contents of ``run.json``."""

    survey: PdfSurvey | None
    """The contents of ``pdf_survey.json``."""

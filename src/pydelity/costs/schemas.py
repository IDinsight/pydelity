"""The cost records: ``cost.jsonl`` lines, the estimate and ``max_cost`` checks.

Money is a `decimal.Decimal` in US dollars. In JSON files it is written as a number.
"""

# Standard Library
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

# Third Party Library
from pydantic import BaseModel, ConfigDict, PlainSerializer

# A sum of money in US dollars, written as a JSON number.
type Money = Annotated[
    Decimal, PlainSerializer(float, return_type=float, when_used="json")
]

# Which ``max_cost`` check failed: ``plan``, before the run starts spending, or
# ``request``, before one model request.
type MaxCostCheck = Literal["plan", "request"]


class _Record(BaseModel):
    """Base for the cost records."""

    model_config = ConfigDict(use_attribute_docstrings=True)


class LedgerEntry(_Record):
    """One model request that returned a response, as a line of ``cost.jsonl``."""

    cache_read_tokens: int
    """Input tokens read from the provider's prompt cache (included in
    ``input_tokens``)."""

    cache_write_tokens: int
    """Input tokens written to the provider's prompt cache (included in
    ``input_tokens``)."""

    cost_usd: Money | None
    """What the request cost, rounded to 6 decimals; ``None`` when no price is known
    for the model."""

    input_tokens: int
    """All input tokens of the request."""

    model: str
    """The model ID pydelity asked for."""

    output_tokens: int
    """Output tokens, thinking included."""

    price_source: str | None
    """Where the price came from: ``genai-prices <version>``, ``config`` (prices set in
    ``advanced.models``), or ``None`` when unpriced."""

    provider: str
    """The provider, ``anthropic`` or ``openai``."""

    request: int
    """The request's number within the step's run, from 1."""

    response_model: str | None
    """The model name the provider reported, which may carry a date or version."""

    run_id: str
    """The run that made the request."""

    schema_version: str
    """The version of this line's schema, ``"MAJOR.MINOR"``."""

    step: str
    """The step that made the request, such as ``survey``."""

    timestamp: datetime
    """When the response arrived (UTC)."""


class MaxCostWarning(_Record):
    """The details of a ``max_cost_exceeded`` warning."""

    allowed: bool | None
    """Whether the run was allowed to go over ``max_cost``; ``None`` until decided."""

    check: MaxCostCheck
    """Which check failed: before the run (``plan``) or before a request
    (``request``)."""

    max_cost: Money
    """The ``max_cost`` setting."""

    projected_usd: Money | None
    """The spend the run could reach: the folder's spend so far plus the run's (or the
    request's) maximum; ``None`` when no price is known for the model."""

    spent_usd: Money
    """What the output folder's ledger had recorded before the check."""


class StepEstimate(_Record):
    """The cost estimate for one step."""

    expected_usd: Money | None
    """The likely cost: one request with a typical answer; ``None`` when unpriced."""

    max_usd: Money | None
    """The most the step can cost: every allowed retry, each with the longest answer
    allowed; ``None`` when unpriced."""

    model: str
    """The model, as ``<provider>:<model-id>``."""

    name: str
    """The step, such as ``survey``."""

    requests_max: int
    """The most model requests the step can make (provider retries aside)."""

    reused: bool
    """Whether the step's saved output will be reused, so it costs nothing."""


class CostEstimate(_Record):
    """A run's likely and maximum cost, estimated before it spends anything."""

    expected_usd: Money | None
    """The steps' likely cost; ``None`` when a model is unpriced."""

    max_cost: Money | None
    """The ``max_cost`` setting."""

    max_usd: Money | None
    """The most the steps can cost; ``None`` when a model is unpriced."""

    over_max_cost: bool
    """Whether ``max_cost`` is set and either the folder's spend plus ``max_usd``
    exceeds it or a model has no known price."""

    priced: bool
    """Whether a price is known for every model the run uses."""

    spent_usd: Money
    """What the output folder's ledger has recorded so far, from earlier runs."""

    steps: list[StepEstimate]
    """The estimate for each step."""

    warnings: list[str]
    """Problems with the estimate, such as a model with no known price."""

"""Prices for model requests, from ``genai-prices`` or from ``advanced.models``.

pydelity has no price table of its own. It prices requests with PydanticAI's cost
calculation, which uses the price data bundled with ``genai-prices`` and does not
fetch updates. Prices set for a model in ``advanced.models`` take precedence. If
neither source has a price for the model, its cost is ``None``.
"""

# Future Library
from __future__ import annotations

# Standard Library
from collections.abc import Mapping
from decimal import Decimal
from typing import TYPE_CHECKING

# Third Party Library
import genai_prices

from genai_prices import Usage, calc_price

# Package Library
from pydelity.config.schemas import ModelPrices
from pydelity.providers.profiles import parse_model

if TYPE_CHECKING:
    # Third Party Library
    from pydantic_ai.messages import ModelResponse

# Prices are per million tokens.
_TOKENS_PER_PRICE_UNIT = Decimal(1_000_000)

# Where a price from advanced.models comes from, as the ledger records it.
CONFIG_PRICE_SOURCE = "config"

# Where a price from genai-prices comes from, as the ledger records it.
GENAI_PRICES_SOURCE = f"genai-prices {genai_prices.__version__}"


def _config_price(
    *,
    cache_read_tokens: int,
    cache_write_tokens: int,
    input_tokens: int,
    output_tokens: int,
    prices: ModelPrices,
) -> Decimal:
    """Price token counts with prices set in ``advanced.models``.

    Parameters
    ----------
    cache_read_tokens
        Input tokens read from the prompt cache.
    cache_write_tokens
        Input tokens written to the prompt cache.
    input_tokens
        All input tokens, cache reads and writes included.
    output_tokens
        Output tokens.
    prices
        The model's prices per million tokens. An unset cache price is the input
        price, and a cache price of 0 is free.

    Returns
    -------
    Decimal
        The cost in US dollars.
    """

    uncached = max(input_tokens - cache_read_tokens - cache_write_tokens, 0)
    # Only an unset cache price falls back to the input price; a price of 0 is free.
    read_price = prices.cache_read_usd_per_mtok
    if read_price is None:
        read_price = prices.input_usd_per_mtok
    write_price = prices.cache_write_usd_per_mtok
    if write_price is None:
        write_price = prices.input_usd_per_mtok
    total = (
        uncached * prices.input_usd_per_mtok
        + cache_read_tokens * read_price
        + cache_write_tokens * write_price
        + output_tokens * prices.output_usd_per_mtok
    )
    return total / _TOKENS_PER_PRICE_UNIT


def price_response(
    *,
    model: str,
    overrides: Mapping[str, ModelPrices],
    response: ModelResponse,
) -> tuple[Decimal | None, str | None]:
    """Price a model's response from the usage it reports.

    Parameters
    ----------
    model
        The model setting, ``<provider>:<model-id>``.
    overrides
        Prices from ``advanced.models``, by model setting.
    response
        The response, with the provider's usage.

    Returns
    -------
    tuple[Decimal | None, str | None]
        The cost in US dollars and where its price came from, or ``(None, None)`` when
        no price is known.
    """

    usage = response.usage
    if model in overrides:
        cost = _config_price(
            cache_read_tokens=usage.cache_read_tokens,
            cache_write_tokens=usage.cache_write_tokens,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            prices=overrides[model],
        )
        return cost, CONFIG_PRICE_SOURCE
    try:
        return response.cost().total_price, GENAI_PRICES_SOURCE
    except (LookupError, ValueError):
        # LookupError: genai-prices does not know the model. ValueError: the response
        # carried no usage, so its cost cannot be known.
        return None, None


def price_usage(
    *,
    input_tokens: int,
    model: str,
    output_tokens: int,
    overrides: Mapping[str, ModelPrices],
) -> Decimal | None:
    """Price token counts for a model, as a cost estimate does.

    No prompt caching is assumed, so every input token is priced in full.

    Parameters
    ----------
    input_tokens
        Input tokens.
    model
        The model setting, ``<provider>:<model-id>``.
    output_tokens
        Output tokens.
    overrides
        Prices from ``advanced.models``, by model setting.

    Returns
    -------
    Decimal | None
        The cost in US dollars, or ``None`` when no price is known for the model.

    Examples
    --------
    >>> price_usage(
    ...     input_tokens=1_000_000,
    ...     model="anthropic:claude-opus-5-5",
    ...     output_tokens=0,
    ...     overrides={},
    ... )
    Decimal('4.0')
    """

    if model in overrides:
        return _config_price(
            cache_read_tokens=0,
            cache_write_tokens=0,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            prices=overrides[model],
        )
    choice = parse_model(model)
    usage = Usage(input_tokens=input_tokens, output_tokens=output_tokens)
    try:
        return calc_price(
            usage, choice.model_id, provider_id=choice.provider
        ).total_price
    except LookupError:
        return None

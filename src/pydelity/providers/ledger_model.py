"""``LedgerModel``: checks ``max_cost`` before each model request and records each one.

Every model pydelity builds is wrapped in a `LedgerModel`. Before a request is sent,
it asks the run's ``max_cost`` guard whether the request may go ahead. After a
response arrives, it prices the response's usage and appends a line to the output
folder's ``cost.jsonl``. A request that the provider fails or rejects, after the SDK's
retries, raises `pydelity.errors.ProviderError`.
"""

# Standard Library
import json
import math

from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

# Third Party Library
from loguru import logger
from pydantic_ai import RunContext
from pydantic_ai.exceptions import ModelAPIError, ModelConnectionError, ModelHTTPError
from pydantic_ai.messages import (
    BinaryContent,
    DocumentUrl,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextContent,
    UploadedFile,
    UserContent,
    UserPromptPart,
)
from pydantic_ai.models import Model, ModelRequestParameters, StreamedResponse
from pydantic_ai.models.wrapper import WrapperModel
from pydantic_ai.settings import ModelSettings, merge_model_settings

# Package Library
from pydelity.config.schemas import Config
from pydelity.costs.budget import PROMPT_CHARS_PER_TOKEN, SpendGuard, format_usd
from pydelity.costs.ledger import append_entry
from pydelity.costs.pricing import price_response, price_usage
from pydelity.costs.schemas import LedgerEntry
from pydelity.errors import ProviderError
from pydelity.schema_versions import LEDGER_SCHEMA_VERSION
from pydelity.utils.pdf import PdfInfo

# Ledger costs are rounded to this many decimal places of a US dollar.
_COST_QUANTUM = Decimal("0.000001")

# The lowest HTTP status code of a server error, which the SDKs retry.
_FIRST_SERVER_ERROR_CODE = 500

# HTTP status codes below 500 that the SDKs treat as temporary and retry.
_TEMPORARY_STATUS_CODES = frozenset({408, 409, 429})


def _input_tokens(
    *,
    messages: Sequence[ModelMessage],
    parameters: ModelRequestParameters,
    pdf_tokens: int,
) -> int:
    """Estimate a request's input tokens, as the cost estimate does.

    Text counts `PROMPT_CHARS_PER_TOKEN` characters per token, including the output
    and tool schemas. Each document counts ``pdf_tokens``. Each earlier answer counts
    the output tokens the provider reported for it.

    Parameters
    ----------
    messages
        The messages the request sends.
    parameters
        The request's tools and output schema.
    pdf_tokens
        Estimated input tokens for each document the request carries.

    Returns
    -------
    int
        The estimated input tokens.
    """

    schemas = [tool.parameters_json_schema for tool in parameters.function_tools]
    schemas += [tool.parameters_json_schema for tool in parameters.output_tools]
    if parameters.output_object is not None:
        schemas.append(parameters.output_object.json_schema)
    chars = sum(len(json.dumps(schema)) for schema in schemas)

    documents = 0
    earlier_output_tokens = 0
    for message in messages:
        if isinstance(message, ModelResponse):
            earlier_output_tokens += message.usage.output_tokens
            continue
        message_chars, message_documents = _request_size(message)
        chars += message_chars
        documents += message_documents

    text_tokens = math.ceil(chars / PROMPT_CHARS_PER_TOKEN)
    return text_tokens + documents * pdf_tokens + earlier_output_tokens


def _is_temporary(error: ModelAPIError) -> bool:
    """Tell whether a failure is of a kind the provider SDKs retry.

    Parameters
    ----------
    error
        The error PydanticAI raised.

    Returns
    -------
    bool
        ``True`` for a connection error, a timeout, or HTTP 408, 409, 429 or 5xx.
    """

    if isinstance(error, ModelConnectionError):
        return True
    if isinstance(error, ModelHTTPError):
        code = error.status_code
        return code in _TEMPORARY_STATUS_CODES or code >= _FIRST_SERVER_ERROR_CODE
    return False


def _provider_message(error: ModelAPIError) -> str:
    """Return the provider's own error message, or the exception's text.

    Parameters
    ----------
    error
        The error PydanticAI raised.

    Returns
    -------
    str
        The ``message`` in the provider's error body (Anthropic nests it under
        ``error``), unchanged; otherwise the exception's text.
    """

    body = error.body
    if isinstance(body, dict):
        detail = body.get("error", body)
        if isinstance(detail, dict) and isinstance(detail.get("message"), str):
            return detail["message"]
    return error.message


def _request_size(message: ModelRequest) -> tuple[int, int]:
    """Measure one request message: its text characters and documents.

    Parameters
    ----------
    message
        The request message.

    Returns
    -------
    tuple[int, int]
        The characters of text, and the number of documents.
    """

    chars = len(message.instructions or "")
    documents = 0
    for part in message.parts:
        if isinstance(part, UserPromptPart):
            part_chars, part_documents = _user_content_size(part.content)
            chars += part_chars
            documents += part_documents
        else:
            chars += len(str(getattr(part, "content", "")))
    return chars, documents


def _sentence(text: str) -> str:
    """End a piece of text with a period, unless it already ends a sentence.

    Parameters
    ----------
    text
        The text.

    Returns
    -------
    str
        The text, ending with ``.``, ``!`` or ``?``.
    """

    return text if text.endswith((".", "!", "?")) else f"{text}."


def _user_content_size(content: str | Sequence[UserContent]) -> tuple[int, int]:
    """Measure a user prompt: its text characters and documents.

    Parameters
    ----------
    content
        The prompt's content.

    Returns
    -------
    tuple[int, int]
        The characters of text, and the number of documents (PDFs or other
        document files, sent inline, by URL or as an uploaded file).
    """

    if isinstance(content, str):
        return len(content), 0
    chars = 0
    documents = 0
    for item in content:
        if isinstance(item, str):
            chars += len(item)
        elif isinstance(item, TextContent):
            chars += len(item.content)
        elif isinstance(item, DocumentUrl | UploadedFile) or (
            isinstance(item, BinaryContent) and item.is_document
        ):
            documents += 1
    return chars, documents


@dataclass(frozen=True)
class LedgerContext:
    """What a step's model requests are checked against and recorded with.

    Attributes
    ----------
    guard
        The run's ``max_cost`` guard.
    ledger_path
        The output folder's ``cost.jsonl``.
    pdf
        The PDF the step's requests carry, or ``None`` when they carry none.
    run_id
        The run that makes the requests.
    step
        The step that makes them, such as ``survey``.
    """

    guard: SpendGuard
    ledger_path: Path
    pdf: PdfInfo | None
    run_id: str
    step: str


class LedgerModel(WrapperModel):
    """A model that checks ``max_cost`` before each request and records each response.

    Parameters
    ----------
    wrapped
        The provider's model.
    config
        The run's settings, for the model, its prices and the retry count.
    context
        The guard, ledger, PDF, run and step the requests belong to.
    """

    def __init__(
        self, wrapped: Model, *, config: Config, context: LedgerContext
    ) -> None:
        """Wrap a provider's model for one step of one run."""

        super().__init__(wrapped)
        self._config = config
        self._context = context
        self._requests = 0

    async def _check_max_cost(
        self,
        *,
        messages: Sequence[ModelMessage],
        model_settings: ModelSettings | None,
        parameters: ModelRequestParameters,
    ) -> None:
        """Ask the ``max_cost`` guard whether the request may go ahead.

        The request's upper bound is its estimated input with the longest answer
        allowed (its ``max_tokens``).

        Parameters
        ----------
        messages
            The messages the request sends.
        model_settings
            The request's settings, merged with the model's own.
        parameters
            The request's tools and output schema.

        Raises
        ------
        BudgetExceededError
            If the request could take the folder over ``max_cost`` and the decision
            is no.
        """

        pdf = self._context.pdf
        pdf_tokens = 0
        if pdf is not None:
            profile = self._config.survey_model.profile
            pdf_tokens = pdf.page_count * profile.pdf_tokens_per_page
        input_tokens = _input_tokens(
            messages=messages, parameters=parameters, pdf_tokens=pdf_tokens
        )
        upper_bound = price_usage(
            input_tokens=input_tokens,
            model=self._config.survey_model.setting,
            output_tokens=(model_settings or {}).get("max_tokens", 0),
            overrides=self._config.advanced.models,
        )
        await self._context.guard.check(check="request", upper_bound_usd=upper_bound)

    def _provider_error(
        self, error: ModelAPIError, messages: Sequence[ModelMessage]
    ) -> ProviderError:
        """Turn a failed request's error into a `ProviderError`.

        Parameters
        ----------
        error
            The error PydanticAI raised, after the SDK's retries.
        messages
            The messages the request sent, to tell whether it carried the PDF.

        Returns
        -------
        ProviderError
            The error, with a message that names the provider and model, then the
            provider's message, the PDF when the request carried it, and, for a
            temporary failure, the retries made.
        """

        choice = self._config.survey_model
        provider_message = _provider_message(error)
        status_code = error.status_code if isinstance(error, ModelHTTPError) else None
        temporary = _is_temporary(error)

        sentences = [f"{choice.setting}: {_sentence(provider_message)}"]
        pdf = self._context.pdf
        documents = sum(
            _request_size(message)[1]
            for message in messages
            if isinstance(message, ModelRequest)
        )
        if pdf is not None and documents:
            pages = f"{pdf.page_count} page" + ("" if pdf.page_count == 1 else "s")
            sentences.append(
                f"The request carried {pdf.name} ({pages}, {pdf.bytes:,} bytes)."
            )
        if temporary:
            retries = self._config.advanced.provider_retries
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

    def _record(self, response: ModelResponse) -> None:
        """Price a response and append its line to ``cost.jsonl``.

        Parameters
        ----------
        response
            The response, with the usage the provider reported.
        """

        choice = self._config.survey_model
        cost, source = price_response(
            model=self._config.survey_model.setting,
            overrides=self._config.advanced.models,
            response=response,
        )
        usage = response.usage
        self._requests += 1
        entry = LedgerEntry(
            cache_read_tokens=usage.cache_read_tokens,
            cache_write_tokens=usage.cache_write_tokens,
            cost_usd=None if cost is None else cost.quantize(_COST_QUANTUM),
            input_tokens=usage.input_tokens,
            model=choice.model_id,
            output_tokens=usage.output_tokens,
            price_source=source,
            provider=choice.provider,
            request=self._requests,
            response_model=response.model_name,
            run_id=self._context.run_id,
            schema_version=LEDGER_SCHEMA_VERSION,
            step=self._context.step,
            timestamp=datetime.now(UTC),
        )
        append_entry(entry=entry, path=self._context.ledger_path)
        logger.debug(
            "{step} request {number}: {input} input and {output} output tokens, {cost}",
            cost="price unknown" if cost is None else format_usd(cost),
            input=usage.input_tokens,
            number=self._requests,
            output=usage.output_tokens,
            step=self._context.step.capitalize(),
        )

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """Check ``max_cost``, send the request, and record the response.

        Parameters
        ----------
        messages
            The messages to send.
        model_settings
            The request's settings.
        model_request_parameters
            The request's tools and output schema.

        Returns
        -------
        ModelResponse
            The provider's response.

        Raises
        ------
        BudgetExceededError
            If the request could take the folder over ``max_cost`` and the decision
            is no; nothing is sent.
        ProviderError
            If the provider fails or rejects the request after the SDK's retries.
        """

        await self._check_max_cost(
            messages=messages,
            model_settings=merge_model_settings(self.settings, model_settings),
            parameters=model_request_parameters,
        )
        try:
            response = await super().request(
                messages, model_settings, model_request_parameters
            )
        except ModelAPIError as error:
            raise self._provider_error(error, messages) from error
        self._record(response)
        return response

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncGenerator[StreamedResponse]:
        """Check ``max_cost``, stream the response, and record it once it ends.

        Parameters
        ----------
        messages
            The messages to send.
        model_settings
            The request's settings.
        model_request_parameters
            The request's tools and output schema.
        run_context
            The agent run's context, passed on to the wrapped model.

        Yields
        ------
        StreamedResponse
            The response as it streams.

        Raises
        ------
        BudgetExceededError
            If the request could take the folder over ``max_cost`` and the decision
            is no; nothing is sent.
        ProviderError
            If the provider fails or rejects the request after the SDK's retries.
        """

        await self._check_max_cost(
            messages=messages,
            model_settings=merge_model_settings(self.settings, model_settings),
            parameters=model_request_parameters,
        )
        try:
            async with super().request_stream(
                messages, model_settings, model_request_parameters, run_context
            ) as stream:
                yield stream
        except ModelAPIError as error:
            raise self._provider_error(error, messages) from error
        self._record(stream.get())

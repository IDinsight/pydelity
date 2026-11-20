---
title: cost.jsonl
description: The fields of cost.jsonl and the figures the cost estimate uses.
sidebar:
  order: 7
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

The output folder's ledger: one JSON object per line, one line for each model
response pydelity received, in the order received.

## cost.jsonl line

One model request that returned a response, as a line of `cost.jsonl`.

- `agent` (string or null; required): The step's agent that made the request,
  such as `extractor` or `verifier`; `None` for a step with one agent, such as
  the survey.
- `cache_read_tokens` (integer; required): Input tokens read from the provider's
  prompt cache (included in `input_tokens`).
- `cache_write_tokens` (integer; required): Input tokens written to the
  provider's prompt cache (included in `input_tokens`).
- `cost_usd` (number or null; required): What the request cost, rounded to 6
  decimals; `None` when no price is known for the model.
- `input_tokens` (integer; required): All input tokens of the request.
- `model` (string; required): The model ID pydelity asked for.
- `output_tokens` (integer; required): Output tokens, thinking included.
- `page_index` (integer or null; required): The page the request was about
  (0-based); `None` for a request about the whole PDF, such as the survey's.
- `price_source` (string or null; required): Where the price came from:
  `genai-prices <version>`, `config` (prices set in `advanced.models`), or
  `None` when unpriced.
- `provider` (string; required): The provider, `anthropic` or `openai`.
- `request` (integer; required): The request's number, from 1, among this run's
  requests by the same step, page and agent.
- `response_model` (string or null; required): The model name the provider
  reported, which may carry a date or version.
- `run_id` (string; required): The run that made the request.
- `schema_version` (string; required): The version of this line's schema,
  `"MAJOR.MINOR"`.
- `step` (string; required): The step that made the request, such as `survey`.
- `timestamp` (date and time (ISO 8601); required): When the response arrived
  (UTC).

## Estimate constants

The figures the cost estimate and the `max_cost` checks use.

- `PROMPT_CHARS_PER_TOKEN` = `4`: Characters of prompt text per input token, for
  the estimate.
- `TEXT_CHARS_PER_OUTPUT_TOKEN` = `2`: Characters of a page's text layer per
  output token of its extraction, beyond `TYPICAL_PAGE_OUTPUT_TOKENS`, for the
  estimate. The answer repeats the text with an item's fields around it.
- `TYPICAL_OUTPUT_TOKENS` = `8000`: The output tokens of a typical survey
  answer, thinking included, for the estimate.
- `TYPICAL_PAGE_OUTPUT_TOKENS` = `4000`: The output tokens of a typical page
  extraction, thinking included, before the page's text is counted, for the
  estimate.
- `TYPICAL_VERDICT_OUTPUT_TOKENS` = `3000`: The output tokens of a typical
  verdict on a page, thinking included, for the estimate.

- `anthropic`: 4,784 image and 3,000 text input tokens per PDF page; uploads
  kept 1 to 2,160 hours.
- `openai`: 3,000 image and 3,000 text input tokens per PDF page; uploads kept 1
  to 720 hours.

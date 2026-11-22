---
title: cost.jsonl
description:
  The fields of cost.jsonl and of the cost estimate, and the figures the
  estimate uses.
sidebar:
  order: 8
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

The output folder's ledger: one JSON object per line, one line for each model
response pydelity received, in the order received.

## cost.jsonl line

One model request that returned a response, as a line of `cost.jsonl`.

- `agent` (string; required): The step's agent that made the request: `surveyor`
  or `verifier` for the survey, `extractor` or `verifier` for page extraction,
  `judge` or `verifier` for page-break verification.
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
  (0-based); for page-break verification, the page before the break; `None` for
  a request about the whole PDF, such as the survey's.
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

## Cost estimate

A run's likely and maximum cost, estimated before it spends anything.

- `expected_usd` (number or null; required): The steps' likely cost; `None` when
  a model is unpriced.
- `max_cost` (number or null; required): The `max_cost` setting.
- `max_usd` (number or null; required): The most the steps can cost; `None` when
  a model is unpriced.
- `over_max_cost` (boolean; required): Whether `max_cost` is set and either the
  folder's spend plus `expected_usd` exceeds it or a model has no known price.
  Each request is still checked against its own maximum before it is sent.
- `priced` (boolean; required): Whether a price is known for every model the run
  uses.
- `spent_usd` (number; required): What the output folder's ledger has recorded
  so far, from earlier runs.
- `steps` (list of objects ([`steps[]`](#steps)); required): The estimate for
  each step.
- `warnings` (list of strings; required): Problems with the estimate, such as a
  model with no known price.

## `steps[]`

The cost estimate for one step.

- `breaks` (integer or null; required): How many page breaks the step would
  judge, for page-break verification; `None` for the other steps.
- `expected_usd` (number or null; required): The likely cost: one request per
  agent that runs (and per page or break, for a step that sends requests about
  each) with a typical answer; `None` when unpriced.
- `max_usd` (number or null; required): The most the step can cost: every
  allowed retry, each with the longest answer allowed; `None` when unpriced.
- `model` (string; required): The model, as `<provider>:<model-id>`.
- `name` (string; required): The step, such as `survey`.
- `pages` (integer or null; required): How many pages the step would send
  requests about, for a page step; `None` for a step that reads the whole PDF at
  once, such as the survey.
- `requests_max` (integer; required): The most model requests the step can make
  (provider retries aside).
- `reused` (boolean; required): Whether the step's saved output will be reused,
  so it costs nothing.
- `verifier` (boolean; required): Whether `expected_usd`, `max_usd` and
  `requests_max` include the step's verifier requests; `False` for a reused
  step.

## Estimate constants

The figures the cost estimate and the `max_cost` checks use.

- `PROMPT_CHARS_PER_TOKEN` = `4`: Characters of prompt text per input token, for
  the estimate.
- `TEXT_CHARS_PER_OUTPUT_TOKEN` = `2`: Characters of a page's text layer per
  output token of its extraction, beyond `TYPICAL_PAGE_OUTPUT_TOKENS`, for the
  estimate. The answer repeats the text with an item's fields around it.
- `TYPICAL_BREAK_OUTPUT_TOKENS` = `4000`: The output tokens of a typical
  page-break verdict, thinking included, for the estimate.
- `TYPICAL_BREAK_VERDICT_OUTPUT_TOKENS` = `3000`: The output tokens of a typical
  review of a page-break verdict, thinking included, for the estimate.
- `TYPICAL_OUTPUT_TOKENS` = `8000`: The output tokens of a typical survey
  answer, thinking included, for the estimate.
- `TYPICAL_PAGE_OUTPUT_TOKENS` = `4000`: The output tokens of a typical page
  extraction, thinking included, before the page's text is counted, for the
  estimate.
- `TYPICAL_SURVEY_VERDICT_OUTPUT_TOKENS` = `6000`: The output tokens of a
  typical verdict on the survey, thinking included, for the estimate: three
  quarters of a typical survey answer, as for a page.
- `TYPICAL_VERDICT_OUTPUT_TOKENS` = `3000`: The output tokens of a typical
  verdict on a page, thinking included, for the estimate.

- `anthropic`: 4,784 image and 3,000 text input tokens per PDF page; uploads
  kept 1 to 2,160 hours.
- `openai`: 3,000 image and 3,000 text input tokens per PDF page; uploads kept 1
  to 720 hours.

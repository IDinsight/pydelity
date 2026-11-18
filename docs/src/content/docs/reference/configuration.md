---
title: Configuration
description: Every setting pydelity reads, with its type, default and meaning.
sidebar:
  order: 1
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

Settings come from the command's options, from a JSON or YAML config file
(`--config`), or from keyword arguments to the Python functions. Options and
keyword arguments win over the file, and the file wins over the defaults.
Settings under `advanced` are set in the file or as an `advanced` mapping in
Python.

## Top-level settings

All the settings for a pydelity run.

- `advanced` (object ([`advanced`](#advanced))): Settings most runs never need
  to change.
- `instructions` (string or null; default `null`): Extra instructions for the
  model about this PDF.
- `languages` (list of strings; default `[]`): The PDF's languages as BCP-47
  tags such as `en` or `ar`, in standard form.
- `max_cost` (number or null; more than 0; default `null`): The most the output
  folder's model requests may cost, in US dollars.
- `model` (string; default `"anthropic:claude-opus-5-5"`): The model, as
  `<provider>:<model-id>`; provider `anthropic` or `openai`.

  The model ID is sent to the provider as given.

- `output_dir` (path or null; default `null`): The output folder;
  `pydelity-output/<PDF name>` in the current folder if unset.
- `overwrite` (boolean; default `false`): Whether to redo steps whose outputs
  could be reused.
- `pdf` (path; required): The PDF to process.

## `advanced`

Settings most runs never need to change.

- `models` (map of string to object
  ([`advanced.models.<provider>:<model-id>`](#advancedmodelsprovidermodel-id));
  default `{}`): Prices for models, by `<provider>:<model-id>`.
- `provider_retries` (integer; at least 0; at most 10; default `2`): How many
  times a request to the provider is retried after a temporary failure.
- `survey` (object ([`advanced.survey`](#advancedsurvey))): Settings for the
  survey step.
- `uploads` (object ([`advanced.uploads`](#advanceduploads))): Settings for PDFs
  uploaded to the provider.

## `advanced.models.<provider>:<model-id>`

Prices for one model, in US dollars per million tokens.

- `cache_read_usd_per_mtok` (number or null; at least 0; default `null`): Price
  of input tokens read from the prompt cache; the input price if unset.
- `cache_write_usd_per_mtok` (number or null; at least 0; default `null`): Price
  of input tokens written to the prompt cache; the input price if unset.
- `input_usd_per_mtok` (number; at least 0; required): Price of input tokens.
- `output_usd_per_mtok` (number; at least 0; required): Price of output tokens.

## `advanced.survey`

Settings for the survey step.

- `check_retries` (integer; at least 0; at most 5; default `2`): How many times
  the model may answer again after failing the survey's checks.
- `effort` (one of `low`, `medium`, `high`; default `"high"`): How hard the
  model thinks before answering.
- `max_output_tokens` (integer; more than 0; default `32000`): The most tokens
  one model answer may contain, thinking included.
- `request_timeout_seconds` (number; more than 0; default `900`): How long to
  wait for one model request before it counts as failed.

## `advanced.uploads`

Settings for PDFs uploaded to the provider.

- `expiry_hours` (integer or null; at least 1; default `null`): How long the
  provider keeps an uploaded PDF; the provider's maximum if unset.

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
- `languages` (list of strings; default `[]`): The PDF's languages as BCP-47
  tags such as `en` or `ar`, in standard form.
- `max_cost` (number or null; more than 0; default `null`): The most the output
  folder's model requests may cost, in US dollars.
- `model` (string or null; default `null`): The model for every step, as
  `<provider>:<model-id>`; each step's default if unset.

  The provider is `anthropic` or `openai`, and the model ID is sent to the
  provider as given.

- `output_dir` (path or null; default `null`): The output folder;
  `pydelity-output/<PDF name>` in the current folder if unset.
- `overwrite` (boolean; default `false`): Whether to redo steps whose outputs
  could be reused.
- `pages` (string or null; default `null`): The pages to extract, numbered from
  1 as a PDF viewer shows them, such as `1-5,8`; every page if unset. The survey
  always reads every page.

  Page-break verification runs only when every page has an up-to-date page file,
  from this run or an earlier one.

- `pause` (boolean; default `true`): Whether to stop after a step that wrote new
  output, so it can be checked before the next step is paid for.
- `pdf` (path; required): The PDF to process.
- `verify` (boolean; default `false`): Whether a verifier reviews each step's
  answer.

  The verifier is a second request to the step's model, which checks the answer
  against the PDF and may correct it. Each verifier request adds cost.

## `advanced`

Settings most runs never need to change.

- `extraction` (object ([`advanced.extraction`](#advancedextraction))): Settings
  for page extraction.
- `models` (map of string to object
  ([`advanced.models.<provider>:<model-id>`](#advancedmodelsprovidermodel-id));
  default `{}`): Prices for models, by `<provider>:<model-id>`.
- `page_breaks` (object ([`advanced.page_breaks`](#advancedpage_breaks))):
  Settings for page-break verification.
- `provider_retries` (integer; at least 0; at most 10; default `2`): How many
  times a request to the provider is retried after a temporary failure.
- `survey` (object ([`advanced.survey`](#advancedsurvey))): Settings for the
  survey step.
- `uploads` (object ([`advanced.uploads`](#advanceduploads))): Settings for PDFs
  uploaded to the provider.

## `advanced.extraction`

Settings for page extraction.

- `check_retries` (integer; at least 0; at most 5; default `2`): How many times
  a model may answer again after failing page extraction's checks.
- `concurrent_pages` (integer; at least 1; at most 32; default `8`): How many
  pages are extracted at the same time.
- `effort` (one of `low`, `medium`, `high`; default `"high"`): How hard the
  model thinks before answering.
- `instructions` (string or null; default `null`): What is particular, different
  or nuanced about this PDF, in your own words, for page extraction's model and
  its verifier. Blank text counts as unset.
- `max_output_tokens` (integer; more than 0; default `32000`): The most tokens
  one model answer may contain, thinking included.
- `model` (string or null; default `null`): The model for page extraction, as
  `<provider>:<model-id>`; `model`, or else page extraction's default, if unset.
- `request_timeout_seconds` (number; more than 0; default `600`): How long to
  wait for one model request before it counts as failed.
- `verify` (boolean or null; default `null`): Whether a verifier reviews each
  page's extraction; `verify` if unset.

## `advanced.models.<provider>:<model-id>`

Prices for one model, in US dollars per million tokens.

- `cache_read_usd_per_mtok` (number or null; at least 0; default `null`): Price
  of input tokens read from the prompt cache; the input price if unset.
- `cache_write_usd_per_mtok` (number or null; at least 0; default `null`): Price
  of input tokens written to the prompt cache; the input price if unset.
- `input_usd_per_mtok` (number; at least 0; required): Price of input tokens.
- `output_usd_per_mtok` (number; at least 0; required): Price of output tokens.

## `advanced.page_breaks`

Settings for page-break verification.

- `check_retries` (integer; at least 0; at most 5; default `2`): How many times
  a model may answer again after failing page-break verification's checks.
- `concurrent_breaks` (integer; at least 1; at most 32; default `8`): How many
  page breaks are judged at the same time.
- `effort` (one of `low`, `medium`, `high`; default `"high"`): How hard the
  model thinks before answering.
- `instructions` (string or null; default `null`): What is particular, different
  or nuanced about this PDF's page breaks, in your own words, for page-break
  verification's model and its verifier. Blank text counts as unset.
- `max_output_tokens` (integer; more than 0; default `32000`): The most tokens
  one model answer may contain, thinking included.
- `model` (string or null; default `null`): The model for page-break
  verification, as `<provider>:<model-id>`; `model`, or else page-break
  verification's default, if unset.
- `request_timeout_seconds` (number; more than 0; default `600`): How long to
  wait for one model request before it counts as failed.
- `verify` (boolean or null; default `null`): Whether a verifier reviews each
  page break's verdict; `verify` if unset.

## `advanced.survey`

Settings for the survey step.

- `check_retries` (integer; at least 0; at most 5; default `2`): How many times
  the model may answer again after failing the survey's checks.
- `effort` (one of `low`, `medium`, `high`; default `"high"`): How hard the
  model thinks before answering.
- `instructions` (string or null; default `null`): What is particular, different
  or nuanced about this PDF, in your own words, for the survey's model and its
  verifier. Blank text counts as unset.
- `max_output_tokens` (integer; more than 0; default `32000`): The most tokens
  one model answer may contain, thinking included.
- `request_timeout_seconds` (number; more than 0; default `900`): How long to
  wait for one model request before it counts as failed.
- `verify` (boolean or null; default `null`): Whether a verifier reviews the
  survey's answer; `verify` if unset.

## `advanced.uploads`

Settings for PDFs uploaded to the provider.

- `expiry_hours` (integer or null; at least 1; default `null`): How long the
  provider keeps an uploaded PDF; the provider's maximum if unset.

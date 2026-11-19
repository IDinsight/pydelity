---
title: run.json
description: Every field of run.json.
sidebar:
  order: 6
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

The contents of `run.json`: one run on one PDF.

## `run.json`

The contents of `run.json`: one run on one PDF.

- `cost` (object ([`cost`](#cost)); required): What the run's model requests
  cost.
- `ended_at` (date and time (ISO 8601) or null; required): When the run ended
  (UTC); `None` while it runs.
- `error` (string or null; required): Why the run failed, stopped or was
  interrupted, if it was.
- `pdf` (object ([`pdf`](#pdf)); required): The PDF.
- `pydelity_version` (string; required): The pydelity version that ran.
- `review` (list of objects ([`review[]`](#review)); required): The review
  issues of every step output the run used, reused ones included.
- `run_id` (string; required): The run's ID: its start time (UTC) and a random
  suffix.
- `schema_version` (string; required): The version of this file's schema,
  `"MAJOR.MINOR"`.
- `settings` (map of string to any value; required): The resolved settings,
  which hold no API keys.
- `started_at` (date and time (ISO 8601); required): When the run started (UTC).
- `status` (one of `running`, `completed`, `failed`, `stopped`, `interrupted`;
  required): How the run ended, or `running`.
- `steps` (list of objects ([`steps[]`](#steps)); required): What each step did.
- `warnings` (list of objects ([`warnings[]`](#warnings)); required): The
  user-facing warnings, in the order they were issued.

## `cost`

What a run's model requests cost, from `cost.jsonl`.

- `by_step` (map of string to number; required): This run's priced requests,
  summed by step.
- `output_folder_usd` (number; required): Every priced request recorded in the
  output folder, from every run.
- `run_usd` (number; required): This run's priced requests.
- `unpriced_requests` (integer; required): How many of this run's requests have
  no known price.

## `pdf`

The PDF a run processed.

- `bytes` (integer; required): The PDF's size in bytes.
- `page_count` (integer; required): The PDF's number of pages.
- `path` (string; required): The PDF's path, as given.
- `sha256` (string; required): The PDF's SHA-256 hex digest.

## `review[]`

A problem a person should review.

- `check` (one of `labels`, `regions`, `rotation`, `page_numbering`,
  `artifacts`, `writing_direction`, `languages` or one of `rotation_differs`,
  `page_number_differs`; required): The check or comparison that found the
  problem.
- `details` (map of string to any value; required): The values the problem is
  about, such as `{"measured": 90, "profile": 0}`.
- `message` (string; required): What is wrong.
- `page_index` (integer or null; required): The page the problem is on, or
  `None` when no single page applies.
- `step` (one of `survey`; required): The step whose check found the problem.

## `steps[]`

What one step of a run did.

- `cost_usd` (number; required): What the step's priced requests in this run
  cost.
- `ended_at` (date and time (ISO 8601) or null; required): When the step ended
  (UTC).
- `error` (string or null; required): Why the step failed or stopped, if it did.
- `name` (string; required): The step, such as `survey`.
- `outputs` (list of strings; required): The files the step wrote or reused, by
  name.
- `pdf_transport` (one of `upload`, `request` or null; required): How the PDF
  went to the model: `upload` or `request`; `None` when no request carried it.
- `requests` (integer; required): How many model requests the step made in this
  run.
- `started_at` (date and time (ISO 8601); required): When the step started
  (UTC).
- `status` (one of `completed`, `reused`, `failed`, `stopped`, `skipped`;
  required): How the step ended.

## `warnings[]`

A user-facing warning the run issued.

- `code` (one of `damaged_output`, `max_cost_exceeded`, `other_pdf_in_folder`,
  `probe_unavailable`, `unpriced_model`, `upload_fallback`; required): The kind
  of warning.
- `details` (map of string to any value; required): The values the warning is
  about.
- `message` (string; required): The warning's text.
- `step` (string or null; required): The step that issued it, or `None` when no
  step was running.

---
title: run.json
description: Every field of run.json.
sidebar:
  order: 8
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
- `status` (one of `running`, `completed`, `paused`, `failed`, `stopped`,
  `interrupted`; required): How the run ended, or `running`.
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

- `check` (one of `ids`, `continues`, `duplicates`, `joins`, `furniture`,
  `header_rows`, `repeats`, `markers` or `verdicts_differ` or `start_markers` or
  one of `labels`, `content`, `languages`, `boxes`, `containers`, `captions` or
  one of `reading_order`, `artifacts`, `form_fields`, `text_dropped`,
  `text_added` or `no_matching_label` or one of `labels`, `regions`, `rotation`,
  `page_numbering`, `artifacts`, `writing_direction`, `languages` or one of
  `rotation_differs`, `page_number_differs` or `verifier`; required): What found
  the problem: a check, a hint or another source. `step` says whose, since two
  steps can have checks and hints of the same name.
- `details` (map of string to any value; required): The values the problem is
  about. A survey hint gives values such as `{"measured": 90, "profile": 0}`,
  and a check gives its failure's `details`, such as `{"item_ref": "t3"}` on a
  page or `{"item": "p0004-002"}` on a page break. A `no_matching_label` issue
  gives the `kind` and `role` that no label fits, with the items' refs and IDs
  (`item_refs`, `item_ids`). A `verifier` issue gives the problem's `category`,
  with its `item_ref` on a page and its `item` on a page break. A
  `verdicts_differ` issue gives the difference's `details`, with the `field`,
  the `kept` and `verifier` values, and the `item`, `entry` and `cell` where
  they apply.
- `item_id` (string or null; required): The item the problem is about, or `None`
  when no single item applies.
- `message` (string; required): What is wrong.
- `page_index` (integer or null; required): The page the problem is on, or
  `None` when no single page applies. For page-break verification, it is the
  page before the break.
- `step` (one of `survey`, `extraction`, `page_breaks`; required): The step
  whose check found the problem.

## `steps[]`

What one step of a run did.

- `breaks` (object ([`steps[].breaks`](#stepsbreaks)) or null; required): How
  many breaks the step judged and reused; `None` for a step other than
  page-break verification, and for a page-break verification step that was
  skipped.
- `cost_usd` (number; required): What the step's priced requests in this run
  cost.
- `ended_at` (date and time (ISO 8601) or null; required): When the step ended
  (UTC).
- `error` (string or null; required): Why the step failed or stopped, if it did.
- `name` (string; required): The step, such as `survey`.
- `outputs` (list of strings; required): The files the step wrote or reused, by
  name.
- `pages` (object ([`steps[].pages`](#stepspages)) or null; required): How many
  pages the step selected, extracted and reused; `None` for a step other than
  page extraction, and for a page extraction step that was skipped.
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

- `code` (one of `damaged_output`, `max_cost_exceeded`, `missing_page_files`,
  `other_pdf_in_folder`, `probe_unavailable`, `unpriced_model`,
  `upload_fallback`; required): The kind of warning.
- `details` (map of string to any value; required): The values the warning is
  about.
- `message` (string; required): The warning's text.
- `step` (string or null; required): The step that issued it, or `None` when no
  step was running.

## `steps[].breaks`

How many breaks between pages page-break verification judged and reused.

- `judged` (integer; required): The breaks whose verdict file this run wrote,
  with or without a request.
- `reused` (integer; required): The breaks whose saved verdict file was reused.
- `total` (integer; required): The breaks in the PDF, one fewer than its pages.

## `steps[].pages`

How many pages a page step selected, extracted and reused.

- `extracted` (integer; required): The selected pages extracted in this run.
- `reused` (integer; required): The selected pages whose saved output was
  reused.
- `selected` (integer; required): The pages selected with `pages`; every page
  when it is unset.

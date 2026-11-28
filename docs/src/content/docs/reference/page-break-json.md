---
title: page_breaks/<NNNN>-<NNNN>.json
description: Every field of a verdict file, page_breaks/<NNNN>-<NNNN>.json.
sidebar:
  order: 7
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

The contents of `page_breaks/<NNNN>-<NNNN>.json`: one break's verdict.

## `page_breaks/<NNNN>-<NNNN>.json`

The contents of `page_breaks/<NNNN>-<NNNN>.json`: one break's verdict.

- `checks` (list of objects ([`checks[]`](#checks)); required): The result of
  each check on the kept verdict, in the order the checks run.
- `earlier_page_index` (integer; required): The page before the break (0-based).
- `fingerprint` (string; required): `sha256:` fingerprint of `inputs`; a
  matching file is reused.
- `hints` (list of objects ([`hints[]`](#hints)); required): Each hint's
  differences on the kept verdict, in the order the hints run, whether or not
  the review list shows them.
- `inputs` (object ([`inputs`](#inputs)); required): What the verdict depends
  on.
- `issues` (list of objects ([`issues[]`](#issues)); required): The break's
  review issues: checks still failing on the kept verdict, hint differences, and
  verifier problems that were not corrected. Hint differences are listed unless
  the verifier passed the verdict or its correction was kept, so on a break no
  verifier reviewed every one is listed. The `hints` list keeps them either way.
- `judged_at` (date and time (ISO 8601); required): When the verdict file was
  written (UTC).
- `judgment` (one of `model`, `no_content`; required): How the verdict was made:
  `model` when a model judged the break, or `no_content` when a page of the
  break has no content items, so nothing can continue and no request was made.
- `later_page_index` (integer; required): The page after the break (0-based):
  `earlier_page_index` plus 1.
- `pydelity_version` (string; required): The pydelity version that wrote the
  file.
- `schema_version` (string; required): The version of this file's schema,
  `"MAJOR.MINOR"`.
- `verdict` (object ([`verdict`](#verdict)); required): The kept verdict: the
  judge's, or the verifier's correction when it was kept.
- `verification` (object ([`verification`](#verification)) or null; required):
  The verifier's review; `None` when no verifier reviewed the verdict.

## `checks[]`

The result of one check on the break's kept verdict.

- `attempts` (integer; required): How many verdicts were checked: 1 plus the
  retries used.
- `failures` (list of objects ([`checks[].failures[]`](#checksfailures));
  required): The problems the check found in the kept verdict. A review issue
  made from a failure names its item by ID in `item_id`.
- `name` (one of `ids`, `continues`, `duplicates`, `joins`, `furniture`,
  `header_rows`, `repeats`, `markers`; required): The check.
- `passed` (boolean; required): Whether the kept verdict passed: `failures` is
  empty.

## `hints[]`

How the break's kept verdict compares with one hint.

- `differences` (list of objects ([`checks[].failures[]`](#checksfailures));
  required): Where the kept verdict differs from what the survey found; empty
  when it agrees. A review issue made from a difference names its item by ID in
  `item_id`.
- `name` (`start_markers`; required): The hint.

## `inputs`

What a break's verdict depends on, which its fingerprint covers.

- `context` (object ([`inputs.context`](#inputscontext)); required): What the
  break's requests are made from besides its two pages.
- `earlier` (object ([`inputs.earlier`](#inputsearlier)); required): The page
  before the break and its page file.
- `later` (object ([`inputs.earlier`](#inputsearlier)); required): The page
  after the break and its page file.
- `model` (string; required): The model, as `<provider>:<model-id>`.
- `pdf_sha256` (string; required): The PDF's SHA-256 hex digest.
- `prompt_version` (integer; required): The version of page-break verification's
  prompts.
- `rendering` (object ([`inputs.rendering`](#inputsrendering)); required): How
  the page images were made.
- `settings` (object ([`inputs.settings`](#inputssettings)); required): The
  page-break verification settings used.

## `issues[]`

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

## `verdict`

A verdict on one break: whether content continues across it, and how.

- `containers` (list of objects ([`verdict.containers[]`](#verdictcontainers));
  required): Each bordered or shaded box that continues across the break, also
  when the content inside it starts a new unit on the later page; empty when
  none does.
- `continues` (boolean; required): Whether any content carries on from the
  earlier page to the later page.
- `pieces` (list of objects ([`verdict.pieces[]`](#verdictpieces)); required):
  Each piece of content that carries on across the break; empty when nothing
  continues.
- `reason` (string; required): Why, in a sentence or two, quoting the text that
  decides it.

## `verification`

The verifier's review of the break's verdict.

- `attempts` (integer; required): How many verdicts the verifier gave: 1 plus
  the retries its correction used.
- `correction_applied` (boolean; required): Whether the verifier's corrected
  verdict replaced the judge's. A correction replaces it when it passes every
  check, whatever its hint differences.
- `correction_failures` (list of objects ([`checks[]`](#checks)); required): The
  checks a correction that was not applied still failed; empty when it was
  applied or there was none.
- `verdict` (object ([`verification.verdict`](#verificationverdict)); required):
  The verdict as the verifier gave it.

## `checks[].failures[]`

A problem a check found in a model's answer, or a difference from a hint.

- `details` (map of string to any value; required): The values the problem is
  about. A survey check gives the proposed value and, where it applies, what it
  was checked against, such as `{"proposed": 9, "page_count": 6}`, and a survey
  hint gives the measured value and the profile's, such as
  `{"measured": 90, "profile": 0}`. A page extraction check or hint gives the
  ref that the model's answer gave the item or container, or `None` when no
  single one applies, such as `{"item_ref": "t3"}`. That ref comes from the
  answer, and the page file's items have IDs instead. A page-break verification
  check or hint gives the IDs of the item, list entry or container it is about,
  and the row and cell of a table cell, such as `{"item": "p0004-002"}` or
  `{"cell": 1, "item": "p0004-002", "row": 0}`. A difference between two
  verdicts for the same break gives the `field` that differs, each verdict's
  value as `kept` and `verifier`, the `item` and `entry` where the piece ends on
  the earlier page, and the `cell` of a cell join, such as
  `{"entry": "p0004-002.3", "field": "join", "item": "p0004-002", "kept": "continue_entry", "verifier": "new_entry"}`.
- `message` (string; required): What is wrong or differs, starting with the name
  of the check, hint or comparison.
- `page_index` (integer or null; required): The page the problem is on, or
  `None` when no single page applies.

## `inputs.context`

What a break's requests are made from besides its two pages.

- `continuation_notes` (list of strings; required): The survey's notes on how
  content continues from one page to the next.
- `instructions` (string or null; required): The user's page-break verification
  instructions, if any.
- `page_count` (integer; required): The PDF's number of pages.
- `start_markers` (list of objects
  ([`inputs.context.start_markers[]`](#inputscontextstart_markers)); required):
  The survey's start markers: text that marks where a new unit of content
  starts.

## `inputs.earlier`

One page of a break and the page file the verdict was made from.

- `page_file_sha256` (string; required): `sha256:` digest of the page file's
  bytes, as written.
- `page_index` (integer; required): The page (0-based).

## `inputs.rendering`

How page images and figure crops are made.

- `crop_dpi` (integer; required): The resolution of figure crops, in dots per
  inch.
- `jpeg_quality` (integer; required): The JPEG quality of page images, from 0
  to 100.
- `max_dpi` (integer; required): The highest resolution of a page image, in dots
  per inch.

## `inputs.settings`

The page-break verification settings a verdict depends on.

- `check_retries` (integer; required): How many times a model could answer again
  after failing the checks.
- `effort` (one of `low`, `medium`, `high`; required): How hard the models
  thought before answering.
- `max_output_tokens` (integer; required): The most tokens one model answer
  could contain, thinking included.

## `verdict.containers[]`

A bordered or shaded box that continues across the break.

- `earlier` (string; required): The box's container ID on the earlier page.
- `later` (string; required): The box's container ID on the later page.

## `verdict.pieces[]`

A piece of content that carries on from the earlier page to the later page.

- `cell_joins` (list of (one of `space`, `no_space`, `dehyphenate`, `newline`,
  `repeat` or null) or null; required): For `merge_split_row`, one value per
  cell of the later page's merged row (its first row after the repeated header
  rows), in the row's cell order: how that cell's text joins the text of the
  cell above it on the earlier page (`space`, `no_space` or `dehyphenate`),
  `repeat` when the later cell only repeats the earlier cell's text, such as a
  row label printed again, so that the text is kept once, or null when either
  cell has no text. Null for every other join.
- `earlier_entry` (string or null; required): When the piece ends in a list
  entry on the earlier page, that entry's ID; null otherwise.
- `earlier_item` (string; required): The ID of the item where the piece ends on
  the earlier page.
- `join` (one of `continue_text`, `continue_entry`, `new_entry`, `append_rows`,
  `merge_split_row`; required): How the piece joins across the break.
- `later_entry` (string or null; required): When the piece starts in a list
  entry on the later page, that entry's ID; null otherwise.
- `later_item` (string; required): The ID of the item where the piece starts on
  the later page.
- `markers` (list of objects
  ([`verdict.pieces[].markers[]`](#verdictpiecesmarkers)); required): Words or
  symbols on the continued unit on the later page that say it continues; empty
  when there are none.
- `repeated_header_rows` (integer or null; required): For `append_rows` and
  `merge_split_row`, how many rows at the top of the later page's table repeat
  the earlier table's header, 0 when none do; null for every other join.
- `repeated_items` (list of strings; required): The IDs of items on the later
  page, before the continued unit, that repeat what the earlier page printed for
  it, such as a repeated title; empty when there are none.
- `text_join` (one of `space`, `no_space`, `dehyphenate`, `newline`, `repeat` or
  null; required): For `continue_text` and `continue_entry`, how the two pieces
  of text join: `space`, `no_space` or `dehyphenate`, or `newline` between code
  items. Null for every other join.

## `verification.verdict`

The verifier's verdict on one break's verdict.

- `corrected` (object ([`verdict`](#verdict)) or null; required): The whole
  verdict given again with the problems fixed; null when the verdict passed or
  cannot be corrected.
- `passed` (boolean; required): Whether the verdict is right, with nothing to
  fix.
- `problems` (list of objects
  ([`verification.verdict.problems[]`](#verificationverdictproblems));
  required): The problems found; empty when the verdict passed.

## `inputs.context.start_markers[]`

Text that marks where a new unit of content starts.

- `description` (string; required): What starts where the text appears.
- `text` (string; required): The text, as printed.

## `verdict.pieces[].markers[]`

Words or symbols on the continued unit that say it continues.

- `cell` (integer or null; required): When a table cell carries the marker, the
  cell's position in its row, from 0; null otherwise.
- `item` (string; required): The ID of the item on the later page that carries
  the marker.
- `row` (integer or null; required): When a table cell carries the marker, the
  row's position among the table's rows, from 0; null otherwise.
- `text` (string; required): The marker, as printed.

## `verification.verdict.problems[]`

A problem the verifier found in a verdict.

- `category` (one of `continues`, `piece`, `join`, `header_rows`,
  `repeated_items`, `markers`, `containers`, `other`; required): What kind of
  problem it is.
- `description` (string; required): What is wrong and where, so that a person
  can find it.
- `item` (string or null; required): The ID of the item or container on either
  page the problem is about; null when it is about no single one, such as
  content that continues but is missing from the verdict.

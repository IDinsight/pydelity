---
title: pages/<NNNN>.json
description: Every field of a page file, pages/<NNNN>.json.
sidebar:
  order: 6
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

The contents of `pages/<NNNN>.json`: one page's items, checks and hints.

## `pages/<NNNN>.json`

The contents of `pages/<NNNN>.json`: one page's items, checks and hints.

- `checks` (list of objects ([`checks[]`](#checks)); required): The result of
  each check on the kept answer, in the order the checks run.
- `column_order` (one of `left_to_right`, `right_to_left` or null; required): On
  a page written top to bottom, the order its columns are read in; `None` on
  other pages.
- `containers` (list of objects ([`containers[]`](#containers)); required): The
  bordered or shaded boxes on the page.
- `extracted_at` (date and time (ISO 8601); required): When the page file was
  written (UTC).
- `fingerprint` (string; required): `sha256:` fingerprint of `inputs`; a
  matching file is reused.
- `height_pt` (number; required): The displayed page's height in points.
- `hints` (list of objects ([`hints[]`](#hints)); required): Each hint's
  differences on the kept answer, in the order the hints run, whether or not the
  review list shows them.
- `image` (object ([`image`](#image)); required): The size of the page image the
  models were sent.
- `inputs` (object ([`inputs`](#inputs)); required): What the page's extraction
  depends on.
- `issues` (list of objects ([`issues[]`](#issues)); required): The page's
  review issues: checks still failing on the kept answer, hint differences,
  content no label fits, and verifier problems that were not corrected. Hint
  differences are listed unless the verifier passed the page or its correction
  was kept, so on a page no verifier reviewed every one is listed. The `hints`
  list keeps them either way.
- `items` (list of objects ([`items[]`](#items)); required): The page's items,
  in reading order.
- `page_index` (integer; required): The page (0-based).
- `page_number` (integer; required): The page's number from 1, as a PDF viewer
  shows it.
- `pydelity_version` (string; required): The pydelity version that wrote the
  file.
- `rotation` (one of `0`, `90`, `180`, `270`; required): The clockwise rotation
  applied to make the page upright for the models.
- `schema_version` (string; required): The version of this file's schema,
  `"MAJOR.MINOR"`.
- `text_comparison` (one of `compared`, `no_text_layer`, `garbled_text_layer`,
  `text_layer_mismatch`; required): Whether the items' text was compared with
  the page's text layer, and if not, why.
- `verification` (object ([`verification`](#verification)) or null; required):
  The verifier's review; `None` when no verifier reviewed the page.
- `width_pt` (number; required): The displayed page's width in points.
- `writing_direction` (one of `ltr`, `rtl`, `ttb`; required): The page's writing
  direction.

## `checks[]`

The result of one check on the page's kept answer.

- `attempts` (integer; required): How many answers were checked: 1 plus the
  retries used.
- `failures` (list of objects ([`checks[].failures[]`](#checksfailures));
  required): The problems the check found in the kept answer. A review issue
  made from a failure names its item by ID in `item_id`.
- `name` (one of `labels`, `content`, `languages`, `boxes`, `containers`,
  `captions`; required): The check.
- `passed` (boolean; required): Whether the kept answer passed: `failures` is
  empty.

## `containers[]`

A bordered or shaded box on the page that holds items.

- `bbox` (list of numbers; required): The box's `[x0, y0, x1, y1]` in points on
  the displayed page.
- `container` (string or null; required): The ID of the container this box sits
  inside, or `None`.
- `id` (string; required): The container's ID, such as `p0003-c01`: the page
  index and its position among the page's containers.
- `label` (string; required): The container's label from the profile.

## `hints[]`

How the page's kept answer compares with one hint.

- `differences` (list of objects ([`checks[].failures[]`](#checksfailures));
  required): Where the kept answer differs from what code measured or the survey
  found; empty when it agrees. A review issue made from a difference names its
  item by ID in `item_id`.
- `name` (one of `reading_order`, `artifacts`, `form_fields`, `text_dropped`,
  `text_added`; required): The hint.

## `image`

The size of the page image the models were sent.

- `height_px` (integer; required): Its height in pixels.
- `width_px` (integer; required): Its width in pixels.

## `inputs`

What a page's extraction depends on, which its fingerprint covers.

- `context` (object ([`inputs.context`](#inputscontext)); required): The page's
  context.
- `model` (string; required): The model, as `<provider>:<model-id>`.
- `pdf_sha256` (string; required): The PDF's SHA-256 hex digest.
- `prompt_version` (integer; required): The version of the extraction and
  verifier prompts.
- `rendering` (object ([`inputs.rendering`](#inputsrendering)); required): How
  the page image and the figure crops were made.
- `settings` (object ([`inputs.settings`](#inputssettings)); required): The page
  extraction settings used.

## `issues[]`

A problem a person should review.

- `check` (one of `labels`, `content`, `languages`, `boxes`, `containers`,
  `captions` or one of `reading_order`, `artifacts`, `form_fields`,
  `text_dropped`, `text_added` or `no_matching_label` or one of `labels`,
  `regions`, `rotation`, `page_numbering`, `artifacts`, `writing_direction`,
  `languages` or one of `rotation_differs`, `page_number_differs` or `verifier`;
  required): What found the problem: a check, a hint or another source. `step`
  says whose, since two steps can have checks and hints of the same name.
- `details` (map of string to any value; required): The values the problem is
  about. A survey hint gives values such as `{"measured": 90, "profile": 0}`,
  and a check gives its failure's `details`, such as `{"item_ref": "t3"}` on a
  page. A `no_matching_label` issue gives the `kind` and `role` that no label
  fits, with the items' refs and IDs (`item_refs`, `item_ids`). A `verifier`
  issue gives the problem's `category`, and on a page its `item_ref`.
- `item_id` (string or null; required): The item the problem is about, or `None`
  when no single item applies.
- `message` (string; required): What is wrong.
- `page_index` (integer or null; required): The page the problem is on, or
  `None` when no single page applies.
- `step` (one of `survey`, `extraction`; required): The step whose check found
  the problem.

## `items[]`

One item on the page, in the page file.

- `bbox` (list of numbers; required): The item's `[x0, y0, x1, y1]` in points on
  the displayed page.
- `caption_of` (string or null; required): For a caption, the ID of the item it
  captions; `None` for other items.
- `container` (string or null; required): The ID of the container the item sits
  inside, or `None`.
- `entries` (list of objects ([`items[].entries[]`](#itemsentries)) or null;
  required): A list's entries in reading order; `None` for other kinds.
- `field` (object ([`items[].field`](#itemsfield)) or null; required): A field's
  content; `None` for other kinds.
- `figure` (object ([`items[].figure`](#itemsfigure)) or null; required): A
  figure's content; `None` for other kinds.
- `id` (string; required): The item's ID, such as `p0003-007`: the page index
  and its position in reading order from 1. The same extraction always gives the
  same IDs.
- `kind` (one of `code`, `field`, `figure`, `formula`, `list`, `table`, `text`;
  required): What kind of content the item holds.
- `label` (string; required): The item's label from the profile.
- `language` (string or null; required): The BCP-47 tag of the item's text, in
  standard form; `None` when the item has no text.
- `latex` (string or null; required): A formula in LaTeX; `None` for other
  kinds.
- `role` (one of `artifact`, `aside`, `body`, `caption`, `footnote`, `heading`,
  `navigation`; required): The role the item plays on the page.
- `table` (object ([`items[].table`](#itemstable)) or null; required): A table's
  content; `None` for other kinds.
- `text` (string or null; required): The text of a text, code or formula item,
  as printed; `None` for other kinds.

## `verification`

The verifier's review of the page's extraction.

- `attempts` (integer; required): How many verdicts the verifier gave: 1 plus
  the retries its correction used.
- `correction_applied` (boolean; required): Whether the verifier's corrected
  extraction replaced the extraction model's. A correction replaces it when it
  passes every check, whatever its hint differences.
- `correction_failures` (list of objects ([`checks[]`](#checks)); required): The
  checks a correction that was not applied still failed; empty when it was
  applied or there was none.
- `verdict` (object ([`verification.verdict`](#verificationverdict)); required):
  The verdict as the verifier gave it.

## `checks[].failures[]`

One problem a check found in a model's answer.

- `details` (map of string to any value; required): The values the problem is
  about. A survey check gives the proposed value and, where it applies, what it
  was checked against, such as `{"proposed": 9, "page_count": 6}`. A page
  extraction check gives the ref that the model's answer gave the item or
  container, or `None` when no single one applies, such as `{"item_ref": "t3"}`.
  That ref comes from the answer, and the page file's items have IDs instead.
- `message` (string; required): What is wrong, starting with the check's name.
- `page_index` (integer or null; required): The page the problem is on, or
  `None` when no single page applies.

## `inputs.context`

What one page's requests are made from and its answers are checked against.

- `form_fields` (list of objects
  ([`inputs.context.form_fields[]`](#inputscontextform_fields)); required): The
  PDF's fillable form fields on the page, with boxes in points on the displayed
  page; empty when there are none or the form could not be read.
- `height_pt` (number; required): The displayed page's height in points.
- `instructions` (string or null; required): The user's page extraction
  instructions, if any.
- `labels` (list of objects ([`inputs.context.labels[]`](#inputscontextlabels));
  required): The profile's labels.
- `languages` (list of strings; required): The profile's languages, as BCP-47
  tags in standard form.
- `page_count` (integer; required): The PDF's number of pages.
- `page_index` (integer; required): The page (0-based).
- `repeated_lines` (list of objects
  ([`inputs.context.repeated_lines[]`](#inputscontextrepeated_lines));
  required): The repeated lines that appear on the page.
- `rotation` (one of `0`, `90`, `180`, `270`; required): The clockwise rotation,
  from the profile, that makes the page upright.
- `rotation_attribute` (integer; required): The page's rotation attribute in the
  PDF, in degrees.
- `text_quality` (one of `none`, `good`, `garbled`; required): Whether the
  page's text layer is readable, as measured.
- `width_pt` (number; required): The displayed page's width in points.
- `writing_direction` (one of `ltr`, `rtl`, `ttb`; required): The page's writing
  direction, from the profile.

## `inputs.rendering`

How page images and figure crops are made.

- `crop_dpi` (integer; required): The resolution of figure crops, in dots per
  inch.
- `jpeg_quality` (integer; required): The JPEG quality of page images, from 0
  to 100.
- `max_dpi` (integer; required): The highest resolution of a page image, in dots
  per inch.

## `inputs.settings`

The page extraction settings a page's result depends on.

- `check_retries` (integer; required): How many times a model could answer again
  after failing the checks.
- `effort` (one of `low`, `medium`, `high`; required): How hard the models
  thought before answering.
- `max_output_tokens` (integer; required): The most tokens one model answer
  could contain, thinking included.

## `items[].entries[]`

One item of a list.

- `id` (string; required): The entry's ID: its list's ID and its position in the
  list from 1, such as `p0003-007.2`.
- `level` (integer; required): How deeply the entry is nested: 0 for the top
  level.
- `marker` (string or null; required): The entry's bullet or number as printed,
  or `None`.
- `text` (string; required): The entry's text as printed.

## `items[].field`

A form field: a place on a form for a value, a mark or a signature.

- `checked` (boolean or null; required): Whether a checkbox or radio button is
  marked; null for other fields.
- `field_type` (one of `text`, `checkbox`, `radio`, `choice`, `signature`;
  required): The field's type.
- `fillable_name` (string or null; required): The name of the PDF's fillable
  form field this is, as listed with the page; null on a form that is only
  printed or scanned.
- `options` (list of strings; required): The choices of a choice field, as
  printed; empty for other fields.
- `prompt` (string or null; required): The field's printed label or question,
  such as `Name`; null when it has none.
- `value` (string or null; required): The value filled in or written on the
  field, as it appears; null when it is empty.

## `items[].figure`

A picture, chart, diagram, photo or other image.

- `crop` (string; required): The figure's image, cut from the page: its path
  relative to the output folder, such as `figures/p0003-004.png`.
- `description` (string; required): What the figure shows.
- `text` (string or null; required): Any text inside the figure, as printed, or
  `None`.

## `items[].table`

A table: rows of cells, with spans as in HTML.

- `header_rows` (integer; required): How many rows at the top are header rows.
- `rows` (list of list of objects ([`items[].table.rows[][]`](#itemstablerows));
  required): The rows from top to bottom, each with its cells in reading order.

## `verification.verdict`

The verifier's verdict on one page's extraction.

- `corrected` (object
  ([`verification.verdict.corrected`](#verificationverdictcorrected)) or null;
  required): The whole page extracted again with the problems fixed; null when
  the extraction passed or cannot be corrected.
- `passed` (boolean; required): Whether the extraction is faithful to the page,
  with nothing to fix.
- `problems` (list of objects
  ([`verification.verdict.problems[]`](#verificationverdictproblems));
  required): The problems found; empty when the extraction passed.

## `inputs.context.form_fields[]`

One interactive form field.

- `bbox` (list of 4 numbers; required): The field's box on the displayed page.
- `checked` (boolean or null; required): Whether a checkbox or radio button is
  on; `None` for other fields.
- `name` (string; required): The field's fully qualified name.
- `options` (list of strings; required): The choices of a combobox or listbox;
  empty for other fields.
- `page_index` (integer; required): The page the field is on.
- `type` (one of `text`, `checkbox`, `radio`, `combobox`, `listbox`,
  `signature`, `button`; required): The field's type.
- `value` (string or null; required): The field's current value, if it has one.

## `inputs.context.labels[]`

A name for one kind of content in this PDF, with its role and allowed kinds.

- `description` (string; required): What content gets this label.
- `kinds` (list of one of `code`, `field`, `figure`, `formula`, `list`, `table`,
  `text`; required): The kinds of item this label may be given to; at least one.
- `name` (string; required): The label's name, unique in the PDF regardless of
  case.
- `role` (one of `artifact`, `aside`, `body`, `caption`, `footnote`, `heading`,
  `navigation`; required): The role content with this label plays.

## `inputs.context.repeated_lines[]`

A repeated line that appears on the page, with what the survey decided it is.

- `id` (string; required): The line's ID in `pdf_facts.json`, such as `R1`.
- `normalized` (string; required): The form the line is compared in: Unicode
  NFKC, case-folded, whitespace collapsed, each run of digits written as `#`.
- `text` (string; required): The line as printed where it first appears in the
  PDF.
- `use` (one of `artifact`, `content`, `unclassified`; required): Whether the
  survey decided the line is page furniture (`artifact`), content (`content`),
  or neither (`unclassified`).

## `items[].table.rows[][]`

One cell of a table. A cell covered by another cell's span is left out.

- `col_span` (integer; required): How many columns the cell spans: 1 for one
  column.
- `row_span` (integer; required): How many rows the cell spans: 1 for one row.
- `text` (string or null; required): The cell's text as printed; null when the
  cell is empty.

## `verification.verdict.corrected`

The model's reading of one page: its items in reading order.

- `column_order` (one of `left_to_right`, `right_to_left` or null; required): On
  a page written top to bottom, the order its columns are read in; null on other
  pages.
- `containers` (list of objects
  ([`verification.verdict.corrected.containers[]`](#verificationverdictcorrectedcontainers));
  required): The bordered or shaded boxes on the page; empty when there are
  none.
- `items` (list of objects
  ([`verification.verdict.corrected.items[]`](#verificationverdictcorrecteditems));
  required): Every item on the page, in reading order.

## `verification.verdict.problems[]`

A problem the verifier found in the extraction.

- `category` (one of `missing`, `extra`, `merged`, `split`, `kind_or_role`,
  `label`, `reading_order`, `box`, `text`, `table`, `field`, `container`,
  `caption`, `other`; required): What kind of problem it is.
- `description` (string; required): What is wrong and where, so that a person
  can find it.
- `item_ref` (string or null; required): The ref of the item or container the
  problem is about; null when it is about no single one, such as a missing item.

## `verification.verdict.corrected.containers[]`

A bordered or shaded box on the page that holds items.

- `box` (list of integers; required): The box's `[x0, y0, x1, y1]` on the 0-1000
  grid of the page image.
- `container` (string or null; required): The ref of the container this box sits
  inside, or null.
- `label` (string; required): A label from the profile for the box.
- `ref` (string; required): A short name of your own for the box, unique on the
  page, such as `c1`.

## `verification.verdict.corrected.items[]`

One item on the page, such as a paragraph, a heading, a list or a table.

- `box` (list of integers; required): The item's `[x0, y0, x1, y1]` on the
  0-1000 grid of the page image.
- `caption_of` (string or null; required): For a caption, the ref of the item it
  captions; null for every other item.
- `container` (string or null; required): The ref of the container the item sits
  inside, or null.
- `entries` (list of objects
  ([`verification.verdict.corrected.items[].entries[]`](#verificationverdictcorrecteditemsentries))
  or null; required): A list's entries in reading order; null for other kinds.
- `field` (object ([`items[].field`](#itemsfield)) or null; required): A field's
  content; null for other kinds.
- `figure` (object
  ([`verification.verdict.corrected.items[].figure`](#verificationverdictcorrecteditemsfigure))
  or null; required): A figure's content; null for other kinds.
- `kind` (one of `code`, `field`, `figure`, `formula`, `list`, `table`, `text`;
  required): What kind of content the item holds.
- `label` (string; required): A label from the profile whose role and kinds
  match the item.
- `language` (string or null; required): The BCP-47 tag of the language of the
  item's text, such as `en` or `ar`; null when the item has no text.
- `latex` (string or null; required): A formula in LaTeX; null for other kinds.
- `ref` (string; required): A short name of your own for the item, unique on the
  page, such as `t1`.
- `role` (one of `artifact`, `aside`, `body`, `caption`, `footnote`, `heading`,
  `navigation`; required): The role the item plays on the page.
- `table` (object ([`items[].table`](#itemstable)) or null; required): A table's
  content; null for other kinds.
- `text` (string or null; required): The text of a text, code or formula item,
  as printed; null for other kinds.

## `verification.verdict.corrected.items[].entries[]`

One item of a list.

- `level` (integer; required): How deeply the entry is nested: 0 for the top
  level.
- `marker` (string or null; required): The entry's bullet or number as printed,
  such as `3.` or `b)`; null when there is none.
- `text` (string; required): The entry's text as printed.

## `verification.verdict.corrected.items[].figure`

A picture, chart, diagram, photo or other image on the page.

- `description` (string; required): What the figure shows, in the language of
  the page's text.
- `text` (string or null; required): Any text inside the figure, as printed;
  null when there is none.

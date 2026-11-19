---
title: pdf_survey.json
description: Every field of pdf_survey.json.
sidebar:
  order: 5
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

The contents of `pdf_survey.json`: the checked survey of one PDF.

## `pdf_survey.json`

The contents of `pdf_survey.json`: the checked survey of one PDF.

- `checks` (list of objects ([`checks[]`](#checks)); required): The result of
  each check, C1 to C7 in order.
- `facts` (object ([`facts`](#facts)); required): A copy of the measured facts
  the survey used.
- `fingerprint` (string; required): `sha256:` fingerprint of what the survey
  depends on; a matching file is reused.
- `inputs` (object ([`inputs`](#inputs)); required): What the survey was made
  from.
- `issues` (list of objects ([`issues[]`](#issues)); required): One review issue
  per failure on the accepted answer.
- `profile` (object ([`profile`](#profile)); required): How the PDF's pages are
  laid out, for later steps.
- `proposal` (object ([`proposal`](#proposal)); required): The rest of the
  model's answer.
- `schema_version` (string; required): The version of this file's schema,
  `"MAJOR.MINOR"`.

## `checks[]`

The result of one check on the accepted answer.

- `attempts` (integer; required): How many model answers were checked: 1 plus
  the retries used.
- `failures` (list of objects ([`checks[].failures[]`](#checksfailures));
  required): The problems the check found in the accepted answer.
- `name` (one of `labels`, `regions`, `rotation`, `page_numbering`, `artifacts`,
  `writing_direction`, `languages`; required): The check.
- `passed` (boolean; required): Whether the accepted answer passed: `failures`
  is empty.

## `facts`

Everything the probe measured.

- `bookmarks` (list of objects ([`facts.bookmarks[]`](#factsbookmarks)) or null;
  required): The bookmarks (outline).
- `form` (object ([`facts.form`](#factsform)) or null; required): Which kinds of
  form the PDF holds.
- `form_fields` (list of objects ([`facts.form_fields[]`](#factsform_fields)) or
  null; required): The interactive form fields.
- `page_numbering` (list of objects
  ([`facts.page_numbering[]`](#factspage_numbering)); required): Ranges of pages
  whose printed numbers follow their indexes.
- `pages` (list of objects ([`facts.pages[]`](#factspages)); required): What was
  measured on each page.
- `probe_errors` (list of objects
  ([`facts.probe_errors[]`](#factsprobe_errors)); required): The facts that
  could not be read.
- `repeated_lines` (list of objects
  ([`facts.repeated_lines[]`](#factsrepeated_lines)); required): Lines that
  repeat across pages, most frequent first.
- `repeated_lines_truncated` (boolean; required): Whether more repeated lines
  were found than are kept.
- `structure` (object ([`facts.structure`](#factsstructure)) or null; required):
  What the structure tags cover.

## `inputs`

What a survey was made from.

- `facts_fingerprint` (string; required): The fingerprint of the
  `pdf_facts.json` the survey used.
- `instructions` (string or null; required): The user's survey instructions
  (`advanced.survey.instructions`), if any.
- `languages` (list of strings; required): The user's languages, in standard
  form.
- `model` (string; required): The model, as `<provider>:<model-id>`.
- `page_count` (integer; required): The PDF's number of pages.
- `pdf_bytes` (integer; required): The PDF's size in bytes.
- `pdf_name` (string; required): The PDF's file name.
- `pdf_sha256` (string; required): The PDF's SHA-256 hex digest.
- `prompt_version` (integer; required): The version of the survey prompt.
- `settings` (object ([`inputs.settings`](#inputssettings)); required): The
  survey settings used.

## `issues[]`

A problem a person should review.

- `check` (one of `labels`, `regions`, `rotation`, `page_numbering`,
  `artifacts`, `writing_direction`, `languages` or one of `rotation_differs`,
  `page_number_differs`; required): The check or comparison that found the
  problem.
- `details` (map of string to any value; required): The values the problem is
  about, such as `{"measured": 90, "profile": 0}`.
- `item_id` (string or null; required): The item the problem is about, or `None`
  when no single item applies.
- `message` (string; required): What is wrong.
- `page_index` (integer or null; required): The page the problem is on, or
  `None` when no single page applies.
- `step` (one of `survey`, `extraction`; required): The step whose check found
  the problem.

## `profile`

What later steps depend on: how the PDF's pages are laid out.

- `continuation_notes` (list of strings; required): How content continues from
  one page to the next.
- `labels` (list of objects ([`profile.labels[]`](#profilelabels)); required):
  The labels for this PDF's content; always includes `other`.
- `languages` (list of strings; required): BCP-47 tags in standard form: the
  user's languages, then the model's.
- `page_numbering` (list of objects
  ([`profile.page_numbering[]`](#profilepage_numbering)); required): How printed
  page numbers relate to page indexes, by range of pages.
- `rotation` (list of objects ([`profile.rotation[]`](#profilerotation));
  required): The rotation that makes each range of pages upright; other pages
  need none.
- `start_markers` (list of objects
  ([`profile.start_markers[]`](#profilestart_markers)); required): Text that
  marks where a new unit of content starts.
- `writing_direction` (object
  ([`profile.writing_direction`](#profilewriting_direction)); required): The
  writing direction of the pages.

## `proposal`

The model's answer that is not part of the profile.

- `artifacts` (list of objects ([`proposal.artifacts[]`](#proposalartifacts));
  required): Page furniture, with the repeated lines it accounts for.
- `non_artifact_lines` (list of objects
  ([`proposal.non_artifact_lines[]`](#proposalnon_artifact_lines)); required):
  Repeated lines that are content rather than page furniture.
- `notes` (list of strings; required): Anything else the model noticed about the
  layout.
- `regions` (list of objects ([`proposal.regions[]`](#proposalregions));
  required): Areas of single pages the model labeled.

## `checks[].failures[]`

One problem a check found in a model's answer.

- `details` (map of string to any value; required): The proposed value and,
  where it applies, what it was checked against, such as
  `{"proposed": 9, "page_count": 6}`.
- `message` (string; required): What is wrong, starting with the check's name.
- `page_index` (integer or null; required): The page the problem is on, or
  `None` when no single page applies.

## `facts.bookmarks[]`

One entry of the PDF's bookmarks (outline).

- `level` (integer; required): Nesting level, 1 for top-level bookmarks.
- `page_index` (integer or null; required): The page the bookmark points to, or
  `None` when it points nowhere.
- `title` (string; required): The bookmark's title.

## `facts.form`

Which kinds of form the PDF holds.

- `has_acroform` (boolean; required): Whether the PDF has an AcroForm
  (interactive form) dictionary.
- `has_xfa` (boolean; required): Whether the form also carries an XFA form.

## `facts.form_fields[]`

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

## `facts.page_numbering[]`

Consecutive measured pages whose printed numbers follow their page indexes.

- `first_page_index` (integer; required): The first page of the range.
- `last_page_index` (integer; required): The last page of the range, inclusive.
- `offset` (integer; required): The printed number minus the page index, the
  same on every page measured.
- `pages_measured` (integer; required): How many pages in the range have a
  printed number.
- `style` (one of `arabic`, `roman`; required): How the numbers are written.

## `facts.pages[]`

What the probe measured on one page.

- `direction` (object ([`facts.pages[].direction`](#factspagesdirection));
  required): The writing direction.
- `height_pt` (number; required): The displayed page's height in points.
- `index` (integer; required): The page's index.
- `orientation` (object ([`facts.pages[].orientation`](#factspagesorientation));
  required): Which way the text runs.
- `printed_number` (object
  ([`facts.pages[].printed_number`](#factspagesprinted_number)) or null;
  required): The page number printed on the page, if one was found.
- `rotation_attribute` (integer; required): The page's rotation attribute in
  degrees, clockwise.
- `text` (object ([`facts.pages[].text`](#factspagestext)); required): The text
  layer.
- `width_pt` (number; required): The displayed page's width in points.

## `facts.probe_errors[]`

A fact the probe could not read, because reading it failed.

- `fact` (one of `bookmarks`, `form`, `structure`; required): Which fact could
  not be read.
- `message` (string; required): What went wrong.

## `facts.repeated_lines[]`

A line that repeats across pages, such as a running header or footer.

- `band` (one of `top`, `bottom`, `middle`; required): Where the line usually
  sits on its pages.
- `id` (string; required): The line's identifier, `R1`, `R2` and so on, most
  frequent first.
- `normalized` (string; required): The form lines are compared in: Unicode NFKC,
  case-folded, whitespace collapsed, each run of digits written as `#`.
- `pages` (list of integers; required): The pages the line appears on.
- `text` (string; required): The line as printed where it first appears.

## `facts.structure`

What the PDF's structure tags (the tagged-PDF tree) cover.

- `element_count` (integer; required): How many structure elements the tree has
  (up to the probe's cap).
- `marked` (boolean; required): Whether the PDF declares itself a tagged PDF.
- `pages_with_tagged_content` (integer; required): How many pages have content
  linked to the tree.
- `quality` (one of `none`, `poor`, `partial`, `good`; required): `none` without
  a tree; `poor` with only grouping elements or very few; `partial` when tagged
  content covers too few of the pages with text; `good` otherwise.
- `tagged` (boolean; required): Whether the PDF has a structure tree.
- `truncated` (boolean; required): Whether the probe stopped counting at its
  element cap.
- `type_counts` (map of string to integer; required): Elements by standard type,
  after the tree's role map is applied.

## `inputs.settings`

The survey settings a survey's result depends on.

- `check_retries` (integer; required): How many times the model could answer
  again after failing the checks.
- `effort` (one of `low`, `medium`, `high`; required): How hard the model
  thought before answering.
- `max_output_tokens` (integer; required): The most tokens one model answer
  could contain, thinking included.

## `profile.labels[]`

A name for one kind of content in this PDF, with its role and allowed kinds.

- `description` (string; required): What content gets this label.
- `kinds` (list of one of `code`, `field`, `figure`, `formula`, `list`, `table`,
  `text`; required): The kinds of item this label may be given to; at least one.
- `name` (string; required): The label's name, unique in the PDF regardless of
  case.
- `role` (one of `artifact`, `aside`, `body`, `caption`, `footnote`, `heading`,
  `navigation`; required): The role content with this label plays.

## `profile.page_numbering[]`

Consecutive pages whose printed numbers follow one style and offset.

- `first_page_index` (integer; required): The first page of the range (0-based).
- `last_page_index` (integer; required): The last page of the range, inclusive.
- `offset` (integer or null; required): The printed number minus the page index,
  or `None` when the pages print no numbers that follow the page index.
- `style` (one of `arabic`, `roman`, `other`, `none`; required): How the numbers
  are written.

## `profile.rotation[]`

Consecutive pages whose content needs the same rotation to be upright.

- `degrees` (one of `0`, `90`, `180`, `270`; required): The clockwise rotation
  that makes the displayed page's content upright.
- `first_page_index` (integer; required): The first page of the range (0-based).
- `last_page_index` (integer; required): The last page of the range, inclusive.

## `profile.start_markers[]`

Text that marks where a new unit of content starts.

- `description` (string; required): What starts where the text appears.
- `text` (string; required): The text, as printed.

## `profile.writing_direction`

The writing direction of the PDF's pages.

- `default` (one of `ltr`, `rtl`, `ttb`; required): The direction of every page
  no range covers.
- `ranges` (list of objects
  ([`profile.writing_direction.ranges[]`](#profilewriting_directionranges));
  required): Ranges of pages whose direction differs from `default`.

## `proposal.artifacts[]`

Page furniture the model identified, such as a running header or a stamp.

- `description` (string; required): What the artifact is, in a few words.
- `id` (string; required): The artifact's identifier, such as `A1`.
- `position` (one of `top`, `bottom`, `left`, `right`, `middle`; required):
  Where the artifact sits on the displayed page.
- `repeated_line_ids` (list of strings; required): The IDs of the measured
  repeated lines (`R1`, `R2` and so on) that are this artifact; empty when no
  repeated line is.

## `proposal.non_artifact_lines[]`

A measured repeated line that is not page furniture.

- `reason` (string; required): Why the line is content rather than page
  furniture.
- `repeated_line_id` (string; required): The repeated line's ID, such as `R3`.

## `proposal.regions[]`

An area of one page the model labeled, with its box in points.

- `bbox` (list of 4 numbers; required): The area on the displayed page, as
  `[x0, y0, x1, y1]` in points.
- `label` (string; required): The label of the area's content.
- `note` (string; required): Why the area is worth marking; may be empty.
- `page_index` (integer; required): The page (0-based).

## `facts.pages[].direction`

The writing direction measured on a page.

- `inline` (one of `ltr`, `rtl`, `mixed`, `none`; required): `rtl` or `ltr` when
  right-to-left or left-to-right letters reach the dominant share of the page's
  letters, `mixed` when neither does, `none` without letters.
- `vertical_share` (number; required): The share of the page's characters on
  lines in vertical writing mode.

## `facts.pages[].orientation`

Which way the text runs on the displayed page.

- `chars_by_angle` (map of string to integer; required): Characters on
  horizontal-mode lines, by baseline angle (`"0"`, `"90"`, `"180"`, `"270"`,
  counterclockwise on the displayed page).
- `confident` (boolean; required): Whether there are enough characters and the
  dominant angle has a large enough share for the measurement to be relied on.
- `dominant` (one of `0`, `90`, `180`, `270` or null; required): The angle most
  characters run at, or `None` without horizontal text.

## `facts.pages[].printed_number`

The page number printed on a page, or its page label.

- `source` (one of `page_label`, `text`; required): `page_label` from the PDF's
  page labels, or `text` from a line near the top or bottom of the page.
- `style` (one of `arabic`, `roman`, `label`; required): `arabic` or `roman`
  numerals, or `label` for any other page label.
- `text` (string; required): The number or label as printed.
- `value` (integer or null; required): The number's value, or `None` for a label
  that is not a number.

## `facts.pages[].text`

How much text a page's text layer holds, and whether it is readable.

- `chars` (integer; required): Characters other than whitespace.
- `control_chars` (integer; required): Control characters among them.
- `private_use_chars` (integer; required): Private-use characters among them.
- `quality` (one of `none`, `good`, `garbled`; required): `none` without
  characters; `garbled` when control, private-use, unassigned and replacement
  characters reach the garbled share; `good` otherwise.
- `replacement_chars` (integer; required): Replacement characters (U+FFFD) among
  them, for glyphs with no known character.
- `unassigned_chars` (integer; required): Characters Unicode does not assign,
  among them.

## `profile.writing_direction.ranges[]`

Consecutive pages written in one direction.

- `direction` (one of `ltr`, `rtl`, `ttb`; required): The writing direction on
  these pages.
- `first_page_index` (integer; required): The first page of the range (0-based).
- `last_page_index` (integer; required): The last page of the range, inclusive.

---
title: pdf_facts.json
description: Every field of pdf_facts.json, and the probe's thresholds.
sidebar:
  order: 4
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

The contents of `pdf_facts.json`: the measured facts and their summary.

## `pdf_facts.json`

The contents of `pdf_facts.json`: the measured facts and their summary.

- `facts` (object ([`facts`](#facts)); required): The measured facts.
- `fingerprint` (string; required): `sha256:` fingerprint of what the facts
  depend on; a matching file is reused.
- `measured_at` (date and time (ISO 8601); required): When the PDF was measured
  (UTC).
- `pdf` (object ([`pdf`](#pdf)); required): Which PDF was measured.
- `probe_version` (integer; required): The version of the measurement rules.
- `pydelity_version` (string; required): The pydelity version that measured the
  PDF.
- `schema_version` (string; required): The version of this file's schema,
  `"MAJOR.MINOR"`.
- `summary` (list of strings; required): The facts as plain-text lines, for
  people and for the model.

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

## `pdf`

Which PDF the facts describe.

- `bytes` (integer; required): The file's size in bytes.
- `name` (string; required): The file name.
- `page_count` (integer; required): The number of pages.
- `sha256` (string; required): The SHA-256 hex digest of the file.

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

## Measurement constants

- `BAND_SHARE` = `0.1`: A page's top band, and its bottom band, as a share of
  the displayed page's height. Printed page numbers are looked for there, and
  repeated lines are placed by it.
- `DIRECTION_DOMINANT_SHARE` = `0.7`: A page's inline direction is right-to-left
  (or left-to-right) when right-to-left (or left-to-right) letters reach this
  share of its letters.
- `GARBLED_SHARE` = `0.1`: A page's text is garbled when control, private-use,
  unassigned and replacement characters together reach this share of its
  characters.
- `ORIENTATION_DOMINANT_SHARE` = `0.8`: The measured orientation is confident
  when the most common angle has at least this share of the characters on
  horizontal lines, and the page has at least `ORIENTATION_MIN_CHARS` of them.
- `ORIENTATION_MIN_CHARS` = `20`: The fewest characters on horizontal lines that
  a confident orientation needs.
- `PROBE_VERSION` = `1`: Increase this whenever a measurement rule, a
  measurement constant or the summary format changes, so an upgraded pydelity
  measures again instead of reusing old facts.
- `REPEATED_MAX_LINES` = `1000`: At most this many repeated lines are kept, most
  frequent first.
- `REPEATED_MIN_PAGES` = `3`: A line is repeated when it appears on at least
  this many pages and on at least `REPEATED_MIN_SHARE` of the pages.
- `REPEATED_MIN_SHARE` = `0.05`: The share of the pages a repeated line must
  appear on.
- `REPEATED_SMALL_PDF_MIN_PAGES` = `2`: In a PDF of 2 or 3 pages, a line on this
  many pages is repeated.
- `STRUCTURE_ELEMENT_CAP` = `20000`: The structure tree is counted up to this
  many elements; beyond it, `truncated` is set.
- `STRUCTURE_GOOD_PAGE_SHARE` = `0.9`: Tagged content must cover at least this
  share of the pages with text for the structure tags to be good rather than
  partial.
- `STRUCTURE_GROUPING_TYPES` =
  `['Art', 'Div', 'Document', 'NonStruct', 'Part', 'Sect', 'Span']`: Element
  types that only group other elements. Structure tags made of these alone, or
  of fewer than `STRUCTURE_MIN_ELEMENTS` elements, are poor.
- `STRUCTURE_MIN_ELEMENTS` = `10`:

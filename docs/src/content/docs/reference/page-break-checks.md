---
title: Page-break checks
description:
  The checks every page-break verdict goes through, the hint it is compared
  with, and how the verifier's verdict is compared with the judge's.
sidebar:
  order: 13
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

Each verdict, from the judge or the verifier, goes through the checks. A check
tests the verdict against the page files of the break's two pages. While retries
remain (`advanced.page_breaks.check_retries`), a verdict that fails a check is
sent back to the model with every failure listed. The last verdict is accepted
as it is. Each check the judge's verdict still fails becomes a review issue. The
checks the verifier's verdict still fails are saved in the verdict file's
`verification` and are not review issues. The hint compares the judge's verdict
with the survey's start markers, which can be wrong, so the model's reading of
the pages decides. A hint difference never sends a verdict back and never stops
a run.

The judge's verdict is always the one kept. The verdict file's `checks` holds
each check's result on it, and its `hints` the hint's differences. With the
verifier on (`advanced.page_breaks.verify`, or `verify`), the judge's request is
sent again for the verifier, so it judges the break without seeing the judge's
verdict, and code compares the two verdicts. A hint difference becomes a review
issue unless the verifier's verdict matches the judge's. With the verifier off,
every hint difference is a review issue. When a page of a break has no content
items, no request is made. The verdict says nothing continues, and its `checks`
record 0 attempts.

Each review issue of a break has the page before the break as its `page_index`,
names both pages in its message, and names the item it is about in `item_id`
when that item is on either page.

## Checks

### `ids`

Check that every ID the verdict names exists on the page it is named for.

Ends and earlier containers are on the earlier page. Starts, later containers,
repeated items and the items carrying markers are on the later page. Each entry
belongs to the item named with it, and each marker's row and cell exist in its
item's table.

### `continues`

Check that `continues` is true when the verdict names pieces, and only then.

### `duplicates`

Check that no item, entry or container is named twice where once is allowed.

### `joins`

Check each piece against the rules of its join.

Each join ends and starts in items of the kinds it joins, sets the fields it
uses and leaves the others null. `continue_text` joins two items of one kind,
`continue_entry` joins the last or first entry of a list, and the table joins
keep `repeated_header_rows` and `cell_joins` within the later table. `new_entry`
starts in a list, and ends in a list or in a text item, for a list whose part on
the earlier page was extracted as text. `repeat` joins only the cells of a
merged row, and `newline` only code.

### `furniture`

Check that no piece ends or starts in page furniture.

### `header_rows`

Check that repeated header rows repeat rows of the earlier table.

For each table piece with `repeated_header_rows` n above 0, the later table's
first n rows must match, in order, n different rows among the earlier table's
first n + h rows, where h is the earlier table's `header_rows`. Rows match by
their cell texts joined in order, and two empty rows match.

### `repeats`

Check that repeated items and `repeat` cells repeat text on the earlier page.

A repeated item with text matches when its text matches an item's text, a list
entry's text, or a table row's cell texts joined in order, or when either
contains the other in comparison form. A cell of a merged row whose cell join is
`repeat` must have text, and that text must match the text of a cell in the
split row on the earlier page, the earlier table's last row, in the same way.
Any cell of that row counts, so cells that span differently on the two pages
still match.

### `markers`

Check that each continuation marker is in the text that carries it.

## Hints

### `start_markers`

Compare where pieces start with the survey's start markers.

A piece starts with the start entry's text, a list's first entry, the cell texts
of a table's first row after the repeated header rows, or the start item's text.
A start marker whose comparison form is empty is skipped. Two kinds of piece are
skipped too: an `append_rows` piece, whose new rows can begin with a start
marker while the table carries on, and a piece whose verdict names a
continuation marker in its start, on its start item and, for a table, on the row
its start text comes from.

## How text is compared

Text is compared as overlapping runs of three characters, after Unicode NFKC
normalization and case folding, keeping only letters, marks and digits. Spaces,
punctuation and line breaks drop out, so scripts written without spaces between
words compare the same way as others, and no word list or tokenizer is needed.

Two texts match when their comparison forms are equal, or when both have at
least 3 characters and a Dice coefficient of at least 0.8 over those runs of
three characters.

## Comparing the two verdicts

Compare the kept verdict for a break with the verifier's.

When only one verdict says content continues, that is the one difference, and
when neither does, nothing else is compared. Otherwise the pieces are paired by
their end, then by their start. Each piece left unpaired is a difference, the
kept verdict's first, and each pair is compared field by field in the kept
verdict's order. Repeated items, markers, containers and the reason are not
compared.

### `verdicts_differ`

Each way the verifier's verdict differs from the judge's is a review issue. Its
`details` hold the `field` that differs, one of `cell_joins`, `continues`,
`end`, `join`, `piece`, `repeated_header_rows`, `start`, `text_join`, each
verdict's value as `kept` and `verifier`, the `item` and `entry` where the piece
ends on the page before the break, null when no piece applies, and the `cell` of
one cell's join. The verdict file's `verification` keeps each difference.

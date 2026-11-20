---
title: Page extraction checks
description:
  The checks every page answer goes through, and the other review issues page
  extraction records.
sidebar:
  order: 11
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

Each page answer, from the extraction model or in a verifier's correction, goes
through these checks. While retries remain
(`advanced.extraction.check_retries`), an answer that fails a check is sent back
to the model with every failure listed. The last answer is kept as it is. A
verifier correction replaces the extraction when it passes every check other
than `text_dropped` and `text_added`. The page file's `checks` holds each
check's result on the kept answer. Each check it still fails becomes a review
issue, except `text_dropped` and `text_added` on a page the verifier passes or
whose correction is kept.

## Checks

### `labels`

Check that each label is in the profile and fits its item's role and kind.

The label `other` fits any item that no other label in the profile fits; those
items are listed for review as `no_matching_label` instead.

### `content`

Check that refs are unique and each item holds the content its kind needs.

### `languages`

Check that each language tag is valid and every item with text has one.

### `boxes`

Check that every box is well formed and on the page, and no two items share one.

### `containers`

Check that containers exist, do not nest in a loop, and hold what names them.

### `captions`

Check that each caption names the item it captions, and only captions do.

### `reading_order`

Check that the reading order follows the page's writing direction.

Over consecutive items of the page's flow (headings, body text and navigation),
a jump back against the direction is allowed only with a move to a new column,
or to a new band on a page written top to bottom.

### `artifacts`

Keep the page furniture the survey found inside items with role artifact.

Each line the survey classed as page furniture is found on the page in the
stored text, which gives its box. The line passes when the center of each of its
boxes lies inside the box of an item with role `artifact`, within 20 grid units.
Its text is never compared with the answer's, since the stored text can differ
from what is printed. A furniture line the page's stored text does not hold is
skipped.

### `form_fields`

Check that the page's fillable fields are field items with the same values.

A field the PDF has more than once on the page, such as a group of radio
buttons, needs as many field items naming it, with the same checked states or
values. Values are compared with whitespace collapsed.

### `text_dropped`

Find lines the page's text layer has that the answer does not.

It runs only when the page file's `text_comparison` is `compared`. A line also
counts as found when its reversed text is in the answer.

### `text_added`

Find lines the answer has that the page's text layer does not.

It runs only when the page file's `text_comparison` is `compared`.

## How text is compared

Text is compared as overlapping runs of three characters, after Unicode NFKC
normalization and case folding, keeping only letters, marks and digits. Spaces,
punctuation and line breaks drop out, so scripts written without spaces between
words compare the same way as others, and no word list or tokenizer is needed.

## Other review issues

These are recorded without sending the answer back.

### `no_matching_label`

Record content that no label in the profile fits, once per role and kind.

An item with the label `other` passes the `labels` check when no other label
fits its role and kind. Sending the answer back cannot fix the profile, so such
content goes on the review list instead.

### `verifier`

A problem the verifier model found on a page whose extraction it did not
replace, because it gave no correction or its correction failed a check. The
issue names the item or container the problem is about, when there is one.

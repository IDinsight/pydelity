---
title: Survey checks
description:
  The checks every survey answer goes through, its comparisons with the facts,
  and the survey verifier's review issues.
sidebar:
  order: 10
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

Each survey answer goes through checks C1 to C7 and is compared with the hints.
While retries remain (`advanced.survey.check_retries`), an answer that fails a
check is sent back to the model with every failure listed, and the last answer
is kept as it is. When the survey's verifier is on (`advanced.survey.verify`, or
`verify`), it reviews the accepted answer and may give a corrected one, which
goes through the same checks and is sent back to the verifier while retries
remain. The correction replaces the answer only when it passes every check. Each
check still failing on the kept answer becomes a review issue.

## Checks

### C1

Label names are present and unique, labels have kinds, regions use them.

Names compare regardless of case. A region may also use `other`, which pydelity
adds to every profile.

### C2

Each region is on a page of the PDF, with a box inside the page.

### C3

Rotation ranges lie inside the PDF and do not overlap.

### C4

Page-numbering ranges lie inside the PDF and do not overlap.

### C5

Every repeated line is accounted for exactly once.

Each repeated line ID appears once, in an artifact or in `non_artifact_lines`,
and no other ID appears.

### C6

Writing-direction ranges lie inside the PDF and do not overlap.

### C7

The answer lists at least one language, as valid BCP-47 tags.

A tag is valid when `langcodes` finds every part of it in the IANA language
subtag registry; special tags such as `zxx` are valid.

## Hints

A hint compares the answer with what the probe measured, which can be wrong, so
the model's reading of the PDF decides. A hint difference never sends an answer
back and never stops a run. `pdf_survey.json`'s `hints` holds each hint's
differences on the kept answer. Each difference is a review issue, unless the
verifier passed the answer or its correction was kept.

### `rotation_differs`

List the pages whose confident measured rotation the profile does not give.

This is a hint. A page can differ only where the probe measured a confident text
angle. The profile's rotation for a page comes from the first rotation range
inside the PDF that covers it, and is 0 when none does.

### `page_number_differs`

List the pages whose measured printed number the profile does not give.

This is a hint. A page can differ only where the probe measured a printed number
with a value. The profile's number for a page comes from the first numbering
range inside the PDF that covers it.

## Other review issues

### `verifier`

A problem the survey's verifier found when its correction was not kept, because
it gave no correction or its correction failed a check. The issue gives the
problem's category and, when the problem is about one page, that page.

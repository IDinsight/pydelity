---
title: Survey checks
description:
  The checks every survey answer goes through, and its comparisons with the
  facts.
sidebar:
  order: 9
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

Each survey answer goes through checks C1 to C7. While retries remain
(`advanced.survey.check_retries`), an answer that fails a check is sent back to
the model with every failure listed; the last answer is kept as it is, and each
check it still fails becomes a review issue. The accepted answer is then
compared with the measured facts.

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

## Comparisons with the facts

Record where the accepted answer differs from the measured facts.

A page can differ only where the probe measured a value: a confident text angle
for rotation, or a printed number with a value for page numbering. The profile's
value for a page comes from the first range inside the PDF that covers it. The
comparison never changes the answer and never sends it back to the model.

- `page_number_differs`: List the pages whose measured printed number the
  profile does not give.
- `rotation_differs`: List the pages whose confident measured rotation the
  profile does not give.

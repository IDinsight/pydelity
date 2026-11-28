---
title: Verify page breaks
description:
  See how pydelity decides whether content continues from one page to the next,
  what it needs before it starts, and how each verdict is checked.
---

Page-break verification is the step after page extraction. For each break
between two pages that follow each other, a model looks at both pages and gives
a verdict. The verdict says whether any content carries on from the earlier page
to the later one and, if it does, how the two pages' items join. pydelity checks
the verdict in code and saves it as one verdict file per break in
`page_breaks/`. If you turn on the step's verifier, a second request to the same
model also reviews each verdict against the two pages.

Page-break verification changes no page file. It records what later steps need
to join the pages into one document.

## What you get

Each verdict file holds one break's verdict. Its `continues` field says whether
any content carries on across the break. When content does carry on, `pieces`
lists each piece that continues. A break can have more than one piece, such as
body text and a footnote that both carry on. Each piece names:

- the item where it ends on the earlier page and the item where it starts on the
  later page, by their item IDs from the page files, and the list entry's ID
  when a list entry continues
- how it joins (`join`):
  - `continue_text`: a text item carries on in a text item, or a code item in a
    code item
  - `continue_entry`: the last entry of a list carries on, in the next page's
    first list entry or in a text item
  - `new_entry`: a list carries on with a new entry
  - `append_rows`: a table carries on with more rows
  - `merge_split_row`: a table carries on, and its last row is cut by the break,
    so that row and the next page's first row are one row
- how the two pieces of text join (`text_join`), for `continue_text` and
  `continue_entry`:
  - `space`: with a space, where the script puts one between words
  - `no_space`: with no space, where the script writes none or the break falls
    inside a word that has no hyphen
  - `dehyphenate`: by removing the hyphen at the end of the earlier line
  - `newline`: with a line break, for code, which is never dehyphenated
- for `merge_split_row`, the same choice for each cell of the split row
  (`cell_joins`)
- for a table, how many rows at the top of the later page's table repeat the
  earlier table's header (`repeated_header_rows`), `0` when none do
- the items above the continued unit on the later page that repeat what the
  earlier page printed for it, such as a title printed again on each page of a
  long table (`repeated_items`)
- any words or symbols on the later page that say the unit continues, such as
  "(continued)" after a heading, with the item or table cell that carries them
  (`markers`)

`containers` lists each bordered or shaded box that continues across the break,
by its ID on both pages. A box can continue even when the content inside it
starts something new on the later page. `reason` says why, in a sentence or two.

Only text, code, lists and tables continue. Figures, form fields and formulas
never do, so a figure printed across two pages stays two images. Page furniture,
such as running headers and page numbers, is never joined to content. A footer
at the bottom of one page and a header at the top of the next don't stop content
from continuing.

The verdict spells out the join, so that later steps can join the text in any
script without knowing the language. The files are named after the break's two
page indexes, so the break between the first and second pages is
`page_breaks/0000-0001.json`. [Read the outputs](../outputs/#verdict-files)
shows the rest of the file, and the
[verdict file reference](../../reference/page-break-json/) lists every field.

## Check the page files first

By default, a run in which page extraction writes at least one new page file
stops before page-break verification, as long as every page has a page file. Its
summary ends like this:

```text
Paused after page extraction wrote new page files. Check pages/ and report.html, then run pydelity again to verify the page breaks, or pass --no-pause (pause=False in Python) to run every step at once.
```

Each verdict rests on the two page files of its break, and a page extracted
again has both of its breaks judged again. So check the extracted pages in
`report.html` before you pay for verdicts on them. Then run the same command
again. The next run reuses the survey and the page files and goes on to
page-break verification.

A new PDF therefore takes three runs: the survey, page extraction, then
page-break verification. To run every step without stopping, turn the pause off
with `--no-pause` (`-np`), `pause: false` in a config file or `pause=False` in
Python. A run that reuses every page file never pauses before page-break
verification.
[Check the survey first](../page-extraction/#check-the-survey-first) covers the
pause after the survey.

## Every page needs a page file

Page-break verification judges every break in the PDF, or none. It runs only
when every page of the PDF has a current page file. A page file is current when
page extraction would reuse it now without a model call. A page file left by
another PDF in the same folder, or one made from an older survey, other settings
or another model, is not current.

With `pages` set, page extraction covers only the pages you select. When another
page has no current page file, pydelity extracts the selected pages, sends no
page-break request and warns you:

```text
Page-break verification needs a current page file for every page, and page 2 has none. Run pydelity again without --pages (pages in the config file), or with pages that include it, to verify the page breaks.
```

The run still completes, and `run.json` records page-break verification as
`skipped`. pydelity never extracts the other pages on its own to fill the gaps.

Pages extracted by earlier runs count. If earlier runs left a current page file
for every page you leave out, a run with `pages` set judges every break in the
PDF. For example, after `--pages 1-10` and then `--pages 11-20` on a 20-page PDF
with the pause off, the second run judges all 19 breaks.

With `overwrite`, only the pages extracted in this run are current, so
`overwrite` with `pages` set never judges breaks. A PDF with one page has no
breaks, so the step makes no request and the run completes.

To try page-break verification on part of a long PDF, make a shorter copy of the
PDF that holds only those pages, and run pydelity on the copy.

## Choose the model

Page-break verification uses `anthropic:claude-opus-5-5` at effort `high` unless
you choose another model. The `model` setting (`--model`) chooses the model for
every step. To use a different model for page-break verification only, set
`advanced.page_breaks.model` in a config file:

```yaml
# The survey and page extraction use this model.
model: anthropic:claude-opus-5-5
advanced:
  page_breaks:
    # Page-break verification uses this one.
    model: openai:gpt-6.2-astra
```

The same model judges each break and, with the verifier on, reviews the verdict.
It must read images. See
[Choose a model](../models-and-providers/#choose-a-model) for model IDs and API
keys.

## Tell the model about your PDF

If something about how content runs across your PDF's pages is unusual, describe
it in your own words in `advanced.page_breaks.instructions`. pydelity adds your
text to what it sends page-break verification's model, and its verifier when it
is on, with every break:

```yaml
advanced:
  page_breaks:
    instructions: >-
      Each chapter starts on a new page. The tables in the appendix run across
      several pages and repeat their title and header on each one.
```

These instructions go to page-break verification only. The survey and page
extraction have their own (`advanced.survey.instructions` and
`advanced.extraction.instructions`), which page-break verification doesn't send.
Instructions can be set in a config file or from Python, not on the command
line:

```python
import pydelity

breaks = await pydelity.averify_breaks(
    "document.pdf",
    advanced={"page_breaks": {"instructions": "Each chapter starts on a new page."}},
)
```

Changing page-break verification's instructions judges every break again. It
doesn't redo the survey or any page.

## How a break is judged

For each break, pydelity sends one request with both pages:

- an image of each page, turned upright as page extraction turned it, so rotated
  pages and sideways tables read the right way up
- each page's items as page extraction recorded them, in reading order, with
  their IDs, kinds, roles, boxes and content, and the page's containers
- each page's writing direction and column order
- pydelity's instructions for page-break verification
- the survey's notes on how content continues across pages and its markers of
  where new units of content start, as hints that the pages override
- your `advanced.page_breaks.instructions`, if you set them

The items help the model name and find content. They can be wrong in places, so
the images decide what continues. The end of a page is where its reading order
ends, and the start of the next page is where its reading order starts. On a
right-to-left page with columns, or a page of vertical text, these are not at
the bottom and top edges of the page.

The request carries no PDF, none of the text stored in the PDF and no other
step's instructions. Page-break verification uploads nothing.

When either page of a break holds no content items, such as a blank page or one
with only page furniture, nothing can continue across the break. pydelity then
writes a verdict that nothing continues, with `judgment` set to `no_content`,
and makes no request, with or without the verifier.

## How a verdict is checked

pydelity looks at each verdict in code in two ways, with checks and with a hint.
The [page-break checks](../../reference/page-break-checks/) reference lists
both.

**Checks** test the verdict against itself and the two page files: that every
item, list entry and container it names is on the page it names, that
`continues` agrees with `pieces`, that no item ends or starts two pieces, that
each join fits its items' kinds, that no piece ends or starts in page furniture,
that the header rows a verdict counts as repeated match the earlier table's
header, that each repeated item matches text printed on the earlier page, and
that each marker's text is in the item or cell that carries it. A verdict that
fails a check goes back to the model with the failures listed, up to
`advanced.page_breaks.check_retries` times (2 by default). When retries run out,
pydelity keeps the last verdict, puts each check it still fails on the review
list and goes on with the run.

**The hint** compares the verdict with what the survey found. `start_markers`
flags a piece whose start on the later page begins with one of the survey's
markers of where new units of content start, such as a numbered heading. The
survey can be wrong, so the model's reading of the pages decides. A difference
from the hint is never sent back to the model and never fails a break or a run.
It goes on the review list, unless the verifier passed the verdict or its
correction was kept. The verdict file's `hints` keeps every difference either
way.

Page-break verification's verifier is off by default. When you turn it on, it
looks for what code can't judge, such as content that continues but is missing
from the verdict, a piece that doesn't continue, the wrong join or text join, a
wrong count of repeated header rows, and repeated items, markers or containers
that are missing or wrong. It either passes the verdict or lists the problems,
usually with a corrected verdict. The correction goes through the same checks
and retries. pydelity keeps it when it passes every check, whatever its
difference from the hint. Otherwise pydelity keeps the first verdict and puts
each problem the verifier found on the review list. The verdict file keeps the
verifier's verdict and says when no verifier ran.
[Review answers with a verifier](../verifiers/) shows how to turn it on and what
it costs.

## Breaks run at the same time

pydelity judges up to 8 breaks at the same time, each with its own requests. Set
`advanced.page_breaks.concurrent_breaks` (1 to 32) to change that. If your
provider account has low rate limits and runs fail with rate-limit errors, lower
it.

A break fails, and the run stops, only when no usable answer comes back: the
model refuses, its answer runs out of output tokens, it never gives a verdict in
the form pydelity expects, or the provider keeps returning errors. The breaks
still in progress are canceled. Verdict files already written stay saved, and
the next run judges only the rest. See
[When page-break verification fails](../models-and-providers/#when-page-break-verification-fails).

---
title: Extract pages
description:
  Choose which pages to extract, check the survey before paying for them, tell
  the models about your PDF and see how pydelity checks each page.
---

Page extraction is the step after the survey. For each page you select, a model
reads an image of the page and lists everything on it as items in reading order:
headings, paragraphs, lists, tables, formulas, code, figures and form fields,
each with its position on the page. pydelity checks the answer in code, and the
result is saved as one page file per page in `pages/`. If you turn on page
extraction's verifier, a second request to the same model also reviews each
answer against the page image.

## What you get

Each page file lists the page's items in the order a person reads them. Every
item has:

- an `id`, such as `p0003-007`: the page index and the item's place in reading
  order. Extracting the same answer again gives the same IDs.
- a `kind`: `text`, `list`, `table`, `formula`, `code`, `figure` or `field`
- a `role`: `heading`, `body`, `caption`, `footnote`, `aside`, `navigation`, or
  `artifact` for page furniture such as running headers and page numbers
- a `label`, one of the labels the survey found for this PDF
- a `bbox`: its box in points on the page as displayed, from the top-left corner
- its content: the text as printed, in its own script and untranslated; a list's
  entries; a table's rows and cells, with cells that span rows or columns; a
  formula's LaTeX; a code block's exact spacing; a field's value or whether it
  is checked; and for a figure, a description and an image of it in `figures/`

Bordered or shaded boxes on the page are recorded as containers. Items inside a
box keep their own kind and role and name the box they sit in. A caption names
the item it captions.

A page that is a single picture, such as a slide or a poster, comes back as one
figure item. That is a valid answer, not a problem to review.

[Read the outputs](../outputs/#page-files) shows where the files are, and the
[page file reference](../../reference/page-json/) lists every field.

## Check the survey first

By default, a run that makes a new survey stops before page extraction. Its
summary ends like this:

```text
Paused after the new survey. Check pdf_survey.json and report.html, then run pydelity again to extract the pages, or pass --no-pause (pause=False in Python) to run every step at once.
```

Page extraction reads the survey's results for every page: which way the text
runs, how far to turn the page, the labels to use and which repeated lines are
page furniture. If the survey got one of these wrong, every page that depends on
it can come out wrong too, and page extraction costs more than the survey. Open
`report.html`, check the survey's results and its review issues, then run the
same command again. The next run reuses the survey and goes on to page
extraction.

To run every step without stopping, turn the pause off:

```sh
pydelity document.pdf --no-pause
```

```yaml
# In a config file
pause: false
```

```python
import pydelity

result = await pydelity.arun("document.pdf", pause=False)
```

`-np` is the short form of `--no-pause`. A run that reuses a saved survey
doesn't pause after it, because there's nothing new to check. The same pause
comes after page extraction when it writes new page files, before page-break
verification. See
[Check the page files first](../page-breaks/#check-the-page-files-first). A
paused run exits with code 0.

## Choose the pages

Page extraction covers every page unless you set `pages`. Pages are numbered
from 1, as a PDF viewer shows them. List single pages and ranges, separated by
commas:

```sh
# Pages 1 to 5 and page 8.
pydelity document.pdf --pages 1-5,8
```

```yaml
# In a config file
pages: 1-5,8
```

```python
import pydelity

result = await pydelity.arun("document.pdf", pages="1-5,8")
```

`-p` is the short form of `--pages`. The survey always reads the whole PDF,
whatever you select. A `pages` value that pydelity can't read, or that names a
page the PDF doesn't have, stops the run before anything is sent, with an error
that names `pages`.

Selecting more pages later extracts only the new ones. Selecting fewer leaves
the page files of the pages you dropped in `pages/`, but `run.json` and the
report cover only the pages selected in the latest run.

Page-break verification judges the breaks only when every page of the PDF has a
current page file, from this run or an earlier one. When `pages` leaves a page
without one, the run extracts the selected pages and skips page-break
verification with a warning. See
[Every page needs a page file](../page-breaks/#every-page-needs-a-page-file).

## Choose the model

Page extraction uses `anthropic:claude-opus-5-5` at effort `high` unless you
choose another model. The `model` setting (`--model`) chooses the model for
every step. To use a different model for page extraction only, set
`advanced.extraction.model` in a config file:

```yaml
# The survey uses this model.
model: anthropic:claude-opus-5-5
advanced:
  extraction:
    # Page extraction uses this one.
    model: openai:gpt-6.2-astra
```

The same model reads each page and, with the verifier on, reviews it. It must
read images. See [Choose a model](../models-and-providers/#choose-a-model) for
model IDs and API keys.

## Tell the models about your PDF

If something about your PDF is unusual, describe it in your own words in
`advanced.extraction.instructions`. pydelity adds your text to what it sends the
page extraction model, and the verifier when it is on, with every page:

```yaml
advanced:
  extraction:
    instructions: >-
      Answers to the form's questions are handwritten in the boxes to the right
      of each question. Treat each answer as the value of the field beside it.
```

The survey has its own setting, `advanced.survey.instructions`, which goes only
to the survey's model. Instructions can be set in a config file or from Python,
not on the command line:

```python
import pydelity

result = await pydelity.arun(
    "document.pdf",
    advanced={"extraction": {"instructions": "Each page is a slide with notes."}},
)
```

Changing page extraction's instructions extracts every selected page again. It
doesn't redo the survey.

## How a page is read

For each page, pydelity:

1. Draws the page as an image and turns it upright, using the rotation the
   survey gave for that page. Sideways tables and rotated pages are read the
   right way up. The image is as large as both providers accept without
   shrinking it, and never more than 300 DPI: about 2,200 pixels on the long
   edge for a Letter or A4 page.
2. Sends that one image to the model, with the survey's labels and some hints
   about the page: the writing direction the survey found, the page's repeated
   lines with their stored text and what the survey found each one to be, and
   any fillable form fields on the page with their stored values. The hints come
   from the survey and the PDF's stored data, which can be wrong, so the model
   gives what the image shows where the two disagree. The model reads all of the
   page's text from the image. pydelity doesn't send the rest of the text stored
   in the PDF, because that text can be wrong, for example with letters out of
   order in Arabic or broken ligatures.
3. Checks the answer in code, and sends it back to the model with the failed
   checks listed, up to `advanced.extraction.check_retries` times (2 by
   default). Differences from the hints are never sent back.
4. With the verifier on, sends the image, the answer, the checks it still fails
   and its differences from the hints to the verifier, a second request to the
   same model, which reviews the page against the image.
5. Turns each box back into points on the page as displayed, cuts out each
   figure as an image and writes the page file.

The model reads the page in the direction it is written, with the survey's
writing direction as a hint. Pages with columns are read column by column: from
the left on left-to-right pages, from the right on right-to-left pages, and for
vertical text, in the order its script reads its columns.

## How a page is checked

pydelity looks at each answer in code in two ways: with checks and with hints.
The [page extraction checks](../../reference/extraction-checks/) reference lists
both.

**Checks** test the answer against itself, the survey's labels and the page:
that every label fits the survey's labels and the item's role and kind, that
each item holds the content its kind needs, that every item with text has a
valid language tag, that boxes are well formed, sit on the page and aren't
shared, and that containers and captions point at items that exist. An answer
that fails a check goes back to the model with the failures listed. When retries
run out, pydelity keeps the last answer, puts each check it still fails on the
review list and goes on with the run.

**Hints** compare the answer with what pydelity measured in the PDF or the
survey found:

- `reading_order`: whether the items follow the writing direction the survey
  found
- `artifacts`: whether each repeated line the survey found to be page furniture
  sits in an item with role `artifact`
- `form_fields`: whether each of the page's fillable form fields has a field
  item that names it, with the value the PDF stores
- `text_dropped` and `text_added`: lines of the PDF's stored text that the
  answer doesn't have, and lines of the answer that the stored text doesn't
  have. See
  [Text compared with the PDF's stored text](#text-compared-with-the-pdfs-stored-text).

Measurements and the survey can be wrong, so the model's reading of the page
image decides. A difference from a hint is never sent back to the model and
never fails a page or a run. It goes on the review list, unless a verifier
passed the page or its correction was kept. The page file's `hints` keeps every
difference either way.

A page fails, and the run stops, only when no usable answer comes back, such as
when the model refuses, runs out of output tokens or the provider keeps
returning errors. See
[When page extraction fails](../models-and-providers/#when-page-extraction-fails).

Page extraction's verifier is off by default. When you turn it on, it looks for
what code can't judge, such as a missed or merged item, a misread word, a wrong
reading order on a complex page or a box on the wrong content. It either passes
the page or lists the problems, usually with a corrected answer. The correction
goes through the same checks and retries. pydelity keeps it when it passes every
check, whatever its differences from the hints. Otherwise pydelity keeps the
first answer and puts each problem the verifier found on the review list. The
page file keeps the verifier's verdict, whether or not its correction was used,
and says when no verifier reviewed the page.
[Review answers with a verifier](../verifiers/) shows how to turn it on and what
it costs.

## Text compared with the PDF's stored text

Many PDFs store their text as well as drawing it. On pages where that stored
text reads well, pydelity compares it with the text in the answer, in any
script, to find lines the model dropped or added. Stored text can be wrong while
the page looks right, so these differences are hints and are never sent back to
the model. Each goes on the review list unless a verifier passed the page or its
correction was kept. With the verifier on, its request quotes the stored lines
each difference is about, and the page image decides whether the answer is
wrong.

Pages whose stored text is missing, garbled or mostly unlike the answer skip the
comparison, and the page file's `text_comparison` says why.

## Pages run at the same time

pydelity extracts up to 8 pages at the same time, each as its own requests. Set
`advanced.extraction.concurrent_pages` (1 to 32) to change that. If your
provider account has low rate limits and runs fail with rate-limit errors, lower
it.

If one page fails, for example because the provider keeps returning errors or
the model refuses, the run stops and the pages still in progress are canceled.
Pages already written stay saved, and the next run extracts only the rest. See
[When page extraction fails](../models-and-providers/#when-page-extraction-fails).

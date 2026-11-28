---
title: Read the outputs
description:
  What each file in the output folder holds, how to read the review list and
  what the HTML report shows.
---

Every run writes to one output folder, `pydelity-output/<PDF name>/` unless you
set `output_dir`.

| File              | What it holds                                                         | Reference                                           |
| ----------------- | --------------------------------------------------------------------- | --------------------------------------------------- |
| `report.html`     | The results as a page to open in a browser                            |                                                     |
| `report/`         | The report's page images and their list                               |                                                     |
| `run.json`        | The latest run: settings, status, cost, warnings and review list      | [run.json](../../reference/run-json/)               |
| `pdf_facts.json`  | What pydelity measured in the PDF                                     | [pdf_facts.json](../../reference/pdf-facts-json/)   |
| `pdf_survey.json` | The survey's checked answer                                           | [pdf_survey.json](../../reference/pdf-survey-json/) |
| `pages/`          | One page file per extracted page, such as `pages/0003.json`           | [Page file](../../reference/page-json/)             |
| `figures/`        | An image of each figure, such as `figures/p0003-004.png`              | [Page file](../../reference/page-json/#itemsfigure) |
| `page_breaks/`    | One verdict file per page break, such as `page_breaks/0003-0004.json` | [Verdict file](../../reference/page-break-json/)    |
| `cost.jsonl`      | One line per model request, from every run                            | [cost.jsonl](../../reference/cost-jsonl/)           |
| `uploads.json`    | The PDF's uploads to providers                                        | [uploads.json](../../reference/uploads-json/)       |

Pages in the JSON files are numbered by `page_index`, which starts at 0, so the
PDF's first page is page 0 and its page file is `pages/0000.json`. The `pages`
setting, the command's summary and the report number pages from 1, as a PDF
viewer does. Each page file holds both.

Each JSON file has a `schema_version`. In Python, `pydelity.load(folder)` reads
the folder back as objects. See [Use pydelity from Python](../python/).

## The report

Open `report.html` in any browser. It shows:

- how the run went, what it cost and its warnings
- the review list, by step, with links to each issue's page and item
- the survey's results: page numbering, rotation, writing direction, languages,
  labels and page furniture, and what the survey's verifier found, or that no
  verifier ran
- the measured facts
- each page as an image
- each page break's verdict, beside its two pages

On a page that hasn't been extracted, the image shows the survey's regions and
any form fields. On an extracted page, it shows every item as a box numbered in
reading order, and every container as a dotted box. A box marked `!` has review
issues. Beside the image is the list of items, with each item's ID, kind, role,
label and content, a table drawn with its spans, a field's value, and a figure's
description and image. Select a box to go to its item, and select an item's ID
in the review list to go to its box. The page's details also say what the
verifier found, or that no verifier ran, and whether its text was compared with
the PDF's stored text.

Below the pages, the "Page breaks" section has one card per break, headed with
its two page numbers, such as "Pages 4 and 5". It shows both pages with boxes on
the items and containers the verdict names: where each piece ends and starts,
the repeated items, the items that carry a continuation marker and the
containers that continue. Beside them are whether content continues, each
piece's join, text join or cell joins, repeated header rows, repeated items and
markers, the continuing containers, the verdict's reason, and what the verifier
found or that no verifier ran. A break where a page has no content items says
that no request was made. Each review issue about a break links to its card.

The report is a single page with no scripts, and it loads nothing from the
internet. It shows images from the `report/` and `figures/` folders next to it,
so keep them together if you move or share the report.

## run.json

`run.json` describes the latest run on the folder:

- `status`: `completed`, `paused` (stopped after a new survey, or after page
  extraction wrote new page files, to be checked), `failed`, `stopped`,
  `interrupted`, or `running` while the run is going
- `error`: why the run failed or stopped, if it did
- `steps`: what each step did, such as `completed`, `reused` or `skipped` (a
  step after a pause, or page-break verification when a page has no current page
  file), and how many requests it made. Page extraction says how many pages were
  selected, extracted and reused, and page-break verification (`page_breaks`)
  how many breaks the PDF has and how many were judged and reused.
- `settings`: the settings the run used (never your API key)
- `cost`: what the run and the whole folder have spent. See
  [Control costs](../costs/#what-a-run-spent).
- `warnings`: problems that didn't stop the run, each with the step that was
  running
- `review`: the review list

### Warnings

Each warning has a `code`:

| Code                  | Meaning                                                                   |
| --------------------- | ------------------------------------------------------------------------- |
| `damaged_output`      | A saved file couldn't be read, so its step or page ran again              |
| `max_cost_exceeded`   | The run could go over `max_cost`                                          |
| `missing_page_files`  | Some pages have no current page file, so no page break was judged         |
| `other_pdf_in_folder` | The folder held results for another PDF, which this run replaced          |
| `probe_unavailable`   | pydelity couldn't read the PDF's bookmarks, form fields or structure tags |
| `unpriced_model`      | pydelity has no price for the model, so its costs aren't recorded         |
| `upload_fallback`     | Uploading the PDF failed, so it was sent inside each request instead      |

## The review list

The review list in `run.json` holds everything a person should check: the
survey's issues first, then each selected page's issues in page order, then each
page break's issues in break order. Each issue names the `step` (`survey`,
`extraction` or `page_breaks`) and the `check` that found it, the `page_index`
it is on (or `null`), the `item_id` it is about (or `null`), a `message` and the
values involved in `details`. For a page break, `page_index` is the page before
the break, and the message names both pages, such as `pages 4 and 5: ...`.

**Checks the survey's answer still fails.** pydelity checks every survey answer,
for example that page ranges don't overlap and that every repeated line is
accounted for. It sends a failing answer back to the model, up to
`advanced.survey.check_retries` times. Whatever the last answer still gets wrong
goes on the list. The [Survey checks](../../reference/survey-checks/) reference
lists every check.

**Places where the survey and the measurements disagree.** pydelity gives the
survey's model what it measured as hints and keeps the model's reading, because
the model sees the pages and is usually the better judge. It never sends an
answer back for differing from a hint. Where the answer differs from what
pydelity measured, the page goes on the list:

- `rotation_differs`: the text on the page runs at an angle that needs a
  different rotation from the one the model gave.
- `page_number_differs`: the page shows a page number, in its text or in the
  PDF's page labels, that the model's page numbering doesn't give.

When the survey's verifier ran and passed the answer, or its correction was
kept, these differences are left off the list, because the verifier checked the
answer against the PDF. Otherwise each one is listed.

Read these two kinds of issue. Either side can be wrong. The measurements can
take numbers in a table for page numbers, or report page labels that number a
cover page that prints no number. `details.source` says whether the number came
from the page's text (`text`) or its page label (`page_label`). The model can
also misread a page where the measurements were right, and the review list is
the only place that shows it.

**Checks a page's answer still fails.** Each page answer goes through the
[page extraction checks](../../reference/extraction-checks/), with retries.
Whatever the kept answer still gets wrong goes on the list, usually naming the
item.

**Places where a page and its hints disagree.** Page extraction compares each
answer with what pydelity measured in the PDF or the survey found, and keeps the
model's reading:

- `reading_order`: the items don't follow the writing direction the survey
  found.
- `artifacts`: a repeated line the survey found to be page furniture sits in no
  item with role `artifact`.
- `form_fields`: a fillable form field has no field item that names it, or its
  field item gives a value other than the one the PDF stores.
- `text_dropped` and `text_added`: a line of the PDF's stored text isn't in the
  answer, or a line of the answer isn't in the stored text.

These are listed on every page no verifier reviewed. On a page the verifier
reviewed, they are listed only when it didn't pass the page and its correction
wasn't used. As with the survey, either side can be wrong. See
[How a page is checked](../page-extraction/#how-a-page-is-checked).

**Checks a page-break verdict still fails.** Each verdict goes through the
[page-break checks](../../reference/page-break-checks/), with retries. Whatever
the kept verdict still gets wrong goes on the list, usually naming an item on
one of the two pages.

**Places where a verdict and the survey disagree.** `start_markers` lists a
piece whose start on the later page begins with one of the survey's markers of
where new units of content start. It is listed on every break no verifier
reviewed, and on a reviewed break only when the verifier didn't pass the verdict
and its correction wasn't kept. Either side can be wrong. See
[How a verdict is checked](../page-breaks/#how-a-verdict-is-checked).

**Problems a verifier found.** When the survey's, a page's or a break's verifier
finds problems and its correction isn't kept, each problem goes on the list as a
`verifier` issue. See
[Review answers with a verifier](../verifiers/#the-review-list-with-and-without-a-verifier).

**Content no label fits.** When the survey gave no label for an item's role and
kind, the item gets the label `other`, and the page gets one `no_matching_label`
issue for each such role and kind.

Where a page number, a rotation or an item matters for your work, check the page
in the report.

## Page files

Each page file in `pages/` holds one extracted page:

- `items`: the page's items in reading order, each with its `id`, `kind`,
  `role`, `label`, `bbox` in points on the page as displayed, and its content.
  [Extract pages](../page-extraction/#what-you-get) describes them.
- `containers`: the page's bordered or shaded boxes. Items inside one name it in
  `container`.
- `checks`: each check's result on the kept answer, failures included
- `hints`: each hint's differences from the kept answer, whether or not the
  review list shows them
- `issues`: the page's review issues, the same ones `run.json` lists
- `verification`: `null` when no verifier reviewed the page. Otherwise the
  verifier's verdict as it gave it (`passed`, the `problems` it found and any
  `corrected` answer), whether the correction was used (`correction_applied`)
  and, if it wasn't, the checks it failed
- `text_comparison`: whether the items' text was compared with the PDF's stored
  text (`compared`), and if not, why
- `writing_direction`, `rotation` and `column_order`: how the page was read
- `inputs` and `fingerprint`: what the page was made from, which decides when it
  is reused. See [Rerun and resume](../reruns/#what-gets-reused).

A figure item's `figure.crop` names its image in `figures/`, cut from the page
and turned upright.

Every page file a verifier reviewed keeps its verdict, so you can count how
often the verifier passed pages, found problems and had its correction used.

## Verdict files

Each verdict file in `page_breaks/` holds one page break's verdict. It is named
after the two page indexes, so `page_breaks/0003-0004.json` is the break between
the fourth and fifth pages.

- `earlier_page_index` and `later_page_index`: the break's two pages
- `verdict`: the kept verdict, with `continues`, the continuing `pieces`, the
  continuing `containers` and the `reason`.
  [Verify page breaks](../page-breaks/#what-you-get) describes them.
- `judgment`: `model` when a model judged the break, or `no_content` when a page
  of the break has no content items, so nothing can continue and no request was
  made
- `checks`: each check's result on the kept verdict, failures included
- `hints`: the kept verdict's differences from the survey's start markers,
  whether or not the review list shows them
- `issues`: the break's review issues, the same ones `run.json` lists
- `verification`: `null` when no verifier reviewed the verdict. Otherwise the
  verifier's verdict as it gave it (`passed`, the `problems` it found and any
  `corrected` verdict), whether the correction was kept (`correction_applied`)
  and, if it wasn't, the checks it failed
- `inputs` and `fingerprint`: what the verdict was made from, which decides when
  it is reused. See [Rerun and resume](../reruns/#what-gets-reused).

Every verdict file a verifier reviewed keeps the verifier's verdict, so you can
count how often it passed verdicts, found problems and had its correction kept.

## pdf_facts.json

pydelity measures the PDF before calling any model and saves the results here
straight away. They stay even if you stop at the cost question or the run fails
later.

- `summary`: the facts as short lines of text, the same lines the survey's model
  gets
- `facts`: each page's text layer, text angle, writing direction and printed
  page number, plus the repeated lines, bookmarks, form fields and structure
  tags
- `facts.probe_errors`: any of these that couldn't be read

## pdf_survey.json

- `profile`: how the PDF's pages are laid out: page numbering, rotation, writing
  direction, languages, the labels for its kinds of content and where new units
  of content start. Page extraction builds on this.
- `proposal`: the rest of the model's answer: the regions it labeled on single
  pages, which repeated lines are page furniture such as running headers and
  which are content, and any notes
- `checks`: whether the kept answer passed each check, and how many answers it
  took. The kept answer is the survey's own, or the verifier's correction when
  it was kept.
- `hints`: the kept answer's differences from the measured facts
  (`rotation_differs` and `page_number_differs`), whether or not the review list
  shows them
- `issues`: the survey's review issues: the checks the kept answer still fails,
  the places it differs from the measured facts unless the verifier passed it or
  its correction was kept, and the verifier's problems when its correction
  wasn't kept
- `verification`: `null` when no verifier reviewed the survey. Otherwise the
  verifier's verdict, whether its correction was kept and how many verdicts it
  took, as for a page file
- `inputs`: what the survey was made from, which decides when it is reused
- `facts`: a copy of the measured facts the survey used

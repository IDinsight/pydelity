---
title: Read the outputs
description:
  What each file in the output folder holds, how to read the review list and
  what the HTML report shows.
---

Every run writes to one output folder, `pydelity-output/<PDF name>/` unless you
set `output_dir`. Page numbers in every file are page indexes that start at 0,
so the PDF's first page is page 0.

| File              | What it holds                                                    | Reference                                           |
| ----------------- | ---------------------------------------------------------------- | --------------------------------------------------- |
| `report.html`     | The results as a page to open in a browser                       |                                                     |
| `report/`         | The report's page images and their list                          |                                                     |
| `run.json`        | The latest run: settings, status, cost, warnings and review list | [run.json](../../reference/run-json/)               |
| `pdf_facts.json`  | What pydelity measured in the PDF                                | [pdf_facts.json](../../reference/pdf-facts-json/)   |
| `pdf_survey.json` | The model's checked answer                                       | [pdf_survey.json](../../reference/pdf-survey-json/) |
| `cost.jsonl`      | One line per model request, from every run                       | [cost.jsonl](../../reference/cost-jsonl/)           |
| `uploads.json`    | The PDF's uploads to providers                                   | [uploads.json](../../reference/uploads-json/)       |

Each JSON file has a `schema_version`. In Python, `pydelity.load(folder)` reads
the folder back as objects. See [Use pydelity from Python](../python/).

## The report

Open `report.html` in any browser. It shows:

- how the run went, what it cost and its warnings
- the review list
- the survey's results: page numbering, rotation, writing direction, languages,
  labels and page furniture
- the measured facts
- each page as an image, with the model's regions and any form fields drawn on
  it

The report is a single page with no scripts, and it loads nothing from the
internet. It shows the page images from the `report/` folder next to it, so keep
the two together if you move or share the report.

## run.json

`run.json` describes the latest run on the folder:

- `status`: `completed`, `failed`, `stopped`, `interrupted`, or `running` while
  the run is going
- `error`: why the run failed or stopped, if it did
- `steps`: what each step did, such as `completed` or `reused`, and how many
  requests it made
- `settings`: the settings the run used (never your API key)
- `cost`: what the run and the whole folder have spent. See
  [Control costs](../costs/#what-a-run-spent).
- `warnings`: problems that didn't stop the run
- `review`: the review list

### Warnings

Each warning has a `code`:

| Code                  | Meaning                                                                   |
| --------------------- | ------------------------------------------------------------------------- |
| `damaged_output`      | A saved file couldn't be read, so its step ran again                      |
| `max_cost_exceeded`   | The run could go over `max_cost`                                          |
| `other_pdf_in_folder` | The folder held results for another PDF, which this run replaced          |
| `probe_unavailable`   | pydelity couldn't read the PDF's bookmarks, form fields or structure tags |
| `unpriced_model`      | pydelity has no price for the model, so its costs aren't recorded         |
| `upload_fallback`     | Uploading the PDF failed, so it was sent inside each request instead      |

## The review list

The review list in `run.json` holds everything a person should check. Each issue
names the `check` that found it, the `page_index` it is on (or `null`), a
`message` and the values involved in `details`. It comes from two places.

**Checks the answer still fails.** pydelity checks every answer, for example
that page ranges don't overlap and that every repeated line is accounted for. It
sends a failing answer back to the model, up to `advanced.survey.check_retries`
times. Whatever the last answer still gets wrong goes on the list. The
[Survey checks](../../reference/survey-checks/) reference lists every check.

**Places where the model and the measurements disagree.** pydelity keeps the
model's reading, because the model sees the pages and is usually the better
judge. Where it differs from what pydelity measured, the page goes on the list:

- `rotation_differs`: the text on the page runs at an angle that needs a
  different rotation from the one the model gave.
- `page_number_differs`: the page shows a page number, in its text or in the
  PDF's page labels, that the model's page numbering doesn't give.

Read these two kinds of issue. Either side can be wrong. The measurements can
take numbers in a table for page numbers, or report page labels that number a
cover page that prints no number. `details.source` says whether the number came
from the page's text (`text`) or its page label (`page_label`). The model can
also misread a page where the measurements were right, and the review list is
the only place that shows it.

Where a page number or rotation matters for your work, check the page in the
report.

## pdf_facts.json

pydelity measures the PDF before calling any model and saves the results here
straight away. They stay even if you stop at the cost question or the run fails
later.

- `summary`: the facts as short lines of text, the same lines the model gets
- `facts`: each page's text layer, text angle, writing direction and printed
  page number, plus the repeated lines, bookmarks, form fields and structure
  tags
- `facts.probe_errors`: any of these that couldn't be read

## pdf_survey.json

- `profile`: how the PDF's pages are laid out: page numbering, rotation, writing
  direction, languages, the labels for its kinds of content and where new units
  of content start. Later pydelity steps will build on this.
- `proposal`: the rest of the model's answer: the regions it labeled on single
  pages, which repeated lines are page furniture such as running headers and
  which are content, and any notes
- `checks`: whether the answer passed each check, and how many answers it took
- `issues`: the survey's review issues, both the checks the accepted answer
  failed and the places it differs from the measured facts
- `inputs`: what the survey was made from, which decides when it is reused
- `facts`: a copy of the measured facts the survey used

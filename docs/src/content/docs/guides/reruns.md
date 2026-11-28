---
title: Rerun and resume
description:
  What pydelity reuses when you run it again, what makes it redo the survey, a
  page or a page break, and how to pick up after a run that stopped or failed.
---

pydelity saves each result in the output folder as soon as it has it. When you
run it again on the same folder, it reuses what still fits and only redoes the
rest. So you never pay twice for the same survey, page or page break, and a run
that stopped can carry on where it left off.

## What gets reused

**The measured facts** (`pdf_facts.json`) are reused as long as the PDF's
content is unchanged. pydelity compares a SHA-256 hash of the file, so renaming
or moving the PDF doesn't matter here. A newer pydelity that measures PDFs
differently measures them again.

**The survey** (`pdf_survey.json`) is reused as long as everything it was made
from is unchanged:

- the PDF's content, by its SHA-256 hash, so renaming or moving the PDF doesn't
  matter here
- the measured facts
- the survey's model: `model`, or the default when it isn't set
- `languages` and `advanced.survey.instructions`
- `advanced.survey.effort`, `check_retries` and `max_output_tokens`
- the survey instructions built into pydelity, which a newer release may change

Changing any of these runs the survey again, at full cost. Changing anything
else, such as `max_cost`, `provider_retries`, `request_timeout_seconds`,
`expiry_hours`, `pages` or any page extraction setting, keeps the saved survey.

**Each page file** (`pages/<NNNN>.json`) is reused as long as everything that
page's extraction was made from is unchanged:

- the PDF's content
- what the survey found for that page: its writing direction and rotation, the
  survey's labels and languages, and which of the page's repeated lines are page
  furniture
- the page's measured facts and fillable form fields
- page extraction's model: `advanced.extraction.model`, else `model`, else the
  default
- `advanced.extraction.instructions`
- `advanced.extraction.effort`, `check_retries` and `max_output_tokens`
- the page extraction instructions and the page image settings built into
  pydelity, which a newer release may change

So a new survey reruns only the pages whose results it changed. Changing
`concurrent_pages`, `request_timeout_seconds` or `max_cost` reruns no page. A
page file that names a figure image no longer in `figures/` counts as damaged
and is extracted again.

**Each verdict file** (`page_breaks/<NNNN>-<NNNN>.json`) is reused as long as
everything that break's verdict was made from is unchanged:

- the PDF's content
- the page files of the break's two pages, byte for byte
- the survey's notes on how content continues across pages and its start markers
- page-break verification's model: `advanced.page_breaks.model`, else `model`,
  else the default
- `advanced.page_breaks.instructions`
- `advanced.page_breaks.effort`, `check_retries` and `max_output_tokens`
- the page-break verification instructions and the page image settings built
  into pydelity, which a newer release may change

A page extracted again is a new page file, even when its items come out the
same, so both breaks next to it are judged again, and no other break is.
Changing a page-break verification setting judges every break again but redoes
neither the survey nor any page. Changing `concurrent_breaks`,
`request_timeout_seconds` or `max_cost` judges no break again.

By default the output folder is named after the PDF, so a renamed PDF also gets
a new, empty output folder unless you set `output_dir`.

The verifier settings are not among these inputs. With a step's verifier on, a
saved survey, page file or verdict file that no verifier reviewed is made again
with the verifier. With it off, saved outputs are reused whether or not a
verifier reviewed them. Changing one step's verifier setting redoes another
step's output only when the first step's new output changes what the other was
made from. See
[Turn a verifier on or off later](../verifiers/#turn-a-verifier-on-or-off-later).

**The upload** of the PDF to the provider (`uploads.json`) is reused while at
least an hour is left before the provider deletes it. See
[How long the provider keeps your PDF](../models-and-providers/#how-long-the-provider-keeps-your-pdf).

When a run reuses a step, that step makes no model request and costs nothing.
The command's summary shows the step as `reused`, for page extraction how many
pages were extracted and reused, and for page-break verification how many breaks
were judged and reused:

```text
Run completed: survey reused, extraction reused (2 pages selected: 0 extracted, 2 reused), page_breaks reused (1 break: 0 judged, 1 reused); cost $0.00 this run, ...
```

## Change the pages you select

Selecting more pages extracts only the pages without a page file that still
fits. Selecting fewer leaves the other pages' files in `pages/`, so selecting
them again later reuses them. `run.json` and the report cover the pages selected
in the latest run. `pydelity.load` returns every page file in the folder that
was made from the folder's PDF.

Page-break verification needs a current page file for every page of the PDF,
whichever pages you select. See
[Every page needs a page file](../page-breaks/#every-page-needs-a-page-file).

## Redo everything

To measure, survey, extract and judge the page breaks again even though nothing
changed, use `overwrite`:

```sh
pydelity document.pdf --overwrite
```

```python
import pydelity

result = await pydelity.arun("document.pdf", overwrite=True)
```

A new survey, new page files and new verdicts cost as much as the first ones.
The upload is still reused.

With the pause on, an `overwrite` run redoes the survey and then pauses. Leave
`--overwrite` off on the next run, or the survey is redone again. That next run
reuses each page file whose inputs the new survey didn't change. To redo every
step, every page included, in one run, add `--no-pause`:

```sh
pydelity document.pdf --overwrite --no-pause
```

`overwrite` covers the selected pages only. To redo some pages, select just
those:

```sh
pydelity document.pdf --overwrite --no-pause --pages 4
```

This redoes the survey too, because `overwrite` redoes every step. It judges no
page break, because with `overwrite` only the pages extracted in this run have a
current page file. Run again without `--overwrite` and `--pages` to judge the
breaks.

## After a run that stopped or failed

A run can end early because you answered no, it hit `max_cost`, the provider
failed, the survey, a page or a page break had no usable answer, or you pressed
Ctrl+C. In each case `run.json` records how it ended and why, and anything
already finished stays saved, including each page file and verdict file written
before the run ended.

To continue, run the same command again. pydelity reuses the saved facts,
upload, survey, page files and verdict files, and redoes only what is missing.
Money already spent in the folder still counts toward `max_cost`.

Each run replaces `run.json` and `report.html`, so they describe the latest run.
`cost.jsonl` keeps every run's requests.

## Damaged or leftover files

pydelity writes each file in full to a temporary file and then moves it into
place, so an interrupted run never leaves a half-written output, page file,
figure image or verdict file. Temporary files left by an interruption are
removed by a later run.

If a saved file is damaged anyway, for example after being edited by hand,
pydelity warns you and redoes the step, page or page break that writes it. A
damaged last line in `cost.jsonl` is skipped with a warning. A damaged line
anywhere else in `cost.jsonl` stops every run on the folder with an
`OutputError` that names the line. Fix that line, or use a new output folder.

## One PDF per folder, one run at a time

An output folder holds the results for one PDF. If you point a run at a folder
that holds results for a different PDF, pydelity warns you and replaces them.
Page files of the other PDF that the run doesn't replace stay in `pages/`, but
`run.json`, the report and `pydelity.load` leave them out. The folder's earlier
spending still counts toward `max_cost`, because it stays in `cost.jsonl`.

Run only one pydelity run on an output folder at a time. pydelity doesn't detect
two runs on the same folder, and they can overwrite each other's files. Runs on
different folders can go at the same time.

On Windows, pydelity can't replace a file while another program has it open. If
a run fails with an error naming a file in the output folder, close the program
that has it open and run again.

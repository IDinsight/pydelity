---
title: Use pydelity from Python
description:
  Call pydelity from scripts and notebooks, read its results as Python objects
  and handle its errors, warnings and logs.
---

`import pydelity` gives you the same steps as the command, without the
questions. Its functions are async, so you `await` them. Every function except
`load` takes the PDF, an optional `config` and settings as keyword arguments,
and `load` takes an output folder. The
[Python API reference](../../reference/python-api/) lists every argument, result
and error.

## The functions

| Function         | What it does                                                                                              | Needs an API key | Calls a model |
| ---------------- | --------------------------------------------------------------------------------------------------------- | ---------------- | ------------- |
| `ameasure`       | Measures the PDF and saves `pdf_facts.json`                                                               | No               | No            |
| `aestimate`      | Estimates what a run would cost, and writes nothing                                                       | No               | No            |
| `asurvey`        | Runs the survey and saves `pdf_survey.json`, with no `run.json` or report                                 | Yes              | Yes           |
| `aextract`       | Runs the survey if needed, then extracts the selected pages, with no `run.json` or report                 | Yes              | Yes           |
| `averify_breaks` | Runs the survey and page extraction if needed, then judges every page break, with no `run.json` or report | Yes              | Yes           |
| `arun`           | Runs everything the command does and returns all of it                                                    | Yes              | Yes           |
| `load`           | Reads an existing output folder back as Python objects                                                    | No               | No            |

`ameasure`, `aestimate`, `asurvey`, `aextract`, `averify_breaks` and `arun`
reuse saved results the same way the command does. See
[Rerun and resume](../reruns/).

## Async and sync

In Jupyter, `await` works at the top level of a cell, so the examples on this
page run there as they are. In a script, put the calls in an `async def`
function and start it with `asyncio.run`:

```python
import asyncio

import pydelity


async def main() -> None:
    result = await pydelity.arun("document.pdf")
    print(result.record.status)


asyncio.run(main())
```

Each async function also has a sync version, named without the `a`: `measure`,
`estimate`, `survey`, `extract`, `verify_breaks` and `run`. They take the same
arguments and return the same results, for code that doesn't use `async`. They
start their own event loop, so they raise `RuntimeError` where one is already
running, as in Jupyter or inside an `async def` function. `load` has only a sync
version, because it reads files only.

## Run pydelity

```python
import pydelity

result = await pydelity.arun("document.pdf", languages=["en"])

# run.json: how the run went
print(result.record.status)  # "paused" after a step wrote new output
print(result.record.cost.run_usd)

# pdf_survey.json: the survey's checked answer
for numbering in result.survey.profile.page_numbering:
    print(numbering.first_page_index, numbering.last_page_index, numbering.style)

# The review list: things a person should check
for issue in result.record.review:
    print(issue.step, issue.check, issue.page_index, issue.item_id, issue.message)
```

`arun` behaves like the command. A run that makes a new survey stops before page
extraction, with status `paused`, so you can check the survey first. A run in
which page extraction writes new page files stops before page-break verification
in the same way. A paused run returns normally, and nothing is raised. Call
`arun` again to go on to the next step, or pass `pause=False` to run every step
in one call:

```python
import pydelity

result = await pydelity.arun("document.pdf", pause=False, pages="1-5,8")
```

`arun` returns a `RunResult` with seven parts:

- `record`: the contents of `run.json`
- `facts`: the contents of `pdf_facts.json`
- `survey`: the contents of `pdf_survey.json`
- `pages`: the page files of the pages the run selected, in page order
- `breaks`: the verdict files of every page break, in break order, or an empty
  list when the run didn't reach page-break verification or skipped it
- `ledger`: the lines of `cost.jsonl`, one per model request
- `output_dir`: the output folder

The Python functions never ask questions. They go ahead with the model requests
unless the run could go over `max_cost`. In that case they raise
`BudgetExceededError` before spending more, unless you pass
`allow_over_max_cost=True`. [Control costs](../costs/) explains both.

## Extract pages

`aextract` runs page extraction on its own. It reuses a saved survey that still
fits, or runs the survey first, and never pauses. It returns the selected pages'
page files:

```python
import pydelity

pages = await pydelity.aextract("document.pdf", pages="3-4")
for page in pages:
    print(f"Page {page.page_number}: {len(page.items)} items")
    for item in page.items:
        # Each item: its ID, what it is and where it is, in points on the page.
        print(item.id, item.kind, item.role, item.label, item.bbox)
        if item.text is not None:
            print("  ", item.text)
        if item.figure is not None:
            print("   figure image:", item.figure.crop)
```

Like `asurvey`, `aextract` writes no `run.json` and no report. The page files
and figure images go to the output folder as usual. A list item's entries are in
`item.entries`, a table's rows in `item.table.rows`, and a form field's value in
`item.field`. The [page file reference](../../reference/page-json/) lists every
field.

## Verify page breaks

`averify_breaks` runs page-break verification on its own. It reuses a saved
survey and page files that still fit, or runs the survey and extracts the
selected pages first, and never pauses. It returns every break's verdict file,
in break order:

```python
import pydelity

breaks = await pydelity.averify_breaks("document.pdf")
for page_break in breaks:
    verdict = page_break.verdict
    # Page indexes start at 0, so add 1 for the page numbers a PDF viewer shows.
    print(page_break.earlier_page_index + 1, page_break.later_page_index + 1)
    print("  continues:", verdict.continues, "-", verdict.reason)
    for piece in verdict.pieces:
        # Where the piece ends and starts, and how the two parts join.
        print("  ", piece.earlier_item, "->", piece.later_item, piece.join)
        print("     text join:", piece.text_join)
```

Like `aextract`, `averify_breaks` writes no `run.json` and no report. The
verdict files go to `page_breaks/` in the output folder as usual. Every page of
the PDF needs a current page file. With `pages` set, the breaks are judged only
when every other page has one from an earlier run. Otherwise `averify_breaks`
issues a warning that names the pages without one and returns an empty list. It
also returns an empty list for a PDF with one page. See
[Verify page breaks](../page-breaks/), and the
[verdict file reference](../../reference/page-break-json/) for every field.

## Pass settings

Settings can come from keyword arguments, a config file or both. Keyword
arguments win, as described in [Settings and config files](../configuration/).

```python
import pydelity

# From a file, with one setting changed.
result = await pydelity.arun(config="report.yaml", output_dir="results/run-2")

# From a dictionary, which is handy when the settings come from your own code.
settings = {"pdf": "document.pdf", "model": "openai:gpt-6.2-astra"}
result = await pydelity.arun(config=settings)

# Settings under `advanced` go in a nested mapping.
result = await pydelity.arun(
    "document.pdf",
    advanced={"extraction": {"instructions": "Each page is a slide with notes."}},
)

# Have a verifier review each step's answer, at extra cost.
result = await pydelity.arun("document.pdf", verify=True)
```

[Review answers with a verifier](../verifiers/) shows how to turn on one step's
verifier only.

## Check a PDF before you spend

`ameasure` and `aestimate` need no API key and call no model:

```python
import pydelity

# Measure the PDF and save pdf_facts.json in its output folder.
facts = await pydelity.ameasure("document.pdf")
print("\n".join(facts.summary))

# Estimate a run with the default model. Nothing is written.
estimate = await pydelity.aestimate("document.pdf", pause=False)
print(estimate.expected_usd, estimate.max_usd)  # likely and largest cost, in USD
for step in estimate.steps:
    # step.verifier says whether the figures include the step's verifier.
    # step.pages counts pages for page extraction, step.breaks page breaks for
    # page-break verification.
    print(step.name, step.verifier, step.pages, step.breaks, step.expected_usd)
```

The estimate covers the steps the run would do. Before a survey exists, a run
with the pause on would stop after the survey, so its estimate covers only the
survey. Pass `pause=False`, as above, to include the later steps. Page-break
verification is left out when a page would have no current page file, as can
happen with `pages` set. `expected_usd` and `max_usd` are `None` when pydelity
has no price for the model.

## Read an earlier run

`load` reads an output folder without calling a model or writing anything:

```python
import pydelity

result = pydelity.load("pydelity-output/document")
if result.record is not None:
    print(result.record.status, len(result.record.review))
for page in result.pages:
    # verification is None when no verifier reviewed the page.
    reviewed = page.verification is not None
    print(page.page_index, len(page.items), reviewed)
for page_break in result.breaks:
    print(page_break.earlier_page_index, page_break.verdict.continues)
```

A part is `None`, or an empty list for `pages` and `breaks`, when its files are
missing, so a folder that only `ameasure` wrote still loads. `pages` holds the
page files made from the PDF in `pdf_facts.json`, including pages left from an
earlier, wider `pages` selection. It leaves out page files of another PDF that
ran in the folder, and it is empty when the folder has no `pdf_facts.json`.
`breaks` holds the verdict files, in break order, made from the page files that
`pages` holds. A verdict made from a page file that has since been replaced is
left out.

## Run several PDFs at once

Runs on different output folders can go at the same time, for example with
`asyncio.gather`. Each PDF gets its own output folder by default, named after
the PDF:

```python
import asyncio

import pydelity

results = await asyncio.gather(
    pydelity.arun("form-a.pdf", pause=False),
    pydelity.arun("form-b.pdf", pause=False),
)
for result in results:
    print(result.output_dir, result.record.status)
```

Each run extracts up to `advanced.extraction.concurrent_pages` pages, and judges
up to `advanced.page_breaks.concurrent_breaks` page breaks, at once, so two runs
together send up to twice as many requests. Lower `concurrent_pages` and
`concurrent_breaks` if your provider account has low rate limits.

Don't start two runs on the same output folder at once. pydelity does not detect
it, and the two runs can overwrite each other's files.

## Errors

Every error pydelity raises on purpose is a `pydelity.PydelityError`, so one
`except` clause catches them all. Each kind also has its own class:

| Error                 | When                                                                                                 |
| --------------------- | ---------------------------------------------------------------------------------------------------- |
| `ConfigError`         | A setting is invalid, such as a PDF path that doesn't exist, or the config file can't be read        |
| `PdfError`            | The PDF is empty, password-protected or can't be opened                                              |
| `MissingApiKeyError`  | The API key for a step's model provider is not set                                                   |
| `BudgetExceededError` | The run could go over `max_cost` and `allow_over_max_cost` is not set                                |
| `ProviderError`       | The provider rejected a request or kept failing after its retries                                    |
| `SurveyError`         | The survey's model or its verifier refused, ran out of output tokens or never gave a usable answer   |
| `ExtractionError`     | A page's model or its verifier refused, ran out of output tokens or never gave a usable answer       |
| `PageBreakError`      | A page break's model or its verifier refused, ran out of output tokens or never gave a usable answer |
| `OutputError`         | `load` can't read the output folder, or a run finds a damaged line in `cost.jsonl` before its last   |

```python
import pydelity

try:
    result = await pydelity.arun("document.pdf", max_cost=1, pause=False)
except pydelity.BudgetExceededError as error:
    print("Too expensive:", error)
except pydelity.PydelityError as error:
    print("pydelity failed:", error)
```

`ProviderError` keeps the provider's own message in `provider_message`, and the
HTTP status in `status_code`. An error from page extraction names the page, and
one from page-break verification names the break. Page files and verdict files
written before the error stay saved, and the next run makes only the ones still
missing.

## Warnings

pydelity issues a `pydelity.PydelityWarning` through Python's `warnings` module
for problems that don't stop the run, such as a model with no known price. Each
one is also saved in `run.json` under `warnings`. Use the standard tools to
change how they behave:

```python
import warnings

import pydelity

# Hide pydelity's warnings.
warnings.filterwarnings("ignore", category=pydelity.PydelityWarning)

# Or turn them into errors.
warnings.filterwarnings("error", category=pydelity.PydelityWarning)
```

## Logs

pydelity logs with [loguru](https://loguru.readthedocs.io/) and keeps its log
messages off until you turn them on. Importing it prints nothing.

```python
import sys

from loguru import logger

logger.enable("pydelity")
# loguru prints everything to standard error by default. To see less:
logger.remove()
logger.add(sys.stderr, level="INFO")
```

---
title: Rerun and resume
description:
  What pydelity reuses when you run it again, what makes it redo the survey and
  how to pick up after a run that stopped or failed.
---

pydelity saves each result in the output folder as soon as it has it. When you
run it again on the same folder, it reuses what still fits and only redoes the
rest. So you never pay twice for the same survey, and a run that stopped can
carry on where it left off.

## What gets reused

**The measured facts** (`pdf_facts.json`) are reused as long as the PDF's
content is unchanged. pydelity compares a SHA-256 hash of the file, so renaming
or moving the PDF doesn't matter here. A newer pydelity that measures PDFs
differently measures them again.

**The survey** (`pdf_survey.json`) is reused as long as everything it was made
from is unchanged:

- the PDF's content and its file name
- the measured facts
- `model`
- `instructions` and `languages`
- `advanced.survey.effort`, `check_retries` and `max_output_tokens`
- the survey instructions built into pydelity, which a newer release may change

Changing any of these runs the survey again, at full cost. Changing anything
else, such as `max_cost`, `provider_retries`, `request_timeout_seconds` or
`expiry_hours`, keeps the saved survey.

By default the output folder is named after the PDF, so a renamed PDF also gets
a new, empty output folder unless you set `output_dir`.

**The upload** of the PDF to the provider (`uploads.json`) is reused while at
least an hour is left before the provider deletes it. See
[How long the provider keeps your PDF](../models-and-providers/#how-long-the-provider-keeps-your-pdf).

When a run reuses the survey, it makes no model request and costs nothing. The
command's summary shows the step as `reused`.

## Redo everything

To measure and survey again even though nothing changed, use `overwrite`:

```sh
pydelity document.pdf --overwrite
```

```python
import pydelity

result = pydelity.run("document.pdf", overwrite=True)
```

The new survey costs as much as the first one. The upload is still reused.

## After a run that stopped or failed

A run can end early because you answered no, it hit `max_cost`, the provider
failed, the survey had no usable answer or you pressed Ctrl+C. In each case
`run.json` records how it ended and why, and anything already finished stays
saved.

To continue, run the same command again. pydelity reuses the saved facts, upload
and survey, and redoes only what is missing. Money already spent in the folder
still counts toward `max_cost`.

Each run replaces `run.json` and `report.html`, so they describe the latest run.
`cost.jsonl` keeps every run's requests.

## Damaged or leftover files

pydelity writes each file in full to a temporary file and then moves it into
place, so an interrupted run never leaves a half-written output. Temporary files
left by an interruption are removed at the start of the next run.

If a saved file is damaged anyway, for example after being edited by hand,
pydelity warns you and redoes the step that writes it. A damaged last line in
`cost.jsonl` is skipped with a warning.

## One PDF per folder, one run at a time

An output folder holds the results for one PDF. If you point a run at a folder
that holds results for a different PDF, pydelity warns you and replaces them.
The folder's earlier spending still counts toward `max_cost`, because it stays
in `cost.jsonl`.

Run only one pydelity run on an output folder at a time. pydelity doesn't detect
two runs on the same folder, and they can overwrite each other's files. Runs on
different folders can go at the same time.

On Windows, pydelity can't replace a file while another program has it open. If
a run fails with an error naming a file in the output folder, close the program
that has it open and run again.

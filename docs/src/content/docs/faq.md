---
title: Frequently Asked Questions
description: Short answers to common questions about using pydelity.
---

Short answers to questions people often ask. Each answer links to the page with
the full details.

## About the survey

### What does a survey give me?

Before calling a model, pydelity measures the PDF itself: its text layer, the
angle of its text, printed page numbers, bookmarks, form fields and the lines
that repeat across pages. These measured facts are saved on their own, so you
keep them even if you stop before the model is called.

The model then reads the whole PDF and answers:

- which pages carry which printed page numbers, and in which numbering style
- which pages need turning to read upright
- which way the text runs (left to right, right to left or top to bottom)
- which languages the PDF is in
- which repeated lines are headers, footers and other page furniture, and which
  are part of the content
- what kinds of regions the pages hold, such as headings, tables and figures

pydelity checks the answer and keeps a list of anything a person should look at,
such as a page where the model's page number differs from the one printed on it.
All of this goes into an output folder, with an HTML report that shows each page
with the model's regions drawn on it. See
[Read the outputs](../guides/outputs/).

### Does pydelity extract the text of each page?

Not yet. This release does the survey only. Later releases add the steps that
extract each page's content and assemble it into one document.

### Why does pydelity keep the model's answer when it disagrees with what it measured?

The model sees the pages, so it's usually the better reader. The measurements
can go wrong, for example by taking numbers in a table for page numbers. Where
the model's page number or rotation differs from what pydelity measured,
pydelity keeps the model's answer and puts the page on the review list, so a
person can decide. See [The review list](../guides/outputs/#the-review-list).

### What should I check in the results?

Open `report.html` in the output folder and start with the review issues. They
are the pages and answers that pydelity couldn't settle by itself. See
[Read the outputs](../guides/outputs/).

## Models and your data

### Which models can I use?

Anthropic and OpenAI models that read PDFs and support the `effort` setting. The
default is `anthropic:claude-opus-5-5`. To use another model, give its ID with
the provider in front, such as `openai:gpt-6.2-astra`. pydelity keeps no list of
models, so any model ID your provider accepts works. See
[Choose a model](../guides/models-and-providers/#choose-a-model).

### What does pydelity send to the provider?

The PDF, pydelity's instructions for the survey, a plain-text summary of what it
measured, and your `instructions` and `languages` if you set them. Run with
`--verbose` to see the text it sends. Only send a PDF that you're allowed to
share with your provider. See
[What is sent to the provider](../guides/models-and-providers/#what-is-sent-to-the-provider).

### How long does the provider keep my PDF?

pydelity uploads the PDF to your provider account's file storage. By default
Anthropic keeps it for 90 days and OpenAI for 30 days. Set `expiry_hours` to
keep it for less time. See
[How long the provider keeps your PDF](../guides/models-and-providers/#how-long-the-provider-keeps-your-pdf).

### Can I use pydelity without an API key?

Partly. Measuring a PDF, estimating the cost and reading an output folder work
without a key: in Python, use `measure`, `estimate` and `load`. On the command
line, a run without a key still measures the PDF and saves `pdf_facts.json`,
then stops with exit code 2. See
[Check a PDF before you spend](../guides/python/#check-a-pdf-before-you-spend).

## Costs

### How much does a survey cost?

It depends on the model and the PDF. Before spending anything, pydelity
estimates a likely cost and a maximum. For a 6-page form with the default model,
that was about $0.36, at most $2.90. On the command line it then asks whether to
go ahead. In Python, `pydelity.estimate` shows the estimate without an API key.
See [The estimate](../guides/costs/#the-estimate).

### Does running it again cost money again?

Not if the PDF and the settings that shape the survey are unchanged. pydelity
reuses the saved survey and makes no model request. Changing the model,
`instructions`, `languages` or a survey setting runs the survey again at full
cost. See [What gets reused](../guides/reruns/#what-gets-reused).

### How do I cap what a PDF can cost?

Set `max_cost`. It counts everything spent in the output folder, across runs.
When a run would go over it, the command warns you and asks whether to continue;
with `--yes`, it continues after the warning. In Python, the run raises
`BudgetExceededError` unless you pass `allow_over_max_cost=True`. See
[Set a spending limit](../guides/costs/#set-a-spending-limit).

## Running pydelity

### Does it work on Windows?

Yes. pydelity runs on Windows, macOS and Linux with Python 3.13 or 3.14 (see
[Check your Python](../start/install/#check-your-python)). A few platforms have
no ready-built PyMuPDF 2 package, among them Intel Macs and Windows on ARM. See
[Check your platform](../start/install/#check-your-platform).

### Can I run it in a script, without the cost question?

Yes. Add `--yes` to skip the question, and use the exit code to tell how the run
ended. See [Run it in a script](../guides/command-line/#run-it-in-a-script) and
[Exit codes](../guides/command-line/#exit-codes).

### Can I use it in Jupyter?

Yes, with the async functions. In a notebook, `pydelity.run` raises
`RuntimeError`, so use `await pydelity.arun(...)` instead. See
[Jupyter and async code](../guides/python/#jupyter-and-async-code).

### A run stopped partway. Is my work lost?

No. `run.json` records how the run ended and why, and anything already finished
stays saved. Run the same command again to continue. pydelity redoes only what
is missing. See
[After a run that stopped or failed](../guides/reruns/#after-a-run-that-stopped-or-failed).

### Can I survey several PDFs at once?

Yes, as long as each PDF has its own output folder, which is the default. Don't
start two runs on the same output folder at once, because pydelity doesn't
detect it and the runs can overwrite each other's files. See
[One PDF per folder, one run at a time](../guides/reruns/#one-pdf-per-folder-one-run-at-a-time).

## License

### What license does pydelity use?

pydelity is MIT-licensed. PyMuPDF, which it depends on, is licensed under the
AGPL-3.0 or a commercial license from Artifex. See
[License](../start/install/#license).

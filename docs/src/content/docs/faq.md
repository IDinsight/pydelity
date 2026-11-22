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

### Why does pydelity keep the model's answer when it disagrees with what it measured?

The model sees the pages, so it's usually the better reader. The measurements
can go wrong, for example by taking numbers in a table for page numbers, so
pydelity gives them to the model as hints only. Where the model's page number or
rotation differs from what pydelity measured, pydelity keeps the model's answer
and puts the page on the review list, so a person can decide. It never sends the
answer back to make it match. When the survey's verifier is on and accepts the
answer, the difference stays off the list. Page extraction treats its
measurements the same way. See
[The review list](../guides/outputs/#the-review-list).

### What should I check in the results?

Open `report.html` in the output folder and start with the review issues. They
are the pages and answers that pydelity couldn't settle by itself. See
[Read the outputs](../guides/outputs/).

## About page extraction

### Does pydelity extract the text of each page?

Yes. After the survey, page extraction reads each page you select and lists its
content in reading order: headings, paragraphs, lists, tables, formulas, code,
figures and form fields, each with its box on the page. Text is transcribed as
printed, in its own script, without translating it. Each page goes into its own
file in `pages/`. See [Extract pages](../guides/page-extraction/).

### Why did my run stop after the survey?

By default, a run that makes a new survey stops before page extraction, so you
can check the survey before paying for page extraction. Run the same command
again to extract the pages, or add `--no-pause` to run both steps at once. See
[Check the survey first](../guides/page-extraction/#check-the-survey-first).

### Can I extract only some pages?

Yes. Set `pages`, such as `--pages 1-5,8`. Pages are numbered from 1, as a PDF
viewer shows them. The survey still reads the whole PDF. See
[Choose the pages](../guides/page-extraction/#choose-the-pages).

### Does pydelity read the text stored in the PDF?

The models read each page's text from an image of the page. pydelity sends the
stored text of the page's repeated lines and its form fields' values as hints,
and compares the model's reading with the rest of the stored text, where it
reads well, to catch dropped or added lines. Stored text can be wrong, for
example with Arabic letters out of order or broken ligatures, so the model's
reading is kept and each difference goes on the review list. See
[Text compared with the PDF's stored text](../guides/page-extraction/#text-compared-with-the-pdfs-stored-text).

### Can pydelity double-check the model's answers?

Yes, if you turn on the verifiers with `--verify` (`verify: true` in a config
file, `verify=True` in Python). A verifier is a second request to the same model
that reviews a step's answer against the PDF and may correct it. It looks for
mistakes code can't find, such as a label that doesn't fit, a missed item or a
wrong reading order. Verifiers are off by default because each one adds cost.
The survey's verifier sends the whole PDF again, and page extraction's adds a
request for every page. Without them, every difference from what pydelity
measured goes on the review list. See
[Review answers with a verifier](../guides/verifiers/).

## Models and your data

### Which models can I use?

Anthropic and OpenAI models that read PDFs and images and support the `effort`
setting. The default for both steps is `anthropic:claude-opus-5-5`. To use
another model, give its ID with the provider in front, such as
`openai:gpt-6.2-astra`. pydelity keeps no list of models, so any model ID your
provider accepts works. See
[Choose a model](../guides/models-and-providers/#choose-a-model).

### What does pydelity send to the provider?

For the survey: the PDF, pydelity's instructions, a plain-text summary of what
it measured, and your `languages` and `advanced.survey.instructions` if you set
them. For page extraction: an image of each page, pydelity's instructions, your
`advanced.extraction.instructions` if you set them, and these hints: the
survey's results for that page, the page's repeated lines with their stored
text, and its fillable form fields with their values. A verifier, when it is on,
also gets the step's answer to review, the checks it still fails and its
differences from the hints. Only send a PDF that you're allowed to share with
your provider. See
[What is sent to the provider](../guides/models-and-providers/#what-is-sent-to-the-provider).

### How long does the provider keep my PDF?

pydelity uploads the PDF to your provider account's file storage for the survey.
By default Anthropic keeps it for 90 days and OpenAI for 30 days. Set
`advanced.uploads.expiry_hours` to keep it for less time. Page extraction sends
page images inside each request and uploads nothing. See
[How long the provider keeps your PDF](../guides/models-and-providers/#how-long-the-provider-keeps-your-pdf).

### Can I use pydelity without an API key?

Partly. Measuring a PDF, estimating the cost and reading an output folder work
without a key: in Python, use `ameasure`, `aestimate` and `load`. On the command
line, a run without a key still measures the PDF and saves `pdf_facts.json`,
then stops with exit code 2. See
[Check a PDF before you spend](../guides/python/#check-a-pdf-before-you-spend).

## Costs

### How much does a run cost?

It depends on the model and the PDF. Before spending anything, pydelity
estimates a likely cost and a maximum for each step it will run. For a 6-page
form with the default model, the survey was about $0.36, at most $2.90. Page
extraction makes one request per page, so its cost grows with the number of
pages you select. Turning on the verifiers adds a request to review the survey
and each page, which about doubles the cost. On the command line pydelity then
asks whether to go ahead. In Python, `pydelity.aestimate` shows the estimate
without an API key. See [The estimate](../guides/costs/#the-estimate).

### Does running it again cost money again?

Not if nothing that shapes the results has changed. pydelity reuses the saved
survey and page files and makes no model request. Changing the survey's model,
`languages`, `advanced.survey.instructions`, or `advanced.survey.effort`,
`check_retries` or `max_output_tokens` runs the survey again at full cost. Other
settings, such as `max_cost` or `advanced.survey.request_timeout_seconds`, keep
the saved survey. A page is extracted again only when something it depends on
changes. Turning a verifier on redoes the saved outputs that no verifier
reviewed. See [What gets reused](../guides/reruns/#what-gets-reused).

### How do I cap what a PDF can cost?

Set `max_cost`. It counts everything spent in the output folder, across runs.
When a run could go over it, the command warns you and asks whether to continue;
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

Yes. Add `--yes` to skip the question, `--no-pause` to run every step in one go,
and use the exit code to tell how the run ended. See
[Run it in a script](../guides/command-line/#run-it-in-a-script) and
[Exit codes](../guides/command-line/#exit-codes).

### Can I use it in Jupyter?

Yes. pydelity's Python functions are async, and `await pydelity.arun(...)` works
directly in a notebook cell. The sync versions, such as `pydelity.run`, raise
`RuntimeError` there. See [Async and sync](../guides/python/#async-and-sync).

### A run stopped partway. Is my work lost?

No. `run.json` records how the run ended and why, and anything already finished
stays saved, including every page file written before the run stopped. Run the
same command again to continue. pydelity redoes only what is missing. See
[After a run that stopped or failed](../guides/reruns/#after-a-run-that-stopped-or-failed).

### Can I run pydelity on several PDFs at once?

Yes, as long as each PDF has its own output folder, which is the default. Don't
start two runs on the same output folder at once, because pydelity doesn't
detect it and the runs can overwrite each other's files. See
[One PDF per folder, one run at a time](../guides/reruns/#one-pdf-per-folder-one-run-at-a-time).

## License

### What license does pydelity use?

pydelity is MIT-licensed. PyMuPDF, which it depends on, is licensed under the
AGPL-3.0 or a commercial license from Artifex. See
[License](../start/install/#license).

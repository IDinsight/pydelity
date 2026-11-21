---
title: Your first run
description:
  Run pydelity on a PDF from the command line, check the survey, extract the
  pages and find the results.
---

This page follows one PDF from the command line through the survey and page
extraction. You need pydelity installed and your API key set, as in
[Install pydelity](../install/).

## Run the survey

Open a terminal in the folder that holds your PDF and run:

```sh
pydelity document.pdf
```

If you know which languages the PDF is in, say so with `--language` (or `-l`),
once per language. The tags are BCP-47 language tags, such as `en` for English
or `ar` for Arabic:

```sh
pydelity document.pdf -l en -l ar
```

## Answer the cost question

pydelity first opens and measures the PDF. Then it estimates what the model
requests will cost and asks before sending anything. For a 2-page scanned tax
form, the output looked like this:

```text
16:04:47 | INFO     | Survey cost estimate: about $0.24, at most $2.53 (up to 3 requests to anthropic:claude-opus-5-5)
16:04:47 | INFO     | Spent so far in this output folder: $0.00; max_cost: not set
Go ahead with the model requests? [y/N]:
```

The estimate gives a likely cost and a maximum. The maximum assumes every retry
is used and every answer is as long as allowed, so most runs cost much less.

- Type `y` and press Enter to go ahead.
- Press Enter, or type `n`, to stop. Nothing is sent and nothing is spent. The
  measured facts are saved, and the next run reuses them.

To skip the question, for example in a script, add `--yes`. To cap what a PDF
may cost, see [Control costs](../../guides/costs/).

## Wait for the survey

The model reads the whole PDF in one request. That can take a few minutes for a
long PDF. pydelity checks the answer, and if it fails a check, sends it back
with the problems listed, up to two more times. Add `--verbose` to see each step
as it happens.

## Check the survey

When the survey is done, the run stops before page extraction and says so:

```text
Paused after the new survey. Check pdf_survey.json and report.html, then run pydelity again to extract the pages, or pass --no-pause (pause=False in Python) to run every step at once.
```

The results go to `pydelity-output/<PDF name>/` in the current folder, so
`document.pdf` gives `pydelity-output/document/`. To choose another folder, use
`--output-dir`.

Open `report.html` in a browser. It shows the run and its cost, the review
issues, the survey's results, the measured facts and each page with the model's
regions and any form fields drawn on it. Page extraction relies on the survey's
rotation, writing direction and labels for every page, so check those and the
review issues before you go on. [Read the outputs](../../guides/outputs/)
explains what to look for.

## Extract the pages

Run the same command again:

```sh
pydelity document.pdf
```

pydelity reuses the survey, estimates page extraction and asks again. For the
same form:

```text
16:04:48 | INFO     | Extraction cost estimate: about $0.45, at most $10.41 (2 pages, up to 12 requests to anthropic:claude-opus-5-5)
```

It also shows what the folder has spent so far, then asks the same question.

Each page takes two requests: one to read it and one to review it. The maximum
counts every retry of both. To extract only some pages, add `--pages`, such as
`--pages 1-5,8`. To run the survey and page extraction in one go next time, add
`--no-pause`. [Extract pages](../../guides/page-extraction/) covers both.

pydelity extracts up to 8 pages at the same time. When the run ends, it prints a
summary: how the run ended, what each step did and cost, how many review issues
it found with the first few listed, and the files it wrote.

## Find the results

The output folder now holds:

| File              | What it holds                                                    |
| ----------------- | ---------------------------------------------------------------- |
| `report.html`     | The results as a page to open in a browser                       |
| `pages/`          | One page file per extracted page, such as `pages/0000.json`      |
| `figures/`        | An image of each figure the pages hold                           |
| `pdf_facts.json`  | What pydelity measured in the PDF before calling a model         |
| `pdf_survey.json` | The survey's checked answer: page numbers, rotation, regions     |
| `run.json`        | How the run went, its settings, cost, warnings and review issues |
| `cost.jsonl`      | One line per model request, with its tokens and cost             |
| `uploads.json`    | The PDF's upload to the provider, so later runs can reuse it     |
| `report/pages/`   | The page images the report shows                                 |

Reload `report.html`. Each extracted page now shows its items as numbered boxes
in reading order, beside a list of the items with their content. Start with the
review issues: each one links to the page, and to the item when it is about one.
[Read the outputs](../../guides/outputs/) explains each file and what to check.

## Run it again

Running the same command again reuses the survey and every page file and costs
nothing, as long as the PDF and the settings that affect them are unchanged.
[Rerun and resume](../../guides/reruns/) explains when pydelity redoes a step or
a page.

## Next

- [Extract pages](../../guides/page-extraction/)
- [Use pydelity from Python](../../guides/python/)
- [Keep settings in a file](../../guides/configuration/)

---
title: Your first survey
description:
  Run pydelity on a PDF from the command line, answer the cost question and find
  the results.
---

This page walks through one survey from the command line. You need pydelity
installed and your API key set, as in [Install pydelity](../install/).

## Run it

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
requests will cost and asks before sending anything. For a 6-page tax form, the
output looked like this:

```text
07:05:01 | INFO     | Survey cost estimate: about $0.36, at most $2.90 (up to 3 requests to anthropic:claude-opus-5-5)
07:05:01 | INFO     | Spent so far in this output folder: $0.00; max_cost: not set
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

When the run ends, pydelity prints a summary: how the run ended, what it cost,
how many review issues it found with the first few listed, and where the output
folder is.

## Find the results

The results go to `pydelity-output/<PDF name>/` in the current folder, so
`document.pdf` gives `pydelity-output/document/`. To choose another folder, use
`--output-dir`.

The folder holds:

| File              | What it holds                                                    |
| ----------------- | ---------------------------------------------------------------- |
| `report.html`     | The results as a page to open in a browser                       |
| `pdf_facts.json`  | What pydelity measured in the PDF before calling a model         |
| `pdf_survey.json` | The model's checked answer: page numbers, rotation, regions      |
| `run.json`        | How the run went, its settings, cost, warnings and review issues |
| `cost.jsonl`      | One line per model request, with its tokens and cost             |
| `uploads.json`    | The PDF's upload to the provider, so later runs can reuse it     |
| `report/pages/`   | The page images the report shows                                 |

Start with `report.html`. It shows the run and its cost, the review issues, the
survey's results, the measured facts and each page with the model's regions and
any form fields drawn on it. [Read the outputs](../../guides/outputs/) explains
each file and what to check.

## Run it again

Running the same command again reuses the saved survey and costs nothing, as
long as the PDF and the settings that affect the survey are unchanged.
[Rerun and resume](../../guides/reruns/) explains when pydelity redoes the
survey.

## Next

- [Use pydelity from Python](../../guides/python/)
- [Keep settings in a file](../../guides/configuration/)

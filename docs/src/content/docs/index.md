---
title: pydelity
description:
  Survey any PDF with Anthropic or OpenAI models, the first step from a PDF to
  faithful, structured JSON.
---

pydelity turns PDFs into structured JSON. Its first step, the survey, reads a
PDF with an Anthropic or OpenAI model and records how its pages are laid out:
page numbers, rotation, writing direction and repeated lines, with a list of
things for a person to review.

This release does the survey only. Later releases add the steps that extract
each page's content and assemble it into one document.

## Quickstart

1. Install pydelity with [uv](https://docs.astral.sh/uv/), which also installs
   Python 3.13 if you don't have it:

   ```sh
   uv tool install pydelity
   ```

2. Set your Anthropic API key, replacing `[API_KEY]` with your own key:

   ```sh
   export ANTHROPIC_API_KEY="[API_KEY]"
   ```

   In Windows PowerShell, run `$env:ANTHROPIC_API_KEY = "[API_KEY]"` instead.

3. In the folder that holds your PDF, run a survey:

   ```sh
   pydelity document.pdf
   ```

   pydelity measures the PDF, shows what the survey will likely cost and asks
   before sending anything. Type `y` and press Enter to go ahead.

4. Open `pydelity-output/document/report.html` in a browser to see the results
   and the issues to review.

See [Install pydelity](start/install/) for other ways to install and the
platforms PyMuPDF doesn't support, and [Your first survey](start/first-survey/)
for a walkthrough.

## Find your next step

- [Install pydelity](start/install/): install it on Windows, macOS or Linux and
  set an API key.
- [Your first survey](start/first-survey/): follow one survey from the command
  line to the report.
- Guides: keep [settings](guides/configuration/) in a file, use the
  [command line](guides/command-line/) or [Python](guides/python/), choose
  [models](guides/models-and-providers/), control [costs](guides/costs/), rerun
  and resume [runs](guides/reruns/), and read the
  [output files](guides/outputs/).
- [Reference](reference/configuration/): look up exact setting names, files and
  fields.
- [FAQ](faq/): get short answers to common questions, including what a survey
  gives you.
- [Need Help?](need-help/): ask a question, report a bug or suggest an
  improvement.

---
title: pydelity
description:
  Survey any PDF, extract each page's content and verify its page breaks with
  Anthropic or OpenAI models, on the way from a PDF to faithful, structured
  JSON.
---

pydelity turns PDFs into structured JSON with Anthropic or OpenAI models. It
works in steps:

- **The survey** reads the whole PDF and records how its pages are laid out:
  page numbers, rotation, writing direction, languages and the lines that repeat
  on many pages, such as headers and footers.
- **Page extraction** reads each page you select and lists everything on it in
  reading order: headings, paragraphs, lists, tables, figures, form fields and
  more, each with its position on the page.
- **Page-break verification** looks at each pair of pages that follow each other
  and decides whether content carries on across the break, such as a sentence, a
  list or a table, and how the two parts join.

Each step has an optional verifier, a second request to the same model that
reviews the step's answer against the PDF and may correct it. Verifiers are off
unless you turn them on, because each one adds cost. Every step keeps a list of
things for a person to review. Later releases add the steps that join the pages
into one document.

## Quickstart

1. Install pydelity with [uv](https://docs.astral.sh/uv/), which also installs
   Python 3.13 if you don't have it:

   ```sh
   uv tool install --python 3.13 pydelity
   ```

2. Set your Anthropic API key, replacing `[API_KEY]` with your own key:

   ```sh
   export ANTHROPIC_API_KEY="[API_KEY]"
   ```

   In Windows PowerShell, run `$env:ANTHROPIC_API_KEY = "[API_KEY]"` instead.

3. In the folder that holds your PDF, run the survey:

   ```sh
   pydelity document.pdf
   ```

   pydelity measures the PDF, shows what the survey will likely cost and asks
   before sending anything. Type `y` and press Enter to go ahead. When the
   survey is done, the run stops so you can check it.

4. Open `pydelity-output/document/report.html` in a browser to check the
   survey's results and the issues to review.

5. Run the same command again to extract the pages. pydelity reuses the survey,
   shows what page extraction will likely cost and asks again.

6. Reload `report.html` to see each page with its items drawn on it.

7. Run the same command a third time to verify the page breaks. pydelity reuses
   the survey and the page files, shows what page-break verification will likely
   cost and asks again.

8. Reload `report.html` to see each page break's verdict beside its two pages.

See [Install pydelity](start/install/) for other ways to install and the
platforms PyMuPDF doesn't support, and [Your first run](start/first-survey/) for
a walkthrough.

## Find your next step

- [Install pydelity](start/install/): install it on Windows, macOS or Linux and
  set an API key.
- [Your first run](start/first-survey/): follow a PDF from the command line
  through the survey, page extraction and page-break verification to the report.
- Guides: keep [settings](guides/configuration/) in a file, use the
  [command line](guides/command-line/) or [Python](guides/python/),
  [extract pages](guides/page-extraction/),
  [verify page breaks](guides/page-breaks/), turn on
  [verifiers](guides/verifiers/), choose [models](guides/models-and-providers/),
  control [costs](guides/costs/), rerun and resume [runs](guides/reruns/), and
  read the [output files](guides/outputs/).
- [Reference](reference/configuration/): look up exact setting names, files and
  fields.
- [FAQ](faq/): get short answers to common questions, including what each step
  gives you.
- [Need Help?](need-help/): ask a question, report a bug or suggest an
  improvement.

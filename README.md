# pydelity

[![Docstring coverage](https://raw.githubusercontent.com/IDinsight/pydelity/main/interrogate_badge.svg)](https://interrogate.readthedocs.io/)

pydelity reads a PDF with Anthropic or OpenAI models and turns it into
structured JSON in two steps:

- **The survey** records how the PDF's pages are laid out: page numbers,
  rotation, writing direction, languages and the lines that repeat on many
  pages, such as headers and footers.
- **Page extraction** lists everything on each page you select in reading order:
  headings, paragraphs, lists, tables, formulas, figures and form fields, each
  with its position on the page.

Each step has an optional verifier, a second request to the same model that
reviews the step's answer against the PDF and may correct it. Verifiers are off
unless you turn them on, because each one adds cost.

pydelity saves the results as JSON, with a list of things a person should check,
and an HTML report you can open in a browser. These are the first steps of a
longer pipeline that will turn a PDF into faithful, structured JSON. Later
releases join the pages into one document.

- Docs: <https://idinsight.github.io/pydelity/>
- Source code: <https://github.com/IDinsight/pydelity>

## Install

pydelity needs Python 3.13 or 3.14 on Windows, macOS or Linux. On a Mac, Python
3.14 needs macOS 14 or later. Python 3.15 isn't supported yet, because a library
PyMuPDF needs has no Python 3.15 release.

To use the `pydelity` command anywhere, install it with
[uv](https://docs.astral.sh/uv/getting-started/installation/), which downloads
Python 3.13 if you don't have it:

```sh
uv tool install --python 3.13 pydelity
```

To use it from Python, install it into your project's environment instead, for
example with `pip install pydelity` or `uv add pydelity`, in an environment that
runs Python 3.13 or 3.14.

pydelity is MIT-licensed. It uses [PyMuPDF](https://pymupdf.readthedocs.io/) to
read PDFs, which is licensed under the AGPL-3.0 or a commercial license from
Artifex. Check that this fits how you plan to use and share your own code.

## Set an API key

pydelity reads the API key from an environment variable: `ANTHROPIC_API_KEY` for
Anthropic models (the default) or `OPENAI_API_KEY` for OpenAI models. It does
not read `.env` files.

```sh
# macOS and Linux
export ANTHROPIC_API_KEY="[API_KEY]"
```

```powershell
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "[API_KEY]"
```

Replace `[API_KEY]` with your own key. These commands set the key for the
current terminal only.
[Install pydelity](https://idinsight.github.io/pydelity/start/install/) shows
how to keep it set.

## Run it

```sh
pydelity document.pdf
```

pydelity measures the PDF, shows what the survey will likely cost and asks
before it sends anything to the model. When the survey is done, the run stops so
you can check it before paying for page extraction. The results go to
`pydelity-output/document/` in the current folder. Open `report.html` there to
see them.

Then run the same command again to extract the pages. It reuses the survey and
asks before spending again:

```sh
pydelity document.pdf
```

To extract only some pages, add `--pages 1-5,8`. To run both steps without
stopping, add `--no-pause`. To have a verifier review each step's answer, at
extra cost, add `--verify`. Run `pydelity --help` for the options.

From Python:

```python
import asyncio

import pydelity


async def main() -> None:
    # Python doesn't ask before spending. pydelity.aestimate(...) shows the
    # likely cost first, with no API key needed.
    result = await pydelity.arun("document.pdf", languages=["en"], pause=False)

    # Each page's items, in reading order.
    for page in result.pages:
        for item in page.items:
            print(item.id, item.kind, item.text)

    # Each issue is something a person should check.
    for issue in result.record.review:
        print(issue.step, issue.page_index, issue.message)


asyncio.run(main())
```

In Jupyter, `await pydelity.arun(...)` works directly in a cell. Each async
function also has a sync version, named without the `a`, such as
`pydelity.run(...)`.

## Settings

You can keep settings in a JSON or YAML file and pass it with
`pydelity --config config.yaml`. The
[`examples/`](https://github.com/IDinsight/pydelity/tree/main/examples) folder
has a file in each format with every setting at its default value. Copy one and
change what you need.

## Learn more

- [Your first run](https://idinsight.github.io/pydelity/start/first-survey/)
  walks through the survey, page extraction and the output files.
- The [guides](https://idinsight.github.io/pydelity/guides/configuration/) cover
  settings, the command line, Python, page extraction, verifiers, models, costs,
  reruns and outputs.
- The [reference](https://idinsight.github.io/pydelity/reference/configuration/)
  lists every setting, option, function and output field.
- [Contributing](https://idinsight.github.io/pydelity/contributing/development/)
  covers local development, the docs site and releases.

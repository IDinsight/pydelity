# pydelity

[![Docstring coverage](https://raw.githubusercontent.com/IDinsight/pydelity/main/interrogate_badge.svg)](https://interrogate.readthedocs.io/)

pydelity reads a PDF with an Anthropic or OpenAI model and records how its pages
are laid out: page numbers, rotation, writing direction, languages and the lines
that repeat on many pages, such as headers and footers. It saves the results as
JSON, with a list of things a person should check, and an HTML report you can
open in a browser.

This survey is the first step of a longer pipeline that will turn a PDF into
faithful, structured JSON. Version 0.1.0 does the survey only. Later releases
add the other steps.

- Docs: <https://idinsight.github.io/pydelity/>
- Source code: <https://github.com/IDinsight/pydelity>

## Install

pydelity needs Python 3.13 or later on Windows, macOS or Linux. To use the
`pydelity` command anywhere, install it with
[uv](https://docs.astral.sh/uv/getting-started/installation/):

```sh
uv tool install pydelity
```

To use it from Python, install it into your project's environment instead, for
example with `pip install pydelity` or `uv add pydelity`.

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

## Run a survey

```sh
pydelity document.pdf
```

pydelity measures the PDF, shows what the survey will likely cost and asks
before it sends anything to the model. The results go to
`pydelity-output/document/` in the current folder. Open `report.html` there to
see them. Run `pydelity --help` for the options.

From Python:

```python
import pydelity

# Python doesn't ask before spending. pydelity.estimate("document.pdf")
# shows the likely cost first, with no API key needed.
result = pydelity.run("document.pdf", languages=["en"])

# Each issue is something a person should check.
for issue in result.record.review:
    print(issue.page_index, issue.message)
```

In Jupyter and other async code, use `await pydelity.arun(...)` instead.

## Settings

You can keep settings in a JSON or YAML file and pass it with
`pydelity --config config.yaml`. The
[`examples/`](https://github.com/IDinsight/pydelity/tree/main/examples) folder
has a file in each format with every setting at its default value. Copy one and
change what you need.

## Learn more

- [Your first survey](https://idinsight.github.io/pydelity/start/first-survey/)
  walks through a run and its output files.
- The [guides](https://idinsight.github.io/pydelity/guides/configuration/) cover
  settings, the command line, Python, models, costs, reruns and outputs.
- The [reference](https://idinsight.github.io/pydelity/reference/configuration/)
  lists every setting, option, function and output field.
- [Contributing](https://idinsight.github.io/pydelity/contributing/development/)
  covers local development, the docs site and releases.

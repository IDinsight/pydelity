---
title: Use pydelity from Python
description:
  Call pydelity from scripts and notebooks, read its results as Python objects
  and handle its errors, warnings and logs.
---

`import pydelity` gives you the same survey as the command, without the
questions. Every function takes the PDF, an optional `config` and settings as
keyword arguments. The [Python API reference](../../reference/python-api/) lists
every argument, result and error.

## The functions

| Function   | What it does                                                                   | Needs an API key | Calls a model |
| ---------- | ------------------------------------------------------------------------------ | ---------------- | ------------- |
| `measure`  | Measures the PDF and saves `pdf_facts.json`                                    | No               | No            |
| `estimate` | Estimates what a run would cost, and writes nothing                            | No               | No            |
| `survey`   | Runs the survey step and saves `pdf_survey.json`, with no `run.json` or report | Yes              | Yes           |
| `run`      | Runs everything the command does and returns all of it                         | Yes              | Yes           |
| `load`     | Reads an existing output folder back as Python objects                         | No               | No            |

`measure`, `estimate`, `survey` and `run` reuse saved results the same way the
command does. See [Rerun and resume](../reruns/).

## Run a survey

```python
import pydelity

result = pydelity.run("document.pdf", languages=["en"])

# run.json: how the run went
print(result.record.status)  # "completed"
print(result.record.cost.run_usd)

# pdf_survey.json: the model's checked answer
for numbering in result.survey.profile.page_numbering:
    print(numbering.first_page_index, numbering.last_page_index, numbering.style)

# The review list: things a person should check
for issue in result.record.review:
    print(issue.check, issue.page_index, issue.message)
```

`run` returns a `RunResult` with five parts:

- `record`: the contents of `run.json`
- `facts`: the contents of `pdf_facts.json`
- `survey`: the contents of `pdf_survey.json`
- `ledger`: the lines of `cost.jsonl`, one per model request
- `output_dir`: the output folder

The Python functions never ask questions. They go ahead with the model requests
unless the run could go over `max_cost`. In that case they raise
`BudgetExceededError` before spending anything, unless you pass
`allow_over_max_cost=True`. [Control costs](../costs/) explains both.

## Pass settings

Settings can come from keyword arguments, a config file or both. Keyword
arguments win, as described in [Settings and config files](../configuration/).

```python
import pydelity

# From a file, with one setting changed.
result = pydelity.run(config="survey.yaml", output_dir="results/run-2")

# From a dictionary, which is handy when the settings come from your own code.
settings = {"pdf": "document.pdf", "model": "openai:gpt-6.2-astra"}
result = pydelity.run(config=settings)
```

## Check a PDF before you spend

`measure` and `estimate` need no API key and call no model:

```python
import pydelity

# Measure the PDF and save pdf_facts.json in its output folder.
facts = pydelity.measure("document.pdf")
print("\n".join(facts.summary))

# Estimate a run with the default model. Nothing is written.
estimate = pydelity.estimate("document.pdf")
print(estimate.expected_usd, estimate.max_usd)  # likely and largest cost, in USD
```

`expected_usd` and `max_usd` are `None` when pydelity has no price for the
model.

## Read an earlier run

`load` reads an output folder without calling a model or writing anything:

```python
import pydelity

result = pydelity.load("pydelity-output/document")
if result.record is not None:
    print(result.record.status, len(result.record.review))
```

A part is `None` when its file is missing, so a folder that only `measure` wrote
still loads.

## Jupyter and async code

The functions above use their own event loop. Where one is already running, as
in a Jupyter notebook or an `async` function, they raise `RuntimeError`. Use the
async versions there. They take the same arguments and are named with an `a` in
front: `ameasure`, `aestimate`, `asurvey` and `arun`.

```python
import pydelity

# In a Jupyter cell, await works at the top level.
result = await pydelity.arun("document.pdf")
```

`load` works anywhere, because it reads files only.

Runs on different output folders can go at the same time, for example with
`asyncio.gather`. Don't start two runs on the same output folder at once.
pydelity does not detect it, and the two runs can overwrite each other's files.

## Errors

Every error pydelity raises on purpose is a `pydelity.PydelityError`, so one
`except` clause catches them all. Each kind also has its own class:

| Error                 | When                                                                      |
| --------------------- | ------------------------------------------------------------------------- |
| `ConfigError`         | A setting is invalid, or the config file can't be read                    |
| `PdfError`            | The PDF is missing, empty, password-protected or can't be opened          |
| `MissingApiKeyError`  | The API key for the model's provider is not set                           |
| `BudgetExceededError` | The run could go over `max_cost` and `allow_over_max_cost` is not set     |
| `ProviderError`       | The provider rejected the request or kept failing after its retries       |
| `SurveyError`         | The model refused, ran out of output tokens or never gave a usable answer |
| `OutputError`         | `load` can't read the output folder                                       |

```python
import pydelity

try:
    result = pydelity.run("document.pdf", max_cost=1)
except pydelity.BudgetExceededError as error:
    print("Too expensive:", error)
except pydelity.PydelityError as error:
    print("pydelity failed:", error)
```

`ProviderError` keeps the provider's own message in `provider_message`, and the
HTTP status in `status_code`.

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

On some Python installs, the first model request in a process prints a short
banner from PydanticAI, the library pydelity uses to talk to models. To hide it,
set the environment variable `PYDANTIC_AI_NO_BANNER=1`, or run this before
calling pydelity:

```python
import pydantic_ai

pydantic_ai.BANNER_ENABLED = False
```

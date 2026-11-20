---
title: Python API
description: The functions, classes and errors the pydelity package exports.
sidebar:
  order: 3
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

`import pydelity` gives these functions and classes. `estimate`, `extract`,
`measure`, `run` and `survey` also have async forms, named with an `a` prefix,
to await in code that runs an event loop.

## Functions

### `estimate`

```python
def estimate(
    pdf: str | PathLike[str] | None = None,
    *,
    config: ConfigSource | None = None,
    **settings: object,
) -> CostEstimate
```

Estimate what a run on a PDF would cost (the sync version of `aestimate`).

**Parameters**

- `pdf`: The PDF. Overrides a `pdf` in `config`.
- `config`: A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a
  mapping of settings.
- `**settings`: Settings by name. They override `config`.

**Returns**

- `CostEstimate`: The expected and largest cost, the output folder's spend so
  far, and whether the run would go over `max_cost`.

**Raises**

- `ConfigError`: Listing every invalid setting, or naming a config file that
  cannot be read, or `pages` naming a page past the PDF's last page.
- `PdfError`: If the PDF is empty, password-protected or cannot be opened.
- `RuntimeError`: If called while an event loop is running, as in Jupyter or
  async code. Use `await pydelity.aestimate(...)` there instead.

### `aestimate`

```python
async def aestimate(
    pdf: str | PathLike[str] | None = None,
    *,
    config: ConfigSource | None = None,
    **settings: object,
) -> CostEstimate
```

Estimate what a run on a PDF would cost, writing nothing and calling no model.

The saved facts are used when they match, and otherwise the PDF is measured
without saving them. A survey or page file that would be reused costs nothing.
The estimate covers page extraction whenever the run would extract pages: the
selected pages without a page file to reuse, or every selected page when the
survey runs first and the run would not pause. No API key is needed.

**Parameters**

- `pdf`: The PDF. Overrides a `pdf` in `config`.
- `config`: A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a
  mapping of settings.
- `**settings`: Settings by name, such as `model="openai:gpt-6.2-astra"`. They
  override `config`.

**Returns**

- `CostEstimate`: The expected and largest cost, the output folder's spend so
  far, and whether the run would go over `max_cost`.

**Raises**

- `ConfigError`: Listing every invalid setting, or naming a config file that
  cannot be read, or `pages` naming a page past the PDF's last page.
- `PdfError`: If the PDF is empty, password-protected or cannot be opened.

### `extract`

```python
def extract(
    pdf: str | PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> list[PageFile]
```

Extract a PDF's selected pages (the sync version of `aextract`).

**Parameters**

- `pdf`: The PDF. Overrides a `pdf` in `config`.
- `allow_over_max_cost`: Whether to continue, with a warning, when the run could
  exceed `max_cost`. If false, such a run raises `BudgetExceededError` instead.
- `config`: A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a
  mapping of settings.
- `**settings`: Settings by name. They override `config`.

**Returns**

- `list[PageFile]`: The selected pages' page files, in page order.

**Raises**

- `BudgetExceededError`: If the run could go over `max_cost` and
  `allow_over_max_cost` is not set.
- `ConfigError`: Listing every invalid setting, or naming a config file that
  cannot be read, or `pages` naming a page past the PDF's last page.
- `ExtractionError`: If a model refuses, runs out of output tokens, or never
  gives a usable answer for a page.
- `MissingApiKeyError`: If the API key of a step's provider is not set.
- `PdfError`: If the PDF is empty, password-protected or cannot be opened.
- `ProviderError`: If the provider rejects the upload for an invalid API key or
  as too large, or a request fails after the provider retries.
- `RuntimeError`: If called while an event loop is running, as in Jupyter or
  async code. Use `await pydelity.aextract(...)` there instead.
- `SurveyError`: If the survey's model refuses, runs out of output tokens, or
  never gives an answer that matches the survey's answer format.

### `aextract`

```python
async def aextract(
    pdf: str | PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> list[PageFile]
```

Extract a PDF's selected pages, running or reusing the survey first.

The survey saved in `pdf_survey.json` is reused when its inputs are unchanged;
otherwise the survey runs. Then each selected page's page file is reused when
its inputs are unchanged, and the other pages are extracted, several at a time,
and saved in `pages/`, with figure images in `figures/`. It never pauses, writes
no `run.json` and no report, and does not prompt for input.

**Parameters**

- `pdf`: The PDF. Overrides a `pdf` in `config`.
- `allow_over_max_cost`: Whether to continue, with a warning, when the run could
  exceed `max_cost`. If false, such a run raises `BudgetExceededError` instead.
- `config`: A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a
  mapping of settings.
- `**settings`: Settings by name, such as `pages="1-5,8"` or
  `advanced={"extraction": {"concurrent_pages": 4}}`. They override `config`.

**Returns**

- `list[PageFile]`: The selected pages' page files, in page order.

**Raises**

- `BudgetExceededError`: If the run could go over `max_cost` and
  `allow_over_max_cost` is not set.
- `ConfigError`: Listing every invalid setting, or naming a config file that
  cannot be read, or `pages` naming a page past the PDF's last page.
- `ExtractionError`: If a model refuses, runs out of output tokens, or never
  gives a usable answer for a page.
- `MissingApiKeyError`: If the API key of a step's provider is not set.
- `PdfError`: If the PDF is empty, password-protected or cannot be opened.
- `ProviderError`: If the provider rejects the upload for an invalid API key or
  as too large, or a request fails after the provider retries.
- `SurveyError`: If the survey's model refuses, runs out of output tokens, or
  never gives an answer that matches the survey's answer format.

### `load`

```python
def load(output_dir: str | PathLike[str]) -> RunResult
```

Read an output folder back as Python objects.

It calls no model, needs no API key and writes nothing, so it works anywhere,
including in a running event loop.

**Parameters**

- `output_dir`: The output folder of an earlier `run`, `survey` or `measure`.

**Returns**

- `RunResult`: The folder's `run.json`, `pdf_facts.json`, `pdf_survey.json`,
  `cost.jsonl` and every page file in `pages/`, in page order. A part is `None`,
  or empty, when its files are absent.

**Raises**

- `OutputError`: If the folder does not exist, holds none of those files, or
  holds one that is not valid JSON, does not match its schema or has another
  major schema version, or a page file names a figure image that is missing.

### `measure`

```python
def measure(
    pdf: str | PathLike[str] | None = None,
    *,
    config: ConfigSource | None = None,
    **settings: object,
) -> PdfFacts
```

Measure a PDF and save `pdf_facts.json` (the sync version of `ameasure`).

**Parameters**

- `pdf`: The PDF. Overrides a `pdf` in `config`.
- `config`: A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a
  mapping of settings.
- `**settings`: Settings by name. They override `config`.

**Returns**

- `PdfFacts`: The facts, as saved in `pdf_facts.json`.

**Raises**

- `ConfigError`: Listing every invalid setting, or naming a config file that
  cannot be read.
- `PdfError`: If the PDF is empty, password-protected or cannot be opened.
- `RuntimeError`: If called while an event loop is running, as in Jupyter or
  async code. Use `await pydelity.ameasure(...)` there instead.

### `ameasure`

```python
async def ameasure(
    pdf: str | PathLike[str] | None = None,
    *,
    config: ConfigSource | None = None,
    **settings: object,
) -> PdfFacts
```

Measure a PDF and save `pdf_facts.json`, or reuse the saved facts.

No API key is needed and no model is called. Only the `pdf`, `output_dir` and
`overwrite` settings matter, though every setting is checked.

**Parameters**

- `pdf`: The PDF. Overrides a `pdf` in `config`.
- `config`: A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a
  mapping of settings.
- `**settings`: Settings by name, such as `output_dir="out/w9"`. They override
  `config`.

**Returns**

- `PdfFacts`: The facts, as saved in `pdf_facts.json`.

**Raises**

- `ConfigError`: Listing every invalid setting, or naming a config file that
  cannot be read.
- `PdfError`: If the PDF is empty, password-protected or cannot be opened.

### `run`

```python
def run(
    pdf: str | PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> RunResult
```

Run pydelity on a PDF (the sync version of `arun`).

**Parameters**

- `pdf`: The PDF to process. Overrides a `pdf` in `config`.
- `allow_over_max_cost`: Whether to continue, with a warning, when the run could
  exceed `max_cost`. If false, such a run raises `BudgetExceededError` instead.
- `config`: A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a
  mapping of settings.
- `**settings`: Settings by name, such as `model="openai:gpt-6.2-astra"`,
  `pages="1-5"`, `pause=False` or `advanced={"survey": {"effort": "medium"}}`.
  They override `config`.

**Returns**

- `RunResult`: The run's record, facts, survey, selected pages' page files and
  the output folder's ledger.

**Raises**

- `BudgetExceededError`: If the run could go over `max_cost` and
  `allow_over_max_cost` is not set.
- `ConfigError`: Listing every invalid setting, or naming a config file that
  cannot be read, or `pages` naming a page past the PDF's last page.
- `ExtractionError`: If a model refuses, runs out of output tokens, or never
  gives a usable answer for a page.
- `MissingApiKeyError`: If the API key of a step's provider is not set.
- `PdfError`: If the PDF is empty, password-protected or cannot be opened.
- `ProviderError`: If the provider rejects the upload for an invalid API key or
  as too large, or a request fails after the provider retries.
- `RuntimeError`: If called while an event loop is running, as in Jupyter or
  async code. Use `await pydelity.arun(...)` there instead.
- `SurveyError`: If the model refuses, runs out of output tokens, or never gives
  an answer that matches the survey's answer format.

### `arun`

```python
async def arun(
    pdf: str | PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> RunResult
```

Run pydelity on a PDF.

The run validates the settings, opens the PDF and measures it, or reuses the
facts saved in `pdf_facts.json` in the output folder. It then reuses the survey
saved in `pdf_survey.json` when its inputs are unchanged. Otherwise it checks
the providers' API keys and the cost estimate against `max_cost`, uploads the
PDF (or reuses its upload from `uploads.json`), asks the model to survey it and
saves `pdf_survey.json`. With `pause` on, the default, a run that made a new
survey ends there with status `paused`, so the survey can be checked first; the
next run goes on. Page extraction then reuses or writes a page file in `pages/`
for each selected page. The run is recorded in `run.json` and `report.html`,
also when it fails, stops or pauses, and does not prompt for input.

**Parameters**

- `pdf`: The PDF to process. Overrides a `pdf` in `config`.
- `allow_over_max_cost`: Whether to continue, with a warning, when the run could
  exceed `max_cost`. If false, such a run raises `BudgetExceededError` instead.
- `config`: A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a
  mapping of settings.
- `**settings`: Settings by name, such as `model="openai:gpt-6.2-astra"`,
  `pages="1-5"`, `pause=False` or `advanced={"survey": {"effort": "medium"}}`.
  They override `config`.

**Returns**

- `RunResult`: The run's record, facts, survey, selected pages' page files and
  the output folder's ledger.

**Raises**

- `BudgetExceededError`: If the run could go over `max_cost` and
  `allow_over_max_cost` is not set.
- `ConfigError`: Listing every invalid setting, or naming a config file that
  cannot be read, or `pages` naming a page past the PDF's last page.
- `ExtractionError`: If a model refuses, runs out of output tokens, or never
  gives a usable answer for a page.
- `MissingApiKeyError`: If the API key of a step's provider is not set.
- `PdfError`: If the PDF is empty, password-protected or cannot be opened.
- `ProviderError`: If the provider rejects the upload for an invalid API key or
  as too large, or a request fails after the provider retries.
- `SurveyError`: If the model refuses, runs out of output tokens, or never gives
  an answer that matches the survey's answer format.

### `survey`

```python
def survey(
    pdf: str | PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> PdfSurvey
```

Run the survey step alone (the sync version of `asurvey`).

**Parameters**

- `pdf`: The PDF. Overrides a `pdf` in `config`.
- `allow_over_max_cost`: Whether to continue, with a warning, when the survey
  could exceed `max_cost`. If false, such a survey raises `BudgetExceededError`
  instead.
- `config`: A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a
  mapping of settings.
- `**settings`: Settings by name. They override `config`.

**Returns**

- `PdfSurvey`: The survey, as saved in `pdf_survey.json`.

**Raises**

- `BudgetExceededError`: If the survey could go over `max_cost` and
  `allow_over_max_cost` is not set.
- `ConfigError`: Listing every invalid setting, or naming a config file that
  cannot be read.
- `MissingApiKeyError`: If the selected provider's API key is not set.
- `PdfError`: If the PDF is empty, password-protected or cannot be opened.
- `ProviderError`: If the provider rejects the upload for an invalid API key or
  as too large, or a request fails after the provider retries.
- `RuntimeError`: If called while an event loop is running, as in Jupyter or
  async code. Use `await pydelity.asurvey(...)` there instead.
- `SurveyError`: If the model refuses, runs out of output tokens, or never gives
  an answer that matches the survey's answer format.

### `asurvey`

```python
async def asurvey(
    pdf: str | PathLike[str] | None = None,
    *,
    allow_over_max_cost: bool = False,
    config: ConfigSource | None = None,
    **settings: object,
) -> PdfSurvey
```

Run the survey step alone and save `pdf_survey.json`, or reuse the saved one.

It writes `pdf_facts.json`, `pdf_survey.json` and the ledger lines of its
requests, but no `run.json` and no report. It does not prompt for input.

**Parameters**

- `pdf`: The PDF. Overrides a `pdf` in `config`.
- `allow_over_max_cost`: Whether to continue, with a warning, when the survey
  could exceed `max_cost`. If false, such a survey raises `BudgetExceededError`
  instead.
- `config`: A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a
  mapping of settings.
- `**settings`: Settings by name, such as `model="openai:gpt-6.2-astra"`. They
  override `config`.

**Returns**

- `PdfSurvey`: The survey, as saved in `pdf_survey.json`.

**Raises**

- `BudgetExceededError`: If the survey could go over `max_cost` and
  `allow_over_max_cost` is not set.
- `ConfigError`: Listing every invalid setting, or naming a config file that
  cannot be read.
- `MissingApiKeyError`: If the selected provider's API key is not set.
- `PdfError`: If the PDF is empty, password-protected or cannot be opened.
- `ProviderError`: If the provider rejects the upload for an invalid API key or
  as too large, or a request fails after the provider retries.
- `SurveyError`: If the model refuses, runs out of output tokens, or never gives
  an answer that matches the survey's answer format.

## Classes and errors

- `BudgetExceededError`: A run would go over `max_cost` and the caller did not
  allow it.
- [`Config`](../configuration/): All the settings for a pydelity run.
- `ConfigError`: One or more settings are invalid.
- `CostEstimate`: A run's likely and maximum cost, estimated before it spends
  anything.
- `ExtractionError`: Page extraction could not get a usable answer for a page.
- `MissingApiKeyError`: The API key for the selected model provider is missing
  or empty.
- `OutputError`: An output folder, or a file in it, cannot be read back.
- `PageFile`: The contents of `pages/<NNNN>.json`: one page's items and their
  checks.
- `PdfError`: The PDF is empty, password-protected or cannot be opened.
- [`PdfFacts`](../pdf-facts-json/): The contents of `pdf_facts.json`: the
  measured facts and their summary.
- [`PdfSurvey`](../pdf-survey-json/): The contents of `pdf_survey.json`: the
  checked survey of one PDF.
- `ProviderError`: A model provider failed or rejected a request after its
  retries.
- `PydelityError`: Base class for every error pydelity raises deliberately.
- `PydelityWarning`: A problem the user should know about that does not stop the
  run.
- [`RunRecord`](../run-json/): The contents of `run.json`: one run on one PDF.
- `RunResult`: What a run left in its output folder, read back as Python
  objects.
- `SurveyError`: The survey step could not produce a usable answer.

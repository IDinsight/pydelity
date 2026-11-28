---
title: Settings and config files
description:
  Keep pydelity's settings in a JSON or YAML file, and learn which setting wins
  when the same one is given twice.
---

pydelity's settings can be given in three places:

- as a command-line option, such as `--model` or `--max-cost`
- as a keyword argument to a Python function, such as `model=` or `max_cost=`
- in a JSON or YAML config file

The settings under `advanced`, such as each step's instructions, have no
command-line option. Set them in a config file or from Python.

The [Configuration reference](../../reference/configuration/) lists every
setting with its type, default and meaning.

## Start from an example file

The repository's
[`examples/`](https://github.com/IDinsight/pydelity/tree/main/examples) folder
holds `config.yaml` and `config.json`. Each lists every setting at its default
value, with the YAML file explaining each one in a comment. Copy one next to
your PDFs, delete the settings you don't need to change and edit the rest.

A small config file might look like this:

```yaml
# report.yaml
pdf: reports/annual-report-2025.pdf
languages: [en, fr]
pages: 1-20
max_cost: 20
advanced:
  survey:
    instructions: >-
      The appendix tables run sideways on landscape pages.
```

Then run:

```sh
pydelity --config report.yaml
```

The file must end in `.json`, `.yaml` or `.yml`. A setting pydelity does not
know, such as a misspelled name, is an error rather than being ignored.

## Which setting wins

When a setting is given in more than one place, the most specific one wins:

1. A command-line option or Python keyword argument.
2. The config file.
3. pydelity's default.

For example, `pydelity other.pdf --config report.yaml` runs on `other.pdf`, not
the PDF named in the file, and keeps the file's other settings. The same holds
inside `advanced`: a Python keyword argument that sets one advanced setting
keeps the file's other advanced settings.

## Relative paths

The `pdf` and `output_dir` settings are paths.

- In a config file, a relative path is relative to the folder that holds the
  config file, not the folder you run pydelity from. This lets you keep a config
  file next to its PDFs and run it from anywhere.
- On the command line or in Python, a relative path is relative to the current
  folder.

A path starting with `~` means your home folder in both cases.

When `output_dir` is not set, the output goes to `pydelity-output/<PDF name>/`
in the current folder, where `<PDF name>` is the PDF's file name without `.pdf`.

## Invalid settings

pydelity checks every setting before it opens the PDF or calls a model, and
lists all the problems at once:

```text
07:05:40 | ERROR    | 2 invalid settings:
- max_cost: Input should be greater than 0 (got -1)
- modle: not a setting pydelity knows
```

The command then exits with code 2. In Python, the same problems raise
`pydelity.ConfigError`. A `pages` value that names a page past the end of the
PDF is caught the same way, just after the PDF is opened and still before
anything is sent.

## Advanced settings

Settings under `advanced:` tune each step and how pydelity talks to the models.
Most runs never need them.

| Setting                                        | Default | What it changes                                                          |
| ---------------------------------------------- | ------- | ------------------------------------------------------------------------ |
| `advanced.extraction.check_retries`            | `2`     | How often a model may try again after failing the page checks            |
| `advanced.extraction.concurrent_pages`         | `8`     | How many pages are extracted at the same time, from 1 to 32              |
| `advanced.extraction.effort`                   | `high`  | How hard the models think: `low`, `medium` or `high`                     |
| `advanced.extraction.instructions`             | not set | What is unusual about the PDF, in your words, for page extraction        |
| `advanced.extraction.max_output_tokens`        | `32000` | The longest answer a model may give for one page, thinking included      |
| `advanced.extraction.model`                    | not set | The model for page extraction only, in place of `model`                  |
| `advanced.extraction.request_timeout_seconds`  | `600`   | How long to wait for one page request                                    |
| `advanced.extraction.verify`                   | not set | Turns page extraction's verifier on or off, in place of `verify`         |
| `advanced.models`                              | none    | Your own prices for a model                                              |
| `advanced.page_breaks.check_retries`           | `2`     | How often a model may try again after failing the page-break checks      |
| `advanced.page_breaks.concurrent_breaks`       | `8`     | How many page breaks are judged at the same time, from 1 to 32           |
| `advanced.page_breaks.effort`                  | `high`  | How hard the models think: `low`, `medium` or `high`                     |
| `advanced.page_breaks.instructions`            | not set | What is unusual about the PDF's page breaks, in your words               |
| `advanced.page_breaks.max_output_tokens`       | `32000` | The longest answer a model may give for one break, thinking included     |
| `advanced.page_breaks.model`                   | not set | The model for page-break verification only, in place of `model`          |
| `advanced.page_breaks.request_timeout_seconds` | `600`   | How long to wait for one page-break request                              |
| `advanced.page_breaks.verify`                  | not set | Turns page-break verification's verifier on or off, in place of `verify` |
| `advanced.provider_retries`                    | `2`     | Retries after a temporary provider failure, such as a timeout            |
| `advanced.survey.check_retries`                | `2`     | How often the model may try again after failing the survey checks        |
| `advanced.survey.effort`                       | `high`  | How hard the model thinks: `low`, `medium` or `high`                     |
| `advanced.survey.instructions`                 | not set | What is unusual about the PDF, in your words, for the survey             |
| `advanced.survey.max_output_tokens`            | `32000` | The longest answer the model may give, thinking included                 |
| `advanced.survey.request_timeout_seconds`      | `900`   | How long to wait for one survey request                                  |
| `advanced.survey.verify`                       | not set | Turns the survey's verifier on or off, in place of `verify`              |
| `advanced.uploads.expiry_hours`                | not set | How long the provider keeps the PDF uploaded for the survey              |

Lowering `effort` or `check_retries` makes a run cheaper and faster, and can
make the answer less reliable. [Extract pages](../page-extraction/) covers page
extraction's settings and instructions, [Verify page breaks](../page-breaks/)
covers page-break verification's,
[Review answers with a verifier](../verifiers/) covers `verify` and each step's
override, [Models and providers](../models-and-providers/) covers retries and
uploads, and [Control costs](../costs/) covers prices.

On the command line, advanced settings can only come from a config file. In
Python, pass them as a nested mapping:

```python
import pydelity

# Only the settings given here change; the rest keep their defaults.
result = await pydelity.arun(
    "document.pdf",
    advanced={"extraction": {"effort": "medium"}, "provider_retries": 4},
)
```

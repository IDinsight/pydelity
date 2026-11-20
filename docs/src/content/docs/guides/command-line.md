---
title: Use the command line
description:
  Run pydelity from a terminal or a script, read what it prints and act on its
  exit codes.
---

The `pydelity` command takes one PDF and any options:

```sh
pydelity [OPTIONS] [pdf]
```

Run `pydelity --help` to list the options, or see the
[Command line reference](../../reference/cli/). If the command is not on your
path, `python -m pydelity` runs the same thing.

## Common options

```sh
# Say which languages the PDF is in.
pydelity document.pdf --language en --language ar

# Extract only pages 1 to 5 and page 8.
pydelity document.pdf --pages 1-5,8

# Run the survey and page extraction without stopping in between.
pydelity document.pdf --no-pause

# Use an OpenAI model. It needs OPENAI_API_KEY.
pydelity document.pdf --model openai:gpt-6.2-astra

# Write the results to a folder of your choice.
pydelity document.pdf --output-dir results/document

# Read the settings from a file, but run on another PDF.
pydelity other.pdf --config report.yaml
```

Options you leave out come from the config file if you give one, and otherwise
from pydelity's defaults. Some settings, such as each step's instructions, have
no option and come only from the config file. See
[Settings and config files](../configuration/).

## Two runs or one

By default, the first run on a PDF stops after the survey, so you can check it
before paying for page extraction. The second run reuses the survey and extracts
the pages. Add `--no-pause` (or `-np`) to do both in one run.
[Extract pages](../page-extraction/#check-the-survey-first) explains why.

## What it prints

By default, pydelity prints only warnings, errors, the cost estimate and the
summary at the end. Add `--verbose` (or `-v`) to also see each step as it
happens: the settings in use, what was measured in the PDF, the text sent with
the survey, and each page's checks, verifier result and cost.

The summary lists each step's outcome and cost, and the first review issues,
each with the step, the page number from 1 and, when it is about one item, the
item's ID:

```text
Run completed: survey reused, extraction completed (2 pages selected: 2 extracted, 0 reused); ...
```

Everything goes to standard error, so you can save it with `2>`:

```sh
pydelity document.pdf --verbose 2> pydelity.log
```

The same information is saved in the output folder whatever you choose here.
[Read the outputs](../outputs/) covers where.

## Run it in a script

pydelity asks before it spends money. When its input is not a terminal, as in a
script, a scheduled job or CI, it can't ask, so it stops with exit code 3
instead. Add `--yes` (or `-y`) to go ahead without asking, and `--no-pause` to
run every step:

```sh
pydelity document.pdf --yes --no-pause --max-cost 10
```

With `--yes`, `--max-cost` does not stop the run. If the run could go over it,
pydelity prints a warning and carries on. To stop a script at `max_cost`, call
pydelity from Python instead, where going over it raises an error unless you
allow it. See [Control costs](../costs/).

To run every PDF in a folder on macOS or Linux:

```sh
for pdf in pdfs/*.pdf; do
  pydelity "$pdf" --yes --no-pause || echo "Failed: $pdf (exit code $?)"
done
```

In Windows PowerShell:

```powershell
Get-ChildItem pdfs\*.pdf | ForEach-Object {
    pydelity $_.FullName --yes --no-pause
    if ($LASTEXITCODE -ne 0) { Write-Host "Failed: $($_.Name) (exit code $LASTEXITCODE)" }
}
```

Each PDF gets its own output folder named after its file. Two PDFs with the same
file name in different folders would share one output folder, so give them
different names or set `--output-dir` for each.

## Exit codes

| Code  | Meaning                                                                                      | What to do                                                                          |
| ----- | -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `0`   | The run completed, or paused after the survey. It may still have review issues.              | Read the review issues in the report; after a pause, run again to extract the pages |
| `1`   | The run failed: the provider returned an error, or the survey or a page had no usable answer | Read the error; the [models guide](../models-and-providers/) covers provider errors |
| `2`   | A setting is invalid, the API key is not set, or the PDF can't be opened                     | Fix what the error names and run again                                              |
| `3`   | The run stopped: you answered no, or input is not a terminal and `--yes` was not given       | Run again, with `--yes` in a script                                                 |
| `130` | You pressed Ctrl+C                                                                           | Run again to continue                                                               |

Once the PDF is open, a run that stops or fails still writes `run.json` and
`report.html`, and keeps whatever it finished, including every page file already
written. Running the same command again picks up from there. See
[Rerun and resume](../reruns/).

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

# Give the model a hint about this PDF.
pydelity document.pdf --instructions "Pages 40 to 52 are scanned and rotated."

# Use an OpenAI model. It needs OPENAI_API_KEY.
pydelity document.pdf --model openai:gpt-6.2-astra

# Write the results to a folder of your choice.
pydelity document.pdf --output-dir results/document

# Read the settings from a file, but survey another PDF.
pydelity other.pdf --config survey.yaml
```

Options you leave out come from the config file if you give one, and otherwise
from pydelity's defaults. See [Settings and config files](../configuration/).

## What it prints

By default, pydelity prints only warnings, errors, the cost estimate and the
summary at the end. Add `--verbose` (or `-v`) to also see each step as it
happens, the settings in use, what was measured in the PDF and the text sent to
the model.

Everything goes to standard error, so you can save it with `2>`:

```sh
pydelity document.pdf --verbose 2> pydelity.log
```

The same information is saved in the output folder whatever you choose here.
[Read the outputs](../outputs/) covers where.

## Run it in a script

pydelity asks before it spends money. When its input is not a terminal, as in a
script, a scheduled job or CI, it can't ask, so it stops with exit code 3
instead. Add `--yes` (or `-y`) to go ahead without asking:

```sh
pydelity document.pdf --yes --max-cost 3
```

With `--yes`, `--max-cost` does not stop the run. If the run could go over it,
pydelity prints a warning and carries on. To stop a script at `max_cost`, call
pydelity from Python instead, where going over it raises an error unless you
allow it. See [Control costs](../costs/).

To survey every PDF in a folder on macOS or Linux:

```sh
for pdf in pdfs/*.pdf; do
  pydelity "$pdf" --yes || echo "Failed: $pdf (exit code $?)"
done
```

In Windows PowerShell:

```powershell
Get-ChildItem pdfs\*.pdf | ForEach-Object {
    pydelity $_.FullName --yes
    if ($LASTEXITCODE -ne 0) { Write-Host "Failed: $($_.Name) (exit code $LASTEXITCODE)" }
}
```

Each PDF gets its own output folder named after its file. Two PDFs with the same
file name in different folders would share one output folder, so give them
different names or set `--output-dir` for each.

## Exit codes

| Code  | Meaning                                                                                | What to do                                                                          |
| ----- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `0`   | The run completed. It may still have review issues.                                    | Read the review issues in the report                                                |
| `1`   | The run failed: the provider returned an error, or the survey had no usable answer     | Read the error; the [models guide](../models-and-providers/) covers provider errors |
| `2`   | A setting is invalid, the API key is not set, or the PDF can't be opened               | Fix what the error names and run again                                              |
| `3`   | The run stopped: you answered no, or input is not a terminal and `--yes` was not given | Run again, with `--yes` in a script                                                 |
| `130` | You pressed Ctrl+C                                                                     | Run again to continue                                                               |

Once the PDF is open, a run that stops or fails still writes `run.json` and
`report.html`, and keeps whatever it finished. Running the same command again
picks up from there. See [Rerun and resume](../reruns/).

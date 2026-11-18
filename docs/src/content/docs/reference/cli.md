---
title: Command line
description: The pydelity command's argument, options and exit codes.
sidebar:
  order: 2
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

Turn a PDF into faithful, structured JSON.

```sh
pydelity [OPTIONS] [pdf]
```

## Argument and options

- `pdf`: The PDF to process. Overrides pdf in the config file.
- `--config`, `-c` `FILE`: A JSON or YAML file of settings.
- `--instructions`, `-i` `TEXT`: Extra instructions for the model about this
  PDF.
- `--language`, `-l` `TAG`: A language of the PDF as a BCP-47 tag, such as en;
  repeat for more.
- `--output-dir`, `-d` `DIR`: The output folder. Default:
  `pydelity-output/<PDF name>`.
- `--model`, `-m` `MODEL`: The model, as &lt;provider&gt;:&lt;model-id&gt; with
  provider anthropic or openai. Default: `anthropic:claude-opus-5-5`.
- `--max-cost`, `-mc` `USD`: The most the output folder's model requests may
  cost, in US dollars.
- `--overwrite`, `-o`: Redo steps whose outputs could be reused.
- `--yes`, `-y`: Go ahead without asking, even over max_cost (after its
  warning).
- `--verbose`, `-v`: Also show progress and details, such as the settings in
  use.
- `--version`, `-V`: Show the version and exit.
- `-h`, `--help`: Show the options and exit.

## Exit codes

- `0`: The run completed, with or without review issues.
- `1`: The run failed: a provider error, a survey error or an unexpected error.
- `2`: A setting, the API key or the PDF is invalid.
- `3`: The run stopped at the user's answer, or because input is not a terminal
  and `--yes` was not given.
- `130`: The run was interrupted with Ctrl+C.

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
- `--language`, `-l` `TAG`: A language of the PDF as a BCP-47 tag, such as en;
  repeat for more.
- `--pages`, `-p` `PAGES`: Pages to extract, numbered from 1, such as 1-5,8; all
  pages if unset.
- `--output-dir`, `-d` `DIR`: The output folder. Default:
  `pydelity-output/<PDF name>`.
- `--model`, `-m` `MODEL`: The model for every step, as
  &lt;provider&gt;:&lt;model-id&gt; with provider anthropic or openai. If unset,
  the survey uses anthropic:claude-opus-5-5 and page extraction uses
  anthropic:claude-opus-5-5. advanced.extraction.model in the config file
  overrides it for page extraction.
- `--max-cost`, `-mc` `USD`: The most the output folder's model requests may
  cost, in US dollars.
- `--overwrite`, `-o`: Redo steps whose outputs could be reused.
- `--no-pause`, `-np`: Run every step without stopping after the survey.
- `--verify`, `-vf`: Have a verifier review each step's answer, at extra cost.
- `--yes`, `-y`: Go ahead without asking, even over max_cost (after its
  warning).
- `--verbose`, `-v`: Also show progress and details, such as the settings in
  use.
- `--version`, `-V`: Show the version and exit.
- `-h`, `--help`: Show the options and exit.

## Exit codes

- `0`: The run completed, with or without review issues.
- `1`: The run failed: a provider error, a survey or page extraction error, or
  an unexpected error.
- `2`: A setting, the API key or the PDF is invalid.
- `3`: The run stopped at the user's answer, or because input is not a terminal
  and `--yes` was not given.
- `130`: The run was interrupted with Ctrl+C.

<!-- STANDARDS
Artifact: DEVELOPMENT
Cycle: build-step-3-page-break-verification-of-20261122T170208Z-00fe2896
-->

# Development Plan

`Cycle`: `build-step-3-page-break-verification-of-20261122T170208Z-00fe2896`
`Mode`: `STEPWISE` `User Style`: `tony` `User Style Locked`: `true` `Status`:
`IN_PROGRESS` `Verification Cadence`: `AFTER_IMPLEMENTATION`
`Current Increment`: `NONE`

## Implementation Contract

- `Scope`:
  `.standards/docs/scope/build-step-3-page-break-verification-of-20261122T170208Z-00fe2896.md`
- `Architecture`:
  `.standards/docs/specs/build-step-3-page-break-verification-of-20261122T170208Z-00fe2896.md`
- `Request`:
  `Build page-break verification (step 3) on top of 0.2.0: one verdict per break between consecutive pages, judged from both whole pages, naming the continuing pieces by item ID with their join rules, repeated header rows, repeated items, continuation markers and continuing containers; code checks and the survey's start-marker hint; an opt-in verifier; the step's settings, pause, estimate, spend control, reuse, review list, report, Python functions, smoke test and reference pages, ready for release 0.3.0.`

## Build Steps

### DEV-001 — Page-break verification settings

`Status`: `DONE` `Depends On`: `NONE` `Acceptance`:
`AC-008, AC-009, AC-010, AC-028`

**Goal**

Give the config the step's settings and the resolved model and verifier switch,
so later steps read them from `Config`.

**Affected Area**

`src/pydelity/config/schemas.py` (`PageBreaksConfig`,
`AdvancedConfig.page_breaks`, `Config.page_breaks_model`,
`Config.verify_page_breaks`, the `pages` docstring),
`src/pydelity/providers/profiles.py` (`DEFAULT_PAGE_BREAKS_MODEL`),
`src/pydelity/providers/factory.py` and `pipeline/runner.py` `_step_model`
(settings type), `examples/config.json`, `examples/config.yaml`.

**Expected Outcome**

- `advanced.page_breaks` (`extra="forbid"`) with the design's **Defaults**:
  `check_retries` 2 (0–5), `concurrent_breaks` 8 (1–32), `effort` `high`,
  `instructions` unset (blank is unset), `max_output_tokens` 32,000, `model`
  unset, `request_timeout_seconds` 600, `verify` `null`. It sits between
  `models` and `provider_retries`.
- `Config.page_breaks_model` is `advanced.page_breaks.model`, else `model`, else
  `anthropic:claude-opus-5-5`; `Config.verify_page_breaks` is
  `advanced.page_breaks.verify`, else `verify`.
- `build_model` and `_step_model` accept `PageBreaksConfig`.
- Both example files hold `advanced.page_breaks` with every key at its default,
  in alphabetical order, with the comments the design names, and load without a
  `ConfigError`. No CLI option is added.

**Self-Check**

`.venv/bin/ruff check scripts src`, `ruff format --check`,
`ty check scripts src` and `interrogate scripts src`; pytest and the doctests
(the example-config completeness test must pass); a scratchpad script that
resolves the model and the verifier switch from files and keywords (overrides,
`null`, `--model`, `verify`), rejects out-of-range values and unknown keys, and
loads both example files; the regenerated configuration reference page shows the
new section.

Evidence, 2026-11-22, repo root, on `13ac196` plus the uncommitted DEV-001
changes (macOS arm64, Python 3.13.9). The tools ran from `.venv/bin`, since uv
cannot write its cache in the sandbox. Assessed content:
`git diff HEAD -- src scripts examples docs`, 9 files, 167 insertions and 13
deletions, SHA-256 starting `a708fe3fbeda1df5`.

- `ruff check scripts src`, `ruff format --check scripts src` (56 files) and
  `ty check scripts src`: all passed. `interrogate scripts src`: 100%.
- `.venv/bin/python -m pytest -q --numprocesses auto -p no:cacheprovider`: 211
  passed, including the example-config completeness test.
  `--doctest-modules src`: 28 passed, 1 skipped. Same counts as the baseline.
- Scratchpad `dev001_settings_check.py` (`resolve_config` with keywords and with
  each example file): 29 of 29 checks passed. Defaults are 2, 8, `high`, unset
  instructions, 32,000, unset model, 600 and `verify: null`; the default model
  is `anthropic:claude-opus-5-5` and the verifier is off. `advanced` keys are
  `extraction`, `models`, `page_breaks`, `provider_retries`, `survey`,
  `uploads`. `model` sets the step's model; `advanced.page_breaks.model`
  overrides it for this step only, with or without `model`. `verify: true` turns
  on `verify_page_breaks`; the override's `true` or `false` wins and changes no
  other step's switch. Blank instructions are unset. Out-of-range
  `check_retries`, `concurrent_breaks`, `max_output_tokens` and
  `request_timeout_seconds`, `effort: max`, malformed or unsupported models and
  the unknown key `concurrent_pages` each give one `advanced.page_breaks.<key>`
  line. Both example files hold the section in alphabetical order at its
  defaults and load.
- `scripts/generate_reference_docs.py`, then
  `prek exec prettier-markdown -- node scripts/format_markdown.mjs` (run outside
  the sandbox, which blocks prek's log in `~/.cache/prek`): only
  `reference/configuration.md` (the `advanced.page_breaks` section, the
  `page_breaks` entry and the `pages` note) and `reference/cli.md` (the
  `--model` help) changed. The formatter also reflowed this plan; the STANDARDS
  check passed.
- `python -m pydelity --help` shows the new `--model` help naming the three
  steps' defaults and both overrides.

**Implementation Notes**

- `--model`'s help now names page-break verification and
  `advanced.page_breaks.model`. `--no-pause`'s help ("without stopping after the
  survey") changes with the pause after page extraction in DEV-008.
- The step's settings are not read by any step yet; DEV-004 and DEV-006 use
  them, and the run records them in `run.json` through the config as before.

### DEV-002 — Verdict contract, verdict file and the step's names

`Status`: `DONE` `Depends On`: `DEV-001` `Acceptance`:
`AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017, AC-018, AC-027, AC-030`

**Goal**

Define what the judge answers, what the verifier answers and what a verdict file
holds, and add the step's names to the shared review, error and version modules.

**Affected Area**

CREATE `src/pydelity/verifying/__init__.py`,
`src/pydelity/verifying/schemas.py`; MODIFY `src/pydelity/review.py`,
`src/pydelity/schema_versions.py`, `src/pydelity/errors.py`.

**Expected Outcome**

- `verifying/schemas.py` holds `BreakVerdict`, `ContinuingPiece`,
  `ContinuingContainer`, `ContinuationMarker`, `Join`, `TextJoin`,
  `BreakProblem`, `BreakVerifierVerdict` (with `VerifierVerdict`'s invariants),
  `BreakVerification`, `BreakCheckResult`, `BreakHintResult`, `BreakContext`,
  `BreakPage`, `BreakSettings`, `BreakInputs` and `BreakFile`, with the fields
  of **Verdict contract**, **Verdict file** and **Verdict inputs and reuse** in
  alphabetical order. The answer models use plain types, enums, lists and
  objects with no patterns or bounds; `BreakFile` accepts unknown fields.
- `review.py`: `page_breaks` in `StepName`, `BreakCheckName` (`ids`,
  `continues`, `duplicates`, `joins`, `furniture`, `header_rows`, `repeats`,
  `markers`), `BreakHintName` (`start_markers`), both in `IssueName`;
  `ReviewIssue.page_index`'s docstring covers the break's earlier page.
- `schema_versions.py`: `BREAK_SCHEMA_VERSION = "1.0"`. `errors.py`:
  `PageBreakError` and the warning code `missing_page_files`.

**Self-Check**

The lint commands of DEV-001; pytest and doctests; a scratchpad script that
builds each answer model's JSON schema (no `pattern`, `minimum`, `maximum`,
`minLength` or `maxLength`), builds PydanticAI prompted and native output
schemas for `BreakVerdict` and `BreakVerifierVerdict`, rejects a verifier
verdict that breaks the invariants, and round-trips a `BreakFile` with an
unknown field.

Evidence, 2026-11-22, repo root, on `75e0ecd` (the user's DEV-001 commit) plus
the uncommitted DEV-002 changes. Assessed content:
`git diff HEAD -- src scripts examples docs` (7 files, 83 insertions and 41
deletions) with the new `src/pydelity/verifying/__init__.py` and `schemas.py`
(381 lines) appended, SHA-256 starting `e740c3e2f3a8867b`.

- `ruff check scripts src`, `ruff format --check scripts src` (58 files) and
  `ty check scripts src`: all passed. `interrogate scripts src`: 100%.
- `.venv/bin/python -m pytest -q --numprocesses auto -p no:cacheprovider`: 211
  passed. `--doctest-modules src`: 28 passed, 1 skipped.
- Scratchpad `dev002_schema_check.py`, run with `PYTHONPATH=src` (see the
  implementation notes): 34 of 34 checks passed. Every model in
  `verifying/schemas.py` lists its fields in alphabetical order.
  `BreakVerdict`'s and `BreakVerifierVerdict`'s JSON schemas hold no `pattern`,
  `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, `minLength`,
  `maxLength`, `minItems`, `maxItems` or `format`. Requests captured from
  PydanticAI 2.69.0 with a mock HTTP transport (no network): on OpenAI Responses
  both are sent as native `json_schema` output with `strict: true`, as
  `PageAnswer` is, with no bounds; on Anthropic both are prompted output, with
  the schema in the system prompt and no tools. The verifier's verdict accepts
  passed alone, failed with a problem and failed with a correction, and rejects
  passed with a problem, passed with a correction and failed without a problem.
  A full `BreakFile` (a `merge_split_row` piece with cell joins, a marker in a
  table cell, repeated items and header rows, a continuing container, a
  `header_rows` review issue with `step: "page_breaks"`) round-trips through
  JSON with an unknown top-level field, and a bad `judgment` or issue `step` is
  rejected.
- `scripts/generate_reference_docs.py` and the Markdown formatter (outside the
  sandbox): `reference/run-json.md` lists the new check and hint names, the
  `page_breaks` step, the `page_index` note and `missing_page_files`;
  `reference/cli.md` the exit code 1 text; `page-json.md` and
  `pdf-survey-json.md` the new check names through the shared `IssueName`. The
  STANDARDS check passed.

**Implementation Notes**

- The venv's editable install is a setuptools link tree under
  `build/__editable__.pydelity-0.2.0-py3-none-any/`, with one symlink per file,
  so `pydelity.verifying` does not import from the venv until the package is
  reinstalled. Scratch checks use `PYTHONPATH=src` until then. The package must
  be reinstalled (`just install`, or
  `uv sync --locked --reinstall-package pydelity`) before DEV-008, when the
  runner imports `verifying` and the test suite with it.
- `CheckFailure.details` and `ReviewIssue.details` docstrings gain the
  page-break forms in DEV-003, which defines them.

### DEV-003 — Checks and the start-marker hint

`Status`: `PENDING` `Depends On`: `DEV-002` `Acceptance`:
`AC-013, AC-014, AC-016, AC-017, AC-019, AC-021, AC-022, AC-023, AC-024, AC-025, AC-026`

**Goal**

Decide in code what code can decide about a verdict, and compare it with the
survey's start markers without ever sending that difference back.

**Affected Area**

CREATE `src/pydelity/verifying/validators.py`.

**Expected Outcome**

- `CHECKS` in the order `ids`, `continues`, `duplicates`, `joins`, `furniture`,
  `header_rows`, `repeats`, `markers`, and `run_checks(verdict, earlier, later)`
  giving `CheckFailure`s whose `details` name the item, entry, container or cell
  and whose `page_index` is the page it is on, as **Checks and hints** defines.
- Text matching through `comparison_form` and `trigrams` with the 0.8 Dice
  bound, the containment rules of `repeats` and `markers`, and both-empty header
  rows matching.
- `HINTS` (`start_markers`) and `compare_with_hints`, skipping markers with an
  empty comparison form; difference messages say which marker the start begins
  with and never say what to change.
- `retry_message` built from check failures only, and the helpers that turn
  failures into `BreakCheckResult`s, differences into `BreakHintResult`s, and
  both plus verifier problems into review issues in the order of **Review
  issues**, with `step: "page_breaks"`, the earlier page in `page_index`, the
  item when it is on either page, and both pages in the message.
- No check raises on the faults **Robustness** lists; missing content fails the
  check that needs it.

**Self-Check**

The lint commands; pytest and doctests; a scratchpad script with hand-built page
files and verdicts that makes each check pass and fail at least once, runs every
**Robustness** fault without an exception, matches repeated titles and header
rows in Latin, Chinese and Arabic text, and confirms `retry_message` never holds
a hint difference.

### DEV-004 — Prompts, agents and requests

`Status`: `PENDING` `Depends On`: `DEV-003` `Acceptance`:
`AC-009, AC-019, AC-020, AC-022, AC-023, AC-025, AC-029, AC-038`

**Goal**

Build the judge's and the verifier's requests and agents, and map unusable
answers to `PageBreakError`.

**Affected Area**

CREATE `src/pydelity/verifying/prompts.py`, `src/pydelity/verifying/agents.py`,
`src/pydelity/verifying/llm.py`. `providers/ledger_model.py` stays as it is:
`for_page` with the break's earlier page gives the ledger line the design asks
for.

**Expected Outcome**

- `prompts.py`: `PROMPT_VERSION = 1`, `judge_break` and `verify_break` returning
  `PromptPair`s with the instructions of **Judge request** and **Verifier
  request** in their order, the hints heading with the survey's continuation
  notes and start markers (`none` when absent) and
  `advanced.page_breaks.instructions` last when set. No text names a language,
  document type or domain concept, or assumes a direction.
- The user content: page N's text part (first line
  `Page break between page indexes <i> and <i+1> (pages <i+1> and <i+2> of <n>)`),
  its upright image, page N+1's text part, its image, then the verifier's review
  part (`The page-break verdict to review:`, the failing checks, the hint
  differences) and a cache point. Each page text holds its index and number, the
  turn applied, the writing direction as the survey found it, `column_order`,
  and containers and items as compact JSON, one per line, with grid boxes from
  `points_box_to_grid` and numbered rows and cells. No page file `inputs`,
  `checks`, `hints` or `issues`, no PDF and no text layer.
- `agents.py`: the judge agent (`BreakVerdict`, retries only on `run_checks`
  failures) and the verifier agent (`BreakVerifierVerdict`, the correction retry
  message), as page extraction's agents are built.
- `llm.py`: `JUDGE`, `VERIFIER`, the step's `StepModel`, `BreakInput`,
  `ask_judge`, `ask_verifier`, the request settings with Anthropic instruction
  caching, and the error mapping to `PageBreakError` with the design's message
  forms.

**Self-Check**

The lint commands; pytest and doctests; a scratchpad script with PydanticAI's
`FunctionModel` that checks the content order, the hints heading and the
instructions' place, that a check failure is sent back within `check_retries`
and a hint difference never is, that the last failing verdict is accepted, that
a failing correction is sent back, and that a refusal, used-up output tokens and
no usable answer each raise `PageBreakError` naming the break and the agent; a
read of the prompt text for language, document-type and direction words.

### DEV-005 — Stand-in routing and canned break answers

`Status`: `PENDING` `Depends On`: `DEV-004` `Acceptance`: `AC-040, AC-042`

**Goal**

Let the stand-in provider answer page-break requests, so self-checks, the smoke
test and Tester's tests run the step without a model.

**Affected Area**

MODIFY `tests/fixtures/mock_providers.py`; CREATE
`tests/fixtures/break_answers/irs_form_1040a_1965_scan.json`.

**Expected Outcome**

- A request whose text holds `Page break between page indexes <i>` gets the
  judge's canned answer for break `<i>`, or the verifier's when it holds
  `The page-break verdict to review:`, whatever order concurrent requests arrive
  in, for Anthropic Messages and OpenAI Responses. Page and survey routing stay
  as they are.
- `MockProviders` takes break answers beside page answers, and the command line
  takes `--break-answers <file>`.
- The canned file holds a judge and a verifier answer for the 1965 scan's one
  break, citing item IDs from its canned page answers.

**Self-Check**

The lint commands on `tests/fixtures`; the existing tests; a scratchpad script
that sends `ask_judge` and `ask_verifier` requests for both providers through
the stand-in and gets the canned answers, with page requests still routed as
before.

### DEV-006 — The page-break step

`Status`: `PENDING` `Depends On`: `DEV-005` `Acceptance`:
`AC-002, AC-011, AC-019, AC-021, AC-026, AC-027, AC-029, AC-030, AC-031, AC-035, AC-036, AC-037, AC-038`

**Goal**

Judge every break from the current page files, reuse valid verdicts, and write
each verdict file atomically.

**Affected Area**

CREATE `src/pydelity/verifying/verification.py`.

**Expected Outcome**

- Current page files with the SHA-256 of their bytes, `BreakInputs` and the
  break fingerprint, `break_file_path`, `BREAKS_FOLDER_NAME` (`page_breaks`) and
  file names `<NNNN>-<NNNN>.json`.
- `plan_breaks`: computes every break's inputs, loads each verdict file, warns
  `damaged_output` on damage, reuses a valid matching file when `overwrite` is
  off and it is `no_content`, holds a verification or the verifier is off, logs
  the counts unless quiet, and logs an info line for a file passed over only for
  lacking a verification.
- `verify_breaks`: removes temporary files in `page_breaks/`, judges at most
  `concurrent_breaks` breaks at once on one `PdfWorker`, writes a `no_content`
  verdict without a request when a page has no item outside role `artifact`,
  otherwise renders both upright images, asks the judge, then the verifier when
  on, keeps the verdict as **Verdict application** says, computes hints and
  issues, writes the file atomically, reports it to the caller, and logs the
  break's line. The first failure cancels the other breaks and is raised;
  verdict files already written stay.

**Self-Check**

The lint commands; pytest and doctests; a scratchpad script that runs the step
through the stand-in on the 1965 scan and on hand-built page files (a blank
page, two breaks sharing a page): verdict files are written and load; a rerun
reuses them; changing one page file's bytes re-judges its two breaks only;
`overwrite` re-judges all; the verifier on re-judges unverified `model`
verdicts; a damaged file warns and is judged again; an injected failure cancels
the rest, keeps the written files and raises.

### DEV-007 — Page-break verification in the estimate and the ledger

`Status`: `PENDING` `Depends On`: `DEV-006` `Acceptance`:
`AC-032, AC-033, AC-034`

**Goal**

Price the breaks a run will judge, with the verifier only when it runs, and
document the ledger's break lines.

**Affected Area**

MODIFY `src/pydelity/costs/budget.py` (`BreakRequestSize`,
`estimate_page_breaks`, `TYPICAL_BREAK_OUTPUT_TOKENS`,
`TYPICAL_BREAK_VERDICT_OUTPUT_TOKENS`), `src/pydelity/costs/schemas.py`
(`StepEstimate.breaks`, `LedgerEntry.agent` and `page_index` docstrings),
`src/pydelity/verifying/verification.py` (request sizes, measured and
allowance), and the existing `StepEstimate` callers (`breaks=None`).

**Expected Outcome**

- `estimate_page_breaks(config, breaks)` follows **Cost estimate**: judge input
  from the measured characters plus two images of the step's model's profile,
  typical outputs of 4,000 and 3,000 tokens, the maximum over every attempt with
  `max_output_tokens`, `requests_max`, `reused` when nothing is to be judged,
  `no_content` breaks left out.
- Request sizes: measured by building both prompts for a break whose page files
  are current and unchanged; else the allowance (instructions measured from the
  survey when it exists, else a fixed allowance, plus per page a fixed allowance
  and twice its text-layer characters). The allowance constants are rounded up
  from prompts built from page files of the local real runs under
  `pydelity-output/` (git-ignored, read only) and the canned answers.

**Self-Check**

The lint commands; pytest and doctests; a scratchpad script that compares
`estimate_page_breaks` with hand-computed figures for verifier off and on,
reused and `no_content` breaks, and that prints the measured prompt sizes behind
the allowance constants.

### DEV-008 — Page-break verification in runs

`Status`: `PENDING` `Depends On`: `DEV-007` `Acceptance`:
`AC-001, AC-002, AC-003, AC-004, AC-005, AC-007, AC-031, AC-032, AC-033, AC-034, AC-038`

**Goal**

Run page-break verification after page extraction, with the pause, the skips,
the single estimate, the run record, the review list and `load`.

**Affected Area**

MODIFY `src/pydelity/pipeline/runner.py`, `src/pydelity/pipeline/schemas.py`.

**Expected Outcome**

- `_steps`: survey, page extraction, page-break verification, as decision 10
  orders them: a one-page PDF skips the step with an info line; a page without a
  current page file skips it with the `missing_page_files` warning and the run
  completes; a page extraction that wrote a page file with `pause` on skips it
  and the run pauses; every step not reached is `skipped`.
- The estimate, the question, the `max_cost` check and the API-key checks happen
  once, before the run's first request, in whichever of the three steps spends
  first, and cover the breaks **Cost estimate** names. `run_estimate` covers
  them too.
- `run.json`: step `page_breaks` with `breaks` (`BreakCounts`: `total`,
  `judged`, `reused`) and outputs `page_breaks/`; `StepRecord.breaks` required
  and `null` for other steps; `RunResult.breaks` required, in break order.
- The review list adds each break's issues after the pages'. The summary shows
  the step line, break review lines, the pause message after page extraction and
  the `--overwrite` note; estimate lines name steps by title.
- `load_run` returns the verdicts whose PDF hash and both page-file hashes match
  the page files it returns, and raises `OutputError` on an invalid verdict
  file.

**Self-Check**

The lint commands; pytest and doctests, with the tests of replaced contracts
listed for Tester (see Plan Notes); a scratchpad script running `run_pipeline`
through the stand-in on the 1965 scan: pause after new page files, then a second
run that judges the break; `pause=False` in one run; `pages` narrowed with and
without the other pages current; a one-page PDF; spend control with the estimate
in each of the three steps; `load` after each.

### DEV-009 — Python functions and the CLI

`Status`: `PENDING` `Depends On`: `DEV-008` `Acceptance`:
`AC-001, AC-006, AC-031, AC-038`

**Goal**

Give Python callers `verify_breaks` and `averify_breaks`, export the new types,
and make the CLI report page-break errors and summaries as the other steps'.

**Affected Area**

MODIFY `src/pydelity/pipeline/runner.py` (the runner function behind
`verify_breaks`), `src/pydelity/api.py`, `src/pydelity/__init__.py`,
`src/pydelity/cli.py`.

**Expected Outcome**

- `verify_breaks(pdf=None, *, allow_over_max_cost=False, config=None, **settings)`
  and `averify_breaks` run the survey and page extraction of the selected pages
  when needed, then page-break verification, never pause, write no `run.json`
  and no report, and return the verdicts in break order (none for a one-page PDF
  or a missing page file, with the warning).
- `run`, `arun`, `estimate` and `aestimate` docstrings describe the new step and
  the pause; `__all__` gains `verify_breaks`, `averify_breaks`, `BreakFile` and
  `PageBreakError`.
- The CLI maps `PageBreakError` to exit code 1 and shows the error; the CLI and
  `run()` record the same steps.

**Self-Check**

The lint commands; pytest and doctests; a scratchpad script calling
`verify_breaks` and `averify_breaks` through the stand-in (fresh folder, reuse,
narrowed `pages`, one-page PDF); the CLI against the stand-in with `-np`, a
paused run, and an injected page-break failure (exit 1).

### DEV-010 — Page breaks in the HTML report

`Status`: `PENDING` `Depends On`: `DEV-008` `Acceptance`: `AC-039`

**Goal**

Show each verdict beside its two pages so a person can check it.

**Affected Area**

MODIFY `src/pydelity/report/html.py`, its stylesheet, and the runner's report
inputs.

**Expected Outcome**

- `ReportInputs` gains the verdicts and the page files they were judged from.
- A "Page breaks" section after the pages, one card per verdict (anchor
  `break-<NNNN>`, heading `Pages <n> and <n+1>`) with both page images from
  `report/pages/`, boxes for each piece's end and start, repeated items, marker
  items and continuing containers, and the details of decision 14, including the
  verifier's outcome, `no verifier`, or no request for a `no_content` verdict.
- `_STEP_TITLES` gains `page_breaks`; review entries for a break link to its
  card; all PDF, settings and model text is escaped; no section without
  verdicts.

**Self-Check**

The lint commands; pytest and doctests; a report generated from a stand-in run
and from hand-built verdicts with HTML-like text, checked for anchors, links,
boxes and escaping, and viewed in the in-app browser.

### DEV-011 — Smoke test, package description and reference pages

`Status`: `PENDING` `Depends On`: `DEV-009, DEV-010` `Acceptance`:
`AC-042, AC-044, AC-047`

**Goal**

Run the new step from the built wheel, describe the release, and generate the
reference pages for the new contracts.

**Affected Area**

MODIFY `scripts/smoke_installed_wheel.py`, `scripts/generate_reference_docs.py`,
`pyproject.toml` (description); regenerate `docs/src/content/docs/reference/`,
adding `page-break-json.md` and `page-break-checks.md`.

**Expected Outcome**

- The smoke script runs the CLI and the Python API through the three steps
  without a pause against the stand-in on the 1965 scan, with its expected
  requests updated, and checks that the folder loads with one verdict.
- `pyproject.toml`'s description says pydelity surveys a PDF, extracts its pages
  and verifies its page breaks, with an optional verifier for each step.
- The reference pages cover `advanced.page_breaks`, `verify_breaks`,
  `averify_breaks`, `BreakFile` and its parts, the checks and the hint apart,
  `StepRecord.breaks`, `RunResult.breaks`, `StepEstimate.breaks`, the ledger
  docstrings and the new cost constants, and the staleness check passes.

**Self-Check**

The lint commands; pytest and doctests; `scripts/generate_reference_docs.py`
twice with no diff the second time, and the Markdown formatter; the smoke script
from a built wheel where the sandbox allows it, otherwise its steps run from the
source tree with the limitation recorded.

---

## Plan Notes

- Project references loaded: `NONE` (`.standards/project-references/` does not
  exist).
- Names for the user's approval, all from the design unless marked: step name
  `page_breaks`; settings section `advanced.page_breaks` and its keys
  `check_retries`, `concurrent_breaks`, `effort`, `instructions`,
  `max_output_tokens`, `model`, `request_timeout_seconds`, `verify`;
  `PageBreaksConfig`, `Config.page_breaks_model`, `Config.verify_page_breaks`,
  `DEFAULT_PAGE_BREAKS_MODEL` (DEV-001); package `verifying/` with
  `verification.py`; output folder `page_breaks/` with files
  `<NNNN>-<NNNN>.json`; `BREAK_SCHEMA_VERSION`; models and fields of **Verdict
  contract**, **Verdict file** and **Verdict inputs and reuse**; check names
  `ids`, `continues`, `duplicates`, `joins`, `furniture`, `header_rows`,
  `repeats`, `markers` and hint `start_markers`; `PageBreakError`; warning code
  `missing_page_files` (DEV-002, DEV-003); ledger agents `judge` and `verifier`
  (DEV-004); `--break-answers` and `tests/fixtures/break_answers/` (DEV-005,
  Developer's proposal); `BreakRequestSize`, `estimate_page_breaks`,
  `StepEstimate.breaks`, `TYPICAL_BREAK_OUTPUT_TOKENS`,
  `TYPICAL_BREAK_VERDICT_OUTPUT_TOKENS` (DEV-007); `BreakCounts`,
  `StepRecord.breaks`, `RunResult.breaks` (DEV-008); `verify_breaks`,
  `averify_breaks` (DEV-009); reference pages `page-break-json.md` and
  `page-break-checks.md` (DEV-011, Developer's proposal, following
  `page-json.md` and `extraction-checks.md`). The user approved the plan with
  these names on 2026-11-22, after confirming the step's default model and
  effort.
- Order: DEV-010 depends only on DEV-008 and may run before DEV-009.
- Tests are Tester's. Tests of a replaced contract fail until Tester updates
  them: from DEV-007, code building `StepEstimate` without `breaks`; from
  DEV-008, runs that now pause after page extraction or record a third step, and
  code building `StepRecord` or `RunResult` without `breaks`. Each step lists
  the failing tests in its evidence.
- Self-checks use `.venv/bin` tools directly, because uv cannot write its cache
  in the sandbox, and use the stand-in or PydanticAI's test models. No real
  model run, download or new dependency is planned; any would need the user's
  go-ahead.
- The user makes the commits.

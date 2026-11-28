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
  `Build page-break verification (step 3) on top of 0.2.0: one verdict per break between consecutive pages, judged from both whole pages, naming the continuing pieces by item ID with their join rules, repeated header rows, repeated items, continuation markers and continuing containers; code checks and the survey's start-marker hint; an opt-in verifier; the step's settings, pause, estimate, spend control, reuse, review list, report, Python functions, smoke test and reference pages, ready for release 0.3.0. Rework of 2026-11-28 after the real Anthropic runs (DEV-012 to DEV-016): new_entry from a text item, a repeat cell join, the unfinished-text rule, a narrower start-marker hint, and a verifier that judges each break a second time without seeing the first, compared in code.`

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

`Status`: `DONE` `Depends On`: `DEV-002` `Acceptance`:
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

Evidence, 2026-11-22, repo root, on `10a8d7e` (the user's DEV-002 commit) plus
the uncommitted DEV-003 changes. Assessed content:
`git diff HEAD -- src scripts examples docs` (4 files, 29 insertions and 16
deletions) with the new `src/pydelity/verifying/validators.py` (2,068 lines)
appended, SHA-256 starting `5ba61e33cd0af3a7`.

- `ruff check scripts src tests`, `ruff format --check scripts src tests` and
  `ty check scripts src tests`: all passed. `interrogate scripts src tests`:
  100%.
- `.venv/bin/pytest --numprocesses auto`: 211 passed. `--doctest-modules src`:
  33 passed, 1 skipped (5 new examples in `verifying/validators.py`).
- Scratchpad `dev003_check.py`, run with `PYTHONPATH=src` on page files built
  from a local page file's structure with hand-made items: 73 of 73 checks
  passed. A verdict with `continue_text` (text and code), `continue_entry`,
  `merge_split_row`, two `append_rows`, repeated items, markers in an item and a
  table cell and a continuing container passes all eight checks, as do a
  `new_entry` verdict and an empty one. Each check fails at least once with the
  failures the design names: `ids` (missing end, entry of another item, missing
  repeated item, six bad marker places including negative positions, missing
  containers on both pages, each on its own page), `continues` (both
  directions), `duplicates` (item, entry, containers on each page, repeated item
  that starts a piece), `joins` (20 cases covering kinds, same kind, text joins,
  the fields each join sets or leaves null, entry ends, header-row bounds, cell
  join count and `newline`, a figure end), `furniture` (both ends),
  `header_rows` (no match, match within the first n + h rows only, empty rows,
  too few rows), `repeats` (no match, with text-less and missing items skipped,
  matches on an entry and a joined row) and `markers` (item, cell and a
  text-less item, with a symbol-only marker passing). Repeated titles and header
  rows match in Latin, Chinese and Arabic. The `start_markers` hint finds starts
  in a text item, a list's first entry and a table's first row after the header
  rows, skips a marker whose comparison form is empty, names the marker and says
  nothing about what to change. `retry_message` holds no `start_markers` text.
  Every **Robustness** fault (table items with `table: null`, lists with
  `entries: null`, text items with `text: null`, a table with no rows and
  negative `header_rows`, negative counts, a `column_order` that does not fit)
  runs through all checks and the hint without an exception, and missing content
  fails `joins`, `header_rows` or `ids`. Review issues list checks, then hints,
  then verifier problems, leave hints out when the verifier passed the verdict
  or its correction was kept, leave problems out when the correction was kept,
  and carry `step: "page_breaks"`, the earlier page, `pages 4 and 5:` in the
  message, and an `item_id` (a container ID included) only when one of the pages
  has it.
- `scripts/generate_reference_docs.py` and the Markdown formatter (outside the
  sandbox): `page-json.md`, `pdf-survey-json.md` and `run-json.md` carry the new
  `details` forms. Markdownlint passed.

**Implementation Notes**

- Failure messages name pieces as `piece 2 (p0003-007 to p0004-001)` and the
  pages as the earlier and later page, so they read the same to the model and in
  the review list, where the issue adds `pages 4 and 5:`.
- A failure about a piece's fields rather than one end (`joins` field rules,
  `continue_entry` with no entry) has `page_index` `null` and names the earlier
  item in `details`. `continues` failures have `page_index` `null` and empty
  `details`.
- `markers` and `repeats` leave a marker or repeated item whose item, row or
  cell does not exist to `ids`, so one fault is reported once. `header_rows` and
  `joins` both report a missing table, since each needs it.
- For `start_markers`, a list item's start without `later_entry` is its first
  entry, since list items have no `text`. A `new_entry` or `append_rows` start
  that begins with a start marker is reported like any other, as the design
  says.

### DEV-004 — Prompts, agents and requests

`Status`: `DONE` `Depends On`: `DEV-003` `Acceptance`:
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

Evidence, 2026-11-22, repo root, on `06471da` (the user's DEV-003 commit) plus
the uncommitted DEV-004 changes. Assessed content: the new
`src/pydelity/verifying/agents.py` (241 lines), `llm.py` (374 lines) and
`prompts.py` (572 lines), with no other change under `src`, `scripts`,
`examples` or `docs`, SHA-256 starting `34393b4b52d3e25e`.

- `ruff check scripts src tests`, `ruff format --check` and
  `ty check scripts src tests`: all passed. `interrogate scripts src tests`:
  100%.
- `.venv/bin/pytest --numprocesses auto`: 211 passed. `--doctest-modules src`:
  33 passed, 1 skipped. The reference-page generator and the Markdown formatter
  change no page.
- Scratchpad `dev004_check.py`, run with `PYTHONPATH=src` on PydanticAI 2.69.0's
  `FunctionModel` (native output, no network, no paid request) with a stand-in
  for `LedgerModel.for_page`: 38 of 38 checks passed. The judge's content is the
  earlier page's text, its image, the later page's text, its image and a cache
  point. The first line is
  `Page break between page indexes 3 and 4 (pages 4 and 5 of 10)`, the second
  text starts `The page after the break: page index 4, page 5.`, and neither
  holds `Page index <i> (`, `The extraction to review:`,
  `The survey answer to review:` or any page-file `inputs`, `checks`, `hints`,
  `issues` or fingerprint. Each page text states the turn, the survey's writing
  direction and a set column order, and lists containers and items as JSON lines
  with grid boxes, numbered rows and cells, spans other than 1, and missing
  content as it is (`"table": null`, `"entries": null`). The judge's
  instructions hold the eleven parts of **Judge request** in order, the hints
  say `none` when the survey gave none, the user's instructions come last only
  when set, and the instructions are the same for every break. A verdict that
  passes the checks and differs from a hint gets one request. A failing verdict
  is sent back with `retry_message` (no `start_markers` text, also when the
  verdict fails a check and a hint), and the last failing verdict is kept, with
  three requests at `check_retries` 2 and one at 0. The verifier's content
  repeats the judge's page texts, then the review text
  (`The page-break verdict to review:`, the checks with `none`, the hint
  differences) and a cache point, and its instructions put the review list, the
  verdict rules, the judge's rules, the hints and the user's instructions in
  order. A failing correction is sent back with "Your corrected verdict does not
  pass every check. Give the whole verdict again, with the correction fixed."
  followed by `retry_message`, and a correction still failing at the last
  attempt is accepted with its failures. A refusal, used-up output tokens and an
  unusable answer raise `PageBreakError` with the design's message forms for the
  judge and the verifier. Requests are recorded for the agents `judge` and
  `verifier` on the earlier page. Anthropic requests cache the instructions, and
  OpenAI requests set nothing.
- The instructions of both prompts, without the survey's hints, hold none of 31
  language, script, direction and document-type words checked (such as
  "English", "Arabic", "left to right", "chapter", "article", "report", "law",
  "paragraph").

**Implementation Notes**

- A page-break request has two or three text parts, so `prompts.py` returns a
  `BreakPrompts` (instructions, `earlier_text`, `later_text`, `review_text`)
  rather than a `PromptPair`. `verify_break` takes the judge's `BreakPrompts`
  and repeats their page texts, which keeps it to five arguments.
- `llm.py` names the answers `JudgeAnswer` (verdict, attempts, check failures)
  and `VerifierAnswer` (the verifier's answer, attempts, correction failures),
  as page extraction's `ModelPage` and `ModelVerdict`. `_model_settings` is
  repeated from page extraction rather than shared, to leave that module as it
  is.
- Each item line lists the content fields its kind fills, also when null, and
  any other content field that is set. Figures give their description and text,
  and not their crop file.
- PydanticAI 2.69 sends an output validator's `ModelRetry` text inside a user
  prompt part wrapped in `<pyai:retry_feedback>`, not as a retry part. The
  stand-in in DEV-005 routes on the request's first user content, which this
  does not change.

### DEV-005 — Stand-in routing and canned break answers

`Status`: `DONE` `Depends On`: `DEV-004` `Acceptance`: `AC-040, AC-042`

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

Evidence, 2026-11-22, repo root, on `fc5cb0c` (the user's DEV-004 commit) plus
the uncommitted DEV-005 changes. Assessed content: the changed
`tests/fixtures/mock_providers.py` (1,335 lines) and the new
`tests/fixtures/break_answers/irs_form_1040a_1965_scan.json` (15 lines), with no
change under `src`, `scripts`, `examples` or `docs`, SHA-256 of the two files in
that order starting `cecb1cd647a7dfc4`.

- `ruff check tests/fixtures`, `ruff format --check tests/fixtures` and
  `ty check tests`: all passed. `interrogate tests`: 100%.
- `.venv/bin/pytest --numprocesses auto`: 211 passed.
- `python -m tests.fixtures.mock_providers --help` lists `--break-answers`.
- Scratchpad `dev005_check.py`, run with `PYTHONPATH=src:.` against the stand-in
  (loopback only, no paid request): 40 of 40 checks passed. For
  `anthropic:claude-opus-5-5` and `openai:gpt-5.5`, a model from `build_model`
  sends `ask_judge` and `ask_verifier` for break 0 of the 1965 scan's canned
  pages. Each returns the canned answer in one attempt with no check failures,
  and the stand-in records `judge` then `verifier` with break index 0, no page
  index and status 200. Through each SDK directly, sent in reverse order (the
  break's verifier before its judge, page 1's verifier before its extractor,
  then page 0's extractor and a survey request), every request gets its canned
  answer and is recorded with the right agent, break index and page index. A
  break with no answer gets HTTP 400 naming
  `judge answer for the break after page index 5`. Break answers alone start the
  stand-in, and no answers at all raise `ValueError`.

**Implementation Notes**

- `_request_agent` became `_request_target`, which returns a small `_Target`
  (agent, break index, page index). Break requests are matched first, because
  their item lines could hold any text. `RecordedRequest` gains `break_index`.
- Page and break answers share `_next_answer`, and the two file readers share
  `_read_answers_by_index`, so `read_page_answers` keeps its name for
  `tests/conftest.py`.
- The `--answer` help and the `answers` parameter now say the survey answer goes
  to requests that name no page or break.

### DEV-006 — The page-break step

`Status`: `DONE` `Depends On`: `DEV-005` `Acceptance`:
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

Evidence, 2026-11-22, repo root, on `1da7f13` (the user's DEV-005 commit) plus
the uncommitted DEV-006 changes. Assessed content: the new
`src/pydelity/verifying/verification.py` (1,093 lines, SHA-256 starting
`caabecda8a3d9637`), with no other change under `src`, `scripts`, `examples` or
`docs`.

- `ruff check scripts src tests`, `ruff format --check` and
  `ty check scripts src tests`: all passed. `interrogate scripts src tests`:
  100%.
- `.venv/bin/pytest --numprocesses auto`: 211 passed. `--doctest-modules src`:
  33 passed, 1 skipped. The reference-page generator followed by the Markdown
  formatter changes no page.
- Scratchpad `dev006_check.py`, run with `PYTHONPATH=src:.` against the stand-in
  (loopback only, no paid request): 51 of 51 checks passed.
  - The 1965 scan, surveyed and extracted with `aextract`: both page files are
    current, each with the hash of its bytes; with `overwrite`, none is current
    unless extracted in this run. `plan_breaks` logs
    `Page-break verification: 1 break, 0 reused, 1 to judge`. `verify_breaks`
    sends one judge request and writes `page_breaks/0000-0001.json` with the
    canned verdict, `judgment: "model"`, the eight checks passed after 1
    attempt, `start_markers` with no differences, no issues, both page hashes,
    the PDF hash and the plan's fingerprint. It writes one ledger line (`judge`,
    page index 0) and logs
    `Break after page 1 (pages 1 and 2): nothing continues, 0 review issues, no verifier; $0.02 for 1 request`.
    A rerun reuses it with no request. With the verifier on, the break is judged
    again with the info line and a verifier request. The file records the
    verifier's pass, and with the verifier off it is reused.
  - Eight hand-built page files on an eight-page PDF (page 3 blank, page 6 page
    furniture only): 7 breaks, with judge requests for breaks 0, 3 and 6 only,
    and `no_content` verdicts for the four breaks touching pages 3 and 6. Those
    verdicts have every check passed after 0 attempts, no hint differences, no
    issues and no verification, and log lines such as
    `Break after page 2 (pages 2 and 3): nothing continues, no request, page 3 has no content items`.
    A rerun reuses all 7. New bytes for page index 3 re-judge only breaks 2
    and 3. `overwrite` re-judges all 7. The verifier on re-judges the three
    `model` verdicts and reuses the `no_content` ones. Invalid JSON and schema
    version `2.0` each give a `damaged_output` warning and the break is judged
    again. A leftover temporary file is removed.
  - Failures: with `concurrent_breaks` 1 and no canned answer for break 3, the
    `no_content` verdicts and break 0 are written, `ProviderError` is raised,
    break 6 gets no request, breaks 3 and 6 keep their files, and no temporary
    file is left. With a judge stand-in that fails break 3 while breaks 0 and 6
    wait, `PageBreakError` is raised as it is within 3 seconds, breaks 0 and 6
    are canceled and keep their files, and the `no_content` verdicts are still
    written.

**Implementation Notes**

- `current_pages(config, extracted, output_folder, survey)` returns the current
  page files by page index, each read from its bytes with their hash, and the
  caller finds the pages missing from it. A page file that stops validating
  between the plan and the read counts as missing.
- `_break_inputs` and `_break_fingerprint` stay private, since only this module
  uses them (DEV-007's request sizes live here too).
- `no_content` verdicts are written before the concurrent part, without the PDF
  worker. The self-check found that a waiting `no_content` break, which never
  awaits, could be written after another break had failed. Their checks and
  hints come from running `run_checks` and `compare_with_hints` on the empty
  verdict, so the file has the same shape as a `model` verdict.
- Each break renders both its page images, so a page shared by two breaks is
  rendered twice. The design allows keeping an image for both breaks, which can
  be added if rendering shows up in run times.
- `verify_breaks` takes the step's model even when every break to judge is
  `no_content`. DEV-008 builds the model only when a break is to be judged, as
  for pages, which needs the provider's API key in that case.

### DEV-007 — Page-break verification in the estimate and the ledger

`Status`: `DONE` `Depends On`: `DEV-006` `Acceptance`: `AC-032, AC-033, AC-034`

**Goal**

Price the breaks a run will judge, with the verifier only when it runs, and
document the ledger's break lines.

**Affected Area**

MODIFY `src/pydelity/costs/budget.py` (`BreakRequestSize`,
`estimate_page_breaks`, `TYPICAL_BREAK_OUTPUT_TOKENS`,
`TYPICAL_BREAK_VERDICT_OUTPUT_TOKENS`), `src/pydelity/costs/schemas.py`
(`StepEstimate.breaks`, `LedgerEntry.agent` and `page_index` docstrings),
`src/pydelity/verifying/verification.py` (request sizes, measured and
allowance), `src/pydelity/verifying/prompts.py` (`judge_instructions`, split out
of `judge_break`), the existing `StepEstimate` callers (`breaks=None`), and the
regenerated `docs/src/content/docs/reference/cost-jsonl.md`.

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

Evidence, 2026-11-22, repo root, on `09cad96` (the user's DEV-006 commit) plus
the uncommitted DEV-007 changes. Assessed content, lines and SHA-256 prefix:
`src/pydelity/costs/budget.py` (809, `64128e6fd55a2243`),
`src/pydelity/costs/schemas.py` (178, `d3b6d87bc8d0516b`),
`src/pydelity/verifying/prompts.py` (589, `979c746d39dc4896`),
`src/pydelity/verifying/verification.py` (1,244, `5e70c82ba3d2aa17`) and
`docs/src/content/docs/reference/cost-jsonl.md` (121, `d99b02a4f9e78248`), with
no other change under `src`, `scripts`, `examples` or `docs`.

- `ruff check scripts src tests`, `ruff format --check` and
  `ty check scripts src tests`: all passed. `interrogate scripts src tests`:
  100%.
- `.venv/bin/pytest --numprocesses auto`: 211 passed. No existing test builds
  `StepEstimate`, so none fails from the new required `breaks`.
  `--doctest-modules src`: 33 passed, 1 skipped. The reference-page generator
  followed by the Markdown formatter changes only `cost-jsonl.md`, which now
  shows `StepEstimate.breaks`, the ledger's `judge` agent and break
  `page_index`, and the two new constants.
- Scratchpad `measure.py` (read only, `PYTHONPATH=src`) built the prompts from
  the 26 local runs under `pydelity-output/` whose surveys load. The judge's
  instructions and verdict format measure 10,820 to 13,967 characters, and the
  verifier's instructions, review text and answer format up to 17,143. The
  allowances are 14,000 and 18,000. Page details minus twice the text-layer
  characters, over 1,792 page texts, have a median of 1,400, a 90th percentile
  of 3,323 and a maximum of 17,768 (two scanned pages of `imnci`). Fitted so no
  run's breaks together come out smaller than measured, the real runs need at
  most 2,708 per page (`imnci`, 93 breaks), and the canned 1965 scan, whose form
  pages have no text layer, needs 5,353. The page allowance is 6,000, which puts
  the real runs' totals at 1.25 to 1.63 times measured and the scan's at 1.06.
- Scratchpad `dev007_check.py` (`PYTHONPATH=src:.`, prices set at $2 and $10 per
  million input and output tokens): 25 of 25 checks passed.
  - `estimate_page_breaks` equals the hand-computed expected and maximum costs
    for `anthropic:claude-opus-5-5` (4,784 image tokens) and `openai:gpt-5.5`
    (12,000), with the verifier off and on. It gives `breaks` 2, `pages` null,
    `requests_max` 6 or 12, and `verifier` as set. It also matches with
    `max_output_tokens` 2,500 and one retry (`requests_max` 4).
    `advanced.page_breaks.verify: false` wins over `verify`. No breaks gives a
    reused, free step. An unknown model gives no figures. `estimate_run` adds
    the step and counts nothing for a reused one.
  - `request_sizes` on DEV-006's eight hand-built pages leaves out the four
    `no_content` breaks and equals the instructions, page texts and formats of
    `judge_break` and `verify_break` with an empty verdict.
  - `request_sizes_before_pages` gives 14,000 or 18,000 plus the user's
    instructions before the survey, the measured instructions with it, and each
    page 6,000 plus twice its text-layer characters. On the 1965 scan it gives
    26,000 before the survey and 22,528 with it, against 21,233 measured.

**Implementation Notes**

- `judge_instructions(context)` is split out of `judge_break` with its output
  unchanged, so the allowance can measure the judge's instructions before any
  page file exists. The verifier's are measured by calling `verify_break` with
  empty page texts.
- The allowance adds the user's `instructions` before the survey, since they are
  known then and can be long.
- `request_sizes` leaves out `no_content` breaks itself. The caller passes the
  breaks to judge, as for pages. `request_sizes_before_pages` counts every break
  it is given, since no page file shows which would need no request.

### DEV-008 — Page-break verification in runs

`Status`: `DONE` `Depends On`: `DEV-007` `Acceptance`:
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

Evidence, 2026-11-22, repo root, on `203aa10` (the user's DEV-008 commit) plus
the uncommitted change that names a break's pages once in the summary, rerun in
full. Assessed content, lines and SHA-256 prefix:
`src/pydelity/pipeline/runner.py` (2,367, `b66d384213472a06`),
`src/pydelity/pipeline/schemas.py` (229, `fd9148c191c58db9`) and
`docs/src/content/docs/reference/run-json.md` (147, `b44358da74f1d4b8`), with no
other change under `src`, `scripts`, `examples` or `docs`.

- `ruff check scripts src tests`, `ruff format --check` and
  `ty check scripts src tests`: all passed. `interrogate scripts src tests`:
  100%.
- `.venv/bin/pytest --numprocesses auto`: 200 passed, 11 failed, each from a
  replaced contract, for Tester:
  - Runs that now reach page-break verification with no break answer given to
    the stand-in, which answers "No judge answer for the break after page index
    0":
    `costs/test_budget.py::test_estimate_writes_nothing_and_a_reusable_survey_costs_nothing`,
    `pipeline/test_runner.py::test_a_rerun_with_unchanged_inputs_reuses_everything`,
    `pipeline/test_runner.py::test_no_output_file_holds_the_api_key`,
    `pipeline/test_runner.py::test_run_json_records_each_step_its_pages_cost_and_review_issues`,
    `report/test_html.py::test_a_page_no_verifier_reviewed_says_so_in_the_report`,
    `surveying/test_survey.py::test_turning_the_survey_s_verifier_on_surveys_again_only_what_no_verifier_reviewed`
    and
    `test_api.py::test_async_run_gives_what_run_gives_with_the_same_warnings`.
  - Runs that now record a third step:
    `test_cli.py::test_a_pdf_alone_runs_the_survey_with_keys_from_the_environment`
    (a survey pause skips `page_breaks` too) and
    `test_cli.py::test_pages_and_no_pause_extract_only_those_pages_in_one_run`
    (`page_breaks` skipped with `missing_page_files`).
  - A run that now pauses after page extraction:
    `extracting/test_extraction.py::test_a_failed_page_stops_the_run_and_the_next_run_extracts_only_what_is_missing`.
  - An estimate with a third step:
    `costs/test_budget.py::test_the_estimate_covers_page_extraction_and_its_verifier_only_when_it_runs`.
  - Five passing tests in `report/test_html.py` and
    `extracting/test_extraction.py` narrow `pages` and now issue
    `missing_page_files`.
- `--doctest-modules src`: 34 passed, 1 skipped (the new `_page_ranges`
  example). The reference-page generator followed by the Markdown formatter
  changes only `run-json.md`, which now shows `steps[].breaks` and its counts.
  `markdownlint-cli2 --all-files`: passed.
- Scratchpad `dev008_check.py` (`PYTHONPATH=src:.`, the stand-in with the canned
  1965 scan answers): 132 of 132 checks passed.
  - Pause on: the first run pauses after the survey with page extraction and
    page-break verification skipped and an estimate of the survey only. The
    second extracts both pages, skips the step with no break counts and no
    outputs, pauses with the page-extraction message and estimates page
    extraction only. The third makes one judge request and no page request,
    estimates the step in it (1 break), records
    `page_breaks completed (1 break: 1 judged, 0 reused)` with its request and
    cost, and returns the verdict file as written. The fourth asks nothing,
    sends nothing and records `reused`.
  - Pause off: one estimate of all three steps, the judge request after the last
    page request, and titled estimate lines (`Survey`, `Extraction` with
    `2 pages`, `Page-break verification` with `1 break`).
  - Narrowed `pages`: page 1 alone completes with one `missing_page_files`
    warning in the step naming page index 1 and the exact message, an estimate
    without the step and no judge request. Page 2 next, with page 1 current,
    estimates page extraction and the break in page extraction and judges it.
    `--overwrite` with page 2 leaves the break out of the estimate, warns about
    page index 0, keeps the old verdict file on disk, and `load` leaves it out.
    A missing page file wins over the pause, and a narrowed run that leaves
    every page current judges the break.
  - One-page PDF: a survey pause skips both later steps; the next run completes
    after page extraction with the info line, no warning and no request; the
    run's estimate and `aestimate` leave the step out.
  - Spend control: a no in the survey, in page extraction and in page-break
    verification stops the run with that step `stopped`, nothing sent, and the
    estimate covering exactly the steps the run would reach. A `max_cost` no in
    page-break verification stops it before `confirm`. With the step's model on
    OpenAI and no OpenAI key, the run fails with `MissingApiKeyError` before any
    request, whether the estimate is in the survey, page extraction or the step.
    With pause on, page extraction does not need that key. With the key, the
    break is judged on OpenAI.
  - `aestimate`: covers the step only when the run would reach it, counts the
    break when only the survey is saved and pause is off, and when only the
    pages are saved, shows it as reused when the verdict is saved, and counts it
    with its verifier when `verify` is on and pause off. It writes nothing.
  - Review: a verdict failing `continues` with no retries is kept; `run.json`
    lists the survey's, the pages' and then the break's issues, and the summary
    shows `page_breaks: pages 1 and 2: continues: ...`, naming the pages once,
    and `continues 1`.
  - Failure: a break with no answer fails the run and the step with
    `ProviderError` and counts 0 judged; the next run judges only that break.
    `extract()` makes no page-break request and writes no `page_breaks/`.
  - `load`: returns the verdict file; leaves it out when a page file's bytes
    change, when its PDF hash differs, or without `pdf_facts.json`; raises
    `OutputError` on an invalid file and on schema version 2.0; ignores
    `notes.json` and temporary files.

**Implementation Notes**

- The estimate made before the survey also leaves the step out when `overwrite`
  is set and `pages` is narrowed, since then no unselected page can be current
  (decision 8 and the first rule of **Cost estimate**).
- Before page extraction, each break between two pages that are current now is
  planned on its own with `plan_breaks(quiet=True)` and measured if it is to be
  judged. Breaks with a page to extract use `request_sizes_before_pages`.
- In page-break verification the estimate counts the breaks the models judge.
  When only `no_content` verdicts are to be written, no estimate is shown and
  nothing is asked, but the step still builds its model and so needs its
  provider's API key.
- A run that fails or stops records the steps it started, as before. Steps not
  reached are recorded `skipped` after a pause, as decision 10 says.
- The `--overwrite` note cannot follow a page-extraction pause, because
  `--overwrite` always runs the survey again and the run pauses there, so the
  note stays the survey pause's.
- A break issue's summary line leaves the pages out of its place, as
  `page_breaks, item p0004-012: pages 4 and 5: ...`, because the issue's message
  already names them. **Summary and log lines** shows them in both, which
  repeated them; the user chose to name them once on 2026-11-22.

### DEV-009 — Python functions and the CLI

`Status`: `DONE` `Depends On`: `DEV-008` `Acceptance`:
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

Evidence, 2026-11-22, repo root, on `35034f1` (the user's commit after DEV-008)
plus the uncommitted DEV-009 changes. Assessed content, lines and SHA-256
prefix: `src/pydelity/__init__.py` (90, `e94479723f274eb6`),
`src/pydelity/api.py` (906, `098dfe89de3d9bd9`), `src/pydelity/cli.py` (388,
`b74fa8c65df4f0a9`), `src/pydelity/pipeline/runner.py` (2,451,
`54f84989e705602b`), `docs/src/content/docs/reference/cli.md` (54,
`f59508352ab19817`) and `docs/src/content/docs/reference/python-api.md` (612,
`059818e58fb2d7dc`), with no other change under `src`, `scripts`, `examples` or
`docs`.

- `ruff check scripts src tests`, `ruff format --check` and
  `ty check scripts src tests`: all passed. `interrogate scripts src tests`:
  100%.
- `.venv/bin/pytest --numprocesses auto`: 200 passed, 11 failed, the same 11
  tests of replaced contracts DEV-008 lists, and no other.
  `--doctest-modules src`: 34 passed, 1 skipped. The reference-page generator
  followed by the Markdown formatter changes `python-api.md` (`verify_breaks`,
  the async forms line, and the `run`, `estimate` and `load` docstrings) and
  `cli.md` (`--no-pause`). `markdownlint-cli2 --all-files`: passed.
- Scratchpad `dev009_check.py` (`PYTHONPATH=src:.`, the stand-in with the canned
  1965 scan answers): 35 of 35 checks passed.
  - `pydelity.__all__` holds `verify_breaks`, `averify_breaks`, `BreakFile` and
    `PageBreakError`.
  - `averify_breaks` on a fresh folder runs the survey, both pages and the
    judge, with pause on by default and no pause, logs one estimate of the three
    steps, writes no `run.json` and no report, and returns the verdict `load`
    reads. A second call sends nothing and returns the same verdict.
  - With `pages="1"` it returns no verdict, issues one warning naming page 2 and
    sends no judge request. With `pages="2"` next it judges the break.
  - A one-page PDF returns no verdict, with the info line and no warning.
  - `max_cost` below the folder's spend raises `BudgetExceededError` before any
    request, and `allow_over_max_cost=True` goes on with the warning.
  - `verify_breaks` works without a running event loop and, inside one, raises
    `RuntimeError` naming `averify_breaks`.
  - A judge answer that is not a verdict raises `PageBreakError`: "Break after
    page 1 (pages 1 and 2), judge: the model gave no usable answer: Exceeded
    maximum output retries (2)". The page files stay and no verdict file is
    written.
  - The `pydelity` command, run as a subprocess against the stand-in: `--help`
    shows the new `--no-pause` text. `-np -y` exits 0 with three completed
    steps, the summary line and the page-break estimate line. Without `-np`,
    three runs pause after the survey, pause after page extraction with its
    message, then judge the break, each exiting 0. `run(pause=False)` records
    the same steps and statuses as `-np`. With a judge answer that is not a
    verdict, the command exits 1, logs the error, and `run.json` records the run
    and the step `failed` with `PageBreakError`.

**Implementation Notes**

- The CLI already maps every `PydelityError` other than input and spend errors
  to exit code 1, so `PageBreakError` needed no handler of its own. Only the
  `--no-pause` help changed.
- `run_page_breaks_step` shares a new `_open_run` with `run_extraction_step`,
  which opens the PDF, prepares the folder and starts a run without a record.
- `api.py`'s module docstring lists `verify_breaks`, and `load`'s names it among
  the functions whose folder it reads.

### DEV-010 — Page breaks in the HTML report

`Status`: `DONE` `Depends On`: `DEV-008` `Acceptance`: `AC-039`

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

Evidence, 2026-11-22, repo root, on `7e5ea61` (the user's commit after DEV-009)
plus the uncommitted DEV-010 changes. Assessed content, lines and SHA-256
prefix: `src/pydelity/report/html.py` (1,660, `9ed3afa592c96e8f`),
`src/pydelity/report/report.css` (290, `65d8df1cb78b8fb9`) and
`src/pydelity/pipeline/runner.py` (2,458, `d2c449279577fdb7`), with no other
change under `src`, `scripts`, `examples` or `docs`.

- `ruff check scripts src tests`, `ruff format --check` and
  `ty check scripts src tests`: all passed. `interrogate scripts src tests`:
  100%.
- `.venv/bin/pytest --numprocesses auto`: 200 passed, 11 failed, the same 11
  tests of replaced contracts DEV-008 lists, and no other.
  `--doctest-modules src`: 37 passed, 1 skipped (the new examples of
  `_break_anchor`, `_break_labels` and `_marker_text`). The reference-page
  generator followed by the Markdown formatter leaves `docs` unchanged.
- Scratchpad `dev010_check.py` (`PYTHONPATH=src:.`, the stand-in with the canned
  1965 scan answers): 45 of 45 checks passed. Every report parses with each
  element closed in order, and every `id` is unique.
  - The fixture's verdict (nothing continues): the "Page breaks" section comes
    after the pages, with card `break-0000`, heading "Pages 1 and 2", both
    `report/pages/` images, no boxes, "Content continues: no", "Verifier: no
    verifier ran", no pieces or containers, a plain caption, the reason with its
    quotes escaped, and the model in the header.
  - A judge verdict naming real items, with the page-break verifier on and
    finding one problem: boxes "end 1" on page 1 and "start 1, marker 1" and
    "repeat 1" on page 2, those named by a review issue marked and labeled !,
    containers the pages lack listed but not drawn, every piece field, "found 1
    problem, listed for review", and the card's review issues. The review
    table's "Page-break verification" heading has a "Pages" column whose links
    go to `#break-0000`, and the page cards show none of the break's issues.
  - `pages="1"` then `pages="2"`: the first report has no section. In the
    second, page 1 has a survey card, not an extracted one, and the break card
    still draws page 1's box from the page file page-break verification read.
  - Hand-built verdicts written with `write_report`: a reason, entry, marker,
    repeated item, container and issue holding `<script>`, `<img onerror>` and
    other markup all appear escaped, with no `script` element and no extra
    image. A `merge_split_row` piece shows its cell joins, repeated header rows
    and entries. A kept correction reads "found 2 problems and its correction
    was kept". A `no_content` verdict on a made-up third page shows "Requests:
    none, because a page of the break has no content items" and no verifier
    line. Review links reach both cards, and a break issue's item is plain
    escaped text. With no verdicts the report has no section and no model line.
  - Viewed in the in-app browser, served over a local port at 1400 pixels wide
    and the pane's width: the two pages sit side by side and stack when narrow,
    boxes and labels sit on the right items, escaped text shows as written, and
    the review link to "2 and 3" goes to its card.

**Implementation Notes**

- The verdict's details go below the two images rather than beside them. Beside
  them, three columns would shrink each page image too far to read.
- Page cards leave out page-break issues. They keep their `page_index` (the
  break's earlier page), so without the filter they would also show on page 1's
  card. They appear on their break's card and in the review table.
- Break-card boxes carry no `id`, so they never clash with the page cards' box
  anchors. A break issue's item in the review table is plain text, because its
  page may have no page card with items in this report.
- `_run_header` adds "Page-break verification model" from the first verdict.
- For the Tester: `test_a_page_no_verifier_reviewed_says_so_in_the_report`
  counts `Verifier: no verifier ran` lines, and a break card adds one when the
  run reaches page-break verification with the verifier off.

### DEV-011 — Smoke test, package description and reference pages

`Status`: `DONE` `Depends On`: `DEV-009, DEV-010` `Acceptance`:
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

Evidence, 2026-11-22, repo root, on `94ac1b6` (the user's commit after DEV-010)
plus the uncommitted DEV-011 changes. Assessed content, lines and SHA-256
prefix: `pyproject.toml` (199, `e16be032c8450389`),
`scripts/smoke_installed_wheel.py` (538, `d1fab52124a94ff6`),
`scripts/generate_reference_docs.py` (1,339, `d40f69e8f66eb18f`), the new
`docs/src/content/docs/reference/page-break-json.md` (298, `89a26f4198085e31`)
and `page-break-checks.md` (116, `57008dbfe7e8ce96`), and the regenerated
`cost-jsonl.md`, `extraction-checks.md`, `python-api.md`, `run-json.md`,
`survey-checks.md` and `uploads-json.md` (side-panel order, and the `BreakFile`
link). Nothing under `src` or `examples` changed.

- `ruff check scripts src tests`, `ruff format --check` and
  `ty check scripts src tests`: all passed. `interrogate scripts src tests`:
  100%.
- `.venv/bin/pytest --numprocesses auto`: 200 passed, 11 failed, the same 11
  tests of replaced contracts DEV-008 lists, and no other.
  `--doctest-modules src`: 37 passed, 1 skipped.
- `scripts/generate_reference_docs.py` followed by the Markdown formatter writes
  13 pages. A second run of both leaves every page's bytes unchanged.
  `markdownlint-cli2 --all-files`: passed.
- The new pages cover `BreakFile` and every part of it, the eight checks and the
  `start_markers` hint apart, text comparison with the match thresholds read
  from the code (3 characters, Dice 0.8), and the `verifier` issue.
  `advanced.page_breaks`, `verify_breaks`, `averify_breaks`,
  `StepRecord.breaks`, `StepEstimate.breaks`, the ledger docstrings and the two
  page-break cost constants were already on their pages from DEV-001 to DEV-009.
  The Python API page's `RunResult` return text names the verdict files.
- `uv build --wheel --offline` built `pydelity-0.2.0-py3-none-any.whl`, and
  `twine check --strict` passed on it. Its `Summary` is the new description.
- The smoke script against that wheel: 13 of 13 checks passed. For each
  provider, `pydelity --yes --no-pause` exits 0, its folder loads with a page
  file for each page and one verdict, and the run sends one upload and 4 model
  requests (survey, two pages, one judge) to the stand-in. `run(pause=False)`
  through the installed copy returns the same with `load()` equal. `--version`
  prints 0.2.0.
- Limitation: the sandbox has no network, and uv's cache lacks the locked
  `pydantic-core` 2.50.4, so pip could not install the wheel's dependencies from
  PyPI. A scratchpad wrapper replaced only the script's `_install`. It created a
  fresh environment with `uv venv --offline`, installed the wheel with
  `--no-deps`, and added the project environment's site-packages after it in a
  `.pth` file for the dependencies. That directory is not a site directory, so
  the project's editable pydelity was not importable, and the "installed copy"
  check confirmed `pydelity` came from the new environment. The install from
  PyPI itself runs in CI's wheel job on Linux, macOS and Windows.

**Implementation Notes**

- The verdict file page comes after the page file page, and the page-break
  checks page after page extraction's, so `run.json`, `cost.jsonl`,
  `uploads.json`, the survey checks and the extraction checks each move down one
  place in the side panel.
- A list whose items have more than one type now shows them in parentheses, such
  as `cell_joins`: `list of (one of ... or null) or null`. No other page's text
  changed with it.
- The smoke script's load and run checks require a verdict for each break, so a
  run that skipped page-break verification fails them.

### DEV-012 — Verdict format additions, the unfinished-text rule and a narrower start-marker hint

`Status`: `DONE` `Depends On`: `NONE` `Acceptance`:
`AC-013, AC-014, AC-022, AC-047, AC-052, AC-053, AC-054, AC-055`

**Goal**

Let a verdict start a new list entry from a text item and mark a split row's
cell that only repeats the cell above it, tell the model when text is
unfinished, and stop the start-marker hint from flagging appended rows and
pieces whose start carries a continuation marker.

**Affected Area**

MODIFY `src/pydelity/verifying/schemas.py` (`TextJoin`, the `cell_joins` and
`text_join` docstrings), `src/pydelity/verifying/validators.py` (`joins`,
`repeats`, `start_markers`), `src/pydelity/verifying/prompts.py` (the joins rule
and the new rule 6), `scripts/generate_reference_docs.py` (the page-break checks
page's text for these three); regenerate the reference pages.

**Expected Outcome**

- `TextJoin` holds `repeat`. `joins` accepts `repeat` only in a
  `merge_split_row` piece's `cell_joins` and fails it in `text_join`; `newline`
  still fails in `cell_joins`. A `new_entry` piece passes from a list item or a
  text item on the earlier page to a list item on the later page, and fails when
  its start is not a list item.
- `repeats` fails a `repeat` cell whose merged-row cell has no text, or whose
  text matches no cell of the earlier table's last row, by the matching rules
  repeated items use, containment included.
- `start_markers` skips an `append_rows` piece, and a piece with a marker on its
  start item and, for a table, on the row its start text comes from. Other
  pieces are compared as before.
- The judge's rules add `new_entry` from a text item and `repeat` to the joins
  rule, and the design's "when text continues" rule as rule 6, with the later
  rules renumbered. No added text names a language, document type, marker style
  or direction. `PROMPT_VERSION` stays 1.
- The page-break checks reference page describes the new `joins` and `repeats`
  cases and the hint's two exceptions.

**Self-Check**

The lint commands; pytest and doctests, with tests of replaced rules listed for
Tester; a scratchpad script with hand-built page files and verdicts that passes
and fails each new `joins`, `repeats` and `start_markers` case, matches `repeat`
cells with and without "(contd)" in Latin, Chinese and Arabic text, and reads
the new rules for language, document-type and direction words; the
reference-page generator and the Markdown formatter, run twice with no change
the second time.

Evidence, 2026-11-28, repo root, on `33492a6` plus the uncommitted DEV-012
changes (macOS arm64, Python 3.13.9, tools from `.venv/bin`). Assessed content:
`git diff HEAD -- src scripts examples docs` (5 files, 231 insertions and 56
deletions), SHA-256 starting `08631ca3615b7d34`.

- `ruff check scripts src tests`, `ruff format --check scripts src tests` (101
  files) and `ty check scripts src tests`: all passed.
  `interrogate scripts src tests`: 100%.
- `.venv/bin/pytest --numprocesses auto -p no:cacheprovider`: 248 passed, none
  failed. No existing test covered a rule this step replaced.
  `--doctest-modules src`: 37 passed, 1 skipped.
- Scratchpad `dev012_check.py` (`PYTHONPATH=src:.`, page files from the builders
  in `tests/pydelity/verifying/conftest.py`): 38 of 38 checks passed.
  - `new_entry` from a text item to a list passes every check, and from a list
    to a list still passes `joins`. Starting in a text item fails `joins` on the
    later page ("uses new_entry, which starts in list items, but it starts in
    p0003-002, a text item"), and ending in a code item fails it.
  - `repeat` cells pass every check for "PHONICS (contd)" and "PHONICS" over
    "PHONICS", "语音（续）" over "语音", "الصوتيات (تابع)" over "الصوتيات", and
    over another cell of the split row. A `repeat` cell matching no split-row
    cell, with no text, or over a split row whose cells are empty fails
    `repeats`, with the cell, item and row in `details` and the later page in
    `page_index`. A cell join past the row's cells is left to `joins`, which
    still fails it. `newline` in `cell_joins` fails `joins`, whose message now
    lists `repeat` as allowed. `repeat` as the `text_join` of `continue_text`
    (text and code) and of `continue_entry` fails `joins`, ending "repeat is
    only for the cell_joins of merge_split_row".
  - `start_markers` skips an `append_rows` piece, a `merge_split_row` piece with
    a marker on its start row, and text and list pieces with a marker on their
    start item. A marker on another row of the start table or on another item
    skips nothing, and a text piece starting with a start marker is still a
    difference. `retry_message` holds no `start_markers` text.
  - The judge's instructions define `repeat`, allow `new_entry` from a text
    item, and hold the "When text carries on" rule between "Text joins" and
    "Tables". The rules hold none of 22 language, script, direction,
    document-type and marker words checked, such as "Arabic", "left to right",
    "report", "contd" and "bullet".
- `scripts/generate_reference_docs.py`, then the Markdown formatter (outside the
  sandbox, which blocks prek's log in `~/.cache/prek`): only
  `page-break-checks.md` (the `joins`, `repeats` and `start_markers` text) and
  `page-break-json.md` (`cell_joins`, `text_join`) changed. A second run of both
  changed nothing. `markdownlint-cli2 --all-files`: passed.

**Implementation Notes**

- The prompt's rules are headed paragraphs, not numbered ones, so the design's
  rule 6 is a new paragraph, "When text carries on", between "Text joins" and
  "Tables". Nothing was renumbered.
- `_JOIN_KINDS` became `_JOIN_END_KINDS` and `_JOIN_START_KINDS`, since
  `new_entry` now ends in more kinds than it starts in.
- `scripts/generate_reference_docs.py` needed no change. The page-break checks
  page takes each check's and hint's text from its docstring.
- Code cannot tell a repeated label from a joined one, so a text join for a cell
  that only repeats the cell above it still passes the checks. The prompt rule
  and, with the verifier on, DEV-015's comparison are what catch it.

### DEV-013 — Comparing two verdicts for the same break

`Status`: `DONE` `Depends On`: `DEV-012` `Acceptance`: `AC-058`

**Goal**

Give code a comparison of two verdicts for the same break, so the verifier's
second judgment can be compared with the kept one.

**Affected Area**

MODIFY `src/pydelity/verifying/validators.py` (`compare_verdicts`),
`src/pydelity/review.py` (`verdicts_differ` in `IssueName`, the `details`
docstrings of `CheckFailure` and `ReviewIssue`).

**Expected Outcome**

- `compare_verdicts(kept, verifier)` returns one `CheckFailure` per difference,
  as **Verdict comparison** sets out: one `continues` difference and nothing
  else when only one verdict continues; pieces paired by end, then by start; one
  `piece` difference per unpaired piece, the kept verdict's first; per pair
  `end`, `start` and `join`, and, when the joins are equal, `text_join`,
  `cell_joins` (one per differing cell, or one for the whole list when the
  lengths differ) and `repeated_header_rows`. Repeated items, markers,
  containers and `reason` are not compared. An empty list means the verdicts
  match.
- Each difference has a message starting `verdicts_differ` that names both
  values and the piece, the break's earlier page as `page_index`, and `details`
  with `field`, `kept`, `verifier`, and `item`, `entry` and `cell` where they
  apply.
- `verdicts_differ` is in `IssueName`, in its own type `BreakComparisonName`.
  Nothing calls `compare_verdicts` yet.

**Self-Check**

The lint commands; pytest and doctests; a scratchpad script with pairs of
verdicts for each rule above, including pieces in a different order, a pair
found by start only, two pieces with the same end, a cell-join list of another
length, and verdicts that differ only in repeated items, markers, containers or
reason (no difference).

Evidence, 2026-11-28, repo root, on `50229ba` plus the uncommitted DEV-013
changes (macOS arm64, Python 3.13.9, tools from `.venv/bin`). Assessed content:
`git diff HEAD -- src scripts examples docs` (6 files, 564 insertions and 33
deletions), SHA-256 starting `0e203a086200d51d`.

- `ruff check scripts src tests`, `ruff format --check scripts src tests` (101
  files) and `ty check scripts src tests`: all passed.
  `interrogate scripts src tests`: 100%.
- `.venv/bin/pytest --numprocesses auto -p no:cacheprovider`: 248 passed in 20
  of 23 runs. In the other 3,
  `test_break_requests_sent_at_once_are_held_to_max_cost_together` failed (in
  one of them with one other test), and it passed when its file ran alone. It
  times requests in flight with a 0.3 s stand-in delay, nothing in this step is
  on its path, and 5 runs on a clean copy of `50229ba` all passed, so it looks
  like a timing failure under load. It tests contracts DEV-015 replaces; noted
  for Tester.
- `--doctest-modules src`: 40 passed, 1 skipped (the new `_all_of`, `_point` and
  `_value` examples among them).
- Scratchpad `dev013_check.py` (`PYTHONPATH=src`, verdicts built in code): 29 of
  29 checks passed.
  - Same verdicts, verdicts that both say nothing continues, and pieces in
    another order give no difference.
  - Only one verdict continuing gives one `continues` difference, with
    `kept`/`verifier` true or false, the first continuing piece's item, the
    earlier page in `page_index`, and a message naming every continuing piece
    ("the kept verdict says content continues, in piece 1 (p0003-009 to
    p0004-001) and piece 2 (...), and the verifier's says nothing continues"). A
    continuing verdict with no pieces says it names no piece and points at no
    item.
  - Pairs found by end give a `start` difference, and a pair found by start only
    gives an `end` difference. An entry counts in the end, with the entry IDs as
    values and in `entry`.
  - Two kept pieces with the same end pair the first and leave the second as a
    `piece` difference with its ends as `kept` and null as `verifier`. Two such
    pieces in another order pair by end, then by start. Unpaired pieces come
    first, the kept verdict's before the verifier's, then the pairs'
    differences.
  - Different joins give only a `join` difference. Same joins give `text_join`,
    `repeated_header_rows` and one `cell_joins` difference per differing cell,
    with `cell` first in `details`. A cell-join list of another length, or null
    against a list, gives one difference for the whole list, with no `cell`.
  - Different repeated items, markers, containers and reason give no difference.
- `scripts/generate_reference_docs.py`, then the Markdown formatter (outside the
  sandbox): `page-break-json.md`, `page-json.md`, `pdf-survey-json.md` and
  `run-json.md` changed, each with `verdicts_differ` in the issue names and the
  new `details` text. A second run of both changed nothing.
  `markdownlint-cli2 --all-files`: passed.

**Implementation Notes**

- `compare_verdicts` takes the break's earlier page as a keyword, `page_index`,
  since a verdict does not hold it.
- A piece's end and start are given as one ID, the entry's when the piece names
  one, else the item's, in both the messages and the `kept` and `verifier`
  values. An unpaired piece's value is its ends, such as
  `p0003-009 to p0004-005`.
- `item` and `entry` are always in `details`, null when no piece applies; `cell`
  is there only for one cell's join.
- Pieces in messages are named by their position in their own verdict, as the
  checks name them, so a verifier-only piece reads "the verifier's piece 2
  (...)".
- `_piece_name` now names pieces for the checks too, so both use one form.
- `IssueName`'s `verifier` comment still covers page breaks; DEV-015 limits it
  to the survey and page extraction when the page-break verifier issue goes.

### DEV-014 — The stand-in answers a break's requests in arrival order

`Status`: `PENDING` `Depends On`: `NONE` `Acceptance`: `AC-040, AC-042`

**Goal**

Let the stand-in answer page-break requests without telling the judge's from the
verifier's, since after DEV-015 the two send the same request.

**Affected Area**

MODIFY `tests/fixtures/mock_providers.py`,
`tests/fixtures/break_answers/irs_form_1040a_1965_scan.json`.
`scripts/smoke_installed_wheel.py` and `tests/conftest.py` pass the file's
content through and should need no change.

**Expected Outcome**

- `break_answers` (the argument, the `--break-answers` file and
  `read_break_answers`) maps each break's earlier page index to one answer or a
  list. Each request for that break gets the next answer, the last one
  repeating, however different breaks' requests interleave. A page-break request
  without an answer gets HTTP 400 naming the break.
- A page-break request is recorded with its `break_index` and `agent: None`, and
  `"judge"` leaves the stand-in's agent names. The cost ledger says which agent
  sent each request. Page and survey routing stay as they are.
- The canned 1965 scan file holds the judge's verdict alone for break 0, with no
  agent key.

**Self-Check**

The lint commands on `tests/fixtures`; the existing tests, with those that key
break answers by agent or read a break request's agent listed for Tester; a
scratchpad script that runs the current step through the stand-in for both
providers with a list of answers per break, two breaks interleaved and a check
retry, and a break without an answer (HTTP 400);
`python -m tests.fixtures.mock_providers --help`.

### DEV-015 — The verifier judges each break a second time

`Status`: `PENDING` `Depends On`: `DEV-013, DEV-014` `Acceptance`:
`AC-027, AC-028, AC-031, AC-032, AC-033, AC-038, AC-039, AC-047, AC-056, AC-057, AC-058, AC-059`

**Goal**

Replace the verifier's review of the judge's verdict with the judge's request
sent again and compared in code, through the verdict file, the review list, the
log, the estimate and the report.

**Affected Area**

MODIFY `src/pydelity/verifying/schemas.py`, `prompts.py`, `agents.py`, `llm.py`,
`validators.py` (`review_issues`) and `verification.py`;
`src/pydelity/costs/budget.py`; `src/pydelity/review.py` (the `verifier` name's
comment); `src/pydelity/report/html.py`; `src/pydelity/config/schemas.py`,
`src/pydelity/cli.py` (`--verify` help) and `examples/config.yaml` where they
describe the page-break verifier; `scripts/generate_reference_docs.py` (the
comparison in place of the verifier issue on the page-break checks page);
regenerate the reference pages.

**Expected Outcome**

- `BreakVerification` holds `attempts`, `checks` (`list[BreakCheckResult]` in
  `CHECKS` order), `differences` (`list[CheckFailure]`) and `verdict`
  (`BreakVerdict`). `BreakVerifierVerdict`, `BreakProblem` and
  `BreakProblemCategory` are gone.
- `judge_break` builds the break's one request. `verify_break`, the review text
  and the verifier-only instructions are gone. One agent factory and one send
  function serve both agents, with the agent's name in log lines, errors and the
  ledger. The verifier's request has the judge's instructions and user content
  and no message history, and its verdict is checked and sent back within
  `check_retries` as the judge's is, the last one accepted as it is.
- Per break, the judge's accepted verdict is written with `verification: null`.
  With the verifier on, the same request is then sent for `verifier`, and
  `verification` saves its verdict, attempts, check results and
  `compare_verdicts(kept, verifier's)`. The issues are recomputed and the file
  is rewritten. The judge's verdict is always the kept one.
- Issues: checks still failing on the kept verdict, then hint differences unless
  `verification` is set with no differences, then one `verdicts_differ` issue
  per difference with its `details`. The verifier's own check failures are saved
  and not listed, and page-break verification gives no `verifier` issue.
- The break's log line says `verifier agrees`, `verifier differs in <n> places`
  (`1 place`) or `no verifier`.
- Estimate: `BreakRequestSize.chars` (the one request), one judge request and,
  with the verifier on, one verifier request per break, each with
  `TYPICAL_BREAK_OUTPUT_TOKENS` of output; the maximum covers every attempt of
  each agent. `TYPICAL_BREAK_VERDICT_OUTPUT_TOKENS` and the verifier's own
  allowance are removed.
- A break card's verifier line says the verifier's verdict matches, lists each
  difference's message, or says no verifier ran.
- `advanced.page_breaks.verify`, `verify`, `--verify` and the YAML example's
  comments describe the page-break verifier as a second judgment compared with
  the first. The page-break checks and verdict file reference pages describe the
  comparison and the new `verification`.

**Self-Check**

The lint commands; pytest and doctests, with tests of the replaced verifier
listed for Tester; a scratchpad script through the stand-in on the 1965 scan and
hand-built page files: with the verifier off, one request per break and
`verification: null`; with it on, two requests with equal instructions and user
content, ledger lines `judge` then `verifier`, a matching verdict that adds no
issue and drops the hint issues, a differing one that adds `verdicts_differ`
issues, a failing verifier verdict sent back and then kept with its failures
saved but not listed, and a failed verifier request that raises `PageBreakError`
naming `verifier` and leaves the judge's verdict file; the estimate against
hand-computed figures; a report with the three verifier lines and escaped
difference text; the reference-page generator and the Markdown formatter.

### DEV-016 — Keep the judge's verdict when only the verifier's judgment is missing

`Status`: `PENDING` `Depends On`: `DEV-015` `Acceptance`:
`AC-033, AC-035, AC-042, AC-060`

**Goal**

When the verifier is turned on over verdicts judged without it, ask only the
verifier and keep the judge's verdict, and price only that request.

**Affected Area**

MODIFY `src/pydelity/verifying/verification.py` (`PlannedBreak`, `plan_breaks`,
the reuse rule, the break task, request sizes), `src/pydelity/costs/budget.py`
(`BreakRequestSize.judge`, `estimate_page_breaks`), and
`src/pydelity/pipeline/runner.py` only where its estimate paths need the flag.

**Expected Outcome**

- A valid, matching verdict file with `judgment: "model"` and no verification,
  while the verifier is on and `overwrite` is off, keeps its judge's verdict: it
  counts among the breaks to judge, gets an info line that the verifier judges
  it now and the judge's verdict is kept, sends only the verifier's request, and
  keeps its `verdict`, `checks` and `hints` while the file is rewritten with
  `verification` set. Other files are reused or judged as before.
- `BreakRequestSize.judge` is `False` for such a break, and the estimate prices
  only its verifier request. `requests_max` sums, over the breaks, the agents
  that run times the attempts. The run's estimate, `estimate()` and
  `aestimate()` follow.

**Self-Check**

The lint commands; pytest and doctests; a scratchpad script through the
stand-in: a run with the verifier off, then on, sends only verifier requests and
keeps each verdict, its checks and its hints; a rerun reuses every break;
`overwrite` sends both requests again; a failed verifier request followed by a
rerun asks only the verifier; the estimates price only the verifier for those
breaks. A wheel built with `uv build --wheel --offline`, `twine check --strict`,
and the smoke script against it, as DEV-011 ran it.

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

### Rework after the real runs (2026-11-28)

- Recovery frame 1 (`Owner: SCOPING`, `ResumeAt: REVIEWING_FINAL`,
  `RerunThrough: DOCUMENTING`) reran Scoper and Architect. Developer reruns
  downstream with its full gate. No Developer assignment was interrupted: the
  plan was `COMPLETE` when final review routed the rework, so no suspended
  assignment is saved.
- DEV-001 to DEV-011 stay `DONE` with the earlier pass's evidence. The rework
  replaces these parts of their outcomes: DEV-002's `BreakVerifierVerdict`,
  `BreakProblem` and `BreakVerification` fields (DEV-015) and `TextJoin`
  (DEV-012); DEV-003's `joins`, `repeats` and `start_markers` rules (DEV-012)
  and its review-issue order (DEV-015); DEV-004's verifier prompt, agent and
  `ask_verifier` (DEV-015) and the judge's rules (DEV-012); DEV-005's break
  answers keyed by agent (DEV-014); DEV-006's verdict application (DEV-015) and
  reuse rule (DEV-016); DEV-007's `BreakRequestSize` fields, the verdict-review
  constant and the verifier allowance (DEV-015, DEV-016); DEV-010's verifier
  line (DEV-015); DEV-011's reference pages (DEV-012, DEV-015).
- Names for the user's approval. From the design: the cell join `repeat`, the
  issue name `verdicts_differ`, `BreakVerification`'s fields `attempts`,
  `checks`, `differences` and `verdict`, the difference `details` keys `field`,
  `kept`, `verifier`, `item`, `entry` and `cell`, with `field` values
  `continues`, `piece`, `end`, `start`, `join`, `text_join`, `cell_joins` and
  `repeated_header_rows`, the function `compare_verdicts`, and
  `BreakRequestSize`'s `chars` and `judge`. Developer's proposals:
  `BreakComparisonName` for the type holding `verdicts_differ` (DEV-013);
  `create_break_agent(agent=...)` for the one agent factory, `ask_model` for the
  one send function and `BreakAnswer` for its result, in place of `JudgeAnswer`
  and `VerifierAnswer` (DEV-015); page-break requests recorded by the stand-in
  with `agent: None` (DEV-014).
- Order: DEV-014 needs nothing earlier and may run before DEV-012 or DEV-013.
  DEV-015 is the critical path. Each step leaves the package importable.
- Tests are Tester's. Tests of the replaced contracts fail until Tester updates
  them, as in the earlier pass: verdicts and verifier answers with the old
  shapes, break answers keyed by agent, a break request's recorded agent, the
  review rules for a verifier's problems and correction, the old reuse rule and
  the old estimate. Each step lists the failing tests in its evidence.
- No real model run, download or new dependency is planned. The user's next real
  runs (`AC-061`, `AC-062`) come after the build, with new output folders or
  `--overwrite`, since earlier verdict files with a verification no longer load.

<!-- STANDARDS
Artifact: DEVELOPMENT
Cycle: build-step-2-page-extraction-of-the-20261119T174118Z-0419318a
-->

# Development Plan

`Cycle`: `build-step-2-page-extraction-of-the-20261119T174118Z-0419318a` `Mode`:
`STEPWISE` `User Style`: `tony` `User Style Locked`: `true` `Status`:
`IN_PROGRESS` `Verification Cadence`: `AFTER_IMPLEMENTATION`
`Current Increment`: `NONE`

## Implementation Contract

- `Scope`:
  `.standards/docs/scope/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a.md`
- `Architecture`:
  `.standards/docs/specs/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a.md`
- `Request`:
  `Build step 2 (page extraction) of pydelity on top of the 0.1.x survey: one page file per selected page with items in reading order for any script, layout and writing direction, code checks plus a verifier model on every page, per-step models and instructions, a pause after a new survey, page selection, concurrent page requests, the run features (cost ledger, max_cost, resume, review list, HTML report, CLI and Python API), 0.1.0's follow-up fixes, and release readiness for 0.2.0, with no backwards compatibility with 0.1.x.`

## Build Steps

### DEV-001 — Settings for pages, pause, per-step models and instructions

`Status`: `DONE` `Depends On`: `NONE` `Acceptance`:
`AC-001, AC-002, AC-004, AC-005, AC-006, AC-059, AC-060, AC-061`

**Goal**

Give the config the settings step 2 needs and move instructions under each step,
so the survey already runs on its own resolved model and its own instructions.

**Affected Area**

`config/schemas.py`, `config/loading.py`, `providers/profiles.py`,
`surveying/schemas.py`, `surveying/prompts.py`, `surveying/survey.py`, the code
that reads `config.model`, `config.model_choice` or `config.instructions`
(`pipeline/runner.py`, `api.py`), `cli.py`, `examples/config.json`,
`examples/config.yaml`.

**Expected Outcome**

- `pages` (text, or one integer in a file or keyword) is parsed into its
  canonical form, such as `1-5,8`. Bad syntax is a `ConfigError` line naming
  `pages`, reported with the other settings' problems. Unset means every page.
- `pause` (default `true`), optional `model`, `advanced.survey.instructions`,
  and `advanced.extraction` (`ExtractionConfig`, `extra="forbid"`) with the
  design's defaults and ranges. Blank instructions count as unset.
- `Config` gives the resolved survey and extraction models (`ModelChoice`):
  extraction from `advanced.extraction.model`, else `model`, else its own
  default; the survey from `model`, else its own default. Two default constants
  in `providers/profiles.py`, both `anthropic:claude-opus-5-5`.
  `Config.model_choice` and `DEFAULT_MODEL` are gone.
- The top-level `instructions` setting is gone, so it gets the unknown-setting
  `ConfigError`. `--instructions`/`-i` is gone, so it gets Typer's usage error
  (exit 2).
- The survey's prompt, `SurveyInputs` and fingerprint take
  `advanced.survey.instructions`. `Profile.user_instructions` is removed.
- CLI: `--pages`/`-p` and `--no-pause`/`-np` set those settings, and `--model`
  help names both steps and their defaults. The runner acts on them from DEV-002
  (page numbers past the PDF) and DEV-010 (the pause).
- Both example files hold every setting at its default, in alphabetical order,
  with no top-level `instructions`.

**Self-Check**

Ruff check and format check, `ty check` and interrogate on `scripts src`; pytest
on the tests this step does not break, with the broken ones listed (see Plan
Notes); a scratchpad script that loads files, keywords and mixtures (page forms
and their errors, blank instructions, top-level `instructions` rejected, the
model resolution order); `pydelity <pdf> -i x` exits 2 before any request; both
example files load.

Evidence, 2026-11-19, repo root, on `458d1f6` plus the uncommitted DEV-001
changes (macOS arm64, Python 3.13.9, PyMuPDF 2.1). uv cannot write its cache in
the sandbox, so the tools ran from `.venv/bin` directly.

- `.venv/bin/ruff check scripts src`, `ruff format --check scripts src`,
  `ty check scripts src`: all passed. `interrogate scripts src`: 100%.
- `.venv/bin/python scripts/generate_reference_docs.py`, then
  `prek exec prettier-markdown -- node scripts/format_markdown.mjs` (run outside
  the sandbox, because prek writes its log to `~/.cache/prek`): only
  `reference/cli.md`, `configuration.md` and `pdf-survey-json.md` changed, with
  the new options and settings and without `instructions`, `-i` and
  `user_instructions`. The STANDARDS check passed.
- `.venv/bin/python -m pytest -q --numprocesses auto`: 100 passed, 5 failed.
  Each of the 5 passes the removed top-level `instructions` setting and now gets
  `ConfigError: instructions: not a setting pydelity knows` (`AC-061`), so they
  are Tester's to update:
  `config/test_loading.py::test_config_file_paths_resolve_against_its_folder_and_keywords_win`,
  `surveying/test_survey.py::test_user_languages_lead_and_rejected_model_tags_become_review_issues`,
  `surveying/test_survey.py::test_request_sends_the_facts_as_hints_with_every_repeated_line`
  (it also expects the instructions in the user message; they are now last in
  the system message),
  `report/test_html.py::test_report_escapes_text_from_the_pdf_the_user_and_the_model`
  and
  `pipeline/test_runner.py::test_changing_a_survey_input_or_overwrite_reruns_the_survey[instructions]`.
  `ty check tests` reports 2 errors: `Config.instructions` in
  `config/test_loading.py:120` and `Profile.user_instructions` in
  `surveying/test_survey.py:246`. Doctests (`--doctest-modules src`): 18 passed,
  1 skipped, including the new `parse_pages` example.
- Scratchpad `dev001_settings_check.py`: 50 of 50 checks passed. Page lists
  become canonical (`" 8 , 1-5, 4-6"` gives `1-6,8`, `1-3,4` gives `1-4`, `3` as
  an integer gives `3`); unset is `None`. `""`, `"0"`, `"5-2"`, `"a"`, `"1,,2"`,
  `"1 - 3"`, an Arabic-Indic digit, `-3` (text and integer), `true` and `2.5`
  are each one `- pages:` line, such as
  `- pages: the range 5-2 ends before it starts`; a bad `pages` and a bad
  language are reported together. `pause` defaults to true. Blank survey and
  extraction instructions are unset; top-level `instructions` as a keyword or in
  a YAML file is `- instructions: not a setting pydelity knows`. Models: both
  steps default to `anthropic:claude-opus-5-5`; `model` sets both;
  `advanced.extraction.model` overrides page extraction only, with or without
  `model`; a bad one is named `advanced.extraction.model`; extraction effort is
  `high`. Extraction defaults are 2, 8, 32,000 and 600; `concurrent_pages` 0 or
  33, `check_retries` 6 and an unknown key are rejected. The upload expiry is
  checked against the survey's model only. Both example files resolve to every
  setting at its default (the placeholder price entry aside). The survey prompt
  ends its system message with the instructions only when they are set, never
  puts them in the user message, and `Profile` has no `user_instructions`.
  Survey instructions change the survey fingerprint; page extraction's settings,
  `pages` and `pause` do not.
- Scratchpad `dev001_standin_check.py` (the stand-in provider from
  `tests/fixtures/mock_providers.py`, the 1965 scan and its canned answer): 12
  of 12 checks passed. For Anthropic and OpenAI, `advanced.survey.instructions`
  is in the request's system instructions and not in its messages; unset, no
  instructions heading is sent; `pdf_survey.json` keeps them in `inputs` and the
  profile has none. PydanticAI's first-run banner still prints from the Python
  API (`AC-040`, DEV-011).
- CLI (bash, keys unset, scratchpad output folders): `-i x` and
  `--instructions x` exit 2 with `No such option` and create no output folder;
  `-p 0` and `-p 2-1,x` exit 2 naming `pages`; `-np` and `--pages 3,1-2` are
  accepted, and a run with `-p 3,1-2 -np -v` records `pages: "1-3"`,
  `pause: false`, `model: null` and the `advanced.extraction` defaults in
  `run.json` before stopping on the missing `ANTHROPIC_API_KEY` (exit 2).
  `--help` lists `--pages`/`-p` and `--no-pause`/`-np`; like the other flags,
  `--no-pause` shows `<bool>` in Typer's help table.
- Left for Documenter: `docs/src/content/docs/guides/command-line.md` and
  `guides/configuration.md` still describe `-i` and the top-level
  `instructions`.

**Implementation Notes**

- The code that read `config.model_choice` or `config.model` (factory, ledger
  model, uploads, budget, runner) now reads `config.survey_model`; DEV-003 makes
  it per step. The upload-expiry check uses the survey's model because only the
  survey uploads the PDF.
- The survey's instructions moved from the user message to the end of the system
  message, under a sentence saying they add to pydelity's rules (design decision
  18). `PROMPT_VERSION` stays 1, as scope requires. The report's profile section
  shows them from `pdf_survey.json` `inputs`.

---

### DEV-002 — Shared review issues, per-step run records and the page check

`Status`: `DONE` `Depends On`: `DEV-001` `Acceptance`: `AC-002, AC-026`

**Goal**

Make the review list and `run.json` ready for more than one step, and stop a run
whose `pages` names a page the PDF does not have.

**Affected Area**

`CREATE` `src/pydelity/review.py` (name to approve, see Plan Notes), a code
module that defines `ReviewIssue` and the check-failure models for both steps;
it adds no output file. `surveying/schemas.py`, `surveying/validators.py`,
`surveying/survey.py` (imports); `pipeline/schemas.py`; `pipeline/runner.py`;
`utils/coroutines.py`; `report/html.py` (imports).

**Expected Outcome**

- `ReviewIssue` lives in `review.py` with `step` (`survey` or `extraction`),
  `check`, `message`, `details`, `page_index` and a required, nullable
  `item_id`. `pdf_survey.json` and `run.json` use it, and `surveying` and
  `pipeline` import it from there.
- `RunStatus` gains `paused`. `StepRecord` gains `pages` (`PageCounts`:
  `selected`, `extracted`, `reused`), `null` for the survey. The runner builds
  one `StepRecord` per step from per-step state instead of survey-only fields.
- `warn` records the step that was running (a context variable the runner sets),
  so `warnings[].step` names it.
- After the PDF is opened and before the output folder is prepared, a page
  number past the PDF raises `ConfigError` naming `pages` and the page count, in
  `run` and `estimate`. `extract` gets the same check in DEV-011.
- Survey-only runs otherwise behave as before.

**Self-Check**

Lint as in DEV-001; unaffected tests; a stand-in survey run whose `run.json` has
one survey record, review issues with `step` and `item_id: null`, and warnings
attributed to `survey`; `pages: "99"` on a 6-page PDF stops before `run.json` is
written, from `run()` and from `estimate()`.

Evidence, 2026-11-19, repo root, on `458d1f6` plus the uncommitted DEV-001 and
DEV-002 changes (macOS arm64, Python 3.13.9).

- `uv sync --locked`, run outside the sandbox because uv's cache is in
  `~/.cache/uv`: the strict editable install links only the files that existed
  when it was built, so the new `review.py` needed it. It rebuilt only pydelity.
- `.venv/bin/ruff check scripts src`, `ruff format`, `ty check scripts src`: all
  passed; `interrogate scripts src`: 100%.
- `.venv/bin/python -m pytest -q --numprocesses auto`: 100 passed, the same 5
  failed as after DEV-001 (top-level `instructions`), none new. `ty check tests`:
  the same 2 errors as after DEV-001. Doctests: 18 passed, 1 skipped.
- Reference pages regenerated and formatted as in DEV-001 (Prettier outside the
  sandbox): only `reference/run-json.md` (`paused`, `steps[].pages`,
  `review[].item_id`, `review[].step` with `extraction`) and
  `pdf-survey-json.md` (`issues[].item_id` and `step`) changed.
- Scratchpad `dev002_run_check.py` (the stand-in provider, the 1965 scan and its
  canned answer, temporary folders): 16 of 16 checks passed.
  - A new survey in a folder holding another PDF's `pdf_facts.json`, with a
    language the survey's check rejects (`check_retries: 0`) and a tiny
    `max_cost` allowed: `run.json` is `completed` with one step record
    (`survey`, `completed`, `pages: null`, `error: null`, 1 request, outputs
    `pdf_facts.json` and `pdf_survey.json`, start before end); the
    `max_cost_exceeded` warning has `step: "survey"` and `other_pdf_in_folder`,
    issued before the step, has `step: null`; `review` equals
    `pdf_survey.json`'s one issue, with `step: "survey"` and `item_id: null`;
    `pydelity.load` reads it back.
  - The same settings again: the step is `reused`, with 0 requests and both
    outputs.
  - A model fault (HTTP 400 on every request): the run and its step are
    `failed`, the step's `error` is the run's `ProviderError` text, and its
    outputs are `pdf_facts.json` only.
  - A tiny `max_cost` declined: the run and its step are `stopped`.
  - `pages="2,5-99"` on the 6-page W-9: `run()` and `estimate()` raise
    `ConfigError` with
    `- pages: 2,5-99 goes past the last page; irs_form_w9.pdf has 6 pages`, and
    the output folder is not created; `pages="1-6"` is accepted.

**Implementation Notes**

- `review.py` also holds the survey's check and comparison names
  (`SurveyCheckName`, `SurveyComparisonName`, formerly `CheckName` and
  `ComparisonName` in `surveying/schemas.py`), because `ReviewIssue.check` needs
  them and `surveying/schemas.py` imports `review.py`. DEV-005 adds page
  extraction's names there. `CheckResult` stays in `surveying/schemas.py`,
  since its names are the survey's.
- The runner keeps a `_Step` per started step (outputs, transport, page counts,
  status, error, times). `_finish` ends a step still running as `failed` when
  the run failed and `stopped` otherwise; only the step that was running gets
  the error. Warnings carry the step from `running_step` in
  `utils/coroutines.py`, which replaces counting warnings by position.
- The page check (`_selected_pages`) lives in the runner and returns the
  selected page indexes, which DEV-009 to DEV-011 use. Its message follows
  `resolve_config`'s `N invalid setting:` form.

---

### DEV-003 — Spend control for page requests

`Status`: `PENDING` `Depends On`: `DEV-001` `Acceptance`:
`AC-028, AC-030, AC-058`

**Goal**

Make the ledger, prices and `max_cost` work for page requests: each step's own
model, images counted, and requests in flight reserved.

**Affected Area**

`providers/profiles.py` (image limits, image detail value, per-image token
figure), `providers/factory.py`, `providers/ledger_model.py`, `costs/budget.py`,
`costs/schemas.py`, `pipeline/runner.py` (cost per step).

**Expected Outcome**

- `ProviderProfile` holds each provider's image limits, the detail value to send
  and an upper-bound token figure per image (Anthropic 4,784). The OpenAI patch
  size is confirmed in OpenAI's current images guide and recorded with its
  source in the self-check evidence.
- `LedgerEntry` gains required `page_index` and `agent`, both `null` for the
  survey. `LedgerContext` carries the step, page and agent, and a request is
  priced with its own step's resolved model.
- `LedgerModel` counts each image at the profile's figure in a request's bound,
  reserves the bound with `SpendGuard` before sending, and releases it after the
  ledger line is written or on any error or cancellation.
- `SpendGuard` lets a request through only when recorded spend plus reservations
  plus its bound stays within `max_cost`, or the run's decision is yes. It still
  asks once per run. The plan-time check uses the expected cost, and
  `CostEstimate.over_max_cost` follows. `StepEstimate` gains `pages`.
- `build_model` takes a step's `ModelChoice` and builds one provider client per
  step; a ledger wrapper is made per page and agent.
- `RunCost.by_step` and the summary report each step and the total.

**Self-Check**

Lint as in DEV-001; unaffected tests; a scratchpad script that sends many
concurrent requests through `LedgerModel` over a PydanticAI `FunctionModel` with
a small `max_cost`, and shows that recorded spend plus reservations never passes
it without the decision, that a canceled request releases its reservation, and
that an image adds the profile's tokens to the bound; a stand-in survey run
whose ledger line has `page_index` and `agent` set to `null`.

---

### DEV-004 — Upright page images, box mapping and figure crops

`Status`: `PENDING` `Depends On`: `DEV-003` `Acceptance`:
`AC-009, AC-011, AC-013, AC-058`

**Goal**

Render the image each page request carries, upright and as large as the
providers use, and map the model's grid boxes back to points on the displayed
page.

**Affected Area**

`CREATE` `src/pydelity/extracting/__init__.py` and
`src/pydelity/extracting/rendering.py` (name to approve, see Plan Notes).

**Expected Outcome**

- One page image per request: the displayed page turned clockwise by the page's
  rotation, JPEG quality 90, no alpha, at the largest zoom that fits every
  provider profile's limits and 300 DPI (about 2,180 px on the long edge for
  Letter or A4).
- Grid-to-points mapping by the design's table for rotations 0, 90, 180 and 270,
  clamped to the page and rounded to 0.01, and the inverse for form-field hints.
- Figure crops: the box mapped to unrotated page coordinates, rendered at 200
  DPI, turned upright, as PNG bytes.
- Every PyMuPDF call in step 2 goes through one shared worker thread, one call
  at a time, never on the event loop.

**Self-Check**

Lint; a scratchpad script on scratch copies of a test PDF with rotation
attributes 90, 180 and 270 and on CAPS's sideways pages: image sizes and
Anthropic tile counts within the limits; the images, viewed, are upright; text
spans' PyMuPDF boxes sent through the inverse and forward mappings land within 1
pt of where they started; crops are upright and cover their box.

---

### DEV-005 — Page answer, verdict, page file and structural checks

`Status`: `PENDING` `Depends On`: `DEV-002, DEV-004` `Acceptance`:
`AC-007, AC-008, AC-010, AC-012, AC-014, AC-016, AC-017, AC-018, AC-020, AC-021, AC-056`

**Goal**

Define what the model answers and what a page file holds, and check answers in
code wherever code can decide.

**Affected Area**

`CREATE` `src/pydelity/extracting/schemas.py` and
`src/pydelity/extracting/validators.py`; `schema_versions.py`
(`PAGE_SCHEMA_VERSION = "1.0"`); `review.py` (check names).

**Expected Outcome**

- `PageAnswer`, `AnswerItem` and its parts, `AnswerContainer`, `VerifierVerdict`
  (passed means no problems and no correction; not passed means at least one
  problem) and `VerifierProblem`, as the design gives them. Pydantic checks
  types and enum values only.
- `PageContext` (direction, rotation, repeated lines with their classification,
  labels, languages, instructions, form fields, page facts). The step builds it
  in DEV-009.
- `PageFile`, `Item`, `Container` and `ExtractionCheckResult` with field
  docstrings. An answer turns into items with Python-assigned IDs
  (`p<NNNN>-<nnn>`, `<item id>.<k>`, `p<NNNN>-c<nn>`) and point boxes, and the
  same answer always gives the same items.
- Checks 1–9 (`labels` to `form_fields`) with messages that name the item ref,
  and the `no_matching_label` issue. A one-figure page passes every check.
- No document type, language-specific word or default direction anywhere in the
  code.

**Self-Check**

Lint; a scratchpad script with hand-written answers that pass and fail each
check, `reading_order` for `ltr`, `rtl` and `ttb` with both `column_order`
values, table spans and row widths with rowspans, a one-figure page, and the
same answer turned into items twice with identical results; a search of
`extracting/` for language, script and document-type words.

---

### DEV-006 — Text layer and text comparison

`Status`: `PENDING` `Depends On`: `DEV-004, DEV-005` `Acceptance`:
`AC-022, AC-023`

**Goal**

Read a page's text-layer lines and find text the answer dropped or added, in any
script.

**Affected Area**

`CREATE` `src/pydelity/extracting/text_layer.py` (name to approve, see Plan
Notes); `extracting/validators.py` (`text_dropped`, `text_added`, the comparison
status).

**Expected Outcome**

- Text-layer lines read on the PyMuPDF worker with the probe's text flags.
  Normalization by NFKC, case folding and Unicode categories `L*`, `M*` and `N*`
  only.
- `text_dropped` and `text_added` by character trigrams as the design states,
  with the reversed-line match and the retry message that allows keeping a
  reading not visible on the page or read from an image.
- `text_comparison` is `compared`, `no_text_layer`, `garbled_text_layer` or
  `text_layer_mismatch`, and the comparison is skipped for the last three.

**Self-Check**

Lint; a scratchpad script on the Arabic, Simplified Chinese, Japanese and an
English test page: an answer built from the page's own lines passes, removing a
line of at least 5 letters or digits fails `text_dropped`, and adding one fails
`text_added`; the 1965 scan is `no_text_layer`. Thresholds stay at the design's
values unless this shows they break the guarantee.

---

### DEV-007 — Extractor and verifier prompts, agents and requests

`Status`: `PENDING` `Depends On`: `DEV-003, DEV-005, DEV-006` `Acceptance`:
`AC-010, AC-017, AC-018, AC-020, AC-021, AC-023, AC-024, AC-033, AC-058, AC-060`

**Goal**

Ask the models for a page and for a verdict, with every check enforced through
retries, and turn provider failures into clear errors.

**Affected Area**

`CREATE` `src/pydelity/extracting/prompts.py`, `agents.py` and `llm.py`;
`errors.py` (`ExtractionError`).

**Expected Outcome**

- `PROMPT_VERSION = 1` and two `PromptPair` functions written for pydelity. They
  take a piece of KGForEdGlobal's extraction or validation prompt only when it
  holds for any PDF and fits pydelity's answer, and write the rest new. Before
  the step, the user sees which pieces are taken and which are new. The prompts
  carry the design's rules: reading order per direction, page furniture as
  `artifact`, text as printed, one entry per list item, spans and header rows,
  LaTeX, exact code whitespace, figures, fields, containers, captions and
  one-figure pages. `advanced.extraction.instructions` goes last, under a
  heading saying it comes from the user, only when set, to both agents.
- Request content: one text part starting `Page index <i> (page <i+1> of <n>)`
  with the page context and, for a `good` text layer, `<text_layer>` hints; the
  image (with `detail: "original"` for OpenAI); a `CachePoint`. The verifier's
  part adds the answer and the checks it still fails. Anthropic requests cache
  the instructions.
- Extractor and verifier agents whose output validators run every check (on
  `corrected` for the verifier) and raise `ModelRetry` with all failures while
  retries remain, and keep the last answer otherwise.
- `ExtractionError` for a refusal, running out of output tokens (naming
  `advanced.extraction.max_output_tokens`) or no usable answer. It and
  `ProviderError` name the page and the agent.

**Self-Check**

Lint; a scratchpad script with a PydanticAI `FunctionModel` that captures
requests (one image and no PDF, the first line, hints only on `good` pages,
instructions only when set, `detail` on OpenAI-shaped parts) and drives the
retry rule (a failing answer retried, the last one kept with its failures); a
search of the prompts for language, script, document-type and direction
defaults.

---

### DEV-008 — Stand-in provider for page requests, canned answers and a rotated test PDF

`Status`: `PENDING` `Depends On`: `DEV-007` `Acceptance`:
`AC-011, AC-045, AC-047`

**Goal**

Let page extraction run end to end without paying for model calls, with pages
answered in any order, and give the tests a real PDF with rotated pages.

**Affected Area**

`tests/fixtures/mock_providers.py`; `CREATE`
`tests/fixtures/extraction_answers/` (name to approve); `CREATE`
`tests/fixtures/pdfs/irs_w9_instructions_rotated.pdf` and its entry in
`tests/fixtures/pdfs/SOURCES.md` (source and name to approve).

**Expected Outcome**

- The stand-in routes each request to its page's extractor or verifier answer by
  the first text line and the instructions, whatever order concurrent requests
  arrive in, and accepts image parts in both providers' request formats.
- Canned extractor and verifier answers for the pages the smoke script and the
  self-checks use.
- A copy of `irs_w9_instructions.pdf` whose pages 2, 3 and 4 have rotation
  attributes 90, 180 and 270, made by a recorded PyMuPDF command, under 500 KB,
  with `SOURCES.md` saying how it was made.

The tests that use these are Tester's.

**Self-Check**

Lint, including `tests` for the changed files; the existing stand-in tests still
pass; `python -m tests.fixtures.mock_providers` answers a hand-made page request
in each provider's format; the rotated PDF opens with the expected rotations and
passes `check-added-large-files`.

---

### DEV-009 — Page extraction step

`Status`: `PENDING` `Depends On`: `DEV-002, DEV-007, DEV-008` `Acceptance`:
`AC-007, AC-008, AC-009, AC-011, AC-013, AC-014, AC-016, AC-017, AC-018, AC-019, AC-021, AC-024, AC-025, AC-031, AC-032, AC-033, AC-056, AC-057, AC-058`

**Goal**

Extract every selected page that has no valid matching page file, several at a
time, and write page files and crops safely.

**Affected Area**

`CREATE` `src/pydelity/extracting/extraction.py` (name to approve, see Plan
Notes); `utils/files.py` if temp-file cleanup needs the new folders.

**Expected Outcome**

- Page context resolved per page by the design's rules, so overlapping, gapped
  or out-of-PDF ranges and missing, repeated or unknown artifact IDs never fail
  the step.
- Each page file's fingerprint and `inputs` cover only that page's inputs. Valid
  matching page files are reused; damaged ones (not valid, another major
  version, or a named crop missing) are extracted again with a `damaged_output`
  warning; `overwrite` reruns every selected page.
- Page tasks run in an `asyncio.TaskGroup` under a semaphore of
  `concurrent_pages`: render and read text, extractor, verifier, apply the
  verdict (a correction that passes every check replaces the answer; otherwise
  each problem becomes a `verifier` issue), IDs and point boxes, crops, then the
  page file atomically, then stale crops removed, and one log line per page with
  its outcome and cost.
- On the first page error, the other tasks are canceled, no new page starts, and
  the error ends the step; written page files stay valid. Leftover temporary
  files in the output folder, `pages/`, `figures/` and `report/pages/` are
  removed at the start of a run.

**Self-Check**

Lint; a scratchpad script that calls the step against the stand-in on the
rotated PDF, the Arabic PDF and the W-9: page files and crops are written; a
second call makes no request; changing the extraction instructions reruns every
page, and changing one page's context reruns only that page; a corrupted page
file or a deleted crop is extracted again; the stand-in's log shows at most
`concurrent_pages` requests in flight; an injected fault on one page stops the
step, cancels the others and keeps the written pages; a cancel mid-run leaves no
temporary file.

---

### DEV-010 — Page extraction in runs: pause, estimate and run record

`Status`: `PENDING` `Depends On`: `DEV-002, DEV-003, DEV-009` `Acceptance`:
`AC-003, AC-004, AC-026, AC-027, AC-028, AC-029, AC-030, AC-031, AC-033`

**Goal**

Make a run go from the survey to page extraction, pause after a new survey, and
estimate, guard and record both steps.

**Affected Area**

`pipeline/runner.py`, `pipeline/schemas.py`, `costs/budget.py`
(`estimate_extraction`), `report/html.py` (the `paused` status only).

**Expected Outcome**

- `run_pipeline` runs the survey, then page extraction. With `pause` on, a run
  that wrote a new survey ends `paused` with extraction `skipped`, sends no page
  request, and its summary says how to continue (and, after `overwrite`, to
  leave it off or use `--overwrite --no-pause`). A run that reuses the survey
  goes straight on.
- `estimate_extraction` prices the pages to extract with both agents, expected
  and maximum. The run's estimate, the CLI question, the plan-time check and the
  API-key checks cover every step that will run, once, before the first request.
- `run.json` has a record per step with page counts, and review issues from the
  survey and then each selected page. A failed page ends the run `failed`, with
  `run.json` and the report written first.
- The summary lists each step's status and cost, the page counts, and review
  issues as `<step>, page <number>[, item <id>]: <message>`.

**Self-Check**

Lint; stand-in runs through `run()`: the defaults pause after a new survey and
the next run extracts; `pause=False` does both in one run; an extraction-only
change does not rerun the survey; a tiny `max_cost` warns and a no stops the
run; an injected page fault ends it `failed` with `run.json` written;
`estimate()` before and after the survey.

---

### DEV-011 — Python API and CLI for page extraction

`Status`: `PENDING` `Depends On`: `DEV-010` `Acceptance`:
`AC-001, AC-002, AC-004, AC-027, AC-029, AC-033, AC-040`

**Goal**

Let users run page extraction on its own from Python and through the CLI, and
read page files back.

**Affected Area**

`api.py`, `__init__.py`, `cli.py`, `pipeline/runner.py` (`run_extraction_step`,
`load_run`).

**Expected Outcome**

- `extract`/`aextract` reuse a valid matching survey or run it, then extract the
  selected pages. They never pause, write no `run.json` or report, return the
  selected pages' page files in page order, and check `pages` against the PDF as
  `run` does.
- `load(output_dir)` returns `RunResult.pages` from `pages/` in page order; a
  damaged page file raises `OutputError`.
- `RunResult`, `PageFile` and `ExtractionError` are exported from `pydelity`.
  Every public run, survey, extract, measure and estimate function turns
  PydanticAI's banner off before its first agent runs; importing pydelity still
  changes nothing.
- The CLI runs both steps with `-p` and `-np`, shows the summary and exits 1 on
  `ExtractionError`.

**Self-Check**

Lint; with the stand-in: `extract()`, `await aextract()`, `load()`, a damaged
page file, and the CLI with `-p 2-3 -np --yes`; no banner from the Python API in
a fresh environment. Then, with the user's go-ahead at that point, a small real
run with the user's keys (a few pages on Anthropic and on OpenAI) to confirm the
image detail, instruction caching, both answer schemas and the ledger, with the
spend recorded.

---

### DEV-012 — HTML report with extracted pages

`Status`: `PENDING` `Depends On`: `DEV-010` `Acceptance`: `AC-034`

**Goal**

Show each extracted page with its items so a person can check them.

**Affected Area**

`report/html.py`, `report/report.css`.

**Expected Outcome**

- Each extracted page's report image with every item's box drawn and numbered in
  reading order and every container drawn in its own style, beside the item list
  (number, ID, kind, role, label, content, a table with spans, field value,
  figure description and crop) and the page's verifier outcome.
- The review section lists issues under a heading per step, sorted by page
  within each step (the user's choice, 2026-11-19; `run.json` keeps one list).
- A review issue with an `item_id` links to that item's anchor, and the item's
  box is marked. Paused runs show the survey as now.

**Self-Check**

Lint; reports from stand-in runs and from the DEV-011 real run viewed in the
built-in browser, light and dark; links from issues land on their boxes; markup
in model text is shown, never run.

---

### DEV-013 — Probe follow-ups

`Status`: `PENDING` `Depends On`: `NONE` `Acceptance`:
`AC-035, AC-036, AC-037, AC-038`

**Goal**

Fix the probe defects 0.1.0 left open, which affect the facts page extraction
reads.

**Affected Area**

`surveying/probe.py`.

**Expected Outcome**

The rules under the design's **Follow-up fixes** for `AC-035` to `AC-038`,
without raising `PROBE_VERSION`.

**Self-Check**

Lint; scratchpad PDFs made with PyMuPDF (a checked checkbox without a normal
appearance, one broken widget among good ones, an all-off radio group with `/V`
set, letter-style page labels, indirect `/K` arrays, a capped walk, tagged pages
without text, an outline cycle); the probe on every test PDF before and after,
with only the expected differences.

---

### DEV-014 — Other follow-ups: transport, cache price, workflows, changelog

`Status`: `PENDING` `Depends On`: `NONE` `Acceptance`:
`AC-039, AC-041, AC-042, AC-043`

**Goal**

Close the remaining 0.1.0 follow-ups that are code or configuration.

**Affected Area**

`surveying/survey.py` or `surveying/llm.py` (transport), `costs/pricing.py`,
`.github/workflows/ci.yml`, `.github/workflows/docs.yml`, `CHANGELOG.md`,
`pyproject.toml`.

**Expected Outcome**

The rules under the design's **Follow-up fixes** for `AC-039`, `AC-041` and
`AC-042`; `CHANGELOG.md` links `c63d891`; `pyproject.toml` drops the `def cli`
exclusion and the `./src/pydelity/__init__.py` omit. The docs wording of
`AC-044` is Documenter's.

**Self-Check**

Lint, including zizmor; a stand-in survey run with a fault injected after the
PDF is sent records its transport; a `0` cache price prices as zero; the
stale-reference command run locally with an untracked generated page fails;
`docs.yml`'s plan command run locally shows a `node` error.

---

### DEV-015 — Wheel smoke test with page extraction and package description

`Status`: `PENDING` `Depends On`: `DEV-008, DEV-011` `Acceptance`:
`AC-047, AC-048, AC-049`

**Goal**

Show that the installed wheel runs the survey and page extraction on every CI
platform, and describe the release.

**Affected Area**

`scripts/smoke_installed_wheel.py`, `pyproject.toml` (description). The README
is Documenter's.

**Expected Outcome**

The smoke script runs the CLI and the Python API through the survey and page
extraction against the stand-in. The package description names surveying a PDF
and extracting its pages; the classifiers are unchanged.

**Self-Check**

`just build` (with `twine check --strict`) and the smoke script locally; CI's
wheel jobs on ubuntu, macOS and Windows after a push.

---

### DEV-016 — Reference pages for page extraction

`Status`: `PENDING` `Depends On`: `DEV-011` `Acceptance`: `AC-052`

**Goal**

Generate reference pages for everything new, so CI's staleness check covers
them.

**Affected Area**

`scripts/generate_reference_docs.py`; the generated pages under
`docs/src/content/docs/reference/`, with two new ones, `page-json.md` for
`pages/<NNNN>.json` and `extraction-checks.md` (names to approve).

**Expected Outcome**

The reference covers the new settings, CLI options and public functions, the
page file, the extraction checks and review-issue names, and the changed
`run.json` and `cost.jsonl` fields, all generated from the code.

**Self-Check**

`just docs-reference` twice with byte-identical output; `just lint`; `just docs-build`.
---

## Plan Notes

- Order: the steps run in number order, one at a time (`STEPWISE`). DEV-013 and
  DEV-014 depend on nothing and can move earlier if the user wants. Before each
  step, Developer lists the files and folders it will change or add and waits
  for the user's approval before changing any of them. Each step report ends
  with the next step's approach, files, checks and approvals.
- Names to approve with this plan (the design's candidates):
  `src/pydelity/review.py` (shared review issues), `src/pydelity/extracting/`
  `extraction.py` (the step), `rendering.py` (images, coordinates, crops and the
  PyMuPDF worker) and `text_layer.py`; output `pages/<NNNN>.json` and
  `figures/<item id>.png`; `tests/fixtures/extraction_answers/`;
  `tests/fixtures/pdfs/irs_w9_instructions_rotated.pdf` (a copy of the approved
  `irs_w9_instructions.pdf` with pages 2–4 at rotation attributes 90, 180 and
  270); reference pages `page-json.md` and `extraction-checks.md`. The names
  fixed by scope (`extracting/agents.py`, `llm.py`, `prompts.py`,
  `validators.py`, `schemas.py`) need no approval.
- Existing tests are Tester's, and Developer does not edit them. This cycle
  replaces parts of the contract that some of them assert or type-check against
  (the top-level `instructions` setting, `Profile.user_instructions`, the
  survey-only run record and ledger line, and more in later steps). So from
  DEV-001 on, some tests fail and `ty check` reports errors in `tests/` until
  Tester updates them in `TESTING`. Each step's evidence lists the tests it
  breaks and why; its self-check runs Ruff, ty and interrogate on `scripts src`
  and every test it does not break. The git hooks run ty over `tests/` on every
  Python commit. The user makes the commits and skips that hook for them
  (2026-11-19), so the cadence stays `AFTER_IMPLEMENTATION`.
- Real model calls: the self-checks use the stand-in provider and PydanticAI
  test models. The only planned real run is at the end of DEV-011, with the
  user's go-ahead and keys at that point and the spend recorded. No pydelity
  code reads the environment or changes behavior for tests.
- Not Developer's: `AC-044`, the README part of `AC-049`, `AC-051` and `AC-053`
  (Documenter); the tests of `AC-045` (Tester); `AC-046` and `AC-050` need no
  change, since CI's jobs and the release-please configuration stay as they are;
  `AC-054` (the user's review of real runs).
- Work moved out of a step to a later pipeline step goes in "Pushed to later
  steps" at the bottom of `artifacts/next_cycle_inputs.md`.
- Styles: `styles/universal.md`, the `tony` user style and `styles/python.md`;
  `styles/github-actions.md` for DEV-014, and `styles/html.md` and
  `styles/css.md` for DEV-012.
- Project references loaded: `NONE` (`.standards/project-references/developer/`
  does not exist).

<!-- STANDARDS
Artifact: DEVELOPMENT
Cycle: build-step-2-page-extraction-of-the-20261119T174118Z-0419318a
-->

# Development Plan

`Cycle`: `build-step-2-page-extraction-of-the-20261119T174118Z-0419318a` `Mode`:
`STEPWISE` `User Style`: `tony` `User Style Locked`: `true` `Status`: `COMPLETE`
`Verification Cadence`: `AFTER_IMPLEMENTATION` `Current Increment`: `NONE`

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
  failed as after DEV-001 (top-level `instructions`), none new.
  `ty check tests`: the same 2 errors as after DEV-001. Doctests: 18 passed, 1
  skipped.
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
  extraction's names there. `CheckResult` stays in `surveying/schemas.py`, since
  its names are the survey's.
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

`Status`: `DONE` `Depends On`: `DEV-001` `Acceptance`: `AC-028, AC-030, AC-058`

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

Evidence, 2026-11-19, repo root, on `458d1f6` plus the uncommitted DEV-001 to
DEV-003 changes (macOS arm64, Python 3.13.9).

- Provider image limits, read on 2026-11-19 by a web-fetch subagent from the
  official guides:
  - Anthropic, `https://platform.claude.com/docs/en/build-with-claude/vision`:
    for "Claude 4.7 and later models" the high-resolution tier allows a long
    edge of 2,576 px and 4,784 visual tokens; an image costs
    `ceil(width/28) x ceil(height/28)` tokens (28 x 28 px patches); older models
    shrink to 1,568 px and 1,568 tokens.
  - OpenAI, `https://platform.openai.com/docs/guides/images-vision` (redirects
    to `https://developers.openai.com/api/docs/guides/images-vision`): `detail`
    takes `low`, `high`, `original` and `auto`; patches are 32 x 32 px,
    `ceil(width/32) x ceil(height/32)`, times a 1.2 multiplier on the GPT-5.x
    models. `original` allows 10,000 patches and 6,000 px on GPT-5.4 and GPT-5.5
    and up to 65,535 px per side on GPT-5.6 and GPT-6-astra, with 30,000 patches
    per image at most; GPT-5.2, GPT-4.1 and older do not take `original`.
  - So `ProviderProfile` holds Anthropic 2,576 px, 4,784 patches of 28 px, no
    detail value and 4,784 tokens per image; OpenAI 6,000 px, 10,000 patches of
    32 px (the design asked Developer to confirm the patch size; it is 32, not
    28), `detail: "original"` and 12,000 tokens per image (10,000 x 1.2).
- `.venv/bin/ruff check`, `ruff format`, `ty check` on `scripts src`: passed;
  `interrogate`: 100%. Doctests: 19 passed, 1 skipped (adds
  `ProviderProfile.image_patches`).
- `.venv/bin/python -m pytest -q --numprocesses auto`: 98 passed, 7 failed. The
  5 from DEV-001, plus 2 that follow from this step's design rules, for Tester
  to update:
  `costs/test_budget.py::test_earlier_spend_counts_and_a_disallowed_run_stops_resumably`
  sets `max_cost` between the run's expected cost and its maximum and expects
  the up-front warning; the up-front check now uses the expected cost (design
  decision 12), and the request's own bound stays within `max_cost`, so no
  warning is issued.
  `test_cli.py::test_over_max_cost_warns_then_a_yes_completes_with_one_question`
  matches the old wording "plus this run's maximum makes"; the warning now says
  "plus what this run may still spend makes". `ty check tests`: the same 2
  errors as after DEV-001.
- Reference pages regenerated and formatted (Prettier outside the sandbox): only
  `reference/cost-jsonl.md` changed (`agent`, `page_index`, the new meaning of
  `request`). `python-api.md` does not list the estimate's fields, so it is
  unchanged.
- Scratchpad `dev003_spend_check.py` (`LedgerModel` over PydanticAI
  `FunctionModel`s that answer after 0.3 s, models priced at $1 and $5 per
  million tokens through `advanced.models`, `max_tokens` 10,000): 12 of 12
  checks passed.
  - A JPEG part adds 4,784 input tokens to an Anthropic request's bound and
    12,000 to an OpenAI one's.
  - Six concurrent page requests (one wrapper per page from `for_page`) with a
    bound of $0.0548 each and `max_cost` $0.20: at most 3 were in flight, 3 were
    sent and 3 refused with `BudgetExceededError`, the decision was asked once,
    nothing stayed held afterward, the recorded spend stayed under $0.20, and
    the 3 ledger lines carry `page_index` 0–2, `agent: "extractor"`,
    `request: 1` and `step: "extraction"`.
  - With a yes, all 6 were sent and the decision was asked once.
  - A request canceled while waiting held its $0.0548 bound and released it.
  - A provider HTTP 400 on page index 3 gives
    `ProviderError: anthropic:test-model: Bad image. The request was for extraction, page 4 (index 3), extractor.`
    and releases what it held.
  - `estimate_survey` on the 1965 scan (expected $0.24, maximum $2.55):
    `max_cost` between the two is not `over_max_cost`; below the expected cost
    is. The survey's `StepEstimate.pages` is `null`.
  - A stand-in survey run writes a ledger line with `page_index: null`,
    `agent: null` and `request: 1`.

**Implementation Notes**

- `build_model` takes the step's `ModelChoice` and its settings section
  (`advanced.survey` or `advanced.extraction`), which both hold `effort`,
  `max_output_tokens` and `request_timeout_seconds`. Passing the three values
  separately with the new `choice` made six parameters, over Ruff's limit of
  five.
- `LedgerModel.for_page(agent=..., page_index=...)` makes a wrapper per page and
  agent on the same provider model and client. `LedgerEntry.request` now counts
  per step, page and agent, since each wrapper counts its own requests; for the
  survey it means what it did.
- `SpendGuard.reserve` checks a request and holds its bound under one lock, and
  releases it when the block ends, after the ledger line is written. After a no,
  every later check raises `BudgetExceededError` without asking again, so
  concurrent page requests ask once per run, as the survey did.
- `ProviderError` from a page request names the page and the agent here, in
  `ledger_model.py`, rather than in DEV-007, because the ledger model already
  knows both.

---

### DEV-004 — Upright page images, box mapping and figure crops

`Status`: `DONE` `Depends On`: `DEV-003` `Acceptance`:
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

Evidence, 2026-11-19, repo root, on the user's DEV-003 commit plus the
uncommitted DEV-004 changes (macOS arm64, Python 3.13.9, PyMuPDF 2.1).

- `uv sync --locked` outside the sandbox, to link the new `extracting/` folder
  into the strict editable install.
- `.venv/bin/ruff check`, `ruff format`, `ty check` on `scripts src`: passed;
  `interrogate`: 100%. Doctests (`--doctest-modules src`): 21 passed, 1 skipped,
  including `grid_box_to_points` and `points_box_to_grid`.
- `.venv/bin/python -m pytest -q --numprocesses auto`: the same 7 failed and 98
  passed as after DEV-003; `ty check tests`: the same 2 errors. No test imports
  `extracting/` yet.
- PyMuPDF behavior checked first with scratchpad `probe_pymupdf.py` on
  `irs_w9_instructions.pdf`: `Matrix(z, z).prerotate(90)` turns the rendered
  image a quarter turn clockwise (the title then runs down the right side), so
  `prerotate(r)` with the profile's clockwise rotation gives the upright image.
  With the page's rotation attribute set to 90, a `get_pixmap` clip in
  displayed-page coordinates captures a span's text, and the same span's
  unrotated box captures other text, so PyMuPDF 2.1 takes the clip in
  displayed-page coordinates.
- Scratchpad `dev004_rendering_check.py`: 16 of 16 checks passed.
  - Sizes: Letter gives 1,688 x 2,184 px at 199 DPI upright (2,184 x 1,688 when
    turned), with 4,758 of Anthropic's 4,784 patches and 3,657 of OpenAI's
    10,000; A4 gives 1,624 x 2,296 px at 196 DPI (4,756 and 3,672 patches). An
    image 0.2% larger does not fit, so the size is the largest; a 300 x 200 pt
    page stops at 300 DPI. Anthropic's patch limit binds, as the design
    expected.
  - A scratchpad copy of `irs_w9_instructions.pdf` with pages 2, 3 and 4 at
    rotation attributes 90, 180 and 270, rendered with the rotation that undoes
    each (270, 180 and 90), gives the same 1,688 x 2,184 image as the original
    page rendered as is: for attribute 90 no sample differs; for 180 and 270 the
    mean difference is about 6 of 255 and 0.009–0.012% of samples differ by more
    than 128, which is anti-aliasing at a sub-pixel offset. Viewed, the
    attribute-180 page reads upright with its page number at the bottom right.
  - For 25 text spans on each of those pages, the grid box from the rotated copy
    equals the one from the original page (difference 0 units), and points to
    grid and back lands within 0.39 pt.
  - A crop of a span's displayed box with each rotation is a PNG of the box's
    size at 200 DPI within 2 px, such as 610 x 37 px for a 609 x 36 estimate;
    viewed, the attribute-270 crop reads upright.
  - CAPS page 0 (595 x 842 pt portrait, rotation attribute 0, text at 90
    degrees) rendered with rotation 90 gives a 2,296 x 1,624 px landscape image;
    viewed, its table reads upright, and a crop of the table's title reads
    upright.
  - Eight concurrent `call`s all ran on the thread `pydelity-pymupdf_0`.
    Rendering 7 pages concurrently took 0.89 s, and the event loop's longest
    pause was 0.138 s, about one page's rendering: PyMuPDF keeps Python's GIL
    while it renders, so the loop waits during each render even though the
    render runs on the worker thread. Next to model requests that take tens of
    seconds, this does not matter.

**Implementation Notes**

- Crops pass the item's displayed-page box to PyMuPDF's clip as it is, because
  PyMuPDF 2.1 takes the clip in displayed-page coordinates (see the evidence);
  mapping it back to unrotated coordinates first, as the design's rendering
  section describes, would clip the wrong area. The crop is still the item's
  box, upright, at 200 DPI.
- The largest zoom is found by halving a range 40 times, counting part pixels as
  whole, because the image only grows with the zoom.
- `PdfWorker` is an async context manager over a one-thread executor. `call`
  runs any function of the open PDF there, which DEV-006 uses for text-layer
  lines.

---

### DEV-005 — Page answer, verdict, page file and structural checks

`Status`: `DONE` `Depends On`: `DEV-002, DEV-004` `Acceptance`:
`AC-007, AC-008, AC-010, AC-012, AC-014, AC-016, AC-017, AC-018, AC-020, AC-021, AC-056`

**Goal**

Define what the model answers and what a page file holds, and check answers in
code wherever code can decide.

**Affected Area**

`CREATE` `src/pydelity/extracting/schemas.py` and
`src/pydelity/extracting/validators.py`; `schema_versions.py`
(`PAGE_SCHEMA_VERSION = "1.0"`); `review.py` (check names). Added with the
user's approval during the step (2026-11-19): `CREATE`
`src/pydelity/utils/text.py` and `MODIFY` `surveying/probe.py`, to share the
repeated-line normalization the `artifacts` check needs.

**Expected Outcome**

- `PageAnswer`, `AnswerItem` and its parts, `AnswerContainer`, `VerifierVerdict`
  (passed means no problems and no correction; not passed means at least one
  problem) and `VerifierProblem`, as the design gives them. Pydantic checks
  types and enum values only.
- `PageContext` (direction, rotation, repeated lines with their classification,
  labels, languages, instructions, form fields, page facts). The step builds it
  in DEV-009.
- `PageFile`, `Item`, `Container` and `ExtractionCheckResult` with field
  docstrings. Turning an answer into items moved to DEV-009 (the user's
  approval, 2026-11-19), where the page file is written.
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

Evidence, 2026-11-19, repo root, on the user's DEV-004 commit plus the
uncommitted DEV-005 changes (macOS arm64, Python 3.13.9).

- `uv sync --locked` outside the sandbox, for the new modules.
- `.venv/bin/ruff check`, `ruff format`, `ty check` on `scripts src`: passed;
  `interrogate`: 100%. Doctests: 21 passed, 1 skipped (`normalize_line` replaces
  the probe's `_normalize` example).
- `.venv/bin/python -m pytest -q --numprocesses auto`: the same 7 failed and 98
  passed as after DEV-003; `ty check tests`: the same 2 errors. No test used the
  probe's private `_normalize`.
- Moving the normalization: scratchpad code ran the old `_normalize` from
  `git show HEAD:src/pydelity/surveying/probe.py` beside the new
  `utils.text.normalize_line` on all 18 repeated lines the probe finds in the
  test PDFs; the old function, the new one and the stored `normalized` agree on
  every line.
- Reference pages regenerated and formatted (Prettier outside the sandbox): only
  `reference/run-json.md` and `pdf-survey-json.md` changed, where
  `review[].check` and `issues[].check` now list page extraction's names too.
- Scratchpad `dev005_checks.py`: 81 of 81 checks passed.
  - A hand-written two-column left-to-right page (page furniture, heading, text,
    a list with nested entries, a table with a column span and a row span, a
    figure and its caption, a formula, code with language `zxx`, a checkbox, a
    text field, a two-button radio group, a printed field without
    `fillable_name`, and an aside in a container) passes every check, and the
    checks run in the order `labels`, `content`, `languages`, `boxes`,
    `containers`, `captions`, `reading_order`, `artifacts`, `form_fields`.
  - One change at a time fails exactly the check meant to catch it, such as: a
    label not in the profile, a label for another role, `other` where a label
    fits, a container label not in the profile (`labels`); a ref used twice, a
    text item with a table, a formula without LaTeX, an empty list, a blank
    figure description, a checkbox without `checked`, and table rows covering 3
    and 4 columns, a row span past the last row, overlapping cells,
    `header_rows` 4 of 3, no cell text, no rows, a span of 0 (`content`); the
    tag `zz`, text without a language, figure text without a language
    (`languages`); a reversed box, a box reaching 1,010, three values, two items
    with one box (`boxes`; 1,004 passes); an unknown container, an item outside
    its container, two containers inside each other (`containers`; 15 units
    outside and a box inside a box pass); a caption without `caption_of`, of a
    missing item, of itself, and `caption_of` on a body item (`captions`);
    dropping the page furniture or giving it role `body` (`artifacts`); a
    checkbox state or text value that differs, a radio group with one item or
    both buttons on, a field item naming a field the page lacks, a missing form
    field (`form_fields`). Whitespace in text values and the order of a radio
    group's buttons do not matter.
  - Reading order: right-to-left columns pass on an `rtl` page and fail on an
    `ltr` one; left-to-right columns pass on `ltr` and fail on `rtl`; three
    right-to-left columns pass; a jump back up within one column fails. On a
    `ttb` page, a missing `column_order` fails; two bands of columns read
    `right_to_left` pass and the same order declared `left_to_right` fails;
    columns read left to right pass with `left_to_right`. `column_order` on an
    `ltr` page fails. An aside anywhere in the order passes.
  - The label `other` on a heading list, which no profile label fits, passes and
    gives one `no_matching_label` issue (`step: "extraction"`, page 2, role
    `heading`, kind `list`).
  - A page that is one figure with a full-page box passes every check.
  - `check_results` keeps the check order and the attempts; `retry_message`
    lists each failure on its own line with the item refs; `review_issues` names
    each item's ID from the ref map (`p0002-003`, `p0002-007`); the same answer
    gives the same failures.
  - `VerifierVerdict` accepts passed with nothing else and failed with problems,
    with or without a correction; it rejects passed with a problem or a
    correction, and failed with no problem.
  - The JSON schemas of `PageAnswer` and `VerifierVerdict` have field
    descriptions and no patterns, bounds or length limits.
  - A search of `extracting/*.py` for the survey tests' document-type words,
    language and script names, form names, "left column", "right column",
    KGForEdGlobal, "step 2", `DEV-0` and `AC-0` finds nothing. The process
    wording grep of the changed files finds only "cycle" in its graph sense.

**Implementation Notes**

- A failure about one item or container puts its ref in
  `CheckFailure.details["item_ref"]`, and `review_issues` maps it to the ID that
  DEV-009 assigns, so `CheckFailure` stays shared with the survey.
- `labels` also checks that a container's label is in the profile; the design
  names the rule for items only, and a container's label is from the profile
  too. The label `other` passes on any item no other label fits, and
  `unmatched_labels` records those for review.
- `form_fields` compares a field the PDF has several times on the page, such as
  a radio group's buttons, as a group: as many field items as widgets, with the
  same checked states or values in any order. A field item naming a fillable
  field the page does not have also fails.
- In `reading_order`, a horizontal page compares top edges, and left edges on
  `ltr` pages or right edges on `rtl` pages, where columns line up; a vertical
  page compares right edges for `right_to_left` columns and left edges for
  `left_to_right` ones.
- The field-item type is `FieldItemType`, to keep it apart from the survey's
  `FieldType` of PDF form fields.

---

### DEV-006 — Text layer and text comparison

`Status`: `DONE` `Depends On`: `DEV-004, DEV-005` `Acceptance`: `AC-022, AC-063`

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

Evidence, 2026-11-19, repo root, on the user's DEV-005 commit plus the
uncommitted DEV-006 changes (macOS arm64, Python 3.13.9, PyMuPDF 2.1).

- `uv sync --locked` outside the sandbox, for the new module.
- `.venv/bin/ruff check`, `ruff format --check`, `ty check` on `scripts src`:
  passed; `interrogate`: 100%. Doctests: 23 passed, 1 skipped (adds
  `comparison_form` and `trigrams`).
- `.venv/bin/python -m pytest -q --numprocesses auto`: the same 7 failed and 98
  passed; `ty check tests`: the same 2 errors.
- Scratchpad `dev006_experiment.py` compared ways to decide which text-layer
  line the answer is missing, removing each line of 5 or more letters or digits
  in turn from an answer made of the page's own lines joined five to a
  paragraph:
  - Handing the answer's runs to the text-layer lines in reading order, a
    literal reading of the design's consumption rule, caught 25 of 53 removals
    on the Arabic page, 42 of 43 on the Chinese, 12 of 15 on the Japanese and 15
    of 124 on the English (`irs_w9_instructions.pdf` page 2): a removed line
    whose runs also occur elsewhere takes later lines' runs, and the shortfall
    spreads thin.
  - Counting a run as found when it occurs in the answer at all caught 7, 40, 10
    and 0.
  - Handing the missing runs out one line at a time, each time to the line that
    misses the largest share of its own, caught 53, 43, 14 and 123. In the two
    other cases a near or exact copy of the removed line was flagged instead, so
    every removal still failed the check.
  - None of the three flagged anything on the correct answers, and all caught
    every added line.

  The checks use the last rule (see Implementation Notes).

- Vertical Japanese: PyMuPDF stores each character of the gazette's columns as a
  line of its own (222 lines, 216 of one character, direction `(0, 1)`), so only
  3 lines were long enough to judge. `read_lines` joins pieces that continue one
  another along their writing direction, which gives 26 lines, the longest 45
  characters, 15 of them long enough to judge.
- Scratchpad `dev006_checks.py` (lines read through `PdfWorker`): 29 of 29
  checks passed.
  - On the Arabic and Simplified Chinese page 1, the vertical Japanese page and
    the English page, an answer made of the page's own lines is `compared` with
    no text failure.
  - Removing each line of 5 or more letters or digits makes `text_dropped` fail
    every time: Arabic 53 of 53, Chinese 43 of 43, Japanese 15 of 15, English
    124 of 124, and the failure names the removed line itself in all but one
    English case, where it names a near-identical line.
  - Adding each such line from the next page of the same PDF as a new item makes
    `text_added` fail naming that item: Arabic 133 of 133, Chinese 137 of 137,
    English 118 of 118; an added Japanese line is caught too.
  - Text quality `none`, `garbled` or no lines gives `no_text_layer` or
    `garbled_text_layer`, and the 1965 scan has no text-layer lines; an Arabic
    answer against the English text layer is `text_layer_mismatch`; none of
    these sends anything back.
  - Arabic lines stored reversed, as visual order stores them, are found by
    their reversed text, both ways.
  - A text-layer line written twice in the answer fails `text_added` once,
    naming the second copy.
  - Figure text, a field value and formula text that the text layer lacks are
    not flagged.
  - `run_checks` gives all 11 checks with the text checks last; `retry_message`
    ends with the note that the model may keep text not visible on the page or
    read from an image, and leaves it out when no text check failed; long lines
    are cut in messages.
- `dev005_checks.py`, rerun with empty text-layer lines for the new `run_checks`
  argument: 81 of 81. On its first rerun it caught a form name in a
  `text_layer.py` doctest example, now neutral text.

**Implementation Notes**

- Which lines miss their runs: the runs the lines hold beyond what the other
  side has are missing, and they are handed out one line at a time to the line
  that misses the largest share of its own runs, ties to the later line. This
  keeps the design's runs of three characters, its half-found threshold, its
  3-run minimum, the reversed match and its exclusions, and changes only how
  missing runs are shared out among lines. The design's rule as written met its
  own guarantee on none of the four pages (see the evidence). The same rule
  serves both checks; for `text_added` it still counts a repeated line against
  its last copy, as the design's reading-order rule did.
- `read_lines` joins stored lines that continue each other along one writing
  direction: same direction, lined up across it, with a gap of at most two line
  thicknesses. That turns vertical text stored a character at a time into lines,
  and joins a horizontal line stored in pieces, while the lines of a paragraph
  or of sideways text, which sit side by side, stay apart.
- `run_checks` takes the page's text-layer lines as a third argument, so they
  are not stored in each page file's context.
- The text flags are a copy of the probe's private `_TEXT_FLAGS`, since
  `probe.py` was not in this step; DEV-013, which changes `probe.py` anyway, can
  move both to one shared place if the user wants.

---

### DEV-007 — Extractor and verifier prompts, agents and requests

`Status`: `DONE` `Depends On`: `DEV-003, DEV-005, DEV-006` `Acceptance`:
`AC-010, AC-017, AC-018, AC-020, AC-021, AC-033, AC-058, AC-060, AC-063, AC-064`

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

Evidence, 2026-11-19, repo root, on the user's DEV-006 commit plus the
uncommitted DEV-007 changes (macOS arm64, Python 3.13.9, PydanticAI 2.69).

- PydanticAI research in the installed package: the OpenAI Responses model sends
  `BinaryContent.vendor_metadata["detail"]` as the image's `detail` unchanged
  (`binary_content_to_response_content`), so `"original"` reaches OpenAI;
  Anthropic caches the instructions with the model setting
  `anthropic_cache_instructions`; a refusal raises `ContentFilterError` only for
  a response with no text and `finish_reason` `content_filter`.
- `uv sync --locked` outside the sandbox, for the new modules.
- `.venv/bin/ruff check`, `ruff format --check`, `ty check` on `scripts src`:
  passed; `interrogate`: 100%. Doctests: 23 passed, 1 skipped.
- `.venv/bin/python -m pytest -q --numprocesses auto`: the same 7 failed and 98
  passed; `ty check tests`: the same 2 errors.
- Reference pages regenerated and formatted: only `reference/cli.md` changed,
  its exit code 1 now naming page extraction errors.
- Scratchpad `dev007_check.py` (`ask_extractor` and `ask_verifier` over
  `LedgerModel`s wrapping PydanticAI `FunctionModel`s that answer scripted JSON,
  on a page context with rotation 90, writing direction `rtl`, a repeated line,
  a checkbox, a push button and two text-layer lines): 32 of 32 checks passed.
  - A failing answer (label not in the profile) is sent back with a message that
    names item `'t1'`, and the fixed answer is kept: 2 attempts, no failures,
    and two ledger lines with `agent: "extractor"`, `page_index: 3`, `request` 1
    and 2. With `check_retries` 0 the failing answer is kept with its `labels`
    failure.
  - The request content is the page text, one JPEG image and a cache point, with
    no PDF; the text starts `Page index 3 (page 4 of 9)` and gives the
    direction, the rotation applied, the repeated line with what the survey
    found, the checkbox with its grid box (not the push button) and, on a `good`
    page only, the `<text_layer>` hints.
  - Anthropic requests carry `anthropic_cache_instructions` and an image without
    a detail value; OpenAI requests carry `detail: "original"` and no cache
    setting.
  - Page extraction instructions end the extractor's and the verifier's
    instructions, under the sentence saying they add to pydelity's rules.
  - The verifier gets the page text, the extraction as JSON and
    `Checks it still fails: none`; a passed verdict is kept (1 attempt, no
    correction); a correction that fails the checks is sent back with "Your
    corrected extraction does not pass every check" and the fixed one kept (2
    attempts); one still failing on the last attempt is kept as given with its
    failures; a verdict that breaks its own rules (passed with a problem) is
    sent back; verifier requests are recorded with `agent: "verifier"`.
  - A refusal, running out of output tokens and an answer that is not JSON each
    raise `ExtractionError` starting `Page 4 (index 3), extractor:`, the second
    naming `advanced.extraction.max_output_tokens`.
  - The extractor's instructions are the same for every page; a `ttb` page's
    text asks for `column_order`. The instructions run to 6,506 characters for
    the extractor and 8,508 for the verifier.
  - Neutral wording: the prompts and `prompts.py`, `agents.py` and `llm.py` hold
    none of the survey tests' document-type words, language or script names,
    form names, "left column before", KGForEdGlobal's schema names or
    "curriculum". The first run caught "slide" and "report" from that word list
    in the prompt text; they now read "a page made of a single picture" and
    "List only".
  - The rules describe all three writing directions, none as a default.
- Process wording grep of the changed files: no hits.

**Implementation Notes**

- KGForEdGlobal pieces taken, reworded (as approved before the step): the image
  as the source of truth; text exactly as printed, not completed; scanning every
  margin; ignoring drawn lines; tight, unique boxes; heading versus caption by
  role; content per kind; its table rules; list markers as printed; figure
  descriptions; text-layer hints for spelling only; the verifier's auditing
  stance, checklist and full correction. Everything else in the prompts is
  written for pydelity.
- `ask_extractor` and `ask_verifier` take a `StepModel` (the model, its choice
  and the settings, shared by a run's pages) and a `PageInput` (the page's
  context, image and text-layer lines); passing them as separate arguments made
  six or more parameters, over Ruff's limit of five. Each makes its own ledger
  wrapper with `LedgerModel.for_page`.
- `ask_verifier` returns the verdict as given and the checks its correction
  fails; DEV-009 decides whether the correction replaces the extraction.

---

### DEV-008 — Stand-in provider for page requests, canned answers and a rotated test PDF

`Status`: `DONE` `Depends On`: `DEV-007` `Acceptance`: `AC-011, AC-045, AC-047`

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

Evidence, 2026-11-19, repo root, on the user's DEV-007 commit plus the
uncommitted DEV-008 changes (macOS arm64, Python 3.13.9, PyMuPDF 2.1).

- `.venv/bin/ruff check` and `ruff format --check` on
  `scripts src tests/fixtures`, `ty check scripts src tests/fixtures`: passed;
  `interrogate scripts src tests`: 100%.
- `.venv/bin/python -m pytest -q --numprocesses auto`: the same 7 failed and 98
  passed; every existing stand-in test still passes.
- `prek run check-added-large-files` on the rotated PDF and the answers file:
  passed. `prek run markdownlint-cli2` on `SOURCES.md`: passed, after fixing a
  missing blank line before a separator in this plan, which markdownlint read as
  a heading.
- `python -m tests.fixtures.mock_providers --help` lists `--page-answers`.
- The rotated PDF: made by the command recorded in `SOURCES.md`; 187,076 bytes,
  7 pages with rotation attributes 0, 90, 180, 270, 0, 0, 0, the same text on
  every page as `irs_w9_instructions.pdf`, its 22 bookmarks and its structure
  tags. Saving without object streams gave 274 KB, so the command uses them.
  Running the command again changes only the second part of the trailer's file
  ID, so `SOURCES.md` records the committed file's hash and says so.
- Scratchpad `dev008_check.py` (pydelity's survey and `ask_extractor`/
  `ask_verifier` through the real Anthropic and OpenAI SDKs and `build_model`,
  sent to the stand-in with a 0.3-second delay per model request): 15 of 15
  checks passed.
  - For each provider, a survey of the 1965 scan gets the canned survey answer;
    then both pages are extracted at once, page 1 started first. Each page gets
    its own canned answer (20 items on the front, 11 on the back), which passes
    every check against the profile the survey made, and the verifier's `passed`
    verdict. The recorded requests carry `page_index` and `agent`: page 1 and
    page 0 for the extractor, then each for the verifier.
  - Anthropic requests carry an `image` block with a JPEG `base64` source and no
    `document`; OpenAI requests carry an `input_image` with a JPEG data URI and
    `detail: "original"` and no `input_file`. Two model requests were answered
    at the same time.
  - With no canned answer for page 1, its request gets HTTP 400 and pydelity
    raises
    `ProviderError: anthropic:claude-opus-5-5: No extractor answer for page index 1 (mock provider). The request was for extraction, page 2 (index 1), extractor.`
  - Hand-made requests: an Anthropic page request gets the extractor's first
    answer, then its second, which then repeats; an OpenAI request holding "The
    extraction to review:" gets the verifier's answer; a request naming no page
    gets the survey answer.

**Implementation Notes**

- The stand-in tells a page request by the `Page index N (` line pydelity's
  prompts start the page text with, and the verifier by the "The extraction to
  review:" heading only its requests hold. Changing either in
  `extracting/prompts.py` means changing `tests/fixtures/mock_providers.py` too.
- `page_answers` takes one answer or a list per page and agent, as
  `read_page_answers` reads them from a JSON file keyed by page index, so a test
  can script retries. A page request without an answer gets HTTP 400 rather than
  the survey queue, so a routing mistake fails loudly.
- `RecordedRequest` gains `agent` and `page_index`, and `MockProviders` gains
  `max_in_flight`, the most model requests it answered at the same time, which
  DEV-009 uses to show the concurrency limit holds.
- The canned answers describe the blank 1965 form as printed: headings,
  instruction text, empty fields and unmarked checkboxes, and the dependents
  table with its header row and two empty rows.

---

### DEV-009 — Page extraction step

`Status`: `DONE` `Depends On`: `DEV-002, DEV-007, DEV-008` `Acceptance`:
`AC-007, AC-008, AC-009, AC-011, AC-013, AC-014, AC-016, AC-017, AC-018, AC-019, AC-021, AC-025, AC-031, AC-032, AC-033, AC-056, AC-057, AC-058, AC-064`

**Goal**

Extract every selected page that has no valid matching page file, several at a
time, and write page files and crops safely.

**Affected Area**

Approved by the user before the step (2026-11-19): `CREATE`
`src/pydelity/extracting/extraction.py`; `MODIFY` `utils/files.py`
(`write_bytes_atomic` for the PNG crops, which `write_text_atomic` now uses) and
`extracting/rendering.py` (one public `RENDERING_SETTINGS` in place of the three
private constants, so the page inputs record them). Added with the user's
approval after the review (2026-11-19): `MODIFY` `surveying/validators.py` (the
range rule made public as `covering_range`) and `report/html.py` (the page's
rotation by that rule).

**Expected Outcome**

- Page context resolved per page by the design's rules, so overlapping, gapped
  or out-of-PDF ranges and missing, repeated or unknown artifact IDs never fail
  the step.
- An answer turns into items with Python-assigned IDs (`p<NNNN>-<nnn>`,
  `<item id>.<k>`, `p<NNNN>-c<nn>`) and point boxes, and the same answer always
  gives the same items (moved here from DEV-005).
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
  files in `pages/` and `figures/` are removed when the step starts. The runner
  builds the step's model and calls the step in DEV-010, which also clears
  `report/pages/` at the start of a run.

**Self-Check**

Lint; a scratchpad script that calls the step against the stand-in on the
rotated PDF, the Arabic PDF and the W-9: page files and crops are written; a
second call makes no request; changing the extraction instructions reruns every
page, and changing one page's context reruns only that page; a corrupted page
file or a deleted crop is extracted again; the stand-in's log shows at most
`concurrent_pages` requests in flight; an injected fault on one page stops the
step, cancels the others and keeps the written pages; a cancel mid-run leaves no
temporary file.

Evidence, 2026-11-19, repo root, on the user's DEV-008 commit (`3f356b0`) plus
the uncommitted DEV-009 changes (macOS arm64, Python 3.13.9, PyMuPDF 2.1).

- `uv sync --locked` outside the sandbox, for the new module.
- `.venv/bin/ruff check`, `ruff format --check`, `ty check` on `scripts src`:
  passed; `interrogate`: 100%. Doctests: 23 passed, 1 skipped.
- `.venv/bin/python -m pytest -q --numprocesses auto`: the same 7 failed and 98
  passed as after DEV-003; `ty check tests`: the same 2 errors. The tests of
  `write_text_atomic`'s callers still pass with it writing through
  `write_bytes_atomic`.
- Scratchpad `dev009_check.py`: 48 of 48 checks passed. Each scenario surveys
  its PDF through the stand-in with an answer built from the PDF's facts, then
  plans and extracts as the runner will (one `build_model` for the step, inside
  `running_step("extraction")`), with extractor answers built from each page's
  own text blocks, form fields, a figure and one page-wide container.
  - Rotated PDF (`irs_w9_instructions_rotated.pdf`, Anthropic,
    `concurrent_pages` 2): the profile's rotations are 0, 270, 180, 90, 0, 0, 0;
    7 page files and 6 crops written, at most 2 requests in flight; each file's
    fingerprint is its own inputs' fingerprint, and its inputs record the
    rendering settings; item IDs `p<NNNN>-<nnn>` in reading order and container
    `p<NNNN>-c01`, named by each item; every box inside the displayed page; on
    the pages with rotation attributes 0, 90, 180 and 270 the stored boxes are
    within 0.39 pt of the PyMuPDF text blocks they came from; each crop is
    `figures/<item ID>.png`, upright, 425 x 198 px for its 153 x 71 pt box at
    200 DPI, and `figures/` holds only the crops the files name.
  - Verifier: a passed verdict keeps the extraction; a correction that passes
    every check replaces it (page 1 lost its figure and crop) and its problems
    stay in the verdict only; problems without a correction become `verifier`
    issues, one naming `p0002-001` and one with no item; a correction that still
    fails `labels` after 3 verdicts is not kept, and the page file records its
    failing checks.
  - The canned answers for pages 2 and 3 follow the content stream, which jumps
    back up the page, and fail `reading_order` the same way on the unrotated
    `irs_w9_instructions.pdf`; the kept answer's issue names `p0002-027` with
    its ref in `details`. Text comparison ran on all 7 pages with no text
    failure.
  - One log line per page, such as
    `Page 1 (index 0): 25 items, 0 review issues, verifier passed; $0.05 for 2 requests`,
    and one plan line,
    `Page extraction: 7 pages selected, 0 reused, 7 to extract`. The 20 ledger
    lines carry their page and agent.
  - A second call reuses all 7 with no request. New extraction instructions or
    `overwrite` plan every page; a new request timeout plans none; a direction
    range for page 5 alone plans only page 5.
  - A page file made invalid JSON and a deleted crop give one `damaged_output`
    warning each
    (`0004.json is not valid: ...; extracting page 5 (index 4) again`;
    `pages/0006.json names the figure image figures/p0006-009.png, which is missing; ...`),
    and only those two pages are requested; the same answer gives identical
    items and containers.
  - `overwrite` at the default `concurrent_pages` 8: 7 requests in flight at
    most; page 0's new answer has no figure, so its old crop is removed after
    its new page file; page 5's items are byte-identical to the first run's.
  - A page without a canned answer (index 4, `concurrent_pages` 2): the
    `ProviderError` naming page 5 (index 4) is raised as itself, not as a group;
    page 6 is never requested; pages 0–3 stay valid; the next call extracts only
    pages 4, 5 and 6.
  - Canceling the step 2.6 s in (`concurrent_pages` 2, 0.5 s per request): pages
    0 and 1 written and valid, the rest canceled, no temporary file anywhere in
    the output folder.
  - Arabic PDF through OpenAI's format: 4 requests with `detail: "original"`,
    both pages `rtl`, text compared with no text failure, items tagged `ar`.
  - W-9 with pages 0 and 1 selected: page 0's context holds its 23 form fields
    and the others none; the 23 field items carry the form's names and values
    and `form_fields` passes; only `0000.json` and `0001.json` are written.
  - Page context on a profile with a range past the PDF, a reversed range and
    overlapping ranges: directions rtl, rtl, rtl, ttb, ttb, ltr, ltr and
    rotations 90, 180, 0, 0, 0, 0, 0 (first covering range inside the PDF, else
    the default or 0); a repeated line listed in two artifacts and as content is
    `artifact`, one listed only as content is `content`, the rest
    `unclassified`, and the unknown `R99` is ignored.
- Process wording grep of the changed files: only "supported", which matched
  "ported".

**Implementation Notes**

- `plan_pages(config, output_folder, page_indexes, survey)` gives a
  `PlannedPage` per selected page (inputs, fingerprint, the page file to reuse
  or `None`), which DEV-010's estimate can count before any request.
  `extract_pages(model, output_folder, pages, pdf_path)` takes a `StepModel`
  that the caller builds with `build_model`, extracts the pages without a page
  file, and returns every selected page's page file in order.
- Page context comes from `pdf_survey.json` alone: it holds the profile, the
  proposal and a copy of the facts the survey used, which match `pdf_facts.json`
  whenever the survey is reused. The PDF's SHA-256 in the inputs is the
  survey's.
- One range rule everywhere: `covering_range` in `surveying/validators.py`
  (formerly its private `_covering`) gives the first range inside the PDF that
  covers a page, and the survey comparison, `page_context` and the report's
  per-page "Rotation to make it upright" all use it. The review after the step
  found three copies, and the report's did not skip a range running past the
  last page, so on a survey whose rotation check still failed with such a range
  (such as 5-99 on a 7-page PDF) the report showed that range's rotation while
  page extraction and the survey comparison used another. Surveys whose checks
  pass cannot hold such a range.
- When a page fails, the task group cancels the others and the step re-raises
  the first error itself (`raise first from first.__cause__`), so callers see
  `ExtractionError`, `ProviderError` or `BudgetExceededError` rather than an
  exception group.
- A box that does not have four values (kept only when `boxes` still fails after
  the retries) is stored as the whole page, and a figure whose box has no width
  or height once kept inside the page is cut from the whole page, so every
  figure item still names a crop; the `boxes` issue stays on the page.
- `no_matching_label` issues gain `details.item_ids` beside the refs the check
  gives, since refs mean nothing outside the answer. `verifier` issues hold the
  problem's description as the message and its category and ref in `details`.
- A page's cost in its log line sums this step's ledger lines for that page,
  read from `cost.jsonl` after the page is written.
- Review after the step, at the user's request (2026-11-19), for correctness,
  contradictions and major repetition in `extraction.py`, `rendering.py` and
  `utils/files.py`: no code change. Checked against the design's page context,
  fingerprint, page file, crop, verifier and failure rules; the docstrings match
  the behavior. Scratchpad `dev009_review_probe.py`: with pages 0 and 1 both
  failing at `concurrent_pages` 4, one `ProviderError` is raised with no
  exception group in its traceback, and no temporary file is left. Left as they
  are: `_cost_of_page` formats spend as the survey's `_spent_since` does
  (sharing it means changing `costs/` and `surveying/survey.py`), and
  `plan_pages` warns about damaged page files, which an estimate that only plans
  would also do; DEV-010 decides that when it adds the estimate.
- The shared range rule, after the review (same day, same base): Ruff, ty and
  interrogate on `scripts src` passed; pytest: the same 7 failed and 98 passed;
  `ty check tests`: the same 2 errors; doctests: 24 passed, 1 skipped (adds
  `covering_range`'s example, where a range running past the last page is
  skipped). `dev009_check.py`: 48 of 48 again. Scratchpad
  `dev009_range_probe.py`, on the rotated PDF's survey with rotation ranges 90
  for pages 5-99, 270 for page 1 and 180 for pages 0-6: the report's rotation,
  page extraction's and the survey comparison's profile value agree on every
  page (180, 270, 180, 180, 180, 180, 180); before the change the report showed
  90 on pages 5 and 6. Process wording grep of the added lines: no hits.

---

### DEV-010 — Page extraction in runs: pause, estimate and run record

`Status`: `DONE` `Depends On`: `DEV-002, DEV-003, DEV-009` `Acceptance`:
`AC-003, AC-004, AC-026, AC-027, AC-028, AC-029, AC-030, AC-031, AC-033`

**Goal**

Make a run go from the survey to page extraction, pause after a new survey, and
estimate, guard and record both steps.

**Affected Area**

Approved by the user before the step (2026-11-19): `MODIFY`
`pipeline/runner.py`, `costs/budget.py` (`estimate_extraction`),
`extracting/extraction.py` (request sizes for the estimate) and `report/html.py`
(the `paused` status only, which needed no change: the report shows the status
and the skipped step as they are). `pipeline/schemas.py` already had `paused`
and `PageCounts`. Regenerated: `docs/src/content/docs/reference/cost-jsonl.md`.

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

Evidence, 2026-11-19, repo root, on the user's DEV-009 commit (`436b67f`) plus
the uncommitted DEV-010 changes (macOS arm64, Python 3.13.9).

- `.venv/bin/ruff check`, `ruff format --check`, `ty check` on `scripts src`:
  passed; `interrogate`: 100%. Doctests: 24 passed, 1 skipped. The git hooks
  other than ty pass on the changed files.
- `scripts/generate_reference_docs.py`, then Prettier through prek (outside the
  sandbox): only `reference/cost-jsonl.md` changed, listing the three new
  estimate figures.
- `.venv/bin/python -m pytest -q --numprocesses auto`: 86 passed, 19 failed: the
  7 from DEV-001 and DEV-003, and 12 that follow from this step's design rules,
  for Tester to update:
  - Ending `paused` after a new survey, where they expect `completed`
    (`AC-003`):
    `providers/test_ledger_model.py::test_fewer_temporary_failures_than_the_retries_still_complete`,
    `test_api.py::test_async_run_gives_what_run_gives_with_the_same_warnings`,
    `providers/test_uploads.py::test_a_file_the_provider_no_longer_has_is_uploaded_again_once`,
    `providers/test_uploads.py::test_a_failed_upload_falls_back_to_sending_the_pdf_in_the_request`,
    `pipeline/test_runner.py::test_a_failed_survey_saves_no_survey_and_its_spend_counts_next_time`,
    `pipeline/test_runner.py::test_no_output_file_holds_the_api_key`,
    `costs/test_budget.py::test_an_unpriced_model_without_max_cost_runs_and_records_no_price`
    and
    `test_cli.py::test_a_pdf_alone_runs_the_survey_with_keys_from_the_environment`.
  - A second run that reuses the survey now extracts the pages, and the stand-in
    has no page answers for the scan, so the page request gets HTTP 400
    (`AC-027`):
    `pipeline/test_runner.py::test_a_rerun_with_unchanged_survey_inputs_reuses_everything`
    and `report/test_html.py::test_page_images_are_rendered_only_when_missing`.
  - The summary names pages from 1 (`AC-026`, the design's CLI summary format):
    `surveying/test_survey.py::test_checks_still_failing_after_the_retries_are_listed_for_review`
    expects `survey, page 2: labels: a region on page 2`; the line now reads
    `survey, page 3: labels: a region on page 2` (see Implementation Notes).
  - The estimate after a saved survey covers page extraction (`AC-029`):
    `costs/test_budget.py::test_estimate_writes_nothing_and_a_reusable_survey_costs_nothing`
    expects 0.
- Scratchpad `dev010_check.py` (the stand-in, the rotated PDF, canned survey and
  page answers built as in `dev009_check.py`, page 2's verifier naming a
  problem): 32 of 32 checks passed.
  - Defaults: the first run ends `paused` with the survey `completed` and page
    extraction `skipped` (no page counts, outputs or requests), sends only the
    survey's request, estimates the survey only, writes `run.json` and the
    report, and its summary says
    `Paused after the new survey. Check pdf_survey.json and report.html, then run pydelity again to extract the pages, or pass --no-pause (pause=False in Python) to run every step at once.`
    A leftover temporary file in `report/pages/` is gone after the run.
  - The next run reuses the survey and extracts the 7 pages: the extraction
    record has pages 7 selected, 7 extracted, 0 reused, 18 requests (pages 2 and
    3 retry twice, as their canned answers fail `reading_order`), outputs
    `pages/` and `figures/` and no transport; the estimate is made there
    (`Extraction cost estimate: about $2.10, at most $36.66 (7 pages, up to 42 requests to anthropic:claude-opus-5-5)`);
    `review` holds the survey's 6 issues, then the pages' 3 in page order; cost
    by step is extraction $0.43; the summary reads
    `Run completed: survey reused, extraction completed (7 pages selected: 7 extracted, 0 reused); cost $0.43 this run (extraction $0.43), ...`
    and lists issues such as
    `extraction, page 3, item p0002-001: verifier: The box is too wide.`
  - A third run sends nothing, and page extraction is `reused` with the same
    review list. New extraction instructions with `pages="2-3"` reuse the survey
    and extract pages index 1 and 2 only.
  - `pause=False` (through `run_pipeline` with a counting confirmation): survey
    and extraction in one run, 19 requests, one question before the survey with
    an estimate of both steps (extraction for 7 pages), logged once.
  - A tiny `max_cost` after the paused survey: one `max_cost_exceeded` warning,
    attributed to `extraction`; without permission the run and the step end
    `stopped` before any page request; with `allow_over_max_cost=True` one
    warning for the whole run and every page extracted.
  - A page without a canned answer (`concurrent_pages` 2): the run ends `failed`
    with `run.json` and the report written, the step `failed` with the page's
    `ProviderError`, 4 pages counted as extracted, and the review holding the
    issues of pages 0–3; the error reaches the caller.
  - `estimate()`: before the survey, the survey only, or survey and extraction
    for 7 pages with `pause=False`; after the survey, the survey reused and 7
    pages ($2.10 expected, $36.66 at most); after the pages with one page file
    damaged, 1 page and no warning. Per page, the measured estimate is $0.30 and
    the allowance before the survey $0.31. `estimate()` writes and sends
    nothing.
  - With page extraction on OpenAI and no `OPENAI_API_KEY`, `pause=False` raises
    `MissingApiKeyError` with nothing sent; with the pause, the survey runs.
  - A damaged page file's `damaged_output` warning is attributed to `extraction`
    in `run.json`.
- `dev009_check.py` again: 48 of 48.
- Process wording grep of the added lines: no hits.

**Implementation Notes**

- The run keeps one `SpendGuard` for all its steps (`_Run.guard`), so it asks
  about `max_cost` at most once. Each step builds its model with `_step_model`,
  which also logs it; page requests get no PDF in their ledger context, so their
  bounds count no PDF pages.
- `_steps` runs the survey, then pauses (extraction recorded `skipped`, run
  `paused`) when the survey is new and `pause` is on, else runs page extraction.
  A new survey makes the estimate, question, plan-time check and page
  extraction's key check (`read_api_key`) for both steps when the run will not
  pause; a reused survey leaves them to page extraction, which skips them, and
  builds no model, when every page file is reused.
- The estimate is split into `estimate_survey` and `estimate_extraction`, which
  give one `StepEstimate` each, and `estimate_run`, which adds them up, decides
  `over_max_cost` and lists one warning per unpriced model.
  `estimate_extraction` uses each page's request sizes: measured from its
  context and prompts when the survey exists (`request_sizes`), and before the
  survey an allowance of 20,000 characters for the extractor and 24,000 for the
  verifier (`request_sizes_before_survey`; the measured requests are about
  15,000 and 19,000 with a small profile), plus the page's text-layer hints in
  both cases. An answer is 4,000 output tokens plus the page's text characters
  divided by 2, and a verdict 3,000.
- `plan_pages(quiet=True)` plans without warnings or the log line, for
  `estimate()`. `extract_pages(on_written=...)` reports each page file as it is
  written, so `run.json`'s page counts and review list are right when a page
  fails.
- The summary names pages from 1, but the survey's check and comparison messages
  from 0.1.x say "page 2" for page index 2, so a line can read
  `survey, page 3: labels: a region on page 2`. Rewording those messages to
  "page index 2" needs `surveying/validators.py`, which was not in this step's
  files.
- For DEV-012: the report's header shows `Model: None` when `model` is unset,
  which it is by default since DEV-001; it should name each step's model.

---

### DEV-011 — Python API and CLI for page extraction

`Status`: `DONE` `Depends On`: `DEV-010` `Acceptance`:
`AC-001, AC-002, AC-004, AC-027, AC-029, AC-033, AC-040`

**Goal**

Let users run page extraction on its own from Python and through the CLI, and
read page files back.

**Affected Area**

Approved by the user before the step (2026-11-19): `MODIFY` `api.py`,
`__init__.py`, `cli.py`, `pipeline/runner.py` (`run_extraction_step`,
`load_run`), `pipeline/schemas.py` (`RunResult.pages`) and
`surveying/validators.py` (the survey's messages name page indexes, so the
summary's 1-based page numbers no longer contradict them). Regenerated:
`docs/src/content/docs/reference/python-api.md`.

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

Evidence so far, 2026-11-19, repo root, on the user's DEV-010 commit (`ce66a4f`)
plus the uncommitted DEV-011 changes (macOS arm64, Python 3.13.9).

- `.venv/bin/ruff check`, `ruff format --check`, `ty check` on `scripts src`:
  passed; `interrogate`: 100%. Doctests: 24 passed, 1 skipped. The git hooks
  other than ty pass on the changed files.
- Reference pages regenerated and formatted: only `reference/python-api.md`
  changed, adding `extract` and `aextract` and the changed docstrings.
- `.venv/bin/python -m pytest -q --numprocesses auto`: 81 passed, 24 failed: the
  19 listed under DEV-010, and 5 that expect the survey's old wording "page N"
  where its messages now say "page index N" (the user's approval, 2026-11-19),
  for Tester to update:
  `surveying/test_validators.py::test_labels_check_finds_empty_repeated_kindless_and_unknown_labels`,
  `test_rotation_check_finds_ranges_outside_the_pdf_and_overlaps`,
  `test_writing_direction_check_finds_ranges_outside_the_pdf_and_overlaps`,
  `test_page_numbering_check_finds_ranges_outside_the_pdf_and_overlaps` and
  `surveying/test_survey.py::test_answers_that_differ_from_the_facts_are_kept_and_listed_by_page`.
  `ty check tests`: the same 2 errors.
- Scratchpad `dev011_check.py` (the stand-in and the canned answers of
  `dev010_check.py`): 16 of 16 checks passed.
  - `extract()` on a new folder runs the survey and the 7 pages (19 requests)
    with the default pause on, returns 7 `PageFile`s in page order, and writes
    `pdf_survey.json` and `pages/` but no `run.json` or report. Called again,
    and as `await aextract(pages="2-3")`, it sends nothing and returns the saved
    page files (indexes 1 and 2 for the second). `pages="99"` raises
    `ConfigError` naming `pages` before the folder is created.
  - `load()` returns the 7 page files in page order; an invalid page file raises
    `OutputError` (`0004.json is not valid: ...`), and so does a missing crop
    (`pages/0005.json names the figure image figures/p0005-033.png, which is missing; ...`).
  - `run()`: a paused run's `pages` is empty; `run(pages="1-3")` returns those 3
    page files, and `load()` gives the same.
  - CLI `pydelity <pdf> -p 2-3 -np --yes`: exit 0, both steps, page counts 2
    selected and 2 extracted, both estimates and the summary shown. A page
    answer that is not JSON: exit 1, `run.json` `failed` with
    `ExtractionError: Page 1 (index 0), extractor: the model gave no usable answer ...`.
  - Banner, in fresh Python processes without `CI`, `PYTEST_VERSION` or
    `PYDANTIC_AI_NO_BANNER`: a plain PydanticAI agent prints the banner (its
    `PYDANTIC_AI_NO_BANNER=1` line); importing pydelity leaves
    `pydantic_ai.BANNER_ENABLED` true; `pydelity.extract(...)` prints no banner
    and leaves the flag false.
- `dev009_check.py` 48 of 48 and `dev010_check.py` 32 of 32 again.
- Process wording grep of the added lines: no hits.
- Real run, by the user in their own terminal with their keys (no keys are set
  in this session's shell). Offline estimates first (`pydelity.estimate`,
  nothing sent): `irs_w9_instructions_rotated.pdf` pages 1-3 on the defaults,
  about $1.34 and at most $18.81; `irs_pub1_arabic.pdf` page 1 on
  `openai:gpt-6.2-astra`, about $1.11 and at most $15.83.
  - Anthropic
    (`pydelity tests/fixtures/pdfs/irs_w9_instructions_rotated.pdf -p 1-3 -np -mc 20 -v`,
    output in the session scratchpad's `real-anthropic/`): the survey completed
    (1 request, 31,896 input and 2,431 output tokens, $0.21); page 1's first
    extractor request was refused with HTTP 400:
    `anthropic:claude-opus-5-5: The compiled grammar is too large, which would cause performance issues. Simplify your tool schemas or reduce the number of strict tools. The request was for extraction, page 1 (index 0), extractor.`
    The run ended `failed`, with `run.json` (survey `completed`, extraction
    `failed`, 0 page requests recorded), the report and the error message
    written as designed. Spend: $0.21.
  - Cause: page extraction asks for `NativeOutput(PageAnswer)` and
    `NativeOutput(VerifierVerdict)`, which Anthropic enforces with a compiled
    grammar. Their JSON schemas hold 18 and 20 nullable fields (`anyOf` with
    null) against the survey answer's 1. Anthropic's structured outputs page
    (`https://platform.claude.com/docs/en/build-with-claude/structured-outputs`,
    read 2026-11-19 by a web-fetch subagent, partly from a model summary of the
    page) caps fields with union types, nullable ones included, at 16 per
    request across strict schemas, and optional fields at 24, beyond further
    internal grammar-size limits. The design's flat answer, with per-kind fields
    null when unused (decision 7), is over that cap; OpenAI was not run.
  - Routed to Architect as an `ARCHITECTURE` failure (see Suspended Assignment 1
    in Plan Notes).
  - OpenAI, first run
    (`pydelity tests/fixtures/pdfs/irs_pub1_arabic.pdf -p 1 -np -m openai:gpt-6.2-astra -mc 20 -v`,
    `real-openai/`): `completed`, $1.14 (survey $0.24, page $0.90 for 2
    extractor and 2 verifier requests); native output accepted both schemas; the
    second request of each agent read cached tokens (7,322 and 11,437). The
    page's text copied the PDF's stored text, broken ligatures and swapped
    letters included, with every text check passing; the design's decision 21
    answers this.
- Real runs again after DEV-017 (decisions 20 and 21), by the user, into new
  folders (`real-anthropic-2/`, `real-openai-2/`), 2026-11-19:
  - Anthropic, `irs_w9_instructions_rotated.pdf` pages 1-3 on the defaults:
    `completed`, $1.00 (survey $0.23; pages $0.77 for 7 requests: page index 1's
    extractor answered twice, each other agent once). Prompted output worked for
    the survey, the extractor and the verifier, where native output had been
    refused. Each request wrote the cache (survey 31,166 tokens, each page's
    first requests about 9,900 to 16,200); page index 1's second extractor
    request read 9,947 cached tokens and the verifiers of pages index 0 and 1
    read 6,186 each, written by the verifier of page index 2, which ran first;
    the first concurrent requests read none, as the design expects. All 3 pages
    pass every check (`compared`), the verifier passed each, 0 review issues,
    29, 28 and 27 items with 2 figure crops. On the pages with rotation
    attributes 0, 90 and 180 (rotations applied 0, 270 and 180), each item's box
    overlaps the union of the text-layer lines its text contains with a median
    IoU of 0.87, 0.90 and 0.78 (scratchpad measurement), so the boxes land on
    their content on rotated pages too.
  - OpenAI, `irs_pub1_arabic.pdf` page 1 on `openai:gpt-6.2-astra`: `completed`,
    $1.03 (survey $0.21; page $0.82 for 3 extractor answers and 1 verifier
    verdict, which passed). Cache reads on the second and third extractor
    requests (6,139 and 9,671 tokens). The page's text now follows the image:
    the text layer's `1 املنشور`, `. حق االطالع1` and
    `والتحدث إىل أحد املرشفني ...` are read as `المنشور 1`, `1. حق الاطلاع` and
    `والتحدث إلى أحد المشرفين ...`. Such lines fail `text_dropped` (the stored
    line) and `text_added` (the reading) after the retries, giving 11 review
    issues (6 and 5) that name the items, as the design's risk note expects.
  - Spend on real runs for DEV-011: $0.21 + $1.14 + $1.00 + $1.03 = $3.38.

**Implementation Notes**

- Every API function turns PydanticAI's banner off in `_resolve`, which each of
  them except `load` calls first; the CLI's own line went, since it calls the
  API.
- `run_extraction_step` runs `_steps` with `pause=False` and returns the
  selected pages' files; `_steps` now takes the pause, so `run_pipeline` passes
  the setting. `RunResult.pages` holds a run's selected pages' page files, and
  every page file in `pages/` when read back with `load()`, which also raises
  for a missing crop, as a damaged page file is defined.
- The survey's messages now say "page index N" and "page indexes 0-N", so a
  summary line reads `survey, page 3: labels: a region on page index 2 ...`.

---

### DEV-012 — HTML report with extracted pages

`Status`: `DONE` `Depends On`: `DEV-010` `Acceptance`: `AC-034`

**Goal**

Show each extracted page with its items so a person can check them.

**Affected Area**

Approved by the user before the step (2026-11-20): `MODIFY` `report/html.py`,
`report/report.css` and `pipeline/runner.py` (passing the selected pages' page
files to the report).

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

Evidence, 2026-11-20, repo root, on the user's commit `3e2c3cb` plus the
uncommitted DEV-018 and DEV-012 changes (macOS arm64, Python 3.13.9).

- `.venv/bin/ruff check`, `ruff format --check`, `ty check` on `scripts src`:
  passed; `interrogate`: 100%. Doctests: 26 passed, 1 skipped (new examples for
  `_box_style` and `_page_heading`).
- `.venv/bin/python -m pytest -q --numprocesses auto`: 81 passed, 24 failed, the
  same 24 as before. The two report tests among them fail before the report is
  written, for the reasons listed under DEV-010 (the extraction that now follows
  the survey has no stand-in answers) and DEV-001 (settings).
- Scratchpad `dev012_check.py`: 35 of 35 checks passed. It runs the stand-in on
  the rotated PDF's pages 1-3 with `pause=False`: page index 0 adds a table with
  a column span and a row span, a nested list, a code item, a formula with
  LaTeX, a caption, a second container and `<script>`/`onerror` markup in text,
  cells and the figure description; page index 1's verdict names an item, a
  container and no item, with no correction. It also runs a paused run, and
  writes reports for copies of `real-anthropic-2/` and `real-openai-2/` from
  their saved files with `load()`, `render_pages` and `write_report`, with no
  model call.
  - No `script`, `iframe` or `object` element and no `on*` attribute in any
    report; the markup shows as text.
  - Every in-page link lands on an element (173, 168 and 60 links). Each item
    has a numbered box and a list entry with anchors (81, 84 and 28 items), each
    container a box (4, 0 and 3), numbered in reading order on each page.
  - The items and containers that review issues name are exactly the marked
    boxes, and each is linked from the review tables (8 in the stand-in report,
    5 in the OpenAI one).
  - Figure crops are shown and present (3, 2 and 1). Tables keep their spans,
    lists their markers and nesting, a formula its LaTeX, a caption its link to
    the item it captions.
  - The header names the survey and page extraction models and never `None`; the
    review section has a heading per step in run order, page extraction issues
    sorted by page; each extracted page shows its verifier outcome (`passed`,
    `found 3 problems, listed for review`).
  - Pages with no page file and the paused run keep the survey's card, with no
    item boxes. Arabic item text carries `lang="ar"` and `dir="auto"`.
- Viewed in the built-in browser over a temporary local server on the scratchpad
  output (the repo has no preview configuration): the stand-in report at 1,400
  pixels in light (image beside the item list, a linked box highlighted, the
  table, list, code, formula, figure crop and escaped markup, the review tables)
  and in the narrow pane in dark (image above the list); the OpenAI Arabic page
  in dark (right-to-left item text and the figure crop); the Anthropic page with
  rotation attribute 90 in light (boxes on the sideways text columns). The first
  view showed the review tables' page and item links wrapping; they now stay on
  one line.
- `dev009_check.py` 48 of 48, `dev010_check.py` 32 of 32, `dev011_check.py` 16
  of 16, `dev017_check.py` 11 of 11 and `dev018_check.py` 7 of 7 again.
- Process wording grep of the added lines: only HTML's `scope` attribute.

**Implementation Notes**

- `write_report` takes one `ReportInputs` (facts, page images, output folder,
  the selected pages' page files, run record, survey), which keeps it within
  Ruff's argument limit; the runner builds it.
- An extracted page shows its items and containers instead of the survey's
  regions and form fields; other pages keep the survey's card. Every card's
  heading now reads `Page 1 (index 0)`, as the run summary counts pages.
- An item's issues show under its list entry; issues about the page or a
  container show under "Review issues about the page". A marked box shows `!` as
  well as its color, and a box links to its list entry.
- The header names the survey's model (from `pdf_survey.json`) and the page
  extraction model (from the page files), instead of the `model` setting, which
  is now `null` unless set.
- The stylesheet adds a dark color scheme; the colors drawn over page images
  stay the same in both, since the images are light.
- A report shows the issues saved in the page files it reads: the OpenAI run's
  page, written before DEV-018, still lists its 11 text issues.

---

### DEV-013 — Probe follow-ups

`Status`: `DONE` `Depends On`: `NONE` `Acceptance`:
`AC-035, AC-036, AC-037, AC-038`

**Goal**

Fix the probe defects 0.1.0 left open, which affect the facts page extraction
reads.

**Affected Area**

Approved by the user before the step (2026-11-20): `MODIFY`
`surveying/probe.py`, `utils/pdf.py` (public `TEXT_FLAGS`, the one place both
the probe and the text layer take their text extraction flags from, the user's
choice over two copies or the probe's own constant) and
`extracting/text_layer.py` (imports `TEXT_FLAGS` instead of its copy).

**Expected Outcome**

The rules under the design's **Follow-up fixes** for `AC-035` to `AC-038`,
without raising `PROBE_VERSION`.

**Self-Check**

Lint; scratchpad PDFs made with PyMuPDF (a checked checkbox without a normal
appearance, one broken widget among good ones, an all-off radio group with `/V`
set, letter-style page labels, indirect `/K` arrays, a capped walk, tagged pages
without text, an outline cycle); the probe on every test PDF before and after,
with only the expected differences.

Evidence, 2026-11-20, repo root, on the user's DEV-012 commit (`abb4829`) plus
the uncommitted DEV-013 changes (macOS arm64, Python 3.13.9, PyMuPDF 2.1).

- `.venv/bin/ruff check`, `ruff format --check`, `ty check` on `scripts src`:
  passed; `interrogate`: 100%. Doctests: 26 passed, 1 skipped (`_label_number`'s
  example now gives each label's style).
- `.venv/bin/python -m pytest -q --numprocesses auto`: 81 passed, 24 failed, the
  same 24 as before; the probe's own tests pass.
- Scratchpad `dev013/make_pdfs.py` writes the defect PDFs by setting their
  objects directly, and `dev013/dev013_check.py` checks them: 11 of 11 passed.
  The committed probe, run on the same PDFs, gets each case wrong: the form fact
  unreadable (`TypeError` from `on_state()`), letter labels `C`, `D`, `c`, `d`
  read as 100 and 500, an indirect `/K` tree rated `none`, the partly tagged PDF
  rated `good`, the capped walk `partial`, and an outline cycle giving no
  bookmarks.
  - A checked checkbox with no appearance reads `checked` and `Yes`; a checkbox
    with appearances reads `On` or `Off` as before; a radio group whose two
    buttons are `/AS /Off` with `/V /B` reads value `B` on both, with the button
    whose appearances name `B` checked; a text field reads `Ann`.
  - With one field's read made to raise, the other 5 fields are kept and one
    `form` error reads `Field subscribe: RuntimeError: cannot read this widget`.
    PyMuPDF reads every malformed widget tried (`/Rect 5`, `/Opt 5`, a
    dictionary `/V` or `/T`, an unknown `/FT`), so no real widget fails yet.
  - Page labels: `A`-`D` (`/S /A`) and `c`, `d` (`/S /a`) give style `label` and
    no value; `iv`, `v` (`/S /r`) give roman 4 and 5; `7` (`/S /D`) arabic 7;
    `Back` (prefix only) a label.
  - A 12-page tagged PDF whose root and element `/K` entries are indirect arrays
    rates as its direct copy: `good`, 13 elements, 12 pages. With 9 of 12 pages
    with text tagged plus 2 tagged pages without text: `partial` (11 tagged
    pages counted before). The fully tagged PDF with the element cap set to 10:
    truncated, 9 pages reached, `good`.
  - An outline whose last entry links back to the first keeps all 4 bookmarks;
    one whose nested `Two.a` links back to `One` keeps `One`, `Two`, `Two.a`. No
    probe error, and the PDF file's SHA-256 is unchanged.
  - The 10 test PDFs: `probe_pdf`'s facts and `read_lines`' text-layer lines
    (5,420 lines) are the same as before the change.
- `dev009_check.py` 48 of 48, `dev010_check.py` 32 of 32, `dev011_check.py` 16
  of 16, `dev012_check.py` 35 of 35, `dev017_check.py` 11 of 11 and
  `dev018_check.py` 7 of 7 again.
- Process wording grep of the added lines: only "cycle" for a cycle in an
  outline's links.

**Implementation Notes**

- `utils/pdf.py` holds `TEXT_FLAGS`, which the probe and `text_layer.py` import.
- Fields are read by widget annotation (`Page.annot_xrefs`, then
  `Page.load_widget`), each in its own `try`, so the order matches
  `Page.widgets()` and a failure loses only that field. A failed field's error
  names it from `/T` or its parent's `/T`, else its object number.
- A checkbox is on when `/AS` (or, without one, `/V`) is not `Off`; its value is
  `/V`, else `/AS`. A radio button is on when its `/AS` is not `Off`, or when
  its group's `/V` names one of the on states in its `/AP` `/N` or `/D`.
- The outline is walked by its `/First` and `/Next` links before `get_toc()`. At
  the first link back to an entry already read, that link and every link not yet
  followed are removed from the open document, which is never saved.
- `pages_with_tagged_content` still counts every tagged page; only the rating
  leaves out tagged pages without text.

---

### DEV-014 — Other follow-ups: transport, cache price, workflows, changelog

`Status`: `DONE` `Depends On`: `NONE` `Acceptance`:
`AC-039, AC-041, AC-042, AC-043`

**Goal**

Close the remaining 0.1.0 follow-ups that are code or configuration.

**Affected Area**

Approved by the user before the step (2026-11-20): `MODIFY` `surveying/llm.py`
(reports the transport once the PDF is attached), `surveying/survey.py` (passes
it through), `pipeline/runner.py` (records it on the step at once),
`costs/pricing.py`, `.github/workflows/ci.yml`, `.github/workflows/docs.yml`,
`CHANGELOG.md`, `pyproject.toml`.

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

Evidence, 2026-11-20, repo root, on the user's DEV-012 commit (`abb4829`) plus
DEV-013 (staged) and the uncommitted DEV-014 changes (macOS arm64, Python
3.13.9, Node 23.10.0 as the runner's own Node).

- `.venv/bin/ruff check`, `ruff format --check`, `ty check` on `scripts src`:
  passed; `interrogate`: 100%. Doctests: 26 passed, 1 skipped.
  `zizmor --persona=auditor --offline .`: no findings (the online audits need a
  GitHub token this session lacks). The git hooks other than ty pass on every
  changed file. `uv lock --check`: the lock still matches `pyproject.toml`.
- `.venv/bin/python -m pytest -q --numprocesses auto`: 81 passed, 24 failed, the
  same 24 as before.
- Scratchpad `dev014_check.py`: 8 of 8 checks passed.
  - A stand-in survey whose every answer is not JSON fails with `SurveyError`
    after 3 requests; `run.json`'s survey step records `pdf_transport` `upload`,
    on Anthropic and on OpenAI. The committed code, run the same way from a
    clone, records `null`.
  - `_config_price` for 1M input tokens with 0.5M read from and 0.25M written to
    the cache at $4 input: $1 with cache prices of 0, $4 with them unset, $2.45
    with $0.40 and $5.
  - The CI step "Fail if the lint recipes changed or added any file", run with
    bash in a fresh clone: exit 0 when clean, 1 with an untracked
    `reference/page-json.md` (named in its message), 1 with a changed
    `reference/cli.md`.
  - The docs plan step, run with bash: `build:versions` on a push with the
    release tags, `build` on a pull request, `build` with no tags and no error
    output, and with a broken `versions.mjs` it fails with Node's error instead
    of falling back to `build`.
- `dev009_check.py` 48 of 48, `dev010_check.py` 32 of 32, `dev011_check.py` 16
  of 16, `dev012_check.py` 35 of 35, `dev017_check.py` 11 of 11,
  `dev018_check.py` 7 of 7 and `dev013_check.py` 11 of 11 again.
- Process wording grep of the added lines: no hits.

**Implementation Notes**

- `ask_model` and `run_survey` take `on_attached`, called with the transport
  each time the PDF is attached (again after a lost upload is replaced), before
  any request. They no longer take `output_folder`, which was always
  `config.output_folder`, so they stay within Ruff's argument limit. The runner
  passes `_Step.record_transport`; `run_survey` still returns the transport.
- The CI step keeps `git diff --exit-code` and adds
  `git status --porcelain --untracked-files=all` on the reference folder,
  failing with an `::error::` that lists the untracked pages.
- The docs plan step prints how many documented releases there are. The one
  error meaning "no release tag yet" prints 0; any other error fails the step.
  Its comment now says it runs the runner's own Node and Python.
- `docs.yml`'s cache comment: `cache: false` turns off only Astro's asset cache;
  the action's `setup-node` still restores the pnpm store keyed on
  `docs/pnpm-lock.yaml` (checked in the action's `action.yml` at the pinned
  commit).

---

### DEV-015 — Wheel smoke test with page extraction and package description

`Status`: `DONE` `Depends On`: `DEV-008, DEV-011` `Acceptance`:
`AC-047, AC-048, AC-049`

**Goal**

Show that the installed wheel runs the survey and page extraction on every CI
platform, and describe the release.

**Affected Area**

Approved by the user before the step (2026-11-20): `MODIFY`
`scripts/smoke_installed_wheel.py`, `pyproject.toml` (description). The README
is Documenter's.

**Expected Outcome**

The smoke script runs the CLI and the Python API through the survey and page
extraction against the stand-in. The package description names surveying a PDF
and extracting its pages; the classifiers are unchanged.

**Self-Check**

`just build` (with `twine check --strict`) and the smoke script locally; CI's
wheel jobs on ubuntu, macOS and Windows after a push.

Evidence, 2026-11-20, repo root, on the user's commit `e318364` (DEV-013 and
DEV-014) plus the uncommitted DEV-015 changes (macOS arm64, Python 3.13.9).

- `.venv/bin/ruff check`, `ruff format --check`, `ty check` on `scripts src`:
  passed; `interrogate`: 100%. The git hooks other than ty pass on both changed
  files.
- `uv build` then `twine check --strict dist/*`: both artifacts `PASSED`
  (`pydelity-0.1.1-py3-none-any.whl` and `.tar.gz`; the version is
  release-please's to raise). Run with `UV_NATIVE_TLS=1` outside the sandbox,
  since uv's own certificates rejected PyPI's on this machine; `just build` runs
  the same two commands.
- `python scripts/smoke_installed_wheel.py`: 13 of 13 checks passed. The wheel
  installs with pip in a fresh environment; `pydelity --version` prints 0.1.1;
  for each provider the installed `pydelity <pdf> --yes --no-pause` and
  `pydelity.run(..., pause=False)` complete both steps on the 2-page scan, load
  back with a page file for each page, and send exactly one upload and 5 model
  requests (the survey's, then an extractor and a verifier request per page),
  all to the stand-in.
- The committed smoke script, run against the same wheel: 9 of 13, with both
  runs per provider ending `paused`, since a new survey pauses by default. So
  CI's wheel jobs fail on this branch until this step is committed.
- `.venv/bin/python -m pytest -q --numprocesses auto`: 81 passed, 24 failed, the
  same 24 as before. The DEV-009 to DEV-018 self-checks were not rerun, since
  nothing under `src/` changed.
- Process wording grep of the added lines: no hits.
- CI's wheel jobs on ubuntu, macOS and Windows run after the user pushes.

**Implementation Notes**

- The stand-in serves
  `tests/fixtures/extraction_answers/irs_form_1040a_1965_scan.json` for the
  pages. Its answers pass every check on the scan, so the request count is fixed
  at `EXPECTED_REQUESTS`.
- `pyproject.toml`'s description now reads "Survey any PDF and extract its pages
  with Anthropic or OpenAI models: a profile of the PDF, then each page's items
  in reading order with their boxes and figure crops, as JSON with a list of
  things to review." The classifiers are unchanged.

---

### DEV-016 — Reference pages for page extraction

`Status`: `DONE` `Depends On`: `DEV-011` `Acceptance`: `AC-052`

**Goal**

Generate reference pages for everything new, so CI's staleness check covers
them.

**Affected Area**

Approved by the user before the step (2026-11-20): `MODIFY`
`scripts/generate_reference_docs.py`; the generated pages under
`docs/src/content/docs/reference/`, with two new ones, `page-json.md` for
`pages/<NNNN>.json` and `extraction-checks.md`. A docstring under `src/` that
reads badly on a generated page is changed only with the user's approval.

**Expected Outcome**

The reference covers the new settings, CLI options and public functions, the
page file, the extraction checks and review-issue names, and the changed
`run.json` and `cost.jsonl` fields, all generated from the code.

**Self-Check**

`just docs-reference` twice with byte-identical output; `just lint`;
`just docs-build`.

Evidence, 2026-11-20, repo root, on the user's commit `52929aa` plus the
uncommitted DEV-016 changes (macOS arm64, Python 3.13.9, Node 23.10.0, pnpm).

- `.venv/bin/ruff check`, `ruff format --check`, `ty check` and `interrogate` on
  `scripts`: passed (100%).
- The generator then Prettier
  (`prek exec prettier-markdown -- node scripts/format_markdown.mjs`), run
  twice: the 11 reference pages are byte-identical (SHA-1 of each). New:
  `page-json.md` (`pages/<NNNN>.json`, every field of `PageFile` and each model
  inside it) and `extraction-checks.md` (the 11 checks in the order they run,
  how text is compared, and the `no_matching_label` and `verifier` issues).
  Changed: the side-panel order of `run-json.md`, `cost-jsonl.md`,
  `uploads-json.md` and `survey-checks.md`, and `python-api.md` now links
  `PageFile` to its page. The settings, CLI, Python API, `run.json` and
  `cost.jsonl` pages already came from the code and needed no other change.
- `just lint`: `docs-reference` and `lint-markdown` pass; `lint-python` stops at
  the 2 known ty errors in `tests/` (`Config.instructions`,
  `Profile.user_instructions`), which are Tester's.
  `ruff check scripts src tests` passes, and
  `zizmor --persona=auditor --offline .` reports nothing.
- `just docs-build` (`pnpm install --frozen-lockfile`, `pnpm run build`,
  `pnpm run check-links`): 27 pages built, every local link and fragment
  resolves. The built `page-json` page's heading reads `pages/<NNNN>.json`, and
  both new pages are in the Reference side panel.
- `.venv/bin/python -m pytest -q --numprocesses auto`: 81 passed, 24 failed, the
  same 24 as before.
- Process wording grep of the added script lines and both new pages: no hits.

**Implementation Notes**

- Three check docstrings name internal functions (`comparison_status`,
  `unmatched_labels`, `check_labels`). `_CHECK_REFERENCES` swaps those phrases
  for what a reader sees (the page file's `text_comparison`, the
  `no_matching_label` issue, the `labels` check), so no source docstring
  changed.
- "How text is compared" is the third paragraph of `text_layer`'s module
  docstring. The `verifier` issue's text is written in the generator, as the
  survey checks page's introduction is.

---

### DEV-017 — Prompted output on Anthropic and page reading from the image only

`Status`: `DONE` `Depends On`: `DEV-007, DEV-010` `Acceptance`:
`AC-005, AC-022, AC-029, AC-063`

**Goal**

Apply the design's decisions 20 and 21, added after DEV-011's real runs: every
agent asks Anthropic for prompted output, and the page models read the page's
text from the image only.

**Affected Area**

Approved by the user before the step (2026-11-19): `MODIFY`
`providers/profiles.py` (`ProviderProfile.output_mode`), `providers/factory.py`
(`output_mode` from the provider profile or the model's JSON-schema support;
`structured_output`), `extracting/prompts.py` (no text-layer section; the rule
to read all text from the image; `extract_page` and `verify_page` no longer take
text-layer lines), `extracting/llm.py` (the prompt calls),
`extracting/validators.py` (the text checks' retry note),
`extracting/text_layer.py` (its docstring), `extracting/extraction.py` (request
sizes without text-layer characters) and `costs/budget.py` (`PageRequestSize`
and estimate docstrings); regenerated reference pages if they change. Not
changed: `tests/fixtures/mock_providers.py`, which already answers Anthropic
requests as JSON text.

**Expected Outcome**

- The survey's agent, the extractor and the verifier ask Anthropic for
  `PromptedOutput` (no native output format in the request, the answer's JSON
  schema in the instructions) and OpenAI for `NativeOutput`. A model without
  JSON-schema output gets prompted output on either provider. The "Model ready"
  log line names the mode.
- No extractor or verifier request holds the page's text-layer lines. The
  prompts say to transcribe all text from the image, since the text a PDF stores
  can differ from what is printed. The text checks still compare the answer with
  the text layer, and their retry message adds that the stored text can be wrong
  (letters out of order, broken ligatures, wrong characters), so the model keeps
  what the image shows.
- The extraction estimate counts no text-layer characters in a request.
- No answer or verdict schema changes; `PROMPT_VERSION` stays 1, since no page
  file has been released.

**Self-Check**

Lint; unaffected tests; a scratchpad script with the stand-in that captures
survey, extractor and verifier requests for both providers: Anthropic requests
carry no output format and their instructions hold the answer's schema, OpenAI
requests carry the JSON-schema format, no page request holds a text-layer line,
and a failing text check's retry message holds the new note; the DEV-009 to
DEV-011 self-checks again. Then DEV-011's real runs, with the user's go-ahead.

Evidence, 2026-11-19, repo root, on the user's DEV-010 commit (`ce66a4f`) plus
the uncommitted DEV-011 and DEV-017 changes (macOS arm64, Python 3.13.9,
PydanticAI 2.69).

- `.venv/bin/ruff check`, `ruff format --check`, `ty check` on `scripts src`:
  passed; `interrogate`: 100%. Doctests: 24 passed, 1 skipped. The git hooks
  other than ty pass on the changed files.
- `.venv/bin/python -m pytest -q --numprocesses auto`: 81 passed, 24 failed, the
  same 24 as after DEV-011's code (listed there and under DEV-010); the
  stand-in's Anthropic survey tests pass under prompted output.
  `ty check tests`: the same 2 errors.
- Reference pages regenerated: no change beyond DEV-011's `python-api.md`.
- A direct check of `output_mode`: an `AnthropicModel` gives `prompted` and
  `PromptedOutput`, an `OpenAIResponsesModel` `native` and `NativeOutput`.
- Scratchpad `dev017_check.py` (the stand-in, `pydelity.extract` on the rotated
  PDF's pages 1-2 for each provider, page index 1's first extractor answer
  missing its longest text item): 11 of 11 checks passed.
  - Anthropic: the survey's, the extractor's and the verifier's requests carry
    no output format (`output_config` holds only `{"effort": "high"}`), and each
    one's instructions hold its answer's JSON schema (`SurveyAnswer`,
    `PageAnswer`, `VerifierVerdict`); the stand-in's JSON text answers are
    accepted.
  - OpenAI: every request carries `text.format.type` `json_schema`.
  - The "Model ready" lines name `prompted` for both of Anthropic's steps and
    `native` for OpenAI's.
  - No page request holds a text-layer section, and page index 0's first
    extractor request holds none of its 97 text-layer lines longer than 20
    characters. The `text_dropped` retry on page index 1 says the stored text
    can be wrong (broken ligatures) and to keep what the image shows; 3
    extractor and 2 verifier requests per provider.
  - `request_sizes` on pages index 0 and 1 (4,880 and 5,942 text-layer
    characters): 14,417 and 14,612 extractor characters, 18,123 and 18,318
    verifier characters, which no longer grow with the text layer.
- `dev009_check.py` 48 of 48, `dev010_check.py` 32 of 32 and `dev011_check.py`
  16 of 16 again.
- Process wording grep of the added lines: no hits.

**Implementation Notes**

- `output_mode` reads the model's provider (`model.system`, which the ledger
  wrapper passes through) to find its `ProviderProfile`; a model of another
  kind, such as a PydanticAI test model, falls back to its JSON-schema support.
  The runner's "Model ready" line already named the mode.
- `extract_page` and `verify_page` take only the page context (and the
  verifier's answer and failures); `PageInput.text_lines` stays for the checks.
- `PROMPT_VERSION` stays 1 as planned, although the comment above it asks for a
  new version whenever a prompt's text changes: no page file has been released,
  and DEV-011's real runs use new output folders.

---

### DEV-018 — No text review issues on pages the verifier passes

`Status`: `DONE` `Depends On`: `DEV-009` `Acceptance`: `AC-063`

**Goal**

Apply the user's rework after DEV-011's real runs: on a page the verifier
passes, the text differences left after the check retries stay in the page
file's check results but are not review issues, since the verifier saw them
beside the image and accepted the reading.

**Affected Area**

`extracting/extraction.py` (`_page_issues`), `extracting/schemas.py` (the
`PageFile.issues` docstring).

**Expected Outcome**

- When the verdict passed, `text_dropped` and `text_added` failures left on the
  kept answer are not review issues in the page file, so they are not in
  `run.json`, the run summary or the report either. Every other check still
  failing is listed as before.
- When the verdict did not pass, they are review issues as before.
- The page file's `checks` keeps every failure either way, and the page's log
  line counts only the listed issues.
- No prompt, answer, verdict, page file field or fingerprint input changes. A
  saved page file keeps the issues it was written with until its page is
  extracted again.

**Self-Check**

Lint; unaffected tests; a scratchpad script with the stand-in on the rotated
PDF: a page whose last extractor answer still fails `text_dropped` and a passing
verdict lists no text issues while its `checks` keeps the failure; the same page
with a verdict that finds problems and no correction lists the text issues and
the verifier's problems; on a passed page another check still failing is listed;
`run.json`'s review matches the page files. The DEV-009 to DEV-011 and DEV-017
self-checks again. The rule applied to the saved real OpenAI page file (verdict
passed, 11 text issues) leaves no issues, with no model call.

Evidence, 2026-11-20, repo root, on the user's commit `3e2c3cb` plus the
uncommitted DEV-018 changes (macOS arm64, Python 3.13.9, PydanticAI 2.69).

- `.venv/bin/ruff check`, `ruff format --check`, `ty check` on `scripts src`:
  passed; `interrogate`: 100%. Doctests: 24 passed, 1 skipped.
- `.venv/bin/python -m pytest -q --numprocesses auto`: 81 passed, 24 failed, the
  same 24 as after DEV-017 (listed under DEV-010 and DEV-011). None asserts text
  issues on a page the verifier passed.
- Scratchpad `dev018_check.py` (the stand-in, `pydelity.run` on the rotated
  PDF's pages 1-3 with `pause=False`, every extractor answer missing its longest
  text item, so `text_dropped` fails through all 3 attempts): 7 of 7 checks
  passed.
  - Page index 0, verdict passed: `checks` keeps `text_dropped` with 16
    failures; no review issues.
  - Page index 1, a verifier problem and no correction: 19 `text_dropped`
    issues, one per failure, then the `verifier` issue.
  - Page index 2, verdict passed, one item's box turned inside out: `boxes` and
    `reading_order` are listed; its 23 `text_dropped` failures stay in `checks`
    only.
  - `run.json`'s `review` and `RunResult.record.review` are the survey's issues,
    then each page file's (28 in all); each page's log line counts its listed
    issues (0, 20 and 2).
  - The saved real OpenAI page file (`real-openai-2/pages/0000.json`, verdict
    passed): 11 text issues as written, none under the rule.
- `dev009_check.py` 48 of 48, `dev010_check.py` 32 of 32, `dev011_check.py` 16
  of 16 and `dev017_check.py` 11 of 11 again.
- Process wording grep of the added lines: no hits.

**Implementation Notes**

- `_page_issues` drops the text checks' results by the names in
  `validators.TEXT_CHECKS` before turning failures into issues, so the rule
  follows the text checks if one is added or renamed.
- A verifier correction that replaced the answer has a verdict that did not
  pass, but the kept correction passes every check, so it has no text issues to
  list either way.

---

### DEV-019 — Keep verifier corrections that fail only the text comparison

`Status`: `DONE` `Depends On`: `DEV-009, DEV-018` `Acceptance`: `AC-063, AC-064`

**Goal**

Apply the design rerun after the code review (decisions 9 and 10): a verifier
correction that fails only `text_dropped` and `text_added` replaces the
extraction, and a page that keeps the correction lists no text differences for
review.

**Affected Area**

`extracting/extraction.py` (`_kept_answer`, `_page_issues`),
`extracting/schemas.py` (the docstrings of `PageFile.issues` and
`PageVerification`), `scripts/generate_reference_docs.py` (the checks page's
opening paragraph) and the regenerated `reference/extraction-checks.md` and
`reference/page-json.md`.

**Expected Outcome**

- A correction whose only failures are `text_dropped` and `text_added` is kept.
  The page file's `checks` are the correction's, those failures included, and
  its `issues` leave them out. The verifier's problems stay in the verdict only.
- A correction that fails any other check is rejected as now: the page keeps the
  extraction, each verifier problem is a `verifier` issue, and text differences
  are listed unless the verdict passed.
- The verifier is already asked again for text failures on its correction, with
  the note that the image decides (`AC-063`). The self-check confirms it, and
  that code does not change.
- No prompt, page file field or fingerprint input changes.

**Self-Check**

Lint; unaffected tests; a scratchpad script with the stand-in: a correction that
fails only `text_dropped` through its retries is kept, the verifier was asked
again with the text note, the page file's `checks` hold the failure and its
issues do not; a correction that fails `boxes` is rejected with `verifier` and
text issues listed; a passed verdict is unchanged. The DEV-009 to DEV-018
self-checks again; the reference pages regenerated twice, byte-identical.

Evidence, 2026-11-20, repo root, on the user's commit `98ac7f7` plus the
uncommitted DEV-019 changes (macOS arm64, Python 3.13.9, PydanticAI 2.69).

- `.venv/bin/ruff check`, `ruff format --check`, `ty check` on `scripts src`:
  passed; `interrogate`: 100%. Doctests: 26 passed, 1 skipped.
- `.venv/bin/python -m pytest -q --numprocesses auto`: 81 passed, 24 failed, the
  same 24 as before.
- Scratchpad `dev019_check.py` (the stand-in, `pydelity.run` on the rotated
  PDF's pages 1-3 with `pause=False`): 8 of 8 checks passed.
  - Page index 0, whose extraction misses a line and whose correction relabels
    an item but still misses it: the verifier was asked again twice, each time
    with the `text_dropped` failure and the note to keep what the image shows.
    The correction is kept (`correction_applied`, the relabeled item in the page
    file), the page file's `checks` hold its 16 `text_dropped` failures, and the
    page has no review issues.
  - Page index 1, whose correction also turns a box inside out: rejected
    (`correction_failures` name `boxes` and `text_dropped`). The extraction is
    kept and its issues are `text_dropped` and `verifier`.
  - Page index 2, a passed verdict: the extraction is kept with its own
    `reading_order` failure listed, as before.
  - `run.json`'s `review` matches the page files (27 issues).
- The same script on the committed code, from a clone: 6 of 8. The page index 0
  correction is rejected and `run.json` lists 44 issues.
- The generator then Prettier, twice: byte-identical. `extraction-checks.md`
  says when a correction replaces the extraction and that text differences are
  not listed on a page whose correction is kept; `page-json.md` carries the new
  `correction_applied` and `issues` docstrings.
- `dev009_check.py` 48 of 48, `dev010_check.py` 32 of 32, `dev011_check.py` 16
  of 16, `dev012_check.py` 35 of 35, `dev013_check.py` 11 of 11,
  `dev017_check.py` 11 of 11 and `dev018_check.py` 7 of 7 again.
- Process wording grep of the added lines: no hits.

**Implementation Notes**

- `_kept_answer` keeps a correction when no check outside `TEXT_CHECKS` failed.
  A kept correction's failures, text ones included, become the page file's
  `checks`, as they already did.
- `_page_issues` leaves out the text checks when the verdict passed or the
  correction was kept.
- The verifier's output validator already ran the text checks on a correction
  and sent `retry_message`, with its text note, while retries remained, so
  nothing changed there.

---

### DEV-020 — Check page furniture by position

`Status`: `DONE` `Depends On`: `DEV-019` `Acceptance`: `AC-018`

**Goal**

Apply decision 22: the `artifacts` check finds each page-furniture line on the
page from the stored text and checks that an `artifact` item's box covers it,
never comparing the stored text with the model's reading.

**Affected Area**

`surveying/probe.py` (its line reading, with each line's box on the displayed
page, made public so page extraction finds lines exactly as the survey did),
`extracting/text_layer.py` (a `PageText` holding the page's text-layer lines and
each furniture line's boxes on the upright image's grid),
`extracting/validators.py` (`check_artifacts` by position; every check takes the
page's `PageText`, so one check type replaces two), `extracting/agents.py` and
`extracting/llm.py` (pass `PageText` where they pass text lines now),
`extracting/extraction.py` (read `PageText` on the PyMuPDF worker), and the
regenerated `reference/extraction-checks.md`.

**Expected Outcome**

- On each page, every line the survey classed as page furniture is found in the
  stored text by the survey's own line reading and `normalize_line`, and its box
  is mapped to the grid with `points_box_to_grid`.
- The check passes a line when the center of each of its boxes lies inside the
  box of an item with role `artifact`, within 20 grid units. A failure names the
  line and its place on the grid. A furniture line the page's stored text does
  not hold is skipped.
- The check keeps its name, its place in the order and its retry rule; no
  fingerprint input, prompt or page file field changes.

**Self-Check**

Lint; unaffected tests; a scratchpad script with the stand-in on the rotated W9
instructions PDF: on pages with rotation attributes 0, 90, 180 and 270, an
`artifact` item placed on the furniture line's box passes with its text changed,
one placed elsewhere fails with the line and grid place named, and a page whose
stored text lacks the line is skipped; the furniture boxes are found on every
page the facts list each furniture line on. The DEV-009 to DEV-019 self-checks
again; the reference pages regenerated twice, byte-identical.

Evidence, 2026-11-20, repo root, on the user's DEV-019 commit (`e4633ea`) plus
the uncommitted DEV-020 changes (macOS arm64, Python 3.13.9, PyMuPDF 2.1).

- `.venv/bin/ruff check`, `ruff format --check`, `ty check` on `scripts src`:
  passed; `interrogate`: 100%. Doctests: 27 passed, 1 skipped (new example for
  `_center`).
- `.venv/bin/python -m pytest -q --numprocesses auto`: 81 passed, 24 failed, the
  same 24 as before.
- Scratchpad `dev020_check.py` (the rotated W9 instructions PDF, surveyed
  through the stand-in with the footer `R2` and the page number `R1` classed as
  page furniture and the list marker `R3` as content): 6 of 6 checks passed.
  - `read_page_text` finds `R1` and `R2` on pages index 1 to 6, the pages the
    facts list them on, and on no other page.
  - On pages with rotation attributes 90, 180, 270 and 0, the answer's items
    over the furniture made `artifact` items, with their text replaced by a
    reading that differs from the stored text: `check_artifacts` passes. With
    those items moved to `[0, 0, 60, 30]`: one failure per furniture line, such
    as "the repeated line R1, '2', is page furniture at [69, 947, 77, 964] on
    the grid, but no item with role artifact covers it".
  - The footer lands at the bottom of the upright grid on every page (top edge
    948), alternating left and right as the printed pages do.
  - Page index 0 holds no furniture line, and the check passes.
  - `pydelity.run(pages="2-5", pause=False)`: `artifacts` passes on pages index
    1 to 3 and fails on page index 4, whose artifact items were moved, with 2
    `artifacts` review issues.
- The generator then Prettier, twice: byte-identical. `extraction-checks.md` now
  describes the check by position.
- `dev009_check.py` 48 of 48, `dev010_check.py` 32 of 32, `dev011_check.py` 16
  of 16, `dev012_check.py` 35 of 35, `dev013_check.py` 11 of 11 (the probe's
  facts and text-layer lines on the 10 test PDFs unchanged), `dev017_check.py`
  11 of 11, `dev018_check.py` 7 of 7 and `dev019_check.py` 8 of 8 again.
- Process wording grep of the added lines: no hits.

**Implementation Notes**

- The probe's `_Line` keeps its box (`rect`), and the public `line_boxes(page)`
  returns each line's text and box. `read_page_text` matches furniture lines on
  `normalize_line` of those lines, as the survey's repeated-line count does.
- `PageText` holds `lines` (from `read_lines`, for the text comparison) and
  `furniture` (grid boxes by repeated line ID). Every check now takes it, so the
  `Check` and `TextCheck` types are one; the eight checks that do not need it
  say so in their docstrings. `comparison_status` still takes the lines.
- A furniture line passes only when every one of its boxes on the page is
  covered; a failure names the first uncovered box.

---

## Plan Notes

### Design rerun after the code review

Reconciled on resuming (2026-11-20), in the rerun that recovery frame 1 asks of
Developer (`RerunThrough`: `DEVELOPING`, `ResumeAt`: `TESTING`). The user
retired `AC-024` for `AC-064` and `AC-062` for `AC-063`, and the design added
decision 22 and changed decisions 9 and 10. The steps that named the retired
criteria now name their replacements. DEV-001 to DEV-018 stand, apart from the
two behaviors DEV-019 and DEV-020 change: when a correction is kept, and how
`artifacts` decides. Both add to DEV-009's and DEV-018's code rather than
reopening them, so their recorded evidence still describes what they did. The
plan returns to `PROPOSED` for the two new steps. After DEV-020, the frame
closes and the workflow resumes at `TESTING`. The user approved the revised plan
and DEV-019's files (2026-11-20), then DEV-020's files.

### Review findings sent to the Architect

After the plan was complete, the user asked for a review of this session's code
(2026-11-20), keeping only major issues. Two findings conflict with decision 21
(the page image decides the text). The user sent both to the Architect. No code
changed.

1. **Verifier corrections and the text checks.** The verifier's output validator
   (`extracting/agents.py`, `run_checks` on `verdict.corrected` near line 210)
   runs every check on a correction, `text_dropped` and `text_added` included,
   and asks again while retries remain. `_kept_answer`
   (`extracting/extraction.py`, line 393) applies a correction only when it
   fails no check. On a page whose stored text differs from what is printed
   (broken letter forms, as on `irs_pub1_arabic.pdf`), a correction that reads
   the image correctly fails the text checks just as the extraction did. The
   verifier is retried for failures it cannot fix, its correction is rejected,
   and its problems become `verifier` review issues. So the verifier can never
   improve such a page. Decision 10 and `AC-024` ("a corrected extraction that
   passes the code checks") require this. Decisions 9 and 21, the verifier
   prompt ("the image decides") and the retry note (`_TEXT_NOTE`: "keep what the
   image shows") point the other way. Confirmed by calling `_kept_answer` with
   only `text_dropped` failures on the correction: rejected, extraction kept.
2. **The `artifacts` check and stored text.** `check_artifacts`
   (`extracting/validators.py`, line 701) requires each repeated line the survey
   classed as page furniture, in `normalize_line` form (NFKC, case-folded,
   spacing collapsed, digit runs as `#`), to appear inside an `artifact` item's
   text. Repeated lines come from the stored text. So on such PDFs a running
   header read correctly from the image never matches. The check fails on every
   attempt and spends the page's check retries. It stays a review issue when the
   verifier passes the page, since `AC-062` exempts only `text_dropped` and
   `text_added`. Through finding 1, it also blocks every verifier correction.
   Not run on a real PDF: the Arabic test PDF has one page and no repeated
   lines.

Also found and judged not major, so left as they are: an inline (direct) widget
dictionary makes the probe lose every form field; a dangling outline link loses
every bookmark; checkbox and radio `value`s changed on ordinary forms (an off
radio button now carries its group's value; checks compare only checked states);
an interrupted overwrite can leave an old page file naming a new figure crop; a
table header cell spanning into body rows shifts body cells in the report; the
report header names no model for a step that failed.

### Second review findings sent to the Architect

After the design rerun, the user asked for a second review of this session's
code (2026-11-20), keeping only major issues. One finding is a gap in decision
22 and went to the Architect. Two are implementation defects of DEV-020, for
Developer to fix in the rerun that follows. No code changed.

1. **Which stored line is the furniture line** (design gap, decision 22).
   `read_page_text` (`extracting/text_layer.py`, line 179) collects the box of
   every line on the page whose `normalize_line` form equals a furniture line's,
   and `check_artifacts` (`extracting/validators.py`, line 745) requires each of
   those boxes to be covered by an `artifact` item. The survey counts a repeated
   line once per page, the first line with that form in the probe's reading
   order, and decision 22 speaks of "its box". So a body line that shares the
   furniture's normalized form must also be an artifact. `normalize_line` turns
   digit runs into `#`, so a page number (`#`) matches every digits-only line,
   such as table cells and axis labels. Such a page fails `artifacts` on every
   attempt, the retry message tells the model to mark data as page furniture,
   the issue stays, and every verifier correction is rejected. On the test PDFs:
   `caps_english_hl_pages_28_35.pdf` has "GRADE 1" (R3) three times per page,
   `irs_form_1040_1950.pdf` has "$" (R1) 6 to 25 times per page,
   `bls_navigating_slides.pdf` has its footer (R1) twice on four pages, and
   `irs_w9_instructions.pdf` has "1." (R3) up to 9 times. Taking only the
   occurrence the survey counted does not settle it: that first occurrence is
   often not the header or footer ("GRADE 1" is first found mid-page, none of
   its three in the top or bottom band; "$" is first found mid-page on page
   index 0), and the line nearest a page edge is not reliably it either.
   Confirmed by running: a page with a page number and a table of numbers, with
   only the page number marked `artifact`, fails on the first table cell.
   Developer's suggestion: a furniture line passes when at least one of its
   occurrences on the page lies inside an `artifact` item, which needs no guess
   about which occurrence is the furniture.
2. **A malformed artifact box crashes the run** (implementation, DEV-020).
   `check_artifacts` reads four values from each `artifact` item's box through
   `_covers` (`extracting/validators.py`, line 307) without the `_box_problem`
   guard the other checks use. Pydantic accepts a box such as `[485, 950]`, so
   on a page with furniture the check raises `IndexError` inside the agent's
   output validator. That ends the page task, cancels every other page and fails
   the run, where the `boxes` check would only have reported it. Confirmed by
   running.
3. **Misplaced docstrings** (implementation, DEV-020). The edit that gave the
   eight context-only checks their `page_text` parameter put its eight
   descriptions into `unmatched_labels` (`extracting/validators.py`, line 1459),
   which does not take it. The eight checks do not document it.

Also checked and correct: corrections kept when they fail only the text checks,
with their `checks`, `issues` and `correction_failures`; the furniture boxes'
grid places on pages with `/Rotate` 0, 90, 180 and 270, every profile rotation
and an offset crop box (32 cases); the report and reference pages; the probe and
workflows.

### Handoff to Tester

Every step, DEV-001 to DEV-018, is `DONE` (2026-11-20). Each step's evidence
above lists its commands and results. The scratchpad scripts it names
(`dev009_check.py` to `dev018_check.py`) were Developer's self-checks and are
not in the repository. The real model runs of DEV-011 (Anthropic and OpenAI,
$3.38 in all) are recorded under DEV-011.

The test suite gives 81 passed and 24 failed. All 24 are existing tests that
assert the contract this cycle replaced, listed with their reasons under
DEV-001, DEV-010 and DEV-011. `ty check tests` reports 2 errors, for the same
reason. They are:

- `config/test_loading.py::test_config_file_paths_resolve_against_its_folder_and_keywords_win`
- `costs/test_budget.py`:
  `test_an_unpriced_model_without_max_cost_runs_and_records_no_price`,
  `test_earlier_spend_counts_and_a_disallowed_run_stops_resumably`,
  `test_estimate_writes_nothing_and_a_reusable_survey_costs_nothing`
- `pipeline/test_runner.py`:
  `test_a_failed_survey_saves_no_survey_and_its_spend_counts_next_time`,
  `test_a_rerun_with_unchanged_survey_inputs_reuses_everything`,
  `test_changing_a_survey_input_or_overwrite_reruns_the_survey[instructions]`,
  `test_no_output_file_holds_the_api_key`
- `providers/test_ledger_model.py::test_fewer_temporary_failures_than_the_retries_still_complete`
- `providers/test_uploads.py`:
  `test_a_failed_upload_falls_back_to_sending_the_pdf_in_the_request`,
  `test_a_file_the_provider_no_longer_has_is_uploaded_again_once`
- `report/test_html.py`: `test_page_images_are_rendered_only_when_missing`,
  `test_report_escapes_text_from_the_pdf_the_user_and_the_model`
- `surveying/test_survey.py`:
  `test_answers_that_differ_from_the_facts_are_kept_and_listed_by_page`,
  `test_checks_still_failing_after_the_retries_are_listed_for_review`,
  `test_request_sends_the_facts_as_hints_with_every_repeated_line`,
  `test_user_languages_lead_and_rejected_model_tags_become_review_issues`
- `surveying/test_validators.py`:
  `test_labels_check_finds_empty_repeated_kindless_and_unknown_labels`,
  `test_page_numbering_check_finds_ranges_outside_the_pdf_and_overlaps`,
  `test_rotation_check_finds_ranges_outside_the_pdf_and_overlaps`,
  `test_writing_direction_check_finds_ranges_outside_the_pdf_and_overlaps`
- `test_api.py::test_async_run_gives_what_run_gives_with_the_same_warnings`
- `test_cli.py`:
  `test_a_pdf_alone_runs_the_survey_with_keys_from_the_environment`,
  `test_over_max_cost_warns_then_a_yes_completes_with_one_question`

Contract changes after DEV-011 that tests may touch:

- `ask_model` and `run_survey` take `on_attached` instead of `output_folder`
  (DEV-014).
- `write_report` takes one `ReportInputs` (DEV-012).
- `TEXT_FLAGS` moved to `utils/pdf.py` (DEV-013).
- Text issues are left off the review list on pages the verifier passes
  (DEV-018).

Changes after the code review, in the design rerun of recovery frame 1:

- A verifier correction that fails only `text_dropped` and `text_added` is kept,
  and a page that keeps it lists no text differences (`AC-063`, `AC-064`,
  DEV-019).
- `artifacts` checks page furniture by position (decision 22, DEV-020). Every
  check, and `run_checks`, takes a `PageText` from `read_page_text` instead of
  the text lines. The probe has a public `line_boxes`.

Not yet run: CI on GitHub, including the wheel jobs on ubuntu, macOS and
Windows, which run after the user pushes.

### Suspended Assignment 1

`Recovery Frame`: `1` `Recovery Reason`:
`Anthropic rejects PageAnswer and VerifierVerdict as structured output: their 18 and 20 nullable fields exceed its limit of 16 union-type fields per request.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`DEV-001 to DEV-010 committed through ce66a4f; DEV-011's code uncommitted (api.py, __init__.py, cli.py, pipeline/runner.py, pipeline/schemas.py, surveying/validators.py, reference/python-api.md), its stand-in checks passed (dev011_check.py 16 of 16), its real Anthropic run refused at page 1's extractor.`
`Next Action`:
`Reconcile the corrected design with DEV-001 to DEV-011 (schemas, prompts, agents, validators, extraction, estimate), reopen and fix the affected steps, rerun the self-checks, then repeat DEV-011's real runs on Anthropic and OpenAI with the user's go-ahead.`

Reconciled on resuming (2026-11-19), after the design rerun that added decisions
20 and 21 and closed frame 1 with no reruns: no answer, verdict or page file
schema changed, so DEV-001 to DEV-010 stand. Decisions 20 and 21 change the
output mode (`providers/`), the page prompts and the estimate's request sizes,
which DEV-017 covers as one step rather than reopening DEV-003, DEV-007 and
DEV-010, whose other outcomes still hold. DEV-011's code stands; its real runs
repeat after DEV-017, on new output folders, since the prompt text changes
without a new `PROMPT_VERSION`. The user approved the revised plan and DEV-017's
files (2026-11-19).

Reconciled on resuming (2026-11-20), after the user's rework that retired
`AC-023` for `AC-062` and the design rerun that closed its frame: the text
comparison and its retry message stand, so DEV-006, DEV-007 and DEV-017 now name
`AC-062` instead of the retired `AC-023`. Listing text differences only when the
verdict did not pass is new behavior in the page's review issues, which DEV-018
covers rather than reopening DEV-009, whose other outcomes hold. DEV-018 runs
before DEV-012, so the report is built on the new issue list. The user approved
the revised plan and DEV-018's files (2026-11-20).

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
- No shipped wording from the development process (user's rule, 2026-11-19,
  after `extracting/__init__.py` opened with "Step 2, page extraction"): every
  step's self-check also greps the files it adds or changes for numbered
  pipeline steps, `DEV-` and `AC-` IDs, cycle, design, scope, workflow role
  names and KGForEdGlobal, and rewords any hit. Naming a step ("the survey",
  "page extraction") or saying "later steps" is fine; the public docs describe
  the pipeline that way. The docstring now reads "Page extraction: each selected
  page's items, in reading order, as a page file", and a repo-wide search on
  2026-11-19 (tracked and new files outside `.standards/`, `.claude/`,
  `.agents/`, `.codex/` and `artifacts/`) found no other such wording in files
  Developer owns. For Tester: `tests/pydelity/surveying/test_survey.py:39` says
  "AC-006 keeps them out of prompts", which should name the rule itself instead.
  The comments in `.markdownlint-cli2.yaml`, `.pre-commit-config.yaml`,
  `.prettierrc.yaml` and `scripts/format_markdown.mjs` about how the tooling
  treats STANDARDS files describe repo tooling, not the process, and stay.

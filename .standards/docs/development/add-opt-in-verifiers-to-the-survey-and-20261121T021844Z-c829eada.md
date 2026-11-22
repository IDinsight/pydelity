<!-- STANDARDS
Artifact: DEVELOPMENT
Cycle: add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada
-->

# Development Plan

`Cycle`: `add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada`
`Mode`: `STEPWISE` `User Style`: `tony` `User Style Locked`: `true` `Status`:
`PROPOSED` `Verification Cadence`: `INCREMENTAL` `Current Increment`: `NONE`

## Implementation Contract

- `Scope`:
  `.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
- `Architecture`:
  `.standards/docs/specs/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
- `Request`:
  `Reorder every module first; then make each step's verifier opt-in (one global switch plus a per-step override, off by default), give the survey a verifier like page extraction's, make page extraction's verifier optional with every difference listed when none ran, fix page extraction's remaining defects, and ready 0.2.0's docstrings, reference pages and package description. Then, as user rework: code's measurements of the PDF become hints in both steps; only checks send an answer back, outputs record hints apart, and prompts present them as hints.`

## Build Steps

### DEV-001 — Reorder every module in the package and the scripts

`Status`: `DONE` `Depends On`: `NONE` `Acceptance`: `AC-041`

**Goal**

Put every Python module in `src/pydelity/` and `scripts/` in the design's
**Module order** before any other change, as a move-only change the user can
commit and review on its own.

**Affected Area**

Every `.py` file under `src/pydelity/` (53 modules) and `scripts/`
(`check_env_template.py`, `generate_reference_docs.py`,
`smoke_installed_wheel.py`); the generated pages under
`docs/src/content/docs/reference/` if `generate_reference_docs.py` lists
constants in a new order. Tests are not touched.

**Expected Outcome**

- Each module follows **Module order**: header (docstring, imports,
  `TYPE_CHECKING` block); module variables and type aliases (dunders, then
  private, then public; assignments before aliases; alphabetical); private
  classes, then private functions; public classes, then public functions; each
  group alphabetical; runtime statements kept beside what they use; any
  `if __name__ == "__main__":` block last. Inside classes, methods ordered
  `__init__` first, then other underscore names, then public names, each
  alphabetical, with property setters after their getters and Pydantic
  validators, fields, enum members and nested classes left where they are.
- A move takes the whole definition with its decorators and the comment lines
  directly above it. No text changes, no name changes, no annotation is turned
  into a string.
- Where the rule's order would break import on Python 3.13 (base classes,
  decorators, default values, class bodies or eagerly evaluated annotations
  using a name defined later), the module keeps the working order. Each such
  departure is listed below under **Order departures**, by module, with its
  reason. Expected kinds: schema modules kept in dependency order (such as
  `surveying/schemas.py`, `extracting/schemas.py`), `__init__.py`'s
  `_logger.disable("pydelity")`, and `smoke_installed_wheel.py`'s `sys.path`
  setup before its `tests.fixtures` import.
- `pytest`, the doctests, `ruff check`, `ruff format --check`, `ty check` and
  `interrogate` give the same results as before the reorder.

**Self-Check**

1. Baseline on the clean commit `126f52f`, before any move: the tests
   (`.venv/bin/python -m pytest -q --numprocesses auto -p no:cacheprovider`),
   the doctests
   (`.venv/bin/python -m pytest -q --doctest-modules src -p no:cacheprovider`),
   `ruff check scripts src tests`, `ruff format --check scripts src tests`,
   `ty check scripts src tests` and `interrogate scripts src tests` from
   `.venv/bin`, with counts recorded here.
2. The reorder is made by a scratch script in the session scratchpad (never in
   the repo) that parses each module with `ast`, splits it into top-level blocks
   with their decorators and leading comments, sorts the blocks and the methods
   by the rule, and writes the result; dependency departures are then placed by
   hand and reviewed module by module.
3. A second scratch script compares each file with `126f52f`: the same multiset
   of non-blank lines, the same multiset of top-level statements (`ast.dump`),
   the same members per class, and the same field or member order in every
   Pydantic model, dataclass and enum. It also checks every module against
   **Module order** and prints each departure, which must match the list below.
4. The checks in 1 again, with the same results; then
   `.venv/bin/python scripts/generate_reference_docs.py` and `git diff --stat`
   on the reference pages, whose changes may only reorder the constants lists.
5. Limitation: Python 3.14 is not installed here (only 3.11–3.13 under
   `/opt/homebrew/bin`), so the self-check runs on 3.13.9, the stricter case,
   since 3.13 evaluates annotations eagerly. CI runs 3.14; installing it locally
   is a download that needs the user's approval.

Evidence, 2026-11-21, repo root, macOS arm64, Python 3.13.9 (`.venv`), PyMuPDF
2.1. Assessed content: `126f52f` plus the uncommitted reorder of 16 files
(`git diff -- src scripts`, 667 insertions and 668 deletions, SHA-256 of the
diff starting `0f21ce5c770d636c`). Tests and `tests/` are untouched.

- Baseline on `126f52f` (clean `src`, `scripts`, `tests`, `docs`): tests 177
  passed (`-p no:randomly`); doctests 27 passed, 1 skipped; 177 test IDs and 28
  doctest IDs collected (`--collect-only`, sorted and saved); `ruff check` "All
  checks passed!"; `ruff format --check` "89 files already formatted";
  `ty check` "All checks passed!"; `interrogate` 100.0%. All exit 0.
- Reorder: scratch tool `reorder/reorder.py` in the session scratchpad, which
  splits each module into top-level blocks (decorators, comment lines directly
  above, attribute docstrings and deeper trailing comments included), sorts them
  by **Module order**, then fixes eager-dependency violations: a constant that
  reads a later definition moves below it, and a class or function read by an
  earlier one moves above that reader. It also sorts methods in their slots,
  leaving fields, validators and nested classes in place. It found no line
  outside a block, no runtime statement other than `__init__.py`'s
  `_logger.disable`, and no class needing a method move: every class's methods
  were already in order. `ruff format scripts src` afterwards changed nothing.
- Comparison: scratch tool
  `reorder/compare.py 126f52f <every .py in src/pydelity and scripts>` exit 0:
  every file has the same multiset of non-blank lines, the same multiset of
  top-level statements (`ast.dump`), the same members in every class (nested
  ones included), and the same order of every non-method member (fields, enum
  members, validators, `model_config`, docstrings). Its order check reports only
  the departures listed below.
- After the reorder, the same commands: tests 177 passed with `-p no:randomly`
  and 177 passed with random order; doctests 27 passed, 1 skipped; collected
  test and doctest IDs identical to the baseline (`diff` empty); `ruff check`,
  `ruff format --check` (89 files), `ty check` and `interrogate` (100.0%) as
  before. `pydelity --help` exits 0, and `scripts/check_env_template.py`
  exits 0.
- Reference pages: `.venv/bin/python scripts/generate_reference_docs.py`, then
  `scripts/format_markdown.mjs` with the hook's pinned Prettier 3.10.1 and Node
  24.22.3 from `~/.cache/prek` (what `just lint` runs): no change to any
  generated page. The public constants of `costs/budget.py` were already
  alphabetical, and no public constant of `surveying/probe.py` moved relative to
  another. The formatter also left four older STANDARDS records unformatted, as
  before this step.
- Not run: Python 3.14 (not installed locally), `just` recipes through `uv` (uv
  cannot write its cache in the sandbox; the `.venv/bin` tools are the same
  pinned versions), and the wheel smoke test (it needs `uv build`; the reorder
  does not touch packaging).

**Implementation Notes**

#### Order departures

Each keeps an order that Python 3.13 needs to import the module, where a base
class, a field or parameter annotation, a default value or a constant's value
reads another definition of the module.

- `scripts/smoke_installed_wheel.py`: `REPO_ROOT` and `sys.path.insert(...)`
  stay among the imports, before the `tests.fixtures` import that needs them;
  `_Venv` stays above `_Smoke`, whose field annotation names it.
- `src/pydelity/__init__.py`: `_logger.disable("pydelity")` stays last, after
  `__version__`; it runs code and nothing depends on it.
- `src/pydelity/cli.py`: `_show_version` stays above `_pydelity`, whose
  `--version` option names it as its callback.
- `src/pydelity/config/schemas.py`: `ExtractionConfig`, `ModelPrices`,
  `SurveyConfig` and `UploadsConfig` above `AdvancedConfig`, whose fields use
  them.
- `src/pydelity/costs/schemas.py`: `StepEstimate` above `CostEstimate`.
- `src/pydelity/errors.py`: `PydelityError` above `BudgetExceededError`, its
  first subclass alphabetically.
- `src/pydelity/extracting/rendering.py` (unchanged file): `UprightImage` above
  `PdfWorker`.
- `src/pydelity/extracting/schemas.py`: `FieldContent`, `TableCell` and `Table`
  above `AnswerItem` (`TableCell` above `Table`); `PageRepeatedLine` above
  `PageContext`; `RenderingSettings` above `PageInputs`; `PageImageSize`,
  `PageInputs` and `PageVerification` above `PageFile`, with `VerifierProblem`
  above `VerifierVerdict` above `PageVerification`.
- `src/pydelity/extracting/validators.py`: `CHECKS` below the check functions it
  lists (after `check_reading_order`), and `TEXT_CHECKS` below
  `check_text_added` and `check_text_dropped`.
- `src/pydelity/pipeline/runner.py`: `_Step` above `_Run`.
- `src/pydelity/pipeline/schemas.py`: `StepRecord` and `WarningItem` above
  `RunRecord`.
- `src/pydelity/providers/profiles.py`: `PROFILES` below `ProviderProfile`,
  whose instances it holds.
- `src/pydelity/surveying/schemas.py`: `FormField`, `FormInfo`,
  `NumberingRange`, `PageFacts` (with `OrientationFacts`, `PrintedNumber` and
  `TextFacts` above it), `ProbeError`, `RepeatedLine` and `StructureFacts` above
  `Facts`; `PdfIdentity` above `PdfFacts`; `RotationRange`, `StartMarker` and
  `WritingDirection` above `Profile`; `Region` above `Proposal`;
  `SurveySettings` above `SurveyInputs`; `Profile`, `Proposal`, `SurveyInputs`
  and `SurveyVerification` (with `SurveyAnswer`, `SurveyProblem` and
  `SurveyVerdict` above it) above `PdfSurvey`, which DEV-006 moved to the end.
- `src/pydelity/surveying/validators.py`: `CHECKS` below the check functions it
  lists (after `check_writing_direction`).

Files changed: `scripts/check_env_template.py`, `config/loading.py`,
`costs/budget.py`, `costs/ledger.py`, `costs/schemas.py`, `errors.py`,
`extracting/extraction.py`, `extracting/schemas.py`, `extracting/validators.py`,
`pipeline/runner.py`, `providers/profiles.py`, `report/html.py`,
`surveying/facts.py`, `surveying/probe.py`, `surveying/schemas.py`,
`surveying/validators.py` (paths under `src/pydelity/` except the script). The
other 40 modules already followed the rule.

---

### DEV-002 — Verifier settings and the CLI switch

`Status`: `DONE` `Depends On`: `DEV-001` `Acceptance`:
`AC-001, AC-002, AC-003, AC-004`

**Goal**

Add the global verifier switch and one override per step, off by default, with
resolved properties that every step reads.

**Affected Area**

`src/pydelity/config/schemas.py`, `src/pydelity/cli.py`, `examples/config.json`,
`examples/config.yaml`.

**Expected Outcome**

- `Config.verify: bool = False`, `SurveyConfig.verify: bool | None = None` and
  `ExtractionConfig.verify: bool | None = None`, with the design's docstrings
  (**Settings**), and resolved properties `Config.verify_survey` and
  `Config.verify_extraction` (the override when set, else `verify`), placed
  beside `survey_model` and `extraction_model`.
- The other `advanced.survey` and `advanced.extraction` docstrings that call the
  verifier a model say "the verifier" or "a second request to the same model".
- CLI `--verify`/`-vf` (`bool | None`, like `--overwrite`): passes `verify=True`
  when given and nothing otherwise, with the design's help text.
- Python callers pass `verify=True` or `advanced={"survey": {"verify": True}}`
  through the existing `**settings` keywords; no API signature changes.
- Both example files gain `verify: false` after `pdf`, and
  `advanced.survey.verify: null` and `advanced.extraction.verify: null` last in
  their sections, alphabetical like the rest, with comments saying what each
  does, that `null` follows `verify`, and that a verifier adds cost.
- No step reads the properties yet; DEV-003 and DEV-006 do.

**Self-Check**

Ruff check and format check, `ty check` and interrogate on `scripts src`; a
scratchpad script that resolves the config from defaults, a JSON file, a YAML
file, keywords and `--verify`/`-vf` through Typer's test runner, covering each
override with `verify` on and off; both example files load without a
`ConfigError`; the existing tests, with any failure from a replaced contract
listed.

Evidence, 2026-11-21, repo root, on `4a6bec7` plus the uncommitted DEV-002
changes to `src/pydelity/config/schemas.py`, `src/pydelity/cli.py`,
`examples/config.json` and `examples/config.yaml` (macOS arm64, Python 3.13.9,
`.venv` with a strict editable install whose files link to `src/`).

- Scratch script `dev002/check_settings.py` in the session scratchpad, run with
  `.venv/bin/python -I check_settings.py <repo>`: 27 of 27 checks passed.
  Defaults give `verify: false`, both overrides `null` and both resolved
  properties false. `settings={"verify": True}` turns both on. Every combination
  of `verify` (false, true) with `advanced.survey.verify` or
  `advanced.extraction.verify` (false, true) sets that step from the override
  and the other from `verify`; an explicit `null` follows `verify`. A JSON file
  and a YAML file set them; a keyword overrides the file, and a nested
  `advanced` keyword merges into the file's `advanced`. `verify: maybe` gives
  the `ConfigError` line
  `advanced.survey.verify: Input should be a valid boolean`. Both example files
  load with `false`, `null`, `null`. Through Typer's `CliRunner` (with
  `arun_with_questions` replaced by a stub that resolves the settings): no
  option passes no `verify` keyword (both steps off), `--verify` and `-vf` pass
  `verify=True` (both on), no option keeps a config file's `verify: true`,
  `--help` lists `--verify` and `-vf`, and `--no-verify` is a usage error (exit
  2).
- `.venv/bin/ruff check scripts src tests` "All checks passed!";
  `ruff format --check` "89 files already formatted";
  `ty check scripts src tests` "All checks passed!"; `interrogate` 100.0%.
- Tests: `.venv/bin/python -m pytest -q --numprocesses auto -p no:cacheprovider`
  177 passed (the example-file completeness test in `test_loading.py` included);
  doctests 27 passed, 1 skipped. No test fails from this step.
- `compare.py`'s order check on the two changed modules reports only the
  departures listed under DEV-001.
- Reference pages: generated in a scratch copy of the tree and formatted with
  Prettier 3.10.1, `cli.md` gains the `--verify`/`-vf` line and
  `configuration.md` gains the three `verify` settings and the changed `effort`
  and `instructions` wording. With the user's go-ahead, the pages were then
  regenerated in the repo: `.venv/bin/python scripts/generate_reference_docs.py`
  and `scripts/format_markdown.mjs` with the hook's Prettier 3.10.1 and Node
  24.22.3 changed only `docs/src/content/docs/reference/cli.md` (1 line added)
  and `configuration.md` (15 lines added, 5 removed), as in the scratch copy.

**Implementation Notes**

- The class docstrings of `SurveyConfig` and `ExtractionConfig` say their
  settings apply to the step's requests and its verifier's alike, and `effort`
  and `instructions` no longer speak of page extraction's "models". The YAML
  example's comments follow the docstrings; the JSON example has no comments.
- `--verify` sits after `--no-pause` in the option list.

---

### DEV-003 — Page extraction with an optional verifier

`Status`: `DONE` `Depends On`: `DEV-002` `Acceptance`:
`AC-001, AC-005, AC-006, AC-018, AC-020`

**Goal**

Run page extraction's verifier only when `verify_extraction` is on, list every
difference on pages no verifier reviewed, and price the verifier only when it
will run.

**Affected Area**

`src/pydelity/extracting/extraction.py` (page task, `_kept_answer`,
`_page_issues`, `plan_pages`, the page log line),
`src/pydelity/extracting/llm.py` and `StepModel` (carry the switch),
`src/pydelity/extracting/schemas.py` (`PageFile.verification`, docstrings),
`src/pydelity/costs/budget.py` (`estimate_extraction`),
`src/pydelity/costs/schemas.py` (`StepEstimate.verifier`),
`src/pydelity/report/html.py` (`_verifier_text`),
`src/pydelity/pipeline/runner.py` (estimate lines),
`scripts/smoke_installed_wheel.py` (expected requests with default settings).

**Expected Outcome**

- With `verify_extraction` off, each page runs the extractor with its checks and
  retries, keeps its answer, makes no verifier request and saves
  `verification: null`; with it on, behavior is as today.
- `PageFile.verification` is `PageVerification | None` (required).
  `_page_issues` leaves the text checks off only when `verification` is set and
  the verdict passed or the correction was applied, and adds `verifier` issues
  only when `verification` is set and the correction was not applied.
- `plan_pages` reuses a page file only when its fingerprint matches, `overwrite`
  is off, and either the verifier is off or the file holds a verification; a
  page passed over only for lacking a verification gets an info log line. No
  fingerprint includes the switch.
- The page log line and the report's page card say `no verifier` and
  `no verifier ran` when none ran.
- `StepEstimate.verifier: bool` (required); `estimate_extraction` prices the
  verifier, and `requests_max = 2 * attempts * pages`, only when it is on, else
  `attempts * pages`. The survey's estimate sets `verifier: false` until
  DEV-007. The CLI's estimate lines name a step's verifier when its figures
  include one.
- The smoke script's expected requests match the default settings (no verifier
  requests).

**Self-Check**

Ruff, ty and interrogate on `scripts src`; a scratchpad run of page extraction
against the stand-in provider on a test PDF with defaults, with
`advanced.extraction.verify: true`, and after turning it on over a folder made
without it (pages rerun, survey reused), checking the page files, review list,
ledger lines and estimate figures; turning it off over verified pages reuses
them; the existing tests with replaced-contract failures listed.

Evidence, 2026-11-21, repo root, on `4a6bec7` plus the uncommitted DEV-002 and
DEV-003 changes (macOS arm64, Python 3.13.9, `.venv`). DEV-003 changed
`src/pydelity/extracting/extraction.py`, `extracting/llm.py`,
`extracting/schemas.py`, `costs/budget.py`, `costs/schemas.py`,
`pipeline/runner.py`, `report/html.py`, `scripts/smoke_installed_wheel.py` and
the generated `docs/src/content/docs/reference/page-json.md`.

- Scratch script `dev003/check_pages.py` in the session scratchpad, run with
  `.venv/bin/python -I check_pages.py <repo>` against the stand-in
  (`tests/fixtures/mock_providers.py`) on `irs_form_1040a_1965_scan.pdf` with
  its canned survey and page answers, default model: 30 of 30 checks passed.
  - Default settings: the requests are the upload, the survey and 2 extractor
    requests; both page files have `verification: null`; `cost.jsonl` has no
    `verifier` line; each page lists every failing check and no `verifier`
    issue; both page log lines say `no verifier;`; no estimate line names a
    verifier; `report.html` says `no verifier ran` twice.
  - `advanced={"extraction": {"verify": True}}` on the same folder: the survey
    is reused; both pages are extracted again with 2 extractor and 2 verifier
    requests; each page logs
    `no verifier reviewed its page file, so the page is extracted again with the verifier`;
    the estimate line starts `Extraction with its verifier cost estimate`; 2
    `verifier` ledger lines; the page log lines give the verifier's outcome;
    pages the verifier passed list no text check.
  - Verifier off again: no request, both pages reused with their verification.
    `verify=True` over the verified pages: no request, both reused.
    `verify=True` with `advanced.extraction.verify: false` on a new folder: no
    verifier request.
  - `estimate()` after a paused run with the survey saved: the survey's
    `verifier` is false; extraction's `verifier` is false, then true with
    `verify=True`; `requests_max` 6, then 12. With the verifier, the expected
    and maximum cost equal those of the formula before this step (reproduced in
    the script with `budget._price`), $0.454520 and $10.411560; without it, they
    equal that formula's extractor terms, $0.227552 and $4.810656. A reused
    extraction step has `verifier: false`.
- Scratch script `dev003/check_text_differences.py`: 7 of 7 checks passed. A
  3-page text PDF built with PyMuPDF as the tests' `_text_pdf` does, the tests'
  label set, and an extraction that leaves out the page's last stored line. With
  no verifier: 3 extractor requests and no verifier request; `text_dropped`
  fails and is the page's one review issue, quoting the line; `verification` is
  null; `text_comparison` is `compared`. With the verifier on and a passing
  verdict: 3 extractor requests and 1 verifier request; `text_dropped` stays in
  `checks` and the review list is empty.
- `.venv/bin/ruff check scripts src tests` "All checks passed!";
  `ruff format --check` "89 files already formatted" (after `ruff format` on
  `extraction.py`); `ty check scripts src` "All checks passed!"; `interrogate`
  100.0%; the module order check finds no new departure.
- `ty check scripts src tests` reports 6 errors, all in
  `tests/pydelity/extracting/test_extraction.py` lines 897–916, which read
  `page.verification` attributes without allowing `None`.
- Tests: 14 failed, 163 passed; doctests 27 passed, 1 skipped. Each failure
  expects a verifier on every page by default, the contract this step replaces:
  `tests/pydelity/costs/test_budget.py::test_the_estimate_covers_page_extraction_with_both_models_when_the_run_goes_on`
  (`requests_max` 6, expected 12);
  `tests/pydelity/extracting/test_extraction.py`:
  `test_each_page_request_carries_one_upright_image_and_only_its_own_instructions[anthropic]`
  and `[openai]`,
  `test_the_verifier_s_verdict_decides_the_kept_answer_and_its_issues[passed]`,
  `[correction_kept]` and `[correction_rejected]`,
  `test_a_failed_page_stops_the_run_and_the_next_run_extracts_only_what_is_missing`,
  `test_page_files_rerun_only_when_their_inputs_change`,
  `test_a_page_file_naming_a_missing_crop_is_extracted_again` (no verifier
  request or verdict); `tests/pydelity/pipeline/test_runner.py`:
  `test_a_rerun_with_unchanged_inputs_reuses_everything` (3 requests, expected
  5), `test_run_json_records_each_step_its_pages_cost_and_review_issues` (no
  verifier issue);
  `tests/pydelity/report/test_html.py::test_report_draws_extracted_items_numbered_with_links_from_their_issues`
  (no verifier issue to flag the item); `tests/pydelity/test_cli.py`:
  `test_a_pdf_alone_runs_the_survey_with_keys_from_the_environment` and
  `test_pages_and_no_pause_extract_only_those_pages_in_one_run` (no verifier
  request).
- Reference pages: `generate_reference_docs.py` and `format_markdown.mjs` change
  `page-json.md` only (the `issues` and `verification` descriptions),
  regenerated as for DEV-002 so CI's stale-page check passes.
- Not run: the wheel smoke test (it needs `uv build` and PyPI downloads; CI's
  wheel jobs run it), Python 3.14.

**Implementation Notes**

- `_reusable_page` holds the reuse rule, so `plan_pages` stays simple. The page
  log line's outcome now carries the word `verifier` itself, so a page with no
  verifier says `no verifier`.
- The extractor-only maximum lists each page's extractor attempts before its
  verifier attempts; the sums are unchanged.
- Left for DEV-011: `review.py` (two comments) and `extracting/schemas.py`
  (module docstring) still say "verifier model", as do the generator's check
  texts.

**Correction for recovery frame 1**

Tester found that the smoke script's request check was still named "one upload
and 5 model requests" after `EXPECTED_REQUESTS` became one upload and 3 model
requests (verification report, **Open Findings and Dependencies**). DEV-003 was
reopened for it. `_check_requests` in `scripts/smoke_installed_wheel.py` now
counts the model requests in `EXPECTED_REQUESTS` for the name, so the name
cannot drift from the list again. No other file changed.

Evidence, 2026-11-21, repo root, on `384204a` plus this one change
(`git diff HEAD -- scripts`, 2 insertions and 1 deletion, SHA-256 starting
`e1141021307f15d3`):

- Scratch script `dev003/check_smoke_name.py` loads the script and calls
  `_check_requests` with a stub stand-in: with `EXPECTED_REQUESTS` it prints
  `PASS CLI, anthropic: one upload and 3 model requests, all to the stand-in`;
  with one extra model request it prints the same name as `FAIL`, with the
  requests in the detail. `grep -n "5 model requests"` finds nothing.
- `.venv/bin/ruff check scripts src tests` "All checks passed!";
  `ruff format --check` "89 files already formatted";
  `ty check scripts src tests` "All checks passed!"; `interrogate` 100.0%.
- Tests: 188 passed (with Tester's updated tests in `384204a`); doctests 27
  passed, 1 skipped. `python scripts/smoke_installed_wheel.py --help` exits 0.
- Not run: the full wheel smoke test (it needs `uv build` and PyPI downloads;
  CI's wheel jobs run it).

---

### DEV-004 — Every survey request names its agent

`Status`: `DONE` `Depends On`: `DEV-001` `Acceptance`: `AC-015, AC-016`

**Goal**

Make every request of every step name its agent, so survey and survey-verifier
requests can be told apart in `cost.jsonl` and go through the same reservation
path.

**Affected Area**

`src/pydelity/providers/ledger_model.py` (a wrapper method that names an agent
without a page, beside `for_page`), `src/pydelity/costs/schemas.py`
(`LedgerEntry.agent: str`), `src/pydelity/surveying/llm.py` and
`src/pydelity/surveying/agents.py` (the survey request through the `surveyor`
wrapper), `src/pydelity/pipeline/runner.py` if it builds the survey's context,
`scripts/smoke_installed_wheel.py` if it checks ledger agents.

**Expected Outcome**

- `LedgerEntry.agent` is a required `str`; a `cost.jsonl` whose lines have
  `agent: null` no longer validates and is treated as damaged.
- The survey's own requests write `agent: "surveyor"`, `step: "survey"`,
  `page_index: null`; page extraction's stay `extractor` and `verifier`.
- Each survey request's reservation still counts the PDF's tokens and goes
  through `SpendGuard`.

**Self-Check**

Ruff, ty and interrogate; a scratchpad survey run against the stand-in checking
the ledger lines and that a ledger with `agent: null` lines raises
`OutputError`; the existing tests with replaced-contract failures listed.

Evidence, 2026-11-21, repo root, on `50aca23` plus the uncommitted DEV-004
changes to `src/pydelity/providers/ledger_model.py`, `costs/schemas.py`,
`surveying/llm.py` and the generated
`docs/src/content/docs/reference/cost-jsonl.md` (macOS arm64, Python 3.13.9,
`.venv`). `surveying/agents.py`, `pipeline/runner.py` and the smoke script
needed no change.

- Scratch script `dev004/check_agents.py` in the session scratchpad, run with
  `.venv/bin/python -I check_agents.py <repo>` against the stand-in on
  `irs_form_1040a_1965_scan.pdf` with its canned answers: 9 of 9 checks passed.
  - A run that pauses after the survey writes ledger lines that all have
    `agent: "surveyor"`, `step: "survey"`, `page_index: null`. With
    `SpendGuard.reserve` wrapped to record each bound, every survey reservation
    is at least the price of the PDF's tokens (2 pages times
    `pdf_tokens_per_page`) with `max_output_tokens` of output, $0.702272.
  - After page extraction, the survey lines stay `surveyor` and the page lines
    are `extractor` for pages 0 and 1.
  - A copy of that `cost.jsonl` with every `agent` set to null stops the next
    run with `OutputError`
    (`cost.jsonl: line 1 is damaged, and it is not the last line`), and the
    stand-in receives no request.
  - A `LedgerModel` around PydanticAI's `TestModel` with a context that names no
    agent raises `RuntimeError`
    (`... requests must go through a wrapper that names their agent`) before any
    reservation, and writes no ledger line. Its `for_agent(agent="surveyor")`
    wrapper keeps the PDF in its context and records one line with
    `agent: "surveyor"`, `page_index: null`, `step: "survey"`.
- `.venv/bin/ruff check scripts src tests` "All checks passed!";
  `ruff format --check` "89 files already formatted";
  `ty check scripts src tests` "All checks passed!"; `interrogate` 100.0%; the
  module order check finds no new departure.
- Tests: 188 passed; doctests 27 passed, 1 skipped. No existing test reads a
  survey ledger line's agent or builds a `LedgerContext`, so no test fails.
- Reference pages: `generate_reference_docs.py` and `format_markdown.mjs` change
  only the `agent` entry of `cost-jsonl.md`, which now says `string`, required,
  `surveyor` or `verifier` for the survey and `extractor` or `verifier` for page
  extraction. The survey's `verifier` agent arrives with DEV-005; Increment 3 is
  assessed as a whole.

**Implementation Notes**

- `LedgerModel.for_agent` sits beside `for_page`. The step's own wrapper keeps
  `agent: None`, since `attach_pdf` uses it for the provider's client, and a
  private `_agent` check makes any request through it fail before anything is
  reserved or sent.
- `surveying/llm.py` names the agent with a `SURVEYOR` constant, as
  `extracting/llm.py` does with `EXTRACTOR` and `VERIFIER`.

---

### DEV-005 — The survey verifier's verdict, prompt, agent and request

`Status`: `DONE` `Depends On`: `DEV-004` `Acceptance`:
`AC-007, AC-008, AC-009, AC-012, AC-017`

**Goal**

Build the survey verifier's request and verdict, mirroring page extraction's
verifier, without yet applying it in the survey step.

**Affected Area**

`src/pydelity/surveying/schemas.py` (`SurveyProblem`, `SurveyVerdict`,
`SurveyVerification`), `src/pydelity/surveying/prompts.py` (`verify_survey`,
with shared rule text moved into sections both prompts use),
`src/pydelity/surveying/agents.py` (the verifier agent with
`retries={"output": check_retries}` and an output validator running C1–C7 on the
correction), `src/pydelity/surveying/llm.py` (asking the verifier on the survey
request's attachment, retrying once with a fresh upload when the file is gone,
and the error mapping of decision 10).

**Expected Outcome**

- The schemas follow **Survey verdict**, with the Pydantic invariants of
  `VerifierVerdict`, plain types only.
- `verify_survey` returns a `PromptPair` as decision 7 describes; the user
  message contains `The survey answer to review:`;
  `advanced.survey.instructions` comes last; no prompt names a document type,
  language or direction; what `survey_pdf`'s messages say is unchanged.
- The verifier request sends `[attachment.content, user message, CachePoint()]`
  through the `verifier` wrapper, with the survey request's attachment, so a
  usable recorded upload is reused and no new upload is made.
- A correction failing C1–C7 is sent back with the design's retry message while
  `check_retries` allows; the result carries the verdict, its attempts and the
  rejected correction's check failures.
- A failed verifier request maps to `ProviderError` or `SurveyError` naming the
  verifier as in `surveying/llm.py` `_run_agent`.

**Self-Check**

Ruff, ty and interrogate; a scratchpad script with PydanticAI's `FunctionModel`
that checks the request's content and instructions, a correction sent back for a
failed check, the last-attempt acceptance, and the error mapping; the existing
tests.

**Evidence**

Evidence, 2026-11-21, repo root, on `dbc6aed` plus the uncommitted DEV-005
changes to `src/pydelity/surveying/schemas.py`, `prompts.py`, `agents.py`,
`llm.py` and `survey.py` (macOS arm64, Python 3.13.9, `.venv`). `survey.py`
changes only to call `ask_model` with the new `SurveyStep`; the survey step does
not yet run the verifier.

- `survey_pdf`'s messages before and after the change, for three inputs (with
  and without instructions, languages and repeated lines; 1, 2 and 40 pages),
  compare byte for byte equal (scratch `dev005/survey_prompt_snapshot.py`).
- Scratch script `dev005/check_verifier.py` in the session scratchpad, run with
  `.venv/bin/python -I check_verifier.py <repo>`, with PydanticAI's
  `FunctionModel` inside the real `LedgerModel`, the measured facts of
  `irs_form_1040a_1965_scan.pdf` and its canned survey answer: 42 of 42 checks
  passed.
  - `SurveyVerdict` accepts passed with nothing else and failed with problems,
    with or without a correction; it rejects passed with a problem or a
    correction, failed without a problem, and an unknown category. Its JSON
    schema has no pattern, bound or format.
  - After `ask_model`, `ask_verifier` sends
    `[UploadedFile(file-abc), user message, CachePoint()]` with the survey's
    attachment; `attach_pdf` runs once, for the survey, and no replacement
    upload is made. The ledger has one `surveyor` line, then one `verifier`
    line, both `step: "survey"`, `page_index: null`.
  - The user message is `verify_survey`'s: the survey's own user message, then
    the line `The survey answer to review:` and the answer as JSON, then
    `Checks it still fails:` (`none`) and `Differences from the measured facts:`
    (the `compare_with_facts` messages, or `none`). The instructions run from
    the audit task through the review list, the verdict rules, the page index
    conventions and the survey's rules from labels to notes, and end with
    `advanced.survey.instructions` under the survey's heading. They name no
    document type or language.
  - A correction failing C1–C7 is sent back once with "Your corrected survey
    does not pass every check. Give the whole verdict again, with the correction
    fixed." and the survey's `retry_message`, naming the failure; the fixed
    correction is accepted with `attempts` 2 and no correction failures. With
    `check_retries` 1 the second bad correction is accepted with its failures;
    with 0 the first is.
  - Errors: a refusal gives `SurveyError` "The verifier refused to review the
    survey. ..."; running out of output tokens "The verifier used all 32,000
    output tokens before finishing its answer. Raise
    advanced.survey.max_output_tokens, or lower advanced.survey.effort."; no
    matching verdict, or one breaking the invariants, "The verifier gave no
    usable verdict on the survey: ...". A 400 after an inline fallback gives
    `ProviderError` with "The upload had failed before: ...", and no replacement
    upload.
  - A 404 naming the file makes one replacement upload, calls `on_attached` with
    its transport and repeats the review on the new file; a second 404 raises
    `ProviderError` with no second replacement.
- `ruff check` "All checks passed!"; `ruff format --check scripts src tests` "89
  files already formatted"; `ty check scripts src tests` "All checks passed!";
  `interrogate` 100.0%; the module order check finds no new departure in the
  four survey modules.
- Tests: 188 passed; doctests 28 passed, 1 skipped (the new one is
  `verify_survey`'s).
- `generate_reference_docs.py` and `format_markdown.mjs` change no reference
  page: `PdfSurvey` gains `verification` in DEV-006.

**Implementation Notes**

- `surveying/schemas.py` adds the alias `SurveyProblemCategory` and the three
  classes after `SurveyAnswer`, which `SurveyVerdict.corrected` needs above it.
  Fields are in alphabetical order, as in `VerifierVerdict`.
- `surveying/prompts.py` moves the text both prompts share into `_CONVENTIONS`
  (page indexes, ranges and positions) and `_RULES` (labels through notes), and
  the user instructions into `_with_user_instructions`. The verifier gets
  `_CONVENTIONS` too, since a correction gives page ranges. `verify_survey`
  takes the survey request's own user message rather than rebuilding it.
- `surveying/llm.py`: `SurveyStep` (config, facts, model, `on_attached`, PDF)
  carries what every survey request needs, as `StepModel` and `PageInput` do for
  page extraction, so `ask_model(step)` and `ask_verifier(step, surveyed=...)`
  stay within the argument limit. `_run_with_upload` holds the one replacement
  upload both requests use. `ModelSurvey` gains `prompts`; the survey's own
  `ModelVerdict` also carries the attachment, so the step can report how the
  last request carried the PDF. The survey's error messages are unchanged.

---

### DEV-006 — The survey applies the verdict

`Status`: `DONE` `Depends On`: `DEV-002, DEV-005` `Acceptance`:
`AC-001, AC-006, AC-008, AC-010, AC-011, AC-013, AC-014, AC-017`

**Goal**

Run the survey's verifier when `verify_survey` is on, keep the right answer,
build the review list, save the verification and show it in the report.

**Affected Area**

`src/pydelity/surveying/survey.py` (`run_survey`, `build_survey`,
`saved_survey`, the log line), `src/pydelity/surveying/schemas.py`
(`PdfSurvey.verification`, `issues` and `checks` docstrings),
`src/pydelity/review.py` (`verifier` shared by both steps),
`src/pydelity/report/html.py` (the survey's verifier text),
`src/pydelity/pipeline/runner.py` (the failed-step path, if it needs a change).

**Expected Outcome**

- **Survey verdict application** steps 1–5: the kept answer, `checks` with the
  kept answer's attempts, `issues` in the design's order, and the log line's
  outcome.
- `PdfSurvey.verification` is required and `null` exactly when no verifier ran;
  an old `pdf_survey.json` without it is surveyed again with `damaged_output`.
- `saved_survey` reuses a file only under decision 2's rule, with an info log
  line when it is passed over only for lacking a verification.
- A failed verifier request ends the survey step `failed`, writes no
  `pdf_survey.json` and leaves an existing one as it was.
- The report's profile section shows one of the four verifier texts.

**Self-Check**

Ruff, ty and interrogate; a scratchpad run against the stand-in with
`advanced.survey.verify: true` and a fault-injecting scratch model for each
outcome (passed, correction kept, correction not kept, no correction, failed
request), checking `pdf_survey.json`, `run.json`'s review list, the report text
and the exit code; the existing tests.

**Evidence**

Evidence, 2026-11-21, repo root, on `e4d479f` plus the uncommitted DEV-006
changes to `src/pydelity/surveying/survey.py`, `surveying/schemas.py`,
`review.py`, `report/html.py`, `pipeline/runner.py` and the generated
`docs/src/content/docs/reference/pdf-survey-json.md`, `page-json.md` and
`run-json.md` (macOS arm64, Python 3.13.9, `.venv`).

- Scratch script `dev006/check_survey_verdict.py` in the session scratchpad, run
  with `.venv/bin/python -I check_survey_verdict.py <repo>` against the stand-in
  on `irs_form_1040a_1965_scan.pdf`, with the survey's canned answer and then
  the verdicts queued as later answers: 51 of 51 checks passed.
  - Verifier off (the default): `verification: null`, the last key of
    `pdf_survey.json`; one `surveyor` ledger line; the report's survey section
    says "Verifier: no verifier ran"; the log line says `no verifier`.
  - With `advanced.survey.verify: true`:
    - **Passed:** the answer is kept, with `verification` passed, 1 attempt and
      no failures. There is one upload and two model requests; the `surveyor`
      line comes before the `verifier` line. `run.json`'s survey step shows 2
      requests, transport `upload`, `completed`. The report says `passed` and
      the log line `verifier passed`.
    - **Correction kept**, run with `languages: ["fr"]`: the profile and
      proposal come from the correction, `fr` stays first, and the facts copy
      equals `pdf_facts.json`'s. No `verifier` issue is listed; the checks carry
      the verifier's attempts. The report says "found 1 problem and its
      correction was kept" and the log line `verifier corrected the survey`.
    - **Correction not kept**: every one of 3 verdicts gives a correction that
      fails C7. The survey's answer is kept, with checks at its own attempts,
      and `correction_failures` holds the `languages` result with attempts 3.
      The review list in `pdf_survey.json` and `run.json` is the design's single
      `verifier` issue (`details: {"category": "labels"}`, the problem's
      `page_index`, `item_id: null`). The report says "found 1 problem, listed
      for review"; the ledger has `surveyor` then three `verifier` lines.
    - **No correction**, two problems: two `verifier` issues in problem order;
      the report says "found 2 problems, listed for review" and the log line
      `verifier found 2 problems`.
  - Reuse:
    - A survey made without a verifier is reused while the verifier is off. It
      is run again, with the line "No verifier reviewed the survey in ..., so
      the survey runs again with the verifier", once it is on.
    - `pydelity.estimate` calls it not reused with the verifier on and reused
      with it off.
    - A reviewed survey is reused with the verifier either on or off, with no
      survey request.
  - An old `pdf_survey.json` without `verification` gives `damaged_output` and a
    new survey request.
  - Failed verifier request:
    - Three answers that are not verdicts raise `SurveyError` "The verifier gave
      no usable verdict on the survey: ...".
    - A 400 injected into only the verifier's request raises `ProviderError`
      with the provider's message.
    - Either way, `run.json`'s survey step is `failed` with the error and the
      ledger keeps the survey's paid line. No `pdf_survey.json` is written, or
      an existing unreviewed one is left byte for byte as it was.
    - The CLI with `--verify --yes` exits 1 and shows the error.
  - `build_survey` with facts edited to give a `rotation_differs` lists:
    - with no verifier, `languages` then `rotation_differs`;
    - with a passed verdict or a kept correction, `languages` only;
    - with a correction not kept, `languages`, `rotation_differs`, then one
      `verifier` issue per problem.
- The DEV-004 and DEV-005 scratch checks still pass (9 of 9, 42 of 42).
- `ruff check` "All checks passed!"; `ruff format --check scripts src tests` "89
  files already formatted"; `ty check scripts src` "All checks passed!";
  `interrogate` 100.0%; doctests 28 passed, 1 skipped.
- The module order check finds one new departure, `PdfSurvey` below
  `SurveyVerification`, now listed above; `ProposedRegion` and `SurveyAnswer`
  moved up to keep the rest alphabetical. A comparison with `e4d479f` finds
  every class but `PdfSurvey` unchanged apart from its place.
- Reference pages:
  - `pdf-survey-json.md` gains `verification` and its parts, and the new
    `checks` and `issues` texts.
  - `page-json.md`, `run-json.md` and `pdf-survey-json.md` list `verifier` as
    its own issue name, after `page_number_differs`.
- Tests: 176 passed, 12 failed. Each failure is a replaced contract, for Tester
  in Increment 3:
  - Ten tests pass the global `verify=True`, which now runs the survey's
    verifier too, while the stand-in answers that request with a survey answer:
    - `test_extraction.py`:
      `test_each_page_request_carries_one_upright_image_and_only_its_own_instructions`
      (both providers) and
      `test_the_verifier_s_verdict_decides_the_kept_answer_and_its_issues` (all
      three outcomes);
    - `test_html.py`:
      `test_report_draws_extracted_items_numbered_with_links_from_their_issues`;
    - `test_budget.py`:
      `test_estimate_writes_nothing_and_a_reusable_survey_costs_nothing`;
    - `test_runner.py`:
      `test_run_json_records_each_step_its_pages_cost_and_review_issues`;
    - `test_cli.py`:
      `test_verify_adds_a_verifier_request_for_each_page_and_to_the_estimate`
      (`--verify` and `-vf`).
  - `test_html.py::test_a_page_no_verifier_reviewed_says_so_in_the_report`
    counts two "no verifier ran" lines, and the survey section now adds a third.
  - `test_survey.py::test_profile_owns_other_dedupes_kinds_and_converts_region_boxes`
    calls `build_survey` without the new required `verification`;
    `ty check tests` reports the same one call.

**Implementation Notes**

- `survey.py` mirrors page extraction: a private `_KeptAnswer` and
  `_kept_answer` apply the verdict, `_verifier_issue` and `_verifier_outcome`
  give the issue and the log text. `build_survey` takes the kept answer, its
  attempts and the required `verification`, and builds the review list. A
  correction is kept only when it passes every check.
- `run_survey` returns the transport of the verifier's last request when the
  verifier ran, so a replacement upload is reported.
- `saved_survey` gains `quiet`, as `plan_pages` has. The runner's private
  `_reusable_survey` is gone: the estimate calls `saved_survey(quiet=True)`, so
  both follow the same reuse rule.
- `review.py`: `ExtractionIssueName` is `no_matching_label` alone, and the new
  `VerifierIssueName` (`verifier`) is shared by both steps.
- `report/html.py`: the existing `_verifier_text` takes a page's or the survey's
  verification, and the profile section's details end with "Verifier".

---

### DEV-007 — The survey verifier in estimates

`Status`: `DONE` `Depends On`: `DEV-003, DEV-005` `Acceptance`:
`AC-005, AC-015, AC-016`

**Goal**

Price the survey's verifier in every estimate when it will run, and report its
cost in the survey's cost.

**Affected Area**

`src/pydelity/costs/budget.py` (`estimate_survey`,
`TYPICAL_SURVEY_VERDICT_OUTPUT_TOKENS = 6_000`),
`src/pydelity/pipeline/runner.py` (the verifier's prompt size beside
`_prompt_chars`, the estimate lines), `src/pydelity/pipeline/schemas.py` only if
`RunCost.by_step` does not already sum every survey line.

**Expected Outcome**

- Decision 9 for the survey: expected adds one verifier request, maximum adds
  `check_retries + 1`, `requests_max` is `2 * (check_retries + 1)`, and
  `StepEstimate.verifier` is true, only when `verify_survey` is on, in the CLI's
  estimate, the run's plan-time check, `estimate()` and `aestimate()`.
- The verifier's prompt size is measured from its messages with an empty
  `SurveyAnswer` plus `SurveyVerdict`'s JSON schema.
- The run's survey cost and the step's log line include verifier lines.

**Self-Check**

Ruff, ty and interrogate; a scratchpad script comparing `estimate()` with the
survey verifier off and on and checking the arithmetic by hand; a stand-in run
with `max_cost` below the verified estimate, answered no and yes; the existing
tests.

**Evidence**

Evidence, 2026-11-21, repo root, on `7804c97` plus the uncommitted DEV-007
changes to `src/pydelity/costs/budget.py`, `pipeline/runner.py` and the
generated `docs/src/content/docs/reference/cost-jsonl.md` (macOS arm64, Python
3.13.9, `.venv`). `pipeline/schemas.py` needed no change: `RunCost.by_step` sums
every ledger line by step, the verifier's included.

- Scratch script `dev007/check_estimates.py` in the session scratchpad, run with
  `.venv/bin/python -I check_estimates.py <repo>` against the stand-in on
  `irs_form_1040a_1965_scan.pdf`: 21 of 21 checks passed.
  - `estimate()` with the survey's verifier off gives `verifier: false`,
    `requests_max` 3, expected $0.235352 and at most $2.530056. With
    `advanced.survey.verify: true` it gives `verifier: true`, `requests_max` 6,
    expected $0.466232 and at most $5.454696. Both equal a price worked out by
    hand in the script, from the prompts built again and `price_usage`:
    - expected adds one verifier request reading the PDF, the verifier's prompt
      (an empty `SurveyAnswer`, plus `SurveyVerdict`'s schema) and 8,000 tokens
      of answer, giving 6,000;
    - maximum adds 3 requests of `max_output_tokens`, with `(attempt + 1)`
      longest answers in their input.
  - `aestimate()` and the global `verify=True` give the same survey estimate.
    With `pause=False`, the survey's estimate is the same and page extraction's
    has no verifier. A reused survey costs 0, with `verifier: false`.
  - A verified run's estimate line reads "Survey with its verifier cost
    estimate: ... (up to 6 requests ...)". Its ledger has a `surveyor` and a
    `verifier` line; `run.json`'s `cost.by_step.survey` and the step's
    `cost_usd` equal both lines' sum ($0.048), and the survey's log line says
    "for 2 requests".
  - With `max_cost` $0.3508, between the two expected costs, only the verified
    estimate is over `max_cost`:
    - Python without `allow_over_max_cost` raises `BudgetExceededError` before
      any model request; with it, the survey and its verifier run.
    - The CLI with `--verify --max-cost` asks "Go ahead, even though this run
      could go over max_cost?". Answered `n`, it exits 3 with no model request;
      answered `y`, it exits 0 after 2 model requests.
- The DEV-004, DEV-005 and DEV-006 scratch checks still pass (9 of 9, 42 of 42,
  51 of 51).
- `ruff check` "All checks passed!"; `ruff format --check scripts src tests` "89
  files already formatted"; `ty check scripts src` "All checks passed!";
  `interrogate` 100.0%; doctests 28 passed, 1 skipped; the module order check
  finds no new departure.
- Tests: 176 passed and the same 12 failed as under DEV-006; no test calls
  `estimate_survey`.
- `cost-jsonl.md` gains `TYPICAL_SURVEY_VERDICT_OUTPUT_TOKENS` = `6000`.

**Implementation Notes**

- `estimate_survey` gains `verifier_chars` and prices the verifier as
  `estimate_extraction` prices the page verifier, with the answer it reads and
  its verdict each capped at `max_output_tokens`.
- `_prompt_chars` in `pipeline/runner.py` returns the survey's and the
  verifier's prompt sizes, so every estimate path (`_survey_estimate`) gets
  both.

---

### DEV-008 — `load()` returns only the folder's PDF's page files

`Status`: `DONE` `Depends On`: `DEV-001` `Acceptance`: `AC-021`

**Goal**

Leave other PDFs' page files out of `load()`.

**Affected Area**

`src/pydelity/pipeline/runner.py` (`_load_pages`, `load_run`),
`src/pydelity/pipeline/schemas.py` (`RunResult.pages` docstring).

**Expected Outcome**

`load()` returns only page files whose `inputs.pdf_sha256` equals
`pdf_facts.json`'s `pdf.sha256`, in page order, comparing the hash before the
figure-crop check; no `pdf_facts.json` means no pages; a page file that does not
validate still raises `OutputError`. The docstring says what each function
returns.

**Self-Check**

Ruff, ty and interrogate; a scratchpad folder holding two PDFs' page files, one
with a missing crop, loaded with and without `pdf_facts.json`; the existing
tests.

**Evidence**

Evidence, 2026-11-21, repo root, on `83faebb` plus the uncommitted DEV-008
changes to `src/pydelity/pipeline/runner.py`, `pipeline/schemas.py`,
`src/pydelity/api.py` (the public `load` docstring, which repeated the old
wording) and the generated `docs/src/content/docs/reference/python-api.md`
(macOS arm64, Python 3.13.9, `.venv`).

- Scratch script `dev008/check_load.py` in the session scratchpad, run with
  `.venv/bin/python -I check_load.py <repo>`, on a folder from a stand-in run of
  `irs_form_1040a_1965_scan.pdf` (pages 0 and 1): 10 of 10 checks passed.
  - Added page files 3 and 5, with `inputs.pdf_sha256` set to another PDF's and
    each holding a figure item. Page 3's image exists and page 5's is missing.
    `load()` returns pages 0 and 1, with no error.
  - A figure image missing from one of this PDF's own page files still raises
    `OutputError` naming it, and a page file that is not valid JSON
    (`pages/0007.json`) raises `OutputError`.
  - With `pdf_facts.json` removed, each of those folders loads with no pages and
    `facts: None`, while `run.json` and `pdf_survey.json` still load. With facts
    naming another PDF, no page is returned.
  - A run in the mixed folder still returns its own selected pages, 0 and 1.
- `ruff check` "All checks passed!"; `ruff format --check scripts src tests` "89
  files already formatted"; `ty check scripts src tests` "All checks passed!";
  `interrogate` 100.0%; doctests 28 passed, 1 skipped; the module order check
  finds no new departure.
- Tests: 200 passed.
- Reference pages: `python-api.md` changes only in `load`'s return and error
  text.

**Implementation Notes**

- `_load_pages` takes the facts' `sha256`, or `None` without `pdf_facts.json`,
  and returns no pages for `None` without reading `pages/`. So a page file that
  is not valid JSON raises only when the folder has facts.
- `load_run` passes the facts it already reads; nothing else reads them again.

---

### DEV-009 — Report tables keep body cells in their columns

`Status`: `DONE` `Depends On`: `DEV-001` `Acceptance`: `AC-022`

**Goal**

Render a table's rows in one row group so a header cell's `rowspan` reaches the
body rows.

**Affected Area**

`src/pydelity/report/html.py` (`_item_table`).

**Expected Outcome**

Every row goes in one row group, header-row cells as `th`; a header cell whose
`row_span` passes `header_rows` leaves every body cell in the column the page
file gives it.

**Self-Check**

Ruff, ty and interrogate; a scratchpad page file with such a table rendered and
its HTML parsed to check each cell's column; the existing tests.

**Evidence**

Evidence, 2026-11-21, repo root, on `a307946` plus the uncommitted DEV-009
change to `src/pydelity/report/html.py` (macOS arm64, Python 3.13.9, `.venv`).

- Scratch script `dev009/check_tables.py` in the session scratchpad, run with
  `.venv/bin/python -I check_tables.py <repo>`: 13 of 13 checks passed.
  - The script parses the rendered table with the standard library's HTML parser
    and places each cell as the HTML table model does, ending a row span at the
    end of its row group. It compares each cell's column with the page file's
    own grid.
  - Four tables: a header cell spanning two body rows; two header rows with a
    column span and a row span through the whole body; no header rows; spans
    inside the header only.
  - After the fix, every cell is in the page file's column, in one row group,
    with header-row cells `th scope="col"`, body cells `td`, and every span as
    given. `_item_table` at `a307946`, run on the same tables, puts the body
    cells of the first two one column to the left; the other two are unchanged.
- In the built-in browser, the first table before and after the fix, served from
  the scratchpad on `127.0.0.1`: before, the spanning header cell stops at the
  header row and `b1` and `c1` sit under its own column and the next; after, it
  spans all three rows and `b1` and `c1` sit under "Item" and "Amount".
- `ruff check` "All checks passed!"; `ruff format --check scripts src tests` "89
  files already formatted"; `ty check scripts src tests` "All checks passed!";
  `interrogate` 100.0%; doctests 28 passed, 1 skipped.
- Tests: 200 passed. No test or stylesheet refers to `thead`.
- Reference pages: no change.

**Implementation Notes**

- Only `_item_table` changes. The report's other tables (`_table`) keep their
  `thead`: their one header row has no spans.

---

### DEV-010 — Probe fixes for outline links and inline widgets, and the `TEXT_FLAGS` comment

`Status`: `DONE` `Depends On`: `DEV-001` `Acceptance`: `AC-023, AC-024, AC-025`

**Goal**

Keep the readable bookmarks and form fields of PDFs with a dangling outline link
or an inline widget, and correct the `TEXT_FLAGS` comment.

**Affected Area**

`src/pydelity/surveying/probe.py` (`_cut_outline_cycle`, `_form`,
`_field_error`), `src/pydelity/utils/pdf.py` (comment only).

**Expected Outcome**

- An outline `First` or `Next` link to an object number outside
  `1..xref_length() - 1` is set to null in the open document, and the walk
  carries on, so `get_toc` reads every bookmark reachable without that link, in
  reading order, with no blank entry and no probe error; a cycle after the link
  is still cut (the corrected design, plan revision 1). Which PyMuPDF calls
  raise on such a number is confirmed first.
- An annotation with object number 0 is skipped with one `form` probe error
  naming its page, without reading keys of object 0, and the other fields are
  kept; `_field_error` never reads keys of object 0.
- The `TEXT_FLAGS` comment says text is clipped to the page's CropBox.
- `PROBE_VERSION` is not raised.

**Self-Check**

Ruff, ty and interrogate; scratchpad PDFs built with PyMuPDF (not added to the
repo) with a dangling `Next` link and with an inline widget, probed before and
after the fix; the existing tests.

**Evidence**

Evidence, 2026-11-21, repo root, on `c7d8ac7` plus the uncommitted DEV-010
changes to `src/pydelity/surveying/probe.py` and `src/pydelity/utils/pdf.py`
(macOS arm64, Python 3.13.9, `.venv`, PyMuPDF 2.1).

- PyMuPDF calls confirmed first (scratch `dev010/confirm.py`, on PDFs built by
  `dev010/make_pdfs.py` in the session scratchpad):
  - `Document.xref_get_key` and `xref_set_key` raise `ValueError: bad xref` for
    object 0 and for any number at or past `xref_length()`. `get_toc` raises on
    neither; it reads the outline and returns `[level, " ", -1]` where the
    missing object would be.
  - `Page.annot_xrefs()` gives an inline widget object number 0.
    `load_widget(0)` loads the first inline widget on the page, so a second one
    comes back as the first. Reading an inline checkbox's state by object number
    raises, and `_field_error` then raises again on object 0's keys.
  - `get_text` leaves out text outside the CropBox, with or without
    `TEXT_MEDIABOX_CLIP`, since PyMuPDF reads within the page's displayed area.
- Scratch script `dev010/check_probe.py`, run with
  `.venv/bin/python -I check_probe.py`, compares `probe_pdf` at `c7d8ac7` with
  the fix: 11 of 11 checks passed.
  - Outline cases, each with a link to an object the PDF does not have:
    - a `Next` on the last top-level entry;
    - a `First` on a leaf entry, with a `Next` to `0 0 R`;
    - a `Next` in the middle of the top level;
    - the catalog's `Outlines` itself;
    - a cycle (`C` → `A`) together with a dangling `First`.

    Before the fix, each gave no bookmarks and the probe error
    `ValueError: bad xref`; the cycle case gave no bookmarks. After it, each
    gives exactly what `get_toc` reads, with no probe error. For the cycle case
    that means `get_toc` on the same PDF with only the cycle link removed.

  - Inline widgets, each beside a normal text field (`kept`, page index 1):
    - one inline text field: before, kept as `inline`;
    - two inline text fields: before, recorded as `first` twice;
    - an inline checkbox: before, every field lost, with `bad xref`.

    After the fix, each keeps only `kept`, with one `form` probe error per
    inline widget: "Page 2 (index 1): a form field written inside the page's
    annotation list has no object number, so it was not read".

  - `_field_error` on object 0 returns "Field object 0: ..." without reading a
    key (before: `bad xref`). A PDF with no inline field gives the same facts
    before and after. `PROBE_VERSION` is unchanged.
- `probe_pdf` gives the same facts before and after for all 10 PDFs in
  `tests/fixtures/pdfs/`.
- `ruff check` "All checks passed!"; `ruff format --check scripts src tests` "89
  files already formatted"; `ty check scripts src tests` "All checks passed!";
  `interrogate` 100.0%; doctests 28 passed, 1 skipped.
- Tests: 200 passed. Reference pages: no change.

**Implementation Notes**

- `_cut_outline_cycle` skips a link outside `1..xref_length() - 1`, the
  `Outlines` root included, and leaves it in the document, so `get_toc` reads
  the outline as 0.1.x did (`AC-023`), placeholder entry included.
- Observation, for the user: if dangling links were set to null instead,
  `get_toc` would read every remaining entry with no blank placeholder. For
  example, a dangling `First` on a leaf now loses the entries after it. That
  goes beyond `AC-023`'s "as 0.1.x did", so it is not done here.
- `_form` skips object 0 before loading it. `_field_error` reads no key of
  object 0, though `_form` no longer passes it one.

**Rework Evidence (plan revision 1)**

Evidence, 2026-11-21, repo root, on `81d7dcd` plus the uncommitted rework of
`src/pydelity/surveying/probe.py`: `git diff HEAD -- src scripts examples docs`
has 14 insertions and 11 deletions, SHA-256 starting `1f9284d55a30de84` (macOS
arm64, Python 3.13.9, `.venv`, PyMuPDF 2.1).

- `_cut_outline_cycle` is renamed `_cut_broken_outline_links`, as the design
  allows. It sets a `First` or `Next` link to an object outside
  `1..xref_length() - 1` to null in the open document and carries on. The
  `_bookmarks` docstring says so too.
- Scratch `dev010/check_probe.py`, updated to the corrected rule: 12 of 12
  checks passed. The expected bookmarks are worked out independently, by setting
  every dangling link to null by hand and calling `get_toc`.
  - A dangling `Next` on the last entry, or a dangling `First` on a leaf, now
    gives all five bookmarks, A, B, B1, B2 and C, with no blank entry and no
    probe error. A dangling `Next` mid-level gives A, the only one reachable,
    and a dangling `Outlines` root gives none.
  - A cycle together with a dangling `First` gives the same five bookmarks as
    the PDF without the cycle.
  - The walk changes the open document's outline but not the file's bytes.
  - The inline-widget, `_field_error` and `PROBE_VERSION` checks pass unchanged.
- `probe_pdf` gives the same facts as at `c7d8ac7` for all 10 fixture PDFs.
- `ruff check`, `ruff format --check scripts src tests` (89 files),
  `ty check scripts src tests` and `interrogate` clean; doctests 28 passed, 1
  skipped. Reference pages: no change.
- Tests: 205 passed, 2 failed. Both are Tester's tests of the replaced rule, for
  full verification: the two rows (`first`, `next`) of
  `test_probe.py::test_outline_links_to_missing_objects_keep_the_bookmarks_pymupdf_reads`
  expect the blank entry the corrected design removes.

---

### DEV-011 — Docstrings, reference pages and the package description

`Status`: `DONE` `Depends On`:
`DEV-003, DEV-006, DEV-007, DEV-008, DEV-009, DEV-010` `Acceptance`:
`AC-028, AC-030, AC-033`

**Goal**

Make the code's docstrings, the generated reference pages and the package text
describe 0.2.0 as built.

**Affected Area**

`src/pydelity/extracting/prompts.py` (docstrings, and the extraction model's
instructions, under plan revision 1), `src/pydelity/extracting/text_layer.py`
(docstrings), `scripts/generate_reference_docs.py` (the hand-written check
texts: the survey checks page gains `verifier`, and the extraction checks page's
wording no longer calls the verifier a model or says it reviews every page; the
generated type text says "one of" for a list of one name, such as `verifier`;
the `verification` fields' `None` wording was dropped, see Evidence), any other
docstring or comment that still calls the verifier a model (such as in
`src/pydelity/review.py` and `src/pydelity/extracting/schemas.py`),
`pyproject.toml` (`description`), the generated pages under
`docs/src/content/docs/reference/`.

**Expected Outcome**

- No docstring says pydelity sends none of the PDF's stored text; they say the
  page's repeated lines with their stored text and its form fields are sent, and
  text retry messages quote stored lines.
- The reference pages, regenerated, cover the new settings, `--verify`/`-vf`,
  `PdfSurvey.verification` and its parts, the nullable `PageFile.verification`,
  `StepEstimate.verifier`, the required `LedgerEntry.agent`, and the survey's
  `verifier` issue.
- `pyproject.toml`'s description says pydelity surveys a PDF and extracts its
  pages, with an optional verifier for each step.
- Plan revision 1: the extraction model's instructions end "Your answer is
  checked by code. You will be told what to fix if a check fails." They no
  longer say a second model reviews the answer. `PROMPT_VERSION` stays 1, as the
  scope says.
- The wheel smoke test runs the survey and page extraction with default settings
  from the built wheel.

**Self-Check**

`.venv/bin/python scripts/generate_reference_docs.py` and a review of the diff;
ruff, ty and interrogate; `uv build` and `twine check --strict` (or the
`.venv/bin` equivalents where uv cannot write its cache);
`python scripts/smoke_installed_wheel.py`; the full test and doctest run.

**Evidence**

Evidence, 2026-11-21, repo root, on `7311f93` plus the uncommitted DEV-011
changes: `git diff HEAD -- src scripts examples docs pyproject.toml` has 163
insertions and 57 deletions over 13 files, SHA-256 starting `b00a83ede04aedb0`
(macOS arm64, Python 3.13.9, `.venv`).

- Plan revision 1: the extraction model's instructions end "Your answer is
  checked by code. You will be told what to fix if a check fails."
  `PROMPT_VERSION` is unchanged.
- Docstrings (`AC-034`): `extracting/prompts.py` and `extracting/text_layer.py`
  now say what is sent:
  - the page's repeated lines with their stored text, and its fillable form
    fields with their values;
  - in a retry message for a failed text check, the stored lines it is about;
  - nothing else of the page's stored text.

  `extracting/__init__.py`, `extracting/schemas.py` and `review.py` no longer
  call the verifier a model or say it reviews every page. A search of `src/`,
  `scripts/` and `pyproject.toml` finds no other such wording.

- `scripts/generate_reference_docs.py`:
  - A field that takes one literal or enum value is named by that value alone.
    `IssueName` now reads "`no_matching_label`" and "`verifier`", not "one of
    `verifier`".
  - The extraction checks page says every failing check is listed with the
    verifier off, and names "page extraction's verifier".
  - The survey checks page describes the survey's verifier, says when the
    differences from the facts are listed, and gains the `verifier` issue.
  - The cost page gains the cost estimate (`CostEstimate` and `steps[]`,
    `StepEstimate.verifier` included). The design expected the generator to pick
    up `StepEstimate.verifier` by itself, but no page described the estimate.
- The `verification` fields keep saying `None` when no verifier ran. That is how
  41 other fields on the JSON pages word it, since docstrings serve the Python
  and the JSON pages alike, so the earlier note to change only these two is
  dropped.
- `pyproject.toml`: the description says pydelity surveys a PDF and extracts its
  pages with Anthropic or OpenAI models, "with an optional verifier for each
  step" (`AC-030`'s package part). The README is Documenter's.
- Reference pages, regenerated and formatted. The diff covers `cost-jsonl.md`,
  `extraction-checks.md`, `page-json.md`, `pdf-survey-json.md`, `run-json.md`
  and `survey-checks.md`, and reads as above. With the earlier steps' pages
  (`configuration.md`, `cli.md`, `page-json.md`, `pdf-survey-json.md`,
  `cost-jsonl.md`), the reference covers:
  - the three settings and `--verify`/`-vf`;
  - `PdfSurvey.verification` and its parts;
  - the nullable `PageFile.verification`, `StepEstimate.verifier` and the
    required `LedgerEntry.agent`;
  - the survey's `verifier` issue (`AC-033`).
- Build: `uv build --offline` into a temporary folder made
  `pydelity-0.1.1-py3-none-any.whl` and `pydelity-0.1.1.tar.gz` from uv's cache,
  with nothing downloaded. uv ran outside the sandbox, which blocks writes to
  its cache. `.venv/bin/twine check --strict` passed both files; the wheel's
  `Summary` is the new description, and it holds no `tests/`. The version is
  0.1.1, since the release setup raises it (`AC-031`, not Developer's).
- `ruff check`, `ruff format --check scripts src tests` (89 files),
  `ty check scripts src tests` and `interrogate` clean; doctests 28 passed, 1
  skipped; the module order check finds no new departure.
- Tests: 205 passed, 2 failed, the same two rows recorded under DEV-010's
  rework, for Tester.
- Not run locally: `scripts/smoke_installed_wheel.py`. It installs the wheel's
  dependencies from PyPI into a fresh environment. On 2026-11-21 the user chose
  to leave it to CI, which runs it on Linux, macOS and Windows; Tester's full
  verification assesses that result (`AC-028`).

---

### DEV-012 — Page extraction keeps checks and hints apart

`Status`: `DONE` `Depends On`: `DEV-003, DEV-011` `Acceptance`:
`AC-043, AC-044, AC-046, AC-047, AC-048, AC-049`

**Goal**

Make page extraction's five comparisons with the PDF hints that never send an
answer or a correction back, record them in the page file apart from the six
checks, and list their differences under the design's review rule (decisions 3,
14 and 15).

**Affected Area**

`src/pydelity/review.py` (`ExtractionCheckName` to the six checks, new
`ExtractionHintName`, `IssueName`); `src/pydelity/extracting/validators.py`
(`CHECKS`, `HINTS`, `compare_with_hints`, hint results and their review issues,
`run_checks`, `retry_message`, the hint messages, module docstring);
`src/pydelity/extracting/schemas.py` (`ExtractionHintResult`, `PageFile.hints`,
the `issues`, `checks` and `PageVerification` docstrings);
`src/pydelity/extracting/agents.py` (docstrings);
`src/pydelity/extracting/llm.py` (`ModelPage`, `ModelVerdict`, `ask_verifier`);
`src/pydelity/extracting/prompts.py` (`verify_page`'s two sections only);
`src/pydelity/extracting/extraction.py` (`_extract_page`, `_KeptAnswer`,
`_kept_answer`, `_page_issues`); `scripts/generate_reference_docs.py` only as
far as it needs to keep running with `TEXT_CHECKS` gone; the regenerated
`page-json.md` and `run-json.md`.

**Expected Outcome**

- `CHECKS` holds `labels`, `content`, `languages`, `boxes`, `containers`,
  `captions`; `HINTS` holds `reading_order`, `artifacts`, `form_fields`,
  `text_dropped`, `text_added`, each returning its differences as
  `CheckFailure`s. `TEXT_CHECKS` and `_TEXT_NOTE` are gone. What each hint
  compares, its tolerances and the `comparison_status` gate stay as they are.
- `run_checks` runs `CHECKS` only, so both agents' output validators raise
  `ModelRetry` only for a check failure and the retry message lists check
  failures only. An answer or correction whose only differences are hints is
  accepted on that attempt. A final answer still failing a check is kept and
  written, as now.
- Hint messages describe the difference and never say what to change, in the
  sense of **Checks and hints** (for example, `text_dropped`: "the page's text
  layer has the line '…', which is not in the answer").
- `_kept_answer` keeps a correction that passes every check, whatever its hint
  differences.
- The verifier's user message gives, after the extraction,
  `Checks it still fails, which a correction must pass:` and
  `Differences from the hints, which the page image overrides:`, each with one
  line per failure or difference or `none`, compared on the extractor's answer.
  The rest of the prompt wording is DEV-014's.
- `PageFile.hints: list[ExtractionHintResult]` (required, `name` and
  `differences`) holds each hint's differences on the kept answer, in `HINTS`
  order, whatever the verdict. `checks` holds the six checks. A page file
  without `hints` fails validation and is made again with `damaged_output`.
  `PAGE_SCHEMA_VERSION` and `PROMPT_VERSION` stay as they are.
- `_page_issues` lists, in order: each check still failing on the kept answer;
  each hint difference, unless `verification` is set and the verdict passed or
  the correction was applied; `no_matching_label` issues; then `verifier` issues
  when the correction was not applied. A hint issue keeps the hint's name in
  `check`.
- Docstrings in the changed modules say a hint difference never sends an answer
  back.

**Self-Check**

Ruff check and format check, `ty check` and interrogate on `scripts src`; the
module order check. A scratchpad script, with the stand-in on a test PDF and
PydanticAI's `FunctionModel` inside `LedgerModel`, checks that:

- an answer differing from the page only in hints (a dropped text line, an
  uncovered furniture line, a wrong field value, an out-of-order item) is
  accepted on the first attempt with no retry, and its differences are in
  `hints` and on the review list with no verifier;
- an answer failing a check is sent back, the retry message names only check
  failures, and a last answer still failing is kept and listed;
- with the verifier on, its user message has both sections, a `text_dropped`
  line quoting its stored line; a correction differing only in hints is kept; a
  correction failing a check is not; hint issues are left off the list when the
  verdict passed or the correction was kept, and listed otherwise;
- an old page file without `hints` is extracted again with `damaged_output`.

Then `generate_reference_docs.py` and `format_markdown.mjs`, and the existing
tests and doctests, with each failure from a replaced contract listed.

**Evidence**

Evidence, 2026-11-22, repo root, on `5cb51ac` plus the uncommitted DEV-012
changes: `git diff HEAD -- src scripts examples docs pyproject.toml` has 456
insertions and 247 deletions over 13 files, SHA-256 starting `b3a1d7fad6a32d30`
(macOS arm64, Python 3.13.9, `.venv`). Changed: `src/pydelity/review.py`,
`extracting/validators.py`, `extracting/schemas.py`, `extracting/agents.py`,
`extracting/llm.py`, `extracting/prompts.py`, `extracting/extraction.py`,
`scripts/generate_reference_docs.py`, and the generated `extraction-checks.md`,
`page-json.md`, `pdf-survey-json.md`, `run-json.md` and `python-api.md`.

- Scratch module `dev012/check_hints.py` in the session scratchpad, run with
  `.venv/bin/python -m pytest -p tests.conftest -p tests.pydelity.extracting.conftest`
  against the stand-in on the tests' 3-page text PDF: 9 of 9 passed.
  - `CHECKS` and `HINTS` hold the design's six and five names in order.
  - No verifier, an answer that drops the page's last line and adds one: one
    extractor request, no retry; every check passes; `hints` holds one
    `text_dropped` difference quoting the stored line ("which is not in the
    answer") and one `text_added`; the review list is `text_dropped`,
    `text_added`, as in `run.json`'s `review` after a whole run; the page file's
    `hints` lists the five names; `verification` is null.
  - No verifier, an answer leaving the running header uncovered and putting the
    second line 380 units above the first: one extractor request; `artifacts`
    ("the survey found the repeated line R1 ...") and `reading_order` ("..., for
    the direction the survey found") differences, both listed.
  - A label not in the profile, together with a dropped line: three extractor
    requests; each retry message names `labels:` and no hint, and has no "keep
    what the image shows" note; the last answer is kept; issues are `labels`,
    then `text_dropped`.
  - Verifier on, extraction dropping a line, verdict passed: one extractor and
    one verifier request; the verifier's user message has
    `Checks it still fails, which a correction must pass:` with `none`, then
    `Differences from the hints, which the page image overrides:` with the
    `text_dropped` line quoting "Ask the office for a form."; `hints` keeps the
    difference; no review issue.
  - A correction differing from the hints only (an added line): kept on the
    first verifier request, `correction_applied` true, no correction failures,
    `hints` holds `text_added`, no review issue.
  - A correction with a label not in the profile: three verifier requests, each
    retry naming `labels:` and no hint; not kept; `correction_failures` is
    `labels` only; issues are `text_dropped`, then `verifier` naming the item's
    ID.
  - A page file with `hints` removed gives the warning "0000.json is not valid:
    hints: Field required; extracting page 1 (index 0) again" and a new
    extractor request.
  - `compare_with_hints` on a page with form fields and `column_order` set on a
    left-to-right page gives "the PDF stores the values ['Springfield'] for the
    form field 'city', but its field items say ['Shelbyville']", "the PDF stores
    the checked states [True] for the form field 'agree', but its field items
    say [False]" and "column_order is left_to_right, but the survey found the
    page written left to right"; no hint message says "must", "set it" or "Fix";
    `run_checks` on the same answer finds nothing.
- `ruff check` "All checks passed!"; `ruff format --check scripts src tests` "89
  files already formatted"; `ty check scripts src` "All checks passed!";
  `interrogate` 100.0%; doctests 28 passed, 1 skipped.
- Module order (scratch `dev012/order_check.py` on the seven changed modules):
  the only new departures are `CHECKS`, below `check_languages`, and `HINTS`,
  below `check_text_dropped`, the last functions each lists; the rest are the
  `extracting/schemas.py` departures listed under DEV-001.
- Reference pages: `generate_reference_docs.py`, then `format_markdown.mjs` with
  the hook's Prettier and Node 24.22.3. `extraction-checks.md` lists the six
  checks under "Checks" and the five hints under "Hints", after two paragraphs
  on the rule; `page-json.md` gains `hints` and `hints[]`, and the
  `correction_applied`, `issues` and `IssueName` texts change;
  `pdf-survey-json.md` and `run-json.md` change only in `IssueName`;
  `python-api.md` only in `PageFile`'s summary. The formatter's STANDARDS check
  passed.
- Tests: 195 passed, 12 failed. Each is a replaced contract, for Tester:
  - Retries on hint differences:
    `test_extraction.py::test_a_page_no_verifier_reviewed_keeps_its_extraction_and_lists_each_difference`
    (3 extractor requests expected, 1 made) and
    `test_the_verifier_s_verdict_decides_the_kept_answer_and_its_issues`
    (`passed`, `correction_kept`, `correction_rejected`: retries and the text
    note expected).
  - Old message wording: `test_validators.py`
    `test_artifacts_check_names_uncovered_furniture_and_skips_what_it_cannot_judge`,
    `test_form_fields_check_compares_fillable_fields_with_field_items` and
    `test_reading_order_check_allows_new_columns_but_not_jumps_back` (`ltr`,
    `rtl`, `ttb-left-to-right`, `ttb-right-to-left`).
  - `run_checks` holding the hints:
    `test_a_page_answered_as_one_full_page_figure_passes_every_check`.
  - The text note in retry messages:
    `test_text_checks_are_skipped_when_the_text_layer_cannot_be_compared`.
  - `ty check tests` reports 2 errors, `test_validators.py` lines 1161 and 1166,
    which pass text hint names to `retry_message`.
- Not run: the wheel smoke test and Python 3.14, as before.

**Implementation Notes**

- The hint functions keep their names (`check_reading_order`, `check_artifacts`,
  `check_form_fields`, `check_text_dropped`, `check_text_added`), since the
  design names only the `HINTS` table and `compare_with_hints`. Their docstrings
  start "Compare ..." or "Find ..." and say they are hints.
- `hint_results` and `hint_issues` sit beside `check_results` and
  `review_issues`; both issue builders share `_review_issue`.
- `extraction-checks.md`'s rule text and headings changed here rather than in
  DEV-015, because the page would otherwise describe the rule this step
  replaced. DEV-015 still does the survey's page and the remaining docstrings.
- The verifier prompt's `_VERDICT` paragraph still speaks of checks finding
  differences from stored text; DEV-014 rewrites it.

---

### DEV-013 — The survey keeps checks and hints apart

`Status`: `PENDING` `Depends On`: `DEV-006, DEV-012` `Acceptance`:
`AC-011, AC-043, AC-044, AC-049`

**Goal**

Record the survey's two comparisons with the facts as hints, apart from C1–C7,
and give them to its verifier as hints (decisions 14 and 15).

**Affected Area**

`src/pydelity/review.py` (`SurveyComparisonName` becomes `SurveyHintName`);
`src/pydelity/surveying/validators.py` (`HINTS`, `compare_with_hints` in place
of `compare_with_facts`, the two hints returning `CheckFailure`s, their review
issues, module docstring); `src/pydelity/surveying/schemas.py` (`HintResult`,
`PdfSurvey.hints`, the `issues` docstring); `src/pydelity/surveying/survey.py`
(`build_survey`); `src/pydelity/surveying/llm.py` (`ask_verifier`);
`src/pydelity/surveying/prompts.py` (`verify_survey`'s heading and input);
`scripts/generate_reference_docs.py` only as far as it needs to keep running;
the regenerated `pdf-survey-json.md` and `run-json.md`.

**Expected Outcome**

- `HINTS` is `rotation_differs`, then `page_number_differs`, each returning its
  differences as `CheckFailure`s with today's messages and details;
  `compare_with_hints` runs them. `compare_with_facts` and
  `SurveyComparisonName` are gone.
- `PdfSurvey.hints: list[HintResult]` (required) holds each hint's differences
  on the kept answer, whatever the verdict. A `pdf_survey.json` without `hints`
  fails validation and is surveyed again with `damaged_output`.
  `SURVEY_SCHEMA_VERSION` stays as it is.
- `issues` follow **Survey verdict application** step 4: checks still failing,
  then each hint difference unless the verdict passed or its correction was
  applied, then `verifier` issues. A hint issue keeps the hint's name in
  `check`, as `run.json` has it now.
- The verifier's user message gives the hint differences under
  `Differences from the measured facts, which are hints the PDF overrides:`.
  C1–C7, their retries and the keep rule are unchanged.

**Self-Check**

Ruff, ty, interrogate and the module order check; a scratchpad survey run
against the stand-in, with facts edited to give a `rotation_differs` and a
`page_number_differs`, for no verifier, passed, correction kept and correction
not kept, checking `hints`, the review list in `pdf_survey.json` and `run.json`,
the verifier's user message, and that no survey retry message carries a hint; an
old `pdf_survey.json` without `hints` surveyed again with `damaged_output`; the
reference pages regenerated; the existing tests with replaced-contract failures
listed.

---

### DEV-014 — Prompts present measured facts as hints

`Status`: `PENDING` `Depends On`: `DEV-012, DEV-013` `Acceptance`:
`AC-043, AC-045, AC-054`

**Goal**

Make page extraction's prompts, and the survey verifier's verdict rules, present
code's measurements and the survey's findings as hints the model's own reading
overrides (decision 16).

**Affected Area**

`src/pydelity/extracting/prompts.py` (`_page_text`, `_RULES`, `extract_page`,
`_VERDICT`); `src/pydelity/surveying/prompts.py` (`_VERDICT`).

**Expected Outcome**

- The page text gives the writing direction as what the survey found. The
  repeated lines, each with its stored text and what the survey found it to be,
  and the fillable form fields with their stored values come under headings that
  call them hints from the PDF's stored data and the survey, which the image
  overrides. The line about how the image was turned stays a plain statement.
- `_RULES` gains a short paragraph on hints. The page furniture rule no longer
  tells the model to put a furniture line in an item with role `artifact`; the
  forms rule says to set `fillable_name` when a field item is one of the fields
  given and to give the value or mark the image shows; the reading order rule
  follows the direction the page is written in, with the survey's direction as a
  hint.
- The extraction model's system message ends with "Your answer is checked by
  code for form and consistency, and you will be told what to fix if a check
  fails."
- Page extraction's `_VERDICT` second paragraph and the survey's `_VERDICT` say
  a correction must pass the checks and need not agree with the hints or facts.
- The extraction request still carries the page image, the repeated lines with
  their stored text and the form fields with their values, and no other stored
  text. No prompt asks the model to change an answer to match a hint.
  `PROMPT_VERSION` stays 1. `survey_pdf`'s messages are unchanged.

**Self-Check**

Ruff, ty and interrogate; a scratchpad script printing every system, user and
retry message of both steps for two test PDFs, compared with the messages before
the step, checking the headings, that `survey_pdf`'s messages are unchanged byte
for byte, that the extraction user message holds no stored text beyond the
repeated lines and field values, and that no message tells the model to match a
hint or to put a repeated line in an artifact item; the existing tests and
doctests.

---

### DEV-015 — Docstrings and the generated checks pages

`Status`: `PENDING` `Depends On`: `DEV-012, DEV-013, DEV-014` `Acceptance`:
`AC-033, AC-051, AC-052`

**Goal**

Make the docstrings and the generated checks pages describe the hint rule and
what page extraction sends.

**Affected Area**

`scripts/generate_reference_docs.py` (the `extraction-checks` and
`survey-checks` pages); docstrings still describing the old rule in
`src/pydelity/extracting/prompts.py`, `text_layer.py`, `validators.py`,
`agents.py`, `src/pydelity/surveying/validators.py` and
`src/pydelity/review.py`; the regenerated pages under
`docs/src/content/docs/reference/`.

**Expected Outcome**

- Each checks page lists the step's checks and hints under headings of their
  own, from `CHECKS` and `HINTS`, and says that a check may send an answer back
  within the check retries, a hint never does, when a hint difference goes on
  the review list, and that a kept answer still failing a check is kept and
  listed.
- No docstring says pydelity sends none of the PDF's stored text or that a text
  difference sends an answer back. They say page requests carry the repeated
  lines with their stored text and the survey's findings, and the form fields
  with their values, all as hints, and that with the verifier on its request
  lists the answer's hint differences, quoting stored lines.
- The reference pages, regenerated and formatted, cover `hints` in both output
  files and the new names.

**Self-Check**

`generate_reference_docs.py` and `format_markdown.mjs`, and a review of the
diff; a search of `src/`, `scripts/` and the reference pages for the old
wording; ruff, ty and interrogate; the full test and doctest run, with
replaced-contract failures listed.

---

## Verification Increments

### Increment 1

`Development Steps`: `DEV-001` `Acceptance`: `AC-041, AC-042`

**Ready Outcome**

`src/pydelity/` and `scripts/` follow **Module order**, with the departures
listed under DEV-001, and every check gives its baseline result with the tests
unchanged. Tester then reorders `tests/` (`AC-042`) and confirms both reorders
against `126f52f` before DEV-002 starts.

### Increment 2

`Development Steps`: `DEV-002, DEV-003` `Acceptance`:
`AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-018, AC-019, AC-020`

**Ready Outcome**

The settings and `--verify`/`-vf` resolve as the design says, and page
extraction runs with or without its verifier: page files, review list, ledger,
estimate figures, report and log line follow decisions 2–4 and 9 for pages. The
survey parts of `AC-001`, `AC-005` and `AC-006` are left for Increment 3.

### Increment 3

`Development Steps`: `DEV-004, DEV-005, DEV-006, DEV-007` `Acceptance`:
`AC-001, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017`

**Ready Outcome**

Every request names its agent, and the survey runs with or without its verifier:
request content, attachment reuse, check retries on corrections, the kept
answer, issues, `pdf_survey.json`, report, ledger lines, estimates, spend
control and the stop on a failed verifier request follow decisions 2–10 for the
survey. The stand-in needs routing for `The survey answer to review:`.

### Increment 4

`Development Steps`: `DEV-008, DEV-009, DEV-010` `Acceptance`:
`AC-021, AC-022, AC-023, AC-024, AC-025`

**Ready Outcome**

`load()`, report tables, outline links, inline widgets and the `TEXT_FLAGS`
comment behave as **Remaining fixes** says.

DEV-011 is the last step; after it the plan goes to full verification with no
separate increment.

---

## Plan Notes

- Project references loaded: `NONE` (`.standards/project-references/` does not
  exist).
- Order: DEV-008 to DEV-010 depend only on DEV-001 and may run before DEV-002 if
  the user prefers; the plan follows the design's build order.
- Names for the user's approval, all from the design: settings `verify`,
  `advanced.survey.verify`, `advanced.extraction.verify`; CLI `--verify`/`-vf`;
  properties `Config.verify_survey` and `Config.verify_extraction` (DEV-002);
  ledger agent `surveyor` (DEV-004); `SurveyProblem`, `SurveyVerdict`,
  `SurveyVerification`, `PdfSurvey.verification`, prompt `verify_survey`
  (DEV-005, DEV-006); `StepEstimate.verifier` (DEV-003);
  `TYPICAL_SURVEY_VERDICT_OUTPUT_TOKENS` (DEV-007). No new file or folder. The
  user approved the plan with these names on 2026-11-21.
- Tests are Tester's. Tests of a replaced contract fail until Tester updates
  them at the next checkpoint; each step lists them.
- Self-checks use `.venv/bin` tools directly, because uv cannot write its cache
  in the sandbox, and use the stand-in or PydanticAI test models. No real model
  run or download is planned; any would need the user's go-ahead.
- The user makes the commits. DEV-001 is meant to be committed on its own.

### Checkpoint: Increment 1

- Ready: DEV-001 is `DONE`; its self-check evidence and order departures are
  under DEV-001. Claim: `src/pydelity/` and `scripts/` follow **Module order**
  except the listed departures, with no change of text, name or behavior, and
  every check gives its `126f52f` result with `tests/` unchanged (`AC-041`).
- Assessed content: `126f52f` plus the uncommitted reorder of 16 files listed
  under DEV-001 (diff SHA-256 starting `0f21ce5c770d636c`). If the user commits
  it before Tester runs, the commit holds the same content.
- For Tester: reorder `tests/`, each `conftest.py` included (`AC-042`), list its
  departures in the verification report, and assess both reorders against
  `126f52f` under the design's technical acceptance criteria for `AC-041` and
  `AC-042`. The scratch tools above live only in this session's scratchpad and
  are not part of the deliverable.
- Limitations: Python 3.14 not run locally; the wheel smoke test and `uv`
  recipes not run (see DEV-001's evidence).
- Next after the return: DEV-002, then DEV-003 (Increment 2).

### Increment 1 return

Tester returned Increment 1 `VERIFIED` (verification report, **Increment
Assessments**, E1–E11, including CI on Python 3.14.4). Reconciled on `4a6bec7`:
`src/pydelity/`, `scripts/`, `docs/`, `examples/` and `pyproject.toml` are
unchanged since `0f4c949`; `tests/` changed only by Tester's reorder (`ac9e4cb`,
`7bd7f90`). Rerun on `4a6bec7`: tests 177 passed; `ruff check`,
`ruff format --check` (89 files) and `ty check` clean; `compare.py 126f52f` exit
0 with the listed departures only. `Current Increment` moves to 2.

### Checkpoint: Increment 2

- Ready: DEV-002 and DEV-003 are `DONE`, with their self-check evidence under
  each step. Claim: the settings `verify`, `advanced.survey.verify` and
  `advanced.extraction.verify` and the CLI option `--verify`/`-vf` resolve as
  the design's decision 1 says, and page extraction follows decisions 2–4 and 9
  for pages (`AC-001` to `AC-006` and `AC-018` to `AC-020` for page extraction).
- Not yet built: the survey's verifier, its estimate and its reuse rule
  (Increment 3), so the survey parts of `AC-001`, `AC-005` and `AC-006` are not
  claimed. With `verify` on, the survey still runs without a verifier.
- Assessed content: `4a6bec7` plus the uncommitted changes to the 15 files
  listed under DEV-002 and DEV-003
  (`git diff HEAD -- src scripts examples docs`, 263 insertions and 108
  deletions, SHA-256 starting `f710dcdbc349c854`). If the user commits it before
  Tester runs, the commits hold the same content.
- Tests of the replaced contract: 14 tests fail and `ty` reports 6 errors in
  `tests/pydelity/extracting/test_extraction.py`, all listed under DEV-003. They
  expect a verifier on every page by default.
- Limitations: the wheel smoke test (its `EXPECTED_REQUESTS` now has the upload
  and 3 model requests) and Python 3.14 were not run locally.
- Next after the return: DEV-004 to DEV-007 (Increment 3).

### Recovery frame 1 return

The frame's correction (the smoke script's check name) is done and verified
under DEV-003. Scoped return under **Implementation and Verification Recovery
Gates**: the plan stays `IN_PROGRESS` with `Current Increment: 2`, because
DEV-004 to DEV-011 are approved future work, not part of this correction. No
rerun is needed, so the frame is popped and Tester resumes its suspended
Increment 2 assessment (verification report, **Suspended Assignment 1**).

### Increment 2 return

Tester returned Increment 2 `VERIFIED` (verification report, E12–E21), with the
smoke script fix from recovery frame 1 (`45bfa10`). Reconciled on `50aca23`:
since `384204a`, `src/`, `scripts/`, `examples/`, `docs/` and `pyproject.toml`
changed only by that fix; the later commit changes only STANDARDS records. Rerun
on `50aca23`: tests 188 passed; `ruff check` and `ty check` clean.
`Current Increment` moves to 3.

### Checkpoint: Increment 3

- Ready: DEV-004 to DEV-007 are `DONE`, with their self-check evidence under
  each step. Claim: every request names its agent, and the survey runs with or
  without its verifier as decisions 2–10 say for the survey. That covers:
  - the request's content and the reuse of its attachment;
  - check retries on corrections and the kept answer;
  - the review list, `pdf_survey.json` and the report;
  - ledger lines, estimates and spend control;
  - the stop on a failed verifier request. This covers the survey parts of
    `AC-001`, `AC-005` and `AC-006`, and `AC-007` to `AC-017`.
- Assessed content: `50aca23..7804c97` (`dbc6aed` DEV-004, `e4d479f` DEV-005,
  `7804c97` DEV-006), plus the uncommitted DEV-007 changes to
  `src/pydelity/costs/budget.py`, `src/pydelity/pipeline/runner.py` and
  `docs/src/content/docs/reference/cost-jsonl.md`. Those are
  `git diff HEAD -- src scripts examples docs`: 122 insertions and 38 deletions,
  SHA-256 starting `11022516909a4f82`. If the user commits them before Tester
  runs, the commit holds the same content.
- Tests of the replaced contract: 12 tests fail, all listed under DEV-006.
  `ty check tests` reports one error, the `build_survey` call in
  `test_survey.py`. Ten of the failures pass the global `verify=True`, which now
  runs the survey's verifier too. They need the stand-in to route a request
  whose user message has the line `The survey answer to review:` to a queued
  survey verdict (the design's **Test seams**), or the per-step
  `advanced.extraction.verify`.
- The scratch checks drove the survey verifier through the stand-in by queuing
  verdicts after the survey answer, since survey requests are sequential. They
  live only in this session's scratchpad and are not part of the deliverable.
- Limitations: the wheel smoke test and Python 3.14 were not run locally; no
  real model ran.
- Next after the return: DEV-008 to DEV-010 (Increment 4).

### Increment 3 return

Tester returned Increment 3 `VERIFIED` (verification report, E22–E31; no open
defect), with its test updates in `83faebb`. Reconciled on `83faebb`:

- since `e9914c0` (DEV-007), `src/`, `scripts/`, `examples/`, `docs/` and
  `pyproject.toml` are unchanged;
- `787cecc` changes only STANDARDS records, and `83faebb` only `tests/`.

Rerun on `83faebb`: tests 200 passed; `ruff check`, `ruff format --check` (89
files), `ty check scripts src tests` and `check` clean. The report's **Scenario
Budget** has no allowance left for `pipeline/runner.py`, which DEV-008 changes.
`Current Increment` moves to 4.

### Checkpoint: Increment 4

- Ready: DEV-008 to DEV-010 are `DONE`, with their self-check evidence under
  each step. Claim: `load()`, report tables, outline links, inline widgets and
  the `TEXT_FLAGS` comment behave as **Remaining fixes** says (`AC-021` to
  `AC-025`).
- Assessed content: `83faebb..c7d8ac7` (`a307946` DEV-008, `c7d8ac7` DEV-009),
  plus the uncommitted DEV-010 changes to `src/pydelity/surveying/probe.py` and
  `src/pydelity/utils/pdf.py`. Those are
  `git diff HEAD -- src scripts examples docs`: 30 insertions and 7 deletions,
  SHA-256 starting `0af92bee3665119a`. If the user commits them before Tester
  runs, the commit holds the same content.
- Tests of the replaced contract: none; all 200 tests pass.
- The report's **Scenario Budget** has no allowance left for
  `pipeline/runner.py`, which DEV-008 changes, so `AC-021`'s scenario may need
  the user's decision.
- The scratch PDFs and scripts live only in this session's scratchpad and are
  not part of the deliverable. The design asks for a PDF with a dangling link
  and one with an inline widget; `dev010/make_pdfs.py` shows how they were built
  with PyMuPDF.
- Limitations: the wheel smoke test and Python 3.14 were not run locally.
- Next after the return: DEV-011, then full completion and full verification.

### Increment 4 return

Tester returned Increment 4 `VERIFIED` (verification report, E32–E38; no open
defect), with its tests in `5ec4eec`. Reconciled on `5ec4eec`: since `5bddc38`
(DEV-010), `src/`, `scripts/`, `examples/`, `docs/` and `pyproject.toml` are
unchanged; `5ec4eec` changes only `tests/` and STANDARDS records. Rerun on
`5ec4eec`: tests 207 passed; `ruff check`, `ruff format --check` (89 files),
`ty check scripts src tests` and `check` clean.

DEV-011 belongs to no increment. `Current Increment` stays 4 until full
completion sets it to `NONE` and hands the plan to full verification.

Found while planning DEV-011: the extraction model's instructions
(`extract_page` in `extracting/prompts.py`) say "Your answer is checked by code
and reviewed by a second model". Since decision 1 the verifier is off by
default, so the sentence is untrue on a default run. No design decision or plan
step covers this prompt text. Changing it is a plan revision for the user's
approval.

### Plan revision 1

The user approved two changes on 2026-11-21:

- DEV-011 also corrects the extraction model's instructions. It drops "and
  reviewed by a second model", so the sentence is true with the verifier on or
  off; `PROMPT_VERSION` stays 1, as the scope says. No design decision covers
  that sentence, so this is a change to the plan only, now approved.
- The probe sets an outline `First` or `Next` link to an object the PDF does not
  have to null, rather than leaving it, so `get_toc` reads every remaining
  bookmark with no blank placeholder entry. This changes the design's
  **Remaining fixes** outline rule ("the walk carries on with the links left, so
  PyMuPDF's `get_toc` reads the outline as it did before"). So it is routed to
  Architect as `USER_REWORK` (`ARCHITECTURE`), not absorbed into this plan.
  `AC-023`'s "yields the bookmarks that can be read … instead of none" still
  holds; Architect decides whether the scope needs Scoper. When the design is
  corrected, DEV-010 reopens for it: its outcome changes, and DEV-010 is the
  probe step.

### Suspended Assignment 1

`Recovery Frame`: `1` `Recovery Reason`:
`The user asked that the probe set an outline link to a missing object to null, so get_toc reads every remaining bookmark with no blank entry; the design's outline rule leaves such a link in place.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`5ec4eec (Increment 4 verified; DEV-001 to DEV-010 DONE; DEV-011 PENDING with plan revision 1)`
`Next Action`:
`Reconcile the corrected outline rule: reopen DEV-010 to set dangling outline links to null, then implement DEV-011 with plan revision 1, then full completion and full verification.`

### Outline rework return

Architect corrected the design in `81d7dcd`. **Remaining fixes** now sets an
outline `First` or `Next` link to a missing object to null, and `AC-023`'s
technical criterion asks for every bookmark reachable without that link, with no
blank entry and no probe error. Architect found no rerun needed, popped recovery
frame 1, and resumed development (`RESUME`).

Reconciled on `81d7dcd`:

- since `5ec4eec`, only `.standards/STATE.md` and the design changed;
- the corrected rule is the change the user approved in plan revision 1.

Suspended Assignment 1 is restored. DEV-010 reopens with the corrected outcome,
then DEV-011 follows with plan revision 1. The DEV-010 evidence above describes
the first version, which left such links in place.

### Full completion

- Ready: DEV-001 to DEV-011 are `DONE`, with their self-check evidence under
  each step. The plan is `COMPLETE`, `Current Increment` is `NONE`, and the user
  style `tony` stays locked. Plan revision 1 is approved and built:
  - the extraction prompt sentence, in DEV-011;
  - dangling outline links set to null, in DEV-010's rework, after Architect's
    `81d7dcd`.
- Assessed content: `126f52f..7311f93`, plus the uncommitted DEV-011 changes to
  `src/`, `scripts/`, `docs/` and `pyproject.toml`. Those are
  `git diff HEAD -- src scripts examples docs pyproject.toml`: 163 insertions
  and 57 deletions over 13 files, SHA-256 starting `b00a83ede04aedb0`. If the
  user commits them before Tester runs, the commit holds the same content.
- Tests of the replaced contract: the two rows (`first`, `next`) of
  `test_probe.py::test_outline_links_to_missing_objects_keep_the_bookmarks_pymupdf_reads`
  expect the blank bookmark entry that the corrected outline rule removes. All
  205 other tests pass.
- Since Increment 4, the probe's outline walk and the extraction prompt changed.
  `AC-023`'s Increment 4 evidence no longer applies, and `AC-028` (the wheel
  smoke test) and Python 3.14 rest on CI.
- Not Developer's: the README and the docs guides and FAQ (`AC-030`'s README
  part, `AC-032`, `AC-034`'s FAQ part, `AC-035` to `AC-038`, Documenter); the
  0.2.0 release setup (`AC-031`); the user's real runs (`AC-039`, `AC-040`). The
  README still says "A second model reviews every page".
- Next: Tester's full verification (`Assessment Purpose` `FULL`).

### Plan revision 2: hints rerun

During synchronization the user changed the request: code's measurements of the
PDF become hints that never send an answer back, in every step that calls a
model. Scoper (`01598d8`) and Architect (`5cb51ac`) corrected the scope and
design under recovery frame 1 (owner `SCOPING`, `RerunThrough`
`REVIEWING_FINAL`, `ResumeAt` `SYNCHRONIZING`). Developer runs as a downstream
rerun. Reconciled on `5cb51ac`:

- Since the full completion above, the code changed by DEV-011's commit
  (`b579737`) and by Documenter's docstring corrections in `c0ed1e9`
  (`extracting/schemas.py`, `pipeline/schemas.py`, `review.py`); after them only
  `tests/`, STANDARDS records, the scope and the design changed.
- New outcomes, in the design's build step 7: DEV-012 (page extraction's checks
  and hints), DEV-013 (the survey's), DEV-014 (prompt text) and DEV-015
  (docstrings and the generated checks pages). They change what DEV-003,
  DEV-005, DEV-006 and DEV-011 built in places (the page review list, the
  verifiers' user messages, the extraction prompt's closing sentence); those
  steps stay `DONE` as the record of what they built, and the new steps carry
  the changed outcomes.
- Retired identifiers: `AC-019` is dropped from DEV-003 (replaced by `AC-048`,
  DEV-012) and `AC-034` from DEV-011 (replaced by `AC-051`, DEV-015).
- No new increment: during recovery the work goes to Tester as a full
  verification after DEV-015, with no checkpoint.
- Names from the design: `HINTS`, `compare_with_hints`, `ExtractionHintName`,
  `SurveyHintName`, `ExtractionHintResult`, `HintResult`, `PageFile.hints`,
  `PdfSurvey.hints`. Developer names only private helpers.
- Expected order departures: each `HINTS` sits below the hint functions it
  lists, as `CHECKS` does.
- What stops working, as the design says: page files and `pdf_survey.json`
  written before this change lack `hints` and are made again with
  `damaged_output`. No compatibility is kept.

The four steps are a material addition, so the plan returned to `PROPOSED`. The
user approved plan revision 2 on 2026-11-22. The user style `tony` stays locked.

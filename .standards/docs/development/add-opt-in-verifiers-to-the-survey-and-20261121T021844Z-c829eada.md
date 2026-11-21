<!-- STANDARDS
Artifact: DEVELOPMENT
Cycle: add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada
-->

# Development Plan

`Cycle`: `add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada`
`Mode`: `STEPWISE` `User Style`: `tony` `User Style Locked`: `true` `Status`:
`IN_PROGRESS` `Verification Cadence`: `INCREMENTAL` `Current Increment`: `4`

## Implementation Contract

- `Scope`:
  `.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
- `Architecture`:
  `.standards/docs/specs/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
- `Request`:
  `Reorder every module first; then make each step's verifier opt-in (one global switch plus a per-step override, off by default), give the survey a verifier like page extraction's, make page extraction's verifier optional with every difference listed when none ran, fix page extraction's remaining defects, and ready 0.2.0's docstrings, reference pages and package description.`

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
`AC-001, AC-005, AC-006, AC-018, AC-019, AC-020`

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

`Status`: `PENDING` `Depends On`: `DEV-001` `Acceptance`:
`AC-023, AC-024, AC-025`

**Goal**

Keep the readable bookmarks and form fields of PDFs with a dangling outline link
or an inline widget, and correct the `TEXT_FLAGS` comment.

**Affected Area**

`src/pydelity/surveying/probe.py` (`_cut_outline_cycle`, `_form`,
`_field_error`), `src/pydelity/utils/pdf.py` (comment only).

**Expected Outcome**

- An outline `First` or `Next` link to an object number outside
  `1..xref_length() - 1` is not followed, and `get_toc` reads the outline as
  before the cycle cut existed. Which PyMuPDF calls raise on such a number is
  confirmed first.
- An annotation with object number 0 is skipped with one `form` probe error
  naming its page, without reading keys of object 0, and the other fields are
  kept; `_field_error` never reads keys of object 0.
- The `TEXT_FLAGS` comment says text is clipped to the page's CropBox.
- `PROBE_VERSION` is not raised.

**Self-Check**

Ruff, ty and interrogate; scratchpad PDFs built with PyMuPDF (not added to the
repo) with a dangling `Next` link and with an inline widget, probed before and
after the fix; the existing tests.

---

### DEV-011 — Docstrings, reference pages and the package description

`Status`: `PENDING` `Depends On`:
`DEV-003, DEV-006, DEV-007, DEV-008, DEV-009, DEV-010` `Acceptance`:
`AC-028, AC-030, AC-033, AC-034`

**Goal**

Make the code's docstrings, the generated reference pages and the package text
describe 0.2.0 as built.

**Affected Area**

`src/pydelity/extracting/prompts.py`, `src/pydelity/extracting/text_layer.py`
(docstrings), `scripts/generate_reference_docs.py` (the hand-written check
texts: the survey checks page gains `verifier`, and the extraction checks page's
wording no longer calls the verifier a model or says it reviews every page; the
generated type text says "one of" for a list of one name, such as `verifier`,
and the `verification` fields say `None` where a JSON page means `null`), any
other docstring or comment that still calls the verifier a model (such as in
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
- The wheel smoke test runs the survey and page extraction with default settings
  from the built wheel.

**Self-Check**

`.venv/bin/python scripts/generate_reference_docs.py` and a review of the diff;
ruff, ty and interrogate; `uv build` and `twine check --strict` (or the
`.venv/bin` equivalents where uv cannot write its cache);
`python scripts/smoke_installed_wheel.py`; the full test and doctest run.

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

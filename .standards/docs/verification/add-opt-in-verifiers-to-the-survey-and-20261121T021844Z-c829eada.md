<!-- STANDARDS
Artifact: VERIFICATION
Cycle: add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada
-->

# Verification Report

`Cycle`: `add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada`
`Mode`: `REVERIFY` `Status`: `IN_PROGRESS` `User Style`: `tony`
`Assessment Purpose`: `INCREMENT` `Assessment Target`: `Increment 2`

## Assessed Inputs

- Scope
  `.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
  (last changed in `49448e5`, SHA-256 `dd6ea5291602d518…`), design
  `.standards/docs/specs/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
  (`126f52f`, `846800debae3d32f…`; decisions 1–4 and 9, **Settings**, **Example
  config files**, **CLI**, **Page extraction without a verifier**, **Page
  file**, **Cost estimate**, **HTML report**, and the technical criteria of
  `AC-001` to `AC-006` and `AC-018` to `AC-020`), development plan
  `.standards/docs/development/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
  (`45bfa10`; `DEV-002`, `DEV-003` with its correction for recovery frame 1,
  **Checkpoint: Increment 2**, **Recovery frame 1 return**),
  `.standards/CONTEXT.md` (`0573e11`, `09045f457b2df4c1…`), user style
  `.standards/user-styles/tester/tony.md` (`797def3`, `e64ef290173c7c32…`).
  Scope, design, context and style are unchanged since Increment 1. The
  assessment began as `VERIFY`; after Developer's correction for recovery frame
  1 it resumed as `REVERIFY`, reconciling the evidence the changed script
  touches (E20, E21). Current acceptance set: `AC-001` to `AC-042`, none
  retired.
- Assignment: Increment 2 (`DEV-002`, `DEV-003`; `AC-001` to `AC-006`, `AC-018`
  to `AC-020`) from the plan's **Verification Increments** and **Checkpoint:
  Increment 2**: the settings `verify`, `advanced.survey.verify`,
  `advanced.extraction.verify` and `--verify`/`-vf` resolve as decision 1 says,
  and page extraction runs with or without its verifier as decisions 2–4 and 9
  say. The survey parts of `AC-001`, `AC-005` and `AC-006` are Increment 3's.
- Source assessed: `45bfa10`. The user committed the checkpoint's changes to 15
  files under `src/`, `scripts/`, `examples/` and `docs/` in `384204a`
  (`git diff 4a6bec7 384204a -- src scripts examples docs`, 263 insertions, 108
  deletions, SHA-256 `f710dcdbc349c854…`, the content the plan's checkpoint
  claims and E12–E19 assess). `45bfa10` adds Developer's correction, which
  changes only `scripts/smoke_installed_wheel.py`
  (`git diff 384204a 45bfa10 -- src scripts examples docs tests`, 2 insertions,
  1 deletion, SHA-256 `e1141021307f15d3…`).
- Tests assessed: this assessment's changes to 7 test modules, committed in
  `384204a` (`git diff 4a6bec7 384204a -- tests`, 394 insertions, 87 deletions,
  SHA-256 `e3a5c176d5dd1e4b…`) and unchanged in `45bfa10`. Increment 1's tests
  reorder is in `4a6bec7`.
- Environment: macOS 26.6.2 arm64, Python 3.13.9 (`.venv`, strict editable
  install), PyMuPDF 2.1, Pydantic 2.14.3, pytest 9.2.0 with pytest-randomly and
  pytest-xdist, ruff 0.17.5, ty 0.0.105, interrogate 1.7.0, Prettier 3.10.1 with
  Node 24.22.3 from `~/.cache/prek`. Python 3.14 is not installed locally; CI
  runs it.
- Session: the same Tester chat as Increment 1, with no Developer conversation
  in it. The client cannot certify session freshness; this assessment is built
  from the persisted records and the repository.
- Project references loaded: `NONE` (`.standards/project-references/tester/`
  does not exist). Shipped reference loaded:
  `.claude/skills/tester/references/llm-api-testing.md` (the change calls
  provider APIs; the stand-in in `tests/fixtures/mock_providers.py` is the
  seam).

## Acceptance Evidence

| AC / technical criterion                                                                                                                                                                                                                         | Tests or checks                                                                                                                                                                                                                                                                                                                                   | Disposition and evidence                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AC-001` / no setting: both properties false, no verifier request, no `verifier` ledger line (page extraction)                                                                                                                                   | `test_loading.py::test_each_step_s_verifier_follows_verify_unless_its_own_setting_is_set[default]`; `test_extraction.py::test_a_page_no_verifier_reviewed_keeps_its_extraction_and_lists_each_difference`; `test_cli.py::test_a_pdf_alone_runs_the_survey_with_keys_from_the_environment`                                                         | Verified for page extraction: both properties false; default runs send extractor requests only and the ledger has no `verifier` line. E13–E15. The survey part is `AWAITING_IMPLEMENTATION` (Increment 3, `DEV-004`–`DEV-006`).                                                                                                               |
| `AC-002` / `verify: true` in JSON or YAML, `--verify`/`-vf`, `verify=True` make both properties true                                                                                                                                             | `test_loading.py::test_verify_turns_on_both_steps_verifiers_from_a_file_or_a_keyword`; `test_cli.py::test_verify_adds_a_verifier_request_for_each_page_and_to_the_estimate[--verify]`, `[-vf]`                                                                                                                                                    | Verified: JSON file, YAML file and keyword give both properties true; both CLI forms turn page extraction's verifier on end to end. E13–E15. The survey reading `verify_survey` is `DEV-006`'s (Increment 3).                                                                                                                                 |
| `AC-003` / an override sets its step either way, the other follows `verify`, `null` follows; file and nested keyword                                                                                                                             | `test_loading.py::test_each_step_s_verifier_follows_verify_unless_its_own_setting_is_set` rows `survey-on-in-file`, `both-off-file-and-keyword`, `extraction-on`; `test_extraction.py::test_turning_the_verifier_on_extracts_again_only_pages_it_has_not_reviewed`                                                                                | Verified: each step's override on while `verify` is off and off while it is on, in a file and by a nested keyword that keeps the file's other `advanced` settings. E13–E15.                                                                                                                                                                   |
| `AC-004` / both example files hold the three settings at their defaults and load                                                                                                                                                                 | `test_loading.py::test_example_config_holds_every_setting_at_its_default[config.json]`, `[config.yaml]` (reused); inspection of both files                                                                                                                                                                                                        | Verified: both pass (key sets equal the models' fields, values equal the defaults, no `ConfigError`); the YAML comments say what each setting does, that `null` follows `verify` and that a verifier adds cost. E14, E19.                                                                                                                     |
| `AC-005` / a step's `verifier` and its figures include the verifier exactly when it runs: CLI estimate, plan-time check, `estimate()`, `aestimate()` (page extraction)                                                                           | `test_budget.py::test_the_estimate_covers_page_extraction_and_its_verifier_only_when_it_runs`, `::test_the_check_before_spending_counts_the_verifier_only_when_it_runs`, `::test_estimate_writes_nothing_and_a_reusable_survey_costs_nothing`; `test_api.py::test_async_estimate_gives_what_estimate_gives_and_raises_alike`; the CLI tests above | Verified for page extraction: `requests_max` 6 and 12 for 2 pages, 3 and 6 for 1, `verifier` false and true, higher expected and maximum cost with the verifier; the plan-time projection equals each estimate; reused steps say `false`; the CLI line names the verifier. E13–E15. The survey part is `AWAITING_IMPLEMENTATION` (`DEV-007`). |
| `AC-006` / a page file with `verification: null` is not reused while the verifier is on, one with a verification is reused while it is off, no fingerprint includes the switch, changing only `advanced.extraction.verify` never runs the survey | `test_extraction.py::test_turning_the_verifier_on_extracts_again_only_pages_it_has_not_reviewed`; `::test_page_files_rerun_only_when_their_inputs_change`; `test_runner.py::test_a_rerun_with_unchanged_inputs_reuses_everything`                                                                                                                 | Verified for page extraction: turning it on reruns both pages with a log line each and no survey request; off reuses the reviewed files; on again sends nothing; fingerprints equal; unverified files are reused while off. E13–E15. The survey part is `AWAITING_IMPLEMENTATION` (`DEV-006`).                                                |
| `AC-018` / with `verify_extraction` off, extractor requests only, the extractor's answer kept                                                                                                                                                    | `test_extraction.py::test_a_page_no_verifier_reviewed_keeps_its_extraction_and_lists_each_difference`; the default-run tests in `test_extraction.py`, `test_runner.py`, `test_cli.py`, `test_html.py`                                                                                                                                             | Verified: 3 extractor attempts with their retries, the last answer kept, no verifier request (the stand-in has no verifier answer, so one would fail the run). E13–E15.                                                                                                                                                                       |
| `AC-019` / no verifier: every failing check, `text_dropped` and `text_added` included, is a review issue; with a verifier the rules are unchanged                                                                                                | Same no-verifier test; `test_extraction.py::test_the_verifier_s_verdict_decides_the_kept_answer_and_its_issues[passed]`, `[correction_kept]`, `[correction_rejected]` with the verifier on                                                                                                                                                        | Verified: both text checks are issues quoting the dropped and the added line; with the verifier on, the three verdict outcomes list what they listed before. E13–E15.                                                                                                                                                                         |
| `AC-020` / `verification` null exactly when no verifier ran; the report and the log line then say so                                                                                                                                             | Same no-verifier test (page file, log line); `test_html.py::test_a_page_no_verifier_reviewed_says_so_in_the_report`; `::test_report_draws_extracted_items_numbered_with_links_from_their_issues` with the verifier on                                                                                                                             | Verified: `"verification": null` in the file, `no verifier;` in the page's log line, `Verifier` / `no verifier ran` on both pages' cards; with the verifier on, the file holds the verdict and the card its outcome. E13–E15.                                                                                                                 |
| `AC-041` / move only, **Module order** with the listed departures, checks as before (Python 3.13 and 3.14)                                                                                                                                       | Increment 1 evidence; `ordercheck.py order` on the 17 modules this increment changed                                                                                                                                                                                                                                                              | Verified (Increment 1, E1–E7, E10–E11). The changed modules still follow **Module order** with only the listed departures. E18.                                                                                                                                                                                                               |
| `AC-042` / the same for `tests/`                                                                                                                                                                                                                 | Increment 1 evidence; `ordercheck.py order` on the 7 test modules changed here                                                                                                                                                                                                                                                                    | Verified (Increment 1, E8–E11). New tests sit in their alphabetical places; no new departure. E18.                                                                                                                                                                                                                                            |
| `AC-007`, `AC-008`, `AC-009`, `AC-010`, `AC-011`, `AC-012`, `AC-013`, `AC-014`, `AC-015`, `AC-016`, `AC-017`, `AC-021`, `AC-022`, `AC-023`, `AC-024`, `AC-025`, `AC-028`, `AC-030`, `AC-033`, `AC-034`                                           | Increments 3–4 and `DEV-011`                                                                                                                                                                                                                                                                                                                      | `AWAITING_IMPLEMENTATION`: `DEV-004`–`DEV-011` are `PENDING`.                                                                                                                                                                                                                                                                                 |
| `AC-026`, `AC-027`, `AC-029`, `AC-031`                                                                                                                                                                                                           | Tests written at each increment; CI, build and release checks at full verification                                                                                                                                                                                                                                                                | `AWAITING_IMPLEMENTATION`: the tests for items 2 and 4 cover page extraction so far (above); the survey's verifier and the fixes come with `DEV-004`–`DEV-011`.                                                                                                                                                                               |
| `AC-032`, `AC-035`, `AC-036`, `AC-037`, `AC-038`                                                                                                                                                                                                 | Documentation evidence                                                                                                                                                                                                                                                                                                                            | Pending a later role: Documenter, with documentation-record evidence for each AC.                                                                                                                                                                                                                                                             |
| `AC-039`, `AC-040`                                                                                                                                                                                                                               | The user's review of real runs                                                                                                                                                                                                                                                                                                                    | Pending a later role: the user's accepted real runs on Anthropic and OpenAI, after the build.                                                                                                                                                                                                                                                 |

### Test module order departures

Each keeps an order that Python 3.13 needs to import the module.

- `tests/fixtures/mock_providers.py`: `_ROUTES` stays below the public type
  aliases `Provider` and `Route`, which its annotation
  `dict[str, tuple[Provider, Route]]` reads; `RecordedRequest` stays above
  `MockProviders`, whose `requests` property's return annotation names it.
- `tests/pydelity/config/test_loading.py`: `_EXAMPLES` stays below `_REPO_ROOT`,
  which its value reads.

A constant moves below the definition it reads, and a class or function moves
above the definition that reads it, as in the package's departures.

## Increment Assessments

| Increment | Outcome and acceptance scope                                                                                                                             | Assessed inputs / evidence                                                                          | Disposition |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ----------- |
| 1         | `src/pydelity/`, `scripts/` and `tests/` follow **Module order** with the listed departures (`AC-041`, `AC-042`)                                         | `0f4c949`; tests diff `60f9212d56eab4d4…` (committed in `ac9e4cb`); E1–E9 on 3.13, E10–E11 on 3.14  | VERIFIED    |
| 2         | Verifier settings and `--verify`/`-vf`; page extraction with or without its verifier (`AC-001` to `AC-006` and `AC-018` to `AC-020` for page extraction) | `384204a` (source `f710dcdbc349c854…`, tests `e3a5c176d5dd1e4b…`) and the fix in `45bfa10`; E12–E21 | VERIFIED    |

## Scenario Budget

| Source file                                                                                 | Reused coverage                                                                                                                                                                                                                                                                                                                                  | Active-change allocations                                                                                                                                                                                                                                                                                                                             | User additions |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| The 16 reordered modules of `src/pydelity/` and `scripts/` (Increment 1)                    | The existing suite as regression checks                                                                                                                                                                                                                                                                                                          | 0                                                                                                                                                                                                                                                                                                                                                     | NONE           |
| `src/pydelity/config/schemas.py`                                                            | Example-file completeness test (2 rows)                                                                                                                                                                                                                                                                                                          | 5 of 5: the 4 rows of `test_each_step_s_verifier_follows_verify_unless_its_own_setting_is_set`; `test_verify_turns_on_both_steps_verifiers_from_a_file_or_a_keyword`                                                                                                                                                                                  | NONE           |
| `src/pydelity/cli.py`                                                                       | `test_pages_and_no_pause_extract_only_those_pages_in_one_run` (updated to the default)                                                                                                                                                                                                                                                           | 3: `test_verify_adds_a_verifier_request_for_each_page_and_to_the_estimate` (2 rows); `test_a_pdf_alone_runs_the_survey_with_keys_from_the_environment` (expanded: no verifier request or ledger line, estimate count)                                                                                                                                 | NONE           |
| `src/pydelity/pipeline/runner.py`                                                           | `test_a_rerun_with_unchanged_inputs_reuses_everything` (updated); `test_run_json_records_each_step_its_pages_cost_and_review_issues` (verifier on)                                                                                                                                                                                               | 4: the 3 CLI scenarios above (estimate lines, the switch reaching page extraction); `test_the_check_before_spending_counts_the_verifier_only_when_it_runs`                                                                                                                                                                                            | NONE           |
| `src/pydelity/costs/budget.py`                                                              | —                                                                                                                                                                                                                                                                                                                                                | 5 of 5: `test_the_estimate_covers_page_extraction_and_its_verifier_only_when_it_runs` (verifier off, verifier on); `test_the_check_before_spending_counts_the_verifier_only_when_it_runs`; `test_async_estimate_gives_what_estimate_gives_and_raises_alike` (expanded); `test_estimate_writes_nothing_and_a_reusable_survey_costs_nothing` (expanded) | NONE           |
| `src/pydelity/costs/schemas.py`                                                             | —                                                                                                                                                                                                                                                                                                                                                | 3: the estimate test's two partitions; the reused-step expansion                                                                                                                                                                                                                                                                                      | NONE           |
| `src/pydelity/extracting/extraction.py`                                                     | The 3 verdict rows and both provider rows of the request test (verifier on); `test_page_files_rerun_only_when_their_inputs_change`, `test_a_failed_page_stops_the_run_and_the_next_run_extracts_only_what_is_missing`, `test_a_page_file_naming_a_missing_crop_is_extracted_again` (updated); 4 tests whose unused verifier answers were removed | 3: `test_a_page_no_verifier_reviewed_keeps_its_extraction_and_lists_each_difference`; `test_turning_the_verifier_on_extracts_again_only_pages_it_has_not_reviewed` (turning on redoes unreviewed pages; turning off keeps reviewed ones)                                                                                                              | NONE           |
| `src/pydelity/extracting/schemas.py`                                                        | As for `extraction.py`                                                                                                                                                                                                                                                                                                                           | 2: the same no-verifier test (`verification: null` written); the reuse test (read back and reused)                                                                                                                                                                                                                                                    | NONE           |
| `src/pydelity/extracting/llm.py`                                                            | As for `extraction.py`                                                                                                                                                                                                                                                                                                                           | 2: the no-verifier test; the reuse test's turned-on run                                                                                                                                                                                                                                                                                               | NONE           |
| `src/pydelity/report/html.py`                                                               | `test_report_draws_extracted_items_numbered_with_links_from_their_issues` (verifier on)                                                                                                                                                                                                                                                          | 1: `test_a_page_no_verifier_reviewed_says_so_in_the_report`                                                                                                                                                                                                                                                                                           | NONE           |
| `scripts/smoke_installed_wheel.py`, `examples/config.json`, `examples/config.yaml`, `docs/` | Example-file completeness test; smoke replays and page regeneration in the scratchpad (E16, E17, E21)                                                                                                                                                                                                                                            | 0                                                                                                                                                                                                                                                                                                                                                     | NONE           |

A test updated only to the new default, or run with the verifier on to keep its
existing scenario, uses that scenario's existing allocation. An update that
asserts new behavior counts as an allocation. `config/schemas.py` and
`costs/budget.py` are at the ceiling of five; their survey parts in Increment 3
(`DEV-006`, `DEV-007`) need new allowance only if they add scenarios charged to
these files. The suite has 188 test IDs: the 177 of Increment 1, less the
replaced extraction estimate test, plus 12 new.

## Execution Evidence

Working directory: repo root unless noted. Tools: `.venv/bin`. Scratch tools and
logs live in this session's scratchpad (`tools/`, `logs/`), not in the repo.
2026-11-21.

- **E1–E11 — Increment 1.** As recorded for Increment 1: the baseline on
  `126f52f` (E1); move-only comparison of the package, scripts and tests (E2,
  E3, E8); **Module order** and departures (E4, E5, E8); checks on `0f4c949` and
  after the tests reorder (E6, E9); reference pages (E7); CI run `44907613193`
  on pull request 11 with Python 3.14.4 and every other check passing (E10);
  static checks targeting 3.14 (E11). They assess `0f4c949` and `7bd7f90` and
  stay valid for `AC-041` and `AC-042`; the source changes since then add
  behavior and are assessed below.
- **E12 — The checkpoint as handed over.** `git diff --cached` SHA-256
  `f710dcdbc349c854…`, equal to the plan's claim. With the tests unchanged:
  `pytest -q --numprocesses auto -p no:cacheprovider` 14 failed, 163 passed, the
  14 tests the plan lists under `DEV-003`; `ty check scripts src tests` 6
  diagnostics, all in `tests/pydelity/extracting/test_extraction.py`. Each
  failure expected a verifier on every page by default.
- **E13 — Tests changed.** In `test_extraction.py`: the default-run tests expect
  extractor requests only and queue no verifier answer, so a verifier request
  would fail the run; the request test and the verdict test run with
  `verify=True`; two new tests (no verifier; turning the verifier on and off).
  In `test_runner.py`: the rerun test expects 3 model requests; the `run.json`
  test runs with the verifier on. In `test_html.py`: the item test runs with the
  verifier on; one new test for `no verifier ran`. In `test_budget.py`: the
  extraction estimate test replaced by one covering the verifier off and on; one
  new plan-time test; the reuse test runs with the verifier on and checks
  `verifier: false` on reused steps. In `test_api.py`: `aestimate` compared with
  `estimate` with the verifier on. In `test_cli.py`: the two default runs expect
  no verifier request (summary cost `$0.10`, extraction `$0.07`, which the
  ledger's three extractor lines of `$0.024` give); one new test with two rows
  for `--verify` and `-vf`. In `test_loading.py`: two new tests, one with four
  rows.
- **E14 — Suite and linters on the assessed content.**
  `pytest -q --numprocesses auto -p no:cacheprovider` exit 0, 188 passed, 65
  warnings; `pytest -q -p no:cacheprovider -p no:randomly` exit 0, 188 passed
  (`logs/inc2_pytest_parallel.log`, `logs/inc2_pytest_serial.log`); 188 test IDs
  (`logs/inc2_test_ids.txt`); doctests 27 passed, 1 skipped; `ruff check` "All
  checks passed!"; `ruff format --check` "89 files already formatted";
  `ty check scripts src tests` "All checks passed!"; `interrogate` 100.0%.
- **E15 — The tests catch the defects they target.** `tools/mutate.py` copies
  `src/`, `tests/`, `examples/` and `pyproject.toml` to the scratchpad, applies
  one change to the copy's source, and runs the named tests there with
  `PYTHONPATH` set to the copy (`logs/inc2_mutations.log`, exit 0). All 13
  changes are caught: an override read with `or`, the survey reading page
  extraction's override (`test_each_step_s_verifier...`); reuse ignoring the
  verification (`test_turning_the_verifier_on...`); reuse always needing one
  (`test_page_files_rerun...`, `test_a_rerun_with_unchanged_inputs...`); text
  checks dropped with no verifier, the verifier always running, the log line
  saying `verifier passed` (`test_a_page_no_verifier_reviewed...`); the estimate
  always pricing the verifier (both estimate tests); a reused step claiming
  `verifier` (`test_estimate_writes_nothing...`); the report saying `passed`
  (`test_a_page_no_verifier_reviewed_says_so...`); the CLI dropping `--verify`,
  the estimate line omitting the verifier, the runner ignoring the switch
  (`test_verify_adds...`, `test_turning_the_verifier_on...`). The unmutated copy
  passes the 14 targeted tests.
- **E16 — Smoke script's expected requests.** `tools/smoke_requests.py` imports
  `scripts/smoke_installed_wheel.py` and runs its API run in-process with the
  editable install, for both providers, against the stand-in with the script's
  answer files: each run completes and sends exactly `EXPECTED_REQUESTS` (one
  upload, then the survey and one extractor request per page). The check's name
  at line 302 still said "one upload and 5 model requests", the defect routed to
  Developer and fixed in `45bfa10` (E21). The installed-wheel run itself is not
  replayed.
- **E17 — Reference pages.** `git checkout-index -a` into the scratchpad (the
  staged content), `python scripts/generate_reference_docs.py` there with
  `PYTHONPATH` set to the copy (11 pages), Prettier 3.10.1 on the pages, then
  `diff -r` with the repo's `docs/src/content/docs/reference/`: identical `.md`
  files (the repo also has the client's empty, untracked `.claude` folder
  there).
- **E18 — Module order of changed modules.** `tools/ordercheck.py order` on the
  10 changed modules of `src/` and `scripts/` and the 7 changed test modules:
  only the departures listed under `DEV-001` and in this report.
- **E19 — Inspection.** The `Config.verify`, `SurveyConfig.verify` and
  `ExtractionConfig.verify` docstrings, the `--verify`/`-vf` help text, the
  example files (values, positions after `pdf` and last in each section, YAML
  comments), `_log_estimate`'s `with its verifier`, `_verifier_outcome` and
  `_verifier_text` match **Settings**, **Example config files**, **CLI**, **Page
  extraction without a verifier** and **HTML report**.
- **E20 — Commits hold the assessed content.** `git diff 4a6bec7 384204a` gives
  SHA-256 `f710dcdbc349c854…` for `src scripts examples docs` and
  `e3a5c176d5dd1e4b…` for `tests`, so E12–E19 assess what `384204a` holds.
  `git diff --stat 384204a 45bfa10 -- src scripts examples docs tests pyproject.toml`
  lists only `scripts/smoke_installed_wheel.py` (2 insertions, 1 deletion), with
  SHA-256 `e1141021307f15d3…`, the plan's claim. Only E16 depends on that file;
  E12–E15 and E17–E19 stay valid, and E14 is rerun below.
- **E21 — The correction and checks on `45bfa10`.** `_check_requests` now names
  the check from the model requests in `EXPECTED_REQUESTS`;
  `grep -n "5 model requests" scripts/smoke_installed_wheel.py` finds nothing.
  `tools/smoke_check_name.py` (`python -I`) runs the script's API run in-process
  for both providers against the stand-in and passes the stand-in's requests to
  the script's own `_check_requests`: each run gives
  `PASS API, <provider>: one upload and 3 model requests, all to the stand-in`;
  a rerun on the same folder, which sends no request, gives `FAIL` with that
  name and `requests (route, status): []` (`logs/inc2_smoke_check_name.log`,
  exit 0). On the clean `45bfa10` tree:
  `pytest -q --numprocesses auto -p no:cacheprovider` exit 0, 188 passed;
  `pytest -q -p no:cacheprovider -p no:randomly` exit 0, 188 passed
  (`logs/inc2r_pytest_parallel.log`, `logs/inc2r_pytest_serial.log`); the 188
  collected IDs equal E14's; doctests 27 passed, 1 skipped; `ruff check`,
  `ruff format --check` (89 files), `ty check` and `interrogate` (100.0%) as in
  E14; `scripts/smoke_installed_wheel.py --help` exit 0; `ordercheck.py order`
  on the script reports only its listed departures.
- **Not run locally.** The wheel smoke test (it needs `uv build` and PyPI
  downloads; CI's wheel-install jobs run it, and `AC-028` is assessed at full
  verification). Python 3.14 (CI). The `just` recipes through `uv` (uv cannot
  write its cache in the sandbox; the `.venv/bin` tools are the versions they
  run).
- **Developer evidence.** The plan's `DEV-002` and `DEV-003` self-checks,
  including the correction's, agree with E12–E21; they were not used as
  evidence.

## Open Findings and Dependencies

- No open defect. The smoke script's check name, found in this assessment and
  routed to Developer with recovery frame 1, is fixed in `45bfa10` and verified
  (E21).
- Later-role dependencies, unchanged: `AC-032`, `AC-035`, `AC-036`, `AC-037` and
  `AC-038` (Documenter, documentation-record evidence); `AC-039` and `AC-040`
  (the user's accepted real runs).

## Resume or Handoff

Increments 1 and 2 are `VERIFIED`. Increment 2 (E12–E21) is returned to
Developer with a `CHECKPOINT`. The report stays `IN_PROGRESS` until full
verification.

### Suspended Assignment 1

`Recovery Frame`: `1` `Recovery Reason`:
`The wheel smoke script names its request check "one upload and 5 model requests" but now expects one upload and 3 model requests (scripts/smoke_installed_wheel.py line 302).`
`Purpose`: `INCREMENT` `Target`: `Increment 2` `Assessed Inputs`:
`4a6bec7 plus staged diff f710dcdbc349c854; tests diff e3a5c176d5dd1e4b`
`Next Action`:
`Check that the source diff changed only the smoke script's check name, replay E16 with the corrected script, rerun the suite and linters, then mark Increment 2 VERIFIED and return it to Developer with a CHECKPOINT.`

Restored on Developer's `RESUME` after frame 1 closed, and completed: E20 and
E21 carry out its next action.

Next Tester action: assess Increment 3 (`DEV-004` to `DEV-007`; the survey parts
of `AC-001`, `AC-005`, `AC-006`, and `AC-007` to `AC-017`) when Developer hands
it over. `config/schemas.py` and `costs/budget.py` have no scenario allowance
left (see **Scenario Budget**).

Remaining acceptance work after Increment 2: the survey parts of `AC-001`,
`AC-005` and `AC-006`, and `AC-007` to `AC-017` (Increment 3); `AC-021` to
`AC-025` (Increment 4); `AC-026` to `AC-031`, `AC-033`, `AC-034` with `DEV-011`
and full verification.

<!-- STANDARDS
Artifact: VERIFICATION
Cycle: build-step-3-page-break-verification-of-20261122T170208Z-00fe2896
-->

# Verification Report

`Cycle`: `build-step-3-page-break-verification-of-20261122T170208Z-00fe2896`
`Mode`: `VERIFY` `Status`: `COMPLETE` `User Style`: `tony` `Assessment Purpose`:
`FULL` `Assessment Target`: `NONE`

## Assessed Inputs

- Scope `.standards/docs/scope/<id>.md` (SHA-256 `c0f8b54a9851b32c`), design
  `.standards/docs/specs/<id>.md` (`e9006fbf2a78ee99`), plan
  `.standards/docs/development/<id>.md` (`01434a6d99513f03`, `COMPLETE`,
  `AFTER_IMPLEMENTATION`, `Current Increment: NONE`), context
  `.standards/CONTEXT.md` (`0e940ffe605aecff`). These were unchanged from start
  to end. The current acceptance set is `AC-001` to `AC-051`, and the scope
  retires none. The design's technical acceptance criteria share those IDs.
- Active change: `main..HEAD` on `tz6/pipeline-step-3` at `68b675c`, with no
  source changes in the working tree.
  - Scale: 41 files, 7,836 insertions, 380 deletions (commits `75e0ecd` to
    `68b675c`).
  - New package: `src/pydelity/verifying/`.
  - Changed source: `config/schemas.py`, `providers/{profiles,factory}.py`,
    `review.py`, `errors.py`, `schema_versions.py`, `costs/{budget,schemas}.py`,
    `pipeline/{runner,schemas}.py`, `api.py`, `__init__.py`, `cli.py`,
    `report/{html.py,report.css}`.
  - Other changes: `examples/config.{json,yaml}`,
    `scripts/{smoke_installed_wheel,generate_reference_docs}.py`, and the
    generated reference pages.
- Tester's working-tree changes are uncommitted (8 modified files and 2 new
  paths).
  - Modified: `tests/conftest.py`, `tests/fixtures/mock_providers.py`,
    `tests/pydelity/{config/test_loading,costs/test_budget,extracting/test_extraction,pipeline/test_runner,report/test_html,test_cli}.py`.
  - New: `tests/pydelity/verifying/` (`__init__.py`, `conftest.py`
    `d52c2f7cf9d26176`, `test_prompts.py` `ef6ebe46604b4416`,
    `test_validators.py` `ca8e8684e7aaa0ab`, `test_verification.py`
    `93154fb2a8b74d99`) and this report.
- Environment: macOS arm64 (Darwin 25.6.0).
  - Main environment: Python 3.13.9 in `.venv`, with PydanticAI 2.69.0, PyMuPDF
    2.1 and Pydantic 2.14.3.
  - Second environment: Python 3.14.10 in a scratch uv environment built from
    `uv.lock`.
  - Tools run from `.venv/bin`, because uv cannot write its cache in the
    sandbox.
- Reason: full verification after the Developer's forward handoff (DEV-001 to
  DEV-011 `DONE`, plan `COMPLETE`). It includes the 11 tests of replaced
  contracts that the plan lists.
- Session: this Tester conversation holds no Developer implementation history.
  The client gives no session metadata, so freshness is not machine-certified.
- Project references loaded: `NONE` (`.standards/project-references/` does not
  exist). Shipped reference loaded: `references/llm-api-testing.md` (the step
  calls model APIs through PydanticAI).

## Acceptance Evidence

Paths are under `tests/pydelity/`. Abbreviations:

- `TV` = `verifying/test_verification.py`
- `TVA` = `verifying/test_validators.py`
- `TP` = `verifying/test_prompts.py`

Scenario IDs (V, F, R, C, A, L, P, H, CFG, API, U) are defined under Scenario
Budget and Resume or Handoff. Every listed test passed in the final run on
Python 3.13 and on Python 3.14 (Execution Evidence 2 and 3), unless the row says
otherwise.

| AC / technical criterion | Tests or checks                                                                                                                                                                                   | Disposition and evidence                                                                                                                                                                                                                                                                                                                                                                                                |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AC-001                   | R1 `TV::test_run_pauses_after_the_survey_and_page_extraction_then_judges`; U5 (CLI, three runs)                                                                                                   | Verified. Default `run()` and the CLI each record survey, extraction and `page_breaks`, and both judge after the second pause.                                                                                                                                                                                                                                                                                          |
| AC-002                   | R3, API2, U7; inspection of `verifying/verification.py:923` `current_pages`                                                                                                                       | Verified. Only pages written this run, or pages `plan_pages(quiet=True)` would reuse, are read. That reuse rule is page extraction's, which checks the PDF hash, fingerprint and verifier, and its existing tests cover it. A missing page file means no step request.                                                                                                                                                  |
| AC-003                   | U7 (CLI `-p 2 -np`), API2, R3                                                                                                                                                                     | Verified. The step is `skipped`, and one `missing_page_files` warning gives the exact message and `page_indexes`. The run is `completed`, and every break is judged once the other pages are current.                                                                                                                                                                                                                   |
| AC-004                   | R4 `TV::test_a_one_page_pdf_makes_no_page_break_request_and_completes`                                                                                                                            | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-005                   | R1, U5, U6 (second run), U11; `-np` in U7 and U12                                                                                                                                                 | Verified. A new page file gives `paused` with the step skipped. The next run judges, and a run that reuses every page file goes on. With `pause` off, the run never pauses.                                                                                                                                                                                                                                             |
| AC-006                   | API1 `TV::test_the_api_judges_what_is_missing_without_pausing_and_reuses_it`, API2                                                                                                                | Verified. `verify_breaks`/`averify_breaks` run the missing steps, never pause, return verdicts in break order, reuse on a second call, and follow the narrowed-`pages` rule.                                                                                                                                                                                                                                            |
| AC-007                   | R7 `TV::test_load_leaves_out_a_verdict_whose_page_file_changed`; U4                                                                                                                               | Verified. `load` returns verdicts in break order and leaves out a verdict whose page file changed.                                                                                                                                                                                                                                                                                                                      |
| AC-008                   | CFG1 (3 rows); inspection of `config/schemas.py:468`                                                                                                                                              | Verified. The resolution order is the step override, then `model`, then `DEFAULT_PAGE_BREAKS_MODEL`, with effort `high`.                                                                                                                                                                                                                                                                                                |
| AC-009                   | F2+P3 `TV::test_the_step_s_instructions_reach_only_its_requests_and_rerun_only_it`; inspection of `cli.py` (no option)                                                                            | Verified. Instructions end the judge's and verifier's instructions only. No break request holds another step's instructions or `pdf_sha256`, and without the setting no instructions section is sent.                                                                                                                                                                                                                   |
| AC-010                   | Existing example-config completeness test (`config/`), unchanged and passing                                                                                                                      | Verified. Both files hold `advanced.page_breaks` at its defaults and load.                                                                                                                                                                                                                                                                                                                                              |
| AC-011                   | F1, U4, R1                                                                                                                                                                                        | Verified. `page_breaks/NNNN-NNNN.json` holds both page indexes and `continues`.                                                                                                                                                                                                                                                                                                                                         |
| AC-012                   | V1 (several pieces, entry IDs); V7                                                                                                                                                                | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-013 / AC-014          | V1 (space, no space, dehyphenate, cell joins); V2 (code dehyphenate, `new_entry` with a text join)                                                                                                | Verified. Join-rule breaches fail `joins`.                                                                                                                                                                                                                                                                                                                                                                              |
| AC-015 / AC-024          | V1, V4                                                                                                                                                                                            | Verified. `repeated_header_rows` is accepted when the rows match the earlier header, and fails `header_rows` when they do not.                                                                                                                                                                                                                                                                                          |
| AC-016                   | V1, V5                                                                                                                                                                                            | Verified. A repeated item the earlier page did not print fails `repeats`.                                                                                                                                                                                                                                                                                                                                               |
| AC-017                   | V1 (`续表` marker in a cell), V6                                                                                                                                                                  | Verified. A marker its cell does not hold fails `markers`.                                                                                                                                                                                                                                                                                                                                                              |
| AC-018                   | V1, V7 (container on the wrong page fails `ids`); H1                                                                                                                                              | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-019                   | V3; inspection of the judge's instructions in `verifying/prompts.py`                                                                                                                              | Verified. A piece ending in page furniture fails `furniture`. The instructions say furniture never joins and does not stop content from continuing.                                                                                                                                                                                                                                                                     |
| AC-020                   | P1 `TV::test_rotated_pages_are_sent_upright_with_boxes_on_the_upright_grid`; P2 `TP::test_right_to_left_and_vertical_pages_state_their_direction_and_column_order`                                | Verified. Images are sent upright for content turned sideways on an attribute-0 page and for attribute 90 (turns 90 and 270). Boxes go out on the upright grid and come back on page extraction's grid. Right-to-left and vertical pages state their direction and column order, and end and start are defined by reading order. Attribute 180 goes through the same rendering path that page extraction's tests cover. |
| AC-021                   | V8 `TVA::test_page_files_that_break_their_own_rules_go_through_every_check_and_prompt`; inspection of `verification.py:194` `_break_context`                                                      | Verified. Every check, the hint and both prompts run without error on failing checks, `null` or dangling `container`/`caption_of`, a column order that does not fit the direction, and broken tables and lists. The step reads only `continuation_notes` and `start_markers` from the profile, so faulty ranges or artifact mappings cannot reach it.                                                                   |
| AC-022                   | Inspection: grep of `src/pydelity/verifying/*.py` for language, script, document-type and direction words and for regexes                                                                         | Verified. Logic holds no word lists or patterns. The direction statements in prompts are chosen from page-file values. Docstring and doctest examples are not logic.                                                                                                                                                                                                                                                    |
| AC-023                   | A1 `TV::test_a_failed_check_is_sent_back_then_the_last_verdict_is_kept_for_review`; L1                                                                                                            | Verified. A failed check is retried within `check_retries`. The last verdict is kept with its failures in `checks`, `issues`, `run.json` and the summary, and the run goes on.                                                                                                                                                                                                                                          |
| AC-025                   | V9; F2+P3 (notes and markers under the hints heading)                                                                                                                                             | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-026                   | V9 (retry message excludes the hint; issues with and without a passing verifier); F5–F7 rows (A2)                                                                                                 | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-027                   | R1 (no verifier ledger line, `verification` null)                                                                                                                                                 | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-028                   | CFG2 (2 rows); U12 (`--verify` and `-vf`); U13                                                                                                                                                    | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-029                   | F5–F7 `TV::test_each_verifier_outcome_decides_the_kept_verdict_and_the_review_issues` (3 rows); A3 `TV::test_a_correction_that_fails_a_check_is_sent_back_then_rejected`                          | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-030                   | F5–F7, A3 (saved `verification`, attempts, applied flag, failed checks)                                                                                                                           | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-031                   | A1 (`run.json` and summary line "page_breaks: pages 1 and 2: …"); F5–F7; H1                                                                                                                       | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-032                   | U6 (ledger line `page_breaks`/earlier page/`judge`, `by_step`, total); U12 (verifier line)                                                                                                        | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-033                   | U8 (estimate with and without the verifier; step left out for a narrowed `pages`); C1 within R3; R5 `TV::test_a_page_break_request_first_shows_the_estimate_and_a_no_stops_it_unsent`; U9         | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-034                   | R6 `TV::test_break_requests_sent_at_once_are_held_to_max_cost_together`                                                                                                                           | Verified. Three concurrent requests raise `BudgetExceededError` with the projected spend about the recorded spend plus $64. One at a time, the run completes without a warning.                                                                                                                                                                                                                                         |
| AC-035                   | U4 (unchanged inputs); F1 (one page, two breaks); F2 (instructions only, earlier steps reused); one-off check of `overwrite`, step model, `max_output_tokens` and `effort` (Execution Evidence 9) | Verified. Each change re-judged both breaks, and only `overwrite` reran the earlier steps. A third run with the same change reused every verdict. The fingerprint covers the whole stored `inputs`, including continuation notes and start markers (`verification.py:288`). The one-off check is not kept in the suite.                                                                                                 |
| AC-036                   | F3 (turning the step's verifier on re-judges only unreviewed `model` verdicts; `no_content` stays); F1; inspection of `_break_inputs`                                                             | Verified. Another step's verifier affects a break only through page-file bytes or the survey context, both of which are in the fingerprint.                                                                                                                                                                                                                                                                             |
| AC-037                   | F8 `TV::test_a_damaged_verdict_file_warns_and_its_break_is_judged_again`; L2; inspection of `write_model_atomic` at `verification.py:836`                                                         | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-038                   | L1 (CLI exit 1); L2 (provider error after retries; the next run judges only the rest); L3/L4 (refusal and used-up output tokens raise `PageBreakError` unretried, one row per provider)           | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-039                   | H1 `report/test_html.py::test_a_break_card_shows_its_pieces_beside_both_pages_with_links_from_issues`; H2 `…::test_a_break_with_an_empty_page_and_markup_in_a_verdict_show_safely`; U10           | Verified. Each card shows both pages, the item and container boxes, join rules, repeated rows and items, markers and the verifier outcome. Issues link to `#break-NNNN`, and markup is escaped.                                                                                                                                                                                                                         |
| AC-040                   | The whole suite (Execution Evidence 2)                                                                                                                                                            | Verified. Anthropic and OpenAI responses come from the stand-in, and no request leaves the machine. The suite covers each listed case.                                                                                                                                                                                                                                                                                  |
| AC-041                   | `.github/workflows/ci.yml` (tests on 3.13 and 3.14) unchanged from `main`; ruleset 27420482 on `main` requires "Lint and test" and "TruffleHog secret scan"; local 3.14 run                       | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-042                   | Smoke script on macOS (Execution Evidence 7)                                                                                                                                                      | Partly verified: macOS passed. Linux and Windows are pending (see Open Findings and Dependencies).                                                                                                                                                                                                                                                                                                                      |
| AC-043                   | Build, `twine check --strict` and the smoke install (Execution Evidence 6 and 7)                                                                                                                  | Verified.                                                                                                                                                                                                                                                                                                                                                                                                               |
| AC-044                   | `pyproject.toml` description and classifiers                                                                                                                                                      | The package text is verified: the description names the three steps and the verifiers. The README is pending Documenter (it still says "in two steps", `README.md:6`).                                                                                                                                                                                                                                                  |
| AC-045                   | `release-please-config.json` and `.release-please-manifest.json` (`0.2.0`) unchanged from `main`                                                                                                  | The setup is verified. The release is pending a later phase (see Open Findings and Dependencies).                                                                                                                                                                                                                                                                                                                       |
| AC-046                   | None at this phase                                                                                                                                                                                | Pending Documenter.                                                                                                                                                                                                                                                                                                                                                                                                     |
| AC-047                   | Regenerated reference pages compared with the committed ones (Execution Evidence 8); grep for new settings, functions, verdict fields, checks and hint                                            | Verified. All 13 pages match the code. `configuration.md`, `python-api.md`, `page-break-json.md`, `page-break-checks.md`, `run-json.md` and `cost-jsonl.md` hold the new content.                                                                                                                                                                                                                                       |
| AC-048                   | None at this phase                                                                                                                                                                                | Pending Documenter.                                                                                                                                                                                                                                                                                                                                                                                                     |
| AC-049                   | None at this phase                                                                                                                                                                                | Pending Documenter.                                                                                                                                                                                                                                                                                                                                                                                                     |
| AC-050                   | None at this phase                                                                                                                                                                                | Pending the user's real runs.                                                                                                                                                                                                                                                                                                                                                                                           |
| AC-051                   | None at this phase                                                                                                                                                                                | Pending the user's real runs.                                                                                                                                                                                                                                                                                                                                                                                           |

## Scenario Budget

Allocations were recorded before coverage was added and are final. Scenario IDs
are local to this report. Updated tests of replaced contracts (U1–U13, listed
under Resume or Handoff) reuse their existing allocations.

| Source file                   | Reused coverage                  | Active-change allocations (used)            | User additions     |
| ----------------------------- | -------------------------------- | ------------------------------------------- | ------------------ |
| `verifying/validators.py`     | none                             | V1–V9 (9)                                   | approved: up to 9  |
| `verifying/verification.py`   | U4                               | F1, F2, F3, F4, F5, F6, F7, F8, L2, A3 (10) | approved: up to 10 |
| `pipeline/runner.py`          | U1–U13 where they record steps   | R1, R3, R4, R5, R6, R7, C1, A1, L1 (9)      | approved: up to 9  |
| `verifying/prompts.py`        | none                             | P1, P2, P3, V8 (4)                          | none               |
| `verifying/llm.py`            | none                             | P1, L1, L3, L4 (4)                          | none               |
| `verifying/agents.py`         | none                             | A1, A2, A3 (3)                              | none               |
| `config/schemas.py`           | example-config completeness test | CFG1 (3 rows), CFG2 (2 rows) (5)            | none               |
| `api.py`                      | none                             | API1, API2 (2)                              | none               |
| `report/html.py`              | U10                              | H1, H2 (2)                                  | none               |
| `cli.py`                      | U5, U7, U12                      | L1, R5 (2)                                  | none               |
| `costs/budget.py`             | U8, U9                           | R6, C1 (2)                                  | none               |
| `examples/config.{json,yaml}` | example-config completeness test | none                                        | none               |

User additions: on 2026-11-22 the user approved targeted increases to 9 new
scenarios for `verifying/validators.py`, 10 for `verifying/verification.py` and
9 for `pipeline/runner.py`, for the scenarios planned below, and no others.

How scenarios share tests:

- C1 sits in R3's test, as the estimate for the same narrowed run.
- F2 and P3 share one test, and F3 and F4 share one test.
- A2 is asserted in each F5–F7 row.
- L3 and L4 are one parametrized test, with one row per provider.
- CFG1 adds the `page-breaks-model` row. CFG2 adds the `page-breaks-on` and
  `page-breaks-off-in-file` rows.

Test-helper changes do not count toward any file's allowance:

- The stand-in's `REFUSAL` and `OUTPUT_LIMIT` answers.
- `blank_pdf` in `tests/conftest.py`.
- `break_answers` in `canned_answers`.
- The `verifying/conftest.py` builders.

Scenario plan:

- V1 a correct verdict with several pieces (a sentence in Arabic, a split table
  row and repeated header rows in Chinese, a repeated title, markers, a
  continuing container) passes every check and differs from no hint; V2 a join
  breach fails `joins`; V3 an end in page furniture fails `furniture`; V4 header
  rows that do not repeat fail `header_rows`; V5 a repeated item not on the
  earlier page fails `repeats`; V6 a marker not in its carrier fails `markers`;
  V7 an unknown item and an entry of another item fail `ids`; V8 page files that
  break their own rules run through every check, the hint and both prompts
  without an error; V9 a start marker gives a `start_markers` difference that no
  retry message holds.
- F1 re-extracting one page re-judges its two breaks only; F2 a change to
  page-break verification's instructions alone re-judges every break and reruns
  neither earlier step; F3 turning the step's verifier on re-judges only
  unreviewed `model` verdicts; F4 a page with no content items gives a
  `no_content` verdict without a request; F5 verifier passed; F6 correction
  kept; F7 problems without a correction listed; F8 a damaged verdict file warns
  and is judged again; L2 a provider error after retries stops the run, keeps
  written verdicts, and the next run judges only the rest; A3 a correction that
  fails a check is sent back, then rejected.
- R1 `run()` with default settings pauses after the survey and after page
  extraction, then judges, recording the same steps; R3 a narrowed `pages` with
  every other page current judges every break; R4 a one-page PDF; R5 a run whose
  first request is a page-break request shows the estimate and a no stops it
  unsent; R6 concurrent break requests are held to `max_cost`; R7 `load` leaves
  out a verdict whose page file changed; C1 the estimate includes the step when
  the run will judge breaks; A1 a check failure is sent back, then the last
  verdict is kept and listed in `run.json` and the summary; L1 an unusable judge
  answer stops the run and the CLI exits 1.
- P1 rotated pages are sent as upright images with upright grid boxes; P2
  right-to-left and vertical pages state their direction and column order; P3
  the instructions hold the hints, then the step's instructions last, and no
  other step's instructions; L3 a refusal and L4 used-up output tokens each
  raise `PageBreakError`; A2 a hint difference is never sent back; CFG1 the
  step's model resolution; CFG2 the step's verifier switch; API1
  `averify_breaks` runs what is missing, never pauses and returns verdicts in
  break order; API2 a narrowed `pages` returns none with the warning; H1 a break
  card with pieces; H2 a `no_content` card and escaping.

## Execution Evidence

All commands ran from the repo root on the assessed revision with the Tester
changes above.

1. Baseline at `68b675c`:
   `.venv/bin/python -m pytest -q --numprocesses auto -p no:cacheprovider` gave
   200 passed and 11 failed. The failures were the 11 tests of replaced
   contracts that DEV-008 lists, which matches the plan's claim. Developer
   self-checks are not formal evidence.
2. Final run on Python 3.13.9, same command: 248 passed, 0 failed, exit 0 (211
   before plus 37 new).
   - The 70 warnings are PyMuPDF's SWIG `DeprecationWarning`s and 4 expected
     `missing_page_files` `PydelityWarning`s. The 4 come from earlier tests that
     narrow `pages`, which is this cycle's contract (AC-003).
3. Python 3.14.10, with `UV_CACHE_DIR=$TMPDIR/uv-cache` and
   `UV_PROJECT_ENVIRONMENT=$TMPDIR/venv314`:
   - `uv run --python 3.14 --locked pytest -q --numprocesses auto -p no:cacheprovider`:
     248 passed.
   - Doctests (`python -m pytest -q --doctest-modules src`): 37 passed, 1
     skipped.
4. Python 3.13.9 doctests:
   `.venv/bin/python -m pytest -q --doctest-modules src -p no:cacheprovider`
   gave 37 passed and 1 skipped (an existing `+SKIP` example).
5. Lint, types and docstrings all passed:
   - `.venv/bin/ruff check scripts src tests`
   - `.venv/bin/ruff format --check scripts src tests` (101 files already
     formatted)
   - `.venv/bin/ty check scripts src tests`
   - `.venv/bin/interrogate scripts src tests` (100%)
6. Build: `uv build --out-dir "$TMPDIR/dist"`, then `twine check --strict` on
   the wheel and sdist.
   - Both passed. The build needed pypi.org and files.pythonhosted.org, allowed
     for that command.
   - The version string is `0.2.0`, from the manifest. release-please sets
     `0.3.0` after merge.
7. Wheel smoke test on macOS arm64:
   `.venv/bin/python scripts/smoke_installed_wheel.py --wheel $TMPDIR/dist/pydelity-0.2.0-py3-none-any.whl`
   passed 13 of 13 checks.
   - It ran outside the sandbox, because pip fails TLS verification inside it.
   - pip installed the wheel into a clean environment. The `pydelity` command
     and the Python API then ran the survey, page extraction and page-break
     verification against the stand-in, with each provider.
8. Reference pages: `scripts/generate_reference_docs.py` was run into a scratch
   copy and formatted with the hook's pinned prettier 3.10.1. All 13 pages are
   byte-identical to the committed ones.
9. One-off check of the `overwrite`, step-model, `max_output_tokens` and
   `effort` changes (AC-035):
   - A temporary parametrized test in `tests/pydelity/verifying/` used the
     suite's fixtures. It passed 4 of 4 and was then removed.
   - Its source is kept at
     `/private/tmp/claude-501/-Users-tzz--claude-spares-spare-cJvwTV/fd9c16e8-1ed8-4165-814f-5c0217cedc7a/scratchpad/test_scratch_rejudge.py`.
   - It is execution evidence, not regression coverage. Adding it to the suite
     would need another allocation for `verifying/verification.py`.
10. CI and release setup:
    - `git diff main --stat -- .github release-please-config.json .release-please-manifest.json`
      is empty.
    - `gh api repos/{owner}/{repo}/rulesets/27420482`: active on `main`, and
      requires "Lint and test" and "TruffleHog secret scan".
    - The "Lint and test" gate needs `lint-and-test`, `test-py314` and the
      `wheel` matrix (Linux, macOS, Windows).
11. `node .standards/bin/check.mjs`: no problems (run before handoff).

Limits:

- No real provider was called.
- The Linux and Windows wheel runs are not local.
- The judge's real accuracy on real documents is out of scope here; AC-050 and
  AC-051 cover it.

## Open Findings and Dependencies

No implementation, upstream or verification defect is open, and no blocking user
question is pending.

Later-role dependencies, each resolved under the same AC ID:

| AC     | Owner                                                     | Evidence still required                                                                                                                                                 |
| ------ | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AC-042 | The user pushes the branch, and CI checks it before merge | `Wheel install (ubuntu-latest)` and `Wheel install (windows-latest)` pass on this branch's pull request. The required "Lint and test" check enforces this before merge. |
| AC-044 | Documenter                                                | The README describes the three steps and the optional verifier for each.                                                                                                |
| AC-045 | Release after sign-off and merge                          | release-please opens the 0.3.0 pull request (tag `v0.3.0`), and accepting it starts the PyPI and docs publication.                                                      |
| AC-046 | Documenter                                                | The docs-site guides, with the async functions first in the Python guide.                                                                                               |
| AC-047 | Documenter                                                | Only if the docs change the code: regenerate the pages and keep them matching.                                                                                          |
| AC-048 | Documenter                                                | The README quick start and all command and code examples match 0.3.0.                                                                                                   |
| AC-049 | Documenter                                                | `artifacts/next_cycle_inputs.md` "Pushed to later steps" is updated.                                                                                                    |
| AC-050 | User                                                      | Real runs with default settings on the named PDF kinds are accepted.                                                                                                    |
| AC-051 | User                                                      | Real runs with the verifier on are accepted.                                                                                                                            |

Note for review: R1 (`TV::test_run_pauses_after_…`) covers AC-027 as well as
AC-001 and AC-005.

## Resume or Handoff

Testing is complete. Hand off to Reviewer, review kind `IMPLEMENTATION`.

Updated tests of replaced contracts (paths under `tests/pydelity/`):

- U1 `test_api.py::test_async_run_gives_what_run_gives_with_the_same_warnings`:
  passes through `canned_answers`, which now gives break answers.
- U2
  `surveying/test_survey.py::test_turning_the_survey_s_verifier_on_surveys_again_only_what_no_verifier_reviewed`:
  same.
- U3 `pipeline/test_runner.py::test_no_output_file_holds_the_api_key`: same.
- U4
  `pipeline/test_runner.py::test_a_rerun_with_unchanged_inputs_reuses_everything`:
  four first-run requests, every verdict reused, and the step's concurrency and
  timeout settings may change.
- U5
  `test_cli.py::test_a_pdf_alone_runs_the_survey_with_keys_from_the_environment`:
  three runs. The third judges the break after its estimate.
- U6
  `pipeline/test_runner.py::test_run_json_records_each_step_its_pages_cost_and_review_issues`:
  a page-break ledger line, `by_step`, outputs, and a pause after a page is
  extracted again.
- U7 `test_cli.py::test_pages_and_no_pause_extract_only_those_pages_in_one_run`:
  `page_breaks` is skipped with `missing_page_files`, and the estimate leaves
  the step out.
- U8
  `costs/test_budget.py::test_the_estimate_covers_the_later_steps_and_their_verifiers_only_when_they_run`
  (renamed): the step's breaks and requests, with and without the verifier.
- U9
  `costs/test_budget.py::test_estimate_writes_nothing_and_a_reusable_survey_costs_nothing`:
  the verdicts are reused.
- U10
  `report/test_html.py::test_a_page_no_verifier_reviewed_says_so_in_the_report`:
  break answers and a shorter docstring.
- U11
  `extracting/test_extraction.py::test_a_failed_page_stops_the_run_and_the_next_run_extracts_only_what_is_missing`:
  the next run pauses after the new page files.
- U12
  `test_cli.py::test_verify_adds_a_verifier_request_for_each_step_and_to_the_estimate`
  (2 rows): the whole PDF, with the break's judge and verifier requests, the
  estimate and the ledger.
- U13
  `config/test_loading.py::test_verify_turns_on_every_step_s_verifier_from_a_file_or_a_keyword`
  (renamed): all three verifiers. The two existing rows of the verifier test
  gained a third expectation, and `both-off-file-and-keyword` became
  `two-off-file-and-keyword`.

For the independent Reviewer:

- Inputs: the scope, design, plan and context above; the branch `main..HEAD` at
  `68b675c`; and the uncommitted Tester changes listed under Assessed Inputs.
- Re-run the checks with Execution Evidence 2, 4 and 5.
- The evidence that matters most for review:
  - AC-035 (one-off check, not kept in the suite).
  - AC-042 (Linux and Windows wait for CI).
  - AC-022 (inspection).
  - The later-role dependencies listed above, which must be resolved under their
    IDs before sign-off.

<!-- STANDARDS
Artifact: VERIFICATION
Cycle: build-step-3-page-break-verification-of-20261122T170208Z-00fe2896
-->

# Verification Report

`Cycle`: `build-step-3-page-break-verification-of-20261122T170208Z-00fe2896`
`Mode`: `REVERIFY` `Status`: `COMPLETE` `User Style`: `tony`
`Assessment Purpose`: `FULL` `Assessment Target`: `NONE`

## Assessed Inputs

- Scope `.standards/docs/scope/<id>.md` (SHA-256 `f8655478af2060c8`), design
  `.standards/docs/specs/<id>.md` (`5bd367355f1a64b8`), plan
  `.standards/docs/development/<id>.md` (`c8107620423e0d6e`, `COMPLETE`,
  `AFTER_IMPLEMENTATION`, `Current Increment: NONE`, DEV-001 to DEV-016 `DONE`),
  context `.standards/CONTEXT.md` (`0e940ffe605aecff`). None changed during this
  pass.
- Current acceptance set: `AC-001` to `AC-024`, `AC-027`, `AC-028`, `AC-031` to
  `AC-035`, `AC-037` to `AC-049` and `AC-052` to `AC-062`. Retired: `AC-025`,
  `AC-026`, `AC-029`, `AC-030`, `AC-036`, `AC-050`, `AC-051` (see Superseded
  evidence). The design's technical criteria share these IDs.
- Active change: `main..HEAD` on `tz6/pipeline-step-3` at `bc56b21`, with no
  source changes in the working tree.
  - The rework under reconciliation is `50229ba` to `bc56b21` (after the docs
    commit `1a0cae1`). It changes
    `verifying/{agents,llm,prompts,schemas,validators,verification}.py`,
    `review.py`, `costs/budget.py`, `report/html.py`, `cli.py` and
    `config/schemas.py` (help and descriptions),
    `scripts/{generate_reference_docs,smoke_installed_wheel}.py`,
    `examples/config.yaml`, eight generated reference pages, and two test
    helpers the Developer changed: `tests/fixtures/mock_providers.py` (break
    answers by earlier page, served in arrival order) and
    `tests/fixtures/break_answers/irs_form_1040a_1965_scan.json`.
  - `uv.lock`, `pyproject.toml` and `.github/` are unchanged since the earlier
    pass at `68b675c`.
- Tester's working-tree changes are uncommitted (6 test files and this report):
  `tests/conftest.py` (`c4c0c04766276a5a`), `tests/fixtures/mock_providers.py`
  (`81ddfe107d2bc806`), `tests/pydelity/report/test_html.py`
  (`6a847167c5d1a4c7`), `tests/pydelity/test_cli.py` (`6ac521cb6ac34459`),
  `tests/pydelity/verifying/test_validators.py` (`450645e43a532a44`),
  `tests/pydelity/verifying/test_verification.py` (`74855c4384bf601b`).
- Environment: macOS arm64 (Darwin 25.6.0).
  - Main: Python 3.13.9 in `.venv`, with PydanticAI 2.69.0, PyMuPDF 2.1 and
    Pydantic 2.14.3.
  - Second: Python 3.14.10 in a scratch uv environment built from `uv.lock`.
  - Tools run from `.venv/bin`, because uv cannot write its cache in the
    sandbox.
- Reason: full reverification for recovery frame 1 (from `REVIEWING_FINAL`)
  after the user's rework, DEV-012 to DEV-016: `new_entry` from a text item, the
  `repeat` cell join, the unfinished-text rule, the narrower start-marker hint,
  and the verifier's second, unseen judgment compared in code. Evidence from the
  earlier pass is reused only where its source, tests and environment are
  unchanged; every check was re-run on `bc56b21`.
- Session: this Tester conversation holds no Developer implementation history.
  The client gives no session metadata, so freshness is not machine-certified.
- Project references loaded: `NONE` (`.standards/project-references/` does not
  exist). Shipped reference loaded: `references/llm-api-testing.md`.

## Acceptance Evidence

Paths are under `tests/pydelity/`. `TV` = `verifying/test_verification.py`,
`TVA` = `verifying/test_validators.py`, `TP` = `verifying/test_prompts.py`.
Scenario IDs are defined under Scenario Budget and Resume or Handoff. Every
listed test passed in the final runs on Python 3.13 and 3.14 (Execution Evidence
2 and 3).

| AC / technical criterion | Tests or checks                                                                                                                                                                                                                                                                                                                                                                                           | Disposition and evidence                                                                                                                                                                                                                   |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| AC-001                   | R1 `TV::test_run_pauses_after_the_survey_and_page_extraction_then_judges`; U5                                                                                                                                                                                                                                                                                                                             | Verified. `run()` and the CLI record survey, extraction and `page_breaks`, and judge after the second pause.                                                                                                                               |
| AC-002                   | R3, API2, U7; inspection of `current_pages` in `verifying/verification.py`                                                                                                                                                                                                                                                                                                                                | Verified. Only pages written this run, or pages page extraction would reuse, are read. A missing page file means no step request.                                                                                                          |
| AC-003                   | U7, API2, R3                                                                                                                                                                                                                                                                                                                                                                                              | Verified. The step is `skipped` with one `missing_page_files` warning naming the page indexes; the run completes.                                                                                                                          |
| AC-004                   | R4 `TV::test_a_one_page_pdf_makes_no_page_break_request_and_completes`                                                                                                                                                                                                                                                                                                                                    | Verified.                                                                                                                                                                                                                                  |
| AC-005                   | R1, U5, U6, U11; `-np` in U7 and U12                                                                                                                                                                                                                                                                                                                                                                      | Verified.                                                                                                                                                                                                                                  |
| AC-006                   | API1 `TV::test_the_api_judges_what_is_missing_without_pausing_and_reuses_it`, API2                                                                                                                                                                                                                                                                                                                        | Verified. Ledger agents show one judge request per break.                                                                                                                                                                                  |
| AC-007                   | R7 `TV::test_load_leaves_out_a_verdict_whose_page_file_changed`; U4                                                                                                                                                                                                                                                                                                                                       | Verified.                                                                                                                                                                                                                                  |
| AC-008                   | CFG1 (3 rows)                                                                                                                                                                                                                                                                                                                                                                                             | Verified.                                                                                                                                                                                                                                  |
| AC-009                   | F2+P3 `TV::test_the_step_s_instructions_reach_only_its_requests_and_rerun_only_it`                                                                                                                                                                                                                                                                                                                        | Verified. The instructions reach the judge's and the verifier's requests only.                                                                                                                                                             |
| AC-010                   | Existing example-config completeness test                                                                                                                                                                                                                                                                                                                                                                 | Verified.                                                                                                                                                                                                                                  |
| AC-011                   | F1, U4, R1                                                                                                                                                                                                                                                                                                                                                                                                | Verified.                                                                                                                                                                                                                                  |
| AC-012                   | V1, V7                                                                                                                                                                                                                                                                                                                                                                                                    | Verified.                                                                                                                                                                                                                                  |
| AC-013 / AC-014          | V1, V2; V11 and V13 (`TVA::test_a_new_entry_into_text_and_a_repeat_text_join_fail_the_joins_check`)                                                                                                                                                                                                                                                                                                       | Verified. Join-rule breaches fail `joins`, including `new_entry` starting in a text item and `repeat` as a text join.                                                                                                                      |
| AC-052                   | V10 `TVA::test_a_new_entry_from_a_text_item_and_a_repeated_row_label_pass_every_check`; V11; inspection of the `new_entry` rule in `verifying/prompts.py` (`_RULES`)                                                                                                                                                                                                                                      | Verified. A `new_entry` ending in a text item on the earlier page passes every check; one starting in a text item on the later page fails `joins`. The instructions allow the earlier end to be a text item.                               |
| AC-053                   | V12 (same test as V10), V13, V14 `TVA::test_repeat_cells_with_no_text_or_another_text_fail_the_repeats_check`; inspection of the `repeat` rule in `_RULES`                                                                                                                                                                                                                                                | Verified. A `repeat` cell repeating the split row's label passes; `repeat` as a text join fails `joins`; a `repeat` cell with no text or other text fails `repeats`.                                                                       |
| AC-054                   | Inspection of `verifying/prompts.py` `_RULES` ("When text carries on"), which `judge_instructions` puts in every break request; F5' shows the verifier gets the same request                                                                                                                                                                                                                              | Verified. Text or an entry continues only when the text itself is unfinished; a paragraph broken between sentences with no new paragraph is unfinished; a complete entry followed by a newly numbered one is `new_entry`.                  |
| AC-015 / AC-024          | V1, V4                                                                                                                                                                                                                                                                                                                                                                                                    | Verified.                                                                                                                                                                                                                                  |
| AC-016                   | V1, V5                                                                                                                                                                                                                                                                                                                                                                                                    | Verified.                                                                                                                                                                                                                                  |
| AC-017                   | V1, V6                                                                                                                                                                                                                                                                                                                                                                                                    | Verified.                                                                                                                                                                                                                                  |
| AC-018                   | V1, V7; H1                                                                                                                                                                                                                                                                                                                                                                                                | Verified.                                                                                                                                                                                                                                  |
| AC-019                   | V3; inspection of `_RULES`                                                                                                                                                                                                                                                                                                                                                                                | Verified.                                                                                                                                                                                                                                  |
| AC-020                   | P1 `TV::test_rotated_pages_are_sent_upright_with_boxes_on_the_upright_grid`; P2 `TP::test_right_to_left_and_vertical_pages_state_their_direction_and_column_order`                                                                                                                                                                                                                                        | Verified.                                                                                                                                                                                                                                  |
| AC-021                   | V8 `TVA::test_page_files_that_break_their_own_rules_go_through_every_check_and_prompt`                                                                                                                                                                                                                                                                                                                    | Verified. Every check, the comparison inputs, the hint and the prompt run on page files that break their own rules.                                                                                                                        |
| AC-022                   | Inspection: grep of `src/pydelity/verifying/*.py` for regexes and for language, script, document-type and direction words                                                                                                                                                                                                                                                                                 | Verified. No regex, word list or document name in logic. The start-marker exceptions rest on the verdict's join and continuation markers only (`check_start_markers`).                                                                     |
| AC-023                   | A1 `TV::test_a_failed_check_is_sent_back_then_the_last_verdict_is_kept_for_review`; L1; A3'                                                                                                                                                                                                                                                                                                               | Verified.                                                                                                                                                                                                                                  |
| AC-055                   | V9 `TVA::test_a_piece_that_starts_with_a_start_marker_is_a_hint_difference_only`; V15–V18 `TVA::test_appended_rows_and_a_marked_start_are_no_start_marker_difference` (4 rows); F2+P3                                                                                                                                                                                                                     | Verified. Hints reach the model under the hints heading. A start marker at a piece's start is a difference, except for `append_rows` and a marker the verdict names on the start item or start row; a marker on another row still differs. |
| AC-056                   | V9 (retry message holds no hint; issues with a matching and a differing verification); F5'/F7' `TV::test_the_verifier_judges_the_break_again_unseen_and_lists_each_difference` (`agrees`, `differs`); A2                                                                                                                                                                                                  | Verified. The hint difference is never sent back, is listed unless the verifier's judgment matched, and stays in the verdict file either way.                                                                                              |
| AC-027                   | R1                                                                                                                                                                                                                                                                                                                                                                                                        | Verified. No verifier request or ledger line; `verification` is `null`.                                                                                                                                                                    |
| AC-028                   | CFG2 (2 rows); U12; U13; inspection of `--verify` help                                                                                                                                                                                                                                                                                                                                                    | Verified.                                                                                                                                                                                                                                  |
| AC-057                   | F5', F7' (verifier request body equals the judge's; ledger judge then verifier); A3' `TV::test_a_verifier_verdict_that_fails_a_check_is_sent_back_then_compared_as_it_is`; U12                                                                                                                                                                                                                            | Verified. The second judgment is made unseen, checked, and sent back within `check_retries`.                                                                                                                                               |
| AC-058                   | C1–C6 (`TVA::test_verdicts_that_differ_only_in_what_is_not_compared_match`, `…only_one_verdict_continuing_is_the_one_difference`, `…pieces_pair_by_end_then_by_start_and_unpaired_pieces_come_first`, `…a_pair_with_the_same_join_differs_in_each_text_join_cell_and_header_row`, `…a_pair_with_different_joins_differs_in_the_join_alone`, `…cell_joins_of_another_length_are_one_difference`); F5', F7' | Verified. Uncompared fields and piece order do not count; each compared difference is one `verdicts_differ` issue naming it; the judge's verdict is kept; no third request.                                                                |
| AC-059                   | F5', F7', A3'                                                                                                                                                                                                                                                                                                                                                                                             | Verified. `verification` saves the verifier's verdict, attempts, checks and differences.                                                                                                                                                   |
| AC-031                   | A1; F7' (issue on item `p0000-001`, "pages 1 and 2: verdicts_differ: …"); H1                                                                                                                                                                                                                                                                                                                              | Verified.                                                                                                                                                                                                                                  |
| AC-032                   | U6; U12; F3', F9 and A3' (ledger agents)                                                                                                                                                                                                                                                                                                                                                                  | Verified.                                                                                                                                                                                                                                  |
| AC-033                   | U8 (with the verifier, 6 requests at most for one break); F3' (verifier only, 3); E1 within R3; R5 `TV::test_a_page_break_request_first_shows_the_estimate_and_a_no_stops_it_unsent`; U9                                                                                                                                                                                                                  | Verified.                                                                                                                                                                                                                                  |
| AC-034                   | R6 `TV::test_break_requests_sent_at_once_are_held_to_max_cost_together` (corrected, Execution Evidence 11)                                                                                                                                                                                                                                                                                                | Verified. Three concurrent requests stop with `BudgetExceededError`; the warning projects the spend so far plus $64 (one request in flight and the next). One at a time, no warning.                                                       |
| AC-035                   | U4; F1 `TV::test_extracting_one_page_again_judges_only_the_two_breaks_beside_it`; F2; one-off check (Execution Evidence 9)                                                                                                                                                                                                                                                                                | Verified. `overwrite`, the step model, `max_output_tokens` and `effort` each re-judge both breaks; only `overwrite` reruns earlier steps; a third run reuses. The one-off check is not kept in the suite.                                  |
| AC-060                   | F3' `TV::test_a_page_with_no_content_items_and_turning_on_the_step_s_verifier`; F9 `TV::test_a_refused_verifier_request_keeps_the_judge_s_verdict_for_the_next_run`; F1                                                                                                                                                                                                                                   | Verified. Turning the verifier on sends one verifier request per break and keeps the judge's verdict, checks and fingerprint; `no_content` breaks stay. Another step's output re-judges only through the break's inputs.                   |
| AC-037                   | F8 `TV::test_a_damaged_verdict_file_warns_and_its_break_is_judged_again`; L2                                                                                                                                                                                                                                                                                                                              | Verified.                                                                                                                                                                                                                                  |
| AC-038                   | L1; L2 `TV::test_a_failed_request_stops_the_run_and_the_next_run_judges_only_the_rest`; L3/L4 (one row each); F9                                                                                                                                                                                                                                                                                          | Verified. A refused verifier request raises `PageBreakError` naming the verifier; the judge's verdict is kept and the next run asks only the verifier.                                                                                     |
| AC-039                   | H1 `report/test_html.py::test_a_break_card_shows_its_pieces_beside_both_pages_with_links_from_issues`; H2; U10; F5', F7' (report lines)                                                                                                                                                                                                                                                                   | Verified. The card says "no verifier ran", "its verdict matches" or "its verdict differs in N place(s): …", escaped.                                                                                                                       |
| AC-040                   | The whole suite (Execution Evidence 2)                                                                                                                                                                                                                                                                                                                                                                    | Verified. All responses come from the stand-in.                                                                                                                                                                                            |
| AC-041                   | `.github/` unchanged from `main`; ruleset 27420482; local 3.14 run                                                                                                                                                                                                                                                                                                                                        | Verified.                                                                                                                                                                                                                                  |
| AC-042                   | Smoke script on macOS (Execution Evidence 7)                                                                                                                                                                                                                                                                                                                                                              | Partly verified: macOS passed. Linux and Windows pending CI.                                                                                                                                                                               |
| AC-043                   | Execution Evidence 6 and 7                                                                                                                                                                                                                                                                                                                                                                                | Verified.                                                                                                                                                                                                                                  |
| AC-044                   | `pyproject.toml` description and classifiers                                                                                                                                                                                                                                                                                                                                                              | The package text is verified. The README is pending Documenter: `README.md:18-20` and `:102` still describe a verifier that reviews and may correct, which no longer fits page breaks.                                                     |
| AC-045                   | Release files unchanged from `main` (manifest `0.2.0`)                                                                                                                                                                                                                                                                                                                                                    | Setup verified; release pending.                                                                                                                                                                                                           |
| AC-046                   | None at this phase                                                                                                                                                                                                                                                                                                                                                                                        | Pending Documenter.                                                                                                                                                                                                                        |
| AC-047                   | Regenerated reference pages (Execution Evidence 8)                                                                                                                                                                                                                                                                                                                                                        | Verified. All 13 pages match the code, including `repeat`, `verification.{attempts,checks,differences,verdict}`, `verdicts_differ` and the start-marker exceptions.                                                                        |
| AC-048                   | None at this phase                                                                                                                                                                                                                                                                                                                                                                                        | Pending Documenter.                                                                                                                                                                                                                        |
| AC-049                   | None at this phase                                                                                                                                                                                                                                                                                                                                                                                        | Pending Documenter.                                                                                                                                                                                                                        |
| AC-061                   | None at this phase                                                                                                                                                                                                                                                                                                                                                                                        | Pending the user's real runs.                                                                                                                                                                                                              |
| AC-062                   | None at this phase                                                                                                                                                                                                                                                                                                                                                                                        | Pending the user's real runs.                                                                                                                                                                                                              |

Superseded evidence: the earlier pass's evidence for the retired IDs is not
current coverage. `AC-025` (V9, F2+P3) is now `AC-055`; `AC-026` (V9, F5–F7) is
now `AC-056`; `AC-029` (F5–F7, A3) is now `AC-057` and `AC-058`; `AC-030` is now
`AC-059`; `AC-036` (F3) is now `AC-060`; `AC-050` and `AC-051` are now `AC-061`
and `AC-062`. The tests of F5, F6, F7, A3 and F3 were removed or replaced, as
listed under Resume or Handoff.

## Scenario Budget

Allocations carry over from the earlier pass. Replacements reuse their
allocation; F6 was removed with `AC-029` and its allocation stays used.

| Source file                   | Reused coverage                  | Active-change allocations (used)                              | User additions     |
| ----------------------------- | -------------------------------- | ------------------------------------------------------------- | ------------------ |
| `verifying/validators.py`     | none                             | V1–V18, C1–C6 (24)                                            | approved: up to 24 |
| `verifying/verification.py`   | U4                               | F1, F2, F3', F4, F5', F6 (removed), F7', F8, F9, L2, A3' (11) | approved: up to 11 |
| `pipeline/runner.py`          | U1–U13 where they record steps   | R1, R3, R4, R5, R6, R7, E1, A1, L1 (9)                        | approved: up to 9  |
| `verifying/prompts.py`        | none                             | P1, P2, P3, V8 (4)                                            | none               |
| `verifying/llm.py`            | none                             | P1, L1, L3, L4, F9 (5)                                        | none               |
| `verifying/agents.py`         | none                             | A1, A2, A3' (3)                                               | none               |
| `config/schemas.py`           | example-config completeness test | CFG1 (3 rows), CFG2 (2 rows) (5)                              | none               |
| `api.py`                      | none                             | API1, API2 (2)                                                | none               |
| `report/html.py`              | U10                              | H1, H2, F5' (3)                                               | none               |
| `cli.py`                      | U5, U7, U12                      | L1, R5 (2)                                                    | none               |
| `costs/budget.py`             | U8, U9                           | R6, E1, F3' (3)                                               | none               |
| `review.py`                   | none                             | F7' (1)                                                       | none               |
| `examples/config.{json,yaml}` | example-config completeness test | none                                                          | none               |

User additions: on 2026-11-22 the user approved up to 9 scenarios for
`verifying/validators.py`, 10 for `verifying/verification.py` and 9 for
`pipeline/runner.py`. On 2026-11-28 the user approved 15 more for
`verifying/validators.py` (V10–V18, C1–C6) and 1 more for
`verifying/verification.py` (F9), for those scenarios and no others.

Notes:

- `verifying/schemas.py` holds field definitions, which the scenarios charged to
  `validators.py` and `verification.py` exercise. It is not charged separately,
  as in the earlier pass.
- The prompt rules of `AC-052` to `AC-054` are verified by inspection and use no
  allocation.
- E1 is the earlier pass's C1 (the estimate includes the step when the run will
  judge breaks), renamed to keep C1–C6 for the comparison.
- F2 and P3 share one test; F3' and F4 share one test; V10 and V12 share one
  test; V11 and V13 share one test; F5' and F7' are the two rows of one test; A2
  is asserted in F5' and F7' (one judge request each, with a hint difference).
- Test-helper changes count toward no allowance: the stand-in's public
  `delay_seconds` attribute, `_break_agents` and `_break_requests` in `TV`,
  `_curriculum_pages` in `TVA`, and the `canned_answers` docstring.

Scenario plan:

- V1–V9 as in the earlier pass (V8 no longer runs a verifier review prompt; V9
  now compares a matching and a differing verification). V10 `new_entry` from a
  text item passes; V11 `new_entry` starting in a text item fails `joins`; V12 a
  `repeat` cell on a repeated row label passes; V13 `repeat` as a text join
  fails `joins`; V14 `repeat` cells with no text or other text fail `repeats`;
  V15 `append_rows`, V16 a marker on the start item and V17 a marker on the
  start row skip the start-marker difference; V18 a marker on another row does
  not.
- C1 verdicts differing only in uncompared fields and piece order match; C2 one
  verdict continuing is the one difference; C3 pieces pair by end, then start,
  and unpaired pieces come first; C4 a same-join pair differs per text join,
  cell join and header rows; C5 different joins differ only in the join; C6 cell
  joins of another length are one difference.
- F1, F2, F4, F8, L2 as in the earlier pass. F3' turning the step's verifier on
  over existing verdicts sends only verifier requests and keeps the judge's
  verdict; F5' the verifier's judgment agrees; F7' it differs and each
  difference is listed; F9 a refused verifier request keeps the judge's verdict
  file and the next run asks only the verifier; A3' a verifier verdict failing a
  check is sent back, then compared as it is.
- R1, R3–R7, E1, A1, A2, L1, L3, L4, P1–P3, CFG1, CFG2, API1, API2, H1, H2 as in
  the earlier pass.

## Execution Evidence

All commands ran from the repo root on `bc56b21` with the Tester changes above,
on 2026-11-28.

1. Baseline:
   `.venv/bin/python -m pytest -q --numprocesses auto -p no:cacheprovider` gave
   214 passed, 25 failed and 1 error (`TVA` no longer imported), which matches
   the plan's handoff claim. Developer self-checks are not formal evidence.
2. Final run on Python 3.13.9, same command: 261 passed, 0 failed. The 70
   warnings are PyMuPDF's SWIG `DeprecationWarning`s and expected
   `missing_page_files` warnings from tests that narrow `pages` (AC-003). The
   suite also passed 12 of 12 repeated runs before the R6 correction.
3. Python 3.14.10, with `UV_CACHE_DIR`, `UV_PROJECT_ENVIRONMENT` and
   `UV_PYTHON_INSTALL_DIR` under `$TMPDIR`:
   `uv run --python 3.14 --locked pytest -q --numprocesses auto -p no:cacheprovider`
   gave 261 passed; doctests gave 40 passed, 1 skipped. The cached 3.14 install
   had lost files to `/tmp` cleanup and was reinstalled first.
4. Python 3.13.9 doctests:
   `.venv/bin/python -m pytest -q --doctest-modules src -p no:cacheprovider`
   gave 40 passed, 1 skipped (an existing `+SKIP` example).
5. Lint, types and docstrings all passed: `ruff check scripts src tests`,
   `ruff format --check scripts src tests` (101 files),
   `ty check scripts src tests` (the 9 diagnostics DEV-015 listed are gone),
   `interrogate scripts src tests` (100%).
6. Build: `uv build --out-dir "$TMPDIR/dist"`, then `twine check --strict` on
   the wheel and sdist: both passed. The version string is `0.2.0` from the
   manifest; release-please sets `0.3.0` after merge.
7. Wheel smoke test on macOS arm64:
   `.venv/bin/python scripts/smoke_installed_wheel.py --wheel $TMPDIR/dist/pydelity-0.2.0-py3-none-any.whl`
   passed 13 of 13 checks (run outside the sandbox, where pip's TLS check
   works). Both providers ran the survey, page extraction and page-break
   verification against the stand-in through the command and the Python API.
8. Reference pages: `scripts/generate_reference_docs.py` (it takes no options,
   so it wrote into `docs/` in place), then the hook's pinned prettier 3.10.1
   through `prek exec prettier-markdown -- prettier --write` on the 13 pages.
   `git status docs` was clean afterwards: every page is byte-identical to the
   committed one.
9. One-off check of the `overwrite`, step-model, `max_output_tokens` and
   `effort` changes (AC-035): a temporary 4-row test in
   `tests/pydelity/verifying/` passed 4 of 4 and was removed. Its source is at
   `/private/tmp/claude-501/-Users-tzz--claude-spares-spare-PIwSYx/9b29212a-1bd2-43ce-8363-e8001fcf9fe9/scratchpad/test_scratch_rejudge.py`.
   It is execution evidence, not regression coverage.
10. CI and release setup:
    `git diff main --stat -- .github release-please-config.json .release-please-manifest.json`
    is empty. `gh api repos/{owner}/{repo}/rulesets/27420482`: active on the
    default branch, requiring "Lint and test" and "TruffleHog secret scan".
11. R6 flakiness (reported by DEV-013):
    - Reproduced with a stress script that runs the test while 24 busy-loop
      processes load 12 cores: 1 failure in 20. The warning still fired and the
      run still stopped, but the projection was $0.60 higher: the first request
      had already finished, so its real cost was in the ledger and its hold was
      released. That is the guard's contract. The test assumed the next check
      comes within the stand-in's 0.3 s delay, and page-image work under load
      can take longer.
    - Correction (test-owned): the stand-in's `delay_seconds` is now a public
      attribute. The test holds break requests for 1.0 s during the concurrent
      run only, and reads the spend from the warning's own "already spent"
      figure. The test takes 1.5 s.
    - After: 40 of 40 under the same load. Negative control: a scratch pytest
      plugin that drops the guard's in-flight hold makes the test fail with "DID
      NOT WARN".
12. Test validity: paired rows show each assertion can fail. C1 against C2–C6,
    V15–V17 against V18, F5' against F7', V10/V12 against V11/V13, F3' (3
    requests at most) against U8 (6), and F9's ledger assertion, which fails if
    the judge is asked again.
13. `node .standards/bin/check.mjs`: no problems (run before handoff).

Limits:

- No real provider was called.
- The Linux and Windows wheel runs are not local.
- The judge's and verifier's accuracy on real documents is for `AC-061` and
  `AC-062`.

## Open Findings and Dependencies

No implementation, upstream or verification defect is open, and no blocking user
question is pending. The R6 flake was a test timing assumption, corrected and
verified above.

Later-role dependencies, each resolved under the same AC ID:

| AC     | Owner                                                     | Evidence still required                                                                                                                                                 |
| ------ | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AC-042 | The user pushes the branch, and CI checks it before merge | `Wheel install (ubuntu-latest)` and `Wheel install (windows-latest)` pass on this branch's pull request.                                                                |
| AC-044 | Documenter                                                | The README describes the page-break verifier's second judgment (`README.md:18-20`, `:102`).                                                                             |
| AC-045 | Release after sign-off and merge                          | release-please opens the 0.3.0 pull request (tag `v0.3.0`), and accepting it starts the PyPI and docs publication.                                                      |
| AC-046 | Documenter                                                | The guides describe the second judgment and its differences. DEV-015 names `guides/command-line.md`, `guides/python.md`, `guides/outputs.md` and `guides/verifiers.md`. |
| AC-047 | Documenter                                                | Only if the docs change the code: regenerate the pages and keep them matching.                                                                                          |
| AC-048 | Documenter                                                | The README quick start and all command and code examples match 0.3.0.                                                                                                   |
| AC-049 | Documenter                                                | `artifacts/next_cycle_inputs.md` "Pushed to later steps" is current.                                                                                                    |
| AC-061 | User                                                      | Real runs with default settings on the named PDF kinds are accepted.                                                                                                    |
| AC-062 | User                                                      | Real runs with the verifier on are accepted.                                                                                                                            |

## Resume or Handoff

Testing is complete. Hand off to Reviewer, review kind `IMPLEMENTATION`.

Tests changed in this pass (paths under `tests/pydelity/`):

- Replaced: A3 by A3'; F3 by F3' (with F4); F5 by F5' and F7 by F7' (one
  parametrized test); F6 removed.
- Added: V10–V18, C1–C6 in `TVA`; F9 in `TV`.
- Updated under existing allocations: V8, V9; H1 (a verifier verdict that
  differs in its header rows), H2; U5 and U12 in `test_cli.py`; U10; R6 (timing
  correction).
- Mechanical updates for the stand-in's break answers by earlier page (a list
  serves the judge, then the verifier): L2's error text, the refusal and
  unusable-answer request counts, the rotated-page test, API1 and F2+P3's ledger
  agents.
- `tests/conftest.py`: the `canned_answers` docstring.
- `tests/fixtures/mock_providers.py`: `delay_seconds` is a public attribute.

The earlier pass's U1–U13 (tests of replaced contracts from DEV-008) remain as
recorded there and all pass.

For the independent Reviewer:

- Inputs: the scope, design, plan and context above; `main..HEAD` at `bc56b21`;
  and the uncommitted Tester changes under Assessed Inputs.
- Re-run Execution Evidence 2, 4 and 5.
- The evidence that matters most: the R6 correction (Execution Evidence 11), the
  AC-035 one-off check, the inspections for AC-022 and AC-054, the 2026-11-28
  budget increase, and the later-role dependencies above, which must be resolved
  under their IDs before sign-off.

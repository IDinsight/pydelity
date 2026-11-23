<!-- STANDARDS
Artifact: REVIEW
Cycle: build-step-3-page-break-verification-of-20261122T170208Z-00fe2896
ReviewKind: IMPLEMENTATION
-->

# Review Report

`Cycle`: `build-step-3-page-break-verification-of-20261122T170208Z-00fe2896`
`ReviewKind`: `IMPLEMENTATION` `Status`: `COMPLETE` `User Style`: `tony`

## Assessed Inputs and Scope

- Cycle mode `STANDARD`, completion policy `FULL_DELIVERABLE`, project mode
  `BROWNFIELD`. The current acceptance set is `AC-001` to `AC-051`; the scope
  retires none. The design's technical acceptance criteria use the same IDs.
- Records, by the first 16 hex digits of their SHA-256. Each one matches what
  Tester assessed:
  - scope `c0f8b54a9851b32c`
  - design `e9006fbf2a78ee99`
  - plan `01434a6d99513f03` (`COMPLETE`, `AFTER_IMPLEMENTATION`,
    `Current Increment: NONE`, DEV-001 to DEV-011 `DONE`)
  - context `0e940ffe605aecff`
  - verification report `41861e7f5baec0a1` (`COMPLETE`, `FULL`, `NONE`)
- Change: `main...HEAD` on `tz6/pipeline-step-3`, merge base `7dc2cba` (0.2.0),
  HEAD `8201e2e`. The working tree is clean.
  - Tester's commit `8201e2e` changes only tests and STANDARDS records.
  - So `src/`, `scripts/`, `examples/`, the generated reference pages and
    `pyproject.toml` are the same as at `68b675c`, where Tester built the wheel
    and regenerated the pages.
  - `.github/`, `release-please-config.json` and `.release-please-manifest.json`
    are unchanged from `main`.
- Source read in full or in the changed parts:
  - `verifying/verification.py`, `verifying/llm.py`, `verifying/agents.py`
  - the rules and page text of `verifying/prompts.py`
  - `verifying/schemas.py` (verifier invariants)
  - the run flow, estimate placement, pause, `load_run`, `_review` and `_record`
    in `pipeline/runner.py`
  - `costs/budget.py` (`estimate_page_breaks`), `costs/schemas.py`
  - `config/schemas.py` (`PageBreaksConfig`, `page_breaks_model`,
    `verify_page_breaks`)
  - `api.py`, `cli.py`, `errors.py`, `review.py`
  - `report/html.py` (break cards, review rows, escaping)
  - `report/images.py` `render_pages` (every page is rendered)
  - the spend bound in `providers/ledger_model.py`
  - page extraction's `_reusable_page`, which "current" relies on
- `verifying/validators.py` was read by an independent subagent briefed with the
  design, not with this review's conclusions. It checked every check against the
  design and fuzzed about 64,000 verdicts on loadable but inconsistent page
  files. Reviewer then read the parts its report relied on (`check_duplicates`,
  `_repeat_problems`, `_repeat_matches`, `_printed_forms`).
- Tests read: the scenario list in the verification report, and R6 and F5–F7 in
  `tests/pydelity/verifying/test_verification.py` to see what they assert.
- Project references: `NONE` (`.standards/project-references/` does not exist).
- Session: this Reviewer conversation holds no authoring history. The client
  gives no session or model metadata, so freshness and the authoring models are
  not known.
- Excluded: the docs-site guides, the README and
  `artifacts/next_cycle_inputs.md` (Documenter's, later), and real model runs
  (the user's).

## Contract and Evidence Assessment

Tester evidence is in the verification report. Reviewer diagnostics are under
**Checks and Results**. "Supported" means the implementation does what the AC
asks and the evidence shows it.

| Obligation             | Assessed evidence                                                                                                                                                                                                                                                                  | Current disposition                                                                                   |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| AC-001                 | R1, U5. `_steps` runs the survey, extraction and `_page_breaks` for both the CLI and `run()`.                                                                                                                                                                                      | Supported                                                                                             |
| AC-002                 | `current_pages` takes pages extracted this run plus `plan_pages(quiet=True)` `saved`. `_reusable_page` checks the fingerprint, `overwrite` and the verifier. R3, API2, U7.                                                                                                         | Supported                                                                                             |
| AC-003                 | `_current_page_files` gives the `missing_page_files` warning and the step is `skipped` with the run `completed`. U7, API2, R3.                                                                                                                                                     | Supported                                                                                             |
| AC-004                 | One-page branch in `_current_page_files` and `_breaks_estimate`. R4.                                                                                                                                                                                                               | Supported                                                                                             |
| AC-005                 | `_steps` sets `pause=pause and new_pages`. `_log_pause` picks the last step that was not skipped. R1, U5, U6, U11.                                                                                                                                                                 | Supported                                                                                             |
| AC-006                 | `run_page_breaks_step` calls `_steps(pause=False)`. `verify_breaks`/`averify_breaks` go through `run_sync`. API1, API2.                                                                                                                                                            | Supported                                                                                             |
| AC-007                 | `_load_breaks` matches the PDF hash and both page-file byte hashes and sorts by break. R7, U4.                                                                                                                                                                                     | Supported                                                                                             |
| AC-008                 | `Config.page_breaks_model` resolves the step setting, then `model`, then `DEFAULT_PAGE_BREAKS_MODEL`. Effort defaults to `high`. CFG1.                                                                                                                                             | Supported                                                                                             |
| AC-009                 | `_with_user_instructions` puts the step's instructions last in both system messages. Page texts hold no `inputs`. No CLI option. F2+P3.                                                                                                                                            | Supported                                                                                             |
| AC-010                 | Example-config completeness test.                                                                                                                                                                                                                                                  | Supported                                                                                             |
| AC-011, AC-012         | `BreakFile`, `ContinuingPiece`, `_break_file_name`. F1, V1, V7.                                                                                                                                                                                                                    | Supported                                                                                             |
| AC-013, AC-014         | `joins` check, confirmed by the subagent for every join, bound, `newline` rule and `cell_joins` length. V1, V2.                                                                                                                                                                    | Supported. See limitation L3 for a list case the `duplicates` rule cannot express.                    |
| AC-015, AC-024         | `header_rows` check (ordered, distinct rows among the first n + h). V1, V4.                                                                                                                                                                                                        | Supported. The design's Risks section accepts the Dice-only matching (L4).                            |
| AC-016                 | `repeated_items` field, `ids` and `repeats`. V1, V5.                                                                                                                                                                                                                               | Supported. `repeats` is looser than its purpose suggests (L1, L2).                                    |
| AC-017                 | `markers` field and check. V1, V6.                                                                                                                                                                                                                                                 | Supported                                                                                             |
| AC-018                 | `containers` apart from `pieces`. V1, V7, H1.                                                                                                                                                                                                                                      | Supported                                                                                             |
| AC-019                 | `furniture` check and the furniture rule in `_RULES`. V3.                                                                                                                                                                                                                          | Supported                                                                                             |
| AC-020                 | `page_image(rotation=page.rotation)`, `points_box_to_grid` with the page's rotation, and the reading-order rule. P1, P2.                                                                                                                                                           | Supported                                                                                             |
| AC-021                 | Fuzzing found no exception in checks, hints, retry messages or issues. V8. The step reads only the continuation notes and start markers from the profile.                                                                                                                          | Supported                                                                                             |
| AC-022                 | Grep of `verifying/*.py`: the only direction text is a statement chosen from each page's own value. No word list, no regex, no document type.                                                                                                                                      | Supported                                                                                             |
| AC-023                 | The judge's output validator retries only on `run_checks` failures and keeps the last verdict at `last_attempt`. A1, L1.                                                                                                                                                           | Supported                                                                                             |
| AC-025, AC-026         | The hints sit under their own heading. `compare_with_hints` is used only for the verifier's content and the verdict file. Retry messages come from `run_checks` only (confirmed by the subagent). V9, A2.                                                                          | Supported                                                                                             |
| AC-027                 | `verification=None` when the verifier is off. R1.                                                                                                                                                                                                                                  | Supported                                                                                             |
| AC-028                 | `verify_page_breaks` and `PageBreaksConfig.verify`. CFG2, U12, U13.                                                                                                                                                                                                                | Supported                                                                                             |
| AC-029, AC-030         | `_kept_verdict` keeps a correction only with no check failure and records `correction_failures` otherwise. The verifier's invariants match page extraction's. F5–F7, A3.                                                                                                           | Supported                                                                                             |
| AC-031                 | `review_issues`, `_issue_place`, `_review`. A1, F5–F7, H1.                                                                                                                                                                                                                         | Supported                                                                                             |
| AC-032                 | `for_page(agent=..., page_index=earlier)`. `_cost` sums by step. U6, U12.                                                                                                                                                                                                          | Supported                                                                                             |
| AC-033                 | One estimate per run: in the survey, else in extraction, else in `_judge_breaks`. `_breaks_estimate` leaves the step out when the run will not reach it. U8, C1, R5, U9.                                                                                                           | Supported                                                                                             |
| AC-034                 | `LedgerModel` reserves each request's bound, two images included, in the run's `SpendGuard`. R6 asserts a held request and a projection of the spend plus $64.                                                                                                                     | Supported                                                                                             |
| AC-035                 | `BreakInputs` covers both page-file byte hashes, the hints, the instructions, the model, `check_retries`, `effort`, `max_output_tokens`, the prompt version and the rendering. `overwrite` is in `_reusable_break`. U4, F1, F2, and Tester's one-off check (Execution Evidence 9). | Supported. The one-off check is execution evidence, backed here by reading the fingerprint.           |
| AC-036                 | `_reusable_break` re-judges unreviewed `model` verdicts once the verifier is on. Other steps reach a break only through page bytes or survey fields. F3.                                                                                                                           | Supported                                                                                             |
| AC-037                 | `write_model_atomic`, `remove_stale_temp_files`, `_saved_break` with `damaged_output`. F8.                                                                                                                                                                                         | Supported                                                                                             |
| AC-038                 | `_run` maps refusals, used-up output tokens and unusable answers to `PageBreakError`. The task group cancels the rest and raises the first error. The CLI catches `PydelityError`. L1–L4.                                                                                          | Supported                                                                                             |
| AC-039                 | `_breaks_section` and `_break_card` (both images, boxes, every verdict field, verifier outcome, escaping through `_definitions` and `_list`). `_review_row` links to `#break-NNNN`. `render_pages` renders every page. H1, H2, U10.                                                | Supported                                                                                             |
| AC-040                 | The whole suite, 248 tests, run by Reviewer.                                                                                                                                                                                                                                       | Supported                                                                                             |
| AC-041                 | CI workflows unchanged. Tester read the ruleset. Python 3.14 run by Tester.                                                                                                                                                                                                        | Supported                                                                                             |
| AC-042                 | macOS smoke run (Tester). Linux and Windows are not run.                                                                                                                                                                                                                           | Permitted later dependency (below)                                                                    |
| AC-043                 | Tester's build and `twine check --strict`. The packaging inputs are unchanged since then.                                                                                                                                                                                          | Supported                                                                                             |
| AC-044                 | The `pyproject.toml` description names the three steps and the verifiers. The README still says two steps.                                                                                                                                                                         | Package text supported. README is a permitted later dependency.                                       |
| AC-045                 | Release config and the `0.2.0` manifest are unchanged. The scope limits in-cycle evidence to release readiness.                                                                                                                                                                    | Readiness supported. The non-breaking `feat:` squash title is the user's merge action after sign-off. |
| AC-046, AC-048, AC-049 | None yet.                                                                                                                                                                                                                                                                          | Permitted later dependency (Documenter)                                                               |
| AC-047                 | Tester regenerated all 13 reference pages, byte-identical. Source and scripts are unchanged since.                                                                                                                                                                                 | Supported in code. Documenter regenerates only if the docs change the code.                           |
| AC-050, AC-051         | None yet.                                                                                                                                                                                                                                                                          | Permitted later dependency (the user's real runs)                                                     |

## Checks and Results

All commands ran from the repo root on HEAD `8201e2e` with a clean tree, macOS
arm64, Python 3.13.9 in `.venv`, on 2026-11-22.

- `.venv/bin/python -m pytest -q --numprocesses auto -p no:cacheprovider`: 248
  passed, exit 0. The 70 warnings are the ones the verification report explains.
  This repeats Tester's Execution Evidence 2.
- `.venv/bin/ruff check scripts src tests`,
  `.venv/bin/ruff format --check scripts src tests`,
  `.venv/bin/ty check scripts src tests` and
  `.venv/bin/interrogate scripts src tests`: all passed. The tree stayed clean.
- `.venv/bin/python -m pytest -q --doctest-modules src -p no:cacheprovider`: 37
  passed, 1 skipped.
- `BreakVerdict` and `BreakVerifierVerdict` through PydanticAI's
  `OpenAIJsonSchemaTransformer(strict=True)`: both strict-compatible. Native
  output on OpenAI can therefore take them.
- Greps of the changed shipped files: no compatibility code, and no DEV/AC IDs,
  KGForEdGlobal, step numbers, STANDARDS or dates.
- Greps of `verifying/*.py`: no language, script or document-type word lists or
  regexes.
- `gh pr list --head tz6/pipeline-step-3` and the check runs for `8201e2e`, run
  outside the sandbox because gh's TLS check fails inside it: no pull request
  and no check runs. So no Linux or Windows evidence exists yet for AC-042.
- Subagent results on `verifying/validators.py`: every check matched the design.
  About 64,000 fuzzed verdicts on inconsistent page files raised nothing. The
  existing validator tests passed.
- `node .standards/bin/check.mjs`: passed.
- Reused without rerunning:
  - Tester's Python 3.14 run, wheel build, `twine check` and macOS wheel smoke
    test.
  - Tester's regeneration of the reference pages.
  - These still apply because `8201e2e` changes neither the source nor the
    packaging, scripts or docs inputs.

## Findings

No material findings.

## Questions, Limitations, and Later Dependencies

Limitations (not findings). Each matches the design as written. None makes a
verdict wrong unless the model has already erred. None fails a run or loses
money beyond a few retries. Under this cycle's major-issues-only bar they do not
block this gate. Real runs (AC-050, AC-051) are the place to see whether any of
them matters in practice.

- **L1 — `repeats` accepts containment of any length** (`validators.py`
  `_repeat_matches`, `_printed_forms`).
  - Page N's texts include page furniture such as a page number.
  - So a wrongly named repeated item passes when it contains the page number, as
    "Chapter 5 Methods" contains "5".
  - It also passes when its text is a word printed anywhere on page N.
  - The design's Risks section accepts the second case only.
  - If the judge misnames an item, the check does not catch it, and assembly
    would drop that item with no review line when no verifier runs.
- **L2 — `repeats` skips items with no text** (`_repeat_problems`). A table or
  list named as repeated is never compared. The design says "whose text is not
  empty", so this is as designed.
- **L3 — `duplicates` is per item** (`check_duplicates`).
  - The case: page N's last list entry carries on as a text item, and the list
    then goes on as a separate list item on page N+1.
  - It needs two pieces ending in the same list item, so the correct verdict
    fails `duplicates`.
  - After the retries, either it is kept and listed for review, or the model
    drops a piece and the list stays split.
  - No content is lost.
- **L4 — `header_rows` uses only text similarity.** A repeated header row with a
  continuation word inside a short cell can score below 0.8 and fail a correct
  count. The design's Risks section accepts this, and real runs test it.
- **L5 — a symbol-only marker such as "→" always passes `markers`**, because its
  comparison form is empty. No harm to output was shown.

Later dependencies, each still needing evidence under its own ID before final
review can pass:

| AC                     | Owner                                           | Evidence still required                                                                                                       |
| ---------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| AC-042                 | User (push the branch), checked at final review | `Wheel install (ubuntu-latest)` and `Wheel install (windows-latest)` pass for the reviewed HEAD on the branch's pull request. |
| AC-044                 | Documenter                                      | The README describes the three steps and the optional verifier for each.                                                      |
| AC-046, AC-048, AC-049 | Documenter                                      | As the verification report lists.                                                                                             |
| AC-047                 | Documenter                                      | Regenerated pages that still match, if the docs work changes the code.                                                        |
| AC-050, AC-051         | User                                            | Accepted real runs with the verifier off and on.                                                                              |

No blocking user question is open. `Active Work.BlockedOn` is `NONE`.

## Progress and Conclusion

- Done: the inputs were reconciled with what Tester assessed, and none changed.
  The implementation was read against every AC and the design's technical
  criteria. The suite and static checks were rerun. The validators were checked
  by an independent read with fuzzing.
- The gate passes:
  - no material finding or assessment gap is open;
  - every current AC is supported or has a permitted later dependency with its
    owner and the evidence needed;
  - `check` passes;
  - recovery is inactive.
- Inputs were rechecked against the hashes and HEAD above just before marking
  this report `COMPLETE`.
- Next: Documenter (`DOCUMENTING`), then final review. Final review must find
  the Linux and Windows wheel CI results for AC-042 and resolve every later
  dependency above.

Plain-language summary: the page-break code can move on to documentation.
Nothing needs fixing before then. It does what the scope asks, and the tests,
lint and type checks pass. Five weak spots in the code's safety checks are
written down above. They only matter when the model has already made a mistake,
and the real runs will show whether they matter. Still unchecked: the wheel on
Linux and Windows (CI runs it when you push the branch), the README and guides
(Documenter), and real model runs (you).

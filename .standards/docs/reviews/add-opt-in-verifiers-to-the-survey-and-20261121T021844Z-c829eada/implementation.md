<!-- STANDARDS
Artifact: REVIEW
Cycle: add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada
ReviewKind: IMPLEMENTATION
-->

# Review Report

`Cycle`: `add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada`
`ReviewKind`: `IMPLEMENTATION` `Status`: `COMPLETE` `User Style`: `tony`

## Assessed Inputs and Scope

- Cycle mode `STANDARD`, completion policy `FULL_DELIVERABLE`, project mode
  `BROWNFIELD`. Current acceptance set: `AC-001` to `AC-042`, none retired.
- Contract, by last commit and SHA-256 prefix:
  - scope
    `.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`49448e5`, `dd6ea5291602d518`);
  - design
    `.standards/docs/specs/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`81d7dcd`, `3c0eddfeb9d136e8`), decisions 1–13 and the technical acceptance
    criteria;
  - development plan
    `.standards/docs/development/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`b579737`, `4251351f9aef7154`; `COMPLETE`, `DEV-001` to `DEV-011` `DONE`,
    plan revision 1);
  - verification report
    `.standards/docs/verification/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`fc6df7d`, `2aceaad01ae2660c`; `COMPLETE`, `FULL`, target `NONE`);
  - project context `.standards/CONTEXT.md` (`0573e11`, `09045f457b2df4c1`);
    user style `.standards/user-styles/reviewer/tony.md` (`797def3`,
    `43b3830a5152e51d`).
- Repository: branch `tz6/pipeline-step-2` at `fc6df7d`, clean apart from this
  report. Baseline `126f52f`, the commit before the reorder (the design's and
  Tester's baseline).
  `git diff 126f52f fc6df7d -- src scripts examples docs pyproject.toml` SHA-256
  `3f8330e0d4f507b5` (45 files), the same as Tester assessed on `b579737`;
  nothing under those paths changed after `b579737`. Tests:
  `git diff 126f52f fc6df7d -- tests`, 17 files, SHA-256 `fa53c88508ee6a3f`. The
  feature work was read as `git diff 4a6bec7 fc6df7d` (after the reorder and its
  verification), the reorder as `126f52f..0f4c949` (package and scripts) and
  `126f52f..7bd7f90` (tests). `.github/`, `release-please-config.json` and
  `.release-please-manifest.json` are unchanged since `126f52f`.
- Areas read in full or by diff: settings and CLI (`config/schemas.py`,
  `cli.py`, both example files); the survey's verifier (`surveying/schemas.py`,
  `prompts.py`, `agents.py`, `llm.py`, `survey.py`); page extraction
  (`extracting/extraction.py`, `llm.py`, `schemas.py`, `prompts.py`,
  `text_layer.py`, `__init__.py`); costs and ledger (`costs/budget.py`,
  `costs/schemas.py`, `providers/ledger_model.py`); runner, API and report
  (`pipeline/runner.py`, `pipeline/schemas.py`, `api.py`, `report/html.py`,
  `review.py`); the fixes (`surveying/probe.py`, `utils/pdf.py`); the smoke
  script, the reference page generator and `pyproject.toml`. Tests sampled:
  `tests/pydelity/surveying/test_survey.py` (the verdict, reuse and failure
  tests) and the fixtures in `tests/conftest.py`. The docs guides, README and
  FAQ were not reviewed: they are Documenter's in this cycle.
- Environment: macOS arm64, Python 3.13.9 (`.venv`, editable install), PyMuPDF
  2.1. Python 3.14 is not installed locally; CI covers it.
- Project references loaded: `NONE` (`.standards/project-references/reviewer/`
  does not exist).
- Session: a new conversation that started with this review and holds no
  authoring history. The client cannot certify freshness, and the models that
  produced the work are not recorded, so whether this review ran on a different
  model is unknown.

## Contract and Evidence Assessment

| Obligation / criterion                                                                  | Assessed evidence                                                                                                                        | Current disposition                                                                                                                                   |
| --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AC-001` / defaults off, no `verifier` request or ledger line                           | `Config.verify_survey`, `verify_extraction`; `run_survey`, `_extract_page`; verification E22–E26; R2                                     | Supported. Both properties are false by default and each step asks its verifier only when its property is set.                                        |
| `AC-002` / one global switch in file, CLI (`--verify`/`-vf`) and Python                 | `Config.verify`, `cli.py` option passing `verify=True`; E13–E15, E23–E25                                                                 | Supported.                                                                                                                                            |
| `AC-003` / per-step overrides under `advanced:`                                         | `SurveyConfig.verify`, `ExtractionConfig.verify`, resolved properties; E13–E15; R3                                                       | Supported. R3 confirms the global switch with `advanced.survey.verify: false` reviews pages only.                                                     |
| `AC-004` / example files hold the settings and load                                     | `examples/config.json`, `config.yaml`; completeness test (E14, E23)                                                                      | Supported.                                                                                                                                            |
| `AC-005` / estimates include a verifier exactly when it runs                            | `estimate_survey`, `estimate_extraction`, `_prompt_chars`, `_log_estimate`, `run_estimate`; E23–E25 (hand-worked figures, mutations)     | Supported. The formulas match decision 9; `StepEstimate.verifier` is false for reused steps.                                                          |
| `AC-006` / turning a verifier on reruns unreviewed outputs only; no fingerprint change  | `saved_survey`, `_reusable_page`; `SurveySettings` and page inputs hold no switch; E13–E15, E23–E25                                      | Supported.                                                                                                                                            |
| `AC-007` / verifier request after acceptance, with failures and differences             | `ask_verifier`, `verify_survey`; E23–E25, E27 (survey prompt byte for byte unchanged)                                                    | Supported. The verifier gets the survey's rules and the user's instructions last; no prompt names a document type.                                    |
| `AC-008` / correction of any part, user languages first, facts unchanged                | `_kept_answer` then `build_survey`; E23–E25                                                                                              | Supported.                                                                                                                                            |
| `AC-009` / failing correction sent back within retries, kept only if every check passes | `create_verifier_agent` output validator, `_kept_answer`; E23–E25                                                                        | Supported.                                                                                                                                            |
| `AC-010`, `AC-011` / kept answer and review list per outcome                            | `build_survey` issue order (failures, differences unless accepted, problems when not applied); E23–E25; R2 (problems with no correction) | Supported. R2 covers the no-correction outcome that Tester's suite runs only through the shared not-kept branch.                                      |
| `AC-012` / PDF transport, recorded upload reused                                        | `ask_verifier` passes `surveyed.attachment` to `_run_with_upload`; E23–E25, E31                                                          | Supported. The 404 replacement path is shared with the survey request and tested there (see limitations).                                             |
| `AC-013` / `pdf_survey.json` saves the verdict or `null`                                | `PdfSurvey.verification` (required), `SurveyVerification`; E23–E25                                                                       | Supported.                                                                                                                                            |
| `AC-014` / report shows the survey verifier outcome                                     | `_profile_section`, `_verifier_text`; E23–E25; R2                                                                                        | Supported.                                                                                                                                            |
| `AC-015` / ledger lines `surveyor` and `verifier`; survey cost includes both            | `LedgerModel.for_agent`, required `LedgerEntry.agent`, `_agent()` guard before sending; E23–E25; R2                                      | Supported.                                                                                                                                            |
| `AC-016` / spend control covers verifier requests                                       | plan-time estimate with the verifier; `for_agent` keeps the step's PDF in the reservation bound; E23–E25                                 | Supported.                                                                                                                                            |
| `AC-017` / failed verifier request stops the run, no new survey written                 | `_run_agent` error mapping; `run_survey` writes only after the verdict is applied; E23–E25                                               | Supported.                                                                                                                                            |
| `AC-018`, `AC-019`, `AC-020` / page extraction without its verifier                     | `_extract_page`, `_kept_answer`, `_page_issues`, `_verifier_outcome`, `_verifier_text`, nullable `PageFile.verification`; E12–E21, E23   | Supported. With the verifier on, the text-difference rule is unchanged from 0.2.0.                                                                    |
| `AC-021` / `load()` leaves out other PDFs' page files                                   | `_load_pages(sha256=...)`, hash compared before the crop check; E32–E34                                                                  | Supported.                                                                                                                                            |
| `AC-022` / spanning header cells keep body cells in their columns                       | `_item_table` writes one `tbody` with `th` header cells; E32–E34                                                                         | Supported.                                                                                                                                            |
| `AC-023` / dangling outline links give every reachable bookmark                         | `_cut_broken_outline_links` nulls links outside `1..xref_length()-1`, still cuts cycles; E39–E42                                         | Supported under the corrected design (`81d7dcd`).                                                                                                     |
| `AC-024` / inline widget keeps the other fields                                         | `_form` skips object 0 with one `form` probe error; `_field_error` reads no key of object 0; E32–E34                                     | Supported.                                                                                                                                            |
| `AC-025` / `TEXT_FLAGS` comment names the CropBox                                       | `src/pydelity/utils/pdf.py`                                                                                                              | Supported by inspection.                                                                                                                              |
| `AC-026` / mocked tests cover items 2–5                                                 | 207 tests (R1); Tester's mutation runs E15, E25, E34, E42; sampled tests read                                                            | Supported. Every case the AC lists has a passing test whose assertions observe the outcome.                                                           |
| `AC-027` / CI on 3.13 and 3.14; required checks gate `main`                             | R4 (CI on `fc6df7d`), R5 (`main`'s rules)                                                                                                | Supported.                                                                                                                                            |
| `AC-028` / wheel installs and runs on Linux, macOS, Windows                             | R4 ("Wheel install" on three runners); smoke script expects default settings                                                             | Supported.                                                                                                                                            |
| `AC-029` / wheel and sdist install and pass metadata checks                             | E44, R4                                                                                                                                  | Supported.                                                                                                                                            |
| `AC-030` / package description, classifiers and README                                  | `pyproject.toml` description; E44                                                                                                        | Package part supported. README part is a permitted later dependency (Documenter).                                                                     |
| `AC-031` / release setup produces 0.2.0                                                 | Manifest `0.1.1`, release files unchanged since `126f52f` (R5); E45                                                                      | Supported for release readiness, which the scope says in-cycle evidence covers; the release pull request itself follows merge.                        |
| `AC-032`, `AC-035`, `AC-036`, `AC-037`, `AC-038` / docs, README, next-cycle inputs      | None yet                                                                                                                                 | Permitted later dependency: Documenter. README line 13 and the docs home and page extraction guide still say a second model reviews every page (E43). |
| `AC-033` / reference pages cover the new settings and fields                            | Generated pages; CI's stale-page check passing (R4); E43                                                                                 | Supported for the generated reference pages.                                                                                                          |
| `AC-034` / what page extraction sends                                                   | `extracting/prompts.py`, `text_layer.py` docstrings; E43                                                                                 | Docstring part supported. FAQ and guide part is a permitted later dependency (Documenter).                                                            |
| `AC-039`, `AC-040` / user review of real runs                                           | None yet                                                                                                                                 | Permitted later dependency: the user, after documentation.                                                                                            |
| `AC-041` / package and scripts reordered, move only                                     | R6 (move-only on `126f52f..0f4c949`), R7 (order on `fc6df7d`); E1–E11                                                                    | Supported. Every departure R7 reports is listed under `DEV-001`, with `SurveyVerification` above `PdfSurvey` from `DEV-006`.                          |
| `AC-042` / tests reordered, move only                                                   | R6 (`126f52f..7bd7f90`), R7; E8–E11                                                                                                      | Supported. Departures match the verification report's list.                                                                                           |

Constraints checked across the change: no shipped file names a development step,
date, role or cycle (R8); `PROBE_VERSION`, both `PROMPT_VERSION`s and
`schema_versions.py` are unchanged (R9); no alias, fallback, optional field or
default was added to keep old files loading (`PdfSurvey.verification`,
`PageFile.verification` and `LedgerEntry.agent` are required), so the user
style's compatibility rule is met. Developer self-checks were read as claims;
the dispositions rest on Tester's formal evidence (E-numbers in the verification
report) and on this review's diagnostics (R-numbers below).

## Checks and Results

All commands from the repo root on `fc6df7d`, 2026-11-21, with `.venv/bin`
tools. Scratch scripts live in this session's scratchpad (`review/`), not in the
repo.

- **R1 — Suite and linters.**
  `pytest -q --numprocesses auto -p no:cacheprovider` 207 passed;
  `pytest -q --doctest-modules src` 28 passed, 1 skipped;
  `ruff check scripts src tests` "All checks passed!";
  `ruff format --check scripts src tests` "89 files already formatted";
  `ty check scripts src tests` "All checks passed!"; `interrogate` 100.0%. All
  exit 0. This repeats Tester's E41 on the same content.
- **R2 — A verdict with problems and no correction.** A scratch test run with
  the repo's fixtures (`pytest -p tests.conftest --rootdir=.`, the stand-in
  provider, the CAPS excerpt with an answer turning pages 0–3 only,
  `advanced.survey.verify: true`): one `surveyor` and one `verifier` request and
  ledger line, `correction_applied` false, no correction failures,
  `rotation_differs` issues before the two `verifier` issues with page indexes 2
  and `null`, and the report's "found 2 problems, listed for review". Passed.
- **R3 — Global switch with the survey's override off.** Same harness,
  `verify=True` with `advanced.survey.verify: false` on the 1965 scan: the
  survey has `verification: null` and every page has a verification, one
  `verifier` request per page. Passed.
- **R4 — CI on the current head.** `gh pr view 12` and `gh pr checks 12` (run
  outside the sandbox, whose proxy fails GitHub's TLS check): head `fc6df7d`,
  draft, now closed. "Lint and test (Python 3.13)", "Test (Python 3.14)", "Wheel
  install" on `macos-latest`, `ubuntu-latest` and `windows-latest`, "Lint and
  test", "TruffleHog secret scan" and "Build the docs" all pass. `fc6df7d`
  differs from Tester's `1b311bc` only in `STATE.md` and the verification
  report, so this confirms E47 on the assessed content.
- **R5 — Merge gate and release setup.**
  `gh api repos/IDinsight/pydelity/rules/branches/main` (outside the sandbox):
  pull request rule and required checks "Lint and test" and "TruffleHog secret
  scan".
  `git diff --stat 126f52f HEAD -- .github release-please-config.json .release-please-manifest.json`
  is empty; the manifest is `0.1.1`.
- **R6 — Move only.** `review/moveonly.py` compares each changed file between
  two commits: the same multiset of non-blank lines, of top-level statements, of
  each class's members, and the same order of each class's non-method members.
  `126f52f` to `0f4c949` over `src/` and `scripts/`: 16 files, no problem.
  `126f52f` to `7bd7f90` over `tests/`: 16 files; only
  `tests/fixtures/mock_providers.py` differs at the top level, because
  `MockProviders`' methods moved inside the class; its members and field order
  are the same.
- **R7 — Module order.** `review/ordercheck.py` on every tracked module in
  `src/pydelity/`, `scripts/` and `tests/` at `fc6df7d`, applying the design's
  **Module order** (top-level groups and method order, validators and setters
  exempt). It reports 31 places, each one a departure listed under `DEV-001` or
  in the verification report, and no method out of order.
- **R8 — Process wording.**
  `grep -rnE "DEV-[0-9]|AC-[0-9]|2026-|KGForEd|STANDARDS|Scoper|Architect|Developer|Tester|cycle"`
  over `src`, `scripts`, `examples` and `pyproject.toml`: only outline and
  container "cycle" in their technical sense, and `scripts/format_markdown.mjs`,
  which this cycle did not change. No "second model", "verifier model" or
  "reviews every page" in those paths.
- **R9 — Version constants.** `PROBE_VERSION`, the survey's and page
  extraction's `PROMPT_VERSION` are 1 at `5b94a4d` and at `fc6df7d`;
  `schema_versions.py` is unchanged.
- **R10 — Output schema size.** `review/depth.py`: `SurveyVerdict`'s JSON schema
  has object depth 4 and 49 properties expanded, against 5 and 43 for page
  extraction's `VerifierVerdict`, which has run on both providers. This suggests
  the nested correction stays within provider limits; only the real runs
  (`AC-040`) can show it.
- Not run: Python 3.14 locally (CI covers it), the `just` recipes through `uv`,
  the wheel smoke test locally (CI covers it), any real model.

## Findings

**No material findings.**

## Questions, Limitations, and Later Dependencies

Later dependencies, each with its owner and the evidence still required:

- Documenter, documentation-record evidence: `AC-032`, `AC-035`, `AC-036`,
  `AC-037`, `AC-038`, the README part of `AC-030`, and the FAQ and guide part of
  `AC-034`. The README (line 13), `docs/src/content/docs/index.md` (line 16) and
  `docs/src/content/docs/guides/page-extraction.md` (line 11) still say a second
  model reviews every page.
- The user: `AC-039` and `AC-040`, accepted real runs on Anthropic and OpenAI
  with default settings and with both verifiers on.

Non-material limitations, none of which blocks this gate:

- The survey verifier's replacement upload after a 404 has no test of its own.
  It runs through `_run_with_upload`, the same code the survey request uses,
  which `test_uploads.py` covers, and Developer's scratch check exercised it.
- A dangling catalog `Outlines` link has no test; `AC-023` names `First` and
  `Next` links, which are tested.
- A verdict with problems and no correction runs in the suite only through the
  branch it shares with a rejected correction; R2 checked it end to end.
- The verifier's `page_index` for a survey problem is the model's and is not
  checked against the page count. An out-of-range value gives a review issue
  whose page link leads nowhere; nothing fails.
- Whether `SurveyVerdict` works with OpenAI's native output and Anthropic's
  prompted output is known only from the schema's shape (R10) until the real
  runs.

No blocking user question.

## Progress and Conclusion

- Done: the contract read in full; every current AC and technical criterion
  accounted for; the feature code read by diff and in place; tests sampled;
  R1–R10 run. Nothing remains to check for this gate.
- The gate passes. No material finding or assessment gap is open, and the only
  open items are later-phase dependencies owned by Documenter and the user,
  recorded under the same ACs.
- Plain-language summary: the work can move on to documentation. The code does
  what the scope and design ask. Verifiers are off unless turned on, the survey
  has its own verifier, pages without a verifier list every difference, and the
  five leftover fixes are in. The reorder only moved code. Tests, linters and CI
  on all three systems and both Python versions pass. Still open: the README and
  docs still describe a verifier that always runs, which Documenter fixes, and
  the user's real runs on both providers. Passing this review does not finish
  the cycle.
- Handoff: forward to Documenter (`DOCUMENTING`), with the later dependencies
  above.

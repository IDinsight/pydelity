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
  `BROWNFIELD`. This pass is the implementation review rerun under recovery
  frame 1 (owner `SCOPING`, `ResumeAt` `SYNCHRONIZING`, `RerunThrough`
  `REVIEWING_FINAL`): the user's rework that makes code's measurements of the
  PDF hints. Reviewer does not own the frame.
- Current acceptance set: `AC-001` to `AC-054` without `AC-019` and `AC-034`,
  which are retired (replaced by `AC-048` and `AC-051`). New since the earlier
  pass: `AC-043` to `AC-054`.
- Contract, by last commit and SHA-256 prefix:
  - scope
    `.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`01598d8`, `2d921029f902dc4e`);
  - design
    `.standards/docs/specs/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`5cb51ac`, `a69221d00c35dfd5`), decisions 1–16, **Checks and hints** and
    the technical acceptance criteria;
  - development plan
    `.standards/docs/development/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`de4efcd`, `215cd7c4e02faf4f`; `COMPLETE`, `DEV-001` to `DEV-015` `DONE`,
    plan revision 2 approved);
  - verification report
    `.standards/docs/verification/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`278264b`, `2dac1da950f88fb9`; `COMPLETE`, `FULL`, target `NONE`, E1–E60);
  - project context `.standards/CONTEXT.md` (`0573e11`, `09045f457b2df4c1`,
    unchanged); user style `.standards/user-styles/reviewer/tony.md` (`797def3`,
    `43b3830a5152e51d`, unchanged).
  - Read as context for later dependencies only: the documentation record
    (`c0ed1e9`, `ce37e24b779ea0bb`) and the final review (`82dfd30`,
    `82523a6d2d888be8`), both from before the rework.
- Repository: branch `tz6/pipeline-step-2` at `278264b`, clean apart from this
  report. Baseline `126f52f`, the commit before the reorder.
  - Source: `de4efcd`. The hints rerun is
    `git diff 6807b18 de4efcd -- src scripts` (15 files, SHA-256
    `11e8a07375080e4a`); the cycle's whole change is
    `git diff 126f52f de4efcd -- src scripts examples docs pyproject.toml`
    (SHA-256 `9de0a5151e9832a2`). Both match Tester's identities. Between the
    earlier pass (`fc6df7d`) and `6807b18` the source changed only in
    Documenter's docstrings (`extracting/schemas.py`, `pipeline/schemas.py`,
    `review.py`, `c0ed1e9`).
  - Tests: `git diff de4efcd 3648a0b -- tests` SHA-256 `080c66931785a977` (3
    files, Tester's assessed change); `git diff 126f52f 3648a0b -- tests`
    `ff7807a5c5dedcf5`. `278264b` differs from `3648a0b` only in `STATE.md` and
    the verification report.
  - `.github/`, `release-please-config.json` and `.release-please-manifest.json`
    (`0.1.1`) are unchanged since `126f52f`.
- Areas read for this pass, by diff and in place: `extracting/validators.py`,
  `extraction.py` (`_extract_page`, `_kept_answer`, `_page_issues`,
  `request_sizes`), `llm.py`, `agents.py`, `prompts.py` (whole prompt text),
  `schemas.py`, `text_layer.py`; `surveying/validators.py`, `survey.py`
  (`build_survey`, `run_survey`), `llm.py`, `agents.py`, `prompts.py` (whole
  prompt text), `schemas.py`; `review.py`; `pipeline/runner.py`;
  `scripts/generate_reference_docs.py`. Tests read: the 3648a0b diff of
  `test_extraction.py` (P1–P4, REQ, P3) and the survey test for `AC-049`. Areas
  the rework did not touch rest on the earlier pass below, rerun through the
  suite.
- Environment: macOS arm64, Python 3.13.9 (`.venv`, editable install), PyMuPDF
  2.1. Python 3.14 is not installed locally; CI covers it.
- Project references loaded: `NONE` (`.standards/project-references/reviewer/`
  does not exist).
- Session: a new conversation that started with this review and holds no
  authoring history. The client cannot certify freshness. The models that
  produced the work are not recorded, so whether this review ran on a different
  model is unknown.

## Contract and Evidence Assessment

| Obligation / criterion                                                                                                                                         | Assessed evidence                                                                                                                        | Current disposition                                                                                                                                                                                                                                                      |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `AC-043` / every request presents facts and survey findings as hints; no message asks to match                                                                 | Both steps' prompt text read in full (R13); P4, REQ, S4; retry builders read (R13)                                                       | Supported. Page text gives the direction as what the survey found and the repeated lines and fields under hint headings; `_RULES` says the image decides; both verifiers say a correction need not agree; the survey's own request already calls the facts hints.        |
| `AC-044` / only checks send an answer or correction back; a hint never fails anything                                                                          | All four output validators call `run_checks` only (R13); `run_checks` holds `CHECKS` only; P1–P3, S1–S3, V1; Tester's mutations (E54)    | Supported. Hints are computed after the kept answer is chosen and only build `hints` and issues; no hint path raises.                                                                                                                                                    |
| `AC-045` / extraction request carries only repeated lines and field values                                                                                     | `_page_text` read (R13); no check in `CHECKS` reads `page_text` (R14); REQ, P2                                                           | Supported. No retry message can quote a stored line, since none of the six checks reads the text layer.                                                                                                                                                                  |
| `AC-046` / page verifier lists every hint difference, `text_dropped` quoting its line                                                                          | `_extract_page` passes `compare_with_hints(extracted.answer, …)`; `verify_page` sections; P3, P2 `passed`                                | Supported.                                                                                                                                                                                                                                                               |
| `AC-047` / a correction passing every check is kept whatever its hint differences                                                                              | `_kept_answer` (`not any(correction_failures.values())`, checks only); P3 `correction_kept` (differs from `artifacts` and `text_added`)  | Supported.                                                                                                                                                                                                                                                               |
| `AC-048` / page review list by outcome; `hints` keeps every difference                                                                                         | `_page_issues` order (checks, hints unless accepted, `no_matching_label`, `verifier`); `hint_results` on the kept answer; P1, P2, P3, V1 | Supported. Matches **Page extraction without a verifier**.                                                                                                                                                                                                               |
| `AC-049` / a final answer still failing a check is kept and listed; only unusable answers stop                                                                 | P2 (both rows, `run.json` `completed`), S4, `test_checks_still_failing_after_the_retries_are_listed_for_review`; stop handlers unchanged | Supported. The page and survey stop conditions in each `llm.py` are untouched by the rerun.                                                                                                                                                                              |
| `AC-050` / tests of item 10, both providers mocked, each verifier on and off                                                                                   | P1–P4, REQ, V1, S1–S4; E52 (211 passed), E54 (27 mutations caught), E60 (CI)                                                             | Supported. Each case the AC lists has a passing test whose assertions observe the outcome (R13 sampled P1–P4).                                                                                                                                                           |
| `AC-054` / repeated lines and the survey's finding as hints; no order to put one in an artifact                                                                | `_page_text`, `_RULES` page furniture paragraph (R13); P4                                                                                | Supported. The general furniture definition remains; no sentence ties a repeated line to role `artifact`.                                                                                                                                                                |
| `AC-011` / survey review list by outcome; `hints` keeps every difference                                                                                       | `build_survey` (hints on the kept answer, listed unless accepted); S1–S4                                                                 | Supported.                                                                                                                                                                                                                                                               |
| `AC-051` / docs and docstrings say what page extraction sends                                                                                                  | `extracting/prompts.py`, `text_layer.py`, `validators.py`, `agents.py`, `surveying/validators.py`, `review.py` docstrings (R13)          | Docstring part supported. Guides and FAQ part is a permitted later dependency (Documenter); see R18.                                                                                                                                                                     |
| `AC-052` / docs explain hints, checks and when a run stops                                                                                                     | Generated `extraction-checks.md` and `survey-checks.md` (E56; generator read, R13)                                                       | Generated part supported. Guides part is a permitted later dependency (Documenter); see R18.                                                                                                                                                                             |
| `AC-053` / `next_cycle_inputs.md` records the hint rule                                                                                                        | None yet                                                                                                                                 | Permitted later dependency: Documenter.                                                                                                                                                                                                                                  |
| `AC-018` / with the verifier off, extractor requests only                                                                                                      | `_extract_page` (`run.model.verify`); P1, P2 `no_verifier`                                                                               | Supported.                                                                                                                                                                                                                                                               |
| `AC-020` / `verification: null` when no verifier ran; report and log say so                                                                                    | Unchanged code; E52 rerun                                                                                                                | Supported (earlier pass, rerun).                                                                                                                                                                                                                                         |
| `AC-001`, `AC-002`, `AC-003`, `AC-004`, `AC-005`, `AC-006`, `AC-007`, `AC-008`, `AC-009`, `AC-010`, `AC-012`, `AC-013`, `AC-014`, `AC-015`, `AC-016`, `AC-017` | Earlier pass's dispositions; E52 and E59 rerun; R13 for the changed survey verifier input                                                | Supported. The survey verifier's request now takes `compare_with_hints` output under the new heading; `ask_verifier`, the agent, the keep rule and the verdict application are otherwise unchanged. `AC-007`'s "differences from the measured facts" are the hints (S4). |
| `AC-021`, `AC-022`, `AC-023`, `AC-024`, `AC-025`                                                                                                               | Earlier pass; code unchanged since; E52                                                                                                  | Supported.                                                                                                                                                                                                                                                               |
| `AC-026`                                                                                                                                                       | 211 tests (R11, E52, E60)                                                                                                                | Supported.                                                                                                                                                                                                                                                               |
| `AC-027`                                                                                                                                                       | R17 (CI on `3648a0b`, `main`'s rules)                                                                                                    | Supported.                                                                                                                                                                                                                                                               |
| `AC-028`, `AC-029`                                                                                                                                             | R17 ("Wheel install" on three runners, metadata check), E60                                                                              | Supported.                                                                                                                                                                                                                                                               |
| `AC-030`                                                                                                                                                       | `pyproject.toml` description (unchanged since `b579737`)                                                                                 | Package part supported. README part is a permitted later dependency (Documenter).                                                                                                                                                                                        |
| `AC-031`                                                                                                                                                       | R17: release files unchanged, manifest `0.1.1`; E57 (no breaking marker)                                                                 | Supported for release readiness; the release pull request follows merge.                                                                                                                                                                                                 |
| `AC-033`                                                                                                                                                       | E56 (regeneration identical), generator read (R13)                                                                                       | Supported; `page-json.md` and `pdf-survey-json.md` cover `hints`.                                                                                                                                                                                                        |
| `AC-032`, `AC-035`, `AC-036`, `AC-037`, `AC-038`                                                                                                               | Documenter's earlier record, from before the rework                                                                                      | Permitted later dependency: Documenter, in this rerun. `AC-032`'s "which differences go on the review list" now changes (R18).                                                                                                                                           |
| `AC-039`, `AC-040`                                                                                                                                             | None yet                                                                                                                                 | Permitted later dependency: the user's accepted real runs, including the GPF reading and math PDFs.                                                                                                                                                                      |
| `AC-041`, `AC-042`                                                                                                                                             | Earlier pass (R6, R7); the rerun's departures (`CHECKS`, `HINTS` below the functions they list) are listed in the plan; R15              | Supported.                                                                                                                                                                                                                                                               |

Retired `AC-019` and `AC-034` are historical only; their earlier rows no longer
stand as coverage.

Constraints checked across the rerun: no shipped file names a development step,
date, role or cycle (R16); both `PROMPT_VERSION`s and `PROBE_VERSION` are 1 and
`schema_versions.py` is unchanged (R16); no alias, fallback or optional field
was added for older files (`PageFile.hints` and `PdfSurvey.hints` are required,
and `compare_with_facts`, `TEXT_CHECKS` and `SurveyComparisonName` are gone), so
the user style's compatibility rule is met. That older output files are made
again is what the design says and is not a finding. Developer self-checks were
read as claims; the dispositions rest on Tester's formal evidence (E-numbers)
and this review's diagnostics (R-numbers).

## Checks and Results

This pass: repo root, `278264b`, 2026-11-22, `.venv/bin` tools. Scratch scripts
in this session's scratchpad (`review/`), not in the repo.

- **R11 — Suite and linters.**
  `pytest -q --numprocesses auto -p no:cacheprovider` 211 passed;
  `pytest -q --doctest-modules src -p no:cacheprovider` 28 passed, 1 skipped;
  `ruff check scripts src tests` "All checks passed!";
  `ruff format --check scripts src tests` "89 files already formatted";
  `ty check scripts src tests` "All checks passed!";
  `interrogate scripts src tests` 100.0% (the badge it rewrites is unchanged).
  All exit 0. This repeats Tester's E52 on the same content.
- **R12 — Identities.** The hints rerun diff, the whole-cycle diff and the test
  diff hash to Tester's recorded values (see **Assessed Inputs and Scope**).
- **R13 — Inspection of the rerun.** Every changed module read by diff and the
  prompts in full. Findings: `CHECKS` and `HINTS` hold the design's names in
  order in both steps; every output validator (both producers, both verifiers)
  calls `run_checks` only and builds its retry message from check failures only;
  `_kept_answer` keeps a correction with no check failure; `_page_issues` and
  `build_survey` follow the design's order and acceptance rule; `hints` is
  computed on the kept answer and the verifier's differences on the reviewed
  answer; each hint message describes what was measured or found and what the
  answer says, and none says what to change (read by meaning, not by word list);
  the page verifier's and survey verifier's rules say a correction must pass the
  checks and need not agree with the hints.
- **R14 — Checks never read stored text.** An `ast` walk of
  `extracting/validators.py` finds no use of `page_text` in `check_labels`,
  `check_content`, `check_languages`, `check_boxes`, `check_containers` or
  `check_captions`, so no retry message can quote a text-layer line (`AC-045`).
- **R15 — Module order of the changed modules.** `review/order.py` on the nine
  changed source modules: the only out-of-order definitions are `CHECKS` and
  `HINTS` below the functions they list, which plan revision 2 and `DEV-012`,
  `DEV-013` list as departures. Its other reports are the script's own
  simplification (it sorts capitals before underscores), not departures.
- **R16 — Process wording, versions, compatibility.**
  `grep -rnE "DEV-[0-9]|AC-[0-9]|2026-|KGForEd|STANDARDS|Scoper|Architect|Developer|Tester"`
  over `src`, `scripts`, `examples` and `pyproject.toml` (excluding
  `format_markdown.mjs`): no match. `PROMPT_VERSION = 1` in both prompt modules,
  `PROBE_VERSION = 1`, `schema_versions.py` unchanged since `fc6df7d`. A search
  of the changed modules for alias, deprecation, legacy, backward compatibility
  or fallback finds only unrelated technical uses.
- **R17 — CI and merge gate.** `gh pr view 13` and `gh pr checks 13` (run
  outside the sandbox, whose proxy fails GitHub's TLS check): head `3648a0b`,
  draft, now closed; "Lint and test (Python 3.13)", "Test (Python 3.14)", "Wheel
  install" on `macos-latest`, `ubuntu-latest` and `windows-latest`, "Lint and
  test", "TruffleHog secret scan" and "Build the docs" pass.
  `gh api repos/IDinsight/pydelity/rules/branches/main`: pull request rule and
  required checks "Lint and test" and "TruffleHog secret scan". This confirms
  E60 on the assessed content.
- **R18 — Docs wording the rework makes stale (for Documenter).** A search of
  `README.md` and `docs/src/content/docs` outside `reference/`:
  `guides/models-and-providers.md` lines 77–78 say a text check sends an answer
  back with stored lines quoted; `guides/page-extraction.md` lines 176–178 say a
  problem with the page's text can quote stored lines in the send-back;
  `guides/verifiers.md` lines 120–130 list only text differences as left off
  with a passing verifier and say they stay in `checks`; `guides/outputs.md`
  lines 122–128 put text differences under "Checks a page's answer still fails"
  and name only the two text hints. These are `AC-032`, `AC-051` and `AC-052`'s
  docs parts, Documenter's in this rerun.
- Earlier pass (2026-11-21, on `fc6df7d`), R1–R10: R1, R4, R8 and R9 are
  superseded by R11, R17 and R16 on the current content. R2 (a survey verdict
  with problems and no correction) assessed `build_survey` before the rework;
  the not-kept branch is now read in R13 and run by S3 `correction_not_kept`. R3
  (global switch with the survey's override off), R5 (release setup), R6 and R7
  (move-only and order of the reorder), and R10 (the verdict schema's size)
  assessed code and files the rework did not change, so they still apply.
- Not run: Python 3.14 locally (CI covers it), the `just` recipes through `uv`,
  the wheel smoke test locally (CI covers it), any real model.

## Findings

**No material findings.**

## Questions, Limitations, and Later Dependencies

Later dependencies, each with its owner and the evidence still required:

- Documenter, documentation-record evidence in this rerun: `AC-032`, `AC-035`,
  `AC-036`, `AC-037`, `AC-038`, `AC-053`, the README part of `AC-030`, and the
  guides and FAQ parts of `AC-051` and `AC-052`. R18 lists the passages that
  still describe the old rule.
- The user: `AC-039` and `AC-040`, accepted real runs on Anthropic and OpenAI
  with default settings and with both verifiers on, including the GPF reading
  and math PDFs.

Non-material limitations, none of which blocks this gate:

- How real models respond to the hint wording, and whether fewer artifact items
  and more review issues follow, is known only from the real runs (`AC-039`,
  `AC-040`); the design names this risk.
- Carried from the earlier pass, in code the rework did not change: the survey
  verifier's replacement upload after a 404 has no test of its own (it shares
  `_run_with_upload` with the survey request, which `test_uploads.py` covers); a
  dangling catalog `Outlines` link has no test (`AC-023` names `First` and
  `Next`, which are tested); a survey verifier problem's `page_index` is not
  checked against the page count, so an out-of-range value gives an issue whose
  page link leads nowhere, and nothing fails; `SurveyVerdict` on both providers'
  structured output is known only from its schema's shape until the real runs.

No blocking user question.

## Progress and Conclusion

- Done: the contract and records read; every current AC and technical criterion
  accounted for; the rerun's code read by diff and in place; the new tests
  sampled; R11–R18 run. Nothing remains to check for this gate.
- Reconciled on resumption: the earlier `COMPLETE` conclusion was reopened
  because the scope gained `AC-043` to `AC-054` and retired `AC-019` and
  `AC-034`, and the source, design, plan and tests changed. The earlier rows for
  code the rework did not touch are kept, with the reason under R11–R18.
- The gate passes. No material finding or assessment gap is open; the open items
  are later-phase dependencies owned by Documenter and the user, recorded under
  the same ACs.
- Plain-language summary: the work can move on to documentation. The code now
  treats what pydelity measures about the PDF as hints. A difference from a hint
  is written down and shown for review but never sends an answer back to the
  model or stops a run; only problems with the answer itself do. The prompts
  call the measurements hints and no longer tell the model to put repeated lines
  in page furniture items. Tests, linters and CI on both Python versions and all
  three systems pass. Still open: several docs guides describe the old rule,
  which Documenter fixes next, and the user's real runs on both providers.
  Passing this review does not finish the cycle.
- Handoff: forward to Documenter (`DOCUMENTING`) as the next state of recovery
  frame 1's rerun, which stays on the stack through `REVIEWING_FINAL` before
  synchronization resumes.

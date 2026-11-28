<!-- STANDARDS
Artifact: REVIEW
Cycle: build-step-3-page-break-verification-of-20261122T170208Z-00fe2896
ReviewKind: IMPLEMENTATION
-->

# Review Report

`Cycle`: `build-step-3-page-break-verification-of-20261122T170208Z-00fe2896`
`ReviewKind`: `IMPLEMENTATION` `Status`: `COMPLETE` `User Style`: `tony`

## Assessed Inputs and Scope

This is the second implementation review of this cycle. It runs inside recovery
frame 1 (`Owner: SCOPING`, `ResumeAt: REVIEWING_FINAL`,
`RerunThrough: DOCUMENTING`), after the user's rework of 2026-11-28. The earlier
review (2026-11-22, HEAD `8201e2e`, AC-001 to AC-051) is superseded; see
**Progress and Conclusion**.

- Cycle mode `STANDARD`, completion policy `FULL_DELIVERABLE`, project mode
  `BROWNFIELD`. Current acceptance set: `AC-001` to `AC-024`, `AC-027`,
  `AC-028`, `AC-031` to `AC-035`, `AC-037` to `AC-049`, `AC-052` to `AC-062`.
  Retired: `AC-025`, `AC-026`, `AC-029`, `AC-030`, `AC-036`, `AC-050`, `AC-051`.
  The design's technical acceptance criteria use the same IDs.
- Records, by the first 16 hex digits of their SHA-256. Each matches what Tester
  assessed:
  - scope `f8655478af2060c8`
  - design `5bd367355f1a64b8`
  - plan `c8107620423e0d6e` (`COMPLETE`, `AFTER_IMPLEMENTATION`,
    `Current Increment: NONE`, DEV-001 to DEV-016 `DONE`)
  - context `0e940ffe605aecff`
  - verification report `783bc5e09658a610` (`COMPLETE`, `FULL`, `NONE`), as
    committed in `5f5e75d`
- Change: `main...HEAD` on `tz6/pipeline-step-3`, merge base `7dc2cba` (0.2.0),
  HEAD `5f5e75d`, also pushed as `origin/tz6/pipeline-step-3`. The working tree
  is clean apart from this report.
  - The rework is `50229ba` to `bc56b21` (Developer) and `5f5e75d` (Tester).
    Reviewed as `git diff 1a0cae1..HEAD -- . ':!.standards'`: 29 files.
  - `5f5e75d` changes only tests, `tests/conftest.py`,
    `tests/fixtures/mock_providers.py` and STANDARDS records. Its six test files
    have the hashes Tester recorded as uncommitted (`c4c0c04766276a5a`,
    `81ddfe107d2bc806`, `6a847167c5d1a4c7`, `6ac521cb6ac34459`,
    `450645e43a532a44`, `74855c4384bf601b`). So `src/`, `scripts/`, `examples/`,
    `docs/` and `pyproject.toml` are as at `bc56b21`, where Tester built the
    wheel and regenerated the reference pages.
  - `uv.lock`, `pyproject.toml`, `.github/`, `release-please-config.json` and
    `.release-please-manifest.json` are unchanged since the earlier review.
- Source read in full or in the changed parts:
  - `verifying/verification.py` (the rework diff: `_judge_break`,
    `_break_input`, `_verified_file`, `_matching_break`, `_needs_verifier`,
    `plan_breaks`, `request_sizes`, `request_sizes_before_pages`, the tail of
    `verify_breaks`)
  - `verifying/agents.py` and `verifying/llm.py` in full
  - `verifying/prompts.py` (the rework diff: the `new_entry`, `repeat` and "When
    text carries on" rules, the removed verifier prompt)
  - `verifying/schemas.py` in full
  - `verifying/validators.py` `review_issues`, `_issue`, `_issue_item`
  - `costs/budget.py` (`BreakRequestSize`, `estimate_page_breaks`)
  - `pipeline/runner.py` `_breaks_estimate`, `_breaks_estimate_before_survey`,
    the step's `StepModel` (`verify=config.verify_page_breaks`)
  - `report/html.py` `_break_verifier_text`
  - `review.py`, `cli.py` (`--verify` help), `config/schemas.py`,
    `examples/config.yaml`, `scripts/smoke_installed_wheel.py` (diffs)
- The rest of `verifying/validators.py` (`joins`, `repeats`, `start_markers`,
  `compare_verdicts`) was checked by an independent subagent briefed with the
  design and scope, not with this review's conclusions. See **Checks and
  Results**.
- Tests read: the scenario list in the verification report, and in
  `tests/pydelity/verifying/test_verification.py` F3', F5'/F7', F9 and A3', to
  see what they assert.
- Project references: `NONE` (`.standards/project-references/` does not exist).
- Session: this Reviewer conversation holds no authoring history. The client
  gives no session or model metadata, so freshness and the authoring models are
  not known.
- Excluded: the docs-site guides, the README and
  `artifacts/next_cycle_inputs.md` (Documenter reruns them next), and real model
  runs (the user's).

## Contract and Evidence Assessment

Tester evidence is in the verification report (scenario IDs as named there).
Reviewer diagnostics are under **Checks and Results**. "Supported" means the
code does what the AC asks and the evidence shows it. ACs the rework did not
touch were rechecked against the rework diff for side effects; their earlier
evidence stands where its source is unchanged.

| Obligation                                                     | Assessed evidence                                                                                                                                                                                                                                                      | Current disposition                                                                          |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008 | Run flow, current page files, pause, API, `load` and model settings are unchanged by the rework. R1, R3, R4, R7, U4–U7, U11, API1, API2, CFG1 all pass on `5f5e75d`.                                                                                                   | Supported                                                                                    |
| AC-009                                                         | `ask_model` builds one request from `judge_break` for both agents; the step's instructions go last. F2+P3; F5'/F7' assert the verifier's body equals the judge's.                                                                                                      | Supported                                                                                    |
| AC-010                                                         | `examples/config.yaml` comments changed only. Example-config completeness test passes.                                                                                                                                                                                 | Supported                                                                                    |
| AC-011, AC-012                                                 | Verdict and verdict file fields unchanged apart from `verification`. F1, V1, V7.                                                                                                                                                                                       | Supported                                                                                    |
| AC-013, AC-014                                                 | `joins` matches the design's join table (subagent reference check, pass and fail). V1, V2, V11, V13.                                                                                                                                                                   | Supported. L7 notes messages that leave out a second reason.                                 |
| AC-052                                                         | `new_entry` ends in a list or text item and starts in a list item; the rule is in `_RULES`. V10, V11; subagent.                                                                                                                                                        | Supported                                                                                    |
| AC-053                                                         | `TextJoin` holds `repeat`; `joins` allows it only in `cell_joins`; `repeats` checks each `repeat` cell against the split row, in any script. V12–V14; subagent (Chinese, Arabic, Japanese, NFKC).                                                                      | Supported. L1 covers the design-accepted looseness of matching any cell.                     |
| AC-054                                                         | Read `_RULES` "When text carries on": unfinished text only; a paragraph broken between sentences with no new paragraph is unfinished; a complete entry then a newly numbered one is `new_entry`. Sent in both agents' requests.                                        | Supported (prompt rule; code cannot enforce it, as the design says)                          |
| AC-015, AC-024                                                 | `header_rows` unchanged. V1, V4.                                                                                                                                                                                                                                       | Supported. L4 stands.                                                                        |
| AC-016                                                         | `repeated_items` and `repeats` unchanged for items. V1, V5.                                                                                                                                                                                                            | Supported. L1, L2 stand.                                                                     |
| AC-017, AC-018                                                 | Unchanged. V1, V6, V7, H1.                                                                                                                                                                                                                                             | Supported. L5 stands.                                                                        |
| AC-019, AC-020, AC-021                                         | Unchanged checks, rotation and rendering. V3, P1, P2, V8; subagent fuzzing on self-contradicting page files raised nothing.                                                                                                                                            | Supported                                                                                    |
| AC-022                                                         | Greps of `verifying/*.py`: the only direction text is a statement chosen from each page's own value; the start-marker exceptions read only the verdict's join, markers and the start item's kind.                                                                      | Supported                                                                                    |
| AC-023                                                         | One output validator for both agents; `ModelRetry` only for `run_checks` failures; last verdict kept. A1, L1, A3'.                                                                                                                                                     | Supported                                                                                    |
| AC-055                                                         | Hints sit under their heading. `start_markers` skips `append_rows` and a piece with a marker on its start item (and start row for a table). V9, V15–V18; subagent.                                                                                                     | Supported. L9 notes two loose spots in the design's wording.                                 |
| AC-056                                                         | `review_issues` lists hint differences unless a verification exists with no differences; `hints` keeps them; no retry message holds one. V9, F5'/F7', A2.                                                                                                              | Supported. L6 is one rare case where a verifier match is overstated.                         |
| AC-027, AC-028                                                 | `verification=None` without the verifier; `verify_page_breaks` wiring unchanged (`StepModel.verify`). R1, CFG2, U12, U13.                                                                                                                                              | Supported                                                                                    |
| AC-057                                                         | `_judge_break` sends the same request for `VERIFIER` after the judge's file is written, through the same agent factory and validator. F5'/F7' (equal bodies, ledger judge then verifier), A3' (sent back within `check_retries`).                                      | Supported                                                                                    |
| AC-058                                                         | `compare_verdicts(kept, verifier)` with the judge's verdict kept; pairing, field order and uncompared fields match the design (subagent reference over 202,000 fuzzed pairs, plus C1–C6). No third request exists in the code.                                         | Supported, apart from L6 (an end or start that differs only in its item when entries match). |
| AC-059                                                         | `BreakVerification` holds `attempts`, `checks`, `differences`, `verdict`; written by `_verified_file`. F5', F7', A3'.                                                                                                                                                  | Supported                                                                                    |
| AC-031                                                         | Issues name the step, both pages and the item. F7', A1, H1; subagent. `item_id` can hold a container ID (L8, unchanged since the earlier pass).                                                                                                                        | Supported                                                                                    |
| AC-032, AC-034                                                 | Each agent's request goes through `model.model.for_page(agent=..., page_index=earlier)`, so the ledger and `SpendGuard` cover verifier requests. U6, U12, F3', F9, R6 (corrected).                                                                                     | Supported                                                                                    |
| AC-033                                                         | `estimate_page_breaks` prices `int(judge) + int(verify)` agents per break; `request_sizes` sets `judge=planned.unverified is None`; the runner passes unreused breaks only. U8, F3', E1, R5, U9.                                                                       | Supported                                                                                    |
| AC-035                                                         | Fingerprint and `_matching_break` unchanged in substance. U4, F1, F2, Tester's one-off check (Execution Evidence 9).                                                                                                                                                   | Supported                                                                                    |
| AC-060                                                         | `_needs_verifier` (model judgment, no verification, verifier on) sets `PlannedBreak.unverified`; `_judge_break` skips the judge and `_verified_file` keeps `verdict`, `checks`, `hints`. Another step's verifier reaches a break only through page bytes. F3', F9, F1. | Supported                                                                                    |
| AC-037, AC-038                                                 | Two atomic writes per verified break; the judge's file is saved before the verifier's request. `_run` maps errors for either agent. F8, L1–L4, F9.                                                                                                                     | Supported                                                                                    |
| AC-039                                                         | `_break_verifier_text` says matches, lists each difference, or no verifier ran; text goes through the existing escaping. H1, H2, U10, F5'/F7'.                                                                                                                         | Supported                                                                                    |
| AC-040                                                         | 261 tests, run by Reviewer on `5f5e75d`.                                                                                                                                                                                                                               | Supported                                                                                    |
| AC-041                                                         | `.github/` unchanged; Tester's ruleset read and Python 3.14 run.                                                                                                                                                                                                       | Supported                                                                                    |
| AC-042                                                         | macOS smoke run by Tester on `bc56b21` source. Pull request 16's Linux and Windows wheel jobs passed, but on `d2e8cca`, before the rework's source changes. No check run exists for `5f5e75d`.                                                                         | Permitted later dependency (below)                                                           |
| AC-043                                                         | Tester's build and `twine check --strict` on `bc56b21`; packaging inputs unchanged since.                                                                                                                                                                              | Supported                                                                                    |
| AC-044                                                         | `pyproject.toml` text unchanged and correct. The README still describes a reviewing verifier (`README.md:18-20`, `:102`, per Tester).                                                                                                                                  | Package text supported; README is a permitted later dependency                               |
| AC-045                                                         | Release config and the `0.2.0` manifest unchanged.                                                                                                                                                                                                                     | Readiness supported; the release follows sign-off and merge                                  |
| AC-046, AC-048, AC-049                                         | The guides and README from `1a0cae1` describe the replaced verifier.                                                                                                                                                                                                   | Permitted later dependency (Documenter, rerun next)                                          |
| AC-047                                                         | Tester regenerated all 13 reference pages on `bc56b21`, byte-identical; `page-break-json.md` and `page-break-checks.md` describe `repeat`, `verdicts_differ` and `verification`'s new fields. Source and scripts unchanged since.                                      | Supported in code; Documenter regenerates only if the docs work changes the code             |
| AC-061, AC-062                                                 | None yet.                                                                                                                                                                                                                                                              | Permitted later dependency (the user's real runs)                                            |

## Checks and Results

All commands ran from the repo root on HEAD `5f5e75d` with a clean tree (apart
from this report), macOS arm64, Python 3.13.9 in `.venv`, on 2026-11-28.

- `.venv/bin/python -m pytest -q --numprocesses auto -p no:cacheprovider`: 261
  passed, exit 0. The 70 warnings are the ones the verification report explains.
  This repeats Tester's Execution Evidence 2.
- `.venv/bin/python -m pytest -q --doctest-modules src -p no:cacheprovider`: 40
  passed, 1 skipped.
- `.venv/bin/ruff check scripts src tests`,
  `.venv/bin/ruff format --check scripts src tests` (101 files),
  `.venv/bin/ty check scripts src tests` and
  `.venv/bin/interrogate scripts src tests` (100%): all passed. The tracked
  `interrogate_badge.svg` stayed unchanged.
- `BreakVerdict` through PydanticAI's `OpenAIJsonSchemaTransformer(strict=True)`
  after `TextJoin` gained `repeat`: strict-compatible, so native output on
  OpenAI still takes it.
- Greps of the lines the rework adds to `src`, `scripts` and `examples`: no
  compatibility code, and no DEV/AC IDs, KGForEdGlobal, step numbers, STANDARDS
  or dates.
- `gh pr list --head tz6/pipeline-step-3 --state all` and `gh pr checks 16`, run
  outside the sandbox because gh's TLS check fails inside it: pull request 16 is
  closed, head `d2e8cca`, with every check passed there, `Wheel install` on
  ubuntu, macOS and Windows included. `d2e8cca` predates the rework's source
  changes, so this is not evidence for the current code. The check-runs API
  returns nothing for `5f5e75d`.
- Independent subagent check of `verifying/validators.py` against the design's
  **Verdict contract**, **Checks and hints**, **Verdict comparison** and
  **Review issues**:
  - About 100 hand-written cases and 282,000 fuzzed verdict pairs on four
    page-file pairs, including page files that break their own rules and
    Chinese, Arabic and Japanese text. No exception.
  - Matched references built from the design for `joins`, `repeat` cells,
    `start_markers` and the comparison's pairing and field order. Invariants
    that held: a verdict compared with itself gives nothing; every difference
    has the earlier page and the `verdicts_differ` prefix; changing repeated
    items, markers, containers or reason changes no difference; piece order does
    not matter when ends and starts are unique.
  - One departure from the design, which Reviewer reproduced with the subagent's
    script (`compare_verdicts` returned `[]`; recorded as L6), and three smaller
    ones (L7–L9).
  - Not covered by it: the report, the step flow and the prompts. Reviewer read
    those.
- `node .standards/bin/check.mjs`: passed with this report `COMPLETE`, after
  naming each AC in the table (a first run read `AC-001 – AC-008` as two IDs).
- Reused without rerunning, because `5f5e75d` changes neither the source nor the
  packaging, scripts or docs inputs since `bc56b21`:
  - Tester's Python 3.14 run, wheel build, `twine check --strict` and macOS
    wheel smoke test (Execution Evidence 3, 6, 7).
  - Tester's regeneration of the reference pages (Execution Evidence 8).

## Findings

No material findings.

## Questions, Limitations, and Later Dependencies

Limitations (not findings). Under this cycle's major-issues-only bar, a finding
must make the delivered output wrong, lose money, fail a run or break a function
the acceptance review relies on. None of these does on its own: each needs a
model to have erred already, or only changes a message or a review-list line,
never the kept verdict. The real runs (AC-061, AC-062) are where to see whether
any matters.

Carried over from the earlier review, still present:

- **L1 — `repeats` accepts containment of any length** (`_repeat_matches`,
  `_printed_forms`). A wrongly named repeated item passes when its text holds a
  word printed on page N, such as the page number. The same matching now serves
  `repeat` cells, which can match any cell of the split row (the design's Risks
  section accepts this).
- **L2 — `repeats` skips repeated items with no text** (`_repeat_problems`), as
  designed.
- **L3 — `duplicates` is per item** (`check_duplicates`). A list whose last
  entry carries on as a text item and then goes on as a list on page N+1 needs
  two pieces ending in the same list item, so the correct verdict fails
  `duplicates` and is kept and listed.
- **L4 — `header_rows` uses only text similarity.** A repeated header row with a
  continuation word in a short cell can score below 0.8 and fail a correct
  count. The design's Risks section accepts this.
- **L5 — a symbol-only marker such as "→" always passes `markers`**, because its
  comparison form is empty.

New in this review:

- **L6 — an end or start that differs only in its item is no difference**
  (`validators.py` `_pair_differences` with `_point`). `_point` names an end or
  start by its entry ID when the piece names one, and ignores the item then.
  - Case: the kept piece ends in `p0007-004` / `p0007-004.2`, and the verifier's
    ends in `p0007-002` / `p0007-004.2`. `compare_verdicts` returns nothing. The
    same holds for starts.
  - Such a verifier verdict names an entry that is not in its item, so it fails
    `ids`. The verifier gets `check_retries` chances to fix it, and only its
    last verdict is compared.
  - Effect: the break reads "verifier agrees", and any start-marker hint
    difference on the kept verdict leaves the review list. The verifier's `ids`
    failure stays in `verification.checks`. The kept verdict, which assembly
    uses, is not changed and passes its checks.
  - The AC-058 text says the items and entries are compared, so this departs
    from its letter. It stays a limitation under the bar above because both
    verdicts name the same entry and nothing assembly uses is wrong. Developer
    could compare the item and the entry both, if the user wants it fixed.
  - The user chose on 2026-11-28 to have Developer fix it, after this review
    passed. It went to `DEVELOPING` as user rework (`IMPLEMENTATION`, recovery
    frame 2). Required outcome: two paired pieces whose `earlier_item` or
    `later_item` differ give an `end` or `start` difference even when their
    entries are the same, with both verdicts' item and entry in the difference.
    The case above reproduces it. Reviewer rechecks it on the rerun.
- **L7 — `joins` messages can leave out a second reason.** `repeat` in a
  `text_join` whose end item is missing, and `newline` in `cell_joins` when the
  header-row count is also wrong, fail for the other reason first. The verdict
  is still sent back or listed. Only the message is incomplete.
- **L8 — `item_id` can hold a container ID** (`_issue_item` falls back to
  `container`), as in the earlier pass and as its docstring says. The design
  says `item_id` is the item. The issue still names the break and points at the
  box concerned.
- **L9 — two loose spots in the `start_markers` design text.** For a list start
  with no `later_entry`, the code reads the list's first entry, which the design
  does not list but which fits its intent. Whether a start is "a table" for the
  marker exception is decided by the start item's kind, not the join. The two
  readings differ only on verdicts that already fail `joins`.
- **L10 — withdrawn.** It said the plan records no approval of the rework's new
  names (`repeat`, `verdicts_differ`, `BreakVerification`'s fields, the
  difference `details` keys, `compare_verdicts`, `BreakRequestSize`'s fields,
  `BreakComparisonName`, `create_break_agent`, `ask_model`, `BreakAnswer`). The
  user confirmed on 2026-11-28 that they approved these names, so nothing is
  open.
- **L11 — older verdict files are reused with the older prompt.** The judge's
  rules changed (DEV-012) and `PROMPT_VERSION` stays 1, as the scope sets for
  0.3.0. A verdict file without a verifier in an earlier real-run folder still
  matches and is reused. Real runs for AC-061 and AC-062 need new output folders
  or `--overwrite`, as the scope's Assumptions say.

Later dependencies, each still needing evidence under its own ID before final
review can pass:

| AC                     | Owner                                                        | Evidence still required                                                                                                                                                       |
| ---------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AC-042                 | User (push and open a pull request), checked at final review | `Wheel install (ubuntu-latest)` and `Wheel install (windows-latest)` pass for the reviewed HEAD, which includes the rework. Pull request 16's runs on `d2e8cca` do not count. |
| AC-044                 | Documenter                                                   | The README describes the three steps and each step's verifier, with the page-break verifier as a second judgment.                                                             |
| AC-046, AC-048, AC-049 | Documenter                                                   | As the verification report lists; the guides that quote the old verifier are named in DEV-015.                                                                                |
| AC-047                 | Documenter                                                   | Regenerated pages that still match, if the docs work changes the code.                                                                                                        |
| AC-061, AC-062         | User                                                         | Accepted real runs with the verifier off and on, in new output folders or with `--overwrite` (L11).                                                                           |

No blocking user question is open. `Active Work.BlockedOn` is `NONE`.

## Progress and Conclusion

- Superseded: the review of 2026-11-22 (HEAD `8201e2e`, scope
  `c0f8b54a9851b32c`, design `e9006fbf2a78ee99`) passed AC-001 to AC-051 with no
  material findings and limitations L1–L5. The rework replaced the verifier,
  changed `joins`, `repeats` and `start_markers`, and retired seven ACs, so that
  conclusion no longer applies. Its validators fuzzing and its reading of
  unchanged run, estimate and report code were rechecked against the rework diff
  and still apply where the code is unchanged.
- Done: the inputs were reconciled with Tester's, and none changed. The rework
  was read against every current AC and the design's technical criteria. The
  suite and static checks were rerun on `5f5e75d`. The validators were checked
  by an independent read with fuzzing, and its one departure was reproduced.
- The gate passes:
  - no material finding or assessment gap is open;
  - every current AC is supported or has a permitted later dependency, with its
    owner and the evidence needed;
  - no blocking question is open, and no obligation belongs to this state;
  - `check` passes, and the inputs were rechecked against the hashes and HEAD
    above just before marking this report `COMPLETE`.
- Next: Documenter (`DOCUMENTING`) reruns the docs under recovery frame 1
  (`RerunThrough: DOCUMENTING`), then the frame returns to final review. Final
  review must find Linux and Windows wheel CI on the reviewed HEAD for AC-042
  and resolve every later dependency above.

Plain-language summary: the reworked page-break code can move on to
documentation. Nothing needs fixing first. The verifier now asks the same
question a second time without seeing the first answer, code compares the two,
and every difference goes on the review list. Tests, lint and type checks pass.
One rare gap: if the second answer names a list entry under the wrong item and
keeps doing so after its retries, the comparison misses it and the break reads
as agreed (L6). The answer that is kept is not affected. Still unchecked: the
wheel on Linux and Windows for the reworked code (CI runs when you open a pull
request), the README and guides (Documenter, next), and real model runs (you, in
new output folders).

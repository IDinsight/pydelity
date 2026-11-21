<!-- STANDARDS
Artifact: VERIFICATION
Cycle: add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada
-->

# Verification Report

`Cycle`: `add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada`
`Mode`: `VERIFY` `Status`: `BLOCKED` `User Style`: `tony` `Assessment Purpose`:
`INCREMENT` `Assessment Target`: `Increment 1`

## Assessed Inputs

- Scope
  `.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
  (last changed in `49448e5`, SHA-256 `dd6ea5291602d518…`), design
  `.standards/docs/specs/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
  (`126f52f`, `846800debae3d32f…`; decision 13, **Module order**, the `AC-041`
  and `AC-042` technical criteria), development plan
  `.standards/docs/development/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
  (`d149079`, `9d036812eb736d5b…`), `.standards/CONTEXT.md` (`0573e11`,
  `09045f457b2df4c1…`), user style `.standards/user-styles/tester/tony.md`
  (`797def3`, `e64ef290173c7c32…`). Current acceptance set: `AC-001` to
  `AC-042`, none retired.
- Assignment: Increment 1 (`DEV-001`; `AC-041`, `AC-042`) from the plan's
  **Verification Increments** and **Checkpoint: Increment 1**: assess
  Developer's reorder of `src/pydelity/` and `scripts/`, reorder `tests/`, and
  confirm both against `126f52f`, the commit before the reorder.
- Source assessed: `0f4c949`
  (`refactor: put each module's definitions in the agreed order`), whose
  `git diff 126f52f 0f4c949 -- src scripts` (16 files, 667 insertions, 668
  deletions) has SHA-256 `0f21ce5c770d636c…`, the same content as the plan's
  checkpoint claim. `docs/` and `tests/` are unchanged from `126f52f` in that
  commit.
- Tests assessed: `0f4c949` plus this assessment's uncommitted reorder of 16
  test modules (`git diff -- tests`, 1705 insertions, 1706 deletions, SHA-256
  `60f9212d56eab4d4…`). The other working-tree change is this report.
- Environment: macOS 26.6.2 arm64, Python 3.13.9 (`.venv`, strict editable
  install), PyMuPDF 2.1, Pydantic 2.14.3, pytest 9.2.0 with pytest-randomly and
  pytest-xdist, ruff 0.17.5, ty 0.0.105, interrogate 1.7.0. Python 3.14 is not
  installed (`/opt/homebrew/bin` has 3.11–3.13; uv has no managed Pythons).
- Session: started as a Tester invocation with no Developer conversation in it.
  The client cannot certify session freshness; this assessment is built from the
  persisted records and the repository.
- Project references loaded: `NONE` (`.standards/project-references/tester/`
  does not exist).

## Acceptance Evidence

| AC / technical criterion                                                                                                                                                                                                                                                                         | Tests or checks                                                                                            | Disposition and evidence                                                                                                                                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AC-041` / move only: same non-blank lines, top-level statements, class members, field and member order                                                                                                                                                                                          | `ordercheck.py compare 126f52f` on the 56 modules of `src/pydelity/` and `scripts/`; `comments.py 126f52f` | Verified: 56 files, 0 problems; no class had its methods reordered; every definition keeps the comment lines directly above it. See E2, E3.                                  |
| `AC-041` / every module follows **Module order** except the listed departures                                                                                                                                                                                                                    | `ordercheck.py order`; `expected.py` (both constructions); `strict.py`                                     | Verified: departures in exactly the 14 modules the plan lists, each needed (strict order raises `NameError`) and no wider than needed. See E4, E5.                           |
| `AC-041` / pytest, doctests, ruff check, ruff format --check, ty, interrogate as before, on Python 3.13                                                                                                                                                                                          | Existing suite and linters on `0f4c949` with `tests/` unchanged                                            | Verified on 3.13: 177 passed (random-order parallel and serial), same 177 test IDs; 27 doctests passed, 1 skipped, same 28 IDs; every linter as on `126f52f`. See E1, E6.    |
| `AC-041` / the same on Python 3.14                                                                                                                                                                                                                                                               | Same suite on 3.14                                                                                         | Blocked: not run, Python 3.14 is not installed here. See Open Findings.                                                                                                      |
| `AC-041` / reference pages change only by constants order                                                                                                                                                                                                                                        | `generate_reference_docs.py` in a copy of `0f4c949`, then Prettier 3.10.1                                  | Verified: the 11 generated pages are identical to the committed ones. See E7.                                                                                                |
| `AC-042` / move only, as for `AC-041`                                                                                                                                                                                                                                                            | `ordercheck.py compare 126f52f` and `comments.py` on the 32 modules of `tests/`                            | Verified: 32 files, 0 problems; only `MockProviders` had methods reordered; comments stay with their definitions; blank lines differ only where Ruff's import rule asks. E8. |
| `AC-042` / every module follows **Module order** except the listed departures                                                                                                                                                                                                                    | `ordercheck.py order`; `expected.py`; `strict.py`                                                          | Verified: departures in 2 modules, listed below, each needed. See E8.                                                                                                        |
| `AC-042` / the suite runs the same tests with the same results; linters as before, on Python 3.13                                                                                                                                                                                                | Existing suite and linters after the test reorder                                                          | Verified on 3.13: 177 passed (random-order parallel and serial), same 177 IDs; doctests unchanged; ruff, format, ty, interrogate as before. See E9.                          |
| `AC-042` / the same on Python 3.14                                                                                                                                                                                                                                                               | Same suite on 3.14                                                                                         | Blocked: not run, as for `AC-041`.                                                                                                                                           |
| `AC-001`, `AC-002`, `AC-003`, `AC-004`, `AC-005`, `AC-006`, `AC-007`, `AC-008`, `AC-009`, `AC-010`, `AC-011`, `AC-012`, `AC-013`, `AC-014`, `AC-015`, `AC-016`, `AC-017`, `AC-018`, `AC-019`, `AC-020`, `AC-021`, `AC-022`, `AC-023`, `AC-024`, `AC-025`, `AC-028`, `AC-030`, `AC-033`, `AC-034` | Increments 2–4 and `DEV-011`                                                                               | `AWAITING_IMPLEMENTATION`: `DEV-002`–`DEV-011` are `PENDING`.                                                                                                                |
| `AC-026`, `AC-027`, `AC-029`, `AC-031`                                                                                                                                                                                                                                                           | Tests written at Increments 2–4; CI, build and release checks at full verification                         | `AWAITING_IMPLEMENTATION`: they depend on `DEV-002`–`DEV-011`; Tester assesses them at the later increments and full verification.                                           |
| `AC-032`, `AC-035`, `AC-036`, `AC-037`, `AC-038`                                                                                                                                                                                                                                                 | Documentation evidence                                                                                     | Pending a later role: Documenter, with documentation-record evidence for each AC.                                                                                            |
| `AC-039`, `AC-040`                                                                                                                                                                                                                                                                               | The user's review of real runs                                                                             | Pending a later role: the user's accepted real runs on Anthropic and OpenAI, after the build.                                                                                |

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

| Increment | Outcome and acceptance scope                                                                                     | Assessed inputs / evidence                                                                       | Disposition |
| --------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ----------- |
| 1         | `src/pydelity/`, `scripts/` and `tests/` follow **Module order** with the listed departures (`AC-041`, `AC-042`) | `0f4c949` plus test diff `60f9212d56eab4d4…`; E1–E9 pass on 3.13; the Python 3.14 run is missing | BLOCKED     |

## Scenario Budget

| Source file                                                | Reused coverage                                                       | Active-change allocations | User additions |
| ---------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------- | -------------- |
| The 16 reordered modules of `src/pydelity/` and `scripts/` | The existing suite (177 tests, 28 doctest items) as regression checks | 0                         | NONE           |

The reorder adds no behavior, so no scenario is added. The tests reorder moves
existing tests only and creates or removes none (same 177 IDs). The scratch
tools below are not tests and are not in the repository.

## Execution Evidence

Working directory: repo root unless noted. Tools: `.venv/bin`. Scratch tools and
logs live in this session's scratchpad (`tools/ordercheck.py`,
`tools/expected.py`, `tools/strict.py`, `tools/comments.py`, `tools/reorder.py`,
`logs/`), not in the repo. 2026-11-21.

- **E1 — Baseline on `126f52f`.** `git archive 126f52f` extracted to the
  scratchpad; in that copy with `PYTHONPATH=<copy>/src`:
  `python -m pytest -q --numprocesses auto -p no:cacheprovider` exit 1, 176
  passed, 1 failed, 65 warnings. The one failure is
  `test_package_loads_from_installed_tree_not_src`, which fails by design when
  `src` is on the path; it passes on the real checkout (E6), and its source is
  unchanged by the reorder. `--collect-only -p no:randomly`: 177 test IDs (saved
  sorted). `pytest -q --doctest-modules src`: 27 passed, 1 skipped, 28 IDs.
  `ruff check scripts src tests` "All checks passed!";
  `ruff format --check scripts src tests` "89 files already formatted";
  `ty check scripts src tests` "All checks passed!";
  `interrogate scripts src tests` 100.0%. All exit 0.
- **E2 — Move-only comparison, package and scripts.**
  `ordercheck.py compare 126f52f <the 56 .py files of src/pydelity and scripts>`
  exit 0: for each file, the same multiset of non-blank lines, the same multiset
  of top-level statements (`ast.dump`, with methods compared as a multiset), the
  same classes and members, and the same order of every non-method member
  (fields, enum members, validators, docstrings). Raw `ast.dump` multisets are
  also equal (no method moved). Negative controls on mutated copies of
  `costs/schemas.py` (swapped fields, changed text, dropped line) are each
  reported.
- **E3 — Comments stay attached.** `comments.py 126f52f` on all 88 modules of
  `src/pydelity/`, `scripts/` and `tests/`: 0 definitions whose directly-above
  comment lines changed. A negative control with swapped comments is reported.
- **E4 — Order check.** `ordercheck.py order` on `src/pydelity/` and `scripts/`
  reports departures in exactly the 14 modules under **Order departures** in the
  plan, with the same items. Positive control: on the `126f52f` copy it flags 22
  modules, which include all 16 the reorder changed.
- **E5 — Departures are needed and no wider than needed.** `strict.py` executes
  each departure module with its blocks in strict **Module order**: all 12 of
  `cli.py`, `config/schemas.py`, `costs/schemas.py`, `errors.py`,
  `extracting/rendering.py`, `extracting/schemas.py`,
  `extracting/validators.py`, `pipeline/runner.py`, `pipeline/schemas.py`,
  `providers/profiles.py`, `surveying/schemas.py` and `surveying/validators.py`
  raise `NameError` for the dependency the plan names; `surveying/probe.py` (no
  departure) imports. `expected.py` derives the order from **Module order** plus
  eager dependencies: with dependencies moved above their readers it matches
  every schema module, `cli.py`, `rendering.py` and `runner.py`; with a reading
  constant moved below its dependency it matches `extracting/validators.py`,
  `surveying/validators.py` and `providers/profiles.py`. The remaining
  departures are runtime statements: `__init__.py`'s `_logger.disable` (last)
  and `smoke_installed_wheel.py`'s `REPO_ROOT` and `sys.path.insert` before the
  `tests.fixtures` import.
- **E6 — Checks on `0f4c949`, tests unchanged.**
  `pytest -q --numprocesses auto -p no:cacheprovider` exit 0, 177 passed, 65
  warnings; `pytest -q -p no:cacheprovider -p no:randomly` exit 0, 177 passed;
  collected IDs equal to E1's; doctests 27 passed, 1 skipped, IDs equal; ruff,
  format (89 files), ty and interrogate (100.0%) as in E1. `pydelity --help`
  exit 0, `scripts/check_env_template.py` exit 0,
  `scripts/smoke_installed_wheel.py --help` exit 0.
- **E7 — Reference pages.** In a `git archive 0f4c949` copy:
  `python scripts/generate_reference_docs.py` (11 pages), then Prettier 3.10.1
  from `~/.cache/prek` (`prettier --write` on the pages); `diff -r` with the
  committed `docs/src/content/docs/reference/`: identical `.md` files. (The
  checkout also holds an empty, untracked `.claude/.cc-writes` folder there from
  the agent client; not part of the generator.)
- **E8 — Tests reorder.** `tools/reorder.py` splits each test module into blocks
  (decorators, comment lines directly above, attribute docstrings, indented
  trailing comments), refuses any non-blank line outside a block, sorts by
  **Module order** with the dependency rule above, sorts methods in classes
  whose methods follow their other members, and keeps the
  `if __name__ == "__main__":` block last. It changed 16 modules; the other 16
  already followed the rule and were left byte-identical. Then
  `ruff format tests` (no change) and
  `ruff check --fix --select I001 tests/pydelity/extracting/test_validators.py`,
  which removed one blank line after the imports now that a constant follows
  them. Afterwards: `ordercheck.py compare 126f52f` on the 32 test modules exit
  0 (only `tests/fixtures/mock_providers.py` reordered methods, in
  `MockProviders`); blank-line counts per file equal to `126f52f` except that
  one line; `ordercheck.py order` reports only the departures listed above;
  `strict.py` raises `NameError` for `mock_providers.py` (`Provider`) and
  `test_loading.py` (`_REPO_ROOT`), and `test_api.py` (no departure) imports.
  The only autouse fixture is `_no_provider_access` in `tests/conftest.py`, so
  fixture setup order cannot change.
- **E9 — Checks after the tests reorder.**
  `pytest -q --numprocesses auto -p no:cacheprovider` exit 0, 177 passed, 65
  warnings (as in E6); `pytest -q -p no:cacheprovider -p no:randomly` exit 0,
  177 passed; collected 177 IDs equal to E1's; doctests 27 passed, 1 skipped,
  IDs equal; `ruff check` "All checks passed!", `ruff format --check` "89 files
  already formatted", `ty check` "All checks passed!", `interrogate` 100.0%.
- **Not run.** Python 3.14 (not installed; see Open Findings). The `just`
  recipes through `uv` (uv cannot write its cache in the sandbox; the
  `.venv/bin` tools are the pinned versions the recipes run). The wheel smoke
  test (needs `uv build` and package downloads); the reorder changes no
  packaging, and CI's wheel-install jobs run it on push.
- **Developer evidence.** The plan's `DEV-001` self-checks agree with E1–E7;
  they were not used as evidence.

## Open Findings and Dependencies

- Required unrun check: the `AC-041` and `AC-042` technical criteria ask for the
  same results on Python 3.14, and 3.14 is not installed here. Every other part
  of both criteria is verified on 3.13 (E1–E9). Getting the evidence needs a
  user action: either the user commits the tests reorder and pushes the branch,
  so CI's "Test (Python 3.14)" job runs the suite, which Tester then reads with
  `gh`; or the user approves installing Python 3.14 here with uv (a download,
  run outside the sandbox) and a 3.14 environment for a local run.
- Blocking user question, as in `Active Work.BlockedOn`: how to get the Python
  3.14 run for Increment 1.

## Resume or Handoff

Next action: on the user's answer, get the Python 3.14 results for `0f4c949`
plus the tests reorder (or the commit holding it, if its tests diff matches
`60f9212d56eab4d4…`), record them as E10, set Increment 1 `VERIFIED` and the
report `IN_PROGRESS`, clear `Active Work.BlockedOn`, run `check`, and return a
`CHECKPOINT` to Developer for Increment 2 (`DEV-002`, `DEV-003`). If 3.14 shows
a failure, diagnose it and route it under **Defects and Routing**.

Remaining acceptance work after Increment 1: `AC-001`–`AC-040` with Increments
2–4, `DEV-011` and full verification. The tests reorder is ready for the user to
commit on its own, apart from the package reorder.

<!-- STANDARDS
Artifact: VERIFICATION
Cycle: add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada
-->

# Verification Report

`Cycle`: `add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada`
`Mode`: `VERIFY` `Status`: `IN_PROGRESS` `User Style`: `tony`
`Assessment Purpose`: `INCREMENT` `Assessment Target`: `Increment 1`

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
- Tests assessed: this assessment's reorder of 16 test modules, which the user
  committed as `ac9e4cb` (with this report and `STATE.md`; `7bd7f90` changes
  only this report). `git diff 0f4c949 7bd7f90 -- tests` (1705 insertions, 1706
  deletions) has SHA-256 `60f9212d56eab4d4…`, the content assessed in E8 and E9.
  `7bd7f90` is the head of draft pull request 11
  (`https://github.com/IDinsight/pydelity/pull/11`), 0 commits behind `main`.
- Environment: macOS 26.6.2 arm64, Python 3.13.9 (`.venv`, strict editable
  install), PyMuPDF 2.1, Pydantic 2.14.3, pytest 9.2.0 with pytest-randomly and
  pytest-xdist, ruff 0.17.5, ty 0.0.105, interrogate 1.7.0. Python 3.14 is not
  installed (`/opt/homebrew/bin` has 3.11–3.13; uv has no managed Pythons), so
  the 3.14 evidence is CI's: ubuntu-latest, CPython 3.14.4 (E10).
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
| `AC-041` / the same on Python 3.14                                                                                                                                                                                                                                                               | CI "Test (Python 3.14)" on pull request 11; `ty` and `ruff` targeting 3.14                                 | Verified: CPython 3.14.4, 177 passed; doctests 27 passed, 1 skipped; the 3.14-target static results equal `126f52f`'s. See E10, E11.                                         |
| `AC-041` / reference pages change only by constants order                                                                                                                                                                                                                                        | `generate_reference_docs.py` in a copy of `0f4c949`, then Prettier 3.10.1                                  | Verified: the 11 generated pages are identical to the committed ones. See E7.                                                                                                |
| `AC-042` / move only, as for `AC-041`                                                                                                                                                                                                                                                            | `ordercheck.py compare 126f52f` and `comments.py` on the 32 modules of `tests/`                            | Verified: 32 files, 0 problems; only `MockProviders` had methods reordered; comments stay with their definitions; blank lines differ only where Ruff's import rule asks. E8. |
| `AC-042` / every module follows **Module order** except the listed departures                                                                                                                                                                                                                    | `ordercheck.py order`; `expected.py`; `strict.py`                                                          | Verified: departures in 2 modules, listed below, each needed. See E8.                                                                                                        |
| `AC-042` / the suite runs the same tests with the same results; linters as before, on Python 3.13                                                                                                                                                                                                | Existing suite and linters after the test reorder                                                          | Verified on 3.13: 177 passed (random-order parallel and serial), same 177 IDs; doctests unchanged; ruff, format, ty, interrogate as before. See E9.                          |
| `AC-042` / the same on Python 3.14                                                                                                                                                                                                                                                               | As for `AC-041`, with the tests reorder in `7bd7f90`                                                       | Verified: the same CI run tested `7bd7f90`'s content. See E10, E11.                                                                                                          |
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

| Increment | Outcome and acceptance scope                                                                                     | Assessed inputs / evidence                                                                         | Disposition |
| --------- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ----------- |
| 1         | `src/pydelity/`, `scripts/` and `tests/` follow **Module order** with the listed departures (`AC-041`, `AC-042`) | `0f4c949`; tests diff `60f9212d56eab4d4…` (committed in `ac9e4cb`); E1–E9 on 3.13, E10–E11 on 3.14 | VERIFIED    |

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
- **E10 — CI on pull request 11.** `gh pr checks 11 --repo IDinsight/pydelity`
  and `gh run view --job <id> --log` (read-only `gh` calls run outside the
  sandbox, whose proxy fails `gh`'s certificate check). Run `44907613193`, event
  `pull_request`, head `7bd7f90`, checked out as merge commit `0b17fdd` of
  `7bd7f90` into `c7582e7`; the branch is 0 commits behind `main`
  (`gh api .../compare/main...7bd7f90`: ahead 57, behind 0), so the merge holds
  `7bd7f90`'s content. All checks pass: "Test (Python 3.14)" job `136856437295`
  ("Using CPython 3.14.4"; tests "177 passed"; doctests "27 passed, 1 skipped");
  "Lint and test (Python 3.13)" job `136856437680` (CPython 3.13.18; every lint
  recipe, including "STANDARDS check passed.", ruff "All checks passed!", ty
  "All checks passed!", interrogate 100.0%; tests "177 passed"; doctests "27
  passed, 1 skipped"); "Wheel install" on macos-latest, ubuntu-latest and
  windows-latest; "Build the docs"; "TruffleHog secret scan"; "Lint and test".
  "Publish to GitHub Pages" is skipped, as for pull requests.
- **E11 — Static checks targeting 3.14.** Ruff and ty do not run on the
  interpreter, so the project's configured runs (target `py313`) already give
  E9's results under 3.14. As an extra check, on `7bd7f90` and on the `126f52f`
  copy: `ty check --python-version 3.14 scripts src tests` "All checks passed!"
  on both; `ruff check --target-version py314` reports the same 11 `UP037`
  (quoted annotations that 3.13 needs) on both;
  `ruff format --check --target-version py314` "2 files would be reformatted" on
  both. The reorder changes none of these results. Interrogate counts
  docstrings, which the reorder does not change (E2).
- **Not run locally.** Python 3.14 (CI ran it, E10). The `just` recipes through
  `uv` (uv cannot write its cache in the sandbox; the `.venv/bin` tools are the
  pinned versions the recipes run, and CI ran the recipes, E10). The wheel smoke
  test (CI's wheel-install jobs ran it, E10).
- **Developer evidence.** The plan's `DEV-001` self-checks agree with E1–E7;
  they were not used as evidence.

## Open Findings and Dependencies

- None for Increment 1. No defect, unrun check or blocking question remains.
- Later-role dependencies, unchanged: `AC-032`, `AC-035`, `AC-036`, `AC-037` and
  `AC-038` (Documenter, documentation-record evidence); `AC-039` and `AC-040`
  (the user's accepted real runs).

## Resume or Handoff

Increment 1 is `VERIFIED` (E1–E11) and returned to Developer with a
`CHECKPOINT`. The report stays `IN_PROGRESS` until full verification.

Next Tester action: assess Increment 2 (`DEV-002`, `DEV-003`; `AC-001` to
`AC-006`, `AC-018` to `AC-020`) when Developer hands it over, with `REVERIFY` if
the inputs above change. Tests of replaced contracts are expected to fail at
that checkpoint until Tester updates them, as the plan notes. Remaining
acceptance work: `AC-001` to `AC-040` with Increments 2–4, `DEV-011` and full
verification.

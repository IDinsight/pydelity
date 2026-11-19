<!-- STANDARDS
Artifact: VERIFICATION
Cycle: build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c
-->

# Verification Report

`Cycle`: `build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c` `Mode`:
`VERIFY` `Status`: `BLOCKED` `User Style`: `tony` `Assessment Purpose`: `FULL`
`Assessment Target`: `NONE`

## Assessed Inputs

- Scope, design and plan at commit `f8c816b`: scope `8c873b1`, design `e9cd886`,
  development plan `COMPLETE` (DEV-001 to DEV-021 and DEV-023 `DONE`, cadence
  `AFTER_IMPLEMENTATION`, `Current Increment: NONE`). Context:
  `.standards/CONTEXT.md` at `f8c816b`.
- Current acceptance set: `AC-001`, `AC-002`, `AC-004` to `AC-011`, `AC-014`,
  `AC-015`, `AC-017` to `AC-047`. Retired: `AC-003`, `AC-012`, `AC-013`,
  `AC-016`.
- Implementation under test: `src/`, `scripts/` (apart from Tester's smoke-check
  correction below), `examples/`, `docs/` and `.github/` exactly as at `f8c816b`
  (checked with `git diff --quiet f8c816b`). Tester's uncommitted changes: the
  new suite under `tests/` (14 test modules), `tests/conftest.py`, an extended
  `tests/fixtures/mock_providers.py` (a request delay, a wait for the first
  model request, quiet handling of a client that went away, a 0.05 s stop poll),
  and the `test` recipe in `justfile`. The recipe now also runs the docstring
  examples in `src/` in a second pytest session, as the user asked (plan notes),
  and, at the user's request in this session (2026-11-18), runs the tests in one
  worker per CPU with pytest-xdist, added to the dev group as
  `pytest-xdist==3.8.0` (`pyproject.toml`, `uv.lock`; runtime dependencies
  unchanged). With no failure, `KEEP_GOING=1` now keeps each session's summary
  line in `.cache/test-errors`. SHA-256 over `tests/` (PDFs excluded),
  `justfile`, `pyproject.toml` and `uv.lock`: `267053db6cb60db8…`.
- Environment: macOS arm64 (Darwin 25.6.0), Python 3.13.9, the `.venv` from
  `uv.lock` (pytest 9.2.0, pydantic-ai 2.69.0, anthropic 2.10.0, openai 3.53.0,
  PyMuPDF 2.1, genai-prices 0.2.4), Node 23.10.0 and pnpm from
  `docs/package.json` (CI pins Node 24.22.3). Tests that start the stand-in
  provider server bind a loopback port, which this session's sandbox blocks, so
  test runs ran outside the sandbox.
- Reason: first formal verification of the cycle, after Developer's full
  completion and the closed AC-047 recovery frame (`Handoff.Kind: RESUME`).
- Session: this Tester conversation holds no Developer authoring history; client
  metadata cannot certify session freshness.
- Project references loaded: `NONE` (`.standards/project-references/` does not
  exist). Shipped Tester reference loaded: `references/llm-api-testing.md` (the
  change calls Anthropic and OpenAI). Applied through the design's seam: the
  SDKs' base URLs point at the stand-in server, whose bodies follow the
  installed SDKs' response types; an autouse fixture sets placeholder keys and a
  closed port; retries use short `retry-after-ms` waits.

## Acceptance Evidence

Test paths are under `tests/pydelity/`. "Suite" means the run recorded under
Execution Evidence. Every model response comes from the stand-in server; no test
reaches a provider.

| AC     | Tests or checks                                                                                                                                                                                                                                                                                                                         | Disposition                                                                                                        |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| AC-001 | `surveying/test_probe.py` (8 scenarios: text quality none/good/garbled, bookmarks, form values and checkbox states, tags, repeated lines, angle on rotation-0 pages, printed numbers and offsets, unreadable fact); `_normalize` doctest (Cf removal)                                                                                   | VERIFIED. Facts copy in `pdf_survey.json`: `test_profile_owns_other_dedupes_kinds_and_converts_region_boxes`.      |
| AC-002 | `surveying/test_survey.py::test_profile_owns_other_dedupes_kinds_and_converts_region_boxes`                                                                                                                                                                                                                                             | VERIFIED                                                                                                           |
| AC-004 | `test_user_languages_lead_and_rejected_model_tags_become_review_issues`, `test_request_sends_the_facts_as_hints_with_every_repeated_line`; inspection: no setting disables a check or the comparison                                                                                                                                    | VERIFIED                                                                                                           |
| AC-005 | `test_probe.py`: Arabic two columns, Japanese vertical, W-9 filled form with checkboxes, CAPS sideways tables, scanned pages, W-9 instructions with bookmarks and tags, untagged PDFs                                                                                                                                                   | VERIFIED                                                                                                           |
| AC-006 | `test_prompt_schema_and_vocabulary_name_no_document_type`; `grep` of `src/pydelity` for domain words and word lists (only false hits: HTML "terms", API "contract")                                                                                                                                                                     | VERIFIED                                                                                                           |
| AC-007 | `test_cli.py::test_a_pdf_alone_runs_the_survey_with_keys_from_the_environment`; `test_package.py::test_import_reads_no_settings_opens_no_connection_and_prints_nothing`                                                                                                                                                                 | VERIFIED                                                                                                           |
| AC-008 | `config/test_loading.py::test_config_file_paths_resolve_against_its_folder_and_keywords_win`; `test_cli.py::test_the_pdf_argument_wins_over_the_config_file`                                                                                                                                                                            | VERIFIED                                                                                                           |
| AC-009 | `test_every_invalid_setting_is_named_in_one_error_before_any_request`, `test_spellings_of_one_language_tag_resolve_to_one_standard_form`, `test_cli.py::test_invalid_options_are_all_named_and_nothing_runs`                                                                                                                            | VERIFIED                                                                                                           |
| AC-010 | Import test above (empty environment, audit hook: no file opened in the folder, no socket, no output); every API test runs without the CLI                                                                                                                                                                                              | VERIFIED                                                                                                           |
| AC-011 | `providers/test_uploads.py::test_the_pdf_is_uploaded_once_recorded_and_referenced[anthropic,openai]`; `pipeline/test_runner.py::...[model]`                                                                                                                                                                                             | VERIFIED                                                                                                           |
| AC-014 | `test_api.py::test_load_reads_back_what_run_returned_and_costs_add_up`, CLI summary in `test_a_pdf_alone_runs...`, `test_fewer_temporary_failures_than_the_retries_still_complete`, `costs/test_budget.py::test_prices_set_for_a_model_replace...`                                                                                      | VERIFIED                                                                                                           |
| AC-015 | `test_cli.py` non-interactive, no and yes tests; `test_estimate_writes_nothing_and_a_reusable_survey_costs_nothing`; Python API with a stdin that fails on read (`test_earlier_spend_counts...`)                                                                                                                                        | VERIFIED                                                                                                           |
| AC-017 | `test_runner.py`: unchanged inputs reuse, 5 rows of changed input or `overwrite`, new `PROBE_VERSION`                                                                                                                                                                                                                                   | VERIFIED                                                                                                           |
| AC-018 | `utils/test_files.py`, `test_damaged_outputs_and_leftover_temp_files_are_replaced`, `test_ctrl_c_at_the_question_records_an_interrupted_run`, `test_cancelling_arun...`, `test_a_damaged_uploads_file_counts_as_empty`, fallback writes no upload record                                                                                | VERIFIED                                                                                                           |
| AC-019 | `test_checks_still_failing_after_the_retries_are_listed_for_review` (CLI summary by check, step, page)                                                                                                                                                                                                                                  | VERIFIED                                                                                                           |
| AC-020 | `report/test_html.py` (3 scenarios: content and offline, escaping, image reuse)                                                                                                                                                                                                                                                         | VERIFIED                                                                                                           |
| AC-021 | Whole suite: autouse guard (dummy keys, closed loopback port), both providers, uploads, reuse, re-upload, fallback, 401 and 413 stops, rejections, every `max_cost` answer, retries, each public function sync and async                                                                                                                | VERIFIED                                                                                                           |
| AC-022 | Inspection of `.github/workflows/ci.yml` (`gate` "Lint and test" needs `lint-and-test`, `test-py314`, `wheel`, runs `if: !cancelled()`, fails unless all succeed); CI run `44429967364` on `c40b521`: Python 3.13 and 3.14 jobs each 104 passed and 17 doctests passed; the gate failed because the macOS wheel job failed, as designed | PARTIAL: both Python versions pass in CI; a passing gate run awaits the corrected smoke check (see Open Findings). |
| AC-023 | CI run `44429967364` on `c40b521`: `Wheel install (windows-latest)` 13 of 13 smoke checks passed (fresh venv, pip install of the built wheel, `pydelity --yes` and the Python API with both providers against the stand-in)                                                                                                             | VERIFIED on `c40b521`; rerun with the corrected check pending.                                                     |
| AC-024 | `just build` locally and in CI: wheel and sdist pass `twine check --strict`; CI `Wheel install` on ubuntu-latest and windows-latest: 13 of 13 smoke checks; macos-latest: 11 of 13, the 2 failures a defect in the smoke check (corrected, see Open Findings)                                                                           | PARTIAL: clean-environment install passes on Linux and Windows; macOS rerun pending.                               |
| AC-025 | Wheel `METADATA`: summary describes the survey; classifiers Alpha, 3.13, 3.14, Typed, OS independent, Console                                                                                                                                                                                                                           | Metadata VERIFIED; README PENDING Documenter (still the placeholder text).                                         |
| AC-026 | Inspection of `release.yml` (`permissions: {}`, `contents: read` build job, tag equals version, `just build`, only `publish` has `id-token: write`, environment `pypi`, no token); `just lint-workflows`: no findings                                                                                                                   | VERIFIED for readiness; publishing happens after sign-off.                                                         |
| AC-027 | `just docs-build` (11 pages, links checked); a temporary page with a missing page and a missing fragment made `check-links` exit 1, then was removed                                                                                                                                                                                    | VERIFIED                                                                                                           |
| AC-028 | Scratch clone with local tags `v0.1.0` and `v0.2.0` (never pushed): `build-versions.mjs` built both, latest at `/pydelity/`, each at `/pydelity/v/<version>/`, `versions.json`, a version selector; links checked in 33 pages                                                                                                           | VERIFIED                                                                                                           |
| AC-029 | The `docs.yml` plan step run in the scratch clone: push with tag and matching version publishes; pull request, manual run, untagged version and no tags do not; zizmor no findings                                                                                                                                                      | VERIFIED for readiness; deployment happens after sign-off.                                                         |
| AC-030 | `docs/package.json` exact versions and pinned pnpm; Dependabot `npm` for `/docs`; docs pages are `.md` and pass `just lint`                                                                                                                                                                                                             | VERIFIED                                                                                                           |
| AC-031 | —                                                                                                                                                                                                                                                                                                                                       | PENDING Documenter: prose pages; examples then checked against behavior.                                           |
| AC-032 | `just lint` regenerates and formats the 9 reference pages with no diff; spot checks: `advanced.*`, every CLI option, `a`-functions, `load`, facts and survey fields                                                                                                                                                                     | VERIFIED                                                                                                           |
| AC-033 | —                                                                                                                                                                                                                                                                                                                                       | PENDING Documenter: contributor and release pages.                                                                 |
| AC-034 | —                                                                                                                                                                                                                                                                                                                                       | PENDING Documenter: README quick start and docs examples, each checked against the release's behavior.             |
| AC-035 | The user's answer in this Tester session, 2026-11-18: they ran the survey with real Anthropic and OpenAI models on PDFs of their choice covering the required kinds (two-column right-to-left, Chinese or Japanese, tax or fillable form, slide deck or image-heavy, CAPS), reviewed the output and HTML reports, and accept them       | VERIFIED by the user's acceptance                                                                                  |
| AC-036 | `release-please-config.json` and manifest `0.0.1` unchanged; `main` holds no tag and no `feat`, `fix` or breaking commit; release-please 17.6.0 source read independently (manifest fallback, minor bump for `feat` before 1.0)                                                                                                         | VERIFIED for readiness; the 0.1.0 pull request appears after merge.                                                |
| AC-037 | `test_a_pdf_the_provider_rejects_ends_with_its_message` (CLI), `test_a_request_the_provider_rejects_is_sent_once...`, 413 upload stop, fallback rejection; `grep`: no per-model limit figures                                                                                                                                           | VERIFIED                                                                                                           |
| AC-038 | `test_cli.py`: plan-time yes, no, `--yes`, non-interactive; request-time no; earlier spend counted (`test_earlier_spend_counts...`); unpriced with and without `max_cost`                                                                                                                                                               | VERIFIED                                                                                                           |
| AC-039 | `costs/test_budget.py`: disallowed stop then allowed rerun keeping spend, warning logged and recorded, unpriced, request-time stop                                                                                                                                                                                                      | VERIFIED                                                                                                           |
| AC-040 | `test_measure_saves_the_facts_with_no_key_and_reuses_them` (summary at INFO), CLI non-interactive with `--verbose` (saved and logged before the estimate and the question), missing key, `max_cost` stop, failed survey                                                                                                                 | VERIFIED                                                                                                           |
| AC-041 | `providers/test_ledger_model.py` (retries 0 and 3 send 1 and 4 requests, fewer failures complete, 400 sent once); CLI exit 1 with message; uploads tried `1 + retries` times before the fallback                                                                                                                                        | VERIFIED                                                                                                           |
| AC-042 | `test_measure_saves_the_facts_with_no_key_and_reuses_them` (keys removed, provider port closed)                                                                                                                                                                                                                                         | VERIFIED                                                                                                           |
| AC-043 | `test_load_reads_back...`, measured-only folder, missing folder, damaged file                                                                                                                                                                                                                                                           | VERIFIED                                                                                                           |
| AC-044 | Sync functions in a loop (4 rows), `load` in a loop, async parity (4), two `asurvey` in one loop (1 s mock delay each, under 1.8 s together), loop responsiveness, cancelling `arun`                                                                                                                                                    | VERIFIED                                                                                                           |
| AC-045 | `test_validators.py` (C1 to C7 and a passing answer), retry with each failure named, failures after the last attempt in both files                                                                                                                                                                                                      | VERIFIED                                                                                                           |
| AC-046 | `test_answers_that_differ_from_the_facts_are_kept_and_listed_by_page`; unmeasured pages give no issue (scanned PDF)                                                                                                                                                                                                                     | VERIFIED                                                                                                           |
| AC-047 | `test_example_config_holds_every_setting_at_its_default[config.json, config.yaml]`                                                                                                                                                                                                                                                      | VERIFIED                                                                                                           |

Technical criteria notes:

- AC-001 repeated lines: the Cf-removal rule is checked by the `_normalize`
  doctest, which `just test` now runs. No committed or generated PDF yields Cf
  characters in PyMuPDF's extracted text (Base14 fonts replace them, MuPDF maps
  a soft hyphen to `-`), so no end-to-end test covers that rule.
- AC-044 responsiveness: the loop is never blocked for the whole measurement,
  but turns can wait up to about 50 ms on this machine, because PyMuPDF holds
  the GIL while it reads a page. The test asserts the longest wait is under 60%
  of the measurement; measuring on the loop fails it (negative control run).
- AC-041: `retry-after-ms: 1` keeps retries fast; the count assertion holds for
  0 and 3 retries and for the default 2 on uploads and requests.
- Not covered by a test (design detail, no AC of its own): a model refusal or an
  answer cut off at the output-token limit raising `SurveyError`. The stand-in
  server always answers with a normal stop, and `surveying/llm.py` has used its
  budget; an unparseable answer covers the shared `SurveyError` path.

## Scenario Budget

Every source file is new in this cycle; the repo had 2 tests (`test_package.py`,
reused, consuming nothing). User additions: on 2026-11-18, in this Tester
session, the user raised the per-file ceiling to `runner.py` 22, `cli.py` 16,
`api.py` 15, `budget.py` 12, `survey.py` 11, `validators.py` 10, `probe.py` 9,
`uploads.py` 9 and `ledger_model.py` 6, and later raised `survey.py` to 12;
every other file keeps 5.

Counting: each parameter row is a scenario. A scenario is charged to the files
whose behavior it is named for and to any file whose distinct behavior only it
tests. Supporting assertions on behavior another scenario already charges to a
file (such as `run.json` recording `failed` after a provider error) are not
charged again.

| Source file                 | Allocations | Scenarios (test files)                                                                                          |
| --------------------------- | ----------- | --------------------------------------------------------------------------------------------------------------- |
| `__init__.py`               | 1 / 5       | import safety                                                                                                   |
| `__main__.py`               | 1 / 5       | `python -m pydelity --version`                                                                                  |
| `api.py`                    | 15 / 15     | measure, load equals run, sync-in-loop x4, load in loop, async parity x4, survey only, concurrent, loop, cancel |
| `cli.py`                    | 16 / 16     | `test_cli.py` (15) and the review summary in `test_survey.py`                                                   |
| `config/loading.py`         | 4 / 5       | file and precedence, every invalid setting, both example files                                                  |
| `config/schemas.py`         | 3 / 5       | file settings, invalid values, language spellings                                                               |
| `costs/budget.py`           | 12 / 12     | `test_budget.py` (7, the first counts twice) and the 5 CLI `max_cost` tests                                     |
| `costs/ledger.py`           | 2 / 5       | lines and sums, retries add none                                                                                |
| `costs/pricing.py`          | 2 / 5       | price override, unpriced model                                                                                  |
| `errors.py`                 | 1 / 5       | `ProviderError` fields                                                                                          |
| `pipeline/runner.py`        | 18 / 22     | load x4, survey only, cancel, stopped, estimate, reuse, damage, failure, other PDF, secret, summary, CLI states |
| `providers/factory.py`      | 4 / 5       | retry count x2, both providers' models x2                                                                       |
| `providers/ledger_model.py` | 5 / 6       | retries x2, fewer failures, 400 once, request-time check                                                        |
| `providers/profiles.py`     | 2 / 5       | default expiry and purpose per provider x2                                                                      |
| `providers/uploads.py`      | 9 / 9       | `test_uploads.py` (9)                                                                                           |
| `report/html.py`            | 2 / 5       | content and offline, escaping                                                                                   |
| `report/images.py`          | 2 / 5       | images for every page, reuse                                                                                    |
| `surveying/agents.py`       | 3 / 5       | last attempt accepted, retry, failures recorded                                                                 |
| `surveying/facts.py`        | 3 / 5       | save and reuse, new probe version, damaged facts                                                                |
| `surveying/llm.py`          | 5 / 5       | retry request, request content, unparseable answer, re-upload, fallback rejection                               |
| `surveying/probe.py`        | 8 / 9       | `test_probe.py` (8)                                                                                             |
| `surveying/prompts.py`      | 2 / 5       | request content, neutral vocabulary                                                                             |
| `surveying/schemas.py`      | 1 / 5       | neutral field names and enums                                                                                   |
| `surveying/survey.py`       | 12 / 12     | profile, languages, disagreements, spellings, reuse, 5 changed inputs, probe version, damaged survey            |
| `surveying/validators.py`   | 10 / 10     | passing answer, C1 to C7, the two comparisons                                                                   |
| `utils/coroutines.py`       | 5 / 5       | sync in a loop x4, warnings reach the caller                                                                    |
| `utils/files.py`            | 2 / 5       | interrupted write, stale temp removal                                                                           |
| `utils/pdf.py`              | 3 / 5       | empty, not a PDF, password-protected                                                                            |
| `examples/config.json`      | 1 / 5       | example file                                                                                                    |
| `examples/config.yaml`      | 1 / 5       | example file                                                                                                    |

## Execution Evidence

All at the repo root on `f8c816b` plus Tester's uncommitted changes, macOS
arm64, 2026-11-18.

- `.venv/bin/python -m pytest -q` (random order, outside the sandbox): 104
  passed, four runs in a row. One earlier run failed
  `test_event_loop_stays_responsive_while_measuring` while it counted ticks; the
  test now measures the longest wait instead (see the AC-044 note) and passed 6
  repeated runs and every full run since. Superseded: the tick-count version.
- `just test`: 104 passed; then `pytest --doctest-modules src`: 17 passed, 1
  skipped (`open_pdf`'s example is marked to skip). Exit 0.
- `just lint`: exit 0 (Prettier, STANDARDS check, markdownlint, Ruff, ty,
  interrogate 100%, zizmor). `git diff` afterwards showed no change outside
  Tester's files, so the reference pages regenerate identically.
- `just lint-workflows`: "No findings to report".
- `just build`: wheel `pydelity-0.0.1-py3-none-any.whl` and sdist;
  `twine check --strict` PASSED for both.
- `just docs-build`: 11 pages built; "Checked local links and fragments in 11
  HTML pages". Broken-link negative check: exit 1 naming both bad targets.
- Versioned docs build in a scratch clone with local tags: "Built 2
  documentation versions"; 33 pages link-checked; the release marker added for
  `v0.2.0` shows at the root and under `/v/0.2.0/` only.
- Negative controls run and discarded: the import audit hook records a `.env`
  read and a socket connection when they happen; running the probe on the event
  loop fails the responsiveness test.
- Not run: the CI workflows (Python 3.14 job, the wheel job on Windows, macOS
  and Linux, the "Lint and test" gate), the wheel smoke script
  (`scripts/smoke_installed_wheel.py`, which downloads the runtime dependencies
  from PyPI into a fresh environment; the CI `Wheel install` jobs run it), real
  provider calls (AC-035 rests on the user's own runs), publishing and
  deployment (after sign-off by design).
- Parallel runs, after adding pytest-xdist: `just test` 5 times (12 workers):
  104 passed in 7.8-9.1 s each, then 17 doctests passed, 1 skipped; 8 more
  `pytest -n auto` runs in random order: 104 passed each. Serial baseline on the
  same tree: 104 passed in 19.4-19.6 s. A temporary failing test made
  `just test` exit 2 and `KEEP_GOING=1 just test` exit 1 with the failure in
  `.cache/test-errors`; it was then deleted. `uv lock --check`, the git hooks on
  `justfile`, `pyproject.toml` and `uv.lock`, and zizmor pass.
- After marking the tests' fake keys for detect-secrets: Ruff, ty and every git
  hook (`prek run --files` on all changed and new files, detect-secrets
  included) pass; `just test` again 104 passed, 17 doctests passed, 1 skipped.
- CI on draft pull request IDinsight/pydelity#3, head `c40b521` (the user's
  commit of exactly the assessed content: hash `267053db6cb60db8…`, clean tree,
  `src/`, `scripts/`, `examples/`, `docs/` and `.github/` unchanged from
  `f8c816b`), CI run `44429967364`, read with `gh` on 2026-11-18 while it was
  still running: `Lint and test (Python 3.13)`, `Test (Python 3.14)` and
  `Wheel install (ubuntu-latest)` succeeded; `Wheel install (macos-latest)` and
  `Wheel install (windows-latest)` were in progress, so the "Lint and test" gate
  had not run. Docs run `44429967665` (`Build the docs`) and the TruffleHog scan
  succeeded; `Publish to GitHub Pages` was skipped, as the docs workflow intends
  for a pull request.
- The same CI run, finished: `Lint and test (Python 3.13)`, `Test (Python 3.14)`
  (each 104 passed on 2 workers, then 17 doctests passed, 1 skipped) and
  `Wheel install` on ubuntu-latest and windows-latest (13 of 13 smoke checks)
  succeeded. `Wheel install (macos-latest)` failed with 11 of 13: both "Python
  API with (provider): pydelity is the installed copy" checks. Every survey run,
  load and stand-in request check passed there too. The "Lint and test" gate
  then failed, as it must when a needed job fails.
- Diagnosis (test defect, Tester-owned): the smoke script compares the path the
  child reports for `pydelity.__file__` with the venv path from
  `tempfile.TemporaryDirectory`. On macOS the temporary folder is a symbolic
  link (`/var` to `/private/var`), and a venv's Python reports its site-packages
  under the real path, so `is_relative_to` was false although pydelity was the
  installed copy (the log shows `/private/var/.../venv/.../site-packages`).
  Reproduced locally with a venv in a symlinked temporary folder and a stand-in
  package: false as written, true with both paths resolved. Correction: both
  paths are resolved before comparing (`scripts/smoke_installed_wheel.py`,
  uncommitted). The check still fails for a copy imported from outside the venv,
  such as the repo's `src/`. Ruff, ty and interrogate pass on `scripts/`. The
  design assigns the smoke script to Developer as a reusable asset that Tester
  may extend (plan notes); this is a same-state correction of a test check, with
  no change to pydelity, so no recovery frame.

## Open Findings and Dependencies

- Waiting on a CI rerun (AC-022, AC-024; AC-023 to be reconfirmed): the
  smoke-check correction in `scripts/smoke_installed_wheel.py` needs committing
  and pushing to draft pull request IDinsight/pydelity#3. Required evidence on
  the new head commit: every CI job succeeds, including
  `Wheel install (macos-latest)` with 13 of 13 checks and the "Lint and test"
  gate. The draft pull request is not to be merged before sign-off.
- Later-role dependencies: AC-025 README text, AC-031, AC-033 and AC-034, owner
  Documenter, with evidence that each README and docs example matches the
  release's behavior.
- Observation for Reviewer and Documenter (no AC defect): the Python API leaves
  PydanticAI's first-run banner on, so the first `run()` in a process prints it;
  the CLI turns it off, and AC-010 covers import only.

## Resume or Handoff

Next action, once the smoke-check correction is pushed and CI on
IDinsight/pydelity#3 has finished: check that the new head holds exactly the
assessed content plus that correction, read every job's result and the test and
smoke-test logs with `gh`, and record them for AC-022, AC-023 and AC-024.
Diagnose and route any failure under Defects and Routing. When every job passes,
mark this report `COMPLETE` and hand off to Reviewer (`IMPLEMENTATION`);
Documenter's AC-025 README text, AC-031, AC-033 and AC-034 stay pending
downstream.

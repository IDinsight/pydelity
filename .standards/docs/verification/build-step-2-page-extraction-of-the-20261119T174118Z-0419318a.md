<!-- STANDARDS
Artifact: VERIFICATION
Cycle: build-step-2-page-extraction-of-the-20261119T174118Z-0419318a
-->

# Verification Report

`Cycle`: `build-step-2-page-extraction-of-the-20261119T174118Z-0419318a` `Mode`:
`VERIFY` `Status`: `BLOCKED` `User Style`: `tony` `Assessment Purpose`: `FULL`
`Assessment Target`: `NONE`

## Assessed Inputs

- Scope
  `.standards/docs/scope/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a.md`
  (blob `8f6dbf9b42`): current `AC-001` to `AC-064` except retired `AC-015`,
  `AC-023`, `AC-024`, `AC-062`.
- Architecture
  `.standards/docs/specs/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a.md`
  (blob `878aa2339b`), decisions 1–22 and the technical acceptance criteria.
- Context `.standards/CONTEXT.md` (blob `be80a93c12`).
- Development plan
  `.standards/docs/development/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a.md`
  (blob `ee8450ca87`), `COMPLETE`, DEV-001 to DEV-021 `DONE`, cadence
  `AFTER_IMPLEMENTATION`, `Current Increment: NONE`.
- Implementation under test: `src/`, `scripts/`, `examples/`, `docs/`,
  `.github/`, `CHANGELOG.md` and `pyproject.toml` exactly as at `5ecbf9d` on
  `tz6/pipeline-step-2` (`git status` shows changes only under `tests/` and this
  report). Active change: `git diff c7582e7..5ecbf9d` outside `.standards/`,
  `.claude/` and `artifacts/`.
- Tester's changes, uncommitted: 12 modified test files, new
  `tests/pydelity/extracting/` (`conftest.py`, `test_extraction.py`,
  `test_rendering.py`, `test_text_layer.py`, `test_validators.py`) and fixtures
  `canned_answers` (`tests/conftest.py`) and `profile_labels`. SHA-256 over the
  sorted `.py`, `.json` and `.md` files under `tests/` (PDFs excluded):
  `ac1ecfc7db455bdb…`. No change to `tests/fixtures/`.
- Environment: macOS arm64; Python 3.13.9 (repo `.venv`) and CPython 3.14.10 (a
  separate environment from `uv.lock`, `uv sync --locked --python 3.14`). `uv
  run` cannot reach its cache inside the sandbox, so tools run from the
  environments' `bin/` folders. pip, `gh` and prek ran outside the sandbox
  because its network proxy fails their TLS checks or blocks prek's log.
- Reason: first formal verification of this cycle (no earlier report); the
  previous `TESTING` entry was interrupted by recovery frame 1 before a report
  was written. Session metadata is not visible; this chat holds no Developer
  history. It resumed once after a client restart; the work found on disk was
  reviewed before reuse (see Execution Evidence).
- Project references loaded: `NONE` (`.standards/project-references/tester/`
  does not exist). Shipped reference loaded:
  `.claude/skills/tester/references/llm-api-testing.md` guidance applied through
  the existing seam: both SDKs' base URLs point at the stand-in server.

## Acceptance Evidence

Test paths are under `tests/pydelity/`. "Suite" means the runs under Execution
Evidence. Every model response comes from the stand-in server or a test model;
no test reaches a provider.

| AC | Tests or checks | Disposition |
| --- | --- | --- |
| AC-001 | `config/test_loading.py::test_config_file_paths_resolve…` (file `pages: 5, 1-3, 2` → `1-3,5`); `test_cli.py::test_pages_and_no_pause…` (`-p 2`); keyword `pages=` in `extracting/test_extraction.py`; unset selects all (`pipeline/test_runner.py::test_a_rerun_with_unchanged_inputs…`, 2 of 2); `test_page_files_rerun…` (a wider selection sends no survey request) | VERIFIED |
| AC-002 | `test_cli.py::test_invalid_options_are_all_named…` (`-p 1,4-2`); `test_api.py::test_pages_past_the_pdf_stop_every_function…` (`run`, `extract`, `estimate`; nothing written or sent) | VERIFIED |
| AC-003 | `test_cli.py::test_a_pdf_alone_runs_the_survey…` (paused, extraction skipped, how to continue, then the same command reuses the survey and extracts); `run()` returns a `paused` record without an exception (`costs/test_budget.py`, `providers/test_uploads.py`) | VERIFIED |
| AC-004 | `-np` (`test_cli.py::test_pages_and_no_pause…`); keyword `pause=False` (many); file `pause: false` resolves (`test_config_file_paths…`) | VERIFIED |
| AC-005 | `config/test_loading.py::test_each_step_resolves_its_own_model` (2 rows); defaults: `costs/test_budget.py::test_the_estimate_covers_page_extraction…` (`anthropic:claude-opus-5-5`) and the example-config test (`effort: high`); output mode: `extracting/test_extraction.py::test_each_page_request_carries…` (Anthropic: no output format, schema in the instructions; OpenAI: `json_schema` for survey, extractor and verifier) | VERIFIED |
| AC-006 | `config/test_loading.py::test_example_config_holds_every_setting…` (both files, `advanced.extraction` included) | VERIFIED |
| AC-059 | File (`test_config_file_paths…`) and Python (`advanced=` in `test_each_page_request_carries…`, `surveying/test_survey.py`); no CLI option (`test_cli.py::test_the_removed_instructions_option…`) | VERIFIED |
| AC-060 | `test_each_page_request_carries…` (extraction instructions in extractor and verifier instructions only; survey's only in the survey request); `surveying/test_survey.py` (survey instructions in its system message, not in the profile); `test_page_files_rerun…` (blank counts as unset, no heading; new extraction instructions rerun pages, not the survey); `pipeline/test_runner.py` survey-instructions row reruns the survey | VERIFIED |
| AC-061 | `config/test_loading.py::test_the_removed_instructions_setting…` (file, keyword); `test_cli.py::test_the_removed_instructions_option…` (`-i`, `--instructions`, exit 2); no request, nothing written | VERIFIED |
| AC-007 | `extracting/test_extraction.py::test_an_answer_becomes_a_page_file…`; labels check and `no_matching_label` (`extracting/test_validators.py`) | VERIFIED |
| AC-008 | `test_an_answer_becomes_a_page_file…` (ID rule); `test_the_same_answer_gives_the_same_items…` (stored items and containers identical) | VERIFIED |
| AC-009 | Grid-to-points mapping (`test_an_answer_becomes_a_page_file…`); boxes on content after rotation (`extracting/test_rendering.py`); boxes check | VERIFIED for code; box accuracy on real pages rests on the models: PENDING user review (`AC-054`) |
| AC-010 | Reading-order check, 4 rows (`ltr`, `rtl`, `ttb` either column order); the prompt states the page's direction (`test_each_page_request_carries…`); per-page direction from the profile (`test_an_inconsistent_survey…`) | Code VERIFIED; reading order on the named real PDFs depends on the models: PENDING user review (`AC-054`) |
| AC-011 | `extracting/test_rendering.py` (`/Rotate` 90, 180, 270 render like the unrotated original and boxes land on their text; CAPS sideways content renders landscape) | Rendering and mapping VERIFIED; upright reading on real PDFs: PENDING user review (`AC-054`) |
| AC-012 | Content check (`test_validators.py`); `test_an_answer_becomes_a_page_file…` (list entry IDs, table spans and header rows, code text with whitespace unchanged, formula LaTeX, field value) | VERIFIED |
| AC-013 | `test_the_same_answer_gives_the_same_items…` (crop named after its item, cut at 200 DPI); `test_a_page_file_naming_a_missing_crop…`; upright crop (`test_rendering.py`); report shows it | VERIFIED |
| AC-014 | `caption_of` becomes the figure's ID (`test_an_answer_becomes_a_page_file…`); captions check | VERIFIED |
| AC-056 | Container IDs and boxes, items name them (`test_an_answer_becomes_a_page_file…`); containers check; report draws them | VERIFIED |
| AC-016 | Form-fields check (`test_validators.py`); printed-form field value with `fillable_name: null` (`test_an_answer_becomes_a_page_file…`); scanned-form checkbox items (canned answers) | VERIFIED |
| AC-017 | One full-page figure passes every check (`test_validators.py`); five one-figure pages kept with no issues (`test_no_more_pages_run_at_once…`) | VERIFIED |
| AC-018 | Artifacts check by position (`test_validators.py`, 2 scenarios: one covered place passes with differing text; uncovered fails naming places; malformed box ignored without error); furniture places on a turned page (`extracting/test_text_layer.py`); a real header passes every check (`test_each_page_request_carries…`) | VERIFIED |
| AC-019 | `test_an_inconsistent_survey_still_gives_every_page_a_context` (overlapping, gapped and out-of-PDF ranges; repeated, conflicting and unknown artifact IDs) | VERIFIED |
| AC-020 | Inspection: the survey test's 31 domain words matched against `src/pydelity/extracting/*.py` give only the verb "report"; text handling uses Unicode categories (`text_layer.comparison_form`); no setting defaults a direction | VERIFIED (inspection) |
| AC-021 | Retries with every failure, last answer kept, failures listed (`test_cli.py::test_pages_and_no_pause…`: 3 extractor requests, `labels` issue); corrections checked (`test_the_verifier_s_verdict…`) | VERIFIED |
| AC-022 | `test_validators.py`: removed and added line on Arabic, Chinese, Japanese and English pages (8 rows, real text layers) | VERIFIED |
| AC-063 | `test_the_verifier_s_verdict…` (3 rows: text retries to extractor and verifier carry the note; text issues listed only when the extraction is kept without a pass; checks keep them); skipped comparisons (`test_validators.py`; `no_text_layer` and `compared` in page files); no text-layer lines in requests (`test_each_page_request_carries…`) | VERIFIED |
| AC-064 | `test_the_verifier_s_verdict…` (correction failing only `text_added` kept; correction failing `labels` rejected with `verifier` issue naming the item ID) | VERIFIED |
| AC-025 | Verdict, `correction_applied` and `correction_failures` in the page file (`test_the_verifier_s_verdict…`) | VERIFIED |
| AC-026 | `pipeline/test_runner.py::test_run_json_records_each_step…` (`step`, `page_index`, `item_id` in `run.json`); CLI summary line `extraction, page 2, item p0001-001: …` | VERIFIED |
| AC-027 | CLI and `run()` with pause and resume; `test_api.py::test_aextract_runs_the_survey_first…` (`aextract`, `extract`, `load`) | VERIFIED |
| AC-028 | `test_run_json_records_each_step…` (ledger lines with page and agent; per-step and total cost); CLI summary per-step cost | VERIFIED |
| AC-029 | `costs/test_budget.py::test_the_estimate_covers_page_extraction…` (both agents with retries, sums); paused estimate covers only the survey; CLI "Extraction cost estimate" | VERIFIED |
| AC-057 | `test_no_more_pages_run_at_once_than_the_limit` (5 pages, limit 2, at most 2 in flight) | VERIFIED |
| AC-058 | `test_each_page_request_carries…` (one image per request, no PDF or file ID; both providers) | VERIFIED |
| AC-030 | `costs/test_budget.py::test_requests_running_at_once_are_held_to_max_cost_together` (reservations of requests in flight); `test_each_page_image_counts_toward…` (image tokens in a page request's bound stop it unsent) | VERIFIED |
| AC-031 | Unchanged rerun reuses all (`test_runner.py`); `test_page_files_rerun…` (instructions, wider selection, `overwrite`); fingerprint covers all page inputs (inspection of `page_fingerprint`) | VERIFIED |
| AC-032 | Damaged page file regenerated with a warning (`test_run_json_records_each_step…`); missing crop regenerated and leftover temp files removed (`test_a_page_file_naming_a_missing_crop…`); atomic writes (`utils/test_files.py`) | VERIFIED |
| AC-033 | `test_a_failed_page_stops_the_run…` (provider error stops the run, written page kept, report written, next run requests only the missing pages); `test_a_model_that_never_answers…` (`ExtractionError` naming page and role) | VERIFIED |
| AC-034 | `report/test_html.py::test_report_draws_extracted_items_numbered…` | VERIFIED |
| AC-035 | `surveying/test_probe.py` (checkbox without appearances; one unreadable widget; radio group all off with a value) | VERIFIED |
| AC-036 | `test_letter_page_labels_give_no_page_number` | VERIFIED |
| AC-037 | `test_structure_kids_stored_in_a_separate_array…`, `test_structure_walk_cut_short…`, `test_tagged_pages_without_text…` | VERIFIED |
| AC-038 | `test_outline_with_a_cycle_keeps_the_bookmarks_before_it` | VERIFIED |
| AC-039 | `surveying/test_survey.py::test_an_answer_that_never_parses…` (`pdf_transport: upload` on the failed step) | VERIFIED |
| AC-040 | `test_api.py::test_the_python_api_turns_off_pydantic_ai_s_first_run_banner` | VERIFIED |
| AC-041 | `costs/test_budget.py::test_a_cache_price_of_zero_is_priced_as_zero` | VERIFIED |
| AC-042 | `ci.yml` step run locally: an untracked reference page fails it (exit 1), a clean tree passes; `docs.yml` plan step's Node script run with no tags (0) and with tags (2), and its errors are not redirected; comments match the pnpm cache behavior | VERIFIED |
| AC-043 | Inspection: `CHANGELOG.md` links `c63d891`; `pyproject.toml` lacks the `def cli` exclusion and the `__init__.py` omit | VERIFIED |
| AC-044 | — | PENDING Documenter: the listed docs wording fixes. |
| AC-045 | Suite: 175 tests, stand-in or test models only; an autouse fixture points both providers at a closed port | VERIFIED |
| AC-046 | `ci.yml` inspection (3.13 and 3.14 test jobs gate "Lint and test"); `gh api …/rules/branches/main` lists "Lint and test" and "TruffleHog secret scan"; suite passes locally on 3.13.9 and 3.14.10 | BLOCKED: no CI run yet (CI runs on pull requests to `main`; none exists) |
| AC-047 | Local smoke test on macOS 13 of 13 | BLOCKED: needs the Windows wheel job of a CI run |
| AC-048 | `uv build` then `twine check --strict` PASSED (wheel and sdist); smoke test in a fresh venv with pip from PyPI, 13 of 13 | VERIFIED locally; CI's three-OS wheel jobs pending the same run as AC-046 |
| AC-049 | Wheel metadata `Summary` describes surveying and extracting pages; classifiers unchanged | Metadata VERIFIED; README PENDING Documenter |
| AC-050 | Inspection: `release-please-config.json`, `.release-please-manifest.json` (`0.1.1`) and `release.yml` unchanged since `c7582e7` | VERIFIED (configuration); release itself happens after merge, outside in-cycle evidence |
| AC-051 | — | PENDING Documenter: guides; Reviewer then checks them against behavior. |
| AC-052 | `generate_reference_docs.py` then the Markdown formatter leaves `docs/` unchanged (11 pages, `page-json.md` and `extraction-checks.md` included); CI fails on stale or untracked pages (AC-042) | VERIFIED |
| AC-053 | — | PENDING Documenter: README quick start and examples, each checked against 0.2.0 behavior. |
| AC-054 | — | PENDING the user: real Anthropic and OpenAI runs on the PDFs the scope names, reviewed and accepted before sign-off. |

## Scenario Budget

User addition (2026-11-20, this Tester session): the user approved raising the
per-file ceiling to `extracting/validators.py` 23, `extracting/extraction.py`
16, `pipeline/runner.py` 10, `extracting/text_layer.py` 9,
`surveying/probe.py` 8 and `extracting/rendering.py` 7; every other file keeps
5. Each parameter row counts. A scenario is charged to every file whose
active-change behavior it materially verifies; supporting assertions on behavior
another scenario already charges to a file are not charged again. Updating an
existing test to the replaced contract (24 tests, listed in the plan's handoff)
reuses its allocation.

| Source file | Allocations (new scenarios) | Where |
| --- | --- | --- |
| `extracting/validators.py` | 23 of 23 | `extracting/test_validators.py` |
| `extracting/extraction.py` | 16 of 16 | `test_extraction.py` 14 (failed page; missing crop; temp cleanup; page file; inconsistent survey; concurrency; instructions rerun; wider selection; `overwrite`; same items; crop; verdict ×3); `test_runner.py` 2 (unchanged reuse; damaged page file) |
| `pipeline/runner.py` | 10 of 10 | unchanged reuse; multi-step `run.json`; step-attributed warning; failed page record; pause and resume (CLI); `-p`/`-np` (CLI); pages past the PDF; estimate with extraction; `load` with page files; damaged page file in `load` |
| `extracting/text_layer.py` | 9 of 9 | 8 text rows; `test_text_layer.py` 1 |
| `surveying/probe.py` | 8 of 8 | `surveying/test_probe.py` |
| `extracting/rendering.py` | 7 of 7 | `extracting/test_rendering.py` |
| `config/schemas.py` | 5 | removed instructions ×2; model resolution ×2; blank instructions |
| `cli.py` | 5 | pause and resume; `-p`/`-np` summary; `-i`, `--instructions`; malformed `-p` |
| `api.py` | 4 | `aextract`/`extract`/`load`; damaged page file; pages past the PDF; banner |
| `extracting/llm.py` | 3 | request contents ×2; no usable answer |
| `extracting/agents.py` | 3 | extractor text retry; verifier text retry; retries then kept with issues |
| `extracting/prompts.py` | 3 | request contents ×2; no heading when blank |
| `costs/budget.py` | 3 | reservations; image tokens; estimate with extraction |
| `providers/profiles.py` | 3 | request contents ×2; image tokens |
| `providers/factory.py` | 2 | request contents ×2 |
| `report/html.py` | 1 | extracted page card |
| `costs/pricing.py` | 1 | cache price 0 |
| `surveying/survey.py`, `surveying/llm.py` | 1 | transport on a failed step |

## Execution Evidence

All commands from the repository root; `.venv/bin/` is Python 3.13.9 and
`$TMPDIR/venv314/bin/` is CPython 3.14.10, both from `uv.lock`.

- Baseline at `5ecbf9d` before Tester changes:
  `.venv/bin/python -m pytest --numprocesses auto -q`: 24 failed, 81 passed,
  matching the plan's list of tests on the replaced contract.
- `.venv/bin/python -m pytest --numprocesses auto -q` (random order, xdist):
  175 passed, 0 failed, 0 skipped; repeated 3 times with new seeds, all passing.
  The timing-sensitive tests (concurrency, failed page) passed 5 of 5 runs alone.
- `$TMPDIR/venv314/bin/python -m pytest --numprocesses auto -q`: 175 passed.
- `.venv/bin/python -m pytest --doctest-modules src -q`: 27 passed, 1 skipped
  (marked `+SKIP` in the source); same on 3.14.
- `ruff check`, `ruff format --check`, `ty check` on `scripts src tests`: no
  problems; `interrogate scripts src tests`: 100%.
- Negative controls: with `extraction.TEXT_CHECKS` emptied, the verdict test's
  `passed` and `correction_kept` rows fail; with the text retry note changed, all
  three rows fail. The text rows assert that the correct answer passes and the
  changed one fails on each page.
- `UV_CACHE_DIR=$TMPDIR/uv-cache uv build --out-dir $TMPDIR/dist`, then
  `.venv/bin/twine check --strict`: wheel and sdist PASSED.
- `python scripts/smoke_installed_wheel.py --wheel <wheel>` (outside the sandbox,
  fresh venv, pip from PyPI): 13 of 13 checks passed on macOS (both providers,
  CLI and Python API, survey and extraction, all requests to the stand-in).
- `python scripts/generate_reference_docs.py` then `prek exec prettier-markdown
  -- node scripts/format_markdown.mjs`: `git status docs` clean. The formatter
  also reflowed the plan and `STATE.md`; both were restored to their committed
  text (whitespace only).
- `gh run list --branch tz6/pipeline-step-2`, `gh pr list --head …`: no runs, no
  pull request. CI triggers only on pull requests to `main` and pushes to `main`.
- Work from before the client restart (the 24 updated tests, new budget, runner,
  API, CLI and report tests, and the probe, rendering, validator and text-layer
  tests written by helper agents) was read and rerun in this session; it is
  covered by the results above.
- Developer self-checks were not used as evidence.

## Open Findings and Dependencies

- Blocking user action (`Active Work.BlockedOn`): `AC-046` and `AC-047` need a
  CI run, which happens only on a pull request to `main`. The test changes must
  be committed and pushed, and a draft pull request opened, so that "Lint and
  test" (3.13, 3.14, wheel jobs on ubuntu, macOS, Windows) runs. `AC-048`'s
  three-OS evidence comes from the same run.
- PENDING Documenter: `AC-044`, the README part of `AC-049`, `AC-051`, `AC-053`.
- PENDING the user: `AC-054` real runs and review, which also carry the
  model-dependent parts of `AC-009`, `AC-010` and `AC-011`.
- No implementation, upstream or verification defect found.

## Resume or Handoff

Next action: once the CI run on the draft pull request finishes, record its run
ID and the results of "Lint and test", "Test (Python 3.14)" and the three
"Wheel install" jobs for `AC-046`, `AC-047` and `AC-048`, check the tested head
matches `5ecbf9d` plus these test changes, rerun `check`, mark the report
`COMPLETE` if all pass, and hand off to Reviewer (`IMPLEMENTATION`). A failure
there is diagnosed and routed under the defect table.

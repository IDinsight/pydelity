# Project Context

## Project Baseline

- pydelity is a Python library and CLI that turns a PDF into faithful,
  structured JSON through a planned six-step pipeline. Two steps exist and ship
  in 0.2.0: the survey (step 1) and page extraction (step 2), each with an
  opt-in verifier. Steps 3–6 (page-break verification, assembly, schema
  proposal, projection) have no code.
- The baseline is 0.2.0 as merged. `main`, `origin/main` and tag `v0.2.0` are
  all `7dc2cba` (the release-please commit, pull request 15); the feature squash
  commit is `0c7e5ce` (pull request 14). `pyproject.toml`,
  `.release-please-manifest.json` and `CHANGELOG.md` say `0.2.0` (2026-11-22).
  PyPI publication is user input only; the sandbox blocks GitHub and PyPI.
- Branch `tz6/pipeline-step-3` is 2 commits ahead of `main` (`ac53add`,
  `d3f1221`): the STANDARDS installation, `AGENTS.md`, `CLAUDE.md`, and
  `artifacts/next_cycle_inputs.md` filling in pull request 14. It has no code,
  test, docs or config difference from `main`.
- Code on `main` matches the verifier cycle's sign-off commit `af1b2d1`, apart
  from release metadata and the rewritten `next_cycle_inputs.md`. No dependency
  changed in the verifier cycle or the release.
- Three earlier cycles, with records only in git history:
  `build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c` (survey,
  commit `83743ef`),
  `build-step-2-page-extraction-of-the-20261119T174118Z-0419318a` and
  `add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada` (both at
  `af1b2d1`). Read them with `git show <commit>:.standards/docs/<kind>/<id>.md`
  (reviews at `.standards/docs/reviews/<id>/<kind>.md`). The verifier cycle's
  design sets the checks-and-hints split, the settings, the verdict shapes and
  the estimate rules that step 3 follows. Its scope has 54 conditions. The
  context at `af1b2d1` dates from that cycle's start (`0573e11`) and predates
  its changes. This file replaces it.
- Inputs: `artifacts/next_cycle_inputs.md` (newer; wins where it differs from
  the brief) and `artifacts/design_brief.md`, whose step 3 section starts at
  line 334, evidence E1–E10 at line 536, and open questions at line 648.
  `next_cycle_inputs.md` answers question 12: step 3's Architect picks the
  design without a measured comparison first. Options A–D are inputs, not a
  closed list, and option E is out, since pages carry no continuity marks.
- Terminology differs. In pydelity's code and docs, the "verifier" is an
  optional second request to the step's own model that reviews an answer and may
  return a full correction. The brief uses "verifier" for step 3's main
  per-break judgment and "validator" for the second reviewing model.

## Stack and Tooling

- Python `>=3.13`; `.python-version` is `3.13`; classifiers list 3.13 and 3.14
  only. The local `.venv` runs Python 3.13.9.
- Runtime dependencies are minimum versions in `pyproject.toml`: `genai-prices`
  0.2.4, `langcodes` 3.5.1, `loguru` 0.8.0, `pydantic` 2.14.3,
  `pydantic-ai-slim[anthropic,openai]` 2.69.0, `pydantic-settings[yaml]` 2.16.3,
  `pymupdf` 2.1, `typer` 0.29.1. `uv.lock` also holds `anthropic` 2.10.0,
  `openai` 3.53.0 and `onnxruntime` 1.32.0, which PyMuPDF 2.x pulls in.
- Build: setuptools (`>=77`, kept by hand), src layout, console script
  `pydelity = "pydelity.cli:main"`, and `python -m pydelity`. uv
  (`required-version = ">=0.8.1"`; CI pins `0.13.8`).
- Dev tools are pinned exactly: ruff, ty, interrogate, pytest (9.2.0) with
  pytest-xdist, pytest-randomly and pytest-cov, prek, rust-just, twine, zizmor,
  detect-secrets.
- Docs site: Astro Starlight under `docs/` with pnpm and versioned builds. Node
  `24.22.3` is pinned by hand in `.pre-commit-config.yaml` and `docs.yml`.
- `just` recipes run under bash
  (`set shell := ["bash", "-euo", "pipefail", "-c"]`).

## Structure and Boundaries

- `src/pydelity/__init__.py` — public re-exports: `run`, `survey`, `extract`,
  `measure`, `estimate` with `a`-prefixed async twins, `load`, `Config`,
  `CostEstimate`, `PageFile`, `PdfFacts`, `PdfSurvey`, `RunRecord`, `RunResult`
  and the errors.
- `src/pydelity/api.py` — the public functions; `arun_with_questions` serves the
  CLI. `src/pydelity/cli.py` — one Typer command: `PDF`, `--config` `-c`,
  `--language` `-l`, `--pages` `-p`, `--output-dir` `-d`, `--model` `-m`,
  `--max-cost` `-mc`, `--overwrite` `-o`, `--no-pause` `-np`, `--verify` `-vf`,
  `--yes` `-y`, `--verbose` `-v`, `--version`, `-h`.
- `src/pydelity/config/schemas.py` — `Config` (`advanced`, `languages`,
  `max_cost`, `model`, `output_dir`, `overwrite`, `pages`, `pause`, `pdf`,
  `verify` default `False`; `extra="forbid"`), with properties `survey_model`,
  `extraction_model`, `output_folder`, `verify_survey` and `verify_extraction`.
  `AdvancedConfig` has `extraction`, `models`, `provider_retries`, `survey` and
  `uploads`. `SurveyConfig` and `ExtractionConfig` both have `check_retries`
  (0–5, default 2), `effort` (`high`), `instructions`, `max_output_tokens`
  (32,000), `request_timeout_seconds` (900 and 600) and `verify`
  (`bool | None`). `ExtractionConfig` adds `concurrent_pages` (1–32, default 8)
  and `model`. `config/loading.py` `resolve_config` merges keywords over the
  file over the defaults.
- `src/pydelity/surveying/` — the survey. `probe.py` (facts, `PROBE_VERSION` 1,
  `_walk_structure`, `line_boxes`), `facts.py`, `prompts.py` (`PROMPT_VERSION`
  1, `survey_pdf`, `verify_survey`), `agents.py` (`create_survey_agent`,
  `create_verifier_agent`), `llm.py` (`SURVEYOR`, `VERIFIER`, `ask_model`,
  `ask_verifier`), `validators.py`, `schemas.py` and `survey.py`.
- `src/pydelity/extracting/` — page extraction:
  - `extraction.py`: `page_context`, `page_inputs`, `page_fingerprint`,
    `plan_pages`, `extract_pages`, `request_sizes`,
    `request_sizes_before_survey`, `page_file_path`, `PAGES_FOLDER_NAME`
    (`pages`) and `FIGURES_FOLDER_NAME` (`figures`).
  - `llm.py`: `EXTRACTOR`, `VERIFIER`, `StepModel`, `PageInput`, `ask_extractor`
    and `ask_verifier`.
  - `agents.py`, `prompts.py` (`PROMPT_VERSION` 1, `extract_page`,
    `verify_page`), `rendering.py`, `text_layer.py`, `validators.py` and
    `schemas.py`.
  - It imports from `surveying`, and `surveying` never imports `extracting`.
- `src/pydelity/review.py` — `CheckFailure`, `ReviewIssue` and the name types
  `StepName` (`survey`, `extraction`), `SurveyCheckName`, `SurveyHintName`,
  `ExtractionCheckName`, `ExtractionHintName`, `ExtractionIssueName`
  (`no_matching_label`), `VerifierIssueName` (`verifier`) and their union
  `IssueName`. The check and hint names are part of the `run.json` contract.
- `src/pydelity/pipeline/runner.py`:
  - Public functions: `run_pipeline`, `run_survey_step`, `run_extraction_step`,
    `run_estimate`, `run_measure` and `load_run`.
  - Private helpers: `_steps`, `_survey`, `_extraction`, `_Step`, `_Run`,
    `_review`, `_selected_pages`, `_step_model` and `_load_pages`.
  - Step-name constants: `_SURVEY_STEP` and `_EXTRACTION_STEP`.
  - `pipeline/schemas.py` defines `RunRecord`, `StepRecord`, `PageCounts`,
    `RunCost` and `RunResult`.
- `src/pydelity/costs/` — `budget.py` (`SpendGuard`, `estimate_survey`,
  `estimate_extraction`, `estimate_run`, `PageRequestSize`, typical-token
  constants), `ledger.py`, `pricing.py` and `schemas.py` (`StepEstimate`,
  `CostEstimate`, `LedgerEntry`).
- `src/pydelity/providers/`:
  - `profiles.py`: `DEFAULT_SURVEY_MODEL` and `DEFAULT_EXTRACTION_MODEL`, both
    `anthropic:claude-opus-5-5`; `ModelChoice`; `ProviderProfile` with image
    limits, `image_detail` and `output_mode`; `parse_model`.
  - `factory.py`: `build_model` and `output_mode`.
  - `ledger_model.py`: `LedgerModel` with `for_agent` and `for_page`, and
    `LedgerContext`.
  - `uploads.py`.
- `src/pydelity/report/` — `html.py` writes `report.html`, and `images.py`
  writes the report's page images.
- `src/pydelity/utils/` — `files.py` (atomic writes, validated loads, temp-file
  cleanup), `fingerprints.py`, `pdf.py`, `coroutines.py` (`warn`,
  `running_step`, `run_sync`), `prompts.py` (`PromptPair`) and `text.py`.
- `src/pydelity/schema_versions.py` — one constant per output file, all `"1.0"`:
  facts, ledger, manifest, page, run, survey and uploads.
- `src/pydelity/errors.py` — `PydelityError` and its subclasses, including
  `ExtractionError`, `SurveyError`, `ProviderError` and `BudgetExceededError`,
  plus `PydelityWarning` and the CLI `ExitCode`.
- `scripts/generate_reference_docs.py` generates the docs reference pages; CI
  fails on stale ones. `scripts/smoke_installed_wheel.py` runs the built wheel
  against the stand-in providers.
- Docs: `docs/src/content/docs/guides/` covers command line, configuration,
  costs, models and providers, outputs, page extraction, Python, reruns and
  verifiers. `reference/` holds the generated pages: CLI, configuration, Python
  API, `cost.jsonl`, `pdf_facts.json`, `pdf_survey.json`, page file, `run.json`,
  `uploads.json`, survey checks and extraction checks.
- `examples/config.json` and `examples/config.yaml` hold every setting at its
  default.
- Git-ignored local folders (`data/`, `pydelity-output/`, `graveyard/`,
  `build/`) are not part of the baseline.

## Nearest Analogues

- Page extraction is the nearest analogue for a step that works page by page and
  writes one file per unit:
  - `extracting/extraction.py` `plan_pages` computes each unit's inputs and
    fingerprint, then loads and reuses valid matching files.
  - `extract_pages` runs units concurrently (`concurrent_pages`) on one
    `PdfWorker`, cancels the rest on the first failure, and writes each file
    atomically through `on_written`.
  - `_extract_page` runs the producer, then the verifier when `StepModel.verify`
    is set. `_kept_answer` then applies the verdict, and `_page_issues` builds
    the review issues.
  - Tests are in `tests/pydelity/extracting/test_extraction.py`, which has its
    own `conftest.py`.
- The opt-in verifier is the analogue for a per-unit reviewing request:
  - `extracting/agents.py` `create_verifier_agent` sets output type
    `VerifierVerdict` and `retries={"output": check_retries}`. Its output
    validator checks `verdict.corrected` and raises `ModelRetry` while retries
    remain.
  - `prompts.py` `verify_page` builds the verifier's own system message. Its
    user message adds the answer as JSON (`The extraction to review:`), the hint
    differences and the failing checks.
  - `schemas.py` defines `VerifierVerdict` (`passed`, `problems`, `corrected`)
    and `PageVerification` (`attempts`, `correction_applied`,
    `correction_failures`, `verdict`). `PageFile.verification` is `None` when no
    verifier ran.
  - A correction is kept when it passes every check, whatever its hint
    differences (`_kept_answer`).
- The model-call wrapper is `extracting/llm.py`:
  - `_content` sends `[text, image, CachePoint()]`, with the provider's image
    `detail`.
  - `_model_settings` turns on `anthropic_cache_instructions` for Anthropic.
  - `_run` maps a refusal (`ContentFilterError`), used-up output tokens
    (`OutputTokenLimitExceeded`) and no usable answer
    (`UnexpectedModelBehavior`) to `ExtractionError`, naming the page and the
    agent.
- The survey is the analogue for one request about the whole PDF that carries
  the uploaded PDF. `surveying/llm.py` `ask_model` and `_run_with_upload` reuse
  or refresh the upload in `uploads.json` and fall back to sending the PDF
  inline.
- KGForEdGlobal's step 3 (read-only,
  `/Users/tzz/Projects/private/idi/KGForEdGlobal`, commit `5e2d7cc`, under
  `backend/src/kgfeg/`) is the port source. Facts from `page_ir_verification/`
  and `entries/verify_page_ir_continuity.py`:
  - Per break, Python picks up to 3 bottom anchors on page N and 3 top
    candidates on page N+1 by box y-order, capped at 9 pairs
    (`verify_page_pairs.py`). It skips a break when either page has no items.
  - Each pair gets two sequential `run_sync` requests: a verifier, then a
    validator that always runs. A failed validation's `corrected_verdict`
    replaces the verdict (`llm.py`). The run has no concurrency.
  - Each request sends the full page N render (the extraction's PNG, 250 DPI
    default) and a top crop of page N+1 down to the candidate item plus 120 px
    padding. It also sends compact JSON excerpts of the candidates, with the
    extractor's boundary hints stripped.
  - `PageIRContinuityVerdict` (`schemas.py:18`) has `confidence`,
    `continuation_kind` (`figure`, `none`, `table`, `text`), `is_continuation`,
    `rationale`, page indexes and `set_next_table_repeats_header`
    (`bool | None`). It has no header-row count, no join rule, no continuation
    marker and no item references; Python tracks the pair by item index.
  - Settings (`schemas.py:3489–3521`): `min_confidence_to_patch` 0.75,
    `min_confidence_to_select_positive` 0.50,
    `min_confidence_to_stop_negative_search` 0.95, `next_page_crop_padding_px`
    120, and `verification_auto_stitch_confidence` 0.75. The last one is an
    assembly setting.
  - Assembly applies the verdicts in `document_ir/compute_page_break_links.py`.
    Below the confidence threshold, it falls back to a heuristic linker, which
    E1 says can go.
  - Language and layout assumptions to leave out:
    - English, curriculum-flavored prompt wording with a
      `## RUNTIME CURRICULUM INSTRUCTIONS` hook for per-document rules.
    - Candidates in top-to-bottom order only.
    - Page-number noise regexes.
    - Latin-only sentence ends at `document_ir/stitch_segments.py:994`.
    - A Latin-letter header score.
    - Resume by file existence, and non-atomic writes.
  - Its API differs from pydelity's: pydantic-ai 1.63 (`output_retries=`,
    `run_sync`), Pillow crops and PNG pages. Its table post-processing in
    `postprocess_page_irs.py` is tied to its old table format.

## Commands

- `just install` — runs `uv sync --locked`, then `uv run --locked prek install`.
- `just lint` — runs `docs-reference`, then `lint-markdown`, `lint-python`
  (`ruff check --fix`, `ruff format`, `ty check`, `interrogate`) and
  `lint-workflows` (zizmor).
- `just test` — runs pytest in parallel with `--exitfirst`, then the docstring
  examples (`--doctest-modules src`).
- `just build`, `just docs`, `just docs-build`, `just docs-reference` — build
  the wheel, serve or build the docs, or regenerate the reference pages.
- `.venv/bin/python -m pytest -q --numprocesses auto -p no:cacheprovider`, then
  `.venv/bin/python -m pytest -q --doctest-modules src -p no:cacheprovider` —
  run the tests without uv, where the sandbox blocks uv's cache.
- `uv run --locked python scripts/smoke_installed_wheel.py` — runs the wheel
  smoke test.
- `python -m tests.fixtures.mock_providers --answer <file> --page-answers <file>`
  — runs the stand-in provider server by hand.
- `node .standards/bin/check.mjs` — runs the STANDARDS consistency check. It
  exists only while STANDARDS is installed.

## Conventions and Constraints

- Code style is enforced in `pyproject.toml`:
  - Ruff with line length 88, the rule families ANN, B, C4, C90, D, E, F, I, PL,
    PT, RET, RUF, S, SIM, UP and W, and McCabe complexity at most 10.
  - NumPy docstrings.
  - Import sections "Future Library", "Standard Library", "Third Party Library",
    "Package Library" and "Local Folder".
  - interrogate at 100% and ty over `scripts`, `src` and `tests`.
- The user styles hold the code conventions. They are in
  `artifacts/user-styles/<role>/tony.md`, with identical copies under
  `.standards/user-styles/`:
  - Constants and type aliases come first, then private before public, each
    group alphabetical.
  - Multi-argument calls use keyword arguments in alphabetical order.
  - Docstrings use plain language with no stock AI phrasing, in American
    English.
  - Each step's checks go in `<step>/validators.py`, and prompts return a
    `PromptPair`.
  - `justfile` recipes and `pyproject.toml` tables are alphabetical.
- Shipped code, config, docstrings and docs never mention the development
  process: no dates, DEV or AC IDs, cycles, STANDARDS roles, KGForEdGlobal, or
  numbered steps. Name the step, as in "page-break verification".
- New step folders under `src/pydelity/` take "-ing" names: `verifying/` comes
  next. Each holds `agents.py`, `llm.py`, `prompts.py`, `validators.py` and
  `schemas.py` beside the step module. Outputs, logs and estimates name a step
  with a noun. The user approves new names of settings, CLI options, files and
  folders before the build step that creates them.
- The user decisions for later steps are in `next_cycle_inputs.md` **User
  decisions that apply to later steps**. They include:
  - Acceptance rests on the user's real runs on Anthropic and OpenAI.
  - The document-type-agnostic rule.
  - The checks-and-hints rule.
  - One structured-output mode per provider.
  - No per-model limits.
  - The spending question and `max_cost` behavior.
  - The PDF transport rule.
  - Async twins.
  - PyMuPDF 2.x on one worker thread.
  - No backwards compatibility.
  - Short forms for every CLI option.
  - Python 3.13 and 3.14.
  - The release-please rules.
  - Test PDFs under 500 KB that the user approves.
  - Developer working `STEPWISE` while the user makes the commits and Tester
    owns the tests.
- Items still open for this cycle's Scoper and Architect are under **Open for
  step 3's Scoper and Architect**:
  - The options A–D and validator coverage.
  - Breaks under a narrowed `pages` selection.
  - Settings, output files and the fingerprint over two page files.
  - Joins inside list entries and table cells.
  - The release.
  - Whether reviews keep the major-issues-only bar.
- The **Pushed to later steps** entries that apply to step 3 are:
  - Pauses: each later step adds its own pause under `pause`.
  - Model per step: an optional `advanced.<step>.model`.
  - Verifier per step: an optional `advanced.<step>.verify`, a
    `Config.verify_<step>` property, `verification: null` when none ran, and an
    estimate that prices the verifier only when it runs.
  - Instructions per step: `advanced.<step>.instructions`.
  - Another PDF's page files in a reused folder: skip page files whose
    `inputs.pdf_sha256` differs, and decide about page files kept for a narrowed
    selection.
- `PROBE_VERSION`, each `PROMPT_VERSION` and every output `schema_version` stay
  at 1 or `"1.0"`. When to raise them is undecided.
- Output files are written atomically, validated on load, and carry a
  `schema_version`. A file from another major version is rejected.
- Commits follow Conventional Commits and carry no `Co-Authored-By` trailer or
  other AI attribution. Repo tooling must work without `.standards/`. "Lint and
  test" and "TruffleHog secret scan" are required checks on `main`. Work merges
  to `main` only after sign-off and after STANDARDS is uninstalled on the
  branch.
- The reviews of 0.2.0 raised only major issues. Whether step 3's reviews keep
  that bar is for the user to say (`next_cycle_inputs.md`).

## External Systems and Data

- Providers: Anthropic and OpenAI through PydanticAI, named
  `<provider>:<model-id>`.
  - Both steps default to `anthropic:claude-opus-5-5` at effort `high`.
  - The survey uses `model`. Page extraction uses `advanced.extraction.model`,
    else `model`.
  - Keys come only from `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`.
  - Structured output is prompted on Anthropic and native on OpenAI
    (`ProviderProfile.output_mode`).
- PDF transport, survey only: the provider file upload recorded in
  `uploads.json`, falling back to inline. Page extraction sends its own page
  images, never the PDF.
- Page images:
  - Upright JPEGs at quality 90, the largest that fits every provider's
    documented limits, capped at 300 DPI (`RENDERING_SETTINGS`).
  - Anthropic allows a 2,576 px long edge and 4,784 patches of 28 px.
  - OpenAI allows `detail: "original"`, a 6,000 px long edge and 10,000 patches
    of 32 px.
  - Figure crops are PNGs at 200 DPI.
- Prices come from `genai-prices`, overridden per model by `advanced.models`.
- Real-run costs (`next_cycle_inputs.md` **What step 3 builds on**):
  - The 2026-11-22 acceptance runs covered 5 PDFs and 18 pages. Page extraction
    cost $2.09 on Anthropic without verifiers and $3.39 with them, and $3.00 and
    $4.16 on OpenAI.
  - KGForEdGlobal's step 3 on 99 CAPS breaks cost $15.25 and took 20 minutes on
    Opus 5, with about 13.6k input tokens per break (brief E7).
- CI: `ci.yml` (job "Lint and test", Python 3.13 lint and tests, Python 3.14
  tests, and wheel builds and smoke tests on Ubuntu, macOS and Windows),
  `docs.yml`, `release-please.yml`, `release.yml` (PyPI Trusted Publishing) and
  `trufflehog-pr.yml`. release-please reads the squash-merge title: `feat:`
  makes a minor release.
- The first consumer is KGForEdGlobal's KG stage, which does not read page
  files. Its later needs are recorded under **Pipeline outcomes for steps 3–6**
  in `next_cycle_inputs.md`.

## Testing and Verification Baseline

- On 2026-11-22, on Python 3.13.9, 211 tests and 28 docstring examples pass,
  with 1 skipped (commands under **Commands**). The 65 warnings are PyMuPDF's
  `swigvarlink` deprecation.
- Test files under `tests/pydelity/`:
  - `config/test_loading.py`, which keeps the example configs complete.
  - `costs/test_budget.py`.
  - `extracting/` (`conftest.py`, `test_extraction.py`, `test_rendering.py`,
    `test_text_layer.py`, `test_validators.py`).
  - `pipeline/test_runner.py`.
  - `providers/test_ledger_model.py` and `test_uploads.py`.
  - `report/test_html.py`.
  - `surveying/test_probe.py`, `test_survey.py` and `test_validators.py`.
  - `utils/`, `test_api.py`, `test_cli.py` and `test_package.py`.
- `tests/conftest.py` sets dummy keys and a closed port, so no test reaches a
  provider.
- `tests/fixtures/mock_providers.py` stands in for Anthropic Messages and Files
  and for OpenAI Responses and Files. It routes requests by their text:
  - `Page index <i> (` names a page.
  - `The extraction to review:` marks the page verifier.
  - `The survey answer to review:` marks the survey verifier.
  - Any other request gets the next queued survey answer.
  - Faults can be injected.
- Canned answers exist only for `irs_form_1040a_1965_scan`, in
  `tests/fixtures/survey_answers/` and `tests/fixtures/extraction_answers/`.
  Other tests build answers in code.
- Test PDFs are in `tests/fixtures/pdfs/`, with sources in `SOURCES.md`:
  - The CAPS fixture is brief E9's sideways table: landscape tables printed on
    portrait pages with rotation attribute 0. Its text layer has
    `PHONICS (contd)` on page index 2 and `READING AND VIEWING (contd)` on page
    index 5.
  - The rotated W-9 instructions copy sets pages 2–4 to 90, 180 and 270 degrees.
  - A sentence runs from page 2 to page 3 of `irs_w9_instructions.pdf`
    (`next_cycle_inputs.md`).

  Each PDF's page count, and whether its catalog has a structure tree:

  | PDF                                       | Pages | Structure tree |
  | ----------------------------------------- | ----- | -------------- |
  | `bls_navigating_slides.pdf`               | 16    | yes            |
  | `caps_english_hl_pages_28_35.pdf`         | 8     | no             |
  | `irs_form_1040_1950.pdf`                  | 4     | no             |
  | `irs_form_1040a_1965_scan.pdf`            | 2     | no             |
  | `irs_form_w9.pdf`                         | 6     | yes            |
  | `irs_pub1_arabic.pdf`                     | 2     | yes            |
  | `irs_pub1_chinese_simplified.pdf`         | 2     | yes            |
  | `irs_w9_instructions.pdf`                 | 7     | yes            |
  | `irs_w9_instructions_rotated.pdf`         | 7     | yes            |
  | `japan_official_gazette_2019_extra_9.pdf` | 1     | no             |

- pytest runs with `--strict-config`, `--strict-markers` and `xfail_strict`,
  plus the marker `costs-money`. pytest-randomly shuffles the order. No test
  covers `LedgerModel` on streamed requests.

## Relevant Existing Behavior

- Output folder, one per PDF: `run.json`, `pdf_facts.json`, `pdf_survey.json`,
  `cost.jsonl`, `uploads.json`, `report.html`, `report/pages/<NNNN>.jpg`,
  `pages/<NNNN>.json` and `figures/<item id>.png`.
- The page file (`PageFile`, `extracting/schemas.py`) is step 3's main input:
  - Fields: `checks`, `column_order`, `containers`, `extracted_at`,
    `fingerprint`, `height_pt`, `hints`, `image`, `inputs` (`PageInputs`),
    `issues`, `items`, `page_index`, `page_number`, `pydelity_version`,
    `rotation`, `schema_version`, `text_comparison`, `verification`, `width_pt`
    and `writing_direction`.
  - `Item` has `bbox` (points on the displayed page, origin top left),
    `caption_of`, `container`, `entries` (`Entry`: `id`, `level`, `marker`,
    `text`), `field`, `figure` (`crop`, `description`, `text`), `id`, `kind`,
    `label`, `language`, `latex`, `role`, `table` (`header_rows`, then `rows` of
    `TableCell` with `col_span`, `row_span` and `text`) and `text`.
  - `Container` has `bbox`, `container` (its parent), `id` and `label`.
  - Items are in reading order. Kinds are `text`, `list`, `table`, `figure`,
    `field`, `formula` and `code`. Roles are `heading`, `body`, `caption`,
    `footnote`, `artifact`, `navigation` and `aside`.
- Item IDs come from position in `_page_items`. On page index 3 the seventh item
  is `p0003-007`, the second entry of that item's list is `p0003-007.2`, and the
  first container is `p0003-c01`. The same answer always gives the same IDs, but
  extracting a page again can number them differently.
  - When a ref repeats, the first item with it keeps it.
  - A `container` or `caption_of` ref that matches nothing becomes `None`.
- Page files can break their own rules. When retries run out, the last answer is
  kept with its failing `checks` and `issues`. `column_order` may not fit the
  writing direction, and hint differences stay in `hints`. Nothing marks
  continuity, open tops or open bottoms. Page furniture is items with role
  `artifact`.
- `page_context` resolves a page from the survey as follows:
  - Direction and rotation come from the first covering range inside the PDF,
    else the profile's default direction and rotation 0.
  - Repeated-line use is `artifact` when an artifact lists the line, else
    `content`, else `unclassified`.
  - Labels and languages come from the profile.
  - Form fields come from the facts.
  - Instructions come from `advanced.extraction.instructions`.
- Page reuse (`plan_pages`, `_reusable_page`): a page file is reused when it
  loads, its fingerprint matches, `overwrite` is off, and either it holds a
  verification or the verifier is off.
  - The fingerprint covers `PageInputs`: the PDF SHA-256, the resolved
    `PageContext`, the model, `ExtractionSettings`, `PROMPT_VERSION`,
    `RenderingSettings` and the page schema version.
  - A survey change reruns only the pages it touches.
  - No verify switch is in a fingerprint.
  - A damaged file triggers a `damaged_output` warning, and the page is
    extracted again.
- Survey data for continuation:
  - `pdf_survey.json` `profile.continuation_notes` is a list of strings.
  - `profile.start_markers` is a list of `StartMarker` with `text` and
    `description`.
  - The survey verifier's problem categories include `continuation` and
    `start_markers`.
  - The profile is not guaranteed consistent: ranges can overlap or run past the
    PDF, and artifact mapping can miss, repeat or invent IDs. `page_context`
    absorbs these for one page.
- Structure tags: `pdf_facts.json` `facts.structure` (`StructureFacts`) holds
  counts and a quality rating only: `element_count`, `marked`,
  `pages_with_tagged_content`, `quality`, `tagged`, `truncated` and
  `type_counts`.
  - `probe.py` `_walk_structure` collects element types and covered pages,
    capped at `STRUCTURE_ELEMENT_CAP` (20,000).
  - Nothing links tag elements to page content or to items. Option A would need
    that link.
- Rendering and text (`extracting/rendering.py`, `text_layer.py`):
  - `PdfWorker` runs every PyMuPDF call of a step on one thread. `call(fn)` runs
    a function, `page_image(page_index, rotation)` returns an `UprightImage`
    (JPEG data, `height_px`, `width_px`), and
    `crop(box_pt, page_index, rotation)` returns an upright PNG.
  - `grid_box_to_points` and `points_box_to_grid` map between points and the
    0–1000 grid (`GRID`).
  - `comparison_form` normalizes text with NFKC and case folding, keeping
    letters, marks and numbers. `trigrams` counts its character trigrams.
- Review issues: `ReviewIssue` has `step`, `check`, `message`, `details`,
  `page_index` and `item_id`. A page's issues are listed in this order:
  1. Failing checks.
  2. Hint differences, unless the verifier passed the page or its correction was
     kept.
  3. `no_matching_label` issues.
  4. Verifier problems, when no correction was kept.

  `run.json` `review` lists the survey's issues, then each selected page's
  (`runner._review`). The CLI summary lists the first 10.

- Run flow (`runner._steps`):
  1. The survey runs.
  2. If the survey is new and `pause` is on, the run records extraction as
     `skipped` and ends `paused`.
  3. Otherwise page extraction runs.

  Further behavior:
  - Only a new survey pauses today.
  - `extract()` never pauses.
  - The estimate, the spending question, the `max_cost` check and the API-key
    checks run once, before the first request. They run in the survey step when
    it runs, else in extraction.
  - `SpendGuard` reserves each in-flight request's highest cost.
  - Run statuses are `running`, `completed`, `paused`, `failed`, `stopped` and
    `interrupted`. Step statuses are `completed`, `reused`, `failed`, `stopped`
    and `skipped`.
  - `StepRecord.pages` (`PageCounts`: `selected`, `extracted`, `reused`) is
    specific to page extraction.

- Page selection: `pages` (from 1, such as `1-5,8`) becomes 0-based indexes in
  `_selected_pages`. The survey always reads every page. `run.json` and the
  report cover only the selected pages.
- Estimate (`costs/budget.py`):
  - `estimate_extraction` prices one extractor request per page:
    `TYPICAL_PAGE_OUTPUT_TOKENS` 4,000, plus the text-layer characters divided
    by `TEXT_CHARS_PER_OUTPUT_TOKEN` 2.
  - With the verifier on, it adds one verifier request per page
    (`TYPICAL_VERDICT_OUTPUT_TOKENS` 3,000).
  - The maximum assumes every retry with `max_output_tokens`.
  - Prompt text counts at 4 characters a token (`PROMPT_CHARS_PER_TOKEN`).
  - `StepEstimate` has `expected_usd`, `max_usd`, `model`, `name`, `pages`,
    `requests_max`, `reused` and `verifier`. `estimate_run` adds the steps up.
- Ledger: every `cost.jsonl` line carries its step, page and agent.
  - Agents are `surveyor` and `verifier` for the survey, and `extractor` and
    `verifier` for page extraction.
  - `LedgerModel.for_page(agent=..., page_index=...)` wraps per-page requests.
    `for_agent(agent=...)` wraps whole-PDF requests.
- `load(output_dir)` (`runner.load_run`, `_load_pages`) returns only page files
  whose `inputs.pdf_sha256` matches `pdf_facts.json`, in page order. It returns
  none when the facts are absent, and it raises `OutputError` when a figure crop
  is missing. A run warns when the folder holds another PDF's results
  (`_warn_other_pdf`).
- Errors:
  - A run stops on an unusable answer (`ExtractionError` or `SurveyError`) or a
    provider error after retries (`ProviderError`).
  - A check still failing on the last answer is kept and listed.
  - A hint difference never sends an answer back or fails a run.

## Known Unknowns

- PyPI publication of 0.2.0 and the docs site deployment were not checked. The
  sandbox blocks network access to GitHub and PyPI. This matters only for
  release work.
- KGForEdGlobal's past-run outputs (`results/kg_for_ed/`, local and not in git)
  were not inspected. The brief's E1–E10 summarize them.
- The size of KGForEdGlobal's step 3 prompt is not recorded anywhere. Its prompt
  caching uses no explicit settings.
- No measurement exists of model accuracy or cost for a whole-break design in
  pydelity. Real-run costs exist only for the survey and page extraction.

## Evidence

- `git log`, `git rev-parse` (`main`, `origin/main`, `v0.2.0`, `HEAD`),
  `git diff --stat main..HEAD` and `git diff --stat af1b2d1 main` — the
  baseline, branch and release state.
- `pyproject.toml`, `uv.lock`, `justfile`, `CHANGELOG.md`,
  `.release-please-manifest.json` and `.github/workflows/` — the stack, pins,
  recipes, CI and release.
- `src/pydelity/review.py`, `schema_versions.py`, `__init__.py`, `cli.py` and
  `config/schemas.py` — names, settings and the public surface.
- `src/pydelity/extracting/{schemas,extraction,llm,rendering,text_layer}.py` —
  the page file, reuse, IDs, the verifier flow, rendering and text.
- `src/pydelity/surveying/{schemas,probe,llm,agents,prompts}.py` — the profile,
  continuation fields, the structure walk and the survey verifier.
- `src/pydelity/pipeline/{runner,schemas}.py` and `costs/budget.py` — the run
  flow, pause, review list, loading and estimate.
- `tests/fixtures/mock_providers.py`, `tests/fixtures/pdfs/SOURCES.md` and a
  PyMuPDF read of the fixture PDFs — the stand-in, page counts, structure trees
  and the CAPS `(contd)` lines.
- `.venv/bin/python -m pytest` — 211 passed; the doctests gave 28 passed and 1
  skipped.
- `git show af1b2d1:.standards/CONTEXT.md` and the verifier cycle's design at
  `af1b2d1` — the prior context and the design outline.
- KGForEdGlobal `backend/src/kgfeg/page_ir_verification/`,
  `entries/verify_page_ir_continuity.py`,
  `document_ir/compute_page_break_links.py` and `document_ir/stitch_segments.py`
  — the port source, read only.
- `artifacts/next_cycle_inputs.md`, `artifacts/design_brief.md` and the active
  request in `.standards/STATE.md` — the user decisions and inputs.

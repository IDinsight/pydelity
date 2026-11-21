# Project Context

## Project Baseline

- pydelity is a Python library and CLI that will turn a PDF into faithful,
  structured JSON through a six-step pipeline. Two steps exist: the survey (step
  1) and page extraction (step 2). Steps 3–6 (page-break verification, assembly,
  schema proposal, projection) do not exist.
- `main` is at `c7582e7` (release 0.1.1, the survey only; 0.1.0's squash commit
  is `c63d891`, pull request 4). The working branch `tz6/pipeline-step-2` is 47
  commits ahead of `main` (merge base `c7582e7`, head `5b94a4d`): the STANDARDS
  installation, page extraction and its cycle records. Page extraction is not
  merged or released; `pyproject.toml` and `CHANGELOG.md` still say `0.1.1`,
  because release-please bumps the version. The branch's pull request is 10, a
  draft titled `Tz6/pipeline step 2` (`artifacts/next_cycle_inputs.md`; not
  checked here).
- Page extraction's cycle,
  `build-step-2-page-extraction-of-the-20261119T174118Z-0419318a`, was signed
  off on 2026-11-20. Its records are under `.standards/docs/` (`scope/`,
  `specs/`, `development/`, `verification/`, `documentation/`,
  `synchronization/`, `reviews/<id>/`): scope `AC-001`–`AC-064` (`AC-015`,
  `AC-023`, `AC-024`, `AC-062` retired), design decisions 1–22. Its work is now
  the baseline. The survey cycle's records are at commit `83743ef`
  (`git show 83743ef:<path>`; `git fetch origin pull/4/head` in a clone that
  lacks it).
- This cycle runs on the same branch, and its work merges with page extraction
  and ships with it as 0.2.0 (user input). Merge happens only after this cycle's
  sign-off and STANDARDS Project Uninstallation on the branch, with a
  non-breaking `feat:` pull request title (`next_cycle_inputs.md` **Loose
  ends**).
- Inputs: `artifacts/next_cycle_inputs.md`, rewritten for this cycle in
  `5b94a4d` (its **Next cycle, before step 3** section, the user decisions that
  apply to later steps, what 0.2.0 provides, risks, review findings left for
  later, and **Pushed to later steps**), and `artifacts/design_brief.md`. Where
  they differ, `next_cycle_inputs.md` is newer. History in the brief includes
  its per-model PDF limits, its step 1 and three of its step 2 design points
  (text-layer hints, a validator only on failed or hard pages, DPI from page
  size), container open-top/open-bottom hints, step 3 option E, and "released
  only once all six steps are done".
- Terminology differs between the two inputs. In pydelity's code and docs the
  "verifier" is a second request to the same model that reviews an answer
  against the source and may return a full correction. The brief calls that
  role a "validator" and uses "verifier" for step 3's main per-break model.

## Stack and Tooling

- Python `>=3.13`; `.python-version` is `3.13`; classifiers name 3.13 and 3.14
  only (`Development Status :: 3 - Alpha`). Python 3.14 on a Mac needs macOS 14
  or later. The local `.venv` runs Python 3.13.9.
- Runtime dependencies are minimum versions (`pyproject.toml`): `genai-prices`
  0.2.4, `langcodes` 3.5.1, `loguru` 0.8.0, `pydantic` 2.14.3,
  `pydantic-ai-slim[anthropic,openai]` 2.69.0, `pydantic-settings[yaml]` 2.16.3,
  `pymupdf` 2.1, `typer` 0.29.1. `uv.lock` holds those versions plus `anthropic`
  2.10.0, `openai` 3.53.0 and `onnxruntime` 1.32.0 (pulled in by PyMuPDF 2.x,
  which has no wheels for Intel Macs, Windows ARM, 32-bit Windows or musl Linux).
  Page extraction added no dependency.
- Build: setuptools (`requires = ["setuptools>=77"]`, kept by hand; Dependabot
  ignores setuptools), src layout, package data `report/*.css`. Console script
  `pydelity = "pydelity.cli:main"`; `python -m pydelity` works.
- uv manages the environment (`required-version = ">=0.8.1"`, CI pins uv
  `0.13.8`) with a strict editable install.
- Dev tools, exact pins: detect-secrets 1.5.0, interrogate 1.7.0, prek 0.5.11,
  pytest 9.2.0, pytest-cov 7.1.0, pytest-randomly 5.1.0, pytest-xdist 3.8.0,
  ruff 0.17.5, rust-just 1.59.0, twine 7.0.0, ty 0.0.105, zizmor 1.32.0.
- Docs site: Astro Starlight under `docs/` with pnpm, versioned builds. Node
  `24.22.3` is kept by hand in two `.pre-commit-config.yaml` hooks and
  `docs.yml`.
- `just` recipes run under bash; there are no Windows-native recipes.

## Structure and Boundaries

- `src/pydelity/__init__.py` — public re-exports (`run`, `survey`, `extract`,
  `measure`, `estimate` and their `a`-prefixed async twins, `load`, `Config`,
  `CostEstimate`, `PageFile`, `PdfFacts`, `PdfSurvey`, `RunRecord`, `RunResult`,
  the errors), `__version__`, `logger.disable("pydelity")`.
- `src/pydelity/api.py` — the public functions; each takes `pdf`, `config` and
  setting keywords; `allow_over_max_cost` on the run, survey and extract
  functions; `arun_with_questions` for the CLI.
- `src/pydelity/cli.py` — one Typer command: `PDF`; `--config` `-c`,
  `--language` `-l`, `--pages` `-p`, `--output-dir` `-d`, `--model` `-m`,
  `--max-cost` `-mc`, `--overwrite` `-o`, `--no-pause` `-np`, `--yes` `-y`,
  `--verbose` `-v`, `--version`, `-h`. Instructions have no CLI option.
- `src/pydelity/config/schemas.py` — `Config` (`advanced`, `languages`,
  `max_cost`, `model`, `output_dir`, `overwrite`, `pages`, `pause`, `pdf`;
  `extra="forbid"`; properties `survey_model`, `extraction_model`,
  `output_folder`), `AdvancedConfig` (`extraction`, `models`,
  `provider_retries`, `survey`, `uploads`), `SurveyConfig` (`check_retries`
  0–5 default 2, `effort` `high`, `instructions`, `max_output_tokens` 32,000,
  `request_timeout_seconds` 900), `ExtractionConfig` (the same plus
  `concurrent_pages` 1–32 default 8 and `model`; timeout 600). No setting turns
  a verifier on or off. `config/loading.py` `resolve_config` merges keywords
  over a file over defaults and reports every problem in one `ConfigError`.
- `src/pydelity/surveying/` — the survey: `probe.py`, `facts.py`,
  `prompts.py` (`PROMPT_VERSION = 1`, `survey_pdf`), `agents.py`
  (`create_survey_agent`), `llm.py` (`ask_model`, `ModelSurvey`),
  `validators.py` (checks C1–C7, `compare_with_facts`, `covering_range`),
  `schemas.py`, `survey.py` (`run_survey`, `build_survey`, `saved_survey`,
  `survey_inputs`, `survey_fingerprint`).
- `src/pydelity/extracting/` — page extraction: `extraction.py` (page context,
  plan, fingerprints, reuse, page tasks, verifier application, crops, page
  files), `agents.py`, `llm.py`, `prompts.py` (`PROMPT_VERSION = 1`,
  `extract_page`, `verify_page`), `rendering.py` (`PdfWorker`, page images,
  crops, `grid_box_to_points`, `points_box_to_grid`), `schemas.py`,
  `text_layer.py`, `validators.py`. It imports `surveying.schemas`,
  `surveying.probe` (`line_boxes`), `surveying.validators` (`covering_range`)
  and `review`; `surveying` never imports `extracting`.
- `src/pydelity/review.py` — `ReviewIssue`, `CheckFailure`, and the name lists
  `StepName` (`survey`, `extraction`), `SurveyCheckName`,
  `SurveyComparisonName`, `ExtractionCheckName`, `ExtractionIssueName`
  (`no_matching_label`, `verifier`), `IssueName`.
- `src/pydelity/pipeline/` — `runner.py` (`run_pipeline`, `run_survey_step`,
  `run_extraction_step`, `run_estimate`, `run_measure`, `load_run`; the survey
  and extraction steps, the pause, estimates, the summary) and `schemas.py`
  (`RunRecord`, `StepRecord`, `PageCounts`, `RunCost`, `RunResult`).
- `src/pydelity/costs/` — `ledger.py`, `pricing.py`, `budget.py` (`SpendGuard`
  with per-request reservations, `estimate_survey`, `estimate_extraction`,
  `estimate_run`, `PageRequestSize`), `schemas.py`.
- `src/pydelity/providers/` — `profiles.py` (`DEFAULT_SURVEY_MODEL`,
  `DEFAULT_EXTRACTION_MODEL`, `ModelChoice`, `ProviderProfile` with image
  limits, per-image tokens and `output_mode`), `factory.py` (`build_model`,
  `structured_output`, `output_mode`), `ledger_model.py` (`LedgerModel`,
  `LedgerContext`, `LedgerModel.for_page`), `uploads.py` (`attach_pdf`,
  `uploads.json`).
- `src/pydelity/report/` — `images.py` (report page JPEGs), `html.py`
  (`report.html`, including extracted pages), `report.css`.
- `src/pydelity/utils/` — `files.py` (atomic writes, validated loads, temp-file
  cleanup), `fingerprints.py`, `pdf.py` (`open_pdf`, `TEXT_FLAGS`),
  `coroutines.py` (`run_sync`, `warn`, step-attributed warnings), `prompts.py`
  (`PromptPair`), `text.py`.
- `src/pydelity/schema_versions.py` — one constant per output file (facts,
  ledger, manifest, page, run, survey, uploads), all `"1.0"`.
- `src/pydelity/errors.py` — `PydelityError` and subclasses
  (`BudgetExceededError`, `ConfigError`, `ExtractionError`,
  `MissingApiKeyError`, `OutputError`, `PdfError`, `ProviderError`,
  `SurveyError`), `PydelityWarning`, CLI `ExitCode`.
- `scripts/` — `generate_reference_docs.py`, `smoke_installed_wheel.py` (runs
  the survey and page extraction from the built wheel against the stand-in),
  `check_env_template.py`, `format_markdown.mjs`.
- `examples/config.json`, `examples/config.yaml` — every setting at its default.
- `docs/src/content/docs/` — `start/`, `guides/` (command line, configuration,
  costs, models and providers, outputs, page extraction, Python, reruns),
  `reference/` (generated: CLI, configuration, Python API, `cost.jsonl`,
  `pdf_facts.json`, `pdf_survey.json`, page file, `run.json`, `uploads.json`,
  survey checks, extraction checks), `faq.md`, `need-help.md`, `contributing/`.
- Git-ignored local folders (`data/`, `pydelity-output/`, `graveyard/`,
  `build/`) are not baseline.
- KGForEdGlobal (`/Users/tzz/Projects/private/idi/KGForEdGlobal`) is outside
  the repo and read-only. What page extraction ported from its
  `backend/src/kgfeg/page_ir_extraction/` is in `next_cycle_inputs.md` **Reuse
  from KGForEdGlobal so far**; its validator (a second request to the same
  model, run once on every page, with a full correction) is the source of
  pydelity's page verifier. Its survey has no counterpart.

## Nearest Analogues

- Page extraction's verifier is the analogue for a survey verifier and for any
  opt-in switch:
  - `extracting/agents.py` `create_verifier_agent`: an agent with output type
    `VerifierVerdict` and `retries={"output": check_retries}`, whose output
    validator runs every check on `verdict.corrected` and raises `ModelRetry`
    while retries remain, accepting the verdict as given on the last attempt.
  - `extracting/prompts.py` `verify_page`: its own system message (audit task,
    checklist, verdict rules, the same labels and the step's instructions last)
    and a user message that adds the answer as JSON and the checks it still
    fails; `extracting/llm.py` `ask_verifier` returns `ModelVerdict` (verdict,
    correction failures, attempts).
  - `extracting/schemas.py` `VerifierVerdict` (`passed`, `problems`,
    `corrected`; Pydantic invariants: passed means no problems and no
    correction), `VerifierProblem` (`item_ref`, `category`, `description`),
    `PageVerification` (`attempts`, `correction_applied`,
    `correction_failures`, `verdict`), required on `PageFile.verification`.
  - `extracting/extraction.py` `_extract_page` calls `ask_verifier` on every
    page unconditionally; `_kept_answer` keeps a correction that passes every
    check other than `text_dropped` and `text_added`; `_page_issues` leaves the
    text checks off the review list when the verdict passed or the correction
    was kept, and adds a `verifier` issue per problem when no correction was
    kept; `_verifier_outcome` feeds the per-page log line.
  - Costs: `LedgerModel.for_page(agent=..., page_index=...)` wraps the model
    per page and agent, so `cost.jsonl` lines carry `agent` (`extractor` or
    `verifier`); `estimate_extraction` prices one verifier request per page
    (`TYPICAL_VERDICT_OUTPUT_TOKENS` 3,000) in the expected cost and
    `check_retries + 1` verifier requests in the maximum;
    `requests_max = 2 * attempts * pages`; `request_sizes` and
    `request_sizes_before_survey` measure the verifier's text.
  - Report: `report/html.py` `_verifier_text` shows each page's outcome.
  - Tests: `tests/pydelity/extracting/test_extraction.py`; the stand-in routes
    a page request to the verifier answer when its text holds
    `The extraction to review:`.
- The survey's single-agent flow is what a survey verifier would extend:
  `surveying/llm.py` `ask_model` attaches the PDF once (`attach_pdf`: reuse a
  recorded upload with at least an hour left, upload, or send inline), runs the
  agent with `[attachment.content, user message, CachePoint()]`, retries once
  with a fresh upload when the provider says the file is gone, and returns
  `ModelSurvey(answer, attachment, attempts)`. `build_survey` reruns
  `run_checks` on the accepted answer to build `checks` and `issues`.
- How the survey differs from page extraction: one request (plus check
  retries) for the whole PDF, sent as an uploaded or inline document, not page
  images; checks C1–C7 run against `Facts`; the comparisons `rotation_differs`
  and `page_number_differs` are review issues only, never retries;
  `PdfSurvey` has no verification field; survey ledger lines have
  `agent: null` and `page_index: null`; `LedgerModel.for_page` requires a page
  index, and no wrapper names an agent without a page; `estimate_survey` prices
  one request (`TYPICAL_OUTPUT_TOKENS` 8,000) expected and `check_retries + 1`
  at most.

## Commands

- `just install` — `uv sync --locked`, then `uv run --locked prek install`.
- `just lint` — `docs-reference`, then `lint-markdown`, `lint-python`
  (`ruff check --fix`, `ruff format`, `ty check`, `interrogate`) and
  `lint-workflows` (zizmor).
- `just test` — pytest with `--numprocesses auto` and `--exitfirst`, then the
  docstring examples with `--doctest-modules src`; `KEEP_GOING=1 just test`
  runs everything and writes failures to `.cache/test-errors`.
- `just build` — fresh `dist/` with `uv build`, then `twine check --strict`.
- `just docs`, `just docs-build`, `just docs-reference` — serve or build the
  docs site; regenerate the reference pages (CI fails when they are stale or a
  generated page is untracked).
- `uv run --locked python scripts/smoke_installed_wheel.py` — wheel smoke test
  against the stand-in providers.
- `python -m tests.fixtures.mock_providers --answer <answer JSON> --page-answers <page answers JSON>`
  — runs the stand-in provider server by hand.
- `uv run prek run --all-files` — every git hook.
- `.venv/bin/python -m pytest -q --numprocesses auto -p no:cacheprovider`, then
  `.venv/bin/python -m pytest -q --doctest-modules src -p no:cacheprovider` —
  the tests without uv, where uv cannot write its cache.
- `node .standards/bin/check.mjs` — STANDARDS consistency check.

## Conventions and Constraints

- Code style (`pyproject.toml`): Ruff, line length 88, rule families ANN, B, C4,
  C90, D, E, F, I, PL, PT, RET, RUF, S, SIM, UP, W; McCabe complexity at most
  10; NumPy docstrings; import sections "Future Library", "Standard Library",
  "Third Party Library", "Package Library", "Local Folder"; interrogate at 100%
  of `scripts`, `src` and `tests`; ty over all three.
- User conventions: private globals, classes and functions before public ones,
  alphabetical within each group; American English; plain-language docstrings;
  each step's checks on model answers in `<step>/validators.py`; prompts return
  a `PromptPair`; output schema versions in `schema_versions.py`; `justfile`
  recipes and `pyproject.toml` tables, keys and lists alphabetical. Shipped
  code, config, docstrings and docs never mention the development process
  (dates, DEV or AC IDs, cycles, STANDARDS roles, KGForEdGlobal, numbered
  pipeline steps).
- Step folders under `src/pydelity/` are "-ing" words (`surveying/`,
  `extracting/`, then `verifying/`, `assembling/`, `proposing/`,
  `projecting/`), split into `agents.py`, `llm.py`, `prompts.py`,
  `validators.py`, `schemas.py` beside the step module. Outputs, logs and
  estimates name a step with a noun (`survey`, `extraction`). The user approves
  new file and folder names before the build step that creates them.
- User decisions in force (`next_cycle_inputs.md` **User decisions that apply
  to later steps**), among them:
  - Acceptance rests on the user's review of real runs with Anthropic and
    OpenAI models on PDFs of their choice (two-column right-to-left, Chinese or
    Japanese, a tax or fillable form, a slide deck or image-heavy PDF, CAPS);
    no parity target; cost reported without a target.
  - The model's reading is trusted over measured facts: code may send an answer
    back with a difference, the model's last answer is kept, and a difference
    left goes on the review list. For page extraction, text differences are
    listed only when the page keeps the extraction and the verifier did not
    pass it.
  - Each check sits where it can be enforced: Pydantic for shape,
    `<step>/validators.py` for what code decides, a verifying model for what
    code cannot judge. The survey uses Python checks only today; this cycle's
    request replaces that rule.
  - One structured-output mode per provider for every step: `PromptedOutput`
    on Anthropic, `NativeOutput` on OpenAI.
  - Document-type agnostic: no core logic, prompt, field or default may assume
    a document type, language or writing direction; no word lists or patterns.
  - No per-model limits checked before a call; no default `max_cost`; the CLI
    asks at most once per run (`--yes`), Python passes `allow_over_max_cost` or
    gets `BudgetExceededError`.
  - Every function that measures, estimates or runs has an `a`-prefixed async
    twin; `load` stays sync; the docs lead with the async functions.
  - No backwards compatibility while pydelity has no public users: no aliases,
    deprecations, migrations or compatibility-only defaults. `PROBE_VERSION`,
    each `PROMPT_VERSION` and every output `schema_version` stayed at 1 /
    `1.0` through both cycles; when to raise them again is open.
  - Every CLI option has a short form; no `--quiet`.
  - `examples/config.json` and `examples/config.yaml` hold every setting at its
    default, kept complete by `tests/pydelity/config/test_loading.py`.
  - Each later step gets its own pause (`pause`, `--no-pause`/`-np`), its own
    `advanced.<step>.model` and its own `advanced.<step>.instructions`.
  - Test PDFs are real public documents the user approves, under 500 KB; a
    rotated copy counts when `SOURCES.md` says how it was made.
  - A new runtime dependency's minimum is its latest stable release that day.
- How the user works with Developer (`next_cycle_inputs.md`): `STEPWISE`
  collaboration, files listed for review before each build step, a stop after
  each step, each report ending with the next step's plan; the user makes the
  commits; Developer does not edit tests (they are Tester's). Self-checks use
  the stand-in and PydanticAI test models; real runs only with the user's
  go-ahead and keys, with spend recorded; faults use scratch scripts. Since
  `PROMPT_VERSION` is not raised, real runs after a prompt change use new
  folders or `--overwrite`.
- Page extraction's reviews kept only major issues (a finding must, on input
  the release targets, make output wrong, lose money, fail a run, or break a
  function acceptance relies on). Whether this cycle's reviews use the same bar
  is for the user to say.
- Output files are written atomically, validated on load, and carry a
  `schema_version`; `load_run` rejects another major version.
- Commits follow Conventional Commits with no `Co-Authored-By` trailer or other
  AI attribution. Repo tooling must work without `.standards/`, which `main`
  does not have. "Lint and test" and "TruffleHog secret scan" are required
  checks on `main`.

## External Systems and Data

- Providers: Anthropic and OpenAI through PydanticAI, as
  `<provider>:<model-id>`. Both steps default to `anthropic:claude-opus-5-5` at
  effort `high` (`DEFAULT_SURVEY_MODEL`, `DEFAULT_EXTRACTION_MODEL`). The survey
  uses `model`, else its default; page extraction uses
  `advanced.extraction.model`, else `model`, else its default. Keys come from
  `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` only. `effort` maps to Anthropic
  adaptive thinking or OpenAI `reasoning_effort`.
- Structured output: `ProviderProfile.output_mode` (Anthropic `prompted`,
  OpenAI `native`); under prompted output the answer's JSON schema is part of
  the instructions, which Anthropic requests cache.
- PDF transport (survey only): the Files API upload recorded in `uploads.json`,
  reused while at least `REUSE_MIN_REMAINING` (one hour) is left, with inline
  fallback; upload expiry bounds Anthropic 1–2,160 hours, OpenAI 1–720. A
  survey request is priced at the page count times `pdf_tokens_per_page`
  (Anthropic 4,784 image plus 3,000 text; OpenAI 3,000 plus 3,000). Page
  extraction sends its own page images, never the PDF.
- Page images: upright JPEG quality 90, the largest that fits every provider's
  documented limits and 300 DPI (Anthropic 2,576 px long edge and 4,784 tiles of
  28 px; OpenAI `detail: "original"`, 6,000 px and 10,000 patches of 32 px), as
  of November 2026.
- Prices: `genai-prices`, overridden per model by `advanced.models`.
- Real-run costs (2026-11-20, 7 PDFs, 22 pages): page extraction $5.38 on the
  Anthropic default, of which the verifier was $1.48 (28%), and $9.02 on
  `openai:gpt-6.2-astra`, of which the verifier was $3.18 (35%); the surveys
  cost $0.98 and $2.09 (`next_cycle_inputs.md`).
- GitHub workflows: `ci.yml` (job "Lint and test" gates the Python 3.13 lint
  and test job, the Python 3.14 tests and the wheel builds plus smoke test on
  ubuntu, macOS and Windows), `docs.yml`, `release-please.yml`, `release.yml`
  (PyPI Trusted Publishing on a published release), `trufflehog-pr.yml`.
  release-please reads the squash-merge title: `feat:` makes a minor release.
- KGForEdGlobal's KG stage is the first consumer; its contract is in
  `next_cycle_inputs.md` and the brief. It does not read page files.

## Testing and Verification Baseline

- 177 tests and 27 docstring examples (1 skipped) pass locally on Python 3.13.9
  (commands under **Commands**, 2026-11-21).
- Test files: `tests/pydelity/` `config/test_loading.py`,
  `costs/test_budget.py`, `extracting/test_{extraction,rendering,text_layer,validators}.py`,
  `pipeline/test_runner.py`, `providers/test_{ledger_model,uploads}.py`,
  `report/test_html.py`, `surveying/test_{probe,survey,validators}.py`,
  `utils/test_{files,pdf}.py`, `test_api.py`, `test_cli.py`,
  `test_package.py`.
- `tests/conftest.py` sets dummy keys and a closed port, so no test reaches a
  provider. `tests/fixtures/mock_providers.py` stands in for Anthropic Messages
  and Files and OpenAI Responses and Files. Page requests are routed by content
  (`Page index <i> (` names the page; `The extraction to review:` marks the
  verifier), so concurrent requests get the right answer. A request that names
  no page, such as the survey's, gets the next queued survey answer in order;
  nothing tells a survey answer request from any other survey request. Anthropic
  answers come back as JSON text, OpenAI's in native format; faults can be
  injected.
- Canned answers: `tests/fixtures/survey_answers/` and
  `tests/fixtures/extraction_answers/` hold one file each, for
  `irs_form_1040a_1965_scan`; other tests build answers in code.
- Test PDFs (`tests/fixtures/pdfs/`, sources in `SOURCES.md`): BLS slides, CAPS
  pages 28–35, IRS 1040 (1950), 1040A (1965 scan), W-9 (fillable), Publication
  1 in Arabic and Simplified Chinese, W-9 instructions and its rotated copy
  (pages 2–4 at 90, 180, 270), Japan Official Gazette (vertical, one page).
- pytest: `--strict-config`, `--strict-markers`, `xfail_strict`, marker
  `costs-money`; pytest-randomly shuffles order; coverage configured but not
  enforced. No test covers `LedgerModel.request_stream`.

## Relevant Existing Behavior

- Output folder (one per PDF, the unit of resume and spend): `run.json`,
  `pdf_facts.json`, `pdf_survey.json`, `cost.jsonl`, `uploads.json`,
  `report.html`, `report/pages/<NNNN>.jpg`, `pages/<NNNN>.json`,
  `figures/<item id>.png`. `_prepare_folder` removes temp files from the folder
  and `report/pages/`; `extract_pages` removes them from `pages/` and
  `figures/` when the extraction step runs.
- Survey reuse: `pdf_survey.json` is reused while `survey_fingerprint` matches
  (PDF SHA-256, facts fingerprint, model, `advanced.survey.instructions`,
  languages, `check_retries`, `effort`, `max_output_tokens`,
  `PROMPT_VERSION`, schema version) and `overwrite` is off.
  `SurveyInputs.pdf_name` is stored but not fingerprinted.
- Page reuse: a page file's fingerprint covers `PageInputs`: the PDF SHA-256,
  the resolved `PageContext` (labels, languages, page extraction's
  instructions, direction, rotation, repeated lines and their classification,
  form fields, measured page facts), the resolved model, `ExtractionSettings`
  (`check_retries`, `effort`, `max_output_tokens`), `PROMPT_VERSION`,
  `RenderingSettings` and the page schema version. A survey change reruns only
  the pages it touches; no extraction setting reruns the survey.
- Page extraction per page: render the image and read the text layer on the
  PdfWorker thread; extractor with checks (`labels`, `content`, `languages`,
  `boxes`, `containers`, `captions`, `reading_order`, `artifacts`,
  `form_fields`, `text_dropped`, `text_added`) and retries; the verifier on
  every page; apply the verdict; map boxes; write crops, then the page file
  atomically. Text comparison is skipped as `no_text_layer`,
  `garbled_text_layer` or `text_layer_mismatch`. The text-check retry message
  says the model may keep its reading. Requests carry no text-layer lines.
- Page file `verification` is always present and the report and per-page log
  line always show a verifier outcome. Pages the verifier did not pass keep the
  extraction with text differences listed; pages it passed or corrected list
  none.
- Run behavior: `run()` and the CLI pause after a step that wrote new output in
  the run (today only after a new survey) unless `pause` is off; `extract()`
  never pauses; status `paused`, extraction `skipped`. Run statuses `running`,
  `completed`, `paused`, `failed`, `stopped`, `interrupted`; step statuses
  `completed`, `reused`, `failed`, `stopped`, `skipped`. `StepRecord.pages`
  (`selected`, `extracted`, `reused`) for extraction. The estimate, question,
  plan-time check (expected cost) and API-key check run once, before the run's
  first request. `SpendGuard` reserves each in-flight request's bound.
- Review issues: `ReviewIssue` (`step`, `check`, `message`, `details`,
  `page_index`, `item_id`); `run.json` `review` lists the survey's, then each
  selected page's; the CLI summary prints
  `<step>, page <number>[, item <id>]: <message>`.
- `load(output_dir)` takes only the folder and returns every page file in
  `pages/` in page order, without checking which PDF each came from; each page
  file records `inputs.pdf_sha256`, and `pdf_facts.json` records the PDF's
  identity (`PdfFacts.pdf`). A run warns when the folder holds another PDF's
  results, and `run.json` and the report list only the selected pages.
- Where the remaining-issue candidates live (`next_cycle_inputs.md` lists their
  failure cases):
  - `load()` and other PDFs' page files: `pipeline/runner.py` `load_run`,
    `_load_pages`, `_warn_other_pdf`.
  - Boxes and stored text: `extracting/text_layer.py`, `surveying/probe.py`
    `line_boxes`, `extracting/rendering.py` box mapping,
    `extracting/validators.py` text checks and `comparison_status`; the page
    prompt's box rules in `extracting/prompts.py`.
  - Probe (`surveying/probe.py`): an inline `/Annots` widget reaches
    `_field_error` from `_form`'s per-widget `try`; a dangling outline link
    fails in `_cut_outline_cycle`; the structure walk's cap
    (`STRUCTURE_ELEMENT_CAP` 20,000, `_walk_structure`).
  - Report: table header cells with `row_span` past `header_rows` in
    `report/html.py`'s table rendering.
  - Crops named by item position, written before the page file
    (`extraction.py` `_write_page`); the page JPEG has no byte cap and crops
    render at 200 DPI with no pixel cap (`rendering.py`).
  - The `TEXT_FLAGS` comment in `utils/pdf.py` says text is clipped to the
    media box; PyMuPDF clips to the CropBox.
  - Docs wording looser than the code: README, `index.md` and
    `guides/page-extraction.md` say "A second model reviews every page"; the
    other items are in `next_cycle_inputs.md` **Review findings and
    observations left for later**.
- A 0.1.x output folder whose `cost.jsonl` has one line spends one request
  before stopping with `OutputError`; with more lines it stops before any
  request.

## Known Unknowns

- Pull request 10's current state and title were not checked: the sandbox
  blocked the GitHub API. It matters only at merge.
- Anthropic's per-image byte limit (about 5 MB in the implementation review)
  was not checked against current documentation; synthetic grain made Letter
  page JPEGs of 3.7–6.1 MB, while the test PDFs peak at 1.04 MB.
- No measurement exists of a survey verifier's cost; `next_cycle_inputs.md`
  expects a verified survey to cost roughly twice as much, since it sends the
  whole PDF again.
- Ctrl+C at a CLI question on Windows, a filled or handwritten form value and a
  one-picture page were not exercised by real runs.

## Evidence

- `pyproject.toml`, `uv.lock`, `justfile`, `.github/workflows/*.yml`,
  `examples/config.yaml` — stack, pins, recipes, CI, settings.
- `src/pydelity/surveying/{agents,llm,survey,schemas,validators,prompts}.py`,
  `src/pydelity/extracting/{agents,llm,extraction,schemas,prompts,rendering}.py`,
  `src/pydelity/costs/budget.py`, `src/pydelity/providers/{ledger_model,profiles,uploads}.py`,
  `src/pydelity/pipeline/runner.py`, `src/pydelity/review.py`,
  `src/pydelity/config/schemas.py`, `src/pydelity/report/html.py`,
  `src/pydelity/schema_versions.py`, `src/pydelity/cli.py` — behavior cited
  above.
- `tests/fixtures/mock_providers.py`, `tests/conftest.py`,
  `tests/fixtures/pdfs/SOURCES.md` — test harness.
- `.venv/bin/python -m pytest` — 177 passed; doctests 27 passed, 1 skipped.
- `git log`, `git rev-list --count main..HEAD`, `git merge-base main HEAD`,
  `git diff --stat main..HEAD` — history and branch.
- `.standards/docs/*/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a.md`
  and its `reviews/` — page extraction's scope, design, plan, verification,
  reviews, documentation and synchronization.
- `artifacts/next_cycle_inputs.md`, `artifacts/design_brief.md`, the active
  request in `.standards/STATE.md` — user decisions and inputs.

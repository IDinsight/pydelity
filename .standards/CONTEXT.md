# Project Context

## Project Baseline

- pydelity is a Python library and CLI that will turn a PDF into faithful,
  structured JSON through a six-step pipeline. Only step 1, the survey, exists.
  It ships as 0.1.0 (squash commit `c63d891`, pull request 4) and 0.1.1
  (`4403966`, a docs fix; release commit `c7582e7`), both on `main`. Version
  `0.1.1` is in `pyproject.toml`, `uv.lock` and `CHANGELOG.md`; the classifier
  is `Development Status :: 3 - Alpha`.
- The working branch `tz6/pipeline-step-2` is `main` plus commit `fa5ab75`,
  which installs STANDARDS. Outside STANDARDS paths (`.standards/`, `.agents/`,
  `.claude/`, `.codex/`) it changes only `AGENTS.md` and `CLAUDE.md`. `main` has
  no STANDARDS installation.
- The survey cycle's records (scope, design, plan, verification, reviews,
  documentation, synchronization and its `CONTEXT.md`) are at commit `83743ef`,
  present in this clone, under
  `.standards/docs/.../build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c.md`.
  `git fetch origin pull/4/head` gets it in a clone that lacks it. Read them
  with `git show 83743ef:<path>`.
- `CHANGELOG.md` links the 0.1.0 feature entry to commit `d13c0fd`, which no
  longer exists on `main` after its history was rewritten; the same change is
  now `c63d891` (user input, consistent with `git log main`).
- Request inputs: `artifacts/next_cycle_inputs.md` (the survey cycle's
  decisions, what 0.1.0 provides and lacks for step 2, corrections to the brief,
  follow-ups) and `artifacts/design_brief.md` (step 2 design points, known
  KGForEdGlobal defects, evidence E1–E23, the KG consumer contract). Where they
  differ, `next_cycle_inputs.md` is newer. Both predate 0.1.1; the active
  request (`.standards/STATE.md`) lists what changed since. Statements in the
  brief that are now history include its step 1 design points, per-model PDF
  limits, "released only once all six steps are done" and its open questions,
  which `next_cycle_inputs.md` answers.
- User input in the request, not checked against PyPI: the `0.0.1` placeholder
  is yanked, and Python 3.15 waits on an `onnxruntime` 3.15 build, which PyMuPDF
  2.x requires.

## Stack and Tooling

- Python `>=3.13`; `.python-version` is `3.13`; classifiers name 3.13 and 3.14
  only. Python 3.14 on a Mac needs macOS 14 or later (user input, 0.1.1 docs).
  The local `.venv` runs Python 3.13.9.
- Runtime dependencies are minimum versions (`pyproject.toml`): `genai-prices`
  0.2.4, `langcodes` 3.5.1, `loguru` 0.8.0, `pydantic` 2.14.3,
  `pydantic-ai-slim[anthropic,openai]` 2.69.0, `pydantic-settings[yaml]` 2.16.3,
  `pymupdf` 2.1, `typer` 0.29.1. Installed and locked: those versions, plus
  `anthropic` 2.10.0, `openai` 3.53.0, `onnxruntime` 1.32.0 and `numpy` 2.5.5
  (PyMuPDF 2.x pulls in `onnxruntime`). A `pyproject.toml` comment records that
  PyMuPDF 2.x has no wheels for Intel Macs, Windows ARM, 32-bit Windows or musl
  Linux.
- Build: setuptools (`requires = ["setuptools>=77"]`, kept by hand; Dependabot
  ignores setuptools in `.github/dependabot.yml`), src layout, package data
  `report/*.css`. Console script `pydelity = "pydelity.cli:main"`;
  `python -m pydelity` works through `__main__.py`.
- uv manages the environment (`required-version = ">=0.8.1"`, CI pins uv
  `0.13.8`), with a strict editable install so tests see only what a wheel would
  hold.
- Dev tools, exact pins: detect-secrets 1.5.0, interrogate 1.7.0, prek 0.5.11,
  pytest 9.2.0, pytest-cov 7.1.0, pytest-randomly 5.1.0, pytest-xdist 3.8.0,
  ruff 0.17.5, rust-just 1.59.0, twine 7.0.0, ty 0.0.105, zizmor 1.32.0.
- Docs site: Astro Starlight under `docs/` with pnpm (`docs/pnpm-lock.yaml`),
  versioned builds (`docs/versioning.mjs`, `docs/scripts/build-versions.mjs`).
  Node `24.22.3` is kept by hand in `.pre-commit-config.yaml` and `docs.yml`.
- `just` recipes run under bash
  (`set shell := ["bash", "-euo", "pipefail", "-c"]`); there are no
  Windows-native recipes.

## Structure and Boundaries

- `src/pydelity/__init__.py` — public API re-exports, `__version__`, and
  `logger.disable("pydelity")`; importing reads no settings and does not log.
- `src/pydelity/api.py` — `run`/`arun`, `survey`/`asurvey`,
  `measure`/`ameasure`, `estimate`/`aestimate`, `load`, plus
  `arun_with_questions` (used by the CLI). Sync functions call
  `utils/coroutines.py` `run_sync`. Each takes `pdf`, `config` (path, `Config`
  or mapping) and setting keywords; `allow_over_max_cost` on `run` and `survey`.
- `src/pydelity/cli.py` — one Typer command: argument `PDF`; options `--config`
  `-c`, `--instructions` `-i`, `--language` `-l`, `--output-dir` `-d`, `--model`
  `-m`, `--max-cost` `-mc`, `--overwrite` `-o`, `--yes` `-y`, `--verbose` `-v`,
  `--version`; help `-h`. It runs the whole pipeline, which is the survey only.
- `src/pydelity/config/` — `schemas.py` `Config` (top level: `advanced`,
  `instructions`, `languages`, `max_cost`, `model`, `output_dir`, `overwrite`,
  `pdf`; `extra="forbid"`), `AdvancedConfig` (`models`, `provider_retries`,
  `survey`, `uploads`), `SurveyConfig` (`check_retries` 0–5 default 2, `effort`
  default `high`, `max_output_tokens` default 32,000, `request_timeout_seconds`
  default 900), `ProviderEnv` (API keys from the environment only). `loading.py`
  `resolve_config` merges keywords over a JSON or YAML file over defaults and
  reports every problem in one `ConfigError`. There is no `pages` setting and
  only one `model` setting.
- `src/pydelity/pipeline/` — `runner.py` (`run_pipeline`, `run_survey_step`,
  `run_measure`, `run_estimate`, `load_run`) and `schemas.py` (`RunRecord`,
  `StepRecord`, `RunCost`, `WarningItem`, `RunResult`; `RunStatus`,
  `StepStatus`).
- `src/pydelity/costs/` — `ledger.py` (`cost.jsonl` append and read),
  `pricing.py` (genai-prices plus `advanced.models` overrides), `budget.py`
  (`SpendGuard`, `estimate_survey`, `format_usd`), `schemas.py`.
- `src/pydelity/providers/` — `profiles.py` (`DEFAULT_MODEL`, `parse_model`,
  per-provider `ProviderProfile`), `factory.py` (`build_model`,
  `structured_output`, `output_mode`), `ledger_model.py` (`LedgerModel`,
  `LedgerContext`), `uploads.py` (`attach_pdf`, `uploads.json`).
- `src/pydelity/surveying/` — step 1: `probe.py` (PyMuPDF facts), `facts.py`
  (`measure_facts`, `pdf_facts.json`), `prompts.py`, `agents.py`, `llm.py`,
  `validators.py` (checks C1–C7 and comparisons), `schemas.py`, `survey.py`.
- `src/pydelity/report/` — `images.py` (page JPEGs and `report/manifest.json`),
  `html.py` (`report.html`), `report.css`, `schemas.py`.
- `src/pydelity/utils/` — `files.py` (atomic writes, validated loads, temp-file
  cleanup), `fingerprints.py`, `pdf.py` (`open_pdf`, `PdfInfo`), `coroutines.py`
  (`run_sync`, `warn`, `collect_warnings`, `run_in_daemon_thread`), `prompts.py`
  (`PromptPair`).
- `src/pydelity/schema_versions.py` — one `"MAJOR.MINOR"` constant per output
  file (facts, ledger, manifest, run, survey, uploads), all `1.0`.
- `src/pydelity/errors.py` — `PydelityError` and subclasses
  (`BudgetExceededError`, `ConfigError`, `MissingApiKeyError`, `OutputError`,
  `PdfError`, `ProviderError`, `SurveyError`), `PydelityWarning`, CLI
  `ExitCode`.
- `scripts/` — `generate_reference_docs.py` (reference pages from the code),
  `smoke_installed_wheel.py` (wheel smoke test against the mock providers),
  `check_env_template.py`, `format_markdown.mjs`.
- `examples/config.json`, `examples/config.yaml` — every setting at its default.
- `docs/src/content/docs/` — `start/`, `guides/` (command line, configuration,
  costs, models and providers, outputs, Python, reruns), `reference/`
  (generated: CLI, configuration, Python API, `cost.jsonl`, `pdf_facts.json`,
  `pdf_survey.json`, `run.json`, `uploads.json`, survey checks), `faq.md`,
  `need-help.md`, `contributing/`.
- Git-ignored local folders: `data/` (holds `caps_english_hl_grade_3_fs.pdf`,
  `imnci.pdf`, `math_wolof_OA_fixed.pdf`), `pydelity-output/` (survey outputs
  for those three PDFs from pre-release builds that record version `0.0.1`, and
  `dev013-preview/`), `graveyard/`, `build/`. They are not baseline.
- KGForEdGlobal (`/Users/tzz/Projects/private/idi/KGForEdGlobal`) is outside the
  repo and read-only; see **KGForEdGlobal page extraction**.

## Nearest Analogues

- `src/pydelity/surveying/` is the analogue for a new step folder. Its split is
  `agents.py` (an `Agent` with `output_type=structured_output(model, T)`,
  `retries={"output": check_retries}`, and an `output_validator` that raises
  `ModelRetry(retry_message(failures))` while retries remain and keeps the last
  answer when `context.last_attempt`), `llm.py` (builds the request content,
  attaches the PDF, adds a `CachePoint`, maps PydanticAI errors to `SurveyError`
  or `ProviderError`), `prompts.py` (`PROMPT_VERSION = 1` and a function
  returning a `PromptPair`), `validators.py` (check functions returning
  `CheckFailure` lists, `check_results`, `review_issues`, `compare_with_facts`),
  `schemas.py` (the model's answer and the saved file), and `survey.py`
  (`saved_survey` reuse, `run_survey`, `build_survey`, `survey_inputs`,
  `survey_fingerprint`). Tests: `tests/pydelity/surveying/` (`test_probe.py`,
  `test_validators.py`, `test_survey.py`) and `tests/pydelity/test_api.py`,
  `test_cli.py`, `pipeline/test_runner.py`.
- The survey sends one request for the whole PDF (uploaded or inline) and writes
  one file. Step 2, as requested, works per selected page from rendered images
  and writes a file per page, so it has no existing analogue for per-page
  parallel requests, image rendering for a model, or per-page reuse.
- `src/pydelity/report/images.py` is the only code that renders pages: it
  renders each displayed page (`page.get_pixmap` with a zoom to about 1000 px
  wide) as a JPEG at quality 80 for the report.
- `src/pydelity/report/html.py` `_box` draws a box over a page image in percent
  of the displayed page's size, with kinds `region` and `field`; `_page_card`
  draws the survey's regions and the form fields.

## Commands

- `just install` — `uv sync --locked`, then `uv run --locked prek install`.
- `just lint` — `docs-reference`, then `lint-markdown`, `lint-python`
  (`ruff check --fix`, `ruff format`, `ty check`, `interrogate` over
  `scripts src tests`) and `lint-workflows` (zizmor).
- `just test` — pytest with `--numprocesses auto` and `--exitfirst`, then the
  docstring examples with `--doctest-modules src` in a separate session;
  `KEEP_GOING=1 just test` runs everything and writes failures to
  `.cache/test-errors`.
- `just build` — fresh `dist/` with `uv build`, then `twine check --strict`.
- `just docs`, `just docs-build` — serve or build the docs site (pnpm, frozen
  lockfile; `docs-build` also checks links). `just docs-reference` regenerates
  the reference pages; CI fails when they are stale.
- `uv run --locked python scripts/smoke_installed_wheel.py` — installs the built
  wheel in a fresh environment and runs the CLI and Python API against the mock
  providers.
- `python -m tests.fixtures.mock_providers --answer <answer JSON>` — runs the
  stand-in provider server by hand.
- `uv run prek run --all-files` — every git hook.
- `.venv/bin/python -m pytest` — runs the tests without uv, which works where uv
  cannot write its cache.
- `node .standards/bin/check.mjs` — STANDARDS consistency check.

## Conventions and Constraints

- Code style (`pyproject.toml`): Ruff, line length 88, rule families ANN, B, C4,
  C90, D, E, F, I, PL, PT, RET, RUF, S, SIM, UP, W; McCabe complexity at most
  10; NumPy docstrings with a blank line after each; import sections headed
  "Future Library", "Standard Library", "Third Party Library", "Package
  Library", "Local Folder". interrogate requires 100% docstring coverage of
  `scripts`, `src` and `tests`, private and nested functions included. ty
  type-checks all three.
- User conventions from the survey cycle (`next_cycle_inputs.md`): private
  globals, classes and functions come before public ones in each module,
  alphabetical within each group; American English; shipped code, config and
  docstrings never mention the development process (decision dates, DEV or AC
  IDs, KGForEdGlobal); each step's checks on model answers live in
  `<step>/validators.py`; prompts return a `PromptPair`, written the way
  KGForEdGlobal writes its prompts; output schema versions live in
  `schema_versions.py`; `justfile` recipes and `pyproject.toml` tables, keys and
  lists stay alphabetical.
- Step folders sit directly under `src/pydelity/`, named with an "-ing" word:
  `surveying/` now, then `extracting/` for step 2. Inside, model code follows
  the `agents.py`, `llm.py`, `prompts.py`, `validators.py`, `schemas.py` split.
  The user approves file and folder names before the step that creates them.
- Every public function that measures, estimates or runs has an async twin
  prefixed `a`; sync versions use `asyncio.run` only and raise `RuntimeError`
  naming the async function inside a running event loop. `load` stays sync.
- Every CLI option has a short form. The CLI shows warnings, errors, the cost
  estimate and the summary by default; `--verbose` shows everything; there is no
  `--quiet`.
- `examples/config.json` and `examples/config.yaml` hold every setting at its
  default; `tests/pydelity/config/test_loading.py` keeps them complete.
- Output files are written atomically (`utils/files.py` temp file plus
  `os.replace`), validated on load, and carry a `schema_version`. A field
  addition raises the minor version; removing, renaming or redefining a field
  raises the major version (`schema_versions.py`). `load_run` rejects a file
  whose major version differs.
- Settings models use `extra="forbid"` and `use_attribute_docstrings=True`; the
  reference docs are generated from field docstrings.
- No per-model limits (PDF size, pages, context windows) ship or are checked;
  the provider's error surfaces as `ProviderError`. There is no default
  `max_cost`.
- Test PDFs are real public-domain documents the user approves, under 500 KB
  each (the `check-added-large-files` hook rejects larger new files).
- A new runtime dependency's minimum version is its latest stable release on the
  day it is added.
- Commits follow Conventional Commits; a squash-merge title is the commit
  message and `feat:` makes a minor release through release-please. Commit
  messages never carry a `Co-Authored-By` trailer or other AI attribution. Work
  merges to `main` only after its cycle is signed off and STANDARDS is
  uninstalled on the branch; repo tooling must work without `.standards/`.
- Developer collaboration in the survey cycle was `STEPWISE`: files listed for
  review before each build step, a stop after each step, and each step report
  ending with the next step's plan. Self-checks used the real Anthropic and
  OpenAI APIs on small PDFs with the user's keys and recorded the spend; faults
  a provider cannot produce on demand used scratch scripts, never pydelity code.

## External Systems and Data

- Providers: Anthropic and OpenAI through PydanticAI, as
  `<provider>:<model-id>`; default `anthropic:claude-opus-5-5`. Keys come from
  `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` only (no `.env` loading). Structured
  output uses `NativeOutput` when the model profile supports JSON schema output,
  otherwise `PromptedOutput`. `effort` maps to Anthropic adaptive thinking or
  OpenAI `reasoning_effort` (`providers/profiles.py`). `ProviderProfile` holds
  token estimates per PDF page (Anthropic 4,784 image plus 3,000 text; OpenAI
  3,000 plus 3,000) and upload expiry bounds (Anthropic 1–2,160 hours, OpenAI
  1–720).
- PDF transport: `providers/uploads.py` uploads the whole PDF with the
  provider's Files API, falls back to sending it inline, reuses an upload with
  at least one hour left (`REUSE_MIN_REMAINING`), replaces an expired one, and
  records uploads in `uploads.json`.
- Prices: `genai-prices`, overridden per model by `advanced.models`.
- GitHub workflows (`.github/workflows/`): `ci.yml` (job "Lint and test" gates
  `lint-and-test` on Python 3.13, `test-py314`, and `wheel` builds plus the
  smoke test on ubuntu, macOS and Windows under bash), `docs.yml` (builds the
  site; publishes to GitHub Pages from a push when `main`'s version has its
  release tag), `release-please.yml`, `release.yml` (publishes to PyPI with
  Trusted Publishing in the `pypi` environment on a published GitHub release),
  `trufflehog-pr.yml`.
- KGForEdGlobal's KG stage is the first consumer; its contract and the
  corrections to the brief are in `artifacts/next_cycle_inputs.md` (Pipeline
  outcomes, KGForEdGlobal compatibility) and the survey cycle's context at
  `83743ef`. It loads `stitching/document_ir.json` with
  `DocumentIR.model_validate` and forbids undeclared keys, so it cannot read a
  pydelity file without KGForEdGlobal-side changes. Each KGForEdGlobal
  `TextUnit` needs a BCP-47 `language`.

### KGForEdGlobal page extraction

Read-only reference, read at HEAD `5e2d7cc` on `tz6/page-ir-extraction-cleanup`
(clean tree), the brief's pinned commit. Paths are under `backend/src/kgfeg/`.

- Flow (`entries/extract_page_ir.py`, `page_ir_extraction/`): for each page in a
  contiguous `[start_page, end_page)` range, sequentially, render a PNG, call
  `llm.extract_page_ir`, then fill `coord_space`, `doc_key`, `dpi`, `pdf_name`
  and `boundary_state` and write `extraction/page_irs/<NNNN>.json` (non-atomic,
  `utils/general.py` `write_to_json`). Any page error aborts the run.
  `extraction_run.json` is rewritten at start and end.
- Resume checks only that the page JSON and PNG exist (`extract_page_ir.py`
  lines 85–102); a reused PNG keeps its old DPI while `dpi` comes from config.
- Rendering (`page_ir_extraction/utils.py` `render_and_save_page_to_png`, lines
  712–768): `Matrix(dpi/72, dpi/72)`, `get_pixmap(alpha=False)`, PNG.
  `fix_rotation` (prerotate by the page's rotation) defaults to False and the
  entry does not set it. DPI is one setting, default 250 (`schemas.py`
  `ExtractionConfig`, line 3314).
- Agents (`page_ir_extraction/agents.py`): the extractor
  `Agent(..., output_retries=max_retries, output_type=wrap_output_type(PageIR))`
  with `max_retries` 3; its output validator runs the quality checks and raises
  `ModelRetry` with the error text, saving per-attempt artifacts. The validation
  agent returns `ExtractionValidationVerdict` (`passed`, `issues`, `rationale`,
  `corrected_page_ir`) and runs the same checks on the correction.
  `wrap_output_type` uses `PromptedOutput` for Anthropic (`model_registry.py`).
- Producer-verifier (`llm.py` `extract_page_ir`, lines 204–376): the validator
  runs once on every page; on a pass the extraction is kept; on a fail the
  correction is kept unless the correction guard rejects it. No loop back to the
  extractor. Verdicts are only logged, never saved. Both agents use the same
  model; requests carry the system prompt, a short user message, optional
  text-layer and table hints in `<text_layer>` and `<table_layer>` tags, and the
  full page PNG (no crops). No concurrency, no response cache.
- Page IR (`page_ir_extraction/schemas.py`): `PageIR.items` is a list of
  `Block | Table`, where list order is the reading order; items have no IDs and
  are referenced by index; only top-level items carry a `bbox` in pixels, origin
  top left (`coord_space: "px"`). `Block.block_type` (`utils/constants.py`
  `BlockType`): artifact, caption, figure, footnote, heading, list, paragraph;
  `boundary` (complete, resumed, truncated, both); `TextUnit` has `text`, BCP-47
  `language` and `text_en`; `Table` has rows of `TableCell` (`col_span`,
  `row_span`, no cell boxes), `header_row_count`, `repeats_header`; `FigureUnit`
  has `figure_kind` (14 values), `alt_text`, `caption`, `contains_text`,
  `embedded_text`. No role, label, container, form field or checkbox type
  exists; figures are not cropped. `BaseSchema` forbids extra keys.
- Prompts (`page_ir_extraction/prompts.py`): a system prompt of numbered rule
  sections (hard rules, Python-filled fields, bounding boxes, boundaries, block
  classes, content, languages, tables, lists, figures, text-layer hints) with
  the image size interpolated; user instructions are appended last under a
  "RUNTIME CURRICULUM INSTRUCTIONS" heading. Hard rule 2 (line 113) and
  validation checklist item 5 say "left column before right".
- Quality checks (`page_ir_extraction/validators.py`, run in fixed order by
  `llm.verify_page_ir_extraction_quality` with a 2 px tolerance): image size;
  bboxes present and in bounds; no duplicate or placeholder boxes; full-page
  boxes only for one figure; a forced retry on attempt 0 for a single full-page
  figure (also in the validator's own counter); footnote position; table
  integrity and collapse heuristics; continuity marks within the first or last
  five items; artifact plausibility; basic block invariants; `text_en` empty;
  gross reading order.
- Brief defects confirmed in the code: `validate_gross_reading_order` (line 836)
  rejects an upward jump that moves left (lines 869–871), the correct order for
  right-to-left columns; English-only lists and patterns at lines 28 (section
  titles), 425 (`^\s*section\s+\w+`) and 784 (`\bscan(ned)?\b`); full-page
  figure checks at 663 and 728; the letter-run tokenizer
  `_CONTENT_WORD_PATTERN = [^\W_]+` (`utils.py` line 29); file-existence resume;
  no form-field type; no crops; fixed DPI.
- Text-layer hints (`page_ir_extraction/utils.py`): page text from
  `get_text("text")`, used only when it has at least 20 characters, a printable
  share of at least 0.90 and at most 0.02 U+FFFD; table hints from
  `find_tables`. Hints are page-level text in the prompt, not matched to items.
  The correction guard compares per-page word counts (NFKC, casefold, at least
  two characters with a letter) and rejects a correction that adds words beyond
  both the text layer and the extraction; artifacts, alt text and embedded text
  are skipped. Running the regex with the system Python during this audit split
  Devanagari into single letters, which the length rule drops, and turned CJK
  into sentence-length runs.
- Tests (`backend/tests/kgfeg/page_ir_extraction/`): `test_llm.py` stubs the
  agents with `_StubAgent` and monkeypatching (no PydanticAI `TestModel`);
  `test_prompts.py`, `test_schemas.py`, `test_utils.py` (hint gates, rendering
  DPI and rotation with `uganda_regular.pdf` and `uganda_rotated.pdf`, guard),
  `test_validators.py`. The agents' output validators and the entry are not
  tested.
- Locked versions (`backend/uv.lock`): pydantic-ai 1.63.0, pydantic 2.12.5,
  PyMuPDF 1.26.7. pydelity runs PydanticAI 2.69 (output retries are
  `Agent(retries={"output": n})`) and PyMuPDF 2.1.

## Testing and Verification Baseline

- 105 tests plus 17 docstring examples (1 skipped) pass locally on Python 3.13.9
  (`.venv/bin/python -m pytest -q --numprocesses auto`, then
  `--doctest-modules src`, 2026-11-19).
- `tests/conftest.py`: an autouse fixture sets dummy API keys and points both
  SDKs' base URLs at a closed port, so no test reaches a provider; the
  `mock_providers` fixture starts `tests/fixtures/mock_providers.py`, a
  standard-library stand-in for Anthropic Messages and Files and OpenAI
  Responses and Files, which returns queued answers with set usage and can
  inject faults. `facts_of` and `pdf_path` fixtures read the test PDFs.
  `tests/fixtures/survey_answers/` holds a canned survey answer.
- Test PDFs (`tests/fixtures/pdfs/`, sources and hashes in `SOURCES.md`): BLS
  slide deck (16 pages, images), CAPS pages 28–35 (sideways tables on pages with
  rotation attribute 0, page labels), IRS Form 1040 1950 (sideways table
  headings), IRS Form 1040A 1965 scan (no text layer), IRS W-9 (fillable: 8
  checkboxes, 15 text fields, XFA), IRS Publication 1 Arabic (two and three
  right-to-left columns), Publication 1 Simplified Chinese (two and three
  columns), W-9 instructions (two columns, bookmarks), Japan Official Gazette
  (vertical Japanese, signature field). None has a page whose rotation attribute
  is 90, 180 or 270.
- pytest settings: `--strict-config`, `--strict-markers`, `xfail_strict`, marker
  `costs-money`; pytest-randomly shuffles order. Coverage is configured
  (`branch`, `concurrency = ["thread"]`) but no run enforces it.
  `[tool.coverage.report]` still holds the scaffold `def cli` exclusion and the
  `omit` for `./src/pydelity/__init__.py`.
- No test covers `LedgerModel.request_stream`.

## Relevant Existing Behavior

- Output folder (default `pydelity-output/<PDF stem>` under the current
  directory): `run.json`, `pdf_facts.json`, `pdf_survey.json`, `cost.jsonl`,
  `uploads.json`, `report.html`, `report/manifest.json`, and
  `report/pages/<NNNN>.jpg`. One folder per PDF is the unit of resume and spend;
  leftover temp files are removed at the start of a run.
- Reuse: `pdf_facts.json` is reused while its fingerprint matches;
  `pdf_survey.json` while `survey_fingerprint` matches the PDF SHA-256, facts
  fingerprint, model, instructions, languages, survey settings (not
  `request_timeout_seconds`), `PROMPT_VERSION` and the survey schema version,
  and `overwrite` is off. `PROBE_VERSION` (`surveying/probe.py`) and
  `PROMPT_VERSION` (`surveying/prompts.py`) are both 1.
- The runner is written for one step: `_SURVEY_STEP = "survey"`, `_Run` holds
  survey-only fields, `_record` builds one `StepRecord`, `review` is the
  survey's issues, every warning after the start is attributed to the survey,
  and `_log_summary` lists `steps[0].outputs`. `load_run` reads only `run.json`,
  `pdf_facts.json`, `pdf_survey.json` and `cost.jsonl`. `StepRecord.name`,
  `LedgerEntry.step` and `StepEstimate.name` are plain strings.
- Run statuses: `running`, `completed`, `failed`, `stopped` (a `max_cost` no or
  a declined confirmation), `interrupted`; step statuses add `reused` and
  `skipped`. `run.json` and the report are written before an error reaches the
  caller.
- Spend: `SpendGuard` checks a plan bound before spending and each request's
  bound before sending, against the ledger's recorded total only (requests in
  flight are not counted), asks at most once per run under an `asyncio.Lock`,
  and a yes lets the rest of the run exceed `max_cost`. `LedgerModel` bounds a
  request by its text characters (4 per token), each document at the PDF's page
  count times the provider's per-page tokens, and `max_tokens`; images are not
  counted (`_user_content_size`). `estimate_survey` covers only the survey; the
  CLI asks before spending (skipped with `--yes`), and the Python API never
  asks.
- `ReviewIssue` (`surveying/schemas.py`) has `step: Literal["survey"]`, `check`
  limited to the survey's check and comparison names, `message`, `details`,
  `page_index`, and no item field. `run.json` `review[]` uses it.
- Profile (`pdf_survey.json` `profile`): `labels` (name, role, kinds,
  description; always ends with `other`), `languages` (standard BCP-47),
  `writing_direction` (`default` plus `ranges` of `ltr`, `rtl`, `ttb`),
  `rotation` (clockwise degrees that make the displayed page's content upright),
  `page_numbering`, `continuation_notes`, `start_markers`, `user_instructions`.
  The ranges and the artifact mapping in `proposal` are stored as the model
  answered when check retries run out, so they can overlap, run past the PDF, or
  name missing or repeated line IDs; the survey's own comparison takes the first
  range covering a page. `proposal.artifacts` and `proposal.non_artifact_lines`
  sit outside `profile`, which the survey design named as what steps 2–3
  fingerprint.
- Item vocabulary (`surveying/schemas.py`): `ItemKind` `code`, `field`,
  `figure`, `formula`, `list`, `table`, `text`; `ItemRole` `artifact`, `aside`,
  `body`, `caption`, `footnote`, `heading`, `navigation`.
- Coordinates: survey regions and form fields are `[x0, y0, x1, y1]` in points
  on the displayed page (after the page's rotation attribute, origin top left):
  form-field boxes are `widget.rect * page.rotation_matrix`, region fractions
  are scaled by `PageFacts.width_pt`/`height_pt`. Text-angle facts are counted
  counterclockwise on the displayed page.
- Facts per page (`pdf_facts.json`): text counts and quality (`none`, `good`,
  `garbled`), direction, orientation, printed number, rotation attribute, size
  in points; per PDF: bookmarks, form fields (type, name, value, checked,
  options, bbox), structure-tag quality, repeated lines with IDs and bands, page
  numbering. The page text itself is not stored. The probe reads text with
  `get_text("dict")` and flags `TEXT_PRESERVE_LIGATURES`,
  `TEXT_PRESERVE_WHITESPACE`, `TEXT_MEDIABOX_CLIP`.
- Known probe defects left open (`next_cycle_inputs.md`, review findings): a
  checked checkbox without a normal appearance makes `on_state()` raise and the
  form fact unreadable; letter-style page labels read as roman numerals;
  structure-tag quality misrated for indirect `/K` arrays and a capped walk;
  `run.json` records `pdf_transport: null` for a failed step that sent the PDF;
  the Python API leaves PydanticAI's first-run banner on; `costs/pricing.py`
  `_config_price` treats a `0` cache price as unset. A probe fix must raise
  `PROBE_VERSION`, which reruns every saved survey.
- `report/images.py` renders a page image only when missing, and all of them
  again when the manifest names another PDF.

## Known Unknowns

- No real public PDF with a page whose rotation attribute is 90, 180 or 270 is
  in the repo; whether a rotated copy of a real document counts as a real test
  PDF was never asked. It matters for testing upright rendering and box mapping.
  KGForEdGlobal's test fixtures
  `backend/tests/fixtures/utils/uganda_regular.pdf` and `uganda_rotated.pdf` (3
  pages each, rotation attribute 90 on every page, 152 KB and 184 KB) exist, but
  their source and copyright status were not established, and the survey cycle's
  21 checked candidates did not include them.
- PyPI state (0.0.1 yanked, 0.1.0 and 0.1.1 published) is user input and was not
  checked here; it does not affect step 2's code.
- How PyMuPDF 2.1 rendering and text extraction behave on Windows is untested
  beyond CI's wheel smoke test, which runs the survey against the mock
  providers.

## Evidence

- `pyproject.toml`, `uv.lock`, `.python-version`, `justfile`,
  `.github/workflows/*.yml`, `.github/dependabot.yml`, `.pre-commit-config.yaml`
  — stack, pins, recipes, CI and release.
- `src/pydelity/**` — modules and behavior cited above, especially
  `pipeline/runner.py`, `config/schemas.py`, `costs/budget.py`,
  `providers/ledger_model.py`, `providers/factory.py`, `providers/profiles.py`,
  `surveying/{agents,llm,survey,schemas,probe}.py`, `report/{images,html}.py`,
  `schema_versions.py`.
- `tests/conftest.py`, `tests/fixtures/mock_providers.py`,
  `tests/fixtures/pdfs/SOURCES.md` — test harness and PDFs.
- `.venv/bin/python -m pytest` — 105 passed; doctests 17 passed, 1 skipped.
- `git log main`, `git diff --name-only main..HEAD`, `git cat-file -t 83743ef`,
  `git show 83743ef:.standards/CONTEXT.md`, `CHANGELOG.md` — history and
  records.
- `artifacts/next_cycle_inputs.md`, `artifacts/design_brief.md`, and the active
  request in `.standards/STATE.md` — user decisions and inputs.
- `pydelity-output/*/run.json`, `pdf_survey.json` — local survey runs (not
  baseline).

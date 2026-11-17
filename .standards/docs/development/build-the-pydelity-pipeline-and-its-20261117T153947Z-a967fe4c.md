<!-- STANDARDS
Artifact: DEVELOPMENT
Cycle: build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c
-->

# Development Plan

`Cycle`: `build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c` `Mode`:
`STEPWISE` `User Style`: `tony` `User Style Locked`: `false` `Status`:
`PROPOSED` `Verification Cadence`: `AFTER_IMPLEMENTATION` `Current Increment`:
`NONE`

## Implementation Contract

- `Scope`:
  `.standards/docs/scope/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c.md`
- `Architecture`:
  `.standards/docs/specs/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c.md`
- `Request`:
  `Build step 1 (survey) of pydelity with the run features it needs (config, CLI and Python API, input limits, cost ledger and spend controls, resume, review list, HTML report) for Anthropic and OpenAI models; CI on Python 3.13 and 3.14 with wheel installs on Windows, macOS and Linux; the 0.1.0 PyPI release workflow; and the Astro Starlight docs site.`

## Build Steps

### DEV-001 — Package foundation: dependencies, errors, import-safe root, general utilities

`Status`: `PENDING` `Depends On`: `NONE` `Acceptance`: `AC-010, AC-018`

**Goal**

Make pydelity a real package that later steps build on: runtime dependencies,
the errors component, an import-safe package root and the general utilities.

**Affected Area**

`pyproject.toml` and `uv.lock` (`uv add` pydantic, pydantic-settings[yaml],
pydantic-ai-slim[anthropic,openai], loguru, typer, pymupdf; twine exact in the
dev group), `.template.env` (only `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`),
`src/pydelity/__init__.py`; candidates `src/pydelity/errors.py` and
`src/pydelity/utils/{files,fingerprints,pdf}.py`.

**Expected Outcome**

`import pydelity` exposes `__version__`, disables loguru for `pydelity` and
reads no file, network or environment. `PydelityError` with `ConfigError`,
`PdfError`, `InputLimitError`, `MissingApiKeyError`, `BudgetExceededError` and
`SurveyError`, plus `PydelityWarning`. Utilities: atomic UTF-8 write (temp file
in the same folder, flush, `fsync`, `os.replace`), validated load into a
Pydantic model that reports damage instead of raising, stale `*.tmp-*` cleanup,
canonical-JSON `sha256:` fingerprints, and opening a PDF (full SHA-256 ported
from KGForEdGlobal `utils/pdf.py`, page count, bytes; `PdfError` for
password-protected, empty or unopenable files).

**Self-Check**

`just lint`; `just test` (existing smoke tests); a scratchpad script exercising
atomic write and load, fingerprints and PDF opening; `import pydelity` with an
empty environment prints nothing.

### DEV-002 — Test fixture PDFs and their generator

`Status`: `PENDING` `Depends On`: `DEV-001` `Acceptance`: `AC-005, AC-021`

**Goal**

Give the probe, the mocked survey and the wheel smoke test small, reproducible
PDFs covering the cases AC-005 names.

**Affected Area**

Candidates `scripts/make_test_pdfs.py` and `tests/fixtures/pdfs/*.pdf`.

**Expected Outcome**

One committed script regenerates every fixture with PyMuPDF: a plain multi-page
PDF with repeated header and footer lines, printed page numbers with an offset,
roman front matter and bookmarks; two-column right-to-left text; Chinese and
Japanese text, including vertical writing; a fillable form with text fields,
checkboxes and radio buttons; rotated content (sideways text on pages whose
rotation attribute is 0, and a page with rotation attribute 90); image-only
pages with no text layer; control and private-use characters; a tagged PDF with
a structure tree and an untagged twin. Each file stays under the 500 KB hook
limit. If PyMuPDF cannot write a valid structure tree, Developer stops and asks
the user to approve a small public tagged PDF instead (design Build Plan step
2).

**Self-Check**

Run the script twice and compare outputs; inspect each fixture with PyMuPDF
(pages, text, widgets, table of contents, `StructTreeRoot`, rotation) and its
size; `just lint`.

**Implementation Notes**

Font sources for right-to-left and CJK text are settled at the step (PyMuPDF's
built-in CJK fonts; Hebrew or Arabic may need a committed OFL font file) and
listed before it starts.

### DEV-003 — Model catalog and input-limit check

`Status`: `PENDING` `Depends On`: `DEV-001` `Acceptance`:
`AC-011, AC-012, AC-013`

**Goal**

Know each supported provider's and model's PDF limits, and stop an oversized PDF
before any upload or request.

**Affected Area**

Candidates `src/pydelity/models/{schemas,catalog}.py`.

**Expected Outcome**

Model settings parse as `<provider>:<model-id>` with provider `anthropic` or
`openai` only. Provider facts: transports (upload, then in-request fallback),
OpenAI upload purpose `user_data`, upload expiry range and default. Entries for
`anthropic:claude-opus-5-5` and one current OpenAI model recommended for PDF
input, each with `max_pdf_pages`, `max_pdf_bytes`, `max_request_pdf_bytes`,
`context_window_tokens`, `pdf_tokens_per_page`, `limits_source` (URL and date),
effort mapping and output mode, rechecked against the providers' docs.
`advanced.models` overrides merge over an entry. The check raises
`InputLimitError` naming the model, the limit, its value and the PDF's value,
with the split-or-switch advice; an unknown model warns and proceeds; estimated
input tokens over the context window warn. Confirms whether the locked
`genai-prices` prices the default model and ships catalog prices if not.

**Self-Check**

Scratchpad script covering page and byte overruns, overrides, an unknown model
and the context warning; `just lint`.

**Implementation Notes**

Rechecking limits reads `platform.claude.com` and `developers.openai.com`.

### DEV-004 — Configuration

`Status`: `PENDING` `Depends On`: `DEV-003` `Acceptance`:
`AC-004, AC-007, AC-008, AC-009`

**Goal**

Resolve and validate every setting before any work, from defaults, an optional
JSON or YAML file, and CLI options or Python keywords.

**Affected Area**

Candidates `src/pydelity/config/{schemas,loading}.py`.

**Expected Outcome**

`Config` (`pdf`, `instructions`, `languages`, `output_dir`, `model`, `max_cost`,
`overwrite`, `advanced`) and `AdvancedConfig` (`survey`, `uploads`, `models`)
with `extra="forbid"` and the design's defaults and bounds; BCP-47 syntax
validation; `.json`, `.yaml` and `.yml` loading with relative paths resolved
against the config file's folder; precedence keywords or CLI over file over
defaults, with the CLI `PDF` winning; `expiry_hours` checked against the
selected provider's range; one `ConfigError` listing every invalid setting by
dotted path. `ProviderEnv` (pydantic-settings, environment only, no `.env`,
`SecretStr`) built per run, and `MissingApiKeyError` for the selected provider's
empty key.

**Self-Check**

Scratchpad script with valid and invalid JSON and YAML files, several errors at
once, precedence cases and a missing key; `just lint`.

### DEV-005 — Survey probe (measured facts)

`Status`: `PENDING` `Depends On`: `DEV-001, DEV-002` `Acceptance`:
`AC-001, AC-005, AC-006`

**Goal**

Measure everything the survey can know about a PDF without a model.

**Affected Area**

Candidates `src/pydelity/steps/survey/{schemas,probe}.py`.

**Expected Outcome**

Facts schemas and the `kind` and `role` enums (design decision 8). The probe
fills `facts` by the design's measurement rules: per-page text quality,
orientation (rotation-attribute aware, vertical lines excluded), inline
direction from Unicode bidi classes, printed numbers from page labels or top and
bottom bands, page-numbering ranges, repeated lines with normalisation and caps,
bookmarks, form fields with checked states and XFA presence, and structure-tree
quality with a node cap. Every threshold is a named constant; no word lists or
document-type terms. A bookmarks, forms or structure read that fails is recorded
as unavailable, in the shape the corrected design sets, and never fails the run.

**Self-Check**

Run the probe on every fixture and compare with what the generator wrote;
`just lint`.

### DEV-006 — Mock provider server

`Status`: `PENDING` `Depends On`: `DEV-001` `Acceptance`: `AC-021, AC-023`

**Goal**

Let the survey, the wheel smoke script and Tester's tests run both providers'
real PydanticAI adapters with no route to a provider.

**Affected Area**

Candidate `tests/fixtures/mock_providers.py` (standard library only).

**Expected Outcome**

A loopback HTTP server, reached through `ANTHROPIC_BASE_URL` and
`OPENAI_BASE_URL`, that answers Anthropic Messages and Files API calls and
OpenAI Responses and Files API calls with canned bodies: a structured survey
answer the caller supplies, usage figures, upload success, "file not found",
upload failures (server error, authentication failure), and a request log the
caller can inspect. No production code path exists only for it.

**Self-Check**

Drive it with the `anthropic` and `openai` SDK clients from a scratchpad script;
`just lint`.

### DEV-007 — Cost ledger, pricing, estimate and budget guard

`Status`: `PENDING` `Depends On`: `DEV-001, DEV-003` `Acceptance`:
`AC-014, AC-015, AC-016`

**Goal**

Price, record and limit every model request.

**Affected Area**

Candidates `src/pydelity/costs/{schemas,ledger,pricing,budget}.py`.

**Expected Outcome**

Ledger-entry and `CostEstimate` schemas; `cost.jsonl` appends with flush and
`fsync` under an in-process lock, and a reader that skips a damaged trailing
line with a warning; pricing through PydanticAI's `ModelResponse.cost()` with
`advanced.models` price overrides and `price_source`, unpriced responses
recorded as null; the estimate formulas with named constants; a budget guard
that refuses a request when folder spend plus that request's upper bound exceeds
`max_cost`, and refuses an unpriced model when `max_cost` is set. Money is
`Decimal`; genai-prices runtime updates stay off.

**Self-Check**

Scratchpad script writing and reading a ledger (including a damaged last line),
pricing a synthetic response, estimate figures and guard decisions; `just lint`.

### DEV-008 — Model factory and LedgerModel

`Status`: `PENDING` `Depends On`: `DEV-003, DEV-004, DEV-006, DEV-007`
`Acceptance`: `AC-011, AC-014, AC-016`

**Goal**

Build every model through one factory that applies provider settings and records
every request.

**Affected Area**

Candidates `src/pydelity/models/{factory,ledger_model}.py`.

**Expected Outcome**

`build_model` returns the Anthropic or OpenAI Responses model with the API key
from `ProviderEnv`, the request timeout, max output tokens, the effort mapping
(Anthropic adaptive thinking with effort; OpenAI reasoning effort) and the
provider's output mode (`NativeOutput` or `PromptedOutput`, never forced
`tool_choice`), wrapped in `LedgerModel`, a PydanticAI `WrapperModel` that asks
the budget guard before each request and appends a ledger line after each
response. Ported from KGForEdGlobal `model_registry.py` without its hand-kept
model set.

**Self-Check**

Scratchpad agent runs against the mock server for both providers, checking
requests, ledger lines and a budget refusal; `just lint`.

### DEV-009 — PDF uploads, reuse and in-request fallback

`Status`: `PENDING` `Depends On`: `DEV-008` `Acceptance`:
`AC-011, AC-012, AC-018, AC-021`

**Goal**

Send the whole PDF once per provider and keep it for reuse, with the in-request
path as the fallback.

**Affected Area**

Candidate `src/pydelity/models/uploads.py`.

**Expected Outcome**

Uploads through each provider's Files API (OpenAI purpose `user_data`) with
expiry from `advanced.uploads.expiry_hours` or the provider maximum;
`uploads.json` written atomically after a successful upload, one record per
provider and PDF SHA-256; reuse while at least one hour remains; one re-upload
after "file not found"; a damaged `uploads.json` treated as empty. When the
upload path fails (anything but an authentication failure, after the SDK's own
retries), the step switches to `BinaryContent` for the rest of the step run,
records a warning and `pdf_transport: request`, writes no upload record, and
raises `SurveyError` when the PDF is over the in-request limit. An
authentication failure stops the run.

**Self-Check**

Scratchpad runs against the mock server covering upload, reuse, re-upload,
fallback, the authentication stop and the too-large fallback; `just lint`.

### DEV-010 — Survey proposal, profile, prompt and checks

`Status`: `PENDING` `Depends On`: `DEV-005` `Acceptance`:
`AC-002, AC-003, AC-004, AC-006`

**Goal**

Define what the model proposes and how Python checks it.

**Affected Area**

Candidates `src/pydelity/steps/survey/{schemas,prompt,checks}.py`.

**Expected Outcome**

The model-facing proposal schema (strings, integers, booleans, enums, arrays and
objects only; region boxes as page fractions), the stored `profile` and the
`PdfSurvey` model for `pdf_survey.json` 1.0; a document-type-neutral prompt with
`PROMPT_VERSION` carrying the facts summary, user instructions and languages;
checks C1–C7 returning failures that name the check, the pages and the measured
values.

**Self-Check**

Scratchpad script running the checks on hand-made passing and failing proposals
against fixture facts; a search of code and prompt for document-type terms and
word lists; `just lint`.

### DEV-011 — Survey step

`Status`: `PENDING` `Depends On`: `DEV-009, DEV-010` `Acceptance`:
`AC-002, AC-003, AC-004, AC-011, AC-017, AC-018`

**Goal**

Run the survey end to end and store a checked profile.

**Affected Area**

Candidate `src/pydelity/steps/survey/step.py`.

**Expected Outcome**

The fingerprint from the design's inputs; reuse of a valid, matching
`pdf_survey.json` unless `overwrite`, and regeneration of a damaged one; the
agent built through `build_model` with the uploaded file, a cache breakpoint
after the PDF and facts summary, and an output validator that raises
`ModelRetry` while retries remain and, on the last attempt, accepts and records
still-failing checks as review issues. Python adds `other`, merges languages,
stores `user_instructions`, converts region boxes to points and writes
`pdf_survey.json` atomically. A refusal or an answer that never parses raises
`SurveyError`.

**Self-Check**

Scratchpad survey runs on fixtures against the mock server for both providers:
pass, retry then pass, still failing after retries, reuse, a changed-input rerun
and `overwrite`; `just lint`.

### DEV-012 — Run orchestration

`Status`: `PENDING` `Depends On`: `DEV-004, DEV-007, DEV-011` `Acceptance`:
`AC-014, AC-016, AC-018, AC-019`

**Goal**

Wrap steps in a run that owns the output folder, `run.json`, the review list and
interrupts.

**Affected Area**

Candidates `src/pydelity/pipeline/{schemas,runner}.py`.

**Expected Outcome**

Settings resolved and validated, the PDF opened and limit-checked, the folder
prepared (stale temp files removed; a warning when `run.json` names another
PDF); `run.json` written at start and end with steps, cost (`run_usd`,
`by_step`, `output_folder_usd`, `unpriced_requests`), the review list (reused
outputs' issues included), warnings and error; `failed`, `stopped` and
`interrupted` recorded before re-raising, with `KeyboardInterrupt` caught and
re-raised. A planning hook gives the CLI the estimate before any spend.

**Self-Check**

Scratchpad runs against the mock server covering completion, a budget stop then
a resume with a higher `max_cost`, an injected error and a simulated interrupt;
`just lint`.

### DEV-013 — HTML report

`Status`: `PENDING` `Depends On`: `DEV-012` `Acceptance`: `AC-020`

**Goal**

Show the survey's findings on page images.

**Affected Area**

Candidates `src/pydelity/report/{html,images}.py`.

**Expected Outcome**

`report.html` and `report/pages/<NNNN>.<jpg|png>` (about 1000 px wide,
re-rendered only when missing or when `report/manifest.json`'s PDF SHA-256
differs): run header, cost, review list, profile, facts summary, and one card
per page with region and form-field boxes as percent-positioned CSS overlays and
the page's findings. Static, no JavaScript, no external URLs, every inserted
string escaped; written at the end of every run that got past input validation.

**Self-Check**

Reports for completed and failed fixture runs opened from disk; escaping checked
with a hostile label; `just lint`.

**Implementation Notes**

Loads the Developer HTML and CSS styles.

### DEV-014 — Python API

`Status`: `PENDING` `Depends On`: `DEV-012, DEV-013` `Acceptance`:
`AC-010, AC-015`

**Goal**

Expose `run`, `survey` and `estimate` and the public types from the package
root.

**Affected Area**

Candidate `src/pydelity/api.py`; `src/pydelity/__init__.py`.

**Expected Outcome**

Synchronous `run`, `survey` and `estimate` taking `pdf`, `config` (a path, a
`Config` or a mapping) and setting keywords. They never prompt or read stdin,
and they work inside a running event loop (on a worker thread). The root
re-exports them with `Config`, the result models, `CostEstimate`, the errors and
`PydelityWarning`; import stays free of side effects.

**Self-Check**

Scratchpad calls of all three against the mock server, including from inside
`asyncio.run`; import with an empty environment prints nothing; `just lint`.

### DEV-015 — CLI

`Status`: `PENDING` `Depends On`: `DEV-014` `Acceptance`:
`AC-007, AC-008, AC-009, AC-015, AC-019`

**Goal**

Run the survey from the command line with nothing but a PDF path.

**Affected Area**

Candidates `src/pydelity/cli.py` and `src/pydelity/__main__.py`;
`pyproject.toml` (`[project.scripts]`).

**Expected Outcome**

The design's options and flow (estimate, spend so far and `max_cost`;
confirmation, `--yes`, the non-interactive stop), exit codes (0, 1, 2, 3, 130),
logging levels and the end-of-run summary with review issues; the `pydelity`
console script and `python -m pydelity`.

**Self-Check**

The installed `pydelity` against the mock server: `--yes`, piped stdin without
`--yes`, a declined prompt, invalid settings and `--version`; `just lint`.

### DEV-016 — Wheel build and smoke script

`Status`: `PENDING` `Depends On`: `DEV-015` `Acceptance`: `AC-023, AC-024`

**Goal**

Show that a built wheel installs and runs on any supported platform.

**Affected Area**

`justfile` (`build`); candidate `scripts/smoke_installed_wheel.py`.

**Expected Outcome**

`just build` cleans `dist/`, runs `uv build` and `twine check --strict`. The
standard-library smoke script makes a fresh venv with pip, installs the wheel,
starts the mock server, and runs the console script (`--yes`) and the Python API
with each provider on a fixture PDF, asserting exit codes and valid outputs; it
handles Windows paths and scripts.

**Self-Check**

`just build`, then the smoke script on macOS; `just lint`.

### DEV-017 — CI jobs for Python 3.14, wheels and the gate

`Status`: `PENDING` `Depends On`: `DEV-016` `Acceptance`: `AC-022, AC-023`

**Goal**

Test every supported Python version and platform while keeping the required
check name.

**Affected Area**

`.github/workflows/ci.yml`.

**Expected Outcome**

Jobs "Lint and test (Python 3.13)", "Test (Python 3.14)" and "Wheel install
(`<os>`)" on Ubuntu, Windows and macOS, and a gate job named "Lint and test"
that fails unless every needed job succeeded; SHA-pinned actions, least
privilege, timeouts and concurrency as the repo already does.

**Self-Check**

`just lint-workflows`; a local Python 3.14 test run through uv. The workflow
itself runs only once pushed, so it stays unverified until then.

### DEV-018 — Release workflow, package metadata and 0.1.0 evidence

`Status`: `PENDING` `Depends On`: `DEV-016` `Acceptance`:
`AC-024, AC-025, AC-026, AC-036`

**Goal**

Make release-please's GitHub release publish 0.1.0 to PyPI.

**Affected Area**

Candidate `.github/workflows/release.yml`; `pyproject.toml` (description,
classifiers, `Documentation` URL); `release-please-config.json` only if the
evidence calls for `release-as`.

**Expected Outcome**

`release.yml` as designed: the tag must equal `v` plus the version, `uv build`,
`twine check --strict`, an artifact, and a `publish` job in environment `pypi`
holding only `id-token: write` with a SHA-pinned `pypa/gh-action-pypi-publish`;
zizmor clean. Metadata describes the usable survey release. Evidence, from
release-please v5.0.0's bundled source or a dry run against a throwaway local
repository, that manifest `0.0.1` plus one `feat:` commit yields 0.1.0;
otherwise the `release-as` fallback.

**Self-Check**

`just lint-workflows`; `just build`; the AC-036 evidence recorded here.

### DEV-019 — Docs site scaffold and versioned build

`Status`: `PENDING` `Depends On`: `NONE` `Acceptance`: `AC-027, AC-028, AC-030`

**Goal**

Build an Astro Starlight site the way IDinsight/standards builds its own.

**Affected Area**

Candidate `docs/` (`package.json` with exact versions and pinned pnpm,
`pnpm-lock.yaml`, `astro.config.mjs` with `base: /pydelity`, a `.md` page
skeleton and sidebar under `src/content/docs/`, `scripts/check-links.mjs`,
`scripts/build-versions.mjs`, `src/versioning/`); `justfile` (`docs`,
`docs-build`); `.gitignore`; `.github/dependabot.yml` (npm for `/docs`);
`.pre-commit-config.yaml` only if `pnpm-lock.yaml` exceeds 500 KB.

**Expected Outcome**

The current tree builds, and a broken internal link or fragment fails the link
check. The versioned build (stable `vX.Y.Z` tags from 0.1.0, each tag's
`pyproject.toml` version equal to the tag) serves the latest release at the root
and each release under `/v/<version>/`, with `versions.json` and a selector.

**Self-Check**

`just docs-build`; a deliberately broken link fails it; the versioned build in a
scratch clone with a local, never-pushed test tag; `just lint`.

**Implementation Notes**

Reads IDinsight/standards from GitHub. Has no dependency, so it can be taken
earlier if the user prefers.

### DEV-020 — Docs workflow

`Status`: `PENDING` `Depends On`: `DEV-019` `Acceptance`: `AC-027, AC-029`

**Goal**

Build and check the site on pull requests, and deploy it only once the version
on `main` has its tag.

**Affected Area**

Candidate `.github/workflows/docs.yml`.

**Expected Outcome**

Pull requests build the current tree and run the link check; pushes to `main`,
`v*` tags and `workflow_dispatch` run the versioned build when a supported tag
exists; `deploy` (`pages: write`, `id-token: write`, environment `github-pages`)
runs only when `v<pyproject version>` exists; zizmor clean.

**Self-Check**

`just lint-workflows`; the tag-existence logic exercised in the scratch clone.

### DEV-021 — Generated reference pages

`Status`: `PENDING` `Depends On`: `DEV-015, DEV-019` `Acceptance`: `AC-032`

**Goal**

Keep the reference pages in step with the code.

**Affected Area**

Candidate `scripts/generate_reference_docs.py`;
`docs/src/content/docs/reference/*.md`; `justfile` (`docs-reference`, run by
`lint` before `lint-markdown`).

**Expected Outcome**

Generated pages for configuration, CLI, Python API, `pdf_survey.json`,
`run.json`, `cost.jsonl`, `uploads.json` and the survey checks, each marked as
generated and including the measurement and estimate constants; regenerating
after Markdown formatting is byte-identical, so CI's `git diff --exit-code`
catches a stale page.

**Self-Check**

`just lint` twice with no diff; a deliberate settings change makes a page stale;
`just docs-build`.

## Plan Notes

- Collaboration: `STEPWISE`. The user also asked that before each step Developer
  lists the files and folders it will create or change and waits for their
  review; after each step Developer stops for the go-ahead to the next.
- File and folder names are the user's decision (design, **Components**). The
  proposed layout below needs their sign-off with the plan and again before each
  step. The orchestration and step folders avoid the names `run` and `survey` at
  the package root, where a subpackage would shadow the public `pydelity.run`
  and `pydelity.survey` functions.

  ```text
  src/pydelity/
    __init__.py         public API re-exports, __version__, logger.disable
    __main__.py         python -m pydelity
    api.py              run, survey, estimate
    cli.py              Typer CLI
    errors.py           PydelityError and subclasses, PydelityWarning
    config/             schemas.py (Config, AdvancedConfig, ProviderEnv), loading.py
    costs/              schemas.py, ledger.py, pricing.py, budget.py (estimate, guard)
    models/             schemas.py, catalog.py, factory.py, ledger_model.py, uploads.py
    pipeline/           schemas.py (run.json, review issues), runner.py
    report/             html.py, images.py
    steps/survey/       schemas.py, probe.py, prompt.py, checks.py, step.py
    utils/              files.py, fingerprints.py, pdf.py
  scripts/              make_test_pdfs.py, smoke_installed_wheel.py,
                        generate_reference_docs.py
  tests/fixtures/       mock_providers.py, pdfs/
  docs/                 Astro Starlight site
  .github/workflows/    release.yml, docs.yml (new); ci.yml (changed)
  ```

- Ownership: formal tests, the autouse test guard fixture and verification
  evidence are Tester's. The fixture PDFs, the mock provider server and the
  smoke script are reusable project assets the design's Build Plan assigns to
  Developer; Tester may extend them.
- `AC-031`, `AC-033`, `AC-034` and `AC-035` have no Developer step: they rest on
  Documenter's pages and README and on the user's review of real runs.
- User style `tony` names pylint and mypy; this repo enforces the same intent
  with Ruff (`PL`, `C90`) and ty, which Developer uses.
- Project references loaded: `NONE` (`.standards/project-references/` does not
  exist).

### Suspended Assignment 1

`Recovery Frame`: `1` `Recovery Reason`:
`Design leaves pdf_survey.json fields open: how an unreadable probe fact (bookmarks, forms, structure) is recorded, writing_direction.ranges[] item fields, the artifacts[].position value set, and checks[].failures item shape.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`scope and design at commit 5be0f98; this plan draft` `Next Action`:
`Reconcile DEV-005 and DEV-010 with the corrected design, then present the plan for approval.`

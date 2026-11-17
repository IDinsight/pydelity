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
  `Build step 1 (survey) of pydelity with the run features it needs (config, CLI and Python API, provider errors, cost ledger and spend controls, resume, review list, HTML report) for Anthropic and OpenAI models; CI on Python 3.13 and 3.14 with wheel installs on Windows, macOS and Linux; the 0.1.0 PyPI release workflow; and the Astro Starlight docs site.`

## Build Steps

### DEV-001 — Package foundation and a first `pydelity` command

`Status`: `PENDING` `Depends On`: `NONE` `Acceptance`: `AC-010, AC-018`

**Goal**

Make pydelity a real package that later steps build on: runtime dependencies,
the errors component, an import-safe package root, the general utilities, and a
first `pydelity` command that each later step extends.

**Affected Area**

`pyproject.toml` and `uv.lock` (`uv add` pydantic, pydantic-settings[yaml],
pydantic-ai-slim[anthropic,openai], loguru, typer, pymupdf; twine exact in the
dev group), `.template.env` (only `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`),
`src/pydelity/__init__.py`, `[project.scripts]` in `pyproject.toml`; candidates
for the errors, the utilities (atomic files, fingerprints, PDF opening), the
Typer CLI, `python -m pydelity` and a first `run()` the CLI calls.

**Expected Outcome**

`import pydelity` exposes `__version__`, disables loguru for `pydelity` and
reads no file, network or environment. `PydelityError` with `ConfigError`,
`PdfError`, `MissingApiKeyError`, `BudgetExceededError`, `ProviderError` and
`SurveyError`, plus `PydelityWarning`. Utilities: atomic UTF-8 write (temp file
in the same folder, flush, `fsync`, `os.replace`), validated load into a
Pydantic model that reports damage instead of raising, stale `*.tmp-*` cleanup,
canonical-JSON `sha256:` fingerprints, and opening a PDF (full SHA-256 ported
from KGForEdGlobal `utils/pdf.py`, page count, bytes; `PdfError` for
password-protected, empty or unopenable files). A first `run()` opens the PDF
and logs each stage through loguru; the CLI enables logging at INFO and calls
it.

From the command line: `pydelity <pdf>` opens the PDF, logs its name, page
count, size and SHA-256, then `Run finished`; a missing, password-protected or
broken file logs the error and exits non-zero; `pydelity --version` prints the
version; `python -m pydelity <pdf>` does the same.

**Self-Check**

`just lint`; `just test` (existing smoke tests); a scratchpad script exercising
atomic write and load and fingerprints; `pydelity` on a PDF and on a broken
file; `import pydelity` with an empty environment prints nothing.

### DEV-002 — Real public-domain PDF set

`Status`: `PENDING` `Depends On`: `DEV-001` `Acceptance`:
`AC-005, AC-023, AC-035`

**Goal**

Have real public-domain documents for the probe and for real survey runs as the
code is built, plus one small file the CI wheel smoke test can use.

**Affected Area**

`data/pdfs/` (git-ignored; the user downloads the files); candidate
`tests/fixtures/pdfs/` for the one committed smoke-test PDF; the source list in
Plan Notes.

**Expected Outcome**

Developer proposes public-domain PDFs, each with source URL, why it is public
domain, size, page count and what it covers; the user approves and downloads
them into `data/pdfs/`. Together they cover two-column right-to-left text
(Arabic, Hebrew, Persian or Urdu); Chinese; Japanese with vertical
(top-to-bottom) writing; a fillable form with checkboxes (such as a US federal
tax form); rotated pages, including sideways text on pages whose rotation
attribute is 0 if one can be found; scanned pages with no text layer; PDFs with
and without bookmarks and structure tags; and a slide deck or image-heavy PDF.
CAPS, already on disk in KGForEdGlobal's `data/` (which stays unchanged), is
used locally as it is. Where no public-domain document covers a case, Developer
says so and offers an openly licensed one for the user to accept or reject. Each
file is a size the providers are likely to accept. One small file (under the 500
KB hook limit) is copied, with the user's OK, to `tests/fixtures/pdfs/` and
committed for the CI wheel smoke test. Each file's source, licence basis, size,
page count and SHA-256 are recorded in Plan Notes.

From the command line: `pydelity data/pdfs/<file>` opens each downloaded PDF and
logs its page count and size.

**Self-Check**

Open each file with PyMuPDF (page count, text-layer presence, bookmarks,
structure tags, form fields, rotation attributes, size), confirm it covers what
it was chosen for, and record its SHA-256.

### DEV-003 — Provider profiles

`Status`: `PENDING` `Depends On`: `DEV-001` `Acceptance`: `AC-011, AC-037`

**Goal**

Record the few provider-level facts pydelity needs, and nothing per model.

**Affected Area**

Candidates for the provider profiles in the models area, and the `--model`
option of the CLI.

**Expected Outcome**

Model settings parse as `<provider>:<model-id>` with provider `anthropic` or
`openai` only; any model ID is sent as given. One profile per provider: PDF
transports (upload, then in-request fallback), OpenAI upload purpose
`user_data`, the allowed upload expiry range with its maximum as the default
(OpenAI's range checked against its docs), a PDF tokens-per-page figure for the
cost estimate (a named constant derived from the provider's PDF docs), and the
`effort` mapping. No page, size or context-window figure and no list of models
anywhere. The current OpenAI model recommended for document input is picked for
the docs, and a `genai-prices` minimum version that prices
`anthropic:claude-opus-5-5` is set (if no release prices it, the default model
goes back to Architect).

From the command line: `pydelity <pdf> --model <provider:model-id>` logs the
provider and model it will use; a provider other than `anthropic` or `openai`
stops with an error.

**Self-Check**

Scratchpad script printing both profiles and parsing valid and invalid model
settings; a search of `src/` for per-model figures; `just lint`.

**Implementation Notes**

Reads `platform.claude.com`, `developers.openai.com` and the `genai-prices`
release data.

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
`overwrite`, `advanced`) and `AdvancedConfig` (`survey`, `uploads`, and `models`
holding prices only) with `extra="forbid"` and the design's defaults and bounds;
BCP-47 syntax validation; `.json`, `.yaml` and `.yml` loading with relative
paths resolved against the config file's folder; precedence keywords or CLI over
file over defaults, with the CLI `PDF` winning; `expiry_hours` checked against
the selected provider's range; one `ConfigError` listing every invalid setting
by dotted path. `ProviderEnv` (pydantic-settings, environment only, no `.env`,
`SecretStr`) built per run, and `MissingApiKeyError` for the selected provider's
empty key.

From the command line: `--config <file>`, `--instructions`, `--language`,
`--output-dir`, `--max-cost` and `--overwrite` work; the run logs `Settings OK`
(the resolved settings with `--verbose`) or stops with one error listing every
bad setting.

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
document-type terms. A bookmarks, form or structure read that raises sets that
fact to `null` (never an empty value) and adds a `probe_errors[]` item (`fact`,
`message` without file contents); the run continues. A PDF that simply has none
records `[]`, or a `structure` with `tagged: false`.

From the command line: the run logs `Probe finished` with a one-line summary
(pages without text or with garbled text, writing direction, rotated pages,
repeated lines, bookmarks, form fields, structure-tag quality, unreadable
facts); `--verbose` logs the facts page by page.

**Self-Check**

Run the probe on every PDF in the set and check its facts against the documents
(pages, bookmarks, form fields, tags, rotation, printed numbers); `just lint`.

### DEV-007 — Cost ledger, pricing, estimate and `max_cost` guard

`Status`: `PENDING` `Depends On`: `DEV-003, DEV-004` `Acceptance`:
`AC-014, AC-015, AC-038, AC-039`

**Goal**

Price and record every model request, and let the user decide when a run would
go over `max_cost`.

**Affected Area**

Candidates in the costs area: schemas, ledger, pricing, estimate and the
`max_cost` guard.

**Expected Outcome**

Ledger-entry and `CostEstimate` schemas; `cost.jsonl` appends with flush and
`fsync` under an in-process lock, and a reader that skips a damaged trailing
line with a warning; pricing through PydanticAI's `ModelResponse.cost()` with
`advanced.models` price overrides and `price_source`, unpriced responses
recorded as null; the estimate formulas with named constants and the provider's
tokens-per-page figure, including `over_max_cost`; and the `max_cost` guard
(design decision 11): a plan-time check against the estimate's maximum and a
per-request check against that request's upper bound, both counting the whole
folder's recorded spend, with an unpriced model counting as over. A tripped
check records one `max_cost_exceeded` warning and asks the run's decision once;
yes lets the rest of the run go over with no further question, and no raises
`BudgetExceededError` before anything is sent, leaving the run resumable. Money
is `Decimal`; genai-prices runtime updates stay off.

From the command line: before anything that costs money, the run shows the cost
estimate, the spend already recorded in the output folder and `max_cost`, and
asks whether to continue; over `max_cost`, it logs the `max_cost_exceeded`
warning first and the same question decides both; `--yes` skips the question and
a non-interactive run without `--yes` stops.

**Self-Check**

Scratchpad script writing and reading a ledger (including a damaged last line),
pricing responses from small real provider calls against the provider's reported
usage, estimate figures, and the guard's warning and both answers with spend
already in the folder; `just lint`.

### DEV-008 — Model factory and LedgerModel

`Status`: `PENDING` `Depends On`: `DEV-003, DEV-004, DEV-007` `Acceptance`:
`AC-011, AC-014, AC-037, AC-038, AC-039`

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
`tool_choice`, chosen from the model's PydanticAI profile), wrapped in
`LedgerModel`, a PydanticAI `WrapperModel` that runs the per-request `max_cost`
check before each request and appends a ledger line after each response. A model
request that fails after the SDK's retries raises `ProviderError` with the
provider's own message unchanged and the original exception as its cause. Ported
from KGForEdGlobal `model_registry.py` without its hand-kept model set.

From the command line: the run checks the selected provider's API key and logs
`Model ready` with the model, effort and output mode, or stops with the
missing-key error. No model call happens yet.

**Self-Check**

Small real agent runs with each provider, checking the provider settings sent,
ledger lines and prices against the provider's reported usage, the per-request
`max_cost` question (a `max_cost` below one request), and `ProviderError` from a
real rejection (a model ID the provider does not have); `just lint`.

### DEV-009 — PDF uploads, reuse and in-request fallback

`Status`: `PENDING` `Depends On`: `DEV-008` `Acceptance`:
`AC-011, AC-018, AC-021, AC-037`

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
upload path fails (after the SDK's own retries), the step switches to
`BinaryContent` for the rest of the step run, records an `upload_fallback`
warning and `pdf_transport: request`, and writes no upload record. Two upload
errors stop the run with `ProviderError` instead: an authentication failure and
a rejection as too large (413). Nothing checks the PDF's size first; a provider
rejection of the in-request call raises `ProviderError` that also gives the
earlier upload error.

From the command line: after confirmation, the run uploads the PDF and logs the
provider's file id and expiry, or `Reusing upload` on a rerun; `uploads.json`
appears in the output folder. No model call happens yet.

**Self-Check**

Real runs with each provider covering upload, reuse from `uploads.json`, and
re-upload after a recorded file id the provider does not have; an invalid key
for the authentication stop; a real rejection where a provider refuses a PDF
from the set, if one does; the upload failure and fallback by fault injection in
the scratchpad script (a failing upload call), since a provider cannot be made
to fail on demand; `just lint`.

### DEV-010 — Survey proposal, profile, prompt and checks

`Status`: `PENDING` `Depends On`: `DEV-005` `Acceptance`:
`AC-002, AC-003, AC-004, AC-006`

**Goal**

Define what the model proposes and how Python checks it.

**Affected Area**

Candidates in the survey step folder, following KGForEdGlobal's
`page_ir_extraction/` split: a prompts module (prompt builders), a validators
module (checks C1–C7: what Pydantic cannot check, such as comparing the answer
with the measured facts) and the schemas module (shapes and bounds Pydantic
enforces).

**Expected Outcome**

The model-facing proposal schema (strings, integers, booleans, enums, arrays and
objects only; region boxes as page fractions; artifact `position` as `top` |
`bottom` | `left` | `right` | `middle`), the stored `profile` (including
`writing_direction.ranges[]` with inclusive page indexes and `direction`) and
the `PdfSurvey` model for `pdf_survey.json` 1.0; a document-type-neutral prompt
with `PROMPT_VERSION` carrying the facts summary (saying which facts were
unavailable), user instructions and languages; checks C1–C7, each returning
failure items (`page_index` or null, `message` naming the check with the
proposed and measured values, `details`), one item per affected page, and the
`checks[]` and `issues[]` records built from them in C1–C7 order. Unlike
KGForEdGlobal's validators, which raise on the first problem, each check returns
all its failures, so one retry message names every problem and the last attempt
can record them all.

From the command line: `--verbose` logs the prompt and facts summary the survey
will send. No model call happens yet.

**Self-Check**

Scratchpad script running the checks on hand-made passing and failing proposals
against facts from the PDF set; a search of code and prompt for document-type
terms and word lists; `just lint`.

### DEV-011 — Survey step

`Status`: `PENDING` `Depends On`: `DEV-009, DEV-010` `Acceptance`:
`AC-002, AC-003, AC-004, AC-011, AC-017, AC-018`

**Goal**

Run the survey end to end and store a checked profile.

**Affected Area**

Candidates following KGForEdGlobal: an agents module (builds the agent and its
output validator, which turns check failures into `ModelRetry`), an llm module
(builds the message with the PDF and facts summary and runs the agent), and the
step's entry function (fingerprint, reuse, writing `pdf_survey.json`).

**Expected Outcome**

The fingerprint from the design's inputs; reuse of a valid, matching
`pdf_survey.json` unless `overwrite`, and regeneration of a damaged one; the
agent built through `build_model` with the uploaded file, a cache breakpoint
after the PDF and facts summary, and an output validator that raises
`ModelRetry` while retries remain and, on the last attempt, accepts and records
still-failing checks as review issues. It uses PydanticAI's retry count and
last-attempt flag in place of KGForEdGlobal's hand-kept attempt counter, and
drops its raw-attempt files and `ExtractionUsageTracker` (the ledger replaces
it). Python adds `other`, merges languages, stores `user_instructions`, converts
region boxes to points and writes `pdf_survey.json` atomically. A refusal or an
answer that never parses raises `SurveyError`.

From the command line: the run makes the real survey call and logs
`Survey finished` with the labels, languages, rotation, review-issue count and
cost, writing `pdf_survey.json` and `cost.jsonl`; a rerun with the same inputs
logs `Survey reused` without a call; `--overwrite` reruns it.

**Self-Check**

Real survey runs with both providers on PDFs from the set: reuse, a
changed-input rerun and `overwrite`; retry-then-pass and still failing after
retries by fault injection in the scratchpad script (a check forced to fail);
`pdf_survey.json` reviewed against each PDF; `just lint`.

### DEV-012 — Run orchestration

`Status`: `PENDING` `Depends On`: `DEV-004, DEV-007, DEV-011` `Acceptance`:
`AC-014, AC-018, AC-019, AC-037, AC-038, AC-039`

**Goal**

Wrap steps in a run that owns the output folder, `run.json`, the review list and
interrupts.

**Affected Area**

Candidates `src/pydelity/pipeline/{schemas,runner}.py`.

**Expected Outcome**

Settings resolved and validated, the PDF opened (no size or page check), the
folder prepared (stale temp files removed; a warning when `run.json` names
another PDF); `run.json` written at start and end with steps, cost (`run_usd`,
`by_step`, `output_folder_usd`, `unpriced_requests`), the review list (reused
outputs' issues included), warnings and error; `failed`, `stopped` and
`interrupted` recorded before re-raising, with `KeyboardInterrupt` caught and
re-raised. Warnings are items (`code`, `step`, `message`, `details`) with this
cycle's codes (`unpriced_model`, `max_cost_exceeded`, `other_pdf_in_folder`,
`damaged_output`, `upload_fallback`, `probe_unavailable`), and each also goes to
`PydelityWarning` and the log. A `ProviderError` or a `max_cost` no ends the run
`failed` or `stopped`, with every written file valid. A planning hook gives the
CLI the estimate before any spend.

From the command line: every run writes `run.json` and ends with a summary line
(status, cost of this run and of the folder, review-issue count); Ctrl+C logs
`interrupted`; a budget stop says how to resume.

**Self-Check**

Real runs covering completion, a budget stop then a resume with a higher
`max_cost`, an injected error and a Ctrl+C during the model call; `just lint`.

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

From the command line: the run logs `Report written` with the path of
`report.html`, which opens in a browser.

**Self-Check**

Reports for completed and failed runs on PDFs from the set, opened from disk;
escaping checked with a hostile label; `just lint`.

**Implementation Notes**

Loads the Developer HTML and CSS styles.

### DEV-014 — Python API

`Status`: `PENDING` `Depends On`: `DEV-012, DEV-013` `Acceptance`:
`AC-010, AC-015, AC-039`

**Goal**

Expose `run`, `survey` and `estimate` and the public types from the package
root.

**Affected Area**

Candidate `src/pydelity/api.py`; `src/pydelity/__init__.py`.

**Expected Outcome**

Synchronous `run`, `survey` and `estimate` taking `pdf`, `config` (a path, a
`Config` or a mapping) and setting keywords; `run` and `survey` also take
`allow_over_max_cost` (default `False`), which answers the `max_cost` decision.
They never prompt or read stdin, and they work inside a running event loop (on a
worker thread). The root re-exports them with `Config`, the result models,
`CostEstimate`, the errors and `PydelityWarning`; import stays free of side
effects.

From Python: `pydelity.run(...)`, `pydelity.survey(...)` and
`pydelity.estimate(...)` work, in a script or in Jupyter; the command line is
unchanged.

**Self-Check**

Real calls of all three, including from inside `asyncio.run`; import with an
empty environment prints nothing; `just lint`.

### DEV-015 — CLI

`Status`: `PENDING` `Depends On`: `DEV-014` `Acceptance`:
`AC-007, AC-008, AC-009, AC-015, AC-019, AC-037, AC-038`

**Goal**

Run the survey from the command line with nothing but a PDF path.

**Affected Area**

The CLI module from DEV-001.

**Expected Outcome**

Finishes the command built up since DEV-001 to the design's contract: every
option in the design's order of work, the mid-run `max_cost` question, a
provider's error printed unchanged after the provider and model (with the PDF's
name, pages and size when the call carried it), exit codes (0, 1, 2, 3, 130),
logging levels, warnings printed as they occur, and the end-of-run summary with
review issues grouped by check, a count per check before the list; the
`pydelity` console script and `python -m pydelity`.

**Self-Check**

The installed `pydelity` with real providers: `--yes`, piped stdin without
`--yes`, a declined prompt, invalid settings and `--version`; `just lint`.

### DEV-006 — Mock provider server

`Status`: `PENDING` `Depends On`: `DEV-015` `Acceptance`: `AC-021, AC-023`

**Goal**

Let the CI wheel smoke test (AC-023) run both providers' real PydanticAI
adapters with no provider keys and no spend. Development self-checks do not use
it; they call the real providers. Tester may reuse and extend it for the
automated tests (AC-021).

**Affected Area**

Candidate `tests/fixtures/mock_providers.py` (standard library only).

**Expected Outcome**

A loopback HTTP server, reached through `ANTHROPIC_BASE_URL` and
`OPENAI_BASE_URL`, that answers Anthropic Messages and Files API calls and
OpenAI Responses and Files API calls with canned bodies: a structured survey
answer the caller supplies, usage figures, upload success, "file not found",
upload failures (server error, authentication failure, 413 too large), a request
that rejects the PDF, and a request log the caller can inspect. The canned
bodies follow the response shapes recorded from the real development runs (usage
figures and ids only, never keys). No production code path exists only for it.

From the command line: with `ANTHROPIC_BASE_URL` or `OPENAI_BASE_URL` pointed at
the stand-in, `pydelity <pdf> --yes` completes with no keys and no spend.

**Self-Check**

Run the installed `pydelity` (`--yes`) and the Python API against it for both
providers on the committed smoke-test PDF; `just lint`.

### DEV-016 — Wheel build and smoke script

`Status`: `PENDING` `Depends On`: `DEV-006, DEV-015` `Acceptance`:
`AC-023, AC-024`

**Goal**

Show that a built wheel installs and runs on any supported platform.

**Affected Area**

`justfile` (`build`); candidate `scripts/smoke_installed_wheel.py`.

**Expected Outcome**

`just build` cleans `dist/`, runs `uv build` and `twine check --strict`. The
standard-library smoke script makes a fresh venv with pip, installs the wheel,
starts the mock server, and runs the console script (`--yes`) and the Python API
with each provider on the committed smoke-test PDF, asserting exit codes and
valid outputs; it handles Windows paths and scripts.

From the command line: `just build`, then the smoke script, which installs the
built package into a fresh environment and runs `pydelity`.

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
  layout below is a sketch only: plan approval does not approve it, and the user
  approves each file and folder name and location at the step that creates it.
  The orchestration and step folders avoid the names `run` and `survey` at the
  package root, where a subpackage would shadow the public `pydelity.run` and
  `pydelity.survey` functions.

  ```text
  src/pydelity/
    __init__.py         public API re-exports, __version__, logger.disable
    __main__.py         python -m pydelity
    api.py              run, survey, estimate
    cli.py              Typer CLI
    errors.py           PydelityError and subclasses, PydelityWarning
    config/             schemas.py (Config, AdvancedConfig, ProviderEnv), loading.py
    costs/              schemas.py, ledger.py, pricing.py, budget.py (estimate, guard)
    models/             providers.py, factory.py, ledger_model.py, uploads.py
    pipeline/           schemas.py (run.json, review issues), runner.py
    report/             html.py, images.py
    steps/survey/       schemas.py, probe.py, prompts.py, validators.py, agents.py,
                        llm.py, step.py
    utils/              files.py, fingerprints.py, pdf.py
  scripts/              smoke_installed_wheel.py,
                        generate_reference_docs.py
  tests/fixtures/       mock_providers.py, pdfs/ (the one smoke-test PDF)
  data/pdfs/            real public-domain PDFs the user downloads (git-ignored)
  docs/                 Astro Starlight site
  .github/workflows/    release.yml, docs.yml (new); ci.yml (changed)
  ```

- Development self-checks call the real Anthropic and OpenAI APIs with the
  user's keys (user decision, 2026-11-17), on small PDFs, and each step's
  self-check evidence records the spend. Developer loads the keys from the
  user's environment without printing them. Paths a provider cannot produce on
  demand (upload failure, a check that fails then passes) use fault injection in
  scratchpad scripts, never in pydelity code.
- The mock provider server (DEV-006) is built late, only because the CI wheel
  smoke test must run without keys or spend (AC-023 and the scope's mocked-test
  constraint). Formal tests, the autouse test guard fixture and verification
  evidence are Tester's. The smoke-test PDF, the mock server and the smoke
  script are reusable project assets the design's Build Plan assigns to
  Developer; Tester may extend them.
- `AC-031`, `AC-033`, `AC-034` and `AC-035` have no Developer step: they rest on
  Documenter's pages and README and on the user's review of real runs.
- User style `tony` names pylint and mypy; this repo enforces the same intent
  with Ruff (`PL`, `C90`) and ty, which Developer uses.
- Test PDFs are real public-domain documents, not generated ones (user decision,
  2026-11-17, in line with the scope's assumption that test PDFs are public
  documents the user approves). This replaces the design Build Plan's synthetic
  fixtures; no technical criterion depends on how the PDFs were made. Tester
  chooses which PDFs its committed tests use.
- DEV-022 was withdrawn before approval (folded into DEV-002); its number is not
  reused.
- Every step from DEV-001 to DEV-016 leaves `pydelity <pdf>` (or, for DEV-014,
  the Python API) able to try what the step built: each stage logs through
  loguru that it finished, or why it failed, and the run ends after the last
  stage built so far (user decision, 2026-11-17). DEV-017 to DEV-021 change CI,
  the release and the docs, and are tried with the commands in their
  self-checks.
- The survey's model code follows KGForEdGlobal's `page_ir_extraction/` split
  (`agents.py`, `llm.py`, `prompts.py`, `validators.py`, `schemas.py`), with
  validators holding the checks Pydantic cannot express (user direction,
  2026-11-17). File names are still approved at each step.
- Project references loaded: `NONE` (`.standards/project-references/` does not
  exist).

### Suspended Assignment 1

`Recovery Frame`: `1` `Recovery Reason`:
`Design leaves pdf_survey.json fields open: how an unreadable probe fact (bookmarks, forms, structure) is recorded, writing_direction.ranges[] item fields, the artifacts[].position value set, and checks[].failures item shape.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`scope and design at commit 5be0f98; this plan draft` `Next Action`:
`Reconcile DEV-005 and DEV-010 with the corrected design, then present the plan for approval.`

Restored on the `RESUME` from `ARCHITECTING` (design commit `c9828bc`) and
reconciled: DEV-005 now sets unreadable facts to `null` with `probe_errors[]`;
DEV-010 takes the artifact `position` values, the `writing_direction.ranges[]`
fields and the failure-item shape for `checks[]` and `issues[]`; DEV-012 takes
the warning items and codes; DEV-015 groups review issues by check in the
summary. No step was added or reordered, and nothing was implemented before the
correction.

### Suspended Assignment 2

`Recovery Frame`: `1` `Recovery Reason`:
`User rework: drop shipped per-model PDF input limits (send the PDF and report the provider's error) and make max_cost warn and let the user continue (the CLI asks; library callers pass a continue flag) instead of stopping.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`scope 9b8b030 and design c9828bc; this unapproved plan draft` `Next Action`:
`Reconcile DEV-003, DEV-007, DEV-009, DEV-012, DEV-014 and DEV-015 with the reworked scope and design, then present the plan for approval.`

Restored on the `RESUME` from `ARCHITECTING` (scope `8fa6449`, design `a80a831`)
and reconciled: DEV-003 is now provider profiles only (`AC-037` replaces the
retired `AC-012` and `AC-013`); DEV-007, DEV-008 and DEV-014 carry the
`max_cost` warning, the CLI question and `allow_over_max_cost` (`AC-038` and
`AC-039` replace the retired `AC-016`); DEV-008, DEV-009, DEV-012 and DEV-015
carry `ProviderError`; DEV-001 drops `InputLimitError`; DEV-004 keeps only
prices under `advanced.models`; DEV-006 adds rejection responses. No step was
added, removed or reordered.

### Suspended Assignment 3

`Recovery Frame`: `1` `Recovery Reason`:
`User rework: save the probe's measured facts and their summary in a new output file right after measuring, before any API key check, cost question or model call, so they survive a declined, failed or keyless run.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`scope 8fa6449 and design a80a831; this unapproved plan draft` `Next Action`:
`Reconcile DEV-005 (and any step the new output touches, such as DEV-012, DEV-013 and DEV-021) with the reworked scope and design, then present the plan for approval.`

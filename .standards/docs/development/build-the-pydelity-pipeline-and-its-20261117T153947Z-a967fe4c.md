<!-- STANDARDS
Artifact: DEVELOPMENT
Cycle: build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c
-->

# Development Plan

`Cycle`: `build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c` `Mode`:
`STEPWISE` `User Style`: `tony` `User Style Locked`: `true` `Status`:
`IN_PROGRESS` `Verification Cadence`: `AFTER_IMPLEMENTATION`
`Current Increment`: `NONE`

## Implementation Contract

- `Scope`:
  `.standards/docs/scope/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c.md`
- `Architecture`:
  `.standards/docs/specs/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c.md`
- `Request`:
  `Build step 1 (survey) of pydelity with the run features it needs (config, CLI and Python API, provider errors, cost ledger and spend controls, resume, review list, HTML report) for Anthropic and OpenAI models; CI on Python 3.13 and 3.14 with wheel installs on Windows, macOS and Linux; the 0.1.0 PyPI release workflow; and the Astro Starlight docs site.`

## Build Steps

### DEV-001 — Package foundation and a first `pydelity` command

`Status`: `DONE` `Depends On`: `NONE` `Acceptance`: `AC-010, AC-018, AC-044`

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
Typer CLI, `python -m pydelity`, the helper that runs a coroutine from sync
code, and a first `arun()` with its sync `run()` that the CLI calls.

**Expected Outcome**

`import pydelity` exposes `__version__`, disables loguru for `pydelity` and
reads no file, network or environment. `PydelityError` with `ConfigError`,
`PdfError`, `MissingApiKeyError`, `BudgetExceededError`, `ProviderError`,
`SurveyError` and `OutputError`, plus `PydelityWarning`. Utilities: atomic UTF-8
write (temp file in the same folder, flush, `fsync`, `os.replace`), validated
load into a Pydantic model that reports damage instead of raising, stale
`*.tmp-*` cleanup, canonical-JSON `sha256:` fingerprints, and opening a PDF
(full SHA-256 ported from KGForEdGlobal `utils/pdf.py`, page count, bytes;
`PdfError` for password-protected, empty or unopenable files), and a helper that
runs a coroutine from sync code (`asyncio.run` without a running loop, otherwise
a worker thread with its own loop, re-issuing its warnings in the caller's
thread). A first `arun()`, with `run()` calling it through that helper, opens
the PDF off the event loop and logs each stage through loguru; the CLI enables
logging at INFO and calls `run()`.

From the command line: `pydelity <pdf>` opens the PDF, logs its name, page
count, size and SHA-256, then `Run finished`; a missing, password-protected or
broken file logs the error and exits non-zero; `pydelity --version` prints the
version; `python -m pydelity <pdf>` does the same.

**Self-Check**

`just lint`; `just test` (existing smoke tests); a scratchpad script exercising
atomic write and load and fingerprints; `pydelity` on a PDF and on a broken
file; `import pydelity` with an empty environment prints nothing.

Evidence, 2026-11-17, repo root, on `0f1c417` plus the uncommitted DEV-001
changes (macOS arm64, Python 3.13.9). First run on PyMuPDF 1.28.2. After the
user switched to PyMuPDF 2.1 the same day, every check below was rerun on 2.1
with the same results.

- `just lint`: Prettier, the STANDARDS check, markdownlint, Ruff check and
  format, ty, interrogate (100%) and zizmor all passed. It ran outside the
  sandbox because prek writes to `~/.cache/prek`.
- `just test`: 2 passed. The 5 warnings are PyMuPDF's SWIG `DeprecationWarning`s
  (`builtin type SwigPyObject has no __module__ attribute`) at import, which
  pytest shows.
- Scratchpad `dev001_utils_check.py`: 30 of 30 checks passed. Atomic write
  produces UTF-8 with LF only and permissions from the umask (0644), leaves no
  temp file, and keeps the old content and removes the temp file when `fsync`
  fails. Load returns the model; neither for an absent file; and damage for
  invalid JSON, a wrong schema or non-UTF-8 bytes, with none of the file's text
  in the message. Cleanup removes only `<name>.tmp-<16 hex>` files in that
  folder (not other `.tmp-` names or subfolders). Fingerprints ignore key order
  and reject NaN and non-JSON values. `run_coroutine` runs in the calling thread
  without a loop and on the `pydelity` worker thread with a loop. On the worker
  thread, results, errors and `PydelityWarning`s arrive in the caller's thread
  (warnings attributed to the caller's file). A real SIGINT cancels the
  coroutine (it sees `CancelledError`) and raises `KeyboardInterrupt` within 0.6
  s in all three cases: no loop, a sync call inside `asyncio.run`, and a plain
  loop as in Jupyter. A cancellation requested before the call does not cancel
  the work.
- `pydelity` on KGForEdGlobal's
  `data/funda_wande/caps_english_hl_grade_3_fs.pdf` (read only) logged
  `142 pages, 2,007,018 bytes`, SHA-256 `c939a3a9…b878d24d` (equal to
  `shasum -a 256`), then `Run finished`, and exited 0. `python -m pydelity` gave
  the same result with exit 0. `--version` printed `pydelity 0.0.1` (exit 0).
  Scratchpad copies exited 2 with the file and reason logged: a missing file
  (`no such file`), a folder (`not a file`), an empty file
  (`the file is empty`), a truncated copy (`the PDF has no pages`), a text file
  named `.pdf` (`cannot be opened as a PDF`) and an AES-256 copy with a user
  password (`password-protected`). A missing argument exited 2 with Typer's
  error.
- `env -i` `.venv/bin/python -c "import pydelity"` printed only the script's own
  output (nothing on stderr). With `-W default`, PyMuPDF's SWIG
  `DeprecationWarning`s appear. They are PyMuPDF's, not pydelity output, and are
  hidden by Python's default filters. On 2.1 the import (about 0.4 s cold) does
  not load onnxruntime or numpy, and runs in the sandbox showed no network
  access.
- `scripts/check_env_template.py` reports the six `LLM_*` names still in the
  user's local `.env`. The user is removing them (2026-11-17).

**Implementation Notes**

- Files approved by the user (2026-11-17):
  `src/pydelity/{__main__,api,cli,errors}.py` and
  `src/pydelity/utils/{__init__,coroutines,files,fingerprints,pdf}.py`.
- Versions: each runtime dependency's minimum is its latest stable release on
  2026-11-17 (user request): loguru 0.8.0, pydantic 2.14.3, pydantic-ai-slim
  2.69.0, pydantic-settings 2.16.3, typer 0.29.1. Dev group: `twine==7.0.0`, and
  `ty` bumped to 0.0.105. PyMuPDF is `>=2.1` by user decision (2026-11-17). The
  user first chose `>=1.28.2,<2`, then switched once it came to light that only
  2.x fixes page-label bugs (#5214 garbled UTF-16 or `/` prefixes, #5140
  `IndexError` before the first label), a 1.28 hang in `get_text` and
  `get_pixmap` (#5082), the `get_pixmap` hang on heavily tagged pages (#5125)
  and form-field problems (#5101, radio groups), and that 1.x gets no further
  releases. Costs accepted: 2.x requires onnxruntime, numpy, networkx and more
  (wheels of about 89 MB plus about 28 MB), and has no wheels for Intel Macs,
  Windows ARM, 32-bit Windows or musl Linux. Documenter should say which
  platforms are supported. CI's `ubuntu-latest`, `windows-latest` and
  `macos-latest` (arm64) all have wheels.
- pydelity warnings go through `pydelity.utils.coroutines.warn`, which records
  them on a worker thread (a `ContextVar` set there) and issues them as
  `PydelityWarning` otherwise. This avoids `warnings.catch_warnings`, which is
  process-global and unsafe with concurrent sync calls from several threads.
- Within a running loop, `run_coroutine` also cancels the coroutine when the
  calling task gets a new cancellation request. That is how the first Ctrl+C
  arrives under `asyncio.run`, while the waiting thread blocks the loop.
- Conventions from the user's review (2026-11-17), for every later step: modules
  put private globals, classes and functions before public ones (alphabetical
  within each group); shipped code, config and docstrings use American English
  and never mention the development process (decision dates, DEV or AC IDs,
  KGForEdGlobal). DEV-001 was reordered and reworded to match, and `just lint`,
  `just test`, the scratchpad check (30 of 30) and the CLI runs passed again
  afterwards.
- `arun`/`run` take only `pdf` and return `None` for now. DEV-014 gives them the
  designed signature and `RunResult`. The CLI requires `PDF` until DEV-004 and
  DEV-015 add `--config`.

### DEV-002 — Real public-domain PDF set

`Status`: `DONE` `Depends On`: `DEV-001` `Acceptance`: `AC-005, AC-023, AC-035`

**Goal**

Have real public-domain documents for the probe and for real survey runs as the
code is built, plus one small file the CI wheel smoke test can use.

**Affected Area**

`tests/fixtures/pdfs/` (committed; every test PDF, each under the 500 KB hook
limit) and `tests/fixtures/pdfs/SOURCES.md` (provenance), as the user decided on
2026-11-17 in place of the git-ignored `data/pdfs/`; Plan Notes point to
`SOURCES.md`.

**Expected Outcome**

Developer proposes public-domain PDFs, each with source URL, why it is public
domain, size, page count and what it covers; the user approves them and they are
downloaded into `tests/fixtures/pdfs/` and committed. Together they cover
two-column right-to-left text (Arabic, Hebrew, Persian or Urdu); Chinese;
Japanese with vertical (top-to-bottom) writing; a fillable form with checkboxes
(such as a US federal tax form); rotated pages, including sideways text on pages
whose rotation attribute is 0 if one can be found; scanned pages with no text
layer; PDFs with and without bookmarks and structure tags; and a slide deck or
image-heavy PDF. CAPS, already on disk in KGForEdGlobal's `data/` (which stays
unchanged), is used locally as it is. Where no public-domain document covers a
case, Developer says so and offers an openly licensed one for the user to accept
or reject. Each file is under 500 KB, so every one can be committed; a case that
only a larger file covers is reported to the user instead. One of them serves
the CI wheel smoke test. `tests/fixtures/pdfs/SOURCES.md` records each file's
source URL, licence basis (with any attribution an open licence requires), size,
page count, SHA-256 and the cases it covers.

From the command line: `pydelity tests/fixtures/pdfs/<file>` opens each PDF and
logs its page count and size.

**Self-Check**

Open each file with PyMuPDF (page count, text-layer presence, bookmarks,
structure tags, form fields, rotation attributes, size), confirm it covers what
it was chosen for, and record its SHA-256.

Evidence, 2026-11-17, repo root, uncommitted on top of `0f1c417` (PyMuPDF 2.1):

- Candidates: 21 PDFs downloaded to the scratchpad with the user's permission
  and inspected with a scratchpad script (`tools/inspect_pdfs.py`: page sizes,
  rotation attributes, character counts, line directions, `wmode`, Unicode bidi
  share, block columns, bookmarks, page labels, widgets, XFA, `StructTreeRoot`
  and `MarkInfo`). Rejected: `f1040--1913.pdf` (retyped, not a scan), the other
  older Form 1040 and 1040A scans (only one scan needed), Persian and Urdu
  Publication 1 (same layout as Arabic), the Knesset law (one body column),
  Forms W-4 and 8962 (W-9 chosen). Two courts.go.jp judgments failed TLS
  certificate verification and were skipped. CDC, BLS, SSA, GAO and CRS refuse
  scripted downloads.
- Committed set, approved by the user: 9 files in `tests/fixtures/pdfs/` (1.4 MB
  in total), each under 500 KB: `bls_navigating_slides.pdf` (16 slides, images
  on every slide, tagged), `caps_english_hl_pages_28_35.pdf` (CAPS pages 28–35
  copied with PyMuPDF `insert_pdf`, page labels 23–30 kept; rotation attribute 0
  with 88–98% of each page's text in direction (0, −1)),
  `irs_form_1040_1950.pdf` (page labels; 400 sideways heading characters on page
  4), `irs_form_1040a_1965_scan.pdf` (images only, 0 characters),
  `irs_form_w9.pdf` (8 checkboxes, 15 text fields, XFA, tagged, 51 sideways
  characters on page 1), `irs_pub1_arabic.pdf` (89–92% right-to-left, two and
  three columns, tagged), `irs_pub1_chinese_simplified.pdf` (two and three
  columns, tagged), `irs_w9_instructions.pdf` (22 bookmarks, tagged) and
  `japan_official_gazette_2019_extra_9.pdf` (213 of 251 characters with `wmode`
  1, page labels, a signature field, untagged).
- Coverage of the cases: two-column right-to-left (Arabic); Chinese; vertical
  Japanese; a fillable form with checkboxes; sideways text on pages whose
  rotation attribute is 0 (CAPS, dominant; W-9 and 1950 Form 1040, minor); pages
  with no text layer (1965 Form 1040A); with bookmarks and tags (W-9
  instructions); tagged without bookmarks (Publication 1, W-9, slides); neither
  (gazette, CAPS, both old forms); a slide deck (BLS). Not covered: a page whose
  rotation attribute is 90, 180 or 270. No candidate that could be downloaded
  had one.
- `tests/fixtures/pdfs/SOURCES.md` gives each file's source, license basis (17
  U.S.C. § 105; Japan's Copyright Act Article 13; South Africa's Copyright Act
  section 12(8)(a) for CAPS, which the user confirmed), size, page count,
  SHA-256 and contents. A scratchpad check recomputed every size and SHA-256 and
  matched all 9 entries, with no PDF missing an entry.
- `pydelity tests/fixtures/pdfs/<file>` opened all 9 and logged the expected
  page count, size and SHA-256 (exit 0).
- `uv run --locked prek run --files tests/fixtures/pdfs/* src/pydelity/api.py`:
  every hook passed, including `check-added-large-files`, `detect-secrets` and
  `env-template-sync` (the user's `.env` now matches `.template.env`).
  `just lint-markdown` and `just lint-python` passed.

**Implementation Notes**

- The CAPS excerpt is regenerated only by copying pages 28–35 of the
  KGForEdGlobal copy (`data/funda_wande/caps_english_hl_grade_3_fs.pdf`, SHA-256
  `c939a3a9…b878d24d`, left unchanged). PyMuPDF writes a new file ID on each
  save, so a regenerated excerpt has a different SHA-256.
- While running this step, DEV-001's log line was corrected to say `1 page`
  rather than `1 pages`.

### DEV-003 — Provider profiles

`Status`: `DONE` `Depends On`: `DEV-001` `Acceptance`: `AC-011, AC-037`

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

Evidence, 2026-11-17, repo root, uncommitted on top of `ed70f71`:

- Scratchpad `tools/dev003_check.py`: 13 of 13 checks passed. It printed both
  profiles: Anthropic (upload then request, no purpose, expiry 1–2,160 hours,
  7,784 tokens per page, effort `high` →
  `anthropic_effort: high, anthropic_thinking: adaptive`) and OpenAI (upload
  then request, purpose `user_data`, expiry 1–720 hours, 6,000 tokens per page,
  `openai_reasoning_effort: high`). The default model parses to
  `anthropic:claude-opus-5-5`, and model IDs are kept as given (including ones
  with `:`). Missing `:`, an empty provider or model ID, `google:` and
  `Anthropic:` each raise `ConfigError`. `import pydelity` loads no
  `pydantic_ai`; the settings types are imported for type checking only, because
  `pydantic_ai.settings` alone takes about 1 s to import.
- `pydelity tests/fixtures/pdfs/irs_pub1_arabic.pdf` logged
  `Model: claude-opus-5-5 from provider anthropic`, and with
  `--model openai:gpt-6.2-astra` logged `gpt-6.2-astra from provider openai`
  (both exit 0). `--model google:gemini-3` logged
  `model: provider 'google' is not supported; use 'anthropic' or 'openai'` and
  exited 2, and `--model claude` exited 2.
- A search of `src/` for context windows, page or size limits and model names
  found only the default model and a doctest.
- `just lint-python` (Ruff, ty, interrogate 100%) and `just test` (2 passed)
  passed.

**Implementation Notes**

- Files approved by the user (2026-11-17): `src/pydelity/providers/__init__.py`
  and `src/pydelity/providers/profiles.py`. The user chose `providers/` over
  `models/` for this component; DEV-008 and DEV-009 add the model factory, the
  ledger wrapper and uploads there.
- Sources read 2026-11-17: Anthropic's installed SDK (`anthropic` 2.10.0,
  `files.upload(expires_in_seconds=...)`: 3,600–7,776,000 s); OpenAI's installed
  SDK (`openai` 3.53.0, `expires_after.seconds`: 3,600–2,592,000 s; without it,
  non-batch files persist until deleted); Anthropic's PDF support page
  (1,500–3,000 text tokens per page, plus each page billed as an image) and
  vision page (at most 4,784 tokens per image on Claude 4.7 and later); OpenAI's
  PDF files guide (text plus page images; no per-page figure; `user_data` for
  model inputs) and images guide (patch-based models: high detail up to 2,500
  patches × 1.2 tokens).
- Tokens per page: Anthropic 3,000 text + 4,784 image = 7,784; OpenAI 3,000 text
  (OpenAI gives none, so Anthropic's upper bound for the same page text) + 3,000
  image = 6,000. Both are upper bounds, so estimates err high. DEV-007 compares
  them with the usage real requests report.
- OpenAI model for the docs: `openai:gpt-6.2-astra`, which OpenAI's models page
  recommends as the default ("If you're not sure where to start"). It takes
  image input (so PDF text plus page images) and reasoning effort low to max.
- `genai-prices>=0.2.4` (latest) is now a direct runtime dependency. 0.2.4
  prices `claude-opus-5-5` ($4 / $20 per million tokens) and `gpt-6.2-astra`
  ($16 / $60), so the default model stays as designed.
- Until DEV-004 adds the full configuration, `arun`/`run` take `model` as a
  keyword argument, checked before the PDF is opened.

### DEV-004 — Configuration

`Status`: `PENDING` `Depends On`: `DEV-003` `Acceptance`:
`AC-004, AC-007, AC-008, AC-009, AC-041`

**Goal**

Resolve and validate every setting before any work, from defaults, an optional
JSON or YAML file, and CLI options or Python keywords.

**Affected Area**

Candidates `src/pydelity/config/{schemas,loading}.py`.

**Expected Outcome**

`Config` (`pdf`, `instructions`, `languages`, `output_dir`, `model`, `max_cost`,
`overwrite`, `advanced`) and `AdvancedConfig` (`provider_retries` 0–10, default
2; `survey` with `check_retries`; `uploads`; and `models` holding prices only)
with `extra="forbid"` and the design's defaults and bounds; BCP-47 syntax
validation; `.json`, `.yaml` and `.yml` loading with relative paths resolved
against the config file's folder; precedence keywords or CLI over file over
defaults, with the CLI `PDF` winning; `expiry_hours` checked against the
selected provider's range; one `ConfigError` listing every invalid setting by
dotted path. `ProviderEnv` (pydantic-settings, environment only, no `.env`,
`SecretStr`) built per run, and `MissingApiKeyError` for the selected provider's
empty key.

From the command line: `--config <file>`, `--instructions`, `--language`,
`--output-dir`, `--max-cost` and `--overwrite` work; the run logs `Settings OK`
(the resolved settings with `--verbose`) or stops with one error listing every
bad setting.

**Self-Check**

Scratchpad script with valid and invalid JSON and YAML files, several errors at
once, precedence cases and a missing key; `just lint`.

### DEV-005 — Survey probe and `pdf_facts.json`

`Status`: `PENDING` `Depends On`: `DEV-001, DEV-002, DEV-004` `Acceptance`:
`AC-001, AC-005, AC-006, AC-017, AC-018, AC-040`

**Goal**

Measure everything the survey can know about a PDF without a model, and save it
with a summary before anything needs a key or costs money.

**Affected Area**

Candidates in the survey step folder for the facts schemas and the probe, plus
the facts summary and `pdf_facts.json` writing.

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
records `[]`, or a `structure` with `tagged: false`. The probe runs off the
event loop (`asyncio.to_thread`). `pdf_facts.json` holds `fingerprint` (PDF
SHA-256, `PROBE_VERSION`, facts `schema_version`), `probe_version`,
`measured_at`, `pdf`, `facts` and `summary[]` (plain-text lines built
deterministically from the facts). It is written atomically into the output
folder right after measuring, before any API key check, estimate or question; a
valid file with a matching fingerprint is reused unless `overwrite`, and a
damaged one is measured again with a `damaged_output` warning. The summary lines
are logged at INFO.

From the command line: the run logs the summary lines (pages without text or
with garbled text, writing direction, rotated pages, page numbering, repeated
lines, bookmarks, form fields, structure-tag quality, unreadable facts) and
writes `pdf_facts.json` to the output folder, with no API key needed; a rerun
logs `Facts reused`; `--verbose` logs the facts page by page.

**Self-Check**

Run the probe on every PDF in the set and check its facts against the documents
(pages, bookmarks, form fields, tags, rotation, printed numbers); a rerun reuses
`pdf_facts.json`, a damaged one is rewritten, and a run with no API key still
writes it; `just lint`.

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
is `Decimal`; genai-prices runtime updates stay off. The run asks its questions
through callables it is given: the CLI passes its prompt (or `--yes`), and the
Python API passes none and never asks.

From the command line: after the facts are saved and before anything that costs
money, the run shows the cost estimate, the spend already recorded in the output
folder and `max_cost`, and asks whether to continue; over `max_cost`, it logs
the `max_cost_exceeded` warning first and the same question decides both;
`--yes` skips the question and a non-interactive run without `--yes` stops.

**Self-Check**

Scratchpad script writing and reading a ledger (including a damaged last line),
pricing responses from small real provider calls against the provider's reported
usage, estimate figures, and the guard's warning and both answers with spend
already in the folder; `just lint`.

### DEV-008 — Model factory and LedgerModel

`Status`: `PENDING` `Depends On`: `DEV-003, DEV-004, DEV-007` `Acceptance`:
`AC-011, AC-014, AC-037, AC-038, AC-039, AC-041`

**Goal**

Build every model through one factory that applies provider settings and records
every request.

**Affected Area**

Candidates `src/pydelity/models/{factory,ledger_model}.py`.

**Expected Outcome**

`build_model` builds the SDK client itself (`AsyncAnthropic` or `AsyncOpenAI`
with `max_retries` from `advanced.provider_retries` and the request timeout) and
passes it to PydanticAI's provider, so one retry count governs model requests
and uploads, with no retry layer of pydelity's own. It returns the Anthropic or
OpenAI Responses model with the API key from `ProviderEnv`, max output tokens,
the effort mapping (Anthropic adaptive thinking with effort; OpenAI reasoning
effort) and the provider's output mode (`NativeOutput` or `PromptedOutput`,
never forced `tool_choice`, chosen from the model's PydanticAI profile), wrapped
in `LedgerModel`, a PydanticAI `WrapperModel` that runs the per-request
`max_cost` check before each request and appends a ledger line after each
response. A model request that fails after the provider retries raises
`ProviderError` with the provider's own message unchanged, `temporary` set for
failures of a kind the SDK retries (with the message naming the retry count and
setting), and the original exception as its cause. Ported from KGForEdGlobal
`model_registry.py` without its hand-kept model set.

From the command line: after the facts are saved, the run checks the selected
provider's API key and logs `Model ready` with the model, effort and output
mode, or stops with the missing-key error. No model call happens yet.

**Self-Check**

Small real agent runs with each provider, checking the provider settings sent,
ledger lines and prices against the provider's reported usage, the per-request
`max_cost` question (a `max_cost` below one request), and `ProviderError` from a
real rejection (a model ID the provider does not have); attempt counts for
`provider_retries` 0 and 3 by fault injection in the scratchpad (an unreachable
address or a local stub answering 503), since a provider cannot be made to fail
on demand; `just lint`.

### DEV-009 — PDF uploads, reuse and in-request fallback

`Status`: `PENDING` `Depends On`: `DEV-008` `Acceptance`:
`AC-011, AC-018, AC-021, AC-037, AC-041`

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
upload path fails (after the provider retries, through the same SDK client), the
step switches to `BinaryContent` for the rest of the step run, records an
`upload_fallback` warning and `pdf_transport: request`, and writes no upload
record. Two upload errors stop the run with `ProviderError` instead: an
authentication failure and a rejection as too large (413). Nothing checks the
PDF's size first; a provider rejection of the in-request call raises
`ProviderError` that also gives the earlier upload error.

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
with `PROMPT_VERSION` carrying the `pdf_facts.json` summary lines (which say
which facts were unavailable), user instructions and languages; checks C1–C7,
each returning failure items (`page_index` or null, `message` naming the check
with the proposed and measured values, `details`), one item per affected page,
and the `checks[]` and `issues[]` records built from them in C1–C7 order. Unlike
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

The fingerprint from the design's inputs, including the `pdf_facts.json`
fingerprint; reuse of a valid, matching `pdf_survey.json` unless `overwrite`,
and regeneration of a damaged one; the agent built through `build_model` with
the uploaded file, a cache breakpoint after the PDF and facts summary, and an
output validator that raises `ModelRetry` while check retries
(`advanced.survey.check_retries`) remain and, on the last attempt, accepts and
records still-failing checks as review issues. `pdf_survey.json` copies the
facts it used and records `inputs.facts_fingerprint`. It uses PydanticAI's retry
count and last-attempt flag in place of KGForEdGlobal's hand-kept attempt
counter, and drops its raw-attempt files and `ExtractionUsageTracker` (the
ledger replaces it). Python adds `other`, merges languages, stores
`user_instructions`, converts region boxes to points and writes
`pdf_survey.json` atomically. A refusal or an answer that never parses raises
`SurveyError`.

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
`AC-014, AC-018, AC-019, AC-037, AC-038, AC-039, AC-040`

**Goal**

Wrap steps in a run that owns the output folder, `run.json`, the review list and
interrupts.

**Affected Area**

Candidates `src/pydelity/pipeline/{schemas,runner}.py`.

**Expected Outcome**

Settings resolved and validated, the PDF opened (no size or page check), the
folder prepared (stale temp files removed; an `other_pdf_in_folder` warning when
`run.json` or `pdf_facts.json` names another PDF); `run.json` written at start
and end with steps (each listing the `outputs` it wrote or reused,
`pdf_facts.json` as soon as it exists), cost (`run_usd`, `by_step`,
`output_folder_usd`, `unpriced_requests`), the review list (reused outputs'
issues included), warnings and error; `failed`, `stopped` and `interrupted`
recorded before re-raising, with `KeyboardInterrupt` and a cancelled `arun`
(`CancelledError`) caught and re-raised. Warnings are items (`code`, `step`,
`message`, `details`) with this cycle's codes (`unpriced_model`,
`max_cost_exceeded`, `other_pdf_in_folder`, `damaged_output`, `upload_fallback`,
`probe_unavailable`), and each also goes to `PydelityWarning` and the log. A
`ProviderError` or a `max_cost` no ends the run `failed` or `stopped`, with
every written file valid. A planning hook gives the CLI the estimate before any
spend.

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
differs, rendered off the event loop): run header, cost, review list, profile,
facts (the `pdf_facts.json` summary lines first), and one card per page with
region and form-field boxes as percent-positioned CSS overlays and the page's
findings. Static, no JavaScript, no external URLs, every inserted string
escaped; written at the end of every run that got past input validation.

From the command line: the run logs `Report written` with the path of
`report.html`, which opens in a browser.

**Self-Check**

Reports for completed and failed runs on PDFs from the set, opened from disk;
escaping checked with a hostile label; `just lint`.

**Implementation Notes**

Loads the Developer HTML and CSS styles.

### DEV-014 — Python API

`Status`: `PENDING` `Depends On`: `DEV-012, DEV-013` `Acceptance`:
`AC-010, AC-015, AC-039, AC-040, AC-042, AC-043, AC-044`

**Goal**

Let synchronous or async code measure a PDF, estimate, run the survey and read
the results back without the CLI.

**Affected Area**

Candidates for the API module and the package root.

**Expected Outcome**

The coroutines `ameasure`, `aestimate`, `asurvey` and `arun` hold the logic;
`measure`, `estimate`, `survey` and `run` take the same arguments (`pdf`,
`config` as a path, `Config` or mapping, setting keywords; `run` and `survey`
also `allow_over_max_cost`) and call them through the DEV-001 helper, so both
forms give the same results, errors and warnings, including inside Jupyter.
`measure` prepares the output folder and writes or reuses `pdf_facts.json`,
returning `PdfFacts`, with no API key or model call. `survey` writes
`pdf_facts.json` and `pdf_survey.json` and returns `PdfSurvey`. `run` returns a
`RunResult` (`output_dir`, `record`, `facts`, `survey`, `ledger`).
`load(output_dir)`, sync only, reads a folder back into a `RunResult` with
missing parts as `None` and raises `OutputError` for a missing folder or a
corrupt file. Cancelling `asurvey` or `arun` is handled like Ctrl+C. Every
function validates the whole configuration, never prompts or reads stdin. The
root re-exports all of them with `Config`, the result models, `CostEstimate`,
the errors and `PydelityWarning`; import stays free of side effects.

From Python: every function works, sync and async, in a script or in Jupyter,
and `pydelity.load("<output folder>")` reads a run back; the command line is
unchanged.

**Self-Check**

Real calls of every function in both forms, including from inside a running
event loop and two `asurvey` calls on different folders at once; `measure` and
`load` with no API key; cancelling `arun`; import with an empty environment
prints nothing; `just lint`.

### DEV-015 — CLI

`Status`: `PENDING` `Depends On`: `DEV-014` `Acceptance`:
`AC-007, AC-008, AC-009, AC-015, AC-019, AC-037, AC-038, AC-040`

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
upload failures (server error, authentication failure, 413 too large), temporary
failures (429 and 5xx with a short `retry-after-ms`) on model requests and
uploads, a request that rejects the PDF, and a request log the caller can
inspect. The canned bodies follow the response shapes recorded from the real
development runs (usage figures and ids only, never keys). No production code
path exists only for it.

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

Generated pages for configuration, CLI, Python API, `pdf_facts.json`,
`pdf_survey.json`, `run.json`, `cost.jsonl`, `uploads.json` and the survey
checks, each marked as generated and including the measurement and estimate
constants; regenerating after Markdown formatting is byte-identical, so CI's
`git diff --exit-code` catches a stale page.

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
    api.py              measure, estimate, survey, run, their a-versions, load
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
- The survey has no model verifier: its checks are the Python checks only (user
  decision, 2026-11-17; scope non-goal).
- Approved by the user on 2026-11-17 (scope `a938118`, design `2e96832`); user
  style `tony` is locked. Implementation continues in a new session, starting
  with DEV-001's file and folder list for the user's review.
- Test PDF sources: `tests/fixtures/pdfs/SOURCES.md` (DEV-002).
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

Restored on the `RESUME` from `ARCHITECTING` (scope `93d74b8`, design `a78c078`)
and reconciled: DEV-005 now writes and reuses `pdf_facts.json` with its summary
lines and depends on DEV-004 for the output folder; DEV-007 and DEV-008 run
after the facts are saved, with questions asked through callables; DEV-010 sends
the summary lines; DEV-011 adds the facts fingerprint and copy; DEV-012,
DEV-013, DEV-014, DEV-015 and DEV-021 take `pdf_facts.json` and `AC-040`. No
step was added, removed or reordered.

### Suspended Assignment 4

`Recovery Frame`: `1` `Recovery Reason`:
`User rework: add a configurable provider retry count, measure(pdf, ...) and load(output_dir) to the Python API, and async versions of the API functions named arun, asurvey, aestimate and so on; the survey keeps Python checks only, with no model verifier.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`scope 93d74b8 and design a78c078; this unapproved plan draft` `Next Action`:
`Reconcile DEV-004, DEV-005, DEV-008, DEV-014, DEV-015 and DEV-021 (and any other step the new settings and functions touch) with the reworked scope and design, then present the plan for approval.`

Restored on the `RESUME` from `ARCHITECTING` (scope `a938118`, design `2e96832`)
and reconciled: DEV-001 adds `OutputError`, the coroutine helper and an
async-first `arun`; DEV-004 adds `advanced.provider_retries` and renames check
retries; DEV-008 and DEV-009 build the SDK clients with the retry count and set
`ProviderError.temporary`; DEV-014 is rewritten for `measure`, `load` and the
`a` functions; DEV-005, DEV-012 and DEV-013 move blocking work off the event
loop and handle cancellation; DEV-006 adds temporary failures. No step was
added, removed or reordered.

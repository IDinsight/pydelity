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
runs an async function from sync code with `asyncio.run` (design decision 14).
Called while an event loop is running in its thread, the helper raises
`RuntimeError` naming the async function to await (`await pydelity.arun(...)`)
before it creates the coroutine, so nothing is written and no coroutine is left
unawaited. A first `arun()`, with `run()` calling it through that helper, opens
the PDF off the event loop and logs each stage through loguru; the CLI enables
logging at INFO and runs `arun` with `asyncio.run`.

From the command line: `pydelity <pdf>` opens the PDF, logs its name, page
count, size and SHA-256, then `Run finished`; a missing, password-protected or
broken file logs the error and exits non-zero; `pydelity --version` prints the
version; `python -m pydelity <pdf>` does the same.

**Self-Check**

`just lint`; `just test` (existing smoke tests); a scratchpad script exercising
atomic write and load and fingerprints; `pydelity` on a PDF and on a broken
file; `import pydelity` with an empty environment prints nothing. For the
decision-14 rework: `run()` from a script works and its warnings reach the
caller; `run()` inside a running loop (`asyncio.run`, and the
`python -m asyncio` REPL, which awaits at the top level like Jupyter) raises
`RuntimeError` naming `arun`, creates no output folder and leaves no "never
awaited" warning; `await arun()` works there; a real SIGINT during `run()`
cancels the coroutine and raises `KeyboardInterrupt`.

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

Rework evidence (design decision 14), 2026-11-18, on `76e25f0` plus the
uncommitted rework of `utils/coroutines.py`, `api.py` and `cli.py` (macOS arm64,
Python 3.13.9). The `run_coroutine` evidence above is superseded.

- `just lint-python` (Ruff check and format, ty, interrogate 100%) and
  `just test` (2 passed) pass; the `run_sync` doctest passes.
- Scratchpad `dev001_rework_check.py`: 13 of 13 checks passed, on
  `tests/fixtures/pdfs/irs_form_w9.pdf`. From a script, `run()` finishes and
  writes `pdf_facts.json`; its `max_cost` warning (tiny `max_cost`,
  `allow_over_max_cost=True`) reaches the caller's `catch_warnings` and points
  at the script's file. Inside `asyncio.run`, `run()` raises `RuntimeError`
  whose message says that `pydelity.run()` cannot be called while an event loop
  is running and to use `await pydelity.arun(...)` instead, creates no output
  folder and leaves no warning at all after `gc.collect()`; `await arun()` there
  finishes, and its warning also points at the script. In `python -m asyncio`
  (top-level `await`, as in Jupyter) `run()` raises the same `RuntimeError` and
  writes nothing, and `await pydelity.arun(...)` finishes. A real SIGINT 0.3 s
  into `run_sync` on a sleeping coroutine: the coroutine saw `CancelledError`
  and `KeyboardInterrupt` arrived 0.05 s after the signal.
- CLI: `pydelity tests/fixtures/pdfs/irs_form_w9.pdf --yes --output-dir ...`
  logged the estimate and `Run finished`, exit 0; with piped input and no
  `--yes` it stopped before any model request, exit 3.
- Limitation: no Jupyter kernel is installed, so `python -m asyncio` stands in
  for it. The earlier DEV-005 and DEV-007 scratchpad scripts were cleared with
  the scratchpad and were not rerun; the CLI runs above and the warning checks
  cover the paths the rework touched.

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
- pydelity warnings go through `pydelity.utils.coroutines.warn`, which issues a
  `PydelityWarning` that skips stack frames in pydelity and in asyncio, so it
  points at the caller's line in both forms.
- `run_sync(function, /, *args, **kwargs)` takes the async function, not a
  coroutine, so it can check for a running loop before any coroutine exists. Its
  error names the sync function and the `a` function to await, from the
  function's name. The CLI calls `asyncio.run` directly, since it never runs
  inside an event loop. Ctrl+C is `asyncio.run`'s own handling: the first SIGINT
  cancels the main task, then `KeyboardInterrupt` is raised.
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
  prices `claude-opus-5-5` ($4 / $20 per million tokens) and `gpt-6.2-astra` ($8
  / $40 up to 272,000 input tokens per request, $16 / $60 above; corrected
  during DEV-007), so the default model stays as designed.
- Until DEV-004 adds the full configuration, `arun`/`run` take `model` as a
  keyword argument, checked before the PDF is opened.

### DEV-004 — Configuration

`Status`: `DONE` `Depends On`: `DEV-003` `Acceptance`:
`AC-004, AC-007, AC-008, AC-009, AC-041`

**Goal**

Resolve and validate every setting before any work, from defaults, an optional
JSON or YAML file, and CLI options or Python keywords.

**Affected Area**

Candidates `src/pydelity/config/{schemas,loading}.py`; `pyproject.toml` and
`uv.lock` (`uv add` langcodes).

**Expected Outcome**

`Config` (`pdf`, `instructions`, `languages`, `output_dir`, `model`, `max_cost`,
`overwrite`, `advanced`) and `AdvancedConfig` (`provider_retries` 0–10, default
2; `survey` with `check_retries`; `uploads`; and `models` holding prices only)
with `extra="forbid"` and the design's defaults and bounds; language tags
checked with `langcodes.tag_is_valid` and kept in `langcodes.standardize_tag`
form (design decision 15), a rejected tag named by position and value
(`languages[1]: "zz"`); `.json`, `.yaml` and `.yml` loading with relative paths
resolved against the config file's folder; precedence keywords or CLI over file
over defaults, with the CLI `PDF` winning; `expiry_hours` checked against the
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

Evidence, 2026-11-17, repo root, uncommitted on top of `274b41a`:

- Scratchpad `tools/dev004_check.py`: 37 of 37 checks passed.
  - Files: YAML and JSON load; `pdf` and `output_dir` in a file are relative to
    the file's folder; `max_cost: 0.1` in YAML becomes `Decimal("0.1")` exactly;
    defaults fill in (model, provider retries 2, check retries 2, output folder
    `pydelity-output/<PDF name>`).
  - Precedence: a keyword `pdf` wins over the file's; keywords win, and nested
    `advanced` keywords merge with the file; a `False` keyword wins over a
    file's `True`; a `Config` given as `config` contributes only the values it
    was given; keyword paths are relative to the current directory.
  - One `ConfigError` named all 10 problems in one file: missing PDF, a bad
    language tag, a negative `max_cost`, provider `google`, an unknown key
    `colour`, out-of-range provider and check retries, effort `max`, and a
    `models` entry with a bad key and a missing price. The upload expiry is
    checked against the selected provider (Anthropic 1–2,160 hours, OpenAI
    1–720), and skipped when the model setting is itself invalid.
  - Unreadable files: invalid JSON, invalid YAML, a list instead of settings, a
    `.toml` file and a missing file each give a `ConfigError` naming the file;
    an empty YAML file holds no settings.
  - Language tags: `en`, `zh-Hant-TW`, `zxx`, `ar-EG-u-nu-latn` and `x-private`
    pass; `en_US`, `e`, `en-`, `123` and `english words` fail.
  - `read_api_key` raises `MissingApiKeyError` naming `ANTHROPIC_API_KEY` when
    the key is unset or blank, ignores the `.env` in the current folder, and
    returns a `SecretStr` that hides the key.
- CLI: `pydelity -c settings.yaml` (PDF, language and OpenAI model in the file)
  logged `Settings OK` and `Model: gpt-6.2-astra from provider openai`. With a
  PDF argument, `--model`, `--language`, `--max-cost 2.50`, `--overwrite`,
  `--output-dir`, `--instructions` and `-v`, the options won over the file, and
  the resolved settings were logged as JSON with the effective output folder.
  `--model google:x --language en_US --max-cost abc` printed one error listing
  all 3 settings and exited 2; no PDF anywhere exited 2 with
  `pdf: required: give the PDF as an argument or set pdf`; a missing config file
  was named.
- `just lint-python` (Ruff, ty, interrogate 100%) and `just test` (2 passed)
  passed. `env -i` `import pydelity` printed nothing, took 0.18 s and loaded no
  `pydantic_ai`.

Rework evidence, 2026-11-17, after design `117eafe` (decision 15), uncommitted
on top of it:

- `langcodes` 3.5.1 added (`uv add`; no other package came with it). Probe of
  its two functions: `en_US` and `EN-us` → `en-US`, `iw` → `he`, `eng` → `en`;
  `zxx`, `und`, `mul`, `qaa`, `x-private`, `zh-Hant-TW` and `ar-EG-u-nu-latn`
  valid; `zz`, `en-`, `e`, `123`, `english` and `en US` rejected.
- Scratchpad `tools/dev004_check.py`, updated for decision 15: 48 of 48 checks
  passed, the earlier 37 included. `languages: [en_US, EN-us, en-US, ar]`
  resolves to `[en-US, en-US, en-US, ar]`; `[en, zz, en-]` gives one
  `ConfigError` naming `languages[1]: "zz"` and `languages[2]: "en-"`; the
  10-problem file now names `languages[1]` for its `zz`.
- CLI: `--language en_US --language EN-us --language iw -v` logged
  `["en-US", "en-US", "he"]`; `--language ar --language zz --language en-`
  listed both bad tags by position and exited 2.
- `just lint-python` and `just test` (2 passed) passed. `env -i`
  `import pydelity` printed nothing and took 0.25 s (it loads `langcodes`, not
  `pydantic_ai`).

**Implementation Notes**

- Files approved by the user (2026-11-17):
  `src/pydelity/config/{__init__,schemas,loading}.py`, plus changes to `api.py`
  and `cli.py`.
- `parse_model` (DEV-003) now raises `ValueError`, so the configuration reports
  a bad model setting with every other problem instead of stopping at it.
- The upload-expiry range is checked in `resolve_config`, after the model is
  known, not inside `Config`; every API path goes through `resolve_config`.
- `Config.output_dir` stays `None` when not set; `Config.output_folder` applies
  the default (`pydelity-output/<PDF name>` in the current folder).
- `is_language_tag` checks BCP-47 syntax only (RFC 5646 well-formed tags,
  without grandfathered tags) and is public, so the survey's language check
  (DEV-010) can reuse it.
- Language tags (design decision 15): `is_language_tag` is
  `langcodes.tag_is_valid` and `standard_language_tag` is
  `langcodes.standardize_tag`; both are public in `config/schemas.py` so DEV-010
  and DEV-011 reuse them. The setting keeps duplicates after standardizing
  (`en_US` and `en-US` both stay); DEV-011's merge, which compares exact
  standard forms, is where repeated tags meet. Error paths write list items by
  position (`languages[1]`) and show values as JSON.
- CLI options default to `None`, so an option left out never overrides the
  config file. `--quiet` and `--yes` come with DEV-015 and DEV-007.

### DEV-005 — Survey probe and `pdf_facts.json`

`Status`: `DONE` `Depends On`: `DEV-001, DEV-002, DEV-004` `Acceptance`:
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

Evidence, 2026-11-17, repo root, uncommitted on top of the DEV-004 rework
commit:

- Scratchpad `tools/dev005_check.py`: 35 of 35 checks passed, on the 9 committed
  PDFs, a scratchpad copy of `irs_pub1_arabic.pdf` with page 0 set to rotation
  90, and KGForEdGlobal's full 142-page CAPS (read only).
  - Arabic Publication 1: right to left on both pages, upright, tagged (good).
    Chinese: text good, Han letters count as left to right. Gazette: 85% of
    characters in vertical writing; one signature field; AcroForm without XFA;
    printed number from its page label.
  - W-9: 23 fields (8 checkboxes unchecked, 15 text), AcroForm and XFA, field
    boxes inside the page; a short sideways line on page 0 while the dominant
    angle stays 0. W-9 instructions: 22 bookmarks, pages 1–6 printed 2–7 (offset
    +1), running footer repeated in the bottom band.
  - 1965 Form 1040A scan: no characters, no orientation, no direction.
  - CAPS excerpt: rotation attribute 0 on every page with the text at 90°
    (confident); page labels 23–30 as one range, offset +23; untagged. Rotated
    copy: page 0 (attribute 90) reads 270 and is landscape, page 1 stays 0.
  - 1950 Form 1040: labels 1–4 (offset +1); 202 sideways heading characters on
    page 3 with the dominant angle 0. Slides: 16 pages of 720 × 540 points,
    footer repeated on all 16, IDs `R1`… in order.
  - `pdf_facts.json` via `pydelity.run`: written with no API key in the
    environment; a stale `pdf_facts.json.tmp-…` removed; `schema_version` `1.0`,
    `probe_version` 1, `pydelity_version` and the PDF identity set; the
    fingerprint equals the formula; `summary` equals `summarize(facts)`; a rerun
    leaves the file byte-identical; `overwrite=True` measures again; a damaged
    file issues a `PydelityWarning` and is measured again.
  - Fault injection (scratchpad patch of `_bookmarks` raising `RuntimeError`):
    `bookmarks` is `null`, one `probe_errors` item, a summary line and a
    `PydelityWarning`; the form and structure are still read.
  - Event loop: while `arun` measured the 142-page CAPS (1.55 s), a ticker task
    kept running; its longest wait was 47 ms (median about 30 ms), because
    PyMuPDF holds the GIL while it extracts text.
- CLI on every PDF in the set: the summary lines are logged at INFO, `-v` logs
  one line per page, and a rerun logs `Facts reused`.
- First run of the W-9 instructions picked a list marker (`1.`) near the top
  over the page number at the bottom, splitting the numbering into four ranges.
  Fixed: among a page's candidates, the style and offset most pages share wins,
  and nearness to the edge breaks ties.
- A search of `surveying/` for document-type and domain words found none.
- `just lint` (Prettier, STANDARDS check, markdownlint, Ruff, ty, interrogate
  100%, zizmor) and `just test` (2 passed) passed; `env -i` `import pydelity`
  printed nothing.

**Implementation Notes**

- Files approved by the user (2026-11-17):
  `src/pydelity/surveying/{__init__,schemas,probe,facts}.py`, plus `api.py` and
  `.gitignore` (`pydelity-output/`).
- PyMuPDF reports text directions and boxes in the unrotated page's coordinates,
  so the probe turns line directions into displayed angles
  (`(unrotated angle − rotation attribute) mod 360`) and boxes into displayed
  coordinates with `page.rotation_matrix`.
- Measurement constants (public in `probe.py`, for the generated reference):
  band 10% of page height; direction share 0.7; garbled share 0.1; orientation
  share 0.8 with at least 20 characters; repeated lines on at least 3 pages and
  5% of pages (2 pages for 2–3-page PDFs), at most 200; structure cap 20,000
  elements, at least 10 elements, 90% page coverage for `good`.
- The structure tree is walked with `xref_get_key`, parsing `K` arrays for
  references, marked-content IDs and inline references; page coverage counts
  pages with marked content or object references. The summary marks a page as
  mostly vertical from 50% vertical characters.
- PDFs are iterated by index (`document[index]`), since PyMuPDF's `Document` has
  no `__iter__` for type checkers. `measure_facts` issues warnings from the
  coroutine (`pydelity.utils.coroutines.warn`) and logs them; DEV-012 adds them
  to `run.json`.

### DEV-007 — Cost ledger, pricing, estimate and `max_cost` guard

`Status`: `DONE` `Depends On`: `DEV-003, DEV-004` `Acceptance`:
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

Evidence, 2026-11-17, repo root, uncommitted on top of the DEV-005 commit:

- Scratchpad `tools/dev007_check.py` (no network): 36 of 36 checks passed.
  - Ledger: `cost_usd` written as a JSON number; spend and unpriced count read
    back; a damaged last line skipped with a note; the next append removes the
    unfinished line (3 valid lines after); a damaged middle line (edited by
    hand) raises `OutputError` naming the line; 50 concurrent appends give 50
    valid lines; a missing ledger reads as empty.
  - Pricing and estimate: 1M input tokens on `claude-opus-5-5` = $4; an unknown
    model is unpriced; `advanced.models` prices apply. Estimate for 7 pages and
    4,000 prompt characters: expected $0.381952 and maximum $2.969856 (3
    requests), equal to the formulas by hand. Over `max_cost` at $1, and at $2
    with $1.90 already spent; an unpriced model with `max_cost` is over (no
    price) and warns, and without `max_cost` only warns; a reused survey costs
    nothing.
  - Guard: within `max_cost` no question; 5 concurrent request checks over it
    ask once, record `spent_usd` 0.5 and `projected_usd` 1.1, issue one
    `PydelityWarning`, then allow; a no raises `BudgetExceededError` naming the
    three ways to continue; no `max_cost` never asks.
  - Python API: over `max_cost` raises `BudgetExceededError` after a
    `PydelityWarning`; `allow_over_max_cost=True` completes; no `max_cost`
    completes without a question.
  - CLI with piped input: no `--yes` exits 3 and says to pass `--yes`; `--yes`
    completes; over `max_cost` without `--yes` warns then exits 3; with `--yes`
    warns then completes.
  - CLI in a pseudo-terminal (run outside the sandbox, which has no pty
    devices): answer `n` exits 3; `y` completes; over `max_cost` asks once,
    after the warning; Ctrl+C at the question ends the run in 0.03 s (exit 130).
- Scratchpad `tools/dev007_real.py` (real requests, keys loaded from the user's
  `.env` into that process only, run outside the sandbox because its proxy broke
  TLS): one tiny request each to `anthropic:claude-opus-5-5` (18 input, 4 output
  tokens, $0.000152) and `openai:gpt-6.2-astra` (13 input, 5 output, $0.000304).
  Each price equals the list price by hand ($4 / $20; $8 / $40),
  `advanced.models` prices apply to the same responses, and the two ledger lines
  sum to $0.000456. Total spend on these checks: about $0.001.
- `just lint` and `just test` (2 passed) passed; `env -i` `import pydelity`
  printed nothing and loaded no `pydantic_ai`.

**Implementation Notes**

- Files approved by the user (2026-11-17):
  `src/pydelity/costs/{__init__,schemas,ledger,pricing,budget}.py`, plus changes
  to `api.py` and `cli.py`. `utils/coroutines.py` gains `run_in_daemon_thread`,
  a helper inside an approved file.
- Questions run on a daemon thread (`run_in_daemon_thread`), not
  `asyncio.to_thread`: `asyncio.run` waits for its executor's threads on exit,
  so Ctrl+C at a question would otherwise wait for an answer.
- `append_entry` removes an unfinished last line before appending. Without it,
  an interrupted append followed by a later run left a damaged line in the
  middle of `cost.jsonl`, and every later read failed.
- The CLI runs through `pydelity.api.arun_with_questions` (confirmation and
  over-`max_cost` decision as callables); `arun` passes none and decides with
  `allow_over_max_cost`. DEV-012 moves the run into the orchestration component.
  `SpendDeclinedError` (a `PydelityError` in `costs/budget.py`, not exported)
  marks a declined confirmation; the CLI exits 3 for it and for
  `BudgetExceededError`.
- Until DEV-010 builds the prompt, the estimate counts the facts summary and the
  instructions as the prompt. `TYPICAL_OUTPUT_TOKENS` (8,000) and the
  tokens-per-page figures are to be compared with real survey usage in DEV-011.
- `gpt-6.2-astra` has tiered prices in `genai-prices` (see the DEV-003 note);
  pydelity prices each request through `genai-prices`, which applies the tier.

### DEV-008 — Model factory and LedgerModel

`Status`: `DONE` `Depends On`: `DEV-003, DEV-004, DEV-007` `Acceptance`:
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

Evidence, 2026-11-18, on `8a96ab0` plus the uncommitted DEV-008 changes (macOS
arm64, Python 3.13.9, pydantic-ai-slim 2.69.0).

- `just lint-python` (Ruff check and format, ty, interrogate 100%) and
  `just test` (2 passed) pass.
- Scratchpad `dev008_offline.py`: 25 of 25 checks passed against a loopback stub
  of the Anthropic API reached through `ANTHROPIC_BASE_URL` (the design's test
  seam), with no provider key in the environment. It ran outside the sandbox,
  which does not allow binding a local port. The SDK clients get `max_retries`
  from `advanced.provider_retries` (3 and 0 tried) and the 900 s timeout. Model
  settings: Anthropic `anthropic_effort`, adaptive `anthropic_thinking` and
  `max_tokens` 32000; OpenAI `openai_reasoning_effort` and `max_tokens`. Output
  mode: native for `claude-opus-5-5` and `gpt-6.2-astra`, prompted for an
  unknown older Claude ID. A missing key raises `MissingApiKeyError`. The
  request body carried `max_tokens` 32000, adaptive thinking,
  `output_config.effort` and a `json_schema` format. Each response wrote one
  ledger line priced by hand ($0.008 for 1,000 input and 200 output tokens),
  with requests numbered 1 and 2. A `max_cost` of $0.01 (one request's upper
  bound is $0.64) asked once: no raised `BudgetExceededError` with nothing sent
  and no ledger; yes sent and recorded two requests with one question. A 400
  gave `ProviderError` after one attempt, not temporary, with the provider's
  message unchanged. A 503 (`retry-after-ms: 1`) made 1 attempt with
  `provider_retries` 0 and 4 with 3, temporary, and the message names the
  retries and `advanced.provider_retries`. An unreachable address gave a
  temporary `ProviderError` with no status code.
- Scratchpad `dev008_real.py`, real requests with the user's keys loaded from
  `.env` into that process only (never printed), effort `low`, default
  `max_output_tokens`: for `anthropic:claude-opus-5-5` and
  `openai:gpt-6.2-astra`, a `max_cost` below one request with the answer no sent
  nothing; with yes, one question, a parsed structured answer, and one ledger
  line priced exactly by hand ($0.001008 for 207 input and 9 output tokens;
  $0.00088 for 50 and 12). The bodies sent carried `max_tokens` (Anthropic) or
  `max_output_tokens` (OpenAI) 32000, effort `low`, a `json_schema` output
  format and no `tool_choice`. Nonexistent model IDs gave `ProviderError` 404,
  not temporary, with the provider's own message (`model: claude-nonexistent-1`;
  OpenAI's "does not exist or you do not have access to it") and no ledger line.
  A streamed Anthropic run recorded its line too. 15 of 15 passed; about $0.003
  spent.
- CLI on `tests/fixtures/pdfs/irs_form_w9.pdf` with `--yes`: without
  `ANTHROPIC_API_KEY`, the facts were saved, then exit 2 with the missing-key
  error. With a placeholder key (no request is made), it logged
  `Model ready: claude-opus-5-5 from anthropic, effort high, native structured output`,
  then the estimate and `Run finished`, exit 0; `gpt-6.2-astra` and an unknown
  older Claude ID logged native and prompted output.

**Implementation Notes**

- Files approved by the user (2026-11-18): `src/pydelity/providers/factory.py`
  and `src/pydelity/providers/ledger_model.py` (in the existing `providers/`
  folder, not the sketched `models/`), plus changes to `src/pydelity/errors.py`
  and `src/pydelity/api.py`.
- The per-request upper bound is the request's estimated input (text at
  `PROMPT_CHARS_PER_TOKEN`, each document at the PDF's page count times the
  provider's tokens per page, each earlier answer at its reported output tokens)
  plus the request's own `max_tokens`. With the default 32000 that is about
  $0.64 per request on `claude-opus-5-5` and $1.28 on `gpt-6.2-astra`, so a
  smaller `max_cost` always asks. `costs/budget.py`'s `request_upper_bound`,
  which read the survey's `max_output_tokens`, is no longer used.
- `LedgerModel` wraps the streaming path too, so no request goes unrecorded. An
  unpriced response is recorded with a null cost; the estimate already warns
  `unpriced_model` before the run spends.
- `api.py` makes a run ID (`_new_run_id`) for the ledger context until DEV-012
  moves the run into its own module.
- For DEV-011: a `PydelityWarning` raised inside PydanticAI's agent loop (the
  per-request `max_cost` warning) points at PydanticAI's own file, because
  `warn` skips only pydelity and asyncio frames; DEV-011 should make it point at
  the caller's code. PydanticAI prints a first-run banner only when a script
  calls an agent itself, not when an installed library does; DEV-011 confirms no
  banner appears when the survey runs from pydelity.

### DEV-009 — PDF uploads, reuse and in-request fallback

`Status`: `DONE` `Depends On`: `DEV-008` `Acceptance`:
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

Evidence, 2026-11-18, on `80e6bcb` plus the uncommitted DEV-009 changes (macOS
arm64, Python 3.13.9, anthropic 2.10.0, openai 3.53.0).

- `just lint-python` (Ruff check and format, ty, interrogate 100%) and
  `just test` (2 passed) pass.
- Scratchpad `dev009_offline.py`: 20 of 20 checks passed against a loopback stub
  of Anthropic's Files API (through `ANTHROPIC_BASE_URL`, no provider key; run
  outside the sandbox, which does not allow binding a local port). The first
  upload sends the provider maximum (`expires_in_seconds` 7776000) and records
  provider, file ID, PDF name, size, SHA-256 and expiry in `uploads.json`; a
  rerun reuses it with no upload. A record with 59 minutes left is uploaded
  again and replaced, while another provider's record for the same PDF stays.
  `expiry_hours` 1 sends 3600. A damaged `uploads.json` and one with
  `schema_version` 2.0 each give one warning, then an upload and a rewritten
  file. A 503 with `provider_retries` 2 made 3 attempts, then fell back: the
  PDF's bytes as `BinaryContent` (`application/pdf`), one warning, no record,
  and an `upload_error` naming the PDF and the provider's message; a 400 fell
  back after one attempt. A 401 and a 413 stopped with `ProviderError` after one
  attempt, not temporary, nothing recorded. `is_missing_file` is true for a 404
  naming the file ID, false for a missing model and for a PDF sent in the
  request; `replace_missing_upload` uploads again and replaces the record, or
  falls back when that upload fails; `with_upload_error` gives both errors.
- Scratchpad `dev009_real.py`, real Files API calls with the user's keys loaded
  from `.env` into that process only (never printed), `expiry_hours` 2: for
  Anthropic and OpenAI, an upload recorded with about two hours left, then
  reused by a rerun. A recorded file ID the provider does not have made a
  request fail with the provider's 404 (Anthropic: ``File `file_…` not found.``;
  OpenAI: `Files [file-…] were not found`), no ledger line and no charge;
  `is_missing_file` recognized it, and `replace_missing_upload` uploaded again
  and replaced the record. An invalid key stopped the upload with
  `ProviderError` 401 for both providers. The CLI with `--yes` and a config file
  logged `Uploaded irs_form_w9.pdf to anthropic: file …, expires … UTC`, then
  `Reusing upload …` on the rerun. 13 of 13 passed; every test upload was
  deleted afterwards. No PDF in the set is rejected by either provider, so no
  real rejection was available.
- A first real run used `expiry_hours` 1. Its reuse checks failed as the design
  intends: a one-hour upload starts with just under an hour left, below the
  one-hour reuse threshold, so it is never reused. The run was repeated with two
  hours; the extra test uploads it left were deleted.

**Implementation Notes**

- Files approved by the user (2026-11-18): `src/pydelity/providers/uploads.py`
  and `src/pydelity/providers/schemas.py`, plus changes to `src/pydelity/api.py`
  and `src/pydelity/costs/budget.py` (the unused `request_upper_bound` removed).
- Uploads go through the model's own SDK client, so `advanced.provider_retries`
  and the timeout apply to them too.
- DEV-011 calls `attach_pdf` (already called in `api.py` after the
  confirmation), puts `PdfAttachment.content` in the user message, uses
  `is_missing_file` and `replace_missing_upload` once on a 404, and wraps a
  rejection after the fallback with `with_upload_error`. The `upload_fallback`
  warning text and `PdfAttachment.upload_error` are ready for `run.json`
  (DEV-012).
- OpenAI's own 401 message repeats the key it received, masked except for its
  first and last few characters, and `ProviderError` keeps the provider's
  message unchanged.

### DEV-010 — Survey proposal, profile, prompt and checks

`Status`: `DONE` `Depends On`: `DEV-005` `Acceptance`:
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
and the `checks[]` and `issues[]` records built from them in C1–C7 order. C7
checks the model's languages with `langcodes` (design decision 15): one failure
item per rejected tag (`details`: `{"proposed": "<tag>"}`) or one for an empty
list, `page_index` null. Unlike KGForEdGlobal's validators, which raise on the
first problem, each check returns all its failures, so one retry message names
every problem and the last attempt can record them all.

From the command line: `--verbose` logs the prompt and facts summary the survey
will send. No model call happens yet.

**Self-Check**

Scratchpad script running the checks on hand-made passing and failing proposals
against facts from the PDF set; a search of code and prompt for document-type
terms and word lists; `just lint`.

Evidence, 2026-11-18, on `80e6bcb` plus the uncommitted DEV-009 and DEV-010
changes (macOS arm64, Python 3.13.9).

- `just lint-python` (Ruff check and format, ty, interrogate 100%) and
  `just test` (2 passed) pass; the `survey_pdf` doctest passes.
- `SurveyAnswer`'s JSON schema (about 9,000 characters) passes the strict
  structured-output transformers PydanticAI uses for `claude-opus-5-5` and
  `gpt-6.2-astra`.
- Scratchpad `dev010_check.py`: 30 of 30 checks passed, on facts the probe
  measured from the committed PDFs. An answer built from each PDF's own facts
  passes all seven checks on all 9 PDFs. C1: an empty name, a name used twice
  (`Body`, and `body` followed by a space), a label without kinds and a region
  naming a missing label give 4 failures, the last on the region's page; a
  region using `Other` passes. C2: a region on page 6 of 6 (page null), a box
  with `x0 == x1` and one with `x1` 1.2 (on their pages). C3 on the CAPS extract
  (8 pages measured at 90 degrees): no rotation gives 8 failures, one per page,
  `{"measured": 90, "proposed": 0}`; a range past the last page gives a
  page-null failure and leaves pages 5-7 failing; overlapping ranges give one
  failure per shared page (3, 4). C4 on the W-9 instructions (pages 1-6 print
  index + 1): offset 2 gives 12 failures (6 wrong pages, 6 pages of the
  uncovered measured range); style `none` gives the same 12; covering pages 1-3
  only fails pages 4-6; with one page's number changed, 5 of 6 matching (83%)
  passes and 4 of 6 (67%) fails on the 2 wrong pages. C5 on the CAPS extract (8
  repeated lines): 5 missing IDs, `R2` twice and an unknown `R9` give 7
  failures. C6: a range past the last page and page 3 in two ranges. C7: `zz`
  and `en-` rejected with `{"proposed": tag}`, `zxx` and `EN_us` accepted; an
  empty list fails once with `{"proposed": []}`. `check_results` gives 7 results
  in C1-C7 order with the attempts; `review_issues` one issue per failure with
  `step` `survey`; `retry_message` names all 9 failures. The prompt explains
  every role and kind, and the request text carries the page count, facts,
  instructions and languages.
- Word search of `prompts.py`, `validators.py`, `schemas.py` and the
  instructions for document-type and domain words (invoice, contract, textbook,
  lesson, chapter, exam, student, grade, article, report, tax, legal, medical,
  letter, slide, book and others): only "contract" (the interface later steps
  rely on) and "letters" (Unicode letter characters) in `schemas.py`, neither a
  document type. The only string lists in code are the `Literal` vocabularies of
  the schemas, not natural-language word lists.
- CLI on `irs_form_w9.pdf` with `--verbose`, a placeholder key and piped input:
  it logged `Survey instructions (prompt version 1):` with the instructions and
  `Survey text sent with the PDF:` with the facts, then stopped before any
  upload, exit 3. The estimate now counts the real prompt (instructions, text
  and answer schema): about $0.36, at most $2.90 on `claude-opus-5-5`, up from
  $0.35 and $2.87.
- Prompt rework at the user's request, 2026-11-18: the prompt is built the way
  KGForEdGlobal builds its prompts. `survey_pdf` in `surveying/prompts.py`
  writes both messages inside the function and returns a `PromptPair`
  (`system_message`, `user_message`) from the new `utils/prompts.py`; the role
  and kind descriptions sit in the text next to their enum values. Both messages
  are identical to the earlier module-level text, for a 1-page PDF without
  instructions or languages and for a 12-page PDF with both, so `PROMPT_VERSION`
  stays 1. After the change, `dev010_check.py` (30 of 30), Ruff, ty, interrogate
  100% and the doctests pass, and the CLI check above gives the same log and
  estimate.

**Implementation Notes**

- Files approved by the user (2026-11-18): `src/pydelity/surveying/prompts.py`
  and `src/pydelity/surveying/validators.py` (the user chose `validators.py`
  over `checks.py`, and later steps use the same name), plus changes to
  `src/pydelity/surveying/schemas.py` and `src/pydelity/api.py`. With the prompt
  rework, the user approved the new `src/pydelity/utils/prompts.py` for
  `PromptPair`, which later steps' prompts also return.
- The user kept all checks in `validators.py` (2026-11-18) after reviewing which
  rules need only the answer and could run as Pydantic validators instead;
  moving them would make those failures fail the survey on the last attempt, a
  design change, so the design stays as it is.
- Local choices in the checks: label names and region labels compare after
  trimming spaces, regardless of case. A range outside the PDF, or ending before
  it starts, gives one failure with `page_index` null; overlapping ranges give
  one failure per shared page. C3 compares the clockwise rotation with the
  measured counterclockwise text angle, which are equal for upright content. In
  C4, a null offset matches no printed number; when a range fails the 80% rule,
  its pages with a wrong number fail; each page of a measured range of 3 or more
  pages (arabic or roman) fails unless a range with the measured offset covers
  that page. C5's failures have `page_index` null, since a repeated line is on
  many pages. The thresholds are named constants (`PAGE_NUMBERING_MATCH_SHARE`
  0.8, `PAGE_NUMBERING_MIN_RANGE_PAGES` 3).
- `PdfSurvey` holds the design's fields plus `schema_version`. Adding `other`,
  merging languages, storing `user_instructions` and converting region boxes to
  points are DEV-011's.

### DEV-011 — Survey step

`Status`: `DONE` `Depends On`: `DEV-009, DEV-010` `Acceptance`:
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
ledger replaces it). Python adds `other`, merges languages (user tags first, all
in standard form, leaving out model tags C7 still rejects after the check
retries), stores `user_instructions`, converts region boxes to points and writes
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

Evidence, 2026-11-18, on `a65021a` plus the uncommitted DEV-011 changes (macOS
arm64, Python 3.13.9, PydanticAI 2.69.0).

- `just lint-python` (Ruff check and format, ty, interrogate 100%) and
  `just test` (2 passed) pass.
- Scratchpad `dev011_offline.py`, 30 of 30 checks, no network: PydanticAI's
  `FunctionModel` inside pydelity's `LedgerModel` stands in for the provider.
  - A correct answer: one request; all seven checks pass with `attempts` 1. The
    request is the instructions as the system message, then the uploaded file,
    the text and a cache point.
  - The profile:
    - The model's `Other` label is dropped, and `other` is added last with role
      `body` and every kind.
    - With the user's `en_US` and the model's `EN` and `fr`, the languages are
      `en-US`, `en` and `fr`.
    - A region box becomes points on the page's measured size, and its label
      takes the profile label's spelling.
    - The user's instructions are stored, the facts are copied in, and the
      fingerprint matches the inputs.
  - `Survey finished` names the labels, languages, rotation, review-issue count
    and cost.
  - Reuse: the same inputs (also with `EN-us`) and changed
    `advanced.provider_retries`, timeout or `max_cost` reuse the survey.
    `overwrite`, or a change to the instructions, languages, model, check
    retries, effort or `max_output_tokens`, runs it again. `arun` with unchanged
    inputs logs `Survey reused` with no API key set; with `overwrite` or new
    instructions it goes on to the model and stops at the missing key. A damaged
    `pdf_survey.json` gives a warning and the survey runs again.
  - Retry, then pass, on the CAPS extract: the second request carries the retry
    message naming page 0 and the measured 90 degrees; every check passes with
    `attempts` 2.
  - Still failing with `check_retries` 1: the second answer is accepted. There
    are 12 review issues (labels 2, regions 1, rotation 8, languages 1), each
    with `step` `survey`, its check and its page. `zz` is left out of the
    profile's languages, and an issue names it. The duplicate label is dropped,
    the label without kinds may take every kind, and the region on page 99 is
    dropped.
  - `SurveyError` and no `pdf_survey.json` for an answer that never parses
    (after 3 requests), a refusal (with the refusal text) and running out of
    output tokens (naming `advanced.survey.max_output_tokens`).
  - A 404 naming the uploaded file: one new upload, the `uploads.json` record
    replaced, and the survey starts over with the new file. A failed re-upload
    falls back to sending the PDF in the request. When the provider rejects that
    too, the `ProviderError` keeps the provider's message, adds the upload
    error, and has the SDK error as its cause. A 404 that does not name the file
    (a missing model) raises `ProviderError` with no new upload.
  - The `max_cost` warning raised inside the agent loop points at the calling
    script. Before the change to `utils/coroutines.py` it pointed at a
    PydanticAI file, and then at an anyio file.
- Scratchpad `dev001_rework_check.py` (12 of 12) still passes. It now stops each
  run at a tiny `max_cost` instead of letting it reach the model.
- Real runs (`dev011_real.py`, $1.86 in total, each run held under $6 by
  pydelity's own `max_cost` guard):
  - `openai:gpt-6.2-astra` on the W-9: a first run (one request, $0.39), a rerun
    that sent nothing, and a rerun with new instructions that reused the upload
    (one request, $0.40). The `--overwrite` run was stopped by the plan-time
    guard before anything was sent: its maximum ($5.55, three requests of up to
    32,000 output tokens) was more than the budget left. The overwrite path
    itself ran on Anthropic and offline. The cache point is accepted by OpenAI's
    Responses API.
  - `anthropic:claude-opus-5-5` on the W-9 from the command line with
    `--language en_US --yes`: exit 0, `Survey finished` (one request, $0.19).
    The rerun logged `Survey reused` and sent nothing. New instructions reused
    the upload (one request, $0.20). `overwrite` within five minutes read 27,804
    tokens from the cache ($0.08).
  - The CAPS extract on Anthropic: the model's first answer had 5 check
    failures; the second passed. The profile has rotation 90 on pages 0-7, page
    numbers with offset 23 and every repeated line accounted for (two requests,
    $0.24).
  - Fault injection on the W-9 (a C1 failure added in the script): failing once
    gave two requests, `attempts` 2, and all checks passing, with the retry
    reading 27,767 tokens from the cache. Always failing, with `check_retries`
    1, gave two requests and an accepted answer with `labels` failed and one
    review issue.
  - Each `pdf_survey.json` was reviewed against its PDF:
    - W-9: page 0 has no page number and pages 1-5 print the page index plus
      1. The running form name (R1) and `Page N` (R2) are artifacts, and the
         form, tables and their notes are regions.
    - CAPS extract: one table runs across all 8 pages, rotated 90 degrees, with
      an upright running header and footer.
  - The estimate is above the real cost: $0.36 against $0.08-$0.20 per Anthropic
    survey, and $0.63 against $0.39-$0.40 per OpenAI survey. The real output was
    1,858-5,633 tokens per answer, against the estimate's 8,000.
- PydanticAI's first-run banner appeared in these runs. PydanticAI hides it when
  the code that starts the agent is in `site-packages`. On this Homebrew Python,
  though, the standard library's real path (`/opt/homebrew/Cellar/...`) differs
  from the one `sysconfig` reports (`/opt/homebrew/opt/...`). PydanticAI then
  takes `contextlib` for the user's code, and the banner appears even with
  pydelity installed from a wheel (checked in a fresh virtual environment).

**Implementation Notes**

- Files approved by the user (2026-11-18): `src/pydelity/surveying/agents.py`,
  `src/pydelity/surveying/llm.py` and `src/pydelity/surveying/survey.py`, plus
  changes to `src/pydelity/api.py` and `src/pydelity/utils/coroutines.py`.
- In PydanticAI 2.69 the output retry count is `Agent(retries={"output": n})`;
  an answer that does not parse uses one of the same retries. `attempts` is the
  run's request count, which is 1 plus the retries used.
- After the last attempt, the profile keeps the model's values with these
  exceptions, each reported by a review issue:
  - a label with an empty name, or a name an earlier label already uses
    (regardless of case), is left out;
  - a label without kinds may take every kind, so every label has at least one
    (AC-002);
  - a region on a page the PDF does not have is left out, since its box cannot
    be converted. Region boxes are rounded to 0.01 points.
- The survey's cost in `Survey finished` is the sum of the `cost.jsonl` lines
  the survey added.
- `arun` checks for a reusable `pdf_survey.json` right after the facts, so a
  reused survey needs no API key and logs no estimate.
- `warn` also skips PydanticAI, pydantic_graph and anyio frames. A warning
  raised inside the agent loop runs in an anyio task. It points at the line that
  called the sync function, or, for an awaited `arun`, at the code that runs the
  event loop.
- The user approved a change to `src/pydelity/cli.py` (2026-11-18): the command
  sets `pydantic_ai.BANNER_ENABLED = False` for its own process, while the
  Python API leaves the banner to PydanticAI and the caller. Checked offline
  with a placeholder key and no network: the command printed no banner, and
  `pydelity.run` in the same setup printed it once. In that run the command also
  printed each `PydelityWarning` a second time, as a Python warning pointing at
  a Typer file, after its log line; DEV-012 handles warnings in the command.

### DEV-012 — Run orchestration

`Status`: `DONE` `Depends On`: `DEV-004, DEV-007, DEV-011` `Acceptance`:
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

Evidence, 2026-11-18, on `a5a1c06` plus the uncommitted DEV-012 changes (macOS
arm64, Python 3.13.9).

- `just lint-python` (Ruff check and format, ty, interrogate 100%) and
  `just test` (2 passed) pass.
- Scratchpad `dev012_offline.py`, 26 of 26 checks, no network. `build_model` is
  patched to wrap PydanticAI's `FunctionModel` in `LedgerModel`, and the command
  runs in a child process with the same patch.
  - Completed run: `run.json` is `completed`, with one survey step (`completed`,
    outputs `pdf_facts.json` and `pdf_survey.json`, 1 request, transport
    `upload`). `cost.by_step`, `run_usd` and the step's `cost_usd` equal this
    run's ledger lines, and `output_folder_usd` the whole ledger. The record
    holds the PDF, the settings (no API key), the version and the times. `run()`
    returns the `RunResult` as written. The summary gives the status, the steps,
    the cost by step and the folder total, and the output files.
  - A failing answer then a rerun: the rerun has a new run ID and a `reused`
    step with no request, no transport, no cost this run and the same 9 review
    issues. The summary counts them by check (`rotation 8, languages 1`) and
    lists them.
  - `max_cost` stop: `BudgetExceededError`; `run.json` `stopped` with the error,
    the step `stopped` with `pdf_facts.json` only, nothing sent. One
    `max_cost_exceeded` warning (step `survey`, check `plan`, `allowed` false,
    `projected_usd` set) and one `PydelityWarning`. The summary says how to
    continue. A rerun with a higher `max_cost` completes and reuses the facts.
    With `allow_over_max_cost=True` the run completes and the warning has
    `allowed` true.
  - Failures: a provider rejection (`ProviderError`), a refusal (`SurveyError`)
    and a missing API key (`MissingApiKeyError`) each leave `run.json` `failed`
    with the error, the step `failed`, and a valid `pdf_facts.json`.
  - Warnings, each in `run.json` once with its code, step and details, as one
    `PydelityWarning` and one log line:
    - `other_pdf_in_folder` (no step, naming `run.json` and `pdf_facts.json`);
    - `damaged_output` for `pdf_survey.json` and for a damaged last `cost.jsonl`
      line;
    - `upload_fallback` (provider and upload error, step transport `request`);
    - `unpriced_model` (with the unpriced request counted);
    - `probe_unavailable` (the fact).
  - A cancelled `arun` during the model request: `CancelledError` reaches the
    caller, `run.json` is `interrupted`, the step `stopped`, and there is no
    `pdf_survey.json`.
  - The command: `--yes` over `max_cost` completes and prints the warning once,
    with no Python warning output. Without `--yes` and no terminal it exits 3
    with `run.json` `stopped`. Ctrl+C during the model request exits 130 with
    `run.json` `interrupted` and logs `Run interrupted` and `Interrupted`.
- `dev011_offline.py` (30 of 30), `dev010_check.py` (30 of 30) and
  `dev001_rework_check.py` (12 of 12) still pass.
- Real runs from the command line (`dev012_real.py`, `claude-opus-5-5`, a config
  file setting `check_retries` 0 and `max_output_tokens` 16,000; $0.25 recorded
  in total):
  - completion: exit 0, `run.json` `completed` by upload; `run_usd`, `by_step`
    and the folder total all equal the one ledger line ($0.19);
  - budget stop: `--max-cost 0.01` without a terminal logged the
    `max_cost_exceeded` warning and the "pass --yes" message, then exited 3 with
    `run.json` `stopped`, nothing spent and the hint to run again. The rerun
    with `--max-cost 1 --yes` reused the facts and completed ($0.06);
  - injected error: `--model anthropic:claude-does-not-exist-1` logged the
    `unpriced_model` warning, then exited 1 with `run.json` `failed` and the
    provider's message;
  - Ctrl+C four seconds into the model request: exit 130, `run.json`
    `interrupted`, the step `stopped`, no `pdf_survey.json`. The interrupted
    request has no `cost.jsonl` line, since no response came back; the provider
    may still bill it.

**Implementation Notes**

- Files approved by the user (2026-11-18): `src/pydelity/pipeline/` with
  `schemas.py` and `runner.py` (plus its `__init__.py`), and changes to
  `src/pydelity/api.py`, `src/pydelity/cli.py`,
  `src/pydelity/utils/coroutines.py`, `src/pydelity/surveying/facts.py`,
  `src/pydelity/surveying/survey.py`, `src/pydelity/providers/uploads.py`,
  `src/pydelity/costs/budget.py` and, for the codes below,
  `src/pydelity/errors.py`.
- `warn` now takes the warning's code and details. It logs the warning, issues
  the `PydelityWarning` and adds it to the run's list (`collect_warnings`, a
  context variable, so tasks PydanticAI starts add to the same list). The
  modules' own `_warn` helpers are gone. The `max_cost_exceeded` item gets
  `allowed` after the decision.
- Warnings issued before the survey step (only `other_pdf_in_folder`) have no
  step; the rest belong to the survey step, which covers the facts.
- `run.json` is written at the start (`running`, no steps) and at the end. An
  interrupted step is recorded as `stopped`. `error` is the error's type and
  message as one string.
- `run_survey` also returns how the last request carried the PDF, for the step's
  `pdf_transport`.
- The run's summary is logged by the runner, so Python callers who enable
  pydelity's log see it too. It lists the first 10 review issues.
- The command hides Python's own output for `PydelityWarning`, since each
  warning is already logged, and exits 130 on Ctrl+C.
- At the user's request (2026-11-18), the codes that are part of pydelity's
  contract live in `src/pydelity/errors.py`: `WarningCode`, the `run.json`
  warning codes, and `ExitCode`, an `IntEnum` of the command's exit status
  (`COMPLETED` 0, `FAILED` 1, `INVALID_INPUT` 2, `STOPPED` 3, `INTERRUPTED`
  130). The command and `utils/coroutines.py` import them from there. After the
  move, lint, `just test`, `dev012_offline.py` (26 of 26) and
  `dev011_offline.py` (30 of 30) pass.

### DEV-013 — HTML report

`Status`: `DONE` `Depends On`: `DEV-012` `Acceptance`: `AC-020`

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

Evidence, 2026-11-18, on `a5a1c06` plus the uncommitted DEV-012 and DEV-013
changes (macOS arm64, Python 3.13.9). No model was called and nothing was spent.

- `just lint-python` (Ruff check and format, ty, interrogate 100%), `just test`
  (2 passed) and the `_short_name` doctest pass. The built wheel contains
  `pydelity/report/report.css`, and so does the strict editable install.
- Scratchpad `dev013_check.py`, 26 of 26 checks, with no API key set:
  - Copies of four real-run folders from DEV-011 were run again with their own
    settings: the W-9 on Anthropic and on OpenAI, the CAPS extract, and the W-9
    with a forced check failure. Each run reused the survey, completed, and
    logged `Report written` and `report.html` in its summary. Each folder has
    one 1000-pixel-wide JPEG per page and a manifest with the PDF's SHA-256.
  - Each report is well formed, with no `script` element, no event-handler
    attribute and no external URL, and every image it names exists. It holds, in
    order, the cost and review sections, then the profile and facts sections
    (the facts begin with the summary lines), then one page card per page. The
    W-9 reports draw 20 or 21 region boxes and 23 form-field boxes; the CAPS
    report draws 8 region boxes. The report with the forced failure lists its
    review issue.
  - A failed run (a model that needs the API key, which is not set) wrote a
    report with the error, the facts and the pages, and no profile.
  - Images: after one image was deleted, only that image was rendered again. A
    manifest naming another PDF made every page render again.
  - Hostile strings put into a saved survey (a label and a region named
    `<script>alert("label")</script>`, an `" onmouseover="` description, an
    `<img ... onerror=...>` note and a `</style><script>` note) appear in the
    report as text. The report has no `script` element, no event handler and no
    image but the page images.
- `dev012_offline.py` (26 of 26) passes, with every run writing `report.html`:
  completed, reused, failed (provider error, refusal, missing API key), stopped
  and interrupted (a cancelled `arun` and Ctrl+C in the command).
- Opened from disk in the browser pane: the W-9 report's header, cost, review
  and facts sections and its page cards read as intended, with the form-field
  boxes over page 0. The pane shows a local file as a snapshot without its
  images, so the images were checked on disk instead. The CAPS page images show
  each page as displayed, portrait with the table turned. Copies of five reports
  are in the git-ignored `pydelity-output/dev013-preview/`.

**Implementation Notes**

- Loads the Developer HTML and CSS styles.
- Files approved by the user (2026-11-18): `src/pydelity/report/` with
  `__init__.py`, `schemas.py`, `images.py`, `html.py` and `report.css`, and a
  change to `src/pydelity/pipeline/runner.py`. The user also approved adding
  `[tool.setuptools.package-data]` to `pyproject.toml`, since setuptools
  packages only Python modules and `py.typed` otherwise.
- Page images are JPEG (quality 80), about 280 KB per W-9 page. Each is written
  to a temporary file and then moved into place, and leftover temporary files in
  `report/pages/` are removed. When the manifest is missing, unreadable or names
  another PDF, the old images are deleted and every page is rendered again.
- `report.html` holds the run header, cost, warnings, review issues, profile,
  facts and page cards. Region boxes are solid and form-field boxes dashed, each
  with its label written in the box, so the two differ by more than color.
  Form-field boxes show the field's short name, and the facts table gives the
  full one.
- The run writes the report after the final `run.json`, off the event loop, for
  every status. If the report cannot be written, the run logs an error and ends
  as it would have.
- The user saw region boxes that did not match the page (2026-11-18). The report
  draws each box where `pdf_survey.json` puts it: in the browser pane each box
  sat at its stored fraction of the page image, and PyMuPDF drew the same boxes
  in the same places. Form-field boxes, measured from the PDF, line up with the
  form. Region boxes are the model's estimates and are often off: round
  fractions on the W-9 (its `Sign Here` box covers the certification paragraph),
  and on page 2 of the CAPS extract a box over the left 30% of a table that
  spans the page. With the user's approval, the caption under each page now says
  the region boxes are where the model placed them and can be off, and that the
  form-field boxes are measured from the PDF. Making region boxes accurate
  (snapping them to measured content, or a check that rejects boxes over empty
  areas) is a design question for the Architect when a later step that uses
  regions is designed.
- At the user's request (2026-11-18), the six schema versions moved into the new
  `src/pydelity/schema_versions.py`: `FACTS_SCHEMA_VERSION`,
  `LEDGER_SCHEMA_VERSION`, `MANIFEST_SCHEMA_VERSION`, `RUN_SCHEMA_VERSION`,
  `SURVEY_SCHEMA_VERSION` and `UPLOADS_SCHEMA_VERSION`. The schema modules no
  longer define them, and the modules that write the files import them from
  there. `PROBE_VERSION` and `PROMPT_VERSION` stay next to the probe and the
  prompt, which they must follow. After both changes, lint, `just test`, the
  doctests, `dev010_check.py`, `dev011_offline.py`, `dev012_offline.py` and
  `dev013_check.py` (26 of 26) pass.

### DEV-014 — Python API

`Status`: `DONE` `Depends On`: `DEV-012, DEV-013` `Acceptance`:
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
forms give the same results, errors and warnings. Inside a running event loop
(Jupyter, async code) a sync function raises `RuntimeError` naming the `a`
function to await, writes nothing and leaves no un-awaited coroutine. `measure`
prepares the output folder and writes or reuses `pdf_facts.json`, returning
`PdfFacts`, with no API key or model call. `survey` writes `pdf_facts.json` and
`pdf_survey.json` and returns `PdfSurvey`. `run` returns a `RunResult`
(`output_dir`, `record`, `facts`, `survey`, `ledger`). `load(output_dir)`, sync
only, reads a folder back into a `RunResult` with missing parts as `None` and
raises `OutputError` for a missing folder or a corrupt file. Cancelling
`asurvey` or `arun` is handled like Ctrl+C. Every function validates the whole
configuration, never prompts or reads stdin. The root re-exports all of them
with `Config`, the result models, `CostEstimate`, the errors and
`PydelityWarning`; import stays free of side effects.

From Python: the sync functions work in scripts, the `a` functions work
anywhere, including Jupyter with top-level `await`, and
`pydelity.load("<output folder>")` reads a run back anywhere; the command line
is unchanged.

**Self-Check**

Real calls of every function in both forms; each sync function inside a running
event loop raises `RuntimeError` naming its `a` function and writes nothing; two
`asurvey` calls on different folders at once; `measure` and `load` with no API
key; cancelling `arun`; import with an empty environment prints nothing;
`just lint`.

Evidence, 2026-11-18, on `f339afa` plus the uncommitted DEV-014 changes (macOS
arm64, Python 3.13.9).

- `just lint-python` (Ruff check and format, ty, interrogate 100%) and
  `just test` (2 passed) pass.
- Scratchpad `dev014_offline.py`, 25 of 25 checks, with no API key set and a
  stand-in model (PydanticAI's `FunctionModel` inside `LedgerModel`):
  - `measure` writes only `pdf_facts.json` and returns facts equal to it. A
    second call reuses the file without rewriting it, and `ameasure` returns the
    same facts.
  - `estimate` on a new folder writes nothing, not even the folder, and returns
    one survey step of up to 3 requests. `aestimate` returns the same estimate.
    Where the survey would be reused, the step is `reused`, nothing is to be
    spent, and the folder's spend is counted.
  - `survey` writes `pdf_facts.json`, `pdf_survey.json`, `cost.jsonl` and
    `uploads.json`, but no `run.json` or report, and returns the survey as
    saved. `asurvey` on the same folder reuses it and sends nothing.
  - `load` on a completed run's folder equals what `run` returned, with an
    absolute or a relative path, and equals what `arun` returned after a rerun.
    On a folder only `measure` wrote, it returns the facts, and `None` or an
    empty ledger elsewhere. It raises `OutputError` for a missing folder, an
    empty folder, a corrupt `pdf_survey.json` (naming the file) and a `run.json`
    of schema 2.0.
  - Inside a running event loop, `measure`, `estimate`, `survey` and `run` each
    raise `RuntimeError` naming the `a` function to await. They write nothing
    and leave no "never awaited" warning, and `load` works there.
  - Two `asurvey` calls on different folders run at once, and their model
    requests overlap.
  - While `ameasure` measured the W-9 instructions (about 190 ms), the longest
    pause of the event loop was 32 to 45 ms, against 180 to 204 ms for the probe
    run on the loop itself. The probe runs on a worker thread, but PyMuPDF holds
    the GIL during some calls, so the loop gets short pauses rather than none.
  - `measure` and `ameasure` give the same `PydelityWarning` for a damaged
    `pdf_facts.json`.
  - `import pydelity` with an empty environment exits 0 and prints nothing. The
    package root exports the API, the result models, `Config`, `CostEstimate`,
    the errors and `PydelityWarning`.
- `dev011_offline.py` (30 of 30), `dev012_offline.py` (26 of 26, which also
  covers a cancelled `arun`), `dev013_check.py` (26 of 26) and
  `dev001_rework_check.py` (12 of 12) still pass.
- Real calls (`dev014_real.py`, `claude-opus-5-5`, one request of at most 10,000
  output tokens per survey; $0.41 recorded in total):
  - `measure` and `ameasure`, then `estimate` and `aestimate`, on a new folder
    gave equal results and wrote only `pdf_facts.json`. The estimate was about
    $0.36, at most $0.40.
  - Two `asurvey` calls at once, on the W-9 and the CAPS extract, finished in 24
    seconds ($0.19 and $0.17). They wrote no `run.json` or report, and the CAPS
    survey has rotation 90 on pages 0-7.
  - `survey` on the W-9 folder reused the survey and spent nothing. `arun` there
    completed with the survey reused, wrote `run.json` and the report, and
    `load` equals what it returned.
  - `run` on a new folder completed with one request ($0.05, reading the PDF
    from the cache), and `load` equals what it returned.

**Implementation Notes**

- Files approved by the user (2026-11-18): changes to `src/pydelity/api.py`,
  `src/pydelity/__init__.py`, `src/pydelity/pipeline/runner.py` and
  `src/pydelity/surveying/facts.py`.
- The runner has a public function for each part: `run_measure`, `run_estimate`,
  `run_survey_step`, `run_pipeline` and `load_run`. `measure` and `survey`
  prepare the folder and warn about another PDF's files, as a run does, but
  write no `run.json` and no report.
- `estimate` uses the saved facts when they match and otherwise measures the PDF
  without saving (`measure_facts(save=False)`). It checks for a reusable survey
  without logging `Survey reused`. A reused step is logged as "the saved output
  would be reused".
- `load` checks each file's major schema version against `schema_versions.py`.
  `RunResult.output_dir` is the resolved folder in both `run` and `load`, so the
  two compare equal.

### DEV-015 — CLI

`Status`: `DONE` `Depends On`: `DEV-014` `Acceptance`:
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

Evidence, 2026-11-18, on `e9cb796` plus the uncommitted DEV-015 changes (macOS
arm64, Python 3.13.9).

- `just lint-python` (Ruff check and format, ty, interrogate 100%) and
  `just test` (2 passed) pass. `dev012_offline.py` (26 of 26) still passes.
- Scratchpad `dev015_offline.py`, 14 of 14 checks, with no API key. Runs that
  reach the model use the command with a stand-in model, and questions are
  answered through a pseudo-terminal. That check ran outside the sandbox, which
  allows no pseudo-terminals, and made no network calls.
  - `--version` prints `pydelity 0.0.1`, and `python -m pydelity --version`
    prints the same.
  - `--help` lists the options in the design's order, ending `--verbose`,
    `--quiet`, `--version`, with the default output folder and model shown.
  - Three invalid settings (`--max-cost -1`, `--language zz`,
    `--model nope:model`) give exit 2 and one error naming all three, with
    nothing written. No PDF gives exit 2 naming `pdf`. `--quiet` with
    `--verbose` gives exit 2.
  - No API key: exit 2 naming `ANTHROPIC_API_KEY`, with `pdf_facts.json` saved
    and `run.json` `failed`.
  - `--quiet` logs only WARNING lines, the `max_cost` warning among them.
    `--verbose` adds DEBUG lines with the settings and the prompt. The default
    level logs INFO lines, the summary and the report path.
  - Input that is not a terminal, without `--yes`: exit 3, "pass --yes",
    `run.json` `stopped`, nothing sent.
  - On a terminal: answering no exits 3 with nothing sent; yes completes. Over
    `max_cost`, the only question is the `max_cost` one: no exits 3, and yes
    completes with the warning recorded as allowed.
- Real runs of the command installed from a wheel in a fresh virtual environment
  (`dev015_real.py`, `claude-opus-5-5`, one request of at most 10,000 output
  tokens per run; $0.25 recorded):
  - `--version` and two invalid settings (exit 2, nothing written);
  - input that is not a terminal without `--yes`, and a terminal question
    answered no: both exit 3, `stopped`, nothing spent;
  - a terminal question answered yes: exit 0, completed, report written ($0.19);
  - `--yes`: exit 0, completed, with no PydanticAI banner and no Python warning
    output ($0.06).

**Implementation Notes**

- File approved by the user (2026-11-18): `src/pydelity/cli.py`.
- Rework at the user's request (2026-11-18), with
  `src/pydelity/pipeline/runner.py` also approved:
  - `--quiet` is gone. By default the command shows only warnings, errors, the
    cost estimate (with the folder's spend and `max_cost`) and the end-of-run
    summary. The runner marks those lines with the loguru `extra` key
    `SUMMARY_LOG_KEY`, and the command's log filter lets them through.
    `--verbose` shows every message, progress and details included.
  - Every option has a short form: `-c` config, `-i` instructions, `-l`
    language, `-d` output folder, `-m` model, `-mc` max cost, `-o` overwrite,
    `-y` yes, `-v` verbose, `-V` version and `-h` help. Click reads `-mc` as one
    option before trying `-m` with a value, so `-m` and `-mc` work together.
  - The summary now says "1 request" rather than "1 requests".
  - Evidence: `dev015_offline.py`, 16 of 16 (outside the sandbox, for
    pseudo-terminals, with no network calls):
    - `--help` lists every short form and no `--quiet`, `-h` and `-V` work, and
      `--quiet` is an unknown option (exit 2).
    - By default only the estimate, the `max_cost` warning and the summary
      appear, with no progress or DEBUG lines. `--verbose` adds progress, the
      settings, the prompt and the report path.
    - `-o`, `-i`, `-l`, `-m` and `-mc` reach the run's settings, and `-d` sets
      the output folder.
    - The earlier checks (version, invalid settings, missing API key, piped
      input, questions on a terminal) still pass.

    Lint, `just test`, `dev012_offline.py` and `dev014_offline.py` pass too.
- The help text had lost its two defaults, because Typer reads `[default: …]` in
  help text as markup. They now use Typer's `show_default`, which prints
  `[default: (pydelity-output/<PDF name>)]` and
  `[default: (anthropic:claude-opus-5-5)]`. The model default comes from
  `DEFAULT_MODEL`.
- The rest of the design's contract was already in place from DEV-001, DEV-007,
  DEV-011 and DEV-012: the options, the questions and the mid-run `max_cost`
  question, the provider's message printed unchanged, exit codes 0, 1, 2, 3 and
  130, warnings printed once as they occur, and the summary with review issues
  counted by check.

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

- The user's run on a second PDF of their own (142 pages, $1.91, 2026-11-18)
  showed why every survey so far needed a second request. The facts summary
  names only the 3 most frequent repeated lines, but check C5 needs every
  repeated line ID accounted for (58 here). The model could not classify lines
  it could not see, so its first answer failed C5, and it learned the missing
  texts from the retry message. With the user's approval, the text sent with the
  PDF now lists every repeated line (ID, text, page count, band; the probe keeps
  at most 200), and the artifacts paragraph of the prompt says so.
  - Changed: `src/pydelity/surveying/prompts.py` (`survey_pdf` takes
    `repeated_lines`), `src/pydelity/surveying/llm.py` and
    `src/pydelity/pipeline/runner.py` (the prompt length for the estimate). On
    that PDF the list adds about 5,600 characters (about 1,400 tokens).
  - Checks: lint, `just test`, the doctests, `dev010_check.py` (still no
    document-type words in the prompt), `dev011_offline.py` (31 of 31, now
    checking that every repeated line is in the request text),
    `dev012_offline.py` and `dev014_offline.py` pass.
  - Not changed: the same run showed that this PDF's page labels number pages
    0-4 (cover to a blank page) 1-5, and the back cover 137, though those pages
    print no number. The design takes the page label as the printed number
    whenever labels exist, and check C4 makes the model agree. Taking printed
    numbers from the page text, with labels as a separate fact, would change the
    design and the facts schema; it is left for the Architect.
- The user's own run on a 94-page PDF of their own (2026-11-18, $1.35) found two
  general gaps. The fixes changed `src/pydelity/surveying/probe.py` and
  `src/pydelity/surveying/prompts.py`, with the user's approval, and hold no
  document-specific rules:
  - The probe read a page label as a page number only when the whole label was a
    number. PDF page labels are a prefix plus a number, so "Page 12" gave no
    number and the text on the page was never checked. The probe now reads the
    number at the end of a label (`Page 12`, `A-iv`, `Part II`). When a label
    has no number, it looks for the number printed on the page.
  - The model saw printed page numbers that the facts had missed, but answered
    "no numbers" because the prompt asked it to agree with the facts. It also
    left out the rotation of pages whose text is inside images, which the facts
    cannot measure. The prompt now says the facts can miss things such as text
    inside images or page numbers, that answers must agree with what the facts
    did measure, and to describe what is seen where they measured nothing. For
    rotation it names pages whose text is inside images; for page numbering, to
    give the numbers seen even where the facts found none.
  - At the user's request, `PROBE_VERSION` and `PROMPT_VERSION` stay at 1 until
    the first release, so a rerun needs `--overwrite` to measure and survey
    again.
  - Checks:
    - Measured before and after on the nine test PDFs and the user's two PDFs,
      only the user's 94-page PDF changed: its printed numbers now run with
      offset 1 on all 94 pages. Every other fact of every PDF is unchanged.
    - With labels that have no number, set on a copy of the W-9 instructions,
      the probe now finds the printed numbers it finds without labels.
    - The label examples (`12`, `Page 12`, `Page12`, `A-iv`, `Part II`, `Cover`,
      `Appendix`, Arabic-Indic digits) read as expected.
    - Lint, `just test`, the doctests, `dev010_check.py` (no document-type words
      in the prompt), `dev011_offline.py` and `dev012_offline.py` pass.
- A deviation from the design's CLI contract, approved by the user on
  2026-11-18: the command has no `--quiet`. By default it shows warnings,
  errors, the cost estimate and the summary, and `--verbose` shows everything.
  Every option also has a short form, `-mc` for `--max-cost` among them.
- Deviations from the design's decision 2, approved by the user on 2026-11-18:
  the survey prompt is built in a function that returns a `PromptPair` rather
  than kept in string constants, and the report's stylesheet ships as package
  data (`report/report.css`, through `[tool.setuptools.package-data]`) rather
  than as a string constant. The report's HTML is still built in Python.
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
- Step folders (user decision, 2026-11-17): each pipeline step gets one folder
  directly under `src/pydelity/`, named with an "-ing" word so it never collides
  with a public API function (a verb such as `survey` or `run`): `surveying/`
  for step 1, and later `extracting/`, `verifying/`, `assembling/`, `proposing/`
  and `projecting/`. Each step folder holds its own modules (`schemas.py`,
  `probe.py`, `prompts.py`, `validators.py` and so on), so nothing is more than
  two levels deep; this replaces the `steps/survey/` sketch above. DEV-005's
  files: `surveying/{__init__,schemas,probe,facts}.py`, `api.py` and
  `.gitignore`.
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

### Suspended Assignment 5

`Recovery Frame`: `1` `Recovery Reason`:
`User rework: check BCP-47 language tags (the languages setting and survey check C7) with the langcodes library, a new runtime dependency, instead of a hand-written pattern.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`scope a938118 and design 2e96832; DEV-001 to DEV-003 committed (121f87d, ed70f71, 274b41a); DEV-004 done but uncommitted in the working tree`
`Next Action`:
`Reconcile DEV-004 (replace the BCP-47 pattern in config/schemas.py with langcodes and add the dependency) and DEV-010 (C7) with the corrected design, then list DEV-005's files for the user's review.`

Restored on the `RESUME` from `ARCHITECTING` (design `117eafe`, decision 15) and
reconciled without changing the plan's steps or their order: DEV-004 is reopened
to check language tags with `langcodes` and keep them in standard form, with the
`languages[n]` error naming; DEV-010's C7 and DEV-011's language merge follow
decision 15. The change is the user's own request and touches no other step, so
the plan stays approved.

### Suspended Assignment 6

`Recovery Frame`: `1` `Recovery Reason`:
`User rework: sync Python API functions use asyncio.run only; called while an event loop is already running (Jupyter, async code), they raise an error saying to await the async version instead of running the coroutine on a worker thread.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`scope a938118 and design 117eafe; DEV-001 to DEV-005 committed (DEV-005 e2c02cf); DEV-007 done and a plain-language pass over the package's docstrings and comments (wording only, lint and tests pass) both uncommitted in the working tree`
`Next Action`:
`Reconcile DEV-001 (reduce utils/coroutines.py and the sync wrappers to the corrected design, dropping the worker thread and its warning replay; keep run_in_daemon_thread for terminal questions) and any other step the corrected design changes, then list DEV-008's files for the user's review.`

Restored on the `RESUME` from `ARCHITECTING` (design `76e25f0`, decision 14) and
reconciled without changing the plan's steps or their order. DEV-001 is
reopened: its helper takes the async function and its arguments, so it can check
for a running loop before the coroutine exists, and the CLI calls `asyncio.run`
directly. DEV-014's outcome and self-check now expect `RuntimeError` from the
sync functions inside a running loop. DEV-007 already uses only
`run_in_daemon_thread` and `warn`, which stay. The change is the user's own
request, so the plan stays approved; as with every step, the user reviews
DEV-001's files before the rework starts.

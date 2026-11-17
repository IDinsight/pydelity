<!-- STANDARDS
Artifact: ARCHITECTURE
Cycle: build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c
-->

# Technical Design: pydelity survey step and first working release

Design mode: `FOUNDATION`. This is pydelity's first code. It fixes the package
layout, the run framework (configuration, output folder, cost ledger, resume,
review list, report) and the release and docs foundations that steps 2–6 will
inherit, and builds step 1 (survey) on them.

## Context

- Scope:
  `.standards/docs/scope/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c.md`
  (AC-001 to AC-036). Project context: `.standards/CONTEXT.md`. Design inputs:
  `artifacts/design_brief.md` (step 1 design points, cross-cutting directions,
  known source defects) and `artifacts/next_cycle_inputs.md`.
- Baseline: `src/pydelity/` holds only a docstring module and `py.typed`; no
  runtime dependency, CLI or console script. Tooling is just, prek, uv (strict
  editable install), Ruff, ty, interrogate (100%), pytest with pytest-randomly,
  zizmor, Prettier and markdownlint over every Markdown file, Dependabot, and
  release-please (manifest `0.0.1`, no tags or GitHub releases). The ruleset on
  `main` requires the checks "Lint and test" and "TruffleHog secret scan".
- Conventions to keep: alphabetical `pyproject.toml` tables, keys and lists;
  justfile recipes alphabetical after `default`; dev tools pinned exactly,
  runtime dependencies as minimum versions; one pinned version per tool, with
  "Kept by hand" comments where Dependabot cannot update; actions pinned by SHA,
  least-privilege permissions, `persist-credentials: false`, per-workflow
  `concurrency`, `timeout-minutes` on every job; NumPy docstrings; tooling must
  work where STANDARDS is not installed.
- User decision recorded 2026-11-17 during this design: the survey's PDF library
  is **PyMuPDF**, as in KGForEdGlobal, accepting that it is AGPL-3.0 (or
  Artifex's commercial licence). pydelity's own licence stays MIT.
- No project references exist under `.standards/project-references/`; none is
  named for downstream roles.

## Decision

1. **Library first, thin CLI.** All behaviour lives in the `pydelity` package
   behind a small public Python API (`run`, `survey`, `estimate`, `Config`,
   result models, exceptions). The Typer CLI only parses options, shows the
   estimate, asks for confirmation, calls the API and prints a summary.
   Importing pydelity reads no environment, builds no settings and emits no log
   output: `pydelity/__init__.py` calls `loguru.logger.disable("pydelity")` and
   the CLI enables it.
2. **Stack.** Runtime dependencies (minimum versions, written by `uv add`):
   `pydantic`, `pydantic-settings[yaml]`, `pydantic-ai-slim[anthropic,openai]`
   (the slim distribution, so installs pull only the two supported providers; it
   brings `genai-prices`, whose bundled price data PydanticAI's cost calculation
   uses), `loguru`, `typer`, `pymupdf`. No templating library: prompts and the
   HTML report template are Python string constants, so the wheel needs no
   package data beyond `py.typed`.
3. **Models.** A model setting is `<provider>:<model-id>` with provider
   `anthropic` or `openai`; any other provider is an invalid setting. Default:
   `anthropic:claude-opus-5-5` (1M context, PDF input up to 600 pages). OpenAI
   models run through PydanticAI's Responses model. All model construction goes
   through one factory (`build_model`) that returns the provider model wrapped
   in a ledger wrapper (decision 6). Structured output must not depend on forced
   `tool_choice` (Claude Opus 5.5 rejects `any`/`tool` with a 400): use
   PydanticAI `NativeOutput` (provider structured outputs) where the pinned
   PydanticAI supports it for the provider, otherwise `PromptedOutput`, as
   KGForEdGlobal's `model_registry.py` already does for Anthropic. Thinking:
   Anthropic models run adaptive thinking with an explicit `effort`; OpenAI
   models get `reasoning_effort`. pydelity's `effort` setting is `low`, `medium`
   or `high` (default `high`) and maps to each provider.
4. **The PDF goes to the model whole, uploaded and kept for reuse, with an
   in-request fallback.** PDF transport policy (user decisions, 2026-11-17),
   applied to every provider: use the provider's file upload API when it has
   one, and fall back to sending the PDF inside the request when the upload path
   fails; a provider without uploads gets the PDF inside the request; a provider
   that offers neither cannot be used with pydelity. Each provider's transports
   are recorded once, at provider level. This cycle builds both paths for
   Anthropic and OpenAI.

   The survey uploads the PDF with the provider's Files API (Anthropic; OpenAI
   with purpose `user_data`) and sends one user message that references it
   through PydanticAI's `UploadedFile`, plus a text part with the measured facts
   summary and any user instructions and languages. No splitting. Retries
   reference the same file instead of resending the bytes, and Anthropic accepts
   up to 500 MB per uploaded file against 128 MB for a PDF sent inside the
   request.

   Fallback: when the upload path fails, the step sends the PDF inside the
   request instead, as PydanticAI `BinaryContent(media_type="application/pdf")`,
   for the rest of that step run. The upload path has failed when the upload
   call fails after the provider SDK's own retries (connection error, timeout,
   rate limit, server error, or any other error response except an
   authentication failure), or when a re-upload after "file not found" fails. An
   authentication failure stops the run, since the in-request call would fail
   the same way. Errors from the model request itself never trigger the
   fallback. The fallback is recorded as a warning in `run.json` (with the
   upload error) and the step's `pdf_transport` becomes `request`; nothing is
   written to `uploads.json`. If the PDF is over the model's in-request size
   limit, the fallback is impossible and the step fails with a `SurveyError`
   naming the upload error, the in-request limit and the PDF's size. Prompt
   caching applies the same way on both paths.

   Uploads are kept, not deleted. Each upload sets the provider's expiry from
   `advanced.uploads.expiry_hours`, which defaults to the provider's maximum
   (Anthropic: 90 days); a value outside the provider's allowed range is an
   invalid setting. The output folder's `uploads.json` records each upload, and
   any later run or step that needs the same PDF on the same provider reuses it
   while it has at least one hour left. A file the provider no longer has (for
   example after expiry or under another API key) is uploaded again and the
   record replaced. pydelity never deletes uploads; they expire at the provider.
   Uploads are free and are not ledger entries. Nothing is uploaded before the
   CLI's confirmation and the budget check.

   In the step designs so far, only the survey sends the whole PDF: steps 2–6
   send page images, crops and text that pydelity renders locally. Keeping the
   upload saves re-uploading when the survey reruns (changed instructions,
   settings or `overwrite`) and leaves the file available to later steps whose
   designs choose to use it.

   Prompt caching is separate from the upload: it depends on each retry
   repeating the same prompt prefix. Anthropic caches only after an explicit
   cache breakpoint, so the survey sets one after the PDF and the facts summary;
   OpenAI caches long repeated prefixes automatically. Check-failure retries
   then read the PDF's tokens from cache.

5. **Checks run in a PydanticAI output validator.** Every model answer is
   checked by deterministic Python checks against the measured facts. While
   retries remain, a failed check raises `ModelRetry` with a message naming each
   failure and the measured values. On the final allowed attempt
   (`RunContext.last_attempt`), the validator accepts the answer and records
   each still-failing check as a review issue. `advanced.survey.max_retries`
   (default 2) sets `output_retries`. An answer that never parses into the
   proposal schema exhausts PydanticAI's retries and fails the survey.
6. **Cost ledger by wrapping the model.** `LedgerModel`, a PydanticAI
   `WrapperModel`, wraps every model pydelity builds. Before each request it
   asks the budget guard whether the request's upper-bound cost fits under
   `max_cost`; after each response it prices the response's usage and appends
   one line to the output folder's `cost.jsonl`. This records every request,
   including retries, for every future step without per-step code. Each response
   is priced with PydanticAI's own cost calculation (`ModelResponse.cost()`,
   backed by `genai-prices`); pydelity keeps no price table. Prices set for a
   model under `advanced.models` replace that calculation for the model; a model
   `genai-prices` does not know and that has no override is unpriced.
   genai-prices' runtime price updates stay off, so pydelity makes no network
   calls other than to the model providers.
7. **Output folder is the unit of resume and spend.** One folder per PDF run
   holds `pdf_survey.json`, `run.json`, `cost.jsonl`, `uploads.json`,
   `report.html` and `report/`. Every JSON and HTML file is written atomically
   (temp file in the same folder, flush, `fsync`, `os.replace`) and validated on
   load. Each step output stores a fingerprint of its inputs; a valid output
   with a matching fingerprint is reused, anything else is regenerated.
8. **Profile vocabulary.** Item `kind`: `text`, `list`, `table`, `figure`,
   `field`, `formula`, `code`. Item `role`: `heading`, `body`, `caption`,
   `footnote`, `artifact`, `navigation`, `aside`. A value is in these lists only
   when a later step must treat it differently; per-PDF detail belongs in
   labels. `code` covers code and other preformatted text: its whitespace and
   line breaks are kept exactly, and a cross-page join is a newline with no
   dehyphenation. Boxes become containers in a later step, not a kind or role.
   These enums are the page-schema contract steps 2–6 build on; changing them
   changes the output `schema_version`.
9. **Docs site follows IDinsight/standards.** Astro with Starlight in `docs/`,
   pnpm, a custom built-HTML link checker, a versioned combined build from
   release tags (`scripts/build-versions.mjs` pattern, latest at the root, each
   release at `/v/<version>/`, version selector), deployed to GitHub Pages only
   once the package version on `main` has its tag. Reference pages for
   configuration, CLI, Python API and output files are generated from the code.
10. **Release.** release-please stays as configured. A new `release.yml`,
    triggered by release-please's GitHub release, builds the sdist and wheel,
    checks them with `twine check --strict` and publishes with PyPI Trusted
    Publishing through `pypa/gh-action-pypi-publish` in a `pypi` environment.

### Reuse from KGForEdGlobal

KGForEdGlobal has no survey step, so reuse is limited to infrastructure. Port
and adapt, without changing KGForEdGlobal:

- `utils/pdf.py` `compute_doc_key` → pydelity's PDF SHA-256 helper (full 64-hex
  digest, the later `doc_key`).
- `model_registry.py` → the models component: per-provider settings (Anthropic
  adaptive thinking plus effort, OpenAI Responses reasoning effort) and the
  per-provider output wrapping. Replace its hand-kept adaptive-thinking model
  set with catalog data (decision 3).
- `page_ir_extraction/agents.py` → the agent pattern: `Agent` with an output
  validator raising `ModelRetry` with Python check messages.
- Superseded rather than ported: `AgentUsageBucket` (tokens only; replaced by
  the per-request ledger with money) and `write_to_json` (not atomic, a listed
  defect; replaced by the atomic writer). No page-extraction validator, prompt
  or constant is ported: none applies to the survey, and several carry the
  listed defects (left-to-right reading order, English word lists).

## Acceptance Coverage

- `AC-001`: The survey probe and the `facts` section of `pdf_survey.json` under
  **Interfaces and Contracts**; measurement rules under **Technical Acceptance
  Criteria**.
- `AC-002`: Model-facing proposal schema and the stored `profile` section, the
  `kind`/`role` enums (decision 8), Python-owned `other` label.
- `AC-003`: Checks C1–C7, the output-validator retry rule (decision 5), review
  issues for checks still failing after retries.
- `AC-004`: User instructions and languages flow into the prompt and the stored
  profile after the checks; no setting disables a check.
- `AC-005`: Probe measurement rules; committed test PDF fixtures (Build Plan
  step 2). Correctness evidence is Tester's.
- `AC-006`: Vocabulary and prompt constraints under **Technical Acceptance
  Criteria**; checks and measurements use Unicode properties, never word lists.
- `AC-007`: CLI positional `PDF`; provider keys read at run time from
  `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`.
- `AC-008`: `Config` model, JSON/YAML loading, precedence rule.
- `AC-009`: Validation before any model call; error formatting naming every
  invalid setting.
- `AC-010`: Public API; import-time rules (decision 1).
- `AC-011`: Model factory and provider settings (decision 3).
- `AC-012`, `AC-013`: Model catalog with PDF limits, `advanced.models`
  overrides, the input-limit check and unknown-model warning.
- `AC-014`: `LedgerModel`, `cost.jsonl`, per-step and total cost in `run.json`
  and the CLI summary.
- `AC-015`: `estimate()`, CLI confirmation flow, `--yes`, non-interactive stop;
  the Python API has no prompt.
- `AC-016`: Budget guard over the folder's whole ledger, checked before every
  request; stop leaves resumable state.
- `AC-017`: Survey fingerprint and reuse rule; `overwrite`.
- `AC-018`: Atomic writes, temp-file cleanup, validate-on-load, interrupt
  handling.
- `AC-019`: Review issue contract in `run.json`; CLI end-of-run summary.
- `AC-020`: `report.html` and `report/pages/` contract.
- `AC-021`: Test seams: provider base URLs, the test environment guard, the
  shared mock provider server and canned responses.
- `AC-022`: CI job layout with the "Lint and test" gate job.
- `AC-023`, `AC-024`: `just build`, wheel smoke script and the cross-platform
  wheel job; `twine check --strict`.
- `AC-025`: Package metadata decisions (description, classifiers, URLs). The
  README text is Documenter's.
- `AC-026`: `release.yml`.
- `AC-036`: release-please configuration and the first-release rule under
  **Technical Acceptance Criteria**; the squash-merge title rule for the release
  procedure.
- `AC-027`, `AC-028`, `AC-029`, `AC-030`: Docs site, link checker, versioned
  build, docs workflow, pins and Dependabot.
- `AC-032`: Generated reference pages and their staleness check.
- `AC-031`, `AC-033`, `AC-034`: No architectural impact beyond the recipes,
  generated reference and public interfaces fixed here; satisfaction depends on
  Documenter's pages and README and on Tester/Reviewer evidence that examples
  match behaviour. Docs pages are `.md` (decision 9 constraints).
- `AC-035`: No architectural impact — the user's review of real runs with their
  own API keys, after implementation and verification.

## Components

**File and folder names are the user's decision (2026-11-17).** This design
fixes components, responsibilities, contracts and dependency direction, not
module, file or folder names. Before creating or renaming any file or folder,
Developer proposes the names and layout (in the development plan, and again
before each step) and waits for the user's sign-off. Every new path named in
this design is a candidate only. The user's general guidance, to apply where it
fits rather than as a rule: group code by feature; a feature folder can hold its
own `schemas.py` and `utils.py`; general helpers shared across features go in
`src/pydelity/utils/`. Fixed names are only external contracts: the `pydelity`
import package and command, the public API names, the output files named in
**Interfaces and Contracts**, and existing repo files.

Components, in dependency order (each may use only those after it; any component
may use the errors component; nothing uses the entry points):

- **Entry points** — package root (public API re-exports, `__version__` from
  `importlib.metadata`, `logger.disable("pydelity")`, no file, network or
  environment access at import); `python -m pydelity`; the Typer CLI (single
  root command); the synchronous API functions `run`, `survey`, `estimate`.
- **Run orchestration** — output folder, `run.json`, step sequencing, review
  list, warnings, interrupt handling, calling the report.
- **Survey step** — facts schemas and the `kind`/`role` enums, proposal and
  profile schemas, `PdfSurvey`; the PyMuPDF probe; the generic prompt and
  `PROMPT_VERSION`; checks C1–C7; the agent, output validator, merge,
  fingerprint and reuse.
- **Report** — `report.html`, page images and their manifest.
- **Configuration** — `Config` and `AdvancedConfig`, file loading, precedence,
  error formatting; `ProviderEnv` (pydantic-settings, environment only, built
  per run).
- **Costs** — ledger entry and `CostEstimate` schemas, the ledger, pricing
  (PydanticAI's cost calculation plus `advanced.models` overrides), the
  estimate, the budget guard.
- **Models** — the catalog (provider, PDF limits with source URL and date,
  context window, PDF tokens-per-page estimate, effort mapping, output mode) and
  the input-limit check; `build_model`, provider settings and `LedgerModel`;
  provider-level facts (PDF transports, upload expiry range); Files API upload,
  reuse and the `uploads.json` record; the in-request fallback.
- **General utilities** — atomic write, validated load and temp cleanup (UTF-8
  for every text read and write); opening a PDF (SHA-256, page count, size,
  `PdfError`); canonical-JSON fingerprints.
- **Errors** — `PydelityError` and subclasses, `PydelityWarning`.

Shared components (configuration, costs, models, utilities) never use run
orchestration or a step. Later steps add step components beside the survey.

Repo-level components: a reference-docs generator script, a wheel smoke-test
script, the Astro site under `docs/`, and CI, docs and release workflows under
`.github/workflows/`.

## Interfaces and Contracts

### Configuration

- File: optional, `.json`, `.yaml` or `.yml` by extension (any other extension
  is an error). Top-level keys only those below plus `advanced`; unknown keys at
  any level are invalid settings (`extra="forbid"`). Relative paths inside a
  config file resolve against the config file's folder; CLI and Python paths
  resolve against the current directory.
- Top-level settings (each also a CLI option of the same name, kebab-cased;
  `advanced` is config- or Python-only):
  - `pdf` (path; required from somewhere, must exist and be a file).
  - `instructions` (string or null).
  - `languages` (list of BCP-47 tags, syntax-validated; default empty).
  - `output_dir` (path; default `./pydelity-output/<pdf stem>/`).
  - `model` (`<provider>:<model-id>`; default `anthropic:claude-opus-5-5`).
  - `max_cost` (positive decimal USD or null; no default).
  - `overwrite` (bool; default false).
- `advanced.survey`: `max_retries` (0–5, default 2), `effort` (`low` | `medium`
  | `high`, default `high`), `max_output_tokens` (default 32000),
  `request_timeout_seconds` (default 900).
- `advanced.uploads.expiry_hours`: integer hours or null (default null, meaning
  the provider's maximum). It must lie within the selected provider's allowed
  range (Anthropic: 1 to 2160 hours), checked with the other settings before any
  upload. It is not part of any fingerprint.
- `advanced.models.<provider:model-id>`: any of `max_pdf_pages`,
  `max_pdf_bytes`, `max_request_pdf_bytes`, `context_window_tokens`,
  `pdf_tokens_per_page`, `input_usd_per_mtok`, `output_usd_per_mtok`,
  `cache_read_usd_per_mtok`, `cache_write_usd_per_mtok`. Merged over the catalog
  entry for that model.
- Precedence: CLI options or Python keyword settings > config file > defaults.
  The CLI's `PDF` argument wins over the file's `pdf` (AC-008).
- Environment (`ProviderEnv`, read only when a run needs a provider):
  `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` as `SecretStr`. The key for the selected
  provider must be non-empty before any model call. pydelity loads no `.env`
  file; the provider SDKs' own `ANTHROPIC_BASE_URL` / `OPENAI_BASE_URL` are
  honoured (the test seam). `.template.env` is reduced to the two keys pydelity
  reads.
- Errors: `ConfigError` lists every invalid setting by dotted path
  (`advanced.survey.max_retries`) with the reason, collected in one pass
  (Pydantic errors plus file, path and key checks), raised before any model
  call.

### CLI

- `pydelity [PDF] [--config/-c FILE] [--instructions TEXT] [--language TAG]... [--output-dir DIR] [--model MODEL] [--max-cost USD] [--overwrite] [--yes/-y] [--verbose/-v | --quiet/-q] [--version]`.
  Console script `pydelity`, pointing at the CLI module's entry function.
- Flow: resolve and validate config → open the PDF, input-limit check → plan
  (which steps run or are reused) → if a model call is planned: print the
  estimate, spend so far in the folder and `max_cost`; stop if the budget guard
  rejects the first request; confirm (`--yes` proceeds; an interactive stdin
  prompts, default No; a non-interactive stdin stops with a message to pass
  `--yes`) → run → print the summary (status, cost this run by step, folder
  total, review issue count and the first issues with step, page and check,
  output paths, report path).
- Exit codes: `0` completed (review issues allowed); `1` failed (provider or
  model error, unexpected error); `2` invalid settings, a missing API key, an
  unreadable PDF or a PDF over the input limits; `3` stopped before spending
  (declined, needs `--yes`, budget, unpriced model with `max_cost`) or stopped
  by the budget mid-run; `130` interrupted.
- Logging: loguru to stderr at INFO, DEBUG with `--verbose`, WARNING with
  `--quiet`. User-facing warnings are printed regardless of level.

### Python API

- `run(pdf=None, *, config=None, **settings) -> RunResult` — the whole pipeline
  (this cycle: the survey), writes `run.json` and the report. `config` is a
  path, a `Config` or a mapping; `settings` uses the top-level setting names
  (`advanced` as a mapping).
- `survey(pdf=None, *, config=None, **settings) -> PdfSurvey` — step 1 only:
  writes `pdf_survey.json` and ledger lines, not `run.json` or the report.
- `estimate(pdf=None, *, config=None, **settings) -> CostEstimate` — no model
  call, nothing written.
- Never prompts. Problems raise `ConfigError`, `PdfError`, `InputLimitError`,
  `MissingApiKeyError`, `BudgetExceededError`, `SurveyError` (all
  `PydelityError`). User-facing warnings (unknown model limits, unpriced model,
  output folder holding another PDF's results) use `warnings.warn` with
  `PydelityWarning` and are also recorded in `run.json`.
- Synchronous functions must also work when an event loop is already running
  (Jupyter), for example by running the coroutine on a worker thread.

### Model catalog and input limits

- Per provider: the transports it offers under the policy in decision 4 (both
  supported providers: upload, then in-request fallback), upload purpose where
  the provider needs one, and the allowed upload expiry range with its maximum
  as the default.
- Each model entry: `provider`, `model_id`, `max_pdf_pages` (null when the
  provider documents no page limit), `max_pdf_bytes` (the largest PDF the
  provider accepts as model input through its primary transport, here the
  upload), `max_request_pdf_bytes` (the largest PDF file that fits inside one
  request after base64 encoding, less an allowance for the prompt; null when the
  provider has no in-request path), `context_window_tokens`,
  `pdf_tokens_per_page`, `limits_source` (URL and as-of date), effort mapping,
  output mode.
- Entries ship for the default model and for every model the docs name. The docs
  name at least the default Anthropic model and one OpenAI model that accepts
  PDF input (Developer picks the current OpenAI model recommended for document
  input and records its documented limits and source).
- Documented limits as read on 2026-11-17 (Developer rechecks the sources):
  - Anthropic (`platform.claude.com` PDF support and Files API pages): 600 pages
    per request (100 when the context window is under 1M tokens); 128 MB per
    request for PDFs sent inside the request; 500 MB per Files API file. The
    default model's entry: 600 pages, 500 MB uploaded, in-request about 95 MB
    (128 MB after base64's 4/3 growth, less the prompt allowance; Developer sets
    the exact figure).
  - OpenAI (`developers.openai.com` PDF files guide): under 50 MB per file and
    50 MB per request, inline or uploaded; no page limit stated; files for model
    input use purpose `user_data`. OpenAI entries: 50 MB both ways, pages null
    (Developer confirms how OpenAI counts the 50 MB for base64 input).
- Check (before any model call or upload, on the whole file): page count >
  `max_pdf_pages` or byte size > `max_pdf_bytes` raises `InputLimitError` whose
  message names the model, the limit (pages or bytes), the limit's value and the
  PDF's value, and tells the user to split the PDF or choose a model with higher
  limits. A model with no catalog entry and no override gets a `PydelityWarning`
  and proceeds. When the estimated input tokens exceed the model's context
  window, warn (not block): Anthropic notes that large PDFs can fail before the
  page limit, even through the Files API.
- The check above uses the primary transport's limit only; a PDF that fits the
  upload but not the in-request limit runs normally and fails only if the
  fallback is needed.
- `advanced.models.<provider:model-id>` overrides any limit, the context window
  and the prices.

### `pdf_survey.json`

All pydelity JSON outputs carry `schema_version` as a `"MAJOR.MINOR"` string
(this cycle `"1.0"`; additive changes bump the minor, breaking changes the
major) and `pydelity_version`. All bounding boxes in stored outputs are PDF
points in the displayed (rotation-applied) page space, origin top-left,
`[x0, y0, x1, y1]`. Page indexes are 0-based.

- `fingerprint` — `"sha256:<hex>"` of the canonical JSON (sorted keys, no
  whitespace) of: PDF SHA-256, resolved `model`, `instructions`, `languages`,
  `advanced.survey` values (`max_retries`, `effort`, `max_output_tokens`),
  `PROMPT_VERSION`, survey `schema_version`. Excludes `max_cost`, `overwrite`,
  `output_dir`, model limits and prices.
- `inputs` — `pdf_name`, `pdf_sha256`, `pdf_bytes`, `page_count`, `model`,
  `instructions`, `languages`, survey settings, `prompt_version`.
- `facts` (measured, no model):
  - `pages[]`: `index`, `width_pt`, `height_pt`, `rotation_attribute`, `text`
    (`chars`, `control_chars`, `replacement_chars`, `private_use_chars`,
    `unassigned_chars`, `quality`: `none` | `good` | `garbled`), `orientation`
    (`dominant`: 0 | 90 | 180 | 270 | null, `confident`, `chars_by_angle`),
    `direction` (`inline`: `ltr` | `rtl` | `mixed` | `none`, `vertical_share`),
    `printed_number` (`text`, `value`, `style`: `arabic` | `roman` | `label`,
    `source`: `page_label` | `text`) or null.
  - `bookmarks[]`: `level`, `title`, `page_index` (null when unresolved).
  - `form_fields[]`: `page_index`, `name`, `type` (`text` | `checkbox` | `radio`
    | `combobox` | `listbox` | `signature` | `button`), `value`, `checked` (bool
    for checkbox/radio, else null), `options`, `bbox`; plus `form`:
    `has_acroform`, `has_xfa`.
  - `structure`: `tagged`, `marked`, `element_count`, `type_counts` (after
    RoleMap), `pages_with_tagged_content`, `quality` (`none` | `poor` |
    `partial` | `good`), `truncated`.
  - Unreadable facts: when reading bookmarks, the form or the structure tree
    raises on a malformed PDF, that fact is `null` (`bookmarks`, both
    `form_fields` and `form`, or `structure`), never an empty value, so `null`
    means "could not be read" and `[]` means "the PDF has none". Each such case
    adds one `probe_errors[]` item: `fact` (`bookmarks` | `form` | `structure`),
    `message` (the error, without file contents). `probe_errors` is `[]` when
    every fact was read. The survey continues; the facts summary sent to the
    model says the fact is unavailable, no check depends on these facts, and
    each item becomes a `probe_unavailable` warning in `run.json`.
  - `repeated_lines[]`: `id` (`R1`, `R2`, …), `text` (a representative
    original), `normalized`, `pages`, `band` (`top` | `bottom` | `middle`);
    `repeated_lines_truncated`.
  - `page_numbering[]`: measured ranges `first_page_index`, `last_page_index`,
    `style`, `offset` (printed − page index), `pages_measured`.
- `proposal` (model output that is not profile): `regions[]` (`page_index`,
  `bbox`, `label`, `note`), `artifacts[]` (`id`, `description`, `position`,
  `repeated_line_ids`), `non_artifact_lines[]` (`repeated_line_id`, `reason`),
  `notes[]`. `position` is where the artifact sits on the displayed page: `top`
  | `bottom` | `left` | `right` | `middle` (`middle` covers watermarks and
  stamps over the content). It is informational; no check uses it.
- `profile` (what steps 2–3 depend on and fingerprint):
  - `labels[]`: `name`, `role`, `kinds`, `description`. Always contains `other`
    (role `body`, all kinds), which Python adds and owns; a model-made `other`
    is replaced.
  - `languages[]` — user languages first, then model languages not already
    present (case-insensitive).
  - `writing_direction`: `default` (`ltr` | `rtl` | `ttb`) and `ranges[]`, each
    `first_page_index`, `last_page_index` (inclusive), `direction` (`ltr` |
    `rtl` | `ttb`); pages no range covers use `default`.
  - `rotation[]`: `first_page_index`, `last_page_index`, `degrees` (0 | 90 | 180
    | 270, clockwise rotation that makes the displayed page's content upright);
    uncovered pages are 0.
  - `page_numbering[]`: `first_page_index`, `last_page_index`, `style` (`arabic`
    | `roman` | `other` | `none`), `offset` (int or null).
  - `continuation_notes[]` (strings), `start_markers[]` (`text`, `description`),
    `user_instructions` (string or null).
- `checks[]`: one item per check C1–C7, in that order: `name` (the check name),
  `passed` (true when `failures` is empty), `attempts` (model answers checked, 1
  plus the retries used), `failures[]` (on the accepted answer). Each failure
  item: `page_index` (int, or null when no single page applies), `message`
  (names the check, what was proposed and what was measured), `details` (object
  with the proposed and measured values, such as
  `{"proposed": 0, "measured": 90}`). A failure that concerns several pages is
  one item per page, so a wrong rotation range over 30 pages gives 30 items.
- `issues[]`: review issues from this step, one per failure item of the accepted
  answer: the failure's `page_index`, `message` and `details` plus `step`
  (`"survey"`) and `check` (the check name), the same shape as `run.json`
  `review[]`.
- Model-facing proposal schema: a separate Pydantic model using only strings,
  integers, booleans, enums, arrays and objects (no pattern, length or numeric
  bounds) so it fits both providers' structured-output subsets; bounds are
  checked in Python. Region boxes are fractions (0–1) of the displayed page;
  Python converts them to points.

### Checks (names are part of the `run.json` contract)

- `labels` (C1): names non-empty and unique (case-insensitive), every label has
  at least one kind, every region names an existing label.
- `regions` (C2): valid page index; box within 0–1 with `x0 < x1`, `y0 < y1`.
- `rotation` (C3): ranges inside the PDF, non-overlapping; on every page whose
  measured orientation is confident, the profile's degrees equal the measured
  `dominant`.
- `page_numbering` (C4): ranges inside the PDF, non-overlapping; in each range,
  at least 80% of pages with a measured arabic number match `index + offset`; a
  measured range of 3 or more pages must be covered by a profile range with the
  same offset.
- `artifacts` (C5): every probe repeated-line ID appears exactly once, in an
  artifact or in `non_artifact_lines`; no unknown IDs.
- `writing_direction` (C6): ranges inside the PDF and non-overlapping.
- `languages` (C7): at least one syntactically valid BCP-47 tag (`zxx` allowed).

### `run.json`

- `schema_version`, `pydelity_version`, `run_id` (UTC timestamp plus random
  suffix), `status` (`running` | `completed` | `failed` | `stopped` |
  `interrupted`), `started_at`, `ended_at`, `pdf` (`path`, `sha256`,
  `page_count`, `bytes`), `settings` (resolved, no secrets), `steps[]` (`name`,
  `status`: `completed` | `reused` | `failed` | `stopped` | `skipped`, `output`,
  `requests`, `cost_usd`, `pdf_transport` (`upload` | `request` | null when no
  PDF was sent), `started_at`, `ended_at`, `error`), `cost` (`run_usd`,
  `by_step`, `output_folder_usd`, `unpriced_requests`), `review[]`,
  `warnings[]`, `error`.
- Warning item: `code`, `step` (or null), `message`, `details` (object). Codes
  this cycle: `unknown_model_limits`, `unpriced_model`, `context_window`,
  `other_pdf_in_folder`, `damaged_output`, `upload_fallback`,
  `probe_unavailable`. The same message goes to `PydelityWarning` in Python and
  to the CLI. The CLI summary groups review issues by check and shows a count
  per check before listing them.
- Review issue: `step`, `check`, `page_index` (null when none applies),
  `message`, `details` (object). The run's review list holds the issues of every
  step output used by the run, reused ones included.
- Written at start (`running`) and at the end; on Ctrl+C the pipeline catches
  `KeyboardInterrupt`, writes `interrupted`, and re-raises.

### `cost.jsonl`

- One JSON object per model request that returned a response (retries and
  responses that failed validation included): `schema_version`, `run_id`,
  `step`, `request` (sequence within the step run), `timestamp`, `provider`,
  `model`, `response_model`, `input_tokens`, `output_tokens`,
  `cache_read_tokens`, `cache_write_tokens`, `cost_usd` (number rounded to 6
  decimals, or null when unpriced), `price_source` (`genai-prices <version>` |
  `config` | null).
- Append, flush and `fsync` one line at a time under an in-process lock (later
  steps run requests concurrently). Readers skip a damaged trailing line with a
  warning. Money is `Decimal` in Python.

### `uploads.json`

- `schema_version`, `pydelity_version`, `uploads[]`: `provider`, `file_id`,
  `pdf_sha256`, `pdf_name`, `bytes`, `uploaded_at`, `expires_at` (null when the
  provider sets no expiry).
- At most one record per provider and PDF SHA-256; a new upload replaces the old
  record. Written atomically after each successful upload. Holds no secrets.
  Uploads are per provider account, so a different API key can make a recorded
  file unavailable; the "file not found" re-upload rule covers it.

### Cost estimate and budget

- `CostEstimate`: per planned step `name`, `model`, `reused`, `requests_max`,
  `expected_usd`, `max_usd`; totals; `spent_usd` (folder ledger); `max_cost`;
  `priced`; `warnings`.
- Input tokens per request ≈ `page_count × pdf_tokens_per_page` + prompt
  characters ÷ 4. Expected = one request with a typical output (a named
  constant). Maximum = `(1 + max_retries)` requests, each with
  `max_output_tokens` of output and the previous answer added to the input.
  Constants are named and documented in the reference.
- Budget guard: before each request, if `spent_usd` (whole folder ledger) + that
  request's upper bound > `max_cost`, raise `BudgetExceededError` without
  calling. With `max_cost` set and no price for the model, refuse before the
  first call. Without `max_cost`, unpriced requests are recorded with null cost
  and a warning.

### HTML report

- `report.html` plus `report/pages/<NNNN>.<jpg|png>` (4-digit 0-based index,
  about 1000 px wide), rendered by PyMuPDF; images are re-rendered only when
  missing or when `report/manifest.json`'s PDF SHA-256 differs.
- Content: run header (PDF, status, model), cost (this run by step, folder
  total), review list, profile, facts summary (bookmarks, form fields, structure
  quality, repeated lines with their artifact mapping), then one card per page:
  image with region and form-field boxes as CSS overlays positioned in percent,
  page findings (text quality, orientation, direction, printed number, profile
  rotation, repeated lines, issues on that page).
- Static HTML: no JavaScript requirement, no external URLs, every inserted
  string HTML-escaped. Written at the end of every run that got past input
  validation, whatever its status, with the data available.

### Test seam

- Provider SDKs read `ANTHROPIC_BASE_URL` and `OPENAI_BASE_URL`; tests and the
  wheel smoke script point them at a loopback mock server that returns canned
  provider responses, including both providers' Files API upload, the "file not
  found" answer that triggers a re-upload, and upload failures that trigger the
  in-request fallback. No production code path exists only for tests.
- An autouse test fixture removes real provider keys, sets dummy ones, and
  points both base URLs at an unused loopback port unless a test supplies the
  mock server, so no test can reach a provider. Tests marked `costs-money` stay
  opt-in.

### Docs site

- `docs/`: Astro + Starlight, `package.json` with exact versions and
  `packageManager` pinning pnpm exactly, `pnpm-lock.yaml`, `astro.config.mjs`
  (`site: https://idinsight.github.io`, `base: /pydelity`), content in
  `docs/src/content/docs/` as `.md` only (Prettier and markdownlint cover them;
  MDX is not linted), `scripts/check-links.mjs` (built-HTML internal link and
  fragment checker, as in IDinsight/standards), `scripts/build-versions.mjs` and
  `src/versioning/` adapted from IDinsight/standards: versions are stable
  `vX.Y.Z` tags ≥ `0.1.0`; each tag's `pyproject.toml` version must equal the
  tag; shared rendering files come from the current checkout; latest at
  `/pydelity/`, each release at `/pydelity/v/<version>/`; `versions.json` and a
  version selector.
- Generated reference pages in `docs/src/content/docs/reference/`
  (configuration, CLI, Python API, `pdf_survey.json`, `run.json`, `cost.jsonl`,
  `uploads.json`, survey checks), produced by
  `scripts/generate_reference_docs.py` from the `Config`, Typer command, public
  API and output Pydantic models, each marked as generated. Prose pages are
  Documenter's.
- Node `24.22.3` (the repo's one Node version, kept by hand in CI as in the
  hooks).

### CI, release and recipes

- `ci.yml` jobs: `lint-and-test` "Lint and test (Python 3.13)" (today's steps),
  `test-py314` "Test (Python 3.14)" (`uv` with `--python 3.14`, `just test`),
  `wheel` "Wheel install (`<os>`)" on `ubuntu-latest`, `windows-latest`,
  `macos-latest` (build, then `scripts/smoke_installed_wheel.py`), and `gate`
  named **"Lint and test"** with `needs` on all three and
  `if: ${{ !cancelled() }}`, failing unless every needed job's result is
  `success`. The ruleset keeps requiring "Lint and test"; no ruleset change.
- `scripts/smoke_installed_wheel.py` (stdlib only): creates a fresh `venv` with
  pip, `pip install`s the built wheel (its runtime dependencies from PyPI),
  starts the loopback mock server, and runs both the `pydelity` console script
  (`--yes`) and the Python API on a small fixture PDF with each provider,
  asserting exit codes and valid outputs. Works on Windows paths and scripts.
- `release.yml`: `on: release: types: [published]`, `permissions: {}`. Job
  `build` (`contents: read`): checkout at the release tag, fail unless the tag
  equals `v` + the `pyproject.toml` version, `uv build`, `twine check --strict`,
  upload `dist/` as an artifact; no caches. Job `publish` (`needs: build`,
  environment `pypi`, `id-token: write` only): download the artifact and run
  `pypa/gh-action-pypi-publish` (SHA-pinned). zizmor clean.
- `docs.yml`: pull requests build the current tree and run the link checker;
  pushes to `main` and `v*` tags and `workflow_dispatch` run the versioned build
  when at least one supported tag exists (else the current-tree build), then the
  link checker; a `deploy` job (`pages: write`, `id-token: write`, environment
  `github-pages`) runs only on pushes to `main` or tags when the
  `pyproject.toml` version on the built commit has its tag. Tag builds check out
  `main` for shared rendering, as IDinsight/standards does.
- `dependabot.yml`: add the `npm` ecosystem for `/docs` (`build(deps)`, monthly,
  grouped, 7-day cooldown).
- `justfile` (alphabetical after `default`): `build` (clean `dist/`, `uv build`,
  `twine check --strict dist/*`), `docs` (pnpm install with frozen lockfile, dev
  server), `docs-build` (frozen install, current-tree build, link check),
  `docs-reference` (run the generator), and `lint` runs `docs-reference` before
  `lint-markdown`, so CI's existing `git diff --exit-code` fails on stale
  reference pages.
- `pyproject.toml`: runtime dependencies (decision 2), `twine` exact in the dev
  group, `[project.scripts]`, `Documentation` URL, description describing the
  usable survey release, classifiers (`Development Status :: 3 - Alpha`, Python
  3.13 and 3.14, `Typing :: Typed`, OS independent, console environment).
  `.gitignore`: `docs/node_modules/`, `docs/dist/`, `docs/.astro/`.

## Data and Control Flow

1. Resolve settings (defaults ← file ← CLI or keywords); validate everything,
   collecting all errors; raise `ConfigError` before anything else.
2. Open the PDF (PyMuPDF): SHA-256, page count, size; a password-protected,
   empty or unopenable PDF raises `PdfError` naming the file and the reason;
   then the input-limit check against the merged catalog entry.
3. Prepare the output folder: create it, remove stale `*.tmp-*` files, warn if
   an existing `run.json` names a different PDF SHA-256, write `run.json`
   (`running`).
4. Plan the survey: load `pdf_survey.json` if present; invalid JSON or schema →
   warn and treat as absent; matching fingerprint and no `overwrite` → reuse.
5. If the survey runs: check the provider key; CLI estimate and confirmation
   (Python skips it); probe facts; reuse the PDF's upload from `uploads.json` if
   it has at least an hour left, otherwise upload it and record it; build the
   agent through `build_model`; run it; each request passes the budget guard and
   is written to the ledger; the output validator runs C1–C7 and retries or
   accepts as in decision 5; Python adds `other`, merges user languages, stores
   `user_instructions`, converts region boxes; write `pdf_survey.json`
   atomically. If the provider answers that the recorded file no longer exists,
   upload again once, replace the record and retry the request. When the upload
   path fails (decision 4), send the PDF inside the request instead, or fail
   with `SurveyError` when the PDF is over the in-request limit.
6. Assemble `run.json` (steps, cost from the ledger, review list, warnings),
   write the report, print the CLI summary.
7. Any exception after step 3 records `failed`, `stopped` or `interrupted` in
   `run.json` and still writes the report before re-raising. A stopped or
   interrupted survey writes no `pdf_survey.json`; the next run redoes it, with
   the earlier spend already in the ledger and counted against `max_cost`.

## Technical Acceptance Criteria

- `AC-001`, `AC-005`: Measurement rules, each a named constant documented in the
  generated reference:
  - Text quality from PyMuPDF character text: `none` when a page has no
    non-whitespace characters; `garbled` when control (Cc other than tab, line
    feed, carriage return), private-use (Co), unassigned (Cn) and U+FFFD
    characters together reach a threshold share of the page's characters;
    otherwise `good`. Raw counts are always stored.
  - Orientation: each line's direction vector combined with the page's rotation
    attribute gives the baseline angle on the displayed page, counterclockwise
    from left-to-right, quantised to 0/90/180/270 and weighted by character
    count; lines in vertical writing mode (PyMuPDF `wmode` 1) are excluded and
    counted in `vertical_share`. `confident` needs a minimum character count and
    a dominant share of at least 80%. So a page with rotation attribute 0 and
    sideways text reports 90 or 270.
  - Inline direction from Unicode bidirectional classes of letters: `rtl` when R
    and AL classes reach 70% of strong characters, `ltr` when L does, `mixed`
    otherwise, `none` without strong characters.
  - Printed numbers: the PDF page label when the document defines labels;
    otherwise a line in the top or bottom band that is a single number in any
    script's decimal digits (Python `int()` on `str.isdecimal()` text) or a
    roman numeral, with only non-letter decoration around it. Ranges of constant
    `printed − index` form `page_numbering`.
  - Repeated lines: normalise (NFKC, case fold, collapse whitespace, decimal
    digits → `#`); a normalised line counts once per page and is repeated when
    it appears on at least 3 pages and at least 5% of pages (2 pages when the
    PDF has 2 or 3 pages); at most 200, most frequent first, with
    `repeated_lines_truncated` set when capped.
  - Bookmarks from PyMuPDF's table of contents; form fields from PyMuPDF
    widgets, with checkbox and radio `checked` from the on-state value; XFA
    presence from the AcroForm dictionary.
  - Structure: walk `StructTreeRoot` through PyMuPDF's low-level object access,
    map types through RoleMap, count types and pages referenced, with a node cap
    that sets `truncated`. `poor` when only grouping types (Document, Part,
    Sect, Div, Span, NonStruct, Art) or few elements; `partial` when content
    types exist but tagged pages cover less than 90% of pages with text; `good`
    otherwise.
  - Probe failures in bookmarks, forms or structure on malformed PDFs set that
    fact to `null`, add a `probe_errors[]` item and a `probe_unavailable`
    warning, and never fail the run; a PDF that simply has none of them records
    `[]` (or a `structure` with `tagged: false`).
- `AC-002`: The stored profile always has `other`; every label maps to exactly
  one role and a non-empty kind list from the enums.
- `AC-003`: Each failing check produces a `ModelRetry` message naming the check,
  the pages and the measured values while retries remain; after the last allowed
  attempt, every still-failing check appears in `pdf_survey.json` `issues` and
  in the run's review list with `step: "survey"`, the check name and the page
  where one applies.
- `AC-004`: Instructions and languages appear in the prompt and in `profile`;
  the checks run identically with and without them; no setting skips a check.
- `AC-006`: Core code, prompts, schema field names, defaults and checks contain
  no document-type or domain words and no natural-language word lists; language
  handling uses Unicode properties only. Prompt examples, if any, use neutral
  placeholders.
- `AC-007`, `AC-010`: `import pydelity` performs no file, network or environment
  reads and produces no output on stdout, stderr or loguru sinks.
- `AC-009`: Every invalid setting in a single input is reported in one error; no
  model request happens.
- `AC-011`: Both providers pass the same survey flow with their canned responses
  through the real PydanticAI provider adapters.
- `AC-012`, `AC-013`: The check runs before any upload or request; overrides
  under `advanced.models` replace catalog values; unknown models warn and
  proceed.
- `AC-014`: The ledger has one line per returned response; `run.json`
  `cost.by_step` and `run_usd` equal the sums of this run's ledger lines;
  `output_folder_usd` equals the whole ledger.
- `AC-015`: No request happens before confirmation in the CLI; a non-interactive
  stdin without `--yes` exits 3 before spending; the Python API never reads
  stdin.
- `AC-016`: No request is sent when the folder's recorded spend plus that
  request's upper bound exceeds `max_cost`; the run then ends `stopped` with
  every written file valid, and a later run with a higher `max_cost` completes
  without discarding recorded spend.
- `AC-017`: A rerun with identical fingerprint inputs sends no request; changing
  any fingerprint input or setting `overwrite` sends requests.
- `AC-018`: No output file exists in a partial state at any point; a corrupt or
  schema-invalid `pdf_survey.json` is regenerated; stale temp files are removed;
  an `uploads.json` record is written only after its upload succeeded, and a
  damaged `uploads.json` is treated as empty (the PDF is uploaded again).
- `AC-019`: Review issues carry step, check and page (or null); the CLI summary
  shows their count and entries.
- `AC-020`: The report opens from disk with no network access and shows every
  page image with its findings and region boxes, the profile, the run's cost and
  the review list.
- `AC-021`: The test suite runs with no route to a provider; both providers'
  response shapes, both providers' Files API uploads, upload reuse from
  `uploads.json`, re-upload after "file not found", the in-request path, the
  fallback after an upload failure, the stop on an authentication failure, and
  the error when the PDF is too large for the fallback are exercised.
- `AC-011`, `AC-018`: A survey whose upload fails for a reason other than
  authentication completes through the in-request path when the PDF fits, with a
  warning and `pdf_transport: "request"` in `run.json`, and writes no
  `uploads.json` record.
- `AC-022`: "Lint and test" fails when any of lint, Python 3.13 tests, Python
  3.14 tests or the wheel jobs fails or is skipped.
- `AC-023`, `AC-024`: On `windows-latest` (and Linux, macOS) a fresh venv
  installs the built wheel with pip and both the console script and the Python
  API complete a mocked survey; wheel and sdist pass `twine check --strict`.
- `AC-026`: Publishing needs no stored PyPI token; only the `publish` job holds
  `id-token: write`; zizmor `--persona=auditor` reports nothing for
  `release.yml`.
- `AC-036`: With the manifest at `0.0.1`, no `v0.0.1` tag or release, and no
  feat, fix or breaking commit on `main` before this cycle's merge,
  release-please (the version bundled in the pinned
  `release-please-action@v5.0.0`) treats the manifest version as the last
  release and proposes `0.1.0` for one `feat:` commit. Developer establishes
  this from that release-please version's source or a dry run against a
  throwaway repository; if it does not hold, the fallback is
  `"release-as": "0.1.0"` in `release-please-config.json`, removed in the first
  pull request after the release, and the release procedure says so. The
  squash-merge title of this cycle's pull request is a non-breaking `feat:`.
- `AC-027`, `AC-028`, `AC-029`: The current-tree build fails on a broken
  internal link or fragment. The versioned build, run in a scratch clone with a
  local test tag (never pushed), produces the latest version at the root, each
  release under `/v/<version>/` and a working selector. Deploy is skipped while
  `v<pyproject version>` does not exist.
- `AC-030`: `docs/package.json` uses exact versions; Dependabot covers `/docs`;
  docs pages are `.md` and pass the repo's Markdown hooks.
- `AC-032`: Reference pages regenerate byte-identically from the code after
  Markdown formatting; a stale page fails CI through `just lint` and
  `git diff --exit-code`.

## Build Plan

Existing files are marked `MODIFY`. Every new file or folder is `CANDIDATE`:
Developer proposes its name and place and waits for the user's sign-off.

1. **Package foundation** — `MODIFY pyproject.toml`, `uv.lock` (dependencies,
   `twine`, console script, metadata), `src/pydelity/__init__.py`,
   `.template.env`; `CANDIDATE` modules for errors, `python -m pydelity`,
   configuration, general utilities (atomic files, fingerprints) and the model
   catalog. Must land together so the package imports and the strict editable
   install still passes the existing smoke tests.
2. **PDF and probe** — `CANDIDATE` modules for opening PDFs, the facts schemas
   and enums, and the probe; test PDF fixtures (each under the 500 KB hook
   limit; synthetic ones generated by a committed script with PyMuPDF; a
   tagged-PDF fixture needs a producer that writes structure trees, or a small
   public document approved by the user).
3. **Cost and model layer** (parallel with 2) — `CANDIDATE` modules for the
   ledger, pricing, estimate and budget guard; `build_model`, provider settings
   and `LedgerModel`; Files API upload, reuse and the `uploads.json` record; the
   in-request fallback.
4. **Survey step** — `CANDIDATE` modules for the prompt, checks, proposal and
   profile schemas, and the step (agent, validator, fingerprint, reuse). Depends
   on 2 and 3.
5. **Run, report, API, CLI** — `CANDIDATE` modules for run orchestration, the
   report, the API functions and the CLI; canned provider responses for tests.
   Critical path: 1 → 2 → 4 → 5.
6. **CI and release** — `MODIFY .github/workflows/ci.yml`,
   `.github/dependabot.yml`, `justfile`, `.gitignore`; `CANDIDATE` release
   workflow and wheel smoke-test script; establish the AC-036 evidence. Depends
   on 5.
7. **Docs site** — `CANDIDATE` Astro project under `docs/` (versioning and
   link-check scripts adapted from IDinsight/standards, page skeleton and
   sidebar), docs workflow, reference-docs generator and the generated reference
   pages. Depends on 5 for the generator; the site scaffold can start any time.
   Documenter writes the prose pages and README later.

## Risks and Follow-up

- PyMuPDF is AGPL-3.0 (user's choice). The README and docs should say so where
  installation is described (Documenter).
- release-please's handling of a manifest version with no matching tag is
  unverified (CONTEXT Known Unknowns); AC-036 names the evidence and the
  fallback.
- Provider PDF limits, prices and model IDs drift. Catalog entries carry their
  source and date; `advanced.models` covers the gap between releases. The
  `genai-prices` data in the KGForEdGlobal environment lists `claude-opus-5` but
  not `claude-opus-5-5`; Developer confirms that the pinned version prices the
  default model, or ships an override for it in the catalog.
- Uploaded PDFs stay in the user's provider file storage until they expire: by
  default the provider's maximum (90 days on Anthropic), and they count against
  the organization's storage (Anthropic: 1 TB). Anthropic's expiry range is
  documented (1 hour to 90 days). OpenAI's upload expiry and its allowed range
  were not confirmed (its API reference page could not be read), so Developer
  checks them. If OpenAI offers no expiry, its uploads persist until the user
  deletes them, and `expiry_hours` set for OpenAI is an invalid setting. The
  docs must say that PDFs are uploaded to and stored by the provider, for how
  long, and how to shorten it (Documenter).
- The token estimate is a heuristic; `max_cost` relies on per-request upper
  bounds, so it can stop a run that would have fitted. A 600-page PDF can exceed
  a 1M context window within the page limit; the estimate warns and the
  provider's error is reported.
- Non-streaming requests with large `max_output_tokens` need an explicit request
  timeout (the Anthropic SDK refuses long non-streaming requests otherwise). If
  Developer switches to streaming, `LedgerModel` must wrap the streaming request
  path too.
- Claude Opus 5.5 can stop with `refusal`; the survey reports it as a failure.
  Server-side refusal fallbacks are not enabled in this cycle (they change the
  billed model mid-request).
- `pnpm-lock.yaml` may approach the 500 KB new-file hook limit; if it exceeds
  it, exclude that one path from `check-added-large-files` with a comment.
- One run per output folder at a time; concurrent runs in the same folder are
  unsupported and not detected.
- On Windows, `os.replace` fails while another program holds the target open;
  the error names the file.
- The versioned docs build meets real tags only after sign-off; in-cycle
  evidence uses a local test tag in a scratch clone.
- Coverage scaffold entries (`def cli` exclusion, `__init__.py` omit) in
  `pyproject.toml` can be tidied while editing it; not required.
- Later cycles: steps 2–6 reuse `build_model`, `LedgerModel`, the budget guard,
  atomic files, fingerprints, review issues and the report; they add `pages`,
  `schema` and per-step `advanced:` settings and extend the default run. Other
  PydanticAI providers can be added later by extending the provider allowlist,
  the model factory and the catalog; this cycle supports only Anthropic and
  OpenAI.

## Alternatives

- pypdfium2 plus pypdf instead of PyMuPDF: permissive licences, but more probe
  code and less reuse. Rejected by the user's decision.
- PDFs sent inside the request (base64) as the first choice for providers that
  also offer uploads: no stored copy at the provider, but a 128 MB request limit
  for Anthropic instead of 500 MB per file, and every retry and rerun resends
  the PDF. Prompt caching works the same either way. The user's policy prefers
  uploads and keeps the in-request path as the fallback.
- Falling back on model-request errors too: a model error rarely comes from the
  upload, and resending would repeat a paid request; the fallback covers only
  the upload path's own failures.
- Deleting uploads when the step ends: less stored data at the provider, but
  every rerun uploads again and later steps cannot reuse the file. The user
  chose to keep uploads until their expiry.
- Counting cost from `result.usage()` after each agent run: loses per-request
  detail and cannot stop before a request; the model wrapper does both.
- Checks outside PydanticAI in a hand-written retry loop: more code, and the
  output validator already gives retries with conversation history and a
  last-attempt signal.
- Required checks for each new CI job: needs a ruleset change the repo cannot
  make; the gate job keeps the existing required check name.
- npm instead of pnpm for the docs: departs from IDinsight/standards and
  produces a larger lock file.
- Hand-written reference pages: drift from the code; generation makes AC-032
  checkable.

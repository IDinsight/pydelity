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
  (AC-001 to AC-046; AC-003, AC-012, AC-013 and AC-016 are retired). Project
  context: `.standards/CONTEXT.md`. Design inputs: `artifacts/design_brief.md`
  (step 1 design points, cross-cutting directions, known source defects) and
  `artifacts/next_cycle_inputs.md`.
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
- User rework recorded 2026-11-17 during development (scope AC-037 to AC-039):
  pydelity ships no per-model PDF input limits and checks none before the call;
  the provider's own error reaches the user. Going over `max_cost` warns and the
  user decides: the CLI asks (`--yes` continues), and Python callers pass a
  boolean argument. The design applies the same reasoning to all per-model data
  (decision 3).
- User rework recorded 2026-11-17 during development (scope AC-040): the
  measured facts and their summary go in their own permanent output file,
  written before any API key check, cost question or model call, and the summary
  is logged; `pdf_survey.json` still holds the facts (AC-001). The design names
  the file `pdf_facts.json`, after `pdf_survey.json`.
- User rework recorded 2026-11-17 during development (scope AC-041 to AC-044):
  the provider retry count is a setting (today both SDKs default to 2); the
  Python API adds `measure` and `load` and async versions named with an `a`
  prefix; the survey keeps Python checks only, with no verifier model. The scope
  leaves to Architect the default retry count, how the checks work and whether
  `load` gets an async version (decisions 5, 13 and 14).
- User rework recorded 2026-11-17 during development: language tags (the
  `languages` setting and check C7) are checked with the `langcodes` library, a
  new runtime dependency, instead of a hand-written pattern (decision 15).
- User rework recorded 2026-11-18 during development: the sync API functions use
  `asyncio.run` only and raise an error pointing to the async version when an
  event loop is already running, instead of using a worker thread (decision 14).
- User rework recorded 2026-11-18 during development (scope AC-045 and AC-046,
  replacing AC-003): the survey's model treats the measured facts as hints and
  trusts its own reading of the PDF. The checks that send an answer back test
  only that it is well formed and complete; differences from the measured
  rotation and printed page numbers go on the review list (decision 5). It
  followed a run where the probe took numbers in table cells for printed page
  numbers and the old page-numbering check made the model agree with them.
- Survey changes the user approved during development (2026-11-18, recorded in
  the development plan) are part of this design: repeated lines ignore invisible
  formatting characters and the probe keeps up to 1,000 of them; a page label
  gives the number at its end; and the survey request lists every repeated line.
- Test PDFs are real public-domain documents the user approves, not generated
  ones (user decision recorded in the development plan, 2026-11-17).
- No project references exist under `.standards/project-references/`; none is
  named for downstream roles.

## Decision

1. **Library first, thin CLI.** All behaviour lives in the `pydelity` package
   behind a small public Python API (`measure`, `estimate`, `survey`, `run`,
   their async versions, `load`, `Config`, result models, exceptions). The Typer
   CLI only parses options, shows the estimate, asks for confirmation, calls the
   API and prints a summary. Importing pydelity reads no environment, builds no
   settings and emits no log output: `pydelity/__init__.py` calls
   `loguru.logger.disable("pydelity")` and the CLI enables it.
2. **Stack.** Runtime dependencies (minimum versions, written by `uv add`):
   `pydantic`, `pydantic-settings[yaml]`, `pydantic-ai-slim[anthropic,openai]`
   (the slim distribution, so installs pull only the two supported providers; it
   brings `genai-prices`, whose bundled price data PydanticAI's cost calculation
   uses), `langcodes` (MIT, no runtime dependencies; decision 15), `loguru`,
   `typer`, `pymupdf`. No templating library: prompts and the HTML report
   template are Python string constants, so the wheel needs no package data
   beyond `py.typed`.
3. **Models.** A model setting is `<provider>:<model-id>` with provider
   `anthropic` or `openai`; any other provider is an invalid setting. Default:
   `anthropic:claude-opus-5-5`. OpenAI models run through PydanticAI's Responses
   model. All model construction goes through one factory (`build_model`) that
   returns the provider model wrapped in a ledger wrapper (decision 6).

   **pydelity ships no per-model data**: no PDF page or size limits, context
   windows or capability lists, since none of it can be kept current (the user's
   reason for AC-037). It ships provider-level facts only (under **Providers and
   models**). Per-model knowledge comes from maintained upstream data:
   PydanticAI's model profiles (structured-output support) and `genai-prices`
   (prices). Every model of a provider gets the same request settings, and a
   model that rejects a setting or the PDF fails with the provider's own error
   (`ProviderError`, AC-037).

   Structured output must not depend on forced `tool_choice` (Claude Opus 5.5
   rejects `any`/`tool` with a 400): use PydanticAI `NativeOutput` (provider
   structured outputs) where the model's PydanticAI profile supports it,
   otherwise `PromptedOutput`, as KGForEdGlobal's `model_registry.py` already
   does for Anthropic. Thinking: Anthropic models run adaptive thinking with an
   explicit `effort`; OpenAI models get `reasoning_effort`. pydelity's `effort`
   setting is `low`, `medium` or `high` (default `high`) and maps to each
   provider. Older models that reject these settings are not supported; the docs
   name the supported models.

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
   summary, every repeated line (ID, text, page count, band) and any user
   instructions and languages. No splitting. Retries reference the same file
   instead of resending the bytes, and Anthropic accepts up to 500 MB per
   uploaded file against 128 MB for a PDF sent inside the request.

   Fallback: when the upload path fails, the step sends the PDF inside the
   request instead, as PydanticAI `BinaryContent(media_type="application/pdf")`,
   for the rest of that step run. The upload path has failed when the upload
   call fails after the provider retries (decision 13; connection error,
   timeout, rate limit, server error, or any other error response except the two
   below), or when a re-upload after "file not found" fails. Two upload errors
   stop the run with `ProviderError` instead, because the in-request call would
   fail the same way: an authentication failure, and a rejection as too large
   (HTTP 413; neither supported provider accepts a larger PDF inside a request
   than as an upload). Errors from the model request itself never trigger the
   fallback. The fallback is recorded as a warning in `run.json` (with the
   upload error) and the step's `pdf_transport` becomes `request`; nothing is
   written to `uploads.json`. pydelity does not check the PDF against any size
   limit before the fallback: if the provider rejects the in-request call too,
   the run stops with `ProviderError` carrying that rejection, and its message
   also gives the earlier upload error. Prompt caching applies the same way on
   both paths.

   Uploads are kept, not deleted. Each upload sets the provider's expiry from
   `advanced.uploads.expiry_hours`, which defaults to the provider's maximum
   (Anthropic: 90 days); a value outside the provider's allowed range is an
   invalid setting. The output folder's `uploads.json` records each upload, and
   any later run or step that needs the same PDF on the same provider reuses it
   while it has at least one hour left. A file the provider no longer has (for
   example after expiry or under another API key) is uploaded again and the
   record replaced. pydelity never deletes uploads; they expire at the provider.
   Uploads are free and are not ledger entries. Nothing is uploaded before the
   CLI's confirmation and the plan-time `max_cost` check.

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

5. **The model's reading wins over the measured facts; Python checks only that
   the answer is well formed and complete** (AC-045, AC-046). The probe reads
   the PDF's text layer and objects, not the page as a reader sees it, so it can
   miss things (text inside images) or mistake them (a number in a table cell
   taken for a page number). The prompt therefore gives the measured facts as
   hints: wherever the model's own reading of the PDF differs from them, for
   page numbers, rotation or any other fact, the model answers with what it
   reads. It must still say, for every repeated line, whether it is an artifact
   or content.

   Checks C1–C7 run in a PydanticAI output validator on every model answer. They
   use the facts only for the page count and the repeated-line IDs, and never
   compare the answer with a measured value. While retries remain, a failed
   check raises `ModelRetry` with a message naming each failure. On the final
   allowed attempt (`RunContext.last_attempt`), the validator accepts the answer
   and records each still-failing check as a review issue.
   `advanced.survey.check_retries` (default 2) sets `output_retries`. An answer
   that never parses into the proposal schema exhausts PydanticAI's retries and
   fails the survey. Check retries are new model requests and are separate from
   provider retries (decision 13).

   Once the answer is accepted, Python compares the profile with the measured
   rotation and printed page numbers (**Disagreements with the facts**) and
   records each difference as a review issue. This comparison runs once, never
   sends the answer back and never changes the profile. The checks and this
   comparison are all the survey checks: no second model reviews or corrects the
   answer (scope non-goal).

6. **Cost ledger by wrapping the model.** `LedgerModel`, a PydanticAI
   `WrapperModel`, wraps every model pydelity builds. Before each request it
   asks the `max_cost` guard (decision 11) whether the request may go ahead;
   after each response it prices the response's usage and appends one line to
   the output folder's `cost.jsonl`. This records every request, including
   retries, for every future step without per-step code. Each response is priced
   with PydanticAI's own cost calculation (`ModelResponse.cost()`, backed by
   `genai-prices`); pydelity keeps no price table. Prices set for a model under
   `advanced.models` replace that calculation for the model; a model
   `genai-prices` does not know and that has no override is unpriced.
   genai-prices' runtime price updates stay off, so pydelity makes no network
   calls other than to the model providers.
7. **Output folder is the unit of resume and spend.** One folder per PDF run
   holds `pdf_facts.json`, `pdf_survey.json`, `run.json`, `cost.jsonl`,
   `uploads.json`, `report.html` and `report/`. Every JSON and HTML file is
   written atomically (temp file in the same folder, flush, `fsync`,
   `os.replace`) and validated on load. Each step output stores a fingerprint of
   its inputs; a valid output with a matching fingerprint is reused, anything
   else is regenerated.
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
11. **`max_cost` warns and the user decides** (AC-038, AC-039). A run is about
    to go over `max_cost` when the output folder's recorded spend plus what the
    run may still spend exceeds it. That is checked twice: at plan time, after
    the estimate and before any upload or request, against the estimate's
    maximum for the run; and before each model request, against that request's
    upper bound, which catches a run whose real usage beats the estimate. With
    `max_cost` set, an unpriced model counts as going over, since its spend
    cannot be known. Either check raises one `max_cost_exceeded` warning and
    asks the run's over-`max_cost` decision: the CLI asks on the terminal
    (`--yes` answers yes), and the Python API answers with its
    `allow_over_max_cost` argument (default `False`) and never prompts. Yes lets
    the run go over for the rest of that run, with no further warning or
    question; no stops the run in a resumable state (`BudgetExceededError`)
    before anything is sent. The CLI asks at most once: when the plan-time check
    trips, its confirmation question is also the `max_cost` question.
12. **The survey saves its measured facts first** (AC-040). The survey writes
    `pdf_facts.json` (facts plus a plain-text summary) as soon as the probe
    finishes, and logs the summary, before the API key check, the estimate, the
    CLI's question and any upload or model call. So a run that is declined,
    stopped at `max_cost`, rejected by the provider or missing its API key still
    leaves the facts on disk. The facts file has its own fingerprint and is
    reused like any step output; the survey fingerprint includes it, and
    `pdf_survey.json` keeps a copy of the facts it used (AC-001). The run asks
    the CLI's questions through callables it is given, after the facts are
    saved: a confirmation callable (the CLI's prompt or `--yes`; the Python API
    passes none and never asks) and the over-`max_cost` decision (decision 11).
13. **Provider retries are one setting** (AC-041). `advanced.provider_retries`
    (integer 0–10, default 2, the SDKs' own default) is how many times a request
    to the provider is retried after a temporary failure. `build_model` builds
    the SDK client itself (`AsyncAnthropic` or `AsyncOpenAI` with `max_retries`
    and the request timeout) and passes it to PydanticAI's provider
    (`anthropic_client` / `openai_client`), so the same count governs model
    requests and Files API uploads. The SDKs decide what is temporary
    (connection errors, timeouts, HTTP 408, 409, 429 and 5xx, and their
    `x-should-retry` header) and wait as the provider's `retry-after` headers
    say. pydelity adds no retry layer of its own and does not enable
    PydanticAI's optional HTTP retries, so no request is sent more than
    `1 + provider_retries` times. A model request that still fails raises
    `ProviderError`. Two re-sends are not provider retries, because the request
    changes: the one re-send after a new upload replaces a file the provider no
    longer has, and the in-request fallback after the upload path fails (each
    gets its own provider retries).
14. **Async core, sync wrappers** (AC-042 to AC-044). Each measuring, estimating
    or running function is written once as a coroutine: `ameasure`, `aestimate`,
    `asurvey`, `arun`. The sync functions `measure`, `estimate`, `survey`, `run`
    take the same arguments and run the coroutine with `asyncio.run`, so both
    forms give the same results, errors and warnings. A sync function called
    while an event loop is running in its thread (Jupyter, async code) raises
    `RuntimeError` before doing anything, with a message naming the async
    function to await instead (`await pydelity.arun(...)`). It checks for a
    running loop before creating the coroutine, so no file is written and no
    coroutine is left unawaited. The coroutines never call `asyncio.run` and do
    no long blocking work on the event loop: opening and hashing the PDF, the
    probe, and rendering report images run in `asyncio.to_thread`; small JSON
    reads and writes run inline. Warnings are issued from the coroutine, never
    from a worker thread. `load` stays sync only and uses no event loop, so it
    works anywhere: it reads a few local files, and async code can call it
    directly or through `asyncio.to_thread`.
15. **Language tags are checked with `langcodes`.** A language tag, from the
    `languages` setting or from the model, is valid when
    `langcodes.tag_is_valid` accepts it. That checks the tag against the IANA
    language subtag registry bundled with `langcodes`, so a well-formed but
    unregistered tag such as `zz` is rejected; special and private-use tags
    (`zxx`, `und`, `mul`, `qaa`, `x-…`) are valid. pydelity keeps every valid
    tag in its standard form (`langcodes.standardize_tag` with default
    arguments): `en_US` and `EN-us` become `en-US`, deprecated codes become
    their replacements (`iw` becomes `he`), and three-letter codes with a
    two-letter equivalent become two-letter (`eng` becomes `en`). Settings,
    fingerprints, prompts and stored outputs all use the standard form, so two
    spellings of one tag are the same tag. pydelity uses only these two
    functions and does not need the optional `language-data` extra.

### Reuse from KGForEdGlobal

KGForEdGlobal has no survey step, so reuse is limited to infrastructure. Port
and adapt, without changing KGForEdGlobal:

- `utils/pdf.py` `compute_doc_key` → pydelity's PDF SHA-256 helper (full 64-hex
  digest, the later `doc_key`).
- `model_registry.py` → the models component: per-provider settings (Anthropic
  adaptive thinking plus effort, OpenAI Responses reasoning effort) and the
  per-provider output wrapping. Drop its hand-kept adaptive-thinking model set:
  pydelity keeps no per-model data (decision 3).
- `page_ir_extraction/agents.py` → the agent pattern: `Agent` with an output
  validator raising `ModelRetry` with Python check messages.
- Superseded rather than ported: `AgentUsageBucket` (tokens only; replaced by
  the per-request ledger with money) and `write_to_json` (not atomic, a listed
  defect; replaced by the atomic writer). No page-extraction validator, prompt
  or constant is ported: none applies to the survey, and several carry the
  listed defects (left-to-right reading order, English word lists).

## Acceptance Coverage

- `AC-001`: The survey probe, the `facts` contract under `pdf_facts.json` and
  its copy in `pdf_survey.json`; measurement rules under **Technical Acceptance
  Criteria**.
- `AC-040`: `pdf_facts.json` and its summary, written and logged before the key
  check, estimate, questions and model calls (decision 12); facts reuse by
  fingerprint.
- `AC-002`: Model-facing proposal schema and the stored `profile` section, the
  `kind`/`role` enums (decision 8), Python-owned `other` label.
- `AC-045`: Checks C1–C7, the output-validator retry rule (decision 5), review
  issues for checks still failing after the retries; the request lists every
  repeated line so the model can account for each one (decision 4).
- `AC-046`: The prompt's treatment of the facts as hints (decision 5); the
  comparison under **Disagreements with the facts**, run once on the accepted
  answer and never sent back, and its review issues.
- `AC-004`: User instructions and languages flow into the prompt and the stored
  profile after the checks; no setting disables a check or the comparison.
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
- `AC-041`: `advanced.provider_retries` and the SDK clients built with it
  (decision 13); `ProviderError` after the retries.
- `AC-042`: `measure` / `ameasure` and the `PdfFacts` result.
- `AC-043`: `load`, `RunResult` and `OutputError`.
- `AC-044`: The async functions and the sync wrappers (decision 14).
- `AC-014`: `LedgerModel`, `cost.jsonl`, per-step and total cost in `run.json`
  and the CLI summary.
- `AC-015`: `estimate()`, CLI confirmation flow, `--yes`, non-interactive stop;
  the Python API has no prompt.
- `AC-037`: No per-model data and no pre-call PDF check (decision 3);
  `ProviderError` and its CLI output under **Providers and models**; the upload
  fallback rules (decision 4).
- `AC-038`, `AC-039`: The `max_cost` guard (decision 11) over the folder's whole
  ledger: plan-time and per-request checks, the `max_cost_exceeded` warning, the
  CLI question and `--yes`, the Python `allow_over_max_cost` argument and
  `BudgetExceededError`; a stop leaves resumable state.
- `AC-017`: Facts and survey fingerprints and the reuse rule; `overwrite`.
- `AC-018`: Atomic writes, temp-file cleanup, validate-on-load, interrupt
  handling.
- `AC-019`: Review issue contract in `run.json`; CLI end-of-run summary.
- `AC-020`: `report.html` and `report/pages/` contract.
- `AC-021`: Test seams: provider base URLs, the test environment guard, the
  shared mock provider server and canned responses, including temporary failures
  for provider retries.
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
  root command); the API functions (`measure`, `estimate`, `survey`, `run`,
  their async versions, `load`).
- **Run orchestration** — output folder, `run.json`, step sequencing, review
  list, warnings, interrupt handling, calling the report.
- **Survey step** — facts schemas and the `kind`/`role` enums, proposal and
  profile schemas, `PdfSurvey`; the PyMuPDF probe, `PROBE_VERSION`, the facts
  summary and `pdf_facts.json` (write and reuse); the generic prompt and
  `PROMPT_VERSION`; checks C1–C7; the comparison with the facts; the agent,
  output validator, merge, fingerprint and reuse.
- **Report** — `report.html`, page images and their manifest.
- **Configuration** — `Config` and `AdvancedConfig`, file loading, precedence,
  error formatting; `ProviderEnv` (pydantic-settings, environment only, built
  per run).
- **Costs** — ledger entry and `CostEstimate` schemas, the ledger, pricing
  (PydanticAI's cost calculation plus `advanced.models` overrides), the
  estimate, the `max_cost` guard.
- **Models** — provider profiles (PDF transports, upload purpose, upload expiry
  range, PDF tokens-per-page estimate, effort mapping); the SDK clients with the
  retry count and timeout; `build_model`, provider settings and `LedgerModel`;
  Files API upload, reuse and the `uploads.json` record; the in-request
  fallback; turning provider errors into `ProviderError`.
- **General utilities** — atomic write, validated load and temp cleanup (UTF-8
  for every text read and write); opening a PDF (SHA-256, page count, size,
  `PdfError`); canonical-JSON fingerprints; running a coroutine from sync code
  (decision 14).
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
  - `languages` (list of BCP-47 tags, checked and kept in standard form as in
    decision 15; default empty). A rejected tag is an invalid setting named by
    its position and value (`languages[1]: "zz"`).
  - `output_dir` (path; default `./pydelity-output/<pdf stem>/`).
  - `model` (`<provider>:<model-id>`; default `anthropic:claude-opus-5-5`).
  - `max_cost` (positive decimal USD or null; no default).
  - `overwrite` (bool; default false).
- `advanced.provider_retries`: integer 0–10, default 2 (decision 13). It is not
  part of any fingerprint.
- `advanced.survey`: `check_retries` (0–5, default 2), `effort` (`low` |
  `medium` | `high`, default `high`), `max_output_tokens` (default 32000),
  `request_timeout_seconds` (default 900).
- `advanced.uploads.expiry_hours`: integer hours or null (default null, meaning
  the provider's maximum). It must lie within the selected provider's allowed
  range (Anthropic: 1 to 2160 hours), checked with the other settings before any
  upload. It is not part of any fingerprint.
- `advanced.models.<provider:model-id>`: prices only: `input_usd_per_mtok` and
  `output_usd_per_mtok` (required in an entry), `cache_read_usd_per_mtok` and
  `cache_write_usd_per_mtok` (default: the input price). An entry replaces
  PydanticAI's cost calculation for that model. There are no limit settings.
- Precedence: CLI options or Python keyword settings > config file > defaults.
  The CLI's `PDF` argument wins over the file's `pdf` (AC-008).
- Environment (`ProviderEnv`, read only when a run needs a provider):
  `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` as `SecretStr`. The key for the selected
  provider must be non-empty before any model call. pydelity loads no `.env`
  file; the provider SDKs' own `ANTHROPIC_BASE_URL` / `OPENAI_BASE_URL` are
  honoured (the test seam). `.template.env` is reduced to the two keys pydelity
  reads.
- Errors: `ConfigError` lists every invalid setting by dotted path
  (`advanced.survey.check_retries`) with the reason, collected in one pass
  (Pydantic errors plus file, path and key checks), raised before any model
  call.

### CLI

- `pydelity [PDF] [--config/-c FILE] [--instructions TEXT] [--language TAG]... [--output-dir DIR] [--model MODEL] [--max-cost USD] [--overwrite] [--yes/-y] [--verbose/-v | --quiet/-q] [--version]`.
  Console script `pydelity`, pointing at the CLI module's entry function.
- Flow: resolve and validate config → open the PDF → prepare the output folder →
  measure or reuse the facts, write `pdf_facts.json` and log its summary → plan
  (which steps run or are reused) → if a model call is planned: check the API
  key; print the estimate, spend so far in the folder and `max_cost`; when the
  plan-time `max_cost` check trips, log the `max_cost_exceeded` warning first →
  confirm (`--yes` proceeds; an interactive stdin prompts, default No, and a yes
  also allows going over `max_cost` for this run; a non-interactive stdin stops
  with a message to pass `--yes`) → model calls; if a per-request `max_cost`
  check trips, log the warning and ask again (default No; `--yes` continues
  without asking) → print the summary (status, cost this run by step, folder
  total, review issue count and the first issues with step, page and check,
  output paths, report path). Every step after "prepare the output folder" runs
  inside the run, which calls back into the CLI for its questions (decision 12).
- A run that ends on `ProviderError` prints the provider's message as given,
  prefixed by the provider and model, plus the PDF's name, pages and size when
  the failed call carried the PDF.
- Exit codes: `0` completed (review issues allowed); `1` failed (provider error,
  survey error, unexpected error); `2` invalid settings, a missing API key or an
  unreadable PDF; `3` stopped by the user's answer or by a non-interactive run
  without `--yes`, before spending or at a `max_cost` question mid-run; `130`
  interrupted.
- Logging: loguru to stderr at INFO, DEBUG with `--verbose`, WARNING with
  `--quiet`. User-facing warnings are printed regardless of level.

### Python API

- In every function below that takes them, `config` is a path, a `Config` or a
  mapping, and `settings` uses the top-level setting names (`advanced` as a
  mapping). Every function validates the whole configuration the same way, so an
  invalid setting raises `ConfigError` even where the function does not use it.
- `measure(pdf=None, *, config=None, **settings) -> PdfFacts` — prepares the
  output folder, then measures or reuses the facts and writes `pdf_facts.json`
  as in step 4 of **Data and Control Flow**, and returns them. Uses only `pdf`,
  `output_dir` and `overwrite`; no API key, no model call, no `run.json`, no
  report.
- `estimate(pdf=None, *, config=None, **settings) -> CostEstimate` — no model
  call, nothing written.
- `survey(pdf=None, *, config=None, allow_over_max_cost=False, **settings) -> PdfSurvey`
  — step 1 only: writes `pdf_facts.json`, `pdf_survey.json` and ledger lines,
  not `run.json` or the report.
- `run(pdf=None, *, config=None, allow_over_max_cost=False, **settings) -> RunResult`
  — the whole pipeline (this cycle: the survey), writes `run.json` and the
  report.
- `ameasure`, `aestimate`, `asurvey`, `arun` — the same functions as coroutines,
  with the same arguments, results, errors and warnings (decision 14).
  Cancelling `asurvey` or `arun` is handled like Ctrl+C: `arun` records
  `interrupted` in `run.json`, every written file stays valid, and
  `CancelledError` propagates. Calls on different output folders may run
  concurrently, in one event loop or in several threads.
- `load(output_dir) -> RunResult` — reads an output folder back, with no model
  call, no API key and nothing written. Each part is `None` (or an empty ledger)
  when its file is absent, so a folder that only `measure` or `survey` wrote
  also loads. It raises `OutputError` when the folder does not exist, holds none
  of `pdf_facts.json`, `pdf_survey.json`, `run.json` and `cost.jsonl`, or holds
  one that is not valid JSON, fails its schema or has a different
  `schema_version` major version. Output models ignore fields they do not know,
  so a `1.x` file written by a newer pydelity loads. A damaged trailing
  `cost.jsonl` line is skipped with a `damaged_output` warning, as everywhere.
- Result models: `PdfFacts` (the contents of `pdf_facts.json`), `PdfSurvey` (of
  `pdf_survey.json`), `CostEstimate`, and `RunResult`: `output_dir`, `record`
  (`RunRecord`, the contents of `run.json`, or `None`), `facts` (`PdfFacts` or
  `None`), `survey` (`PdfSurvey` or `None`), `ledger` (the `cost.jsonl` entries
  in order). `run` returns a `RunResult` with every part set, as `load` would
  read it from the folder afterwards.
- `allow_over_max_cost` is a function argument, not a setting: it is not in
  `Config`, config files or the fingerprint. `True` lets the call continue past
  `max_cost` after the warning; `False` makes a tripped `max_cost` check raise
  `BudgetExceededError` (decision 11).
- Never prompts. Problems raise `ConfigError`, `PdfError`, `MissingApiKeyError`,
  `BudgetExceededError`, `ProviderError`, `SurveyError`, `OutputError` (all
  `PydelityError`). `SurveyError` covers a survey answer that never parses after
  the check retries and a model refusal. User-facing warnings (each `run.json`
  warning code) use `warnings.warn` with `PydelityWarning`, are logged through
  loguru at WARNING, and are recorded in `run.json` when the function writes
  one. Calling a sync function inside a running event loop is a usage error and
  raises `RuntimeError`, the type `asyncio.run` itself raises there, not a
  `PydelityError` (decision 14).

### Providers and models

- Provider profiles, the only model-related data pydelity ships, one per
  supported provider: the PDF transports under the policy in decision 4 (both
  providers: upload, then in-request fallback); the upload purpose where the
  provider needs one (OpenAI: `user_data`); the allowed upload expiry range with
  its maximum as the default (Anthropic: 1 to 2160 hours; OpenAI: Developer
  checks); a PDF tokens-per-page figure for the cost estimate (a named constant
  that Developer derives from the provider's PDF documentation and documents in
  the reference); the `effort` mapping.
- No per-model entries: no page, size or context-window limits, no
  `limits_source`, no list of models. Any `anthropic:` or `openai:` model ID is
  accepted and sent as given; the provider decides whether the model exists and
  accepts the PDF and the settings.
- The docs name the default model and at least one OpenAI model that accepts PDF
  input and `reasoning_effort` (Developer picks the current OpenAI model
  recommended for document input; Documenter names both).
- Provider errors (AC-037): any provider error that ends a run raises
  `ProviderError`: a model request that fails after the provider retries
  (decision 13), an upload error that stops the run (decision 4), or an
  in-request fallback that the provider rejects. It carries `provider`, `model`,
  `status_code` (null for a connection error or timeout), `provider_message`
  (the provider's own message from its error body when present, otherwise the
  exception's text, never reworded), `upload_error` (the earlier upload error
  after a fallback, else null) and `temporary` (true when the failure is of a
  kind the SDK retries: connection error, timeout, HTTP 408, 409, 429 or 5xx),
  with the SDK or PydanticAI exception as `__cause__`. Its message starts with
  the provider and model and then `provider_message`, adds the PDF's name, pages
  and size when the failed call carried the PDF, and, when `temporary`, says the
  request failed after `advanced.provider_retries` retries (naming the count and
  the setting). A rejected PDF is one such error, whatever the reason (too
  large, too many pages, over the context window, unreadable). The run ends
  `failed`; nothing is retried with a smaller PDF.

### `pdf_facts.json`

All pydelity JSON outputs carry `schema_version` as a `"MAJOR.MINOR"` string
(this cycle `"1.0"`; additive changes bump the minor, breaking changes the
major) and `pydelity_version`. All bounding boxes in stored outputs are PDF
points in the displayed (rotation-applied) page space, origin top-left,
`[x0, y0, x1, y1]`. Page indexes are 0-based.

The survey's measured facts and their summary, saved right after measuring and
before any API key check, cost question or model call (AC-040). It is a
permanent output: pydelity never deletes it, and only a new measurement replaces
it (atomically).

- `fingerprint` — `"sha256:<hex>"` of the canonical JSON of: PDF SHA-256,
  `PROBE_VERSION`, facts `schema_version`. `PROBE_VERSION` is a named constant
  bumped whenever a measurement rule, a measurement constant or the summary
  format changes, so an upgraded pydelity measures again.
- `probe_version`, `measured_at`, `pdf` (`name`, `sha256`, `bytes`,
  `page_count`).
- `summary[]` — the facts summary as plain-text lines, built deterministically
  from `facts`: page count; pages with no text and with garbled text; inline
  direction and vertical writing; pages whose measured orientation is not 0, as
  ranges; measured page-numbering ranges; repeated lines (count and the most
  frequent); bookmarks; form fields (count, AcroForm, XFA); structure-tag
  quality; unreadable facts. The same lines are logged at INFO, form the facts
  part of the survey prompt, and head the report's facts section. Developer sets
  the wording.
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

### `pdf_survey.json`

- `fingerprint` — `"sha256:<hex>"` of the canonical JSON (sorted keys, no
  whitespace) of: PDF SHA-256, the `pdf_facts.json` fingerprint, resolved
  `model`, `instructions`, `languages`, `advanced.survey` values
  (`check_retries`, `effort`, `max_output_tokens`), `PROMPT_VERSION`, survey
  `schema_version`. Excludes `max_cost`, `allow_over_max_cost`, `overwrite`,
  `output_dir`, `advanced.provider_retries`, `request_timeout_seconds` and
  prices.
- `inputs` — `pdf_name`, `pdf_sha256`, `pdf_bytes`, `page_count`,
  `facts_fingerprint`, `model`, `instructions`, `languages`, survey settings,
  `prompt_version`.
- `facts` — a copy of the `facts` object of the `pdf_facts.json` this survey
  used (AC-001), so `pdf_survey.json` stands alone.
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
    present, all in standard form (decision 15), so the comparison is exact.
    Model tags that C7 still rejects after the check retries are left out.
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
  (names the check and what is wrong), `details` (object with the proposed value
  and, where it applies, what it was checked against, such as the page count). A
  failure that concerns several pages is one item per page, so ranges that
  overlap on 30 pages give 30 items.
- `issues[]`: review issues from this step: one per failure item of the accepted
  answer (its `page_index`, `message` and `details`, with `check` the check
  name), then one per disagreement with the facts (with `check` the comparison
  name), each with `step` (`"survey"`); the same shape as `run.json` `review[]`.
- Model-facing proposal schema: a separate Pydantic model using only strings,
  integers, booleans, enums, arrays and objects (no pattern, length or numeric
  bounds) so it fits both providers' structured-output subsets; bounds are
  checked in Python. Region boxes are fractions (0–1) of the displayed page;
  Python converts them to points.

### Checks (names are part of the `run.json` contract)

Each check tests that the answer is well formed and complete (AC-045). None
compares the answer with a measured value (AC-046).

- `labels` (C1): names non-empty and unique (case-insensitive), every label has
  at least one kind, every region names an existing label.
- `regions` (C2): valid page index; box within 0–1 with `x0 < x1`, `y0 < y1`.
- `rotation` (C3): ranges inside the PDF and non-overlapping.
- `page_numbering` (C4): ranges inside the PDF and non-overlapping.
- `artifacts` (C5): every probe repeated-line ID appears exactly once, in an
  artifact or in `non_artifact_lines`; no unknown IDs.
- `writing_direction` (C6): ranges inside the PDF and non-overlapping.
- `languages` (C7): the model's list has at least one tag, and `langcodes`
  accepts every tag (decision 15; `zxx` allowed). One failure item per rejected
  tag (`details`: `{"proposed": "<tag>"}`), or one for an empty list
  (`{"proposed": []}`); `page_index` is null.

### Disagreements with the facts (names are part of the `run.json` contract)

Python compares the accepted answer with the facts once, after the output
validator accepts it (AC-046). The comparison never raises `ModelRetry`, never
changes the profile and runs the same whatever the instructions and languages. A
page can disagree only where the probe measured a value. Where it measured
nothing (no text layer, text inside images, an orientation that is not
confident, no printed number found), the profile stands with no issue. The
profile's value for a page comes from the first range in the answer that covers
it, ignoring ranges outside the PDF. Each disagreement is one review issue with
the page's `page_index`, a `message` naming the page, the measured value (with
the printed text for a page number) and the profile's value, and these
`details`:

- `rotation_differs`: on a page whose measured orientation is confident, the
  profile's degrees (0 when no range covers the page) differ from the measured
  `dominant`. `details`: `measured`, `profile` (such as
  `{"measured": 90, "profile": 0}`).
- `page_number_differs`: on a page whose measured printed number has a `value`,
  the profile's number for the page differs from it. The profile's number is
  `index + offset` when a range with style `arabic` or `roman` and an offset
  covers the page, and null otherwise (no range, style `other` or `none`, or a
  null offset). `details`: `measured`, `profile` and `source` (the printed
  number's `page_label` or `text`), such as
  `{"measured": 12, "profile": null, "source": "text"}`.

Disagreements are not check failures: they are not in `checks[]`, and a survey
with only disagreements has every check passed.

### `run.json`

- `schema_version`, `pydelity_version`, `run_id` (UTC timestamp plus random
  suffix), `status` (`running` | `completed` | `failed` | `stopped` |
  `interrupted`), `started_at`, `ended_at`, `pdf` (`path`, `sha256`,
  `page_count`, `bytes`), `settings` (resolved, no secrets), `steps[]` (`name`,
  `status`: `completed` | `reused` | `failed` | `stopped` | `skipped`, `outputs`
  (the files the step wrote or reused, by name; the survey lists
  `pdf_facts.json` as soon as it exists, then `pdf_survey.json`), `requests`,
  `cost_usd`, `pdf_transport` (`upload` | `request` | null when no PDF was
  sent), `started_at`, `ended_at`, `error`), `cost` (`run_usd`, `by_step`,
  `output_folder_usd`, `unpriced_requests`), `review[]`, `warnings[]`, `error`.
- Warning item: `code`, `step` (or null), `message`, `details` (object). Codes
  this cycle: `unpriced_model`, `max_cost_exceeded`, `other_pdf_in_folder`,
  `damaged_output`, `upload_fallback`, `probe_unavailable`. The same message
  goes to `PydelityWarning` in Python and to the CLI. `max_cost_exceeded`
  details: `max_cost`, `spent_usd` (recorded in the folder before the check),
  `projected_usd` (the spend the run expects to reach: `spent_usd` plus the
  run's estimated maximum at plan time, or plus the request's upper bound before
  a request; null when the model is unpriced), `check` (`plan` | `request`),
  `allowed` (the decision). The CLI summary groups review issues by check and
  shows a count per check before listing them.
- Review issue: `step`, `check` (a check or comparison name), `page_index` (null
  when none applies), `message`, `details` (object). The run's review list holds
  the issues of every step output used by the run, reused ones included.
- Written at start (`running`) and at the end; on Ctrl+C or when `arun` is
  cancelled, the pipeline catches `KeyboardInterrupt` or `CancelledError`,
  writes `interrupted`, and re-raises.

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

### Cost estimate and `max_cost`

- `CostEstimate`: per planned step `name`, `model`, `reused`, `requests_max`,
  `expected_usd`, `max_usd`; totals; `spent_usd` (folder ledger); `max_cost`;
  `priced`; `over_max_cost` (the plan-time check: `max_cost` is set and either
  `spent_usd` + total `max_usd` > `max_cost` or the model is unpriced);
  `warnings`.
- Input tokens per request ≈ `page_count` × the provider's PDF tokens-per-page
  figure + prompt characters ÷ 4. Expected = one request with a typical output
  (a named constant). Maximum = `(1 + check_retries)` requests, each with
  `max_output_tokens` of output and the previous answer added to the input.
  Constants are named and documented in the reference.
- `max_cost` guard (decision 11), shared by every step: the plan-time check uses
  `over_max_cost`; the per-request check, run by `LedgerModel` before each
  request while the run has not been allowed over, trips when `spent_usd` (the
  whole folder ledger at that moment) + that request's upper bound > `max_cost`.
  A tripped check records the `max_cost_exceeded` warning and calls the run's
  over-`max_cost` decision once; later checks in that run reuse the answer. The
  decision is an internal callable passed into the run: the public API passes
  one that returns `allow_over_max_cost`, and the CLI passes one that returns
  true with `--yes` and otherwise asks on the terminal. The guard serialises the
  question so concurrent requests in later steps ask once, and runs a terminal
  question off the event loop. A no raises `BudgetExceededError` before the
  upload or request; the run ends `stopped`, and its message says how to
  continue (a higher `max_cost`, `--yes`, or `allow_over_max_cost=True`).
  Without `max_cost`, there is no check, and unpriced requests are recorded with
  null cost and an `unpriced_model` warning.

### HTML report

- `report.html` plus `report/pages/<NNNN>.<jpg|png>` (4-digit 0-based index,
  about 1000 px wide), rendered by PyMuPDF; images are re-rendered only when
  missing or when `report/manifest.json`'s PDF SHA-256 differs.
- Content: run header (PDF, status, model), cost (this run by step, folder
  total), review list, profile, facts (the `pdf_facts.json` summary lines, then
  bookmarks, form fields, structure quality, repeated lines with their artifact
  mapping), then one card per page: image with region and form-field boxes as
  CSS overlays positioned in percent, page findings (text quality, orientation,
  direction, printed number, profile rotation, repeated lines, issues on that
  page).
- Static HTML: no JavaScript requirement, no external URLs, every inserted
  string HTML-escaped. Written at the end of every run that got past input
  validation, whatever its status, with the data available.

### Test seam

- Provider SDKs read `ANTHROPIC_BASE_URL` and `OPENAI_BASE_URL`; tests and the
  wheel smoke script point them at a loopback mock server that returns canned
  provider responses, including both providers' Files API upload, the "file not
  found" answer that triggers a re-upload, upload failures that trigger the
  in-request fallback, an upload rejected as too large (413), and error
  responses that reject the PDF on the request, and temporary failures (429 and
  5xx with a short `retry-after-ms` header, which both SDKs honour, so retry
  tests do not wait) on the model request and on the upload. No production code
  path exists only for tests.
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
  (configuration, CLI, Python API, `pdf_facts.json`, `pdf_survey.json`,
  `run.json`, `cost.jsonl`, `uploads.json`, survey checks), produced by
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
   empty or unopenable PDF raises `PdfError` naming the file and the reason. No
   size or page check follows.
3. Prepare the output folder: create it, remove stale `*.tmp-*` files, warn
   (`other_pdf_in_folder`) if an existing `run.json` or `pdf_facts.json` names a
   different PDF SHA-256; `run` also writes `run.json` (`running`). `measure`
   stops after step 4.
4. Facts (decision 12): load `pdf_facts.json` if present; invalid JSON or schema
   → `damaged_output` warning and treat as absent; matching fingerprint and no
   `overwrite` → reuse; otherwise run the probe, build the summary and write
   `pdf_facts.json` atomically. Log the summary at INFO either way and add a
   `probe_unavailable` warning per `probe_errors` item. Nothing before this
   point needs an API key or contacts a provider.
5. Plan the survey: load `pdf_survey.json` if present; invalid JSON or schema →
   warn and treat as absent; matching fingerprint (which includes the facts
   fingerprint) and no `overwrite` → reuse.
6. If the survey runs: check the provider key; estimate; the plan-time
   `max_cost` check and its decision (decision 11); CLI confirmation (Python
   skips it); reuse the PDF's upload from `uploads.json` if it has at least an
   hour left, otherwise upload it and record it; build the agent through
   `build_model`; run it; each request passes the per-request `max_cost` check
   and is written to the ledger; the output validator runs C1–C7 and retries or
   accepts as in decision 5; Python adds `other`, merges user languages, stores
   `user_instructions`, converts region boxes, copies the facts in, compares the
   profile with the facts and adds a review issue per disagreement; write
   `pdf_survey.json` atomically. If the provider answers that the recorded file
   no longer exists, upload again once, replace the record and retry the
   request. When the upload path fails (decision 4), send the PDF inside the
   request instead. A provider rejection of the PDF on any path raises
   `ProviderError`.
7. Assemble `run.json` (steps, cost from the ledger, review list, warnings),
   write the report, print the CLI summary.
8. Any exception after step 3, cancellation included, records `failed`,
   `stopped` or `interrupted` in `run.json` and still writes the report before
   re-raising. A stopped, failed or interrupted survey writes no
   `pdf_survey.json`; the next run redoes it, with the earlier spend already in
   the ledger and counted against `max_cost`. `pdf_facts.json`, once written,
   stays and is reused by that next run.

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
  - Printed numbers: when the document defines page labels, the number at the
    end of the page's label, after any prefix (`12`, `Page 12`, `A-iv`), as
    decimal digits in any script or a roman numeral; a label that ends in no
    number is kept with style `label` and a null `value`. On a page with no
    label number, a line in the top or bottom band that is a single number in
    any script's decimal digits (Python `int()` on `str.isdecimal()` text) or a
    roman numeral, with only non-letter decoration around it. Ranges of constant
    `printed − index` form `page_numbering`.
  - Repeated lines: remove invisible formatting characters (Unicode category
    Cf), then normalise (NFKC, case fold, collapse whitespace, decimal digits →
    `#`); a line with nothing visible is never repeated. A normalised line
    counts once per page and is repeated when it appears on at least 3 pages and
    at least 5% of pages (2 pages when the PDF has 2 or 3 pages); at most 1,000,
    most frequent first, with `repeated_lines_truncated` set when capped.
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
- `AC-045`: Each failing check produces a `ModelRetry` message naming the check
  and what is wrong while retries remain; after the last allowed attempt, every
  still-failing check appears in `pdf_survey.json` `issues` and in the run's
  review list with `step: "survey"`, the check name and the page where one
  applies. An answer that leaves out a repeated-line ID, gives one twice or
  names one the probe did not find fails C5. The request text holds every
  repeated line's ID.
- `AC-046`: A well-formed answer whose rotation or page numbering differs from
  the facts passes C1–C7 and is accepted after one request, with no check retry.
  The stored profile keeps the model's rotation and page numbering unchanged,
  and the review list has one `rotation_differs` or `page_number_differs` issue
  per page that differs, with its `page_index` and the measured and profile
  values in `details`. A page with no confident orientation or no measured
  number gets no such issue. The prompt presents the facts as hints and asks the
  model to answer with its own reading where they differ.
- `AC-004`: Instructions and languages appear in the prompt and in `profile`;
  the checks and the comparison with the facts run identically with and without
  them; no setting skips either.
- `AC-006`: Core code, prompts, schema field names, defaults and checks contain
  no document-type or domain words and no natural-language word lists; language
  handling uses Unicode properties only, and language tags are checked against
  the IANA registry that `langcodes` bundles. Prompt examples, if any, use
  neutral placeholders.
- `AC-045`, `AC-004`, `AC-009`: The `languages` values `en_US`, `EN-us` and
  `en-US` all resolve to `en-US` in the resolved settings, the survey
  fingerprint and the profile; `zz` or `en-` in the setting raises `ConfigError`
  naming its position and value before any model call. A model answer whose
  languages include `zz` fails C7 for that tag; after the last check retry, `zz`
  is absent from the stored profile and a review issue names it.
- `AC-007`, `AC-010`: `import pydelity` performs no file, network or environment
  reads and produces no output on stdout, stderr or loguru sinks.
- `AC-041`: With the mock provider answering a model request with temporary
  failures, the request is sent exactly `1 + advanced.provider_retries` times
  (for 0 and for a value above 2), then the CLI exits 1 printing the provider's
  message and the Python API raises `ProviderError` with `temporary` true; with
  fewer failures than that, the survey completes. A non-temporary error (such
  as 400) is sent once. Uploads follow the same count before the fallback.
  Retries never add ledger lines.
- `AC-042`: `measure` with no API key in the environment and the mock provider
  unreachable writes a valid `pdf_facts.json` and returns a `PdfFacts` equal to
  its contents; a second call with the same inputs measures nothing and returns
  the same result.
- `AC-043`: `load` on the folder of a completed run returns a `RunResult` equal
  to the one `run` returned, with no API key and no network; on a folder that
  only `measure` wrote it returns the facts and `None` elsewhere; on a missing
  folder or a corrupt file it raises `OutputError` naming the file.
- `AC-044`: Each async function, awaited inside a running event loop, gives the
  same result, errors and `PydelityWarning`s as its sync form. Each sync
  function called while an event loop is running in its thread raises
  `RuntimeError` naming the async function to await, writes nothing and leaves
  no "coroutine was never awaited" warning; `load` works there. Two `asurvey`
  calls on different folders run concurrently in one loop. The event loop stays
  responsive while `ameasure` measures. Cancelling `arun` leaves `run.json`
  `interrupted` and every file valid.
- `AC-009`: Every invalid setting in a single input is reported in one error; no
  model request happens.
- `AC-011`: Both providers pass the same survey flow with their canned responses
  through the real PydanticAI provider adapters.
- `AC-014`: The ledger has one line per returned response; `run.json`
  `cost.by_step` and `run_usd` equal the sums of this run's ledger lines;
  `output_folder_usd` equals the whole ledger.
- `AC-015`: No request happens before confirmation in the CLI; a non-interactive
  stdin without `--yes` exits 3 before spending; the Python API never reads
  stdin.
- `AC-037`: pydelity's code and data hold no per-model page, size or
  context-window figure, and nothing compares the PDF with one. A PDF the mock
  provider rejects (on the upload with 413, or on the request) ends the CLI run
  with exit code 1 and the provider's message printed unchanged, and makes the
  Python API raise `ProviderError` whose `provider_message` equals the
  provider's message and whose `__cause__` is the original exception; `run.json`
  records `failed` and every written file is valid.
- `AC-038`: With `max_cost` set below the recorded folder spend plus the run's
  estimated maximum, the CLI logs one `max_cost_exceeded` warning naming
  `max_cost` and `projected_usd` before any upload or request, and asks once:
  yes completes the run with no further question; no, or a non-interactive stdin
  without `--yes`, exits 3 with `run.json` `stopped` and nothing sent; `--yes`
  completes without asking. When only a per-request check trips, the same
  warning and question come before that request is sent. Spend recorded by
  earlier runs in the folder counts in every check.
- `AC-039`: Under the same conditions, the Python API issues the warning as
  `PydelityWarning`, logs it, and never reads stdin. With
  `allow_over_max_cost=True` the run completes; without it,
  `BudgetExceededError` is raised before the upload or request, the run is
  `stopped` with every written file valid, and a later call with
  `allow_over_max_cost=True` or a higher `max_cost` completes without discarding
  recorded spend.
- `AC-038`, `AC-039`: With `max_cost` set and an unpriced model, the plan-time
  check trips (`projected_usd` null); without `max_cost`, no check runs and no
  question is asked.
- `AC-017`: A rerun with identical fingerprint inputs sends no request and
  measures nothing; changing any fingerprint input or setting `overwrite` sends
  requests; a changed `PROBE_VERSION` measures again and reruns the survey.
- `AC-040`: `pdf_facts.json` exists, is valid and holds the facts and summary
  after a run with no API key, a declined or non-interactive confirmation, a
  `max_cost` no and a provider error, in both the CLI and the Python API. It is
  written before the API key check, the estimate output and any question, upload
  or request, and its summary lines are logged at INFO. A completed survey's
  `pdf_survey.json` `facts` equals that file's `facts`, and its
  `inputs.facts_fingerprint` equals that file's `fingerprint`.
- `AC-018`: No output file exists in a partial state at any point; a corrupt or
  schema-invalid `pdf_facts.json` or `pdf_survey.json` is regenerated; stale
  temp files are removed; an `uploads.json` record is written only after its
  upload succeeded, and a damaged `uploads.json` is treated as empty (the PDF is
  uploaded again).
- `AC-019`: Review issues carry step, check and page (or null); the CLI summary
  shows their count and entries.
- `AC-020`: The report opens from disk with no network access and shows every
  page image with its findings and region boxes, the profile, the run's cost and
  the review list.
- `AC-021`: The test suite runs with no route to a provider; both providers'
  response shapes, both providers' Files API uploads, upload reuse from
  `uploads.json`, re-upload after "file not found", the in-request path, the
  fallback after an upload failure, the stops on an authentication failure and
  on a 413 upload, a provider rejecting the PDF on the request and on the
  fallback, and every `max_cost` answer (CLI yes, no, `--yes` and
  non-interactive; Python with and without `allow_over_max_cost`) are exercised,
  as are provider retries and every public function in its sync and async form.
- `AC-011`, `AC-018`: A survey whose upload fails for a reason other than
  authentication or 413 completes through the in-request path when the provider
  accepts the in-request PDF, with a warning and `pdf_transport: "request"` in
  `run.json`, and writes no `uploads.json` record.
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
   configuration, general utilities (atomic files, fingerprints, running a
   coroutine from sync code) and the provider profiles. Must land together so
   the package imports and the strict editable install still passes the existing
   smoke tests.
2. **PDF and probe** — `CANDIDATE` modules for opening PDFs, the facts schemas
   and enums, the probe, the facts summary and `pdf_facts.json`; test PDF
   fixtures (real public-domain documents the user approves, each committed one
   under the 500 KB hook limit, including a tagged PDF).
3. **Cost and model layer** (parallel with 2) — `CANDIDATE` modules for the
   ledger, pricing, estimate and `max_cost` guard; the SDK clients with the
   retry count, `build_model`, provider settings and `LedgerModel`; Files API
   upload, reuse and the `uploads.json` record; the in-request fallback;
   `ProviderError` mapping.
4. **Survey step** — `CANDIDATE` modules for the prompt, checks, proposal and
   profile schemas, and the step (agent, validator, fingerprint, reuse). Depends
   on 2 and 3.
5. **Run, report, API, CLI** — `CANDIDATE` modules for run orchestration, the
   report, the API functions (async functions, their sync wrappers, `measure`
   and `load`) and the CLI; canned provider responses for tests. Critical path:
   1 → 2 → 4 → 5.
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
- Provider limits, prices and model IDs drift. pydelity ships no per-model data,
  so limits are the provider's to enforce (AC-037) and prices follow
  `genai-prices` releases, with `advanced.models` covering the gap. The
  `genai-prices` data in the KGForEdGlobal environment lists `claude-opus-5` but
  not `claude-opus-5-5`. Developer sets a `genai-prices` minimum version that
  prices the default model; if no release does, Developer routes the default
  model choice back to Architect rather than shipping a price.
- With no pre-call check, a PDF too large for the provider costs one rejected
  upload and, unless the upload was rejected with 413, one rejected in-request
  attempt before the error; rejected calls return no usage and are not billed.
  If a provider reports "too large" on upload with another status, the
  in-request attempt sends the PDF a second time.
- Older models that reject adaptive thinking, `effort` or `reasoning_effort`
  fail with the provider's error; supporting them would need per-model data.
- Uploaded PDFs stay in the user's provider file storage until they expire: by
  default the provider's maximum (90 days on Anthropic), and they count against
  the organization's storage (Anthropic: 1 TB). Anthropic's expiry range is
  documented (1 hour to 90 days). OpenAI's upload expiry and its allowed range
  were not confirmed (its API reference page could not be read), so Developer
  checks them. If OpenAI offers no expiry, its uploads persist until the user
  deletes them, and `expiry_hours` set for OpenAI is an invalid setting. The
  docs must say that PDFs are uploaded to and stored by the provider, for how
  long, and how to shorten it (Documenter).
- The token estimate is a heuristic with conservative upper bounds: the
  `max_cost` question can come for a run that would have fitted, and rarely
  mid-run when real usage beats the estimate.
- Non-streaming requests with large `max_output_tokens` need an explicit request
  timeout (the Anthropic SDK refuses long non-streaming requests otherwise). If
  Developer switches to streaming, `LedgerModel` must wrap the streaming request
  path too.
- A request that times out on pydelity's side may still finish, and be billed,
  at the provider. pydelity sees no usage for it, so it has no ledger line; with
  provider retries, each timed-out attempt can add such unseen cost.
- The IANA registry inside `langcodes` is fixed per release: a tag registered
  later is rejected until `langcodes` is upgraded, and a release that changes a
  tag's standard form changes the survey fingerprint for runs that use it, so
  the survey runs again.
- With the model's reading kept, a probe mistake no longer reaches the profile,
  but it does reach the review list: numbers in table cells taken for page
  numbers, or page labels that number pages printing none (a cover labelled 1),
  give one `page_number_differs` issue per page. `source` tells label numbers
  from text numbers. Keeping page labels as a separate fact from the printed
  text would cut that noise; it changes the facts schema, so it is left for a
  later cycle if review lists show it matters.
- The model can also be wrong where the facts were right. The review list is the
  only signal, so users should read the `rotation_differs` and
  `page_number_differs` issues; the docs say so (Documenter).
- Every repeated line is sent with the request and must be accounted for, so a
  PDF near the 1,000-line cap adds input and output tokens to each request.
- In Jupyter and other async code the sync functions raise, so users there
  `await` the `a` functions (Jupyter allows top-level `await`). The docs show
  both forms and say which to use where (Documenter).
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
- Later cycles: steps 2–6 reuse `build_model`, `LedgerModel`, the `max_cost`
  guard, atomic files, fingerprints, review issues and the report; they add
  `pages`, `schema` and per-step `advanced:` settings and extend the default
  run. Other PydanticAI providers can be added later by extending the provider
  allowlist, the model factory and the provider profiles; this cycle supports
  only Anthropic and OpenAI.

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
- Facts only inside `pdf_survey.json` (the earlier design): one file fewer, but
  the facts are lost whenever the survey does not finish; the user chose a
  separate file. Dropping `facts` from `pdf_survey.json` instead of copying them
  would contradict AC-001.
- A shipped per-model catalog of PDF limits with a pre-call check (the earlier
  design): clearer errors before any upload, but the user ruled it out as not
  maintainable; providers enforce their own limits (AC-037).
- Stopping at `max_cost` (the earlier design): replaced by the user's rework;
  the run warns and the user or caller decides.
- Checking `max_cost` only at plan time: misses runs whose real usage beats the
  estimate. Asking before every request instead: too many questions; one answer
  covers the rest of the run.
- Counting cost from `result.usage()` after each agent run: loses per-request
  detail and cannot check before a request; the model wrapper does both.
- Checks outside PydanticAI in a hand-written retry loop: more code, and the
  output validator already gives retries with conversation history and a
  last-attempt signal.
- A second model that verifies the survey answer: excluded by the scope; the
  Python checks test the answer's form and the comparison flags differences from
  the facts for review.
- Checks that send an answer back when its rotation or page numbering differs
  from the facts (the earlier design): they made the model agree with probe
  mistakes, such as numbers in table cells taken for page numbers. The user
  chose the model's reading, with differences on the review list.
- Flagging pages where the model reports a value the probe did not measure (such
  as a page number in an image): the facts have nothing to disagree with there,
  and a scanned PDF would get an issue on every page.
- Separate retry counts for uploads and model requests, or per step: more
  settings for little gain; one count covers every request to the provider.
  Retrying in pydelity (or with PydanticAI's optional retry transport) instead
  of the SDKs: duplicates the SDKs' handling of `retry-after` and risks retrying
  more often than the setting allows.
- A sync core with async functions that run it in a worker thread: simpler, but
  PydanticAI is async already, and an async core lets later steps send requests
  concurrently in one loop.
- Sync functions that run the coroutine on a worker thread when an event loop is
  already running (the earlier design): they would work in Jupyter, but they
  block that loop while they run and need warnings carried back from the thread.
  The user chose `asyncio.run` only, with an error that points to the async
  function.
- An async `load` (`aload`): it would only wrap a few small file reads.
- Reusing `advanced.survey.max_retries` as the name for check retries: two
  settings called retries for different things invite mistakes, so the survey's
  is `check_retries`.
- Required checks for each new CI job: needs a ruleset change the repo cannot
  make; the gate job keeps the existing required check name.
- npm instead of pnpm for the docs: departs from IDinsight/standards and
  produces a larger lock file.
- A hand-written BCP-47 pattern for language tags (the earlier design): no
  dependency, but it accepts well-formed tags that no registry defines (such as
  `zz`) and leaves spelling variants unmerged; the user chose `langcodes`.
- Hand-written reference pages: drift from the code; generation makes AC-032
  checkable.

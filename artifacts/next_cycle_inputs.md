# pydelity: inputs for the page extraction cycle (step 2)

The survey, step 1 of the pipeline, was scoped, built, reviewed and signed off
on 2026-11-19 in the STANDARDS cycle
`build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c` (branch
`tz6/pipeline`), and ships as pydelity 0.1.0. STANDARDS was then uninstalled so
the work could merge to `main`, which removed that cycle's records. Commit
`83743ef` on `tz6/pipeline` still holds them, and the merged pull request keeps
that commit if the branch is deleted:

- scope, design, development plan, verification report, documentation record and
  synchronization record:
  `.standards/docs/<scope|specs|development|verification|documentation|synchronization>/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c.md`;
- implementation and final reviews:
  `.standards/docs/reviews/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c/<implementation|final-deliverable>.md`.

For example,
`git show 83743ef:.standards/docs/specs/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c.md`
prints the survey's design. `main` takes squash merges, so `83743ef` never
reaches it. Once `tz6/pipeline` is deleted, a clone that lacks the commit gets
it with `git fetch origin pull/<N>/head`, where `<N>` is the number of the pull
request that merged the survey.

This file keeps what the next cycle needs from those records. The full request,
design directions, step design points, known source defects, evidence E1–E23 and
the KGForEdGlobal consumer contract are in `artifacts/design_brief.md`. Where
the brief and this file disagree, this file is newer. The earlier version of
this file, written for the survey cycle, is in git history.

Nothing here is an acceptance condition. The survey cycle's AC numbers belong to
that cycle; the next cycle numbers its own.

## User decisions that apply to later steps

Made while scoping the pipeline (2026-11-16) or during the survey cycle
(2026-11-17 to 2026-11-19). Where a rule goes beyond what the user decided, the
bullet says which part was the survey design's choice, which Architect may
revisit.

- Acceptance of each step rests on the user's review of real runs on PDFs of
  their choice, covering two-column right-to-left, Chinese or Japanese, a tax or
  fillable form, a slide deck or image-heavy PDF, and CAPS. There is no numeric
  parity target with KGForEdGlobal, and cost is reported with no pass/fail
  target.
- Reuse before rewriting: pydelity ports over KGForEdGlobal's code and reuses
  what fits, and writes new or updated code where it does not fit. Ported code
  must not carry the defects listed in `artifacts/design_brief.md`.
  KGForEdGlobal (`/Users/tzz/Projects/private/idi/KGForEdGlobal`) is read-only.
- pydelity ships no per-model PDF input limits and checks none before a model
  call, because keeping them current is not maintainable. The provider enforces
  its own limits. The CLI shows the provider's error, and the Python API raises
  `ProviderError` carrying it. Extending this to all per-model data (context
  windows, capability lists) was the survey design's choice (decision 3), so a
  per-model limit step 2 needs, such as for images, is open for Architect.
- There is no default `max_cost`. When a run would go over it, pydelity logs a
  warning and the user decides. The CLI asks (`--yes` answers yes), and Python
  callers pass `allow_over_max_cost=True` or get `BudgetExceededError` and a run
  they can resume. The survey design (decision 11) added that the CLI asks at
  most once per run and that the guard serializes the question so concurrent
  requests ask once. Step 2's Architect may revisit both for parallel page
  requests.
- The number of provider retries is a setting. The user decided only that. The
  survey design made it one setting, `advanced.provider_retries` (0 to 10,
  default 2), shared by model requests and uploads, with no retry layer of
  pydelity's own (decision 13). A per-step retry count is open for Architect.
- Every Python function that measures, estimates or runs has an async version
  named with an `a` prefix (`arun`, `asurvey`, `ameasure`, `aestimate`). The
  sync functions use `asyncio.run` only and raise `RuntimeError`, naming the
  async function to await, when called inside a running event loop (Jupyter,
  async code). New steps add their functions the same way. `load` stays sync,
  which Architect chose.
- Language tags are checked with `langcodes`. Storing them in their standard
  form was the survey design's choice (decision 15).
- The survey's model trusts its own reading of the PDF over the probe's measured
  facts, which are hints, because the model sees the page and is the more
  capable reader. This applies to page numbers, rotation and every other fact,
  and each disagreement on rotation or printed page numbers goes on the review
  list. The decision is recorded for the survey, but the user stated it
  generally: the model should be trusted over the facts "in general". Step 2's
  planned checks compare the model's text with the text layer and send the page
  back when text is dropped or invented. Whether those checks keep retrying
  under this decision, or only list the differences for review as the survey
  does, was not asked. Step 2's Scoper settles it with the user.
- The survey uses Python checks only. A second model that verifies answers (a
  producer-verifier pass like KGForEdGlobal's page extraction) was left to later
  steps such as page extraction.
- People must be able to install and use pydelity on Windows. `just` recipes
  that work on Windows without a POSIX shell were left out of the survey cycle;
  whether a later cycle takes them up is the user's call.
- CI tests Python 3.13 and 3.14 (the user's decision). Smoke-testing the built
  wheel on Linux and macOS as well as Windows was the survey design's choice.
- Releases come from release-please. A pull request's squash-merge title is the
  commit message, so it must be a Conventional Commit, and a `feat:` title makes
  a minor release. Work merges to `main` only after its cycle is signed off and
  STANDARDS is uninstalled.
- `examples/config.json` and `examples/config.yaml` hold every setting at its
  default, and a test keeps them complete, so a new setting goes into both.
- PyMuPDF is pydelity's PDF library, as in KGForEdGlobal, and the user accepted
  its AGPL-3.0 license (pydelity itself stays MIT). Step 2's rendering need not
  reopen that choice.
- PDF transport, for every provider: upload the PDF with the provider's file API
  when it has one, send it inside the request only when the upload path fails,
  keep uploads until they expire at the provider, and treat a provider that
  offers neither as unusable.
- Test PDFs are real public-domain documents that the user approves, never
  generated ones.
- The CLI has no `--quiet`. By default it shows warnings, errors, the cost
  estimate and the summary, and `--verbose` shows everything. Every option also
  has a short form (such as `-mc` for `--max-cost`), so options step 2 adds,
  such as `pages`, need one too.
- File and folder names are the user's to approve, before the step that creates
  them. Each pipeline step gets one folder directly under `src/pydelity/`, named
  with an "-ing" word so it never collides with a public function: `surveying/`
  for step 1, then `extracting/`, `verifying/`, `assembling/`, `proposing/` and
  `projecting/`. Inside a step folder, model code follows KGForEdGlobal's
  `page_ir_extraction/` split (`agents.py`, `llm.py`, `prompts.py`,
  `validators.py`, `schemas.py`).
- How the user worked with Developer: `STEPWISE` collaboration. Before each
  build step, Developer listed the files and folders it would create or change
  and waited for the user's review; after each step it stopped for a go-ahead,
  and its report ended with the next step's plan (what it builds and how, the
  files, how it will be checked, and anything needing approval, such as
  downloads or spending).
- During development, self-checks call the real Anthropic and OpenAI APIs with
  the user's keys, on small PDFs, and record the spend. Failure paths a provider
  cannot produce on demand use fault injection in scratch scripts, never in
  pydelity code. After each build step, `pydelity <pdf>` (or the Python API) can
  try what that step built. `PROBE_VERSION` and `PROMPT_VERSION` stayed at 1
  until the first release, and reruns used `--overwrite`; ask whether step 2's
  prompt version follows the same rule.
- A new runtime dependency's minimum version is its latest stable release on the
  day it is added.
- Code conventions from the user's reviews: private globals, classes and
  functions come before public ones in each module, alphabetical within each
  group; American English throughout; shipped code, config and docstrings never
  mention the development process (decision dates, DEV or AC IDs,
  KGForEdGlobal); each step's checks on model answers live in
  `<step>/validators.py`; prompts return a `PromptPair` from
  `src/pydelity/utils/prompts.py`, written the way KGForEdGlobal writes its
  prompts; output schema versions live in `src/pydelity/schema_versions.py`;
  `justfile` recipes and `pyproject.toml` tables, keys and lists stay
  alphabetical.

These decisions replace earlier plans:

- The brief's **Cross-cutting** input limits, its open question 11 and the
  earlier version of this file planned per-model PDF limits, checked before the
  model call, with a warning for unknown models. pydelity keeps no limits and
  checks none.
- Going over `max_cost` no longer stops a run on its own.
- The brief's **Step 1 (survey) design points** had the survey's checks compare
  the profile with the probe's rotation and page numbers, and require proposed
  artifacts to cover about 80% of the repeated lines. The built survey lists
  rotation and page-number differences for review instead of retrying. For
  repeated lines it is stricter: while check retries remain, check C5 sends the
  answer back until every repeated line is classified, exactly once, as an
  artifact or as content. The last allowed answer is kept as it is, and each
  check still failing goes on the review list. That section of the brief is now
  history.
- The pipeline is no longer released only once all six steps are done. 0.1.0
  ships the survey alone, and each later cycle decides its own release.

## Answers to the brief's open questions

The numbers follow **Open questions for Scoper to settle with the user** in
`artifacts/design_brief.md`. All twelve are settled.

1. A default run goes through all six steps, projection included, with a setting
   to stop after `document.json`. In 0.1.0 it runs only the survey.
2. Yes. The CLI shows an estimate and asks before spending, `--yes` skips the
   question, and the Python API never asks.
3. Both: the review list in `run.json`, a CLI summary at the end of a run, and
   an HTML report.
4. No parity target. Acceptance rests on the user's review of real runs on PDFs
   of their choice.
5. Two-column right-to-left, Chinese or Japanese, tax or fillable forms, and
   slide decks or image-heavy PDFs, plus CAPS.
6. Architect picks each step's default model (the survey's is
   `anthropic:claude-opus-5-5`). There is no default `max_cost`. 0.1.0 has one
   global `model` setting, used by the survey, so step 2's design decides how a
   user picks a different model for page extraction.
7. Both, and a PDF path given on the CLI is used over the config file's.
8. No. A user-supplied domain schema does not seed page-profile labels, so
   changing it reruns only steps 5–6.
9. Architect picks the final `kind` and `role` lists. The survey design
   (decision 8) added `formula` and `code` to kind and `aside` to role; the
   lists are under **What 0.1.0 provides for step 2**. Step 2's Architect may
   change them, which changes the output `schema_version`.
10. Option (a): bordered or shaded boxes become containers. Page extraction
    records them, and assembly joins a box that crosses pages into one container
    (see **Item vocabulary** below).
11. pydelity keeps no per-model limits (see above).
12. Architect picks the step 3 design, with no measured comparison of the
    options first.

## What 0.1.0 provides for step 2

- **Layout.** `src/pydelity/` holds `api.py`, `cli.py`, `config/`, `costs/`,
  `pipeline/runner.py`, `providers/`, `report/`, `surveying/` and `utils/`.
  Later steps add their own step folders beside `surveying/`, named as described
  under **User decisions that apply to later steps**.
- **Models.** `build_model` builds every model as `<provider>:<model-id>`
  (`anthropic` or `openai`; default `anthropic:claude-opus-5-5`) and wraps it in
  `LedgerModel`. `LedgerModel` asks the `max_cost` guard before each request and
  writes each response's tokens and cost to `cost.jsonl`, so every step's
  requests are recorded. Spend control does not yet cover step 2. The guard's
  upper bound for a request counts text and documents only: `_user_content_size`
  in `providers/ledger_model.py` ignores images, and each document counts as the
  whole PDF. The plan-time estimate covers the survey only (`estimate_survey` in
  `costs/budget.py`, called from `pipeline/runner.py`). Step 2 sends page
  images, so it needs its own estimate and a per-request bound that counts
  images. Otherwise a run can go over `max_cost` without the question. The guard
  also checks each request against recorded spend only (`costs/budget.py`), so
  requests already in flight are not counted, and parallel page requests can
  together go over `max_cost` with no question. Structured output uses
  PydanticAI `NativeOutput` where the model supports it, otherwise
  `PromptedOutput`, never forced `tool_choice`. The survey's model settings sit
  under `advanced.survey`: `effort` (mapped to Anthropic's adaptive thinking and
  OpenAI's `reasoning_effort`), `max_output_tokens`, `request_timeout_seconds`
  and `check_retries`. A new step gets its own `advanced:` section the same way.
  The plan-time maximum assumes every request writes `max_output_tokens` and
  every check retry happens. With the survey's default of 32,000 output tokens,
  one request's bound is about $0.64 on `claude-opus-5-5` and $1.28 on
  `gpt-6.2-astra`, while real survey answers used 1,858 to 5,633 output tokens.
  Copied per page, those defaults would make the `max_cost` question come on
  nearly every step 2 run, so step 2 needs its own per-page defaults.
- **Output folder.** One folder per PDF is the unit of resume and spend. Every
  JSON and HTML file is written atomically and validated on load. Each output
  stores a fingerprint of its inputs and is reused while valid and matching.
- **Uploads.** The survey uploads the whole PDF to the provider, keeps it until
  the provider's expiry (`advanced.uploads.expiry_hours`, default the provider's
  maximum, 90 days on Anthropic) and records it in `uploads.json`, so a later
  step can reuse it. The survey design assumed steps 2–6 send page images, crops
  and text rendered locally; whether a step uses the upload is its own design
  choice.
- **The profile step 2 builds on.** `pdf_survey.json` `profile` holds:
  - `labels[]` (`name`, `role`, `kinds`, `description`), always including
    `other`;
  - `languages[]`, in standard form;
  - `writing_direction` (a default plus page ranges, each `ltr`, `rtl` or
    `ttb`);
  - `rotation[]` (clockwise degrees that make each page range upright);
  - `page_numbering[]`, `continuation_notes[]`, `start_markers[]` and
    `user_instructions`.

  `proposal.artifacts[]` and `proposal.non_artifact_lines[]` say which repeated
  lines are page furniture and which are content. These inputs are not
  guaranteed valid. When the check retries run out (at once when
  `advanced.survey.check_retries` is 0), the survey keeps the model's last
  answer. Python cleans up only labels, languages and regions. The `rotation`,
  `writing_direction` and `page_numbering` ranges and the artifact mapping are
  stored as answered, so ranges can overlap or run past the PDF, and the mapping
  can miss, repeat or invent repeated-line IDs, each with only a review issue.
  Step 2 must handle these. The survey's own comparison takes, for each page,
  the first range that covers it and ignores ranges outside the PDF. The design
  names `profile` as what steps 2–3 depend on and include in their fingerprints.
  The artifact mapping is outside `profile`, so if step 2 uses it (the brief's
  step 2 design sends pre-matched artifact lines), step 2's fingerprint must
  include it too, or a changed mapping will not rerun step 2.

- **Item vocabulary.** Kind: `text`, `list`, `table`, `figure`, `field`,
  `formula`, `code`. Role: `heading`, `body`, `caption`, `footnote`, `artifact`,
  `navigation`, `aside`. A value is in these lists only when a later step must
  treat it differently, and per-PDF detail goes in labels. `code` keeps its
  whitespace and line breaks exactly, and a cross-page join is a newline with no
  dehyphenation. Changing these lists changes the output `schema_version`.
  Bordered or shaded boxes become containers, not a kind or role. The brief puts
  `container` in the page schema for steps 2–4: items inside a box keep their
  own kind and carry a container ID, and each container has a bounding box and
  open-top and open-bottom hints for cross-page continuation. So page extraction
  records containers on each page, and assembly joins a box that crosses pages
  into one container. The survey design says only "in a later step", so step 2's
  design settles the container contract.
- **Facts.** `pdf_facts.json` holds per-page text-layer quality (`none`, `good`
  or `garbled`), bookmarks, form fields and checkbox states, structure tags and
  their quality, repeated lines with IDs and bands, text direction and printed
  page numbers. The brief's step 2 design skips text-layer hints on pages with
  garbled text (E22). The text layer also misses text inside images, and the
  survey's prompt had to be changed to say so after the model left out the
  rotation of such pages. A check for invented text against the text layer must
  allow for text the model reads from images, which bears on the open question
  of whether step 2's text checks retry.
- **Review and report.** Review issues go to `run.json` `review[]` with `step`,
  `page_index`, `check`, `message` and `details`, and the CLI prints a summary.
  `report.html` renders page images (`report/images.py`) with the survey's
  findings. The `ReviewIssue` model is survey-specific today: it lives in
  `surveying/schemas.py`, its `step` can only be `survey`, its `check` can only
  be a survey check name, and it has no item field. Step 2 needs a shared model
  that can also name an item, which changes the `run.json` contract. The report
  needs item boxes.
- **Tests.** `tests/fixtures/mock_providers.py` is a stand-in Anthropic and
  OpenAI server reached through the SDKs' base URLs. An autouse fixture sets
  dummy keys and a closed port, so no test reaches a provider. Nine public test
  PDFs are in `tests/fixtures/pdfs/`, with their sources in `SOURCES.md`. None
  has a page whose rotation attribute is 90, 180 or 270, because no downloadable
  candidate had one. Step 2 renders rotated pages upright and maps boxes back to
  PDF points, so it needs a real public PDF with such a page, approved by the
  user. The survey cycle already checked 21 candidates (CDC, BLS, SSA, GAO and
  CRS refuse scripted downloads). Its self-checks used a copy of
  `irs_pub1_arabic.pdf` with page 0's rotation attribute set to 90. Whether such
  a copy of a real document counts as a real test PDF, as the CAPS page excerpt
  did, was never asked.
- **Docs.** `scripts/generate_reference_docs.py` generates the reference pages
  from the code, and CI fails when they are stale. The guides describe the
  survey only and need updating for each new step.

## Reuse from KGForEdGlobal so far

KGForEdGlobal has no survey step, so the survey cycle ported only infrastructure
(paths under `backend/src/kgfeg/`):

- `utils/pdf.py` `compute_doc_key` became pydelity's PDF SHA-256 helper.
- `model_registry.py` became the model factory and provider profiles, without
  its hand-kept list of models.
- `page_ir_extraction/agents.py` gave the agent pattern: an output validator
  that raises `ModelRetry` with the Python checks' messages.
- `AgentUsageBucket` and `write_to_json` were replaced by the cost ledger and
  atomic writes rather than ported.

Nothing else from `page_ir_extraction` has been ported: not its validators,
prompts or constants. It is step 2's main source, and most of the brief's
**Known defects in the source code to design out** are in it or in the code it
uses: left-to-right reading order in the prompt and in
`validate_gross_reading_order`, English-only word lists, full-page figure checks
that reject one-figure pages, a letter-run word tokenizer, no form-field or
checkbox type, figure crops not saved, one DPI for every page (a setting with
default 250), and resume that checks only whether a file exists.

Ported code targets KGForEdGlobal's locked versions, pydantic-ai 1.63.0 and
PyMuPDF 1.26.7, so it needs updating for PydanticAI 2.69 or later (output
retries, for example, are `Agent(retries={"output": n})`) and PyMuPDF 2.1 or
later. Keep PyMuPDF 2.x: the user chose it for fixes that include `get_pixmap`
hangs (#5082, and #5125 on heavily tagged pages).

## Pipeline outcomes for steps 2–6

Scoped before the pipeline was split into one cycle per step, copied from the
earlier version of this file. The old AC numbers in parentheses are retired.

- Page extraction (step 2), was AC-005 to AC-007: each selected page gets a page
  file of items in reading order for its writing direction (including
  right-to-left and multi-column), each with a stable ID, kind, role, label,
  bounding box in PDF points and content; rotated content is read upright.
  Figures are saved as crops, captions link to what they caption, form fields
  and checkboxes carry their values (including fillable-field values), and
  single-figure pages are accepted. Dropped or invented text, compared with the
  text layer in any script, is caught, retried and otherwise put on the review
  list.
- Page-break verification (step 3), was AC-009: each break gets a verdict on
  whether content continues, which items connect, the join rule for their kind
  (text: space, no space or dehyphenate; list: continue item or new item; table:
  append rows or merge a split row), how many repeated header rows to drop, and
  which repeated items above the continued unit to drop.
- Assembly (step 4), was AC-011 to AC-014: `document.json` with a
  `schema_version`, every item accounted for exactly once, joins only where
  verdicts say so (continuation markers folded in), per-item provenance kept,
  and artifacts out of the reading flow unless `keep_headers_footers` is set. An
  outline tree of headings, with `section_path` as outline ancestors outermost
  first; contents-page mismatches and cross-page role or kind inconsistencies go
  on the review list. Boxes as containers with an ID per list item, one
  container per cross-page box. Table grids with spans marked as spans, plus a
  filled-down view for grouped tables unless `fill_down` is off.
- Domain schema (step 5), was AC-016: without a user schema,
  `schema_proposed.json` (`x-key` on every array of objects with required key
  fields, `x-verbatim` only on strings, a place for content that is not a main
  record) and `schema_notes.md` mapping every outline section to a path or an
  exclusion reason. A user schema skips the proposal. Unknown `x-*` annotations
  pass through.
- Projection (step 6), was AC-018 and AC-019: `domain.json` validates against
  the schema; `x-verbatim` strings match their cited items; cited IDs exist;
  objects get stable IDs from their key paths; arrays follow document order;
  conflicting values go on the review list. A coverage report lists uncited
  content items, verbatim retries and merge conflicts.
- KGForEdGlobal compatibility, was AC-036 to AC-038: segment IDs follow today's
  recipe and are stable across reruns, boxes are in PDF points, and an item ID
  to segment ID lookup is included; `document.json` holds the data an adapter
  needs for each KG field in use today and for CAPS requirement boxes as
  one-column tables; a written mapping documents where each comes from. Each
  KGForEdGlobal `TextUnit` (every text block and table cell) has a required
  BCP-47 `language` that the KG stage reads, which the brief's consumer contract
  leaves out. Step 2's design decides whether items carry a language tag or an
  adapter fills it from the profile's `languages`. Corrections to the brief from
  the survey cycle's audit: KGForEdGlobal's KG stage loads
  `stitching/document_ir.json` with `DocumentIR.model_validate`, not a
  `document.json`. Its schema models forbid undeclared keys (`extra="forbid"`),
  so even a top-level `schema_version` fails validation. The brief's field-use
  counts come from substring matches; whole-word counts are lower for
  `segment_id` (38, not 223), `section_path` (23, not 72), `grid_sources` (46,
  not 53) and `columns_signature` (19, not 31). Reading pydelity's
  `document.json` therefore needs KGForEdGlobal-side changes, which stay out of
  pydelity's cycles.
- User sign-off of each step's output, was AC-004, AC-008, AC-010, AC-015,
  AC-017 and AC-020.

The cross-cutting outcomes scoped with them (configuration, CLI and library use,
cost and spend controls, resume, providers and tests, the review list and HTML
report, no document-type assumptions, user docs) were built for the survey in
0.1.0, with the changes listed under **User decisions that apply to later
steps**. Each later step extends them to its own outputs. Two parts are still
open: a changed input reruns its own outputs and everything downstream, and
nothing else, once there is more than one step; and review issues name the item,
not only the page.

The direction for the default run is unchanged: `pydelity <pdf>` eventually runs
all six steps, with a setting to stop after `document.json`. In 0.1.0 it runs
the survey only.

## Constraints, non-goals and assumptions still in force

- Constraints: Python 3.13 or later (3.14 tested), with Pydantic,
  pydantic-settings, PydanticAI, loguru and Typer. Models are reached through
  provider APIs via PydanticAI, and both Anthropic and OpenAI must work. The PDF
  path is the only required input, configuration is one optional JSON or YAML
  file with an `advanced:` section, and a normal run resumes. No hand-written
  per-document config or domain Pydantic classes, and no core logic, prompt,
  schema field or default that assumes a document type. The domain schema is
  JSON Schema data with `x-key` and `x-verbatim`, never Python source.
  Consumer-specific needs go in `document.json` fields or the consumer's
  adapter. The brief's design directions are input for Architect, and evidence
  E1–E23 illustrates rather than specifies.
- Non-goals: any change to KGForEdGlobal; KG, Learning Component and Learning
  Progression logic; generating KG config from a pydelity schema; automatic
  splitting or a chunked survey for PDFs a provider rejects as too large;
  per-model PDF limits; continuity judged inside step 2 (step 3 option E); a
  measured comparison of step 3 designs; a default spending limit; a hosted
  service, web UI beyond the HTML report, telemetry and other Level 4 features.
- Assumptions: Level 3 (internally testable) maturity. Test PDFs are public
  documents chosen with the user's approval. A user-supplied domain schema does
  not seed page-profile labels, so changing it reruns only steps 5–6. Real model
  runs use the user's own API keys, and automated tests mock every model call.

## Risks and follow-up from the survey design

- Steps 2–6 reuse `build_model`, `LedgerModel`, the `max_cost` guard, atomic
  files, fingerprints, review issues and the report. They add `pages` and
  `schema` settings and per-step `advanced:` settings, and extend the default
  run. Other PydanticAI providers can be added by extending the provider
  allowlist, the model factory and the provider profiles.
- Prices and model IDs drift. Prices follow `genai-prices` releases, and
  `advanced.models` covers a model it does not know yet. Older models that
  reject adaptive thinking, `effort` or `reasoning_effort` fail with the
  provider's error.
- A request that times out on pydelity's side may still finish, and be billed,
  at the provider, with no ledger line. Each timed-out retry can add such unseen
  cost, and page-level parallel requests multiply it.
- Non-streaming requests with a large `max_output_tokens` need an explicit
  request timeout. `LedgerModel` already wraps streamed requests
  (`request_stream` runs the same `max_cost` check and writes the ledger line),
  but no test covers that path, so a step that streams should add one.
- PyMuPDF holds the GIL while it reads a page, so rendering pages in
  `asyncio.to_thread` does not run them in parallel, and each read can hold up
  the event loop (by up to about 50 ms on the survey's test machine).
- The cost estimate is a heuristic with conservative upper bounds, so the
  `max_cost` question can come for a run that would have fitted.
- Uploaded PDFs stay in the user's provider storage until they expire (90 days
  on Anthropic by default) and count against the organization's storage.
- The IANA registry inside `langcodes` is fixed per release, and a release that
  changes a tag's standard form changes fingerprints, so outputs that use the
  tag run again.
- Probe mistakes reach the review list as `page_number_differs` issues, for
  example numbers in table cells, or page labels on pages that print no number.
  Keeping page labels as a fact separate from the printed text would cut that
  noise. It changes the facts schema, so it waits until review lists show it
  matters.
- The model can be wrong where the facts were right, and the review list is the
  only signal.
- Every repeated line (up to 1,000) goes with the survey request and must be
  accounted for.
- Claude Opus 5.5 can stop with `refusal`, which the survey reports as a
  failure. Server-side refusal fallbacks are off because they change the billed
  model in the middle of a request.
- The survey's region boxes are the model's estimates and are often off. Making
  them accurate, by snapping them to measured content or rejecting boxes over
  empty areas, is a design question for the first step that uses regions.
- One run per output folder at a time. Concurrent runs in the same folder are
  unsupported and not detected.
- On Windows, `os.replace` fails while another program holds the target open,
  and the error names the file.
- `docs/pnpm-lock.yaml` may approach the 500 KB limit of the large-file hook. If
  it goes over, exclude that one path with a comment.
- `pyproject.toml` `[tool.coverage.report]` still holds two scaffold entries,
  the `def cli` exclusion and `omit = ["./src/pydelity/__init__.py"]`, that can
  be tidied while editing it. The `*/__init__.py` omit in `[tool.coverage.run]`
  is real.

## Review findings and observations left for later

The first four items are the implementation review's findings F-001 and F-003 to
F-005, withdrawn as not material for 0.1.0, each with a reproducer in its
report. The rest are its non-material observations.

Any fix to the probe (the checkbox, page-label and structure-tag items below)
must raise `PROBE_VERSION` in `surveying/probe.py`. That changes the facts
fingerprint, which the survey's fingerprint includes. So every existing output
folder reruns the paid survey on its next run, and step 2 reruns too wherever
the profile changes.

- `run.json` records `pdf_transport: null` for a failed step even when a request
  carried the PDF, because the transport is set only when the survey returns.
  Record it as soon as the PDF is attached to a request.
- A checked checkbox with no normal appearance (`/AP /N`) makes PyMuPDF's
  `on_state()` raise, and the whole form fact becomes unreadable. Read the
  checked state without needing appearances, and keep one bad widget from
  discarding the other fields. Step 2 carries form-field values, so this matters
  there.
- Letter-style page labels (`/S /A`, `/S /a`) are read as roman numerals (`C`
  becomes 100). Use the label range's numbering style, which
  `Document.get_page_labels()` returns. Recording a letter-style number may need
  a new facts `style` value, which is Architect's decision.
- Structure-tag quality is misrated in two cases. A structure element whose `/K`
  is an indirect reference to an array is not followed, so a fully tagged PDF
  reads as `poor`. A walk that stops at the 20,000-element cap counts unvisited
  pages as untagged, so a long, well-tagged PDF reads as `partial`. Before step
  2 relies on tags, its design should resolve indirect `/K` entries and settle
  how a capped walk is rated.
- The Python API leaves PydanticAI's first-run banner on, so the first `run()`
  in a process prints it (the CLI turns it off). The Python guide mentions it.
- `costs/pricing.py` `_config_price` uses `or`, so a cache price set to `0` in
  `advanced.models` is priced at the input price. The ledger can only overstate.
- CI's check for stale reference pages (`git diff --exit-code`) does not catch a
  newly generated page left untracked.
- `docs.yml` says a published build never reuses files another run wrote, which
  is not true of the pnpm store cache that `withastro/action` restores. Its plan
  step runs the runner's own `node` and `python3` and hides `node`'s error with
  `2>/dev/null`.
- Probe edge cases with low impact: an outline whose `/Next` links form a cycle
  reads as no bookmarks; tagged pages without text count toward structure
  coverage; a radio group whose kids are all `/AS /Off` with `/V` set reads as
  unchecked.

The final review found these wording issues in the docs, none material:

- `contributing/docs-site.md` says a manual run of the docs workflow publishes,
  but `docs.yml` publishes only on a push. It should say how to republish:
  re-run the push run for the tag or for `main`.
- `contributing/docs-site.md` and `contributing/development.md` say
  `just docs-reference` regenerates the reference pages, but its output stays
  unformatted until `just lint-markdown` or `just lint` runs Prettier.
- `contributing/development.md`: `--randomly-seed` repeats the shuffle but not
  each pytest-xdist worker's order, and skips the docstring session; Dependabot
  opens up to four monthly pull requests (github-actions, npm, pre-commit, uv),
  not one; several hooks check the whole tree, not only the commit's files.
- `contributing/releases.md`: by release-please's default changelog sections,
  `perf:` and `revert:` commits may also make a patch release (not confirmed
  from a repo file).
- `contributing/docs-site.md`: the docs build runs on pull requests to `main`,
  not on every pull request.
- `faq.md` says changing any survey setting reruns the survey, which is looser
  than `guides/reruns.md`: `request_timeout_seconds` keeps the saved survey.

Not exercised in the survey cycle: Ctrl+C at a CLI question on Windows, and the
exact release-please version bundled in `release-please-action` v5.0.0 (its
17.6.0 source was read).

## Loose ends

- After merging, check that release-please proposes 0.1.0 from the `0.0.1`
  manifest with no earlier tag (confirmed from its source, not yet in practice),
  that the PyPI Trusted Publisher, the `pypi` environment and GitHub Pages are
  set up, and that the docs site publishes from the `v0.1.0` tag.
- Whether to yank the `0.0.1` placeholder on PyPI is the user's call.
- Node `24.22.3` is kept by hand in three places: two hooks in
  `.pre-commit-config.yaml` and `docs.yml`. `docs/package.json`'s `engines.node`
  (`>=22.23.4`) follows the locked Astro's own minimum.
- Repo-setup risks still open: Dependabot's uv can lag behind the uv people use,
  and updates fail if it falls below `required-version`. Dependabot may propose
  raising `setuptools>=77`; ignore that with a comment. Hand-kept pins (the uv
  bound, CI's uv, Node, Prettier) go stale unless someone bumps them, and a
  Prettier bump can reformat many files. zizmor's online audits can fail CI when
  an advisory is published for an action the repo uses. prek is pre-1.0.
  Markdown formatting also covers STANDARDS files while STANDARDS is installed.
  PyPI versions are permanent.

## Pushed to later steps

Decided while scoping step 2 (2026-11-19). Each entry names the step that picks
it up. Add to this list whenever work is moved out of the current step.

- **Translation (after assembly, step 4 or later).** Revisit an optional step
  that translates extracted text into a target language the user sets. pydelity
  serves any PDF and any downstream use, so translation is worth having even
  though KGForEdGlobal does not translate. A run for KGForEdGlobal leaves it
  off. Step 2 transcribes text as printed and translates nothing. Translating
  after assembly means text continued across a page break is translated as one
  unit.
- **Page continuity (step 3).** Step 2 records no continuity. Items carry no
  continuation marks, and containers carry no open-top or open-bottom hints,
  which the brief's container proposal had. Step 3 decides whether content
  continues across each page break.
- **Boxes that cross pages (step 4).** Step 2 records a bordered or shaded box
  as a container on each page it appears on, with an ID and a bounding box, and
  the items inside name their container. Assembly joins the pieces of a box that
  crosses pages into one container, using step 3's verdicts.
- **Pauses between steps (each later step).** By default, a run stops after a
  step that wrote new output, so the user can check it before paying for the
  next step, and the next run continues. One setting, in the config file, the
  CLI and Python, turns every pause off. Step 2 adds the pause after the survey.
  Each later step adds its own pause under the same setting.
- **Model per step (each later step).** The global `model` setting chooses the
  model for every step. Step 2 adds an optional page extraction override under
  `advanced:`, and each later step gets its own optional override the same way.
- **Instructions per step (each later step).** Instructions live under each
  step's `advanced:` section, `advanced.survey.instructions` and
  `advanced.extraction.instructions` in step 2, and go only to that step's
  models. They are set in the config file or from Python, with no CLI option,
  because each step's instructions are specific to that step. Step 2 removes the
  top-level `instructions` setting and `--instructions`/`-i`. Each later step
  gets its own optional `advanced.<step>.instructions` the same way.
- **Raising internal versions again (not yet decided).** Step 2 raises no
  `PROBE_VERSION`, `PROMPT_VERSION` or output `schema_version`, because no one
  uses pydelity yet. When to go back to raising them for changed outputs is
  still open. Step 2 also keeps no backwards compatibility with 0.1.x (no
  aliases, deprecation warnings, migration or defaults kept only for old files).
  When pydelity starts keeping compatibility, likely once it has public users,
  is open too.

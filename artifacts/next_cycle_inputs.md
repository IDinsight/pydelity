# pydelity: inputs for page-break verification (step 3)

Two pipeline steps are built, in three STANDARDS cycles:

- The survey (step 1), released as 0.1.0 and 0.1.1. Cycle
  `build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c`, with its
  records in commit `83743ef` (`git fetch origin pull/4/head` if a clone lacks
  it).
- Page extraction (step 2) and the verifier cycle after it, on one branch,
  shipped together as 0.2.0 through pull request `14`. Cycles
  `build-step-2-page-extraction-of-the-20261119T174118Z-0419318a` (signed off
  2026-11-20) and
  `add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada` (signed off
  2026-11-22), with both cycles' records in commit `af1b2d1`
  (`git fetch origin pull/14/head` if a clone lacks it).

STANDARDS is uninstalled before each merge to `main`, so cycle records live only
in git history, at
`.standards/docs/<scope|specs|development|verification|documentation|synchronization>/<cycle id>.md`
and `.standards/docs/reviews/<cycle id>/<implementation|final-deliverable>.md`.
For example,
`git show af1b2d1:.standards/docs/specs/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
prints the verifier cycle's design.

`artifacts/design_brief.md` holds the full request, the design directions, each
step's design points (including step 3's options), known defects in the source
code, evidence E1–E23 and the KGForEdGlobal consumer contract. Where the brief
and this file disagree, this file is newer. The user styles for each role, which
hold the code conventions, are in `artifacts/user-styles/`. Nothing here is an
acceptance condition, and old AC numbers are retired.

## User decisions that apply to later steps

A rule marked as a design choice was an Architect's rather than the user's, and
a later Architect may revisit it.

Acceptance and reviews:

- Each step is accepted on the user's review of real runs with Anthropic and
  OpenAI models on PDFs of their choice, covering two-column right-to-left,
  Chinese or Japanese, a tax or fillable form, a slide deck or image-heavy PDF,
  and CAPS. There is no parity target with KGForEdGlobal, and cost is reported
  with no pass/fail target.
- Reviews raise only major issues: on input the release targets, a finding must
  make the delivered output wrong, lose money, fail a run, or break a function
  the acceptance review relies on. Smaller problems are recorded as limitations.
  Ask the user whether step 3's reviews keep this bar.

Design rules:

- Reuse before rewriting: port KGForEdGlobal's code where it fits (see
  **KGForEdGlobal sources**), without the defects the brief lists.
- Document-type agnostic: no core logic, prompt, output field or default may
  assume a document type, a language or a writing direction, and there is no
  hand-written per-document config, domain Pydantic class or language-specific
  word list or pattern. Document-specific knowledge comes only from the survey's
  profile and each step's instructions.
- Code's measurements of the PDF are hints, in every step that calls a model.
  Code measures facts such as stored text, page labels, rotation, repeated lines
  and form fields, and gives them to the model with the survey's findings as
  hints. The model's own reading decides the answer, and no message asks it to
  match a hint. A step sorts its comparisons into two groups:
  - Hints compare the answer with what code measured or the survey found. A
    difference never sends an answer back and never fails a page, a step or a
    run. It goes on the review list unless that step's verifier passed the
    answer or its correction was kept, and the output's `hints` keeps it either
    way.
  - Checks test the answer's own consistency (against itself and the survey's
    profile) and hard limits (the page count, each page's area). They may send
    an answer back within the step's `check_retries`, and a final answer still
    failing one is kept and listed while the run goes on.

  A run stops only on an unusable answer (none in the answer format within the
  retries, a refusal, or output tokens used up) or a provider error after the
  provider retries. Stored text can be wrong (broken Arabic letter forms,
  ligatures, private-use characters), so it is evidence, never the answer. Page
  extraction sends no stored text beyond the page's repeated lines and form
  field values, and the models read the rest from the page image.

- Each check sits where it can be enforced: Pydantic classes for shape,
  `<step>/validators.py` for what code can decide, and the step's verifier for
  what code cannot judge. A verifier is a second request to the step's own model
  with that step's instructions only. It runs on all of the step's work or none
  of it, and may return a full correction, kept when it passes every check. Its
  settings are under **Pushed to later steps**. The brief's terms differ: there
  the "verifier" makes step 3's main judgment on each break, and a "validator"
  is a second model that reviews it, the role page extraction's verifier plays.
- One structured-output mode per provider for every request: prompted output on
  Anthropic and native output on OpenAI. Anthropic compiles native output into a
  grammar whose limits page extraction's answer exceeded, and those limits can
  change, so no step depends on them.
- pydelity keeps no per-model limits and checks none before a model call, which
  drops the brief's per-model PDF limits. The provider enforces its own, the CLI
  shows its error, and Python raises `ProviderError`. Page extraction keeps each
  provider's documented image limits in `providers/profiles.py` to size its
  images.
- The CLI shows an estimate and asks once before spending (`--yes` answers yes),
  and Python never asks. There is no default `max_cost`. When a run could go
  over it, the CLI asks (at most once per run, a design choice), and Python
  callers pass `allow_over_max_cost=True` or get `BudgetExceededError`. That
  question can come partway through a run.
- PDF transport, whenever a step sends the PDF: upload it with the provider's
  file API, reuse the upload recorded in `uploads.json` while it is usable, and
  send it inside the request only when the upload path fails.
- Every Python function that measures, estimates or runs has an async version
  named with an `a` prefix. `load` stays sync (a design choice). The docs lead
  with the async functions.
- PyMuPDF 2.x is the PDF library, and the user accepted its AGPL-3.0 license
  (pydelity stays MIT). PyMuPDF is not safe across threads, so page extraction
  runs its PyMuPDF calls on one worker thread per run (`PdfWorker`).
- No backwards compatibility while pydelity has no public users: no aliases,
  deprecation warnings, migrations or defaults kept for old files.
  `PROBE_VERSION`, each `PROMPT_VERSION` and every output `schema_version` stay
  at their first value for now (see **Pushed to later steps**).

Names and interface:

- Names of settings, CLI options, files and folders are the user's to approve
  before the build step that creates them. Each step gets one folder under
  `src/pydelity/` named with an "-ing" word: `verifying/`, `assembling/`,
  `proposing/` and `projecting/` come next. Inside it, `agents.py`, `llm.py`,
  `prompts.py`, `validators.py` and `schemas.py` sit beside the step's own
  module. Outputs, logs and estimates name a step with a noun (`survey`,
  `extraction`).
- Every CLI option has a short form, and there is no `--quiet`.
- Shipped code, config, docstrings and docs never mention the development
  process: no dates, DEV or AC IDs, cycles, STANDARDS roles, KGForEdGlobal, or
  numbered steps such as "step 3". Name the step instead ("page-break
  verification", "later steps").

Platform, release and repo:

- Python 3.13 and 3.14 only, both tested in CI. Python 3.15 waits until
  `onnxruntime`, which PyMuPDF 2.x requires, ships a 3.15 build. People must be
  able to install and use pydelity on Windows, but `just` recipes that work
  there without a POSIX shell have not been a goal so far.
- Releases come from release-please, and a pull request's squash-merge title is
  the commit it reads, so it must be a Conventional Commit. `feat:` makes a
  minor release, `fix:`, `perf:`, `revert:`, `docs:` and `deps:` a patch, and
  `chore:`, `test:`, `ci:`, `build(deps):` and `ci(deps):` none. A breaking
  change below 1.0.0 would propose 1.0.0. Each cycle decides its own release,
  and its work merges to `main` only after sign-off and after STANDARDS is
  uninstalled on the branch.
- Commit messages carry no `Co-Authored-By` trailer or other AI attribution.
- A new runtime dependency's minimum version is its latest stable release on the
  day it is added.
- STANDARDS is not installed on every branch, `main` included, so scripts,
  `just` recipes, hooks and CI work without `.standards/`.
- Test PDFs are real public documents the user approves, under 500 KB each. A
  copy with some pages' rotation attribute changed counts when
  `tests/fixtures/pdfs/SOURCES.md` says how it was made.

Working with the user:

- Developer works `STEPWISE`. Before each build step it lists the files and
  folders it will create or change and waits for the user's review. After each
  step it stops for a go-ahead, and its report ends with the next step's plan:
  what it builds and how, the files, how it will be checked, and anything
  needing approval, such as downloads or spending. The user makes the commits.
  Developer does not edit tests, so tests of a replaced contract fail until
  Tester updates them, and the user skips the `ty` commit hook for those
  commits.
- Self-checks use the stand-in provider and PydanticAI test models. Real runs
  use the user's keys, only with their go-ahead, and record the spend. Failure
  paths a provider cannot produce on demand use fault injection in scratch
  scripts, never in pydelity code. While `PROMPT_VERSION` is not raised, real
  runs after a prompt change use new output folders or `--overwrite`.

The brief's survey design points for its checks are history, and so are three of
its page extraction design points: text-layer hints with pre-matched artifact
lines (see the hints rule above), a validator only on failed or hard pages plus
a sample (a verifier runs on all of a step's work or none), and a DPI chosen
from the page size (images are sized from the providers' limits).

## Answers to the brief's open questions

The numbers follow **Open questions for Scoper to settle with the user** in the
brief. Questions 2, 4, 5, 6, 10 and 11 are settled by the rules above, the
pipeline outcomes and **Pushed to later steps**.

- **1.** A default run goes through all six steps, with a setting to stop after
  `document.json`.
- **3.** The review list in `run.json`, a CLI summary at the end of a run, and
  an HTML report.
- **7.** Both CLI and config file, and a PDF path given on the CLI is used over
  the file's.
- **8.** A user-supplied domain schema does not seed page-profile labels, so
  changing it reruns only steps 5–6.
- **9.** The item lists stay: kind `text`, `list`, `table`, `figure`, `field`,
  `formula`, `code`, and role `heading`, `body`, `caption`, `footnote`,
  `artifact`, `navigation`, `aside`. `code` keeps its whitespace exactly, and a
  cross-page join of code is a newline with no dehyphenation (a design choice).
- **12.** Step 3's Architect picks its design, with no measured comparison
  first. The brief's options A–D, which can be combined, are inputs, not a
  closed list.

## What step 3 builds on

The code and the docs site's reference pages describe 0.2.0 in full. What step 3
most needs to know:

- **Page files are not guaranteed to follow their rules.** `pages/<NNNN>.json`
  (`PageFile` in `extracting/schemas.py`) is step 3's main input. When check
  retries run out, the last answer is kept with its failures, `container` and
  `caption_of` are `null` when the model's ref matched nothing, and a page can
  keep a `column_order` that does not fit its writing direction (the
  `reading_order` hint). Step 3 should read each page's `checks`, `hints` and
  `issues` rather than assume the shape. The survey's profile is not guaranteed
  either: its ranges can overlap or run past the PDF, and its artifact mapping
  can miss, repeat or invent IDs. `page_context` in `extracting/extraction.py`
  already resolves these for a page.
- **Item IDs can change.** IDs follow reading-order position (`p0003-007`, list
  entries `<item id>.<k>`, containers `p<NNNN>-c<nn>`). The same answer gives
  the same IDs, but a page extracted again can number its items differently, so
  an output that cites item IDs must depend on the page files it read.
- **No continuity marks.** Page extraction judges no continuity, and items and
  containers carry no continuation mark or open-top or open-bottom hint, so the
  brief's step 3 option E is out. Page furniture is extracted as items with role
  `artifact` where a reader meets them, and captions name what they caption in
  `caption_of`. Boxes are `[x0, y0, x1, y1]` in points on the displayed page,
  origin top left.
- **Reuse.** A fingerprint covers only what an output is made from, so a changed
  input reruns its own outputs and everything downstream, and nothing else. No
  verifier switch is in a fingerprint, and while a step's verifier is on, an
  output no verifier reviewed is made again. Step 3 continues this.
- **Continuation inputs.** `pdf_survey.json` `profile.continuation_notes[]` and
  `profile.start_markers[]` are the brief's survey-supplied continuation rules
  for step 3. `pdf_facts.json`'s structure summary holds only counts, whether
  the PDF is tagged and one quality rating. Option A needs the tag tree linked
  to page content, and `_walk_structure` in `surveying/probe.py` is a starting
  point.
- **Images and text.** Option B's seam images can build on
  `PdfWorker.page_image` and `PdfWorker.crop` and on the 0–1000 grid mapping in
  `extracting/rendering.py`. `extracting/text_layer.py` normalizes stored text
  for comparison (NFKC, case-folded, character trigrams that ignore spaces).
- **Extending the pipeline.** A new step adds its name to `StepName` and its
  check and hint names to `IssueName` in `review.py`, names its agents in
  `cost.jsonl` (today `surveyor`, `extractor` and `verifier`), and adds its
  estimate to `costs/budget.py`, its settings under `advanced.<step>`, its guide
  and its generated reference pages (CI fails on stale ones).
- **Tests.** `tests/fixtures/mock_providers.py` is a stand-in Anthropic and
  OpenAI server that routes answers by request content: each page request's
  first text line is `Page index <i> (page <i+1> of <n>)`, and verifier requests
  are told apart by `The extraction to review:` or
  `The survey answer to review:`. Only `irs_form_1040a_1965_scan` has canned
  answer files, so step 3 needs canned page and break answers for the PDFs it
  tests. Content already continues across breaks in `irs_w9_instructions.pdf` (a
  sentence from page 2 to page 3) and in CAPS's tables. The Japanese gazette is
  one page, so a Chinese or Japanese break needs the two-page Chinese
  Publication 1 or another PDF.
- **Real-run costs.** On 2026-11-20 (7 PDFs, 22 pages, verifier on every page)
  page extraction cost about $0.24 a page on Anthropic and $0.41 on OpenAI
  (`gpt-6.2-astra`). On 2026-11-22 (5 PDFs, 18 pages, the acceptance runs for
  0.2.0) it cost $2.09 without verifiers and $3.39 with them on Anthropic, and
  $3.00 and $4.16 on OpenAI. The five surveys cost $0.79 without the verifier
  and $1.58 with it on Anthropic, and $1.78 and $2.03 on OpenAI. The survey's
  verifier wrote 90 to 4,075 output tokens, under the estimate's 6,000.

## KGForEdGlobal sources

KGForEdGlobal (`/Users/tzz/Projects/private/idi/KGForEdGlobal`) is read-only.
Paths are under `backend/src/kgfeg/`. Step 3's source is `page_ir_verification/`
and `entries/verify_page_ir_continuity.py`, and the brief's step 3 section and
evidence E1–E10 describe it and its costs. Assembly's is `document_ir/` (such as
`stitch_segments.py`) and `entries/stitch_document_ir.py`.

KGForEdGlobal targets pydantic-ai 1.63.0 and PyMuPDF 1.26.7, so ported code
needs updating for PydanticAI 2.69 or later (output retries are
`Agent(retries={"output": n})`) and PyMuPDF 2.1 or later. Keep PyMuPDF 2.x: the
user chose it for fixes that include `get_pixmap` hangs (#5082, and #5125 on
heavily tagged pages). Page extraction did not port text-layer hints,
left-to-right rules, English word lists, boundary and continuity marks,
file-existence resume or non-atomic writes.

## Pipeline outcomes for steps 3–6

Scoped before the pipeline was split into one cycle per step.

- Page-break verification (step 3): each break gets a verdict on whether content
  continues, which items connect, the join rule for their kind (text: space, no
  space or dehyphenate; code: newline, no dehyphenation; list: continue the item
  or start a new one; table: append rows or merge a split row), how many
  repeated header rows to drop, and which repeated items above the continued
  unit to drop. The verdict also names any continuation marker on the continued
  unit, such as a row label or heading that says it continues ("(contd)",
  "continued", the brief's E9), which assembly folds into the original label.
  Code cannot find these markers, since no language-specific patterns are
  allowed. The verdict also says which containers continue across the break,
  even when the content inside starts a new unit.
- Assembly (step 4): `document.json` with a `schema_version`, every item
  accounted for exactly once, joins only where verdicts say so, per-item
  provenance kept, and artifacts out of the reading flow unless
  `keep_headers_footers` is set. An outline tree of headings, with
  `section_path` as outline ancestors outermost first. Contents-page mismatches
  and cross-page role or kind inconsistencies go on the review list. The pieces
  of a box that crosses pages join into one container, using step 3's verdicts.
  Each list item gets an ID, and table grids mark spans as spans, plus a
  filled-down view for grouped tables unless `fill_down` is off.
- Domain schema (step 5): without a user schema, `schema_proposed.json` (`x-key`
  on every array of objects with required key fields, `x-verbatim` only on
  strings, a place for content that is not a main record) and `schema_notes.md`
  mapping every outline section to a path or an exclusion reason. A user schema
  skips the proposal. Unknown `x-*` annotations pass through.
- Projection (step 6): `domain.json` validates against the schema, `x-verbatim`
  strings match their cited items, cited IDs exist, objects get stable IDs from
  their key paths, arrays follow document order, and conflicting values go on
  the review list. A coverage report lists uncited content items, verbatim
  retries and merge conflicts.
- KGForEdGlobal compatibility: segment IDs follow today's recipe and are stable
  across reruns, boxes are in PDF points, and an item ID to segment ID lookup is
  included. `document.json` holds the data an adapter needs for each KG field in
  use today and for CAPS requirement boxes as one-column tables, with a written
  mapping of where each comes from. Each KGForEdGlobal `TextUnit` needs a BCP-47
  `language`, which page items with text already carry. KGForEdGlobal's KG stage
  loads `stitching/document_ir.json` with `extra="forbid"` models, so even a
  top-level `schema_version` fails there, and reading pydelity's output needs
  KGForEdGlobal-side changes outside pydelity's cycles. The brief's field-use
  counts are substring matches. Whole-word counts are lower for `segment_id`
  (38, not 223), `section_path` (23, not 72), `grid_sources` (46, not 53) and
  `columns_signature` (19, not 31).
- Each later step extends the cross-cutting outcomes (configuration, CLI and
  library use, cost and spend controls, resume, providers and tests, the review
  list and HTML report, user docs) to its own outputs.

## Open for step 3's Scoper and Architect

- Which of the brief's options A–D step 3 uses, alone or combined, and whether a
  validator reviews every break, some (option D) or none.
- Which breaks a run checks when `pages` selects only some pages, for example
  only breaks between two selected pages that follow each other.
- Step 3's other settings and output files (the brief proposes
  `page_breaks/NNNN-NNNN.json`), and how its fingerprint covers the two page
  files each break reads. The default run includes step 3, and the entries under
  **Pushed to later steps** for step 3 and for each later step apply.
- How text joins inside a list entry or table cell that continues across the
  break. The brief's join rules cover only text items, today's KGForEdGlobal
  join always inserts a space and knows only Latin sentence ends, and code
  cannot choose without language rules, so the verdict likely has to give it.
- Which release the cycle ships, such as 0.3.0.

## Constraints and non-goals still in force

- The PDF path is the only required input. Configuration is one optional JSON or
  YAML file with an `advanced:` section, and a normal run resumes. The domain
  schema is JSON Schema data with `x-key` and `x-verbatim`, never Python source.
  Consumer-specific needs go in `document.json` fields or the consumer's
  adapter. Automated tests mock every model call and make no network calls to
  providers. Target maturity is Level 3 (internally testable).
- The repo setup stays as it is unless a cycle needs a change. "Lint and test"
  and "TruffleHog secret scan" stay required checks on `main`.
- Non-goals: any change to KGForEdGlobal; KG, Learning Component and Learning
  Progression logic; generating KG config from a pydelity schema; splitting or a
  chunked survey for PDFs a provider rejects as too large; a hosted service, a
  web UI beyond the HTML report, telemetry and other Level 4 features.

## Risks

- Prices and model IDs drift. Prices follow `genai-prices` releases, and
  `advanced.models` covers a model it does not know yet. Older models that
  reject adaptive thinking, `effort` or `reasoning_effort`, or an OpenAI model
  without `detail: "original"`, fail with the provider's error.
- A request that times out or is canceled on pydelity's side may still be billed
  at the provider, with no ledger line, and concurrent requests multiply it.
- Eight concurrent page requests can hit low provider rate limits. Lowering
  `concurrent_pages` is the remedy.
- A step that streams should add a test of `LedgerModel` on streamed requests,
  which nothing covers yet. Non-streaming requests with a large
  `max_output_tokens` need an explicit request timeout.
- Two runs in one process can run PyMuPDF on two threads at once (each has its
  own `PdfWorker`, and the report and the probe use `asyncio.to_thread`). It has
  not been seen to fail.
- The cost estimate is a heuristic. Maximums assume every retry with the longest
  answer, prompt text is counted at 4 characters a token, which undercounts
  non-Latin text, and request bounds price input at the plain rate though
  Anthropic bills cache writes at 1.25 times.
- Prompted output on Anthropic has no grammar behind it, so an answer that is
  not valid JSON costs a retry and, on the last attempt, stops the run. A dense
  page can exceed 32,000 output tokens at effort `high` and stop the run with
  `ExtractionError`. Claude Opus 5.5 can stop with `refusal`, which is a
  failure. Server-side refusal fallbacks are off because they change the billed
  model mid-request.
- Uploaded PDFs stay in the user's provider storage until they expire (90 days
  on Anthropic by default).
- A `langcodes` release that changes a tag's standard form changes fingerprints.
- The review list is the only signal when the model is wrong. A verifier that
  wrongly passes, or a kept correction that drops or adds a line, keeps that
  difference off the list, visible only in the output's `hints`. Without
  verifiers, which is the default, nothing beyond the checks catches missed or
  merged items, a wrong reading order or boxes on the wrong content.
- One changed word in a long line stays within the text hints' tolerance, so
  single-word misreadings never reach the review list. The 2026-11-22 runs had a
  few in Arabic (such as `بشأن` for the printed `بشان`) and Japanese (such as
  `明治三十五年` for `明治二十五年`), at the earlier runs' rate.
- The hint rule was not tried on the GPF reading and math PDFs, where the
  earlier text check's retries made models merge each grade grid's nine grade
  cells into one. The cause is gone, but whether models keep those cells apart
  is not shown.
- Probe mistakes, such as numbers in table cells or page labels on pages that
  print no number, reach the review list as `page_number_differs`. Keeping page
  labels apart from printed text would cut that noise and changes the facts
  schema.
- The `artifacts` hint trusts the model's boxes, and one covered occurrence is
  enough. The text hints can flag text read from pictures, and can be misled by
  right-to-left text stored in visual order or legacy encodings rated `good`.
- Every repeated line (up to 1,000) goes with the survey request. The survey's
  region boxes are often off, and page boxes rest on the models (see **Pushed to
  later steps**).
- One run per output folder at a time, which is not detected. On Windows,
  `os.replace` fails while another program holds the target open. Large PDFs
  make large reports.
- `docs/pnpm-lock.yaml` may approach the large-file hook's 500 KB limit. If it
  goes over, exclude that one path with a comment.

## Observations left for later

Still open from page extraction's implementation review:

- An interrupted `overwrite` can leave an old page file naming a crop the new
  answer overwrote, since crops are named by item position and written first.
- Temporary files in `pages/` or `figures/` are removed only when a page is
  extracted, and the provider image limits that size page images are not in the
  page fingerprint.
- A structure walk cut short at its cap (more than 20,000 elements) can count an
  unreached page as untagged when the tree is out of page order.
- Page JPEGs have no byte cap (synthetic grain reached 3.7–6.1 MB for a Letter
  page, against about 5 MB for Anthropic, not checked against its current docs),
  and figure crops have no pixel cap (a full-page figure on a 36 x 48 in page
  takes about 0.8 GB to render).

From the verifier cycle's reviews:

- The survey verifier's replacement upload after a 404, and a catalog `Outlines`
  entry naming a missing object, have no test of their own.
- A survey verifier problem's `page_index` is not checked against the page
  count, so an out-of-range one links nowhere in the report.
- The CLI reference's exit code `0` leaves out a paused run, and a run stopped
  at the spending question lists `pages/` and `figures/` before they exist.

From page-break verification's implementation review (limitations of the checks,
none of which makes a verdict wrong unless the model has already erred):

- `repeats` accepts containment of any length, so a wrongly named repeated item
  passes when its text contains a page number or a word printed anywhere on page
  N, and assembly would drop it with no review line when no verifier runs.
- `repeats` skips repeated items with no text, such as a table or list named as
  repeated.
- `duplicates` is per item. When page N's last list entry carries on as a text
  item and the list goes on as a separate list item on page N+1, the correct
  verdict needs two pieces ending in the same list item and fails `duplicates`.
- `header_rows` uses text similarity only, so a repeated header row with a
  continuation word in a short cell can score below 0.8 and fail a correct
  count.
- A marker made only of symbols, such as "→", always passes `markers`, because
  its comparison form is empty.
- A `ProviderError` from a break names the step and the earlier page
  (`page_breaks, page 4 (index 3), judge`), not both pages as a `PageBreakError`
  does.

From the user's real runs:

- The providers structure some pages differently (OpenAI put the ten rights on a
  Chinese page in one list where Anthropic gave 20 heading and body items, and
  marks more containers). Both fit the rules, so later steps must not assume one
  provider's structure.
- In one run, the one-page Japanese gazette's survey made no label for page
  furniture, so its furniture items got the label `other` with
  `no_matching_label` issues.
- Under the hint rule, no model made up a field for the Japanese gazette's 0.6 x
  0.8 pt `Signature1` widget. It is a `form_fields` review issue without a
  verifier, and both verifiers accepted the page.
- Not exercised by real runs: a filled or handwritten form value, a page that is
  one picture, and Ctrl+C at a CLI question on Windows.

## Loose ends

- After the merge, check that release-please opens the 0.2.0 release pull
  request (tag `v0.2.0`) from the `0.1.1` manifest, and that merging it
  publishes 0.2.0 to PyPI and the docs site.
- Node `24.22.3` is kept by hand in two hooks in `.pre-commit-config.yaml` and
  in `docs.yml`. `docs/package.json`'s `engines.node` follows the locked Astro's
  minimum.
- Repo-setup risks: Dependabot's uv can lag below `required-version`, and
  Dependabot ignores setuptools, whose `[build-system]` minimum is kept by hand.
  Hand-kept pins (the uv bound, CI's uv, Node, Prettier) go stale unless bumped,
  and a Prettier bump can reformat many files. zizmor's online audits can fail
  CI when an advisory names an action the repo uses. prek is pre-1.0. PyPI
  versions are permanent.

## Pushed to later steps

Work moved out of a step, naming the step that picks it up. Add to this list
whenever work is moved out of the current step.

- **Translation (after assembly, step 4 or later).** An optional step that
  translates extracted text into a target language the user sets, worth having
  for other uses though KGForEdGlobal does not translate. A run for
  KGForEdGlobal leaves it off. Translating after assembly keeps text continued
  across a break as one unit.
- **Pauses between steps (each later step).** A run stops after a step that
  wrote new output, so the user can check it before paying for the next, and the
  next run continues. `pause` (`--no-pause`/`-np`) turns every pause off. Each
  later step adds its own pause under the same setting.
- **Model per step (each later step).** The global `model` chooses every step's
  model, and each later step gets an optional `advanced.<step>.model`, as page
  extraction has (the survey has none). With neither set, every step defaults to
  `anthropic:claude-opus-5-5` at effort `high`, from its own default constant in
  `providers/profiles.py`.
- **Verifier per step (each later step).** Every step's verifier is off by
  default. `verify` (`--verify`/`-vf`, `verify=True`) turns on every step's
  verifier, and each step has an optional `advanced.<step>.verify` (`true`,
  `false`, or `null` to follow `verify`), with no CLI option. Each later step
  adds that override, a `Config.verify_<step>` property, `verification: null` in
  its outputs when no verifier ran, and an estimate that prices the verifier
  only when it runs.
- **Instructions per step (each later step).** Each step's instructions live in
  `advanced.<step>.instructions`, set in the config file or from Python with no
  CLI option, and go only to that step's models.
- **Raising internal versions again (not yet decided).** When to raise
  `PROBE_VERSION`, a `PROMPT_VERSION` or an output `schema_version` for changed
  outputs again, and when pydelity starts keeping backwards compatibility, is
  open, likely once it has public users.
- **Continuation between pages that do not follow each other (assembly, step 4,
  or later).** Page-break verification judges only page N against page N+1, so
  text that jumps to a later page, or a table interrupted by an inserted
  full-page figure, gets no verdict that joins it.
- **A page with no content items between two pages (assembly, step 4).** A break
  where either page has no content item (a blank page, or one with only page
  furniture) gets a `no_content` verdict that nothing continues, with no
  request. Whether a unit that continues around such a page should be joined
  across it is open.
- **"Continued on the next page" notes on the earlier page (page-break
  verification or assembly, not yet scheduled).** The verdict names markers on
  the continued unit on page N+1 and repeated items above it, but not a note on
  page N that says the content continues, so assembly would keep such a note in
  the joined text.
- **Structure tags as evidence (page-break verification, not yet scheduled).**
  The brief's option A. Tags exist on some PDFs only, and nothing links them to
  page extraction's items yet, so that link is new probe work.
- **Snapping boxes to measured text (page extraction, not yet scheduled).** A
  few boxes sit off their text, such as a Chinese footer's box about 7 pt below
  its line and a vertical Japanese line's about 9 pt to its left. Moving a box
  onto the text layer's words for the item could tighten them on pages with a
  good text layer.
- **Judging each page's stored text (page extraction, not yet scheduled).** The
  text hints skip a page with no text layer, a garbled one, and one where fewer
  than half of the answer's trigrams are in the text layer. Pages whose stored
  text is wrong in part still list differences the model is right about, such as
  22–23 issues for the two Arabic test pages and 7–8 for the Japanese gazette
  without verifiers in the 2026-11-22 runs. Comparing the stored text with the
  model's reading first, and skipping the hints when the stored text is wrong,
  would cut that noise.
- **Two box rules for the page prompt (page extraction, not yet scheduled).**
  The prompt has no rule for a paragraph that continues at the top of the next
  column (two Chinese items' text held the continuation while their boxes
  covered only the first column), and does not say whether a field's box
  includes its printed label (OpenAI's W-9 boxes covered only the input area,
  Anthropic's took in the label). The user accepted both for 0.2.0. Changing the
  prompt raises the question of versions above.

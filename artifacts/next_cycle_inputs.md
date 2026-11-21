# pydelity: inputs for page-break verification (step 3)

Two steps of the pipeline are built, in three STANDARDS cycles:

- The survey (step 1), in the cycle
  `build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c`, released as
  0.1.0 (squash commit `c63d891` on `main`, pull request 4) and 0.1.1, a docs
  fix.
- Page extraction (step 2), in the cycle
  `build-step-2-page-extraction-of-the-20261119T174118Z-0419318a` on branch
  `tz6/pipeline-step-2` (pull request 10), signed off on 2026-11-20.
- The verifier cycle,
  `add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada`, on the
  same branch after page extraction (see **The verifier cycle, before step 3**).
  Page extraction and the verifier cycle merge together and ship as 0.2.0 (see
  **Loose ends**).

STANDARDS is uninstalled before each merge to `main`, which removes the cycles'
records, so they live only in git history:

- Survey cycle: commit `83743ef`. A clone that lacks it gets it with
  `git fetch origin pull/4/head`.
- Page extraction cycle and the verifier cycle after it: until the verifier
  cycle ends, both cycles' records are on `tz6/pipeline-step-2` under
  `.standards/docs/`. After that, they are in the parent of the commit that
  uninstalls STANDARDS on the branch. A clone that lacks it runs
  `git fetch origin pull/10/head`; then
  `git log -1 --format=%h --diff-filter=D FETCH_HEAD -- .standards/STATE.md`
  names the uninstall commit, and its parent holds both cycles' records.

In either commit the records are
`.standards/docs/<scope|specs|development|verification|documentation|synchronization>/<cycle id>.md`
and `.standards/docs/reviews/<cycle id>/<implementation|final-deliverable>.md`.
For example,
`git show 83743ef:.standards/docs/specs/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c.md`
prints the survey's design. Page extraction's design (decisions 1–22) is in its
`specs/` record.

This file keeps what the next cycle needs from those records. The full request,
design directions, each step's design points (including **Step 3 (page-break
verification): options to consider; not decided**), known source defects,
evidence E1–E23 and the KGForEdGlobal consumer contract are in
`artifacts/design_brief.md`. Where the brief and this file disagree, this file
is newer. Earlier versions of this file, written for the survey and page
extraction cycles, are in git history.

Nothing here is an acceptance condition. Each cycle numbers its own AC IDs, and
old numbers mentioned here are retired.

## The verifier cycle, before step 3

What the verifier cycle settled for 0.2.0, in short. Its scope, design and
documentation records hold the details and are newer than this file where they
differ.

- Every step's verifier is optional and off by default. `verify` (config file,
  `--verify`/`-vf`, Python `verify=True`) turns on every step's verifier, and
  `advanced.survey.verify` and `advanced.extraction.verify` (`true`, `false`, or
  `null` to follow `verify`) override it for one step, in a config file or from
  Python only. `Config.verify_survey` and `Config.verify_extraction` resolve
  them, and each step reads only its own.
- The survey has a verifier like page extraction's: after the survey's answer is
  accepted, a second request to the survey's model with the survey's
  instructions reviews it against the PDF (on the same upload) and may return a
  full corrected `SurveyAnswer`, kept only when it passes every survey check.
- With a step's verifier off, every difference goes on the review list: every
  failing check, page extraction's `text_dropped` and `text_added`, and the
  survey's `rotation_differs` and `page_number_differs`. With it on, a
  difference is left off when the verdict passed or its correction was kept.
- `PdfSurvey.verification` and `PageFile.verification` are `null` when no
  verifier ran. No fingerprint holds a verifier switch. A saved output with
  `verification: null` is not reused while its step's verifier is on, and one a
  verifier reviewed is reused after the verifier is turned off.
- Every request names its agent in `cost.jsonl`: `surveyor` or `verifier` for
  the survey, `extractor` or `verifier` for page extraction. `LedgerEntry.agent`
  is required. Estimates price a verifier only when it will run
  (`StepEstimate.verifier`).
- The cycle also fixed `load()` for another PDF's page files, report tables with
  spanning header cells, outline links to missing objects, inline form widgets,
  the `TEXT_FLAGS` comment and the docs wording page extraction's final review
  found, and reordered every module to the user styles' ordering rule.

The user's request (2026-11-20), kept for reference:

1. The survey gets the producer and verifier approach page extraction has: after
   the survey's answer is accepted, a verifier request reviews it against the
   PDF and may return a corrected answer, which must pass the survey's checks.
   This replaces the survey cycle's rule that the survey uses Python checks
   only.
2. The verifier is optional for every step, and the user opts in to it.
3. Finish the remaining issues. The candidates, for the Scoper to settle with
   the user: the page extraction entries under **Pushed to later steps**
   (another PDF's page files in `load()`, snapping boxes to measured text,
   judging each page's stored text, the two box rules for the page prompt); the
   items under **Review findings and observations left for later**; and any risk
   under **Risks and follow-up** the user wants closed.

The request's points for its Scoper and Architect:

- Opt-in turns off by default what 0.2.0's page extraction does on every page
  (its scope's `AC-064`, design decision 10). Without a verifier, a page keeps
  its extraction with no pass, so under today's rule its text differences go on
  the review list. That brings back the review noise the user removed for pages
  whose stored text is wrong, such as the Arabic and Japanese test pages, and
  nothing then catches missed or merged items, a wrong reading order in a
  complex layout, or boxes on the wrong content. The cycle needs a rule for text
  differences when no verifier runs. In the user's real runs the verifier was
  28% of page extraction's cost on Anthropic ($1.48 of $5.38) and 35% on OpenAI
  ($3.18 of $9.02).
- A survey verifier sends the whole PDF again (it can reuse the upload in
  `uploads.json`), so a verified survey costs roughly twice as much. The surveys
  in the real runs cost $0.98 on Anthropic and $2.09 on OpenAI for 7 PDFs.
- Design choices: the setting's shape (one per step under `advanced.<step>`, or
  one global setting with per-step overrides), how it enters each step's
  fingerprint and estimate, what the page file's `verification` field and the
  report hold when no verifier runs, and what the survey's verifier may correct.
- The user decisions below apply, including acceptance by real runs on both
  providers and one structured-output mode per provider.
- The cycle's work merges with page extraction and ships with it as 0.2.0. Step
  3 follows, as the rest of this file describes.

## User decisions that apply to later steps

Made while scoping the pipeline (2026-11-16), during the survey cycle
(2026-11-17 to 2026-11-19) or during the page extraction cycle (2026-11-19 to
2026-11-20). Where a rule was a design's choice rather than the user's, the
bullet says so, and a later Architect may revisit it.

- Acceptance of each step rests on the user's review of real runs with Anthropic
  and OpenAI models on PDFs of their choice, covering two-column right-to-left,
  Chinese or Japanese, a tax or fillable form, a slide deck or image-heavy PDF,
  and CAPS. There is no numeric parity target with KGForEdGlobal, and cost is
  reported with no pass/fail target. Page extraction was accepted on Publication
  1 in Arabic and in Chinese, the Japanese gazette, W-9 page 1, the scanned 1965
  form, slides 1–6 and CAPS, all from `tests/fixtures/pdfs/`.
- Reuse before rewriting: pydelity ports over KGForEdGlobal's code and reuses
  what fits, and writes new code where it does not fit. Ported code must not
  carry the defects listed in `artifacts/design_brief.md`. KGForEdGlobal
  (`/Users/tzz/Projects/private/idi/KGForEdGlobal`) is read-only.
- Document-type agnostic: no core logic, prompt, output field or default may
  assume a document type, a language or a writing direction. There is no
  hand-written per-document config, no domain Pydantic class and no
  language-specific word list or pattern. Document-specific knowledge comes only
  from the survey's profile and the instructions the user gives each step.
- The model's reading is trusted over measured facts such as the text layer.
  Code may send an answer back with the difference it found, but the model's
  last answer is kept, and any difference left goes on the review list. Page
  extraction applies this strictly. Its design (decision 21, after real runs)
  sends no text-layer lines as hints, so the models read the text from the page
  image. A text difference goes back with a note that the model may keep its
  reading. On a page no verifier reviewed, every text difference is listed for
  review. With the verifier on, text differences are listed only when the
  verifier did not pass the page and the page keeps the extraction. The verifier
  cycle applied the same rule to the survey's comparisons with the facts. A
  PDF's stored text can be wrong (broken Arabic letter forms, ligatures,
  private-use characters), so stored text is evidence, never the answer.
- Each check sits where it can be enforced: Pydantic classes for shape,
  `<step>/validators.py` for what code can decide, and a verifying model for
  what code cannot judge. Each step's verifier is a second request to that
  step's own model with that step's instructions only, and it is opt-in (see
  **Pushed to later steps**). With its verifier on, page extraction sends every
  page to it with the page image, the answer and its remaining check failures,
  and the survey sends the PDF with the answer, its failing checks and its
  differences from the facts. Either may return a full correction. The brief's
  terms differ: there the "verifier" is the model that makes step 3's main
  judgment on each break, and a "validator" is a second model that reviews it,
  which is the role page extraction's verifier plays. Whether step 3 has a
  validator on every break, only on some (the brief's option D) or none is step
  3's design.
- pydelity ships no per-model limits and checks none before a model call. The
  provider enforces its own limits, the CLI shows the provider's error, and the
  Python API raises `ProviderError` carrying it. Extending this to all per-model
  data was the survey design's choice. Page extraction's design (decision 4)
  keeps each provider's documented image limits in `providers/profiles.py`, as
  provider facts, to size its page images.
- There is no default `max_cost`. When a run would go over it, pydelity warns
  and the user decides. The CLI asks (`--yes` answers yes), at most once per run
  by the survey design's choice (decision 11), and Python callers pass
  `allow_over_max_cost=True` or get `BudgetExceededError` and a run they can
  resume. Page extraction's design (decision 12) added a reservation for each
  request in flight, counts images in each request's bound, and makes the
  plan-time check use the expected cost instead of the maximum, so the question
  can come partway through a run.
- The number of provider retries is a setting. The survey design made it one
  setting, `advanced.provider_retries` (0 to 10, default 2), shared by model
  requests and uploads, with no retry layer of pydelity's own. Each step has its
  own `check_retries` under `advanced.<step>`.
- Every Python function that measures, estimates or runs has an async version
  named with an `a` prefix (`arun`, `asurvey`, `aextract`, `ameasure`,
  `aestimate`). The sync functions use `asyncio.run` only and raise
  `RuntimeError`, naming the async function to await, when called inside a
  running event loop. `load` stays sync (the survey design's choice, kept by
  page extraction's scope). The docs lead with the async functions and mention
  the sync ones as the same names without the `a` (the user's request,
  2026-11-20).
- Language tags are checked with `langcodes` and stored in standard form (the
  survey design's choice). Page items carry a BCP-47 `language` (page
  extraction's design).
- People must be able to install and use pydelity on Windows. `just` recipes
  that work on Windows without a POSIX shell were a non-goal of both cycles;
  whether a later cycle takes them up is the user's call.
- Python 3.13 and 3.14 only, both tested in CI. Python 3.15 waits until
  `onnxruntime`, which PyMuPDF 2.x requires, ships a 3.15 build, and Python 3.14
  on a Mac needs macOS 14 or later. `requires-python` is `>=3.13`. The built
  wheel is smoke-tested on Linux, macOS and Windows (the survey design's
  choice), and the smoke test runs the survey and page extraction against the
  stand-in provider.
- Releases come from release-please. A pull request's squash-merge title is the
  commit message, so it must be a Conventional Commit. With the Python release
  type's changelog sections, which this repo does not change, `feat:` makes a
  minor release; `fix:`, `perf:`, `revert:`, `docs:` and `deps:` make a patch
  release; `chore:`, `test:`, `ci:`, `build(deps):` and `ci(deps):` make none. A
  breaking change below 1.0.0 would make release-please propose 1.0.0. Work
  merges to `main` only after its cycle is signed off and STANDARDS is
  uninstalled.
- Commit messages carry no `Co-Authored-By` trailer or other AI attribution.
- One structured-output mode per provider, for every step: prompted output on
  Anthropic and native output on OpenAI (the user's choice, page extraction's
  decision 20). Anthropic compiles a native output schema into a grammar whose
  limits page extraction's answer exceeded, and those limits can change, so no
  step depends on them, even one whose answer fits today, as the survey's does.
- `examples/config.json` and `examples/config.yaml` hold every setting at its
  default, and a test keeps them complete, so a new setting goes into both.
- PyMuPDF 2.x is pydelity's PDF library, and the user accepted its AGPL-3.0
  license (pydelity itself stays MIT). PyMuPDF is not safe across threads, so
  page extraction's design (decision 11) runs every PyMuPDF call of the step on
  one worker thread per run (`PdfWorker` in `extracting/rendering.py`), one call
  at a time.
- PDF transport, for every provider and whenever a step sends the PDF: upload
  the PDF with the provider's file API when it has one, send it inside the
  request only when the upload path fails, keep uploads until they expire at the
  provider, and treat a provider that offers neither as unusable. The survey
  records its upload in `uploads.json`, so a later step that sends the PDF can
  reuse it. Page extraction never sends the PDF or uses the upload; it sends
  page images it renders itself.
- Test PDFs are real public documents that the user approves, under 500 KB each,
  never generated ones. A copy of an approved test PDF with some pages' rotation
  attribute changed counts as a real test PDF when
  `tests/fixtures/pdfs/SOURCES.md` says how it was made.
- The CLI has no `--quiet`. By default it shows warnings, errors, the cost
  estimate and the summary, and `--verbose` shows everything. Every option has a
  short form (`-mc` for `--max-cost`, `-p` for `--pages`, `-np` for
  `--no-pause`), so options step 3 adds need one too.
- File and folder names are the user's to approve, before the build step that
  creates them. Each pipeline step gets one folder directly under
  `src/pydelity/`, named with an "-ing" word so it never collides with a public
  function: `surveying/`, `extracting/`, then `verifying/`, `assembling/`,
  `proposing/` and `projecting/`. Inside a step folder, model code follows
  KGForEdGlobal's split (`agents.py`, `llm.py`, `prompts.py`, `validators.py`,
  `schemas.py`), beside the step's own module (`surveying/survey.py`,
  `extracting/extraction.py`). Outputs, logs and estimates name a step with a
  noun, `survey` or `extraction` (page extraction's design, decision 1).
- pydelity keeps no backwards compatibility while it has no public users:
  renamed or removed settings, options, functions and output fields get no
  aliases, deprecation warnings or migrations, and no field gets a default only
  so that older files still load. Internal versions (`PROBE_VERSION`, each
  step's `PROMPT_VERSION`, every output `schema_version`) were not raised for
  either cycle's changes, and a new step's versions start at 1. When to change
  either rule is open (see **Pushed to later steps**).
- Pages to extract are chosen with `pages` (numbered from 1, such as `1-5,8`;
  `--pages`/`-p`; every page when unset). The survey always reads the whole PDF,
  and narrowing the selection leaves other page files in place.
- Pauses, a model per step and instructions per step follow the entries under
  **Pushed to later steps**.
- How the user works with Developer: `STEPWISE` collaboration. Before each build
  step, Developer lists the files and folders it will create or change and waits
  for the user's review; after each step it stops for a go-ahead, and its report
  ends with the next step's plan (what it builds and how, the files, how it will
  be checked, and anything needing approval, such as downloads or spending). The
  user makes the commits. Tests belong to Tester, so Developer does not edit
  them; tests of a replaced contract fail until Tester updates them, and the
  user skips the `ty` commit hook for those commits.
- During development, self-checks use the stand-in provider and PydanticAI test
  models; real Anthropic and OpenAI runs use the user's keys, only with their
  go-ahead, and record the spend. Failure paths a provider cannot produce on
  demand use fault injection in scratch scripts, never in pydelity code. Since
  `PROMPT_VERSION` is not raised, real runs after a prompt change use new output
  folders or `--overwrite`.
- Page extraction's reviews kept only major issues (the user's bar, 2026-11-20):
  a finding must, on input the release targets, make the delivered output wrong,
  lose money, fail a run, or break a function the acceptance review relies on.
  Confirmed problems below that bar were recorded as limitations. Ask the user
  whether step 3's reviews use the same bar.
- A new runtime dependency's minimum version is its latest stable release on the
  day it is added.
- Code conventions from the user's reviews: private globals, classes and
  functions come before public ones in each module, alphabetical within each
  group; American English throughout; plain language in docstrings; each step's
  checks on model answers live in `<step>/validators.py`; prompts return a
  `PromptPair` from `src/pydelity/utils/prompts.py`, written the way
  KGForEdGlobal writes its prompts; output schema versions live in
  `src/pydelity/schema_versions.py`; `justfile` recipes and `pyproject.toml`
  tables, keys and lists stay alphabetical.
- Shipped code, config, docstrings and docs never mention the development
  process: no decision dates, DEV or AC IDs, cycles, STANDARDS roles,
  KGForEdGlobal, or numbered pipeline steps such as "step 3". Name the step
  instead ("page-break verification", "later steps").
- STANDARDS is not installed on every branch, `main` included, so scripts,
  `just` recipes, hooks and CI must work without `.standards/` and skip
  STANDARDS-specific work when it is absent.
- Work moved out of the current step goes in **Pushed to later steps** at the
  bottom of this file, naming the step that picks it up.

These decisions replace earlier plans in the brief:

- The brief's per-model PDF limits, checked before the model call, are dropped.
  pydelity keeps no limits and checks none.
- Going over `max_cost` no longer stops a run on its own.
- The brief's **Step 1 (survey) design points** for its checks are history, and
  so are three of its **Step 2 (page extraction) design points**:
  - Text-layer hints and pre-matched artifact lines. A page request carries the
    page's repeated lines with how the survey classified them, and its form
    fields with their values, but no other text-layer lines. Text-comparison
    failures sent back to the extractor or the verifier do quote stored lines.
    The `artifacts` check finds page furniture by position.
  - A validator only on pages that failed checks or are hard, plus a random
    sample. A step's verifier runs on all of that step's work or on none of it.
    Step 3's option D proposes the conditional pattern for breaks.
  - A DPI chosen from the page size. Page images are sized from the providers'
    image limits instead.
- Containers carry no open-top or open-bottom hints, and step 2 judges no
  continuity, so the brief's step 3 option E is out.
- The pipeline is not released only once all six steps are done. Each cycle
  decides its own release: 0.1.0 shipped the survey, and 0.2.0 ships page
  extraction.

## Answers to the brief's open questions

The numbers follow **Open questions for Scoper to settle with the user** in
`artifacts/design_brief.md`.

1. A default run goes through all six steps, projection included, with a setting
   to stop after `document.json`. In 0.2.0 `pydelity <pdf>` runs the survey and
   page extraction, pausing after a new survey unless `pause` is off.
2. Yes. The CLI shows an estimate and asks before spending, `--yes` skips the
   question, and the Python API never asks.
3. Both: the review list in `run.json`, a CLI summary at the end of a run, and
   an HTML report.
4. No parity target. Acceptance rests on the user's review of real runs on PDFs
   of their choice.
5. Two-column right-to-left, Chinese or Japanese, tax or fillable forms, and
   slide decks or image-heavy PDFs, plus CAPS.
6. Each step has its own default model, so far `anthropic:claude-opus-5-5` at
   effort `high` for both. The global `model` setting sets every step, and
   `advanced.extraction.model` overrides it for page extraction; each later step
   gets its own override. The survey has none. There is no default `max_cost`.
7. Both, and a PDF path given on the CLI is used over the config file's.
8. No. A user-supplied domain schema does not seed page-profile labels, so
   changing it reruns only steps 5–6.
9. The `kind` and `role` lists, unchanged by page extraction: kind `text`,
   `list`, `table`, `figure`, `field`, `formula`, `code`; role `heading`,
   `body`, `caption`, `footnote`, `artifact`, `navigation`, `aside`. Changing
   them would change the output `schema_version` once versions are raised again
   (see **Pushed to later steps**). `code` keeps its whitespace and line breaks
   exactly, and a cross-page join of code is a newline with no dehyphenation
   (the survey design's decision 8, which a later Architect may revisit).
10. Option (a): bordered or shaded boxes become containers. Page extraction
    records them on each page, and assembly joins a box that crosses pages into
    one container (see **Pushed to later steps**).
11. pydelity keeps no per-model limits (see above).
12. Step 3's Architect picks its design, with no measured comparison first. The
    brief's options A–D, which can be combined, are inputs, not a closed list.
    Option E is out.

## What 0.2.0 provides for step 3

- **Layout.** `src/pydelity/` holds `api.py`, `cli.py`, `config/`, `costs/`,
  `errors.py`, `extracting/`, `pipeline/`, `providers/`, `report/`, `review.py`,
  `schema_versions.py`, `surveying/` and `utils/`. `extracting/` holds
  `agents.py`, `extraction.py` (the step: page plan, reuse, page tasks and
  writing), `llm.py`, `prompts.py`, `rendering.py` (page images, crops, the box
  mapping and `PdfWorker`), `schemas.py`, `text_layer.py` and `validators.py`.
  `extracting` imports `surveying.schemas`, `surveying.probe` (`line_boxes`),
  `surveying.validators` (`covering_range`) and `review`; `surveying` never
  imports `extracting`, and `pipeline` imports both.
- **Output folder.** One folder per PDF is the unit of resume and spend:
  `run.json`, `pdf_facts.json`, `pdf_survey.json`, `cost.jsonl`, `uploads.json`,
  `report.html` with its page images in `report/pages/<NNNN>.jpg`, the page
  files `pages/<NNNN>.json` (`NNNN` is the 0-based page index) and the figure
  crops `figures/<item id>.png`. Every JSON and HTML file is written atomically
  and validated on load, and a later run removes temporary files left by an
  interrupted write.
- **Page files**, the main input to step 3 (schema version `1.0`,
  `PAGE_SCHEMA_VERSION`):
  - Page fields: `page_index` (0-based), `page_number` (1-based), `width_pt` and
    `height_pt` of the displayed page (after its rotation attribute), `rotation`
    (the clockwise degrees applied to read it upright), `writing_direction`
    (`ltr`, `rtl` or `ttb`), `column_order` (how the columns of a `ttb` page are
    read, `left_to_right` or `right_to_left`, else `null`) and `image` (the size
    of the image the models saw).
  - `items`, in reading order, each with `id`, `kind`, `role`, `label`, `bbox`,
    `language`, `container`, `caption_of`, `text`, `latex`, `entries`, `table`,
    `figure` and `field`. Fields that do not go with the item's kind should be
    `null`: `text` and `code` use `text`; `formula` uses `text` and `latex`;
    `list` uses `entries` (each with `id`, `marker`, `text` and `level`);
    `table` uses `table` (`rows` of cells with `text`, `row_span` and
    `col_span`, HTML-style, with covered cells left out, and `header_rows`);
    `figure` uses `figure` (`description`, `text` and `crop`, the crop's path in
    the output folder); `field` uses `field` (`field_type`, `prompt`, `value`,
    `checked`, `options` and `fillable_name`).
  - These rules are checks, not guarantees. The `content` check (and, for
    `column_order`, the `reading_order` check) sends a wrong answer back while
    check retries remain, but the last answer is kept with its failures listed.
    `container` and `caption_of` are left `null` when the model's ref matches
    nothing. Step 3 should read a page's `checks` rather than assume the shape.
  - `bbox` is `[x0, y0, x1, y1]` in points on the displayed page, origin top
    left, as the survey's regions and form fields are.
  - Item IDs come from reading-order position, `p<NNNN>-<nnn>` from 1 (such as
    `p0003-007`), and list entries are `<item id>.<k>`. Container IDs,
    `p<NNNN>-c<nn>`, follow the order the answer lists the containers. The same
    answer always gives the same IDs, but a page extracted again with a
    different answer can number its items differently, so an output that cites
    item IDs must depend on the page files it read.
  - `containers`, each with `id`, `bbox`, `label` and `container` (the box it
    sits in, if any). Items inside a box name it in `container`. No item or
    container carries a continuation mark or an open-top or open-bottom hint.
  - Page furniture (running headers, footers, page numbers) is extracted as
    items with role `artifact`, where a reader meets them. Captions name what
    they caption in `caption_of`.
  - Checks and review: `text_comparison` (`compared`, `no_text_layer`,
    `garbled_text_layer` or `text_layer_mismatch`), `checks` (each check's
    `name`, `passed`, `failures` and `attempts` for the kept answer), `issues`
    and `verification` (`verdict`, `correction_applied`, `correction_failures`
    and `attempts`, or `null` when no verifier reviewed the page).
  - `inputs` (`context`, `model`, `pdf_sha256`, `prompt_version`, `rendering`,
    `settings`), `fingerprint`, `extracted_at` and `pydelity_version`.
- **Page context.** `page_context` in `extracting/extraction.py` resolves each
  page's writing direction, rotation, repeated lines and their classification,
  labels, languages, instructions, form fields and measured facts from the
  survey. It handles surveys whose ranges overlap, leave gaps or run past the
  PDF: the first range inside the PDF that covers the page applies, else the
  default (rotation 0), and artifact IDs the facts do not hold are ignored.
- **Reuse.** A page file's fingerprint covers only what its requests are made
  from: the PDF, the page, its resolved page context, the resolved model, the
  step's settings that change answers (`check_retries`, `effort`,
  `max_output_tokens`), `PROMPT_VERSION`, the rendering constants and the page
  file's schema version. So a survey change reruns only the pages it touches, a
  wider selection extracts only the new pages, `overwrite` reruns every selected
  page, and no page extraction setting reruns the survey. A verifier switch is
  not an input. While a step's verifier is on, a saved output with no
  verification is redone. Step 3 continues the rule that a changed input reruns
  its own outputs and everything downstream, and nothing else.
- **Reading page files.** `load(output_dir)` returns a `RunResult` whose `pages`
  holds the page files in `pages/` whose `inputs.pdf_sha256` matches
  `pdf_facts.json`, in page order, and none without `pdf_facts.json`. A damaged
  page file raises `OutputError`. In a run, a damaged page file, or one naming a
  missing crop, is extracted again with a `damaged_output` warning, and a
  selected page whose file came from another PDF fails its fingerprint and is
  extracted again. A run leaves unselected page files of another PDF in `pages/`
  (see **Pushed to later steps**).
- **Runner and `run.json`.** `pipeline/runner.py` runs the steps in order and
  writes one `StepRecord` per step: `name`, `status` (`completed`, `reused`,
  `failed`, `stopped` or `skipped`), `started_at`, `ended_at`, `cost_usd`,
  `requests`, `outputs`, `error`, `pdf_transport` and, for page extraction,
  `pages` (`selected`, `extracted`, `reused`). A run's status is `running`,
  `completed`, `paused`, `failed`, `stopped` or `interrupted`. Each warning
  records the step that was running. A run pauses after a step that wrote new
  output in that run, which today means after a new survey. `extract()` and
  `aextract()` run the survey when needed, then page extraction, and write no
  `run.json` or report, as `survey()` does. The CLI summary lists each step's
  status and cost, the page counts, and review issues as
  `<step>, page <number>[, item <id>]: <message>`.
- **Review issues.** One `ReviewIssue` model in `review.py` with `step`
  (`survey` or `extraction`), `check`, `message`, `details`, `page_index` and
  `item_id`. A new step adds its name to `StepName` and its check names to
  `IssueName`. `run.json` `review` lists the survey's issues, then each selected
  page's, and the report groups them by step.
- **Models and providers.** `build_model` builds every model as
  `<provider>:<model-id>` and wraps it in `LedgerModel`. Each step resolves its
  own model: page extraction uses `advanced.extraction.model`, else `model`,
  else `DEFAULT_EXTRACTION_MODEL`; the survey uses `model`, else
  `DEFAULT_SURVEY_MODEL` (both in `providers/profiles.py`). Every agent on
  Anthropic uses PydanticAI's `PromptedOutput` and every agent on OpenAI uses
  `NativeOutput` (`ProviderProfile.output_mode`), one mode per provider for
  every step by the user's choice (see **User decisions that apply to later
  steps**). Each step's model settings sit under `advanced.<step>`:
  `check_retries`, `effort` (mapped to Anthropic's adaptive thinking and
  OpenAI's reasoning effort), `instructions`, `max_output_tokens` and
  `request_timeout_seconds` (900 seconds for the survey, 600 for page
  extraction), plus `model` and `concurrent_pages` (1–32, default 8) for page
  extraction. Anthropic requests cache the instructions, which hold the answer's
  JSON schema under prompted output.
- **Images.** Each page extraction request sends one upright JPEG (quality 90)
  of one page, as large as every supported provider takes without shrinking it
  and at most 300 DPI: 1,688 x 2,184 pixels for a Letter page and 1,624 x 2,296
  for A4 (Anthropic: at most 2,576 pixels and 4,784 tiles of 28 x 28 pixels;
  OpenAI with `detail: "original"`). The model gives boxes on a 0–1000 grid of
  that image, which `grid_box_to_points` in `extracting/rendering.py` maps to
  points (`points_box_to_grid` goes the other way). `PdfWorker.page_image` and
  `PdfWorker.crop` render images and crops; crops are 200 DPI PNGs. The brief's
  option B (seam images of the bottom of one page above the top of the next,
  with item IDs drawn on their boxes) can build on these.
- **Text layer.** `extracting/text_layer.py` reads a page's text-layer lines
  (text only), finds the grid boxes of the page-furniture lines through
  `surveying.probe.line_boxes`, and normalizes text for comparison (NFKC,
  case-folded, letters, marks and numbers only, compared as character trigrams
  that ignore spaces, so scripts written without spaces work the same). A step 3
  check that uses stored text can reuse it, keeping in mind that stored text can
  be wrong.
- **Costs.** `cost.jsonl` lines carry `step`, `page_index` and a required
  `agent` (`surveyor`, `extractor` or `verifier`). Step 3 names its own agents
  the same way. `SpendGuard` holds a reservation for each request in flight, and
  each image counts at its provider profile's per-image token figure.
  `estimate_survey` and `estimate_extraction` in `costs/budget.py` price their
  steps, each with its verifier only when it will run, and the run's estimate
  covers the steps the run will perform. Step 3 adds its own estimate. In the
  user's real runs (2026-11-20, 7 PDFs, 22 pages extracted), page extraction
  cost $5.38 on the Anthropic default (about $0.24 a page) and $9.02 on
  `openai:gpt-6.2-astra` (about $0.41 a page); the surveys cost $0.98 and $2.09.
- **Report.** `report.html` shows each extracted page's image with every item's
  box numbered in reading order and every container drawn, beside the item list
  with figure crops and the verifier's outcome, or "no verifier ran". The
  survey's section shows its verifier's outcome the same way. A review issue
  about an item links to its box.
- **The profile and facts step 3 builds on.** `pdf_survey.json` `profile` holds
  `labels[]`, `languages[]`, `writing_direction`, `rotation[]`,
  `page_numbering[]`, `continuation_notes[]` and `start_markers[]`, the last two
  being the brief's survey-supplied continuation rules for step 3. The profile
  no longer holds instructions; each step's instructions are in its own
  settings. `proposal.artifacts[]` and `proposal.non_artifact_lines[]` say which
  repeated lines are page furniture. These inputs are not guaranteed valid: when
  its check retries run out, the survey keeps the model's last answer, so ranges
  can overlap or run past the PDF and the artifact mapping can miss, repeat or
  invent IDs. `pdf_facts.json` holds per-page text-layer quality (`none`, `good`
  or `garbled`), bookmarks, form fields and their values, a summary of the
  structure tags, repeated lines with IDs and bands, text direction and printed
  page numbers. The structure summary (`StructureFacts`) holds only counts
  (elements, element types, pages with tagged content), whether the PDF is
  tagged and marked, and one quality rating for the whole PDF, not the tags
  themselves. The brief's option A needs step 3 to read the tag tree and link
  its elements to page content; the probe's walk (`_walk_structure` in
  `surveying/probe.py`) is a starting point. Step 2 fixed the rating (indirect
  `/K` arrays, capped walks, tagged pages without text), which tells whether the
  tags can be trusted.
- **Tests.** `tests/fixtures/mock_providers.py` is a stand-in Anthropic and
  OpenAI server reached through the SDKs' base URLs. It routes answers by
  request content, so concurrent requests get the right answer in any order:
  each page request's first text line is `Page index <i> (page <i+1> of <n>)`,
  and a verifier request is told apart by the heading
  `The extraction to review:` in its text. A survey verifier request has
  `The survey answer to review:`. It answers Anthropic as JSON text (prompted
  output) and OpenAI in its native format. Canned answers are in
  `tests/fixtures/survey_answers/` and `tests/fixtures/extraction_answers/`. An
  autouse fixture sets dummy keys and a closed port, so no test reaches a
  provider. Ten public test PDFs are in `tests/fixtures/pdfs/` with their
  sources in `SOURCES.md`, including `irs_w9_instructions_rotated.pdf`, a copy
  of the W-9 instructions with pages 2–4 at rotation attributes 90, 180 and 270.
  Some test PDFs already have content that continues across a page break: in
  `irs_w9_instructions.pdf` a sentence runs from page 2 onto page 3, and CAPS's
  tables continue from page to page. Only `irs_form_1040a_1965_scan` has canned
  answer files today (the extraction tests build their answers in code), so step
  3 needs canned page and break answers for the PDFs it tests. The Japanese
  gazette is one page, so it has no break; step 3's Chinese or Japanese real run
  needs the two-page Chinese Publication 1 or another multi-page PDF.
- **Docs.** `scripts/generate_reference_docs.py` generates the reference pages
  (settings, CLI, Python API, `run.json`, `cost.jsonl`, the page file, the
  extraction checks) from the code, and CI fails when they are stale or a new
  page is left untracked. Each step adds its own guide (page extraction's is
  `guides/page-extraction.md`) and reference pages.

## Reuse from KGForEdGlobal so far

Paths are under `backend/src/kgfeg/`. The survey ported only infrastructure:

- `utils/pdf.py` `compute_doc_key` became pydelity's PDF SHA-256 helper.
- `model_registry.py` became the model factory and provider profiles, without
  its hand-kept list of models.
- `page_ir_extraction/agents.py` gave the agent pattern: an output validator
  that raises `ModelRetry` with the Python checks' messages.
- `AgentUsageBucket` and `write_to_json` were replaced by the cost ledger and
  atomic writes rather than ported.

Page extraction ported from `page_ir_extraction/` (its design's decision 16),
rewritten for neutrality and for PydanticAI 2.x and PyMuPDF 2.x: the extraction
and validation prompts' generic sections, the validator's audit stance,
checklist, severity guide and full-answer correction, the duplicate-box check,
the table occupancy simulation, the "table has some text" check, and prompted
output on Anthropic. It did not port text-layer hints, left-to-right rules,
English word lists, full-page-figure checks, the letter-run tokenizer, boundary
and continuity marks, `text_en`, `figure_kind`, `local_code`, the footnote
position check, the table-collapse heuristics, `find_tables` hints, fixed DPI,
file-existence resume or non-atomic writes.

Step 3's source is `page_ir_verification/` and
`entries/verify_page_ir_continuity.py`; the brief's step 3 section and evidence
E1–E10 describe it and its costs. Assembly's source is `document_ir/` (such as
`stitch_segments.py`) and `entries/stitch_document_ir.py`. KGForEdGlobal's code
targets pydantic-ai 1.63.0 and PyMuPDF 1.26.7, so ported code needs updating for
PydanticAI 2.69 or later (output retries, for example, are
`Agent(retries={"output": n})`) and PyMuPDF 2.1 or later. Keep PyMuPDF 2.x: the
user chose it for fixes that include `get_pixmap` hangs (#5082, and #5125 on
heavily tagged pages).

## Pipeline outcomes for steps 3–6

Scoped before the pipeline was split into one cycle per step. The old AC numbers
in parentheses are retired. Page extraction (step 2, was AC-005 to AC-007) is
built in 0.2.0.

- Page-break verification (step 3), was AC-009: each break gets a verdict on
  whether content continues, which items connect, the join rule for their kind
  (text: space, no space or dehyphenate; code: newline, no dehyphenation; list:
  continue item or new item; table: append rows or merge a split row), how many
  repeated header rows to drop, and which repeated items above the continued
  unit to drop. The verdict also names any continuation marker on the continued
  unit, such as a row label or heading that says it continues ("(contd)",
  "continued"; the brief's E9), which assembly folds into the original label.
  Code cannot find these markers itself, since no language-specific word lists
  or patterns are allowed. Since page extraction's containers carry no open-top
  or open-bottom hints (the brief planned them; the user removed them), the
  verdict must also say which containers continue across the break, even when
  the content inside starts a new unit, such as a new heading at the top of a
  box that runs across both pages. Assembly builds one container per cross-page
  box from these verdicts (step 2's scope: "Step 3 decides continuity, and
  assembly joins a box that crosses pages into one container").
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
  BCP-47 `language` that the KG stage reads; page items with text already carry
  one. KGForEdGlobal's KG stage loads `stitching/document_ir.json` with
  `DocumentIR.model_validate`, not a `document.json`, and its schema models
  forbid undeclared keys (`extra="forbid"`), so even a top-level
  `schema_version` fails validation. The brief's field-use counts come from
  substring matches; whole-word counts are lower for `segment_id` (38, not 223),
  `section_path` (23, not 72), `grid_sources` (46, not 53) and
  `columns_signature` (19, not 31). Reading pydelity's `document.json` therefore
  needs KGForEdGlobal-side changes, which stay out of pydelity's cycles.
- User sign-off of each step's output, was AC-004, AC-008, AC-010, AC-015,
  AC-017 and AC-020.

The cross-cutting outcomes scoped with them (configuration, CLI and library use,
cost and spend controls, resume, providers and tests, the review list and HTML
report, no document-type assumptions, user docs) are built for the survey and
page extraction. Each later step extends them to its own outputs.

## Open for step 3's Scoper and Architect

- Which of the brief's options A–D step 3 uses, alone or combined, and whether a
  validator reviews every break, some breaks (option D) or none.
- Which breaks a run checks when `pages` selects only some pages, for example
  only breaks between two selected pages that follow each other.
- Step 3's other settings and its output files (the brief proposes
  `page_breaks/NNNN-NNNN.json`), and how its fingerprint covers the two page
  files each break reads. Already settled by the user: the default run includes
  step 3 (answer 1), with a pause after page extraction under the `pause`
  setting, and step 3 defaults to `anthropic:claude-opus-5-5` at effort `high`
  with its own `advanced.<step>.model` and `advanced.<step>.instructions` (see
  **Pushed to later steps**).
- How step 3 treats page files that come from another PDF or an older survey
  (see **Pushed to later steps**).
- How text joins inside a list entry that continues across the break, and inside
  each cell of a table row split across it (space, no space or dehyphenate). The
  brief's join rules cover this only for text items, its known defects include
  today's join that always inserts a space and knows only Latin sentence ends,
  and code cannot choose without language rules, so the verdict likely has to
  give it.
- Which release the cycle ships, such as 0.3.0.

## Constraints, non-goals and assumptions still in force

- Constraints: Python 3.13 and 3.14, with Pydantic, pydantic-settings,
  PydanticAI, loguru, Typer and PyMuPDF 2.x. Models are reached through provider
  APIs via PydanticAI, and both Anthropic and OpenAI must work. The PDF path is
  the only required input, configuration is one optional JSON or YAML file with
  an `advanced:` section, a PDF path given on the CLI is used over the config
  file's, and a normal run resumes. The domain schema is JSON Schema data with
  `x-key` and `x-verbatim`, never Python source. Consumer-specific needs go in
  `document.json` fields or the consumer's adapter. The brief's design
  directions are input for Architect, and evidence E1–E23 illustrates rather
  than specifies. Automated tests mock every model call and make no network
  calls to model providers.
- The repo setup stays as it is unless a cycle needs a change: just, prek,
  Dependabot, zizmor, the Markdown rules, exact pins for dev tools and minimum
  versions for runtime dependencies. "Lint and test" and "TruffleHog secret
  scan" stay required checks on `main`.
- Non-goals: any change to KGForEdGlobal; KG, Learning Component and Learning
  Progression logic; generating KG config from a pydelity schema; automatic
  splitting or a chunked survey for PDFs a provider rejects as too large;
  per-model PDF limits; continuity judged inside step 2; a measured comparison
  of step 3 designs; a default spending limit; a hosted service, web UI beyond
  the HTML report, telemetry and other Level 4 features.
- Assumptions: Level 3 (internally testable) maturity. Test PDFs are public
  documents chosen with the user's approval. A user-supplied domain schema does
  not seed page-profile labels, so changing it reruns only steps 5–6. Real model
  runs use the user's own API keys.

## Risks and follow-up

From the survey's and page extraction's designs and reviews, still open:

- Prices and model IDs drift. Prices follow `genai-prices` releases, and
  `advanced.models` covers a model it does not know yet. Older models that
  reject adaptive thinking, `effort` or `reasoning_effort` fail with the
  provider's error. Image limits are the providers' documentation as of November
  2026; an OpenAI model that does not accept `detail: "original"` fails with the
  provider's error.
- A request that times out or is canceled on pydelity's side may still finish,
  and be billed, at the provider, with no ledger line. Each timed-out retry can
  add such unseen cost, and concurrent requests multiply it. When one page
  fails, page extraction cancels the pages in flight.
- Eight concurrent page requests can hit low provider rate limits. The SDKs
  retry 429 responses up to `provider_retries`, after which the run stops;
  lowering `concurrent_pages` is the remedy.
- Non-streaming requests with a large `max_output_tokens` need an explicit
  request timeout. `LedgerModel` wraps streamed requests too, but no test covers
  that path, so a step that streams should add one.
- PyMuPDF holds the GIL while it reads a page. Page extraction serializes its
  PyMuPDF calls on one worker thread per run. Two runs in one process each have
  their own worker, and the report and the probe use `asyncio.to_thread`, so
  PyMuPDF can run on two threads at once, which `rendering.py`'s docstring calls
  unsafe (not seen to fail; 30 gathered runs gave identical results).
- The cost estimate is a heuristic: maximums assume every retry with the longest
  answer, and the plan-time check now uses the expected cost, so the question
  can come mid-run. Prompt text is counted at 4 characters a token, which
  undercounts non-Latin text, and a request's bound prices input at the plain
  input rate while Anthropic bills cache writes at 1.25 times.
- Prompted output on Anthropic has no grammar behind it, so an answer that is
  not valid JSON costs a retry and, on the last allowed attempt, fails the page
  or the survey and stops the run.
- Effort `high` costs more thinking tokens. A dense page can exceed 32,000
  output tokens; the run then stops with `ExtractionError` naming the setting.
- Uploaded PDFs stay in the user's provider storage until they expire (90 days
  on Anthropic by default) and count against the organization's storage.
- The IANA registry inside `langcodes` is fixed per release, and a release that
  changes a tag's standard form changes fingerprints, so outputs that use the
  tag run again.
- Probe mistakes reach the review list as `page_number_differs` issues, for
  example numbers in table cells, or page labels on pages that print no number.
  Keeping page labels as a fact separate from the printed text would cut that
  noise; it changes the facts schema.
- The model can be wrong where the facts were right, and the review list is the
  only signal. A verifier that wrongly passes a page, or whose correction drops
  or adds a line, keeps that line off the review list; the failure stays in the
  page file's `checks`. A survey verifier that wrongly passes the survey keeps
  its differences from the facts off the list, visible only by comparing the
  profile with the facts in `pdf_survey.json`.
- With the verifiers off, which is the default, pages whose stored text is
  wrong, such as the Arabic and Japanese test pages, put their text differences
  on the review list, and nothing beyond the code checks catches missed or
  merged items, a wrong reading order or boxes on the wrong content.
- A verified survey sends the PDF twice, so it costs about twice as much. The
  estimate's typical survey verdict (6,000 output tokens) is a guess that real
  runs have not measured yet. A survey verifier request that fails after a paid
  survey answer makes the next run pay for the survey request again.
- `SurveyVerdict` nests a whole `SurveyAnswer`. Neither OpenAI's native output
  nor Anthropic's prompted output had run it at the end of the verifier cycle's
  build; its real runs check it.
- Every repeated line (up to 1,000) goes with the survey request and must be
  accounted for.
- Claude Opus 5.5 can stop with `refusal`, which is reported as a failure.
  Server-side refusal fallbacks are off because they change the billed model in
  the middle of a request.
- The survey's region boxes are the model's estimates and are often off. Page
  boxes rest on the extraction and verifier models; snapping either to measured
  content is open (see **Pushed to later steps**).
- The `artifacts` check trusts the model's boxes: furniture inside a loose
  `artifact` box passes, and since one occurrence is enough, a page that marks a
  body occurrence as an artifact and misses the real header or footer passes.
- The text comparison can flag text read from raster images (slides with
  pictured text), costing retries. Text layers that store right-to-left text in
  visual order, or legacy encodings rated `good`, can mislead it.
- One run per output folder at a time. Concurrent runs in the same folder are
  unsupported and not detected.
- Output folders from earlier builds do not carry over. A `pdf_survey.json`
  without `verification` is surveyed again, and a `cost.jsonl` with survey lines
  whose `agent` is `null` (0.1.x and page extraction's build) stops every run on
  the folder with `OutputError`. Use a new folder.
- On Windows, `os.replace` fails while another program holds the target open,
  and the error names the file.
- Large PDFs make large reports, which is acceptable at Level 3.
- `docs/pnpm-lock.yaml` may approach the 500 KB limit of the large-file hook. If
  it goes over, exclude that one path with a comment.

## Review findings and observations left for later

The verifier cycle fixed the defects page extraction's implementation review
withdrew as not material (inline form widgets, outline links to missing objects,
report tables with spanning header cells, `load()` with another PDF's page
files), the `TEXT_FLAGS` comment and the docs wording its final review found.
Still open, from page extraction's implementation review:

- An interrupted `overwrite` run can leave an old page file naming a crop that
  the new answer overwrote, since crops are named by item position and written
  before the page file.
- Temporary files left in `pages/` or `figures/` are removed only when a page is
  extracted, and the provider image limits that size the page image are not in
  the page fingerprint.
- A structure walk cut short at its cap rates pages up to the last page it
  reached, so in a tree out of page order an unreached page can count as
  untagged (more than 20,000 elements needed).
- The page JPEG has no byte cap. Synthetic grain measured 3.7–6.1 MB for a
  Letter page, against what the review took to be Anthropic's per-image limit,
  about 5 MB (not checked against its current documentation); the test PDFs peak
  at 1.04 MB.
- Figure crops render at a fixed 200 DPI with no pixel cap, so a full-page
  figure on a 36 x 48 in page takes about 0.8 GB while it renders.
- Page extraction's design says crops are clipped in unrotated coordinates,
  where the code clips in displayed-page coordinates. The design is a signed-off
  cycle's record, so the wording stays as it is.

From the user's real runs (2026-11-20), accepted for 0.2.0:

- On both providers, reading order was right on the Arabic, Chinese and Japanese
  pages, CAPS's sideways tables were read upright, and the W-9's fillable fields
  matched the form. A few boxes sat off their text, and the two providers boxed
  form fields differently (see **Pushed to later steps**).
- The providers structure some pages differently: OpenAI put the ten rights on a
  Chinese page in one list item with 10 entries where Anthropic gave 20 heading
  and body items, and OpenAI marked more containers. Both fit the item rules, so
  later steps must not assume one provider's structure.
- In the Anthropic run of the Japanese gazette, the one-page survey made no
  label for page furniture, so its furniture items (7 text items and the
  masthead figure) got the label `other`, with two `no_matching_label` issues.
  On both providers, a field item made from a zero-size `Signature1` widget at
  the page corner got one too.
- Not exercised by real runs, with mocked-test evidence only: a filled or
  handwritten form value, and a page that is one picture.
- Not recorded as exercised in either cycle: Ctrl+C at a CLI question on
  Windows.

## Loose ends

- Merge `tz6/pipeline-step-2` only after the verifier cycle is signed off.
  Before merging: commit every STANDARDS change, sign-off included, so both
  cycles' records are in the parent of the uninstall commit; then run STANDARDS
  Project Uninstallation on the branch, since `main` has no STANDARDS
  installation, and give pull request 10 a non-breaking `feat:` title covering
  both cycles' work, because its squash-merge title becomes the commit that
  release-please reads (the draft's title is `Tz6/pipeline step 2`).
- After merging, check that release-please opens the 0.2.0 release pull request
  (tag `v0.2.0`) from the `0.1.1` manifest, and that merging it publishes 0.2.0
  to PyPI and the docs site.
- Node `24.22.3` is kept by hand in three places: two hooks in
  `.pre-commit-config.yaml` and `docs.yml`. `docs/package.json`'s `engines.node`
  (`>=22.23.4`) follows the locked Astro's own minimum.
- Repo-setup risks still open: Dependabot's uv can lag behind the uv people use,
  and updates fail if it falls below `required-version`. Dependabot ignores
  setuptools, whose `[build-system]` minimum is kept by hand. Hand-kept pins
  (the uv bound, CI's uv, Node, Prettier) go stale unless someone bumps them,
  and a Prettier bump can reformat many files. zizmor's online audits can fail
  CI when an advisory is published for an action the repo uses. prek is pre-1.0.
  While STANDARDS is installed, Markdown formatting fixes whitespace in its
  files and leaves any other change alone. PyPI versions are permanent.

## Pushed to later steps

Work moved out of a step, naming the step that picks it up. Add to this list
whenever work is moved out of the current step.

- **Translation (after assembly, step 4 or later).** Revisit an optional step
  that translates extracted text into a target language the user sets. pydelity
  serves any PDF and any downstream use, so translation is worth having even
  though KGForEdGlobal does not translate. A run for KGForEdGlobal leaves it
  off. Page extraction transcribes text as printed and translates nothing.
  Translating after assembly means text continued across a page break is
  translated as one unit.
- **Page continuity (step 3).** Page extraction records no continuity. Items
  carry no continuation marks, and containers carry no open-top or open-bottom
  hints, which the brief's container proposal had. Step 3 decides whether
  content continues across each page break.
- **Boxes that cross pages (step 4).** Page extraction records a bordered or
  shaded box as a container on each page it appears on, with an ID and a
  bounding box, and the items inside name their container. Assembly joins the
  pieces of a box that crosses pages into one container, using step 3's
  verdicts.
- **Pauses between steps (each later step).** By default, a run stops after a
  step that wrote new output, so the user can check it before paying for the
  next step, and the next run continues. One setting, `pause` in the config file
  and Python and `--no-pause`/`-np` on the CLI, turns every pause off. Page
  extraction added the pause after the survey. Each later step adds its own
  pause under the same setting.
- **Model per step (each later step).** The global `model` setting chooses the
  model for every step. Page extraction added `advanced.extraction.model`, and
  each later step gets its own optional override the same way. With neither set,
  every step defaults to `anthropic:claude-opus-5-5` at effort `high`, as the
  survey and page extraction do (the user's decision, 2026-11-19, confirmed on
  2026-11-20 for every later step, step 3 included). Each step keeps its own
  default constant in `providers/profiles.py`, so one can change alone.
- **Verifier per step (each later step).** Every step's verifier is opt-in and
  off by default. The global `verify` setting (`--verify`/`-vf` on the CLI,
  `verify=True` in Python) turns on every step's verifier, and each step has an
  optional override of its own, `advanced.<step>.verify` (`true`, `false`, or
  `null` to follow `verify`), set in the config file or from Python, with no CLI
  option. The survey and page extraction have theirs. Each later step adds its
  own override, a resolved `Config.verify_<step>` property, a verifier that is a
  second request to its own model with its own instructions,
  `verification: null` in its outputs when no verifier ran, every difference on
  the review list when none ran, an estimate that prices the verifier only when
  it will run, and the reuse rule that redoes outputs no verifier reviewed while
  the verifier is on. A step's verifier runs on all of that step's work or on
  none of it.
- **Instructions per step (each later step).** Instructions live under each
  step's `advanced:` section (`advanced.survey.instructions`,
  `advanced.extraction.instructions`) and go only to that step's models. They
  are set in the config file or from Python, with no CLI option, because each
  step's instructions are specific to that step. The top-level `instructions`
  setting and `--instructions`/`-i` are gone. Each later step gets its own
  optional `advanced.<step>.instructions` the same way.
- **Raising internal versions again (not yet decided).** No cycle so far raised
  `PROBE_VERSION`, a `PROMPT_VERSION` or an output `schema_version`, because no
  one uses pydelity yet. When to go back to raising them for changed outputs is
  still open, and so is when pydelity starts keeping backwards compatibility
  (aliases, deprecation warnings, migrations or defaults kept for old files),
  likely once it has public users.
- **Page files of another PDF in a reused folder (step 3).** When a different
  PDF runs into a folder another PDF used and does not extract every page the
  first PDF had (it is shorter, or its page selection is narrower), the first
  PDF's other page files stay in `pages/`. The run warns that the folder holds
  another PDF's results, `run.json` and the report list only this run's pages,
  and `load()` leaves out page files whose `inputs.pdf_sha256` differs from
  `pdf_facts.json`'s. Step 3, the first step that reads page files, should skip
  them the same way. Page extraction keeps old page files on purpose, for
  narrowed page selections. A page file kept that way can come from an older
  survey or other settings, and step 3 should decide whether to use it.
- **Snapping boxes to measured text (page extraction, not yet scheduled).** Box
  accuracy rests on the extraction and verifier models. In the Anthropic real
  runs a few boxes sat off their text, such as a Chinese footer's box about 7 pt
  below its line and the box of a vertical Japanese line about 9 pt to the left
  of its text. Moving a box onto the text layer's words for the item could
  tighten them on pages with a good text layer.
- **Judging each page's stored text (page extraction, not yet scheduled).** The
  text comparison already skips a page with no text layer, one whose text layer
  the probe measures as garbled, and one where fewer than half of the answer's
  three-character runs are in the text layer. Pages whose stored text is wrong
  in part, such as broken Arabic letter forms or private-use characters, still
  spend their check retries on text differences that the model is right to keep.
  Comparing the stored text with the model's reading first, and skipping the
  comparison when the stored text is wrong, would save those retries.
- **Two box rules for the page prompt (page extraction, not yet scheduled).**
  The prompt has no rule for a paragraph that continues at the top of the next
  column. On a Chinese page in the Anthropic run, two items' text held the
  continuation while their boxes covered only the first column's part. The
  prompt also does not say whether a field's box includes its printed label. On
  the W-9, OpenAI's field boxes covered only the input area or checkbox, while
  Anthropic's took in the label. The user accepted both for 0.2.0. Changing the
  prompt raises the question of page extraction's `PROMPT_VERSION` (now 1) in
  the entry above.

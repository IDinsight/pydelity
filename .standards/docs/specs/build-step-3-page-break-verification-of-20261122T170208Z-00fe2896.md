<!-- STANDARDS
Artifact: ARCHITECTURE
Cycle: build-step-3-page-break-verification-of-20261122T170208Z-00fe2896
-->

# Technical Design: page-break verification and release 0.3.0

## Context

- Scope:
  `.standards/docs/scope/build-step-3-page-break-verification-of-20261122T170208Z-00fe2896.md`
  (`AC-001` to `AC-051`). Target maturity is Level 3. Architect mode: feature.
  The new step is a bounded capability that follows the shape the survey and
  page extraction already set (settings, checks and hints, opt-in verifier,
  reuse, estimate, review list, report). Nothing here is a transition or a new
  cross-cutting rule.
- Baseline: 0.2.0 as merged (`.standards/CONTEXT.md`). The designs of the survey
  (`git show 83743ef:...`), page extraction and the verifier cycle (both
  `git show af1b2d1:.standards/docs/specs/<id>.md`) stay in force. This design
  adds a step and changes the run flow, the estimate placement, `run.json` and
  the report. It replaces none of their decisions.
- Nearest analogue for everything new: page extraction.
  `extracting/extraction.py` (`plan_pages`, `_reusable_page`, `_saved_page`,
  `extract_pages`, `_extract_page`, `_kept_answer`, `_page_issues`),
  `extracting/llm.py` (`StepModel`, `_content`, `_model_settings`, `_run`),
  `extracting/agents.py` (both agents' output validators),
  `extracting/validators.py` (`CHECKS`, `HINTS`, `run_checks`,
  `compare_with_hints`, `retry_message`) and the runner's `_extraction`.
- Inputs the step reads: every page's page file (`PageFile`), and from
  `pdf_survey.json` only `profile.continuation_notes` and
  `profile.start_markers`. Page files can break their own rules and the profile
  can be inconsistent (`CONTEXT.md` **Relevant Existing Behavior**). This design
  reads no profile range, so overlapping or out-of-range ranges never reach the
  step. Each page's rotation and writing direction come from its page file.
- Port source: KGForEdGlobal `page_ir_verification/` (read-only). This design
  ports its table decision procedure (column structure, a new table announced
  outside the grid, a header that redefines the columns), its rule that a border
  or closed box around each page's part is no sign of a new table, and its rule
  that the item data helps locate items while the images decide. It ports none
  of its candidate-pair search, confidence thresholds, per-pair validator,
  page-number regexes, top-to-bottom candidate order, English or curriculum
  prompt text, boolean header flag, file-existence resume or non-atomic writes.
- Constraints that shape this design (scope **Constraints**): the model's own
  reading decides; code's measurements and the survey's findings are hints that
  never send an answer back; checks may send it back within the step's check
  retries; a run stops only on an unusable answer or a provider error after
  retries; an opt-in verifier reviews every break or none; one structured-output
  mode per provider; document-type, language and direction agnostic; PyMuPDF on
  one worker thread; no per-model limits; no default `max_cost`; async twins; no
  backwards compatibility; existing `schema_version`s, `PROBE_VERSION` and
  `PROMPT_VERSION`s stay; the step's own versions start at 1 and `"1.0"`.
- Names are proposals for the user to approve in the development plan before the
  build step that creates them: the step name `page_breaks`, the settings
  section `advanced.page_breaks` and its keys, the folder `page_breaks/` and its
  file names, the agent `judge`, the Python functions `verify_breaks` and
  `averify_breaks`, the module `verifying/verification.py`, the warning code
  `missing_page_files`, and the new `run.json`, estimate and verdict-file field
  names, check and hint names listed under **Interfaces and Contracts**.
- No project references exist under `.standards/project-references/`.

## Decision

1. **One request per break, showing both whole pages.** The step's model judges
   each break between page N and page N+1 in a request of its own. The request
   carries both pages whole: their upright images and their items as page
   extraction recorded them. Whole pages are needed because the end of a page in
   reading order can sit anywhere on it (the bottom of the left column of a
   right-to-left page, the last column of vertical text), and because a repeated
   header or title on page N+1 is compared with what page N printed at the top
   of the same unit. One break per request keeps each verdict made from exactly
   two page files, so re-extracting one page re-judges only its two breaks
   (`AC-035`), and keeps every request small enough for any provider. Requests
   run several at a time (decision 11).
2. **The request shows pages, items and hints, and nothing from other steps.**
   Content, in order: a text part about page N, page N's upright image, a text
   part about page N+1, page N+1's upright image, and a cache point, so check
   retries read all of it from the provider's cache. Each page text gives the
   page's index and number, the turn applied to its image as a plain statement,
   the writing direction as what the survey found, its `column_order`, and its
   containers and items in reading order with their IDs, kinds, roles, labels,
   container and caption refs, boxes on the 0–1000 grid of the upright image
   (`points_box_to_grid` with the page file's `rotation`), and their content
   (text, list entries with IDs and markers, table rows with each row and cell
   numbered, figure description and text, field content, LaTeX). Images are
   rendered by `PdfWorker.page_image` with the page file's `rotation` and
   `RENDERING_SETTINGS`, as page extraction renders them, so every image reads
   upright (`AC-020`). The instructions hold the rules, then the survey's
   continuation notes and start markers under a heading that calls them hints
   the pages override, then `advanced.page_breaks.instructions` last when set.
   The instructions are the same for every break of a run, so Anthropic caches
   them (`anthropic_cache_instructions`) and OpenAI caches the prefix itself. No
   request carries the PDF, the text layer, a page file's `inputs`, `checks`,
   `hints` or `issues`, or another step's instructions (`AC-009`).
3. **The verdict names continuing pieces by item ID, each with a join rule.**
   The answer (`BreakVerdict`) says whether content continues, lists each
   continuing piece, lists the continuing containers and gives a short reason. A
   piece names the item where it ends on page N and where it starts on page N+1,
   with the list entry's ID when an end or start is a list entry, and carries
   its join rule, the text join where text continues, the repeated header rows
   for a table, the repeated items above it on page N+1 to drop, and its
   continuation markers. Several pieces may continue at one break (body text and
   a footnote). Containers continue apart from pieces, also when the content
   inside starts a new unit. **Verdict contract** has every field.
4. **Join rules follow the kinds, and only text, code, list and table items
   continue.** `continue_text` joins a text item to a text item, or a code item
   to a code item, with a text join of `space`, `no_space` or `dehyphenate` for
   text and `newline` for code. `continue_entry` joins text where at least one
   end is a list entry and the other is a list entry or a text item: the last
   entry of the list on page N, the first entry of the list on page N+1. It
   covers a list whose last entry continues, including when page extraction made
   the continued text a text item. `new_entry` continues a list with a new
   entry. `append_rows` continues a table with new rows. `merge_split_row`
   merges the row cut by the break with the first row on page N+1 after any
   repeated header rows, and gives one text join per cell of that row, `null`
   where one side of the cell has no text to join. Figures, fields and formulas
   never continue: assembly has nothing to join for them, and a figure printed
   across two pages stays two images. The text join is the verdict's because
   code cannot choose it without language rules (`AC-014`).
5. **Checks are what code can decide about the verdict, and the only hint is the
   survey's start markers.** Checks test the verdict against itself, the two
   page files and its hard limits; a failure may send it back within
   `advanced.page_breaks.check_retries`, and a last verdict still failing one is
   kept and listed while the run goes on (`AC-023`). Checks, in order: `ids`,
   `continues`, `duplicates`, `joins`, `furniture`, `header_rows`, `repeats`,
   `markers` (**Checks and hints**). `header_rows` compares the rows a verdict
   counts as repeated with the earlier table's leading rows, and `repeats`
   compares each repeated item with text printed on page N, both by tolerant
   text similarity in any script. They are checks, not hints, because assembly
   drops the rows and items they name, so a wrong count or a wrong item loses
   content; a model that keeps its answer after the retries is kept and listed
   (`AC-024`). The one hint, `start_markers`, flags a piece whose start on page
   N+1 begins with one of the survey's start markers (`AC-025`). Hints follow
   the verifier cycle's decision 14: never sent back, never fail anything,
   listed unless the step's verifier passed the verdict or its correction was
   kept, and always kept in the verdict file's `hints` (`AC-026`). The survey's
   continuation notes are free text, so code compares nothing with them; they
   reach only the model.
6. **A break where a page has no content items gets a verdict without a
   request.** When either page has no item whose role is not `artifact` (a blank
   page, or one holding only page furniture), nothing can continue, since only
   consecutive pages are judged. The step writes a verdict saying nothing
   continues, with `judgment: "no_content"`, all checks passed with 0 attempts,
   no hints, no issues and `verification: null`, and makes no request, with or
   without the verifier. Every other verdict has `judgment: "model"`.
7. **The verifier mirrors page extraction's.** With `verify_page_breaks` on,
   after the judge's verdict is accepted, a second request to the same model
   with the same pages and items, the verdict as JSON, its failing checks and
   its hint differences returns a `BreakVerifierVerdict`: passed, or problems
   plus an optional full corrected verdict. Its output validator runs the checks
   on the correction and sends it back while retries remain. A correction is
   kept when it passes every check, whatever its hint differences. Passed: keep
   the verdict. Correction kept: keep it, and the problems stay in the
   verifier's verdict only. Otherwise: keep the judge's verdict and list each
   problem (`AC-029`). Its instructions are the step's rules and hints and
   `advanced.page_breaks.instructions` only, and the effort, output tokens,
   timeout and check retries are the step's.
8. **The step runs only when every page has a current page file.** A page file
   is current when page extraction made it in this run, or when page extraction
   would reuse it now without a model call: `plan_pages` over every page of the
   PDF with `quiet=True` gives it `saved` (valid, fingerprint matching this PDF,
   survey, settings and model, `overwrite` off, verified when page extraction's
   verifier is on). That rule leaves out another PDF's page files and files made
   from an older survey, other settings or another model (`AC-002`). When a page
   lacks a current page file, as a narrowed `pages` can leave, the run extracts
   the selected pages, makes no page-break request, records the step as
   `skipped` with a `missing_page_files` warning naming those pages and how to
   get verdicts, and ends `completed` (`AC-003`). With `overwrite` on, only
   pages extracted in this run are current, so a narrowed `pages` with
   `overwrite` never judges breaks. A one-page PDF records the step as `skipped`
   with an info line and no request (`AC-004`).
9. **A verdict's fingerprint covers the bytes of its two page files.** Its
   inputs (`BreakInputs`) are the PDF's SHA-256, each page's index and the
   SHA-256 of its page file's bytes on disk, the survey's continuation notes and
   start markers, the page count, `advanced.page_breaks.instructions`, the
   model, the step's settings that shape an answer (`check_retries`, `effort`,
   `max_output_tokens`), the step's `PROMPT_VERSION` and `RENDERING_SETTINGS`;
   the fingerprint adds the verdict file's schema version. A page extracted
   again has a new `extracted_at`, so its bytes change and both its breaks are
   judged again, even when its page fingerprint is unchanged. A verdict file is
   reused when it is valid, its fingerprint matches, `overwrite` is off, and it
   is a `no_content` verdict, holds a verification, or the step's verifier is
   off (`AC-035`, `AC-036`). No verifier switch is in the fingerprint, as for
   the other steps. A damaged file gives the `damaged_output` warning and the
   break is judged again (`AC-037`). Settings of page-break verification are in
   no survey or page fingerprint, so changing them reruns neither.
10. **The run goes survey, page extraction, page-break verification, with a
    pause after each step that wrote new output.** After page extraction, the
    run decides in this order: a one-page PDF skips the step; a page without a
    current page file skips it with the warning (decision 8); a page extraction
    that wrote at least one page file, with `pause` on, records the step
    `skipped` and ends `paused` (`AC-005`); otherwise the step runs. Every step
    the run did not reach is recorded `skipped`, after a survey pause too. The
    estimate, the spending question, the `max_cost` check on it and the API-key
    checks happen once per run, before its first request: in the survey step
    when the survey runs, else in page extraction when it has pages to extract,
    else in page-break verification when it has breaks to judge (`AC-033`). The
    estimate covers every step the run will reach and leaves out a step the run
    will not reach (**Cost estimate**). `extract()` stops after page extraction;
    `verify_breaks()` runs through page-break verification and never pauses
    (`AC-006`).
11. **Settings mirror page extraction's.** `advanced.page_breaks` holds
    `check_retries` (0–5, 2), `concurrent_breaks` (1–32, 8), `effort` (`high`),
    `instructions` (none), `max_output_tokens` (32,000), `model` (none),
    `request_timeout_seconds` (600) and `verify` (`null`). `Config` gains
    `page_breaks_model` (`advanced.page_breaks.model`, else `model`, else
    `DEFAULT_PAGE_BREAKS_MODEL`, `anthropic:claude-opus-5-5`) and
    `verify_page_breaks` (`advanced.page_breaks.verify`, else `verify`). No CLI
    option is added; `--model` and `--verify` reach the step through the global
    settings (`AC-008`, `AC-009`, `AC-028`).
12. **Outputs.** One verdict file per break, `page_breaks/<NNNN>-<NNNN>.json`
    (the two page indexes, four or more digits each), written atomically
    (`BreakFile`). In `run.json`, the step is named `page_breaks`, its record
    gains `breaks` (`total`, `judged`, `reused`), its `outputs` are
    `page_breaks/`, and its review issues follow the pages'. A review issue and
    a ledger line about a break carry the break's earlier page in `page_index`;
    breaks are only ever between page N and N+1, so the earlier page names the
    break, and the message names both pages (`AC-031`, `AC-032`). `RunResult`
    gains `breaks`, the verdicts in break order. `load()` returns only verdicts
    whose PDF hash matches `pdf_facts.json` and whose two page-file hashes match
    the page files it returns (`AC-007`).
13. **A failed request stops the run, and verdicts already written stay.** A
    provider error after the provider retries, a timeout, a refusal, used-up
    output tokens or no verdict matching the format, from the judge or the
    verifier, raises `ProviderError` or a new `PageBreakError` naming the break
    and the agent. The other breaks' tasks are canceled, the step ends `failed`,
    the run ends `failed`, the CLI shows the error and exits `FAILED` (1), and
    Python raises it. Verdict files already written are valid, and the next run
    judges only the breaks without a reusable verdict (`AC-038`).
14. **The report shows each break beside its two pages.** A new section, after
    the pages, has one card per verdict: both page images (the report's existing
    `report/pages/<NNNN>.jpg`, no new image files) with the items and containers
    the verdict names drawn on them, and beside them whether content continues,
    each piece with its join rule, text join or cell joins, repeated header
    rows, repeated items and markers, the continuing containers, the reason, the
    verifier's outcome or that no verifier ran (or that no request was made, for
    a `no_content` verdict), and the break's review issues. Each review issue
    about a break links to its card (`AC-039`).
15. **The step's code lives in `src/pydelity/verifying/`.** `schemas.py`,
    `prompts.py`, `validators.py`, `agents.py`, `llm.py` and the step module
    `verification.py`, split as page extraction splits its own. `verifying`
    imports `extracting` (page file schemas, `plan_pages`, `PdfWorker`, the grid
    mapping, `comparison_form` and `trigrams`), `surveying.schemas`, `review`,
    `costs`, `providers` and `utils`; nothing imports `verifying` except
    `pipeline`, `api`, `report` and `costs` where they need its types or sizes.
    `extracting` and `surveying` never import it.
16. **One Python function runs the step on its own.** `verify_breaks()` and
    `averify_breaks()` take what `extract()` takes, run the survey and page
    extraction of the selected pages when their outputs are missing or out of
    date, then page-break verification under decision 8, never pause, write no
    `run.json` and no report, and return the verdicts in break order: every
    break's, or none when the PDF has one page or a page lacks a current page
    file (with the warning).

### Defaults

| Setting                                        | Default | Range                    |
| ---------------------------------------------- | ------- | ------------------------ |
| `advanced.page_breaks.check_retries`           | `2`     | 0–5                      |
| `advanced.page_breaks.concurrent_breaks`       | `8`     | 1–32                     |
| `advanced.page_breaks.effort`                  | `high`  | `low`, `medium`, `high`  |
| `advanced.page_breaks.instructions`            | `null`  | text; blank is unset     |
| `advanced.page_breaks.max_output_tokens`       | `32000` | > 0                      |
| `advanced.page_breaks.model`                   | `null`  | `<provider>:<model-id>`  |
| `advanced.page_breaks.request_timeout_seconds` | `600`   | > 0                      |
| `advanced.page_breaks.verify`                  | `null`  | bool, or `null` (follow) |

## Acceptance Coverage

- `AC-001`: decision 10; **Run flow**. The CLI and `run()` both go through
  `run_pipeline`.
- `AC-002`: decision 8; **Current page files**.
- `AC-003`: decisions 8 and 10; **Run flow**, **Warnings**.
- `AC-004`: decisions 8 and 10.
- `AC-005`: decision 10; **Run flow**, **Summary and log lines**.
- `AC-006`: decision 16; **Python API**.
- `AC-007`: decision 12; **`load()`**.
- `AC-008`: decision 11; **Settings**.
- `AC-009`: decisions 2 and 11; **Judge request**, **Verifier request**.
- `AC-010`: **Example config files**; the existing completeness test holds both
  files to every setting.
- `AC-011`: decision 12; **Verdict file**.
- `AC-012`: decision 3; **Verdict contract**.
- `AC-013`: decision 4; **Verdict contract**, **Checks and hints** (`joins`).
- `AC-014`: decision 4; **Verdict contract** (`text_join`, `cell_joins`).
- `AC-015`: **Verdict contract** (`repeated_header_rows`).
- `AC-016`: **Verdict contract** (`repeated_items`).
- `AC-017`: **Verdict contract** (`markers`), **Checks and hints** (`markers`).
- `AC-018`: **Verdict contract** (`containers`).
- `AC-019`: decision 5 (`furniture`); **Judge request** (furniture rule).
- `AC-020`: decision 2; **Judge request** (reading order rule).
- `AC-021`: **Robustness**.
- `AC-022`: **Judge request**, **Checks and hints**; no field, default or check
  names a document type, language or direction.
- `AC-023`: decision 5; **Checks and hints**, **Agents**.
- `AC-024`: decision 5; **Checks and hints** (`header_rows`).
- `AC-025`: decisions 2 and 5; **Checks and hints** (`start_markers`).
- `AC-026`: decision 5; **Review issues**, **Test seams**.
- `AC-027`: decisions 7 and 11; **Verdict file** (`verification: null`).
- `AC-028`: decision 11; **Settings**.
- `AC-029`: decision 7; **Verifier request**, **Verdict application**.
- `AC-030`: **Verdict file** (`verification`).
- `AC-031`: decision 12; **Review issues**, **Summary and log lines**.
- `AC-032`: decision 12; **`cost.jsonl`**.
- `AC-033`: decision 10; **Cost estimate**.
- `AC-034`: every request goes through its agent's `LedgerModel` wrapper, which
  reserves its bound in the run's `SpendGuard` before sending, so concurrent
  requests are covered as page extraction's are; **`cost.jsonl`**.
- `AC-035`: decision 9; **Verdict inputs and reuse**.
- `AC-036`: decision 9.
- `AC-037`: decision 9; **Verdict file** (atomic writes, damage).
- `AC-038`: decision 13; **Errors**.
- `AC-039`: decision 14; **HTML report**.
- `AC-040`: **Test seams** define the contracts the tests rely on; writing and
  running the tests is Tester's.
- `AC-041`: No architectural impact — CI's workflows, jobs and required checks
  stay as they are; Tester's evidence covers them.
- `AC-042`: **CI and release** (the smoke script runs the three steps from the
  built wheel against the stand-in); evidence is Tester's.
- `AC-043`, `AC-045`: No architectural impact — the build, the wheel's contents
  (setuptools picks up `verifying/` in the src layout), release-please's
  configuration and the release workflows stay as they are; the release follows
  sign-off and merge.
- `AC-044`: **CI and release** (`pyproject.toml` description); the README is
  Documenter's.
- `AC-046`, `AC-048`: No architectural impact — Documenter's guides, README and
  examples, which describe the behavior this design fixes.
- `AC-047`: **Docs generator** (the generated reference pages come from the
  code's names, fields and docstrings); the guides are Documenter's.
- `AC-049`: No architectural impact — Documenter's update to
  `artifacts/next_cycle_inputs.md`; **Risks and Follow-up** lists what this
  design leaves to later steps.
- `AC-050`, `AC-051`: No architectural impact — the user's review of real runs
  after the build, with the default settings and with `verify` on.

## Components

- **Settings** (`config/schemas.py`, `providers/profiles.py`):
  `PageBreaksConfig`, `AdvancedConfig.page_breaks`, `Config.page_breaks_model`,
  `Config.verify_page_breaks`, `DEFAULT_PAGE_BREAKS_MODEL`.
- **Page-break verification** (`verifying/`):
  - `schemas.py`: the verdict, the verifier's verdict, the verdict file and its
    parts.
  - `prompts.py`: `PROMPT_VERSION = 1`, the judge's and the verifier's
    `PromptPair`s.
  - `validators.py`: `CHECKS`, `HINTS`, `run_checks`, `compare_with_hints`,
    `retry_message`, and the helpers that turn failures into check results, hint
    results and review issues.
  - `agents.py`: the judge and verifier agents with their output validators.
  - `llm.py`: `JUDGE` and `VERIFIER` agent names, the step's `StepModel`, the
    per-break input, `ask_judge`, `ask_verifier`, and the error mapping.
  - `verification.py`: current page files with their hashes, break inputs and
    fingerprints, `plan_breaks`, `verify_breaks` (the concurrent tasks),
    `break_file_path`, `BREAKS_FOLDER_NAME`, and request sizes for the estimate.
- **Review** (`review.py`): `page_breaks` in `StepName`, `BreakCheckName`,
  `BreakHintName`, both in `IssueName`; `verifier` shared.
- **Errors** (`errors.py`): `PageBreakError`, warning code `missing_page_files`.
- **Versions** (`schema_versions.py`): `BREAK_SCHEMA_VERSION = "1.0"`.
- **Costs and providers** (`costs/budget.py`, `costs/schemas.py`,
  `providers/ledger_model.py`): `estimate_page_breaks`, `BreakRequestSize`,
  `StepEstimate.breaks`, the typical-token constants, ledger lines for breaks.
- **Runner** (`pipeline/runner.py`, `pipeline/schemas.py`): the step, the run
  flow and pauses, the single estimate, `BreakCounts`, `StepRecord.breaks`,
  `RunResult.breaks`, the review list, `load_run`.
- **Python API and CLI** (`api.py`, `__init__.py`, `cli.py`): `verify_breaks`,
  `averify_breaks`, `BreakFile` and `PageBreakError` exported; the CLI gains no
  option.
- **Report** (`report/html.py`, its stylesheet): the page-breaks section.
- **Test tooling** (`tests/fixtures/mock_providers.py`, canned break answers,
  `scripts/smoke_installed_wheel.py`): routing break requests and running the
  step from the wheel.
- **Docs generator** (`scripts/generate_reference_docs.py`): the verdict file
  and page-break checks pages.

## Interfaces and Contracts

### Settings

- `advanced.page_breaks` (`PageBreaksConfig`, `extra="forbid"`), between
  `models` and `provider_retries` in `AdvancedConfig`'s alphabetical order. Its
  docstring says its settings apply to page-break verification's requests and
  its verifier's alike. Field docstrings as `ExtractionConfig`'s, with
  `concurrent_breaks` "How many page breaks are judged at the same time" and
  `instructions` "What is particular, different or nuanced about this PDF's page
  breaks, in your own words, for page-break verification's model and its
  verifier. Blank text counts as unset."
- `Config.pages`' docstring adds that page-break verification needs a current
  page file for every page.
- `build_model` and `_step_model` take `PageBreaksConfig` beside the other
  steps' settings; they read only `effort`, `max_output_tokens` and
  `request_timeout_seconds`.

### Example config files

`examples/config.json` and `examples/config.yaml` gain `advanced.page_breaks`
with every key at its default, in alphabetical key order, with comments as for
`advanced.extraction`: that `model` and `verify` follow the global settings when
`null`, that the instructions go only to this step's model and verifier, and
that a verifier adds cost.

### Current page files

- After page extraction, the step's page files are the page files extracted in
  this run plus, for every other page of the PDF, the `saved` page file of
  `plan_pages(page_indexes=<every page>, quiet=True)`. A page with neither lacks
  a current page file.
- Each current page file is read from disk with the SHA-256 of its bytes
  (`sha256:<hex>`, as `fingerprint` writes it). The hash is of the file as
  written, never of a re-serialized model.

### Verdict contract

`BreakVerdict`, the judge's answer and the verdict a verdict file keeps. Plain
types, enums, lists and objects only, with no patterns or bounds, so it fits
prompted output on Anthropic and native output on OpenAI. Fields in alphabetical
order, as pydelity's other models:

- `containers: list[ContinuingContainer]` — each box that continues across the
  break: `earlier` (its container ID on page N) and `later` (on page N+1).
- `continues: bool` — whether any content continues from page N to page N+1.
- `pieces: list[ContinuingPiece]` — each continuing piece; empty when nothing
  continues.
- `reason: str` — why, in a sentence or two, quoting the text that decides it.

`ContinuingPiece`:

- `cell_joins: list[TextJoin | None] | None` — for `merge_split_row`, one value
  per cell of page N+1's merged row (the first row after the repeated header
  rows), in the row's cell order: how that cell's text joins the text of the
  cell above it on page N, `null` when either cell has no text to join. `null`
  for every other join.
- `earlier_entry: str | None` — the list entry's ID when the piece ends in a
  list entry on page N.
- `earlier_item: str` — the ID of the item where the piece ends on page N.
- `join: Join` — `continue_text`, `continue_entry`, `new_entry`, `append_rows`
  or `merge_split_row` (decision 4).
- `later_entry: str | None` — the list entry's ID when the piece starts in a
  list entry on page N+1.
- `later_item: str` — the ID of the item where the piece starts on page N+1.
- `markers: list[ContinuationMarker]` — words or symbols on the continued unit
  on page N+1 that say it continues: `item` (its item ID), `row` and `cell`
  (from 0, in `table.rows` and that row, when a table cell carries it; else
  `null`) and `text` (the marker as printed).
- `repeated_header_rows: int | None` — for a table, how many rows at the top of
  page N+1's table repeat the earlier table's header, `0` when none do; `null`
  for other joins.
- `repeated_items: list[str]` — IDs of items on page N+1 before the continued
  unit that repeat what page N printed for it, such as a repeated title.
- `text_join: TextJoin | None` — `space`, `no_space`, `dehyphenate` or
  `newline`, for `continue_text` and `continue_entry`; `null` for other joins.

Join rules (enforced by the `joins` check):

| Join              | Earlier end                               | Later start                                | Text join                                                         | Other fields                                           |
| ----------------- | ----------------------------------------- | ------------------------------------------ | ----------------------------------------------------------------- | ------------------------------------------------------ |
| `continue_text`   | text item, or code item                   | same kind as the earlier end               | text: `space`, `no_space`, `dehyphenate`; code: `newline`         | entries, cell joins, header rows `null`                |
| `continue_entry`  | last entry of a list item, or a text item | first entry of a list item, or a text item | `space`, `no_space`, `dehyphenate`                                | at least one entry set; cell joins, header rows `null` |
| `new_entry`       | list item                                 | list item                                  | `null`                                                            | entries, cell joins, header rows `null`                |
| `append_rows`     | table item                                | table item                                 | `null`                                                            | header rows set, from 0 to the later table's rows      |
| `merge_split_row` | table item with at least one row          | table item                                 | `null`; `cell_joins` one per cell of the merged row, no `newline` | header rows set, below the later table's rows          |

Figures, fields and formulas are never an end or a start.

### Verdict file

`page_breaks/<NNNN>-<NNNN>.json`, `BreakFile`. Fields in alphabetical order:

- `checks: list[BreakCheckResult]` — each check's result on the kept verdict
  (`attempts`, `failures`, `name`, `passed`), in `CHECKS` order.
- `earlier_page_index: int`, `later_page_index: int` — the break's two pages
  (`AC-011`).
- `fingerprint: str` — of `inputs` with the schema version.
- `hints: list[BreakHintResult]` — each hint's differences on the kept verdict
  (`differences`, `name`), in `HINTS` order.
- `inputs: BreakInputs` — **Verdict inputs and reuse**.
- `issues: list[ReviewIssue]` — **Review issues**.
- `judged_at: datetime` — when the verdict was written (UTC).
- `judgment: Literal["model", "no_content"]` — decision 6.
- `pydelity_version: str`, `schema_version: str` (`BREAK_SCHEMA_VERSION`).
- `verdict: BreakVerdict` — the kept verdict.
- `verification: BreakVerification | None` — the verifier's review: `attempts`,
  `correction_applied`, `correction_failures` (checks a correction that was not
  kept still failed), `verdict` (`BreakVerifierVerdict` as given); `null` when
  no verifier ran (`AC-027`, `AC-030`).

Written with `write_model_atomic`; temporary files left in `page_breaks/` are
removed when the step starts. A file that does not load or has another major
schema version is damaged (decision 9). Output models accept unknown fields, as
the page file does.

### Verdict inputs and reuse

`BreakInputs`: `context` (`BreakContext`: `continuation_notes`, `instructions`,
`page_count`, `start_markers`), `earlier` and `later` (`BreakPage`:
`page_file_sha256`, `page_index`), `model`, `pdf_sha256`, `prompt_version`,
`rendering` (`RenderingSettings`), `settings` (`BreakSettings`: `check_retries`,
`effort`, `max_output_tokens`). The fingerprint is
`fingerprint(inputs.model_dump(mode="json") | {"schema_version": BREAK_SCHEMA_VERSION})`.
`plan_breaks` computes every break's inputs from the current page files, loads
each verdict file, warns on damage, applies the reuse rule of decision 9, and
logs `Page-break verification: <n> breaks, <r> reused, <j> to judge` unless
quiet. A verdict file passed over only because no verifier reviewed it gets an
info line, as for pages.

### Judge request

- Instructions (`prompts.py`, `judge_break`), in this order:
  1. The task: judge one break between two consecutive pages, saying whether
     content carries on and exactly how, for a program that joins the pages'
     items and knows no language.
  2. What comes: each page as an upright image with its items as another model
     extracted them, in reading order, with IDs. The items help name and locate
     content and can be wrong in places; the images decide what continues; the
     verdict names items by their listed IDs.
  3. Reading order: the end of page N is where its reading order ends and the
     start of page N+1 where its reading order starts, following each page's
     writing direction and columns, not its top and bottom edges.
  4. Page furniture (role `artifact`) is never joined, and furniture between two
     pieces does not stop content from continuing.
  5. Pieces, join rules and text joins, as **Verdict contract** defines them,
     with what each text join means in terms that hold for any script: a space
     where the script separates the two pieces with a space, no space where it
     writes none or the break falls inside a word without a hyphen, removing the
     hyphen where a word broken with a hyphen at the line end continues, and a
     newline for code.
  6. Tables: the same table continues when its column structure matches, nothing
     outside the grid announces a new table between the start of page N+1 and
     the table, and no header redefines the columns; a border or closed box
     around each page's part is no sign of a new table; a split row is a row
     whose cells are cut by the break and resume in the first row after any
     repeated header rows.
  7. Repeated items, continuation markers and containers, as defined.
  8. Nothing continuing is a valid answer; decide from what the pages show.
  9. The answer is checked by code for consistency, and the model is told what
     to fix if a check fails.
  10. Hints: the survey's continuation notes and start markers (each start
      marker's text and description), which describe the whole PDF, can be
      wrong, and are overridden by the pages; `none` when the survey gave none.
  11. `advanced.page_breaks.instructions` under its own heading, when set.
- No instruction, example or field description is in a particular language,
  names a document type or domain concept, or assumes a direction (`AC-022`).
- User content: decision 2. The first text part's first line is
  `Page break between page indexes <i> and <i+1> (pages <i+1> and <i+2> of <n>)`.
  The second text part introduces page N+1. Each page's items are serialized as
  compact JSON, one item per line; Developer chooses the exact layout.
- Agent: `structured_output(model, BreakVerdict)`,
  `retries={"output": check_retries}`, an output validator that runs
  `run_checks` only and raises `ModelRetry` with `retry_message(failures)` while
  retries remain, and accepts the last verdict as it is. Request settings as
  `extracting/llm.py` `_model_settings`.

### Verifier request

- Instructions (`verify_break`): another model's verdict on this break, check it
  against the pages and correct it; a checklist of what code cannot judge
  (content that continues but is missed, pieces that do not continue, wrong ends
  or starts, wrong join or text joins, a wrong count of repeated header rows,
  repeated items or markers missed or wrong, containers missed or wrong);
  verdict rules as page extraction's (passed with no problems and no correction
  when nothing material is wrong, otherwise every problem and the whole verdict
  corrected, starting from the verdict); a correction must pass the checks and
  need not agree with the hints; then the judge's rules, hints and instructions
  as above.
- User content: the judge's content, then a text part with
  `The page-break verdict to review:` and the verdict as JSON,
  `Checks it still fails, which a correction must pass:` with one line per
  failure or `none`, and `Differences from the hints, which the pages override:`
  with one line per difference or `none`, then the cache point.
- `BreakVerifierVerdict`: `corrected: BreakVerdict | None`, `passed: bool`,
  `problems: list[BreakProblem]`, with `VerifierVerdict`'s invariants.
  `BreakProblem`: `category` (`continues`, `piece`, `join`, `header_rows`,
  `repeated_items`, `markers`, `containers`, `other`), `description` (what is
  wrong and where), `item` (the ID of the item or container on either page it is
  about, or `null`).
- Agent: as page extraction's verifier agent, with the correction retry message
  "Your corrected verdict does not pass every check. Give the whole verdict
  again, with the correction fixed." followed by `retry_message`.

### Verdict application

1. The judge's verdict is accepted (every check passed, or retries ran out).
2. With `verify_page_breaks` on: the verifier request on it, given its check
   failures and `compare_with_hints` differences.
3. Kept verdict: the correction when it has no check failure, else the judge's
   verdict. `checks` are the kept verdict's results with the attempts of the
   model that gave it.
4. `hints`: `compare_with_hints` on the kept verdict.
5. `issues` (**Review issues**), the verdict file, its atomic write, and the
   break's log line.

### Checks and hints

Checks, in this order (`BreakCheckName`); each failure's `details` names the
item, entry, container or cell concerned (`{"item": "p0003-007"}` and the like)
and its `page_index` is the page it is on:

1. `ids` — every item, entry and container the verdict names exists on the page
   it names (ends and earlier containers on page N; starts, later containers,
   repeated items and marker items on page N+1); each entry belongs to the item
   named with it; each marker's `row` and `cell` exist in its item's table; a
   marker with a `cell` has a `row`.
2. `continues` — `continues` is true exactly when `pieces` is not empty.
3. `duplicates` — no item or entry on page N ends two pieces, none on page N+1
   starts two, no container is named twice on one page, and no repeated item is
   also a piece's start.
4. `joins` — **Verdict contract**'s join rules: kinds, entries, text joins,
   `cell_joins` length and values, `repeated_header_rows` set only for tables
   and within its bounds.
5. `furniture` — no piece ends or starts in an item with role `artifact`.
6. `header_rows` — for each table piece with `repeated_header_rows` n above 0,
   page N+1's table's first n rows match, in order, n distinct rows among page
   N's table's first n + h rows, where h is page N's table's `header_rows`.
7. `repeats` — each repeated item whose text is not empty matches some text
   printed on page N: an item's text, a list entry's text, or a table row's cell
   texts joined in order.
8. `markers` — each marker's text is in the text of the item or cell that
   carries it.

Text matching in checks and hints uses `comparison_form` (NFKC, case-folded,
letters, marks and numbers only), so it holds in any script. Two texts match
when their comparison forms are equal or both have at least 3 characters and the
Dice coefficient of their `trigrams` is at least 0.8; `repeats` also accepts
either form containing the other, so a repeated heading with a marker added
matches the original; `markers` requires the marker's form to be contained in
the carrier's. Both empty counts as a match for header rows.

Hint (`BreakHintName`), never sent back:

- `start_markers` — a piece whose start on page N+1 (the start item's text, the
  start entry's text, or for a table the cell texts of its first row after the
  repeated header rows) begins, in comparison form, with the comparison form of
  one of the survey's start markers. A marker whose comparison form is empty is
  skipped. The difference message says which marker the start begins with and
  that the verdict joins it to page N; it never tells the model what to change.

Check failure messages may say what to fix. Every retry message is built from
`run_checks` failures only.

### Review issues

A break's `issues`, in this order: each check still failing on the kept verdict;
each hint difference, unless a verifier ran and passed the verdict or its
correction was kept; each verifier problem, when a verifier ran and its
correction was not kept. Every issue has `step: "page_breaks"`, `page_index` =
the break's earlier page, `item_id` = the item the failure or problem names when
it is on either page, else `null`, and a message that names both pages, such as
`pages 4 and 5: ...`. Verifier issues have `check: "verifier"` and
`details: {"category": <category>, "item": <item or null>}`. `run.json` `review`
lists the survey's issues, then each selected page's, then each break's in break
order. `ReviewIssue.page_index`'s docstring says that for page-break
verification it is the break's earlier page.

### `cost.jsonl`

Each judge and verifier request writes one line with `step: "page_breaks"`,
`agent: "judge"` or `"verifier"`, and `page_index` = the break's earlier page.
The step's `LedgerModel` wrapper for a break sets those (a `for_page` call with
the earlier page, or a sibling Developer names). `LedgerEntry.agent`'s and
`page_index`'s docstrings say so. `RunCost.by_step["page_breaks"]` and the
step's `cost_usd` sum both agents' lines.

### `run.json`

- Step name `page_breaks`; statuses as for the other steps: `completed`,
  `reused` (every verdict reused), `failed`, `stopped`, `skipped`.
- `StepRecord.breaks: BreakCounts | None` (required): `total` (breaks in the
  PDF), `judged` (verdicts written by this run, with or without a request),
  `reused`; `null` for the other steps and for a skipped page-break step.
- `outputs`: `["page_breaks/"]`.
- `RUN_SCHEMA_VERSION` stays `"1.0"` (scope).

### Warnings

- `missing_page_files` (new `WarningCode`), issued in the page-break step:
  "Page-break verification needs a current page file for every page, and pages
  `<ranges>` have none. Run pydelity again without --pages (pages in the config
  file), or with pages that include them, to verify the page breaks."
  `details: {"page_indexes": [...]}` (0-based). The step is `skipped` and the
  run `completed`.

### Summary and log lines

- `_step_summary`: `page_breaks completed (7 breaks: 5 judged, 2 reused)`.
- The summary's review lines show
  `page_breaks, pages 4 and 5, item p0004-012: ...` for a break issue.
- Paused after page extraction: "Paused after page extraction wrote new page
  files. Check pages/ and report.html, then run pydelity again to verify the
  page breaks, or pass --no-pause (pause=False in Python) to run every step at
  once." The `--overwrite` note as after a survey pause, naming the pages too.
  The summary knows which step paused from the last step that is not `skipped`.
- One-page PDF: an info line that the PDF has one page and so no page breaks.
- Per break:
  `Break after page 4 (pages 4 and 5): continues, 2 pieces, 0 review issues, verifier passed; $0.06 for 2 requests`
  (or `nothing continues`, `no request, page 5 has no content items`,
  `no verifier`).
- Estimate lines name steps with a title (`Survey`, `Extraction`,
  `Page-break verification`) instead of capitalizing the step name, and say
  `7 breaks` where the extraction line says pages.

### Cost estimate

- `BreakRequestSize`: `judge_chars` (instructions, both page texts and the
  verdict format, without images) and `verifier_chars` (the verifier's
  instructions, both page texts and the verifier verdict format, without images
  and without the verdict it reviews).
- `estimate_page_breaks(config, breaks)`: per break, judge input =
  `ceil(judge_chars / PROMPT_CHARS_PER_TOKEN) + 2 * image_tokens` of the step's
  model's profile. Expected: one judge request with
  `TYPICAL_BREAK_OUTPUT_TOKENS = 4_000` of output, plus, with the verifier on,
  one verifier request reading that verdict with
  `TYPICAL_BREAK_VERDICT_OUTPUT_TOKENS = 3_000`. Maximum: every attempt of each
  agent that runs with `max_output_tokens`, earlier answers added to the input,
  as `estimate_extraction`. `requests_max = agents * attempts * breaks`.
  `StepEstimate(name="page_breaks", breaks=<n>, pages=None, verifier=...)`;
  `reused` when no break is to be judged. `no_content` breaks cost nothing and
  are not counted.
- `StepEstimate.breaks: int | None` (required): breaks the step would judge, for
  page-break verification; `None` for the other steps.
- Sizes: a break whose page files are both current and unchanged by this run is
  measured by building its prompts (with an empty verdict for the verifier). A
  break with a page that this run will extract, or before the survey exists,
  uses an allowance: the instructions measured from the survey when it exists,
  else a fixed allowance, plus for each page a fixed allowance plus twice its
  text-layer characters. Developer rounds the allowance constants up from
  measured requests on the test PDFs, as page extraction's were.
- Which breaks an estimate covers (in the run's single estimate, in `estimate()`
  and in `aestimate()`):
  - none when the PDF has one page, or the run will pause before the step (a new
    survey or a page extraction that will extract a page, with `pause` on), or a
    page will lack a current page file after page extraction;
  - with the survey reused: every break whose verdict would not be reused, where
    a break touching a page to extract is always judged;
  - with the survey to run and `pause` off: every break, when every page is
    selected or has a page file whose `inputs.pdf_sha256` matches the PDF; none
    otherwise.
- The API key of the step's provider is checked with the other steps' before the
  first request, whenever the estimate covers the step.

### `load()`

`RunResult.breaks: list[BreakFile]` (required): for a run, its verdicts in break
order (empty when the step was skipped); for `load`, every verdict file in
`page_breaks/` whose `inputs.pdf_sha256` equals `pdf_facts.json`'s and whose
`earlier` and `later` `page_file_sha256` equal the hashes of the page files
`load` returns for those pages, in break order. A verdict file that does not
validate, or has another major schema version, raises `OutputError`, as a page
file does.

### Python API

- `verify_breaks(pdf=None, *, allow_over_max_cost=False, config=None, **settings) -> list[BreakFile]`
  and its async twin `averify_breaks`, built like `extract` and `aextract`
  (decision 16). Their docstrings list `PageBreakError` with the other errors.
- `run`/`arun` docstrings: the run goes through page-break verification and
  pauses after a step that wrote new output; `estimate`/`aestimate` docstrings
  include page-break verification.
- `pydelity.__all__` gains `verify_breaks`, `averify_breaks`, `BreakFile` and
  `PageBreakError`.

### Errors

`PageBreakError(PydelityError)`. Message forms, from `verifying/llm.py` `_run`:
`Break after page <n> (pages <n> and <n+1>), judge: the model refused. ...`,
`... used all <k> output tokens before finishing its answer. Raise advanced.page_breaks.max_output_tokens, or lower advanced.page_breaks.effort.`,
`... the model gave no usable answer: ...`. Provider errors stay
`ProviderError`. The CLI maps `PageBreakError` to `FAILED` with the others.

### HTML report

- `ReportInputs` gains `breaks` (the run's verdicts) and the current page files
  they were judged from, by page index.
- Section "Page breaks", after the pages, one card per verdict with anchor
  `break-<NNNN>` (earlier page index): heading `Pages <n> and <n+1>`, both page
  images with boxes for each piece's end and start, repeated items, marker items
  and continuing containers (boxes in points on the displayed page, as page
  cards draw them), and the details of decision 14. `_STEP_TITLES` gains
  `page_breaks: "Page-break verification"`, and review entries for a break link
  to its card. All text from the PDF, settings or model is escaped.
- No verdicts: no section.

### Robustness

Page-break verification runs to completion on any page file that loads and any
survey that loads (`AC-021`): items with a kind and no matching content (a
`table` item with `table: null`, a `list` with `entries: null`), `container` or
`caption_of` `null`, a `column_order` that does not fit the direction, and page
files with failing `checks`, `hints` or `issues`. The listing shows such fields
as they are. Checks treat missing content as a failure of the check that needs
it, never as an error. The step reads no profile range or artifact mapping.

### Test seams

- The judge's user content contains
  `Page break between page indexes <i> and <i+1>`; the verifier's contains
  `The page-break verdict to review:`. No page-break request contains
  `Page index <i> (`, `The extraction to review:` or
  `The survey answer to review:`, so the stand-in routes them apart from the
  other steps' requests.
- Hint differences reach a model only in the verifier's user content, after
  `Differences from the hints, which the pages override:`. Every retry message
  is built from `run_checks` failures only.
- The stand-in answers a break request with the canned judge or verifier answer
  for its earlier page index, whatever order concurrent requests arrive in.
- No step code reads the environment or chooses behavior for tests.

### CI and release

- Workflows, jobs and required checks are unchanged.
  `scripts/smoke_installed_wheel.py` runs the CLI and the Python API through the
  survey, page extraction and page-break verification without a pause, against
  the stand-in, on the two-page 1965 scan (one break), with its expected
  requests updated, and checks that the output folder loads with one verdict.
- `pyproject.toml`'s description says pydelity surveys a PDF, extracts its pages
  and verifies its page breaks, with an optional verifier for each step. The
  version and release-please's configuration are unchanged.

### Docs generator

`scripts/generate_reference_docs.py` gains a verdict file page
(`page_breaks/<NNNN>-<NNNN>.json` from `BreakFile` and its parts) and a
page-break checks page (checks and hints apart, from `CHECKS` and `HINTS`, with
the rules of decision 5), and picks up `advanced.page_breaks`, `verify_breaks`,
`averify_breaks`, `StepRecord.breaks`, `RunResult.breaks`,
`StepEstimate.breaks`, the new ledger docstrings and the new constants in
`costs/budget.py` from the code, so CI's staleness check covers them. Page names
are the user's to approve with the other names.

## Data and Control Flow

1. Settings resolve `page_breaks_model` and `verify_page_breaks` once.
2. Survey step as now. When the survey runs, its single estimate covers page
   extraction and page-break verification as far as the run will reach them, and
   the page-break model's API key is checked when the estimate covers it.
3. Pause after a new survey; extraction and page-break verification are recorded
   `skipped`.
4. Page extraction as now, with the estimate when it is the run's first spending
   step. `extract()` ends here.
5. Page-break step: one page → `skipped`. Current page files (**Current page
   files**); a page without one → `missing_page_files`, `skipped`, run
   `completed`. New page files and `pause` on → `skipped`, run `paused`.
   Otherwise `plan_breaks`; when the estimate has not been made, estimate and
   ask; with nothing to judge, the step ends `reused`.
6. Breaks to judge run at most `concurrent_breaks` at once on one `PdfWorker`.
   Per break: a page without content items → `no_content` verdict; else render
   both upright images, build the texts, the judge request with checks and
   retries, the verifier when on, apply the verdict, compute hints and issues,
   write the verdict file atomically, log the line. Developer may keep a page's
   image until both its breaks have used it. The first failure cancels the other
   tasks and ends the step `failed`.
7. Every request goes through its agent's `LedgerModel` wrapper: reserve its
   bound, send, write its ledger line (`page_breaks`, earlier page, agent),
   release.
8. `run.json` with `StepRecord.breaks`, the review list with the breaks' issues,
   the report with the page-breaks section, and the summary.

## Technical Acceptance Criteria

- `AC-001`: with default settings and every page current after page extraction,
  `pydelity <pdf>` and `run()` both make page-break requests after the last page
  request, and both record the same steps and statuses.
- `AC-002`: the step reads only page files made by page extraction in this run
  or returned as `saved` by `plan_pages` over every page with `quiet=True`; a
  page file with another `inputs.pdf_sha256`, another fingerprint, or no
  verification while page extraction's verifier is on is never read by it.
- `AC-003`: with a page lacking a current page file, no request goes through a
  `page_breaks` wrapper, the step is `skipped`, one `missing_page_files` warning
  names exactly those pages, and the run is `completed`; with every unselected
  page current, every break is judged or reused.
- `AC-004`: a one-page PDF makes no page-break request and the run completes.
- `AC-005`: with `pause` on, a run whose page extraction wrote a page file ends
  `paused` with the step `skipped` and the pause message; the next run with the
  same settings makes no page request and judges the breaks; a run that reuses
  every page file goes on; `pause` off never pauses.
- `AC-006`: `verify_breaks` and `averify_breaks` never pause, reuse a valid
  matching survey and page files, run what is missing first, follow decision 8
  for a narrowed `pages`, and return the verdicts in break order.
- `AC-007`: `load` returns, in break order, exactly the verdicts whose PDF hash
  and both page-file hashes match the facts and the page files it returns.
- `AC-008`: `page_breaks_model` is `advanced.page_breaks.model`, else `model`,
  else `anthropic:claude-opus-5-5`, with effort `high` by default.
- `AC-009`: the judge's and verifier's instructions end with
  `advanced.page_breaks.instructions` when set and contain no other step's
  instructions; no page-break request contains a page file's `inputs`; no other
  step's request contains `advanced.page_breaks.instructions`.
- `AC-010`: both example files hold `advanced.page_breaks` with every key at its
  default and load without a `ConfigError`.
- `AC-011`: each judged break has `page_breaks/<NNNN>-<NNNN>.json` with
  `earlier_page_index`, `later_page_index` and `verdict.continues`.
- `AC-012`: each piece names `earlier_item` and `later_item`, with the entry IDs
  when an end or start is a list entry; a verdict may hold several pieces.
- `AC-013`, `AC-014`: a verdict breaking a join rule of **Verdict contract**
  fails `joins`; `continue_text` and `continue_entry` always carry a text join,
  `newline` only between code items, and `merge_split_row` one cell join per
  cell of the merged row.
- `AC-015`: every table piece carries `repeated_header_rows` ≥ 0.
- `AC-016`: `repeated_items` holds page N+1 item IDs, checked by `ids` and
  `repeats`.
- `AC-017`: each marker names its item, its row and cell when a table cell
  carries it, and its text, checked by `ids` and `markers`.
- `AC-018`: `containers` pairs container IDs on both pages, independent of
  `pieces`.
- `AC-019`: a piece ending or starting in an `artifact` item fails `furniture`;
  the instructions say furniture never joins and does not stop content from
  continuing.
- `AC-020`: both images are rendered with their page file's `rotation`; item
  boxes in the request are on the upright image's grid; the instructions define
  a page's end and start by reading order.
- `AC-021`: the step completes on page files and surveys with the faults
  **Robustness** lists, and no check raises on them.
- `AC-022`: no prompt text, verdict field, default or check names a document
  type, domain concept or language, or assumes a writing direction; checks
  compare text only in comparison form.
- `AC-023`: the judge's output validator raises `ModelRetry` only for
  `run_checks` failures, within `check_retries`; a last verdict still failing is
  written with each failure in `checks` and `issues`, and the run goes on.
- `AC-024`: a table piece whose counted rows do not match page N's leading rows
  fails `header_rows`.
- `AC-025`: the instructions hold the survey's continuation notes and start
  markers under the hints heading; a piece starting with a start marker gives a
  `start_markers` difference.
- `AC-026`: a hint difference never raises `ModelRetry`, never appears in a
  retry message, and never sets a step or run status; it is in `hints` always
  and in `issues` unless the verifier passed the verdict or its correction was
  kept.
- `AC-027`: with default settings, no request goes through a page-break
  `verifier` wrapper, no ledger line has `step: "page_breaks"` and
  `agent: "verifier"`, and every verdict file has `verification: null`.
- `AC-028`: `verify` (file, `--verify`/`-vf`, `verify=True`) turns on
  `verify_page_breaks` when the override is `null`; the override's `true` or
  `false` wins; `Config.verify_page_breaks` exists.
- `AC-029`: a correction failing a check is sent back within `check_retries` and
  never kept; one passing every check is kept whatever its hint differences;
  issues follow **Review issues** for each outcome.
- `AC-030`: `verification` holds the verifier's verdict as given, its attempts,
  whether the correction was applied and the checks a rejected correction
  failed.
- `AC-031`: every page-break issue has `step: "page_breaks"`, the earlier page
  in `page_index`, both pages in its message, and its item when one applies, and
  appears in `run.json` `review` and the summary's lines.
- `AC-032`: each page-break request writes one ledger line with its step, the
  earlier page and its agent; `by_step["page_breaks"]` and the total include
  them.
- `AC-033`: the estimate's page-break step exists exactly when the run will
  judge breaks, covers the breaks **Cost estimate** names, prices the verifier
  exactly when it will run, and a run whose first request is a page-break
  request shows the estimate and asks before it.
- `AC-034`: each page-break request's bound is reserved in the run's
  `SpendGuard` before it is sent, with `concurrent_breaks` requests in flight.
- `AC-035`: a rerun with unchanged inputs makes no request; changing either page
  file, the continuation notes or start markers, the step's instructions, model
  or answer settings re-judges exactly the affected breaks; re-extracting one
  page re-judges its two breaks only; `overwrite` re-judges every break;
  changing only `advanced.page_breaks` settings makes no survey or page request.
- `AC-036`: with the step's verifier turned on, verdicts with
  `verification: null` and `judgment: "model"` are judged again; changing
  another step's verifier setting re-judges a break only when that step's
  outputs changed a page file's bytes or the survey's continuation fields.
- `AC-037`: verdict files are written atomically; a damaged one gives
  `damaged_output` and is judged again.
- `AC-038`: a failed page-break request after the provider retries, or an
  unusable answer, ends the run `failed` with `ProviderError` or
  `PageBreakError`, the CLI exits 1, verdict files already written stay, and the
  next run judges only breaks without a reusable verdict.
- `AC-039`: the report holds one card per verdict with both page images, the
  named items and containers drawn, every verdict field of decision 14, the
  verifier's outcome, and links from the break's review issues.
- `AC-042`: the smoke script's runs complete with one verdict and load.
- `AC-044`: the package description names the three steps and the optional
  verifiers.
- `AC-047`: the generated reference pages hold every new setting, function,
  verdict-file field, `run.json` and `cost.jsonl` change, and the page-break
  checks and hint, and CI's staleness check passes.

## Build Plan

1. **Settings** (`AC-008` to `AC-010`, `AC-028`). MODIFY
   `src/pydelity/config/schemas.py`, `src/pydelity/providers/profiles.py`,
   `src/pydelity/providers/factory.py` (settings type), `examples/config.json`,
   `examples/config.yaml`. Names approved first.
2. **Verdict contract and names** (`AC-011` to `AC-018`, `AC-027`, `AC-030`).
   CREATE `src/pydelity/verifying/__init__.py`,
   `src/pydelity/verifying/schemas.py`; MODIFY `src/pydelity/review.py`,
   `src/pydelity/schema_versions.py`, `src/pydelity/errors.py`. Depends on 1.
3. **Checks and hints** (`AC-019`, `AC-021` to `AC-026`). CREATE
   `src/pydelity/verifying/validators.py`. Depends on 2.
4. **Prompts, agents and requests** (`AC-009`, `AC-020`, `AC-022`, `AC-023`,
   `AC-029`, `AC-038` mapping). CREATE `src/pydelity/verifying/prompts.py`,
   `src/pydelity/verifying/agents.py`, `src/pydelity/verifying/llm.py`; MODIFY
   `src/pydelity/providers/ledger_model.py` only if Developer adds a break
   wrapper. Depends on 3.
5. **The step** (`AC-002`, `AC-011`, `AC-029` to `AC-031`, `AC-035` to
   `AC-038`). CREATE `src/pydelity/verifying/verification.py`. Depends on 4.
6. **Test tooling** (seams for self-checks). MODIFY
   `tests/fixtures/mock_providers.py`; CREATE canned break answers under
   `tests/fixtures/` (folder name to approve). Depends on 4; may go with 5.
   Tests themselves are Tester's.
7. **Costs** (`AC-032` to `AC-034`). MODIFY `src/pydelity/costs/budget.py`,
   `src/pydelity/costs/schemas.py` (`StepEstimate.breaks`, `LedgerEntry`
   docstrings). Depends on 5 for request sizes.
8. **Run flow, API and CLI** (`AC-001` to `AC-007`, `AC-031`, `AC-033`). MODIFY
   `src/pydelity/pipeline/runner.py`, `src/pydelity/pipeline/schemas.py`,
   `src/pydelity/api.py`, `src/pydelity/__init__.py`, `src/pydelity/cli.py`
   (error mapping and summary only, if needed). The run flow, the single
   estimate's placement, `StepRecord.breaks` and `RunResult.breaks` change
   together. Depends on 5 and 7. This is the critical path.
9. **Report** (`AC-039`). MODIFY `src/pydelity/report/html.py` and its
   stylesheet. Depends on 8.
10. **Smoke test, docs generator and package text** (`AC-042`, `AC-044`,
    `AC-047` in code). MODIFY `scripts/smoke_installed_wheel.py`,
    `scripts/generate_reference_docs.py`, `pyproject.toml` (description);
    regenerate `docs/src/content/docs/reference/` with `just docs-reference`.
    After 1–9.

New code follows the user styles' module order and keyword-argument order. Tests
are Tester's; the guides, README and `artifacts/next_cycle_inputs.md` are
Documenter's.

## Risks and Follow-up

- Cost: each break sends two whole page images and both pages' items, and each
  page's image is sent for two breaks. The instructions are cached across
  breaks, the images are not. No pydelity measurement exists; the 4,000- and
  3,000-token typical outputs are guesses the real runs check.
- Verdicts cite item IDs, which change when a page is extracted again. The
  page-file hashes make such verdicts stale, so they are judged again, never
  misapplied, but re-extracting a page pays for its two breaks too.
- The `header_rows` and `repeats` checks compare page extraction's readings of
  two pages. A misread header or title can fail a correct verdict; the model
  then spends its retries and the verdict is kept and listed. The 0.8 similarity
  bound is a judgment call that the real runs test, and `repeats` can pass a
  short repeated item whose text happens to appear on page N.
- Models must count table rows and cells for `markers` and `cell_joins`; the
  listing numbers them to help. A miscount fails `ids` or `joins`.
- The `start_markers` hint depends on the survey's markers. Wrong markers list
  correct joins for review when no verifier runs.
- Page extraction can structure two pages differently (a list on one page, text
  on the next; providers differ). `continue_entry` accepts a list entry joined
  to a text item, but a table on one page and text on the other cannot be
  joined, and fails `joins` if the model tries.
- With `pause` on, a new PDF takes three runs. With `overwrite` and a narrowed
  `pages`, page-break verification never runs (decision 8).
- Prompted output on Anthropic has no grammar, so a verdict that is not valid
  JSON costs a retry and, on the last attempt, stops the run.
- Left to later steps for `artifacts/next_cycle_inputs.md`: continuation across
  pages that do not follow each other; "continued on the next page" notes on
  page N, which the verdict does not name; structure tags as evidence (option
  A); whether a `no_content` page breaks a unit that continues around it.
- What stops working (no backwards compatibility is kept):
  - A 0.2.0 `run.json` has no `breaks` in its step records, so `load()` on a
    0.2.0 output folder raises `OutputError` until a run rewrites `run.json`.
    Page files, `pdf_survey.json`, `pdf_facts.json` and `cost.jsonl` from 0.2.0
    stay valid and are reused.
  - `run()` and `pydelity <pdf>` with default settings now stop after a page
    extraction that wrote page files (status `paused`), where 0.2.0 completed,
    and judge breaks on the next run. A script that expected one run to finish
    needs `pause=False` or a second run.
  - Code that builds `StepEstimate`, `StepRecord` or `RunResult` must pass the
    new required `breaks` field.
  - `LedgerEntry.page_index` and `ReviewIssue.page_index` now also mean a
    break's earlier page, for `step: "page_breaks"`; code that groups ledger
    lines or issues by page without the step mixes breaks with pages.

## Alternatives

- Windowed requests judging about ten breaks at once (option C): rejected. A
  verdict would be made from every page of its window, so re-extracting one page
  would re-judge the whole window or hold verdicts whose inputs were not all
  fingerprinted (`AC-035`), and an eleven-image request is the kind of size
  per-model limits would have to police. Cached instructions already carry the
  survey's whole-PDF hints to every break.
- Seam images joining the bottom of page N to the top of page N+1 (option B):
  rejected. The end of a page in reading order is not at its bottom on
  right-to-left multi-column or vertical pages, and repeated headers and titles
  are compared with the top of the unit on page N.
- Item labels drawn on the images (option B's set-of-mark): rejected. Labels
  hide the text and hyphens the judgment turns on, and dense pages crowd them.
  The listing's grid boxes are the coordinates page extraction's model wrote.
- Structure tags as evidence (option A): not now. Tags exist on some PDFs only
  and nothing links them to items yet; that link is new probe work no acceptance
  condition needs.
- A confidence field with thresholds: rejected. No acceptance condition uses it,
  assembly joins where the verdict says, and the verifier reviews every break or
  none.
- `header_rows` and `repeats` as hints: rejected, since assembly drops what they
  name and a wrong count loses content; hints would let it through with only a
  review-list line.
- A `break` field on `ReviewIssue` and `LedgerEntry`: rejected. Breaks are only
  between consecutive pages, so the earlier page in `page_index` with the step
  names the break, and a field holding the later page would only repeat it.
- Per-cell text joins keyed by grid column: rejected for the cell order of the
  merged row, which the model reads directly; assembly maps cells to columns.
- Hashing a re-serialized page file instead of its bytes: rejected; the bytes as
  written need no round-trip guarantee.
- Letting figures continue: rejected; assembly would have nothing to join, and
  the brief's past runs found no figure continuation that mattered.

<!-- STANDARDS
Artifact: ARCHITECTURE
Cycle: build-step-3-page-break-verification-of-20261122T170208Z-00fe2896
-->

# Technical Design: page-break verification and release 0.3.0

## Context

- Scope:
  `.standards/docs/scope/build-step-3-page-break-verification-of-20261122T170208Z-00fe2896.md`
  (`AC-001` to `AC-024`, `AC-027`, `AC-028`, `AC-031` to `AC-035`, `AC-037` to
  `AC-049`, `AC-052` to `AC-062`). `AC-025`, `AC-026`, `AC-029`, `AC-030`,
  `AC-036`, `AC-050` and `AC-051` are retired. Target maturity is Level 3.
  Architect mode: feature. The new step is a bounded capability that follows the
  shape the survey and page extraction already set (settings, checks and hints,
  opt-in verifier, reuse, estimate, review list, report). Nothing here is a
  transition or a new cross-cutting rule.
- Rework after the real runs. The user's ten Anthropic runs and their review
  (`.standards/docs/reviews/build-step-3-page-break-verification-of-20261122T170208Z-00fe2896/final-deliverable.md`,
  C12 and R-1 to R-4) led to the scope rework this revision follows. It changes
  decisions 2, 4, 5, 7, 9, 13 and 14 and the sections they reach, and the rest
  stands as built. The code from the earlier pass (`src/pydelity/verifying/` and
  the run, estimate and report changes) is this cycle's own work, not baseline.
  **Build Plan** lists only what changes in it. R-2, a header row that page
  extraction misread, is a page file fault with no fix in this step. R-4, merge
  or append for the same row, is the kind of disagreement the verifier's
  comparison now flags.
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
  retries; an opt-in verifier judges every break a second time without seeing
  the first judgment, or judges none, and code compares the two; one
  structured-output mode per provider; document-type, language and direction
  agnostic; PyMuPDF on one worker thread; no per-model limits; no default
  `max_cost`; async twins; no backwards compatibility; existing
  `schema_version`s, `PROBE_VERSION` and `PROMPT_VERSION`s stay; the step's own
  versions start at 1 and `"1.0"`.
- The user approved the earlier pass's names in the development plan: the step
  name `page_breaks`, the settings section `advanced.page_breaks` and its keys,
  the folder `page_breaks/` and its file names, the agents `judge` and
  `verifier`, the Python functions `verify_breaks` and `averify_breaks`, the
  module `verifying/verification.py`, the warning code `missing_page_files`, and
  the `run.json`, estimate and verdict-file field names and the check and hint
  names. This revision's new names are proposals for the user to approve before
  the build step that creates them: the cell join value `repeat`, the review
  issue name `verdicts_differ`, the fields of `BreakVerification` (`attempts`,
  `checks`, `differences`, `verdict`), the difference `details` keys (`field`,
  `kept`, `verifier`, `item`, `entry`, `cell`) and their `field` values, the
  function `compare_verdicts`, and the `BreakRequestSize` fields `chars` and
  `judge`.
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
   `hints` or `issues`, another step's instructions (`AC-009`), another verdict
   or a hint difference. The judge and the verifier send the same request
   (decision 7).
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
   the continued text a text item. `new_entry` continues a list with a new entry
   on page N+1. Its earlier end is the list on page N, or a text item when page
   extraction read the list's part on page N, such as its first entry, as text
   (`AC-052`). Its later start is a list. `append_rows` continues a table with
   new rows. `merge_split_row` merges the row cut by the break with the first
   row on page N+1 after any repeated header rows, and gives one cell join per
   cell of that row. A cell join is a text join, or `repeat` when the later cell
   only repeats the text of the cell above it, such as a row label printed again
   with or without "(contd)", so that assembly keeps the text once (`AC-053`),
   or `null` where one side of the cell has no text. Text and list entries
   continue only when the break leaves the text itself unfinished, and the
   instructions say so (**Judge request**, `AC-054`). Figures, fields and
   formulas never continue: assembly has nothing to join for them, and a figure
   printed across two pages stays two images. The text join is the verdict's
   because code cannot choose it without language rules (`AC-014`).
5. **Checks are what code can decide about the verdict, and the only hint is the
   survey's start markers.** Checks test the verdict against itself, the two
   page files and its hard limits; a failure may send it back within
   `advanced.page_breaks.check_retries`, and a last verdict still failing one is
   kept and listed while the run goes on (`AC-023`). Checks, in order: `ids`,
   `continues`, `duplicates`, `joins`, `furniture`, `header_rows`, `repeats`,
   `markers` (**Checks and hints**). `header_rows` compares the rows a verdict
   counts as repeated with the earlier table's leading rows. `repeats` compares
   each repeated item with text printed on page N, and each `repeat` cell with
   the cells of the split row on page N. Both use tolerant text similarity in
   any script. They are checks, not hints, because assembly drops the rows,
   items and cell texts they name, so a wrong count or a wrong item loses
   content. A model that keeps its answer after the retries is kept and listed
   (`AC-024`). The one hint, `start_markers`, flags a piece whose start on page
   N+1 begins with one of the survey's start markers, except an `append_rows`
   piece and a piece that names a continuation marker in that start (`AC-055`).
   A hint difference is never sent back and never fails anything. It is listed
   unless the verifier ran and its verdict matched the kept verdict (decision
   7), and the verdict file's `hints` always keep it (`AC-056`). The survey's
   continuation notes are free text, so code compares nothing with them. They
   reach only the model.
6. **A break where a page has no content items gets a verdict without a
   request.** When either page has no item whose role is not `artifact` (a blank
   page, or one holding only page furniture), nothing can continue, since only
   consecutive pages are judged. The step writes a verdict saying nothing
   continues, with `judgment: "no_content"`, all checks passed with 0 attempts,
   no hints, no issues and `verification: null`, and makes no request, with or
   without the verifier. No model judged it, so the verifier has no judgment to
   repeat (`AC-057`). Every other verdict has `judgment: "model"`.
7. **The verifier judges each break a second time without seeing the first
   judgment, and code compares the two.** With `verify_page_breaks` on, after
   the judge's verdict is accepted and written, the verifier sends the judge's
   request again unchanged: the same instructions and user content, with no
   message history, so it never sees the judge's verdict, checks or hints. Its
   answer is a `BreakVerdict`, checked and sent back within `check_retries` by
   the judge's output validator (`AC-057`). The judge's verdict is always the
   kept verdict. Code compares the two on `continues` and, for each piece, its
   end, start, join, text join, cell joins and repeated header rows (**Verdict
   comparison**). Each difference becomes a `verdicts_differ` review issue, a
   match adds none, and no third request settles a difference (`AC-058`). The
   verdict file saves the verifier's verdict, its attempts and checks, and the
   differences (`AC-059`). A verifier's verdict that still fails a check after
   its retries is compared as it is. Its check failures are saved and not
   listed, since assembly never uses that verdict, while any difference it gives
   is listed. The verifier's request runs after the judge's in the same break
   task, so it reads the request from the provider's cache. Its effort, output
   tokens, timeout and check retries are the step's, and the ledger names its
   agent `verifier`.
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
   reused as it is when it is valid, its fingerprint matches, `overwrite` is
   off, and it is a `no_content` verdict, holds a verification, or the step's
   verifier is off (`AC-035`). A valid, matching file with `judgment: "model"`
   and no verification, while the verifier is on and `overwrite` is off, keeps
   its judge's verdict, checks and hints without a request, and only the
   verifier's request is made (`AC-060`). No verifier switch is in the
   fingerprint, as for the other steps. A damaged file gives the
   `damaged_output` warning and the break is judged again (`AC-037`). Settings
   of page-break verification are in no survey or page fingerprint, so changing
   them reruns neither.
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
    judges only the breaks without a reusable verdict (`AC-038`). The judge's
    verdict is written before the verifier's request, so when that request
    fails, the next run with the verifier on keeps the judge's verdict and asks
    only the verifier.
14. **The report shows each break beside its two pages.** A new section, after
    the pages, has one card per verdict: both page images (the report's existing
    `report/pages/<NNNN>.jpg`, no new image files) with the items and containers
    the verdict names drawn on them, and beside them whether content continues,
    each piece with its join rule, text join or cell joins, repeated header
    rows, repeated items and markers, the continuing containers, the reason,
    whether the verifier's verdict matched, with each difference when it did
    not, or that no verifier ran (or that no request was made, for a
    `no_content` verdict), and the break's review issues. Each review issue
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
- `AC-052`: decision 4; **Verdict contract** (`new_entry` row), **Checks and
  hints** (`joins`), **Judge request** (joins rule).
- `AC-014`: decision 4; **Verdict contract** (`text_join`, `cell_joins`).
- `AC-053`: decision 4; **Verdict contract** (`repeat` in `cell_joins`),
  **Checks and hints** (`joins`, `repeats`), **Judge request** (text joins
  rule).
- `AC-054`: decision 4; **Judge request** (unfinished-text rule).
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
- `AC-055`: decisions 2 and 5; **Judge request** (hints), **Checks and hints**
  (`start_markers` and its exceptions).
- `AC-056`: decision 5; **Review issues**, **Test seams**.
- `AC-027`: decisions 7 and 11; **Verdict file** (`verification: null`).
- `AC-028`: decision 11; **Settings**.
- `AC-057`: decision 7; **Verifier request**, **Verdict application**.
- `AC-058`: decision 7; **Verdict comparison**, **Review issues**.
- `AC-059`: decision 7; **Verdict file** (`verification`).
- `AC-031`: decision 12; **Review issues**, **Summary and log lines**.
- `AC-032`: decision 12; **`cost.jsonl`**.
- `AC-033`: decision 10; **Cost estimate**.
- `AC-034`: every request goes through its agent's `LedgerModel` wrapper, which
  reserves its bound in the run's `SpendGuard` before sending, so concurrent
  requests are covered as page extraction's are; **`cost.jsonl`**.
- `AC-035`: decision 9; **Verdict inputs and reuse**.
- `AC-060`: decisions 9 and 13; **Verdict inputs and reuse**, **Verdict
  application**, **Cost estimate** (`judge`).
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
- `AC-061`, `AC-062`: No architectural impact — the user's review of real runs
  with Anthropic models after the build, with the default settings and with the
  step's verifier on. The verdict file, review list and report fields they rely
  on are covered under `AC-011` to `AC-039` and `AC-052` to `AC-060`.

## Components

- **Settings** (`config/schemas.py`, `providers/profiles.py`):
  `PageBreaksConfig`, `AdvancedConfig.page_breaks`, `Config.page_breaks_model`,
  `Config.verify_page_breaks`, `DEFAULT_PAGE_BREAKS_MODEL`.
- **Page-break verification** (`verifying/`):
  - `schemas.py`: the verdict, the verifier's record (`BreakVerification`), the
    verdict file and its parts.
  - `prompts.py`: `PROMPT_VERSION = 1` and the break request's prompts, which
    the judge and the verifier both send.
  - `validators.py`: `CHECKS`, `HINTS`, `run_checks`, `compare_with_hints`,
    `compare_verdicts`, `retry_message`, and the helpers that turn failures and
    differences into check results, hint results and review issues.
  - `agents.py`: the one agent factory both agents use, with its output
    validator.
  - `llm.py`: `JUDGE` and `VERIFIER` agent names, the step's `StepModel`, the
    per-break input, one function that sends the break's request for either
    agent, and the error mapping.
  - `verification.py`: current page files with their hashes, break inputs and
    fingerprints, `plan_breaks`, `verify_breaks` (the concurrent tasks),
    `break_file_path`, `BREAKS_FOLDER_NAME`, and request sizes for the estimate.
- **Review** (`review.py`): `page_breaks` in `StepName`, `BreakCheckName`,
  `BreakHintName` and the `verdicts_differ` issue name, all in `IssueName`. The
  `verifier` issue name stays the survey's and page extraction's only.
- **Errors** (`errors.py`): `PageBreakError`, warning code `missing_page_files`.
- **Versions** (`schema_versions.py`): `BREAK_SCHEMA_VERSION = "1.0"`.
- **Costs and providers** (`costs/budget.py`, `costs/schemas.py`,
  `providers/ledger_model.py`): `estimate_page_breaks`, `BreakRequestSize`,
  `StepEstimate.breaks`, the typical-token constant, ledger lines for breaks.
- **Runner** (`pipeline/runner.py`, `pipeline/schemas.py`): the step, the run
  flow and pauses, the single estimate, `BreakCounts`, `StepRecord.breaks`,
  `RunResult.breaks`, the review list, `load_run`.
- **Python API and CLI** (`api.py`, `__init__.py`, `cli.py`): `verify_breaks`,
  `averify_breaks`, `BreakFile` and `PageBreakError` exported; the CLI gains no
  option.
- **Report** (`report/html.py`, its stylesheet): the page-breaks section.
- **Test tooling** (`tests/fixtures/mock_providers.py`, canned break answers,
  `scripts/smoke_installed_wheel.py`): answering break requests in the order
  they arrive and running the step from the wheel.
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

`BreakVerdict`, the judge's and the verifier's answer, and the verdict a verdict
file keeps. Plain types, enums, lists and objects only, with no patterns or
bounds, so it fits prompted output on Anthropic and native output on OpenAI.
Fields in alphabetical order, as pydelity's other models:

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
  cell above it on page N (`space`, `no_space` or `dehyphenate`), `repeat` when
  both cells have text and the later cell only repeats the earlier cell's text,
  so that assembly keeps that text once, or `null` when either cell has no text
  to join. `null` for every other join.
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

`TextJoin` is `space`, `no_space`, `dehyphenate`, `newline` or `repeat`.
`repeat` is for `cell_joins` only and `newline` never goes there. One enum
serves both fields so that a value in the wrong field fails the `joins` check,
which is kept and listed after the retries, rather than the answer format, which
stops the run at the last attempt.

Join rules (enforced by the `joins` check):

| Join              | Earlier end                                                    | Later start                                | Text join                                                                                                   | Other fields                                           |
| ----------------- | -------------------------------------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `continue_text`   | text item, or code item                                        | same kind as the earlier end               | text: `space`, `no_space`, `dehyphenate`; code: `newline`                                                   | entries, cell joins, header rows `null`                |
| `continue_entry`  | last entry of a list item, or a text item                      | first entry of a list item, or a text item | `space`, `no_space`, `dehyphenate`                                                                          | at least one entry set; cell joins, header rows `null` |
| `new_entry`       | list item, or a text item (the list's part on page N, as text) | list item                                  | `null`                                                                                                      | entries, cell joins, header rows `null`                |
| `append_rows`     | table item                                                     | table item                                 | `null`                                                                                                      | header rows set, from 0 to the later table's rows      |
| `merge_split_row` | table item with at least one row                               | table item                                 | `null`; `cell_joins` one per cell of the merged row: `space`, `no_space`, `dehyphenate`, `repeat` or `null` | header rows set, below the later table's rows          |

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
- `verdict: BreakVerdict` — the kept verdict, always the judge's.
- `verification: BreakVerification | None` — the verifier's second judgment:
  `attempts` (1 plus the retries it used), `checks` (each check's result on the
  verifier's verdict, in `CHECKS` order), `differences` (`list[CheckFailure]`
  from **Verdict comparison**, empty when the two verdicts match) and `verdict`
  (the verifier's `BreakVerdict` as accepted); `null` when no verifier ran
  (`AC-027`, `AC-059`). `BreakVerifierVerdict`, `BreakProblem` and
  `BreakProblemCategory` are removed.

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
quiet. A break whose verdict file keeps the judge's verdict and needs only the
verifier's request counts among those to judge, is marked as needing no judge
request, and gets an info line saying that the verifier judges it now and the
judge's verdict is kept.

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
     newline for code. `new_entry` may start from a text item when page
     extraction read the list's part on page N as text (`AC-052`). A cell join
     is `repeat` when the later cell only repeats the earlier cell's text, such
     as a row label printed again with a continuation marker, and never a text
     join that would print that text twice (`AC-053`).
  6. When text continues: text or a list entry continues only when the break
     cuts off a sentence, paragraph or entry, so that the text itself is
     unfinished at the end of page N. A paragraph that breaks between two
     sentences, with no new paragraph starting page N+1, is unfinished. A
     complete entry followed by an entry with its own new number is a new entry
     (`new_entry`), not a continued one (`AC-054`). The rule names no language
     and no marker style.
  7. Tables: the same table continues when its column structure matches, nothing
     outside the grid announces a new table between the start of page N+1 and
     the table, and no header redefines the columns; a border or closed box
     around each page's part is no sign of a new table; a split row is a row
     whose cells are cut by the break and resume in the first row after any
     repeated header rows.
  8. Repeated items, continuation markers and containers, as defined.
  9. Nothing continuing is a valid answer; decide from what the pages show.
  10. The answer is checked by code for consistency, and the model is told what
      to fix if a check fails.
  11. Hints: the survey's continuation notes and start markers (each start
      marker's text and description), which describe the whole PDF, can be
      wrong, and are overridden by the pages; `none` when the survey gave none.
  12. `advanced.page_breaks.instructions` under its own heading, when set.
- The instructions say nothing about a second judgment, so the judge's and the
  verifier's requests are the same.
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
  `extracting/llm.py` `_model_settings`. Its log lines name the agent, so the
  verifier's agent comes from the same factory.

### Verifier request

- The judge's request, sent again unchanged: the same instructions and user
  content from the same prompt function, with no message history. It never
  carries the judge's verdict, its check failures or its hint differences, so
  the verifier judges the break without seeing the first judgment (`AC-057`).
  The verifier-only prompt (`verify_break`, `_REVIEW`, `_VERDICT`) and the
  `review_text` part are removed.
- It is sent in the same break task once the judge's verdict is accepted and
  written, so it reads the request from the provider's cache, and the stand-in's
  arrival order for a break is fixed (**Test seams**).
- Agent: the judge's factory, output validator, `check_retries` and settings,
  with a ledger wrapper for agent `verifier`. Its answer is a `BreakVerdict`,
  and a verdict that still fails a check at the last attempt is accepted as it
  is. Errors name the agent `verifier`, as now.

### Verdict application

1. The judge's verdict. When the break's verdict file keeps its judge's verdict
   (decision 9), take the file's `verdict`, `checks` and `hints`. Otherwise send
   the judge's request with its checks and retries. Its accepted verdict is the
   kept verdict, `checks` are its results with the judge's attempts, and `hints`
   are `compare_with_hints` on it. Write the verdict file with
   `verification: null` and its issues.
2. With `verify_page_breaks` on, the verifier's request. `verification` holds
   its verdict as accepted, its attempts, its check results, and
   `compare_verdicts(kept, verifier's)`.
3. `issues` (**Review issues**), the verdict file rewritten atomically, and the
   break's log line, once per break.

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
   texts joined in order. Each `repeat` value in a `merge_split_row` piece's
   `cell_joins` names a merged-row cell whose text is not empty and matches the
   text of some cell in page N's split row (the last row of the earlier table).
   Any cell of that row counts, so cell spans that differ between the pages do
   not matter.
8. `markers` — each marker's text is in the text of the item or cell that
   carries it.

Text matching in checks and hints uses `comparison_form` (NFKC, case-folded,
letters, marks and numbers only), so it holds in any script. Two texts match
when their comparison forms are equal or both have at least 3 characters and the
Dice coefficient of their `trigrams` is at least 0.8; `repeats` also accepts
either form containing the other, so a repeated heading or cell with a marker
added matches the original; `markers` requires the marker's form to be contained
in the carrier's. Both empty counts as a match for header rows.

Hint (`BreakHintName`), never sent back:

- `start_markers` — a piece whose start on page N+1 (the start item's text, the
  start entry's text, or for a table the cell texts of its first row after the
  repeated header rows) begins, in comparison form, with the comparison form of
  one of the survey's start markers. A marker whose comparison form is empty is
  skipped. Two kinds of piece are skipped (`AC-055`): an `append_rows` piece,
  and a piece that names a continuation marker in its start, meaning one of its
  `markers` has the start item as its `item` and, for a table, the row the start
  text comes from as its `row`. These exceptions read only the verdict's join
  and markers. The difference message says which marker the start begins with
  and that the verdict joins it to page N. It never tells the model what to
  change, and no request carries it.

Check failure messages may say what to fix. Every retry message is built from
`run_checks` failures only.

### Verdict comparison

`compare_verdicts(kept, verifier)` in `validators.py` compares the kept verdict
with the verifier's and returns `list[CheckFailure]`, one per difference. Each
difference's message starts with `verdicts_differ` and names both verdicts'
values and the items, its `page_index` is the break's earlier page, and its
`details` hold `field`, the `kept` and `verifier` values, and `item`, `entry`
and `cell` where they apply.

1. `continues`. When the two verdicts differ on it, that is the one difference
   (`field: "continues"`), and its message names the pieces of the verdict that
   continues. When both say nothing continues, nothing else is compared.
2. Pairing, when both say content continues. For each kept piece in order, the
   first unpaired verifier piece with the same end (`earlier_item` and
   `earlier_entry`). Then, for each kept piece still unpaired, the first
   unpaired verifier piece with the same start (`later_item` and `later_entry`).
   Each piece left unpaired on either side is one difference (`field: "piece"`),
   the kept verdict's first.
3. Per pair, in the kept verdict's order: the end (`end`), the start (`start`)
   and the join (`join`). When the joins are the same, also `text_join`,
   `cell_joins` (one difference per differing cell, or one for the whole list
   when the lengths differ) and `repeated_header_rows`. When the joins differ,
   the join is the pair's only further difference, since the other fields follow
   from the join.

`item` and `entry` are the kept piece's earlier end, or the verifier piece's
when only the verifier names that piece, so a difference's review issue points
at the piece. For a `continues` difference they are the first piece's of the
verdict that continues, or `null` when it names none. Repeated items, markers,
containers and `reason` are not compared (`AC-058`). The verdicts match when the
list is empty.

### Review issues

A break's `issues`, in this order: each check still failing on the kept verdict;
each hint difference, unless a verifier ran and its verdict matched the kept
verdict (`AC-056`); each difference from **Verdict comparison**, with
`check: "verdicts_differ"` and the difference's `details` (`AC-058`). The
verifier's verdict's own check failures are saved in `verification.checks` and
not listed. Every issue has `step: "page_breaks"`, `page_index` = the break's
earlier page, `item_id` = the item the failure or difference names when it is on
either page, else `null`, and a message that names both pages, such as
`pages 4 and 5: ...`. Page-break verification gives no `verifier` issue.
`run.json` `review` lists the survey's issues, then each selected page's, then
each break's in break order. `ReviewIssue.page_index`'s docstring says that for
page-break verification it is the break's earlier page, and the `details`
docstrings of `ReviewIssue` and `CheckFailure` describe a `verdicts_differ`
issue's keys.

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
  `Break after page 4 (pages 4 and 5): continues, 2 pieces, 0 review issues, verifier agrees; $0.06 for 2 requests`
  (or `nothing continues`, `no request, page 5 has no content items`,
  `verifier differs in 2 places`, `no verifier`).
- Estimate lines name steps with a title (`Survey`, `Extraction`,
  `Page-break verification`) instead of capitalizing the step name, and say
  `7 breaks` where the extraction line says pages.

### Cost estimate

- `BreakRequestSize`: `chars` (instructions, both page texts and the verdict
  format, without images, the request both agents send) and `judge` (whether the
  break needs the judge's request, `False` when its verdict file keeps the
  judge's verdict and only the verifier's request is needed).
- `estimate_page_breaks(config, breaks)`: per break, input =
  `ceil(chars / PROMPT_CHARS_PER_TOKEN) + 2 * image_tokens` of the step's
  model's profile. Expected: one judge request when `judge` is set and one
  verifier request when the verifier is on, each with
  `TYPICAL_BREAK_OUTPUT_TOKENS = 4_000` of output.
  `TYPICAL_BREAK_VERDICT_OUTPUT_TOKENS` is removed. Maximum: every attempt of
  each agent that runs with `max_output_tokens`, earlier answers added to the
  input, as `estimate_extraction`. `requests_max` sums, over the breaks, the
  agents that run times the attempts.
  `StepEstimate(name="page_breaks", breaks=<n>, pages=None, verifier=...)`;
  `reused` when no break is to be judged. `no_content` breaks cost nothing and
  are not counted.
- `StepEstimate.breaks: int | None` (required): breaks the step would judge, for
  page-break verification; `None` for the other steps.
- Sizes: a break whose page files are both current and unchanged by this run is
  measured by building its prompts. A break with a page that this run will
  extract, or before the survey exists, uses an allowance: the instructions
  measured from the survey when it exists, else one fixed allowance, plus for
  each page a fixed allowance plus twice its text-layer characters. The
  verifier's separate allowance goes. Developer rounds the allowance constants
  up from measured requests on the test PDFs, as page extraction's were.
- Which breaks an estimate covers (in the run's single estimate, in `estimate()`
  and in `aestimate()`):
  - none when the PDF has one page, or the run will pause before the step (a new
    survey or a page extraction that will extract a page, with `pause` on), or a
    page will lack a current page file after page extraction;
  - with the survey reused: every break whose verdict would not be reused as it
    is, where a break touching a page to extract is always judged, and a break
    whose verdict file keeps the judge's verdict is priced for the verifier
    only;
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
  cards draw them), and the details of decision 14. The card's verifier line
  says that the verifier's verdict matches, or lists each difference's message,
  or that no verifier ran. `_STEP_TITLES` gains
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

- The judge's and the verifier's requests are the same, and both contain
  `Page break between page indexes <i> and <i+1>`. No page-break request
  contains `Page index <i> (`, `The extraction to review:` or
  `The survey answer to review:`, so the stand-in routes them apart from the
  other steps' requests.
- The stand-in cannot tell the verifier's request from the judge's, so it
  answers each break's requests in the order they arrive, retries included, from
  a list of answers for the break's earlier page index, the last one repeating,
  whatever order different breaks' requests interleave in. Within a break the
  verifier's request starts only after the judge's verdict is accepted, so that
  order is fixed. The ledger's `agent` says which agent sent each request. The
  canned break answers (`tests/fixtures/break_answers/`) and the stand-in's
  `break_answers` argument become one answer or a list per break, with no agent
  key.
- No request carries a hint difference or another verdict. Every retry message
  is built from `run_checks` failures only.
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
the rules of decision 5, and the verifier's comparison from **Verdict
comparison**, in place of the verifier issue it describes now), and picks up
`advanced.page_breaks`, `verify_breaks`, `averify_breaks`, `StepRecord.breaks`,
`RunResult.breaks`, `StepEstimate.breaks`, the new ledger docstrings and the new
constants in `costs/budget.py` from the code, so CI's staleness check covers
them. Page names are the user's to approve with the other names.

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
   Per break: a page without content items → `no_content` verdict. Otherwise
   render both upright images and build the request. Unless the verdict file
   keeps the judge's verdict, send the judge's request with checks and retries,
   compute hints and issues, and write the verdict file atomically. With the
   verifier on, send the same request for the verifier, compare, recompute the
   issues and write the file again. Then log the line. Developer may keep a
   page's image until both its breaks have used it. The first failure cancels
   the other tasks and ends the step `failed`.
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
- `AC-052`: a `new_entry` piece from a text item on page N to a list item on
  page N+1 passes `joins`, and one whose start is not a list item fails it.
- `AC-053`: `repeat` passes `joins` in `cell_joins` and fails it in `text_join`.
  A `repeat` cell whose text is empty, or matches no cell of page N's split row,
  fails `repeats`. The instructions say when a cell join is `repeat`.
- `AC-054`: the instructions say that text or a list entry continues only when
  the break leaves it unfinished, that a paragraph broken between two sentences
  with no new paragraph on page N+1 is unfinished, and that a complete entry
  followed by an entry with a new number is a new entry.
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
- `AC-055`: the instructions hold the survey's continuation notes and start
  markers under the hints heading. A piece starting with a start marker gives a
  `start_markers` difference, unless its join is `append_rows` or one of its
  markers is on its start item (and, for a table, on its start row).
- `AC-056`: a hint difference never raises `ModelRetry`, never appears in a
  request or a retry message, and never sets a step or run status. It is in
  `hints` always, and in `issues` unless `verification` is set with no
  differences.
- `AC-027`: with default settings, no request goes through a page-break
  `verifier` wrapper, no ledger line has `step: "page_breaks"` and
  `agent: "verifier"`, and every verdict file has `verification: null`.
- `AC-028`: `verify` (file, `--verify`/`-vf`, `verify=True`) turns on
  `verify_page_breaks` when the override is `null`; the override's `true` or
  `false` wins; `Config.verify_page_breaks` exists.
- `AC-057`: with the verifier on, each break with `judgment: "model"` gets one
  verifier request whose instructions and user content equal the judge's, with
  no message history, and a verifier verdict failing a check is sent back within
  `check_retries`.
- `AC-058`: the kept verdict is always the judge's. `compare_verdicts` gives no
  difference for verdicts that agree on every compared field, one `continues`
  difference when only one verdict continues, and one difference per unpaired
  piece and per differing compared field of a pair. Repeated items, markers,
  containers and `reason` give none. Each difference is one `verdicts_differ`
  issue, and no third request is made.
- `AC-059`: when the verifier ran, `verification` holds its verdict, attempts,
  check results and differences.
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
- `AC-060`: with the step's verifier turned on over matching verdict files with
  `verification: null` and `judgment: "model"`, each such break gets one
  verifier request and no judge request, keeps its `verdict`, `checks` and
  `hints`, and its file is rewritten with `verification` set. Changing another
  step's verifier setting re-judges a break only when that step's outputs
  changed a page file's bytes or the survey's continuation fields.
- `AC-037`: verdict files are written atomically; a damaged one gives
  `damaged_output` and is judged again.
- `AC-038`: a failed page-break request after the provider retries, or an
  unusable answer, ends the run `failed` with `ProviderError` or
  `PageBreakError`, the CLI exits 1, verdict files already written stay, and the
  next run judges only breaks without a reusable verdict.
- `AC-039`: the report holds one card per verdict with both page images, the
  named items and containers drawn, every verdict field of decision 14, whether
  the verifier's verdict matched with each difference, or that no verifier ran,
  and links from the break's review issues.
- `AC-042`: the smoke script's runs complete with one verdict and load.
- `AC-044`: the package description names the three steps and the optional
  verifiers.
- `AC-047`: the generated reference pages hold every new setting, function,
  verdict-file field, `run.json` and `cost.jsonl` change, the page-break checks
  and hint, and the verifier's comparison, and CI's staleness check passes.

## Build Plan

The earlier pass built the settings, the step, the run flow, the API, the
estimate, the report, the smoke test and the reference pages (DEV-001 to DEV-011
in the development plan), and they stand except where the steps below change
them. The rework, in dependency order:

1. **Verdict contract and names** (`AC-053`, `AC-058`, `AC-059`). MODIFY
   `src/pydelity/verifying/schemas.py` (`TextJoin` gains `repeat`,
   `BreakVerification` takes its new fields, `BreakVerifierVerdict`,
   `BreakProblem` and `BreakProblemCategory` go, docstrings of `cell_joins`,
   `verdict`, `verification` and `issues`) and `src/pydelity/review.py` (the
   `verdicts_differ` issue name in `IssueName`, the `verifier` name's docstring
   limited to the survey and page extraction, the `details` docstrings). Names
   approved first.
2. **Checks, hint and comparison** (`AC-052`, `AC-053`, `AC-055`, `AC-056`,
   `AC-058`). MODIFY `src/pydelity/verifying/validators.py`: `joins`
   (`new_entry` from a text item, `repeat` only in `cell_joins`), `repeats`
   (`repeat` cells), the `start_markers` exceptions, `compare_verdicts`, and
   `review_issues` with the new hint rule and difference issues in place of
   verifier problems. Depends on 1.
3. **Prompts and requests** (`AC-052` to `AC-054`, `AC-057`). MODIFY
   `src/pydelity/verifying/prompts.py` (the rules for `new_entry`, `repeat` and
   unfinished text, the verifier prompt and `review_text` removed;
   `PROMPT_VERSION` stays 1), `src/pydelity/verifying/agents.py` (one factory
   for both agents) and `src/pydelity/verifying/llm.py` (one function that sends
   the break's request for either agent). Depends on 2.
4. **The step** (`AC-038`, `AC-057` to `AC-060`). MODIFY
   `src/pydelity/verifying/verification.py`: the reuse rule, the verdict file
   written after the judge's verdict and again after the verifier's, the log
   lines, and request sizes with `chars` and `judge`. Depends on 3. This is the
   critical path.
5. **Estimate** (`AC-033`, `AC-060`). MODIFY `src/pydelity/costs/budget.py`
   (`BreakRequestSize`, `estimate_page_breaks`, the removed constant) and the
   call sites in `src/pydelity/pipeline/runner.py` if their arguments change.
   Depends on 4.
6. **Report** (`AC-039`). MODIFY `src/pydelity/report/html.py` (the page-break
   branch of the verifier line). Depends on 4; may go with 5.
7. **Test tooling** (seams for self-checks). MODIFY
   `tests/fixtures/mock_providers.py` (break answers in arrival order, no agent
   key), `tests/fixtures/break_answers/irs_form_1040a_1965_scan.json` and
   `scripts/smoke_installed_wheel.py` (the answer file's new shape). Depends on
   3; goes with 4 so the step can be run against the stand-in. Tests themselves
   are Tester's.
8. **Reference pages** (`AC-047` in code). MODIFY
   `scripts/generate_reference_docs.py` (the page-break checks page's comparison
   section, the verdict file page) and regenerate
   `docs/src/content/docs/reference/` with `just docs-reference`. After 1–6.

New code follows the user styles' module order and keyword-argument order. Tests
are Tester's; the guides, README and `artifacts/next_cycle_inputs.md` are
Documenter's.

## Risks and Follow-up

- Cost: each break sends two whole page images and both pages' items, and each
  page's image is sent for two breaks. The instructions are cached across
  breaks, and within a break the verifier reads the judge's request from the
  cache. The ten real runs before the rework cost about $4.36 with the verifier
  off and $7.92 with it on, for 29 breaks with page extraction of new pages
  included. The verifier now costs about one more judge answer per break. The
  4,000-token typical output is still a guess that the next real runs check.
- Two answers from the same model to the same request share its blind spots. A
  match does not prove a verdict right. The rework rests on C12, where two
  separate judge runs differed at exactly the breaks R-1 to R-4 and nowhere
  else, while the reviewing verifier caught none of them.
- The comparison only flags. A difference stays for a person to settle, and
  assembly follows the kept verdict, the judge's.
- `repeat` lets assembly drop a later cell's text. The `repeats` check matches
  it against any cell of the split row, so it can pass a wrong `repeat` when
  another cell of that row has similar text.
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
  correct joins for review when no verifier runs or the two verdicts differ. Its
  exceptions clear the six CAPS false alarms of C12 (four `append_rows` pieces
  and two pieces with a "(contd)" marker on their start), and a new row that
  starts with a strand label and has no marker is still listed.
- Page extraction can structure two pages differently (a list on one page, text
  on the next; providers differ). `continue_entry` accepts a list entry joined
  to a text item, and `new_entry` a text item on page N, but a table on one page
  and text on the other cannot be joined, and fails `joins` if the model tries.
  A header row that page extraction misread (R-2) can still make a correct
  repeated-header count fail `header_rows`. That is a page extraction fault.
- The unfinished-text rule is a prompt rule only. Code cannot tell a finished
  sentence in any script, so a model that breaks the rule is caught only by the
  verifier's comparison or the user's review.
- With `pause` on, a new PDF takes three runs. With `overwrite` and a narrowed
  `pages`, page-break verification never runs (decision 8).
- Prompted output on Anthropic has no grammar, so a verdict that is not valid
  JSON costs a retry and, on the last attempt, stops the run.
- Left to later steps for `artifacts/next_cycle_inputs.md`: continuation across
  pages that do not follow each other; "continued on the next page" notes on
  page N, which the verdict does not name; structure tags as evidence (option
  A); whether a `no_content` page breaks a unit that continues around it; how
  assembly keeps a `repeat` cell's text once and drops its continuation marker;
  and what assembly does at a break whose two verdicts differ.
- Verdict files from the earlier 0.3.0 builds, such as the user's real-run
  folders, are not migrated. `PROMPT_VERSION` and `BREAK_SCHEMA_VERSION` stay at
  1 and `"1.0"`, as the scope says. A file whose verifier ran has the old
  `verification` shape, so it does not load: a run warns `damaged_output` and
  judges the break again, and `load()` raises `OutputError` on its folder. A
  file without a verifier still loads and its fingerprint still matches, so it
  is reused with the older prompt's verdict. Real runs after the rework use new
  output folders or `--overwrite`, as the scope says.
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
  assembly joins where the verdict says, and the verifier judges every break or
  none.
- A verifier that reviews and corrects the judge's verdict, as page extraction's
  does (the earlier design): replaced at the user's request. In C12 it passed
  all 29 verdicts and corrected none, while two separate judge runs differed at
  exactly the breaks R-1 to R-4. A third request to choose between two differing
  verdicts is a scope non-goal.
- A verifier request worded differently from the judge's, or told that it is a
  second judgment: rejected. Any change to the request changes the judgment
  being compared, and the evidence in C12 is for the same request sent twice.
- The verifier's request sent at the same time as the judge's: rejected. It
  would shorten a break's wait but lose the cache read, and the stand-in's
  arrival order within a break would no longer be fixed. Breaks already run
  `concurrent_breaks` at a time.
- A `CellJoin` enum without `newline`, apart from `TextJoin`: rejected. On
  Anthropic's prompted output a value outside the enum fails the answer format,
  which stops the run at the last attempt, while a `joins` failure is kept and
  listed.
- Listing the verifier's own check failures as review issues: rejected. Assembly
  never uses its verdict, and its differences already flag the break.
- Comparing repeated items, markers and containers: the scope leaves them out.
- One verdict file write per break, after the verifier: rejected. Writing the
  judge's verdict first lets a failed verifier request keep it, and the same
  code then serves a break whose file already holds the judge's verdict
  (`AC-060`).
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

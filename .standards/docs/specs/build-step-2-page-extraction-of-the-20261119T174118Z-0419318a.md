<!-- STANDARDS
Artifact: ARCHITECTURE
Cycle: build-step-2-page-extraction-of-the-20261119T174118Z-0419318a
-->

# Technical Design: page extraction (step 2) and release 0.2.0

## Context

- Scope:
  `.standards/docs/scope/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a.md`
  (`AC-001` to `AC-058`; `AC-015` is retired). Target maturity is Level 3.
- Baseline: pydelity 0.1.1, the survey only (`.standards/CONTEXT.md`). The
  survey's design
  (`git show 83743ef:.standards/docs/specs/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c.md`,
  decisions 1–15) stays in force except where a decision below replaces part of
  it, which the decision says.
- Inputs: `artifacts/next_cycle_inputs.md` (newer) and
  `artifacts/design_brief.md` ("Step 2 (page extraction) design points", "Known
  defects in the source code to design out"). KGForEdGlobal's
  `backend/src/kgfeg/page_ir_extraction/` is the port source (read-only);
  **Reuse from KGForEdGlobal** below says what is ported.
- Constraints that shape this design: no core logic, prompt, field or default
  may assume a document type, language or writing direction; the model's reading
  wins over measured facts, and code may only send an answer back with the
  difference before the model's last answer is kept; each check sits where it
  can be enforced (Pydantic, then `extracting/validators.py`, then the verifier
  model); no per-model limits; no default `max_cost`; an async twin for every
  function that measures, estimates or runs; internal versions are not raised
  and step 2's versions start at 1; no backwards compatibility with 0.1.x (no
  aliases, deprecation paths, migrations, or defaults kept only so 0.1.x files
  load); names and defaults the user chose (`--no-pause`/`-np`; page extraction
  on `anthropic:claude-opus-5-5` at effort `high`); instructions per step under
  `advanced:`, replacing the top-level setting (`AC-059` to `AC-061`).
- Real runs during development (2026-11-19) changed two decisions. Anthropic
  refused the page answer as native structured output (HTTP 400, "The compiled
  grammar is too large"); its structured-outputs guide caps fields with union
  types, nullable ones included, at 16 per request, and `PageAnswer` and
  `VerifierVerdict` hold 18 and 20. OpenAI's native structured output accepted
  both. On the Arabic test page (OpenAI), the extraction copied the PDF's stored
  text, broken ligatures and swapped letters included, and every text check
  passed. Decisions 20 and 21 answer these.
- File and folder names are the user's to approve before the build step that
  creates them. `src/pydelity/extracting/` with `agents.py`, `llm.py`,
  `prompts.py`, `validators.py` and `schemas.py` is fixed by scope. Every other
  new path in this design is a `CANDIDATE`, and every output file or folder name
  (`pages/`, `figures/`) is a proposal the user confirms in the development
  plan.
- No project references exist under `.standards/project-references/`.

## Decision

1. **Step 2 follows the survey's patterns.** Code lives in
   `src/pydelity/extracting/` with the survey's split: `schemas.py` (the model's
   answer, the verifier's verdict, the page file), `prompts.py`
   (`PROMPT_VERSION = 1`, two `PromptPair` functions), `validators.py` (the
   checks and the text comparison), `agents.py` (the extractor and verifier
   agents, each with an output validator that raises `ModelRetry`) and `llm.py`
   (request content, agent runs, error mapping). Three more modules are
   candidates: the step itself (plan, reuse, concurrency, writing; the analogue
   of `surveying/survey.py`), rendering and coordinates, and reading the text
   layer. The step's name everywhere (`run.json`, `cost.jsonl`, review issues,
   estimates) is `extraction`.
2. **Each step has its own model, resolved from three places.** `model` becomes
   optional (`None` by default). The survey uses `model`, else
   `anthropic:claude-opus-5-5`. Page extraction uses
   `advanced.extraction.model`, else `model`, else its own default,
   `anthropic:claude-opus-5-5` at effort `high` (the user's choice). The two
   defaults are separate constants so either can change alone. The resolved
   setting, never `config.model`, goes to `build_model`, `LedgerModel`, pricing,
   the estimate and fingerprints. `Config.model_choice` is removed; callers name
   the step.
3. **Pages are selected with `pages`, and runs pause after a new survey.**
   `pages` (`--pages`, `-p`) takes 1-based page numbers and ranges, such as
   `1-5,8`; unset means every page. Its syntax is checked with the other
   settings, and page numbers past the PDF are checked right after the PDF is
   opened, both as `ConfigError` naming `pages`, before anything is written or
   sent. `pause` (default `true`; `--no-pause`, `-np`) makes `run()` and the CLI
   stop after a step that wrote new output in this run, before the next step.
   With one later step, the only pause is after a new survey. `extract()` never
   pauses, because its caller asked for page extraction.
4. **One request per page, from an upright image rendered by pydelity.** Page
   extraction never sends the PDF or uses the survey's upload. For each selected
   page, pydelity renders the displayed page turned clockwise by the profile's
   rotation for that page, so content is upright, as a JPEG (quality 90). The
   image is as large as the providers use without shrinking it, from their
   documented limits, not a fixed size: the largest that fits Anthropic's
   high-resolution limits (at most 2,576 px on the long edge and at most 4,784
   tiles of 28 x 28 px), within OpenAI's `detail: "original"` limits, and never
   above 300 DPI. That is about 2,180 px on the long edge (about 200 DPI) for a
   Letter or A4 page. OpenAI requests send the same image with
   `detail: "original"`, so OpenAI does not shrink it to `high`'s 2,048 px and
   2,500 patches. Each extractor and verifier request carries that one image
   (`AC-058`); several pages run at once as separate requests. The limits are
   provider-level facts in `providers/profiles.py`; the size rule and the format
   are not settings.
5. **The model gives boxes on a 0–1000 grid of the upright image.** Integer
   `[x0, y0, x1, y1]` in thousandths of the image's width and height from its
   top left. The grid is independent of any resizing a provider does and costs
   few output tokens. Python maps each box back to points on the displayed page
   (origin top left, the survey's coordinate system) with the rotation table
   under **Rendering and coordinates**, clamped to the page and rounded to 0.01.
6. **One page file per page holds everything about that page.**
   `pages/<NNNN>.json` (`NNNN` is the 0-based page index, as in
   `report/pages/<NNNN>.jpg`) holds the items, the containers, the check
   results, the review issues, the verifier's verdict and the fingerprint.
   Figure crops are PNG files in `figures/`, written before the page file that
   names them. One atomic write per page keeps resume simple.
7. **Items are flat records with Python-assigned IDs.** The model names each
   item with a short `ref` of its own; `caption_of` and `container` refer to
   refs. Python assigns IDs from reading-order position: item `p<NNNN>-<nnn>`
   (such as `p0003-007`), list entry `<item id>.<k>`, container `p<NNNN>-c<nn>`.
   The same answer always gives the same IDs (`AC-008`). Every item has the same
   fields, with the per-kind fields `null` when unused. A flat schema keeps
   provider structured-output schemas simple; the `content` check enforces which
   fields go with which kind. The `kind` and `role` lists stay as 0.1.0 defined
   them. Each item with text carries a BCP-47 `language`, so a consumer such as
   KGForEdGlobal needs no adapter guess. Containers are records beside the
   items, not a kind or role, and carry no continuity hints.
8. **Pydantic checks shape; validators check meaning.** The answer models check
   types and enum values only. Anything an answer could get partly wrong (box
   order, refs, labels, spans, text) is a check in `validators.py`, because a
   Pydantic failure on the last allowed attempt fails the page and stops the
   run, while a failed check keeps the answer and lists the problem for review.
   The verdict's own invariants are Pydantic validators, since any answer can
   meet them. The retry rule is the survey's (decision 5 of its design): while
   check retries remain, any failed check raises `ModelRetry` with every
   failure; the last allowed answer is kept and each check still failing becomes
   a review issue.
9. **Text is compared as character trigrams, never words.** On pages whose
   measured text quality is `good`, Python compares the items' text with the
   page's text layer after Unicode normalization, using character trigrams that
   ignore spaces, so scripts written without spaces work the same as others.
   Text-layer lines with too little coverage in the answer are dropped text;
   answer lines with too little coverage in the text layer are added text. Both
   are checks and go back to the model within the check retries; the retry
   message says it may keep its reading when the text is not visible on the page
   or was read from an image, and that the PDF's stored text can be wrong, so
   the page image decides (decision 21).
10. **A verifier reviews every page and may replace it.** After the extractor's
    answer is accepted, a verifier request with the same image, the same page
    context, the answer and its remaining check failures returns a verdict:
    passed, or problems plus a full corrected answer. The correction runs
    through every code check in the verifier's output validator, with the same
    retry rule. A correction that passes every check replaces the extraction; a
    rejected or missing correction keeps the extraction, and each problem the
    verifier named becomes a review issue. No loop back to the extractor and no
    second verification. The verdict is saved in the page file.
11. **Pages run concurrently up to a limit; PyMuPDF runs one call at a time.**
    `advanced.extraction.concurrent_pages` (1–32, default 8) bounds the page
    tasks in flight with a semaphore; a page task covers rendering, extraction,
    verification, crops and the write. PyMuPDF is not safe across threads, so
    every PyMuPDF call in step 2 runs on one shared worker thread, one at a
    time. Page tasks run in an `asyncio.TaskGroup`: when one page fails, the
    others are canceled, no new page starts, and the first error ends the run.
    Pages already written stay valid for the next run.
12. **`max_cost` counts images, requests in flight, and the expected cost at
    plan time.** This replaces the plan-time rule of the survey's decision 11.
    (a) A request's upper bound counts each image at the provider profile's
    per-image token figure. (b) `SpendGuard` keeps a reservation for each
    request it lets through and releases it when the request's ledger line is
    written or the request ends without one; a request passes when recorded
    spend plus reservations plus its own bound stays within `max_cost`, so
    concurrent requests cannot together go over without the warning (`AC-030`).
    (c) The plan-time check compares recorded spend plus the run's expected cost
    with `max_cost`, not the maximum: per-page maximums assume every retry with
    the longest answer and would bring the question on nearly every run, while
    the reservations still stop every request that could go over. The warning,
    the single question per run, `--yes`, `allow_over_max_cost` and
    `BudgetExceededError` are unchanged.
13. **Each page file is reused while its own inputs are unchanged.** A page
    file's fingerprint covers only what that page's requests are made from: the
    PDF, the page, its resolved page context (labels, languages, page
    extraction's instructions, this page's direction and rotation, its repeated
    lines and their artifact classification, its measured page facts and form
    fields), the resolved model, the step's settings that change answers,
    `PROMPT_VERSION`, the rendering constants and the page file's schema
    version. So a profile change reruns only the pages it touches, a new
    selection extracts only new pages, `overwrite` reruns every selected page,
    and no extraction setting reruns the survey.
14. **Review issues and `run.json` become multi-step.** One shared `ReviewIssue`
    model, with `step` and an optional `item_id`, replaces the survey-only one
    and moves out of `surveying/schemas.py` to a module both steps import. The
    runner records one `StepRecord` per step, attributes each warning to the
    step that was running when it was issued (a context variable that `warn`
    reads), and gains run status `paused`.
15. **The report draws the items on the page images it already renders.** Each
    extracted page shows its report image with every item's box numbered in
    reading order and every container drawn, beside a list of the items. A
    review issue about an item links to that item's box.
16. **Reuse from KGForEdGlobal.** Port, rewriting for neutrality and for
    PydanticAI 2.x and PyMuPDF 2.x:
    - the extraction and validation prompts' generic sections (image as the
      source of truth, verbatim text, every item has a kind, scan every margin,
      drawn rules are not content, box rules, heading versus caption by role,
      content rules per kind, tables, lists, figures, user instructions appended
      last under a neutral heading);
    - the validator's audit stance, checklist, severity guide and full-answer
      correction;
    - the duplicate-box check, the table occupancy simulation (HTML-style spans,
      covered cells omitted; it also measures row width with rowspans, which
      KGForEdGlobal's width counts missed) and the "table has some text" check;
    - prompted output for every Anthropic agent (its `wrap_output_type`;
      decision 20).

    Not ported: text-layer hints and their gate (decision 21), every
    left-to-right rule, the English word lists and patterns, the
    full-page-figure checks, the letter-run tokenizer and word-count correction
    guard (replaced by decision 9 run on the correction), boundary and
    continuity marks, `text_en`, `figure_kind`, `local_code`, the footnote
    position check, the table-collapse heuristics (left to the verifier),
    `find_tables` hints, per-attempt artifact files, fixed DPI, file-existence
    resume and non-atomic writes.

17. **0.1.0's follow-ups are fixed where they live.** None raises
    `PROBE_VERSION`. Details under **Follow-up fixes**.
18. **Each step has its own instructions, under `advanced:`.**
    `advanced.survey.instructions` and `advanced.extraction.instructions`
    replace the top-level `instructions` setting and `--instructions`/`-i`, with
    no alias. Each goes only into its own step's instructions to the model (the
    system message, sent with every request), last, under a heading that says
    they come from the user and add to pydelity's rules without replacing them.
    Page extraction's go to the extractor and the verifier alike. A step without
    instructions sends no heading. The profile no longer carries instructions
    (`Profile.user_instructions` is removed), so the survey's instructions
    cannot reach later steps. Each step's fingerprint includes only its own
    instructions.
19. **No backwards compatibility with 0.1.x.** Changed models get new required
    fields (nullable where a value can be absent), with no defaults kept for
    0.1.x files; removed settings and options are simply unknown. A 0.1.x
    `pdf_survey.json` or `pdf_facts.json` that no longer validates is treated as
    damaged and made again; a 0.1.x `cost.jsonl` with more than one line stops
    the run with `OutputError` naming the file, as any damaged ledger does.
20. **Every step uses prompted output on Anthropic.** Anthropic compiles a
    native output schema into a grammar with limits the flat page answer exceeds
    (Context), and those limits can change. So every agent on Anthropic (the
    survey's, the extractor and the verifier) asks for `PromptedOutput`, as
    KGForEdGlobal does for Anthropic; the survey's answer fits today's limits,
    but by the user's choice it does not depend on them. Every agent on OpenAI
    keeps `NativeOutput`, which accepted both page schemas in the real run. This
    replaces the survey design's rule (its decision 3) of native output wherever
    the model supports it. `ProviderProfile` gains `output_mode` (Anthropic
    `prompted`, OpenAI `native`); `output_mode` in `providers/factory.py`
    returns `prompted` when the model's provider profile says so or the model
    has no JSON-schema output, otherwise `native`, and `structured_output` wraps
    the answer type to match. The runner's "Model ready" log line names the
    mode. Under prompted output PydanticAI adds the answer's JSON schema to the
    instructions, so the schema is part of the instructions Anthropic caches,
    and both steps' estimates already count it (`AC-029`). An answer that is not
    JSON or does not match the schema is sent back by PydanticAI as an output
    retry within the same `check_retries` budget, and on the last allowed
    attempt fails the page or the survey, as decision 8 and the survey's
    decision 5 say. No answer or verdict schema changes, and no internal version
    is raised: a saved survey stays reusable, since its answer means the same
    whichever mode produced it.
21. **The models read the page's text from the image only.** No extractor or
    verifier request carries the page's text-layer lines. With them as hints and
    a prompt that preferred their spelling, the model copied the Arabic page's
    stored text, whose ligatures and letter order are wrong, and the text checks
    then compared the stored text with itself. The survey's measured text
    quality (control, private-use, replacement and unassigned characters) cannot
    see such faults, which are common in PDFs of right-to-left and other complex
    scripts. Without hints the comparison (decision 9) checks the model's own
    reading against the text layer, which follows the scope's rule that the
    model's reading wins, and requests are smaller. The prompts say to
    transcribe all text from the image, and that the text a PDF stores can
    differ from what is printed. The page's repeated lines stay in the page
    context only to say which lines are page furniture. The text-comparison
    retry message adds that the PDF's stored text can be wrong (letters out of
    order, broken ligatures, wrong characters), so the model keeps what the
    image shows.

### Defaults

| Setting                                       | Default      | Range             |
| --------------------------------------------- | ------------ | ----------------- |
| `pages`                                       | `null` (all) | page list         |
| `pause`                                       | `true`       | bool              |
| `model`                                       | `null`       | model setting     |
| `advanced.extraction.model`                   | `null`       | model setting     |
| `advanced.extraction.check_retries`           | `2`          | 0–5               |
| `advanced.extraction.concurrent_pages`        | `8`          | 1–32              |
| `advanced.extraction.effort`                  | `high`       | low, medium, high |
| `advanced.extraction.instructions`            | `null`       | text              |
| `advanced.extraction.max_output_tokens`       | `32000`      | > 0               |
| `advanced.extraction.request_timeout_seconds` | `600`        | > 0               |
| `advanced.survey.instructions`                | `null`       | text              |

`effort`, `instructions`, `max_output_tokens` and `request_timeout_seconds`
apply to the extractor and the verifier alike. `max_output_tokens` includes
thinking, which effort `high` raises, so a dense page needs the room; a larger
limit no longer brings the plan-time `max_cost` question, because that check
uses the expected cost (decision 12).

## Acceptance Coverage

- `AC-001`, `AC-002`: `pages` setting, CLI option and keyword; parsing and the
  two validation points (decision 3, **Page selection**). The survey is
  untouched by `pages`.
- `AC-003`, `AC-004`: `pause`, run status `paused`, the pause message, and the
  same behavior in `run()` and the CLI (decision 3, **Pause**).
- `AC-005`: Model resolution (decision 2, **Settings**) and each provider's
  output mode (decision 20).
- `AC-006`: **Example config files**; the existing completeness test.
- `AC-059`, `AC-060`, `AC-061`: Per-step instructions (decision 18,
  **Settings**, **Requests**, **CLI**); the existing unknown-setting and
  unknown-option errors for the removed ones.
- `AC-007`: Page file, item fields, label rule (**Page file**, check `labels`).
- `AC-008`: ID rule (decision 7).
- `AC-009`: Coordinate contract and mapping (decision 5); check `boxes`; the
  verifier for boxes on the wrong content.
- `AC-010`: Per-page direction from the profile in the prompt; check
  `reading_order` per direction (**Checks**).
- `AC-011`: Upright rendering from the profile's rotation and the mapping table
  (**Rendering and coordinates**); a rotated test PDF (**Test seams**).
- `AC-012`: Per-kind content fields and check `content`.
- `AC-013`: **Figure crops**.
- `AC-014`: `caption_of` and check `captions`.
- `AC-056`: Containers, item `container`, check `containers`.
- `AC-016`: Field content, form-field hints, check `form_fields`.
- `AC-017`: No check or verifier rule counts items or figure coverage; prompts
  and the verifier state that a one-figure page is valid.
- `AC-018`: Prompt rule for page furniture; check `artifacts`.
- `AC-019`: **Page context** resolution rules for ranges and the artifact
  mapping.
- `AC-020`: Neutrality rules under **Technical Acceptance Criteria**; nothing
  ported that names a document type, language or direction.
- `AC-021`: Checks and the retry rule (decision 8); `check_retries`.
- `AC-022`, `AC-023`: **Text comparison** (decision 9), on a reading the models
  make from the image alone (decision 21); `text_comparison` in the page file.
- `AC-024`, `AC-025`: Verifier and its application (decision 10); `verification`
  in the page file.
- `AC-026`: Shared `ReviewIssue` with `step`, `page_index`, `item_id`;
  `run.json` `review`; CLI summary (decision 14).
- `AC-027`: `run()`, `extract()`/`aextract()`, `load()` (**Python API**).
- `AC-028`: Ledger lines with `step`, `page_index` and `agent`; per-step and
  total cost (**`cost.jsonl`**).
- `AC-029`: `estimate()`/`aestimate()` and the CLI estimate cover the steps the
  run will perform (**Cost estimate and `max_cost`**).
- `AC-057`: `concurrent_pages` and the page semaphore (decision 11).
- `AC-058`: One image per request (decision 4).
- `AC-030`: Images in request bounds and reservations (decision 12).
- `AC-031`: Page fingerprints and reuse (decision 13).
- `AC-032`: Atomic page and crop writes, crop cleanup, damaged-file regeneration
  (**Page file**, **Figure crops**).
- `AC-033`: Failure handling and `ExtractionError` (decision 11, **Errors**).
- `AC-034`: **HTML report**.
- `AC-035` to `AC-044`: **Follow-up fixes**. `AC-043` and `AC-044` are
  Documenter's and Developer's edits with no architectural impact beyond the
  rules stated there.
- `AC-045`: **Test seams**; test evidence is Tester's.
- `AC-046`, `AC-047`: CI unchanged except the wheel smoke test, which also runs
  page extraction (**CI and release**).
- `AC-048`, `AC-049`, `AC-050`: **CI and release**; README text is Documenter's.
- `AC-051`, `AC-053`: No architectural impact beyond the interfaces fixed here;
  satisfaction depends on Documenter's guides and README and on Reviewer
  evidence that examples match behavior.
- `AC-052`: Reference generation covers the new settings, CLI options, public
  functions, the page file and the changed `run.json` (**Docs**).
- `AC-054`: No architectural impact — the user's review of real runs with their
  own keys after implementation and verification.

## Components

- **Settings** (`config/schemas.py`, `config/loading.py`): `pages`, `pause`,
  optional `model`, `ExtractionConfig` under `advanced.extraction`, model
  resolution per step, the page-list parser.
- **Runner** (`pipeline/runner.py`, `pipeline/schemas.py`): runs the survey and
  then page extraction, with the pause; per-step records and warnings;
  `run_extraction_step` for `extract()`; `load_run` reads page files.
- **Page extraction step** (`extracting/`, step module `CANDIDATE`): builds the
  page plan, reuses or extracts each selected page, runs the page tasks under
  the concurrency limit, writes crops and page files.
- **Rendering and coordinates** (`extracting/` `CANDIDATE`): the upright page
  image, figure crops, the grid-to-points mapping, and the single PyMuPDF worker
  that runs every PyMuPDF call of the step.
- **Text layer** (`extracting/` `CANDIDATE`): reads a page's text-layer lines
  and normalizes text for the comparison.
- **Prompts, agents, LLM, validators, schemas** (`extracting/`): as decision 1.
- **Review** (shared module `CANDIDATE`, such as `src/pydelity/review.py`):
  `ReviewIssue` and the check-failure model, imported by both steps and
  `pipeline/schemas.py` (which already imports `surveying/schemas.py`, so the
  model cannot live there).
- **Costs and providers** (`costs/budget.py`, `costs/schemas.py`,
  `providers/ledger_model.py`, `providers/factory.py`, `providers/profiles.py`):
  reservations, image counting, step models, ledger fields, the extraction
  estimate, each provider's output mode.
- **Report** (`report/html.py`, `report.css`): page cards with items.
- **API and CLI** (`api.py`, `cli.py`, `__init__.py`): `extract`/`aextract`, new
  options, the banner fix.
- **Probe** (`surveying/probe.py`): form-field, page-label, structure-tag and
  outline fixes.
- **Errors** (`errors.py`): `ExtractionError`.

Dependency direction: `extracting` imports `surveying.schemas` (vocabulary,
profile, facts) and the shared review module; `surveying` never imports
`extracting`; `pipeline` imports both.

## Interfaces and Contracts

### Settings

- `pages: str | None = None` — page list (**Page selection**). A single integer
  given in a file or keyword is accepted as that page.
- `pause: bool = True` — "Whether to stop after a step that wrote new output, so
  it can be checked before the next step is paid for."
- `model: str | None = None` — "The model for every step, as
  `<provider>:<model-id>`; each step's default if unset."
- `advanced.extraction` (`ExtractionConfig`, `extra="forbid"`, field
  docstrings): `check_retries`, `concurrent_pages`, `effort`, `instructions`,
  `max_output_tokens`, `model`, `request_timeout_seconds` (Defaults table).
- `advanced.survey` gains `instructions: str | None = None`.
- Both `instructions` fields: "What is particular, different or nuanced about
  this PDF, in your own words, for this step's model." Blank text counts as
  unset.
- The top-level `instructions` setting is removed. A file or keyword that sets
  it gets the existing unknown-setting `ConfigError` before any model call.
- `Config` gains properties for the resolved survey and extraction models
  (`ModelChoice`); `Config.model_choice` is removed.
- `advanced.models` prices apply to whichever step uses the model.

### Example config files

`examples/config.json` and `examples/config.yaml` gain `pages: null`,
`pause: true`, `model: null` (replacing the current default value),
`advanced.survey.instructions: null` and the whole `advanced.extraction` section
at its defaults, in alphabetical key order like the rest, and lose the top-level
`instructions`. The existing completeness test covers them.

### CLI

- New options: `--pages`/`-p` (`TEXT`, "Pages to extract, numbered from 1, such
  as 1-5,8; all pages if unset") and `--no-pause`/`-np` ("Run every step without
  stopping after the survey"). Given options override the config file, as now.
- `--instructions`/`-i` is removed; using it gives Typer's unknown-option usage
  error (exit 2) before any model call. Instructions have no CLI option; they
  are set in the config file or from Python.
- `--model` help names both steps and both defaults.
- Exit codes unchanged: a paused run exits 0; `ExtractionError` exits 1
  (`FAILED`), like other `PydelityError`s.
- The end-of-run summary lists each step's status and cost, the extraction's
  page counts (selected, extracted, reused), and review issues as
  `<step>, page <number>[, item <id>]: <message>`, where `<number>` is 1-based
  as in `pages`. After a pause it says how to continue (**Pause**).

### Python API

- `run`/`arun`: unchanged signature; `pages=` and `pause=` arrive through
  `**settings`. Returns `RunResult`.
- `extract`/`aextract(pdf=None, *, allow_over_max_cost=False, config=None, **settings) -> list[PageFile]`:
  reuses a valid matching survey or runs it, then extracts the selected pages;
  never pauses; writes no `run.json` and no report, like `survey()`. Returns the
  selected pages' page files in page order.
- `estimate`/`aestimate`: cover the steps the run would perform (**Cost estimate
  and `max_cost`**).
- `load(output_dir)`: `RunResult` gains `pages: list[PageFile]`, every page file
  in `pages/` in page order. A damaged page file raises `OutputError`, as other
  files do.
- `RunResult`, `PageFile` and `ExtractionError` are exported from `pydelity`.
- Every public run, survey, extract, measure and estimate function sets
  `pydantic_ai.BANNER_ENABLED = False` before its first agent runs, as the CLI
  does (`AC-040`). Importing pydelity still changes nothing.

### Page selection

- Syntax: comma-separated items, each `N` or `N-M` with `1 <= N <= M`, spaces
  allowed around items. Overlaps and repeats merge. Stored in canonical form
  (ascending, merged, such as `1-5,8`).
- Errors: bad syntax is reported with the other settings by `resolve_config`
  (`pages: ...`). A page number past the PDF raises `ConfigError` naming `pages`
  and the PDF's page count, after the PDF is opened and before the output folder
  is prepared, in `run`, `extract` and `estimate` alike.
- The survey always reads the whole PDF. Narrowing the selection leaves other
  page files in place; `run.json` and the report cover the selected pages only.

### Pause

- A run pauses when `pause` is on, the survey step wrote a new `pdf_survey.json`
  in this run, and page extraction would follow. The run then ends with status
  `paused`; the extraction step is recorded as `skipped`. The estimate and the
  CLI's spending question cover only the survey.
- The summary says: check `pdf_survey.json` and `report.html`, then run again to
  extract the pages, or pass `--no-pause` (`pause=False`) to run every step at
  once. When `overwrite` was set, it adds that the next run should leave it off,
  and that `--overwrite --no-pause` redoes every step in one run.
- A run that reuses the survey goes straight on to page extraction.

### Page context

Resolved per selected page from `pdf_survey.json` and `pdf_facts.json`, so step
2 runs to completion on any survey the survey step accepted (`AC-019`):

- Direction: the first `writing_direction.ranges` entry whose range lies inside
  the PDF and covers the page, else `writing_direction.default`. Rotation: the
  first such `rotation` entry, else 0. This is the survey comparison's rule.
- Repeated lines on the page: each fact line whose `pages` include the page,
  classified `artifact` when any `proposal.artifacts` entry lists its ID, else
  `content` when `proposal.non_artifact_lines` lists it, else `unclassified`.
  IDs the facts do not have are ignored.
- Labels: `profile.labels`. Languages: `profile.languages`. Instructions:
  `advanced.extraction.instructions` (never the survey's).
- Form fields on the page: `facts.form_fields` entries for the page; none when
  the form fact could not be read.
- Measured page facts: size, rotation attribute, text quality.

### Rendering and coordinates

- Displayed page: `page.rect` after the rotation attribute, `W` x `H` points,
  origin top left (as the survey's form-field boxes).
- Upright image: the displayed page turned clockwise by the page context's
  rotation `r`, JPEG quality 90, no alpha, at the largest zoom whose image stays
  within the image limits below and at most 300 DPI:
  - Anthropic: long edge at most 2,576 px, and
    `ceil(width/28) * ceil(height/28)` at most 4,784 (28 x 28 px tiles, one
    visual token each);
  - OpenAI, at `detail: "original"`: long edge at most 6,000 px and at most
    10,000 patches, counted with the patch size OpenAI's current images guide
    gives, which Developer confirms there.

  Each `ProviderProfile` holds its provider's limits, the image detail value to
  send, and a per-image token figure that is an upper bound for an image within
  those limits (Anthropic: 4,784). Rendering applies every supported provider's
  limits, so one image fits either provider without being shrunk. With the
  figures above, Anthropic's limits bind.

- Grid point `(x, y)` on the upright image gives `u = x/1000`, `v = y/1000`,
  then displayed fractions `(s, t)` and points `(s*W, t*H)`:

  | `r` | `s`     | `t`     |
  | --- | ------- | ------- |
  | 0   | `u`     | `v`     |
  | 90  | `v`     | `1 - u` |
  | 180 | `1 - u` | `1 - v` |
  | 270 | `1 - v` | `u`     |

  A box maps both corners and takes their min and max, clamped to the page.
  Form-field boxes sent as hints use the inverse mapping.

- Crops: the item's displayed-points box mapped back to the page's unrotated
  coordinates for PyMuPDF's clip, rendered at 200 DPI, turned upright by `r`,
  saved as PNG.
- All PyMuPDF calls (open, render, crop, text) of step 2 run on one worker
  thread, one at a time, never on the event loop.

### Requests

- Extractor instructions (`PromptPair.system_message`, the same for every page
  of a run, so providers can cache them): the task, the item vocabulary with
  role and kind definitions, the profile's labels with role, kinds and
  description, the item rules, the box grid, the output rules, and
  `advanced.extraction.instructions` last (decision 18). Verifier instructions:
  the audit task, the checklist and the verdict rules, with the same vocabulary,
  labels and `advanced.extraction.instructions` last. The survey's prompt takes
  `advanced.survey.instructions` the same way, in place of the top-level
  setting.
- User content per request: one text part whose first line is
  `Page index <i> (page <i+1> of <n>)` (logs and the test stand-in rely on it),
  then the page's direction and rotation applied, its repeated lines with their
  classification, and its form fields (name, type, value, checked, options, grid
  box); never the page's text-layer lines (decision 21); then the image (with
  `detail: "original"` for OpenAI, as PydanticAI's image vendor metadata); then
  a `CachePoint`. The verifier's text part adds the extractor's answer as JSON
  and the checks it still fails.
- Output: `PromptedOutput` on Anthropic, `NativeOutput` on OpenAI (decision 20).
- Anthropic requests also cache the instructions (PydanticAI's Anthropic
  instruction-caching setting), which hold the answer's JSON schema under
  prompted output. OpenAI caches prefixes itself.
- Prompt rules that matter to checks: list items in reading order for the page's
  direction (horizontal text column by column in the direction's order, so `rtl`
  starts from the right-hand column; vertical text band by band from the top,
  and within a band column by column in the order the script reads them, which
  the answer states in `column_order`); include page furniture as items with
  role `artifact`; transcribe text as printed, in its own script, without
  translating or correcting; one list entry per list item; tables with
  HTML-style spans and header rows; formulas with LaTeX; code with exact
  whitespace; all text read from the image, since the text a PDF stores can
  differ from what is printed; one item per figure with a description and any
  text inside it; one field item per form field, naming the fillable field when
  there is one; bordered or shaded boxes as containers; a caption names what it
  captions; a page that is one figure is one figure item. No prompt names a
  document type, language or direction as a default.

### Model answer and verdict

`PageAnswer`: `items: list[AnswerItem]` (reading order),
`containers: list[AnswerContainer]`,
`column_order: Literal["left_to_right", "right_to_left"] | None` (the order the
page's columns of vertical text are read in; set on pages whose direction is
`ttb`, `null` otherwise). The survey's `ttb` does not say which way columns run,
so the model, which sees the script, states it.

`AnswerItem`: `ref: str`, `kind: ItemKind`, `role: ItemRole`, `label: str`,
`box: list[int]` (grid), `language: str | None`, `container: str | None` (ref),
`caption_of: str | None` (ref), `text: str | None`, `latex: str | None`,
`entries: list[AnswerEntry] | None`, `table: AnswerTable | None`,
`figure: AnswerFigure | None`, `field: AnswerField | None`.

- `AnswerEntry`: `marker: str | None`, `text: str`, `level: int` (0 for top
  level).
- `AnswerTable`: `rows: list[list[AnswerCell]]`, `header_rows: int`;
  `AnswerCell`: `text: str | None`, `row_span: int`, `col_span: int`.
- `AnswerFigure`: `description: str`, `text: str | None` (text inside the
  figure).
- `AnswerField`: `field_type` (`text`, `checkbox`, `radio`, `choice`,
  `signature`), `prompt: str | None` (its printed label), `value: str | None`,
  `checked: bool | None`, `options: list[str]`, `fillable_name: str | None` (the
  PDF form field's name; `null` on a printed or scanned form).
- `AnswerContainer`: `ref: str`, `box: list[int]`, `label: str`,
  `container: str | None` (a box inside a box).

Which fields go with each kind (check `content`): `text` and `code` use `text`;
`formula` uses `text` (as printed) and `latex`; `list` uses `entries`; `table`
uses `table`; `figure` uses `figure`; `field` uses `field`. Other per-kind
fields are `null`.

`VerifierVerdict`: `passed: bool`, `problems: list[VerifierProblem]`,
`corrected: PageAnswer | None`. `VerifierProblem`: `item_ref: str | None`,
`category` (`missing`, `extra`, `merged`, `split`, `kind_or_role`, `label`,
`reading_order`, `box`, `text`, `table`, `field`, `container`, `caption`,
`other`), `description: str`. Pydantic invariants: passed means no problems and
no correction; not passed means at least one problem.

### Page file (`pages/<NNNN>.json`)

`PageFile` (field docstrings, schema version constant
`PAGE_SCHEMA_VERSION = "1.0"` in `schema_versions.py`):

- `schema_version`, `fingerprint`, `inputs` (what the fingerprint covers, as the
  survey's `inputs`), `extracted_at`, `pydelity_version`;
- `page_index` (0-based), `page_number` (1-based), `width_pt`, `height_pt`
  (displayed page), `rotation` (degrees applied to make it upright),
  `writing_direction`, `column_order`, `image` (`width_px`, `height_px`);
- `items: list[Item]` in reading order; `containers: list[Container]`;
- `text_comparison`: `compared`, `no_text_layer`, `garbled_text_layer` (measured
  quality `none` or `garbled`) or `text_layer_mismatch` (fewer than half of the
  answer's trigrams occur in a text layer measured as `good`, so it cannot be
  relied on);
- `checks: list[ExtractionCheckResult]` (name, passed, failures, attempts) for
  the kept extraction; `issues: list[ReviewIssue]`;
- `verification`: the verdict as given, `correction_applied: bool`, the checks
  the correction still failed when rejected, and the verifier's attempts.

`Item`: `id`, `kind`, `role`, `label`, `bbox` (`[x0, y0, x1, y1]` points on the
displayed page), `language`, `container` (container ID), `caption_of` (item ID),
`text`, `latex`, `entries` (each with `id`, `marker`, `text`, `level`), `table`,
`figure` (`description`, `text`, `crop`: the crop's path relative to the output
folder), `field`. `Container`: `id`, `bbox`, `label`, `container`.

Writing: figure crops first, then the page file atomically, then removal of the
page's older crops it no longer names. Loading: a page file is valid when it
parses, its major schema version matches, and every crop it names exists;
anything else is damaged and is extracted again with a `damaged_output` warning.

### Figure crops

`figures/<item id>.png`, one per figure item, written atomically. At run start
the runner removes leftover temporary files from the output folder, `pages/`,
`figures/` and `report/pages/`.

### Checks (names are part of the `run.json` contract)

Run in this order on every extractor answer and every verifier correction. Each
returns failures with a message naming the item ref.

1. `labels`: the label exists in the profile (regardless of case); its role is
   the item's role and its kinds include the item's kind. When no profile label
   has the item's role and kind, `other` passes and Python records one
   `no_matching_label` issue per page and role-kind pair instead (retrying
   cannot fix a missing label).
2. `content`: refs unique; per-kind fields present and the others `null`;
   non-empty text where required; list entries non-empty; table grid valid by
   the occupancy simulation (spans inside the grid, no overlaps, equal row
   widths), `0 <= header_rows <= rows`, some cell text; figure description
   non-empty; `checked` set for checkboxes and radio buttons.
3. `languages`: each `language` is a valid BCP-47 tag (`is_language_tag`) and
   set on every item with text; stored in standard form.
4. `boxes`: four values with `x0 < x1` and `y0 < y1` inside the grid within 5
   units; no two items with the same box. Full-page boxes are allowed.
5. `containers`: container refs resolve, nesting has no cycle, and each item or
   container lies inside its container's box within 20 units.
6. `captions`: every `caption` item names an item on the page that is not a
   caption; only caption items set `caption_of`.
7. `reading_order`: on the upright image's grid, over consecutive items with
   role `heading`, `body` or `navigation`, a jump back against the flow is
   allowed only with a column or band change in the reading order. Horizontal
   pages: a jump up by more than 150 grid units must move right (`ltr`) or left
   (`rtl`) by at least 200. `ttb` pages: `column_order` must be set, and a jump
   by more than 150 against it (right for `right_to_left`, left for
   `left_to_right`) must move down by at least 200.
8. `artifacts`: each repeated line the survey classified as `artifact` that is
   on the page is contained, in the repeated line's normalized form, in the text
   of some item with role `artifact`.
9. `form_fields`: each fillable form field on the page except push buttons is
   named by exactly one field item, whose `value` or `checked` matches the
   form's after whitespace is collapsed.
10. `text_dropped` and 11. `text_added`: **Text comparison**.

Other review-issue names: `no_matching_label` (above) and `verifier` (decision
10). Python only records them; neither sends an answer back.

### Text comparison

- Normalization: NFKC, case-folded, keeping only letters, marks and numbers
  (Unicode categories `L*`, `M*`, `N*`); everything else, including spaces and
  hyphens, is removed. No word lists and no tokenizer.
- Text-layer lines: the page's lines from the text layer, with the probe's text
  flags. Answer text: each item's text, list entries, table cells, field prompts
  and values, figure text and formula text.
- `text_dropped`: a text-layer line with at least 3 trigrams fails when fewer
  than half of its trigrams are found in the answer's trigram multiset. A line
  also counts as found when its reversed text matches, for PDFs that store
  right-to-left text in visual order.
- `text_added`: an answer line (item text split at line breaks; figure text,
  field values and formula text excluded, since they can come from images or
  form data) with at least 3 trigrams fails when fewer than half of its trigrams
  remain in the text layer's multiset, consumed in reading order, so a repeated
  line also counts as added.
- Guarantee: on a page with a `good` text layer, removing a line of at least 5
  letters or digits from a correct answer, or adding one, fails a check, in any
  script. Developer may tune the thresholds only with tests that keep this.
- Skipped, with the page file saying why, when the measured quality is `none` or
  `garbled`, and on `text_layer_mismatch`.
- Retry message for these two checks: the lines found, plus that the model may
  keep its reading when the text is not visible on the page or was read from an
  image, and that the PDF's stored text can be wrong (letters out of order,
  broken ligatures, wrong characters), so where the image shows the text
  differently the model keeps what the image shows.

### Verifier application

1. Extractor answer accepted (all checks passed, or retries ran out).
2. Verifier request. Its output validator runs every check on `corrected` when
   present, with the retry rule; a verdict whose correction still fails on the
   last attempt is accepted as given.
3. `passed`: keep the extraction. Problems with a correction that passes every
   check: keep the correction; the problems stay in the verdict only. Problems
   otherwise: keep the extraction; each problem becomes a `verifier` review
   issue naming its item when it has one.
4. The kept answer's check results and issues go into the page file.

### Review issues

Shared `ReviewIssue`: `step` (`survey` or `extraction`), `check` (the survey's
names, the extraction checks, `no_matching_label`, `verifier`), `message`,
`details`, `page_index`, `item_id: str | None` (required, `null` when no item
applies). `pdf_survey.json` uses it too. `run.json` `review` holds the survey's
issues and then each selected page's issues in page order.

### Survey changes

- `SurveyInputs.instructions` and the survey fingerprint take
  `advanced.survey.instructions`; the prompt's "user's instructions" section
  uses it (decision 18).
- `Profile.user_instructions` is removed.
- On Anthropic the survey's agent asks for `PromptedOutput` (decision 20); its
  answer schema, checks and retry rule are unchanged.

### `run.json`

- `status` adds `paused`. `steps` has a record per step that started or was
  skipped by a pause, in pipeline order.
- `StepRecord` adds `pages: PageCounts | None` (`selected`, `extracted`,
  `reused`) for the extraction step. Its `outputs` names `pages/` and
  `figures/`, not each file. `pdf_transport` is `null` for extraction.
- `warnings[].step` is the step running when the warning was issued.
- Schema versions are not raised this cycle. New fields are required (decision
  19).

### `cost.jsonl`

`LedgerEntry` adds required `page_index: int | None` and `agent: str | None`
(`extractor` or `verifier`; both `null` for the survey). `step` is `extraction`
for both agents. `RunCost.by_step` and the summary report each step and the
total.

### Cost estimate and `max_cost`

- `estimate_extraction` (beside `estimate_survey`) prices the pages that would
  be extracted (selected pages without a reusable page file; all of them with
  `overwrite`). Per page, input tokens are the instructions and context
  characters (the answer schema included) divided by `PROMPT_CHARS_PER_TOKEN`
  and the provider's per-image tokens; no text-layer characters, since requests
  carry none (decision 21). Expected: one extractor and one verifier request,
  with typical output that grows with the page's measured characters. Maximum:
  `check_retries + 1` requests of each agent with `max_output_tokens` each and
  earlier answers added to input. When the survey runs in the same run, the
  profile's size is a fixed allowance.
- The run's estimate covers the survey when it will run, and extraction when it
  will run in this run (not paused); when the survey runs first, every selected
  page counts as to extract. The estimate, the CLI question, the plan-time check
  and the API-key check of every step that will run happen once, before the
  run's first request: in the survey step when the survey runs, otherwise in the
  extraction step. `StepEstimate` adds `pages: int | None`.
- `CostEstimate.over_max_cost` becomes: `max_cost` set and recorded spend plus
  the expected cost exceeds it, or a model is unpriced (decision 12).
- `LedgerModel` counts each image at `ProviderProfile`'s per-image token figure
  (**Rendering and coordinates**) and prices the request with its own step's
  model. It reserves its bound with the guard before sending and releases it
  after the ledger line or on any error or cancellation.

### HTML report

- Pages section: for each selected page with a page file, the report image
  (displayed page) with every item's box drawn in percent of the displayed page
  (the existing `_box` approach), numbered by reading-order position, and every
  container drawn in its own style. Beside it, a list of items: number, ID,
  kind, role, label, content (text, entries, a table with spans, field value,
  figure description and its crop as an image), and the page's verifier outcome.
- Each review issue with an `item_id` links to that item's box and list entry
  (an anchor per item ID), and the item's box is marked.
- Paused runs show the survey as now.

### Errors

`ExtractionError(PydelityError)` for a page whose model refuses, runs out of
output tokens (naming `advanced.extraction.max_output_tokens`), or never gives
an answer matching its schema. Its message and `ProviderError`s from page
requests name the page (`page <n> (index <i>)`) and the agent. On either, the
run cancels its other page tasks and ends `failed`; `run.json` and the report
are written first.

### Follow-up fixes

- `AC-035`: read a checkbox's state from its `/V` and `/AS` values without
  `on_state()`; each widget is read on its own, so one failure loses only that
  field (with a probe error naming it); a radio group whose buttons are all off
  but whose `/V` names one of their on states reads that value.
- `AC-036`: page labels with letter style (`/S /A`, `/S /a`) give
  `PrintedNumber(style="label", value=None)`; only decimal and roman styles give
  numbers.
- `AC-037`: follow indirect `/K` arrays; a walk that stops at its cap rates
  coverage over the pages it reached only; tagged pages without text are left
  out of coverage.
- `AC-038`: stop the outline walk at the first repeated entry and keep the
  bookmarks read before it.
- `AC-039`: the survey step records its PDF transport as soon as a request
  carries the PDF, so a failed step reports it.
- `AC-041`: `_config_price` treats only `None` as unset.
- `AC-042`: CI's stale-reference check also fails on untracked generated pages
  (`git status --porcelain` on the reference folder); `docs.yml` comments
  describe the pnpm cache accurately and its plan step no longer hides `node`'s
  errors.
- `AC-043`, `AC-044`: `CHANGELOG.md` links `c63d891`; `pyproject.toml` drops the
  `def cli` exclusion and the `./src/pydelity/__init__.py` omit; the listed docs
  wording fixes.

### Test seams

- The stand-in provider server gains answer routing by request content, so
  concurrent page requests get their page's extractor or verifier answer
  whatever order they arrive in (the first text line names the page; the
  instructions tell the agents apart). It accepts image parts from both
  providers, and answers every Anthropic request, the survey's included, as JSON
  text (prompted output), and OpenAI's in their native output format.
- Canned extraction and verifier answers for the test PDFs live beside the
  survey answers (`CANDIDATE` folder).
- A rotated test PDF: a copy of an approved test PDF with pages whose rotation
  attribute is 90, 180 and 270, recorded in `tests/fixtures/pdfs/SOURCES.md`
  with how it was made (`CANDIDATE` name; the user approves source and name).
- No step 2 code reads the environment or chooses behavior for tests.

### CI and release

- Workflows keep their jobs and gates; "Lint and test" and "TruffleHog secret
  scan" stay required. `scripts/smoke_installed_wheel.py` also runs page
  extraction against the stand-in on ubuntu, macOS and Windows.
- `pyproject.toml` description and README describe surveying a PDF and
  extracting its pages; classifiers unchanged (Alpha, Python 3.13 and 3.14).
- release-please stays as configured: the manifest at `0.1.1` and a `feat:`
  squash commit give 0.2.0 and `v0.2.0`; `release.yml` and `docs.yml` publish as
  for 0.1.x.

### Docs

`scripts/generate_reference_docs.py` gains pages for `pages/<NNNN>.json`, the
extraction checks and review-issue names, and picks up the new settings, CLI
options, functions and `run.json` and `cost.jsonl` fields from the code, so CI's
staleness check covers them.

## Data and Control Flow

1. Resolve settings; open the PDF; check `pages` against its page count; prepare
   the output folder (clean temp files in it, `pages/`, `figures/`,
   `report/pages/`); write `run.json` (`running`).
2. Survey step as now, except that its estimate, question, plan-time check and
   key check also cover extraction when the run will not pause. If it wrote a
   new survey and `pause` is on, finish with `paused`.
3. Extraction step: build each selected page's context; load and check each page
   file against its fingerprint; the rest are to extract. When the survey was
   reused, the estimate, the CLI question, the plan-time `max_cost` check and
   the key check happen here.
4. Build the step's provider client once; run one page task per page to extract
   in a `TaskGroup`, at most `concurrent_pages` at once. A page task: render the
   image and read the text-layer lines (PyMuPDF worker); extractor agent with
   checks and retries; verifier agent with checks on its correction; apply the
   verdict; map boxes to points and assign IDs; render and write crops; write
   the page file; remove stale crops; log the page's outcome and cost.
5. Each request: `LedgerModel` reserves its bound (images counted), sends,
   writes its ledger line with page and agent, releases the reservation.
6. On the first page error or a `max_cost` no: cancel the other page tasks,
   finish `failed` or `stopped`, write `run.json` and the report, raise.
7. On success: `run.json` with both steps, review issues from the survey and the
   selected pages, the report, the summary.

`extract()` runs steps 1–5 without `run.json` or the report, never pauses, and
returns the selected pages' page files. `survey()` is unchanged.

## Technical Acceptance Criteria

- `AC-001`: `pages` is accepted from a file, `--pages`/`-p` and the keyword;
  `1-5,8` selects page indexes 0–4 and 7; unset selects all; the survey's inputs
  and fingerprint do not include `pages`.
- `AC-002`: malformed `pages` and page numbers past the PDF raise `ConfigError`
  whose message names `pages`, before `run.json` is written and before any
  request, in `run`, `extract` and `estimate`.
- `AC-003`: with defaults, a run that writes a new survey ends `paused`, sends
  no extraction request, and its summary says how to continue; the next run
  reuses the survey and extracts; `run()` returns a `RunResult` whose record is
  `paused`, with no exception.
- `AC-004`: `pause` false (file, `--no-pause`/`-np`, keyword) runs survey and
  extraction in one run.
- `AC-005`: the extraction model is `advanced.extraction.model`, else `model`,
  else `anthropic:claude-opus-5-5`; the survey's is `model`, else its default;
  extraction's default effort is `high`; ledger lines, estimates and
  fingerprints use each step's resolved model. Survey, extractor and verifier
  requests to Anthropic carry no native output format and their instructions
  hold the answer's JSON schema; to OpenAI they carry the JSON-schema output
  format.
- `AC-006`: both example files hold every setting at its default, including
  `pages`, `pause`, `model: null`, `advanced.survey.instructions` and
  `advanced.extraction`, hold no top-level `instructions`, and load without a
  settings error.
- `AC-059`: `advanced.survey.instructions` and
  `advanced.extraction.instructions` are accepted from a file and from Python
  (`advanced={...}`); the CLI has no option for either.
- `AC-060`: each step's instructions appear in its own agents' instructions only
  (the survey's agent; the extractor and the verifier), in every request of that
  step, and in no other step's requests; with the setting unset or blank, no
  instructions heading is sent; `pdf_survey.json` `profile` holds no
  instructions; each step's fingerprint includes only its own instructions.
- `AC-061`: top-level `instructions` in a file or keyword gives the
  unknown-setting `ConfigError`, and `--instructions` or `-i` gives the
  unknown-option usage error, both before any request.
- `AC-007`: every page file item has an ID, a `kind` and `role` from the
  vocabulary, and a profile label whose role and kinds match, or `other` with a
  `no_matching_label` issue when no profile label has that role and kind.
- `AC-008`: IDs follow the rule in decision 7; two page files built from the
  same answer are byte-identical in `items` and `containers`.
- `AC-009`: every stored box is in points on the displayed page, origin top
  left, inside the page, and is the mapping of the model's grid box.
- `AC-010`: the prompt states the page's resolved direction; `reading_order`
  accepts column-by-column order and rejects a backward jump without a column or
  band change, for `ltr`, `rtl` and `ttb` with either `column_order`.
- `AC-011`: the image sent is upright per the resolved rotation, for rotation
  attributes 0, 90, 180 and 270 and for sideways content on rotation-0 pages; a
  grid box maps to the displayed-page points of the same content; the image is
  the largest within every provider's limits and 300 DPI.
- `AC-012`: `content` enforces the per-kind fields; list entries get their own
  IDs; tables keep rows, spans and `header_rows`; formulas carry `latex`; code
  text is stored unchanged; fields carry `value` or `checked`.
- `AC-013`: every figure item names an existing PNG crop in `figures/`, cut from
  its box and upright.
- `AC-014`: every caption item's `caption_of` names an item ID on its page, or
  the page has a `captions` issue.
- `AC-056`: every container has an ID and a box; items inside name it; `kind`
  and `role` are unaffected by containment.
- `AC-016`: fillable fields' values and states reach field items or
  `form_fields` issues; printed or scanned forms' marked values are field items
  with `fillable_name: null`.
- `AC-017`: a page answer of one full-page figure passes every check and is not
  a verifier problem by itself.
- `AC-018`: repeated lines classified as artifacts appear in `artifact` items,
  or the page has an `artifacts` issue.
- `AC-019`: overlapping, gapped or out-of-PDF ranges and a missing, repeated or
  unknown artifact mapping resolve by the **Page context** rules without error.
- `AC-020`: `extracting/` code, prompts, page file fields and defaults contain
  no document-type names, language-specific words or patterns, or a default
  direction; text handling uses Unicode categories only.
- `AC-021`: checks run on every answer and correction; failures retry up to
  `check_retries`; the last answer is kept with each still-failing check as a
  review issue.
- `AC-022`: the comparison meets the guarantee under **Text comparison** on
  Arabic, Chinese, Japanese and English test pages.
- `AC-023`: text failures retry with the message described; leftovers are review
  issues; skipped pages record the reason in `text_comparison`. No extractor or
  verifier request holds the page's text-layer lines.
- `AC-024`: every extracted page has exactly one verifier verdict; the kept
  answer is the correction only when it passes every check; otherwise each
  verifier problem is a `verifier` issue.
- `AC-025`: every page file holds its verdict, whether the correction was
  applied, and why not.
- `AC-026`: extraction issues carry `step: "extraction"`, `page_index` and
  `item_id` where an item applies; they appear in `run.json` `review` and in the
  CLI summary.
- `AC-027`: `pydelity <pdf>` and `run()` include extraction per the pause rule;
  `extract`/`aextract` reuse or run the survey and return the page files;
  `load()` returns them.
- `AC-028`: every extractor and verifier request has a ledger line with
  `step: "extraction"`, `page_index` and `agent`; `run.json` and the summary
  report per-step and total cost.
- `AC-029`: `estimate`, `aestimate` and the CLI estimate include extraction of
  the pages to extract, with both agents, whenever the run would extract.
- `AC-057`: no more than `concurrent_pages` page tasks are in flight at once.
- `AC-058`: each extractor and verifier request carries exactly one page image
  and no PDF.
- `AC-030`: with `max_cost` set, no request is sent while recorded spend plus
  reservations plus its bound exceeds `max_cost` unless the run's decision is
  yes, whatever the concurrency; images count in each bound.
- `AC-031`: unchanged inputs reuse every valid page file with no request; a
  change to any fingerprinted input reruns exactly the affected pages; new
  selections extract only new pages; `overwrite` reruns every selected page; no
  extraction setting changes the survey's fingerprint.
- `AC-032`: an interrupted run leaves no partial page file or crop; a page file
  that does not validate or names a missing crop is extracted again.
- `AC-033`: a page's provider error, timeout, refusal or unusable answer ends
  the run `failed` with the error carrying the provider's message; the CLI exits
  1; written page files stay valid and are reused next time.
- `AC-034`: the report shows each extracted page with numbered item boxes,
  containers, the item list with crops, and links from item issues to boxes.
- `AC-035` to `AC-044`: the rules under **Follow-up fixes** hold.
- `AC-045`: tests run with the stand-in or PydanticAI test models only, with no
  network access to providers.
- `AC-047`: the wheel smoke test runs survey and extraction on Windows.
- `AC-048` to `AC-050`: built artifacts pass `twine check --strict`; metadata
  describes both steps; release-please configuration is unchanged.
- `AC-052`: generated reference pages cover every new setting, option, function
  and output field, and CI fails when they are stale or untracked.

## Build Plan

Critical path: 1 → 2 → 3 → 4 → 5 → 6. Step 7 can go any time; 8 and 9 follow the
code they cover.

1. **Settings and runner shape.** `MODIFY` `config/schemas.py`,
   `config/loading.py`, `examples/config.json`, `examples/config.yaml`,
   `providers/profiles.py` (second default model, image limits): `pages`,
   `pause`, optional `model`, `advanced.extraction`, model resolution, and the
   move of instructions to `advanced.survey.instructions` (`MODIFY`
   `surveying/prompts.py`, `surveying/survey.py`, `surveying/schemas.py`;
   `cli.py` loses `-i`). Move `ReviewIssue` to the shared module (`CREATE`
   `CANDIDATE` `src/pydelity/review.py`; `MODIFY` `surveying/*`,
   `pipeline/schemas.py`). Refactor `pipeline/runner.py` to per-step records,
   step-attributed warnings (`MODIFY` `utils/coroutines.py`), run status
   `paused` and the pause, with the extraction step still empty.
2. **Costs and models.** `MODIFY` `costs/budget.py` (reservations, expected-cost
   plan check), `costs/schemas.py`, `providers/ledger_model.py` (images, step
   model, page and agent context, reservations), `providers/factory.py` (step
   model; one client per step, one ledger wrapper per page and agent; output
   mode from the provider profile), `providers/profiles.py` (each provider's
   output mode).
3. **Extraction core.** `CREATE` `extracting/__init__.py`, `schemas.py`,
   `prompts.py`, `validators.py`, `agents.py`, `llm.py`, and the rendering and
   text-layer modules (`CANDIDATE` names); `MODIFY` `schema_versions.py`,
   `errors.py`.
4. **Extraction step.** `CREATE` the step module (`CANDIDATE`): page context,
   fingerprints, reuse, page tasks, verifier application, crops, page files.
   `MODIFY` `pipeline/runner.py`, `utils/files.py` if temp cleanup needs the new
   folders.
5. **API and CLI.** `MODIFY` `api.py`, `cli.py`, `__init__.py`,
   `pipeline/runner.py` (`load_run`, estimates, summary).
6. **Report.** `MODIFY` `report/html.py`, `report/report.css`.
7. **Follow-up fixes.** `MODIFY` `surveying/probe.py`, `surveying/survey.py` or
   `surveying/llm.py` (transport), `costs/pricing.py`,
   `.github/workflows/ci.yml`, `.github/workflows/docs.yml`, `CHANGELOG.md`,
   `pyproject.toml`.
8. **Tests and fixtures.** `MODIFY` `tests/fixtures/mock_providers.py`,
   `tests/conftest.py`, `scripts/smoke_installed_wheel.py`; `CREATE` the rotated
   test PDF and canned answers (`CANDIDATE` names); tests beside each module.
9. **Release and reference.** `MODIFY` `pyproject.toml` (description),
   `scripts/generate_reference_docs.py`; README and guides are Documenter's.

## Risks and Follow-up

- Box accuracy rests on the model and the verifier. Snapping boxes to measured
  text is a possible later improvement, not in this cycle.
- The text comparison can flag text read from raster images on pages with a good
  text layer (slides with pictured text), costing retries and adding review
  issues. Thresholds may need tuning on the user's real runs.
- Text layers that store right-to-left text in visual order, vertical text with
  unusual line order, or legacy font encodings rated `good` can mislead the
  comparison; the reversed-line match and `text_layer_mismatch` reduce this.
  Stored text with broken ligatures still differs from a correct reading on
  short lines: on the Arabic test page, hand-corrected body lines keep 67–84% of
  their trigrams in the stored text and pass, while a short numbered heading
  keeps 12% and fails. Such pages spend their check retries and list those lines
  for review. Judging each page's stored text against the model's reading is a
  possible later improvement.
- Without text-layer hints, exact spelling on clean pages rests on the image at
  about 200 DPI; the comparison still catches dropped and added lines.
- Prompted output has no grammar behind it, so an Anthropic answer that is not
  valid JSON costs a retry, and on the last allowed attempt fails the survey or
  the page and stops the run.
- Image limits are provider documentation as of November 2026 (Anthropic's
  vision guide for Opus 4.7 and later; OpenAI's images guide). Older Claude
  models shrink the image to their own lower limit, which the grid coordinates
  tolerate. An OpenAI model that does not accept `detail: "original"` fails with
  the provider's error, as any unsupported setting does.
- Effort `high` costs more thinking tokens per page than `medium`; the estimate
  shows it. A dense page can still exceed 32,000 output tokens; the run then
  stops with `ExtractionError` naming the setting.
- A 0.1.x output folder may stop a run on its `cost.jsonl` (decision 19); the
  user starts a new folder or deletes the old one.
- Eight concurrent requests can hit low provider rate limits; the SDKs retry
  429s up to `provider_retries`, after which the run stops. Lowering
  `concurrent_pages` is the remedy, and the docs should say so.
- Canceling in-flight pages after a failure may leave requests the provider
  still bills, with no ledger line (as for timed-out requests today).
- Serialized PyMuPDF calls bound rendering speed; model requests dominate run
  time, so this is acceptable.
- The plan-time `max_cost` check now uses the expected cost, so a run may ask
  mid-run instead of up front. The costs guide must say so.
- The first wave of concurrent requests cannot read the instruction cache.
- `model` becoming optional changes the example files and generated reference; a
  saved survey stays reusable because its fingerprint uses the resolved model.
- Probe fixes do not raise `PROBE_VERSION`, so old facts are not remeasured
  without `overwrite`.
- Large PDFs make large reports; acceptable at Level 3.

## Alternatives

- **Pixel coordinates with the image size in the prompt** (KGForEdGlobal):
  rejected, because providers may resize images and the model then answers in
  another scale.
- **Discriminated union of item content**: rejected for the answer schema; a
  flat item with per-kind checks keeps structured-output schemas simple and
  failures retryable.
- **Sending the uploaded PDF and naming the page**: rejected; a rendered upright
  image gives exact geometry for rotated content and one image per request.
- **Verifier only on failed or hard pages** (the brief): rejected by scope,
  which requires every page.
- **Letting in-flight pages finish after a failure**: saves some spend but adds
  coordination code; cancellation through `TaskGroup` is simpler.
- **Verdicts in their own files**: rejected; one page file per page keeps writes
  atomic and resume simple.
- **Plan-time check against the maximum** (0.1.0): rejected for multi-page
  steps, where the maximum is far above any real run.
- **A fixed page image size** (2,000 px on the long edge in the first design):
  rejected; it used about 85% of what Anthropic's current models take, and
  OpenAI's `high` detail shrank it. Sizing from the providers' documented limits
  gives the most detail they use without wasted pixels.
- **A shared instructions setting for every step**: replaced by the user's
  choice of instructions per step, since each step's instructions are specific
  to it.
- **Native output on Anthropic with a smaller answer schema**: rejected. Nested
  or union content also counts against Anthropic's union-type limit, the error
  in the real run was a grammar-size limit that is not published, and fitting
  the schema to it would trade the flat answer (decision 7) for a guess.
- **Native output on Anthropic for the survey, whose answer fits today**:
  rejected by the user's choice. Anthropic's limits can change, and one output
  mode per provider is simpler than one per step.
- **Text-layer hints with a prompt that trusts the image** (the first design
  sent them when the measured quality was `good`): rejected after the Arabic
  run. Any hint invites copying stored text the survey cannot judge, and makes
  the text checks compare the stored text with itself.

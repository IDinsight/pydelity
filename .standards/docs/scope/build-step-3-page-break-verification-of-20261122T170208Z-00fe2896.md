<!-- STANDARDS
Artifact: SCOPE
Cycle: build-step-3-page-break-verification-of-20261122T170208Z-00fe2896
-->

# pydelity page-break verification (step 3) and release 0.3.0

## Goal

Release 0.2.0 ships the survey and page extraction, each with an opt-in
verifier. This cycle builds page-break verification, the third of the pipeline's
six steps, and ships it as 0.3.0.

Page-break verification reads the page files and judges each break between two
consecutive pages: whether content carries on from one page to the next, which
items connect, how they join, how many repeated table header rows and which
repeated items above the continued unit to drop, any marker on the continued
unit that says it continues, and which containers continue. One-page judgments
miss most continuations (brief E2 and E3), so the judgment looks at both pages.
Assembly, the next step, will join content only where these verdicts say so,
which means they must be right in any script, layout and writing direction and
must give assembly what it needs without language rules.

Verdicts always cover the whole PDF. Page-break verification runs only when
every page has a current page file, and a run whose `pages` setting leaves gaps
extracts what it was asked to and stops short of judging breaks.

The step follows the rules the survey and page extraction follow: the model's
own reading decides, code's measurements and the survey's findings are hints,
checks of the verdict's own consistency may send it back, an opt-in verifier
covers every break or none, and what stays unresolved goes on the review list.
Here the verifier is a second judgment that does not see the first, and where
the two disagree goes on the review list. The cycle extends the run features to
the new step: settings, the CLI and Python API, the pause between steps, the
cost estimate and spend control, resume, the review list and HTML report, tests,
docs and the release.

## Constraints

- Target maturity: Level 3 (internally testable) for the library, the CLI, the
  release and the docs site, as for 0.1.0 and 0.2.0.
- Python 3.13 and 3.14 only, with Pydantic, pydantic-settings, PydanticAI,
  loguru, Typer and PyMuPDF 2.x. PyMuPDF calls run on one worker thread per run.
  Models are reached through provider APIs via PydanticAI, and every request,
  the verifier's included, must work with both Anthropic and OpenAI models.
- One structured-output mode per provider for every request: prompted output on
  Anthropic and native output on OpenAI.
- Document-type agnostic: no core logic, prompt, verdict field or default may
  assume a document type, a language or a writing direction. There is no
  hand-written per-document config, no domain Pydantic class and no
  language-specific word list or pattern. Document-specific knowledge comes only
  from the survey's profile, its continuation notes and start markers included,
  and from the instructions the user gives this step. Code therefore cannot find
  continuation markers or choose how two pieces of text join; the verdict says.
- Hints and checks. Code's measurements of the PDF and the survey's findings are
  hints that the model's own reading overrides. No message asks the model to
  match a hint, and a difference from a hint never sends an answer back and
  never fails a break, the step or a run. It goes on the review list unless the
  step's verifier ran and its judgment matched the kept verdict, and the verdict
  file keeps it either way. Checks test the verdict's consistency with itself,
  the two page files and the survey's profile, and its hard limits. They may
  send a verdict back within the step's check retries, and a final verdict still
  failing one is kept and listed while the run goes on.
- A run stops only on an unusable answer (none in the answer format within the
  retries, a refusal, or output tokens used up) or a provider error after the
  provider retries.
- Each check sits where it can be enforced: Pydantic classes for shape, the
  step's `validators.py` for what code can decide, and the step's verifier for
  what code cannot judge. A verifier is a second request to the step's own model
  with this step's instructions only. Here it judges every break a second time,
  without seeing the first judgment, or judges none, and code compares the two.
- The step's code sits in `src/pydelity/verifying/`, with `agents.py`, `llm.py`,
  `prompts.py`, `validators.py` and `schemas.py` beside the step's own module.
  Outputs, logs and estimates name the step with a noun. Every other new name of
  a setting, CLI option, file or folder is the user's to approve before the
  build step that creates it.
- Reuse before rewriting: pydelity ports KGForEdGlobal's page-break verification
  (`backend/src/kgfeg/page_ir_verification/` and
  `entries/verify_page_ir_continuity.py`) where it fits, updated for PydanticAI
  2.69 or later and PyMuPDF 2.1 or later, and carries none of the defects listed
  under "Known defects in the source code to design out" in
  `artifacts/design_brief.md`. KGForEdGlobal
  (`/Users/tzz/Projects/private/idi/KGForEdGlobal`) is read-only.
- PDF transport, whenever a request sends the PDF: upload it with the provider's
  file API, reuse the upload recorded in `uploads.json` while it is usable, and
  send the PDF inside the request only when the upload path fails.
- pydelity keeps no per-model limits and checks none before a model call. There
  is no default `max_cost`. When a run could go over it, the CLI asks at most
  once per run, possibly partway through (`--yes` answers yes), and Python
  callers pass `allow_over_max_cost=True` or get `BudgetExceededError`.
- Every Python function that measures, estimates or runs has an async version
  named with an `a` prefix, and the docs lead with the async functions. `load`
  stays sync.
- Every CLI option has a short form, and there is no `--quiet`.
- No backwards compatibility is kept. A setting, option, function, output field
  or file format that this cycle renames, removes or changes is replaced
  outright, with no aliases, deprecation warnings, migrations, fallbacks for old
  files or defaults kept for older calls, and output folders written by 0.2.0
  are not migrated. `PROBE_VERSION`, the existing `PROMPT_VERSION`s and every
  existing output `schema_version` stay where they are, and page-break
  verification's own versions start at 1 (`"1.0"` for its output).
- Automated tests mock every model call and make no network calls to model
  providers. Real model runs use the user's own API keys, only with the user's
  go-ahead, and record the spend.
- Test PDFs are real public documents the user approves, under 500 KB each. A
  copy with some pages' rotation attribute changed counts when
  `tests/fixtures/pdfs/SOURCES.md` says how it was made.
- Acceptance rests on the user's review of real runs with Anthropic models (the
  user's choice on 2026-11-28). Mocked tests alone show that every request works
  with OpenAI models. There is no parity target with KGForEdGlobal, and cost is
  reported with no pass/fail target.
- Reviews raise only major issues, as for 0.2.0 (confirmed by the user for this
  cycle on 2026-11-22). On input the release targets, a finding must make the
  delivered output wrong, lose money, fail a run, or break a function the
  acceptance review relies on. Smaller problems are recorded as limitations.
- The repo setup stays as it is unless this work needs a change. Scripts, `just`
  recipes, hooks and CI work without `.standards/`. "Lint and test" and
  "TruffleHog secret scan" stay required checks on `main`. A new runtime
  dependency's minimum version is its latest stable release on the day it is
  added.
- Shipped code, config, docstrings and docs never mention the development
  process: no dates, DEV or AC IDs, cycles, STANDARDS roles, KGForEdGlobal or
  numbered steps. They name the step ("page-break verification", "later steps").
- Commits follow Conventional Commits and carry no `Co-Authored-By` trailer or
  other AI attribution. The branch merges to `main` only after this cycle's
  sign-off and STANDARDS Project Uninstallation on the branch.
- The release is 0.3.0 (tag `v0.3.0`), chosen by the user for this cycle alone.
  Once the cycle is signed off, its work reaches `main` as one non-breaking
  `feat:` commit (the squash-merged pull request's title). A breaking commit
  would make release-please propose 1.0.0, so the commit stays non-breaking even
  where this cycle changes an earlier interface. In-cycle evidence covers
  release readiness, not the upload or the docs site's deployment.

## Non-goals

- Assembly and the later steps and their outputs: joining content,
  `document.json`, the outline, segment IDs, fill-down, the domain schema,
  `domain.json`, and the KGForEdGlobal-compatibility outcomes that depend on
  them. Page-break verification records verdicts and changes no page file.
- Verdicts for part of a PDF. Page-break verification never judges a subset of
  the breaks because of a narrowed `pages` selection, and it never extracts
  unselected pages to fill the gaps.
- Continuation between pages that do not follow each other, such as text that
  jumps to a later page or a table interrupted by an inserted full-page figure.
  Each break is judged only between page N and page N+1.
- Continuity inside one page, such as a paragraph carried from one column to the
  next, which page extraction's reading order already covers.
- Continuity marks in page extraction (the brief's option E).
- A verifier that reviews only some breaks, a sample, or only failed or
  low-confidence breaks (the brief's option D as written), and a separate model,
  effort or other model setting for the verifier.
- A verifier that reviews or corrects the first judgment's verdict, and a third
  request that chooses between two judgments that differ.
- Real model runs with OpenAI models for this cycle's acceptance.
- Changing what the survey and page extraction produce, beyond the run flow
  changes this step needs. The page extraction items under "Pushed to later
  steps" and "Observations left for later" in `artifacts/next_cycle_inputs.md`
  stay open, and so do the risks listed there.
- Raising `PROBE_VERSION`, an existing `PROMPT_VERSION` or an existing output
  `schema_version`, and deciding when pydelity starts keeping backwards
  compatibility.
- Translating extracted text.
- Any change to KGForEdGlobal, and KG, Learning Component or Learning
  Progression logic.
- Per-model limits, splitting a PDF a provider rejects, and a default spending
  limit.
- `just` recipes that work on Windows without a POSIX shell, a hosted service, a
  web UI beyond the HTML report, telemetry, and other Level 4 capabilities.

## Work

### 1. Run page-break verification in the pipeline

**Intent:** Make page-break verification part of a default run, after page
extraction, whenever every page of the PDF has a current page file, and give it
the per-step model, instructions and pause that later steps share.

**Done when:**

- `AC-001`: `pydelity <pdf>` and `run()` with default settings run page-break
  verification after page extraction. The CLI and the Python API behave the same
  way.
- `AC-002`: Page-break verification judges every break between consecutive pages
  of the PDF, and it runs only when every page has a current page file: a page
  file that page extraction would reuse now without a model call. It never reads
  a page file that another PDF left in the folder or one made from an older
  survey, other settings or another model.
- `AC-003`: When some pages of the PDF have no current page file after page
  extraction, as can happen when `pages` selects only some pages, the run
  extracts the selected pages, makes no page-break verification request, says
  which pages lack a current page file and how to get verdicts, and does not
  fail. When earlier runs left a current page file for every page the selection
  leaves out, page-break verification judges every break of the PDF.
- `AC-004`: A one-page PDF has no breaks. Page-break verification makes no
  request for it, and the run completes.
- `AC-005`: By default, a run in which page extraction writes at least one new
  page file stops after page extraction, before page-break verification, and
  tells the user how to continue. The next run reuses the page files and goes on
  to page-break verification. A run that reuses every page file goes straight
  on. The existing pause setting (`pause`, `--no-pause`/`-np`) turns this pause
  off as it turns off the pause after the survey.
- `AC-006`: From Python, page-break verification also runs on its own through a
  function with an async version, which never pauses. It reuses a valid matching
  survey and page files, runs what is missing or out of date first, and follows
  the same rule for a narrowed `pages` selection as `run()`.
- `AC-007`: `load(output_dir)` also returns the folder's verdicts, in break
  order, and only those made from the page files it returns.
- `AC-008`: The global `model` setting (and `--model`) chooses page-break
  verification's model unless an optional page-break verification setting under
  `advanced:` overrides it for this step only. With neither set, the step uses
  `anthropic:claude-opus-5-5` at effort `high`, from its own default constant.
- `AC-009`: Page-break verification has its own optional instructions setting
  under `advanced:`, set in the config file or from Python, with no CLI option.
  Its instructions go to page-break verification's model and its verifier and to
  no other step's model, and the step's requests carry no other step's
  instructions. Without the setting, the step sends no instructions.
- `AC-010`: `examples/config.json` and `examples/config.yaml` hold every setting
  the config file accepts, the new ones included, at its default, and pydelity
  reads both without a settings error.

**Depends on:** None.

### 2. Judge each break

**Intent:** Give assembly one verdict per break that says exactly what to join
and how, for any script, layout and writing direction, so that assembly needs no
language rules and builds no duplicate titles or split rows (brief E9).

**Done when:**

- `AC-011`: For each break it judges, page-break verification writes a verdict
  to the output folder that names the break's two pages and says whether any
  content continues from the earlier page to the later one.
- `AC-012`: When content continues, the verdict names each continuing piece by
  the ID of its end on the earlier page and of its start on the later page, with
  the list entry's ID when a list entry continues. One verdict can name more
  than one continuing piece, such as body text and a footnote that both carry
  on.
- `AC-013`: Each continuing piece has a join rule that fits its kind. Text joins
  with a space, with no space, or by removing a line-end hyphen. Code joins with
  a newline and is never dehyphenated. A list continues its last entry or starts
  a new entry. A table appends rows, or merges the split row at the bottom of
  the earlier page with the first row of the later page.
- `AC-052`: When a list carries on across the break and its first entry on the
  earlier page is a text item, as when page extraction read that entry as text,
  the verdict can start a new entry on the later page from that text item.
- `AC-014`: Wherever text continues across the break, whether in a text item, in
  a list entry that continues, or in the cells of a split table row, the verdict
  says how the two pieces of text join (space, no space or removing a line-end
  hyphen, and a newline for code), so that assembly can join them in any script
  without language rules.
- `AC-053`: When a cell in the later part of a split row only repeats the text
  of the cell above it, such as a row label printed again as "PHONICS (contd)",
  the verdict says that the later cell repeats it in place of a text join, so
  that assembly keeps the text once.
- `AC-054`: Page-break verification's instructions to its model say that text or
  a list entry continues only when the break cuts off a sentence, paragraph or
  entry, so that the text itself is unfinished. A paragraph that breaks between
  two sentences, with no new paragraph starting the later page, is unfinished. A
  complete entry followed by an entry with a new number is a new entry.
- `AC-015`: For a table that continues, the verdict gives the number of header
  rows at the top of the later page's table that repeat the earlier table's
  header, `0` when none do.
- `AC-016`: The verdict names the items above the continued unit on the later
  page that repeat what the earlier page printed for that unit, such as a title
  repeated on each page of a multi-page table, so that assembly can drop them.
- `AC-017`: The verdict names any continuation marker on the continued unit,
  such as a heading or row label that says it continues ("(contd)",
  "continued"), with the item or table cell that carries it and the marker's
  text, so that assembly can fold it into the original label.
- `AC-018`: The verdict names each container that continues across the break by
  its ID on both pages, also when the content inside it starts a new unit on the
  later page.
- `AC-019`: A verdict never joins page furniture (items with role `artifact`) to
  content, and page furniture between the two pieces, such as a footer and a
  running header, does not stop content from continuing.
- `AC-020`: Page-break verification handles every writing direction and rotation
  the survey and page extraction handle: right-to-left and vertical text, pages
  whose rotation attribute is 90, 180 or 270, and content turned sideways on
  pages whose attribute is 0. Whatever the model is shown of a page reads
  upright, and the end and start of each page follow its reading order, not its
  top and bottom edges.
- `AC-021`: Page-break verification runs to completion on page files that keep
  failing checks, a `container` or `caption_of` that is `null`, or a column
  order that does not fit the writing direction, and on a survey profile whose
  ranges overlap or run past the PDF or whose artifact mapping misses, repeats
  or invents IDs.
- `AC-022`: Page-break verification's core code, prompts, verdict fields and
  defaults name no document type or domain concept, hold no language-specific
  word lists or patterns, and assume no writing direction.

**Depends on:** 1.

### 3. Check every verdict

**Intent:** Catch verdicts that contradict themselves, the pages or the profile,
treat the survey's continuation findings as hints, flag the breaks where the
optional verifier's independent second judgment disagrees with the first, and
leave a person only what code and two agreeing judgments do not settle.

**Done when:**

- `AC-023`: Before a verdict is accepted, code checks what it can decide, for
  example that every item, entry and container the verdict names exists on the
  page it names, that each join rule fits its item's kind, and that a verdict
  saying nothing continues names no continuing piece. A failed check sends the
  verdict back to the model within the step's check retries, a setting. When the
  retries run out, the last verdict is kept, each check it still fails goes on
  the review list, and the run goes on.
- `AC-024`: Code compares the header rows a verdict counts as repeated with the
  earlier table's header rows. A count whose rows do not repeat that header is a
  check failure or a hint difference, handled as `AC-023` or `AC-056` says.
- `AC-055`: The survey's continuation notes and start markers reach the model as
  hints that its own reading of the pages overrides. A piece whose start on the
  later page begins with one of the survey's start markers is a hint difference,
  unless the piece appends table rows or the verdict names a continuation marker
  in that start. These exceptions rest only on the verdict's own join and
  continuation markers, and they name no document, label or language.
- `AC-056`: A hint difference never sends a verdict back to the model and never
  fails a break, the step or a run. It goes on the review list unless the step's
  verifier ran and its judgment matched the kept verdict, and the verdict file
  keeps it either way. No message, retry messages included, asks the model to
  change its verdict to match a hint.
- `AC-027`: With default settings, page-break verification sends no verifier
  request, the cost ledger has no page-break verifier lines, and each verdict
  file says that no verifier ran.
- `AC-028`: The global `verify` setting (`--verify`/`-vf`, `verify=True`) turns
  on page-break verification's verifier along with every other step's. An
  optional page-break verification setting under `advanced:` (`true`, `false`,
  or `null` to follow `verify`), with no CLI option, overrides it for this step
  only, and `Config` has a `verify_<step>` property for it, as it has for the
  survey and page extraction.
- `AC-057`: With the verifier on, a second request to page-break verification's
  own model judges every break again, the way the first judgment does and
  without seeing the first judgment. Its answer is checked, and sent back within
  the check retries, as the first judgment's is.
- `AC-058`: Code compares a break's two judgments on whether anything continues
  and, for each piece, the items and entries where it ends and starts, its join,
  its text join, its cell joins and its repeated header rows. Repeated items,
  continuation markers and containers are not compared. The first judgment is
  the kept verdict. When the two match, the comparison adds nothing to the
  review list. When they differ, a review issue names each difference, and no
  third request chooses between them.
- `AC-059`: When the verifier ran, the verdict file saves the second judgment
  and the differences between the two judgments, so that how often they differ
  can be measured.
- `AC-031`: Review issues from page-break verification name the step, the
  break's two pages and, where one applies, the item. They are listed in
  `run.json` and in the CLI summary at the end of the run.

**Depends on:** 2.

### 4. Pay for, resume and stop page-break verification

**Intent:** Give page-break verification the run features page extraction has:
cost reporting and control, safe resume, a clear stop on failure and a report a
person can check verdicts in.

**Done when:**

- `AC-032`: Every page-break verification request and verifier request is
  recorded in the cost ledger with its step, its break and its agent, and the
  run reports page-break verification's cost as a step and in the total.
- `AC-033`: The cost estimate the CLI shows before spending, and `estimate()`
  with `aestimate()`, include page-break verification for the breaks the run
  will judge, its verifier only when the verifier will run, and leave the step
  out when the run will not judge breaks. A run whose first request is a
  page-break verification request shows the estimate and asks before that
  request.
- `AC-034`: No run takes the output folder's recorded spend over `max_cost`
  through page-break verification requests without the warning and, in the CLI,
  the question, or in Python, the caller's permission. This holds when several
  of the step's requests run at the same time.
- `AC-035`: Rerunning with unchanged inputs reuses every valid verdict without a
  model call. A break is judged again when anything its verdict is made from
  changes: either of its two page files, the survey findings the step uses, the
  step's instructions, its model, or a setting it uses. Extracting one page
  again re-judges only the breaks on either side of it. `overwrite` re-judges
  every break. A change that affects only page-break verification reruns neither
  the survey nor page extraction.
- `AC-060`: Turning page-break verification's verifier on makes a second
  judgment for each break whose verdict file has none, and keeps that break's
  first judgment without a new request when nothing it is made from changed. A
  change to another step's verifier setting re-judges a break only when that
  step's new output changes what the break's verdict is made from.
- `AC-037`: An interrupted run (an error, a timeout or Ctrl+C) leaves no
  half-written verdict file, and a damaged verdict file is made again on the
  next run.
- `AC-038`: When a page-break verification or verifier request still fails after
  the provider retries, or the model gives an unusable answer, the run stops.
  The CLI shows the error and exits non-zero, and the Python API raises an error
  that carries it. Verdicts already written are kept, and the next run requests
  only the breaks without a valid matching verdict.
- `AC-039`: The HTML report shows each judged break's verdict beside the two
  pages, marking the items and containers it connects, with the join rules, the
  repeated header rows and items to drop, any continuation markers, and the
  verifier's outcome or that no verifier ran. Each review issue about a break
  points at that break.

**Depends on:** 1, 2, 3.

### 5. Test across providers, Python versions and platforms

**Intent:** Prove page-break verification works without paying for model calls,
on every Python version and platform the release supports.

**Done when:**

- `AC-040`: Automated tests cover items 1–4 with both providers' responses
  mocked and no network calls to model providers, using canned page and break
  answers for the PDFs they test. They include a sentence that continues across
  a break, a table that continues with repeated header rows, a repeated title, a
  split row and a continuation marker, a Chinese or Japanese break, a
  right-to-left break, rotated pages, a break where nothing continues, more than
  one continuing piece at one break, page files that break their own rules, the
  rule for a narrowed `pages` selection, the pause, reuse and re-judging after
  one page changes, the verifier off and on with each of its outcomes, hint
  differences that are listed and sent nowhere, a check failure sent back, spend
  control, the stop on a failed request, `load` and the report.
- `AC-041`: CI runs the tests on Python 3.13 and Python 3.14, and "Lint and
  test" and "TruffleHog secret scan" still gate merges to `main`.
- `AC-042`: On Linux, macOS and Windows, the built wheel installs with pip, and
  the `pydelity` command and the Python API run the survey, page extraction and
  page-break verification with mocked model responses.

**Depends on:** 1, 2, 3, 4.

### 6. Prepare release 0.3.0

**Intent:** Ship page-break verification to PyPI as 0.3.0 once the cycle is
signed off and merged.

**Done when:**

- `AC-043`: The built wheel installs with pip into a clean environment and
  provides the package, its runtime dependencies and the `pydelity` command, and
  the wheel and sdist pass a package metadata check.
- `AC-044`: The package description, classifiers and README describe a release
  that surveys a PDF, extracts its pages and verifies its page breaks, with an
  optional verifier for each step.
- `AC-045`: The release setup produces 0.3.0. With the release-please manifest
  at `0.2.0`, this cycle's work reaching `main` as a non-breaking `feat:` commit
  makes release-please open a release pull request for 0.3.0 (tag `v0.3.0`), and
  the GitHub release it creates when accepted starts the PyPI release and the
  docs site's publication of 0.3.0.

**Depends on:** 5.

### 7. Document page-break verification

**Intent:** Let a user run and understand page-break verification, and a
maintainer work on it, from the docs alone.

**Done when:**

- `AC-046`: Following the docs site alone, a user can run page-break
  verification, knows that it needs a current page file for every page and what
  a narrowed `pages` selection does to it, can read the verdict files, verifier
  outcomes, review list and report, can choose the step's model, instructions
  and verifier, controls its spend, and can resume or rerun it. The Python guide
  shows the async functions first.
- `AC-047`: The generated reference pages cover every new setting and public
  Python function, every field of the verdict file and every new or changed
  field of `run.json` and `cost.jsonl`, and page-break verification's checks and
  hints, and they match the code.
- `AC-048`: The README's quick start and every command and code example in the
  README and the docs match 0.3.0's behavior.
- `AC-049`: Under "Pushed to later steps", `artifacts/next_cycle_inputs.md`
  lists any work this cycle moves to a later step, and no longer lists as open
  the step 3 entries this cycle completes.

**Depends on:** 1–6.

### 8. User review of real runs

**Intent:** Confirm page-break verdicts are right on real documents, which
mocked tests cannot show.

**Done when:**

- `AC-061`: The user runs the survey, page extraction and page-break
  verification with default settings, so that no verifier runs, with real
  Anthropic models on PDFs of their choice covering at least one two-column
  right-to-left document, one Chinese or Japanese document, one tax or fillable
  form, one slide deck or image-heavy PDF, and CAPS, reviews the verdicts,
  review lists and HTML reports, and accepts them, with every issue they raise
  resolved.
- `AC-062`: The user runs page-break verification with its verifier on, with
  real Anthropic models on PDFs of their choice, reviews the kept verdicts, the
  differences between the two judgments, the review lists and the HTML reports,
  and accepts them, with every issue they raise resolved.

**Depends on:** 1, 2, 3, 4.

## Retired Acceptance Identifiers

The user's rework of 2026-11-28, after ten real Anthropic runs, replaced these
conditions. The verifier no longer reviews the first verdict. It judges each
break a second time without seeing the first, and code compares the two.

- `AC-025`: Replaced by `AC-055`, which keeps the hints and narrows the
  start-marker hint difference.
- `AC-026`: Replaced by `AC-056`. A hint difference now stays off the review
  list when the verifier ran and its judgment matched, since no verifier passes
  or corrects a verdict any more.
- `AC-029`: Replaced by `AC-057` (the second judgment) and `AC-058` (the
  comparison).
- `AC-030`: Replaced by `AC-059`, which saves the second judgment and the
  differences.
- `AC-036`: Replaced by `AC-060`, which adds a second judgment without judging
  the break a first time again.
- `AC-050`: Replaced by `AC-061`. The user chose real runs with Anthropic models
  only.
- `AC-051`: Replaced by `AC-062`, with Anthropic models only and the two
  judgments' differences in place of the verifier's verdicts.

## Assumptions

- Architect picks the design, with no measured comparison first: the brief's
  options A–C (structure tags as evidence, seam images with item labels,
  windowed verification), alone or combined, or another design. The brief rules
  out code heuristics as the decision (E1), one-page marks as a gate for
  skipping the judgment (E3) and a text-only view without images (E8).
- Architect also decides, with names left for the user's approval: the step's
  noun for outputs, logs, estimates and `advanced:`; the verdict file's layout
  and path (the brief proposes `page_breaks/NNNN-NNNN.json`); the step's other
  settings, such as check retries, effort, output tokens, request timeout and
  how many requests run at once; the fingerprint over the two page files; how
  many breaks one request judges; what `run.json` records for the step; how a
  break is handled when either page has no content items; whether figures,
  fields or formulas can continue; and which comparisons are checks and which
  are hints, `AC-024` included.
- The step is named "verification" and has its own opt-in "verifier", and the
  brief's "verifier" and "validator" mean the step's main request and its second
  request. Architect proposes names that keep these apart.
- Architect decides how the two judgments' pieces are paired for the comparison,
  how a second judgment that still fails a check after its retries is compared
  and listed, and the verdict's value for a cell that only repeats the cell
  above it.
- The user chose on 2026-11-22 that verdicts cover only the whole PDF, so trying
  page-break verification on part of a long PDF needs a cut copy of the PDF, as
  the CAPS test fixture is. A real run of a whole long PDF pays for page
  extraction of every page first.
- With the pauses on, a new PDF takes three runs (survey, page extraction,
  page-break verification) unless the user turns pauses off.
- The user's ten Anthropic runs before the rework cost about $4.36 with the
  verifier off and $7.92 with it on, for 29 breaks over five PDFs, page
  extraction of new pages included. KGForEdGlobal's design judged 99 CAPS breaks
  for $15.25 on Opus 5 with a reviewing request on every break (brief E7).
- Page-break verification's `PROMPT_VERSION` starts at 1 and is not raised
  before 0.3.0. Real runs after a prompt change use new output folders or
  `--overwrite`.

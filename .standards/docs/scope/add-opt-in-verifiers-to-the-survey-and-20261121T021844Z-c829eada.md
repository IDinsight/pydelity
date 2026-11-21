<!-- STANDARDS
Artifact: SCOPE
Cycle: add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada
-->

# Opt-in verifiers for the survey and page extraction, and fixes left from page extraction

## Goal

Release 0.2.0 will ship the survey and page extraction. Page extraction's cycle
is signed off but not merged. This cycle runs on the same branch before
page-break verification, and its work merges with page extraction and ships with
it as 0.2.0.

The cycle does four things:

- First, before the other work, each Python module in the package, the scripts
  and the tests is reordered to the ordering rule that the developer and tester
  user styles now give. The reorder only moves code.
- The survey gets the producer and verifier approach page extraction has. After
  the survey's answer is accepted, a second request to the survey's model
  reviews the answer against the PDF and may return a corrected answer, which is
  kept only if it passes the survey's checks. Code cannot judge everything a
  survey can get wrong, such as a label that does not fit the content, a region
  on the wrong area, page furniture classified as content or a wrong page
  numbering, and every later step relies on the survey's profile.
- Every step's verifier becomes optional and is off by default. The user turns
  it on for every step at once or for one step. A verifier costs real money: in
  the user's real runs it was 28% of page extraction's cost on Anthropic and 35%
  on OpenAI, and a verified survey sends the whole PDF a second time.
- The correctness fixes and docs wording fixes left from page extraction's
  reviews are made.

With the verifiers off, a run checks each answer with code only, and a
difference from the measured facts that no verifier has accepted goes on the
review list.

## Constraints

- Target maturity: Level 3 (internally testable), as for 0.1.0 and page
  extraction.
- Python 3.13 and 3.14 only, with Pydantic, pydantic-settings, PydanticAI,
  loguru, Typer and PyMuPDF 2.x. Models are reached through provider APIs via
  PydanticAI, and every request, the survey's verifier included, must work with
  both Anthropic and OpenAI models.
- One structured-output mode per provider for every request of every step:
  prompted output on Anthropic and native output on OpenAI.
- Document-type agnostic: no core logic, prompt, output field or default may
  assume a document type, a language or a writing direction, and there are no
  language-specific word lists or patterns.
- The model's reading is trusted over measured facts. Code may send an answer
  back with a difference it found, but the model's last answer is kept, and a
  difference left goes on the review list unless that step's verifier passed the
  answer or its correction was kept. The user extended this rule to the survey's
  comparisons with the measured facts on 2026-11-20.
- Each check sits where it can be enforced: Pydantic classes for shape, the
  step's `validators.py` for what code can decide, and the step's verifier for
  what code cannot judge. This replaces the survey cycle's rule that the survey
  uses Python checks only.
- Each step's verifier is a second request to that step's own model, and it gets
  that step's instructions and no other step's.
- PDF transport, whenever a request sends the PDF: upload it with the provider's
  file API, reuse an upload recorded in `uploads.json` while it is usable, and
  send the PDF inside the request only when the upload path fails.
- No per-model limits are checked before a model call, and there is no default
  `max_cost`. When a run would go over `max_cost`, the CLI asks at most once per
  run (`--yes` answers yes), and Python callers pass `allow_over_max_cost=True`
  or get `BudgetExceededError`.
- Every Python function that measures, estimates or runs has an `a`-prefixed
  async version, and `load` stays sync.
- Every CLI option has a short form. New setting, CLI option, file and folder
  names are the user's to approve before the build step that creates them;
  Architect proposes the verifier settings' names.
- `examples/config.json` and `examples/config.yaml` hold every setting at its
  default.
- No backwards compatibility while pydelity has no public users: no aliases,
  deprecation warnings, migrations, or defaults kept only so that old files
  load. As in both earlier cycles, `PROBE_VERSION`, each `PROMPT_VERSION` and
  every output `schema_version` are not raised for this cycle's changes, and an
  old output file that no longer validates is regenerated, as a damaged one is.
  When to start raising them again is not decided here.
- Automated tests mock every model call and make no network calls to model
  providers. Real model runs use the user's own API keys, only with the user's
  go-ahead, and record the spend.
- Test PDFs are real public documents the user approves, under 500 KB each.
- Acceptance rests on the user's review of real runs with Anthropic and OpenAI
  models on PDFs of their choice. Cost is reported with no pass/fail target.
- The repo setup stays as it is unless this work needs a change. Scripts, `just`
  recipes, hooks and CI work without `.standards/`, and "Lint and test" and
  "TruffleHog secret scan" stay required checks on `main`.
- Shipped code, config, docstrings and docs never mention the development
  process: no dates, DEV or AC IDs, cycles, STANDARDS roles, KGForEdGlobal or
  numbered pipeline steps.
- Commits follow Conventional Commits and carry no `Co-Authored-By` trailer or
  other AI attribution. The branch merges to `main` only after this cycle's
  sign-off and STANDARDS Project Uninstallation on the branch, as one
  non-breaking `feat:` commit covering page extraction and this cycle, which
  release-please turns into 0.2.0 (tag `v0.2.0`). In-cycle evidence covers
  release readiness, not the upload or the docs site's deployment.

## Non-goals

- Page-break verification and the later steps, including their verifiers. When
  each is built, its verifier follows this cycle's settings: the global setting
  and an override of its own.
- Changing what page extraction's verifier does when it is on. With it on, pages
  keep 0.2.0's rules for applying the verdict and for listing text differences.
- A verifier that runs on only some pages, on a sample, or only when checks
  fail. A step's verifier runs on all of that step's work or on none of it.
- A separate model, effort or other model setting for the verifiers.
- The remaining issues the user left for later on 2026-11-20:
  - Output limits and leftovers: crops named by item position after an
    interrupted `overwrite`, temporary files in `pages/` and `figures/` removed
    only when a page is extracted, provider image limits missing from the page
    fingerprint, no byte cap on page images, no pixel cap on figure crops, and
    the structure walk's cap.
  - Extraction quality: snapping boxes to the text layer, judging each page's
    stored text, and the page prompt's two box rules.
- Closing any risk under "Risks and follow-up" in
  `artifacts/next_cycle_inputs.md`.
- The page extraction design's wording about how crops are clipped, which sits
  in a signed-off cycle's record.
- Bringing code that this cycle's work does not otherwise change in line with
  the user styles' other updated rules, such as comment wording, American
  English and private names.
- Any change to KGForEdGlobal.
- `just` recipes that work on Windows without a POSIX shell, a hosted service, a
  web UI beyond the HTML report, telemetry, and other Level 4 capabilities.

## Work

### 1. Reorder each module

**Intent:** Put every module in the updated order before the other work changes
it, so that the reorder and this cycle's changes can be reviewed apart.

**Done when:**

- `AC-041`: Every Python module in `src/pydelity/` and `scripts/` follows this
  ordering rule. Module-level constants and type aliases come first, private
  before public. Private classes and functions (names that begin with an
  underscore) come next, then public ones, and inside each class private methods
  come before public ones. Within the private names and within the public names,
  each logical group, such as classes or functions, is in alphabetical order. A
  module departs from the rule only where the rule's order would break execution
  or make the code hard to follow, such as for dependencies, Pydantic validators
  and type definitions. The reorder only moves code, with comments and
  docstrings moving with it. It changes no name or behavior, and the tests, Ruff
  and ty give the same results after it as before.
- `AC-042`: Every Python module in `tests/`, each `conftest.py` included,
  follows the ordering rule in `AC-041`. The reorder only moves code, with
  comments and docstrings moving with it, and the suite runs the same tests with
  the same results after it as before.

**Depends on:** None.

### 2. Turn verifiers on and off

**Intent:** Let the user decide whether to pay for a verifier, for every step at
once or for one step, with no verifier unless they ask for one.

**Done when:**

- `AC-001`: With default settings, neither the survey nor page extraction sends
  a verifier request, and the cost ledger has no verifier lines.
- `AC-002`: One setting turns the verifier on for every step. It is available in
  the config file, as a CLI option with a short form and as a Python keyword.
- `AC-003`: The survey and page extraction each have an optional setting under
  `advanced:` that overrides the global setting for that step only: it turns the
  step's verifier on while the global setting is off, or off while it is on.
  Both are set in the config file or from Python.
- `AC-004`: `examples/config.json` and `examples/config.yaml` hold the new
  settings at their defaults, and pydelity reads both without a settings error.
- `AC-005`: The cost estimate the CLI shows before spending, and `estimate()`
  with `aestimate()`, include a step's verifier requests when that step's
  verifier will run and leave them out when it will not.
- `AC-006`: Turning a step's verifier on reruns that step's outputs that were
  made without one. A change to page extraction's verifier setting never reruns
  the survey. When a change to the survey's verifier setting reruns the survey,
  pages rerun only when the new survey changes what they depend on.

**Depends on:** 1.

### 3. Review the survey with a verifier

**Intent:** Catch survey mistakes that code cannot judge before later steps rely
on the profile, the way page extraction's verifier reviews each page.

**Done when:**

- `AC-007`: With the survey's verifier on, after the survey's answer is accepted
  (its checks pass or its check retries run out), a second request to the
  survey's model, with the survey's instructions, reviews the answer against the
  PDF. The request shows the checks the answer still fails and the answer's
  differences from the measured facts. The verdict says the answer passes, or
  lists the problems found, with a corrected answer when the verifier can give
  one.
- `AC-008`: The verifier may correct any part of the model's answer: the
  profile's labels, languages, writing direction, rotation, page numbering,
  continuation notes and start markers, and the proposal's regions, artifact
  classification and notes. The kept profile still lists the user's languages
  first, and the measured facts are not changed.
- `AC-009`: A correction that fails a survey check is sent back to the verifier
  within the survey's check retries, and a correction is kept only when it
  passes every survey check.
- `AC-010`: When the verdict passes, the survey keeps the answer. When the
  verifier finds problems and its correction is kept, the survey keeps the
  correction and the problems are saved with the verdict only. Otherwise the
  survey keeps the answer and each problem goes on the review list as a survey
  issue.
- `AC-011`: Each survey check still failing on the kept answer goes on the
  review list, as it does without the verifier. The survey's differences from
  the measured facts (`rotation_differs` and `page_number_differs`) go on the
  review list only when the verifier did not run, or found problems and its
  correction was not kept.
- `AC-012`: The verifier request sends the PDF by the PDF transport rule. When
  the upload recorded in `uploads.json` is still usable, the verifier uses it
  and makes no new upload.
- `AC-013`: `pdf_survey.json` saves the verifier's verdict, so that how often
  the verifier finds and fixes problems can be measured, and it says when no
  verifier ran.
- `AC-014`: The HTML report shows the survey verifier's outcome, or that no
  verifier ran.
- `AC-015`: Every survey verifier request is recorded in the cost ledger as a
  survey request made by the verifier, and the run's reported survey cost
  includes it.
- `AC-016`: No run takes the output folder's recorded spend over `max_cost`
  through the survey's verifier requests without the warning and, in the CLI,
  the question, or in Python, the caller's permission.
- `AC-017`: When a survey verifier request still fails after the provider
  retries (a provider error, a timeout or a model refusal), the run stops. The
  CLI shows the provider's error and exits non-zero, and the Python API raises
  an error that carries it.

**Depends on:** 2.

### 4. Extract pages without a verifier

**Intent:** Make page extraction's verifier optional and keep a signal for what
code finds on pages that no verifier reviewed.

**Done when:**

- `AC-018`: With page extraction's verifier off, each page's extraction goes
  through the code checks and their retries and is kept, and no verifier request
  is made for the page.
- `AC-019`: On a page that no verifier reviewed, each check still failing goes
  on the review list, `text_dropped` and `text_added` included. With the
  verifier on, pages follow 0.2.0's rules: text differences are listed only when
  the verifier did not pass the page and the page keeps the extraction.
- `AC-020`: A page file says whether a verifier reviewed the page and holds the
  verdict when one did. For a page that no verifier reviewed, the HTML report
  and the page's log line say that no verifier ran instead of showing a verifier
  outcome.

**Depends on:** 2.

### 5. Fix the correctness issues left from page extraction

**Intent:** Close the confirmed defects that page extraction's reviews left for
later, before 0.2.0 ships them.

**Done when:**

- `AC-021`: `load(output_dir)` returns only the page files that came from the
  PDF the folder's facts describe, and leaves out page files that another PDF
  left in `pages/`.
- `AC-022`: In the HTML report, a table whose header cell has a `row_span`
  reaching past `header_rows` shows every body row's cells in their own columns,
  as the page file holds them.
- `AC-023`: An outline in which an entry's next or first link names an object
  the PDF does not have still yields the bookmarks that can be read, as 0.1.x
  did, instead of none.
- `AC-024`: A form widget written inline in a page's annotations, rather than as
  an object of its own, does not discard the PDF's other form fields.
- `AC-025`: The `TEXT_FLAGS` comment in `src/pydelity/utils/pdf.py` says that
  text is clipped to the CropBox, as PyMuPDF does.

**Depends on:** 1.

### 6. Test across providers, Python versions and platforms

**Intent:** Prove the verifier settings, the survey's verifier and the fixes
without paying for model calls, on every Python version and platform 0.2.0
supports.

**Done when:**

- `AC-026`: Automated tests cover items 2–5 with both providers' responses
  mocked and no network calls to model providers. They include the default with
  no verifier, the global setting and each override, the survey verifier's
  outcomes (passed, correction kept, correction not kept) and their review
  issues, a correction sent back for failing a check, the reuse of a recorded
  upload, page extraction's review list with and without its verifier, the
  estimates with and without verifiers, reruns after turning a verifier on, the
  cost ledger's verifier lines, spend control, the stop on a failed verifier
  request, and each correctness fix.
- `AC-027`: CI runs the tests on Python 3.13 and Python 3.14, and "Lint and
  test" and "TruffleHog secret scan" still gate merges to `main`.
- `AC-028`: On Linux, macOS and Windows, the built wheel installs with pip, and
  the `pydelity` command and the Python API run the survey and page extraction
  with mocked model responses.

**Depends on:** 1, 2, 3, 4, 5.

### 7. Prepare release 0.2.0

**Intent:** Ship page extraction and this cycle's work to PyPI as 0.2.0 once the
cycle is signed off and merged.

**Done when:**

- `AC-029`: The built wheel installs with pip into a clean environment and
  provides the package, its runtime dependencies and the `pydelity` command, and
  the wheel and sdist pass a package metadata check.
- `AC-030`: The package description, classifiers and README describe a release
  that surveys a PDF and extracts its pages, with an optional verifier for each
  step.
- `AC-031`: The release setup produces 0.2.0. With the release-please manifest
  at `0.1.1`, the combined work reaching `main` as a non-breaking `feat:` commit
  makes release-please open a release pull request for 0.2.0 (tag `v0.2.0`), and
  the GitHub release it creates when accepted starts the PyPI release and the
  docs site's publication of 0.2.0.

**Depends on:** 6.

### 8. Document the verifiers and correct the docs wording

**Intent:** Let a user choose and read the verifiers from the docs alone, and
correct the wording that page extraction's final review found looser than the
code.

**Done when:**

- `AC-032`: Following the docs site alone, a user can turn the verifiers on for
  every step or for one step, knows what each verifier reviews and that it adds
  cost, can read the survey's and each page's verifier outcome, and knows which
  differences go on the review list with and without a verifier. No page says
  that a verifier reviews every page by default or that the verifier is a second
  model rather than a second request to the same model.
- `AC-033`: The reference pages cover the new settings, the new CLI option, and
  every new or changed field of `pdf_survey.json`, the page file, `cost.jsonl`
  and `run.json`, and they match the code.
- `AC-034`: The docs and docstrings describe what page extraction sends
  accurately. None says that pydelity sends none of the PDF's stored text, since
  page requests list the page's repeated lines with their stored text and text
  retry messages quote stored lines, and the FAQ's list of what page extraction
  sends includes form field values.
- `AC-035`: The page file reference shows page extraction's own examples for
  `checks[].failures[]` and `issues[].details` and does not say that a failure
  names an item by its answer ref. The `run.json` reference says that
  `steps[].pages` is also `null` for a skipped page extraction step.
- `AC-036`: The other wording that page extraction's final review found is
  corrected:
  - the command-line guide's log example no longer sends the spending question
    to the log, where the command waits with nothing shown;
  - the Python guide says that `load` takes the output folder, not the PDF;
  - `RunResult.pages` is described as what each function returns: the selected
    pages for a run, and the folder's page files for `load`;
  - the costs guide says that requests already in flight may still be billed
    after the user says no;
  - the FAQ names `advanced.uploads.expiry_hours` in full;
  - the reruns guide lists the PDF's hash, not its file name, among the survey's
    inputs, and says that a damaged line in `cost.jsonl` other than the last
    stops every run on the folder with an `OutputError`.
- `AC-037`: The README's quick start and every command and code example in the
  README and the docs match 0.2.0's behavior.
- `AC-038`: Under "Pushed to later steps", `artifacts/next_cycle_inputs.md`
  records that each later step's verifier is opt-in, under the global setting
  and an override of its own, and the file still lists the remaining issues this
  cycle left for later.

**Depends on:** 2, 3, 4, 5.

### 9. User review of real runs

**Intent:** Confirm on real documents, which mocked tests cannot show, that the
survey's verifier helps and that runs without verifiers give a usable review
list.

**Done when:**

- `AC-039`: The user runs the survey and page extraction with default settings,
  so that no verifier runs, with real Anthropic and OpenAI models on PDFs of
  their choice, reviews the review lists and HTML reports, and accepts them,
  with every issue they raise resolved.
- `AC-040`: The user runs the survey and page extraction with both verifiers on,
  with real Anthropic and OpenAI models on PDFs of their choice covering at
  least one two-column right-to-left document, one Chinese or Japanese document,
  one tax or fillable form, one slide deck or image-heavy PDF, and CAPS, reviews
  the survey verdicts, page files, review lists and HTML reports, and accepts
  them, with every issue they raise resolved.

**Depends on:** 2, 3, 4, 5.

## Assumptions

- Architect decides, with names left for the user's approval: the settings'
  shape in detail, how the verifier setting enters each step's fingerprint and
  estimate, whether outputs made with a verifier are reused after it is turned
  off, what the page file's `verification` field and `pdf_survey.json` hold when
  no verifier ran, the survey verifier's prompt and verdict, the expected size
  of its answer in the estimate, and what a failed survey verifier request
  leaves for the next run.
- No measurement of a survey verifier's cost exists yet. Because it sends the
  whole PDF again, a verified survey is expected to cost about twice as much as
  one without the verifier; the real runs will show the actual figure.
- The real runs without verifiers come before the runs with them, so that
  turning the verifiers on reruns the surveys and pages with verifiers.

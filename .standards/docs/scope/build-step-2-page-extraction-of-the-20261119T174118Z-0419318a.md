<!-- STANDARDS
Artifact: SCOPE
Cycle: build-step-2-page-extraction-of-the-20261119T174118Z-0419318a
-->

# pydelity page extraction (step 2) and release 0.2.0

## Goal

pydelity turns (almost) any PDF into faithful, structured JSON through six
steps. Release 0.1.x ships step 1, the survey, which writes a per-PDF profile to
`pdf_survey.json`. This cycle builds step 2, page extraction, and ships it as
0.2.0.

Page extraction reads each selected page, guided by the survey's profile, and
writes a page file that lists the page's items in reading order: text blocks,
lists, tables, figures, form fields and the other kinds pydelity knows, each
with a stable ID, kind, role, label, bounding box in PDF points and content.
Page-break verification and assembly will build on these files, so they must be
faithful to the page in any script, layout and writing direction. Code checks
what it can decide, a second vision model reviews every page for what code
cannot judge, and anything still unresolved goes on the review list.

The cycle extends the run features the survey built to page extraction:
settings, the CLI and Python API, cost reporting and spend control, resume, the
review list and HTML report, tests for both providers, CI, Windows use and the
docs site. It adds a pause between steps, so a user can check the survey's
profile before paying for page extraction, and it fixes the follow-ups that
0.1.0 left open.

## Constraints

- Target maturity: Level 3 (internally testable) for the library, the CLI, the
  release and the docs site, as for 0.1.0.
- Python 3.13 and 3.14 only. Python 3.15 waits until `onnxruntime`, which
  PyMuPDF 2.x requires, ships a 3.15 build. Python 3.14 on a Mac needs macOS 14
  or later.
- Pydantic, pydantic-settings, PydanticAI, loguru, Typer and PyMuPDF 2.x. Models
  are reached through provider APIs via PydanticAI, and page extraction must
  work with both Anthropic and OpenAI models.
- The PDF path is the only required input. Configuration is one optional JSON or
  YAML file with an `advanced:` section. A PDF path given on the CLI is used
  instead of the config file's.
- Document-type agnostic: no core logic, prompt, page file field or default may
  assume a document type, a language or a writing direction. There is no
  hand-written per-document config, no domain Pydantic class and no
  language-specific word list. Document-specific knowledge comes only from the
  survey's profile and the user's instructions.
- The model's reading of a page is trusted over measured facts such as the text
  layer. Code may send an answer back with the difference it found, but the
  model's final answer is kept, and any difference left goes on the review list.
- Each check sits where it can be enforced. What a Pydantic model can check
  stays in the Pydantic classes. What code can check deterministically goes in
  step 2's `validators.py`. What is too complex to check in code is left to the
  verifying vision model.
- Step 2's code sits in its own step folder, `src/pydelity/extracting/`, with
  the same split as `surveying/` (`agents.py`, `llm.py`, `prompts.py`,
  `validators.py`, `schemas.py`). Other new file and folder names are the user's
  to approve before the build step that creates them.
- pydelity keeps no per-model PDF input limits and checks none before a model
  call. The provider's error reaches the user.
- There is no default `max_cost`. When a run would go over it, pydelity warns
  and the user decides whether to continue. The CLI asks, and `--yes` answers
  yes. Python callers pass `allow_over_max_cost=True` or get an error and a run
  they can resume.
- How many times a failed provider request is retried is a setting.
- Every Python function that measures, estimates or runs has an async version
  named with an `a` prefix. `load` stays sync.
- Internal versions stay where they are, because no one uses pydelity yet.
  `PROBE_VERSION`, the survey's `PROMPT_VERSION` and every existing output
  `schema_version` are not raised for this cycle's changes, and output folders
  written by 0.1.x are not migrated. An old file that no longer validates is
  regenerated, as a damaged file is. Step 2's own versions start at 1.
- Automated tests mock every model call and make no network calls to model
  providers. Real model runs use the user's own API keys.
- Test PDFs are real public documents that the user approves, under 500 KB each.
  A copy of an approved test PDF with some pages' rotation attribute changed
  counts as a real test PDF when `tests/fixtures/pdfs/SOURCES.md` says how it
  was made.
- Acceptance of page extraction rests on the user's review of real runs on PDFs
  of their choice. There is no numeric parity target against KGForEdGlobal, and
  cost is reported with no pass/fail target.
- Reuse before rewriting: pydelity ports KGForEdGlobal's page extraction
  (`backend/src/kgfeg/page_ir_extraction/` and the code it uses), reuses what
  fits and writes new code where it does not. Ported code meets every constraint
  here and carries none of the defects listed under "Known defects in the source
  code to design out" in `artifacts/design_brief.md`. KGForEdGlobal
  (`/Users/tzz/Projects/private/idi/KGForEdGlobal`) is read-only.
- The repo setup stays as it is unless this work needs a change: just, prek,
  Dependabot, zizmor, the Markdown rules, exact pins for dev tools, minimum
  versions for runtime dependencies (a new one's minimum is its latest stable
  release on the day it is added), and tooling that works without `.standards/`.
  "Lint and test" and "TruffleHog secret scan" stay required checks on `main`.
- Commits follow Conventional Commits and carry no `Co-Authored-By` trailer or
  other AI attribution. The branch merges to `main` only after the cycle is
  signed off and STANDARDS is uninstalled.
- The release is 0.2.0 (tag `v0.2.0`). Once this cycle is signed off, its work
  reaches `main` as a non-breaking `feat:` commit (the squash-merged pull
  request's title), release-please opens the 0.2.0 release pull request, and
  accepting it publishes 0.2.0 to PyPI and to the docs site. In-cycle evidence
  covers release readiness, not the upload or the deployment.

## Non-goals

- Steps 3–6 and their outputs (page-break verdicts, `document.json`, the domain
  schema and `domain.json`), and the KGForEdGlobal-compatibility outcomes that
  depend on them, such as segment IDs and the item-to-segment lookup.
- Page continuity in step 2. No item or container carries a continuation mark or
  an open-top or open-bottom hint, and step 2 does not judge whether content
  continues across pages (the brief's step 3 option E). Step 3 decides
  continuity, and assembly joins a box that crosses pages into one container.
- Translating extracted text. Revisit it after assembly (step 4) as an optional
  step that translates into a target language the user sets. pydelity serves any
  PDF and any downstream use, so translation is worth having even though
  KGForEdGlobal does not translate, and a consumer like KGForEdGlobal can leave
  it off.
- Any change to KGForEdGlobal, and KG, Learning Component or Learning
  Progression logic.
- Shipping per-model PDF input limits, checking a PDF against them, and
  splitting a PDF a provider rejects.
- A default spending limit.
- Migrating output folders written by 0.1.x.
- just recipes that work on Windows without a POSIX shell. Windows support means
  installing and using pydelity.
- A hosted service, a web UI beyond the HTML report, telemetry, and other Level
  4 capabilities such as structured audit logging and staging environments.

## Work

### 1. Choose pages, model and pauses

**Intent:** Let a user say which pages to extract and with which model, and stop
after the survey to check the profile before paying for page extraction. Later
steps will pause the same way, controlled by the same setting.

**Done when:**

- `AC-001`: A `pages` setting, available in the config file, as a CLI option
  with a short form and as a Python keyword, selects the pages to extract. Pages
  are numbered from 1, as a PDF viewer shows them, and a selection lists single
  pages and ranges, such as `1-5,8`. Without the setting, every page is
  extracted. The survey reads the whole PDF whatever the selection.
- `AC-002`: A `pages` value that is malformed or names a page outside the PDF
  stops the run before any model call, with a message naming the setting.
- `AC-003`: By default, a run that writes a new survey stops after the survey,
  before page extraction, and tells the user how to continue. The next run
  reuses the survey and goes on to page extraction. The CLI and the Python API
  behave the same way.
- `AC-004`: A setting, available in the config file, as a CLI option with a
  short form and as a Python keyword, turns the pauses off, so one run goes
  through the survey and page extraction without stopping.
- `AC-005`: The global `model` setting (and `--model`) chooses the model for
  every step. An optional page extraction setting under `advanced:` overrides it
  for page extraction only. With neither set, page extraction uses its own
  default model.
- `AC-006`: `examples/config.json` and `examples/config.yaml` hold every setting
  the config file accepts, including the new ones, at its default, and pydelity
  reads both without a settings error.

**Depends on:** None.

### 2. Extract each page

**Intent:** Turn each selected page into a faithful list of items that later
steps can join, cite and check, whatever the page's script, layout and writing
direction.

**Done when:**

- `AC-007`: For each selected page, step 2 writes a page file that lists the
  page's items in reading order. Each item has an ID, a kind and a role from
  pydelity's item vocabulary, a label from the survey profile's labels whose
  role and kinds match the item, a bounding box, and content.
- `AC-008`: Item IDs are unique across the PDF, and writing the same extraction
  of a page again gives its items the same IDs.
- `AC-009`: Bounding boxes are in PDF points on the displayed page, with the
  origin at the top left, as the survey's regions and form fields are, and each
  box covers its item's content.
- `AC-010`: Reading order follows the page's writing direction from the profile.
  Multi-column pages are read column by column, right-to-left pages starting
  from the right-hand column, and vertical text in its own column order. This
  holds on test PDFs with two- and three-column right-to-left text, two- and
  three-column Chinese, vertical Japanese and two-column left-to-right text.
- `AC-011`: Rotated content is read upright. On pages whose rotation attribute
  is 90, 180 or 270, and on pages whose content is turned sideways while the
  attribute is 0 (such as CAPS's sideways tables), item text reads upright and
  each box lands on its content in the displayed page's coordinates. This holds
  on a test PDF with pages at each of the three rotation attributes and on CAPS.
- `AC-012`: Each item's content fits its kind. Text is transcribed as printed,
  each list item is a separate entry with its own ID, tables keep their rows,
  cells, row and column spans and header rows, formulas have a text form such as
  LaTeX, code keeps its whitespace and line breaks, and fields keep their
  values.
- `AC-013`: Each figure is saved as an image crop in the output folder, and its
  item names the crop file.
- `AC-014`: Each caption item names the item it captions.
- `AC-056`: Bordered or shaded boxes are recorded as containers. Each container
  has an ID and a bounding box, and items inside a box keep their own kind and
  role and name their container.
- `AC-016`: Form fields and checkboxes are field items that carry their values:
  the values of fillable fields, including checked or unchecked checkboxes and
  radio buttons, and values written or marked on forms that are only printed or
  scanned.
- `AC-017`: A page that is one figure, such as a slide, a poster or a full-page
  image, is accepted as a single figure item. It is not sent back or put on the
  review list for being one figure.
- `AC-018`: Page furniture such as running headers, footers and page numbers is
  extracted as items with the artifact role.
- `AC-019`: Step 2 runs to completion on a survey whose page ranges overlap,
  leave gaps or run past the PDF, or whose artifact classification misses,
  repeats or names unknown repeated lines, as a survey can when its check
  retries run out.
- `AC-020`: Core code, prompts, page file fields and defaults name no document
  type or domain concept, hold no language-specific word lists or patterns, and
  assume no writing direction.

**Depends on:** None.

### 3. Check every page

**Intent:** Catch dropped, invented or misplaced content before a page file is
kept, using code where code can decide and a vision model where it cannot, and
leave a person only what neither resolves.

**Done when:**

- `AC-021`: Before a page's answer is accepted, code checks what it can decide,
  for example that labels, roles and kinds agree with the profile, that boxes
  sit inside the page, and that the reading order fits the page's writing
  direction, including right-to-left and vertical pages. A failed check is sent
  back to the model, up to a number of check retries set by a setting. When the
  retries run out, the last answer is kept and each check still failing goes on
  the review list.
- `AC-022`: On pages with a good text layer, the text of the page's items is
  compared with the text layer in any script, including scripts written without
  spaces between words, so that text dropped from the page or added to it is
  found. On test pages in Arabic, Chinese, Japanese and English, removing a line
  from a correct answer or adding one to it is caught.
- `AC-023`: A text difference is sent back to the model within the check
  retries, telling it that it may keep its reading when the text is not visible
  on the page or was read from an image. Differences left after the retries go
  on the review list. Pages whose text layer is missing or garbled skip the
  comparison, and their page file says so.
- `AC-024`: After the code checks, a second vision-model pass reviews every
  extracted page against the page image for problems code cannot judge, such as
  missed, merged or misclassified items, a wrong reading order in a complex
  layout, or boxes on the wrong content. When it finds problems, the page file
  holds a corrected extraction that passes the code checks, or the problems go
  on the review list.
- `AC-025`: Every verifier verdict is saved in the output folder with its page,
  so that how often the verifier finds and fixes problems can be measured.
- `AC-026`: Review issues from page extraction name the step, the page and,
  where one applies, the item. They are listed in `run.json` and in the CLI
  summary at the end of the run.

**Depends on:** 2.

### 4. Run, pay for and resume page extraction

**Intent:** Give page extraction the run features the survey has: CLI and Python
use, cost control, safe resume and a clear stop on failure. Pages are
independent, so several run at the same time to finish a long PDF sooner.

**Done when:**

- `AC-027`: `pydelity <pdf>` and `run()` include page extraction as item 1
  describes. From Python, page extraction also runs on its own through a
  function with an async version, which reuses a valid matching survey or runs
  the survey first, and `load(output_dir)` reads the page files back.
- `AC-028`: Every page extraction and verifier request is recorded in the cost
  ledger, and the run reports its cost per step and in total.
- `AC-029`: The cost estimate the CLI shows before spending, and `estimate()`
  with `aestimate()`, cover the steps the run will perform, including page
  extraction of the selected pages and its verifier.
- `AC-057`: A setting controls how many pages are extracted at the same time,
  with a default of 8. A run never has more pages in extraction at once than the
  setting allows.
- `AC-058`: Each page extraction request and each verifier request sends one
  page. Several pages run at the same time as separate requests.
- `AC-030`: No run takes the output folder's recorded spend over `max_cost`
  without the warning and, in the CLI, the question, or in Python, the caller's
  permission. This holds when requests send page images and when several page
  requests run at the same time.
- `AC-031`: Rerunning with unchanged inputs reuses every valid page file without
  a model call. A page reruns when anything its extraction depends on changes:
  the PDF, the survey's profile or artifact classification, the instructions,
  the model, or a setting page extraction uses. Selecting more pages extracts
  only the newly selected ones. `overwrite` reruns every selected page. A change
  that affects only page extraction does not rerun the survey.
- `AC-032`: An interrupted run (an error, a timeout or Ctrl+C) leaves no
  half-written page file or figure crop, and a damaged page file is regenerated
  on the next run.
- `AC-033`: When a page's request still fails after the provider retries (a
  provider error, a timeout or a model refusal), the run stops. The CLI shows
  the provider's error and exits non-zero, and the Python API raises an error
  that carries it. Page files already written are kept, and the next run
  requests only the pages without a valid matching page file.
- `AC-034`: The HTML report shows each extracted page's image with every item's
  box drawn and numbered in reading order, beside a list of the page's items
  with their ID, kind, role, label, content and, for figures, the crop.
  Containers are shown, and each review issue about an item points at that
  item's box.

**Depends on:** 1, 2, 3.

### 5. Fix 0.1.0's open follow-ups

**Intent:** Close the issues the survey cycle left open, several of which affect
what page extraction reads.

**Done when:**

- `AC-035`: Form-field facts read a checked checkbox that has no normal
  appearance, and one unreadable widget does not discard the other fields. A
  radio group whose buttons are all off but whose value is set reads that value.
- `AC-036`: Letter-style page labels, such as `A`, `B` and `C`, are read as
  letters, not as roman numerals.
- `AC-037`: Structure-tag quality follows structure elements whose children are
  an indirect reference to an array. A walk that stops at its element cap does
  not count the pages it did not reach as untagged, and tagged pages without
  text do not count toward structure coverage.
- `AC-038`: An outline whose next-links form a cycle yields the bookmarks before
  the cycle, not none.
- `AC-039`: `run.json` records the PDF transport of a failed step once a request
  carried the PDF.
- `AC-040`: The Python API does not print PydanticAI's first-run banner.
- `AC-041`: A cache price of `0` under `advanced.models` is priced as zero, not
  as the input price.
- `AC-042`: CI's check for stale reference pages fails when a newly generated
  page is left untracked. `docs.yml` describes its caching accurately, and its
  plan step does not hide errors from `node`.
- `AC-043`: `CHANGELOG.md`'s 0.1.0 entry links commit `c63d891` instead of
  `d13c0fd`, and `pyproject.toml` no longer holds the scaffold coverage entries
  (the `def cli` exclusion and the `./src/pydelity/__init__.py` omit).
- `AC-044`: The docs wording issues found in 0.1.0's final review are corrected:
  how to republish the docs site, formatting after `just docs-reference`, what
  `--randomly-seed` repeats, how many pull requests Dependabot opens, which
  hooks check the whole tree, which commit types make a patch release, when the
  docs build runs on pull requests, and which settings rerun the survey
  according to `faq.md`.

**Depends on:** None.

### 6. Test across providers, Python versions and platforms

**Intent:** Prove page extraction and the fixes work without paying for model
calls, on every platform and Python version the release supports.

**Done when:**

- `AC-045`: Automated tests cover what code can check in items 1–5, including
  page selection, the pause and its setting, the model override, page files for
  each writing direction and rotation, crops, captions, containers, fields,
  one-figure pages, the code checks and text comparison, the verifier, spend
  control with page requests running at the same time, resume, the stop on a
  failed page, review issues that name items, the report and each follow-up fix,
  with both providers' responses mocked and no network calls to model providers.
- `AC-046`: CI runs the tests on Python 3.13 and Python 3.14, and "Lint and
  test" and "TruffleHog secret scan" still gate merges to `main`.
- `AC-047`: On Windows, the built wheel installs with pip, and the `pydelity`
  command and the Python API run the survey and page extraction with mocked
  model responses.

**Depends on:** 1, 2, 3, 4, 5.

### 7. Prepare release 0.2.0

**Intent:** Ship page extraction to PyPI as 0.2.0 as soon as the cycle is signed
off and merged.

**Done when:**

- `AC-048`: The built wheel installs with pip into a clean environment and
  provides the package, its runtime dependencies and the `pydelity` command, and
  the wheel and sdist pass a package metadata check.
- `AC-049`: The package description, classifiers and README describe a release
  that surveys a PDF and extracts its pages.
- `AC-050`: The release setup produces 0.2.0. With the release-please manifest
  at `0.1.1`, this cycle's work reaching `main` as a non-breaking `feat:` commit
  makes release-please open a release pull request for 0.2.0 (tag `v0.2.0`), and
  the GitHub release it creates when accepted starts the PyPI release and the
  docs site's publication of 0.2.0.

**Depends on:** 6.

### 8. Document page extraction

**Intent:** Let a user run and understand page extraction, and a maintainer work
on it, from the docs alone.

**Done when:**

- `AC-051`: Following the docs site alone, a user can select pages, run the
  survey and page extraction with and without the pause, choose the page
  extraction model, find and read the page files, figure crops, verifier
  verdicts, review list and HTML report, control spend for page extraction, and
  resume or rerun a run.
- `AC-052`: The reference pages cover every setting, CLI option and public
  Python function, including the new ones, and every field of the page file and
  of the changed `run.json`, and they match the code.
- `AC-053`: The README's quick start and every command and code example in the
  README and the docs match 0.2.0's behavior.

**Depends on:** 1–7.

### 9. User review of real page extraction runs

**Intent:** Confirm page extraction is faithful on real documents, which mocked
tests cannot show.

**Done when:**

- `AC-054`: The user runs the survey and page extraction with real Anthropic and
  OpenAI models on PDFs of their choice, including at least one two-column
  right-to-left document, one Chinese or Japanese document, one tax or fillable
  form, one slide deck or image-heavy PDF, and CAPS, reviews the page files and
  the HTML report, and accepts them, with every issue they raise resolved.

**Depends on:** 1, 2, 3, 4.

## Retired Acceptance Identifiers

- `AC-015`: Retired by user rework. Containers no longer say whether they are
  open at the top or the bottom of the page, because step 2 records no page
  continuity; replaced by `AC-056`.

## Assumptions

- Architect decides the page file's layout and location, the final item `kind`
  and `role` lists, the rendering resolution, how the verifier's corrections are
  applied, whether items carry a language tag or a later adapter fills it from
  the profile's languages, what happens to pages still in extraction when one
  page fails, any per-model image limit, and page extraction's default model and
  per-page settings. Copied per page, the survey's default of 32,000 output
  tokens would bring the `max_cost` question on nearly every run, so page
  extraction needs its own defaults.
- Step 2's prompt version starts at 1 and is not raised before 0.2.0. Reruns
  during development use `overwrite`.
- Narrowing the `pages` selection leaves the page files of pages no longer
  selected in the output folder.
- The pause comes only after a step that ran in the current run, so a run that
  reuses the survey goes straight on to page extraction.

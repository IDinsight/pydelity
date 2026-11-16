<!-- STANDARDS
Artifact: SCOPE
Cycle: build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de
-->

# pydelity: repo setup and PyPI name

## Goal

pydelity will be a standalone Python package and CLI that turns (almost) any PDF
into faithful, structured JSON (`document.json`, optionally `domain.json`). The
full request is in `artifacts/design_brief.md`. Publishing it to PyPI is a
project goal.

This cycle does two things. It gets the repo into shape for a Python 3.13
library with a Typer CLI that ships to PyPI, clearing out the leftovers of the
KGForEdGlobal scaffold it was copied from. And it reserves the name `pydelity`
on PyPI as early as possible with a placeholder release, so no one else takes
it.

The PDF pipeline itself (steps 1–6 of the brief) is the next cycle. On
2026-11-16 the user split it out so the name could be reserved without waiting
for the whole pipeline to be designed. What this cycle had already scoped for
the pipeline, and the user's answers to the brief's open questions, are kept
under **Deferred to the Next Cycle** as input for that cycle. None of it is part
of this cycle.

## Constraints

- Python 3.13 library with a Typer CLI. The package and the PyPI project are
  both named `pydelity`.
- Repo setup is interactive: the user points out what to change, and Developer
  proposes and makes each change, without a pre-planned exhaustive list.
- Package code stays limited to empty modules and a smoke test. The STANDARDS
  files (`.standards/`, `.agents/`, `.claude/skills`, `AGENTS.md`, `CLAUDE.md`)
  stay unchanged, with one exception the user chose on 2026-11-16: Markdown
  linting and formatting cover every Markdown file, STANDARDS ones included,
  because the changes they make there are cosmetic. The protocol treats shipped
  framework files as changed only by installation or upgrade; the user accepts
  cosmetic formatting of them anyway.
- The PyPI project belongs to the user's PyPI account. Upload credentials never
  enter the repo, and nothing is uploaded to PyPI without the user's go-ahead
  for that upload.
- KGForEdGlobal (`/Users/tzz/Projects/private/idi/KGForEdGlobal`, commit
  `5e2d7cc`) is read-only reference material.

## Non-goals

- Pipeline code (steps 1–6) and everything listed under **Deferred to the Next
  Cycle**.
- A usable package on PyPI. The placeholder only reserves the name.
- Any change to KGForEdGlobal.

## Work

### 1. Repo setup

**Intent:** The scaffold came from KGForEdGlobal and still carries its leftovers
(web-app and KG settings, Docker targets, unused dependencies). Get the files
and folders into shape for a Python 3.13 library with a Typer CLI that ships to
PyPI: READMEs, `pyproject.toml`, Makefiles, env templates and `.envrc`,
`.gitignore`, pre-commit, CI workflows, and the folder layout (including whether
`backend/` stays or the package moves to the repo root).

**Done when:**

- `AC-001`: On a clean checkout, `make install`, every lint target, `make test`
  (running at least one smoke test of the package) and
  `pre-commit run --all-files` all succeed.
- `AC-002`: The user has signed off the repo setup before any pipeline code is
  written.
- `AC-041`: The Markdown lint and format checks cover every Markdown file in the
  repo, including those under `.standards/`, `.agents/` and `.claude/skills` and
  `AGENTS.md` and `CLAUDE.md`. Any change they make to a STANDARDS file is
  whitespace or line wrapping only, and `node .standards/bin/check.mjs` still
  passes afterwards. Other formatters, linters and hooks leave STANDARDS files
  unchanged.

**Depends on:** None.

### 2. Reserve the name on PyPI

**Intent:** Own `pydelity` on PyPI before anyone else can take it. This is one
of the first repo-setup tasks; it needs only enough packaging to build an
installable placeholder, not a working package.

**Done when:**

- `AC-040`: A `pydelity` release is published on PyPI under the user's account.
  Its project page says the package is under development and not yet usable, and
  `pip install pydelity` in a fresh Python 3.13 environment installs it.

**Depends on:** None. Done as early in repo setup as the packaging allows.

## Retired Acceptance Identifiers

All of these moved to the next cycle when the user split out the pipeline on
2026-11-16. Their text is kept under **Deferred to the Next Cycle**.

- `AC-003`: Survey (step 1) output.
- `AC-004`: User sign-off of step 1.
- `AC-005`: Page extraction (step 2) items and reading order.
- `AC-006`: Figures, captions, form fields and single-figure pages.
- `AC-007`: Dropped or invented text caught in any script.
- `AC-008`: User sign-off of step 2.
- `AC-009`: Page-break (step 3) verdicts.
- `AC-010`: User sign-off of step 3.
- `AC-011`: Assembly (step 4) output and provenance.
- `AC-012`: Outline and `section_path`.
- `AC-013`: Boxes as containers.
- `AC-014`: Table grid and fill-down.
- `AC-015`: User sign-off of step 4.
- `AC-016`: Domain schema (step 5) output.
- `AC-017`: User sign-off of step 5.
- `AC-018`: Projection (step 6) output.
- `AC-019`: Coverage report.
- `AC-020`: User sign-off of step 6.
- `AC-021`: Default run with no config file.
- `AC-022`: Optional config file.
- `AC-023`: Library use without the CLI.
- `AC-024`: Wheel installs and provides the CLI.
- `AC-025`: Cost ledger and report.
- `AC-026`: Cost estimate and confirmation.
- `AC-027`: max_cost.
- `AC-028`: Survey model PDF input limits.
- `AC-029`: Resume after a stop.
- `AC-030`: Reruns after changed inputs.
- `AC-031`: Anthropic and OpenAI models.
- `AC-032`: Mocked automated tests.
- `AC-033`: Review list in `run.json`.
- `AC-034`: HTML review report.
- `AC-035`: No document-type assumptions.
- `AC-036`: Segment IDs, PDF points and item-to-segment lookup.
- `AC-037`: Data for the KG stage's fields and box shape.
- `AC-038`: Written KG field mapping.
- `AC-039`: README for pipeline use.

## Assumptions

- How the placeholder is built and uploaded (by hand or through a CI workflow)
  is for Architect and Developer to decide.
- The placeholder's version number leaves room for the working release to sort
  above it, since PyPI never lets a version number be reused.

## Deferred to the Next Cycle

Input for the next cycle's Scoper. This is not part of this cycle and holds no
current obligations; the next cycle numbers its own acceptance conditions.

### User decisions made while scoping the pipeline

- Acceptance rests on the user's sign-off of each build step. The user runs the
  relevant commands on PDFs of their choice, reviews the output, and asks the
  owning role when something needs explaining or reviewing. No numeric parity
  with today's pipeline, and cost is reported with no pass/fail target.
- New document types to handle and try: two-column right-to-left, Chinese or
  Japanese, tax or fillable form, slide deck or image-heavy.
- A default run goes through all six steps, with a setting to stop after
  `document.json`.
- The CLI shows a cost estimate and asks before spending; `--yes` skips the
  question. There is no default max_cost.
- The review list goes to `run.json`, a CLI summary and an HTML report.
- Bordered or shaded boxes become containers.
- The PDF path comes from the CLI or the config file; the CLI wins.
- A survey model with no known PDF limits gets a warning and the call proceeds;
  the user can set limits under `advanced:`.
- Anthropic and OpenAI models must both work. Automated tests mock model API
  calls.
- Architect picks the step 3 design (no comparison gate), the final `kind` and
  `role` lists, and the default model for each step.
- The working pydelity is published to PyPI when the pipeline is signed off.

### Constraints, non-goals and assumptions scoped for the pipeline

- Constraints: Python 3.13 with Pydantic, pydantic-settings, PydanticAI, loguru
  and Typer. Models reached through provider APIs via PydanticAI. The PDF path
  is the only required input, configuration is one optional JSON or YAML file,
  and a normal run resumes. No hand-written per-document config or domain
  Pydantic classes, and no core logic, prompt, schema field or default that
  assumes a document type. The domain schema is JSON Schema data with `x-key`
  and `x-verbatim`, never Python source. Consumer-specific needs go in
  `document.json` fields or the consumer's adapter. The brief's design
  directions are input for Architect, and evidence E1–E23 illustrates rather
  than specifies.
- Non-goals: any change to KGForEdGlobal; KG, Learning Component and Learning
  Progression logic; generating KG config from a pydelity schema; automatic
  splitting or a chunked survey for PDFs over the survey model's input limits;
  continuity judged inside step 2 (step 3 option E); a measured comparison of
  step 3 designs; a default spending limit; a hosted service, web UI beyond the
  HTML report, telemetry and other Level 4 features.
- Assumptions: Level 3 (internally testable) maturity. Test PDFs for the new
  document types are public documents chosen with the user's approval. A
  user-supplied domain schema does not seed page-profile labels, so changing it
  reruns only steps 5–6. Real model runs use the user's own API keys.

### Pipeline outcomes scoped in this cycle before the split

- Survey (step 1), was AC-003: given only a PDF, plus optional instructions and
  languages, step 1 writes `pdf_survey.json`, holding facts measured from the
  PDF without a model (text-layer quality per page, bookmarks, form fields,
  structure tags, repeated lines, text direction per page, printed page numbers)
  and a model-proposed profile checked against them: per-PDF labels mapped to
  one role and allowed kinds and always including `other`, languages, writing
  direction, rotation per page range, continuation notes and start markers. User
  inputs add to the profile but never bypass its checks.
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
- User sign-off of each step's output, was AC-004, AC-008, AC-010, AC-015,
  AC-017 and AC-020.
- Configuration, CLI and library use, was AC-021 to AC-024: `pydelity <pdf>`
  runs with no config file; an optional JSON or YAML file sets the PDF path and
  the global settings, with an `advanced:` section; the CLI's PDF path wins;
  invalid settings stop the run with a message naming them. The pipeline and
  each step run from Python without the CLI, and importing needs no environment
  settings and logs nothing unless asked. A built wheel installs with pip and
  provides the package and the `pydelity` command.
- Cost and spend controls, was AC-025 to AC-028: a per-call cost ledger and
  per-step and total cost per run; the CLI's estimate-and-confirm prompt with
  `--yes`, stopping non-interactive runs without it, and no prompt from the
  Python API; max_cost counting all spend in the output folder, including
  resumed runs, and stopping in a resumable state; a check of the whole PDF
  against the survey model's PDF input limits before any model call, with a
  clear error, known limits for default and documented models, overrides under
  `advanced:` and a warning for unknown models.
- Resume and reruns, was AC-029 and AC-030: a stopped run resumes and redoes
  only unfinished outputs, with no half-written files and damaged files
  regenerated; a changed input reruns its outputs and everything downstream, and
  nothing else; `overwrite` reruns everything.
- Providers and tests, was AC-031 and AC-032: every step works with Anthropic or
  OpenAI models chosen by setting; the automated tests cover every step and both
  providers with mocked responses and no network calls to model providers.
- Review list and HTML report, was AC-033 and AC-034: issues left after retries
  go to `run.json` with step, page, item and failed check, a CLI summary, and an
  HTML report with page images and item boxes.
- No document-type assumptions, was AC-035: core code, prompts, page-schema
  fields and defaults name no document type or domain concept, hold no
  language-specific word lists, and contain no per-document rules or domain
  Pydantic classes.
- KGForEdGlobal compatibility, was AC-036 to AC-038: segment IDs follow today's
  recipe and are stable across reruns, boxes are in PDF points, and an item ID
  to segment ID lookup is included; `document.json` holds the data an adapter
  needs for each KG field in use today and for CAPS requirement boxes as
  one-column tables; a written mapping documents where each comes from.
- User documentation, was AC-039: a README that lets another engineer install
  pydelity, set provider keys, run it, find outputs, read the review list and
  reports, and resume or rerun.

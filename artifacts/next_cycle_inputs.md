# pydelity: inputs for the pipeline cycle

The repo setup and the `0.0.1` placeholder release were scoped, built and signed
off in an earlier STANDARDS cycle
(`build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de`, branch
`tz6/port-over`). STANDARDS was then uninstalled so the setup could merge to
`main`, which removed that cycle's records. This file keeps what the next cycle
needs from them:

- the scope's **Deferred to the Next Cycle** section, copied unchanged below the
  first three headings;
- the design's **Risks and Follow-up** section;
- loose ends that were still open at sign-off.

The full request, design directions and evidence E1–E23 are in
`artifacts/design_brief.md`. Its "First work item: repo setup" section is done
and its "done when" line names the retired Make and pre-commit commands; the
repo now uses just and prek. Its open questions are answered under **User
decisions made while scoping the pipeline** below.

Nothing here is an acceptance condition. The old AC numbers (AC-003 to AC-039)
are retired; the next cycle numbers its own.

## Deferred from the repo-setup scope

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
- Added 2026-11-16, after the placeholder release: people must be able to
  install and use pydelity on Windows.

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

### Pipeline outcomes scoped before the split

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

## Risks and follow-up from the repo-setup design

- Dependabot's uv can lag behind the uv people use. If it falls below
  `required-version`, uv updates fail until the bound is lowered. A lock written
  by a different uv patch release may also differ slightly; CI's `--locked`
  check shows it on the Dependabot pull request.
- Dependabot's uv updater raises lower bounds it touches, so it may propose
  raising `setuptools>=77` in `[build-system]`. That bound is set by what the
  build needs; if Dependabot proposes raising it, add an ignore with a comment
  rather than accepting it.
- Hand-kept pins (the uv bound, CI's uv, Node's `language_version`, prettier) go
  stale unless someone bumps them. A prettier bump can reformat many files at
  once (3.6.2 and 3.10.1 already differ on `AGENTS.md` and `CLAUDE.md`).
- With the job token, zizmor's online audits can fail CI when an advisory is
  published for an action the repo uses, with no repo change. That is intended;
  the fix is a Dependabot or hand update of the action.
- The `auditor` persona allows false positives; each one costs a written ignore.
  With two workflows, that is cheap.
- prek is pre-1.0 (0.5.x). Its behaviour may shift between releases;
  Dependabot's cooldown and the CI run on its pull requests limit the surprise.
- Markdown formatting covers STANDARDS files too, which departs from the
  protocol rule that only installation or upgrade changes shipped framework
  files; the user accepted this during the repo setup. If a STANDARDS release
  ships files prettier would rewrap, they will differ from upstream (whitespace
  only) until the next upgrade replaces them.
- Role-written records that prettier would change beyond whitespace stay
  unformatted and show up as warnings until their owning role rewrites them. A
  markdownlint violation in a new record fails the prek run until its owner
  fixes it or the config is tuned.
- PyPI versions are permanent. A mistake in `0.0.1` can only be fixed with
  `0.0.2`.
- `>=3.13` lets Python 3.14 users install versions tested only on 3.13. The next
  cycle can add 3.14 to CI.
- Next cycle: runtime dependencies, the Typer CLI and its console script, a
  release workflow with Trusted Publishing (which zizmor will also check),
  whether to yank the placeholder after the working release, and Windows
  support, which will need recipes that do not assume a POSIX shell.

## Loose ends from the repo setup

Context, not requirements.

- The README doesn't say the `just` recipes need bash.
- Node `24.22.3` is written in two hooks in `.pre-commit-config.yaml`, so a
  version bump has to change both.
- `[tool.coverage.report]` in `pyproject.toml` still holds scaffold entries: a
  `def cli` exclusion and an `omit` for `src/pydelity/__init__.py`.

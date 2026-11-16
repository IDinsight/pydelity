# Request: pydelity — generic PDF → structured JSON package (redesign of KGForEdGlobal stages 1–3)

## Terminology

General

- Today / current: KGForEdGlobal at the pinned commit (5e2d7cc). "New" means the
  pydelity design.
- Document: the whole PDF as pydelity represents it in document.json, faithful
  to the source and free of domain meaning (no grades, tax lines, etc.).
- Domain: what a document is about and how its content is organized for a use
  case (e.g., a curriculum's grade → term → skill hierarchy). Domain structure
  lives only in the domain schema and domain.json, never in the page schema.
- Provenance: where each piece of output came from: page, item ID, bounding box,
  and for domain output, the cited item IDs (`source`).
- Consumer: a downstream system that reads pydelity output (first one:
  KGForEdGlobal's KG stage).
- Adapter: consumer-owned code that converts pydelity output into the consumer's
  shapes. It lives in the consumer's repo, not in pydelity.

Pages and items (steps 1–2)

- Page index: 0-based position of a page in the PDF. Printed page number: the
  number printed on the page; the two differ by an offset (e.g., front matter).
- Text layer: the text embedded in the PDF, read by Python (PyMuPDF). Missing on
  scanned pages, and sometimes garbled.
- Structure tags: optional logical structure in "tagged" PDFs (e.g., headings,
  paragraphs, tables that span pages). Quality varies widely.
- Survey: step 1. One model call over the whole PDF plus Python facts, producing
  pdf_survey.json.
- Profile: the part of pdf_survey.json that later steps depend on: e.g., labels,
  rules, languages, direction, rotation per page range, continuation notes,
  start markers.
- Item: the smallest unit extracted from one page (e.g., a text block, list,
  table, figure or form field), with a stable item ID, kind, role, label and
  bounding box.
- Kind: what an item is structurally (e.g., text, list, table, figure, field;
  maybe formula).
- Role: what an item does in the document (e.g., heading, caption, footnote,
  artifact, navigation, body; maybe aside).
- Label: a per-PDF name from the profile's closed list (always including
  `other`); each label maps to one role and its allowed kinds.
- Artifact: page furniture repeated across pages (e.g., running headers,
  footers, page numbers). Dropped from the reading flow unless
  keep_headers_footers is set.
- Container: a bordered or shaded box whose items keep their own kinds
  (proposed; open question 10).
- Bounding box (bbox): an item's rectangle, in PDF points in pydelity (today:
  pixels at 250 DPI).

Page breaks and assembly (steps 3–4)

- Page break (break): the boundary between page N and page N+1.
- Continuation: an item at the end of page N that carries on at the start of
  page N+1.
- Verdict: step 3's decision for one break: whether it continues, which items
  connect, the join rule, repeated header rows and repeated items.
- Join rule: how two halves combine (e.g., text: space / no space / dehyphenate;
  list: continue item / new item; table: append rows / merge split row).
- Repeated header rows / repeated items: table header rows, or titles above a
  table, that a printer repeats on each page; dropped when joining.
- Start marker: text the survey identifies as starting a new unit (e.g., a
  recurring box title); Python uses it only as a check.
- Seam image: one image of the bottom of page N directly above the top of page
  N+1 (step 3 option B).
- Chain: the sequence of item pieces linked by verdicts across pages.
- Segment: one assembled unit in document.json (a chain, or a single item), with
  a segment ID.
- Outline: the tree of headings built in step 4.
- section_path: a segment's outline ancestors, outermost first (today: a running
  list of every heading seen so far).
- Fill-down / grouping columns: repeating a row label into the blank cells below
  it, so each row stands alone.

Domain output (steps 5–6)

- Page schema: the fixed, generic schema of pages/*.json and document.json.
- Domain schema: a per-PDF JSON Schema, proposed in step 5 or supplied by the
  user, that shapes domain.json.
- x-key: annotation naming the fields that identify an object within an array;
  used to merge fragments and to build stable object IDs.
- x-verbatim: annotation marking a string that must be copied exactly from its
  cited source.
- Evidence pack: the compact view of document.json that the schema model reads
  in step 5.
- schema_notes.md: step 5's mapping of each outline section to a schema path, or
  the reason it is excluded.
- Projection: step 6. Filling the domain schema from document.json.
- Window: the slice of document.json for one projection call (e.g., one box,
  section or table).
- Fragment: the part of the domain schema one window fills, returned with its
  ancestor keys.
- Pointer mode: option where the model returns only an item ID and Python copies
  the text.
- Coverage report: items that no domain output cites, plus verbatim retries and
  merge conflicts.

Quality and operations

- Extractor / verifier: the model that makes the primary judgment in step 2
  (items on a page) or step 3 (a page break).
- Validator: a second model that reviews extractor or verifier output in steps
  2–3.
- Checker: an optional second model that reviews step 5 schemas or step 6
  fragments.
- Review list: issues left for a human after retries (in run.json or a report;
  open question 3).
- Fingerprint: a hash of an output's inputs (PDF, profile or schema, prompt
  version, model, settings); resume reruns only outputs whose fingerprint
  changed.
- Reference labels: free ground truth for comparing designs (e.g., good
  structure tags, or rules checkable from the text layer).
- Evidence (E1–E23): findings from the sample PDFs and past runs, cited by
  design points; they illustrate and test, not specify.

KGForEdGlobal

- KG stage: KGForEdGlobal's knowledge-graph pipeline (entries/create_kgs.py). It
  reads document.json and builds academic-standards items, then Learning
  Components and Learning Progressions.
- KG item: one academic-standards node (StandardsFrameworkItem), e.g., a grade,
  term or skill; parent links connect them.
- DocumentIR / TableSegment / BlockSegment: today's document.json types that the
  KG stage imports.
- doc_key: SHA-256 of the PDF bytes (utils/pdf.py:13); today's results folder
  name and part of the segment ID recipe.
- CAPS: South Africa's English Home Language Grades R–3 curriculum PDF, the main
  sample used in this handoff.

## Goal

Build a new, standalone Python package, `pydelity`, that turns (almost) any PDF
into one faithful, structured JSON file (`document.json`) with item-level
provenance (e.g., page, bounding box), and optionally into a per-PDF domain
JSON. It replaces stages 1–3 of KGForEdGlobal (Page IR extraction, Page IR
verification, Document IR construction). Its `document.json` must remain usable
as the input to KGForEdGlobal's knowledge-graph (KG) stage. KGForEdGlobal's
curriculum PDFs are the first test set, not the target.

## Setup and access

- This repo (`pydelity`) is new, with STANDARDS installed in greenfield mode.
- KGForEdGlobal sits outside this repo; read it by absolute path (see Source
  material). Adding it as a session folder (e.g., `/add-dir`) avoids a
  permission prompt on each read.

## First work item: repo setup (before any pipeline code)

Scope this as the first item of the cycle, finished and signed off before steps
1–6 are built.

- Goal: get the repo's files and folders into shape for a Python 3.13 library
  with a Typer CLI that will later ship to PyPI: READMEs, pyproject.toml,
  Makefiles, env templates and .envrc, .gitignore, pre-commit, CI workflows, and
  folder layout (e.g., whether to keep backend/ or move the package to the repo
  root).
- Working mode: interactive. The user points out what to change; Developer
  proposes and makes each change. Don't pre-plan an exhaustive list of edits.
- Context: the scaffold was copied from KGForEdGlobal and still carries its
  leftovers (web-app and KG settings, Docker targets, unused dependencies).
- Out of bounds: package code beyond empty modules and a smoke test; STANDARDS
  files (.standards/, .agents/, .claude/skills, AGENTS.md, CLAUDE.md).
- Done when the user signs off and `make install`, the lint targets, `make test`
  and `pre-commit run --all-files` all pass.

## Source material (read-only reference; do not modify)

- Repo: /Users/tzz/Projects/private/idi/KGForEdGlobal (branch
  tz6/page-ir-extraction-cleanup, commit 5e2d7cc)
- Code (all under backend/src/kgfeg/): page_ir_extraction/,
  page_ir_verification/, document_ir/, entries/extract_page_ir.py,
  entries/verify_page_ir_continuity.py, entries/stitch_document_ir.py,
  utils/pdf.py, regexes.py, utils/constants.py, and the stage 1–3 parts of
  schemas.py, config.py, model_registry.py
- Tests (under backend/tests/kgfeg/): page_ir_extraction/,
  page_ir_verification/, document_ir/, test_regexes.py
- Docs: docs/architecture.md, docs/pipeline/page-ir-extraction.md,
  page-ir-verification.md, document-ir.md
- Example configs: examples/ (hand-written per-document instructions and KG
  configs; examples/funda_wande/config_english_curriculum.json is the CAPS one,
  see E10 and E16)
- Sample PDFs (8 in data/): data/funda_wande/caps_english_hl_grade_3_fs.pdf
  ("CAPS"; 142 pages, no bookmarks, no structure tags);
  data/rwanda/rwanda_math_p1_p3.pdf (147 pages, useful structure tags);
  data/ghana/ghana_english_scope_and_sequence.pdf and
  data/india/madhi/mathematics.pdf (smaller, tagged; see E6).
- Past-run outputs (local, not in git): results/kg_for_ed/<doc_key>/. Six runs
  are from June–July 2026 and the CAPS run from 2026-10-09; stage 1–3 code
  changed after some of them (e.g., 569e055 on 2026-10-13 added the correction
  guard and per-document instructions), so the evidence reflects the code that
  produced each run.

## User decisions (fixed unless there is a conflict)

1. New repo named `pydelity` (also the package name). Python 3.13.
2. Libraries: PydanticAI, Pydantic, pydantic-settings, loguru. CLI: Typer.
3. Cost calculator and tracker for model API calls.
4. CLI first; the architecture must allow a later PyPI release (pip install).
5. Runtime config: one optional JSON or YAML file, far simpler than today's. The
   PDF path is the only required input; it can be given as a CLI argument, so no
   config file is needed for a basic run. Optional inputs are a small set of
   global settings (see Cross-cutting), including a user schema path and
   `overwrite`. A normal run resumes from the last interrupted point (e.g.,
   failure, timeout, Ctrl+C).
6. Must work on (almost) any PDF: curricula, tax documents, image-heavy PDFs,
   non-Latin and right-to-left scripts.
7. No hand-written per-document runtime config and no hard-coded domain Pydantic
   classes. A frontier model proposes the per-PDF profile and schema, or the
   user supplies a schema.
8. Model access through provider APIs (e.g., Anthropic, OpenAI) via PydanticAI.
9. Document-type agnostic: no core logic, prompt, schema field or default may
   assume a document type (e.g., grades, terms, skills, banners).
   Document-specific knowledge comes only from the survey profile, user
   instructions, user schemas, or consumer adapters. Sample PDFs and their
   findings (see Evidence) are test inputs and illustrations, not requirements.
10. Repo setup comes first: see "First work item". No pipeline code until it is
    signed off.

## Agreed design directions (input for Architect, not yet approved scope)

Steps:

| Step                              | Model                                                                                                              | Python                                                                                                                                            | User (optional)                                          | Output                                |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ------------------------------------- |
| 1 Survey                          | Reads the PDF (whole file); proposes the page profile                                                              | Input limit checks (see Cross-cutting), text layer, bookmarks, profile validation, etc. (see the step 1 section)                                  | document-specific instructions, document languages, etc. | pdf_survey.json                       |
| 2 Page extraction                 | Extractor per page + conditional validator (see the step 2 section)                                                | Rendering, quality checks, text-layer guard, retries                                                                                              | pages, instructions                                      | pages/NNNN.json                       |
| 3 Page-break verification         | Verifier (continue?, join rule, repeated header rows/items) + validator; design options in the step 3 section      | Candidate items, verdict checks, review list                                                                                                      | instructions                                             | page_breaks/NNNN-NNNN.json            |
| 4 Assembly                        | Outline tree from headings, contents pages, bookmarks and tags; grouping columns for flagged tables                | Chains from verdicts only, text/table joins, provenance, every-item-used-once check, outline and cross-page consistency checks, deterministic IDs | keep_headers_footers, fill_down: off                     | document.json                         |
| 5 Schema (skipped if user schema) | Proposes JSON Schema + schema notes from an evidence pack; optional checker                                        | Evidence pack, schema checks, adds `source` fields, run-time schema handling (see the step 5 section)                                             | schema, instructions, edits, --review-schema             | schema_proposed.json, schema_notes.md |
| 6 Projection (optional)           | Fills one schema fragment per window with ancestor keys, cites item IDs; optional checker (see the step 6 section) | Window planning, source and verbatim checks (x-verbatim), keyed merge (x-key), stable object IDs, coverage report                                 | max_cost, edits                                          | domain.json, coverage report          |

Two separate schemas:

- Page schema (steps 2–4): fixed and generic; never supplied by the user.
- Domain schema (steps 5–6): JSON Schema with `x-key` and `x-verbatim`
  annotations; proposed by the model in step 5 or supplied by the user. Whether
  a user schema also seeds the page-profile labels is open question 8.

Core page schema (generic and the same for every PDF; the lists below may change
if there is a conflict, a missing element, or a better design):

- `kind`: text, list, table, figure, field (form field / checkbox). Proposed
  addition: formula (math/chemistry, with a text form such as LaTeX); see open
  question 9.
- `role`: heading, caption, footnote, artifact, navigation, body. Proposed
  addition: aside (sidebars, callout boxes, margin notes outside the main
  reading order, so assembly does not join body text into them across pages);
  see open question 9.
- `label` (per PDF): closed list from the survey profile; each label maps to one
  role and allowed kinds; always includes `other`. No core Python logic branches
  on label values.
- Proposed addition: `container` (bordered or shaded boxes). Items inside a box
  keep their own kind (heading, list, text) and carry a container ID; each
  container has a bbox and open-top/open-bottom hints for cross-page
  continuation; see open question 10.
- Stable item IDs; per-page writing direction; `caption_of` links; figure crop
  paths.
- `pdf_survey.json` holds document facts, regions, artifacts, notes, and a
  `profile` section (labels, rules, languages, direction, rotation per page
  range, continuation notes, start markers). Steps 2–3 fingerprint only
  `profile`.
- The model writes JSON Schema (data), never Python source; Python validates
  against it at run time (see the step 5 section).

Cross-cutting:

- Input limits: step 1 sends the whole PDF in one model call, so the PDF must
  fit the selected survey model's PDF input limits (max pages and max request
  size; e.g., current 1M-context Claude models allow 600 pages and 32 MB,
  200k-context Claude models 100 pages). pydelity keeps these limits per model
  and checks page count and file size before any model call. If either is
  exceeded, the run stops with a clear error naming the model, the limit and the
  PDF's value, and telling the user to split the PDF or pick a model with higher
  limits. No automatic splitting or chunked survey. The limits apply to the
  whole file even when `pages` selects a subset. Unknown models: see open
  question 11.
- Resume: each artifact stores a fingerprint of its inputs (e.g., PDF hash,
  profile/schema hash, prompt version, model, settings); only steps with changed
  inputs rerun. Atomic writes (temp file + rename); validate files on load.
- Cost: PydanticAI RunUsage + genai-prices; per-call ledger cost.jsonl; max_cost
  limit.
- Library-first: core run() API + per-step functions; CLI is a thin wrapper
  ([project.scripts]); loguru disabled in the library by default; no Settings
  object built at import time; environment settings (API keys, default model)
  separate from run config.
- Optional global inputs: schema, instructions (one field sent to every agent),
  languages, pages, output_dir, model, max_cost, overwrite. Per-step options
  (keep_headers_footers, fill_down, review_schema) and advanced internals go in
  an `advanced:` section.
- Removed or internal (today's settings): dpi (auto by page size),
  use_extracted_hints (always on, except on pages with garbled text),
  country/year (unused), four instruction fields (merged), confidence thresholds
  and crop padding (internal, tuned defaults), min_link_score (heuristic linker
  removed), max_section_path_length (outline replaces it), repair_hyphenation
  (verifier join rule), sort_items_by_bbox (removed),
  table_filldown_group_cols_max (model decision).

## Step 1 (survey) design points

- Python probe (no model): text layer per page (character counts, garbled or
  control characters), bookmarks, form fields, structure-tag quality, lines
  repeated across pages (artifact candidates), text direction per page (rotated
  text can appear even when the page's rotation attribute is 0, E22), font
  sizes, printed page numbers.
- One model call over the whole PDF plus the probe facts returns a structured
  survey proposal: regions, artifacts, notes and the profile (labels, rules,
  languages, direction, rotation per page range, continuation notes, start
  markers).
- Python checks (ModelRetry, up to 2 retries): labels map to valid roles and
  kinds; regions sit inside pages; rotation agrees with the probe's text
  direction; proposed artifacts cover at least ~80% of the probe's repeated
  lines; the printed-page offset agrees with printed page numbers (E22).
- User inputs (languages, instructions) add to the proposal; they never bypass
  the checks.

## Step 2 (page extraction) design points

- Rendering: DPI chosen from page size; pages with rotated content are rendered
  upright per the profile, and bounding boxes are mapped back to PDF points.
- Input per page: a cached prefix (generic prompt + page schema + profile + user
  instructions), then the page image, text-layer hints (skipped on pages with
  garbled text, E22), and artifact lines pre-matched from the survey.
- Python checks: page-schema validation and label/role/kind consistency;
  bounding boxes inside the page with no implausible overlaps; character-level,
  script-agnostic text coverage against the text layer, so dropped or invented
  text is caught; reading order checked per the page's writing direction;
  artifacts consistent with the survey. Up to ~2 retries, then the review list.
- Validator only on pages that failed checks or are hard (rotated, dense tables,
  low coverage), plus a random sample; save every verdict so its value can be
  measured (E5, E23).
- Pages are independent, so they run in parallel; each page file is written
  atomically with its fingerprint.

## Step 3 (page-break verification): options to consider; not decided

Today: one verifier call per break plus a validator call on every break, with an
uncached prompt and the full previous page as an image (cost and timing: E7).

Options (can be combined): A. PDF structure tags as evidence. Tagged PDFs record
which table, paragraph or list content belongs to, across pages. The survey
probe rates tag quality; step 3 passes tag evidence to the verifier, and Python
flags verdicts that contradict good tags. Tags inform the verdict but never
decide it alone (E6). B. Seam images with item labels. Python builds one image
per break: the bottom of page N directly above the top of page N+1, rotated
upright per the profile for sideways pages, with step 2 item IDs drawn on the
boxes (set-of-mark prompting). The model names labels it can see instead of
matching JSON indexes to pixels; images are smaller than today's. C. Windowed
verification. One call judges ~10 consecutive breaks and returns one verdict per
break, with the survey's continuation notes and start markers in the cached
prompt prefix, so verdicts within a multi-page unit stay consistent. Breaks that
fail Python checks or have low confidence are re-asked alone. Verdicts are still
stored per break; a changed page re-asks only its two breaks. D. Conditional
validator. Run the validator only on low-confidence breaks, failed Python
checks, contradictions with tags or start markers, and a random sample; save
every verdict (E5). E. Continuity inside step 2 (the extractor also sees a crop
of the neighbouring page). Cheapest, but the extractor for page N+1 can't know
page N's item IDs while pages run in parallel, the extraction prompt grows, and
resume couples neighbouring pages. An experiment, not version 1.

Ruled out by evidence: Python heuristics as the decision (E1); one-page boundary
marks as a gate for skipping the verifier (E3); a text-only pass without images,
which loses shading and borders (E8).

Whatever the design, the verdict must cover:

- Join rule per kind: text (space / no space / dehyphenate), list (continue item
  / new item), table (append rows / merge split row). Today's stitch code only
  appends rows, so a row split across pages becomes two rows (E9).
- Repeated header rows as a count, not a boolean, checked by Python against the
  base header (keep today's guard against dropping non-matching rows,
  document_ir/stitch_segments.py:345).
- Repeated items above a continued unit, such as a running title repeated on
  each page of a multi-page table; otherwise assembly builds one heading per
  page (E9).
- Continuation markers in row labels or headings (e.g., "(contd)", "continued"),
  which step 4 folds into the original label (E9).
- Survey-supplied continuation rules: profile continuation notes and optional
  start markers that mark the start of a new unit, inferred by the survey from
  the whole PDF. They replace today's hand-written per-document rules (E10).
  Python uses markers only as a check.

Before choosing, compare designs against free reference labels: document rules
checkable from the text layer (E8) and good structure tags (E6).

## Step 4 (assembly) design points

- Outline (one model call). Inputs: heading items (text, page, numbering, font
  size and weight from the text layer), the contents pages (role navigation,
  kept out of the body flow), and bookmarks and heading tags when present. All
  are evidence, not truth. The model sets a parent for each heading and may
  demote a "heading" that is really a box or table title (E14). Python checks
  the result is a tree, parents come before children in reading order, and each
  contents entry matches a heading within a page tolerance. Mismatches are
  flagged, not fatal; printed contents pages can be wrong (E13). Outline depth
  inside boxes depends on open question 10.
- section_path = outline ancestors, replacing today's running list of every
  heading seen so far (E12).
- Cross-page consistency check: the same repeated text extracted with different
  roles or kinds across pages goes to the review list (E14).
- Table grid: cells covered by a span are marked as spans, not filled with
  copied text, and the col-span repair count is reported (E15).
- Grouping and fill-down: Python flags tables whose leading columns have blank
  cells under a filled one; the model decides the grouping columns (E9, E11).
- Review list entries from step 4: outline mismatches with the contents pages,
  cross-page role or kind inconsistencies, and tables that needed span repairs.

## Step 5 (schema proposal) design points

- Evidence pack: send the whole document.json in compact form (outline, then
  each segment as markdown with item IDs, lists as bullets, tables as markdown)
  when it fits a token budget (E17). Above the budget, sample: every outline
  section, plus a few examples of each repeated structure with its count. Do not
  derive enums from table header-row positions; repeated tables are often
  extracted with labels in different rows (E15).
- Output: JSON Schema plus schema_notes.md, which maps every outline section to
  a schema path or marks it excluded with a reason. List structure must reach
  step 5 as list items, since leaf records often map to individual list items.
- Leftover content: documents mix main records with notes, guidance or
  commentary in similar styling (E20). The schema needs a place for content that
  is not a main record, or step 6 forces it into records.
- Python checks (ModelRetry, up to 2 retries): an allowed JSON Schema keyword
  subset; `x-key` on every array of objects, with the key fields required;
  `x-verbatim` only on strings; every enum value appears verbatim in the
  document (case-insensitive); every outline section mapped or excluded in
  schema_notes.md.
- Optional checker model: wrong nesting, missing structures, merged or split
  levels.
- Run-time schema handling: consider PydanticAI `StructuredDict(json_schema)`
  (available in 1.63.0, the version installed in KGForEdGlobal) as the step 6
  output type, plus JSON Schema validation (e.g., `jsonschema`) and Python's own
  x-key / x-verbatim checks, instead of building Pydantic models at run time.
  Strip `x-*` annotations before sending a schema to the provider (whether
  providers accept unknown keywords in structured-output schemas is unchecked).
- Stability: the schema is proposed once, saved and reused on reruns unless
  `overwrite`; user edits to schema_proposed.json change its fingerprint, so
  step 6 reruns.
- Testing: when a hand-written schema or config exists for a test PDF, use it as
  the expected answer for steps 5–6 (E16).

## Step 6 (projection) design points

- Windows: one unit per window (e.g., one repeated box, one section, one table),
  chosen from the outline and the schema_notes.md mapping (E18). The model gets
  the schema fragment for its target path and returns it with its ancestor keys
  and the item IDs those keys came from, so Python can place it.
- Input per call: a cached prefix (prompt + full schema with x-* stripped and
  source fields added), the target path and its schema fragment, and the window
  content rendered from document.json with an item ID on every line and on every
  list item.
- Citations: every verbatim string carries the item IDs it came from. One ID per
  list item needs list items with their own IDs (containers, open question 10a);
  when a box is a table, a whole block of list items can share one cell ID, and
  verbatim checks become substring checks inside that cell.
- Python checks per window: JSON Schema validation; every cited ID exists and
  sits inside the window; each x-verbatim string matches its own cited item (or
  a substring of it) after normalizing whitespace and list markers. Check
  against the cited source only, because documents repeat text with small
  differences (E19). A mismatch triggers a retry that names the exact
  difference.
- Merge: Python places each fragment by its keys; fragments with the same keys
  merge their arrays by x-key; conflicting values go to the review list.
- Pointer mode (option): for a field that copies a whole item, the model returns
  only the item ID and Python copies the text. Otherwise verbatim fields make
  the model re-type most of the document, so output tokens dominate cost (E18);
  pointer mode cuts most output tokens and removes verbatim retries.
- Coverage report: items per window and section that nothing cited (structural
  labels are expected; content lines are flagged for review), plus verbatim
  retries and merge conflicts. It cannot see text lost in step 2; only step 2's
  text-coverage check can.

## domain.json and KGForEdGlobal's KG stage (consumer-specific; later)

Today the KG stage never reads domain.json. It reads document.json and runs its
own projection (entries/create_kgs.py steps 3–9), which builds the same kind of
tree step 6 would (E21).

- Option 1 (current plan): the KG stays on document.json; no transform layer.
  Step 6 is unused for KG runs, and the KG keeps its hand-written per-curriculum
  rules and its own model calls.
- Option 2 (later, in KGForEdGlobal): a thin adapter turns domain.json into KG
  items and parent links. Each object at a mapped schema path becomes one item
  (statement type, normalized type, verbatim text as description); the parent
  comes from nesting; the ID comes from the key path (plus text for unkeyed
  leaves); cited item IDs map to document.json segment IDs and pages for
  provenance; framework metadata comes from the existing kgs.metadata config.
  Learning Components and Learning Progressions then run unchanged. The
  schema-path → statement-type mapping comes either from (a) a schema per
  curriculum plus a mapping table in KGForEdGlobal config, or (b) one generic
  curriculum schema for every curriculum (a recursive tree of groupings, each
  with a statement_type and text, standards as leaves), which keeps the adapter
  generic. (b) suits the 7 curricula of different depths. Curricula whose
  hierarchy comes from printed codes (e.g., B1.1.1.1) need the codes as x-key
  fields so nesting follows the codes.
- What pydelity does now so option 2 stays cheap (all generic):
  - Pass unknown `x-*` annotations through untouched in user-supplied schemas
    and schema_proposed.json, so a consumer can tag schema paths (e.g.,
    `x-kg-statement-type`); pydelity never interprets them.
  - Give every domain.json object a stable ID derived from its key path; parent
    links stay as nesting; array order follows document order.
  - Make cited item IDs resolvable to document.json segment IDs (a lookup
    carried in document.json).
- Test reference for the later adapter: today's CAPS KG tree (E16).

## Known defects in the source code to design out (paths under backend/src/kgfeg/)

- Reading order assumes left-to-right: extraction prompt rule 2 ("left column
  before right") in page_ir_extraction/prompts.py; validate_gross_reading_order
  (page_ir_extraction/validators.py:836) rejects "jump up and move left", which
  is correct order for right-to-left multi-column pages.
- Cross-page text join always inserts a space and knows only Latin sentence
  ends: document_ir/stitch_segments.py:994, :1040.
- Header-row inference counts only Latin letters: regexes.py:29 used at
  stitch_segments.py:913.
- Correction guard tokenizes words as letter runs
  (page_ir_extraction/utils.py:29); scripts without spaces likely break it
  (predicted, not observed).
- English-only lists: page_ir_extraction/validators.py:28, :425; caption
  prefixes utils/constants.py:119 (en/fr/sw only).
- Full-page figure checks (validators.py:663, :728) push back on pages that are
  one figure (slides, comics, posters).
- Bounding-box sort is top-to-bottom then left-to-right
  (document_ir/normalize_page_items.py:500); it mixes columns. All 7 example
  configs enable it.
- No form-field or checkbox type (utils/constants.py:10); fillable PDF fields
  are not read; figure crops are not saved; DPI fixed at 250.
- Resume checks only file existence (entries/extract_page_ir.py ~line 96);
  changed model or instructions silently reuse old pages. JSON writes are not
  atomic (utils/general.py:431).
- Settings built at import time and requires PATHS_PROJECT_DIR (config.py:64,
  :175).
- `country` and `year` are required/optional config fields with no effect
  (schemas.py:3311; only persisted at page_ir_extraction/utils.py:608).
- Curriculum naming leftovers: "RUNTIME CURRICULUM INSTRUCTIONS" in both
  prompts.py files; unused NodeRole enum (utils/constants.py:69).

## Evidence (E1–E23; illustrations and test cases, not requirements)

Past runs (7 curriculum PDFs, results/kg_for_ed/):

- E1. Verifier verdicts produced 397 of 401 page-break links; the ~2.1k-line
  heuristic fallback linker produced 4. The fallback can go.
- E2. Verification added continuation to 371 item boundaries (of ~802
  continuation sides) that one-page extraction marked complete, removed 10, and
  set repeats_header 282 times. A two-page judgment is essential.
- E3. In 501 of 684 past breaks both pages' one-page marks said "complete", and
  the verifier still found 232 continuations.
- E4. All 7 example configs use the same tuned values, which differ from code
  defaults: min_confidence_to_patch 0.5 (default 0.75),
  min_confidence_to_stop_negative_search 0.9 (0.95),
  verification_auto_stitch_confidence 0.7 (0.75), use_extracted_hints true
  (false).
- E5. Extraction-validator and verification-validator verdicts are not saved, so
  the validators' value is unmeasured. Structure tags (8 sample PDFs):
- E6. 5 of the 8 sample PDFs have a tag tree. Three mark tables or lists across
  pages: Rwanda (37 tables and 7 lists bridging 85 breaks), Ghana English scope
  and sequence (tables bridging 11 of 13 breaks) and India Madhi mathematics
  (tables bridging 5 of 8 breaks). Ghana English and Nigeria have trees with
  only one section element; CAPS has none. Tags vs the verifier: Rwanda agrees
  on 136 of 144 breaks (tags likely right on 3 table breaks the verifier
  rejected, pp47→48, 120→121, 142→143, two at confidence 0.4; the verifier right
  on 5 text breaks the tags missed, e.g., p9→10); Madhi agrees on all 8. Ghana
  scope and sequence had no past run. CAPS (today's run covered PDF pp36–136):
- E7. Step 3 today: one verifier call per break (full previous page at 250 DPI +
  next-page crop + candidate JSON + a ~20 KB uncached prompt; ~13.6k input
  tokens per break), then a validator call on every break. 99 breaks on Opus 5:
  $15.25 and 20 minutes; the validator cost slightly more than the verifier.
- E8. The document's own start-of-box banner, checked against the text layer,
  matches all 99 verifier verdicts (a free reference). All 3 low-confidence
  breaks turned on a shaded band continuing across the break, which a text-only
  view would miss.
- E9. An 8-page sideways table (pp28–35) repeats its title and column-header row
  on each page; one page starts with a row label ending "(contd)"; at p31→32 a
  row splits across pages.
- E10. Today's run needed hand-written continuation rules naming two
  start-of-box phrases ("REQUIREMENTS PER TERM", "RECOMMENDED TEXTS/RESOURCES
  FOR THE YEAR"); pydelity's survey must infer such markers.
- E11. Today's assembly: 59 segments (7 headings, 52 tables); fill-down changed
  0 of 52 tables; the sideways table (E9) is the one that needs grouping.
- E12. Today's section_path (document_ir/stitch_segments.py:2115,
  `_update_section_stack`) appends every heading, never removes one when a
  sibling or higher-level heading appears, and keeps the last 60. A table in the
  last grade section carries all four grade headings plus two box titles; the KG
  reads the path nearest-first for scope values
  (kgs/sfi_extraction_windows.py:513), so it sees four grade candidates instead
  of one.
- E13. The contents page lists one section at printed p53; it starts at p55.
  Expected outline (test): Section 1 (1.1–1.4, with 1.4.1–1.4.4), Section 2
  (2.1–2.8), Section 3 (daily programme and overview table, 3.1–3.4 Grade R–3),
  Glossary.
- E14. The same repeated title is a table title row on p59 and a heading on
  pp84, 109 and 135, so today's path treats it as a section.
- E15. Boxes extracted as tables: 36 of 52 became 2-column tables because a
  banner row puts two labels side by side; Python made 54 col-span repairs;
  rows_grid copies full-width text into both columns. The same banner labels sit
  in different header rows across the 52 tables.
- E16. Reference domain model: the hand-written KG config (examples/funda_wande/
  config_english_curriculum.json, kgs.as) defines Grade → Term → Skill Area →
  Sub-strand → Skill with value lists; today's CAPS KG has 1,144 items (4 Grade,
  16 Term, 48 Skill Area, 152 Sub-strand, 924 Skill) and 1,144 parent links.
  Expected answer for steps 5–6 on CAPS.
- E17. ~296k characters of text (~74k tokens by characters ÷ 4); today's
  document_ir.json is 2.2 MB, mostly because table rows are stored three times
  (rows, rows_grid, rows_filldown).
- E18. Step 6 on CAPS: about 55–60 windows (one per box or section); verbatim
  fields would make the model re-type ~52k tokens for the box section alone.
- E19. Near-duplicates: assessment bullets repeat content bullets with small
  differences (a dropped "s", square vs round brackets).
- E20. Same styling, different roles: bold-italic lines inside boxes are
  sometimes sub-headings (in E16's Sub-strand list) and sometimes schedule or
  guidance notes.
- E21. The KG stage's own projection: 55 windows; 1,220 candidates from a model
  producer and checker; 138 model review calls to merge duplicates (1,220 →
  1,144); 1,144 generator + 1,144 checker calls to resolve parent links (0
  corrections).
- E22. CAPS probe facts: rotated text on p1 and pp28–35 although every page's
  rotation attribute is 0; control characters on pp1 and 12; printed page = PDF
  page − 5; no text on p142.
- E23. Step 2 today on CAPS (100 pages, Opus 5, no cache reads, 68 minutes):
  extraction 1.54M input / 114k output tokens (~$10.57); validation 1.49M input
  / 209k output tokens (~$12.67). The validator cost more than the extractor.

## Consumer contract: what document.json must preserve for KGForEdGlobal's KG stage

(Consumer-specific. Keep it in document.json fields or in the KGForEdGlobal
adapter, never in core logic.)

- KG code (13 modules in kgs/ and evals/) imports DocumentIR, BlockSegment,
  TableSegment, TableCell, TextUnit. Field uses: segment_id 223, section_path
  72, grid_sources 53, columns_signature 31, local_code 21, row_provenance 11,
  rows_grid 10, rows_filldown 8.
- Keep the segment ID recipe (UUIDv5 of doc_key + kind + first page + item
  index, document_ir/stitch_segments.py:213) so IDs stay stable across pydelity
  reruns. They will still differ from today's IDs, because pydelity numbers
  items differently.
- Add `schema_version` to document.json; KGForEdGlobal pins a compatible range.
- section_path changes meaning (running list of headings → outline ancestors)
  but keeps its shape (a list of heading references, outermost first). KG
  outputs will shift (E12).
- Bounding boxes change from pixels at 250 DPI (today's coord_space "px") to PDF
  points; the KGForEdGlobal adapter converts them if anything downstream reads
  them.
- document.json carries a lookup from item IDs to segment IDs, so citations in
  domain.json (and any later KG adapter) resolve to segments and pages.
- CAPS requirement boxes reach the KG today as one-column TableSegments whose
  banner lines are header rows. document.json must carry enough to rebuild that
  shape (see open question 10).

## Open questions for Scoper to settle with the user

1. Does projection run by default when no schema is supplied? (For KGForEdGlobal
   runs, step 6 is unused unless the later adapter in "domain.json and
   KGForEdGlobal's KG stage" is built.)
2. Confirmation prompt before spending money (with --yes for scripts)?
3. Review output: a list in run.json, or an HTML report?
4. Acceptance bar: parity with the current pipeline on the 7 example PDFs, plus
   a new test set (tax form, two-column right-to-left document, Chinese/Japanese
   document, slide deck)?
5. Which scripts and document types are must-have for version 1?
6. Default model(s) and default max_cost.
7. Should the PDF path be a positional CLI argument, a config field, or both
   (CLI wins)?
8. Should a user-supplied domain schema also drive the page-profile labels?
9. Final `kind` and `role` lists: add `formula` (kind) and `aside` (role)? Any
   others (e.g., `code` kind)?
10. How should bordered or shaded boxes (callouts, requirement boxes, form
    sections) be represented? Options: (a) a `container` element, so boxed
    content keeps its structure (headings, lists, text) and a consumer adapter
    maps containers to whatever shape it needs (KGForEdGlobal: one-column
    TableSegments); (b) keep boxes as tables, pinned by a user instruction such
    as "Treat bordered boxes as tables." A survey model cannot infer which shape
    a downstream consumer needs. Trade-offs: as tables, boxes with multi-part
    banners become multi-column tables that need span repairs (E15), and
    headings inside boxes sit in cell text (E20). With (a), headings inside
    boxes become outline nodes that steps 4 and 5 see directly, and each list
    item gets its own ID, so step 6 can cite and check one item at a time.
11. PDF input limits for the survey model: which models ship with known limits
    in version 1, can the user override them (e.g., under `advanced:`), and what
    happens for a model with no known limits (fail before the call, or warn and
    let the provider reject an oversized file)?
12. Which step 3 design goes into version 1 (options A–E in the step 3 section)?
    Should the choice be made by comparing today's per-break verifier with the
    chosen design on CAPS and Rwanda against the free reference labels (E6, E8)
    before building the rest?

## Out of scope for this cycle

- Any change to KGForEdGlobal (adapter, create_kgs.py taking a document.json
  path, removing stages 1–3, docs). That work happens later, in KGForEdGlobal.
- Building the domain.json → KG adapter and replacing KG steps 3–9 (later, in
  KGForEdGlobal; test against today's CAPS KG tree, E16).
- KG, Learning Components, and Learning Progressions logic.
- Generating KGForEdGlobal KG config from a pydelity schema (a possible later
  step).
- Publishing to PyPI. Only the design must allow it.

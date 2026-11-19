# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `DEVELOPING` `CycleMode`: `STANDARD` `PendingCycleMode`:
`UNSET` `PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`CompletionPolicy`: `FULL_DELIVERABLE` `Id`:
`build-step-2-page-extraction-of-the-20261119T174118Z-0419318a`

`Request`:
`Build step 2 (page extraction) of the pydelity pipeline, on top of the survey (step 1) released as 0.1.0 and 0.1.1 and now on main. This cycle covers step 2 only; steps 3-6 stay out. Using the survey's profile in pdf_survey.json as its per-PDF guide, step 2 writes a page file for each selected page: items in reading order for the page's writing direction (including right-to-left and multi-column pages), each with a stable ID, kind, role, label, bounding box in PDF points and content. Rotated content is read upright, figures are saved as crops, captions link to what they caption, bordered or shaded boxes become containers, form fields and checkboxes carry their values, and single-figure pages are accepted. Python checks compare the model's text with the text layer in any script and catch dropped or invented text. Step 2 reuses and extends the run features the survey built: settings, the CLI and Python API with async versions, the cost ledger and max_cost, resume and fingerprints, the review list and HTML report, mocked tests for both providers, CI on Python 3.13 and 3.14, Windows install and use, and the docs site. pydelity ports over and reuses what fits from KGForEdGlobal's page extraction (/Users/tzz/Projects/private/idi/KGForEdGlobal, read-only reference, never changed) and writes new code where it doesn't fit. Inputs: artifacts/next_cycle_inputs.md first (the survey cycle's decisions, what 0.1.0 provides and its gaps for step 2, corrections to the brief, and open follow-ups; where it and the brief disagree, it is newer), then artifacts/design_brief.md (its "Step 2 (page extraction) design points", the known source defects to design out, evidence E1-E23 and the KG consumer contract). Changes since next_cycle_inputs.md was written: 0.1.1 fixed the docs to state that pydelity supports Python 3.13 and 3.14 only (Python 3.14 on a Mac needs macOS 14 or later; Python 3.15 waits on onnxruntime, which PyMuPDF 2.x requires, shipping a 3.15 build); the 0.0.1 placeholder is yanked on PyPI; Dependabot now ignores setuptools, whose [build-system] minimum is kept by hand; main's history was rewritten to remove a co-author credit, so the survey's squash commit is now c63d891 (CHANGELOG.md still links the old d13c0fd), and the survey cycle's records are at commit 83743ef, fetched with "git fetch origin pull/4/head". Commit messages never carry a Co-Authored-By trailer or other AI attribution. Open for Scoper to settle with the user: how pages are selected; whether "pydelity <pdf>" now runs the survey and page extraction by default; whether step 2's text checks send a page back or only list differences for review, given the user's decision to trust the model's reading over the facts; whether a second model verifies failed or hard pages; how a user picks a model for page extraction; how the HTML report shows item boxes; and which release this cycle ships, such as 0.2.0. User rework after the first scope: step 2 records no page continuity, so neither items nor containers carry continuation marks or open-top or open-bottom hints, and step 3 decides continuity; a setting controls how many pages are extracted at the same time, with a default of 8; translating extracted text is out of scope for step 2 and is to be revisited after assembly as an optional step with a target-language setting, because pydelity serves any PDF and downstream use, and a consumer such as KGForEdGlobal can leave it off. Second rework: several page requests run at once, each carrying one page, and provider batch APIs and multi-page requests need no non-goal entry. Third rework, after the technical design: page extraction's default model stays anthropic:claude-opus-5-5 with effort high; the CLI option that turns pauses off is --no-pause with short form -np; add an optional instructions setting for page extraction, available in the config file and as a Python keyword but not on the CLI, in which the user describes in natural language what is particular, different or nuanced about the PDF, and which is added to the messages sent to both the page extraction model and the verifier model to help them with hard cases; and revisit the page image size (2,000 pixels on the long edge), which the user questioned as perhaps not standard or optimal. Refined by the user: instructions become per step and live under advanced:, advanced.survey.instructions for the survey and advanced.extraction.instructions for page extraction, each sent only to its own step's models (page extraction's to both the extraction and verifier models), settable in the config file and from Python, with no CLI option, because each step's instructions are specific to that step; they replace the top-level instructions setting and the --instructions/-i option. Fourth rework: pydelity keeps no backwards compatibility with 0.1.x, because it has no public users yet, so there are no aliases, deprecation paths, migrations or compatibility-only defaults for renamed or removed settings, options, functions or output fields.`

`Scope`:
`.standards/docs/scope/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a.md`
`Architecture`:
`.standards/docs/specs/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a.md`
`Development`: `NONE` `PromotionReason`: `NONE` `AuditTarget`: `NONE`
`BlockedOn`: `NONE` `PendingVerificationCadence`: `NONE`

`BaselineReconciliation`: `NONE`

<!-- When non-NONE, use one Markdown list entry per source cycle:
- `SourceCycle`: `<cancelled-cycle-id>`
  `Request`: `<source-cycle request summary>`
Preserve existing entries; see PROTOCOL.md, Baseline Reconciliation Format.
-->

## Handoff

`Kind`: `RESUME` `From`: `ARCHITECTING` `FailureType`: `NONE` `Reason`:
`Design rerun done (per-step instructions, effort high, -np, image size from provider limits, no 0.1.x compatibility); frame closed.`

## Recovery

`Active`: `false`

## Outstanding Obligations

`Active`: `false`

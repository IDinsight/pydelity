# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `DOCUMENTING` `CycleMode`: `STANDARD` `PendingCycleMode`:
`UNSET` `PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`CompletionPolicy`: `FULL_DELIVERABLE` `Id`:
`add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada`

`Request`:
`Start a new standard cycle on tz6/pipeline-step-2, after page extraction's sign-off and before step 3 (page-break verification). Three parts: (1) give the survey the producer and verifier approach page extraction has: after the survey's answer is accepted, a verifier request reviews it against the PDF and may return a corrected answer, which must pass the survey's checks; this replaces the survey cycle's rule that the survey uses Python checks only. (2) Make the verifier optional for every step, opt-in, so the user turns it on. (3) Finish the remaining issues; the candidates, for Scoper to settle with the user, are the page extraction entries under "Pushed to later steps" in artifacts/next_cycle_inputs.md (another PDF's page files in load(), snapping boxes to measured text, judging each page's stored text, the two box rules for the page prompt), the items under "Review findings and observations left for later", and any risk under "Risks and follow-up" the user wants closed. Inputs, in this order: the "Next cycle, before step 3: verifiers and remaining issues" section of artifacts/next_cycle_inputs.md first (including its points for Scoper and Architect: a rule for text differences when no verifier runs, the setting's shape, how it enters each step's fingerprint and estimate, what the page file's verification field and the report hold when no verifier runs, and what the survey's verifier may correct), then the rest of that file (the user decisions that apply to later steps, including acceptance by real runs on both providers and one structured-output mode per provider), page extraction's cycle records under .standards/docs/ (cycle build-step-2-page-extraction-of-the-20261119T174118Z-0419318a), and artifacts/design_brief.md. The work merges with page extraction and ships with it as 0.2.0. Added on 2026-11-21: as the cycle's first step, before the other work, Developer and Tester reorganize the constants, type aliases, classes, functions and methods in each module according to the updated ordering in the developer and tester user styles. Added on 2026-11-22, as user rework during synchronization and before 0.2.0: code's measurements of the PDF become hints only. (1) A code layer still measures facts about the PDF (such as stored text, page labels, rotation, repeated lines and form fields) and gives them to the model as hints. (2) The model may use the hints, but its own reading of the page decides the final answer; no message tells it to fix an answer to match a hint. (3) Where the answer and a hint disagree, the difference goes on the review list; a disagreement never causes a retry and never makes a run fail. (4) The rule applies to every step that calls a model: the survey, page extraction (its verifier included) and every later step. Reason: in the user's real runs on the GPF reading and math PDFs, the text check's retries pushed the model to merge each grade grid's nine grade cells into one cell to match stored lines such as "x x x x x" and "123456789", losing which grades the marks belong to, and its retry message made the verifier drop correct fixes. For Scoper to settle with the user: which checks count as hints (comparisons with the PDF) and which stay as the answer's own consistency checks that may still ask for a correction, and which facts stay hard limits (such as the page count); how hints reach the model, including whether the stored text goes into the first page request (cost, and what the docs say is sent); whether a malformed final answer should still stop a run, which is separate from hint mismatches; and the effect on AC-019 and on the scope's rule that code may send an answer back with a difference it found. Added on 2026-11-22 while scoping that rework: the survey's finding for each repeated line (page furniture, content or not decided) also reaches page extraction as a hint, not an order; no message tells the model to put a repeated line in an artifact item.`

`Scope`:
`.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
`Architecture`:
`.standards/docs/specs/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
`Development`:
`.standards/docs/development/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
`PromotionReason`: `NONE` `AuditTarget`: `NONE` `BlockedOn`: `NONE`
`PendingVerificationCadence`: `NONE`

`BaselineReconciliation`: `NONE`

<!-- When non-NONE, use one Markdown list entry per source cycle:
- `SourceCycle`: `<cancelled-cycle-id>`
  `Request`: `<source-cycle request summary>`
Preserve existing entries; see PROTOCOL.md, Baseline Reconciliation Format.
-->

## Handoff

`Kind`: `FORWARD` `From`: `REVIEWING_IMPLEMENTATION` `FailureType`: `NONE`
`Reason`:
`Implementation review of the hints rerun is COMPLETE with no material findings; Documenter updates the docs under recovery frame 1.`

## Recovery

`Active`: `true`

### Frame 1

`From`: `SYNCHRONIZING` `Owner`: `SCOPING` `FailureType`: `SCOPING` `Reason`:
`The user changed the request: code's measurements of the PDF become hints that never cause retries or failed runs, for every step; see Active Work.Request.`
`ResumeAt`: `SYNCHRONIZING` `RerunThrough`: `REVIEWING_FINAL`

## Outstanding Obligations

`Active`: `false`

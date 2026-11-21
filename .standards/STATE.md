# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `TESTING` `CycleMode`: `STANDARD` `PendingCycleMode`: `UNSET`
`PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`CompletionPolicy`: `FULL_DELIVERABLE` `Id`:
`add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada`

`Request`:
`Start a new standard cycle on tz6/pipeline-step-2, after page extraction's sign-off and before step 3 (page-break verification). Three parts: (1) give the survey the producer and verifier approach page extraction has: after the survey's answer is accepted, a verifier request reviews it against the PDF and may return a corrected answer, which must pass the survey's checks; this replaces the survey cycle's rule that the survey uses Python checks only. (2) Make the verifier optional for every step, opt-in, so the user turns it on. (3) Finish the remaining issues; the candidates, for Scoper to settle with the user, are the page extraction entries under "Pushed to later steps" in artifacts/next_cycle_inputs.md (another PDF's page files in load(), snapping boxes to measured text, judging each page's stored text, the two box rules for the page prompt), the items under "Review findings and observations left for later", and any risk under "Risks and follow-up" the user wants closed. Inputs, in this order: the "Next cycle, before step 3: verifiers and remaining issues" section of artifacts/next_cycle_inputs.md first (including its points for Scoper and Architect: a rule for text differences when no verifier runs, the setting's shape, how it enters each step's fingerprint and estimate, what the page file's verification field and the report hold when no verifier runs, and what the survey's verifier may correct), then the rest of that file (the user decisions that apply to later steps, including acceptance by real runs on both providers and one structured-output mode per provider), page extraction's cycle records under .standards/docs/ (cycle build-step-2-page-extraction-of-the-20261119T174118Z-0419318a), and artifacts/design_brief.md. The work merges with page extraction and ships with it as 0.2.0. Added on 2026-11-21: as the cycle's first step, before the other work, Developer and Tester reorganize the constants, type aliases, classes, functions and methods in each module according to the updated ordering in the developer and tester user styles.`

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

`Kind`: `CHECKPOINT` `From`: `DEVELOPING` `FailureType`: `NONE` `Reason`:
`Increment 1 ready: DEV-001 reordered src/pydelity and scripts (AC-041); Tester reorders tests (AC-042) and assesses both reorders.`

## Recovery

`Active`: `false`

## Outstanding Obligations

`Active`: `false`

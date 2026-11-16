# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `DEVELOPING` `CycleMode`: `STANDARD` `PendingCycleMode`:
`UNSET` `PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`CompletionPolicy`: `FULL_DELIVERABLE` `Id`:
`build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de` `Request`:
`Build pydelity, a standalone Python 3.13 library with a Typer CLI that turns (almost) any PDF into a faithful document.json with item-level provenance and optionally a per-PDF domain.json (steps 1-6: survey, page extraction, page-break verification, assembly, schema proposal, projection). It replaces KGForEdGlobal stages 1-3 and its document.json must stay usable by the KGForEdGlobal KG stage. Publishing to PyPI is a project goal. User rework 2026-11-16: this cycle is only the interactive repo setup (signed off by the user) plus a placeholder pydelity release on PyPI, published as early as possible so the user owns the name; the pipeline (steps 1-6) and a working PyPI release move to the next cycle. User rework 2026-11-16 (2): Markdown linting and formatting cover all Markdown files, including STANDARDS-generated ones, since those changes are cosmetic. Full request, design directions, evidence E1-E23 and open questions: artifacts/design_brief.md.`
`Scope`:
`.standards/docs/scope/build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de.md`
`Architecture`:
`.standards/docs/specs/build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de.md`
`Development`: `NONE` `PromotionReason`: `NONE` `AuditTarget`: `NONE`
`BlockedOn`: `NONE` `PendingVerificationCadence`: `NONE`

`BaselineReconciliation`: `NONE`

<!-- When non-NONE, use one Markdown list entry per source cycle:
- `SourceCycle`: `<cancelled-cycle-id>`
  `Request`: `<source-cycle request summary>`
Preserve existing entries; see PROTOCOL.md, Baseline Reconciliation Format.
-->

## Handoff

`Kind`: `FORWARD` `From`: `AUDITING` `FailureType`: `NONE` `Reason`:
`Initial greenfield audit complete: .standards/CONTEXT.md records the pre-implementation baseline.`

## Recovery

`Active`: `false`

## Outstanding Obligations

`Active`: `false`

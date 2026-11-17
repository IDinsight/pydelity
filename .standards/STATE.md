# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `SCOPING` `CycleMode`: `STANDARD` `PendingCycleMode`: `UNSET`
`PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`CompletionPolicy`: `FULL_DELIVERABLE` `Id`:
`build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c` `Request`:
`Build the pydelity pipeline and its first working PyPI release. pydelity is a standalone Python 3.13 library with a Typer CLI that turns (almost) any PDF into a faithful document.json with item-level provenance and, optionally, a per-PDF domain.json, through steps 1-6: survey, page extraction, page-break verification, assembly, schema proposal and projection. It replaces KGForEdGlobal stages 1-3, and its document.json must stay usable by the KGForEdGlobal KG stage. People must be able to install and use pydelity on Windows. The working release (0.1.0 or later) goes to PyPI once the pipeline is signed off. Inputs: artifacts/design_brief.md holds the full request, design directions, step design points, known source defects to design out, evidence E1-E23 and the KG consumer contract; its 'First work item: repo setup' section is done (just and prek replaced Make and pre-commit) and its open questions are answered in the next input. artifacts/next_cycle_inputs.md holds what the earlier repo-setup cycle left for this one: the user's answers to the brief's open questions; the pipeline constraints, non-goals, assumptions and outcomes scoped before the split, whose old AC numbers (AC-003 to AC-039) are retired so this cycle numbers its own; the setup's risks and follow-up (runtime dependencies, the Typer CLI and its console script, a PyPI release workflow with Trusted Publishing that zizmor also checks, whether to yank the 0.0.1 placeholder, Windows recipes that do not assume a POSIX shell, adding Python 3.14 to CI); and loose ends from the setup. The repo setup on main stays as it is unless this work needs a change: just, prek, Dependabot, zizmor, the Markdown rules that cover STANDARDS files, one pinned version per tool, and CI ('Lint and test' and 'TruffleHog secret scan' are required checks on main). Releases: release-please (.github/workflows/release-please.yml) versions and tags releases and writes CHANGELOG.md from the Conventional Commit messages on main but does not publish to PyPI; the PyPI workflow should publish from its GitHub releases; a feat: commit on main opens the 0.1.0 release pull request, which should be merged only once the pipeline is signed off. KGForEdGlobal (/Users/tzz/Projects/private/idi/KGForEdGlobal) is read-only reference material.`
`Scope`: `NONE` `Architecture`: `NONE` `Development`: `NONE` `PromotionReason`:
`NONE` `AuditTarget`: `NONE` `BlockedOn`: `NONE` `PendingVerificationCadence`:
`NONE`

`BaselineReconciliation`: `NONE`

<!-- When non-NONE, use one Markdown list entry per source cycle:
- `SourceCycle`: `<cancelled-cycle-id>`
  `Request`: `<source-cycle request summary>`
Preserve existing entries; see PROTOCOL.md, Baseline Reconciliation Format.
-->

## Handoff

`Kind`: `FORWARD` `From`: `AUDITING` `FailureType`: `NONE` `Reason`:
`Project context established in .standards/CONTEXT.md; Scoper defines the pipeline and release scope.`

## Recovery

`Active`: `false`

## Outstanding Obligations

`Active`: `false`

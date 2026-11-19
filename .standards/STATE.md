# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `DOCUMENTING` `CycleMode`: `STANDARD` `PendingCycleMode`:
`UNSET` `PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`CompletionPolicy`: `FULL_DELIVERABLE` `Id`:
`build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c` `Request`:
`Build step 1 (survey) of the pydelity pipeline, with the cross-cutting run features it needs, an official Astro docs site, and publish it as pydelity's first working PyPI release. pydelity is a standalone Python 3.13 library with a Typer CLI that will turn (almost) any PDF into a faithful document.json with item-level provenance and, optionally, a per-PDF domain.json, through steps 1-6: survey, page extraction, page-break verification, assembly, schema proposal and projection. It replaces KGForEdGlobal stages 1-3, and its document.json must stay usable by the KGForEdGlobal KG stage. This cycle builds only step 1; steps 2-6 come in later cycles. User decisions made while scoping this cycle (2026-11-17): the cycle ships every cross-cutting run feature that applies to the survey (CLI, optional JSON or YAML config and Python API, PDF input-limit check, cost ledger with estimate-and-confirm, --yes and max_cost, resume, Anthropic and OpenAI models, mocked tests, Windows install and use, review list in run.json with a CLI summary) plus an HTML report for the survey; CI also tests on Python 3.14; the survey-only release, version 0.1.0 (tag v0.1.0), goes to PyPI from release-please's GitHub release with Trusted Publishing once this cycle is signed off; the docs site uses Astro with Starlight like https://github.com/IDinsight/standards, built and link-checked on pull requests and published to GitHub Pages as versioned docs once a release tag exists; Windows contributor recipes stay out of this cycle. People must be able to install and use pydelity on Windows. Inputs: artifacts/design_brief.md holds the full request, design directions, step design points, known source defects to design out, evidence E1-E23 and the KG consumer contract; its 'First work item: repo setup' section is done (just and prek replaced Make and pre-commit) and its open questions are answered in the next input. artifacts/next_cycle_inputs.md holds what the earlier repo-setup cycle left for this one: the user's answers to the brief's open questions; the pipeline constraints, non-goals, assumptions and outcomes scoped before the split, whose old AC numbers (AC-003 to AC-039) are retired so this cycle numbers its own; the setup's risks and follow-up (runtime dependencies, the Typer CLI and its console script, a PyPI release workflow with Trusted Publishing that zizmor also checks, whether to yank the 0.0.1 placeholder, Windows recipes that do not assume a POSIX shell, adding Python 3.14 to CI); and loose ends from the setup. The repo setup on main stays as it is unless this work needs a change: just, prek, Dependabot, zizmor, the Markdown rules that cover STANDARDS files, one pinned version per tool, and CI ('Lint and test' and 'TruffleHog secret scan' are required checks on main). Releases: release-please (.github/workflows/release-please.yml) versions and tags releases and writes CHANGELOG.md from the Conventional Commit messages on main but does not publish to PyPI; the PyPI workflow should publish from its GitHub releases; a feat: commit on main opens the 0.1.0 release pull request, which should be merged only once this cycle is signed off. User decisions added 2026-11-17 after the first scope: when this cycle's work is merged into main, release-please opens a release pull request whose version is 0.1.0, and accepting it publishes v0.1.0 to PyPI; and pydelity ports over and reuses what it can from KGForEdGlobal, writing new or updated code for pydelity where that code does not fit, without changing KGForEdGlobal. KGForEdGlobal (/Users/tzz/Projects/private/idi/KGForEdGlobal) is otherwise read-only reference material. User decisions added 2026-11-17 during development: pydelity does not ship or maintain per-model PDF input limits, because keeping them current is not maintainable; it sends the PDF and shows the provider's error in the CLI (or raises it for library users) when a PDF is too large. max_cost no longer stops a run: when a run would go over it, pydelity warns and the CLI asks whether to continue; library callers still get the warning logged and choose with a boolean function argument whether the survey continues automatically. Answered 2026-11-17 while rescoping: a CLI run with --yes continues past max_cost after the warning, and a Python caller who does not pass the continue argument gets an error and a resumable run. User decision added 2026-11-17 during development: the probe's measured facts and their summary are saved in their own permanent output file, written right after measuring and before any API key check, cost question or model call, so a run that is declined, fails or has no API key still leaves them on disk; the summary is also logged. Confirmed 2026-11-17 while rescoping, after learning that pdf_survey.json holds the facts only once the survey finishes: keep the separate facts file. User decisions added 2026-11-17 during development: the number of provider retries (today the SDKs' default of 2) is configurable; the Python API adds measure(pdf, ...), which measures the PDF and writes pdf_facts.json with no model call or API key, and load(output_dir), which reads a finished output folder back as Python objects; the API also offers async versions of its functions, named with an a prefix (arun, asurvey, aestimate and so on); and the survey keeps Python checks only, with no model verifier (producer-verifier is left to later steps such as page extraction). User decision added 2026-11-17 during development: BCP-47 language tags (the languages setting and the survey's language check) are checked with the langcodes library, added as a runtime dependency, instead of a hand-written pattern. User decision added 2026-11-18 during development: the sync Python API functions use asyncio.run only; called while an event loop is already running (in a Jupyter cell or in async code), they raise an error saying to await the async version (such as await pydelity.arun(...)), instead of running the coroutine on a worker thread, which kept the sync functions working there at the cost of much more code. User decision added 2026-11-18 during development: the survey's model defaults to trusting its own reading of the PDF over the probe's measured facts, which are hints, because it is the more capable reader (vision); this applies to page numbers and in general. It follows a run where the probe took numbers in table cells for printed page numbers and the page-numbering check made the model agree with them. Answered 2026-11-18 while rescoping: the model's answer is kept where it disagrees with the measured rotation or printed page numbers, and each disagreement goes on the review list; every answer still says, for each repeated line, whether it is page furniture or content. User decision added 2026-11-18 after development, before testing: add a root-level examples/ folder with a JSON and a YAML config file that users can copy as a starting template for pydelity's settings.`
`Scope`:
`.standards/docs/scope/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c.md`
`Architecture`:
`.standards/docs/specs/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c.md`
`Development`:
`.standards/docs/development/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c.md`
`PromotionReason`: `NONE` `AuditTarget`: `NONE` `BlockedOn`: `NONE`
`PendingVerificationCadence`: `NONE`

`BaselineReconciliation`: `NONE`

<!-- When non-NONE, use one Markdown list entry per source cycle:
- `SourceCycle`: `<cancelled-cycle-id>`
  `Request`: `<source-cycle request summary>`
Preserve existing entries; see PROTOCOL.md, Baseline Reconciliation Format.
-->

## Handoff

`Kind`: `RESUME` `From`: `DEVELOPING` `FailureType`: `NONE` `Reason`:
`PdfError docstring, its reference page and the docs site's Node floor fixed in DEV-001 and DEV-019 with no behavior change. Documenter fixes the Python guide's error table and the docs-site page's Node.js version; final review then rechecks all three.`

## Recovery

`Active`: `true`

### Frame 1

`From`: `SYNCHRONIZING` `Owner`: `DEVELOPING` `FailureType`: `IMPLEMENTATION`
`Reason`:
`User asked to fix final review's withdrawn F-001 to F-003: PdfError docstring and reference, Python guide error table, docs-site Node.js version.`
`ResumeAt`: `SYNCHRONIZING` `RerunThrough`: `REVIEWING_FINAL`

## Outstanding Obligations

`Active`: `false`

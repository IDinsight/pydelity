<!-- STANDARDS
Artifact: DOCUMENTATION
Cycle: build-step-3-page-break-verification-of-20261122T170208Z-00fe2896
-->

# Documentation Record

`Cycle`: `build-step-3-page-break-verification-of-20261122T170208Z-00fe2896`
`Status`: `COMPLETE` `Collaboration`: `AUTONOMOUS` `Target`: `ACTIVE_CHANGE`
`Target Detail`: `the active cycle` `User Style`: `tony`

## Assessed Inputs and Boundary

- Started 2026-11-22 on `tz6/pipeline-step-3`, HEAD `acee8e2`, clean tree. The
  comparison is HEAD against the working tree. Every documentation change in
  this record is unstaged or untracked on top of `acee8e2`. HEAD already holds
  the cycle's code, tests and the Developer, Tester and implementation Reviewer
  records.
- Records, by the first 16 hex digits of their SHA-256, unchanged from start to
  finish:
  - scope `.standards/docs/scope/<cycle>.md` `c0f8b54a9851b32c`
  - design `.standards/docs/specs/<cycle>.md` `e9006fbf2a78ee99`
  - plan `.standards/docs/development/<cycle>.md` `01434a6d99513f03`
  - verification `.standards/docs/verification/<cycle>.md` `41861e7f5baec0a1`
  - implementation review `.standards/docs/reviews/<cycle>/implementation.md`
    `47accb225ac7dc58`
  - context `.standards/CONTEXT.md` `0e940ffe605aecff`
- Behavior sources inspected: `src/pydelity/api.py` (`averify_breaks`,
  `verify_breaks`, `aestimate`, `load`), `providers/ledger_model.py` (the
  `ProviderError` label), the CLI's `--help` and the stand-in providers in
  `tests/fixtures/mock_providers.py`. Generated reference pages under
  `docs/src/content/docs/reference/` are a generation output, not edited.
- Editing boundary: README, the docs site's guides, start pages, FAQ and
  contributing page, the docs site's sidebar and description in
  `docs/astro.config.mjs`, and `artifacts/next_cycle_inputs.md`. No source,
  test, fixture, example, package or release config was changed.
- Collaboration and target: no choice in the request or scope, so the defaults
  for new work. User style `tony` (`.standards/user-styles/documenter/tony.md`),
  selected by the user in the invocation. Technology style: Python, for the code
  examples.
- Project references: `NONE`.
- User decision: the new guide's name. The scope requires approval for new
  public names. The user chose `docs/src/content/docs/guides/page-breaks.md`
  (URL `/guides/page-breaks/`, title "Verify page breaks"), placed after
  "Extract pages" in the sidebar. `Active Work.BlockedOn` was set before the
  question and cleared after it.

## Documentation Work and Evidence

Audiences: users who run pydelity from the command line or Python, and
maintainers who run the smoke test. Each surface below was edited, saved,
formatted and read back. Hashes are the final content.

### New guide: Verify page breaks

`docs/src/content/docs/guides/page-breaks.md` `9eb39f2f3303afdd`, and its
sidebar entry in `docs/astro.config.mjs` `be3ee3c7729d01e9`. It covers what a
verdict holds (pieces, joins, text joins, cell joins, repeated header rows,
repeated items, markers, containers, reason), the pause after page extraction,
the rule that every page needs a current page file and what a narrowed `pages`
selection or `overwrite` does, the step's model and instructions, what each
request sends, `no_content` breaks, checks, the `start_markers` hint, the
verifier, concurrency and failures. ACs: `AC-046`, and the user-facing behavior
of work items 1 to 4 (`AC-001` to `AC-039`).

### Guides changed for the third step

- `guides/outputs.md` `02ee5d1cc6ddb1be`: the `page_breaks/` folder, the
  report's page-break cards, the `paused` status after extraction, `steps`
  entries and `breaks` counts, the `missing_page_files` warning, review-list
  order, checks a verdict still fails, places where a verdict and the survey
  disagree, and a new "Verdict files" section.
- `guides/reruns.md` `53149bb09d30660a`: what a verdict file is reused against,
  that re-extracting a page re-judges its two breaks, `overwrite` and `pages`,
  and stopped or failed runs.
- `guides/verifiers.md` `5f87ec9f1c3ec649`: `advanced.page_breaks.verify`, the
  page-break verifier, its cost line, report, log, files and costs, and
  `no_content` breaks.
- `guides/page-extraction.md` `d856bc91d121530d`: the pause after extraction,
  and that page-break verification needs every page.
- `guides/models-and-providers.md` `51f9aa9f689cf7a0`: the step's model, effort,
  what each request sends, no upload, timeouts, `concurrent_breaks`, and a new
  "When page-break verification fails" section.
- `guides/costs.md` `2465559f18a40832`: the step's estimate line, what it
  counts, ledger agents `judge` and `verifier`, `by_step`, and ways to spend
  less.
- `guides/command-line.md` `f5c1956e20168bbb`: three runs or one, the verbose
  break line, the summary line and exit codes.
- `guides/configuration.md` `af45581b53f307cd`: the eight
  `advanced.page_breaks.*` settings.
- `guides/python.md` `94e7c3b8cf3f205a`: `averify_breaks` in the functions table
  (async functions first, sync names after), a new "Verify page breaks" section,
  `RunResult.breaks`, `StepEstimate.breaks`, `load` with breaks, and
  `PageBreakError`.

ACs: `AC-046`, `AC-048`, and the user-facing behavior of `AC-001` to `AC-039`.

### Start pages, FAQ, overview and contributing

- `start/first-survey.md` `4ebc1d42abfbb006`: the pause after extraction, a new
  "Verify the page breaks" section, the `page_breaks/` row and the report card.
- `index.md` `27fb6ac8c192adf3`, `faq.md` `d26a9f1e4eb3b03e`: the third step,
  three new page-break questions, a "Verifiers" heading, and answers on the
  default model, what is sent, cost, reruns and stopped runs.
- `contributing/development.md` `0e6c96c3cbc10e21`: the smoke test runs all
  three steps, as `68b675c` made it do.
- The docs site's description in `docs/astro.config.mjs` names all three steps.

ACs: `AC-046`, `AC-048`.

### README

`README.md` `54eb0adac395db69`: three steps with an optional verifier for each,
the third run, `pages` and `--no-pause`, a `result.breaks` loop in the Python
example, and links. The package description and classifiers in `pyproject.toml`
already name the three steps and the verifiers (Developer, checked by Tester and
the implementation review). ACs: `AC-044`, `AC-048`.

### Reference pages

No source, docstring or generator changed, so the reference pages need no
regeneration. They were regenerated anyway and match byte for byte
(`page-break-json` `89a26f4198085e31`, `page-break-checks` `57008dbfe7e8ce96`,
`python-api` `3b3e4c3b46daf996`, `run-json` `232c48e46dfc3abe`, `configuration`
`bbe8c2a9afb6b921`, `cost-jsonl` `57d5fba603690cdf`). AC: `AC-047`.

### Next cycle inputs

`artifacts/next_cycle_inputs.md` `f9f1cb0b9c34460d`: under "Pushed to later
steps", removed the completed "Page files of another PDF in a reused folder
(step 3)" entry and added four pushed entries (continuation between pages that
do not follow each other, a page with no content items between two pages,
"continued on the next page" notes on the earlier page, and structure tags as
evidence). Entries for "each later step" stay, because they still apply after
step 3. Observations L1 to L5 from the implementation review and the
`ProviderError` label were added under "Observations left for later". AC:
`AC-049`.

### Behavior ACs, by where the docs cover them

These ACs belong to Developer and Tester. The docs describe the behavior they
set, as the verification report and the stand-in runs show it, without restating
the criteria.

- Running the step in the pipeline: `AC-001`, `AC-002`, `AC-003`, `AC-004`,
  `AC-005`, `AC-006`, `AC-007`, `AC-008`, `AC-009`, `AC-010`. Covered in
  `guides/page-breaks.md` ("Check the page files first", "Every page needs a
  page file"), `guides/command-line.md`, `guides/python.md`, `guides/outputs.md`
  and `start/first-survey.md`.
- Judging each break: `AC-011`, `AC-012`, `AC-013`, `AC-014`, `AC-015`,
  `AC-016`, `AC-017`, `AC-018`, `AC-019`, `AC-020`, `AC-021`, `AC-022`. Covered
  in `guides/page-breaks.md` ("What you get", "Choose the model", "Tell the
  model about your PDF", "How a break is judged"),
  `guides/models-and-providers.md` and `guides/outputs.md` ("Verdict files").
- Checking every verdict: `AC-023`, `AC-024`, `AC-025`, `AC-026`, `AC-027`,
  `AC-028`, `AC-029`, `AC-030`, `AC-031`. Covered in `guides/page-breaks.md`
  ("How a verdict is checked"), `guides/verifiers.md`, `guides/outputs.md` and
  `guides/models-and-providers.md` ("When page-break verification fails").
- Paying for, resuming and stopping the step: `AC-032`, `AC-033`, `AC-034`,
  `AC-035`, `AC-036`, `AC-037`, `AC-038`, `AC-039`. Covered in
  `guides/costs.md`, `guides/reruns.md`, `guides/verifiers.md`,
  `guides/command-line.md` and `guides/page-breaks.md` ("Breaks run at the same
  time").

### No documentation change needed

- `AC-040`, `AC-041` and `AC-042`: tests and CI, owned by Tester and CI. The
  contributing page already describes how to run them, and only the smoke test
  changed.
- `AC-043`, `AC-045`: the wheel check and release setup. The release docs
  (`contributing/releases.md`) already describe the release-please flow and need
  no change for 0.3.0.
- `AC-050`, `AC-051`: the user's real runs, not documentation.

## Checks and Applicability

All commands ran from the repository root on macOS with the project's `.venv`
unless noted. Each passed with exit code 0.

1. Formatting.
   `PATH=<cached prek node env>/bin:$PATH node scripts/format_markdown.mjs` with
   Prettier 3.10.1, the version `.pre-commit-config.yaml` pins. `prek exec`
   itself could not run because the sandbox blocks writes to
   `~/.cache/prek/prek.log`, so the cached hook binaries were run directly. It
   formatted the changed files and ran `check.mjs`, which passed.
2. Lint. `markdownlint-cli2` v0.24.1 (markdownlint v0.42.1) from the cached hook
   env: 242 files, 0 issues.
3. Build. `pnpm run build` in `docs/`: 32 pages built. `pnpm run check-links`:
   local links and fragments in 32 pages checked, none broken. The new anchors
   `#verdict-files`, `#when-page-break-verification-fails`,
   `#check-the-page-files-first`, `#every-page-needs-a-page-file`,
   `#how-a-verdict-is-checked`, `#what-you-get` and the reference page's
   `#verification` are each present once in the built HTML. `pnpm install` was
   not run, because it needs the network and `node_modules` was present.
4. CLI behavior. A scratch script ran the installed `pydelity` command three
   times against `MockProviders` on
   `tests/fixtures/pdfs/irs_form_1040a_1965_scan.pdf`, with fixture survey, page
   and break answers. It confirmed the pause message after extraction, the
   `missing_page_files` warning text, that a narrowed run completes without a
   pause, the estimate lines with and without the verifier, the verbose break
   line, the summary line, verdict file fields, `run.json` `steps[].breaks` and
   `by_step.page_breaks`, `cost.jsonl` agents and the report's page-break card.
   `pydelity --help` lists every option the docs use, with `-np`, `-v` and `-y`.
5. Python examples. A scratch script ran, in process against `MockProviders`,
   the `averify_breaks` loop and the `averify_breaks` call with
   `advanced.page_breaks.instructions` from the guides, the `aestimate` loop
   with `step.breaks`, the README's `arun` example twice, and the `load`
   example. All ran. The second `arun` reported `page_breaks` as `reused` with
   `BreakCounts(judged=0, reused=1, total=1)`, and `result.breaks` held the
   reused verdict.
6. Reference pages. `.venv/bin/python scripts/generate_reference_docs.py` (the
   `just docs-reference` recipe runs the same script through `uv run --locked`)
   wrote 13 pages. After formatting, `git status` showed no change under
   `docs/src/content/docs/reference/`.
7. Style. The added text was searched for semicolons in prose, colons that set
   up a reveal, British spellings, process references (step numbers, AC or DEV
   IDs) and AI-sounding phrases. Semicolons appear only in quoted program
   output. Two new colon reveals were reworded. Step numbers appear only in
   `artifacts/next_cycle_inputs.md`, where the project uses them.
8. `node .standards/bin/check.mjs`: passed, after the record was completed.

Limits:

- The stand-in providers return fixture answers and made-up costs. The costs
  example in `guides/costs.md` comes from the stand-in run's estimate, which
  uses real prices and the fixture PDF, not from a real model call. The verbose
  break line example leaves out its cost for this reason.
- These checks show the docs match the code's behavior with canned answers.
  Whether real models give good verdicts is `AC-050` and `AC-051`.

## Discrepancies, Dependencies, and Remaining Work

`NONE` for documentation. Dependencies outside this role, none of which blocks
this gate:

- `AC-042` (CI on Linux, macOS and Windows) and `AC-045` (the 0.3.0 release pull
  request) happen after merge, as the scope says.
- `AC-050` and `AC-051` are the user's real runs. Any issue they raise may need
  doc changes in a later rework.
- Final review must check this record and the documentation against the scope.

## Resume and Conclusion

- Next: final review (`REVIEWING_FINAL`, kind `FINAL_DELIVERABLE`). On a rework,
  compare the hashes above with the current files first.
- Blocking question: `NONE`.
- The selected target and the full Documenter gate are both complete. Full
  documentation completion is not cycle completion or sign-off. See
  `.standards/STATE.md` for routing.

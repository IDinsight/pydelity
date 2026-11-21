<!-- STANDARDS
Artifact: DOCUMENTATION
Cycle: add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada
-->

# Documentation Record

`Cycle`: `add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada`
`Status`: `COMPLETE` `Collaboration`: `AUTONOMOUS` `Target`: `ACTIVE_CHANGE`
`Target Detail`: `the active cycle` `User Style`: `tony`

## Assessed Inputs and Boundary

- Workflow: `STANDARD`, `FULL_DELIVERABLE`, project `BROWNFIELD`, entered from a
  `FORWARD` handoff out of `REVIEWING_IMPLEMENTATION`. No recovery, no
  outstanding obligations. Current ACs `AC-001` to `AC-042`, none retired.
- Contract and owner evidence, by last commit and SHA-256 prefix, read at
  `31cbf8a` with a clean tree:
  - scope
    `.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`49448e5`, `dd6ea5291602`);
  - design
    `.standards/docs/specs/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`81d7dcd`, `3c0eddfeb9d1`), decisions 1–13, **Interfaces and Contracts**,
    **Docs and docstrings**, **Risks and Follow-up**;
  - development plan
    `.standards/docs/development/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`b579737`, `4251351f9aef`; `COMPLETE`; approved names `verify`,
    `advanced.survey.verify`, `advanced.extraction.verify`, `--verify`/`-vf`,
    agent `surveyor`);
  - verification report
    `.standards/docs/verification/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`fc6df7d`, `2aceaad01ae2`; `COMPLETE`, `FULL`; its E43 lists the docs
    wording left to Documenter);
  - implementation review
    `.standards/docs/reviews/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada/implementation.md`
    (`31cbf8a`, `7e0539ce3ca5`; `COMPLETE`, no material findings; later
    dependencies on Documenter for `AC-030` README part, `AC-032`, the FAQ and
    guide part of `AC-034`, `AC-035` to `AC-038`);
  - project context `.standards/CONTEXT.md` (`0573e11`, `09045f457b2d`);
  - page extraction's final review
    `.standards/docs/reviews/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a/final-deliverable.md`,
    limitations L-3 to L-9, the source of the wording that `AC-034` to `AC-036`
    name.
- Behavior inspected in source at `31cbf8a`: `config/schemas.py` (the three
  settings and resolved properties), `cli.py` (`--verify`/`-vf`, the question on
  standard error at line 77), `surveying/prompts.py` (`_REVIEW`, `_VERDICT`,
  `verify_survey`), `surveying/survey.py` (`_verifier_outcome`, the reuse log
  line, `survey_fingerprint`, which leaves out `pdf_name`),
  `surveying/schemas.py`, `extracting/extraction.py` (`_kept_answer`,
  `_page_issues`, `_reusable_page`, `_verifier_outcome`, the page log line),
  `extracting/agents.py` (the verifier's correction retries),
  `extracting/validators.py` (`_failure` details `{"item_ref": ...}`,
  `review_issues`), `extracting/prompts.py` and `text_layer.py` docstrings,
  `report/html.py` (`_verifier_text`), `pipeline/runner.py` (`_log_estimate`,
  `_load_pages`, the skipped step with `pages: null`), `costs/ledger.py` (a
  damaged line before the last raises `OutputError`), `costs/budget.py`.
- Baseline: `31cbf8a` (`HEAD`, clean). Every change in this record is
  uncommitted work on top of it, listed with hashes under **Documentation Work
  and Evidence**. Nothing else in the tree changed.
- Editing boundary: the README, the docs site's hand-written pages and its
  sidebar entry, docstrings (no behavior), the generated reference pages through
  `scripts/generate_reference_docs.py` and Prettier only, and
  `artifacts/next_cycle_inputs.md`. No code, test, fixture, example config or
  tooling changed.
- Environment: macOS arm64, Python 3.13.9 (`.venv`, editable install), Node
  23.10.0, the repo's locked uv, prek, Prettier and markdownlint.
- Style files: `styles/universal.md`, `styles/python.md` (docstrings), user
  style `.standards/user-styles/documenter/tony.md` (`797def3`, `e93537bf4a93`).
  `references/readme.md` was not needed: the README kept its structure.
- Project references loaded: `NONE` (`.standards/project-references/documenter/`
  does not exist).

## Documentation Work and Evidence

Saved content, by SHA-256 prefix after the last formatting pass:

- `docs/src/content/docs/guides/verifiers.md` `8d2edcacea82` (new) and its
  sidebar entry in `docs/astro.config.mjs` `2d773a3bf4a8`, after the page
  extraction guide, as the page extraction cycle added its guide. Users who
  decide whether to pay for a verifier. It covers turning the verifiers on for
  every step (`--verify`/`-vf`, `verify: true`, `verify=True`) or one step
  (`advanced.survey.verify`, `advanced.extraction.verify`, `true`/`false`/`null`
  in a file or from Python), what each verifier reviews (the survey checklist
  from `_REVIEW`, the page checklist), the verdict outcomes, a table of which
  issues go on the review list with no verifier, a passed or kept correction,
  and problems not kept, the cost with estimate lines, reading the outcome in
  the report, the log, `verification` and `cost.jsonl`, turning a verifier on or
  off later, and a failed verifier request. `AC-032`, `AC-002`, `AC-003`,
  `AC-005`, `AC-006`, `AC-007` to `AC-020` (user-facing behavior), design
  **Risks and Follow-up** ("the docs should say so" for turning a verifier off).
- `README.md` `898dfbef56e2`: the "second model reviews every page" sentence
  replaced by an optional verifier for each step, a second request to the same
  model, off unless turned on; `--verify` added to the run options; the guides
  list names verifiers. `AC-030` (README part), `AC-032`, `AC-037`.
- `docs/src/content/docs/index.md` `f078026c81a2`: the same correction and a
  link to the new guide. `AC-032`.
- `guides/page-extraction.md` `ab66829e8da0`: the verifier is off by default and
  reviews each page only when on; what a page request sends (repeated lines with
  what the survey found each to be, form fields with their values, no other
  stored text) and that text retries quote stored lines; the text-difference
  rule with and without a verifier. `AC-019`, `AC-032`, `AC-034`.
- `guides/outputs.md` `f96c3b9df996`: the report's survey and page verifier
  lines or "no verifier ran"; the survey's differences left off the list when
  its verifier passed or its correction was kept; text differences on every page
  no verifier reviewed; `verifier` issues from both steps; `verification: null`;
  `pdf_survey.json`'s `checks`, `issues` and `verification`. `AC-011`, `AC-013`,
  `AC-014`, `AC-019`, `AC-020`, `AC-032`.
- `guides/configuration.md` `2658de7bd63b`: the two overrides in the advanced
  settings table and a link to the new guide. `AC-003`, `AC-032`.
- `guides/costs.md` `cc1f39c72e75`: the extraction estimate example is the
  default, unverified one; a verifier's requests and the named estimate line;
  every `cost.jsonl` line names its agent (`surveyor`, `extractor`, `verifier`);
  `by_step` includes the verifier; after "no", requests in progress are canceled
  and may still be billed; leaving the verifiers off. `AC-005`, `AC-015`,
  `AC-016`, `AC-036`, `AC-037`.
- `guides/reruns.md` `71b95d50c6c0`: the survey's inputs hold the PDF's hash,
  not its name; the verifier switches are not inputs, with the reuse rule;
  `pydelity.load` returns only the folder's PDF's page files; a damaged
  `cost.jsonl` line before the last stops every run with an `OutputError`;
  another PDF's leftover page files are left out of `run.json`, the report and
  `load`. `AC-006`, `AC-021`, `AC-036`.
- `guides/models-and-providers.md` `7f0b8fef76a2`: what the survey's verifier
  sends; what page requests send of the stored text (repeated lines, form field
  values, quoted lines in text retries); the verifier in a second request only
  when on; a failing survey verifier saves no `pdf_survey.json`. `AC-012`,
  `AC-017`, `AC-034`.
- `guides/python.md` `cfae1aea7126`: every function except `load` takes the PDF,
  and `load` takes the folder; `RunResult.pages` from a run is the selected
  pages; a `verify=True` example; `step.verifier` in the estimate example; the
  `load` example no longer reads `page.verification.verdict`, which is `None` by
  default and would raise `AttributeError`; `load`'s pages are the facts' PDF's
  only; `SurveyError` and `ExtractionError` cover the verifiers; `OutputError`
  covers a damaged ledger line. `AC-002`, `AC-021`, `AC-036`, `AC-037`.
- `guides/command-line.md` `98c1723dd3c6`: a `--verify` example; the verbose
  output names the verifier outcome; the log example adds `--yes`, because the
  question also goes to standard error. `AC-002`, `AC-036`.
- `start/first-survey.md` `399c62b37113`: the extraction estimate line and the
  requests per page match the default; a note on `--verify`. `AC-037`.
- `faq.md` `8de2f7eb8e3e`: a new question on the verifiers; the survey's
  differences stay off the list when its verifier accepts the answer; page
  extraction's list of what is sent includes the repeated lines' stored text and
  form field values; `advanced.uploads.expiry_hours` in full; one request per
  page by default; turning a verifier on redoes unreviewed outputs. `AC-032`,
  `AC-034`, `AC-036`, `AC-037`.
- Docstrings (no behavior; none of these models is in an output type sent to a
  model: those are `PageAnswer`, `VerifierVerdict`, `SurveyAnswer` and
  `SurveyVerdict`):
  - `src/pydelity/review.py` `14530d7b6827`: `CheckFailure.details` gives the
    survey's example and page extraction's `{"item_ref": "t3"}`, saying the ref
    comes from the answer and page file items have IDs instead;
    `ReviewIssue.details` gives the survey comparison's, a page check's, a
    `no_matching_label` issue's and a `verifier` issue's details.
  - `src/pydelity/extracting/schemas.py` `863f1617f27a`:
    `ExtractionCheckResult.failures` no longer says a failure "names" its item
    in `details`; it says the review issue names the item by ID in `item_id`.
  - `src/pydelity/pipeline/schemas.py` `fc28fb76c358`: `StepRecord.pages` is
    also `None` for a skipped page extraction step.
  - Regenerated: `reference/page-json.md` `cdd59c85b960`,
    `reference/pdf-survey-json.md` `37bf7aaf8987`, `reference/run-json.md`
    `0c2c05dac01d`. `AC-033`, `AC-035`.
  - Reading of `AC-035`: page extraction's failure details do hold the answer's
    `item_ref`, so an accurate example shows it. The reference now says what
    that ref is and that it is not an item ID, and points to `item_id` for the
    item, rather than saying the failure names the item.
- `artifacts/next_cycle_inputs.md` `5568740b9c12`: a **Verifier per step (each
  later step)** entry under **Pushed to later steps** (opt-in, the global
  `verify` and an `advanced.<step>.verify` override of its own, and what each
  later step adds); the title and the section before step 3 now summarize what
  the verifier cycle settled; the user decisions, the 0.2.0 summary (page file
  `verification`, reuse, `load()`, agents, estimates, report, the stand-in's
  survey verifier marker) and the risks match this cycle; the fixed review items
  are removed and the remaining ones kept (crops after an interrupted
  `overwrite`, temporary files and image limits, the structure walk's cap, the
  page JPEG's byte cap, figure crops' pixel cap, the crop-clipping design
  wording, and the three page extraction entries under **Pushed to later
  steps**). `AC-038`.
- No change needed, assessed:
  - `start/install.md`, `need-help.md`, `contributing/development.md`,
    `contributing/docs-site.md`, `contributing/releases.md`: nothing they say
    changed this cycle; `releases.md` already gives `feat:` as 0.1.1 → 0.2.0
    (`AC-031`). The module order (`AC-041`, `AC-042`) is a rule of the user
    styles, which the contributing guide does not cover.
  - The other generated reference pages: regenerated with no change from the
    committed ones (`AC-033`, already covered by Developer and Tester's E43).
  - `examples/config.json`, `examples/config.yaml`, `pyproject.toml`:
    Developer's (`AC-004`, `AC-030` package part); their comments and
    description were read and match the guides.
  - `AGENTS.md`, `CLAUDE.md`: STANDARDS guidance only, no project guidance about
    this work.
- Every current AC, by ID:
  - Documented in the new guide and the pages above: `AC-001`, `AC-002`,
    `AC-003`, `AC-004` (the configuration guide already points to the example
    files, which now hold the new settings), `AC-005`, `AC-006`, `AC-007`,
    `AC-008`, `AC-009`, `AC-010`, `AC-011`, `AC-012`, `AC-013`, `AC-014`,
    `AC-015`, `AC-016`, `AC-017`, `AC-018`, `AC-019`, `AC-020`, `AC-021`.
  - Documentation ACs, saved and checked above: `AC-030` (README part),
    `AC-032`, `AC-033`, `AC-034`, `AC-035`, `AC-036`, `AC-037`, `AC-038`.
  - No documentation impact: `AC-022` (report tables), `AC-023` (outline links),
    `AC-024` (inline widgets) and `AC-025` (the `TEXT_FLAGS` comment,
    Developer's) restore expected behavior that no page described otherwise.
    `AC-026`, `AC-027`, `AC-028`, `AC-029` and `AC-031` are tests, CI and
    release readiness, which the contributing pages already describe correctly.
    `AC-041` and `AC-042` reorder code and change no documented behavior.
  - Not documentation: `AC-039` and `AC-040`, the user's real runs after this
    phase.

## Checks and Applicability

All from the repository root on the saved content above, 2026-11-21.

- Reference pages: `.venv/bin/python scripts/generate_reference_docs.py`, then
  `uv run --locked prek exec prettier-markdown -- node scripts/format_markdown.mjs`
  (outside the sandbox, which blocks uv's cache in `~/.cache`): afterward only
  `page-json.md`, `pdf-survey-json.md` and `run-json.md` differ from `HEAD`,
  with the docstring changes shown above. Running both again gives the same
  bytes, which is the check CI makes.
- `just lint-markdown` (outside the sandbox): Prettier formatted the changed
  pages, `STANDARDS check passed.`, `markdownlint-cli2 ... Passed`, exit 0.
- `just docs-build` (outside the sandbox): `29 page(s) built`, then
  `Checked local links and fragments in 29 HTML pages.`, exit 0. This covers the
  new page's sidebar entry and every anchor the changed pages link to.
- Python, after the docstring edits: `.venv/bin/ruff check scripts src tests`
  "All checks passed!"; `.venv/bin/ruff format --check scripts src tests` "89
  files already formatted"; `.venv/bin/ty check scripts src tests` "All checks
  passed!"; `.venv/bin/interrogate scripts src tests` 100.0% (badge unchanged);
  `.venv/bin/pytest -q --numprocesses auto -p no:cacheprovider` 207 passed;
  `.venv/bin/pytest -q --doctest-modules src -p no:cacheprovider` 28 passed, 1
  skipped. All exit 0.
- Estimate lines, with the stand-in survey answer
  `tests/fixtures/survey_answers/irs_form_1040a_1965_scan.json` and the 2-page
  `irs_form_1040a_1965_scan.pdf`, the CLI run with placeholder keys, base URLs
  on a closed local port and input from `/dev/null`, so it stopped at the
  question with exit 3 and sent nothing:
  - no survey yet:
    `Survey cost estimate: about $0.24, at most $2.53 (up to 3 requests ...)`
    (unchanged from the docs) and with `--verify`
    `Survey with its verifier cost estimate: about $0.47, at most $5.45 (up to 6 requests ...)`;
  - survey saved:
    `Extraction cost estimate: about $0.23, at most $4.81 (2 pages, up to 6 requests ...)`,
    and with `advanced.extraction.verify: true`
    `Extraction with its verifier cost estimate: about $0.45, at most $10.41 (2 pages, up to 12 requests ...)`,
    the same figures the docs showed from a real run before verifiers became
    optional, so the stand-in survey gives the real run's page estimate;
  - `--verify` on a folder whose survey has no verification estimates the survey
    again, as decision 2 says.
  - The FAQ's 6-page form, `irs_form_w9.pdf`: `about $0.36, at most $2.90`,
    unchanged.
- Python examples, run against the stand-in (`MockProviders` with the fixtures
  above and a passing survey verdict) in a scratch folder: the README example;
  the `load` example with `page.verification is not None` (`False` for default
  runs); `aestimate(..., verify=True)` with `step.verifier` (`True` for both
  steps); `arun(..., verify=True)` (survey and both pages verified, agents
  `extractor`, `surveyor`, `verifier`);
  `advanced={"extraction": {"verify": True}}` (survey `verification` `None`,
  both pages verified). All ran.
- CLI examples, against the stand-in: the pause message, the "Run completed"
  summaries for a new and a reused extraction, and the invalid-settings output
  (exit 2) match the pages that quote them.
- Wording: a search of the README, the docs pages, `src/`, `examples/` and
  `pyproject.toml` for "second model", "reviews every page", "one to review",
  "two requests", "verifier model", "doesn't send the text stored" and "names it
  in" finds nothing. The added lines have no workflow terms, step numbers or
  IDs.
- Not run: Python 3.14 locally, the wheel smoke test and CI. No code behavior
  changed, so the implementation evidence in the verification and review reports
  still applies; CI's stale-reference and docs jobs cover these files once
  committed.

## Discrepancies, Dependencies, and Remaining Work

No `DOC-NNN` entry is open: nothing in the documentation contract is unmet.

Non-blocking observations, outside this record's ownership, which do not stop
this gate because no AC or documented behavior depends on them:

- The generated CLI reference's exit code `0` reads "The run completed, with or
  without review issues", from the command's help text, and leaves out a paused
  run. The command-line guide's exit code table covers the pause. Owner:
  Developer, if the user wants it changed.
- A run stopped at the question before page extraction lists `pages/` and
  `figures/` among the output folder's files even when neither exists yet.
  Owner: Developer, if the user wants it changed.

Dependencies after this gate, owned by others:

- Final Reviewer: assesses this record and the changed pages
  (`FINAL_DELIVERABLE`).
- Synchronizer: reconciles the deliverable. The docstring edits change three
  files under `src/` after Tester's and the implementation review's assessed
  content (`git diff 31cbf8a -- src` is docstrings only).
- The user: `AC-039` and `AC-040`, the real runs on both providers.

## Resume and Conclusion

- Done: every required documentation surface for this cycle assessed and updated
  or given a no-change reason; checks above pass on the saved content.
- Next: final review in a separate session. On resume, recompare the hashes
  above with the working tree.
- Blocking question: `NONE`.
- Selected target `ACTIVE_CHANGE` and the full Documenter gate are complete.
  This is not cycle completion or sign-off. Normal handoff: `REVIEWING_FINAL`,
  kind `FINAL_DELIVERABLE`, with `CompletionPolicy: FULL_DELIVERABLE`.

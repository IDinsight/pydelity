<!-- STANDARDS
Artifact: DOCUMENTATION
Cycle: add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada
-->

# Documentation Record

`Cycle`: `add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada`
`Status`: `COMPLETE` `Collaboration`: `AUTONOMOUS` `Target`: `ACTIVE_CHANGE`
`Target Detail`: `the active cycle` `User Style`: `tony`

## Assessed Inputs and Boundary

- Workflow: `STANDARD`, `FULL_DELIVERABLE`, project `BROWNFIELD`. This pass is
  the documentation rerun under recovery frame 1 (owner `SCOPING`, `ResumeAt`
  `SYNCHRONIZING`, `RerunThrough` `REVIEWING_FINAL`), entered by a `FORWARD`
  handoff from `REVIEWING_IMPLEMENTATION`: the user's rework that makes code's
  measurements of the PDF hints. Documenter does not own the frame. No
  outstanding obligations.
- Current ACs: `AC-001` to `AC-054` without `AC-019` and `AC-034`, which are
  retired (replaced by `AC-048` and `AC-051`). New since the earlier pass:
  `AC-043` to `AC-054`.
- Contract and owner evidence, by last commit and SHA-256 prefix, read at
  `a1d6cfe` with a clean tree:
  - scope
    `.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`01598d8`, `2d921029f902`);
  - design
    `.standards/docs/specs/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`5cb51ac`, `a69221d00c35`), decisions 1–16, **Checks and hints**, **Docs
    and docstrings**, **Risks and Follow-up**;
  - development plan
    `.standards/docs/development/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`de4efcd`, `215cd7c4e02f`; `COMPLETE`);
  - verification report
    `.standards/docs/verification/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`278264b`, `2dac1da950f8`; `COMPLETE`, `FULL`, E1–E60);
  - implementation review
    `.standards/docs/reviews/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada/implementation.md`
    (`a1d6cfe`, `938622aee9ab`; `COMPLETE`, no material findings; R18 lists the
    docs passages the rework made stale; later dependencies on Documenter:
    `AC-032`, `AC-035` to `AC-038`, `AC-053`, the README part of `AC-030`, the
    guides and FAQ parts of `AC-051` and `AC-052`);
  - final review from before the rework
    `.standards/docs/reviews/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada/final-deliverable.md`
    (`82dfd30`, `82523a6d2d88`), read as context only;
  - project context `.standards/CONTEXT.md` (`0573e11`, `09045f457b2d`).
- Behavior inspected in source at `a1d6cfe`: `extracting/prompts.py` (`_RULES`
  hints paragraph, page furniture and forms rules, `_page_text` hint headings,
  `_VERDICT`, `extract_page`'s closing line), `extracting/extraction.py`
  (`_kept_answer`, `_page_issues`, the page log line),
  `extracting/validators.py` (`_failure` details, `check_form_fields`, the
  `reading_order` differences), `extracting/text_layer.py`,
  `extracting/agents.py` and `extracting/llm.py` docstrings,
  `surveying/prompts.py` (the facts as hints, the verifier's heading),
  `surveying/validators.py` (hint details `measured`, `profile`, `source`),
  `surveying/survey.py` (issues), `review.py`, and the generated
  `extraction-checks.md` and `survey-checks.md`.
- Baseline and comparison: the earlier documentation commit `c0ed1e9` through
  `a1d6cfe` (`HEAD`). Since `c0ed1e9` the rework changed `src/`, `scripts/`,
  `tests/` and the generated reference pages; no hand-written docs page,
  `README.md` or `artifacts/next_cycle_inputs.md` changed. The cycle's code
  change `git diff 126f52f HEAD -- src scripts examples docs pyproject.toml`
  hashes `9de0a5151e9832a2`, as the implementation review recorded at `de4efcd`.
  Every change in this pass is uncommitted on top of `a1d6cfe`
  (`git diff -- . ':!.standards'` SHA-256 `0385501736e6b7e7`); nothing under
  `tests/`, `scripts/`, `examples/` or `pyproject.toml` changed.
- Editing boundary: the README, the docs site's hand-written pages, docstrings
  (no behavior), the generated reference pages through
  `scripts/generate_reference_docs.py` and Prettier only, and
  `artifacts/next_cycle_inputs.md`. No code behavior, test, fixture, example
  config or tooling changed.
- Environment: macOS arm64, Python 3.13.9 (`.venv`, editable install), Node
  23.10.0, the repo's locked uv, prek, Prettier and markdownlint.
- Style files: `styles/universal.md`, `styles/python.md` (docstrings), user
  style `.standards/user-styles/documenter/tony.md` (`797def3`, `e93537bf4a93`).
  `references/readme.md` was not needed: the README keeps its structure and
  needs no change.
- Project references loaded: `NONE` (`.standards/project-references/documenter/`
  does not exist).

## Documentation Work and Evidence

Saved content, by SHA-256 prefix after the last formatting pass. Each changed
page was read back as a diff after saving.

- `docs/src/content/docs/guides/page-extraction.md` `2924cb41135a`. Users who
  run page extraction and read its review list. **How a page is read**: step 2
  sends the writing direction, repeated lines with stored text and the survey's
  finding, and form fields with stored values as hints the image overrides; step
  3 sends back failed checks only, never hint differences; step 4 gives the
  verifier the checks still failing and the hint differences; reading order
  takes the survey's direction as a hint. **How a page is checked** rewritten:
  checks (consistency and the page's area) may send an answer back and a final
  failing answer is kept and listed while the run goes on; the five hints, what
  each compares, that the image decides, that a hint difference never sends an
  answer back or fails a page or run, when it is listed, and that the page
  file's `hints` keeps it; a page fails only when no usable answer comes back; a
  verifier correction is kept when it passes every check, whatever its hint
  differences. **Text compared with the PDF's stored text**: the text
  differences are hints, never sent back, listed unless a verifier passed the
  page or its correction was kept, quoted in the verifier's request. `AC-032`,
  `AC-043`, `AC-044`, `AC-045`, `AC-046`, `AC-047`, `AC-048`, `AC-049`,
  `AC-051`, `AC-052`, `AC-054`.
- `guides/verifiers.md` `15e434633047`: the survey verifier treats the facts as
  hints; the page verifier gets the hint differences, quoting stored lines, and
  the image decides; a correction is kept when it passes every check, whatever
  its hint differences (the old "text comparison doesn't count" line is gone);
  the review list table now has one row for checks in either step, the survey's
  two hints and the page's five hints; a difference left off the list stays in
  the output file's `hints`, and no hint difference sends anything back. The two
  estimate lines with a verifier now read $5.46 (survey maximum) and $0.46,
  $10.42 (extraction), as the CLI prints them with the changed prompts.
  `AC-005`, `AC-032`, `AC-037`, `AC-044`, `AC-046`, `AC-047`, `AC-048`.
- `guides/outputs.md` `abe7c5af14a0`: the survey's measurements are hints and
  never send an answer back; a new **Places where a page and its hints
  disagree** paragraph lists the five hints and when they are listed; the checks
  paragraph covers checks only; `hints` added to the page file and
  `pdf_survey.json` lists. `AC-011`, `AC-013`, `AC-020`, `AC-032`, `AC-048`,
  `AC-052`.
- `guides/models-and-providers.md` `93f065e43e20`: the survey's facts and
  repeated lines are hints; a page request carries the image and how far it was
  turned, and as hints the direction, the repeated lines with stored text and
  the survey's finding, and the form fields with stored values; the verifier's
  second request adds the checks still failing and the hint differences, quoting
  stored lines; no request asks a model to match a hint; the "goes back for a
  text check" sentence is gone; both failure sections say a hint difference is
  never sent back and never fails the step. `AC-043`, `AC-044`, `AC-045`,
  `AC-046`, `AC-049`, `AC-051`, `AC-052`, `AC-054`.
- `faq.md` `191ae4aacfc1`: the measurements are given as hints only and never
  make pydelity send an answer back, for the survey and page extraction alike;
  the stored text question says the repeated lines' text and form field values
  go as hints and each text difference goes on the review list; the "what is
  sent" answer lists the hints, form field values included, and the verifier's
  checks and hint differences. `AC-051`, `AC-052`.
- `guides/command-line.md` `426088b6e93d`: the verbose page line gives the
  number of items and review issues, as `extraction.py` logs it, not "checks".
  `AC-036` area (docs accuracy).
- `src/pydelity/review.py` `6485fe1930da` (docstrings only): `CheckFailure`'s
  class, `details` and `message` docstrings now cover hint differences too,
  since `hints[].differences[]` uses the same model: a survey hint's details
  (`{"measured": 90, "profile": 0}`), a page hint's `item_ref`, and a message
  starting with the hint's name. Regenerated: `reference/page-json.md`
  `a33732d6e378` and `reference/pdf-survey-json.md` `83d74bd07370`. `AC-033`,
  `AC-035` (page extraction's own examples still shown, and the failure still
  does not claim to name an item by its ref).
- `artifacts/next_cycle_inputs.md` `433b778a496a`: **User decisions that apply
  to later steps** replaces the rule that code may send an answer back with the
  hint rule (measurements are hints in every step, the model's reading decides,
  no message asks it to match a hint, a hint difference never causes a retry or
  failed run and is listed unless the verifier accepted the answer, consistency
  checks and hard limits may still send an answer back, a run stops only on an
  unusable answer or a provider error, each later step sorts its comparisons the
  same way); the verifier summary lists each step's checks and hints and the
  `hints` fields; the user's 2026-11-22 rework request and its reason are kept
  for reference; the verifier bullet names the hint differences; the page file
  notes add `hints` and say `column_order` is a hint; the brief's replaced
  design point, the text layer note, the risks (no hint retried, fewer artifact
  items, `hints` instead of `checks`, output folders without `hints` redone) and
  **Judging each page's stored text** match the rule. The remaining issues stay
  listed. `AC-038`, `AC-053`.
- No change needed, assessed:
  - `README.md` and `docs/src/content/docs/index.md`: they say only that
    pydelity checks answers and lists what a person should check, and describe
    the optional verifiers, all still accurate. `AC-030` README part, `AC-032`.
  - `start/first-survey.md`: "if it fails a check, sends it back ... up to two
    more times" is still accurate for checks. `guides/costs.md` (`check_retries`
    sends fewer answers back), `guides/configuration.md` (the `check_retries`
    rows), `guides/python.md`, `guides/reruns.md`: nothing about hints.
    `start/install.md`, `need-help.md`, `contributing/*`: unaffected.
  - The other generated reference pages, `extraction-checks.md` and
    `survey-checks.md` included: regenerated with no change from `HEAD`. They
    list checks and hints apart and say a hint never sends an answer back or
    stops a run (Developer's generator text, read for `AC-052`).
  - Docstrings the design names for `AC-051` (`extracting/prompts.py`,
    `text_layer.py`, `validators.py`, `agents.py`, `llm.py`,
    `surveying/validators.py`, `review.py`): read; they say what is sent, as
    hints, and that a hint difference never sends an answer back. A search finds
    no docstring saying pydelity sends none of the stored text or that a text
    difference goes back.
  - `AGENTS.md`, `CLAUDE.md`: STANDARDS guidance only.
- Every current AC, by ID:
  - Documented user-facing behavior, from the earlier pass and still accurate
    except where this pass changed the page: `AC-001`, `AC-002`, `AC-003`,
    `AC-004`, `AC-005`, `AC-006`, `AC-007`, `AC-008`, `AC-009`, `AC-010`,
    `AC-011`, `AC-012`, `AC-013`, `AC-014`, `AC-015`, `AC-016`, `AC-017`,
    `AC-018`, `AC-020`, `AC-021`. The rework did not change settings, the CLI,
    estimates, reuse, the ledger, the report's verifier texts, transport or
    `load()`, so the earlier evidence for these pages applies.
  - Documented in this pass: `AC-043`, `AC-044`, `AC-045`, `AC-046`, `AC-047`,
    `AC-048`, `AC-049`, `AC-054` (user-facing descriptions only; the behavior
    evidence is Tester's E1–E60 and the implementation review).
  - Documentation ACs, saved and checked: `AC-030` (README part, no change),
    `AC-032`, `AC-033`, `AC-035`, `AC-036`, `AC-037`, `AC-038`, `AC-051`,
    `AC-052`, `AC-053`.
  - No documentation impact: `AC-022`, `AC-023`, `AC-024`, `AC-025` restore
    expected behavior that no page described otherwise. `AC-026`, `AC-027`,
    `AC-028`, `AC-029`, `AC-031` and `AC-050` are tests, CI and release
    readiness, which the contributing pages already describe correctly. `AC-041`
    and `AC-042` reorder code.
  - Not documentation: `AC-039` and `AC-040`, the user's real runs after this
    phase.
  - Retired, history only: `AC-019`, `AC-034`.

## Checks and Applicability

All from the repository root on the saved content above, 2026-11-22.

- Reference pages: `.venv/bin/python scripts/generate_reference_docs.py`, then
  `just lint-markdown` (outside the sandbox, which blocks uv's cache in
  `~/.cache`). Before the `review.py` docstring edit, nothing under `reference/`
  differed from `HEAD`. After it, only `page-json.md` and `pdf-survey-json.md`
  differ, with exactly the docstring change. Running both again gives the same
  bytes, which is CI's staleness check.
- `just lint-markdown`: Prettier formatted the changed pages,
  `STANDARDS check passed.`, `markdownlint-cli2 ... Passed`, exit 0.
- `just docs-build` (in `docs/`, outside the sandbox): `29 page(s) built`, then
  `Checked local links and fragments in 29 HTML pages.`, exit 0. This covers the
  new in-page link to `#text-compared-with-the-pdfs-stored-text` and the links
  to `#how-a-page-is-checked` and `#when-page-extraction-fails`.
- Python, after the docstring edit: `.venv/bin/ruff check scripts src tests`
  "All checks passed!"; `.venv/bin/ruff format --check scripts src tests` "89
  files already formatted"; `.venv/bin/ty check scripts src tests` "All checks
  passed!"; `.venv/bin/interrogate scripts src tests` "RESULT: PASSED (minimum:
  100.0%, actual: 100.0%)", badge unchanged in git;
  `.venv/bin/pytest -q --numprocesses auto -p no:cacheprovider` 211 passed;
  `.venv/bin/pytest -q --doctest-modules src -p no:cacheprovider` 28 passed, 1
  skipped. A first `ruff check` failed (D205, D209) on a two-line class
  docstring; it was shortened to one line and passed.
- Python examples, rerun because the code under them changed: a scratch script
  (`run_examples.py` in the session scratchpad) starts `MockProviders` with
  `tests/fixtures/survey_answers/irs_form_1040a_1965_scan.json`, the canned page
  answers and a passing survey verdict, copies `irs_form_1040a_1965_scan.pdf` to
  a temporary folder as `document.pdf` and runs the README example
  (`arun(..., languages=["en"], pause=False)`, items and review printed; page 0
  has the six `checks`, the five `hints` with no differences, `verification`
  `None`) and the verifiers guide's `verify=True` example (both pages verified,
  no survey issue). Exit 0. The other Python and CLI examples use APIs the
  rework did not change (`git diff c0ed1e9 HEAD` of `reference/python-api.md`
  changes only `RunResult.pages`' summary wording), so the earlier pass's runs
  of them still apply.
- Wording: a search of `README.md` and `docs/src/content/docs` outside
  `reference/` for "text check", "goes back for", "leaving aside the text",
  "other than the text comparison", "may keep its reading", "costing retries",
  step numbers, AC or DEV IDs and "cycle" finds nothing, and no added line in
  the docs has a semicolon. `artifacts/next_cycle_inputs.md` keeps "sends ...
  back" only where it states the hint rule.
- Estimate lines, re-measured because the prompts' sizes changed: the CLI run
  with placeholder keys, base URLs on closed port 9 and input from `/dev/null`
  in a scratch folder holding `irs_form_1040a_1965_scan.pdf` as `document.pdf`,
  so each run stopped at the question with exit 3 and sent nothing:
  - no survey: `Survey cost estimate: about $0.24, at most $2.53 (up to 3 ...)`,
    and with `--verify`
    `Survey with its verifier cost estimate: about $0.47, at most $5.46 (up to 6 ...)`;
  - after `asurvey` against `MockProviders` with the stand-in survey answer:
    `Extraction cost estimate: about $0.23, at most $4.81 (2 pages, up to 6 ...)`,
    and with `advanced.extraction.verify: true` in a config file
    `Extraction with its verifier cost estimate: about $0.46, at most $10.42 (2 pages, up to 12 ...)`;
  - `aestimate` on `irs_form_w9.pdf` (the FAQ's 6-page form): about $0.36, at
    most $2.90.

  The figures without a verifier match `first-survey.md`, `costs.md` and the FAQ
  unchanged. The three verifier figures moved by a cent and were corrected in
  `verifiers.md`. A search finds no other copy of the old figures.

- Earlier evidence retained: the CLI examples (pause message, summaries, invalid
  settings) and the no-change dispositions for pages this pass did not touch,
  because the rework changed no setting, option, exit code or summary format.
  Superseded: the earlier record's statements that text differences go back to
  the model and stay in `checks`, its verifier estimate figures, and its check
  results at `31cbf8a`.
- Not run: Python 3.14 locally, the wheel smoke test and CI. No code behavior
  changed in this pass; CI's stale-reference and docs jobs cover these files
  once committed.

## Discrepancies, Dependencies, and Remaining Work

No `DOC-NNN` entry is open: nothing in the documentation contract is unmet.

Non-blocking observations, outside this record's ownership, carried from the
earlier pass because no AC or documented behavior depends on them:

- The generated CLI reference's exit code `0` reads "The run completed, with or
  without review issues" and leaves out a paused run. The command-line guide's
  exit code table covers the pause. Owner: Developer, if the user wants it
  changed.
- A run stopped at the question before page extraction lists `pages/` and
  `figures/` among the output folder's files even when neither exists yet.
  Owner: Developer, if the user wants it changed.

Dependencies after this gate, owned by others:

- Final Reviewer: reassesses this record and the changed pages
  (`FINAL_DELIVERABLE`), the last rerun state of recovery frame 1.
- Synchronizer: reconciles the deliverable when the frame resumes
  `SYNCHRONIZING`. The `review.py` docstring edit changes one file under `src/`
  after Tester's and the implementation review's assessed content
  (`git diff a1d6cfe -- src` is docstrings only).
- The user: `AC-039` and `AC-040`, the real runs on both providers.

## Resume and Conclusion

- Done: every docs passage the rework made stale (implementation review R18, and
  the others found by search) is corrected; every required documentation surface
  is assessed and updated or given a no-change reason; the checks above pass on
  the saved content.
- Next: final review in a separate session. On resume, recompare the hashes
  above with the working tree.
- Blocking question: `NONE`.
- Selected target `ACTIVE_CHANGE` and the full Documenter gate are complete.
  This is not cycle completion or sign-off. Handoff: `FORWARD` to
  `REVIEWING_FINAL`, kind `FINAL_DELIVERABLE`, with recovery frame 1 kept on the
  stack; Reviewer is its `RerunThrough` boundary and resumes `SYNCHRONIZING`
  after its gate passes.

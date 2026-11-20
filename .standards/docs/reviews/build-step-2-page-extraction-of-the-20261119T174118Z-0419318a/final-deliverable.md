<!-- STANDARDS
Artifact: REVIEW
Cycle: build-step-2-page-extraction-of-the-20261119T174118Z-0419318a
ReviewKind: FINAL_DELIVERABLE
-->

# Review Report

`Cycle`: `build-step-2-page-extraction-of-the-20261119T174118Z-0419318a`
`ReviewKind`: `FINAL_DELIVERABLE` `Status`: `BLOCKED` `User Style`: `NONE`

## Assessed Inputs and Scope

- Cycle mode `STANDARD`, completion policy `FULL_DELIVERABLE`, project mode
  `BROWNFIELD`. Entry: `RESUME` from `DOCUMENTING` after the user's async-first
  rework (its recovery frame popped); recovery inactive, no outstanding
  obligations, no blocker.
- Repository: branch `tz6/pipeline-step-2`, head `e9c7c94`, clean tree, pushed.
  Baseline `c7582e7` (`main`, release 0.1.1, the merge base). Active change:
  `git diff c7582e7..e9c7c94` outside `.standards/`, `.claude/`, `artifacts/`
  and the STANDARDS blocks in `AGENTS.md` and `CLAUDE.md`.
- Since the implementation review's head `4866b88`, only `.standards/`,
  `README.md`, `docs/astro.config.mjs` and hand-written pages under
  `docs/src/content/docs/` changed. Trees at `e9c7c94`: `src` `72daf0b4293b`,
  `scripts` `3a4c589069e8`, `examples` `d7cf92debfd7`, `.github`
  `5cc03340a06e`, `tests` `37d48a959897`, the identities the implementation
  review and the documentation record name.
- Records (git blob, 12 hex): scope `8f6dbf9b42a6` (current `AC-001` to
  `AC-064` except retired `AC-015`, `AC-023`, `AC-024`, `AC-062`); design
  `878aa2339bac` (decisions 1–22, technical acceptance criteria); context
  `be80a93c129c`; development plan `bf0636cfd9ef` (`COMPLETE`); verification
  report `37e0f1d4170f` (`REVERIFY`, `COMPLETE`, `FULL`); implementation review
  `c1e03da97691` (`COMPLETE`); documentation record `6ad33fb23b54`
  (`COMPLETE`).
- Documentation assessed: `docs/src/content/docs` tree `ebad8994fbd4`
  (hand-written guides, start pages, FAQ, contributing pages and the generated
  reference pages), `README.md` `b4451d9e668c`, `docs/astro.config.mjs`.
  `contributing/releases.md` blob `37144730caa5` (F-001).
- Environment: macOS arm64, repo `.venv` (Python 3.13.9, `uv.lock`).
- Project references loaded: `NONE` (`.standards/project-references/reviewer/`
  does not exist). User style: none selected.
- Inspection scope: every hand-written docs page and the README against the code
  at `e9c7c94`, the generated reference pages for currency and coverage, and
  the implementation review's conclusions against current content. Four
  read-only helper agents checked separate page sets in parallel (README, home,
  start pages, command line and FAQ; page extraction, outputs and the page,
  check and run references; configuration, models, costs and reruns with their
  references and the example configs; the Python guide and reference and the
  contributing pages). Each finding and limitation below was rechecked in this
  session against the source or by running it; helper claims not rechecked are
  not recorded. `artifacts/` and KGForEdGlobal were not reassessed.
- Session: this conversation holds none of the authoring history. The
  authoring sessions' models are not visible; this review ran on Claude Opus
  5.5.
- Severity bar: the one the user set for the implementation review (a finding
  must make delivered output wrong, lose money or fail a run, or break a
  function the acceptance review relies on), plus an acceptance condition left
  unmet. Confirmed inaccuracies below that bar are listed under limitations.

## Contract and Evidence Assessment

"Tester" means the verification report's tests and checks; "Reviewer" means
this review's inspection and diagnostics; "Documenter" means the documentation
record's checks.

| Obligation / criterion | Assessed evidence | Current disposition |
| --- | --- | --- |
| AC-001 to AC-006, AC-059 to AC-061 | Tester tests (unchanged source and tests); implementation review; Reviewer helper reran the CLI options, exit codes, config precedence and example configs | Supported |
| AC-007 to AC-014, AC-016 to AC-020, AC-056 | Tester tests and implementation review for code; model-dependent parts of AC-009 to AC-011 carried by AC-054 | Code supported; model-dependent parts: gap G-1 |
| AC-021, AC-022, AC-025, AC-026, AC-063, AC-064 | Tester tests; implementation review; Reviewer helper checked the guide's verifier and text-comparison rules against `extraction.py` and `validators.py` | Supported |
| AC-027 to AC-034, AC-057, AC-058 | Tester tests; implementation review; Reviewer diagnostic: 6 `arun(pause=False)` calls gathered, 5 rounds, all `completed`, identical page content (Checks) | Supported |
| AC-035 to AC-041 | Tester tests; implementation review (`implementation.md#F-002` resolved there) | Supported |
| AC-042, AC-043 | Tester; CI run `44823340233` on `e9c7c94` (staleness step passed); `CHANGELOG.md` links `c63d891` | Supported |
| AC-044 | Documenter edits to `faq.md`, `contributing/development.md`, `docs-site.md`, `releases.md`; Reviewer helper checked each listed item against the tooling | Six items supported; the patch-release item is wrong: F-001 |
| AC-045, AC-046, AC-047, AC-048 | 177 tests pass locally on `e9c7c94` (Reviewer); CI run `44823340233` on `e9c7c94`: both test jobs, `Wheel install` on Ubuntu, macOS and Windows (13 of 13 smoke checks), "Lint and test" `success`; TruffleHog run `44823340298` `success` | Supported |
| AC-049 | `pyproject.toml` description; classifiers Alpha, 3.13, 3.14; README and site description describe the survey and page extraction (Reviewer read) | Supported |
| AC-050 | `.release-please-manifest.json` `0.1.1`; release-please configuration unchanged since `c7582e7`; a `feat:` squash commit gives a minor bump under release-please 17.6.0's rules (Reviewer read upstream source) | Supported |
| AC-051 | Documenter's guides and example runs; Reviewer and helpers checked each task the AC lists (select pages, the pause, the model, page files, crops, verdicts, review list, report, spend control, reruns) against the code | Supported; limitations L-3 to L-9 |
| AC-052 | CI's lint job regenerates and formats the reference pages and fails on any change or untracked page: passed on `e9c7c94`; helpers regenerated the page file, run, check, CLI, configuration, cost and Python API pages and found them current and covering every field, setting, option, check and public function | Supported; limitations L-4, L-5 |
| AC-053 | Documenter ran every Python block (20 passed) and YAML block against the stand-in; helpers reran the README example, the CLI commands and quoted output, and the YAML blocks | Supported; limitation L-6 |
| AC-054 | No evidence | Gap G-1: the user's real runs and acceptance |

Technical acceptance criteria are assessed under the same IDs. The
implementation review's technical conclusions stand, because `src`, `tests`,
`scripts`, `examples` and `.github` are unchanged since it passed; its withdrawn
findings and limitations L-1 to L-10 still apply.

## Checks and Results

All from the repository root on `e9c7c94` (2026-11-20) unless stated.

- `node .standards/bin/check.mjs`: `STANDARDS check passed.`, exit 0, at entry
  and before handoff.
- `.venv/bin/python -m pytest --numprocesses auto -q`: 177 passed.
  `--doctest-modules src`: 27 passed, 1 skipped. `ruff check`,
  `ruff format --check`, `ty check` on `scripts src tests`: no problems.
- `gh run view` (outside the sandbox, whose proxy fails `gh`'s TLS check): CI
  `44823340233` on `e9c7c94`, every job `success`, including "Fail if the lint
  recipes changed or added any file" after `just lint`; Docs `44823340242`,
  "Build the docs" `success` (publish skipped, as on a branch); TruffleHog
  `44823340298` `success`.
- F-001 evidence (outside the sandbox, read-only GitHub API):
  `release-please-action` at the pinned commit `45996ed` (v5.0.0) locks
  `release-please` 17.6.0. At `v17.6.0`, `src/strategies/python.ts` lines
  31–44 set the Python strategy's changelog sections: `feat`, `fix`, `perf`,
  `deps`, `revert` and `docs` shown; `style`, `chore`, `refactor`, `test`,
  `build` and `ci` hidden. `src/strategies/base.ts` line 331 skips a release
  only when the changelog entry is empty; `src/versioning-strategies/default.ts`
  `determineReleaseType` returns a patch bump for any commit that is neither
  breaking nor `feat`. `release-please-config.json` sets `release-type:
  python` and no `changelog-sections`.
- Concurrent runs (the Python guide's "Run several PDFs at once"): scratch
  script `$TMPDIR/rvf/gather.py`, outside the repository, with the stand-in
  (`tests/fixtures/mock_providers.py`) and the scanned 1965 form's canned
  answers: 6 copies gathered with `arun(pause=False)`, 5 rounds: 30 of 30
  `completed` with 2 pages each; the items, containers, checks, text comparison
  and verification of every copy's page files identical. Limit: PyMuPDF's
  thread safety across runs is not proven by this (limitation L-2).
- Reused: the implementation review's checks and the verification report's
  evidence, because the code, tests and configuration they assessed are
  byte-identical at `e9c7c94` (same trees).
- Not run: a real model run (gap G-1); `just docs-build` locally (CI's Docs run
  on `e9c7c94` built the site and checked its links).

## Findings

### F-001 — The release guide says `docs:` commits make no release, but they make a patch release

`Severity`: `P2` `Status`: `OPEN` `Owner`: `DOCUMENTER` `FailureType`:
`DOCUMENTATION`

- **Reference:** `docs/src/content/docs/contributing/releases.md` (blob
  `37144730caa5`), the table at lines 32–37 (`docs:` under "Other types ...
  None") and lines 39–41 ("These follow release-please's default changelog
  sections ... types with a section of their own in the changelog make a
  release, and the rest don't"). `AC-044` (which commit types make a patch
  release).
- **Failure case:** a maintainer merges a pull request whose squash title is
  `docs: ...`, as this branch's documentation commits are titled, into `main`.
  The guide says no release follows. release-please, with `release-type:
  python`, uses the Python strategy's sections, in which `docs` and `deps` have
  shown sections, so the changelog entry is not empty and it opens a release
  pull request for a patch version (for example 0.2.1).
- **Impact:** `AC-044` asked for this statement to be corrected and it is still
  wrong for the type most often merged. The explanation also points readers to
  the wrong source (the default strategy's sections, which hide `docs`). A
  maintainer who trusts it gets an unexpected release pull request; merging it
  publishes a patch release to PyPI with no code change.
- **Evidence:** the upstream source lines under Checks; the documentation
  record notes that it read `master` of
  `conventional-changelog-conventionalcommits`, not the bundled version, and
  not the Python strategy. Dependabot's prefixes here are `ci(deps)` and
  `build(deps)` (`.github/dependabot.yml`), both hidden, so the table's
  `build(deps):` row is right.
- **Smallest correction:** list `docs:` (and `deps:`) with `fix:`, `perf:` and
  `revert:` as making a patch release, keep `chore:`, `test:`, `ci:`,
  `build(deps):` and `ci(deps):` as making none, and say the rule comes from the
  changelog sections of release-please's Python release type, which this repo
  doesn't change.

**No other material findings.**

## Questions, Limitations, and Later Dependencies

Gap that blocks this gate:

- G-1, `AC-054` (with the model-dependent parts of `AC-009`, `AC-010` and
  `AC-011`, box accuracy, reading order and upright reading on real pages): no
  current evidence. The scope requires the user to run the survey and page
  extraction with real Anthropic and OpenAI models on PDFs of their choice,
  including at least one two-column right-to-left document, one Chinese or
  Japanese document, one tax or fillable form, one slide deck or image-heavy
  PDF, and CAPS, review the page files and the HTML report, and accept them,
  with every issue they raise resolved. The real runs in the development plan
  (DEV-011: the rotated W-9 instructions on Anthropic and Arabic Publication 1
  page 1 on OpenAI, 2026-11-19) were Developer self-checks on code before the
  later fixes, not the named set or the user's acceptance. Owner: the user.
  Consequence: this gate cannot pass until the user reports the outcome; an
  issue they raise goes to its owner first. Next check: on re-review, record
  the user's report (which PDFs, which providers, accepted or the issues found)
  and, if the user shares the output folders, inspect their page files and
  reports. If still missing then, `Active Work.BlockedOn` holds the request.

Earlier later dependencies, resolved with current evidence:

- `AC-044`, `AC-051`, `AC-053` and the README part of `AC-049`: Documenter's
  guides, README and wording fixes, assessed above; all supported except
  F-001.

Limitations and observations that do not block this gate, with why (each
rechecked in this session; worth fixing if a page is edited anyway):

- L-1: the implementation review's limitations L-1 to L-10 and its withdrawn
  findings still apply; no code changed since.
- L-2: two runs gathered in one process each have their own PyMuPDF worker
  thread (`extraction.py` line 840), and the report and probe use
  `asyncio.to_thread`, so PyMuPDF can run on two threads at once, which
  `rendering.py`'s docstring calls unsafe. The 0.1.1 Python guide already said
  runs on different folders can go at the same time, the test suite gathers two
  surveys, and 30 gathered page-extraction runs gave identical, correct
  results. Not established as a failure.
- L-3: "pydelity doesn't send the text stored in the PDF"
  (`guides/page-extraction.md` lines 171–174, `guides/models-and-providers.md`
  line 70; the `prompts.py` and `text_layer.py` docstrings) is not quite true:
  each page request lists the page's repeated lines with their stored text and
  what the survey found each one to be (`prompts.py` lines 269–282), not only
  page furniture as line 170 says, and `text_dropped` retry messages quote
  stored lines (`validators.py` lines 1350–1356). Not material: the survey
  already sends the whole PDF to the same provider, and the guide's text
  comparison section says differences go back to the model. The FAQ's list of
  what page extraction sends (`faq.md` lines 94–96) also leaves out the form
  fields' values that the models guide lists.
- L-4: `reference/page-json.md` shows survey examples for `checks[].failures[]`
  and `issues[].details` (`{"proposed": 9, "page_count": 6}`,
  `{"measured": 90, "profile": 0}`, from the shared docstrings in `review.py`),
  and "a failure about one item names it in `details`" means the answer's
  `item_ref` (such as `t1`), which no page-file field holds; `issues[].item_id`
  is the item ID. Not material: the fields' types are right and the review list
  names items by ID.
- L-5: `reference/run-json.md` says `steps[].pages` is `None` for a step that
  reads the whole PDF, but a skipped extraction step after a pause also has
  `pages: null` (`runner.py` lines 1119–1124). Its `status` is `skipped`.
- L-6: `guides/command-line.md`'s `2> pydelity.log` example (unchanged since
  0.1.1) sends the spending question to the log file too (`cli.py` line 77,
  `err=True`), so in a terminal the command waits with nothing shown until the
  user answers.
- L-7: wording that is looser than the code: "a second model reviews" (README
  line 13, `index.md`, `page-extraction.md` line 11; the verifier is a second
  request to the same model, as the same page says at lines 126 and 177);
  "Every function takes the PDF" (`python.md` line 9; `load` takes the folder);
  `RunResult.pages` "the page files in `pages/`" (`python.md` line 91; `arun`
  returns the selected pages, `load` every page file); "Every error pydelity
  raises on purpose is a `PydelityError`" (the sync functions' `RuntimeError`
  inside a running loop is documented separately at line 51); "If you say no,
  the run stops with nothing more spent" (`costs.md` line 108; requests already
  in flight may be billed, as the same page says at lines 144–146); `faq.md`
  line 104 names `expiry_hours` without its `advanced.uploads.` prefix (the
  linked guide and the error give it).
- L-8: `guides/reruns.md` line 23 (unchanged since 0.1.1) lists the PDF's file
  name among the survey's inputs; the survey fingerprint holds the PDF's hash,
  not its name, so with `output_dir` set a renamed PDF reuses its survey.
  Harmless: it costs less than the guide suggests.
- L-9: `guides/reruns.md` lines 133–135 describe a damaged last line in
  `cost.jsonl`; a damaged earlier line stops every run on that folder with an
  `OutputError` naming the line (`costs/ledger.py` lines 150–153), which the
  guide does not mention. It needs a hand edit.

No blocking user question at this point (see G-1).

## Progress and Conclusion

- Completed: inputs and identities; source, tests and configuration unchanged
  since the implementation review; local suite and CI on the head; every
  hand-written docs page, the README and the generated reference pages against
  the code; release configuration; concurrent-run diagnostic.
- Not passing (2026-11-20, on `e9c7c94`): F-001 is open for Documenter, and gap
  G-1 (`AC-054`) needs the user's real runs and acceptance.
- Next: Documenter corrects F-001 (`DOCUMENTATION` failure, recovery frame with
  `ResumeAt: REVIEWING_FINAL`). On re-review, recheck `releases.md` against the
  release-please 17.6.0 rules above and any other page Documenter changed,
  rerun `check`, the suite or CI on the new head as needed, and record the
  user's `AC-054` report; if it is still missing, persist it in
  `Active Work.BlockedOn` and ask.

Plain-language summary: the work can't move to the last step yet, for two
reasons. First, one sentence in the release guide is wrong: it says a commit
titled `docs: ...` makes no new release, but this repo's release tool does make
a small release for it. Someone trusting the guide would get a release pull
request they didn't expect. Documenter fixes that one page. Second, the scope
asks you to try page extraction on real documents with real Anthropic and
OpenAI models and accept the results, and that hasn't happened yet: the right-
to-left, Chinese or Japanese, form, slide-deck and CAPS PDFs. Only you can do
that, since it needs your keys and your judgment. Everything else checked out:
the code and tests are unchanged since the last review and all pass, CI passes,
the reference pages are current, and the guides match what pydelity does,
apart from small wording points listed in the report that don't need a fix.

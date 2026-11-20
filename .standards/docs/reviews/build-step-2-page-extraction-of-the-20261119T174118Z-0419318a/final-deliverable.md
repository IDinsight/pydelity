<!-- STANDARDS
Artifact: REVIEW
Cycle: build-step-2-page-extraction-of-the-20261119T174118Z-0419318a
ReviewKind: FINAL_DELIVERABLE
-->

# Review Report

`Cycle`: `build-step-2-page-extraction-of-the-20261119T174118Z-0419318a`
`ReviewKind`: `FINAL_DELIVERABLE` `Status`: `COMPLETE` `User Style`: `NONE`

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
- Re-review (2026-11-20, after recovery frame 1 closed with a `RESUME` from
  `DOCUMENTING`): head `2f295eb`, clean tree, pushed. Since `02186fb` (this
  report's first commit) only `contributing/releases.md` (blob `37144730caa5`
  to `dd569f254cb0`), the documentation record (blob `d6adbcefe570`,
  `.standards/docs/documentation/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a.md#DOC-001`)
  and `STATE.md` changed; `src` `72daf0b4293b` and every other docs page
  unchanged, so the assessments above still apply to them.
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
| AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-059, AC-060, AC-061 | Tester tests (unchanged source and tests); implementation review; Reviewer helper reran the CLI options, exit codes, config precedence and example configs | Supported |
| AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-016, AC-017, AC-018, AC-019, AC-020, AC-056 | Tester tests and implementation review for code; model-dependent parts of AC-009 to AC-011 carried by AC-054 | Supported; model-dependent parts settled by the user's real runs (G-1 closed) |
| AC-021, AC-022, AC-025, AC-026, AC-063, AC-064 | Tester tests; implementation review; Reviewer helper checked the guide's verifier and text-comparison rules against `extraction.py` and `validators.py` | Supported |
| AC-027, AC-028, AC-029, AC-030, AC-031, AC-032, AC-033, AC-034, AC-057, AC-058 | Tester tests; implementation review; Reviewer diagnostic: 6 `arun(pause=False)` calls gathered, 5 rounds, all `completed`, identical page content (Checks) | Supported |
| AC-035, AC-036, AC-037, AC-038, AC-039, AC-040, AC-041 | Tester tests; implementation review (`implementation.md#F-002` resolved there) | Supported |
| AC-042, AC-043 | Tester; CI run `44823340233` on `e9c7c94` (staleness step passed); `CHANGELOG.md` links `c63d891` | Supported |
| AC-044 | Documenter edits to `faq.md`, `contributing/development.md`, `docs-site.md`, `releases.md`; Reviewer helper checked each listed item against the tooling | Supported (F-001 resolved on re-review: `releases.md` `dd569f254cb0`) |
| AC-045, AC-046, AC-047, AC-048 | 177 tests pass locally on `e9c7c94` (Reviewer); CI run `44823340233` on `e9c7c94`: both test jobs, `Wheel install` on Ubuntu, macOS and Windows (13 of 13 smoke checks), "Lint and test" `success`; TruffleHog run `44823340298` `success` | Supported |
| AC-049 | `pyproject.toml` description; classifiers Alpha, 3.13, 3.14; README and site description describe the survey and page extraction (Reviewer read) | Supported |
| AC-050 | `.release-please-manifest.json` `0.1.1`; release-please configuration unchanged since `c7582e7`; a `feat:` squash commit gives a minor bump under release-please 17.6.0's rules (Reviewer read upstream source) | Supported |
| AC-051 | Documenter's guides and example runs; Reviewer and helpers checked each task the AC lists (select pages, the pause, the model, page files, crops, verdicts, review list, report, spend control, reruns) against the code | Supported; limitations L-3 to L-9 |
| AC-052 | CI's lint job regenerates and formats the reference pages and fails on any change or untracked page: passed on `e9c7c94`; helpers regenerated the page file, run, check, CLI, configuration, cost and Python API pages and found them current and covering every field, setting, option, check and public function | Supported; limitations L-4, L-5 |
| AC-053 | Documenter ran every Python block (20 passed) and YAML block against the stand-in; helpers reran the README example, the CLI commands and quoted output, and the YAML blocks | Supported; limitation L-6 |
| AC-054 | The user's real runs on both providers (`pydelity-output/real/anthropic/` and `openai/`, 14 runs, 44 pages, $17.47); Reviewer's inspection under G-1; the user's acceptance, 2026-11-20 | Supported (G-1 closed) |

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

`Severity`: `P2` `Status`: `RESOLVED` `Owner`: `DOCUMENTER` `FailureType`:
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
- **Reassessment (resolved, 2026-11-20, on `2f295eb`):** `releases.md`
  (`dd569f254cb0`, lines 30–46) now puts `fix:`, `perf:`, `revert:`, `docs:`
  and `deps:` under patch, `chore:`, `test:`, `ci:`, `build(deps):` and
  `ci(deps):` under none, names the Python release type's changelog sections as
  the source, and says a `docs:` pull request opens a patch release pull request
  that publishes nothing until merged. Each matches the release-please 17.6.0
  source lines under Checks (Python strategy sections; empty-changelog skip;
  patch for any non-breaking, non-`feat` commit); `release.yml` runs only on a
  published GitHub release, which release-please creates when its release pull
  request is merged. The original failure case (a `docs:` merge) is
  now described correctly. Boundaries: a search of `README.md` and the
  hand-written pages finds no other statement about which commits make a
  release; the feat-to-minor and breaking-below-1.0.0 rows are unchanged and
  still right.

**No other material findings.**

## Questions, Limitations, and Later Dependencies

Gap at the first review, now closed:

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
  Re-review (2026-11-20): the user answered "not done yet" and asked for the
  commands; Reviewer gave CLI commands for the scope's PDF kinds from
  `tests/fixtures/pdfs/` (Arabic and Chinese Publication 1, the Japanese
  gazette, W-9 page 1, the scanned 1965 form, slides 1–6, CAPS) on each
  provider, into `pydelity-output/real/<provider>/<pdf>/`. Offline estimates
  (`pydelity.estimate`, nothing sent): about $8 on the Anthropic default and
  about $18 on `openai:gpt-6.2-astra` in all. `BlockedOn` stays set.
  Anthropic runs (the user's, 2026-11-20, default model, `-np`, folders
  `pydelity-output/real/anthropic/<pdf>/`, pydelity at `2f295eb`), inspected
  by Reviewer at the user's request as supporting evidence, not acceptance:
  - All 7 runs `completed`, $6.36 in all (survey $0.98, extraction $5.38); 22
    pages extracted, 0 failures. Review list: 3 issues, all on the Japanese
    page; none elsewhere.
  - Reading order (`AC-010`): Arabic page 1 reads the right column, then the
    left; page 2 its three columns from the right. Chinese reads left to right,
    two and three columns. The Japanese page is `ttb`, `column_order:
    right_to_left`, its columns read from x 390 down to 132.
  - Rotation (`AC-011`): all 8 CAPS pages applied 90 degrees; text compared
    with no failure; every table box contains all of its table's words (414 to
    608 per page) and tracks each table's width.
  - Boxes (`AC-009`): Reviewer's scratch check of every text-layer word's
    center against the item boxes (3 pt margin, displayed coordinates): 0
    outside on all 6 slides, all 8 CAPS pages and Arabic page 2; 2 of 581 on
    Arabic page 1, 6 of 933 on W-9 (field labels), 16 of 117 on Chinese page 1
    (the footer box sits about 7 pt below its line), 5 of 276 on Chinese page 2
    and 25 of 222 on the Japanese page. The Chinese page 2 misses are two
    paragraphs that continue at the top of the next column (items
    `p0001-014`, `p0001-027`): each item's text includes the continuation, its
    box covers only the first column's part. The Japanese misses are the
    right-margin vertical line (`p0000-005`), whose box sits about 9 pt left
    of its two text lines. The prompt (`extracting/prompts.py`) has no rule for
    text that continues into the next column.
  - Forms (`AC-016`): W-9 page 1 has 25 field items, the form's 8 checkboxes and
    15 text fields by `fillable_name` plus 2 printed fields, `form_fields`
    passed; the 1965 scan has 38 field items, no text layer. Both forms are
    blank, so no filled or written value was exercised.
  - Text comparison (`AC-063`): Arabic (both pages) and Japanese keep
    `text_dropped`/`text_added` failures from stored text with broken letter
    forms and private-use characters; the verifier passed, so none is listed,
    as designed.
  - Japanese issues: 2 `no_matching_label` because the one-page survey made no
    label for page furniture (7 text items and the masthead figure get
    `other`); 1 for a field item made from a zero-size `Signature1` widget at
    the page's corner (`[0, 841, 1, 842]`).
  - Slides: one figure per slide, the logo, as an artifact; the slides' other
    images are the full-slide background and the footer band. No slide in
    1–6 is one picture, so `AC-017` was not exercised. Figure crops: 9, each
    named after its item.
  - User decision (2026-11-20): after Reviewer explained that the box misses
    are saved `bbox` values (the text is complete and correct; the report draws
    the page file's boxes as saved), the user accepted them for 0.2.0: "accept
    them". No issue raised from the Anthropic runs.
  OpenAI runs (the user's, 2026-11-20, `openai:gpt-6.2-astra` for both steps,
  `-np -y`, folders `pydelity-output/real/openai/<pdf>/`, same PDFs, pages
  and code), inspected the same way:
  - All 7 runs `completed`, $11.11 in all (survey $2.09, extraction $9.02); 22
    pages extracted, 0 failures. Review list: 1 issue, the Japanese page's
    zero-size `Signature1` field again (`no_matching_label`).
  - Reading order (`AC-010`): Arabic page 1 right column then left (item
    centers x 424–545, then 174–276); page 2 three columns from the right;
    Chinese page 2 three columns from the left; the Japanese page
    `column_order: right_to_left`, columns from x 435 down to 138.
  - Rotation (`AC-011`): all 8 CAPS pages applied 90 degrees; text compared
    with no failure; every word inside a box.
  - Boxes (`AC-009`): 0 words outside every box on all 6 slides, 8 CAPS pages
    and both Arabic and Chinese pages; 6 of 222 on the Japanese page (single
    marks such as `〇` and `。`). W-9: 184 of 933, in 35 lines: the field items'
    boxes cover only the input area or checkbox, as the fillable-field hints'
    boxes do, while each field's printed label is saved in its `prompt` (for
    example item `p0000-009`, box `[59, 118, 576, 132]`, label line at y 97).
    The Anthropic run's field boxes took in the label. The prompt's box rule
    ("close around the visible content"; "Field boxes given with the page use
    the same grid") does not say whether a field's box includes its label.
    Every check passed on the W-9 page, text comparison included.
  - Structure: Chinese page 1 puts the ten rights in one list item with 10
    entries (Anthropic: 20 heading and body items); OpenAI marks more
    containers (W-9 12, CAPS 2–3 a page). Both readings fit the item rules.
  - Text comparison (`AC-063`): Arabic and Japanese keep stored-text
    differences, not listed since the page was passed or corrected; the
    verifier's correction was kept on Arabic page 2 and the 1965 scan's page
    2.
  - User decision (2026-11-20): after Reviewer's summary of these results,
    the W-9 field boxes included, the user accepted them: "Accept". No issue
    raised.
  - Resolution (2026-11-20): G-1 is closed. The user ran the survey and page
    extraction with real Anthropic and OpenAI models on a two-column
    right-to-left PDF, Chinese and Japanese PDFs, two tax forms (one fillable),
    a slide deck and CAPS, and accepted the results with no issue raised. The
    page files and reports were reviewed through Reviewer's inspection above at
    the user's request; the acceptance decision is the user's own. This also
    settles the model-dependent parts of `AC-009`, `AC-010` and `AC-011`.
    Not exercised by these runs, with mocked-test evidence only: a filled or
    handwritten form value (`AC-016`) and a page that is one picture
    (`AC-017`). `AC-054` names neither, so this does not keep the gap open.

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

No blocking user question remains: the `AC-054` question was answered and
`Active Work.BlockedOn` is cleared (2026-11-20).

## Progress and Conclusion

- Completed: inputs and identities; source, tests and configuration unchanged
  since the implementation review; local suite and CI on `e9c7c94`; every
  hand-written docs page, the README and the generated reference pages against
  the code; release configuration; concurrent-run diagnostic. Re-review on
  `2f295eb`: F-001's correction rechecked and resolved; no other file the
  assessment relies on changed; CI, Docs and TruffleHog runs on `2f295eb` all
  `success`. G-1 closed by the user's real runs on both providers and their
  acceptance.
- Freshness, rechecked immediately before this conclusion (2026-11-20): head
  `2f295eb`; the only uncommitted changes are this report and `STATE.md`;
  `src` `72daf0b4293b`, `docs/src/content/docs` `d15cc68ffdad`, `README.md`
  `b4451d9e668c`, `tests` `37d48a959897`, `scripts` `3a4c589069e8`, `.github`
  `5cc03340a06e`; scope `8f6dbf9b42a6`, design `878aa2339bac`, context
  `be80a93c129c`, development plan `bf0636cfd9ef`, verification report
  `37e0f1d4170f`, documentation record `d6adbcefe570`: all as assessed.
- **Passing (2026-11-20, on `2f295eb`).** F-001 is resolved; no finding is
  open; every current AC and relevant technical criterion has a supported
  disposition with current evidence; no later dependency, material gap,
  blocking question or outstanding obligation remains; `check` passes. Next:
  `SYNCHRONIZING` (`FULL_DELIVERABLE`). Passing this gate is not cycle
  completion or sign-off.

Earlier conclusions (2026-11-20): on `e9c7c94`, not passing with F-001 open for
Documenter and G-1 open; on `2f295eb` before the real runs, not passing with
G-1 open and its question in `Active Work.BlockedOn`.

Plain-language summary: the final review passes, and the work can move on to
synchronization. The release guide is fixed. Your real runs on both providers
showed page extraction reading right-to-left, Chinese, vertical Japanese,
sideways and form pages correctly, with complete text and nearly all boxes
tight around their content. You accepted the few boxes that sit a little off
or, on OpenAI's W-9, leave out a field's printed label. What these runs did not
try: a filled-in form and a slide that is one picture; mocked tests cover both.
Synchronization and your sign-off are still to come.

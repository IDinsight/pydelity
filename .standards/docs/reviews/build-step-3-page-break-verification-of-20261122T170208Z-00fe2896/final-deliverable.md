<!-- STANDARDS
Artifact: REVIEW
Cycle: build-step-3-page-break-verification-of-20261122T170208Z-00fe2896
ReviewKind: FINAL_DELIVERABLE
-->

# Review Report

`Cycle`: `build-step-3-page-break-verification-of-20261122T170208Z-00fe2896`
`ReviewKind`: `FINAL_DELIVERABLE` `Status`: `IN_PROGRESS` `User Style`: `tony`

## Assessed Inputs and Scope

- Cycle mode `STANDARD`, completion policy `FULL_DELIVERABLE`, project mode
  `BROWNFIELD`. The current acceptance set is `AC-001` to `AC-051`. The scope
  retires none, and the design's technical acceptance criteria use the same IDs.
- Records, by the first 16 hex digits of their SHA-256. Each matches what the
  documentation record and the implementation review assessed:
  - scope `c0f8b54a9851b32c`
  - design `e9006fbf2a78ee99`
  - plan `01434a6d99513f03` (`COMPLETE`)
  - context `0e940ffe605aecff`
  - verification report `41861e7f5baec0a1` (`COMPLETE`, `FULL`, `NONE`)
  - implementation review `47accb225ac7dc58` (`COMPLETE`, no findings)
  - documentation record `84022bee20f0fc06` (`COMPLETE`)
- Change: `main...HEAD` on `tz6/pipeline-step-3`, merge base `7dc2cba` (0.2.0),
  HEAD `acee8e2`, plus the documentation changes staged on top of HEAD.
  - `acee8e2` differs from `8201e2e`, the commit the implementation review
    assessed, only in that review's record and `STATE.md`.
  - `src/`, `scripts/`, `examples/`, `pyproject.toml`, the generated reference
    pages, `.github/` and the release-please files are the same as at `68b675c`,
    where Tester built the wheel and regenerated the pages. No test changed
    after `8201e2e`.
  - The staged documentation is 18 Markdown files and `docs/astro.config.mjs`.
    Each matches the hash in the documentation record: the new
    `guides/page-breaks.md` `9eb39f2f3303afdd`, nine changed guides, three start
    and overview pages, the contributing page, `README.md` `54eb0adac395db69`
    and `artifacts/next_cycle_inputs.md` `f9f1cb0b9c34460d`.
  - The branch is pushed to `origin` at `acee8e2`. It has no pull request, and
    the staged documentation is not pushed.
- Resumed 2026-11-28: the user committed the staged documentation and records as
  `1a0cae1` (`docs: document page-break verification`), pushed it and opened
  draft pull request 16 (`tz6/pipeline-step-3` into `main`), head `1a0cae1`.
  - `1a0cae1` holds the documentation files at the hashes above (checked for
    `page-breaks.md`, `python.md`, `faq.md`, `README.md`, `next_cycle_inputs.md`
    and `astro.config.mjs`), plus this report and `STATE.md`. It changes nothing
    under `src/`, `scripts/`, `tests/`, `examples/`, `pyproject.toml` or the
    reference pages. So every conclusion above still applies.
- Source read to check the docs: `pipeline/runner.py` (`_page_breaks`,
  `_current_page_files`, `_steps`, `_log_pause`, `_review`, `_page_ranges`,
  estimate titles), `verifying/schemas.py` in full, `verifying/prompts.py`
  rules, `_reusable_break` and the log labels in `verifying/verification.py`,
  `PageBreaksConfig` in `config/schemas.py`, `averify_breaks` in `api.py`,
  `PageBreakError`, and the request label in `providers/ledger_model.py`.
- Docs read: `guides/page-breaks.md` in full, and the whole staged diff of every
  other changed file.
- Project references: `NONE` (`.standards/project-references/` does not exist).
- Session: this conversation holds no authoring history for any record or file
  under review. The client gives no metadata on the models that wrote them.
- Real model behavior is the user's to accept under `AC-050` and `AC-051`. C12
  reads the user's Anthropic runs as supporting evidence only.

## Contract and Evidence Assessment

Formal evidence is Tester's (the verification report). Reviewer diagnostics are
under **Checks and Results**. Documentation evidence is Documenter's record plus
this review's reading and checks. The implementation evidence for `AC-001` to
`AC-041` is reused: the code, tests and records it rests on are unchanged since
the implementation review, and the suite still passes (C1).

| Obligation       | Assessed evidence                                                                                                                                                                                                                                                                                                                                 | Current disposition                                            |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| AC-001 to AC-010 | Verification report and implementation review, unchanged inputs. Docs: `page-breaks.md`, `command-line.md`, `python.md`, `configuration.md`, `first-survey.md`. C4 shows the pause after extraction, the next run judging the break, and a narrowed run warning and completing. The eight `advanced.page_breaks.*` rows match `PageBreaksConfig`. | Supported                                                      |
| AC-011 to AC-022 | As above. Docs: `page-breaks.md` "What you get" and "How a break is judged", `outputs.md` "Verdict files". Field names, join and text-join values, `judgment` and the file name match `verifying/schemas.py` and the prompt rules.                                                                                                                | Supported. See limitation L1 on `continue_entry`'s wording.    |
| AC-023 to AC-031 | As above. Docs: `page-breaks.md` "How a verdict is checked", `verifiers.md`, `outputs.md` review list, `models-and-providers.md`. The review-list order and the `pages N and N+1` message match `_review` and `_issue_place`.                                                                                                                     | Supported                                                      |
| AC-032 to AC-039 | As above. Docs: `costs.md`, `reruns.md`, `verifiers.md`, `command-line.md`. The reuse inputs in `reruns.md` match `BreakInputs`. C4 shows the estimate line, the verbose break line, both summary lines, and `overwrite` with `pages` judging no break, each as the docs quote them.                                                              | Supported                                                      |
| AC-040           | Tester's scenario allocation, read by the implementation review. C1: 248 passed.                                                                                                                                                                                                                                                                  | Supported                                                      |
| AC-041           | CI workflows unchanged from `main`. Tester read the ruleset. Python 3.14 run by Tester on unchanged code.                                                                                                                                                                                                                                         | Supported                                                      |
| AC-042           | CI on pull request 16, head `1a0cae1`: `Wheel install` passes on `macos-latest`, `ubuntu-latest` and `windows-latest` (C10). Each installs the built wheel and runs all three steps through the CLI and the Python API against the stand-in.                                                                                                      | Supported (G-1 closed)                                         |
| AC-043           | C5: wheel and sdist rebuilt with the new README as the long description, `twine check --strict` passes. Tester's clean-install smoke run still applies, because only the README changed.                                                                                                                                                          | Supported                                                      |
| AC-044           | `pyproject.toml` description and classifiers (Tester). README now names the three steps and an optional verifier for each.                                                                                                                                                                                                                        | Supported                                                      |
| AC-045           | Release config and the `0.2.0` manifest unchanged from `main`, `version = "0.2.0"` in `pyproject.toml`. The scope limits in-cycle evidence to release readiness.                                                                                                                                                                                  | Supported for release readiness. The release PR follows merge. |
| AC-046           | `page-breaks.md` and the guide changes cover running the step, the every-page rule and narrowed `pages`, verdict files, verifier outcomes, the review list, the report, model, instructions, verifier, spend, resume and rerun. `python.md` lists async functions first. C2 and C3.                                                               | Supported                                                      |
| AC-047           | Reference pages unchanged since Tester's byte-identical regeneration at `68b675c`, and so are `src/` and `scripts/`. Documenter regenerated them again with no change.                                                                                                                                                                            | Supported                                                      |
| AC-048           | C4 for every quoted CLI line. Documenter's runs of the Python examples. The README quick start reads as the CLI now behaves: three runs, `--pages`, `--no-pause`, `--verify`, `result.breaks`.                                                                                                                                                    | Supported                                                      |
| AC-049           | `next_cycle_inputs.md` "Pushed to later steps": the completed step 3 entry is gone and four pushed entries are added. The "each later step" entries stay, and still apply.                                                                                                                                                                        | Supported. See L4 for a stale entry outside this AC.           |
| AC-050, AC-051   | Ten real Anthropic runs, verifier off and on, over all five required kinds of PDF (C12): all complete, every verdict read against its pages, issues R-1 to R-4 raised for the user. No OpenAI run, and no user acceptance yet.                                                                                                                    | Gap G-2                                                        |

The implementation review's later dependencies are resolved as follows: AC-044,
AC-046, AC-047, AC-048 and AC-049 by the documentation above. AC-042, AC-050 and
AC-051 remain open as G-1 and G-2.

## Checks and Results

All commands ran from the repository root on 2026-11-28, macOS arm64, Python
3.13.9 in `.venv`, on HEAD `acee8e2` with the staged documentation.

- **C1.**
  `.venv/bin/python -m pytest -q --numprocesses auto -p no:cacheprovider`: 248
  passed, exit 0, in 10.3 s. Same count as Tester and the implementation review.
- **C2.** `pnpm run build` in `docs/`: 32 pages built. `pnpm run check-links`:
  "Checked local links and fragments in 32 HTML pages", exit 0. This checks the
  new guide's anchors and every link the changed pages add.
- **C3.** Prettier 3.10.1 (the pinned hook binary) `--check` on the 18 staged
  Markdown files: all pass. `markdownlint-cli2` from the hook env on the repo:
  243 files, 0 issues.
- **C4.** A scratch script started `tests/fixtures/mock_providers.py` with the
  fixture survey, page and break answers and ran `.venv/bin/pydelity` on
  `irs_form_1040a_1965_scan.pdf` (2 pages) with no real API key:
  - Run 1 paused after the survey. Run 2 extracted both pages and paused with
    the exact message `page-breaks.md` and `first-survey.md` quote, exit 0.
  - Run 3 (`-v`) printed the estimate line `costs.md` quotes, the verbose break
    line in the form `command-line.md` gives, and the summary line
    `command-line.md` quotes. `page_breaks/0000-0001.json` was written.
  - Run 4 reused every step, with the summary line `reruns.md` quotes.
  - A new folder with `--pages 1 -np` printed the exact `missing_page_files`
    warning `page-breaks.md` quotes, recorded the step `skipped`, completed and
    exited 0.
  - `--overwrite -np --pages 1` on the full folder judged no break, as
    `reruns.md` says.
  - The stand-in got 2 uploads and 8 model requests and nothing else.
- **C5.** `UV_CACHE_DIR=$TMPDIR/uvcache uv build --out-dir <scratch>`, fetching
  setuptools from PyPI, then `.venv/bin/python -m twine check --strict` (twine
  7.0.0): `pydelity-0.2.0-py3-none-any.whl` and `pydelity-0.2.0.tar.gz` PASSED.
  This covers the changed README's rendering as the package's long description.
  The tree stayed clean.
- **C6.** `gh pr list --head tz6/pipeline-step-3 --state all`: none.
  `gh api .../branches/tz6/pipeline-step-3`: `acee8e2`. Check runs for
  `acee8e2`: none, and no workflow run on the branch. `ci.yml` runs only on pull
  requests to `main` and pushes to `main`. These `gh` calls ran outside the
  sandbox, because `gh`'s TLS check fails inside it.
- **C7.** An offline `pydelity.aestimate` over each folder in
  `pydelity-output/real-hints/{anthropic,openai}/{default,verify}/`, to help the
  user plan G-2. It writes nothing. Surveys and page files there are reused,
  except slides (10 more pages) and W-9 (5 more pages), which those runs
  extracted only in part. The Japanese gazette has one page and so no break.
  Totals with the earlier five PDFs: Anthropic about $6.05 off and $11.85 with
  the verifier, OpenAI about $16.27 and $32.02. The earlier runs spent less than
  their estimates.
- **C8.** Greps of the staged docs: no DEV or AC IDs, KGForEdGlobal, STANDARDS,
  dates or numbered steps outside `artifacts/next_cycle_inputs.md`, no British
  spellings, and no compatibility wording.
- **C9.** `node .standards/bin/check.mjs`: passed.
- **C10.** `gh pr view 16` and `gh pr checks 16`, outside the sandbox for `gh`'s
  TLS check: draft, open, `tz6/pipeline-step-3` into `main`, head `1a0cae1`. All
  pass: `Lint and test`, `Lint and test (Python 3.13)`, `Test (Python 3.14)`,
  `Wheel install` on `macos-latest`, `ubuntu-latest` and `windows-latest`,
  `Build the docs` and `TruffleHog secret scan`. `Publish to GitHub Pages` is
  skipped, as on every pull request. This repeats C1 and C2 in CI on the
  committed content.
- **C11.** A second offline `pydelity.aestimate` with the Anthropic default
  model over the candidate folders for G-2. The `real-hints` folders reuse their
  surveys and page files. The `real-0.2.0` folders reuse nothing, so the Chinese
  PDF, which only `real-0.2.0` holds, needs a fresh folder. For slides, CAPS,
  W-9 and Arabic from `real-hints` copies plus a fresh Chinese folder: about
  $6.70 without the verifier and $13.15 with `--verify`.
- **C12.** The user's ten Anthropic runs of 2026-11-28, read with scratch
  scripts over `run.json`, `cost.jsonl`, `page_breaks/`, `pages/` and
  `report.html` in `pydelity-output/real-0.3.0/anthropic/{default,verify}/`.
  Local HEAD is `1a0cae1`, with only this report and `STATE.md` changed. The
  package still reports 0.2.0 until the release. Every request went to
  `claude-opus-5-5`.
  - All ten runs `completed`, with no errors. Each mode has 29 breaks: slides
    15, CAPS 7, W-9 5, Arabic 1, Chinese 1. Every break has a verdict file, and
    each report shows every break beside its two pages.
  - Cost: about $4.36 with the verifier off and $7.92 with it on, $12.28 in all,
    under C11's estimates. This includes extracting the slides' 10 new pages and
    the fresh Chinese folder.
  - Retries: five verdicts needed a second judge attempt (off: CAPS 0006-0007,
    W-9 0002-0003; on: CAPS 0000-0001, W-9 0000-0001 and 0002-0003). Every kept
    verdict passes every check. The verifier needed two attempts once (CAPS
    0000-0001).
  - The verifier passed all 29 verdicts and corrected none.
  - Review lists: empty with the verifier on. With it off, CAPS has 6
    `start_markers` hint differences. The rest are extraction issues (slides 4
    `text_dropped`, W-9 1 `text_added`, Arabic 13 `text_dropped` and 10
    `text_added`), not page-break ones.
  - Verdicts read against their two pages:
    - Slides: in both runs, nothing continues at all 15 breaks. Right: each
      slide stands alone.
    - Arabic and Chinese: in both runs, nothing continues at the one break.
      Right: a boxed mission statement ends the first page and a new part starts
      the second. Neither PDF carries text across a break, so no right-to-left
      or Chinese text join was exercised.
    - W-9: with the verifier off, all 5 are right: a `continue_text` with a
      space at 0000-0001, nothing at the others. With it on, 4 of 5 (R-1).
    - CAPS: in both runs, all 7 breaks continue the one overview table, with the
      repeated title as a repeated item and `(contd)` as a marker where printed.
      Right. The differences are R-2 to R-4.
    - The 6 CAPS hint differences are false alarms. The survey's start markers
      are the strand labels (PHONICS, READING AND VIEWING, HANDWRITING,
      WRITING), and here they start new rows of the same table.
- Reused without rerunning: Tester's Python 3.14 run, clean-install smoke test
  on macOS and reference regeneration, and Documenter's runs of the Python
  examples. They still apply because the code, scripts and examples they ran are
  unchanged, and the Python examples call functions whose code is unchanged.

## Findings

No material findings.

## Questions, Limitations, and Later Dependencies

Gap that blocks this gate: G-2. G-1 is closed.

- **G-1, `AC-042`: no Linux or Windows wheel run (closed 2026-11-28).**
  Resolution: the user opened draft pull request 16, and CI's `Wheel install`
  passes on all three systems on head `1a0cae1`, whose content matches what this
  review assessed (C10). The original gap follows. The AC needs the built wheel
  to install with pip and run all three steps on Linux, macOS and Windows. macOS
  has Tester's run. CI's `Wheel install (ubuntu-latest)` and
  `Wheel install (windows-latest)` jobs would give the rest, but CI runs only on
  a pull request to `main`, and the branch has none (C6).
  - Owner: the user. Opening a pull request is outward-facing, so it needs the
    user's go-ahead. A draft pull request is enough. The scope still keeps the
    merge until after sign-off and Project Uninstallation.
  - Needed: the staged documentation and the cycle records committed and pushed,
    a pull request to `main`, and both jobs passing on its head. CI's docs build
    on the pull request also rechecks C2.
  - Next check: read the check runs for that head and confirm it matches the
    content assessed here.
- **G-2, `AC-050` and `AC-051`: no accepted real runs.** The user ran the
  Anthropic half on 2026-11-28 (C12). The user has not yet accepted those runs,
  and there are no OpenAI runs.
  - `AC-050`: the user runs all three steps with default settings, with real
    Anthropic and OpenAI models, on PDFs covering at least one two-column
    right-to-left document, one Chinese or Japanese document, one tax or
    fillable form, one slide deck or image-heavy PDF, and CAPS. The user reviews
    the verdicts, review lists and reports, and accepts them, with every issue
    raised resolved.
  - `AC-051`: the same with page-break verification's verifier on, on PDFs of
    the user's choice.
  - Owner: the user. An issue they raise goes to its owner first.
  - A planning note, not a requirement: the Japanese gazette used for 0.2.0 has
    one page and gives no break. `irs_pub1_chinese_simplified.pdf` (2 pages)
    gives one. Copying the `real-hints` folders to new output folders before
    running keeps the 0.2.0 records and reuses their surveys and page files
    (C7).
  - Next check: record which PDFs and providers ran, with the verifier off and
    on, and the user's acceptance or issues. If the user shares the folders,
    inspect verdicts, review lists and reports as supporting evidence, and
    recheck that the inputs above are unchanged.
  - The user's plan (2026-11-28): run Anthropic models only, with and without
    the verifier, and not OpenAI "for this exercise". Reviewer gave the commands
    (C11): slides, CAPS, W-9 and Arabic in copies of the `real-hints` Anthropic
    folders, and the Chinese PDF in a fresh folder, with `-y -np`, and `-vf` for
    the verified runs. `AC-050` and `AC-051` name both providers, so Anthropic
    runs alone leave them open. Closing them needs OpenAI runs too, or a scope
    change the user asks Scoper for. Reviewer cannot waive either AC.
  - The runs (2026-11-28): all ten complete, and 53 of 58 verdicts read right
    against their pages with nothing to raise (C12). Reviewer raises four
    issues, covering the other five verdicts, for the user's acceptance review.
    Each needs the user to accept it or send it to its owner:
    - **R-1, W-9 0002-0003, verifier on.** The judge says exempt payee code 1
      (text item `p0002-039`, ending "section 401(f)(2).") carries on in the
      first entry of the next page's list ("2— The United States …"), as
      `continue_entry` with a space. Code 1 ends complete, and code 2 is a
      separate code, so assembly that follows this verdict would make the two
      codes one entry. No text would be lost. The verifier passed it. With the
      verifier off, the judge said nothing continues. That is the best answer
      the page files allow: step 2 extracted code 1 as a text item, and
      `new_entry` needs a list on the earlier page. If the user wants a fix, it
      goes to Developer, for example a prompt rule that `continue_entry` from a
      text item needs the text itself to be cut.
    - **R-2, CAPS 0000-0001, verifier on.** The later page repeats the grade
      header, but the verdict counts 0 repeated header rows. The cause is step
      2: the 0.2.0 extraction of the first page, copied into this folder, puts
      "LISTENING AND SPEAKING" in the header row and gives the body row 4 cells.
      The `header_rows` check rightly rejected a count of 1 against that page
      file, so the judge retried and gave 0. Assembly would print the grade
      header again mid-table. The verifier-off folder's first page is extracted
      right, and its verdict counts 1.
    - **R-3, CAPS 0001-0002, both runs.** Both merge the split PHONICS row, but
      they join its label cell differently: `null` with the verifier off,
      `space` with it on. Both cells have text ("PHONICS" and "PHONICS
      (contd)"), and the field's rule gives `null` only when a cell has no text.
      No join value says the later label only repeats the earlier one. After the
      `(contd)` marker is removed, `space` gives "PHONICS PHONICS". No text is
      lost. Step 4 (assembly) needs a rule for this, which would belong in
      `next_cycle_inputs.md` "Pushed to later steps".
    - **R-4, CAPS 0004-0005.** With the verifier off, the judge merges the
      "READING AND VIEWING (contd)" row into the split row before it. With it
      on, the judge appends it as a new row. Both keep all text. The `(contd)`
      label favors merging, as both runs did for "PHONICS (contd)".
  - None of R-1 to R-4 is a Reviewer finding. The code does what the scope and
    design say, and each issue is a model's reading or a step 2 page file. The
    acceptance call is the user's.
  - The user's call (2026-11-28): rework step 3 now with four changes Reviewer
    proposed from these runs, routed as `USER_REWORK` to Scoper, because the
    scope's ACs define the verdict format, the hint and the verifier (`AC-025`
    to `AC-030`):
    1. Let `new_entry` start from a text item that is the first entry of a list
       carrying on at the next page (R-1), and add a cell join value meaning the
       later cell only repeats the earlier cell's text (R-3).
    2. A prompt rule: `continue_text` and `continue_entry` need the text itself
       to be cut off, and a complete entry followed by a new number is a new
       entry (R-1).
    3. The `start_markers` hint skips `append_rows` pieces, which clears 4 of
       the 6 CAPS false alarms. Skipping a piece whose own continuation marker
       is in that text would clear the other 2. That second rule is optional and
       for Scoper to settle with the user.
    4. Replace the verifier's review of the judge's verdict with a second,
       independent judgment. Code compares the two, keeps the first when they
       match and lists a review issue naming the difference when they do not. In
       C12 the two runs' judges disagreed at exactly the R-1 to R-4 breaks and
       nowhere else, while the verifier caught none.
  - R-2 has no step 3 fix: the fault is in a step 2 page file. R-4 is a judgment
    call that change 4 would flag.
  - The OpenAI half is still open. The rework request asks Scoper to settle with
    the user whether `AC-050` and `AC-051` still need OpenAI runs.
  - Next check, after the rework returns here: reconcile every input against the
    changed scope and design, and read the user's new real runs as C12 read
    these.

`Active Work.BlockedOn` is `NONE`: the user answered, and the open OpenAI
question is in the rework request for Scoper.

Limitations (not findings). None makes delivered output wrong, loses money,
fails a run or breaks a function the acceptance review relies on, so under the
scope's major-issues-only bar they do not block this gate:

- **L1.** `page-breaks.md` describes `continue_entry` as the last list entry
  carrying on "in the next page's first list entry or in a text item". The code
  and prompt also allow a text item carrying on in the next page's first list
  entry. The generated reference page states the full rule.
- **L2.** The FAQ's answer on what page-break verification sends leaves out the
  survey's start markers. `models-and-providers.md` and `page-breaks.md` list
  them.
- **L3.** `python.md` says an error from page-break verification "names the
  break". A `PageBreakError` does, while a `ProviderError` names the page before
  the break. `models-and-providers.md` says this correctly, and
  `next_cycle_inputs.md` records the label as an observation.
- **L4.** `next_cycle_inputs.md` "Loose ends" still asks to check the 0.2.0
  release pull request from the `0.1.1` manifest, which 0.2.0's release has
  done, and the file's title still says it holds inputs for step 3. `AC-049`
  covers only "Pushed to later steps". The next cycle's start should refresh
  these.
- The implementation review's L1 to L5 (check limits) stand as recorded there
  and in `next_cycle_inputs.md`. G-2's real runs are where they would show.

## Progress and Conclusion

- Done: inputs reconciled with every earlier record, and none changed. Every
  changed doc read against the code. The suite, docs build, link check,
  formatting, lint and package check rerun. The quoted CLI output checked
  against a stand-in run.
- The gate does not pass. No material finding is open. G-1 is closed by CI on
  pull request 16. G-2 stays open: the Anthropic runs are read (C12), but the
  user has not accepted them, and the OpenAI half has no runs and no scope
  change. Final review cannot pass with an open dependency.
- Status `IN_PROGRESS`. The user's rework moves the cycle to `SCOPING`, with a
  recovery frame that resumes at `REVIEWING_FINAL`.
- Next, on resume: reconcile every input above against the reworked scope,
  design, code, tests and docs, since the rework changes the verdict format, the
  hint, the verifier and AC wording. Rerun C1 to C3, C5 and C9, recheck the CI
  on pull request 16's new head, and read the new real runs. Then mark this
  report `COMPLETE` and hand off to Synchronizer only when `AC-050` and `AC-051`
  have accepted runs for the providers the scope then names.

Plain-language summary: the work goes back to scoping for a rework you asked
for, and this review picks up again afterwards. The code did what the scope
said. The docs match it, and the tests, docs build, link check and package check
all pass, in CI too. The ten Anthropic runs all finished, for about $12, and 53
of the 58 page-break verdicts look right. The misses showed where step 3 can do
better, so you chose four changes: give the model the answers it was missing,
tighten one prompt rule, quiet a noisy hint, and swap the verifier for a second
independent judgment. The OpenAI question goes to Scoper with them. Four small
wording slips in the docs are written down above and don't block anything.

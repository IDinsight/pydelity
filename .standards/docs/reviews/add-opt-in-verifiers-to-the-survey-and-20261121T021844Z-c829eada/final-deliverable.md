<!-- STANDARDS
Artifact: REVIEW
Cycle: add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada
ReviewKind: FINAL_DELIVERABLE
-->

# Review Report

`Cycle`: `add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada`
`ReviewKind`: `FINAL_DELIVERABLE` `Status`: `COMPLETE` `User Style`: `tony`

## Assessed Inputs and Scope

- Cycle mode `STANDARD`, completion policy `FULL_DELIVERABLE`, project mode
  `BROWNFIELD`, entered by a `FORWARD` handoff from `DOCUMENTING`. No recovery,
  no outstanding obligations. Current ACs `AC-001` to `AC-042`, none retired.
- Records, by last commit and SHA-256 prefix:
  - scope
    `.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`49448e5`, `dd6ea5291602`);
  - design
    `.standards/docs/specs/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`81d7dcd`, `3c0eddfeb9d1`), decisions 1–13 and the technical acceptance
    criteria;
  - development plan
    `.standards/docs/development/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`b579737`, `4251351f9aef`; `COMPLETE`);
  - verification report
    `.standards/docs/verification/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`fc6df7d`, `2aceaad01ae2`; `COMPLETE`, `FULL`);
  - implementation review
    `.standards/docs/reviews/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada/implementation.md`
    (`31cbf8a`, `7e0539ce3ca5`; `COMPLETE`, no material findings);
  - documentation record
    `.standards/docs/documentation/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`c0ed1e9`, `ce37e24b779e`; `COMPLETE`);
  - project context `.standards/CONTEXT.md` (`0573e11`, `09045f457b2d`); user
    style `.standards/user-styles/reviewer/tony.md` (`797def3`, `43b3830a5152`).
- Repository: branch `tz6/pipeline-step-2` at `c0ed1e9` (also the pushed remote
  head), clean apart from this report. Tree identities at `c0ed1e9` (SHA-256
  prefix of `git ls-tree -r HEAD -- <path>`): `src` `e69594900418`, `tests`
  `9f196e12f589`, `scripts` `5f27c2dedfd2`, `docs/src/content/docs`
  `86e44c540eda`, `examples` `4cdd597a30eb`, `.github` `70836f8a13a9`.
- Change read for this gate: `git diff 31cbf8a c0ed1e9` (23 files: the
  Documenter's docs, README, three docstrings, three regenerated reference
  pages, `artifacts/next_cycle_inputs.md`, its record and `STATE.md`). Every
  saved-content hash in the documentation record matches the tree. The code and
  tests themselves were assessed by the implementation review on `fc6df7d`; this
  review relies on that assessment only after confirming (R3) that `src`,
  `scripts`, `tests`, `examples`, `pyproject.toml`, `uv.lock` and `.github`
  changed since then only in docstrings.
- Docs read against the code: the new `guides/verifiers.md` in full, and the
  changed parts of `README.md`, `index.md`, `guides/page-extraction.md`,
  `outputs.md`, `configuration.md`, `costs.md`, `reruns.md`,
  `models-and-providers.md`, `python.md`, `command-line.md`,
  `start/first-survey.md` and `faq.md`; the reference pages for the new settings
  and fields. Code read for that: `config/schemas.py`, `cli.py`,
  `surveying/prompts.py`, `survey.py`, `agents.py`, `schemas.py`,
  `extracting/extraction.py`, `agents.py`, `validators.py`, `report/html.py`,
  `pipeline/runner.py`, `review.py`, `surveying/facts.py`.
- Environment: macOS arm64, Python 3.13.9 (`.venv`, editable install), Node
  23.10.0, the repo's locked uv, prek, Prettier and markdownlint, pnpm for the
  docs site.
- Project references loaded: `NONE` (`.standards/project-references/reviewer/`
  does not exist).
- Session: a new conversation that started with this review and holds none of
  the authoring history. The client cannot certify freshness, and the models
  that produced the work are not recorded, so whether this review ran on a
  different model is unknown.

## Contract and Evidence Assessment

Code-level dispositions rest on Tester's formal evidence (E-numbers in the
verification report) and the implementation review (its R-numbers), still
applicable because only docstrings changed since (R3) and the suite passes on
the current head (R1). This review's diagnostics are R1–R8 below.

| Obligation / criterion                                                                                                               | Assessed evidence                                                                                                                        | Current disposition                                                                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AC-001`, `AC-002`, `AC-003`, `AC-004`, `AC-005`, `AC-006` / settings, switches, estimates, reuse                                    | Verification E13–E15, E22–E26; implementation review; R1; R5 (estimates, reuse when turned on and off, against the stand-in)             | Supported. The verifier guide, configuration, costs and reruns guides describe this behavior as the code does.                                                         |
| `AC-007`, `AC-008`, `AC-009`, `AC-010`, `AC-011`, `AC-012`, `AC-013`, `AC-014`, `AC-015`, `AC-016`, `AC-017` / the survey's verifier | Verification E23–E25, E27, E31; implementation review R2; R5; R6; G-1 real runs                                                          | Supported. On real PDFs it ran on both providers' output modes: 7 verdicts each, 3 Anthropic corrections kept, every OpenAI survey passed.                             |
| `AC-018`, `AC-019`, `AC-020` / page extraction without its verifier                                                                  | Verification E12–E21, E23; implementation review R3; R5; G-1 real runs                                                                   | Supported. Real default runs made no verifier request, saved `verification: null` and listed every text difference.                                                    |
| `AC-021`, `AC-022`, `AC-023`, `AC-024`, `AC-025` / the five fixes                                                                    | Verification E32–E34, E39–E42; implementation review                                                                                     | Supported. `reruns.md` and `python.md` describe `load()`'s filter as `_load_pages` does.                                                                               |
| `AC-026` / mocked tests                                                                                                              | 207 tests (R1); verification report                                                                                                      | Supported.                                                                                                                                                             |
| `AC-027`, `AC-028` / CI, required checks, wheel on three systems                                                                     | CI on `fc6df7d` (implementation review R4, R5); R3                                                                                       | Supported. No CI run exists for `c0ed1e9` (the draft pull request is closed); the code CI ran on differs only in docstrings, and R1, R2 and R7 cover the rest locally. |
| `AC-029` / wheel and sdist install and pass metadata checks                                                                          | Verification E44; R7 (`twine check --strict` on the new README)                                                                          | Supported.                                                                                                                                                             |
| `AC-030` / description, classifiers, README                                                                                          | `pyproject.toml` description and classifiers; `README.md` lines 8–17 and 89–91                                                           | Supported. The README says each step has an optional verifier, a second request to the same model, off unless turned on.                                               |
| `AC-031` / release setup produces 0.2.0                                                                                              | Implementation review R5; manifest `0.1.1`; `contributing/releases.md`                                                                   | Supported for release readiness; the release pull request follows merge, as the scope says.                                                                            |
| `AC-032` / a user can choose and read the verifiers from the docs alone                                                              | `guides/verifiers.md`; R4 (no "second model", "reviews every page" left); R5; R6                                                         | Supported. The guide covers both switches, each verifier's review, the cost, every outcome and its fields, and the review list with and without one.                   |
| `AC-033` / reference pages cover the new settings and fields                                                                         | R2 (regenerated pages identical after formatting); reference pages for `verify`, `--verify`/`-vf`, `verification`, `agent`, `verifier`   | Supported.                                                                                                                                                             |
| `AC-034` / what page extraction sends                                                                                                | `page-extraction.md`, `models-and-providers.md`, `faq.md`; `extracting/prompts.py` `_page_text`, `_form_field_line`                      | Supported. The guides and FAQ list the repeated lines' stored text and the form fields' values, and that text retries quote stored lines.                              |
| `AC-035` / page file reference examples                                                                                              | `reference/page-json.md` lines 62–66, 116–124, 182–190; `extracting/validators.py` `_failure`, `unmatched_labels`                        | Supported. The examples are page extraction's own, and the text says the `item_ref` comes from the answer and that items have IDs, not that it names one.              |
| `AC-036` / the other wording                                                                                                         | `command-line.md` (`--yes` with `2>`), `python.md` (`load` takes the folder; `RunResult.pages`), `costs.md`, `faq.md`, `reruns.md`       | Supported. Each item matches the code: `cli.py` asks on standard error; the survey fingerprint holds `pdf_sha256`, not `pdf_name`; `costs/ledger.py`.                  |
| `AC-037` / README and docs examples match 0.2.0                                                                                      | R5 (the guide's estimate lines and figures, the `load`, `verify=True`, `aestimate` and override examples); R2 (docs build, links)        | Supported for what can run offline. The README's quick start sends real requests and is covered by the same code paths.                                                |
| `AC-038` / next-cycle inputs                                                                                                         | `artifacts/next_cycle_inputs.md` **Pushed to later steps** ("Verifier per step") and **Review findings and observations left for later** | Supported. The later steps' verifiers are opt-in with the global setting and an override each, and every remaining item the scope left is still listed.                |
| `AC-039` / accepted real runs with default settings                                                                                  | G-1: 14 runs in `pydelity-output/real-0.2.0/{anthropic,openai}/default/`; the user's acceptance, 2026-11-21                              | Supported (G-1 closed).                                                                                                                                                |
| `AC-040` / accepted real runs with both verifiers on                                                                                 | G-1: 14 runs in `pydelity-output/real-0.2.0/{anthropic,openai}/verify/`, every PDF kind the AC names; the user's acceptance, 2026-11-21  | Supported (G-1 closed).                                                                                                                                                |
| `AC-041`, `AC-042` / the reorder                                                                                                     | Implementation review R6, R7; verification E1–E11; R3 (no code moved since)                                                              | Supported.                                                                                                                                                             |

Constraints across the deliverable: no shipped file names a development step,
date, role or cycle (R4); the docs use American spelling ("canceled"); no
compatibility code was added for older files, and the docs say old output
folders do not carry over only where the design asks (the user style's
compatibility rule is met).

## Checks and Results

All from the repository root on `c0ed1e9`, 2026-11-21. Scratch scripts are in
this session's scratchpad (`fr/`), not in the repo.

- **R1 — Suite and linters.**
  `.venv/bin/pytest -q --numprocesses auto -p no:cacheprovider` 207 passed;
  `.venv/bin/pytest -q --doctest-modules src -p no:cacheprovider` 28 passed, 1
  skipped; `ruff check scripts src tests` "All checks passed!";
  `ruff format --check scripts src tests` "89 files already formatted";
  `ty check scripts src tests` "All checks passed!"; `interrogate` 100.0%. All
  exit 0.
- **R2 — Reference pages, Markdown and the docs site.**
  `.venv/bin/python scripts/generate_reference_docs.py` (11 pages), then
  `just lint-markdown` (outside the sandbox, which blocks uv's cache): afterward
  `git status` shows no change to any tracked file, which is CI's
  stale-reference check; `STANDARDS check passed.`; markdownlint "Passed".
  `pnpm run build` in `docs/` "29 page(s) built", then `pnpm run check-links`
  "Checked local links and fragments in 29 HTML pages.", exit 0.
- **R3 — Code unchanged since the implementation review.**
  `git diff --name-only 31cbf8a c0ed1e9 -- src scripts tests examples pyproject.toml .github uv.lock`
  lists only `src/pydelity/extracting/schemas.py`, `pipeline/schemas.py` and
  `review.py`; a scratch AST comparison with docstrings removed (`fr/nodoc.py`)
  finds the same code in all three. None of the three models is part of an
  output type sent to a model.
- **R4 — Wording.**
  `grep -rnE "DEV-[0-9]|AC-[0-9]|2026-|KGForEd|STANDARDS|Scoper|Architect|Developer|Tester|Documenter|\bcycle\b|step [1-6]\b|second model|reviews every page|verifier model|two requests per page"`
  over `README.md`, `docs/src/content/docs`, `src/pydelity`, `examples` and
  `pyproject.toml`: only two docstrings using "cycle" for a cycle in a tree. No
  British spelling in the added lines.
- **R5 — The guides' examples against the stand-in** (`fr/examples.py`, the
  repo's `MockProviders` with the 1965 scan's survey and page answers and a
  passing survey verdict; nothing sent to a provider):
  - before a survey: survey estimate `0.235352`/`2.530056`, 3 requests,
    `verifier` false; with `verify=True` `0.466232`/`5.454696`, 6 requests,
    `verifier` true. The CLI with `--verify` and no input printed
    `Survey with its verifier cost estimate: about $0.47, at most $5.45 (up to 6 requests to anthropic:claude-opus-5-5)`
    and exited 3;
  - after a default survey: extraction `0.227496`/`4.810488`, 6 requests; with
    `advanced={"extraction": {"verify": True}}` `0.454464`/`10.411392`, 12
    requests; the CLI printed
    `Extraction cost estimate: about $0.23, at most $4.81 (2 pages, up to 6 requests to anthropic:claude-opus-5-5)`.
    These are the figures in `verifiers.md`, `costs.md` and `first-survey.md`;
  - `--verify` on that folder estimates the survey again, as `verifiers.md` and
    `reruns.md` say;
  - default run, then the `python.md` `load` example: both pages
    `verification is not None` false; ledger agents `extractor`, `surveyor`;
  - `verify=True` on a new folder: survey and both pages verified; ledger
    `(survey, surveyor)`, `(survey, verifier)`, `(extraction, extractor)`,
    `(extraction, verifier)`;
  - the extraction override alone: survey `verification` `None`, both pages
    verified;
  - turning `verify` on for the default folder: 6 new requests (survey and its
    verifier, two pages each with extractor and verifier), all verified; then
    off again: no request, both steps `reused`.
- **R6 — Guide text against the code.** The survey checklist in `verifiers.md`
  is `surveying/prompts.py` `_REVIEW` items 1–8; the report and log outcome
  texts are `report/html.py` `_verifier_text` and both steps'
  `_verifier_outcome`; the review-list table matches `build_survey` and
  `_page_issues`; the reuse lines match `saved_survey` and `_reusable_page`; the
  error classes and exit code match `run_survey` and the CLI's mapping as the
  implementation review assessed them.
- **R7 — Package build.** `just build` (outside the sandbox): wheel and sdist
  built, `twine check --strict` PASSED for both, with the new README as the long
  description.
- **R8 — Existing real-run folders.** `pydelity-output/real/{anthropic,openai}/`
  hold 14 runs written on 2026-11-20 with page extraction's code: every
  `pdf_survey.json` lacks `verification`, so none is evidence for `AC-039` or
  `AC-040`. Their `cost.jsonl` survey lines have `agent: null`, so a run on one
  of those folders now stops with an `OutputError` (design decision 8); new runs
  need new folders.
- Offline estimate for the real runs, `pydelity.aestimate` with the 2026-11-20
  PDFs and page selections (`fr/est.py`, nothing sent): default settings about
  $5.34 on the Anthropic default and $11.42 on `openai:gpt-6.2-astra`; with
  `verify=True` about $10.36 and $22.21.
- Not run: Python 3.14 locally, the wheel smoke test locally, zizmor, CI on
  `c0ed1e9`. CI on `fc6df7d` covered them on code that differs only in
  docstrings (R3); the merge pull request runs them again as required checks.

## Findings

**No material findings.**

## Questions, Limitations, and Later Dependencies

Gap at the first review, now closed:

- **G-1, `AC-039` and `AC-040`: no evidence of the user's real runs (closed
  2026-11-21).** The scope requires the user to run the survey and page
  extraction with real Anthropic and OpenAI models on PDFs of their choice, once
  with default settings (`AC-039`) and once with both verifiers on (`AC-040`,
  covering at least one two-column right-to-left document, one Chinese or
  Japanese document, one tax or fillable form, one slide deck or image-heavy
  PDF, and CAPS), review the results and accept them, with every issue they
  raise resolved. These also carry the design's open risks: whether
  `SurveyVerdict`, which nests a whole survey answer, works with OpenAI's native
  output and Anthropic's prompted output, and the 6,000-token typical verdict.
  Owner: the user. Consequence: this gate cannot pass, so the cycle cannot reach
  synchronization or sign-off, until the user reports the outcome; an issue they
  raise goes to its owner first. The question is in `Active Work.BlockedOn`.
  Next check, on re-review: record which PDFs and providers ran, with and
  without verifiers, and the user's acceptance or issues; if the user shares the
  output folders, inspect the surveys' verdicts, page files, review lists and
  reports as supporting evidence, and recheck that the assessed inputs above are
  unchanged. Re-review (2026-11-21): the user asked for the commands, and
  Reviewer gave CLI loops over the 2026-11-20 PDFs and page selections (Arabic
  and Chinese Publication 1, the Japanese gazette, W-9 page 1, the 1965 scan,
  slides 1–6, CAPS) with `-m anthropic:claude-opus-5-5 -np -y`, into
  `pydelity-output/real-0.2.0/anthropic/default/<pdf>/` and, with `-vf`,
  `.../anthropic/verify/<pdf>/`, run with `.venv/bin/pydelity` on `c0ed1e9`.
  Anthropic runs (the user's), inspected by Reviewer at the user's request as
  supporting evidence, not acceptance:
  - All 14 runs `completed`, no warnings, no error. Default $4.77 (survey $0.93,
    extraction $3.84; 43 requests); with verifiers $8.10 (survey $0.96 plus its
    verifier $1.01, extraction $3.95 plus its verifier $2.18; 75 requests). The
    page verifier was 36% of extraction's cost; the survey's verifier about
    doubled the survey's. Offline estimates were $5.34 and $10.36.
  - Defaults (`AC-001`, `AC-018`, `AC-020`): no `verifier` ledger line, every
    `pdf_survey.json` and page file has `verification: null`, and each report's
    survey and page lines say `no verifier ran`.
  - Review lists without a verifier (`AC-019`, `AC-039`): Arabic 24 (22
    `text_dropped`/`text_added` from its broken stored text, 2
    `no_matching_label`), the Japanese page 7 (6 text differences, 1
    `no_matching_label`), slides 14 (11 `no_matching_label`, because that run's
    survey made no page-furniture label; 1 `labels`; 2 `text_dropped`), the
    rest 0. The slides' `text_dropped` lines are real duplicates: the text layer
    holds each footer twice (`read_lines` on pages 2 and 3), and the answer has
    it once.
  - The survey's verifier (`AC-007` to `AC-013`, `AC-040`): it ran on all 7 PDFs
    on Anthropic's prompted output with one verdict each. 4 passed; 3 found one
    problem each and their corrections were kept, with no correction failures:
    the slides' note named the wrong pages for the duplicated footer, a W-9
    region box covered the wrong area, and the Japanese running-header region
    sat too low. No survey issue remained. Verdict output averaged about 2,000
    tokens, against the estimate's 6,000.
  - Page verifiers: 22 pages, 26 verifier requests. 18 passed; 3 corrections
    kept: slides page 2 (footer case and box, 3 attempts; the six subject areas
    came back as one list item), Arabic page 1 (a dropped letter in item `p8`, 3
    attempts) and Chinese page 0 (five boxes and containers shifted below their
    text). Their text differences stay in `checks` and off the review list, as
    `AC-019` says; the verified runs' review lists hold 1 issue in all
    (`no_matching_label` on the Japanese page).
  - Boxes, by Reviewer's scratch check of each text-layer word's center against
    the item boxes (3 pt margin, displayed coordinates), default and verified: 0
    outside on all slides, all 8 CAPS pages and Chinese page 0; W-9 25 and 13 of
    933 (field labels); Arabic 0 and 3 of 581, 0 and 5 of 1,294; Chinese page 1
    3 and 0 of 276; the Japanese page 31 and 26 of 222, the kind of miss the
    user accepted on 2026-11-20.
  - Reading order and rotation: Arabic `rtl`, the top row read right to left and
    the columns from the right; the Japanese page `ttb`,
    `column_order: right_to_left`, columns from x 390 down to 132; Chinese left
    to right; CAPS pages 0–7 turned 90 degrees.
  - Whether the verifier improved the results, asked by the user. The two runs
    made their own surveys and extractions, so their differences mix the
    verifier's effect with run-to-run variation. Each of the six kept
    corrections was therefore checked against the PDF (text-layer positions and
    renders) and against the run without a verifier:
    - right, and the default run made the same mistake unflagged: Arabic page 1,
      `فستعين` corrected to `فسيتعين` (item `p0001-014`; the default run keeps
      `فستعين`, and none of its 12 text issues names that line);
    - right, where the default run was already right: the W-9 survey's
      name-and-number table region (the verified run's survey put it on the
      certification items), the slides survey's note on which pages duplicate
      the footer (`read_lines` shows indexes 2, 3, 7 and 9), and the slides page
      2 footer's case;
    - worse: the Japanese survey's running-header region, moved to y 0.005–0.028
      of the page, in blank space above the header line, whose text-layer words
      sit at y 0.050–0.065 (a render confirms it); the default run's region,
      0.035–0.06, covers the header;
    - no better: Chinese page 0's boxes, moved from about half a line too low to
      about half a line too high. The `IRS 的使命` box the verifier called low
      (grid y 889–907) matched its text-layer words (889–904); the correction
      (881–898) is worse.
    - Review list: 45 issues without verifiers against 1 with them. 28 are text
      differences against the Arabic and Japanese stored text, which the
      verifier accepted, and 14 come from the default run's slides survey
      lacking a page-furniture label, which is run-to-run variation, not the
      verifier.
    - The design's risks name a kept correction that is worse. This is evidence
      for the user's acceptance of `AC-040`, not an established defect against
      the contract: the scope asks the verifier to catch what code cannot judge,
      not that every correction is right.
  - Text, which the user named as what later steps depend on most (boxes
    slightly off are acceptable to the user). Scratch scripts `fr/textdiff.py`
    and `fr/vslayer.py`:
    - Between the runs: 10,367 words (CJK by character), 10 of 22 pages
      identical. The other differences are page furniture in a different
      reading-order place (CAPS), a space (Chinese), arrows and leader dots
      (1965 scan, W-9), a ruby's order (Japanese), and four real ones, settled
      against renders: Arabic `فسيتعين` and the print's single parenthesis in
      two phone lines, and the 1965 scan's smudged `even` (default `eve-`), each
      right in the verified run; the Japanese margin marks `○ ▷ ○`, kept only in
      the default run.
    - The verifier itself changed text on two pages: the Arabic letter and the
      slides footer's case. The verified run's other text gains came from its
      own extractor, which the verifier passed.
    - Against the stored text where it is reliable (the 6 slides, 8 CAPS pages,
      the W-9 and both Chinese pages): both runs match word for word, apart from
      the duplicated slide footers, labels the stored text joins (`ITaxpayer`,
      `IICertification`) and two phone numbers the answers join.
    - Not established: errors both runs share on the Arabic, Japanese and
      scanned pages, which only a proofread against the images would show.
  - The user's acceptance (2026-11-21): "Accept them", for the Anthropic runs
    with and without verifiers, after the box, region and text comparisons
    above; the user said boxes slightly off are acceptable and raised no issue.
    OpenAI runs (the user's, `-m openai:gpt-6.2-astra`, the same loops into
    `pydelity-output/real-0.2.0/openai/{default,verify}/<pdf>/`), inspected by
    Reviewer the same way:
  - All 14 runs `completed`, no warnings, no error. Default $8.16 (survey $2.05,
    extraction $6.10); with verifiers $10.69 (survey $1.07 plus its verifier
    $1.42, extraction $5.20 plus its verifier $3.00). The verified run's own
    requests cost less than the default run's, likely from the provider's prompt
    cache, so the totals understate the verifiers' share.
  - Defaults behave as with Anthropic: no `verifier` ledger line, every
    `verification` `null`. Review lists without a verifier: Arabic 26 and the
    Japanese page 7 (text differences, 1 `no_matching_label`), slides 2 (the
    duplicated footers), the rest 0; with verifiers, 1 (`no_matching_label` on
    the Japanese page).
  - The survey's verifier ran on OpenAI's native output on all 7 PDFs and passed
    every survey, with no correction (about 500 output tokens each). This
    settles the design's risk about `SurveyVerdict` on both providers.
  - Page verifiers: 22 pages, 24 requests; 21 passed. One correction kept,
    Arabic page 1 (3 attempts), with two text problems: it restored `الصحف`
    ("newspapers"), which that run's extractor had dropped, and it changed
    `ضريبية` to `ضريبة`, which is wrong: a 600 DPI render shows the page prints
    `بديون ضريبية`, as the default run has it.
  - Text between the runs: 10,521 words, 18 of 22 pages identical. The verified
    run is better on the Japanese decree number, `政令第百四十三号` (a render
    and the stored text confirm `百`), which the default run gives as
    `第四十三号` twice; its `text_added` issue on the default review list quotes
    that line. Also better: the 1965 scan's `—If` (default `—if`) and `◀`, and
    the Japanese section banners `政令` and `告示` as text. These came from the
    verified run's own extractor; its verifier passed those pages.
  - Against the reliable stored text: both runs match word for word on the
    slides, CAPS, the W-9 and both Chinese pages, apart from the same
    stored-text artifacts as Anthropic's and phone numbers the answers join.
  - Boxes: 0 words outside on the slides, CAPS, Arabic and Chinese pages; the
    Japanese page 6 of 222 in both runs; the W-9 189 of 933 in both, because
    OpenAI's field boxes cover the input area and not the printed label, as the
    user accepted on 2026-11-20.
  - Across both providers the verifiers changed text materially three times in
    44 pages, two right and one wrong, and changed no OpenAI survey. The text
    differences between runs are mostly run-to-run variation.
  - Providers compared, asked by the user (default runs, `fr/xdiff.py`, each
    disagreement settled against a render): text is close to even. Both match
    the reliable stored text word for word. Anthropic's runs have two wrong
    Arabic letters (`فستعين`; `تُغلق` where the page prints `نُغلق`, which its
    verifier passed) and an added parenthesis; OpenAI's default run has the
    Japanese decree number as `第四十三号`, `—if` and no text for the section
    banners. OpenAI's 1965 exemption checkboxes are prompted `Regular`,
    `65 or over` and `Blind` twice, without `Yourself` and `Wife`, which
    Anthropic keeps. Default runs: Anthropic $4.77 and 11.0 minutes, OpenAI
    $8.16 and 18.6 minutes.
  - The user's acceptance (2026-11-21): "Accept them", for the OpenAI runs with
    and without verifiers, after the comparisons above, raising no issue. With
    both providers accepted and no issue open, G-1 is closed and
    `Active Work.BlockedOn` is cleared.

Non-material limitations, none of which prevents assessing the documentation:

- No CI run exists for `c0ed1e9`. The changes since CI's last run are docs,
  docstrings and the README, checked locally by R1, R2 and R7.
- `artifacts/next_cycle_inputs.md` **Loose ends** still names pull request 10
  (closed, like 11 and 12) as the one to retitle `feat:` before merging. The
  line predates this cycle (`5b94a4d`), and the instruction itself (a
  non-breaking `feat:` title on the merge pull request, since its squash title
  is what release-please reads) still holds for whichever pull request merges.
- The README's Python quick start sends real requests and was not run; R5 ran
  the same functions against the stand-in.
- The documentation record's two non-blocking observations (the CLI exit code 0
  help text, and the file list of a run stopped at the question) are not
  documentation defects: the command-line guide's exit code table covers the
  pause, and no AC depends on either.

No later-role dependency, material gap or blocking question remains.

## Progress and Conclusion

- Done: inputs and identities; every documentation surface against the code;
  R1–R8; G-1's real runs on both providers, inspected and accepted; every
  current AC and relevant technical criterion has a supported disposition with
  current evidence.
- Freshness, rechecked immediately before this conclusion (2026-11-21): head
  `c0ed1e9`; the only uncommitted changes are this report and `STATE.md`; scope
  `dd6ea5291602`, design `3c0eddfeb9d1`, development plan `4251351f9aef`,
  verification report `2aceaad01ae2`, documentation record `ce37e24b779e`,
  implementation review `7e0539ce3ca5`, context `09045f457b2d`; trees `src`
  `e69594900418`, `tests` `9f196e12f589`, `scripts` `5f27c2dedfd2`,
  `docs/src/content/docs` `86e44c540eda`, `examples` `4cdd597a30eb`, `.github`
  `70836f8a13a9`: all as assessed.
- **Passing (2026-11-21, on `c0ed1e9`).** No material finding; G-1 is closed by
  the user's accepted real runs on both providers; no later dependency, material
  gap, blocking question or outstanding obligation remains; `check` passes.
  Next: `SYNCHRONIZING` (`FULL_DELIVERABLE`). Passing this gate is not cycle
  completion or sign-off.

Earlier conclusion (2026-11-21, on `c0ed1e9`): not passing, blocked on G-1 until
the real runs and the user's acceptance.

Plain-language summary: the final review passes, and the work can move on to
synchronization. The docs describe the opt-in verifiers as the code behaves, and
the tests, docs build and package check pass. Your real runs on Anthropic and
OpenAI, with and without verifiers, all completed, and you accepted them. They
showed the verifiers work on both providers but changed little: three material
text corrections in 44 pages, two right and one wrong, which supports keeping
them off by default. Synchronization and your sign-off are still to come.

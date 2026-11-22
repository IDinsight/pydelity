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
  `BROWNFIELD`. This pass is the final review rerun under recovery frame 1
  (owner `SCOPING`, `ResumeAt` `SYNCHRONIZING`, `RerunThrough`
  `REVIEWING_FINAL`), entered by a `FORWARD` handoff from `DOCUMENTING`: the
  user's rework that makes code's measurements of the PDF hints. Reviewer does
  not own the frame. No outstanding obligations.
- Current acceptance set: `AC-001` to `AC-054` without `AC-019` and `AC-034`,
  which are retired (replaced by `AC-048` and `AC-051`). New since the earlier
  pass: `AC-043` to `AC-054`.
- Records, by last commit and SHA-256 prefix, read at `2b090b4`:
  - scope
    `.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`01598d8`, `2d921029f902`);
  - design
    `.standards/docs/specs/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`5cb51ac`, `a69221d00c35`), decisions 1–16, **Checks and hints**, **Docs
    and docstrings**, **Test seams** and the technical acceptance criteria;
  - development plan
    `.standards/docs/development/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`de4efcd`, `215cd7c4e02f`; `COMPLETE`);
  - verification report
    `.standards/docs/verification/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`278264b`, `2dac1da950f8`; `COMPLETE`, `FULL`, E1–E60);
  - implementation review
    `.standards/docs/reviews/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada/implementation.md`
    (`a1d6cfe`, `938622aee9ab`; `COMPLETE`, no material findings, R11–R18);
  - documentation record
    `.standards/docs/documentation/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
    (`2b090b4`, `69eaad16c215`; `COMPLETE`);
  - project context `.standards/CONTEXT.md` (`0573e11`, `09045f457b2d`); user
    style `.standards/user-styles/reviewer/tony.md` (`797def3`, `43b3830a5152`).
- Repository: branch `tz6/pipeline-step-2` at `2b090b4`, clean apart from this
  report. Tree identities at `2b090b4` (SHA-256 prefix of
  `git ls-tree -r HEAD -- <path>`): `src` `369f58ab7050`, `tests`
  `98ea84f67b1b`, `scripts` `cb966db01cbe`, `docs/src/content/docs`
  `1b0b9eb10dae`, `examples` `4cdd597a30eb`, `.github` `70836f8a13a9`. The
  cycle's code change
  `git diff 126f52f HEAD -- src scripts examples docs pyproject.toml` hashes
  `38c6feeae76ded0a`.
- Change read for this gate: `git diff a1d6cfe 2b090b4` (the documentation pass:
  six guides and the FAQ, `review.py` docstrings, two regenerated reference
  pages and `artifacts/next_cycle_inputs.md`). Its diff outside `.standards/`
  hashes `0385501736e6b7e7`, the value in the documentation record, and each
  saved-content hash in that record matches the tree. The code and tests rest on
  Tester's evidence and the implementation review at `278264b`, still applicable
  because the only code-path file changed since is `src/pydelity/review.py`, in
  docstrings only (R3).
- Docs read against the code: the changed parts of `guides/page-extraction.md`,
  `verifiers.md`, `outputs.md`, `models-and-providers.md`, `command-line.md` and
  `faq.md`; the generated `extraction-checks.md`, `survey-checks.md`,
  `page-json.md` and `pdf-survey-json.md`; `README.md` and `index.md` for
  wording the rework could make stale; `artifacts/next_cycle_inputs.md` **User
  decisions that apply to later steps** and **Pushed to later steps**. Code read
  for that: `extracting/prompts.py` in full, `extracting/extraction.py`
  (`_extract_page`, `_kept_answer`, `_page_issues`, `extract_pages`),
  `extracting/validators.py` (module docstring, the six checks, `CHECKS`, the
  `artifacts` and `form_fields` hints), `surveying/validators.py` (module
  docstring and the two hints' details), `surveying/prompts.py` (hint wording),
  `review.py`.
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
verification report) and the implementation review's diagnostics (its
R-numbers), still applicable because only docstrings changed since (R3) and the
suite passes on the current head (R1). This review's diagnostics are R1–R7
below.

| Obligation / criterion                                                                                                                                                                                                                                                               | Assessed evidence                                                                                                                                             | Current disposition                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `AC-043` / every request presents the facts and survey findings as hints; no message asks to match one                                                                                                                                                                               | Verification E51–E55 (P4, REQ, S4); implementation review R13; `extracting/prompts.py` and `surveying/prompts.py` read (R5)                                   | Supported. `page-extraction.md`, `models-and-providers.md` and the FAQ describe the hint headings and that the image decides, as the prompts say.                                                                                                |
| `AC-044` / only checks send an answer or correction back; a hint never fails anything                                                                                                                                                                                                | E51–E55 (P1–P3, S1–S3, V1), E54; implementation review R13, R14                                                                                               | Supported. The guides' checks and hints split matches `CHECKS` and `HINTS` in both steps (R5).                                                                                                                                                   |
| `AC-045` / page requests carry no stored text beyond repeated lines and form field values                                                                                                                                                                                            | E51–E55 (REQ, P2); implementation review R14; `_page_text` read (R5)                                                                                          | Supported.                                                                                                                                                                                                                                       |
| `AC-046` / the page verifier lists every hint difference, quoting stored lines                                                                                                                                                                                                       | E51–E55 (P3); `verify_page` read (R5)                                                                                                                         | Supported. `verifiers.md` and `page-extraction.md` say the verifier's request quotes the stored lines a text difference is about.                                                                                                                |
| `AC-047` / a correction passing every check is kept whatever its hint differences                                                                                                                                                                                                    | E51–E55 (P3); `_kept_answer` read (R5)                                                                                                                        | Supported, and documented in `verifiers.md` and `page-extraction.md`.                                                                                                                                                                            |
| `AC-048` / page review list by outcome; `hints` keeps every difference                                                                                                                                                                                                               | E51–E55 (P1, V1, P2, P3); `_page_issues` read (R5); R4 (`hints` on each page file, no difference listed when none)                                            | Supported. The review-list table in `verifiers.md` and the hints list in `outputs.md` match `_page_issues`.                                                                                                                                      |
| `AC-049` / a final answer still failing a check is kept and listed; only an unusable answer stops a run                                                                                                                                                                              | E51–E55 (P2, S4 and the stop tests); `extract_pages` read (R5)                                                                                                | Supported. `models-and-providers.md` names the stop conditions for both steps as the code raises them.                                                                                                                                           |
| `AC-050` / item 10's tests, both providers mocked, each verifier on and off                                                                                                                                                                                                          | E51–E55, E60; R1 (211 passed)                                                                                                                                 | Supported.                                                                                                                                                                                                                                       |
| `AC-054` / repeated lines and the survey's finding as hints; no order to put one in an artifact item                                                                                                                                                                                 | E51–E55 (P4, REQ); `_RULES` page furniture paragraph read (R5)                                                                                                | Supported.                                                                                                                                                                                                                                       |
| `AC-051` / docs and docstrings say what page extraction sends                                                                                                                                                                                                                        | `models-and-providers.md` lines 64–80, FAQ "What is sent", `page-extraction.md` step 2; module docstrings of `extracting/prompts.py`, `validators.py`; R2, R5 | Supported. The FAQ lists form field values; no page or docstring says nothing stored is sent or that a text difference goes back (R2).                                                                                                           |
| `AC-052` / docs explain hints, checks, retries and when a run stops                                                                                                                                                                                                                  | `page-extraction.md` **How a page is checked**; `outputs.md`; `verifiers.md`; `models-and-providers.md` failure sections; generated checks pages (R6)         | Supported. A user learns from the docs alone which checks may send an answer back, which comparisons are hints, that a hint difference never retries or fails a run, when it is listed, and that a run stops only on an unusable answer.         |
| `AC-053` / `next_cycle_inputs.md` records the hint rule                                                                                                                                                                                                                              | **User decisions that apply to later steps**, hint bullet (read in full)                                                                                      | Supported. It replaces the earlier send-back rule with the hint rule, keeps consistency checks and hard limits as what may send an answer back, and asks each later step to sort its comparisons the same way.                                   |
| `AC-001`, `AC-002`, `AC-003`, `AC-004`, `AC-005`, `AC-006`, `AC-007`, `AC-008`, `AC-009`, `AC-010`, `AC-011`, `AC-012`, `AC-013`, `AC-014`, `AC-015`, `AC-016`, `AC-017`, `AC-018`, `AC-020` / settings, estimates, reuse, the survey's verifier, page extraction without a verifier | Earlier pass's evidence; verification E13–E31; implementation review; R1; R4                                                                                  | Supported. R4 reran the guides' run examples on the current code: defaults make no verifier request, `verify=True` verifies the survey and every page, turning it on reruns, off again reuses, and the estimate figures in `verifiers.md` match. |
| `AC-021`, `AC-022`, `AC-023`, `AC-024`, `AC-025` / the five fixes                                                                                                                                                                                                                    | Earlier pass; code unchanged since (R3); E32–E42                                                                                                              | Supported.                                                                                                                                                                                                                                       |
| `AC-026` / mocked tests                                                                                                                                                                                                                                                              | R1 (211 passed); verification report                                                                                                                          | Supported.                                                                                                                                                                                                                                       |
| `AC-027`, `AC-028`, `AC-029` / CI, required checks, wheel on three systems, metadata check                                                                                                                                                                                           | Implementation review R17 (CI on `3648a0b`, `main`'s rules); E44, E60; R3                                                                                     | Supported. No CI run exists for `2b090b4`; it differs from `3648a0b` in docs, docstrings and records only, which R1, R2 and R6 cover locally.                                                                                                    |
| `AC-030` / description, classifiers, README                                                                                                                                                                                                                                          | `pyproject.toml` (unchanged since `b579737`); `README.md` lines 15–19 and 90–91                                                                               | Supported. The README's description of the optional verifiers and the review list is still accurate under the hint rule.                                                                                                                         |
| `AC-031` / release setup produces 0.2.0                                                                                                                                                                                                                                              | Implementation review R17; manifest `0.1.1`                                                                                                                   | Supported for release readiness; the release pull request follows merge.                                                                                                                                                                         |
| `AC-032` / a user can choose and read the verifiers from the docs alone                                                                                                                                                                                                              | `verifiers.md` (read in full at the changes); R4; R5                                                                                                          | Supported. The review-list table now covers checks in either step, the survey's two hints and the page's five hints.                                                                                                                             |
| `AC-033` / reference pages cover the new settings and fields                                                                                                                                                                                                                         | R6 (regeneration identical after formatting); `page-json.md` and `pdf-survey-json.md` list `hints`                                                            | Supported.                                                                                                                                                                                                                                       |
| `AC-035` / page file reference examples                                                                                                                                                                                                                                              | `reference/page-json.md` (`checks[].failures[]`, `issues[].details`, `item_ref` wording); `run-json.md` `steps[].pages`                                       | Supported. The `CheckFailure` docstring change keeps page extraction's own example and says the ref comes from the answer.                                                                                                                       |
| `AC-036` / the other wording                                                                                                                                                                                                                                                         | Earlier pass; the rework changed none of those passages except the verbose line in `command-line.md`, which now matches the page log line                     | Supported.                                                                                                                                                                                                                                       |
| `AC-037` / README and docs examples match 0.2.0                                                                                                                                                                                                                                      | R4 (estimate lines, `verify=True`, the extraction override, `load`, reruns); the documentation record's run of the README example                             | Supported for what can run offline. The README's quick start sends real requests and is covered by the same code paths.                                                                                                                          |
| `AC-038` / next-cycle inputs: later verifiers opt-in, remaining issues listed                                                                                                                                                                                                        | **Pushed to later steps** "Verifier per step" and the remaining items                                                                                         | Supported.                                                                                                                                                                                                                                       |
| `AC-041`, `AC-042` / the reorder                                                                                                                                                                                                                                                     | Implementation review R6, R7, R15; verification E1–E11; R3                                                                                                    | Supported.                                                                                                                                                                                                                                       |
| `AC-039` / accepted real runs with default settings                                                                                                                                                                                                                                  | G-2: 10 runs in `pydelity-output/real-hints/{anthropic,openai}/default/`; the user's acceptance, 2026-11-22                                                   | Supported (G-2 closed). The user chose not to rerun the GPF PDFs.                                                                                                                                                                                |
| `AC-040` / accepted real runs with both verifiers on                                                                                                                                                                                                                                 | G-2: 10 runs in `pydelity-output/real-hints/{anthropic,openai}/verify/`, every kind the AC names; the user's acceptance, 2026-11-22                           | Supported (G-2 closed).                                                                                                                                                                                                                          |

Retired `AC-019` and `AC-034` are history only.

Constraints across the deliverable: no shipped file names a development step,
date, role or cycle, and no stale send-back wording remains (R2); both
`PROMPT_VERSION`s and `PROBE_VERSION` are 1; no alias, fallback or optional
field was added for older files, and the docs say older output folders do not
carry over, which the design asks for, so the user style's compatibility rule is
met.

## Checks and Results

All from the repository root on `2b090b4`, 2026-11-22. Scratch scripts are in
this session's scratchpad (`fr2/`), not in the repo.

- **R1 — Suite and linters.**
  `.venv/bin/pytest -q --numprocesses auto -p no:cacheprovider` 211 passed;
  `.venv/bin/pytest -q --doctest-modules src -p no:cacheprovider` 28 passed, 1
  skipped; `ruff check scripts src tests` "All checks passed!";
  `ruff format --check scripts src tests` "89 files already formatted";
  `ty check scripts src tests` "All checks passed!";
  `interrogate scripts src tests` "RESULT: PASSED (minimum: 100.0%, actual:
  100.0%)". All exit 0, and `git status` afterward showed no change.
- **R2 — Wording.**
  `grep -rnE "DEV-[0-9]|AC-[0-9]|2026-|KGForEd|STANDARDS|Scoper|Architect|Developer|Tester|Documenter|step [1-6]\b|second model|reviews every page|text check|goes back for|leaving aside the text|other than the text comparison|may keep its reading|costing retries|sends none of|TEXT_CHECKS|compare_with_facts|SurveyComparisonName"`
  over `README.md`, `docs/src/content/docs`, `src/pydelity`, `examples`,
  `pyproject.toml` and `scripts/*.py`: no match. "match a hint" appears only
  where the docs and a docstring say no request asks for it. A British-spelling
  search finds one `cancelled` in the `pipeline/runner.py` module docstring,
  from page extraction (`ce66a4f`) on a line this cycle did not change, which
  the scope's non-goals leave as it is.
- **R3 — Code unchanged since the implementation review.**
  `git diff --stat 278264b HEAD -- src scripts tests examples pyproject.toml uv.lock .github`
  lists only `src/pydelity/review.py`; `fr2/nodoc.py`, which compares the two
  versions' syntax trees with docstrings removed, prints "same code".
- **R4 — The guides' examples against the stand-in** (`fr2/examples.py`, the
  repo's `MockProviders` with the 1965 scan's survey and page answers and a
  passing survey verdict; nothing sent to a provider):
  - before a survey: survey estimate `0.235352`/`2.530056`, 3 requests,
    `verifier` false; with `verify=True` `0.466448`/`5.455344`, 6 requests,
    `verifier` true, the "$0.47, at most $5.46" in `verifiers.md`;
  - after a survey: extraction `0.228808`/`4.814424`, 6 requests; with
    `advanced={"extraction": {"verify": True}}` `0.457560`/`10.420680`, 12
    requests, the "$0.46, at most $10.42" in `verifiers.md`;
  - default run `completed`: both pages `verification` `None`, the six checks in
    `checks`, the five hints in `hints` (no differences), no issue; ledger
    agents `(extraction, extractor)`, `(survey, surveyor)`; `load` returns both
    pages;
  - `verify=True` on a new folder `completed`: the survey's verdict passed, its
    `hints` holds `rotation_differs` and `page_number_differs`, both pages
    verified and passed; ledger adds `(survey, verifier)` and
    `(extraction, verifier)`;
  - `verify` on for the default folder: 6 new requests, both pages verified; off
    again: no request, both steps `reused`.
- **R5 — Guide text against the code.** The checks the guides list are `CHECKS`
  in `extracting/validators.py` (labels, content, languages, boxes, containers,
  captions) and C1–C7; the hints are `HINTS` in both steps. Each hint's
  description in `outputs.md` and `page-extraction.md` matches its function's
  docstring and message (`check_artifacts`, `check_form_fields`,
  `check_reading_order`, the text hints). What the guides and the FAQ say a page
  request carries matches `_page_text` and `extract_page`; the verifier's
  sections match `verify_page`; the keep rule matches `_kept_answer`; the review
  list matches `_page_issues` and `build_survey`; the stop conditions match
  `extract_pages`' `Raises` and the survey's failure section. The
  `CheckFailure.details` example `{"measured": 90, "profile": 0}` matches
  `surveying/validators.py`'s rotation hint.
- **R6 — Reference pages, Markdown and the docs site.**
  `.venv/bin/python scripts/generate_reference_docs.py` (11 pages), then
  `just lint-markdown` (outside the sandbox, which blocks uv's cache in
  `~/.cache`): afterward `git status` shows no change to any tracked file
  outside this report, which is CI's stale-reference check;
  `STANDARDS check passed.` (with this report reopened); markdownlint "Passed",
  exit 0. `pnpm run build` in `docs/` (outside the sandbox) "29 page(s) built",
  then `pnpm run check-links` "Checked local links and fragments in 29 HTML
  pages.", exit 0.
- **R7 — Existing real-run folders.** No run exists on the hint code: the newest
  folders are `pydelity-output/real-0.2.0/` (2026-11-21, `c0ed1e9`) and
  `pydelity-output/data/{gpf_math,gpf_reading,imnci}` (2026-11-21 and the early
  hours of 2026-11-22 UTC, before `0bfbfde`). Their page files lack `hints`, so
  none is evidence for `AC-039` or `AC-040` now, and a run on one of those
  folders makes its survey and pages again with the `damaged_output` warning. In
  the GPF runs' page files, the stored lines "123456789" and "x x x x x" are in
  text differences on `gpf_math` page indexes 10–38 and `gpf_reading` 12–23
  (page numbers 11–39 and 13–24), which is where the grade grids are. Offline
  estimates for those pages (`fr2/est.py`, `aestimate`, nothing sent), including
  each PDF's whole survey: Anthropic default about $14.62 (at most $129.41),
  with verifiers about $28.50 (at most $275.84); OpenAI default about $41.17,
  with verifiers about $80.94. The earlier fixture runs cost $4.77 and $8.10 on
  Anthropic and $8.16 and $10.69 on OpenAI.
- Not run: Python 3.14 locally, the wheel smoke test locally, zizmor, CI on
  `2b090b4`, and any real model. CI on `3648a0b` covered the first three on code
  that differs only in docstrings (R3); the merge pull request runs them again
  as required checks.

## Findings

**No material findings.**

## Questions, Limitations, and Later Dependencies

Gap at this pass, now closed:

- **G-2, `AC-039` and `AC-040`: no accepted real runs on the current code
  (closed 2026-11-22).** The scope requires the user to run the survey and page
  extraction with real Anthropic and OpenAI models on PDFs of their choice, once
  with default settings (`AC-039`) and once with both verifiers on (`AC-040`,
  covering at least one two-column right-to-left document, one Chinese or
  Japanese document, one tax or fillable form, one slide deck or image-heavy
  PDF, and CAPS), review the results and accept them, with every issue they
  raise resolved. Its assumptions add that these runs include the GPF reading
  and math PDFs, where the merged grade cells showed. The runs the user accepted
  on 2026-11-21 (G-1 below) ran before the hint rule, and the rework changed
  what every request says, what is retried and what the review list holds, so
  they no longer show the current behavior. They also carry the design's open
  risks: how real models respond to the hint wording and whether models give
  fewer artifact items so that `artifacts` issues grow.
  - The user's choice (2026-11-22): "i dont need to run the GPF tests". The ACs
    leave the PDFs to the user, so the scope's assumption about the GPF PDFs is
    not an acceptance requirement and this choice needs no scope change. Whether
    the grade cells now stay apart is then not shown by these runs. The smallest
    set that covers `AC-040`'s kinds is five of the earlier test PDFs: the
    Arabic Publication 1 (two-column right to left), the Japanese gazette, W-9
    page 1, slides 1–6 and CAPS, each on both providers. `AC-039` names no
    kinds; the same five with verifiers off is recommended, since that is where
    the hint rule shows most, and matches the 2026-11-21 runs for comparison.
    Offline estimates (`fr2/est_min.py`): Anthropic about $4.35 off and $8.43
    on, OpenAI about $9.27 off and $18.00 on; the earlier runs' actual spend was
    below their estimates.
  - Owner: the user. Consequence: this gate cannot pass, so the cycle cannot
    resume synchronization or reach sign-off, until the user reports the runs'
    outcome; an issue they raise goes to its owner first. The question is in
    `Active Work.BlockedOn`.
  - Next check, on re-review: record which PDFs, pages and providers ran, with
    and without verifiers, and the user's acceptance or issues. If the user
    shares the output folders, inspect each page's `hints` and review list
    (`artifacts` issues in particular), the survey verdicts and the reports as
    supporting evidence, compare them with the 2026-11-21 runs, and recheck that
    the assessed inputs above are unchanged.
  - The user's runs (2026-11-22, 13:48–14:25 UTC, after `2b090b4` at 13:36 UTC),
    inspected by Reviewer at the user's request as supporting evidence, not
    acceptance. The five PDFs above, with `-m anthropic:claude-opus-5-5` and
    `-m openai:gpt-6.2-astra`, `-np -y`, and `-vf` for the verified runs, into
    `pydelity-output/real-hints/{anthropic,openai}/{default,verify}/<pdf>/`.
    Scratch scripts `fr2/inspect.py` and inline comparisons:
    - All 20 runs `completed`, no error. Ledger spend: Anthropic $2.89 without
      verifiers and $4.98 with them, OpenAI $4.77 and $6.18 (total $18.82).
    - Defaults (`AC-001`, `AC-018`, `AC-020`): no `verifier` ledger line, every
      `verification` `null`. Verified runs: one survey verifier request and one
      page verifier request per page, every `verification` set.
    - Fewer answers sent back (`AC-044`): extractor requests for the 18 pages,
      against the 2026-11-21 runs: Anthropic 29 to 19 without verifiers and 30
      to 21 with them, OpenAI 30 to 18 and 30 to 18. Four pages still took a
      second answer (Anthropic, Arabic page 0 in both runs and slides pages 2
      and 4 with verifiers); hints cannot cause that (implementation review R13,
      R14), and every kept answer passes every check.
    - The Japanese gazette's `Signature1` widget, a 0.6 by 0.8 point box at the
      page's bottom-left corner: in all four 2026-11-21 runs the `form_fields`
      check had each model add a `signature` field item for it; now no model
      does, the difference is a `form_fields` review issue without a verifier,
      and both verifiers accepted the page. This is the hint rule working as the
      scope intends.
    - No `artifacts` difference in any run, and artifact items are as many as
      before except Anthropic's Japanese page (10 to 3 without a verifier, 8 to
      5 with), where every furniture line the survey found is still covered. The
      design's risk of more `artifacts` issues did not show.
    - Review lists without a verifier (`AC-048`, `AC-039`): Arabic 23 and 22
      (text differences from its broken stored text), Japanese 8 and 7 (its
      stored date in private-use characters, text the stored layer splits, and
      `Signature1`), slides 2 each (the footers the text layer holds twice), W-9
      1 each (`Sign Here`, drawn but not stored, which the models now give as
      heading text where the earlier runs gave it as a field prompt), CAPS 0.
      Each is a stored-data artifact, not a model error. With verifiers, all 10
      review lists are empty, and the differences stay in `hints`.
    - The survey's verifier (`AC-007` to `AC-013`, `AC-040`): 7 passed, 3
      corrections kept, all Anthropic: the slides' continuation note (named page
      5 for page 8) and its duplicated-footer pages (2, 3, 7 and 9, as
      `read_lines` showed in the earlier pass), and the W-9 exemption chart's
      region top, moved up to take in its header row. OpenAI passed all 5.
    - Page verifiers (`AC-046`, `AC-047`): 34 pages, 31 passed, 3 corrections
      kept: Anthropic's W-9 (a field prompt that is not printed, removed),
      Anthropic's CAPS page 0 (a strand cell made to span two rows), and
      OpenAI's Arabic page 1 (two tanwīn restored and `بشأن` changed back to
      `بشان`). The Arabic one is right: the stored text has `بشان`, `نظرةً` and
      `بأشخاصٍ`, and a 400 DPI render shows `بشان` without the hamza. The Arabic
      correction was kept with 12 text differences on the page, as `AC-047`
      allows. The other two are right too, by renders: the W-9's LLC entry space
      has no printed label, and the CAPS strand cell runs the table's full
      length through the header and body rows.
  - Text and boxes, checked at the user's request (2026-11-22). Scratch scripts
    `fr2/textcmp.py` (each page's text as words, CJK by character, NFKC and
    case-folded) and `fr2/boxes.py` (each text-layer word's center against the
    item boxes, 3 pt margin, displayed coordinates; it reproduces the earlier
    pass's figures for the 2026-11-21 runs):
    - Against the stored text where it is reliable (slides, CAPS and W-9): all
      four runs match word for word, apart from the slides' `bls` logo, the
      footers the text layer holds twice, and Anthropic's verified W-9, which
      gives the printed `Other (see instructions)` as the prompt of both its
      checkbox and its entry line.
    - Against the 2026-11-21 runs, same provider and settings: identical text on
      17 of 18 pages on Anthropic and 16 of 18 on OpenAI. Between each
      provider's two new runs, only the Arabic page 1 and, on OpenAI, the
      Japanese page differ.
    - The differences, settled against renders: Arabic page 1 prints `بشان`,
      `تفعل`, `لسبب` and `تكاليفك`. Anthropic's run without a verifier gives
      `بشأن` and `التكاليف` for two of them (and now has `فسيتعين` right, which
      its 2026-11-21 run had wrong); its verified run has all four right.
      OpenAI's runs give `بشأن` (without a verifier) and `نفعل` (both), and its
      verified run `لسرد`; some tanwīn and damma marks also differ. The Japanese
      masthead prints `明治二十五年`: OpenAI's run without a verifier gives
      `明治三十五年`, and, as on 2026-11-21, `第四十三号` for the decree number
      `第百四十三号`, which is now a `text_added` review issue. OpenAI's
      verified run and both Anthropic runs have both right.
    - None of the Arabic misreadings or the masthead date is on a review list or
      in `hints`: one changed word in a long line stays within the text hints'
      tolerance, and the earlier send-back rule missed the same kind of error
      (`فستعين`, `第四十三号` on 2026-11-21). They are model misreadings at the
      earlier runs' rate, not an effect of the hint rule.
    - Boxes, text-layer words outside every item box (new runs, against
      2026-11-21): slides, CAPS and Arabic 0 in all eight runs (Anthropic's
      verified Arabic had 8); W-9 Anthropic 0 (25) and 17 (13), OpenAI 178 (189)
      and 189 (189), whose field boxes cover the input area and not the printed
      label, as the user accepted on 2026-11-20; the Japanese page Anthropic 36
      (31) and 16 (26), OpenAI 6 (6) and 6 (6). Anthropic's 36 include the
      masthead date column, whose text is in the answer.
    - Not checked: the GPF grade grids, by the user's choice.
  - The user's acceptance (2026-11-22): "Accept them", for the runs on both
    providers with and without verifiers, after the inspection and the text and
    box comparisons above, raising no issue. With no issue open, G-2 is closed
    and `Active Work.BlockedOn` is cleared.

Non-material limitations, none of which prevents assessing the rest of this
gate:

- No CI run exists for `2b090b4`. The changes since CI's last run (`3648a0b`)
  are docs, `review.py` docstrings and records, checked locally by R1, R2 and
  R6.
- The README's Python quick start sends real requests and was not run here; R4
  ran the same functions against the stand-in, and the documentation record ran
  the README example against it.
- The documentation record's two observations (exit code `0`'s help text leaves
  out a paused run; a run stopped at the question lists `pages/` and `figures/`
  before they exist) are not documentation defects: the command-line guide's
  exit code table covers the pause, and no AC depends on either.
- `artifacts/next_cycle_inputs.md` **Loose ends** still names pull request 10 as
  the one to retitle `feat:`; the instruction holds for whichever pull request
  merges, as the earlier pass noted.

No later-role dependency, material gap or blocking question remains.

### Earlier pass (2026-11-21, on `c0ed1e9`), superseded

The earlier pass found no material finding and closed **G-1** (the same two ACs)
after the user ran 14 runs on each provider into
`pydelity-output/real-0.2.0/{anthropic,openai}/{default,verify}/<pdf>/` and
accepted them ("Accept them", for Anthropic and then OpenAI). Its main
observations, kept for comparison with the new runs: every run completed;
default runs made no verifier request; the survey's verifier ran on both
providers' output modes (3 Anthropic corrections kept, every OpenAI survey
passed), settling the design's `SurveyVerdict` risk; the verifiers changed text
materially three times in 44 pages, two right and one wrong; with verifiers off,
pages with unreliable stored text (Arabic, Japanese) listed their text
differences, as designed. Those runs predate the hint rule and the GPF runs, so
they no longer carry `AC-039` or `AC-040`. Its R1–R8 are superseded by R1–R7
above, except its R3 and R5 conclusions on the settings and estimates, which R4
reran on the current code.

## Progress and Conclusion

- Done: inputs and identities; every current AC and relevant technical criterion
  accounted for; the documentation pass read against the code; R1–R7; G-2's real
  runs on both providers, inspected and accepted.
- Reconciled on resumption: the earlier `COMPLETE` conclusion was reopened,
  because the scope gained `AC-043` to `AC-054` and retired `AC-019` and
  `AC-034`, and the source, tests, design and docs changed. Earlier evidence is
  kept only where R3 and R4 show its content unchanged.
- Freshness, rechecked immediately before this conclusion (2026-11-22): head
  `2b090b4`; the only uncommitted changes are this report and `STATE.md`; scope
  `2d921029f902`, design `a69221d00c35`, development plan `215cd7c4e02f`,
  verification report `2dac1da950f8`, implementation review `938622aee9ab`,
  documentation record `69eaad16c215`, context `09045f457b2d`; trees `src`
  `369f58ab7050`, `tests` `98ea84f67b1b`, `scripts` `cb966db01cbe`,
  `docs/src/content/docs` `1b0b9eb10dae`, `examples` `4cdd597a30eb`, `.github`
  `70836f8a13a9`: all as assessed. The development plan and the verification
  report (`FULL`) are `COMPLETE`, so the full Developer and Tester gates hold.
- **Passing (2026-11-22, on `2b090b4`).** No material finding; G-2 is closed by
  the user's accepted real runs on both providers; no later dependency, material
  gap, blocking question or outstanding obligation remains; `check` passes. This
  is recovery frame 1's `RerunThrough` boundary, so the frame is popped and the
  cycle resumes `SYNCHRONIZING` with `Handoff.Kind: RESUME`. Passing this gate
  is not cycle completion or sign-off.

Earlier conclusion of this pass (2026-11-22, on `2b090b4`): not passing, blocked
on G-2 until the real runs on the current code and the user's acceptance.

Plain-language summary: the final review passes, and the work goes back to
synchronization. The docs describe the hints change as the code behaves, and the
tests, docs build and package checks pass. Your new runs on Anthropic and
OpenAI, with and without verifiers, all completed, and you accepted them. They
show the change working: fewer answers sent back, no made-up signature field, no
more page-furniture issues, and text and boxes as good as before. The models
still misread a few Arabic and Japanese words, as they did before, and the
review list does not catch those. Synchronization and your sign-off are still to
come.

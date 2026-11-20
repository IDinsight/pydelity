<!-- STANDARDS
Artifact: REVIEW
Cycle: build-step-2-page-extraction-of-the-20261119T174118Z-0419318a
ReviewKind: IMPLEMENTATION
-->

# Review Report

`Cycle`: `build-step-2-page-extraction-of-the-20261119T174118Z-0419318a`
`ReviewKind`: `IMPLEMENTATION` `Status`: `BLOCKED` `User Style`: `NONE`

## Assessed Inputs and Scope

- Cycle mode `STANDARD`, completion policy `FULL_DELIVERABLE`, project mode
  `BROWNFIELD`. Recovery inactive at entry, no outstanding obligations, no
  blocker.
- Scope
  `.standards/docs/scope/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a.md`
  (blob `8f6dbf9b42`): current `AC-001` to `AC-064` except retired `AC-015`,
  `AC-023`, `AC-024`, `AC-062`.
- Design
  `.standards/docs/specs/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a.md`
  (blob `878aa2339b`): decisions 1–22 and the technical acceptance criteria.
- Context `.standards/CONTEXT.md` (blob `be80a93c12`).
- Development plan (blob `8e3382b0f7`, `COMPLETE`, DEV-001 to DEV-021 `DONE`).
  It differs from the blob `ee8450ca87` that the verification report names only
  in whitespace (`git diff -w --word-diff=porcelain 5ecbf9d 936003e` on the
  plan: no word changed).
- Verification report (blob `8e3761eebf`, `COMPLETE`, `Assessment Purpose:
  FULL`).
- Repository: branch `tz6/pipeline-step-2`, head `53e985e`, clean tree before
  this review. Baseline `c7582e7` (`main`, release 0.1.1, the merge base).
  Active change: `git diff c7582e7..53e985e` outside `.standards/`, `.claude/`,
  `artifacts/`, and the STANDARDS blocks in `AGENTS.md` and `CLAUDE.md`. Source,
  scripts, examples, docs and workflows are identical at `5ecbf9d` (Developer's
  last commit), `a0afbfa` (Tester's assessed head) and `53e985e`;
  `a0afbfa..53e985e` changes only `STATE.md` and the verification report.
- Blobs of the files the findings name: `surveying/probe.py` `8b4a56f63a`,
  `report/html.py` `84100a82cd`, `report/report.css` `c98dbfcd4c`,
  `costs/ledger.py` `d1a24a1864` (unchanged since `c7582e7`),
  `pipeline/runner.py` `c9835f0948`.
- Environment: macOS arm64, repo `.venv` (Python 3.13.9, `uv.lock`).
- Project references loaded: `NONE` (`.standards/project-references/reviewer/`
  does not exist). User style: none selected.
- Inspection scope: the whole active change, with the deepest reading of
  `src/pydelity/extracting/`, the runner, spend control and the ledger, the
  probe follow-ups, the report and the workflows. `artifacts/` and KGForEdGlobal
  were not reassessed; the design's port decisions were taken as given.
- Session: this conversation holds none of the authoring history. The authoring
  sessions' models are not visible; this review ran on Claude Opus 5.5. Four
  read-only helper agents inspected separate areas in parallel (rendering and
  text layer; spend control and ledger; runner, API, CLI and config; probe,
  report and workflows). Every finding below was reproduced or read in the code
  in this session before it was recorded; helper claims not rechecked are not
  findings.
- Severity bar (reassessed at the user's request, 2026-11-20, "major issues"
  only): a finding must, on input the release targets, make the delivered
  output wrong, lose money or fail a run, or break a function the acceptance
  review relies on. Confirmed behavior below that bar is recorded as withdrawn
  with its reason and kept under limitations.

## Contract and Evidence Assessment

"Tester" means the verification report's tests and checks, which this review
read and whose suite it reran; "Reviewer" means this review's own inspection
and diagnostics.

| Obligation / criterion | Assessed evidence | Current disposition |
| --- | --- | --- |
| AC-001, AC-002 | Tester tests; Reviewer helper ran `pages` edge cases (`""`, `"0"`, `"3-1"`, `"1,,2"`, `"1-"`, negatives, pages past the PDF in `run`, `extract`, `estimate`) | Supported |
| AC-003, AC-004 | Tester CLI and API tests; Reviewer helper ran pause, `overwrite` with pause, `extract()` without pause | Supported |
| AC-005, AC-059, AC-060, AC-061 | Tester tests; Reviewer read `extracting/prompts.py` (instructions last, extractor and verifier only); helper confirmed request contents and resolved models in ledger, pricing, estimate and fingerprints | Supported |
| AC-006 | Tester example-config test | Supported |
| AC-007, AC-008, AC-012, AC-014, AC-056 | Tester tests; Reviewer read `extraction.py` `_page_items`, `_item` and the `labels`, `content`, `captions`, `containers` checks | Supported |
| AC-009, AC-010, AC-011 | Tester rendering and reading-order tests; Reviewer read `check_reading_order`; Reviewer helper checked the mapping table for every `/Rotate` × profile rotation × offset CropBox (32 cases, error ≤ 1 grid unit, round trip ≤ 0.24 pt), the rotated W-9 pages against the original (identical grid boxes for every line), and about 930 page sizes against every provider limit and 300 DPI (none exceeded, zoom within 0.2% of the largest) | Code: supported. Model-dependent accuracy: permitted later dependency (user, `AC-054`) |
| AC-013 | Tester crop tests; Reviewer read `_write_page` (crops before the page file, atomic writes) | Supported; limitation L-2 |
| AC-016 | Tester tests; the facts the `form_fields` check enforces come from the probe | Finding F-002 |
| AC-017, AC-018, AC-019, AC-020 | Tester tests and inspection; Reviewer read `check_artifacts` (decision 22), `page_context`, both prompts (no document type, language or default direction) | Supported |
| AC-021, AC-022, AC-063, AC-064, AC-025 | Tester tests incl. negative controls; Reviewer read `agents.py`, `llm.py`, `_kept_answer`, `_page_issues`, the text comparison | Supported |
| AC-026 | Tester `run.json` and CLI tests | Supported |
| AC-027 | Tester API tests; Reviewer helper reproduced `load()` on a folder reused by another PDF | Supported; withdrawn F-007 |
| AC-028 | Tester ledger tests; Reviewer helper confirmed `step`, `page_index`, `agent` per request and per retry | Supported; limitation L-3 |
| AC-029 | Tester estimate tests; helper confirmed paused and reused-page cases | Supported |
| AC-030 | Tester concurrency and image-bound tests; helper confirmed check and reservation under one lock | Supported; limitation L-4; withdrawn F-006 |
| AC-031, AC-032, AC-033 | Tester tests; Reviewer helper ran fingerprint changes (effort, tokens, retries, model, instructions, profile) and non-changes (concurrency, timeouts, prices), failures and cancellation | Supported; limitations L-2, L-5 |
| AC-034 | Tester report test; Reviewer read `report/html.py` and `report.css` | Finding F-005; withdrawn F-004 |
| AC-035 | Tester probe tests | Finding F-002; withdrawn F-001 |
| AC-036, AC-039, AC-040, AC-041 | Tester tests | Supported |
| AC-037 | Tester tests; Reviewer read `_structure_quality` | Supported; limitation L-6 |
| AC-038 | Tester cycle test; Reviewer reproduced a dangling link | Supported; withdrawn F-003 |
| AC-042, AC-043 | Tester workflow runs and inspection; Reviewer confirmed `c63d891` exists and the `pyproject.toml` entries are gone; helper read both workflows | Supported |
| AC-044, AC-051, AC-053; README part of AC-049 | — | Permitted later dependency: Documenter, then final review |
| AC-045 | 175 tests pass (Reviewer rerun); no provider reached | Supported for the current code; the corrections need Tester evidence |
| AC-046, AC-047, AC-048 | CI run `44805308210` on `a0afbfa`: every job `success` (Reviewer read it with `gh`); source unchanged since | Supported |
| AC-049 (metadata), AC-050 | `pyproject.toml` description; release-please files unchanged since `c7582e7` | Supported |
| AC-052 | Tester regeneration check and CI staleness step | Supported |
| AC-054 | — | Permitted later dependency: the user's real runs before sign-off |

Technical acceptance criteria are assessed under the same IDs. Decisions 4, 5
and 11 hold: every PyMuPDF call of the step (open, render, crop, text, close)
goes through `PdfWorker`, and none runs on the event loop. The design's crop
rule says the box is mapped back to the page's unrotated coordinates; the code
passes displayed-page coordinates, which is what PyMuPDF's clip takes, and the
crops land on their boxes in every rotation case (wording only, L-9).

## Checks and Results

All from the repository root on `53e985e` unless stated.

- `.venv/bin/python -m pytest --numprocesses auto -q -p no:randomly`: 175
  passed (13.7 s).
- `.venv/bin/python -m pytest --doctest-modules src -q`: 27 passed, 1 skipped.
- `.venv/bin/ruff check scripts src tests`, `ruff format --check`, `ty check`:
  no problems.
- `node .standards/bin/check.mjs`: passed.
- `gh run view 44805308210 --repo IDinsight/pydelity`: head `a0afbfa`,
  conclusion `success`, all six jobs `success` (run outside the sandbox, whose
  proxy fails `gh`'s TLS check).
- Reproducers, each run against HEAD's `src` and, for regressions, against
  `c7582e7`'s `src` extracted with `git archive` to `$TMPDIR/rv/main` (scripts
  in `$TMPDIR/rv/` and `$TMPDIR/rev/`, outside the repository): inline widget
  (F-001), radio value against shown state (F-002) and the `form_fields` check
  on its facts, dangling outline link (F-003), one-line old ledger at unit level
  and end to end (F-006). Outputs are quoted in each finding.
- Read, not run: the report table and box markup and CSS (F-004, F-005); the
  helper measured both in a browser, and the code shows the cause.

## Findings

### F-001 — One inline widget drops every form field on the PDF

`Severity`: `P2` `Status`: `WITHDRAWN` `Owner`: `DEVELOPER` `FailureType`:
`IMPLEMENTATION`

- **Reference:** `src/pydelity/surveying/probe.py` (blob `8b4a56f63a`): the
  per-widget `try` around `page.load_widget(xref)` (about line 553) calls
  `_field_error` (line 488) in its `except`, and `_field_error` calls
  `document.xref_get_key(xref, key)` (about line 510). `AC-035`.
- **Failure case:** a page whose `/Annots` holds ordinary text fields and one
  widget written inline (object number 0). Reading it raises, `_field_error`
  raises again on `xref_get_key(0, ...)`, and the form fact is lost.
- **Evidence:** HEAD and `c7582e7` alike: `form_fields: None`, `probe_errors:
  [ProbeError(fact='form', message='ValueError: bad xref')]`.
- **Reassessment (withdrawn, 2026-11-20):** the behavior is confirmed but not
  material. Inline widgets are not conforming PDF (annotations must be indirect
  objects), the case is the same on `c7582e7`, and losing the form fact only
  removes hints and the `form_fields` check; the run completes and the models
  still read every field from the image. Kept as a limitation.

### F-002 — A radio button that shows off is read as checked when the group's value names another button

`Severity`: `P2` `Status`: `OPEN` `Owner`: `DEVELOPER` `FailureType`:
`IMPLEMENTATION`

- **Reference:** `src/pydelity/surveying/probe.py` `_button_state` (lines
  271–284). `AC-035`, `AC-016`, `AC-021`.
- **Failure case:** a radio group with `/V /B`, button A with `/AS /A`, button
  B with `/AS /Off`, as a filler leaves it when it sets the group's value
  without updating the appearances of a form that already had A selected. The
  page shows A on. The fallback to the group's value runs for each button
  without checking whether another button of the group shows on, so both are
  read as checked.
- **Impact:** the facts say two buttons of one radio group are checked, unlike
  the page and unlike `c7582e7`. Both are sent to the extraction model as
  `checked` hints, the `form_fields` check then rejects a correct reading and
  asks the model to change it within the check retries, and the verifier is
  told a correction must pass that check. So the pipeline spends retries
  pushing a correct reading toward an impossible one, and a page file can end
  with the wrong radio values, or keep the right ones with a false review
  issue. This regression came with the `AC-035` change; `AC-035` asks for the
  value fallback only when every button of the group is off.
- **Evidence:** HEAD: `[('choice','radio',True,'B'), ('choice','radio',True,'B')]`;
  rendered page: A filled `(0,0,0)`, B empty `(255,255,255)`. `c7582e7`:
  `[('choice','radio',True,'A'), ('choice','radio',False,'Off')]`.
  `check_form_fields` on HEAD's facts with the correct answer (A checked, B
  not): `the form field 'choice' is checked [True, True], but its field items
  say [False, True]`.
- **Smallest correction:** apply the group-value fallback only when no button
  of the group shows on. Tester adds the mixed case to the probe tests.

### F-003 — A dangling outline link now loses every bookmark

`Severity`: `P2` `Status`: `WITHDRAWN` `Owner`: `DEVELOPER` `FailureType`:
`IMPLEMENTATION`

- **Reference:** `src/pydelity/surveying/probe.py` `_cut_outline_cycle` (line
  344; `xref_get_key(holder, key)` about line 366). `AC-038`.
- **Failure case:** an outline entry whose `/Next` or `/First` names an object
  number past the cross-reference table; HEAD records `bookmarks: None` with a
  `ValueError: bad xref` probe error, where `c7582e7` read the bookmarks.
- **Reassessment (withdrawn, 2026-11-20):** confirmed but not material. It needs
  a damaged outline, the survey still runs, and only the bookmarks hint is lost,
  with a probe error naming the fact. Kept as a limitation.

### F-004 — The report moves body cells when a header cell spans into the body

`Severity`: `P2` `Status`: `WITHDRAWN` `Owner`: `DEVELOPER` `FailureType`:
`IMPLEMENTATION`

- **Reference:** `src/pydelity/report/html.py` (blob `84100a82cd`), lines
  629–636: rows before `header_rows` go in `<thead>`, the rest in `<tbody>`,
  and browsers end a `rowspan` at its row group. `AC-034`.
- **Failure case:** a header cell whose `row_span` reaches past `header_rows`;
  the next body row's cells shift one column left in the report.
- **Reassessment (withdrawn, 2026-11-20):** confirmed but not material. It
  needs an answer whose `header_rows` disagrees with its own spans, the page
  file holds the table correctly, and only the report's display of that table
  shifts. Kept as a limitation.

### F-005 — Item boxes on the page image take the item list's styles

`Severity`: `P2` `Status`: `OPEN` `Owner`: `DEVELOPER` `FailureType`:
`IMPLEMENTATION`

- **Reference:** `src/pydelity/report/html.py` line 504 writes boxes as
  `class="box item"`; `src/pydelity/report/report.css` (blob `c98dbfcd4c`)
  lines 209–216 style `.item` (the item list entries) with `padding-block:
  0.5rem` and `.item:target` with the opaque `--highlight` background. `AC-034`,
  `AC-009`, `AC-054`.
- **Failure case:** every report, every page. (1) Each item box gets 0.5rem
  padding top and bottom on an absolutely placed `border-box`, so a box shorter
  than about 18 px on screen is drawn at least 18 px tall from its top. On the
  page image, at most 50rem (800 px) wide, a Letter page's 10 pt line is about
  13 px, so headings, single lines, captions, page furniture and fields are
  drawn taller than the page file says and run into the next line. (2)
  `.item:target` has the same specificity as `.box:target` and comes later, so
  following a review issue's link to `#box-<id>` fills that box with an opaque
  color and hides the content the issue is about.
- **Impact:** the report is how the user checks the page files' boxes and
  review issues before accepting the release (`AC-054`). As drawn, small items'
  boxes look loose when the page file's boxes may be tight, and every
  item-level issue link covers the item it points at.
- **Evidence:** the CSS rules and markup above; the box style sets `height` in
  percent of the page (`_box_style`, `html.py` line 90). The helper measured
  computed styles in a browser: a 10.2 px page-number box drawn 18.0 px tall;
  targeted box background `rgb(255,244,194)` (light) and `rgb(74,63,10)` (dark).
- **Smallest correction:** give the page-image boxes a class the item list does
  not use, or scope the list styles to the list. Tester extends the report
  test.

### F-006 — A complete but invalid last ledger line is ignored, then crashes the run after it spends

`Severity`: `P2` `Status`: `WITHDRAWN` `Owner`: `DEVELOPER` `FailureType`:
`IMPLEMENTATION`

- **Reference:** `src/pydelity/costs/ledger.py` (blob `d1a24a1864`):
  `read_ledger` skips any damaged last line; `_drop_unfinished_line` removes it
  only when it lacks its line break. The new required `agent` and `page_index`
  fields make every 0.1.x line damaged (decision 19). `AC-030`.
- **Failure case:** a 0.1.x output folder whose `cost.jsonl` has exactly one
  line. End to end: `estimate spent_usd: 0` for a $5.00 old line, one request
  sent, then `OutputError ... line 1 is damaged, and it is not the last line`
  and `run.json status: running`.
- **Reassessment (withdrawn, 2026-11-20):** confirmed but not material. Only
  0.1.x output folders trigger it, the scope gives 0.1.x no compatibility, and
  the cost is one request before the run stops; every later run stops before
  any request, as the design's risk note expects for 0.1.x folders. Kept as a
  limitation; real runs for `AC-054` should use new output folders.

### F-007 — `load()` returns page files of another PDF that used the same output folder

`Severity`: `P2` `Status`: `WITHDRAWN` `Owner`: `ARCHITECT` `FailureType`:
`ARCHITECTURE`

- **Reference:** design, **Python API** (`load()` returns "every page file in
  `pages/`"); `src/pydelity/pipeline/runner.py` `_load_pages` (lines 518–556).
  `AC-027`.
- **Failure case:** a 4-page PDF and then a 2-page PDF run into one folder;
  `load()` returns the second PDF's pages 0–1 and the first PDF's pages 2–3.
- **Reassessment (withdrawn, 2026-11-20):** confirmed but not material. It needs
  a folder reused by a different, shorter PDF after the run warns that the
  folder holds another PDF's results; only the Python `load()` is affected, the
  extra pages carry their own `inputs.pdf_sha256` and page indexes past the
  PDF's page count, and the run's `run.json` and report are right. The design
  keeps old page files on purpose (narrowed selections). Kept as a limitation
  for the later steps that read page files.

## Questions, Limitations, and Later Dependencies

Later dependencies (permitted at this gate):

- `AC-044`, `AC-051`, `AC-053`, and the README part of `AC-049`: Documenter's
  guides, README and wording fixes, checked against 0.2.0's behavior at final
  review.
- `AC-054`, which also carries the model-dependent parts of `AC-009`, `AC-010`
  and `AC-011`: the user's real Anthropic and OpenAI runs on the named PDFs,
  reviewed and accepted before sign-off.

Limitations and observations that do not block this gate, with why:

- L-1: no real model run was made in this review; model-dependent behavior
  rests on `AC-054`.
- L-2: an interrupted `overwrite` run can leave an old page file naming a crop
  file the new answer overwrote, since crops are named by item position and
  written before the page file; a later run reuses that page file. It needs
  `overwrite`, an interruption between a page's crop writes and its page file,
  and a different figure at the same position. Not material: the window is short
  and the crop still shows the same page region in the usual case. The plan
  notes list it.
- L-3: page requests canceled in flight (another page failed, or the `max_cost`
  answer was no) get no ledger line though the provider may bill them. The
  design accepts this risk explicitly (Risks; Alternatives, "Letting in-flight
  pages finish"), as for timed-out requests in 0.1.x.
- L-4: a request's bound prices input at the plain input rate, while Anthropic
  bills cache writes at 1.25 times; with an answer at the output limit the
  recorded cost can exceed the bound by about $0.008 a request (helper: bound
  `0.673116`, recorded `0.681395`). The 4-characters-per-token rule the design
  chose undercounts non-Latin prompt text similarly. Not material: a few cents
  per request in flight, only when answers reach the output limit.
- L-5: temporary files left in `pages/` or `figures/` are removed only when a
  page is extracted; the provider image limits that size the page image are not
  in the page fingerprint (only `RENDERING_SETTINGS` is). Neither produces wrong
  output today.
- L-6: a structure walk cut short at its cap rates pages up to the last page it
  reached, so in a tree whose elements are out of page order an unreached page
  below that one counts as untagged. Needs more than 20,000 structure elements
  out of page order, and only lowers a hint.
- L-7: the page JPEG has no byte cap. The helper measured 3.7–6.1 MB for a
  Letter page of synthetic grain or noise at the chosen size and quality 90
  (fixtures peak at 1.04 MB); Anthropic's per-image byte limit is about 5 MB
  (not checked against its current documentation here). Not established on a
  realistic page.
- L-8: figure crops render at a fixed 200 DPI with no pixel cap, so a full-page
  figure on a very large page (36 x 48 in) takes about 0.8 GB while it renders,
  one at a time on the PyMuPDF worker. It completes.
- L-9: design wording under **Rendering and coordinates** (crop clip in
  unrotated coordinates) and the `TEXT_FLAGS` comment (text clipped to the media
  box; PyMuPDF clips to the CropBox) do not match the correct code.
- L-10: withdrawn findings F-001 (inline widget), F-003 (dangling outline link),
  F-004 (report table spans), F-006 (one-line 0.1.x ledger) and F-007 (`load()`
  on a folder reused by another PDF): confirmed behavior below this gate's bar;
  each finding states its input and reason. Worth fixing if their code is
  touched anyway.

No blocking user question.

## Progress and Conclusion

**Not passing.** Two `P2` findings are open, both owned by Developer
(`IMPLEMENTATION`): F-002 (radio facts) and F-005 (report boxes). No material
assessment gap remains for the current code: every current AC has a disposition
above, the extraction core, rendering, spend control, runner, API, CLI,
configuration, probe, report and workflows were inspected, and the suite,
doctests, lint and types pass.

History: the first conclusion (2026-11-20) held seven `P2` findings and routed
an `ARCHITECTURE` failure for F-007. At the user's request the findings were
reassessed against the "major issues" bar above the same day, before any role
acted on that route: F-001, F-003, F-004, F-006 and F-007 were withdrawn, and
the uncommitted route to `ARCHITECTING` was replaced by an `IMPLEMENTATION`
failure to `DEVELOPING` with `ResumeAt: REVIEWING_IMPLEMENTATION`.

On resume: compare the inputs above with the current ones; recheck F-002 and
F-005 against their failure cases (reproducers in `$TMPDIR/rv/` may be gone;
each finding states its input) and the affected boundaries (the probe on the
fixture PDFs and the `form_fields` check; the report's boxes, issue links and
item list); check Tester's new evidence for both; then apply the full gate.

Plain-language summary: the work cannot move on yet, but only two problems
stand in the way, both small fixes for the developer. First, when a form's
radio buttons were saved inconsistently, the survey now reports two options as
ticked where the page shows one, and page extraction then pushes the model to
agree, so the extracted form can come out wrong. Second, the HTML report draws
the boxes of short items, such as headings, single lines and page numbers,
taller than they are, and an issue's link covers the item it points at, which
would mislead your review of the real runs. Everything else checked held up:
reading pages, the checks and verifier, rotation, spending limits, resume and
failure handling. Five smaller problems are recorded but do not block. Not
checked here: real model runs, which you review before sign-off, and the
documentation, which comes later.

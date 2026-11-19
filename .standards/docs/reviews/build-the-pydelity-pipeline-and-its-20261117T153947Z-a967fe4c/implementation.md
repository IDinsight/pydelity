<!-- STANDARDS
Artifact: REVIEW
Cycle: build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c
ReviewKind: IMPLEMENTATION
-->

# Review Report

`Cycle`: `build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c`
`ReviewKind`: `IMPLEMENTATION` `Status`: `COMPLETE` `User Style`: `NONE`

## Assessed Inputs and Scope

- Cycle mode `STANDARD`, completion policy `FULL_DELIVERABLE`, recovery
  inactive, no outstanding obligations, `BlockedOn: NONE`
  (`.standards/STATE.md`).
- Contract (SHA-256 prefixes of the files at `b0ca0be`): scope
  `1c127ab4fa9a2c5e`, design `7e579b1ed3535e6e`, development plan
  `0478a22683d35a06` (`COMPLETE`, `AFTER_IMPLEMENTATION`,
  `Current Increment: NONE`), verification report `af7061899800eecb`
  (`COMPLETE`, `FULL`), context `.standards/CONTEXT.md` `aa4a553cf773451e`.
  Current at the final assessment (`2c8720c`): scope, design and context
  unchanged; development plan `4aa6bef88043e791` (`COMPLETE`); verification
  report `e8e654e6b3ccffcb` (`REVERIFY`, `COMPLETE`, `FULL`); `src` `cae826c`,
  `tests` `268e597` (see **Progress and Conclusion**).
- Current acceptance set (43): `AC-001`, `AC-002`, `AC-004` to `AC-011`,
  `AC-014`, `AC-015`, `AC-017` to `AC-047`. Retired, historical only: `AC-003`,
  `AC-012`, `AC-013`, `AC-016`.
- Comparison range: `main` (`bdd8488`, the merge base) to `tz6/pipeline` at
  `b0ca0be`, clean working tree, no untracked files. The branch also installs
  STANDARDS (`.standards/`, `.claude/`, `.agents/`), which is workflow tooling,
  not project work. Tree identities at `b0ca0be`: `src` `0bb160c`, `tests`
  `b0ca803`, `scripts` `19567bb`, `examples` `235e934`, `docs` `a8bfe22`,
  `.github` `4cc0d13`; blobs `pyproject.toml` `3cb2e48`, `uv.lock` `8b205c6`,
  `justfile` `ff59f1c`, `release-please-config.json` `e2af4b1`,
  `.release-please-manifest.json` `b985ff6`. `b0ca0be` changes only the
  verification report after Tester's assessed head `02b3ea1`.
- Environment: macOS arm64, Python 3.13.9 from the repo's `.venv` (built from
  `uv.lock`); `uv run` could not be used inside this session's sandbox (its
  cache lock is outside the writable area), so commands call `.venv/bin/python`
  directly.
- Project references loaded: `NONE` (`.standards/project-references/` does not
  exist). User style: none selected.
- Session: a fresh conversation started for this review; it holds none of the
  scope, design, implementation, test or documentation authoring history. Client
  metadata cannot certify freshness, and the models that produced the work are
  not recorded, so no model comparison is claimed.

## Contract and Evidence Assessment

"Tester" cites the verification report's formal evidence, rechecked against the
tests named there; "Reviewer" is this review's own inspection or diagnostic.

| Obligation / criterion                                               | Assessed evidence                                                                                                                                                     | Current disposition                                                     |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| AC-001 measured facts                                                | Tester: `test_probe.py` (9 scenarios). Reviewer: probe rules rechecked with built PDFs (rotation, crop box, repeated-line thresholds, labels, forms, structure)       | Supported (F-002 resolved; F-001, F-003 to F-005 withdrawn)             |
| AC-002 profile                                                       | Reviewer: `surveying/survey.py` `build_survey`, `_labels` (Python-owned `other`), schemas. Tester: `test_profile_owns_other...`                                       | Supported                                                               |
| AC-045 checks C1–C7, retry, last attempt                             | Reviewer: `validators.py`, `agents.py` (`ModelRetry`, `last_attempt`), `build_survey` reruns checks on the accepted answer. Tester: `test_validators.py`, retry tests | Supported                                                               |
| AC-046 facts as hints, disagreements listed                          | Reviewer: prompt ("Treat them as hints"), `compare_with_facts` runs once and never retries. Tester: `test_answers_that_differ...`                                     | Supported                                                               |
| AC-004 instructions and languages                                    | Reviewer: prompt sections, `_languages`, no setting skips a check                                                                                                     | Supported                                                               |
| AC-005 facts correct on the PDF kinds listed                         | Tester: fixture tests on Arabic, Japanese, W-9, CAPS, scans, tagged and untagged PDFs                                                                                 | Supported                                                               |
| AC-006 no document-type rules                                        | Reviewer: prompt, checks, schemas and enums read; checks use IDs, ranges and `langcodes` only. Tester: vocabulary test and grep                                       | Supported                                                               |
| AC-040 facts saved first                                             | Reviewer: `measure_facts` runs before `build_model` reads the key, the estimate and any question (`runner.py:691-735`). Tester: API and CLI cases                     | Supported (F-002 resolved)                                              |
| AC-007, AC-008, AC-009, AC-047 CLI and config                        | Reviewer: `cli.py`, `config/loading.py`, `config/schemas.py`, `examples/`. Tester: CLI and config tests, example-file test                                            | Supported                                                               |
| AC-010 import is silent                                              | Reviewer: `__init__.py`. Tester: audit-hook import test                                                                                                               | Supported (see the banner observation below)                            |
| AC-011 both providers                                                | Reviewer: `providers/factory.py`; diagnostic with both providers. Tester: parametrized upload and runner tests                                                        | Supported                                                               |
| AC-041 provider retries                                              | Reviewer: SDK clients built with `max_retries`; connection-error diagnostic. Tester: `test_ledger_model.py` counts                                                    | Supported                                                               |
| AC-042, AC-043, AC-044 Python API                                    | Reviewer: `api.py`, `utils/coroutines.py` (`run_sync` checks for a running loop first), `load_run`. Tester: API tests                                                 | Supported                                                               |
| AC-014 ledger and cost                                               | Reviewer: `LedgerModel._record`, `costs/ledger.py`, `_cost`. Tester: ledger and summary tests                                                                         | Supported                                                               |
| AC-015, AC-038, AC-039 spend controls                                | Reviewer: `_ask_before_spending`, `SpendGuard`, CLI `_ask`, `_fixed_decision`. Tester: CLI and budget tests                                                           | Supported                                                               |
| AC-037 provider rejection                                            | Reviewer: profiles hold provider-level data only; `ProviderError` mapping; rejection diagnostic. Tester: 400, 413 and fallback tests                                  | Supported                                                               |
| AC-017, AC-018 reuse and interruption                                | Reviewer: fingerprints, `write_text_atomic`, temp cleanup, damaged-file handling. Tester: runner and file tests                                                       | Supported                                                               |
| AC-019 review list and CLI summary                                   | Reviewer: `RunRecord.review`, `_log_summary`. Tester: review-summary test                                                                                             | Supported                                                               |
| AC-020 HTML report                                                   | Reviewer: `report/images.py`, escaping in `report/html.py`, boxes placed on the displayed page. Tester: `test_html.py`                                                | Supported                                                               |
| AC-021 mocked tests                                                  | Reviewer: suite run (104 passed); autouse guard; mock server routes. Tester: whole suite                                                                              | Supported                                                               |
| AC-022, AC-023, AC-024 CI, Windows, wheel                            | Reviewer: CI on `b0ca0be` all `SUCCESS`; gate and wheel jobs reviewed. Tester: CI runs and `just build`                                                               | Supported                                                               |
| AC-025 metadata and README                                           | Reviewer: `pyproject.toml` description and classifiers                                                                                                                | Metadata supported; README is a permitted later dependency (Documenter) |
| AC-026, AC-036 release                                               | Reviewer: `release.yml` and release-please path reviewed (readiness only; publishing follows sign-off). Tester: zizmor, release-please source                         | Supported for readiness                                                 |
| AC-027, AC-028, AC-029, AC-030, AC-032 docs site and reference pages | Reviewer: `docs.yml`, versioned build and link checker reviewed. Tester: `just docs-build`, scratch-clone versioned build, regeneration check                         | Supported (non-material observations below)                             |
| AC-031, AC-033, AC-034 docs pages and README examples                | No pages yet; design assigns them to Documenter                                                                                                                       | Permitted later dependency (Documenter)                                 |
| AC-035 user review of real runs                                      | Tester: the user's acceptance recorded 2026-11-18, after the last change to `src/` (`f8c816b`); plan notes record the user's real runs                                | Supported by the user's acceptance                                      |

## Checks and Results

- `.venv/bin/python -m pytest -q --numprocesses auto` at the repo root on
  `b0ca0be`, 2026-11-18: 104 passed in 7.84 s (exit 0). Reviewer diagnostic, not
  Tester evidence.
- `node .standards/bin/check.mjs`: "STANDARDS check passed." before review work.
- `gh pr view 3 --repo IDinsight/pydelity` (read-only, run outside the sandbox
  because the sandbox blocked TLS certificate checks): head `b0ca0be`, every
  check `SUCCESS` ("Lint and test (Python 3.13)", "Test (Python 3.14)", "Wheel
  install" on macOS, Ubuntu and Windows, "Lint and test", "Build the docs",
  "TruffleHog secret scan"); "Publish to GitHub Pages" `SKIPPED` as designed for
  a pull request. The draft pull request is closed; it existed only for CI.
- Diagnostic `$TMPDIR/rev/conn.py` (scratch, not committed): `pydelity.run` on
  `bls_navigating_slides.pdf` with both base URLs at a closed loopback port,
  dummy keys and `provider_retries: 0`, for `anthropic:claude-opus-5-5` and
  `openai:gpt-5`. Each raised `ProviderError` (`status_code` null, `temporary`
  true, `__cause__` `ModelConnectionError`) whose message gives the request and
  the earlier upload error; an `upload_fallback` warning was issued and
  `run.json` recorded `failed`. Matches design decision 4 and **Providers and
  models** for connection errors, which no committed test exercises.
- Diagnostic `$TMPDIR/rev/reject.py`: the stand-in server
  (`tests/fixtures/mock_providers.py`) accepts the upload and rejects every
  model request with HTTP 400. `run.json` then holds `status: failed` and
  `steps[0].pdf_transport: null`, though `uploads.json` records the upload and
  the rejected request referenced it (see F-001, withdrawn).
- Second pass, Reviewer diagnostics: a checked checkbox with a normal appearance
  and no down appearance (`$TMPDIR/rev/probe/n_only.pdf`) reads
  `('agree', 'Yes', True)` with no probe error; the CLI on the malformed
  page-label PDF prints a `TypeError` traceback and exits 1 without writing
  `pdf_facts.json` (F-002).
- Probe rules (helper agent, read-only, scripts in
  `/private/tmp/claude-501/probe_review/`; Reviewer read and reran the scripts
  behind F-002 to F-005 and got the results quoted there). The helper also
  reported as correct: angles and boxes on pages with `/Rotate` 0, 90, 180 and
  270 and with a crop box offset from the media box (text and widgets); sideways
  text on a rotation-0 page giving 90; the 20-character, 80% confidence rule;
  vertical lines counted in `vertical_share`; the 70% direction rule;
  repeated-line thresholds (2 pages for 2-3-page PDFs, 3 and 5% otherwise),
  ordering, band and normalization; labels `Page 12`, `A-iv` and `第5`;
  unresolved bookmarks with `page_index` null; checkbox and radio on-states;
  AcroForm and XFA flags; RoleMap mapping and cycle safety; documents closed;
  under 0.2 s per fixture. Reviewer relies on these as supporting diagnostics.
- CI, release and docs tooling (helper agent, read-only, scratch clone with
  local tags, never pushed; Reviewer read `docs.yml` and the `ci.yml` diff check
  directly and the CI results above). Reported as correct: the "Lint and test"
  gate fails on any failed, skipped or cancelled needed job; the 3.14 job runs
  CPython 3.14.4; the wheel jobs install the built wheel into a fresh venv and
  check the installed copy; `release-please.yml` authenticates with a personal
  token, so its GitHub release starts `release.yml`; `release.yml` checks the
  tag against the version, builds with `twine check --strict`, gives
  `id-token: write` only to `publish` in the `pypi` environment and passes
  `dist/` as an artifact; release-please 17.6.0 falls back to the manifest
  version and bumps `0.0.1` to `0.1.0` for a `feat:` commit, and bumps the
  `uv.lock` entry; the versioned docs build (latest at the root, releases under
  `/v/<version>/`, `versions.json`, selector, prerelease and pre-0.1.0 tags left
  out, a tag whose `pyproject.toml` version differs fails); the link checker
  catches missing pages and fragments; deploy runs only on a push with
  `v<version>` present; Dependabot covers `/docs`; reference pages regenerate
  byte-identically. No material defect was established in this area (see the
  observations below).
- Reviewer measured structure density on the committed fixtures with
  `probe_pdf`: `irs_w9_instructions.pdf` 704 elements on 7 pages,
  `irs_form_w9.pdf` 708 on 6, `irs_pub1_arabic.pdf` 448 on 2,
  `irs_pub1_chinese_simplified.pdf` 105 on 2; all `good`, none truncated.

## Findings

### F-001 — `run.json` says no request carried the PDF when a request did

`Severity`: `P2` `Status`: `WITHDRAWN` `Owner`: `DEVELOPER` `FailureType`:
`IMPLEMENTATION`

- **Reassessment (2026-11-18, second pass):** withdrawn as not material. The
  value is wrong only on a failed step, where the same run already records how
  the PDF went: the `ProviderError` message says the request carried the PDF and
  gives any earlier upload error, and a fallback adds an `upload_fallback`
  warning to `run.json`. Nothing reads `pdf_transport` of a failed step, so the
  user loses no information. Kept as an observation for Developer.
- **Reference:** `src/pydelity/pipeline/runner.py:736` (`run.transport` is set
  only from `run_survey`'s return value) and `:594` (written to the step's
  `pdf_transport`), tree `src` `0bb160c`. Contract: design **`run.json`**
  (`pdf_transport` is `upload` | `request`, null when no PDF was sent) and the
  generated reference `docs/src/content/docs/reference/run-json.md:87` ("`None`
  when no request carried it"). Related ACs: `AC-037`, `AC-019`.
- **Failure case:** the PDF is uploaded (or the fallback sends it inside the
  request) and the provider then rejects the request, as in a PDF rejected for
  its size or page count (`AC-037`), or a request fails after the provider
  retries. `run_survey` raises, so `run.transport` stays `None` and `run.json`
  records `pdf_transport: null` for a step whose requests carried the PDF.
- **Impact:** in exactly the runs a user inspects to learn why a provider
  refused their PDF, `run.json` misstates how the PDF was sent and contradicts
  its documented contract; a reader cannot tell an upload rejection path from an
  in-request one from `run.json`.
- **Evidence:** diagnostic `$TMPDIR/rev/reject.py` above: routes `upload` then
  `model` (400), `uploads.json` written, `run.json` `pdf_transport` `None`. No
  committed test asserts `pdf_transport` on a failed run.
- **Smallest correction:** record the step's transport as soon as the PDF is
  attached to a request (updating it after a fallback or re-upload), so failed
  and stopped steps report it; leave it null only when no request carried the
  PDF (for example, a stop before any request).

### F-002 — A malformed `/PageLabels` tree makes every run on the PDF fail

`Severity`: `P2` `Status`: `RESOLVED` `Owner`: `DEVELOPER` `FailureType`:
`IMPLEMENTATION`

- **Reassessment (2026-11-18, on resumption at `2c8720c`):** resolved. Fix
  `e372d91` makes `_page_label` treat any error from `Page.get_label()` as no
  label and adds `_has_page_labels`, which does the same for
  `Document.get_page_labels()`; the page's printed number then comes from its
  text. Reviewer reran the original failure case: `probe_pdf` on
  `$TMPDIR/rev/probe/duplabel.pdf` returns facts with no probe error, and
  `pydelity.measure` writes `pdf_facts.json` with no warning. Boundary check:
  the 9 committed fixture PDFs give facts identical to the probe at `b0ca0be`
  (old module loaded from `git show b0ca0be:...`), so PDFs whose labels read
  normally are unaffected. Tester's new
  `test_a_damaged_page_label_tree_counts_as_no_labels` observes the fix (numbers
  from the text, offset 12, no probe error) and, by Tester's negative control,
  fails on the old code. The broad `except Exception` wraps only the two PyMuPDF
  label calls, matching how `_read_fact` guards the other facts.
- **Reference:** `src/pydelity/surveying/probe.py:794-797` (`_page_label`
  catches only `IndexError`, `RuntimeError` and `ValueError`), reached from
  `probe_pdf` at `:1323` via `_page` at `:764`; tree `src` `0bb160c`. Contract:
  `_page_label`'s own docstring ("treating a failure as no label"), design
  **Technical Acceptance Criteria** (probe failures on malformed PDFs "never
  fail the run"), scope `AC-001` and the goal of surveying (almost) any PDF.
- **Failure case:** a PDF whose page-label number tree lists one start page
  twice, `/PageLabels <</Nums [0 <</S/D>> 0 <</S/r>>]>>`. PyMuPDF's
  `Page.get_label()` sorts the entries and raises
  `TypeError: '<' not supported between instances of 'PdfObj' and 'PdfObj'`. The
  error escapes `probe_pdf`, so `measure`, `run` and the CLI fail before any
  facts are saved.
- **Impact:** a readable PDF with a damaged page-label tree cannot be surveyed
  at all, and no `pdf_facts.json` is written (`AC-040`). No setting avoids it,
  so the user has no workaround. Malformed number trees are rare, but the
  failure is total, and the probe's own contract is to degrade, not stop.
- **Evidence:** reproducer `/private/tmp/claude-501/probe_review/duplabel.py`
  (written by a helper agent, read and rerun by Reviewer): traceback ends in
  `probe.py:795` with the `TypeError` above. Second pass, the CLI on the same
  PDF: `pydelity duplabel.pdf -d cli_out --yes` printed the traceback and exited
  1; the folder held `run.json` (`failed`, `TypeError: '<' not supported ...`)
  and the report, but no `pdf_facts.json`.
- **Smallest correction:** treat any error from reading a page's label as "no
  label" (falling back to the page text, as for a page without a label number),
  so a malformed label tree never stops the probe. A test with such a PDF is
  Tester's.

### F-003 — One appearance-less checked checkbox erases every form field

`Severity`: `P2` `Status`: `WITHDRAWN` `Owner`: `DEVELOPER` `FailureType`:
`IMPLEMENTATION`

- **Reassessment (2026-11-18, second pass):** withdrawn as not material, and the
  failure case below overstated how often it occurs. PyMuPDF's `on_state()`
  returns the first non-`Off` normal appearance before it reaches the missing
  entry, so the error needs a checked checkbox with no normal (`/AP /N`)
  appearance at all; a checked checkbox with a normal appearance and no down
  (`/D`) appearance reads correctly (Reviewer diagnostic
  `$TMPDIR/rev/probe/n_only.pdf`: `('agree', 'Yes', True)`, no probe error).
  Such checkboxes are rare, the run continues, and the form fact is reported as
  unreadable rather than wrong. Kept as an observation for Developer.
- **Reference:** `src/pydelity/surveying/probe.py:436-440` (`widget.on_state()`
  for any checkbox or radio value other than `""` or `Off`); tree `src`
  `0bb160c`. Contract: scope `AC-001` (form fields with their values, including
  checkboxes) and `AC-005`; design **`pdf_facts.json`** (`null` means the fact
  "could not be read").
- **Failure case:** a filled form whose checkbox has `/V /Yes` and `/AS /Yes`
  but no `/AP` appearance dictionary, as forms filled with
  `NeedAppearances true` often have. PyMuPDF's `Widget.on_state()` iterates a
  `None` entry of `button_states()` and raises `TypeError`, which the form
  reader turns into `form: null`, `form_fields: null` and a `probe_errors` item.
- **Impact:** the whole form fact is lost for the PDF, every other field
  included, although its values are readable; the survey and the report then say
  the form could not be read.
- **Evidence:** `/private/tmp/claude-501/probe_review/noap.py` builds the PDF;
  Reviewer's `probe_pdf` run on it gives
  `form_fields None form None errors [ProbeError(fact='form', message="TypeError: 'NoneType' object is not iterable")]`.
- **Smallest correction:** read a checkbox or radio button's checked state
  without failing when it has no appearance states (for example, treat a value
  other than `Off` as checked when no on-state can be read), and keep one bad
  widget from discarding the other fields.

### F-004 — Letter-style page labels are read as roman numerals

`Severity`: `P2` `Status`: `WITHDRAWN` `Owner`: `DEVELOPER` `FailureType`:
`IMPLEMENTATION`

- **Reassessment (2026-11-18, second pass):** withdrawn as not material. Pure
  letter-style page labels are uncommon, the design (`AC-046`) has the profile
  keep the model's own reading of the page numbers, so a wrong hint does not
  reach the profile, and the only visible effect is a `page_number_differs`
  issue the user can dismiss on review. Kept as an observation for Developer.
- **Reference:** `src/pydelity/surveying/probe.py:494-528` (the label's ending
  is parsed as text) and the roman pattern near `:126`; tree `src` `0bb160c`.
  Contract: scope `AC-001` (printed page numbers with their offset), design
  **Technical Acceptance Criteria** ("the number at the end of the page's
  label"), and `AC-046` (review issues for pages whose number differs).
- **Failure case:** page labels in the PDF's uppercase or lowercase letter style
  (`/S /A` or `/S /a`): pages labelled `A`, `B`, `C`, `D` (numbers 1 to 4) and
  `c` (number 3). The probe records `C` as roman 100, `D` as 500 and `c` as 100,
  `A` and `B` as style `label` with no value, and builds `page_numbering` ranges
  with offsets 94, 493 and 89.
- **Impact:** wrong measured printed numbers and page-numbering ranges in
  `pdf_facts.json` and `pdf_survey.json`, sent to the model as hints, and a
  false `page_number_differs` review issue on each such page whenever the model
  reads the page correctly.
- **Evidence:** `/private/tmp/claude-501/probe_review/labels.py`, rerun by
  Reviewer: `6 ... style='roman' text='C' value=100`,
  `7 ... text='D' value=500`, `11 ... text='c' value=100`, and the three ranges
  above.
- **Smallest correction:** use the label range's numbering style, which
  `Document.get_page_labels()` already returns, to read the number (letters as
  letters, roman as roman, decimal as decimal), rather than guessing the style
  from the label's text. If recording a letter-style number needs a change to
  the facts schema's `style` values, route that decision to Architect.

### F-005 — Structure-tag quality is misrated for valid tagged PDFs

`Severity`: `P2` `Status`: `WITHDRAWN` `Owner`: `DEVELOPER` `FailureType`:
`IMPLEMENTATION`

- **Reassessment (2026-11-18, second pass):** withdrawn as not material for this
  cycle. No check, comparison or profile field uses structure quality; it is one
  hint line in the prompt and a stored fact, and a capped walk is already marked
  `truncated: true`. It matters when a later step decides whether to trust the
  tags, so the page-extraction cycle's design should settle how to rate a
  truncated walk and resolve indirect `/K` arrays. Kept as an observation.
- **Reference:** `src/pydelity/surveying/probe.py:474-475` and `:1245-1250`
  (`_kids` and `_visit_object` take an indirect `/K` for one element) and
  `:1079`, `:1251-1253` with `STRUCTURE_ELEMENT_CAP = 20_000` at `:86` (quality
  rated from a truncated depth-first walk); tree `src` `0bb160c`. Contract:
  scope `AC-001` and `AC-005` (structure tags and their quality), design
  **Technical Acceptance Criteria** (walk `StructTreeRoot`, `good` when tagged
  pages cover at least 90% of pages with text).
- **Failure cases:** (a) a structure element whose `/K` is an indirect reference
  to an array of kids, which the PDF specification allows: a 10-page PDF tagged
  on every page reports `element_count=1`, `pages_with_tagged_content=0`,
  `quality='poor'`, while the same tree with a direct array reports 21 elements,
  10 pages and `good`. (b) a fully tagged long PDF: 300 pages with 100 elements
  each reports `truncated=True`, `pages_with_tagged_content=200`,
  `quality='partial'`. The committed IRS fixtures run 52 to 224 elements per
  page, so ordinary tagged publications of a few hundred pages reach the cap.
- **Impact:** a false structure-quality fact for well-tagged PDFs, in the facts
  summary sent to the model and in the stored facts that later steps will read
  to decide whether to trust the tags.
- **Evidence:** `/private/tmp/claude-501/probe_review/structtree.py` and
  `bigstruct.py`, rerun by Reviewer with the results above; fixture densities
  measured by Reviewer (`irs_w9_instructions.pdf` 704 elements on 7 pages,
  `irs_pub1_arabic.pdf` 448 on 2).
- **Smallest correction:** resolve an indirect `/K` (and an indirect
  `StructTreeRoot` `/K`) to its object before walking it, and stop a walk that
  hits the cap from rating coverage as if unvisited pages were untagged (for
  example, by walking enough of the tree to cover every page, or by rating
  coverage only over what was walked). If the rating rule for a truncated walk
  needs a design decision, route it to Architect.

## Questions, Limitations, and Later Dependencies

- Later dependencies (permitted at this gate), owner Documenter, under the same
  ACs: `AC-025` (README text), `AC-031`, `AC-033`, `AC-034`. Required evidence:
  the docs pages and README, with each command and example checked against the
  release's behavior. The design also leaves to Documenter the PyMuPDF AGPL
  note, how long providers keep uploaded PDFs, reading `rotation_differs` and
  `page_number_differs` issues, and the sync and async forms in Jupyter.
- The F-002 correction changes behavior only for PDFs whose page-label tree
  makes PyMuPDF raise, which could not be surveyed at all before, and the
  committed fixtures' facts are unchanged, so the user's acceptance of real runs
  (`AC-035`) still applies to the corrected code.
- CI has not run on `e372d91` or `2c8720c` (the draft pull request is closed).
  Tester reused the CI evidence for `AC-022` to `AC-024` with a stated reason;
  Reviewer agrees: the change is platform-independent exception handling in one
  Python module, with no change to packaging, dependencies or workflows, and the
  local suite, doctests and build pass. Not material to this gate.
- Non-material observations (no correction required by this gate; owners may
  take them up):
  - The Python API leaves PydanticAI's first-run banner on, so the first `run()`
    in a process prints it to stderr (the CLI turns it off). `AC-010` covers
    import only. `PYDANTIC_AI_NO_BANNER=1` or
    `pydantic_ai.BANNER_ENABLED = False` turns it off; worth a docs mention.
  - `costs/pricing.py` `_config_price` uses `or`, so a cache price set to `0` in
    `advanced.models` is priced as the input price; both supported providers
    charge for cache reads and writes, so the ledger can only overstate.
  - `ci.yml` checks generated reference pages with `git diff --exit-code`, which
    does not catch a newly generated page left untracked; this is the design's
    stated mechanism, and every current page is committed.
  - `docs.yml`: the comment "a published build never reuses files another run
    wrote" is not true of the pnpm store cache that `withastro/action` restores
    (the design requires no caches only for `release.yml`); the plan step runs
    the runner's own `node` and `python3` and hides the `node` error with
    `2>/dev/null` (the intended signal for "no release tag"), outside the pinned
    Node 24.22.3.
  - Probe edge cases with low impact: an outline whose `/Next` links form a
    cycle reads as no bookmarks rather than unreadable; tagged pages without
    text count toward structure coverage; a radio group whose kids are all
    `/AS /Off` with `/V` set reads unchecked (PyMuPDF's `field_value`).
  - The withdrawn F-001, F-003, F-004 and F-005 describe real but minor
    behavior, kept above with their reproducers for Developer or a later cycle.
  - By the user's approved CLI deviation (no `--quiet`, progress only with
    `--verbose`), the facts summary is logged at INFO and shown by the CLI only
    with `--verbose`; `AC-040`'s logging is met at INFO.
- Limitations: Windows behavior rests on CI's wheel job (Ctrl+C at a question on
  Windows was not exercised); publishing, the Pages deploy and PyPI's Trusted
  Publisher settings are untestable before sign-off by design; the exact
  release-please patch release bundled in `release-please-action@v5.0.0` was not
  confirmed beyond 17.6.0 source. Two helper agents ran the probe and the
  CI/release/docs inspections; every defect they reported was reproduced by
  Reviewer before being recorded, and their other results are supporting
  diagnostics. None of these limits the findings above or would change this
  gate's outcome.
- No blocking user question. `Active Work.BlockedOn` stays `NONE`.

## Progress and Conclusion

- Inspected: protocol, state, scope, design, development plan notes,
  verification report and context; every runtime module of `src/pydelity` (the
  probe through a helper and Reviewer reruns); tests behind the verification
  report's evidence; `examples/`; CI, release, docs workflows and scripts
  (through a helper, with direct reads of `docs.yml` and `ci.yml`); CI results
  for `b0ca0be`. Test suite: 104 passed.
- Second pass (2026-11-18, at the user's request to keep only major issues):
  each finding was rechecked for how often its trigger occurs and what it
  breaks. F-001, F-003, F-004 and F-005 are withdrawn as not material (reasons
  in each finding); for F-003 the first pass overstated how often the trigger
  occurs. F-002 stays open: it is the only one that stops a run, with no
  workaround. Inputs are unchanged (`b0ca0be`, clean tree apart from this report
  and `STATE.md`).
- After the second pass, F-002 was routed to Developer (recovery frame 1),
  corrected in `e372d91`, covered by Tester's test in `2c8720c` and reverified
  (verification report `REVERIFY`, `COMPLETE`, `FULL`); the frame closed and the
  review resumed (`Handoff.Kind: RESUME`).
- Resumption, 2026-11-18, at `2c8720c` (clean tree): changed inputs since
  `b0ca0be` are `src/pydelity/surveying/probe.py` (tree `src` `cae826c`),
  `tests/pydelity/surveying/test_probe.py` (tree `tests` `268e597`), the
  development plan (`4aa6bef88043e791`, `COMPLETE`), the verification report
  (`e8e654e6b3ccffcb`), this report and `STATE.md`. Scope, design, context,
  every other source file, scripts, workflows, docs and dependencies are
  unchanged, so every other conclusion above still applies. Reviewer reran
  `.venv/bin/python -m pytest -q --numprocesses auto` (105 passed) and
  `pytest -q --doctest-modules src` (17 passed, 1 skipped), and rechecked F-002
  as recorded in the finding. The Developer and Tester full gates hold for the
  current implementation.
- Gate: **passes.** No material finding is open: F-002 is resolved, and F-001,
  F-003, F-004 and F-005 are withdrawn. Every current AC and relevant technical
  criterion has supporting evidence, except `AC-025` (README), `AC-031`,
  `AC-033` and `AC-034`, which remain permitted later dependencies for
  Documenter with the evidence named above. No blocking question or review-owned
  obligation remains. Passing this gate does not finish the cycle:
  documentation, final review and synchronization follow (`FULL_DELIVERABLE`).
- Plain-language summary: the implementation is ready for documentation. The one
  major problem, a crash on PDFs with damaged page-numbering data, is fixed and
  tested, and nothing else changed. The survey, settings, spend controls,
  resume, the report, CI and the release path all check out, and the tests pass.
  Still to come: the README and the docs pages, then a final review of the whole
  deliverable. Real publishing to PyPI and GitHub Pages can only be checked
  after sign-off.

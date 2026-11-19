<!-- STANDARDS
Artifact: REVIEW
Cycle: build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c
ReviewKind: FINAL_DELIVERABLE
-->

# Review Report

`Cycle`: `build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c`
`ReviewKind`: `FINAL_DELIVERABLE` `Status`: `COMPLETE` `User Style`: `NONE`

## Assessed Inputs and Scope

- Cycle mode `STANDARD`, completion policy `FULL_DELIVERABLE`, recovery
  inactive, no outstanding obligations, `BlockedOn: NONE`; entered by `FORWARD`
  from `DOCUMENTING` (`.standards/STATE.md`).
- Contract and owner records (SHA-256 prefixes at HEAD `ae81cb5`): scope
  `1c127ab4fa9a2c5e`, design `7e579b1ed3535e6e`, development plan
  `4aa6bef88043e791` (`COMPLETE`), verification report `e8e654e6b3ccffcb`
  (`REVERIFY`, `COMPLETE`, `FULL`), implementation review `3fd035240dc9ad4e`
  (`COMPLETE`), context `.standards/CONTEXT.md` `aa4a553cf773451e`,
  documentation record `2095612e0b613520` (`COMPLETE`). The first six match the
  identities the implementation review and the documentation record assessed.
- Current acceptance set (43): `AC-001`, `AC-002`, `AC-004` to `AC-011`,
  `AC-014`, `AC-015`, `AC-017` to `AC-047`. Retired, historical only: `AC-003`,
  `AC-012`, `AC-013`, `AC-016`.
- Comparison range: `main` (`bdd8488`, merge base) to `tz6/pipeline` at
  `ae81cb5`, clean tree apart from this report. Since the implementation
  review's last assessed head (`2c8720c`), `9273074` changed only the review
  report and `STATE.md`, and `ae81cb5` changed only documentation: `README.md`,
  13 prose pages and 2 new pages under `docs/src/content/docs/` (outside
  `reference/`), `docs/astro.config.mjs` (sidebar and the `PageTitle`
  component), the new `docs/src/components/PageTitle.astro`, the documentation
  record and `STATE.md`.
- Tree and blob identities at `ae81cb5`, unchanged since `2c8720c` unless noted:
  `src` `cae826c`, `tests` `268e597`, `examples` `235e934`, `scripts` `19567bb`,
  `.github` `4cc0d13`, `docs/src/content/docs/reference` `8762d28`;
  `pyproject.toml` `3cb2e48`, `uv.lock` `8b205c6`, `justfile` `ff59f1c`,
  `.template.env` `56e4725`, `docs/package.json` `75d2284`. Changed: `README.md`
  `6d56470`, `docs/astro.config.mjs` `73e9712`, `docs` tree `6c0e9ce`. Prose
  pages match the documentation record's blob identities: `index.md` `b35e064`,
  `faq.md` `e4fda48`, `need-help.md` `35b1ce6`, `start/install.md` `e8f8e43`,
  `start/first-survey.md` `e339ead`, `guides/configuration.md` `4ba5504`,
  `guides/command-line.md` `f0b1391`, `guides/python.md` `076e549`,
  `guides/models-and-providers.md` `5f7c2c1`, `guides/costs.md` `4622163`,
  `guides/reruns.md` `4d36731`, `guides/outputs.md` `a3fceb7`,
  `contributing/development.md` `f226fb4`, `contributing/docs-site.md`
  `061f43d`, `contributing/releases.md` `dca1af0`.
- Environment: macOS arm64 (Darwin 25.6.0), the repo's `.venv` (Python 3.13.9,
  pydelity `0.0.1` from this checkout), Node 23.10.0 and the `docs/`
  `node_modules` installed from `docs/pnpm-lock.yaml`.
- Included: every prose page, the README, the sticker component and sidebar, the
  generated reference pages where the guides rely on them, and every AC's
  current evidence. Excluded: re-running the implementation's formal tests, CI
  and real provider runs, because `src`, `tests`, `scripts`, workflows and
  dependencies are byte-identical to what Tester verified and implementation
  review last assessed (see **Questions, Limitations, and Later Dependencies**).
- Project references loaded: `NONE` (`.standards/project-references/` does not
  exist). User style: none selected.
- Session: a fresh conversation started for this review; it holds none of the
  scope, design, implementation, test, implementation-review or documentation
  authoring history. Client metadata cannot certify freshness, and the models
  that produced the work are not recorded, so no model comparison is claimed.
  One helper agent checked the three contributor pages read-only; every mismatch
  recorded below was confirmed by Reviewer from the files.

## Contract and Evidence Assessment

"Tester" cites the verification report's formal evidence; "Impl. review" the
implementation review's conclusions, rechecked here against current content;
"Reviewer" this review's own inspection or diagnostics. Implementation evidence
is reused because `src`, `tests`, `scripts`, `examples`, workflows and
dependencies are unchanged since that evidence was produced.

- **AC-001, AC-002, AC-004, AC-005, AC-006, AC-040, AC-045, AC-046 survey.**
  Evidence: Tester and Impl. review (F-002 there resolved, others withdrawn).
  Reviewer: `faq.md`, `first-survey.md`, `outputs.md` match the facts and survey
  models, the comparison names and `details.source` values. Disposition:
  Supported.
- **AC-007, AC-008, AC-009, AC-047 CLI, config, examples.** Evidence: Tester and
  Impl. review. Reviewer: `configuration.md`, `command-line.md` against
  `cli.py`, `config/schemas.py`, `config/loading.py`, `ExitCode`; `--help` usage
  line. Disposition: Supported.
- **AC-010 silent import.** Evidence: Tester and Impl. review. Reviewer:
  `python.md` logs section; PydanticAI banner rules in the installed
  `_display.py`. Disposition: Supported.
- **AC-011, AC-037, AC-041 providers, rejection, retries.** Evidence: Tester and
  Impl. review. Reviewer: `models-and-providers.md` against
  `providers/uploads.py` (401/413 stop, 1-hour reuse), `providers/profiles.py`,
  the retry and timeout settings. Disposition: Supported.
- **AC-042, AC-043, AC-044 measure, load, async.** Evidence: Tester and Impl.
  review. Reviewer: `python.md` examples rerun (diagnostic below). Disposition:
  Supported.
- **AC-014, AC-015, AC-038, AC-039 cost ledger and spend controls.** Evidence:
  Tester and Impl. review. Reviewer: `costs.md` against `costs/budget.py` (two
  checks, one decision per run), `_log_estimate`, `RunCost`, `price_source`.
  Disposition: Supported.
- **AC-017, AC-018 reuse and interruption.** Evidence: Tester and Impl. review.
  Reviewer: `reruns.md` against the facts and survey fingerprints (PDF name
  included), `overwrite` handling, upload reuse. Disposition: Supported.
- **AC-019, AC-020 review list and report.** Evidence: Tester and Impl. review.
  Reviewer: `outputs.md` warning codes equal `WarningCode`; the report has no
  scripts or outside links. Disposition: Supported.
- **AC-021 mocked tests.** Evidence: Tester (suite) and Impl. review (105 passed
  at `2c8720c`); `tests` unchanged. Disposition: Supported.
- **AC-022, AC-023, AC-024 CI, Windows, wheel.** Evidence: Tester CI runs at
  `02b3ea1`/`b0ca0be`, reused by Impl. review after the probe fix; `ae81cb5`
  changes no packaging. Documenter's `just build` with `twine check --strict`
  passed for the new README. Disposition: Supported.
- **AC-025 metadata and README.** Evidence: Reviewer: README describes the
  usable survey release; `pyproject.toml` description and classifiers.
  Disposition: Supported.
- **AC-026, AC-036 release workflow and 0.1.0.** Evidence: Tester and Impl.
  review (readiness; publishing follows sign-off). Reviewer: `releases.md`
  matches `release.yml`, release-please config and manifest, the `pypi`
  environment. Disposition: Supported for readiness.
- **AC-027, AC-028, AC-029, AC-030 docs site, versions, deploy, conventions.**
  Evidence: Tester and Impl. review; workflows unchanged. Reviewer: docs build
  and link check at `ae81cb5` pass; markdownlint passes; `PageTitle` keys on the
  route id, so every versioned build shows the sticker only on its overview.
  Disposition: Supported.
- **AC-031 user can install and use pydelity from the docs.** Evidence:
  Reviewer: Start here, Guides, FAQ, Need Help? read against the code; examples
  rerun. Disposition: Supported (withdrawn F-002 is a non-material error-table
  wording issue).
- **AC-032 reference pages match the code.** Evidence: Tester: regeneration is
  byte-identical. Reviewer: `reference/python-api.md:368` describes `PdfError`
  differently from the code's behavior, a non-material wording issue (withdrawn
  F-001). Disposition: Supported.
- **AC-033 contributor pages.** Evidence: Reviewer and helper: `development.md`,
  `docs-site.md`, `releases.md` against `justfile`, hooks, workflows,
  release-please config, `docs/pnpm-lock.yaml`. Disposition: Supported, with
  non-material observations below (withdrawn F-003 among them).
- **AC-034 README and docs commands and examples match behavior.** Evidence:
  Reviewer: README and guide examples rerun or traced to code; Documenter's
  command runs. `just docs` and `just docs-build` fail on part of the Node range
  `docs-site.md` states, with Astro's own message naming the version it needs
  (withdrawn F-003). Disposition: Supported.
- **AC-035 user review of real runs.** Evidence: Tester: the user's acceptance
  (2026-11-18); `src` has changed since only by the probe fix, which leaves the
  committed fixtures' facts unchanged (Impl. review). Disposition: Supported.

Design notes assigned to Documenter (PyMuPDF AGPL where install is described;
upload storage, duration and how to shorten it; the default model and an OpenAI
model; reading `rotation_differs` and `page_number_differs`; sync and async
forms in Jupyter; timed-out requests that may be billed; one run per output
folder): each is present and accurate in the pages named in the documentation
record.

## Checks and Results

- `node .standards/bin/check.mjs` before review work: "STANDARDS check passed."
- Docs build, Reviewer diagnostic, in `docs/` on `ae81cb5`, 2026-11-19, Node
  23.10.0: `pnpm run build` built 25 pages, then `pnpm run check-links`:
  `Checked local links and fragments in 25 HTML pages.`; exit 0.
- `.venv/bin/prek run markdownlint-cli2 --all-files` at the repo root (outside
  the sandbox, which blocks prek's cache): `Passed`, exit 0; no file changed.
- Python API diagnostic in a scratch folder (`$TMPDIR/fr`, the `irs_form_w9.pdf`
  fixture as `document.pdf`, no API key): `pydelity.measure("missing.pdf")`
  raised `ConfigError` (`1 invalid setting: - pdf: no such file: missing.pdf`);
  an empty file raised `PdfError` (`the file is empty`); `measure` returned
  facts whose `summary` is a list of strings and wrote only `pdf_facts.json`;
  `estimate` returned `Decimal` `expected_usd` 0.360284 and `max_usd` 2.904852
  (the guides' $0.36 and $2.90); `load` after `measure` gave `record` `None`,
  `survey` `None`, facts set and an empty ledger. Field names used in the
  guides' examples (`profile.page_numbering[].first_page_index`,
  `last_page_index`, `style`; `ReviewIssue.check`, `page_index`, `message`;
  `ProviderError.provider_message` and `status_code`; `RunCost` fields; the six
  warning codes; the two comparison names; `details.source` values) exist in the
  models.
- `pydelity --help` (`.venv`): usage line `pydelity [OPTIONS] [pdf]`, as in
  `command-line.md`.
- Source reads behind the guides' claims: log lines and the cost question
  (`runner.py` `_log_estimate`, `_log_summary`, `cli.py` `_ask`), exit codes
  (`errors.py` `ExitCode`), option names (`cli.py`), defaults and bounds
  (`config/schemas.py`), relative paths in config files (`config/loading.py`),
  upload expiry, reuse and fallback (`providers/uploads.py`,
  `providers/profiles.py`), the `max_cost` checks (`costs/budget.py`), facts and
  survey fingerprints (`surveying/facts.py`, `surveying/survey.py`), the order
  of the cost question and the upload (`runner.py` `_survey` asks before
  `run_survey` attaches the PDF), the report's lack of scripts and outside links
  (`report/html.py`), PydanticAI's banner rules (installed
  `pydantic_ai/_display.py`), and PyMuPDF 2.1's wheel platforms in `uv.lock`
  (macOS arm64, manylinux x86_64 and aarch64, Windows amd64), which match the
  install page's unsupported list. The OpenAI example model
  `openai:gpt-6.2-astra` is the one the development plan records in real runs.
- Contributor pages (helper agent, read-only, no repository writes; Reviewer
  confirmed each mismatch below from the files): Astro 7.4.10's engine floor in
  `docs/pnpm-lock.yaml:742-744` (`node: '>=22.23.4'`) and its startup check in
  `docs/node_modules/astro/bin/astro.mjs:31-46`; `docs/package.json:9`
  (`>=22.12.0`); `docs.yml:5-6` and `:61-69` (publish only on `push`);
  `.pre-commit-config.yaml` hooks with `pass_filenames: false`;
  `.github/dependabot.yml` (four monthly ecosystems); the `test` recipe
  (`justfile:68-80`). About 80 other concrete claims (recipes, paths, triggers,
  permissions, environments, the release flow, all relative links) matched.

## Findings

### F-001 — The `PdfError` description says a missing PDF raises it

`Severity`: `P2` `Status`: `WITHDRAWN` `Owner`: `DEVELOPER` `FailureType`:
`IMPLEMENTATION`

- **Reassessment (2026-11-19, second pass at the user's request to keep only
  major issues):** withdrawn as not material. The error is a wording slip in one
  class docstring and the reference line generated from it. Every function's
  `Raises` entry in the same reference page is correct, the error raised for a
  missing path (`ConfigError`) is still a `PydelityError` with the message
  `pdf: no such file`, and the CLI exits with code 2 either way, as documented.
  Only code that catches `PdfError` alone to skip missing paths is affected, and
  it fails loudly with a clear message. The failure recovery frame routed for it
  was withdrawn before any Developer work (see **Progress and Conclusion**).
  Kept as an observation for Developer.

- **Reference:** `src/pydelity/errors.py:65` (`PdfError` docstring "The PDF is
  missing, empty, password-protected or cannot be opened."), reproduced in the
  generated `docs/src/content/docs/reference/python-api.md:368`; tree `src`
  `cae826c`, reference tree `8762d28`. Contract: `AC-032` (reference pages match
  the code); design **Data and Control Flow** steps 1–2 (validation raises
  `ConfigError` first; `PdfError` covers a password-protected, empty or
  unopenable PDF).
- **Failure case:** `pydelity.run("missing.pdf")` (or `measure`, `estimate`,
  `survey`, or a config file's `pdf`) for a path that does not exist. Settings
  validation (`Config._check_pdf`, `config/schemas.py`) rejects it and raises
  `ConfigError` (`pdf: no such file`), not `PdfError`. Code that follows the
  reference and catches `pydelity.PdfError` to skip missing files does not catch
  it. `utils/pdf.py:127-128` raises `PdfError` for a missing file only if the
  file disappears after validation.
- **Impact:** the reference misdescribes the public error contract for the most
  common PDF problem, and contradicts itself: each function's `Raises` entry in
  the same page (for example `:45`, `:83`) correctly leaves "missing" out.
- **Evidence:** Reviewer diagnostic above (`measure("missing.pdf")` →
  `ConfigError`); the docstring and generated line quoted.
- **Smallest correction:** make the `PdfError` docstring describe what raises it
  (an empty, password-protected or unopenable PDF; optionally a file that
  vanished after the settings were checked), and regenerate the reference pages
  so `python-api.md` matches.

### F-002 — The Python guide's error table sends a missing PDF to `PdfError`

`Severity`: `P2` `Status`: `WITHDRAWN` `Owner`: `DOCUMENTER` `FailureType`:
`DOCUMENTATION`

- **Reassessment (2026-11-19, second pass):** withdrawn as not material, for the
  reasons under F-001: one table row repeats the docstring's wording, the
  guide's examples and the CLI exit codes are right, and the misnamed case still
  raises a `PydelityError` that the guide's own catch-all example handles. Kept
  as an observation for Documenter.

- **Reference:** `docs/src/content/docs/guides/python.md:137` (blob `076e549`),
  the **Errors** table: "`PdfError` | The PDF is missing, empty,
  password-protected or can't be opened". `ConfigError`'s row (`:136`) does not
  mention a missing PDF. Related: `AC-031`, `AC-034`; F-001.
- **Failure case:** a user writes the batch loop the guide implies,
  `except pydelity.PdfError: continue`, over a list that includes a path that
  does not exist; `ConfigError` escapes and the loop stops.
- **Impact:** the guide teaches the wrong exception for the most common PDF
  problem, in the section users read to write their error handling.
- **Evidence:** Reviewer diagnostic above; the guide's table row; the CLI
  guide's exit-code table is unaffected (both errors exit with code 2).
- **Smallest correction:** say in the table that a missing PDF path is an
  invalid setting (`ConfigError`), and keep `PdfError` for an empty,
  password-protected or unopenable PDF.

### F-003 — The docs-site page states a Node.js floor that Astro rejects

`Severity`: `P2` `Status`: `WITHDRAWN` `Owner`: `DOCUMENTER` `FailureType`:
`DOCUMENTATION`

- **Reassessment (2026-11-19, second pass):** withdrawn as not material. It
  affects only contributors who build the docs site on Node 22.12 to 22.23.3;
  Astro stops at once with a message naming the version it needs, so the fix is
  obvious, and CI and the hooks pin Node 24.22.3, so no published build or
  release is affected. Kept as an observation for Documenter (and for
  `docs/package.json`'s engines field, Developer's).

- **Reference:** `docs/src/content/docs/contributing/docs-site.md:17` (blob
  `061f43d`): "Node.js 22.12 or later". Locked Astro 7.4.10 requires
  `node >=22.23.4` (`docs/pnpm-lock.yaml:742-744`) and checks it when it starts
  (`docs/node_modules/astro/bin/astro.mjs:31-46`). The design names Node
  `24.22.3` as the repo's one Node version, pinned in CI and the hooks. Related:
  `AC-033`, `AC-034`.
- **Failure case:** a contributor on Node 22.12 to 22.23.3, which the page says
  is enough, runs `just docs` or `just docs-build`; `pnpm install` passes (the
  stale `docs/package.json` engines field only warns), then Astro exits 1 with
  "Node.js v22.x is not supported by Astro!".
- **Impact:** the documented setup for previewing and building the docs site
  fails for part of the version range the page states.
- **Evidence:** the lock file entry and Astro's start-up check quoted above,
  confirmed by Reviewer; the page copies `docs/package.json:9` (`>=22.12.0`),
  which Astro has outgrown.
- **Smallest correction:** state a Node version the site actually builds with,
  such as the repo's pinned 24.22.3 or Astro's floor of 22.23.4.

## Questions, Limitations, and Later Dependencies

- No blocking user question. `Active Work.BlockedOn` stays `NONE`.
- Earlier later-role dependencies from the implementation review (`AC-025`
  README, `AC-031`, `AC-033`, `AC-034`, owner Documenter) now have
  owner-produced evidence sufficient for this gate.
- Non-material observations (no correction required by this gate; owners may
  take them up later): withdrawn F-001 to F-003 above, and:
  - `docs-site.md:99-101` says manual runs build every released version and that
    the site is published once the version has its tag; `docs.yml:61-69`
    publishes only on a `push`, so a manual run never publishes. Worth saying
    how to republish (re-run the tag's or `main`'s push run).
  - `docs-site.md:49-53` and `development.md:55` describe `just docs-reference`
    as regenerating the pages, but its output is unformatted until
    `just lint-markdown` or the hook runs Prettier, so on its own it leaves
    every reference page modified. `just lint` does both.
  - `development.md:69-71`: `uv run pytest --randomly-seed=<seed>` gives the
    same shuffle but not each xdist worker's order, and skips the docstring
    session, which prints its own seed.
  - `development.md:104`: Dependabot opens up to four monthly pull requests
    (github-actions, npm in `docs/`, pre-commit, uv), not one.
  - `development.md:108`: several hooks (`prettier-markdown`,
    `markdownlint-cli2`, `env-template-sync`, `ty`, `interrogate`, `zizmor`)
    check the whole tree, not only the commit's files.
  - `releases.md:37`: by release-please's default changelog sections, `perf:`
    and `revert:` commits also make a patch release (not confirmed from a repo
    file).
  - `docs-site.md:41-42`: the docs build runs on pull requests to `main`, not
    every pull request.
  - `faq.md` ("a survey setting" reruns the survey) is looser than `reruns.md`,
    which correctly says `request_timeout_seconds` keeps the saved survey.
  - `docs/package.json:9` engines `>=22.12.0` is below Astro's floor
    (Developer's config; Astro enforces its own floor, so only the warning is
    lost).
- Limitations: CI has not run on `ae81cb5`; the commit changes only Markdown,
  the sidebar and a presentation component, and the docs build, link check and
  markdownlint pass locally. GitHub settings (squash-merge title, environments,
  Pages source), remote tags and the PyPI Trusted Publisher cannot be checked
  before sign-off; `.standards/CONTEXT.md` records the squash-title rule the
  docs repeat. None of these changes this gate's outcome.

## Progress and Conclusion

- Inspected: protocol, state, scope, design (docs sections and Documenter
  notes), development plan notes, verification report, implementation review,
  context, documentation record; the README, every prose page and the sticker
  component; the reference pages the guides rely on; the source behind each
  guide claim; contributor pages through a helper with Reviewer confirmation.
  Docs build, link check and markdownlint pass.
- First pass (2026-11-19): recorded F-001 to F-003 as open P2 findings and made
  an uncommitted `FAILURE` handoff to `DEVELOPING` with recovery frame 1 for
  F-001.
- Second pass (2026-11-19, at the user's request to keep only major issues):
  each finding was rechecked for how often its trigger occurs and what it
  breaks. All three are withdrawn as not material (reasons in each finding). No
  Developer work took place under the frame, and nothing had been committed, so
  `STATE.md` was restored to its committed `REVIEWING_FINAL` state before this
  review's own forward handoff, instead of running an empty Developer recovery.
  Inputs are unchanged: HEAD `ae81cb5`, clean tree apart from this report and
  `STATE.md`.
- Gate: **passes.** No material finding or assessment gap is open, every current
  AC has sufficient current evidence, the earlier implementation-stage
  dependencies are resolved by Documenter's pages and README, and no blocking
  question or review-owned obligation remains. Passing this gate does not finish
  the cycle: synchronization follows (`FULL_DELIVERABLE`), then the user's
  sign-off.
- User decision (2026-11-19, after this gate passed and the forward handoff to
  `SYNCHRONIZING`): fix all three withdrawn findings. Routed as `USER_REWORK`
  (`IMPLEMENTATION`) to `DEVELOPING` with recovery frame 1 (`ResumeAt`
  `SYNCHRONIZING`), since F-001 starts in `src/pydelity/errors.py` and the
  reference generated from it. Each finding's **Smallest correction** states the
  required outcome: F-001 for Developer, F-002 and F-003 for Documenter. The
  rerun must include `DOCUMENTING` and `REVIEWING_FINAL`, where Reviewer
  rechecks the three corrections and any changed inputs before synchronization.
- Plain-language summary: the whole deliverable is ready for the final
  consistency check. The code, tests, release setup, docs site and docs all
  check out against each other, and the docs build with no broken links. A few
  small wording slips remain in the docs (listed in this report), none of which
  stops anyone from installing, running or releasing pydelity. Not checked
  before sign-off: real publishing to PyPI and GitHub Pages, and CI on the last
  docs commit.

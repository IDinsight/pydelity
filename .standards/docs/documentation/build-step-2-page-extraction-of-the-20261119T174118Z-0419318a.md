<!-- STANDARDS
Artifact: DOCUMENTATION
Cycle: build-step-2-page-extraction-of-the-20261119T174118Z-0419318a
-->

# Documentation Record

`Cycle`: `build-step-2-page-extraction-of-the-20261119T174118Z-0419318a`
`Status`: `COMPLETE` `Collaboration`: `AUTONOMOUS` `Target`: `ACTIVE_CHANGE`
`Target Detail`: `build-step-2-page-extraction-of-the-20261119T174118Z-0419318a`
`User Style`: `tony`

## Assessed Inputs and Boundary

- Workflow state: `DOCUMENTING`, `STANDARD`, `FULL_DELIVERABLE`, forward handoff
  from `REVIEWING_IMPLEMENTATION`; recovery and outstanding obligations
  inactive.
- Checkout: branch `tz6/pipeline-step-2`, HEAD `daab6a9` (implementation at
  `4866b88`). Comparison range: `main` (`c7582e7`, release 0.1.1, the merge
  base) to HEAD, 41 commits, plus this record's uncommitted documentation edits.
  No staged, moved or deleted files; the only untracked files are this record
  and `docs/src/content/docs/guides/page-extraction.md`.
- Input identities at HEAD (git object, 12 hex), unchanged during this work:
  - Scope `.standards/docs/scope/<cycle>.md` `8f6dbf9b42a6`; design
    `.standards/docs/specs/<cycle>.md` `878aa2339bac`; development plan
    `.standards/docs/development/<cycle>.md` `bf0636cfd9ef`; verification report
    `.standards/docs/verification/<cycle>.md` `37e0f1d4170f`; implementation
    review `.standards/docs/reviews/<cycle>/implementation.md` `c1e03da97691`;
    `.standards/CONTEXT.md` `be80a93c129c`; `artifacts/next_cycle_inputs.md`
    `c292552b1b84`.
  - Behavior and tooling: `src` `72daf0b4293b`; `scripts` `3a4c589069e8`;
    `examples` `d7cf92debfd7`; `.github` `5cc03340a06e`; `justfile`
    `ff59f1cc113a`; `.pre-commit-config.yaml` `418a80d9204e`;
    `release-please-config.json` `e2af4b1b9c9b`; `.release-please-manifest.json`
    at `0.1.1`.
  - Documentation before the edits: `docs/src/content/docs` `7c17a35be8cb`;
    `README.md` `c1bfbea05dc7`; `docs/astro.config.mjs` `73e97125e2ce`.
- Generated reference pages (`docs/src/content/docs/reference/`) belong to
  `scripts/generate_reference_docs.py`. Tester verified them current and
  complete (verification report, `AC-052`); this work did not edit them, and no
  source change since then touches them.
- Editing boundary: `README.md`, the hand-written pages under
  `docs/src/content/docs/` (not `reference/`), and the site description and
  sidebar in `docs/astro.config.mjs`. `AGENTS.md` and `CLAUDE.md` hold only the
  managed STANDARDS block, so there is no project agent guidance to change.
  Code, docstrings, examples, workflows and `CHANGELOG.md` were left alone; no
  discrepancy needed a change there.
- User decision during this work: the user approved adding
  `docs/src/content/docs/guides/page-extraction.md` ("Extract pages") as a new
  file, listed in the sidebar after the Python guide.
- Styles loaded: `.claude/skills/documenter/styles/universal.md`;
  `.standards/user-styles/documenter/tony.md` (`7aa74f1cc62d`), selected by the
  user; `.claude/skills/documenter/styles/python.md` was not needed beyond
  keeping examples runnable. `references/readme.md` not loaded (no README
  restructure).
- Project references loaded: `NONE` (`.standards/project-references/` does not
  exist).

## Documentation Work and Evidence

User rework, async first (recovery frame 1). Python examples now use the async
functions, and the sync versions are mentioned as the same names without the
`a`. Current identities after `just lint-markdown`; they supersede the earlier
identities listed for these files below:

- `docs/src/content/docs/guides/python.md` `bfdf291bf136`. Function table uses
  the `a` names; new "Async and sync" section (top-level `await` in Jupyter, a
  full `asyncio.run` script, the sync versions and their `RuntimeError` inside a
  running loop, `load` sync only) replaces "Jupyter and async code"; every
  example awaits; new "Run several PDFs at once" with an `asyncio.gather`
  example, the per-run `concurrent_pages` note and the same-folder warning.
  `AC-027`, `AC-029`, `AC-033`, `AC-051`, `AC-053`.
- `README.md` `b4451d9e668c`. Python example is an `asyncio.run` script with
  `await pydelity.arun(...)`; one line for Jupyter and the sync versions.
  `AC-053`.
- `docs/src/content/docs/faq.md` `13940c58e70f`. `ameasure`, `aestimate`;
  Jupyter answer links to `#async-and-sync`. `AC-051`.
- `guides/costs.md` `43724eadb664`, `guides/models-and-providers.md`
  `d7dcfd835b99`, `guides/configuration.md` `1cee28492eac`,
  `guides/page-extraction.md` `d86ef9ace131`, `guides/reruns.md` `96d55f3b88a5`:
  examples await `arun` or `aestimate`; prose names `pydelity.aestimate`.
- Not changed: the generated Python API reference. Its order (sync form first)
  and intro come from `scripts/generate_reference_docs.py`, tooling outside this
  boundary; the content is accurate.

Earlier saved outcomes, with content identities (`git hash-object`, 12 hex)
after `just lint-markdown` formatted them:

- `docs/src/content/docs/guides/page-extraction.md` `62790f18a7ea` (new). Users.
  What page extraction gives (item fields, kinds, roles, containers, captions,
  one-figure pages), the pause, `pages`, the model override,
  `advanced.extraction.instructions`, how a page is read (upright image, size,
  hints sent, text read from the image only), the checks and verifier, text
  comparison and when differences are listed, `concurrent_pages` and page
  failures. `AC-001`–`AC-005`, `AC-007`–`AC-014`, `AC-016`–`AC-018`, `AC-021`,
  `AC-022`, `AC-051`, `AC-056`–`AC-061`, `AC-063`, `AC-064`.
- `docs/astro.config.mjs` `4ecd0286e326`. Site description covers both steps;
  sidebar lists the new guide. `AC-049`, `AC-051`.
- `README.md` `57eeef1098be`. Describes the survey and page extraction, the
  two-run quick start with the pause, `--pages` and `--no-pause`, and a Python
  example with `pause=False` and page items. `AC-049` (README part), `AC-053`.
- `docs/src/content/docs/index.md` `b640d35efd25`. Overview of both steps;
  quickstart with the pause and the second run. `AC-051`, `AC-053`.
- `docs/src/content/docs/start/first-survey.md` `c3514736a2bf`. Title now "Your
  first run" (file name kept, so links stay valid): survey, pause message,
  second run with the extraction estimate, output folder table with `pages/` and
  `figures/`, the report's extracted pages. `AC-003`, `AC-027`, `AC-029`,
  `AC-034`, `AC-051`, `AC-053`.
- `docs/src/content/docs/start/install.md` `c9613e12a073`. Page images are sent
  too; next-page link text. `AC-051`.
- `docs/src/content/docs/faq.md` `8af4c4e0351c`. Page extraction answers (what
  it gives, the pause, page selection, stored text), what each step sends,
  uploads, costs per step, reruns with the corrected survey-settings wording.
  `AC-044` (faq item), `AC-051`, `AC-053`.
- `docs/src/content/docs/guides/configuration.md` `9466ec66e25d`. Replaced the
  YAML example that used the removed top-level `instructions` with
  `advanced.survey.instructions`; `pages`; advanced settings table with every
  `advanced.extraction` setting and both instructions settings; `pages` past the
  PDF. `AC-001`, `AC-002`, `AC-005`, `AC-057`, `AC-059`, `AC-061`, `AC-053`.
- `docs/src/content/docs/guides/command-line.md` `458c6305eebe`. Removed the
  `--instructions` example; `--pages`, `--no-pause`; two runs or one; verbose
  output and the summary's review-issue form; script examples with `--no-pause`;
  exit codes for a paused run and a failed page. `AC-001`, `AC-003`, `AC-004`,
  `AC-026`, `AC-033`, `AC-051`, `AC-053`, `AC-061`.
- `docs/src/content/docs/guides/python.md` `fb99320400c3`. `extract` and
  `aextract`, `RunResult.pages`, `run()` pausing without raising, `pause=False`,
  reading items, `estimate` with `pause=False` and per-step figures, `load` with
  pages, `ExtractionError`; removed the banner workaround now that the API turns
  the banner off. `AC-003`, `AC-027`, `AC-029`, `AC-033`, `AC-040`, `AC-051`,
  `AC-053`.
- `docs/src/content/docs/guides/models-and-providers.md` `2bb4377a8b7a`. Model
  per step and `advanced.extraction.model`; what each step sends (no PDF and no
  stored text for page extraction); uploads are the survey's only; timeouts per
  step; `concurrent_pages` and rate limits; when page extraction fails.
  `AC-005`, `AC-033`, `AC-051`, `AC-057`, `AC-058`, `AC-060`.
- `docs/src/content/docs/guides/costs.md` `5657e1d85726`. Extraction estimate;
  the plan-time check now uses the likely cost (the old text said the maximum),
  per-request checks with requests in flight, a question partway through; ledger
  lines name page and agent; cache price `0` is free; ways to spend less on page
  extraction. `AC-028`–`AC-030`, `AC-041`, `AC-051`.
- `docs/src/content/docs/guides/reruns.md` `1c1a6fb0ce88`. Survey inputs with
  `advanced.survey.instructions`; what each page file's reuse depends on;
  changing the selection; `overwrite` with the pause and with `--no-pause`;
  resuming after a stop; damaged page files and crops. `AC-031`–`AC-033`,
  `AC-051`.
- `docs/src/content/docs/guides/outputs.md` `287ae3ba13ee`. `pages/` and
  `figures/`; page numbering from 0 and from 1; the report's extracted pages;
  `run.json` status `paused`, step `skipped` and page counts, warnings by step;
  the review list by step and item with each extraction source; page file fields
  including the verdict. `AC-013`, `AC-025`, `AC-026`, `AC-034`, `AC-051`,
  `AC-063`, `AC-064`.
- `docs/src/content/docs/contributing/development.md` `acf3289557c4`. `AC-044`:
  `just docs-reference` output stays unformatted until `just lint-markdown`;
  what `--randomly-seed` repeats; up to four monthly Dependabot pull requests;
  which hooks check the whole tree. Smoke test now runs page extraction
  (`AC-047`).
- `docs/src/content/docs/contributing/docs-site.md` `78c399a883a7`. `AC-044`:
  the docs build runs on pull requests to `main`; reference pages need
  `just lint-markdown` after `just docs-reference`, and CI also fails on
  untracked pages (`AC-042`); a manual run never publishes, and how to
  republish.
- `docs/src/content/docs/contributing/releases.md` `37144730caa5`. `AC-044`:
  `perf:` and `revert:` also make a patch release, from release-please's default
  changelog sections; a breaking change below 1.0.0 gives 1.0.0. Replaced the
  out-of-date "first release" section with where the version comes from.
  `AC-050`.
- No change, assessed: `docs/src/content/docs/need-help.md` (nothing
  step-specific); generated reference pages (current per Tester, `AC-052`);
  `AGENTS.md` and `CLAUDE.md` (managed block only); `CHANGELOG.md`
  (release-please writes it; `AC-043` link fix is Developer's and verified).

Accounting for every current acceptance condition (retired `AC-015`, `AC-023`,
`AC-024` and `AC-062` are history):

- Settings and the pause, documented in the page extraction, configuration,
  command-line and Python guides: `AC-001`, `AC-002`, `AC-003`, `AC-004`,
  `AC-005`, `AC-059`, `AC-060`, `AC-061`.
- What a page file holds, documented in the page extraction and outputs guides,
  with field detail in the generated page file reference: `AC-007`, `AC-008`
  (IDs and their stability), `AC-009` (boxes in points from the top left),
  `AC-010` (reading order by direction and columns), `AC-011` (upright reading),
  `AC-012` (content per kind), `AC-013`, `AC-014`, `AC-016`, `AC-017`
  (one-figure pages are valid), `AC-018`, `AC-056`.
- Checks, verifier and review list, documented in the page extraction and
  outputs guides: `AC-021`, `AC-022`, `AC-025`, `AC-026`, `AC-063`, `AC-064`.
- Running, costs and resume, documented in the Python, models, costs, reruns and
  outputs guides: `AC-027`, `AC-028`, `AC-029`, `AC-030`, `AC-031`, `AC-032` (no
  half-written page files or crops; damaged ones redone), `AC-033`, `AC-034`,
  `AC-057`, `AC-058`.
- Follow-up fixes with a user-visible effect: `AC-040` (banner workaround
  removed from the Python guide), `AC-041` (cache price `0` in the costs guide).
- Documentation-owned conditions: `AC-044`, `AC-049` (README and site
  description; package metadata is Developer's, verified), `AC-051`, `AC-053`.
- Release and CI facts kept accurate in the contributing pages: `AC-047` (smoke
  test runs page extraction), `AC-050` (release types and versions).
- `AC-006`: example config files are Developer's, verified by Tester; the
  configuration guide points to them unchanged.
- `AC-052`: generated reference pages, verified by Tester; no hand edit.
- No user-facing documentation needed: `AC-019` (robustness to odd surveys),
  `AC-020` (neutrality of code and prompts), `AC-035`, `AC-036`, `AC-037`,
  `AC-038` and `AC-039` (probe and transport fixes, whose effects show in the
  outputs already documented), `AC-042` and `AC-043` (CI and changelog fixes,
  Developer's; the docs-site page now mentions untracked reference pages),
  `AC-045` and `AC-046` (tests and CI), `AC-048` (wheel and metadata check).
  `AC-054` is the user's review of real runs before sign-off, not documentation.

## Checks and Applicability

All run on 2026-11-20 from the repository root unless noted.

Async-first rework, same inputs (HEAD `daab6a9`, `src` `72daf0b4293b`, user
style `7aa74f1cc62d`):

- `just lint-markdown` (outside the sandbox): 4 files formatted, including
  `faq.md` and `python.md`; `markdownlint-cli2 ... Passed`; STANDARDS check
  passed; exit 0.
- `just docs-build` (outside the sandbox):
  `Checked local links and fragments in 28 HTML pages.`; exit 0. Covers the new
  `#async-and-sync` anchor the FAQ links to.
- Python examples: scratch `run_doc_examples.py` (session scratchpad) started
  the stand-in with the scanned 1965 form fixture and its canned answers, copied
  it as `document.pdf`, `form-a.pdf` and `form-b.pdf`, and ran every `python`
  block of `README.md` and the Python, page extraction, configuration, costs,
  models and reruns guides in order, one folder per file. Blocks with top-level
  `await` ran inside an event loop, as in a Jupyter cell. 20 passed, 0 failed;
  the install page's `api_key` block skipped. Page lists past 2 pages were
  narrowed to `1-2`. This supersedes the earlier example check below.
- Claims: `asyncio.gather` of two `arun(..., pause=False)` calls completed with
  2 pages each in `pydelity-output/form-a` and `pydelity-output/form-b`;
  `measure`, `estimate`, `survey`, `extract` and `run` each raised
  `RuntimeError` inside a running loop; sync `run(..., pause=False)` returned a
  completed `RunResult`; `load` worked inside a running loop. The per-run page
  limit is an `asyncio.Semaphore` created per extraction
  (`src/pydelity/extracting/extraction.py`).

Earlier checks:

- `node .standards/bin/check.mjs`: `STANDARDS check passed.`, exit 0, before any
  work and again before handoff.
- `just lint-markdown` (outside the sandbox, which blocks uv's cache in the home
  folder): Prettier formatted 13 changed Markdown files;
  `markdownlint-cli2 ... Passed`; exit 0. The STANDARDS check it runs passed.
- `just docs-build` (outside the sandbox, same reason): 28 pages built, the new
  guide included; `Checked local links and fragments in 28 HTML pages.`; exit 0.
- Python examples: a scratch script outside the repo (`run_doc_examples.py`)
  started the test stand-in (`tests/fixtures/mock_providers.py`) with the
  scanned 1965 form fixture and its canned survey and page answers, copied the
  PDF as `document.pdf`, and ran every `python` block of `README.md` and the
  configuration, Python, page extraction, models, costs and reruns guides with
  the repo's `.venv` (pydelity at HEAD). 19 blocks passed; skipped: the
  top-level `await` block (Jupyter only) and the install page's `api_key` block
  (needs the reader's variable). Page lists past the fixture's 2 pages were
  narrowed to `1-2`.
- Pause, async and selection: a second scratch script checked that `run()` with
  defaults ends `paused` with extraction `skipped`, the next `run()` completes
  with 2 page files, `arun(pause=False)` completes, `extract(pages="2")` returns
  page 2 and writes no `run.json`, and narrowing to `pages="1"` reports 1
  selected, 1 reused while `load()` still returns pages 0 and 1.
- YAML examples: every `yaml` block of the configuration, page extraction,
  models and costs guides loaded as settings through `pydelity.estimate` with no
  error. Top-level `instructions` gives
  `instructions: not a setting pydelity knows`; `pages="1-5,8"` on the 2-page
  PDF gives `pages: 1-5,8 goes past the last page; document.pdf has 2 pages`.
- CLI output quoted in the docs comes from runs of the repo's `pydelity` command
  against the stand-in: the pause message, the `--overwrite` hint, the summary
  line forms and both estimate lines. The estimate lines are pydelity's own
  computation from the PDF and current prices; the stand-in's spend figures come
  from fake token counts, so the docs quote none of them.
- Behavior read in source at HEAD to support wording: CLI questions
  (`src/pydelity/cli.py`), summary, pause and estimate logging
  (`src/pydelity/pipeline/runner.py`), page logging and checks
  (`src/pydelity/extracting/`), report sections (`src/pydelity/report/html.py`),
  inline page images (`src/pydelity/extracting/llm.py`), banner off
  (`src/pydelity/api.py`), `.github/workflows/docs.yml` and `ci.yml`,
  `justfile`, `.github/dependabot.yml`, `.pre-commit-config.yaml`,
  `pyproject.toml` pytest settings.
- release-please patch types: upstream source read on `master`, not the 17.x tag
  that `release-please-action` v5.0.0 bundles.
  `conventional-changelog-conventionalcommits` `src/constants.js` shows `feat`,
  `feature`, `fix`, `perf` and `revert` and hides `docs`, `style`, `chore`,
  `refactor`, `test`, `build` and `ci`; release-please passes no sections of its
  own when `changelog-sections` is unset (`src/changelog-notes/default.ts`,
  `src/factory.ts`); `src/versioning-strategies/default.ts` gives a patch for
  any shown type other than `feat`, and a major bump for a breaking change while
  `bump-minor-pre-major` is unset. Limit: not read at the bundled version.
- Not run: a real model run (needs the user's keys; `AC-054` covers it); the
  versioned docs build (`pnpm run build:versions`), which needs release tags and
  does not depend on these pages' content.

## Discrepancies, Dependencies, and Remaining Work

`NONE`. No documentation discrepancy is open, and no other owner's defect was
found. Final review depends on this record and the saved documents; the user's
real runs (`AC-054`) remain before sign-off as the implementation review
recorded.

## Resume and Conclusion

- User rework (2026-11-20, recovery frame 1, from `REVIEWING_FINAL`, resume
  there). The user asked whether the documentation covers async usage; it did,
  in one Python guide section, a README line, a FAQ entry and the generated
  reference. The user then asked for async usage as the main examples, with the
  sync versions mentioned as the same names without the `a`. Request and scope
  unchanged. Applied, inspected and checked as recorded above.
- Example form chosen: snippets use top-level `await`, which runs as is in
  Jupyter; the Python guide and README show one full `asyncio.run` script.
- Blocking question: `NONE`.
- No downstream work to rerun: final review had not produced a report for this
  cycle, so the frame pops and the workflow resumes at `REVIEWING_FINAL`, review
  kind `FINAL_DELIVERABLE`.
- Selected target `ACTIVE_CHANGE` and the full Documenter gate are complete for
  the inputs above. This is not cycle completion or sign-off.
- On resumption: compare the identities above, rerun `just lint-markdown`,
  `just docs-build` and the scratch example checks if any listed file changed.

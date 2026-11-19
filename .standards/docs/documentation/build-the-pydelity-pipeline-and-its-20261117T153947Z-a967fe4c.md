<!-- STANDARDS
Artifact: DOCUMENTATION
Cycle: build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c
-->

# Documentation Record

`Cycle`: `build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c`
`Status`: `COMPLETE` `Collaboration`: `AUTONOMOUS` `Target`: `ACTIVE_CHANGE`
`Target Detail`: `build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c`
`User Style`: `tony`

## Assessed Inputs and Boundary

- Workflow: `STANDARD`, `FULL_DELIVERABLE`, `DOCUMENTING`, recovery inactive, no
  outstanding obligations (`.standards/STATE.md`). Entered by `FORWARD` from
  `REVIEWING_IMPLEMENTATION`.
- Contract and owner evidence (SHA-256 prefixes, unchanged at HEAD `9273074`
  when rechecked on 2026-11-19): scope `1c127ab4fa9a2c5e`, design
  `7e579b1ed3535e6e`, development plan `4aa6bef88043e791`, verification report
  `e8e654e6b3ccffcb`, implementation review `3fd035240dc9ad4e`, context
  `.standards/CONTEXT.md` `aa4a553cf773451e`. These match the identities the
  implementation review assessed.
- Behavior inputs at HEAD `9273074`, unchanged by this work: trees `src`
  `cae826c`, `tests` `268e597`, `examples` `235e934`, `scripts` `19567bb`,
  `.github` `4cc0d13`; blobs `pyproject.toml` `3cb2e48`, `justfile` `ff59f1c`,
  `.template.env` `56e4725`; generated `docs/src/content/docs/reference/` as
  committed.
- Comparison range: `main` (`bdd8488`, merge base) to `tz6/pipeline` at
  `9273074`, plus this record's uncommitted documentation edits. The STANDARDS
  installation (`.standards/`, `.claude/`, `.agents/`) is workflow tooling, not
  project documentation.
- Editing boundary: prose docs pages under `docs/src/content/docs/` (outside the
  generated `reference/` folder), `README.md`, and the sidebar list in
  `docs/astro.config.mjs`. At the user's request (2026-11-19) it also covers the
  overview's comic sticker: `docs/src/components/PageTitle.astro` and its
  `components` entry in `docs/astro.config.mjs`, docs-site presentation only. No
  change to behavior, tests, generated reference pages, the generator, workflows
  or other configuration.
- Styles: `.claude/skills/documenter/styles/universal.md`,
  `.standards/user-styles/documenter/tony.md` (selected by the user,
  2026-11-18), `.claude/skills/documenter/styles/python.md` for Python examples;
  `.claude/skills/documenter/references/readme.md` for the README restructure.
  Organization rules applied: API keys appear only as the placeholder
  `[API_KEY]`; no respondent data in examples (the sample PDF is a blank public
  IRS Form W-9 test fixture).
- Project references loaded: `NONE` (`.standards/project-references/` does not
  exist).

## Documentation Work and Evidence

The user approved the inventory below on 2026-11-19 ("let's write these") and
will review the written docs. Saved content identities are `git hash-object`
prefixes after `just lint-markdown` formatting.

Written or updated:

- `README.md` `6d56470` (users, PyPI): replaces the name-reserving placeholder
  with what 0.1.0 does, install with uv or pip, Python 3.13+, the PyMuPDF
  AGPL-3.0 note, API keys by environment variable, a CLI and Python quick start,
  the `examples/` pointer and links to the docs site. Absolute URLs, because
  PyPI renders the README. The contributor sections moved to the docs site
  (approved).
- `docs/src/content/docs/index.md` `b35e064`: a short overview, a Quickstart
  (install with uv, set the Anthropic key, run, open the report) and "Find your
  next step" links, laid out like the STANDARDS docs overview at the user's
  request. The user dropped "Why We Built This" and moved "What a survey gives
  you" to the FAQ. The "being written" placeholder is gone.
- `docs/src/content/docs/faq.md` `e4fda48` (new, at the user's request): what a
  survey gives you (moved from the overview), why the model's answer is kept,
  models, what is sent and kept, use without a key, costs, reruns, `max_cost`,
  Windows, scripts, Jupyter, resuming, several PDFs, license. Each answer links
  to its guide section.
- `docs/src/content/docs/need-help.md` `35b1ce6` (new, at the user's request):
  GitHub Issues and the four issue forms in `.github/ISSUE_TEMPLATE/`, adapted
  from the STANDARDS page, with a warning not to post keys or private PDFs.
- `docs/src/components/PageTitle.astro` `9d04eb4` (new, at the user's request):
  a comic-style "READ PDFs WITH" sticker before the overview's title, in
  IDinsight's blues, adapted from the STANDARDS overview sticker. Other pages
  use Starlight's default title.
- `docs/src/content/docs/start/install.md` `e8f8e43`: platforms without PyMuPDF
  2 wheels, install as a tool or into a project (macOS, Linux, Windows
  PowerShell), API keys per OS for the session and permanently, the license
  note.
- `docs/src/content/docs/start/first-survey.md` `e339ead`: a first CLI run, the
  cost question, the output folder and its files.
- `docs/src/content/docs/guides/configuration.md` `4ba5504`: config files, the
  `examples/` templates, precedence (nested `advanced` merge), relative paths,
  invalid settings, the `advanced:` settings.
- `docs/src/content/docs/guides/command-line.md` `f0b1391`: options, what is
  printed and where, scripts and CI with `--yes`, `--yes` over `max_cost`, batch
  loops for bash and PowerShell, exit codes.
- `docs/src/content/docs/guides/python.md` `076e549`: the five functions and
  their async forms, `RunResult`, settings, `measure`/`estimate`/`load`,
  Jupyter, concurrency limits, errors, warnings, logs and the PydanticAI banner.
- `docs/src/content/docs/guides/models-and-providers.md` `5f7c2c1`: choosing a
  model, what is sent, upload storage and `expiry_hours` per provider, large
  PDFs, retries, timeouts that may be billed unseen, survey failures.
- `docs/src/content/docs/guides/costs.md` `4622163`: the estimate, the question,
  `max_cost` per output folder in the CLI and Python, the ledger, prices and
  `advanced.models`, ways to spend less.
- `docs/src/content/docs/guides/reruns.md` `4d36731`: what is reused and what
  triggers a new survey, `overwrite`, resuming, damaged and leftover files, one
  PDF and one run per folder, the Windows open-file limit.
- `docs/src/content/docs/guides/outputs.md` `a3fceb7`: each output file, the
  report, warning codes, the review list and why users should read
  `rotation_differs` and `page_number_differs` issues.
- `docs/src/content/docs/contributing/development.md` `f226fb4`: prerequisites,
  every just recipe, tests (offline stand-in provider, random order,
  `KEEP_GOING`), dependencies, git hooks and commit messages; moved from the
  README and updated for the current recipes.
- `docs/src/content/docs/contributing/docs-site.md` `061f43d`: Node.js and pnpm,
  preview, build and link check, reference regeneration, writing pages, the
  versioned build and publishing rules.
- `docs/src/content/docs/contributing/releases.md` `dca1af0`: the release flow,
  commit types, making a release, the first 0.1.0 release, and the one-time PyPI
  Trusted Publisher, `pypi` environment, GitHub Pages and release-please token
  settings.
- `docs/astro.config.mjs` `73e9712`: the sidebar adds the Start here group, FAQ,
  Need Help?, and the Guides and Contributing groups; Overview and the
  autogenerated Reference group are unchanged. `components` adds `PageTitle`.

Assessed with no change:

- Generated `docs/src/content/docs/reference/*.md`: produced by
  `scripts/generate_reference_docs.py` and checked by Developer and Tester
  (AC-032). The guides link to them and were cross-checked against them; no
  disagreement found.
- `pyproject.toml` metadata: the description and classifiers already describe
  the survey release ("Development Status :: 3 - Alpha", Python 3.13 and 3.14).
- `.template.env`, `examples/config.json`, `examples/config.yaml`: match the
  settings and keys the docs describe.
- `AGENTS.md` and `CLAUDE.md` (only the managed STANDARDS block), `CHANGELOG.md`
  (release-please output) and the issue templates: nothing in this cycle changes
  them.

Behavior checked before writing (source read at HEAD `9273074`): `cli.py`,
`api.py`, `errors.py`, `__init__.py`, `pipeline/runner.py`, `config/loading.py`,
`config/schemas.py`, `costs/budget.py`, `providers/uploads.py`,
`providers/profiles.py`, `surveying/facts.py`, `surveying/survey.py`,
`surveying/validators.py`, `surveying/prompts.py`, `report/html.py`,
`report/images.py`, the workflows, `justfile`, `docs/package.json` and
`docs/scripts/`, and the design's known limits.

## Checks and Applicability

All commands ran on macOS (Darwin 25.6.0, arm64) on 2026-11-19, from the repo
root unless noted, against the saved content listed above. Commands that need
uv's cache ran outside the Claude Code sandbox, which blocks `~/.cache/uv`.

- Examples run against the package (`.venv`, pydelity `0.0.1` from this
  checkout) in a scratch folder with the `tests/fixtures/pdfs/irs_form_w9.pdf`
  fixture copied as `document.pdf`, with no real API key and no input terminal,
  so nothing reached a provider:
  - CLI with no key: exit 2, `ANTHROPIC_API_KEY is not set`; `run.json`,
    `pdf_facts.json`, `report.html` and `report/pages/` written.
  - CLI with a dummy key and stdin from `/dev/null`: the estimate lines quoted
    in `first-survey.md` and `costs.md` (about $0.36, at most $2.90, up to 3
    requests), then `Input is not a terminal ...`, exit 3, status `stopped`.
  - Every CLI example in `command-line.md` and `configuration.md`
    (`--language`/`-l`, `--instructions`, `--model openai:gpt-6.2-astra`,
    `--output-dir`, `--config` with and without a PDF argument): each parsed,
    reached the cost question with the expected model and output folder, and
    exited 3. The config file's relative `pdf` resolved against the file's
    folder when run from another folder, and the default output folder was in
    the current folder.
  - Invalid settings: the two-line message quoted in `configuration.md`
    (`max_cost` and an unknown key), exit 2. `python -m pydelity --version` and
    `pydelity --version`: `pydelity 0.0.1`.
  - Python: `measure`, `estimate` (Decimal results), `load` after `measure` only
    (record and survey `None`), `estimate(config={...})`, nested `advanced`
    keywords, `RuntimeError` from `measure` inside a running loop with the
    "await `pydelity.ameasure(...)`" message, `ameasure`, `BudgetExceededError`
    from `run(max_cost=0.01)` before any request (run status `stopped`, warning
    `max_cost_exceeded`), float `max_cost`, custom prices in `advanced.models`,
    the unpriced-model warning and `over_max_cost` for it, and `expiry_hours`
    outside each provider's range (1 to 720 for OpenAI, 1 to 2,160 for
    Anthropic) as a `ConfigError`. All matched the docs.
  - Not run: a paid survey. Completed-run output (the summary line and review
    issues) is described from the code's log formats and the Tester's evidence,
    with no invented figures.
- `just lint-markdown` (outside the sandbox): Prettier formatted the 12 new or
  changed pages and the README; markdownlint then reported one issue, MD060 in
  this record's inventory table (since replaced by lists). Rerun on the final
  content: Prettier changed only this record's whitespace, markdownlint `Passed`
  on all files, STANDARDS check passed; exit 0.
- `just docs-build` (outside the sandbox), rerun on the final content: 23 pages
  built; `Checked local links and fragments in 23 HTML pages.`; exit 0. Its only
  warning, that the `i18n` collection is empty, does not concern these pages.
  Rerun after the user's overview changes, the FAQ, Need Help? and the sticker
  (with `just lint-markdown`, which passed, exit 0): 25 pages built;
  `Checked local links and fragments in 25 HTML pages.`; exit 0. It warned again
  about `i18n`, and once that no `404` docs entry exists, so Starlight builds
  its own 404 page; neither concerns these pages. The built overview holds the
  sticker and `faq/index.html` does not.
- Sticker inspected in the built site (`astro preview`, in-app browser): dark
  theme at desktop width, light theme at 375 px. At 375 px it first overlapped
  the wrapped title; a wider row gap fixed it, and a rebuild passed (25 pages,
  links checked, exit 0).
- FAQ claim checked: `pydelity` on a test PDF with no API key and no terminal
  (`tests/fixtures/pdfs/japan_official_gazette_2019_extra_9.pdf`, scratch output
  folder, since removed) logged that `ANTHROPIC_API_KEY` is not set, saved
  `pdf_facts.json`, `run.json` and `report.html`, and exited 2.
- Need Help? links: `gh repo view IDinsight/pydelity` reports `PUBLIC` with
  issues enabled; the four form links name the files in
  `.github/ISSUE_TEMPLATE/`.
- `just build` (outside the sandbox): wheel and sdist built;
  `twine check --strict` PASSED for both, so the new README renders as the PyPI
  description; exit 0.
- `node .standards/bin/check.mjs`: "STANDARDS check passed." before any work and
  after formatting.

## Acceptance Criteria Dispositions

Documentation ACs:

- `AC-025`: README now describes the usable survey release; package description
  and classifiers already did. Evidence: README, `just build` twine check.
- `AC-031`: Start here and Guides pages cover install on Windows, macOS and
  Linux, API keys, CLI and Python runs, every output file, spend control and
  reruns. Evidence: the pages, the examples checks and the docs build.
- `AC-032`: Owned by Developer and Tester (generated reference pages,
  verification report). No hand edit; the guides link to and agree with them.
- `AC-033`: Contributing pages cover just recipes, tests, building and
  previewing the docs, and the release procedure with the one-time PyPI and
  Pages settings. Evidence: the pages and the docs build.
- `AC-034`: README quick start and docs-site links present; every command and
  example was run or checked against the code as listed under Checks.
- `AC-047`: README and `guides/configuration.md` point to `examples/`; the files
  themselves are Developer and Tester evidence.

Behavior ACs documented for users, with Tester's verification as the evidence of
behavior:

- `AC-001`, `AC-002`, `AC-004`, `AC-046`: `faq.md`, `outputs.md` (profile,
  proposal, model kept over facts).
- `AC-007`, `AC-008`, `AC-009`: `first-survey.md`, `command-line.md`,
  `configuration.md`.
- `AC-010`, `AC-042`, `AC-043`, `AC-044`: `python.md`.
- `AC-011`, `AC-037`, `AC-041`: `models-and-providers.md`.
- `AC-014`, `AC-015`, `AC-038`, `AC-039`: `costs.md`, `command-line.md`.
- `AC-017`, `AC-018`: `reruns.md`.
- `AC-019`, `AC-020`, `AC-045`: `outputs.md`.
- `AC-040`: `first-survey.md`, `outputs.md` (facts saved before the question).
- `AC-023`, `AC-024`: `install.md` (platforms, Windows install and keys).
- `AC-026`, `AC-029`, `AC-036`: `contributing/releases.md` and
  `contributing/docs-site.md`.
- `AC-027`, `AC-028`, `AC-030`: `contributing/docs-site.md`.
- `AC-021`, `AC-022`: `contributing/development.md` (tests, CI on 3.13 and 3.14,
  wheel check on three systems).

Need no user documentation:

- `AC-005`, `AC-006`: internal correctness and naming; covered by the facts
  reference and Tester evidence.
- `AC-035`: the user's own review of real runs (Tester and user, not
  documentation).

Retired and not documented as current: `AC-003`, `AC-012`, `AC-013`, `AC-016`.

Design notes assigned to Documenter, all addressed: PyMuPDF AGPL where install
is described; upload storage, duration and how to shorten it; sync functions in
Jupyter and the async forms; reading `rotation_differs` and
`page_number_differs`; timed-out requests that may be billed; one run per output
folder.

## Discrepancies, Dependencies, and Remaining Work

`NONE`. No discrepancy between the docs and the code was found. Dependencies on
later owners: the final reviewer assesses these docs; the published site and the
PyPI page exist only after the v0.1.0 release that follows sign-off.

## Resume and Conclusion

- The user reviewed the written docs and asked for changes to the overview, a
  FAQ, a Need Help? page and a comic sticker, all written and checked above.
  They then approved the docs on 2026-11-19 ("Looks good"). No blocking question
  remains.
- Gate rechecked on approval: every written surface and every assessed input
  matches the identities above (git blob and SHA-256 prefixes), HEAD is still
  `9273074`, and the behavior inputs have no uncommitted changes. Every current
  AC has a disposition. No discrepancy, pending guided edit or Documenter-owned
  outstanding obligation remains.
- Selected target and full Documenter gate: complete. Handoff: `FORWARD` to
  `REVIEWING_FINAL` for a `FINAL_DELIVERABLE` review in a fresh Reviewer chat.
  The final reviewer assesses these docs; the published site and the PyPI page
  exist only after the v0.1.0 release that follows sign-off.

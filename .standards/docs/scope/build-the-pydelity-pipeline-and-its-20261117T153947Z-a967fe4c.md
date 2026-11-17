<!-- STANDARDS
Artifact: SCOPE
Cycle: build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c
-->

# pydelity survey step and first working release

## Goal

pydelity will turn (almost) any PDF into a faithful `document.json` with
item-level provenance, and optionally a per-PDF `domain.json`, through six
steps: survey, page extraction, page-break verification, assembly, schema
proposal and projection. This cycle builds step 1, the survey, and ships it as
pydelity's first working release, version 0.1.0.

The survey reads a whole PDF once, measures what Python can measure without a
model, and asks a model for a profile of the document that later steps rely on:
its labels, languages, writing direction, rotated pages, and how content
continues across pages. Every later step depends on that profile, so it comes
first. Because a survey run calls a paid model, the cycle also delivers the run
features any paid step needs: configuration, a CLI and a Python API, input-limit
checks, cost reporting and spend controls, resume, and review output. People on
Windows, macOS and Linux install the release from PyPI and learn to use it from
an official, versioned docs site.

## Constraints

- Target maturity: Level 3 (internally testable) for the library, the CLI, the
  release workflow and the docs site.
- Python 3.13, with Pydantic, pydantic-settings, PydanticAI, loguru and Typer.
  Models are reached through provider APIs via PydanticAI. Both Anthropic and
  OpenAI models must work.
- The PDF path is the only required input. It comes from the CLI or from the
  config file, and the CLI wins. Configuration is one optional JSON or YAML file
  with a small set of global settings and an `advanced:` section.
- Document-type agnostic: no core logic, prompt, profile field or default may
  assume a document type (such as grades, terms, skills or tax lines). No
  hand-written per-document config and no domain Pydantic classes.
  Document-specific knowledge comes only from the survey profile and the user's
  instructions.
- The survey model reads the whole PDF. A PDF over the survey model's input
  limits is rejected with a clear error, never split.
- The CLI shows a cost estimate and asks before spending; `--yes` skips the
  question. There is no default `max_cost`. Cost is reported with no pass/fail
  target.
- Automated tests mock model API calls and make no network calls to model
  providers. Real model runs use the user's own API keys.
- Acceptance of the survey's output rests on the user's review of real runs on
  PDFs of their choice. There is no numeric parity target against KGForEdGlobal.
- The repo setup on `main` stays as it is unless this work needs a change: just,
  prek, Dependabot, zizmor, the Markdown rules (which also cover STANDARDS
  files), one pinned version per tool, exact pins for dev tools and minimum
  versions for runtime dependencies, Conventional Commits, and tooling that
  works where STANDARDS is not installed. "Lint and test" and "TruffleHog secret
  scan" stay required checks on `main`.
- release-please versions, tags and writes `CHANGELOG.md`; the PyPI release is
  published from its GitHub release with Trusted Publishing. The release version
  is 0.1.0 (tag `v0.1.0`): once this cycle is signed off, its work reaches
  `main` as a non-breaking `feat:` commit (the squash-merged pull request's
  title), release-please opens the 0.1.0 release pull request, and accepting
  that pull request publishes 0.1.0 to PyPI.
- The docs site uses Astro with Starlight, following
  [IDinsight/standards](https://github.com/IDinsight/standards): built and
  link-checked on pull requests, versioned by stable release tag, and published
  to GitHub Pages only once the release tag exists.
- Publishing happens after sign-off. The branch merges to `main` only after the
  cycle is signed off and STANDARDS is uninstalled, so the PyPI upload and the
  first docs deployment follow sign-off. In-cycle evidence covers release and
  deployment readiness, not the upload or deployment itself.
- Reuse before rewriting: port KGForEdGlobal's stage 1–3 code into pydelity and
  reuse what fits the survey and this scope; write new or updated pydelity code
  where it does not fit. Ported code meets every other constraint here,
  including the document-type-agnostic rule, and does not carry over the defects
  listed under "Known defects in the source code to design out" in
  `artifacts/design_brief.md`.
- KGForEdGlobal (`/Users/tzz/Projects/private/idi/KGForEdGlobal`) itself is
  read-only: pydelity copies from it but changes nothing in it.

## Non-goals

- Steps 2–6 and their outputs (page files, page-break verdicts, `document.json`,
  the domain schema and `domain.json`), and the KGForEdGlobal-compatibility
  outcomes that depend on them, such as segment IDs and the consumer field
  mapping. Later cycles build them.
- Any change to KGForEdGlobal, and KG, Learning Component or Learning
  Progression logic.
- Automatic splitting or a chunked survey for PDFs over the survey model's input
  limits.
- A default spending limit.
- A hosted service, a web UI beyond the HTML report, telemetry, and other Level
  4 capabilities such as structured audit logging and staging environments.
- just recipes that work for contributors on Windows without a POSIX shell.
  Windows support in this cycle means installing and using pydelity.
- Yanking the `0.0.1` placeholder. That is the user's call on PyPI after the
  working release is live.
- Docs versions for releases before the first working release (`0.0.1` has no
  tag).

## Work

### 1. Survey a PDF

**Intent:** Give later steps a checked, per-PDF profile and the facts behind it,
so that no step needs hand-written per-document rules.

**Done when:**

- `AC-001`: Given only a PDF, the survey writes `pdf_survey.json` holding facts
  measured from the PDF without a model: text-layer quality per page (including
  pages with no text and pages with garbled or control characters), bookmarks,
  form fields with their values (including fillable fields and checkboxes),
  structure tags and their quality, lines repeated across pages, text direction
  per page (including rotated text on pages whose rotation attribute is 0), and
  printed page numbers with their offset from the page index.
- `AC-002`: `pdf_survey.json` holds a model-proposed profile: per-PDF labels,
  each mapped to one role and its allowed kinds and always including `other`;
  languages; writing direction; rotation per page range; continuation notes; and
  start markers.
- `AC-003`: The profile is checked against the measured facts before it is
  accepted: labels map to valid roles and kinds, rotation agrees with the
  measured text direction, the printed-page offset agrees with the printed page
  numbers, and proposed artifacts account for the repeated lines. A failed check
  is sent back to the model; a check that still fails after the retries is
  recorded on the review list.
- `AC-004`: Optional user instructions and document languages add to the profile
  but never bypass its checks.
- `AC-005`: The measured facts are correct on test PDFs that cover two-column
  right-to-left text, Chinese or Japanese text, a fillable form with checkboxes,
  rotated content, pages with no text layer, and PDFs with and without bookmarks
  and structure tags.
- `AC-006`: Core code, prompts, profile fields and defaults name no document
  type or domain concept, hold no language-specific word lists, and contain no
  per-document rules or domain Pydantic classes.

**Depends on:** None.

### 2. Run the survey from the CLI or from Python

**Intent:** Let a user run the survey with nothing but a PDF path, and let code
call it without the CLI.

**Done when:**

- `AC-007`: `pydelity <pdf>` runs the survey with no config file, reading
  provider API keys from the environment.
- `AC-008`: An optional JSON or YAML config file sets the PDF path, the global
  settings that apply to the survey (including instructions, languages, output
  folder, model, `max_cost` and `overwrite`) and an `advanced:` section. A PDF
  path given on the CLI wins over the config file's.
- `AC-009`: Invalid settings stop the run before any model call with a message
  naming each invalid setting.
- `AC-010`: The run and the survey step can be called from Python without the
  CLI. Importing pydelity needs no environment settings and logs nothing unless
  the caller asks for logs.
- `AC-011`: The survey runs with an Anthropic model or an OpenAI model, chosen
  by setting.

**Depends on:** 1.

### 3. Control spend and input size

**Intent:** Stop the user from paying for a call that cannot succeed, and show
what a run costs before and after it spends.

**Done when:**

- `AC-012`: Before any model call, the whole PDF's page count and file size are
  checked against the survey model's PDF input limits. A PDF over either limit
  stops the run with an error that names the model, the limit and the PDF's
  value and tells the user to split the PDF or choose a model with higher
  limits.
- `AC-013`: Known PDF input limits ship for the default survey models and every
  survey model the docs name. The user can override a model's limits under
  `advanced:`. A model with no known limits gets a warning and the call goes
  ahead.
- `AC-014`: Every model call is recorded in a per-call cost ledger with its
  token usage and cost, and each run reports its cost per step and in total.
- `AC-015`: Before spending, the CLI shows a cost estimate and asks to continue.
  `--yes` skips the question, a non-interactive run without `--yes` stops before
  spending, and the Python API never prompts.
- `AC-016`: When `max_cost` is set, it counts all spend recorded in the output
  folder, including earlier and resumed runs, and the run stops in a resumable
  state rather than exceed it.

**Depends on:** 1, 2.

### 4. Resume, rerun and review a run

**Intent:** Make reruns cheap and safe, and show the user what needs a human
look.

**Done when:**

- `AC-017`: Rerunning with unchanged inputs reuses a complete, valid
  `pdf_survey.json` without a model call. A changed input (the PDF,
  instructions, languages, model or a setting the survey uses) reruns the
  survey, and `overwrite` reruns it regardless.
- `AC-018`: An interrupted run (an error, a timeout or Ctrl+C) leaves no
  half-written output, and a damaged output is regenerated on the next run.
- `AC-019`: Issues left after retries are recorded in `run.json` with their
  step, page where one applies, and the check that failed, and the CLI prints a
  summary of them at the end of the run.
- `AC-020`: Each run writes an HTML report showing page images with the survey's
  page-level findings and any regions it marks, together with the profile, the
  run's cost and the review list.

**Depends on:** 1, 2.

### 5. Test across providers, Python versions and platforms

**Intent:** Prove the survey and its run features work without paying for model
calls, on every platform and Python version the release supports.

**Done when:**

- `AC-021`: Automated tests cover the survey, configuration, the CLI and Python
  API, the spend and input-limit controls, resume and the review output, with
  both providers' responses mocked and no network calls to model providers.
- `AC-022`: CI runs the tests on Python 3.13 and Python 3.14, and "Lint and
  test" and "TruffleHog secret scan" still gate merges to `main`.
- `AC-023`: On Windows, the built wheel installs with pip, and the `pydelity`
  command and the Python API run the survey with mocked model responses.

**Depends on:** 1, 2, 3, 4.

### 6. Prepare the first working release

**Intent:** Ship the survey to PyPI as pydelity's first working release, version
0.1.0, as soon as the cycle is signed off and merged.

**Done when:**

- `AC-024`: The built wheel installs with pip into a clean environment and
  provides the package, its runtime dependencies and the `pydelity` command, and
  the wheel and sdist pass a package metadata check.
- `AC-025`: The package's description, classifiers and README describe a usable
  survey release rather than a name-reserving placeholder.
- `AC-026`: A release workflow, started by release-please's GitHub release,
  builds the wheel and sdist and publishes them to PyPI with Trusted Publishing
  and least-privilege permissions, and zizmor reports no findings for it.
- `AC-036`: The release setup produces version 0.1.0: with the release-please
  manifest at `0.0.1` and no earlier release tag, this cycle's work reaching
  `main` as a non-breaking `feat:` commit makes release-please open a release
  pull request for 0.1.0 (tag `v0.1.0`), and the GitHub release it creates when
  accepted starts the PyPI release workflow.

**Depends on:** 5.

### 7. Build the docs site

**Intent:** Give pydelity an official docs site, versioned by release, built the
way IDinsight/standards builds its own.

**Done when:**

- `AC-027`: An Astro Starlight docs site builds from the repo locally and in CI
  on every pull request, and a broken internal link fails the CI build.
- `AC-028`: The combined build serves the latest stable release at the site root
  and every stable release from the first working release onward at its own
  versioned path, with a version selector.
- `AC-029`: A docs workflow deploys the combined site to GitHub Pages from
  `main` and from release tags, and only once the package version on `main` has
  a release tag; zizmor reports no findings for it.
- `AC-030`: The docs tooling follows the repo's conventions: one pinned version
  per tool, version updates from Dependabot, and docs pages covered by the
  Markdown rules.

**Depends on:** None for the site; the versioned build and deployment depend on
6 for release tags.

### 8. Write the docs

**Intent:** Let another engineer install, run and understand the survey, and let
a maintainer contribute and release, from the docs alone.

**Done when:**

- `AC-031`: Following the docs site alone, a user on Windows, macOS or Linux can
  install pydelity from PyPI, set provider API keys, run the survey from the CLI
  and from Python, find and read `pdf_survey.json`, `run.json`, the cost ledger
  and the HTML report, control spend, and resume or rerun a run.
- `AC-032`: The docs site's reference pages cover every configuration setting
  (including `advanced:`), every CLI option, the public Python API and every
  `pdf_survey.json` field, and match the code.
- `AC-033`: The contributor pages cover local development with the just recipes,
  the tests, building and previewing the docs site, and the release procedure,
  including the one-time PyPI Trusted Publisher and GitHub Pages settings.
- `AC-034`: The README gives a short install-and-run quick start and links to
  the docs site, and every command and code example in the README and the docs
  matches the release's actual behavior.

**Depends on:** 1–7.

### 9. User review of real survey runs

**Intent:** Confirm the survey's output is useful on real documents, which
mocked tests cannot show.

**Done when:**

- `AC-035`: The user runs the survey with real Anthropic and OpenAI models on
  PDFs of their choice, including at least one two-column right-to-left
  document, one Chinese or Japanese document, one tax or fillable form, one
  slide deck or image-heavy PDF, and CAPS, reviews the output and the HTML
  report, and accepts it, with every issue they raise resolved.

**Depends on:** 1, 2, 3, 4.

## Assumptions

- This cycle builds only step 1, so `pydelity <pdf>` runs the survey. Later
  cycles extend the default run through all six steps, with a setting to stop
  after `document.json`.
- Test PDFs for the new document types are public documents chosen with the
  user's approval.
- The user makes the one-time settings the repo cannot: a PyPI Trusted Publisher
  for `pydelity`, and GitHub Pages set to deploy from GitHub Actions.
- Architect picks the default model for the survey, the final `kind` and `role`
  lists that labels map to, and how the survey's checks are carried out.

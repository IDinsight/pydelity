<!-- STANDARDS
Artifact: ARCHITECTURE
Cycle: build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de
-->

# Technical Design: pydelity repo setup and PyPI name

Design mode: `FOUNDATION`.

## Context

The scope covers two things: getting the repo into shape for a Python 3.13
library with a Typer CLI that ships to PyPI (`AC-042` to `AC-045`, `AC-041`,
`AC-002`), and reserving `pydelity` on PyPI with a placeholder release
(`AC-040`). Pipeline code is out of scope; package code stays at empty modules
and a smoke test.

Two user reworks on 2026-11-16 shape this design:

- `AC-041`: Markdown linting and formatting cover every Markdown file, STANDARDS
  files included, as long as the changes they make to STANDARDS files are
  whitespace or line wrapping only and `node .standards/bin/check.mjs` still
  passes. The scope records that the user accepts cosmetic formatting of shipped
  framework files, which the protocol otherwise treats as changed only by
  installation or upgrade.
- After the placeholder was published: just replaces Make as the task runner and
  prek replaces pre-commit as the hook runner (`AC-042`, which replaces the
  retired Make and pre-commit condition, and `AC-043`), Dependabot keeps pinned
  versions current (`AC-044`), and zizmor checks the GitHub Actions workflows
  (`AC-045`). This revision replaces the Makefile and pre-commit in decisions 1,
  3 and 8 to 10, turns the exact uv pin into a lower bound, and adds decisions
  11 to 13.

The repo as it stands (observed 2026-11-16 on `tz6/port-over` at `73739f7`):

- Build Plan steps 1 and 2 are done (development plan `DEV-001` to `DEV-003` and
  `DEV-011`): root `src/` layout, root `pyproject.toml`, `uv.lock`
  (`revision = 5`), `.python-version` (`3.13`), one smoke test, and
  `pydelity 0.0.1` published on PyPI under the user's account and verified.
- The root `Makefile` has `install` (`uv sync --locked`), `test`, `clean` (still
  running `pnpm store prune`) and an unpinned `npx prettier` `lint-markdown`.
  `[tool.uv] required-version` is `==0.13.8`. The dev group still holds the
  scaffold's tools, `pre-commit==4.3.0` among them; the Python toolchain the
  user chose (Ruff, ty, interrogate) is pending in the development plan.
- `.pre-commit-config.yaml` still names `backend/` and `--project python`, and
  its comments mention pre-commit. The only workflow is
  `.github/workflows/trufflehog-pr.yml`. There is no `.github/dependabot.yml`.
- Markdown evidence (2026-11-16, checked in a copy of the repo):
  - With prettier 3.10.1, `proseWrap: always` and `printWidth: 80`, every
    shipped framework file and `AGENTS.md` and `CLAUDE.md` are already
    formatted. Only role-written records change, some in more than whitespace
    (prettier pads table delimiter rows). Prettier 3.6.2 also added a trailing
    blank line to `AGENTS.md` and `CLAUDE.md`, so output depends on the prettier
    version.
  - After formatting, prettier's changes left `check.mjs` passing.
  - markdownlint-cli2 0.24.1 with line length off still reports `MD025`,
    `MD036`, `MD041` and `MD026` in shipped skill templates, the user-style
    files and `.github/pull_request_template.md`. Shipped files also re-enable
    `MD013` through inline `markdownlint-enable` comments, so turning it off in
    the repo config is not enough on its own.
- Tool evidence (2026-11-16):
  - Latest on PyPI, all installable on Python 3.13: `rust-just` 1.59.0 (a wheel
    that ships the `just` binary), `prek` 0.5.11 and `zizmor` 1.32.0.
  - prek reads `.pre-commit-config.yaml`, `.pre-commit-config.yml` or its own
    `prek.toml`, and adds `repo: builtin` hooks that pre-commit lacks. For
    `language: node` hooks it downloads Node when needed and supports
    `language_version` and `additional_dependencies`. In a scratch repo, prek
    0.5.11 failed a run whose hook modified a file, as pre-commit does.
  - Dependabot supports the `uv`, `pre-commit` and `github-actions` ecosystems.
    The `pre-commit` updater reads `.pre-commit-config.yaml`, updates each
    remote hook's `rev` and its version comment, and skips `local` and `meta`
    hooks. GitHub's announcement does not say it updates
    `additional_dependencies` or `language_version`. Every updater accepts a
    `cooldown` (`default-days` plus per-semver keys); GitHub's default is 3
    days.
  - Dependabot's uv updater runs its own uv, 0.13.7 in `dependabot-core` `main`
    on 2026-11-16. When the project's `required-version` excludes that uv, the
    update fails with `ToolVersionNotSupported` (the
    `lock_file_error_handler.rb` source and its spec). With today's `==0.13.8`,
    every uv update would fail.
  - zizmor runs its online audits (`impostor-commit`,
    `known-vulnerable-actions`, `ref-confusion`, `stale-action-refs`) only when
    it finds a GitHub token in `GH_TOKEN`, `GITHUB_TOKEN` or
    `ZIZMOR_GITHUB_TOKEN`, and runs offline otherwise. Given the repo root, it
    audits the workflows and `.pre-commit-config.yaml`, and it also audits
    `.github/dependabot.yml`: `dependabot-cooldown` flags `default-days` under 7
    by default, and `dependabot-execution` flags
    `insecure-external-code-execution: allow`. Findings can be ignored through
    `rules.<id>.ignore` in `zizmor.yml` or `.github/zizmor.yml`, or with an
    inline `# zizmor: ignore[<id>]` comment that may carry a trailing reason.
  - zizmor 1.32.0, offline, on the repo root: under the default `regular`
    persona it reports one `artipacked` finding in `trufflehog-pr.yml` (checkout
    without `persist-credentials: false`) and counts two more as suppressed.
    Under `pedantic` or `auditor`, those two show as `anonymous-definition` and
    `concurrency-limits`.
- Local tools: Python 3.13.9, Node 23.10.0; the user's uv is 0.13.8. Remote:
  `git@github.com:IDinsight/pydelity.git` (public). `LICENSE` is MIT.

User decisions made during architecture (2026-11-16):

- The package moves to a root `src/` layout. The user first leaned towards
  keeping `backend/` for a possible future web UI; they chose the root layout
  after weighing that a UI would sit beside the library as `frontend/` (or
  `web/`) and import it.
- `requires-python = ">=3.13"`, with no upper cap.

`.standards/CONTEXT.md` describes the repository before Developer started; this
design is authoritative for the planned changes. No project references exist
under `.standards/project-references/`.

## Decision

1. **Root `src/` layout.** `pyproject.toml`, `uv.lock`, `.python-version`,
   `justfile`, `README.md` and `LICENSE` sit at the repo root; the package is
   `src/pydelity/` and tests are `tests/`. `backend/` and `cicd/` are removed.
   The root `README.md` is the PyPI project page. A future UI goes in
   `frontend/` beside the library.
2. **Build backend: setuptools (≥ 77).** It is already in place, its default
   sdist only picks up the package and standard top-level files, and ≥ 77
   supports SPDX `license = "MIT"` with `license-files`. Static version in
   `pyproject.toml`.
3. **One locked dev environment, one pin per tool.** `uv.lock` is the only lock.
   Every Python tool, just (`rust-just`), prek and zizmor included, is in the
   PEP 735 `dev` dependency group, so it never appears in published metadata and
   Dependabot's uv updater keeps it current. Recipes, local hooks and CI run
   these tools from that environment through `uv run`. Each tool has exactly one
   pinned version in the repo: a Python tool in the dev group (never also as a
   hook `rev`), a remote hook by its `rev`, a Node package in its hook's
   `additional_dependencies`.
   - `[tool.uv] required-version` is a lower bound (`>=`), no longer an exact
     pin, because Dependabot's uv updater fails on any project whose
     `required-version` excludes the uv it runs. The bound is the oldest uv that
     handles this lock and the `[tool.uv]` settings in use, and no newer than
     the uv Dependabot runs. CI installs one exact uv that meets the bound,
     named in the workflow, so CI results do not shift with uv releases.
4. **Python.** `requires-python = ">=3.13"`. `.python-version` pins `3.13` so
   local and CI environments use 3.13 even when a newer Python is installed. CI
   tests 3.13 only.
5. **No runtime dependencies and no console script this cycle.** Nothing imports
   the KGForEdGlobal stack yet, so `[project].dependencies` is empty. The next
   cycle adds dependencies as code needs them, plus the Typer CLI and its
   `[project.scripts]` entry. The package ships a `py.typed` marker.
6. **Placeholder version `0.0.1`, a final release.** A pre-release such as
   `0.0.1.dev0` is avoided because installers skip pre-releases in some cases. A
   corrected placeholder takes `0.0.2`, `0.0.3` and so on. The working release
   in the next cycle is `0.1.0` or higher.
7. **The user uploads the placeholder by hand** from their own terminal with
   `uv publish` (or `twine upload`), entering their own PyPI token when asked or
   exporting it in that shell only. Agents never see, type or store the token. A
   release workflow with PyPI Trusted Publishing comes with the working release
   in the next cycle.
8. **CI.** A GitHub Actions workflow runs the `AC-042` commands on Python 3.13
   for pull requests to `main` (Dependabot's included) and pushes to `main`. The
   TruffleHog workflow stays. Third-party actions are pinned by commit SHA with
   a version comment, as the existing workflow does, which is the form
   Dependabot's `github-actions` updater maintains. Every workflow passes zizmor
   (decision 13).
9. **Markdown: one formatter and one linter over every Markdown file.** Prettier
   formats and markdownlint-cli2 lints every Markdown file that git tracks or
   would track, STANDARDS files included. Each tool has one exact version and
   one repo config, shared by the just recipes, the prek hooks and CI.
   - Prettier uses `proseWrap: always` and `printWidth: 80`, the format
     STANDARDS ships in, so shipped files stay byte-identical and upgrades cause
     no churn.
   - A **whitespace guard** sits between prettier and STANDARDS files: a
     STANDARDS file is rewritten only when prettier's output differs from it in
     whitespace alone. Otherwise the file is left untouched and reported as a
     warning. Failing instead would block every phase on edits that only the
     record's owning role or a framework upgrade may make.
   - The Markdown format recipe and hook run `node .standards/bin/check.mjs`
     after formatting and fail if it fails.
   - markdownlint only checks and never fixes. Its config is tuned so every
     current Markdown file passes, and every deviation from markdownlint's
     defaults carries a comment giving its reason. Violations fail for every
     file. Shipped files cannot be edited, so a violation in one is settled by
     tuning the config.
10. **Other tooling leaves STANDARDS files alone.** Every other formatter or
    hook that can write files excludes `.standards/`, `.agents/`,
    `.claude/skills/`, `.claude/settings.json`, `.codex/hooks.json`, `AGENTS.md`
    and `CLAUDE.md`. That covers trailing-whitespace, end-of-file-fixer, `--fix`
    linters and any prettier use on non-Markdown files. The two settings files
    come from the STANDARDS installation (`.standards/INSTALLATION.json`).
    Read-only checks such as detect-secrets may scan them.
11. **just is the task runner; the Makefile goes.** A root `justfile` is the
    single entry point, with `install`, the lint recipes, `test` and `clean`.
    Recipes call tools through `uv run`, never a globally installed copy. To
    start from a clean checkout, a person needs git, a uv that meets
    `required-version`, and any `just` on `PATH` (for example from
    `uv tool install rust-just` or Homebrew) at or above the minimum version the
    README names for the justfile. CI runs the locked just with
    `uv run --locked just <recipe>`, so the version CI checks is the one
    Dependabot maintains.
12. **prek is the hook runner; its config stays `.pre-commit-config.yaml`.**
    `prek` replaces `pre-commit` in the dev group. The config stays in YAML at
    `.pre-commit-config.yaml`, not `prek.toml`, because that is the file
    Dependabot's `pre-commit` updater and zizmor read. It uses only remote repos
    (by URL and `rev`), `local` hooks and `meta` hooks. prek's `repo: builtin`
    hooks stay out, since those other readers do not know them. The file name
    and the `pre-commit/pre-commit-hooks` repo are names, not `pre-commit`
    commands, so they do not conflict with `AC-043`.
13. **Dependabot and zizmor.**
    - `.github/dependabot.yml` has one updater for each kind of pin Dependabot
      supports in this repo: `uv`, `pre-commit` and `github-actions`, each for
      directory `/`. Each sets a `cooldown` with `default-days` of at least 7
      (zizmor's default minimum), and none allows insecure external code
      execution. Schedule, grouping and pull-request limits are Developer's
      choice with the user.
    - zizmor runs as a lint recipe and as a local prek hook over the repo root,
      which covers every workflow, any action definition, the hook config and
      the Dependabot config. It runs check-only, never with `--fix`, and with
      the `auditor` persona, because the lower personas hide findings by design.
      Locally it runs offline unless the person has a GitHub token in their
      environment; CI gives it the job's read-only token, so the online audits
      run there too.
    - A finding is fixed rather than hidden wherever possible. One that is
      accepted instead is ignored for that finding only, with an inline
      `# zizmor: ignore[<id>]` comment or a `rules.<id>.ignore` entry in a
      single zizmor config file, and its reason is written beside it. No audit
      is disabled, and no severity or confidence filter narrows the run.

The lint toolchain for Python, env templates, `.envrc`, `.gitignore` contents,
recipe names beyond those above, and git hook installation are settled during
the interactive setup between the user and Developer, within the contracts
below.

## Acceptance Coverage

- `AC-042`: Decisions 1, 3 to 5 and 8 to 12; the dev-environment, tooling,
  Markdown and CI contracts below.
- `AC-043`: Decisions 11 and 12; the tooling contract below.
- `AC-044`: Decisions 3, 8 and 13; the Dependabot contract below.
- `AC-045`: Decisions 8 and 13; the zizmor and CI contracts below.
- `AC-002`: No architectural impact. Satisfaction depends on the user's sign-off
  of the repo setup during Developer's interactive work, before any pipeline
  code is written. This design adds no pipeline modules.
- `AC-040`: Decisions 1, 2 and 4 to 7; the distribution and credential contracts
  below. Satisfied by the published `0.0.1`.
- `AC-041`: Decisions 9 and 10; the Markdown contract below.

## Components

- `src/pydelity/`: the import package. This cycle it holds only module
  docstrings and `py.typed`; empty subpackages are optional.
- `tests/`: pytest suite with at least one smoke test of the installed package.
- `pyproject.toml`: project metadata, build system, dependency groups and tool
  settings. The single source of package metadata, the version and every Python
  tool's pin.
- `uv.lock` and `.python-version`: the locked dev environment and its Python.
- `justfile`: the root entry point for `install`, the lint recipes, `test` and
  `clean`. It replaces the `Makefile`.
- `.pre-commit-config.yaml`, run by prek: generic file checks, secret detection,
  Markdown formatting and linting, zizmor, and local hooks that run the locked
  Python tools.
- Markdown format runner (`CANDIDATE` under `scripts/`): runs the pinned
  prettier over the Markdown file list, applies the whitespace guard to
  STANDARDS files, then runs `check.mjs`. Used by the Markdown format recipe and
  hook. Developer picks the language; Node fits, since prettier needs Node
  anyway.
- Prettier and markdownlint-cli2 configs at the repo root (for example
  `.prettierrc` and `.markdownlint-cli2.yaml`).
- `.github/workflows/`: the new CI workflow and the existing TruffleHog
  workflow.
- `.github/dependabot.yml`: the three updaters.
- zizmor config (`CANDIDATE` `.github/zizmor.yml`): only if a finding has to be
  ignored in config rather than inline.

## Interfaces and Contracts

### Published distribution (`AC-040`)

| Field             | Value                                                                                        |
| ----------------- | -------------------------------------------------------------------------------------------- |
| Name              | `pydelity`                                                                                   |
| Version           | `0.0.1` (later placeholders `0.0.N`)                                                         |
| Description       | Says the package is under development and not yet usable                                     |
| Long description  | Root `README.md`, opening with the same statement                                            |
| Classifiers       | `Development Status :: 1 - Planning`, `Programming Language :: Python :: 3.13`               |
| License           | `license = "MIT"`, `license-files = ["LICENSE"]`                                             |
| `requires-python` | `>=3.13`                                                                                     |
| Dependencies      | None                                                                                         |
| Entry points      | None                                                                                         |
| Artifacts         | `pydelity-0.0.1.tar.gz` and a pure-Python `pydelity-0.0.1-py3-none-any.whl`, from `uv build` |

Distribution contents are an allowlist. The wheel holds only `pydelity/` (with
`py.typed`) and its metadata. The sdist adds `pyproject.toml`, `README.md`,
`LICENSE` and, optionally, `tests/`. Neither may contain `.standards/`,
`.agents/`, `.claude/`, `.codex/`, `artifacts/`, `graveyard/`, `.idea/`,
`.github/` or any `.env*` file. `artifacts/design_brief.md` is internal material
and must never be published.

Author, maintainer and project URL fields are public on PyPI. Developer confirms
them with the user; project URLs point at the GitHub repo only if it is or will
be public.

### Credentials

PyPI tokens never appear in tracked files, the justfile, CI configuration,
`.env*` files or a `.pypirc` in the repo. `dist/` and build output are
gitignored. The first upload of a new project needs an account-scoped token,
because a project-scoped token cannot exist before the project does. The CI
token zizmor uses is the job's own `github.token` with read-only permissions; no
personal token is stored in the repo or its secrets for it.

### Dev environment (`AC-042`)

- Prerequisites on a clean checkout: git, network access, a uv that meets
  `required-version`, and a `just` at or above the README's minimum. Nothing
  else: no system Node (prek fetches Node for its Node hooks), no `.env*` file,
  no direnv, no pre-set environment variable.
- `just install` builds the environment from the committed `uv.lock` and fails
  if the lock is out of date with `pyproject.toml` (`uv sync --locked`
  semantics).
- The project itself is installed into that environment from `src/`. Tests
  import `pydelity` as installed; no `pythonpath` or `sys.path` entry for `src`
  may hide a packaging error.
- `just test` needs no env file or provider key and runs at least one test.
  Pytest configuration only uses options and markers whose plugins are in the
  dev group and are registered.

### Tooling (`AC-042`, `AC-043`)

- Python lint, format and type tools, just, prek and zizmor come from the dev
  group only. Recipes and local hooks call them through `uv run`, so recipes,
  hooks and CI run the same versions. External hook repos are pinned by `rev`.
- No tool is pinned twice. A tool in the dev group is not also a remote hook
  repo, so detect-secrets (today both a dev-group pin and a hook `rev`) keeps
  one of the two.
- Every path that a recipe, hook, script or workflow names exists in the layout.
  Nothing refers to `backend/`, `cicd/` or `frontend/`.
- There is no `Makefile`, and `pre-commit` is not in the dev group. No README,
  workflow, script, recipe, hook entry or config comment runs a `make` or
  `pre-commit` command or tells anyone to. They name `just` and `prek` instead.
- No formatter or hook except the Markdown format runner writes to a STANDARDS
  path (decision 10).

### Markdown (`AC-041`, `AC-042`)

- **File set:** every `*.md` file git tracks or would track. No ignore file or
  hook `exclude` leaves out STANDARDS paths.
- **Versions:** prettier and markdownlint-cli2 are each pinned to one exact
  version, the same in recipes, hooks and CI; the Makefile's unpinned
  `npx prettier` goes with the Makefile. Developer picks the versions; any
  prettier version must leave the shipped STANDARDS files unchanged, as 3.10.1
  does.
- **Whitespace guard:** for each STANDARDS file, compare the file with
  prettier's output after deleting all whitespace from both. If they match,
  write prettier's output. If not, leave the file byte-identical and print its
  path and the reason as a warning. Project files get prettier's output
  unconditionally.
- **Check after format:** `node .standards/bin/check.mjs` runs after formatting,
  in the same recipe and hook; a failure fails them.
- **Linting:** markdownlint-cli2 runs with `fix` off, over the same file set and
  one root config. Every rule disabled or changed from the defaults has a
  comment in the config saying why. The config must hold even where shipped
  files re-enable rules through inline comments (for example by setting
  `noInlineConfig` or by setting rule options rather than switching rules off).
- **Hooks:** a hook that rewrites files fails the prek run, so formatted files
  must be re-staged before a commit goes through.

### Dependabot (`AC-044`)

Every kind of pinned version in the repo, and what keeps it current:

| Pin                                                        | Kept current by                               |
| ---------------------------------------------------------- | --------------------------------------------- |
| Dev-group packages in `pyproject.toml` and `uv.lock`       | Dependabot `uv`                               |
| Remote hook `rev` values in `.pre-commit-config.yaml`      | Dependabot `pre-commit`                       |
| Action commit SHAs and version comments in workflows       | Dependabot `github-actions`                   |
| `[tool.uv] required-version` and CI's exact uv version     | By hand (Dependabot has no updater)           |
| Node `language_version` and `additional_dependencies` pins | By hand (the `pre-commit` updater skips them) |

- `.github/dependabot.yml` is `version: 2`, with the three updaters, each with
  `directory: "/"`, a schedule, and `cooldown.default-days` of 7 or more. It has
  no `insecure-external-code-execution: allow`, and it passes zizmor.
- A pin kept by hand is changed on purpose, never implicitly. A comment next to
  each says so.
- `required-version` stays at or below the uv that Dependabot's updater runs. If
  a uv update from Dependabot fails because the running uv is excluded, the
  bound is lowered rather than the updater removed.
- Pull requests from Dependabot run the same CI as any other pull request.

### zizmor (`AC-045`)

- Input: the repo root, so zizmor collects every workflow under
  `.github/workflows/`, any action definition, `.pre-commit-config.yaml` and
  `.github/dependabot.yml`.
- Options: `--persona=auditor`; no `--min-severity`, `--min-confidence`, `--fix`
  or `--no-online-audits`; no `rules.<id>.disable`.
- Result: zizmor exits successfully. Its summary counts as suppressed only
  findings ignored by an inline comment or a config entry that has a written
  reason beside it.
- Token: the CI step that runs zizmor sets `GH_TOKEN` to `github.token`; local
  runs need no token and run the offline audits.

### CI (`AC-042`, `AC-045`)

The workflow runs on `ubuntu-latest` with Python 3.13 and one exact uv version
that meets `required-version`. It runs `just install`, every lint recipe,
`just test` and `prek run --all-files`, each through `uv run --locked`, and
fails if any of them fails. A hook that modifies files counts as a failure, so
formatting is enforced even if a lint recipe writes fixes. Permissions are
`contents: read`. Both workflows pass zizmor under the contract above; for
example `actions/checkout` sets `persist-credentials: false`, and jobs carry
names and concurrency limits.

## Data and Control Flow

Placeholder release (done on 2026-11-16, `DEV-002` and `DEV-003`):

1. Repo is in the root layout with the `AC-040` metadata and README.
2. `uv build` writes the sdist and wheel to `dist/`.
3. Pre-upload checks: `twine check --strict` on both archives, a listing of both
   against the contents allowlist, and an install of the wheel into a fresh
   Python 3.13 venv followed by `import pydelity`.
4. The user gives the go-ahead and runs the upload from their own terminal with
   their own token.
5. Post-upload check: `https://pypi.org/project/pydelity/` shows the
   under-development text, and in a fresh Python 3.13 venv
   `pip install pydelity` installs `0.0.1`.
6. The user revokes the account-scoped token or replaces it with a
   project-scoped one.

Dependency updates:

1. On its schedule, Dependabot checks each updater's pins and, once a release
   has passed the cooldown, opens a pull request: `uv` rewrites `pyproject.toml`
   and `uv.lock`, `pre-commit` rewrites a hook `rev`, `github-actions` rewrites
   an action SHA and its comment.
2. CI runs the `AC-042` commands on that pull request, so a new tool version
   that breaks a recipe, a hook, the Markdown format or zizmor fails there.
3. The user reviews and merges. Hand-kept pins are bumped in ordinary pull
   requests through the same CI.

## Technical Acceptance Criteria

- `AC-042`: `pyproject.toml`, `uv.lock`, `.python-version` (3.13) and the
  `justfile` are at the repo root; `backend/` and `cicd/` are gone; the package
  is at `src/pydelity/`.
- `AC-042`: `just install` on a clean checkout creates the environment from the
  committed lock with no `.env*` file and no system Node, and fails on a stale
  lock.
- `AC-042`: At least one test imports `pydelity` as installed in the project
  environment, with no `src` path injection, and `just test` runs it with no
  environment setup.
- `AC-042`: Recipes, local hooks and CI use one locked set of tool versions,
  every tool is pinned exactly once, and no recipe, hook, script or workflow
  names a missing path.
- `AC-042`: CI runs `just install`, every lint recipe, `just test` and
  `prek run --all-files` on Python 3.13 for pull requests and pushes to `main`,
  fails when any fails, and pins third-party actions by SHA.
- `AC-042`: `required-version` is a lower bound that admits the uv Dependabot
  runs, and CI installs one exact uv that meets it.
- `AC-043`: No `Makefile` exists, `pre-commit` is not in the dev group, and no
  README, workflow, script, recipe, hook entry or config comment runs or tells
  anyone to run `make` or `pre-commit`.
- `AC-044`: `.github/dependabot.yml` is valid `version: 2` config with `uv`,
  `pre-commit` and `github-actions` updaters for `/`, each with
  `cooldown.default-days` of at least 7, and none allowing insecure external
  code execution.
- `AC-044`: Every pinned version in the repo is either covered by one of those
  updaters or listed in the design's table as kept by hand, with a comment
  beside the pin.
- `AC-045`: zizmor is in the dev group, runs over the repo root with
  `--persona=auditor` in a lint recipe and a prek hook, and runs in CI with the
  job token so the online audits run.
- `AC-045`: zizmor passes on every workflow, the hook config and the Dependabot
  config, and every finding its summary counts as suppressed is an inline or
  config ignore with a written reason beside it; no audit is disabled and no
  severity or confidence filter is set.
- `AC-040`: The published distribution matches the metadata table, is version
  `0.0.1` (or a later `0.0.N` placeholder), and has no dependencies or entry
  points.
- `AC-040`: Both archives pass `twine check --strict` and contain only the
  allowlisted files.
- `AC-040`: No PyPI credential is in any tracked file, and `dist/` is
  gitignored.
- `AC-041`: The Markdown format and lint steps in the recipes, the prek hooks
  and CI run over every `*.md` file git tracks or would track, STANDARDS paths
  included, with one pinned version and one config per tool.
- `AC-041`: The format step never writes a change to a STANDARDS file that
  differs from the original in anything but whitespace. A file that would need
  such a change is left byte-identical and named in a warning.
- `AC-041`: `node .standards/bin/check.mjs` runs after the format step in the
  same recipe and hook, and its failure fails them.
- `AC-041`: markdownlint never modifies a file, and every Markdown file passes
  it under the repo config.
- `AC-041`: No formatter or hook other than the Markdown format runner modifies
  a STANDARDS path.

## Build Plan

1. **Root layout and packaging.** Done (`DEV-001`). Its `Makefile` targets move
   to the justfile in step 3.
2. **Placeholder release** (`AC-040`). Done (`DEV-002`, `DEV-003`, `DEV-011`).
3. **Task and hook runners** (critical path for `AC-042` and `AC-043`). In one
   step, so the repo always has a working entry point: `MODIFY` `pyproject.toml`
   (add `rust-just`, `prek` and `zizmor` to the dev group, remove `pre-commit`,
   make `required-version` a lower bound) and `uv.lock`; `CREATE` `justfile`
   with `install`, `test`, `clean` and the lint recipes that exist so far;
   `DELETE` `Makefile`; `MODIFY` `.pre-commit-config.yaml` for prek (new paths,
   local hooks through `uv run`, no `--project`, the decision 10 exclusions,
   comments that name prek); `MODIFY` `README.md` with the prerequisites and
   `just` commands.
4. **Interactive setup** (`AC-042`, `AC-041`). With the user: the Python lint
   toolchain; the Markdown format runner, prettier and markdownlint configs and
   pinned versions (decision 9); `scripts/check_env_template.py`, env templates
   and `.envrc`; `.gitignore`; leftovers such as the tracked `.DS_Store`,
   `interrogate_badge.svg` and `pnpm store prune`. Each lands as a recipe and,
   where it applies, a prek hook.
5. **Workflows, Dependabot and zizmor** (`AC-044`, `AC-045`, `AC-042`). The
   zizmor recipe and hook; `CREATE` `.github/dependabot.yml`; `CREATE` the CI
   workflow under `.github/workflows/`; `MODIFY` `trufflehog-pr.yml` until
   zizmor passes; `CANDIDATE` `.github/zizmor.yml` only if a config ignore is
   needed. CI depends on steps 3 and 4; Dependabot and zizmor can start once
   step 3 is in.
6. **Sign-off** (`AC-002`). The user signs off the setup before any pipeline
   code is written.

## Risks and Follow-up

- Dependabot's uv can lag behind the uv people use. If it falls below
  `required-version`, uv updates fail until the bound is lowered. A lock written
  by a different uv patch release may also differ slightly; CI's `--locked`
  check shows it on the Dependabot pull request.
- Dependabot's uv updater raises lower bounds it touches, so it may propose
  raising `setuptools>=77` in `[build-system]`. That bound is set by what the
  build needs; if Dependabot proposes raising it, Developer adds an ignore with
  a comment rather than accepting it.
- Hand-kept pins (the uv bound, CI's uv, Node's `language_version`, prettier) go
  stale unless someone bumps them. A prettier bump can reformat many files at
  once (3.6.2 and 3.10.1 already differ on `AGENTS.md` and `CLAUDE.md`).
- With the job token, zizmor's online audits can fail CI when an advisory is
  published for an action the repo uses, with no repo change. That is intended;
  the fix is a Dependabot or hand update of the action.
- The `auditor` persona allows false positives; each one costs a written ignore.
  With two workflows, that is cheap.
- prek is pre-1.0 (0.5.x). Its behaviour may shift between releases;
  Dependabot's cooldown and the CI run on its pull requests limit the surprise.
- Formatting shipped framework files departs from the protocol rule that only
  installation or upgrade changes them; the user accepted this in the scope.
  Today no shipped file changes. If a later STANDARDS release ships files
  prettier would rewrap, they will differ from upstream (whitespace only) until
  the next upgrade replaces them.
- Role-written records that prettier would change beyond whitespace stay
  unformatted and show up as warnings until their owning role rewrites them. A
  markdownlint violation in a new record fails the prek run until its owner
  fixes it or the config is tuned.
- PyPI versions are permanent. A mistake in `0.0.1` can only be fixed with
  `0.0.2`.
- `>=3.13` lets Python 3.14 users install versions tested only on 3.13. The next
  cycle can add 3.14 to CI.
- Next cycle: runtime dependencies, the Typer CLI and its console script, a
  release workflow with Trusted Publishing (which zizmor will also check),
  whether to yank the placeholder after the working release, and Windows
  support, which will need recipes that do not assume a POSIX shell.

## Alternatives

- **Keep `backend/`.** Rejected by the user on 2026-11-16. A future UI sits
  beside the library; keeping `backend/` would need copies of `README.md` and
  `LICENSE` inside it (build backends do not package files outside the project
  directory) and task-runner and hook delegation.
- **Hatchling or `uv_build`.** Hatchling's default sdist includes every
  non-ignored file, which would ship `.standards/` and `artifacts/` unless
  configured. Setuptools is already in place and does not.
- **Trusted Publishing for the placeholder.** It needs a release workflow and a
  PyPI pending publisher first, which would have delayed the name reservation.
  It is the plan for the working release.
- **Pre-release placeholder version.** Rejected because installers may skip
  pre-releases, which could break `pip install pydelity`.
- **Keeping the pipeline dependencies.** Rejected because nothing imports them
  and `pip install pydelity` would pull a heavy, unused stack.
- **TestPyPI rehearsal.** Not needed: `twine check` and a local wheel install
  covered the same risks without a second account and token.
- **An exact `required-version`.** The earlier decision. Dependabot's uv updater
  fails on any uv the pin excludes, so it would block `AC-044`.
- **Installing just in CI with an action** (`extractions/setup-just`,
  `taiki-e/install-action`). The just version would be an action input that
  Dependabot does not update, or the latest release if omitted.
- **`prek.toml` or prek's `repo: builtin` hooks.** Dependabot and zizmor read
  `.pre-commit-config.yaml` only, so the hook revs would lose their updater.
- **A `package.json` for prettier and markdownlint-cli2.** Dependabot's `npm`
  updater would keep them current, but every clean checkout would need system
  Node and an `npm` install step in a Python repo. prek's managed Node avoids
  both; the cost is the hand-kept prettier pin.
- **zizmor through its own pre-commit repo or `zizmor-action`.** Either adds a
  second zizmor pin, and the action's SARIF upload needs
  `security-events: write`.
- **zizmor's `regular` or `pedantic` persona.** Both hide some findings without
  a written reason, which `AC-045` rules out.
- **Excluding STANDARDS files from Markdown tooling.** The original decision 9;
  replaced at the user's request by `AC-041`.
- **Letting prettier write any change to STANDARDS files.** `AC-041` allows
  whitespace and line wrapping only; prettier also pads table delimiter rows and
  normalizes list and emphasis markers.
- **Failing when a STANDARDS file needs more than whitespace.** It would block
  the repo on edits that only a record's owner or a framework upgrade may make.
- **Separate strict and relaxed markdownlint configs.** More moving parts for a
  handful of rule changes; one commented config is enough.

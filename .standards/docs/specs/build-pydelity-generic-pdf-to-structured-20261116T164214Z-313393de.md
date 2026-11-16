<!-- STANDARDS
Artifact: ARCHITECTURE
Cycle: build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de
-->

# Technical Design: pydelity repo setup and PyPI name

Design mode: `FOUNDATION`.

## Context

The scope covers two things: getting the repo into shape for a Python 3.13
library with a Typer CLI that ships to PyPI (`AC-001`, `AC-002`), and reserving
`pydelity` on PyPI with a placeholder release (`AC-040`). Pipeline code is out of
scope; package code stays at empty modules and a smoke test.

What the scaffold looks like today (observed 2026-11-16 on branch
`tz6/port-over`):

- The package sits in `backend/src/pydelity/` (empty `__init__.py` files plus
  `cli/` and `utils/` subpackages), with `backend/pyproject.toml` (setuptools,
  version `0.0.0`, `requires-python = ">=3.13,<3.14"`), `backend/uv.lock`, a
  `backend/Makefile` and empty `backend/tests/`. `backend/__init__.py` and
  `backend/src/__init__.py` also exist.
- Dependencies are locked twice: `backend/uv.lock` and hashed `uv pip compile`
  files in `cicd/requirements/`. `make install` lives only in
  `backend/Makefile`; the root `Makefile` has no `install` or `test` target.
- `[project].dependencies` lists the KGForEdGlobal runtime stack (pydantic-ai,
  PyMuPDF and others) though no code imports it, and dev tools are a published
  `dev` extra.
- Known blockers for `AC-001`: `make test` passes `-m tests` (a marker
  expression, so nothing is selected) and `test-all` uses an unregistered
  `--run-slow` option; the `env-template-sync` pre-commit hook points at a path
  that does not exist; `detect-secrets` expects a `.secrets.baseline` that does
  not exist; `scripts/check_env_template.py` scans a `frontend/` section; the
  only workflow is `.github/workflows/trufflehog-pr.yml`.
- Formatting today can touch STANDARDS files: `make lint-markdown` runs
  `prettier --write` on every `**/*.md`, and the generic pre-commit hooks run on
  every file.
- `pydelity` is free on PyPI and TestPyPI (both returned 404 on 2026-11-16).
- Local tools: uv 0.7.3 (latest is 0.13.8), Python 3.13 at
  `/opt/homebrew/bin/python3.13`, Node 23.10.0. Remote:
  `git@github.com:IDinsight/pydelity.git`. `LICENSE` is MIT.

User decisions made during architecture (2026-11-16):

- The package moves to a root `src/` layout. The user first leaned towards
  keeping `backend/` for a possible future web UI; they chose the root layout
  after weighing that a UI would sit beside the library as `frontend/` (or
  `web/`) and import it.
- `requires-python = ">=3.13"`, with no upper cap.

No project references exist under `.standards/project-references/`.

## Decision

1. **Root `src/` layout.** `pyproject.toml`, `uv.lock`, `.python-version`,
   `Makefile`, `README.md` and `LICENSE` sit at the repo root; the package is
   `src/pydelity/` and tests are `tests/`. `backend/` and `cicd/` are removed.
   The root `README.md` is the PyPI project page. A future UI goes in
   `frontend/` beside the library.
2. **Build backend: setuptools (≥ 77).** It is already in place, its default
   sdist only picks up the package and standard top-level files, and ≥ 77
   supports SPDX `license = "MIT"` with `license-files`. Static version in
   `pyproject.toml`.
3. **One locked dev environment.** `uv.lock` is the only lock. Dev tools move to
   a PEP 735 `[dependency-groups]` `dev` group, so they never appear in
   published metadata. `make install`, the lint targets, pre-commit's local
   hooks and CI all run the tools from that environment through `uv`. The
   required uv version is pinned once (`[tool.uv] required-version`) and CI
   installs a uv that satisfies it, so a lock written by one uv can be read by
   the others. Developer picks the version with the user; the local uv 0.7.3 may
   need upgrading.
4. **Python.** `requires-python = ">=3.13"`. `.python-version` pins `3.13` so
   local and CI environments use 3.13 even when a newer Python is installed. CI
   tests 3.13 only.
5. **No runtime dependencies and no console script this cycle.** Nothing
   imports the KGForEdGlobal stack yet, so `[project].dependencies` is empty.
   The next cycle adds dependencies as code needs them, plus the Typer CLI and
   its `[project.scripts]` entry. The package ships a `py.typed` marker.
6. **Placeholder version `0.0.1`, a final release.** A pre-release such as
   `0.0.1.dev0` is avoided because installers skip pre-releases in some cases.
   A corrected placeholder takes `0.0.2`, `0.0.3` and so on. The working
   release in the next cycle is `0.1.0` or higher.
7. **The user uploads the placeholder by hand** from their own terminal with
   `uv publish` (or `twine upload`), entering their own PyPI token when asked
   or exporting it in that shell only. Agents never see, type or store the
   token. A release workflow with PyPI Trusted Publishing comes with the
   working release in the next cycle.
8. **CI.** A GitHub Actions workflow runs the `AC-001` commands on Python 3.13
   for pull requests to `main` and pushes to `main`. The TruffleHog workflow
   stays. Third-party actions are pinned by commit SHA with a version comment,
   as the existing workflow does.
9. **STANDARDS files are off limits to tooling.** Every formatter, linter and
   pre-commit hook excludes `.standards/`, `.agents/`, `.claude/skills/`,
   `.claude/settings.json`, `.codex/hooks.json`, `AGENTS.md` and `CLAUDE.md`.
   The last two settings files come from the STANDARDS installation
   (`.standards/INSTALLATION.json`), so they are protected with the paths the
   scope names.

The lint toolchain itself (keeping black, isort, pylint, interrogate and cloc,
or moving to Ruff for linting and formatting), env templates, `.envrc`,
`.gitignore` contents, author and URL metadata, and which empty subpackages to
keep are settled during the interactive setup between the user and Developer,
within the contracts below.

## Acceptance Coverage

- `AC-001`: Decisions 1 to 5, 8 and 9; the dev-environment, test-import,
  tooling and CI contracts below.
- `AC-002`: No architectural impact. Satisfaction depends on the user's sign-off
  of the repo setup during Developer's interactive work, before any pipeline
  code is written. This design adds no pipeline modules.
- `AC-040`: Decisions 1, 2 and 4 to 7; the distribution and credential
  contracts below.

## Components

- `src/pydelity/`: the import package. This cycle it holds only module
  docstrings and `py.typed`; empty subpackages are optional.
- `tests/`: pytest suite with at least one smoke test of the installed package.
- `pyproject.toml`: project metadata, build system, dependency groups and tool
  settings. The single source of package metadata and the version.
- `uv.lock` and `.python-version`: the locked dev environment and its Python.
- `Makefile`: the root entry point for `install`, the lint targets, `test` and
  `clean`. There is no delegation into subdirectories.
- `.pre-commit-config.yaml`: generic file checks, secret detection, Markdown
  checks, and local hooks that run the locked Python tools.
- `.github/workflows/`: the new CI workflow and the existing TruffleHog
  workflow.

## Interfaces and Contracts

### Published distribution (`AC-040`)

| Field             | Value                                                                                     |
| ----------------- | ----------------------------------------------------------------------------------------- |
| Name              | `pydelity`                                                                                |
| Version           | `0.0.1` (later placeholders `0.0.N`)                                                      |
| Description       | Says the package is under development and not yet usable                                  |
| Long description  | Root `README.md`, opening with the same statement                                         |
| Classifiers       | `Development Status :: 1 - Planning`, `Programming Language :: Python :: 3.13`            |
| License           | `license = "MIT"`, `license-files = ["LICENSE"]`                                          |
| `requires-python` | `>=3.13`                                                                                  |
| Dependencies      | None                                                                                      |
| Entry points      | None                                                                                      |
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

PyPI tokens never appear in tracked files, the Makefile, CI configuration,
`.env*` files or a `.pypirc` in the repo. `dist/` and build output are
gitignored. The first upload of a new project needs an account-scoped token,
because a project-scoped token cannot exist before the project does.

### Dev environment (`AC-001`)

- On a clean checkout, with only uv, git and network access, `make install`
  builds the environment from the committed `uv.lock` and fails if the lock is
  out of date with `pyproject.toml` (`uv sync --locked` semantics). It needs no
  `.env*` file, direnv or pre-set environment variable.
- The project itself is installed into that environment from `src/`. Tests
  import `pydelity` as installed; no `pythonpath` or `sys.path` entry for `src`
  may hide a packaging error.
- `make test` needs no env file or provider key and runs at least one test.
  Pytest configuration only uses options and markers whose plugins are in the
  dev group and are registered.

### Tooling

- Python lint, format and type tools come from the dev group only. Local
  pre-commit hooks call them through `uv run`, so `make`, pre-commit and CI run
  the same versions. External pre-commit repos are pinned by `rev`.
- Every path that a Makefile target, hook, script or workflow names exists in
  the new layout. Nothing refers to `backend/`, `cicd/` or `frontend/`.
- STANDARDS-owned paths (decision 9) are excluded from every hook and
  formatting target. A lint run never changes them, and `pre-commit run
  --all-files` passes without editing them.

### CI

The workflow runs on `ubuntu-latest` with Python 3.13 and a uv version that
meets `required-version`. It runs `make install`, every lint target, `make
test` and `pre-commit run --all-files`, and fails if any of them fails. A hook
that modifies files counts as a failure, as pre-commit does by default, so
formatting is enforced even if the `make` lint targets write fixes. Permissions
are `contents: read`.

## Data and Control Flow

Placeholder release, in order:

1. Repo is in the root layout with the `AC-040` metadata and README.
2. `uv build` writes the sdist and wheel to `dist/`.
3. Pre-upload checks: `twine check --strict dist/*` (for example through
   `uvx`), a listing of both archives against the contents allowlist, and an
   install of the wheel into a fresh Python 3.13 venv followed by `import
   pydelity`.
4. The user gives the go-ahead and runs the upload from their own terminal with
   their own token.
5. Post-upload check: `https://pypi.org/project/pydelity/` shows the
   under-development text, and in a fresh Python 3.13 venv
   `pip install pydelity` installs `0.0.1`. PyPI's CDN can lag a few minutes.
6. The user revokes the account-scoped token or replaces it with a
   project-scoped one.

## Technical Acceptance Criteria

- `AC-001`: `pyproject.toml`, `uv.lock`, `.python-version` (3.13) and the
  `Makefile` are at the repo root; `backend/` and `cicd/` are gone; the package
  is at `src/pydelity/`.
- `AC-001`: `make install` on a clean checkout creates the environment from the
  committed lock with no `.env*` file, and fails on a stale lock.
- `AC-001`: At least one test imports `pydelity` as installed in the project
  environment, with no `src` path injection, and `make test` runs it with no
  environment setup.
- `AC-001`: `make`, pre-commit's local hooks and CI use one locked set of tool
  versions, and no target, hook, script or workflow names a missing path.
- `AC-001`: No lint, format or pre-commit run modifies a STANDARDS-owned path.
- `AC-001`: CI runs the `AC-001` commands on Python 3.13 for pull requests and
  pushes to `main`, fails when any fails, and pins third-party actions by SHA.
- `AC-040`: The published distribution matches the metadata table, is version
  `0.0.1` (or a later `0.0.N` placeholder), and has no dependencies or entry
  points.
- `AC-040`: Both archives pass `twine check --strict` and contain only the
  allowlisted files.
- `AC-040`: No PyPI credential is in any tracked file, and `dist/` is
  gitignored.

## Build Plan

1. **Root layout and packaging** (critical path for `AC-040`). Move
   `backend/src/pydelity` to `src/pydelity` and `backend/tests` to `tests`;
   remove `backend/__init__.py` and `backend/src/__init__.py`. `CREATE` root
   `pyproject.toml` (from `backend/pyproject.toml`, rewritten to the metadata
   table, with dependencies emptied and dev tools in a dependency group),
   `uv.lock`, `.python-version` and `src/pydelity/py.typed`. `MODIFY`
   `README.md` to the under-development statement. `DELETE` `backend/` and
   `cicd/`. Add `install` and `test` targets to the root `Makefile` and the
   smoke test, so the project stays buildable and testable.
2. **Placeholder release** (`AC-040`). Build, run the pre-upload checks, have
   the user upload, run the post-upload check. Do this before the rest of the
   setup so the name is reserved early.
3. **Interactive setup** (`AC-001`). With the user: lint toolchain and targets,
   `.pre-commit-config.yaml` (fix the broken hooks, add exclusions),
   `scripts/check_env_template.py`, env templates and `.envrc`, `.gitignore`
   (including `dist/`), `CREATE` the CI workflow under `.github/workflows/`,
   and leftovers such as the tracked `.DS_Store` and `interrogate_badge.svg`.
4. **Sign-off** (`AC-002`). The user signs off the setup before any pipeline
   code is written.

## Risks and Follow-up

- PyPI may reject a name it considers confusable with an existing project even
  though `pydelity` returned 404. If the upload is refused, stop and route the
  name change to Scoper.
- The name could still be taken before step 2. That is why step 2 comes before
  the rest of the setup.
- Published versions are permanent. A mistake in `0.0.1` can only be fixed with
  `0.0.2`, which is why the pre-upload checks exist.
- `>=3.13` lets Python 3.14 users install versions tested only on 3.13. The
  next cycle can add 3.14 to CI.
- Next cycle: runtime dependencies, the Typer CLI and its console script, a
  release workflow with Trusted Publishing, and whether to yank the
  placeholder after the working release.

## Alternatives

- **Keep `backend/`.** Rejected by the user on 2026-11-16. A future UI sits
  beside the library; keeping `backend/` would need copies of `README.md` and
  `LICENSE` inside it (build backends do not package files outside the project
  directory) and Makefile and pre-commit delegation.
- **Hatchling or `uv_build`.** Hatchling's default sdist includes every
  non-ignored file, which would ship `.standards/` and `artifacts/` unless
  configured. Setuptools is already in place and does not.
- **Trusted Publishing for the placeholder.** It needs a release workflow and a
  PyPI pending publisher first, which delays the name reservation. It is the
  plan for the working release.
- **Pre-release placeholder version.** Rejected because installers may skip
  pre-releases, which could break `pip install pydelity`.
- **Keeping the pipeline dependencies.** Rejected because nothing imports them
  and `pip install pydelity` would pull a heavy, unused stack.
- **TestPyPI rehearsal.** Not required: `twine check` and a local wheel install
  cover the same risks without a second account and token. The user may still
  ask for one.

# Project Context

## Project Baseline

- `pydelity` is a new repository with no implementation. It was copied from the
  KGForEdGlobal scaffold and still carries that project's web-app, KG and Docker
  leftovers. `ProjectMode` is `GREENFIELD`.
- The only package code is empty `__init__.py` files under
  `backend/src/pydelity/` (with `cli/` and `utils/` subpackages). The only test
  files are empty `__init__.py` files and an empty `conftest.py` under
  `backend/tests/`. Nothing is defined anywhere.
- The active technical design (`Active Work.Architecture`) plans a new root
  layout, packaging, tooling, CI and a placeholder PyPI release. None of it
  exists in the repository yet, and the design is authoritative for its
  contents. Everything below describes the repository before Developer starts.
- `pydelity` is not registered on PyPI or TestPyPI: both JSON API endpoints
  returned 404 on 2026-11-16.

## Stack and Tooling

- `backend/pyproject.toml`: setuptools backend (`setuptools>=61`), src layout
  (`package-dir = {"" = "src"}`), static version `0.0.0`,
  `requires-python = ">=3.13,<3.14"`, `readme = "README.md"` (resolves to
  `backend/README.md`), author and maintainer set to a team address, no license
  field and no `[project.scripts]`.
- `[project].dependencies` lists the KGForEdGlobal runtime stack (pydantic-ai,
  PyMuPDF, pydantic, pydantic-settings, loguru, typer, PyYAML and others). No
  code imports any of it.
- Dev tools are a published `[project.optional-dependencies] dev` extra with
  exact pins: black 25.9.0, isort 6.1.0, ruff 0.13.3, mypy 1.18.2, pylint 3.3.8
  with pylint-pytest, interrogate 1.7.0, pytest 8.2.0 with the asyncio, bdd,
  cov, mock, order, randomly and xdist plugins, pre-commit 4.3.0 and
  detect-secrets 1.5.0.
- Dependencies are locked twice: `backend/uv.lock` (`version = 1`,
  `revision = 2`, `requires-python = "==3.13.*"`, 165 packages) and hashed
  `uv pip compile` output in `cicd/requirements/requirements.txt` and
  `requirements_dev.txt`. `backend/Makefile` installs from the `cicd/` files,
  not from `uv.lock`.
- Tool settings live in `backend/pyproject.toml`: black and isort at 88 columns
  (isort `profile = "black"` with named import-section headings and a
  KGForEdGlobal `known_third_party` list), ruff (`target-version = "py313"`,
  mccabe 10), mypy (`disallow_untyped_defs`, `plugins = ["pydantic.mypy"]`),
  interrogate (`fail-under = 100`, badge written to `../`), pytest and coverage.
  Pylint reads `backend/.pylintrc`.
- Markdown: root `make lint-markdown` runs an unpinned
  `npx prettier --write --prose-wrap always --print-width 80` over `**/*.md`,
  using `.gitignore` and the empty `.prettierignore` as ignore files and
  skipping `CHANGELOG.md`. Pre-commit runs the `markdownlint-cli2` hook at
  `rev: v0.23.2` with `language_version: "24.15.0"`. No `.markdownlint*` or
  `.prettierrc*` config exists.
- This machine on 2026-11-16: uv 0.7.3; `python3.13` is 3.13.9 at
  `/opt/homebrew/bin/python3.13` while `python3` on `PATH` is 3.11.6; Node
  23.10.0 (nvm); a global pre-commit 4.2.0; GNU Make 3.81; direnv, pnpm and cloc
  are installed. GitHub's `ubuntu-latest` runners ship a newer GNU Make, so
  Makefile syntax must work on both.
- STANDARDS 0.15.0 is installed (`.standards/VERSION.json`). Its runtime tools
  in `.standards/bin/` run with Node.

## Structure and Boundaries

- `backend/` — the current Python project: `pyproject.toml`, `uv.lock`,
  `Makefile`, `.pylintrc`, `.gitignore`, `.envrc` (only `source_env ../.envrc`
  added), `.template.env.local`, `README.md` (a bare `# README` heading),
  `__init__.py`, `src/__init__.py`, `src/pydelity/` and `tests/`.
  `backend/.gitignore` holds the only Python build and cache ignores
  (`__pycache__/`, `dist/`, `build/`, `*.egg-info/`, `.pytest_cache/`,
  `.mypy_cache/`, `.ruff_cache/`, `.coverage` and similar).
- `cicd/requirements/` — the two hashed requirement files and nothing else.
- Repo root — `Makefile` (`help`, `clean`, `lint`, `lint-markdown`),
  `README.md` (title and the tagline "PDF to structured JSON, faithfully"),
  `LICENSE` (MIT), `.gitignore`, `.pre-commit-config.yaml`, `.secrets.baseline`,
  `.template.env`, `.envrc`, empty `.prettierignore`, `interrogate_badge.svg`
  and a tracked `.DS_Store` (which `.gitignore` also lists).
- `scripts/check_env_template.py` — checks that each `.env*` file and its
  `.template.env*` partner declare the same variable names, in sections `.`,
  `backend` and `frontend`. `frontend/` does not exist; missing pairs are
  skipped with a message.
- `.github/` — `workflows/trufflehog-pr.yml` (the only workflow), `CODEOWNERS`
  (one default owner for every path), issue templates and
  `pull_request_template.md`.
- `artifacts/design_brief.md` — tracked internal brief: the full pipeline
  request, design directions, evidence E1–E23 and open questions. Input for the
  next cycle, not this one.
- STANDARDS files — `.standards/`, `.agents/skills/`, `.claude/skills/`,
  `.claude/settings.json`, `.codex/hooks.json`, `AGENTS.md` and `CLAUDE.md`.
  `.standards/INSTALLATION.json` lists the two settings files as
  installer-created; both register a Stop hook that runs
  `.standards/bin/hook.mjs`. `.agents/skills/` and `.claude/skills/` hold
  parallel copies of the role skills (88 Markdown files each).
- Ignored local state, not baseline and not inspected: `.env`, `.env.local`,
  `backend/.env.local`, `backend/.venv/`, `backend/.ruff_cache/`, `.idea/` and
  an empty `graveyard/`.

## Nearest Analogues

- `backend/Makefile` and `backend/pyproject.toml` — the scaffold's Python
  conventions: `help` built from `##` target comments, colour codes silenced
  when `TERM` is unset, uv-driven targets, exact dev pins and tool settings in
  `pyproject.toml`. They assume the `backend/` layout and the `cicd/` lock
  files.
- `.github/workflows/trufflehog-pr.yml` — the only CI precedent:
  `permissions: contents: read`, `ubuntu-latest`, triggered on pull requests to
  `main`, third-party actions pinned by commit SHA with a version comment
  (`actions/checkout` v7.0.1, `trufflesecurity/trufflehog` v3.99.7).
- No packaging, build or publishing precedent exists in the repository.
  KGForEdGlobal (`/Users/tzz/Projects/private/idi/KGForEdGlobal`, branch
  `tz6/page-ir-extraction-cleanup`, HEAD `5e2d7cc`) is the scaffold's origin and
  read-only reference; this cycle needs nothing from its pipeline code.

## Commands

The targets as they stand. Several fail or have side effects:

- `make help` (root or `backend/`) — list targets.
- `make lint-markdown` and `make lint` (root) — prettier in write mode over
  every Markdown file, fetching whatever prettier version is current.
- `make clean` (root) — removes JavaScript build directories, then runs
  `pnpm store prune`, which changes the machine-wide pnpm store.
- `cd backend && make install` — `uv venv`, `ensurepip`, then `uv pip sync` from
  `../cicd/requirements/*.txt`. There is no root `install` or `test` target.
- `cd backend && make lint` — isort and black (both rewrite files), ruff,
  interrogate, mypy, pylint and cloc over `src/` and `tests/`, using
  `backend/.venv/bin`.
- `cd backend && make test` — sources `tests/test.env` and runs
  `uv run pytest -n auto --dist worksteal ... --cov=. -m tests`. `-m tests` is a
  marker expression, so only tests marked `tests` would run, and there are no
  tests. `make test-all` passes `--run-slow`, which no plugin or conftest
  registers.
- `cd backend && make uv-lock` — rewrites both `cicd/` files and `uv.lock`.
- `cd backend && make clean-docker` — deletes all local Docker containers,
  images, volumes and build caches. A leftover; never run it.
- `pre-commit run --all-files` — runs `.pre-commit-config.yaml`. The
  `env-template-sync` entry is
  `uv run --project python scripts/check_env_template.py`, and no `python/`
  directory exists. The Python hooks match only `^backend/(src|tests)/.*\.py$`
  and run through `uv run --project backend`.
- `node .standards/bin/check.mjs` — STANDARDS consistency check; read-only. It
  passes on the current tree.
- Not established in the repository: a build, distribution check or publish
  command (no `uv build`, `twine` or `uv publish` usage anywhere).

## Conventions and Constraints

- `CLAUDE.md` imports `AGENTS.md`, which sets the STANDARDS workflow and has no
  other project-specific rules.
- The protocol treats `.standards/PROTOCOL.md`, `.standards/protocol/`,
  `.standards/bin/`, `VERSION.json` and `INSTALLATION.json` as changed only by
  installation or upgrade. The scope records the user's `AC-041` exception for
  cosmetic Markdown formatting; the scope and design hold its terms.
- Repository Markdown is wrapped at 80 columns with prose wrap, the format
  STANDARDS ships in. 29 tracked Markdown files, including
  `.standards/PROTOCOL.md`, the role references under
  `.agents/skills/*/references/` and `.claude/skills/*/references/`, and this
  cycle's design, wrap long blocks in `<!-- markdownlint-disable MD013 -->` and
  `<!-- markdownlint-enable MD013 -->` pairs.
- `.gitignore` ignores `.env*` and `*.env*` except `.envrc`, `.template.env*`
  and `backend/tests/test.env`. It also ignores `data/`, `results/`, `logs/`,
  `caches/`, `secrets/`, `graveyard/`, `.venv`, `.idea/` and `.vscode/`. It has
  no Python build or cache entries (those sit in `backend/.gitignore`).
- Environment variable names only (values not recorded): `.template.env`
  declares `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` and `LLM_*` model-tuning
  settings; `backend/.template.env.local` and the committed fake-value
  `backend/tests/test.env` declare `CHAT_ENV` and `LOGGING_LOG_LEVEL`.
  `backend/Makefile` also sets `PATHS_PROJECT_DIR` for tests. All are
  KGForEdGlobal leftovers.
- `.envrc` exports `PROJECT_ENV=local`, loads `.env` if present, and exits with
  an error when `.env.local` is missing. It only runs under direnv.
- `backend/pyproject.toml` pytest settings: `pythonpath = [".", "src"]` (puts
  `src` on `sys.path`), `asyncio_mode = "auto"`,
  `bdd_features_base_dir = "tests/features/"` and a registered `costs-money`
  marker. Coverage paths still name `backend/src`.
- mypy loads the `pydantic.mypy` plugin, which needs pydantic importable in the
  environment mypy runs from.
- interrogate's `generate-badge = "../"` writes `interrogate_badge.svg` to the
  repo root when run from `backend/`, which is why that file is tracked.
- `.secrets.baseline` (detect-secrets 1.5.0, generated 2026-11-16) is committed
  with zero results.
- Git history uses Conventional Commits. Remote
  `git@github.com:IDinsight/pydelity.git`, default branch `main`, work branch
  `tz6/port-over`.

## External Systems and Data

- PyPI and TestPyPI: the `pydelity` name is unregistered (404 on 2026-11-16).
  No `.pypirc`, PyPI token reference or publishing configuration exists in the
  repository.
- GitHub `IDinsight/pydelity`: Actions runs only TruffleHog on pull requests to
  `main`, with `--only-verified` and a separate step that fails the job when the
  scan fails.
- Model providers (Anthropic, OpenAI) appear only as environment-variable names
  in `.template.env`; no code calls them. They belong to the next cycle.
- KGForEdGlobal is an external, read-only reference repository.

## Testing and Verification Baseline

- No tests exist. `backend/tests/` holds only empty `__init__.py`,
  `conftest.py`, `fixtures/__init__.py` and `pydelity/__init__.py`, plus
  `test.env`.
- `make test` selects nothing today, and no CI job runs lint or tests.
- `node .standards/bin/check.mjs` passes.
- Prettier and markdownlint behaviour on STANDARDS files was measured during
  Architecture (prettier 3.10.1 leaves shipped files unchanged; markdownlint-cli2
  0.24.1 reports rule violations in shipped files). The design holds those
  results; this audit did not re-run them.

## Relevant Existing Behavior

- `import pydelity` would import an empty package. There is no CLI entry point
  and no published distribution.
- Pre-commit today runs `check-yaml --unsafe`, `end-of-file-fixer` and
  `trailing-whitespace` on every file, STANDARDS files included; detect-secrets
  against the baseline (excluding `pnpm-lock.yaml` and `.template.env`);
  markdownlint-cli2 (excluding `CHANGELOG.md`); and local hooks that target only
  `backend/` Python files plus the broken `env-template-sync` hook.

## Known Unknowns

- GitHub repository visibility could not be checked: the GitHub API call failed
  TLS verification inside this session's sandbox. It matters for whether PyPI
  project URLs may point at the repo, which the design leaves to Developer and
  the user.
- Whether `pre-commit run --all-files` or `backend/make lint` pass today was not
  run: both rewrite files or install hook environments. The broken paths above
  show they cannot pass in the planned layout as written.
- In this agent environment, the client sandbox denies writes under
  `.claude/skills/` and to `.claude/settings.json`. A formatter run from an
  agent session here cannot change those paths, although a run from the user's
  own terminal can.

## Evidence

- `.standards/STATE.md`, `.standards/MODE.md` — active cycle, `GREENFIELD`.
- `.standards/docs/scope/build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de.md`,
  `.standards/docs/specs/build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de.md`
  — cycle scope and planned design.
- `git ls-files`, `git status --ignored`, `git log --stat` — tracked and ignored
  files, history.
- `backend/pyproject.toml`, `backend/uv.lock` header,
  `cicd/requirements/requirements.txt` header — packaging, pins, locks, tool
  settings.
- `Makefile`, `backend/Makefile` — targets and their defects.
- `.pre-commit-config.yaml`, `scripts/check_env_template.py`,
  `.github/workflows/trufflehog-pr.yml` — hooks and CI.
- `.gitignore`, `backend/.gitignore`, `.envrc`, `backend/.envrc`, variable names
  in `.template.env`, `backend/.template.env.local`, `backend/tests/test.env`.
- `.claude/settings.json`, `.codex/hooks.json`, `.standards/INSTALLATION.json`,
  `.standards/VERSION.json` — STANDARDS-managed files.
- `grep` for `markdownlint-enable` over tracked Markdown — 29 files re-enable
  `MD013`.
- `curl` of `https://pypi.org/pypi/pydelity/json` and the TestPyPI equivalent —
  404 on 2026-11-16.
- `uv --version`, `node --version`, `python3.13 --version`, `make --version`,
  `pre-commit --version` — local tool versions.
- `git -C /Users/tzz/Projects/private/idi/KGForEdGlobal log -1` — reference
  repo branch and HEAD.
- `node .standards/bin/check.mjs` — passes.

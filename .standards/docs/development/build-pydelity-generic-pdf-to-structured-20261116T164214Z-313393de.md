<!-- STANDARDS
Artifact: DEVELOPMENT
Cycle: build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de
-->

# Development Plan

`Cycle`: `build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de`
`Mode`: `STEPWISE` `User Style`: `tony` `User Style Locked`: `true` `Status`:
`IN_PROGRESS` `Verification Cadence`: `AFTER_IMPLEMENTATION`
`Current Increment`: `NONE`

## Implementation Contract

- `Scope`:
  `.standards/docs/scope/build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de.md`
- `Architecture`:
  `.standards/docs/specs/build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de.md`
- `Request`: Interactive repo setup for a Python 3.13 library with a Typer CLI
  that ships to PyPI (signed off by the user), plus a placeholder `pydelity`
  release on PyPI published as early as possible. Markdown linting and
  formatting cover every Markdown file, STANDARDS files included. No pipeline
  code.

## Build Steps

### DEV-001 — Root src layout and placeholder packaging

`Status`: `DONE` `Depends On`: `NONE` `Acceptance`: `AC-001, AC-040`

**Goal**

Move the project to the root `src/` layout with root packaging that builds the
`0.0.1` placeholder, a locked dev environment, and working `make install` and
`make test` targets (design decisions 1 to 6, Build Plan step 1).

**Affected Area**

`backend/` and `cicd/` (removed); new root `pyproject.toml`, `uv.lock`,
`.python-version`, `src/pydelity/` (with `py.typed`), `tests/`; root
`README.md`, `Makefile` and `.gitignore`; `.pylintrc` moved to the root.

**Expected Outcome**

- `src/pydelity/__init__.py` (module docstring only) and `py.typed`. The empty
  `cli/` and `utils/` subpackages and `backend/__init__.py`,
  `backend/src/__init__.py` are gone.
- Root `pyproject.toml` matches the design's metadata table: version `0.0.1`,
  under-development description, the two classifiers, `license = "MIT"` with
  `license-files`, `requires-python = ">=3.13"`, no dependencies or entry
  points, `setuptools>=77`. The KGForEdGlobal runtime stack is removed. Dev
  tools move unchanged to `[dependency-groups] dev`;
  `[tool.uv] required-version` is set. Tool settings move from
  `backend/pyproject.toml` with paths updated (pytest drops `pythonpath`;
  coverage drops `backend/src`). Toolchain choices stay for `DEV-004`.
- `uv.lock` at the root is the only lock; `.python-version` is `3.13`.
- `backend/tests/` moves to `tests/` with one smoke test that imports the
  installed `pydelity` and reads its version from installed metadata.
- Root `Makefile` gains `install` (`uv sync --locked`) and `test` (pytest
  through `uv run`, no env file). `backend/Makefile` and its Docker targets go.
- Root `.gitignore` takes the Python build and cache entries from
  `backend/.gitignore`, including `dist/`.
- `README.md` opens with the under-development statement used on PyPI.
- No tracked path under `backend/` or `cicd/` remains.

**Self-Check**

From the repo root: `make install` (and `uv lock --check`), `make test`,
`git ls-files backend cicd` (empty), `node .standards/bin/check.mjs`. Then set
`.standards/MODE.md` to `BROWNFIELD`.

Evidence (2026-11-16, uncommitted working tree on `828e4d7`, uv 0.13.8 from a
scratch tool directory with `UV_CACHE_DIR` in the session temp directory,
because the agent sandbox cannot write to `~/.cache/uv` or the installed uv):

- `uv lock`: CPython 3.13.9 (`/opt/homebrew/opt/python@3.13`), 58 packages, lock
  `revision = 5`. `uv lock --check`: up to date.
- `make install`: passed. `make test`: 1 passed
  (`tests/pydelity/test_package.py`).
- `import pydelity` resolves to
  `build/__editable__.pydelity-0.0.1-py3-none-any/pydelity/__init__.py`; no
  `sys.path` entry ends in `src`. A probe module added under `src/pydelity/` was
  importable on the next `uv run`, and gone after it was deleted.
- `git ls-files backend cicd`: 0 files. `check.mjs`: passed.
- Scratch copy of tracked and new files (no `.env` or `.env.local`):
  `make install` and `make test` passed; after adding a dependency to
  `pyproject.toml`, `make install` failed with uv's out-of-date lock error.

**Implementation Notes**

- uv's default editable install puts `src` on `sys.path`, which the design's
  dev-environment contract rules out. `[tool.uv]` installs the project in
  setuptools' strict editable mode (a link tree under the gitignored `build/`
  holding only packaged files), and `cache-keys` reinstalls it when anything
  under `src/` changes, so new modules are picked up.
- `interrogate`'s badge path is now `.` (the repo root) instead of `../`; other
  tool settings moved unchanged and wait for `DEV-004`. Until `DEV-004`,
  `DEV-006` and `DEV-007` run, `.pre-commit-config.yaml` still names `backend/`
  and `--project python`, so its Python and env hooks fail.
- `tests/test.env` (KGForEdGlobal values) was removed with `backend/`;
  `make test` needs no env file.

---

### DEV-002 — Build and pre-upload checks for the 0.0.1 placeholder

`Status`: `DONE` `Depends On`: `DEV-001` `Acceptance`: `AC-040`

**Goal**

Produce the placeholder sdist and wheel and run the design's pre-upload checks
(Data and Control Flow steps 2 and 3) before anything reaches PyPI.

**Affected Area**

`dist/` (gitignored build output); no tracked file changes unless a check finds
a packaging defect in `DEV-001` output.

**Expected Outcome**

`dist/pydelity-0.0.1.tar.gz` and `dist/pydelity-0.0.1-py3-none-any.whl` exist,
pass `twine check --strict`, contain only the allowlisted files, carry the
metadata table's values with no `Requires-Dist` or entry points, and the wheel
installs into a fresh Python 3.13 venv where `import pydelity` works. The upload
command for the user is ready.

**Self-Check**

`uv build`; `uvx twine check --strict dist/*`; archive listings (`tar -tzf`,
`unzip -l`) against the allowlist; the wheel's `METADATA`; a fresh
`uv venv --python 3.13` with the wheel installed and `import pydelity`.

Evidence (2026-11-16, uncommitted working tree on `828e4d7`, uv 0.13.8 as in
`DEV-001`):

- `uv build`: `dist/pydelity-0.0.1.tar.gz` and
  `dist/pydelity-0.0.1-py3-none-any.whl`, built by setuptools 84.2.1. SHA-256:
  wheel `a870390e910f7b817546ff1ff63e3d31d2faa7933f7abf0ed3466f565266d2cf`,
  sdist `ecefbe9527430477a0b935b2b0f36884d1883cdd961c98baefbea6fff23ebbbe`.
- `uvx twine check --strict` on both files: `PASSED`.
- Wheel: `pydelity/__init__.py`, `pydelity/py.typed` and `dist-info`
  (`METADATA`, `WHEEL`, `RECORD`, `top_level.txt`, `licenses/LICENSE`). Tag
  `py3-none-any`, `Root-Is-Purelib: true`.
- sdist: `LICENSE`, `README.md`, `pyproject.toml`, `src/pydelity/__init__.py`,
  `src/pydelity/py.typed`, plus setuptools' generated metadata (`PKG-INFO`,
  `src/pydelity.egg-info/`, and a `setup.cfg` holding only its `[egg_info]`
  build tags).
- No path under `.standards`, `.agents`, `.claude`, `.codex`, `artifacts`,
  `graveyard`, `.idea` or `.github`, and no `.env*` file, in either archive.
- `METADATA`: version `0.0.1`; summary "Under development and not yet usable.
  PDF to structured JSON, faithfully."; `License-Expression: MIT`; the two
  classifiers; `Requires-Python: >=3.13`; Markdown long description; the three
  GitHub project URLs; author and maintainer `IDinsight DSEM`. No
  `Requires-Dist` and no `entry_points.txt`.
- Fresh `uv venv --no-project --python 3.13` (3.13.9) with the wheel installed,
  run outside the repo: `import pydelity` loads from `site-packages`, `py.typed`
  is present, `importlib.metadata` reports version `0.0.1`, no requirements and
  no entry points.

**Implementation Notes**

- `uv build` also writes `dist/.gitignore`, so the upload must name the two
  archives explicitly rather than `dist/*`.

---

### DEV-003 — Placeholder published on PyPI and verified

`Status`: `DONE` `Depends On`: `DEV-002, DEV-011` `Acceptance`: `AC-040`

**Goal**

The user uploads `0.0.1` from their own terminal with the token from `DEV-011`,
after giving the go-ahead; Developer then runs the post-upload check (design
steps 4 to 6).

**Affected Area**

PyPI project `pydelity` (user action). No repository change.

**Expected Outcome**

`https://pypi.org/project/pydelity/` shows `0.0.1` with the under-development
text, and `pip install pydelity` in a fresh Python 3.13 venv installs `0.0.1`.
The user has been reminded to revoke the account-scoped token or replace it with
a project-scoped one. Agents never see, type or store the token.

**Self-Check**

PyPI JSON API for `pydelity` (version, summary, files); a fresh Python 3.13 venv
with `pip install pydelity` and `import pydelity`, allowing for CDN lag.

Evidence (2026-11-16):

- The user upgraded their uv to 0.13.8 and ran, in their own terminal with the
  token read through a hidden prompt,
  `uv publish dist/pydelity-0.0.1.tar.gz dist/pydelity-0.0.1-py3-none-any.whl`.
  uv reported both files hashed and uploaded to
  `https://upload.pypi.org/legacy/` with no error.
- PyPI JSON API: `pydelity` `0.0.1`, summary "Under development and not yet
  usable. PDF to structured JSON, faithfully.", `License-Expression: MIT`,
  `requires_python >=3.13`, no `requires_dist`, the two classifiers, the three
  GitHub URLs, Markdown description opening "Under development and not yet
  usable." The uploaded wheel and sdist SHA-256 values match the `DEV-002`
  build. Upload times 2026-11-16T20:03:31Z (wheel) and 20:03:32Z (sdist).
- `https://pypi.org/project/pydelity/` returned HTTP 200, and the simple index
  lists both files.
- Fresh `python3.13 -m venv` (3.13.9, pip 25.3), run outside the repo:
  `pip install pydelity` installed `pydelity-0.0.1`; `import pydelity` loads
  from `site-packages`, `py.typed` is present, no requirements. Limitation:
  inside the agent sandbox pip's macOS trust-store check failed
  (`OSStatus -26276`) while curl and uv reached PyPI normally, so the install
  ran with `--use-deprecated=legacy-certs` (certifi's CA bundle). This is a
  sandbox limit, not a PyPI fault.
- The user was reminded to delete the account-wide token or replace it with a
  `pydelity`-only token.

---

### DEV-004 — Python lint, format and type toolchain

`Status`: `PENDING` `Depends On`: `DEV-001` `Acceptance`: `AC-001`

**Goal**

Move the Python tooling to Ruff wherever Ruff covers the same check, type-check
with ty, keep interrogate, trim the leftover test plugins, and run everything
from one locked set of versions. The exact Ruff rule sets are settled with the
user in this step.

**Affected Area**

`pyproject.toml` (dev group and tool settings), `.pylintrc` (removed), root
`Makefile` lint and test targets, the local Python hooks in
`.pre-commit-config.yaml`, `interrogate_badge.svg`.

**Expected Outcome**

- Ruff formats (replacing black) and sorts imports (replacing isort), keeping
  the five section headings through `lint.isort.import-heading` and the current
  isort settings Ruff supports, such as first-party `pydelity` and
  `lines-between-types`. Ruff is pinned to a version that has `import-heading`
  (0.17.5 was the latest on 2026-11-16).
- Ruff's docstring rules with the NumPy convention check only docstring format;
  its missing-docstring rules (`D100` to `D107`) are off, so interrogate alone
  checks docstring coverage. `C901` keeps McCabe complexity at 10 or less;
  Ruff's pylint-derived rules replace pylint; Ruff's annotation rules require
  type hints in function signatures (what mypy's `disallow_untyped_defs` did).
- ty, pinned to an exact version (it is in beta: 0.0.104 on 2026-11-16),
  replaces mypy and checks `src/` and `tests/`.
- interrogate stays at 100 %, covering the private and nested functions that
  Ruff's docstring rules skip, and regenerates `interrogate_badge.svg` at the
  repo root instead of outside the repo.
- black, isort, mypy, mypy-extensions, pylint, pylint-pytest, `.pylintrc` and
  cloc are gone. The dev group keeps only tools in use: the pytest plugins and
  type stubs left from KGForEdGlobal (asyncio, bdd, mock, order, randomly,
  xdist, `types-*`) go, with their pytest settings; the next cycle adds what
  pipeline tests need.
- Root `make` lint targets and the local pre-commit hooks run the tools through
  `uv run` over `src/` and `tests/`, with no `--project backend` and no
  `backend/` path. No Python tool touches STANDARDS paths or writes outside the
  repo.

**Self-Check**

`make lint` (Python targets) and
`uv run pre-commit run <python hook ids> --all-files` pass on the current tree.

---

### DEV-005 — Markdown format runner, configs and linting

`Status`: `PENDING` `Depends On`: `DEV-001` `Acceptance`: `AC-041, AC-001`

**Goal**

Implement the design's Markdown contract (decision 9): one pinned prettier and
one pinned markdownlint-cli2, one config each, over every Markdown file git
tracks or would track, with the whitespace guard for STANDARDS files and
`check.mjs` after formatting.

**Affected Area**

New `scripts/` format runner (Node), `.prettierrc`, `.markdownlint-cli2.yaml`,
Markdown hooks in `.pre-commit-config.yaml`, root `Makefile` Markdown targets,
`.prettierignore`.

**Expected Outcome**

- Versions are pinned once in `.pre-commit-config.yaml`: prettier `3.10.1` as a
  local `language: node` hook dependency and markdownlint-cli2 by hook `rev`,
  both on a pinned Node. `make` and CI call those hooks through
  `uv run pre-commit run ... --all-files`, so they need no system Node, no
  `package.json` and no unpinned `npx`.
- The runner formats project Markdown unconditionally; a STANDARDS file is
  rewritten only when prettier's output matches it with all whitespace removed,
  otherwise it is left byte-identical and named in a warning. It then runs
  `node .standards/bin/check.mjs` and fails if that fails.
- markdownlint runs without fixing; every deviation from its defaults in the
  config has a comment; the config holds against inline `markdownlint-enable`
  comments; every current Markdown file passes.

**Self-Check**

The Markdown `make` targets on the full tree; `git diff` of STANDARDS paths
shows whitespace-only changes; `check.mjs` passes; a guard test in a scratch
copy (a non-whitespace change to a STANDARDS table is warned and left
byte-identical). Limitation: this agent sandbox cannot write under
`.claude/skills/`; prettier `3.10.1` leaves those shipped files unchanged.

---

### DEV-006 — Generic pre-commit hooks and STANDARDS exclusions

`Status`: `PENDING` `Depends On`: `DEV-001` `Acceptance`: `AC-001, AC-041`

**Goal**

Make the generic and secret-scanning hooks fit the new layout and decision 10.

**Affected Area**

`.pre-commit-config.yaml` (pre-commit-hooks, detect-secrets),
`.secrets.baseline` if a rescan is needed.

**Expected Outcome**

`end-of-file-fixer`, `trailing-whitespace` and every other hook that can write
files exclude `.standards/`, `.agents/`, `.claude/skills/`,
`.claude/settings.json`, `.codex/hooks.json`, `AGENTS.md` and `CLAUDE.md`.
Read-only checks (`check-yaml`, detect-secrets) still scan them. Leftover
excludes (for example `pnpm-lock.yaml`) are dropped. External repos stay pinned
by `rev`.

**Self-Check**

`uv run pre-commit run <generic hook ids> --all-files` passes with no file
changes; STANDARDS paths unchanged in `git status`.

---

### DEV-007 — Env templates, .envrc and the env-template check

`Status`: `PENDING` `Depends On`: `DEV-001` `Acceptance`: `AC-001`

**Goal**

Decide with the user which environment variables and env-file behaviour the
library keeps, and fix the broken `env-template-sync` hook.

**Affected Area**

`.template.env`, `.envrc`, `scripts/check_env_template.py`, the
`env-template-sync` hook.

**Expected Outcome**

The templates declare only variables the user keeps (KGForEdGlobal leftovers
such as `CHAT_ENV` are gone with `backend/`). `.envrc` behaviour matches the
user's choice. The script checks only sections that exist (no `backend` or
`frontend`), and the hook runs it through `uv run` with no `--project python`.
No `make` target or test needs an env file.

**Self-Check**

`uv run pre-commit run env-template-sync --all-files` passes; the script run
directly reports the expected pairs. Values in `.env*` files are never read or
printed.

---

### DEV-008 — Scaffold leftovers cleaned up

`Status`: `PENDING` `Depends On`: `DEV-004` `Acceptance`: `AC-001`

**Goal**

Remove the remaining KGForEdGlobal and web-app leftovers the user agrees to.

**Affected Area**

`.gitignore`, root `Makefile` `clean`, tracked `.DS_Store`,
`interrogate_badge.svg` (per `DEV-004`), `.github/` templates if they carry
leftovers.

**Expected Outcome**

`.gitignore` has no stale entries (`!backend/tests/test.env`, `vite-project/`
and others the user drops). `make clean` removes only this repo's Python caches
and build output; no `pnpm store prune` or JavaScript directories. `.DS_Store`
is untracked. No tracked file outside STANDARDS paths names `backend/`, `cicd/`
or `frontend/` unless intended.

**Self-Check**

`make clean`; `git status --ignored`; `git grep` for `backend`, `cicd`,
`frontend`, `pnpm` and `docker` outside STANDARDS paths.

---

### DEV-009 — CI workflow for the AC-001 commands

`Status`: `PENDING` `Depends On`: `DEV-004, DEV-005, DEV-006, DEV-007, DEV-008`
`Acceptance`: `AC-001`

**Goal**

Add the GitHub Actions workflow from design decision 8 and the CI contract.

**Affected Area**

New `.github/workflows/ci.yml`; `trufflehog-pr.yml` unchanged.

**Expected Outcome**

On pull requests to `main` and pushes to `main`, one job on `ubuntu-latest`
installs a uv that meets `required-version`, then runs `make install`, every
lint target, `make test` and `pre-commit run --all-files`, failing if any fails
(including a hook that modifies files). `permissions: contents: read`,
`timeout-minutes`, a concurrency group, and third-party actions pinned by commit
SHA with a version comment.

**Self-Check**

`check-yaml` over the workflow and a review against the CI contract. The
workflow cannot run from this session; it stays unverified until the user pushes
the branch.

---

### DEV-010 — Clean-checkout run and user sign-off of the repo setup

`Status`: `PENDING` `Depends On`: `DEV-003, DEV-009` `Acceptance`:
`AC-002, AC-001, AC-041`

**Goal**

Show the user the finished setup working from a clean copy and record their
sign-off before any pipeline code exists.

**Affected Area**

This plan (sign-off record); a scratch copy of the tracked and new files.

**Expected Outcome**

In a fresh copy with no `.env*` files, `make install`, every lint target,
`make test`, `pre-commit run --all-files` and `check.mjs` all pass. The user has
reviewed the setup and signed it off; the date and what was signed off are
recorded here.

**Self-Check**

The commands above in the scratch copy, with actual output recorded; the user's
sign-off message.

---

### DEV-011 — PyPI account and upload token ready

`Status`: `DONE` `Depends On`: `NONE` `Acceptance`: `AC-040`

**Goal**

Guide the user, one step at a time, through creating their PyPI account and an
upload token, and settle where the project lives: the user's account now, an
IDinsight organization later if PyPI approves one.

**Affected Area**

The user's PyPI account (user actions on pypi.org). No repository change.
Developer never creates the account, enters a password or 2FA code, or sees the
token.

**Expected Outcome**

- The user has a PyPI account under `tony.zhao@idinsight.org` with a verified
  email and two-factor authentication on (PyPI requires 2FA to upload), and
  their recovery codes are saved.
- The user holds an API token scoped to the entire account (a project-scoped
  token cannot exist before the project does), kept only on their side for the
  next step.
- The organization question is settled: an upload always comes from a user's
  token, PyPI organizations need admin approval with no stated timeline, and
  projects can be moved into an organization later. So `0.0.1` goes up under the
  user's account, as `AC-040` requires, and the user may request an `idinsight`
  organization separately.

**Self-Check**

The user confirms each item without sharing secrets; the user's public PyPI
profile page loads.

Evidence (2026-11-16): Developer gave the steps from PyPI's current docs
(docs.pypi.org: managing your account, two-factor authentication, publishing).
The user confirmed the account is ready, with username `tonyzhao6`, and handled
every secret on their own side; none was shared in the conversation or written
to the repo. `https://pypi.org/user/tonyzhao6/` returned HTTP 200, but PyPI
served a browser challenge page to the script, so the page content was not read;
the upload in `DEV-003` is the working proof of the account and token.
`https://pypi.org/pypi/pydelity/json` still returned 404 (name free).

---

## Plan Notes

- **Approval.** The user approved this plan on 2026-11-16 with its defaults and
  just as the task runner (for the rework).
- **Order.** `DEV-001`, `DEV-002`, `DEV-011` and `DEV-003` run first so the name
  is reserved early. The user may start `DEV-011` (account, 2FA, token) sooner,
  since it needs nothing from the repo. `DEV-004` to `DEV-008` follow in the
  order the user prefers; `DEV-009` and `DEV-010` come last. STEPWISE pauses
  after every step.
- **Interactive setup.** The scope makes setup user-directed. When the user
  points out a further change inside the design's contracts, it is folded into
  the matching pending step or added as a new `DEV-NNN` and shown before it is
  made. A change that would alter the scope or design is routed to its owner.
- **Decisions taken at approval (defaults unless the user says otherwise):**
  - uv: the user upgrades their uv to `0.13.8` (`uv self update 0.13.8`, their
    terminal); `[tool.uv] required-version = "==0.13.8"`. An exact pin keeps
    every uv able to read the lock; upgrades are deliberate, like prettier's.
  - Public author and maintainer: unchanged, `IDinsight DSEM`
    `<dsem@idinsight.org>`. Project URLs: `Homepage` and `Repository` point at
    `https://github.com/IDinsight/pydelity` and `Issues` at its issues page (the
    user made the repo public on 2026-11-16).
  - Python tooling (`DEV-004`), as the user chose on 2026-11-16: Ruff wherever
    it covers the check, interrogate kept with its badge, pylint and cloc
    dropped. ty replaces mypy, and the leftover test plugins go, unless the user
    says otherwise.
- **User rework after `DEV-003`.** On 2026-11-16 the user chose prek in place of
  pre-commit, Dependabot, and zizmor for the workflows, and is choosing chose
  just as the task runner. `AC-001` names `make` and `pre-commit`, and the
  design owns the task runner, hook runner, CI and new services, so these are
  routed to Scoper and Architect as user rework, not absorbed here. The rework
  runs once `DEV-003` has reserved the name; this plan is then reconciled with
  the corrected scope and design (`DEV-004` to `DEV-010` are likely to change).
  The same rework passes the Scoper a next-cycle input: the user wants people to
  be able to install and use pydelity on Windows.
  - The empty `cli/` and `utils/` subpackages are dropped; the next cycle adds
    the Typer CLI.
- **Smoke test.** The design's Build Plan step 1 puts one smoke test in
  `DEV-001` so `make test` has something to run. It is scaffold, not formal
  verification; Tester owns formal tests and may revise it.
- **Local ignored files under `backend/`.** `.venv/`, `.ruff_cache/` and
  `backend/.env.local` (empty, per the user, who asked for its removal on
  2026-11-16; not read) are deleted with `backend/`.
- **Upload.** `DEV-003` blocks on the user's go-ahead and upload. No commit is
  made unless the user asks.
- **Styles loaded:** `styles/universal.md`, user style `tony`,
  `styles/python.md`; `styles/github-actions.md` for `DEV-009`.
- **Project references loaded:** `NONE`.

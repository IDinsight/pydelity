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
  formatting cover every Markdown file, STANDARDS files included. After the
  placeholder: just and prek replace Make and pre-commit, Dependabot keeps pins
  current, and zizmor checks the workflows. No pipeline code.

## Build Steps

### DEV-001 — Root src layout and placeholder packaging

`Status`: `DONE` `Depends On`: `NONE` `Acceptance`: `AC-042, AC-040`

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
- Superseded on 2026-11-16 by the design revision for `AC-042` to `AC-045`: the
  Makefile `install` and `test` targets move to the justfile, and the exact uv
  pin becomes a lower bound, both in `DEV-012`. `AC-001` was retired for
  `AC-042`.
- Corrected on 2026-11-16 during `DEV-006`: `cache-keys` watches
  `src/pydelity/**/*` instead of `src/**/*`, which rebuilt the project on every
  `uv run` (details under `DEV-006`).
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

`Status`: `DONE` `Depends On`: `DEV-006` `Acceptance`: `AC-042`

**Goal**

Move the Python tooling to Ruff wherever Ruff covers the same check, type-check
with ty, keep interrogate, trim the leftover test plugins, and run everything
from one locked set of versions through just recipes and prek hooks. The exact
Ruff rule sets are settled with the user in this step.

**Affected Area**

`pyproject.toml` (dev group and tool settings), `uv.lock`, `.pylintrc`
(removed), `justfile` lint recipes, the local Python hooks in
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
  repo root.
- black, isort, mypy, mypy-extensions, pylint, pylint-pytest, `.pylintrc` and
  cloc are gone. The dev group keeps only tools in use: the pytest plugins and
  type stubs left from KGForEdGlobal (asyncio, bdd, mock, order, randomly,
  xdist, `types-*`) go, with their pytest settings; the next cycle adds what
  pipeline tests need.
- The justfile's lint recipes and the local prek hooks run these tools through
  `uv run` over `src/` and `tests/`. No Python tool touches STANDARDS paths or
  writes outside the repo.

**Self-Check**

The Python lint recipes and
`uv run --locked prek run <python hook ids> --all-files` pass on the current
tree; `just test` still passes.

Evidence (2026-11-16, uncommitted working tree on `cd6b470`, `PREK_HOME` and
`UV_CACHE_DIR` in the session temp directory):

- `uv lock`: 25 packages. Removed black, isort, mypy, mypy-extensions, pylint,
  pylint-pytest, pytest-asyncio, pytest-bdd, pytest-mock, pytest-order,
  pytest-randomly, pytest-xdist and both `types-*` stubs (with their
  dependencies); Ruff 0.13.3 to 0.17.5; added ty 0.0.104. `.pylintrc` deleted;
  the black, isort and mypy settings and the pytest-asyncio and pytest-bdd
  options are gone.
- Ruff selects `ANN`, `B`, `C4`, `C90`, `D`, `E`, `F`, `I`, `PL`, `PT`, `RET`,
  `RUF`, `S`, `SIM`, `UP` and `W`, ignores `D100` to `D107` and `D202`, uses the
  NumPy docstring convention, McCabe 10, the five import headings, and lets
  tests use `assert` and literal values (`S101`, `PLR2004`).
- `uv run --locked ruff check src tests`: all checks passed (after the `D202`
  ignore). `ruff format --check`: 6 files already formatted.
  `ty check src tests`: all checks passed. `interrogate src tests`: 100 % (after
  `tests/conftest.py` got a module docstring).
- `uv run --locked prek run --all-files`: `ruff check`, `ruff format`, ty,
  interrogate and every generic hook passed; only markdownlint-cli2 failed,
  which `DEV-005` settles. The interrogate hook left the badge unchanged.
- `uv run --locked just lint-python` passed; `uv run --locked just test`: 1
  passed.
- A scratch module written to break the rules got 15 findings across `I`, `F`,
  `ANN`, `B006`, `D400`, `D403`, `S101`, `S602`, `S607`, `PLW1510`, `SIM103` and
  `RET505`, and `ruff check --fix` added the `# Standard Library` import
  heading.
- `git grep` outside STANDARDS paths finds no `black`, `isort`, `mypy`, `pylint`
  or `cloc`.

**Implementation Notes**

- `D202` (no blank line after a function docstring) is ignored because the
  repo's own Python (`scripts/check_env_template.py`, the smoke test) puts a
  blank line between docstring and body, and Ruff's formatter keeps it.
- The committed `interrogate_badge.svg` said 0.0 %; it now says 100 %.
- `lint-python` writes fixes (`ruff check --fix`, `ruff format`), as the old
  Makefile's `lint` did. CI (`DEV-009`) must therefore not let a lint recipe
  hide unformatted code: run `prek run --all-files` before the lint recipes, or
  fail when they leave a `git diff`.
- `tests/conftest.py` was empty; it now holds only a module docstring so
  interrogate passes. Tester may replace it.

---

### DEV-005 — Markdown format runner, configs and linting

`Status`: `DONE` `Depends On`: `DEV-006` `Acceptance`: `AC-041, AC-042, AC-044`

**Goal**

Implement the design's Markdown contract (decision 9): one pinned prettier and
one pinned markdownlint-cli2, one config each, over every Markdown file git
tracks or would track, with the whitespace guard for STANDARDS files and
`check.mjs` after formatting.

**Affected Area**

New `scripts/` format runner (Node), `.prettierrc`, `.markdownlint-cli2.yaml`,
Markdown hooks in `.pre-commit-config.yaml`, the justfile's Markdown recipes,
`.prettierignore`.

**Expected Outcome**

- prettier `3.10.1` is the `additional_dependencies` pin of a local
  `language: node` hook with a pinned Node `language_version`, and
  markdownlint-cli2 is pinned by its hook `rev`. The two hand-kept pins carry a
  comment saying so. The Markdown recipes, and CI through them, call those hooks
  with `uv run prek run <id> --all-files`, so they need no system Node, no
  `package.json` and no `npx`. The Markdown recipe ported in `DEV-012` is
  replaced.
- The runner formats project Markdown unconditionally; a STANDARDS file is
  rewritten only when prettier's output matches it with all whitespace removed,
  otherwise it is left byte-identical and named in a warning. It then runs
  `node .standards/bin/check.mjs` and fails if that fails.
- markdownlint runs without fixing; every deviation from its defaults in the
  config has a comment; the config holds against inline `markdownlint-enable`
  comments; every current Markdown file passes.

**Self-Check**

The Markdown recipes on the full tree; `git diff` of STANDARDS paths shows
whitespace-only changes; `check.mjs` passes; a guard test in a scratch copy (a
non-whitespace change to a STANDARDS table is warned and left byte-identical).
Limitation: this agent sandbox cannot write under `.claude/skills/`; prettier
`3.10.1` leaves those shipped files unchanged.

Evidence (2026-11-16, uncommitted working tree, `PREK_HOME` and `UV_CACHE_DIR`
in the session temp directory):

- Pins: prettier 3.10.1 (`additional_dependencies` of the local
  `prettier-markdown` hook) and markdownlint-cli2 `v0.24.1` (hook `rev`), both
  the latest on npm on 2026-11-16, on Node 24.22.3 (the latest Node 24 LTS),
  with "kept by hand" comments beside the Node and prettier pins. The empty
  `.prettierignore` is deleted.
- Format runner on the repo (197 Markdown files from `git ls-files`): 1 file
  formatted (this plan), 0 STANDARDS files left unformatted; `check.mjs` passed.
  Compared with a snapshot taken just before, this plan was the only changed
  file and the change was whitespace only; every shipped STANDARDS file stayed
  byte-identical.
- Guard test in a scratch git copy: a STANDARDS file whose table Prettier would
  pad (`|-|-|`) produced the warning and stayed byte-identical; a STANDARDS file
  with one long line was rewrapped; a project file had `*` bullets turned into
  `-`; with an invalid `WorkflowState` in `STATE.md` the runner exited 1 and the
  prek hook failed. With a valid `STATE.md` the runner exited 0. Rewriting a
  tracked file made the prek hook fail with "files were modified by this hook".
- markdownlint, default rules first: 615 findings in 71 files (`MD013` 516,
  `MD036` 77, `MD025` 14, `MD041` 7, `MD026` 1). Skipping code blocks and tables
  left 5 `MD013` findings, all long code spans in `STATE.md`, this plan and the
  brief's title. The final config turns off `MD013`, `MD025`, `MD036` and
  `MD041` and narrows `MD026`, each with its reason, and sets `noInlineConfig`;
  with inline comments honoured, shipped files re-enabled `MD013` and produced
  34 findings. Final run: passed.
- `uv run --locked just lint` (Markdown and Python) passed;
  `uv run --locked prek run --all-files`: every hook passed; `just test`: 1
  passed.

**Implementation Notes**

- The runner finds Prettier through the `prettier` command that prek's Node
  environment puts on `PATH`, so the repo needs no `package.json`. The
  `lint-markdown` recipe runs it with `prek exec`, which does not fail just
  because files were rewritten; the hook does, as the design requires.
- Both Markdown hooks take their file list from git rather than from prek, so
  untracked new Markdown files are covered. prek detects rewrites only in
  tracked files, so an untracked file is formatted without failing the hook.
- Revised on 2026-11-16 at the user's request. They first asked for a
  `.markdownlint.yaml` with `MD013: {tables: false}` and `MD025`, `MD026`,
  `MD036` and `MD041` off. That file can hold only rules, so without
  `noInlineConfig` and `globs` (prek passed the tracked files) markdownlint
  reported 6 `MD013` findings: 3 in `.standards/STATE.md` and 2 in this plan
  (values the STANDARDS formats keep in one long code span) and 1 in
  `artifacts/design_brief.md` (a 98-character title). The user then chose one
  `.markdownlint-cli2.yaml` again, as before, with their rules except `MD013`,
  which stays off; `MD026` is now off rather than narrowed. The hook is back to
  `pass_filenames: false`.
- Also at the user's request: not every branch, `main` included, has STANDARDS
  installed. The runner now runs `.standards/bin/check.mjs` only when it exists
  and otherwise exits 0 without a message (at the user's request, so people who
  do not know STANDARDS are not puzzled; it prints a line only when it runs the
  check, and names STANDARDS files only when the guard left one unformatted).
  Evidence: in the repo, `uv run --locked just lint-markdown` formatted this
  plan (whitespace), ran the STANDARDS check (passed) and markdownlint (passed).
  In a scratch git copy without `.standards/`, `.agents/`, `.claude/`,
  `.codex/`, `AGENTS.md` and `CLAUDE.md`, the runner formatted a new `notes.md`
  (`*` to `-`), printed that STANDARDS is not installed and exited 0, and
  `prek run prettier-markdown markdownlint-cli2 --all-files` passed.

---

### DEV-006 — Hook configuration for prek

`Status`: `DONE` `Depends On`: `DEV-012` `Acceptance`: `AC-042, AC-043, AC-041`

**Goal**

Make `.pre-commit-config.yaml` work under prek in the new layout, with one pin
per tool, and keep every hook that writes files away from STANDARDS files
(design decisions 3, 10 and 12).

**Affected Area**

`.pre-commit-config.yaml`, `pyproject.toml` (detect-secrets pin),
`.secrets.baseline` if a rescan is needed.

**Expected Outcome**

- Local hooks call dev-group tools through `uv run`, with no `--project` option
  and only paths that exist (`src/`, `tests/`). `env-template-sync` runs
  `scripts/check_env_template.py` through `uv run`.
- `end-of-file-fixer`, `trailing-whitespace` and every other hook that can write
  files exclude `.standards/`, `.agents/`, `.claude/skills/`,
  `.claude/settings.json`, `.codex/hooks.json`, `AGENTS.md` and `CLAUDE.md`.
  Read-only checks (`check-yaml`, detect-secrets) still scan them. Leftover
  excludes (`pnpm-lock.yaml`) go.
- detect-secrets keeps either its dev-group pin or its hook `rev`, not both. The
  file uses only remote repos (by URL and `rev`), `local` hooks and `meta`
  hooks; no `repo: builtin`.
- Comments name prek; nothing in the file runs or tells anyone to run a
  `pre-commit` command.

**Self-Check**

`uv run --locked prek run --all-files`: every hook passes except the Python tool
hooks that `DEV-004` replaces, whose failures are recorded; no STANDARDS path
changes; `git grep` finds no `make` or `pre-commit` command outside STANDARDS
paths.

Evidence (2026-11-16, uncommitted working tree on `cd6b470`, `PREK_HOME` and
`UV_CACHE_DIR` in the session temp directory):

- `uv run --locked prek validate-config .pre-commit-config.yaml`: all configs
  valid.
- `uv run --locked prek run --all-files`: `check-yaml`, `end-of-file-fixer`,
  `trailing-whitespace`, `detect-secrets`, `env-template-sync`, black, isort,
  ruff and pylint passed. Failed as expected: interrogate (`tests/conftest.py`
  has no module docstring; it also rewrote `interrogate_badge.svg`, which was
  restored with `git checkout`) and mypy (the `pydantic.mypy` plugin cannot
  load), both replaced in `DEV-004`; markdownlint-cli2 (567 findings, mostly
  `MD013` in shipped skill references), which `DEV-005` settles.
- No STANDARDS path changed (`git status` over `.standards`, `.agents`,
  `.claude`, `.codex`, `AGENTS.md` and `CLAUDE.md` shows only this plan, edited
  by Developer).
- `git grep` outside STANDARDS paths: no `make` or `pre-commit` command. The
  file keeps the `pre-commit/pre-commit-hooks` repo URL and calls itself a
  pre-commit-format file; both are names, which the design allows.

**Implementation Notes**

- detect-secrets is pinned once, in the dev group, and runs as a local hook
  (`detect-secrets-hook`), so `uv run detect-secrets scan` can refresh the
  baseline with the same version. Its old `pnpm-lock.yaml` exclude is gone; the
  `.template.env` exclude stays.
- Each writing hook repeats the STANDARDS exclude pattern instead of using a
  YAML anchor, so every reader of the file (prek, Dependabot, zizmor) sees it
  plainly.
- Correction to `DEV-001` found here: the `cache-keys` glob `src/**/*` also
  matched `src/pydelity.egg-info/`, which every build rewrites, so each `uv run`
  rebuilt the project (and needed the network for `setuptools`). The glob is now
  `src/pydelity/**/*`. Three `uv run` calls in a row built once; a new module
  was still picked up and a deleted one dropped; `uv lock --check` passed; the
  uv bound script passed again with 0.8.1 and 0.13.7.

---

### DEV-007 — Env templates, .envrc and the env-template check

`Status`: `DONE` `Depends On`: `DEV-006` `Acceptance`: `AC-042`

**Goal**

Decide with the user which environment variables and env-file behaviour the
library keeps, and make the env-template check fit the layout.

**Affected Area**

`.template.env`, `.envrc`, `scripts/check_env_template.py`.

**Expected Outcome**

The templates declare only variables the user keeps (KGForEdGlobal leftovers
such as `CHAT_ENV` went with `backend/`). `.envrc` behaviour matches the user's
choice. The script checks only sections that exist (no `backend` or `frontend`).
No recipe or test needs an env file.

**Self-Check**

`uv run --locked prek run env-template-sync --all-files` passes; the script run
directly reports the expected pairs. Values in `.env*` files are never read or
printed.

Evidence (2026-11-16, uncommitted working tree; no value in a `.env*` file was
read or printed, only variable names; probes used fake values in scratch
folders):

- `.template.env` keeps its eight variables (the user's choice); its header now
  says to copy the file to `.env` rather than rename it. `.envrc` loads `.env`
  then `.env.local` with `dotenv_if_exists`; `PROJECT_ENV` and the required
  `.env.local` are gone. `scripts/check_env_template.py` checks only the repo
  root, for the pairs `.env`/`.template.env` and `.env.local`/
  `.template.env.local`.
- `uv run --locked python scripts/check_env_template.py`: exit 0 (the user's
  `.env` matches the template; the `.env.local` pair is skipped because there is
  no `.template.env.local`). `prek run env-template-sync --all-files`: passed.
- Mismatch probe: a scratch `.env` with one template variable and one extra
  variable made the script list both differences and exit 1.
- direnv 2.35.0 in a scratch folder (its data and config directories in the
  session temp directory): with `.env` and `.env.local` present, a variable set
  in both took the `.env.local` value; with neither present, direnv loaded
  without an error. `bash -n .envrc` passed.
- `uv run --locked prek run --all-files`: every hook passed. `git grep` outside
  STANDARDS paths finds no `PROJECT_ENV`, `.env.development` or
  `.env.production`.

**Implementation Notes**

- direnv refuses a changed `.envrc` until it is allowed again, so the user runs
  `direnv allow` once in their checkout.

Correction (2026-11-16): Developer's question about `.envrc` called its
`PROJECT_ENV` switch a KGForEdGlobal leftover, which was an unchecked
assumption; the user explained that it lets people pick a local, development or
production env file. The switch and the development and production pairs in
`scripts/check_env_template.py` are restored, with the user's approval of two
changes: `export PROJECT_ENV="${PROJECT_ENV:-local}"` (so the shell can choose
without editing `.envrc`) and a warning instead of `exit 1` when the selected
file is missing. An invalid `PROJECT_ENV` still stops with an error. The
simplified `.envrc` described above is superseded.

Evidence for the correction (direnv 2.35.0 in a scratch folder with fake
values): with no `PROJECT_ENV`, `.env` then `.env.local` loaded and `.env.local`
won; with `PROJECT_ENV=production`, `.env.production` won; with `development`
and no `.env.development`, the warning printed and `.env` still loaded; with
`staging`, direnv stopped with the error (exit 1); with no env files, the
warning printed and nothing failed. After `export PROJECT_ENV=production` and
`direnv reload` in a shell, `PROJECT_ENV` stayed `production`. The env check
(exit 0, three pairs skipped for missing files), `bash -n .envrc` and
`uv run --locked prek run --all-files` (every hook) all passed.

---

### DEV-008 — Scaffold leftovers cleaned up

`Status`: `DONE` `Depends On`: `DEV-004` `Acceptance`: `AC-042`

**Goal**

Remove the remaining KGForEdGlobal and web-app leftovers the user agrees to.

**Affected Area**

`.gitignore`, tracked `.DS_Store`, `interrogate_badge.svg` (per `DEV-004`),
`.github/` templates if they carry leftovers.

**Expected Outcome**

`.gitignore` has no stale entries (`!backend/tests/test.env`, `vite-project/`
and others the user drops). `.DS_Store` is untracked. No tracked file outside
STANDARDS paths names `backend/`, `cicd/`, `frontend/`, `pnpm` or Docker unless
intended.

**Self-Check**

`just clean`; `git status --ignored`; `git grep` for `backend`, `cicd`,
`frontend`, `pnpm` and `docker` outside STANDARDS paths.

Evidence (2026-11-16, uncommitted working tree):

- Reviewed: `.gitignore`, `.github/` (CODEOWNERS, issue templates, pull request
  template, workflows), `.secrets.baseline`, tracked files and `git grep` for
  `backend`, `cicd`, `frontend`, `pnpm`, `docker` and `vite`. The issue and pull
  request templates and the secrets baseline already fit pydelity.
- Changed, as the user chose: `.gitignore` drops `!backend/tests/test.env` and
  `vite-project/` and its header no longer calls it the "global" file;
  `git rm --cached .DS_Store` (the file stays on disk and `git check-ignore`
  shows `.gitignore:16` ignoring it); the README shows the interrogate badge
  under the title, from
  `https://raw.githubusercontent.com/IDinsight/pydelity/main/interrogate_badge.svg`,
  linked to the interrogate docs. Kept, as the user chose: the `data/`,
  `results/`, `logs/`, `caches/`, `secrets/` and `docs/_build/` ignores and the
  CODEOWNERS sample text.
- `git grep` outside STANDARDS paths finds none of those words except
  `build-backend` in `pyproject.toml`. `git status --ignored` lists only local
  files (`.DS_Store`, `.env`, `.env.local`, `.idea/`, caches, `.venv/`,
  `build/`, `dist/`, `src/pydelity.egg-info/`).
- `just clean` in a scratch copy removed `.venv`, `build`, `dist`,
  `.pytest_cache` and `.coverage`. A scratch `uv build` of the changed README
  passed `twine check --strict`. `uv run --locked prek run --all-files`: every
  hook passed.

**Implementation Notes**

- The badge points at `main`, which today holds only `.gitignore`, `LICENSE` and
  `README.md`, so the image stays broken until this branch is merged. PyPI shows
  the README from the next release on.

---

### DEV-009 — CI workflow

`Status`: `DONE` `Depends On`:
`DEV-004, DEV-005, DEV-006, DEV-007, DEV-008, DEV-013, DEV-014` `Acceptance`:
`AC-042, AC-045`

**Goal**

Add the GitHub Actions workflow from design decision 8 and the CI contract.

**Affected Area**

New `.github/workflows/ci.yml`.

**Expected Outcome**

On pull requests to `main` (Dependabot's included) and pushes to `main`, one
named job on `ubuntu-latest` installs one exact uv that meets `required-version`
(with a comment saying it is kept by hand), uses Python 3.13 from
`.python-version`, and runs `just install`, every lint recipe, `just test` and
`prek run --all-files`, each through `uv run --locked`. It fails if any of them
fails, including a hook that modifies files. The zizmor step gets `GH_TOKEN`
from `github.token`, so the online audits run. `permissions: contents: read`,
`timeout-minutes`, a concurrency group, `persist-credentials: false` on
checkout, and third-party actions pinned by commit SHA with a version comment.
The workflow passes zizmor.

**Self-Check**

The zizmor recipe and a YAML check over the workflow, and a review against the
CI contract. The workflow cannot run from this session; it stays unverified
until the user pushes the branch.

Evidence (2026-11-16, uncommitted working tree):

- `.github/workflows/ci.yml`: on pull requests to `main` and pushes to `main`;
  `permissions: contents: read`; a concurrency group per workflow and ref with
  `cancel-in-progress`; one job, "Lint and test", on `ubuntu-latest` with
  `timeout-minutes: 20`. Steps: `actions/checkout` v7.0.1 (same SHA as the
  TruffleHog workflow) with `persist-credentials: false`; `astral-sh/setup-uv`
  v10.3.3 pinned to commit `68559e99cc807c1eb7e9238fd43a15bba460eec2` (the
  latest tag, a lightweight tag on that commit, from `git ls-remote`) with
  `version: "0.13.8"` and a "Kept by hand" comment; then
  `uv run --locked just install`,
  `uv run --locked prek run --all-files --show-diff-on-failure` and
  `uv run --locked just lint` (both with `GH_TOKEN: ${{ github.token }}` so
  zizmor runs its online audits), `git diff --exit-code`, and
  `uv run --locked just test`. Python 3.13 comes from `.python-version`.
- `zizmor --persona=auditor .` (offline): no findings. actionlint 1.7.12 (run
  once with `uvx --from actionlint-py`, not added to the repo) on both
  workflows: exit 0. `uv run --locked prek run --all-files` in the repo: every
  hook passed.
- Rehearsal of the job's commands, in order, in a clean committed scratch copy
  with no `.env` files and no `GH_TOKEN`: install, every hook, every lint
  recipe, `git diff --exit-code` and the tests all exited 0. With an unformatted
  module committed, the hook step failed (`ruff format`); with that module
  checked out again, `just lint` reformatted it and `git diff --exit-code`
  exited 1.
- Not verified here: a run on GitHub (setup-uv, the managed Python download on
  the runner, the token-backed zizmor audits), which needs the branch pushed.

**Implementation Notes**

- The hooks run before the lint recipes, and a `git diff --exit-code` step
  follows the recipes, so neither a hook nor a recipe can fix a file silently in
  CI.
- `GH_TOKEN` is set only on the two steps that run zizmor, not job-wide.
- No STANDARDS file is needed: the Markdown runner skips the STANDARDS check
  where STANDARDS is not installed.

---

### DEV-010 — Clean-checkout run and user sign-off of the repo setup

`Status`: `IN_PROGRESS` `Depends On`:
`DEV-003, DEV-009, DEV-016, DEV-017, DEV-018, DEV-019` `Acceptance`:
`AC-002, AC-042, AC-043, AC-044, AC-045, AC-041`

**Goal**

Show the user the finished setup working from a clean copy and record their
sign-off before any pipeline code exists.

**Affected Area**

This plan (sign-off record); a scratch copy of the tracked and new files.

**Expected Outcome**

In a fresh copy with no `.env*` files and no system Node on the path the recipes
use, `just install`, every lint recipe, `just test`, `prek run --all-files` and
`check.mjs` all pass, and there is no `Makefile`. If the user has pushed the
branch, the CI run and GitHub's check of the Dependabot file are reviewed too.
The user has reviewed the setup and signed it off; the date and what was signed
off are recorded here.

**Self-Check**

The commands above in the scratch copy, with actual output recorded; the user's
sign-off message.

Evidence (2026-11-16):

- Clean checkout: `git clone` of the branch at `48cbd00` (all repo-setup
  commits, pushed to `origin/tz6/port-over`) into a new temporary folder. Run
  with an empty environment except `HOME`, the sandbox proxy settings and `PATH`
  = scratch uv 0.13.8 plus `/usr/bin:/bin:/usr/sbin:/sbin`: no `node` and no
  `python3.13` on `PATH`, no `Makefile`, no `.env*` files, fresh `PREK_HOME` and
  Python install folders.
- In order, each exit 0: `uv run --locked just install` (synced the environment,
  installed the prek git hook),
  `uv run --locked prek run --all-files --show-diff-on-failure` (every hook
  passed), `uv run --locked just lint` (zizmor: no findings),
  `git diff --exit-code`, `uv run --locked just test` (1 passed). uv downloaded
  Python 3.13.18 for `.venv`; prek downloaded Node 24.22.3 for the Markdown
  hooks. `node .standards/bin/check.mjs` in the clone: passed.
- GitHub: the public API shows no pull request from `tz6/port-over` and no
  workflow runs on it, since CI runs on pull requests to `main` and pushes to
  `main`. GitHub reads `.github/dependabot.yml` only on the default branch, so
  neither the CI run nor GitHub's check of the Dependabot file has happened.
- Waiting for the user's sign-off of the repo setup (`AC-002`).

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

### DEV-012 — just and prek replace Make and pre-commit

`Status`: `DONE` `Depends On`: `DEV-001` `Acceptance`: `AC-042, AC-043`

**Goal**

Switch the task runner to just and the hook runner to prek in one step, so the
repo always has a working entry point (design decisions 3, 11 and 12, Build Plan
step 3).

**Affected Area**

`pyproject.toml` (dev group, `[tool.uv]`), `uv.lock`, new `justfile`, `Makefile`
(deleted), `README.md`.

**Expected Outcome**

- The dev group adds `rust-just`, `prek` and `zizmor` at exact pins (1.59.0,
  0.5.11 and 1.32.0 were the latest on 2026-11-16) and drops `pre-commit`;
  `uv.lock` is regenerated.
- `[tool.uv] required-version` is a lower bound: the oldest uv that reads this
  lock and handles the `[tool.uv]` settings in use (`cache-keys`,
  `config-settings-package`), and no newer than the uv Dependabot runs (0.13.7
  on 2026-11-16). Candidate versions are tried with `uv sync --locked` and the
  test recipe to find it.
- A root `justfile` with `install` (`uv sync --locked`), `test`, `clean` (only
  this repo's Python caches and build output; no `pnpm store prune`) and the one
  lint recipe that exists so far, the Makefile's Markdown format, ported as it
  is until `DEV-005` replaces it. `just --list` shows a one-line description per
  recipe, and recipes call tools through `uv run`. Whether `just install` also
  installs the prek git hook is settled with the user in this step.
- The `Makefile` is gone.
- `README.md` keeps its opening under-development statement and gains a short
  development section: prerequisites (git, a uv at or above the bound, a just at
  or above the justfile's minimum version) and the `just` commands.

**Self-Check**

`just --list`; `just install` and `just test` with the lowest allowed uv and
with the newest; `uv lock --check`; `uv run --locked just test`; `git grep` for
`make` and `pre-commit` commands outside STANDARDS paths (only
`.pre-commit-config.yaml`, which `DEV-006` rewrites, may still have them).

Evidence (2026-11-16, uncommitted working tree on `cd6b470`, uv 0.13.8 from the
scratch tool directory as in `DEV-001`, `PREK_HOME` and `UV_CACHE_DIR` in the
session temp directory because the agent sandbox cannot write to `~/.cache`):

- `uv lock`: removed `pre-commit` 4.3.0 (and its `virtualenv` and
  `python-discovery`), added `prek` 0.5.11, `rust-just` 1.59.0 and `zizmor`
  1.32.0; 53 packages, lock `revision = 5`. `uv lock --check` passes after
  `required-version` became `>=0.8.1`.
- Lower uv bound: a script copied the project to a scratch directory, ran
  `uv sync --locked` with a given uv, checked that `uv.lock` was not rewritten,
  that `pydelity` imports from the strict editable tree with no `src` entry on
  `sys.path`, that the tests pass, and that a new module under `src/pydelity/`
  is picked up. Passed: 0.8.1, 0.8.24, 0.9.30, 0.10.0, 0.13.7, 0.13.8. Failed:
  0.7.0 and 0.8.0, whose installs ignore `config-settings-package` and put
  `src/` on the path (uv's changelog adds it in 0.8.1). uv 0.8.24 and 0.9.15
  panicked inside the agent sandbox while reading macOS proxy settings
  (`system-configuration`, "Attempted to create a NULL object"); 0.8.24 passed
  when rerun outside the sandbox, so the panic is a sandbox effect. 0.8.1 is at
  or below Dependabot's uv (0.13.7).
- Lower just bound: rust-just 1.35.0 (the oldest on PyPI) and 1.59.0 both list
  the recipes, run `just test` (1 passed) and dry-run `clean` and `install`.
- Scratch git copies with uv 0.8.1 and with uv 0.13.8, both with just 1.35.0: no
  `Makefile`; `just install` synced the environment and installed
  `.git/hooks/pre-commit` through prek; `just test` 1 passed; `uv.lock`
  unchanged; `pydelity` imported from
  `build/__editable__.pydelity-0.0.1-py3-none-any/`. In the 0.13.8 copy,
  `just clean` removed `.venv`, `build` and `dist`, and `just install` then
  `just test` worked again.
- Repo: `uv run --locked just --version` is 1.59.0 and
  `uv run --locked just test` 1 passed. The prek hook was not installed in the
  user's checkout.
- `git grep` outside STANDARDS paths: no `make` command; `pre-commit` appears
  only in `.pre-commit-config.yaml` (a repo URL and a comment) and in a comment
  in `scripts/check_env_template.py` naming that file, both left for `DEV-006`.
  `.pylintrc` has the English phrase "To make it work" and goes in `DEV-004`.

**Implementation Notes**

- `just clean` also removes `.venv` and `build/`, as the old backend `clean`
  did: the strict editable install lives in `build/`, so removing one without
  the other would leave a broken environment.
- The ported `lint-markdown` recipe still calls an unpinned `npx prettier`, as
  the design's Build Plan step 3 asks ("the lint recipes that exist so far");
  `DEV-005` replaces it.
- Until `DEV-006` and `DEV-004` fix the hook configuration, running
  `just install` in the user's checkout would install a git hook whose Python
  and env hooks fail, blocking commits.

---

### DEV-013 — zizmor checks the workflows

`Status`: `DONE` `Depends On`: `DEV-006` `Acceptance`: `AC-045`

**Goal**

Run zizmor over the repo as a lint recipe and a prek hook, and fix the existing
TruffleHog workflow until it passes (design decision 13 and the zizmor
contract).

**Affected Area**

`justfile` (lint recipe), `.pre-commit-config.yaml` (local zizmor hook),
`.github/workflows/trufflehog-pr.yml`, `.github/zizmor.yml` only if a finding
has to be ignored in config.

**Expected Outcome**

- `zizmor --persona=auditor .` from the dev group runs as part of the lint
  recipes and as a local prek hook through `uv run`. It never runs with `--fix`,
  `--min-severity`, `--min-confidence` or `--no-online-audits`, and no audit is
  disabled. Locally it runs offline unless a GitHub token is in the environment.
- `trufflehog-pr.yml` passes: for example `actions/checkout` sets
  `persist-credentials: false`, and the job has a name and a concurrency limit.
- A finding is fixed wherever possible. One that is accepted is ignored for that
  finding only, inline or in `.github/zizmor.yml`, with its reason written
  beside it.

**Self-Check**

The zizmor recipe and `uv run --locked prek run zizmor --all-files` exit 0; the
summary's suppressed count matches the written ignores. Limitation: the online
audits need a token, so they first run in CI (`DEV-009`).

Evidence (2026-11-16, uncommitted working tree, `PREK_HOME` and `UV_CACHE_DIR`
in the session temp directory, no GitHub token, so zizmor ran offline):

- Before the fix, `zizmor --persona=auditor .` (1.32.0) audited
  `trufflehog-pr.yml` and `.pre-commit-config.yaml` and reported 3 findings, all
  in the workflow: `artipacked` (checkout without `persist-credentials: false`),
  `anonymous-definition` (job without a name) and `concurrency-limits` (no
  concurrency setting); exit 13.
- Fix in `trufflehog-pr.yml`: `persist-credentials: false` on checkout (the scan
  reads only the local clone), job name "TruffleHog secret scan",
  `timeout-minutes: 10`, and a workflow concurrency group on
  `${{ github.workflow }}-${{ github.ref }}` with `cancel-in-progress: true`.
  Actions stay pinned by SHA.
- After: `uv run --locked just lint-workflows` printed "No findings to report";
  no finding is suppressed and no ignore was needed, so there is no
  `.github/zizmor.yml`. `uv run --locked prek run --all-files`: every hook
  passed, `zizmor` included. `uv run --locked just lint` exited 0.
- Not verified here: the online audits (`impostor-commit`,
  `known-vulnerable-actions`, `ref-confusion`, `stale-action-refs`), which need
  a token and first run in CI (`DEV-009`), and the workflow itself, which runs
  only on GitHub.

**Implementation Notes**

- The job's check name on pull requests changes from `trufflehog` to "TruffleHog
  secret scan". If branch protection requires the old name, the required check
  has to be updated.
- The zizmor hook runs when anything under `.github/` or the hook config
  changes, and always audits the whole repo, so the Dependabot file from
  `DEV-014` is covered without changes.

---

### DEV-014 — Dependabot keeps the pins current

`Status`: `DONE` `Depends On`: `DEV-005, DEV-013` `Acceptance`: `AC-044, AC-045`

**Goal**

Add the Dependabot configuration from design decision 13 and the Dependabot
contract, and mark every pin Dependabot cannot update as kept by hand.

**Affected Area**

New `.github/dependabot.yml`; comments beside hand-kept pins in `pyproject.toml`
and `.pre-commit-config.yaml`.

**Expected Outcome**

- `.github/dependabot.yml` is `version: 2` with `uv`, `pre-commit` and
  `github-actions` updaters for `/`, each with a schedule and
  `cooldown.default-days` of at least 7, and none allowing insecure external
  code execution. Schedule, grouping and pull-request limits are chosen with the
  user.
- `required-version`, Node's `language_version` and prettier's
  `additional_dependencies` pin each carry a comment saying they are kept by
  hand; `DEV-009` adds the same comment beside CI's uv version.
- zizmor passes on the new file.

**Self-Check**

The zizmor recipe; a YAML check; validation against the published Dependabot
configuration schema. GitHub itself validates the file only once the branch is
pushed, so that part stays unverified until then.

Evidence (2026-11-16, uncommitted working tree):

- GitHub's Dependabot options reference (fetched 2026-11-16) lists
  `github-actions`, `pre-commit` and `uv` as ecosystems, says `cooldown`
  `default-days` works for all three, and marks `enable-beta-ecosystems` as not
  in use, so no beta flag is needed.
- `.github/dependabot.yml`: `version: 2`; `github-actions`, `pre-commit` and
  `uv` updaters for `/`, each monthly, `cooldown.default-days: 7`, one group
  with `patterns: ["*"]`, and commit prefix `ci(deps)` (actions) or
  `build(deps)` (the other two); no `insecure-external-code-execution`.
- `uvx check-jsonschema --builtin-schema vendor.dependabot` (0.39.0): "ok --
  validation done".
- `uv run --locked zizmor --persona=auditor .` audited `.github/dependabot.yml`,
  the workflow and the hook config: no findings. A scratch copy with
  `default-days: 3` got three `dependabot-cooldown` warnings, so the audit does
  cover the file.
- Pin inventory: dev-group pins and `uv.lock` (uv updater); the
  `pre-commit-hooks` and `markdownlint-cli2` hook revs (pre-commit updater); the
  `actions/checkout` and `trufflehog` SHAs (github-actions updater). Kept by
  hand, each with a comment beside it: `required-version` in `pyproject.toml`
  (comment added here), Node `language_version` on both Markdown hooks and
  prettier's `additional_dependencies` (comments from `DEV-005`); CI's uv comes
  in `DEV-009`.
- `uv lock --check` passed; `uv run --locked prek run --all-files`: every hook
  passed on the second run (the first rewrapped this plan).
- Not verified here: GitHub's own validation of the file, which runs only once
  the branch is pushed.

**Implementation Notes**

- Within each updater, `package-ecosystem` comes first and the other keys are
  alphabetical; the updaters are in alphabetical order of ecosystem.
- `.python-version` (`3.13`) is a design decision (CI tests 3.13), not a version
  to keep current, so it has no updater or comment.
- If Dependabot's uv updater proposes raising `setuptools>=77` in
  `[build-system]`, add an `ignore` with a comment rather than accepting it
  (design risk).

---

### DEV-015 — pyproject.toml in alphabetical order

`Status`: `DONE` `Depends On`: `DEV-004` `Acceptance`: `AC-002, AC-042`

**Goal**

Order `pyproject.toml` alphabetically, as the user asked on 2026-11-16, without
changing any setting.

**Affected Area**

`pyproject.toml` only.

**Expected Outcome**

Tables appear in alphabetical order of their full names, keys are alphabetical
within each table, and lists whose order has no meaning (keywords, coverage
patterns, interrogate patterns) are alphabetical. Each table's comment moves
with it; the old group banners go. Every setting keeps its value.

**Self-Check**

Load the old and new files with `tomllib` and compare them, ignoring the order
of the reordered lists; `uv lock --check`; Ruff, ty, interrogate and the test
recipe still pass.

Evidence (2026-11-16, uncommitted working tree): `tomllib` loads of the old and
new files compare equal once `keywords`, the coverage `exclude_lines` and `omit`
lists and interrogate's `ignore-regex` are compared as sorted lists. The 18
tables run `build-system` to `tool.uv` in `LC_ALL=C` sort order.
`uv lock --check` passed; `uv run --locked just lint-python` passed (Ruff, ty,
interrogate 100 %); `uv run --locked just test`: 1 passed.

---

### DEV-016 — README lists every just recipe and how to get the tools

`Status`: `DONE` `Depends On`: `DEV-009` `Acceptance`: `AC-002, AC-042`

**Goal**

As the user asked on 2026-11-16 while reviewing the setup for sign-off: the
README names every just recipe and tells people how and where to get prek (and
just), since not everyone has them installed.

**Affected Area**

`README.md` (the Development section; the README is also the PyPI page).

**Expected Outcome**

The Development section lists the prerequisites, explains that prek and the
other dev tools come with `just install` (installed into `.venv` from
`uv.lock`), gives optional global installs for prek and just with links to their
docs, and lists every recipe in the justfile (`just`, `clean`, `install`,
`lint`, `lint-markdown`, `lint-python`, `lint-workflows`, `test`) with what each
does.

**Self-Check**

Compare the README's recipe list with `just --list`; the Markdown hooks; a
scratch `uv build` with `twine check --strict`.

Evidence (2026-11-16, uncommitted working tree on `48cbd00`; the user had fixed
the "ocally" typo in `ci.yml`):

- `README.md` Development section: Prerequisites (git, uv 0.8.1+, just 1.35.0+
  with `uv tool install rust-just` or `brew install just`); a paragraph saying
  prek, Ruff, ty, interrogate, pytest and zizmor come with `just install` from
  the lock, with `uv run` as the way to call them; optional global installs of
  prek (`uv tool install prek`, `brew install prek`, linking prek's installation
  guide) and `uv run --locked just <recipe>` for people without just; a Commands
  table of every recipe; a note on what the git hook does.
- Install commands checked against each tool's docs: just's packages page lists
  `brew install just` and `uv tool install rust-just`; prek's installation page
  lists `uv tool install prek` and `brew install prek`. All five new links
  returned HTTP 200. `uv run --locked just <recipe>` without just on `PATH` was
  shown in `DEV-010`'s clean checkout.
- The README table's recipes equal `just --summary` minus `default` (clean,
  install, lint, lint-markdown, lint-python, lint-workflows, test), plus a
  `just` row for listing.
- `just lint-markdown` formatted the README table (Prettier) and passed
  markdownlint; a scratch `uv build` passed `twine check --strict`;
  `uv run --locked prek run --all-files`: every hook passed.

---

### DEV-017 — More file checks, stricter tests and scripts linted

`Status`: `DONE` `Depends On`: `DEV-016` `Acceptance`: `AC-002, AC-042`

**Goal**

The setup additions the user agreed on 2026-11-16 before sign-off: more generic
file checks, stricter pytest with tests in random order, a `test` recipe that
stops at the first failure unless `KEEP_GOING=1`, `scripts/` linted like `src/`
and `tests/`, and prek environments cached in CI. (No `.editorconfig`, at the
user's request.)

**Affected Area**

`.pre-commit-config.yaml`, `pyproject.toml` and `uv.lock`, `justfile`,
`scripts/check_env_template.py`, `.github/workflows/ci.yml`, `README.md`.

**Expected Outcome**

- prek runs `check-toml`, `check-merge-conflict`, `check-added-large-files`,
  `check-case-conflict`, `mixed-line-ending` and `detect-private-key` from
  `pre-commit-hooks`; `mixed-line-ending`, which rewrites files, excludes
  STANDARDS paths.
- pytest runs with `--strict-markers`, `--strict-config` and
  `xfail_strict = true`, and in random order (`pytest-randomly`, which prints
  the seed to reproduce an order).
- `just test` stops at the first failure. With `KEEP_GOING=1` it runs every test
  and writes all failures and errors to `.cache/test-errors` (gitignored).
- The Python lint recipe and hooks cover `scripts/`, and
  `scripts/check_env_template.py` passes Ruff, ty and interrogate.
- CI caches prek's hook environments, keyed on the hook config and `uv.lock`,
  with `actions/cache` pinned by SHA.
- The README describes the test options.

**Self-Check**

prek over all files; `just lint`; `just test` with a passing and a failing
scratch test, with and without `KEEP_GOING=1`; two runs show different seeds;
zizmor and actionlint on the workflow.

Evidence (2026-11-16, uncommitted working tree on the user's latest commit):

- Hooks: the six `pre-commit-hooks` v6.0.0 ids were confirmed in that release's
  hook manifest and added in alphabetical order; `mixed-line-ending` excludes
  STANDARDS paths like the other two writing hooks. Run over all files: all six
  passed and changed nothing.
- pytest: `addopts = ["--strict-config", "--strict-markers"]`,
  `xfail_strict = true`, the `costs-money` marker now has a description, and
  `pytest-randomly` 5.1.0 is in the dev group (lock: 26 packages). A scratch
  test with an unregistered marker failed collection; two runs printed different
  seeds; `--randomly-seed=1234` reran with that seed.
- `just test`: with two failing scratch tests (removed afterwards) the default
  run stopped after 1 failure (exit 1); `KEEP_GOING=1` ran all (2 failed, 1
  passed, exit 1) and `.cache/test-errors` held the FAILURES section with both
  failures and pytest's short summary. With all tests passing, `KEEP_GOING=1`
  exited 0 and the file held the final summary line. `.cache/` is gitignored and
  `just clean` now removes it. The recipe also ran under just 1.35.0.
- `scripts/`: `scripts/check_env_template.py` gained a module docstring,
  one-line docstring summaries (`D205`), hyphens instead of en dashes (`RUF001`)
  and a split long line (`E501`); messages are otherwise unchanged. The
  `lint-python` recipe and the `ruff-check`, `ruff-format`, `ty` and
  `interrogate` hooks now cover `scripts/`; all passed, interrogate at 100 %.
- CI: an `actions/cache` v5.1.0 step (lightweight tag on commit
  `caa296126883cff596d87d8935842f9db880ef25`) caches `~/.cache/prek`, prek's
  documented default on Linux, keyed on `.pre-commit-config.yaml` and `uv.lock`.
  zizmor: no findings; actionlint 1.7.12: exit 0.
- README: the `just test` row and a short Tests section describe stopping at the
  first failure, `KEEP_GOING=1`, `.cache/test-errors` and replaying a seed.
- `uv lock --check`, `uv run --locked just lint` (exit 0) and
  `uv run --locked prek run --all-files` (every hook) all passed.

**Implementation Notes**

- The `test` recipe is a bash script recipe. Its raw log goes to
  `.cache/test-output` and is deleted on exit, so it needs no system temp
  folder.
- CI still runs `just test`, which stops at the first failure; setting
  `KEEP_GOING=1` there would report every failure in one run.

---

### DEV-018 — Dev tools at their latest stable releases

`Status`: `DONE` `Depends On`: `DEV-017` `Acceptance`: `AC-002, AC-042`

**Goal**

As the user asked on 2026-11-16: check PyPI for every pinned tool in
`pyproject.toml` and move the outdated ones to their latest stable release.

**Affected Area**

`pyproject.toml` (`dev` group) and `uv.lock`.

**Expected Outcome**

Every `dev` pin is the latest stable release on PyPI on 2026-11-16 (pytest 8.2.0
to 9.2.0 and pytest-cov 7.0.0 to 7.1.0; the other eight already were), the lock
matches, and every recipe and hook still passes.

**Self-Check**

`uv lock --check`; `just test`, `KEEP_GOING=1 just test`, `just lint`; prek over
all files.

Evidence (2026-11-16, uncommitted working tree): PyPI's JSON API, one request
per package, showed detect-secrets 1.5.0, interrogate 1.7.0, prek 0.5.11,
pytest-randomly 5.1.0, ruff 0.17.5, rust-just 1.59.0, ty 0.0.104 and zizmor
1.32.0 already at their latest release, and pytest (9.2.0, 2026-10-27) and
pytest-cov (7.1.0, 2026-03-21) behind; none of the latest releases is a
pre-release or yanked. After the bump, `uv lock` updated both and added pygments
2.21.0 (a new pytest dependency); 27 packages; `uv lock --check` passed.
`just test` (pytest 9.2.0, cov 7.1.0, randomly 5.1.0): 1 passed;
`KEEP_GOING=1 just test` with a failing scratch test (removed afterwards) exited
1 and `.cache/test-errors` began with the FAILURES header and ended with the
summary; an unregistered marker still failed collection;
`pytest -W error::DeprecationWarning` passed; `uv run --locked just lint` exited
0; `uv run --locked prek run --all-files`: every hook passed. The
`setuptools>=77` build requirement is a lower bound, not a pin, and stays.

---

### DEV-019 — README explains how to add, remove and upgrade dependencies

`Status`: `DONE` `Depends On`: `DEV-018` `Acceptance`: `AC-002, AC-042`

**Goal**

As the user asked on 2026-11-16: the README's Development section explains how
to add, remove and upgrade a third-party library and what to run afterwards.

**Affected Area**

`README.md`.

**Expected Outcome**

A Dependencies subsection with the uv commands for dev tools (exact pins) and
runtime dependencies (minimum versions), removing and upgrading, hand edits and
rebuilding `.venv`, and what to run and commit afterwards, matching how uv
0.13.8 behaves in this repo.

**Self-Check**

Each command tried in a scratch copy; the Markdown recipe; a scratch `uv build`
with `twine check --strict`.

Evidence (2026-11-16, uncommitted working tree, uv 0.13.8): in scratch copies of
the project, `uv add --dev "pytest-timeout"` wrote `>=2.4.0` and
`uv add --dev "pytest-timeout==2.4.0"` an exact pin, both in alphabetical place;
`uv add --dev "pytest-randomly==5.0.0"` replaced the existing pin, relocked and
installed 5.0.0; `uv add requests` and `uv add pyyaml` wrote `>=` minimums in
alphabetical order; `uv lock --upgrade-package`, `uv remove` and
`uv remove --dev` worked; after a hand edit `uv sync --locked` (what
`just install` runs) refused the stale lock until `uv lock`. The README's new
Dependencies subsection gives those commands, the exact-pin versus minimum rule,
and what to run and commit afterwards. `just lint-markdown` formatted the README
table and markdownlint passed; a scratch `uv build` passed
`twine check --strict`; `uv run --locked prek run --all-files`: every hook
passed.

---

## Plan Notes

- **Approval.** The user approved the first version of this plan on 2026-11-16
  (STEPWISE, user style `tony`, its defaults). The version revised after the
  rework below was approved by the user on 2026-11-16.
- **Rework reconciliation (2026-11-16).** Suspended Assignment 1 was restored on
  the `RESUME` from `ARCHITECTING` (frame 1 closed). The scope retired `AC-001`
  for `AC-042` (just and prek) and added `AC-043` (no Make or pre-commit
  commands), `AC-044` (Dependabot) and `AC-045` (zizmor); the design made
  `required-version` a lower bound and added decisions 11 to 13.
  - `DEV-001` stays `DONE`: its layout, packaging, lock and smoke-test outcomes
    stand. Its Makefile targets and exact uv pin are superseded by `DEV-012`.
  - `DEV-002`, `DEV-003` and `DEV-011` are unaffected (`AC-040`).
  - `DEV-004` to `DEV-010` are revised for just, prek, zizmor and Dependabot.
    `DEV-006` now holds the prek hook configuration, including the env-template
    hook entry that was in `DEV-007`, and `make clean` moved from `DEV-008` to
    `DEV-012`.
  - New: `DEV-012` (just and prek), `DEV-013` (zizmor), `DEV-014` (Dependabot).
- **Order.** `DEV-012`, then `DEV-006`. After that `DEV-004`, `DEV-005`,
  `DEV-007`, `DEV-008` and `DEV-013` in the order the user prefers, `DEV-014`
  once `DEV-005` and `DEV-013` are done, then `DEV-009` and `DEV-010`. STEPWISE
  pauses after every step.
- **Interactive setup.** The scope makes setup user-directed. When the user
  points out a further change inside the design's contracts, it is folded into
  the matching pending step or added as a new `DEV-NNN` and shown before it is
  made. A change that would alter the scope or design is routed to its owner.
- **Decisions (defaults unless the user says otherwise):**
  - uv: `required-version` is a lower bound found in `DEV-012` (design decision
    3), replacing the exact `==0.13.8` chosen at first approval. The user's uv
    is 0.13.8.
  - Public author and maintainer: `IDinsight DSEM` `<dsem@idinsight.org>`.
    Project URLs point at `https://github.com/IDinsight/pydelity` (public since
    2026-11-16).
  - Python tooling (`DEV-004`), as the user chose on 2026-11-16: Ruff wherever
    it covers the check, interrogate kept with its badge, pylint and cloc
    dropped, ty in place of mypy, leftover test plugins removed.
  - The empty `cli/` and `utils/` subpackages are dropped; the next cycle adds
    the Typer CLI.
  - Git hook (`DEV-012`), as the user chose on 2026-11-16: `just install` also
    runs `prek install`, so the hooks run before every commit.
  - Ordering, as the user asked on 2026-11-16: `justfile` recipes stay in
    alphabetical order (with `default` first, since just runs the first recipe),
    and so do `pyproject.toml` tables, keys and order-free lists.
  - Dependabot (`DEV-014`), as the user chose on 2026-11-16: monthly checks, one
    pull request per ecosystem, and `build(deps)` / `ci(deps)` commit messages.
  - Env files (`DEV-007`), as the user chose on 2026-11-16: `.template.env`
    keeps all eight variables, and `.envrc` keeps its `PROJECT_ENV` switch
    (local, development, production), with two changes the user approved:
    `PROJECT_ENV` defaults to `local` but can be set from the shell, and a
    missing env file is a warning rather than an error.
  - Leftovers (`DEV-008`), as the user chose on 2026-11-16: drop the stale
    `.gitignore` lines and untrack `.DS_Store`; keep the `data/`, `results/`,
    `logs/`, `caches/`, `secrets/` and `docs/_build/` ignores and the CODEOWNERS
    text; show the interrogate badge under the README title.
  - CI (`DEV-017` review), as the user chose on 2026-11-16: CI keeps running
    plain `just test`, which stops at the first failed test.
  - Extra Ruff rule families (`DEV-004`), as the user chose on 2026-11-16: `B`,
    `UP`, `SIM`, `C4`, `RET`, `RUF`, `PT` and `S`, on top of the chosen `E`,
    `W`, `F`, `I`, `D` (format only), `C90`, `PL` and `ANN`.
- **Smoke test.** The design's Build Plan step 1 put one smoke test in `DEV-001`
  so the test command has something to run. It is scaffold, not formal
  verification; Tester owns formal tests and may revise it.
- **Local ignored files under `backend/`.** `.venv/`, `.ruff_cache/` and
  `backend/.env.local` (empty, per the user, who asked for its removal on
  2026-11-16; not read) were deleted with `backend/`.
- **GitHub settings (2026-11-16).** At the user's request, Developer wrote a
  step-by-step walkthrough, checked against GitHub's docs that day, for:
  Dependabot alerts, Dependabot security updates (grouped), Secret Protection
  with push protection, private vulnerability reporting, and a branch ruleset on
  `main` (pull request required, the "Lint and test" and "TruffleHog secret
  scan" checks required, no force pushes or deletions). The user applies them in
  the repository settings; they are not repository files. Before the walkthrough
  `main` had only the IDinsight organization's Copilot code review ruleset. The
  user reported the settings on. GitHub's public API then showed, for `main`,
  ruleset 27420482 "Protect main" (active, repository): `deletion`,
  `non_fast_forward`, `pull_request` with 0 approvals and
  `required_status_checks` for "Lint and test" and "TruffleHog secret scan"
  (strict), beside the organization's Copilot ruleset; and private vulnerability
  reporting `enabled: true`. Dependabot alerts, security updates and push
  protection are visible only to repository admins, so they rest on the user's
  report. The user chose no bypass for themselves. The two required checks stay
  on "Any source" for now: GitHub lists an app as a check's source only after it
  has reported that check, and the source picker did not offer GitHub Actions
  before either check had run. After the first pull request to `main` runs them,
  the user switches both to GitHub Actions.
- **Commits.** No commit is made unless the user asks.
- **Styles loaded:** `styles/universal.md`, user style `tony`,
  `styles/python.md`; `styles/github-actions.md` for `DEV-009`, `DEV-013` and
  `DEV-014`.
- **Project references loaded:** `NONE`.

### Suspended Assignment 1

`Recovery Frame`: `1` `Recovery Reason`:
`User rework: replace Make with just and pre-commit with prek, and add Dependabot and zizmor; AC-001 names make and pre-commit.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`commit a5aacd0 (DEV-001, DEV-002, DEV-011 and DEV-003 done; pydelity 0.0.1 on PyPI)`
`Next Action`:
`Reconcile DEV-004 to DEV-010 with the corrected scope and design, get approval if the plan changes materially, then continue STEPWISE with the next approved step.`

Restored on 2026-11-16 when frame 1 closed; the reconciliation is recorded
above.

# Project Context

## Project Baseline

- pydelity is a Python library repository with the repo setup done and no
  pipeline code. `src/pydelity/__init__.py` holds only a module docstring ("has
  no public API yet") and `src/pydelity/py.typed`. There is no CLI, no console
  script and no runtime dependency (`dependencies = []` in `pyproject.toml`).
- Version `0.0.1` is a name-reserving placeholder. PyPI lists only `0.0.1`
  (wheel and sdist, uploaded 2026-11-16, `requires_python >=3.13`). The README
  and the package description say it is not yet usable, and the classifier is
  `Development Status :: 1 - Planning`.
- The repo setup was built in an earlier STANDARDS cycle on branch
  `tz6/port-over`, merged to `main` as pull request 1 on 2026-11-17 after
  STANDARDS was uninstalled (commit `6378f01`), so that cycle's records are
  gone. `artifacts/next_cycle_inputs.md` carries what this cycle needs from
  them.
- The working branch `tz6/pipeline` is `main` plus one commit (`5b15381`) that
  installs STANDARDS. Outside STANDARDS-owned paths the two branches are
  identical. `main` has no STANDARDS installation.
- `artifacts/design_brief.md` and `artifacts/next_cycle_inputs.md` are the
  cycle's request inputs (tracked in git). Some brief statements are now stale
  and are superseded by the active request and `next_cycle_inputs.md`:
  "STANDARDS installed in greenfield mode" (now `BROWNFIELD`); the repo-setup
  "done when" line naming `make` and `pre-commit` (now just and prek); "No
  pipeline code until it is signed off" (signed off); "Out of scope: Publishing
  to PyPI" (the active request publishes the working release); and the open
  questions, answered under "User decisions made while scoping the pipeline" in
  `next_cycle_inputs.md`.

## Stack and Tooling

- Python 3.13: `.python-version` is `3.13`, `requires-python = ">=3.13"`, Ruff
  `target-version = "py313"`. The local `.venv` runs Python 3.13.9.
- Build backend: setuptools (`requires = ["setuptools>=77"]`, needed for SPDX
  `license = "MIT"` with `license-files`), src layout
  (`[tool.setuptools] package-dir = {"" = "src"}`, packages found under `src`
  matching `pydelity*`).
- uv manages the environment and lock: `[tool.uv] required-version = ">=0.8.1"`
  (a lower bound kept at or below Dependabot's uv), CI pins uv `0.13.8`, local
  uv is 0.13.8. `uv.lock` holds 27 packages, all dev tools. The project installs
  as a strict editable install (`config-settings-package`,
  `editable_mode = "strict"`) so the environment sees only files a wheel would
  contain; `cache-keys` reinstall it when `pyproject.toml` or `src/pydelity/**`
  changes.
- Dev tools, exact pins in `[dependency-groups] dev`: detect-secrets 1.5.0,
  interrogate 1.7.0, prek 0.5.11, pytest 9.2.0, pytest-cov 7.1.0,
  pytest-randomly 5.1.0, ruff 0.17.5, rust-just 1.59.0, ty 0.0.104, zizmor
  1.32.0.
- Markdown tools run under prek with Node `24.22.3` (written in two hooks in
  `.pre-commit-config.yaml`): Prettier `3.10.1` through
  `scripts/format_markdown.mjs`, and markdownlint-cli2 `v0.24.1`.
- Task runner: just, with `set shell := ["bash", "-euo", "pipefail", "-c"]`; the
  `test` recipe is a bash shebang script using `tee` and `awk`, and `clean` uses
  `rm -rf` and `find`.
- The libraries the request names (Pydantic, pydantic-settings, PydanticAI,
  loguru, Typer) and PyMuPDF are not yet dependencies of pydelity.

## Structure and Boundaries

- `src/pydelity/` — the package; empty apart from the docstring module and
  `py.typed`.
- `tests/` — `tests/pydelity/test_package.py` (two smoke tests);
  `tests/conftest.py` and `tests/fixtures/__init__.py` exist with docstrings
  only.
- `scripts/` — `check_env_template.py` (the `env-template-sync` hook: `.env*`
  files and their `.template.env*` partners declare the same variable names) and
  `format_markdown.mjs` (formats Markdown with Prettier, guards STANDARDS files
  to whitespace-only changes, runs `.standards/bin/check.mjs` only when
  STANDARDS is installed).
- `.github/` — `workflows/ci.yml`, `workflows/release-please.yml`,
  `workflows/trufflehog-pr.yml`, `dependabot.yml`, issue templates, `CODEOWNERS`
  (`*` owned by the repo owner) and `pull_request_template.md`.
- Release config — `release-please-config.json`, `.release-please-manifest.json`
  (`".": "0.0.1"`); `CHANGELOG.md` does not exist yet and is written by
  release-please.
- `artifacts/` — the cycle's two input documents.
- STANDARDS-owned paths: `.standards/`, `.agents/`, `.claude/skills/`,
  `.claude/settings.json`, `.codex/hooks.json`, `AGENTS.md`, `CLAUDE.md`.
- Git-ignored local folders include `data/`, `results/`, `graveyard/`, `logs/`,
  `caches/`, `secrets/`, `build/`, `dist/`, `.cache`, and every `.env*` file
  except `.envrc` and `.template.env*` (`.gitignore`). `dist/` currently holds
  the `0.0.1` wheel and sdist.
- KGForEdGlobal (`/Users/tzz/Projects/private/idi/KGForEdGlobal`) is outside the
  repo and read-only for this cycle.

## Nearest Analogues

- pydelity has no pipeline, CLI or model-calling code to extend. Its only code
  analogue is `tests/pydelity/test_package.py`, which shows the test style:
  module and test docstrings, Ruff's import-section headings, a repo root from
  `Path(__file__).absolute().parents[2]`, plain `assert`, and tests that import
  the installed `pydelity` rather than `src/`.
- KGForEdGlobal stages 1–3 are the behavior pydelity replaces, under
  `backend/src/kgfeg/`: `page_ir_extraction/` (`agents.py` builds PydanticAI
  `Agent`s with `ModelRetry`; `llm.py` renders pages with `pymupdf` and sends
  them as `BinaryContent`; `validators.py`, `prompts.py`, `schemas.py`),
  `page_ir_verification/`, `document_ir/` (`stitch_segments.py`,
  `normalize_page_items.py`, `compute_page_break_links.py`), the entry points
  `entries/extract_page_ir.py`, `entries/verify_page_ir_continuity.py`,
  `entries/stitch_document_ir.py`, and `model_registry.py` (per-provider
  Anthropic and OpenAI `ModelSettings`). `utils/general.py` `AgentUsageBucket`
  accumulates token counts from PydanticAI `RunUsage`; no stage 1–3 code prices
  calls in money. Tests are under `backend/tests/kgfeg/` (`page_ir_extraction/`,
  `page_ir_verification/`, `document_ir/`, `test_regexes.py`). The brief's
  "Known defects in the source code to design out" lists behavior in these
  modules that pydelity must not carry over.

## Commands

- `just install` — `uv sync --locked`, then `uv run --locked prek install`.
- `just lint` — runs `lint-markdown`, `lint-python` and `lint-workflows`. These
  write fixes (Prettier, `ruff check --fix`, `ruff format`) before checking.
- `just lint-markdown` — Prettier through `scripts/format_markdown.mjs`, then
  `prek run markdownlint-cli2 --all-files`.
- `just lint-python` — Ruff fix and format, `ty check`, then `interrogate`, over
  `scripts src tests`.
- `just lint-workflows` — `zizmor --persona=auditor .`.
- `just test` — `uv run --locked pytest --exitfirst`; `KEEP_GOING=1 just test`
  runs every test and writes failures to `.cache/test-errors`.
- `just clean` — removes `.venv`, caches, `build`, `dist` and egg-info.
- `uv run --locked just <recipe>` — runs the pinned just when just is not on
  `PATH`.
- `uv run prek run --all-files` — every git hook on every file (CI adds
  `--show-diff-on-failure`).
- `uv run pytest --randomly-seed=<seed>` — repeats a random test order.
- Dependency changes: `uv add` / `uv remove` (`--dev` for dev tools), then
  commit `pyproject.toml` and `uv.lock` together (README "Dependencies").
- `node .standards/bin/check.mjs` — the STANDARDS consistency check.
- Not established: a build command for the wheel and sdist, a PyPI publish
  command, and any Windows equivalent of the just recipes. None is a recipe or
  documented, and the repo does not record how `0.0.1` was built or uploaded.

## Conventions and Constraints

- Ordering: `pyproject.toml` keeps tables, keys and order-free lists in
  alphabetical order (its header comment); justfile recipes follow `default` in
  alphabetical order.
- Ruff: line length 88; rule families ANN, B, C4, C90, D, E, F, I, PL, PT, RET,
  RUF, S, SIM, UP, W; McCabe complexity at most 10; NumPy docstrings with D202
  ignored (a blank line follows each docstring); D100–D107 ignored because
  interrogate checks presence; tests may use `assert` and magic values. Import
  sections carry headings "Future Library", "Standard Library", "Third Party
  Library", "Package Library", "Local Folder", with a blank line between
  `import` and `from` groups.
- interrogate requires 100% docstring coverage over `scripts`, `src` and
  `tests`, private and nested functions included (`ignore-regex` skips
  `mock_*`), and regenerates `interrogate_badge.svg` at the repo root.
- ty type-checks `scripts`, `src` and `tests`.
- Pins: dev tools exact (`==`); runtime dependencies get minimum versions (`>=`,
  as `uv add` writes) so pydelity installs alongside other packages (README).
  One pinned version per tool. Pins Dependabot cannot update carry a "Kept by
  hand" comment: uv's `required-version`, CI's uv `0.13.8`, Node `24.22.3`
  (twice) and Prettier `3.10.1`.
- Git hooks (prek, `.pre-commit-config.yaml`): pre-commit-hooks v6.0.0
  (`check-added-large-files` rejects new files over 500 KB, case conflicts,
  merge markers, TOML, YAML, private keys, end-of-file, line endings, trailing
  whitespace), Prettier, markdownlint-cli2, detect-secrets against
  `.secrets.baseline`, env-template-sync, Ruff check and format, ty, interrogate
  and zizmor. Hooks that rewrite files exclude STANDARDS-owned paths; Prettier
  may change STANDARDS Markdown only in whitespace.
- Markdown: Prettier wraps prose at 80 columns (`.prettierrc.yaml`);
  `.markdownlint-cli2.yaml` lints every tracked or untracked-but-not-ignored
  `*.md` file, STANDARDS records included, ignores inline disable comments
  (`noInlineConfig: true`) and turns off MD013, MD025, MD026, MD036 and MD041.
  `CHANGELOG.md` is excluded from both.
- GitHub Actions style: actions pinned by commit SHA with a version comment;
  least-privilege `permissions` (`contents: read`, or `{}`);
  `persist-credentials: false` on checkout; per-workflow `concurrency`;
  `timeout-minutes` on every job; zizmor audits workflows, the hook config and
  Dependabot with the `auditor` persona (CI passes `GH_TOKEN` for its online
  audits).
- Dependabot: github-actions (`ci(deps)`), pre-commit and uv (`build(deps)`),
  monthly, grouped, 7-day cooldown.
- Commits follow Conventional Commits; a squash-merged pull request's title
  becomes the commit message. release-please makes `fix:` a patch, `feat:` a
  minor and `!` or `BREAKING CHANGE:` a major release; other types make none
  (README "Releases").
- Repo tooling must keep working where STANDARDS is not installed
  (`scripts/format_markdown.mjs` header; `main` has no STANDARDS). Before a
  branch with a finished cycle merges to `main`, STANDARDS is uninstalled on it,
  as commit `6378f01` did for the repo setup.
- Secrets: `.env*` files are git-ignored; `.template.env` declares variable
  names only. Records and code never hold key values.
- The user's decisions, constraints, non-goals and assumptions for the pipeline
  are explicit user input in `artifacts/next_cycle_inputs.md` ("User decisions
  made while scoping the pipeline"; "Constraints, non-goals and assumptions
  scoped for the pipeline") and the brief's "User decisions" 1–10. Scoper turns
  them into this cycle's acceptance conditions; the brief's design directions
  are input for Architect.

## External Systems and Data

- PyPI project `pydelity`: only `0.0.1`, uploaded 2026-11-16. No workflow
  publishes to PyPI; README says releases are not published automatically.
- GitHub repository `IDinsight/pydelity` (read through `gh api`, 2026-11-17):
  - Ruleset `main` on the default branch blocks deletion and force pushes,
    requires pull requests, and requires the status checks "Lint and test" (job
    `check` in `ci.yml`) and "TruffleHog secret scan" (job `trufflehog` in
    `trufflehog-pr.yml`). Classic branch protection is not set. Ruleset
    "Automatic Copilot code review" applies to all branches.
  - Environments: `release-please` (custom deployment-branch policy) and
    `copilot`. No environment for PyPI publishing exists.
  - No git tags and no GitHub releases exist, although
    `.release-please-manifest.json` records `0.0.1`.
- release-please (`.github/workflows/release-please.yml`): runs on pushes to
  `main` and `workflow_dispatch` in the `release-please` environment, with
  `permissions: {}` and the fine-grained token secret
  `RELEASE_PLEASE_TOKEN_PYDELITY`, not the job token, so its pull requests and
  releases trigger other workflows. Config: `release-type: python`, tags
  `vX.Y.Z` without a component, and an `extra-files` jsonpath that bumps the
  `pydelity` version in `uv.lock`. It creates the GitHub release but does not
  publish.
- Model providers: `.template.env` declares `ANTHROPIC_API_KEY`,
  `OPENAI_API_KEY` and `LLM_ANTHROPIC_EFFORT`,
  `LLM_ANTHROPIC_THINKING_BUDGET_TOKENS`, `LLM_MAX_OUTPUT_TOKENS`,
  `LLM_OPENAI_REASONING_EFFORT`, `LLM_OPENAI_TEMPERATURE`, `LLM_OPENAI_TOP_P`.
  No pydelity code reads them yet. `.envrc` (direnv, bash) loads `.env` and then
  `.env.<PROJECT_ENV>` (`local`, `development` or `production`, default
  `local`).
- KGForEdGlobal's KG stage is the first consumer of `document.json`; see
  **KGForEdGlobal consumer contract** below.
- Sample PDFs live in KGForEdGlobal's `data/` (not in this repo):
  `funda_wande/caps_english_hl_grade_3_fs.pdf` (CAPS),
  `rwanda/rwanda_math_p1_p3.pdf`, `ghana/ghana_english_scope_and_sequence.pdf`,
  `ghana/ghana.pdf`, `ghana/ghana_english.pdf`, `nigeria/nigeria_maths_1_3.pdf`,
  `india/madhi/mathematics.pdf` and
  `india/pratham/learning_standards_science.pdf`. Seven past-run folders sit
  under KGForEdGlobal's `results/kg_for_ed/`, local and not in git. pydelity
  ignores `data/` and `results/`, and its hook rejects new files over 500 KB.

### KGForEdGlobal consumer contract

Read at KGForEdGlobal `tz6/page-ir-extraction-cleanup`, HEAD `5e2d7cc` (the
brief's pinned commit; clean working tree). Paths are under
`backend/src/kgfeg/`.

- How the KG stage reads today's output: `entries/create_kgs.py` (Typer command
  `create`, line 404) computes `doc_key` from the PDF, checks that
  `<output_dir>/<doc_key>/extraction/extraction_run.json` records the same
  `doc_key` (`kgs/utils.py:1323–1352`), and loads
  `<output_dir>/<doc_key>/stitching/document_ir.json` (`kgs/utils.py:1354–1359`)
  with `DocumentIR.model_validate` (`kgs/utils.py:907`). It then requires a
  matching `doc_key`, non-empty `pages` and `segments`, and unique `segment_id`
  values (`kgs/utils.py:907–933`). The file is `document_ir.json`, not
  `document.json` as the brief says.
- Every schema model inherits `BaseSchema` with
  `ConfigDict(extra="forbid", from_attributes=True)` (`schemas.py:255`), so any
  key the model does not declare, including a top-level `schema_version`, fails
  that validation. Today's KG stage therefore cannot read a pydelity
  `document.json` without KGForEdGlobal-side changes; the brief and
  `next_cycle_inputs.md` place those changes (an adapter, `create_kgs.py` taking
  a `document.json` path) in KGForEdGlobal, out of this cycle.
- Types, located in `document_ir/schemas.py` and `page_ir_extraction/schemas.py`
  (the brief's "schemas.py" holds only `BaseSchema`, `BBox` and
  `LanguageField`):
  - `DocumentIR` (`document_ir/schemas.py:959`): `coord_space: str`, `doc_key`,
    `dpi`, `page_count` (must equal `len(pages)`),
    `pages: list[DocumentPageMeta]`, `pdf_name`, `segments` (union of
    `BlockSegment` and `TableSegment` on `kind`), `warnings`.
  - `BlockSegment` (`:465`): `kind: "block"`, `block_type`, `text: TextUnit`,
    `combined_text`, `list_items`, `figure`, `local_code`, `section_path`,
    `segment_id`, `segment_provenance`, `slices`.
  - `TableSegment` (`:603`): `kind: "table"`, `n_cols`, `header_row_count`,
    `header_rows`, `header_rows_canonical`, `rows`, `rows_grid`,
    `rows_filldown`, `row_provenance` (one per row), `grid_sources`,
    `columns_signature`, `local_code`, `section_path`, `segment_id`,
    `segment_provenance`, `slices`, with shape validators (`:822`, `:872`,
    `:891`).
  - `TextUnit` (`page_ir_extraction/schemas.py:80`): `text`, `language`
    (BCP-47), `text_en`. `TableCell` (`:96`): `text`, `col_span`, `row_span`,
    `rowspan_placeholder` (implies `synthetic`), `synthetic`.
- Segment ID:
  `uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_key}:segment:{kind}:p{page_index:04d}:i{item_index:04d}")`,
  with `kind` `block` or `table` and 0-based page and item indexes of the
  chain's first item (`document_ir/stitch_segments.py:213–244`). `doc_key` is
  the full 64-hex SHA-256 of the PDF bytes (`utils/pdf.py:13`, lines 29–30).
- Coordinates: `BBox` is `[x0, y0, x1, y1]` in pixels, origin top-left
  (`schemas.py:218–226`, `page_ir_extraction/schemas.py:724–726`). 250 DPI is
  the `ExtractionConfig.dpi` default (`schemas.py:3314`), not a constant; the
  seven local past runs all used `px` at 250 DPI.
- `section_path`: a list of `SectionHeadingRef {item_index, page_index, text}`
  (`document_ir/schemas.py:335`), root first. The stitcher appends each heading,
  drops consecutive duplicates and keeps the last `max_section_path_length`
  (default 12, `schemas.py:3468`; example configs set 24, 40 or 60), and each
  segment takes a snapshot (`stitch_segments.py:2184–2190`, `:2442`). The KG
  reads it nearest-first as dicts (`kgs/sfi_extraction_windows.py:513`).
- Consumers: seven `kgs/` modules import from `kgfeg.document_ir.schemas`
  (`utils.py`, `sfi_extraction_windows.py`, `sfi_finalization.py`,
  `sfi_registry.py`, `sfi_export.py`, `lc_finalization.py`,
  `sfi_relationships.py`); only `kgs/utils.py:22` imports `TableCell` and
  `TextUnit`. `evals/` imports none and reads `document_ir.json` as raw JSON for
  `doc_key`, `pdf_name` and `page_count`
  (`evals/lp_eval/sampling.py:4045–4073`). The brief's field-use counts
  reproduce with substring `grep -r` over `kgs` and `evals`; whole-word counts
  are lower for `segment_id` (38 of 223), `section_path` (23 of 72),
  `grid_sources` (46 of 53) and `columns_signature` (19 of 31), and equal for
  `local_code`, `row_provenance`, `rows_grid` and `rows_filldown`.
- KGForEdGlobal's locked versions (`backend/uv.lock`): pydantic-ai 1.63.0,
  pydantic 2.12.5, PyMuPDF 1.26.7, typer 0.20.0, loguru 0.7.3, pydantic-settings
  2.12.0, and genai-prices 0.0.55 as a pydantic-ai-slim dependency; Python
  `>=3.13,<3.14`.

## Testing and Verification Baseline

- Tests: pytest with pytest-randomly (random order, seed printed) and
  pytest-cov; `addopts = ["--strict-config", "--strict-markers"]`,
  `xfail_strict = true`, `testpaths = ["tests"]`, and one registered marker,
  `costs-money` ("calls a paid model provider API"). Coverage is configured
  (`branch = true`, `source = ["pydelity"]`) but no run applies `--cov` or a
  threshold.
- Current suite: two smoke tests in `tests/pydelity/test_package.py`; the
  package imports, ships `py.typed`, reports the `pyproject.toml` version, and
  loads from the installed tree with `src/` absent from `sys.path`. Both pass
  (`.venv/bin/python -m pytest -q`, 2026-11-17).
- `[tool.coverage.report]` still holds scaffold entries: a `def cli` exclusion
  and an `omit` for `./src/pydelity/__init__.py`.
- CI (`ci.yml`, job "Lint and test"): one `ubuntu-latest` job on pull requests
  to and pushes to `main`; installs with `uv run --locked just install`, runs
  `prek run --all-files --show-diff-on-failure`, `just lint`, fails on any file
  the lint recipes changed (`git diff --exit-code`), then `just test`. Python
  comes from `.python-version` only. No Windows or macOS runner and no Python
  3.14 run exist.
- TruffleHog (`trufflehog-pr.yml`) scans each pull request's commits with
  `--only-verified`.
- No test, fixture or recipe exercises a model provider, a PDF, a built wheel,
  or Windows.

## Relevant Existing Behavior

- `import pydelity` has no side effects and needs no environment settings.
- The installed distribution's version comes from `pyproject.toml`
  (`version = "0.0.1"`, "Bumped by release-please's release pull requests, with
  uv.lock; not edited by hand").
- Merging a release-please pull request sets the version in `pyproject.toml` and
  `uv.lock`, tags `vX.Y.Z` and creates the GitHub release; a `feat:` commit
  reaching `main` opens the next minor release pull request.
- The README documents development only (prerequisites, just recipes,
  dependencies, tests, hooks, releases). It does not say the recipes need bash,
  and has no install-and-use section for the library.

## Known Unknowns

- PyPI-side settings for `pydelity` (owners, any Trusted Publisher) cannot be
  read from the repo; they decide what a publishing workflow needs.
- How release-please computes the first release when the manifest says `0.0.1`
  but no `v0.0.1` tag or GitHub release exists was not verified; it affects
  whether the next release is `0.1.0`.
- How `0.0.1` was built and uploaded is not recorded; `dist/` holds its files.
- No tooling has been run on Windows, so which recipes, hooks and scripts work
  there is unknown beyond the POSIX-shell dependencies listed above.

## Evidence

- `pyproject.toml`, `uv.lock`, `.python-version`, `justfile` — stack, pins, test
  and lint settings, recipes.
- `.pre-commit-config.yaml`, `.markdownlint-cli2.yaml`, `.prettierrc.yaml`,
  `.prettierignore`, `scripts/format_markdown.mjs`,
  `scripts/check_env_template.py` — hooks and Markdown rules.
- `.github/workflows/ci.yml`, `release-please.yml`, `trufflehog-pr.yml`,
  `.github/dependabot.yml`, `release-please-config.json`,
  `.release-please-manifest.json` — CI, release and update automation.
- `src/pydelity/__init__.py`, `tests/pydelity/test_package.py`, `README.md` —
  current package, tests and documentation.
- `.gitignore`, `.envrc`, `.template.env` (names only) — local files and
  environment variables.
- `git log`, `git diff main tz6/pipeline` — branch history and the STANDARDS
  install commit; `gh pr list` — pull requests 1 and 2 merged 2026-11-17.
- `gh api repos/IDinsight/pydelity/{rulesets,environments,tags}`,
  `gh release list` — rulesets, environments, no tags or releases.
- `https://pypi.org/pypi/pydelity/json` — published versions.
- `.venv/bin/python -m pytest -q` — two tests pass.
- `artifacts/design_brief.md`, `artifacts/next_cycle_inputs.md` — request inputs
  and user decisions.
- KGForEdGlobal paths cited above, read by path at `5e2d7cc`; the
  consumer-contract file and line references were checked against that commit
  (`git rev-parse HEAD`, `git status --porcelain`, `grep -r` over `kgs` and
  `evals`).

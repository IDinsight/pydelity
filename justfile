# pydelity task runner. Run `just` to list the recipes.
#
# Every tool comes from the locked dev environment (`uv.lock`) through `uv run`, so
# recipes, git hooks and CI use the same versions.

set shell := ["bash", "-euo", "pipefail", "-c"]

# List the available recipes
default:
    @just --list

# Build the wheel and sdist into a fresh dist/, then check their metadata as PyPI would
build:
    rm -rf dist
    uv build
    uv run --locked twine check --strict dist/*

# Remove the dev environment, caches and build output (run `just install` afterwards)
clean:
    rm -rf .venv build dist .cache .coverage .coverage.* htmlcov .pytest_cache .ruff_cache .mypy_cache
    rm -rf docs/.astro docs/dist docs/node_modules
    find . -name __pycache__ -type d -prune -exec rm -rf {} +
    find . -name '*.egg-info' -type d -prune -exec rm -rf {} +

# Install the docs site's packages from its lock file and serve the site with live reload
[working-directory: 'docs']
docs:
    pnpm install --frozen-lockfile
    pnpm run dev

# Build the docs site from the current tree, then check its internal links and fragments
[working-directory: 'docs']
docs-build:
    pnpm install --frozen-lockfile
    pnpm run build
    pnpm run check-links

# Regenerate the docs site's reference pages from the code (`lint` formats them)
docs-reference:
    uv run --locked python scripts/generate_reference_docs.py

# Create the dev environment from uv.lock (fails if the lock is out of date) and install the git hooks
install:
    uv sync --locked
    uv run --locked prek install

# Regenerate the docs site's reference pages, then run every lint recipe
lint: docs-reference lint-markdown lint-python lint-workflows

# Format every Markdown file with Prettier, then lint it with markdownlint
lint-markdown:
    uv run --locked prek exec prettier-markdown -- node scripts/format_markdown.mjs
    uv run --locked prek run markdownlint-cli2 --all-files

# Fix and format the Python code, then type-check it and check docstring coverage
lint-python:
    uv run --locked ruff check --fix scripts src tests
    uv run --locked ruff format scripts src tests
    uv run --locked ty check scripts src tests
    uv run --locked interrogate scripts src tests

# Audit the GitHub Actions workflows, the hook config and the Dependabot config with zizmor
lint-workflows:
    uv run --locked zizmor --persona=auditor .

# Run the tests in parallel, then the docstring examples in src/, in random order and stop at the first failure; KEEP_GOING=1 runs them all and writes every failure to .cache/test-errors
test:
    #!/usr/bin/env bash
    set -euo pipefail
    # The tests run in one worker process per CPU (pytest-xdist). The docstring
    # examples run in a pytest session of their own: collecting src/ puts it on
    # sys.path, which the tests forbid so that they use the installed package.
    if [[ "${KEEP_GOING:-0}" != "1" ]]; then
        uv run --locked pytest --exitfirst --numprocesses auto
        exec uv run --locked pytest --exitfirst --doctest-modules src
    fi

    # Run every test and example, show the output as usual, and keep pytest's failure
    # and error sections plus its short summaries in .cache/test-errors.
    mkdir -p .cache
    log=".cache/test-output"
    trap 'rm -f "$log"' EXIT
    status=0
    uv run --locked pytest --numprocesses auto --tb=long -rfE 2>&1 | tee "$log" || status=$?
    uv run --locked pytest --tb=long -rfE --doctest-modules src 2>&1 | tee -a "$log" || status=$?
    awk '/^=+ (FAILURES|ERRORS) =+$/ { keep = 1 } keep' "$log" > .cache/test-errors
    # With no failure, keep each session's summary line (an interpreter warning can
    # print after it, so the log's last line is not always the summary).
    if [[ ! -s .cache/test-errors ]]; then
        grep -E '^=+ .+ in [0-9.]+s' "$log" > .cache/test-errors || tail -n 1 "$log" > .cache/test-errors
    fi
    echo "Test failures and errors written to .cache/test-errors"
    exit "$status"

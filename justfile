# pydelity task runner. Run `just` to list the recipes.
#
# Every tool comes from the locked dev environment (`uv.lock`) through `uv run`, so
# recipes, git hooks and CI use the same versions.

set shell := ["bash", "-euo", "pipefail", "-c"]

# List the available recipes
default:
    @just --list

# Remove the dev environment, caches and build output (run `just install` afterwards)
clean:
    rm -rf .venv build dist .cache .coverage .coverage.* htmlcov .pytest_cache .ruff_cache .mypy_cache
    find . -name __pycache__ -type d -prune -exec rm -rf {} +
    find . -name '*.egg-info' -type d -prune -exec rm -rf {} +

# Create the dev environment from uv.lock (fails if the lock is out of date) and install the git hooks
install:
    uv sync --locked
    uv run --locked prek install

# Run every lint recipe
lint: lint-markdown lint-python lint-workflows

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

# Run the tests in random order and stop at the first failure; KEEP_GOING=1 runs them all and writes every failure to .cache/test-errors
test:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ "${KEEP_GOING:-0}" != "1" ]]; then
        exec uv run --locked pytest --exitfirst
    fi

    # Run every test, show the output as usual, and keep pytest's failure and error
    # sections plus its short summary in .cache/test-errors.
    mkdir -p .cache
    log=".cache/test-output"
    trap 'rm -f "$log"' EXIT
    status=0
    uv run --locked pytest --tb=long -rfE 2>&1 | tee "$log" || status=$?
    awk '/^=+ (FAILURES|ERRORS) =+$/ { keep = 1 } keep' "$log" > .cache/test-errors
    if [[ ! -s .cache/test-errors ]]; then
        tail -n 1 "$log" > .cache/test-errors
    fi
    echo "Test failures and errors written to .cache/test-errors"
    exit "$status"

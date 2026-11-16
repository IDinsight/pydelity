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
    rm -rf .venv build dist .coverage .coverage.* htmlcov .pytest_cache .ruff_cache .mypy_cache
    find . -name __pycache__ -type d -prune -exec rm -rf {} +
    find . -name '*.egg-info' -type d -prune -exec rm -rf {} +

# Create the dev environment from uv.lock (fails if the lock is out of date) and install the git hooks
install:
    uv sync --locked
    uv run --locked prek install

# Run every lint recipe
lint: lint-markdown lint-python

# Format Markdown with Prettier (to be replaced by the pinned Markdown tooling)
lint-markdown:
    npx prettier --write --prose-wrap always --print-width 80 --ignore-path .gitignore --ignore-path .prettierignore "**/*.md" "!CHANGELOG.md"

# Fix and format the Python code, then type-check it and check docstring coverage
lint-python:
    uv run --locked ruff check --fix src tests
    uv run --locked ruff format src tests
    uv run --locked ty check src tests
    uv run --locked interrogate src tests

# Run the test suite
test:
    uv run --locked pytest

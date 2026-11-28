---
title: Local development
description:
  Set up pydelity for development, and run its tests, linters and git hooks with
  just.
---

This page is for people changing pydelity itself. To use pydelity, see
[Install pydelity](../../start/install/).

## Prerequisites

- [git](https://git-scm.com/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.8.1 or later
- [just](https://just.systems/man/en/packages.html), a recent version, for
  example with `uv tool install rust-just` or `brew install just`. The repo pins
  just 1.59.0 in `pyproject.toml`.

Everything else is pinned in the repo, so you don't need to install it yourself.
[prek](https://prek.j178.dev/) (which runs the git hooks), Ruff, ty,
interrogate, pytest, twine and zizmor are pinned in `pyproject.toml` and
installed into `.venv` by `just install`. Run one directly with `uv run`, for
example `uv run prek run --all-files`. Prettier and markdownlint, and the
Node.js they run on, are pinned in `.pre-commit-config.yaml`. prek sets them up
the first time a git hook or `just lint-markdown` needs them.

Without just installed, `uv run --locked just <recipe>` runs the pinned just
instead. If you'd rather have `prek` on your `PATH` too, install it with
`uv tool install prek` or `brew install prek` (see
[prek's installation guide](https://prek.j178.dev/installation/)).

The docs site needs Node.js and pnpm as well. See
[The docs site](../docs-site/).

The recipes use bash, so on Windows run them from Git Bash or WSL.

## Get started

```sh
git clone https://github.com/IDinsight/pydelity.git
cd pydelity
just install
just test
```

## Commands

| Command               | What it does                                                                                                   |
| --------------------- | -------------------------------------------------------------------------------------------------------------- |
| `just`                | List every recipe                                                                                              |
| `just build`          | Build the wheel and sdist into a fresh `dist/`, then check their metadata as PyPI would                        |
| `just clean`          | Remove `.venv`, caches and build output (run `just install` afterwards)                                        |
| `just docs`           | Serve the docs site with live reload                                                                           |
| `just docs-build`     | Build the docs site, then check its internal links                                                             |
| `just docs-reference` | Regenerate the docs site's reference pages from the code, unformatted until `just lint-markdown` runs          |
| `just install`        | Create `.venv` from `uv.lock` (fails if the lock is out of date) and install the prek git hook                 |
| `just lint`           | Regenerate the reference pages, then run every lint recipe below                                               |
| `just lint-markdown`  | Format every Markdown file with Prettier, then lint it with markdownlint                                       |
| `just lint-python`    | Fix and format the Python code with Ruff, type-check it with ty, and check docstring coverage with interrogate |
| `just lint-workflows` | Audit the GitHub Actions workflows, the hook config and the Dependabot config with zizmor                      |
| `just test`           | Run the tests, then the docstring examples, in random order, and stop at the first failure                     |

## Tests

- `just test` runs the tests in parallel, one worker per CPU, then the examples
  in the docstrings under `src/`. It stops at the first failure. To run
  everything and collect every failure instead, use `KEEP_GOING=1 just test`.
  The failures and errors are also written to `.cache/test-errors`.
- Tests run in a random order. pytest prints the seed at the top
  (`Using --randomly-seed=...`). `uv run pytest --randomly-seed=<seed>` runs the
  tests again in that shuffled order, in one process. It doesn't repeat which
  test each parallel worker ran when, and it leaves out the docstring examples,
  which `just test` runs in a second session with its own seed.
- No test calls a real model provider or spends money. Every test runs with
  dummy API keys and with the providers' addresses pointed at a closed local
  port. Tests that need a provider use the stand-in server in
  `tests/fixtures/mock_providers.py`.
- The tests import the installed package, not `src/`, so they test what users
  get.

CI runs the tests on Python 3.13 and 3.14. It also builds the wheel and, on
Linux, macOS and Windows, installs it in a fresh environment and runs the
survey, page extraction and page-break verification against the stand-in server
(`scripts/smoke_installed_wheel.py`).

## Dependencies

`uv add` and `uv remove` update `pyproject.toml` and `uv.lock` and sync `.venv`
in one step, and keep the lists in alphabetical order.

| Task                                    | Command                                                    |
| --------------------------------------- | ---------------------------------------------------------- |
| Add a dev tool (test, lint, type check) | `uv add --dev "<package>==<version>"`                      |
| Add a runtime dependency                | `uv add <package>`                                         |
| Upgrade a dev tool                      | `uv add --dev "<package>==<new version>"`                  |
| Upgrade a runtime dependency            | `uv lock --upgrade-package <package>`, then `just install` |
| Remove a dependency                     | `uv remove <package>` (with `--dev` for a dev tool)        |
| After editing `pyproject.toml` by hand  | `uv lock`, then `just install`                             |
| Rebuild `.venv` from scratch            | `just clean`, then `just install`                          |

- Dev tools are pinned to an exact version (`==`), so everyone and CI run the
  same one. Runtime dependencies get a minimum version (`uv add` writes `>=`),
  so pydelity installs alongside other packages.
- Afterwards, run `just lint` and `just test`, and commit `pyproject.toml` and
  `uv.lock` together. CI fails if the lock does not match `pyproject.toml`.
- After pulling someone else's dependency change, run `just install`.
- Each month, Dependabot opens up to four pull requests that move the pins to
  newer releases, one for each kind of pin: the GitHub Actions in the workflows,
  the docs site's npm packages, the git hooks' versions and the Python packages
  in `uv.lock`.

## Git hooks

With the git hook installed, prek runs the checks when you commit. Most hooks
check only the files in the commit. A few check the whole tree whenever the
commit touches a file they cover: Prettier and markdownlint check every Markdown
file, ty and interrogate check all of `scripts/`, `src/` and `tests/`, and
zizmor checks the workflows and the hook and Dependabot configs. The check that
`.template.env` and `.env` match runs on every commit. To run every hook on
every file, use `uv run prek run --all-files`.

## Commit messages

Commit messages on `main` follow
[Conventional Commits](https://www.conventionalcommits.org/), because
release-please works out each release from them. When a pull request is
squash-merged, its title becomes the commit message. See
[Releases](../releases/).

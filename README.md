# pydelity

[![Docstring coverage](https://raw.githubusercontent.com/IDinsight/pydelity/main/interrogate_badge.svg)](https://interrogate.readthedocs.io/)

Under development and not yet usable.

`pydelity` will turn PDFs into faithful, structured JSON. This release only
reserves the name on PyPI and contains no working code. The first usable release
will be 0.1.0 or later.

Source code: <https://github.com/IDinsight/pydelity>

## Development

### Prerequisites

- [git](https://git-scm.com/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.8.1 or later
- [just](https://just.systems/man/en/packages.html) 1.35.0 or later, for example
  with `uv tool install rust-just` or `brew install just`

Everything else, including [prek](https://prek.j178.dev/) (which runs the git
hooks), Ruff, ty, interrogate, pytest and zizmor, is pinned in `pyproject.toml`
and installed into `.venv` by `just install`. You don't need to install any of
them yourself; run one directly with `uv run`, for example
`uv run prek run --all-files`.

If you'd rather have `prek` on your `PATH` too, install it with
`uv tool install prek` or `brew install prek` (see
[prek's installation guide](https://prek.j178.dev/installation/)). Without just
installed, `uv run --locked just <recipe>` runs the pinned just instead.

### Commands

| Command               | What it does                                                                                                   |
| --------------------- | -------------------------------------------------------------------------------------------------------------- |
| `just`                | List every recipe                                                                                              |
| `just clean`          | Remove `.venv`, caches and build output (run `just install` afterwards)                                        |
| `just install`        | Create `.venv` from `uv.lock` (fails if the lock is out of date) and install the prek git hook                 |
| `just lint`           | Run every lint recipe below                                                                                    |
| `just lint-markdown`  | Format every Markdown file with Prettier, then lint it with markdownlint                                       |
| `just lint-python`    | Fix and format the Python code with Ruff, type-check it with ty, and check docstring coverage with interrogate |
| `just lint-workflows` | Audit the GitHub Actions workflows, the hook config and the Dependabot config with zizmor                      |
| `just test`           | Run the tests                                                                                                  |

With the git hook installed, prek runs the checks on the files in each commit.
To run every hook on every file, use `uv run prek run --all-files`.

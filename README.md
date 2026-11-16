# pydelity

Under development and not yet usable.

`pydelity` will turn PDFs into faithful, structured JSON. This release only
reserves the name on PyPI and contains no working code. The first usable release
will be 0.1.0 or later.

Source code: <https://github.com/IDinsight/pydelity>

## Development

You need [git](https://git-scm.com/), [uv](https://docs.astral.sh/uv/) 0.8.1 or
later, and [just](https://just.systems/) 1.35.0 or later. One way to get just is
`uv tool install rust-just`.

```sh
just install  # create .venv from uv.lock and install the git hooks
just test     # run the tests
just lint     # run the linters and formatters
just          # list every recipe
```

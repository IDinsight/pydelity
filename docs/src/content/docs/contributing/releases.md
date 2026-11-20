---
title: Releases
description:
  How a change on main becomes a release on PyPI and the docs site, and the
  one-time settings publishing needs.
---

pydelity's releases are driven by commit messages. Nobody edits the version or
the changelog by hand.

## How a release happens

1. Changes reach `main` with
   [Conventional Commits](https://www.conventionalcommits.org/) messages. When a
   pull request is squash-merged, its title becomes the message, so the title
   must follow the format.
2. After each push to `main`,
   [release-please](https://github.com/googleapis/release-please) opens or
   updates a release pull request with the next version and its `CHANGELOG.md`
   entry.
3. Merging the release pull request sets the version in `pyproject.toml` and
   `uv.lock`, tags the commit `vX.Y.Z` and creates a GitHub release.
4. The GitHub release starts the `Release` workflow
   (`.github/workflows/release.yml`). It checks that the tag matches the package
   version, builds the wheel and sdist with `just build` and publishes them to
   PyPI.
5. The new tag starts the `Docs` workflow, which publishes the docs site with
   the new version. See [The docs site](../docs-site/#versions-and-publishing).

The commit type decides the version:

| Commit message                                                               | Release                      |
| ---------------------------------------------------------------------------- | ---------------------------- |
| `fix: ...`, `perf: ...`, `revert: ...`, `docs: ...` or `deps: ...`           | Patch, such as 0.1.0 → 0.1.1 |
| `feat: ...`                                                                  | Minor, such as 0.1.1 → 0.2.0 |
| `feat!: ...`, or a `BREAKING CHANGE:` footer                                 | Major                        |
| Other types, such as `chore:`, `test:`, `ci:`, `build(deps):` or `ci(deps):` | None                         |

These follow the changelog sections of release-please's Python release type,
which this repo doesn't change: types with a section of their own in the
changelog make a release, and the rest don't. So a pull request titled
`docs: ...` opens a release pull request for a patch version too. Nothing is
published until that release pull request is merged. While the version is below
1.0.0, a breaking change still makes the next version 1.0.0. Check the version
in the release pull request before merging it.

## Make a release

1. Wait for CI to pass on the release pull request, and read its `CHANGELOG.md`
   entry.
2. Merge it.
3. Watch the `Release` workflow in the repository's Actions tab. The
   `Publish to PyPI` job waits for approval if the `pypi` environment requires
   it.
4. Check that the new version is on [PyPI](https://pypi.org/project/pydelity/)
   and that `uv tool install --python 3.13 pydelity` installs it.
5. Check that the docs site shows the new version.

If the `Release` workflow fails before publishing, fix the cause and re-run the
workflow from the Actions tab. PyPI never accepts the same version twice, so a
version that was published can't be replaced, only followed by a new release.

## Where the version comes from

`.release-please-manifest.json` holds the latest released version, and
release-please works out the next one from it and the commits since its tag. The
first release, 0.1.0, followed the 0.0.1 placeholder that reserved the name on
PyPI. That placeholder is now yanked.

## One-time settings

Publishing needs these settings outside the repository. Set them up before the
first release.

### PyPI Trusted Publishing

The `Release` workflow publishes with
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/), so no PyPI
token is stored anywhere. On PyPI, an owner of the `pydelity` project adds a
trusted publisher under the project's **Publishing** settings:

| Field            | Value         |
| ---------------- | ------------- |
| Owner            | `IDinsight`   |
| Repository name  | `pydelity`    |
| Workflow name    | `release.yml` |
| Environment name | `pypi`        |

### The `pypi` environment on GitHub

In the repository's **Settings → Environments**, create an environment named
`pypi`. Under its deployment branches and tags, allow tags matching `v*`, since
the workflow runs on the release tag. You can also require a reviewer, so that
each upload to PyPI waits for someone's approval.

### GitHub Pages

In the repository's **Settings → Pages**, set the source to **GitHub Actions**.
Then, in **Settings → Environments → github-pages**, allow deployments from the
`main` branch and from tags matching `v*`, because the `Docs` workflow publishes
from both.

### The release-please token

release-please uses a fine-grained personal access token, stored as the
`RELEASE_PLEASE_TOKEN_PYDELITY` secret of the `release-please` environment. It
needs read and write access to this repository's contents, issues and pull
requests. A release pull request made with the workflow's own token would start
no CI, which is why a personal token is used. If the token expires or is
revoked, release-please fails until the secret holds a new one.

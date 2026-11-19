---
title: The docs site
description:
  Preview, build and check the docs site, regenerate its reference pages and
  learn how the versioned site is published.
---

The docs site is built with [Astro](https://astro.build/) and
[Starlight](https://starlight.astro.build/) and lives in `docs/`. Its pages are
Markdown files in `docs/src/content/docs/`. The sidebar is set in
`docs/astro.config.mjs`.

## Prerequisites

Besides the tools in [Local development](../development/), the site needs:

- [Node.js](https://nodejs.org/) 22.12 or later
- [pnpm](https://pnpm.io/installation) 10.34.5, the version `docs/package.json`
  names. `corepack enable` sets it up from that file, or install it with
  `npm install -g pnpm@10.34.5`.

The site's own packages are pinned in `docs/pnpm-lock.yaml`. The recipes below
install them from the lock file.

## Preview the site

```sh
just docs
```

This serves the site with live reload. Open the address it prints, which ends in
`/pydelity/`. Changes to pages show up as you save them.

## Build and check it

```sh
just docs-build
```

This builds the site from the current tree into `docs/dist/` and then checks
every internal link and `#fragment` in it. A broken link fails the build. CI
runs the same build and check on every pull request.

## Reference pages

The pages in `docs/src/content/docs/reference/` are generated from pydelity's
code by `scripts/generate_reference_docs.py`: the settings from the Pydantic
models, the command from Typer, the Python API from the docstrings, and each
output file from its schema. Don't edit them by hand. Change the code or its
docstrings, then run:

```sh
just docs-reference
```

`just lint` runs this too, before formatting Markdown. CI regenerates the pages
and fails if they differ from what is committed, so a reference page can't fall
behind the code.

## Write a page

- Write pages in Markdown (`.md`), with a `title` and `description` in the front
  matter. `just lint-markdown` formats them with Prettier and checks them with
  markdownlint, and the git hook does the same on commit.
- Link to other pages with relative links, such as `../../reference/cli/`. The
  site is served at `/pydelity/` and each release at `/pydelity/v/<version>/`,
  and relative links work in both.
- Add a new page to the sidebar in `docs/astro.config.mjs`, except under
  `reference/`, whose pages are listed automatically.
- Link to reference pages for exact names and fields rather than copying them,
  so there is one place to keep up to date.

## Versions and publishing

The published site has one version per release, from v0.1.0 on. The latest
release is at `https://idinsight.github.io/pydelity/`, and every release is also
at `/pydelity/v/<version>/`, with a version selector on each page.

To build all versions locally, fetch the tags and run the versioned build:

```sh
git fetch --tags
cd docs
pnpm install --frozen-lockfile
pnpm run build:versions
pnpm run check-links
```

Each version's pages come from its release tag (`v<version>`). The version
selector, styles and components come from the current checkout, so they are the
same on every version. The build fails when there is no release tag of v0.1.0 or
later.

The `Docs` workflow (`.github/workflows/docs.yml`) publishes the site to GitHub
Pages:

- Pull requests build the current tree and check its links. Nothing is
  published.
- Pushes to `main`, release tags and manual runs build every released version.
  The site is published only when the package version on `main` has its release
  tag.

Because pages come from release tags, a docs change merged into `main` reaches
the published site with the next release.

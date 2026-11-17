<!-- STANDARDS
Artifact: DOCUMENTATION
Cycle: build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de
-->

# Documentation Record

`Cycle`: `build-pydelity-generic-pdf-to-structured-20261116T164214Z-313393de`
`Status`: `COMPLETE` `Collaboration`: `AUTONOMOUS` `Target`: `ACTIVE_CHANGE`
`Target Detail`: `active cycle` `User Style`: `tony`

## Assessed Inputs and Boundary

- Workflow: `STANDARD`, `FULL_DELIVERABLE`, `BROWNFIELD`, entered by `FORWARD`
  from `REVIEWING_IMPLEMENTATION`; no recovery, no outstanding obligations,
  `BlockedOn: NONE`.
- Contract and owner evidence (git blob ids): scope
  `.standards/docs/scope/<cycle>.md` `5439835`; design
  `.standards/docs/specs/<cycle>.md` `6481c12`; development plan `5a1c29e`
  (`COMPLETE`); verification report `523697e` (`COMPLETE`, `FULL`);
  implementation review `adf4cba` (`COMPLETE`, no material findings);
  `.standards/CONTEXT.md` `7e05b3a`.
- Behavior sources read in full: `justfile` `395cb0e`, `pyproject.toml`
  `00dbb75`, `.pre-commit-config.yaml` `e610a09`, `.github/dependabot.yml`
  `347a698`, `.github/workflows/ci.yml` `85e4a97`; `scripts/format_markdown.mjs`
  `5174883` for the Markdown recipe.
- Comparison: `HEAD` `662ffae` (tree `1318818`) on `tz6/port-over`, clean at the
  start. The deliverable is `README.md`: `fed8661` at `HEAD`, `10f0cdf` after
  this role's edit (unstaged). Nothing else in the working tree changed apart
  from this record.
- Editing boundary, from the user on 2026-11-16: the repo needs no formal
  documentation yet, and the root `README.md` is the only document that may need
  updating; if it is fine, leave it. Other surfaces are inventoried below as
  no-change, not edited.
- Styles: `.claude/skills/documenter/styles/universal.md` `19cc923`; user style
  `.standards/user-styles/documenter/tony.md` `e5393eb` (selected by the user in
  the invocation). No technology style applies: the README documents commands
  and tools, not a Python API. `references/readme.md` `bb2e877` read for the
  documentation-impact inventory.
- Project references loaded: `NONE` (no `.standards/project-references/`).

## Documentation Work and Evidence

### Root `README.md`: PyPI page and contributor guide

Audiences: PyPI visitors (the README is the project's long description) and
engineers working on the repo. Sections: title, badge and status; Development
(Prerequisites, Commands, Dependencies, Tests, Git hooks).

Each claim was checked against the files above and owner evidence:

- Status text and "first usable release 0.1.0 or later" match design decision 6
  and the published metadata (`AC-040`; review R5). This role did not change
  them; PyPI keeps showing the 0.0.1 README until the next release.
- Prerequisites: uv 0.8.1 matches `required-version = ">=0.8.1"`, tried by
  Developer and by Reviewer R4; just 1.35.0 matches Developer's oldest-just run
  (plan, `DEV-012` evidence). Install commands for just and prek were checked
  against their docs in `DEV-016`.
- Commands table: the recipes equal `just --summary` (C2) and each description
  matches its recipe in `justfile` (`AC-042`, `AC-045` for `lint-workflows`,
  `AC-041` for `lint-markdown`).
- Dependencies: commands and pin rules match the uv behavior Developer tried in
  `DEV-019`; the monthly Dependabot line matches `.github/dependabot.yml`, which
  sends each ecosystem's updates as one monthly pull request (`AC-044`).
- Tests and Git hooks: `KEEP_GOING`, `.cache/test-errors`, random order and the
  seed rerun match the `test` recipe and the pytest config; `just install` runs
  `prek install`.
- No `make` or `pre-commit` command anywhere in the README (C3, `AC-043`).

One inaccuracy found and fixed (saved, `10f0cdf`): the paragraph after the
prerequisites said that everything else is pinned in `pyproject.toml` and
installed by `just install`. Prettier, markdownlint and their Node.js are pinned
in `.pre-commit-config.yaml` (`prettier@3.10.1`, markdownlint-cli2 `v0.24.1`,
Node `24.22.3`), and `pyproject.toml` names none of them (C3). The paragraph now
says where each group is pinned and that prek sets up the Node tools when a hook
or `just lint-markdown` first needs them (C4 shows this from an empty prek
cache). The rest of the README is unchanged.

### Other documentation surfaces: no change

- Formal documentation (guides, API docs, docs site): none needed this cycle, by
  the user's direction above. There is no public API yet (empty package, no
  console script).
- Project agent guidance: `AGENTS.md` and `CLAUDE.md` hold only the STANDARDS
  installer text; no project guidance exists to update, and the user limited
  this cycle's documentation to the README.
- `.github/` issue and pull request templates: Developer found they already fit
  pydelity (plan, `DEV-008`); they hold no tool commands.
- `AC-002` (user sign-off of the setup): no documentation impact.
- Retired `AC-039` (pipeline README) moved to the next cycle; not current.

## Checks and Applicability

All on 2026-11-16, repo root, macOS arm64 in the agent sandbox, uv 0.13.8, with
`UV_CACHE_DIR`, `UV_TOOL_DIR` and `PREK_HOME` in the session temp folder.

- **C1, links:** `curl -s -o /dev/null -L -w '%{http_code}'` on every README
  link. 200 for interrogate's docs, the GitHub repo, git-scm.com, uv's install
  page, just's packages page, prek's home and install pages. 404 for the badge
  image on `raw.githubusercontent.com/.../main/interrogate_badge.svg`, expected:
  `main` does not have the file until this branch merges (see L1).
- **C2, recipes:** `uv run --locked just --summary` →
  `clean default install lint lint-markdown lint-python lint-workflows test`,
  exit 0. Matches the Commands table (`default` is the bare `just` row).
- **C3, inspection:** `grep` on `README.md` for `make` and `pre-commit`
  commands: none. `grep` on `pyproject.toml` for prettier, markdownlint and
  node: none; `.pre-commit-config.yaml` lines 45, 46 and 55 hold the Node and
  prettier pins.
- **C4, Markdown recipe from an empty prek cache:**
  `uv run --locked just lint-markdown` with a new, empty `PREK_HOME`. prek set
  up Node and prettier (its `tools`, `hooks` and `repos` folders appeared),
  prettier left `README.md` unchanged and reformatted only the then-unfilled
  record stub; the run then failed on the STANDARDS check's five unfilled-field
  problems in that stub, which this record's content replaces. Rerun as C5.
- **C5, final checks** after this record was saved: see **Resume and
  Conclusion**.

## Discrepancies, Dependencies, and Remaining Work

`NONE` open. Non-blocking limits:

- **L1, badge image 404 until merge.** The README's interrogate badge points at
  `main`, which does not have `interrogate_badge.svg` yet (Developer recorded
  this in `DEV-008`). It resolves when this branch merges; the URL is right for
  that.
- **L2, Windows.** The README does not say that the recipes need bash. The scope
  makes Windows support next-cycle work, and the design's follow-up notes that
  it will need recipes that do not assume a POSIX shell; the README should be
  updated then.
- **L3, published PyPI page.** The README fix reaches PyPI only with the next
  release; the 0.0.1 page keeps the README it was published with, which
  satisfies `AC-040` as it is.

## Resume and Conclusion

- Final checks (C5), after saving this record:
  `uv run --locked just lint-markdown` exit 0 (STANDARDS check passed,
  markdownlint passed); `uv run --locked prek run --all-files` exit 0;
  `node .standards/bin/check.mjs` passed. `README.md` still `10f0cdf`.
- Blocking question: `NONE`. No guided step pending.
- The full Documenter gate passes: the README is checked and corrected, every
  other surface has a no-change disposition, and every current AC (`AC-040` to
  `AC-045`, `AC-002`) is accounted for above. Next: final review
  (`REVIEWING_FINAL`, `FINAL_DELIVERABLE`). This is not cycle completion or
  sign-off.

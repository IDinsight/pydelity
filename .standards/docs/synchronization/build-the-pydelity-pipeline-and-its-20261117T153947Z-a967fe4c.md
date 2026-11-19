<!-- STANDARDS
Artifact: SYNCHRONIZATION
Cycle: build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c
-->

# Synchronization Record

`Cycle`: `build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c`
`Status`: `COMPLETE` `User Style`: `NONE`

## Assessed Inputs

- Workflow (`.standards/STATE.md`): `STANDARD`, `FULL_DELIVERABLE`,
  `SYNCHRONIZING`, entered by `RESUME` from `REVIEWING_FINAL` when recovery
  frame 1 closed. Frame 1 was the user's rework of the final review's withdrawn
  findings (pushed from `SYNCHRONIZING`, owner `DEVELOPING`,
  `RerunThrough: REVIEWING_FINAL`). Recovery inactive, outstanding obligations
  inactive, `BlockedOn`, `BaselineReconciliation`, `PromotionReason` and
  `PendingVerificationCadence` all `NONE`. No synchronization record existed
  before this pass, so this is the first.
- Owner records, SHA-256 prefixes at HEAD `7cd93f6` (provenance cycle and kind
  match the path for each):
  - scope `1c127ab4fa9a2c5e`; design `7e579b1ed3535e6e`; context
    `.standards/CONTEXT.md` `aa4a553cf773451e`;
  - development plan `06983d3c3a3e01c2` (`COMPLETE`, `AFTER_IMPLEMENTATION`,
    `Current Increment: NONE`);
  - verification report `e8e654e6b3ccffcb` (`REVERIFY`, `COMPLETE`, `FULL`);
  - implementation review `3fd035240dc9ad4e` (`IMPLEMENTATION`, `COMPLETE`);
  - documentation record `1a9e821f300fbca7` (`COMPLETE`);
  - final-deliverable review `3705bddb34756f8c` (`FINAL_DELIVERABLE`,
    `COMPLETE`, its three findings `RESOLVED`).

  The first seven match the identities the final review's rerun recorded. The
  final review changed only by its own rerun commit `7cd93f6`.

- Current acceptance set (43): `AC-001`, `AC-002`, `AC-004` to `AC-011`,
  `AC-014`, `AC-015`, `AC-017` to `AC-047`. Retired, history only: `AC-003`,
  `AC-012`, `AC-013`, `AC-016`. Same set in the verification report and both
  reviews.
- Comparison range: `main` (`bdd8488`, the merge base) to `tz6/pipeline` at
  `7cd93f6`, which `origin/tz6/pipeline` also points to. Clean tree: nothing
  staged, unstaged or untracked. The branch also installs STANDARDS
  (`.standards/`, `.claude/`, `.agents/`, `.codex/`, `AGENTS.md`, `CLAUDE.md`),
  which is workflow tooling, not part of the deliverable; `main` has no
  STANDARDS installation.
- Deliverable identities at `7cd93f6`: trees `src` `f37825c`, `tests` `268e597`,
  `examples` `235e934`, `scripts` `19567bb`, `.github` `4cc0d13`, `docs`
  `680ad84`, `docs/src/content/docs/reference` `70524e5`; blobs `pyproject.toml`
  `3cb2e48`, `uv.lock` `8b205c6`, `justfile` `ff59f1c`, `.template.env`
  `56e4725`, `docs/package.json` `398fe9f`, `docs/pnpm-lock.yaml` `d383b7c`,
  `README.md` `6d56470`, `docs/astro.config.mjs` `73e9712`,
  `docs/src/components/PageTitle.astro` `9d04eb4`, `src/pydelity/errors.py`
  `4a52ef2`, `release-please-config.json` `e2af4b1`,
  `.release-please-manifest.json` `b985ff6`. The 15 prose pages match the blob
  identities in the documentation record and the final review (`python.md`
  `9c8365b` and `docs-site.md` `1a72c55` after the rerun).
- Changes since each assessment:
  - Since the final review's rerun (`f2df723`): nothing outside `.standards/`.
  - Since the implementation review's last head (`2c8720c`) in `src`, `tests`,
    `scripts`, `examples`, `.github`, `pyproject.toml`, `uv.lock`, `justfile`
    and the docs package files: only the `PdfError` docstring
    (`src/pydelity/errors.py`, `ac5e43f`) and `docs/package.json`'s
    `engines.node`, `>=22.12.0` to `>=22.23.4` (`8ba5dae`). The reference page
    regenerated from the docstring changed one line. The rest is documentation
    (`ae81cb5`, `f2df723`) and workflow records.
- Environment: macOS arm64 (Darwin 25.6.0), repo `.venv`, Node 23.10.0.
- Project references loaded: `NONE` (`.standards/project-references/` does not
  exist). User style: none selected.
- Boundary: every current AC and the design's technical acceptance criteria, the
  seven owner records, the deliverable above, and the state chain of frame 1.
  This record's own writes and the `STATE.md` transition after it are not
  deliverable inputs.

## Completion and Evidence References

Each line names the evidence that accounts for the ACs and why it still applies
to the content above. The owner records hold the detail.

- Survey: `AC-001`, `AC-002`, `AC-004`, `AC-005`, `AC-006`, `AC-040`, `AC-045`,
  `AC-046`. CLI, config and Python API: `AC-007`, `AC-008`, `AC-009`, `AC-010`,
  `AC-042`, `AC-043`, `AC-044`, `AC-047`. Providers: `AC-011`, `AC-037`,
  `AC-041`. Spend: `AC-014`, `AC-015`, `AC-038`, `AC-039`. Reuse and review:
  `AC-017`, `AC-018`, `AC-019`, `AC-020`. Tests and builds: `AC-021`, `AC-022`,
  `AC-023`, `AC-024`. With the design's **Technical Acceptance Criteria** for
  them, these rest on the verification report's **Acceptance Evidence** and
  **Technical criteria notes** (all `VERIFIED`), the implementation review's
  **Contract and Evidence Assessment** (all supported, with
  `.standards/docs/reviews/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c/implementation.md#F-002`
  resolved), and the final review's **Contract and Evidence Assessment**
  (supported, with the guides checked against the code). Still applicable: since
  the evidence was produced, `src` changed only by the probe fix that Tester
  reverified (`e372d91`, test `2c8720c`) and by the `PdfError` docstring, which
  changes no behavior. `tests` is unchanged since `2c8720c`. The final review
  reran the suite (105 passed) and the doctests (17 passed, 1 skipped) on
  `f2df723`, which holds the same deliverable as `7cd93f6`.
- `AC-022`, `AC-023`, `AC-024` (CI, Windows, wheel): the CI evidence (runs
  `44432796735` on `02b3ea1` and `44436367131` on `b0ca0be`) was reused by
  Tester after the probe fix with a stated reason, and both reviews agreed.
  `.github`, `pyproject.toml`, `uv.lock`, `justfile` and `scripts` are unchanged
  since `b0ca0be`, and the later changes are platform-independent Python,
  Markdown, a docs component and one `engines` field. See **Limitations**.
- `AC-025`, `AC-031`, `AC-033`, `AC-034`: pending on Documenter in the
  verification report (**Open Findings and Dependencies**) and the
  implementation review (**Questions, Limitations, and Later Dependencies**),
  resolved under the same IDs by the documentation record's **Acceptance
  Criteria Dispositions** and **Checks and Applicability**, and assessed as
  supported by the final review. The README and every prose page match the
  record's identities.
- `AC-026`, `AC-029`, `AC-036`: readiness evidence from Tester (release and docs
  workflows, zizmor, release-please source) and both reviews. Publishing and
  deployment follow sign-off by the scope's constraints. Workflows and
  release-please files unchanged since that evidence.
- `AC-027`, `AC-028`, `AC-030`: Tester's docs build, versioned build and pin
  checks, implementation review, and the final review's rerun docs build and
  link check (25 pages) on `f2df723`. The `engines.node` floor is a minimum, not
  a tool pin. Node stays pinned at 24.22.3 in `docs.yml` and the hooks, and
  `docs/pnpm-lock.yaml` is unchanged, so `AC-030`'s evidence still applies.
- `AC-032`: Tester's regeneration check. After the docstring change, Developer
  (DEV-001 evidence) and the final Reviewer (rerun) regenerated and formatted
  the reference pages with no diff, and `python-api.md` describes `PdfError` as
  the code raises it.
- `AC-035`: the user's acceptance of real runs (verification report,
  2026-11-18). The implementation review found that the probe fix leaves the
  committed fixtures' facts unchanged, and the docstring changes no behavior.
- Frame 1 corrections:
  `.standards/docs/reviews/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c/final-deliverable.md#F-001`
  (Developer, `ac5e43f`),
  `.standards/docs/reviews/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c/final-deliverable.md#F-002`
  and
  `.standards/docs/reviews/build-the-pydelity-pipeline-and-its-20261117T153947Z-a967fe4c/final-deliverable.md#F-003`
  (Documenter, `f2df723`, with Developer's `docs/package.json` in `8ba5dae`) are
  `RESOLVED` in the final review against the original failure cases. The frame's
  rerun skipped `TESTING` and `REVIEWING_IMPLEMENTATION` on the frame owner's
  recorded reason (development plan **Plan Notes**, "Recovery, 2026-11-19"), and
  the final review agreed that the Developer and Tester full gates still hold.
  Synchronizer agrees: the diff since `2c8720c` is the two lines shown above,
  neither assessment relied on the docstring's wording or the `engines` floor,
  and the checks that cover them passed on the new content. The implementation
  review and the verification report therefore still apply, although their
  recorded `src` identity (`cae826c`) predates the docstring.
- Reconciliation checks run for this record (2026-11-19, repo root):
  - `node .standards/bin/check.mjs` before any work: "STANDARDS check passed.",
    exit 0.
  - `git status --porcelain=v1 --untracked-files=all`: empty. Identities above
    from `shasum -a 256` and `git rev-parse HEAD:<path>`.
  - `git diff --stat f2df723 HEAD -- . ':(exclude).standards'`: empty.
  - `git diff 2c8720c HEAD` over the implementation inputs: the two one-line
    changes described above.
  - `grep` over `README.md`, `docs/src/content/docs`, `src` and
    `docs/package.json` for `22.12` and `is missing, empty`: no match. The
    Python guide's error table, the `PdfError` docstring and every `Raises`
    entry in `python-api.md` agree.
  - `gh run list` and `gh pr list` for `IDinsight/pydelity`, branch
    `tz6/pipeline` (read-only, outside the sandbox because it blocks TLS
    certificate checks): the last runs are CI `44436367131`, Docs `44436367042`
    and TruffleHog `44436367169` on `b0ca0be`, all `success`. Draft pull request
    IDinsight/pydelity#3 is closed at `b0ca0be`. No run exists for a later
    commit.
  - Not rerun here: tests, doctests, lint, the docs build and the link check.
    The final review ran them on `f2df723`, and the deliverable has not changed
    since.

## Discrepancies and Dispositions

`NONE`. Cycle IDs, provenance, artifact paths, completion labels, AC sets and
content identities agree across `STATE.md` and the seven owner records, and each
assessment still applies to the current content as shown above.

## Limitations and Remaining Work

- CI has not run since `b0ca0be`. The later commits change one probe module and
  its test (reverified locally by Tester), Markdown, the sidebar, one docs
  component, one docstring, one `engines` field and workflow records. Local
  tests, doctests, reference regeneration, markdownlint, docs build and link
  check passed on the current content. CI runs again on the pull request that
  merges this work after sign-off. This does not block readiness because no CI
  input changed and every reviewer accepted the reuse with reasons. The user may
  open a pull request before signing off if they want CI on the final head.
- By the scope's constraints, these happen only after sign-off and merge: the
  PyPI upload, the release-please 0.1.0 pull request, the GitHub Pages
  deployment and the one-time PyPI Trusted Publisher and Pages settings. The
  README's docs-site links and `pip install pydelity` reach 0.1.0 only after
  that release.
- Non-material observations remain for their owners or a later cycle: the
  implementation review's withdrawn findings and other observations (its
  **Findings** and **Questions, Limitations, and Later Dependencies**) and the
  final review's contributor-page and FAQ wording notes. They are not
  discrepancies in this cycle's contract.
- `.standards/CONTEXT.md` describes the baseline before this cycle (for example
  the placeholder README). That is expected, since planned work does not make
  context stale, and `.standards/` is removed before the merge.
- No blocking question. `Active Work.BlockedOn` stays `NONE`.

## Resume and Synchronization Conclusion

- The work can go to user sign-off. The full Synchronizer gate passes: every
  current AC and relevant technical criterion has current evidence from its
  owners, the implementation review, the verification report and the final
  review all apply to the content at `7cd93f6`, the earlier Documenter
  dependencies are resolved under the same IDs, and no discrepancy, blocker or
  obligation remains.
- Recovery is inactive with an empty stack, so no return is due. **Standard
  Cycle Completion** for `FULL_DELIVERABLE` holds, and the workflow moves to
  `AWAITING_USER_SIGNOFF`. Readiness is not acceptance. At sign-off, recheck
  that HEAD still holds the identities above; any change to the deliverable
  needs its owners' reassessment first.
- After sign-off, the scope requires uninstalling STANDARDS on this branch
  before it merges to `main` (which has no STANDARDS installation), with the
  squash-merged pull request titled as a non-breaking `feat:` commit.

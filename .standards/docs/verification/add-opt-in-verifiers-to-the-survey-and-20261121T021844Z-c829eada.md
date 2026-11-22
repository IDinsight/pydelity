<!-- STANDARDS
Artifact: VERIFICATION
Cycle: add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada
-->

# Verification Report

`Cycle`: `add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada`
`Mode`: `REVERIFY` `Status`: `BLOCKED` `User Style`: `tony`
`Assessment Purpose`: `FULL` `Assessment Target`: `NONE`

## Assessed Inputs

- Recovery frame 1 (owner `SCOPING`, `ResumeAt` `SYNCHRONIZING`, `RerunThrough`
  `REVIEWING_FINAL`): the user's rework that makes code's measurements hints.
  Tester runs as a downstream rerun with a full assessment, after Developer's
  `FORWARD` handoff with the plan `COMPLETE`.
- Scope
  `.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
  (`01598d8`, SHA-256 `2d921029f902dc4e…`), design
  `.standards/docs/specs/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
  (`5cb51ac`, `a69221d00c35dfd5…`; decisions 14 to 16, **Checks and hints**),
  development plan
  `.standards/docs/development/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
  (`de4efcd`, `215cd7c4e02faf4f…`; `COMPLETE`, `Current Increment` `NONE`,
  `DEV-001` to `DEV-015` `DONE`, **Plan revision 2: hints rerun**, **Full
  completion: hints rerun**), `.standards/CONTEXT.md` (`0573e11`,
  `09045f457b2df4c1…`, unchanged), user style
  `.standards/user-styles/tester/tony.md` (`797def3`, `e64ef290173c7c32…`,
  unchanged). Current acceptance set: `AC-001` to `AC-054` without `AC-019` and
  `AC-034`, which are retired.
- Mode: `REVERIFY`, purpose `FULL`. The scope, the design and the code changed
  since the last full pass (`1b311bc`): Documenter's `c0ed1e9` (docs, README and
  three docstrings) and DEV-012 to DEV-015 (`0bfbfde`, `4b552a6`, `716400f`,
  `de4efcd`). Every current AC is reconciled against `de4efcd`; earlier evidence
  is reused only where its inputs are unchanged or the suite reran it (E59).
- Source assessed: `de4efcd`, clean tree.
  `git diff 1b311bc de4efcd -- src scripts examples docs pyproject.toml` (35
  files, 1,279 insertions, 609 deletions, SHA-256 `bab69561220c2be5…`); the
  hints rerun alone is `git diff 6807b18 de4efcd -- src scripts` (15 files,
  SHA-256 `11e8a07375080e4a…`); the cycle's whole change is
  `git diff 126f52f de4efcd -- src scripts examples docs pyproject.toml` (59
  files, SHA-256 `9de0a5151e9832a2…`). `.github/`, `release-please-config.json`
  and `.release-please-manifest.json` are unchanged since `126f52f`.
- Tests assessed: the cycle's tests up to `1b311bc` (no test changed since),
  plus this assessment's uncommitted changes to
  `tests/pydelity/extracting/test_extraction.py`,
  `tests/pydelity/extracting/test_validators.py` and
  `tests/pydelity/surveying/test_survey.py` (`git diff HEAD -- tests`: identity
  in E50).
- CI: no pull request is open for `tz6/pipeline-step-2`. Pull request 12 is
  closed at `fc6df7d`, and no CI run exists for `de4efcd` (E58).
- Environment: macOS 26.6.2 arm64, Python 3.13.9 (`.venv`, strict editable
  install whose link tree points at `src/`), PyMuPDF 2.1, Pydantic 2.14.3,
  pytest 9.2.0 with pytest-randomly and pytest-xdist, ruff 0.17.5, ty 0.0.105,
  interrogate 1.7.0, Prettier 3.10.1 with Node 24.22.3 from `~/.cache/prek`.
  Python 3.14 is not installed locally.
- Session: a new Tester chat with no Developer conversation in it. The client
  cannot certify session freshness; this assessment is built from the persisted
  records and the repository.
- Project references loaded: `NONE` (`.standards/project-references/tester/`
  does not exist). Shipped reference loaded:
  `.claude/skills/tester/references/llm-api-testing.md` (the change calls
  provider APIs; the stand-in in `tests/fixtures/mock_providers.py` is the
  seam).

## Acceptance Evidence

Test names below are in `tests/pydelity/extracting/test_extraction.py` (page
tests), `tests/pydelity/extracting/test_validators.py` (validator tests) and
`tests/pydelity/surveying/test_survey.py` (survey tests) unless a path is given.
Short names: P1
`test_a_page_no_verifier_reviewed_keeps_its_extraction_and_lists_each_difference`;
P2
`test_an_answer_failing_a_check_is_sent_back_then_kept_with_its_failure_listed`
(rows `no_verifier`, `passed`); P3
`test_the_verifier_s_verdict_decides_the_kept_answer_and_its_issues` (page, rows
`passed`, `correction_kept`, `correction_rejected`); P4
`test_page_prompts_give_what_the_pdf_and_the_survey_say_as_hints`; REQ
`test_each_page_request_carries_one_upright_image_and_only_its_own_instructions`
(`anthropic`, `openai`); V1
`test_every_hint_difference_is_a_review_issue_and_never_a_check_failure`; S1
`test_answers_that_differ_from_the_facts_are_kept_and_listed_by_page`; S2
`test_an_answer_that_fails_a_check_is_sent_back_with_each_failure`; S3
`test_the_verifier_s_verdict_decides_the_kept_answer_and_its_issues` (survey,
rows `passed`, `correction_kept`, `correction_not_kept`); S4
`test_the_verifier_request_carries_the_survey_s_file_text_failures_and_differences`.

| AC / technical criterion                                                                                                                                                                                                                                             | Tests or checks                                                                                                                                                                                                                                                                           | Disposition and evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AC-043` / every request of both steps, verifiers included, presents the measured facts and the survey's findings as hints the model's reading overrides; no system, user or retry message asks the model to match a hint; hint messages follow **Checks and hints** | P4; REQ; S4; `test_request_sends_the_facts_as_hints_with_every_repeated_line`; the retry messages in P2, P3 `correction_rejected`, S2 and S3 `correction_kept`; V1 and the updated hint message tests                                                                                     | Verified: both page prompts give the direction as what the survey found, the repeated lines with the survey's finding and the fields with their stored values under headings that call them hints the image overrides, and the rule that the image decides; the page verifier's and the survey verifier's rules say a correction need not agree with the hints; the survey's own request calls the facts hints; every retry message names check failures only; no hint difference holds "fix", "must", "need", "set it" or "should" (E51–E55).                                                                                                          |
| `AC-044` / both steps' output validators raise `ModelRetry` only for a `run_checks` failure; an answer or correction whose only differences are hints is accepted on that attempt; no hint difference raises an error or sets a status                               | P1; P2; P3; S1; S2; S3; `test_a_page_answered_as_one_full_page_figure_passes_every_check_and_hint`; V1                                                                                                                                                                                    | Verified: a page answer with two text differences, and a survey answer with 8 differences from the facts, are accepted on the first request; a page correction differing from two hints is kept on the verifier's first answer; only a label or survey check failure sends an answer or correction back; `run_checks` holds the six checks only; the runs with hint differences complete (P2: `run.json` `completed`) (E51–E55).                                                                                                                                                                                                                        |
| `AC-045` / the extraction request holds the page text sections and the image only, its stored text limited to the repeated lines and the form fields' values; no retry message holds a text-layer line                                                               | REQ; P2; `test_text_hints_are_skipped_when_the_text_layer_cannot_be_compared`                                                                                                                                                                                                             | Verified: on both providers the extraction request has none of the page's three stored body lines and gives the running header only in the hints section; neither of P2's retry messages holds the header or any stored line; a retry for an answer that also leaves out a stored line quotes no stored line (E51–E55).                                                                                                                                                                                                                                                                                                                                 |
| `AC-046` / with `verify_extraction` on, the verifier's user message lists each hint difference of the reviewed answer under the hints heading, a `text_dropped` line quoting its line, and `none` when there is none                                                 | P3 (all rows); P2 `passed`                                                                                                                                                                                                                                                                | Verified: with no check failure the checks section says `none` and the hints section holds one `text_dropped` line quoting "Ask the office for a form."; with a label failure the checks section names `labels` and the hints section `text_dropped` (E51–E55).                                                                                                                                                                                                                                                                                                                                                                                         |
| `AC-047` / a correction with no `run_checks` failure is kept whatever its hint differences; one with a check failure is not                                                                                                                                          | P3 `correction_kept`, `correction_rejected`                                                                                                                                                                                                                                               | Verified: a correction that adds a line and gives the running header as body text (an `artifacts` and a `text_added` difference) is kept on the verifier's first answer with `correction_failures` empty; under the earlier rule `artifacts` would have rejected it. A correction with a label not in the profile is sent back twice and not kept (E51–E55).                                                                                                                                                                                                                                                                                            |
| `AC-048` / a page's `issues` follow **Page extraction without a verifier** for no verifier, passed, correction kept, correction not kept; `hints` holds every hint difference on the kept answer whatever the outcome                                                | P1; V1; P2; P3                                                                                                                                                                                                                                                                            | Verified: with no verifier the page file's `hints` holds all five results in order and each difference is a review issue; each of the five hints, on one answer, becomes a review issue in order with its item's ID; with the verifier, hint differences are left off when the verdict passed or the correction was kept and listed before the `verifier` issue when it was rejected; a check failure is listed with or without the verifier (E51–E55).                                                                                                                                                                                                 |
| `AC-049` / a kept answer of the survey or a page still failing a check is written with each failure in `checks` and `issues`, and the step goes on; a run stops only on an unusable answer                                                                           | P2 (both rows); S4; `test_checks_still_failing_after_the_retries_are_listed_for_review`; `test_a_model_that_never_answers_in_the_format_fails_its_page`, `test_an_answer_that_never_parses_fails_the_survey`, `test_a_verifier_that_gives_no_usable_verdict_fails_the_survey`; inspection | Verified: a page's last answer still failing a label check is kept and listed, with or without the verifier, and `run.json` says `completed` (P2); the survey's, without a verifier, is listed and the command exits 0 (reused, rerun in E52); with the verifier on and a passed verdict, the survey's answer still failing `languages` is kept, its failure is the only review issue and the survey step completes (S4, under the user's raised limit) (E51–E55). The stop conditions (refusal, output tokens, no answer) are unchanged: the rework did not touch their handlers in either step's `llm.py` (inspection of `git diff 1b311bc de4efcd`). |
| `AC-050` / tests of item 10 with both providers mocked, each step with its verifier on and off                                                                                                                                                                       | P1–P4, REQ, V1, S1–S4 and the reused tests above                                                                                                                                                                                                                                          | Verified: for each step with its verifier off and on, a hint difference sends nothing back and is listed by `AC-011` and `AC-048`; a check failure sends the answer or correction back; a page verifier's correction differing from the hints is kept; a final answer still failing a check is kept and listed while the run completes; no retry message holds a hint. Every request goes to the stand-in; REQ runs both providers (E51–E55).                                                                                                                                                                                                           |
| `AC-054` / the page text lists each repeated line with its stored text and the survey's finding under a heading that calls them hints; no prompt text tells the model to put a repeated line in an item with role `artifact`                                         | P4; REQ                                                                                                                                                                                                                                                                                   | Verified: `page furniture`, `content` and `not decided` for the three uses; no sentence of either system message names a repeated line together with `artifact`; restoring the earlier sentence fails P4 (E51–E55).                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `AC-011` / `issues` follow **Survey verdict application** step 4 for each outcome; `hints` holds every `rotation_differs` and `page_number_differs` difference on the kept answer whatever the outcome                                                               | S1; S2; S3; S4                                                                                                                                                                                                                                                                            | Verified: with no verifier the 8 differences are in `hints` and the review list in that order; with the verifier, the 4 rotation differences stay in `hints` for every outcome and are listed only when the correction was not kept (E51–E55). A check still failing on the kept answer is listed with a passed verdict too (S4).                                                                                                                                                                                                                                                                                                                       |
| `AC-018` / with `verify_extraction` off, each page makes extractor requests only and keeps the extractor's answer                                                                                                                                                    | P1; P2 `no_verifier`                                                                                                                                                                                                                                                                      | Verified: one extractor request when only hints differ, three when a check fails, no verifier request, and the last answer kept (E51–E55).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `AC-020` / `PageFile.verification` is `null` exactly when no verifier ran; the report and the log line then say so                                                                                                                                                   | P1; `test_html.py::test_a_page_no_verifier_reviewed_says_so_in_the_report`; `test_turning_the_verifier_on_extracts_again_only_pages_it_has_not_reviewed`                                                                                                                                  | Verified, rerun on `de4efcd` (E52).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `AC-001` to `AC-010`, `AC-012` to `AC-017`, `AC-021` to `AC-025`, `AC-041`, `AC-042`                                                                                                                                                                                 | As listed for the earlier pass (**Superseded and reused evidence**)                                                                                                                                                                                                                       | Verified: the tests they rest on pass on `de4efcd` with the updated tests (E52); the code they assessed is unchanged by the hints rerun apart from the parts E51–E57 reassess. The changed test modules follow **Module order** (E56).                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `AC-026` / tests cover items 2–5 with both providers mocked                                                                                                                                                                                                          | The suite (211 tests)                                                                                                                                                                                                                                                                     | Verified on Python 3.13 locally (E52); the run on Python 3.14 waits for CI (`AC-027`).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `AC-027` / CI runs the tests on Python 3.13 and 3.14, and "Lint and test" and "TruffleHog secret scan" gate merges to `main`                                                                                                                                         | `.github/workflows/ci.yml` (unchanged); `main`'s ruleset (E45)                                                                                                                                                                                                                            | Blocked: the workflows and the ruleset are unchanged, but no CI run exists on the assessed content, and Python 3.14 is not installed locally (E58). Needs a CI run on the commit holding this assessment's tests.                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `AC-028` / on Linux, macOS and Windows the built wheel installs with pip and the command and API run both steps with mocked responses                                                                                                                                | `ci.yml` "Wheel install" running `scripts/smoke_installed_wheel.py`; in-process replay (E53)                                                                                                                                                                                              | Blocked: the replay of the script's API runs against the stand-in on `de4efcd` passes for both providers with the script's expected requests, but the wheel install on the three runners needs CI on the final content (E58).                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `AC-029` / the wheel installs into a clean environment and the wheel and sdist pass a metadata check                                                                                                                                                                 | CI's "Build the wheel and sdist and check their metadata" and the smoke script's install                                                                                                                                                                                                  | Blocked with `AC-028`: `pyproject.toml` is unchanged since E44, but the package source changed, and the build and fresh install rest on CI (E58).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `AC-030` / package description, classifiers and README                                                                                                                                                                                                               | `pyproject.toml` (unchanged since `b579737`); E44                                                                                                                                                                                                                                         | Package part verified (E44, unchanged input). README part pending a later role: Documenter, in this rerun.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `AC-031` / the release setup produces 0.2.0                                                                                                                                                                                                                          | Inspection (E45); `git log v0.1.1..HEAD`                                                                                                                                                                                                                                                  | Verified by inspection: the release files and workflows are unchanged since `126f52f`, and no commit since `v0.1.1` carries a breaking marker (E57). The 0.2.0 release pull request follows the merge to `main`.                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `AC-033` / the reference pages cover the new settings, CLI option and every new or changed field, and match the code                                                                                                                                                 | Regeneration in the scratchpad (E56)                                                                                                                                                                                                                                                      | Verified: the regenerated and formatted pages equal the committed ones; `page-json.md` and `pdf-survey-json.md` cover `hints` and `hints[]`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `AC-051` / the docs and docstrings say what page extraction sends                                                                                                                                                                                                    | Inspection of the `extracting/prompts.py`, `extracting/text_layer.py`, `extracting/validators.py`, `extracting/agents.py`, `surveying/validators.py` and `review.py` docstrings; a search of `src/`, `scripts/` and the reference pages (E57)                                             | Docstring part verified: they say the page requests carry the repeated lines with their stored text and the survey's findings and the form fields' values, as hints the image overrides, that the verifier's request quotes the stored lines a text difference is about, and that a hint difference never sends an answer back; no old wording remains. The guides and FAQ part is pending a later role: Documenter.                                                                                                                                                                                                                                    |
| `AC-052` / the docs say measurements are hints, which checks are hints, that a hint difference never retries or fails a run, when it is listed, and that a run stops only on an unusable answer                                                                      | The generated checks pages (E56, E57)                                                                                                                                                                                                                                                     | Generated part verified: `extraction-checks.md` and `survey-checks.md` list checks and hints under headings of their own and say a check may send an answer back within the check retries, a hint never does and never stops a run, when a hint difference is a review issue, and that the last answer is kept with each failing check listed. The guides part is pending a later role: Documenter.                                                                                                                                                                                                                                                     |
| `AC-032`, `AC-035`, `AC-036`, `AC-037`, `AC-038`, `AC-053`                                                                                                                                                                                                           | Documentation evidence                                                                                                                                                                                                                                                                    | Pending a later role: Documenter, with documentation-record evidence for each AC in this rerun.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `AC-039`, `AC-040`                                                                                                                                                                                                                                                   | The user's review of real runs                                                                                                                                                                                                                                                            | Pending a later role: the user's accepted real runs on Anthropic and OpenAI, after the build.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

### Superseded and reused evidence

- `AC-019` and `AC-034` are retired. Their earlier evidence (the text checks
  listed on pages no verifier reviewed; docstrings saying retry messages quote
  stored lines) no longer stands as current coverage.
- The earlier rows for `AC-001` to `AC-010`, `AC-012` to `AC-017`, `AC-021` to
  `AC-025`, `AC-041` and `AC-042` keep their tests and dispositions as recorded
  at `1b311bc` (E12–E42). Every one of those tests passes on `de4efcd` (E52).
- Superseded: the earlier page verdict rows (`passed`, `correction_kept`,
  `correction_rejected`) and P1, which expected retries for text differences and
  the "keep what the image shows" note; E47's CI run, which assessed `1b311bc`.

### Test module order departures

Each keeps an order that Python 3.13 needs to import the module.

- `tests/fixtures/mock_providers.py`: `_ROUTES` stays below the public type
  aliases `Provider` and `Route`, which its annotation
  `dict[str, tuple[Provider, Route]]` reads; `RecordedRequest` stays above
  `MockProviders`, whose `requests` property's return annotation names it.
- `tests/pydelity/config/test_loading.py`: `_EXAMPLES` stays below `_REPO_ROOT`,
  which its value reads.

A constant moves below the definition it reads, and a class or function moves
above the definition that reads it, as in the package's departures.

## Increment Assessments

| Increment | Outcome and acceptance scope                                                                                                                                                     | Assessed inputs / evidence                                                                          | Disposition |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ----------- |
| 1         | `src/pydelity/`, `scripts/` and `tests/` follow **Module order** with the listed departures (`AC-041`, `AC-042`)                                                                 | `0f4c949`; tests diff `60f9212d56eab4d4…` (committed in `ac9e4cb`); E1–E9 on 3.13, E10–E11 on 3.14  | VERIFIED    |
| 2         | Verifier settings and `--verify`/`-vf`; page extraction with or without its verifier (`AC-001` to `AC-006` and `AC-018` to `AC-020` for page extraction)                         | `384204a` (source `f710dcdbc349c854…`, tests `e3a5c176d5dd1e4b…`) and the fix in `45bfa10`; E12–E21 | VERIFIED    |
| 3         | Every request names its agent; the survey with or without its verifier (`AC-007` to `AC-017`, and the survey parts of `AC-001`, `AC-005`, `AC-006`), with Increment 2 reconciled | `e9914c0` (source `70c16aa7dcbb5ced…`), tests `6a3b39a693d8e4ca…`; E22–E31                          | VERIFIED    |
| 4         | `load()`, report tables, outline links, inline widgets and the `TEXT_FLAGS` comment (`AC-021` to `AC-025`), with earlier increments rerun                                        | `5bddc38` (source `51d64cee9f3fac0c…`), tests `24032d6d1c082a1e…`; E32–E38                          | VERIFIED    |

## Scenario Budget

| Source file                                                                                                                                                                                                                                                                         | Reused coverage                                                                                                                                                                                                                                      | Active-change allocations                                                                                                                                                                                                                                                                                                                                                                                                                                                      | User additions                                                                                                                          |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| The 16 reordered modules of `src/pydelity/` and `scripts/` (Increment 1)                                                                                                                                                                                                            | The existing suite as regression checks                                                                                                                                                                                                              | 0                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | NONE                                                                                                                                    |
| `src/pydelity/config/schemas.py`                                                                                                                                                                                                                                                    | Example-file completeness test (2 rows)                                                                                                                                                                                                              | 5 of 5 (Increment 2): the 4 rows of `test_each_step_s_verifier_follows_verify_unless_its_own_setting_is_set`; `test_verify_turns_on_both_steps_verifiers_from_a_file_or_a_keyword`. Increment 3 adds none.                                                                                                                                                                                                                                                                     | NONE                                                                                                                                    |
| `src/pydelity/cli.py`                                                                                                                                                                                                                                                               | `test_pages_and_no_pause_extract_only_those_pages_in_one_run`                                                                                                                                                                                        | 3 (Increment 2): `test_verify_adds_a_verifier_request_for_each_step_and_to_the_estimate` (2 rows; renamed from `..._for_each_page_...` and updated in Increment 3 because `--verify` now turns the survey's verifier on too, the same scenario); `test_a_pdf_alone_runs_the_survey_with_keys_from_the_environment` (expanded)                                                                                                                                                  | NONE                                                                                                                                    |
| `src/pydelity/pipeline/runner.py`                                                                                                                                                                                                                                                   | `test_a_rerun_with_unchanged_inputs_reuses_everything`; `test_run_json_records_each_step_its_pages_cost_and_review_issues` (now with `advanced.extraction.verify`); every test that reads pages back with `load()`                                   | 8 of 8: Increment 2's 4 (the 3 CLI scenarios, `test_the_check_before_spending_counts_the_verifier_only_when_it_runs`); Increment 3's `test_turning_the_survey_s_verifier_on...` (the estimate does not reuse an unreviewed survey) and `test_the_survey_estimate_prices_its_verifier_only_when_it_runs` (verifier on: the verifier's prompt size); Increment 4's `test_load_leaves_out_the_page_files_of_another_pdf` and `test_load_of_a_folder_without_facts_gives_no_pages` | Limit 6 for Increment 3's survey verifier, then 8 for Increment 4's `load()`, the user's choices on 2026-11-21 (`Raise both` each time) |
| `src/pydelity/costs/budget.py`                                                                                                                                                                                                                                                      | `test_the_check_before_spending...` and `test_async_estimate...` now include the survey's verifier with no new assertion                                                                                                                             | 8 of 8: Increment 2's 5; Increment 3's `test_the_survey_estimate_prices_its_verifier_only_when_it_runs` (verifier off, verifier on) and `test_verify_counts_the_survey_s_verifier_in_the_estimate_and_the_question`                                                                                                                                                                                                                                                            | Limit 8 for Increment 3's survey verifier, the user's choice on 2026-11-21 (`Raise both`)                                               |
| `src/pydelity/costs/schemas.py`                                                                                                                                                                                                                                                     | —                                                                                                                                                                                                                                                    | 4: Increment 2's 3; `test_a_ledger_whose_lines_name_no_agent_is_damaged_and_stops_the_run`                                                                                                                                                                                                                                                                                                                                                                                     | NONE                                                                                                                                    |
| `src/pydelity/providers/ledger_model.py`                                                                                                                                                                                                                                            | `test_ledger_model.py`                                                                                                                                                                                                                               | 2: `test_the_verifier_request_carries_the_survey_s_file_text_failures_and_differences` (each request's agent in the ledger); `test_the_survey_verifier_s_highest_cost_counts_the_pdf_and_stops_it_unsent`                                                                                                                                                                                                                                                                      | NONE                                                                                                                                    |
| `src/pydelity/surveying/survey.py`                                                                                                                                                                                                                                                  | `test_survey.py`'s 8 existing tests (one updated for `verification=None`); `test_a_rerun_with_unchanged_inputs_reuses_everything`                                                                                                                    | 5 of 5: the 3 rows of `test_the_verifier_s_verdict_decides_the_kept_answer_and_its_issues`; `test_turning_the_survey_s_verifier_on_surveys_again_only_what_no_verifier_reviewed`; `test_a_failed_verifier_request_stops_the_run_and_leaves_the_saved_survey`                                                                                                                                                                                                                   | NONE                                                                                                                                    |
| `src/pydelity/surveying/llm.py`                                                                                                                                                                                                                                                     | The survey request tests in `test_survey.py` and `test_uploads.py`                                                                                                                                                                                   | 5 of 5: `test_the_verifier_request_carries...`; the verdict test's `correction_kept` and `correction_not_kept` rows; `test_a_failed_verifier_request...`; `test_a_verifier_that_gives_no_usable_verdict_fails_the_survey`                                                                                                                                                                                                                                                      | NONE                                                                                                                                    |
| `src/pydelity/surveying/agents.py`                                                                                                                                                                                                                                                  | The survey agent's tests                                                                                                                                                                                                                             | 2: the verdict test's `correction_kept` (sent back, then kept) and `correction_not_kept` (accepted as given on the last attempt) rows                                                                                                                                                                                                                                                                                                                                          | NONE                                                                                                                                    |
| `src/pydelity/surveying/prompts.py`                                                                                                                                                                                                                                                 | `test_request_sends_the_facts_as_hints_with_every_repeated_line`; the doctest of `verify_survey`                                                                                                                                                     | 2: `test_the_verifier_request_carries...`; `test_prompt_schema_and_vocabulary_name_no_document_type` (expanded to the verifier's prompt)                                                                                                                                                                                                                                                                                                                                       | NONE                                                                                                                                    |
| `src/pydelity/surveying/schemas.py`                                                                                                                                                                                                                                                 | `test_prompt_schema_and_vocabulary_name_no_document_type` reads `PdfSurvey`'s schema, which now holds the verdict's fields                                                                                                                           | 5 of 5: the verdict test's 3 rows (the saved verification); `test_turning_the_survey_s_verifier_on...` (`null` with no verifier); `test_a_survey_saved_without_its_verification_is_damaged_and_made_again`                                                                                                                                                                                                                                                                     | NONE                                                                                                                                    |
| `src/pydelity/review.py`                                                                                                                                                                                                                                                            | Page extraction's `verifier` issue tests                                                                                                                                                                                                             | 1: the verdict test's `correction_not_kept` row (a survey `verifier` issue)                                                                                                                                                                                                                                                                                                                                                                                                    | NONE                                                                                                                                    |
| `src/pydelity/extracting/extraction.py`, `extracting/schemas.py`, `extracting/llm.py`                                                                                                                                                                                               | As recorded for Increment 2; the request test and the verdict test now turn the verifier on with `advanced.extraction.verify`, the same scenarios                                                                                                    | 3, 2 and 2 (Increment 2); unchanged in Increment 3                                                                                                                                                                                                                                                                                                                                                                                                                             | NONE                                                                                                                                    |
| `src/pydelity/report/html.py`                                                                                                                                                                                                                                                       | `test_report_draws_extracted_items_numbered_with_links_from_their_issues` (now with `advanced.extraction.verify`)                                                                                                                                    | 6 of 6: Increment 2's 1; Increment 3's verdict test rows (3) and `test_a_page_no_verifier_reviewed_says_so_in_the_report` (expanded); Increment 4's `test_a_header_cell_spanning_into_the_body_keeps_each_body_cell_in_its_column`                                                                                                                                                                                                                                             | Limit 6 for Increment 4's report tables, the user's choice on 2026-11-21 (`Raise both`)                                                 |
| `src/pydelity/surveying/probe.py`                                                                                                                                                                                                                                                   | The probe tests on the 10 committed PDFs; `test_outline_with_a_cycle_keeps_the_bookmarks_before_it`; `test_form_field_that_cannot_be_read_is_left_out_with_a_probe_error`                                                                            | 4: `test_outline_links_to_missing_objects_are_dropped_and_every_other_bookmark_kept` (2 rows; replaces `..._keep_the_bookmarks_pymupdf_reads` for the corrected rule, the same scenarios); `test_an_inline_form_field_is_left_out_with_a_probe_error_and_the_others_kept` (2 rows)                                                                                                                                                                                             | NONE                                                                                                                                    |
| `src/pydelity/api.py`, `src/pydelity/pipeline/schemas.py`, `src/pydelity/utils/pdf.py`, and `DEV-011`'s `extracting/__init__.py`, `extracting/prompts.py`, `extracting/schemas.py`, `extracting/text_layer.py`, `review.py`, `scripts/generate_reference_docs.py`, `pyproject.toml` | Docstrings, a comment, one sentence of the extraction instructions, the reference page generator and the description; the existing suite, regeneration and inspection (E37, E43, E44)                                                                | 0                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | NONE                                                                                                                                    |
| `scripts/smoke_installed_wheel.py`, `examples/config.json`, `examples/config.yaml`, `docs/`                                                                                                                                                                                         | Example-file completeness test; smoke replays and page regeneration in the scratchpad (E16, E17, E21, E29, E30)                                                                                                                                      | 0                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | NONE                                                                                                                                    |
| Hints rerun: `src/pydelity/extracting/validators.py`                                                                                                                                                                                                                                | The validator tests updated to the hint contract under new names: the full-page answer, artifacts (2), form fields, reading order (4 rows), the added and dropped text lines (8 rows) and the skipped text hints, which now checks the retry message | 2 of 5: V1; P2 `no_verifier` (the retry message holds check failures only)                                                                                                                                                                                                                                                                                                                                                                                                     | NONE                                                                                                                                    |
| Hints rerun: `src/pydelity/extracting/extraction.py`                                                                                                                                                                                                                                | P1 and P3 updated to the hint contract (P3's `correction_kept` now differs from a non-text hint, which replaces the text-check exception it held)                                                                                                    | 5 of 5: Increment 2's 3; P2 `no_verifier` and `passed`                                                                                                                                                                                                                                                                                                                                                                                                                         | NONE                                                                                                                                    |
| Hints rerun: `src/pydelity/extracting/agents.py`                                                                                                                                                                                                                                    | —                                                                                                                                                                                                                                                    | 1 of 5: P2 `no_verifier` (only a check failure sends the extraction back; the last answer is kept)                                                                                                                                                                                                                                                                                                                                                                             | NONE                                                                                                                                    |
| Hints rerun: `src/pydelity/extracting/prompts.py`                                                                                                                                                                                                                                   | REQ updated to the hint wording, the same scenario                                                                                                                                                                                                   | 2 of 5: P4; P3's verifier-request sections (`AC-046`)                                                                                                                                                                                                                                                                                                                                                                                                                          | NONE                                                                                                                                    |
| Hints rerun: `src/pydelity/extracting/llm.py`                                                                                                                                                                                                                                       | —                                                                                                                                                                                                                                                    | 3 of 5: Increment 2's 2; P3's verifier-request sections (`ask_verifier` passes the differences)                                                                                                                                                                                                                                                                                                                                                                                | NONE                                                                                                                                    |
| Hints rerun: `src/pydelity/extracting/schemas.py`                                                                                                                                                                                                                                   | P1 and P3 now read `hints` beside `checks`                                                                                                                                                                                                           | 2 (Increment 2); no new allocation                                                                                                                                                                                                                                                                                                                                                                                                                                             | NONE                                                                                                                                    |
| Hints rerun: `src/pydelity/surveying/validators.py`                                                                                                                                                                                                                                 | —                                                                                                                                                                                                                                                    | 1 of 5: S2, expanded so both answers differ from the facts and the retry holds no hint                                                                                                                                                                                                                                                                                                                                                                                         | NONE                                                                                                                                    |
| Hints rerun: `src/pydelity/surveying/prompts.py`                                                                                                                                                                                                                                    | S4's heading updated, the same scenario                                                                                                                                                                                                              | 3 of 5: the earlier 2; S4's verdict rules on hints                                                                                                                                                                                                                                                                                                                                                                                                                             | NONE                                                                                                                                    |
| Hints rerun: `src/pydelity/surveying/survey.py`                                                                                                                                                                                                                                     | S1 and S3 now read `hints` beside `issues`                                                                                                                                                                                                           | 6 of 6: the earlier 5; S4's kept answer still failing a check, listed with a passed verdict while the survey completes                                                                                                                                                                                                                                                                                                                                                         | Limit 6 for this one scenario, the user's choice on 2026-11-22 (`Raise to 6`)                                                           |
| Hints rerun: `review.py`, `extracting/text_layer.py`, `surveying/schemas.py`, `surveying/llm.py`, `pipeline/runner.py`, `pipeline/schemas.py`, `scripts/generate_reference_docs.py`                                                                                                 | Name splits, docstrings, a required field, call sites and the page generator; the suite, regeneration and inspection (E52, E56, E57)                                                                                                                 | 0                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | NONE                                                                                                                                    |

A test updated only to the new contract for its existing scenario, such as
turning page extraction's verifier on with `advanced.extraction.verify` instead
of the global switch, or queuing a survey verdict where the global switch now
runs the survey's verifier, uses that scenario's existing allocation. An update
that asserts new behavior counts as an allocation. A scenario is charged to the
files whose changed behavior it is built to check, not to every file it runs
through. The user raised the limit for `costs/budget.py` to 8 and for
`pipeline/runner.py` to 6, for the five survey-verifier scenarios named in those
rows only; for Increment 4 it raised `pipeline/runner.py` to 8 and
`report/html.py` to 6, for the three `load()` and table scenarios named there.
`config/schemas.py`, `costs/budget.py`, `pipeline/runner.py`,
`surveying/survey.py`, `surveying/llm.py`, `surveying/schemas.py` and
`report/html.py` have no allowance left; `surveying/probe.py` has 1. The
stand-in's survey verdicts and the `survey_verdict` fixture are test helpers.
The suite has 207 test IDs: Increment 2's 188 (with the `--verify` test's 2 rows
renamed), 12 new in Increment 3 and 7 in Increment 4.

In the hints rerun, a scenario updated only to the corrected contract keeps its
allocation, as before. P1's and S1's and S3's assertions on `hints` are counted
with their scenarios: the design's technical criteria for `AC-011` and `AC-048`
state where each hint difference goes, in `hints` and on the review list, as one
rule per verdict outcome. P3's `correction_kept` row replaces the earlier row's
correction, which differed only in text, with one that also differs from the
`artifacts` hint, so that the row tells the corrected keep rule from the earlier
one; its scenario, a correction differing from the hints kept, is the same. The
renamed validator tests are the same scenarios under the hint contract. The
suite has 211 test IDs: the earlier 207, with the renames, plus V1, P2's 2 rows
and P4. `extracting/extraction.py` and `surveying/survey.py` now have no
allowance left. The user raised `surveying/survey.py` to 6 for S4's added
scenario only.

## Execution Evidence

Working directory: repo root unless noted. Tools: `.venv/bin`. Scratch tools and
logs live in the Tester session's scratchpad (`tools/`, `logs/`), not in the
repo. E1–E47: 2026-11-21. E48 onward: 2026-11-22.

- **E1–E11 — Increment 1.** As recorded for Increment 1: the baseline on
  `126f52f` (E1); move-only comparison of the package, scripts and tests (E2,
  E3, E8); **Module order** and departures (E4, E5, E8); checks on `0f4c949` and
  after the tests reorder (E6, E9); reference pages (E7); CI run `44907613193`
  on pull request 11 with Python 3.14.4 and every other check passing (E10);
  static checks targeting 3.14 (E11). They stay valid for `AC-041` and `AC-042`.
- **E12–E21 — Increment 2.** As recorded for Increment 2: the checkpoint and its
  14 replaced-contract failures (E12); the test changes (E13); suite and linters
  (E14); 13 mutations caught (E15); the smoke script's expected requests (E16);
  reference pages (E17); module order (E18); inspection (E19); commits holding
  the assessed content (E20); the smoke script's correction (E21). Increment 3
  changed `survey.py`, `budget.py`, `runner.py`, `html.py`, `review.py` and
  `costs/schemas.py`, which E13–E15 assessed, so the Increment 2 tests are rerun
  in E23 and their changes are listed in E22; the conclusions for page
  extraction stand.
- **E22 — The checkpoint as handed over.** On `e9914c0` with Increment 2's
  tests: `pytest -q --numprocesses auto -p no:cacheprovider` 12 failed, 176
  passed (`logs/inc3_handover_pytest.log`); `ty check scripts src tests` 1
  diagnostic, the `build_survey` call in `test_survey.py`. The 12 are the tests
  the plan lists under `DEV-006`: 10 passed `verify=True` with no survey verdict
  for the stand-in, one counted two `no verifier ran` lines, one called
  `build_survey` without `verification`. Changes: the stand-in routes a request
  holding `The survey answer to review:` to a new `survey_verdicts` queue (HTTP
  400 when empty) and names every model request's agent (`surveyor` for the
  survey's own); a `survey_verdict` fixture in `tests/conftest.py`; the page
  tests that need page extraction's verifier only turn it on with
  `advanced.extraction.verify`; the budget reuse test and the CLI `--verify`
  rows queue a passed verdict, and the rows expect both verifiers; the report
  test counts three `no verifier ran` lines; `build_survey` gets
  `verification=None`; three expectations of `(None, None)` for the survey's
  request become `(None, "surveyor")`. New: 7 tests in `test_survey.py`, 2 in
  `test_runner.py`, 2 in `test_budget.py`, 1 in `test_cli.py`.
- **E23 — Suite and linters on the assessed content.**
  `pytest -q --numprocesses auto -p no:cacheprovider` exit 0, 200 passed;
  `pytest -q -p no:cacheprovider -p no:randomly` exit 0, 200 passed
  (`logs/inc3_pytest_parallel.log`, `logs/inc3_pytest_serial.log`); 200 test IDs
  (`logs/inc3_test_ids.txt`: Increment 2's 188 with the 2 renamed rows, plus
  12); `pytest --doctest-modules src` 28 passed, 1 skipped; `ruff check` "All
  checks passed!"; `ruff format --check` "89 files already formatted";
  `ty check scripts src tests` "All checks passed!"; `interrogate` 100.0%.
- **E24 — The tests check what they claim.** The new tests passed on their first
  run against `e9914c0`. One assertion was too weak: the failed-verifier test's
  first survey equaled the one the run would write, so it could not see a survey
  written before the verifier; its second answer now differs (E25, S14).
- **E25 — The tests catch the defects they target.** `tools/mutate3.py` copies
  `src/`, `tests/`, `examples/` and `pyproject.toml` to the scratchpad, applies
  one change to the copy's source, and runs the named tests there with
  `PYTHONPATH` set to the copy (`logs/inc3_mutations.log`, exit 0). All 36
  changes are caught, 44 test runs in all:
  - `survey.py`: the verifier never or always running; a failing correction
    kept; a correction never kept; differences always listed, or dropped with
    any verdict; problems listed when the correction was kept; the kept
    correction taking the survey's attempts; an unreviewed survey reused with
    the verifier on, in the run or only in the estimate; a reviewed survey
    always needed; `verifier passed` logged with no verifier; a problem's page
    dropped; a survey written before the verifier runs.
  - `llm.py`: the survey's text, the failures, the differences or the user's
    instructions left out of the verifier's request; the verifier recorded as
    `surveyor`; a correction's failures checked on the answer; the error naming
    the model; the verifier making its own upload.
  - `agents.py` (no send-back), `prompts.py` (no user instructions),
    `surveying/schemas.py` (`verification` optional), `ledger_model.py` (the
    verifier's bound without the PDF), `costs/schemas.py` (`agent` optional),
    `html.py` (no survey verifier row; a kept correction shown as listed),
    `runner.py` (the verifier's prompt size 0, or the survey's), `budget.py`
    (the survey's verifier never priced, its requests not doubled, its answer
    left out of the maximum or the expected cost, its `verifier` false).
  - The unmutated copy passes the 15 targeted tests.
- **E26 — Stand-in replays of the wheel smoke script.**
  `tools/smoke_check_name.py` (`python -I`) runs the script's API run in-process
  for both providers against the changed stand-in and passes its requests to the
  script's own `_check_requests`:
  `PASS API, <provider>: one upload and 3 model requests, all to the stand-in`
  for both, and the rerun with no request gives `FAIL` as before
  (`logs/inc3_smoke_check_name.log`, exit 0).
- **E27 — The survey's prompt is unchanged.** `tools/survey_prompts.py` measures
  the CAPS excerpt (8 repeated lines) and the scan (none) with each tree and
  prints `survey_pdf`'s messages for three inputs (with and without
  instructions, with and without languages). Run once with `50aca23`'s `src/`
  first on `sys.path` (confirmed by `prompts.__file__`) and once with
  `e9914c0`'s: the two outputs are byte for byte equal
  (`promptwork/base50.json`, `promptwork/pydelity.json`).
- **E28 — Module order of changed modules.** `tools/ordercheck.py order` on the
  11 source modules changed since `50aca23` and the 8 changed test files: only
  the departures listed under `DEV-001` and in this report, plus
  `SurveyVerification` above `PdfSurvey`, which `DEV-006` lists.
- **E29 — Reference pages.** `git archive HEAD` into the scratchpad,
  `python scripts/generate_reference_docs.py` there with `PYTHONPATH` set to the
  copy (11 pages), Prettier 3.10.1 with the repo's config, then `diff -r` with
  the repo's `docs/src/content/docs/reference/`: identical apart from the
  client's empty, untracked `.claude` folder. `pdf-survey-json.md` holds
  `verification` and its parts, `cost-jsonl.md` the required `agent` and
  `TYPICAL_SURVEY_VERDICT_OUTPUT_TOKENS`.
- **E30 — The verdict's shape.** `tools/verdict_shape.py` (`python -I`):
  `SurveyVerdict` accepts passed alone and failed with a problem, and rejects
  passed with a problem, passed with a correction, failed with no problem and an
  unknown category; its JSON schema has no `pattern`, bound, length or `format`
  keyword (`logs/inc3_verdict_shape.log`, exit 0). This is a scratch check, not
  a test in the suite.
- **E31 — Inspection.** `run_survey` asks the verifier only when
  `config.verify_survey` is set and builds the survey after it; `ask_verifier`
  sends `surveyed.attachment` through `_run_with_upload`, the replacement-upload
  path the survey's own request uses, which
  `test_uploads.py::test_a_file_the_provider_no_longer_has_is_uploaded_again_once`
  checks for the survey; `create_verifier_agent` uses `structured_output` and
  `retries={"output": check_retries}`; `SurveySettings`, which the fingerprint
  reads, has no verifier setting; `PROMPT_VERSION` stays 1. These match
  decisions 2, 5, 6 and 7.
- **E32 — The checkpoint as handed over.** On `5bddc38` with Increment 3's
  tests: `pytest -q --numprocesses auto -p no:cacheprovider` exit 0, 200 passed
  (`logs/inc4_handover_pytest.log`); `ty check scripts src tests` "All checks
  passed!". No test held the replaced behavior. New: 2 tests in `test_api.py`, 1
  in `test_html.py` (with a table-placement parser), 2 tests with 2 rows each in
  `test_probe.py` (PDFs built in the test with PyMuPDF). One assertion of mine
  expected `Results` after a dangling `First`; PyMuPDF itself stops reading the
  outline at the placeholder entry, as the plan's `DEV-010` observation says, so
  the assertion was wrong and is removed.
- **E33 — Suite and linters on the assessed content.**
  `pytest -q --numprocesses auto -p no:cacheprovider` exit 0, 207 passed;
  `pytest -q -p no:cacheprovider -p no:randomly` exit 0, 207 passed
  (`logs/inc4_pytest_parallel.log`, `logs/inc4_pytest_serial.log`); 207 test IDs
  (`logs/inc4_test_ids.txt`: Increment 3's 200 plus 7); doctests 28 passed, 1
  skipped; `ruff check` "All checks passed!"; `ruff format --check` "89 files
  already formatted"; `ty check scripts src tests` "All checks passed!";
  `interrogate` 100.0%.
- **E34 — The tests catch the defects they target.** `tools/mutate4.py` (as
  `mutate3.py`, with several edits per mutation; `logs/inc4_mutations.log`, exit
  0). All 9 changes are caught, 11 test runs in all: another PDF's page files
  kept; the figure image checked before the PDF; every page file loaded without
  facts; header rows in a `thead` of their own (the code before `DEV-009`);
  header cells written as `td`; the outline walk stopping at a missing object,
  which leaves the cycle uncut; a missing object followed; an inline field read;
  an inline field skipped with no probe error. The unmutated copy passes the 7
  targeted tests.
- **E35 — How PyMuPDF reads such outlines.** `get_toc(simple=True)` on 8 scratch
  PDFs (5 entries, one with a child): a dangling `Next` or `First` gives a
  `[level, " ", -1]` entry and ends the outline there; adding a cycle from the
  last entry back to the first makes `get_toc` return `[]` whenever its reading
  reaches the cycle. So the `[first]` row fails if the cycle is not cut after
  the dangling link.
- **E36 — Reference pages and probe facts.** `git archive HEAD` into the
  scratchpad, `generate_reference_docs.py` and Prettier there, then `diff -r`
  with the repo's reference pages: identical apart from the client's empty
  `.claude` folder (`python-api.md` holds `load`'s new return and error text).
  `tools/probe_all.py` runs `probe_pdf` on the 10 committed test PDFs with
  `83faebb`'s `src/` and with `5bddc38`'s (confirmed by `probe.__file__`): the
  facts are byte for byte equal (`logs/inc4_probe_before.json`,
  `logs/inc4_probe_after.json`).
- **E37 — Inspection and order.** The `TEXT_FLAGS` comment names the CropBox;
  `PROBE_VERSION` is unchanged; `_field_error` reads no key of object 0; the
  `load` docstrings in `api.py` and `pipeline/runner.py` and `RunResult.pages`'
  docstring say what each returns, as **Remaining fixes** asks.
  `tools/ordercheck.py order` on the 6 changed source modules and 3 changed test
  modules: only the departures listed under `DEV-001`.
- **E38 — Stand-in replays of the wheel smoke script.**
  `tools/smoke_check_name.py` on `5bddc38`: both providers `PASS`, the reruns
  `FAIL` as the negative control (`logs/inc4_smoke_check_name.log`, exit 0).
- **E39 — Full verification as handed over.** On `b579737` with the tests of
  `5ec4eec`: `pytest -q --numprocesses auto -p no:cacheprovider` exit 1, 205
  passed, 2 failed (`logs/full_handover_pytest.log`), the two rows the plan
  lists, which expected the blank entry the corrected rule removes;
  `ty check scripts src tests` "All checks passed!".
- **E40 — Test change.** The outline test is replaced by
  `test_outline_links_to_missing_objects_are_dropped_and_every_other_bookmark_kept`,
  with the same two PDFs: it expects `Intro`, `Methods`, `Results` and no probe
  error, and for the `first` row the same bookmarks as the PDF without the
  cycle. Its 2 rows keep the scenarios' allocations.
- **E41 — Suite and linters on the assessed content.**
  `pytest -q --numprocesses auto -p no:cacheprovider` exit 0, 207 passed;
  `pytest -q -p no:cacheprovider -p no:randomly` exit 0, 207 passed
  (`logs/full_pytest_parallel.log`, `logs/full_pytest_serial.log`); 207 test IDs
  (`logs/full_test_ids.txt`); `pytest --doctest-modules src` 28 passed, 1
  skipped; `ruff check` "All checks passed!"; `ruff format --check` "89 files
  already formatted"; `ty check scripts src tests` "All checks passed!";
  `interrogate` 100.0%.
- **E42 — The outline test catches the defects it targets.**
  `tools/mutate_full.py` (`logs/full_mutations.log`, exit 0): a missing link
  left in place, the walk stopping at it, and the missing object followed are
  each caught, 5 test runs in all; the unmutated copy passes both rows.
- **E43 — Reference pages and wording.** `git archive HEAD`,
  `generate_reference_docs.py` and Prettier in the scratchpad, then `diff -r`
  with the repo's pages: identical apart from the client's empty `.claude`
  folder. A search of `src/`, `scripts/`, `pyproject.toml`, `README.md` and the
  docs for "second model", "reviews every page" and "none of the PDF's stored
  text" finds none in `src/`, `scripts/` or `pyproject.toml`; `README.md` line
  13, `docs/src/content/docs/index.md` line 16 and
  `docs/src/content/docs/guides/page-extraction.md` line 11 still say a second
  model reviews every page (Documenter's). The extraction instructions end "Your
  answer is checked by code. You will be told what to fix if a check fails.";
  both `PROMPT_VERSION`s are 1, as the scope says.
- **E44 — Build and metadata.** `uv build --offline` on `git archive b579737`
  (run outside the sandbox, which blocks uv's cache; nothing was downloaded)
  built the wheel and sdist named above. `.venv/bin/twine check --strict` passed
  both. The wheel has 61 files, none under `tests/`; its `METADATA` has the new
  `Summary`, `Version: 0.1.1`, `Requires-Python: >=3.13` and the unchanged
  classifiers, and `entry_points.txt` has `pydelity = pydelity.cli:main`. An
  offline install into a fresh uv environment failed: uv's cache lacks some
  locked runtime packages (`loguru` among them), so a clean install needs PyPI,
  which is left to CI.
- **E45 — CI and release setup.**
  `git diff 126f52f HEAD -- .github release-please-config.json .release-please-manifest.json`
  is empty. `ci.yml` runs on pull requests to `main` and pushes to `main`; its
  "Lint and test" job needs "Lint and test (Python 3.13)", "Test (Python 3.14)"
  and "Wheel install" on `macos-latest`, `ubuntu-latest` and `windows-latest`,
  which build the wheel and sdist, check their metadata and run
  `scripts/smoke_installed_wheel.py`.
  `gh api repos/IDinsight/pydelity/rules/branches/main` (run outside the
  sandbox, whose proxy fails GitHub's TLS check) gives a pull request rule and
  required checks "Lint and test" and "TruffleHog secret scan".
  `gh run list --branch tz6/pipeline-step-2`: the latest CI runs are on
  `4a6bec7` (pull request 11, now closed), all `success`; none is later. The
  manifest is `0.1.1`, `release-type` `python`, `include-v-in-tag` true;
  `release.yml` runs on `release: published`; `docs.yml` on pushes to `main` and
  `v*` tags. `git log v0.1.1..HEAD` has no `!:` subject and no `BREAKING`
  footer.
- **E46 — Evidence reused.** Since Increment 4 (`5ec4eec`), the source changed
  only in `surveying/probe.py` (the outline rule), the docstrings and the one
  instruction sentence listed under `DEV-011`, the reference page generator, the
  reference pages and `pyproject.toml`'s description. E41 reruns every test on
  the final content, so the test-based conclusions of E12–E38 stand on it.
  `AC-023`'s Increment 4 evidence (E32–E35) is replaced by E40–E42. The mutation
  runs (E15, E25, E34) assessed code that is unchanged since, apart from
  `probe.py`'s outline walk, which E42 covers. The prompt comparison (E27), the
  probe-facts comparison (E36) and the module order checks (E18, E28, E37)
  assessed modules that `DEV-011` changed only in docstrings and one instruction
  sentence; the module order check on `DEV-011`'s modules finds no new departure
  (the plan's evidence, and `ordercheck.py` here).
- **E47 — CI on the final commit.** `gh pr view 12`: draft, open, head
  `1b311bc`, base `main`. `gh pr checks 12` and `gh run view 44938779421 --log`
  (`logs/full_ci_44938779421.log`; run outside the sandbox, whose proxy fails
  GitHub's TLS check), event `pull_request`, head `1b311bc`, conclusion
  `success`:
  - "Lint and test (Python 3.13)" (CPython 3.13.18): every git hook and lint
    recipe, no file changed by them, 207 passed, doctests 28 passed and 1
    skipped.
  - "Test (Python 3.14)" (Python 3.14.4): 207 passed, doctests 28 passed and 1
    skipped.
  - "Wheel install" on `ubuntu-latest`, `macos-latest` and `windows-latest`:
    built the wheel and sdist, `twine check --strict` passed both, then
    `scripts/smoke_installed_wheel.py` installed the wheel with pip into a new
    `venv` and reported "13 of 13 checks passed", no `FAIL`.
  - "Lint and test" passed; "TruffleHog secret scan" (run `44938779423`) and
    "Build the docs" (run `44938779405`) passed; "Publish to GitHub Pages" was
    skipped, as on every pull request.
  - `git diff b579737 1b311bc` changes only
    `tests/pydelity/surveying/test_probe.py` (SHA-256 `a488fc395f45a9d7…`, the
    assessed change), this report and `STATE.md`, so E39–E46 assess the content
    CI ran.
- **E48 — Full verification as handed over.** On `de4efcd` with the tests of
  `1b311bc`: `pytest -q --numprocesses auto -p no:cacheprovider` exit 1, 191
  passed, 16 failed (`logs/hints_handover_pytest.log`);
  `ty check scripts src tests` 3 diagnostics (`test_validators.py` lines 1161
  and 1166, `test_survey.py` line 481). The 16 are the tests the plan lists
  under DEV-012 (12), DEV-013 (2) and DEV-014 (2), each expecting retries on
  hint differences, the earlier message or prompt wording, the text note,
  `run_checks` holding the hints, or `verify_survey` taking review issues.
- **E49 — Test changes.** The 16 replaced-contract tests are updated to the hint
  contract: validator tests renamed from "check" to "hint" with the new
  messages, and `run_checks` and `compare_with_hints` asserted apart; P1 and P3
  rewritten for no retries on hint differences; REQ for the direction line and
  the hints section; S4 and the vocabulary test for the new heading and
  argument. New: V1, P2 (2 rows), P4. Expanded: S1 and S3 (`hints`), S2 (hint
  differences present, none in the retry). Helpers: `_retry_messages` and
  `_verifier_sections` in the page tests and `_RETRY_FEEDBACK` in both modules,
  which read PydanticAI's `<pyai:retry_feedback>` block on both providers (seen
  in a scratch dump of an extractor retry, `probe/test_dump_retry.py`).
- **E50 — Test content.** `git diff HEAD -- tests` on `de4efcd`: 3 files, 591
  insertions, 172 deletions, SHA-256 `080c66931785a977…`, S4's added scenario
  included. Before it, at the time of the budget question: 581 insertions, 171
  deletions, `9f60cbcaabbadc96…`.
- **E51 — The new and updated tests passed on their first run** against
  `de4efcd`, so E54 checks that they can fail.
- **E52 — Suite and linters on the assessed content.**
  `pytest -q --numprocesses auto -p no:cacheprovider` exit 0, 211 passed;
  `pytest -q -p no:cacheprovider -p no:randomly` exit 0, 211 passed
  (`logs/hints_pytest_parallel.log`, `logs/hints_pytest_serial.log`); 211 test
  IDs (`logs/hints_test_ids.txt`); `pytest --doctest-modules src` 28 passed, 1
  skipped; `ruff check scripts src tests` "All checks passed!";
  `ruff format --check scripts src tests` "89 files already formatted";
  `ty check scripts src tests` "All checks passed!";
  `interrogate scripts src tests` 100.0%.
- **E53 — Stand-in replay of the wheel smoke script.** `tools/smoke_replay.py`
  (`python -I`) runs the script's API run in-process with its own answers, PDF,
  models and `EXPECTED_REQUESTS`, on the editable install: `PASS` for Anthropic
  and OpenAI, each with one upload and 3 model requests, `run.json` `completed`,
  both page files, `load()` equal to the result, and five empty hint results per
  page (`logs/hints_smoke_replay.log`, exit 0). It does not install the wheel.
- **E54 — The tests catch the defects they target.** `tools/mutate_hints.py`
  copies `src/`, `tests/`, `examples/` and `pyproject.toml` to the scratchpad,
  checks that the copy's `pydelity` is imported, applies one change at a time
  and runs the named tests there (`logs/hints_mutations.log`). The unmutated
  copy passes the 13 targeted tests; all 27 changes are caught:
  - page extraction: the extractor or the verifier's correction sent back for
    hint differences; `run_checks` holding the hints; check failures dropped
    when the verdict passed; hint differences listed though the verdict passed,
    or never listed; `hints` taken from the extractor's answer; the verifier
    given no hint differences; a last answer still failing a check stopping the
    page; empty hint results left out; hint issues without item IDs; a reading
    order difference that says "fix";
  - page prompts: the page furniture order restored; the direction stated as a
    fact; no rule that the image decides; the repeated lines or fields without
    their hints heading; the survey's finding left out; the earlier closing
    sentence; a verifier told a correction must agree with the hints;
  - survey: `hints` emptied when accepted; hint differences listed though
    accepted; `run_checks` holding the hints; `page_number_differs` dropped from
    `hints`; the verifier's heading or verdict rules without hints; check
    failures dropped from the review list when the verdict passed (caught by S4
    after the user raised the limit; before it, no test caught it, E57).
- **E55 — Retry and request content.** As E54's targets show, every retry
  message the tests read, from the extractor (P2), the page verifier (P3) and
  both survey agents (S2, S3), names check failures only, and none quotes a
  stored line.
- **E56 — Reference pages and order.** `git archive HEAD` into the scratchpad,
  `generate_reference_docs.py` there with the copy's `src/` imported (11 pages),
  Prettier 3.10.1 with the repo's config, then `diff -r` with the repo's
  reference pages: identical apart from the client's empty, untracked `.claude`
  folder. `tools/ordercheck.py` (top-level order: constants, private classes and
  functions, public ones, each alphabetical) finds nothing in the three changed
  test modules and reports the known departures in
  `tests/fixtures/mock_providers.py` and `test_loading.py`
  (`logs/hints_ordercheck.log`).
- **E57 — Inspection.** The design's points hold in the code: each step's
  `validators.py` keeps `CHECKS` and `HINTS` apart; both page agents' and both
  survey agents' output validators call `run_checks` only; `_kept_answer` keeps
  a correction with no check failure; `_page_issues` and `build_survey` list
  checks, then hint differences unless accepted, then `verifier` issues;
  `PageFile.hints` and `PdfSurvey.hints` are required, so a file without them
  fails validation (`logs/hints_required_field.log`) and is made again through
  the damaged-output path the earlier tests cover. A search of `src/`,
  `scripts/` and the reference pages finds no "sends none", "none of the PDF's
  stored", "text check", "furniture check", "comparisons with the facts",
  `compare_with_facts`, `TEXT_CHECKS`, `SurveyComparisonName` or "keep what the
  image shows". `git log v0.1.1..HEAD` has no breaking marker. A whole-suite run
  on a copy whose `build_survey` drops check failures when the verdict passed
  fails only `test_package.py::test_package_loads_from_installed_tree_not_src`,
  which fails on any copy, so no test covered that case until S4's added
  scenario (E54).
- **E58 — CI state.** `gh pr list --head tz6/pipeline-step-2 --state all` (run
  outside the sandbox, whose proxy fails GitHub's TLS check): pull requests 10,
  11 and 12, all closed; 12's head is `fc6df7d`.
  `gh run list --branch tz6/pipeline-step-2`: the latest runs are on `fc6df7d`;
  none on `de4efcd`. CI runs on pull requests to `main` and pushes to `main`
  only, so a run on this content needs a commit and a pull request.
- **E59 — Evidence reused.** Since `1b311bc`, the source changed in
  `extracting/` (validators, agents, llm, prompts, extraction, schemas,
  text_layer docstring), `surveying/` (validators, survey, schemas, llm,
  prompts), `review.py`, `pipeline/runner.py` (one argument),
  `pipeline/schemas.py` (a docstring) and the reference page generator. E52
  reruns every test on the final content, so the test-based conclusions of
  E12–E42 stand on it. Of the earlier mutation runs, those on the page review
  list and the kept answer (E15) and on the survey's differences (E25) assessed
  code the hints rerun changed; E54 replaces them for that code. The other
  mutations assessed code that is unchanged. E47's CI run no longer applies.
- **Not run locally.** Python 3.14 and the wheel install on the three runners,
  which need CI (E58). The `just` recipes through `uv` (uv cannot write its
  cache in the sandbox; the `.venv/bin` tools are the versions they run). No
  real model ran.
- **Developer evidence.** The plan's DEV-012 to DEV-015 self-checks agree with
  E48–E57; they were not used as evidence.

## Open Findings and Dependencies

- No open defect in the implementation or the upstream records.
- Resolved: the user raised the scenario limit for
  `src/pydelity/surveying/survey.py` to 6 on 2026-11-22, and S4 now covers the
  survey with its verifier on (E54).
- Required unrun checks, and the blocking user question
  (`Active Work.BlockedOn`): CI on the commit holding this assessment's tests,
  for `AC-026`'s Python 3.14 run, `AC-027`, `AC-028` and `AC-029` (E58). No pull
  request is open, and CI runs only on pull requests to `main` and pushes to it,
  so the user commits the test changes with this report and `STATE.md` and opens
  a draft pull request to `main`, as for pull requests 10 to 12.
- Later-role dependencies, each pending with its owner and the evidence still
  required:
  - Documenter, documentation-record evidence in this rerun: `AC-032`, `AC-035`
    to `AC-038`, `AC-053`, the README part of `AC-030`, and the guides and FAQ
    parts of `AC-051` and `AC-052`.
  - The user: `AC-039` and `AC-040`, accepted real runs on Anthropic and OpenAI
    with the default settings and with `verify` on, including the GPF reading
    and math PDFs.
- Post-merge observation for `AC-031`: the 0.2.0 release pull request follows
  the merge to `main`.

## Resume or Handoff

Full verification is `BLOCKED` (`FULL`, target `NONE`) under recovery frame 1.
Next actions, in order:

1. Done: S4's added scenario, the reruns and the final test identity (E50, E52,
   E54).
2. After the user commits the tests with this report and opens a pull request to
   `main`, read its CI runs (Python 3.13 and 3.14, wheel install on three
   runners, TruffleHog, docs) and check that the commit's source and tests equal
   the assessed content.
3. If all pass, mark the report `COMPLETE` and hand off to Reviewer, review kind
   `IMPLEMENTATION`, under the recovery frame's rerun.

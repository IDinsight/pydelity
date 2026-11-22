<!-- STANDARDS
Artifact: ARCHITECTURE
Cycle: add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada
-->

# Technical Design: opt-in verifiers, the survey's verifier, and page extraction's remaining fixes

## Context

- Scope:
  `.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
  (`AC-001` to `AC-054`; `AC-019` and `AC-034` are retired). Target maturity is
  Level 3. Architect mode: cross-cutting, since the scope's newest rule, that
  code's measurements are hints, applies to every step that calls a model. Its
  first work item, `AC-041` and `AC-042`, reorders every Python module to the
  ordering rule of the developer and tester user styles before the other work
  changes them.
- Baseline: the survey and page extraction on `tz6/pipeline-step-2`
  (`.standards/CONTEXT.md`). Page extraction's design
  (`.standards/docs/specs/build-step-2-page-extraction-of-the-20261119T174118Z-0419318a.md`,
  decisions 1–22) and the survey's design (`git show 83743ef:...`, decisions
  1–15) stay in force except where a decision below replaces part of them, which
  the decision says.
- The analogue for everything new is page extraction's verifier:
  `extracting/agents.py` `create_verifier_agent`, `extracting/llm.py`
  `ask_verifier` and `ModelVerdict`, `extracting/schemas.py` `VerifierVerdict`
  and `PageVerification`, `extracting/extraction.py` `_kept_answer`,
  `_page_issues`, `_verifier_issue` and `_verifier_outcome`, and
  `report/html.py` `_verifier_text`.
- Constraints that shape this design: code's measurements of the PDF and the
  survey's findings are hints that the model's own reading overrides; only
  consistency checks and hard limits send an answer back, and a hint difference
  goes on the review list unless the step's verifier passed the answer or its
  correction was kept; a run stops only on an unusable answer; checks sit in
  Pydantic, then `<step>/validators.py`, then the verifier; each verifier is a
  second request to its step's model with that step's instructions only; one
  structured-output mode per provider (prompted on Anthropic, native on OpenAI);
  the PDF transport rule; no default `max_cost`; no backwards compatibility and
  no raised `PROBE_VERSION`, `PROMPT_VERSION` or `schema_version`; every CLI
  option has a short form; shipped text never mentions the development process.
- Names are proposals. The setting names `verify`, `advanced.survey.verify`,
  `advanced.extraction.verify`, the option `--verify`/`-vf` and the survey's
  agent name `surveyor` in `cost.jsonl` are the user's to approve in the
  development plan before the build step that adds them. This design creates no
  file or folder; new modules, if Developer wants any, are also the user's to
  approve.
- No project references exist under `.standards/project-references/`.

## Decision

1. **One global switch with an optional override per step, off by default.**
   `verify: bool = False` at the top level turns every step's verifier on. Each
   step's `advanced.<step>.verify: bool | None = None` overrides it for that
   step: `true` or `false` wins, `null` follows `verify`. The survey and page
   extraction get one each; every later step adds its own the same way. The CLI
   adds `--verify`/`-vf`, which sets `verify` to `true` and, when absent, leaves
   the config file's value alone, as `--overwrite` does. There is no CLI option
   per step: the overrides are set in the config file or from Python, like each
   step's instructions. `Config` gains two resolved properties beside
   `survey_model` and `extraction_model`: `verify_survey` and
   `verify_extraction` (override, else `verify`). Every step reads only these.
   This replaces page extraction's decision 10 rule that the verifier reviews
   every page: it reviews every page when on, and none when off.
2. **The switch is not a fingerprint input; a saved output made without a
   verifier is not reused while the verifier is on.** A saved survey or page
   file is reused when it is valid, its fingerprint matches, `overwrite` is off,
   and either its step's verifier is off or the file holds a verification
   (`verification` is not `null`). So turning a verifier on reruns that step's
   outputs made without one (`AC-006`), while turning it off keeps outputs a
   verifier reviewed, which are at least as checked as a new unverified run
   would be, and costs nothing. Since neither fingerprint changes, page
   extraction's switch never touches the survey, and a survey rerun reruns only
   the pages whose page context it changed (page extraction's decision 13). When
   a saved output is passed over only for lacking a verification, an info log
   line says so.
3. **A run that no verifier reviewed lists every check failure and hint
   difference it leaves.** With a step's verifier off, the producer's answer
   goes through the checks and their retries and is kept, and no verifier
   request is made. Every check still failing and every hint difference goes on
   the review list. With the verifier on, a hint difference is left off the
   review list when the verdict passed or its correction was kept; a check still
   failing is always listed. Decision 14 says which are checks and which are
   hints. Both stay recorded either way, in the output file's `checks` and
   `hints` (decision 15). This extends page extraction's decision 9 to every
   hint and to pages with no verifier, and applies the same rule to the survey.
4. **No verifier means `verification: null`.** `PageFile.verification` becomes
   `PageVerification | None` and `PdfSurvey` gains required
   `verification: SurveyVerification | None`, `null` exactly when no verifier
   ran. The page log line, the report's page card and the report's survey
   section say "no verifier ran" instead of a verifier outcome. An old
   `pdf_survey.json` without the field no longer validates and is surveyed again
   with the `damaged_output` warning (page extraction's decision 19).
5. **The survey's verifier mirrors page extraction's.** After the survey's
   answer is accepted, and only when `verify_survey` is on, a second request to
   the survey's model reviews it against the PDF and returns a `SurveyVerdict`:
   passed, or problems plus an optional full corrected `SurveyAnswer`. The
   verifier agent has `retries={"output": check_retries}` from
   `advanced.survey.check_retries`; its output validator runs C1–C7
   (`run_checks`) on the correction and raises `ModelRetry` while retries
   remain, and accepts the verdict as given on the last attempt. A correction is
   kept only when it passes every survey check. C1–C7 are all consistency checks
   or hard limits (decision 14), so each of them can block a correction, and the
   survey's hints never do. `passed`: keep the answer. Problems with a kept
   correction: keep the correction; the problems stay in the verdict only.
   Otherwise: keep the answer, and each problem becomes a `verifier` review
   issue of the survey. No loop back to the survey request and no second
   verification. The profile and proposal are then built from the kept answer by
   the existing `build_survey` rules, so the user's languages stay first and the
   facts copy is untouched (`AC-008`).
6. **The survey's verifier reuses the survey request's PDF attachment.** It
   sends the same `PdfAttachment` the survey request used (`ModelSurvey`
   `attachment`): the recorded or new upload, or the PDF inside the request when
   this run's upload failed. It makes no upload of its own. If the provider says
   the file is gone, it uploads once more and repeats the verifier request, as
   `ask_model` does for the survey request. No cache is shared with the survey
   request: the verifier's instructions differ, and so does the output schema,
   which prompted output adds to Anthropic's instructions and OpenAI puts in its
   cached prefix. A verified survey therefore pays for the PDF twice; the
   verifier's own check retries read it from the cache.
7. **The survey verifier's prompt reuses the survey's rules.**
   `surveying/prompts.py` gains `verify_survey`, a `PromptPair`. System message:
   the audit task (another model's survey of this PDF, check it and correct it),
   a review checklist of what code cannot judge, the verdict rules, the survey's
   own rules from labels through notes, and `advanced.survey.instructions` last
   under the survey's existing heading. User message: the survey's own user
   message (page count, facts summary, repeated lines with their IDs, the user's
   languages), then `The survey answer to review:` and the answer as JSON, then
   the checks it still fails (one line per failure, or `none`), then its
   differences from the measured facts as hints (one line per `rotation_differs`
   or `page_number_differs` difference, or `none`; decision 16). This work needs
   no change to what `survey_pdf`'s messages say; Developer may move the rule
   text both prompts share into sections of its own. `PROMPT_VERSION` stays 1,
   as the scope says, and covers both prompts.
8. **Every survey request names its agent.** The survey's own requests are made
   by `surveyor` and its verifier's by `verifier`; both have `step: "survey"`
   and `page_index: null`. With every request of every step naming its agent,
   `LedgerEntry.agent` becomes a required `str`: `surveyor` or `verifier` for
   the survey, `extractor` or `verifier` for page extraction, and each later
   step names its own the same way. A `cost.jsonl` whose survey lines have
   `agent: null` no longer validates and is damaged, as page extraction's
   decision 19 treats 0.1.x ledgers. `LedgerModel` needs a wrapper that names an
   agent without a page, and every request goes through one; it keeps the step's
   PDF, so each survey request's bound counts the PDF's tokens and goes through
   `SpendGuard`'s reservation like every other request (`AC-016`). The run's
   survey cost (`RunCost.by_step`, the step's log line) sums every survey line,
   so it includes the verifier.
9. **The estimate prices a verifier only when it will run.** `StepEstimate`
   gains `verifier: bool`, whether its figures include the step's verifier
   requests; the CLI's estimate lines say so. Survey with its verifier on:
   expected adds one verifier request whose input is the PDF, the verifier's
   prompt and `TYPICAL_OUTPUT_TOKENS` of answer, with
   `TYPICAL_SURVEY_VERDICT_OUTPUT_TOKENS = 6_000` of output (three quarters of a
   typical answer, the ratio page extraction uses; the real runs measure it);
   maximum adds `check_retries + 1` verifier requests with `max_output_tokens`
   each and `(attempt + 1) * max_output_tokens` of earlier answers in their
   input; `requests_max` is `2 * (check_retries + 1)`. Page extraction with its
   verifier off: expected and maximum price the extractor only and
   `requests_max = attempts * pages`; with it on, as today. The verifier's
   prompt size is measured the way page extraction measures its own: its
   messages built with an empty answer, plus the verdict's JSON schema.
10. **A failed survey verifier request stops the run and leaves no new survey.**
    A provider error after the provider retries, a timeout, a refusal, running
    out of output tokens, or no verdict matching `SurveyVerdict` ends the survey
    step as `failed`, as a failed survey request does today: the errors map as
    in `surveying/llm.py` `_run_agent` (`ProviderError` with the upload error
    after an inline fallback; `SurveyError` naming the verifier and, for output
    tokens, `advanced.survey.max_output_tokens`). The CLI shows the message and
    exits `FAILED` (1); Python raises the error. No `pdf_survey.json` is
    written, and an existing one is left as it was. The ledger keeps the survey
    request's paid lines and `uploads.json` keeps the upload, so the next run
    reuses the upload but pays for the survey request again.
11. **Each step keeps its own verifier code.** The survey's verifier follows the
    survey's split: `schemas.py` (`SurveyVerdict`, `SurveyProblem`,
    `SurveyVerification`), `prompts.py` (`verify_survey`), `agents.py` (its
    agent), `llm.py` (asking it, returning the verdict, its attempts and its
    correction's check failures, like `ModelVerdict`), and `survey.py` (applying
    the verdict and building the review list). Nothing moves into a shared
    verifier module: the two steps' answer types and keep rules differ. The
    review-issue name `verifier` becomes shared by both steps in `review.py`.
12. **The remaining fixes are made where each defect lives**, without raising
    `PROBE_VERSION`: `load()` filters page files by the facts' PDF hash, the
    report renders a table's rows in one row group, the outline walk sets links
    to objects the PDF does not have to null, the form reader skips inline
    widgets with a probe error, and the `TEXT_FLAGS` comment names the CropBox.
    Details under **Remaining fixes**.
13. **Every module is reordered first, by moving whole definitions only.**
    Before any other build step, each Python module in `src/pydelity/`,
    `scripts/` and `tests/` is put in the order **Module order** defines. A move
    takes a definition with its decorators and the comment lines directly above
    it, and changes no text. Nothing whose order is part of a contract moves:
    fields of Pydantic models and dataclasses (they fix the JSON key order of
    every output file and the constructor's arguments), enum members (their
    order reaches prompts and outputs through `list(ItemKind)` and the like),
    parameters, and `__all__`. Where the rule's order would break import, as a
    definition placed above a name its decorators, default values, base classes
    or eagerly evaluated annotations use, the module keeps the order that works.
    Such departures, including the dependency order that schema modules such as
    `surveying/schemas.py` already use, are listed by module with their reason
    in the development plan for `src/pydelity/` and `scripts/` and in the
    verification report for `tests/`. Annotations are not rewritten as strings
    to make a move possible. Developer reorders `src/pydelity/` and `scripts/`
    (`AC-041`); Tester reorders `tests/` (`AC-042`), since tests are Tester's.
    Each reorder is ready to commit on its own, so the user can review it apart
    from the verifier work.
14. **Code's measurements are hints, and only checks send an answer back.** This
    is the rule for every step that calls a model, and each later step adopts it
    when it is built. A step's comparisons with what code measured or the survey
    found about the PDF are its **hints**; its consistency checks and hard
    limits are its **checks**. **Checks and hints** lists both for the survey
    and page extraction. The rule is enforced at these points:
    - Each step's `validators.py` keeps the two apart: `CHECKS` with
      `run_checks`, and `HINTS` with `compare_with_hints`, each hint returning
      its differences as `CheckFailure`s. Page extraction's `reading_order`,
      `artifacts`, `form_fields`, `text_dropped` and `text_added` move from
      `CHECKS` and `TEXT_CHECKS` to `HINTS`, and `TEXT_CHECKS` goes. The
      survey's `compare_with_facts` becomes `compare_with_hints`, built the same
      way. What each hint compares, its tolerances and the `comparison_status`
      gate on the text hints stay as they are.
    - Each agent's output validator, the producer's and the verifier's, runs
      `run_checks` only. It raises `ModelRetry` only for a check failure, and
      the retry message lists check failures only. An answer or correction that
      differs from the hints and passes every check is accepted at once. Page
      extraction's `_TEXT_NOTE` goes, since no retry message is about text.
    - A verifier's correction is kept when it passes every check, whatever its
      hint differences (`AC-047`). This replaces page extraction's rule that a
      correction passes every check other than `text_dropped` and `text_added`.
    - Hints are compared on the answer a verifier reviews, for its request, and
      on the kept answer, for `hints` and the review list (decisions 3 and 15).
    - A hint difference never raises an error and never fails a page, a step or
      a run. What stops a run stays as it is (`AC-049`): no answer matching the
      format within the retries, a refusal, running out of output tokens, or a
      provider error after the provider retries. A kept answer still failing a
      check is built and written as now: a ref used twice keeps its first item,
      unknown container and caption refs become `null`, boxes are kept inside
      the page, and `covering_range` skips page ranges outside the PDF.
    - A hint difference's message says what code measured or the survey found
      and what the answer says. It never tells the model what to change. A check
      failure's message may say what to fix.
    - The prompts present measured facts and the survey's findings as hints
      (decision 16).

    A later step follows the same pattern: its checks may send an answer back
    within its check retries, its hints never do, its output file records both
    apart, and its review list follows decision 3.

15. **Output files record hints apart from checks.** `PageFile` gains required
    `hints: list[ExtractionHintResult]` and `PdfSurvey` gains required
    `hints: list[HintResult]`: each hint's result on the kept answer, in the
    order of `HINTS`, whether or not the review list shows its differences. A
    result has `name` and `differences: list[CheckFailure]`, which is empty when
    the answer agrees with the hint. It has no `attempts` or `passed`, since
    hints are not retried and `differences` says whether the answer agrees.
    `checks` keeps checks only: a page file's six, and the survey's C1–C7 as
    now. In `review.py`, `ExtractionCheckName` becomes the six checks, a new
    `ExtractionHintName` holds the five hints, `SurveyComparisonName` becomes
    `SurveyHintName`, and `IssueName` takes all of them. A review issue from a
    hint keeps the hint's name in `check`, so the names in `run.json` stay the
    same. A page file or `pdf_survey.json` without `hints` no longer validates
    and is made again with the `damaged_output` warning.
16. **The prompts present hints.** Page extraction, both prompts:
    - The page text gives the writing direction as what the survey found, such
      as "The survey found the page written left to right." The line about how
      the image was turned stays a plain statement, since it says what code did
      to the image. The repeated lines, each with its stored text and what the
      survey found it to be (page furniture, content, not decided), and the
      fillable form fields with their stored values come under headings that
      call them hints from the PDF's stored data and the survey, which the image
      overrides.
    - `_RULES` gains a short paragraph on hints: what comes with the page is
      taken from the PDF's stored data and the survey and can be wrong, so the
      image decides. The page furniture rule drops "include each one found to be
      page furniture in an item with role artifact"; the model decides from the
      image whether a repeated line is page furniture, content, or not on the
      page (`AC-054`). The forms rule says to set `fillable_name` when a field
      item is one of the fields given and to give the value or mark the image
      shows. The reading order rule reads the page in the direction it is
      written in, with the survey's direction as a hint.
    - The extraction model's system message ends with "Your answer is checked by
      code for form and consistency, and you will be told what to fix if a check
      fails."
    - The page verifier's user message gives, after the extraction,
      `Checks it still fails, which a correction must pass:` with one line per
      check failure or `none`, then
      `Differences from the hints, which the page image overrides:` with one
      line per hint difference or `none`. A `text_dropped` line quotes the
      stored line, shortened as the failure message already does (`AC-046`).
      `_VERDICT`'s second paragraph says a correction must pass the checks, the
      hint differences come from stored data and the survey and can be wrong, a
      difference is a problem only when the extraction is wrong about the page,
      and a correction need not agree with the hints.
    - What the extraction model's request carries is unchanged (`AC-045`): the
      page image, the page's repeated lines with their stored text and its
      fillable form fields with their values. Its retry messages no longer quote
      stored lines.

    Survey: its own request already calls the facts hints and asks for what the
    model reads, so it is unchanged. Its verifier's heading becomes
    `Differences from the measured facts, which are hints the PDF overrides:`,
    and its `_VERDICT` says a correction must pass the checks and need not agree
    with the facts. No prompt version changes (scope), and decision 15's
    required field means no page file or survey made with the older prompts is
    reused.

### Defaults

| Setting                      | Default | Range                    |
| ---------------------------- | ------- | ------------------------ |
| `verify`                     | `false` | bool                     |
| `advanced.survey.verify`     | `null`  | bool, or `null` (follow) |
| `advanced.extraction.verify` | `null`  | bool, or `null` (follow) |

## Acceptance Coverage

- `AC-001`: decision 1 (defaults off), decision 3 (no verifier request when
  off), decision 8 (no `verifier` ledger lines without a verifier request).
- `AC-002`: decision 1, **Settings**, **CLI**.
- `AC-003`: decision 1, **Settings**; deep merge in `config/loading.py`
  `resolve_config` already lets a Python caller pass
  `advanced={"survey": {"verify": True}}`.
- `AC-004`: **Example config files**; the existing completeness test in
  `tests/pydelity/config/test_loading.py` holds them to every setting.
- `AC-005`: decision 9, **Cost estimate**.
- `AC-006`: decision 2.
- `AC-007`: decisions 5 and 7, **Survey verifier request**.
- `AC-008`: decision 5 (full `SurveyAnswer` correction built by `build_survey`),
  **Survey verdict**.
- `AC-009`: decision 5 (output validator runs C1–C7 within
  `advanced.survey.check_retries`; kept only when every check passes).
- `AC-010`: decision 5, **Survey verdict application**.
- `AC-011`: decisions 3, 14 and 15, **Survey verdict application**.
- `AC-012`: decision 6.
- `AC-013`: decision 4, **`pdf_survey.json`**.
- `AC-014`: decision 4, **HTML report**.
- `AC-015`: decision 8, **`cost.jsonl`**.
- `AC-016`: decisions 8 and 9.
- `AC-017`: decision 10.
- `AC-018`: decision 3, **Page extraction without a verifier**.
- `AC-020`: decision 4, **Page file**, **HTML report**.
- `AC-021`: **Remaining fixes** (`load()`).
- `AC-022`: **Remaining fixes** (report tables).
- `AC-023`: **Remaining fixes** (outline links).
- `AC-024`: **Remaining fixes** (inline widgets).
- `AC-025`: **Remaining fixes** (`TEXT_FLAGS`).
- `AC-026`, `AC-050`: **Test seams** define the contracts the tests rely on;
  writing and running the tests is Tester's.
- `AC-027`: No architectural impact — CI's workflows, jobs and required checks
  stay as they are; Tester's evidence covers them.
- `AC-028`: **CI and release** (the smoke test runs the survey and page
  extraction from the built wheel with mocked responses); evidence is Tester's.
- `AC-029`, `AC-031`: No architectural impact — the build, the wheel's contents,
  release-please's configuration and the release workflows stay as they are; the
  release itself follows sign-off and merge.
- `AC-030`: **CI and release** (`pyproject.toml` description); the README is
  Documenter's.
- `AC-032`, `AC-035`, `AC-036`, `AC-037`: No architectural impact — Documenter's
  docs and README wording, which must describe the behavior this design fixes
  (decisions 1–10, **Interfaces and Contracts**).
- `AC-033`: **Docs and docstrings** (the reference pages are generated from the
  code's names and docstrings, `hints` included); the guide pages are
  Documenter's.
- `AC-051`: decision 16, **Docs and docstrings** (the `prompts.py`,
  `text_layer.py` and `validators.py` docstrings); the guides and FAQ are
  Documenter's.
- `AC-052`: **Docs and docstrings** (the generated checks pages list checks and
  hints apart); the guides are Documenter's, describing decisions 3 and 14.
- `AC-038`: No architectural impact — Documenter's update to
  `artifacts/next_cycle_inputs.md`; decision 1 is what it records for later
  steps.
- `AC-053`: No architectural impact — Documenter's update to
  `artifacts/next_cycle_inputs.md`; decision 14 is what it records for later
  steps.
- `AC-039`, `AC-040`: No architectural impact — the user's review of real runs
  after the build, made with the default settings and with `verify` on.
- `AC-041`: decision 13, **Module order** (`src/pydelity/` and `scripts/`, by
  Developer).
- `AC-042`: decision 13, **Module order** (`tests/`, `conftest.py` files
  included, by Tester).
- `AC-043`: decisions 14 and 16, **Checks and hints**.
- `AC-044`: decision 14, **Checks and hints**.
- `AC-045`: decision 16 (what the extraction model's request carries; no stored
  line in its retry messages).
- `AC-046`: decision 16 (the page verifier's hints section).
- `AC-047`: decision 14 (the keep rule).
- `AC-048`: decisions 3 and 15, **Page extraction without a verifier**.
- `AC-049`: decision 14 (what stops a run; how a failing answer is built).
- `AC-054`: decision 16 (repeated lines and the survey's findings as hints; no
  page furniture order).

## Components

- **Settings** (`config/schemas.py`): `Config.verify`, `SurveyConfig.verify`,
  `ExtractionConfig.verify`, the resolved properties `verify_survey` and
  `verify_extraction`.
- **CLI** (`cli.py`): `--verify`/`-vf`.
- **Survey step** (`surveying/`): the verifier's schemas, prompt, agent and
  request (decision 11); `survey.py` applies the verdict, builds the review
  list, and adds the verification rule to `saved_survey`; `validators.py`
  `HINTS` and `compare_with_hints`, `schemas.py` `HintResult` and
  `PdfSurvey.hints` (decisions 14 and 15).
- **Page extraction step** (`extracting/extraction.py`, `extracting/llm.py`,
  `extracting/schemas.py`): the verifier made optional in the page task, the
  kept-answer and review-list rules with no verdict, the reuse rule in
  `plan_pages`, the log line; the hint rule in `validators.py`, `agents.py`,
  `prompts.py` and `extraction.py`, `ExtractionHintResult` and `PageFile.hints`
  (decisions 14–16).
- **Review** (`review.py`): `verifier` shared by both steps; the check and hint
  names apart (decision 15).
- **Costs and providers** (`costs/budget.py`, `costs/schemas.py`,
  `providers/ledger_model.py`): the estimates, `StepEstimate.verifier`, the
  required `LedgerEntry.agent`, the wrapper that names an agent without a page.
- **Runner** (`pipeline/runner.py`): the survey verifier's prompt size in the
  estimate, the estimate lines, `load_run`'s page filter. No new step, status or
  `run.json` field.
- **Report** (`report/html.py`): the survey's verifier outcome, "no verifier
  ran", table row groups.
- **Probe** (`surveying/probe.py`) and `utils/pdf.py`: the outline, inline
  widget and comment fixes.
- **Every Python module** in `src/pydelity/`, `scripts/` and `tests/`: the
  reorder (decision 13).

Dependency direction is unchanged: `extracting` imports `surveying.schemas` and
`review`; `surveying` never imports `extracting`; `pipeline` imports both.

## Interfaces and Contracts

### Checks and hints

- Survey checks, which may send an answer back: C1–C7, of which `labels`,
  `artifacts` and `languages` are consistency checks and `regions`, `rotation`,
  `page_numbering` and `writing_direction` are hard limits.
- Survey hints, which never do: `rotation_differs`, `page_number_differs`.
- Page extraction checks: `labels`, `content`, `languages`, `containers` and
  `captions` are consistency checks; `boxes` is both, since a box must be well
  formed and not shared (consistency) and on the page (hard limit).
- Page extraction hints: `reading_order`, `artifacts`, `form_fields`,
  `text_dropped`, `text_added`.

The names run in today's order. Page extraction's `CHECKS`: `labels`, `content`,
`languages`, `boxes`, `containers`, `captions`; its `HINTS`: `reading_order`,
`artifacts`, `form_fields`, `text_dropped`, `text_added`. The survey's C1–C7
stay in their order, and its `HINTS` are `rotation_differs`, then
`page_number_differs`.

Hint messages describe the difference and never tell the model what to change
(decision 14). In the sense of, with the exact words Developer's:

- `text_dropped`: the page's text layer has the line '…', which is not in the
  answer;
- `reading_order`: the survey found the page written top to bottom, but
  `column_order` is null; `column_order` is set, but the survey found the page
  written left to right; item 't3' starts 300 units above item 't2', before it,
  without a move of 200 units to the right, for the direction the survey found;
- `artifacts`: the survey found the repeated line R1, '…', to be page furniture;
  it sits at […] on the grid, and no item with role artifact covers it;
- `form_fields`: the PDF stores '…' for the form field 'x', but its field items
  say '…'; the form field 'x' is on the page twice, and one field item names it;
- the survey's `rotation_differs` and `page_number_differs` keep their current
  messages, which already describe.

### Module order

Top-level statements of each module, in this order:

1. The module docstring, `from __future__` imports, the other imports and any
   `if TYPE_CHECKING:` import block, as they are.
2. Module-level assignments (constants and any other module variables) and type
   aliases (`type` statements). Dunder names such as `__all__` and `__version__`
   first, then private names, then public names. Within the private names and
   within the public names, assignments come before type aliases, each in
   alphabetical order.
3. Private classes, then private functions, each in alphabetical order.
4. Public classes, then public functions, each in alphabetical order.
5. Statements that run code, such as `_logger.disable("pydelity")` in
   `__init__.py` or `sys.path.insert(...)` in
   `scripts/smoke_installed_wheel.py`, keep their place relative to what they
   use and what uses them, and an `if __name__ == "__main__":` block stays last.

Inside each class: its docstring, then class attributes and fields where they
are, then methods: names that begin with an underscore (dunder methods included)
before the others, each in alphabetical order, except that `__init__` comes
first, a property's setter stays right after its getter, and Pydantic validators
stay where the model needs them. Nested classes stay where they are.

Alphabetical order compares names as Python strings, so `_` and capitals sort
before lowercase letters. Test modules follow the same rule: `test_` functions
and fixtures are public names, helpers with an underscore are private.

The docs generator (`scripts/generate_reference_docs.py` `_constants`) lists the
public constants of `costs/budget.py` and `surveying/probe.py` in source order,
each with the comment lines directly above it. So a moved constant takes its
comment with it, and after the reorder `just docs-reference` is run and its
changes, which only reorder those lists, land with the reorder, keeping CI's
stale-reference check passing.

### Settings

- `verify: bool = False` — "Whether a verifier reviews each step's answer: a
  second request to the step's model that checks the answer against the PDF and
  may correct it. Each verifier request adds cost."
- `advanced.survey.verify: bool | None = None` — "Whether a verifier reviews the
  survey's answer; `verify` if unset."
- `advanced.extraction.verify: bool | None = None` — "Whether a verifier reviews
  each page's extraction; `verify` if unset."
- The other `advanced.survey` and `advanced.extraction` settings (`effort`,
  `instructions`, `max_output_tokens`, `request_timeout_seconds`,
  `check_retries`) apply to the step's verifier as to its producer. Docstrings
  that call the verifier a "model" say "the verifier" or "a second request to
  the same model" instead.

### Example config files

`examples/config.json` and `examples/config.yaml` gain `verify: false` (after
`pdf`), `advanced.survey.verify: null` and `advanced.extraction.verify: null`
(each last in its section), in alphabetical key order like the rest, with
comments saying what the setting does, that `null` follows `verify`, and that a
verifier adds cost.

### CLI

- `--verify`/`-vf`: "Have a verifier review each step's answer, at extra cost."
  It is `bool | None` like `--overwrite` and passes `verify=True` when given and
  nothing otherwise.
- The estimate lines the CLI shows (`pipeline/runner.py` `_log_estimate`) name
  each step's verifier when its figures include one, such as
  `Survey with its verifier`.
- Exit codes, the question, `--yes` and the summary are unchanged.

### Survey verdict

- `SurveyProblem`: `category` (`labels`, `languages`, `writing_direction`,
  `rotation`, `page_numbering`, `artifacts`, `regions`, `continuation`,
  `start_markers`, `other`), `description: str` (what is wrong and where,
  quoting the text concerned), `page_index: int | None` (the page it is about;
  `null` when it is about the whole PDF or several pages).
- `SurveyVerdict`: `passed: bool`, `problems: list[SurveyProblem]`,
  `corrected: SurveyAnswer | None` (the whole answer again with every problem
  fixed). Pydantic invariants as `VerifierVerdict`: passed means no problems and
  no correction; not passed means at least one problem. Only plain types, enums,
  lists and objects, so it fits prompted output on Anthropic and native output
  on OpenAI.
- `SurveyVerification`: `attempts` (verdicts given: 1 plus the retries used),
  `correction_applied: bool`, `correction_failures: list[CheckResult]` (the
  checks a correction that was not kept still failed; empty when it was kept or
  there was none), `verdict: SurveyVerdict` (as given).

### Survey verifier request

- Content: `[attachment.content, user message, CachePoint()]`, as the survey
  request, with the instructions from `verify_survey` (decision 7).
- The checklist names what code cannot judge: labels that do not fit the
  content, content no label fits, or labels that should be one; regions on the
  wrong area or with the wrong label; page furniture classified as content and
  content classified as furniture, including furniture with no repeated line;
  pages that are not upright as the rotation says; page numbering whose ranges,
  style or offset differ from the printed numbers; the writing direction; the
  languages; continuation notes and start markers that are wrong or missing. It
  says the measured facts can be wrong and the PDF decides, so a difference from
  the facts is a problem only when the answer is wrong about the PDF.
- Verdict rules as page extraction's: passed with no problems and `corrected`
  null when nothing material is wrong; otherwise every problem, then the whole
  answer corrected, starting from the answer and keeping what is right,
  including every repeated line's accounting; `corrected` null only when the
  verifier cannot correct it; problems change what the answer says about the
  PDF, not matters of taste.
- Correction retry message: "Your corrected survey does not pass every check.
  Give the whole verdict again, with the correction fixed." followed by the
  survey's `retry_message`.
- No prompt names a document type, language or direction.

### Survey verdict application

1. Survey answer accepted (all checks passed, or check retries ran out).
2. When `verify_survey` is on: the verifier request (decision 5).
3. Kept answer: the correction when the verdict has one that passes every check,
   else the survey's answer. `checks` are the kept answer's results with the
   attempts of the model that gave it (the verifier's when its correction was
   kept).
4. `issues`, in this order: each check still failing on the kept answer; then
   each `rotation_differs` and `page_number_differs` difference in `hints`,
   unless `verification` is set and the verdict passed or its correction was
   applied; then, when a verdict was given and its correction was not applied,
   one issue per problem: `step: "survey"`, `check: "verifier"`,
   `message: "verifier: <description>"`, `details: {"category": <category>}`,
   `page_index` from the problem, `item_id: null`.
5. The survey's log line adds the verifier's outcome: `passed`,
   `corrected the survey`, `found <n> problems`, or `no verifier`.

### `pdf_survey.json`

- `verification: SurveyVerification | None` (required): the verifier's review;
  `null` when no verifier ran.
- `hints: list[HintResult]` (required): each hint's differences on the kept
  answer (decision 15).
- `issues` docstring: checks still failing on the kept answer, hint differences
  unless the verifier passed the answer or its correction was kept, and the
  verifier's problems when its correction was not kept.
- `checks` docstring: the kept answer's checks, the survey's or the verifier's
  correction.
- No new input field: `verification` tells whether a verifier ran (decision 2).

### Page extraction without a verifier

- `StepModel` (or the page task) carries `verify_extraction`. With it off, the
  page task runs the extractor and keeps its answer; `_kept_answer` takes no
  verdict and sets `verification` to `null`.
- `_page_issues`, in this order: each check still failing on the kept answer;
  each hint difference in `hints`, unless `verification` is set and the verdict
  passed or the correction was applied; `no_matching_label` issues; then
  `verifier` issues, only when `verification` is set and the correction was not
  applied.
- `_kept_answer` keeps a correction under decision 14's rule.
- `plan_pages` reuses a page file only under decision 2's rule.
- Log line: `verifier <outcome>` becomes `no verifier` when none ran.
- `request_sizes` and `request_sizes_before_survey` keep measuring the
  verifier's text; `estimate_extraction` prices it only when the verifier is on.

### Page file

- `verification: PageVerification | None` (required): the verifier's review;
  `null` when no verifier reviewed the page.
- `hints: list[ExtractionHintResult]` (required): each hint's differences on the
  kept answer (decision 15). `checks` holds the six checks only.
- `issues` docstring: hint differences are listed unless the verifier passed the
  page or its correction was applied, so every one is listed on a page no
  verifier reviewed.
- `PageVerification.correction_applied` docstring: a correction replaces the
  extraction when it passes every check; `correction_failures` holds checks
  only.
- `text_comparison` is unchanged and says whether the text hints ran.

### `cost.jsonl`

- `agent: str` (required): the step's agent that made the request, `surveyor` or
  `verifier` for the survey, `extractor` or `verifier` for page extraction
  (decision 8). `request_number` counts per step, page and agent, as now.

### Cost estimate

- `StepEstimate.verifier: bool` (required): whether `expected_usd`, `max_usd`
  and `requests_max` include the step's verifier requests; `false` for a reused
  step.
- `estimate_survey` reads `verify_survey` and takes the verifier's prompt size
  (decision 9). The runner's `_prompt_chars` (or a sibling) measures the
  verifier's messages with an empty `SurveyAnswer` plus `SurveyVerdict`'s JSON
  schema, and the run, `estimate()` and `aestimate()` all use it.
- `estimate_extraction` reads `verify_extraction` (decision 9).
- `CostEstimate.over_max_cost`, the plan-time check, the single question per
  run, `--yes`, `allow_over_max_cost` and `BudgetExceededError` are unchanged.

### HTML report

- Survey: the profile section's details gain "Verifier": `passed`,
  `found <n> problems and its correction was kept`,
  `found <n> problems, listed for review`, or `no verifier ran`.
- Pages: `_verifier_text` of `null` is `no verifier ran`.
- The review section already lists every issue with its step; survey `verifier`
  issues need nothing new.

### Remaining fixes

- `load()` (`pipeline/runner.py` `_load_pages`): returns only page files whose
  `inputs.pdf_sha256` equals `pdf_facts.json`'s `pdf.sha256`, in page order. The
  hash is compared before the figure-crop check, so another PDF's page file with
  a missing crop is left out rather than raising. With no `pdf_facts.json`,
  which PDF the folder holds is unknown and `pages` is empty. A page file that
  does not validate still raises `OutputError`, since its PDF cannot be told.
  `RunResult.pages`' docstring says what each function returns: the selected
  pages for a run, the folder's PDF's page files for `load`.
- Report tables (`report/html.py` `_item_table`): every row goes in one row
  group, with header-row cells as `th`, so a header cell's `rowspan` reaches the
  body rows as the page file says and HTML does not cut it at a `thead`
  boundary. `report.css` has no `thead` rule to move.
- Outline links (`surveying/probe.py` `_cut_outline_cycle`): a `First` or `Next`
  link to an object number the PDF does not have (not between 1 and
  `xref_length() - 1`) is set to `null` in the open document, and the walk
  carries on with the links left. `get_toc` then reads every entry it can reach,
  in reading order. Left in place, such a link gives a blank entry (title `" "`,
  page -1), and a missing `First` also drops the entries that follow its entry
  at the same level (PyMuPDF 2.1). The missing object is never read, no probe
  error is recorded and the file is not written. A cycle after the link is still
  cut. Developer updates the function's docstring to match and may rename it.
- Inline widgets (`surveying/probe.py` `_form`): an annotation whose object
  number is 0 (written inline in `/Annots`) cannot be loaded as a widget. It is
  skipped with one `form` probe error naming its page, without reading keys of
  object 0, and the PDF's other fields are kept. `_field_error` never reads keys
  of object 0.
- `utils/pdf.py`: the `TEXT_FLAGS` comment says text is clipped to the page's
  CropBox, as PyMuPDF does with `TEXT_MEDIABOX_CLIP`.

### Docs and docstrings

- `scripts/generate_reference_docs.py` picks up the new settings, the CLI
  option, `PdfSurvey.verification`, `SurveyVerification` and its parts, the
  nullable `PageFile.verification`, `StepEstimate.verifier` and the docstring
  changes from the code, and the survey checks page lists the survey's
  `verifier` issue name, so CI's staleness check covers them.
- Docstrings that say pydelity sends none of the PDF's stored text, or that a
  text difference sends the answer back (`extracting/prompts.py`,
  `extracting/text_layer.py`, `extracting/validators.py`,
  `extracting/agents.py`), say what is sent and what happens: the page's
  repeated lines with their stored text and the survey's findings, and its form
  fields with their values, all as hints; with the verifier on, its request
  lists the answer's hint differences, quoting stored lines; a hint difference
  never sends an answer back. `surveying/validators.py` and `review.py` say the
  same of the survey's hints.
- The generated checks pages (`scripts/generate_reference_docs.py`
  `extraction-checks` and `survey-checks`) list each step's checks and hints
  under headings of their own, from `CHECKS` and `HINTS`, and say that a check
  may send an answer back within the check retries, a hint never does, when a
  hint difference goes on the review list, and that a kept answer still failing
  a check is kept and listed (`AC-052`).

### Test seams

- The survey verifier's user message contains the line
  `The survey answer to review:`, so the stand-in provider can route a survey
  verifier request to a queued survey verdict, apart from queued survey answers.
  Page requests keep their existing markers.
- Every retry message, from either step's producer or verifier, is built from
  `run_checks` failures only, so no hint difference can appear in one.
- Hint differences reach a model only in a verifier's user message, after the
  heading `Differences from the hints, which the page image overrides:` on a
  page and
  `Differences from the measured facts, which are hints the PDF overrides:` in
  the survey.
- No step code reads the environment or chooses behavior for tests.

### CI and release

- Workflows, jobs and required checks are unchanged.
  `scripts/smoke_installed_wheel.py` keeps running the survey and page
  extraction from the built wheel against the stand-in, with the default
  settings at least.
- `pyproject.toml`'s description says pydelity surveys a PDF and extracts its
  pages, with an optional verifier for each step. Classifiers, the version and
  release-please's configuration are unchanged.

## Data and Control Flow

1. Settings resolve `verify_survey` and `verify_extraction` once.
2. Survey step: measure facts; reuse `pdf_survey.json` under decision 2's rule,
   else estimate (with the survey's verifier when on, and with page extraction's
   when it follows), ask, then the survey request with checks and retries; when
   `verify_survey` is on, the verifier request on the same attachment, given the
   answer's check failures and hint differences, with checks on its correction;
   apply the verdict; build the profile, proposal, checks, hints and issues from
   the kept answer; write `pdf_survey.json` atomically. A failed verifier
   request ends the step `failed` with nothing written (decision 10).
3. Pause after a new survey, as now.
4. Page extraction: plan pages under decision 2's rule; estimate when the survey
   was reused; per page, render, read the text layer, run the extractor with
   checks and retries; when `verify_extraction` is on, compare the answer with
   the hints, run the verifier with its check failures and hint differences, and
   apply its verdict; compare the kept answer with the hints; build checks,
   hints and issues under decisions 3 and 15; write crops and the page file; log
   the outcome.
5. Each request goes through its agent's `LedgerModel` wrapper, which reserves
   its bound, sends, writes its ledger line with step, page and agent, and
   releases the reservation.
6. `run.json`, the report and the summary as now; `review` holds the survey's
   issues, then each selected page's.

## Technical Acceptance Criteria

- `AC-001`: with no setting given, `verify_survey` and `verify_extraction` are
  both false, no request is made through a `verifier` wrapper, and no ledger
  line has `agent: "verifier"`.
- `AC-002`: `verify: true` in a JSON or YAML file, `--verify`/`-vf`, and the
  keyword `verify=True` each make both resolved properties true when no override
  is set.
- `AC-003`: `advanced.<step>.verify` of `true` or `false` sets that step's
  resolved property whatever `verify` is, leaves the other step's unchanged, and
  `null` follows `verify`; a file and a nested `advanced` keyword both work.
- `AC-004`: both example files hold `verify: false`,
  `advanced.survey.verify: null` and `advanced.extraction.verify: null`, and
  load without a `ConfigError`.
- `AC-005`: a step's estimate has `verifier` equal to whether its verifier will
  run, and its expected cost, maximum and `requests_max` include the verifier's
  requests exactly when `verifier` is true, in the CLI's estimate, the run's
  plan-time check, `estimate()` and `aestimate()`.
- `AC-006`: a saved survey or page file with `verification: null` is not reused
  while its step's verifier is on, and one with a verification is reused while
  it is off; no fingerprint includes a verifier switch; changing only
  `advanced.extraction.verify` never makes the survey step run.
- `AC-007`: the survey verifier's request carries the PDF, the survey's user
  message, the answer as JSON, its failing checks and its comparison
  differences, with `verify_survey`'s instructions ending with
  `advanced.survey.instructions` when set.
- `AC-008`: a kept correction becomes the profile and proposal through
  `build_survey`, with `config.languages` first and `facts` equal to the
  measured facts.
- `AC-009`: a correction failing any of C1–C7 is sent back while
  `advanced.survey.check_retries` allows and is never kept.
- `AC-010`, `AC-011`: `issues` follow **Survey verdict application** step 4 for
  each outcome: passed, correction kept, correction not kept or missing, and no
  verifier; `hints` holds every `rotation_differs` and `page_number_differs`
  difference on the kept answer whatever the outcome.
- `AC-012`: the verifier request uses the survey request's attachment; with a
  usable recorded upload, the run makes no upload call.
- `AC-013`: `pdf_survey.json` holds the verdict as given, its attempts, whether
  the correction was applied and the checks a rejected correction failed, or
  `verification: null`.
- `AC-014`: the report's survey section shows one of the four verifier texts.
- `AC-015`: each survey verifier request writes one ledger line with
  `step: "survey"`, `agent: "verifier"`, `page_index: null`, the survey's own
  requests write `agent: "surveyor"`, and the survey's reported cost sums both.
- `AC-016`: each survey verifier request's bound counts the PDF's tokens and
  passes `SpendGuard` before it is sent.
- `AC-017`: a failed verifier request after the provider retries ends the run
  `failed` with a `ProviderError` or `SurveyError` carrying the provider's or
  model's message, the CLI exits 1, and no new `pdf_survey.json` is written.
- `AC-018`: with `verify_extraction` off, each page makes extractor requests
  only and keeps the extractor's answer.
- `AC-020`: `PageFile.verification` is `null` exactly when no verifier ran, and
  the report and the page's log line then say no verifier ran.
- `AC-021`: `load()` leaves out every page file whose `inputs.pdf_sha256`
  differs from the facts' PDF hash.
- `AC-022`: a header cell whose `row_span` passes `header_rows` leaves every
  body cell in the column the page file gives it.
- `AC-023`: an outline with a `First` or `Next` link to an object number past
  the PDF's objects gives every bookmark reachable without that link, in reading
  order, with no blank entry for the missing object and no probe error; with a
  cycle after the link, the bookmarks are the same as without the cycle.
- `AC-024`: a PDF with an inline widget keeps its other form fields, with one
  `form` probe error for the inline one.
- `AC-025`: the `TEXT_FLAGS` comment names the CropBox.
- `AC-041`, `AC-042`: against the commit before the reorder, each reordered file
  has the same multiset of non-blank lines, each module the same multiset of
  top-level statements (`ast.dump`), each class the same members, and every
  Pydantic model, dataclass and enum the same fields or members in the same
  order; every module follows **Module order** except for the departures the
  development record or the verification report lists; `pytest` and the doctests
  collect and pass the same tests, and `ruff check`, `ruff format --check`,
  `ty check` and `interrogate` report what they did before, on Python 3.13,
  which evaluates annotations when it defines a function or class, and on 3.14.
  `AC-041` holds this for `src/pydelity/` and `scripts/` with the tests
  unchanged; `AC-042` for `tests/` with the package already reordered.
- `AC-043`: the extraction model's, the page verifier's and both survey requests
  introduce the measured facts and the survey's findings as hints that the
  model's reading overrides; no system message, user message or retry message
  tells the model to change its answer to match one; every hint difference
  message follows **Checks and hints**.
- `AC-044`: both steps' output validators raise `ModelRetry` only when
  `run_checks` finds a failure; an answer or correction whose only differences
  are hints is accepted on that attempt; no hint difference raises an error or
  sets a page, step or run status.
- `AC-045`: the extraction model's request holds the page text sections and the
  image only, its stored text limited to the repeated lines and the form fields'
  values; none of its retry messages holds a text-layer line.
- `AC-046`: with `verify_extraction` on, the verifier's user message has one
  line per hint difference of the reviewed answer after the hints heading, a
  `text_dropped` line quoting its stored line, and `none` when there is none.
- `AC-047`: a correction with no `run_checks` failure is kept whatever its hint
  differences; one with a check failure is not.
- `AC-048`: a page's `issues` follow **Page extraction without a verifier** for
  each outcome: no verifier, passed, correction kept, correction not kept or
  missing; `hints` holds every hint difference on the kept answer whatever the
  outcome.
- `AC-049`: a kept answer, of the survey or a page, still failing a check is
  written with each failure in `checks` and `issues`, and the step goes on; the
  step fails only on the errors decision 14 names.
- `AC-054`: the page text lists each repeated line with its stored text and the
  survey's finding under a heading that calls them hints; no prompt text tells
  the model to put a repeated line in an item with role `artifact`.

## Build Plan

1. **Reorder every module** (`AC-041`, then `AC-042`). MODIFY every Python
   module in `src/pydelity/` and `scripts/` (Developer) and in `tests/`
   (Tester), and the generated `docs/src/content/docs/reference/` pages if
   `just docs-reference` changes them. Record the checks' results before the
   reorder first, so "the same results" has a baseline. Nothing else changes in
   this step. With the `INCREMENTAL` verification cadence, which the user
   chooses with Developer, this step is the first increment, so Tester reorders
   the tests and confirms the results before step 2 starts; with
   `AFTER_IMPLEMENTATION`, Tester reorders the tests first when its turn comes.
2. **Settings and switches** (`AC-001` to `AC-004`). MODIFY
   `src/pydelity/config/schemas.py`, `src/pydelity/cli.py`,
   `examples/config.json`, `examples/config.yaml`. Names approved by the user
   first. Depends on 1.
3. **Page extraction with an optional verifier** (`AC-005`, `AC-006`, `AC-018`,
   `AC-020` for pages). MODIFY `src/pydelity/extracting/extraction.py`,
   `src/pydelity/extracting/llm.py`, `src/pydelity/extracting/schemas.py`,
   `src/pydelity/costs/budget.py`, `src/pydelity/costs/schemas.py`,
   `src/pydelity/report/html.py`, `src/pydelity/pipeline/runner.py` (estimate
   lines). Depends on 2.
4. **The survey's verifier** (`AC-005` to `AC-017` for the survey). MODIFY
   `src/pydelity/surveying/schemas.py`, `prompts.py`, `agents.py`, `llm.py`,
   `survey.py`, `src/pydelity/review.py`,
   `src/pydelity/providers/ledger_model.py`, `src/pydelity/costs/budget.py`,
   `src/pydelity/costs/schemas.py`, `src/pydelity/pipeline/runner.py`,
   `src/pydelity/report/html.py`. Depends on 2 and on 3's
   `StepEstimate.verifier`. This is the critical path.
5. **Remaining fixes** (`AC-021` to `AC-025`). MODIFY
   `src/pydelity/pipeline/runner.py`, `src/pydelity/pipeline/schemas.py`
   (docstring), `src/pydelity/report/html.py`,
   `src/pydelity/surveying/probe.py`, `src/pydelity/utils/pdf.py`. Depends on 1
   only; may go before 2–4.
6. **Docstrings, references and package text** (`AC-030`, `AC-033` in code).
   MODIFY `scripts/generate_reference_docs.py` (only if the survey's `verifier`
   issue name is not picked up by itself), `pyproject.toml` (description);
   regenerate `docs/src/content/docs/reference/` with `just docs-reference`.
   After 2–5.
7. **Hints** (`AC-043` to `AC-049`, `AC-054`, and `AC-051`, `AC-052` in code).
   MODIFY `src/pydelity/review.py`, `src/pydelity/extracting/validators.py`,
   `agents.py`, `llm.py`, `prompts.py`, `extraction.py`, `schemas.py`,
   `text_layer.py` (docstring), `src/pydelity/surveying/validators.py`,
   `prompts.py`, `llm.py`, `survey.py`, `schemas.py`, `agents.py` (docstring),
   `scripts/generate_reference_docs.py`; regenerate
   `docs/src/content/docs/reference/` with `just docs-reference`. The split of
   the names, the validators, the agents, the keep rule, the `hints` fields and
   the review lists change together in one step, since each depends on the
   others to build and pass the checks; the prompt text may follow in a step of
   its own. Depends on 3 and 4.

New and changed code in steps 2–7 follows **Module order** as it is written.
Tests are Tester's, the docs guides, README and `artifacts/next_cycle_inputs.md`
are Documenter's.

## Risks and Follow-up

- A verified survey pays for the PDF about twice (decision 6). The 6,000-token
  typical verdict is a guess the real runs will check.
- A verifier request that fails after a paid survey answer makes the next run
  pay for the survey request again (decision 10).
- Turning a verifier off keeps outputs it reviewed until another input changes;
  `overwrite` redoes them without it. This is by design (decision 2), and the
  docs should say so.
- With the verifiers off, pages whose stored text is wrong, such as the Arabic
  and Japanese test pages, put their text differences back on the review list,
  and nothing catches missed or merged items, a wrong reading order or boxes on
  the wrong content beyond the code checks. The scope accepts this.
- No hint sends an answer back now, so dropped or added text, uncovered page
  furniture, a field value the model misread and a reading order against the
  page's direction are no longer retried. With the verifier off, they reach the
  user only through the review list. Since the prompt no longer asks for
  furniture lines in artifact items, models may give fewer artifact items, and
  each missing one is an `artifacts` review issue. The real runs show how many.
- What stops working: every page file and `pdf_survey.json` written before this
  change lacks `hints` and is made again with the `damaged_output` warning, so a
  run on an older output folder pays for the survey and every selected page
  again. Code that reads `PageFile.checks` for `text_dropped`, `text_added`,
  `artifacts`, `form_fields` or `reading_order` finds them in `hints` instead,
  and `TEXT_CHECKS`, `compare_with_facts` and `SurveyComparisonName` are gone.
- A verifier that wrongly passes an answer, or a kept correction that is worse,
  keeps its hint differences off the review list; they are then visible only in
  the output file's `hints`.
- `SurveyVerdict` nests a whole `SurveyAnswer`; OpenAI's native output and
  Anthropic's prompted output have not run it yet. `AC-040`'s real runs will.
- Output folders from earlier runs do not carry over. Their `pdf_survey.json`
  lacks `verification` and is surveyed again (decision 4), and their
  `cost.jsonl` has survey lines with `agent: null`, so it is damaged and runs on
  that folder stop with `OutputError` (decision 8). The real runs use new
  folders.
- `load()` returns no page files for a folder without `pdf_facts.json`.
- For a PDF whose outline links to a missing object, the bookmarks differ from
  0.1.x's: the blank entry is gone, and a missing `First` no longer drops the
  entries that follow its entry at the same level.
- The reorder moves most of the code, so `git blame` points at it for moved
  lines; `git blame --ignore-rev` with its commit, or a `.git-blame-ignore-revs`
  file the user may add, hides it.
- Python 3.13 evaluates annotations when it defines a function or class, and
  3.14 does not, so a move that breaks import may pass on 3.14 alone. No private
  definition annotates a public class of its own module today, so no departure
  is expected from that cause; the checks run on 3.13 first.

## Alternatives

- Putting the verifier switch in each fingerprint, so any change reruns the
  step: rejected, because turning a verifier off would pay to redo reviewed
  outputs, and every default run after a verified one would rerun the survey and
  every page.
- Running only the verifier on a saved output when it is turned on: rejected.
  `pdf_survey.json` and page files hold what was built from the answer (regions
  in points, labels merged, boxes mapped), not the answer, so this would need
  the raw answers saved and a second path; the scope's real runs rerun anyway.
- A shared verifier module for both steps: not now; the keep rules differ, and
  each step keeps its own split. A later step may revisit it.
- Giving the survey verifier the survey's instructions so the PDF is read from
  the cache: not possible while each request's output schema is part of the
  cached prefix (decision 6).
- Keeping `agent: null` for the survey's own requests: rejected; it would make
  the survey the one step whose requests name no agent, only so that older
  ledgers keep loading.
- Saving the unverified survey when its verifier request fails: rejected; it
  would not be reused while the verifier is on.
- One `checks` list with a flag on each hint's result: rejected. Hints have no
  attempts, and the review list treats them apart, so separate lists show the
  rule in the file itself.
- Sending hint differences back with softer wording, or only beside a check
  failure: rejected. Either still asks the model to look at its answer against a
  hint, which is what merged the grade cells.
- Leaving the writing direction stated as a fact while `reading_order` is a
  hint: rejected. A page the survey got wrong would be read against its own
  direction, and the hint would then flag the correct reading.

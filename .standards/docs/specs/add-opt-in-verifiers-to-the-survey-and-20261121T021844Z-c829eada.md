<!-- STANDARDS
Artifact: ARCHITECTURE
Cycle: add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada
-->

# Technical Design: opt-in verifiers, the survey's verifier, and page extraction's remaining fixes

## Context

- Scope:
  `.standards/docs/scope/add-opt-in-verifiers-to-the-survey-and-20261121T021844Z-c829eada.md`
  (`AC-001` to `AC-042`). Target maturity is Level 3. Architect mode: feature.
  Its first work item, `AC-041` and `AC-042`, reorders every Python module to
  the ordering rule of the developer and tester user styles before the other
  work changes them.
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
- Constraints that shape this design: the model's reading is trusted over
  measured facts, and a difference left goes on the review list unless the
  step's verifier passed the answer or its correction was kept; checks sit in
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
3. **A run that no verifier reviewed lists every difference it leaves.** With a
   step's verifier off, the producer's answer goes through the checks and their
   retries and is kept, and no verifier request is made. Every check still
   failing goes on the review list, page extraction's `text_dropped` and
   `text_added` included, and so do the survey's comparisons with the facts
   (`rotation_differs`, `page_number_differs`). With the verifier on, a
   difference is left off the review list when the verdict passed or its
   correction was kept; other failing checks are always listed. This extends
   page extraction's decision 9 to pages with no verifier and applies the same
   rule to the survey's comparisons. The differences stay recorded either way:
   page extraction's in the page file's `checks`, the survey's in the facts and
   profile that `pdf_survey.json` holds.
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
   kept only when it passes every survey check: none of C1–C7 compares with
   stored text, so the survey has no counterpart of page extraction's text-check
   exception. `passed`: keep the answer. Problems with a kept correction: keep
   the correction; the problems stay in the verdict only. Otherwise: keep the
   answer, and each problem becomes a `verifier` review issue of the survey. No
   loop back to the survey request and no second verification. The profile and
   proposal are then built from the kept answer by the existing `build_survey`
   rules, so the user's languages stay first and the facts copy is untouched
   (`AC-008`).
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
   differences from the measured facts (one line per `rotation_differs` or
   `page_number_differs` issue message, or `none`). This work needs no change to
   what `survey_pdf`'s messages say; Developer may move the rule text both
   prompts share into sections of its own. `PROMPT_VERSION` stays 1, as the
   scope says, and covers both prompts.
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
    report renders a table's rows in one row group, the outline walk stops at
    links to objects the PDF does not have, the form reader skips inline widgets
    with a probe error, and the `TEXT_FLAGS` comment names the CropBox. Details
    under **Remaining fixes**.
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
- `AC-011`: decision 3, **Survey verdict application**.
- `AC-012`: decision 6.
- `AC-013`: decision 4, **`pdf_survey.json`**.
- `AC-014`: decision 4, **HTML report**.
- `AC-015`: decision 8, **`cost.jsonl`**.
- `AC-016`: decisions 8 and 9.
- `AC-017`: decision 10.
- `AC-018`: decision 3, **Page extraction without a verifier**.
- `AC-019`: decision 3, **Page extraction without a verifier**.
- `AC-020`: decision 4, **Page file**, **HTML report**.
- `AC-021`: **Remaining fixes** (`load()`).
- `AC-022`: **Remaining fixes** (report tables).
- `AC-023`: **Remaining fixes** (outline links).
- `AC-024`: **Remaining fixes** (inline widgets).
- `AC-025`: **Remaining fixes** (`TEXT_FLAGS`).
- `AC-026`: **Test seams** define the contracts the tests rely on; writing and
  running the tests is Tester's.
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
  code's names and docstrings); the guide pages are Documenter's.
- `AC-034`: **Docs and docstrings** (the `prompts.py` and `text_layer.py`
  docstrings); the guides and FAQ are Documenter's.
- `AC-038`: No architectural impact — Documenter's update to
  `artifacts/next_cycle_inputs.md`; decision 1 is what it records for later
  steps.
- `AC-039`, `AC-040`: No architectural impact — the user's review of real runs
  after the build, made with the default settings and with `verify` on.
- `AC-041`: decision 13, **Module order** (`src/pydelity/` and `scripts/`, by
  Developer).
- `AC-042`: decision 13, **Module order** (`tests/`, `conftest.py` files
  included, by Tester).

## Components

- **Settings** (`config/schemas.py`): `Config.verify`, `SurveyConfig.verify`,
  `ExtractionConfig.verify`, the resolved properties `verify_survey` and
  `verify_extraction`.
- **CLI** (`cli.py`): `--verify`/`-vf`.
- **Survey step** (`surveying/`): the verifier's schemas, prompt, agent and
  request (decision 11); `survey.py` applies the verdict, builds the review
  list, and adds the verification rule to `saved_survey`.
- **Page extraction step** (`extracting/extraction.py`, `extracting/llm.py`,
  `extracting/schemas.py`): the verifier made optional in the page task, the
  kept-answer and review-list rules with no verdict, the reuse rule in
  `plan_pages`, the log line.
- **Review** (`review.py`): `verifier` shared by both steps.
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
   `rotation_differs` and `page_number_differs` from `compare_with_facts` on the
   kept answer, unless `verification` is set and the verdict passed or its
   correction was applied; then, when a verdict was given and its correction was
   not applied, one issue per problem: `step: "survey"`, `check: "verifier"`,
   `message: "verifier: <description>"`, `details: {"category": <category>}`,
   `page_index` from the problem, `item_id: null`.
5. The survey's log line adds the verifier's outcome: `passed`,
   `corrected the survey`, `found <n> problems`, or `no verifier`.

### `pdf_survey.json`

- `verification: SurveyVerification | None` (required): the verifier's review;
  `null` when no verifier ran.
- `issues` docstring: checks still failing on the kept answer, differences from
  the facts unless the verifier passed the answer or its correction was kept,
  and the verifier's problems when its correction was not kept.
- `checks` docstring: the kept answer's checks, the survey's or the verifier's
  correction.
- No new input field: `verification` tells whether a verifier ran (decision 2).

### Page extraction without a verifier

- `StepModel` (or the page task) carries `verify_extraction`. With it off, the
  page task runs the extractor and keeps its answer; `_kept_answer` takes no
  verdict and sets `verification` to `null`.
- `_page_issues`: text checks are left out only when `verification` is set and
  the verdict passed or the correction was applied; `verifier` issues are added
  only when `verification` is set and the correction was not applied.
- `plan_pages` reuses a page file only under decision 2's rule.
- Log line: `verifier <outcome>` becomes `no verifier` when none ran.
- `request_sizes` and `request_sizes_before_survey` keep measuring the
  verifier's text; `estimate_extraction` prices it only when the verifier is on.

### Page file

- `verification: PageVerification | None` (required): the verifier's review;
  `null` when no verifier reviewed the page.
- `issues` docstring: text differences are listed unless the verifier passed the
  page or its correction was applied, so every one is listed on a page no
  verifier reviewed.

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
  `xref_length() - 1`) is not followed, and the walk carries on with the links
  left, so PyMuPDF's `get_toc` reads the outline as it did before the cycle cut
  existed. Developer confirms which PyMuPDF calls raise on such a number.
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
- Docstrings that say pydelity sends none of the PDF's stored text
  (`extracting/prompts.py`, `extracting/text_layer.py`) say what is sent: the
  page's repeated lines with their stored text and its form fields, and stored
  lines quoted in text retry messages.

### Test seams

- The survey verifier's user message contains the line
  `The survey answer to review:`, so the stand-in provider can route a survey
  verifier request to a queued survey verdict, apart from queued survey answers.
  Page requests keep their existing markers.
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
   `verify_survey` is on, the verifier request on the same attachment with
   checks on its correction; apply the verdict; build the profile, proposal,
   checks and issues from the kept answer; write `pdf_survey.json` atomically. A
   failed verifier request ends the step `failed` with nothing written (decision
   10).
3. Pause after a new survey, as now.
4. Page extraction: plan pages under decision 2's rule; estimate when the survey
   was reused; per page, render, read the text layer, run the extractor; when
   `verify_extraction` is on, run the verifier and apply its verdict; build
   issues under decision 3; write crops and the page file; log the outcome.
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
  verifier.
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
- `AC-019`: with no verifier, every failing check, `text_dropped` and
  `text_added` included, is a review issue; with a verifier, the existing rules
  hold unchanged.
- `AC-020`: `PageFile.verification` is `null` exactly when no verifier ran, and
  the report and the page's log line then say no verifier ran.
- `AC-021`: `load()` leaves out every page file whose `inputs.pdf_sha256`
  differs from the facts' PDF hash.
- `AC-022`: a header cell whose `row_span` passes `header_rows` leaves every
  body cell in the column the page file gives it.
- `AC-023`: an outline with a link to an object number past the PDF's objects
  gives the bookmarks `get_toc` can read, not an empty list.
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
3. **Page extraction with an optional verifier** (`AC-005`, `AC-006`, `AC-018`
   to `AC-020` for pages). MODIFY `src/pydelity/extracting/extraction.py`,
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
6. **Docstrings, references and package text** (`AC-030`, `AC-033`, `AC-034` in
   code). MODIFY `scripts/generate_reference_docs.py` (only if the survey's
   `verifier` issue name is not picked up by itself),
   `src/pydelity/extracting/prompts.py`, `src/pydelity/extracting/text_layer.py`
   (docstrings), `pyproject.toml` (description); regenerate
   `docs/src/content/docs/reference/` with `just docs-reference`. After 2–5.

New and changed code in steps 2–6 follows **Module order** as it is written.
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
- A verifier that wrongly passes an answer, or a kept correction that is worse,
  keeps its differences off the review list; the survey's are then visible only
  by comparing the profile with the facts in `pdf_survey.json`.
- `SurveyVerdict` nests a whole `SurveyAnswer`; OpenAI's native output and
  Anthropic's prompted output have not run it yet. `AC-040`'s real runs will.
- Output folders from earlier runs do not carry over. Their `pdf_survey.json`
  lacks `verification` and is surveyed again (decision 4), and their
  `cost.jsonl` has survey lines with `agent: null`, so it is damaged and runs on
  that folder stop with `OutputError` (decision 8). The real runs use new
  folders.
- `load()` returns no page files for a folder without `pdf_facts.json`.
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

---
title: Review answers with a verifier
description:
  Turn on a verifier for every step or for one step, see what it reviews and
  costs, and read what it found.
---

A verifier is a second request to a step's own model. It reviews the step's
answer against the PDF after the code checks, and looks for mistakes that code
can't find. It either passes the answer or lists the problems it found, usually
with a corrected answer. The survey and page extraction each have one.

Verifiers are off by default, because each verifier request costs money. Without
one, a step checks its answers with code only, and every difference from what
pydelity measured goes on the review list for a person to check.

## Turn the verifiers on

The `verify` setting turns on the verifier of every step:

```sh
pydelity document.pdf --verify
```

```yaml
# In a config file
verify: true
```

```python
import pydelity

result = await pydelity.arun("document.pdf", verify=True)
```

`-vf` is the short form of `--verify`. Without `--verify`, the command uses the
config file's `verify`, or `false` when the file doesn't set it.

To turn one step's verifier on or off whatever `verify` is, set
`advanced.survey.verify` or `advanced.extraction.verify` to `true` or `false`.
When one is unset (`null`), that step follows `verify`. These two settings go in
a config file or come from Python, with no command-line option:

```yaml
# Review the survey only.
advanced:
  survey:
    verify: true
```

```yaml
# Review every page, but not the survey.
verify: true
advanced:
  survey:
    verify: false
```

```python
import pydelity

# Review every page, but not the survey.
result = await pydelity.arun(
    "document.pdf", advanced={"extraction": {"verify": True}}
)
```

A verifier uses its step's model and settings. The survey's verifier uses the
survey's model and the `advanced.survey` settings, and page extraction's uses
page extraction's model and the `advanced.extraction` settings. Each step's
`instructions`, `effort`, `max_output_tokens`, `request_timeout_seconds` and
`check_retries` apply to its verifier too.

## What each verifier reviews

**The survey's verifier** gets the whole PDF again, with the survey's answer,
the [survey checks](../../reference/survey-checks/) the answer still fails and
its differences from the measured facts. It looks for:

- labels that don't fit their content, content that no label fits, and labels
  that should be one
- regions on the wrong area of a page or with the wrong label
- page furniture, such as running headers, given as content, and content given
  as page furniture
- pages that aren't upright when turned as the survey's rotation says
- page numbering that differs from the numbers printed on the pages
- a wrong writing direction, and languages that are missing, not in the PDF or
  out of order
- wrong or missing notes on how content continues across pages
  (`continuation_notes`) and markers of where new units of content start
  (`start_markers`)

It may correct any part of the survey's answer. The measured facts never change,
and the languages you set with `languages` stay first in the profile.

**Page extraction's verifier** gets the page image, the extraction and the
[page extraction checks](../../reference/extraction-checks/) it still fails. It
looks for a missed or merged item, a misread word, a wrong reading order on a
complex page and a box on the wrong content.

## What the verdict changes

- **The verifier passes the answer.** pydelity keeps the answer.
- **It finds problems and gives a correction.** The correction goes through the
  step's code checks. When it fails one, it goes back to the verifier with the
  problems listed, up to `check_retries` times. pydelity keeps the correction
  when it passes every check. On a page, the comparison with the PDF's stored
  text doesn't count here, because stored text can be wrong. The problems the
  verifier found then stay in its verdict, and none goes on the review list.
- **It finds problems and gives no correction, or its correction still fails the
  checks after the retries.** pydelity keeps the step's own answer and puts each
  problem on the review list as a `verifier` issue.

A kept correction is not reviewed again.

## The review list with and without a verifier

Which issues go on the review list depends on whether a verifier ran and what it
decided:

| Issue                                                                                        | No verifier | Passed, or correction kept | Problems, correction not kept |
| -------------------------------------------------------------------------------------------- | ----------- | -------------------------- | ----------------------------- |
| A survey check that the kept answer still fails                                              | Listed      | Listed                     | Listed                        |
| The survey's differences from the measured facts (`rotation_differs`, `page_number_differs`) | Listed      | Not listed                 | Listed                        |
| A page check that the kept answer still fails, other than the text comparison                | Listed      | Listed                     | Listed                        |
| A page's lines dropped or added compared with its stored text (`text_dropped`, `text_added`) | Listed      | Not listed                 | Listed                        |
| Each problem the verifier found (`verifier`)                                                 | —           | Not listed                 | Listed                        |

A difference left off the list is still saved. A page's text differences stay in
its page file's `checks`, and the survey's show when you compare the profile
with the facts in `pdf_survey.json`.

[The review list](../outputs/#the-review-list) describes each kind of issue.

## What a verifier costs

Each verifier adds at least one request: one for the survey, and one for each
page it reviews. The survey's verifier sends the whole PDF again, so a reviewed
survey costs about twice as much as one without. Retries to fix a failing
correction add more.

The cost estimate includes a step's verifier when it will run, and names it. For
a 2-page scanned form with the default model, the survey's estimate without a
verifier was about $0.24, at most $2.53, and with one:

```text
Survey with its verifier cost estimate: about $0.47, at most $5.45 (up to 6 requests to anthropic:claude-opus-5-5)
```

Page extraction's estimate for both pages was about $0.23, at most $4.81, and
with its verifier:

```text
Extraction with its verifier cost estimate: about $0.45, at most $10.41 (2 pages, up to 12 requests to anthropic:claude-opus-5-5)
```

`pydelity.aestimate` gives the same figures without an API key, and each step's
`verifier` field says whether its figures include the verifier. `max_cost`
covers verifier requests like any other. See [Control costs](../costs/).

## Read what the verifier found

- **The report.** The survey's section and each extracted page's details have a
  "Verifier" line: `passed`, such as
  `found 2 problems and its correction was kept` or
  `found 2 problems, listed for review`, or `no verifier ran`.
- **The command's log.** With `--verbose`, the survey's line and each page's
  line give the outcome: `verifier passed`, `verifier corrected the survey` (or
  `verifier corrected the extraction` on a page), such as
  `verifier found 2 problems`, or `no verifier`.
- **The output files.** `verification` in `pdf_survey.json` and in each page
  file is `null` when no verifier ran. Otherwise it holds the verdict as the
  verifier gave it (`passed`, the `problems` it found and any `corrected`
  answer), whether the correction was kept (`correction_applied`), the checks a
  correction that wasn't kept still failed (`correction_failures`) and how many
  verdicts it took (`attempts`). This lets you count how often the verifier
  passes answers, finds problems and has its corrections kept.
- **The costs.** Each line of `cost.jsonl` names the request's `agent`:
  `surveyor` or `verifier` for the survey, and `extractor` or `verifier` for
  page extraction. A step's cost in `run.json` includes its verifier.

The [pdf_survey.json](../../reference/pdf-survey-json/#verification) and
[page file](../../reference/page-json/#verification) references list every field
of `verification`.

## Turn a verifier on or off later

Turning a step's verifier on redoes that step's saved outputs that no verifier
reviewed: the survey, or each selected page whose page file has no verification.
With `--verbose`, the command says so for each one. Outputs a verifier already
reviewed are reused as usual.

Turning a verifier off keeps the outputs it reviewed, which costs nothing. To
make them again without the verifier, use `overwrite`. See
[Redo everything](../reruns/#redo-everything).

A verifier setting is not one of the inputs that decide when a survey or page is
reused, so changing page extraction's verifier never redoes the survey. When the
survey's verifier redoes the survey, only the pages whose inputs the new survey
changed are extracted again. See
[What gets reused](../reruns/#what-gets-reused).

## When a verifier request fails

A verifier request fails in the same ways as the step's own request: a provider
error that lasts through the retries, a timeout, a refusal, an answer that runs
out of output tokens, or no verdict in the form pydelity expects. The run stops.
The command shows the error and exits with code 1, and in Python the error is a
`ProviderError`, `SurveyError` or `ExtractionError`.

When the survey's verifier fails, pydelity saves no new `pdf_survey.json` and
leaves an existing one as it was. The upload is kept for the next run, which
pays for the survey request again. When a page's verifier fails, the page fails
as described in
[When page extraction fails](../models-and-providers/#when-page-extraction-fails).

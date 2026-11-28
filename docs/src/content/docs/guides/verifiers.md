---
title: Review answers with a verifier
description:
  Turn on a verifier for every step or for one step, see what it reviews and
  costs, and read what it found.
---

A verifier is a second request to a step's own model. It reviews the step's
answer against the PDF after the code checks, and looks for mistakes that code
can't find. It either passes the answer or lists the problems it found, usually
with a corrected answer. The survey, page extraction and page-break verification
each have one.

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
`advanced.survey.verify`, `advanced.extraction.verify` or
`advanced.page_breaks.verify` to `true` or `false`. When one is unset (`null`),
that step follows `verify`. These settings go in a config file or come from
Python, with no command-line option:

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

```yaml
# Review every page break only.
advanced:
  page_breaks:
    verify: true
```

```python
import pydelity

# Review every page, but not the survey or the page breaks.
result = await pydelity.arun(
    "document.pdf", advanced={"extraction": {"verify": True}}
)
```

A verifier uses its step's model and settings. The survey's verifier uses the
survey's model and the `advanced.survey` settings, page extraction's uses page
extraction's model and the `advanced.extraction` settings, and page-break
verification's uses that step's model and the `advanced.page_breaks` settings.
Each step's `instructions`, `effort`, `max_output_tokens`,
`request_timeout_seconds` and `check_retries` apply to its verifier too.

## What each verifier reviews

**The survey's verifier** gets the whole PDF again, with the survey's answer,
the [survey checks](../../reference/survey-checks/) the answer still fails and
its differences from the measured facts. The measured facts are hints that can
be wrong, so a difference is a problem only when the PDF shows the answer is
wrong. It looks for:

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

**Page extraction's verifier** gets the page image, the extraction, the
[page extraction checks](../../reference/extraction-checks/) it still fails and
its differences from the page's hints, quoting the stored lines a text
difference is about. It looks for a missed or merged item, a misread word, a
wrong reading order on a complex page and a box on the wrong content. The page
image decides whether a difference from a hint is a problem.

**Page-break verification's verifier** gets the break's two page images and
their items, the verdict, the
[page-break checks](../../reference/page-break-checks/) the verdict still fails
and its differences from the survey's start markers. It looks for content that
continues but is missing from the verdict, a piece that doesn't continue, the
wrong end or start of a piece, the wrong join or text join, a wrong count of
repeated header rows, and repeated items, markers or containers that are missing
or wrong. The pages decide whether a difference from the hint is a problem.

## What the verdict changes

- **The verifier passes the answer.** pydelity keeps the answer.
- **It finds problems and gives a correction.** The correction goes through the
  step's code checks. When it fails one, it goes back to the verifier with the
  failed checks listed, up to `check_retries` times. pydelity keeps the
  correction when it passes every check, whatever its differences from the
  hints. The problems the verifier found then stay in its verdict, and none goes
  on the review list.
- **It finds problems and gives no correction, or its correction still fails the
  checks after the retries.** pydelity keeps the step's own answer and puts each
  problem on the review list as a `verifier` issue.

A kept correction is not reviewed again.

## The review list with and without a verifier

Which issues go on the review list depends on whether a verifier ran and what it
decided:

| Issue                                                                                                           | No verifier | Passed, or correction kept | Problems, correction not kept |
| --------------------------------------------------------------------------------------------------------------- | ----------- | -------------------------- | ----------------------------- |
| A check that the kept answer still fails, in the survey, on a page or at a page break                           | Listed      | Listed                     | Listed                        |
| The survey's differences from the measured facts (`rotation_differs`, `page_number_differs`)                    | Listed      | Not listed                 | Listed                        |
| A page's differences from its hints (`reading_order`, `artifacts`, `form_fields`, `text_dropped`, `text_added`) | Listed      | Not listed                 | Listed                        |
| A page break's differences from the survey's start markers (`start_markers`)                                    | Listed      | Not listed                 | Listed                        |
| Each problem the verifier found (`verifier`)                                                                    | —           | Not listed                 | Listed                        |

A difference left off the list is still saved, in the `hints` of
`pdf_survey.json`, the page file or the verdict file. A difference from a hint
never sends an answer or a correction back, with or without a verifier. See
[How a page is checked](../page-extraction/#how-a-page-is-checked).

[The review list](../outputs/#the-review-list) describes each kind of issue.

## What a verifier costs

Each verifier adds at least one request: one for the survey, one for each page
it reviews and one for each page break it reviews. The survey's verifier sends
the whole PDF again, so a reviewed survey costs about twice as much as one
without. Retries to fix a failing correction add more.

The cost estimate includes a step's verifier when it will run, and names it. For
a 2-page scanned form with the default model, the survey's estimate without a
verifier was about $0.24, at most $2.53, and with one:

```text
Survey with its verifier cost estimate: about $0.47, at most $5.46 (up to 6 requests to anthropic:claude-opus-5-5)
```

Page extraction's estimate for both pages was about $0.23, at most $4.81, and
with its verifier:

```text
Extraction with its verifier cost estimate: about $0.46, at most $10.42 (2 pages, up to 12 requests to anthropic:claude-opus-5-5)
```

Page-break verification's line names its verifier the same way, as
`Page-break verification with its verifier cost estimate`, and counts breaks in
place of pages.

`pydelity.aestimate` gives the same figures without an API key, and each step's
`verifier` field says whether its figures include the verifier. `max_cost`
covers verifier requests like any other. See [Control costs](../costs/).

## Read what the verifier found

- **The report.** The survey's section, each extracted page's details and each
  page break's card have a "Verifier" line: `passed`, such as
  `found 2 problems and its correction was kept` or
  `found 2 problems, listed for review`, or `no verifier ran`.
- **The command's log.** With `--verbose`, the survey's line, each page's line
  and each page break's line give the outcome: `verifier passed`,
  `verifier corrected the survey` (or `verifier corrected the extraction` on a
  page and `verifier corrected the verdict` at a break), such as
  `verifier found 2 problems`, or `no verifier`.
- **The output files.** `verification` in `pdf_survey.json`, in each page file
  and in each verdict file is `null` when no verifier ran. Otherwise it holds
  the verdict as the verifier gave it (`passed`, the `problems` it found and any
  `corrected` answer), whether the correction was kept (`correction_applied`),
  the checks a correction that wasn't kept still failed (`correction_failures`)
  and how many verdicts it took (`attempts`). This lets you count how often the
  verifier passes answers, finds problems and has its corrections kept.
- **The costs.** Each line of `cost.jsonl` names the request's `agent`:
  `surveyor` or `verifier` for the survey, `extractor` or `verifier` for page
  extraction, and `judge` or `verifier` for page-break verification. A step's
  cost in `run.json` includes its verifier.

The [pdf_survey.json](../../reference/pdf-survey-json/#verification),
[page file](../../reference/page-json/#verification) and
[verdict file](../../reference/page-break-json/#verification) references list
every field of `verification`.

## Turn a verifier on or off later

Turning a step's verifier on redoes that step's saved outputs that no verifier
reviewed: the survey, each selected page whose page file has no verification, or
each page break whose verdict file has none. A break with no request, because a
page of it has no content items, is not judged again. With `--verbose`, the
command says so for each one. Outputs a verifier already reviewed are reused as
usual.

Turning a verifier off keeps the outputs it reviewed, which costs nothing. To
make them again without the verifier, use `overwrite`. See
[Redo everything](../reruns/#redo-everything).

A verifier setting is not one of the inputs that decide when a survey, page or
page break is reused, so changing page extraction's verifier never redoes the
survey. When the survey's verifier redoes the survey, only the pages whose
inputs the new survey changed are extracted again. In the same way, a page
extracted again with its verifier has the two breaks next to it judged again,
and changing page-break verification's verifier redoes neither the survey nor
any page. See [What gets reused](../reruns/#what-gets-reused).

## When a verifier request fails

A verifier request fails in the same ways as the step's own request: a provider
error that lasts through the retries, a timeout, a refusal, an answer that runs
out of output tokens, or no verdict in the form pydelity expects. The run stops.
The command shows the error and exits with code 1, and in Python the error is a
`ProviderError`, `SurveyError`, `ExtractionError` or `PageBreakError`.

When the survey's verifier fails, pydelity saves no new `pdf_survey.json` and
leaves an existing one as it was. The upload is kept for the next run, which
pays for the survey request again. When a page's verifier fails, the page fails
as described in
[When page extraction fails](../models-and-providers/#when-page-extraction-fails),
and when a page break's verifier fails, the break fails as described in
[When page-break verification fails](../models-and-providers/#when-page-break-verification-fails).

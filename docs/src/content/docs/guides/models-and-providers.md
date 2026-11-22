---
title: Models and providers
description:
  Choose an Anthropic or OpenAI model for each step, and learn what pydelity
  sends, how long the provider keeps your PDF and what happens when a request
  fails.
---

pydelity works with models from Anthropic and OpenAI. You pick one with the
`model` setting, written as `<provider>:<model-id>`.

## Choose a model

Both the survey and page extraction use `anthropic:claude-opus-5-5` by default.
To use an OpenAI model, name it with the `openai:` prefix:

```sh
pydelity document.pdf --model openai:gpt-6.2-astra
```

```python
import pydelity

result = await pydelity.arun("document.pdf", model="openai:gpt-6.2-astra")
```

`model` sets the model for every step. To use a different model for page
extraction only, set `advanced.extraction.model` in a config file or from
Python. Page extraction then uses it in place of `model`, and the survey still
uses `model`:

```yaml
model: anthropic:claude-opus-5-5
advanced:
  extraction:
    model: openai:gpt-6.2-astra
```

pydelity sends the model ID to the provider exactly as you give it. It keeps no
list of models, so you can use any model ID your provider accepts. The survey's
model must read PDFs, page extraction's must read images, and both must support
the `effort` setting (`advanced.survey.effort` and
`advanced.extraction.effort`). An older model that doesn't fails with the
provider's error.

Each provider needs its own API key: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`. A
run that uses both providers needs both keys. See
[Set your API key](../../start/install/#set-your-api-key).

## What is sent to the provider

For the survey, pydelity sends the provider:

- the PDF itself
- pydelity's instructions for the survey
- a plain-text summary of what it measured in the PDF, and the repeated lines it
  found, given as hints that the PDF itself overrides
- your `languages` and `advanced.survey.instructions`, if you set them

With the survey's verifier on, a second request sends the same PDF again, with
the survey's answer, the checks it still fails and its differences from the
measured facts.

For page extraction, each request carries one page:

- an image of the page, turned upright, and how far it was turned
- pydelity's instructions for page extraction, with the labels the survey found
- hints about the page, which the image overrides: the writing direction the
  survey found, the page's repeated lines with their stored text and what the
  survey found each one to be, such as page furniture, and its fillable form
  fields, if it has any, with their stored values
- your `advanced.extraction.instructions`, if you set them
- with page extraction's verifier on, a second request with the extraction to
  review, the checks it still fails and its differences from the hints

Page extraction doesn't send the PDF. Of the text stored in the PDF, it sends
only the page's repeated lines and its form fields' values. The verifier's
request also quotes the stored lines that a text difference is about. No request
asks a model to change its answer to match a hint. Run with `--verbose` to see
the text sent with the survey.

## How long the provider keeps your PDF

pydelity uploads the PDF to your provider account's file storage once for the
survey, then points each survey request at the upload. It records the upload in
`uploads.json` in the output folder, and later runs reuse it while at least an
hour is left before it expires. Page extraction sends its page images inside
each request and uploads nothing.

By default the provider keeps the PDF for as long as it allows:

| Provider  | Kept by default       | `expiry_hours` can be |
| --------- | --------------------- | --------------------- |
| Anthropic | 2,160 hours (90 days) | 1 to 2,160            |
| OpenAI    | 720 hours (30 days)   | 1 to 720              |

To keep it for less time, set `advanced.uploads.expiry_hours` in a config file:

```yaml
advanced:
  uploads:
    # Delete the uploaded PDF from the provider after one day.
    expiry_hours: 24
```

A shorter time means later runs upload the PDF again more often. To remove an
upload sooner, delete it in your provider's console or through its files API,
using the `file_id` in `uploads.json`. Uploads count toward your organization's
file storage with the provider.

If the upload fails, pydelity warns you and sends the PDF inside each survey
request instead, for the rest of the run. Two upload errors stop the run,
because the request would fail the same way: an invalid API key, and a PDF the
provider rejects as too large.

## Large PDFs

pydelity doesn't check a PDF's size or page count against the model's limits,
because those limits change. It sends the PDF and, if the provider rejects it,
shows the provider's error. The command exits with code 1. In Python, the error
is a `ProviderError`, with the provider's own message in `provider_message`.

A rejected request reports no usage, so it adds nothing to `cost.jsonl`. Check
your provider's documentation for its current limits on PDF size and pages.

Page extraction sends one page image at a time, sized to fit both providers'
image limits, so the PDF's length doesn't matter there.

## Failed requests and retries

When a request fails for a temporary reason, such as a dropped connection, a
timeout, a rate limit or a server error, the provider's SDK tries it again.
`advanced.provider_retries` sets how many times, from 0 to 10. The default is 2.
After the last retry, the run fails with a `ProviderError`.

How long pydelity waits for one request is set per step:
`advanced.survey.request_timeout_seconds` (900 seconds by default, which leaves
room for a long PDF) and `advanced.extraction.request_timeout_seconds` (600
seconds by default, for one page).

Page extraction sends up to 8 pages' requests at the same time
(`advanced.extraction.concurrent_pages`). If your provider account has low rate
limits, runs can fail with rate-limit errors after the retries. Lower
`concurrent_pages` to send fewer requests at once.

A request that times out on pydelity's side may still finish at the provider,
and the provider may still bill it. pydelity never sees what such a request
used, so it is missing from `cost.jsonl`. With retries, each timed-out attempt
can add cost of this kind. The same goes for page requests still in flight when
a run stops. If you see timeouts, check your provider's usage page.

## When the survey fails

The survey itself can fail even when every request succeeds:

- The model refuses to answer.
- The answer runs out of output tokens. Raising
  `advanced.survey.max_output_tokens` can help.
- The model never gives an answer in the form pydelity expects.

The same goes for the survey's verifier, when it is on. These raise a
`SurveyError` in Python, and the command exits with code 1, with no new
`pdf_survey.json` saved. An answer that is well formed but fails one of the
[survey checks](../../reference/survey-checks/) is not a failure. pydelity sends
it back to the model with the problems listed, up to
`advanced.survey.check_retries` times, then keeps the last answer and adds each
remaining problem to the review list. A difference from the measured facts is
never sent back and never fails the survey.

## When page extraction fails

A page fails in the same three ways: the model refuses, its answer runs out of
output tokens (raise `advanced.extraction.max_output_tokens`, which includes the
model's thinking), or it never gives an answer in the form pydelity expects. A
provider error that lasts through the retries fails the page too.

When a page fails, the run stops: pages still in progress are canceled and no
new page starts. The command shows the error, which names the page, and exits
with code 1. In Python, the error is an `ExtractionError` or a `ProviderError`.
Page files already written stay saved, and the next run extracts only the pages
that don't have one.

An answer that fails one of the
[page extraction checks](../../reference/extraction-checks/) is not a failure.
pydelity sends it back up to `advanced.extraction.check_retries` times, then
keeps the last answer and puts what is still wrong on the review list. A
difference from the page's hints is never sent back and never fails a page. See
[How a page is checked](../page-extraction/#how-a-page-is-checked).

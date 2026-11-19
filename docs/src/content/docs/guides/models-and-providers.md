---
title: Models and providers
description:
  Choose an Anthropic or OpenAI model, and learn how pydelity sends your PDF,
  how long the provider keeps it and what happens when a request fails.
---

pydelity works with models from Anthropic and OpenAI. You pick one with the
`model` setting, written as `<provider>:<model-id>`.

## Choose a model

The default is `anthropic:claude-opus-5-5`. To use an OpenAI model, name it with
the `openai:` prefix:

```sh
pydelity document.pdf --model openai:gpt-6.2-astra
```

```python
import pydelity

result = pydelity.run("document.pdf", model="openai:gpt-6.2-astra")
```

pydelity sends the model ID to the provider exactly as you give it. It keeps no
list of models, so you can use any model ID your provider accepts. The model
must read PDFs and support the `effort` setting (`advanced.survey.effort`). An
older model that doesn't fails with the provider's error.

Each provider needs its own API key: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`.
See [Set your API key](../../start/install/#set-your-api-key).

## What is sent to the provider

For each survey, pydelity sends the provider:

- the PDF itself
- pydelity's instructions for the survey
- a plain-text summary of what it measured in the PDF, and the repeated lines it
  found
- your `instructions` and `languages`, if you set them

Run with `--verbose` to see the text it sends.

## How long the provider keeps your PDF

pydelity uploads the PDF to your provider account's file storage once, then
points each request at the upload. It records the upload in `uploads.json` in
the output folder, and later runs reuse it while at least an hour is left before
it expires.

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

If the upload fails, pydelity warns you and sends the PDF inside each request
instead, for the rest of the run. Two upload errors stop the run, because the
request would fail the same way: an invalid API key, and a PDF the provider
rejects as too large.

## Large PDFs

pydelity doesn't check a PDF's size or page count against the model's limits,
because those limits change. It sends the PDF and, if the provider rejects it,
shows the provider's error. The command exits with code 1. In Python, the error
is a `ProviderError`, with the provider's own message in `provider_message`.

A rejected request reports no usage, so it adds nothing to `cost.jsonl`. Check
your provider's documentation for its current limits on PDF size and pages.

## Failed requests and retries

When a request fails for a temporary reason, such as a dropped connection, a
timeout, a rate limit or a server error, the provider's SDK tries it again.
`advanced.provider_retries` sets how many times, from 0 to 10. The default is 2.
After the last retry, the run fails with a `ProviderError`.

`advanced.survey.request_timeout_seconds` sets how long to wait for one request.
The default, 900 seconds, leaves room for a long PDF.

A request that times out on pydelity's side may still finish at the provider,
and the provider may still bill it. pydelity never sees what such a request
used, so it is missing from `cost.jsonl`. With retries, each timed-out attempt
can add cost of this kind. If you see timeouts, check your provider's usage
page.

## When the survey fails

The survey itself can fail even when every request succeeds:

- The model refuses to answer.
- The answer runs out of output tokens. Raising
  `advanced.survey.max_output_tokens` can help.
- The model never gives an answer in the form pydelity expects.

These raise a `SurveyError` in Python, and the command exits with code 1. An
answer that is well formed but fails one of the
[survey checks](../../reference/survey-checks/) is not a failure. pydelity sends
it back to the model with the problems listed, up to
`advanced.survey.check_retries` times, then keeps the last answer and adds each
remaining problem to the review list.

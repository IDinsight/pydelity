---
title: Control costs
description:
  See what a run will cost before it starts, set a spending limit and find what
  each run spent.
---

Each step sends your PDF or its pages to a paid model. pydelity shows what it
expects to spend before it starts, lets you set a limit and records what every
request cost.

## The estimate

Before any model request, pydelity estimates each step the run will do. For a
2-page scanned form, the survey's estimate looked like this:

```text
Survey cost estimate: about $0.24, at most $2.53 (up to 3 requests to anthropic:claude-opus-5-5)
Spent so far in this output folder: $0.00; max_cost: not set
```

and, on the next run, page extraction's:

```text
Extraction cost estimate: about $0.23, at most $4.81 (2 pages, up to 6 requests to anthropic:claude-opus-5-5)
```

- **About** is the likely cost. For the survey, that is one request with an
  answer of typical length. For page extraction, it is one request to read each
  page, with an answer that grows with how much text the page holds. A step
  whose verifier is on adds the verifier's requests, and its line names it, such
  as `Extraction with its verifier cost estimate`. For the same form, that about
  doubled each step's likely cost. See
  [Review answers with a verifier](../verifiers/#what-a-verifier-costs).
- **At most** is the worst case: every check retry used, each answer as long as
  allowed. Most runs cost far less.

The survey's estimate counts the PDF's pages and the text sent with it. Page
extraction's counts the page images and the text sent with each page, for the
pages that will be extracted: the selected pages without a saved page file that
still fits, or every selected page with `overwrite`. Both are rough guides, and
real costs can differ.

A run that pauses after the survey shows only the survey's estimate. With
`--no-pause`, the first run shows both.

To see the estimate without running anything, use Python. No API key is needed:

```python
import pydelity

# pause=False includes page extraction, even before a survey exists.
estimate = await pydelity.aestimate("document.pdf", pause=False, pages="1-10")
print(estimate.expected_usd, estimate.max_usd)
for step in estimate.steps:
    print(step.name, step.expected_usd, step.max_usd)
```

A step whose saved output would be reused costs nothing, and the estimate says
so.

## The question

On the command line, pydelity asks before it spends anything:

```text
Go ahead with the model requests? [y/N]:
```

It asks once per run, for every step the run will do. Answering no, or just
pressing Enter, stops the run with exit code 3. Nothing is sent, and the
measured facts are kept for next time. `--yes` answers yes for you.

Python functions never ask. They go ahead unless `max_cost` would stop them.

## Set a spending limit

`max_cost` is the most, in US dollars, that the model requests in one output
folder may cost. It counts every run in that folder, not only the current one,
so a run that is resumed or redone adds to the same total.

```sh
pydelity document.pdf --max-cost 5
```

```yaml
# In a config file
max_cost: 5
```

pydelity checks the limit before the run spends anything, and again before each
model request:

- **Before the run**, it adds the estimate's likely cost to what the folder has
  spent so far.
- **Before each request**, it adds the most that request could cost to what has
  been spent and to the most that the requests still in progress could cost.
  This holds when several pages are extracted at the same time.

When the run could go over the limit, pydelity warns you and then:

| Where                              | What happens                                                  |
| ---------------------------------- | ------------------------------------------------------------- |
| Command line                       | Asks `Go ahead, even though this run could go over max_cost?` |
| Command line with `--yes`          | Goes ahead after the warning                                  |
| Python                             | Raises `BudgetExceededError` before sending the request       |
| Python, `allow_over_max_cost=True` | Goes ahead after the warning                                  |

Because the first check uses the likely cost, a run can pass it and still reach
the question partway through, before the request that could go over. Once you
allow it, the rest of the run goes ahead without asking again. If you say no,
the run stops and sends no more requests. Page requests already in progress when
you answer are canceled, and the provider may still bill them, as
[What a run spent](#what-a-run-spent) explains. Pages already extracted stay
saved. Run it again to continue: the saved files are reused, and the spend so
far still counts toward `max_cost`.

```python
import pydelity

try:
    result = await pydelity.arun("document.pdf", max_cost=2, pause=False)
except pydelity.BudgetExceededError:
    # Decided to spend more after all: go ahead past max_cost, with a warning.
    result = await pydelity.arun(
        "document.pdf", max_cost=2, pause=False, allow_over_max_cost=True
    )
```

## What a run spent

pydelity writes one line to `cost.jsonl` in the output folder for each model
response, with its tokens and cost. Each line names its step and the `agent`
that made the request: `surveyor` for the survey's own requests, `extractor` for
the requests that read a page, and `verifier` for a verifier's requests in
either step. Page extraction's lines also name the page. Lines from every run in
the folder stay in the file, so it is the folder's full spending record.

`run.json` sums it up under `cost`:

- `run_usd`: what this run spent
- `by_step`: this run's spend by step, `survey` and `extraction`, each with its
  verifier's requests included
- `output_folder_usd`: what every run in the folder has spent
- `unpriced_requests`: this run's requests with no known price

The command's closing summary and `report.html` show the same figures. With
`--verbose`, the command also prints what each page cost as it finishes. The
[cost.jsonl reference](../../reference/cost-jsonl/) lists every field.

The ledger only knows what the provider reported. A request that timed out on
pydelity's side, or that was still in progress when the run stopped, may still
have been billed, with no line in `cost.jsonl`. See
[Failed requests and retries](../models-and-providers/#failed-requests-and-retries).

## Prices

pydelity looks up model prices in the
[genai-prices](https://github.com/pydantic/genai-prices) package, which is
updated as providers change their prices. Each line of `cost.jsonl` records
where its price came from.

If genai-prices has no price for your model, pydelity warns you, records the
requests without a cost and counts them in `unpriced_requests`. With `max_cost`
set, a run on an unpriced model always counts as possibly over the limit,
because its cost can't be known.

To set a price yourself, add it under `advanced.models`, in US dollars per
million tokens:

```yaml
advanced:
  models:
    "openai:gpt-6.2-astra":
      input_usd_per_mtok: 1.25
      output_usd_per_mtok: 10.0
      # Optional. Each defaults to the input price.
      cache_read_usd_per_mtok: 0.125
      cache_write_usd_per_mtok: null
```

These numbers are only an example. Use your provider's current prices. A price
set here replaces the one pydelity would look up for that model, whichever step
uses it. A cache price of `0` counts as free.

## Spend less

- Reuse what you have. Running the same command again costs nothing, and a
  stopped run picks up where it left off. See [Rerun and resume](../reruns/).
- Keep the pause on and check the survey before paying for page extraction. A
  wrong survey makes every page that depends on it wrong.
- Extract only the pages you need with `pages`, or try a few pages first, such
  as `--pages 1-3`, before the rest.
- Lower `effort` under `advanced.survey` or `advanced.extraction` to `medium` or
  `low`. The model thinks less, which costs less and can make the answer less
  reliable.
- Lower `check_retries` to send fewer answers back to the model. Problems left
  in the last answer go on the review list instead.
- Leave the verifiers off, which is the default, or turn on only the one you
  need with `advanced.survey.verify` or `advanced.extraction.verify`. The
  survey's verifier sends the whole PDF again.
- Try a cheaper model, for page extraction only if you like, with
  `advanced.extraction.model`. Compare the estimates first with
  `pydelity.aestimate`.

---
title: Control costs
description:
  See what a survey will cost before it runs, set a spending limit and find what
  each run spent.
---

Each survey sends the whole PDF to a paid model. pydelity shows what it expects
to spend before it starts, lets you set a limit and records what every request
cost.

## The estimate

Before any model request, pydelity estimates the survey's cost:

```text
Survey cost estimate: about $0.36, at most $2.90 (up to 3 requests to anthropic:claude-opus-5-5)
Spent so far in this output folder: $0.00; max_cost: not set
```

- **About** is the likely cost: one request with an answer of typical length.
- **At most** is the worst case: the first request plus every check retry, each
  with the longest answer allowed. Most runs cost far less.

The estimate counts the PDF's pages and the text sent with it. It is a rough
guide, and real costs can differ.

To see the estimate without running anything, use Python. No API key is needed:

```python
import pydelity

estimate = pydelity.estimate("document.pdf")
print(estimate.expected_usd, estimate.max_usd)
```

A survey that would be reused costs nothing, and the estimate says so.

## The question

On the command line, pydelity asks before it spends anything:

```text
Go ahead with the model requests? [y/N]:
```

Answering no, or just pressing Enter, stops the run with exit code 3. Nothing is
sent, and the measured facts are kept for next time. `--yes` answers yes for
you.

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

pydelity checks the limit twice: before the run spends anything, using the
estimate's maximum, and again before each model request. When the run could go
over the limit, pydelity warns you and then:

| Where                              | What happens                                                  |
| ---------------------------------- | ------------------------------------------------------------- |
| Command line                       | Asks `Go ahead, even though this run could go over max_cost?` |
| Command line with `--yes`          | Goes ahead after the warning                                  |
| Python                             | Raises `BudgetExceededError` before sending anything          |
| Python, `allow_over_max_cost=True` | Goes ahead after the warning                                  |

Once you allow it, the rest of the run goes ahead without asking again. If you
say no, the run stops with nothing more spent. Run it again to continue: the
saved files are reused, and the spend so far still counts toward `max_cost`.

```python
import pydelity

try:
    result = pydelity.run("document.pdf", max_cost=2)
except pydelity.BudgetExceededError:
    # Decided to spend more after all: go ahead past max_cost, with a warning.
    result = pydelity.run("document.pdf", max_cost=2, allow_over_max_cost=True)
```

Because the check uses the worst case, pydelity can ask about a run that would
have fitted. Raise `max_cost`, or allow the run, if the likely cost is
acceptable.

## What a run spent

pydelity writes one line to `cost.jsonl` in the output folder for each model
response, with its tokens and cost. Lines from every run in the folder stay in
the file, so it is the folder's full spending record.

`run.json` sums it up under `cost`:

- `run_usd`: what this run spent
- `by_step`: this run's spend by step
- `output_folder_usd`: what every run in the folder has spent
- `unpriced_requests`: this run's requests with no known price

The command's closing summary and `report.html` show the same figures. The
[cost.jsonl reference](../../reference/cost-jsonl/) lists every field.

The ledger only knows what the provider reported. A request that timed out on
pydelity's side may still have been billed, with no line in `cost.jsonl`. See
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
set here replaces the one pydelity would look up for that model.

## Spend less

- Reuse what you have. Running the same survey again costs nothing. See
  [Rerun and resume](../reruns/).
- Lower `advanced.survey.effort` to `medium` or `low`. The model thinks less,
  which costs less and can make the answer less reliable.
- Lower `advanced.survey.check_retries` to send fewer answers back to the model.
  Problems left in the last answer go on the review list instead.
- Try a cheaper model. Compare the estimates first with `pydelity.estimate`.

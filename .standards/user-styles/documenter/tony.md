## Documentation style

1. Avoid overloaded jargon, promotional language, filler, and stock AI phrases.
2. Use technical language only when necessary or required.
3. Use plain language and simple explanations.

## Workflow wording

1. Do not write the development workflow's own terms in anything that ships with
   the project: code, comments, docstrings, documentation, test names and
   messages, or config. Readers outside the coding-agent session do not know
   them.
2. Do not number the pipeline's steps ("Step 1", "step 2", "steps 3-6"). Name
   the step instead, such as "the survey" or "page extraction". Saying "later
   steps" or "the next step" is fine.
3. Also leave out plan, acceptance and finding IDs (such as DEV-001, AC-006 and
   F-002), cycle and workflow-role names, decision dates and "the user decided"
   notes, and notes about where code came from (such as "ported from" another
   project). Keep that history in the workflow records and commit messages.
4. Workflow records under `.standards/` are not shipped and may use these terms.

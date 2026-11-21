## Documentation style

1. Avoid overloaded jargon, promotional language, filler, and stock AI phrases,
   such as:
   - two contrasting clauses joined by a semicolon ("X never does A; Y does B")
   - a colon that sets up a reveal ("...: the caller's code"), and aphorisms
   - personification, such as settings that "win over" others or checks that
     "trip"
   - vague nouns ("the same work") and filler words ("exactly", "simply",
     "ever")
2. Use technical language only when necessary or required.
3. Use plain language and simple explanations. Prefer short declarative
   sentences that name the actual function, value or behavior.
4. Use American English, such as behavior, license, serialize, canceled and
   labeled. Keep third-party API names as they are, such as
   `asyncio.CancelledError`.

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

## Backwards compatibility

Do not keep backwards compatibility or legacy behavior unless I explicitly ask
for it. When a change renames, removes or changes a setting, option, function,
output field or file format, replace the old form outright. Do not add aliases,
deprecation warnings, migrations, fallbacks for old files, or defaults that
exist only so that older files or calls keep working. Keeping older files or
calls working is not a reason to choose or reject a design. Data, outputs and
calls made by an earlier version may stop working. If compatibility looks truly
necessary, ask me first. Describe only current behavior. Do not add migration
guides, deprecation notes or breaking-change notices unless I ask.

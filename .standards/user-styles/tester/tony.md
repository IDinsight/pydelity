## Python

1. In each module, place module-level constants and type aliases first, private
   before public. Then place private classes and functions (names that begin
   with an underscore) before public ones, and inside each class, private
   methods before public ones. Within the private names and within the public
   names, keep logical groups, such as classes and functions, each in
   alphabetical order. Exceptions are allowed when ordering would break
   execution or make the code difficult to understand, including dependencies,
   Pydantic validators, and type definitions.
2. When calling functions or methods with multiple arguments, use keyword
   arguments in alphabetical order, except where the API requires positional
   arguments. Single-argument calls may use positional arguments.
3. Docstrings are always in NumPy format.
4. Use blank lines to separate logical sections within function and
   control-block bodies where they improve readability.
5. Always use type hints in function and method signatures. Elsewhere, use them
   when helpful. The repo's `ty` checks type hints.
6. Do not call external APIs or paid services in tests. Mock or stub those
   boundaries. Local MCP client/server integration checks are allowed. If
   external mocking would leave important behavior unverified, explain the gap
   and await my decision.
7. Always reuse existing pytest fixtures when possible. If a new fixture is
   needed, it should be added to the `conftest.py` file in the appropriate
   directory.
8. Private function/method/class/variable names should begin with an underscore
   to distinguish against their public counterparts. Do not rename a
   framework-required name, or a public name, only to follow this rule.
9. For comments and docstrings, use plain language and simple explanations, and
   technical language only when necessary or required. Prefer short declarative
   sentences that name the actual function, value or behavior. Avoid overloaded
   jargon, promotional language, filler, and stock AI phrases, such as:
   - two contrasting clauses joined by a semicolon ("X never does A; Y does B")
   - a colon that sets up a reveal ("...: the caller's code"), and aphorisms
   - personification, such as settings that "win over" others or checks that
     "trip"
   - vague nouns ("the same work") and filler words ("exactly", "simply",
     "ever")
10. Use American English, such as behavior, license, serialize, canceled and
    labeled, in code, comments, docstrings, test names and messages. Keep
    third-party API names as they are, such as `asyncio.CancelledError`.

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
necessary, ask me first. Replace tests of a replaced contract with tests of the
new one. Do not keep tests that hold the old behavior.

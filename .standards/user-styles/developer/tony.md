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
3. Docstrings are always in NumPy format. When helpful for understanding,
   include a short but meaningful `Examples` section showing how the function or
   method is typically invoked **and** what output it produces. Do not include
   trivial or filler examples just for the sake of it. It's ok not to include
   examples if they serve no concrete purpose.
4. Use blank lines to separate logical sections within function and
   control-block bodies where they improve readability.
5. Keep McCabe complexity at 10 or less. Ruff checks it.
6. Always use type hints in function and method signatures. Elsewhere, use them
   when helpful. The repo's `ty` checks type hints.
7. Use inline comments where helpful to explain complex or tricky code.
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
    labeled, in code, comments, docstrings, messages and config. Keep
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

## Step reports

When working through the plan one step at a time, end each step's report with
the next step's plan: what it builds and how, the files and folders it will
create or change, how it will be checked, and anything that needs my approval,
such as downloads or spending on model calls.

## Backwards compatibility

Do not keep backwards compatibility or legacy behavior unless I explicitly ask
for it. When a change renames, removes or changes a setting, option, function,
output field or file format, replace the old form outright. Do not add aliases,
deprecation warnings, migrations, fallbacks for old files, or defaults that
exist only so that older files or calls keep working. Keeping older files or
calls working is not a reason to choose or reject a design. Data, outputs and
calls made by an earlier version may stop working. If compatibility looks truly
necessary, ask me first. Update every caller, example and config file to the new
form. Do not leave shims. Tests and docs are updated by their own roles.

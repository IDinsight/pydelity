## Python

1. Functions, classes, methods, global variables, etc. should be placed
   alphabetically within logical groups in each module. Exceptions are allowed
   when ordering would break execution or make the code difficult to understand,
   including dependencies, Pydantic validators, and type definitions.
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
5. Keep McCabe complexity <= 10. This is checked by the repo's `pylint` tool.
6. Always use type hints in function and method signatures. Elsewhere, use them
   when helpful. The repo's `mypy` tool checks type hints.
7. Use inline comments where helpful to explain complex or tricky code.
8. Private function/method/class/variable names should begin with an underscore
   to distinguish against their public counterparts. Preserve framework-required
   names and established public interfaces.
9. Place private functions, classes, methods and global variables (names that
   begin with an underscore) before public ones in each module, keeping
   alphabetical order within each group. Exceptions are allowed when ordering
   would break execution or make the code difficult to understand, including
   dependencies, Pydantic validators, and type definitions.
10. For comments/docstrings, avoid overloaded jargon, promotional language,
    filler, and stock AI phrases. Use technical language only when necessary or
    required. Use plain language and simple explanations.

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

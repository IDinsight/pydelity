"""The survey's prompts: one for the survey model, one for its verifier.

The prompts name no document type, no language and no writing direction, and hold no
word lists, so they read the same for any PDF in any language. The facts summary tells
the models what was measured and which facts could not be read, and every repeated
line is listed so the models can say which are page furniture.
"""

# Standard Library
import json

from collections.abc import Mapping, Sequence

# Package Library
from pydelity.review import CheckFailure, ReviewIssue, SurveyCheckName
from pydelity.surveying.schemas import ItemKind, ItemRole, RepeatedLine, SurveyAnswer
from pydelity.utils.prompts import PromptPair

# How page indexes, page ranges and positions are given, which both prompts use.
_CONVENTIONS = """\
Page indexes start at 0. Page ranges are inclusive: first_page_index 2 and \
last_page_index 4 cover pages 2, 3 and 4. Positions, directions and boxes refer to \
each page as it is displayed."""

# The verifier's review list: what code cannot judge about a survey.
_REVIEW = """\
Review the survey against the PDF for:
1. Labels: labels that do not fit the content they are given to, content that no \
label fits, and labels that should be one.
2. Regions: regions on the wrong area of the page or with the wrong label.
3. Page furniture: page furniture given as content and content given as page \
furniture, including page furniture that has no repeated line.
4. Rotation: pages that are not upright when turned as the rotation says.
5. Page numbering: ranges, styles or offsets that differ from the numbers printed on \
the pages.
6. Writing direction: a direction that differs from how the pages are written.
7. Languages: languages missing, not used in the PDF, or out of order.
8. Continuation notes and start markers that are wrong or missing.

The measured facts come from the PDF's text layer and internal structure and can be \
wrong, so the PDF decides. A difference from the facts is a problem only when the \
survey is wrong about the PDF."""

# The rules a survey answer follows, which both models get.
_RULES = f"""\
Labels. Make labels for the kinds of content in this PDF. Give each label a short \
name, a description, one role and the kinds of item it may be given to. Use as few \
labels as it takes to tell the content apart. Do not make a label named "other": \
pydelity adds it for content that no label fits.

Roles:
- {ItemRole.ARTIFACT.value}: page furniture that is not part of the content, such as \
running headers, footers and page numbers
- {ItemRole.ASIDE.value}: content beside the main flow, such as a sidebar or callout
- {ItemRole.BODY.value}: the main content
- {ItemRole.CAPTION.value}: a caption of a figure or table
- {ItemRole.FOOTNOTE.value}: a footnote or endnote
- {ItemRole.HEADING.value}: a heading
- {ItemRole.NAVIGATION.value}: a table of contents, index or other navigation aid

Kinds:
- {ItemKind.CODE.value}: code and other preformatted text, whose spacing and line \
breaks must be kept
- {ItemKind.FIELD.value}: a form field, with its label and value
- {ItemKind.FIGURE.value}: an image, chart or diagram
- {ItemKind.FORMULA.value}: a mathematical or chemical formula
- {ItemKind.LIST.value}: a list of items
- {ItemKind.TABLE.value}: a table
- {ItemKind.TEXT.value}: running text

Languages. List the BCP-47 tags of the languages the text is written in, the most \
used first. Use zxx when the PDF has no text in any language.

Writing direction. Give the direction most pages are written in as the default: \
ltr, rtl, or ttb for vertical writing. Add a range for pages written in another \
direction.

Rotation. For pages whose content is not upright as displayed, give the clockwise \
rotation in degrees (90, 180 or 270) that makes it upright. Leave out pages that are \
upright. Include pages whose text is inside images, such as scans, which the facts \
cannot measure.

Page numbering. Give ranges of pages whose printed page numbers follow the page \
index, with the numbers' style and offset: the printed number minus the page index. \
Use style none and offset null for pages that print no numbers. Give the numbers \
you see printed on the pages, whether or not the facts found them.

Artifacts. Page furniture is not part of the content: running headers and footers, \
page numbers, logos, watermarks, stamps and the like. The text sent with the PDF \
lists every line that repeats across pages, with its ID (R1, R2 and so on), its text, \
how many pages it is on and the band of the page it usually sits in. Account for \
every repeated line ID exactly once: in an artifact's repeated_line_ids, or in \
non_artifact_lines with the reason it is content. An artifact may have no repeated \
lines, such as a logo or a stamp.

Continuation notes. Say how content continues across page breaks, such as text, \
lists or tables that run onto the next page.

Start markers. Give text that marks where a new unit of content starts, as printed, \
with what starts there.

Regions. Mark areas of single pages whose content needs a label of its own. Give \
each area's box as fractions of the displayed page, from 0 to 1, measured from the \
top-left corner. Leave regions empty when no area needs one.

Notes. Add anything else about the layout that later steps should know."""

# The verifier's verdict rules.
_VERDICT = """\
Give a verdict. When the survey is faithful to the PDF and nothing material is wrong, \
set passed to true, with no problems and corrected null. Otherwise set passed to false \
and list each problem: its category, the index of the page it is about (null when it \
is about the whole PDF or several pages), and a description that quotes the text \
concerned so that a person can find it. Then give corrected: the whole survey answer \
again with every problem fixed, following the same rules. Start from the survey, fix \
what is wrong and keep what is right, including how it accounts for every repeated \
line. List only problems that change what the survey says about the PDF, not matters \
of taste. Set corrected to null only when you cannot correct the survey.

The checks the survey still fails and its differences from the measured facts are \
given with the PDF. The checks come from code that tests the answer's form and \
completeness: a correction must pass them."""

# The version of the prompts. Increase it whenever the text of either prompt changes,
# so a saved survey made with the older prompts is made again.
PROMPT_VERSION = 1


def _with_user_instructions(system_message: str, instructions: str | None) -> str:
    """Add the user's instructions at the end of a system message, when there are any.

    Parameters
    ----------
    system_message
        pydelity's instructions.
    instructions
        The user's survey instructions, or ``None``.

    Returns
    -------
    str
        The system message, ending with the user's instructions under a heading
        that says they add to pydelity's instructions.
    """

    if not instructions:
        return system_message
    return (
        system_message
        + "\n\nThe user's instructions for this PDF follow. They add to the "
        f"instructions above and do not replace them.\n{instructions}"
    )


def survey_pdf(
    *,
    facts_summary: list[str],
    instructions: str | None,
    languages: list[str],
    page_count: int,
    repeated_lines: list[RepeatedLine],
) -> PromptPair:
    """Write the survey's messages: the instructions, and the text sent with the PDF.

    Parameters
    ----------
    facts_summary
        The facts summary lines from ``pdf_facts.json``.
    instructions
        The user's instructions for the survey (``advanced.survey.instructions``), if
        any.
    languages
        The user's languages, as BCP-47 tags in standard form.
    page_count
        The PDF's number of pages.
    repeated_lines
        The measured repeated lines, each listed with its ID, text, page count and
        band, such as ``R1: "Section A", on 12 pages, usually in the top band``.

    Returns
    -------
    PromptPair
        The instructions as the system message, ending with the user's instructions
        when given. The user message has the page count, the facts summary, the
        repeated lines, and the user's languages when given.

    Examples
    --------
    >>> prompts = survey_pdf(facts_summary=["Text: good on every page."],
    ...     instructions=None, languages=["en"], page_count=2, repeated_lines=[])
    >>> print(prompts.user_message)
    The PDF has 2 pages, with indexes 0 to 1.
    <BLANKLINE>
    Measured facts:
    Text: good on every page.
    <BLANKLINE>
    The user says the PDF is written in: en
    """

    system_message = f"""\
You receive a PDF and facts measured from it without a model. Describe how the PDF's \
pages are laid out, so that later steps can take its content apart page by page.

The facts come from the PDF's text layer and internal structure, not from the pages \
as a reader sees them, so they can miss or mistake things, such as text inside images \
or a number in a table taken for a page number. Treat them as hints. Wherever your \
own reading of the PDF differs from them, answer with what you read.

{_CONVENTIONS}

{_RULES}

Your answer is checked for form and completeness, and you will be told what to fix \
if a check fails."""
    pages = (
        "1 page, with index 0"
        if page_count == 1
        else f"{page_count} pages, with indexes 0 to {page_count - 1}"
    )
    sections = [
        f"The PDF has {pages}.",
        "Measured facts:\n" + "\n".join(facts_summary),
    ]
    if repeated_lines:
        sections.append(
            "Repeated lines:\n"
            + "\n".join(
                f"{line.id}: {json.dumps(line.text, ensure_ascii=False)}, on "
                f"{len(line.pages)} page{'' if len(line.pages) == 1 else 's'}, "
                f"usually in the {line.band} band"
                for line in repeated_lines
            )
        )
    if languages:
        sections.append(f"The user says the PDF is written in: {', '.join(languages)}")

    return PromptPair(
        system_message=_with_user_instructions(system_message, instructions),
        user_message="\n\n".join(sections),
    )


def verify_survey(
    *,
    answer: SurveyAnswer,
    differences: Sequence[ReviewIssue],
    failures: Mapping[SurveyCheckName, list[CheckFailure]],
    instructions: str | None,
    survey_message: str,
) -> PromptPair:
    """Write the verifier's messages: the instructions, and the text sent with the PDF.

    Parameters
    ----------
    answer
        The survey's answer to review.
    differences
        Where the answer differs from the measured facts, from
        `pydelity.surveying.validators.compare_with_facts`.
    failures
        The checks the answer still fails, from
        `pydelity.surveying.validators.run_checks`.
    instructions
        The user's instructions for the survey (``advanced.survey.instructions``), if
        any.
    survey_message
        The user message of the survey's own request, from `survey_pdf`.

    Returns
    -------
    PromptPair
        The instructions as the system message, ending with the user's instructions
        when given. The user message is the survey's own, then the answer, the checks
        it still fails and its differences from the measured facts.

    Examples
    --------
    >>> from pydelity.surveying.schemas import WritingDirection
    >>> answer = SurveyAnswer(artifacts=[], continuation_notes=[], labels=[],
    ...     languages=["en"], non_artifact_lines=[], notes=[], page_numbering=[],
    ...     regions=[], rotation=[], start_markers=[],
    ...     writing_direction=WritingDirection(default="ltr", ranges=[]))
    >>> prompts = verify_survey(answer=answer, differences=[], failures={},
    ...     instructions=None, survey_message="The PDF has 1 page, with index 0.")
    >>> print(prompts.user_message)  # doctest: +ELLIPSIS
    The PDF has 1 page, with index 0.
    <BLANKLINE>
    The survey answer to review:
    {"artifacts": [], ...}
    <BLANKLINE>
    Checks it still fails:
    none
    <BLANKLINE>
    Differences from the measured facts:
    none
    """

    system_message = (
        "You review a survey of a PDF, made by another model, against the PDF and "
        "facts measured from it without a model. You are not surveying the PDF from "
        "scratch: you are checking someone else's work and correcting it where it is "
        "wrong.\n\n"
        f"{_REVIEW}\n\n{_VERDICT}\n\n"
        "The rules the survey follows, which a correction follows too:\n\n"
        f"{_CONVENTIONS}\n\n{_RULES}"
    )
    found = [failure.message for found in failures.values() for failure in found]
    sections = [
        survey_message,
        "The survey answer to review:\n"
        + json.dumps(answer.model_dump(mode="json"), ensure_ascii=False),
        "Checks it still fails:\n"
        + ("\n".join(f"- {message}" for message in found) if found else "none"),
        "Differences from the measured facts:\n"
        + (
            "\n".join(f"- {issue.message}" for issue in differences)
            if differences
            else "none"
        ),
    ]
    return PromptPair(
        system_message=_with_user_instructions(system_message, instructions),
        user_message="\n\n".join(sections),
    )

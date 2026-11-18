"""The survey's prompt.

The prompt names no document type and holds no word lists, so it reads the same for
any PDF in any language. The facts summary tells the model what was measured and which
facts could not be read.
"""

# Package Library
from pydelity.surveying.schemas import ItemKind, ItemRole
from pydelity.utils.prompts import PromptPair

# The version of the prompt. Increase it whenever the text of either message changes,
# so a saved survey made with the older prompt is made again.
PROMPT_VERSION = 1


def survey_pdf(
    *,
    facts_summary: list[str],
    instructions: str | None,
    languages: list[str],
    page_count: int,
) -> PromptPair:
    """Write the survey's messages: the instructions, and the text sent with the PDF.

    Parameters
    ----------
    facts_summary
        The facts summary lines from ``pdf_facts.json``.
    instructions
        The user's instructions, if any.
    languages
        The user's languages, as BCP-47 tags in standard form.
    page_count
        The PDF's number of pages.

    Returns
    -------
    PromptPair
        The instructions as the system message. The user message has the page count,
        the facts summary, and the user's instructions and languages when given.

    Examples
    --------
    >>> prompts = survey_pdf(facts_summary=["Text: good on every page."],
    ...     instructions=None, languages=["en"], page_count=2)
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

Page indexes start at 0. Page ranges are inclusive: first_page_index 2 and \
last_page_index 4 cover pages 2, 3 and 4. Positions, directions and boxes refer to \
each page as it is displayed.

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
upright. Where the facts measure a page's text angle with confidence, your rotation \
for that page must equal it.

Page numbering. Give ranges of pages whose printed page numbers follow the page \
index, with the numbers' style and offset: the printed number minus the page index. \
Use style none and offset null for pages that print no numbers. Your offsets must \
agree with the printed numbers the facts measure.

Artifacts. Page furniture is not part of the content: running headers and footers, \
page numbers, logos, watermarks, stamps and the like. The facts list lines that \
repeat across pages, with IDs (R1, R2 and so on). Account for every repeated line ID \
exactly once: in an artifact's repeated_line_ids, or in non_artifact_lines with the \
reason it is content. An artifact may have no repeated lines, such as a logo or a \
stamp.

Continuation notes. Say how content continues across page breaks, such as text, \
lists or tables that run onto the next page.

Start markers. Give text that marks where a new unit of content starts, as printed, \
with what starts there.

Regions. Mark areas of single pages whose content needs a label of its own. Give \
each area's box as fractions of the displayed page, from 0 to 1, measured from the \
top-left corner. Leave regions empty when no area needs one.

Notes. Add anything else about the layout that later steps should know.

The user's instructions, when given, add to these instructions and do not replace \
them. Your answer is checked against the measured facts, and you will be told what \
to fix if it does not match them."""

    pages = (
        "1 page, with index 0"
        if page_count == 1
        else f"{page_count} pages, with indexes 0 to {page_count - 1}"
    )
    sections = [
        f"The PDF has {pages}.",
        "Measured facts:\n" + "\n".join(facts_summary),
    ]
    if instructions:
        sections.append(f"The user's instructions:\n{instructions}")
    if languages:
        sections.append(f"The user says the PDF is written in: {', '.join(languages)}")

    return PromptPair(system_message=system_message, user_message="\n\n".join(sections))

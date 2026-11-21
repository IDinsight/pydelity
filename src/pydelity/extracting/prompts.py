"""Page extraction's prompts: one for the extraction model, one for the verifier.

Each prompt's instructions (the system message) are the same for every page of a
run, so providers can cache them: the task, the item vocabulary, the PDF's labels,
the rules an extraction follows and, last, the user's page extraction instructions.
The text sent with each page image says which page it is and gives what the survey
and the PDF's own data know about it: its writing direction, its repeated lines and
its fillable form fields. The text the PDF stores for the page is never sent; the
models read all text from the image.

No prompt names a document type, a language or a writing direction as a default.
"""

# Standard Library
import json

from collections.abc import Mapping, Sequence

# Package Library
from pydelity.extracting.rendering import GRID, points_box_to_grid
from pydelity.extracting.schemas import PageAnswer, PageContext
from pydelity.review import CheckFailure, ExtractionCheckName
from pydelity.surveying.schemas import FormField, ItemKind, ItemRole, Label
from pydelity.utils.prompts import PromptPair

# How the page's writing direction is described to the models.
_DIRECTIONS = {
    "ltr": "The page is written left to right.",
    "rtl": "The page is written right to left.",
    "ttb": (
        "The page is written top to bottom, in vertical columns. Set column_order to "
        "the order its columns are read in."
    ),
}

# The heading of the labels list, shared by both prompts.
_LABELS_HEADING = """\
Labels. Give each item a label from this PDF's labels, below. Use a label whose role \
is the item's role and whose kinds include the item's kind; use "other" only when no \
other label fits. Give each container the label that fits it best."""

# The verifier's review list.
_REVIEW = """\
Review the extraction against the page image for:
1. Missing content: anything on the page that no item holds, especially near the \
edges and in the margins.
2. Extra content: items or text that are not on the page.
3. Text: words or lines missing, added or changed, and text translated, corrected or \
completed.
4. Merged or split items: two items run together as one, or one item cut into \
several.
5. Kinds, roles and labels: a table given as a figure or text, a caption given as a \
heading, page furniture given as content, and the like; labels that do not fit.
6. Reading order: items out of the order a reader reads the page in, for its writing \
direction and layout.
7. Tables: rows or columns missing or merged, a grid read as a single column, wrong \
spans or header rows, blank cells filled in.
8. Boxes on the wrong content, or far larger or smaller than it.
9. Figures without a description or without the text inside them; form fields with \
the wrong value or mark; containers or captions that point at the wrong items."""

# The rules an extraction follows, which both models get.
_RULES = f"""\
Items. Every piece of content on the page is one item: a paragraph, a heading, a \
list, a table, a figure, a formula, a block of code, a form field, a line of page \
furniture. Give each item a short ref of your own, unique on the page, such as t1 or \
f2, and use refs to point from one item to another.

Kinds. Each item has one kind, which says what content it holds:
- {ItemKind.TEXT.value}: running text
- {ItemKind.LIST.value}: a list of items
- {ItemKind.TABLE.value}: a table
- {ItemKind.FIGURE.value}: an image, chart, diagram or photo
- {ItemKind.FORMULA.value}: a mathematical or chemical formula
- {ItemKind.CODE.value}: code and other preformatted text, whose spacing and line \
breaks must be kept
- {ItemKind.FIELD.value}: a form field: a place for a value, a mark or a signature

Roles. Each item has one role, which says what it does on the page:
- {ItemRole.BODY.value}: the main content
- {ItemRole.HEADING.value}: a heading
- {ItemRole.CAPTION.value}: the caption of a specific item next to it
- {ItemRole.FOOTNOTE.value}: a footnote or endnote
- {ItemRole.ASIDE.value}: content beside the main flow, such as a sidebar or callout
- {ItemRole.NAVIGATION.value}: a table of contents, index or other navigation aid
- {ItemRole.ARTIFACT.value}: page furniture, such as running headers, footers and \
page numbers

Reading order. List the items in the order a reader reads the page, for the page's \
writing direction, which is given with the page. On a page written left to right, \
read rows left to right and columns from the left-hand one; on a page written right \
to left, read rows right to left and columns from the right-hand one; in each column, \
read from the top down. On a page written in vertical columns, read bands from the \
top down and, in each band, the columns in the order the script reads them. A \
heading comes before what it heads. Put asides, captions, footnotes and page \
furniture where a reader meets them.

Text. Transcribe text exactly as printed, in its own script: keep its spelling, \
mistakes, punctuation, numbers and dot leaders. Do not translate, correct, sum up or \
complete text, including text cut off at the edge of the page, and add no text that \
is not on the page.

Content. Fill only the fields an item's kind uses, and set the others to null:
- text and code items fill text; code keeps its exact spacing and line breaks.
- formula items fill text, as printed, and latex.
- list items fill entries: one entry per list item, in order, with its bullet or \
number exactly as printed in marker (null when there is none; never invent one), and \
its nesting level, 0 for the top level.
- table items fill table: its rows from the top down, each row's cells in reading \
order. Give each cell's row_span and col_span as in HTML and leave out the cells that \
another cell's span covers. Use spans only for merged cells you can see. An empty \
cell has null text. Numbered or bulleted lines inside a cell stay in that cell. \
header_rows counts the header rows at the top. The table ends where its grid ends: a \
heading or paragraph outside the grid is an item of its own.
- figure items fill figure: what the figure shows, in description, and any text \
inside it, as printed, in text.
- field items fill field: its type, its printed label or question as prompt, and \
what is filled in, written or marked on it: value, or checked for a checkbox or radio \
button. A choice field lists its options.

Captions. A caption labels or titles a specific table, figure or other item next to \
it: set its caption_of to that item's ref. Tell a caption from a heading by what it \
does, not by how it looks. A line that names a specific nearby item is a caption even \
when it is bold, centered or numbered; a line that organizes the page's content is a \
heading.

Page furniture. Running headers and footers, page numbers and other content that \
repeats from page to page to frame the content are items with role \
{ItemRole.ARTIFACT.value}. The page's repeated lines are given with the page, with \
what the survey found each one to be; include each one found to be page furniture in \
an item with role {ItemRole.ARTIFACT.value}.

Forms. Each form field on the page is one field item. When the page has fillable \
form fields, they are given with the page: set fillable_name to the field's name and \
give its value or checked state as the page shows it. A radio button or checkbox that \
appears several times is one field item each time. On a form that is only printed or \
scanned, give what is written or marked on it, with fillable_name null.

Containers. A bordered or shaded box that holds items is a container. Give it a ref, \
a box and a label, and set container to its ref on each item inside it. A box inside \
a box names its outer container.

Languages. Give each item that has text the BCP-47 tag of the language its text is \
in, such as en or ar: mul when one item mixes languages, und when you cannot tell, \
zxx for content in no language, such as code or numbers alone. An item without text \
has language null.

Boxes. Give each item's and container's box as [x0, y0, x1, y1] on a grid of {GRID} \
units across and {GRID} down the page image, measured from its top-left corner, \
whatever the image's size: x0 < x1, y0 < y1, close around the visible content. Every \
item has a box of its own. Field boxes given with the page use the same grid.

The whole page. Scan the whole page, every margin included, before you answer. \
Ignore drawn lines and rules, such as the line above footnotes; a separator made of \
characters may be an item with role {ItemRole.ARTIFACT.value}. A page that is one \
figure, such as a page made of a single picture, is one figure item, with a box that \
may cover the whole page.

Text from the image. Read all text from the image, exactly as printed. The text a \
PDF stores for a page can differ from what is printed, with letters out of order, \
broken ligatures or wrong characters, so the image alone decides what the text is."""

# The verifier's verdict rules.
_VERDICT = """\
Give a verdict. When the extraction is faithful to the page and nothing material is \
wrong, set passed to true, with no problems and corrected null. Otherwise set passed \
to false and list each problem: its category, the ref of the item it is about (null \
when it is about no single item, such as missing content), and a description that \
quotes the text concerned so that a person can find it. Then give corrected: the whole \
page extracted again with every problem fixed, following the same rules. Start from \
the extraction, fix what is wrong and keep what is right, including its refs where the \
items stay the same. List only problems that change what the extraction says about \
the page, not matters of taste. Set corrected to null only when you cannot correct the \
page.

The checks it still fails, if any, are given with the page. They come from code that \
cannot see the page: a correction must pass them, but where a check finds a \
difference from the text the PDF stores, the image decides, since that stored text \
can be wrong."""

# The version of the prompts. Increase it whenever the text of either prompt changes,
# so a saved page file made with the older prompts is made again.
PROMPT_VERSION = 1


def _form_field_line(field: FormField, context: PageContext) -> str:
    """Describe one fillable form field for the models.

    Parameters
    ----------
    field
        The form field, with its box in points on the displayed page.
    context
        The page's context, for its size and rotation.

    Returns
    -------
    str
        The field's name, type, value, checked state, options and box on the grid.
    """

    box = points_box_to_grid(
        field.bbox,
        height_pt=context.height_pt,
        rotation=context.rotation,
        width_pt=context.width_pt,
    )
    parts = [json.dumps(field.name, ensure_ascii=False), field.type]
    if field.value is not None:
        parts.append(f"value {json.dumps(field.value, ensure_ascii=False)}")
    if field.checked is not None:
        parts.append("checked" if field.checked else "not checked")
    if field.options:
        options = ", ".join(
            json.dumps(option, ensure_ascii=False) for option in field.options
        )
        parts.append(f"options {options}")
    parts.append(f"box {box}")
    return "- " + ", ".join(parts)


def _labels(labels: Sequence[Label]) -> str:
    """List the PDF's labels with their roles, kinds and descriptions.

    Parameters
    ----------
    labels
        The profile's labels.

    Returns
    -------
    str
        The labels heading and one line per label.
    """

    lines = [
        f"- {json.dumps(label.name, ensure_ascii=False)} (role {label.role}; kinds "
        f"{', '.join(label.kinds)}): {label.description}"
        for label in labels
    ]
    return _LABELS_HEADING + "\n" + "\n".join(lines)


def _page_text(context: PageContext) -> list[str]:
    """Write what is sent about a page with its image, in sections.

    Parameters
    ----------
    context
        The page's context.

    Returns
    -------
    list[str]
        The sections, the first starting with the page's index and number.
    """

    index = context.page_index
    rotation = (
        f"The image was turned {context.rotation} degrees clockwise to show the page "
        "upright."
        if context.rotation
        else "The image shows the page as it is displayed."
    )
    sections = [
        f"Page index {index} (page {index + 1} of {context.page_count})\n"
        f"{_DIRECTIONS[context.writing_direction]} {rotation}"
    ]
    if context.repeated_lines:
        found = {
            "artifact": "page furniture",
            "content": "content",
            "unclassified": "not decided",
        }
        sections.append(
            "Repeated lines on this page, with what the survey found each one to be:\n"
            + "\n".join(
                f"- {line.id}: {json.dumps(line.text, ensure_ascii=False)}, "
                f"{found[line.use]}"
                for line in context.repeated_lines
            )
        )
    fields = [field for field in context.form_fields if field.type != "button"]
    if fields:
        sections.append(
            "Fillable form fields on this page:\n"
            + "\n".join(_form_field_line(field, context) for field in fields)
        )
    return sections


def _with_user_instructions(system_message: str, instructions: str | None) -> str:
    """Add the user's instructions at the end of a system message, when there are any.

    Parameters
    ----------
    system_message
        pydelity's instructions.
    instructions
        The user's page extraction instructions, or ``None``.

    Returns
    -------
    str
        The system message, ending with the user's instructions under a heading
        that says they add to pydelity's rules.
    """

    if not instructions:
        return system_message
    return (
        system_message
        + "\n\nThe user's instructions for this PDF follow. They add to the rules "
        f"above and do not replace them.\n{instructions}"
    )


def extract_page(context: PageContext) -> PromptPair:
    """Write the extraction model's messages for one page.

    Parameters
    ----------
    context
        The page's context.

    Returns
    -------
    PromptPair
        The instructions, the same for every page of a run, and the text sent with
        the page image.
    """

    system_message = (
        "You read one page of a PDF from an image of it and give everything on the "
        "page as items in reading order. The image is the source of truth: give "
        "exactly what is on the page.\n\n"
        f"{_RULES}\n\n{_labels(context.labels)}\n\n"
        "Your answer is checked by code and reviewed by a second model. You will be "
        "told what to fix if a check fails."
    )
    return PromptPair(
        system_message=_with_user_instructions(system_message, context.instructions),
        user_message="\n\n".join(_page_text(context)),
    )


def verify_page(
    context: PageContext,
    *,
    answer: PageAnswer,
    failures: Mapping[ExtractionCheckName, list[CheckFailure]],
) -> PromptPair:
    """Write the verifier's messages for one page's extraction.

    Parameters
    ----------
    context
        The page's context.
    answer
        The extraction to review.
    failures
        The checks the extraction still fails, from
        `pydelity.extracting.validators.run_checks`.

    Returns
    -------
    PromptPair
        The instructions, the same for every page of a run, and the text sent with
        the page image: the page's details, the extraction and its failed checks.
    """

    system_message = (
        "You review one page's extraction, made by another model, against an image "
        "of the page. You are not extracting the page from scratch: you are checking "
        "someone else's work and correcting it where it is wrong.\n\n"
        f"{_REVIEW}\n\n{_VERDICT}\n\n"
        f"The rules the extraction follows, which a correction follows too:\n\n"
        f"{_RULES}\n\n{_labels(context.labels)}"
    )
    found = [failure.message for found in failures.values() for failure in found]
    sections = [
        *_page_text(context),
        "The extraction to review:\n"
        + json.dumps(answer.model_dump(mode="json"), ensure_ascii=False),
        "Checks it still fails:\n"
        + ("\n".join(f"- {message}" for message in found) if found else "none"),
    ]
    return PromptPair(
        system_message=_with_user_instructions(system_message, context.instructions),
        user_message="\n\n".join(sections),
    )

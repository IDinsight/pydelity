"""Fixtures for page extraction's tests: answers and page contexts built in code.

The page context's profile has a label for each role and kind the tests use, plus
the catch-all ``other``, so a well-formed answer passes the labels check.
"""

# Standard Library
from collections.abc import Callable

# Third Party Library
import pytest

# Package Library
from pydelity.extracting.schemas import AnswerItem, PageContext
from pydelity.extracting.text_layer import PageText
from pydelity.surveying.schemas import ItemKind, ItemRole, Label

# The profile's labels in every built page context.
_LABELS = [
    Label(
        description="Running text, lists, tables, code and formulas.",
        kinds=[
            ItemKind.CODE,
            ItemKind.FORMULA,
            ItemKind.LIST,
            ItemKind.TABLE,
            ItemKind.TEXT,
        ],
        name="Body",
        role=ItemRole.BODY,
    ),
    Label(
        description="Pictures and charts.",
        kinds=[ItemKind.FIGURE],
        name="Figure",
        role=ItemRole.BODY,
    ),
    Label(
        description="Places on a form to fill in.",
        kinds=[ItemKind.FIELD],
        name="Form item",
        role=ItemRole.BODY,
    ),
    Label(
        description="Titles and section headings.",
        kinds=[ItemKind.TEXT],
        name="Heading",
        role=ItemRole.HEADING,
    ),
    Label(
        description="Captions of figures and tables.",
        kinds=[ItemKind.TEXT],
        name="Caption",
        role=ItemRole.CAPTION,
    ),
    Label(
        description="Running headers, footers and page numbers.",
        kinds=[ItemKind.TEXT],
        name="Page furniture",
        role=ItemRole.ARTIFACT,
    ),
    Label(
        description="Anything the other labels do not cover.",
        kinds=[ItemKind.TEXT],
        name="other",
        role=ItemRole.BODY,
    ),
]


@pytest.fixture
def answer_item() -> Callable[..., AnswerItem]:
    """Return a function that builds one item of a model's page answer.

    By default the item is body text with the label ``Body``, in English, with a box
    across the top of the page. Keyword arguments replace its fields.

    Returns
    -------
    Callable[..., AnswerItem]
        Takes the fields to replace and returns the item.
    """

    def build(**changes: object) -> AnswerItem:
        """Build an item with some fields replaced."""

        data: dict[str, object] = {
            "box": [100, 100, 900, 150],
            "caption_of": None,
            "container": None,
            "entries": None,
            "field": None,
            "figure": None,
            "kind": "text",
            "label": "Body",
            "language": "en",
            "latex": None,
            "ref": "t1",
            "role": "body",
            "table": None,
            "text": "Some running text.",
        }
        data.update(changes)
        return AnswerItem.model_validate(data)

    return build


@pytest.fixture
def no_page_text() -> PageText:
    """Return a text layer with no lines and no page furniture.

    Returns
    -------
    PageText
        An empty text layer, for checks that do not read it.
    """

    return PageText(furniture={}, lines=())


@pytest.fixture
def page_context() -> Callable[..., PageContext]:
    """Return a function that builds the context of one page.

    By default the page is the first of one, US Letter size, upright, written left
    to right, with a good text layer, no repeated lines, no form fields and no
    instructions. Keyword arguments replace its fields.

    Returns
    -------
    Callable[..., PageContext]
        Takes the fields to replace and returns the context.
    """

    def build(**changes: object) -> PageContext:
        """Build a page context with some fields replaced."""

        data: dict[str, object] = {
            "form_fields": [],
            "height_pt": 792.0,
            "instructions": None,
            "labels": _LABELS,
            "languages": ["en"],
            "page_count": 1,
            "page_index": 0,
            "repeated_lines": [],
            "rotation": 0,
            "rotation_attribute": 0,
            "text_quality": "good",
            "width_pt": 612.0,
            "writing_direction": "ltr",
        }
        data.update(changes)
        return PageContext.model_validate(data)

    return build


@pytest.fixture
def profile_labels() -> list[dict[str, object]]:
    """Return the labels of every built page context, as a survey answer gives them.

    Returns
    -------
    list[dict[str, object]]
        The labels as JSON-ready data, for a survey answer's ``labels``.
    """

    return [label.model_dump(mode="json") for label in _LABELS]

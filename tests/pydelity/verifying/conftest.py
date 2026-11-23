"""Fixtures for page-break verification's tests: page files and contexts built in code.

The page files are shaped like the ones page extraction writes, with item IDs such as
``p0003-002``, entry IDs such as ``p0003-002.1`` and container IDs such as
``p0003-c01``, so the checks and prompts read them as they read real ones.
"""

# Standard Library
from collections.abc import Callable, Sequence
from datetime import UTC, datetime

# Third Party Library
import pytest

# Package Library
from pydelity.extracting.schemas import Item, PageFile
from pydelity.surveying.schemas import StartMarker
from pydelity.verifying.schemas import BreakContext


@pytest.fixture
def break_context() -> Callable[..., BreakContext]:
    """Return a function that builds the context every break of a PDF shares.

    By default the PDF has 8 pages, the survey gave no continuation notes or start
    markers, and the user gave no instructions. Keyword arguments replace its
    fields; start markers are given as ``(text, description)`` pairs.

    Returns
    -------
    Callable[..., BreakContext]
        Takes the fields to replace and returns the context.
    """

    def build(
        *, start_markers: Sequence[tuple[str, str]] = (), **changes: object
    ) -> BreakContext:
        """Build a break context with some fields replaced."""

        data: dict[str, object] = {
            "continuation_notes": [],
            "instructions": None,
            "page_count": 8,
            "start_markers": [
                StartMarker(description=description, text=text)
                for text, description in start_markers
            ],
        }
        data.update(changes)
        return BreakContext.model_validate(data)

    return build


@pytest.fixture
def page_file() -> Callable[..., PageFile]:
    """Return a function that builds the page file of one page.

    By default the page is US Letter size, upright, written left to right, with no
    containers, and every check of page extraction passed.

    Returns
    -------
    Callable[..., PageFile]
        Takes the page index, the items in reading order, and any of
        ``column_order``, ``containers`` (``(id, label)`` pairs), ``rotation`` and
        ``writing_direction``, and returns the page file.
    """

    def build(
        page_index: int,
        *items: Item,
        column_order: str | None = None,
        containers: Sequence[tuple[str, str]] = (),
        rotation: int = 0,
        writing_direction: str = "ltr",
    ) -> PageFile:
        """Build a page file with these items and settings."""

        context: dict[str, object] = {
            "form_fields": [],
            "height_pt": 792.0,
            "instructions": None,
            "labels": [
                {
                    "description": "Everything on the page.",
                    "kinds": [
                        "code",
                        "field",
                        "figure",
                        "formula",
                        "list",
                        "table",
                        "text",
                    ],
                    "name": "other",
                    "role": "body",
                }
            ],
            "languages": ["ar", "en", "ja", "zh-Hans"],
            "page_count": 8,
            "page_index": page_index,
            "repeated_lines": [],
            "rotation": rotation,
            "rotation_attribute": rotation,
            "text_quality": "none",
            "width_pt": 612.0,
            "writing_direction": writing_direction,
        }
        data: dict[str, object] = {
            "checks": [],
            "column_order": column_order,
            "containers": [
                {
                    "bbox": [36.0, 36.0, 576.0, 756.0],
                    "container": None,
                    "id": container_id,
                    "label": label,
                }
                for container_id, label in containers
            ],
            "extracted_at": datetime(2026, 1, 5, tzinfo=UTC),
            "fingerprint": f"sha256:{page_index:064d}",
            "height_pt": 792.0,
            "hints": [],
            "image": {"height_px": 2200, "width_px": 1700},
            "inputs": {
                "context": context,
                "model": "anthropic:claude-opus-5-5",
                "pdf_sha256": "0" * 64,
                "prompt_version": 1,
                "rendering": {"crop_dpi": 200, "jpeg_quality": 90, "max_dpi": 300},
                "settings": {
                    "check_retries": 2,
                    "effort": "high",
                    "max_output_tokens": 32000,
                },
            },
            "issues": [],
            "items": [item.model_dump(mode="json") for item in items],
            "page_index": page_index,
            "page_number": page_index + 1,
            "pydelity_version": "0.3.0",
            "rotation": rotation,
            "schema_version": "1.0",
            "text_comparison": "no_text_layer",
            "verification": None,
            "width_pt": 612.0,
            "writing_direction": writing_direction,
        }
        return PageFile.model_validate(data)

    return build


@pytest.fixture
def page_item() -> Callable[..., Item]:
    """Return a function that builds one item of a page file.

    By default the item is body text in English across the top of the page. A list
    item is given its entries' texts as ``entries``, and a table item its rows'
    cell texts as ``rows``, with ``header_rows`` for its header. Other keyword
    arguments replace the item's fields.

    Returns
    -------
    Callable[..., Item]
        Takes the item's ID and the fields to replace, and returns the item.
    """

    def build(
        item_id: str,
        *,
        entries: Sequence[str] | None = None,
        header_rows: int = 0,
        rows: Sequence[Sequence[str | None]] | None = None,
        **changes: object,
    ) -> Item:
        """Build an item with this ID and some fields replaced."""

        data: dict[str, object] = {
            "bbox": [72.0, 100.0, 540.0, 130.0],
            "caption_of": None,
            "container": None,
            "entries": None,
            "field": None,
            "figure": None,
            "id": item_id,
            "kind": "text",
            "label": "other",
            "language": "en",
            "latex": None,
            "role": "body",
            "table": None,
            "text": "Some running text.",
        }
        if entries is not None:
            data |= {
                "entries": [
                    {
                        "id": f"{item_id}.{position}",
                        "level": 0,
                        "marker": f"{position}.",
                        "text": text,
                    }
                    for position, text in enumerate(entries, start=1)
                ],
                "kind": "list",
                "text": None,
            }
        if rows is not None:
            data |= {
                "kind": "table",
                "table": {
                    "header_rows": header_rows,
                    "rows": [
                        [{"col_span": 1, "row_span": 1, "text": text} for text in row]
                        for row in rows
                    ],
                },
                "text": None,
            }
        data.update(changes)
        return Item.model_validate(data)

    return build

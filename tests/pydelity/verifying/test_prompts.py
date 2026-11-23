"""Tests for page-break verification's prompts: what each page's text says about it."""

# Standard Library
from collections.abc import Callable

# Package Library
from pydelity.extracting.schemas import Item, PageFile
from pydelity.verifying.prompts import judge_break
from pydelity.verifying.schemas import BreakContext


def test_right_to_left_and_vertical_pages_state_their_direction_and_column_order(
    break_context: Callable[..., BreakContext],
    page_file: Callable[..., PageFile],
    page_item: Callable[..., Item],
) -> None:
    """Each page's text gives the direction the survey found and its column order.

    The earlier page is written right to left and the later page in vertical
    columns read from right to left. Text in any script is sent as it is, and no
    page is said to be written left to right.
    """

    earlier = page_file(
        2,
        page_item("p0002-001", language="ar", text="ويستمر النص في الصفحة التالية"),
        writing_direction="rtl",
    )
    later = page_file(
        3,
        page_item("p0003-001", language="ja", text="次の頁に続く文章"),
        column_order="right_to_left",
        writing_direction="ttb",
    )

    prompts = judge_break(break_context(), earlier=earlier, later=later)

    assert "The survey found the page written right to left." in prompts.earlier_text
    assert "vertical columns" not in prompts.earlier_text
    assert "ويستمر النص في الصفحة التالية" in prompts.earlier_text
    assert (
        "The survey found the page written top to bottom, in vertical columns. "
        "Page extraction read its vertical columns from right to left."
        in prompts.later_text
    )
    assert "次の頁に続く文章" in prompts.later_text
    for text in (prompts.earlier_text, prompts.later_text, prompts.system_message):
        assert "left to right" not in text

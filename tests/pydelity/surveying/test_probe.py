"""Tests for the survey's probe: the facts measured from a PDF without a model.

Each test measures one committed public-domain PDF (or a copy made from one), chosen
for the kind of document it stands for, and checks the facts the survey relies on.
"""

# Standard Library
from collections.abc import Callable
from pathlib import Path

# Third Party Library
import pymupdf
import pytest

# Package Library
from pydelity.surveying.probe import probe_pdf
from pydelity.surveying.schemas import Facts


def test_arabic_two_column_pages_read_right_to_left(
    facts_of: Callable[[str], Facts],
) -> None:
    """Arabic text in columns gives right-to-left pages with a good text layer."""

    facts = facts_of("irs_pub1_arabic.pdf")

    assert [page.direction.inline for page in facts.pages] == ["rtl", "rtl"]
    assert {page.text.quality for page in facts.pages} == {"good"}
    assert facts.bookmarks == []
    assert facts.structure is not None
    assert facts.structure.tagged
    assert facts.structure.quality == "good"


def test_japanese_vertical_writing_page_label_and_signature_field(
    facts_of: Callable[[str], Facts],
) -> None:
    """Vertical Japanese text, a page label and a signature field are measured."""

    facts = facts_of("japan_official_gazette_2019_extra_9.pdf")
    page = facts.pages[0]

    assert page.direction.vertical_share >= 0.5
    assert page.text.quality == "good"
    assert page.printed_number is not None
    assert (page.printed_number.value, page.printed_number.source) == (1, "page_label")
    assert facts.form_fields is not None
    assert [field.type for field in facts.form_fields] == ["signature"]
    assert facts.structure is not None
    assert (facts.structure.tagged, facts.structure.quality) == (False, "none")


def test_sideways_tables_on_upright_pages_report_their_turn(
    facts_of: Callable[[str], Facts],
) -> None:
    """Text printed sideways on pages with rotation 0 reports a 90-degree turn.

    The PDF's page labels give the printed numbers, and its running lines repeat in
    the top and bottom bands with their digits treated alike.
    """

    facts = facts_of("caps_english_hl_pages_28_35.pdf")

    for page in facts.pages:
        assert page.rotation_attribute == 0
        assert (page.orientation.dominant, page.orientation.confident) == (90, True)
    numbers = [page.printed_number for page in facts.pages]
    assert [number.value for number in numbers if number] == list(range(23, 31))
    assert {number.source for number in numbers if number} == {"page_label"}
    assert [
        (block.first_page_index, block.last_page_index, block.offset, block.style)
        for block in facts.page_numbering
    ] == [(0, 7, 23, "arabic")]
    bands = {line.normalized: line.band for line in facts.repeated_lines}
    assert bands["#"] == "bottom"
    assert bands["english home language grades r-#"] == "top"
    assert facts.bookmarks == []
    assert facts.structure is not None
    assert facts.structure.tagged is False


def test_scanned_pages_have_no_text_layer(facts_of: Callable[[str], Facts]) -> None:
    """Pages that are only images have no text, direction, angle or page number."""

    facts = facts_of("irs_form_1040a_1965_scan.pdf")

    for page in facts.pages:
        assert (page.text.quality, page.text.chars) == ("none", 0)
        assert page.direction.inline == "none"
        assert (page.orientation.dominant, page.orientation.confident) == (None, False)
        assert page.printed_number is None
    assert facts.repeated_lines == []
    assert facts.page_numbering == []


def test_bookmarks_and_printed_page_numbers_are_read(
    facts_of: Callable[[str], Facts],
) -> None:
    """A tagged PDF's bookmarks resolve to pages, and printed numbers to an offset."""

    facts = facts_of("irs_w9_instructions.pdf")

    assert facts.bookmarks is not None
    assert len(facts.bookmarks) == 22
    assert (facts.bookmarks[0].title, facts.bookmarks[0].page_index) == (
        "Future Developments",
        0,
    )
    assert all(mark.page_index is not None for mark in facts.bookmarks)
    numbers = {
        page.index: (page.printed_number.value, page.printed_number.source)
        for page in facts.pages
        if page.printed_number is not None
    }
    assert numbers == {index: (index + 1, "text") for index in range(1, 7)}
    assert [
        (block.first_page_index, block.last_page_index, block.offset)
        for block in facts.page_numbering
    ] == [(1, 6, 1)]
    assert facts.structure is not None
    assert facts.structure.quality == "good"


def test_filled_form_fields_give_their_values_and_checkbox_states(
    pdf_path: Callable[[str], Path], tmp_path: Path
) -> None:
    """A filled copy of a fillable form gives each field's value and checked state.

    The form also has an XFA part, a running header with page numbers, and a short
    sideways line on its first page, whose rotation attribute is 0.
    """

    document = pymupdf.open(pdf_path("irs_form_w9.pdf"))
    # Widgets stay usable only while their page object is alive.
    first_page = document[0]
    widgets = list(first_page.widgets())
    text_field = next(
        w for w in widgets if w.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT
    )
    checkbox = next(
        w for w in widgets if w.field_type == pymupdf.PDF_WIDGET_TYPE_CHECKBOX
    )
    text_field.field_value = "Jordan Example"
    text_field.update()
    checkbox.field_value = checkbox.on_state()
    checkbox.update()
    filled = tmp_path / "filled_w9.pdf"
    document.save(filled)
    document.close()

    facts = probe_pdf(filled)

    assert facts.form is not None
    assert (facts.form.has_acroform, facts.form.has_xfa) == (True, True)
    assert facts.form_fields is not None
    fields = {field.name: field for field in facts.form_fields}
    assert fields[text_field.field_name].value == "Jordan Example"
    assert fields[checkbox.field_name].checked is True
    boxes = [field for field in facts.form_fields if field.type == "checkbox"]
    assert len(boxes) == 8
    assert sum(1 for box in boxes if box.checked) == 1
    assert sum(1 for field in facts.form_fields if field.type == "text") == 15
    first = facts.pages[0]
    assert first.rotation_attribute == 0
    assert first.orientation.chars_by_angle["90"] > 0
    assert first.orientation.dominant == 0
    repeated = {line.normalized: line for line in facts.repeated_lines}
    assert repeated["page #"].pages == [1, 2, 3, 4, 5]
    assert repeated["page #"].band == "top"


def test_unreadable_characters_make_a_page_garbled(tmp_path: Path) -> None:
    """A page whose text is mostly characters with no readable form is garbled."""

    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 100), "One readable line.", fontname="helv")
    page.insert_text((72, 140), "\x01\x02\x03\x04\x05\x06\x07", fontname="helv")
    path = tmp_path / "garbled.pdf"
    document.save(path)
    document.close()

    text = probe_pdf(path).pages[0].text

    unreadable = (
        text.control_chars
        + text.private_use_chars
        + text.replacement_chars
        + text.unassigned_chars
    )
    assert text.quality == "garbled"
    assert unreadable >= 7


def test_a_fact_that_cannot_be_read_is_null_with_a_probe_error(
    monkeypatch: pytest.MonkeyPatch, pdf_path: Callable[[str], Path]
) -> None:
    """When reading the bookmarks raises, they are null and the error is recorded.

    PyMuPDF raises on some malformed PDFs; the test makes it raise for a sound one.
    """

    def broken_toc(self: pymupdf.Document, simple: bool = True) -> list:
        """Fail as PyMuPDF does on an outline it cannot read."""

        raise RuntimeError("cannot read the outline")

    monkeypatch.setattr(pymupdf.Document, "get_toc", broken_toc)

    facts = probe_pdf(pdf_path("irs_w9_instructions.pdf"))

    assert facts.bookmarks is None
    assert [(error.fact, error.message) for error in facts.probe_errors] == [
        ("bookmarks", "RuntimeError: cannot read the outline")
    ]
    assert facts.form_fields == []
    assert facts.structure is not None

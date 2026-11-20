"""Tests for the survey's probe: the facts measured from a PDF without a model.

Most tests measure one committed public-domain PDF (or a copy made from one), chosen
for the kind of document it stands for, and check the facts the survey relies on.
The others build a small PDF with only the feature they check.
"""

# Standard Library
from collections.abc import Callable
from pathlib import Path

# Third Party Library
import pymupdf
import pytest

# Package Library
from pydelity.surveying.probe import probe_pdf
from pydelity.surveying.schemas import Bookmark, Facts, PrintedNumber, StructureFacts


def _new_object(*, document: pymupdf.Document, source: str) -> int:
    """Add an object to a PDF.

    Parameters
    ----------
    document
        The open PDF.
    source
        The object's source, such as ``<</Type/StructElem>>`` or ``[3 0 R]``.

    Returns
    -------
    int
        The new object's number.
    """

    xref = document.get_new_xref()
    document.update_object(xref, source)
    return xref


def _save_radio_group(*, path: Path, shown: tuple[str, str]) -> None:
    """Save a one-page PDF with a radio group of two buttons whose value is ``B``.

    Parameters
    ----------
    path
        Where to save the PDF.
    shown
        The state each button shows (its ``AS``): ``A`` or ``Off`` for the first,
        ``B`` or ``Off`` for the second. Each button has an on state named ``A``
        or ``B`` and an off state.
    """

    document = pymupdf.open()
    page = document.new_page()
    appearance = _new_object(document=document, source="<<>>")
    document.update_stream(appearance, b"")
    group = _new_object(document=document, source="<<>>")
    buttons = [
        _new_object(
            document=document,
            source=(
                f"<</Type/Annot/Subtype/Widget/Parent {group} 0 R/P {page.xref} 0 R"
                f"/Rect [72 {top} 90 {top + 18}]/F 4/AS/{state_shown}"
                f"/AP <</N <</{state} {appearance} 0 R/Off {appearance} 0 R>>>>>>"
            ),
        )
        for state, state_shown, top in (
            ("A", shown[0], 72),
            ("B", shown[1], 112),
        )
    ]
    kids = " ".join(f"{button} 0 R" for button in buttons)
    # Field flags 49152 make the group a set of radio buttons, one of which is on.
    document.update_object(group, f"<</FT/Btn/Ff 49152/T(choice)/V/B/Kids [{kids}]>>")
    document.xref_set_key(page.xref, "Annots", f"[{kids}]")
    document.xref_set_key(
        document.pdf_catalog(), "AcroForm", f"<</Fields [{group} 0 R]>>"
    )
    document.save(path)
    document.close()


def _save_tagged_pdf(
    *,
    indirect_kids: bool = False,
    paragraphs: list[int],
    path: Path,
    text_pages: set[int],
) -> None:
    """Save a tagged PDF whose structure tree is one Document element of paragraphs.

    Parameters
    ----------
    indirect_kids
        Whether the Document element's ``K`` entry refers to a separate array object
        that lists its kids, instead of listing them itself.
    paragraphs
        How many paragraph (``P``) elements each page has, in page order. Each one
        names its page and holds one marked-content ID.
    path
        Where to save the PDF.
    text_pages
        The indexes of the pages that get a line of text.
    """

    document = pymupdf.open()
    page_xrefs = []
    for index in range(len(paragraphs)):
        page = document.new_page()
        if index in text_pages:
            page.insert_text((72, 100), "A line of body text.", fontname="helv")
        page_xrefs.append(page.xref)

    root = _new_object(document=document, source="<<>>")
    top = _new_object(document=document, source="<<>>")
    references = []
    for page_xref, count in zip(page_xrefs, paragraphs, strict=True):
        for number in range(count):
            paragraph = _new_object(
                document=document,
                source=(
                    f"<</Type/StructElem/S/P/P {top} 0 R"
                    f"/Pg {page_xref} 0 R/K {number}>>"
                ),
            )
            references.append(f"{paragraph} 0 R")
    kids = f"[{' '.join(references)}]"
    if indirect_kids:
        kids = f"{_new_object(document=document, source=kids)} 0 R"

    document.update_object(
        top, f"<</Type/StructElem/S/Document/P {root} 0 R/K {kids}>>"
    )
    document.update_object(root, f"<</Type/StructTreeRoot/K {top} 0 R>>")
    document.xref_set_key(document.pdf_catalog(), "StructTreeRoot", f"{root} 0 R")
    document.save(path)
    document.close()


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


def test_a_damaged_page_label_tree_counts_as_no_labels(tmp_path: Path) -> None:
    """A page-label tree PyMuPDF cannot read leaves the numbers to the page text.

    The tree lists page 0 as the start of two ranges, which makes PyMuPDF raise
    while it sorts them. The pages' printed numbers then come from their text.
    """

    document = pymupdf.open()
    for number in (12, 13, 14):
        page = document.new_page()
        page.insert_text(
            (72, 300), "Body text that changes on each page.", fontname="helv"
        )
        page.insert_text((290, 820), str(number), fontname="helv")
    document.xref_set_key(
        document.pdf_catalog(), "PageLabels", "<</Nums [0 <</S/D>> 0 <</S/r>>]>>"
    )
    path = tmp_path / "damaged_labels.pdf"
    document.save(path)
    document.close()

    facts = probe_pdf(path)

    numbers = [page.printed_number for page in facts.pages]
    assert [(n.value, n.source) for n in numbers if n] == [
        (12, "text"),
        (13, "text"),
        (14, "text"),
    ]
    assert [
        (block.first_page_index, block.last_page_index, block.offset)
        for block in facts.page_numbering
    ] == [(0, 2, 12)]
    assert facts.probe_errors == []


def test_checked_checkbox_without_appearances_is_read_as_checked(
    tmp_path: Path,
) -> None:
    """A checkbox with no appearances is checked when its entries say it is on.

    The widget's shown state (``AS``) and its field's value (``V``) are both
    ``Yes``, and the widget has no appearance streams that name an on state.
    """

    document = pymupdf.open()
    page = document.new_page()
    checkbox = pymupdf.Widget()
    checkbox.field_name = "agree"
    checkbox.field_type = pymupdf.PDF_WIDGET_TYPE_CHECKBOX
    checkbox.field_value = True
    checkbox.rect = pymupdf.Rect(72, 72, 90, 90)
    page.add_widget(checkbox)
    document.xref_set_key(checkbox.xref, "AP", "null")
    path = tmp_path / "checkbox_without_appearances.pdf"
    document.save(path)
    document.close()

    facts = probe_pdf(path)

    assert facts.form_fields is not None
    assert [
        (field.name, field.type, field.checked, field.value)
        for field in facts.form_fields
    ] == [("agree", "checkbox", True, "Yes")]
    assert facts.probe_errors == []


def test_form_field_that_cannot_be_read_is_left_out_with_a_probe_error(
    tmp_path: Path,
) -> None:
    """An unreadable form field is named in a probe error, and the others are kept.

    The second field's default appearance gives a font size that is not a number,
    which makes PyMuPDF raise while it reads that field.
    """

    document = pymupdf.open()
    page = document.new_page()
    widgets = []
    for top, name, value in ((72, "first_name", "Ada"), (112, "last_name", "Lee")):
        widget = pymupdf.Widget()
        widget.field_name = name
        widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
        widget.field_value = value
        widget.rect = pymupdf.Rect(72, top, 272, top + 20)
        page.add_widget(widget)
        widgets.append(widget)
    document.xref_set_key(widgets[1].xref, "DA", "(/Helv twelve Tf 0 g)")
    path = tmp_path / "unreadable_field.pdf"
    document.save(path)
    document.close()

    facts = probe_pdf(path)

    assert facts.form is not None
    assert facts.form_fields is not None
    assert [(field.name, field.value) for field in facts.form_fields] == [
        ("first_name", "Ada")
    ]
    assert len(facts.probe_errors) == 1
    assert facts.probe_errors[0].fact == "form"
    assert facts.probe_errors[0].message.startswith("Field last_name: ")


def test_letter_page_labels_give_no_page_number(tmp_path: Path) -> None:
    """Page labels numbered with letters are not read as roman numerals.

    The first page's label is ``C`` (upper-case letters starting at 3) and the
    second page's is ``i`` (lower-case letters starting at 9).
    """

    document = pymupdf.open()
    for _ in range(2):
        document.new_page()
    document.xref_set_key(
        document.pdf_catalog(),
        "PageLabels",
        "<</Nums [0 <</S/A/St 3>> 1 <</S/a/St 9>>]>>",
    )
    path = tmp_path / "letter_labels.pdf"
    document.save(path)
    document.close()

    facts = probe_pdf(path)

    assert [page.printed_number for page in facts.pages] == [
        PrintedNumber(source="page_label", style="label", text="C", value=None),
        PrintedNumber(source="page_label", style="label", text="i", value=None),
    ]


def test_outline_with_a_cycle_keeps_the_bookmarks_before_it(tmp_path: Path) -> None:
    """An outline whose last entry links back to its first keeps the entries read."""

    document = pymupdf.open()
    for _ in range(3):
        document.new_page()
    document.set_toc([[1, "Intro", 1], [1, "Methods", 2], [1, "Results", 3]])
    catalog = document.pdf_catalog()
    first = document.xref_get_key(catalog, "Outlines/First")[1]
    last = int(document.xref_get_key(catalog, "Outlines/Last")[1].split()[0])
    document.xref_set_key(last, "Next", first)
    path = tmp_path / "outline_cycle.pdf"
    document.save(path)
    document.close()

    facts = probe_pdf(path)

    assert facts.bookmarks == [
        Bookmark(level=1, page_index=0, title="Intro"),
        Bookmark(level=1, page_index=1, title="Methods"),
        Bookmark(level=1, page_index=2, title="Results"),
    ]
    assert facts.probe_errors == []


@pytest.mark.parametrize(
    ("shown", "checked"),
    [(("Off", "Off"), [False, True]), (("A", "Off"), [True, False])],
    ids=["all-off", "first-on"],
)
def test_radio_group_value_turns_on_its_button_only_when_none_shows_on(
    checked: list[bool], shown: tuple[str, str], tmp_path: Path
) -> None:
    """A radio group's value turns on the button it names only if none shows on.

    The group's value is the second button's on state. When both buttons show
    their off state, as a group can be saved, the second button is on. When the
    first button shows on, as a filler leaves it after setting the value without
    updating the appearances, the page shows the first button on, and only it is
    read as checked. Both buttons report the group's value.
    """

    path = tmp_path / "radio_group.pdf"
    _save_radio_group(path=path, shown=shown)

    facts = probe_pdf(path)

    assert facts.form_fields is not None
    assert [
        (field.name, field.type, field.checked, field.value)
        for field in facts.form_fields
    ] == [("choice", "radio", checked[0], "B"), ("choice", "radio", checked[1], "B")]
    assert facts.probe_errors == []


def test_structure_kids_stored_in_a_separate_array_are_counted(
    tmp_path: Path,
) -> None:
    """An element whose kids sit in a separate array object has those kids counted."""

    path = tmp_path / "separate_kids_array.pdf"
    _save_tagged_pdf(indirect_kids=True, paragraphs=[3], path=path, text_pages={0})

    structure = probe_pdf(path).structure

    assert structure is not None
    assert (
        structure.element_count,
        structure.pages_with_tagged_content,
        structure.type_counts,
    ) == (4, 1, {"Document": 1, "P": 3})


def test_structure_walk_cut_short_is_rated_on_the_pages_it_reached(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A walk stopped at the element cap does not count unreached pages as untagged.

    With a cap of 11 elements, the walk counts the Document element and the five
    paragraphs on each of the first two pages, then stops before the third page.
    Both pages it reached have tagged content, so the tags are good.
    """

    monkeypatch.setattr("pydelity.surveying.probe.STRUCTURE_ELEMENT_CAP", 11)
    path = tmp_path / "capped_structure.pdf"
    _save_tagged_pdf(paragraphs=[5, 5, 5], path=path, text_pages={0, 1, 2})

    structure = probe_pdf(path).structure

    assert structure == StructureFacts(
        element_count=11,
        marked=False,
        pages_with_tagged_content=2,
        quality="good",
        tagged=True,
        truncated=True,
        type_counts={"Document": 1, "P": 10},
    )


def test_tagged_pages_without_text_do_not_count_toward_coverage(
    tmp_path: Path,
) -> None:
    """Tags on a page without text do not cover a page with text.

    The first page has text and no tags. The second has ten tagged paragraphs and
    no text. The only page with text is not covered, so the tags are partial.
    """

    path = tmp_path / "tags_on_a_blank_page.pdf"
    _save_tagged_pdf(paragraphs=[0, 10], path=path, text_pages={0})

    facts = probe_pdf(path)

    assert [page.text.quality for page in facts.pages] == ["good", "none"]
    assert facts.structure is not None
    assert (
        facts.structure.pages_with_tagged_content,
        facts.structure.quality,
    ) == (1, "partial")

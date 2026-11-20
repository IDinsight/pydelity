"""The survey's probe: the facts about a PDF that can be measured without a model.

The probe reads the text layer, page labels, bookmarks, form fields and structure tags
with PyMuPDF. It relies on Unicode properties and PDF structure, not word lists, so it
works the same way for any language or type of document. Every threshold is a named
constant below. On a malformed PDF, reading the bookmarks, the form or the structure
tree can fail. The probe then sets that fact to ``None``, records a `ProbeError` and
continues. A form field that cannot be read is left out, with a `ProbeError` naming it,
and the other fields are kept.
"""

# Standard Library
import math
import re
import unicodedata

from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

# Third Party Library
import pymupdf

# Package Library
from pydelity.surveying.schemas import (
    Angle,
    Band,
    Bookmark,
    DirectionFacts,
    Facts,
    FieldType,
    FormField,
    FormInfo,
    InlineDirection,
    NumberingRange,
    OrientationFacts,
    PageFacts,
    PrintedNumber,
    ProbeError,
    ProbeFact,
    RepeatedLine,
    StructureFacts,
    StructureQuality,
    TextFacts,
    TextQuality,
)
from pydelity.utils.pdf import TEXT_FLAGS
from pydelity.utils.text import normalize_line

# A page's top band, and its bottom band, as a share of the displayed page's height.
# Printed page numbers are looked for there, and repeated lines are placed by it.
BAND_SHARE = 0.1

# A page's inline direction is right-to-left (or left-to-right) when right-to-left (or
# left-to-right) letters reach this share of its letters.
DIRECTION_DOMINANT_SHARE = 0.7

# A page's text is garbled when control, private-use, unassigned and replacement
# characters together reach this share of its characters.
GARBLED_SHARE = 0.1

# The measured orientation is confident when the most common angle has at least this
# share of the characters on horizontal lines, and the page has at least
# `ORIENTATION_MIN_CHARS` of them.
ORIENTATION_DOMINANT_SHARE = 0.8

# The fewest characters on horizontal lines that a confident orientation needs.
ORIENTATION_MIN_CHARS = 20

# Increase this whenever a measurement rule, a measurement constant or the summary
# format changes, so an upgraded pydelity measures again instead of reusing old facts.
PROBE_VERSION = 1

# At most this many repeated lines are kept, most frequent first.
REPEATED_MAX_LINES = 1000

# A line is repeated when it appears on at least this many pages and on at least
# `REPEATED_MIN_SHARE` of the pages.
REPEATED_MIN_PAGES = 3

# The share of the pages a repeated line must appear on.
REPEATED_MIN_SHARE = 0.05

# In a PDF of 2 or 3 pages, a line on this many pages is repeated.
REPEATED_SMALL_PDF_MIN_PAGES = 2

# The structure tree is counted up to this many elements; beyond it, `truncated` is set.
STRUCTURE_ELEMENT_CAP = 20_000

# Tagged content must cover at least this share of the pages with text for the
# structure tags to be good rather than partial.
STRUCTURE_GOOD_PAGE_SHARE = 0.9

# Element types that only group other elements. Structure tags made of these alone,
# or of fewer than `STRUCTURE_MIN_ELEMENTS` elements, are poor.
STRUCTURE_GROUPING_TYPES = frozenset(
    {"Art", "Div", "Document", "NonStruct", "Part", "Sect", "Span"}
)

STRUCTURE_MIN_ELEMENTS = 10

# Items of a PDF array as PyMuPDF prints it: references, inline dictionaries and
# integers (marked-content IDs).
_ARRAY_ITEM = re.compile(r"(\d+)\s+\d+\s+R|(<<.*?>>)|(-?\d+)", re.DOTALL)

# Form field types, as PyMuPDF names them, and as pdf_facts.json records them.
_FIELD_TYPES: dict[str, FieldType] = {
    "Button": "button",
    "CheckBox": "checkbox",
    "ComboBox": "combobox",
    "ListBox": "listbox",
    "RadioButton": "radio",
    "Signature": "signature",
    "Text": "text",
}

# How long an error message from a malformed PDF may be.
_MAX_MESSAGE_CHARS = 200

# How many role-map steps lead from a custom structure type to a standard one, at most.
_MAX_ROLE_STEPS = 10

# Page-label numbering styles that give a page number: decimal digits, and upper- or
# lower-case roman numerals. Letter styles (A, a) and labels with no style give none.
_NUMBERED_LABEL_STYLES = frozenset({"D", "R", "r"})

# A line's number or word parts: runs of decimal digits (any script) or of letters.
_NUMBER_PARTS = re.compile(r"\d+|[^\W\d_]+")

# A page label's number at its end, after any prefix: decimal digits, or letters (a
# roman numeral) after a character that is not a letter, as in "Page 12" or "A-iv".
_LABEL_NUMBER = re.compile(r"(?:.*\W)?([^\W\d_]+)|.*?(\d+)")

# The page reference of an inline marked-content or object reference dictionary.
_PAGE_REFERENCE = re.compile(r"/Pg\s+(\d+)\s+\d+\s+R")

# A key of a dictionary whose value is a reference, as PyMuPDF prints the dictionary,
# such as the on and off states of a button's appearances: /Yes 12 0 R.
_REFERENCE_KEY = re.compile(r"/([^\s/<>\[\]()]+)\s+\d+\s+\d+\s+R")

# A pair in an inline role-map dictionary: /CustomType /StandardType.
_ROLE_MAP_PAIR = re.compile(r"/([^\s/<>\[\]()]+)\s*/([^\s/<>\[\]()]+)")

# A roman numeral from 1 to 3999.
_ROMAN = re.compile(r"M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})")

_ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


@dataclass(frozen=True)
class _Line:
    """One line of a page's text layer, as the probe needs it.

    Attributes
    ----------
    angle
        The baseline angle on the displayed page, or ``None`` for vertical writing.
    band
        Where the line sits on the displayed page.
    chars
        Characters other than whitespace.
    edge_distance
        Distance in points from the line to the nearer of the page's top and bottom.
    text
        The line's text, stripped.
    """

    angle: Angle | None
    band: Band
    chars: int
    edge_distance: float
    text: str


@dataclass
class _StructureWalk:
    """What a walk of the structure tree found.

    Attributes
    ----------
    pages
        The pages with content linked to the tree.
    truncated
        Whether the walk stopped at `STRUCTURE_ELEMENT_CAP`.
    types
        Elements by standard type.
    visited
        The objects already walked, so a cycle in a malformed tree ends.
    """

    pages: set[int] = field(default_factory=set)
    truncated: bool = False
    types: Counter[str] = field(default_factory=Counter)
    visited: set[int] = field(default_factory=set)


def _band(*, page_height: float, rect: pymupdf.Rect) -> Band:
    """Place a line in the top band, the bottom band or between them.

    Parameters
    ----------
    page_height
        The displayed page's height.
    rect
        The line's box on the displayed page.

    Returns
    -------
    Band
        Where the line's middle sits.
    """

    middle = (rect.y0 + rect.y1) / 2
    if middle <= page_height * BAND_SHARE:
        return "top"
    if middle >= page_height * (1 - BAND_SHARE):
        return "bottom"
    return "middle"


def _bookmarks(document: pymupdf.Document) -> list[Bookmark]:
    """Read the PDF's bookmarks (outline).

    Parameters
    ----------
    document
        The open PDF.

    Returns
    -------
    list[Bookmark]
        The bookmarks in order; empty when the PDF has none. An outline whose links
        lead back to an entry already read gives the bookmarks before that entry.
    """

    _cut_outline_cycle(document)
    return [
        Bookmark(level=level, page_index=page - 1 if page >= 1 else None, title=title)
        for level, title, page in document.get_toc(simple=True)
    ]


def _button_state(
    *, document: pymupdf.Document, field_type: FieldType, xref: int
) -> tuple[bool, str | None]:
    """Read whether a checkbox or radio button is on, and its field's value.

    Both come from the PDF's entries, not from the button's appearances, which a
    filled form can lack: ``AS`` is the state the button shows, and ``V``, on the
    button or on the field it belongs to, is the field's value.

    Parameters
    ----------
    document
        The open PDF.
    field_type
        ``checkbox`` or ``radio``.
    xref
        The button's object number.

    Returns
    -------
    tuple[bool, str | None]
        Whether the button is on, and the field's value, such as ``Yes`` or ``Off``.
    """

    shown = _name_value(document=document, key="AS", xref=xref)
    value = _name_value(document=document, key="V", xref=xref)
    if value is None:
        value = _name_value(document=document, key="Parent/V", xref=xref)
    if field_type == "checkbox":
        state = shown if shown is not None else value
        return state not in {None, "Off"}, value if value is not None else shown

    on = shown not in {None, "Off"}
    if not on and value not in {None, "Off"}:
        # A radio group can be saved with every button showing off while its value
        # names one button's on state.
        on = value in _on_states(document=document, xref=xref)
    return on, value


def _choose_text_numbers(
    *, lines_by_page: list[list[_Line]], pages: list[PageFacts]
) -> None:
    """Find printed page numbers in the text of pages whose label gives no number.

    A candidate is a line in the top or bottom band that is a single number with
    only non-letter decoration around it. When a page has several candidates, the
    one chosen has the style and offset (printed number minus page index) that the
    most pages share. This way, page numbers at the bottom are chosen over a list
    marker near the top. On a tie, the line nearest the page's edge is chosen.

    Parameters
    ----------
    lines_by_page
        Each page's lines, in page order.
    pages
        The page facts, in page order; updated in place.
    """

    candidates = [
        []
        if page.printed_number is not None and page.printed_number.value is not None
        else _number_candidates(lines)
        for page, lines in zip(pages, lines_by_page, strict=True)
    ]
    agreement: Counter[tuple[str, int]] = Counter()
    for page, found in zip(pages, candidates, strict=True):
        agreement.update({_offset_key(index=page.index, number=n) for _, n in found})

    for page, found in zip(pages, candidates, strict=True):
        scored = [
            (-agreement[_offset_key(index=page.index, number=number)], distance, order)
            for order, (distance, number) in enumerate(found)
        ]
        if scored:
            page.printed_number = found[min(scored)[2]][1]


def _common_band(bands: list[Band]) -> Band:
    """Return the band a repeated line sits in most often (top first on a tie).

    Parameters
    ----------
    bands
        The band of each occurrence.

    Returns
    -------
    Band
        The most common band.
    """

    counts = Counter(bands)
    order: tuple[Band, ...] = ("top", "bottom", "middle")
    return max(order, key=lambda band: counts[band])


def _cut_outline_cycle(document: pymupdf.Document) -> None:
    """End the outline at the first link back to an entry already read.

    PyMuPDF reads no bookmarks at all from an outline whose links form a cycle. The
    outline is walked in reading order: each entry, then its children, then its next
    sibling. At the first link to an entry already read, that link and every link
    not yet followed are removed, so the outline ends there. Only the open document
    changes; the file is not written.

    Parameters
    ----------
    document
        The open PDF; its outline is changed in place when it has a cycle.
    """

    kind, value = document.xref_get_key(document.pdf_catalog(), "Outlines")
    if kind != "xref":
        return
    seen: set[int] = set()
    links = [(int(value.split(maxsplit=1)[0]), "First")]
    while links:
        holder, key = links.pop()
        kind, value = document.xref_get_key(holder, key)
        if kind != "xref":
            continue
        entry = int(value.split(maxsplit=1)[0])
        if entry in seen:
            for open_holder, open_key in [(holder, key), *links]:
                document.xref_set_key(open_holder, open_key, "null")
            return
        seen.add(entry)
        # Pushed in this order so that the children are walked before the sibling.
        links += [(entry, "Next"), (entry, "First")]


def _direction(*, text: str, vertical_share: float) -> DirectionFacts:
    """Measure a page's inline direction from the Unicode classes of its letters.

    Parameters
    ----------
    text
        The page's text.
    vertical_share
        The share of the page's characters in vertical writing mode.

    Returns
    -------
    DirectionFacts
        The inline direction and the vertical share.
    """

    classes = Counter(unicodedata.bidirectional(char) for char in text)
    right_to_left = classes["R"] + classes["AL"]
    left_to_right = classes["L"]
    strong = right_to_left + left_to_right
    inline: InlineDirection
    if strong == 0:
        inline = "none"
    elif right_to_left >= strong * DIRECTION_DOMINANT_SHARE:
        inline = "rtl"
    elif left_to_right >= strong * DIRECTION_DOMINANT_SHARE:
        inline = "ltr"
    else:
        inline = "mixed"
    return DirectionFacts(inline=inline, vertical_share=round(vertical_share, 4))


def _displayed_angle(*, direction: tuple[float, float], rotation: int) -> Angle:
    """Turn a line's writing direction into its baseline angle on the displayed page.

    PyMuPDF gives the direction in the unrotated page's coordinates (y pointing down);
    the page's rotation attribute turns the page clockwise for display.

    Parameters
    ----------
    direction
        The line's direction vector, as PyMuPDF reports it.
    rotation
        The page's rotation attribute, in degrees clockwise.

    Returns
    -------
    Angle
        The baseline angle counterclockwise, rounded to a quarter turn.

    Examples
    --------
    >>> _displayed_angle(direction=(0.0, -1.0), rotation=0)  # reads bottom to top
    90
    """

    unrotated = math.degrees(math.atan2(-direction[1], direction[0]))
    displayed = (round((unrotated - rotation) / 90) * 90) % 360
    angles: dict[int, Angle] = {0: 0, 90: 90, 180: 180, 270: 270}
    return angles[displayed]


def _element_kids(*, document: pymupdf.Document, xref: int) -> list[tuple[str, str]]:
    """Read a structure element's kids, following a ``K`` entry that refers to an array.

    Parameters
    ----------
    document
        The open PDF.
    xref
        The element's object number, or the structure tree root's.

    Returns
    -------
    list[tuple[str, str]]
        The kids, as `_kids` gives them.
    """

    kind, value = document.xref_get_key(xref, "K")
    if kind == "xref":
        target = int(value.split(maxsplit=1)[0])
        source = document.xref_object(target, compressed=True).strip()
        if source.startswith("["):
            return _kids(kind="array", value=source)
    return _kids(kind=kind, value=value)


def _error_message(error: Exception, *, about: str = "") -> str:
    """Describe an error from a malformed PDF briefly.

    Parameters
    ----------
    error
        The error raised while reading.
    about
        What could not be read, put before the error, such as ``Field name: ``.

    Returns
    -------
    str
        The error's type and message, cut to `_MAX_MESSAGE_CHARS` characters.
    """

    message = f"{about}{type(error).__name__}: {error}".strip()
    if len(message) > _MAX_MESSAGE_CHARS:
        message = message[: _MAX_MESSAGE_CHARS - 3] + "..."
    return message


def _field_error(
    *, document: pymupdf.Document, error: Exception, xref: int
) -> ProbeError:
    """Describe a form field that could not be read, naming it.

    Parameters
    ----------
    document
        The open PDF.
    error
        The error raised while reading the field.
    xref
        The field's widget object number.

    Returns
    -------
    ProbeError
        A ``form`` error naming the field, or its object number when it has no name.
    """

    name = f"object {xref}"
    for key in ("T", "Parent/T"):
        kind, value = document.xref_get_key(xref, key)
        if kind == "string" and value:
            name = value
            break
    return ProbeError(
        fact="form", message=_error_message(error, about=f"Field {name}: ")
    )


def _form(
    document: pymupdf.Document, *, errors: list[ProbeError]
) -> tuple[list[FormField], FormInfo]:
    """Read the PDF's interactive form fields and which kinds of form it holds.

    Each field is read on its own, so a field that cannot be read is left out and
    the others are kept.

    Parameters
    ----------
    document
        The open PDF.
    errors
        The probe errors so far; each field that cannot be read adds one.

    Returns
    -------
    tuple[list[FormField], FormInfo]
        The fields in page order, and the kinds of form.
    """

    catalog = document.pdf_catalog()
    info = FormInfo(
        has_acroform=document.xref_get_key(catalog, "AcroForm")[0] != "null",
        has_xfa=document.xref_get_key(catalog, "AcroForm/XFA")[0] != "null",
    )
    fields = []
    for index in range(len(document)):
        page = document[index]
        for xref, annotation_type, *_ in page.annot_xrefs():
            if annotation_type != pymupdf.PDF_ANNOT_WIDGET:
                continue
            # A malformed field can raise many kinds of exceptions, so catch them all.
            # Only that field is lost.
            try:
                form_field = _form_field(
                    document=document,
                    index=index,
                    page=page,
                    widget=page.load_widget(xref),
                )
            except Exception as error:
                errors.append(_field_error(document=document, error=error, xref=xref))
                continue
            if form_field is not None:
                fields.append(form_field)
    return fields, info


def _form_field(
    *,
    document: pymupdf.Document,
    index: int,
    page: pymupdf.Page,
    widget: pymupdf.Widget,
) -> FormField | None:
    """Describe one form field.

    Parameters
    ----------
    document
        The open PDF, for a button's entries.
    index
        The index of the page the field is on.
    page
        The page the field is on.
    widget
        The field, as PyMuPDF reads it.

    Returns
    -------
    FormField | None
        The field, or ``None`` for a field type pydelity does not record.
    """

    field_type = _FIELD_TYPES.get(widget.field_type_string)
    if field_type is None:
        return None

    checked: bool | None = None
    value = widget.field_value
    if field_type in {"checkbox", "radio"}:
        checked, value = _button_state(
            document=document, field_type=field_type, xref=widget.xref
        )
    options = [
        str(choice[-1]) if isinstance(choice, (list, tuple)) else str(choice)
        for choice in widget.choice_values or []
    ]
    box = pymupdf.Rect(widget.rect) * page.rotation_matrix
    return FormField(
        bbox=(round(box.x0, 2), round(box.y0, 2), round(box.x1, 2), round(box.y1, 2)),
        checked=checked,
        name=widget.field_name or "",
        options=options,
        page_index=index,
        type=field_type,
        value=None if value is None or value == "" else str(value),
    )


def _kids(*, kind: str, value: str) -> list[tuple[str, str]]:
    """Split a structure element's ``K`` entry into its kids.

    Parameters
    ----------
    kind
        The entry's type, as `pymupdf.Document.xref_get_key` reports it.
    value
        The entry's value, as PyMuPDF prints it.

    Returns
    -------
    list[tuple[str, str]]
        Each kid as ``("ref", "<xref>")``, ``("mcid", "<n>")`` or
        ``("dict", "<<...>>")``.
    """

    if kind == "xref":
        return [("ref", value.split(maxsplit=1)[0])]
    if kind == "int":
        return [("mcid", value)]
    if kind == "dict":
        return [("dict", value)]
    if kind != "array":
        return []

    kids = []
    for reference, inline, number in _ARRAY_ITEM.findall(value):
        if reference:
            kids.append(("ref", reference))
        elif inline:
            kids.append(("dict", inline))
        else:
            kids.append(("mcid", number))
    return kids


def _label_number(label: str, *, style: str) -> PrintedNumber:
    """Describe a page label as a printed number.

    A PDF page label is an optional prefix followed by a number in its range's style,
    such as ``12``, ``Page 12`` or ``A-iv``. The number is read from the end of the
    label. Only decimal and roman styles give a number. A letter style, which numbers
    pages ``A``, ``B``, ``C``, and a label with no style give none.

    Parameters
    ----------
    label
        The page's label.
    style
        The numbering style of the label's range: ``D``, ``R``, ``r``, ``A``, ``a``,
        or empty for none.

    Returns
    -------
    PrintedNumber
        An arabic or roman number when the style gives one and the label ends in it,
        otherwise a ``label`` with no value.

    Examples
    --------
    >>> pairs = [("12", "D"), ("Page 12", "D"), ("A-iv", "r"), ("C", "A"), ("X", "")]
    >>> [_label_number(label, style=style).value for label, style in pairs]
    [12, 12, 4, None, None]
    """

    match = _LABEL_NUMBER.fullmatch(label.strip())
    letters, digits = (
        match.groups()
        if match is not None and style in _NUMBERED_LABEL_STYLES
        else (None, None)
    )
    if digits is not None:
        return PrintedNumber(
            source="page_label", style="arabic", text=label, value=int(digits)
        )
    roman = _roman_value(letters or "")
    if roman is not None:
        return PrintedNumber(
            source="page_label", style="roman", text=label, value=roman
        )
    return PrintedNumber(source="page_label", style="label", text=label, value=None)


def _label_styles(document: pymupdf.Document) -> list[str] | None:
    """Find the numbering style of each page's page label.

    Parameters
    ----------
    document
        The open PDF.

    Returns
    -------
    list[str] | None
        Each page's style in page order (``D``, ``R``, ``r``, ``A``, ``a``, or empty
        for none), or ``None`` when the PDF defines no page labels that can be read.
    """

    # A damaged page-label tree can raise many kinds of exceptions, so catch them
    # all. The pages then get their printed numbers from their text.
    try:
        ranges = sorted(
            document.get_page_labels(), key=lambda entry: entry["startpage"]
        )
    except Exception:
        return None
    if not ranges:
        return None

    page_count = len(document)
    styles = [""] * page_count
    for number, entry in enumerate(ranges):
        end = (
            ranges[number + 1]["startpage"] if number + 1 < len(ranges) else page_count
        )
        for index in range(max(entry["startpage"], 0), min(end, page_count)):
            styles[index] = entry.get("style", "")
    return styles


def _lines(page: pymupdf.Page) -> list[_Line]:
    """Read a page's text lines, placed on the displayed page.

    Parameters
    ----------
    page
        The page.

    Returns
    -------
    list[_Line]
        The lines that hold text, in PyMuPDF's reading order.
    """

    height = page.rect.height
    lines = []
    for block in page.get_text("dict", flags=TEXT_FLAGS)["blocks"]:
        for line in block.get("lines", []):
            text = "".join(span["text"] for span in line["spans"]).strip()
            if not text:
                continue
            rect = pymupdf.Rect(line["bbox"]) * page.rotation_matrix
            vertical = line.get("wmode") == 1
            lines.append(
                _Line(
                    angle=None
                    if vertical
                    else _displayed_angle(
                        direction=line["dir"], rotation=page.rotation
                    ),
                    band=_band(page_height=height, rect=rect),
                    chars=sum(1 for char in text if not char.isspace()),
                    edge_distance=min(rect.y0, height - rect.y1),
                    text=text,
                )
            )
    return lines


def _map_types(*, role_map: dict[str, str], types: Counter[str]) -> Counter[str]:
    """Count element types again after following the role map.

    Parameters
    ----------
    role_map
        Standard types by custom type.
    types
        Element counts by the type each element names.

    Returns
    -------
    Counter[str]
        Element counts by standard type.
    """

    mapped: Counter[str] = Counter()
    for name, count in types.items():
        mapped[_standard_type(name=name, role_map=role_map)] += count
    return mapped


def _name_value(*, document: pymupdf.Document, key: str, xref: int) -> str | None:
    """Read a name entry of a PDF object, such as ``AS``, without its slash.

    Parameters
    ----------
    document
        The open PDF.
    key
        The entry's key, or a path of keys such as ``Parent/V``.
    xref
        The object's number.

    Returns
    -------
    str | None
        The name, or ``None`` when the entry is missing or is not a name.
    """

    kind, value = document.xref_get_key(xref, key)
    return value.removeprefix("/") if kind == "name" else None


def _number_candidates(lines: list[_Line]) -> list[tuple[float, PrintedNumber]]:
    """List the lines in a page's top and bottom bands that read as a page number.

    Parameters
    ----------
    lines
        The page's lines.

    Returns
    -------
    list[tuple[float, PrintedNumber]]
        Each candidate with its distance from the page's edge.
    """

    candidates = []
    for line in lines:
        if line.band == "middle":
            continue
        number = _text_number(line.text)
        if number is not None:
            candidates.append((line.edge_distance, number))
    return candidates


def _numbering(pages: list[PageFacts]) -> list[NumberingRange]:
    """Group pages whose printed numbers follow their indexes into ranges.

    Consecutive measured pages with the same style and the same offset (printed number
    minus page index) form one range; pages without a number do not break a range.

    Parameters
    ----------
    pages
        The page facts, in page order.

    Returns
    -------
    list[NumberingRange]
        The ranges, in page order.
    """

    ranges: list[NumberingRange] = []
    for page in pages:
        number = page.printed_number
        if number is None or number.value is None:
            continue
        if number.style == "label":
            continue
        style = number.style
        offset = number.value - page.index
        current = ranges[-1] if ranges else None
        if current is not None and (current.style, current.offset) == (style, offset):
            current.last_page_index = page.index
            current.pages_measured += 1
        else:
            ranges.append(
                NumberingRange(
                    first_page_index=page.index,
                    last_page_index=page.index,
                    offset=offset,
                    pages_measured=1,
                    style=style,
                )
            )
    return ranges


def _offset_key(*, index: int, number: PrintedNumber) -> tuple[str, int]:
    """Return a printed number's style and its offset from the page index.

    Parameters
    ----------
    index
        The page's index.
    number
        The printed number; it has a value.

    Returns
    -------
    tuple[str, int]
        The style and the printed number minus the page index.
    """

    return number.style, (number.value or 0) - index


def _on_states(*, document: pymupdf.Document, xref: int) -> set[str]:
    """Read the on states a button has appearances for: every state but ``Off``.

    Parameters
    ----------
    document
        The open PDF.
    xref
        The button's object number.

    Returns
    -------
    set[str]
        The names of its on states; empty when it has no appearances.
    """

    states: set[str] = set()
    for key in ("AP/N", "AP/D"):
        kind, value = document.xref_get_key(xref, key)
        if kind == "xref":
            target = int(value.split(maxsplit=1)[0])
            if document.xref_is_stream(target):
                # A single appearance, with no states to name.
                continue
            value = document.xref_object(target, compressed=True)
        elif kind != "dict":
            continue
        states.update(_REFERENCE_KEY.findall(value))
    return states - {"Off"}


def _orientation(lines: list[_Line]) -> OrientationFacts:
    """Measure which way a page's text runs, weighting each line by its characters.

    Parameters
    ----------
    lines
        The page's lines; vertical-writing lines are left out.

    Returns
    -------
    OrientationFacts
        Characters by angle, the dominant angle and whether it is confident.
    """

    by_angle: dict[Angle, int] = {0: 0, 90: 0, 180: 0, 270: 0}
    for line in lines:
        if line.angle is not None:
            by_angle[line.angle] += line.chars

    total = sum(by_angle.values())
    dominant: Angle | None = None
    confident = False
    if total:
        dominant = max(by_angle, key=lambda angle: by_angle[angle])
        confident = (
            total >= ORIENTATION_MIN_CHARS
            and by_angle[dominant] >= total * ORIENTATION_DOMINANT_SHARE
        )
    return OrientationFacts(
        chars_by_angle={str(angle): count for angle, count in by_angle.items()},
        confident=confident,
        dominant=dominant,
    )


def _page(
    *, index: int, label_style: str | None, page: pymupdf.Page
) -> tuple[PageFacts, list[_Line]]:
    """Measure one page.

    Parameters
    ----------
    index
        The page's index.
    label_style
        The numbering style of the page's label, or ``None`` when the PDF defines no
        page labels.
    page
        The page.

    Returns
    -------
    tuple[PageFacts, list[_Line]]
        The page's facts, and its lines for the repeated-line count.
    """

    lines = _lines(page)
    text = "\n".join(line.text for line in lines)
    total_chars = sum(line.chars for line in lines)
    vertical_chars = sum(line.chars for line in lines if line.angle is None)
    vertical_share = vertical_chars / total_chars if total_chars else 0.0
    label = _page_label(page) if label_style is not None else ""
    facts = PageFacts(
        direction=_direction(text=text, vertical_share=vertical_share),
        height_pt=round(page.rect.height, 2),
        index=index,
        orientation=_orientation(lines),
        # Use the page label's number if it has one. Otherwise `_choose_text_numbers`
        # looks for the number printed on the page.
        printed_number=_label_number(label, style=label_style or "") if label else None,
        rotation_attribute=page.rotation,
        text=_text_facts(text),
        width_pt=round(page.rect.width, 2),
    )
    return facts, lines


def _page_label(page: pymupdf.Page) -> str:
    """Read a page's label, treating a failure as no label.

    Parameters
    ----------
    page
        The page.

    Returns
    -------
    str
        The label, or an empty string.
    """

    # A damaged page-label tree can raise many kinds of exceptions (PyMuPDF raises
    # TypeError when two entries start on the same page), so catch them all. The
    # page then gets its printed number from its text.
    try:
        return page.get_label()
    except Exception:
        return ""


def _page_of(
    *, document: pymupdf.Document, page_indexes: dict[int, int], xref: int
) -> int | None:
    """Return the page a structure object's ``Pg`` entry points to.

    Parameters
    ----------
    document
        The open PDF.
    page_indexes
        Page indexes by page object number.
    xref
        The structure object.

    Returns
    -------
    int | None
        The page index, or ``None`` without a ``Pg`` entry.
    """

    kind, value = document.xref_get_key(xref, "Pg")
    if kind != "xref":
        return None
    return page_indexes.get(int(value.split(maxsplit=1)[0]))


def _read_fact[T](
    *, errors: list[ProbeError], fact: ProbeFact, read: Callable[[], T]
) -> T | None:
    """Read one fact, recording a failure instead of raising it.

    Parameters
    ----------
    errors
        The probe errors so far; a failure is appended.
    fact
        Which fact is being read.
    read
        Reads the fact.

    Returns
    -------
    T | None
        The fact, or ``None`` when reading it failed.
    """

    try:
        return read()
    # Malformed PDFs raise many kinds of exceptions, so catch them all.
    except Exception as error:
        errors.append(ProbeError(fact=fact, message=_error_message(error)))
        return None


def _repeated_lines(
    *, lines_by_page: list[list[_Line]], page_count: int
) -> tuple[list[RepeatedLine], bool]:
    """Find the lines that repeat across pages.

    A line counts once per page. It is repeated when it appears on at least
    `REPEATED_MIN_PAGES` pages and `REPEATED_MIN_SHARE` of the pages (2 pages in a
    PDF of 2 or 3 pages).

    Parameters
    ----------
    lines_by_page
        Each page's lines, in page order.
    page_count
        The number of pages.

    Returns
    -------
    tuple[list[RepeatedLine], bool]
        The repeated lines, most frequent first and at most `REPEATED_MAX_LINES`,
        and whether more were found.
    """

    occurrences: defaultdict[str, list[tuple[int, _Line]]] = defaultdict(list)
    for index, lines in enumerate(lines_by_page):
        seen = set()
        for line in lines:
            normalized = normalize_line(line.text)
            if normalized and normalized not in seen:
                seen.add(normalized)
                occurrences[normalized].append((index, line))

    minimum = _repeated_minimum(page_count)
    found = [
        (normalized, places)
        for normalized, places in occurrences.items()
        if len(places) >= minimum
    ]
    # Most frequent first; ties by first page, then by text, so IDs are deterministic.
    found.sort(key=lambda item: (-len(item[1]), item[1][0][0], item[0]))
    repeated = [
        RepeatedLine(
            band=_common_band([line.band for _, line in places]),
            id=f"R{number}",
            normalized=normalized,
            pages=[index for index, _ in places],
            text=places[0][1].text,
        )
        for number, (normalized, places) in enumerate(
            found[:REPEATED_MAX_LINES], start=1
        )
    ]
    return repeated, len(found) > REPEATED_MAX_LINES


def _repeated_minimum(page_count: int) -> int:
    """Return how many pages a line must appear on to count as repeated.

    Parameters
    ----------
    page_count
        The number of pages.

    Returns
    -------
    int
        The minimum number of pages; more than the page count for a 1-page PDF.
    """

    if page_count < REPEATED_SMALL_PDF_MIN_PAGES:
        return page_count + 1
    if page_count <= REPEATED_MIN_PAGES:
        return REPEATED_SMALL_PDF_MIN_PAGES
    return max(REPEATED_MIN_PAGES, math.ceil(page_count * REPEATED_MIN_SHARE))


def _role_map(*, document: pymupdf.Document, root: int) -> dict[str, str]:
    """Read the structure tree's role map: custom element types to standard ones.

    Parameters
    ----------
    document
        The open PDF.
    root
        The structure tree root's object number.

    Returns
    -------
    dict[str, str]
        Standard types by custom type, without the leading ``/``.
    """

    kind, value = document.xref_get_key(root, "RoleMap")
    if kind == "dict":
        return dict(_ROLE_MAP_PAIR.findall(value))
    if kind != "xref":
        return {}
    role_map = int(value.split(maxsplit=1)[0])
    return {
        key: document.xref_get_key(role_map, key)[1].lstrip("/")
        for key in document.xref_get_keys(role_map)
    }


def _roman_value(text: str) -> int | None:
    """Read a roman numeral written all in upper or all in lower case.

    Parameters
    ----------
    text
        The candidate numeral.

    Returns
    -------
    int | None
        Its value, or ``None`` when it is not a roman numeral.

    Examples
    --------
    >>> _roman_value("xiv"), _roman_value("Mix")
    (14, None)
    """

    if not text or not (text.isupper() or text.islower()):
        return None
    upper = text.upper()
    if _ROMAN.fullmatch(upper) is None:
        return None

    total = 0
    for here, after in zip(upper, [*upper[1:], ""], strict=True):
        value = _ROMAN_VALUES[here]
        total += -value if after and _ROMAN_VALUES[after] > value else value
    return total


def _standard_type(*, name: str, role_map: dict[str, str]) -> str:
    """Follow the role map from an element type to a standard type.

    Parameters
    ----------
    name
        The element's type, without the leading ``/``.
    role_map
        Standard types by custom type.

    Returns
    -------
    str
        The standard type, or the last type reached.
    """

    for _ in range(_MAX_ROLE_STEPS):
        mapped = role_map.get(name)
        if mapped is None or mapped == name:
            break
        name = mapped
    return name


def _structure(*, document: pymupdf.Document, text_pages: set[int]) -> StructureFacts:
    """Measure what the PDF's structure tags cover.

    Parameters
    ----------
    document
        The open PDF.
    text_pages
        The indexes of the pages with text.

    Returns
    -------
    StructureFacts
        The structure tree's size, types, page coverage and quality.
    """

    catalog = document.pdf_catalog()
    marked = document.xref_get_key(catalog, "MarkInfo/Marked") == ("bool", "true")
    kind, value = document.xref_get_key(catalog, "StructTreeRoot")
    if kind != "xref":
        return StructureFacts(
            element_count=0,
            marked=marked,
            pages_with_tagged_content=0,
            quality="none",
            tagged=False,
            truncated=False,
            type_counts={},
        )

    root = int(value.split(maxsplit=1)[0])
    walk = _walk_structure(document=document, root=root)
    return StructureFacts(
        element_count=walk.types.total(),
        marked=marked,
        pages_with_tagged_content=len(walk.pages),
        quality=_structure_quality(walk=walk, text_pages=text_pages),
        tagged=True,
        truncated=walk.truncated,
        type_counts=dict(sorted(walk.types.items())),
    )


def _structure_quality(
    *, text_pages: set[int], walk: _StructureWalk
) -> StructureQuality:
    """Rate the structure tags.

    Coverage is the share of the pages with text that have tagged content. Tagged
    pages without text do not count. A walk cut short at `STRUCTURE_ELEMENT_CAP` is
    rated only on the pages with text up to the last page it reached.

    Parameters
    ----------
    text_pages
        The indexes of the pages with text.
    walk
        What the structure walk found.

    Returns
    -------
    StructureQuality
        ``none``, ``poor``, ``partial`` or ``good``.
    """

    total = walk.types.total()
    if total == 0:
        return "none"
    has_content = any(kind not in STRUCTURE_GROUPING_TYPES for kind in walk.types)
    if total < STRUCTURE_MIN_ELEMENTS or not has_content:
        return "poor"
    rated = text_pages
    if walk.truncated and walk.pages:
        last = max(walk.pages)
        rated = {index for index in text_pages if index <= last}
    covered = walk.pages & rated
    if rated and len(covered) < len(rated) * STRUCTURE_GOOD_PAGE_SHARE:
        return "partial"
    return "good"


def _text_facts(text: str) -> TextFacts:
    """Count a page's characters and judge whether its text layer is readable.

    Parameters
    ----------
    text
        The page's text.

    Returns
    -------
    TextFacts
        The counts and the quality.
    """

    chars = control = private_use = unassigned = replacement = 0
    for char in text:
        if char.isspace():
            continue
        chars += 1
        category = unicodedata.category(char)
        control += category == "Cc"
        private_use += category == "Co"
        unassigned += category == "Cn"
        replacement += char == "�"

    unreadable = control + private_use + unassigned + replacement
    quality: TextQuality
    if chars == 0:
        quality = "none"
    elif unreadable >= chars * GARBLED_SHARE:
        quality = "garbled"
    else:
        quality = "good"
    return TextFacts(
        chars=chars,
        control_chars=control,
        private_use_chars=private_use,
        quality=quality,
        replacement_chars=replacement,
        unassigned_chars=unassigned,
    )


def _text_number(text: str) -> PrintedNumber | None:
    """Read a line as a printed page number, if it is one.

    The line must hold a single number, in any script's decimal digits or in roman
    numerals, with nothing around it but characters that are not letters or digits.

    Parameters
    ----------
    text
        The line.

    Returns
    -------
    PrintedNumber | None
        The number, or ``None`` when the line is not one.

    Examples
    --------
    >>> _text_number("- 12 -").value, _text_number("Page 12")
    (12, None)
    """

    parts = _NUMBER_PARTS.findall(text)
    if len(parts) != 1:
        return None
    part = parts[0]
    if part.isdecimal():
        return PrintedNumber(source="text", style="arabic", text=text, value=int(part))
    roman = _roman_value(part)
    if roman is None:
        return None
    return PrintedNumber(source="text", style="roman", text=text, value=roman)


def _visit(
    *,
    document: pymupdf.Document,
    kid: tuple[str, str],
    page: int | None,
    page_indexes: dict[int, int],
    walk: _StructureWalk,
) -> list[tuple[tuple[str, str], int | None]]:
    """Visit one kid of the structure tree, and return its own kids to visit.

    Parameters
    ----------
    document
        The open PDF.
    kid
        The kid, as `_kids` returns it.
    page
        The page inherited from the parent element.
    page_indexes
        Page indexes by page object number.
    walk
        What the walk has found so far; updated in place.

    Returns
    -------
    list[tuple[tuple[str, str], int | None]]
        The kid's own kids, each with the page it inherits.
    """

    kind, value = kid
    if kind == "ref":
        return _visit_object(
            document=document,
            page=page,
            page_indexes=page_indexes,
            walk=walk,
            xref=int(value),
        )
    if kind == "dict":
        # An inline marked-content or object reference may name its own page.
        found = _PAGE_REFERENCE.search(value)
        if found is not None:
            page = page_indexes.get(int(found.group(1)), page)
    if page is not None:
        walk.pages.add(page)
    return []


def _visit_object(
    *,
    document: pymupdf.Document,
    page: int | None,
    page_indexes: dict[int, int],
    walk: _StructureWalk,
    xref: int,
) -> list[tuple[tuple[str, str], int | None]]:
    """Visit a structure-tree object: an element, or a reference to content.

    Parameters
    ----------
    document
        The open PDF.
    page
        The page inherited from the parent element.
    page_indexes
        Page indexes by page object number.
    walk
        What the walk has found so far; updated in place.
    xref
        The object's number.

    Returns
    -------
    list[tuple[tuple[str, str], int | None]]
        An element's kids, each with the page it inherits; nothing for a reference.
    """

    if xref in walk.visited:
        return []
    walk.visited.add(xref)
    own = _page_of(document=document, page_indexes=page_indexes, xref=xref)
    if own is not None:
        page = own

    kind, value = document.xref_get_key(xref, "S")
    if kind != "name":
        # A marked-content or object reference stored as its own object.
        if page is not None:
            walk.pages.add(page)
        return []
    if walk.types.total() >= STRUCTURE_ELEMENT_CAP:
        walk.truncated = True
        return []

    walk.types[value.lstrip("/")] += 1
    return [(child, page) for child in _element_kids(document=document, xref=xref)]


def _walk_structure(*, document: pymupdf.Document, root: int) -> _StructureWalk:
    """Walk the structure tree, counting elements and the pages they cover.

    Parameters
    ----------
    document
        The open PDF.
    root
        The structure tree root's object number.

    Returns
    -------
    _StructureWalk
        Element types (after the role map), covered pages and whether the walk was
        cut short.
    """

    page_indexes = {document.page_xref(index): index for index in range(len(document))}
    walk = _StructureWalk()
    stack: list[tuple[tuple[str, str], int | None]] = [
        (kid, None) for kid in reversed(_element_kids(document=document, xref=root))
    ]
    while stack and not walk.truncated:
        kid, page = stack.pop()
        children = _visit(
            document=document,
            kid=kid,
            page=page,
            page_indexes=page_indexes,
            walk=walk,
        )
        stack.extend(reversed(children))

    walk.types = _map_types(
        role_map=_role_map(document=document, root=root), types=walk.types
    )
    return walk


def probe_pdf(path: Path) -> Facts:
    """Measure the facts about a PDF that need no model.

    This reads the whole PDF, so async code should call it with `asyncio.to_thread`.

    Parameters
    ----------
    path
        A PDF that `pydelity.utils.pdf.open_pdf` has already checked.

    Returns
    -------
    Facts
        Per-page text, orientation, direction and printed numbers; numbering ranges;
        repeated lines; bookmarks; form fields; structure tags; and any facts that
        could not be read.
    """

    with pymupdf.open(path, filetype="pdf") as document:
        label_styles = _label_styles(document)
        pages: list[PageFacts] = []
        lines_by_page: list[list[_Line]] = []
        for index in range(len(document)):
            facts, lines = _page(
                index=index,
                label_style=None if label_styles is None else label_styles[index],
                page=document[index],
            )
            pages.append(facts)
            lines_by_page.append(lines)
        _choose_text_numbers(lines_by_page=lines_by_page, pages=pages)

        errors: list[ProbeError] = []
        bookmarks = _read_fact(
            errors=errors, fact="bookmarks", read=lambda: _bookmarks(document)
        )
        form = _read_fact(
            errors=errors, fact="form", read=lambda: _form(document, errors=errors)
        )
        text_pages = {page.index for page in pages if page.text.quality != "none"}
        structure = _read_fact(
            errors=errors,
            fact="structure",
            read=lambda: _structure(document=document, text_pages=text_pages),
        )
        repeated, truncated = _repeated_lines(
            lines_by_page=lines_by_page, page_count=len(document)
        )

    return Facts(
        bookmarks=bookmarks,
        form=form[1] if form is not None else None,
        form_fields=form[0] if form is not None else None,
        page_numbering=_numbering(pages),
        pages=pages,
        probe_errors=errors,
        repeated_lines=repeated,
        repeated_lines_truncated=truncated,
        structure=structure,
    )

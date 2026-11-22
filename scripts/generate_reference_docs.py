#!/usr/bin/env python3
"""Generate the docs site's reference pages from pydelity's code.

Run it with ``just docs-reference``; ``just lint`` runs it before formatting Markdown.
It writes one Markdown page per topic to ``docs/src/content/docs/reference/``: the
settings, the ``pydelity`` command, the Python API, each output file, and the checks
of the survey and of page extraction. The pages come from the Pydantic models and
their field docstrings, the Typer command, the public functions and their NumPy
docstrings, and the constants the probe and the cost estimate use. Prettier formats
the pages afterward, and running both again gives the same bytes, so CI catches a page
the code has outgrown and a new page left uncommitted.
"""

# Standard Library
import ast
import inspect
import itertools
import json
import re
import sys
import types
import typing

from collections import deque
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

# Third Party Library
import annotated_types
import typer

from pydantic import BaseModel
from pydantic.fields import FieldInfo

# Package Library
import pydelity

from pydelity import cli, errors
from pydelity.config.schemas import Config
from pydelity.costs import budget
from pydelity.costs.schemas import CostEstimate, LedgerEntry
from pydelity.extracting import text_layer
from pydelity.extracting import validators as extraction_checks
from pydelity.extracting.schemas import PageFile
from pydelity.pipeline.schemas import RunRecord
from pydelity.providers.profiles import PROFILES
from pydelity.providers.schemas import Uploads
from pydelity.surveying import probe, validators
from pydelity.surveying.schemas import PdfFacts, PdfSurvey

# Words for the bounds Pydantic fields carry, by annotated_types class.
_BOUND_WORDS: dict[type, tuple[str, str]] = {
    annotated_types.Ge: ("ge", "at least"),
    annotated_types.Gt: ("gt", "more than"),
    annotated_types.Le: ("le", "at most"),
    annotated_types.Lt: ("lt", "less than"),
}

# Code names in the page-extraction checks' docstrings, and the words a reader of the
# checks page sees instead.
_CHECK_REFERENCES = {
    "`comparison_status` is ``compared``": (
        "the page file's ``text_comparison`` is ``compared``"
    ),
    "`unmatched_labels` records those items for review instead": (
        "those items are listed for review as ``no_matching_label`` instead"
    ),
    "passes `check_labels`": "passes the ``labels`` check",
}

# The reference page that describes each exported class, by class name.
_CLASS_PAGES = {
    "Config": "configuration",
    "PageFile": "page-json",
    "PdfFacts": "pdf-facts-json",
    "PdfSurvey": "pdf-survey-json",
    "RunRecord": "run-json",
}

# How a map's key is shown in a section heading, by field name.
_KEY_NAMES = {"models": "<provider>:<model-id>"}

# The note at the top of every page, after its front matter.
_MARKER = (
    "<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run "
    "`just docs-reference` instead of editing this file. -->"
)

# Plural words for simple type names, for "list of ..." types.
_PLURALS = {
    "boolean": "booleans",
    "integer": "integers",
    "number": "numbers",
    "path": "paths",
    "string": "strings",
}

# The repository root.
_ROOT = Path(__file__).resolve().parents[1]

# JSON-facing names of the plain Python types settings and output fields use.
_SIMPLE_TYPES: dict[object, str] = {
    Decimal: "number",
    Path: "path",
    bool: "boolean",
    datetime: "date and time (ISO 8601)",
    float: "number",
    int: "integer",
    object: "any value",
    str: "string",
}

# Where the pages are written.
OUTPUT_DIR = _ROOT / "docs/src/content/docs/reference"


@dataclass(frozen=True)
class _Page:
    """One reference page."""

    body: str
    """The Markdown after the front matter and the generated-file note."""

    description: str
    """The page's description, for search engines and link previews."""

    name: str
    """The file name, without ``.md``."""

    order: int
    """The page's place in the side panel's Reference group."""

    title: str
    """The page's title."""

    def render(self) -> str:
        """Return the page's full Markdown.

        Returns
        -------
        str
            Front matter, the generated-file note, then the body.
        """

        front = "\n".join(
            [
                "---",
                f"title: {self.title}",
                f"description: {self.description}",
                "sidebar:",
                f"  order: {self.order}",
                "---",
            ]
        )
        return f"{front}\n\n{_MARKER}\n\n{self.body.strip()}\n"


def _anchor(heading: str) -> str:
    """Return the fragment Starlight gives a heading, as github-slugger makes it.

    Parameters
    ----------
    heading
        The heading's text, without Markdown.

    Returns
    -------
    str
        The fragment, such as ``advancedsurvey`` for ``advanced.survey``.
    """

    kept = re.sub(r"[^\w\- ]", "", heading.lower())
    return kept.replace(" ", "-")


def _annotation_metadata(annotation: object) -> Iterator[object]:
    """Yield the metadata inside every ``Annotated`` an annotation holds.

    Parameters
    ----------
    annotation
        A type annotation, such as ``Annotated[int, Field(ge=0)] | None``.

    Yields
    ------
    object
        Each metadata item, with a nested ``FieldInfo`` opened up.
    """

    if typing.get_origin(annotation) is typing.Annotated:
        for item in typing.get_args(annotation)[1:]:
            yield from item.metadata if isinstance(item, FieldInfo) else [item]
    for arg in typing.get_args(annotation):
        yield from _annotation_metadata(arg)


def _attribute_docstrings(cls: type) -> dict[str, str]:
    """Read the docstrings written under a class's attributes in its source.

    Parameters
    ----------
    cls
        The class, such as an ``Enum`` whose members carry docstrings.

    Returns
    -------
    dict[str, str]
        Each documented attribute's docstring, by name.
    """

    tree = ast.parse(inspect.getsource(cls))
    node = tree.body[0] if tree.body else None
    body = node.body if isinstance(node, ast.ClassDef) else []
    found: dict[str, str] = {}
    for current, following in itertools.pairwise(body):
        targets = current.targets if isinstance(current, ast.Assign) else []
        if (
            len(targets) == 1
            and isinstance(targets[0], ast.Name)
            and isinstance(following, ast.Expr)
            and isinstance(following.value, ast.Constant)
            and isinstance(following.value.value, str)
        ):
            found[targets[0].id] = following.value.value
    return found


def _bounds(field: FieldInfo) -> list[str]:
    """Describe a field's numeric bounds, such as ``at least 0``.

    Parameters
    ----------
    field
        The Pydantic field.

    Returns
    -------
    list[str]
        One phrase per bound.
    """

    items = list(field.metadata) + list(_annotation_metadata(field.annotation))
    phrases = []
    for item in items:
        for kind, (attribute, words) in _BOUND_WORDS.items():
            if isinstance(item, kind):
                phrases.append(f"{words} {getattr(item, attribute)}")
    return list(dict.fromkeys(phrases))


def _check_text(doc: str | None) -> str:
    """Give a page-extraction check's docstring summary in a reader's words.

    Parameters
    ----------
    doc
        The check's docstring.

    Returns
    -------
    str
        The text before the parameters, each paragraph on one line, with the code
        names in `_CHECK_REFERENCES` replaced.
    """

    text, _ = _docstring_parts(doc)
    text = "\n\n".join(" ".join(part.split()) for part in text.split("\n\n"))
    for code, words in _CHECK_REFERENCES.items():
        text = text.replace(code, words)
    return text


def _choices(values: list[object]) -> str:
    """Name the values a field may take.

    Parameters
    ----------
    values
        The values, in order.

    Returns
    -------
    str
        Such as ``one of `low`, `high``` or, for one value, ```verifier```.
    """

    names = [f"`{value}`" for value in values]
    return names[0] if len(names) == 1 else "one of " + ", ".join(names)


def _constants(module: types.ModuleType) -> list[str]:
    """List a module's public constants with the comment written above each.

    Parameters
    ----------
    module
        The module, such as `pydelity.surveying.probe`.

    Returns
    -------
    list[str]
        One Markdown list item per constant, in source order.
    """

    source = inspect.getsource(module)
    lines = source.splitlines()
    items = []
    for node in ast.parse(source).body:
        if not isinstance(node, ast.Assign | ast.AnnAssign):
            continue
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        name = target.id if isinstance(target, ast.Name) else ""
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
            continue
        comment = []
        row = node.lineno - 2
        while row >= 0 and lines[row].startswith("#"):
            comment.insert(0, lines[row].lstrip("# ").strip())
            row -= 1
        value = getattr(module, name)
        shown = sorted(value) if isinstance(value, frozenset | set) else value
        items.append(f"- `{name}` = `{shown!r}`: {_prose(' '.join(comment))}")
    return items


def _default(field: FieldInfo) -> str:
    """Describe a field's default value.

    Parameters
    ----------
    field
        The Pydantic field.

    Returns
    -------
    str
        ``required``, ``default `...` ``, or an empty string for a nested object.
    """

    if field.is_required():
        return "required"
    value = field.get_default(call_default_factory=True)
    if isinstance(value, BaseModel):
        return ""
    if isinstance(value, Enum):
        value = value.value
    return f"default `{json.dumps(value, default=str)}`"


def _docstring_parts(doc: str | None) -> tuple[str, dict[str, str]]:
    """Split a NumPy docstring into its text and its sections.

    Parameters
    ----------
    doc
        The docstring.

    Returns
    -------
    tuple[str, dict[str, str]]
        The summary and extended text, then each section's body by title, such as
        ``Parameters``.
    """

    text = inspect.cleandoc(doc or "")
    parts = re.split(r"^([A-Z][A-Za-z ]+)\n-{3,}\n", text, flags=re.MULTILINE)
    return parts[0].strip(), dict(zip(parts[1::2], parts[2::2], strict=True))


def _entries(body: str) -> list[tuple[str, str]]:
    """Read the entries of a docstring section such as Parameters or Raises.

    Parameters
    ----------
    body
        The section's text: each entry's name at the start of a line, its
        description indented below.

    Returns
    -------
    list[tuple[str, str]]
        Each entry's name and description.
    """

    entries: list[tuple[str, list[str]]] = []
    for line in body.splitlines():
        if line and not line[0].isspace():
            entries.append((line.strip(), []))
        elif entries and line.strip():
            entries[-1][1].append(line.strip())
    return [(name, " ".join(text)) for name, text in entries]


def _field_items(model: type[BaseModel], links: dict[type, str]) -> list[str]:
    """Describe a model's fields as Markdown list items.

    Parameters
    ----------
    model
        The Pydantic model.
    links
        The section path of each model the page describes, for links to them.

    Returns
    -------
    list[str]
        One item per field: its name, type, bounds, default and description.
    """

    items = []
    for name, field in model.model_fields.items():
        facts = [_type_name(field.annotation, links), *_bounds(field)]
        facts.append(_default(field))
        details = "; ".join(fact for fact in facts if fact)
        items.append(_item(f"`{name}` ({details})", field.description or ""))
    return items


def _function_section(name: str, function: Callable[..., object]) -> str:
    """Describe one public function: its signature and its docstring's sections.

    Parameters
    ----------
    name
        The name pydelity exports it as.
    function
        The function.

    Returns
    -------
    str
        The Markdown section.
    """

    text, sections = _docstring_parts(function.__doc__)
    blocks = [
        f"### `{name}`",
        f"```python\n{_signature(name, function)}\n```",
        _prose(text),
    ]
    for title in ("Parameters", "Returns", "Raises"):
        entries = _entries(sections.get(title, ""))
        if entries:
            items = "\n".join(_item(f"`{entry}`", info) for entry, info in entries)
            blocks.append(f"**{title}**\n\n{items}")
    return "\n\n".join(blocks)


def _item(label: str, text: str) -> str:
    """Write a Markdown list item, keeping later paragraphs inside the item.

    Parameters
    ----------
    label
        The item's label, such as a field name and type.
    text
        Docstring or help text, which may have several paragraphs.

    Returns
    -------
    str
        ``- label: text``, with later paragraphs indented under it.
    """

    first, *rest = _prose(text).split("\n\n")
    return "\n\n".join(
        [f"- {label}: {first}", *(f"  {paragraph}" for paragraph in rest)]
    )


def _model_section(path: str, model: type[BaseModel], links: dict[type, str]) -> str:
    """Describe one model as a page section headed by its path in the file.

    Parameters
    ----------
    path
        The section's path, such as ``facts.pages[]``.
    model
        The Pydantic model.
    links
        The section path of each model the page describes.

    Returns
    -------
    str
        The Markdown section.
    """

    summary = _docstring_parts(model.__doc__)[0].split("\n\n")[0]
    items = "\n".join(_field_items(model, links))
    heading = path if " " in path else f"`{path}`"
    return f"## {heading}\n\n{_prose(summary)}\n\n{items}"


def _models_page_body(
    root: type[BaseModel], label: str, key_names: dict[str, str]
) -> str:
    """Describe a model and every model nested in it, one section each.

    Parameters
    ----------
    root
        The top-level model, such as `PdfFacts`.
    label
        The top-level section's heading, such as ``pdf_facts.json``.
    key_names
        How a map's key is shown in a heading, by field name.

    Returns
    -------
    str
        The sections, the top level first and then breadth first.
    """

    links: dict[type, str] = {root: label}
    queue = deque([(label, root)])
    ordered = []
    while queue:
        path, model = queue.popleft()
        ordered.append((path, model))
        for name, field in model.model_fields.items():
            for child, suffix in _nested_models(field.annotation, key_names.get(name)):
                if child not in links:
                    prefix = "" if model is root or " " in path else f"{path}."
                    links[child] = f"{prefix}{name}{suffix}"
                    queue.append((links[child], child))
    return "\n\n".join(_model_section(path, model, links) for path, model in ordered)


def _named_type(annotation: object, links: dict[type, str]) -> str:
    """Name a class: a model the page describes, an enum, or a plain type.

    Parameters
    ----------
    annotation
        The class.
    links
        The section path of each model the page describes.

    Returns
    -------
    str
        Such as ``object ([`facts`](#facts))``, ``one of `text`, `table```, or
        ``number``. An enum of one member is named by that member alone.
    """

    if annotation in links:
        path = links[annotation]  # ty: ignore[invalid-argument-type]
        return f"object ([`{path}`](#{_anchor(path)}))"
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return _choices([member.value for member in annotation])
    return _SIMPLE_TYPES.get(
        annotation, getattr(annotation, "__name__", str(annotation))
    )


def _nested_models(
    annotation: object, key_name: str | None
) -> Iterator[tuple[type[BaseModel], str]]:
    """Yield the models a field holds, with the path suffix that reaches each.

    Parameters
    ----------
    annotation
        The field's type annotation.
    key_name
        How a map's key is shown, or ``None`` for ``<key>``.

    Yields
    ------
    tuple[type[BaseModel], str]
        Each model, and ``""``, ``"[]"`` for a list item or ``".<key>"`` for a map
        value.
    """

    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        yield annotation, ""
    elif origin is dict:
        for child, suffix in _nested_models(args[1], key_name):
            yield child, f".{key_name or '<key>'}{suffix}"
    elif origin in {list, tuple}:
        for child, suffix in _nested_models(args[0], key_name):
            yield child, f"[]{suffix}"
    else:
        for arg in args:
            yield from _nested_models(arg, key_name)


def _plural(name: str) -> str:
    """Make a type name plural for ``list of ...``.

    Parameters
    ----------
    name
        A type name, such as ``string`` or ``object ([`labels[]`](#labels))``.

    Returns
    -------
    str
        The plural, such as ``strings`` or ``objects ([`labels[]`](#labels))``.
    """

    if name.startswith("object"):
        return "objects" + name.removeprefix("object")
    return _PLURALS.get(name, name)


def _prose(text: str) -> str:
    """Turn docstring or help text into Markdown prose.

    Double backticks become single ones, angle brackets outside code are escaped so
    they do not read as HTML, and line breaks inside a paragraph become spaces.

    Parameters
    ----------
    text
        The text.

    Returns
    -------
    str
        The Markdown.
    """

    text = re.sub(r"``(.+?)``", r"`\1`", text, flags=re.DOTALL)
    pieces = re.split(r"(`[^`]*`)", text)
    escaped = [
        piece
        if piece.startswith("`")
        else piece.replace("<", "&lt;").replace(">", "&gt;")
        for piece in pieces
    ]
    paragraphs = "".join(escaped).split("\n\n")
    return "\n\n".join(" ".join(paragraph.split()) for paragraph in paragraphs)


def _sequence_name(args: tuple[object, ...], links: dict[type, str]) -> str:
    """Name a list, set or tuple type.

    Parameters
    ----------
    args
        The type's arguments, such as ``(float, float, float, float)``.
    links
        The section path of each model the page describes.

    Returns
    -------
    str
        Such as ``list of strings`` or ``list of 4 numbers``.
    """

    if not args:
        return "list"
    item = _plural(_type_name(args[0], links))
    if len(args) > 1 and args[-1] is not Ellipsis:
        return f"list of {len(args)} {item}"
    return f"list of {item}"


def _series(items: list[str]) -> str:
    """Join items as English does: ``a``, ``a and b``, ``a, b and c``.

    Parameters
    ----------
    items
        The items.

    Returns
    -------
    str
        The joined text.
    """

    if len(items) < 2:  # noqa: PLR2004 - one item needs no joining
        return "".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"


def _signature(name: str, function: Callable[..., object]) -> str:
    """Write a function's signature with short type names.

    Parameters
    ----------
    name
        The name pydelity exports it as.
    function
        The function.

    Returns
    -------
    str
        ``pydelity.<name>(...)``, one parameter per line when it is long.
    """

    signature = inspect.signature(function)
    short = re.compile(r"\b(?:[a-z_][a-z0-9_]*\.)+([A-Za-z_]\w*)")
    # The signature's own text has the `/` and `*` markers; split it at the top-level
    # commas between parameters.
    inner = str(signature.replace(return_annotation=inspect.Signature.empty))[1:-1]
    params = [short.sub(r"\1", param.strip()) for param in _split_top_level(inner)]
    returns = short.sub(r"\1", inspect.formatannotation(signature.return_annotation))
    prefix = "async def" if inspect.iscoroutinefunction(function) else "def"
    one_line = f"{prefix} {name}({', '.join(params)}) -> {returns}"
    if len(one_line) <= 88:  # noqa: PLR2004 - the repo's line length
        return one_line
    inner = "".join(f"    {param},\n" for param in params)
    return f"{prefix} {name}(\n{inner}) -> {returns}"


def _split_top_level(text: str) -> list[str]:
    """Split a parameter list at the commas that are not inside brackets.

    Parameters
    ----------
    text
        Such as ``pdf: str | None = None, *, config: dict[str, int] = None``.

    Returns
    -------
    list[str]
        The parameters, such as ``["pdf: str | None = None", "*", ...]``.
    """

    parts, depth, start = [], 0, 0
    for index, char in enumerate(text):
        depth += (char in "[(") - (char in "])")
        if char == "," and depth == 0:
            parts.append(text[start:index])
            start = index + 1
    parts.append(text[start:])
    return [part for part in parts if part.strip()]


def _type_name(annotation: object, links: dict[type, str]) -> str:
    """Name a field's type the way the JSON or a settings file shows it.

    Parameters
    ----------
    annotation
        The type annotation.
    links
        The section path of each model the page describes.

    Returns
    -------
    str
        Such as ``integer``, ``list of strings``, ``one of `low`, `high```,
        ```verifier``` (a literal of one value) or ``object ([`facts`](#facts))``.
    """

    annotation = _unwrap(annotation)
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin in {typing.Union, types.UnionType}:
        names = [_type_name(arg, links) for arg in args if arg is not type(None)]
        suffix = " or null" if type(None) in args else ""
        return " or ".join(names) + suffix
    if origin is typing.Literal:
        return _choices(list(args))
    if origin in {list, tuple, set, frozenset}:
        return _sequence_name(args, links)
    if origin is dict:
        key, value = (_type_name(arg, links) for arg in args)
        return f"map of {key} to {value}"
    return _named_type(annotation, links)


def _unwrap(annotation: object) -> object:
    """Remove type aliases and ``Annotated`` from around a type.

    Parameters
    ----------
    annotation
        A type annotation, such as ``Annotated[int, Field(ge=0)]`` or an alias.

    Returns
    -------
    object
        The type underneath, such as ``int``.
    """

    while True:
        if isinstance(annotation, typing.TypeAliasType):
            annotation = annotation.__value__
        elif typing.get_origin(annotation) is typing.Annotated:
            annotation = typing.get_args(annotation)[0]
        else:
            return annotation


def cli_page() -> _Page:
    """Describe the ``pydelity`` command: its argument, options and exit codes.

    Returns
    -------
    _Page
        The page.
    """

    command = typer.main.get_command(cli.app)
    usage = " ".join(command.collect_usage_pieces(typer.Context(command)))
    items = []
    for param in command.params:
        flags = ", ".join(f"`{flag}`" for flag in param.opts)
        metavar = f" `{param.metavar}`" if getattr(param, "metavar", None) else ""
        default = getattr(param, "show_default", None)
        shown = f" Default: `{default}`." if isinstance(default, str) else ""
        help_text = _prose(getattr(param, "help", "") or "")
        items.append(f"- {flags}{metavar}: {help_text}{shown}")
    settings = cli.app.info.context_settings or {}
    help_names = settings.get("help_option_names", ["--help"])
    help_flags = ", ".join(f"`{flag}`" for flag in help_names)
    items.append(f"- {help_flags}: Show the options and exit.")

    codes = _attribute_docstrings(errors.ExitCode)
    exits = [
        f"- `{member.value}`: {_prose(codes.get(member.name, ''))}"
        for member in sorted(errors.ExitCode, key=int)
    ]
    body = "\n\n".join(
        [
            _prose(command.help or ""),
            f"```sh\npydelity {usage}\n```",
            "## Argument and options",
            "\n".join(items),
            "## Exit codes",
            "\n".join(exits),
        ]
    )
    return _Page(
        body=body,
        description="The pydelity command's argument, options and exit codes.",
        name="cli",
        order=2,
        title="Command line",
    )


def configuration_page() -> _Page:
    """Describe every setting, from the `Config` model and the models inside it.

    Returns
    -------
    _Page
        The page.
    """

    intro = _prose(
        "Settings come from the command's options, from a JSON or YAML config file "
        "(``--config``), or from keyword arguments to the Python functions. Options "
        "and keyword arguments win over the file, and the file wins over the "
        "defaults. Settings under ``advanced`` are set in the file or as an "
        "``advanced`` mapping in Python."
    )
    body = _models_page_body(Config, "Top-level settings", _KEY_NAMES)
    return _Page(
        body=f"{intro}\n\n{body}",
        description="Every setting pydelity reads, with its type, default and meaning.",
        name="configuration",
        order=1,
        title="Configuration",
    )


def cost_page() -> _Page:
    """Describe ``cost.jsonl``, the cost estimate and the constants it uses.

    Returns
    -------
    _Page
        The page.
    """

    profiles = [
        f"- `{name}`: {profile.pdf_image_tokens_per_page:,} image and "
        f"{profile.pdf_text_tokens_per_page:,} text input tokens per PDF page; "
        f"uploads kept {profile.min_upload_expiry_hours} to "
        f"{profile.max_upload_expiry_hours:,} hours."
        for name, profile in sorted(PROFILES.items())
    ]
    body = "\n\n".join(
        [
            _prose(
                "The output folder's ledger: one JSON object per line, one line for "
                "each model response pydelity received, in the order received."
            ),
            _models_page_body(LedgerEntry, "cost.jsonl line", {}),
            _models_page_body(CostEstimate, "Cost estimate", {}),
            "## Estimate constants",
            _prose("The figures the cost estimate and the ``max_cost`` checks use."),
            "\n".join(_constants(budget)),
            "\n".join(profiles),
        ]
    )
    return _Page(
        body=body,
        description=(
            "The fields of cost.jsonl and of the cost estimate, and the figures the "
            "estimate uses."
        ),
        name="cost-jsonl",
        order=8,
        title="cost.jsonl",
    )


def extraction_checks_page() -> _Page:
    """Describe page extraction's checks, its hints and its other review issues.

    Returns
    -------
    _Page
        The page.
    """

    checks = [
        f"### `{name}`\n\n{_prose(_check_text(check.__doc__))}"
        for name, check in extraction_checks.CHECKS.items()
    ]
    hints = [
        f"### `{name}`\n\n{_prose(_check_text(hint.__doc__))}"
        for name, hint in extraction_checks.HINTS.items()
    ]
    comparison = _docstring_parts(text_layer.__doc__)[0].split("\n\n")[2]
    body = "\n\n".join(
        [
            _prose(
                "Each page answer, from the extraction model or in a verifier's "
                "correction, goes through the checks and is compared with the hints. "
                "A check tests the answer against itself, the PDF's profile and the "
                "page's area. While "
                "retries remain (``advanced.extraction.check_retries``), an answer "
                "that fails a check is sent back to the model with every failure "
                "listed. The last answer is kept as it is, and each check it still "
                "fails becomes a review issue. A hint compares the answer with what "
                "code measured or the survey found about the page, which can be "
                "wrong, so the model's reading of the page image decides. A hint "
                "difference never sends an answer back and never stops a run."
            ),
            _prose(
                "A verifier correction replaces the extraction when it passes every "
                "check, whatever its hint differences. The page file's ``checks`` "
                "holds each check's result on the kept answer, and its ``hints`` each "
                "hint's differences. A hint difference becomes a review issue unless "
                "the verifier passed the page or its correction was kept. With the "
                "verifier off (``advanced.extraction.verify``, or ``verify``), every "
                "hint difference is a review issue."
            ),
            "## Checks",
            *checks,
            "## Hints",
            *hints,
            "## How text is compared",
            _prose(comparison),
            "## Other review issues",
            _prose("These are recorded without sending the answer back."),
            "### `no_matching_label`",
            _prose(_check_text(extraction_checks.unmatched_labels.__doc__)),
            "### `verifier`",
            _prose(
                "A problem page extraction's verifier found on a page whose "
                "extraction it did not replace, because it gave no correction or its "
                "correction failed a check. The issue names the item or container the "
                "problem is about, when there is one."
            ),
        ]
    )
    return _Page(
        body=body,
        description=(
            "The checks every page answer goes through, the hints it is compared "
            "with, and the other review issues page extraction records."
        ),
        name="extraction-checks",
        order=11,
        title="Page extraction checks",
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Write every reference page and remove generated pages no longer made.

    Parameters
    ----------
    argv
        Unused; the script takes no arguments.

    Returns
    -------
    int
        0.
    """

    del argv
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pages = [
        cli_page(),
        configuration_page(),
        cost_page(),
        model_file_page(
            description="Every field of pdf_facts.json, and the probe's thresholds.",
            extra=["## Measurement constants", "\n".join(_constants(probe))],
            model=PdfFacts,
            name="pdf-facts-json",
            order=4,
            title="pdf_facts.json",
        ),
        model_file_page(
            description="Every field of pdf_survey.json.",
            extra=[],
            model=PdfSurvey,
            name="pdf-survey-json",
            order=5,
            title="pdf_survey.json",
        ),
        model_file_page(
            description="Every field of a page file, pages/<NNNN>.json.",
            extra=[],
            model=PageFile,
            name="page-json",
            order=6,
            title="pages/<NNNN>.json",
        ),
        python_api_page(),
        model_file_page(
            description="Every field of run.json.",
            extra=[],
            model=RunRecord,
            name="run-json",
            order=7,
            title="run.json",
        ),
        survey_checks_page(),
        extraction_checks_page(),
        model_file_page(
            description="Every field of uploads.json.",
            extra=[],
            model=Uploads,
            name="uploads-json",
            order=9,
            title="uploads.json",
        ),
    ]
    written = set()
    for page in pages:
        path = OUTPUT_DIR / f"{page.name}.md"
        path.write_text(page.render(), encoding="utf-8")
        written.add(path)
    for path in OUTPUT_DIR.glob("*.md"):
        if path not in written and _MARKER in path.read_text(encoding="utf-8"):
            path.unlink()
    print(f"Wrote {len(written)} reference pages to {OUTPUT_DIR.relative_to(_ROOT)}")
    return 0


def model_file_page(  # noqa: PLR0913 - one argument per part of the page
    *,
    description: str,
    extra: list[str],
    model: type[BaseModel],
    name: str,
    order: int,
    title: str,
) -> _Page:
    """Describe one output file from its model.

    Parameters
    ----------
    description
        The page's description.
    extra
        Markdown blocks added after the fields.
    model
        The file's model, such as `RunRecord`.
    name
        The page's file name, without ``.md``.
    order
        The page's place in the side panel.
    title
        The page's title, which is the file's name.

    Returns
    -------
    _Page
        The page.
    """

    summary, _ = _docstring_parts(model.__doc__)
    body = "\n\n".join([_prose(summary), _models_page_body(model, title, {}), *extra])
    return _Page(
        body=body, description=description, name=name, order=order, title=title
    )


def python_api_page() -> _Page:
    """Describe the functions, classes and errors ``pydelity`` exports.

    Returns
    -------
    _Page
        The page.
    """

    names = [name for name in pydelity.__all__ if name != "__version__"]
    functions = [name for name in names if inspect.isfunction(getattr(pydelity, name))]
    with_async = sorted(name for name in functions if f"a{name}" in functions)

    def order(name: str) -> tuple[str, bool]:
        """Sort each async function right after its sync form, such as `run`, `arun`.

        Parameters
        ----------
        name
            The function's name.

        Returns
        -------
        tuple[str, bool]
            The sync form's name, then whether this is the async form.
        """

        is_async = name.startswith("a") and name[1:] in with_async
        return (name[1:] if is_async else name, is_async)

    functions.sort(key=order)
    classes = sorted(name for name in names if name not in functions)

    sections = [_function_section(name, getattr(pydelity, name)) for name in functions]
    class_items = []
    for name in classes:
        summary, _ = _docstring_parts(getattr(pydelity, name).__doc__)
        link = _CLASS_PAGES.get(name)
        label = f"[`{name}`](../{link}/)" if link else f"`{name}`"
        class_items.append(f"- {label}: {_prose(summary.split(chr(10) * 2)[0])}")
    body = "\n\n".join(
        [
            _prose(
                "``import pydelity`` gives these functions and classes. "
                + _series([f"``{name}``" for name in with_async])
                + " also have async forms, named with an ``a`` prefix, to await in "
                "code that runs an event loop."
            ),
            "## Functions",
            *sections,
            "## Classes and errors",
            "\n".join(class_items),
        ]
    )
    return _Page(
        body=body,
        description="The functions, classes and errors the pydelity package exports.",
        name="python-api",
        order=3,
        title="Python API",
    )


def survey_checks_page() -> _Page:
    """Describe the survey's checks C1 to C7, its comparisons and its verifier issue.

    Returns
    -------
    _Page
        The page.
    """

    checks = []
    for name, function in inspect.getmembers(validators, inspect.isfunction):
        text, _ = _docstring_parts(function.__doc__)
        match = re.match(r"(C\d+): (.*)", text, flags=re.DOTALL)
        if name.startswith("check_") and match:
            label, rest = match.groups()
            checks.append(
                (
                    int(label[1:]),
                    f"### {label}\n\n{_prose(rest[:1].upper() + rest[1:])}",
                )
            )
    comparisons = []
    for code, function in (
        ("page_number_differs", validators._page_number_issues),
        ("rotation_differs", validators._rotation_issues),
    ):
        text, _ = _docstring_parts(function.__doc__)
        comparisons.append(f"- `{code}`: {_prose(text.split(chr(10) * 2)[0])}")
    compare_text, _ = _docstring_parts(validators.compare_with_facts.__doc__)
    body = "\n\n".join(
        [
            _prose(
                "Each survey answer goes through checks C1 to C7. While retries remain "
                "(``advanced.survey.check_retries``), an answer that fails a check is "
                "sent back to the model with every failure listed, and the last answer "
                "is kept as it is. When the survey's verifier is on "
                "(``advanced.survey.verify``, or ``verify``), it reviews the accepted "
                "answer and may give a corrected one, which goes through the same "
                "checks and is sent back to the verifier while retries remain. The "
                "correction replaces the answer only when it passes every check. Each "
                "check still failing on the kept answer becomes a review issue, and "
                "the kept answer is compared with the measured facts."
            ),
            "## Checks",
            *(text for _, text in sorted(checks)),
            "## Comparisons with the facts",
            _prose(compare_text),
            "\n".join(comparisons),
            _prose(
                "Each difference is a review issue, unless the verifier passed the "
                "answer or its correction was kept."
            ),
            "## Other review issues",
            "### `verifier`",
            _prose(
                "A problem the survey's verifier found when its correction was not "
                "kept, because it gave no correction or its correction failed a check. "
                "The issue gives the problem's category and, when the problem is about "
                "one page, that page."
            ),
        ]
    )
    return _Page(
        body=body,
        description=(
            "The checks every survey answer goes through, its comparisons with the "
            "facts, and the survey verifier's review issues."
        ),
        name="survey-checks",
        order=10,
        title="Survey checks",
    )


if __name__ == "__main__":
    sys.exit(main())

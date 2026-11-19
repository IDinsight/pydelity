"""Tests for the HTML report written at the end of each run."""

# Standard Library
import html as html_text
import os

from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path

# Package Library
import pydelity

from pydelity.surveying.schemas import Facts
from tests.fixtures.mock_providers import MockProviders

# The 6-page fillable test form, with form fields and two repeated lines.
_FORM = "irs_form_w9.pdf"


class _Links(HTMLParser):
    """Collect the image sources, link targets and tags of an HTML page."""

    def __init__(self) -> None:
        """Start with nothing collected."""

        super().__init__()
        self.images: list[str] = []
        self.links: list[str] = []
        self.tags: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record the tag and any ``src`` or ``href`` it carries.

        Parameters
        ----------
        tag
            The tag's name.
        attrs
            Its attributes.
        """

        self.tags.add(tag)
        for name, value in attrs:
            if name == "src" and value is not None:
                self.images.append(value)
            elif name == "href" and value is not None:
                self.links.append(value)


def _parse(path: Path) -> _Links:
    """Parse an HTML file.

    Parameters
    ----------
    path
        The file.

    Returns
    -------
    _Links
        What it holds.
    """

    parser = _Links()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def test_report_shows_every_page_with_findings_and_needs_no_network(
    facts_of: Callable[[str], Facts],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """The report shows each page with its boxes, plus the profile, cost and issues.

    It has no script and no outside address, so it opens from disk offline.
    """

    region = {
        "bbox": {"x0": 0.05, "x1": 0.95, "y0": 0.1, "y1": 0.3},
        "label": "Body",
        "note": "Name and address lines.",
        "page_index": 0,
    }
    answer = survey_answer(facts_of(_FORM), languages=["en", "zz"], regions=[region])
    mock_providers(answers=[answer])

    result = pydelity.run(
        pdf_path(_FORM), advanced={"survey": {"check_retries": 0}}, output_dir="out"
    )

    report = Path("out/report.html")
    html = report.read_text(encoding="utf-8")
    parsed = _parse(report)
    assert "script" not in parsed.tags
    assert not [
        target
        for target in parsed.images + parsed.links
        if target.startswith(("http:", "https:", "//"))
    ]
    assert parsed.images == [f"report/pages/{index:04d}.jpg" for index in range(6)]
    for image in parsed.images:
        assert (Path("out") / image).is_file()
    assert '<div class="box region"' in html
    assert '<span class="box-label">Body</span>' in html
    assert html.count('<div class="box field"') == 23
    assert result.record is not None
    (issue,) = result.record.review
    assert html_text.escape(issue.message) in html
    assert "$0.02" in html
    assert result.survey is not None
    for label in result.survey.profile.labels:
        assert html_text.escape(label.name) in html
    assert result.facts is not None
    for line in result.facts.summary:
        assert html_text.escape(line) in html


def test_report_escapes_text_from_the_pdf_the_user_and_the_model(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Markup in instructions and in the model's labels is shown, never run."""

    labels = [
        {
            "description": "<img src=x onerror=alert(2)>",
            "kinds": ["text"],
            "name": "<b>Bold</b>",
            "role": "body",
        }
    ]
    mock_providers(answers=[survey_answer(labels=labels)])

    pydelity.run(
        pdf_path("irs_form_1040a_1965_scan.pdf"),
        instructions="<script>alert(1)</script>",
        output_dir="out",
    )

    html = Path("out/report.html").read_text(encoding="utf-8")
    parsed = _parse(Path("out/report.html"))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<b>Bold</b>" not in html
    assert "&lt;b&gt;Bold&lt;/b&gt;" in html
    assert "x" not in parsed.images
    assert "script" not in parsed.tags


def test_page_images_are_rendered_only_when_missing(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """A rerun keeps the page images it has and renders only a missing one."""

    mock_providers(answers=[survey_answer()])
    pydelity.run(pdf_path("irs_form_1040a_1965_scan.pdf"), output_dir="out")
    first, second = Path("out/report/pages/0000.jpg"), Path("out/report/pages/0001.jpg")
    os.utime(first, (1_000_000_000, 1_000_000_000))
    os.utime(second, (1_000_000_000, 1_000_000_000))
    second.unlink()

    pydelity.run(pdf_path("irs_form_1040a_1965_scan.pdf"), output_dir="out")

    assert first.stat().st_mtime == 1_000_000_000
    assert second.is_file()
    assert second.stat().st_mtime > 1_000_000_000

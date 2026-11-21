"""Tests for the survey step: the request, check retries, the profile and its issues.

Model answers come from the stand-in provider server, so each test controls exactly
what the model says and can read exactly what pydelity sent.
"""

# Standard Library
import json
import re

from collections.abc import Callable
from pathlib import Path

# Third Party Library
import pytest

from typer.testing import Result

# Package Library
import pydelity

from pydelity.config.loading import resolve_config
from pydelity.errors import SurveyError
from pydelity.surveying.prompts import survey_pdf
from pydelity.surveying.schemas import (
    Facts,
    ItemKind,
    ItemRole,
    PdfFacts,
    PdfSurvey,
    SurveyAnswer,
)
from pydelity.surveying.survey import build_survey
from tests.fixtures.mock_providers import MockProviders

# The 8-page test PDF whose text runs sideways and whose page labels are 23 to 30.
_CAPS = "caps_english_hl_pages_28_35.pdf"

# Words that name a document type or a domain, which prompts, schema field names
# and the item vocabulary must not use.
_DOMAIN_WORDS = (
    "article",
    "assessment",
    "bank",
    "book",
    "chapter",
    "contract",
    "course",
    "curriculum",
    "exam",
    "grade",
    "invoice",
    "learner",
    "legal",
    "lesson",
    "medical",
    "newspaper",
    "novel",
    "patient",
    "presentation",
    "receipt",
    "report",
    "resume",
    "school",
    "skill",
    "slide",
    "student",
    "syllabus",
    "tax",
    "teacher",
    "term",
    "textbook",
)

# The 2-page scanned test PDF, with no text layer.
_SCAN = "irs_form_1040a_1965_scan.pdf"


def _caps_answer(
    facts: Facts, survey_answer: Callable[..., dict], **changes: object
) -> dict:
    """Write an answer for the CAPS excerpt that agrees with its measured facts.

    Parameters
    ----------
    facts
        The CAPS excerpt's facts.
    survey_answer
        The fixture that writes well-formed answers.
    **changes
        Top-level keys to replace.

    Returns
    -------
    dict
        The answer: every page turned 90 degrees, numbered from 23.
    """

    agreeing: dict[str, object] = {
        "page_numbering": [
            {
                "first_page_index": 0,
                "last_page_index": 7,
                "offset": 23,
                "style": "arabic",
            }
        ],
        "rotation": [{"degrees": 90, "first_page_index": 0, "last_page_index": 7}],
    }
    return survey_answer(facts, **(agreeing | changes))


def _field_names(schema: dict) -> set[str]:
    """Collect every property name in a JSON schema, at any depth.

    Parameters
    ----------
    schema
        A Pydantic model's JSON schema.

    Returns
    -------
    set[str]
        The property names.
    """

    names: set[str] = set()
    for definition in [schema, *schema.get("$defs", {}).values()]:
        names.update(definition.get("properties", {}))
    return names


def _model_requests(mock: MockProviders) -> list[str]:
    """Return the model requests the stand-in received, each as one JSON string.

    Parameters
    ----------
    mock
        The stand-in server.

    Returns
    -------
    list[str]
        The bodies of the model requests, in order.
    """

    return [
        json.dumps(request.body, ensure_ascii=False)
        for request in mock.requests
        if request.route == "model"
    ]


def test_an_answer_that_fails_a_check_is_sent_back_with_each_failure(
    facts_of: Callable[[str], Facts],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """A first answer missing a repeated line is sent back; the second is accepted.

    The retry message names the check and the missing line, both answers are
    ledger lines, and the stored checks record two attempts and no failure.
    """

    facts = facts_of(_CAPS)
    complete = _caps_answer(facts, survey_answer)
    missing = dict(complete, non_artifact_lines=complete["non_artifact_lines"][:-1])
    mock = mock_providers(answers=[missing, complete])

    result = pydelity.run(pdf_path(_CAPS), output_dir="out")

    requests = _model_requests(mock)
    assert len(requests) == 2
    assert "artifacts: repeated line R8" not in requests[0]
    assert "artifacts: repeated line R8" in requests[1]
    assert result.survey is not None
    assert {(check.passed, check.attempts) for check in result.survey.checks} == {
        (True, 2)
    }
    assert result.survey.issues == []
    assert [entry.request for entry in result.ledger] == [1, 2]


def test_an_answer_that_never_parses_fails_the_survey(
    mock_providers: Callable[..., MockProviders], pdf_path: Callable[[str], Path]
) -> None:
    """An answer that is not the answer format raises `SurveyError` after the retries.

    The run is recorded as failed, with the way the PDF reached the model, no
    survey is saved, and the report is written.
    """

    mock = mock_providers(answers=["I cannot answer in that format."])

    with pytest.raises(SurveyError, match="no usable survey answer"):
        pydelity.run(
            pdf_path(_SCAN), advanced={"survey": {"check_retries": 1}}, output_dir="out"
        )

    assert len(_model_requests(mock)) == 2
    record = pydelity.load("out").record
    assert record is not None
    assert (record.status, record.steps[0].status) == ("failed", "failed")
    assert record.steps[0].pdf_transport == "upload"
    assert record.error is not None
    assert record.error.startswith("SurveyError: ")
    assert not Path("out/pdf_survey.json").exists()
    assert Path("out/report.html").is_file()


def test_answers_that_differ_from_the_facts_are_kept_and_listed_by_page(
    facts_of: Callable[[str], Facts],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """A well-formed answer that disagrees with the facts is accepted at once.

    The profile keeps the model's rotation and numbering. Each page whose measured
    turn or printed number differs gets one review issue; pages that agree get none.
    """

    facts = facts_of(_CAPS)
    answer = _caps_answer(
        facts,
        survey_answer,
        page_numbering=[
            {
                "first_page_index": 0,
                "last_page_index": 3,
                "offset": 23,
                "style": "arabic",
            },
            {
                "first_page_index": 4,
                "last_page_index": 7,
                "offset": None,
                "style": "none",
            },
        ],
        rotation=[{"degrees": 90, "first_page_index": 0, "last_page_index": 3}],
    )
    mock = mock_providers(answers=[answer])

    survey: PdfSurvey = pydelity.survey(pdf_path(_CAPS), output_dir="out")

    assert len(_model_requests(mock)) == 1
    assert all(check.passed and check.attempts == 1 for check in survey.checks)
    assert [
        (r.first_page_index, r.last_page_index) for r in survey.profile.rotation
    ] == [(0, 3)]
    assert len(survey.profile.page_numbering) == 2
    rotation = [i for i in survey.issues if i.check == "rotation_differs"]
    numbers = [i for i in survey.issues if i.check == "page_number_differs"]
    assert [(i.page_index, i.details) for i in rotation] == [
        (page, {"measured": 90, "profile": 0}) for page in range(4, 8)
    ]
    assert [(i.page_index, i.details) for i in numbers] == [
        (page, {"measured": page + 23, "profile": None, "source": "page_label"})
        for page in range(4, 8)
    ]
    assert "page index 4" in rotation[0].message
    assert "27" in numbers[0].message


def test_checks_still_failing_after_the_retries_are_listed_for_review(  # noqa: PLR0913, PLR0917 - fixtures
    facts_of: Callable[[str], Facts],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
    tmp_path: Path,
) -> None:
    """After the last allowed answer, each failure is a review issue in both files.

    The command summary counts the issues by check and lists each with its step and
    its page numbered from 1, as a PDF viewer shows it.
    """

    facts = facts_of(_CAPS)
    complete = _caps_answer(facts, survey_answer)
    flawed = dict(
        complete,
        non_artifact_lines=complete["non_artifact_lines"][:-1],
        regions=[
            {
                "bbox": {"x0": 0.1, "x1": 0.9, "y0": 0.1, "y1": 0.2},
                "label": "Sidebar",
                "note": "",
                "page_index": 2,
            }
        ],
    )
    mock = mock_providers(answers=[flawed])
    config_file = tmp_path / "pydelity.yaml"
    config_file.write_text("advanced:\n  survey:\n    check_retries: 1\n")

    result = run_cli(
        [str(pdf_path(_CAPS)), "--config", str(config_file), "-d", "out", "--yes"]
    )

    assert result.exit_code == 0, result.output
    assert len(_model_requests(mock)) == 2
    survey = pydelity.load("out").survey
    record = pydelity.load("out").record
    assert survey is not None
    assert record is not None
    assert [(i.step, i.check, i.page_index) for i in survey.issues] == [
        ("survey", "labels", 2),
        ("survey", "artifacts", None),
    ]
    assert record.review == survey.issues
    assert "Review issues by check: labels 1, artifacts 1" in result.stderr
    assert "survey, page 3: labels: a region on page index 2" in result.stderr
    assert "survey: artifacts: repeated line R8" in result.stderr


def test_profile_owns_other_dedupes_kinds_and_converts_region_boxes(
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
    tmp_path: Path,
) -> None:
    """The stored profile has Python's ``other`` last and region boxes in points.

    A model-made ``other`` is replaced, kinds are listed once, a label without
    kinds may be given to every kind, and each label keeps exactly one role.
    """

    config = resolve_config(pdf=pdf_path(_SCAN), settings={"output_dir": tmp_path})
    facts: PdfFacts = pydelity.measure(config=config)
    labels = [
        {
            "description": "",
            "kinds": ["text", "text"],
            "name": "Heading",
            "role": "heading",
        },
        {"description": "", "kinds": ["code"], "name": "Other", "role": "aside"},
        {"description": "", "kinds": [], "name": "Box", "role": "aside"},
    ]
    regions = [
        {
            "bbox": {"x0": 0.25, "x1": 0.75, "y0": 0.5, "y1": 1.0},
            "label": "HEADING",
            "note": "Title block.",
            "page_index": 1,
        }
    ]
    answer = SurveyAnswer.model_validate(survey_answer(labels=labels, regions=regions))

    survey = build_survey(answer=answer, attempts=1, config=config, facts=facts)

    profile = survey.profile
    assert [label.name for label in profile.labels] == ["Heading", "Box", "other"]
    assert profile.labels[0].kinds == [ItemKind.TEXT]
    assert profile.labels[1].kinds == list(ItemKind)
    other = profile.labels[-1]
    assert (other.role, other.kinds) == (ItemRole.BODY, list(ItemKind))
    for label in profile.labels:
        assert isinstance(label.role, ItemRole)
        assert label.kinds
    page = facts.facts.pages[1]
    (region,) = survey.proposal.regions
    assert region.label == "Heading"
    assert region.bbox == (
        round(0.25 * page.width_pt, 2),
        round(0.5 * page.height_pt, 2),
        round(0.75 * page.width_pt, 2),
        round(page.height_pt, 2),
    )
    assert survey.facts == facts.facts
    assert survey.inputs.facts_fingerprint == facts.fingerprint


def test_prompt_schema_and_vocabulary_name_no_document_type() -> None:
    """The prompt, the answer and output field names and the item enums are neutral.

    None of them uses a word that names a document type or a domain.
    """

    prompts = survey_pdf(
        facts_summary=["2 pages (indexes 0-1); page indexes start at 0."],
        instructions=None,
        languages=[],
        page_count=2,
        repeated_lines=[],
    )
    names = (
        _field_names(SurveyAnswer.model_json_schema())
        | _field_names(PdfSurvey.model_json_schema())
        | _field_names(PdfFacts.model_json_schema())
    )
    vocabulary = [kind.value for kind in ItemKind] + [role.value for role in ItemRole]
    texts = {
        "prompt": f"{prompts.system_message}\n{prompts.user_message}",
        "field names": " ".join(name.replace("_", " ") for name in sorted(names)),
        "vocabulary": " ".join(vocabulary),
    }

    found = {
        where: word
        for where, text in texts.items()
        for word in _DOMAIN_WORDS
        if re.search(rf"\b{word}s?\b", text, flags=re.IGNORECASE)
    }

    assert found == {}


def test_request_sends_the_facts_as_hints_with_every_repeated_line(
    facts_of: Callable[[str], Facts],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """The request holds the facts summary, each repeated line and the user's text.

    Its instructions tell the model to treat the facts as hints and to answer with
    its own reading where they differ, and end with the survey's instructions from
    the user.
    """

    facts = facts_of(_CAPS)
    mock = mock_providers(answers=[_caps_answer(facts, survey_answer)])

    saved = pydelity.measure(pdf_path(_CAPS), output_dir="out")
    pydelity.survey(
        pdf_path(_CAPS),
        advanced={"survey": {"instructions": "Margin notes are content."}},
        languages=["en"],
        output_dir="out",
    )

    (request,) = _model_requests(mock)
    text = json.loads(request)
    sent = json.dumps(text["messages"], ensure_ascii=False)
    system = json.dumps(text.get("system", ""), ensure_ascii=False)
    for line in saved.summary:
        assert json.dumps(line, ensure_ascii=False)[1:-1] in sent
    for line in facts.repeated_lines:
        assert line.id in sent
        assert json.dumps(line.text, ensure_ascii=False)[1:-1] in sent
    assert "Margin notes are content." not in sent
    assert "Treat them as hints" in system
    assert system.index("The user's instructions for this PDF follow.") > (
        system.index("Treat them as hints")
    )
    assert "Margin notes are content." in system
    assert "answer with what you read" in system


def test_user_languages_lead_and_rejected_model_tags_become_review_issues(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """User tags come first in standard form; a tag C7 rejects is left out.

    With no check retries the first answer is accepted, and its rejected tag is a
    review issue. Pages with nothing measured never differ from the facts, so the
    answer's rotation and page numbering give no issue.
    """

    answer = survey_answer(
        languages=["en", "eng", "zz", "ar"],
        page_numbering=[
            {
                "first_page_index": 0,
                "last_page_index": 1,
                "offset": 5,
                "style": "arabic",
            }
        ],
        rotation=[{"degrees": 90, "first_page_index": 0, "last_page_index": 1}],
    )
    mock = mock_providers(answers=[answer])

    survey = pydelity.survey(
        pdf_path(_SCAN),
        advanced={
            "survey": {"check_retries": 0, "instructions": "Treat stamps as content."}
        },
        languages=["EN_us"],
        output_dir="out",
    )

    assert survey.profile.languages == ["en-US", "en", "ar"]
    assert survey.inputs.instructions == "Treat stamps as content."
    assert "Treat stamps as content." not in survey.profile.model_dump_json()
    assert [(issue.check, issue.details) for issue in survey.issues] == [
        ("languages", {"proposed": "zz"})
    ]
    assert survey.issues[0].step == "survey"
    languages = next(check for check in survey.checks if check.name == "languages")
    assert (languages.passed, languages.attempts) == (False, 1)
    assert len(_model_requests(mock)) == 1

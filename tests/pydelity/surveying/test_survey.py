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
from pydelity.errors import ExitCode, SurveyError
from pydelity.surveying.prompts import survey_pdf, verify_survey
from pydelity.surveying.schemas import (
    Facts,
    ItemKind,
    ItemRole,
    PdfFacts,
    PdfSurvey,
    SurveyAnswer,
)
from pydelity.surveying.survey import build_survey
from pydelity.surveying.validators import retry_message, run_checks
from tests.fixtures.mock_providers import MockProviders, RecordedRequest

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

# What PydanticAI puts around a retry message in the request that follows it.
_RETRY_FEEDBACK = re.compile(
    r"<pyai:retry_feedback>(.*?)</pyai:retry_feedback>", flags=re.DOTALL
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


def _user_text(request: RecordedRequest) -> str:
    """Return the text of an Anthropic request's first user message.

    Parameters
    ----------
    request
        A model request to the Anthropic stand-in.

    Returns
    -------
    str
        The message's text, without the PDF.
    """

    messages = request.body["messages"]
    assert isinstance(messages, list)
    message = messages[0]
    (text,) = [part["text"] for part in message["content"] if part["type"] == "text"]
    return text


def test_a_failed_verifier_request_stops_the_run_and_leaves_the_saved_survey(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    run_cli: Callable[..., Result],
    survey_answer: Callable[..., dict],
) -> None:
    """A verifier request the provider rejects fails the run with exit code 1.

    The command shows the provider's message. The survey made earlier without a
    verifier stays as it was, though the new survey answer differs from it.
    ``run.json`` records the survey step as failed, and the ledger keeps the paid
    survey request.
    """

    heading = {
        "description": "Titles.",
        "kinds": ["text"],
        "name": "Heading",
        "role": "heading",
    }
    mock = mock_providers(answers=[survey_answer(), survey_answer(labels=[heading])])
    pydelity.run(pdf_path(_SCAN), output_dir="out")
    saved = Path("out/pdf_survey.json").read_bytes()
    before = len(mock.requests)

    result = run_cli([str(pdf_path(_SCAN)), "-d", "out", "-y", "--verify"])

    assert result.exit_code == ExitCode.FAILED, result.output
    assert "No survey verdict (mock provider)" in result.stderr
    sent = [(r.agent, r.status) for r in mock.requests[before:]]
    assert sent == [("surveyor", 200), ("verifier", 400)]
    assert Path("out/pdf_survey.json").read_bytes() == saved
    loaded = pydelity.load("out")
    assert loaded.record is not None
    assert (loaded.record.status, loaded.record.steps[0].status) == ("failed", "failed")
    assert [line.agent for line in loaded.ledger] == ["surveyor", "surveyor"]


def test_a_verifier_that_gives_no_usable_verdict_fails_the_survey(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """A verifier answer that is not a verdict raises `SurveyError` naming it."""

    mock = mock_providers(
        answers=[survey_answer()], survey_verdicts=["The survey looks fine to me."]
    )

    with pytest.raises(
        SurveyError, match=r"^The verifier gave no usable verdict on the survey: "
    ):
        pydelity.survey(
            pdf_path(_SCAN),
            advanced={"survey": {"check_retries": 0, "verify": True}},
            model="openai:gpt-6.2-astra",
            output_dir="out",
        )

    agents = [request.agent for request in mock.requests if request.route == "model"]
    assert agents == ["surveyor", "verifier"]


def test_an_answer_that_fails_a_check_is_sent_back_with_each_failure(
    facts_of: Callable[[str], Facts],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """A first answer missing a repeated line is sent back, and the second is kept.

    Both answers turn only half the pages, so they differ from the measured
    rotation on 4 pages. The retry message names the failed check and the missing
    line and nothing of the rotation differences. Both answers are ledger lines, the
    stored checks record two attempts and no failure, and the rotation differences
    of the kept answer are its hints and its review list.
    """

    facts = facts_of(_CAPS)
    complete = _caps_answer(
        facts,
        survey_answer,
        rotation=[{"degrees": 90, "first_page_index": 0, "last_page_index": 3}],
    )
    missing = dict(complete, non_artifact_lines=complete["non_artifact_lines"][:-1])
    mock = mock_providers(answers=[missing, complete])

    result = pydelity.run(pdf_path(_CAPS), output_dir="out")

    requests = _model_requests(mock)
    assert len(requests) == 2
    assert _RETRY_FEEDBACK.findall(requests[0]) == []
    (retry,) = _RETRY_FEEDBACK.findall(requests[1])
    assert "artifacts: repeated line R8" in retry
    assert "rotation_differs" not in retry
    assert result.survey is not None
    assert {(check.passed, check.attempts) for check in result.survey.checks} == {
        (True, 2)
    }
    assert [
        (hint.name, [difference.page_index for difference in hint.differences])
        for hint in result.survey.hints
    ] == [("rotation_differs", [4, 5, 6, 7]), ("page_number_differs", [])]
    assert [issue.check for issue in result.survey.issues] == ["rotation_differs"] * 4
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
    turn or printed number differs is one difference in the survey's hints and one
    review issue, and pages that agree have none.
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
    assert [hint.name for hint in survey.hints] == [
        "rotation_differs",
        "page_number_differs",
    ]
    assert [
        (issue.check, issue.message, issue.page_index) for issue in survey.issues
    ] == [
        (hint.name, difference.message, difference.page_index)
        for hint in survey.hints
        for difference in hint.differences
    ]


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

    survey = build_survey(
        answer=answer, attempts=1, config=config, facts=facts, verification=None
    )

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


def test_prompt_schema_and_vocabulary_name_no_document_type(
    survey_answer: Callable[..., dict],
) -> None:
    """The prompts, the answer and output field names and the item enums are neutral.

    None of them, the verifier's prompt and verdict included, uses a word that names
    a document type or a domain.
    """

    prompts = survey_pdf(
        facts_summary=["2 pages (indexes 0-1); page indexes start at 0."],
        instructions=None,
        languages=[],
        page_count=2,
        repeated_lines=[],
    )
    verifier = verify_survey(
        answer=SurveyAnswer.model_validate(survey_answer()),
        differences={},
        failures={},
        instructions=None,
        survey_message=prompts.user_message,
    )
    names = (
        _field_names(SurveyAnswer.model_json_schema())
        | _field_names(PdfSurvey.model_json_schema())
        | _field_names(PdfFacts.model_json_schema())
    )
    vocabulary = [kind.value for kind in ItemKind] + [role.value for role in ItemRole]
    texts = {
        "prompt": f"{prompts.system_message}\n{prompts.user_message}",
        "verifier prompt": f"{verifier.system_message}\n{verifier.user_message}",
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


def test_the_verifier_request_carries_the_survey_s_file_text_failures_and_differences(
    facts_of: Callable[[str], Facts],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
    survey_verdict: Callable[..., dict],
) -> None:
    """The verifier reviews the accepted answer on the survey's own upload.

    Its request names the survey request's file, so the run makes one upload. Its
    text is the survey's, then the answer, the check it still fails and its
    differences from the facts, under a heading that calls the facts hints the PDF
    overrides. Its instructions hold the review list, the verdict rules, which say a
    correction must pass the checks and need not agree with the facts, and the
    survey's rules, then the user's survey instructions. Each request is a survey
    ledger line of its own agent, and the survey's cost is their sum. The verdict
    passes the answer, which still fails its check with no retries left, so the
    answer is kept, its failure is the only review issue and the survey completes.
    """

    facts = facts_of(_CAPS)
    answer = _caps_answer(
        facts,
        survey_answer,
        languages=["en", "zz"],
        rotation=[{"degrees": 90, "first_page_index": 0, "last_page_index": 3}],
    )
    mock = mock_providers(answers=[answer], survey_verdicts=[survey_verdict()])

    result = pydelity.run(
        pdf_path(_CAPS),
        advanced={
            "survey": {
                "check_retries": 0,
                "instructions": "Margin notes are content.",
                "verify": True,
            }
        },
        output_dir="out",
    )

    assert [request.route for request in mock.requests] == ["upload", "model", "model"]
    surveyor, verifier = mock.requests[1:]
    assert (surveyor.agent, verifier.agent) == ("surveyor", "verifier")
    assert verifier.file_ids == surveyor.file_ids != []
    survey_text = _user_text(surveyor)
    text = _user_text(verifier)
    assert text.startswith(f"{survey_text}\n\nThe survey answer to review:\n")
    reviewed, rest = text.removeprefix(survey_text).split(
        "\n\nChecks it still fails:\n"
    )
    failing, differences = rest.split(
        "\n\nDifferences from the measured facts, which are hints the PDF overrides:\n"
    )
    assert json.loads(reviewed.split(":\n", 1)[1]) == (
        SurveyAnswer.model_validate(answer).model_dump(mode="json")
    )
    (failure,) = failing.splitlines()
    assert failure.startswith("- languages: ")
    assert "zz" in failure
    lines = differences.splitlines()
    assert len(lines) == 4
    assert all(
        line.startswith("- rotation_differs: ") and f"page index {page}" in line
        for line, page in zip(lines, range(4, 8), strict=True)
    )
    system = json.dumps(verifier.body["system"], ensure_ascii=False)
    markers = [
        "You review a survey of a PDF, made by another model",
        "Review the survey against the PDF for:",
        "Give a verdict.",
        "Labels. Make labels",
        "The user's instructions for this PDF follow.",
        "Margin notes are content.",
    ]
    assert [system.index(marker) for marker in markers] == sorted(
        system.index(marker) for marker in markers
    )
    assert "Review the survey" not in json.dumps(surveyor.body["system"])
    assert (
        "The measured facts are hints, which can be wrong. A difference from them is "
        "a problem only when the PDF shows that the survey is wrong, and a "
        "correction need not agree with them."
    ) in system
    ledger = result.ledger
    assert [(line.step, line.page_index, line.agent) for line in ledger] == [
        ("survey", None, "surveyor"),
        ("survey", None, "verifier"),
    ]
    assert result.record is not None
    paid = sum(line.cost_usd for line in ledger if line.cost_usd is not None)
    assert result.record.cost.by_step["survey"] == paid
    assert result.record.steps[0].cost_usd == paid
    assert result.record.steps[0].status == "completed"
    assert result.survey is not None
    assert result.survey.verification is not None
    assert result.survey.verification.verdict.passed
    assert [(issue.check, issue.message) for issue in result.survey.issues] == [
        ("languages", failure.removeprefix("- "))
    ]


@pytest.mark.parametrize(
    "outcome", ["passed", "correction_kept", "correction_not_kept"]
)
def test_the_verifier_s_verdict_decides_the_kept_answer_and_its_issues(  # noqa: PLR0913, PLR0917 - fixtures
    facts_of: Callable[[str], Facts],
    log_messages: list[tuple[str, str]],
    mock_providers: Callable[..., MockProviders],
    outcome: str,
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
    survey_verdict: Callable[..., dict],
) -> None:
    """The survey keeps the answer or the verifier's correction, as the verdict says.

    The answer turns only half the pages, so it differs from the facts on 4 pages.
    A passed verdict keeps it with no review issue. A correction that fails a check is
    sent back with that failure alone, and its fixed version, which still differs
    from the facts, is kept, with the user's language first and the facts unchanged.
    A correction that still fails on the last attempt is not kept, so the
    differences and each problem are listed. The survey's hints hold the 4
    differences whatever the verdict. ``pdf_survey.json``, the report and the log
    line give the verifier's outcome.
    """

    facts = facts_of(_CAPS)
    answer = _caps_answer(
        facts,
        survey_answer,
        rotation=[{"degrees": 90, "first_page_index": 0, "last_page_index": 3}],
    )
    margin = {
        "description": "Notes in the margin.",
        "kinds": ["text"],
        "name": "Margin note",
        "role": "aside",
    }
    correction = dict(answer, labels=[*answer["labels"], margin])
    failing = dict(correction, languages=["zz"])
    labels = ("labels", "The margin notes on page 3 have no label.", 2)
    regions = ("regions", "The box around the margin notes is missing.", None)
    verdicts = {
        "passed": [survey_verdict()],
        "correction_kept": [
            survey_verdict(labels, corrected=failing),
            survey_verdict(labels, corrected=correction),
        ],
        "correction_not_kept": [survey_verdict(labels, regions, corrected=failing)],
    }[outcome]
    mock = mock_providers(answers=[answer], survey_verdicts=verdicts)

    pydelity.run(
        pdf_path(_CAPS),
        advanced={"survey": {"check_retries": 1}},
        languages=["fr"],
        output_dir="out",
        verify=True,
    )

    survey = pydelity.load("out").survey
    assert survey is not None
    verification = survey.verification
    assert verification is not None
    agents = [r.agent for r in mock.requests if r.route == "model"]
    assert agents == ["surveyor"] + ["verifier"] * (1 if outcome == "passed" else 2)
    kept = correction if outcome == "correction_kept" else answer
    assert [label.name for label in survey.profile.labels] == [
        *(label["name"] for label in kept["labels"]),
        "other",
    ]
    assert survey.profile.languages == ["fr", "en"]
    assert survey.facts == facts
    assert {(check.passed, check.attempts) for check in survey.checks} == {
        (True, 2 if outcome == "correction_kept" else 1)
    }
    assert verification.verdict.model_dump(mode="json") == verdicts[-1]
    attempts, applied, failures, report_text, log_text = {
        "passed": (1, False, [], "passed", "verifier passed"),
        "correction_kept": (
            2,
            True,
            [],
            "found 1 problem and its correction was kept",
            "verifier corrected the survey",
        ),
        "correction_not_kept": (
            2,
            False,
            [("languages", False, 2)],
            "found 2 problems, listed for review",
            "verifier found 2 problems",
        ),
    }[outcome]
    assert (verification.attempts, verification.correction_applied) == (
        attempts,
        applied,
    )
    assert [
        (check.name, check.passed, check.attempts)
        for check in verification.correction_failures
    ] == failures
    report = Path("out/report.html").read_text(encoding="utf-8")
    assert f"<dt>Verifier</dt><dd>{report_text}</dd>" in report
    (finished,) = [m for _, m in log_messages if m.startswith("Survey finished:")]
    assert f"; {log_text}; " in finished
    if outcome == "correction_kept":
        retried = _model_requests(mock)[2]
        sent_back = retry_message(
            run_checks(SurveyAnswer.model_validate(failing), facts)
        )
        assert "Your corrected survey does not pass every check." in retried
        assert json.dumps(sent_back)[1:-1] in retried
        assert "does not pass every check" not in _model_requests(mock)[1]
        (feedback,) = _RETRY_FEEDBACK.findall(retried)
        assert "rotation_differs" not in feedback
    assert [
        (hint.name, [difference.page_index for difference in hint.differences])
        for hint in survey.hints
    ] == [("rotation_differs", [4, 5, 6, 7]), ("page_number_differs", [])]
    listed = [] if outcome != "correction_not_kept" else [labels, regions]
    differences = list(range(4, 8)) if listed else []
    assert [
        issue.page_index for issue in survey.issues if issue.check == "rotation_differs"
    ] == differences
    assert [
        (issue.message, issue.details, issue.page_index, issue.item_id, issue.step)
        for issue in survey.issues
        if issue.check == "verifier"
    ] == [
        (f"verifier: {text}", {"category": category}, page, None, "survey")
        for category, text, page in listed
    ]
    assert len(survey.issues) == len(differences) + len(listed)


def test_turning_the_survey_s_verifier_on_surveys_again_only_what_no_verifier_reviewed(
    canned_answers: Callable[[str], dict[str, object]],
    log_messages: list[tuple[str, str]],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_verdict: Callable[..., dict],
) -> None:
    """A survey made without a verifier is surveyed again once its verifier is on.

    The estimate says the survey will run again. The new survey reuses the recorded
    upload, and since the verifier passed it, the page files are reused. Turning the
    verifier off, or on again, then reuses the reviewed survey with no request.
    """

    model = "openai:gpt-6.2-astra"
    on = {"survey": {"verify": True}}
    mock = mock_providers(**canned_answers(_SCAN), survey_verdicts=[survey_verdict()])
    first = pydelity.run(pdf_path(_SCAN), model=model, output_dir="out", pause=False)
    assert first.survey is not None
    assert first.survey.verification is None
    (finished,) = [m for _, m in log_messages if m.startswith("Survey finished:")]
    assert "; no verifier; " in finished

    estimate = pydelity.estimate(
        pdf_path(_SCAN), advanced=on, model=model, output_dir="out", pause=False
    )
    before = len(mock.requests)
    second = pydelity.run(
        pdf_path(_SCAN), advanced=on, model=model, output_dir="out", pause=False
    )

    assert (estimate.steps[0].name, estimate.steps[0].reused) == ("survey", False)
    sent = [(r.route, r.agent) for r in mock.requests[before:]]
    assert sent == [("model", "surveyor"), ("model", "verifier")]
    assert any(
        m.startswith("No verifier reviewed the survey in ") for _, m in log_messages
    )
    assert second.survey is not None
    assert second.survey.verification is not None
    assert second.survey.verification.verdict.passed
    assert second.survey.fingerprint == first.survey.fingerprint
    assert second.pages == first.pages
    for advanced in ({}, on):
        before = len(mock.requests)
        again = pydelity.run(
            pdf_path(_SCAN), advanced=advanced, model=model, output_dir="out"
        )
        assert len(mock.requests) == before
        assert again.survey == second.survey


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

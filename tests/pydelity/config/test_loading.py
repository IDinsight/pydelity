"""Tests for settings: config files, precedence, validation and the example files."""

# Standard Library
import json
import shutil

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

# Third Party Library
import pytest
import yaml

from pydantic import BaseModel

# Package Library
import pydelity

from pydelity.config.loading import resolve_config
from pydelity.config.schemas import (
    AdvancedConfig,
    Config,
    ExtractionConfig,
    ModelPrices,
    SurveyConfig,
    UploadsConfig,
)
from pydelity.errors import ConfigError
from pydelity.surveying.facts import facts_fingerprint
from pydelity.surveying.schemas import Facts, PdfFacts, PdfIdentity
from pydelity.surveying.survey import survey_fingerprint, survey_inputs
from tests.fixtures.mock_providers import MockProviders

# The repo's root folder, three levels above this file's folder.
_REPO_ROOT = Path(__file__).absolute().parents[3]

# The example config files users copy.
_EXAMPLES = (
    _REPO_ROOT / "examples" / "config.json",
    _REPO_ROOT / "examples" / "config.yaml",
)


def _field_names(model: type[BaseModel]) -> set[str]:
    """Return the setting names a settings model accepts.

    Parameters
    ----------
    model
        The settings model.

    Returns
    -------
    set[str]
        Its field names.
    """

    return set(model.model_fields)


def _read_example(path: Path) -> dict:
    """Read an example config file as plain data.

    Parameters
    ----------
    path
        The JSON or YAML file.

    Returns
    -------
    dict
        Its settings, as written.
    """

    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)


def test_config_file_paths_resolve_against_its_folder_and_keywords_win(
    pdf_path: Callable[[str], Path], tmp_path: Path
) -> None:
    """A YAML file sets every top-level setting; relative paths are the file's.

    Each step's instructions and page extraction's own model sit under
    ``advanced``. A PDF and a model given as keywords win over the file's, and page
    extraction's own model wins over the global one.
    """

    folder = tmp_path / "settings"
    (folder / "docs").mkdir(parents=True)
    shutil.copy(pdf_path("irs_form_w9.pdf"), folder / "docs" / "form.pdf")
    config_file = folder / "run.yml"
    config_file.write_text(
        "\n".join(
            [
                "pdf: docs/form.pdf",
                "output_dir: results",
                "languages: [ar, EN_us]",
                "model: openai:gpt-6.2-astra",
                "max_cost: 2.50",
                "overwrite: true",
                "pages: 5, 1-3, 2",
                "pause: false",
                "advanced:",
                "  extraction:",
                "    concurrent_pages: 3",
                "    instructions: Read each page's fields.",
                "    model: anthropic:claude-sonnet-5-5",
                "  provider_retries: 4",
                "  survey:",
                "    effort: medium",
                "    instructions: Read the fields.",
            ]
        ),
        encoding="utf-8",
    )
    other_pdf = pdf_path("irs_pub1_arabic.pdf")

    from_file = resolve_config(config=config_file)
    overridden = resolve_config(
        config=config_file,
        pdf=other_pdf,
        settings={"model": "anthropic:claude-sonnet-5-5"},
    )

    assert from_file.pdf == folder / "docs" / "form.pdf"
    assert from_file.output_folder == folder / "results"
    assert from_file.languages == ["ar", "en-US"]
    assert from_file.model == "openai:gpt-6.2-astra"
    assert from_file.max_cost == Decimal("2.50")
    assert from_file.overwrite is True
    assert from_file.pages == "1-3,5"
    assert from_file.pause is False
    assert from_file.advanced.extraction.concurrent_pages == 3
    assert from_file.advanced.extraction.instructions == "Read each page's fields."
    assert from_file.advanced.provider_retries == 4
    assert from_file.advanced.survey.effort == "medium"
    assert from_file.advanced.survey.check_retries == 2
    assert from_file.advanced.survey.instructions == "Read the fields."
    assert from_file.survey_model.setting == "openai:gpt-6.2-astra"
    assert from_file.extraction_model.setting == "anthropic:claude-sonnet-5-5"
    assert overridden.pdf == other_pdf
    assert overridden.model == "anthropic:claude-sonnet-5-5"
    assert overridden.output_folder == folder / "results"


def test_every_invalid_setting_is_named_in_one_error_before_any_request(
    mock_providers: Callable[..., MockProviders], survey_answer: Callable[..., dict]
) -> None:
    """One `ConfigError` lists each invalid setting by its path; nothing is sent."""

    mock = mock_providers(answers=[survey_answer()])
    settings = {
        "advanced": {
            "provider_retries": 11,
            "survey": {"check_retries": 9},
            "surveyy": {},
            "uploads": {"expiry_hours": 5000},
        },
        "languages": ["en", "zz"],
        "max_cost": 0,
        "pdf": "missing.pdf",
    }

    with pytest.raises(ConfigError) as raised:
        pydelity.run(config=settings, output_dir="out")

    lines = str(raised.value).splitlines()
    assert lines[0] == "7 invalid settings:"
    paths = sorted(line.split(":")[0].removeprefix("- ") for line in lines[1:])
    assert paths == [
        "advanced.provider_retries",
        "advanced.survey.check_retries",
        "advanced.surveyy",
        "advanced.uploads.expiry_hours",
        "languages[1]",
        "max_cost",
        "pdf",
    ]
    assert '- languages[1]: "zz" is not a valid BCP-47 language tag' in str(
        raised.value
    )
    assert mock.requests == []
    assert not Path("out").exists()


@pytest.mark.parametrize("source", ["file", "keyword"])
def test_the_removed_instructions_setting_is_unknown_before_any_request(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    source: str,
    survey_answer: Callable[..., dict],
    tmp_path: Path,
) -> None:
    """A top-level ``instructions`` setting gets the unknown-setting error at once.

    It does so in a config file and as a keyword; instructions are set per step
    under ``advanced`` instead.
    """

    mock = mock_providers(answers=[survey_answer()])
    config_file = tmp_path / "run.yml"
    config_file.write_text("instructions: Read it.", encoding="utf-8")

    pdf = pdf_path("irs_form_w9.pdf")
    start = {
        "file": lambda: pydelity.run(pdf, config=config_file),
        "keyword": lambda: pydelity.run(pdf, instructions="Read it."),
    }[source]

    with pytest.raises(ConfigError) as raised:
        start()

    assert str(raised.value).splitlines() == [
        "1 invalid setting:",
        "- instructions: not a setting pydelity knows",
    ]
    assert mock.requests == []


def test_spellings_of_one_language_tag_resolve_to_one_standard_form(
    facts_of: Callable[[str], Facts], pdf_path: Callable[[str], Path]
) -> None:
    """``en_US``, ``EN-us`` and ``en-US`` give ``en-US`` and the same fingerprint."""

    pdf = pdf_path("irs_form_w9.pdf")
    facts = PdfFacts(
        facts=facts_of("irs_form_w9.pdf"),
        fingerprint=facts_fingerprint("0" * 64),
        measured_at="2026-11-18T00:00:00Z",
        pdf=PdfIdentity(bytes=1, name="irs_form_w9.pdf", page_count=6, sha256="0" * 64),
        probe_version=1,
        pydelity_version="0.0.1",
        schema_version="1.0",
        summary=[],
    )

    resolved = [
        resolve_config(pdf=pdf, settings={"languages": [spelling, "iw"]})
        for spelling in ("en_US", "EN-us", "en-US")
    ]
    fingerprints = {
        survey_fingerprint(survey_inputs(config=config, facts=facts))
        for config in resolved
    }

    assert [config.languages for config in resolved] == [["en-US", "he"]] * 3
    assert len(fingerprints) == 1


@pytest.mark.parametrize(
    ("settings", "survey_model", "extraction_model"),
    [
        (
            {"model": "openai:gpt-6.2-astra"},
            "openai:gpt-6.2-astra",
            "openai:gpt-6.2-astra",
        ),
        (
            {"advanced": {"extraction": {"model": "openai:gpt-6.2-astra"}}},
            "anthropic:claude-opus-5-5",
            "openai:gpt-6.2-astra",
        ),
    ],
    ids=["model", "extraction-model"],
)
def test_each_step_resolves_its_own_model(
    extraction_model: str,
    pdf_path: Callable[[str], Path],
    settings: dict[str, object],
    survey_model: str,
) -> None:
    """Page extraction uses its own model, else ``model``; the survey uses ``model``.

    Page extraction's effort stays ``high`` unless set.
    """

    config = resolve_config(pdf=pdf_path("irs_form_w9.pdf"), settings=settings)

    assert config.survey_model.setting == survey_model
    assert config.extraction_model.setting == extraction_model
    assert config.advanced.extraction.effort == "high"


@pytest.mark.parametrize("example", _EXAMPLES, ids=lambda path: path.name)
def test_example_config_holds_every_setting_at_its_default(
    example: Path, pdf_path: Callable[[str], Path]
) -> None:
    """An example file holds exactly the settings `Config` accepts, at every level.

    It matches the other example's values, and resolving it with a PDF given as an
    argument gives the defaults apart from the PDF and its placeholder price entry.
    """

    data = _read_example(example)
    other = _read_example(next(path for path in _EXAMPLES if path != example))
    advanced = data["advanced"]
    (price_entry,) = advanced["models"].values()
    pdf = pdf_path("irs_form_w9.pdf")

    resolved = resolve_config(config=example, pdf=pdf)

    assert set(data) == _field_names(Config)
    assert set(advanced) == _field_names(AdvancedConfig)
    assert set(advanced["extraction"]) == _field_names(ExtractionConfig)
    assert set(advanced["survey"]) == _field_names(SurveyConfig)
    assert set(advanced["uploads"]) == _field_names(UploadsConfig)
    assert set(price_entry) == _field_names(ModelPrices)
    assert data == other
    expected = Config(advanced={"models": advanced["models"]}, pdf=pdf)
    assert resolved.model_dump() == expected.model_dump()
    assert resolved.output_dir is None
    assert data["pdf"] == "document.pdf"

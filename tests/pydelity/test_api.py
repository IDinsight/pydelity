"""Tests for the Python API: measure, estimate, survey, run, load and async forms.

Runs that call a model use the stand-in provider server. The 2-page scanned PDF has
no repeated lines, so one simple answer fits it.
"""

# Standard Library
import asyncio
import gc
import json
import time
import warnings

from collections.abc import Callable
from pathlib import Path

# Third Party Library
import pydantic_ai
import pytest

# Package Library
import pydelity

from pydelity.errors import ConfigError, OutputError, PydelityWarning
from tests.fixtures.mock_providers import MockProviders

# The output files that only `run` writes.
_RUN_ONLY_FILES = ("report", "report.html", "run.json")

# The 2-page scanned test PDF, with no text layer.
_SCAN = "irs_form_1040a_1965_scan.pdf"

# Each sync API function that runs an event loop, with its async version's name.
_SYNC_FUNCTIONS = (
    (pydelity.estimate, "aestimate"),
    (pydelity.extract, "aextract"),
    (pydelity.measure, "ameasure"),
    (pydelity.run, "arun"),
    (pydelity.survey, "asurvey"),
)


def _never_awaited(caught: list[warnings.WarningMessage]) -> list[str]:
    """Pick out "coroutine was never awaited" warnings.

    Parameters
    ----------
    caught
        Warnings recorded by `warnings.catch_warnings`.

    Returns
    -------
    list[str]
        The messages of the warnings about unawaited coroutines.
    """

    return [
        str(item.message) for item in caught if "never awaited" in str(item.message)
    ]


def test_aextract_runs_the_survey_first_and_load_reads_the_page_files(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
) -> None:
    """`aextract` surveys a new PDF, never pauses, and returns its page files.

    It writes no run record or report, like `survey`. `extract` then reuses the
    survey and the page files, and `load` reads the page files back in page order.
    """

    mock = mock_providers(**canned_answers(_SCAN))

    awaited = asyncio.run(pydelity.aextract(pdf_path(_SCAN), output_dir="out"))

    names = sorted(path.name for path in Path("out").iterdir())
    assert names == [
        "cost.jsonl",
        "figures",
        "pages",
        "pdf_facts.json",
        "pdf_survey.json",
        "uploads.json",
    ]
    assert [page.page_index for page in awaited] == [0, 1]
    requests = len(mock.requests)

    synced = pydelity.extract(pdf_path(_SCAN), output_dir="out")

    assert len(mock.requests) == requests
    assert synced == awaited
    loaded = pydelity.load("out")
    assert loaded.pages == awaited
    assert loaded.record is None
    assert isinstance(loaded.pages[0], pydelity.PageFile)


def test_async_estimate_gives_what_estimate_gives_and_raises_alike(
    pdf_path: Callable[[str], Path],
) -> None:
    """`aestimate` returns the same estimate as `estimate`, and the same error."""

    synced = pydelity.estimate(pdf_path(_SCAN), max_cost="1")
    with pytest.raises(ConfigError) as sync_error:
        pydelity.estimate(pdf_path(_SCAN), languages=["zz"])

    awaited = asyncio.run(pydelity.aestimate(pdf_path(_SCAN), max_cost="1"))
    with pytest.raises(ConfigError) as async_error:
        asyncio.run(pydelity.aestimate(pdf_path(_SCAN), languages=["zz"]))

    assert awaited == synced
    assert str(async_error.value) == str(sync_error.value)


def test_async_measure_gives_what_measure_gives(
    pdf_path: Callable[[str], Path],
) -> None:
    """`ameasure`, awaited in a running loop, returns the same facts as `measure`."""

    synced = pydelity.measure(pdf_path(_SCAN), output_dir="sync")

    awaited = asyncio.run(pydelity.ameasure(pdf_path(_SCAN), output_dir="async"))

    assert awaited.model_dump(exclude={"measured_at"}) == synced.model_dump(
        exclude={"measured_at"}
    )


def test_async_run_gives_what_run_gives_with_the_same_warnings(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
) -> None:
    """`arun` ends like `run` and issues the same `PydelityWarning`.

    Both run the survey and page extraction without a pause and give the same
    pages.
    """

    mock_providers(**canned_answers(_SCAN))
    with pytest.warns(PydelityWarning) as sync_warnings:
        synced = pydelity.run(
            pdf_path(_SCAN),
            allow_over_max_cost=True,
            max_cost="0.0001",
            output_dir="s",
            pause=False,
        )

    with pytest.warns(PydelityWarning) as async_warnings:
        awaited = asyncio.run(
            pydelity.arun(
                pdf_path(_SCAN),
                allow_over_max_cost=True,
                max_cost="0.0001",
                output_dir="a",
                pause=False,
            )
        )

    assert awaited.record is not None
    assert synced.record is not None
    assert awaited.record.status == synced.record.status == "completed"
    assert awaited.survey == synced.survey
    assert [page.items for page in awaited.pages] == [
        page.items for page in synced.pages
    ]
    assert [w.code for w in awaited.record.warnings] == ["max_cost_exceeded"]
    assert [w.code for w in synced.record.warnings] == ["max_cost_exceeded"]
    assert [str(w.message) for w in async_warnings] == [
        str(w.message) for w in sync_warnings
    ]


def test_async_survey_gives_what_survey_gives(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """`asurvey` returns the same survey as `survey` for the same answer."""

    mock_providers(answers=[survey_answer()])
    synced = pydelity.survey(pdf_path(_SCAN), output_dir="sync")

    awaited = asyncio.run(pydelity.asurvey(pdf_path(_SCAN), output_dir="async"))

    assert awaited == synced


def test_cancelling_arun_records_an_interrupted_run_with_valid_files(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Cancelling `arun` mid-request records ``interrupted``; every file still loads."""

    mock = mock_providers(answers=[survey_answer()], delay_seconds=5)

    async def run_then_cancel() -> None:
        """Start a run, cancel it while its model request waits, and await it."""

        task = asyncio.create_task(pydelity.arun(pdf_path(_SCAN), output_dir="out"))
        assert await asyncio.to_thread(mock.wait_for_model_request, 10)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run_then_cancel())

    loaded = pydelity.load("out")
    assert loaded.record is not None
    assert (loaded.record.status, loaded.record.steps[0].status) == (
        "interrupted",
        "stopped",
    )
    assert loaded.facts is not None
    assert loaded.survey is None
    assert loaded.ledger == []
    assert not list(Path("out").glob("*.tmp-*"))


def test_event_loop_stays_responsive_while_measuring(
    pdf_path: Callable[[str], Path],
) -> None:
    """The loop keeps running other tasks while `ameasure` measures the PDF.

    Measuring runs off the loop, so the longest wait between two turns of a ticking
    task is a fraction of the measurement. Measuring on the loop would make that
    wait as long as the whole measurement.
    """

    async def measure_and_tick() -> tuple[float, float, int]:
        """Measure the PDF while a task records the waits between its turns."""

        waits: list[float] = []
        done = asyncio.Event()

        async def tick() -> None:
            """Record how long each turn waits, until the measurement ends."""

            last = time.perf_counter()
            while not done.is_set():
                await asyncio.sleep(0.001)
                now = time.perf_counter()
                waits.append(now - last)
                last = now

        ticker = asyncio.create_task(tick())
        await asyncio.sleep(0)
        started = time.perf_counter()
        await pydelity.ameasure(
            pdf_path("irs_w9_instructions.pdf"), output_dir="out", overwrite=True
        )
        measuring = time.perf_counter() - started
        done.set()
        await ticker
        return measuring, max(waits), len(waits)

    measuring, longest_wait, turns = asyncio.run(measure_and_tick())

    assert turns >= 3
    assert longest_wait < 0.6 * measuring


def test_load_of_a_damaged_file_raises_naming_it(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """`load` raises `OutputError` naming a file that is not valid JSON."""

    mock_providers(answers=[survey_answer()])
    pydelity.run(pdf_path(_SCAN), output_dir="out")
    Path("out/pdf_survey.json").write_text('{"schema_version": "1.0", ', "utf-8")

    with pytest.raises(OutputError, match=r"pdf_survey\.json"):
        pydelity.load("out")


def test_load_of_a_damaged_page_file_raises_naming_it(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
) -> None:
    """`load` raises `OutputError` naming a page file that does not validate."""

    mock_providers(**canned_answers(_SCAN))
    pydelity.extract(pdf_path(_SCAN), output_dir="out")
    Path("out/pages/0001.json").write_text('{"page_index": 1}', "utf-8")

    with pytest.raises(OutputError, match=r"0001\.json"):
        pydelity.load("out")


def test_load_of_a_measured_folder_gives_only_the_facts(
    pdf_path: Callable[[str], Path],
) -> None:
    """A folder that only `measure` wrote loads, with every other part empty."""

    facts = pydelity.measure(pdf_path(_SCAN), output_dir="out")

    loaded = pydelity.load("out")

    assert loaded.facts == facts
    assert (loaded.record, loaded.survey, loaded.ledger) == (None, None, [])


def test_load_of_a_missing_folder_raises(tmp_path: Path) -> None:
    """`load` of a folder that does not exist raises `OutputError` naming it."""

    with pytest.raises(OutputError, match="does not exist"):
        pydelity.load(tmp_path / "nowhere")


def test_load_reads_back_what_run_returned_and_costs_add_up(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """`load` of a run's folder equals the run's result, with no key or network.

    Each response is one ledger line; a run's cost is its own lines, and the
    folder's total counts every run.
    """

    mock_providers(answers=[survey_answer()])
    first = pydelity.run(pdf_path(_SCAN), output_dir="out")
    second = pydelity.run(pdf_path(_SCAN), output_dir="out", overwrite=True)

    loaded = pydelity.load("out")

    assert loaded == second
    assert len(loaded.ledger) == 2
    assert second.record is not None
    assert first.record is not None
    own = [line for line in loaded.ledger if line.run_id == second.record.run_id]
    assert len(own) == 1
    cost = second.record.cost
    assert cost.run_usd == own[0].cost_usd
    assert cost.by_step == {"survey": own[0].cost_usd}
    assert cost.output_folder_usd == sum(
        line.cost_usd for line in loaded.ledger if line.cost_usd is not None
    )
    assert first.record.cost.output_folder_usd == first.record.cost.run_usd
    assert second.record.steps[0].requests == 1


def test_load_works_inside_a_running_loop(pdf_path: Callable[[str], Path]) -> None:
    """`load` is sync only and needs no event loop, so it works inside one."""

    facts = pydelity.measure(pdf_path(_SCAN), output_dir="out")

    async def load_in_loop() -> pydelity.RunResult:
        """Load the folder while this coroutine's loop is running."""

        return pydelity.load("out")

    assert asyncio.run(load_in_loop()).facts == facts


def test_measure_saves_the_facts_with_no_key_and_reuses_them(
    log_messages: list[tuple[str, str]],
    monkeypatch: pytest.MonkeyPatch,
    pdf_path: Callable[[str], Path],
) -> None:
    """`measure` needs no API key or provider and writes ``pdf_facts.json`` only.

    It returns the saved facts and logs their summary; a second call reuses them.
    """

    monkeypatch.delenv("ANTHROPIC_API_KEY")
    monkeypatch.delenv("OPENAI_API_KEY")

    first = pydelity.measure(
        pdf_path("caps_english_hl_pages_28_35.pdf"), output_dir="out"
    )
    second = pydelity.measure(
        pdf_path("caps_english_hl_pages_28_35.pdf"), output_dir="out"
    )

    saved = json.loads(Path("out/pdf_facts.json").read_text(encoding="utf-8"))
    assert sorted(path.name for path in Path("out").iterdir()) == ["pdf_facts.json"]
    assert first == pydelity.PdfFacts.model_validate(saved)
    assert second == first
    info = [text for level, text in log_messages if level == "INFO"]
    for line in first.summary:
        assert f"  {line}" in info
    assert (
        info.count(
            "Facts reused from " + str(Path("out").absolute() / "pdf_facts.json")
        )
        == 1
    )


def test_pages_past_the_pdf_stop_every_function_before_any_request(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """A page number past the PDF's last page raises `ConfigError` naming ``pages``.

    `run`, `extract` and `estimate` all stop before writing anything or sending any
    request.
    """

    mock = mock_providers(answers=[survey_answer()])

    for function in (pydelity.run, pydelity.extract, pydelity.estimate):
        with pytest.raises(ConfigError) as raised:
            function(pdf_path(_SCAN), output_dir="out", pages="1,3-4")
        message = str(raised.value)
        assert "pages" in message
        assert "2 pages" in message

    assert mock.requests == []
    assert not Path("out").exists()


def test_survey_writes_the_step_outputs_but_no_run_record_or_report(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """`survey` saves the facts, the survey, the ledger and the upload record only."""

    mock_providers(answers=[survey_answer()])

    survey = pydelity.survey(pdf_path(_SCAN), output_dir="out")

    names = sorted(path.name for path in Path("out").iterdir())
    assert names == ["cost.jsonl", "pdf_facts.json", "pdf_survey.json", "uploads.json"]
    assert not set(_RUN_ONLY_FILES) & set(names)
    assert pydelity.load("out").survey == survey


@pytest.mark.parametrize(
    ("function", "async_name"), _SYNC_FUNCTIONS, ids=[a for _, a in _SYNC_FUNCTIONS]
)
def test_sync_function_in_a_running_loop_raises_and_writes_nothing(
    async_name: str, function: Callable[..., object], pdf_path: Callable[[str], Path]
) -> None:
    """A sync function called inside an event loop names the async one to await.

    It writes nothing and leaves no unawaited coroutine behind.
    """

    async def call_in_loop() -> None:
        """Call the sync function while this coroutine's loop is running."""

        with pytest.raises(RuntimeError) as raised:
            function(pdf_path(_SCAN), output_dir="out")
        assert f"await pydelity.{async_name}(...)" in str(raised.value)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        asyncio.run(call_in_loop())
        gc.collect()

    assert not Path("out").exists()
    assert _never_awaited(caught) == []


def test_the_python_api_turns_off_pydantic_ai_s_first_run_banner(
    canned_answers: Callable[[str], dict[str, object]],
    mock_providers: Callable[..., MockProviders],
    monkeypatch: pytest.MonkeyPatch,
    pdf_path: Callable[[str], Path],
) -> None:
    """A run from Python turns PydanticAI's first-run banner off, as the CLI does.

    PydanticAI never shows the banner under pytest, so the test checks the flag
    that turns it off rather than the printed output.
    """

    monkeypatch.setattr(pydantic_ai, "BANNER_ENABLED", True)
    mock_providers(**canned_answers(_SCAN))

    pydelity.extract(pdf_path(_SCAN), output_dir="out")

    assert pydantic_ai.BANNER_ENABLED is False


def test_two_async_surveys_on_different_folders_run_in_one_loop(
    mock_providers: Callable[..., MockProviders],
    pdf_path: Callable[[str], Path],
    survey_answer: Callable[..., dict],
) -> None:
    """Two `asurvey` calls gathered in one loop both finish, each in its folder."""

    mock = mock_providers(answers=[survey_answer()], delay_seconds=1.0)

    async def both() -> list[pydelity.PdfSurvey]:
        """Run two surveys at the same time."""

        surveys = await asyncio.gather(
            pydelity.asurvey(pdf_path(_SCAN), output_dir="one"),
            pydelity.asurvey(pdf_path("irs_pub1_arabic.pdf"), output_dir="two"),
        )
        return list(surveys)

    started = time.monotonic()
    one, two = asyncio.run(both())
    elapsed = time.monotonic() - started

    assert one.inputs.pdf_name == _SCAN
    assert two.inputs.pdf_name == "irs_pub1_arabic.pdf"
    assert [len(pydelity.load(f).ledger) for f in ("one", "two")] == [1, 1]
    assert sum(1 for request in mock.requests if request.route == "model") == 2
    # Each model request waits 1 second at the stand-in, so one after the other they
    # would take at least 2 seconds.
    assert elapsed < 1.8

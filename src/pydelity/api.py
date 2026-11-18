"""pydelity's Python API.

Each function is written once as a coroutine (``arun``); its sync version has the same
name without the ``a`` (``run``), takes the same arguments and runs the coroutine with
`pydelity.utils.coroutines.run_coroutine`.
"""

# Standard Library
import asyncio
import json
import os

# Third Party Library
from loguru import logger

# Package Library
from pydelity.config.loading import ConfigSource, resolve_config
from pydelity.surveying.facts import measure_facts
from pydelity.utils.coroutines import run_coroutine
from pydelity.utils.files import remove_stale_temp_files
from pydelity.utils.pdf import open_pdf


async def arun(
    pdf: str | os.PathLike[str] | None = None,
    *,
    config: ConfigSource | None = None,
    **settings: object,
) -> None:
    """Run pydelity on a PDF.

    So far the run checks the settings, opens the PDF, and measures it or reuses its
    saved facts (``pdf_facts.json`` in the output folder); the model call and the
    rest of the run come in later versions.

    Parameters
    ----------
    pdf
        The PDF to process; it wins over a ``pdf`` in ``config``.
    config
        A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a mapping
        of settings.
    **settings
        Settings by name, such as ``model="openai:gpt-6.2-astra"`` or
        ``advanced={"survey": {"effort": "medium"}}``. They win over ``config``.

    Raises
    ------
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    """

    resolved = resolve_config(config=config, pdf=pdf, settings=settings)
    logger.info("Settings OK")
    logger.debug(
        "Settings: {settings}",
        settings=json.dumps(
            resolved.model_dump(mode="json")
            | {"output_folder": str(resolved.output_folder)},
            indent=2,
        ),
    )

    info = await asyncio.to_thread(open_pdf, resolved.pdf)
    logger.info(
        "Opened {name}: {pages}, {size:,} bytes, SHA-256 {sha256}",
        name=info.name,
        pages=f"{info.page_count} page" + ("" if info.page_count == 1 else "s"),
        sha256=info.sha256,
        size=info.bytes,
    )
    output_folder = resolved.output_folder
    output_folder.mkdir(exist_ok=True, parents=True)
    for leftover in remove_stale_temp_files(output_folder):
        logger.debug("Removed {path}, left by an interrupted write", path=leftover)

    await measure_facts(
        output_folder=output_folder, overwrite=resolved.overwrite, pdf=info
    )

    choice = resolved.model_choice
    logger.info(
        "Model: {model_id} from provider {provider}",
        model_id=choice.model_id,
        provider=choice.provider,
    )
    logger.info("Run finished")


def run(
    pdf: str | os.PathLike[str] | None = None,
    *,
    config: ConfigSource | None = None,
    **settings: object,
) -> None:
    """Run pydelity on a PDF; the sync version of `arun`.

    Parameters
    ----------
    pdf
        The PDF to process; it wins over a ``pdf`` in ``config``.
    config
        A JSON or YAML config file, a `pydelity.config.schemas.Config`, or a mapping
        of settings.
    **settings
        Settings by name, such as ``model="openai:gpt-6.2-astra"`` or
        ``advanced={"survey": {"effort": "medium"}}``. They win over ``config``.

    Raises
    ------
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read.
    PdfError
        If the PDF is empty, password-protected or cannot be opened.
    """

    run_coroutine(arun(pdf, config=config, **settings))

"""Combining settings from keywords, a config file and defaults, and checking them.

Keywords (or command-line options) override the config file, which overrides the
defaults. Relative paths in a config file are relative to the file's folder; relative
paths given as keywords or options are relative to the current directory. Every
problem is collected and reported in one `ConfigError`, before any work starts.
"""

# Standard Library
import json
import os

from collections.abc import Mapping
from pathlib import Path

# Third Party Library
import yaml

from pydantic import SecretStr, ValidationError

# Package Library
from pydelity.config.schemas import Config, ProviderEnv
from pydelity.errors import ConfigError, MissingApiKeyError
from pydelity.providers.profiles import (
    DEFAULT_MODEL,
    PROFILES,
    ProviderName,
    parse_model,
)

# Where the settings can come from, besides keywords: a JSON or YAML file, a `Config`,
# or a mapping of settings.
type ConfigSource = str | os.PathLike[str] | Config | Mapping[str, object]

# The environment variable that holds each provider's API key.
_API_KEY_VARIABLES: dict[ProviderName, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}

# The config file formats pydelity reads, by file extension.
_FILE_SUFFIXES = (".json", ".yaml", ".yml")

# How much of an invalid value an error message repeats.
_INPUT_SHOWN_CHARS = 60

# The top-level settings that hold paths.
_PATH_SETTINGS = ("output_dir", "pdf")


def _describe_input(value: object) -> str:
    """Show an invalid value briefly, for an error message.

    Parameters
    ----------
    value
        The value that failed validation.

    Returns
    -------
    str
        The value as JSON (its ``repr`` if it has no JSON form), cut to
        `_INPUT_SHOWN_CHARS` characters.
    """

    try:
        shown = json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        shown = repr(value)
    if len(shown) > _INPUT_SHOWN_CHARS:
        shown = shown[: _INPUT_SHOWN_CHARS - 3] + "..."
    return shown


def _expiry_problem(*, expiry_hours: object, model: object) -> str | None:
    """Check an upload expiry against the selected provider's allowed range.

    Parameters
    ----------
    expiry_hours
        The ``advanced.uploads.expiry_hours`` value, as given.
    model
        The ``model`` value, as given.

    Returns
    -------
    str | None
        Why the expiry is out of range, or ``None`` when it is in range or cannot be
        checked (no expiry, or an expiry or model that is invalid for other reasons).
    """

    if not isinstance(expiry_hours, int) or isinstance(expiry_hours, bool):
        return None
    if not isinstance(model, str):
        return None
    try:
        profile = PROFILES[parse_model(model).provider]
    except ValueError:
        return None

    low, high = profile.min_upload_expiry_hours, profile.max_upload_expiry_hours
    if low <= expiry_hours <= high:
        return None
    return (
        f"{expiry_hours} hours is outside the range {profile.name} allows, "
        f"{low} to {high} hours"
    )


def _format_problems(problems: list[tuple[str, str]]) -> str:
    """Write the problems as one error message, one setting per line.

    Parameters
    ----------
    problems
        Pairs of a setting's dotted path and what is wrong with it.

    Returns
    -------
    str
        The message.
    """

    lines = [f"- {path}: {problem}" for path, problem in problems]
    noun = "setting" if len(problems) == 1 else "settings"
    return f"{len(problems)} invalid {noun}:\n" + "\n".join(lines)


def _load_file(path: Path) -> dict[str, object]:
    """Read a JSON or YAML config file into a dictionary of settings.

    Relative paths among the file's settings are made relative to the file's folder.

    Parameters
    ----------
    path
        The config file.

    Returns
    -------
    dict[str, object]
        The settings in the file.

    Raises
    ------
    ConfigError
        If the file is missing, has an unsupported extension, cannot be parsed, or
        does not hold a mapping of settings.
    """

    if path.suffix.lower() not in _FILE_SUFFIXES:
        raise ConfigError(
            f"config file {path}: use a .json, .yaml or .yml file, "
            f"not {path.suffix or 'a file with no extension'}"
        )
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise ConfigError(f"config file {path}: no such file") from error
    except (OSError, UnicodeDecodeError) as error:
        raise ConfigError(f"config file {path}: cannot be read ({error})") from error

    data = _parse_file_text(path=path, text=text)
    folder = path.expanduser().absolute().parent
    for key in _PATH_SETTINGS:
        value = data.get(key)
        if isinstance(value, str) and value:
            data[key] = str(folder / Path(value).expanduser())
    return data


def _merge(base: Mapping[str, object], overrides: Mapping[str, object]) -> dict:
    """Merge settings, nested mappings included, with the overrides winning.

    Parameters
    ----------
    base
        The lower-precedence settings.
    overrides
        The higher-precedence settings.

    Returns
    -------
    dict
        A new dictionary; neither input is changed.
    """

    merged = dict(base)
    for key, value in overrides.items():
        current = merged.get(key)
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            merged[key] = _merge(current, value)
        else:
            merged[key] = value
    return merged


def _parse_file_text(*, path: Path, text: str) -> dict[str, object]:
    """Parse a config file's text as JSON or YAML, by its extension.

    Parameters
    ----------
    path
        The config file, for its extension and for error messages.
    text
        The file's contents.

    Returns
    -------
    dict[str, object]
        The settings in the file; an empty YAML file has none.

    Raises
    ------
    ConfigError
        If the text cannot be parsed or is not a mapping of settings.
    """

    try:
        if path.suffix.lower() == ".json":
            data = json.loads(text)
        else:
            data = yaml.safe_load(text)
    except json.JSONDecodeError as error:
        raise ConfigError(f"config file {path}: not valid JSON ({error})") from error
    except yaml.YAMLError as error:
        raise ConfigError(f"config file {path}: not valid YAML ({error})") from error

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(
            f"config file {path}: must hold settings by name, "
            f"not a {type(data).__name__}"
        )
    return data


def _problems(error: ValidationError) -> list[tuple[str, str]]:
    """List the settings a validation error names, with what is wrong with each.

    Parameters
    ----------
    error
        The error Pydantic raised while validating the settings.

    Returns
    -------
    list[tuple[str, str]]
        Pairs of a setting's dotted path and what is wrong with it.
    """

    problems = []
    for detail in error.errors(include_url=False):
        path = _setting_path(detail["loc"])
        kind = detail["type"]
        if kind == "missing" and path == "pdf":
            problem = "required: give the PDF as an argument or set pdf"
        elif kind == "missing":
            problem = "required"
        elif kind == "extra_forbidden":
            problem = "not a setting pydelity knows"
        elif kind == "value_error":
            problem = detail["msg"].removeprefix("Value error, ")
        else:
            problem = f"{detail['msg']} (got {_describe_input(detail['input'])})"
        problems.append((path or "(settings)", problem))
    return problems


def _raw_expiry_hours(data: Mapping[str, object]) -> object:
    """Find ``advanced.uploads.expiry_hours`` in settings that failed validation.

    Parameters
    ----------
    data
        The combined settings, as given.

    Returns
    -------
    object
        The value, or ``None`` when it is missing or its parents are not mappings.
    """

    advanced = data.get("advanced")
    if not isinstance(advanced, Mapping):
        return None
    uploads = advanced.get("uploads")
    if not isinstance(uploads, Mapping):
        return None
    return uploads.get("expiry_hours")


def _setting_path(location: tuple[int | str, ...]) -> str:
    """Write a validation error's location as a setting path.

    Parameters
    ----------
    location
        The location Pydantic reports, such as ``("languages", 1)``.

    Returns
    -------
    str
        The setting's path, such as ``languages[1]`` or
        ``advanced.survey.check_retries``.
    """

    path = ""
    for key in location:
        if key == "[key]":
            continue
        if isinstance(key, int):
            path += f"[{key}]"
        else:
            path += f".{key}" if path else key
    return path


def _source_settings(config: ConfigSource | None) -> dict[str, object]:
    """Turn the ``config`` argument into a dictionary of settings.

    Parameters
    ----------
    config
        A config file path, a `Config`, a mapping of settings, or ``None``.

    Returns
    -------
    dict[str, object]
        The settings it holds. A `Config` gives only the settings it was given, so
        its defaults do not override a keyword.
    """

    if config is None:
        return {}
    if isinstance(config, Config):
        return config.model_dump(exclude_unset=True)
    if isinstance(config, Mapping):
        return dict(config)
    return _load_file(Path(config))


def read_api_key(provider: ProviderName) -> SecretStr:
    """Read the selected provider's API key from the environment.

    No ``.env`` file is read. Call this only when a run is about to need the
    provider.

    Parameters
    ----------
    provider
        The provider whose key is needed.

    Returns
    -------
    SecretStr
        The key, kept out of logs and error messages.

    Raises
    ------
    MissingApiKeyError
        If the provider's environment variable is unset or empty.
    """

    environment = ProviderEnv()
    key = (
        environment.anthropic_api_key
        if provider == "anthropic"
        else environment.openai_api_key
    )
    if key is None or not key.get_secret_value().strip():
        variable = _API_KEY_VARIABLES[provider]
        raise MissingApiKeyError(
            f"{variable} is not set; pydelity needs it to use {provider} models"
        )
    return key


def resolve_config(
    *,
    config: ConfigSource | None = None,
    pdf: str | os.PathLike[str] | None = None,
    settings: Mapping[str, object] | None = None,
) -> Config:
    """Combine settings from keywords, a config source and defaults, and check them.

    Parameters
    ----------
    config
        A JSON or YAML config file, a `Config`, or a mapping of settings.
    pdf
        The PDF. Overrides a ``pdf`` in ``config``.
    settings
        Settings by name (``advanced`` as a mapping). They override ``config``.

    Returns
    -------
    Config
        The checked settings.

    Raises
    ------
    ConfigError
        Listing every invalid setting, or naming a config file that cannot be read.

    Examples
    --------
    >>> config = resolve_config(pdf="report.pdf", settings={"languages": ["en"]})
    >>> config.languages, config.model  # doctest: +SKIP
    (['en'], 'anthropic:claude-opus-5-5')
    """

    overrides = dict(settings or {})
    if pdf is not None:
        overrides["pdf"] = os.fspath(pdf)
    data = _merge(_source_settings(config), overrides)

    problems: list[tuple[str, str]] = []
    resolved: Config | None = None
    try:
        resolved = Config.model_validate(data)
    except ValidationError as error:
        problems = _problems(error)

    # The allowed expiry range depends on the provider, so Pydantic cannot check it.
    # Check it here against the model setting, using the raw values if validation
    # failed, unless Pydantic already reported a problem with the expiry.
    expiry_path = "advanced.uploads.expiry_hours"
    if resolved is not None:
        expiry = _expiry_problem(
            expiry_hours=resolved.advanced.uploads.expiry_hours, model=resolved.model
        )
    else:
        expiry = _expiry_problem(
            expiry_hours=_raw_expiry_hours(data),
            model=data.get("model", DEFAULT_MODEL),
        )
    if expiry is not None and expiry_path not in {path for path, _ in problems}:
        problems.append((expiry_path, expiry))

    if problems or resolved is None:
        raise ConfigError(_format_problems(problems))
    return resolved

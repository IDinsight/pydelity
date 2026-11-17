"""Fingerprints of a step's inputs, used to decide whether an output can be reused."""

# Standard Library
import hashlib
import json

from typing import Any


def canonical_json(value: Any) -> str:  # noqa: ANN401 - any JSON value is accepted
    """Return the canonical JSON text of a value.

    Keys are sorted and no whitespace is added, so equal values always give the same
    text. Only JSON types are accepted: dicts with string keys, lists, strings, numbers,
    booleans and ``None``.

    Parameters
    ----------
    value
        The value to serialize.

    Returns
    -------
    str
        The canonical JSON text.

    Raises
    ------
    TypeError
        If the value holds something JSON cannot represent.
    ValueError
        If the value holds ``NaN`` or an infinity.

    Examples
    --------
    >>> canonical_json({"b": [1, 2], "a": "é"})
    '{"a":"é","b":[1,2]}'
    """

    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def fingerprint(value: Any) -> str:  # noqa: ANN401 - any JSON value is accepted
    """Return the ``sha256:`` fingerprint of a value's canonical JSON.

    Parameters
    ----------
    value
        The inputs to fingerprint, as JSON types (see `canonical_json`).

    Returns
    -------
    str
        ``"sha256:"`` followed by the 64-character hex digest of the UTF-8 encoded
        canonical JSON.

    Examples
    --------
    >>> fingerprint({"a": 1}) == fingerprint({"a": 1})
    True
    >>> fingerprint({"a": 1})[:7]
    'sha256:'
    """

    digest = hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"

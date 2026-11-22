"""Comparing lines of text whatever their spacing, case or numbers."""

# Standard Library
import re
import unicodedata


def normalize_line(text: str) -> str:
    """Write a line in the form lines are compared in.

    Lines that differ only in invisible characters, spacing, case, Unicode form or
    the numbers in them, such as a running footer with its page number, become the
    same.

    Parameters
    ----------
    text
        The line as printed.

    Returns
    -------
    str
        Without invisible formatting characters (Unicode category Cf, such as a
        zero-width space), NFKC-normalized, case-folded, whitespace collapsed, each
        run of digits ``#``. A line with nothing visible becomes empty.

    Examples
    --------
    >>> normalize_line("Page  12 of 30"), normalize_line("Page 12\u200b")
    ('page # of #', 'page #')
    >>> normalize_line("\u200b")
    ''
    """

    visible = "".join(char for char in text if unicodedata.category(char) != "Cf")
    folded = unicodedata.normalize("NFKC", visible).casefold()
    return re.sub(r"\d+", "#", " ".join(folded.split()))

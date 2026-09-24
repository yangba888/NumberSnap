from __future__ import annotations

import re

from numbersnap.core.normalization import normalize_numeric_context

# The boundaries prevent digits inside ordinary identifiers from being treated as
# a table cell. Currency/sign and percentage stay part of the captured string.
_NUMBER = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"(?:[-]?[¥$€]?|[¥$€]?[-]?)"
    r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:[.,]\d+)*|[.,]\d+)"
    r"%?"
    r"(?![A-Za-z0-9_.,])"
)


def extract_numbers(text: str) -> list[str]:
    """Return numeric substrings without converting their representation."""

    normalized = normalize_numeric_context(text)
    return [match.group(0) for match in _NUMBER.finditer(normalized)]


def is_number(text: str) -> bool:
    normalized = normalize_numeric_context(text)
    match = _NUMBER.fullmatch(normalized)
    return match is not None and bool(normalized)

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

    return [value for value, _, _ in extract_number_spans(text)]


def extract_number_spans(text: str) -> list[tuple[str, int, int]]:
    """Return each numeric value and its character range in the OCR text."""

    raw_matches = list(_NUMBER.finditer(text))
    if len(raw_matches) > 1:
        return [
            (normalize_numeric_context(match.group(0)), match.start(), match.end())
            for match in raw_matches
        ]

    normalized = normalize_numeric_context(text)
    if _NUMBER.fullmatch(normalized):
        start = len(text) - len(text.lstrip())
        end = len(text.rstrip())
        return [(normalized, start, end)]
    if raw_matches:
        match = raw_matches[0]
        return [
            (
                normalize_numeric_context(match.group(0)),
                match.start(),
                match.end(),
            )
        ]

    start_offset = len(text) - len(text.lstrip())
    return [
        (match.group(0), start_offset + match.start(), start_offset + match.end())
        for match in _NUMBER.finditer(normalized)
    ]


def is_number(text: str) -> bool:
    normalized = normalize_numeric_context(text)
    match = _NUMBER.fullmatch(normalized)
    return match is not None and bool(normalized)

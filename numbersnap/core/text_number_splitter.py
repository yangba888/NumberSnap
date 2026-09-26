from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import median

from numbersnap.core.layout_detector import LayoutResult, detect_layout
from numbersnap.core.models import OCRToken
from numbersnap.core.normalization import normalize_numeric_context
from numbersnap.core.number_filter import is_number

_NUMBER_VALUE = r"-?(?=[0-9OoIl.,]*\d)[0-9OoIl]+(?:[.,][0-9OoIl]+)?"
_LEADING_NUMBER = re.compile(rf"^\s*(?P<number>{_NUMBER_VALUE})(?P<space>\s*)")
_TRAILING_NUMBER = re.compile(rf"(?P<number>{_NUMBER_VALUE})\s*$")
_LOW_CONFIDENCE = 0.65


@dataclass(frozen=True, slots=True)
class _ParsedRow:
    line: str
    leading: str
    middle: str
    trailing: str
    explicit_leading_separator: bool
    coordinate_leading_separator: bool


def split_text_and_numbers(tokens: list[OCRToken]) -> LayoutResult:
    """Restore rows and choose one consistent two- or three-column structure."""

    source = detect_layout(tokens, preserve_columns=False)
    parsed_rows = [_parse_row(row) for row in source.rows]
    three_columns = _use_three_columns(parsed_rows)
    cells: list[list[str]] = []
    uncertain_rows: set[int] = set()

    for row_index, (row, parsed) in enumerate(
        zip(source.rows, parsed_rows, strict=True)
    ):
        if three_columns:
            cells.append([parsed.leading, parsed.middle, parsed.trailing])
            if not parsed.leading or not parsed.trailing:
                uncertain_rows.add(row_index)
        else:
            name = parsed.line[: _trailing_start(parsed.line)].rstrip()
            cells.append([name, parsed.trailing])
            if not parsed.trailing or parsed.leading:
                uncertain_rows.add(row_index)

        if not parsed.middle or any(
            token.confidence < _LOW_CONFIDENCE for token in row
        ):
            uncertain_rows.add(row_index)
        if parsed.trailing and _ambiguous_trailing_name(parsed.line):
            uncertain_rows.add(row_index)

    return LayoutResult(
        cells=cells,
        rows=source.rows,
        column_centers=[],
        uncertain_rows=frozenset(uncertain_rows),
    )


def _parse_row(row: list[OCRToken]) -> _ParsedRow:
    line = _join_row(row).strip()
    trailing_match = _TRAILING_NUMBER.search(line)
    trailing = (
        normalize_numeric_context(trailing_match.group("number"))
        if trailing_match
        else ""
    )
    before_trailing = line[: trailing_match.start()].rstrip() if trailing_match else line
    leading_match = _LEADING_NUMBER.match(before_trailing)
    leading = (
        normalize_numeric_context(leading_match.group("number"))
        if leading_match
        else ""
    )
    middle = (
        before_trailing[leading_match.end() :].strip()
        if leading_match
        else before_trailing.strip()
    )
    ordered = sorted(row, key=lambda token: token.center_x)
    coordinate_separator = (
        len(ordered) > 1 and is_number(ordered[0].normalized_text.strip())
    )
    return _ParsedRow(
        line=line,
        leading=leading,
        middle=middle,
        trailing=trailing,
        explicit_leading_separator=bool(
            leading_match and leading_match.group("space")
        ),
        coordinate_leading_separator=coordinate_separator,
    )


def _use_three_columns(rows: list[_ParsedRow]) -> bool:
    candidates = [row for row in rows if row.leading and row.middle and row.trailing]
    if not candidates:
        return False
    explicit = any(
        row.explicit_leading_separator or row.coordinate_leading_separator
        for row in candidates
    )
    if len(rows) == 1:
        return explicit

    required = max(2, (len(rows) + 1) // 2)
    if len(candidates) < required:
        return False
    leading_widths = {len(row.leading.lstrip("-")) for row in candidates}
    compact_consistent_serials = len(leading_widths) == 1 and max(leading_widths) <= 3
    return explicit or compact_consistent_serials


def _trailing_start(line: str) -> int:
    match = _TRAILING_NUMBER.search(line)
    return match.start() if match else len(line)


def _ambiguous_trailing_name(line: str) -> bool:
    match = _TRAILING_NUMBER.search(line)
    if match is None or match.start() <= 0 or line[match.start() - 1].isspace():
        return False
    previous = line[match.start() - 1]
    return previous.isascii() and previous.isalnum()


def _join_row(row: list[OCRToken]) -> str:
    if not row:
        return ""
    ordered = sorted(row, key=lambda token: token.center_x)
    character_width = median(
        token.width / max(1, len(token.normalized_text.strip())) for token in ordered
    )
    parts = [ordered[0].normalized_text.strip()]
    for previous, current in zip(ordered, ordered[1:], strict=False):
        gap = max(0.0, current.left - previous.right)
        separator = " " if gap > character_width * 0.6 else ""
        parts.extend((separator, current.normalized_text.strip()))
    return "".join(parts)

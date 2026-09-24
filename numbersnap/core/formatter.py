from __future__ import annotations


def to_tsv(rows: list[list[str]]) -> str:
    """Format cells for spreadsheet paste without altering cell text."""

    return "\n".join("\t".join(_safe_cell(cell) for cell in row) for row in rows)


def _safe_cell(value: str) -> str:
    return value.replace("\t", " ").replace("\r", " ").replace("\n", " ")


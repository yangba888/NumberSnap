from __future__ import annotations

from html import escape

from PySide6.QtCore import QMimeData
from PySide6.QtGui import QGuiApplication


def copy_text(text: str) -> None:
    """Copy TSV plus an Excel/WPS-compatible left-aligned text table."""

    clipboard = QGuiApplication.clipboard()
    mime = QMimeData()
    mime.setText(text)
    mime.setHtml(tsv_to_html(text))
    clipboard.setMimeData(mime)


def tsv_to_html(text: str) -> str:
    rows = text.splitlines()
    html_rows: list[str] = []
    for row in rows:
        cells = row.split("\t")
        html_cells = "".join(
            "<td style=\"mso-number-format:'\\@';text-align:left;\">"
            f"{escape(cell)}"
            "</td>"
            for cell in cells
        )
        html_rows.append(f"<tr>{html_cells}</tr>")
    return (
        "<html><head><meta charset=\"utf-8\"></head>"
        "<body><table>"
        + "".join(html_rows)
        + "</table></body></html>"
    )


def clear_clipboard() -> None:
    QGuiApplication.clipboard().clear()

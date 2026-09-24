from __future__ import annotations

from PySide6.QtGui import QGuiApplication


def copy_text(text: str) -> None:
    """Copy TSV as plain Unicode text without HTML or RTF alternatives."""
    QGuiApplication.clipboard().setText(text)


def clear_clipboard() -> None:
    QGuiApplication.clipboard().clear()

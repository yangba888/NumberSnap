from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from numbersnap.core.clipboard import clear_clipboard, copy_text


def test_clipboard_only_exposes_plain_text() -> None:
    app = QApplication.instance() or QApplication([])
    copy_text("00123\t456\n7\t")
    mime = QGuiApplication.clipboard().mimeData()
    assert mime.text() == "00123\t456\n7\t"
    assert mime.hasFormat("text/plain")
    assert not mime.hasHtml()
    assert not mime.hasFormat("text/rtf")
    clear_clipboard()
    app.processEvents()


def test_multicolumn_tsv_preserves_empty_cell_for_spreadsheet_paste() -> None:
    app = QApplication.instance() or QApplication([])
    value = "123\t456\n\t567\n345\t678"
    copy_text(value)
    mime = QGuiApplication.clipboard().mimeData()
    assert mime.text() == value
    assert not mime.hasHtml()
    assert not mime.hasFormat("text/rtf")
    clear_clipboard()
    app.processEvents()

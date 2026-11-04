import ctypes
import os
import sys
from ctypes import wintypes

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QByteArray, QPoint, QRect, Qt
from PySide6.QtWidgets import QApplication

from numbersnap.config.settings import Settings
from numbersnap.ui.main_window import MainWindow


def test_main_window_has_pin_autostart_and_close_controls() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Settings())
    assert window.title_bar.pin_button.toolTip() == "窗口置顶"
    assert window.start_with_windows.text() == "开机自启"
    assert window.auto_columns.text() == "自动分列"
    assert window.auto_columns.isChecked()
    assert window.text_number_split.text() == "文数分列"
    assert window.text_number_split.isChecked()
    assert not window.preview.isReadOnly()
    assert window.toggle_hotkey_edit.keySequence().toString() == "Ctrl+Shift+Z"
    assert window.hotkey_save_button.text() == "保存"
    assert window.toggle_hotkey_save_button.text() == "保存"
    assert window.theme_combo.count() == 3
    assert window.close_button.text() == "退出"
    assert window.testAttribute(Qt.WA_TranslucentBackground)
    window.deleteLater()
    app.processEvents()


def test_right_option_column_is_vertically_aligned() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Settings())
    window.show()
    app.processEvents()
    assert window.auto_columns.geometry().x() == window.text_number_split.geometry().x()
    window.deleteLater()
    app.processEvents()


@pytest.mark.parametrize("theme", ["system", "light", "dark"])
def test_narrow_window_keeps_controls_inside_and_separate(theme) -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Settings(theme=theme))
    window.resize(360, 700)
    window.show()
    app.processEvents()
    assert window.width() == 360
    rows = [
        [window.hotkey_edit, window.hotkey_save_button],
        [window.toggle_hotkey_edit, window.toggle_hotkey_save_button],
        [window.capture_button, window.copy_button, window.clear_button, window.close_button],
        [window.title_bar.pin_button, window.title_bar.minimize_button,
         window.title_bar.maximize_button, window.title_bar.close_button],
    ]
    for row in rows:
        bounds = [QRect(widget.mapTo(window, QPoint()), widget.size()) for widget in row]
        assert all(window.rect().contains(rect) for rect in bounds)
        assert all(
            left.right() < right.left()
            for left, right in zip(bounds, bounds[1:], strict=False)
        )
    window.deleteLater()
    app.processEvents()


def test_auto_columns_is_available_only_in_numbers_only_mode(monkeypatch) -> None:
    monkeypatch.setattr(Settings, "save", lambda self: None)
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Settings())
    assert window.auto_columns.isEnabled()
    window.numbers_only.setChecked(False)
    assert not window.auto_columns.isEnabled()
    window.deleteLater()
    app.processEvents()


def test_manual_preview_edit_is_used_as_result(monkeypatch) -> None:
    monkeypatch.setattr(Settings, "save", lambda self: None)
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Settings())
    window.set_result("猪肋排\t8", frozenset({0}))
    window.preview.setPlainText("猪肋排长切\t8")
    assert window.result_text() == "猪肋排长切\t8"
    assert window.preview.extraSelections() == []
    window.deleteLater()
    app.processEvents()


def test_title_close_hides_and_bottom_close_requests_quit() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Settings(theme="light"))
    requested: list[bool] = []
    window.quit_requested.connect(lambda: requested.append(True))
    window.show()
    app.processEvents()
    window.close()
    app.processEvents()
    assert not window.isVisible()
    assert requested == []
    window.close_button.click()
    assert requested == [True]
    window.deleteLater()
    app.processEvents()


def test_title_bar_icons_follow_selected_theme(monkeypatch) -> None:
    monkeypatch.setattr(Settings, "save", lambda self: None)
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Settings(theme="light"))
    assert not window.title_bar.dark_mode
    window.theme_combo.setCurrentIndex(window.theme_combo.findData("dark"))
    assert window.title_bar.dark_mode
    window.deleteLater()
    app.processEvents()


def test_shortcut_change_is_emitted_only_when_saved() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Settings())
    changes: list[str] = []
    window.hotkey_changed.connect(changes.append)
    window.hotkey_edit.setKeySequence("Ctrl+Alt+7")
    assert changes == []
    window.hotkey_save_button.click()
    assert changes == ["Ctrl+Alt+7"]
    window.deleteLater()
    app.processEvents()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows native resize")
@pytest.mark.parametrize(
    ("x", "y", "hit"),
    [(0, 0, 13), (799, 0, 14), (0, 599, 16), (799, 599, 17),
     (400, 0, 12), (400, 599, 15), (0, 300, 10), (799, 300, 11)],
)
def test_native_resize_edges_and_corners(monkeypatch, x, y, hit):
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Settings())

    def get_rect(hwnd, pointer):
        rect = ctypes.cast(pointer, ctypes.POINTER(wintypes.RECT)).contents
        # Negative origin models a monitor to the left of the primary screen.
        rect.left, rect.top, rect.right, rect.bottom = -1000, -700, -200, -100
        return 1

    monkeypatch.setattr(ctypes.windll.user32, "GetWindowRect", get_rect)
    msg = wintypes.MSG()
    msg.message = 0x0084
    msg.lParam = ((y - 700) & 0xFFFF) << 16 | ((x - 1000) & 0xFFFF)
    assert window.nativeEvent(QByteArray(b"windows_generic_MSG"), ctypes.addressof(msg)) == (
        True, hit
    )
    window.deleteLater()
    app.processEvents()

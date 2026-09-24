import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from numbersnap.config.settings import Settings
from numbersnap.ui.main_window import MainWindow


def test_main_window_has_pin_autostart_and_close_controls() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Settings())
    assert window.title_bar.pin_button.toolTip() == "窗口置顶"
    assert window.start_with_windows.text() == "开机自启"
    assert window.toggle_hotkey_edit.keySequence().toString() == "Ctrl+Shift+Z"
    assert window.theme_combo.count() == 3
    assert window.close_button.text() == "关闭"
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

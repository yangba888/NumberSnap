import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
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
    assert window.close_button.text() == "关闭"
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

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
    assert window.close_button.text() == "关闭"
    window.deleteLater()
    app.processEvents()

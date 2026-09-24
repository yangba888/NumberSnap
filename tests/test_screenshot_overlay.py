import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRect, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from numbersnap.core.capture import DesktopSnapshot
from numbersnap.ui.screenshot_overlay import ScreenshotOverlay


def test_right_click_cancels_capture() -> None:
    app = QApplication.instance() or QApplication([])
    overlay = ScreenshotOverlay(DesktopSnapshot(QRect(0, 0, 40, 40), ()))
    cancelled: list[bool] = []
    overlay.cancelled.connect(lambda: cancelled.append(True))
    overlay.show()
    QTest.mouseClick(overlay, Qt.RightButton)
    assert cancelled == [True]
    assert not overlay.isVisible()
    overlay.deleteLater()
    app.processEvents()

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QSystemTrayIcon

from numbersnap.ui.notification import NotificationService


class FakeTray(QObject):
    messageClicked = Signal()

    def showMessage(self, title, message, icon, duration):
        self.icon = icon


def test_error_click_opens_window_but_success_click_does_not():
    tray = FakeTray()
    opened = []
    service = NotificationService(tray, lambda: opened.append(True))
    tray.messageClicked.emit()
    assert opened == []
    service.show("识别失败", error=True)
    assert tray.icon == QSystemTrayIcon.Critical
    tray.messageClicked.emit()
    assert opened == [True]
    service.show("识别成功")
    tray.messageClicked.emit()
    assert opened == [True]

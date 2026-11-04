from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QSystemTrayIcon


class NotificationService:
    def __init__(self, tray: QSystemTrayIcon, on_error_clicked: Callable[[], None]) -> None:
        self.tray = tray
        self._on_error_clicked = on_error_clicked
        self._last_message_is_error = False
        self.tray.messageClicked.connect(self._message_clicked)

    def _message_clicked(self) -> None:
        if self._last_message_is_error:
            self._on_error_clicked()

    def show(self, message: str, error: bool = False) -> None:
        self._last_message_is_error = error
        icon = QSystemTrayIcon.Critical if error else QSystemTrayIcon.Information
        self.tray.showMessage("NumberSnap", message, icon, 3000)


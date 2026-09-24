from __future__ import annotations

from PySide6.QtWidgets import QSystemTrayIcon


class NotificationService:
    def __init__(self, tray: QSystemTrayIcon) -> None:
        self.tray = tray

    def show(self, message: str, error: bool = False) -> None:
        icon = QSystemTrayIcon.Critical if error else QSystemTrayIcon.Information
        self.tray.showMessage("NumberSnap", message, icon, 3000)


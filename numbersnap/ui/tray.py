from __future__ import annotations

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


def create_app_icon(size: int = 64) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.scale(size / 64, size / 64)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#35B2C0"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 13, 13)
    painter.setPen(Qt.white)
    font = QFont("Segoe UI", 28, QFont.Bold)
    painter.setFont(font)
    painter.drawText(QRect(0, 0, 64, 64), Qt.AlignCenter, "N")
    painter.end()
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    capture_requested = Signal()
    settings_requested = Signal()
    show_requested = Signal()
    quit_requested = Signal()

    def __init__(self) -> None:
        super().__init__(create_app_icon())
        self.setToolTip("NumberSnap")
        menu = QMenu()
        heading = QAction("NumberSnap", menu)
        heading.setEnabled(False)
        capture = menu.addAction("截图识别")
        settings = menu.addAction("显示主窗口")
        menu.addSeparator()
        quit_action = menu.addAction("彻底退出")
        menu.insertAction(capture, heading)
        self.setContextMenu(menu)

        capture.triggered.connect(self.capture_requested)
        settings.triggered.connect(self.settings_requested)
        quit_action.triggered.connect(self.quit_requested)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_requested.emit()

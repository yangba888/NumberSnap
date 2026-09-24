from __future__ import annotations

import ctypes
import sys

from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from numbersnap.core.capture import DesktopSnapshot


class ScreenshotOverlay(QWidget):
    selected = Signal(QRect)
    cancelled = Signal()

    def __init__(self, snapshot: DesktopSnapshot) -> None:
        super().__init__(None)
        self.snapshot: DesktopSnapshot | None = snapshot
        self.origin: QPoint | None = None
        self.cursor: QPoint | None = None
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setCursor(Qt.CrossCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setGeometry(snapshot.geometry)

    def showEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().showEvent(event)
        self.activateWindow()
        self.setFocus(Qt.ActiveWindowFocusReason)
        QTimer.singleShot(0, self._force_foreground)

    def _force_foreground(self) -> None:
        self.raise_()
        self.activateWindow()
        if sys.platform == "win32":
            window_handle = int(self.winId())
            ctypes.windll.user32.BringWindowToTop(window_handle)
            ctypes.windll.user32.SetForegroundWindow(window_handle)
            ctypes.windll.user32.SetFocus(window_handle)

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 105))
        selection = self._selection()
        if not selection.isNull():
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(selection, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor("#36a3ff"), 2))
            painter.drawRect(selection.adjusted(0, 0, -1, -1))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.origin = event.position().toPoint()
            self.cursor = self.origin
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.origin is not None:
            self.cursor = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.LeftButton or self.origin is None or self.snapshot is None:
            return
        self.cursor = event.position().toPoint()
        selection = self._selection()
        if selection.width() >= 3 and selection.height() >= 3:
            global_rect = selection.translated(self.snapshot.geometry.topLeft())
            self.hide()
            self.selected.emit(global_rect)
        else:
            self.origin = None
            self.cursor = None
            self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.hide()
            self.cancelled.emit()
            self.deleteLater()
            return
        super().keyPressEvent(event)

    def release_snapshot(self) -> None:
        """Drop full-screen pixmaps as soon as the overlay is no longer visible."""
        self.snapshot = None

    def _selection(self) -> QRect:
        if self.origin is None or self.cursor is None:
            return QRect()
        return QRect(self.origin, self.cursor).normalized().intersected(self.rect())

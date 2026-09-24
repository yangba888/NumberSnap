from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget


def _title_icon(kind: str, color: str, restored: bool = False) -> QPixmap:
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(color), 1.35, Qt.SolidLine, Qt.SquareCap))
    if kind == "pin":
        painter.drawLine(6, 3, 12, 3)
        painter.drawLine(7, 4, 7, 10)
        painter.drawLine(11, 4, 11, 10)
        painter.drawLine(5, 11, 13, 11)
        painter.drawLine(9, 11, 9, 16)
    elif kind == "minimize":
        painter.drawLine(4, 12, 14, 12)
    elif kind == "maximize" and restored:
        painter.drawRect(6, 4, 8, 8)
        painter.drawRect(4, 6, 8, 8)
    elif kind == "maximize":
        painter.drawRect(4, 4, 10, 10)
    elif kind == "close":
        painter.drawLine(5, 5, 13, 13)
        painter.drawLine(13, 5, 5, 13)
    painter.end()
    return pixmap


class TitleBar(QWidget):
    pin_toggled = Signal(bool)
    close_requested = Signal()

    def __init__(self, pinned: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.dark_mode = True
        self.setObjectName("titleBar")
        self.setFixedHeight(38)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(0)
        self.title = QLabel("NumberSnap")
        self.title.setObjectName("titleBarText")
        layout.addWidget(self.title)
        layout.addStretch(1)

        self.pin_button = self._button("窗口置顶")
        self.pin_button.setCheckable(True)
        self.pin_button.setChecked(pinned)
        self.pin_button.toggled.connect(self._update_pin_icon)
        self.pin_button.toggled.connect(self.pin_toggled)
        layout.addWidget(self.pin_button)

        self.minimize_button = self._button("最小化")
        self.minimize_button.clicked.connect(lambda: self.window().showMinimized())
        layout.addWidget(self.minimize_button)

        self.maximize_button = self._button("最大化")
        self.maximize_button.clicked.connect(self.toggle_maximized)
        layout.addWidget(self.maximize_button)

        self.close_button = self._button("退出到后台")
        self.close_button.setObjectName("closeButton")
        self.close_button.clicked.connect(self.close_requested)
        layout.addWidget(self.close_button)
        self.set_dark_mode(True)

    def _button(self, tooltip: str) -> QToolButton:
        button = QToolButton(self)
        button.setToolTip(tooltip)
        button.setAutoRaise(True)
        button.setIconSize(QSize(18, 18))
        button.setFixedSize(46, 38)
        return button

    def set_dark_mode(self, dark: bool) -> None:
        self.dark_mode = dark
        foreground = "#f5f5f5" if dark else "#202020"
        background = "#202020" if dark else "#f3f3f3"
        hover = "#383838" if dark else "#e5e5e5"
        checked = "#3d5368" if dark else "#cfe6fa"
        self.setStyleSheet(
            f"""
            QWidget#titleBar {{ background: {background}; }}
            QLabel#titleBarText {{ color: {foreground}; font-weight: 600; }}
            QToolButton {{ border: 0; background: transparent; }}
            QToolButton:hover {{ background: {hover}; }}
            QToolButton:checked {{ background: {checked}; }}
            QToolButton#closeButton:hover {{ background: #c42b1c; }}
            """
        )
        self._update_icons()

    def _update_icons(self) -> None:
        color = "#f5f5f5" if self.dark_mode else "#202020"
        self.pin_button.setIcon(_title_icon("pin", color))
        self.minimize_button.setIcon(_title_icon("minimize", color))
        self.maximize_button.setIcon(
            _title_icon("maximize", color, self.window().isMaximized())
        )
        self.close_button.setIcon(_title_icon("close", color))

    def _update_pin_icon(self, pinned: bool) -> None:
        self._update_icons()
        self.pin_button.setToolTip("取消置顶" if pinned else "窗口置顶")

    def toggle_maximized(self) -> None:
        window = self.window()
        if window.isMaximized():
            window.showNormal()
        else:
            window.showMaximized()
        self.sync_maximized_state()

    def sync_maximized_state(self) -> None:
        maximized = self.window().isMaximized()
        self.maximize_button.setToolTip("还原" if maximized else "最大化")
        self._update_icons()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemMove()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.toggle_maximized()
        super().mouseDoubleClickEvent(event)

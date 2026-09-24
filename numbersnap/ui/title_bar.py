from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget


def _pin_pixmap(pinned: bool) -> QPixmap:
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#eeeeee"), 1.4, Qt.SolidLine, Qt.SquareCap))
    painter.drawLine(6, 3, 12, 3)
    painter.drawLine(7, 4, 7, 10)
    painter.drawLine(11, 4, 11, 10)
    painter.drawLine(5, 11, 13, 11)
    painter.drawLine(9, 11, 9, 16)
    painter.end()
    return pixmap


class TitleBar(QWidget):
    pin_toggled = Signal(bool)
    close_requested = Signal()

    def __init__(self, pinned: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(38)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(0)
        title = QLabel("NumberSnap")
        title.setObjectName("titleBarText")
        layout.addWidget(title)
        layout.addStretch(1)

        self.pin_button = self._button("窗口置顶")
        self.pin_button.setCheckable(True)
        self.pin_button.setChecked(pinned)
        self._update_pin_icon(pinned)
        self.pin_button.toggled.connect(self._update_pin_icon)
        self.pin_button.toggled.connect(self.pin_toggled)
        layout.addWidget(self.pin_button)

        minimize = self._button("最小化", "—")
        minimize.clicked.connect(lambda: self.window().showMinimized())
        layout.addWidget(minimize)

        self.maximize_button = self._button("最大化", "□")
        self.maximize_button.clicked.connect(self.toggle_maximized)
        layout.addWidget(self.maximize_button)

        close = self._button("关闭", "×")
        close.setObjectName("closeButton")
        close.clicked.connect(self.close_requested)
        layout.addWidget(close)

        self.setStyleSheet(
            """
            QWidget#titleBar { background: #202020; }
            QLabel#titleBarText { color: #eeeeee; font-weight: 600; }
            QToolButton {
                border: 0; color: #eeeeee; background: transparent;
                font-size: 18px; width: 44px; height: 38px;
            }
            QToolButton:hover { background: #383838; }
            QToolButton:checked { background: #3d5368; }
            QToolButton#closeButton:hover { background: #c42b1c; }
            """
        )

    def _button(self, tooltip: str, text: str = "") -> QToolButton:
        button = QToolButton(self)
        button.setToolTip(tooltip)
        button.setText(text)
        button.setAutoRaise(True)
        button.setFixedSize(44, 38)
        return button

    def _update_pin_icon(self, pinned: bool) -> None:
        self.pin_button.setIcon(_pin_pixmap(pinned))
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
        self.maximize_button.setText("❐" if maximized else "□")
        self.maximize_button.setToolTip("还原" if maximized else "最大化")

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

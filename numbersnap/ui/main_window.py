from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from numbersnap.config.settings import Settings
from numbersnap.ui.title_bar import TitleBar


class MainWindow(QMainWindow):
    capture_requested = Signal()
    copy_requested = Signal()
    clear_requested = Signal()
    hotkey_changed = Signal(str)
    autostart_changed = Signal(bool)
    quit_requested = Signal()

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.setWindowTitle("NumberSnap")
        self.setMinimumSize(520, 390)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self._topmost_applied = False

        root = QWidget(self)
        outer_layout = QVBoxLayout(root)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.title_bar = TitleBar(settings.always_on_top, root)
        self.title_bar.pin_toggled.connect(self._toggle_always_on_top)
        self.title_bar.close_requested.connect(self.close)
        outer_layout.addWidget(self.title_bar)

        content = QWidget(root)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        title = QLabel("NumberSnap")
        title.setStyleSheet("font-size: 24px; font-weight: 600;")
        layout.addWidget(title)

        shortcut_row = QHBoxLayout()
        shortcut_row.addWidget(QLabel("快捷键："))
        self.hotkey_edit = QKeySequenceEdit(QKeySequence(settings.hotkey))
        self.hotkey_edit.setMaximumSequenceLength(1)
        shortcut_row.addWidget(self.hotkey_edit)
        shortcut_row.addStretch(1)
        layout.addLayout(shortcut_row)

        self.numbers_only = QCheckBox("Numbers Only")
        self.auto_copy = QCheckBox("Auto Copy")
        self.preserve_layout = QCheckBox("Preserve Rows & Columns")
        self.start_with_windows = QCheckBox("开机自启")
        self.numbers_only.setChecked(settings.numbers_only)
        self.auto_copy.setChecked(settings.auto_copy)
        self.preserve_layout.setChecked(settings.preserve_layout)
        self.start_with_windows.setChecked(settings.start_with_windows)
        layout.addWidget(self.numbers_only)
        layout.addWidget(self.auto_copy)
        layout.addWidget(self.preserve_layout)
        layout.addWidget(self.start_with_windows)

        layout.addWidget(QLabel("识别结果预览"))
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setLayoutDirection(Qt.LeftToRight)
        self.preview.setPlaceholderText("截图识别后的 TSV 将显示在这里")
        layout.addWidget(self.preview, 1)

        buttons = QHBoxLayout()
        self.capture_button = QPushButton("截图识别")
        self.copy_button = QPushButton("重新复制")
        self.clear_button = QPushButton("清除")
        self.close_button = QPushButton("关闭")
        self.copy_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        buttons.addWidget(self.capture_button)
        buttons.addWidget(self.copy_button)
        buttons.addWidget(self.clear_button)
        buttons.addStretch(1)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

        outer_layout.addWidget(content, 1)

        self.setCentralWidget(root)
        self._connect_settings()

        self.capture_button.clicked.connect(self.capture_requested.emit)
        self.copy_button.clicked.connect(self.copy_requested.emit)
        self.clear_button.clicked.connect(self.clear_requested.emit)
        self.close_button.clicked.connect(self.close)
        self.hotkey_edit.editingFinished.connect(self._emit_hotkey)

    def _connect_settings(self) -> None:
        self.numbers_only.toggled.connect(self._save_settings)
        self.auto_copy.toggled.connect(self._save_settings)
        self.preserve_layout.toggled.connect(self._save_settings)
        self.start_with_windows.toggled.connect(self.autostart_changed)

    def _save_settings(self) -> None:
        self.settings.numbers_only = self.numbers_only.isChecked()
        self.settings.auto_copy = self.auto_copy.isChecked()
        self.settings.preserve_layout = self.preserve_layout.isChecked()
        self.settings.save()

    def _toggle_always_on_top(self, enabled: bool) -> None:
        self.settings.always_on_top = enabled
        self.settings.save()
        self._apply_native_topmost(enabled)

    def _apply_native_topmost(self, enabled: bool) -> None:
        if sys.platform != "win32":
            self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
            return
        user32 = ctypes.windll.user32
        user32.SetWindowPos.argtypes = (
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
        )
        insert_after = wintypes.HWND(-1 if enabled else -2)
        flags = 0x0001 | 0x0002 | 0x0010  # NOSIZE | NOMOVE | NOACTIVATE
        user32.SetWindowPos(wintypes.HWND(int(self.winId())), insert_after, 0, 0, 0, 0, flags)
        self._topmost_applied = True

    def set_busy(self, busy: bool) -> None:
        self.capture_button.setEnabled(not busy)
        self.capture_button.setText("识别中…" if busy else "截图识别")

    def set_result(self, text: str) -> None:
        self.preview.setPlainText(text)
        self.copy_button.setEnabled(bool(text))
        self.clear_button.setEnabled(bool(text))

    def set_hotkey(self, sequence: str) -> None:
        self.hotkey_edit.setKeySequence(QKeySequence(sequence))

    def set_autostart_checked(self, enabled: bool) -> None:
        self.start_with_windows.blockSignals(True)
        self.start_with_windows.setChecked(enabled)
        self.start_with_windows.blockSignals(False)

    def _emit_hotkey(self) -> None:
        sequence = self.hotkey_edit.keySequence().toString(QKeySequence.PortableText)
        self.hotkey_changed.emit(sequence)

    def showEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().showEvent(event)
        if not self._topmost_applied:
            self._apply_native_topmost(self.settings.always_on_top)

    def changeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().changeEvent(event)
        if event.type() == event.Type.WindowStateChange:
            self.title_bar.sync_maximized_state()

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        event.accept()
        self.quit_requested.emit()

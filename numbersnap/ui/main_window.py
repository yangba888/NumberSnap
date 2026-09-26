from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QKeySequence, QTextCursor, QTextFormat
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
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
    toggle_hotkey_changed = Signal(str)
    autostart_changed = Signal(bool)
    quit_requested = Signal()

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.setWindowTitle("NumberSnap")
        self.setMinimumSize(520, 440)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        # Keep the body opaque while allowing the custom title bar to use
        # per-pixel alpha. This is lighter and more reliable than a live blur.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
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
        content.setObjectName("content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        title = QLabel("NumberSnap")
        title.setStyleSheet("font-size: 24px; font-weight: 600;")
        layout.addWidget(title)

        shortcut_row = QHBoxLayout()
        shortcut_row.addWidget(QLabel("截图快捷键："))
        self.hotkey_edit = QKeySequenceEdit(QKeySequence(settings.hotkey))
        self.hotkey_edit.setMaximumSequenceLength(1)
        shortcut_row.addWidget(self.hotkey_edit)
        self.hotkey_save_button = QPushButton("保存")
        shortcut_row.addWidget(self.hotkey_save_button)
        shortcut_row.addStretch(1)
        layout.addLayout(shortcut_row)

        toggle_shortcut_row = QHBoxLayout()
        toggle_shortcut_row.addWidget(QLabel("显示/隐藏快捷键："))
        self.toggle_hotkey_edit = QKeySequenceEdit(QKeySequence(settings.toggle_hotkey))
        self.toggle_hotkey_edit.setMaximumSequenceLength(1)
        toggle_shortcut_row.addWidget(self.toggle_hotkey_edit)
        self.toggle_hotkey_save_button = QPushButton("保存")
        toggle_shortcut_row.addWidget(self.toggle_hotkey_save_button)
        toggle_shortcut_row.addStretch(1)
        layout.addLayout(toggle_shortcut_row)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("界面主题："))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("跟随系统", "system")
        self.theme_combo.addItem("浅色", "light")
        self.theme_combo.addItem("深色", "dark")
        theme_index = max(0, self.theme_combo.findData(settings.theme))
        self.theme_combo.setCurrentIndex(theme_index)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch(1)
        layout.addLayout(theme_row)

        self.numbers_only = QCheckBox("Numbers Only")
        self.auto_columns = QCheckBox("自动分列")
        self.auto_copy = QCheckBox("Auto Copy")
        self.text_number_split = QCheckBox("文数分列")
        self.preserve_layout = QCheckBox("Preserve Rows & Columns")
        self.start_with_windows = QCheckBox("开机自启")
        self.numbers_only.setChecked(settings.numbers_only)
        self.auto_columns.setChecked(settings.auto_columns)
        self.auto_copy.setChecked(settings.auto_copy)
        self.text_number_split.setChecked(settings.text_number_split)
        self.preserve_layout.setChecked(settings.preserve_layout)
        self.start_with_windows.setChecked(settings.start_with_windows)
        options_grid = QGridLayout()
        options_grid.setColumnStretch(2, 1)
        options_grid.addWidget(self.numbers_only, 0, 0)
        options_grid.addWidget(self.auto_columns, 0, 1)
        options_grid.addWidget(self.auto_copy, 1, 0)
        options_grid.addWidget(self.text_number_split, 1, 1)
        layout.addLayout(options_grid)
        layout.addWidget(self.preserve_layout)
        layout.addWidget(self.start_with_windows)

        layout.addWidget(QLabel("识别结果预览"))
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(False)
        self.preview.setLayoutDirection(Qt.LeftToRight)
        self.preview.setPlaceholderText("截图识别后的 TSV 将显示在这里")
        self.preview.setToolTip("黄色行表示低置信度或未找到末尾数量，可直接修改")
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
        self.close_button.clicked.connect(self.quit_requested.emit)
        self.preview.textChanged.connect(self._preview_edited)
        self.hotkey_save_button.clicked.connect(self._emit_hotkey)
        self.toggle_hotkey_save_button.clicked.connect(self._emit_toggle_hotkey)
        self.theme_combo.currentIndexChanged.connect(self._change_theme)
        QGuiApplication.styleHints().colorSchemeChanged.connect(self._system_theme_changed)
        self._apply_theme()

    def _connect_settings(self) -> None:
        self.numbers_only.toggled.connect(self._save_settings)
        self.numbers_only.toggled.connect(self.auto_columns.setEnabled)
        self.auto_columns.toggled.connect(self._save_settings)
        self.auto_copy.toggled.connect(self._save_settings)
        self.text_number_split.toggled.connect(self._save_settings)
        self.preserve_layout.toggled.connect(self._save_settings)
        self.start_with_windows.toggled.connect(self.autostart_changed)
        self.auto_columns.setEnabled(self.numbers_only.isChecked())

    def _save_settings(self) -> None:
        self.settings.numbers_only = self.numbers_only.isChecked()
        self.settings.auto_columns = self.auto_columns.isChecked()
        self.settings.auto_copy = self.auto_copy.isChecked()
        self.settings.text_number_split = self.text_number_split.isChecked()
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

    def set_result(
        self,
        text: str,
        uncertain_rows: frozenset[int] = frozenset(),
    ) -> None:
        self.preview.blockSignals(True)
        self.preview.setPlainText(text)
        self.preview.blockSignals(False)
        selections: list[QTextEdit.ExtraSelection] = []
        for row in uncertain_rows:
            block = self.preview.document().findBlockByNumber(row)
            if not block.isValid():
                continue
            selection = QTextEdit.ExtraSelection()
            selection.cursor = QTextCursor(block)
            selection.cursor.select(QTextCursor.LineUnderCursor)
            selection.format.setBackground(QColor(255, 193, 7, 70))
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selections.append(selection)
        self.preview.setExtraSelections(selections)
        self.copy_button.setEnabled(bool(text))
        self.clear_button.setEnabled(bool(text))

    def result_text(self) -> str:
        return self.preview.toPlainText()

    def _preview_edited(self) -> None:
        self.preview.setExtraSelections([])
        has_text = bool(self.preview.toPlainText())
        self.copy_button.setEnabled(has_text)
        self.clear_button.setEnabled(has_text)

    def set_hotkey(self, sequence: str) -> None:
        self.hotkey_edit.setKeySequence(QKeySequence(sequence))

    def set_toggle_hotkey(self, sequence: str) -> None:
        self.toggle_hotkey_edit.setKeySequence(QKeySequence(sequence))

    def set_autostart_checked(self, enabled: bool) -> None:
        self.start_with_windows.blockSignals(True)
        self.start_with_windows.setChecked(enabled)
        self.start_with_windows.blockSignals(False)

    def _emit_hotkey(self) -> None:
        sequence = self.hotkey_edit.keySequence().toString(QKeySequence.PortableText)
        self.hotkey_changed.emit(sequence)

    def _emit_toggle_hotkey(self) -> None:
        sequence = self.toggle_hotkey_edit.keySequence().toString(QKeySequence.PortableText)
        self.toggle_hotkey_changed.emit(sequence)

    def _change_theme(self) -> None:
        self.settings.theme = str(self.theme_combo.currentData())
        self.settings.save()
        self._apply_theme()

    def _system_theme_changed(self) -> None:
        if self.settings.theme == "system":
            self._apply_theme()

    def _apply_theme(self) -> None:
        system_dark = QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        dark = self.settings.theme == "dark" or (
            self.settings.theme == "system" and system_dark
        )
        foreground = "#f2f2f2" if dark else "#202020"
        background = "#202020" if dark else "#f7f7f7"
        field = "#2b2b2b" if dark else "#ffffff"
        border = "#505050" if dark else "#b8b8b8"
        hover = "#353535" if dark else "#ededed"
        self.setStyleSheet(
            f"""
            QMainWindow {{ background: transparent; }}
            QWidget#content {{ background: {background}; color: {foreground}; }}
            QLabel, QCheckBox {{ color: {foreground}; }}
            QPlainTextEdit, QKeySequenceEdit, QComboBox {{
                color: {foreground}; background: {field}; border: 1px solid {border};
                border-radius: 3px; padding: 4px;
            }}
            QPushButton {{
                color: {foreground}; background: {field}; border: 1px solid {border};
                border-radius: 3px; padding: 5px 12px;
            }}
            QPushButton:hover {{ background: {hover}; }}
            QPushButton:disabled {{ color: #888888; }}
            """
        )
        self.title_bar.set_dark_mode(dark)

    def showEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().showEvent(event)
        if not self._topmost_applied:
            self._apply_native_topmost(self.settings.always_on_top)

    def changeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().changeEvent(event)
        if event.type() == event.Type.WindowStateChange:
            self.title_bar.sync_maximized_state()

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        event.ignore()
        self.hide()

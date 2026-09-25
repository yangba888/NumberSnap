from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from numbersnap.config.settings import Settings
from numbersnap.core.autostart import is_autostart_enabled, reconcile_autostart, set_autostart
from numbersnap.core.capture import DesktopSnapshot, capture_virtual_desktop
from numbersnap.core.clipboard import clear_clipboard, copy_text
from numbersnap.core.hotkey import TOGGLE_WINDOW_HOTKEY_ID, GlobalHotkey
from numbersnap.core.layout_detector import LayoutResult
from numbersnap.ui.main_window import MainWindow
from numbersnap.ui.notification import NotificationService
from numbersnap.ui.screenshot_overlay import ScreenshotOverlay
from numbersnap.ui.tray import TrayIcon, create_app_icon

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from numbersnap.core.worker import OCRWorker


class ApplicationController(QObject):
    recognize_requested = Signal(QImage, bool, bool)

    def __init__(self, app: QApplication, settings: Settings) -> None:
        super().__init__()
        self.app = app
        self.settings = settings
        self._startup_warning: str | None = None
        try:
            autostart_enabled = reconcile_autostart(settings.start_with_windows)
        except OSError as exc:
            autostart_enabled = False
            self._startup_warning = f"无法读取开机自启状态：{exc}"
        self.window = MainWindow(settings)
        self.window.set_autostart_checked(autostart_enabled)
        self.tray = TrayIcon()
        self.notifications = NotificationService(self.tray)
        self.hotkey = GlobalHotkey(settings.hotkey)
        self.toggle_hotkey = GlobalHotkey(
            settings.toggle_hotkey,
            hotkey_id=TOGGLE_WINDOW_HOTKEY_ID,
        )
        self.overlay: ScreenshotOverlay | None = None
        self.snapshot: DesktopSnapshot | None = None
        self.last_text = ""
        self._ocr_busy = False
        self.worker_thread: QThread | None = None
        self.worker: OCRWorker | None = None

        self.window.capture_requested.connect(self.start_capture)
        self.window.copy_requested.connect(self.copy_again)
        self.window.clear_requested.connect(self.clear_result)
        self.window.hotkey_changed.connect(self.change_hotkey)
        self.window.toggle_hotkey_changed.connect(self.change_toggle_hotkey)
        self.window.autostart_changed.connect(self.change_autostart)
        self.window.quit_requested.connect(self.quit)
        self.tray.capture_requested.connect(self.start_capture)
        self.tray.settings_requested.connect(self.show_window)
        self.tray.show_requested.connect(self.show_window)
        self.tray.quit_requested.connect(self.quit)
        self.hotkey.activated.connect(self.start_capture)
        self.hotkey.failed.connect(lambda message: self.notifications.show(message, error=True))
        self.toggle_hotkey.activated.connect(self.toggle_window)
        self.toggle_hotkey.failed.connect(
            lambda message: self.notifications.show(message, error=True)
        )

        self.app.setWindowIcon(create_app_icon())
        self.app.aboutToQuit.connect(self._shutdown)

    def start(self, show_window: bool = True) -> None:
        self.tray.show()
        if show_window:
            self.window.show()
        self.hotkey.start()
        self.toggle_hotkey.start()
        if self.settings.load_warning:
            self.notifications.show(self.settings.load_warning, error=True)
        if self._startup_warning:
            self.notifications.show(self._startup_warning, error=True)

    @Slot()
    def show_window(self) -> None:
        try:
            self.window.set_autostart_checked(is_autostart_enabled())
        except OSError as exc:
            self.notifications.show(f"无法读取开机自启状态：{exc}", error=True)
        self.window.showNormal()
        self.window.raise_()
        self.window.activateWindow()

    @Slot()
    def toggle_window(self) -> None:
        if self.window.isVisible():
            self.window.hide()
        else:
            self.show_window()

    @Slot()
    def start_capture(self) -> None:
        if self.overlay is not None or self._ocr_busy:
            return
        try:
            self.snapshot = capture_virtual_desktop()
            self.overlay = ScreenshotOverlay(self.snapshot)
            self.overlay.selected.connect(self._on_selected)
            self.overlay.cancelled.connect(self._clear_overlay)
            self.overlay.show()
        except Exception as exc:
            LOGGER.exception("Unable to start screen capture")
            self.notifications.show(f"无法开始截图：{exc}", error=True)

    @Slot(object)
    def _on_selected(self, rect) -> None:  # type: ignore[no-untyped-def]
        if self.snapshot is None:
            self._clear_overlay()
            return
        image = self.snapshot.crop(rect)
        self._clear_overlay()
        self._ensure_worker()
        self._ocr_busy = True
        self.window.set_busy(True)
        self.recognize_requested.emit(
            image,
            self.settings.numbers_only,
            self.settings.preserve_layout,
        )

    @Slot()
    def _clear_overlay(self) -> None:
        if self.overlay is not None:
            self.overlay.release_snapshot()
            self.overlay.deleteLater()
        self.overlay = None
        self.snapshot = None

    @Slot(object, str, float)
    def _on_completed(self, result: LayoutResult, text: str, elapsed: float) -> None:
        self._ocr_busy = False
        self.window.set_busy(False)
        self.last_text = text
        self.window.set_result(text)
        if not text:
            self.notifications.show("未识别到数字", error=True)
            return
        if self.settings.auto_copy:
            copy_text(text)
        cell_count = sum(1 for row in result.cells for cell in row if cell)
        suffix = " · 已复制" if self.settings.auto_copy else ""
        message = (
            f"已识别 {cell_count} 个数字 · {result.row_count} 行 × "
            f"{result.column_count} 列{suffix}"
        )
        LOGGER.info("OCR completed in %.3fs: %s", elapsed, message)
        self.notifications.show(message)

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self._ocr_busy = False
        self.window.set_busy(False)
        self.notifications.show(f"识别失败：{message}", error=True)

    @Slot()
    def copy_again(self) -> None:
        if self.last_text:
            copy_text(self.last_text)
            self.notifications.show("识别结果已重新复制")

    @Slot()
    def clear_result(self) -> None:
        self.last_text = ""
        self.window.set_result("")
        clear_clipboard()
        self.notifications.show("识别结果和剪贴板已清除")

    @Slot(str)
    def change_hotkey(self, sequence: str) -> None:
        previous = self.settings.hotkey
        if not sequence:
            self.window.set_hotkey(previous)
            self.notifications.show("快捷键不能为空", error=True)
            return
        try:
            changed = self.hotkey.set_sequence(sequence)
        except ValueError as exc:
            self.window.set_hotkey(previous)
            self.notifications.show(str(exc), error=True)
            return
        if not changed:
            self.window.set_hotkey(previous)
            return
        self.settings.hotkey = sequence
        try:
            self.settings.save()
        except OSError as exc:
            self.settings.hotkey = previous
            self.hotkey.set_sequence(previous)
            self.window.set_hotkey(previous)
            self.notifications.show(f"快捷键保存失败：{exc}", error=True)
            return
        self.window.set_hotkey(sequence)
        self.notifications.show(f"快捷键已设置为 {sequence}")

    @Slot(str)
    def change_toggle_hotkey(self, sequence: str) -> None:
        previous = self.settings.toggle_hotkey
        if not sequence:
            self.window.set_toggle_hotkey(previous)
            self.notifications.show("显示/隐藏快捷键不能为空", error=True)
            return
        try:
            changed = self.toggle_hotkey.set_sequence(sequence)
        except ValueError as exc:
            self.window.set_toggle_hotkey(previous)
            self.notifications.show(str(exc), error=True)
            return
        if not changed:
            self.window.set_toggle_hotkey(previous)
            return
        self.settings.toggle_hotkey = sequence
        try:
            self.settings.save()
        except OSError as exc:
            self.settings.toggle_hotkey = previous
            self.toggle_hotkey.set_sequence(previous)
            self.window.set_toggle_hotkey(previous)
            self.notifications.show(f"显示/隐藏快捷键保存失败：{exc}", error=True)
            return
        self.window.set_toggle_hotkey(sequence)
        self.notifications.show(f"显示/隐藏快捷键已设置为 {sequence}")

    @Slot(bool)
    def change_autostart(self, enabled: bool) -> None:
        previous_preference = self.settings.start_with_windows
        try:
            previous_enabled = is_autostart_enabled()
        except OSError:
            previous_enabled = False
        try:
            set_autostart(enabled)
            if is_autostart_enabled() is not enabled:
                raise OSError("启动项状态与设置不一致")
            self.settings.start_with_windows = enabled
            self.settings.save()
        except OSError as exc:
            try:
                set_autostart(previous_enabled)
            except OSError:
                LOGGER.exception("Unable to restore the previous autostart setting")
            self.settings.start_with_windows = previous_preference
            self.window.set_autostart_checked(previous_enabled)
            self.notifications.show(f"开机自启设置失败：{exc}", error=True)
            return
        message = "已开启开机自启" if enabled else "已关闭开机自启"
        self.notifications.show(message)

    @Slot()
    def quit(self) -> None:
        self.app.quit()

    @Slot()
    def _shutdown(self) -> None:
        self.hotkey.stop()
        self.toggle_hotkey.stop()
        if self.worker_thread is None:
            return
        self.worker_thread.quit()
        if not self.worker_thread.wait(5000):
            LOGGER.warning("OCR worker did not stop within five seconds")
        self.worker = None
        self.worker_thread = None

    def _ensure_worker(self) -> None:
        if self.worker_thread is not None:
            return
        from numbersnap.core.worker import OCRWorker

        thread = QThread(self)
        thread.setObjectName("OCRWorkerThread")
        worker = OCRWorker()
        worker.moveToThread(thread)
        self.recognize_requested.connect(worker.process)
        worker.completed.connect(self._on_completed)
        worker.failed.connect(self._on_failed)
        thread.finished.connect(worker.deleteLater)
        self.worker_thread = thread
        self.worker = worker
        thread.start()

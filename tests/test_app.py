import os
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QRect
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from numbersnap import app as app_module
from numbersnap.config.settings import Settings


@pytest.fixture
def controller(monkeypatch):
    application = QApplication.instance() or QApplication([])
    monkeypatch.setattr(app_module, "reconcile_autostart", lambda enabled: False)
    instance = app_module.ApplicationController(application, Settings())
    instance.notifications.show = Mock()
    yield instance
    instance._clear_overlay()
    instance._shutdown()
    instance.window.deleteLater()
    instance.tray.deleteLater()
    instance.deleteLater()
    application.processEvents()


def test_capture_setup_failure_releases_snapshot(controller, monkeypatch):
    monkeypatch.setattr(app_module, "capture_virtual_desktop", lambda: object())
    monkeypatch.setattr(app_module, "ScreenshotOverlay", Mock(side_effect=RuntimeError("setup")))
    controller.start_capture()
    assert controller.snapshot is None
    assert controller.overlay is None
    controller.notifications.show.assert_called_once_with("无法开始截图：setup", error=True)


@pytest.mark.parametrize("failure", ["crop", "worker"])
def test_selection_failure_releases_capture_and_allows_retry(controller, monkeypatch, failure):
    snapshot = Mock()
    snapshot.crop.return_value = QImage(10, 10, QImage.Format_RGB888)
    overlay = Mock()
    controller.snapshot = snapshot
    controller.overlay = overlay
    if failure == "crop":
        snapshot.crop.side_effect = RuntimeError("crop")
    else:
        monkeypatch.setattr(controller, "_ensure_worker", Mock(side_effect=RuntimeError("worker")))
    controller._on_selected(QRect(0, 0, 10, 10))
    assert controller.snapshot is None and controller.overlay is None
    overlay.hide.assert_called_once()
    overlay.release_snapshot.assert_called_once()
    overlay.deleteLater.assert_called_once()
    assert not controller._ocr_busy
    assert controller.window.capture_button.isEnabled()
    controller.notifications.show.assert_called_once_with(f"识别失败：{failure}", error=True)


def test_busy_capture_does_not_queue_another_snapshot(controller, monkeypatch):
    capture = Mock()
    monkeypatch.setattr(app_module, "capture_virtual_desktop", capture)
    controller._ocr_busy = True
    controller.start_capture()
    capture.assert_not_called()

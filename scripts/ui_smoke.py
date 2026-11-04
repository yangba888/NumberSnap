"""Check real Windows hit testing and notification activation without capturing the screen."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from numbersnap.app import ApplicationController
from numbersnap.config.settings import Settings


def main() -> None:
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    with (
        patch("numbersnap.app.reconcile_autostart", return_value=False),
        patch("numbersnap.app.is_autostart_enabled", return_value=False),
    ):
        controller = ApplicationController(app, Settings())
        window = controller.window
        window.resize(800, 700)
        window.show()
        app.processEvents()
        user32 = ctypes.windll.user32
        user32.SendMessageW.argtypes = (
            wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
        )
        user32.SendMessageW.restype = ctypes.c_ssize_t
        hwnd = wintypes.HWND(int(window.winId()))
        rect = wintypes.RECT()
        assert user32.GetWindowRect(hwnd, ctypes.byref(rect))
        middle_x = (rect.left + rect.right) // 2
        middle_y = (rect.top + rect.bottom) // 2
        points = [
            (rect.left, rect.top, 13), (rect.right - 1, rect.top, 14),
            (rect.left, rect.bottom - 1, 16), (rect.right - 1, rect.bottom - 1, 17),
            (middle_x, rect.top, 12), (middle_x, rect.bottom - 1, 15),
            (rect.left, middle_y, 10), (rect.right - 1, middle_y, 11),
        ]
        for x, y, expected in points:
            position = (x & 0xFFFF) | ((y & 0xFFFF) << 16)
            assert user32.SendMessageW(hwnd, 0x0084, 0, position) == expected
        window.resize(1, 1)
        app.processEvents()
        assert window.width() >= window.minimumWidth()
        assert window.height() >= window.minimumHeight()
        window.showMaximized()
        app.processEvents()
        assert user32.GetWindowRect(hwnd, ctypes.byref(rect))
        position = (rect.left & 0xFFFF) | ((rect.top & 0xFFFF) << 16)
        assert user32.SendMessageW(hwnd, 0x0084, 0, position) not in range(10, 18)
        window.hide()
        with patch.object(controller.tray, "showMessage"):
            controller.notifications.show("UI smoke", error=True)
            controller.tray.messageClicked.emit()
        app.processEvents()
        assert window.isVisible() and not window.isMinimized()
        assert not window.isMaximized()
        assert window.close_button.text() == "退出"
        window.title_bar.close_button.click()
        assert not window.isVisible()
        controller._shutdown()
        window.deleteLater()
        app.processEvents()
    print("UI smoke passed: 8 resize directions, minimum size, maximized state, error activation.")


if __name__ == "__main__":
    main()

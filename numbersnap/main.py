from __future__ import annotations

import logging
import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from numbersnap.app import ApplicationController
from numbersnap.config.settings import Settings
from numbersnap.core.autostart import cleanup_autostart
from numbersnap.core.single_instance import SingleInstanceGuard


def configure_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("NumberSnap")
    app.setApplicationVersion("0.1.6")
    app.setQuitOnLastWindowClosed(False)

    if "--uninstall-cleanup" in sys.argv:
        try:
            cleanup_autostart()
            if "--remove-user-data" in sys.argv:
                Settings.remove_user_data()
            return 0
        except OSError as exc:
            QMessageBox.critical(None, "NumberSnap", f"卸载清理失败：{exc}")
            return 1

    instance_guard = SingleInstanceGuard()
    if not instance_guard.acquire():
        return 0
    settings = Settings.load()
    configure_logging(settings.debug)

    if "--ocr-smoke-test" in sys.argv:
        from numbersnap.smoke import run_ocr_smoke_test

        return run_ocr_smoke_test()

    try:
        controller = ApplicationController(app, settings)
        instance_guard.activation_requested.connect(controller.show_window)
        controller.start(show_window=should_show_window(sys.argv))
        if "--smoke-test" in sys.argv or os.environ.get("NUMBERSNAP_SMOKE_TEST") == "1":
            QTimer.singleShot(500, app.quit)
        return app.exec()
    finally:
        instance_guard.release()


def should_show_window(arguments: list[str]) -> bool:
    return "--startup" not in arguments


if __name__ == "__main__":
    raise SystemExit(main())

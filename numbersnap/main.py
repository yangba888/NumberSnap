from __future__ import annotations

import logging
import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from numbersnap.app import ApplicationController
from numbersnap.config.settings import Settings
from numbersnap.core.single_instance import SingleInstanceGuard


def configure_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    instance_guard = SingleInstanceGuard()
    if not instance_guard.acquire():
        return 0
    settings = Settings.load()
    configure_logging(settings.debug)

    app = QApplication(sys.argv)
    app.setApplicationName("NumberSnap")
    app.setApplicationVersion("0.1.4")
    app.setQuitOnLastWindowClosed(True)

    if "--ocr-smoke-test" in sys.argv:
        from numbersnap.smoke import run_ocr_smoke_test

        return run_ocr_smoke_test()

    try:
        controller = ApplicationController(app, settings)
        controller.start(show_window="--startup" not in sys.argv)
        if "--smoke-test" in sys.argv or os.environ.get("NUMBERSNAP_SMOKE_TEST") == "1":
            QTimer.singleShot(500, app.quit)
        return app.exec()
    finally:
        instance_guard.release()


if __name__ == "__main__":
    raise SystemExit(main())

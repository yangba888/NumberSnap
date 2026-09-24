"""In-memory OCR smoke test; no image is written to disk."""

from __future__ import annotations

import time

from PySide6.QtWidgets import QApplication

from numbersnap.smoke import run_ocr_smoke_test


def main() -> int:
    app = QApplication.instance() or QApplication([])
    started = time.perf_counter()
    result = run_ocr_smoke_test()
    print(f"OCR smoke: {time.perf_counter() - started:.3f}s")
    app.quit()
    return result


if __name__ == "__main__":
    raise SystemExit(main())

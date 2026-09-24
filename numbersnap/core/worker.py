from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage

from numbersnap.core.formatter import to_tsv
from numbersnap.core.layout_detector import LayoutResult, detect_layout
from numbersnap.core.ocr_engine import OCREngine

LOGGER = logging.getLogger(__name__)


class OCRWorker(QObject):
    completed = Signal(object, str, float)
    failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.engine = OCREngine()

    @Slot(QImage, bool, bool)
    def process(self, image: QImage, numbers_only: bool, preserve_layout: bool) -> None:
        import time

        started = time.perf_counter()
        try:
            tokens = self.engine.recognize(image, numbers_only=numbers_only)
            result: LayoutResult = detect_layout(tokens, preserve_columns=preserve_layout)
            text = to_tsv(result.cells)
            self.completed.emit(result, text, time.perf_counter() - started)
        except Exception as exc:  # Worker failures must return control to the UI.
            LOGGER.exception("OCR processing failed")
            self.failed.emit(str(exc))


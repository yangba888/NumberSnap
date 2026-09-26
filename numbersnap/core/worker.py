from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage

from numbersnap.core.formatter import to_tsv
from numbersnap.core.layout_detector import detect_layout
from numbersnap.core.ocr_engine import OCREngine
from numbersnap.core.text_number_splitter import split_text_and_numbers

LOGGER = logging.getLogger(__name__)


class OCRWorker(QObject):
    completed = Signal(object, str, float)
    failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.engine = OCREngine()

    @Slot(QImage, bool, bool, bool, bool)
    def process(
        self,
        image: QImage,
        numbers_only: bool,
        preserve_layout: bool,
        auto_columns: bool,
        text_number_split: bool,
    ) -> None:
        import time

        started = time.perf_counter()
        try:
            tokens = self.engine.recognize(image, numbers_only=numbers_only)
            # The OCR array is already released by the engine. Drop the selected
            # QImage before layout processing so large captures do not inflate peak memory.
            del image
            if text_number_split and not numbers_only:
                result = split_text_and_numbers(tokens)
            else:
                result = detect_layout(
                    tokens,
                    preserve_columns=preserve_layout,
                    auto_columns=auto_columns if numbers_only else True,
                )
            text = to_tsv(result.cells)
            self.completed.emit(result, text, time.perf_counter() - started)
        except Exception as exc:  # Worker failures must return control to the UI.
            LOGGER.exception("OCR processing failed")
            self.failed.emit(str(exc))

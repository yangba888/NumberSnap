from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter

from numbersnap.core.formatter import to_tsv
from numbersnap.core.layout_detector import detect_layout
from numbersnap.core.ocr_engine import OCREngine


def run_ocr_smoke_test() -> int:
    """Exercise the packaged OCR stack entirely in memory."""

    image = QImage(900, 240, QImage.Format_RGB888)
    image.fill(QColor(Qt.white))
    painter = QPainter(image)
    painter.setPen(QColor(Qt.black))
    painter.setFont(QFont("Arial", 42))
    for row, values in enumerate((("123", "456", "789"), ("234", "567", "890"))):
        for column, value in enumerate(values):
            painter.drawText(35 + column * 280, 75 + row * 105, value)
    painter.end()

    tokens = OCREngine().recognize(image)
    actual = to_tsv(detect_layout(tokens).cells)
    expected = "123\t456\t789\n234\t567\t890"
    return 0 if actual == expected else 2

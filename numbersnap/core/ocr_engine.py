from __future__ import annotations

import logging
import os
from collections.abc import Iterable
from typing import Any

from PySide6.QtGui import QImage

from numbersnap.core.models import BoundingBox, OCRToken
from numbersnap.core.normalization import normalize_numeric_context
from numbersnap.core.number_filter import extract_number_spans

LOGGER = logging.getLogger(__name__)


class OCREngine:
    """Lazy RapidOCR adapter that normalizes API differences across releases."""

    def __init__(self, minimum_confidence: float = 0.35) -> None:
        self.minimum_confidence = minimum_confidence
        self._engine: Any | None = None

    def recognize(self, image: QImage, numbers_only: bool = True) -> list[OCRToken]:
        if self._engine is None:
            # NumPy's bundled OpenBLAS otherwise creates one worker per logical CPU
            # even though OCR only uses it for lightweight array operations.
            os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
            from rapidocr import RapidOCR

            LOGGER.info("Initializing local RapidOCR engine")
            self._engine = RapidOCR(
                params={
                    "Global.use_cls": False,
                    "Det.limit_type": "max",
                    "Det.limit_side_len": 1280,
                    "Global.log_level": "warning",
                    "EngineConfig.onnxruntime.intra_op_num_threads": 4,
                    "EngineConfig.onnxruntime.inter_op_num_threads": 1,
                }
            )

        array = _qimage_to_rgb_array(image)
        output = self._engine(array)
        if LOGGER.isEnabledFor(logging.DEBUG):
            records: Iterable[tuple[BoundingBox, str, float]] = list(_iter_output(output))
            LOGGER.debug("OCR raw result: %s", records)
        else:
            records = _iter_output(output)

        tokens: list[OCRToken] = []
        for box, raw_text, confidence in records:
            if confidence < self.minimum_confidence:
                continue
            if numbers_only:
                matches = extract_number_spans(raw_text)
                if not matches:
                    continue
                text_length = max(1, len(raw_text))
                for value, start, end in matches:
                    value_box = _horizontal_box_slice(
                        box,
                        start / text_length,
                        end / text_length,
                    )
                    tokens.append(OCRToken(raw_text, value, confidence, value_box))
            else:
                normalized = normalize_numeric_context(raw_text)
                if normalized:
                    tokens.append(OCRToken(raw_text, normalized, confidence, box))

        del records, output, array
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug(
                "Normalization result: %s",
                [
                    {
                        "raw": token.raw_text,
                        "normalized": token.normalized_text,
                        "confidence": token.confidence,
                        "box": token.box,
                        "center_x": token.center_x,
                        "center_y": token.center_y,
                    }
                    for token in tokens
                ],
            )
        return tokens


def _qimage_to_rgb_array(image: QImage) -> Any:
    import numpy as np

    converted = image.convertToFormat(QImage.Format_RGB888)
    raw = np.frombuffer(converted.bits(), dtype=np.uint8, count=converted.sizeInBytes())
    rows = raw.reshape(converted.height(), converted.bytesPerLine())
    rgb = rows[:, : converted.width() * 3].reshape(converted.height(), converted.width(), 3)
    return rgb.copy()


def _as_box(value: Any) -> BoundingBox:
    points = tuple((float(point[0]), float(point[1])) for point in value)
    if len(points) != 4:
        raise ValueError(f"Expected four points in OCR bounding box, got {len(points)}")
    return points  # type: ignore[return-value]


def _horizontal_box_slice(
    box: BoundingBox,
    start_ratio: float,
    end_ratio: float,
) -> BoundingBox:
    """Approximate per-number boxes when OCR joins several values in one line."""

    top_left, top_right, bottom_right, bottom_left = box

    def interpolate(
        start: tuple[float, float],
        end: tuple[float, float],
        ratio: float,
    ) -> tuple[float, float]:
        return (
            start[0] + (end[0] - start[0]) * ratio,
            start[1] + (end[1] - start[1]) * ratio,
        )

    return (
        interpolate(top_left, top_right, start_ratio),
        interpolate(top_left, top_right, end_ratio),
        interpolate(bottom_left, bottom_right, end_ratio),
        interpolate(bottom_left, bottom_right, start_ratio),
    )


def _iter_output(output: Any) -> Iterable[tuple[BoundingBox, str, float]]:
    # RapidOCR 3.x returns a RapidOCROutput with parallel boxes/txts/scores.
    if hasattr(output, "boxes") and hasattr(output, "txts"):
        boxes = output.boxes if output.boxes is not None else []
        texts = output.txts if output.txts is not None else []
        scores = output.scores if output.scores is not None else []
        for box, text, score in zip(boxes, texts, scores, strict=False):
            yield _as_box(box), str(text), float(score)
        return

    # RapidOCR 1.x/2.x commonly returns (results, elapsed_times).
    records = output
    if isinstance(output, tuple) and len(output) == 2:
        records = output[0]
    if records is None:
        return
    for record in records:
        if len(record) >= 3:
            yield _as_box(record[0]), str(record[1]), float(record[2])

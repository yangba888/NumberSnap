from __future__ import annotations

import sys
from types import ModuleType

from PySide6.QtGui import QImage

from numbersnap.core import ocr_engine


def test_engine_initialization_limits_native_thread_pools(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeRapidOCR:
        def __init__(self, params) -> None:  # type: ignore[no-untyped-def]
            captured.update(params)

        def __call__(self, image):  # type: ignore[no-untyped-def]
            return None

    fake_module = ModuleType("rapidocr")
    fake_module.RapidOCR = FakeRapidOCR  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "rapidocr", fake_module)
    monkeypatch.delenv("OPENBLAS_NUM_THREADS", raising=False)
    monkeypatch.setattr(ocr_engine, "_qimage_to_rgb_array", lambda image: object())

    engine = ocr_engine.OCREngine()
    assert engine.recognize(QImage()) == []
    assert captured["EngineConfig.onnxruntime.intra_op_num_threads"] == 4
    assert captured["EngineConfig.onnxruntime.inter_op_num_threads"] == 1


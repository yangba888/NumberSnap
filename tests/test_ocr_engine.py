from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

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


def test_joined_numbers_receive_separate_bounding_boxes(monkeypatch) -> None:
    output = SimpleNamespace(
        boxes=[[(0, 0), (140, 0), (140, 20), (0, 20)]],
        txts=["123 456"],
        scores=[0.99],
    )
    engine = ocr_engine.OCREngine()
    engine._engine = lambda image: output
    monkeypatch.setattr(ocr_engine, "_qimage_to_rgb_array", lambda image: object())

    tokens = engine.recognize(QImage())

    assert [token.normalized_text for token in tokens] == ["123", "456"]
    assert tokens[0].right < tokens[1].left

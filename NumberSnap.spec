# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

rapidocr_hidden = ["rapidocr.inference_engine.onnxruntime"]
rapidocr_data = collect_data_files("rapidocr")
ort_binaries = collect_dynamic_libs("onnxruntime")

a = Analysis(
    ["numbersnap/main.py"],
    pathex=[],
    binaries=ort_binaries,
    datas=rapidocr_data,
    hiddenimports=rapidocr_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "rapidocr.inference_engine.mnn",
        "rapidocr.inference_engine.openvino",
        "rapidocr.inference_engine.paddle",
        "rapidocr.inference_engine.pytorch",
        "rapidocr.inference_engine.tensorrt",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NumberSnap",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="assets/numbersnap-exe-icon.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="NumberSnap",
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "未找到 .venv。请先按 README 创建虚拟环境并安装 requirements-dev.txt。"
}

& ".venv\Scripts\python.exe" -m pytest
if ($LASTEXITCODE -ne 0) { throw "Tests failed." }

& ".venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm NumberSnap.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

Write-Host "Build complete: dist\NumberSnap\NumberSnap.exe"


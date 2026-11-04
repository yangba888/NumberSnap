$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$Python = ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = ".tools\python312\python.exe"
}
if (-not (Test-Path $Python)) {
    throw "未找到 Python 环境。请先按 README 创建虚拟环境并安装 requirements-dev.txt。"
}

& $Python -m pytest -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "Tests failed." }

& $Python -m PyInstaller --clean --noconfirm NumberSnap.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

Write-Host "Build complete: dist\NumberSnap\NumberSnap.exe"


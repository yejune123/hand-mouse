param([string]$Python = '')

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if ($Python) {
    $pythonCommand = $Python
    $pythonPrefix = @()
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCommand = 'py'
    $pythonPrefix = @('-3.12')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCommand = 'python'
    $pythonPrefix = @()
} else {
    throw 'Python 3.12 is required to build HandMouse.'
}
& $pythonCommand @pythonPrefix -c 'import sys; assert sys.version_info[:2] == (3, 12), "Python 3.12 is required"'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required to build HandMouse.' }

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    & $pythonCommand @pythonPrefix -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Unable to create the build environment.' }
}
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $venvPython -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Unable to install build dependencies.' }

& $venvPython -m PyInstaller --noconfirm --clean --onedir --windowed --name HandMouse --distpath dist --workpath build --collect-all mediapipe --exclude-module pandas --exclude-module openpyxl --exclude-module lxml --add-data 'assets\hand_landmarker.task;assets' app.py
if ($LASTEXITCODE -ne 0) { throw 'Unable to build the Windows application.' }
Write-Host 'Built: dist\HandMouse\HandMouse.exe'

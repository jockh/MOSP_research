$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$BackendDir = Join-Path $PSScriptRoot "backend"
$VenvDir = Join-Path $BackendDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts/python.exe"
if (-not (Test-Path -LiteralPath $VenvPython)) { python -m venv $VenvDir }
& $VenvPython -m pip install -r (Join-Path $BackendDir "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Backend dependency installation failed" }
& $VenvPython -m pip install --no-deps -e $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw "Canonical package installation failed" }
& $VenvPython -m uvicorn main:app --app-dir $BackendDir --reload --port 8000

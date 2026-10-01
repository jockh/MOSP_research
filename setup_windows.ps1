param(
    [string]$PythonExecutable = '',
    [switch]$IncludeWeb
)
$ErrorActionPreference = 'Stop'
$ProjectRootPath = $PSScriptRoot
$VenvDirectory = Join-Path $ProjectRootPath '.venv'
$VenvPythonPath = Join-Path $VenvDirectory 'Scripts/python.exe'
if (-not (Test-Path -LiteralPath $VenvPythonPath)) {
    if ($PythonExecutable) {
        & $PythonExecutable -m venv $VenvDirectory
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.13 -m venv $VenvDirectory
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv $VenvDirectory
    } else {
        $UserPythonPath = Join-Path $env:LOCALAPPDATA 'Programs/Python/Python313/python.exe'
        if (-not (Test-Path -LiteralPath $UserPythonPath)) {
            throw 'Python 3.13 was not found. Pass -PythonExecutable with your Python executable path.'
        }
        & $UserPythonPath -m venv $VenvDirectory
    }
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed' }
}
& $VenvPythonPath -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed' }
$InstallTarget = if ($IncludeWeb) { "$ProjectRootPath[web,test]" } else { $ProjectRootPath }
& $VenvPythonPath -m pip install -e $InstallTarget
if ($LASTEXITCODE -ne 0) { throw 'Canonical editable installation failed' }
Push-Location $ProjectRootPath
try {
    & $VenvPythonPath -X utf8 -B -m validation.check_installation
    if ($LASTEXITCODE -ne 0) { throw 'Canonical package verification failed' }
} finally { Pop-Location }
Write-Output "Installation verified. Run research commands with: $VenvPythonPath"

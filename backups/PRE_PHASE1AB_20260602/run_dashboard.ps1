Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$dashboardRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $dashboardRoot ".venv"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$requirementsPath = Join-Path $dashboardRoot "requirements.txt"

if (-not (Test-Path -LiteralPath $pythonExe)) {
    Write-Host "Creating dashboard virtual environment."
    python -m venv $venvPath
}

Write-Host "Installing dashboard requirements."
& $pythonExe -m pip install -r $requirementsPath

Write-Host "Starting JeffLocal dashboard on 0.0.0.0:8765"
Push-Location $dashboardRoot
try {
    & $pythonExe -m uvicorn app.main:app --host 0.0.0.0 --port 8765
}
finally {
    Pop-Location
}

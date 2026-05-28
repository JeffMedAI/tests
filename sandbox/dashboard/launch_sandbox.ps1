# launch_sandbox.ps1
# Launches the sandbox dashboard for Churchtown Medical Centre
# Port: 5000  |  Environment: sandbox  |  DB: isolated sandbox database
#
# Usage:
#   .\launch_sandbox.ps1
#
# To deploy for a new practice, copy this entire sandbox/dashboard/ folder,
# update .env.sandbox with the practice details, and run this script there.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$dashboardRoot    = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath         = Join-Path $dashboardRoot ".venv"
$pythonExe        = Join-Path $venvPath "Scripts\python.exe"
$requirementsPath = Join-Path $dashboardRoot "requirements.txt"
$startupScript    = Join-Path $dashboardRoot "sandbox_startup.py"

# ── Virtual environment ────────────────────────────────────────────────
if (-not (Test-Path -LiteralPath $pythonExe)) {
    Write-Host "Creating virtual environment..."
    python -m venv $venvPath
}

Write-Host "Installing requirements..."
& $pythonExe -m pip install -r $requirementsPath --quiet

# ── Launch via sandbox_startup.py ──────────────────────────────────────
# sandbox_startup.py loads .env.sandbox, injects template globals, then
# starts uvicorn — no direct modification of main.py or db.py needed.
Write-Host ""
Write-Host "═══════════════════════════════════════════════════"
Write-Host "  JeffLocal Sandbox Dashboard"
Write-Host "  Config: .env.sandbox"
Write-Host "  Press Ctrl+C to stop."
Write-Host "═══════════════════════════════════════════════════"
Write-Host ""

Push-Location $dashboardRoot
try {
    & $pythonExe $startupScript
} finally {
    Pop-Location
}

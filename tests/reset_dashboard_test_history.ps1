param(
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$basePath = "C:\JeffLocal"
$dashboardDb = Join-Path $basePath "dashboard\data\dashboard.sqlite"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = Join-Path $basePath "backup\dashboard_reset_$timestamp"
$backupDb = Join-Path $backupRoot "dashboard.sqlite"

if (-not $Force) {
    $prompt = Read-Host "This will archive and reset the local dashboard SQLite database only. Type YES to continue"
    if ($prompt -ne "YES") {
        Write-Host "Reset cancelled."
        exit 2
    }
}

$pythonFile = Join-Path $env:TEMP ("jefflocal_reset_dashboard_" + [guid]::NewGuid().ToString("N") + ".py")
$pythonCode = @"
import sqlite3
import sys
from pathlib import Path

BASE = Path(r"C:\JeffLocal\dashboard")
sys.path.insert(0, str(BASE))

from app.db import connect, init_db

source = Path(r"C:\JeffLocal\dashboard\data\dashboard.sqlite")
backup = Path(r"$($backupDb.Replace('\', '\\'))")
backup.parent.mkdir(parents=True, exist_ok=True)

if source.exists():
    with sqlite3.connect(source) as src, sqlite3.connect(backup) as dst:
        src.backup(dst)
    print(f"Archived dashboard database to {backup}")
else:
    print("No existing dashboard database found to archive.")

with connect() as conn:
    init_db(conn)
    conn.execute("DELETE FROM cases")
    conn.execute("DELETE FROM audit_events")
    conn.commit()
"@

try {
    $pythonCode | Set-Content -LiteralPath $pythonFile -Encoding UTF8
    python $pythonFile
    if ($LASTEXITCODE -ne 0) {
        throw "Dashboard reset helper failed with exit code $LASTEXITCODE"
    }
}
finally {
    Remove-Item -LiteralPath $pythonFile -Force -ErrorAction SilentlyContinue
}

Write-Host "Dashboard test database reset complete."

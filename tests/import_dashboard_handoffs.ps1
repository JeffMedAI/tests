param(
    [string]$Pattern = "*_handoff.json",
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $Force) {
    $prompt = Read-Host "This will import handoff JSON into the local dashboard SQLite database. Type YES to continue"
    if ($prompt -ne "YES") {
        Write-Host "Import cancelled."
        exit 2
    }
}

$pythonFile = Join-Path $env:TEMP ("jefflocal_import_dashboard_" + [guid]::NewGuid().ToString("N") + ".py")
$pythonCode = @"
import sys
from pathlib import Path

BASE = Path(r"C:\JeffLocal\dashboard")
sys.path.insert(0, str(BASE))

from app.db import connect, init_db
from app.importer import import_handoffs

with connect() as conn:
    init_db(conn)
    count = import_handoffs(conn, pattern=r"$Pattern")

print(count)
"@

try {
    $pythonCode | Set-Content -LiteralPath $pythonFile -Encoding UTF8
    python $pythonFile
}
finally {
    Remove-Item -LiteralPath $pythonFile -Force -ErrorAction SilentlyContinue
}

Write-Host "Dashboard handoff import complete for pattern $Pattern."

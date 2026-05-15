param(
    [switch]$ConfirmReset
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $ConfirmReset) {
    throw "Refusing to reset demo/test data without -ConfirmReset."
}

$root = "C:\JeffLocal"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveRoot = Join-Path $root "backup\test_data_archives\demo_reset_$timestamp"
$prefixes = @(
    "RAWMOCK", "RX-TEST", "N8NTEST", "N8NTEST-PRODSIM", "PRODSIM",
    "DEMO", "GPDEMO", "N8NTEST-GPDEMO", "GPTDEMO"
)
$folders = @(
    "outputs\handoff_json",
    "queue\processed",
    "queue\failed",
    "queue\deadletter",
    "queue\incoming",
    "queue\processing"
)

function Test-DemoName {
    param([string]$Name)
    foreach ($prefix in $prefixes) {
        if ($Name.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

New-Item -ItemType Directory -Force -Path $archiveRoot | Out-Null
$archived = 0
$removed = 0
$skipped = 0

foreach ($relative in $folders) {
    $source = Join-Path $root $relative
    if (-not (Test-Path -LiteralPath $source)) {
        $skipped++
        continue
    }
    Get-ChildItem -LiteralPath $source -File | ForEach-Object {
        if (Test-DemoName -Name $_.BaseName) {
            $targetDir = Join-Path $archiveRoot $relative
            New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
            Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $targetDir $_.Name) -Force
            Remove-Item -LiteralPath $_.FullName -Force
            $script:archived++
            $script:removed++
        }
        else {
            $script:skipped++
        }
    }
}

$dbPath = Join-Path $root "dashboard\data\dashboard.sqlite"
if (Test-Path -LiteralPath $dbPath) {
    $python = Join-Path $root "dashboard\.venv\Scripts\python.exe"
    $code = @'
import json
import sqlite3
from pathlib import Path

root = Path(r"C:\JeffLocal")
archive = Path(r"ARCHIVE_PATH_PLACEHOLDER")
db = root / "dashboard" / "data" / "dashboard.sqlite"
prefixes = ("RAWMOCK", "RX-TEST", "N8NTEST", "N8NTEST-PRODSIM", "PRODSIM", "DEMO", "GPDEMO", "N8NTEST-GPDEMO", "GPTDEMO")

def is_demo(value):
    return any(str(value or "").upper().startswith(prefix.upper()) for prefix in prefixes)

conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
try:
    archive.mkdir(parents=True, exist_ok=True)
    cases = [dict(row) for row in conn.execute("SELECT * FROM cases").fetchall() if is_demo(row["call_id"])]
    audits = [dict(row) for row in conn.execute("SELECT * FROM audit_events").fetchall() if is_demo(row["call_id"])]
    alerts = [
        dict(row) for row in conn.execute("SELECT * FROM alert_events").fetchall()
        if is_demo(row["first_call_id"]) or is_demo(row["alert_id"])
    ]
    recordings = []
    try:
        recordings = [dict(row) for row in conn.execute("SELECT * FROM call_recordings").fetchall() if is_demo(row["call_id"])]
    except sqlite3.OperationalError:
        recordings = []
    (archive / "archived_cases.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
    (archive / "archived_audit_events.json").write_text(json.dumps(audits, indent=2), encoding="utf-8")
    (archive / "archived_alert_events.json").write_text(json.dumps(alerts, indent=2), encoding="utf-8")
    (archive / "archived_recordings.json").write_text(json.dumps(recordings, indent=2), encoding="utf-8")
    case_ids = [row["call_id"] for row in cases]
    if case_ids:
        placeholders = ",".join(["?"] * len(case_ids))
        conn.execute(f"DELETE FROM cases WHERE call_id IN ({placeholders})", case_ids)
        conn.execute(f"DELETE FROM audit_events WHERE call_id IN ({placeholders})", case_ids)
        try:
            conn.execute(f"DELETE FROM call_recordings WHERE call_id IN ({placeholders})", case_ids)
        except sqlite3.OperationalError:
            pass
    alert_ids = [row["id"] for row in alerts]
    if alert_ids:
        placeholders = ",".join(["?"] * len(alert_ids))
        conn.execute(f"DELETE FROM alert_events WHERE id IN ({placeholders})", alert_ids)
    conn.commit()
    print(json.dumps({"sqlite_archived": len(cases) + len(audits) + len(alerts) + len(recordings), "sqlite_removed_cases": len(case_ids)}))
finally:
    conn.close()
'@.Replace("ARCHIVE_PATH_PLACEHOLDER", ($archiveRoot -replace "\\", "\\"))
    $tmp = Join-Path $env:TEMP ("jefflocal_reset_demo_" + [guid]::NewGuid().ToString("N") + ".py")
    try {
        $code | Set-Content -LiteralPath $tmp -Encoding UTF8
        & $python $tmp | Write-Host
    }
    finally {
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
    }
}

[pscustomobject]@{
    archive_path = $archiveRoot
    archived_count = $archived
    removed_count = $removed
    skipped_count = $skipped
} | ConvertTo-Json -Compress

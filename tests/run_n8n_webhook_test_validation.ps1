Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$basePath = "C:\JeffLocal"
$handoffPath = Join-Path $basePath "outputs\handoff_json"
$processedPath = Join-Path $basePath "queue\processed"
$failedPath = Join-Path $basePath "queue\failed"
$deadletterPath = Join-Path $basePath "queue\deadletter"
$auditPath = Join-Path $basePath "logs\audits"
$dashboardDb = Join-Path $basePath "dashboard\data\dashboard.sqlite"

function Count-Files {
    param(
        [string]$Path,
        [string]$Filter
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        return 0
    }
    return @(Get-ChildItem -LiteralPath $Path -Filter $Filter -File -ErrorAction SilentlyContinue).Count
}

function Fail {
    param([string]$Message)
    throw "N8N webhook validation failed: $Message"
}

$handoffs = Count-Files -Path $handoffPath -Filter "N8NTEST*_handoff.json"
$processed = Count-Files -Path $processedPath -Filter "*N8NTEST*.json"
$failed = Count-Files -Path $failedPath -Filter "*N8NTEST*.json"
$deadletter = Count-Files -Path $deadletterPath -Filter "*N8NTEST*.json"

if ($handoffs -ne 5) { Fail "expected 5 N8NTEST handoffs, found $handoffs. Build/run the n8n webhook flow first." }
if ($processed -ne 5) { Fail "expected 5 N8NTEST processed files, found $processed." }
if ($failed -ne 0) { Fail "expected 0 N8NTEST failed files, found $failed." }
if ($deadletter -ne 0) { Fail "expected 0 N8NTEST deadletter files, found $deadletter." }

$auditMatches = @()
if (Test-Path -LiteralPath $auditPath) {
    $auditMatches = @(Get-ChildItem -LiteralPath $auditPath -Filter "audit_*.jsonl" -File -ErrorAction SilentlyContinue |
        Select-String -Pattern "N8NTEST", "disabled_for_test" -SimpleMatch)
}
if ($auditMatches.Count -lt 5) {
    Fail "expected Google push skipped audit entries for N8NTEST calls."
}

if (-not (Test-Path -LiteralPath $dashboardDb)) {
    Fail "dashboard SQLite database not found at $dashboardDb"
}

$python = Join-Path $basePath "dashboard\.venv\Scripts\python.exe"
$checkScript = @"
import sqlite3, json, sys
db = r"$dashboardDb"
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT call_id, priority, red_flags_present, safe_to_queue, staff_review_required FROM cases WHERE call_id LIKE 'N8NTEST-%'").fetchall()
data = {row["call_id"]: dict(row) for row in rows}
errors = []
if len(data) != 5:
    errors.append(f"expected 5 dashboard N8NTEST cases, found {len(data)}")
red = data.get("N8NTEST-005-REDFLAG")
if not red:
    errors.append("missing N8NTEST-005-REDFLAG in dashboard")
else:
    if red["priority"] != "999 Emergency":
        errors.append(f"N8NTEST-005 priority expected 999 Emergency, found {red['priority']}")
    if not bool(red["red_flags_present"]):
        errors.append("N8NTEST-005 red_flags_present expected true")
    if bool(red["safe_to_queue"]):
        errors.append("N8NTEST-005 safe_to_queue expected false")
identity = data.get("N8NTEST-004-IDENTITY")
if not identity:
    errors.append("missing N8NTEST-004-IDENTITY in dashboard")
elif not bool(identity["staff_review_required"]):
    errors.append("N8NTEST-004 staff_review_required expected true")
print(json.dumps({"cases": data, "errors": errors}, indent=2))
sys.exit(1 if errors else 0)
"@

$tempCheck = Join-Path $env:TEMP "jefflocal_n8ntest_validation.py"
Set-Content -LiteralPath $tempCheck -Value $checkScript -Encoding UTF8
& $python $tempCheck
if ($LASTEXITCODE -ne 0) {
    Fail "dashboard case checks failed."
}

Write-Host "N8N webhook test validation passed."
Write-Host "handoffs=$handoffs processed=$processed failed=$failed deadletter=$deadletter"

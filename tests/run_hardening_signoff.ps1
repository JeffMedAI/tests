[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$basePath = "C:\JeffLocal"
$runner = Join-Path $basePath "run_mock_test_v6.ps1"
$processScript = Join-Path $basePath "app\process_queue.ps1"
$auditDir = Join-Path $basePath "logs\audits"
$deadletterDir = Join-Path $basePath "queue\deadletter"
$failedDir = Join-Path $basePath "queue\failed"
$incomingDir = Join-Path $basePath "queue\incoming"
$v4Signoff = Join-Path $basePath "tests\run_v4_signoff.ps1"

function Clear-Queues {
    Remove-Item "$($basePath)\queue\incoming\*" -Force -ErrorAction SilentlyContinue
    Remove-Item "$($basePath)\queue\processing\*" -Force -ErrorAction SilentlyContinue
    Remove-Item "$($basePath)\queue\processed\*" -Force -ErrorAction SilentlyContinue
    Remove-Item "$($basePath)\queue\failed\*" -Force -ErrorAction SilentlyContinue
    Remove-Item "$($basePath)\queue\deadletter\*" -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "==== Hardening signoff starting ====" -ForegroundColor Cyan

if (-not (Test-Path $v4Signoff)) {
    throw "Missing signoff script: $v4Signoff"
}

# Part 1: Existing V4 signoff must still pass
Write-Host ""
Write-Host "==== Part 1: V4 regression signoff ====" -ForegroundColor Cyan
& $v4Signoff

if ($LASTEXITCODE -ne 0) {
    throw "V4 signoff failed."
}

# Part 2: Audit log should exist
Write-Host ""
Write-Host "==== Part 2: Audit log existence ====" -ForegroundColor Cyan
$auditLog = Join-Path $auditDir ("audit_" + (Get-Date -Format "yyyy-MM-dd") + ".jsonl")
if (-not (Test-Path $auditLog)) {
    throw "Audit log not found: $auditLog"
}
Write-Host "PASS: Audit log found -> $auditLog" -ForegroundColor Green

# Part 3: Malformed JSON should deadletter
Write-Host ""
Write-Host "==== Part 3: Deadletter malformed JSON ====" -ForegroundColor Cyan
Clear-Queues

$badFile = Join-Path $incomingDir "ZZ-INVALID-JSON.json"
@"
{ "call_id": "ZZ-INVALID-JSON", "bad_json": true
"@ | Set-Content -LiteralPath $badFile -Encoding UTF8

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $processScript

$deadletteredFile = Join-Path $deadletterDir "ZZ-INVALID-JSON.json"
$deadletterManifest = Join-Path $deadletterDir "ZZ-INVALID-JSON.json.deadletter.json"

if (-not (Test-Path $deadletteredFile)) {
    throw "Malformed JSON file was not moved to deadletter."
}
if (-not (Test-Path $deadletterManifest)) {
    throw "Deadletter manifest was not created."
}

Write-Host "PASS: Malformed JSON deadlettered correctly" -ForegroundColor Green

# Part 4: Missing call_id should deadletter
Write-Host ""
Write-Host "==== Part 4: Deadletter permanent payload failure ====" -ForegroundColor Cyan
Clear-Queues

$missingCallIdFile = Join-Path $incomingDir "ZZ-MISSING-CALLID.json"
@'
{
  "call_timestamp": "2026-04-17T12:00:00",
  "workflow": "prescription_request",
  "request_type": "prescription",
  "source": "Jeff voice agent",
  "patient_name_raw": "Test Patient",
  "dob_raw": "01 Jan 1980",
  "callback_number_raw": "07911111111",
  "medications_raw": "Test Med 1mg",
  "urgency_note_raw": "",
  "pharmacy_raw": "Boots",
  "caller_for_raw": "self",
  "raw_transcript": "Test transcript"
}
'@ | Set-Content -LiteralPath $missingCallIdFile -Encoding UTF8

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $processScript

$missingCallIdDead = Join-Path $deadletterDir "ZZ-MISSING-CALLID.json"
if (-not (Test-Path $missingCallIdDead)) {
    throw "Missing-call_id payload was not moved to deadletter."
}

Write-Host "PASS: Missing call_id payload deadlettered correctly" -ForegroundColor Green

# Part 5: Audit file should include deadletter events
Write-Host ""
Write-Host "==== Part 5: Audit log content ====" -ForegroundColor Cyan
$auditText = Get-Content -LiteralPath $auditLog -Raw
if ($auditText -notmatch "deadletter") {
    throw "Audit log does not contain deadletter events."
}
Write-Host "PASS: Audit log contains deadletter events" -ForegroundColor Green

Write-Host ""
Write-Host "==== Hardening signoff complete ====" -ForegroundColor Green
Write-Host "All checks passed." -ForegroundColor Green
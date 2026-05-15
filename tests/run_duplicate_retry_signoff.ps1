[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$basePath = "C:\JeffLocal"
$processScript = Join-Path $basePath "app\process_queue.ps1"
$incomingDir = Join-Path $basePath "queue\incoming"
$processedDir = Join-Path $basePath "queue\processed"
$failedDir = Join-Path $basePath "queue\failed"
$deadletterDir = Join-Path $basePath "queue\deadletter"
$handoffDir = Join-Path $basePath "outputs\handoff_json"
$auditDir = Join-Path $basePath "logs\audits"

function Clear-State {
    Remove-Item "$incomingDir\*" -Force -ErrorAction SilentlyContinue
    Remove-Item "$processedDir\*" -Force -ErrorAction SilentlyContinue
    Remove-Item "$failedDir\*" -Force -ErrorAction SilentlyContinue
    Remove-Item "$deadletterDir\*" -Force -ErrorAction SilentlyContinue
    Remove-Item "$handoffDir\ZZ-*" -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "==== Duplicate / retry refinement signoff ====" -ForegroundColor Cyan

Clear-State

# Test 1: duplicate call_id in same batch -> deadletter
Write-Host ""
Write-Host "Test 1: duplicate call_id in same batch" -ForegroundColor Cyan

@'
[
  {
    "call_id": "ZZ-DUP-001",
    "call_timestamp": "2026-04-17T13:00:00",
    "workflow": "prescription_request",
    "request_type": "prescription",
    "source": "Jeff voice agent",
    "patient_name_raw": "Jason Morrey",
    "dob_raw": "10 January 1970",
    "callback_number_raw": "07911110001",
    "medications_raw": "Ramipril 5mg",
    "urgency_note_raw": "",
    "pharmacy_raw": "Boots",
    "caller_for_raw": "self",
    "raw_transcript": "Test transcript A"
  },
  {
    "call_id": "ZZ-DUP-001",
    "call_timestamp": "2026-04-17T13:01:00",
    "workflow": "prescription_request",
    "request_type": "prescription",
    "source": "Jeff voice agent",
    "patient_name_raw": "Jason Morrey",
    "dob_raw": "10 January 1970",
    "callback_number_raw": "07911110002",
    "medications_raw": "Atorvastatin 20mg",
    "urgency_note_raw": "",
    "pharmacy_raw": "Boots",
    "caller_for_raw": "self",
    "raw_transcript": "Test transcript B"
  }
]
'@ | Set-Content -LiteralPath (Join-Path $incomingDir "ZZ-DUP-BATCH.json") -Encoding UTF8

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $processScript
if (-not (Test-Path (Join-Path $deadletterDir "ZZ-DUP-BATCH.json"))) {
    throw "FAIL: duplicate batch was not deadlettered"
}
Write-Host "PASS: duplicate batch deadlettered" -ForegroundColor Green

# Test 2: already processed handoff call_id -> deadletter
Write-Host ""
Write-Host "Test 2: duplicate call_id already processed" -ForegroundColor Cyan

Clear-State

@'
{
  "call_id": "ZZ-DUP-CALLID",
  "call_timestamp": "2026-04-17T13:10:00",
  "workflow": "prescription_request",
  "request_type": "prescription",
  "source": "Jeff voice agent",
  "patient_name_raw": "Jason Morrey",
  "dob_raw": "10 January 1970",
  "callback_number_raw": "07911110003",
  "medications_raw": "Ramipril 5mg",
  "urgency_note_raw": "",
  "pharmacy_raw": "Boots",
  "caller_for_raw": "self",
  "raw_transcript": "First version"
}
'@ | Set-Content -LiteralPath (Join-Path $incomingDir "ZZ-DUP-CALLID-1.json") -Encoding UTF8

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $processScript

@'
{
  "call_id": "ZZ-DUP-CALLID",
  "call_timestamp": "2026-04-17T13:11:00",
  "workflow": "prescription_request",
  "request_type": "prescription",
  "source": "Jeff voice agent",
  "patient_name_raw": "Jason Morrey",
  "dob_raw": "10 January 1970",
  "callback_number_raw": "07911110004",
  "medications_raw": "Atorvastatin 20mg",
  "urgency_note_raw": "",
  "pharmacy_raw": "Boots",
  "caller_for_raw": "self",
  "raw_transcript": "Second version"
}
'@ | Set-Content -LiteralPath (Join-Path $incomingDir "ZZ-DUP-CALLID-2.json") -Encoding UTF8

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $processScript
if (-not (Test-Path (Join-Path $deadletterDir "ZZ-DUP-CALLID-2.json"))) {
    throw "FAIL: duplicate processed call_id was not deadlettered"
}
Write-Host "PASS: duplicate processed call_id deadlettered" -ForegroundColor Green

Write-Host ""
Write-Host "==== Duplicate / retry refinement signoff complete ====" -ForegroundColor Green
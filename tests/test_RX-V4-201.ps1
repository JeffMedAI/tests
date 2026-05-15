[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$callId = "RX-V4-201"
$testFile = "RX-V4-201.json"
$basePath = "C:\JeffLocal"

$runner = Join-Path $basePath "run_mock_test_v6.ps1"
$testInputPath = Join-Path $basePath "data\test_inputs\$testFile"
$handoffPath = Join-Path $basePath "outputs\handoff_json\$($callId)_handoff.json"

$incomingPath = Join-Path $basePath "queue\incoming"
$processingPath = Join-Path $basePath "queue\processing"
$processedPath = Join-Path $basePath "queue\processed"
$failedPath = Join-Path $basePath "queue\failed"

Write-Host ""
Write-Host "==== Running test $callId ====" -ForegroundColor Cyan

if (-not (Test-Path $runner)) {
    throw "Runner not found: $runner"
}

if (-not (Test-Path $testInputPath)) {
    throw "Test file not found: $testInputPath"
}

Write-Host "Cleaning queue folders..." -ForegroundColor Yellow
Remove-Item "$incomingPath\*" -Force -ErrorAction SilentlyContinue
Remove-Item "$processingPath\*" -Force -ErrorAction SilentlyContinue
Remove-Item "$processedPath\*" -Force -ErrorAction SilentlyContinue
Remove-Item "$failedPath\*" -Force -ErrorAction SilentlyContinue
Remove-Item $handoffPath -Force -ErrorAction SilentlyContinue

Set-Location $basePath

Write-Host "Starting pipeline for $testFile ..." -ForegroundColor Yellow
& $runner -Model gemma4:e2b -BasePath $basePath -TestFile $testFile

if (-not (Test-Path $handoffPath)) {
    throw "Handoff file not found: $handoffPath"
}

$handoff = Get-Content $handoffPath -Raw | ConvertFrom-Json

Write-Host ""
Write-Host "==== Handoff result ====" -ForegroundColor Cyan
Write-Host "Call ID:              $($handoff.call_id)"
Write-Host "Verification Status:  $($handoff.verification_status)"
Write-Host "Priority:             $($handoff.priority)"
Write-Host "Patient Name:         $($handoff.normalized_input.patient_name)"
Write-Host "DOB:                  $($handoff.normalized_input.dob)"
Write-Host "Matched Patient Name: $($handoff.matched_patient_name)"
Write-Host "Matched Ref:          $($handoff.matched_patient_ref)"
Write-Host "Task Title:           $($handoff.task_title)"

Write-Host ""
if ($handoff.verification_status -eq "matched") {
    Write-Host "PASS: $callId returned matched" -ForegroundColor Green
} else {
    Write-Host "FAIL: expected matched but got $($handoff.verification_status)" -ForegroundColor Red
}
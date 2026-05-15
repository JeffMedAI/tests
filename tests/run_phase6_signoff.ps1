[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$tests = @(
    @{ File = "RX-TEST-101.json"; Expected = "matched" },
    @{ File = "RX-TEST-103.json"; Expected = "insufficient_data" },
    @{ File = "RX-TEST-108.json"; Expected = "matched" },
    @{ File = "RX-TEST-110.json"; Expected = "possible_match_weak" }
)

cd C:\JeffLocal

foreach ($test in $tests) {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "Running $($test.File) | Expected: $($test.Expected)" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan

    Remove-Item C:\JeffLocal\queue\incoming\* -Force -ErrorAction SilentlyContinue
    Remove-Item C:\JeffLocal\queue\processing\* -Force -ErrorAction SilentlyContinue
    Remove-Item C:\JeffLocal\queue\processed\* -Force -ErrorAction SilentlyContinue
    Remove-Item C:\JeffLocal\queue\failed\* -Force -ErrorAction SilentlyContinue

    .\run_mock_test_v6.ps1 -Model gemma4:e2b -BasePath C:\JeffLocal -TestFile $test.File

    $callId = [System.IO.Path]::GetFileNameWithoutExtension($test.File)
    $handoffPath = "C:\JeffLocal\outputs\handoff_json\$($callId)_handoff.json"

    if (-not (Test-Path $handoffPath)) {
        Write-Host "FAIL: handoff file not found: $handoffPath" -ForegroundColor Red
        continue
    }

    $handoff = Get-Content $handoffPath -Raw | ConvertFrom-Json
    $actual = $handoff.verification_status

    if ($actual -eq $test.Expected) {
        Write-Host "PASS: $callId verification_status = $actual" -ForegroundColor Green
    }
    else {
        Write-Host "FAIL: $callId expected $($test.Expected) but got $actual" -ForegroundColor Red
    }
}
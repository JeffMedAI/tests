[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$basePath = "C:\JeffLocal"
$runner = Join-Path $basePath "run_mock_test_v6.ps1"

$tests = @(
    @{ File = "RX-V4-201.json"; Expected = "matched" },
    @{ File = "RX-V4-202.json"; Expected = "possible_match" },
    @{ File = "RX-V4-203.json"; Expected = "possible_match" },
    @{ File = "RX-V4-204.json"; Expected = "possible_match_weak" },
    @{ File = "RX-V4-205.json"; Expected = "no_match" },
    @{ File = "RX-V4-206.json"; Expected = "insufficient_data" },
    @{ File = "RX-V4-207.json"; Expected = "matched" },
    @{ File = "RX-V4-208.json"; Expected = "matched" },
    @{ File = "RX-V4-209.json"; Expected = "matched" },
    @{ File = "RX-V4-210.json"; Expected = "insufficient_data" },
    @{ File = "RX-V4-211.json"; Expected = "possible_match_weak" },
    @{ File = "RX-V4-212.json"; Expected = "matched" }
)

function Clear-Queues {
    Remove-Item C:\JeffLocal\queue\incoming\* -Force -ErrorAction SilentlyContinue
    Remove-Item C:\JeffLocal\queue\processing\* -Force -ErrorAction SilentlyContinue
    Remove-Item C:\JeffLocal\queue\processed\* -Force -ErrorAction SilentlyContinue
    Remove-Item C:\JeffLocal\queue\failed\* -Force -ErrorAction SilentlyContinue
}

Set-Location $basePath

$results = @()

foreach ($test in $tests) {
    $callId = [System.IO.Path]::GetFileNameWithoutExtension($test.File)
    $handoffPath = "C:\JeffLocal\outputs\handoff_json\$($callId)_handoff.json"

    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "Running $($test.File) | Expected: $($test.Expected)" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan

    Clear-Queues
    Remove-Item $handoffPath -Force -ErrorAction SilentlyContinue

    & $runner -Model gemma4:e2b -BasePath $basePath -TestFile $test.File

    if (-not (Test-Path $handoffPath)) {
        $results += [pscustomobject]@{
            CallId   = $callId
            Expected = $test.Expected
            Actual   = "handoff_missing"
            Pass     = $false
        }
        Write-Host "FAIL: handoff file not found" -ForegroundColor Red
        continue
    }

    $handoff = Get-Content $handoffPath -Raw | ConvertFrom-Json
    $actual = $handoff.verification_status
    $pass = $actual -eq $test.Expected

    $results += [pscustomobject]@{
        CallId   = $callId
        Expected = $test.Expected
        Actual   = $actual
        Pass     = $pass
    }

    if ($pass) {
        Write-Host "PASS: $callId => $actual" -ForegroundColor Green
    }
    else {
        Write-Host "FAIL: $callId expected $($test.Expected) but got $actual" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "================ Final Summary ================" -ForegroundColor Yellow
$results | Format-Table -AutoSize

$results | Export-Csv "C:\JeffLocal\tests\v4_signoff_results.csv" -NoTypeInformation -Encoding UTF8
Write-Host "Saved summary to C:\JeffLocal\tests\v4_signoff_results.csv" -ForegroundColor Green
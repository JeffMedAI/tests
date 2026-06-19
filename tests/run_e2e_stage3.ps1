# E2E Stage 3 Re-run Script
# Run from C:\JeffLocal — requires n8n, dashboard (port 8765), and Ollama running.
#
# Usage:
#   cd C:\JeffLocal
#   .\tests\run_e2e_stage3.ps1
#
# What it does:
#   Runs the full 5-stage E2E test and saves results to logs\

Set-Location C:\JeffLocal

# Check prerequisites
Write-Host "`n=== E2E Pre-flight ===" -ForegroundColor Cyan
$dashOk = try { (Invoke-WebRequest http://localhost:8765/api/health -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200 } catch { $false }
$n8nOk  = try { (Invoke-WebRequest http://localhost:5678 -UseBasicParsing -TimeoutSec 3).StatusCode } catch { $false }
Write-Host "Dashboard (8765): $(if ($dashOk) { 'OK' } else { 'OFFLINE - start before running' })"
Write-Host "n8n (5678):       $(if ($n8nOk) { 'OK' } else { 'OFFLINE - start before running' })"
if (-not $dashOk) { Write-Host "`nDashboard not running. Exiting." -ForegroundColor Red; exit 1 }

Write-Host "`n=== Running E2E ===" -ForegroundColor Cyan
python tests\run_e2e_callflow_test.py --dashboard-url http://localhost:8765

Write-Host "`n=== Latest log ===" -ForegroundColor Cyan
$latest = Get-ChildItem logs\e2e_callflow_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latest) {
    $d = Get-Content $latest.FullName | ConvertFrom-Json
    Write-Host "Passed: $($d.passed) / $($d.total)"
    Write-Host "Stage 3 results:"
    $d.results | Where-Object { $_.stage -eq 3 } | ForEach-Object {
        $icon = if ($_.passed) { "[PASS]" } else { "[FAIL]" }
        Write-Host "  $icon $($_.name) — $($_.detail)"
    }
}

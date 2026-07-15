<#
.SYNOPSIS
    Force-restart JeffLocal services. Kills anything on ports 8765 / 5678 then relaunches.

.PARAMETER DashOnly   Restart dashboard only.
.PARAMETER N8nOnly    Restart n8n only.

.NOTES
    watchdog.ps1 only accepts -Once / -Force / -IntervalSeconds — it has no per-service
    switches. Passing -DashOnly/-N8nOnly through to it (the old behaviour) crashed with
    "A parameter cannot be found that matches parameter name 'DashOnly'". Fixed 2026-07-15:
    when a per-service switch is given, this script restarts that one service directly using
    the same launcher scripts watchdog itself uses. With no switches, it still defers to
    watchdog -Force to restart everything.
#>
param([switch]$DashOnly, [switch]$N8nOnly)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$watchdog  = "$ScriptDir\watchdog.ps1"

function Stop-PortProcess([int]$port) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        Where-Object { $_ -gt 0 } |
        ForEach-Object {
            Write-Host "  Killing PID $_ on port $port"
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
    if ($port -eq 5678) { Start-Sleep -Seconds 4 } else { Start-Sleep -Milliseconds 800 }
}

function Test-Http([string]$url) {
    try {
        $resp = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        return ($resp.StatusCode -lt 500)
    } catch { return $false }
}

function Start-HiddenPS([string]$script) {
    $ps = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    Start-Process -FilePath $ps `
        -ArgumentList "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$script`"" `
        -WindowStyle Hidden
}

if ($DashOnly -or $N8nOnly) {
    if ($DashOnly) {
        Write-Host "Restarting dashboard only..."
        Stop-PortProcess 8765
        Start-HiddenPS "$ScriptDir\_launch_dashboard.ps1"
        Start-Sleep -Seconds 12
        if (Test-Http "http://localhost:8765/api/health") {
            Write-Host "Dashboard restarted OK."
        } else {
            Write-Host "Dashboard did not come back up — check logs\service_control\dashboard.log" -ForegroundColor Red
        }
    }
    if ($N8nOnly) {
        Write-Host "Restarting n8n only..."
        Stop-PortProcess 5678
        Start-HiddenPS "$ScriptDir\_launch_n8n.ps1"
        Start-Sleep -Seconds 25
        if (Test-Http "http://localhost:5678/healthz") {
            Write-Host "n8n restarted OK."
        } else {
            Write-Host "n8n did not come back up — check logs\service_control\n8n.log" -ForegroundColor Red
        }
    }
} else {
    Write-Host "Restarting all JeffLocal services..."
    & $watchdog -Force -Once
}

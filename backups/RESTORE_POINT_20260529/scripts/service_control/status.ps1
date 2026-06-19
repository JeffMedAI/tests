<#
.SYNOPSIS
    Show live status of JeffLocal services and last 20 lines of each log.
#>

$LogDir = "C:\JeffLocal\logs\service_control"

function Test-Port([int]$port) {
    try {
        $tcp = [System.Net.Sockets.TcpClient]::new()
        $ar  = $tcp.BeginConnect("127.0.0.1", $port, $null, $null)
        $ok  = $ar.AsyncWaitHandle.WaitOne(1500, $false)
        try { if ($ok) { $tcp.EndConnect($ar) } } catch {}
        $tcp.Close()
        return $ok
    } catch { return $false }
}

function Show-ServiceStatus([string]$name, [int]$port) {
    $up  = Test-Port $port
    $pid_ = (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
                Select-Object -First 1).OwningProcess
    $label = if ($up) { "UP  " } else { "DOWN" }
    $color = if ($up) { "Green" } else { "Red" }
    Write-Host "  [$label] $name  port $port" -ForegroundColor $color -NoNewline
    if ($pid_) { Write-Host "  (PID $pid_)" } else { Write-Host "" }
}

function Show-Log([string]$label, [string]$file, [int]$lines = 20) {
    Write-Host ""
    Write-Host "--- $label ($file) ---" -ForegroundColor Cyan
    if (Test-Path $file) {
        Get-Content $file -Tail $lines | ForEach-Object { Write-Host "  $_" }
    } else {
        Write-Host "  (no log file yet)"
    }
}

Write-Host ""
Write-Host "=== JeffLocal Service Status ===" -ForegroundColor Yellow
Show-ServiceStatus "Dashboard" 8765
Show-ServiceStatus "n8n      " 5678

Write-Host ""
Write-Host "=== Auto-start ===" -ForegroundColor Yellow

$regVal = Get-ItemProperty "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "JeffLocal" -ErrorAction SilentlyContinue
if ($regVal) {
    Write-Host "  [OK] Registry Run key: JeffLocal"
} else {
    Write-Host "  [MISSING] Registry Run key - run install_scheduled_tasks.ps1" -ForegroundColor Red
}

$task = Get-ScheduledTask -TaskName "JeffLocal-Watchdog" -ErrorAction SilentlyContinue
if ($task) {
    $info = Get-ScheduledTaskInfo -TaskName "JeffLocal-Watchdog" -ErrorAction SilentlyContinue
    $next = if ($info -and $info.NextRunTime -gt [datetime]"2000-01-01") { $info.NextRunTime.ToString("yyyy-MM-dd HH:mm:ss") } else { "unknown" }
    Write-Host "  [OK] JeffLocal-Watchdog task  state=$($task.State)  next=$next"
} else {
    Write-Host "  [MISSING] JeffLocal-Watchdog task - run install_scheduled_tasks.ps1" -ForegroundColor Red
}

Show-Log "Watchdog"  "$LogDir\watchdog.log"
Show-Log "Dashboard" "$LogDir\dashboard.log"
Show-Log "n8n"       "$LogDir\n8n.log"

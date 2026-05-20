<#
.SYNOPSIS
    JeffLocal service watchdog.
    Checks dashboard (8765) and n8n (5678). Starts either if down.
    Called by Task Scheduler: at logon, every 5 min, and on workstation unlock.

.PARAMETER Force
    Kill and restart both services even if they appear healthy.

.PARAMETER DashOnly
    Only check / restart the dashboard.

.PARAMETER N8nOnly
    Only check / restart n8n.
#>
param(
    [switch]$Force,
    [switch]$DashOnly,
    [switch]$N8nOnly
)

$ErrorActionPreference = "SilentlyContinue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir    = "C:\JeffLocal\logs\service_control"
$WatchLog  = "$LogDir\watchdog.log"
$PS        = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

function wlog([string]$msg, [string]$lvl = "INFO") {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$lvl] $msg"
    if ((Test-Path $WatchLog) -and (Get-Item $WatchLog).Length -gt 2MB) {
        Move-Item $WatchLog "$WatchLog.old" -Force
    }
    Add-Content -Path $WatchLog -Value $line -Force
    Write-Host $line
}

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

# HTTP-level check: catches stuck processes that hold the port but don't serve
function Test-Http([string]$url) {
    try {
        $resp = Invoke-WebRequest -Uri $url -TimeoutSec 4 -UseBasicParsing -ErrorAction Stop
        return ($resp.StatusCode -lt 500)
    } catch {
        return $false
    }
}

function Test-Dashboard {
    if (-not (Test-Port 8765)) { return $false }
    return Test-Http "http://localhost:8765/api/health"
}

function Test-N8n {
    if (-not (Test-Port 5678)) { return $false }
    return Test-Http "http://localhost:5678/healthz"
}

function Stop-PortProcess([int]$port) {
    # Kill any process holding the port (Listen OR stuck Established)
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        Where-Object { $_ -gt 0 } |
        ForEach-Object {
            wlog "  Killing PID $_ on port $port" "WARN"
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
    # n8n: SQLite DB lock takes a moment to release after kill
    if ($port -eq 5678) { Start-Sleep -Seconds 4 }
    else                 { Start-Sleep -Milliseconds 800 }
}

function Start-HiddenPS([string]$script) {
    $psArgs = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""$script"""
    Start-Process -FilePath $PS -ArgumentList $psArgs -WindowStyle Hidden
}

# ---------------------------------------------------------------------------
wlog "=== watchdog start (Force=$Force DashOnly=$DashOnly N8nOnly=$N8nOnly) ==="

# --- DASHBOARD --------------------------------------------------------------
if (-not $N8nOnly) {
    $dashUp = Test-Dashboard

    if ($dashUp -and -not $Force) {
        wlog "Dashboard OK (port 8765)"
    } else {
        if ($dashUp) { wlog "Force-restart: stopping dashboard" "WARN" }
        else {
            if (Test-Port 8765) { wlog "Dashboard port up but HTTP dead (stuck process) - restarting" "WARN" }
            else                 { wlog "Dashboard DOWN on port 8765 - starting" "WARN" }
        }

        Stop-PortProcess 8765

        $venvPy = "C:\JeffLocal\dashboard\.venv\Scripts\python.exe"
        if (-not (Test-Path $venvPy)) {
            wlog "venv missing - running one-time setup (may take 30 s)" "WARN"
            python -m venv "C:\JeffLocal\dashboard\.venv" 2>&1 | Out-Null
            & $venvPy -m pip install -r "C:\JeffLocal\dashboard\requirements.txt" --quiet 2>&1 | Out-Null
        }

        Start-HiddenPS "$ScriptDir\_launch_dashboard.ps1"
        Start-Sleep -Seconds 10

        if (Test-Dashboard) { wlog "Dashboard started OK" }
        else                 { wlog "Dashboard still not up - check $LogDir\dashboard.log" "ERROR" }
    }
}

# --- N8N --------------------------------------------------------------------
if (-not $DashOnly) {
    $n8nUp = Test-N8n

    if ($n8nUp -and -not $Force) {
        wlog "n8n OK (port 5678)"
    } else {
        if ($n8nUp) { wlog "Force-restart: stopping n8n" "WARN" }
        else {
            if (Test-Port 5678) { wlog "n8n port up but HTTP dead (stuck node) - restarting" "WARN" }
            else                 { wlog "n8n DOWN on port 5678 - starting" "WARN" }
        }

        Stop-PortProcess 5678

        $n8nCmd = "$env:APPDATA\npm\n8n.cmd"
        if (-not (Test-Path $n8nCmd)) {
            wlog "n8n.cmd not found at $n8nCmd - is n8n installed? (npm install -g n8n)" "ERROR"
        } else {
            Start-HiddenPS "$ScriptDir\_launch_n8n.ps1"
            Start-Sleep -Seconds 20

            if (Test-N8n) { wlog "n8n started OK" }
            else           { wlog "n8n still not up - check $LogDir\n8n.log" "ERROR" }
        }
    }
}

wlog "=== watchdog done ==="

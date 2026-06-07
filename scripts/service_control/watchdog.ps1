<#
.SYNOPSIS
    JeffLocal hardened service watchdog.
    Monitors all production services. Restarts if down.
    Sends WhatsApp alerts on failure. Caps restarts to avoid loops.

.DESCRIPTION
    Services monitored:
      - Production dashboard  : port 8765  (FastAPI/uvicorn)
      - n8n                   : port 5678
      - Ollama                : port 11434
      - Cloudflare tunnel     : process check (cloudflared.exe)

    Sandbox removed 2026-06-07. No port 5000 monitoring.

    Restart cap: 3 per service per hour. After cap hit → CRITICAL alert + stop retrying until next hour.
    WhatsApp alerts: sent via python send_whatsapp.py on DOWN and CRITICAL events.

    Run modes:
      - Continuous loop (default): runs forever, checks every 60 seconds.
        Register via Task Scheduler as AtStartup / run indefinitely.
      - Single pass (-Once): checks once and exits (legacy / debug mode).

.PARAMETER Once
    Run a single check pass and exit (no loop).

.PARAMETER Force
    Force-restart all services regardless of health.

.PARAMETER IntervalSeconds
    Seconds between checks in loop mode (default: 60).
#>
param(
    [switch]$Once,
    [switch]$Force,
    [int]$IntervalSeconds = 60
)

$ErrorActionPreference = "SilentlyContinue"

# ── Paths ─────────────────────────────────────────────────────────────────────
$RepoRoot       = "C:\JeffLocal"
$LogDir         = "$RepoRoot\logs\service_control"
$WatchLog       = "$LogDir\watchdog.log"
$AlertScript    = "$RepoRoot\scripts\daily\send_whatsapp.py"
$RestartState   = "$LogDir\restart_state.json"
$PS             = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$ScriptDir      = Split-Path -Parent $MyInvocation.MyCommand.Path

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# ── Logging ───────────────────────────────────────────────────────────────────
function wlog([string]$msg, [string]$lvl = "INFO") {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$lvl] $msg"
    # Rotate log at 5 MB
    if ((Test-Path $WatchLog) -and (Get-Item $WatchLog).Length -gt 5MB) {
        Move-Item $WatchLog "$WatchLog.old" -Force
    }
    Add-Content -Path $WatchLog -Value $line -Force
    Write-Host $line
}

# ── WhatsApp alert ────────────────────────────────────────────────────────────
function Send-Alert([string]$message) {
    if (-not (Test-Path $AlertScript)) { return }
    try {
        $tmpFile = [System.IO.Path]::GetTempFileName() + ".txt"
        Set-Content -Path $tmpFile -Value $message -Encoding UTF8
        Start-Process -FilePath "python" -ArgumentList "`"$AlertScript`" `"$tmpFile`"" -WindowStyle Hidden
        wlog "WhatsApp alert sent: $message" "ALERT"
    } catch {
        wlog "Failed to send WhatsApp alert: $_" "ERROR"
    }
}

# ── Restart rate limiter ──────────────────────────────────────────────────────
# State file: JSON dict of serviceName -> list of restart timestamps (epoch seconds)
# Also tracks last-alert timestamps to suppress repeated WhatsApp alerts.
$RestartMax   = 3     # max restarts per hour per service
$AlertCooldown = 3600  # seconds between repeated CRITICAL alerts per service

function Get-RestartState {
    if (Test-Path $RestartState) {
        try { return Get-Content $RestartState -Raw | ConvertFrom-Json } catch {}
    }
    return [PSCustomObject]@{}
}

function Save-RestartState($state) {
    $state | ConvertTo-Json -Depth 5 | Set-Content -Path $RestartState -Encoding UTF8 -Force
}

function Test-RestartAllowed([string]$svc) {
    $state = Get-RestartState
    $now   = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $hour  = 3600

    $timestamps = @()
    if ($state.PSObject.Properties[$svc]) {
        $timestamps = @($state.$svc | Where-Object { ($now - $_) -lt $hour })
    }

    $state | Add-Member -NotePropertyName $svc -NotePropertyValue $timestamps -Force
    Save-RestartState $state

    return ($timestamps.Count -lt $RestartMax)
}

function Record-Restart([string]$svc) {
    $state = Get-RestartState
    $now   = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $hour  = 3600

    $timestamps = @()
    if ($state.PSObject.Properties[$svc]) {
        $timestamps = @($state.$svc | Where-Object { ($now - $_) -lt $hour })
    }
    $timestamps += $now

    $state | Add-Member -NotePropertyName $svc -NotePropertyValue $timestamps -Force
    Save-RestartState $state
}

function Get-RestartCount([string]$svc) {
    $state = Get-RestartState
    $now   = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $hour  = 3600
    if ($state.PSObject.Properties[$svc]) {
        return @($state.$svc | Where-Object { ($now - $_) -lt $hour }).Count
    }
    return 0
}

# Send alert only if cooldown has elapsed since last alert for this service.
function Send-AlertThrottled([string]$svc, [string]$message) {
    $state   = Get-RestartState
    $now     = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $alertKey = "${svc}_lastAlert"

    $lastAlert = 0
    if ($state.PSObject.Properties[$alertKey]) { $lastAlert = [long]$state.$alertKey }

    if (($now - $lastAlert) -lt $AlertCooldown) {
        wlog "Alert suppressed (cooldown): $message" "INFO"
        return
    }

    $state | Add-Member -NotePropertyName $alertKey -NotePropertyValue $now -Force
    Save-RestartState $state
    Send-Alert $message
}

# ── Port / HTTP checks ────────────────────────────────────────────────────────
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

function Test-Http([string]$url) {
    try {
        $resp = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        return ($resp.StatusCode -lt 500)
    } catch { return $false }
}

function Stop-PortProcess([int]$port) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        Where-Object { $_ -gt 0 } |
        ForEach-Object {
            wlog "  Killing PID $_ on port $port" "WARN"
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
    if ($port -eq 5678) { Start-Sleep -Seconds 4 }
    else                 { Start-Sleep -Milliseconds 800 }
}

function Start-HiddenPS([string]$script) {
    Start-Process -FilePath $PS `
        -ArgumentList "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$script`"" `
        -WindowStyle Hidden
}

# ── Service definitions ───────────────────────────────────────────────────────
# Each service: Name, TestFn (returns $true if healthy), RestartFn
$Services = @(

    [PSCustomObject]@{
        Name = "ProductionDashboard"
        Label = "Production Dashboard (8765)"
        Test = {
            if (-not (Test-Port 8765)) { return $false }
            return (Test-Http "http://localhost:8765/api/health")
        }
        Restart = {
            Stop-PortProcess 8765
            $launch = "$ScriptDir\_launch_dashboard.ps1"
            if (Test-Path $launch) {
                Start-HiddenPS $launch
            } else {
                # Fallback: launch Flask directly
                $venvPy = "$RepoRoot\dashboard\.venv\Scripts\python.exe"
                if (-not (Test-Path $venvPy)) {
                    python -m venv "$RepoRoot\dashboard\.venv" 2>&1 | Out-Null
                    & $venvPy -m pip install -r "$RepoRoot\dashboard\requirements.txt" --quiet 2>&1 | Out-Null
                }
                Start-Process -FilePath $venvPy `
                    -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8765" `
                    -WorkingDirectory "$RepoRoot\dashboard\app" `
                    -WindowStyle Hidden
            }
            Start-Sleep -Seconds 12
            return (Test-Http "http://localhost:8765/api/health")
        }
    },

    [PSCustomObject]@{
        Name = "N8n"
        Label = "n8n (5678)"
        Test = {
            if (-not (Test-Port 5678)) { return $false }
            return (Test-Http "http://localhost:5678/healthz")
        }
        Restart = {
            Stop-PortProcess 5678
            $launch = "$ScriptDir\_launch_n8n.ps1"
            if (Test-Path $launch) {
                Start-HiddenPS $launch
            } else {
                $n8nCmd = "$env:APPDATA\npm\n8n.cmd"
                if (Test-Path $n8nCmd) {
                    Start-Process -FilePath "cmd.exe" `
                        -ArgumentList "/c `"$n8nCmd`" start" `
                        -WindowStyle Hidden
                } else {
                    wlog "n8n.cmd not found — is n8n installed? (npm install -g n8n)" "ERROR"
                    return $false
                }
            }
            Start-Sleep -Seconds 25
            return (Test-Http "http://localhost:5678/healthz")
        }
    },

    [PSCustomObject]@{
        Name = "Ollama"
        Label = "Ollama (11434)"
        Test = {
            if (-not (Test-Port 11434)) { return $false }
            return (Test-Http "http://localhost:11434/api/tags")
        }
        Restart = {
            # Kill any stuck ollama process
            Get-Process -Name "ollama" -ErrorAction SilentlyContinue | Stop-Process -Force
            Start-Sleep -Seconds 2
            # Start ollama serve in background
            Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 8
            return (Test-Http "http://localhost:11434/api/tags")
        }
    },

    [PSCustomObject]@{
        Name = "CloudflareTunnel"
        Label = "Cloudflare Tunnel (cloudflared)"
        Test = {
            $proc = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
            return ($null -ne $proc)
        }
        Restart = {
            # Look for cloudflared config
            $cfConfig = "$RepoRoot\config\cloudflared.yml"
            $cfExeCmd = Get-Command "cloudflared" -ErrorAction SilentlyContinue
            $cfExe = if ($cfExeCmd) { $cfExeCmd.Source } else { $null }
            if (-not $cfExe) { $cfExe = "C:\Program Files\cloudflared\cloudflared.exe" }
            if (-not (Test-Path $cfExe)) {
                wlog "cloudflared.exe not found - cannot auto-restart tunnel" "ERROR"
                return $false
            }
            if (Test-Path $cfConfig) {
                Start-Process -FilePath $cfExe `
                    -ArgumentList "tunnel --config `"$cfConfig`" run" `
                    -WindowStyle Hidden
            } else {
                Start-Process -FilePath $cfExe `
                    -ArgumentList "tunnel run" `
                    -WindowStyle Hidden
            }
            Start-Sleep -Seconds 6
            $proc = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
            return ($null -ne $proc)
        }
    }
)

# ── Single check pass ─────────────────────────────────────────────────────────
function Invoke-CheckPass {
    wlog "--- check pass ---"

    foreach ($svc in $Services) {
        $healthy = & $svc.Test

        if ($healthy -and -not $Force) {
            wlog "$($svc.Label) OK"
            continue
        }

        $reason = if ($Force) { "forced restart" } else { "DOWN" }
        wlog "$($svc.Label) $reason" "WARN"

        # Check restart cap
        if (-not (Test-RestartAllowed $svc.Name)) {
            $count = Get-RestartCount $svc.Name
            wlog "$($svc.Label) restart cap hit ($count/$RestartMax in last hour) — CRITICAL" "ERROR"
            Send-AlertThrottled $svc.Name "CRITICAL: $($svc.Label) has been down for >1 hour and cannot be auto-restarted. Manual intervention needed. (JeffLocal watchdog)"
            continue
        }

        # Attempt restart
        wlog "Restarting $($svc.Label)..." "WARN"
        Send-Alert "ALERT: $($svc.Label) went DOWN — attempting restart. (JeffLocal watchdog)"

        Record-Restart $svc.Name
        $recovered = & $svc.Restart

        if ($recovered) {
            wlog "$($svc.Label) recovered OK" "INFO"
        } else {
            $count = Get-RestartCount $svc.Name
            wlog "$($svc.Label) still not up after restart attempt ($count/$RestartMax this hour)" "ERROR"
            if ($count -ge $RestartMax) {
                Send-Alert "CRITICAL: $($svc.Label) failed $RestartMax restart attempts in 1 hour. Manual intervention needed. (JeffLocal watchdog)"
            }
        }
    }
}

# ── Main ──────────────────────────────────────────────────────────────────────
wlog "=== JeffLocal watchdog started (Once=$Once Force=$Force IntervalSeconds=$IntervalSeconds) ==="
Send-Alert "JeffLocal watchdog STARTED on $env:COMPUTERNAME at $(Get-Date -Format 'yyyy-MM-dd HH:mm')"

if ($Once) {
    Invoke-CheckPass
} else {
    while ($true) {
        try {
            Invoke-CheckPass
        } catch {
            wlog "Unexpected error in check pass: $_" "ERROR"
        }
        Start-Sleep -Seconds $IntervalSeconds
    }
}

wlog "=== watchdog exited ==="

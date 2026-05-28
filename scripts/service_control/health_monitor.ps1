<#
.SYNOPSIS
    JeffLocal comprehensive health monitor — runs every 10 minutes.
    Checks: Dashboard, n8n, Ollama, git repo integrity.
    On failure: runs diagnostics → soft restart → hard restart → dashboard alert.
    Separate from watchdog.ps1 (crash-recovery). This script does DEEP health checking.

.NOTES
    Registered as: JeffLocal-HealthMonitor Task Scheduler task (every 10 min)
    Log: C:\JeffLocal\logs\service_control\health_monitor.log
#>
$ErrorActionPreference = "SilentlyContinue"

$ROOT     = "C:\JeffLocal"
$ScriptDir= Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir   = "$ROOT\logs\service_control"
$LogFile  = "$LogDir\health_monitor.log"
$StateFile= "$LogDir\health_monitor_state.json"
$PS       = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$DashUrl  = "http://localhost:8765"
$N8nUrl   = "http://localhost:5678"
$OllamaUrl= "http://localhost:11434"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# ── Logging ─────────────────────────────────────────────────────────────
function hlog([string]$msg, [string]$lvl = "INFO") {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$lvl] $msg"
    if ((Test-Path $LogFile) -and (Get-Item $LogFile).Length -gt 3MB) {
        Move-Item $LogFile "$LogFile.old" -Force
    }
    Add-Content -Path $LogFile -Value $line -Force
    if ($lvl -ne "INFO") { Write-Warning $line } else { Write-Host $line }
}

# ── State persistence (track consecutive failures) ───────────────────────
function Get-State {
    if (Test-Path $StateFile) {
        try { return Get-Content $StateFile -Raw | ConvertFrom-Json } catch {}
    }
    return [PSCustomObject]@{ dashboard=0; n8n=0; ollama=0; git=0; last_alert="" }
}

function Save-State($state) {
    $state | ConvertTo-Json | Set-Content $StateFile -Force
}

# ── HTTP probe ────────────────────────────────────────────────────────────
function Test-Http([string]$url, [int]$timeoutSec = 4) {
    try {
        $resp = Invoke-WebRequest -Uri $url -TimeoutSec $timeoutSec -UseBasicParsing -ErrorAction Stop
        return ($resp.StatusCode -lt 500)
    } catch { return $false }
}

# ── TCP probe ─────────────────────────────────────────────────────────────
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

# ── Post alert to dashboard DB ────────────────────────────────────────────
function Send-DashAlert([string]$service, [string]$message, [string]$severity = "warning") {
    $body = @{
        service  = $service
        message  = $message
        severity = $severity
        source   = "health_monitor"
        timestamp= (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    } | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri "$DashUrl/api/alerts/ingest" -Method POST `
            -Body $body -ContentType "application/json" -TimeoutSec 5 -ErrorAction Stop
        hlog "Alert posted to dashboard: $message"
    } catch {
        hlog "Could not post alert to dashboard (dashboard may be down): $_" "WARN"
    }
}

# ── Restart helper ─────────────────────────────────────────────────────────
function Invoke-Watchdog([string]$args) {
    & $PS -NoProfile -NonInteractive -ExecutionPolicy Bypass `
        -File "$ScriptDir\watchdog.ps1" @args -ErrorAction SilentlyContinue
}

# ── Service checks ─────────────────────────────────────────────────────────
function Check-Dashboard($state) {
    $name = "Dashboard"
    $ok   = Test-Port 8765
    if ($ok) { $ok = Test-Http "$DashUrl/api/health" }

    if ($ok) {
        if ($state.dashboard -gt 0) { hlog "$name recovered after $($state.dashboard) failures" }
        $state.dashboard = 0
        return $state
    }

    $state.dashboard++
    hlog "$name UNHEALTHY (consecutive failures: $($state.dashboard))" "WARN"

    if ($state.dashboard -eq 1) {
        hlog "$name: attempting soft restart via watchdog" "WARN"
        Invoke-Watchdog "-DashOnly"
        Start-Sleep -Seconds 12
        if (Test-Http "$DashUrl/api/health") {
            hlog "$name recovered after soft restart"
            $state.dashboard = 0
            return $state
        }
    }

    if ($state.dashboard -ge 2) {
        hlog "$name: hard restart (force)" "ERROR"
        Invoke-Watchdog "-DashOnly -Force"
        Start-Sleep -Seconds 15
        if (-not (Test-Http "$DashUrl/api/health")) {
            hlog "$name still down after hard restart — manual intervention needed" "ERROR"
            Send-DashAlert "dashboard" "Dashboard is DOWN and auto-restart failed. Check logs at $LogDir\dashboard.log" "critical"
        } else {
            hlog "$name recovered after hard restart"
            $state.dashboard = 0
        }
    }
    return $state
}

function Check-N8n($state) {
    $name = "n8n"
    $ok   = Test-Port 5678
    if ($ok) { $ok = Test-Http "$N8nUrl/healthz" }

    if ($ok) {
        if ($state.n8n -gt 0) { hlog "$name recovered after $($state.n8n) failures" }
        $state.n8n = 0
        return $state
    }

    $state.n8n++
    hlog "$name UNHEALTHY (consecutive failures: $($state.n8n))" "WARN"

    if ($state.n8n -eq 1) {
        hlog "$name: attempting soft restart via watchdog" "WARN"
        Invoke-Watchdog "-N8nOnly"
        Start-Sleep -Seconds 22
        if (Test-Http "$N8nUrl/healthz") {
            hlog "$name recovered after soft restart"
            $state.n8n = 0
            return $state
        }
    }

    if ($state.n8n -ge 2) {
        hlog "$name: hard restart (force)" "ERROR"
        Invoke-Watchdog "-N8nOnly -Force"
        Start-Sleep -Seconds 25
        if (-not (Test-Http "$N8nUrl/healthz")) {
            hlog "$name still down after hard restart — manual intervention needed" "ERROR"
            Send-DashAlert "n8n" "n8n workflows are DOWN and auto-restart failed. Check $LogDir\n8n.log" "critical"
        } else {
            hlog "$name recovered after hard restart"
            $state.n8n = 0
        }
    }
    return $state
}

function Check-Ollama($state) {
    $name = "Ollama"
    $ok   = Test-Port 11434
    if ($ok) { $ok = Test-Http "$OllamaUrl/api/tags" }

    if ($ok) {
        if ($state.ollama -gt 0) { hlog "$name recovered after $($state.ollama) failures" }
        $state.ollama = 0
        return $state
    }

    $state.ollama++
    hlog "$name UNHEALTHY (consecutive failures: $($state.ollama))" "WARN"

    if ($state.ollama -eq 1) {
        hlog "$name: attempting start via 'ollama serve'" "WARN"
        $ollamaExe = (Get-Command ollama -ErrorAction SilentlyContinue)?.Source
        if ($ollamaExe) {
            Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 10
            if (Test-Http "$OllamaUrl/api/tags") {
                hlog "$name started OK"
                $state.ollama = 0
                return $state
            }
        } else {
            hlog "$name: ollama.exe not found in PATH — is Ollama installed?" "ERROR"
        }
    }

    if ($state.ollama -ge 2) {
        hlog "$name still unreachable after auto-start attempt" "ERROR"
        Send-DashAlert "ollama" "Ollama AI is unreachable on port 11434. Pipeline extraction will fail until Ollama is restored." "warning"
    }
    return $state
}

function Check-GitRepo($state) {
    $name = "Git repo"
    $repoPath = $ROOT
    try {
        $gitStatus = & git -C $repoPath status --porcelain 2>&1
        $gitLog    = & git -C $repoPath log -1 --format="%h %s" 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "git status failed"
        }
        $dirtyCount = ($gitStatus | Where-Object { $_ -match '^\s*[MADRCU?!]' }).Count
        if ($dirtyCount -gt 50) {
            hlog "$name: $dirtyCount uncommitted changes — unusually high (threshold: 50)" "WARN"
            Send-DashAlert "git" "$dirtyCount uncommitted changes in repo. Consider committing or reviewing." "info"
        } else {
            if ($state.git -gt 0) { hlog "$name recovered" }
            hlog "$name OK — last commit: $gitLog | dirty files: $dirtyCount"
            $state.git = 0
        }
    } catch {
        $state.git++
        hlog "$name check FAILED: $_" "ERROR"
        if ($state.git -ge 2) {
            Send-DashAlert "git" "Git repo integrity check failed. Check $ROOT for corruption." "warning"
        }
    }
    return $state
}

# ── Main ──────────────────────────────────────────────────────────────────
hlog "=== health_monitor start ==="
$state = Get-State

$state = Check-Dashboard $state
$state = Check-N8n       $state
$state = Check-Ollama    $state
$state = Check-GitRepo   $state

Save-State $state
hlog "=== health_monitor done ==="

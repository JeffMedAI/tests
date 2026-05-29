# strategy_daily.ps1
# JeffLocal - Strategy Agent Daily Report
# Schedule: Windows Task Scheduler, daily at 07:00
# Label: "JeffLocal - Strategy Agent Daily Report"
#
# What this script does:
#   1. Reads all session logs from last 24 hours (docs\sessions\)
#   2. Reads git log for last 24 hours
#   3. Checks document freshness
#   4. Updates PROJECT_MEMORY.md current status section
#   5. Generates daily briefing: what we did / plan today / blockers
#   6. Saves report to docs\reports\{date}.md
#   7. Commits and pushes to git
#
# Last updated: 2026-05-29

param(
    [string]$RepoRoot    = "C:\JeffLocal",
    [string]$ReportsDir  = "C:\JeffLocal\docs\reports",
    [string]$SessionsDir = "C:\JeffLocal\docs\sessions",
    [string]$ProjectDocs = "C:\JeffLocal\docs\project_documents",
    [string]$MemoryFile  = "C:\JeffLocal\PROJECT_MEMORY.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Today     = (Get-Date).ToString("yyyy-MM-dd")
$Yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
$NowUTC    = (Get-Date).ToUniversalTime().ToString("HH:mm")
$LogFile   = "$RepoRoot\scripts\daily\last_run.log"

function Write-Log {
    param([string]$Message)
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss UTC")
    $entry = "[$ts] $Message"
    Write-Host $entry
    Add-Content -Path $LogFile -Value $entry -ErrorAction SilentlyContinue
}

Write-Log "strategy_daily.ps1 started for $Today"

# ── 1. Read session logs from last 24 hours ───────────────────────────────────
Write-Log "Reading session logs from $SessionsDir..."
$SessionSummaries = @()

if (Test-Path $SessionsDir) {
    $AllSessions = Get-ChildItem -Path $SessionsDir -Filter "*.md" |
        Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" } |
        Sort-Object LastWriteTime -Descending

    foreach ($s in $AllSessions) {
        $Age = ((Get-Date) - $s.LastWriteTime).TotalHours
        if ($Age -le 24) {
            $content = Get-Content $s.FullName -Raw -ErrorAction SilentlyContinue
            $SessionSummaries += [PSCustomObject]@{
                File    = $s.Name
                Age     = [math]::Round($Age, 1)
                Content = $content
            }
        }
    }
}
Write-Log "Found $($SessionSummaries.Count) session log(s) from last 24h"

# ── 2. Extract sections from session logs ────────────────────────────────────
$WhatWeDid = @(); $Blockers = @(); $Approvals = @(); $NextTasks = @()

foreach ($session in $SessionSummaries) {
    $lines = $session.Content -split "`n"
    $inDid = $false; $inBlock = $false; $inApproval = $false; $inNext = $false

    foreach ($line in $lines) {
        if ($line -match "^## WHAT WE DID")    { $inDid=$true; $inBlock=$false; $inApproval=$false; $inNext=$false; continue }
        if ($line -match "^## BLOCKERS")        { $inBlock=$true; $inDid=$false; $inApproval=$false; $inNext=$false; continue }
        if ($line -match "^## PENDING SAEED")   { $inApproval=$true; $inDid=$false; $inBlock=$false; $inNext=$false; continue }
        if ($line -match "^## WHAT TO DO NEXT") { $inNext=$true; $inDid=$false; $inBlock=$false; $inApproval=$false; continue }
        if ($line -match "^## ")                { $inDid=$false; $inBlock=$false; $inApproval=$false; $inNext=$false; continue }

        $clean = $line.Trim()
        if ($clean -and $clean -notmatch "^#" -and $clean -ne "---") {
            if ($inDid     -and $clean -match "^\d+\.")  { $WhatWeDid += $clean -replace "^\d+\.\s*","" }
            if ($inBlock   -and $clean -match "^-")      { $Blockers  += $clean -replace "^-\s*","" }
            if ($inApproval -and $clean -match "^\[")    { $Approvals += $clean -replace "^\[.\]\s*","" }
            if ($inNext    -and $clean -match "^\d+\.")  { $NextTasks += $clean -replace "^\d+\.\s*","" }
        }
    }
}

# ── 3. Git log last 24 hours ──────────────────────────────────────────────────
Write-Log "Collecting git log..."
Push-Location $RepoRoot
try {
    $GitLog = git log --oneline --since="24 hours ago" 2>&1
    if (-not $GitLog) { $GitLog = "(no commits in last 24 hours)" }
    $LatestCommit = (git log --oneline -1 2>&1)
} catch {
    $GitLog = "(git log failed)"; $LatestCommit = "unknown"
}
Pop-Location

# ── 4. Document freshness check ───────────────────────────────────────────────
$StaleDocs = @()
if (Test-Path $ProjectDocs) {
    Get-ChildItem -Path $ProjectDocs -Filter "*.md" -Recurse | ForEach-Object {
        $days = ((Get-Date) - $_.LastWriteTime).Days
        if ($days -gt 3) { $StaleDocs += "$($_.Name) (${days}d old)" }
    }
}

# ── 5. Update PROJECT_MEMORY.md date + git state ─────────────────────────────
Write-Log "Updating PROJECT_MEMORY.md..."
if (Test-Path $MemoryFile) {
    $memory = Get-Content $MemoryFile -Raw
    $memory = $memory -replace "# Last updated: .+", "# Last updated: $Today (auto-updated 07:00)"
    if ($LatestCommit -ne "unknown") {
        $memory = $memory -replace "Latest:\s+.+", "Latest:  $LatestCommit"
    }
    Set-Content -Path $MemoryFile -Value $memory -Encoding UTF8
    Write-Log "PROJECT_MEMORY.md updated"
}

# ── 6. Build daily briefing ───────────────────────────────────────────────────
$DidSection = if ($WhatWeDid.Count -gt 0) { ($WhatWeDid | Select-Object -First 8 | ForEach-Object { "- $_" }) -join "`n" } else { "- No session logs found for last 24h. Check docs\sessions\." }
$BlockerSection = if ($Blockers.Count -gt 0) { ($Blockers | Select-Object -Unique | ForEach-Object { "- $_" }) -join "`n" } else { "- None logged." }
$ApprovalSection = if ($Approvals.Count -gt 0) { ($Approvals | Select-Object -Unique | ForEach-Object { "- [ ] $_" }) -join "`n" } else { "- None outstanding." }
$NextSection = if ($NextTasks.Count -gt 0) { ($NextTasks | Select-Object -First 5 | ForEach-Object { "- $_" }) -join "`n" } else { "- See PROJECT_MEMORY.md open tasks." }
$GitSection = if ($GitLog -is [array]) { ($GitLog | Select-Object -First 10) -join "`n" } else { $GitLog }
$StaleSection = if ($StaleDocs.Count -gt 0) { ($StaleDocs | ForEach-Object { "- $_" }) -join "`n" } else { "- All documents current." }
$SessionFiles = if ($SessionSummaries.Count -gt 0) { ($SessionSummaries | ForEach-Object { "- $($_.File) ($($_.Age)h ago)" }) -join "`n" } else { "- None found." }

$Report = @"
# JEFFLOCAL - DAILY BRIEFING
Date: $Today
Generated: $NowUTC UTC by strategy_daily.ps1
Source: Session logs + git (last 24h)

---

## WHAT WE DID YESTERDAY

$DidSection

---

## WHAT IS PLANNED TODAY

$NextSection

---

## WHAT IS BLOCKING US

$BlockerSection

---

## PENDING SAEED APPROVALS

$ApprovalSection

---

## GIT ACTIVITY (last 24h)

$GitSection

---

## SESSION LOGS COMPILED

$SessionFiles

---

## DOCUMENT HEALTH

$StaleSection

---

*Auto-generated 07:00. Session logs: docs\sessions\  Full memory: PROJECT_MEMORY.md*
"@

# ── 7. Save report ────────────────────────────────────────────────────────────
if (-not (Test-Path $ReportsDir)) { New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null }
$ReportPath = "$ReportsDir\$Today.md"
Set-Content -Path $ReportPath -Value $Report -Encoding UTF8
Write-Log "Report saved: $ReportPath"

# ── 8. Commit + push ──────────────────────────────────────────────────────────
Write-Log "Committing to git..."
Push-Location $RepoRoot
try {
    git config user.email "215987900+Avamedio@users.noreply.github.com"
    git config user.name "Saeed"
    git add PROJECT_MEMORY.md "docs\reports\$Today.md" 2>&1 | Out-Null
    git commit -m "memory: daily auto-update $Today 07:00" 2>&1 | Out-Null
    git push origin HEAD 2>&1 | Out-Null
    Write-Log "Git push complete"
} catch {
    Write-Log "WARNING: Git push failed - $_"
}
Pop-Location

# ── 9. Write last_run summary ─────────────────────────────────────────────────
$Summary = "COMPLETE | Sessions: $($SessionSummaries.Count) | Stale docs: $($StaleDocs.Count) | Report: $ReportPath"
Write-Log $Summary
Set-Content -Path $LogFile -Value "[$Today $NowUTC UTC] strategy_daily $Summary" -Encoding UTF8
Write-Host "Done. Report: $ReportPath" -ForegroundColor Green

# ── 10. Send report via WhatsApp ──────────────────────────────────────────────
Write-Log "Sending report via WhatsApp..."
$PythonScript = "$RepoRoot\scripts\daily\send_whatsapp.py"
try {
    $result = python $PythonScript $ReportPath 2>&1
    Write-Log "WhatsApp send result: $result"
} catch {
    Write-Log "WARNING: WhatsApp send failed - $_"
}

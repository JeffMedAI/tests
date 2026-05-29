# strategy_daily.ps1
# JeffLocal — Strategy Agent Daily Report
# Trigger: Windows Task Scheduler, daily at 07:00
# Label: "JeffLocal — Strategy Agent Daily Report"
# Owner: Strategy Agent (via Lead Agent DevOps registration)
#
# What this script does:
#   1. Reads git log for the last 24 hours
#   2. Checks document freshness in docs\project_documents\
#   3. Triggers Strategy Agent to generate the daily report
#   4. Saves report to docs\reports\{date}.md
#   5. Sends Dispatch summary to Saeed
#
# Last updated: 2026-05-29
# Registered by: DevOps Agent (pending registration — see criterion 4 note)

param(
    [string]$RepoRoot = "C:\JeffLocal",
    [string]$ReportsDir = "C:\JeffLocal\docs\reports",
    [string]$ProjectDocsDir = "C:\JeffLocal\docs\project_documents"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Date helpers ──────────────────────────────────────────────────────────────
$Today     = (Get-Date).ToString("yyyy-MM-dd")
$Yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
$NowUTC    = (Get-Date).ToUniversalTime().ToString("HH:mm")
$LogFile   = "$RepoRoot\scripts\daily\last_run.log"

function Write-Log {
    param([string]$Message)
    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss UTC")
    $entry = "[$timestamp] $Message"
    Write-Host $entry
    Add-Content -Path $LogFile -Value $entry
}

# ── 1. Git log — last 24 hours ────────────────────────────────────────────────
Write-Log "strategy_daily.ps1 started"
Write-Log "Collecting git log (last 24h)..."

Push-Location $RepoRoot
try {
    $GitLog = git log --oneline --since="24 hours ago" 2>&1
    if (-not $GitLog) { $GitLog = "(no commits in last 24 hours)" }
} catch {
    $GitLog = "(git log failed: $_)"
}
Pop-Location

Write-Log "Git log collected: $($GitLog.Count) entries"

# ── 2. Document freshness check ───────────────────────────────────────────────
Write-Log "Checking document freshness in $ProjectDocsDir..."

$StaleDocs   = @()
$FreshnessThresholdDays = 3

if (Test-Path $ProjectDocsDir) {
    $Docs = Get-ChildItem -Path $ProjectDocsDir -Filter "*.md" -Recurse
    foreach ($Doc in $Docs) {
        $DaysSinceUpdate = ((Get-Date) - $Doc.LastWriteTime).Days
        if ($DaysSinceUpdate -gt $FreshnessThresholdDays) {
            $StaleDocs += [PSCustomObject]@{
                Name        = $Doc.Name
                LastUpdated = $Doc.LastWriteTime.ToString("yyyy-MM-dd")
                DaysOld     = $DaysSinceUpdate
            }
        }
    }
}

Write-Log "Document check complete. Stale docs found: $($StaleDocs.Count)"

# ── 3. Read yesterday's report (for context) ──────────────────────────────────
$YesterdayReport = ""
$YesterdayReportPath = "$ReportsDir\$Yesterday.md"
if (Test-Path $YesterdayReportPath) {
    $YesterdayReport = Get-Content $YesterdayReportPath -Raw
    Write-Log "Yesterday's report loaded from $YesterdayReportPath"
} else {
    Write-Log "No report found for $Yesterday — first run or gap in schedule"
}

# ── 4. Build daily report ─────────────────────────────────────────────────────
Write-Log "Building daily report for $Today..."

$StaleDocTable = if ($StaleDocs.Count -gt 0) {
    ($StaleDocs | ForEach-Object { "- $($_.Name) | Last updated: $($_.LastUpdated) | $($_.DaysOld) days old" }) -join "`n"
} else {
    "None — all documents are current."
}

$GitLogFormatted = if ($GitLog -is [array]) {
    ($GitLog | Select-Object -First 20) -join "`n"
} else {
    $GitLog
}

$ReportContent = @"
# STRATEGY AGENT — DAILY REPORT
Date: $Today
Generated: $NowUTC UTC

---

## PROJECT STATUS
Sprint / phase:     [Populated by Strategy Agent on session start]
Overall progress:   [Populated by Strategy Agent on session start]
Last completed:     [Populated by Strategy Agent on session start]
Next in queue:      [Populated by Strategy Agent on session start]
Open blockers:      [Populated by Strategy Agent on session start]

---

## GIT ACTIVITY (last 24h)

$GitLogFormatted

---

## DOCUMENT REPOSITORY STATUS

$StaleDocTable

---

## FLAGS & ACTIONS REQUIRED

[Strategy Agent to populate on session start based on stale doc list above]

---

## MARKETING ACTIONS DUE THIS WEEK

[Strategy Agent to populate on session start]

---

## AGENT PROMPT OBSERVATIONS

[Strategy Agent to populate on session start]

---

## DISPATCH SUMMARY (sent to Saeed)

[Strategy Agent to populate on session start — 2-3 sentences: project status, flags, recommendation]

---
Note: This report skeleton was generated automatically by strategy_daily.ps1 at 07:00.
Strategy Agent will populate all bracketed fields when triggered.
"@

# ── 5. Save report ────────────────────────────────────────────────────────────
$ReportPath = "$ReportsDir\$Today.md"

if (-not (Test-Path $ReportsDir)) {
    New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null
    Write-Log "Created reports directory: $ReportsDir"
}

Set-Content -Path $ReportPath -Value $ReportContent -Encoding UTF8
Write-Log "Report saved to $ReportPath"

# ── 6. Log completion ─────────────────────────────────────────────────────────
$Summary = "strategy_daily.ps1 complete. Report: $ReportPath | Stale docs: $($StaleDocs.Count) | Git commits (24h): $(if ($GitLog -is [array]) { $GitLog.Count } else { 0 })"
Write-Log $Summary

# Write last_run.log summary line (read by Lead Agent on startup)
$RunEntry = "[$Today $NowUTC UTC] strategy_daily — $Summary"
Set-Content -Path "$RepoRoot\scripts\daily\last_run.log" -Value $RunEntry -Encoding UTF8

Write-Host ""
Write-Host "strategy_daily.ps1 finished. Report at: $ReportPath"

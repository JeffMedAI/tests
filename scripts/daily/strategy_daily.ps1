# strategy_daily.ps1
# JeffLocal - Strategy Agent Daily Report
# Schedule: Windows Task Scheduler, daily at 07:00
# Label: "JeffLocal - Strategy Agent Daily Report"
#
# What this script does:
#   1. Reads all session logs from last 24 hours (docs\sessions\)
#   2. Reads git log for last 24 hours
#   3. Checks document freshness
#   4. Checks document freshness
#   5. STATE VERIFICATION: compares PROJECT_MEMORY current status vs session logs
#      — extracts pending/blocked items from memory
#      — checks for drift (memory items with no recent log activity)
#      — appends STATE VERIFICATION section to report
#   6. Updates PROJECT_MEMORY.md current status section
#   7. Generates daily briefing: what we did / plan today / blockers
#   8. Saves report to docs\reports\{date}.md
#   9. Commits and pushes to git
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

# ── 5. STATE VERIFICATION — compare PROJECT_MEMORY with session logs ─────────
Write-Log "Running state verification..."

$MemoryContent = if (Test-Path $MemoryFile) { Get-Content $MemoryFile -Raw } else { "" }

# Extract CURRENT STATUS section from PROJECT_MEMORY.md
$MemoryStatus = ""
if ($MemoryContent -match "(?s)## CURRENT STATUS.*?(?=\n---|\n## )") {
    $MemoryStatus = $Matches[0]
}

# Pull last 5 commits for cross-reference
Push-Location $RepoRoot
try {
    $Last5Commits = git log --oneline -5 2>&1
} catch {
    $Last5Commits = "(git log failed)"
}
Pop-Location

# Extract pending/blocked items from PROJECT_MEMORY current status
$MemoryPendingItems = @()
if ($MemoryStatus) {
    foreach ($line in ($MemoryStatus -split "`n")) {
        $l = $line.Trim()
        if ($l -match "(BLOCKED|Awaiting Saeed|PENDING|awaiting sign-off)" -and $l -ne "") {
            $MemoryPendingItems += $l -replace "^\|?\s*", "" -replace "\s*\|.*$", ""
        }
    }
}

# Collect all topics mentioned in session logs (last 24h)
$SessionTopics = @()
foreach ($session in $SessionSummaries) {
    foreach ($line in ($session.Content -split "`n")) {
        $l = $line.Trim()
        if ($l -match "(cookie|main\.py|N1|N2|R2|GDPR|sandbox|degraded|sign-off|approval)" -and $l -ne "") {
            $SessionTopics += $l
        }
    }
}

# Detect drift: memory items with no corresponding session log activity
$DriftItems = @()
foreach ($item in $MemoryPendingItems) {
    # Check if any session log line references keywords from this item
    $keywords = ($item -replace "[|#\[\]\(\)\*`"]","").Split(" ") |
        Where-Object { $_.Length -gt 5 } | Select-Object -First 3
    $found = $false
    foreach ($kw in $keywords) {
        if ($SessionTopics -join " " -match [regex]::Escape($kw)) { $found = $true; break }
    }
    if (-not $found) { $DriftItems += $item }
}

# Build STATE VERIFICATION section text
$MemoryPendingText = if ($MemoryPendingItems.Count -gt 0) {
    ($MemoryPendingItems | Select-Object -First 10 | ForEach-Object { "- $_" }) -join "`n"
} else { "- No pending/blocked items found in PROJECT_MEMORY current status." }

$DriftText = if ($DriftItems.Count -gt 0) {
    ($DriftItems | ForEach-Object { "- DRIFT: No recent session activity for: $_" }) -join "`n"
} else { "- No drift detected. All memory items have corresponding recent log activity." }

$CommitText = if ($Last5Commits -is [array]) { $Last5Commits -join "`n" } else { $Last5Commits }

$StateVerificationSection = @"

---

## STATE VERIFICATION

*Cross-check: PROJECT_MEMORY current status vs session logs (last 24h)*

### What PROJECT_MEMORY says is pending / blocked

$MemoryPendingText

### Last 5 commits (cross-reference anchor)

$CommitText

### Drift analysis

$DriftText

*Drift = items marked pending/blocked in PROJECT_MEMORY with no matching session log activity in the last 24h.*
*If drift items are present, they may need manual review — either genuinely stale or session log missing.*
"@

Write-Log "State verification complete. Memory pending items: $($MemoryPendingItems.Count). Drift items: $($DriftItems.Count)."

# ── 6. Update PROJECT_MEMORY.md date + git state ────────────────────────────
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

# ── 7. Build daily briefing ───────────────────────────────────────────────────
$DidSection = if ($WhatWeDid.Count -gt 0) { ($WhatWeDid | Select-Object -First 8 | ForEach-Object { "- $_" }) -join "`n" } else { "- No session logs found for last 24h. Check docs\sessions\." }
$BlockerSection = if ($Blockers.Count -gt 0) { ($Blockers | Select-Object -Unique | ForEach-Object { "- $_" }) -join "`n" } else { "- None logged." }
$ApprovalSection = if ($Approvals.Count -gt 0) { ($Approvals | Select-Object -Unique | ForEach-Object { "- [ ] $_" }) -join "`n" } else { "- None outstanding." }
$NextSection = if ($NextTasks.Count -gt 0) { ($NextTasks | Select-Object -First 5 | ForEach-Object { "- $_" }) -join "`n" } else { "- See PROJECT_MEMORY.md open tasks." }
$GitSection = if ($GitLog -is [array]) { ($GitLog | Select-Object -First 10) -join "`n" } else { $GitLog }
$StaleSection = if ($StaleDocs.Count -gt 0) { ($StaleDocs | ForEach-Object { "- $_" }) -join "`n" } else { "- All documents current." }
$SessionFiles = if ($SessionSummaries.Count -gt 0) { ($SessionSummaries | ForEach-Object { "- $($_.File) ($($_.Age)h ago)" }) -join "`n" } else { "- None found." }

$Report = @"
MORNING BRIEF — $Today — 07:00

---

YESTERDAY
$DidSection

---

TODAY
$NextSection

---

BLOCKED
$BlockerSection

---

YOUR CALL (approvals needed)
$ApprovalSection

---

GIT (last 24h)
$GitSection

---

DOCUMENT HEALTH
$StaleSection
$StateVerificationSection

---

Full memory: PROJECT_MEMORY.md | Session logs: docs\sessions\
"@

# ── 8. Save report ────────────────────────────────────────────────────────────
if (-not (Test-Path $ReportsDir)) { New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null }
$ReportPath = "$ReportsDir\$Today.md"
Set-Content -Path $ReportPath -Value $Report -Encoding UTF8
Write-Log "Report saved: $ReportPath"

# ── 9. Commit + push ──────────────────────────────────────────────────────────
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

# ── 10. Write last_run summary ────────────────────────────────────────────────
$Summary = "COMPLETE | Sessions: $($SessionSummaries.Count) | Stale docs: $($StaleDocs.Count) | Report: $ReportPath"
Write-Log $Summary
Set-Content -Path $LogFile -Value "[$Today $NowUTC UTC] strategy_daily $Summary" -Encoding UTF8
Write-Host "Done. Report: $ReportPath" -ForegroundColor Green

# ── 11. Send report via WhatsApp ──────────────────────────────────────────────
Write-Log "Sending report via WhatsApp..."
$PythonScript = "$RepoRoot\scripts\daily\send_whatsapp.py"
if (Test-Path $PythonScript) {
    try {
        $result = python $PythonScript $ReportPath 2>&1
        Write-Log "WhatsApp send result: $result"
    } catch {
        Write-Log "WARNING: WhatsApp send failed - $_"
    }
} else {
    Write-Log "WARNING: WhatsApp sender not found at $PythonScript"
}

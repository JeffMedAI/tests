# strategy_daily.ps1
# JeffLocal - Strategy Agent Daily Brief (plain English for Saeed)
#
# TWO scheduled runs (same script, different -Mode):
#   -Mode Morning  -> 07:00  "MORNING BRIEF"  (look ahead: yesterday recap + today's plan)
#   -Mode Evening  -> 19:00  "EVENING BRIEF"  (session close: what we did today + handover)
#
# COMBINED MODE: When called as a scheduled task (no -DryRun, no -RepoRoot override)
# this script forwards to combined_brief.ps1, which covers BOTH projects (JeffLocal +
# St Marks Pharmacy / STMARKS-WEB) in a single WhatsApp message.
# The -DryRun flag suppresses the forward so combined_brief.ps1 can call this script
# internally without recursion.
#
# Last updated: 2026-06-26

param(
    [ValidateSet('Morning','Evening')]
    [string]$Mode        = 'Morning',
    [switch]$DryRun,
    [string]$RepoRoot    = "C:\JeffLocal",
    [string]$ReportsDir  = "C:\JeffLocal\docs\reports",
    [string]$SessionsDir = "C:\JeffLocal\docs\sessions",
    [string]$ProjectDocs = "C:\JeffLocal\docs\project_documents",
    [string]$MemoryFile  = "C:\JeffLocal\PROJECT_MEMORY.md"
)

# ── Mode-dependent labels ─────────────────────────────────────────────────────
if ($Mode -eq 'Evening') {
    $BriefTitle = "EVENING BRIEF (session close)"
    $BriefClock = "19:00"
    $DidLabel   = "WHAT WE DID TODAY"
    $NextLabel  = "WHAT IS NEXT (tomorrow)"
} else {
    $BriefTitle = "MORNING BRIEF"
    $BriefClock = "07:00"
    $DidLabel   = "WHAT WE DID YESTERDAY"
    $NextLabel  = "WHAT WE ARE DOING TODAY"
}

# ── COMBINED BRIEF FORWARD ────────────────────────────────────────────────────
# When called as a scheduled task (DryRun not set, default RepoRoot) forward to
# combined_brief.ps1 which covers both projects. combined_brief.ps1 then calls
# this script with -DryRun to update PROJECT_MEMORY without looping.
$_CombinedScript = "C:\JeffLocal\scripts\daily\combined_brief.ps1"
if (-not $DryRun -and $RepoRoot -eq "C:\JeffLocal" -and (Test-Path $_CombinedScript)) {
    Write-Host "Forwarding to combined_brief.ps1 (covers JeffLocal + St Marks Pharmacy)..."
    & $_CombinedScript -Mode $Mode
    exit $LASTEXITCODE
}

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
            $content = Get-Content $s.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
            $SessionSummaries += [PSCustomObject]@{
                File    = $s.Name
                Age     = [math]::Round($Age, 1)
                Content = $content
            }
        }
    }
}
Write-Log "Found $($SessionSummaries.Count) session log(s) from last 24h"

# ── 1b. Fallback: if no logs in last 24h, use the most recent one (any age) ───
# Guarantees the brief is NEVER empty. PROJECT_MEMORY is still read below as a
# second source. The "session logs not found" dead-end must never happen.
$UsedFallbackLog = $false
if ($SessionSummaries.Count -eq 0 -and (Test-Path $SessionsDir)) {
    $MostRecent = Get-ChildItem -Path $SessionsDir -Filter "*.md" |
        Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($MostRecent) {
        $UsedFallbackLog = $true
        $content = Get-Content $MostRecent.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        $SessionSummaries += [PSCustomObject]@{
            File    = $MostRecent.Name
            Age     = [math]::Round(((Get-Date) - $MostRecent.LastWriteTime).TotalHours, 1)
            Content = $content
        }
        Write-Log "No logs in last 24h — fell back to most recent: $($MostRecent.Name)"
    } else {
        Write-Log "WARNING: docs\sessions\ has no session logs at all. Session-close protocol was skipped."
    }
}

# ── 2. Extract sections from session logs ────────────────────────────────────
$WhatWeDid = @(); $Blockers = @(); $Approvals = @(); $NextTasks = @()

foreach ($session in $SessionSummaries) {
    $lines = $session.Content -split "`n"
    $inDid = $false; $inBlock = $false; $inApproval = $false; $inNext = $false

    foreach ($line in $lines) {
        # Section headers — broad matches so renamed headings still resolve
        if ($line -match "^## WHAT WE DID")         { $inDid=$true;      $inBlock=$false; $inApproval=$false; $inNext=$false; continue }
        if ($line -match "^## BLOCKERS")             { $inBlock=$true;    $inDid=$false;   $inApproval=$false; $inNext=$false; continue }
        if ($line -match "^## PENDING SAEED")        { $inApproval=$true; $inDid=$false;   $inBlock=$false;   $inNext=$false; continue }
        if ($line -match "^## OPEN TASKS")                   { $inNext=$true;     $inDid=$false; $inBlock=$false;   $inApproval=$false; continue }
        if ($line -match "^## WHAT TO DO")           { $inNext=$true;     $inDid=$false;   $inBlock=$false;   $inApproval=$false; continue }
        if ($line -match "^## ")                     { $inDid=$false;     $inBlock=$false; $inApproval=$false; $inNext=$false; continue }

        $clean = $line.Trim()
        if ($clean -and $clean -notmatch "^#" -and $clean -ne "---") {
            # Accept both numbered (1.) and bullet (-) list items for all sections
            $isBullet   = $clean -match "^-\s+"
            $isNumbered = $clean -match "^\d+\."

            if ($inDid -and ($isNumbered -or $isBullet)) {
                $WhatWeDid += $clean -replace "^(\d+\.\s*|-\s*\[.\]\s*|-\s*)", ""
            }
            if ($inBlock -and $isBullet) {
                $Blockers += $clean -replace "^-\s*", ""
            }
            if ($inApproval -and ($isNumbered -or $isBullet)) {
                # Strip leading markers: "1.", "- [ ]", "- [x]", "- ", "[ ]", "**" bold markers
                $Approvals += $clean `
                    -replace "^(\d+\.\s*|-\s*\[.\]\s*|-\s*|\[.\]\s*)", "" `
                    -replace "^\*\*", "" `
                    -replace "\*\*$", "" `
                    -replace "\*\*", ""
            }
            if ($inNext -and ($isNumbered -or $isBullet)) {
                $NextTasks += $clean -replace "^(\d+\.\s*|-\s*\[.\]\s*|-\s*)", ""
            }
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

$MemoryContent = if (Test-Path $MemoryFile) { Get-Content $MemoryFile -Raw -Encoding UTF8 } else { "" }

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

## MEMORY CHECK

Pending/blocked in PROJECT_MEMORY:
$MemoryPendingText

Last 5 commits:
$CommitText

Drift (memory items with no session log match):
$DriftText
"@

Write-Log "State verification complete. Memory pending items: $($MemoryPendingItems.Count). Drift items: $($DriftItems.Count)."

# ── 6. Update PROJECT_MEMORY.md date + git state ────────────────────────────
Write-Log "Updating PROJECT_MEMORY.md..."
if (Test-Path $MemoryFile) {
    $memory = Get-Content $MemoryFile -Raw -Encoding UTF8
    $memory = $memory -replace "# Last updated: .+", "# Last updated: $Today (auto-updated $BriefClock)"
    if ($LatestCommit -ne "unknown") {
        $memory = $memory -replace "Latest:\s+.+", "Latest:  $LatestCommit"
    }
    if ($DryRun) {
        Write-Log "DryRun: skipped PROJECT_MEMORY.md write"
    } else {
        Set-Content -Path $MemoryFile -Value $memory -Encoding UTF8
        Write-Log "PROJECT_MEMORY.md updated"
    }
}

# ── 7. Build daily briefing ───────────────────────────────────────────────────
$DidSection      = if ($WhatWeDid.Count -gt 0) { ($WhatWeDid | Select-Object -First 8 | ForEach-Object { "- $_" }) -join "`n" } else { "- No session log in last 24h. Check PROJECT_MEMORY.md." }
$BlockerSection  = if ($Blockers.Count -gt 0)  { ($Blockers  | Select-Object -Unique  | ForEach-Object { "- $_" }) -join "`n" } else { "- None." }
$ApprovalSection = if ($Approvals.Count -gt 0) { ($Approvals | Select-Object -Unique  | ForEach-Object { "- [ ] $_" }) -join "`n" } else { "- None." }
$NextSection     = if ($NextTasks.Count -gt 0) { ($NextTasks | Select-Object -First 5  | ForEach-Object { "- $_" }) -join "`n" } else { "- Nothing queued. Check PROJECT_MEMORY.md." }
$GitSection      = if ($GitLog -is [array])    { ($GitLog    | Select-Object -First 10) -join "`n" } else { $GitLog }
$StaleSection    = if ($StaleDocs.Count -gt 0) { ($StaleDocs | ForEach-Object { "- $_" }) -join "`n" } else { "- All docs current." }

$FallbackNote = if ($UsedFallbackLog) {
    $FallbackAge = [math]::Round($SessionSummaries[0].Age, 0)
    "`n⚠ No session log past 24h. Using last known: $($SessionSummaries[0].File) (${FallbackAge}h ago). Normal if weekend / no work done.`n"
} else { "" }

$Report = @"
$BriefTitle — $Today — $BriefClock
$FallbackNote
---

$DidLabel
$DidSection

---

$NextLabel
$NextSection

---

BLOCKERS
$BlockerSection

---

NEEDS YOUR OK
$ApprovalSection

---

GIT
$GitSection

---

STALE DOCS
$StaleSection
$StateVerificationSection

---

Detail: PROJECT_MEMORY.md | Logs: docs\sessions\
"@

# ── 8. Save report ────────────────────────────────────────────────────────────
if (-not (Test-Path $ReportsDir)) { New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null }
$ReportPath = if ($Mode -eq 'Evening') { "$ReportsDir\$Today-evening.md" } else { "$ReportsDir\$Today.md" }
Set-Content -Path $ReportPath -Value $Report -Encoding UTF8
Write-Log "Report saved: $ReportPath"

# ── 8b. Evening mode: write session log if Claude didn't write one today ─────
# Guarantees the brief parser always finds bullet-format content to extract.
# Writes ONLY if no session log file exists for today (human session takes priority).
$SessionLogPath = $null
if ($Mode -eq 'Evening') {
    $TodayLogs = Get-ChildItem -Path $SessionsDir -Filter "$Today-*.md" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" }
    if (-not $TodayLogs) {
        $SessionLogPath = "$SessionsDir\$Today-1800.md"
        $NoWorkContent = @"
# SESSION SUMMARY — [$Today 18:00]
# Tool: Cowork (automated session end)
# Written by: Claude scheduled task at $BriefClock

---

## WHAT WE DID

- No human session today — automated close.

---

## BLOCKERS

$BlockerSection

---

## PENDING SAEED APPROVALS

$ApprovalSection

---

## WHAT TO DO NEXT SESSION

$NextSection

---

## GIT STATE

Latest commit: $LatestCommit
Branch: sandbox
"@
        if (-not $DryRun) {
            Set-Content -Path $SessionLogPath -Value $NoWorkContent -Encoding UTF8
            Write-Log "No session log for today — wrote automated placeholder: $SessionLogPath"
        } else {
            Write-Log "DryRun: would write session log: $SessionLogPath"
        }
    }
}

# ── 9. Commit + push ──────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Log "DryRun: skipped git commit/push"
} else {
    Write-Log "Committing to git..."
    Push-Location $RepoRoot
    try {
        git config user.email "215987900+Avamedio@users.noreply.github.com"
        git config user.name "Saeed"
        $FilesToAdd = @("PROJECT_MEMORY.md", $ReportPath)
        if ($SessionLogPath -and (Test-Path $SessionLogPath)) { $FilesToAdd += $SessionLogPath }
        git add $FilesToAdd 2>&1 | Out-Null
        git commit -m "memory: $($Mode.ToLower()) brief $Today $BriefClock" 2>&1 | Out-Null
        git push origin HEAD 2>&1 | Out-Null
        Write-Log "Git push complete"
    } catch {
        Write-Log "WARNING: Git push failed - $_"
    }

    # Evening mode: create restore tag for this day's state
    if ($Mode -eq 'Evening') {
        try {
            $RestoreTag = "restore/$Today-1800"
            $TagExists = git tag -l $RestoreTag 2>&1
            if (-not $TagExists) {
                git tag $RestoreTag 2>&1 | Out-Null
                git push origin $RestoreTag 2>&1 | Out-Null
                Write-Log "Restore tag created: $RestoreTag"

                # Keep only 3 most recent restore tags
                $AllRestoreTags = @(git tag -l "restore/*" 2>&1 | Where-Object { $_ -match "^restore/" } | Sort-Object)
                if ($AllRestoreTags.Count -gt 3) {
                    $ToDelete = $AllRestoreTags | Select-Object -First ($AllRestoreTags.Count - 3)
                    foreach ($oldTag in $ToDelete) {
                        git tag -d $oldTag 2>&1 | Out-Null
                        git push origin ":refs/tags/$oldTag" 2>&1 | Out-Null
                        Write-Log "Pruned old restore tag: $oldTag"
                    }
                }
            } else {
                Write-Log "Restore tag already exists: $RestoreTag"
            }
        } catch {
            Write-Log "WARNING: Restore tag creation failed - $_"
        }
    }
    Pop-Location
}

# ── 10. Write last_run summary ────────────────────────────────────────────────
$Summary = "COMPLETE | Sessions: $($SessionSummaries.Count) | Stale docs: $($StaleDocs.Count) | Report: $ReportPath"
Write-Log $Summary
Set-Content -Path $LogFile -Value "[$Today $NowUTC UTC] strategy_daily $Summary" -Encoding UTF8
Write-Host "Done. Report: $ReportPath" -ForegroundColor Green

# ── 11. Send report via WhatsApp ──────────────────────────────────────────────
if ($DryRun) {
    Write-Log "DryRun: skipped WhatsApp send"
} else {
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
}

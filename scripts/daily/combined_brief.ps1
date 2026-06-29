# combined_brief.ps1
# Sends ONE combined daily brief covering BOTH active projects:
#   1. JeffLocal (Avamed AI triage system)
#   2. STMARKS-WEB (St Marks Pharmacy website)
#
# Replaces the individual strategy_daily.ps1 call in Task Scheduler.
# The individual scripts still exist and can run standalone.
#
# Mode:
#   -Mode Morning (07:00) — look ahead: yesterday + today's plan
#   -Mode Evening (19:00) — look back: what we did + what's next
#
# Last updated: 2026-06-26

param(
    [ValidateSet('Morning','Evening')]
    [string]$Mode    = 'Morning',
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Today  = (Get-Date).ToString("yyyy-MM-dd")
$NowUTC = (Get-Date).ToUniversalTime().ToString("HH:mm")
$LogFile = "C:\JeffLocal\scripts\daily\combined_brief_last_run.log"

function Write-Log {
    param([string]$Message)
    $ts    = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss UTC")
    $entry = "[$ts] $Message"
    Write-Host $entry
    Add-Content -Path $LogFile -Value $entry -ErrorAction SilentlyContinue
}

Write-Log "combined_brief.ps1 started - $Mode - $Today"

# ── Helper: extract sections from session logs in a given directory ───────────
function Get-ProjectBrief {
    param(
        [string]$SessionsDir,
        [string]$ProjectLabel,
        [string]$Mode
    )

    if ($Mode -eq 'Evening') {
        $DidLabel  = "WHAT WE DID TODAY"
        $NextLabel = "WHAT IS NEXT (tomorrow)"
    } else {
        $DidLabel  = "WHAT WE DID YESTERDAY"
        $NextLabel = "WHAT WE ARE DOING TODAY"
    }

    $SessionSummaries = @()
    if (Test-Path $SessionsDir) {
        $AllSessions = Get-ChildItem -Path $SessionsDir -Filter "*.md" |
            Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" } |
            Sort-Object LastWriteTime -Descending

        foreach ($s in $AllSessions) {
            $Age = ((Get-Date) - $s.LastWriteTime).TotalHours
            if ($Age -le 24) {
                $content = Get-Content $s.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
                $SessionSummaries += [PSCustomObject]@{ File = $s.Name; Content = $content }
            }
        }
    }

    # Fallback to most recent log if none in last 24h
    $FallbackNote = ""
    if ($SessionSummaries.Count -eq 0 -and (Test-Path $SessionsDir)) {
        $MostRecent = Get-ChildItem -Path $SessionsDir -Filter "*.md" |
            Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" } |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($MostRecent) {
            $AgeH = [math]::Round(((Get-Date) - $MostRecent.LastWriteTime).TotalHours, 0)
            $content = Get-Content $MostRecent.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
            $SessionSummaries += [PSCustomObject]@{ File = $MostRecent.Name; Content = $content }
            $FallbackNote = "(No log today - using $($MostRecent.Name), ${AgeH}h ago)"
        } else {
            $FallbackNote = "(No session logs found at all)"
        }
    }

    # Extract the 4 standard sections
    $WhatWeDid = @(); $Blockers = @(); $Approvals = @(); $NextTasks = @()

    foreach ($session in $SessionSummaries) {
        $lines  = $session.Content -split "`n"
        $inDid  = $false; $inBlock = $false; $inApproval = $false; $inNext = $false

        foreach ($line in $lines) {
            if ($line -match "^## WHAT WE DID")   { $inDid=$true;      $inBlock=$false; $inApproval=$false; $inNext=$false; continue }
            if ($line -match "^## BLOCKERS")       { $inBlock=$true;    $inDid=$false;   $inApproval=$false; $inNext=$false; continue }
            if ($line -match "^## PENDING SAEED")  { $inApproval=$true; $inDid=$false;   $inBlock=$false;   $inNext=$false; continue }
            if ($line -match "^## WHAT TO DO")     { $inNext=$true;     $inDid=$false;   $inBlock=$false;   $inApproval=$false; continue }
            if ($line -match "^## OPEN TASKS")     { $inNext=$true;     $inDid=$false;   $inBlock=$false;   $inApproval=$false; continue }
            if ($line -match "^## ")               { $inDid=$false;     $inBlock=$false; $inApproval=$false; $inNext=$false; continue }

            $clean = $line.Trim()
            if ($clean -and $clean -notmatch "^#" -and $clean -ne "---") {
                $isBullet   = $clean -match "^-\s+"
                $isNumbered = $clean -match "^\d+\."

                if ($inDid -and ($isNumbered -or $isBullet)) {
                    $WhatWeDid += $clean -replace "^(\d+\.\s*|-\s*\[.\]\s*|-\s*)", ""
                }
                if ($inBlock -and $isBullet) {
                    $Blockers += $clean -replace "^-\s*", ""
                }
                if ($inApproval -and ($isNumbered -or $isBullet)) {
                    $Approvals += $clean `
                        -replace "^(\d+\.\s*|-\s*\[.\]\s*|-\s*|\[.\]\s*)", "" `
                        -replace "^\*\*", "" -replace "\*\*$", "" -replace "\*\*", ""
                }
                if ($inNext -and ($isNumbered -or $isBullet)) {
                    $NextTasks += $clean -replace "^(\d+\.\s*|-\s*\[.\]\s*|-\s*)", ""
                }
            }
        }
    }

    $Did      = if ($WhatWeDid.Count -gt 0) { ($WhatWeDid | Select-Object -First 6 | ForEach-Object { "  - $_" }) -join "`n" } else { "  - No session log in last 24h." }
    $Blocking = if ($Blockers.Count -gt 0)  { ($Blockers  | Select-Object -Unique  | ForEach-Object { "  - $_" }) -join "`n" } else { "  - None." }
    $Approve  = if ($Approvals.Count -gt 0) { ($Approvals | Select-Object -Unique  | ForEach-Object { "  - [ ] $_" }) -join "`n" } else { "  - None." }
    $Next     = if ($NextTasks.Count -gt 0) { ($NextTasks | Select-Object -First 4  | ForEach-Object { "  - $_" }) -join "`n" } else { "  - Nothing queued." }

    $FallbackLine = if ($FallbackNote) { "`n  $FallbackNote`n" } else { "" }

    return @"
$ProjectLabel$FallbackLine
  $DidLabel
$Did

  $NextLabel
$Next

  BLOCKERS
$Blocking

  NEEDS YOUR OK
$Approve
"@
}

# ── 1. Get brief sections for each project ────────────────────────────────────
Write-Log "Reading JeffLocal session logs..."
$JeffLocalBrief = Get-ProjectBrief `
    -SessionsDir "C:\JeffLocal\docs\sessions" `
    -ProjectLabel "=== AVAMED / JEFFLOCAL ===" `
    -Mode $Mode

Write-Log "Reading SMCPHARMA session logs..."
$StMarksBrief = Get-ProjectBrief `
    -SessionsDir "C:\JeffLocal\SMCPHARMA\docs\sessions" `
    -ProjectLabel "=== ST MARKS PHARMACY (STMARKS-WEB) ===" `
    -Mode $Mode

# ── 2. Get git summaries ──────────────────────────────────────────────────────
Push-Location "C:\JeffLocal"
try   { $JLGit = (git log --oneline -3 2>&1) -join " | " } catch { $JLGit = "git error" }
Pop-Location

Push-Location "C:\JeffLocal\SMCPHARMA"
try   { $SMGit = (git log --oneline -3 2>&1) -join " | " } catch { $SMGit = "git error" }
Pop-Location

# ── 3. Get PROJECT_MEMORY pending items for JeffLocal ────────────────────────
$JLPending = ""
$MemFile = "C:\JeffLocal\PROJECT_MEMORY.md"
if (Test-Path $MemFile) {
    $MemContent = Get-Content $MemFile -Raw -Encoding UTF8
    $PendingLines = ($MemContent -split "`n") | Where-Object {
        $_ -match "(BLOCKED|Awaiting Saeed|PENDING|awaiting sign-off)" -and $_.Trim() -ne ""
    } | Select-Object -First 5
    if ($PendingLines) {
        $JLPending = "`n  (From PROJECT_MEMORY: " + ($PendingLines -join "; ") + ")"
    }
}

# ── 4. Assemble combined brief ────────────────────────────────────────────────
if ($Mode -eq 'Evening') {
    $Title = "EVENING BRIEF (session close)"
    $Clock = "19:00"
} else {
    $Title = "MORNING BRIEF"
    $Clock = "07:00"
}

$CombinedReport = @"
COMBINED $Title — $Today $Clock
Both projects — Avamed AI triage + St Marks Pharmacy website
================================================================

$JeffLocalBrief$JLPending

GIT (JeffLocal): $JLGit

----------------------------------------------------------------

$StMarksBrief

GIT (St Marks): $SMGit

================================================================
Detail: C:\JeffLocal\PROJECT_MEMORY.md | C:\JeffLocal\SMCPHARMA\CLAUDE.md
"@

# ── 5. Save the combined report ───────────────────────────────────────────────
$ReportsDir = "C:\JeffLocal\docs\reports"
if (-not (Test-Path $ReportsDir)) { New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null }
$Suffix      = if ($Mode -eq 'Evening') { "-evening" } else { "" }
$ReportPath  = "$ReportsDir\$Today$Suffix-combined.md"

if ($DryRun) {
    Write-Log "DryRun: would save combined report to $ReportPath"
    Write-Host $CombinedReport
} else {
    Set-Content -Path $ReportPath -Value $CombinedReport -Encoding UTF8
    Write-Log "Combined report saved: $ReportPath"
}

# ── 6. Run the JeffLocal script to update PROJECT_MEMORY + its git/push ──────
# We use -DryRun on the WhatsApp step only — JeffLocal's script still does
# PROJECT_MEMORY updates and git commit; we suppress only its separate send.
if (-not $DryRun) {
    Write-Log "Running JeffLocal strategy_daily.ps1 for PROJECT_MEMORY update..."
    try {
        & "C:\JeffLocal\scripts\daily\strategy_daily.ps1" -Mode $Mode -DryRun 2>&1 | ForEach-Object { Write-Log "  [JL] $_" }
    } catch {
        Write-Log "WARNING: JeffLocal strategy_daily.ps1 failed - $_"
    }
}

# ── 7. Send combined report via WhatsApp ─────────────────────────────────────
if ($DryRun) {
    Write-Log "DryRun: skipped WhatsApp send"
} else {
    $PythonScript = "C:\JeffLocal\scripts\daily\send_whatsapp.py"
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

Write-Log "combined_brief.ps1 complete - $Mode"

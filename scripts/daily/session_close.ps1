# session_close.ps1
# Avamed (JeffLocal) + St Marks Pharmacy - AUTOMATED SESSION CLOSE
#
# Runs every WEEKDAY at 18:30 via the scheduled task
# "JeffLocal - Weekday Session Close 1830", thirty minutes BEFORE the 19:00
# evening brief. Saeed's instruction, 2026-09-04.
#
# WHY THIS EXISTS AS ITS OWN SCRIPT
# Until now the close was buried inside combined_brief.ps1 sections 6 and 6b, so
# the 19:00 brief closed the session AND then described a close it had just
# performed on itself. Splitting them means the brief now reports on a close that
# already finished, which is the correct order, and a close failure is visible in
# that evening's message instead of being invisible.
#
# WHAT A CLOSE IS (all of it done by strategy_daily.ps1 -Mode Evening -NoSend):
#   - writes the session log to docs\sessions\YYYY-MM-DD-1800.md
#   - refreshes HANDOFF.md (only if no real session rewrote it by hand today)
#   - updates PROJECT_MEMORY.md
#   - git add -A, commit, push
#   - cuts the restore tag restore/YYYY-MM-DD-1800 and prunes to the newest 3
#   - refreshes the graphify code map (JeffLocal only)
# It runs unconditionally, whether or not any work happened that day. A day with
# no commits still gets a log saying exactly that.
#
# PUSH GUARD (kept, per Saeed 2026-09-04)
# -ProtectPath names a folder whose unfinished work must never leave this machine:
# "dashboard" for JeffLocal (production, live on port 8765) and "site" for St Marks
# (a push republishes the live pharmacy website via Cloudflare). If that folder has
# uncommitted work the close still COMMITS locally but HOLDS the push, and emits a
# PUSH-HELD signal line. Nothing is ever lost; it just does not go out unreviewed.
#
# HANDOFF TO THE 19:00 BRIEF
# Every run writes a marker file to logs\close-state\YYYY-MM-DD-close.txt holding a
# CLOSED line (or FAILED, if either project failed) plus any PUSH-HELD signals.
# combined_brief.ps1 reads that file in
# Evening mode instead of closing anything itself. logs\ is gitignored, so the
# marker never reaches the repo.
#
# WEEKENDS
# Saturday and Sunday are skipped by design (Saeed's choice, 2026-09-04). Weekend
# work is not stranded: the 07:00 morning brief still commits and pushes every day
# of the week. What a weekend does NOT get is a session log, a HANDOFF refresh or a
# restore tag - those wait until Monday 18:30. Use -Force to close on a weekend by
# hand.
#
# MANUAL USE
#   powershell -File scripts\daily\session_close.ps1            # close now (weekday)
#   powershell -File scripts\daily\session_close.ps1 -Force     # close now, any day
#   powershell -File scripts\daily\session_close.ps1 -DryRun    # show, change nothing
#
# NOTE: a hand-written close by a real session always beats this one. This is the
# safety net for days when nobody sits down. See docs\SHIPPING.md and CLAUDE.md
# "SESSION END PROTOCOL".
#
# Created: 2026-09-04

param(
    # Show what would happen and change nothing. No commit, no push, no tag.
    [switch]$DryRun,
    # Close even on a Saturday or Sunday.
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot   = "C:\JeffLocal"
$SmRepo     = Join-Path $RepoRoot "SMCPHARMA"
$CloseSrc   = Join-Path $RepoRoot "scripts\daily\strategy_daily.ps1"
$Today      = (Get-Date).ToString("yyyy-MM-dd")

# logs\ is gitignored - state and logs stay off the repo.
$LogDir     = Join-Path $RepoRoot "logs"
$StateDir   = Join-Path $LogDir  "close-state"
$LogFile    = Join-Path $LogDir  "session_close.log"
$StateFile  = Join-Path $StateDir "$Today-close.txt"

foreach ($d in @($LogDir, $StateDir)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

function Write-Log {
    param([string]$Message)
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss UTC")
    $entry = "[$ts] $Message"
    Write-Host $entry
    Add-Content -Path $LogFile -Value $entry -ErrorAction SilentlyContinue
}

Write-Log "=================================================================="
Write-Log "session_close.ps1 started - $Today$(if ($DryRun) { ' (DryRun)' })"

# ── Weekday gate ─────────────────────────────────────────────────────────────
$Day = (Get-Date).DayOfWeek
if (($Day -eq [DayOfWeek]::Saturday -or $Day -eq [DayOfWeek]::Sunday) -and -not $Force) {
    Write-Log "$Day - weekend, no close by design. Use -Force to override. Exiting."
    exit 0
}

# Collected PUSH-HELD signal lines from both projects, handed to the 19:00 brief.
$HeldSignals = @()

# Close failures. This list decides whether the marker says CLOSED or FAILED.
# Security Agent review 2026-09-04 caught the original version writing CLOSED
# unconditionally: both closes could throw, be logged as warnings, and the 19:00
# brief would still report a successful close that never happened - precisely the
# silent-failure pattern that hid the 11-19 Aug 2026 outage for eight days.
$Failures = @()

if (-not (Test-Path $CloseSrc)) {
    Write-Log "FATAL: close script not found at $CloseSrc - nothing was closed."
    exit 1
}

# ── 1. Avamed (JeffLocal) ────────────────────────────────────────────────────
# -NoSend: do the whole close but fire no WhatsApp message and do not forward back
# into combined_brief.ps1. The 19:00 brief owns the single daily message.
Write-Log "Closing Avamed (JeffLocal)..."
try {
    if ($DryRun) {
        Write-Log "  DryRun: would run strategy_daily.ps1 -Mode Evening -NoSend -ProtectPath dashboard -RefreshGraph"
    } else {
        $JLOutput = & $CloseSrc `
            -Mode Evening -NoSend -ProtectPath "dashboard" -RefreshGraph 2>&1 |
            ForEach-Object { Write-Log "  [JL] $_"; $_ }
        $HeldSignals += @(@($JLOutput) | ForEach-Object { [string]$_ } | Where-Object { $_ -like "PUSH-HELD|*" })
    }
    Write-Log "Avamed close finished."
} catch {
    Write-Log "WARNING: Avamed close FAILED - $_"
    $Failures += "Avamed|$_"
}

# ── 2. St Marks Pharmacy (SMCPHARMA) ─────────────────────────────────────────
# Its own git repo, its own remote, its own docs tree. Same script, repointed.
Write-Log "Closing St Marks Pharmacy (SMCPHARMA)..."
try {
    if (-not (Test-Path (Join-Path $SmRepo "PROJECT_MEMORY.md"))) {
        Write-Log "WARNING: SMCPHARMA not found at $SmRepo - its close was SKIPPED."
        $Failures += "St Marks|repository not found at $SmRepo"
    } elseif ($DryRun) {
        Write-Log "  DryRun: would run strategy_daily.ps1 -Mode Evening -NoSend -ProtectPath site (SMCPHARMA)"
    } else {
        $SMOutput = & $CloseSrc `
            -Mode Evening -NoSend `
            -ProjectName "St Marks Pharmacy Website (STMARKS-WEB)" `
            -RepoRoot    $SmRepo `
            -ReportsDir  (Join-Path $SmRepo "docs\reports") `
            -SessionsDir (Join-Path $SmRepo "docs\sessions") `
            -ProjectDocs (Join-Path $SmRepo "docs") `
            -MemoryFile  (Join-Path $SmRepo "PROJECT_MEMORY.md") `
            -ProtectPath "site" 2>&1 |
            ForEach-Object { Write-Log "  [SM] $_"; $_ }
        $HeldSignals += @(@($SMOutput) | ForEach-Object { [string]$_ } | Where-Object { $_ -like "PUSH-HELD|*" })
        Write-Log "St Marks close finished."
    }
} catch {
    Write-Log "WARNING: St Marks close FAILED - $_"
    $Failures += "St Marks|$_"
}

# ── 3. Marker file for the 19:00 brief ───────────────────────────────────────
# combined_brief.ps1 -Mode Evening reads this instead of closing anything itself.
#
# CLOSED is written ONLY when both closes succeeded. If either failed, the marker
# says FAILED plus one FAILED-DETAIL line per project, and the brief escalates it
# the same way it escalates a missing marker. A marker that always says CLOSED is
# worse than no marker at all - it launders a failure into a success.
# PUSH-HELD lines drive the separate push-guard banner.
if ($DryRun) {
    Write-Log "DryRun: would write marker $StateFile"
} else {
    if (@($Failures).Count -eq 0) {
        $MarkerLines = @("CLOSED|" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))
    } else {
        $MarkerLines = @("FAILED|" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))
        foreach ($f in @($Failures)) { $MarkerLines += "FAILED-DETAIL|$f" }
    }
    $MarkerLines += @($HeldSignals)
    Set-Content -Path $StateFile -Value $MarkerLines -Encoding UTF8
    Write-Log "Marker written: $StateFile ($(@($HeldSignals).Count) push-held signal(s))"

    # Keep the state folder from growing forever - 30 days is plenty for tracing.
    Get-ChildItem $StateDir -Filter "*-close.txt" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

if (@($HeldSignals).Count -gt 0) {
    Write-Log "PUSH HELD on $(@($HeldSignals).Count) project(s) - tonight's 19:00 brief will shout about it."
} else {
    Write-Log "Push guard: nothing held, both projects pushed normally."
}

if (@($Failures).Count -gt 0) {
    Write-Log "session_close.ps1 finished with $(@($Failures).Count) FAILURE(S) - marker says FAILED."
    # Non-zero on purpose: Task Scheduler records it, and the 06:45 health check's
    # "any scheduled job that failed its last run" test surfaces it next morning.
    exit 1
}

Write-Log "session_close.ps1 finished - both projects closed cleanly."
exit 0

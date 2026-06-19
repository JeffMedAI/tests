<#
.SYNOPSIS
    Replay items from the deadletter queue back into queue/incoming/ for reprocessing.

.DESCRIPTION
    Copies files from C:\JeffLocal\queue\deadletter\ into C:\JeffLocal\queue\incoming\
    with a .replay-YYYYMMDD suffix so the pipeline treats them as fresh intake.

    Originals are kept in deadletter\ as archive — nothing is deleted.

    Logs every action to C:\JeffLocal\logs\service_control\deadletter_replay.log

.PARAMETER DryRun
    Preview what would be replayed without copying any files.

.PARAMETER File
    Replay a single named file from the deadletter queue (filename only, no path).

.EXAMPLE
    .\replay_deadletter.ps1
    Replay all deadletter files.

.EXAMPLE
    .\replay_deadletter.ps1 -DryRun
    Show what would be replayed without touching anything.

.EXAMPLE
    .\replay_deadletter.ps1 -File "intake_20260601_143212.json"
    Replay a single file.
#>

param(
    [switch]$DryRun,
    [string]$File
)

$ErrorActionPreference = "Stop"

# ── Paths ─────────────────────────────────────────────────────────────────────
$DeadletterDir = "C:\JeffLocal\queue\deadletter"
$IncomingDir   = "C:\JeffLocal\queue\incoming"
$LogFile       = "C:\JeffLocal\logs\service_control\deadletter_replay.log"
$DateStamp     = (Get-Date -Format "yyyyMMdd")

# ── Logging helper ────────────────────────────────────────────────────────────
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Add-Content -LiteralPath $LogFile -Value $line
    Write-Host $line
}

# ── Ensure directories exist ──────────────────────────────────────────────────
foreach ($dir in @($DeadletterDir, $IncomingDir, (Split-Path $LogFile))) {
    if (-not (Test-Path -LiteralPath $dir)) {
        throw "Required directory not found: $dir"
    }
}

# ── Announce mode ─────────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Log "=== DRY RUN - no files will be copied ===" "INFO"
} else {
    Write-Log "=== Deadletter replay started ===" "INFO"
}

# ── Collect candidates ────────────────────────────────────────────────────────
$candidates = @()
if ($File) {
    $candidates = Get-ChildItem -LiteralPath $DeadletterDir -File |
                  Where-Object { $_.Name -eq $File }
    if (-not $candidates) {
        Write-Log "File not found in deadletter queue: $File" "ERROR"
        exit 1
    }
} else {
    $candidates = Get-ChildItem -LiteralPath $DeadletterDir -File
}

if (-not $candidates) {
    Write-Log "Deadletter queue is empty - nothing to replay." "INFO"
    exit 0
}

Write-Log "Found $($candidates.Count) file(s) to replay." "INFO"

# ── Replay each file ──────────────────────────────────────────────────────────
$replayed = 0
$skipped  = 0

foreach ($item in $candidates) {
    # Build replay filename: original stem + .replay-YYYYMMDD + original extension
    $stem        = [System.IO.Path]::GetFileNameWithoutExtension($item.Name)
    $ext         = [System.IO.Path]::GetExtension($item.Name)   # includes the dot
    $replayName  = "$stem.replay-$DateStamp$ext"
    $destination = Join-Path $IncomingDir $replayName

    if ($DryRun) {
        Write-Log "[DRY RUN] Would copy: $($item.Name) -> incoming\$replayName" "INFO"
        $replayed++
        continue
    }

    # Guard: do not overwrite if a replay copy already exists for today
    if (Test-Path -LiteralPath $destination) {
        Write-Log "Skipped (already replayed today): $replayName" "WARN"
        $skipped++
        continue
    }

    try {
        Copy-Item -LiteralPath $item.FullName -Destination $destination
        Write-Log "Replayed: $($item.Name) -> incoming\$replayName" "INFO"
        $replayed++
    } catch {
        Write-Log "FAILED to copy $($item.Name): $_" "ERROR"
        $skipped++
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Log "=== DRY RUN complete. Would replay $replayed file(s). ===" "INFO"
} else {
    Write-Log "=== Replay complete. Replayed: $replayed  Skipped: $skipped ===" "INFO"
}

<#
.SYNOPSIS
    Purge data files older than 90 days from queue/processed, outputs/handoff_json,
    and outputs/ollama_raw. Preserves .gitkeep files.
    Intended to run as a scheduled task or manually.
#>

param(
    [int]$RetentionDays = 90,
    [switch]$DryRun
)

$Root    = Split-Path -Parent $PSScriptRoot
$Cutoff  = (Get-Date).AddDays(-$RetentionDays)
$Targets = @(
    "$Root\queue\processed",
    "$Root\outputs\handoff_json",
    "$Root\outputs\ollama_raw"
)

$totalDeleted = 0
$totalBytes   = 0

foreach ($dir in $Targets) {
    if (-not (Test-Path $dir)) { continue }
    $files = Get-ChildItem -Path $dir -File -Recurse |
             Where-Object { $_.Name -ne '.gitkeep' -and $_.LastWriteTime -lt $Cutoff }
    foreach ($f in $files) {
        if ($DryRun) {
            Write-Host "[DRY RUN] Would delete: $($f.FullName)"
        } else {
            $totalBytes += $f.Length
            Remove-Item -Force $f.FullName -ErrorAction SilentlyContinue
            $totalDeleted++
        }
    }
}

if ($DryRun) {
    Write-Host "Dry run complete. $(($files | Measure-Object).Count) file(s) would be deleted."
} else {
    $kb = [math]::Round($totalBytes / 1KB, 1)
    Write-Host "Purge complete: $totalDeleted file(s) deleted ($kb KB freed, cutoff $($Cutoff.ToString('yyyy-MM-dd')))."
}

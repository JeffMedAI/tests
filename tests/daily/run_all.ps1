# Runs every test in this folder and prints one total.
#
# Written to run on WINDOWS POWERSHELL 5.1 as well as pwsh 7 - that is the whole
# point of it. Everything in this series has only ever been tested on pwsh 7 on
# Linux, and 5.1 is stricter: under Set-StrictMode -Version Latest it resolves to
# 3.0, where indexing past the end of an array is a TERMINATING error. With
# $ErrorActionPreference = "Stop" set at the top of the brief, a throw kills the
# whole run and Saeed gets no WhatsApp message at all. That has happened before.
#
#   Windows:  powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\daily\run_all.ps1
#   Linux:    pwsh -NoProfile -File ./tests/daily/run_all.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Here = $PSScriptRoot
Write-Host ""
# $PSVersionTable has NO 'Platform' key on Windows PowerShell 5.1 - it was added
# in 6.0. Reading it blind is precisely the 5.1-only fault this runner exists to
# catch, so it is read defensively. Checked with ContainsKey, not assumed.
$Plat = if ($PSVersionTable.ContainsKey('Platform')) { $PSVersionTable['Platform'] } else { 'Win32NT (Windows PowerShell)' }
Write-Host "PowerShell $($PSVersionTable.PSVersion) on $Plat"
Write-Host "Tests in $Here"
Write-Host ("-" * 60)

$Files = @(Get-ChildItem -Path $Here -Filter "t_*.ps1" -File | Sort-Object Name)
if (@($Files).Count -eq 0) { Write-Host "No tests found."; exit 1 }

$TotalPass = 0; $TotalFail = 0; $Broken = @()
foreach ($f in $Files) {
    Write-Host ""
    Write-Host "== $($f.Name)"
    # Re-invoke THIS same PowerShell for each file, so a test that dies takes
    # its own process down and not the runner. (Get-Process -Id $PID).Path is
    # the running host's own exe - powershell.exe on 5.1, pwsh on 7.
    $exe = (Get-Process -Id $PID).Path
    $out = $null
    try {
        $out  = & $exe -NoProfile -File $f.FullName 2>&1
        $exit = $LASTEXITCODE
    } catch {
        $out  = "$_"
        $exit = 1
    }
    $summary = @($out | Where-Object { "$_" -match '^PASS: \d+\s+FAIL: \d+$' } | Select-Object -Last 1)
    if (@($summary).Count -eq 1 -and "$($summary[0])" -match '^PASS: (\d+)\s+FAIL: (\d+)$') {
        $p = [int]$Matches[1]; $fl = [int]$Matches[2]
        $TotalPass += $p; $TotalFail += $fl
        Write-Host "   $p passed, $fl failed"
        if ($fl -gt 0) { @($out | Where-Object { "$_" -match '^\s+FAIL ' }) | ForEach-Object { Write-Host "   $_" } }
    } else {
        # No summary line means the test file itself died - on 5.1 that is the
        # interesting case, so print everything rather than swallowing it.
        $Broken += $f.Name
        Write-Host "   DID NOT COMPLETE (exit $exit) - full output follows:"
        @($out) | ForEach-Object { Write-Host "   | $_" }
    }
}

Write-Host ""
Write-Host ("=" * 60)
Write-Host "TOTAL: $TotalPass passed, $TotalFail failed"
if (@($Broken).Count -gt 0) { Write-Host "DID NOT COMPLETE: $((@($Broken)) -join ', ')" }
Write-Host ("=" * 60)
if ($TotalFail -gt 0 -or @($Broken).Count -gt 0) { exit 1 }

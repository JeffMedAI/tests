# Tests for the 2026-09-11 brief fixes (tick / contradiction / day's work).
# Functions are pulled OUT OF THE LIVE FILE every run - never a copy. A stale
# copy is exactly how an earlier test in this series passed against dead code.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DefaultScript = Join-Path $RepoRoot "scripts/daily/combined_brief.ps1"

$Script = $DefaultScript
$Src = Get-Content -Path $Script -Raw

$Pass = 0; $Fail = 0
function Assert-Eq { param($Got,$Want,$Name)
    if ("$Got" -eq "$Want") { $script:Pass++; Write-Host "  ok   $Name" }
    else { $script:Fail++; Write-Host "  FAIL $Name`n         got : $Got`n         want: $Want" }
}
function Assert-True { param($Cond,$Name) Assert-Eq ([bool]$Cond) $true $Name }
function Assert-False { param($Cond,$Name) Assert-Eq ([bool]$Cond) $false $Name }

# ── currency guard ───────────────────────────────────────────────────────────
foreach ($fn in @("Test-IsAutoWrittenLog","Test-IsNoneLine","Remove-NoneLines","Test-IsDoneLine")) {
    if ($Src -notmatch "(?m)^function\s+$fn\s*\{") { throw "GUARD: $fn is not in the live script - tests would prove nothing" }
}
# Extract each function body and define it here.
foreach ($fn in @("Test-IsAutoWrittenLog","Test-IsNoneLine","Remove-NoneLines","Test-IsDoneLine")) {
    $m = [regex]::Match($Src, "(?ms)^function\s+$fn\s*\{.*?^\}")
    if (-not $m.Success) { throw "GUARD: could not extract $fn" }
    Invoke-Expression $m.Value
}
Write-Host "Loaded 4 function(s) from the live script."

# ── Fix 1: ticked items are done ─────────────────────────────────────────────
Write-Host "`nFIX 1 - a ticked box is done, not an open approval"
Assert-True  (Test-IsDoneLine "- [x] Alarm system done. Saeed approved.") "lowercase [x] is done"
Assert-True  (Test-IsDoneLine "- [X] Alarm system done.")                 "uppercase [X] is done"
Assert-True  (Test-IsDoneLine "  - [x] indented tick")                    "indented tick is done"
Assert-True  (Test-IsDoneLine "[x] no dash")                              "tick with no dash is done"
Assert-True  (Test-IsDoneLine "1. [x] numbered tick")                     "numbered tick is done"
Assert-False (Test-IsDoneLine "- [ ] Create staff accounts")              "empty box is NOT done"
Assert-False (Test-IsDoneLine "- Create staff accounts")                  "plain line is NOT done"
Assert-False (Test-IsDoneLine "- Fix the [x] rendering bug")              "[x] mid-line is NOT done"
Assert-False (Test-IsDoneLine "")                                          "empty string is NOT done"

# ── Fix 2: a bare None next to real items ────────────────────────────────────
Write-Host "`nFIX 2 - bare 'none' lines go, real blockers stay"
Assert-True  (Test-IsNoneLine "None")                       "None"
Assert-True  (Test-IsNoneLine "none.")                      "none."
Assert-True  (Test-IsNoneLine "Nothing stuck right now")    "Nothing stuck right now"
Assert-True  (Test-IsNoneLine "No blockers")                "No blockers"
Assert-True  (Test-IsNoneLine "Unblocked")                  "Unblocked"
Assert-True  (Test-IsNoneLine "N/A")                        "N/A"
Assert-True  (Test-IsNoneLine "Nothing pending today.")     "Nothing pending today."
# The dangerous direction: real blockers that merely START with a negative.
Assert-False (Test-IsNoneLine "No GPhC number yet")                        "real blocker: No GPhC number yet"
Assert-False (Test-IsNoneLine "No pharmacist sign-off")                    "real blocker: No pharmacist sign-off"
Assert-False (Test-IsNoneLine "Nothing can ship until the ACLs are fixed") "real blocker beginning 'Nothing'"
Assert-False (Test-IsNoneLine "None of the governance gates are signed")   "real blocker beginning 'None'"
Assert-False (Test-IsNoneLine "No staff accounts exist yet")               "real blocker: No staff accounts"

$mixed = @("None", "Three security items outstanding since 11 August", "Nothing stuck right now")
$keptRaw = Remove-NoneLines -Lines $mixed
$kept    = @($keptRaw)
Assert-Eq @($kept).Count 1 "mixed section keeps only the real blocker"
Assert-Eq @($kept)[0] "Three security items outstanding since 11 August" "the survivor is the real one"

$allNone = @("None", "Nothing stuck")
$kept2Raw = Remove-NoneLines -Lines $allNone
$kept2    = @($kept2Raw)
Assert-Eq @($kept2).Count 0 "an all-none section empties, so the standard placeholder renders"

$noneAtAll = @("Real blocker one", "Real blocker two")
$keep3 = Remove-NoneLines -Lines $noneAtAll
Assert-Eq @($keep3).Count 2 "a section with no none-lines is untouched"
$keep4 = Remove-NoneLines -Lines @()
Assert-Eq @($keep4).Count 0 "empty input survives"

# ── Fix 3: which logs were machine-written ───────────────────────────────────
Write-Host "`nFIX 3 - automation's own logs are recognised"
$auto = @"
# SESSION SUMMARY - [2026-09-10 18:00]
# Tool: strategy_daily.ps1 (automated session close at 18:30)
# Built from the day's actual git activity - 7 commit(s).

## WHAT WE DID
- Stopped the close when the file list cannot be read.
"@
Assert-True (Test-IsAutoWrittenLog -Content $auto) "strategy_daily header detected"

$auto2 = $auto -replace "strategy_daily", "session_close"
Assert-True (Test-IsAutoWrittenLog -Content $auto2) "session_close header detected"

$human = @"
# SESSION SUMMARY - [2026-09-11 14:00]
# Written by hand.

## WHAT WE DID
- Talked through the brief with Saeed. He said it reads too long.
- Note: strategy_daily.ps1 is the tool that writes the automated log.
"@
Assert-False (Test-IsAutoWrittenLog -Content $human) "a human log that MENTIONS the tool is not auto"
Assert-False (Test-IsAutoWrittenLog -Content "")     "empty content is not auto"

$late = ("# padding`n" * 12) + "# Tool: strategy_daily.ps1`n"
Assert-False (Test-IsAutoWrittenLog -Content $late) "a Tool: line below the header block does not count"

Write-Host "`n================================"
Write-Host "PASS: $Pass   FAIL: $Fail"
if ($Fail -gt 0) { exit 1 }

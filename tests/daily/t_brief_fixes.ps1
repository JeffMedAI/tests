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
foreach ($fn in @("Test-IsNoneLine","Remove-NoneLines","Test-IsDoneLine")) {
    if ($Src -notmatch "(?m)^function\s+$fn\s*\{") { throw "GUARD: $fn is not in the live script - tests would prove nothing" }
}
# Extract each function body and define it here.
foreach ($fn in @("Test-IsNoneLine","Remove-NoneLines","Test-IsDoneLine")) {
    $m = [regex]::Match($Src, "(?ms)^function\s+$fn\s*\{.*?^\}")
    if (-not $m.Success) { throw "GUARD: could not extract $fn" }
    Invoke-Expression $m.Value
}
Write-Host "Loaded 3 function(s) from the live script."

# ── Fix 1: ticked items are done ─────────────────────────────────────────────
Write-Host "`nFIX 1 - a ticked box is done, not an open approval"
Assert-True  (Test-IsDoneLine "- [x] Alarm system done. Saeed approved.") "lowercase [x] is done"
Assert-True  (Test-IsDoneLine "- [X] Alarm system done.")                 "uppercase [X] is done"
Assert-True  (Test-IsDoneLine "  - [x] indented tick")                    "indented tick is done"
Assert-True  (Test-IsDoneLine "[x] no dash")                              "tick with no dash is done"
Assert-True  (Test-IsDoneLine "1. [x] numbered tick")                     "numbered tick is done"
Assert-True  (Test-IsDoneLine "* [x] asterisk bullet")                    "asterisk bullet tick is done"
Assert-True  (Test-IsDoneLine "+ [x] plus bullet")                        "plus bullet tick is done"
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


# -- Option A: the close stores the plain git record, tidied without a model ---
$DailySrc = Get-Content -Path (Join-Path $RepoRoot "scripts/daily/strategy_daily.ps1") -Raw
if ($DailySrc -notmatch "(?m)^function\s+Format-CommitSubject\s*\{") { throw "GUARD: Format-CommitSubject is not in strategy_daily.ps1" }
$fm = [regex]::Match($DailySrc, "(?ms)^function\s+Format-CommitSubject\s*\{.*?^\}")
Invoke-Expression $fm.Value

# The close must NOT rewrite what it stores - that is the whole of Option A.
# Assert on the CODE between $DidLines and $DidSection, ignoring comments, so
# the guard cannot be satisfied by a comment that merely mentions the rewriter.
$wm = [regex]::Match($DailySrc, '(?ms)^\s*\$DidLines\s*=.*?^\s*\$DidSection\s*=')
Assert-True ($wm.Success) "found the session-log writer's WHAT WE DID block"
$writerCode = (@($wm.Value -split "`n") | Where-Object { $_ -notmatch '^\s*#' }) -join "`n"
Assert-True ($writerCode -notmatch 'Get-BusinessRewrite') "the session-log writer does NOT call the rewriter"
Assert-True ($writerCode -match 'Format-CommitSubject')   "the session-log writer tidies deterministically instead"

Write-Host "`nOPTION A - commit subjects tidied deterministically, no model"
Assert-Eq (Format-CommitSubject "fix(close): refuse when the incoming-file list cannot be parsed reliably") "Refuse when the incoming-file list cannot be parsed reliably." "conventional prefix with scope stripped"
Assert-Eq (Format-CommitSubject "feat: back up unconditionally") "Back up unconditionally." "conventional prefix without scope"
Assert-Eq (Format-CommitSubject "docs(brief)!: breaking change") "Breaking change." "breaking-change marker stripped"
Assert-Eq (Format-CommitSubject "Merge branch 'main' of https://github.com/x") "Merge branch 'main' of https://github.com/x." "a normal sentence is left alone"
Assert-Eq (Format-CommitSubject "Fixed the thing.") "Fixed the thing." "already a sentence - unchanged"
Assert-Eq (Format-CommitSubject "does it work?") "Does it work?" "existing terminator kept"
Assert-Eq (Format-CommitSubject "  fix: trailing space  ") "Trailing space." "trimmed"
Assert-Eq (Format-CommitSubject "") "" "empty stays empty"
Assert-Eq (Format-CommitSubject "fix:") "fix:" "a prefix with nothing after it is not swallowed"

Write-Host "`n================================"
Write-Host "PASS: $Pass   FAIL: $Fail"
if ($Fail -gt 0) { exit 1 }

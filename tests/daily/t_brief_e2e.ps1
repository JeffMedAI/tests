# End-to-end: build a real session-log folder, run the REAL Get-ProjectBrief,
# and read the section it produces. Ollama is not running here, so this also
# exercises the word-glossary fallback path (no AI rewrite).
param([string]$ScriptPath)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DefaultScript = Join-Path $RepoRoot "scripts/daily/combined_brief.ps1"
if (-not $ScriptPath) { $ScriptPath = $DefaultScript }
$Script = $ScriptPath
$Src = Get-Content -Path $Script -Raw

$Pass = 0; $Fail = 0
function Assert-Match { param($Text,$Pattern,$Name)
  if ($Text -match $Pattern) { $script:Pass++; Write-Host "  ok   $Name" }
  else { $script:Fail++; Write-Host "  FAIL $Name (pattern: $Pattern)" } }
function Assert-NotMatch { param($Text,$Pattern,$Name)
  if ($Text -notmatch $Pattern) { $script:Pass++; Write-Host "  ok   $Name" }
  else { $script:Fail++; Write-Host "  FAIL $Name - should NOT contain: $Pattern" } }

$Needed = @("Get-Utf8FileText","Add-PlainEnglishNotes","Select-NearUnique","Get-BusinessRewrite",
            "Test-IsPlaceholderLog","Test-IsAutoWrittenLog","Test-IsNoneLine","Remove-NoneLines",
            "Test-IsDoneLine","Get-LastExpectedCloseTime","Get-ProjectBrief")
foreach ($fn in $Needed) {
  $m = [regex]::Match($Src, "(?ms)^function\s+$fn\s*\{.*?^\}")
  if (-not $m.Success) { throw "GUARD: could not extract $fn from the live script" }
  Invoke-Expression $m.Value
}
function Write-Log { param([string]$Message) }   # silence the C:\ log path
Write-Host "Loaded $($Needed.Count) function(s) from the live script.`n"

$Root = Join-Path ([System.IO.Path]::GetTempPath()) ("brieftest-" + [guid]::NewGuid().ToString("N"))
$Sessions = Join-Path $Root "docs/sessions"
New-Item -ItemType Directory -Path $Sessions -Force | Out-Null
$Stamp = (Get-Date).ToString("yyyy-MM-dd") + "-1800"
@"
# SESSION SUMMARY - [$(Get-Date -Format 'yyyy-MM-dd') 18:00]
# Tool: strategy_daily.ps1 (automated session close at 18:30)
# Built from the day's actual git activity - 7 commit(s).

---

## WHAT WE DID

- Stopped the close when the incoming file list cannot be read.
- Files changed today: 4 (CHANGELOG.md, combined_brief.ps1)

---

## BLOCKERS

- None
- Three security items outstanding since 11 August.

---

## PENDING SAEED APPROVALS

- [x] Alarm system finished, Saeed approved, security review passed.
- [ ] Create staff accounts with names, roles and emails.
- [ ] Sign governance gates 1-7.
- [ ] Agree the HMAC secret before live data flows.
- [ ] Close the three security items.
- [ ] NHS SBS and DSPT both overdue.

---

## WHAT TO DO NEXT SESSION

- Review the 07:00 brief.
- Start on the security items.

---

## GIT STATE

Latest commit: abc1234
Branch: main
"@ | Set-Content -Path (Join-Path $Sessions "$Stamp.md") -Encoding UTF8

$B = Get-ProjectBrief -SessionsDir $Sessions -ProjectLabel "=== TEST PROJECT ===" -Mode "Evening"
$T = $B.Text
Write-Host "----- RENDERED SECTION -----"
Write-Host $T
Write-Host "----------------------------`n"

Write-Host "FIX 1 - the ticked item does not come back as an approval"
Assert-NotMatch $T "Alarm system finished"         "already-approved item is gone"
Assert-Match    $T "\[ \] Create staff accounts"   "genuinely open approval still shown"

Write-Host "`nFIX 2 - no self-contradiction under WHAT'S STUCK"
Assert-Match    $T "Three security items"          "the real blocker is shown"
Assert-NotMatch $T "(?m)^\s*-\s*None\s*$"          "the bare 'None' line is gone"

Write-Host "`nFIX 3 - the automation's line is passed through, not re-worded"
Assert-Match    $T "Stopped the close when the incoming file list cannot be read\." "auto line is verbatim"

Write-Host "`nFIX 5 - capped, with an honest overflow marker"
Assert-Match    $T "\(\+1 more - ask me\)"         "6 approvals minus 1 ticked = 5, cap 4, +1 flagged"
Assert-NotMatch $T "\[ \] \(\+"                    "the overflow marker gets no checkbox"

Remove-Item -Recurse -Force $Root
Write-Host "`n================================"
Write-Host "PASS: $Pass   FAIL: $Fail"
if ($Fail -gt 0) { exit 1 }

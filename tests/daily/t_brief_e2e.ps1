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

$Needed = @("Get-Utf8FileText","Add-PlainEnglishNotes","Select-NearUnique","Protect-BriefLines","Get-BusinessRewrite",
            "Test-IsPlaceholderLog","Test-IsNoneLine","Remove-NoneLines",
            "Test-IsDoneLine","Get-LastExpectedCloseTime","Get-ProjectBrief")
foreach ($fn in $Needed) {
  $m = [regex]::Match($Src, "(?ms)^function\s+$fn\s*\{.*?^\}")
  if (-not $m.Success) { throw "GUARD: could not extract $fn from the live script" }
  Invoke-Expression $m.Value
}
function Write-Log { param([string]$Message) }   # silence the C:\ log path
# Replace the model with a deterministic stand-in that visibly marks every line
# it touches. The test used to assume Ollama was down, so it failed on any
# machine where Ollama is running (it reworded "incoming-file list"). The
# marker also proves which sections are rewritten and which go out verbatim.
function Get-BusinessRewrite { param([string[]]$Lines, [string]$Kind = 'Done')
  if (-not $Lines -or $Lines.Count -eq 0) { return ,$Lines }
  return ,@($Lines | ForEach-Object { "REWRITTEN $_" }) }
Write-Host "Loaded $($Needed.Count) function(s) from the live script.`n"

$Root = Join-Path ([System.IO.Path]::GetTempPath()) ("brieftest-" + [guid]::NewGuid().ToString("N"))
$Sessions = Join-Path $Root "docs/sessions"
New-Item -ItemType Directory -Path $Sessions -Force | Out-Null
$Stamp = (Get-Date).ToString("yyyy-MM-dd") + "-1800"
@"
# SESSION SUMMARY - [$(Get-Date -Format 'yyyy-MM-dd') 18:00]
# Tool: strategy_daily.ps1 (automated session close at 18:30)
#   WHAT WE DID below is the plain git record.
# Built from the day's actual git activity - 7 commit(s).

---

## WHAT WE DID

- Refuse when the incoming-file list cannot be parsed reliably.
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

Write-Host "`nOPTION A - the stored record is the plain git line"
Assert-Match    $T "incoming-file list"                "the day's work reaches Saeed"
Assert-NotMatch $T "must be refused"                   "no policy-speak: the log stores the record, not a paraphrase"

Write-Host "`nH1 - ALARM SECTIONS ARE NEVER CAPPED (Security Agent, 2026-09-11)"
# The first version of Fix 5 capped approvals at 4 and blockers at 3. That
# selects by log order, not severity, so a real security blocker could become
# the integer in "(+3 more)". All five open approvals must be present.
Assert-Match    $T "\[ \] Create staff accounts"     "approval 1 of 5 present"
Assert-Match    $T "Sign governance gates"           "approval 2 of 5 present"
Assert-Match    $T "HMAC"                            "approval 3 of 5 present"
Assert-Match    $T "three security items"            "approval 4 of 5 present"
Assert-Match    $T "NHS SBS and DSPT"                "approval 5 of 5 present"
Assert-NotMatch $T "\(\+\d+ more - ask me\)"        "no overflow marker - nothing was hidden"
Assert-NotMatch $T "\[ \] \(\+"                     "the overflow marker never gets a checkbox"

Write-Host "`n2026-09-14 - APPROVALS AND BLOCKERS ARE NEVER REWRITTEN"
# The rewrite turned open to-dos into finished work ("were created",
# "was obtained"). These two sections must reach Saeed word for word.
Assert-Match    $T "(?m)^\s*- \[ \] Create staff accounts with names, roles and emails\.\s*$" "approval is verbatim"
Assert-Match    $T "(?m)^\s*- Three security items outstanding since 11 August\.\s*$"      "blocker is verbatim"
Assert-NotMatch $T "\[ \] REWRITTEN"                  "no approval went through the rewrite"
Assert-Match    $T "REWRITTEN Review the 07:00 brief" "WHAT'S NEXT still gets the plain-English rewrite"

Write-Host "`n2026-09-14 - STORED FILES HOLD ORIGINAL WORDS (no rewrite feedback loop)"
$Daily = Get-Content -Path (Join-Path $RepoRoot "scripts/daily/strategy_daily.ps1") -Raw -Encoding UTF8
Assert-Match    $Daily '## NEXT \+ BLOCKERS\s+\$NextSectionRecord'           "HANDOFF.md stores the record, not the rewrite"
Assert-NotMatch $Daily '## WHAT TO DO NEXT SESSION\s+\$NextSection\s'        "session logs store the record, not the rewrite"
Assert-NotMatch $Daily '\$(Blockers|Approvals)AI\s*=\s*Get-BusinessRewrite' "strategy_daily never rewrites blockers/approvals"
Assert-NotMatch $Src   '\$(Blockers|Approvals)AI\s*=\s*Get-BusinessRewrite' "combined_brief never rewrites blockers/approvals"

Write-Host "`nSECURITY CONDITION 2026-09-14 - sensitive values are masked, lines are kept"
$Masked = Protect-BriefLines -Lines @(
  "Rotate HMAC secret=abc123XYZ before go-live.",
  "Leaked hash 0123456789abcdef0123456789abcdef found.",
  "Test patient 943 476 5919 still in queue.",
  "See C:\JeffLocal\config\secrets.json for detail.",
  "Create staff accounts with names, roles and emails.")
Assert-NotMatch ($Masked -join "`n") "abc123XYZ"              "secret value hidden"
Assert-NotMatch ($Masked -join "`n") "0123456789abcdef"       "long hex hidden"
Assert-NotMatch ($Masked -join "`n") "943 476 5919"           "NHS-number pattern hidden"
Assert-NotMatch ($Masked -join "`n") "secrets\.json"          "file path hidden"
Assert-Match    ($Masked -join "`n") "Rotate HMAC secret=\[hidden\] before go-live" "alarm line survives, only the value masked"
Assert-Match    ($Masked -join "`n") "(?m)^Create staff accounts with names, roles and emails\.$" "ordinary line untouched"
Assert-Match    @($Masked).Count "^5$"                       "no line dropped"

Write-Host "`nSECURITY L5 - the REAL prompt still carries the tense rule (the stub cannot hide a regression)"
Assert-Match $Src 'Every line is work that has NOT happened yet'  "Planned wording present in live prompt"
Assert-Match $Src 'Get-BusinessRewrite -Lines \$NextTasksCapped -Kind Planned' "WHAT'S NEXT called with -Kind Planned"
Assert-Match $Src 'Get-BusinessRewrite -Lines \$WhatWeDidCapped -Kind Done'    "WHAT WE DID called with -Kind Done"
Assert-Match $Src 'Protect-BriefLines -Lines \$ApprovalsFinal'   "approvals are masked before sending"
Assert-Match $Daily 'Protect-BriefLines -Lines \$NextTasksCapped' "stored WHAT'S NEXT record is masked"

Remove-Item -Recurse -Force $Root
Write-Host "`n================================"
Write-Host "PASS: $Pass   FAIL: $Fail"
if ($Fail -gt 0) { exit 1 }

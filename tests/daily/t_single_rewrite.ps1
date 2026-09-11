# Option A (Saeed's decision, 2026-09-11): there is exactly ONE plain-English
# rewrite in the whole pipeline, and it happens at send time.
#
# The close stores the plain git record - guarded statically in t_brief_fixes.ps1.
# This file guards the other half: every WHAT WE DID line reaching Saeed has been
# through the rewriter exactly ONCE - not twice (the 2026-09-10 fault, where two
# passes of a small model turned a commit subject into a policy statement), and
# not zero times (which would send him raw developer wording).
#
# A plain end-to-end test cannot prove this: Ollama is down in this container, so
# the rewritten and un-rewritten paths render identically. Hence a spy.
param([string]$ScriptPath)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DefaultScript = Join-Path $RepoRoot "scripts/daily/combined_brief.ps1"
if (-not $ScriptPath) { $ScriptPath = $DefaultScript }
$Src = Get-Content -Path $ScriptPath -Raw

$Pass = 0; $Fail = 0
function Assert-True { param($Cond,$Name)
  if ($Cond) { $script:Pass++; Write-Host "  ok   $Name" } else { $script:Fail++; Write-Host "  FAIL $Name" } }

$Needed = @("Get-Utf8FileText","Add-PlainEnglishNotes","Select-NearUnique","Get-BusinessRewrite",
            "Test-IsPlaceholderLog","Test-IsNoneLine","Remove-NoneLines",
            "Test-IsDoneLine","Get-LastExpectedCloseTime","Get-ProjectBrief")
foreach ($fn in $Needed) {
  $m = [regex]::Match($Src, "(?ms)^function\s+$fn\s*\{.*?^\}")
  if (-not $m.Success) { throw "GUARD: could not extract $fn" }
  Invoke-Expression $m.Value
}
function Write-Log { param([string]$Message) }

# The spy. Records every line it is handed, and marks its output so anything
# that went through it is visible in the rendered text.
$global:SpySaw = New-Object System.Collections.ArrayList
function Get-BusinessRewrite {
    param([string[]]$Lines, [string]$OllamaUrl, [string]$Model, [int]$TimeoutSec)
    foreach ($l in @($Lines)) { [void]$global:SpySaw.Add([string]$l) }
    if (-not $Lines -or @($Lines).Count -eq 0) { return ,@($Lines) }
    return ,@(@($Lines) | ForEach-Object { "REWRITTEN::$_" })
}

$Root = Join-Path ([System.IO.Path]::GetTempPath()) ("fix3-" + [guid]::NewGuid().ToString("N"))
$Sessions = Join-Path $Root "docs/sessions"
New-Item -ItemType Directory -Path $Sessions -Force | Out-Null
$Day = (Get-Date).ToString("yyyy-MM-dd")

@"
# SESSION SUMMARY - [$Day 18:00]
# Tool: strategy_daily.ps1 (automated session close at 18:30)
#   WHAT WE DID below is the plain git record.

## WHAT WE DID

- AUTOLINE refuse when the incoming-file list cannot be parsed reliably.
"@ | Set-Content -Path (Join-Path $Sessions "$Day-1800.md") -Encoding UTF8

@"
# SESSION SUMMARY - [$Day 14:00]
# Written by hand.

## WHAT WE DID

- HUMANLINE talked the brief through with Saeed.
"@ | Set-Content -Path (Join-Path $Sessions "$Day-1400.md") -Encoding UTF8

$B = Get-ProjectBrief -SessionsDir $Sessions -ProjectLabel "=== TEST ===" -Mode "Evening"
$T = $B.Text
Write-Host "----- RENDERED -----"; Write-Host $T; Write-Host "--------------------`n"
$Saw = @($global:SpySaw)
Write-Host "The rewriter was handed $(@($Saw).Count) line(s):"
$Saw | ForEach-Object { Write-Host "   | $_" }

Write-Host "`nOPTION A - every line is rewritten exactly once"
$autoSaw  = @(@($Saw) | Where-Object { $_ -like "*AUTOLINE*" })
$humanSaw = @(@($Saw) | Where-Object { $_ -like "*HUMANLINE*" })
Assert-True (@($autoSaw).Count  -eq 1) "the machine-written line went to the rewriter exactly once"
Assert-True (@($humanSaw).Count -eq 1) "the human-written line went to the rewriter exactly once"

Write-Host "`nNo double rewrite - the 2026-09-10 fault"
# A line already carrying the marker would mean it had been through twice.
Assert-True (-not (@($Saw) | Where-Object { $_ -like "REWRITTEN::*" })) "the rewriter was never handed its own output"
Assert-True ($T -notmatch "REWRITTEN::REWRITTEN::")                     "no line was rewritten twice"

Write-Host "`nAnd nothing is sent raw"
Assert-True ($T -match "REWRITTEN::.*AUTOLINE")  "the machine-written line reached Saeed rewritten"
Assert-True ($T -match "REWRITTEN::.*HUMANLINE") "the human-written line reached Saeed rewritten"

Remove-Item -Recurse -Force $Root
Write-Host "`n================================"
Write-Host "PASS: $Pass   FAIL: $Fail"
if ($Fail -gt 0) { exit 1 }

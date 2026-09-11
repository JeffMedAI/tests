# Fix 3 proper: prove the automation's own lines NEVER reach the rewriter.
# The e2e test could not prove this - Ollama is down in this container, so the
# rewritten and un-rewritten paths look identical. This replaces Get-Business-
# Rewrite with a spy that records what it was asked to rewrite.
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
            "Test-IsPlaceholderLog","Test-IsAutoWrittenLog","Test-IsNoneLine","Remove-NoneLines",
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

## WHAT WE DID

- AUTOLINE stopped the close when the file list cannot be read.
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

Write-Host "`nFIX 3 - the automation's line bypasses the rewriter"
Assert-True (-not (@($Saw) | Where-Object { $_ -like "*AUTOLINE*" })) "rewriter NEVER saw the automated line"
Assert-True ($T -match "AUTOLINE")                                     "automated line still reaches Saeed"
Assert-True ($T -notmatch "REWRITTEN::AUTOLINE")                       "automated line was not re-worded"

Write-Host "`nControl - a human line IS still rewritten"
Assert-True (@($Saw) | Where-Object { $_ -like "*HUMANLINE*" })        "rewriter DID see the human line"
Assert-True ($T -match "REWRITTEN::.*HUMANLINE")                       "human line went through the rewriter"

Remove-Item -Recurse -Force $Root
Write-Host "`n================================"
Write-Host "PASS: $Pass   FAIL: $Fail"
if ($Fail -gt 0) { exit 1 }

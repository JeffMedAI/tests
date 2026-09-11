# Tests the WhatsApp copy retention/purge. This block DELETES FILES, so it is
# tested against a scratch folder seeded with decoys it must not touch.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DefaultScript = Join-Path $RepoRoot "scripts/daily/combined_brief.ps1"
$Script = $DefaultScript
$Src = Get-Content -Path $Script -Raw

$Pass = 0; $Fail = 0
function Assert-Eq { param($Got,$Want,$Name)
  if ("$Got" -eq "$Want") { $script:Pass++; Write-Host "  ok   $Name" }
  else { $script:Fail++; Write-Host "  FAIL $Name`n         got : $Got`n         want: $Want" } }

# Pull the purge block out of the LIVE script - never a copy.
$m = [regex]::Match($Src, '(?ms)^# .. 9\. Purge old WhatsApp copies.*?(?=^Write-Log "combined_brief\.ps1 complete)')
if (-not $m.Success) { throw "GUARD: could not find the purge block in the live script" }
$PurgeBlock = $m.Value
function Write-Log { param([string]$Message) }

$Root = Join-Path ([System.IO.Path]::GetTempPath()) ("waptest-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $Root -Force | Out-Null

# 6 copies, oldest first, plus decoys the purge must leave alone.
for ($i = 1; $i -le 6; $i++) {
    $f = Join-Path $Root ("2026-09-0{0}-1900-Evening-whatsapp.txt" -f $i)
    Set-Content -Path $f -Value "message $i" -Encoding UTF8
    (Get-Item $f).LastWriteTime = (Get-Date).AddDays(-10 + $i)
}
Set-Content -Path (Join-Path $Root "IMPORTANT-notes.md") -Value "do not delete" -Encoding UTF8
Set-Content -Path (Join-Path $Root "whatsapp.txt")       -Value "do not delete" -Encoding UTF8
New-Item -ItemType Directory -Path (Join-Path $Root "subfolder") -Force | Out-Null
Set-Content -Path (Join-Path $Root "subfolder/2026-01-01-0700-Morning-whatsapp.txt") -Value "nested" -Encoding UTF8

$WhatsAppLogDir     = $Root
$KeepWhatsAppLogs   = 3
$WhatsAppLogPattern = "*-whatsapp.txt"

Write-Host "DryRun must delete nothing"
$DryRun = $true
Invoke-Expression $PurgeBlock
Assert-Eq (@(Get-ChildItem -Path $Root -Filter "*-whatsapp.txt" -File)).Count 6 "DryRun left all 6 copies"

Write-Host "`nReal run keeps the newest 3"
$DryRun = $false
Invoke-Expression $PurgeBlock
$left = @(Get-ChildItem -Path $Root -Filter "*-whatsapp.txt" -File | Sort-Object LastWriteTime -Descending)
Assert-Eq @($left).Count 3 "3 copies left"
Assert-Eq @($left)[0].Name "2026-09-06-1900-Evening-whatsapp.txt" "newest kept"
Assert-Eq @($left)[2].Name "2026-09-04-1900-Evening-whatsapp.txt" "third-newest kept"

Write-Host "`nNothing else was touched"
Assert-Eq (Test-Path (Join-Path $Root "IMPORTANT-notes.md")) $true "unrelated file survives"
Assert-Eq (Test-Path (Join-Path $Root "whatsapp.txt")) $true "near-miss filename survives"
Assert-Eq (Test-Path (Join-Path $Root "subfolder/2026-01-01-0700-Morning-whatsapp.txt")) $true "nested file survives (no recursion)"
Assert-Eq (Test-Path (Join-Path $Root "subfolder")) $true "subfolder survives"

Write-Host "`nRunning again when only 3 remain deletes nothing"
Invoke-Expression $PurgeBlock
Assert-Eq (@(Get-ChildItem -Path $Root -Filter "*-whatsapp.txt" -File)).Count 3 "still 3 - idempotent"

Write-Host "`nExactly 3 is not 'more than 3'"
Assert-Eq (@(Get-ChildItem -Path $Root -Filter "*-whatsapp.txt" -File)).Count 3 "boundary holds at the keep count"

# M2 - retention keys on the filename stamp, not LastWriteTime. A restore, a
# copy between machines, or a touch while being read bumps LastWriteTime; if
# the purge trusted it, a stale copy would pin itself at the head of the sort
# and push a genuinely recent archive into the delete list - at exactly the
# moment someone is investigating a bad message. Security Agent M2, 2026-09-11.
Write-Host "`nM2 - a wrong LastWriteTime does not change which copies survive"
Remove-Item -Path (Join-Path $Root "*-whatsapp.txt") -Force
$names = @("2026-09-01-190000-Evening-whatsapp.txt",
           "2026-09-02-190000-Evening-whatsapp.txt",
           "2026-09-03-190000-Evening-whatsapp.txt",
           "2026-09-04-190000-Evening-whatsapp.txt")
foreach ($n in $names) { Set-Content -Path (Join-Path $Root $n) -Value $n -Encoding UTF8 }
# The OLDEST message is given the NEWEST timestamp - the hostile case.
(Get-Item (Join-Path $Root $names[0])).LastWriteTime = (Get-Date).AddYears(1)
Invoke-Expression $PurgeBlock
$after = @(Get-ChildItem -Path $Root -Filter "*-whatsapp.txt" -File | Select-Object -ExpandProperty Name | Sort-Object)
Assert-Eq @($after).Count 3 "still 3 kept"
Assert-Eq ($after -join ",") "2026-09-02-190000-Evening-whatsapp.txt,2026-09-03-190000-Evening-whatsapp.txt,2026-09-04-190000-Evening-whatsapp.txt" "the 3 newest BY NAME survived, despite the faked timestamp"

Remove-Item -Recurse -Force $Root
Write-Host "`n================================"
Write-Host "PASS: $Pass   FAIL: $Fail"
if ($Fail -gt 0) { exit 1 }

# combined_brief.ps1
# Sends ONE combined daily brief covering BOTH active projects:
#   1. JeffLocal (Avamed AI triage system)
#   2. STMARKS-WEB (St Marks Pharmacy website)
#
# Replaces the individual strategy_daily.ps1 call in Task Scheduler.
# The individual scripts still exist and can run standalone.
#
# Mode:
#   -Mode Morning (07:00) — look ahead: yesterday + today's plan
#   -Mode Evening (19:00) — look back: what we did + what's next
#
# Last updated: 2026-06-26

param(
    [ValidateSet('Morning','Evening')]
    [string]$Mode    = 'Morning',
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Today  = (Get-Date).ToString("yyyy-MM-dd")
$NowUTC = (Get-Date).ToUniversalTime().ToString("HH:mm")
$LogFile = "C:\JeffLocal\scripts\daily\combined_brief_last_run.log"

function Write-Log {
    param([string]$Message)
    $ts    = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss UTC")
    $entry = "[$ts] $Message"
    Write-Host $entry
    Add-Content -Path $LogFile -Value $entry -ErrorAction SilentlyContinue
}

# `Get-Content -Encoding UTF8` on Windows PowerShell 5.1 can misdetect a
# non-BOM UTF-8 file and mangle multi-byte characters (em dashes, curly
# quotes) into mojibake — found by tracing a corrupted "—" through to an
# Ollama 400 error. Read raw bytes and decode explicitly instead. Kept
# identical to strategy_daily.ps1's copy — update both if this changes.
function Get-Utf8FileText {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    try {
        return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
    } catch {
        return $null
    }
}

# ── Plain-English pass ────────────────────────────────────────────────────────
# Saeed reads this brief and is not a technical person. This does NOT rewrite
# sentences (no AI call — this runs unattended twice a day, and a call that can
# fail or phrase things oddly is not worth the risk here). It just explains a
# short, common list of technical words the FIRST time each one shows up in the
# brief, e.g. "HMAC" -> "HMAC (a security code that proves a message wasn't faked)".
# Added 2026-07-17 per Saeed's instruction. Kept identical to strategy_daily.ps1's
# copy of this function — update both if the glossary changes.
function Add-PlainEnglishNotes {
    param([string[]]$Lines)

    $Glossary = [ordered]@{
        'HMAC'             = "a security code that proves a message wasn't faked"
        'ACL'              = 'the list of who is allowed to change a folder'
        'webhook'          = 'a message one computer program sends automatically to another'
        'API'              = 'a way two computer programs talk to each other'
        'endpoint'         = 'a specific web address a computer program listens on'
        'SQLite'           = 'the database program that stores patient case info'
        'tenant'           = 'a separate customer, like one GP surgery or one pharmacy'
        'TDD'              = 'writing the test for a fix before writing the fix itself'
        'regression test'  = 'a check that makes sure old things still work after a change'
        'commit'           = 'a saved snapshot of a code change'
        'worktree'         = 'a separate, safe copy of the code to test changes in'
    }

    $Explained = @{}
    $Result = @()
    foreach ($line in $Lines) {
        $out = $line
        foreach ($term in $Glossary.Keys) {
            if (-not $Explained.ContainsKey($term)) {
                $pattern = [regex]::Escape($term) -replace '\\ ', '\s+'
                if ($out -match "(?i)\b$pattern\b") {
                    $plain = $Glossary[$term]
                    $evaluator = { param($m) "$($m.Value) ($plain)" }
                    $out = [regex]::Replace($out, "(?i)\b$pattern\b", $evaluator)
                    $Explained[$term] = $true
                }
            }
        }
        $Result += $out
    }
    return ,$Result
}

# ── Near-duplicate filter ─────────────────────────────────────────────────────
# Session logs restate standing notices (e.g. "NOTHING IS LIVE...") near the
# top of almost every log. Exact-match Select-Object -Unique doesn't catch
# these because the wording drifts slightly each time. Drop a line if its
# first 40 characters already showed up in an earlier kept line.
function Select-NearUnique {
    param([string[]]$Lines)
    $seen = @{}
    $keep = @()
    foreach ($line in $Lines) {
        $key = ($line.Substring(0, [Math]::Min(40, $line.Length))).ToLower()
        if (-not $seen.ContainsKey($key)) {
            $seen[$key] = $true
            $keep += $line
        }
    }
    return ,$keep
}

# ── AI rewrite, with a deterministic fallback ─────────────────────────────────
# Calls the project's local Ollama model to rewrite each line into plain,
# 4th-grade-simple English — real sentence rewriting, not word-swapping.
# Runs unattended twice a day, so this MUST fail safe: any problem (Ollama
# down, timeout, wrong line count back, empty response) returns $null, and the
# caller falls back to the word-glossary version instead of sending nothing or
# something broken. Added 2026-07-17 per Saeed's instruction, after testing
# showed the word-glossary alone can't simplify full technical sentences. Kept
# identical to strategy_daily.ps1's copy — update both if this changes.
function Get-FourthGradeRewrite {
    param(
        [string[]]$Lines,
        [string]$OllamaUrl = "http://localhost:11434/api/generate",
        [string]$Model = "gemma4:e2b",
        [int]$TimeoutSec = 90
    )

    if (-not $Lines -or $Lines.Count -eq 0) { return ,$Lines }

    # Session-log lines are sometimes full paragraphs (200+ words). Feeding
    # that straight to a small local model makes it slow (tested: 25s timeout
    # wasn't enough) and gives it a harder job than "rewrite one sentence".
    # Trim first — a short, clear input rewrites faster AND simpler.
    $trimmedLines = $Lines | ForEach-Object {
        if ($_.Length -gt 300) { $_.Substring(0, 300) + "..." } else { $_ }
    }
    $numbered = for ($i = 0; $i -lt $trimmedLines.Count; $i++) { "$($i + 1). $($trimmedLines[$i])" }
    $prompt = @"
Rewrite each numbered line below in one very simple plain-English sentence a
9-year-old would understand.

STRICT OUTPUT FORMAT:
- Reply with ONLY a numbered list, exactly $($Lines.Count) lines, numbered 1 to $($Lines.Count).
- No headings, no options, no alternatives, no markdown, no asterisks, no extra
  commentary before or after.
- Each output line must be ONE sentence only, same order as the input.
- Do not add any fact that is not already in the input line. Do not drop any line.
- No code, no file paths, no jargon words — explain the idea in everyday words instead.

$($numbered -join "`n")
"@

    try {
        $bodyObj = @{
            model   = $Model
            prompt  = $prompt
            stream  = $false
            options = @{ temperature = 0.1 }
        }
        $body = $bodyObj | ConvertTo-Json -Depth 5
        # Windows PowerShell 5.1's Invoke-RestMethod can send a string body with a
        # leading UTF-8 BOM. Ollama's JSON parser (Go) rejects a BOM prefix outright
        # ("invalid character 'ï' looking for beginning of value") — found by testing
        # this against the real server, not a guess. Encode to UTF-8 bytes WITHOUT a
        # BOM explicitly, so the wire body starts with the literal `{` every time.
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        $bodyBytes = $utf8NoBom.GetBytes($body.TrimStart([char]0xFEFF))
        $response = Invoke-RestMethod -Uri $OllamaUrl -Method Post -Body $bodyBytes `
            -ContentType "application/json; charset=utf-8" -TimeoutSec $TimeoutSec

        $text = $response.response
        if (-not $text) { return $null }

        $outLines = ($text -split "`n") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
        $outLines = @($outLines | ForEach-Object { $_ -replace "^\d+\.\s*", "" })

        if ($outLines.Count -ne $Lines.Count) { return $null }
        return ,$outLines
    } catch {
        return $null
    }
}

Write-Log "combined_brief.ps1 started - $Mode - $Today"

# ── Helper: extract sections from session logs in a given directory ───────────
function Get-ProjectBrief {
    param(
        [string]$SessionsDir,
        [string]$ProjectLabel,
        [string]$Mode
    )

    if ($Mode -eq 'Evening') {
        $DidLabel  = "WHAT WE DID TODAY"
        $NextLabel = "WHAT IS NEXT (tomorrow)"
    } else {
        $DidLabel  = "WHAT WE DID YESTERDAY"
        $NextLabel = "WHAT WE ARE DOING TODAY"
    }

    $SessionSummaries = @()
    if (Test-Path $SessionsDir) {
        $AllSessions = Get-ChildItem -Path $SessionsDir -Filter "*.md" |
            Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" } |
            Sort-Object LastWriteTime -Descending

        foreach ($s in $AllSessions) {
            $Age = ((Get-Date) - $s.LastWriteTime).TotalHours
            if ($Age -le 24) {
                $content = Get-Utf8FileText -Path $s.FullName
                $SessionSummaries += [PSCustomObject]@{ File = $s.Name; Content = $content }
            }
        }
    }

    # Fallback to most recent log if none in last 24h
    $FallbackNote = ""
    if ($SessionSummaries.Count -eq 0 -and (Test-Path $SessionsDir)) {
        $MostRecent = Get-ChildItem -Path $SessionsDir -Filter "*.md" |
            Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" } |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($MostRecent) {
            $AgeH = [math]::Round(((Get-Date) - $MostRecent.LastWriteTime).TotalHours, 0)
            $content = Get-Utf8FileText -Path $MostRecent.FullName
            $SessionSummaries += [PSCustomObject]@{ File = $MostRecent.Name; Content = $content }
            $FallbackNote = "(No log today - using $($MostRecent.Name), ${AgeH}h ago)"
        } else {
            $FallbackNote = "(No session logs found at all)"
        }
    }

    # Extract the 4 standard sections
    $WhatWeDid = @(); $Blockers = @(); $Approvals = @(); $NextTasks = @()

    foreach ($session in $SessionSummaries) {
        $lines  = $session.Content -split "`n"
        $inDid  = $false; $inBlock = $false; $inApproval = $false; $inNext = $false

        foreach ($line in $lines) {
            if ($line -match "^## WHAT WE DID")   { $inDid=$true;      $inBlock=$false; $inApproval=$false; $inNext=$false; continue }
            if ($line -match "^## BLOCKERS")       { $inBlock=$true;    $inDid=$false;   $inApproval=$false; $inNext=$false; continue }
            if ($line -match "^## PENDING SAEED")  { $inApproval=$true; $inDid=$false;   $inBlock=$false;   $inNext=$false; continue }
            if ($line -match "^## WHAT TO DO")     { $inNext=$true;     $inDid=$false;   $inBlock=$false;   $inApproval=$false; continue }
            if ($line -match "^## OPEN TASKS")     { $inNext=$true;     $inDid=$false;   $inBlock=$false;   $inApproval=$false; continue }
            if ($line -match "^## ")               { $inDid=$false;     $inBlock=$false; $inApproval=$false; $inNext=$false; continue }

            $clean = $line.Trim()
            if ($clean -and $clean -notmatch "^#" -and $clean -ne "---") {
                # Grab every real content line, not just "-"/"1." ones — session
                # logs are mostly plain one-line-per-item sentences with no
                # leading marker. Requiring a bullet silently dropped almost
                # everything except nested sub-lists — fixed 2026-07-17.
                $stripped = $clean `
                    -replace "^(\d+\.\s*|-\s*\[.\]\s*|-\s*|\[.\]\s*)", "" `
                    -replace "^\*\*", "" -replace "\*\*$", "" -replace "\*\*", ""

                if ($inDid)      { $WhatWeDid += $stripped }
                if ($inBlock)    { $Blockers  += $stripped }
                if ($inApproval) { $Approvals += $stripped }
                if ($inNext)     { $NextTasks += $stripped }
            }
        }
    }

    # NOTE: Select-NearUnique/Add-PlainEnglishNotes/Get-FourthGradeRewrite all
    # `return ,$x` to stop PowerShell unwrapping a 0/1-element array result.
    # That means their output must be captured with a plain assignment first
    # — piping the function call straight into Select-Object, or wrapping the
    # call itself in @(...), treats the whole returned array as ONE pipeline
    # object instead of N. Capture to a variable first, THEN re-wrap/pipe that
    # variable (safe, since it's already a real array by then).
    $WhatWeDidNear = Select-NearUnique -Lines $WhatWeDid
    $WhatWeDidCapped = @($WhatWeDidNear | Select-Object -First 6)
    $BlockersNear = Select-NearUnique -Lines $Blockers
    $BlockersCapped  = @($BlockersNear)
    $ApprovalsNear = Select-NearUnique -Lines $Approvals
    $ApprovalsCapped = @($ApprovalsNear)
    $NextTasksNear = Select-NearUnique -Lines $NextTasks
    $NextTasksCapped = @($NextTasksNear | Select-Object -First 4)

    $WhatWeDidAI = Get-FourthGradeRewrite -Lines $WhatWeDidCapped
    $BlockersAI  = Get-FourthGradeRewrite -Lines $BlockersCapped
    $ApprovalsAI = Get-FourthGradeRewrite -Lines $ApprovalsCapped
    $NextTasksAI = Get-FourthGradeRewrite -Lines $NextTasksCapped

    $WhatWeDidFinal = if ($WhatWeDidAI) { $WhatWeDidAI } else { Write-Log "AI rewrite unavailable ($ProjectLabel WHAT WE DID) - word-glossary fallback"; Add-PlainEnglishNotes -Lines $WhatWeDidCapped }
    $BlockersFinal  = if ($BlockersAI)  { $BlockersAI }  else { Write-Log "AI rewrite unavailable ($ProjectLabel WHAT'S STUCK) - word-glossary fallback"; Add-PlainEnglishNotes -Lines $BlockersCapped }
    $ApprovalsFinal = if ($ApprovalsAI) { $ApprovalsAI } else { Write-Log "AI rewrite unavailable ($ProjectLabel THINGS I NEED YOU TO OK) - word-glossary fallback"; Add-PlainEnglishNotes -Lines $ApprovalsCapped }
    $NextTasksFinal = if ($NextTasksAI) { $NextTasksAI } else { Write-Log "AI rewrite unavailable ($ProjectLabel WHAT'S NEXT) - word-glossary fallback"; Add-PlainEnglishNotes -Lines $NextTasksCapped }

    $Did      = if ($WhatWeDidFinal.Count -gt 0) { ($WhatWeDidFinal | ForEach-Object { "  - $_" }) -join "`n" } else { "  - Nothing logged in the last day." }
    $Blocking = if ($BlockersFinal.Count -gt 0)  { ($BlockersFinal  | ForEach-Object { "  - $_" }) -join "`n" } else { "  - Nothing stuck right now." }
    $Approve  = if ($ApprovalsFinal.Count -gt 0) { ($ApprovalsFinal | ForEach-Object { "  - [ ] $_" }) -join "`n" } else { "  - Nothing needs your OK right now." }
    $Next     = if ($NextTasksFinal.Count -gt 0) { ($NextTasksFinal | ForEach-Object { "  - $_" }) -join "`n" } else { "  - Nothing lined up yet." }

    $FallbackLine = if ($FallbackNote) { "`n  $FallbackNote`n" } else { "" }

    return @"
$ProjectLabel$FallbackLine
  $DidLabel
$Did

  $NextLabel
$Next

  WHAT'S STUCK
$Blocking

  THINGS I NEED YOU TO OK
$Approve
"@
}

# ── 1. Get brief sections for each project ────────────────────────────────────
Write-Log "Reading JeffLocal session logs..."
$JeffLocalBrief = Get-ProjectBrief `
    -SessionsDir "C:\JeffLocal\docs\sessions" `
    -ProjectLabel "=== YOUR AI RECEPTION HELPER (Avamed) ===" `
    -Mode $Mode

Write-Log "Reading SMCPHARMA session logs..."
$StMarksBrief = Get-ProjectBrief `
    -SessionsDir "C:\JeffLocal\SMCPHARMA\docs\sessions" `
    -ProjectLabel "=== YOUR PHARMACY WEBSITE (St Marks) ===" `
    -Mode $Mode

# ── 2. Get git summaries ──────────────────────────────────────────────────────
# Just a count for Saeed's brief — the actual commit hashes/messages are for
# the engineering side and go in the log file, not the message he reads.
Push-Location "C:\JeffLocal"
try   { $JLGitCount = (git log --oneline --since="24 hours ago" 2>&1 | Measure-Object -Line).Lines } catch { $JLGitCount = 0 }
Pop-Location
Write-Log "JeffLocal commits in last 24h: $JLGitCount"

Push-Location "C:\JeffLocal\SMCPHARMA"
try   { $SMGitCount = (git log --oneline --since="24 hours ago" 2>&1 | Measure-Object -Line).Lines } catch { $SMGitCount = 0 }
Pop-Location
Write-Log "St Marks commits in last 24h: $SMGitCount"

# ── 3. PROJECT_MEMORY pending items — logged for troubleshooting only, not
# shown to Saeed (it's raw internal notes text, not written for him to read;
# his own pending items already come through cleanly via THINGS I NEED YOU TO OK
# above, extracted from the session log).
$MemFile = "C:\JeffLocal\PROJECT_MEMORY.md"
if (Test-Path $MemFile) {
    $MemContent = Get-Utf8FileText -Path $MemFile
    $PendingLines = ($MemContent -split "`n") | Where-Object {
        $_ -match "(BLOCKED|Awaiting Saeed|PENDING|awaiting sign-off)" -and $_.Trim() -ne ""
    } | Select-Object -First 5
    if ($PendingLines) {
        Write-Log ("PROJECT_MEMORY pending (internal only): " + ($PendingLines -join "; "))
    }
}

# ── 4. Assemble combined brief ────────────────────────────────────────────────
if ($Mode -eq 'Evening') {
    $Title = "EVENING BRIEF (wrapping up today)"
    $Clock = "19:00"
} else {
    $Title = "MORNING BRIEF"
    $Clock = "07:00"
}

$CombinedReport = @"
$Title - $Today $Clock
Your two projects: the AI reception helper (Avamed) and the pharmacy website (St Marks)
================================================================

$JeffLocalBrief

Behind the scenes: $JLGitCount code change(s) saved today.

----------------------------------------------------------------

$StMarksBrief

Behind the scenes: $SMGitCount code change(s) saved today.

================================================================
Want more detail on anything above? Just ask me next time we talk.
"@

# ── 5. Save the combined report ───────────────────────────────────────────────
$ReportsDir = "C:\JeffLocal\docs\reports"
if (-not (Test-Path $ReportsDir)) { New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null }
$Suffix      = if ($Mode -eq 'Evening') { "-evening" } else { "" }
$ReportPath  = "$ReportsDir\$Today$Suffix-combined.md"

if ($DryRun) {
    Write-Log "DryRun: would save combined report to $ReportPath"
    Write-Host $CombinedReport
} else {
    Set-Content -Path $ReportPath -Value $CombinedReport -Encoding UTF8
    Write-Log "Combined report saved: $ReportPath"
}

# ── 6. Run the JeffLocal script to update PROJECT_MEMORY + its git/push ──────
# We use -DryRun on the WhatsApp step only — JeffLocal's script still does
# PROJECT_MEMORY updates and git commit; we suppress only its separate send.
if (-not $DryRun) {
    Write-Log "Running JeffLocal strategy_daily.ps1 for PROJECT_MEMORY update..."
    try {
        & "C:\JeffLocal\scripts\daily\strategy_daily.ps1" -Mode $Mode -DryRun 2>&1 | ForEach-Object { Write-Log "  [JL] $_" }
    } catch {
        Write-Log "WARNING: JeffLocal strategy_daily.ps1 failed - $_"
    }
}

# ── 7. Send combined report via WhatsApp ─────────────────────────────────────
if ($DryRun) {
    Write-Log "DryRun: skipped WhatsApp send"
} else {
    $PythonScript = "C:\JeffLocal\scripts\daily\send_whatsapp.py"
    if (Test-Path $PythonScript) {
        try {
            $result = python $PythonScript $ReportPath 2>&1
            Write-Log "WhatsApp send result: $result"
        } catch {
            Write-Log "WARNING: WhatsApp send failed - $_"
        }
    } else {
        Write-Log "WARNING: WhatsApp sender not found at $PythonScript"
    }
}

Write-Log "combined_brief.ps1 complete - $Mode"

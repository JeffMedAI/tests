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
# professional, non-technical business English — real sentence rewriting, not word-swapping.
# Runs unattended twice a day, so this MUST fail safe: any problem (Ollama
# down, timeout, wrong line count back, empty response) returns $null, and the
# caller falls back to the word-glossary version instead of sending nothing or
# something broken. Added 2026-07-17 per Saeed's instruction, after testing
# showed the word-glossary alone can't simplify full technical sentences. Kept
# identical to strategy_daily.ps1's copy — update both if this changes.
function Get-BusinessRewrite {
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
    # @(...) wrap is required: piping a single-element array through
    # ForEach-Object unwraps it to a bare string, and a bare string has no
    # .Count under Set-StrictMode -Version Latest — found while testing the
    # Ollama-down fallback with a 1-line brief section.
    $trimmedLines = @($Lines | ForEach-Object {
        if ($_.Length -gt 300) { $_.Substring(0, 300) + "..." } else { $_ }
    })
    $numbered = for ($i = 0; $i -lt $trimmedLines.Count; $i++) { "$($i + 1). $($trimmedLines[$i])" }
    $prompt = @"
Rewrite each numbered line below in one clear, plain-English sentence a smart,
non-technical business or project manager would immediately understand. Professional
in tone, not childish -- no dumbing down, just no jargon.

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
# ---------------------------------------------------------------------------
# Placeholder / staleness helpers
#
# strategy_daily.ps1 writes an automated placeholder session log on any evening
# where no human session was logged. That file is a courtesy, NOT evidence of
# work. Counting it as a real log is exactly what let the 11-19 Aug 2026 outage
# hide: the Cowork session close could not mount C:\JeffLocal, so no real close
# ran for 8 days, but a file existed for each day so nothing ever looked wrong.
# Placeholders are still read for content - they just never reset the clock.
# ---------------------------------------------------------------------------
function Test-IsPlaceholderLog {
    param([string]$Content)
    if ([string]::IsNullOrWhiteSpace($Content)) { return $true }
    # Only the HEADER counts. A real session log that *discusses* the marker - as the
    # 2026-08-20 close does while explaining this very mechanism - must not be misread
    # as a placeholder, or it raises a false staleness alarm. Match the marker only as
    # a comment line in the first 10 lines, which is where the generator puts it.
    $Head = (@($Content -split "`n") | Select-Object -First 10) -join "`n"
    return ($Head -match '(?m)^\s*#\s*AUTOGEN-PLACEHOLDER') -or
           ($Head -match '(?m)^\s*#.*No human session today')
}

function Format-StaleLine {
    param([string]$Name, [double]$Hours, [string]$LogName)
    if ($Hours -ge 99999) { return "!!   $Name : NO session log has ever been found" }
    $Days    = [math]::Floor($Hours / 24)
    $AgeText = if ($Days -ge 1) { "nothing new logged for $Days day(s)" }
               else             { "nothing new logged for $Hours hour(s)" }
    $Src     = if ($LogName) { " - still showing $LogName" } else { "" }
    return "!!   $Name : $AgeText$Src"
}

function Format-HeldLine {
    param([string]$Name, [string]$Path, [int]$Count)
    return "!!   $Name : $Count unfinished file(s) in $Path\"
}

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
    $RealLogCount     = 0
    if (Test-Path $SessionsDir) {
        $AllSessions = Get-ChildItem -Path $SessionsDir -Filter "*.md" |
            Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" } |
            Sort-Object LastWriteTime -Descending

        foreach ($s in $AllSessions) {
            $Age = ((Get-Date) - $s.LastWriteTime).TotalHours
            if ($Age -le 24) {
                $content = Get-Utf8FileText -Path $s.FullName
                $SessionSummaries += [PSCustomObject]@{ File = $s.Name; Content = $content }
                if (-not (Test-IsPlaceholderLog -Content $content)) { $RealLogCount++ }
            }
        }
    }

    # STALE = no REAL session log in the last 24h. A placeholder does not count.
    $FallbackNote = ""
    $IsStale      = $false
    $StaleHours   = 0
    $StaleLogName = ""
    if ($RealLogCount -eq 0 -and (Test-Path $SessionsDir)) {
        $IsStale = $true
        $Candidates = @(Get-ChildItem -Path $SessionsDir -Filter "*.md" |
            Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" } |
            Sort-Object LastWriteTime -Descending)
        $NewestReal = $null
        foreach ($c in $Candidates) {
            if (-not (Test-IsPlaceholderLog -Content (Get-Utf8FileText -Path $c.FullName))) {
                $NewestReal = $c
                break
            }
        }
        if ($NewestReal) {
            $StaleHours   = [math]::Round(((Get-Date) - $NewestReal.LastWriteTime).TotalHours, 0)
            $StaleLogName = $NewestReal.Name
            $FallbackNote = "(STALE - no real session log today. Newest real log: $StaleLogName, ${StaleHours}h ago)"
            if ($SessionSummaries.Count -eq 0) {
                $SessionSummaries += [PSCustomObject]@{ File = $NewestReal.Name; Content = (Get-Utf8FileText -Path $NewestReal.FullName) }
            }
        } else {
            $FallbackNote = "(STALE - no real session log found at all)"
            $StaleHours   = 99999
        }
        Write-Log "STALENESS: $ProjectLabel - no real session log in 24h (newest real: $StaleLogName, ${StaleHours}h ago)"
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

    # NOTE: Select-NearUnique/Add-PlainEnglishNotes/Get-BusinessRewrite all
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

    $WhatWeDidAI = Get-BusinessRewrite -Lines $WhatWeDidCapped
    $BlockersAI  = Get-BusinessRewrite -Lines $BlockersCapped
    $ApprovalsAI = Get-BusinessRewrite -Lines $ApprovalsCapped
    $NextTasksAI = Get-BusinessRewrite -Lines $NextTasksCapped

    # Get-BusinessRewrite returns $null (a real null, not an empty array) only
    # when the Ollama call itself failed/timed out — flag that up to the caller
    # so it can be surfaced on the WhatsApp message, not just in the log file.
    # Compare with -eq $null rather than -not: an empty-but-successful rewrite
    # (,$Lines of a 0-item array) is falsy too and would be a false positive.
    $AIFallbackUsed = ($null -eq $WhatWeDidAI) -or ($null -eq $BlockersAI) -or ($null -eq $ApprovalsAI) -or ($null -eq $NextTasksAI)

    # ,$WhatWeDidAI (not bare $WhatWeDidAI) in the true branch: a bare array
    # variable used as a script block's output gets enumerated element-by-
    # element same as Write-Output, so a 1-item array collapses to a scalar
    # string and the .Count check two lines down throws under strict mode —
    # found while testing the Ollama-down fallback with a 1-line brief section.
    $WhatWeDidFinal = if ($WhatWeDidAI) { ,$WhatWeDidAI } else { Write-Log "AI rewrite unavailable ($ProjectLabel WHAT WE DID) - word-glossary fallback"; Add-PlainEnglishNotes -Lines $WhatWeDidCapped }
    $BlockersFinal  = if ($BlockersAI)  { ,$BlockersAI }  else { Write-Log "AI rewrite unavailable ($ProjectLabel WHAT'S STUCK) - word-glossary fallback"; Add-PlainEnglishNotes -Lines $BlockersCapped }
    $ApprovalsFinal = if ($ApprovalsAI) { ,$ApprovalsAI } else { Write-Log "AI rewrite unavailable ($ProjectLabel THINGS I NEED YOU TO OK) - word-glossary fallback"; Add-PlainEnglishNotes -Lines $ApprovalsCapped }
    $NextTasksFinal = if ($NextTasksAI) { ,$NextTasksAI } else { Write-Log "AI rewrite unavailable ($ProjectLabel WHAT'S NEXT) - word-glossary fallback"; Add-PlainEnglishNotes -Lines $NextTasksCapped }

    $Did      = if ($WhatWeDidFinal.Count -gt 0) { ($WhatWeDidFinal | ForEach-Object { "  - $_" }) -join "`n" } else { "  - Nothing logged in the last day." }
    $Blocking = if ($BlockersFinal.Count -gt 0)  { ($BlockersFinal  | ForEach-Object { "  - $_" }) -join "`n" } else { "  - Nothing stuck right now." }
    $Approve  = if ($ApprovalsFinal.Count -gt 0) { ($ApprovalsFinal | ForEach-Object { "  - [ ] $_" }) -join "`n" } else { "  - Nothing needs your OK right now." }
    $Next     = if ($NextTasksFinal.Count -gt 0) { ($NextTasksFinal | ForEach-Object { "  - $_" }) -join "`n" } else { "  - Nothing lined up yet." }

    $FallbackLine = if ($FallbackNote) { "`n  $FallbackNote`n" } else { "" }

    $Text = @"
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

    return [PSCustomObject]@{
        Text           = $Text
        AIFallbackUsed = $AIFallbackUsed
        IsStale        = $IsStale
        StaleHours     = $StaleHours
        StaleLogName   = $StaleLogName
    }
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

$OllamaNote = if ($JeffLocalBrief.AIFallbackUsed -or $StMarksBrief.AIFallbackUsed) {
    "`n[Note: AI rewrite unavailable - raw summary below]`n"
} else { "" }
Write-Log "Ollama AI rewrite fallback used: JeffLocal=$($JeffLocalBrief.AIFallbackUsed) StMarks=$($StMarksBrief.AIFallbackUsed)"

# Staleness banner - loud, per project, at the very top of the message.
# One project can go dark while the other is busy: on 19 Aug 2026 JeffLocal had
# no real session log for 8 days while St Marks shipped 5 commits the same day.
# The old brief buried that in a small "(No log today...)" note mid-message and
# nobody noticed for over a week. This banner names names, at the top.
$StaleParts = @()
if ($JeffLocalBrief.IsStale) {
    $StaleParts += (Format-StaleLine -Name "AI reception helper (Avamed)" -Hours $JeffLocalBrief.StaleHours -LogName $JeffLocalBrief.StaleLogName)
}
if ($StMarksBrief.IsStale) {
    $StaleParts += (Format-StaleLine -Name "Pharmacy website (St Marks)" -Hours $StMarksBrief.StaleHours -LogName $StMarksBrief.StaleLogName)
}

$StaleBanner = ""
if (@($StaleParts).Count -gt 0) {
    $StaleBody   = (@($StaleParts) -join [Environment]::NewLine)
    $StaleBanner = @"
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! WARNING - PART OF THIS BRIEF IS OUT OF DATE
$StaleBody
!!
!! The daily session close is NOT running for the project(s) above.
!! What you read below for them is OLD news repeated, not today's work.
!! Do not read it as progress. This needs fixing before you trust it.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

"@
    Write-Log "STALENESS BANNER SHOWN for $(@($StaleParts).Count) project(s)"
} else {
    Write-Log "Staleness check: both projects have a real session log within 24h"
}

# ── System health block (morning only) ───────────────────────────────────────
# Written at 06:45 by scripts\daily\health_check.ps1, fifteen minutes before this
# brief. Saeed's instruction 2026-09-04: the brief should be fully informed, not
# just a summary of git activity. It answers "is work flowing" - unresolved cases,
# red flags, stuck queue, backups, the 90-day purge, other jobs quietly failing.
#
# Evening briefs do not carry it: nothing here changes between 06:45 and 19:00
# that the evening reader can act on, and repeating it would pad the message.
$HealthBlock = ""
if ($Mode -eq 'Morning') {
    $HealthFile = "C:\JeffLocal\logs\health\$Today-health.txt"
    if (Test-Path $HealthFile) {
        $HealthText  = Get-Utf8FileText -Path $HealthFile
        $HealthBlock = @"
$HealthText

----------------------------------------------------------------

"@
        Write-Log "Health check block included from $HealthFile"
    } elseif ((Get-Date).DayOfWeek -eq [DayOfWeek]::Saturday -or (Get-Date).DayOfWeek -eq [DayOfWeek]::Sunday) {
        $HealthBlock = "SYSTEM HEALTH: not checked - no health check at weekends." + [Environment]::NewLine +
                       [Environment]::NewLine + "----------------------------------------------------------------" +
                       [Environment]::NewLine + [Environment]::NewLine
        Write-Log "Weekend - no health check expected."
    } else {
        $HealthBlock = @"
SYSTEM HEALTH: UNKNOWN - the 06:45 health check did not run this morning.
Nothing is necessarily wrong; nothing has been checked either.
Check the scheduled task "JeffLocal - Weekday Health Check 0645".

----------------------------------------------------------------

"@
        Write-Log "WARNING: no health file at $HealthFile - health block shows UNKNOWN."
    }
}

$CombinedReport = @"
$Title - $Today $Clock
Your two projects: the AI reception helper (Avamed) and the pharmacy website (St Marks)
================================================================
$StaleBanner$OllamaNote$HealthBlock
$($JeffLocalBrief.Text)

Behind the scenes: $JLGitCount code change(s) saved today.

----------------------------------------------------------------

$($StMarksBrief.Text)

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
# Collects any PUSH-HELD signal the closes emit, so the warning can go into the
# very brief that is about to be sent rather than waiting for the next one.
$HeldSignals     = @()
$NoCloseToday    = $false
$CloseFailDetail = @()

# ── 6-pre. EVENING: the close already happened at 18:30 ──────────────────────
# Saeed's instruction 2026-09-04: the session close moved OUT of this brief and
# into scripts\daily\session_close.ps1, on its own weekday 18:30 scheduled task.
# So in Evening mode this script no longer closes anything - it reads the marker
# that close left behind and reports on it. Correct order: close, then describe.
#
# Morning mode is UNCHANGED. The 07:00 run still calls strategy_daily.ps1 below
# as its git safety net, which is what commits and pushes weekend work (no close
# runs on a Saturday or Sunday).
#
# Deliberately NO fallback close here. If the 18:30 task failed, this brief says
# so loudly rather than quietly closing on its own - a silent auto-recovery is
# how the 11-19 Aug 2026 failure went unnoticed for eight days.
$SkipCloseHere = $false
if ($Mode -eq 'Evening') {
    $SkipCloseHere = $true
    $CloseStateFile = "C:\JeffLocal\logs\close-state\$Today-close.txt"
    if (Test-Path $CloseStateFile) {
        $MarkerLines = @(Get-Content -Path $CloseStateFile -ErrorAction SilentlyContinue)
        $HeldSignals += @(@($MarkerLines) | Where-Object { $_ -like "PUSH-HELD|*" })
        $ClosedAt = @(@($MarkerLines) | Where-Object { $_ -like "CLOSED|*" }) | Select-Object -First 1
        if ($ClosedAt) {
            Write-Log "18:30 close already ran today ($ClosedAt) - this brief reports only."
        } else {
            # Marker present but no CLOSED line: the close RAN and FAILED. Treat it
            # exactly as harshly as a missing marker - the outcome for Saeed is the
            # same (no session log, no handover, no restore point) and a half-done
            # close reported as fine is how failures hide. Security Agent, 2026-09-04.
            $NoCloseToday = $true
            $CloseFailDetail = @(@($MarkerLines) | Where-Object { $_ -like "FAILED-DETAIL|*" }) |
                ForEach-Object { "  - " + (([string]$_).Split("|", 3)[1..2] -join ": ") }
            Write-Log "WARNING: 18:30 close RAN AND FAILED today - $(@($CloseFailDetail).Count) project(s) affected."
        }
    } else {
        $NoCloseToday = $true
        Write-Log "WARNING: no 18:30 close marker at $CloseStateFile - NO CLOSE RAN TODAY."
    }
}

# combined_brief.ps1 owns the single WhatsApp message, so this call uses -NoSend:
# strategy_daily.ps1 still updates PROJECT_MEMORY, commits, pushes and (evening)
# cuts the restore tag - it just does not fire a second message.
# It used to be called with -DryRun, which ALSO switched off the memory write,
# the commit, the push and the tag. That is why 14 commits sat unpushed and no
# restore tag was cut between 28 Jul and 19 Aug 2026. Do NOT put -DryRun back.
if (-not $DryRun -and -not $SkipCloseHere) {
    Write-Log "Running JeffLocal strategy_daily.ps1 (PROJECT_MEMORY + git safety net)..."
    try {
        # -ProtectPath dashboard: C:\JeffLocal\dashboard\ is production, served live
        # on port 8765. A push deploys nothing here, but the rule is the same for
        # both projects - unfinished production work does not leave the machine.
        $JLOutput = & "C:\JeffLocal\scripts\daily\strategy_daily.ps1" `
            -Mode $Mode -NoSend -ProtectPath "dashboard" -RefreshGraph 2>&1 |
            ForEach-Object { Write-Log "  [JL] $_"; $_ }
        $HeldSignals += @(@($JLOutput) | ForEach-Object { [string]$_ } | Where-Object { $_ -like "PUSH-HELD|*" })
    } catch {
        Write-Log "WARNING: JeffLocal strategy_daily.ps1 failed - $_"
    }
}

# ── 6b. Same automated close for St Marks (SMCPHARMA) ────────────────────────
# Saeed's instruction 2026-08-20. Until now only JeffLocal had an automated close,
# so the pharmacy project's session log, HANDOFF and memory only moved when someone
# ran a session by hand - and the combined brief goes stale for whichever project
# stops being logged. Same script, pointed at SMCPHARMA's own folders, -NoSend again
# so there is still exactly one WhatsApp message.
#
# NOTE: this repo is git-connected to Cloudflare - a push redeploys the LIVE pharmacy
# site. The close commits and pushes everything, per Saeed's instruction, so anything
# left uncommitted under site\ goes live at 19:00 without review. Flagged to Saeed
# 2026-08-20; a guard can be added here if he wants one.
if (-not $DryRun -and -not $SkipCloseHere) {
    $SmRepo = "C:\JeffLocal\SMCPHARMA"
    if (Test-Path (Join-Path $SmRepo "PROJECT_MEMORY.md")) {
        Write-Log "Running session close for St Marks (SMCPHARMA)..."
        try {
            & "C:\JeffLocal\scripts\daily\strategy_daily.ps1" `
                -Mode $Mode -NoSend `
                -ProjectName "St Marks Pharmacy Website (STMARKS-WEB)" `
                -RepoRoot    $SmRepo `
                -ReportsDir  (Join-Path $SmRepo "docs\reports") `
                -SessionsDir (Join-Path $SmRepo "docs\sessions") `
                -ProjectDocs (Join-Path $SmRepo "docs") `
                -MemoryFile  (Join-Path $SmRepo "PROJECT_MEMORY.md") `
                -ProtectPath "site" 2>&1 |
                ForEach-Object { Write-Log "  [SM] $_"; $_ } |
                Where-Object { ([string]$_) -like "PUSH-HELD|*" } |
                ForEach-Object { $script:HeldSignals += [string]$_ }
        } catch {
            Write-Log "WARNING: St Marks session close failed - $_"
        }
    } else {
        Write-Log "WARNING: SMCPHARMA not found at $SmRepo - skipped its session close"
    }
}

# ── 6b-2. The 18:30 close did not run? Say so, loudly, tonight ───────────────
# Nothing was lost - the work is still on the machine - but today has no session
# log, no HANDOFF refresh, no commit and no restore tag. Saeed sees it the same
# evening rather than discovering a gap weeks later.
if ($NoCloseToday) {
    $NoCloseBanner = @"
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! TODAY'S SESSION CLOSE DID NOT COMPLETE
!! The 18:30 close did not complete, so today has no session log,
!! no handover note, nothing saved to GitHub and no restore point.
$(if (@($CloseFailDetail).Count -gt 0) { "!! It ran and failed:" + [Environment]::NewLine + (@($CloseFailDetail) -join [Environment]::NewLine) } else { "!! It did not run at all." })
!!
!! Your work is NOT lost - it is still on the computer.
!! Check the scheduled task "JeffLocal - Weekday Session Close 1830".
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

"@
    if (-not $DryRun -and (Test-Path $ReportPath)) {
        $ExistingReport = Get-Utf8FileText -Path $ReportPath
        Set-Content -Path $ReportPath -Value ($NoCloseBanner + $ExistingReport) -Encoding UTF8
    }
    Write-Log "NO CLOSE banner added to tonight's brief"
    Write-Host $NoCloseBanner
}

# ── 6c. Push held? Warn Saeed in THIS message, not tomorrow's ────────────────
# The report file was written in section 5 and the send in section 7 reads it back
# off disk, so prepending here reaches him the same evening with no second
# message and no second browser session.
if (@($HeldSignals).Count -gt 0) {
    $HeldLines = @()
    foreach ($sig in @($HeldSignals)) {
        $parts = ([string]$sig).Split("|")
        if ($parts.Count -ge 4) {
            $HeldLines += (Format-HeldLine -Name $parts[1] -Path $parts[2] -Count ([int]$parts[3]))
        }
    }
    $HeldBody = (@($HeldLines) -join [Environment]::NewLine)
    $HeldBanner = @"
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! PUSH HELD - UNFINISHED WORK IS SITTING IN A LIVE FOLDER
$HeldBody
!!
!! Nothing is lost - it IS saved on this computer. It was NOT
!! sent to GitHub, and NOT published to the website.
!! Finish it or undo it, and the next close will send it.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

"@
    if (-not $DryRun -and (Test-Path $ReportPath)) {
        $ExistingReport = Get-Utf8FileText -Path $ReportPath
        Set-Content -Path $ReportPath -Value ($HeldBanner + $ExistingReport) -Encoding UTF8
    }
    Write-Log "PUSH HELD banner added to tonight's brief for $(@($HeldLines).Count) project(s)"
    Write-Host $HeldBanner
} else {
    Write-Log "Push guard: nothing held, both projects pushed normally"
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

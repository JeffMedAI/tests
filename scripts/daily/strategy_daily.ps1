# strategy_daily.ps1
# JeffLocal - Strategy Agent Daily Brief (plain English for Saeed)
#
# TWO scheduled runs (same script, different -Mode):
#   -Mode Morning  -> 07:00  "MORNING BRIEF"  (look ahead: yesterday recap + today's plan)
#   -Mode Evening  -> 19:00  "EVENING BRIEF"  (session close: what we did today + handover)
#
# COMBINED MODE: When called as a scheduled task (no -DryRun, no -RepoRoot override)
# this script forwards to combined_brief.ps1, which covers BOTH projects (JeffLocal +
# St Marks Pharmacy / STMARKS-WEB) in a single WhatsApp message.
# The -DryRun flag suppresses the forward so combined_brief.ps1 can call this script
# internally without recursion.
#
# Last updated: 2026-06-26

param(
    [ValidateSet('Morning','Evening')]
    [string]$Mode        = 'Morning',
    [switch]$DryRun,
    [string]$RepoRoot    = "C:\JeffLocal",
    [string]$ReportsDir  = "C:\JeffLocal\docs\reports",
    [string]$SessionsDir = "C:\JeffLocal\docs\sessions",
    [string]$ProjectDocs = "C:\JeffLocal\docs\project_documents",
    [string]$MemoryFile  = "C:\JeffLocal\PROJECT_MEMORY.md"
)

# ── Mode-dependent labels ─────────────────────────────────────────────────────
if ($Mode -eq 'Evening') {
    $BriefTitle = "EVENING BRIEF (wrapping up today)"
    $BriefClock = "19:00"
    $DidLabel   = "WHAT WE DID TODAY"
    $NextLabel  = "WHAT IS NEXT (tomorrow)"
} else {
    $BriefTitle = "MORNING BRIEF"
    $BriefClock = "07:00"
    $DidLabel   = "WHAT WE DID YESTERDAY"
    $NextLabel  = "WHAT WE ARE DOING TODAY"
}

# ── COMBINED BRIEF FORWARD ────────────────────────────────────────────────────
# When called as a scheduled task (DryRun not set, default RepoRoot) forward to
# combined_brief.ps1 which covers both projects. combined_brief.ps1 then calls
# this script with -DryRun to update PROJECT_MEMORY without looping.
$_CombinedScript = "C:\JeffLocal\scripts\daily\combined_brief.ps1"
if (-not $DryRun -and $RepoRoot -eq "C:\JeffLocal" -and (Test-Path $_CombinedScript)) {
    Write-Host "Forwarding to combined_brief.ps1 (covers JeffLocal + St Marks Pharmacy)..."
    & $_CombinedScript -Mode $Mode
    exit $LASTEXITCODE
}

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Today     = (Get-Date).ToString("yyyy-MM-dd")
$Yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
$NowUTC    = (Get-Date).ToUniversalTime().ToString("HH:mm")
$LogFile   = "$RepoRoot\scripts\daily\last_run.log"

function Write-Log {
    param([string]$Message)
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss UTC")
    $entry = "[$ts] $Message"
    Write-Host $entry
    Add-Content -Path $LogFile -Value $entry -ErrorAction SilentlyContinue
}

# `Get-Content -Encoding UTF8` on Windows PowerShell 5.1 can misdetect a
# non-BOM UTF-8 file and mangle multi-byte characters (em dashes, curly
# quotes) into mojibake — found by tracing a corrupted "—" through to an
# Ollama 400 error. Read raw bytes and decode explicitly instead.
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
# Added 2026-07-17 per Saeed's instruction.
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
# showed the word-glossary alone can't simplify full technical sentences.
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

Write-Log "strategy_daily.ps1 started for $Today"

# ── 1. Read session logs from last 24 hours ───────────────────────────────────
Write-Log "Reading session logs from $SessionsDir..."
$SessionSummaries = @()

if (Test-Path $SessionsDir) {
    $AllSessions = Get-ChildItem -Path $SessionsDir -Filter "*.md" |
        Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" } |
        Sort-Object LastWriteTime -Descending

    foreach ($s in $AllSessions) {
        $Age = ((Get-Date) - $s.LastWriteTime).TotalHours
        if ($Age -le 24) {
            $content = Get-Utf8FileText -Path $s.FullName
            $SessionSummaries += [PSCustomObject]@{
                File    = $s.Name
                Age     = [math]::Round($Age, 1)
                Content = $content
            }
        }
    }
}
Write-Log "Found $($SessionSummaries.Count) session log(s) from last 24h"

# ── 1b. Fallback: if no logs in last 24h, use the most recent one (any age) ───
# Guarantees the brief is NEVER empty. PROJECT_MEMORY is still read below as a
# second source. The "session logs not found" dead-end must never happen.
$UsedFallbackLog = $false
if ($SessionSummaries.Count -eq 0 -and (Test-Path $SessionsDir)) {
    $MostRecent = Get-ChildItem -Path $SessionsDir -Filter "*.md" |
        Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($MostRecent) {
        $UsedFallbackLog = $true
        $content = Get-Utf8FileText -Path $MostRecent.FullName
        $SessionSummaries += [PSCustomObject]@{
            File    = $MostRecent.Name
            Age     = [math]::Round(((Get-Date) - $MostRecent.LastWriteTime).TotalHours, 1)
            Content = $content
        }
        Write-Log "No logs in last 24h - fell back to most recent: $($MostRecent.Name)"
    } else {
        Write-Log "WARNING: docs\sessions\ has no session logs at all. Session-close protocol was skipped."
    }
}

# ── 2. Extract sections from session logs ────────────────────────────────────
$WhatWeDid = @(); $Blockers = @(); $Approvals = @(); $NextTasks = @()

foreach ($session in $SessionSummaries) {
    $lines = $session.Content -split "`n"
    $inDid = $false; $inBlock = $false; $inApproval = $false; $inNext = $false

    foreach ($line in $lines) {
        # Section headers — broad matches so renamed headings still resolve
        if ($line -match "^## WHAT WE DID")         { $inDid=$true;      $inBlock=$false; $inApproval=$false; $inNext=$false; continue }
        if ($line -match "^## BLOCKERS")             { $inBlock=$true;    $inDid=$false;   $inApproval=$false; $inNext=$false; continue }
        if ($line -match "^## PENDING SAEED")        { $inApproval=$true; $inDid=$false;   $inBlock=$false;   $inNext=$false; continue }
        if ($line -match "^## OPEN TASKS")                   { $inNext=$true;     $inDid=$false; $inBlock=$false;   $inApproval=$false; continue }
        if ($line -match "^## WHAT TO DO")           { $inNext=$true;     $inDid=$false;   $inBlock=$false;   $inApproval=$false; continue }
        if ($line -match "^## ")                     { $inDid=$false;     $inBlock=$false; $inApproval=$false; $inNext=$false; continue }

        $clean = $line.Trim()
        if ($clean -and $clean -notmatch "^#" -and $clean -ne "---") {
            # Grab every real content line, not just ones starting with "-" or
            # "1." — session logs are written "one line per item" (CLAUDE.md
            # style) and most lines are plain sentences with no leading marker.
            # Only requiring a bullet/number silently dropped almost everything
            # except nested sub-lists — fixed 2026-07-17.
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

# ── 3. Git log last 24 hours ──────────────────────────────────────────────────
Write-Log "Collecting git log..."
Push-Location $RepoRoot
try {
    $GitLog = git log --oneline --since="24 hours ago" 2>&1
    if (-not $GitLog) { $GitLog = "(no commits in last 24 hours)" }
    $LatestCommit = (git log --oneline -1 2>&1)
} catch {
    $GitLog = "(git log failed)"; $LatestCommit = "unknown"
}
Pop-Location

# ── 4. Document freshness check ───────────────────────────────────────────────
$StaleDocs = @()
if (Test-Path $ProjectDocs) {
    Get-ChildItem -Path $ProjectDocs -Filter "*.md" -Recurse | ForEach-Object {
        $days = ((Get-Date) - $_.LastWriteTime).Days
        if ($days -gt 3) { $StaleDocs += "$($_.Name) (${days}d old)" }
    }
}

# ── 5. STATE VERIFICATION — compare PROJECT_MEMORY with session logs ─────────
Write-Log "Running state verification..."

$MemoryContent = if (Test-Path $MemoryFile) { Get-Utf8FileText -Path $MemoryFile } else { "" }

# Extract CURRENT STATUS section from PROJECT_MEMORY.md
$MemoryStatus = ""
if ($MemoryContent -match "(?s)## CURRENT STATUS.*?(?=\n---|\n## )") {
    $MemoryStatus = $Matches[0]
}

# Pull last 5 commits for cross-reference
Push-Location $RepoRoot
try {
    $Last5Commits = git log --oneline -5 2>&1
} catch {
    $Last5Commits = "(git log failed)"
}
Pop-Location

# Extract pending/blocked items from PROJECT_MEMORY current status
$MemoryPendingItems = @()
if ($MemoryStatus) {
    foreach ($line in ($MemoryStatus -split "`n")) {
        $l = $line.Trim()
        if ($l -match "(BLOCKED|Awaiting Saeed|PENDING|awaiting sign-off)" -and $l -ne "") {
            $MemoryPendingItems += $l -replace "^\|?\s*", "" -replace "\s*\|.*$", ""
        }
    }
}

# Collect all topics mentioned in session logs (last 24h)
$SessionTopics = @()
foreach ($session in $SessionSummaries) {
    foreach ($line in ($session.Content -split "`n")) {
        $l = $line.Trim()
        if ($l -match "(cookie|main\.py|N1|N2|R2|GDPR|sandbox|degraded|sign-off|approval)" -and $l -ne "") {
            $SessionTopics += $l
        }
    }
}

# Detect drift: memory items with no corresponding session log activity
$DriftItems = @()
foreach ($item in $MemoryPendingItems) {
    # Check if any session log line references keywords from this item
    $keywords = ($item -replace "[|#\[\]\(\)\*`"]","").Split(" ") |
        Where-Object { $_.Length -gt 5 } | Select-Object -First 3
    $found = $false
    foreach ($kw in $keywords) {
        if ($SessionTopics -join " " -match [regex]::Escape($kw)) { $found = $true; break }
    }
    if (-not $found) { $DriftItems += $item }
}

# Build STATE VERIFICATION section text
$MemoryPendingText = if ($MemoryPendingItems.Count -gt 0) {
    ($MemoryPendingItems | Select-Object -First 10 | ForEach-Object { "- $_" }) -join "`n"
} else { "- No pending/blocked items found in PROJECT_MEMORY current status." }

$DriftText = if ($DriftItems.Count -gt 0) {
    ($DriftItems | ForEach-Object { "- DRIFT: No recent session activity for: $_" }) -join "`n"
} else { "- No drift detected. All memory items have corresponding recent log activity." }

$CommitText = if ($Last5Commits -is [array]) { $Last5Commits -join "`n" } else { $Last5Commits }

$StateVerificationSection = @"

---

## MEMORY CHECK

Pending/blocked in PROJECT_MEMORY:
$MemoryPendingText

Last 5 commits:
$CommitText

Drift (memory items with no session log match):
$DriftText
"@

Write-Log "State verification complete. Memory pending items: $($MemoryPendingItems.Count). Drift items: $($DriftItems.Count)."

# ── 6. Update PROJECT_MEMORY.md date + git state ────────────────────────────
Write-Log "Updating PROJECT_MEMORY.md..."
if (Test-Path $MemoryFile) {
    $memory = Get-Utf8FileText -Path $MemoryFile
    $memory = $memory -replace "# Last updated: .+", "# Last updated: $Today (auto-updated $BriefClock)"
    if ($LatestCommit -ne "unknown") {
        $memory = $memory -replace "Latest:\s+.+", "Latest:  $LatestCommit"
    }
    if ($DryRun) {
        Write-Log "DryRun: skipped PROJECT_MEMORY.md write"
    } else {
        Set-Content -Path $MemoryFile -Value $memory -Encoding UTF8
        Write-Log "PROJECT_MEMORY.md updated"
    }
}

# ── 7. Build daily briefing ───────────────────────────────────────────────────
# Dedupe near-identical restated lines, then cap length BEFORE any rewrite —
# keeps the AI prompt small and the final message short either way.
# NOTE: Select-NearUnique/Add-PlainEnglishNotes/Get-BusinessRewrite all
# `return ,$x` to stop PowerShell unwrapping a 0/1-element array result. That
# means their output must be captured with a plain assignment first — piping
# the function call straight into Select-Object, or wrapping the call itself
# in @(...), treats the whole returned array as ONE pipeline object instead of
# N. Capture to a variable first, THEN re-wrap/pipe that variable (safe, since
# it's already a real array by then).
$WhatWeDidNear = Select-NearUnique -Lines $WhatWeDid
$WhatWeDidCapped = @($WhatWeDidNear | Select-Object -First 8)
$BlockersNear = Select-NearUnique -Lines $Blockers
$BlockersCapped  = @($BlockersNear)
$ApprovalsNear = Select-NearUnique -Lines $Approvals
$ApprovalsCapped = @($ApprovalsNear)
$NextTasksNear = Select-NearUnique -Lines $NextTasks
$NextTasksCapped = @($NextTasksNear | Select-Object -First 5)

# Try the AI rewrite first (real sentence simplifying); anything it can't
# handle (Ollama down, timeout, bad output) falls back to the word-glossary
# version so the brief always sends something readable.
$WhatWeDidAI = Get-BusinessRewrite -Lines $WhatWeDidCapped
$BlockersAI  = Get-BusinessRewrite -Lines $BlockersCapped
$ApprovalsAI = Get-BusinessRewrite -Lines $ApprovalsCapped
$NextTasksAI = Get-BusinessRewrite -Lines $NextTasksCapped

# Get-BusinessRewrite returns $null (a real null, not an empty array) only when
# the Ollama call itself failed/timed out — Saeed needs to see that on the
# WhatsApp message itself, not just in the log file. Compare with -eq $null
# rather than -not, because an empty-but-successful rewrite (,$Lines of a
# 0-item array) is falsy too and would be a false positive here.
$OllamaFallbackUsed = ($null -eq $WhatWeDidAI) -or ($null -eq $BlockersAI) -or ($null -eq $ApprovalsAI) -or ($null -eq $NextTasksAI)
Write-Log "Ollama AI rewrite fallback used: $OllamaFallbackUsed"

# ,$WhatWeDidAI (not bare $WhatWeDidAI) in the true branch: a bare array
# variable used as a script block's output gets enumerated element-by-element
# same as Write-Output, so a 1-item array collapses to a scalar string and the
# .Count check further down throws under strict mode — found while testing
# the Ollama-down fallback with a 1-line brief section.
$WhatWeDidFinal = if ($WhatWeDidAI) { ,$WhatWeDidAI } else { Write-Log "AI rewrite unavailable for WHAT WE DID - using word-glossary fallback"; Add-PlainEnglishNotes -Lines $WhatWeDidCapped }
$BlockersFinal  = if ($BlockersAI)  { ,$BlockersAI }  else { Write-Log "AI rewrite unavailable for WHAT'S STUCK - using word-glossary fallback"; Add-PlainEnglishNotes -Lines $BlockersCapped }
$ApprovalsFinal = if ($ApprovalsAI) { ,$ApprovalsAI } else { Write-Log "AI rewrite unavailable for THINGS I NEED YOU TO OK - using word-glossary fallback"; Add-PlainEnglishNotes -Lines $ApprovalsCapped }
$NextTasksFinal = if ($NextTasksAI) { ,$NextTasksAI } else { Write-Log "AI rewrite unavailable for WHAT'S NEXT - using word-glossary fallback"; Add-PlainEnglishNotes -Lines $NextTasksCapped }

$DidSection      = if ($WhatWeDidFinal.Count -gt 0) { ($WhatWeDidFinal | ForEach-Object { "- $_" }) -join "`n" } else { "- Nothing logged in the last day. Ask me and I'll check for you." }
$BlockerSection  = if ($BlockersFinal.Count -gt 0)  { ($BlockersFinal  | ForEach-Object { "- $_" }) -join "`n" } else { "- Nothing stuck right now." }
$ApprovalSection = if ($ApprovalsFinal.Count -gt 0) { ($ApprovalsFinal | ForEach-Object { "- [ ] $_" }) -join "`n" } else { "- Nothing needs your OK right now." }
$NextSection     = if ($NextTasksFinal.Count -gt 0) { ($NextTasksFinal | ForEach-Object { "- $_" }) -join "`n" } else { "- Nothing lined up yet. Ask me and I'll check for you." }

# The raw git commit list and the internal "memory drift" check are for the
# engineering side, not for Saeed's daily read — logged for troubleshooting,
# not shown in the brief itself.
$GitCount = if ($GitLog -is [array]) { $GitLog.Count } else { 0 }
Write-Log "Git commits in last 24h: $GitCount"
Write-Log "Stale docs: $($StaleDocs.Count)"
Write-Log ($StateVerificationSection -replace "`n", " ")

$FallbackNote = if ($UsedFallbackLog) {
    $FallbackAge = [math]::Round($SessionSummaries[0].Age, 0)
    "`n(Heads up: nothing was logged in the last day, so this is using the last thing we know, from ${FallbackAge} hours ago. Normal on a weekend or a day off.)`n"
} else { "" }

$OllamaNote = if ($OllamaFallbackUsed) { "`n[Note: AI rewrite unavailable - raw summary below]`n" } else { "" }

$Report = @"
$BriefTitle - $Today - $BriefClock
$OllamaNote$FallbackNote
---

$DidLabel
$DidSection

---

$NextLabel
$NextSection

---

WHAT'S STUCK
$BlockerSection

---

THINGS I NEED YOU TO OK
$ApprovalSection

---

Behind the scenes: $GitCount code change(s) saved today. Ask me any time if you want the details.

Want more detail on anything above? Just ask me next time we talk.
"@

# ── 8. Save report ────────────────────────────────────────────────────────────
if (-not (Test-Path $ReportsDir)) { New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null }
$ReportPath = if ($Mode -eq 'Evening') { "$ReportsDir\$Today-evening.md" } else { "$ReportsDir\$Today.md" }
Set-Content -Path $ReportPath -Value $Report -Encoding UTF8
Write-Log "Report saved: $ReportPath"

# ── 8b. Evening mode: write session log if Claude didn't write one today ─────
# Guarantees the brief parser always finds bullet-format content to extract.
# Writes ONLY if no session log file exists for today (human session takes priority).
$SessionLogPath = $null
if ($Mode -eq 'Evening') {
    $TodayLogs = Get-ChildItem -Path $SessionsDir -Filter "$Today-*.md" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" }
    if (-not $TodayLogs) {
        $SessionLogPath = "$SessionsDir\$Today-1800.md"
        $NoWorkContent = @"
# SESSION SUMMARY - [$Today 18:00]
# Tool: Cowork (automated session end)
# Written by: Claude scheduled task at $BriefClock

---

## WHAT WE DID

- No human session today - automated close.

---

## BLOCKERS

$BlockerSection

---

## PENDING SAEED APPROVALS

$ApprovalSection

---

## WHAT TO DO NEXT SESSION

$NextSection

---

## GIT STATE

Latest commit: $LatestCommit
Branch: sandbox
"@
        if (-not $DryRun) {
            Set-Content -Path $SessionLogPath -Value $NoWorkContent -Encoding UTF8
            Write-Log "No session log for today - wrote automated placeholder: $SessionLogPath"
        } else {
            Write-Log "DryRun: would write session log: $SessionLogPath"
        }
    }
}

# ── 9. Commit + push ──────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Log "DryRun: skipped git commit/push"
} else {
    Write-Log "Committing to git..."
    Push-Location $RepoRoot
    try {
        git config user.email "215987900+Avamedio@users.noreply.github.com"
        git config user.name "Saeed"
        $FilesToAdd = @("PROJECT_MEMORY.md", $ReportPath)
        if ($SessionLogPath -and (Test-Path $SessionLogPath)) { $FilesToAdd += $SessionLogPath }
        git add $FilesToAdd 2>&1 | Out-Null
        git commit -m "memory: $($Mode.ToLower()) brief $Today $BriefClock" 2>&1 | Out-Null
        git push origin HEAD 2>&1 | Out-Null
        Write-Log "Git push complete"
    } catch {
        Write-Log "WARNING: Git push failed - $_"
    }

    # Evening mode: create restore tag for this day's state
    if ($Mode -eq 'Evening') {
        try {
            $RestoreTag = "restore/$Today-1800"
            $TagExists = git tag -l $RestoreTag 2>&1
            if (-not $TagExists) {
                git tag $RestoreTag 2>&1 | Out-Null
                git push origin $RestoreTag 2>&1 | Out-Null
                Write-Log "Restore tag created: $RestoreTag"

                # Keep only 3 most recent restore tags
                $AllRestoreTags = @(git tag -l "restore/*" 2>&1 | Where-Object { $_ -match "^restore/" } | Sort-Object)
                if ($AllRestoreTags.Count -gt 3) {
                    $ToDelete = $AllRestoreTags | Select-Object -First ($AllRestoreTags.Count - 3)
                    foreach ($oldTag in $ToDelete) {
                        git tag -d $oldTag 2>&1 | Out-Null
                        git push origin ":refs/tags/$oldTag" 2>&1 | Out-Null
                        Write-Log "Pruned old restore tag: $oldTag"
                    }
                }
            } else {
                Write-Log "Restore tag already exists: $RestoreTag"
            }
        } catch {
            Write-Log "WARNING: Restore tag creation failed - $_"
        }
    }
    Pop-Location
}

# ── 10. Write last_run summary ────────────────────────────────────────────────
$Summary = "COMPLETE | Sessions: $($SessionSummaries.Count) | Stale docs: $($StaleDocs.Count) | Report: $ReportPath"
Write-Log $Summary
Set-Content -Path $LogFile -Value "[$Today $NowUTC UTC] strategy_daily $Summary" -Encoding UTF8
Write-Host "Done. Report: $ReportPath" -ForegroundColor Green

# ── 11. Send report via WhatsApp ──────────────────────────────────────────────
if ($DryRun) {
    Write-Log "DryRun: skipped WhatsApp send"
} else {
    Write-Log "Sending report via WhatsApp..."
    $PythonScript = "$RepoRoot\scripts\daily\send_whatsapp.py"
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

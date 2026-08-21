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
# The -NoSend flag suppresses the forward AND the WhatsApp send, so combined_brief.ps1
# can call this script internally without recursing and without firing a second
# message - while STILL getting the PROJECT_MEMORY update, the git commit/push and
# the evening restore tag. Those are the backup safety net; before 2026-08-20 this
# script was called with -DryRun instead, which silently switched all of them off.
# (-DryRun remains a full no-op, for manual testing only.)
#
# Last updated: 2026-06-26

param(
    [ValidateSet('Morning','Evening')]
    [string]$Mode        = 'Morning',
    [switch]$DryRun,
    # Do everything EXCEPT the combined-brief forward and the WhatsApp send.
    [switch]$NoSend,
    # Which project this close is for. The script is fully parameterised so the same
    # close runs for St Marks - see combined_brief.ps1 section 6b.
    [string]$ProjectName = "Avamed (JeffLocal)",
    # LIVE-DEPLOY GUARD. Repo-relative folder whose unfinished work must never be
    # pushed: "site" for St Marks (a push republishes the live pharmacy website),
    # "dashboard" for JeffLocal (production, served live on port 8765).
    # Empty = no guard, push as normal.
    [string]$ProtectPath = "",
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
if (-not $DryRun -and -not $NoSend -and $RepoRoot -eq "C:\JeffLocal" -and (Test-Path $_CombinedScript)) {
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
# This block replaces the Cowork "Daily session end 1800" scheduled task,
# retired 2026-08-20. Cowork could not run it: it writes each task's own file
# into the folder the task points at (C:\JeffLocal\Scheduled\...), then marks
# that path a protected root and drops any folder overlapping it - so the task
# was handed no access to C:\JeffLocal at all. Confirmed by experiment, not
# fixable from settings. The session close now lives here instead.
#
# Two shapes on purpose:
#   * Commits today  -> a REAL narrative built from the day's git activity.
#                       No placeholder marker: it counts as real work.
#   * No commits     -> the stub, WITH the AUTOGEN-PLACEHOLDER marker, so the
#                       staleness banner in combined_brief.ps1 still fires if
#                       the days keep going by empty. An automated log must
#                       never silence that alarm unless real work backs it up.
$SessionLogPath = $null
if ($Mode -eq 'Evening') {
    $TodayLogs = Get-ChildItem -Path $SessionsDir -Filter "$Today-*.md" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" }
    if (-not $TodayLogs) {
        $SessionLogPath = "$SessionsDir\$Today-1800.md"

        # What actually happened today, straight from git.
        # Commits AND uncommitted tracked changes both count as work. On 2026-08-20 a
        # day of substantial work read as "no work today" purely because nothing had
        # been committed yet at the moment the log was written - accurate, but useless.
        # Saeed's instruction: count uncommitted work too, and always commit and push.
        $TodayCommits  = @()
        $FilesTouched  = @()
        $Uncommitted   = @()
        $CurrentBranch = "unknown"
        Push-Location $RepoRoot
        $ActEAP = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'   # git notices on stderr must not abort this
        try {
            $b = (git rev-parse --abbrev-ref HEAD 2>&1 | Select-Object -First 1)
            if ($b) { $CurrentBranch = ([string]$b).Trim() }
            $rawSubjects = @(git log --no-merges --since="midnight" --until="now" --pretty=format:"%s" 2>&1)
            $TodayCommits = @($rawSubjects | ForEach-Object { [string]$_ } |
                Where-Object { $_.Trim() -ne "" -and $_ -notmatch "^fatal:" })
            $rawFiles = @(git log --no-merges --since="midnight" --until="now" --name-only --pretty=format:"" 2>&1)
            $FilesTouched = @($rawFiles | ForEach-Object { [string]$_ } |
                Where-Object { $_.Trim() -ne "" -and $_ -notmatch "^fatal:" } | Sort-Object -Unique)
            # -uno = tracked files only. Untracked junk in this working tree (248 stray
            # files at last count) must never be swept into a commit.
            $rawStatus = @(git status --porcelain -uno 2>&1)
            $Uncommitted = @($rawStatus | ForEach-Object { [string]$_ } |
                Where-Object { $_.Trim() -ne "" -and $_ -notmatch "^fatal:" })
            # Drop this script's OWN bookkeeping. It rewrites PROJECT_MEMORY.md, the
            # report, the session log and HANDOFF.md as part of closing, so those always
            # show as modified. If they counted as work, the placeholder branch could
            # NEVER run and the staleness alarm would be permanently disabled - the very
            # failure this whole day was spent removing. Caught by test, 2026-08-20.
            $Uncommitted = @($Uncommitted | Where-Object {
                $pth = (($_ -replace '^\s*\S+\s+', '') -replace '"', '') -replace '\\', '/'
                ($pth -notmatch '^PROJECT_MEMORY\.md$') -and
                ($pth -notmatch '^HANDOFF\.md$') -and
                ($pth -notmatch '^docs/reports/') -and
                ($pth -notmatch '^docs/sessions/')
            })
        } catch {
            Write-Log "WARNING: could not read today's git activity - $_"
        } finally {
            $ErrorActionPreference = $ActEAP
            Pop-Location
        }
        if (@($Uncommitted).Count -gt 0) {
            Write-Log "Uncommitted tracked changes at close: $(@($Uncommitted).Count) file(s) - these WILL be committed below"
        }

        if (@($TodayCommits).Count -gt 0 -or @($Uncommitted).Count -gt 0) {
            # Real work happened. Describe it in Saeed's language, not git's.
            $DidLines  = @($TodayCommits | Select-Object -First 12)
            $Rewritten = Get-BusinessRewrite -Lines $DidLines
            $DidFinal  = if ($Rewritten) { @($Rewritten) } else { @(Add-PlainEnglishNotes -Lines $DidLines) }
            $DidSection = (@($DidFinal) | ForEach-Object { "- $_" }) -join "`n"

            $FileNote = ""
            if (@($FilesTouched).Count -gt 0) {
                $shown = (@($FilesTouched) | Select-Object -First 6) -join ", "
                $more  = if (@($FilesTouched).Count -gt 6) { ", ..." } else { "" }
                $FileNote = "`n- Files changed today: $(@($FilesTouched).Count) ($shown$more)"
            }
            if (@($Uncommitted).Count -gt 0) {
                $uShown = (@($Uncommitted) | Select-Object -First 6 |
                    ForEach-Object { ($_ -replace '^\s*\S+\s+', '') }) -join ", "
                $uMore  = if (@($Uncommitted).Count -gt 6) { ", ..." } else { "" }
                $FileNote += "`n- Work in progress committed at close: $(@($Uncommitted).Count) file(s) ($uShown$uMore)"
            }
            if (@($TodayCommits).Count -eq 0) {
                $DidLines = @("Work in progress, not yet committed when the log was written - committed at session close.")
            }

            $SessionContent = @"
# SESSION SUMMARY - [$Today 18:00]
# Tool: strategy_daily.ps1 (automated session close at $BriefClock)
# Built from the day's actual git activity - $(@($TodayCommits).Count) commit(s).

---

## WHAT WE DID

$DidSection$FileNote

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
Branch: $CurrentBranch
"@
            Write-Log "Session log built from $(@($TodayCommits).Count) commit(s) today - counts as REAL work"
        } else {
            # Nothing shipped. Keep the marker so the staleness alarm still works.
            $SessionContent = @"
# SESSION SUMMARY - [$Today 18:00]
# Tool: strategy_daily.ps1 (automated session close at $BriefClock)
# AUTOGEN-PLACEHOLDER: no session was logged and no commits were made today.
#   combined_brief.ps1 treats this marker as "no real work logged", so an
#   unnoticed outage cannot hide behind an auto-written file. DO NOT REMOVE.

---

## WHAT WE DID

- No session logged and no commits today - automated close.

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
Branch: $CurrentBranch
"@
            Write-Log "No commits today - wrote placeholder session log (marked, does not count as real work)"
        }

        if (-not $DryRun) {
            Set-Content -Path $SessionLogPath -Value $SessionContent -Encoding UTF8
            Write-Log "Session log written: $SessionLogPath"
        } else {
            Write-Log "DryRun: would write session log: $SessionLogPath"
        }
    }
}

# ── 8c. Evening mode: keep HANDOFF.md current ────────────────────────────────
# HANDOFF.md is the plain-English "where we left off" note the next session
# reads first, straight after PROJECT_MEMORY.md. Nothing automated ever wrote
# it, so it drifted weeks out of date any time no agent session ran - and the
# next session then oriented itself from a three-week-old note.
# Same rule as the session log: if a person or agent rewrote it TODAY, leave it
# alone. Otherwise write an automated one from the day's git activity, clearly
# marked as automated, so the next session is never reading something stale.
if ($Mode -eq 'Evening') {
    $HandoffPath  = Join-Path $RepoRoot "HANDOFF.md"
    $HandoffFresh = $false
    if (Test-Path $HandoffPath) {
        $HandoffFresh = ((Get-Item $HandoffPath).LastWriteTime.Date -eq (Get-Date).Date)
    }

    if ($HandoffFresh) {
        Write-Log "HANDOFF.md was already rewritten today - left as written"
    } else {
        $HandoffBranch = "unknown"
        Push-Location $RepoRoot
        try {
            $bb = (git rev-parse --abbrev-ref HEAD 2>&1 | Select-Object -First 1)
            if ($bb) { $HandoffBranch = ([string]$bb).Trim() }
        } catch { }
        Pop-Location

        $GitLines = @(@($GitLog) | ForEach-Object { [string]$_ } | Where-Object { $_.Trim() -ne "" })
        if ($GitLines.Count -eq 0 -or (($GitLines -join " ") -like "*no commits*")) {
            $CommitList = "- No commits in the last 24 hours."
        } else {
            $CommitList = (@($GitLines | ForEach-Object { "- " + $_.Trim() }) -join "`n")
        }

        $HandoffContent = @"
# HANDOFF - $ProjectName

> Rolling latest-only: overwrite in full at each session close, never append.
> Read at session start, right after PROJECT_MEMORY.md.
> Written automatically by strategy_daily.ps1 at $BriefClock on $Today, because no
> session had rewritten it by hand today. A real session close overwrites this.

Last session date: $Today (automated close at $BriefClock)
Closed by: strategy_daily.ps1 (automated)
Last commit: $LatestCommit
Branch: $HandoffBranch

## WORK SCOPE

$CommitList

## WHAT WORKED / WHAT DIDN'T

- Automated close - no human notes for today. Judge the work from the commits
  above and from docs\sessions\$Today-1800.md.

## HOW THE SESSION CLOSED

- Automated at ${BriefClock}: PROJECT_MEMORY.md updated, session log written,
  changes committed and pushed, restore tag cut.

## NEXT + BLOCKERS

$NextSection

$BlockerSection

$ApprovalSection
"@
        if (-not $DryRun) {
            Set-Content -Path $HandoffPath -Value $HandoffContent -Encoding UTF8
            Write-Log "HANDOFF.md refreshed (automated - no hand-written close today)"
        } else {
            Write-Log "DryRun: would refresh HANDOFF.md"
        }
    }
}

# ── 9. Commit + push ──────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Log "DryRun: skipped git commit/push"
} else {
    Write-Log "Committing to git..."
    Push-Location $RepoRoot
    $PushHeld = $false
    # git writes ordinary NOTICES to stderr - "LF will be replaced by CRLF" is
    # the common one, and push progress is another. Under
    # $ErrorActionPreference = "Stop", `2>&1` promotes any of them to a
    # TERMINATING error, so a harmless line-ending notice aborted the commit
    # and logged it as "Git push failed": the safety net looking like it ran
    # while doing nothing. That is the exact failure shape that hid the brief
    # outage for 8 days. Judge git on $LASTEXITCODE, which is what git actually
    # uses to report failure. Caught by test, 2026-08-20.
    $PrevEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        git config user.email "215987900+Avamedio@users.noreply.github.com" 2>&1 | Out-Null
        git config user.name "Saeed" 2>&1 | Out-Null
        $FilesToAdd = @("PROJECT_MEMORY.md", $ReportPath)
        if ($SessionLogPath -and (Test-Path $SessionLogPath)) { $FilesToAdd += $SessionLogPath }
        # HANDOFF.md carries the "where we left off" note forward to the next
        # session - commit it too, or it only ever exists on this machine.
        $HandoffToAdd = Join-Path $RepoRoot "HANDOFF.md"
        if (Test-Path $HandoffToAdd) { $FilesToAdd += $HandoffToAdd }

        # ---------------------------------------------------------------------
        # LIVE-DEPLOY GUARD (Saeed, 2026-08-21). MUST run BEFORE `git add -A` -
        # once everything is staged the folder looks clean and the guard is blind.
        #
        # Why: this close commits and pushes EVERYTHING. On St Marks a push
        # republishes the live pharmacy website within about a minute, with no
        # review step - so a half-typed price or a missing red-flag warning left
        # in site\ at 19:00 would go live to patients unreviewed. On JeffLocal a
        # push deploys nothing (dashboard\ is already live from disk on 8765), but
        # Saeed chose the same rule for both: unfinished production work means
        # nothing leaves the machine until a human has looked.
        #
        # No -uno: a brand-new half-written page is untracked, and must count too.
        # The commit still happens either way - only the push waits, so nothing
        # is ever lost.
        # ---------------------------------------------------------------------
        $ProtectedDirty = @()
        if ($ProtectPath) {
            $rawProt = @(git status --porcelain -- $ProtectPath 2>&1)
            $ProtectedDirty = @($rawProt | ForEach-Object { [string]$_ } |
                Where-Object { $_.Trim() -ne "" -and $_ -notmatch "^fatal:" })
        }

        # Saeed's instruction 2026-08-20: every session close commits AND pushes
        # EVERYTHING - new files included, so no work can be left behind.
        #
        # `git add -A` stages new, modified and deleted files. It still HONOURS
        # .gitignore, which is what makes this safe here: .env, *.sqlite, *.db, logs/,
        # *.log, *.jsonl, queue/, outputs/ and data/ are all ignored, so secrets and
        # patient data cannot be swept into the repo. Verified 2026-08-20 - do not
        # weaken .gitignore without re-checking that.
        # Stray zero-byte shell-accident files ("None", "Run", "dict[str" and friends)
        # are ignored by name at the bottom of .gitignore for the same reason.
        git add -A 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "git add -A failed (exit $LASTEXITCODE)" }

        git add $FilesToAdd 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "git add failed (exit $LASTEXITCODE)" }

        git commit -m "memory: $($Mode.ToLower()) brief $Today $BriefClock" 2>&1 | Out-Null
        $CommitExit = $LASTEXITCODE
        if ($CommitExit -eq 0) {
            Write-Log "Git commit created"
            if (@($ProtectedDirty).Count -gt 0) {
                # Guard fired. Work is committed locally; it just does not leave.
                $PushHeld = $true
                Write-Log "PUSH HELD: $ProtectPath has $(@($ProtectedDirty).Count) unfinished file(s). Committed locally, NOT pushed."
                foreach ($d in @($ProtectedDirty)) { Write-Log "    held: $d" }
                # Machine-readable signal for combined_brief.ps1, which turns it
                # into a loud line at the top of that evening's WhatsApp brief.
                Write-Output "PUSH-HELD|$ProjectName|$ProtectPath|$(@($ProtectedDirty).Count)"
            } else {
                git push origin HEAD 2>&1 | Out-Null
                if ($LASTEXITCODE -ne 0) { throw "git push failed (exit $LASTEXITCODE)" }
                Write-Log "Git push complete"
            }
        } elseif ($CommitExit -eq 1) {
            # git returns 1 for "nothing to commit" - normal, not a failure.
            Write-Log "Nothing new to commit - skipping push"
        } else {
            throw "git commit failed (exit $CommitExit)"
        }
    } catch {
        Write-Log "WARNING: git commit/push problem - $_"
    } finally {
        $ErrorActionPreference = $PrevEAP
    }

    # Evening mode: create restore tag for this day's state
    if ($Mode -eq 'Evening' -and $PushHeld) {
        # A restore point that cannot be pushed, taken over a tree containing
        # unfinished production work, is worth little and would need pushing
        # later anyway. Skip it; the next clean close cuts one.
        Write-Log "Restore tag skipped - push is held ($ProtectPath has unfinished work)"
    } elseif ($Mode -eq 'Evening') {
        # Same stderr trap as the commit block above - keep git on exit codes.
        $PrevEAP = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
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
        } finally {
            $ErrorActionPreference = $PrevEAP
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
if ($DryRun -or $NoSend) {
    $SkipReason = if ($DryRun) { "DryRun" } else { "NoSend" }
    Write-Log "${SkipReason}: skipped WhatsApp send"
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

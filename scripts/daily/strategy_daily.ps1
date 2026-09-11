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
    # Rebuild the graphify code map at close. JeffLocal only - St Marks is 23
    # static pages and does not keep one.
    [switch]$RefreshGraph,
    [string]$RepoRoot    = "C:\JeffLocal",
    [string]$ReportsDir  = "C:\JeffLocal\docs\reports",
    [string]$SessionsDir = "C:\JeffLocal\docs\sessions",
    [string]$ProjectDocs = "C:\JeffLocal\docs\project_documents",
    [string]$MemoryFile  = "C:\JeffLocal\PROJECT_MEMORY.md",
    # WHAT MAY NEVER ARRIVE ON THIS MACHINE UNSUPERVISED. Saeed asked (2026-09-10)
    # for the close to pull automatically so he stops having to do it by hand. It
    # does - but not for these paths. Everything on main has already been through a
    # PR he approved, so pulling it is delivery of approved work, not a new
    # decision. These two are different: dashboard\ IS the live production app
    # serving reception staff on 8765, and config\ drives the live Ollama/Gemma
    # pipeline. A change landing in either at 18:30 with nobody watching is a
    # deployment, and CLAUDE.md reserves that for Saeed. If an incoming change
    # touches one of these, the close does NOT pull - it says so and waits.
    [string[]]$NoAutoPullPaths = @("dashboard", "config")
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
- HARD LIMIT: 16 words per line. Shorter is better. Cut every word that is not
  carrying meaning. No preamble like "We must", "This refers to", "Please note".
- Use the past tense for work already done. Do not turn a description of what
  happened into a rule about what should happen.
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
                Where-Object { $_.Trim() -ne "" -and $_ -notmatch "^fatal:" } |
                # This close's OWN commits are not work. Without this the alarm silences
                # itself after one day: the close commits its housekeeping, then sees those
                # commits tomorrow and calls the day productive. It fired once on 22 Aug 2026
                # and never again while nobody worked for three days. Saeed, 2026-08-24.
                Where-Object { $_ -notmatch '^memory: (morning|evening) brief' })
            $rawFiles = @(git log --no-merges --since="midnight" --until="now" --name-only --pretty=format:"" 2>&1)
            $FilesTouched = @($rawFiles | ForEach-Object { [string]$_ } |
                Where-Object { $_.Trim() -ne "" -and $_ -notmatch "^fatal:" } |
                # Same reasoning for the file list: the close's own paperwork is not work.
                Where-Object {
                    $pth = ($_ -replace '\\', '/')
                    ($pth -notmatch '^PROJECT_MEMORY\.md$') -and
                    ($pth -notmatch '^HANDOFF\.md$') -and
                    ($pth -notmatch '^docs/reports/') -and
                    ($pth -notmatch '^docs/sessions/')
                } | Sort-Object -Unique)
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
# AUTOGEN-PLACEHOLDER: no session was logged and no real work was committed today.
#   (Automated housekeeping commits do not count - see strategy_daily.ps1.)
#   combined_brief.ps1 treats this marker as "no real work logged", so an
#   unnoticed outage cannot hide behind an auto-written file. DO NOT REMOVE.

---

## WHAT WE DID

- No session logged and no real work committed today - automated close.
- If this repeats for several days, nobody is working on this project. The brief will say so.

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

# ── 8d. Refresh the code map ─────────────────────────────────────────────────
# A STALE map is worse than none - it describes code that no longer exists and
# costs tokens to re-verify without saving any (CLAUDE.md says exactly this).
# Both repos' maps had drifted 3-5 weeks out of date and went unused because of
# it. Rebuilding is cheap: ~15 seconds, AST-only, no API cost. So do it nightly.
#
# graphify-out is gitignored - it is a generated index, not source. Nothing here
# reaches git; this only keeps the on-disk map current for the next session.
if ($RefreshGraph -and -not $DryRun) {
    if (-not (Get-Command graphify -ErrorAction SilentlyContinue)) {
        Write-Log "graphify not on PATH - code map refresh skipped"
    } else {
        Write-Log "Refreshing the code map (graphify update)..."
        $GraphEAP = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        Push-Location $RepoRoot
        try {
            $GraphOut = & graphify update . 2>&1 | Out-String
            $Rebuilt  = @($GraphOut -split "`n" | Where-Object { $_ -match 'Rebuilt:' }) | Select-Object -First 1
            if ($Rebuilt) { Write-Log ("Code map refreshed - " + ([string]$Rebuilt).Trim()) }
            else          { Write-Log "graphify update finished (no rebuild line in its output)" }

            # graphify writes a DATED BACKUP of itself on EVERY run (~2.5MB).
            # Left alone that is roughly 900MB a year of dead snapshots nobody
            # reads. Keep the 3 most recent and drop the rest.
            $SnapRoot = Join-Path $RepoRoot "graphify-out"
            $Snaps = @(Get-ChildItem -Path $SnapRoot -Directory -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}$' } | Sort-Object Name)
            if ($Snaps.Count -gt 3) {
                foreach ($Old in $Snaps[0..($Snaps.Count - 4)]) {
                    Remove-Item -Recurse -Force $Old.FullName -ErrorAction SilentlyContinue
                    Write-Log "Pruned old code-map snapshot: $($Old.Name)"
                }
            }
        } catch {
            # Never let the map break the close - the close matters, the map does not.
            Write-Log "WARNING: code map refresh failed - $_"
        } finally {
            $ErrorActionPreference = $GraphEAP
            Pop-Location
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
    # Set when the push to GitHub is REJECTED, which is a different thing from
    # the push guard deliberately HOLDING it. Both leave work sitting on this
    # computer; only one of them is intentional. Added 2026-09-09.
    $PushFailed = $false
    $PushFailReason = ""
    # Initialised HERE so the finally can restore it unconditionally. The earlier
    # version set $script:PrevLcAll inside the try and guarded the restore with
    # Test-Path variable:script:PrevLcAll - which relies on a scope-qualified
    # provider path resolving the way we assume on PowerShell 5.1, and nobody has
    # run 5.1 to check. Do not leave an unverified assumption in the alarm path
    # when two lines remove the question. Security Agent L-A, 2026-09-09.
    $PrevLcAll = $env:LC_ALL
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
        # SUPERSEDED 2026-09-10 - the paragraph below is no longer true on its own.
        # The close now pushes to origin/close/<date> BEFORE the real branch, so the
        # sha in a PUSH-FAILED IS already on an origin branch. combined_brief.ps1's
        # retirement check now excludes origin/close/* for exactly this reason;
        # the two must be changed together. Security Agent H3.
        #
        # LOAD-BEARING PRECONDITION - DO NOT MOVE THE PUSH OUT FROM UNDER THIS.
        # A push is only ever attempted inside this branch, i.e. immediately after
        # a commit that was just created. That is what guarantees the sha reported
        # in PUSH-FAILED below cannot ALREADY be on origin - and combined_brief.ps1
        # relies on exactly that when it retires the "did not reach GitHub" warning
        # on the evidence "this sha is now on an origin branch".
        #
        # If a future change pushes work that was NOT just committed here - a retry
        # loop, a "push any unpushed work" catch-up, a force-with-lease path - that
        # guarantee is gone and the warning could retire on stale evidence, with no
        # test failing. Change the retirement check in combined_brief.ps1 in the
        # same commit. Security Agent, 2026-09-09 round-3 review.
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
                # git translates its messages, and the classifier below matches
                # English. Force the C locale for this one call so a non-English
                # Windows does not silently fall through to the generic reason.
                # $PrevLcAll is restored in the finally below, not here: if the
                # push line throws, an inline restore is skipped and LC_ALL=C leaks
                # to the rest of the process - including back into combined_brief.ps1,
                # which invoked this script in-process. Security Agent L3.
                $env:LC_ALL = "C"

                # ─────────────────────────────────────────────────────────────
                # 1. BACKUP BRANCH FIRST - the save that can never be refused.
                #
                # Saeed, 2026-09-10, after last night: "WHY DO I HAVE TO PULL AND
                # PUSH? WHY NOT AUTOMATIC SCHEDULED TASK?" He is right. Git glues
                # together two things that should be separate: SAVING his work,
                # which must never need permission and never be refused, and
                # RECEIVING new code, which is a deployment and needs his say-so.
                # Because they were glued, every time GitHub moved ahead of his PC
                # the evening save was rejected and stayed rejected until he fixed
                # it by hand - three days lost 7-9 Sep, and again on 9 Sep.
                #
                # Nobody else ever writes to close/<date>, so this push cannot be
                # rejected as non-fast-forward. His work reaches GitHub every
                # evening whatever state main is in, with no manual step, ever.
                #
                # It still respects the push guard above: this whole block only
                # runs when $ProtectedDirty is empty. Unfinished production work
                # still means nothing leaves the machine, backup branch included.
                # ─────────────────────────────────────────────────────────────
                $CurBranch = (git rev-parse --abbrev-ref HEAD 2>$null)
                if ([string]::IsNullOrWhiteSpace($CurBranch) -or $CurBranch -eq "HEAD") { $CurBranch = "main" }
                $BackupBranch = "close/$Today"
                git push origin "HEAD:refs/heads/$BackupBranch" 2>&1 | Out-Null
                $BackupOk = ($LASTEXITCODE -eq 0)
                if ($BackupOk) {
                    Write-Log "Backup branch pushed: $BackupBranch - today's work is on GitHub regardless of $CurBranch."
                } else {
                    Write-Log "WARNING: backup branch $BackupBranch did NOT push. The work may be on this machine only."
                }

                # 2. Now the real branch.
                $PushOut  = @(git push origin HEAD 2>&1) -join " "
                # Capture it NOW. Any native command below - git rev-parse included -
                # resets $LASTEXITCODE, and the generic reason would then report
                # "exit 0" on a failed push: a banner arguing with itself, inside the
                # alarm path. Security Agent M1, 2026-09-09.
                $PushExit = $LASTEXITCODE

                # ─────────────────────────────────────────────────────────────
                # 3. AUTO-PULL, BUT ONLY WHEN IT IS SAFE.
                #
                # Saeed asked for this on 2026-09-10 and accepted the trade-off
                # explicitly. The reasoning: anything on main got there through a
                # pull request HE approved, so bringing it down is delivery of
                # already-approved work, not a fresh decision. The gate is the
                # merge, not the pull.
                #
                # The exceptions are $NoAutoPullPaths - dashboard\ and config\ -
                # where a change arriving unwatched at 18:30 really would be an
                # unsupervised deployment of the live system. If the incoming
                # change touches one of those, this does NOT pull. It says so and
                # leaves it to Saeed, exactly as before.
                #
                # Three further refusals, all deliberate:
                #   - only on a "you are behind" rejection. A network or auth
                #     failure is not fixed by pulling and must stay loud.
                #   - only if the merge is clean. A conflict is aborted at once:
                #     a half-merged production folder left overnight with nobody
                #     watching is far worse than a failed push.
                #   - only if the tree is clean afterwards, before pushing again.
                # Every refusal path falls through to the existing alarm.
                # ─────────────────────────────────────────────────────────────
                $AutoPulled   = $false
                # ALWAYS ASSIGNED before any path can read it. StrictMode turns an
                # unassigned read into a terminating error, and a crash here takes
                # the whole brief down - Saeed gets no WhatsApp message at all.
                # That defect shipped once already in this series (B1, PR #4).
                $RefuseReason = ""
                # SAEED APPROVED "the CLOSE pulls automatically". strategy_daily.ps1
                # also runs at 07:00 from the morning brief, so without this the live
                # system could change at 07:00, right before the surgery day starts -
                # scope he was never shown. Evening only until he says otherwise.
                # Security Agent M1, 2026-09-10.
                $MayAutoPull = ($Mode -eq 'Evening')
                # A detached HEAD makes $CurBranch fall back to "main", and merging
                # origin/main into a detached HEAD unattended moves the working tree
                # somewhere nobody asked for. Refuse. Security Agent L2.
                $OnRealBranch = ((git rev-parse --abbrev-ref HEAD 2>$null) -eq $CurBranch)
                if ($PushExit -ne 0 -and $PushOut -match 'non-fast-forward|fetch first|behind its remote' `
                    -and $MayAutoPull -and $OnRealBranch) {
                    try {
                        Write-Log "Push rejected as behind. Checking whether it is safe to pull automatically..."
                        git fetch origin $CurBranch 2>&1 | Out-Null
                        if ($LASTEXITCODE -ne 0) {
                            $RefuseReason = "could not reach GitHub to see what was waiting"
                            Write-Log "  Could not fetch $CurBranch - not pulling."
                        } else {
                            # Three dots: what changed on THEIR side since the point
                            # the two copies last agreed. Two dots would also list
                            # this machine's own new files and refuse every time.
                            # EVERY FLAG HERE IS LOAD-BEARING. `git diff --name-only`
                            # on its own does NOT report what it appears to report, and
                            # the Security Agent proved three separate ways past it -
                            # each one able to overwrite or DELETE the live app at
                            # 18:30 while this log line said "Safe". 2026-09-10:
                            #
                            #   --no-renames  Rename detection is ON by default and
                            #     prints ONLY the destination. A remote that renames
                            #     dashboard/app.py -> docs/app_moved.py shows up as
                            #     "docs/app_moved.py" alone, passes the check, and the
                            #     merge DELETES the live file. Renaming the whole
                            #     dashboard/ folder removes the entire production app
                            #     with no alarm. --no-renames splits a rename back into
                            #     delete-old + add-new, so the protected path reappears.
                            #   -c core.quotePath=false  Git QUOTES any non-ASCII path
                            #     by default: config/café.json arrives as the literal
                            #     "config/\303\251.json", starting with a quote
                            #     character, so -like 'config/*' is false. One accented
                            #     filename would defeat the guard permanently.
                            #   -z  NUL-separated, so a newline in a filename cannot
                            #     forge an extra entry, and no quoting is reintroduced.
                            #
                            # Do not remove any one of them thinking the others cover it.
                            $IncRaw   = @(git -c core.quotePath=false diff --no-renames --name-only -z "HEAD...origin/$CurBranch" 2>$null)
                            $DiffOk   = ($LASTEXITCODE -eq 0)
                            $Incoming = @((@($IncRaw) -join "") -split "`0" |
                                          ForEach-Object { [string]$_ } |
                                          Where-Object { $_.Trim() -ne "" })

                            # CROSS-CHECK THE PARSE, BECAUSE IT FAILS OPEN.
                            # -z is right, but it moved this from "split on newlines"
                            # - which every PowerShell does identically - to
                            # "reassemble native output and split on NUL", which has
                            # never executed on Windows PowerShell 5.1, the only place
                            # this actually runs. If 5.1 drops the NUL bytes the whole
                            # list collapses into ONE concatenated string, so
                            # "docs/harmless.md" + "dashboard/app.py" becomes
                            # "docs/harmless.mddashboard/app.py", which does not start
                            # with "dashboard/" - and the guard prints
                            # "Safe: 1 incoming file(s)... Merging." That is the exact
                            # sentence that was in the log when the live app was
                            # deleted in testing. Silent, and intermittent, since it
                            # only bites when the protected path is not first.
                            #
                            # The newline form is parsed identically everywhere, so a
                            # disagreement in COUNT means the parse cannot be trusted.
                            # Refuse rather than assume - the same principle as $DiffOk.
                            # Security Agent S1, 2026-09-10.
                            $IncPlain = @(git -c core.quotePath=false diff --no-renames --name-only "HEAD...origin/$CurBranch" 2>$null |
                                          ForEach-Object { [string]$_ } |
                                          Where-Object { $_.Trim() -ne "" })
                            $ParseOk = (@($Incoming).Count -eq @($IncPlain).Count)
                            $Blocked = @($Incoming | Where-Object {
                                $f = ($_ -replace '\\', '/')
                                $hit = $false
                                foreach ($prot in @($NoAutoPullPaths)) {
                                    $pp = ([string]$prot -replace '\\', '/').Trim('/')
                                    if ($pp -and ($f -eq $pp -or $f -like "$pp/*")) { $hit = $true }
                                }
                                $hit
                            })
                            if (-not $ParseOk) {
                                $RefuseReason = "the list of incoming changes could not be read reliably"
                                Write-Log "  NOT pulling - the two readings of the incoming list disagree ($(@($Incoming).Count) vs $(@($IncPlain).Count)). Refusing rather than trusting either."
                            } elseif (-not $DiffOk) {
                                # An empty list from a FAILED diff is not evidence of
                                # safety - it is absence of evidence, and it would read
                                # as "0 incoming files, none protected, merging". The
                                # guard must be satisfied by proof, never by an error.
                                # Security Agent M3, 2026-09-10.
                                $RefuseReason = "could not read what was waiting on $CurBranch"
                                Write-Log "  NOT pulling - the incoming-change list could not be read. Refusing rather than assuming."
                            } elseif (@($Blocked).Count -gt 0) {
                                $RefuseReason = "the incoming changes touch the live system ($(@($Blocked)[0]))"
                                Write-Log "  NOT pulling - $(@($Blocked).Count) incoming change(s) touch protected paths:"
                                foreach ($b in @($Blocked)) { Write-Log "      $b" }
                            } else {
                                Write-Log "  Safe: $(@($Incoming).Count) incoming file(s), none under $($NoAutoPullPaths -join ', '). Merging."
                                git merge --no-edit "origin/$CurBranch" 2>&1 | Out-Null
                                if ($LASTEXITCODE -ne 0) {
                                    # Abort immediately. Never leave a half-merged
                                    # production folder behind at 18:30.
                                    git merge --abort 2>&1 | Out-Null
                                    $RefuseReason = "the changes clash with tonight's work and need a person to decide"
                                    Write-Log "  Merge CONFLICTED - aborted, nothing changed on disk. Leaving this to Saeed."
                                } else {
                                    $PushOut2  = @(git push origin HEAD 2>&1) -join " "
                                    $PushExit2 = $LASTEXITCODE
                                    if ($PushExit2 -eq 0) {
                                        $AutoPulled = $true
                                        Write-Log "AUTO-PULL SUCCEEDED: pulled $(@($Incoming).Count) file(s) from $CurBranch and pushed. No manual step needed."
                                    } else {
                                        $RefuseReason = "the changes came down cleanly but sending the work back up still failed"
                                        Write-Log "  Pulled cleanly but the push still failed: $PushOut2"
                                    }
                                }
                            }
                        }
                    } catch {
                        $RefuseReason = "the automatic catch-up hit an unexpected error"
                        Write-Log "  Auto-pull attempt failed - $_. Falling through to the alarm."
                        # Best effort: never leave a merge half-done.
                        git merge --abort 2>&1 | Out-Null
                    }
                }

                if ($PushExit -ne 0 -and -not $AutoPulled) {
                    # DO NOT throw. A throw here lands in the catch below, which
                    # only writes to a log file nobody reads, and the close then
                    # reports itself as a success. That is exactly how 7-9 Sep 2026
                    # went: three closes committed locally, every push was rejected
                    # as non-fast-forward, and every alarm said the system was fine.
                    # Saeed found it by hand two days later. Instead, name the
                    # failure and hand it to the brief, the same way PUSH-HELD does.
                    $PushFailed = $true
                    # The branch this machine is ACTUALLY on. The push above is
                    # `git push origin HEAD` - branch-agnostic on purpose - so the
                    # advice must be too. Hardcoding "main" would tell Saeed to
                    # merge main into whatever branch he is on and push main.
                    # Security Agent H3, 2026-09-09.
                    $CurBranch = (git rev-parse --abbrev-ref HEAD 2>$null)
                    if ([string]::IsNullOrWhiteSpace($CurBranch) -or $CurBranch -eq "HEAD") { $CurBranch = "main" }
                    $PushFailReason =
                        if     ($PushOut -match 'non-fast-forward|fetch first|behind its remote') {
                            "this computer is behind GitHub - someone else changed it. Fix: git pull --no-edit origin $CurBranch, then git push origin $CurBranch"
                        } elseif ($PushOut -match 'could not resolve host|unable to access|Connection|timed out|network') {
                            "could not reach GitHub - check the internet connection"
                        } elseif ($PushOut -match 'Authentication|denied|403|401') {
                            "GitHub refused the login for this computer"
                        } else {
                            "git push failed (exit $PushExit)"
                        }
                    Write-Log "PUSH FAILED: $PushFailReason"
                    Write-Log "  git said: $PushOut"
                    # NAME THE COMMIT THAT DID NOT MAKE IT. A bare timestamp proves
                    # only "a push happened", never "THIS work reached GitHub" - so
                    # a later push of a DIFFERENT branch, or a git reset --hard that
                    # discards the work entirely, would otherwise be accepted as
                    # evidence and retire a warning that is still true.
                    # Security Agent H2, 2026-09-09.
                    $FailedSha = (git rev-parse HEAD 2>$null)
                    if ([string]::IsNullOrWhiteSpace($FailedSha)) { $FailedSha = "" }
                    # A pipe inside the reason would shift every field after it.
                    # The reasons above contain none today; this makes that true
                    # by construction rather than by inspection.
                    $PushFailReason = ([string]$PushFailReason) -replace '\|', ' '
                    # WHICH ALARM? This depends on whether the work is actually
                    # at risk, and since the backup branch above that is no longer
                    # the same question as "did the main push succeed".
                    #
                    #   Backup pushed + merely behind  -> the work IS on GitHub.
                    #     "YOUR WORK DID NOT REACH GITHUB" would be false, and a
                    #     banner that repeats something untrue is how Saeed learns
                    #     to stop reading banners. Quiet signal instead.
                    #   Backup failed, or a network/auth failure -> the work really
                    #     may be on this machine only. Loud, exactly as before.
                    #
                    # This also avoids a trap: the retirement check in
                    # combined_brief.ps1 asks "is this sha on an origin branch?".
                    # The backup branch IS an origin branch, so a PUSH-FAILED
                    # raised here would retire itself the same evening - an alarm
                    # silently switching itself off, which is the precise failure
                    # this whole file exists to prevent.
                    $MerelyBehind = ($PushOut -match 'non-fast-forward|fetch first|behind its remote')
                    if ($MerelyBehind -and $BackupOk) {
                        Write-Log "Reporting as BEHIND-REMOTE, not PUSH-FAILED: today's work is safe on $BackupBranch."
                        # SAY THE REAL REASON. This message used to state one
                        # hardcoded cause - "the incoming changes touch the live
                        # system" - on every path, including a fetch failure and an
                        # aborted conflict. In the conflict case it then told Saeed
                        # to run a pull that would conflict for him too, with the
                        # wrong explanation in hand. Security Agent M2, 2026-09-10.
                        $Why = if ($RefuseReason) { $RefuseReason }
                               elseif (-not $MayAutoPull) { "the automatic catch-up only runs at the evening close" }
                               elseif (-not $OnRealBranch) { "this computer is not on a normal branch" }
                               else { "it could not be brought down automatically" }
                        # Pipes would shift every field after them - the same
                        # sanitising $PushFailReason already gets. Security Agent L3.
                        $Why = ([string]$Why) -replace '\|', ' '
                        Write-Output "BEHIND-REMOTE|$ProjectName|this computer is behind GitHub, so tonight's work did not go onto $CurBranch - but it IS saved on GitHub as $BackupBranch, so nothing is at risk. Not pulled automatically because $Why. To catch up: git pull --no-edit origin $CurBranch, then git push origin $CurBranch|$BackupBranch"
                    } else {
                        # Machine-readable signal for session_close.ps1 and the brief.
                        # Format: PUSH-FAILED|<project>|<reason>|<sha>
                        Write-Output "PUSH-FAILED|$ProjectName|$PushFailReason|$($FailedSha.Trim())"
                    }
                } else {
                    Write-Log "Git push complete"
                    # RECORD THE SUCCESS, so a stale failure can be retired.
                    # Saeed's instruction 2026-09-09: the "did not reach GitHub"
                    # banner must STOP once the work reaches GitHub. Unlike the
                    # close-failure banner - whose claim stays true until the close
                    # is re-run - this one becomes FALSE the moment a later push
                    # succeeds, and a warning that repeats something untrue is how
                    # Saeed learns to stop reading warnings.
                    #
                    # Fixed path on purpose: the brief reads one close-state folder
                    # for BOTH projects, and this file must land where it looks.
                    # Same hardcoding as the $_CombinedScript path at the top of
                    # this script. logs\ is gitignored, so it never reaches the repo.
                    try {
                        $OkDir = "C:\JeffLocal\logs\close-state"
                        if (-not (Test-Path $OkDir)) { New-Item -ItemType Directory -Path $OkDir -Force | Out-Null }
                        $OkSlug = ($ProjectName -replace '[\\/:*?"<>|]', '_')
                        # Record WHAT was pushed, not only when. The brief proves a
                        # retirement against this sha; a timestamp alone cannot tell
                        # "Friday's work arrived" from "some other branch arrived".
                        # Security Agent H2, 2026-09-09.
                        $OkSha = (git rev-parse HEAD 2>$null)
                        if ([string]::IsNullOrWhiteSpace($OkSha)) { $OkSha = "" }
                        Set-Content -Path (Join-Path $OkDir "last-push-ok-$OkSlug.txt") `
                                    -Value ((Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "|" + $OkSha.Trim()) -Encoding UTF8
                    } catch {
                        # Never let bookkeeping break a close that just succeeded.
                        Write-Log "WARNING: could not record the successful push - $_"
                    }
                }
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
        $env:LC_ALL = $PrevLcAll
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
                # CHECK THE EXIT CODE. This used to log "Restore tag created"
                # unconditionally - a false success statement inside the very alarm
                # path being hardened. In the network and auth failure classes the
                # tag push fails too, and then NOTHING has left this machine.
                # Security Agent M3, 2026-09-09.
                git push origin $RestoreTag 2>&1 | Out-Null
                if ($LASTEXITCODE -ne 0) {
                    $PushFailed = $true
                    Write-Log "WARNING: restore tag $RestoreTag was created locally but NOT pushed."
                    # ITS OWN SIGNAL NAME, for two reasons. First, a later branch
                    # push does not push this tag, so the branch-push stamp must
                    # never be allowed to retire this line - it would leave a day
                    # with no remote restore point and no alarm, and the next clean
                    # close would then prune the local-only tag away.
                    # Second, the old wording claimed "nothing from today has left
                    # this computer", which is FALSE in the case that produces this
                    # line on its own: the branch push SUCCEEDED. An alarm that
                    # overstates is the same trust problem this week's work exists
                    # to fix. Security Agent H1, 2026-09-09.
                    # Say NOTHING about the commits here. This block is reached even
                    # when nothing was committed - in which case no push was attempted
                    # and "today's commits reached GitHub" would be false. Claim only
                    # what this signal actually knows. Security Agent L4, 2026-09-09.
                    Write-Output "TAG-PUSH-FAILED|$ProjectName|the restore point $RestoreTag did not reach GitHub - there is no snapshot to roll back to for that day|$RestoreTag"
                } else {
                    Write-Log "Restore tag created and pushed: $RestoreTag"
                }

                # Keep only 3 most recent restore tags.
                # NOT while a push is failing: pruning the only remote anchors
                # during a save outage is a bad instinct to leave in the code, even
                # though the remote deletes would themselves fail. Security Agent M3.
                $AllRestoreTags = @(git tag -l "restore/*" 2>&1 | Where-Object { $_ -match "^restore/" } | Sort-Object)
                if ($PushFailed) {
                    Write-Log "Skipping restore-tag prune - a push has failed, keeping every remote anchor."
                } elseif ($AllRestoreTags.Count -gt 3) {
                    $ToDelete = $AllRestoreTags | Select-Object -First ($AllRestoreTags.Count - 3)
                    foreach ($oldTag in $ToDelete) {
                        git tag -d $oldTag 2>&1 | Out-Null
                        git push origin ":refs/tags/$oldTag" 2>&1 | Out-Null
                        Write-Log "Pruned old restore tag: $oldTag"
                    }
                }

            } else {
                # THE TAG EXISTS LOCALLY - BUT IS IT ON GITHUB? This used to stop
                # here. The close overwrites the day's marker with Set-Content, so a
                # hand-run `session_close.ps1 -Force` later the same day rewrote the
                # marker while this branch silently declined to re-emit the alarm.
                # Net result: no remote restore point for that day, and no alarm
                # anywhere. A PUSH-FAILED recurs on a retry; TAG-PUSH-FAILED is now
                # the ONLY carrier of this fact, so it must too.
                # Security Agent L3, 2026-09-09.
                $RemoteTag = @(git ls-remote --tags origin "refs/tags/$RestoreTag" 2>$null)
                $LsExit    = $LASTEXITCODE
                $RemoteTag = @(@($RemoteTag) | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) })
                if ($LsExit -eq 0 -and @($RemoteTag).Count -gt 0) {
                    Write-Log "Restore tag already exists and is on GitHub: $RestoreTag"
                } else {
                    Write-Log "Restore tag $RestoreTag exists locally but is NOT on GitHub - retrying the push."
                    git push origin $RestoreTag 2>&1 | Out-Null
                    if ($LASTEXITCODE -ne 0) {
                        $PushFailed = $true
                        Write-Log "WARNING: restore tag $RestoreTag still did not reach GitHub."
                        Write-Output "TAG-PUSH-FAILED|$ProjectName|the restore point $RestoreTag did not reach GitHub - there is no snapshot to roll back to for that day|$RestoreTag"
                    } else {
                        Write-Log "Restore tag pushed on retry: $RestoreTag"
                    }
                }
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

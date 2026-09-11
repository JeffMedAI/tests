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

# ONE clock reading for the whole run. Separate Get-Date calls can straddle
# midnight and disagree with each other about what day it is, and the close
# marker is filed by day. Security Agent H3, 2026-09-07.
$Now    = Get-Date
$Today  = $Now.ToString("yyyy-MM-dd")
$NowUTC = (Get-Date).ToUniversalTime().ToString("HH:mm")
$LogFile = "C:\JeffLocal\scripts\daily\combined_brief_last_run.log"

# Repo roots, named once. The push-failure retirement check below asks git
# whether a commit actually reached a remote, so it needs the working copy for
# whichever project the signal names. Declared here rather than inline so the
# check is testable off this machine. Security Agent H2, 2026-09-09.
$AvamedRepoRoot  = "C:\JeffLocal"
$StMarksRepoRoot = "C:\JeffLocal\SMCPHARMA"

# ── Deliberately paused projects ─────────────────────────────────────────────
# Saeed's instruction 2026-09-07. A project listed here is paused ON PURPOSE, so
# "no work logged" is the expected state, not a fault. It gets a quiet one-line
# note instead of the full out-of-date banner.
#
# This ONLY silences the "nobody has worked on this" alarm. It does NOT silence
# the close-failure alarm: if the 18:30 close does not run or fails, the loud
# day-named close-failure banner ("FRIDAY'S SESSION CLOSE DID NOT COMPLETE")
# still fires for both projects,
# paused or not. Those are different problems and must stay separately visible.
#
# TO UN-PAUSE A PROJECT: delete its line below. The loud staleness banner comes
# straight back. Keep the reason text current - it is printed to Saeed verbatim.
$PausedProjects = @{
    "Pharmacy website (St Marks)" = "awaiting pharmacist sign-off"
}

# How long a project may sit paused before the quiet note starts asking Saeed to
# confirm it is still correct. One week, Saeed's instruction 2026-09-07 - a pause
# he set and forgot must not become a permanent blind spot.
$PausedNagAfterHours = 24 * 7

# ── How long a quiet project stays quiet ─────────────────────────────────────
# SAEED'S DECISION, 2026-09-09: the loud "PART OF THIS BRIEF IS OUT OF DATE"
# banner starts on the THIRD day, not the first. One or two quiet days are
# ordinary - a day off, or a day spent on the other project - and shouting about
# them is how a banner stops being believed. Days one and two still get a plain
# one-line note, so a real outage is still visible from the first morning; it
# just does not arrive as an emergency until it looks like one.
#
# COUNTED IN MISSED WEEKDAY CLOSES, NOT IN WALL-CLOCK HOURS. The first version of
# this used a flat 72 hours and so counted the weekend: a Thursday log with nobody
# working Friday went loud on SUNDAY, when no close was due and no work was
# expected - after only two working days. That is the same cry-wolf shape this
# threshold exists to remove, moved from a Tuesday to a Sunday. The comment on
# Get-LastExpectedCloseTime already said it: the right question is never "how many
# hours" but "how many closes have come and gone". Security Agent F2, 2026-09-09.
#
# This does NOT loosen anything else. A project whose folder cannot be read is
# still loud immediately, and a project with no session log at all is still loud
# immediately.
$StaleLoudAfterCloses = 3

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

# ---------------------------------------------------------------------------
# Was this session log written by the automation (strategy_daily.ps1 /
# session_close.ps1) rather than by a human?
#
# It matters because strategy_daily.ps1 ALREADY puts its WHAT WE DID lines
# through Get-BusinessRewrite before writing them. Rewriting them a second time
# here ran every line through a small local model TWICE, and the second pass
# drifted off the facts: on 2026-09-10 the commit subject "stop the close if the
# incoming file list cannot be parsed" reached Saeed's phone as "If we cannot
# reliably understand the incoming file list, the process must be stopped" - a
# design rule dressed up as a day's work. Saeed flagged it. Fix 3, 2026-09-11.
#
# Header-only match, for the same reason Test-IsPlaceholderLog is header-only:
# a real session log that DISCUSSES the automation must not be mistaken for one.
function Test-IsAutoWrittenLog {
    param([string]$Content)
    if ([string]::IsNullOrWhiteSpace($Content)) { return $false }
    $Head = (@($Content -split "`n") | Select-Object -First 10) -join "`n"
    return ($Head -match '(?m)^\s*#\s*Tool:\s*(strategy_daily|session_close)\.ps1')
}

# ---------------------------------------------------------------------------
# Is this line a bare "nothing to report" placeholder?
#
# Exact match only, with a short allowed tail. On 2026-09-10 the brief said
# "Work is progressing without any current issues." and then listed three real
# blockers underneath, because the source log carried a "None" line NEXT TO
# real ones and each line was rewritten separately. Fix 2, 2026-09-11.
#
# Deliberately strict. A loose "starts with no/none" test would eat real
# blockers like "No GPhC number yet" - which is a blocker, not an absence of
# one. If in doubt this returns $false and the line is KEPT.
function Test-IsNoneLine {
    param([string]$Line)
    $t = ([string]$Line).Trim().TrimEnd('.', '!', ';', ',').Trim()
    if ($t.Length -eq 0) { return $false }
    if ($t.Length -gt 40) { return $false }
    return ($t -match '^(?i)(none|n/a|na|nothing|no blockers?|nothing stuck|nothing blocking|nothing outstanding|nothing pending|nothing to report|no issues?|no current blockers?|unblocked|all clear)( right now| at present| currently| today| so far| yet)?$')
}

# Drop bare "none" lines from a section. If that empties the section the caller
# renders its own standard "Nothing stuck right now." placeholder, so the wording
# stays consistent and a contradiction can never be printed.
function Remove-NoneLines {
    param([string[]]$Lines)
    $in = @(@($Lines) | ForEach-Object { [string]$_ })
    if (@($in).Count -eq 0) { return ,$in }
    $kept = @($in | Where-Object { -not (Test-IsNoneLine -Line $_) })
    return ,$kept
}

# Is this line a ticked checkbox - i.e. already DONE?
#
# The parser below strips the box off every line with `\[.\]`, which matches
# "[x]" and "[ ]" identically, and the renderer then puts a FRESH EMPTY box
# back on. So anything Saeed had already signed off came back to his phone
# every night asking to be signed off again, for months. Fix 1, 2026-09-11.
function Test-IsDoneLine {
    param([string]$Line)
    return (([string]$Line).Trim() -match '^(?:\d+\.\s*)?-?\s*\[[xX]\]')
}

# When did the most recent session close FALL DUE? (weekday 18:30, per
# session_close.ps1). Everything about "is this project overdue" is measured
# against this, not against a flat 24 hours.
#
# A flat 24h is wrong every weekend: Friday's 18:30 log is 25h old by Saturday
# evening and 61h old by Monday's 07:00 brief, so the loud out-of-date banner
# fired on the Saturday evening, Sunday morning, Sunday evening and Monday
# morning briefs - about 156 times a year - for a gap that is entirely by
# design. Security Agent H4, 2026-09-07.
#
# The right question is not "is it the weekend" but "has a close been due since
# this project last logged anything". If none has, there is nothing to report.
function Get-LastExpectedCloseTime {
    param([datetime]$Now)
    $t = $Now.Date.AddHours(18).AddMinutes(30)
    if ($t -gt $Now) { $t = $t.AddDays(-1) }
    while ($t.DayOfWeek -eq [DayOfWeek]::Saturday -or $t.DayOfWeek -eq [DayOfWeek]::Sunday) {
        $t = $t.AddDays(-1)
    }
    return $t
}

# Roll back N weekday 18:30 closes from the last one that fell due. This is the
# unit the volume decision is made in - see $StaleLoudAfterCloses above for why
# hours are the wrong unit. Security Agent F2, 2026-09-09.
function Get-CloseTimeNBack {
    param([datetime]$From, [int]$Closes)
    $t = $From
    for ($i = 0; $i -lt $Closes; $i++) {
        $t = $t.AddDays(-1)
        while ($t.DayOfWeek -eq [DayOfWeek]::Saturday -or $t.DayOfWeek -eq [DayOfWeek]::Sunday) {
            $t = $t.AddDays(-1)
        }
    }
    return $t
}

# How many weekday closes have come and gone since this project last logged
# anything. ONE counter, used by BOTH the quiet note and the loud banner: the
# note promises "this becomes a warning at 3 working days" and the banner used to
# answer, one day later, "nothing new logged for 4 day(s)" - a different, larger
# number in the message that the previous message promised. At the exact moment
# the design asks Saeed to trust the count, the two numbers disagreed.
# Security Agent C1, 2026-09-09.
# The counter is bounded so a very old log cannot spin it. Anything at or above
# this is reported as "more than N", never as N: saying "99 working days" when the
# truth is 1,745 is a false number inside an alarm, which is the exact fault this
# whole file exists to avoid. Found while testing C1, 2026-09-09.
$ClosesCountCap = 99

function Get-ClosesMissed {
    param([datetime]$Since, [datetime]$LastDue, [int]$Cap = $script:ClosesCountCap)
    $n = 0
    $t = $LastDue
    while ($n -lt $Cap -and $Since -lt $t) {
        $n++
        $t = Get-CloseTimeNBack -From $t -Closes 1
    }
    return $n
}

# Is this commit on a REAL origin branch (not a close/<date> backup)? Factored
# out so the same proof can be re-run after the morning brief's own git safety
# net has pushed - see the re-check after section 6b. Security Agent S2,
# 2026-09-10. Returns $true only on a clean, positive answer; every error,
# empty result or unreachable repo returns $false, which KEEPS the warning.
function Test-WorkOnOrigin {
    param([string]$Sha, [string]$RepoRoot)
    if ($Sha -notmatch '^[0-9a-fA-F]{7,40}$') { return $false }
    if (-not (Test-Path $RepoRoot)) { return $false }
    $PrevEAPGit = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $OnRemote = @(git -C $RepoRoot branch -r --contains $Sha --list 'origin/*' 2>$null |
                      ForEach-Object { [string]$_ } |
                      Where-Object { ($_ -replace '^\s*', '') -notlike 'origin/close/*' })
        $GitExit  = $LASTEXITCODE
        $OnRemote = @(@($OnRemote) | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) })
        return ($GitExit -eq 0 -and @($OnRemote).Count -gt 0)
    } catch {
        # SAY WHICH IT WAS. Without this the caller logs "is NOT on any origin
        # branch", when the truth is "I could not ask" - same alarm, but it sends
        # whoever debugs it on the day to the wrong place. Security Agent G3.
        Write-Log "Could not ask git whether $Sha is on origin (repo $RepoRoot) - treating as NOT arrived, warning kept. $_"
        return $false
    } finally { $ErrorActionPreference = $PrevEAPGit }
}

function Repo-ForProject {
    param([string]$ProjectField)
    if ($ProjectField -match 'STMARKS|SMCPHARMA|St Marks') { return $StMarksRepoRoot }
    return $AvamedRepoRoot
}

function Format-StaleAge {
    param([double]$Hours)
    $Days = [math]::Floor($Hours / 24)
    if ($Days -ge 1) { return "$Days day(s)" }
    return "$Hours hour(s)"
}

# Loud line - for a project that is NOT paused and so should have work logged.
function Format-StaleLine {
    param([string]$Name, [double]$Hours, [string]$LogName, [int]$Closes = 0)
    if ($Hours -ge 99999) { return "!!   $Name : NO session log has ever been found" }
    $Src = if ($LogName) { " - still showing $LogName" } else { "" }
    # LEAD WITH THE SAME UNIT THE QUIET NOTE PROMISED. The calendar figure is kept
    # after it because it is genuinely useful - it is what a person checks against
    # a diary - but it must never be the ONLY number, or it silently contradicts
    # the note that preceded it. Security Agent C1, 2026-09-09.
    if ($Closes -gt 0) {
        $CloseWord = if ($Closes -ge $script:ClosesCountCap) { "more than $script:ClosesCountCap working days" }
                     elseif ($Closes -eq 1) { "1 working day" }
                     else { "$Closes working days" }
        return "!!   $Name : nothing new logged for $CloseWord ($(Format-StaleAge -Hours $Hours) ago)$Src"
    }
    return "!!   $Name : nothing new logged for $(Format-StaleAge -Hours $Hours)$Src"
}

# Quiet line - for a project Saeed has deliberately paused. One sentence, no
# banner, no shouting. Saeed's instruction 2026-09-07: an idle project he already
# knows about must not look like a broken system.
function Format-PausedLine {
    param([string]$Name, [string]$Reason, [double]$Hours, [switch]$CloseRan)
    $Age    = if ($Hours -ge 99999) { "no session log yet" }
              else { "nothing new logged for $(Format-StaleAge -Hours $Hours)" }
    # Say only what the marker evidences: that the 18:30 close ran. It does NOT
    # evidence that the project's close did useful work, so do not say "normally".
    # Security Agent condition C2, 2026-09-07.
    $Closed = if ($CloseRan) { " Today's 18:30 close ran." } else { "" }
    $Line   = "Note: $Name is paused on purpose ($Reason) - $Age.$Closed"

    # After a week, stop being merely informative and ask. Saeed's instruction
    # 2026-09-07: a pause must never quietly become permanent. This line is the
    # only thing standing between "deliberately paused" and "silently forgotten",
    # so it asks a direct question rather than restating the age again.
    # The 99999 sentinel means "no real session log has ever been found", not an
    # age. Feeding it to Format-StaleAge printed "Paused for 4166 day(s)" into
    # Saeed's WhatsApp message. Security Agent M1, 2026-09-07.
    if ($Hours -ge 99999) {
        $Line += [Environment]::NewLine +
                 "      -> Paused, and no session log has ever been found for it. Is this still correct?" +
                 [Environment]::NewLine +
                 "         Tell Claude to un-pause it or change the reason, next time you talk."
    } elseif ($Hours -ge $PausedNagAfterHours) {
        $Line += [Environment]::NewLine +
                 "      -> Paused for $(Format-StaleAge -Hours $Hours) now. Is this still correct?" +
                 [Environment]::NewLine +
                 "         Tell Claude to un-pause it or change the reason, next time you talk."
    }
    return $Line
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

    # ── Can we even see this project's session logs? ─────────────────────────
    # Two failure modes, both of which used to end in silence (Security Agent
    # finding H1, 2026-09-07):
    #   - Folder MISSING: the old code skipped the staleness check entirely, so
    #     $IsStale stayed $false and NO warning was produced for that project.
    #   - Folder PRESENT BUT UNREADABLE: Get-ChildItem threw under
    #     $ErrorActionPreference = "Stop", outside any try, killing the script -
    #     so no brief was sent at all, to anyone, with no error anywhere Saeed
    #     would see it.
    # Both are the shape of the 11-19 Aug 2026 outage: C:\JeffLocal unreachable.
    # "I cannot see this project" is now its own loud state, never "all fine".
    $Unreachable       = $false
    $UnreachableReason = ""
    $AllSessions       = @()
    if (-not (Test-Path $SessionsDir)) {
        $Unreachable       = $true
        $UnreachableReason = "the folder does not exist"
        Write-Log "UNREACHABLE: $ProjectLabel - session folder missing at $SessionsDir"
    } else {
        try {
            $AllSessions = @(Get-ChildItem -Path $SessionsDir -Filter "*.md" -ErrorAction Stop |
                Where-Object { $_.Name -notlike "SESSION_TEMPLATE*" } |
                Sort-Object LastWriteTime -Descending)
        } catch {
            $Unreachable       = $true
            $UnreachableReason = "the folder cannot be read"
            Write-Log "UNREACHABLE: $ProjectLabel - cannot read $SessionsDir - $_"
        }
    }

    $SessionSummaries = @()
    $RealLogCount     = 0
    if (-not $Unreachable) {
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
    $FallbackNote   = ""
    $IsStale        = $false
    $StaleHours     = 0
    $StaleLogName   = ""
    # The exact write time of the newest REAL log, or $null if there is none.
    # $StaleHours is rounded to whole hours and is fine for display, but "is this
    # project overdue" is decided by comparing this against the last close that
    # fell due - an exact comparison with no rounding and no slack to be wrong
    # inside. Security Agent M3, 2026-09-07.
    $NewestRealTime = $null
    if ($Unreachable) {
        # Nothing can be measured, so nothing may be assumed. The banner block
        # treats this separately and always loudly - see $UnreachableParts.
        $FallbackNote = "(CANNOT READ THIS PROJECT'S SESSION LOGS - $UnreachableReason)"
    } elseif ($RealLogCount -eq 0) {
        $IsStale = $true
        $Candidates = @($AllSessions)
        $NewestReal = $null
        foreach ($c in $Candidates) {
            if (-not (Test-IsPlaceholderLog -Content (Get-Utf8FileText -Path $c.FullName))) {
                $NewestReal = $c
                break
            }
        }
        if ($NewestReal) {
            $NewestRealTime = $NewestReal.LastWriteTime
            $StaleHours     = [math]::Round(((Get-Date) - $NewestReal.LastWriteTime).TotalHours, 0)
            $StaleLogName   = $NewestReal.Name
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
    # Fix 3 - WHAT WE DID lines that the automation already rewrote are held
    # apart from human-written ones, so they are not sent through the local
    # model a second time. See Test-IsAutoWrittenLog.
    $WhatWeDidAuto = @()
    # True only if EVERY log read was an autogen placeholder. Their boilerplate
    # explains the alarm mechanism, which is not Saeed's day's work - it is
    # replaced with one plain line further down.
    $AnyRealContent  = $false
    $SawPlaceholder  = $false
    # Fix 1 - how many already-ticked items were dropped, for the run log.
    $DoneDropped = 0

    foreach ($session in $SessionSummaries) {
        $lines  = $session.Content -split "`n"
        $inDid  = $false; $inBlock = $false; $inApproval = $false; $inNext = $false
        $IsAuto        = Test-IsAutoWrittenLog -Content $session.Content
        $IsPlaceholder = Test-IsPlaceholderLog  -Content $session.Content
        if ($IsPlaceholder) { $SawPlaceholder = $true } else { $AnyRealContent = $true }

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

                # Fix 1 - an item Saeed has ALREADY ticked is done. It must not
                # come back as a fresh empty box asking for the same approval.
                # Only the checkbox sections are filtered: a "[x]" inside WHAT
                # WE DID is a record of work and stays.
                $IsDone = Test-IsDoneLine -Line $clean

                if ($inDid) {
                    # Fix 3 - placeholder boilerplate is dropped here and one
                    # short line is substituted after the loop.
                    if     ($IsPlaceholder) { }
                    elseif ($IsAuto)        { $WhatWeDidAuto += $stripped }
                    else                    { $WhatWeDid     += $stripped }
                }
                if ($inBlock)    { $Blockers  += $stripped }
                if ($inApproval) { if ($IsDone) { $DoneDropped++ } else { $Approvals  += $stripped } }
                if ($inNext)     { if ($IsDone) { $DoneDropped++ } else { $NextTasks  += $stripped } }
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
    # Fix 2 - a bare "None" sitting next to real items made the brief contradict
    # itself in one breath ("Work is progressing without any current issues",
    # then three real blockers - 2026-09-10). Drop the none-lines HERE, before
    # the rewrite: afterwards the model has reworded them and "None" is no
    # longer recognisable as one. Test-IsNoneLine is strict by design and keeps
    # anything it is not sure about.
    # Capture to a variable FIRST, then re-wrap. Remove-NoneLines returns ,$x
    # like its neighbours, and `@(Remove-NoneLines ...)` around the call itself
    # collapses the whole returned array into ONE element - the trap the note
    # above this block describes. Caught by t_brief_fixes.ps1 before it shipped.
    $DidNoNone     = Remove-NoneLines -Lines $WhatWeDid
    $WhatWeDid     = @($DidNoNone)
    $AutoNoNone    = Remove-NoneLines -Lines $WhatWeDidAuto
    $WhatWeDidAuto = @($AutoNoNone)
    $BlockNoNone   = Remove-NoneLines -Lines $Blockers
    $Blockers      = @($BlockNoNone)
    $AppNoNone     = Remove-NoneLines -Lines $Approvals
    $Approvals     = @($AppNoNone)
    $NextNoNone    = Remove-NoneLines -Lines $NextTasks
    $NextTasks     = @($NextNoNone)

    # Fix 5 - Saeed asked for shorter messages. Every section is capped, and the
    # overflow is COUNTED and shown ("+3 more - ask me"), never silently
    # dropped. The full text is always in docs\reports\ if he wants it.
    $MaxDid = 4; $MaxNext = 3; $MaxBlockers = 3; $MaxApprovals = 4

    $WhatWeDidNear   = Select-NearUnique -Lines $WhatWeDid
    $WhatWeDidAll    = @($WhatWeDidNear)
    $WhatWeDidCapped = @($WhatWeDidAll | Select-Object -First $MaxDid)
    # Fix 3 - lines the automation already rewrote. Deduplicated and capped like
    # the rest, but NEVER passed to Get-BusinessRewrite again.
    $AutoNear        = Select-NearUnique -Lines $WhatWeDidAuto
    $AutoAll         = @($AutoNear)
    $BlockersNear    = Select-NearUnique -Lines $Blockers
    $BlockersAll     = @($BlockersNear)
    $BlockersCapped  = @($BlockersAll | Select-Object -First $MaxBlockers)
    $ApprovalsNear   = Select-NearUnique -Lines $Approvals
    $ApprovalsAll    = @($ApprovalsNear)
    $ApprovalsCapped = @($ApprovalsAll | Select-Object -First $MaxApprovals)
    $NextTasksNear   = Select-NearUnique -Lines $NextTasks
    $NextTasksAll    = @($NextTasksNear)
    $NextTasksCapped = @($NextTasksAll | Select-Object -First $MaxNext)

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

    # ── Fix 3: fold in the automation's own lines, unrewritten ───────────────
    # These already went through Get-BusinessRewrite once, inside
    # strategy_daily.ps1, before they were written to the session log. Running
    # them through a second time is what turned a commit subject into a policy
    # statement on Saeed's phone. They are appended as-is, sharing the WHAT WE
    # DID cap so the message does not grow.
    $WhatWeDidFinal = @($WhatWeDidFinal)
    $DidRoom = $MaxDid - @($WhatWeDidFinal).Count
    if ($DidRoom -lt 0) { $DidRoom = 0 }
    $AutoShown = @($AutoAll | Select-Object -First $DidRoom)
    if (@($AutoShown).Count -gt 0) {
        $WhatWeDidFinal = @(@($WhatWeDidFinal) + @($AutoShown))
        Write-Log "$ProjectLabel WHAT WE DID - $(@($AutoShown).Count) line(s) from the automated log, passed through WITHOUT a second rewrite"
    }

    # A day where the only log was an autogen placeholder has no work to report.
    # Its boilerplate explains the staleness alarm, which is not Saeed's day -
    # on 2026-09-10 it reached him as "The system automatically closes because
    # no work or activity was recorded today." One plain line says it better.
    # The staleness / paused / close-failure banners above do the explaining.
    if ($SawPlaceholder -and -not $AnyRealContent -and @($WhatWeDidFinal).Count -eq 0) {
        $WhatWeDidFinal = @("No work recorded today.")
    }

    if ($DoneDropped -gt 0) {
        Write-Log "$ProjectLabel - $DoneDropped already-ticked item(s) dropped; they are done and are not re-asked"
    }

    # ── Fix 5: honest overflow markers ───────────────────────────────────────
    # Shown count vs real count. Nothing is hidden - Saeed is told there is more
    # and that he can ask for it. Computed AFTER the rewrite because the rewrite
    # must receive exactly the number of lines it was given.
    $BlockersFinal  = @($BlockersFinal)
    $ApprovalsFinal = @($ApprovalsFinal)
    $NextTasksFinal = @($NextTasksFinal)
    $DidTotal = @($WhatWeDidAll).Count + @($AutoAll).Count
    $DidOver  = $DidTotal - @($WhatWeDidFinal).Count
    if ($DidOver -gt 0)  { $WhatWeDidFinal  = @(@($WhatWeDidFinal)  + @("(+$DidOver more - ask me)")) }
    $BlockOver = @($BlockersAll).Count - @($BlockersFinal).Count
    if ($BlockOver -gt 0) { $BlockersFinal  = @(@($BlockersFinal)  + @("(+$BlockOver more - ask me)")) }
    $AppOver = @($ApprovalsAll).Count - @($ApprovalsFinal).Count
    if ($AppOver -gt 0)   { $ApprovalsFinal = @(@($ApprovalsFinal) + @("(+$AppOver more - ask me)")) }
    $NextOver = @($NextTasksAll).Count - @($NextTasksFinal).Count
    if ($NextOver -gt 0)  { $NextTasksFinal = @(@($NextTasksFinal) + @("(+$NextOver more - ask me)")) }

    # When the project cannot be read, every section is empty - but "Nothing stuck
    # right now" under a banner that says "This is NOT 'nothing to report'" is the
    # exact false comfort this fix exists to remove. Say what is true instead: we
    # do not know. Security Agent M2, 2026-09-07.
    $EmptyDid      = if ($Unreachable) { "  - Not known - could not read this project." } else { "  - Nothing logged in the last day." }
    $EmptyBlocking = if ($Unreachable) { "  - Not known - could not read this project." } else { "  - Nothing stuck right now." }
    $EmptyApprove  = if ($Unreachable) { "  - Not known - could not read this project." } else { "  - Nothing needs your OK right now." }
    $EmptyNext     = if ($Unreachable) { "  - Not known - could not read this project." } else { "  - Nothing lined up yet." }

    $Did      = if ($WhatWeDidFinal.Count -gt 0) { ($WhatWeDidFinal | ForEach-Object { "  - $_" }) -join "`n" } else { $EmptyDid }
    $Blocking = if ($BlockersFinal.Count -gt 0)  { ($BlockersFinal  | ForEach-Object { "  - $_" }) -join "`n" } else { $EmptyBlocking }
    # The overflow marker is a note about the list, not an item in it - giving it
    # a checkbox would ask Saeed to tick "(+2 more)".
    $Approve  = if ($ApprovalsFinal.Count -gt 0) { ($ApprovalsFinal | ForEach-Object { if ([string]$_ -like "(+*more - ask me)") { "  $_" } else { "  - [ ] $_" } }) -join "`n" } else { $EmptyApprove }
    $Next     = if ($NextTasksFinal.Count -gt 0) { ($NextTasksFinal | ForEach-Object { "  - $_" }) -join "`n" } else { $EmptyNext }

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
        NewestRealTime    = $NewestRealTime
        Unreachable       = $Unreachable
        UnreachableReason = $UnreachableReason
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

# ── 3b. EVENING: did the 18:30 close run? ────────────────────────────────────
# Saeed's instruction 2026-09-04: the session close moved OUT of this brief and
# into scripts\daily\session_close.ps1, on its own weekday 18:30 scheduled task.
# So in Evening mode this script no longer closes anything - it reads the marker
# that close left behind and reports on it. Correct order: close, then describe.
#
# Morning mode is UNCHANGED. The 07:00 run still calls strategy_daily.ps1 in
# section 6 as its git safety net, which is what commits and pushes weekend work
# (no close runs on a Saturday or Sunday).
#
# Deliberately NO fallback close here. If the 18:30 task failed, this brief says
# so loudly rather than quietly closing on its own - a silent auto-recovery is
# how the 11-19 Aug 2026 failure went unnoticed for eight days.
#
# READ BEFORE THE BANNERS (moved up from section 6-pre, 2026-09-07): the
# staleness wording below depends on whether the close ran, and section 5 freezes
# the message text. Answering "did the close run" first is what lets the brief
# tell "the close is broken" apart from "nobody worked on this project".
$HeldSignals     = @()
# PUSH-FAILED lines from the marker: the save to GitHub was REJECTED, which
# is a different problem from the push guard HOLDING it on purpose. Each
# entry keeps the DAY its marker belongs to, so the banner can name it -
# on a Saturday this may be Friday's failure. Security Agent B1/H1,
# 2026-09-09: the first version of this never initialised the variable, and
# under Set-StrictMode that crashed the entire brief on a healthy evening -
# no WhatsApp message at all. Never let this list go undeclared.
$FailedPushSignals = @()
# Retired failures are DEMOTED, never deleted. If the retirement logic is ever
# wrong, deleting leaves total silence in the one place Saeed reads, and a
# correct retirement reads identically to the alarm having broken. One plain
# line costs nothing and cannot silence a truth. Security Agent M2, 2026-09-09.
$RetiredPushSignals = @()
# "You are behind GitHub, but tonight's work is safe on its backup branch."
# NOT an emergency and deliberately not in $FailedPushSignals: that list drives
# the loud banner, and this states something that is true and not urgent.
# Saeed, 2026-09-10.
$BehindSignals = @()
# Named for the day whose close is being reported on, NOT for today - on a
# Saturday this is Friday's close. Renamed from $NoCloseToday, which invited
# exactly the "TODAY'S" wording bug below. Security Agent L2, 2026-09-07.
$CloseDayFailed  = $false
$FailedDayNames  = @()
$CloseFailDetail = @()

# WHICH DAY'S CLOSE IS THIS BRIEF REPORTING ON?
# Answer it from the SCHEDULE, not from the clock hour.
#
# My first attempt used "before 06:00 means yesterday", assuming a missed 19:00
# task catches up shortly after midnight. It does not: -StartWhenAvailable runs a
# missed task when the machine next becomes available, which for an office PC is
# the next MORNING. Security Agent H5, 2026-09-07. That left the original hole
# wide open - machine off Friday evening, switched on 10:00 Saturday, the brief
# catches up, asks for Saturday's marker, finds none, calls Saturday a weekend,
# and Friday's FAILED close is never opened or reported to anyone.
#
# So: always report on the last close that actually FELL DUE. That date is
# correct at 19:00 on the day, at 00:30, and at 10:00 the next morning alike, and
# it needs no assumption about how catch-up behaves.
$LastDueClose = Get-LastExpectedCloseTime -Now $Now
$CloseDay     = $LastDueClose.Date
if ($CloseDay -ne $Now.Date) {
    Write-Log "Reporting on the last close that fell due: $($LastDueClose.ToString('ddd yyyy-MM-dd HH:mm')) - not today."
}

# Is today itself a weekend? Kept SEPARATE from $CloseDay on purpose. $CloseDay
# is always a weekday now (a close only ever falls due on a weekday), so it can
# no longer answer "should I explain that no close runs today" - and conflating
# the two would regress the weekend behaviour approved in round 1.
$IsWeekendNow = $Now.DayOfWeek -eq [DayOfWeek]::Saturday -or
                $Now.DayOfWeek -eq [DayOfWeek]::Sunday

# SAEED'S DECISION, 2026-09-10: the morning brief must carry the close-failure
# alarm too. Until now the whole marker read below sat inside `if ($Mode -eq
# 'Evening')`, so $CloseDayFailed was ALWAYS false at 07:00 and section 6b-2
# never fired. A close that ran and failed on Monday evening was shouted about
# once at 19:00 and then never mentioned again - Tuesday's 07:00 brief said
# nothing, and if Saeed missed the one evening message he might never hear of it.
#
# Two things were tangled in one gate and are now separated:
#   $SkipCloseHere is the WRITE side - whether this script runs the close itself.
#     Still evening-only, unchanged.
#   The marker read is READ-ONLY. It looks at logs\close-state and sets the
#     reporting variables. Nothing about it needs to be evening-only, and the
#     day-naming logic already handles "the last close that fell due", which is
#     correct at 07:00 exactly as it is at 19:00.
# Security Agent F1 (PR #6) identified this; Saeed approved the fix.
$SkipCloseHere = ($Mode -eq 'Evening')


# WHICH MARKERS TO READ.
# The due close, always - that is the one whose absence is an alarm.
# PLUS today's, when today is not the due day. session_close.ps1 names its
# marker after the day it ACTUALLY RAN ($Today there), and -Force exists so a
# close can be run by hand at a weekend - CLAUDE.md documents it. Reading only
# the due day would silently drop a hand-run Saturday close that FAILED, and
# would drop its PUSH-HELD lines too, leaving unfinished work sitting unpushed
# in the live dashboard\ folder with no banner. Security Agent H6, 2026-09-07.
$MarkersToRead = @([PSCustomObject]@{ Date = $CloseDay; WasDue = $true })
if ($Now.Date -ne $CloseDay) {
    $MarkersToRead += [PSCustomObject]@{ Date = $Now.Date; WasDue = $false }
}

foreach ($m in $MarkersToRead) {
  # Wrapped: reading a marker must NEVER be able to kill the whole brief.
  # That is what B1 did, and it is the same shape as the unreadable-folder
  # fault from PR #2 - a throw under $ErrorActionPreference = "Stop",
  # outside any try, and Saeed gets no message at all. Security Agent, 2026-09-09.
  try {
    $MarkerPath = "C:\JeffLocal\logs\close-state\$($m.Date.ToString('yyyy-MM-dd'))-close.txt"
    $DayName    = $m.Date.ToString('dddd')
    if (Test-Path $MarkerPath) {
        $MarkerLines = @(Get-Content -Path $MarkerPath -ErrorAction SilentlyContinue)
        # Harvest push-held signals from EVERY marker read, due or hand-run.
        $HeldSignals += @(@($MarkerLines) | Where-Object { $_ -like "PUSH-HELD|*" })
        foreach ($br in @(@($MarkerLines) | Where-Object { $_ -like "BEHIND-REMOTE|*" })) {
            $BehindSignals += [PSCustomObject]@{ Day = $DayName; Sig = [string]$br }
        }
        foreach ($pf in @(@($MarkerLines) | Where-Object { $_ -like "PUSH-FAILED|*" -or $_ -like "TAG-PUSH-FAILED|*" })) {
            # RETIRE A FAILURE THAT HAS SINCE BEEN FIXED. Saeed's instruction
            # 2026-09-09. This banner is NOT like the close-failure one: that
            # stays true until the close is re-run, but "did not reach GitHub"
            # becomes FALSE the moment a later push succeeds. Read on a Saturday,
            # the marker is Friday's - and if Saturday's 07:00 push went through,
            # Friday's work IS on GitHub and the banner would be a lie. A warning
            # that repeats something untrue is how it stops being read.
            #
            # Evidence: strategy_daily.ps1 stamps last-push-ok-<project>.txt on
            # every successful push. If that stamp is NEWER than the marker that
            # recorded the failure, the failure is history - drop it.
            # Format: PUSH-FAILED|<project>|<reason>|<sha>. Older markers
            # written before 2026-09-09 have no 4th field; those can never be
            # PROVEN fixed, so they keep their warning. Safe direction.
            $pfParts   = ([string]$pf).Split("|", 4)
            $pfProject = if (@($pfParts).Count -ge 2) { [string]$pfParts[1] } else { "" }
            $pfSha     = if (@($pfParts).Count -ge 4) { ([string]$pfParts[3]).Trim() } else { "" }
            $pfIsTag   = ([string]$pf) -like "TAG-PUSH-FAILED|*"
            $Retired   = $false
            $RetiredAt = ""

            # A TAG push failure is NEVER retirable by a branch-push stamp: the
            # later push does not push that tag, so the restore point is still
            # missing and the claim is still true. Retiring it would leave a day
            # with no remote restore point and no alarm, and the next clean close
            # would prune the local-only tag away. Security Agent H1, 2026-09-09.
            if (-not $pfIsTag) {
              try {
                # THE PROOF, AND NOTHING ELSE. Ask git the question the banner
                # actually asks: is the commit that failed to push now on GitHub?
                #
                # The first version of this decided on a timestamp - "did a push
                # succeed after the failure?" - which is a DIFFERENT question. A
                # push of another branch satisfied it (the close runs
                # `git push origin HEAD`, so the branch varies), and so did a
                # `git reset --hard` that discarded the work entirely. Both would
                # have switched off a warning that was still true.
                #
                # The timestamp gate that used to sit in front of this has now
                # been REMOVED as well. It could only ever withhold a retirement
                # that git had already proved correct - which is a false alarm on
                # the one banner that must stay believed. Its own failure mode
                # (a clock set forward suppressing the alarm for months) also
                # disappears with it. Security Agent L2 accepted, 2026-09-09.
                # The stamp is still read, but ONLY to say when the work arrived.
                #
                # UPDATED 2026-09-10 - READ THIS BEFORE TRUSTING THE NEXT LINES.
                # The close now pushes to origin/close/<date> BEFORE the real
                # branch, so the old guarantee ("the sha cannot already be on
                # origin") is FALSE. What replaces it is the exclusion below:
                # backup branches are filtered out, so "on an origin branch that
                # is not a backup" still means the work reached a real branch.
                # Security Agent H3, 2026-09-10.
                #
                # WHY "on origin" IS SUFFICIENT PROOF, and what would break it.
                # strategy_daily.ps1 only ever attempts a push inside
                # `if ($CommitExit -eq 0)`, i.e. immediately after creating a
                # commit - so the sha in a PUSH-FAILED signal is always seconds
                # old and CANNOT already have been on origin when the push
                # failed. Finding it on origin later therefore means it genuinely
                # arrived. If that precondition is ever removed over there, this
                # check must be tightened here in the same commit, because no
                # test would fail. Security Agent, 2026-09-09 round-3 review.
                #
                # No sha recorded (markers written before 2026-09-09) = no proof
                # possible = keep shouting.
                if ($pfSha -match '^[0-9a-fA-F]{7,40}$') {
                    # ONE PROOF, ONE IMPLEMENTATION. This used to be an inline copy
                    # of the same logic that section 6b-0 now calls as a function -
                    # near-identical duplicates, which is the worst state for drift:
                    # the next editor assumes syncing them is safe, and one of them
                    # is subtly not the other. Both now route through
                    # Test-WorkOnOrigin, which carries the origin scoping, the
                    # close/* backup exclusion and the 5.1 stderr guard in one
                    # place. The last-push-ok stamp read stays HERE, because it is
                    # presentation for this call site only. Security Agent T4,
                    # 2026-09-10.
                    $RepoForProject = Repo-ForProject -ProjectField $pfProject
                    if (Test-Path $RepoForProject) {
                        if (Test-WorkOnOrigin -Sha $pfSha -RepoRoot $RepoForProject) {
                            $Retired = $true
                            Write-Log "PUSH-FAILED for $pfProject retired - commit $pfSha is on a real origin branch."
                            # WHEN it arrived - presentation only. Nothing below
                            # can change $Retired, so a missing, corrupt or
                            # future-dated stamp costs a phrase, never an alarm.
                            try {
                                $OkFile = Join-Path (Split-Path $MarkerPath -Parent) `
                                          ("last-push-ok-" + ($pfProject -replace '[\\/:*?"<>|]', '_') + ".txt")
                                if (Test-Path $OkFile) {
                                    $OkParts = ([string](Get-Content $OkFile -Raw)).Trim().Split("|", 2)
                                    # ParseExact + InvariantCulture, not Parse:
                                    # Parse reads the machine's culture, and under
                                    # a non-Gregorian default calendar this date
                                    # lands centuries away. Security Agent L1.
                                    $OkStamp = [datetime]::ParseExact(([string]$OkParts[0]).Trim(), `
                                               'yyyy-MM-dd HH:mm:ss', [Globalization.CultureInfo]::InvariantCulture)
                                    if ($OkStamp -le $Now.AddMinutes(5)) {
                                        $RetiredAt = $OkStamp.ToString("ddd HH:mm")
                                    } else {
                                        Write-Log "Last-push stamp for $pfProject is dated in the FUTURE ($OkStamp) - not quoting a time."
                                    }
                                }
                            } catch {
                                Write-Log "Could not read the last-successful-push time for $pfProject - saying 'later' instead. $_"
                            }
                        } else {
                            Write-Log "Commit $pfSha for $pfProject is NOT on any origin branch - keeping the warning."
                        }
                    } else {
                        Write-Log "Cannot reach $RepoForProject to verify $pfSha - keeping the warning."
                    }
                }
              } catch {
                # Cannot tell? Then say nothing about it being fixed and SHOW the
                # banner. Failing safe here means shouting, not going quiet.
                Write-Log "Could not verify whether $pfProject's work reached GitHub - keeping the warning. $_"
              }
            }

            if ($Retired) {
                $RetiredPushSignals += [PSCustomObject]@{ Day = $DayName; Project = $pfProject; At = $RetiredAt }
            } else {
                $FailedPushSignals += [PSCustomObject]@{ Day = $DayName; Sig = [string]$pf }
            }
        }
        $ClosedAt = @(@($MarkerLines) | Where-Object { $_ -like "CLOSED|*" }) | Select-Object -First 1
        if ($ClosedAt) {
            Write-Log "$DayName's close ran ($ClosedAt) - this brief reports only."
        } else {
            # Marker present but no CLOSED line: the close RAN and FAILED. Treat
            # it exactly as harshly as a missing marker - the outcome for Saeed is
            # the same (no session log, no handover, no restore point) and a
            # half-done close reported as fine is how failures hide. A hand-run
            # weekend close that failed lands here too. Security Agent 2026-09-04.
            $CloseDayFailed  = $true
            $FailedDayNames += $DayName
            $CloseFailDetail += @(@($MarkerLines) | Where-Object { $_ -like "FAILED-DETAIL|*" } |
                ForEach-Object { "  - $DayName" + ": " + (([string]$_).Split("|", 3)[1..2] -join ": ") })
            Write-Log "WARNING: $DayName's close RAN AND FAILED."
        }
    } elseif ($m.WasDue) {
        # A close FELL DUE that day and left no marker at all. That is an alarm
        # on any day of the week, including when read on a Saturday: the weekend
        # never excuses a weekday close that did not happen. What the weekend
        # does excuse - that no close runs TODAY - is $IsWeekendNow, not this.
        # Security Agent H2 and H5, 2026-09-07.
        $CloseDayFailed  = $true
        $FailedDayNames += $DayName
        Write-Log "WARNING: no close marker at $MarkerPath - $DayName's close did not run."
    } else {
        # No hand-run close today. Nothing was due, so there is nothing to say.
        Write-Log "No hand-run close marker for today ($DayName) - none was due."
    }
  } catch {
    # Do not go quiet. A marker we cannot read is itself worth shouting about,
    # and the brief must still be sent.
    Write-Log "WARNING: could not read the close marker for $($m.Date.ToString('yyyy-MM-dd')) - $_"
    if ($m.WasDue) {
        $CloseDayFailed  = $true
        $FailedDayNames += $m.Date.ToString('dddd')
    }
  }
}

# May the brief say "today's close ran"? Only in the evening, only if nothing
# failed, and only if the close it reports on actually fell due TODAY. On a
# Saturday $CloseDay is Friday, so "today's close ran" would be false however
# healthy Friday's close was - the opposite lie to the one H2 fixed.
$CloseRanToday = ($Mode -eq 'Evening') -and (-not $CloseDayFailed) -and ($CloseDay -eq $Now.Date)

Write-Log ("Last close fell due {0}. Anything logged since then is current." -f `
    $LastDueClose.ToString('ddd yyyy-MM-dd HH:mm'))

# One plain line so "no close today" is visible and explained rather than simply
# absent - absence is what let eight days go unnoticed. Suppressed when a close
# has actually failed: "no close was due" sitting next to a failure banner reads
# as a broken script, and one message must have one voice. Security Agent M5.
$WeekendNote = ""
if (($Mode -eq 'Evening') -and $IsWeekendNow -and (-not $CloseDayFailed)) {
    $WeekendNote = "Note: no session close at weekends - that is normal. Any work is still saved by the 07:00 brief." +
                   [Environment]::NewLine
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
#
# TWO DIFFERENT PROBLEMS, TWO DIFFERENT VOICES (Saeed's instruction 2026-09-07).
# The old banner said "The daily session close is NOT running" for ANY project
# with no fresh log. That was wrong and it cost Saeed a needless alarm on
# 2026-09-04: the 18:30 close had run perfectly, but St Marks had simply had no
# work committed for 11 days while awaiting pharmacist sign-off, and the brief
# reported a healthy system as broken. A warning that cries wolf gets ignored,
# and this one guards a real eight-day outage.
#
# So now:
#   - Project paused on purpose ($PausedProjects) -> quiet one-line note.
#   - Project NOT paused and gone quiet           -> loud banner, but it says
#     "no work has been logged", which is what was actually measured. It only
#     blames the close when the close really did fail.
#   - The close itself failed or never ran        -> the separate, always-loud
#     day-named close-failure banner in section 6b-2. That one
#     is never silenced by pausing a project.
$StaleParts       = @()
$PausedNotes      = @()
$UnreachableParts = @()
$ScheduleNotes    = @()

foreach ($p in @(
    @{ Name = "AI reception helper (Avamed)";  Brief = $JeffLocalBrief },
    @{ Name = "Pharmacy website (St Marks)";   Brief = $StMarksBrief }
)) {
    # UNREACHABLE BEATS PAUSED, ALWAYS. Pausing a project means "no new work is
    # expected"; it never means "this project's folder may vanish". A missing or
    # unreadable folder is a system fault, and it is the 11-19 Aug 2026 outage
    # shape, so it is loud whatever the pause list says. Security Agent H1.
    if ($p.Brief.Unreachable) {
        $UnreachableParts += "!!   $($p.Name) : $($p.Brief.UnreachableReason)"
        Write-Log "UNREACHABLE BANNER: $($p.Name) - $($p.Brief.UnreachableReason)"
        continue
    }

    if (-not $p.Brief.IsStale) { continue }

    if ($PausedProjects.ContainsKey($p.Name)) {
        $PausedNotes += (Format-PausedLine -Name $p.Name -Reason $PausedProjects[$p.Name] `
            -Hours $p.Brief.StaleHours -CloseRan:$CloseRanToday)
        Write-Log "STALENESS: $($p.Name) is a PAUSED project - quiet note, no banner."
    } elseif ($null -ne $p.Brief.NewestRealTime -and $p.Brief.NewestRealTime -ge $LastDueClose) {
        # Its newest real log is NEWER than the last close that fell due, so no
        # close has been missed - this is the ordinary overnight and weekend gap.
        # Explain it once, quietly.
        # Exact timestamps, no rounding and no slack: with a tolerance, a log
        # written shortly BEFORE a close that then failed would have been called
        # "none has been due since", which is precisely false. Security Agent M3.
        # A project with no real log at all has $null here and can never land in
        # this branch - it always reaches the loud banner. Security Agent H4.
        $ScheduleNotes += "Note: $($p.Name) - nothing new logged since the last session close, and no close has been due since. That is the normal gap, not a problem."
        Write-Log "STALENESS: $($p.Name) last logged $($p.Brief.NewestRealTime.ToString('ddd HH:mm')), after the last due close - quiet note, no banner."
    } elseif ($null -ne $p.Brief.NewestRealTime -and
              $p.Brief.NewestRealTime -ge (Get-CloseTimeNBack -From $LastDueClose -Closes ($StaleLoudAfterCloses - 1))) {
        # QUIET FOR THE FIRST TWO MISSED CLOSES. Saeed's decision 2026-09-09.
        # A close HAS been missed here - that is what separates this from the "no
        # close was due" branch above - but one or two are ordinary, and a loud
        # banner for an ordinary day off is the cry-wolf problem in a different coat.
        #
        # MEASURED IN CLOSES, NOT HOURS, so the weekend cannot count toward the
        # three. $null is routed to the loud branch explicitly: a project with no
        # real log at all has no timestamp to compare and must never land here.
        # Security Agent F2, 2026-09-09.
        #
        # It is still SAID, every day, from the first one: silence is what let the
        # 11-19 Aug 2026 outage run for eight days. Only the volume waits.
        $ClosesMissed = Get-ClosesMissed -Since $p.Brief.NewestRealTime -LastDue $LastDueClose -Cap $StaleLoudAfterCloses
        $CloseWord = if ($ClosesMissed -le 1) { "one working day" } else { "$ClosesMissed working days" }
        # NO "NORMAL SO FAR". A due close has provably been missed, and in a MORNING
        # run this script has not even read the close marker - the marker block is
        # gated on Evening mode - so it cannot know whether the close failed or
        # nobody worked. Asserting normality here is a claim it has not earned, and
        # would contradict the loud close-failure banner Saeed may have read the
        # night before. Say what is true: what was seen, and when it escalates.
        # Security Agent F1, 2026-09-09.
        $ScheduleNotes += "Note: $($p.Name) - nothing new logged for $CloseWord, and a session close has come and gone since. Not shouting yet; this becomes a warning at $StaleLoudAfterCloses working days."
        Write-Log "STALENESS: $($p.Name) has missed $ClosesMissed close(s) - under the $StaleLoudAfterCloses-close threshold, quiet note only."
    } else {
        # Same counter as the quiet note above, so the escalation states the number
        # the note promised. A project with no real log has no timestamp to count
        # from; it keeps its own "NO session log has ever been found" wording.
        $LoudCloses = if ($null -ne $p.Brief.NewestRealTime) {
                          Get-ClosesMissed -Since $p.Brief.NewestRealTime -LastDue $LastDueClose
                      } else { 0 }
        $StaleParts += (Format-StaleLine -Name $p.Name -Hours $p.Brief.StaleHours `
                        -LogName $p.Brief.StaleLogName -Closes $LoudCloses)
    }
}

# ── Cannot see a project at all ──────────────────────────────────────────────
# Its own banner, above everything else. Saeed's brief must never imply a
# project is fine when the script could not look at it.
$UnreachableBanner = ""
if (@($UnreachableParts).Count -gt 0) {
    $UnreachableBody   = (@($UnreachableParts) -join [Environment]::NewLine)
    $UnreachableBanner = @"
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! CANNOT SEE ONE OF YOUR PROJECTS
$UnreachableBody
!!
!! Nothing below can be trusted for the project(s) above - the
!! script could not read their session logs, so it does not know
!! whether work happened or not. This is NOT "nothing to report".
!! Your work is not lost; the computer cannot see the folder.
!! This is how the 11-19 Aug 2026 outage started. Check now.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

"@
    Write-Log "UNREACHABLE BANNER SHOWN for $(@($UnreachableParts).Count) project(s)"
}

$StaleBanner = ""
if (@($StaleParts).Count -gt 0) {
    $StaleBody = (@($StaleParts) -join [Environment]::NewLine)
    # Only point at the close when the close is genuinely the suspect. If it ran,
    # saying so stops Saeed hunting a scheduled-task fault that does not exist.
    $StaleCause = if ($CloseDayFailed) {
        "!! The $(@($FailedDayNames) -join ' and ') session close$(if (@($FailedDayNames).Count -gt 1) { 's' }) did not complete either - see the banner above."
    } elseif ($CloseRanToday) {
        # Claim ONLY what the marker proves: the 18:30 close ran. It says nothing
        # about the health check, the watchdog, the 07:00 brief or the WhatsApp
        # sender. "Nothing is broken in the automation" would tell Saeed to stop
        # looking - the exact direction in which outages hide. Security Agent
        # condition C1, 2026-09-07.
        "!! Today's 18:30 session close ran, so this is not a close failure."
        "!! It means the work itself has stopped, or is not being committed."
    } else {
        "!! Either work has genuinely stopped, or it is not being saved."
    }
    $StaleBanner = @"
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! WARNING - PART OF THIS BRIEF IS OUT OF DATE
$StaleBody
!!
!! No work has been logged for the project(s) above, and they are
!! not marked as paused.
$($StaleCause -join [Environment]::NewLine)
!! What you read below for them is OLD news repeated, not today's work.
!! Do not read it as progress. This needs looking at before you trust it.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

"@
    Write-Log "STALENESS BANNER SHOWN for $(@($StaleParts).Count) project(s)"
} else {
    Write-Log "Staleness check: no unexpected staleness (paused projects: $(@($PausedNotes).Count))"
}

# The quiet note for deliberately paused projects. Sits under the banner block so
# a real alarm is always read first.
$PausedNote = ""
if (@($PausedNotes).Count -gt 0) {
    $PausedNote = (@($PausedNotes) -join [Environment]::NewLine) + [Environment]::NewLine
    Write-Log "PAUSED NOTE shown for $(@($PausedNotes).Count) project(s)"
}

# The quiet "this gap is by design" line for projects that are only stale because
# no close has fallen due since they last logged anything.
$ScheduleNote = ""
if (@($ScheduleNotes).Count -gt 0) {
    $ScheduleNote = (@($ScheduleNotes) -join [Environment]::NewLine) + [Environment]::NewLine
    Write-Log "SCHEDULE NOTE shown for $(@($ScheduleNotes).Count) project(s)"
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
$UnreachableBanner$StaleBanner$PausedNote$ScheduleNote$WeekendNote$OllamaNote$HealthBlock
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
# The close-marker read that used to sit here moved UP to section 3b, above the
# staleness banner. It has to run first: the banner's wording now depends on
# whether the 18:30 close actually ran, and section 5 freezes the message text
# before this point. Moved 2026-09-07. $HeldSignals, $CloseDayFailed,
# $CloseFailDetail and $SkipCloseHere are all set there.

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
        # A rejected push must surface in the MORNING brief too. On 8 Sep 2026 the
        # 07:00 run failed to push and said nothing; and since no close runs at a
        # weekend, a Friday-night failure would otherwise stay invisible until
        # Monday. Security Agent H2, 2026-09-09.
        foreach ($pf in @(@($JLOutput) | ForEach-Object { [string]$_ } | Where-Object { $_ -like "PUSH-FAILED|*" -or $_ -like "TAG-PUSH-FAILED|*" })) {
            $FailedPushSignals += [PSCustomObject]@{ Day = $Now.ToString("dddd"); Sig = [string]$pf }
        }
        # BEHIND-REMOTE too, or it is collected and thrown away. Only the 18:30
        # marker path was updated when this signal was added, so a morning run that
        # was merely behind emitted it here and NOBODY read it - silently reversing
        # the comment directly above, which exists because a rejected push must
        # surface in the morning brief. Security Agent H1, 2026-09-10.
        foreach ($br in @(@($JLOutput) | ForEach-Object { [string]$_ } | Where-Object { $_ -like "BEHIND-REMOTE|*" })) {
            $BehindSignals += [PSCustomObject]@{ Day = $Now.ToString("dddd"); Sig = [string]$br }
        }
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
                ForEach-Object {
                    $line = [string]$_
                    if ($line -like "PUSH-HELD|*")   { $script:HeldSignals += $line }
                    if ($line -like "PUSH-FAILED|*" -or $line -like "TAG-PUSH-FAILED|*") {
                        $script:FailedPushSignals += [PSCustomObject]@{ Day = $Now.ToString("dddd"); Sig = $line }
                    }
                    # Same omission as the JeffLocal site above. Security Agent H1.
                    if ($line -like "BEHIND-REMOTE|*") {
                        $script:BehindSignals += [PSCustomObject]@{ Day = $Now.ToString("dddd"); Sig = $line }
                    }
                }
        } catch {
            Write-Log "WARNING: St Marks session close failed - $_"
        }
    } else {
        Write-Log "WARNING: SMCPHARMA not found at $SmRepo - skipped its session close"
    }
}

# ORDER MATTERS: this block PREPENDS, and so do the three alarm banners that
# follow it (6b-2 close failed, 6c push held, 6b-3 push failed). The LAST
# prepend ends up highest, so this runs FIRST to land BENEATH all of them.
# Placed after them, "NOW FIXED - no action needed" was the first thing Saeed
# saw, sitting on top of live alarms. Security Agent M2, 2026-09-09 re-review.
# ── 6b-0. RE-PROVE RETIREMENT, AFTER this run's own push ─────────────────────
# The marker read happens near the top of the script, because section 5 needs
# $CloseDayFailed early. In MORNING mode that is now BEFORE sections 6/6b run the
# git safety net - so the question "has this work reached GitHub yet?" was asked
# before the push that puts it there, and its answer would be rendered after.
#
# Result without this: the 07:00 brief shouts "the save to GitHub failed" about
# work that the same 07:00 run has just saved. The whole retirement mechanism
# exists (Saeed, 2026-09-09) so that banner stops the moment the work arrives;
# asking too early defeats it on the one run that fixes the problem, and lands a
# false loud banner on the morning after a failure - exactly when Saeed most
# needs it to be true. Security Agent S2, 2026-09-10.
if (-not $DryRun -and -not $SkipCloseHere -and @($FailedPushSignals).Count -gt 0) {
    $StillFailed = @()
    foreach ($entry in @($FailedPushSignals)) {
        $ep = ([string]$entry.Sig).Split("|", 4)
        # Tag failures are never retirable, and a signal with no sha cannot be proven.
        if (([string]$entry.Sig) -like "TAG-PUSH-FAILED|*" -or @($ep).Count -lt 4) {
            $StillFailed += $entry; continue
        }
        if (Test-WorkOnOrigin -Sha ([string]$ep[3]).Trim() -RepoRoot (Repo-ForProject -ProjectField ([string]$ep[1]))) {
            $RetiredPushSignals += [PSCustomObject]@{ Day = $entry.Day; Project = [string]$ep[1]; At = "" }
            Write-Log "Retired on re-check: $($ep[1])'s work reached GitHub during this run."
        } else {
            $StillFailed += $entry
        }
    }
    $FailedPushSignals = @($StillFailed)
}

# DE-DUPLICATE THE BEHIND SIGNALS - ABOVE THEIR CONSUMER, AND KEYED ON PROJECT.
# This was originally placed next to the held-signal dedup, 96 lines BELOW the
# block that renders it, so it was dead code that never ran. And its key was the
# whole signal, which embeds close/$Today - so yesterday's marker entry and this
# morning's entry differ by construction every single day and could never group.
# Two "BEHIND GITHUB" lines for one project, every morning.
# Keep the LAST: the marker is harvested first, so the newest entry is the one
# that reflects the current state. Security Agent T1/T2, 2026-09-10.
# Same two guards as the held dedup below: an index that cannot go out of bounds
# (this one takes [1] only, so it is already safe, but the bounds check is written
# out so the next editor does not have to re-derive why), and a preference for the
# last WELL-FORMED entry. Security Agent G1/G2, 2026-09-10.
$BehindSignals = @(@($BehindSignals) |
                   Group-Object {
                       $b = @(([string]$_.Sig) -split '\|')
                       if ($b.Count -gt 1) { $b[1] } else { "" }
                   } |
                   ForEach-Object {
                       $g  = @($_.Group)
                       # NOTE FOR WHOEVER ADDS A FIFTH PRODUCER: this filter and the
                       # key above both read $_.Sig, and under StrictMode a MISSING
                       # PROPERTY is terminating. It is unreachable today because all
                       # four producers construct [PSCustomObject]@{ Day=; Sig= }
                       # literally - but it is the one guard in these two dedups that
                       # is safe by convention rather than by structure. The held
                       # dedup below cannot throw at all: its members are already
                       # [string] before Group-Object sees them, and it indexes
                       # nothing. Security Agent, round 13.
                       $ok = @($g | Where-Object { @(([string]$_.Sig) -split '\|').Count -ge 3 })
                       if (@($ok).Count -gt 0) { @($ok)[-1] } else { @($g)[-1] }
                   })

# ── 6b-5. Behind GitHub, but the work is safe ────────────────────────────────
# Saeed, 2026-09-10. Since the close pushes to a backup branch that nobody else
# writes to, "behind main" no longer means the work is at risk - so it must not
# borrow the loud banner's voice. It is still SAID, every time, because he does
# need to know there is newer code waiting and why it was not taken
# automatically. Prepended before the alarm blocks so it lands beneath them.
if (@($BehindSignals).Count -gt 0) {
    $BehindLines = @()
    foreach ($b in @($BehindSignals)) {
        $bp = ([string]$b.Sig).Split("|", 4)
        if (@($bp).Count -ge 3) { $BehindLines += "   $($bp[1]): $($bp[2])" }
    }
    $BehindBlock = "BEHIND GITHUB - your work is safe, no rush" + [Environment]::NewLine +
                   (@($BehindLines) -join [Environment]::NewLine) + [Environment]::NewLine + [Environment]::NewLine
    if (-not $DryRun -and (Test-Path $ReportPath)) {
        $ExistingReport = Get-Utf8FileText -Path $ReportPath
        Set-Content -Path $ReportPath -Value ($BehindBlock + $ExistingReport) -Encoding UTF8
    }
    Write-Log "BEHIND-REMOTE note shown for $(@($BehindLines).Count) project(s) - quiet, work is on its backup branch."
    Write-Host $BehindBlock
}

# ── 6b-4. Failures that have since been fixed - DEMOTED, not deleted ─────────
# Saeed asked (2026-09-09) for the "did not reach GitHub" banner to stop once the
# work arrives, and it does: no !! banner, no repetition. But it does not vanish
# without trace. If the retirement check above is ever wrong, deleting the signal
# would leave total silence in the one place Saeed reads - and even when it is
# right, a banner that simply stops appearing reads exactly like the alarm having
# broken. One plain line says which it was. Security Agent M2, 2026-09-09.
if (@($RetiredPushSignals).Count -gt 0) {
    $FixedLines = @()
    foreach ($r in @($RetiredPushSignals)) {
        $When = if ([string]::IsNullOrWhiteSpace([string]$r.At)) { "since" } else { "at $($r.At)" }
        $FixedLines += "   $($r.Day)'s save to GitHub failed for $($r.Project), but the work has arrived $When - it IS on GitHub now. Nothing to do."
    }
    $FixedBlock = "NOW FIXED - no action needed" + [Environment]::NewLine +
                  (@($FixedLines) -join [Environment]::NewLine) + [Environment]::NewLine + [Environment]::NewLine
    if (-not $DryRun -and (Test-Path $ReportPath)) {
        $ExistingReport = Get-Utf8FileText -Path $ReportPath
        Set-Content -Path $ReportPath -Value ($FixedBlock + $ExistingReport) -Encoding UTF8
    }
    Write-Log "Retired $(@($RetiredPushSignals).Count) push-failure signal(s) - demoted to a plain line, not deleted."
    Write-Host $FixedBlock
}

# ── 6b-2. The 18:30 close did not run? Say so, loudly, tonight ───────────────
# Nothing was lost - the work is still on the machine - but today has no session
# log, no HANDOFF refresh, no commit and no restore tag. Saeed sees it the same
# evening rather than discovering a gap weeks later.
if ($CloseDayFailed) {
    # NAME THE DAY. This banner used to say "TODAY'S" unconditionally, but the
    # close it reports on is often not today's - on a Saturday it is Friday's.
    # Telling Saeed to check today's scheduled task when the fault is Friday's
    # sends him to the wrong place, and a banner that looks wrong is a banner he
    # learns to discount. Every positive claim in this script was already
    # day-scoped; the negative ones were not. Security Agent M5, 2026-09-07.
    $FailedDayLabel = if (@($FailedDayNames).Count -gt 1) {
        (@($FailedDayNames) -join " AND ").ToUpper() + " SESSION CLOSES DID NOT COMPLETE"
    } else {
        (@($FailedDayNames)[0]).ToUpper() + "'S SESSION CLOSE DID NOT COMPLETE"
    }
    $FailedDayPlain = (@($FailedDayNames) -join " and ")
    # "NOTHING SAVED TO GITHUB" IS FALSE BY 07:00. The morning brief runs the git
    # safety net (sections 6/6b) BEFORE this banner is prepended, so by the time
    # Saeed reads it that day's work has usually been committed and pushed. Three
    # of the four claims stay true at 07:00; this one does not, and a banner with
    # one false clause in it is a banner he learns to discount - the same trust
    # problem this file has now corrected six times. Security Agent S3, 2026-09-10.
    $SavedClause = if ($Mode -eq 'Evening') { ", nothing saved to GitHub" } else { "" }
    # "has"/"have", and no "18:30": a hand-run weekend close is not an 18:30 one.
    $FailedDayVerb  = if (@($FailedDayNames).Count -gt 1) { "have" } else { "has" }
    $NoCloseBanner = @"
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! $FailedDayLabel
!! The session close did not complete, so $FailedDayPlain $FailedDayVerb no
!! session log, no handover note$SavedClause, no restore point.
$(if (@($CloseFailDetail).Count -gt 0) { "!! What went wrong:" + [Environment]::NewLine + (@($CloseFailDetail) -join [Environment]::NewLine) } else { "!! It did not run at all." })
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
# DE-DUPLICATE THE HELD SIGNALS. Since the marker read moved out of the Evening
# gate, a Morning run fills this from TWO sources: yesterday's marker, and this
# morning's own strategy_daily.ps1 output. session_close.ps1 writes the same
# signal into the marker, so an unfinished dashboard\ folder produces one from
# each. Security Agent S4, 2026-09-10.
#
# KEY ON PROJECT AND PATH, NOT THE WHOLE LINE, AND KEEP THE LAST. The count is
# field 3, so `Select-Object -Unique` let "dashboard|3" from yesterday's marker
# and "dashboard|5" from this morning BOTH through - and because the marker is
# harvested first, the stale 3-file line rendered ABOVE the current 5-file one.
# Security Agent T3, 2026-09-10.
# NEVER INDEX PAST THE END. StrictMode (which -Version Latest resolves to 3.0 on
# Windows PowerShell 5.1, so this is NOT a pwsh-7 artefact) makes an out-of-bounds
# index a TERMINATING error. The harvest filter is -like "PUSH-HELD|*", which
# guarantees ONE pipe, not three - so $p[2] on a truncated line threw, at script
# top level with no enclosing try, and killed the entire brief. Saeed would have
# received NO WhatsApp message at all, on the morning after a close crashed
# mid-write. That is the 11-19 Aug 2026 shape, and it is the same defect class as
# B1. One malformed line poisoned the whole array, good signals included.
# The renderer eight lines below already guards with `Count -ge 4`; this dedup
# runs in FRONT of that guard and must be at least as careful.
# Security Agent G1, 2026-09-10.
#
# And prefer the last WELL-FORMED entry, not simply the last: a malformed line
# arriving from this run would otherwise win the group, be discarded by the
# renderer's guard, and take the good marker-sourced line with it - leaving a
# banner header with nothing under it. Security Agent G2.
$HeldSignals = @(@($HeldSignals) | ForEach-Object { [string]$_ } |
                 Group-Object {
                     $p = @($_ -split '\|')
                     "$(if ($p.Count -gt 1) { $p[1] })|$(if ($p.Count -gt 2) { $p[2] })"
                 } |
                 ForEach-Object {
                     $g  = @($_.Group)
                     $ok = @($g | Where-Object { @([string]$_ -split '\|').Count -ge 4 })
                     if (@($ok).Count -gt 0) { @($ok)[-1] } else { @($g)[-1] }
                 })

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

# ── 6b-3. The save to GitHub was REJECTED ────────────────────────────────────
# Runs in BOTH modes: the evening reads it from the close marker, the morning
# from strategy_daily.ps1's own output in section 6. Security Agent H2.
# Loud, and on TOP of the push-guard banner. Both blocks PREPEND, so the one
# that runs LAST ends up highest - which is why this section now follows 6c
# rather than preceding it. Security Agent L1, 2026-09-09. Reason: a held push is the system working as
# designed, a rejected one is work silently not reaching GitHub. On 7-9 Sep 2026
# that went unreported for three days while every other signal read healthy.
if (@($FailedPushSignals).Count -gt 0) {
    $FailLines = @()
    foreach ($entry in @($FailedPushSignals)) {
        # Split to 4: the sha is a 4th field now, and Split("|",3) would glue it
        # onto the end of the reason Saeed reads. Security Agent H2, 2026-09-09.
        $parts = ([string]$entry.Sig).Split("|", 4)
        if (@($parts).Count -ge 3) { $FailLines += "!!   $($parts[1]): $($parts[2])" }
    }
    $FailBody = (@($FailLines) -join [Environment]::NewLine)
    # NAME THE DAY. Read on a Saturday, the marker is Friday's, so "TODAY'S" would
    # be false - the same defect already corrected for the close banner, and a
    # standing rule in CLAUDE.md ("Every alarm names its day"). Security Agent H1.
    $FailDays = @(@($FailedPushSignals) | ForEach-Object { $_.Day } | Select-Object -Unique)
    $FailWhen = if (@($FailDays).Count -eq 1) { (@($FailDays)[0]).ToUpper() + "'S" }
                else { (@($FailDays) -join " AND ").ToUpper() }
    # DO NOT OVERSTATE WHEN ONLY THE RESTORE TAG FAILED. If every signal here is
    # a TAG-PUSH-FAILED, the commits DID reach GitHub and "your work did not
    # reach GitHub / it is not backed up" is false. The same overstatement was
    # just removed from the signal text itself (Security Agent H1); leaving it in
    # the banner wrapped around that signal would put it straight back.
    $AnyRealPushFail = @(@($FailedPushSignals) |
                         Where-Object { ([string]$_.Sig) -notlike "TAG-PUSH-FAILED|*" }).Count -gt 0
    $FailHead = if ($AnyRealPushFail) { "$FailWhen WORK DID NOT REACH GITHUB" }
                else { "$FailWhen RESTORE POINT DID NOT REACH GITHUB" }
    # The soft text makes NO claim about the work itself. TAG-PUSH-FAILED can be
    # emitted in a run where nothing was committed and so no push was attempted -
    # and if unpushed commits already existed from an earlier day, "your work IS on
    # GitHub" would be false. Say only what this signal knows. Security Agent L4.
    $FailTail = if ($AnyRealPushFail) {
@"
!! Your work is NOT lost - it is saved on this computer. But it is
!! NOT backed up, and it will keep failing every day until this is
!! fixed. Do not ignore this: work piling up unsent, with everything
!! else looking healthy, is how the 11-19 Aug 2026 outage happened.
"@
    } else {
@"
!! This is about the RESTORE POINT, not about your work: there is no
!! snapshot to roll back to for that day. It will not fix itself - a
!! later close only ever cuts THAT day's tag, never an earlier one.
"@
    }
    $FailBanner = @"
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! $FailHead
$FailBody
!!
$FailTail
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

"@
    if (-not $DryRun -and (Test-Path $ReportPath)) {
        $ExistingReport = Get-Utf8FileText -Path $ReportPath
        Set-Content -Path $ReportPath -Value ($FailBanner + $ExistingReport) -Encoding UTF8
    }
    Write-Log "PUSH FAILED banner added - $(@($FailLines).Count) line(s), $(@(@($FailedPushSignals) | ForEach-Object { ([string]$_.Sig).Split('|',4)[1] } | Select-Object -Unique).Count) project(s)"
    Write-Host $FailBanner
}

# ── 7. Keep a copy of what was actually sent ─────────────────────────────────
# Saeed's request, 2026-09-11: "CREATE A LOG FOR WHATSAP MESSAGES. KEEP 3 LATEST
# ONES AND PURGE THE OLDER ONES AUTOMATICALLY."
#
# Why it is worth having: he had been getting already-approved items back in the
# approvals list "for a long time" and neither of us could say how long, because
# there was no record of any message after it left the machine. The report in
# docs\reports\ is what we MEANT to send; this is what we DID send, banners and
# all, byte for byte.
#
# Written BEFORE the send, so a message that fails to send is still on record.
$WhatsAppLogDir   = "C:\JeffLocal\logs\whatsapp-sent"
$KeepWhatsAppLogs = 3
$WhatsAppLogPath  = $null

# Only files this script itself writes are ever considered for deletion.
$WhatsAppLogPattern = "*-whatsapp.txt"

if (-not $DryRun) {
    try {
        if (-not (Test-Path $WhatsAppLogDir)) {
            New-Item -ItemType Directory -Path $WhatsAppLogDir -Force | Out-Null
        }
        $Stamp           = Get-Date -Format "yyyy-MM-dd-HHmm"
        $WhatsAppLogPath = Join-Path $WhatsAppLogDir "$Stamp-$Mode-whatsapp.txt"
        $SentText        = if (Test-Path $ReportPath) { Get-Utf8FileText -Path $ReportPath } else { $CombinedReport }
        $Header = @"
# WhatsApp message sent by combined_brief.ps1
# Mode: $Mode   Written: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# Source report: $ReportPath
# Characters: $(([string]$SentText).Length)
# ---------------------------------------------------------------------------

"@
        Set-Content -Path $WhatsAppLogPath -Value ($Header + $SentText) -Encoding UTF8
        Write-Log "WhatsApp copy saved: $WhatsAppLogPath ($(([string]$SentText).Length) chars)"
    } catch {
        # A failed archive must never stop the message going out.
        Write-Log "WARNING: could not save WhatsApp copy - $_"
        $WhatsAppLogPath = $null
    }
}

# ── 8. Send combined report via WhatsApp ─────────────────────────────────────
if ($DryRun) {
    Write-Log "DryRun: skipped WhatsApp send"
} else {
    $PythonScript = "C:\JeffLocal\scripts\daily\send_whatsapp.py"
    $SendOutcome  = "NOT SENT - sender script not found"
    if (Test-Path $PythonScript) {
        try {
            $result = python $PythonScript $ReportPath 2>&1
            $SendOutcome = "SENT - $result"
            Write-Log "WhatsApp send result: $result"
        } catch {
            $SendOutcome = "SEND FAILED - $_"
            Write-Log "WARNING: WhatsApp send failed - $_"
        }
    } else {
        Write-Log "WARNING: WhatsApp sender not found at $PythonScript"
    }
    # Record the outcome on the copy, so the archive says whether it arrived.
    if ($WhatsAppLogPath -and (Test-Path $WhatsAppLogPath)) {
        try {
            Add-Content -Path $WhatsAppLogPath -Encoding UTF8 `
                -Value "`n# ---------------------------------------------------------------------------`n# Send outcome: $SendOutcome`n"
        } catch {
            Write-Log "WARNING: could not record send outcome on the WhatsApp copy - $_"
        }
    }
}

# ── 9. Purge old WhatsApp copies, keeping the newest 3 ───────────────────────
# Saeed gave explicit written permission for this deletion on 2026-09-11
# ("PURGE THE OLDER ONES AUTOMATICALLY"). CLAUDE.md otherwise forbids deleting
# anything without it, so the scope is kept as narrow as it can be:
#   - one named folder, never recursed into
#   - only files matching $WhatsAppLogPattern, which only this script writes
#   - files only, never directories
#   - nothing deleted at all unless MORE than $KeepWhatsAppLogs exist
#   - each deletion logged by name, each wrapped in its own try/catch
# Newest-first by LastWriteTime, so the three most recent always survive even if
# a file is written out of order or a name is hand-edited.
if ($DryRun) {
    Write-Log "DryRun: skipped WhatsApp copy purge"
} elseif (Test-Path $WhatsAppLogDir) {
    try {
        $Copies = @(Get-ChildItem -Path $WhatsAppLogDir -Filter $WhatsAppLogPattern -File |
                    Sort-Object LastWriteTime -Descending)
        if (@($Copies).Count -gt $KeepWhatsAppLogs) {
            $Doomed = @($Copies | Select-Object -Skip $KeepWhatsAppLogs)
            foreach ($old in $Doomed) {
                try {
                    Remove-Item -LiteralPath $old.FullName -Force
                    Write-Log "WhatsApp copy purged: $($old.Name)"
                } catch {
                    Write-Log "WARNING: could not purge $($old.Name) - $_"
                }
            }
            Write-Log "WhatsApp copies: kept newest $KeepWhatsAppLogs, purged $(@($Doomed).Count)"
        } else {
            Write-Log "WhatsApp copies: $(@($Copies).Count) on disk, nothing to purge"
        }
    } catch {
        Write-Log "WARNING: WhatsApp copy purge failed - $_"
    }
}

Write-Log "combined_brief.ps1 complete - $Mode"

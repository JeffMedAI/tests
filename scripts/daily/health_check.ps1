# health_check.ps1
# Avamed (JeffLocal) - WEEKDAY MORNING HEALTH CHECK
#
# Runs Mon-Fri at 06:45 via the scheduled task
# "JeffLocal - Weekday Health Check 0645", fifteen minutes BEFORE the 07:00
# morning brief, so the brief can report real system health instead of guessing.
# Saeed's instruction, 2026-09-04.
#
# HISTORY - READ THIS BEFORE CHANGING ANYTHING
# A task called "JeffLocal - Health Check" was registered on 21 July 2026 pointing
# at this exact path. The script was never written. For 45 days it failed every
# five minutes with exit code -196608 ("the file does not exist") while showing
# State: Ready in Task Scheduler. Nobody noticed. That old task is retired; this
# is a real script with real checks. If you ever see a task pointed at a script
# that is not on disk, that is the same bug.
#
# WHAT THIS IS NOT
# This does NOT duplicate watchdog.ps1. The watchdog answers "are the services
# running" every 60 seconds, restarts them, and WhatsApps on failure. It has been
# doing that correctly since 19 Aug 2026 and is not touched here.
# This answers the question the watchdog deliberately does not: IS WORK FLOWING?
# Cases piling up unresolved, red flags unactioned, a stuck queue, a stale backup,
# a purge that has stopped running, commits that never reached GitHub, and other
# scheduled tasks quietly failing. Services can be perfectly "up" while all of
# that rots.
#
# SAFETY
# Read-only. It starts nothing, stops nothing, restarts nothing and writes nothing
# outside logs\health\. Databases are opened read-only (see health_check_db.py).
# It is deliberately NOT strict-mode: a health check that crashes on one bad value
# and reports nothing is worse than one that reports nine checks out of ten. Every
# check is wrapped, and a check that fails says so instead of taking the rest down.
#
# OUTPUT (logs\ is gitignored, so none of this reaches the repo)
#   logs\health\YYYY-MM-DD-health.json  - machine readable, full detail
#   logs\health\YYYY-MM-DD-health.txt   - the plain-English block the brief pastes in
#   logs\health\latest.txt              - same as above, always the newest run
# combined_brief.ps1 -Mode Morning reads the .txt. If it is missing, the brief says
# the health check did not run rather than staying silent about it.
#
# MANUAL USE
#   powershell -File scripts\daily\health_check.ps1           # run now (weekday)
#   powershell -File scripts\daily\health_check.ps1 -Force    # run now, any day
#   powershell -File scripts\daily\health_check.ps1 -DryRun   # print, write nothing
#
# Created: 2026-09-04

param(
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Continue"

$RepoRoot  = "C:\JeffLocal"
$SmRepo    = Join-Path $RepoRoot "SMCPHARMA"
$Python    = Join-Path $RepoRoot "dashboard\.venv\Scripts\python.exe"
$DbScript  = Join-Path $RepoRoot "scripts\daily\health_check_db.py"
$Today     = (Get-Date).ToString("yyyy-MM-dd")

$HealthDir = Join-Path $RepoRoot "logs\health"
$LogFile   = Join-Path $RepoRoot "logs\health_check.log"
$JsonOut   = Join-Path $HealthDir "$Today-health.json"
$TextOut   = Join-Path $HealthDir "$Today-health.txt"
$LatestOut = Join-Path $HealthDir "latest.txt"

if (-not (Test-Path $HealthDir)) { New-Item -ItemType Directory -Path $HealthDir -Force | Out-Null }

function Write-Log {
    param([string]$Message)
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss UTC")
    Write-Host "[$ts] $Message"
    Add-Content -Path $LogFile -Value "[$ts] $Message" -ErrorAction SilentlyContinue
}

# ── Findings ─────────────────────────────────────────────────────────────────
# Every check appends here. Level is OK, WATCH or PROBLEM.
#   OK      - nothing to say
#   WATCH   - worth a look, not urgent, nothing is broken
#   PROBLEM - something is actually wrong and needs a decision
$Findings = @()
function Add-Finding {
    param([string]$Level, [string]$Area, [string]$Text)
    $script:Findings += [PSCustomObject]@{ Level = $Level; Area = $Area; Text = $Text }
}

Write-Log "=================================================================="
Write-Log "health_check.ps1 started - $Today$(if ($DryRun) { ' (DryRun)' })"

$Day = (Get-Date).DayOfWeek
if (($Day -eq [DayOfWeek]::Saturday -or $Day -eq [DayOfWeek]::Sunday) -and -not $Force) {
    Write-Log "$Day - weekend, health check does not run. Use -Force to override. Exiting."
    exit 0
}

# ── 1. Services ──────────────────────────────────────────────────────────────
# A light confirmation only. The watchdog is the real service monitor and checks
# these every 60 seconds; this exists so the brief can say "everything is up" in
# one line rather than the reader having to trust silence.
$Services = @(
    @{ Name = "Main dashboard";     Port = 8765 },
    @{ Name = "Tenant 2 dashboard"; Port = 8766 },
    @{ Name = "n8n";                Port = 5678 },
    @{ Name = "Ollama (the AI)";    Port = 11434 }
)
$ServicesDown = @()
foreach ($svc in $Services) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $async  = $client.BeginConnect("127.0.0.1", $svc.Port, $null, $null)
        $up     = $async.AsyncWaitHandle.WaitOne(3000, $false) -and $client.Connected
        $client.Close()
        if (-not $up) { $ServicesDown += "$($svc.Name) (port $($svc.Port))" }
    } catch {
        $ServicesDown += "$($svc.Name) (port $($svc.Port)) - check failed"
    }
}
try {
    if (-not (Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue)) {
        $ServicesDown += "Cloudflare tunnel (the public web address)"
    }
} catch { }

if (@($ServicesDown).Count -gt 0) {
    Add-Finding "PROBLEM" "Services" ("DOWN: " + (@($ServicesDown) -join "; ") + ". The watchdog should be restarting these - if it has not, it is stuck.")
} else {
    Add-Finding "OK" "Services" "All 5 services up (dashboards, n8n, the AI, public web address)."
}

# ── 2. Queue - is work actually moving ───────────────────────────────────────
# The pipeline is: encrypted_raw -> incoming -> processing -> processed / failed
# / deadletter. Anything sitting in incoming or processing for a long time means
# the pipeline has stalled. failed and deadletter should both be empty.
$QueueCounts = @{}
# .gitkeep is a placeholder git needs to keep an empty folder in the repo. It is
# not a call. Counting it reported a call "stuck for 157079 minutes" on the first
# test run - a false alarm that would have cried wolf every morning.
function Get-QueueFiles {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return @() }
    return @(Get-ChildItem $Path -File -ErrorAction SilentlyContinue |
             Where-Object { $_.Name -ne ".gitkeep" -and -not $_.Name.StartsWith(".") })
}
try {
    foreach ($stage in @("encrypted_raw", "incoming", "processing", "processed", "failed", "deadletter")) {
        $p = Join-Path $RepoRoot "queue\$stage"
        $QueueCounts[$stage] = if (Test-Path $p) { @(Get-QueueFiles -Path $p).Count } else { -1 }
    }

    # Stuck = a call still sitting mid-pipeline more than an hour after it arrived.
    $StuckOldest = 0
    foreach ($stage in @("incoming", "processing")) {
        $oldest = Get-QueueFiles -Path (Join-Path $RepoRoot "queue\$stage") |
                  Sort-Object LastWriteTime | Select-Object -First 1
        if ($oldest) {
            $mins = [int]((Get-Date) - $oldest.LastWriteTime).TotalMinutes
            if ($mins -gt $StuckOldest) { $StuckOldest = $mins }
        }
    }

    if ($QueueCounts["deadletter"] -gt 0) {
        Add-Finding "PROBLEM" "Queue" "$($QueueCounts['deadletter']) call(s) in the dead-letter pile - these failed completely and there is still no tool to replay them."
    }
    if ($QueueCounts["failed"] -gt 0) {
        Add-Finding "WATCH" "Queue" "$($QueueCounts['failed']) call(s) sitting in 'failed'."
    }
    if ($StuckOldest -gt 60) {
        $StuckHow = if ($StuckOldest -gt 1440) { "$([int]($StuckOldest / 1440)) day(s)" } else { "$StuckOldest minutes" }
        Add-Finding "PROBLEM" "Queue" "A call has been stuck mid-pipeline for $StuckHow. The pipeline has stalled."
    } elseif ($QueueCounts["deadletter"] -le 0 -and $QueueCounts["failed"] -le 0) {
        Add-Finding "OK" "Queue" "Queue clear - nothing failed, nothing stuck, nothing in the dead-letter pile."
    }
} catch {
    Add-Finding "WATCH" "Queue" "Could not read the queue folders - $_"
}

# ── 3. Databases - is anything sitting unactioned ────────────────────────────
$DbResults = @()
try {
    if ((Test-Path $Python) -and (Test-Path $DbScript)) {
        $raw = & $Python $DbScript 2>$null
        $parsed = $raw | ConvertFrom-Json
        $DbResults = @($parsed.databases)

        foreach ($db in $DbResults) {
            if (-not $db.ok) {
                Add-Finding "PROBLEM" "Database" "$($db.label): cannot be checked - $($db.error)"
                continue
            }
            if ($db.open_emergency -gt 0) {
                Add-Finding "PROBLEM" "Cases" "$($db.label): $($db.open_emergency) EMERGENCY case(s) still open."
            }
            if ($db.open_red_flags -gt 0) {
                Add-Finding "PROBLEM" "Cases" "$($db.label): $($db.open_red_flags) case(s) with a red flag still open."
            }
            if ($db.open_over_24h -gt 0) {
                Add-Finding "WATCH" "Cases" "$($db.label): $($db.open_over_24h) case(s) open for more than a day."
            }
            if ($db.open_identity_issues -gt 0) {
                Add-Finding "WATCH" "Cases" "$($db.label): $($db.open_identity_issues) open case(s) where we could not confirm who the patient is."
            }
            if ($db.open_total -eq 0) {
                Add-Finding "OK" "Cases" "$($db.label): nothing outstanding - all $($db.cases_total) case(s) dealt with."
            }
        }
    } else {
        Add-Finding "WATCH" "Database" "Cannot check the databases - python or health_check_db.py is missing."
    }
} catch {
    Add-Finding "WATCH" "Database" "Database check failed - $_"
}

# ── 4. Disk space ────────────────────────────────────────────────────────────
try {
    $drive  = Get-PSDrive -Name C -ErrorAction Stop
    $freeGB = [math]::Round($drive.Free / 1GB, 1)
    $totGB  = [math]::Round(($drive.Free + $drive.Used) / 1GB, 1)
    if ($freeGB -lt 10) {
        Add-Finding "PROBLEM" "Disk" "Only $freeGB GB free of $totGB GB. Recordings and backups will start failing."
    } elseif ($freeGB -lt 25) {
        Add-Finding "WATCH" "Disk" "$freeGB GB free of $totGB GB - getting tight."
    } else {
        Add-Finding "OK" "Disk" "$freeGB GB free of $totGB GB."
    }
} catch {
    Add-Finding "WATCH" "Disk" "Could not read disk space - $_"
}

# ── 5. Backups ───────────────────────────────────────────────────────────────
# JeffLocal-SQLiteBackup runs 02:15 daily. If the newest backup is older than a
# day and a half, it has stopped and nobody was told.
try {
    $newest = Get-ChildItem (Join-Path $RepoRoot "backups") -File -ErrorAction SilentlyContinue |
              Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $newest) {
        Add-Finding "PROBLEM" "Backups" "No database backups found at all."
    } else {
        $hrs = [int]((Get-Date) - $newest.LastWriteTime).TotalHours
        if ($hrs -gt 36) {
            Add-Finding "PROBLEM" "Backups" "Newest backup is $hrs hours old. The nightly backup has stopped."
        } else {
            Add-Finding "OK" "Backups" "Database backed up $hrs hour(s) ago."
        }
    }
} catch {
    Add-Finding "WATCH" "Backups" "Could not check backups - $_"
}

# ── 6. GDPR purge - the 90-day deletion obligation ───────────────────────────
# Reads the compliance audit trail the purge itself writes. This is the evidence
# a DSPT assessor would ask for, so a silent failure here is a compliance gap,
# not just a technical one.
try {
    $purgeLog = Join-Path $RepoRoot "docs\compliance\gdpr_purge_log.jsonl"
    if (-not (Test-Path $purgeLog)) {
        Add-Finding "WATCH" "GDPR purge" "No purge audit trail found."
    } else {
        # Only REAL runs count. The audit trail also records dry runs, and a manual
        # dry run made this report a compliance failure that had not happened -
        # caught on the first test, 2026-09-04.
        $entry = $null
        foreach ($line in @(Get-Content $purgeLog -Tail 40 -ErrorAction SilentlyContinue)) {
            try {
                $e = $line | ConvertFrom-Json
                if (-not $e.dry_run) { $entry = $e }
            } catch { }
        }
        if (-not $entry) {
            Add-Finding "WATCH" "GDPR purge" "No real (non-test) deletion run found in the recent audit trail."
            $entry = $null
        }
    }
    if ($entry) {
        $when  = [datetime]$entry.timestamp_utc
        $hrs   = [int]((Get-Date).ToUniversalTime() - $when.ToUniversalTime()).TotalHours
        $status = "$($entry.status)"
        if ($status -eq "error") {
            Add-Finding "PROBLEM" "GDPR purge" "The last 90-day deletion run FAILED ($hrs hours ago). This is a compliance gap, not just a bug."
        } elseif ($hrs -gt 36) {
            Add-Finding "WATCH" "GDPR purge" "Last successful deletion run was $hrs hours ago."
        } else {
            Add-Finding "OK" "GDPR purge" "90-day deletion ran cleanly $hrs hour(s) ago."
        }
    }
} catch {
    Add-Finding "WATCH" "GDPR purge" "Could not read the purge audit trail - $_"
}

# ── 7. Work saved to GitHub ──────────────────────────────────────────────────
# Catches the failure mode the push guard creates on purpose (held push) and the
# one nobody intends (close stopped running, commits piling up locally).
foreach ($repo in @(@{N="Avamed"; P=$RepoRoot}, @{N="St Marks"; P=$SmRepo})) {
    try {
        if (-not (Test-Path (Join-Path $repo.P ".git"))) { continue }
        $unpushed = & git -C $repo.P rev-list --count "@{u}..HEAD" 2>$null
        $lastTs   = & git -C $repo.P log -1 --format=%ct 2>$null
        $ageHrs   = if ($lastTs) { [int]((Get-Date).ToUniversalTime() - [datetimeoffset]::FromUnixTimeSeconds([long]$lastTs).UtcDateTime).TotalHours } else { -1 }

        if ($unpushed -and [int]$unpushed -gt 0) {
            Add-Finding "WATCH" "Saved work" "$($repo.N): $unpushed change(s) saved here but NOT sent to GitHub. Usually the push guard holding unfinished work."
        }
        if ($ageHrs -gt 72) {
            Add-Finding "WATCH" "Saved work" "$($repo.N): nothing saved for $ageHrs hours."
        }
        if ((-not $unpushed -or [int]$unpushed -eq 0) -and $ageHrs -ge 0 -and $ageHrs -le 72) {
            Add-Finding "OK" "Saved work" "$($repo.N): everything saved and sent to GitHub (last change $ageHrs hour(s) ago)."
        }
    } catch {
        Add-Finding "WATCH" "Saved work" "$($repo.N): could not check git - $_"
    }
}

# ── 8. Last night's session close ────────────────────────────────────────────
# The 18:30 close writes a marker. No marker on a weekday morning means last
# night has no session log, no handover note and no restore point.
try {
    $back = 1
    $prev = (Get-Date).AddDays(-1)
    while ($prev.DayOfWeek -eq [DayOfWeek]::Saturday -or $prev.DayOfWeek -eq [DayOfWeek]::Sunday) {
        $prev = $prev.AddDays(-1); $back++
    }
    # The 18:30 close was created on 2026-09-04. No marker can exist before that
    # date - before it, the close ran inside the 19:00 brief and left no marker.
    # Without this cutoff every morning reports a close failure that never happened.
    $CloseTaskStart = [datetime]"2026-09-04"
    $prevMarker = Join-Path $RepoRoot ("logs\close-state\" + $prev.ToString("yyyy-MM-dd") + "-close.txt")
    if ($prev.Date -lt $CloseTaskStart) {
        Add-Finding "OK" "Session close" "Nothing to check yet - the 18:30 close starts from 4 Sep 2026."
    } elseif (Test-Path $prevMarker) {
        Add-Finding "OK" "Session close" "Last working day ($($prev.ToString('ddd dd MMM'))) closed properly."
    } else {
        Add-Finding "PROBLEM" "Session close" "The 18:30 close did NOT run on $($prev.ToString('ddd dd MMM')) - that day has no session log, no handover note and no restore point."
    }
} catch {
    Add-Finding "WATCH" "Session close" "Could not check the close marker - $_"
}

# ── 9. Other scheduled tasks quietly failing ─────────────────────────────────
# This check exists because of the 21 Jul - 4 Sep 2026 phantom health check: a task
# showing State: Ready, failing every five minutes for 45 days, telling nobody.
# Long-running service tasks are excluded - they are killed by design and always
# report a non-zero code.
try {
    $Continuous = @("JeffLocal - Service Watchdog", "JeffLocal Dashboard", "JeffLocal n8n",
                    "JeffLocal Encrypted Intake Cycle")
    # Task Scheduler codes that are NOT failures. 267011 is "has not run yet" - a
    # brand new task reports it until its first firing, and treating it as a
    # failure made a task created 20 minutes earlier look broken (2026-09-04).
    $NotFailures = @(267011, 267009, 267014, 267010)
    $bad = @()
    foreach ($t in @(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.TaskName -like "*JeffLocal*" })) {
        if ($t.State -eq "Disabled") { continue }
        if ($Continuous -contains $t.TaskName) { continue }
        $i = $t | Get-ScheduledTaskInfo -ErrorAction SilentlyContinue
        if (-not $i) { continue }
        # A never-run task reports a placeholder date decades in the past.
        if ($null -eq $i.LastRunTime -or $i.LastRunTime -lt [datetime]"2000-01-01") { continue }
        if ($NotFailures -contains $i.LastTaskResult) { continue }
        if ($i.LastTaskResult -ne 0) {
            $bad += "$($t.TaskName) (code $($i.LastTaskResult))"
        }
    }
    if (@($bad).Count -gt 0) {
        Add-Finding "PROBLEM" "Automation" ("These scheduled jobs failed their last run: " + (@($bad) -join "; ") + ".")
    } else {
        Add-Finding "OK" "Automation" "All scheduled jobs completed their last run cleanly."
    }
} catch {
    Add-Finding "WATCH" "Automation" "Could not read the scheduled jobs - $_"
}

# ── Verdict + plain-English block ────────────────────────────────────────────
$Problems = @($Findings | Where-Object { $_.Level -eq "PROBLEM" })
$Watches  = @($Findings | Where-Object { $_.Level -eq "WATCH" })
$Oks      = @($Findings | Where-Object { $_.Level -eq "OK" })

if (@($Problems).Count -gt 0) {
    $Verdict = "NEEDS ATTENTION - $(@($Problems).Count) problem(s)"
} elseif (@($Watches).Count -gt 0) {
    $Verdict = "MOSTLY FINE - $(@($Watches).Count) thing(s) worth a look"
} else {
    $Verdict = "ALL GOOD"
}

$Lines = @()
$Lines += "SYSTEM HEALTH ($(Get-Date -Format 'HH:mm')): $Verdict"
$Lines += ""
if (@($Problems).Count -gt 0) {
    $Lines += "NEEDS A DECISION FROM YOU:"
    foreach ($f in $Problems) { $Lines += "  - [$($f.Area)] $($f.Text)" }
    $Lines += ""
}
if (@($Watches).Count -gt 0) {
    $Lines += "WORTH A LOOK, NOT URGENT:"
    foreach ($f in $Watches) { $Lines += "  - [$($f.Area)] $($f.Text)" }
    $Lines += ""
}
$Lines += "WORKING NORMALLY:"
foreach ($f in $Oks) { $Lines += "  - [$($f.Area)] $($f.Text)" }

$Block = ($Lines -join [Environment]::NewLine)

Write-Host ""
Write-Host $Block
Write-Host ""

if ($DryRun) {
    Write-Log "DryRun: would write $TextOut and $JsonOut"
} else {
    Set-Content -Path $TextOut   -Value $Block -Encoding UTF8
    Set-Content -Path $LatestOut -Value $Block -Encoding UTF8
    $payload = [PSCustomObject]@{
        date      = $Today
        ran_at    = (Get-Date).ToString("s")
        verdict   = $Verdict
        problems  = @($Problems).Count
        watches   = @($Watches).Count
        findings  = $Findings
        queue     = $QueueCounts
        databases = $DbResults
    }
    $payload | ConvertTo-Json -Depth 6 | Set-Content -Path $JsonOut -Encoding UTF8
    Write-Log "Health written: $TextOut"

    # 30 days of history is enough to spot a trend; logs\ is gitignored anyway.
    Get-ChildItem $HealthDir -Filter "*-health.*" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

Write-Log "health_check.ps1 finished - $Verdict"
exit 0

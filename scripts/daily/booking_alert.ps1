# booking_alert.ps1
# St Marks Pharmacy - "BOOKING WAITING OVER 1 HOUR" WhatsApp reminder.
# Saeed's instruction, 2026-10-06: ONE WhatsApp to his own number when a new
# website booking has waited more than 1 hour. Mon-Fri 08:30-18:30 only. No
# patient data in the message - it just points staff at the dashboard.
#
# HOW IT WORKS
# The St Marks website (a Cloudflare Worker) cannot send WhatsApp. This PC can.
# Every 15 minutes the scheduled task "JeffLocal - Booking Alert" runs this script,
# which asks the website: "which bookings are still new?" The answer is booking
# numbers and times ONLY (GET /api/booking-status, bearer token) - no names,
# phones or messages ever leave the website. Any booking older than 60 minutes
# that we have not already warned about triggers ONE WhatsApp via the existing
# send_whatsapp.py (same recipient safety, mute flag and dedup as the briefings).
#
# SECRET
# The bearer token lives in C:\JeffLocal\config\local_secrets.json (gitignored)
# under the key "booking_alert_token". It must equal the Worker secret
# BOOKING_ALERT_TOKEN. Never put it in this file or in git.
#
# STATE (logs\ is gitignored)
#   logs\booking-alerts\alerted.txt   booking ids already warned about, one per line.
#                                     (Plain text on purpose: a JSON file here was mangled by
#                                     Windows PowerShell 5.1 on 2026-10-06 and caused a repeat
#                                     WhatsApp every 15 minutes. Do not go back to JSON.)
#   logs\booking-alerts\run.log       one line per run
#
# TESTING
#   -DryRun      print the message instead of sending, and do not record state
#   -NowOverride pretend it is this time (London), to test the opening-hours rule
#   -TestStampsJson  use this JSON ({"new":[{"id":1,"created_at":"..."}]}) instead
#                    of calling the website
#
# LIMITS (be honest about them)
#   - Only works while this PC is on and WhatsApp Web is signed in.
#   - send_whatsapp.py cannot confirm delivery. "Alerted" here means the send
#     script exited 0.
#   - A booking made late in the day is first flagged next morning at 08:30.

param(
    [switch]$DryRun,
    [datetime]$NowOverride,
    [string]$TestStampsJson,
    [string]$StateDirOverride,   # tests only: keep test state out of the real state folder
    [string]$SendScriptOverride  # tests only: a stub instead of WhatsApp
)

$ErrorActionPreference = 'Stop'

$Root        = 'C:\JeffLocal'
$StateDir    = if ($StateDirOverride) { $StateDirOverride } else { Join-Path $Root 'logs\booking-alerts' }
$StateFile   = Join-Path $StateDir 'alerted.txt'
$RunLog      = Join-Path $StateDir 'run.log'
$SecretsFile = Join-Path $Root 'config\local_secrets.json'
$SendScript  = Join-Path $Root 'scripts\daily\send_whatsapp.py'
$StatusUrl   = 'https://stmarkspharmacy.co.uk/api/booking-status'
$DashUrl     = 'https://stmarkspharmacy.co.uk/staff'
$WaitMinutes = 60

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

function Write-Log([string]$msg) {
    $line = '{0:yyyy-MM-dd HH:mm:ss} {1}' -f (Get-Date), $msg
    Add-Content -Path $RunLog -Value $line -Encoding UTF8
    Write-Host $line
}

try {
    # --- 1. Opening hours (London time), Mon-Fri 08:30-18:30 -----------------
    $london = [TimeZoneInfo]::FindSystemTimeZoneById('GMT Standard Time')
    if ($PSBoundParameters.ContainsKey('NowOverride')) { $nowLocal = $NowOverride }
    else { $nowLocal = [TimeZoneInfo]::ConvertTimeFromUtc((Get-Date).ToUniversalTime(), $london) }

    $minutes = $nowLocal.Hour * 60 + $nowLocal.Minute
    $weekday = $nowLocal.DayOfWeek -notin @([DayOfWeek]::Saturday, [DayOfWeek]::Sunday)
    if (-not $weekday -or $minutes -lt (8 * 60 + 30) -or $minutes -gt (18 * 60 + 30)) {
        Write-Log ('Outside opening hours ({0:ddd HH:mm} London) - nothing to do.' -f $nowLocal)
        exit 0
    }

    # --- 2. Which bookings are still new? ------------------------------------
    if ($TestStampsJson) {
        $answer = $TestStampsJson | ConvertFrom-Json
    } else {
        if (-not (Test-Path $SecretsFile)) { throw "Secrets file missing: $SecretsFile" }
        $token = (Get-Content $SecretsFile -Raw | ConvertFrom-Json).booking_alert_token
        if (-not $token) { throw 'booking_alert_token not set in local_secrets.json' }
        $answer = Invoke-RestMethod -Uri $StatusUrl -Method Get -TimeoutSec 30 `
            -Headers @{ Authorization = "Bearer $token" }
    }
    if (-not $answer.ok -and -not $TestStampsJson) { throw 'Website did not return ok' }

    # --- 3. Which are over an hour old and not yet warned about? -------------
    [int[]]$alerted = @()
    if (Test-Path $StateFile) {
        $alerted = @(Get-Content $StateFile | Where-Object { $_ -match '^\s*\d+\s*$' } | ForEach-Object { [int]$_.Trim() })
    }

    $nowUtc = (Get-Date).ToUniversalTime()
    if ($PSBoundParameters.ContainsKey('NowOverride')) {
        $nowUtc = [TimeZoneInfo]::ConvertTimeToUtc($nowLocal, $london)
    }
    $due = @()
    foreach ($b in @($answer.new)) {
        $created = [datetime]::Parse([string]$b.created_at, $null,
            [System.Globalization.DateTimeStyles]::AdjustToUniversal -bor
            [System.Globalization.DateTimeStyles]::AssumeUniversal)
        if (($nowUtc - $created).TotalMinutes -gt $WaitMinutes -and ($alerted -notcontains [int]$b.id)) {
            $due += [int]$b.id
        }
    }
    if ($due.Count -eq 0) { Write-Log 'No new booking waiting over 1 hour (or already warned).'; exit 0 }

    # --- 4. Build the message: NO patient data -------------------------------
    $word = if ($due.Count -eq 1) { 'booking request is' } else { 'booking requests are' }
    $message = "St Marks Pharmacy: $($due.Count) website $word still waiting after more than 1 hour. " +
               "Please open the staff dashboard and action it: $DashUrl"

    if ($DryRun) {
        Write-Log "DRY RUN - would send: $message  (ids: $($due -join ','))"
        exit 0
    }

    # --- 5. Send via the existing briefing sender, record only on success ----
    $tmp = Join-Path $StateDir 'pending_message.txt'
    Set-Content -Path $tmp -Value $message -Encoding UTF8
    if ($SendScriptOverride) { $out = & $SendScriptOverride $tmp 2>&1 } else { $out = & python $SendScript $tmp 2>&1 }
    $code = $LASTEXITCODE
    if ($code -ne 0) { throw "send_whatsapp.py exited $code : $($out -join ' ')" }

    # Record FIRST-class evidence of the send: append ids as plain lines.
    Add-Content -Path $StateFile -Value ($due | ForEach-Object { [string]$_ }) -Encoding ASCII
    Write-Log "Sent reminder for booking id(s) $($due -join ',')."
    exit 0
}
catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    exit 1
}

param(
    [Parameter(Mandatory = $true)]
    [string]$N8nWebhookUrl,
    [switch]$ConfirmSimulation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = "C:\JeffLocal"
$BatchId = "N8NTEST-PRODSIM-" + (Get-Date -Format "yyyyMMdd-HHmmss")
$ArtifactPattern = "*N8NTEST-PRODSIM*"
$ArchiveRoot = Join-Path $Root ("backup\prodsim_regeneration_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
$Sender = Join-Path $Root "tests\send_5_prodsim_webhook_test_calls.py"
$Python = Join-Path $Root "dashboard\.venv\Scripts\python.exe"
$Report = [ordered]@{
    summary_verdict = "NEEDS ATTENTION"
    preflight = [ordered]@{}
    batch = [ordered]@{ batch_id = $BatchId; call_ids = @() }
    processing = [ordered]@{}
    safety = [ordered]@{
        google_push = "disabled_for_test"
        external_notifications = "not_sent_by_runner"
        external_voice_calls = "not_called_by_runner"
    }
    expected_outcomes = @()
    dashboard_api = [ordered]@{}
    n8n = [ordered]@{}
    artifacts = [ordered]@{}
    remaining_risks = @()
}

function Fail-Sim {
    param([string]$Message)
    $Report.summary_verdict = "FAIL"
    $Report.remaining_risks += $Message
    $Report | ConvertTo-Json -Depth 8
    throw $Message
}

function Invoke-LocalJson {
    param([string]$Url)
    try {
        return Invoke-RestMethod -Uri $Url -TimeoutSec 10
    }
    catch {
        return [pscustomobject]@{ ok = $false; error = $_.Exception.Message }
    }
}

function Test-LocalUrl {
    param([string]$Url)
    $uri = [Uri]$Url
    return ($uri.Scheme -in @("http", "https") -and $uri.Host -in @("localhost", "127.0.0.1", "::1"))
}

function Count-Files {
    param([string]$Folder, [string]$Filter)
    if (-not (Test-Path -LiteralPath $Folder)) { return 0 }
    return @(Get-ChildItem -LiteralPath $Folder -Filter $Filter -File -ErrorAction SilentlyContinue).Count
}

function Archive-ProdsimArtifacts {
    $folders = @(
        "queue\encrypted_raw",
        "queue\incoming",
        "queue\processed",
        "queue\failed",
        "queue\deadletter",
        "outputs\handoff_json",
        "outputs\debug",
        "outputs\ollama_raw",
        "logs\transcripts"
    )
    $summary = @()
    foreach ($relative in $folders) {
        $source = Join-Path $Root $relative
        $count = 0
        if (Test-Path -LiteralPath $source) {
            foreach ($file in Get-ChildItem -LiteralPath $source -Filter $ArtifactPattern -File -ErrorAction SilentlyContinue) {
                if ($file.Name -notlike $ArtifactPattern) {
                    Fail-Sim "Safety check refused non-PRODSIM file: $($file.FullName)"
                }
                $targetFolder = Join-Path $ArchiveRoot $relative
                New-Item -ItemType Directory -Force -Path $targetFolder | Out-Null
                Move-Item -LiteralPath $file.FullName -Destination (Join-Path $targetFolder $file.Name) -Force
                $count++
            }
        }
        $summary += [ordered]@{ folder = $relative; archived = $count }
    }
    return $summary
}

function Get-Handoff {
    param([string]$CallId)
    $path = Join-Path $Root "outputs\handoff_json\$($CallId)_handoff.json"
    if (-not (Test-Path -LiteralPath $path)) {
        return $null
    }
    return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
}

function Validate-Outcome {
    param(
        [string]$CallId,
        [string]$ExpectedRequestType,
        [string]$ExpectedPriority,
        [Nullable[bool]]$ExpectedSafeToQueue,
        [Nullable[bool]]$ExpectedStaffReviewRequired,
        [Nullable[bool]]$ExpectedRedFlagsPresent,
        [string[]]$AllowedVerificationStatus = @()
    )
    $handoff = Get-Handoff -CallId $CallId
    if ($null -eq $handoff) {
        return [ordered]@{ call_id = $CallId; pass = $false; error = "missing handoff" }
    }
    $actual = [ordered]@{
        request_type = $handoff.request_type
        priority = $handoff.priority
        safe_to_queue = [bool]$handoff.safe_to_queue
        staff_review_required = [bool]$handoff.staff_review_required
        red_flags_present = [bool]$handoff.red_flags_present
        verification_status = $handoff.verification_status
    }
    $errors = @()
    if ($actual.request_type -ne $ExpectedRequestType) { $errors += "request_type expected $ExpectedRequestType got $($actual.request_type)" }
    if ($actual.priority -ne $ExpectedPriority) { $errors += "priority expected $ExpectedPriority got $($actual.priority)" }
    if ($null -ne $ExpectedSafeToQueue -and $actual.safe_to_queue -ne [bool]$ExpectedSafeToQueue) { $errors += "safe_to_queue expected $ExpectedSafeToQueue got $($actual.safe_to_queue)" }
    if ($null -ne $ExpectedStaffReviewRequired -and $actual.staff_review_required -ne [bool]$ExpectedStaffReviewRequired) { $errors += "staff_review_required expected $ExpectedStaffReviewRequired got $($actual.staff_review_required)" }
    if ($null -ne $ExpectedRedFlagsPresent -and $actual.red_flags_present -ne [bool]$ExpectedRedFlagsPresent) { $errors += "red_flags_present expected $ExpectedRedFlagsPresent got $($actual.red_flags_present)" }
    if ($AllowedVerificationStatus.Count -gt 0 -and $actual.verification_status -notin $AllowedVerificationStatus) { $errors += "verification_status expected one of $($AllowedVerificationStatus -join ', ') got $($actual.verification_status)" }
    return [ordered]@{
        call_id = $CallId
        expected = [ordered]@{
            request_type = $ExpectedRequestType
            priority = $ExpectedPriority
            safe_to_queue = $ExpectedSafeToQueue
            staff_review_required = $ExpectedStaffReviewRequired
            red_flags_present = $ExpectedRedFlagsPresent
            verification_status = $AllowedVerificationStatus
        }
        actual = $actual
        pass = ($errors.Count -eq 0)
        errors = $errors
    }
}

Write-Host "JeffLocal production-grade local simulation preflight"
Write-Host "Webhook URL: $N8nWebhookUrl"
Write-Host "Batch ID: $BatchId"
Write-Host "Safety: Google push disabled, no external notifications, localhost webhook required."

if (-not (Test-LocalUrl -Url $N8nWebhookUrl)) {
    Fail-Sim "Webhook URL must be localhost/127.0.0.1/::1"
}
if (-not $ConfirmSimulation) {
    Write-Host ""
    Write-Host "Simulation not started. Re-run with -ConfirmSimulation to archive prior PRODSIM artifacts and send 5 local test calls."
    Write-Host "Planned command:"
    Write-Host "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\run_production_grade_simulation.ps1 -N8nWebhookUrl `"$N8nWebhookUrl`" -ConfirmSimulation"
    exit 2
}

$health = Invoke-LocalJson "http://127.0.0.1:8765/api/health"
$services = Invoke-LocalJson "http://127.0.0.1:8765/api/services/status"
$alertsPage = Invoke-WebRequest -Uri "http://127.0.0.1:8765/alerts" -UseBasicParsing -TimeoutSec 10
$n8nHome = Invoke-WebRequest -Uri "http://localhost:5678/" -UseBasicParsing -TimeoutSec 10
$Report.preflight.dashboard_health = $health
$Report.preflight.services_status = $services
$Report.preflight.alerts_page_status = [int]$alertsPage.StatusCode
$Report.preflight.n8n_home_status = [int]$n8nHome.StatusCode
if (-not $health.ok) { Fail-Sim "Dashboard health failed" }
if ($alertsPage.StatusCode -ne 200) { Fail-Sim "Dashboard /alerts failed" }
if ($n8nHome.StatusCode -lt 200 -or $n8nHome.StatusCode -ge 500) { Fail-Sim "n8n homepage failed" }

$Report.artifacts.archive = Archive-ProdsimArtifacts

if (-not (Test-Path -LiteralPath $Python)) { Fail-Sim "Python not found: $Python" }
if (-not (Test-Path -LiteralPath $Sender)) { Fail-Sim "Sender not found: $Sender" }

$senderOutput = & $Python $Sender --url $N8nWebhookUrl --batch-id $BatchId
if ($LASTEXITCODE -ne 0) {
    Fail-Sim "Sender failed: $senderOutput"
}
$Report.n8n.webhook_response = ($senderOutput | Out-String | ConvertFrom-Json)

$callIds = @(
    "$BatchId-001-PRESCRIPTION",
    "$BatchId-002-SICKNOTE",
    "$BatchId-003-REFERRAL",
    "$BatchId-004-IDENTITY",
    "$BatchId-005-REDFLAG"
)
$Report.batch.call_ids = $callIds

$handoffs = Count-Files -Folder (Join-Path $Root "outputs\handoff_json") -Filter "$BatchId*_handoff.json"
$processed = Count-Files -Folder (Join-Path $Root "queue\processed") -Filter "$BatchId*.json"
$failed = Count-Files -Folder (Join-Path $Root "queue\failed") -Filter "$BatchId*.json"
$deadletter = Count-Files -Folder (Join-Path $Root "queue\deadletter") -Filter "$BatchId*.json"
$Report.processing = [ordered]@{ handoffs = $handoffs; processed = $processed; failed = $failed; deadletter = $deadletter }
if ($handoffs -ne 5) { Fail-Sim "Expected 5 handoffs, found $handoffs" }
if ($processed -ne 5) { Fail-Sim "Expected 5 processed files, found $processed" }
if ($failed -ne 0) { Fail-Sim "Expected 0 failed files, found $failed" }
if ($deadletter -ne 0) { Fail-Sim "Expected 0 deadletter files, found $deadletter" }

$Report.expected_outcomes = @(
    (Validate-Outcome -CallId $callIds[0] -ExpectedRequestType "prescription" -ExpectedPriority "routine" -ExpectedSafeToQueue $true -ExpectedStaffReviewRequired $false -ExpectedRedFlagsPresent $false),
    (Validate-Outcome -CallId $callIds[1] -ExpectedRequestType "sick_note" -ExpectedPriority "routine" -ExpectedSafeToQueue $true -ExpectedStaffReviewRequired $true -ExpectedRedFlagsPresent $false),
    (Validate-Outcome -CallId $callIds[2] -ExpectedRequestType "referral" -ExpectedPriority "routine" -ExpectedSafeToQueue $true -ExpectedStaffReviewRequired $true -ExpectedRedFlagsPresent $false),
    (Validate-Outcome -CallId $callIds[3] -ExpectedRequestType "prescription" -ExpectedPriority "review_required" -ExpectedSafeToQueue $true -ExpectedStaffReviewRequired $true -ExpectedRedFlagsPresent $false -AllowedVerificationStatus @("possible_match", "possible_match_weak", "needs_review", "no_match", "insufficient_data")),
    (Validate-Outcome -CallId $callIds[4] -ExpectedRequestType "appointment_redirect" -ExpectedPriority "999 Emergency" -ExpectedSafeToQueue $false -ExpectedStaffReviewRequired $true -ExpectedRedFlagsPresent $true)
)
if (@($Report.expected_outcomes | Where-Object { -not $_.pass }).Count -gt 0) {
    Fail-Sim "One or more expected outcome checks failed"
}

$Report.dashboard_api.health = Invoke-LocalJson "http://127.0.0.1:8765/api/health"
$Report.dashboard_api.services = Invoke-LocalJson "http://127.0.0.1:8765/api/services/status"
$Report.dashboard_api.red_flags = Invoke-LocalJson "http://127.0.0.1:8765/api/red-flags"
$Report.dashboard_api.daily_summary = Invoke-LocalJson "http://127.0.0.1:8765/api/daily-summary"
$Report.dashboard_api.alerts_recent = Invoke-LocalJson "http://127.0.0.1:8765/api/alerts/recent?limit=20"
$Report.n8n.scan_workflows = "Manual n8n workflow execution required unless n8n API automation is configured: JeffLocal - 03 Red Flag Scan, JeffLocal - 04 Overdue Scan, JeffLocal - 05 Daily Summary."
$Report.artifacts.handoffs = @(Get-ChildItem -Path (Join-Path $Root "outputs\handoff_json") -Filter "$BatchId*_handoff.json" -File | Select-Object -ExpandProperty FullName)
$Report.artifacts.processed = @(Get-ChildItem -Path (Join-Path $Root "queue\processed") -Filter "$BatchId*.json" -File | Select-Object -ExpandProperty FullName)
$Report.summary_verdict = "PASS"
$Report | ConvertTo-Json -Depth 10

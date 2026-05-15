param(
    [Parameter(Mandatory = $true)]
    [string]$QueueJsonPath,

    [string]$MonitoringConfigPath = "C:\JeffLocal\config\model_monitoring.json",
    [string]$MonitoringBasePath = "C:\JeffLocal\logs\model_monitoring"
)

$ErrorActionPreference = "Stop"

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Join-ArrayText {
    param([object]$Value)

    if ($null -eq $Value) { return "" }
    if ($Value -is [System.Array]) {
        return (($Value | ForEach-Object { "$_" }) -join ", ")
    }
    return "$Value"
}

Ensure-Dir $MonitoringBasePath
Ensure-Dir (Join-Path $MonitoringBasePath "Runs")

if (-not (Test-Path -LiteralPath $QueueJsonPath)) {
    throw "Queue JSON not found: $QueueJsonPath"
}

if (-not (Test-Path -LiteralPath $MonitoringConfigPath)) {
    throw "Monitoring config not found: $MonitoringConfigPath"
}

$config = Get-Content -LiteralPath $MonitoringConfigPath -Raw | ConvertFrom-Json
$queue = Get-Content -LiteralPath $QueueJsonPath -Raw | ConvertFrom-Json

$issues = @()
$totalScore = 0
$hardFailure = $false

# 1. Schema/basic structure score: 25
$schemaScore = 25
$requiredTopLevel = @(
    "call_id",
    "call_timestamp",
    "workflow",
    "request_type",
    "normalized_input",
    "verification_status",
    "task_title",
    "task_body"
)

foreach ($field in $requiredTopLevel) {
    if ($null -eq $queue.$field -or "$($queue.$field)" -eq "") {
        $schemaScore -= 5
        $issues += "missing_top_level_$field"
    }
}

if ($schemaScore -lt 0) { $schemaScore = 0 }
if ($schemaScore -eq 0) { $hardFailure = $true }

# 2. Required field capture score: 20
$requiredFieldScore = 20
if ([string]::IsNullOrWhiteSpace($queue.normalized_input.patient_name)) {
    $requiredFieldScore -= 7
    $issues += "patient_name_missing"
}
if ([string]::IsNullOrWhiteSpace($queue.normalized_input.dob)) {
    $requiredFieldScore -= 7
    $issues += "dob_missing"
}
if ($null -eq $queue.normalized_input.medications_requested -or $queue.normalized_input.medications_requested.Count -eq 0) {
    $requiredFieldScore -= 6
    $issues += "medications_missing"
}
if ($requiredFieldScore -lt 0) { $requiredFieldScore = 0 }

# 3. Transcript/consistency score: 20
$consistencyScore = 20
if ([string]::IsNullOrWhiteSpace($queue.raw_transcript)) {
    $consistencyScore -= 8
    $issues += "raw_transcript_missing"
}
if ([string]::IsNullOrWhiteSpace($queue.transcript_summary)) {
    $consistencyScore -= 8
    $issues += "summary_missing"
}
if ($queue.transcript_quality_flag -eq "review_needed") {
    $consistencyScore -= 4
}
if ($consistencyScore -lt 0) { $consistencyScore = 0 }

# 4. Summary quality score: 15
$summaryScore = 15
$summaryText = "$($queue.transcript_summary)"
if ([string]::IsNullOrWhiteSpace($summaryText)) {
    $summaryScore = 0
    $issues += "transcript_summary_blank"
}
elseif ($summaryText.Length -lt 25) {
    $summaryScore -= 8
    $issues += "transcript_summary_too_short"
}
if ($summaryText -notmatch "Caller requested") {
    $summaryScore -= 3
}
if ($summaryScore -lt 0) { $summaryScore = 0 }

# 5. Handoff usability score: 10
$handoffScore = 10
if ([string]::IsNullOrWhiteSpace($queue.task_title)) {
    $handoffScore -= 5
    $issues += "task_title_missing"
}
if ([string]::IsNullOrWhiteSpace($queue.task_body)) {
    $handoffScore -= 5
    $issues += "task_body_missing"
}
if ("$($queue.task_body)" -match "Callback number:\s*\.\s") {
    $handoffScore -= 5
    $issues += "task_body_bad_callback_text"
}
if ($handoffScore -lt 0) { $handoffScore = 0 }

# 6. Normalization quality score: 10
$normalizationScore = 10
if (-not [string]::IsNullOrWhiteSpace($queue.normalized_input.dob) -and $queue.normalized_input.dob -notmatch '^\d{4}-\d{2}-\d{2}$') {
    $normalizationScore -= 5
    $issues += "dob_not_normalized"
}
if (-not [string]::IsNullOrWhiteSpace($queue.normalized_input.callback_number) -and $queue.normalized_input.callback_number -notmatch '^\d+$') {
    $normalizationScore -= 3
    $issues += "callback_not_normalized"
}
if ($queue.normalized_input.caller_for -eq "myself") {
    $normalizationScore -= 2
    $issues += "caller_for_not_normalized"
}
if ($normalizationScore -lt 0) { $normalizationScore = 0 }

$totalScore = $schemaScore + $requiredFieldScore + $consistencyScore + $summaryScore + $handoffScore + $normalizationScore

$recommendation = "stay_on_current_model"
if ($hardFailure -or $totalScore -lt $config.poor_run_threshold) {
    $recommendation = "poor_run_review_model"
}
elseif ($totalScore -lt $config.watch_run_threshold) {
    $recommendation = "watch_model_performance"
}

$runObject = [ordered]@{
    call_id = "$($queue.call_id)"
    timestamp = (Get-Date).ToString("s")
    model_name = "$($config.active_model)"
    scores = [ordered]@{
        schema_score = $schemaScore
        required_field_score = $requiredFieldScore
        consistency_score = $consistencyScore
        summary_score = $summaryScore
        handoff_score = $handoffScore
        normalization_score = $normalizationScore
        total_score = $totalScore
    }
    issues = @($issues | Select-Object -Unique)
    hard_failure = $hardFailure
    current_verification_status = "$($queue.verification_status)"
    current_priority = "$($queue.priority)"
    recommendation = $recommendation
    upgrade_candidate = "$($config.upgrade_candidate)"
}

$runPath = Join-Path (Join-Path $MonitoringBasePath "Runs") "$($queue.call_id)-monitor.json"
$runObject | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $runPath -Encoding UTF8

# Rolling summary
$runFiles = Get-ChildItem -LiteralPath (Join-Path $MonitoringBasePath "Runs") -Filter "*-monitor.json" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First $config.rolling_window

$runData = @()
foreach ($file in $runFiles) {
    try {
        $runData += Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
    } catch {}
}

$totalRuns = $runData.Count
$hardFailuresLast10 = @($runData | Select-Object -First 10 | Where-Object { $_.hard_failure -eq $true }).Count
$poorRunsLast10 = @($runData | Select-Object -First 10 | Where-Object { $_.scores.total_score -lt $config.poor_run_threshold }).Count
$schemaFailures = @($runData | Where-Object { $_.scores.schema_score -lt 25 }).Count
$requiredFieldMissRuns = @($runData | Where-Object { $_.scores.required_field_score -lt 20 }).Count
$summaryFailRuns = @($runData | Where-Object { $_.scores.summary_score -lt 12 }).Count
$averageScore = if ($totalRuns -gt 0) {
    $scoreValues = @($runData | ForEach-Object { [double]$_.scores.total_score })
    [Math]::Round((($scoreValues | Measure-Object -Average).Average), 2)
} else { 0 }

$rollingRecommendation = "stay_on_$($config.active_model)"
if (
    ($totalRuns -gt 0 -and ($schemaFailures / $totalRuns) -gt $config.thresholds.schema_failure_rate_max) -or
    ($totalRuns -gt 0 -and ($requiredFieldMissRuns / $totalRuns) -gt $config.thresholds.required_field_miss_rate_max) -or
    ($totalRuns -gt 0 -and ($summaryFailRuns / $totalRuns) -gt $config.thresholds.summary_quality_failure_rate_max) -or
    ($hardFailuresLast10 -gt $config.thresholds.hard_failures_last_10_max) -or
    ($poorRunsLast10 -gt $config.thresholds.poor_runs_last_10_max)
) {
    $rollingRecommendation = "consider_upgrade_to_$($config.upgrade_candidate)"
}

$summaryObject = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    active_model = "$($config.active_model)"
    upgrade_candidate = "$($config.upgrade_candidate)"
    rolling_window = $config.rolling_window
    total_runs_reviewed = $totalRuns
    average_score = $averageScore
    schema_failure_rate = if ($totalRuns -gt 0) { [Math]::Round(($schemaFailures / $totalRuns), 4) } else { 0 }
    required_field_miss_rate = if ($totalRuns -gt 0) { [Math]::Round(($requiredFieldMissRuns / $totalRuns), 4) } else { 0 }
    summary_quality_failure_rate = if ($totalRuns -gt 0) { [Math]::Round(($summaryFailRuns / $totalRuns), 4) } else { 0 }
    hard_failures_last_10 = $hardFailuresLast10
    poor_runs_last_10 = $poorRunsLast10
    recommendation = $rollingRecommendation
}

$summaryPath = Join-Path $MonitoringBasePath "monitoring_summary.json"
$summaryObject | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $summaryPath -Encoding UTF8

Write-Host ""
Write-Host "Monitoring run saved to:"
Write-Host $runPath
Write-Host ""
Write-Host "Monitoring summary saved to:"
Write-Host $summaryPath
Write-Host ""
Write-Host "Run score: $totalScore"
Write-Host "Recommendation: $recommendation"
Write-Host "Rolling recommendation: $rollingRecommendation"
Write-Host ""
param(
    [string]$AppSettingsPath = "C:\JeffLocal\config\app_settings.json",
    [string]$LocalSecretsPath = "C:\JeffLocal\config\local_secrets.json",
    [switch]$ValidateConfigOnly
)

$ErrorActionPreference = "Stop"

# Optional Apps Script encrypted intake bridge.
# This is not the core local intake path. The default cycle uses local
# encrypted_raw file drop unless config explicitly enables this bridge.
if (-not (Test-Path -LiteralPath $AppSettingsPath)) {
    throw "Missing app settings file: $AppSettingsPath"
}

$appSettings = Get-Content -LiteralPath $AppSettingsPath -Raw | ConvertFrom-Json
$bridgeEnabled = $false
if ($appSettings.PSObject.Properties["enable_apps_script_intake_polling"]) {
    $bridgeEnabled = ($appSettings.enable_apps_script_intake_polling -eq $true)
}

if (-not $bridgeEnabled) {
    Write-Host "Optional Apps Script encrypted intake bridge is disabled in app_settings.json."
    exit 0
}

if (-not (Test-Path -LiteralPath $LocalSecretsPath)) {
    throw "Optional Apps Script encrypted intake bridge is enabled, but local secret config is missing: $LocalSecretsPath"
}

$localSecrets = Get-Content -LiteralPath $LocalSecretsPath -Raw | ConvertFrom-Json
$QueueApiUrl = ""
$Token = ""

if ($localSecrets.PSObject.Properties["apps_script_encrypted_intake_bridge_url"]) {
    $QueueApiUrl = [string]$localSecrets.apps_script_encrypted_intake_bridge_url
}

if ($localSecrets.PSObject.Properties["apps_script_encrypted_intake_bridge_token"]) {
    $Token = [string]$localSecrets.apps_script_encrypted_intake_bridge_token
}

if ([string]::IsNullOrWhiteSpace($QueueApiUrl) -or [string]::IsNullOrWhiteSpace($Token)) {
    throw "Optional Apps Script encrypted intake bridge is enabled, but bridge URL or token is missing from local secret config."
}

if ($QueueApiUrl -notmatch "^https://script\.google\.com/macros/") {
    throw "Optional Apps Script encrypted intake bridge URL is not an expected Apps Script endpoint."
}

if ($ValidateConfigOnly) {
    Write-Host "Optional Apps Script encrypted intake bridge config is valid."
    exit 0
}

$EncryptedRawPath = "C:\JeffLocal\queue\encrypted_raw"
$AuditPath = "C:\JeffLocal\logs\audits"

New-Item -ItemType Directory -Force -Path $EncryptedRawPath | Out-Null
New-Item -ItemType Directory -Force -Path $AuditPath | Out-Null

function Write-Audit {
    param(
        [string]$Event,
        [string]$MessageId,
        [string]$Detail
    )

    $auditFile = Join-Path $AuditPath ("poll_encrypted_queue_{0}.jsonl" -f (Get-Date -Format "yyyy-MM-dd"))

    $record = [ordered]@{
        timestamp_utc = (Get-Date).ToUniversalTime().ToString("o")
        event = $Event
        message_id = $MessageId
        detail = $Detail
    }

    ($record | ConvertTo-Json -Compress) | Add-Content -Path $auditFile -Encoding UTF8
}

function Mark-Pulled {
    param(
        [string]$MessageId,
        [string]$RowNumber,
        [string]$Result
    )

    $body = @{
        token = $Token
        action = "mark_pulled"
        message_id = $MessageId
        row_number = $RowNumber
        pull_result = $Result
    } | ConvertTo-Json -Depth 10

    $markResponse = Invoke-RestMethod `
        -Uri $QueueApiUrl `
        -Method POST `
        -ContentType "application/json" `
        -Body $body

    Write-Host "Mark pulled response:"
    $markResponse | ConvertTo-Json -Depth 10
}

function Mark-Failed {
    param(
        [string]$MessageId,
        [string]$RowNumber,
        [string]$Result
    )

    $body = @{
        token = $Token
        action = "mark_failed"
        message_id = $MessageId
        row_number = $RowNumber
        pull_result = $Result
    } | ConvertTo-Json -Depth 10

    $markResponse = Invoke-RestMethod `
        -Uri $QueueApiUrl `
        -Method POST `
        -ContentType "application/json" `
        -Body $body

    Write-Host "Mark failed response:"
    $markResponse | ConvertTo-Json -Depth 10
}

Write-Host "Polling optional Apps Script encrypted intake bridge..."

$pendingUri = "$($QueueApiUrl)?token=$($Token)&action=get_pending_envelopes"

Write-Host "Calling optional bridge endpoint with token redacted."

$response = Invoke-RestMethod `
    -Uri $pendingUri `
    -Method GET

if ($response.status -ne "ok") {
    throw "Queue API returned non-ok status: $($response.status)"
}

if ([int]$response.count -eq 0) {
    Write-Host "No pending encrypted envelopes."
    exit 0
}

foreach ($env in $response.envelopes) {
    $messageId = $env.message_id
    $rowNumber = $env.row_number

    try {
        if ([string]::IsNullOrWhiteSpace($messageId)) {
            throw "Missing message_id"
        }

        if ($env.protocol -ne "JEIE-1") {
            throw "Invalid protocol: $($env.protocol)"
        }

        if ([string]::IsNullOrWhiteSpace($env.envelope_json)) {
            throw "Missing envelope_json"
        }

        $safeMessageId = $messageId -replace '[^a-zA-Z0-9_\-]', '_'
        $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
        $outFile = Join-Path $EncryptedRawPath "$stamp`_$safeMessageId.json"

        [System.IO.File]::WriteAllText($outFile, $env.envelope_json, [System.Text.UTF8Encoding]::new($false))

        Mark-Pulled -MessageId $messageId -RowNumber $rowNumber -Result "saved_to_$outFile"

        Write-Audit `
            -Event "encrypted_envelope_pulled" `
            -MessageId $messageId `
            -Detail "Saved to $outFile"

        Write-Host "Pulled envelope: $messageId"
        Write-Host "Saved to: $outFile"
    }
    catch {
        Mark-Failed -MessageId $messageId -RowNumber $rowNumber -Result $_.Exception.Message
        Write-Audit `
            -Event "encrypted_envelope_pull_failed" `
            -MessageId $messageId `
            -Detail $_.Exception.Message

        Write-Warning "Failed envelope $messageId : $($_.Exception.Message)"
    }
}

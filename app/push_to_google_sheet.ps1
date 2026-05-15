param(
    [Parameter(Mandatory = $true)]
    [string]$JsonPath,

    [string]$WebhookUrl = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$appSettingsPath = "C:\JeffLocal\config\app_settings.json"
if (-not (Test-Path -LiteralPath $appSettingsPath)) {
    throw "Missing app settings file: $appSettingsPath"
}

$appSettings = Get-Content -LiteralPath $appSettingsPath -Raw | ConvertFrom-Json

if ([string]::IsNullOrWhiteSpace($WebhookUrl)) {
    $WebhookUrl = "$($appSettings.google_sheet_webhook_url)"
}

if ([string]::IsNullOrWhiteSpace($WebhookUrl)) {
    throw "Google Sheet webhook URL is missing in app_settings.json and was not passed in."
}

if (-not (Test-Path -LiteralPath $JsonPath)) {
    throw "JSON file not found: $JsonPath"
}

$jsonText = Get-Content -LiteralPath $JsonPath -Raw -Encoding UTF8
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($jsonText)

$response = Invoke-RestMethod `
    -Uri $WebhookUrl `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body $bodyBytes `
    -TimeoutSec ([int]$appSettings.google_sheet_timeout_seconds)

$response
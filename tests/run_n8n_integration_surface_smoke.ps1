Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-True {
    param([string]$Name, [bool]$Condition)
    if (-not $Condition) { throw "$Name expected true" }
}

function Assert-False {
    param([string]$Name, [bool]$Condition)
    if ($Condition) { throw "$Name expected false" }
}

function Test-ScriptParses {
    param([string]$Path)
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors.Count -gt 0) {
        throw "Parse errors in $Path"
    }
}

function Invoke-JsonScript {
    param(
        [string]$Path,
        [string[]]$Arguments = @()
    )

    $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Path @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Path failed with exit code $LASTEXITCODE"
    }
    $jsonText = ($output | Out-String).Trim()
    if (-not $jsonText) {
        throw "$Path returned empty output"
    }
    return $jsonText | ConvertFrom-Json
}

$basePath = "C:\JeffLocal"
$docsPath = Join-Path $basePath "integrations\n8n"
$scriptsPath = Join-Path $basePath "scripts"
$settingsPath = Join-Path $basePath "config\app_settings.json"

$requiredDocs = @(
    "README.md",
    "workflow_01_health_check.md",
    "workflow_02_dashboard_sync.md",
    "workflow_03_red_flag_alert.md",
    "workflow_04_overdue_monitor.md",
    "workflow_05_daily_summary.md",
    "workflow_06_intake_webhook.md",
    "workflow_07_staff_review_form.md"
)

foreach ($doc in $requiredDocs) {
    Assert-True -Name "doc exists $doc" -Condition (Test-Path -LiteralPath (Join-Path $docsPath $doc))
}

$wrapperScripts = @(
    "n8n_health_check.ps1",
    "n8n_dashboard_sync.ps1",
    "n8n_red_flag_scan.ps1",
    "n8n_overdue_scan.ps1",
    "n8n_daily_summary.ps1"
)

foreach ($script in $wrapperScripts) {
    $path = Join-Path $scriptsPath $script
    Assert-True -Name "wrapper exists $script" -Condition (Test-Path -LiteralPath $path)
    Test-ScriptParses -Path $path
    $text = Get-Content -LiteralPath $path -Raw
    Assert-False -Name "$script has no web posting cmdlets" -Condition ($text -match "Invoke-RestMethod|Invoke-WebRequest|curl |wget ")
    Assert-False -Name "$script has no cloud/posting targets" -Condition ($text -match "script\.google|n8n\.cloud|push_to_google_sheet|http://|https://")
}

$health = Invoke-JsonScript -Path (Join-Path $scriptsPath "n8n_health_check.ps1")
Assert-True -Name "health returns ok" -Condition ($health.ok -eq $true)
Assert-True -Name "health no external posting" -Condition ($health.external_posting -eq $false)

$syncText = Get-Content -LiteralPath (Join-Path $scriptsPath "n8n_dashboard_sync.ps1") -Raw
Assert-True -Name "dashboard sync has no external mode" -Condition ($syncText -match "NoExternalPost")
$sync = Invoke-JsonScript -Path (Join-Path $scriptsPath "n8n_dashboard_sync.ps1") -Arguments @("-RawmockOnly", "-NoExternalPost")
Assert-True -Name "dashboard sync returns json" -Condition ($sync.ok -eq $true)
Assert-True -Name "dashboard sync uses rawmock pattern" -Condition ($sync.pattern -eq "RAWMOCK*_handoff.json")

$redFlags = Invoke-JsonScript -Path (Join-Path $scriptsPath "n8n_red_flag_scan.ps1")
Assert-True -Name "red flag scan returns json" -Condition ($redFlags.ok -eq $true -and $null -ne $redFlags.count)

$overdue = Invoke-JsonScript -Path (Join-Path $scriptsPath "n8n_overdue_scan.ps1") -Arguments @("-ThresholdHours", "24")
Assert-True -Name "overdue scan returns json" -Condition ($overdue.ok -eq $true -and $overdue.threshold_hours -eq 24)

$summary = Invoke-JsonScript -Path (Join-Path $scriptsPath "n8n_daily_summary.ps1")
Assert-True -Name "daily summary returns json" -Condition ($summary.ok -eq $true -and $null -ne $summary.summary)

$settings = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
Assert-True -Name "google sheet production config remains enabled" -Condition ($settings.google_sheet_enabled -eq $true)

Write-Output "n8n integration surface smoke test passed."

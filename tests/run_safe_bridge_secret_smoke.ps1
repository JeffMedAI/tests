Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-True {
    param(
        [string]$Name,
        [bool]$Condition
    )

    if (-not $Condition) {
        throw "$Name expected true"
    }
}

function Assert-False {
    param(
        [string]$Name,
        [bool]$Condition
    )

    if ($Condition) {
        throw "$Name expected false"
    }
}

$settings = Get-Content -LiteralPath "C:\JeffLocal\config\app_settings.json" -Raw | ConvertFrom-Json
Assert-True -Name "default intake mode local file drop" -Condition ([string]$settings.intake_mode -eq "local_file_drop")
Assert-False -Name "bridge disabled by default" -Condition ($settings.enable_apps_script_intake_polling -eq $true)

$pollerText = Get-Content -LiteralPath "C:\JeffLocal\app\poll_encrypted_intake_queue.ps1" -Raw
Assert-True -Name "poller reads local secrets" -Condition ($pollerText -match "local_secrets\.json")
Assert-True -Name "poller redacts token logging" -Condition ($pollerText -match "token redacted")
Assert-False -Name "poller has no hardcoded old bridge token" -Condition ($pollerText -match "jefflocal_queue_poll_2026_very_secret")
Assert-False -Name "poller has no hardcoded concrete Apps Script deployment" -Condition ($pollerText -match "AKfycbzLjy-eeMgTmXSrqs_1P717v3rQjsmTOV2NLczndJnka4V0XaWtJydaG9nzdXleJQwyQA")

$gitignoreText = Get-Content -LiteralPath "C:\JeffLocal\.gitignore" -Raw
Assert-True -Name "local secrets ignored" -Condition ($gitignoreText -match "config/local_secrets\.json")

$tempRoot = Join-Path $env:TEMP ("jefflocal_bridge_secret_smoke_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

try {
    $disabledSettingsPath = Join-Path $tempRoot "disabled_app_settings.json"
    '{"enable_apps_script_intake_polling": false}' | Set-Content -LiteralPath $disabledSettingsPath -Encoding UTF8
    $missingSecretsPath = Join-Path $tempRoot "missing_local_secrets.json"

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    $disabledOutput = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\JeffLocal\app\poll_encrypted_intake_queue.ps1" -AppSettingsPath $disabledSettingsPath -LocalSecretsPath $missingSecretsPath -ValidateConfigOnly 2>&1
    if ($LASTEXITCODE -ne 0) {
        $ErrorActionPreference = $previousErrorActionPreference
        throw "Bridge-disabled validation should not require local secrets. Output: $disabledOutput"
    }
    Assert-True -Name "disabled validation message" -Condition (($disabledOutput -join "`n") -match "disabled")

    $enabledSettingsPath = Join-Path $tempRoot "enabled_app_settings.json"
    '{"enable_apps_script_intake_polling": true}' | Set-Content -LiteralPath $enabledSettingsPath -Encoding UTF8

    $enabledOutput = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\JeffLocal\app\poll_encrypted_intake_queue.ps1" -AppSettingsPath $enabledSettingsPath -LocalSecretsPath $missingSecretsPath -ValidateConfigOnly 2>&1
    $enabledExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference
    if ($enabledExitCode -eq 0) {
        throw "Bridge-enabled validation should fail when local secrets are missing."
    }
    Assert-True -Name "missing secrets clear failure" -Condition (($enabledOutput -join "`n") -match "local secret config is missing")
}
finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Output "Safe bridge secret smoke tests passed."

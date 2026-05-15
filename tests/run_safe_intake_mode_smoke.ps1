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
Assert-False -Name "apps script polling disabled by default" -Condition ($settings.enable_apps_script_intake_polling -eq $true)

$cycleText = Get-Content -LiteralPath "C:\JeffLocal\app\run_encrypted_intake_cycle.ps1" -Raw
Assert-True -Name "cycle reads app settings" -Condition ($cycleText -match "app_settings\.json")
Assert-True -Name "cycle checks apps script flag" -Condition ($cycleText -match "enable_apps_script_intake_polling")
Assert-True -Name "cycle labels optional bridge" -Condition ($cycleText -match "Optional Apps Script encrypted intake bridge")
Assert-True -Name "cycle still decrypts local encrypted_raw" -Condition ($cycleText -match "decrypt_encrypted_raw\.py")

$pollText = Get-Content -LiteralPath "C:\JeffLocal\app\poll_encrypted_intake_queue.ps1" -Raw
Assert-True -Name "poller labelled optional bridge" -Condition ($pollText -match "Optional Apps Script encrypted intake bridge")

$receiverText = Get-Content -LiteralPath "C:\JeffLocal\app\receive_encrypted_intake.py" -Raw
Assert-True -Name "local receiver writes encrypted_raw" -Condition ($receiverText -match "queue\\encrypted_raw")
Assert-True -Name "local receiver naming is local" -Condition ($receiverText -match "received_from_local_intake")

$send5Text = Get-Content -LiteralPath "C:\JeffLocal\app\send_5_live_lookup_direct_to_queue.py" -Raw
$send20Text = Get-Content -LiteralPath "C:\JeffLocal\app\send_20_live_lookup_direct_to_queue.py" -Raw
Assert-True -Name "5-call helper writes local encrypted raw" -Condition ($send5Text -match "LOCAL_ENCRYPTED_RAW_DIR")
Assert-True -Name "20-call helper writes local encrypted raw" -Condition ($send20Text -match "LOCAL_ENCRYPTED_RAW_DIR")
Assert-False -Name "5-call helper has no external post" -Condition ($send5Text -match "requests\.post|script\.google|webhook|n8n")
Assert-False -Name "20-call helper has no external post" -Condition ($send20Text -match "requests\.post|script\.google|webhook|n8n")

Write-Output "Safe intake mode smoke tests passed."

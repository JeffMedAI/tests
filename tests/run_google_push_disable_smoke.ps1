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

function Test-ScriptHasParameter {
    param(
        [string]$Path,
        [string]$ParameterName
    )

    $tokens = $null
    $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors)
    if ($errors.Count -gt 0) {
        throw "Parse errors in $Path"
    }

    $paramBlocks = $ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.ParamBlockAst] }, $true)
    foreach ($paramBlock in $paramBlocks) {
        foreach ($parameter in $paramBlock.Parameters) {
            if ($parameter.Name.VariablePath.UserPath -eq $ParameterName) {
                return $true
            }
        }
    }

    return $false
}

$basePath = "C:\JeffLocal"
$processPath = Join-Path $basePath "app\process_queue.ps1"
$cyclePath = Join-Path $basePath "app\run_encrypted_intake_cycle.ps1"
$mockE2EPath = Join-Path $basePath "tests\run_raw_intake_mock_end_to_end_local.ps1"
$settingsPath = Join-Path $basePath "config\app_settings.json"

Assert-True -Name "process_queue accepts DisableGooglePush" -Condition (Test-ScriptHasParameter -Path $processPath -ParameterName "DisableGooglePush")
Assert-True -Name "run_encrypted_intake_cycle accepts DisableGooglePush" -Condition (Test-ScriptHasParameter -Path $cyclePath -ParameterName "DisableGooglePush")
Assert-True -Name "raw mock e2e accepts DisableGooglePush" -Condition (Test-ScriptHasParameter -Path $mockE2EPath -ParameterName "DisableGooglePush")

$processText = Get-Content -LiteralPath $processPath -Raw
$cycleText = Get-Content -LiteralPath $cyclePath -Raw
$mockE2EText = Get-Content -LiteralPath $mockE2EPath -Raw
$settings = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json

Assert-True -Name "process_queue checks env var" -Condition ($processText -match "JEFFLOCAL_DISABLE_GOOGLE_PUSH")
Assert-True -Name "process_queue has disabled_for_test audit reason" -Condition ($processText -match "disabled_for_test")
Assert-True -Name "process_queue writes google_push skipped audit" -Condition ($processText -match 'EventType "google_push"[\s\S]*Status "skipped"')
Assert-True -Name "production push invocation remains" -Condition ($processText -match "push_to_google_sheet\.ps1" -and $processText -match "-JsonPath")
Assert-True -Name "skip branch precedes push invocation" -Condition ($processText.IndexOf('if ($disableGooglePushForTest)') -lt $processText.IndexOf('$pushResponse = & powershell.exe'))

Assert-True -Name "cycle passes DisableGooglePush" -Condition ($cycleText -match "process_queue\.ps1" -and $cycleText -match "DisableGooglePush")
Assert-True -Name "mock e2e passes DisableGooglePush" -Condition ($mockE2EText -match "run_encrypted_intake_cycle\.ps1" -and $mockE2EText -match "DisableGooglePush")

Assert-True -Name "google sheet remains enabled in config" -Condition ($settings.google_sheet_enabled -eq $true)
Assert-False -Name "config has no global disable flag set false" -Condition ($settings.PSObject.Properties["enable_google_sheet_push"] -and $settings.enable_google_sheet_push -eq $false)

Write-Output "Google push disable smoke test passed."

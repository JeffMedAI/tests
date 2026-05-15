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

function Test-ScriptHasParameter {
    param([string]$Path, [string]$ParameterName)
    $tokens = $null
    $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors)
    if ($errors.Count -gt 0) {
        throw "Parse errors in $Path"
    }
    foreach ($paramBlock in $ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.ParamBlockAst] }, $true)) {
        foreach ($parameter in $paramBlock.Parameters) {
            if ($parameter.Name.VariablePath.UserPath -eq $ParameterName) {
                return $true
            }
        }
    }
    return $false
}

$basePath = "C:\JeffLocal"
$freshBatch = Join-Path $basePath "tests\run_fresh_rawmock_end_to_end_batch.ps1"
$resetDashboard = Join-Path $basePath "tests\reset_dashboard_test_history.ps1"
$importDashboard = Join-Path $basePath "tests\import_dashboard_handoffs.ps1"
$mockE2E = Join-Path $basePath "tests\run_raw_intake_mock_end_to_end_local.ps1"
$importer = Join-Path $basePath "dashboard\app\importer.py"

Assert-True -Name "fresh batch accepts Force" -Condition (Test-ScriptHasParameter -Path $freshBatch -ParameterName "Force")
Assert-True -Name "reset script accepts Force" -Condition (Test-ScriptHasParameter -Path $resetDashboard -ParameterName "Force")
Assert-True -Name "import helper accepts Pattern" -Condition (Test-ScriptHasParameter -Path $importDashboard -ParameterName "Pattern")

$freshText = Get-Content -LiteralPath $freshBatch -Raw
$resetText = Get-Content -LiteralPath $resetDashboard -Raw
$importText = Get-Content -LiteralPath $importDashboard -Raw
$mockText = Get-Content -LiteralPath $mockE2E -Raw
$importerText = Get-Content -LiteralPath $importer -Raw

Assert-True -Name "fresh batch resets dashboard db" -Condition ($freshText -match 'reset_dashboard_test_history\.ps1')
Assert-True -Name "fresh batch archives rawmock artifacts" -Condition ($freshText -match 'RefreshRawmockArtifacts')
Assert-True -Name "fresh batch disables google push" -Condition ($freshText -match 'DisableGooglePush')
Assert-True -Name "fresh batch imports rawmock only" -Condition ($freshText -match 'RAWMOCK\*_handoff\.json')
Assert-True -Name "fresh batch runs dashboard tests" -Condition ($freshText -match 'dashboard\\.venv\\Scripts\\python\.exe' -and $freshText -match '-m", "pytest"')
Assert-False -Name "fresh batch does not remove non-temp data" -Condition ($freshText -match 'Remove-Item.*dashboard\\.sqlite|Remove-Item.*queue\\|Remove-Item.*outputs\\|Remove-Item.*logs\\')
Assert-True -Name "reset script archives db" -Condition ($resetText -match 'backup\\dashboard_reset_' -and $resetText -match '\.backup\(')
Assert-False -Name "reset script does not delete db permanently" -Condition ($resetText -match 'Remove-Item.*dashboard\\.sqlite' -or $resetText -match 'Move-Item.*dashboard\\.sqlite')
Assert-True -Name "import helper supports pattern filtering" -Condition ($importText -match 'Pattern = "\*_handoff\.json"' -and $importText -match 'import_handoffs\(conn, pattern=r"\$Pattern"\)')
Assert-True -Name "mock e2e still supports refresh and disable" -Condition ($mockText -match 'RefreshRawmockArtifacts' -and $mockText -match 'DisableGooglePush')
Assert-True -Name "dashboard importer default remains all handoffs" -Condition ($importerText -match 'pattern: str = "\*_handoff\.json"')

Write-Output "Fresh RAWMOCK batch safety smoke test passed."

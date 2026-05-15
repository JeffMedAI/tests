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
$mockE2EPath = Join-Path $basePath "tests\run_raw_intake_mock_end_to_end_local.ps1"
$processPath = Join-Path $basePath "app\process_queue.ps1"

$mockE2EText = Get-Content -LiteralPath $mockE2EPath -Raw
$processText = Get-Content -LiteralPath $processPath -Raw

Assert-True -Name "raw mock e2e accepts RefreshRawmockArtifacts" -Condition (Test-ScriptHasParameter -Path $mockE2EPath -ParameterName "RefreshRawmockArtifacts")
Assert-True -Name "refresh mode is opt-in" -Condition ($mockE2EText -match 'if \(\$RefreshRawmockArtifacts\)')
Assert-True -Name "archive path is under backup rawmock_regeneration timestamp" -Condition ($mockE2EText -match 'backup\\rawmock_regeneration_\$timestamp')
Assert-True -Name "archive scan filters only RAWMOCK names" -Condition ($mockE2EText -match 'Filter "\*RAWMOCK\*"')
Assert-True -Name "archive validates RAWMOCK filenames before move" -Condition ($mockE2EText -match 'Name -notlike "\*RAWMOCK\*"')
Assert-True -Name "archive moves files instead of deleting" -Condition ($mockE2EText -match 'Move-Item')
Assert-False -Name "refresh script does not permanently delete files" -Condition ($mockE2EText -match 'Remove-Item')
Assert-False -Name "refresh script does not archive audit logs by default" -Condition ($mockE2EText -match 'logs\\audits' -or $mockE2EText -match 'audit_\*' -or $mockE2EText -match '\*.jsonl')

$expectedFolders = @(
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

foreach ($folder in $expectedFolders) {
    Assert-True -Name "refresh includes $folder" -Condition ($mockE2EText.Contains($folder))
}

Assert-True -Name "process_queue duplicate file protection remains" -Condition ($processText -match 'Test-FileAlreadyProcessed' -and $processText -match 'file_name_already_processed')
Assert-True -Name "process_queue duplicate call id protection remains" -Condition ($processText -match 'Call_id already processed previously' -and $processText -match 'Duplicate call_id values found in batch')
Assert-False -Name "process_queue has no RAWMOCK duplicate bypass" -Condition ($processText -match 'RefreshRawmockArtifacts' -or $processText -match 'RAWMOCK.*duplicate')
Assert-True -Name "google push disable behavior still exists" -Condition ($mockE2EText -match 'DisableGooglePush' -and $processText -match 'JEFFLOCAL_DISABLE_GOOGLE_PUSH' -and $processText -match 'disabled_for_test')

Write-Output "RAWMOCK refresh safety smoke test passed."

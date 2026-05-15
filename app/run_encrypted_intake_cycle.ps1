param(
    [switch]$DisableGooglePush
)

$ErrorActionPreference = "Continue"

$LogPath = "C:\JeffLocal\logs\app"
New-Item -ItemType Directory -Force -Path $LogPath | Out-Null

$appSettingsPath = "C:\JeffLocal\config\app_settings.json"
$appSettings = $null
if (Test-Path -LiteralPath $appSettingsPath) {
    try {
        $appSettings = Get-Content -LiteralPath $appSettingsPath -Raw | ConvertFrom-Json
    }
    catch {
        $appSettings = $null
    }
}

$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$logFile = Join-Path $LogPath ("encrypted_intake_cycle_{0}.log" -f (Get-Date -Format "yyyy-MM-dd"))

function Write-CycleLog {
    param([string]$Message)
    "[$(Get-Date -Format o)] $Message" | Add-Content -Path $logFile -Encoding UTF8
}

Write-CycleLog "Starting encrypted intake cycle"

$disableGooglePushForTest = ($DisableGooglePush -or $env:JEFFLOCAL_DISABLE_GOOGLE_PUSH -eq "1")
if ($disableGooglePushForTest) {
    Write-CycleLog "TEST MODE: Google Sheet push disabled for this local run."
}

$intakeMode = "local_file_drop"
if ($null -ne $appSettings -and $appSettings.PSObject.Properties["intake_mode"]) {
    $intakeMode = [string]$appSettings.intake_mode
}

$enableAppsScriptPolling = $false
if ($null -ne $appSettings -and $appSettings.PSObject.Properties["enable_apps_script_intake_polling"]) {
    $enableAppsScriptPolling = ($appSettings.enable_apps_script_intake_polling -eq $true)
}

Write-CycleLog "INTAKE: mode=$intakeMode"

if ($enableAppsScriptPolling) {
    try {
        Write-CycleLog "INTAKE: Optional Apps Script encrypted intake bridge enabled; polling remote encrypted queue"
        powershell -ExecutionPolicy Bypass -File "C:\JeffLocal\app\poll_encrypted_intake_queue.ps1" *>> $logFile
    }
    catch {
        Write-CycleLog "INTAKE: Optional Apps Script encrypted intake bridge poll failed: $($_.Exception.Message)"
    }
}
else {
    Write-CycleLog "INTAKE: Optional Apps Script encrypted intake bridge disabled; using local encrypted_raw file drop only"
}

try {
    Write-CycleLog "Decrypting encrypted_raw"
    python "C:\JeffLocal\app\decrypt_encrypted_raw.py" *>> $logFile
}
catch {
    Write-CycleLog "Decrypt failed: $($_.Exception.Message)"
}

try {
    Write-CycleLog "Processing JeffLocal queue until incoming is empty"

    $incomingPath = "C:\JeffLocal\queue\incoming"
    $maxPasses = 50
    $pass = 0

    while ($true) {
        $pendingFiles = @(Get-ChildItem -Path $incomingPath -Filter "*.json" -File -ErrorAction SilentlyContinue)

        if ($pendingFiles.Count -eq 0) {
            Write-CycleLog "PROCESS: Incoming queue is empty."
            break
        }

        $pass++

        if ($pass -gt $maxPasses) {
            Write-CycleLog "PROCESS: Stopping after $maxPasses passes to avoid infinite loop. Files remaining: $($pendingFiles.Count)"
            break
        }

        Write-CycleLog "PROCESS: Pass $pass. Incoming files remaining before run: $($pendingFiles.Count)"

        $processArgs = @("-ExecutionPolicy", "Bypass", "-File", "C:\JeffLocal\app\process_queue.ps1")
        if ($disableGooglePushForTest) {
            $processArgs += "-DisableGooglePush"
        }

        $processOutput = powershell @processArgs 2>&1
        $processOutput | ForEach-Object { Write-CycleLog "PROCESS: $_" }

        Start-Sleep -Seconds 2
    }
}
catch {
    Write-CycleLog "Process queue failed: $($_.Exception.Message)"
}

Write-CycleLog "Encrypted intake cycle complete"

# Hidden launcher - called by watchdog only. Runs uvicorn and appends stdout+stderr to log.
$python  = "C:\JeffLocal\dashboard\.venv\Scripts\python.exe"
$workDir = "C:\JeffLocal\dashboard"
$logFile = "C:\JeffLocal\logs\service_control\dashboard.log"

New-Item -ItemType Directory -Path (Split-Path $logFile) -Force | Out-Null

if ((Test-Path $logFile) -and (Get-Item $logFile).Length -gt 3MB) {
    Move-Item $logFile "$logFile.old" -Force
}

if (-not (Test-Path $python)) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [ERROR] venv not found at $python - run: python -m venv C:\JeffLocal\dashboard\.venv" |
        Out-File $logFile -Append
    exit 1
}

# Load config\secrets.env into the environment so uvicorn inherits it. Never
# fatal: a missing/empty secrets file leaves the dependent endpoints failing
# closed on their own, which is safer than refusing to start the dashboard.
$secretsLoader = Join-Path $PSScriptRoot "_load_secrets.ps1"
if (Test-Path $secretsLoader) {
    . $secretsLoader
    Import-JeffSecrets -LogFile $logFile
} else {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [SECRETS] loader not found at $secretsLoader - starting without secrets" |
        Out-File $logFile -Append
}

Push-Location $workDir
try {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [START] uvicorn starting" | Out-File $logFile -Append
    & $python -m uvicorn app.main:app --host 0.0.0.0 --port 8765 2>&1 |
        ForEach-Object { "$(Get-Date -Format 'HH:mm:ss') $_" } |
        Out-File $logFile -Append
} finally {
    Pop-Location
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [STOP] uvicorn exited" | Out-File $logFile -Append
}

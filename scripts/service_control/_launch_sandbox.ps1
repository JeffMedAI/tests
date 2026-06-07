# Hidden launcher for sandbox dashboard — called by watchdog only.
$python  = "C:\JeffLocal\sandbox\dashboard\.venv\Scripts\python.exe"
$workDir = "C:\JeffLocal\sandbox\dashboard"
$logFile = "C:\JeffLocal\logs\service_control\sandbox.log"

New-Item -ItemType Directory -Path (Split-Path $logFile) -Force | Out-Null

if ((Test-Path $logFile) -and (Get-Item $logFile).Length -gt 3MB) {
    Move-Item $logFile "$logFile.old" -Force
}

if (-not (Test-Path $python)) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [ERROR] venv not found at $python - run: python -m venv C:\JeffLocal\sandbox\dashboard\.venv" |
        Out-File $logFile -Append
    exit 1
}

Push-Location $workDir
try {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [START] uvicorn starting" | Out-File $logFile -Append
    & $python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 2>&1 |
        ForEach-Object { "$(Get-Date -Format 'HH:mm:ss') $_" } |
        Out-File $logFile -Append
} finally {
    Pop-Location
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [STOP] uvicorn exited" | Out-File $logFile -Append
}

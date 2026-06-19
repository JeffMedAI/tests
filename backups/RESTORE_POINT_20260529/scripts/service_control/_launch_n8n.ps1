# Hidden launcher - called by watchdog only. Runs n8n and appends output to log.
# Uses native PS pipeline (& cmd 2>&1 | Out-File) - same pattern as _launch_dashboard.ps1.
# Start-Process + shell >> redirect was used previously but fails in hidden PS processes
# because they have no console, causing cmd.exe to exit immediately with a null-handle error.
$n8nCmd  = "$env:APPDATA\npm\n8n.cmd"
$logFile = "C:\JeffLocal\logs\service_control\n8n.log"

New-Item -ItemType Directory -Path (Split-Path $logFile) -Force | Out-Null

if ((Test-Path $logFile) -and (Get-Item $logFile).Length -gt 3MB) {
    Move-Item $logFile "$logFile.old" -Force
}

if (-not (Test-Path $n8nCmd)) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [ERROR] n8n.cmd not found at $n8nCmd" |
        Out-File $logFile -Append -Encoding utf8
    exit 1
}

"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [START] n8n starting" | Out-File $logFile -Append -Encoding utf8

# Fix PS 5.1 UTF-8 pipeline encoding so n8n's Node output is readable
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

& $n8nCmd start 2>&1 |
    ForEach-Object { "$(Get-Date -Format 'HH:mm:ss') $_" } |
    Out-File $logFile -Append -Encoding utf8

"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [STOP] n8n exited" | Out-File $logFile -Append -Encoding utf8

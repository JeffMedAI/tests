# Complete Jarvis / OpenJarvis Uninstaller
# Removes all installations, configs, caches, and PATH entries
# Right-click -> Run with PowerShell (as Administrator recommended)

Write-Host "========================================" -ForegroundColor Red
Write-Host "  Full Jarvis Removal Script" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "This will remove:" -ForegroundColor Yellow
Write-Host "  - isair/Jarvis (C:\Users\$env:USERNAME\Jarvis)" -ForegroundColor White
Write-Host "  - OpenJarvis (C:\Users\$env:USERNAME\OpenJarvis)" -ForegroundColor White
Write-Host "  - All config/data folders" -ForegroundColor White
Write-Host "  - Downloaded zip files" -ForegroundColor White
Write-Host "  - uv (Python package manager installed by OpenJarvis)" -ForegroundColor White
Write-Host "  - PATH entries related to Jarvis/uv" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Are you sure? This cannot be undone. (YES/no)"
if ($confirm -ne 'YES') { Write-Host "Cancelled." -ForegroundColor Green; exit }

Write-Host ""
Write-Host "Step 1: Killing running Jarvis processes..." -ForegroundColor Cyan
$processes = @("Jarvis", "jarvis", "uv", "uvx", "cargo", "rustc", "ollama")
foreach ($p in $processes) {
    Stop-Process -Name $p -Force -ErrorAction SilentlyContinue
    Write-Host "  Stopped: $p" -ForegroundColor Gray
}
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Step 2: Removing installation folders..." -ForegroundColor Cyan
$folders = @(
    "$env:USERPROFILE\Jarvis",
    "$env:USERPROFILE\OpenJarvis",
    "$env:USERPROFILE\openjarvis",
    "C:\OpenJarvis",
    "$env:USERPROFILE\.openjarvis",
    "$env:USERPROFILE\.local\share\jarvis",
    "$env:APPDATA\jarvis",
    "$env:LOCALAPPDATA\jarvis",
    "$env:USERPROFILE\.config\jarvis"
)
foreach ($folder in $folders) {
    if (Test-Path $folder) {
        Remove-Item -Recurse -Force $folder -ErrorAction SilentlyContinue
        Write-Host "  Removed: $folder" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Step 3: Removing uv (OpenJarvis package manager)..." -ForegroundColor Cyan
$uvFolders = @(
    "$env:USERPROFILE\.local\bin\uv.exe",
    "$env:USERPROFILE\.local\bin\uvx.exe",
    "$env:USERPROFILE\.local\bin\uvw.exe",
    "$env:APPDATA\uv",
    "$env:LOCALAPPDATA\uv",
    "$env:USERPROFILE\.uv"
)
foreach ($item in $uvFolders) {
    if (Test-Path $item) {
        Remove-Item -Recurse -Force $item -ErrorAction SilentlyContinue
        Write-Host "  Removed: $item" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Step 4: Removing downloaded zip files..." -ForegroundColor Cyan
$zips = @(
    "$env:USERPROFILE\Downloads\Jarvis-Windows-x64.zip",
    "$env:USERPROFILE\Downloads\OpenJarvis*.zip"
)
foreach ($zip in $zips) {
    Remove-Item -Force $zip -ErrorAction SilentlyContinue
    Write-Host "  Removed: $zip" -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 5: Cleaning PATH entries..." -ForegroundColor Cyan
$pathsToRemove = @(
    "$env:USERPROFILE\.local\bin",
    "$env:USERPROFILE\.uv\bin",
    "$env:APPDATA\uv\bin"
)
$userPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
foreach ($p in $pathsToRemove) {
    if ($userPath -like "*$p*") {
        $userPath = ($userPath -split ";" | Where-Object { $_ -ne $p }) -join ";"
        Write-Host "  Removed from PATH: $p" -ForegroundColor Green
    }
}
[System.Environment]::SetEnvironmentVariable("PATH", $userPath, "User")

Write-Host ""
Write-Host "Step 6: Removing scheduled tasks..." -ForegroundColor Cyan
Get-ScheduledTask | Where-Object { $_.TaskName -like "*jarvis*" -or $_.TaskName -like "*openjarvis*" } | ForEach-Object {
    Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "  Removed task: $($_.TaskName)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 7: Removing temp/cache files..." -ForegroundColor Cyan
$tempItems = @(
    "$env:TEMP\jarvis*",
    "$env:TEMP\openjarvis*"
)
foreach ($item in $tempItems) {
    Remove-Item -Recurse -Force $item -ErrorAction SilentlyContinue
}
Write-Host "  Temp files cleared." -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  All Jarvis files removed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Note: Ollama and its models were NOT removed." -ForegroundColor Yellow
Write-Host "To remove Ollama too, uninstall it from Settings > Apps." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"

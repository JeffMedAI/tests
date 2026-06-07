# OpenJarvis PATH Fixer / Diagnostic
# Run with: Right-click -> Run with PowerShell

Write-Host "=== OpenJarvis Diagnostic ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check if jarvis is in PATH after refreshing env
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

Write-Host "Checking for 'jarvis' command..." -ForegroundColor Yellow
$jarvisPath = Get-Command jarvis -ErrorAction SilentlyContinue
if ($jarvisPath) {
    Write-Host "Found jarvis at: $($jarvisPath.Source)" -ForegroundColor Green
    Write-Host "Running: jarvis" -ForegroundColor Green
    jarvis
    exit
}

# 2. Search common install locations
Write-Host "jarvis not in PATH. Searching install locations..." -ForegroundColor Yellow
$searchPaths = @(
    "$env:USERPROFILE\.local\bin\jarvis*",
    "$env:USERPROFILE\.cargo\bin\jarvis*",
    "$env:USERPROFILE\OpenJarvis\.venv\Scripts\jarvis*",
    "$env:USERPROFILE\openjarvis\.venv\Scripts\jarvis*",
    "C:\OpenJarvis\.venv\Scripts\jarvis*",
    "$env:USERPROFILE\.uv\bin\jarvis*",
    "$env:APPDATA\uv\bin\jarvis*"
)

$found = $null
foreach ($path in $searchPaths) {
    $match = Get-Item $path -ErrorAction SilentlyContinue
    if ($match) {
        $found = $match.FullName
        Write-Host "Found: $found" -ForegroundColor Green
        break
    }
}

# 3. Check for OpenJarvis directory with uv
$openJarvisDirs = @(
    "$env:USERPROFILE\OpenJarvis",
    "$env:USERPROFILE\openjarvis",
    "C:\OpenJarvis",
    "$env:USERPROFILE\Documents\OpenJarvis"
)

$openJarvisDir = $null
foreach ($dir in $openJarvisDirs) {
    if (Test-Path "$dir\pyproject.toml") {
        $openJarvisDir = $dir
        Write-Host "Found OpenJarvis at: $dir" -ForegroundColor Green
        break
    }
}

if ($openJarvisDir) {
    Write-Host ""
    Write-Host "OpenJarvis is installed at: $openJarvisDir" -ForegroundColor Cyan
    Write-Host "Trying 'uv run jarvis' from that directory..." -ForegroundColor Yellow
    Set-Location $openJarvisDir
    uv run jarvis
} elseif ($found) {
    Write-Host ""
    Write-Host "Adding jarvis directory to your PATH permanently..." -ForegroundColor Yellow
    $dir = Split-Path $found
    $currentPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
    if ($currentPath -notlike "*$dir*") {
        [System.Environment]::SetEnvironmentVariable("PATH", "$currentPath;$dir", "User")
        Write-Host "Done! Close and reopen PowerShell, then run: jarvis" -ForegroundColor Green
    } else {
        Write-Host "Directory already in PATH. Close and reopen PowerShell, then run: jarvis" -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "Could not find OpenJarvis. Let's re-run the installer..." -ForegroundColor Red
    Write-Host "Running: irm https://open-jarvis.github.io/OpenJarvis/install.ps1 | iex" -ForegroundColor Yellow
    irm https://open-jarvis.github.io/OpenJarvis/install.ps1 | iex
}

Write-Host ""
Read-Host "Press Enter to exit"

# OpenJarvis Installer for Windows
# Run this script as Administrator for best results
# Right-click this file and select "Run with PowerShell"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  OpenJarvis - Personal AI Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will install OpenJarvis including:" -ForegroundColor Yellow
Write-Host "  - uv (Python package manager)" -ForegroundColor White
Write-Host "  - Python virtual environment" -ForegroundColor White
Write-Host "  - Ollama (local AI model runner)" -ForegroundColor White
Write-Host "  - A starter AI model (~3 mins on broadband)" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Proceed with installation? (Y/N)"
if ($confirm -ne 'Y' -and $confirm -ne 'y') {
    Write-Host "Installation cancelled." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Starting OpenJarvis installation..." -ForegroundColor Green

# Run the official OpenJarvis Windows installer
irm https://open-jarvis.github.io/OpenJarvis/install.ps1 | iex

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start Jarvis, open PowerShell and run:" -ForegroundColor Yellow
Write-Host "  jarvis" -ForegroundColor White
Write-Host ""
Write-Host "Check status with:" -ForegroundColor Yellow
Write-Host "  jarvis doctor" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"

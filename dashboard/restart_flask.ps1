Write-Host "Stopping any existing Flask/Python processes..."
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "Starting Flask server..."
cd "C:\JeffLocal\dashboard"
python -m flask run

Write-Host "Flask server started. Keep this window open."

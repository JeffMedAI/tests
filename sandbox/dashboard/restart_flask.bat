@echo off
echo Stopping any existing Flask/Python processes...
taskkill /IM python.exe /F 2>nul
timeout /t 2
echo Starting Flask server...
cd /d "C:\JeffLocal\dashboard"
python -m flask run
pause

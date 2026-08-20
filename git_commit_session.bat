@echo off
cd /d C:\JeffLocal

echo Killing any running git.exe processes...
taskkill /f /im git.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo Clearing all stale lock files...
for %%f in (.git\*.lock) do (
    echo   Removing: %%f
    del /f "%%f" 2>nul
)

echo Running git add...
git add docs\sessions\ PROJECT_MEMORY.md

echo Running git commit...
git commit -m "memory: session end protocol 2026-06-12 18:00"

echo Running git push...
git push origin HEAD

echo.
echo Done.
pause

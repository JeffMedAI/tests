@echo off
:: git_safe_commit.bat
:: Safe git commit that clears stale locks and kills competing git processes first.
:: Usage: git_safe_commit.bat "commit message"
::
:: Called by all automated tasks (session end, daily briefing, etc.)
:: Permanent fix for index.lock / HEAD.lock race conditions.

setlocal

set REPO=C:\JeffLocal
set MSG=%~1

if "%MSG%"=="" (
    echo ERROR: No commit message provided.
    echo Usage: git_safe_commit.bat "your commit message"
    exit /b 1
)

cd /d %REPO%

echo [1/4] Killing any running git.exe processes...
taskkill /f /im git.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo [2/4] Clearing all stale lock files...
for %%f in (.git\*.lock) do (
    echo   Removing: %%f
    del /f "%%f" 2>nul
)

echo [3/4] Running git add + commit...
git add docs\sessions\ PROJECT_MEMORY.md
git commit -m "%MSG%"
if errorlevel 1 (
    echo WARNING: git commit failed or nothing to commit.
)

echo [4/4] Pushing to remote...
git push origin HEAD
if errorlevel 1 (
    echo ERROR: git push failed. Check your network or credentials.
    exit /b 1
)

echo.
echo Done. Committed and pushed successfully.
exit /b 0

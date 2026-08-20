@echo off
del /f "C:\JeffLocal\.git\index.lock" 2>nul
if not exist "C:\JeffLocal\.git\index.lock" (
    echo SUCCESS: Lock file deleted.
) else (
    echo FAILED: Could not delete lock file.
)
pause

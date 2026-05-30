# Fix corrupted git index and commit pending changes
# Run this from PowerShell (no admin needed)
Set-Location C:\JeffLocal

Write-Host "=== Fixing git index ===" -ForegroundColor Cyan

# Remove lock file if present
if (Test-Path .git\index.lock) {
    Remove-Item .git\index.lock -Force
    Write-Host "Removed index.lock"
}

# Rebuild index from HEAD (fixes corruption)
Remove-Item .git\index -Force -ErrorAction SilentlyContinue
Write-Host "Cleared corrupted index"
git read-tree HEAD
Write-Host "Index rebuilt from HEAD"

# Check status
git status --short

# Stage all changes and commit
Write-Host "`n=== Committing ===" -ForegroundColor Cyan
git add -A
git commit -m "phase1: sidebar refactor, test suite fixes, E2E run script"
git push origin HEAD

Write-Host "`nDone." -ForegroundColor Green

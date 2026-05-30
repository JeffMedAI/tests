Remove-Item C:\JeffLocal\.git\index.lock -Force
Write-Host "Lock removed. Running git add + commit + push..."
cd C:\JeffLocal
git add -A
git commit -m "phase1: pending changes — watchdog, N1/N2, sandbox degraded, E2E suite"
git push origin HEAD
Write-Host "Done."

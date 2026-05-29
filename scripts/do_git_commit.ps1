# Git commit script - run from C:\JeffLocal\
# Removes stale lock, stages all changes, commits, and pushes

Set-Location "C:\JeffLocal"

# Remove stale lock if present
$lockFile = "C:\JeffLocal\.git\index.lock"
if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force
    Write-Host "Removed stale git lock" -ForegroundColor Yellow
}

# Configure git identity
git config user.email "5256863@gmail.com"
git config user.name "Saeed"

# Stage everything
git add sandbox/agents/
git add governance/
git add docs/
git add scripts/
git add config/
git add backups/RESTORE_POINT_20260529/
git add JeffLocal_Master_Strategy_v1.2.docx
git add JeffLocal_Dispatch_Report_20260529.docx
git add README.md
git add app/
git add tests/
git add dashboard/
git add sandbox/
git add "*.png"
git add .gitignore

# Show what's staged
Write-Host "`nStaged files:" -ForegroundColor Cyan
git diff --cached --stat

# Commit
$msg = @"
chore: restore point 2026-05-29 -- all 8 agents, strategy onboarding complete

All 8 agent CLAUDE.md files present (lead, backend, frontend, database, test, security, devops, strategy)
Strategy Agent fully onboarded (daily script, governance roster, lead protocol updated)
Cookie fix approval pack ready (AWAITING SAEED SIGN-OFF)
Sandbox degraded-status fix ready (AWAITING SAEED SIGN-OFF)
Production dashboard live at dashboard.app-avamed.uk
Backup restore point created at backups/RESTORE_POINT_20260529/
Claude Desktop reinstalled, computer-use and Chrome MCP verified working
Master Strategy v1.2 and Dispatch Report 2026-05-29 added
"@
git commit -m $msg

# Tag this as a restore point
git tag -a "RESTORE_20260529" -m "Restore point 2026-05-29 - all agents present, tools verified"

# Push
Write-Host "`nPushing to origin..." -ForegroundColor Cyan
git push origin HEAD
git push origin RESTORE_20260529

Write-Host "Done. Restore point committed and tagged as RESTORE_20260529" -ForegroundColor Green
git log --oneline -5

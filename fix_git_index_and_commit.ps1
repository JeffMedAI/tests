# fix_git_index_and_commit.ps1
# Run as normal user (no admin needed) from C:\JeffLocal
# Repairs corrupted git index, stages Phase 1A/1B changes, commits and pushes.

Set-Location "C:\JeffLocal"

Write-Host "Step 1: Removing corrupted git index..."
Remove-Item ".git\index" -Force -ErrorAction SilentlyContinue
Write-Host "  Done."

Write-Host "Step 2: Rebuilding index from HEAD..."
git reset HEAD 2>&1
Write-Host "  Done."

Write-Host "Step 3: Staging Phase 1A/1B production changes..."
git add dashboard/app/auth.py
git add dashboard/app/main.py
git add "dashboard/templates/"
git add dashboard/static/dashboard.css
git add sandbox/dashboard/app/main.py
git add .mcp.json
Write-Host "  Done."

Write-Host "Step 4: Committing..."
git commit -m "deploy: Phase 1A security + Phase 1B UX overhaul to production

Phase 1A (security):
- auth.py: SHA-256 token hashing (plaintext never stored in DB)
- auth.py: rate limiting 3 resets/hr per user
- main.py: anti-enumeration on /forgot route
- forgot.html: remove error leaking username existence; 60min expiry

Phase 1B (UX/UI):
- All 11 templates: NHS blue topbar nav, dashboard redesign
- dashboard.css: full UX audit fixes C1-C5, H1-H4, M1-M8, L1-L5
- SVG charts, ARIA tabs, focus-visible, 44px touch targets

Sandbox:
- sandbox main.py: _nav_alert_count + sliding cookie refresh back-ported

n8n:
- .mcp.json: n8n MCP server added for Claude Code sessions"

Write-Host "Step 5: Pushing..."
git push origin HEAD

Write-Host ""
Write-Host "All done. Check above for any errors."

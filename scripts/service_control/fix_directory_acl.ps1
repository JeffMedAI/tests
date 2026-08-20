<#
.SYNOPSIS
    Remediates the "C:\JeffLocal and C:\JeffLocal\config writable by too many
    accounts" security finding (PROJECT_MEMORY.md open item #3).

.DESCRIPTION
    DO NOT SCHEDULE OR AUTO-RUN THIS SCRIPT. It changes Windows folder
    security permissions on the live production directory. Saeed (or another
    admin) must read it, then run it manually in an elevated PowerShell
    window, on a day when a short dashboard restart-and-verify is acceptable.

    Confirmed 2026-07-17 via Get-Acl against the real folders. Both
    C:\JeffLocal and C:\JeffLocal\config currently grant write access to four
    principals that should not have it:
      1. NT AUTHORITY\Authenticated Users       (Modify)
      2. NT AUTHORITY\Authenticated Users       (a second ACE, generic-rights
                                                  code -536805376 — also grants write)
      3. PC8-FYR03-6446\CodexSandboxUsers       (Modify)
      4. An orphaned SID with no resolvable name (Modify) —
         S-1-5-21-3757111369-3529092462-2350175298-2510526684

    Left untouched (these look correct — read-only or admin-only):
      - BUILTIN\Administrators   (FullControl)   -- keep
      - NT AUTHORITY\SYSTEM      (FullControl)   -- keep
      - BUILTIN\Users            (ReadAndExecute) -- keep, read-only is fine

    This also unblocks the new tenant-config loader (feature/multitenancy-db-path,
    merged 2026-07-17), which correctly refuses to start any tenant while
    config\ is writable like this.

.NOTES
    Run as: Administrator, from an elevated PowerShell prompt.
    Read every command before running it. Test in a non-production copy
    first if unsure what /T (recurse to existing children) will touch.
#>

# --- STEP 1: confirm current state before changing anything ---
Write-Host "Current C:\JeffLocal permissions:" -ForegroundColor Cyan
icacls "C:\JeffLocal"

Write-Host "`nCurrent C:\JeffLocal\config permissions:" -ForegroundColor Cyan
icacls "C:\JeffLocal\config"

Write-Host "`nPress Ctrl+C now if you have not read the .DESCRIPTION above." -ForegroundColor Yellow
Read-Host "Press Enter to continue with the removal, or Ctrl+C to abort"

# --- STEP 2: remove the four write-granting principals from both folders ---
# /T recurses into existing files/subfolders (their explicit ACEs won't
# update just because the parent folder's ACL changed). /C continues past
# any single-file error (e.g. a file locked by the running dashboard process)
# instead of aborting the whole run.

foreach ($path in @("C:\JeffLocal", "C:\JeffLocal\config")) {
    Write-Host "`n--- Fixing $path ---" -ForegroundColor Cyan

    icacls $path /remove:g "Authenticated Users" /T /C
    icacls $path /remove:g "CodexSandboxUsers" /T /C
    icacls $path /remove:g "*S-1-5-21-3757111369-3529092462-2350175298-2510526684" /T /C
}

# --- STEP 3: verify the fix ---
Write-Host "`nC:\JeffLocal permissions AFTER fix:" -ForegroundColor Cyan
icacls "C:\JeffLocal"

Write-Host "`nC:\JeffLocal\config permissions AFTER fix:" -ForegroundColor Cyan
icacls "C:\JeffLocal\config"

# --- STEP 4: service-restart test (per memory: fix must be verified live) ---
Write-Host "`nNow restart the dashboard service and confirm it still starts cleanly:" -ForegroundColor Yellow
Write-Host "  powershell -File C:\JeffLocal\scripts\service_control\restart_all.ps1 -DashOnly"
Write-Host "Then check: curl http://127.0.0.1:8765/api/health"
Write-Host "If a tenant is configured, also confirm '-Tenant <name>' still starts (tenant loader's ACL check should now pass)."

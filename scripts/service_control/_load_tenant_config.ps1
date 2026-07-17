# Loads one tenant's non-secret config (JEFFLOCAL_DB_PATH, JEFFLOCAL_PORT,
# JEFFLOCAL_TENANT_NAME) from config\tenants\<tenant>.env into the current
# process environment, so _launch_dashboard.ps1 can point uvicorn at that
# tenant's database and port.
#
# THIS FILE HOLDS NO SECRETS. Tenant secrets (e.g. a future per-tenant intake
# secret) are a separate, not-yet-decided piece of work — see
# governance/MULTI_TENANCY_PROPOSAL.md §8 step 6. Adding a secret value to a
# tenant .env file here is out of scope for this loader and must not be done
# without extending the allowlist model _load_secrets.ps1 already uses.
#
# WITH NO -Tenant FLAG, THIS SCRIPT IS NEVER CALLED. That is deliberate:
# today's single-instance production behaviour (port 8765, default DB path)
# must be unchanged for a caller that supplies no tenant name. See
# _launch_dashboard.ps1.
#
# A TENANT NAME THAT DOESN'T RESOLVE TO A REAL CONFIG FILE IS FATAL, unlike
# a missing secrets.env. Secrets absent is a safe, working default (no
# secret-gated endpoint accepts traffic). A requested tenant that doesn't
# exist is an ops mistake — starting on the wrong port or database silently
# would be worse than refusing to start.

# Every key this loader is permitted to set from a tenant file. Same allowlist
# discipline as _load_secrets.ps1, for the same reason: this becomes the
# dashboard process's environment.
$script:AllowedTenantKeys = @(
    'JEFFLOCAL_DB_PATH',
    'JEFFLOCAL_PORT',
    'JEFFLOCAL_TENANT_NAME'
)

function Import-JeffTenantConfig {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Tenant,
        [string]$ConfigRoot = "C:\JeffLocal\config\tenants",
        [string]$LogFile
    )

    function Write-TenantLog([string]$msg) {
        if ($LogFile) {
            "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" | Out-File $LogFile -Append
        }
    }

    # Tenant name becomes part of a file path below. Restrict to a safe
    # charset up front so it cannot be used for path traversal (e.g.
    # "..\..\secrets" is rejected before it ever reaches Join-Path).
    if ($Tenant -notmatch '^[a-zA-Z0-9_-]+$') {
        # Sanitise before logging: same reasoning as the refused-key log
        # below — an attacker-controlled string must never reach a log file
        # unfiltered.
        $safeTenant = ($Tenant -replace '[^\x20-\x7E]', '?')
        if ($safeTenant.Length -gt 64) { $safeTenant = $safeTenant.Substring(0, 64) + '...' }
        Write-TenantLog "[TENANT] REFUSING TO START: tenant name '$safeTenant' contains characters outside [a-zA-Z0-9_-]"
        throw "Invalid tenant name: $safeTenant"
    }

    # Directory-ACL check, same reasoning and same caveats as
    # _load_secrets.ps1's threat-model comment: advisory, not a trust
    # boundary (misses non-standard SIDs, generic-rights ACEs, and
    # reparse-point redirection), but still worth doing — JEFFLOCAL_DB_PATH
    # is an arbitrary-database-repoint lever if this directory is writable
    # by an untrusted account.
    try {
        $dirAcl  = Get-Acl -LiteralPath $ConfigRoot -ErrorAction Stop
        $writers = $dirAcl.Access | Where-Object {
            $_.AccessControlType -eq 'Allow' -and
            $_.IdentityReference -match 'Everyone|BUILTIN\\Users|Authenticated Users|INTERACTIVE' -and
            $_.FileSystemRights -match 'Write|Modify|FullControl|CreateFiles|AppendData'
        }
        if ($writers) {
            $who = (($writers.IdentityReference | ForEach-Object { $_.ToString() }) | Select-Object -Unique) -join ', '
            Write-TenantLog "[TENANT] REFUSING TO START: $ConfigRoot is writable by: $who"
            throw "Tenant config directory $ConfigRoot is writable by untrusted accounts: $who"
        }
    } catch [System.Management.Automation.ItemNotFoundException] {
        Write-TenantLog "[TENANT] REFUSING TO START: $ConfigRoot does not exist"
        throw "Tenant config directory does not exist: $ConfigRoot"
    }

    $envFile = Join-Path $ConfigRoot "$Tenant.env"
    if (-not (Test-Path -LiteralPath $envFile)) {
        Write-TenantLog "[TENANT] REFUSING TO START: no config file at $envFile for tenant '$Tenant'"
        throw "Unknown tenant: $Tenant (expected $envFile)"
    }

    $loaded = @()
    foreach ($line in (Get-Content -LiteralPath $envFile)) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }

        $idx = $trimmed.IndexOf('=')
        if ($idx -lt 1) { continue }

        $key = $trimmed.Substring(0, $idx).Trim()
        $val = $trimmed.Substring($idx + 1).Trim()

        if ($val.Length -ge 2 -and
            (($val.StartsWith('"') -and $val.EndsWith('"')) -or
             ($val.StartsWith("'") -and $val.EndsWith("'")))) {
            $val = $val.Substring(1, $val.Length - 2)
        }

        if ($key -notin $script:AllowedTenantKeys) {
            # Sanitise before logging: strip non-printable chars and cap
            # length, same as the tenant-name case above and the refused-key
            # handling in _load_secrets.ps1.
            $safeKey = ($key -replace '[^\x20-\x7E]', '?')
            if ($safeKey.Length -gt 64) { $safeKey = $safeKey.Substring(0, 64) + '...' }
            Write-TenantLog "[TENANT] REFUSED key not on allowlist: $safeKey"
            continue
        }

        # -ErrorAction Stop is required: Set-Item's failures are
        # non-terminating, so without it the catch never runs and a failed
        # set would still be recorded as loaded. That matters more here than
        # almost anywhere else in this codebase — if JEFFLOCAL_DB_PATH
        # silently fails to set but is reported as loaded, the completeness
        # check below passes and this tenant falls through to db.py's
        # DEFAULT database, silently mixing this tenant's data with
        # whichever tenant (or the production instance) owns that database.
        try {
            Set-Item -Path "Env:$key" -Value $val -ErrorAction Stop
            $loaded += $key
        } catch {
            Write-TenantLog "[TENANT] FAILED to set $key"
        }
    }

    if ('JEFFLOCAL_DB_PATH' -notin $loaded -or 'JEFFLOCAL_PORT' -notin $loaded) {
        Write-TenantLog "[TENANT] REFUSING TO START: $envFile is missing JEFFLOCAL_DB_PATH or JEFFLOCAL_PORT"
        throw "Incomplete tenant config for '$Tenant' at $envFile"
    }

    Write-TenantLog "[TENANT] loaded config for '$Tenant' from $envFile ($($loaded -join ', '))"
}

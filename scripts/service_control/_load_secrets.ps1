# Loads KEY=VALUE pairs from config\secrets.env into the current process
# environment, so services launched from this session can read them the normal
# way (os.environ.get in Python, $env: in PowerShell). No app code changes and
# no new dependency — the code already reads os.environ, it just had nothing to
# read.
#
# WHY THIS EXISTS: there was no secrets mechanism at all. No .env, no dotenv,
# and the launchers set no environment variables. That left JEFF_WEBHOOK_SECRET
# unsettable (a standing pre-go-live blocker) and STMARKS_INTAKE_SECRET with
# nowhere to live.
#
# SAFETY RULES BAKED IN HERE:
#   - Secret VALUES are never logged. Only key names are, so an operator can
#     confirm what loaded without the log becoming a secrets file.
#   - config\secrets.env is already gitignored via the `config/*secret*` rule.
#   - A missing file is NOT fatal. Services that need a secret fail closed on
#     their own (e.g. the St Marks intake endpoint returns 503 when
#     STMARKS_INTAKE_SECRET is unset) — that is the desired behaviour, and it is
#     safer than refusing to start the dashboard entirely.
#   - Warns (does not fail) if the file is readable beyond its owner.

function Import-JeffSecrets {
    param(
        [string]$Path = "C:\JeffLocal\config\secrets.env",
        [string]$LogFile
    )

    function Write-SecretLog([string]$msg) {
        if ($LogFile) {
            "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" | Out-File $LogFile -Append
        }
    }

    if (-not (Test-Path -LiteralPath $Path)) {
        Write-SecretLog "[SECRETS] no secrets file at $Path - continuing without it"
        return
    }

    # Broad read access on a secrets file is a finding, not a fatal error.
    try {
        $acl = Get-Acl -LiteralPath $Path
        $broad = $acl.Access | Where-Object {
            $_.IdentityReference -match 'Everyone|BUILTIN\\Users|Authenticated Users' -and
            $_.AccessControlType -eq 'Allow'
        }
        if ($broad) {
            $who = ($broad.IdentityReference | ForEach-Object { $_.ToString() }) -join ', '
            Write-SecretLog "[SECRETS] WARNING: $Path is readable by: $who"
            Write-SecretLog "[SECRETS] restrict it with: icacls `"$Path`" /inheritance:r /grant:r `"$($env:USERNAME):(R)`""
        }
    } catch {
        Write-SecretLog "[SECRETS] could not check file permissions on $Path"
    }

    $loaded  = @()
    $skipped = 0

    foreach ($line in (Get-Content -LiteralPath $Path)) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }

        $idx = $trimmed.IndexOf('=')
        if ($idx -lt 1) { $skipped++; continue }

        $key = $trimmed.Substring(0, $idx).Trim()
        $val = $trimmed.Substring($idx + 1).Trim()

        # Reject anything that isn't a plain env var name, rather than passing it
        # to Set-Item and hoping.
        if ($key -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') { $skipped++; continue }

        # Strip one layer of surrounding quotes, so both FOO=bar and FOO="bar"
        # work. Values legitimately contain '=' (base64), so only the FIRST '='
        # splits.
        if ($val.Length -ge 2 -and
            (($val.StartsWith('"') -and $val.EndsWith('"')) -or
             ($val.StartsWith("'") -and $val.EndsWith("'")))) {
            $val = $val.Substring(1, $val.Length - 2)
        }

        Set-Item -Path "Env:$key" -Value $val
        $loaded += $key
    }

    if ($loaded.Count -gt 0) {
        # Key NAMES only — never the values.
        Write-SecretLog "[SECRETS] loaded $($loaded.Count) key(s) from secrets.env: $($loaded -join ', ')"
    } else {
        Write-SecretLog "[SECRETS] secrets.env present but no valid keys found"
    }
    if ($skipped -gt 0) {
        Write-SecretLog "[SECRETS] skipped $skipped malformed line(s)"
    }
}

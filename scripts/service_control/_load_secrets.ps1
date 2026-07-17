# Loads a fixed, allowlisted set of KEY=VALUE secrets from config\secrets.env
# into the current process environment, so services launched from this session
# can read them the normal way (os.environ.get in Python, $env: in PowerShell).
# No app code changes and no new dependency — the code already reads os.environ,
# it just had nothing to read.
#
# WHY THIS EXISTS: there was no secrets mechanism at all. No .env, no dotenv,
# and the launchers set no environment variables. That left JEFF_WEBHOOK_SECRET
# unsettable (a standing pre-go-live blocker) and STMARKS_INTAKE_SECRET with
# nowhere to live.
#
# THREAT MODEL — read this before changing anything here.
# This loader's contents become the environment of the dashboard process, which
# holds the patient database, session auth, and the deterministic safety logic.
# An attacker who controls this FILE controls that environment, and an
# attacker-controlled environment is an attacker-controlled process (e.g. via
# PYTHONPATH, which is a perfectly well-formed variable name). So:
#
#   - Keys are checked against an ALLOWLIST OF NAMES ($script:AllowedSecretKeys),
#     not a regex for "looks like a variable name". A name-shape regex accepts
#     PYTHONPATH / PATH / PSModulePath and hands over arbitrary code execution.
#     Adding a key here is a deliberate, reviewable code change. That is the point.
#   - The DIRECTORY's write ACL is checked, not the file's, because an attacker
#     who plants secrets.env owns it and can give it a pristine ACL — a file-ACL
#     check is structurally incapable of catching a hostile file. If an untrusted
#     account can write into the directory, this refuses to load rather than use
#     attacker-controlled values.
#     THIS CHECK IS ADVISORY, NOT A TRUST BOUNDARY. A standard ACL enumeration
#     misses: non-standard principals (e.g. CodexSandboxUsers or other SIDs not
#     matched by the identity patterns below), generic-rights ACEs (GENERIC_ALL/
#     GENERIC_WRITE do not always surface as the named FileSystemRights this
#     checks for), and reparse points/junctions redirecting the "directory" this
#     code inspects to a different, writable location on disk. Do not describe
#     this gate as sufficient on its own — it is one layer, and host-level write
#     access to C:\JeffLocal already implies compromise this script cannot fully
#     detect. The real trust boundary is who can write to that machine at all.
#   - Secret VALUES are never logged. Only key names. The log must never become a
#     secrets file.
#   - A key is only reported as loaded if Set-Item actually succeeded. A log that
#     claims a secret loaded when it didn't produces false confidence in exactly
#     the wrong direction.
#
# A MISSING FILE IS NOT FATAL, deliberately: an absent file with fail-closed
# endpoints is a safe state, and refusing to boot the dashboard over it would be
# a self-inflicted outage.
#
# FAIL-CLOSED STATUS OF DEPENDENT ENDPOINTS (verified 2026-07-16, do not
# paraphrase this without re-checking the code):
#   - St Marks intake  — FAILS CLOSED. routers/stmarks.py returns 503 when
#                        STMARKS_INTAKE_SECRET is unset. Correct.
#   - Jeff n8n webhook — FAILS OPEN. routers/n8n.py skips HMAC verification and
#                        ACCEPTS the request when JEFF_WEBHOOK_SECRET is unset.
#                        This is a REAL GAP, flagged by the 2026-05-30 HMAC review
#                        (recommendation N1) and still unimplemented. test_mode is
#                        read from the request's OWN payload, so it is attacker-
#                        controlled and gates nothing — do not describe this
#                        endpoint as gated by test_mode. Fixing the open-fail
#                        touches auth logic and needs Saeed's sign-off — tracked
#                        separately. Until then, do NOT describe this loader as
#                        safe because "endpoints fail closed": only one of them
#                        does, and the other's condition is not a real gate.

# Every key this loader is permitted to set. Anything else is refused and logged.
# Extending this list is a security-relevant change — get it reviewed.
$script:AllowedSecretKeys = @(
    'JEFF_WEBHOOK_SECRET',
    'STMARKS_INTAKE_SECRET'
)

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

    # The file exists, so we are about to load its contents into this process's
    # environment. Before we do: can an untrusted account write into the directory
    # it lives in? If so, its contents are not trustworthy and we must not load
    # them. This check runs ONLY when a file is actually present, so a system with
    # no secrets.env boots normally regardless of directory ACL.
    $configDir = Split-Path -Parent $Path
    try {
        $dirAcl  = Get-Acl -LiteralPath $configDir -ErrorAction Stop
        $writers = $dirAcl.Access | Where-Object {
            $_.AccessControlType -eq 'Allow' -and
            $_.IdentityReference -match 'Everyone|BUILTIN\\Users|Authenticated Users|INTERACTIVE' -and
            $_.FileSystemRights -match 'Write|Modify|FullControl|CreateFiles|AppendData'
        }
        if ($writers) {
            $who = (($writers.IdentityReference | ForEach-Object { $_.ToString() }) | Select-Object -Unique) -join ', '
            Write-SecretLog "[SECRETS] REFUSING TO LOAD: $configDir is writable by: $who"
            Write-SecretLog "[SECRETS] a secrets file in a directory untrusted accounts can write to is attacker-controllable; loading it would hand them this process's environment."
            Write-SecretLog "[SECRETS] fix the directory ACL, then restart. No secrets loaded."
            return
        }
    } catch {
        # Cannot determine the ACL => cannot establish the file is trustworthy.
        # Refuse rather than assume. Message is fixed text; never interpolate $_,
        # which could carry file content.
        Write-SecretLog "[SECRETS] REFUSING TO LOAD: could not read the ACL of $configDir to verify it is not writable by untrusted accounts. No secrets loaded."
        return
    }

    $loaded   = @()
    $refused  = @()
    $skipped  = 0

    foreach ($line in (Get-Content -LiteralPath $Path)) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }

        $idx = $trimmed.IndexOf('=')
        if ($idx -lt 1) { $skipped++; continue }

        $key = $trimmed.Substring(0, $idx).Trim()
        $val = $trimmed.Substring($idx + 1).Trim()

        # ALLOWLIST OF NAMES, not a shape check. See threat model above.
        if ($key -notin $script:AllowedSecretKeys) {
            # Sanitise before it ever reaches a log: strip non-printable/control
            # characters and cap length, so a hostile secrets.env cannot use a
            # bogus "key" to inject log lines or blow up the log file size.
            $safeKey = ($key -replace '[^\x20-\x7E]', '?')
            if ($safeKey.Length -gt 64) { $safeKey = $safeKey.Substring(0, 64) + '...' }
            $refused += $safeKey
            continue
        }

        # Strip one layer of surrounding quotes, so both FOO=bar and FOO="bar"
        # work. Values legitimately contain '=' (base64), so only the FIRST '='
        # splits.
        if ($val.Length -ge 2 -and
            (($val.StartsWith('"') -and $val.EndsWith('"')) -or
             ($val.StartsWith("'") -and $val.EndsWith("'")))) {
            $val = $val.Substring(1, $val.Length - 2)
        }

        # -ErrorAction Stop is required: Set-Item's failures are non-terminating,
        # so without it the catch never runs and we would report a key as loaded
        # when it silently wasn't.
        try {
            Set-Item -Path "Env:$key" -Value $val -ErrorAction Stop
            $loaded += $key
        } catch {
            # Key name only. Never $_ — the error text can echo the value.
            Write-SecretLog "[SECRETS] FAILED to set $key"
            $skipped++
        }
    }

    if ($loaded.Count -gt 0) {
        # Key NAMES only — never the values.
        Write-SecretLog "[SECRETS] loaded $($loaded.Count) key(s) from secrets.env: $($loaded -join ', ')"
    } else {
        Write-SecretLog "[SECRETS] secrets.env present but no allowlisted keys loaded"
    }
    if ($refused.Count -gt 0) {
        # Refused key NAMES are safe and important to log: an unexpected key in
        # this file is a strong tamper signal. Cap how many we print — a hostile
        # or corrupt file with thousands of bogus "keys" must not blow up the
        # log file. The count above is always the true total either way.
        $shown = $refused | Select-Object -First 20
        $more  = if ($refused.Count -gt 20) { " (+$($refused.Count - 20) more, not shown)" } else { "" }
        Write-SecretLog "[SECRETS] REFUSED $($refused.Count) key(s) not on the allowlist: $($shown -join ', ')$more"
    }
    if ($skipped -gt 0) {
        Write-SecretLog "[SECRETS] skipped $skipped malformed or failed line(s)"
    }
}

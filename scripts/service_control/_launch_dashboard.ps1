# Hidden launcher - called by watchdog only. Runs uvicorn and appends stdout+stderr to log.
#
# -Tenant is OPTIONAL and defaults to nothing. Callers that omit it (every
# caller today, including watchdog) get EXACTLY today's behaviour: port 8765,
# dashboard.log, and db.py's own default database path. This must never
# change out from under an existing caller — see
# governance/MULTI_TENANCY_PROPOSAL.md §8.
#
# Callers that pass -Tenant <name> get that tenant's port and database from
# config\tenants\<name>.env (see _load_tenant_config.ps1). An unknown tenant
# name fails loudly rather than starting on the wrong port/database.
param(
    [string]$Tenant
)

$python  = "C:\JeffLocal\dashboard\.venv\Scripts\python.exe"
$workDir = "C:\JeffLocal\dashboard"
$port    = 8765
$logFile = "C:\JeffLocal\logs\service_control\dashboard.log"

if ($Tenant) {
    $logFile = "C:\JeffLocal\logs\service_control\dashboard-$Tenant.log"
}

New-Item -ItemType Directory -Path (Split-Path $logFile) -Force | Out-Null

if ((Test-Path $logFile) -and (Get-Item $logFile).Length -gt 3MB) {
    Move-Item $logFile "$logFile.old" -Force
}

if ($Tenant) {
    $tenantLoader = Join-Path $PSScriptRoot "_load_tenant_config.ps1"
    . $tenantLoader
    # Deliberately NOT try/catch: an unknown or incomplete tenant config must
    # stop this launcher, not fall through to the default port/database.
    Import-JeffTenantConfig -Tenant $Tenant -LogFile $logFile
    $port = $env:JEFFLOCAL_PORT
}

if (-not (Test-Path $python)) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [ERROR] venv not found at $python - run: python -m venv C:\JeffLocal\dashboard\.venv" |
        Out-File $logFile -Append
    exit 1
}

# Load config\secrets.env into the environment so uvicorn inherits it.
# A missing file is not fatal (see _load_secrets.ps1). Note: only the St Marks
# intake fails closed without its secret; the Jeff n8n webhook currently fails
# OPEN when JEFF_WEBHOOK_SECRET is unset. Do not treat "no secrets file" as a
# safe state for that endpoint — see the FAIL-CLOSED STATUS block in
# _load_secrets.ps1.
$secretsLoader = Join-Path $PSScriptRoot "_load_secrets.ps1"
if (Test-Path $secretsLoader) {
    . $secretsLoader
    Import-JeffSecrets -LogFile $logFile
} else {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [SECRETS] loader not found at $secretsLoader - starting without secrets" |
        Out-File $logFile -Append
}

Push-Location $workDir
try {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [START] uvicorn starting on port $port$(if ($Tenant) { " (tenant: $Tenant)" })" | Out-File $logFile -Append
    & $python -m uvicorn app.main:app --host 0.0.0.0 --port $port 2>&1 |
        ForEach-Object { "$(Get-Date -Format 'HH:mm:ss') $_" } |
        Out-File $logFile -Append
} finally {
    Pop-Location
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [STOP] uvicorn exited" | Out-File $logFile -Append
}

param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$ErrorActionPreference = "Stop"

$configPath = "C:\JeffLocal\config\security\jeie_v1.config.json"
if (-not (Test-Path -LiteralPath $configPath)) {
    throw "Security config not found: $configPath"
}

$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$encryptedRaw = [string]$config.queue_encrypted_raw_path
if ([string]::IsNullOrWhiteSpace($encryptedRaw)) {
    throw "queue_encrypted_raw_path missing from security config."
}

$source = Resolve-Path -LiteralPath $Path
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "Deadletter file not found: $Path"
}

New-Item -ItemType Directory -Path $encryptedRaw -Force | Out-Null

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$baseName = [System.IO.Path]::GetFileName($source.Path)
if ($baseName.StartsWith("decrypt_failed_")) {
    $baseName = $baseName.Substring("decrypt_failed_".Length)
}

$candidate = Join-Path $encryptedRaw ("replay_{0}_{1}" -f $timestamp, $baseName)
$index = 1
while (Test-Path -LiteralPath $candidate) {
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($baseName)
    $ext = [System.IO.Path]::GetExtension($baseName)
    $candidate = Join-Path $encryptedRaw ("replay_{0}_{1}_{2}{3}" -f $timestamp, $stem, $index, $ext)
    $index += 1
}

Copy-Item -LiteralPath $source.Path -Destination $candidate -ErrorAction Stop

[pscustomobject]@{
    source = $source.Path
    copied_to = $candidate
    note = "Original deadletter was not deleted. Run decrypt_encrypted_raw.py --file on copied_to, or run the normal decrypt cycle."
} | ConvertTo-Json -Depth 3

# Fix stale git index.lock
$lockFile = "C:\JeffLocal\.git\index.lock"
if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force
    Write-Host "Deleted: $lockFile"
} else {
    Write-Host "Lock file not found — already clean."
}
Write-Host "Done. Press any key to close."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

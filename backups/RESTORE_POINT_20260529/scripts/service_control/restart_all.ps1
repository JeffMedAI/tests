<#
.SYNOPSIS
    Force-restart JeffLocal services. Kills anything on ports 8765 / 5678 then calls watchdog.

.PARAMETER DashOnly   Restart dashboard only.
.PARAMETER N8nOnly    Restart n8n only.
#>
param([switch]$DashOnly, [switch]$N8nOnly)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$watchdog  = "$ScriptDir\watchdog.ps1"

$watchArgs = @("-Force")
if ($DashOnly) { $watchArgs += "-DashOnly" }
if ($N8nOnly)  { $watchArgs += "-N8nOnly" }

Write-Host "Restarting JeffLocal services..."
& $watchdog @watchArgs

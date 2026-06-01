# JeffLocal Agent Launcher — Model-Routed
# Usage: .\scripts\launch_agent.ps1 -Agent backend
# Routes each agent to the cheapest model that handles its task complexity.
#
# Model assignments:
#   opus   — Lead, Security (orchestration, judgment, veto decisions)
#   sonnet — Backend, Frontend, Database, Strategy (code, SQL, docs)
#   haiku  — Test, DevOps (pattern-based, scripting, low risk)

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("lead","backend","frontend","database","test","security","devops","strategy")]
    [string]$Agent,
    
    [string]$Task = "",
    
    [switch]$Force  # Override model routing — uses session default
)

# Model routing table
$ModelMap = @{
    "lead"     = "opus"
    "backend"  = "sonnet"
    "frontend" = "sonnet"
    "database" = "sonnet"
    "test"     = "haiku"
    "security" = "opus"
    "devops"   = "haiku"
    "strategy" = "sonnet"
}

$model = $ModelMap[$Agent]

Write-Host ""
Write-Host "JeffLocal Agent Launcher" -ForegroundColor Cyan
Write-Host "  Agent : $Agent" -ForegroundColor White
Write-Host "  Model : $model" -ForegroundColor $(if ($model -eq "opus") {"Red"} elseif ($model -eq "sonnet") {"Yellow"} else {"Green"})
Write-Host ""

Set-Location "C:\JeffLocal"

if ($Force) {
    Write-Host "  [--force] Using session default model" -ForegroundColor Gray
    if ($Task) {
        claude --agent $Agent -p $Task
    } else {
        claude --agent $Agent
    }
} else {
    if ($Task) {
        claude --agent $Agent --model $model -p $Task
    } else {
        claude --agent $Agent --model $model
    }
}

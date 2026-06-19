<#
.SYNOPSIS
    Post-deploy smoke test for JeffLocal.
.DESCRIPTION
    Checks that all critical services are up and the dashboard health endpoint
    returns 200. Exits 0 on pass, 1 on fail.
#>

$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
function Log($msg) { Write-Host "[$Timestamp] $msg" }

$Failures = 0

function Check($Label, $Test) {
    if (& $Test) {
        Log "PASS $Label"
    } else {
        Log "FAIL $Label"
        $script:Failures++
    }
}

Log "=== SMOKE TEST START ==="

# 1. Dashboard responding
Check "Dashboard :8765 /health" {
    $r = try { Invoke-WebRequest "http://localhost:8765/health" -UseBasicParsing -TimeoutSec 10 } catch { $null }
    $r -and $r.StatusCode -eq 200
}

# 2. Dashboard main page returns 200 or redirect
Check "Dashboard :8765 / (redirect or 200)" {
    $r = try { Invoke-WebRequest "http://localhost:8765/" -UseBasicParsing -TimeoutSec 10 -MaximumRedirection 0 } catch { $null }
    $r -and ($r.StatusCode -in 200, 302, 303)
}

# 3. n8n responding
Check "n8n :5678" {
    $r = try { Invoke-WebRequest "http://localhost:5678/healthz" -UseBasicParsing -TimeoutSec 5 } catch { $null }
    $r -and $r.StatusCode -eq 200
}

# 4. Ollama responding
Check "Ollama :11434" {
    $r = try { Invoke-WebRequest "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 5 } catch { $null }
    $r -and $r.StatusCode -eq 200
}

# 5. Database file exists and is non-empty
Check "SQLite database file" {
    $db = "C:\JeffLocal\dashboard\data\dashboard.sqlite"
    (Test-Path $db) -and (Get-Item $db).Length -gt 0
}

# 6. Config files present
Check "Config files (all 4)" {
    ("C:\JeffLocal\config\model_settings.json",
     "C:\JeffLocal\config\pathways.json",
     "C:\JeffLocal\config\routing_rules.json",
     "C:\JeffLocal\config\model_monitoring.json") | ForEach-Object { Test-Path $_ } | Where-Object { -not $_ } | Measure-Object | Select-Object -ExpandProperty Count | ForEach-Object { $_ -eq 0 }
}

Log "=== SMOKE TEST DONE === Failures: $Failures"
exit $Failures

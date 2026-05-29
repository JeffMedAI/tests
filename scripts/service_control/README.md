# JeffLocal Service Watchdog

Continuous watchdog for all production and sandbox services.

## Services monitored

| Service | Port | Health check | Auto-restart |
|---|---|---|---|
| Production Dashboard | 8765 | `/api/health` HTTP | Yes |
| Sandbox Dashboard | 5000 | `/api/health` HTTP | Yes |
| n8n | 5678 | `/healthz` HTTP | Yes |
| Ollama | 11434 | `/api/tags` HTTP | Yes |
| Cloudflare Tunnel | — | `cloudflared` process | Yes |

## How it works

- Checks all services every 60 seconds (continuous loop)
- On failure: logs WARN, sends WhatsApp alert, attempts restart
- Restart cap: **3 restarts per service per hour** — prevents restart loops
- After cap hit: logs CRITICAL, sends second WhatsApp alert, stops retrying until next hour
- Log file: `C:\JeffLocal\logs\service_control\watchdog.log` (rotates at 5 MB)
- Restart state: `C:\JeffLocal\logs\service_control\restart_state.json`

## Scheduled Task

Registered as `\JeffLocal\JeffLocal - Service Watchdog` — runs at system startup, runs indefinitely.

To register (run once as Administrator):
```powershell
C:\JeffLocal\scripts\register_scheduled_tasks.ps1
```

To start immediately without rebooting:
```powershell
Start-ScheduledTask -TaskPath "\JeffLocal\" -TaskName "JeffLocal - Service Watchdog"
```

To check status:
```powershell
Get-ScheduledTask -TaskPath "\JeffLocal\" | Select TaskName, State
```

## Manual run modes

```powershell
# Single check pass (debug):
.\watchdog.ps1 -Once

# Force-restart all services:
.\watchdog.ps1 -Once -Force

# Continuous loop with custom interval:
.\watchdog.ps1 -IntervalSeconds 30
```

## Adding a new service

Add a new `[PSCustomObject]` entry to the `$Services` array in `watchdog.ps1`:

```powershell
[PSCustomObject]@{
    Name    = "MyService"         # Unique key (no spaces) for restart state tracking
    Label   = "My Service (port)" # Human-readable label for logs and alerts
    Test    = {
        # Return $true if healthy, $false if down
        return (Test-Http "http://localhost:XXXX/health")
    }
    Restart = {
        # Commands to restart the service
        # Return $true if recovered, $false if still down
        Start-Process -FilePath "myservice.exe" -WindowStyle Hidden
        Start-Sleep -Seconds 10
        return (Test-Http "http://localhost:XXXX/health")
    }
}
```

## Reading the log

```
2026-05-29 08:00:01 [INFO]  --- check pass ---
2026-05-29 08:00:01 [INFO]  Production Dashboard (8765) OK
2026-05-29 08:00:02 [WARN]  n8n (5678) DOWN
2026-05-29 08:00:02 [ALERT] WhatsApp alert sent: ALERT: n8n (5678) went DOWN...
2026-05-29 08:00:27 [INFO]  n8n (5678) recovered OK
```

Levels: INFO (normal), WARN (service down / restart attempt), ALERT (WhatsApp sent), ERROR (restart failed / cap hit).

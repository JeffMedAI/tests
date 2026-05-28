# Deploying to a New Practice

This dashboard is practice-configurable. All practice-specific settings are controlled by environment variables loaded from `.env.sandbox`. No code changes are needed to deploy for a new practice.

---

## Steps

### 1. Copy this folder to the new practice's server
```
Copy the entire sandbox/dashboard/ folder to the target server.
Example destination: C:\JeffLocal\dashboard\ on the new practice's machine.
```

### 2. Update `.env.sandbox` with the new practice's details
```env
ENVIRONMENT=production          # Change to 'production' to hide sandbox banner
PRACTICE_NAME=Riverside Surgery
PRACTICE_SHORT_CODE=RS
PRACTICE_ACCENT=#00703C         # Practice brand colour (hex)
PORT=8765                       # Or whatever port the practice uses
```

### 3. Set up the practice's database
The dashboard will create a fresh `data/dashboard.sqlite` on first run.
To migrate data from an existing instance, copy the `.sqlite` file and set:
```env
DB_PATH=C:\PracticeName\data\dashboard.sqlite
```

### 4. Configure practice pathways and routing
Copy and update config files for the practice:
- `config/pathways.json` — enable/disable pathways per practice
- `config/routing_rules.json` — update staff groups and queues
- `config/model_settings.json` — Ollama endpoint if different
- `config/model_monitoring.json` — adjust confidence thresholds if needed

### 5. Launch
```powershell
cd C:\<practice-folder>\dashboard
.\launch_sandbox.ps1
```

---

## What Changes Per Practice

| Setting | How to change |
|---------|--------------|
| Practice name | `PRACTICE_NAME` in `.env.sandbox` |
| Brand initials (topbar) | `PRACTICE_SHORT_CODE` in `.env.sandbox` |
| Brand colour | `PRACTICE_ACCENT` in `.env.sandbox` |
| Sandbox banner on/off | `ENVIRONMENT=sandbox` (on) or `ENVIRONMENT=production` (off) |
| Database location | `DB_PATH` in `.env.sandbox` |
| Port | `PORT` in `.env.sandbox` |
| Active pathways | `config/pathways.json` |
| Routing rules | `config/routing_rules.json` |
| Model settings | `config/model_settings.json` |

---

## What Does NOT Change Per Practice

- Application code (`app/`)
- Templates (`templates/`) — except via template variables already in place
- Core pipeline scripts (`../../app/`) — shared across all instances

---

## Environment Values

| `ENVIRONMENT` | Effect |
|--------------|--------|
| `sandbox` | Orange sandbox banner shown on every page |
| `production` | Banner hidden — looks like a live production system |

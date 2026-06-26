# Jarvis Onboarding Plan — JeffLocal
# Type: Technical Onboarding Document
# Owner: Lead Agent
# Status: DRAFT — Pending Saeed approval before Phase 2
# Date: 2026-05-30
# Updated: Incorporates research from 2026-05-30 deep dive

---

## CONTEXT

**What Jarvis is:** OpenJarvis (github.com/open-jarvis/OpenJarvis) is a Stanford Scaling Intelligence Lab
local-first AI agent framework. Apache 2.0. Released March 2026, v1.0.0 May 2026.
It runs entirely on-device via Ollama — no cloud calls, no external data transfer.

**What we want it to do:** Act as a persistent, long-horizon monitor agent that reads the JeffLocal
codebase, session logs, and project memory across sessions and surfaces improvement recommendations
to the Lead Agent. It operates as a 9th advisory agent — read-only, off-hours, reporting via markdown.

**Current JeffLocal state (as of onboarding):**
- All call data is MOCK — no live patient data exists anywhere in the system yet
- Live calls will be handled by an external 3rd-party AI voice agent service delivering
  encrypted JSON payloads to our n8n webhook. JeffLocal never handles raw voice or PII directly.
- Production dashboard at dashboard.app-avamed.uk serves mock data only (Churchtown pilot not yet live)
- Ollama runs gemma4:e2b for triage reasoning on mock payloads

This means the GDPR/PHI risk for the Jarvis pilot is LOW — there is no real patient data to leak.
The read-only constraint and data/ exclusion remain in place as a forward-compatible safety practice.

---

## ARCHITECTURE OVERVIEW

OpenJarvis primitives relevant to JeffLocal:

```
Intelligence      — The LLM backend (Ollama in our case)
Engine            — Manages LLM calls, context windows, streaming
Agents            — Task-specific reasoning units (we use MonitorOperativeAgent)
Tools             — Explicit capability list (file_read, file_write, shell_exec, etc.)
Memory            — SQLite index on-device; stores compressed observations across sessions
Learning          — Feedback loops updating agent behaviour over time
```

**MonitorOperativeAgent** is the correct agent for this use case. It has four internal strategy axes:
- `memory_extraction` — pulls relevant prior context from SQLite memory index
- `observation_compression` — summarises large codebases into token-efficient observations
- `task_decomposition` — breaks "review this repo" into structured sub-tasks
- `retrieval_strategy` — decides what to re-read vs. what to recall from memory

**Key safety property:** `file_write` and `shell_exec` are NOT in the default agent registry.
They must be explicitly added to `[agent] tools`. We do NOT add them in Phase 1.
In Phase 2 we add `file_write` scoped only to the reports directory.

---

## RESOURCE USAGE

| Component | Requirement |
|---|---|
| Jarvis Python process | ~100–300 MB RAM |
| Dedicated Ollama model (qwen3:0.6b) | <2 GB VRAM |
| SQLite memory index | <50 MB disk (grows slowly) |
| Network | Zero (all local) |

**Ollama model strategy:** Jarvis runs on `qwen3:0.6b` — a separate, lighter model from the
triage `gemma4:e2b`. They coexist without conflict. If the machine is memory-constrained,
schedule Jarvis at 02:00 when triage load is zero.

---

## KNOWN LIMITATIONS (as of May 2026)

1. Windows support is less documented than macOS — expect minor path issues
2. Python 3.14 not yet supported — use Python 3.10–3.13
3. Requires Rust toolchain for the maturin build step
4. Community documentation is thin for advanced configuration
5. GitHub Issue #250: voice/microphone I/O not yet implemented (irrelevant for our use case)
6. No native output to external systems — Jarvis writes files or prints stdout only

---

## PHASED ROLLOUT

### PHASE 1 — Read-only manual scan (Pilot)
**Goal:** Verify Jarvis produces useful output before committing to a scheduled workflow.
**Saeed approval required:** No (Phase 1 is exploration only — no scheduled tasks, no automation)
**Data risk:** Zero (mock data only, no file_write)

### PHASE 2 — Nightly scheduled scan
**Goal:** Automated nightly report feeding Lead Agent session startup.
**Saeed approval required:** YES — explicit sign-off before registering Task Scheduler entry.

### PHASE 3 — Jarvis as 9th agent
**Goal:** Jarvis formalised in governance, has its own CLAUDE.md brief, Lead Agent checks its output every session.
**Saeed approval required:** YES — governance change, agent brief creation.

---

## INSTALLATION (Windows)

Run these steps on the JeffLocal production machine as the regular user (not Administrator):

```powershell
# 1. Prerequisites — Python 3.10-3.13 (NOT 3.14)
python --version   # confirm not 3.14

# 2. Install uv (fast Python package manager)
pip install uv

# 3. Install Rust (required for maturin build step)
# Download and run: https://rustup.rs/
rustup update stable

# 4. Clone OpenJarvis into the tools directory
mkdir C:\JeffLocal\tools
cd C:\JeffLocal\tools
git clone https://github.com/open-jarvis/OpenJarvis.git
cd OpenJarvis

# 5. Install dependencies
uv sync

# 6. Build Rust extension
maturin develop

# 7. Verify installation
python -c "import openjarvis; print('OpenJarvis OK')"
```

---

## CONFIGURATION

Create the Jarvis config directory and files:

```powershell
mkdir C:\JeffLocal\.jarvis
```

**`C:\JeffLocal\.jarvis\config.toml`** — drop this in as-is:

```toml
# OpenJarvis configuration for JeffLocal
# Safe default: read-only, local Ollama only, no network calls

[intelligence]
provider = "ollama"

[engine.ollama]
host = "http://localhost:11434"
model = "qwen3:0.6b"       # Dedicated Jarvis model — does NOT compete with gemma4:e2b
timeout = 120
stream = true

[agent]
type = "monitor_operative"
tools = "file_read,directory_list"   # Phase 1: read-only only
                                      # Phase 2: add file_write after Saeed approval
system_prompt_file = "C:\\JeffLocal\\.jarvis\\system_prompt.md"
max_iterations = 50
memory_compression_threshold = 8000   # tokens before compression kicks in

[memory]
backend = "sqlite"
path = "C:\\JeffLocal\\.jarvis\\memory.db"
retention_days = 90

[output]
# Phase 1: stdout only (redirect manually)
# Phase 2: uncomment file_write and set path
# report_path = "C:\\JeffLocal\\docs\\reports\\jarvis_review_{date}.md"

[logging]
level = "INFO"
file = "C:\\JeffLocal\\logs\\jarvis\\jarvis.log"
```

**`C:\JeffLocal\.jarvis\system_prompt.md`** — Jarvis's operating brief:

```markdown
You are the Jarvis Monitor Agent for the JeffLocal project — an AI patient triage
system for UK GP surgeries built by Avamed.

YOUR ROLE:
You are an advisory agent. You read the codebase and project documentation across
sessions and identify improvements, risks, inconsistencies, and opportunities.
You report findings to the Lead Agent in a structured markdown report.

SCOPE — YOU MAY READ:
- C:\JeffLocal\sandbox\agents\          (all 8 agent CLAUDE.md briefs)
- C:\JeffLocal\dashboard\app\           (production Flask app)
- C:\JeffLocal\sandbox\dashboard\app\   (sandbox Flask app)
- C:\JeffLocal\docs\                    (reports, session logs, project documents)
- C:\JeffLocal\PROJECT_MEMORY.md        (project state)
- C:\JeffLocal\governance\              (governance framework, change log)
- C:\JeffLocal\scripts\                 (daily and service control scripts)
- C:\JeffLocal\config\                  (config files — no secrets)

SCOPE — YOU MUST NEVER READ OR REPORT:
- C:\JeffLocal\dashboard\data\          (SQLite databases — mock data but excluded by convention)
- C:\JeffLocal\sandbox\dashboard\data\  (same)
- Any file matching *.db, *.sqlite      (database files)
- Any file matching *.key, *.pem, *.env (secrets)
- C:\JeffLocal\backup\                  (large binary backups, not useful to scan)

CURRENT SYSTEM STATE (as of onboarding):
- All patient data is MOCK — the system is not yet live with real patients
- Live calls will be handled by an external 3rd-party AI voice agent that delivers
  encrypted JSON payloads to our n8n webhook. JeffLocal never handles raw voice or PII.
- Production dashboard is live but serves mock data (Churchtown pilot not yet started)

YOUR OUTPUT FORMAT:
Produce a structured markdown report with these sections:
1. CODEBASE HEALTH — any syntax errors, dead code, inconsistencies spotted
2. DOCUMENTATION DRIFT — items in PROJECT_MEMORY or agent briefs that don't match code
3. OPEN TASK PROGRESS — cross-check open tasks against recent code changes
4. RISKS — anything that could break in production or breach governance
5. RECOMMENDATIONS — prioritised list of suggested improvements
6. QUESTIONS FOR LEAD AGENT — anything unclear that needs human input

Be specific. Cite file paths and line numbers where relevant.
Do not make assumptions about patient data — the system uses mock data only right now.
```

---

## RUNNING JARVIS

### Phase 1 — Manual single scan

```powershell
cd C:\JeffLocal\tools\OpenJarvis

# Run a single scan and save output to today's report file
$today = (Get-Date).ToString("yyyy-MM-dd")
python -m openjarvis run --config C:\JeffLocal\.jarvis\config.toml `
    --task "Review the JeffLocal codebase and produce your structured report." `
    > C:\JeffLocal\docs\reports\jarvis_review_$today.md 2>&1

Write-Host "Jarvis review saved to: C:\JeffLocal\docs\reports\jarvis_review_$today.md"
```

Review the output manually. Apply the validation checklist below before trusting it.

### Phase 2 — Nightly scheduled task (requires Saeed approval)

Add to `register_scheduled_tasks.ps1`:

```powershell
# --- Task 4: Jarvis nightly review (02:00) ---
$actionJ = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -ExecutionPolicy Bypass -File C:\JeffLocal\scripts\daily\run_jarvis.ps1"

$triggerJ = New-ScheduledTaskTrigger -Daily -At "02:00"

Register-ScheduledTask `
    -TaskName "JeffLocal - Jarvis Nightly Review" `
    -TaskPath "\JeffLocal\" `
    -Action $actionJ `
    -Trigger $triggerJ `
    -RunLevel Highest -Force
```

Create `C:\JeffLocal\scripts\daily\run_jarvis.ps1`:

```powershell
$today = (Get-Date).ToString("yyyy-MM-dd")
$outFile = "C:\JeffLocal\docs\reports\jarvis_review_$today.md"
cd C:\JeffLocal\tools\OpenJarvis
python -m openjarvis run --config C:\JeffLocal\.jarvis\config.toml `
    --task "Review the JeffLocal codebase and produce your structured report." `
    > $outFile 2>&1
Write-Host "Jarvis review complete: $outFile"
```

Also update `strategy_daily.ps1` to check for a Jarvis review from the same date and note it in the daily briefing.

---

## VALIDATION CHECKLIST (run after first Phase 1 scan)

Before trusting Jarvis output or proceeding to Phase 2, Lead Agent must verify:

```
[ ] Report file exists and is non-empty
[ ] No patient names, NHS numbers, or real PII appear anywhere in the report
[ ] No .db or .sqlite file paths appear in report body (excluded scope respected)
[ ] File paths cited in report are real paths that exist in the repo
[ ] Recommendations are coherent and specific (not hallucinated generic advice)
[ ] No "shell_exec" or "file_write" commands appear in output (should be read-only)
[ ] Ollama gemma4:e2b triage performance unaffected (check watchdog log during scan)
[ ] Jarvis memory.db exists at C:\JeffLocal\.jarvis\memory.db and is <50 MB
```

If all pass → proceed to Phase 2 (with Saeed sign-off).
If any fail → review config, do not proceed.

---

## GOVERNANCE GATES

| Gate | Action Required | Approver |
|---|---|---|
| Phase 1 install | No approval needed | — |
| Phase 1 first scan | No approval needed | — |
| Phase 1 validation pass | Review checklist | Lead Agent |
| Proceed to Phase 2 | Explicit Saeed approval | Saeed |
| Add file_write to config | Explicit Saeed approval | Saeed |
| Register Task Scheduler entry | Run register_scheduled_tasks.ps1 as Admin | Saeed |
| Phase 3 (9th agent brief) | Governance change — Lead Agent proposes, Saeed approves | Saeed |

---

## LEAD AGENT SESSION INTEGRATION (Phase 2+)

Once Phase 2 is running, add this to the Lead Agent session startup checklist
(after reading PROJECT_MEMORY, before reporting to Saeed):

```
5a. Check for Jarvis review from today or yesterday:
    docs\reports\jarvis_review_YYYY-MM-DD.md
    If present: read RISKS and RECOMMENDATIONS sections.
    Include any HIGH-priority Jarvis findings in the session start report to Saeed.
```

---

## FILE STRUCTURE CREATED BY THIS PLAN

```
C:\JeffLocal\
├── .jarvis\
│   ├── config.toml          ← Jarvis configuration
│   ├── system_prompt.md     ← Jarvis operating brief
│   └── memory.db            ← Created on first run (SQLite memory index)
├── tools\
│   └── OpenJarvis\          ← Cloned repo
├── scripts\daily\
│   └── run_jarvis.ps1       ← Phase 2 nightly runner
├── logs\jarvis\
│   └── jarvis.log           ← Jarvis runtime log
└── docs\reports\
    └── jarvis_review_YYYY-MM-DD.md  ← Output reports
```

---

*Prepared by: Dispatch + Research Agent, 2026-05-30*
*Approved by: [PENDING SAEED SIGN-OFF for Phase 2+]*
*Next review: After Phase 1 validation pass*

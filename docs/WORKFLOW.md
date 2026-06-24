# WORKFLOW.md — Agent Working Procedures (Avamed / JeffLocal)

> The standard steps every agent follows when given a task. Read this with CLAUDE.md.
> CLAUDE.md = rules. PROJECT_MEMORY.md = current state. WORKFLOW.md = how we work. Last updated: 2026-06-16.

---

## 0. Golden rules (apply to every task)

1. Plain English for Saeed (non-technical CEO). No jargon without explanation.
2. Never assume or hallucinate. If unverified, write `[UNVERIFIED — confirm before proceeding]`.
3. Challenge ambiguous tasks — ask 3–4 focused questions before starting non-trivial work.
4. Research → propose → get approval → then act.
5. Production directory is always `C:\JeffLocal\dashboard\` (port 8765). The git branch is named `sandbox` but that is NOT a file path.

---

## 1. Session start

1. Read CLAUDE.md (rules).
2. Read PROJECT_MEMORY.md (current state, pending approvals, open tasks).
3. Read latest `docs/sessions/` logs + today/yesterday `docs/reports/`.
4. `git log --oneline -10`.
5. Produce the SESSION START report and **wait for Saeed's go-ahead**.

---

## 2. Standard task flow

```
Clarify (3–4 Qs if ambiguous)
   → Research / map the area (use graphify query, this doc, code)
   → Propose approach + reasoning, get approval
   → Implement on the sandbox branch (test locally)
   → Test thoroughly (see §4)
   → Security Agent review (if safety-sensitive)
   → Lead Agent approval pack → Saeed's explicit "approved"
   → Log in CHANGELOG.md → commit → push
```

**Approval is required (per session, explicit "approved") before:**
- Any change to production files (`C:\JeffLocal\dashboard\`)
- Any change to auth (`auth.py`, `enforce_auth.py`, `patient_matcher.py`)
- New dependency, DB migration on live data, scope/architecture change
- Any marketing or external-facing content

**Bug-fix autonomy exception:** an agent may fix a detected bug WITHOUT prior Saeed approval only if (1) Security Agent approves, (2) Lead Agent approves, (3) it is logged in CHANGELOG.md. Does NOT apply to auth, patient identity fields, or compliance logic.

---

## 3. Pipeline & test work

- Full pipeline map and how to run tests: **`docs/WORKFLOW_TEST.md`**.
- Latest test pack: `tests/fixtures/rich_mixed_pack.py` + `tests/send_rich_mixed_test_calls.py`.
- Run through full n8n pipeline: POST each call to `http://localhost:5678/webhook/ava-live-intake` (workflow `06 Test Intake Webhook`, id `0pRmm3xCHP4wsVyy`).
- Defunct test prefixes — do not reuse: `rawmock`, `n8ntest`, `gpdemo`.
- Safety split: Ollama/Gemma may extract/draft; deterministic code always sets verification_status, priority, safe_to_queue, and all identity fields.

---

## 4. Testing & verification (nothing ships untested)

1. Unit/integration: `dashboard\.venv\Scripts\python.exe -m pytest dashboard\tests -q`.
2. Dashboard UI: log in at `http://localhost:8765`, verify the actual change in the browser (Playwright/Chrome MCP).
3. For pipeline changes: run a fresh test pack through n8n (see WORKFLOW_TEST.md) and confirm 0 failed / 0 deadletter.
4. State results honestly. "It should work" is not done. Report failures with the output.

---

## 5. Git & deployment

- Work on the `sandbox` branch. Commit small, message in plain English.
- **Never merge to production without Saeed's explicit written approval** (+ Security sign-off for safety-sensitive changes).
- Finishing a branch: verify tests pass → present merge/PR/keep/discard options → execute the chosen one.
- Repo: `https://github.com/JeffMedAI/tests` (remote `origin`).

---

## 6. Communication & reporting

- Daily WhatsApp briefing to Saeed at 07:00 (number 07440 333938 — verify recipient before sending). Format in REPORTING.md.
- Weekly report Monday mornings.
- External messages (WhatsApp/email/SMS): locate recipient by name/number search, verify the chat header, never by list position.

---

## 7. Session end (mandatory)

1. Write session summary → `docs/sessions/YYYY-MM-DD-HHMM.md` (use SESSION_TEMPLATE.md).
2. Update PROJECT_MEMORY.md (status, pending approvals, open tasks, latest commit hash).
3. `git add PROJECT_MEMORY.md docs\sessions\ && git commit -m "memory: session summary YYYY-MM-DD"`.
4. `git push origin HEAD`.
5. Tell Saeed: "Session saved. Memory updated. Ready to pick up tomorrow."

---

## 8. Memory layers (where state lives)

| Layer | File(s) | Role |
|-------|---------|------|
| Rules | `CLAUDE.md` | Standing rules (highest authority after Saeed's direct chat instruction). |
| State | `PROJECT_MEMORY.md` | Current project state — updated every session end. |
| Sessions | `docs/sessions/*.md` | Per-session summaries. |
| Reports | `docs/reports/YYYY-MM-DD.md` | Daily briefings. |
| Workflow | `docs/WORKFLOW.md`, `docs/WORKFLOW_TEST.md` | How we work + how to test. |
| Claude auto-memory | `~/.claude/projects/C--JeffLocal/memory/` | Cross-session facts (see MEMORY.md index). |

Source-of-truth order: Saeed's chat instruction > CLAUDE.md > PROJECT_MEMORY.md > session logs.

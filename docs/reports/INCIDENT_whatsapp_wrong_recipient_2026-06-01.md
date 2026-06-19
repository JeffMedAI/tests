# INCIDENT REPORT — WHATSAPP WRONG RECIPIENT
**Incident ID:** INC-2026-06-01-WHATSAPP  
**Date:** 2026-06-01  
**Time:** ~07:07–07:10 AM  
**Severity:** LOW — Internal Process Failure (no patient data, contained within minutes)  
**Status:** CLOSED — Corrective actions applied  
**Reported by:** Dispatch (Claude)  
**Reviewed by:** Lead Agent + Security Agent  
**Classification:** Internal Process Failure (NOT a reportable data breach — see Security Review)

---

## 1. WHAT HAPPENED

At approximately 07:07 AM on 2026-06-01, the Dispatch agent (Claude, acting as daily briefing sender) transmitted internal JeffLocal project status update messages to a personal WhatsApp group named **"Pics!"** instead of the intended recipient **"Saeed Alam (You)"** (WhatsApp saved messages / self-chat).

The messages contained internal project status information: task queue summaries, agent status, and development notes. **No patient data, no clinical data, no credentials, and no NHS information was included.**

Saeed identified the misdirected messages and deleted them from the "Pics!" group shortly after discovery (~07:10 AM, within minutes of sending).

---

## 2. TIMELINE

| Time | Event |
|------|-------|
| ~07:00 AM | strategy_daily.ps1 executes, generates daily briefing report |
| ~07:07 AM | Dispatch opens WhatsApp Web to send briefing |
| ~07:07 AM | Dispatch selects chat by coordinate click — lands on "Pics!" group |
| ~07:07–07:08 AM | Internal project briefing messages sent to "Pics!" group |
| ~07:08 AM | Dispatch session ends, no verification performed |
| ~07:10 AM | Saeed discovers misdirected messages |
| ~07:10 AM | Saeed deletes messages from "Pics!" group |
| ~07:15 AM | Incident reported; investigation initiated |
| 2026-06-01 | Lead Agent investigation and corrective actions completed |

---

## 3. ROOT CAUSE ANALYSIS

**Primary cause:** Dispatch used a hard-coded screen coordinate `(291, 219)` to click the intended chat in the WhatsApp Web chat list, based on a prior session's screenshot where "Saeed Alam (You)" was at that position.

**Contributing factors:**

1. **No search-by-name navigation.** The correct method (type name in search bar → select verified result) was not used. Coordinates are brittle — chat list order changes as new messages arrive.

2. **No pre-send recipient verification.** Dispatch did not read the chat header to confirm the correct recipient was selected before typing or sending.

3. **No abort condition.** The send script lacked a verification gate that would abort if the expected recipient name was not confirmed in the chat header.

4. **Coordinate-based UI navigation is inherently fragile.** Chat list positions shift whenever any chat receives a new message. A coordinate that worked in a prior session is not reliable in a new session.

**Root cause chain:**
```
Chat list reordered between sessions
  → Coordinate (291, 219) now points to "Pics!" not "Saeed Alam (You)"
    → No search step to find correct chat by name
      → No header verification before send
        → Messages sent to wrong recipient
```

---

## 4. IMPACT ASSESSMENT

| Factor | Assessment |
|--------|-----------|
| Data type exposed | Internal project status notes (task queue, agent status, dev notes) |
| Patient data involved | **NO** — all data is mock/dev; no real patients |
| Credentials/secrets exposed | **NO** |
| Clinical data exposed | **NO** |
| NHS data exposed | **NO** |
| Recipient | Members of Saeed's personal "Pics!" WhatsApp group — personal contacts, not external adversaries or business competitors |
| Duration of exposure | ~2–3 minutes (deleted by Saeed promptly) |
| Persistence | Messages deleted; no screenshot or download evidence |
| Regulatory exposure | Minimal — see Security Review for full GDPR assessment |
| Business impact | Nil — no external disclosure, no reputational harm |
| Repeat risk | Addressed by corrective actions below |

---

## 5. RESPONSIBLE PARTY

**Dispatch (Claude agent)** acting as daily briefing sender.  
The error was caused by a fragile navigation method (coordinate clicks) that was never hardened against chat list reordering. No human was at fault. This is a process/tooling failure.

---

## 6. CORRECTIVE ACTIONS TAKEN

### Immediate (applied 2026-06-01)

1. **send_whatsapp.py updated** — Script now uses search-by-name to locate the correct chat, reads the chat header, and aborts with an error log if the expected recipient is not confirmed. Coordinate-based navigation removed.

2. **backend_CLAUDE.md updated** — Hard rule added: "NEVER use coordinate clicks to select a WhatsApp chat recipient. ALWAYS use search-by-name. ALWAYS verify the chat header before sending."

3. **GOVERNANCE_FRAMEWORK.md updated** — New rule under Agent Communication Protocols: agents must verify recipient identity before sending any message via external channels.

4. **This incident report written** and filed.

5. **Security review conducted** and filed at `docs/compliance/security_review_whatsapp_incident_2026-06-01.md`.

6. **CHANGE_LOG.md updated** with incident entry.

7. **PROJECT_MEMORY.md updated** — Coordinate-based WhatsApp navigation listed as prohibited under Known Process Rules.

### Preventive (ongoing)

- All future WhatsApp automation must use the search-verified navigation pattern (see updated send_whatsapp.py).
- Any new agent briefed via backend_CLAUDE.md or equivalent will see the hard rule before writing any WhatsApp automation code.
- Security Agent to include "recipient verification" check in all future reviews of messaging scripts.

---

## 7. LESSONS LEARNED

1. **Coordinate-based UI automation is not safe for any action with external side effects.** Search-by-name or DOM-based navigation must be used for any messaging action.

2. **Verification gates should be non-optional for external communications.** A confirmation step (read the chat header) adds 1–2 seconds and prevents this class of error entirely.

3. **Prior session screenshots must never be trusted for coordinate positions.** Chat list order, window size, and UI state change between sessions.

---

## 8. RELATED DOCUMENTS

- Security Review: `docs/compliance/security_review_whatsapp_incident_2026-06-01.md`
- Prior breach (for process comparison): `docs/reports/breach_report_2026-05-29.md`
- Updated script: `scripts/daily/send_whatsapp.py`
- Governance rule: `governance/GOVERNANCE_FRAMEWORK.md` — Agent Communication Protocols

---

*Incident closed. No further action required beyond items listed in Section 6.*  
*Lead Agent — 2026-06-01*

# HANDOFF — Avamed (JeffLocal)

> **What this file is:** the single, always-current handoff note for the project.
> It holds **only the most recent session's** handoff — not a history.
> Read it at session start, right after PROJECT_MEMORY.md (see SESSION START PROTOCOL).
> Rewrite it in full at session end (SESSION END PROTOCOL step 2). If it disagrees with
> PROJECT_MEMORY.md on *state*, PROJECT_MEMORY.md wins; this file is the plain-English
> "where we left off" story so the next agent knows what to repeat and what to avoid.
>
> **Rolling latest-only:** overwrite the whole file each close. Do NOT append. Keep it short.

---

**Last session:** — (SEED — not yet written from a real session; overwrite at next close)
**Closed by:** —
**Last commit:** run `git log --oneline -1`
**Production:** dashboard.app-avamed.uk (Cloudflare tunnel → localhost:8765), watchdog-managed, LIVE

---

## WORK SCOPE (what this session set out to do)

_Awaiting first real handoff. At the next session close, replace this with what the session
set out to do._

## WHAT WORKED / WHAT DIDN'T

_Awaiting first real handoff. Record the wins and the dead-ends here so the next agent does
not repeat mistakes. Do not drop the "didn't" side — it is the point of this file._

Durable gotchas already known (keep these until proven otherwise):
- PRODUCTION is always `C:\JeffLocal\dashboard\` (port 8765). The git branch is named "sandbox"
  but the branch name is NOT a file path — always verify the real path before editing.
- LLM output must NEVER set verification_status, safe_to_queue, priority, or any patient-identity
  field — those are deterministic-code-only. Any drift is a critical STOP; escalate to Saeed.
- 5 items sit in the deadletter queue; no replay tooling exists yet (known tech debt).

## HOW THE SESSION CLOSED

_Awaiting first real handoff. Record: commit hash, push, restore tag created, memory + session
log written, any deploy/watchdog state._

## NEXT + BLOCKERS

**Next actions:** _pull the top 2–3 from PROJECT_MEMORY.md open tasks at next close._

**Blockers:** _list, or "None"._

**Pending Saeed:** _items needing his explicit approval, or "None"._

Durable context (until it changes):
- Pilot site (Churchtown Medical Centre, Southport) NOT yet live with real patients; governance
  gates 1–7 unsigned. Do not assume the pilot is active.
- NHS SBS Framework (SBS10523) and DSPT (deadline 30 June 2026) are live commercial obligations —
  check current date against deadlines when planning strategy tasks.

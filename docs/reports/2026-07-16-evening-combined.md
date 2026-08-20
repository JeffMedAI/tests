COMBINED EVENING BRIEF (session close) â€” 2026-07-16 19:00
Both projects â€” Avamed AI triage + St Marks Pharmacy website
================================================================

=== AVAMED / JEFFLOCAL ===
  WHAT WE DID TODAY
  - Fixed `restart_all.ps1` — it was passing `-DashOnly`/`-N8nOnly` straight through to `watchdog.ps1`, which doesn't accept them, so it crashed with a "parameter cannot be found" error. Now restarts each service directly using the same launcher scripts watchdog itself uses (`_launch_dashboard.ps1` / `_launch_n8n.ps1`), and the full-restart path passes `-Once` to watchdog so it no longer hangs in an infinite loop when called with no switches. (commit 6a4e59f)
  - This closes open task #1 from PROJECT_MEMORY (found broken in this morning's 09:50 session close, fixed this afternoon).
  - Earlier today (09:50 close, already logged separately): Item #2 refactor tested end-to-end, 3 bugs fixed, merged to main, production redeployed and verified.

  WHAT IS NEXT (tomorrow)
  - ~~Fix restart_all.ps1~~ — DONE this session (6a4e59f)
  - Run Playwright e2e suite directly against :8765 (proven equivalent on isolated instance already)
  - Reduce router→main.py coupling (107 back-refs, Fable 5 finding, real Item #2 follow-up)
  - Run the Playwright e2e suite directly against production (:8765) to confirm the 5 previously-failing tests pass live.

  BLOCKERS
  - None.

  NEEDS YOUR OK
  - [ ] Real staff accounts — provide names, roles, emails to unblock pilot go-live
  - [ ] Governance gates 1-7 sign-off — cannot be delegated
  - [ ] JEFF_WEBHOOK_SECRET — set in environment before any live Jeff traffic
  - [ ] n8n API key rotation — confirmed "later"
  (From PROJECT_MEMORY: 3. LLM identity fields blocked from patient matching pipeline -- DONE; ### Pending Saeed approvals / actions;  6   | Remove legacy static-salt password fallback       | Backend  | PENDING (already done in auth.py — verify before removing))

GIT (JeffLocal): b53847a Merge fix/importer-reimport-loop into main | 737f664 fix: escape call_id in glob (Security N1) | f937795 fix: Security Agent F1/F2 ÔÇö atomic retire, pipeline dup guard, docs

----------------------------------------------------------------

=== ST MARKS PHARMACY (STMARKS-WEB) ===
  WHAT WE DID TODAY
  - No session log in last 24h.

  WHAT IS NEXT (tomorrow)
  - Nothing queued.

  BLOCKERS
  - None.

  NEEDS YOUR OK
  - None.

GIT (St Marks): 3ee891d draft: disclose Avamed as processor in privacy policy | 476270f fix: correct HANDOFF.md ÔÇö booking-forward feature is done, not pending | f9209d9 feat: forward booking submissions to Avamed JeffLocal dashboard

================================================================
Detail: C:\JeffLocal\PROJECT_MEMORY.md | C:\JeffLocal\SMCPHARMA\CLAUDE.md

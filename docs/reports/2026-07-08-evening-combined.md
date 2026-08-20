COMBINED EVENING BRIEF (session close) â€” 2026-07-08 19:00
Both projects â€” Avamed AI triage + St Marks Pharmacy website
================================================================

=== AVAMED / JEFFLOCAL ===
  WHAT WE DID TODAY
  - Diagnosed root cause of all n8n execution failures: auth middleware returning 302 HTML redirect on unprotected endpoints
  - Fixed 4 URLs across dashboard and n8n workflows — renamed to `/api/n8n/` prefix (already in public allowlist)
  - `GET /api/red-flags` → `/api/n8n/red-flags` (main.py line 2497)
  - `GET /api/overdue` → `/api/n8n/overdue` (main.py line 2520)
  - `POST /api/alerts/log` → `/api/n8n/alerts/log` (main.py line 3390)
  - All 3 n8n workflow HTTP nodes updated via Python script (fix_n8n_auth_urls.py)

  WHAT IS NEXT (tomorrow)
  - Confirm WF04 (Overdue Scan) also succeeds on next scheduled run (09:00 UTC)
  - Remove legacy static-salt password fallback (Backend Task #1 — still pending)
  - Saeed to provide real staff account details — blocks pilot go-live
  - Governance gates 1-7 sign-off

  BLOCKERS
  - No real staff accounts (Saeed must provide)
  - Governance gates 1-7 unsigned
  - JEFF_WEBHOOK_SECRET not set

  NEEDS YOUR OK
  - [ ] Staff account details (names, roles, emails)
  - [ ] Governance gates 1-7 sign-off
  - [ ] JEFF_WEBHOOK_SECRET in Windows environment variables
  - [ ] n8n API key rotation (confirmed "later")
  - [ ] Real staff accounts — provide names, roles, emails to unblock pilot go-live
  - [ ] Governance gates 1-7 sign-off — cannot be delegated
  - [ ] JEFF_WEBHOOK_SECRET — set in environment before any live Jeff traffic
  - [ ] n8n API key rotation — confirmed "later"
  (From PROJECT_MEMORY: 3. LLM identity fields blocked from patient matching pipeline -- DONE; ### Pending Saeed approvals / actions;  1   | Remove legacy static-salt password fallback       | Backend  | PENDING (NOTE: already done in auth.py — verify before removing from list);  5   | Split main.py into modules (refactor/split-main-py branch) | Backend | PENDING — plan written, not started)

GIT (JeffLocal): 7cc846c feat: items #5 and #6 ÔÇö observability module and AI safety boundary (TDD) | 01c73e1 memory: session update 2026-07-08 ÔÇö tasks 1+2 complete, task 3 pending | a168af8 feat: SQLite hot backup ÔÇö TDD tests, script, Task Scheduler entry

----------------------------------------------------------------

=== ST MARKS PHARMACY (STMARKS-WEB) ===
  (No log today - using 2026-07-03-1135.md, 127h ago)

  WHAT WE DID TODAY
  - Site now LIVE on real domain. Added custom domains stmarkspharmacy.co.uk + www to the Cloudflare Worker. HTTPS good.
  - Full end-to-end test on live domain. All 33 pages 200. Zero broken links. No console errors. Mobile-responsive confirmed.
  - Booking form works end-to-end on live domain: POST /api/book -> 200, email Delivered to stmarkssouthport@gmail.com (Resend log, marker QK47).
  - Found + fixed the one real defect: /privacy-policy/, /terms/, /cookies/ were 404 on every footer. Built all three, live now.
  - Privacy policy names Resend + Cloudflare as processors (UK GDPR). Cookie policy = essential-only, no tracking. All 3 marked draft.
  - Fixed stale footer year 2024 -> 2026 site-wide (30 pages + generator).

  WHAT IS NEXT (tomorrow)
  - Saeed: give WhatsApp Business number (button is a dead placeholder link now).
  - Pharmacist: proof-read clinical pages (GPhC sign-off) + give SP GPhC number for footer.
  - Pharmacist/DPO: review the 3 draft legal pages + add ICO registration number.
  - Add cookie consent banner ONLY when GA4/analytics goes on.

  BLOCKERS
  - None technical. Remaining items are human sign-offs (pharmacist, WhatsApp number) — cannot be done in code.

  NEEDS YOUR OK
  - [ ] WhatsApp Business number.
  - [ ] Approve pharmacist review loop for clinical + legal pages before promoting to patients.
  - [ ] Decide: keep static build (recommended — fast, live, cheap) vs migrate to WordPress.

GIT (St Marks): ab25612 session: 2026-07-03 ÔÇö live on stmarkspharmacy.co.uk, full e2e test, legal pages | e563c41 feat: add privacy/terms/cookie pages, fix footer year, live on real domain | 1af65e3 feat: set booking email sender to verified send.stmarkspharmacy.co.uk

================================================================
Detail: C:\JeffLocal\PROJECT_MEMORY.md | C:\JeffLocal\SMCPHARMA\CLAUDE.md

COMBINED EVENING BRIEF (session close) â€” 2026-07-14 19:00
Both projects â€” Avamed AI triage + St Marks Pharmacy website
================================================================

=== AVAMED / JEFFLOCAL ===
  WHAT WE DID TODAY
  - Resumed mid-session after context compact (pages.py was done, cases.py was pending)
  - Extracted 10 case management routes into `app/routers/cases.py` (TDD, commit abc48e0)
  - batch-resolve, bulk-action, recording, copy-audit, action, enrich, api_case_get, case_detail, update_case, quick_action
  - Added `/api/n8n/test-intake-batch` route + 10 helper functions to `routers/n8n.py` (commit 7fc1030)
  - Helpers prefixed `_` to signal internal use
  - Fixed monkeypatches in test_api_endpoints.py to target n8n_router_module

  WHAT IS NEXT (tomorrow)
  - Merge `feature/refactor-2-5-6` → main (requires Saeed explicit approval)
  - Continue Item #3 through #10 of the architectural improvements
  - Staff accounts still needed for pilot (Saeed to provide names, roles, emails)
  - Remove legacy static-salt password fallback — Backend — PENDING (NOTE: already done in auth.py — verify before removing from list)

  BLOCKERS
  - No Saeed approval yet to merge feature branch → main
  - No real staff accounts (pilot blocked)
  - Governance gates 1–7 unsigned
  - JEFF_WEBHOOK_SECRET not set

  NEEDS YOUR OK
  - [ ] Explicit approval to merge feature/refactor-2-5-6 → main
  - [ ] Staff account details for Churchtown pilot
  - [ ] Governance sign-off
  - [ ] Real staff accounts — provide names, roles, emails to unblock pilot go-live
  - [ ] Governance gates 1-7 sign-off — cannot be delegated
  - [ ] JEFF_WEBHOOK_SECRET — set in environment before any live Jeff traffic
  - [ ] n8n API key rotation — confirmed "later"
  (From PROJECT_MEMORY: - **Item #2 (split main.py) EXTRACTION COMPLETE** -- branch feature/refactor-2-5-6, ALL routes extracted, main.py: 4,634 → 2,010 lines, zero inline @app routes remain (last commit 7fc1030). PENDING SAEED APPROVAL TO MERGE.; 3. LLM identity fields blocked from patient matching pipeline -- DONE; ### Pending Saeed approvals / actions;  1   | Merge feature/refactor-2-5-6 → main               | DevOps   | PENDING SAEED APPROVAL;  2   | Remove legacy static-salt password fallback       | Backend  | PENDING (already done in auth.py — verify before removing))

GIT (JeffLocal): 79bd895 Merge feature/refactor-2-5-6 into main (Saeed approved 2026-07-14) | f33fc73 fix: alert import crash, /api/search batch_id bug, notes-gate bypass; add 25-case pipeline test | 2f70e19 memory: session summary 2026-07-14

----------------------------------------------------------------

=== ST MARKS PHARMACY (STMARKS-WEB) ===
  (No log today - using 2026-07-03-1135.md, 271h ago)

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

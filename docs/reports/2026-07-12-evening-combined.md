COMBINED EVENING BRIEF (session close) â€” 2026-07-12 19:00
Both projects â€” Avamed AI triage + St Marks Pharmacy website
================================================================

=== AVAMED / JEFFLOCAL ===
  WHAT WE DID TODAY
  - No session log in last 24h.

  WHAT IS NEXT (tomorrow)
  - Remove legacy static-salt password fallback -- Backend -- PENDING (NOTE: already done in auth.py — verify before removing from list)
  - n8n API key rotation -- DevOps -- Before go-live
  - Set JEFF_WEBHOOK_SECRET -- DevOps -- Before live traffic
  - Get Saeed's sign-off on staff accounts + governance gates 1-7 — this is the main pilot go-live blocker

  BLOCKERS
  - None.

  NEEDS YOUR OK
  - [ ] Real staff accounts -- provide names, roles, emails to unblock pilot go-live
  - [ ] Governance gates 1-7 sign-off -- cannot be delegated
  - [ ] JEFF_WEBHOOK_SECRET -- set in environment before any live Jeff traffic
  - [ ] n8n API key rotation -- confirmed "later"
  (From PROJECT_MEMORY: 3. LLM identity fields blocked from patient matching pipeline -- DONE; ### Pending Saeed approvals / actions;  1   | Remove legacy static-salt password fallback       | Backend  | PENDING (NOTE: already done in auth.py — verify before removing from list);  5   | Split main.py into modules (refactor/split-main-py branch) | Backend | PENDING — plan written, not started)

GIT (JeffLocal): ea0a30f memory: session end protocol 2026-07-11 18:00 | 1b10906 memory: session end protocol 2026-07-10 18:00 | ec30e0a memory: session end protocol 2026-07-09 18:00

----------------------------------------------------------------

=== ST MARKS PHARMACY (STMARKS-WEB) ===
  (No log today - using 2026-07-03-1135.md, 223h ago)

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

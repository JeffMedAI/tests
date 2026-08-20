COMBINED EVENING BRIEF (session close) â€” 2026-07-15 19:00
Both projects â€” Avamed AI triage + St Marks Pharmacy website
================================================================

=== AVAMED / JEFFLOCAL ===
  WHAT WE DID TODAY
  - Full isolated end-to-end pipeline test of the Item #2 refactor (feature/refactor-2-5-6): 25 synthetic calls, real n8n webhook, live Ollama, deterministic matching, safety rules, dashboard import. Ran on a throwaway copy (port 8799), production untouched during the test.
  - All 25 cases verified correct against code-derived expectations. Safety invariant held. All 6 red flags caught, including one buried mid-ramble.
  - Resolved all 25 cases via dashboard endpoints (staff simulation), then a second full pass with genuine browser clicks on a subset.
  - Found + fixed: `alert_row_to_display` NameError crashing `/` and `/requests` whenever a critical alert exists. Live on production since 13 Jul.
  - Independent Fable 5 evaluation of the refactor. Honest score: 4.5/10. Corrected two of my own claims — bugs #2 (search) and #4 (notes-gate) are pre-existing, not refactor-introduced. Flagged 107 back-references from routers into main.py (coupling not actually reduced), dead duplicate functions, zero lint run.
  - Saeed approved 4 fixes: `/api/search` batch_id bug, notes-gate ordering bug, delete 2 dead functions, commit session work.

  WHAT IS NEXT (tomorrow)
  - Run full Playwright E2E suite directly against production (:8765) to confirm the 5 previously-failing tests now pass live (already proven equivalent via the isolated instance, but not yet re-run against :8765 itself).
  - Fix `restart_all.ps1` — it's out of sync with `watchdog.ps1`'s actual parameters (`-DashOnly`/`-N8nOnly` don't exist there).
  - Consider a linter (ruff/pyflakes) as part of the test gate — would have caught the crash bug in one second.
  - De-couple routers from main.py properly (107 back-references currently) — flagged by Fable 5, not fixed this session, real work for Item #2 follow-up.

  BLOCKERS
  - No real staff accounts (names/roles/emails needed from Saeed) — pilot go-live blocker, unrelated to this session's work.
  - Governance gates 1-7 unsigned.
  - JEFF_WEBHOOK_SECRET not set.
  - None of the above block today's work — all closed cleanly.

  NEEDS YOUR OK
  - [ ] None from this session — all 4 approved items done, merge done, production redeployed and verified, batch test passed. Session closed clean.
  - [ ] Standing items (unrelated, carried over): staff accounts, governance gates 1-7, JEFF_WEBHOOK_SECRET, n8n API key rotation.
  - [ ] Real staff accounts — provide names, roles, emails to unblock pilot go-live
  - [ ] Governance gates 1–7 sign-off — cannot be delegated
  - [ ] JEFF_WEBHOOK_SECRET — set in environment before any live Jeff traffic
  - [ ] n8n API key rotation — confirmed "later"
  (From PROJECT_MEMORY: 3. LLM identity fields blocked from patient matching pipeline -- DONE; ### Pending Saeed approvals / actions;  6   | Remove legacy static-salt password fallback       | Backend  | PENDING (already done in auth.py — verify before removing))

GIT (JeffLocal): 6a4e59f fix: restart_all.ps1 no longer passes nonexistent switches to watchdog.ps1 | 5285623 memory: session close 2026-07-15 09:50 ÔÇö refactor tested, fixed, merged, deployed | 298c6cd memory: session end protocol 2026-07-14 18:00

----------------------------------------------------------------

=== ST MARKS PHARMACY (STMARKS-WEB) ===
  (No log today - using 2026-07-03-1135.md, 295h ago)

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

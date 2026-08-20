COMBINED EVENING BRIEF (session close) â€” 2026-07-02 19:00
Both projects â€” Avamed AI triage + St Marks Pharmacy website
================================================================

=== AVAMED / JEFFLOCAL ===
  WHAT WE DID TODAY
  - No work committed today. No commits found since midnight.

  WHAT IS NEXT (tomorrow)
  - Remove legacy static-salt password fallback (Backend — PENDING)
  - n8n API key rotation (DevOps — Before go-live)
  - Set JEFF_WEBHOOK_SECRET (DevOps — Before live traffic)
  - Confirm with Saeed whether any of the 4 pending approvals are ready to action

  BLOCKERS
  - None.

  NEEDS YOUR OK
  - [ ] Real staff accounts — provide names, roles, emails to unblock pilot go-live
  - [ ] Governance gates 1-7 sign-off — cannot be delegated
  - [ ] JEFF_WEBHOOK_SECRET — set in environment before any live Jeff traffic
  - [ ] n8n API key rotation — confirmed "later"
  (From PROJECT_MEMORY: 3. LLM identity fields blocked from patient matching pipeline -- DONE; ### Pending Saeed approvals / actions;  1   | Remove legacy static-salt password fallback       | Backend  | PENDING)

GIT (JeffLocal): 4aaf6e4 memory: session end protocol 2026-07-01 18:00 | c94aabb memory: session end protocol 2026-06-29 18:00 | 7f39d36 feat: combined brief script covering JeffLocal + SMCPHARMA in one message

----------------------------------------------------------------

=== ST MARKS PHARMACY (STMARKS-WEB) ===
  (No log today - using 2026-06-30-1300.md, 36h ago)

  WHAT WE DID TODAY
  - Built all remaining service pages. Site now 30 pages.
  - 6 NHS pages: hub + blood pressure check, contraception (the pill), NHS flu jab, stop smoking, New Medicine Service. Free, walk-in, red flags + FAQ on each.
  - 12 private pages: hub + travel jabs, ear wax microsuction, weight management, private flu, ED, vitamin B12, period delay, emergency contraception, blood tests, hay fever injection, passport photos.
  - Every private page shows pricing (price table) per the rules. Guide prices flagged "confirm in store" where not in the reference.
  - Added booking form on /contact #book: full name, phone, postcode, current pharmacy/GP (St Marks preselected + 10 real Southport pharmacies), service dropdown, date, time, optional message. Submit → "message received" confirmation with patient's first name.
  - New CSS components: price-table, FAQ accordion, booking form.

  WHAT IS NEXT (tomorrow)
  - Wire booking form to a real inbox/booking tool (Calendly/Acuity/Formspree). Right now submit only shows a confirmation — it does NOT send anywhere yet.
  - Pharmacist (Mr Paul Cheston, superintendent) must review every clinical page before launch — GPhC hard gate.
  - Resolve weight-management + ED + period-delay + hay-fever wording for MHRA (no POM advertising) — get compliance/pharmacist eyes on it.
  - Confirm Yellow Fever (NaTHNaC) and ear piercing (Sefton) before advertising those.

  BLOCKERS
  - Booking form has no backend yet — needs a booking/email tool decision from Saeed.
  - Real phone, WhatsApp, hours, SP GPhC number not provided.
  - Pharmacist clinical sign-off not done.

  NEEDS YOUR OK
  - [ ] Decide booking tool (Calendly / Acuity / simple email form).
  - [ ] Provide phone, WhatsApp, opening hours, superintendent pharmacist GPhC number.
  - [ ] Approve / correct the 10 Southport pharmacies in the booking dropdown.
  - [ ] Send clinical pages to the pharmacist for sign-off.
  - [ ] Review live site once Cloudflare finishes deploying.

GIT (St Marks): cc403b3 fix: correct superintendent pharmacist name throughout | bc1aafc feat: one-tap booking email handler + memory protocol | 708c4d4 feat: wire booking form to email, add real phone/hours, fix footer link

================================================================
Detail: C:\JeffLocal\PROJECT_MEMORY.md | C:\JeffLocal\SMCPHARMA\CLAUDE.md

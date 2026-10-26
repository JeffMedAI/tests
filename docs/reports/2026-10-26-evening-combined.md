EVENING BRIEF (wrapping up today) - 2026-10-26 19:00
Your two projects: the AI reception helper (Avamed) and the pharmacy website (St Marks)
================================================================
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! WARNING - PART OF THIS BRIEF IS OUT OF DATE
!!   AI reception helper (Avamed) : nothing new logged for 12 working days (18 day(s) ago) - still showing 2026-10-07-1800.md
!!
!! No work has been logged for the project(s) above, and they are
!! not marked as paused.
!! Either work has genuinely stopped, or it is not being saved.
!! What you read below for them is OLD news repeated, not today's work.
!! Do not read it as progress. This needs looking at before you trust it.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Note: Pharmacy website (St Marks) is paused on purpose (awaiting pharmacist sign-off) - nothing new logged for 19 day(s).
      -> Paused for 19 day(s) now. Is this still correct?
         Tell Claude to un-pause it or change the reason, next time you talk.

=== YOUR AI RECEPTION HELPER (Avamed) ===
  (STALE - no real session log today. Newest real log: 2026-10-07-1800.md, 455h ago)

  WHAT WE DID TODAY
  - The system sent repeated WhatsApp alerts every fifteen minutes.
  - One file, booking_alert.ps1, was changed today.

  WHAT IS NEXT (tomorrow)
  - We will merge the brief fixes once Saeed provides his approval.
  - After merging, we will review morning and evening WhatsApp briefs for correct approvals.
  - We will optionally create glossary notes and remove unnecessary security terms.
  - (+2 more - ask me)

  WHAT'S STUCK
  - Three security items still open: unauthenticated intake endpoint, HMAC secret in git history, directory permissions.
  - Staff accounts for Churchtown do not exist yet.
  - Governance gates 1-7 unsigned.

  THINGS I NEED YOU TO OK
  - [ ] Create staff accounts with names, roles and emails.
  - [ ] Sign governance gates 1-7.
  - [ ] Agree the HMAC secret before live data flows.
  - [ ] Close the three security items.
  - [ ] NHS SBS and DSPT both overdue - set a target.
  - [ ] Clear about 22 empty junk files at repo root (move to archive, not delete).

Behind the scenes: 1 code change(s) saved today.

----------------------------------------------------------------

=== YOUR PHARMACY WEBSITE (St Marks) ===
  (STALE - no real session log today. Newest real log: 2026-10-06-1800.md, 479h ago)

  WHAT WE DID TODAY
  - A secure request retrieved booking IDs and times for the one-hour WhatsApp reminder.
  - Two files, db.js and index.js, were changed today.

  WHAT IS NEXT (tomorrow)
  - We will confirm that all test rows are successfully removed from the data set.
  - We need to decide which staff members should receive booking alerts instead of using Outlook.
  - We should consider adding a visible count for worker logs to monitor for potential bot activity.
  - (+2 more - ask me)

  WHAT'S STUCK
  - None for booking flow. Carry-over blockers as above (pharmacist, GPhC no., WhatsApp no., photos).
  - Project progress is not currently hindered by any outstanding tasks.
  - The remaining steps require obtaining pharmacist approval, securing the regulatory number for the footer, getting a live WhatsApp Business number, and setting up payment processing.
  - Authentic pharmacy photography must be completed before launch because twenty pages are currently displayed on the brand panel following the image cleanup on August 19th.

  THINGS I NEED YOU TO OK
  - [ ] Run SELECT to confirm test rows deleted.
  - [ ] Decide which inbox staff watch for booking alerts.
  - [ ] Carry-over: pharmacist sign-off, GPhC number, WhatsApp number, photography.
  - [ ] The issue with the expiration warning notification has been permanently resolved.
  - [ ] We need to schedule the removal of the "Coming Soon" banner from all twelve private service pages.
  - [ ] We must review the twenty simple pages to determine if they are acceptable or require a redesign.
  - [ ] New pharmacist approval is required for the weight management and clinical pages because their content has been updated.
  - [ ] We must obtain the Superintendent GPhC number for the footer to meet legal requirements.

Behind the scenes: 1 code change(s) saved today.

================================================================
Want more detail on anything above? Just ask me next time we talk.

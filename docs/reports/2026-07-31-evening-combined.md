EVENING BRIEF (wrapping up today) - 2026-07-31 19:00
Your two projects: the AI reception helper (Avamed) and the pharmacy website (St Marks)
================================================================

=== YOUR AI RECEPTION HELPER (Avamed) ===
  WHAT WE DID TODAY
  - Do not commit any work today and make no changes to the live system or source code.

  WHAT IS NEXT (tomorrow)
  - The security logic needs to be fixed immediately because an endpoint is currently exposed, pending a required sign-off.
  - We must rotate the secret key while ensuring this change is properly recorded in our version history.
  - The multi-tenant database separation project is complete, with the final cutover scheduled for July 28, 2026, and only minor items remain pending approval.
  - We need to pursue the three outstanding security approvals before we can launch the pilot program.

  WHAT'S STUCK
  - Nothing stuck right now.

  THINGS I NEED YOU TO OK
  - [ ] Three security items require fixing: an unauthenticated intake endpoint, rotating the HMAC secret in Git history, and setting directory access controls on the local configuration files, for which a fix script is ready to be run manually by Saeed.
  - [ ] Multi-tenancy steps one through five are complete, deployed, and verified live as of July 28, 2026, and the next steps involve verifying login access as a super-admin, setting Cloudflare hostnames, and replacing placeholder logins with actual staff names before launch.
  - [ ] To unblock the pilot launch, we require the names, roles, and email addresses for the real staff accounts.
  - [ ] Sign-off for governance gates one through seven is mandatory and cannot be delegated.
  - [ ] The JEFF_WEBHOOK_SECRET must be set before any live Jeff traffic occurs, as the endpoint remains open until that time.
  - [ ] The rotation of the n8n API key has been confirmed to happen later.
  - [ ] The draft line for the St Marks privacy policy is on branch and requires review by the pharmacist or Data Protection Officer.

Behind the scenes: 1 code change(s) saved today.

----------------------------------------------------------------

=== YOUR PHARMACY WEBSITE (St Marks) ===
  (No log today - using 2026-07-29-1200.md, 52h ago)

  WHAT WE DID TODAY
  - The booking dashboard is self-contained and uses our own database as the single source of truth for all bookings.
  - The staff interface includes login, status views, note-taking capabilities, account management, administrative controls, and automated password changes.
  - Email has been set up as an always-on backup system so that if the database fails, booking information is not lost.
  - External forwarding integrations have been removed, and the privacy policy now specifies that stored bookings are retained for ninety days and are accessible only to staff.
  - The project files include all necessary source code, database setup scripts, administrative seeding tools, and deployment documentation.
  - End-to-end testing is complete, security reviews were performed during development, and one race condition issue related to initial setup has been resolved.

  WHAT IS NEXT (tomorrow)
  - To maximize visibility, claim and optimize the Google Business Profile, then collect reviews via QR codes and staff requests on in-pharmacy posters.
  - For Google Search Console, verify ownership by adding the Cloudflare DNS record and submit the sitemap.
  - If a Stripe account is already established, build the payment system within approximately one day.
  - Add named staff accounts to the dashboard and upload a branded 1200x630 image for sharing.

  WHAT'S STUCK
  - Payments are currently blocked on the St Marks Stripe account, and Saeed is scheduled to open it.
  - The separate approval steps remain unchanged: a pharmacist must provide clinical sign-off and the DPO/ICO must review before patients can be actively promoted.

  THINGS I NEED YOU TO OK
  - [ ] Utilizing the Google Business Profile, reviews, and posters are free tools that offer the highest return on investment.
  - [ ] This requires setting up a Stripe account for payments, establishing a placeholder WhatsApp Business number, and including the SP pharmacist GPhC number in the footer (to be confirmed).

Behind the scenes: 0 code change(s) saved today.

================================================================
Want more detail on anything above? Just ask me next time we talk.

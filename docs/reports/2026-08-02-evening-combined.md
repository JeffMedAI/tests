EVENING BRIEF (wrapping up today) - 2026-08-02 19:00
Your two projects: the AI reception helper (Avamed) and the pharmacy website (St Marks)
================================================================

[Note: AI rewrite unavailable - raw summary below]

=== YOUR AI RECEPTION HELPER (Avamed) ===
  WHAT WE DID TODAY
  - There are no scheduled tasks or commitments for today.

  WHAT IS NEXT (tomorrow)
  - A security fix was implemented in n8n.py to address an HMAC failure by removing the exposed test intake batch API endpoint.
  - The necessary authentication logic is required because the associated endpoint is currently open.
  - The voice agent secret file has been rotated and updated within the Git history to ensure proper tracking of the change.
  - Access control lists for the local configuration files have been successfully updated by Saeed, completing this DevOps task on July 20, 2026.

  WHAT'S STUCK
  - Nothing stuck right now.

  THINGS I NEED YOU TO OK
  - [ ] The 3 security items at the top of this file — unauthenticated intake endpoint (a specific web address a computer program listens on), HMAC (a security code that proves a message wasn't faked)
  - [ ] secret in git history (needs rotation), directory ACLs on C:\JeffLocal + config.
  - [ ] REMINDER — fix script for item 3 is ready: `scripts\service_control\fix_directory_acl.ps1`.
  - [ ] Saeed to run manually (admin PowerShell). Carry this reminder forward every session until done.
  - [ ] Multi-tenancy — IN BUILD, steps 1-3 of 8 done and deployed 2026-07-17. Saeed decided
  - [ ] (2026-07-16, clarified 2026-07-17): separate database per tenant (a separate customer, like one GP surgery or one pharmacy). A tenant (a separate customer, like one GP surgery or one pharmacy) = a GP practice
  - [ ] (Churchtown + 4 more planned) or St Marks. St Marks is simply tenant #2, a stand-alone
  - [ ] pharmacy — NOT a special case, and it will never have "tenant pharmacies" beneath it. Each
  - [ ] tenant's staff get logins scoped to their own tenant. Avamed super-admin = a tenant switcher
  - [ ] (SETTLED 2026-07-17): switch tenant on the dashboard, view each tenant's data individually to
  - [ ] provide support. NOT a merged cross-tenant view; NOT for practice staff. See
  - [ ] governance/MULTI_TENANCY_PROPOSAL.md (§6 settled, §8 sequence). Gates every tenant's go-live,
  - [ ] including St Marks.
  - [ ] Next: step 4, stand up the stmarks tenant instance + hostname + its staff accounts — still
  - [ ] blocked by open item #3 (config dir ACL (the list of who is allowed to change a folder)) below (NOTE: item #3 shows DONE 2026-07-20 in the open
  - [ ] tasks table — this pending-approvals entry may be stale, check before acting).
  - [ ] Real staff accounts — provide names, roles, emails to unblock pilot go-live
  - [ ] Governance gates 1-7 sign-off — cannot be delegated
  - [ ] JEFF_WEBHOOK_SECRET — set before any live Jeff traffic (see #1 — endpoint is open until then)
  - [ ] n8n API (a way two computer programs talk to each other) key rotation — confirmed "later"
  - [ ] St Marks privacy-policy line — drafted on branch `draft/privacy-avamed-processor` in
  - [ ] SMCPHARMA, NOT pushed (that repo auto-deploys). Needs pharmacist/DPO review.

Behind the scenes: 1 code change(s) saved today.

----------------------------------------------------------------

=== YOUR PHARMACY WEBSITE (St Marks) ===
  (No log today - using 2026-07-29-1200.md, 100h ago)

  WHAT WE DID TODAY
  - The self-contained booking dashboard is hosted on our own database, which serves as the single source of truth for all bookings.
  - The staff interface includes features for logging in, managing booking statuses, adding notes, reopening bookings, managing individual accounts, and administrative controls like adding or disabling users, along with automated security tasks.
  - Email has been established as an always-on backup system to ensure data integrity, allowing the system to fall back to email if the database fails without losing any booking information.
  - External forwarding integrations have been removed, the privacy processor was abandoned, and the updated privacy policy now specifies that stored bookings are retained for ninety days and are accessible only to staff.
  - The project involved rewriting several core application files, database migration scripts, administrative seeding routines, and deployment documentation.
  - End-to-end testing is complete across both local and live environments, and a single security issue related to the initial setup race condition has been resolved by implementing an administrative seed during deployment.

  WHAT IS NEXT (tomorrow)
  - The most effective strategy is to claim and optimize the Google Business Profile by collecting reviews through QR codes and staff requests posted in pharmacy posters.
  - To use Google Search Console, verify ownership by adding the Cloudflare DNS record and then submit the sitemap.
  - If a Stripe account already exists, payment setup can be completed within approximately one day.
  - Add named staff accounts to the dashboard and upload a branded image for sharing.

  WHAT'S STUCK
  - Payments are blocked on the St Marks Stripe account until Saeed opens it.
  - The separate approval process remains unchanged: a pharmacist must provide clinical sign-off and the DPO/ICO must review before we can actively promote these items to patients.

  THINGS I NEED YOU TO OK
  - [ ] Use the Google Business Profile, reviews, and posters as free marketing tools that provide the highest return on investment.
  - [ ] We require a Stripe account for payments, a placeholder WhatsApp Business number, and the SP pharmacist GPhC number will be added later.

Behind the scenes: 0 code change(s) saved today.

================================================================
Want more detail on anything above? Just ask me next time we talk.

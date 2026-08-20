EVENING BRIEF (wrapping up today) - 2026-07-27 19:00
Your two projects: the AI reception helper (Avamed) and the pharmacy website (St Marks)
================================================================

[Note: AI rewrite unavailable - raw summary below]

=== YOUR AI RECEPTION HELPER (Avamed) ===
  WHAT WE DID TODAY
  - No tasks or deliverables were scheduled for completion today.

  WHAT IS NEXT (tomorrow)
  - The security logic for the intake endpoint is currently exposed and must be fixed immediately.
  - The secret key needs to be rotated and properly documented in the history to maintain security standards.
  - Access permissions were finalized on July 20, 2026, which unblocks the fourth step of tenant onboarding.
  - Saeed must complete the three outstanding security approvals because they are blocking the final launch.

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
  - [ ] Real staff accounts -- provide names, roles, emails to unblock pilot go-live
  - [ ] Governance gates 1-7 sign-off -- cannot be delegated
  - [ ] JEFF_WEBHOOK_SECRET -- set before any live Jeff traffic (see #1 — endpoint is open until then)
  - [ ] n8n API (a way two computer programs talk to each other) key rotation -- confirmed "later"
  - [ ] St Marks privacy-policy line — drafted on branch `draft/privacy-avamed-processor` in
  - [ ] SMCPHARMA, NOT pushed (that repo auto-deploys). Needs pharmacist/DPO review.

Behind the scenes: 3 code change(s) saved today.

----------------------------------------------------------------

=== YOUR PHARMACY WEBSITE (St Marks) ===
  (No log today - using 2026-07-16-1200.md, 269h ago)

  WHAT WE DID TODAY
  - We have mapped out the current system structure, which consists of 183 data points, 172 connections, and 19 distinct groups, based on the latest version.
  - We are integrating the booking form to automatically send each reservation into the Avamed JeffLocal dashboard as a new task, in addition to the existing email notification.
  - The integration strategy requires direct communication between systems, sending both an email and a dashboard alert, and we will not proceed with writing code until the process is fully tested and proven reliable.
  - Currently, the development work is limited to adding configuration constants and planning notes to the main file, with no functional code written or deployed yet.
  - The related system component for JeffLocal has been reviewed and fixed but has not yet been merged into the main system or deployed to the live dashboard.

  WHAT IS NEXT (tomorrow)
  - Complete the system function that builds booking data and securely forwards it to the external service, ensuring that any errors do not block email delivery.
  - Before committing any changes, test the functionality locally against a local instance of the JeffLocal dashboard as required by Saeed.
  - After successful testing, configure the necessary security secret for the forwarding process, matching the setting on the JeffLocal side without committing the secret to the code.
  - Determine whether the draft privacy policy needs an update to disclose this new data flow to Avamed before the system is launched.

  WHAT'S STUCK
  - The integration cannot be fully launched until the JeffLocal system component is deployed to production.
  - A decision regarding the privacy policy disclosure for the new Avamed data flow has not yet been made.
  - The pharmacist sign-off, WhatsApp Business number, and SP GPhC number are all still outstanding from previous discussions.

  THINGS I NEED YOU TO OK
  - [ ] Should we add the privacy policy disclosure now or handle it in a separate step?
  - [ ] Confirm that the code has been tested before setting the STMARKS_INTAKE_SECRET as an active Cloudflare secret.

Behind the scenes: 0 code change(s) saved today.

================================================================
Want more detail on anything above? Just ask me next time we talk.

EVENING BRIEF (wrapping up today) - 2026-08-08 19:00
Your two projects: the AI reception helper (Avamed) and the pharmacy website (St Marks)
================================================================

[Note: AI rewrite unavailable - raw summary below]

=== YOUR AI RECEPTION HELPER (Avamed) ===
  WHAT WE DID TODAY
  - There are no tasks scheduled for completion today.

  WHAT IS NEXT (tomorrow)
  - Fix the security vulnerability in n8n.py by removing the /api/n8n/test-intake-batch endpoint due to an HMAC failure.
  - The current authentication logic has an open endpoint that needs immediate attention.
  - Rotate the voice agent secret file within the Git history for security purposes, focusing on rotation rather than untracking.
  - We need to address tracking issues.

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
  - [ ] Step 5 (tenant picker + roles) merged and cutover run + verified live 2026-07-28.
  - [ ] Next: step 4/6, stand up the stmarks tenant instance + hostname + its staff accounts — still
  - [ ] blocked by open item #3 (config dir ACL (the list of who is allowed to change a folder)) below (ACL (the list of who is allowed to change a folder) item itself shows DONE 2026-07-20 in the
  - [ ] task table — confirm before assuming still blocked).
  - [ ] Real staff accounts -- provide names, roles, emails to unblock pilot go-live
  - [ ] Governance gates 1-7 sign-off -- cannot be delegated
  - [ ] JEFF_WEBHOOK_SECRET -- set before any live Jeff traffic (see #1 — endpoint is open until then)
  - [ ] n8n API (a way two computer programs talk to each other) key rotation -- confirmed "later"
  - [ ] St Marks privacy-policy line — drafted on branch `draft/privacy-avamed-processor` in
  - [ ] SMCPHARMA, NOT pushed (that repo auto-deploys). Needs pharmacist/DPO review.

Behind the scenes: 1 code change(s) saved today.

----------------------------------------------------------------

=== YOUR PHARMACY WEBSITE (St Marks) ===
  (No log today - using 2026-08-04-1602.md, 99h ago)

  WHAT WE DID TODAY
  - Following up on this morning's CEO readiness review, Saeed provided four instructions to fix compliance issues.
  - The required actions for the checklist include updating it, removing inaccurate reviews, and researching patient benefit statistics.
  - Responsibility for pharmacist, GPhC, WhatsApp, and payments is assigned to him and should not be altered.
  - I asked three scoping questions regarding review replacement, the structure of the compliance process, and where to place the statistics.
  - Since no response was received, we proceeded using the recommended default settings for each item, which were clearly noted in the plan.
  - A Plan agent was dispatched to design the implementation, and this process identified a genuine sourcing error.

  WHAT IS NEXT (tomorrow)
  - Saeed must review the live homepage sections after deployment to confirm that the tone and messaging are correct.
  - No content was pre-approved; only the plan's recommended defaults were used, and those defaults were not confirmed.
  - The compliance checklist flags one unresolved regulatory question: whether naming specific medications is permissible.
  - The open regulatory question concerns using names like Mounjaro, Wegovy, Sildenafil, and Tadalafil in a clinical service context instead of a direct advertisement.

  WHAT'S STUCK
  - The established set of items remains unchanged, including the pharmacist sign-off, GPhC number, WhatsApp contact, and payment details.
  - Saeed explicitly stated that he is responsible for handling these items during this round and has not been involved.

  THINGS I NEED YOU TO OK
  - [ ] Review the two new homepage sections, which include statistics and the honest reviews call to action, once they are live.
  - [ ] The advertising compliance decision flagged in the checklist requires further attention.
  - [ ] This issue needs a review by a qualified legal or regulatory expert, rather than an automatic resolution.
  - [ ] All other pending items remain unchanged from this morning's review.

Behind the scenes: 0 code change(s) saved today.

================================================================
Want more detail on anything above? Just ask me next time we talk.

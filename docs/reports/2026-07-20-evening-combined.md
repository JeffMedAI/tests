EVENING BRIEF (wrapping up today) - 2026-07-20 19:00
Your two projects: the AI reception helper (Avamed) and the pharmacy website (St Marks)
================================================================

=== YOUR AI RECEPTION HELPER (Avamed) ===
  WHAT WE DID TODAY
  - We investigated the missing 7 am WhatsApp brief from Saturday, July 19th, and started by testing read-only access.
  - The system recorded that the scheduled task ran successfully, but the script crashed without logging any error messages.
  - Subsequent checks revealed this was not an isolated incident, as there were three consecutive failed runs on Saturday morning, Saturday afternoon, and Monday morning.
  - A live test run confirmed the exact crash by reproducing a specific data access error during execution.
  - The root cause was determined to be a data type issue where a brief section collapsed into plain text instead of an array, causing the script to fail.
  - Saeed approved the necessary fix and the required directory permissions in the same communication.

  WHAT IS NEXT (tomorrow)
  - The process for setting up the St Marks tenant instance is now unblocked due to the Access Control List fix, so proceed with it.
  - None of the five required standing approvals were completed during this session.
  - We need to monitor the 7:00 AM brief tomorrow to ensure it runs successfully without manual intervention, as this is the first automated run since the fix.
  - To resolve the security issue, we must fix the authentication logic and immediately remove the exposed test intake batch endpoint.

  WHAT'S STUCK
  - There are no updates; all existing items remain exactly the same.

  THINGS I NEED YOU TO OK
  - [ ] The intake endpoint is still open, touches authentication, and requires a formal sign-off.
  - [ ] The HMAC secret needs to be rotated, and this task remains open.
  - [ ] We still need real staff accounts, including names, roles, and emails, to unblock the pilot launch.
  - [ ] Sign-off for governance gates one through seven cannot be delegated.
  - [ ] The privacy policy line for St Marks has been drafted on a branch and requires review by the pharmacist or Data Protection Officer.
  - [ ] The three main security items are the unauthenticated intake endpoint and the HMAC secret.
  - [ ] The secret in the history needs rotation, along with setting access controls for the directory on C:\JeffLocal and config.
  - [ ] A script to fix the issue related to item three is ready.
  - [ ] Saeed must manually run this script using administrator PowerShell and this reminder must be carried forward until completion.
  - [ ] Multi-tenancy is being built, and steps one through three of eight have been completed and deployed on July 17, 2026, as decided by Saeed.
  - [ ] The decision was made to use a separate database for each tenant, where a tenant represents a specific GP practice.
  - [ ] This applies to Churchtown and four other planned entities or St Marks, which is considered a stand-alone tenant.
  - [ ] The pharmacy designation is not a special case and will not include "tenant pharmacies" beneath it; each entity is separate.
  - [ ] Each tenant's staff must have logins scoped only to their specific tenant, and the Avamed super-administrator will serve as a tenant switcher.
  - [ ] It has been settled that the dashboard allows switching tenants and viewing each tenant's data individually for support purposes, not a merged cross-tenant view for practice staff.
  - [ ] This individual view is necessary for support and should not be a merged cross-tenant view or accessible to practice staff.
  - [ ] The governance proposal outlines the sequence of steps and gates required for every tenant's go-live, including St Marks.
  - [ ] This process includes signing off on all relevant governance gates for every tenant, including St Marks.
  - [ ] The next step is to set up the St Marks tenant instance, hostname, and staff accounts, which is still pending.
  - [ ] This setup is blocked by the outstanding issue regarding access controls for the configuration directory.
  - [ ] We need real staff accounts, including names, roles, and emails, to unblock the pilot launch.
  - [ ] Sign-off for governance gates one through seven cannot be delegated.
  - [ ] The webhook secret must be set before any live Jeff traffic occurs because the endpoint remains open until that time.
  - [ ] Rotation of the n8n API key has been confirmed for a later date.
  - [ ] The SMCPHARMA repository is not pushed and requires review by the pharmacist or Data Protection Officer before deployment.

Behind the scenes: 3 code change(s) saved today.

----------------------------------------------------------------

=== YOUR PHARMACY WEBSITE (St Marks) ===
  (No log today - using 2026-07-16-1200.md, 101h ago)

  WHAT WE DID TODAY
  - We have successfully built a data structure containing 183 connections and 19 groups based on the latest code, ensuring the data is current.
  - The booking form will be updated to forward each booking into the Avamed JeffLocal dashboard as a new task, in addition to sending the existing Resend email.
  - The agreed strategy for this integration is to send both the email and the dashboard notification without replacing the email functionality, and we will not commit code until it is fully tested.
  - Currently, only planning documentation has been added to the main file, and no functional code or testing has been written or committed yet.
  - The related system component exists on a separate branch, has been reviewed for security, but has not yet been merged into the main system or deployed to the live dashboard.

  WHAT IS NEXT (tomorrow)
  - Complete the forwarding function to build a message from booking details and send it to the external system, ensuring that any errors do not block email delivery.
  - Before committing or pushing code, test the functionality locally using the development environment against a local instance of the JeffLocal dashboard.
  - After successful testing, configure the necessary security secret within the deployment environment, ensuring it matches the setting on the JeffLocal side without committing the value to the code.
  - Determine whether the draft privacy policy requires an update to disclose this new data flow to Avamed before the system is launched.

  WHAT'S STUCK
  - The integration cannot launch until the JeffLocal system component is deployed to production.
  - The decision regarding privacy policy disclosure for the new Avamed data flow has not yet been made.
  - Several outstanding items, including clinical sign-off, a WhatsApp Business number, and an SP GPhC number, remain pending.

  THINGS I NEED YOU TO OK
  - [ ] Should we add the privacy policy disclosure line now or handle it in a separate follow-up?
  - [ ] Confirm that the code has been tested before setting the STMARKS_INTAKE_SECRET as an active Cloudflare secret.

Behind the scenes: 0 code change(s) saved today.

================================================================
Want more detail on anything above? Just ask me next time we talk.

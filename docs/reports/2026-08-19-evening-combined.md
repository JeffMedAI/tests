EVENING BRIEF (wrapping up today) - 2026-08-19 19:00
Your two projects: the AI reception helper (Avamed) and the pharmacy website (St Marks)
================================================================

=== YOUR AI RECEPTION HELPER (Avamed) ===
  (No log today - using 2026-08-11-1800.md, 192h ago)

  WHAT WE DID TODAY
  - No work has been committed to the repository since midnight.
  - The directory still contains a large number of modified and untracked files that were initially flagged on July 31st.
  - Tooling files and extraneous junk were left untouched.
  - The system state has remained unchanged since the last evening check on July 28th.
  - Multi-tenancy step five has been successfully verified in the live environment.

  WHAT IS NEXT (tomorrow)
  - Correct a security vulnerability by removing an insecure API endpoint related to batch intake.
  - Formal authorization for the authentication logic is required because the system endpoint is currently exposed.
  - We need to rotate the voice agent's secret key, ensuring this action is recorded in the history.
  - The current status of tracking information is missing.

  WHAT'S STUCK
  - Nothing stuck right now.

  THINGS I NEED YOU TO OK
  - [ ] The three security items listed at the top of PROJECT_MEMORY.md relate to an unauthenticated intake endpoint.
  - [ ] The HMAC secret for the test intake batch needs rotation because it was committed to the Git history.
  - [ ] The directory access control list permissions on C:\JeffLocal and config require a fix script.
  - [ ] Saeed must run the fix script located at scripts\service_control\fix_directory_acl.ps1 manually using administrator PowerShell.
  - [ ] Multi-tenancy steps one through five have been completed, deployed, and verified live as of July 28, 2026; the next steps are six and beyond.
  - [ ] The sequence must follow section eight of the governance/MULTI_TENANCY_PROPOSAL.md document.
  - [ ] To unblock the pilot go-live, we need names, roles, and emails for real staff accounts.
  - [ ] Sign-off for governance gates one through seven is mandatory and cannot be delegated.
  - [ ] The JEFF_WEBHOOK_SECRET must be set before any live Jeff traffic occurs because the endpoint remains open until that time.
  - [ ] The rotation of the n8n API key has been confirmed to happen later.
  - [ ] A line for the St Marks privacy policy has been drafted on the draft/privacy-avamed-processor branch.
  - [ ] The SMCPHARMA document is not yet pushed and requires review by the pharmacist and Data Protection Officer.

Behind the scenes: 0 code change(s) saved today.

----------------------------------------------------------------

=== YOUR PHARMACY WEBSITE (St Marks) ===
  WHAT WE DID TODAY
  - We need a "Coming Soon" banner for all twelve private service pages, including the hub and eleven others, using the exact wording provided by Saeed.
  - The purpose of the banner is solely to provide pre-launch caution, not to indicate a staffing or room availability issue, as confirmed by Saeed; the CLAUDE document remains unchanged.
  - The banner is implemented as a single component within the builders file, controlled by a single switch that activates only when the active status is set to 'private-services'.
  - Removing the banner must be done manually, there will be no automatic expiration, and this decision rests with Saeed.
  - The call-to-action links, including booking, phone, and WhatsApp, remain fully functional beneath the banner; it serves as a notice, not a restriction.
  - The photos used on the McKeevers weight-loss page, which Saeed provided, are actual manufacturer product shots of Mounjaro and Wegovy pens.

  WHAT IS NEXT (tomorrow)
  - Review the website; twenty pages are currently open on a plain teal panel, but no one has reviewed them because the preview feature does not capture the full session.
  - We need actual photographs of the pharmacy, team, and premises to resolve the image issues, which is a task for pre-launch.
  - Pharmacist approval is still outstanding for all clinical pages, and the weight page has increased, meaning there is now more content requiring sign-off.
  - Decide if the simple panel design is sufficient and revisit it if necessary.

  WHAT'S STUCK
  - The pharmacist clinical sign-off for all twenty-three clinical and service pages is pending, which is required by the GPhC gate, and Saeed is managing this process.
  - The Superintendent GPhC number in the footer remains undetermined.
  - The WhatsApp Business number is currently using a placeholder link.
  - Payments are currently managed through the Stripe account.
  - The advertising question on checklist row seven still requires review by a qualified legal professional, and the session has been expanded to include names of Orlistat and GLP-1 tablets.

  THINGS I NEED YOU TO OK
  - [ ] The site imagery must be upgraded before launch, and this instruction has been recorded in project memory for reference.
  - [ ] Please review the appearance of the twenty plain-panel pages to confirm they meet the required standards.
  - [ ] A manual notification must be provided when the Coming Soon banner is deployed.
  - [ ] An optional skill update is available but will not be implemented at this time.

Behind the scenes: 5 code change(s) saved today.

================================================================
Want more detail on anything above? Just ask me next time we talk.

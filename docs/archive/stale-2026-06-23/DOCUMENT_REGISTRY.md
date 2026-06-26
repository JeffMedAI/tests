# DOCUMENT REGISTRY — Avamed / JeffLocal
# Maintained by: Strategy Agent
# Last updated: 2026-05-31
# Purpose: Master index of all business, strategy, and operational documents.
#          Strategy Agent reads this at every session start to understand
#          what exists, who owns it, and when it was last reviewed.

---

## HOW TO USE THIS REGISTRY

- **Strategy Agent**: Read this at session start. Compare Last Reviewed dates against
  git log. Flag any document where Last Reviewed is more than 3 days behind a
  significant product change.
- **Lead Agent**: Reference this when building approval packs for document changes.
- **Saeed**: Use this as the single source of truth for what documents exist and their status.

---

## DOCUMENT STATUS LEGEND

```
CURRENT    — Accurate as of last review date. No known gaps.
DRAFT      — First draft complete. Not yet reviewed or approved for external use.
STALE      — Product has changed since last review. Update required.
PENDING    — Proposed changes submitted, awaiting Saeed approval.
ARCHIVED   — Superseded or no longer active. Kept in docs/archive/ for reference only.
```

---

## BUSINESS & STRATEGY DOCUMENTS

### 1. Avamed / JeffLocal Business Document
```
File:          docs\project_documents\Avamed_JeffLocal_Business_Document.docx
Status:        DRAFT
Created:       2026-05-29
Last reviewed: 2026-05-29
Reviewed by:   Saeed (confirmed as good first draft)
Approved for:  Internal reference only — not for external distribution without review
Owner:         Strategy Agent
Contains:      Executive summary, company overview, the problem, the solution,
               how it works, current status, product roadmap, target market,
               business model, go-to-market strategy, competitive landscape,
               team, risks & mitigation, next steps
Placeholders:  Pricing figures (TBC), pilot metrics (Phase 1 completion),
               second practice name (Phase 2)
Next review:   When Phase 1 Priority 1 items complete, or pricing confirmed
```

### 2. Practice Onboarding & Setup Guide
```
File:          docs\project_documents\Avamed_Practice_Onboarding_Guide.docx
Status:        DRAFT
Created:       2026-05-29
Last reviewed: 2026-05-29
Reviewed by:   Pending Saeed review
Approved for:  Internal / Avamed implementation team use
Owner:         Strategy Agent
Contains:      Hardware/software requirements, 10-step installation guide,
               configuration reference, staff account setup, go-live checklist
               (infrastructure, data, E2E test, security), pipeline testing,
               post-live handover, appendix quick reference
Placeholders:  Repo URL (git clone URL), support email, practice URL template
Next review:   Before first Phase 2 practice onboarding
```

### 3. Staff Training Guide
```
File:          docs\project_documents\Avamed_Staff_Training_Guide.docx
Status:        DRAFT
Created:       2026-05-29
Last reviewed: 2026-05-29
Reviewed by:   Pending Saeed review
Approved for:  Internal / practice staff use (after Saeed review)
Owner:         Strategy Agent
Contains:      How JeffLocal works, the dashboard (login, queue, case actions),
               all 8 request types and typical actions, safety flags protocol,
               unmatched patient handling, FAQs, tips, quick reference card
Placeholders:  Practice dashboard URL (per-practice), staff login instructions
Next review:   After dashboard UI changes (Issues R1–R3 now LIVE — review when
               further major UI changes ship)
```

### 4. Website & Marketing Strategy
```
File:          docs\project_documents\Avamed_Website_Marketing_Strategy.docx
Status:        DRAFT
Created:       2026-05-29
Last reviewed: 2026-05-29
Reviewed by:   Pending Saeed review
Approved for:  Internal strategy reference only
Owner:         Strategy Agent
Contains:      Strategic overview, brand positioning, positioning statement,
               brand personality, 3 buyer personas with detail, key message
               hierarchy, objection handling, website structure (8 pages),
               homepage priority sections, SEO priorities, channel strategy
               (Phase 1/2/3), content plan, marketing KPIs
Placeholders:  Pilot metrics, confirmed pricing, second practice name
Next review:   When pilot metrics available (Phase 1 completion)
```

### 5. Marketing Content Pack
```
File:          docs\project_documents\Avamed_Marketing_Content_Pack.docx
Status:        DRAFT
Created:       2026-05-29
Last reviewed: 2026-05-29
Reviewed by:   Pending Saeed review
Approved for:  Internal use only — external use requires Saeed approval per item
Owner:         Strategy Agent
Contains:      Website copy (homepage hero, trust bar, how it works, safety block,
               product page, pricing page, about page), 3 email outreach templates
               (cold intro, follow-up 1, follow-up 2), A4 one-pager copy,
               4 LinkedIn post templates, key message bank (5 categories)
Placeholders:  Pilot metrics, practice name for social proof, confirmed pricing,
               Saeed's contact details, website URL, LinkedIn profile URL
Next review:   When pilot metrics confirmed OR when any content item goes external
```

### 6. Sales & Marketing Pipeline
```
File:          docs\project_documents\Avamed_Sales_Marketing_Pipeline.md
Status:        DRAFT
Created:       2026-05-30
Last reviewed: 2026-05-31
Reviewed by:   Pending Saeed review
Approved for:  Internal strategy reference only — no external use
Owner:         Strategy Agent
Contains:      Buyer persona analysis (4 personas), channel strategy (8 channels),
               90-day content calendar, lead pipeline structure (7 stages),
               CRM recommendation (HubSpot), plugin/MCP recommendations (8 tools),
               week-by-week 90-day action plan, draft outreach templates
Placeholders:  Pilot metrics, Calendly link, website URL, contact details
Next review:   Phase 1 completion; when Churchtown case study approved;
               before any outreach sequence is sent
```

### 7. OpenJarvis Onboarding Plan
```
File:          docs\project_documents\Jarvis_Onboarding_Plan.md
Status:        CURRENT
Created:       2026-05-30
Last reviewed: 2026-05-31
Reviewed by:   Pending Saeed review
Approved for:  Internal planning only
Owner:         Strategy Agent
Contains:      Full onboarding plan for OpenJarvis as second pilot site.
               Phases, timelines, prerequisites, technical requirements,
               staff setup steps.
Next review:   When Saeed confirms OpenJarvis as active pilot target
```

---

## AGENT & GOVERNANCE DOCUMENTS

### 8. Strategy Agent Briefing
```
File:          sandbox\agents\strategy\strategy_CLAUDE.md
Status:        CURRENT
Created:       2026-05-29
Last reviewed: 2026-05-31
Reviewed by:   Saeed (approved as part of team onboarding)
Owner:         Lead Agent (with Strategy Agent input)
Contains:      Identity, file ownership, session startup protocol, daily report
               format, document change rules (minor/major), marketing cadence,
               agent prompt review process, escalation rules, never-does list
Next review:   After first monthly prompt review cycle
```

### 9. Lead Agent Task — Onboard Strategy Agent
```
File:          sandbox\agents\strategy\LEAD_AGENT_TASK_ONBOARD_STRATEGY_AGENT.md
Status:        CURRENT (complete — 2026-05-29)
Created:       2026-05-29
Last reviewed: 2026-05-29
Owner:         Lead Agent
Contains:      Acceptance criteria for Strategy Agent onboarding, constraints,
               directory structure, scheduled task setup, governance updates
Note:          All criteria met. Task Scheduler registration still pending
               (requires Saeed to run scripts\register_scheduled_tasks.ps1
               as Administrator).
```

### 10. Phase 1 Agent Assignments
```
File:          docs\reports\phase1_assignments_2026-05-30.md
Status:        CURRENT
Created:       2026-05-30
Last reviewed: 2026-05-31
Owner:         Lead Agent / Strategy Agent
Contains:      Full assignment briefs with acceptance criteria for all Phase 1
               technical tasks: HMAC verification, password reset, GDPR purge,
               E2E pipeline gap, test fixes, Playwright E2E, multi-tenancy,
               daily task scripts.
Next review:   As tasks complete — update status in PROJECT_MEMORY.md task table
```

---

## GOVERNANCE & FRAMEWORK DOCUMENTS

### 11. Governance Framework
```
File:          governance\GOVERNANCE_FRAMEWORK.md
Status:        CURRENT
Owner:         Lead Agent
Contains:      8-agent governance structure including Strategy Agent (added 2026-05-29).
               Org chart, decision rights, all agent role definitions, communication
               protocols, compliance and audit requirements. G1 breach record added
               2026-05-30.
Last updated:  2026-05-30 — G1 breach record added
Next review:   2026-08-22 (quarterly)
```

### 12. JeffLocal Production Specification
```
File:          governance\JEFFLOCAL_PRODUCTION_SPEC.md
Status:        CURRENT
Owner:         Lead Agent
Contains:      Full production specification: all departments, priority task lists,
               file structure, technical facts, production readiness checklist
Next review:   When Phase 1 Priority 1 items complete
```

### 13. Change Log
```
File:          governance\CHANGE_LOG.md
Status:        CURRENT
Owner:         Lead Agent / all agents (append on deploy)
Contains:      Official record of all approvals, deployments, and decisions.
               Entries through 2026-05-30.
Last updated:  2026-05-31 (Strategy Agent added 2026-05-30 session entries)
```

---

## COMPLIANCE & SECURITY DOCUMENTS

### 14. Security Review — Production Breach 2026-05-29
```
File:          docs\compliance\security_review_2026-05-29_prod_breach.md
Status:        CURRENT
Created:       2026-05-29
Owner:         Security Agent
Contains:      Post-hoc security review of G1 governance breach. All items
               APPROVED WITH NOTES.
```

### 15. Security Review — Watchdog & WhatsApp 2026-05-30
```
File:          docs\compliance\security_review_2026-05-30_watchdog_whatsapp.md
Status:        CURRENT
Created:       2026-05-30
Owner:         Security Agent
Contains:      Security review of watchdog.ps1, send_whatsapp.py, and
               strategy_daily.ps1 Steps 5 & 11. All APPROVED WITH NOTES.
               Key open item: script name mismatch fixed (send_whatsapp.py).
               Pre-live-data actions documented.
```

### 16. G1 Breach Acknowledgement
```
File:          docs\reports\G1_breach_acknowledgement_2026-05-30.md
Status:        CURRENT
Created:       2026-05-30
Owner:         Lead Agent
Contains:      Formal closure of G1 governance breach. All 6 breached rules
               documented. Process improvements confirmed. Status: CLOSED.
```

### 17. N1 Env Var Verification
```
File:          docs\reports\N1_verification_2026-05-30.md
Status:        CURRENT
Created:       2026-05-30
Owner:         Backend Agent / Lead Agent
Contains:      Verification that N1 (missing FLASK_SECRET_KEY env var) has
               been resolved. Fix confirmed complete.
```

---

## REPORTS & SESSION LOGS

### Daily Briefings
```
Directory:     docs\reports\
Format:        YYYY-MM-DD.md (one file per day, auto-generated 07:00)
Owner:         Strategy Agent (strategy_daily.ps1)
Active files:  2026-05-29.md (baseline), 2026-05-30.md, 2026-05-31.md
```

### Operational Reports
```
docs\reports\breach_report_2026-05-29.md     — G1 production breach incident report
docs\reports\config_audit_2026-05-29.md      — Audit confirming 4 config files created
docs\reports\dispatch_2026-05-29.md          — Dispatch summary 2026-05-29
docs\reports\lead_review_2026-05-30.md       — Lead Agent session review 2026-05-30
```

### Session Logs
```
Directory:     docs\sessions\
Format:        YYYY-MM-DD-HHMM.md
Active files:  2026-05-29-1800.md, 2026-05-29-2000.md, 2026-05-29-2245.md,
               2026-05-30-1600.md
Template:      SESSION_TEMPLATE.md
```

### Architecture Notes
```
docs\architecture\llm_vs_rules_responsibility.md  — LLM vs deterministic code boundary rules
docs\testing\end_to_end_test_requirements.md      — E2E test suite requirements
```

---

## MARKETING CONTENT (WORKING FILES)

```
Directory:     docs\marketing\
Status:        Empty — Strategy Agent populates as content is created and approved
Purpose:       Holds approved, ready-to-use marketing assets (social posts approved
               by Saeed, website copy approved for publication, etc.)
```

---

## ARCHIVED DOCUMENTS

```
Directory:  docs\archive\
Note:       Originals should be removed via git rm — see docs_health_2026-05-30.md

docs\archive\root_approvals\
  APPROVAL_PACK_COOKIE_FIX_20260523.md       — Cookie fix approval pack v1 (superseded)
  APPROVAL_PACK_COOKIE_FIX_FINAL.md          — Cookie fix approval pack final (fix LIVE)
  CONTROLTOWER_HARDREQS_VERIFICATION.md      — Part of cookie fix approval pack (fix LIVE)
  GUARDRAIL_SECURITY_REVIEW_COOKIE_FIX.md    — Part of cookie fix approval pack (fix LIVE)
  READY_TO_START.md                          — Sprint 1 Day 1 pre-restructure doc
  SAEED_ACTION_REQUIRED.md                   — Issue #1 approval request (deployed 2026-05-22)
  SAEED_FIX_INSTRUCTIONS.md                  — CSS cache fix for Issue #1 (resolved)

docs\archive\issue_docs\
  Issue_2_Fix_Approach.md                    — Issue #2 fix design (resolved via R1/R3)
  Issue_2_Initial_Assessment.md              — Issue #2 assessment (resolved via R1/R3)
  Issue_2_Investigation.md                   — Issue #2 investigation (resolved via R1/R3)

docs\archive\governance_stale\
  MASTER_STATUS_AND_NEXT_STEPS.md            — Sprint 1 Day 1 status (predates restructure)

docs\archive\state_reports\
  JEFFLOCAL_CURRENT_STATE_2026-05-18_115930.txt  — State snapshot 2026-05-18 (superseded)
```

---

## DOCUMENTS TO CREATE (FUTURE)

```
Priority | Document                          | Trigger
-------- | --------------------------------- | ------------------------------------
High     | Churchtown Pilot Case Study       | Phase 1 completion + metrics confirmed
High     | Pricing & Commercial Terms Sheet  | Before first Phase 2 sales conversation
Medium   | Data Processing Agreement (DPA)   | Before Phase 2 onboarding (GDPR Art. 28)
Medium   | Patient-Facing FAQ / Explainer    | Before Jeff voice agent goes public
Medium   | EMIS Integration Brief            | When EMIS API access application begins
Low      | PCN / Multi-Practice Overview     | Phase 2 commercial rollout
Low      | ICB Commissioner Briefing Pack    | Phase 3 preparation
```

---

## REVISION HISTORY

```
Date        | Change                                              | Author          | Approved by
----------- | --------------------------------------------------- | --------------- | -----------
2026-05-29  | Registry created, all documents indexed             | Strategy Agent  | Saeed
2026-05-29  | Governance Framework status updated: CURRENT        | Lead Agent      | Saeed (onboarding task)
2026-05-29  | Onboarding task status updated: complete            | Lead Agent      | Saeed (onboarding task)
2026-05-30  | Sales & Marketing Pipeline added (item 6)           | Strategy Agent  | Pending Saeed review
2026-05-31  | Full registry update: new docs added, archived docs | Strategy Agent  | Minor update (autonomous)
            | documented, status fields updated to reflect         |                 |
            | completed work (cookie fix, N1/N2, R1/R2/R3,        |                 |
            | watchdog, WhatsApp, E2E suite, G1 closure)           |                 |
```

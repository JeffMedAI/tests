# DOCUMENT REGISTRY — Avamed / JeffLocal
# Maintained by: Strategy Agent
# Last updated: 2026-05-29
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
ARCHIVED   — Superseded or no longer active. Kept for reference only.
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
Next review:   After dashboard UI changes (Issues #2–7 resolved)
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

---

## AGENT & GOVERNANCE DOCUMENTS

### 6. Strategy Agent Briefing
```
File:          sandbox\agents\strategy\strategy_CLAUDE.md
Status:        CURRENT
Created:       2026-05-29
Last reviewed: 2026-05-29
Reviewed by:   Saeed (approved as part of team onboarding)
Owner:         Lead Agent (with Strategy Agent input)
Contains:      Identity, file ownership, session startup protocol, daily report
               format, document change rules (minor/major), marketing cadence,
               agent prompt review process, escalation rules, never-does list
Next review:   After first monthly prompt review cycle
```

### 7. Lead Agent Task — Onboard Strategy Agent
```
File:          sandbox\agents\strategy\LEAD_AGENT_TASK_ONBOARD_STRATEGY_AGENT.md
Status:        CURRENT (complete — 2026-05-29)
Created:       2026-05-29
Last reviewed: 2026-05-29
Owner:         Lead Agent
Contains:      Acceptance criteria for Strategy Agent onboarding, constraints,
               directory structure, scheduled task setup, governance updates
Note:          All criteria met. One item pending: DevOps Agent to register
               strategy_daily.ps1 in Windows Task Scheduler (brief at
               scripts\daily\TASK_REGISTER_STRATEGY_DAILY.md)
```

---

## GOVERNANCE & FRAMEWORK DOCUMENTS

### 8. Governance Framework
```
File:          governance\GOVERNANCE_FRAMEWORK.md
Status:        CURRENT
Owner:         Lead Agent
Contains:      8-agent governance structure including Strategy Agent (added 2026-05-29).
               Org chart, decision rights, all agent role definitions, communication
               protocols, compliance and audit requirements.
Last updated:  2026-05-29 — Strategy Agent added to roster by Lead Agent
Next review:   2026-08-22 (quarterly)
```

### 9. JeffLocal Production Specification
```
File:          governance\JEFFLOCAL_PRODUCTION_SPEC.md
Status:        CURRENT
Owner:         Lead Agent
Contains:      Full production specification: all departments, priority task lists,
               file structure, technical facts, production readiness checklist
Next review:   When Phase 1 Priority 1 items complete
```

### 10. Master Status & Next Steps (Sprint 1 Day 1)
```
File:          governance\MASTER_STATUS_AND_NEXT_STEPS.md
Status:        STALE — predates sidebar fixes (Issues R1, R3) and team restructure
Owner:         Strategy Agent (to update)
Contains:      Sprint 1 Day 1 status report — infrastructure, Issue #1, approval workflow
Next review:   IMMEDIATE — update to reflect current team structure and sprint state
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

## DAILY REPORTS

```
Directory:     docs\reports\
Format:        YYYY-MM-DD.md (one file per day)
Owner:         Strategy Agent
First report:  2026-05-29 (see docs\reports\2026-05-29.md — initial baseline)
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
Date        | Change                                      | Author          | Approved by
----------- | ------------------------------------------- | --------------- | -----------
2026-05-29  | Registry created, all documents indexed     | Strategy Agent  | Saeed
2026-05-29  | Governance Framework status updated: CURRENT| Lead Agent      | Saeed (onboarding task)
2026-05-29  | Onboarding task status updated: complete    | Lead Agent      | Saeed (onboarding task)
```

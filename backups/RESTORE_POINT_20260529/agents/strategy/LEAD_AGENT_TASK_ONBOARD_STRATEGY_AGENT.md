# LEAD AGENT — TASK ASSIGNMENT
# Task: Onboard Strategy Agent (8th team member)
# Assigned by: Saeed
# Priority: Medium
# Blocking: Nothing — can be done independently of current sprint

---

## CONTEXT

We are adding an 8th agent to the JeffLocal team: the **Strategy Agent**.

This agent owns documentation, project memory, governance documents, daily
reporting, and marketing content. It is NOT a technical agent — it has no
production code access and no deployment authority.

The Strategy Agent operates under the same governance framework as all other
agents. The Lead Agent is its line manager. All major document changes require
Lead Agent to include them in an approval pack for Saeed's sign-off before
anything is published or finalised.

The agent briefing file has already been created at:
  `C:\JeffLocal\sandbox\agents\strategy\strategy_CLAUDE.md`

Read it in full before proceeding.

---

## YOUR JOB

Execute all items in the acceptance criteria below. Do not mark this task
complete until every item is confirmed. Report any blocker immediately.

---

## ACCEPTANCE CRITERIA

### 1. Directory structure
```
[ ] C:\JeffLocal\sandbox\agents\strategy\   — exists (already created)
[ ] C:\JeffLocal\docs\reports\              — create if missing
[ ] C:\JeffLocal\docs\marketing\            — create if missing
```

### 2. Lead Agent startup protocol (update your own CLAUDE.md)
```
[ ] Add to Step 1 — Read all context:
      "Read agents\strategy\strategy_CLAUDE.md"

[ ] Add to Step 2 — Check system state:
      "Read docs\reports\{yesterday}.md (Strategy Agent daily report)"
```

### 3. Lead Agent task assignment rules (update your own CLAUDE.md)
```
[ ] Add Strategy Agent as an assignable agent with its scope:
      "Strategy Agent — documentation, reporting, marketing content.
       Assign for: doc updates, daily reports, marketing drafts, prompt reviews.
       Never assign: code tasks, DB tasks, deployment tasks."

[ ] Add to parallel mode rules:
      "Strategy Agent can run in parallel with any technical agent
       (its work never touches the same files)."
```

### 4. Scheduled daily task
```
[ ] Create: scripts\daily\strategy_daily.ps1
    Content:
      # Triggers Strategy Agent daily report at 07:00
      # Reads git log (last 24h), checks doc freshness, generates report
      # Saves to docs\reports\{date}.md
      # Sends Dispatch summary to Saeed
    
[ ] Register with DevOps Agent to add to Windows Task Scheduler
    Trigger: daily 07:00
    Label: "JeffLocal — Strategy Agent Daily Report"
```

### 5. Governance framework update
```
[ ] Update governance\GOVERNANCE_FRAMEWORK.md:
      Add Strategy Agent to team roster with:
      - Role: Documentation, reporting, marketing, governance
      - Line manager: Lead Agent
      - Production access: None
      - Approval authority: None (submits proposals only)
      - Veto authority: None
```

### 6. Lead Agent escalation list (update your own CLAUDE.md)
```
[ ] Add to "When to escalate to human":
      "Strategy Agent has flagged a document as stale for 7+ days"
      "Strategy Agent has a major document change proposal requiring Saeed approval"
      "Marketing content from Strategy Agent is ready for external publication"
```

### 7. Session end report from Lead Agent
```
[ ] After all above is complete, report to Saeed:
      - Confirm each acceptance criterion met (tick list)
      - Confirm Strategy Agent CLAUDE.md path
      - Confirm daily schedule is registered
      - State when Strategy Agent's first daily report will run
      - Note any items deferred and why
```

---

## CONSTRAINTS

```
- Strategy Agent has NO access to: app\, dashboard\, queue\, config\
- Strategy Agent cannot publish marketing content without Saeed's approval
- Strategy Agent cannot edit any agent's CLAUDE.md without Lead Agent approval → Saeed sign-off
- All major document changes go through Lead Agent approval pack before Saeed sees them
- "Do it yourself" is NOT sufficient authorisation for major document changes
```

---

## DO NOT

```
✗ Assign tasks to Strategy Agent before confirming setup is complete
✗ Modify any production code as part of this onboarding
✗ Change governance rules — only add Strategy Agent to the roster
✗ Mark this task complete until every acceptance criterion is ticked
```

---

## FILES TO READ BEFORE STARTING

```
1. C:\JeffLocal\sandbox\agents\strategy\strategy_CLAUDE.md   ← new agent brief
2. C:\JeffLocal\governance\GOVERNANCE_FRAMEWORK.md            ← to update roster
3. Your own CLAUDE.md                                         ← to update protocols
```

---

Assigned by: Saeed
Date: 2026-05-29

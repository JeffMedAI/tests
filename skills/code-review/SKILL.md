# SKILL: Code Review — Avamed
# Trigger: before any PR merge or module handoff.

---

## When to Use

- Before any PR merge or module handoff to production
- When Saeed asks for a review of a specific module or function
- After a debugging session, to confirm the fix is clean

## When NOT to Use

- Documentation-only changes (no code modified)
- Pure configuration or environment changes outside C:\JeffLocal\

---

## Typical Input

A module, function, or set of files to review. Examples:
- "Review the importer.py module for safety issues"
- "Check the patient matching logic in Jeff.PatientMatch.ps1"
- "Review the auth changes before we merge"

---

## Step-by-Step Process

1. **Confirm the file is current.** Check git log — is this file actively used or is it archived/defunct? Do not review stale files.

2. **Read the full module** before commenting. No partial reviews.

3. **Check the Ollama safety rule.** Does any code path allow LLM output to set: verification_status, safe_to_queue, priority, matched_patient_name, EMIS number, NHS number, DOB, or clinical urgency? If yes, that is a CRITICAL issue.

4. **Check compliance.** GDPR handling in place? Audit log entries written? No patient data leaking to external calls or error messages?

5. **Check error handling.** Does it fail gracefully? Does it log clearly? Does it expose any sensitive data in exceptions?

6. **Check test coverage.** Do tests exist for this module? Do they pass? Do they use session-based auth (not the deprecated `jefflocal_staff_id` cookie)? Missing tests = FAIL.

7. **Run the test suite** (or confirm it has been run). Report results.

8. **Produce the structured report** (see Output Format below).

---

## Output Format

```
CODE REVIEW REPORT — [Module Name]
Reviewed by: Claude | Date: YYYY-MM-DD

VERDICT: PASS / FAIL / CONDITIONAL PASS

ISSUES (ranked by severity)
  CRITICAL: [description + file:line reference]
  HIGH:     [description]
  MEDIUM:   [description]
  LOW:      [description / suggestion]

SAFETY RULE CHECK
  Ollama/deterministic split: [PASS / FAIL — detail if fail]
  Prohibited fields verified: [PASS / FAIL]

COMPLIANCE CHECK
  GDPR handling: [PASS / FAIL / N/A]
  Audit logging: [PASS / FAIL / N/A]
  No external patient data leakage: [PASS / FAIL]

TEST RESULTS
  Test suite run: [yes/no]
  Result: [X/Y tests passing]
  Missing coverage: [list gaps]

FIX-IT CHECKLIST
  [ ] [issue 1 — file:line]
  [ ] [issue 2]
  [ ] Add regression test for [scenario]

NEXT STEPS
  [What must happen before this can merge]

DECISIONS NEEDED
  [Anything requiring Saeed's approval]
```

---

## Common Failure Modes — How to Prevent

- **Reviewing defunct files** — always check git log before starting. If the file has been archived or superseded, stop and flag it.
- **Marking untested code as passing** — if tests are missing or failing, the verdict is FAIL. No exceptions.
- **Skipping the safety rule check** — this applies to every code review, not just pipeline code.
- **Partial reviews** — read the whole module, not just the changed lines. Context matters in safety-critical code.

---

## Success Criteria

1. All critical and high issues are identified, documented with file:line references, and have a clear fix-it entry.
2. All tests pass — or failing tests are flagged as blockers with no merge until resolved.
3. The UX and staff workflow are unaffected or improved by the change.

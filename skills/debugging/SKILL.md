# SKILL: Debugging — Avamed
# Trigger: any error, test failure, or unexpected system behaviour.

---

## When to Use

- Any error message or stack trace in the sandbox dashboard or pipeline
- A failing test in the pytest suite
- Unexpected dashboard behaviour (wrong data displayed, action not triggering, etc.)
- A broken pipeline stage (importer not picking up files, n8n not writing, Ollama returning empty)

## When NOT to Use

- Configuration or environment problems that live outside C:\JeffLocal\ — flag to Saeed and stop
- Issues caused by missing config files (PE-01 through PE-04 are known absences, not bugs)

---

## Typical Input

- An error message or Python stack trace
- A failing test name and output (`pytest tests\test_importer.py -v`)
- "The dashboard isn't showing new cases" or similar behavioural description
- "The importer stopped picking up files" or similar pipeline description

---

## Step-by-Step Process

1. **Read the error in full** — do not skim. Stack traces contain the actual cause, not just the symptom.

2. **Identify the root cause, not the symptom.** Ask: "What upstream condition produced this error?" Trace back at least one level further than where the error appears.

3. **Search the codebase** for the source before proposing a fix. Read the relevant module in full.

4. **Check the Ollama safety rule** — if the bug is in the pipeline, verify the fix does not allow LLM output to override deterministic fields.

5. **Propose the fix** in plain English first: what went wrong, why, and what the fix does differently.

6. **Apply the fix to sandbox only** (`C:\JeffLocal\sandbox\dashboard\`). Never touch production during debugging without Saeed's explicit approval.

7. **Add or update a regression test** that covers this exact scenario. If no test existed before, add one.

8. **Run the full test suite** — confirm all tests pass after the fix, not just the one that was failing.

9. **Test every relevant channel** — dashboard UI, pipeline stage, importer, API endpoint, n8n webhook — whichever applies to this bug.

10. **Produce the structured report** (see Output Format below).

---

## Output Format

```
DEBUG REPORT — [Issue Title]
Date: YYYY-MM-DD | Environment: SANDBOX

ROOT CAUSE
  [Plain English explanation of what went wrong and why — not just what the error said]

FIX APPLIED
  File: [path:line]
  Change: [what was changed and why this resolves the root cause]

REGRESSION TEST
  Test added: [yes/no + test name]
  Test file: [path]

TEST RESULTS (post-fix)
  Full suite: [X/Y passing]
  Channels tested: [list every channel verified]

SAFETY RULE CHECK (if pipeline-related)
  Deterministic fields still protected: [PASS / N/A]

NEXT STEPS
  [If production fix needed, flag for Saeed approval]
  [If root cause points to a larger architectural issue, flag it]

DECISIONS NEEDED
  [Anything requiring Saeed's review before production deployment]
```

---

## Common Failure Modes — How to Prevent

- **Fixing the symptom, not the root cause** — always trace back. If the error is in importer.py, ask what created the malformed input. If a test fails, ask why the condition it tests now occurs.
- **Touching production during debugging** — always sandbox first. Production changes need Saeed's approval even for urgent fixes.
- **Marking a fix complete without testing all channels** — a fix that passes tests but breaks the n8n intake or the HMAC endpoint is not done.

---

## Success Criteria

1. Root cause is identified and documented — not just the symptom.
2. The fix is tested thoroughly using every relevant channel for this type of issue.
3. All existing tests continue to pass after the fix is applied.

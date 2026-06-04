# Quality Rules — Avamed
# The standard every Claude output must meet.

---

## Rigour Level: HIGH

Default to the highest standard on all work. No shortcuts on safety, testing, or verification.
This is a clinical-adjacent system handling real patient contact data. Errors have consequences.

---

## Five Quality Criteria

1. **Performance** — does it run efficiently without degrading the pipeline or dashboard response time?
2. **Ease of use** — can reception staff use it without confusion, training, or guesswork?
3. **Error handling** — does it fail gracefully, log clearly, and never expose patient data in error messages?
4. **Testing** — is it covered by tests that pass on every relevant channel?
5. **Staff feedback alignment** — does it address known pain points (clutter, unclear priorities, ambiguous actions)?

---

## Phase 1 Release Gate Criteria

A task or feature is not complete until all applicable gates pass:

- HMAC verification enforced on all incoming webhook payloads
- GDPR 90-day purge covers all patient data directories (not just one)
- Test suite uses session-based auth (not the deprecated `jefflocal_staff_id` cookie)
- Pipeline automation: zero manual steps from call receipt to dashboard display
- Password reset flow works end-to-end
- Practice settings externalised from templates (not hardcoded)
- Audit log table writing entries to SQLite for every relevant action
- Staff onboarding runbook written and reviewed

---

## What a Perfect Response Looks Like

- **Memory continuity** — draws on project history without needing to re-explain context already established
- **Thoroughly researched** — proposes the best solution found, not the first one thought of
- **Humanised language** — written for a non-technical CEO, not an engineer; technical detail available on request

---

## Red Flags — Response Is Bad or Unusable If

- Claims a task is done without running and reporting tests
- Accepts a task without challenging scope or clarifying ambiguity first
- Uses generic filler phrases ("I now have the full picture", "Perfect!", "Great question")
- Drifts outside project scope without flagging it
- Marks untested code as passing
- Reviews old or defunct files as if they were current
- Presents an assumption as a fact without the [UNVERIFIED] label
- Touches production without Saeed's explicit session approval

---

## Priority Order When Tradeoffs Occur

1. **Ask vs assume** — always ask when uncertain; never assume on safety or compliance matters
2. **Safety vs speed** — safety wins every time; never rush a change that touches patient data or auth
3. **Project deliverables** — stay aligned to the current sprint goals; warn if a task would cause drift

---

## Skill Promotion Rule

If the same type of task is requested 3 times, flag it as a Skill candidate.
Propose a SKILL.md for it and ask Saeed whether to formalise it.

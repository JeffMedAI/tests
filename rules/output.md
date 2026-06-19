# Output Rules — Avamed
# Applies to all Claude responses in this project.

---

## Default Format

Plain prose with structured sections. Code always in fenced code blocks with the correct language tag (```python, ```powershell, ```sql, etc.).

Never bullet-point-only responses — use prose to connect the points.
Always UK English spelling (programme, organisation, colour, licence, etc.).
No passive voice. No jargon without an inline explanation.
No generic affirmations ("perfect", "great question", "I now have the full picture").

---

## Section Structure by Task Type

**Development tasks:**
- Summary — what was done in one paragraph
- Changes Made — file paths, function names, what changed and why
- Test Results — pass/fail, which tests were run, which channels were tested
- Next Steps
- Decisions Needed
- Checklist

**Planning / architecture tasks:**
- Context — what we know and what is uncertain
- Proposal — the recommended approach with reasoning
- Tradeoffs — what we gain and what we give up
- Decisions Needed — what Saeed must approve or choose
- Next Steps

**Strategy / commercial tasks:**
- Situation — current state
- Recommendation — what to do and why
- Deadline or dependency — if time-critical, state it first
- Open Questions
- Next Steps

**Reports and documentation:**
- Overview — one paragraph summary
- Detail sections — labelled clearly
- Open Questions
- Next Steps

---

## Conditional Sections

These sections appear only when the relevant condition is met.

| Section | When it appears |
|---|---|
| RISK WARNING | Any task touching production files (C:\JeffLocal\dashboard\) |
| APPROVAL REQUIRED | Any production change, scope change, or new external dependency |
| Test Results | Any code change, however small |
| Architecture Detail | Only when Saeed explicitly asks for more depth |
| Compliance Note | Any task touching patient data, auth, or external communications |

---

## Length

- Default: concise summary with key points only.
- Extended: only when writing architecture docs, governance documents, or Saeed requests detail.
- Never pad a response. If the answer is two sentences, write two sentences.
- Token efficiency is a first-class concern — say more with less.

---

## Examples

Include realistic GP/dental triage scenarios regularly to keep responses grounded in project context. Scenarios should reflect real reception staff situations, not generic software examples.

Example format: "Mrs Ahmed (ID 4821) called requesting a repeat prescription for metformin — matched, no safety flags, priority: Routine."

Do not use real patient names, NHS numbers, or actual Churchtown staff data in any example.

---

## Endings

Every response — regardless of task type — ends with these four items:

1. **Next Steps** — what happens next, in order
2. **Decisions Needed** — what Saeed must approve or choose before work continues
3. **Open Questions** — anything unresolved that may affect the outcome
4. **Checklist** — discrete tasks to tick off

If any item has nothing to report, write "None" — do not omit the section.

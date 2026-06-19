# SKILL: Email via Outlook on Chrome — Avamed
# Trigger: Saeed asks Claude to send him something by email.

---

## When to Use

- Saeed explicitly asks Claude to email him a document, report, or summary
- Saeed asks Claude to send something to an external contact (requires extra confirmation)

## When NOT to Use

- Sending to anyone other than Saeed without his explicit written approval in chat
- Forwarding patient data, credentials, or files containing PII
- Any bulk or automated sending

---

## Safety Rules — Non-Negotiable

1. **Always confirm the To: address before composing.** Read the field header after opening a new message.
2. **Never send without Saeed confirming "send it" in chat.** Show the email summary and wait.
3. **Never attach files containing patient data, credentials, or API keys.**
4. **If any auto-complete suggests a wrong recipient, stop and tell Saeed.**

---

## Step-by-Step Process

1. Open Chrome and navigate to Outlook (outlook.office365.com or outlook.com — whichever Saeed uses).

2. Verify Saeed is signed in. If not, stop and tell him: "Outlook isn't open or signed in — please open it and I'll proceed."

3. Click **New Mail** (or equivalent compose button).

4. In the **To:** field, type Saeed's email address. **Read it back from the UI before proceeding.**

5. Fill in the **Subject** line with a clear, specific subject (no vague subjects like "Document" — use e.g. "Avamed — NHS SBS Draft Submission for Review").

6. Compose the body: plain text, professional UK English, no patient data, no credentials.

7. Attach any files if requested. Confirm each attachment name against what Saeed asked for.

8. **Show Saeed a summary in chat:**
   ```
   Ready to send:
   To: [email address confirmed from UI]
   Subject: [subject line]
   Attachment: [filename or "none"]
   Body preview: [first 2 sentences]

   Confirm: type "send it" to proceed.
   ```

9. Wait for Saeed to type "send it". Do not send until he does.

10. Click **Send**.

11. Confirm in chat: "Sent. Check your inbox."

---

## Output Format

```
EMAIL READY — [Subject]

To: [address]
Subject: [subject]
Attachment: [file or none]

[2-sentence body preview]

Awaiting your confirmation — type "send it" to proceed.
```

---

## Common Failure Modes

- **Auto-complete selecting wrong contact** — always read the resolved To: address from the UI, not just what was typed
- **Attaching wrong file** — confirm filename in the UI attachment bar before asking Saeed to confirm
- **Sending before confirmation** — never skip the confirmation step, even for trivial emails

---

## Success Criteria

1. Email arrives in Saeed's inbox (or specified recipient's) with the correct content.
2. No sensitive data was included without Saeed's explicit approval.
3. Saeed confirmed before sending.

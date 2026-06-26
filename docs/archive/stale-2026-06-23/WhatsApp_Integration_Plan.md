# JeffLocal — WhatsApp Business Integration Plan
**Owner:** Saeed (Avamed)  
**Created:** 2026-06-02  
**Status:** IN PROGRESS — Day 1  
**Target:** Fully functional WhatsApp intake channel at Churchtown Medical Centre

---

## 1. OBJECTIVE

Give patients an alternative to waiting on the phone. They message the surgery's WhatsApp number, Jeff handles the intake conversation, and the structured request lands on the reception dashboard — identical to the voice channel.

**This does NOT replace the voice agent.** It is an additional intake channel.

---

## 2. ARCHITECTURE

```
PATIENT (WhatsApp)
       │
       ▼
META CLOUD API (WhatsApp Business Platform)
       │  webhook POST (JSON event)
       ▼
n8n (localhost:5678)  ←── jefflocal-whatsapp-intake workflow
       │
       ├── Conversation state check (SQLite)
       │     ├── New patient → opt-in flow
       │     ├── Opted in, intake in progress → continue
       │     └── Complete → close session
       │
       ├── Ollama extract (same as voice pipeline)
       │
       ├── Patient match (Jeff.PatientMatch.ps1)
       │
       ├── Safety / emergency check
       │     └── Red flag → immediate WhatsApp reply + staff alert
       │
       └── Write handoff JSON → outputs/handoff_json/
                 │
                 ▼
         Dashboard importer (importer.py)
                 │
                 ▼
         Reception dashboard — task card with [WA] badge
```

**Reply path (Jeff → Patient):**
```
n8n → Meta Cloud API (POST /messages) → Patient WhatsApp
```

---

## 3. PHASE PLAN

### Phase 1 — Foundation (Day 1, no credentials needed)
- [x] Architecture document (this file)
- [ ] Meta setup guide for Saeed
- [ ] GDPR addendum
- [ ] Jeff conversation script (Python module)
- [ ] Conversation state manager (Python + SQLite)
- [ ] Webhook receiver endpoint (Flask route)
- [ ] n8n workflow JSON
- [ ] Patient opt-in flow
- [ ] Patient poster + waiting room content

### Phase 2 — Credentials & Wiring (requires Saeed action)
- [ ] Saeed completes Meta Business account setup
- [ ] Saeed provides: Phone Number ID, WABA ID, Access Token, Verify Token
- [ ] Configure n8n workflow with credentials
- [ ] Set webhook URL in Meta dashboard → n8n endpoint
- [ ] Test webhook verification (GET challenge)
- [ ] Test message receive (sandbox)

### Phase 3 — Integration Test
- [ ] Send real WhatsApp message from test phone
- [ ] Verify conversation flow (greeting → questions → confirmation)
- [ ] Verify handoff JSON written correctly
- [ ] Verify dashboard card appears with [WA] badge
- [ ] Verify emergency escalation path fires correctly
- [ ] Verify opt-in consent stored

### Phase 4 — Production Deployment (requires Saeed approval)
- [ ] Security Agent review
- [ ] Saeed approval for production deployment
- [ ] Configure production webhook URL (dashboard.app-avamed.uk/webhook/whatsapp)
- [ ] Register WhatsApp number with Meta for production
- [ ] Patient communication materials deployed (poster, digital screen)
- [ ] Staff briefing

---

## 4. COMPONENTS

### 4.1 Meta WhatsApp Cloud API
- **Cost:** Free for first 1,000 user-initiated conversations/month. ~$0.05–0.08/conversation after that. For a GP surgery at ~200 calls/day this is negligible.
- **Phone number:** Dedicated virtual UK number recommended (e.g., via Vonage/Twilio virtual number ported to Meta). Cost ~£3–5/month.
- **Webhook:** Meta sends POST events to your URL on every incoming message. You verify ownership via a GET challenge.
- **Rate limits:** 1,000 messages/24h on free tier. Sufficient for pilot.

### 4.2 Jeff Conversation Flow (WhatsApp)
```
Stage 0 — Opt-in check
  First contact → send consent + privacy notice → wait for YES

Stage 1 — Greeting
  "Hi, I'm Jeff, the virtual assistant at [Surgery Name].
   I can take your appointment request so you don't have to wait on the phone.
   What's your full name and date of birth?"

Stage 2 — Reason for contact
  "Thank you [Name]. What's the reason for your contact today?"

Stage 3 — Duration / clarification
  "How long have you had this? (e.g. a few days, a week, longer)"

Stage 4 — Urgency check
  If red-flag keywords detected → immediate escalation message + 999/111
  Otherwise → "Is there anything else you'd like the doctor to know?"

Stage 5 — Confirmation
  "Thank you. Your request has been passed to the reception team.
   They'll contact you to book an appointment. 
   If your condition worsens urgently, call 999 or 111."
```

**Emergency override (any stage):**  
If message contains: chest pain, can't breathe, unconscious, stroke, severe bleeding, suicidal → immediate reply:  
> "⚠️ This sounds urgent. Please call 999 immediately or go to A&E. Do not wait for a callback."  
AND write an emergency-flagged handoff to dashboard.

### 4.3 Patient Opt-in Flow
- Patient texts ANY message to the surgery WhatsApp number
- Jeff replies with consent message including link to Privacy Notice
- Patient must reply "YES" (case-insensitive) to proceed
- Consent stored in `whatsapp_consents` table with timestamp and phone hash
- If patient replies anything other than YES: prompt once more, then end session
- Opted-in patients skip this step on future contacts (within 12 months)

### 4.4 Conversation State (SQLite table: whatsapp_sessions)
```sql
CREATE TABLE whatsapp_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_hash TEXT NOT NULL,          -- SHA-256 of phone number (no PII in DB)
    wa_message_id TEXT,                -- Meta message ID for threading
    stage INTEGER DEFAULT 0,           -- 0=opt-in, 1=greeting, 2=reason, etc.
    collected_data TEXT,               -- JSON blob of extracted fields so far
    opted_in INTEGER DEFAULT 0,        -- 1 = consent confirmed
    opt_in_timestamp TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    last_activity TEXT DEFAULT (datetime('now')),
    status TEXT DEFAULT 'active'       -- active | complete | abandoned | escalated
);
```

### 4.5 Webhook Endpoint (Flask)
- `GET /webhook/whatsapp` — Meta verification challenge
- `POST /webhook/whatsapp` — Incoming message handler
- Validates `X-Hub-Signature-256` header (same HMAC pattern as n8n webhook)
- Extracts message, routes to conversation manager
- Returns 200 immediately (Meta requires fast response; async processing)

### 4.6 n8n Workflow
- **Trigger:** Webhook node (jefflocal-whatsapp-intake)
- **Node 1:** Extract phone, message body, message ID from Meta payload
- **Node 2:** HTTP Request → Flask `/internal/whatsapp/process` (conversation state + Ollama)
- **Node 3:** If complete → write handoff JSON to outputs/handoff_json/
- **Node 4:** HTTP Request → Meta API `/messages` to send Jeff's reply back

### 4.7 Dashboard Channel Badge
- `source_channel` field added to handoff JSON (`"whatsapp"` vs `"voice"`)
- Dashboard importer reads and stores this field
- Task cards show green `WA` pill badge if source = whatsapp
- Existing voice cards unchanged

---

## 5. GDPR / NHS COMPLIANCE

See: `governance/WHATSAPP_GDPR_ADDENDUM.md` (full detail)

**Summary:**
- Meta acts as a Data Processor — DPA must be in place (Meta provides standard DPA)
- Patient phone number hashed in local DB — never stored in plain text
- Conversation content purged per existing 90-day GDPR purge schedule
- Patient opt-in consent recorded with timestamp
- Privacy Notice must be updated to name WhatsApp as an intake channel
- WhatsApp is opt-in only — never mandatory

---

## 6. WHAT SAEED MUST DO (cannot be automated)

### Step 1 — Meta Business Account (Day 1–2)
See full guide: `docs/project_documents/Meta_WhatsApp_Setup_Guide.md`

1. Go to https://business.facebook.com → create/verify business account
2. Go to https://developers.facebook.com → create new app → add WhatsApp product
3. Add a phone number (test number available free, or register a real UK number)
4. Generate a permanent System User Access Token
5. Note down: Phone Number ID, WhatsApp Business Account ID, Access Token

### Step 2 — Provide credentials to Claude
Once Step 1 is done, send Claude these values:
```
PHONE_NUMBER_ID = 
WABA_ID = 
ACCESS_TOKEN = 
WEBHOOK_VERIFY_TOKEN = (you choose this — any random string)
```

### Step 3 — Point webhook at your server
In Meta Developer console → WhatsApp → Configuration → Webhook:
```
URL: https://dashboard.app-avamed.uk/webhook/whatsapp
Verify Token: (same as above)
Subscribe to: messages
```

---

## 7. CREDENTIALS STORAGE

Credentials stored in `.env` file (never committed to git):
```
WA_PHONE_NUMBER_ID=
WA_ACCESS_TOKEN=
WA_WEBHOOK_VERIFY_TOKEN=
WA_API_VERSION=v19.0
```

The `.env` file is already in `.gitignore`. Do NOT paste credentials into chat.

---

## 8. TEST PLAN

| Test | Method | Pass Criteria |
|------|--------|---------------|
| Webhook verification | GET challenge from Meta | 200 + challenge echoed |
| Opt-in flow | Send test message from personal phone | Consent prompt received |
| Intake flow | Complete conversation | Handoff JSON written |
| Dashboard card | Check dashboard after intake | Card appears with WA badge |
| Emergency escalation | Send "chest pain" | Immediate 999 reply, escalated card |
| Opt-in skip | Second message from same number | No consent prompt shown |
| GDPR purge | Run purge with --dry-run | WA sessions included in purge scope |

---

## 9. ROLLBACK PLAN

- All WhatsApp code is additive — no existing routes or DB tables modified
- `WA_ENABLED=false` env flag disables the webhook handler with no code change
- Conversation sessions table can be dropped without affecting existing dashboard data

---

*Last updated: 2026-06-02 | Author: Claude (Cowork)*

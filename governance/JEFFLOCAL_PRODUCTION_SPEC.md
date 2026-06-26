# JeffLocal — Production Project Specification
## Claude Cowork Specialist Agent Handbook

**Version:** 1.0 — 2026-05-22  
**Status:** Pilot Phase (single practice) → Multi-practice roadmap  
**Practice:** Churchtown Medical Centre, Southport  
**Author:** Generated from live codebase and sprint history

---

## 1. What Is JeffLocal?

JeffLocal is a local-first GP reception workflow system. It intercepts inbound patient calls via a voice agent (Jeff), extracts structured intake data, matches patients against practice records, and delivers a verified handoff task to reception staff — before a human has touched the call.

**The problem it solves:**  
UK GP receptions are overwhelmed with inbound calls. Staff spend 30–60% of call time taking notes, confirming identity, and routing requests. JeffLocal automates that entire intake loop, leaving staff with a structured, verified task rather than a raw note.

**The safety contract:**  
Ollama (local LLM) extracts and drafts. Deterministic PowerShell code verifies, matches, validates, and finalises. LLM output **never** overrides verified EMIS/NHS/patient data. Every safety decision is deterministic.

---

## 2. System Architecture

```
[Patient Phone Call]
        │
        ▼
┌─────────────────────┐
│   JEFF VOICE AGENT  │  ← Dept VAI manages
│   (External / 3P)   │
│  - Structured convo │
│  - Encrypts payload │
│  - Sentiment track  │
└────────┬────────────┘
         │  HMAC-signed encrypted JSON
         ▼
┌─────────────────────┐
│   n8n INTAKE ROUTER │  ← Dept IR manages
│   port 5678         │
│  - Webhook receiver │
│  - Payload validate │
│  - Queue ingest     │
└────────┬────────────┘
         │  queue/encrypted_raw/*.json
         ▼
┌─────────────────────┐
│  PS1 PIPELINE       │  ← Dept PE manages
│  process_queue.ps1  │
│  - Decrypt & norm   │
│  - Ollama extract   │  → Ollama port 11434
│  - Patient match    │  → mock_patient_lookup_v1.csv
│  - Emergency scan   │
│  - Handoff build    │
└────────┬────────────┘
         │  outputs/handoff_json/*_handoff.json
         ▼
┌─────────────────────┐
│  STAFF DASHBOARD    │  ← Dept DX manages
│  FastAPI port 8765  │
│  - Case management  │
│  - Auth & sessions  │
│  - Staff workflow   │
│  - Import / review  │
└────────┬────────────┘
         │  (future)
         ▼
┌─────────────────────┐
│  EMIS / NHS         │  ← Dept ENI manages (INACTIVE)
│  PAD integration    │
│  - Patient verify   │
│  - Record update    │
└─────────────────────┘

Cross-cutting:
  Dept SC  — Security & Compliance (all layers)
  Dept ID  — Infrastructure & DevOps (all services)
  Dept QA  — Quality Assurance (all departments)
  Dept PO  — Practice Operations (onboarding & config)
```

---

## 3. Department Index

| Code | Department | Phase | Status |
|------|-----------|-------|--------|
| VAI | Voice Agent Integration | 1 | Active |
| IR | Intake & Routing | 1 | Active |
| PE | Pipeline Engineering | 1 | Active |
| DX | Dashboard & UX | 1 | Active |
| SC | Security & Compliance | 1 | Active |
| ID | Infrastructure & DevOps | 1 | Active |
| QA | Quality Assurance | 1 | Active |
| ENI | EMIS & NHS Integration | 2 | **Inactive — do not build until activated** |
| PO | Practice Operations | 1→2 | Active (single practice), expands Phase 2 |

---

## 4. Core Technical Facts (read before starting any department)

| Item | Value |
|------|-------|
| Dashboard port | 8765 |
| n8n port | 5678 |
| Ollama port | 11434 |
| Active model | gemma4:e2b |
| Fallback model | gemma4:e4b (only if monitoring score < 0.72) |
| DB | `dashboard/data/dashboard.sqlite` (SQLite, unencrypted at rest) |
| Patient lookup | `data/patient_lookup/mock_patient_lookup_v1.csv` |
| Auth | PBKDF2-HMAC-SHA256, session tokens, PIN login, 5-attempt lockout, 60-min sliding expiry |
| Queue stages | `encrypted_raw` → `incoming` → `processing` → `processed` / `failed` / `deadletter` |
| Handoff output | `outputs/handoff_json/*_handoff.json` |
| Backup | `backup/restore_points/` (keep last 3, archive older) |
| Pathways | prescription, sick_note, referral, test_result, appointment, admin, medication_query, unknown |
| Test prefix | `N8NTEST-` (all test call IDs must use this prefix) |
| Shell | PowerShell 5.1 (no `&&` chains, no inline `if` in string concat, no em-dashes in literals) |
| Python | 3.14, venv at `dashboard/.venv/` |

---

## 5. Department Specifications

---

### [VAI] Voice Agent Integration

**Status:** Active  
**Expert Role:** Voice AI Integration Engineer  
**One-line purpose:** Owns the Jeff voice agent boundary — everything from call receipt to encrypted payload delivery.

#### What VAI Owns
- Jeff voice agent conversation flow design (prompt structure, pathway branching, summary read-back)
- Encryption key management (RSA public key at `config/security/keys/jefflocal_public.pem`)
- HMAC signing (`config/security/keys/voice_agent_hmac_secret.txt`)
- Payload schema (`normalized_input`, `pathway_responses`, `voice_agent` metadata blocks)
- Sentiment tracking fields (`caller_sentiment`, `caller_difficulty`, `transcript_quality`)
- Performance tracking (call duration, extraction confidence, handoff confidence)
- Jeff prompt instructions and pathway scripts

#### Current State
- Encryption: RSA key pair generated, public key deployed to voice agent
- Payload schema: defined in `tests/fixtures/live_lookup_test_payloads.py` and `n8n_webhook_test_pack.py`
- Sentiment fields: present in schema (`calm`, `concerned`, `distressed`, `uncertain`)
- Confidence fields: `handoff_confidence`, `extraction_confidence` (0.0–1.0)
- Jeff conversation flow: covers all 8 pathways (prescription, sick_note, referral, test_result, appointment, admin, medication_query, unknown)
- Third-party call handling: `caller_for` field (self / relative / carer / other)
- Red-flag detection: urgency assessment block with `red_flags_mentioned[]`, `emergency_advice_given`, `transfer_offered`

#### Production Gap
- [ ] Jeff prompt scripts not version-controlled in this repo — need a `config/jeff_prompts/` directory
- [ ] No voice agent performance dashboard (call success rate, avg duration, confidence trends)
- [ ] Encryption key rotation procedure not documented
- [ ] No dead-call handling (call dropped mid-intake — partial payload schema undefined)
- [ ] Sentiment scoring is string-only; needs numeric scale for trend analysis
- [ ] No callback number validation at Jeff level (currently accepts any format)

#### Key Files
```
config/security/keys/jefflocal_public.pem
config/security/keys/voice_agent_hmac_secret.txt
config/security/jeie_v1.config.json
tests/fixtures/live_lookup_test_payloads.py    ← payload builder + encrypt_envelope()
tests/fixtures/n8n_webhook_test_pack.py        ← n8n batch builder
app/run_intake.ps1                             ← local intake entry point
```

#### Task Breakdown

**Priority 1 — Blocking for production**
- [ ] VAI-01: Create `config/jeff_prompts/` with versioned prompt scripts for all 8 pathways
- [ ] VAI-02: Define and document partial/dropped-call payload schema (mid-call disconnects)
- [ ] VAI-03: Document encryption key rotation procedure (new key → re-deploy to Jeff → drain old queue)
- [ ] VAI-04: Add numeric confidence thresholds to Jeff prompt — below 0.75 extraction confidence must flag `staff_review_required: true`

**Priority 2 — Core production quality**
- [ ] VAI-05: Add callback number normalisation at Jeff level (strip spaces, validate UK mobile/landline format)
- [ ] VAI-06: Build voice agent performance tracking endpoint (`/api/voice-agent/metrics`) — avg confidence, call duration, sentiment distribution, pathway split
- [ ] VAI-07: Version-stamp all payloads with `schema_version` field for forward compatibility

**Priority 3 — Polish**
- [ ] VAI-08: Add per-pathway conversation analytics (avg duration, completion rate, redirect rate)
- [ ] VAI-09: Create Jeff prompt A/B testing framework for conversation optimisation

#### Acceptance Criteria
- All 8 pathways produce valid encrypted payloads that pass `encrypt_envelope()` without error
- Dropped calls produce a recoverable partial payload (not a silent failure)
- Encryption key can be rotated without dropping in-flight calls
- Confidence < 0.75 always sets `staff_review_required: true`

#### Agent Briefing (cold-start context)
> You are the Voice Agent Integration Engineer for JeffLocal. Your boundary is everything from the patient picking up the phone to an encrypted JSON payload arriving at the n8n webhook. You do not own the pipeline (that's PE) or the intake router (that's IR). Your primary artefacts are the Jeff prompt scripts, the encryption keys, and the payload schema. The payload schema is the contract between you and IR — any changes you make must be backward-compatible or coordinated with IR and PE simultaneously.

---

### [IR] Intake & Routing

**Status:** Active  
**Expert Role:** Integration & Routing Engineer  
**One-line purpose:** Owns the n8n layer — payload receipt, validation, queue ingest, and routing to the PS1 pipeline.

#### What IR Owns
- n8n workflow "JeffLocal - 06 Test Intake Webhook" (workflow ID: `0pRmm3xCHP4wsVyy`)
- Webhook endpoint configuration (`POST /webhook/ava-live-intake` on port 5678)
- Payload validation before queue write
- Queue write logic (`queue/encrypted_raw/`)
- Dashboard intake API (`/api/n8n/test-intake-batch` — test/sandbox only, marked deprecated)
- Batch processing and `refresh_artifacts` logic
- Google Sheets push toggle (`google_sheet_enabled` in `config/app_settings.json`)

#### Current State
- n8n webhook active and receiving on port 5678
- Workflow makes HTTP Request to dashboard's `/api/n8n/test-intake-batch` endpoint
- Endpoint requires `/api/n8n/` prefix to be in `AUTH_PUBLIC_PREFIXES` (fixed 2026-05-22)
- Test mode: batch_id must start with `N8NTEST-` or `GPDEMO-`
- Full batch response includes: processed count, handoff count, failed count, dashboard import count
- Archive/regeneration: previous N8NTEST artifacts are archived before each batch run

#### Production Gap
- [ ] IR-01: The `/api/n8n/test-intake-batch` endpoint bypasses n8n — production must route ALL calls through n8n (this endpoint is deprecated and must be removed before go-live)
- [ ] IR-02: n8n workflow currently has "Response Format" sensitivity — HTTP Request node must handle non-JSON responses gracefully (fixed in dashboard, but n8n node config needs hardening)
- [ ] IR-03: No payload signature (HMAC) verification in n8n workflow — Jeff sends HMAC but n8n doesn't verify it before writing to queue
- [ ] IR-04: No dead-letter handling at n8n level — failed payloads are silently dropped
- [ ] IR-05: Google Sheets push is mock/disabled — production requires either activation or formal deprecation
- [ ] IR-06: n8n workflow has no retry logic for transient dashboard failures
- [ ] IR-07: API key authentication needed for n8n → dashboard HTTP Request (currently relies on public prefix exemption)

#### Key Files
```
~/.n8n/database.sqlite                         ← n8n workflow and execution store
~/.n8n/n8nEventLog.log                         ← execution audit trail
config/app_settings.json                       ← queue paths, google_sheet_enabled
dashboard/app/main.py                          ← /api/n8n/test-intake-batch endpoint
scripts/service_control/_launch_n8n.ps1        ← n8n launch script
logs/n8n_audit_20260522.txt                    ← n8n execution audit
```

#### Task Breakdown

**Priority 1 — Blocking for production**
- [ ] IR-01: Implement HMAC verification in n8n workflow (before queue write, reject invalid signatures)
- [ ] IR-02: Add machine-to-machine API key to dashboard for n8n → `/api/n8n/` calls (replace public prefix exemption with proper key auth)
- [ ] IR-03: Add dead-letter write to n8n workflow — failed payloads write to `queue/deadletter/` with error context
- [ ] IR-04: Remove `/api/n8n/test-intake-batch` bypass endpoint before production (or gate it behind feature flag)

**Priority 2 — Core production quality**
- [ ] IR-05: Add n8n retry logic (3 retries with 2s back-off on 5xx dashboard responses)
- [ ] IR-06: Build n8n execution monitoring endpoint (`/api/intake/status`) — last execution time, success/failure rate
- [ ] IR-07: Add payload size limit (reject > 500KB — protects against malformed payloads)

**Priority 3 — Polish**
- [ ] IR-08: Google Sheets push: either implement fully or remove all references from codebase
- [ ] IR-09: Add n8n execution summary to dashboard health widget (last n8n execution time and status)

#### Acceptance Criteria
- HMAC-invalid payloads are rejected at n8n level, never reaching the queue
- n8n → dashboard communication is authenticated via API key, not public prefix
- All intake paths produce a queue file or a dead-letter entry — no silent drops
- The bypass endpoint does not exist in production code

#### Agent Briefing (cold-start context)
> You are the Intake & Routing Engineer. Your boundary is the n8n layer — from webhook receipt to a validated file in `queue/encrypted_raw/`. You do not own the voice agent (that's VAI) or what happens after the file is written (that's PE). Your primary artefact is the n8n workflow. The n8n workflow database is at `~/.n8n/database.sqlite`. n8n is on port 5678. The dashboard that IR calls is on port 8765. The HMAC secret for payload verification is at `config/security/keys/voice_agent_hmac_secret.txt`.

---

### [PE] Pipeline Engineering

**Status:** Active  
**Expert Role:** Pipeline & AI Integration Engineer  
**One-line purpose:** Owns the PS1 processing pipeline — decryption, Ollama extraction, patient matching, emergency override, and handoff JSON generation.

#### What PE Owns
- `app/process_queue.ps1` — main queue processor
- `app/modules/` — all Jeff.* modules (Common, PatientMatch, Validation, RequestType, Handoff, StaffSummary, Emergency)
- `app/call_ollama.ps1` — Ollama API caller
- `app/detect_flags.ps1` — red-flag detector
- `app/generate_staff_summary.ps1` — staff summary generator
- `app/build_handoff.ps1` — handoff JSON builder
- `app/run_intake.ps1` — encrypted intake entry point
- Queue stage management (encrypted_raw → incoming → processing → processed/failed/deadletter)
- Ollama model configuration and monitoring (confidence thresholds, fallback model)
- Patient matching logic (EMIS lookup CSV)
- Emergency override scan (post-handoff safety check)

#### Current State
- All 8 pathways defined and routed
- Patient matching: name + DOB + optional NHS/postcode, fuzzy match with confidence scoring
- Ollama: `gemma4:e2b`, fallback to `gemma4:e4b` if score < 0.72
- Emergency scan runs post-handoff as final safety layer
- Queue: file-based, atomic write-then-move between stages
- Handoff JSON: flat schema (`call_id`, `patient_name`, `dob`, `request_type`, `priority`, `medications`, etc.)
- Medication deduplication: normalises drug names before dedup check
- Request type classifier: heuristic rules + Ollama confirmation

#### Production Gap
- [ ] PE-01: Schema migration — current flat schema needs additive nested fields (`meta`, `call`, `intake`, `patient`, `caller`, `details`, `safety`, `outputs`, `monitoring`) while keeping flat fields for backward compat
- [ ] PE-02: Pathway activation audit — sick_note and referral pathways need end-to-end tracing with real transcripts (prescription is the only confirmed-live pathway)
- [ ] PE-03: `config/model_settings.json` missing — Ollama model name/temperature currently hardcoded in PS1 scripts
- [ ] PE-04: `config/pathways.json` missing — active pathway list hardcoded; needs externalised config
- [ ] PE-05: `config/routing_rules.json` missing — staff assignment routing logic not externalised
- [ ] PE-06: `config/model_monitoring.json` missing — confidence floor and alert escalation rules not externalised
- [ ] PE-07: Queue deadletter items (5 currently) need investigation and replay tooling
- [ ] PE-08: No replay/retry mechanism for failed queue items without manual intervention
- [ ] PE-09: Ollama raw output (`outputs/ollama_raw/`) has no retention policy (GDPR risk)

#### Key Files
```
app/process_queue.ps1                     ← main processor (entry point)
app/run_intake.ps1                        ← encrypted intake
app/call_ollama.ps1                       ← Ollama API
app/build_handoff.ps1                     ← handoff JSON builder
app/modules/Jeff.Common.ps1
app/modules/Jeff.PatientMatch.ps1         ← patient matching logic
app/modules/Jeff.RequestType.ps1          ← request type classifier
app/modules/Jeff.Validation.ps1
app/modules/Jeff.Emergency.ps1            ← post-handoff emergency override
app/modules/Jeff.Handoff.ps1
app/modules/Jeff.StaffSummary.ps1
app/detect_flags.ps1
app/generate_staff_summary.ps1
data/patient_lookup/mock_patient_lookup_v1.csv
config/app_settings.json                  ← queue paths, model settings (partial)
outputs/handoff_json/                     ← output handoffs (no retention policy)
outputs/ollama_raw/                       ← Ollama raw responses (GDPR risk)
queue/deadletter/                         ← 5 items need investigation
```

#### Task Breakdown

**Priority 1 — Blocking for production**
- [ ] PE-01: Create `config/model_settings.json` — externalise model name, temperature, timeout, confidence floor
- [ ] PE-02: Create `config/pathways.json` — externalise active pathway list with per-pathway routing rules
- [ ] PE-03: Create `config/routing_rules.json` — staff assignment rules per pathway and priority level
- [ ] PE-04: Create `config/model_monitoring.json` — confidence thresholds, alert escalation rules, fallback trigger
- [ ] PE-05: Implement schema migration — additive nested fields alongside flat schema (backward-compatible)
- [ ] PE-06: Investigate and document all 5 deadletter items — build `app/replay_deadletter.ps1`

**Priority 2 — Core production quality**
- [ ] PE-07: Pathway activation audit — trace sick_note and referral transcripts end-to-end (use `tests/send_fresh_20260521_test.py` batch which covers all pathways)
- [ ] PE-08: Add queue replay tooling (failed → re-queue with attempt counter, max 3 retries)
- [ ] PE-09: Add 90-day retention purge for `outputs/ollama_raw/` (GDPR — plain-text patient data)
- [ ] PE-10: Add structured logging to pipeline (currently logs to flat text files)

**Priority 3 — Polish**
- [ ] PE-11: Pipeline performance metrics — avg processing time per pathway, Ollama latency, match rate
- [ ] PE-12: Build `app/validate_handoff.ps1` — post-pipeline handoff JSON schema validator

#### Acceptance Criteria
- All 8 pathways produce valid handoff JSON with no unhandled exceptions
- `config/model_settings.json`, `pathways.json`, `routing_rules.json`, `model_monitoring.json` all exist and are loaded at startup
- Deadletter items have documented root cause and replay procedure
- Schema migration is additive — existing handoff JSONs load without error after migration
- `outputs/ollama_raw/` has automated 90-day purge

#### Agent Briefing (cold-start context)
> You are the Pipeline Engineer. You own everything that happens after a file lands in `queue/encrypted_raw/` and before a handoff JSON appears in `outputs/handoff_json/`. The pipeline is PowerShell 5.1 — no `&&` chains, no inline `if` in string concat. Ollama is on port 11434, model `gemma4:e2b` (run `ollama list` before changing). The safety rule is absolute: Ollama extracts and drafts, deterministic PS1 code verifies. LLM output never overrides verified patient data. The four missing config files (model_settings, pathways, routing_rules, model_monitoring) are your first priority — they're currently hardcoded in PS1 scripts.

---

### [DX] Dashboard & UX

**Status:** Active  
**Expert Role:** Full-Stack Dashboard Engineer  
**One-line purpose:** Owns the staff-facing dashboard — FastAPI backend, Jinja2 templates, auth system, and all staff workflow UX.

#### What DX Owns
- `dashboard/app/main.py` — FastAPI application (~3500 lines)
- `dashboard/app/models.py` — data models
- `dashboard/app/db.py` — SQLite database, `init_db()`, migrations
- `dashboard/app/auth.py` — auth module (PBKDF2, sessions, lockout, PIN)
- `dashboard/app/importer.py` — handoff JSON importer
- `dashboard/templates/` — all Jinja2 templates
- `dashboard/static/dashboard.css` — all styles
- All dashboard API endpoints
- Case management workflow (New → In Progress → Resolved)
- Staff workload tracking
- Service health widget
- Import mechanism

#### Current State (as of 2026-05-22)
- Auth: session-based, PBKDF2-HMAC-SHA256, PIN login, 5-attempt lockout, 60-min sliding expiry
- Templates: `base.html`, `index.html`, `case_detail.html`, `settings.html`, `staff.html`, `profile.html`, `login.html`, `forgot.html`
- Import button: topbar, AJAX call to `/api/import`, triggers `playNewCaseBeep()` on success
- Staff workload widget: live per-staff open/in_progress/resolved_today, AJAX refresh 60s
- Audio: double-beep on import, triple-pulse alarm on service failure
- Side panel: collapsible analytics sidebar with icon rail in collapsed state, localStorage persistence
- Settings page: config file cards with status badges, diagnostics grid, connected services
- Staff page: avatar cards, role badges (admin=amber, staff=blue, readonly=gray), collapsible edit forms
- Case detail: "Call age" label, correct nav highlight ("Requests" active on case detail)
- Auth public paths: `/login`, `/logout`, `/forgot`, `/reset`, `/favicon.ico`, `/static/`, `/api/health`, `/api/n8n/`, `/api/alerts/`

#### Production Gap
- [ ] DX-01: Password reset flow (`/forgot`, `/reset`) — templates exist but flow not fully tested
- [ ] DX-02: `profile.html` — must-change-password flow exists but profile update (email, display name, PIN change) not implemented
- [ ] DX-03: Session purge runs only at login — needs daily scheduled call to `purge_expired_sessions()`
- [ ] DX-04: `/patients` and `/reports` nav links have no routes (404)
- [ ] DX-05: "Last import: Never" on Settings diagnostics even after imports — `last_import_at` tracking not updating
- [ ] DX-06: Case bulk actions (assign, resolve eligible) need end-to-end testing
- [ ] DX-07: No pagination on the cases list — large practice will produce hundreds of cases
- [ ] DX-08: Search/filter on requests list needs performance testing at scale (100+ cases)
- [ ] DX-09: No audit trail UI — `audit` tab on case detail exists but content not fully implemented
- [ ] DX-10: Dashboard runs SQLite without connection pooling — needs review for concurrent staff users

#### Key Files
```
dashboard/app/main.py                     ← FastAPI app (entry point)
dashboard/app/auth.py                     ← auth module
dashboard/app/db.py                       ← init_db(), migrations
dashboard/app/models.py
dashboard/app/importer.py
dashboard/templates/base.html            ← topbar, sidebar, nav, audio
dashboard/templates/index.html           ← main dashboard (cases + workload)
dashboard/templates/case_detail.html     ← case detail view
dashboard/templates/settings.html        ← settings page
dashboard/templates/staff.html           ← staff management
dashboard/templates/profile.html         ← user profile
dashboard/templates/login.html
dashboard/static/dashboard.css
dashboard/data/dashboard.sqlite          ← live database
```

#### Task Breakdown

**Priority 1 — Blocking for production**
- [ ] DX-01: Implement and test full password reset flow (forgot → email token → reset form → confirm)
- [ ] DX-02: Add daily session purge to scheduled tasks (`purge_expired_sessions()` currently only runs at login)
- [ ] DX-03: Implement `/patients` route — patient lookup view (read-only for now, EMIS integration Phase 2)
- [ ] DX-04: Fix "Last import: Never" — update `last_import_at` in dashboard settings/diagnostics on each import
- [ ] DX-05: Add cases list pagination (50 per page, page controls, URL params)

**Priority 2 — Core production quality**
- [ ] DX-06: Implement `/reports` route — basic daily/weekly summary view
- [ ] DX-07: Build audit trail UI on case detail Audit tab (who changed what, when)
- [ ] DX-08: Profile page: implement PIN change and display name update
- [ ] DX-09: Performance test cases list with 500+ rows — add DB index on `status`, `call_timestamp`
- [ ] DX-10: Add SQLite WAL mode and connection timeout handling for concurrent users

**Priority 3 — Polish**
- [ ] DX-11: Add keyboard shortcuts for common staff actions (start review, resolve)
- [ ] DX-12: Mobile responsive review of case detail page
- [ ] DX-13: Add case export (CSV) for practice manager reporting

#### Acceptance Criteria
- Password reset flow works end-to-end without manual DB intervention
- `/patients` and `/reports` return valid pages (not 404)
- Expired sessions are purged daily by scheduler
- Cases list performs under 200ms with 500 rows
- All Audit tab entries for a case show correct timestamps and actor

#### Agent Briefing (cold-start context)
> You are the Dashboard Engineer. Your codebase is in `dashboard/`. FastAPI app is `dashboard/app/main.py` (~3500 lines). Templates are Jinja2 in `dashboard/templates/`. The SQLite DB is at `dashboard/data/dashboard.sqlite`. Auth is session-based — the auth middleware is `enforce_auth` in `main.py` around line 89. Public paths are in `AUTH_PUBLIC_PATHS` and `AUTH_PUBLIC_PREFIXES`. The dashboard runs on port 8765. Python venv is at `dashboard/.venv/`. Do not break the auth middleware — it protects all routes. Do not add new routes without checking if they need auth.

---

### [SC] Security & Compliance

**Status:** Active  
**Expert Role:** Security & GDPR Compliance Engineer  
**One-line purpose:** Owns security posture, data protection, audit logging, and GDPR compliance across all layers.

#### What SC Owns
- Encryption key management (`config/security/keys/`)
- HMAC signing and verification
- Session token security (PBKDF2, token entropy, lockout policy)
- GDPR data retention policies
- Audit logging (all changes to patient data, case status changes)
- Data minimisation (what gets stored, where, how long)
- SQLite encryption at rest (currently unencrypted — acceptable for local pilot, not for production)
- Secret scanning and `.gitignore` policy
- Nonce store (`config/security/nonce_store.json`) — replay attack prevention

#### Current State
- Encryption: RSA public/private key pair in `config/security/keys/`
- Auth: PBKDF2-HMAC-SHA256, 100,000 iterations, session tokens (32 bytes), 60-min sliding expiry
- Lockout: 5 failed attempts → 15-minute lockout
- HMAC: voice agent payload signing with `voice_agent_hmac_secret.txt`
- Audit: case status changes logged, but no centralised audit table in DB
- GDPR gap: `outputs/handoff_json/`, `queue/processed/`, `outputs/ollama_raw/` contain plain-text patient data with no retention policy
- GDPR gap: `purge_expired_sessions()` runs only at login (not scheduled)
- `.gitignore`: private keys and config/security excluded from version control
- DB: SQLite unencrypted at rest (local pilot — acceptable; production requires encrypted volume)

#### Production Gap
- [ ] SC-01: Implement 90-day automated purge for `outputs/handoff_json/`, `queue/processed/`, `outputs/ollama_raw/` (GDPR — currently only queue/processed has a purge script)
- [ ] SC-02: Add centralised audit table to SQLite (`audit_log`: timestamp, user_id, action, entity_type, entity_id, old_value, new_value)
- [ ] SC-03: Implement nonce-based replay attack prevention for HMAC-signed payloads (nonce_store.json exists but verification not enforced)
- [ ] SC-04: SQLite encryption at rest — implement encrypted volume or SQLCipher before multi-practice Phase 2
- [ ] SC-05: Secret rotation procedure for voice agent HMAC key (currently no documented rotation process)
- [ ] SC-06: Add `Content-Security-Policy` and `X-Frame-Options` headers to dashboard responses
- [ ] SC-07: Rate limiting on login endpoint (brute force beyond 5-attempt lockout)
- [ ] SC-08: Data processing agreement template for new practices (GDPR Article 28)

#### Key Files
```
config/security/keys/jefflocal_private.pem
config/security/keys/jefflocal_public.pem
config/security/keys/voice_agent_hmac_secret.txt
config/security/jeie_v1.config.json
config/security/nonce_store.json
dashboard/app/auth.py                        ← auth module
dashboard/app/main.py                        ← enforce_auth middleware
app/purge_old_data.ps1                       ← partial retention script
logs/audits/                                 ← audit log directory
```

#### Task Breakdown

**Priority 1 — Blocking for production**
- [ ] SC-01: 90-day purge for ALL patient data directories (expand `purge_old_data.ps1` to cover `outputs/handoff_json/` and `outputs/ollama_raw/`)
- [ ] SC-02: Add `audit_log` table to SQLite and write audit entries for: case status changes, staff account changes, login events, import events
- [ ] SC-03: Enforce nonce verification on all incoming HMAC-signed payloads (prevent replay)
- [ ] SC-04: Add HTTP security headers to all dashboard responses (`Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`)
- [ ] SC-05: Rate limiting on `/login` — max 10 attempts per IP per 15 minutes (beyond per-account lockout)

**Priority 2 — Core production quality**
- [ ] SC-06: Document and test HMAC key rotation procedure
- [ ] SC-07: Add `Secure` and `HttpOnly` flags to session cookie in production mode
- [ ] SC-08: Build GDPR data subject access request (SAR) export — all data held for a patient by NHS number

**Priority 3 — Polish (Phase 2 pre-requisites)**
- [ ] SC-09: SQLite → encrypted volume migration path documented
- [ ] SC-10: Draft Data Processing Agreement template for practice onboarding
- [ ] SC-11: Add IP allowlist option for dashboard access in production config

#### Acceptance Criteria
- Patient data in `outputs/handoff_json/` and `outputs/ollama_raw/` is purged after 90 days by scheduler
- All case status changes produce an `audit_log` entry
- Replayed (duplicate nonce) payloads are rejected before queue write
- HTTP security headers present on all non-API dashboard responses
- Session cookie has `HttpOnly` flag in production

#### Agent Briefing (cold-start context)
> You are the Security & Compliance Engineer. You own everything related to data protection, encryption, and audit. The most urgent GDPR risk: `outputs/handoff_json/` and `outputs/ollama_raw/` contain plain-text patient data with no retention policy. The partial purge script at `app/purge_old_data.ps1` covers only the queue. The nonce store at `config/security/nonce_store.json` exists but nonce verification is not enforced in the pipeline. The auth module is at `dashboard/app/auth.py`. Do not change the PBKDF2 iteration count or salt values — that would break all existing password hashes.

---

### [ID] Infrastructure & DevOps

**Status:** Active  
**Expert Role:** Infrastructure & DevOps Engineer  
**One-line purpose:** Owns service reliability, scheduled automation, backups, and multi-practice infrastructure planning.

#### What ID Owns
- Watchdog (`scripts/service_control/watchdog.ps1`) — crash recovery for dashboard and n8n
- Health monitor (`scripts/service_control/health_monitor.ps1`) — deep service health checks
- Service launchers (`_launch_dashboard.ps1`, `_launch_n8n.ps1`)
- Scheduled tasks (`install_scheduled_tasks.ps1`) — Watchdog (5min), HealthMonitor (10min), DailyPurge (02:00), DailyBackup (01:00)
- Daily backup (`app/daily_backup.ps1`) — restore points, 3 kept + archive
- Daily purge (`app/purge_old_data.ps1`) — data retention enforcement
- Log management (rotation, archiving)
- Multi-practice infrastructure architecture (Phase 2)
- Port management (8765 dashboard, 5678 n8n, 11434 Ollama)

#### Current State
- Watchdog: running every 5 min, handles dashboard + n8n restart
- Health monitor: every 10 min, deep checks (HTTP not just port), tiered recovery (soft → hard → alert)
- Daily backup: timestamped restore points in `backup/restore_points/`, keeps last 3, archives older
- Daily purge: partial (only covers queue stages, not outputs)
- Scheduled tasks: 4 registered (Watchdog, HealthMonitor, DailyPurge, DailyBackup)
- Broken legacy tasks: "JeffLocal Dashboard" and "JeffLocal n8n" point to non-existent scripts — cannot delete without admin, harmless (watchdog covers them)
- Registry Run key: watchdog starts on user login (`HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run`)
- Log rotation: dashboard.log and watchdog.log rotate at 2MB/3MB

#### Production Gap
- [ ] ID-01: Full pipeline automation — n8n intake → PS1 pipeline → dashboard import with no manual steps (currently requires manual Import button click or API call after pipeline runs)
- [ ] ID-02: Multi-practice architecture design — per-practice SQLite DB isolation, separate queue directories, shared Ollama, separate n8n workflow instances
- [ ] ID-03: "JeffLocal Dashboard" and "JeffLocal n8n" broken scheduled tasks need admin to delete — document workaround or escalation path
- [ ] ID-04: Daily purge doesn't cover `outputs/handoff_json/` or `outputs/ollama_raw/` — coordinate with SC
- [ ] ID-05: No alerting channel — health monitor posts to `/api/alerts/ingest` but there's no outbound notification (email, SMS, Slack) for staff
- [ ] ID-06: Ollama has no watchdog — if Ollama crashes, pipeline silently fails
- [ ] ID-07: Backup restore procedure not documented or tested (backups exist but restore path is manual)

#### Key Files
```
scripts/service_control/watchdog.ps1
scripts/service_control/health_monitor.ps1
scripts/service_control/_launch_dashboard.ps1
scripts/service_control/_launch_n8n.ps1
scripts/service_control/install_scheduled_tasks.ps1
app/daily_backup.ps1
app/purge_old_data.ps1
logs/service_control/watchdog.log
logs/service_control/health_monitor.log
logs/service_control/backup.log
backup/restore_points/LATEST_RESTORE_POINT.txt
```

#### Task Breakdown

**Priority 1 — Blocking for production**
- [ ] ID-01: Full pipeline automation — implement auto-import trigger: after `process_queue.ps1` completes successfully, automatically call `/api/import` (no manual step)
- [ ] ID-02: Add Ollama to watchdog health checks (port 11434 + `/api/tags` endpoint)
- [ ] ID-03: Implement backup restore test — monthly dry-run that restores from latest restore point to a temp directory and validates DB integrity
- [ ] ID-04: Add outbound alert for critical health failures (at minimum: write to `logs/alerts/critical.log` with timestamp; ideally email via SMTP)

**Priority 2 — Core production quality**
- [ ] ID-05: Design multi-practice directory structure (`practices/{practice_id}/queue/`, `practices/{practice_id}/data/`, shared Ollama)
- [ ] ID-06: Add log archiving to daily backup (logs older than 30 days compressed to `backup/log_archives/`)
- [ ] ID-07: Document full disaster recovery procedure (what to do if machine restarts, if DB corrupts, if queue jams)

**Priority 3 — Phase 2 Pre-requisites**
- [ ] ID-08: Implement practice isolation — per-practice app_settings.json, DB, queue, keys
- [ ] ID-09: Build practice provisioning script — create all directories, DB, keys, scheduled tasks for a new practice in one command
- [ ] ID-10: Add monitoring dashboard endpoint (`/api/system/health-full`) — all services, queue depths, last backup time, disk space

#### Acceptance Criteria
- Calls processed by pipeline appear in dashboard automatically without any manual step
- Ollama crash is detected within 10 minutes and logged
- Backup restore procedure is documented and tested against a real restore point
- Health monitor critical failures produce an outbound notification
- Multi-practice structure design is documented as an architecture decision record (ADR)

#### Agent Briefing (cold-start context)
> You are the Infrastructure & DevOps Engineer. Your primary concern is: services stay up, data is backed up, and the pipeline runs without manual intervention. The watchdog is at `scripts/service_control/watchdog.ps1`, runs every 5 minutes. The health monitor is at `scripts/service_control/health_monitor.ps1`, runs every 10 minutes. The dashboard launches via `scripts/service_control/_launch_dashboard.ps1`. The most impactful open task is ID-01: full pipeline automation — currently the pipeline processes calls but the dashboard still needs a manual import trigger. This is the gap between "automated pipeline" and "fully automated system."

---

### [QA] Quality Assurance

**Status:** Active  
**Expert Role:** QA & Test Automation Engineer  
**One-line purpose:** Owns test coverage, regression suites, end-to-end pipeline verification, and release gate criteria.

#### What QA Owns
- `tests/` directory — all test scripts and fixtures
- `tests/fixtures/` — test payloads, patient data, expected outcomes
- End-to-end pipeline test runs (n8n → pipeline → dashboard)
- Regression suite for request type classification
- Patient matching accuracy tests
- Auth and session tests
- Test batch management (N8NTEST-* prefixed call IDs)
- Release gate criteria (what must pass before any production deployment)

#### Current State
- Test scripts: `send_5_n8n_webhook_test_calls.py`, `send_20_live_lookup_direct_to_queue.py`, `send_fresh_20260521_test.py`, `send_gp_demo_n8n_webhook_calls.py`, etc.
- Fixtures: `live_lookup_test_payloads.py` (rich multi-pathway batch), `n8n_webhook_test_pack.py` (5-call webhook batch)
- Expected outcomes: `tests/fixtures/expected_raw_intake_mock_outcomes.json`
- **Critical gap**: ALL test scripts use old `jefflocal_staff_id` cookie auth — broken after session-based auth was introduced
- **Critical gap**: Test fixture call_ids are fixed (N8NTEST-001..005) — re-runs show "Resolved" status, not "New"
- n8n webhook path: verified working (2026-05-22, execution #66)
- Coverage: prescription pathway well-tested, sick_note and referral need tracing

#### Production Gap
- [ ] QA-01: Rewrite all test scripts for session-based auth (login step first, get session cookie, use in subsequent calls)
- [ ] QA-02: Generate unique call_ids per test run (timestamp-suffix: `N8NTEST-{YYYYMMDD-HHMMSS}-001` format)
- [ ] QA-03: Pathway activation audit — trace sick_note, referral, test_result, admin through full pipeline with real-format transcripts
- [ ] QA-04: Add assertion layer to test scripts — currently scripts report counts but don't assert correctness of extracted fields
- [ ] QA-05: Build regression suite for request type classifier (given transcript → expected request_type)
- [ ] QA-06: Build patient matching accuracy test (given name/DOB inputs → expected match/no-match/possible-match result)
- [ ] QA-07: No CI/CD pipeline — tests are run manually

#### Key Files
```
tests/send_5_n8n_webhook_test_calls.py           ← webhook test (use this for n8n path)
tests/send_fresh_20260521_test.py                ← rich 5-call multi-pathway batch
tests/send_20_live_lookup_direct_to_queue.py     ← 20-call stress test (direct queue)
tests/fixtures/live_lookup_test_payloads.py      ← payload builder + PATIENTS dict
tests/fixtures/n8n_webhook_test_pack.py          ← n8n batch builder
tests/fixtures/expected_raw_intake_mock_outcomes.json
dashboard/data/dashboard.sqlite                  ← check imported cases post-test
logs/app/                                        ← pipeline logs
```

#### Task Breakdown

**Priority 1 — Blocking for production**
- [ ] QA-01: Rewrite test scripts with auth flow — `tests/helpers/auth.py` helper that logs in and returns session cookie
- [ ] QA-02: Fix call_id generation — timestamp-suffix per run so re-runs always produce "New" cases
- [ ] QA-03: Add assertion layer — after pipeline completes, query dashboard API and assert: correct request_type, patient matched/unmatched as expected, priority level correct
- [ ] QA-04: Pathway activation audit — all 8 pathways must produce valid handoff JSON with no pipeline errors

**Priority 2 — Core production quality**
- [ ] QA-05: Request type classifier regression suite — 50 sample transcripts with expected classification labels
- [ ] QA-06: Patient matching accuracy suite — test all match states: exact, possible, no_match, third_party
- [ ] QA-07: Build daily auto source check (`scripts/daily_source_check.ps1`) — git diff, run tests, auto-commit if green, alert on failures (Task #16)

**Priority 3 — Polish**
- [ ] QA-08: Add performance benchmarks — pipeline processing time per call (target: < 30s per call)
- [ ] QA-09: Set up GitHub Actions (or equivalent) for CI on PR — run test suite, report pass/fail

#### Acceptance Criteria
- All test scripts authenticate via session cookie (not legacy cookie)
- Each test run generates fresh unique call_ids — no "Resolved" bleedover from previous runs
- All 8 pathways pass end-to-end with correct field extraction
- Request type classifier achieves > 92% accuracy on 50-sample regression suite
- Patient matching achieves > 95% accuracy on test set

#### Agent Briefing (cold-start context)
> You are the QA Engineer. Your test scripts are in `tests/`. The most critical blocker: all test scripts use old `jefflocal_staff_id` cookie auth, which was replaced by session-based auth. Every test that touches an authenticated dashboard endpoint will fail until QA-01 is done. To get a valid session token, POST to `/login` with `{"username": "reception.demo", "password": "Reception2026!"}` and capture the `jefflocal_session` cookie. The n8n webhook test (`send_5_n8n_webhook_test_calls.py`) works because it calls n8n (port 5678), not the dashboard directly. Use that as your working baseline.

---

### [ENI] EMIS & NHS Integration

**Status:** ⛔ INACTIVE — Phase 2. Do not build until explicitly activated by project lead.  
**Expert Role:** Clinical Systems Integration Engineer  
**One-line purpose:** Live patient record lookup, NHS number verification, and EMIS write-back for completed handoffs.

#### What ENI Will Own (Phase 2)
- EMIS PAD API integration (patient record lookup, GP-linked data)
- NHS number verification (NHS Spine / PDS API)
- Live patient lookup replacing `mock_patient_lookup_v1.csv`
- EMIS write-back for completed sick notes, referrals, prescription confirmations
- Appointment slot availability check (before redirect)
- HL7 FHIR message formatting for NHS API calls
- Smartcard / API key management for EMIS access

#### Phase 2 Prerequisites (must all be complete before ENI activates)
- [ ] SC-04: SQLite encrypted at rest (patient record data from EMIS cannot be held unencrypted)
- [ ] ID-08: Multi-practice isolation (EMIS credentials are per-practice)
- [ ] PE-05: Additive schema migration complete (EMIS data fields need new schema slots)
- [ ] PO (Practice Operations): ICB approval and EMIS API access granted for pilot practice

#### Placeholder Architecture
```
Current:  pipeline → Jeff.PatientMatch.ps1 → mock_patient_lookup_v1.csv
Phase 2:  pipeline → Jeff.PatientMatch.ps1 → ENI Lookup Service → EMIS PAD API
                                                                 → NHS PDS API (backup)
```

#### Key Design Decisions (to be made at Phase 2 activation)
1. Pull vs cache: query EMIS live per call vs. nightly cache to local DB
2. Write-back scope: what completed handoffs trigger an EMIS write (sick notes only? all pathways?)
3. Consent model: does patient consent to data sharing via Jeff conversation count for EMIS access?
4. Fallback: what happens when EMIS API is unavailable (fall back to CSV? queue for retry?)

#### Agent Briefing (cold-start context)
> You are the EMIS & NHS Integration Engineer. **Your department is inactive.** Do not start any implementation work. When activated, your entry point will be `app/modules/Jeff.PatientMatch.ps1` — you will replace the CSV lookup with a live EMIS API call while keeping the same output interface. All prerequisites listed above must be confirmed complete before you begin.

---

### [PO] Practice Operations

**Status:** Active (single practice), expands Phase 2  
**Expert Role:** Practice Onboarding & Operations Manager  
**One-line purpose:** Owns practice configuration, staff account management, onboarding procedures, and the multi-practice rollout framework.

#### What PO Owns
- Per-practice configuration (`config/app_settings.json`, future: `config/practice_settings.json`)
- Staff account lifecycle (create, role assignment, PIN setup, deactivation)
- Patient lookup CSV management (upload, validate, replace)
- Practice-specific settings (practice name, address, opening hours, GP list)
- Onboarding runbook for new practices
- Staff training materials and quick-reference guides
- Demo mode management (`DEMO_CALL_PREFIXES`, test data cleanup)

#### Current State (single practice: Churchtown Medical Centre)
- Practice identity: hardcoded in templates ("Churchtown Medical Centre")
- Staff accounts: 6 active (admin.demo, Saeed 1, gp.demo [readonly], Jessica Test1, Mary 1, reception.demo)
- Roles: admin, staff, readonly
- Patient lookup: `mock_patient_lookup_v1.csv` (500 mock patients)
- Demo mode: `N8NTEST-`, `RAWMOCK-`, `GPDEMO-`, `DEMO-` prefixed cases excluded from real reports
- Practice config: no formal `practice_settings.json` — name/address embedded in templates

#### Production Gap
- [ ] PO-01: Create `config/practice_settings.json` — practice name, address, phone, opening hours, GP names (replaces hardcoded template strings)
- [ ] PO-02: Build practice admin UI (settings page section) — allows admin-role staff to update practice details without code changes
- [ ] PO-03: Create staff onboarding runbook — step-by-step for IT/admin to set up JeffLocal at a new practice
- [ ] PO-04: Build CSV validation tool — check patient lookup CSV format before upload (headers, NHS number format, DOB format, duplicates)
- [ ] PO-05: Multi-practice: practice registration flow (provision new practice, assign practice_id, create isolated directories, register scheduled tasks)
- [ ] PO-06: Staff quick-reference guide — 1-page PDF for reception staff explaining how to use the dashboard

#### Key Files
```
config/app_settings.json                     ← practice config (partial)
dashboard/templates/base.html               ← "Churchtown Medical Centre" hardcoded
dashboard/templates/settings.html          ← settings UI
dashboard/app/main.py                       ← staff_create, staff_update endpoints
data/patient_lookup/mock_patient_lookup_v1.csv
```

#### Task Breakdown

**Priority 1 — Blocking for production**
- [ ] PO-01: Create `config/practice_settings.json` with all practice-specific strings
- [ ] PO-02: Update all templates to read practice name/address from `practice_settings.json` (not hardcoded)
- [ ] PO-03: Create patient lookup CSV validation script (`app/validate_patient_csv.ps1`)
- [ ] PO-04: Write staff onboarding runbook (`docs/ONBOARDING_RUNBOOK.md`)

**Priority 2 — Core production quality**
- [ ] PO-05: Build CSV upload UI in settings page (admin-role only, validates before replacing)
- [ ] PO-06: Implement proper demo mode isolation — demo cases never appear in production reports
- [ ] PO-07: Write staff quick-reference guide (1 page: what is JeffLocal, how to review a case, how to resolve)

**Priority 3 — Phase 2 Pre-requisites**
- [ ] PO-08: Design practice provisioning script (one command → new practice fully configured)
- [ ] PO-09: Build practice selection UI for multi-practice admin (switch between practices)
- [ ] PO-10: Create Data Processing Agreement template for new practices (coordinate with SC)

#### Acceptance Criteria
- Practice name/address configurable without touching template files
- New practice can be onboarded end-to-end from the runbook in under 2 hours
- Patient lookup CSV can be validated and replaced via UI (admin only)
- Demo cases never appear in live reports or workload counts

#### Agent Briefing (cold-start context)
> You are the Practice Operations Manager. Your most urgent task is creating `config/practice_settings.json` and removing the hardcoded "Churchtown Medical Centre" strings from the templates. The templates directory is `dashboard/templates/`. The string "Churchtown Medical Centre" appears in `base.html` and likely `login.html`. All practice-specific config should be centralised in `practice_settings.json` and injected via the FastAPI template context. You do not own the code — you own the configuration and process layer.

---

## 6. Cross-Department Dependencies

```
VAI ──────────────────────────► IR
 (payload schema contract)      │
                                 │
                                 ▼
                                PE ◄──── config files (model_settings, pathways,
                                │        routing_rules, model_monitoring)
                                │
                                ▼
                               DX ◄──── auth, import, case management
                                │
                         SC ───►├◄─── all layers (audit, encryption, retention)
                         ID ───►├◄─── all services (watchdog, backup, automation)
                         QA ───►├◄─── all departments (test coverage)
                                │
                               PO ◄──── practice config, staff setup
                                │
                    (Phase 2)   ▼
                               ENI ◄──── EMIS/NHS (inactive)
```

**Hard dependency order for production release:**
1. SC-01, SC-02, SC-03 (GDPR + audit) — must be done before go-live
2. PE-01 through PE-04 (missing config files) — blocks pipeline reliability
3. IR-01, IR-02 (HMAC verification + API key auth) — blocks n8n security
4. QA-01, QA-02, QA-03 (working test suite) — gates everything above
5. ID-01 (pipeline automation) — final gap for zero-manual-intervention
6. PO-01, PO-02 (practice config externalisation) — gates multi-practice
7. DX-01, DX-02 (password reset + session purge) — gates production auth

---

## 7. Production Readiness Checklist

### Phase 1 Gate (Single Practice Go-Live)
- [ ] All Priority 1 tasks across VAI, IR, PE, DX, SC, ID, QA, PO complete
- [ ] 90-day data purge covering all patient data directories
- [ ] Audit log table implemented and writing entries
- [ ] HMAC verification enforced on all incoming payloads
- [ ] Test suite passing with session-based auth and unique call IDs
- [ ] Pipeline automation — zero manual steps from call to dashboard
- [ ] Password reset flow working end-to-end
- [ ] Practice settings externalised from templates
- [ ] Staff onboarding runbook written and reviewed
- [ ] Backup restore procedure tested successfully once

### Phase 2 Gate (Multi-Practice Rollout)
- [ ] All Phase 1 gates passed
- [ ] Per-practice DB isolation implemented
- [ ] Practice provisioning script tested on second practice
- [ ] SQLite encryption at rest implemented
- [ ] ENI prerequisites complete (SC-04, ID-08, PE-05)
- [ ] ENI department activated
- [ ] Data Processing Agreement signed with all practices

---

## 8. Known Technical Debt

| Item | Severity | Owner | Notes |
|------|----------|-------|-------|
| 4 missing config JSON files | High | PE | model_settings, pathways, routing_rules, model_monitoring |
| Test scripts broken (old auth) | High | QA | jefflocal_staff_id cookie replaced by session auth |
| GDPR: outputs/ no retention policy | High | SC | Plain-text patient data, no purge |
| Pipeline not fully automated | Medium | ID | Manual import step still required |
| HMAC verification not enforced | High | IR | Payloads signed but signature not checked |
| "Last import: Never" bug | Low | DX | last_import_at not updating in settings diagnostics |
| Legacy broken scheduled tasks | Low | ID | Cannot delete without admin — harmless |
| 5 deadletter queue items | Medium | PE | Unknown root cause, no replay tooling |
| Session purge only at login | Medium | SC/DX | Daily scheduled purge needed |
| /patients and /reports 404 | Medium | DX | Nav links with no routes |

---

## 9. File Structure Reference

```
C:\JeffLocal\
├── app/                          ← PS1 pipeline scripts
│   ├── process_queue.ps1         ← ENTRY POINT: queue processor
│   ├── run_intake.ps1            ← encrypted intake
│   ├── build_handoff.ps1
│   ├── call_ollama.ps1
│   ├── detect_flags.ps1
│   ├── generate_staff_summary.ps1
│   ├── daily_backup.ps1
│   ├── purge_old_data.ps1
│   └── modules/
│       ├── Jeff.Common.ps1
│       ├── Jeff.PatientMatch.ps1
│       ├── Jeff.RequestType.ps1
│       ├── Jeff.Validation.ps1
│       ├── Jeff.Emergency.ps1
│       ├── Jeff.Handoff.ps1
│       └── Jeff.StaffSummary.ps1
├── config/
│   ├── app_settings.json         ← queue paths, patient lookup path
│   └── security/
│       ├── jeie_v1.config.json
│       ├── nonce_store.json
│       └── keys/
│           ├── jefflocal_public.pem
│           ├── jefflocal_private.pem
│           └── voice_agent_hmac_secret.txt
├── dashboard/
│   ├── app/
│   │   ├── main.py               ← FastAPI app (~3500 lines)
│   │   ├── auth.py               ← auth module
│   │   ├── db.py                 ← init_db, migrations
│   │   ├── models.py
│   │   └── importer.py
│   ├── templates/                ← Jinja2 templates
│   ├── static/
│   │   └── dashboard.css
│   ├── data/
│   │   └── dashboard.sqlite      ← live database
│   └── .venv/                    ← Python virtualenv
├── data/
│   └── patient_lookup/
│       └── mock_patient_lookup_v1.csv
├── queue/
│   ├── encrypted_raw/            ← stage 1: raw encrypted payloads
│   ├── incoming/                 ← stage 2: decrypted/normalised
│   ├── processing/               ← stage 3: in-flight
│   ├── processed/                ← stage 4: success
│   ├── failed/                   ← error: recoverable
│   └── deadletter/               ← error: unrecoverable (5 items)
├── outputs/
│   ├── handoff_json/             ← final handoff JSONs (GDPR: 90-day purge needed)
│   ├── ollama_raw/               ← Ollama raw responses (GDPR: 90-day purge needed)
│   └── debug/
├── scripts/
│   └── service_control/
│       ├── watchdog.ps1
│       ├── health_monitor.ps1
│       ├── _launch_dashboard.ps1
│       ├── _launch_n8n.ps1
│       └── install_scheduled_tasks.ps1
├── tests/
│   ├── fixtures/
│   │   ├── live_lookup_test_payloads.py
│   │   ├── n8n_webhook_test_pack.py
│   │   └── expected_raw_intake_mock_outcomes.json
│   ├── send_5_n8n_webhook_test_calls.py
│   └── send_fresh_20260521_test.py
├── logs/
│   ├── app/
│   ├── audits/
│   ├── service_control/
│   └── transcripts/
└── backup/
    ├── restore_points/
    └── archived_restore_points/
```

---

*This document is the source of truth for Claude Cowork agent onboarding. Each department section is self-contained and can be handed to a specialist agent cold. Update this document whenever a task moves from gap to complete.*

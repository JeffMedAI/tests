# Glossary — Avamed
# Key terms used across this project. Use these consistently.

---

| Term | Meaning |
|---|---|
| **Jeff** | The voice AI that answers patient calls and captures the reason for contact. Provided by Hostcomm UK, not built by Avamed. |
| **Avamed** | The commercial product and company name. JeffLocal is the internal development name only. |
| **Triage** | Classifying an incoming patient request by urgency and type before staff action. Admin-level only — no clinical decisions. |
| **Handoff JSON** | The structured data packet produced by the pipeline and consumed by the dashboard importer. Contains patient match, request type, priority, safety flags, and task text. |
| **EMIS** | The NHS patient record system used as the authoritative source for verifying and matching patient identity. |
| **Red flag** | A safety marker on a case indicating potential urgency or clinical risk. Triggers a mandatory staff alert. Determined by deterministic code, never by the LLM. |
| **Ollama / Gemma** | The local LLM stack used to extract draft fields from call transcripts. Runs on-premises. Active model: `gemma4:e2b`. Fallback: `gemma4:e4b` (triggers if monitoring score < 0.72). |
| **Deterministic override** | The rule that code-verified data always supersedes LLM output. The LLM drafts; the code decides. |
| **Dashboard** | The FastAPI + Jinja2 web UI where reception staff view, prioritise, and action triage requests. Two instances: production (port 8765) and sandbox (port 5000). |
| **90-day purge** | The automated GDPR data deletion process that removes case records and transcripts older than 90 days from all patient data directories. |
| **GuardRail** | The Safety & Governance Agent with independent veto authority over any change touching patient data, auth logic, or clinical safety. |
| **ControlTower** | The Chief Coordinator agent that wraps proposed changes into formal approval packs before escalating to Saeed. |
| **DX Agent** | The Implementation Lead agent. Executes approved work but cannot approve its own changes. |
| **n8n** | The workflow automation tool used as the intake router. Runs on port 5678. Webhook path: `ava-live-intake`. |
| **Deadletter queue** | The final stage in the pipeline queue for cases that failed processing and cannot be automatically retried. Currently contains 5 items with no replay tooling. |
| **ENI** | EMIS/NHS Integration — the department responsible for direct EMIS connectivity. Explicitly INACTIVE; Phase 2 only. |
| **DSPT** | Data Security and Protection Toolkit — mandatory NHS compliance standard for organisations handling NHS data. Deadline: 30 June 2026. |
| **DTAC** | Digital Technology Assessment Criteria — required for NHS procurement approvals. In draft. |
| **Hostcomm UK** | Avamed's voice AI partner, provider of Jeff. Listed on the NHS Digital Marketplace — material to NHS procurement submissions. |
| **NHS SBS** | NHS Shared Business Services. The SBS10523 Healthcare AI Solutions Framework submission deadline is 23 June 2026. |

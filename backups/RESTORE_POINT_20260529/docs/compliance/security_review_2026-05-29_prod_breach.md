# SECURITY REVIEW — POST-HOC EMERGENCY REVIEW
# Commit: 6f5eb8f36084da8a7400253c2903bd59389ece8b
# Branch: sandbox → applied to PRODUCTION dashboard (port 8765)
# Date: 2026-05-29
# Reviewer: Security Agent
# Status: APPROVED WITH NOTES (see section 10)
# Process breach: LOGGED (see section 11)

---

## CONTEXT

This is a post-hoc security review conducted under emergency protocol. Commit 6f5eb8f was
applied directly to the production dashboard (C:\JeffLocal\dashboard\, port 8765) and the
production service was restarted with new code live, WITHOUT prior Security Agent review.
This constitutes a governance breach under the Security Agent's mandate which states all
PRs from all agents must be reviewed BEFORE merge.

This review assesses whether the live changes are safe to remain deployed or must be
immediately rolled back.

---

## CHANGED FILES IN SCOPE

Application code (production):
- dashboard/app/main.py        (+13 lines)
- dashboard/templates/base.html (+4 lines)
- dashboard/static/dashboard.css (+21 lines)

New config files:
- config/model_settings.json   (new, 9 lines)
- config/routing_rules.json    (new, 61 lines)
- config/pathways.json         (new, 70 lines)
- config/model_monitoring.json (new, 38 lines)

Documentation/governance (no security scope):
- docs/reports/config_audit_2026-05-29.md
- docs/reports/dispatch_2026-05-29.md
- governance/GOVERNANCE_FRAMEWORK.md
- sandbox/agents/lead/lead_CLAUDE.md

---

## CHECKLIST

### [PASS] 1. PII CHECK

Scanned all changed files for: NHS number patterns, date-of-birth formats, full names
in logs, email addresses in logs, phone numbers.

- dashboard/app/main.py: New function _nav_alert_count() runs a COUNT query only —
  returns an integer, no patient fields selected.
- dashboard/templates/base.html: Badge renders the integer count only ({{ _ac }}).
  No patient name, NHS number, DOB, or callback number is rendered.
- dashboard/static/dashboard.css: Pure styling — no data.
- config/model_settings.json: Model name, temperature, endpoint, retries only — no PII.
- config/routing_rules.json: Pathway routing logic — no patient data, no staff PII.
  practice_id "churchtown" is a system identifier, not patient data.
- config/pathways.json: Pathway metadata, safety_notes are generic clinical workflow
  instructions, not patient records.
- config/model_monitoring.json: Confidence thresholds, red_flag_keywords, escalation
  rules, log directory path only. No patient data.
- monitoring_log_dir hardcoded path "C:\\JeffLocal\\logs\\model_monitoring": This is
  a filesystem path, not PII. Noted under item 5 (Secrets & Config).

Result: PASS — No PII found in any changed file.

---

### [PASS] 2. SQL INJECTION

Changed SQL: One new query in _nav_alert_count():
  SELECT COUNT(*) FROM alert_events WHERE acknowledged_at IS NULL

Assessment:
- The query is a static string literal with no user input, no f-string, no concatenation.
- No parameters are injected — acknowledged_at IS NULL is a fixed predicate.
- The function takes no arguments. There is no user-controlled variable in scope.
- Return value is fetchone()[0] — a plain integer, never passed back to SQL.

All other SQL in the diff is a count query at main.py line 3875 (existing code, not
modified in this commit).

Result: PASS — No SQL injection vector. Query is parameterless and static.

---

### [PASS] 3. AUTH COVERAGE

The new _nav_alert_count() function:
- Is registered as a Jinja2 template global, not as a route or endpoint.
- It is called only within base.html, which is the authenticated-session template.
- The enforce_auth middleware (lines 102-119) gates ALL non-public paths before any
  template is rendered. base.html is only reached by authenticated requests.
- AUTH_PUBLIC_PATHS and AUTH_PUBLIC_PREFIXES are unchanged in this commit.
- No new routes were added.
- No new API endpoints were added.
- enforce_auth logic itself is unchanged.
- Session cookie settings unchanged: httponly=True, samesite="lax", secure=True,
  max_age=3600.

Edge case checked: _nav_alert_count() runs a DB call on every page render. While this
adds a DB round-trip per authenticated request, it does not expose a new attack surface
and does not run for unauthenticated requests (middleware redirects before template
rendering occurs).

Result: PASS — Auth coverage unchanged and correct. No new unauthenticated routes.

---

### [PASS] 4. EXTERNAL CALLS

Examined all changes for HTTP calls:
- _nav_alert_count(): reads local SQLite only (connect() returns a sqlite3.Connection
  to dashboard/data/dashboard.sqlite). No network call.
- config/model_settings.json: ollama_endpoint is "http://localhost:11434" — localhost
  only. This is configuration data, not executable code. The field documents where the
  existing pipeline scripts call Ollama; no new outbound call is introduced by this commit.
- No new pip packages. No new npm packages. No new webhook registrations.
- No urllib, httpx, requests, http.client, or subprocess calls in the diff.

Result: PASS — No new external HTTP calls. Ollama endpoint remains localhost.

---

### [WARN] 5. SECRETS & CONFIG

No secrets, tokens, passwords, or API keys found in any changed file.

Checked specifically:
- config/model_settings.json: No credentials. ollama_endpoint is localhost with no auth.
- config/routing_rules.json: No credentials. Routing labels and queue names only.
- config/pathways.json: No credentials. Pathway metadata only.
- config/model_monitoring.json: No credentials. Thresholds and keywords only.

NOTED ISSUE (non-veto, but flagged):
  model_monitoring.json contains:
    "monitoring_log_dir": "C:\\JeffLocal\\logs\\model_monitoring"

  This hardcodes an absolute Windows path. While not a secret, this is:
  (a) Environment-specific — breaks if deployed on a different machine or OS.
  (b) An implicit assumption about the production filesystem layout.

  RECOMMENDATION: This value should be resolved relative to ROOT_DIR in the consuming
  script (evaluate_model_output.ps1), or use an environment variable. Flag to Backend
  Agent for resolution before production promotion.

Result: PASS (no secrets) — WITH NOTE: hardcoded absolute path in model_monitoring.json
should be externalised before production promotion.

---

### [PASS] 6. DEPENDENCY AUDIT

No new Python packages added (no requirements.txt or pyproject.toml changes).
No new npm packages added (no package.json changes).
No new imports added to main.py beyond what was already present.
_nav_alert_count() uses the existing connect() helper from .db — no new dependency.

Result: PASS — No new dependencies introduced.

---

### [PASS] 7. TRANSCRIPT HANDLING

No transcript access in the diff. _nav_alert_count() queries alert_events only.
alert_events table does not contain raw transcripts per the schema in db.py (lines
92+). The transcript column lives in the cases table, not alert_events.
No new transcript storage logic. No new purge_after logic required.

Result: PASS — No transcript handling changes.

---

### [PASS] 8. INPUT VALIDATION

_nav_alert_count() accepts no inputs. It is a zero-argument function that runs a
static query and returns an integer. There is no user-controlled input path.

base.html: The badge renders {{ _ac }} — the integer returned from _nav_alert_count().
Jinja2 auto-escapes by default. An integer cannot be an XSS vector.

config files: These are read by PowerShell scripts (evaluate_model_output.ps1,
run_intake.ps1, smoke tests). They are not user-submitted data. The content is
internally authored and version-controlled. No user input path exists.

Result: PASS — No input validation concerns.

---

### [PASS] 9. ERROR HANDLING

_nav_alert_count() has a try/except Exception block:
  try:
      with connect() as conn:
          return conn.execute(...).fetchone()[0]
  except Exception:
      return 0

Assessment:
- Silences all exceptions and returns 0 (safe default — badge disappears, no crash).
- Does NOT propagate stack traces to the template or the HTTP response.
- Does NOT log the exception. This means DB errors are silently swallowed with no
  operator visibility.

NOTED ISSUE (non-veto, but flagged):
  The bare except swallows errors silently. If the alert_events table is missing or
  the DB is corrupt, the badge will silently show 0 rather than alerting operators
  to the underlying problem. A log.warning() call would improve observability without
  changing the safe-default behaviour.

  RECOMMENDATION: Add `import logging` and `logging.getLogger(__name__).warning(...)` 
  in the except block. Flag to Backend Agent.

Result: PASS (no error information exposed to client) — WITH NOTE: silent exception
swallowing reduces operator visibility; logging should be added.

---

### [10. OVERALL DECISION]

## VERDICT: APPROVED WITH NOTES

No veto-trigger issues found. The changes are safe to remain deployed.

Summary of findings by severity:

  BLOCKING (veto triggers): NONE

  NOTES (non-blocking, should be resolved):
    N1. model_monitoring.json hardcodes "C:\\JeffLocal\\logs\\model_monitoring" as an
        absolute path. Recommendation: resolve relative to ROOT_DIR or use an
        environment variable. Assign to Backend Agent.

    N2. _nav_alert_count() silently swallows exceptions with no log output. Staff
        and operators have no visibility if the alert_events table becomes unavailable.
        Recommendation: add a logging.warning() call in the except block.
        Assign to Backend Agent.

  GOVERNANCE ISSUE (separate from code quality):
    G1. This commit was applied to the PRODUCTION dashboard without prior Security
        Agent review. This violates the Security Agent mandate. See section 11.

---

### [11. GOVERNANCE BREACH — PROCESS VIOLATION]

## BREACH FINDING

Commit 6f5eb8f was applied to C:\JeffLocal\dashboard\ (PRODUCTION, port 8765) and the
production service was restarted with new code live, WITHOUT prior Security Agent review.

Per the Security Agent brief:
  "Report must be attached to the PR before merge is allowed."
  "Security Agent reviews every PR from every agent before it is merged."

This applies to the sandbox branch as well as main, when the code touches the
PRODUCTION dashboard directory (dashboard/).

## WHAT HAPPENED

The Backend Agent and the process leading to this commit bypassed the Security Agent
review gate. The production service was restarted with unreviewed code. While this
review has found no veto-trigger issues (the code is safe), the bypass itself is a
governance failure that must be documented and remediated.

## REQUIRED REMEDIATION

1. Lead Agent must acknowledge this breach in the next dispatch report.
2. Backend Agent brief (backend_CLAUDE.md) must be reviewed to confirm it includes
   explicit instruction: "Security Agent review required before any commit touching
   dashboard/ is merged or deployed."
3. Governance Framework must note this as a process failure and record the date
   (2026-05-29) in the decision log.
4. Future commits touching dashboard/app/main.py must always go through:
   Test Agent (failing tests) → Backend Agent (implementation) → Security Agent
   (review) → Lead Agent (approve) → human (merge).

## DISPOSITION

The live deployment is PERMITTED TO REMAIN — code review finds no veto-trigger issues.
However, the process breach is formally recorded here and in the decision log.
The human (Saeed) is advised of this breach as a matter of record.

---

## SIGN-OFF

Reviewed by: Security Agent
Date: 2026-05-29
Commit: 6f5eb8f36084da8a7400253c2903bd59389ece8b
Branch: sandbox (applied to production dashboard/)
Verdict: APPROVED WITH NOTES
Live deployment: PERMITTED TO REMAIN

Outstanding actions for Backend Agent:
  - N1: Externalise monitoring_log_dir in model_monitoring.json
  - N2: Add logging.warning() in _nav_alert_count() except block

Outstanding actions for Lead Agent:
  - G1: Acknowledge breach in dispatch; update backend brief; log in governance

Outstanding actions for Human (Saeed):
  - Awareness: Production dashboard was modified without prior Security Agent review.
    The code is safe (approved with notes). Process remediation is in progress.

# SECURITY REVIEW — HMAC-SHA256 Webhook Signature Verification
# Feature: IR-01 — HMAC payload verification on n8n webhook
# Files reviewed: sandbox/dashboard/app/main.py (verify_hmac_signature, verify_webhook_hmac)
#                 sandbox/dashboard/tests/test_hmac_verification.py
#                 sandbox/dashboard/.env.sandbox
# Date: 2026-05-30
# Reviewer: Security Agent (inline review, Backend Agent task)
# Status: APPROVED — no blocking issues found

---

## CONTEXT

This review covers the HMAC-SHA256 webhook signature verification implementation
added to the JeffLocal sandbox dashboard as task IR-01. The implementation guards
the `/api/n8n/test-intake-batch` endpoint against unsigned or forged POST requests
from callers other than the trusted local n8n instance.

All changes are in the SANDBOX directory (`C:\JeffLocal\sandbox\dashboard\`).
Production (`C:\JeffLocal\dashboard\`) was not touched. This review must be repeated
before any promotion to production.

---

## FILES IN SCOPE

```
sandbox/dashboard/app/main.py
  - Added: import logging (line ~5)
  - Added: _log = logging.getLogger(__name__) (line ~57)
  - Added: verify_hmac_signature(payload_bytes, signature_header, secret) -> bool
  - Modified: verify_webhook_hmac() — env var renamed WEBHOOK_HMAC_SECRET →
              JEFF_WEBHOOK_SECRET; now calls pure helper; logs failures

sandbox/dashboard/.env.sandbox
  - Added: JEFF_WEBHOOK_SECRET=REPLACE-BEFORE-LIVE

sandbox/dashboard/tests/test_hmac_verification.py
  - New file: 14 unit + integration tests (all passing)
```

---

## CHECKLIST

### [PASS] 1. SECRET STORAGE

The shared secret is read exclusively from the environment variable
`JEFF_WEBHOOK_SECRET`:

```python
secret = os.environ.get("JEFF_WEBHOOK_SECRET", "").encode()
```

- No secret is hardcoded anywhere in the implementation.
- `.env.sandbox` contains only a placeholder value (`REPLACE-BEFORE-LIVE`),
  not a real secret.
- The `.env.sandbox` file is in the repository. The placeholder value is
  intentional and clearly labelled. A real secret must be injected via the
  server environment or a secrets manager before go-live.
- If `JEFF_WEBHOOK_SECRET` is absent or empty, verification is skipped with a
  `WARNING` log entry. This is acceptable for the sandbox but **must not be
  permitted in production**. Saeed must confirm the env var is set before live
  traffic reaches this endpoint.

Result: PASS — no hardcoded secrets; env-var driven; placeholder clearly marked.

---

### [PASS] 2. CONSTANT-TIME COMPARISON

The implementation uses `hmac.compare_digest` throughout:

```python
# In verify_hmac_signature():
return hmac.compare_digest(expected, signature_header)
```

- `hmac.compare_digest` performs a constant-time byte comparison, preventing
  timing oracle attacks where an attacker could infer bytes of the expected
  digest by measuring response latency.
- The `==` operator is NOT used anywhere in the signature comparison path.
- The pure function `verify_hmac_signature` returns `False` (not raises) for
  malformed input (missing prefix), so the constant-time path is always reached
  for plausible-looking headers.

Result: PASS — constant-time comparison confirmed; no `==` on secrets.

---

### [PASS] 3. ERROR MESSAGE SAFETY

On verification failure the endpoint raises:

```python
raise HTTPException(status_code=401, detail="Invalid or missing webhook signature")
```

- The detail string is generic. It does not reveal:
  - The expected digest value
  - The secret
  - The raw payload or any fragment of it
  - Whether the failure was a missing header vs. digest mismatch
- The warning log on failure records only: request path, method, and whether
  a signature header was present (boolean). No payload content is logged.

Result: PASS — error responses and logs contain no secret material or payload data.

---

### [PASS] 4. ALGORITHM APPROPRIATENESS

Algorithm used: HMAC-SHA256.

- HMAC-SHA256 is the standard for webhook authentication (GitHub, Stripe, Twilio,
  Shopify all use this scheme). It is the OWASP-recommended algorithm for this use case.
- Header format `X-Hub-Signature-256: sha256=<hex>` follows the GitHub webhook
  convention, which is well-understood and widely implemented.
- SHA-256 produces a 256-bit digest — sufficient for this application. No known
  practical preimage or collision attacks exist.
- The `hashlib.sha256` implementation used is Python's stdlib wrapper over OpenSSL,
  which is FIPS-certified on most platforms.

Result: PASS — algorithm is appropriate and follows industry standard.

---

### [PASS] 5. TIMING ATTACK VECTORS

Three potential timing vectors examined:

**a) Digest comparison:** Covered by `hmac.compare_digest` (see item 2).

**b) Prefix check:** The function first checks `signature_header.startswith("sha256=")`.
This is a public check on the header format (not on the secret material itself), so
no timing information about the secret is leaked. A missing or malformed prefix
returns `False` immediately — but this does not leak the secret because the prefix
is a public protocol constraint.

**c) Early-exit on absent secret:** If `JEFF_WEBHOOK_SECRET` is not set, the
dependency returns early without any comparison. This is a configuration-time
decision, not a per-request timing oracle.

No additional timing attack vectors identified.

Result: PASS — no exploitable timing vectors beyond those already mitigated.

---

### [PASS] 6. PAYLOAD HANDLING

- The raw body is read via `await request.body()` **before** JSON parsing.
  This is correct — signing must be over the raw bytes, not the parsed JSON
  (which may differ from the wire representation).
- The payload bytes are passed to `verify_hmac_signature` but never logged,
  stored, or returned in error responses.
- FastAPI's body consumption via `request.body()` caches the body internally,
  so the subsequent `payload: dict = Body(...)` parameter can still parse it.

Result: PASS — payload handled correctly; raw bytes never exposed.

---

### [PASS] 7. TEST COVERAGE

14 tests, all passing:

Unit tests (9):
- Valid signature → True ✓
- Tampered payload → False ✓
- Wrong secret → False ✓
- Missing header (empty string) → False ✓
- Malformed header (no prefix) → False ✓
- Wrong prefix (sha1=) → False ✓
- Empty payload + valid sig → True ✓
- Empty payload + wrong sig → False ✓
- Short/mismatched sig handled by compare_digest → False (no raise) ✓

Integration tests (5):
- Secret not set → guard skipped, endpoint reachable (not 401) ✓
- Valid HMAC → guard passes (not 401) ✓
- Invalid HMAC → 401 ✓
- Missing header → 401 ✓
- Tampered body → 401 ✓

Result: PASS — test suite comprehensive and fully passing.

---

### [NOTE — non-blocking] 8. PRODUCTION GATE

The current implementation skips HMAC verification when `JEFF_WEBHOOK_SECRET` is
absent. This is intentional for sandbox development but creates a risk if the env
var is accidentally omitted in production.

RECOMMENDATION (non-blocking for sandbox, required before production):
- Add a startup check that logs a loud ERROR (not just WARNING) if
  `JEFF_WEBHOOK_SECRET` is empty when `ENVIRONMENT=production`.
- Consider making the verification non-optional in production mode: raise a
  startup exception if the secret is not set, rather than silently skipping.

This is flagged for the Backend Agent to address before production promotion.
It does not block sandbox approval.

---

### [NOTE — non-blocking] 9. SECRET ROTATION

No secret rotation mechanism exists. If `JEFF_WEBHOOK_SECRET` is compromised,
the process must be restarted with a new value.

RECOMMENDATION (future work, not blocking): Consider supporting two simultaneous
secrets (current + new) during rotation window, similar to GitHub's webhook
secret rotation pattern. Out of scope for IR-01.

---

## OVERALL VERDICT

### APPROVED — no blocking issues

All OWASP webhook authentication criteria are met:
- Secret is env-var driven (not hardcoded) ✓
- HMAC-SHA256 algorithm ✓
- Constant-time comparison via `hmac.compare_digest` ✓
- No secret material in error responses or logs ✓
- Raw body signed (not parsed JSON) ✓
- Tests: 14/14 passing ✓

Non-blocking notes for Backend Agent:
- N1: Add production startup check to reject boot if JEFF_WEBHOOK_SECRET is absent
- N2: Consider secret rotation support (future work)

This implementation is APPROVED for sandbox use. Production promotion requires:
1. Saeed to set a strong random `JEFF_WEBHOOK_SECRET` in the server environment
2. n8n workflow configured to send `X-Hub-Signature-256` header
3. Re-run of this review after any changes during promotion

---

## SIGN-OFF

Reviewed by: Security Agent (inline, Backend Agent task IR-01)
Date: 2026-05-30
Files: sandbox/dashboard/app/main.py, tests/test_hmac_verification.py, .env.sandbox
Verdict: APPROVED (2 non-blocking notes)
Production promotion: PENDING (requires Saeed env var + n8n config + re-review)

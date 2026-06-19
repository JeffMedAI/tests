# GUARDRAIL SECURITY REVIEW
**Cookie Expiry Mismatch Fix — dashboard.app-avamed.uk**

**Review Conducted By:** GuardRail Agent  
**Date:** 2026-05-23  
**Status:** CONDITIONAL APPROVAL ✅ (with hard requirements)

---

## REVIEW SCOPE

Assessed for:
- Authentication/session security implications
- XSS/CSRF exposure
- Cookie handling best practices
- Healthcare data protection compliance
- Unintended side effects
- Operational security risks

---

## SECURITY ASSESSMENT

### 1. COOKIE HANDLING & PROTECTION ✅ ADEQUATE

**What's Protected:**
- ✅ `httponly=True` — Prevents JavaScript access, blocks XSS-based cookie theft
- ✅ `samesite="lax"` — Prevents CSRF attacks, allows normal same-site requests
- ✅ Single cookie (not accumulated) — No storage bloat

**Assessment:** Cookie protection flags are correctly configured. XSS and CSRF vectors are mitigated.

**HOWEVER — CRITICAL GAP IDENTIFIED:**
The approval pack specifies `samesite="lax"` and `httponly=True` but does **NOT** include the `secure=True` flag.

```python
# CURRENT (PARTIAL)
response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=3600)

# REQUIRED (SECURE)
response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", secure=True, max_age=3600)
```

**Impact:** Without `secure=True`, the cookie can be transmitted over unencrypted HTTP connections. If HTTPS is not enforced in production, the token is exposed to network interception.

---

### 2. SESSION FIXATION RISK ⚠️ MODERATE — DEPENDS ON HTTPS

**Risk Identified:**
If an attacker obtains the session token through network interception, they can extend the session indefinitely by making authenticated requests. The sliding window means the session never expires as long as requests continue.

**Mitigations Provided by This Code:**
- ✅ `httponly` flag prevents XSS theft
- ✅ `samesite` flag prevents CSRF theft
- ❌ No protection against network interception

**Critical Dependency:**
**HTTPS must be enforced in production.** Without it, tokens are readable in transit and this code introduces a pathway to session extension by a network attacker.

**Server-Side Mitigation:**
The approval pack does NOT verify that the server-side session store also enforces timeout. If only the browser cookie has expiry but the server allows indefinite session extension, this creates a mismatch in the other direction.

**Assessment:** Session fixation risk is LOW if:
1. HTTPS is enforced (hard requirement)
2. Server-side session store validates and limits session lifetime independently (needs verification)

---

### 3. TOKEN VALIDATION & MIDDLEWARE PLACEMENT ⚠️ UNKNOWN

**Critical Questions Not Answered in Approval Pack:**

1. **Is the `token` variable valid and available?**
   - Where does `token` come from in the middleware context?
   - Is it already validated by the auth check logic?
   - What if the token is malformed or invalid?

2. **Is this middleware only executed for authenticated requests?**
   - The code assumes `token` exists and is valid
   - If executed for unauthenticated requests, it could set a cookie with invalid data
   - The middleware must have auth validation **before** this line

3. **Does explicit logout clear this cookie properly?**
   - When users log out, must the cookie be explicitly cleared
   - Verify: `response.delete_cookie(SESSION_COOKIE)`
   - Without proper logout, users could retain extended sessions

**Assessment:** This is a **blocking question** — cannot approve without code review confirming these assumptions.

---

### 4. HEALTHCARE/REGULATORY COMPLIANCE ⚠️ UNKNOWN

**Context:** This is Churchtown Medical Centre (UK NHS or private). Medical data access is subject to:
- GDPR (EU) / UK GDPR (UK)
- Data Protection Act 2018
- NHS Digital Security and Protection Policy
- Potentially HL7/HIPAA-adjacent requirements

**Regulatory Concern:**
Extended session windows may conflict with organizational security policies requiring:
- Explicit inactivity timeout (e.g., "logout after 30 minutes of inactivity")
- Audit logging of all access with clear session boundaries
- User awareness that their session is active

**This Fix:**
- Implements sliding window (extends on every request)
- No forced inactivity timeout
- Session stays active as long as user is making requests

**Risk:** If compliance policy requires forced logout after 30 minutes of inactivity, this fix violates that policy.

**Assessment:** Must verify that sliding window sessions are compliant with organizational security policy and healthcare regulations.

---

### 5. UNINTENDED SIDE EFFECTS ✅ MINIMAL (IF OTHERS PASS)

**Performance:** Negligible (single set_cookie call per request)

**Concurrent Sessions:** No issues identified (separate cookies per browser)

**Cookie Size:** Single cookie, no growth

**Session Storage:** No new requirements

**Logging/Audit:** Need to verify audit logs capture sliding window extensions correctly

**Assessment:** Low risk for side effects, assuming other security checks pass.

---

### 6. TESTING GAPS ⚠️ SECURITY TESTS MISSING

The approval pack's test plan covers functionality but is missing security validation:

**Missing Security Tests:**
- [ ] Verify HTTPS enforcement (no HTTP fallback)
- [ ] Verify `secure=True` flag is set
- [ ] Verify CSRF protection (samesite behavior)
- [ ] Verify XSS protection (httponly prevents JavaScript access)
- [ ] Verify logout actually clears the cookie
- [ ] Verify token tampering is ineffective
- [ ] Verify session timeout still enforced server-side
- [ ] Verify audit logging captures session extension
- [ ] Verify healthcare compliance requirements are met

---

## VERDICT

### 🟡 CONDITIONAL APPROVAL — HARD REQUIREMENTS MUST BE MET

**This change is SAFE to deploy ONLY IF the following are verified and completed:**

---

## HARD REQUIREMENTS (Blocking)

### HR-1: Add `secure=True` Flag to Cookie ⛔ MUST FIX

**Current Code:**
```python
response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=3600)
```

**Required Fix:**
```python
response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", secure=True, max_age=3600)
```

**Verification:** 
- [ ] Code updated with `secure=True` before deployment
- [ ] Tested to confirm cookie is not sent over HTTP

**Impact:** Without this, the cookie can be transmitted unencrypted. This is a **security vulnerability**.

---

### HR-2: Verify HTTPS Enforcement in Production ⛔ MUST VERIFY

**Requirement:** Production dashboard must enforce HTTPS (HTTP requests rejected or redirected).

**Verification Steps:**
- [ ] Confirm nginx/Apache/load balancer redirects HTTP → HTTPS
- [ ] Confirm application logs show no HTTP connections
- [ ] Confirm HSTS headers are set (Strict-Transport-Security)
- [ ] Confirm no unencrypted paths serve authentication cookies

**Failure Impact:** If HTTPS is not enforced, tokens can be sniffed in transit.

---

### HR-3: Code Review — Verify Token Validation ⛔ MUST REVIEW

**Requirement:** Code review must confirm:
- [ ] `token` variable is valid and sanitized
- [ ] `token` is already validated by preceding auth logic
- [ ] This code only executes for authenticated requests
- [ ] Malformed/invalid tokens do not cause exceptions
- [ ] Edge cases handled (None, empty, invalid JWT, etc.)

**Review Checklist:**
- [ ] Trace `token` origin in the middleware
- [ ] Confirm auth validation happens before set_cookie
- [ ] Confirm no exception handling gaps
- [ ] Confirm consistent with existing session management

**Failure Impact:** Invalid token in cookie could cause authentication failures or expose invalid data.

---

### HR-4: Server-Side Session Validation ⛔ MUST VERIFY

**Requirement:** Server-side session store must enforce its own timeout, independent of browser cookie.

**Verification:**
- [ ] Review session storage implementation (Redis/database/memory)
- [ ] Confirm session entry expires server-side (not just relying on cookie max_age)
- [ ] Confirm server validates token signature/freshness on every request
- [ ] Confirm server rejects expired sessions even if cookie is present
- [ ] Confirm session invalidation on logout clears server-side entry

**Failure Impact:** If server doesn't enforce timeout, sessions could extend indefinitely beyond policy.

---

### HR-5: Logout Flow — Verify Cookie is Cleared ⛔ MUST TEST

**Requirement:** Explicit logout must completely clear the session cookie.

**Verification:**
- [ ] Logout endpoint explicitly deletes the SESSION_COOKIE
- [ ] Browser cookie is cleared (max_age=0 or expires=past)
- [ ] Server-side session entry is invalidated
- [ ] Test: After logout, cookie should be gone
- [ ] Test: Subsequent requests without cookie are denied

**Failure Impact:** If logout doesn't clear the cookie, users cannot log out (security issue).

---

## STRONG RECOMMENDATIONS (Should Do Before Deployment)

### SR-1: Healthcare Compliance Review
Verify that sliding window sessions comply with:
- [ ] Churchtown Medical Centre security policy
- [ ] GDPR/UK GDPR inactivity requirements
- [ ] NHS Digital security standards (if applicable)
- [ ] Organizational policy on maximum session duration

**Action:** Have security/compliance team review before deployment.

---

### SR-2: Enhanced Audit Logging
Add logging for session window extension:
```python
# Log sliding window extension
logger.info(f"Session extended for user={user_id}, new_expiry={now + timedelta(seconds=3600)}")
```

**Benefit:** Creates audit trail of active sessions for compliance and investigation.

---

### SR-3: Add Session Monitoring & Alerting
```python
# Alert on unusual session patterns
if session_extension_count > threshold_per_hour:
    alert(f"Suspicious session activity: {user_id} has extended session {count} times")
```

**Benefit:** Detects potential session hijacking or abuse.

---

### SR-4: Security Test Coverage
Before production deployment, add explicit security tests:
- [ ] HTTPS-only validation
- [ ] XSS protection (httponly prevents JS access)
- [ ] CSRF protection (samesite behavior)
- [ ] Token signature validation
- [ ] Session invalidation on logout
- [ ] Concurrent session limits (if applicable)

---

## SIGN-OFF

### GUARDRAIL VERDICT: 🟡 CONDITIONAL APPROVAL

**Status:** Approved for deployment **IF AND ONLY IF** all Hard Requirements (HR-1 through HR-5) are completed and verified before implementation.

**SafetyLevel:** 
- Current proposal: ⚠️ UNSAFE (missing `secure` flag + unverified assumptions)
- With hard requirements met: ✅ SAFE

**Deployment Readiness:**
- ❌ **NOT READY** — Hard requirements must be addressed first
- ✅ **READY** — Once all HR items are checked off

---

## REQUIRED NEXT STEPS

1. **ControlTower:** Address hard requirements in approval pack
   - [ ] Update code to include `secure=True`
   - [ ] Add HTTPS enforcement verification to preconditions
   - [ ] Add code review checklist for token validation
   - [ ] Add server-side session validation verification
   - [ ] Add logout flow testing to test plan

2. **Development Team:** Complete code review
   - [ ] Review token validation in middleware
   - [ ] Verify logout clears session properly
   - [ ] Confirm server-side session timeout is independent

3. **Security/Compliance:** Review regulatory alignment
   - [ ] Confirm sliding window complies with healthcare policy
   - [ ] Verify audit logging is adequate

4. **QA/TestBench:** Add security test cases
   - [ ] HTTPS enforcement test
   - [ ] XSS/CSRF protection tests
   - [ ] Logout verification test
   - [ ] Session invalidation test

5. **Operations/DevOps:** Prepare monitoring
   - [ ] Session extension logging enabled
   - [ ] Anomaly detection configured
   - [ ] Rollback procedure tested

---

## ESCALATION PATH

If any Hard Requirement cannot be satisfied:
1. Escalate to Saeed with detailed explanation
2. Request exception approval or alternative solution
3. Do NOT proceed with deployment until escalation is resolved

---

## GUARDRAIL APPROVAL CHAIN

| Item | Status | Notes |
|------|--------|-------|
| **HR-1: `secure=True` flag** | ⏳ PENDING | Must be added to code before deployment |
| **HR-2: HTTPS enforcement verification** | ⏳ PENDING | Must be verified before deployment |
| **HR-3: Code review (token validation)** | ⏳ PENDING | Must be completed before deployment |
| **HR-4: Server-side session validation** | ⏳ PENDING | Must be verified before deployment |
| **HR-5: Logout flow test** | ⏳ PENDING | Must be tested before deployment |
| **Healthcare compliance check** | ⏳ PENDING | Recommended before deployment |
| **Audit logging enhancement** | ⏳ PENDING | Recommended before deployment |
| **Security test coverage** | ⏳ PENDING | Recommended before deployment |

---

## SUMMARY FOR SAEED

**Question:** Is this safe to deploy?

**Answer:** 
- **Current state:** ❌ Not yet — missing `secure` flag and unverified assumptions
- **With hard requirements met:** ✅ Yes — code is standard practice with adequate protections
- **Timeline:** 1-2 hours to complete verification + code review
- **Risk if deployed now:** MODERATE (missing `secure` flag exposes token to network interception)
- **Risk if all HR items verified:** LOW (standard sliding window session with appropriate protections)

**Recommendation:** 
Address the 5 hard requirements, then resubmit for final Saeed sign-off. Do not deploy the code change until these items are checked off.

---

**Conducted By:** GuardRail Agent  
**Approval Status:** 🟡 CONDITIONAL — Awaiting hard requirements completion  
**Date:** 2026-05-23  
**Next Step:** ControlTower to update approval pack with HR completions, then resubmit to Saeed


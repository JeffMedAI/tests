# APPROVAL PACK: Cookie Expiry Mismatch Fix
**Production Dashboard Outage — dashboard.app-avamed.uk**

---

## EXECUTIVE SUMMARY

**Issue:** Users automatically logged out after exactly 60 minutes, regardless of activity.

**Root Cause:** Cookie expiry mismatch. Server-side session window slides on every request, but browser cookie (`max_age=3600`) never refreshes — creating a hard logout deadline.

**Proposed Fix:** 1-line addition to `enforce_auth` middleware to refresh browser cookie on every authenticated request.

**Risk Level:** LOW-MEDIUM (security-sensitive code path, but minimal change footprint)

**Estimated Effort:** 15 minutes implementation + 30 minutes testing

---

## CHANGE DETAILS

### File Changed
`dashboard/app/main.py` — `enforce_auth` middleware

### Code Change
**Location:** After `response = await call_next(request)`

**Addition:**
```python
response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=3600)
```

**Context (before and after):**
```python
async def enforce_auth(request: Request, call_next):
    # ... auth check logic ...
    response = await call_next(request)
    
    # NEW: Refresh cookie on every authenticated request
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=3600)
    
    return response
```

### What This Does
- Sets browser cookie on **every** authenticated request (not just login)
- Keeps `max_age=3600` in sync with server's sliding session window
- User stays logged in as long as they're active
- Cookie expires 60 minutes after **last activity**, not login

---

## BUSINESS IMPACT

**Current State (BROKEN):**
- Users forced to log back in every 60 minutes
- Interrupts workflow, especially during patient consultations
- Critical medical staff cannot maintain continuous dashboard access
- Staff workaround: Re-login on session expiry (unacceptable)

**After Fix (WORKING):**
- Users stay logged in while active
- Session extends with each request (standard sliding window behavior)
- No interruption to clinical workflows
- Aligns with user expectations and healthcare data access requirements

---

## RISK ASSESSMENT

### Risks Identified
1. **Security: Session fixation** — Could extend compromised session indefinitely if attacker has stolen token
   - *Mitigation:* Existing `httponly` + `samesite=lax` flags prevent XSS/CSRF attacks that would steal token
   - *Residual Risk:* Network interception (HTTPS required — verify in deployment)

2. **Security: Cookie tampering** — Malicious actor modifies cookie max_age
   - *Mitigation:* `httponly` flag prevents JavaScript access; browser enforces max_age client-side as safety net
   - *Residual Risk:* Negligible (server-side session is source of truth)

3. **Performance:** Cookie refresh on every request
   - *Mitigation:* Single set_cookie call, minimal overhead
   - *Residual Risk:* Negligible (microseconds per request)

4. **Cookie storage limits:** Multiple cookie refresh cycles
   - *Mitigation:* Single cookie, not accumulated
   - *Residual Risk:* None

### Overall Risk Rating
**LOW-MEDIUM** — Code change is minimal, cookie handling is standard practice, but security-sensitive code path requires careful review.

---

## ROLLBACK PLAN

### If Issues Occur
**Time to rollback:** 2 minutes (remove 1 line of code)

**Steps:**
1. Remove the `response.set_cookie(...)` line from `enforce_auth` middleware
2. Restart Flask service
3. Users will revert to 60-minute hard logout behavior

**Verification:**
- Login and remain idle > 60 minutes
- Verify logout occurs at 60-minute mark
- Confirm user must re-login

---

## TEST PLAN

### Pre-Implementation (Sandbox)
- [ ] Code review: Verify syntax and logic
- [ ] Check existing SESSION_COOKIE constant definition
- [ ] Verify httponly + samesite flags are secure defaults

### Post-Implementation (QA)
- [ ] Login with test user account
- [ ] Remain idle for 65 minutes (past old 60-minute deadline)
- [ ] Verify still logged in (session active)
- [ ] Make a request at 65+ minutes
- [ ] Verify cookie updated with new 3600s max_age
- [ ] Log out and verify session destroyed
- [ ] Test on multiple browsers (Chrome, Firefox, Safari)
- [ ] Verify HTTPS only (no cookie refresh over HTTP)

### Production Validation
- [ ] Deploy to production
- [ ] Monitor session logs for any expiry anomalies
- [ ] Alert: If unexplained logouts spike, rollback immediately
- [ ] Confirm staff can maintain >60 minute active sessions

---

## DEPENDENCY CHECK

### Required Preconditions
- [ ] SESSION_COOKIE constant defined in config
- [ ] `enforce_auth` middleware is in place and functioning
- [ ] Flask session management configured correctly
- [ ] HTTPS enforced in production

### Compatibility
- Works with existing session storage (any backend)
- No database changes required
- No client-side changes required
- No configuration changes required

---

## TIMELINE & OWNERSHIP

| Phase | Owner | Duration | Status |
|-------|-------|----------|--------|
| Approval Pack Creation | ControlTower (Claude) | — | ✅ COMPLETE |
| GuardRail Safety Review | GuardRail Agent | 15 min | ⏳ PENDING |
| Saeed Final Sign-off | Saeed | — | ⏳ PENDING |
| Implementation | DX Agent | 15 min | ⏳ BLOCKED |
| QA Testing | TestBench | 30 min | ⏳ BLOCKED |
| Production Deployment | DX Agent | 5 min | ⏳ BLOCKED |
| Post-Deployment Monitoring | DevOps | 30 min | ⏳ BLOCKED |

---

## IMMEDIATE WORKAROUND

**For staff affected NOW:**
Staff should log back in to restore access while code fix is prepared. This is temporary — the permanent fix will be deployed within the hour.

---

## SIGN-OFF TRACKING

| Role | Status | Signature/Approval | Date |
|------|--------|-------------------|------|
| ControlTower | ✅ Pack Created | Claude | 2026-05-23 |
| GuardRail | ⏳ **AWAITING REVIEW** | — | — |
| Saeed | ⏳ **AWAITING FINAL SIGN-OFF** | — | — |

---

## SUPPORTING DOCUMENTS

- Investigation Report: Root cause analysis of 60-minute logout
- Code Diff: Before/after middleware code
- Session Architecture Doc: How sliding window sessions work in this codebase
- Security Policy: Cookie handling standards for this organization

---

**Approval Pack Status:** Ready for GuardRail independent safety review

**Next Step:** GuardRail Agent to review security implications and approve/flag concerns

---

*Prepared by: ControlTower (Claude)*  
*Date: 2026-05-23*  
*Project: Churchtown Medical Centre Dashboard*  
*Issue: Production outage — cookie expiry mismatch*

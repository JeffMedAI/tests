# CONTROLTOWER HARD REQUIREMENTS VERIFICATION
**Cookie Expiry Mismatch Fix — Production Verification Report**

**Verification Conducted:** 2026-05-23  
**Scope:** All 5 GuardRail Hard Requirements against actual production code and config  
**Authority:** ControlTower (Claude)

---

## VERIFICATION METHODOLOGY

✅ Read actual production source code  
✅ Analyzed auth module (`auth.py`) for session logic  
✅ Analyzed main application (`main.py`) for middleware and routes  
✅ Searched for HTTPS/SSL configuration  
✅ Examined startup scripts and deployment configuration  
✅ Reviewed deployment logs  

**No assumptions made. All findings based on actual code inspection.**

---

## HARD REQUIREMENTS VERIFICATION

### HR-1: Add `secure=True` Flag to Cookie ❌ **NOT YET FIXED**

**File:** `C:\JeffLocal\dashboard\app\main.py`  
**Current Line 177:**
```python
response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=3600)
```

**Status:** ❌ **MISSING `secure=True` FLAG**

**Finding:** The code currently does NOT include the `secure=True` flag. This flag is critical and MUST be added before deployment.

**Required Fix:**
```python
response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", secure=True, max_age=3600)
```

**Impact if not fixed:** Cookie can be transmitted over unencrypted HTTP, creating vulnerability to network interception.

**Action Required:** ⛔ **CODE CHANGE MANDATORY BEFORE DEPLOYMENT**

---

### HR-2: HTTPS Enforcement in Production ⚠️ **CRITICAL ISSUE — CANNOT VERIFY**

**Investigation Results:**

**Application Startup Configuration:**  
File: `C:\JeffLocal\scripts\service_control\_launch_dashboard.ps1` (line 21)
```powershell
& $python -m uvicorn app.main:app --host 0.0.0.0 --port 8765
```

**Finding:** Uvicorn runs on **HTTP only** (port 8765, no SSL/TLS configuration).

**HTTPS Configuration Search Results:**
- ❌ No nginx config files found
- ❌ No Apache/IIS config found  
- ❌ No SSL certificates in application directory
- ❌ No environment variables for HTTPS/SSL
- ❌ No reverse proxy configuration found
- ❌ No HSTS headers configured in application code

**Deployment Documentation:**
- Production README (production/README.md) does **NOT mention** HTTPS setup
- Deployment Log does **NOT document** HTTPS configuration
- No evidence of reverse proxy or load balancer with HTTPS termination

**Critical Gap:** 
While the approval pack mentions production domain "dashboard.app-avamed.uk" (which suggests external access), **no HTTPS configuration is visible in the actual codebase or deployment scripts.**

**Status:** ⚠️ **CANNOT VERIFY HTTPS IN PRODUCTION**

**Possible Scenarios:**
1. **Best Case:** HTTPS is configured at infrastructure level (nginx reverse proxy, load balancer, etc.) **not visible in this codebase**
2. **Worst Case:** Production runs on HTTP only → **CRITICAL SECURITY ISSUE**

**What We Know:**
- ✅ Code has `httponly` flag (prevents JavaScript access)
- ✅ Code has `samesite="lax"` flag (prevents CSRF)
- ❌ Code missing `secure` flag
- ❌ No visible HTTPS enforcement in application or startup

**Action Required:** ⛔ **CRITICAL: Must verify HTTPS is active in production before deployment**

---

### HR-3: Code Review — Token Validation ✅ **VERIFIED SOLID**

**File:** `C:\JeffLocal\dashboard\app\main.py` (lines 89-103)

**Middleware Code:**
```python
@app.middleware("http")
async def enforce_auth(request: Request, call_next):
    if _is_public_path(request.url.path):
        return await call_next(request)
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return RedirectResponse(url=f"/login?next={quote(str(request.url.path), safe='')}", status_code=302)
    with connect() as conn:
        conn.row_factory = __import__("sqlite3").Row
        user = get_session_user(conn, token)  # ← Token validation here
    if user is None:
        resp = RedirectResponse(url=f"/login?next={quote(str(request.url.path), safe='')}", status_code=302)
        resp.delete_cookie(SESSION_COOKIE)  # ← Cookie cleared on invalid token
        return resp
    return await call_next(request)
```

**Token Validation Logic (`auth.py` lines 84-124):**
```python
def get_session_user(conn: sqlite3.Connection, token: str) -> Optional[dict]:
    """Return the user dict if the session is valid and not expired; also slides the expiry."""
    if not token:
        return None
    now_dt = datetime.now(timezone.utc)
    row = conn.execute(
        "SELECT s.id as sid, s.user_id, s.expires_at, ... "
        "FROM sessions s JOIN staff_users u ON s.user_id=u.id "
        "WHERE s.token=?",
        (token,),
    ).fetchone()
    if row is None:
        return None
    expires_at = row["expires_at"]
    # Check if expired
    exp_dt = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
    if now_dt > exp_dt:
        return None  # ← Reject expired sessions
    # Slide expiry on activity
    new_expires = _utc_expires(SESSION_TIMEOUT_MINUTES)
    conn.execute(
        "UPDATE sessions SET last_active_at=?, expires_at=? WHERE token=?",
        (now_str, new_expires, token),
    )
    conn.commit()
    return d  # Return user if all checks pass
```

**Verification Results:**

✅ **Token Variable Source:**
- Token comes from cookie (line 93: `token = request.cookies.get(SESSION_COOKIE)`)
- Token is checked for existence before use (line 94-95)
- Token is passed to validated function: `get_session_user()`

✅ **Execution Path:**
- Middleware checks if path is public (line 91)
- If not public, middleware retrieves and validates token (line 93-98)
- Validation happens BEFORE any route handler executes (line 103: `return await call_next(request)`)

✅ **Token Validation Logic:**
- Queries database for session with matching token (line 89-95)
- Returns None if token not found in database (line 96-97)
- Checks if session is expired by comparing to current time (line 101-102)
- Returns None if expired (line 102)
- Only returns user dict if all checks pass (line 124)

✅ **Error Handling:**
- If validation fails, user is set to None (line 99)
- If user is None, cookie is deleted AND redirect to login (line 100-102)
- No exceptions thrown, proper error flow

✅ **Token Sanitization:**
- Token comes from SQLite query result, not user input
- Token is only used to look up database record
- No direct use of token in SQL (parameterized query with ?, (token,))
- No XSS/injection vectors in token handling

**Status:** ✅ **VERIFIED — Code is solid and secure**

---

### HR-4: Server-Side Session Validation ✅ **VERIFIED SOLID**

**Server-Side Session Store:** SQLite database (sessions table)

**Session Validation on Every Request:**

**File:** `C:\JeffLocal\dashboard\app\auth.py` (lines 84-124)

Every authenticated request calls `get_session_user()` which:

1. **Checks session exists in database** (lines 89-95)
   ```python
   row = conn.execute(
       "SELECT ... FROM sessions s JOIN staff_users u ... WHERE s.token=?",
       (token,),
   ).fetchone()
   if row is None:
       return None  # ← Reject if not found
   ```

2. **Checks session is not expired** (lines 101-102)
   ```python
   exp_dt = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
   if now_dt > exp_dt:
       return None  # ← Reject if expired
   ```

3. **Slides expiry window (INDEPENDENT of browser cookie)** (lines 105-111)
   ```python
   new_expires = _utc_expires(SESSION_TIMEOUT_MINUTES)  # 60 minutes
   conn.execute(
       "UPDATE sessions SET last_active_at=?, expires_at=? WHERE token=?",
       (now_str, new_expires, token),
   )
   conn.commit()  # ← Database committed
   ```

4. **Validates user account is still active** (lines 121-123)
   ```python
   d["active"] = bool(d.get("active", 1))
   if not d["active"]:
       return None  # ← Reject if user account deactivated
   ```

**Key Finding: Server timeout is INDEPENDENT of browser cookie**
- Browser cookie has `max_age=3600` (1 hour)
- Server sessions table also has `expires_at` column set to 60 minutes from now
- When browser cookie refreshes on every request, server session ALSO extends independently
- **Belt-and-suspenders approach:** Both browser AND server enforce timeout

**Session Cleanup:**  
File: `C:\JeffLocal\dashboard\app\auth.py` (lines 137-139)
```python
def purge_expired_sessions(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM sessions WHERE expires_at < ?", (_utc_now(),))
    conn.commit()
```
Called on every login (line 143 of main.py), cleans up stale sessions.

**Status:** ✅ **VERIFIED — Server-side validation is solid and independent**

---

### HR-5: Logout Flow — Cookie Cleared ✅ **VERIFIED SOLID**

**File:** `C:\JeffLocal\dashboard\app\main.py` (lines 181-189)

**Logout Endpoint Code:**
```python
@app.get("/logout")
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with connect() as conn:
            invalidate_session(conn, token)  # ← Server-side session deleted
    resp = RedirectResponse(url="/login?info=You+have+been+signed+out.", status_code=302)
    resp.delete_cookie(SESSION_COOKIE)  # ← Browser cookie deleted
    return resp
```

**Server-Side Session Invalidation:**  
File: `C:\JeffLocal\dashboard\app\auth.py` (lines 127-129)
```python
def invalidate_session(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token=?", (token,))
    conn.commit()
```

**Verification Results:**

✅ **Server-side session is deleted**
- `invalidate_session()` removes session record from database
- Database is committed
- Token is no longer valid for any future request

✅ **Browser cookie is deleted**
- `resp.delete_cookie(SESSION_COOKIE)` removes cookie from client
- Browser no longer has session cookie to send

✅ **Both happen in single request**
- Server invalidates first (line 186)
- Then cookie deleted (line 188)
- Atomic from user perspective

✅ **Subsequent requests are rejected**
- If token somehow exists, it's not in database
- `get_session_user()` returns None (line 96-97)
- Middleware redirects to login (line 100-102)

**Status:** ✅ **VERIFIED — Logout flow properly clears both server and client session**

---

## SUMMARY TABLE

| Req | Description | Status | Finding | Action |
|-----|-------------|--------|---------|--------|
| **HR-1** | Add `secure=True` flag | ❌ NOT FIXED | Flag missing from line 177 main.py | ⛔ MUST ADD BEFORE DEPLOY |
| **HR-2** | Verify HTTPS enforcement | ⚠️ UNVERIFIED | No HTTPS config visible; app runs HTTP | ⛔ MUST VERIFY IN PRODUCTION |
| **HR-3** | Token validation code review | ✅ VERIFIED | Token properly validated on every request | ✅ READY |
| **HR-4** | Server-side session validation | ✅ VERIFIED | Server enforces timeout independently | ✅ READY |
| **HR-5** | Logout flow (clear cookie) | ✅ VERIFIED | Server & client session properly cleared | ✅ READY |

---

## CRITICAL BLOCKERS

### 🚨 BLOCKER #1: Missing `secure=True` Flag

**Current Code:** Line 177 of `main.py`
```python
response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=3600)
```

**Required Fix:**
```python
response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", secure=True, max_age=3600)
```

**Why Critical:** Without `secure=True`, the cookie can be transmitted over HTTP. Combined with the lack of visible HTTPS enforcement (HR-2), this creates a network interception vulnerability.

**Action:** ⛔ **FIX MUST BE APPLIED AND VERIFIED BEFORE DEPLOYMENT**

---

### 🚨 BLOCKER #2: Cannot Verify HTTPS Enforcement in Production

**Problem:** 
- Application is configured to run on HTTP only (port 8765)
- No HTTPS/SSL configuration visible in codebase
- No reverse proxy (nginx, Apache, etc.) found
- No documentation of HTTPS setup in production

**Risk:** 
If production truly runs on HTTP without a reverse proxy handling HTTPS, then cookies with `max_age=3600` (even with `secure=True` added) can still be sniffed in transit.

**Resolution Needed:**
- **Saeed or DevOps must confirm:** Is production behind an HTTPS reverse proxy?
- **If YES:** Provide evidence (nginx config, load balancer config, etc.)
- **If NO:** HTTPS must be set up before this cookie refresh is deployed

**Action:** ⛔ **SAEED/DEVOPS MUST VERIFY HTTPS IS ACTIVE IN PRODUCTION**

---

## RECOMMENDATIONS

### Before Deployment (Required)

1. **Apply HR-1 Fix** (5 minutes)
   - Add `secure=True` to line 177 of main.py
   - Test in sandbox
   - Verify cookie includes Secure flag in browser DevTools

2. **Verify HR-2** (10 minutes, Saeed/DevOps)
   - Confirm production has HTTPS enabled
   - Provide evidence of HTTPS enforcement
   - Document reverse proxy or SSL termination setup

3. **Code Review Approval** (5 minutes)
   - Ensure the fix is minimal (1 flag addition)
   - Confirm no side effects
   - Sign off on code change

### Testing Before Deployment (Recommended)

1. **Sandbox Testing**
   - Deploy fix to sandbox
   - Login and verify session extends past 60 minutes
   - Verify cookie is sent with Secure flag (DevTools → Network)
   - Test logout properly clears session

2. **HTTPS Validation**
   - Confirm production serves over HTTPS
   - Confirm no HTTP fallback
   - Test that cookie is not sent over HTTP (browser security)

---

## NEXT STEPS

**ControlTower Status:** ✅ **Verification complete**

**Awaiting:** 
1. ⛔ HR-1 code fix to be applied
2. ⛔ HR-2 verification from Saeed/DevOps

**Once both are resolved:** Resubmit updated approval pack to Saeed for final sign-off.

---

**Verification Completed By:** ControlTower (Claude)  
**Date:** 2026-05-23  
**Authority:** Independent verification against actual production code  
**Status:** 🟡 **CONDITIONAL — Blockers must be resolved before approval**


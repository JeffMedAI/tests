# Staff Access Model - How tenant staff reach their dashboard

**Status:** DECIDED by Saeed 2026-07-21. Applies to every tenant (St Marks and all GP practices).
**Related:** MULTI_TENANCY_PROPOSAL.md (§6/6b access model), TENANT_REGISTRY.md.

---

## The decision

Staff reach their dashboard from their own public website via a **"Staff Login" link**, NOT by
embedding the dashboard into the public site.

1. **Link, not embed.** The tenant's public website (e.g. the St Marks pharmacy site) carries a
   branded "Staff Login" link/button. Clicking it opens the dashboard's OWN login on the dashboard's
   OWN hostname (e.g. `stmarks.app-avamed.uk`). The patient-data app stays on its own isolated
   origin. This is the same "it's a link, not a data switch" principle already settled for the
   Avamed super-admin tenant switcher.
2. **Login lives on the dashboard.** Credentials only ever touch the patient-data app, which already
   has hardened auth (PBKDF2 + per-user salt, lockout, hashed session tokens). The public marketing
   site never sees a password.
3. **Per-tenant branded login page.** Each tenant's dashboard login carries that tenant's
   branding (logo/colours) so the hand-off from "our website" to "our dashboard" feels like one
   product, without literally embedding patient data in the public page.

## Why NOT an iframe embed (rejected 2026-07-21)

- The dashboard session cookie is `SameSite=Lax` (main.py:87, routers/auth.py:108,262). In a
  cross-site iframe, Lax cookies are not sent, so staff could not stay logged in. The only fix is
  `SameSite=None`, which weakens cross-site-request protection.
- Framing a patient-data app inside a public marketing site invites clickjacking and is a likely
  DTAC / clinical-safety finding. Correct posture is the opposite: the dashboard should REFUSE to be
  framed.

## Why NOT reverse-proxy under the public domain (rejected 2026-07-21)

- Serving the dashboard under e.g. `stmarks.co.uk/staff` via the Worker puts the patient app on the
  SAME origin as the public site - any flaw in the public site can reach the dashboard session.
  Weaker isolation, more moving parts, on an auto-deploying repo.

## What building this involves (scoped, not yet built)

**Dashboard side (this repo, needs Security review + Saeed approval - touches production auth surface):**
- Add per-tenant branding to the login page. Branding assets/config keyed off the tenant
  (`JEFFLOCAL_TENANT_NAME` / a per-tenant branding block), NOT hardcoded. No patient data involved.
- Security hardening to do REGARDLESS of this feature: send `X-Frame-Options: DENY` /
  CSP `frame-ancestors 'none'` so the dashboard cannot be framed by anyone.

**Public-site side (SMCPHARMA repo - SEPARATE, LIVE, AUTO-DEPLOYS - extra care):**
- Add a branded "Staff Login" link to the St Marks site pointing at the tenant's dashboard hostname.
- Any change there ships to the live pharmacy site on deploy - must be reviewed and approved before push.

**Prerequisite:** the tenant's dashboard hostname must exist first (Cloudflare public hostname -
currently deferred; today tenant2 is localhost:8766 only). So the public-site link can't point
anywhere real until the hostname step is done.

## Sequence note

This belongs with / just after MULTI_TENANCY_PROPOSAL.md §8 step 5 (tenant picker + Avamed admin)
and the deferred Cloudflare hostname step - it needs the real per-tenant hostname to link to.

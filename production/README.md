# Production Environment — Churchtown Medical Centre

This folder contains production deployment configuration and records. **Code is NEVER edited here directly.** All changes originate in sandbox and are deployed by DevOps after executive approval.

## Deployment Target
- **Location:** Churchtown Medical Centre on-premises server
- **Deployment agent:** DevOps
- **Authority required:** Saeed (executive approval) + GuardRail (compliance approval)

## Deployment Steps (executed by DevOps)
1. Code deployment — move from sandbox → production server
2. Database migrations — run on production SQLite
3. Configuration deployment — update config files on production
4. Service restart — restart all services
5. Smoke tests — quick validation in production
6. Rollback — execute immediately if smoke tests fail

## Records
Deployment logs and rollback logs are stored in:
`sandbox/audit/approval_packs/`

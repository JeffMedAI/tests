# DevOps — Infrastructure, Scripts & Configuration

All infrastructure code lives here. Owned and maintained by the DevOps agent.

## Structure

```
devops/
  scripts/    Deployment, migration, rollback, and smoke test scripts
  configs/    Environment configuration files (non-secret)
```

## Scripts
Deployment scripts follow the naming convention:
- `deploy_<version>_<date>.sh` — full deployment script
- `migrate_<version>_<date>.sh` — database migration script
- `rollback_<version>_<date>.sh` — rollback script (must be tested before deployment)
- `smoke_test_<version>_<date>.sh` — post-deployment smoke tests

## Rules
- Every deployment script must have a corresponding rollback script
- Rollback scripts must be tested in sandbox before production deployment
- Secrets and credentials are NEVER stored in this folder — use the production server's secure config store

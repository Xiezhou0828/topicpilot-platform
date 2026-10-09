# Rollback and recovery readiness

## Application rollback

The Render dashboard exposes provider rollback links for the API and Worker live deployments. A safe application rollback for any future deployment of the forensic-only changes is to redeploy the last verified application SHA 9703c956... (or the previously verified fded17f... release through the protected release workflow), then verify /healthz, /readyz, service revision, and /api/v2/topics. No database rollback is required for PRs #80, #82, or #83 because they contain no migration or schema change.

## Database recovery

Neon Production readback verified a 6-hour history window, no snapshot, and no backup schedule. At readback the rolling earliest restore time was 2026-10-09 13:37 GMT+8, so no 2026-10-08 point remained. This confirms a provider setting and a current rolling boundary, but not an isolated restore target, restore operator, or restore drill. Consequently, a rollback plan still cannot safely include Production database restore.

DATABASE_RECOVERY_READINESS=BLOCKED

The recovery runbook must be completed by the Owner/provider with an isolated target before scheduler approval. Do not use Render rollback as a substitute for database recovery, and do not restore or migrate Production as part of this task.

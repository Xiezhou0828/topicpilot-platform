# Worker runtime identity

## Independent provider evidence

- Provider: Render.
- Service: topicpilot-live.
- Service ID: srv-da6okdpsrm7s73aqbnn0.
- Source: Xiezhou0828/topicpilot-platform, main.
- Last successfully deployed commit: 9703c956....
- Live deploy: dep-db3vkl7f3r2c73domakg.
- Trigger shown by Render: Deploy Hook.
- Auto-deploy: disabled.
- Dashboard: https://dashboard.render.com/worker/srv-da6okdpsrm7s73aqbnn0/deploys/dep-db3vkl7f3r2c73domakg

The provider page ties the live service to an immutable source commit. This is independent runtime evidence and is stronger than an expected environment variable. The repository startup contract remains topicpilot-live, backed by render.yaml.

## Result

WORKER_RUNTIME_IDENTITY=PASS
WORKER_RUNTIME_SHA=9703c956...
WORKER_ARTIFACT_IDENTITY=Render live deployment dep-db3vkl7f3r2c73domakg, source commit 9703c956...
WORKER_CANONICAL_MATCH=NO

The Worker matches the Task 006 canonical/runtime SHA, but not the current canonical fc11856.... Task 007 did not deploy a new Worker. Dashboard logs show the Worker process polling its scheduler; this does not mean Task 007 activated the scheduler. The effective publication writer remained fail-closed with status BLOCKED.

## Oct 8 blocker readback

For schedulerDate=2026-10-08, Render logs show `[qtt4j]` `post_close_scheduled_complete` with `status=BLOCKED` and `reasonCodes=["REFERENCE_PREFLIGHT_PendingRollbackError"]` from 19:50 through 23:55 GMT+8 at five-minute retry intervals. Searches for `ProgrammingError`, `UndefinedColumn`, `InFailedSqlTransaction`, and SQLSTATE produced no earlier PostgreSQL exception. The first transaction-causing error before the mapped reason therefore remains unavailable; no Worker code or runtime was changed.

# Daily formal publication — Production activation evidence

Verification date: 2026-10-06, Asia/Taipei. This report records bounded Production activation and read-only post-activation verification. No formal publication, POST_CLOSE, recovery, backfill, correction, replay, historical-date test, manual receipt, or synthetic `DATA_READY` event was executed.

```text
TASK=TASK-DAILY-FORMAL-PUBLICATION-ORCHESTRATION-PRODUCTION-ACTIVATION-001
TASK_STATUS=COMPLETE_PRODUCTION_ACTIVATED
REQUIRED_TERMINAL_STATE=POST_DEPLOY_VERIFIED
ACHIEVED_TERMINAL_STATE=POST_DEPLOY_VERIFIED
TASK_COMPLETE=YES
OWNER_AUTHORIZATION=GRANTED_FOR_BOUNDED_PRODUCTION_ACTIVATION
PRODUCTION_ACTIVATION_VERIFIED=YES
FIRST_LIVE_DAILY_RUN_VERIFIED=NO_PENDING_NEXT_TRADING_SESSION
DAILY_FORMAL_PUBLICATION_PRODUCTION_ACTIVE=YES
DAILY_DATA_PUBLICATION_SEPARATE_FROM_SOFTWARE_RELEASE=YES
FIRST_LIVE_DAILY_RUN_PENDING_NORMAL_SCHEDULER=YES
TASK_SCOPE_REGRESSION_FREE=YES
COMPETING_SCHEDULER=NONE_CONFIRMED
FOLLOW_UP_REASON=Wait for the next normal eligible trading session plus DATA_READY; never manually trigger the first live Daily run.
```

## Canonical release and alert contract

- Canonical base: `8894138fc930b4512541cacd5214162cd66b4c8f`.
- Production release: `6fff533168b1823052071f6d88d1f266397d327d`, ordinary merge [PR 74](https://github.com/Xiezhou0828/topicpilot-platform/pull/74). No squash, rebase, force push, or branch-protection change.
- The minimal runtime provenance correction is in `services/api/src/topicpilot_api/live/receipt.py`: `RUNTIME_PROVENANCE_TRUST_FAILURE` is emitted when required Worker/API/migration provenance is not `READY`, with `severity=CRITICAL`, `actionRequired=true`, timestamp, and `unverifiedComponents`. The event is carried by normal, correction, and operational receipt event collections; Web is optional for this activation.
- Focused receipt, forward-runner, and live-runtime tests: `29 passed`; Ruff passed.

## Original seven-failure reconciliation

`TASK_SCOPE_REGRESSION_FREE=YES` is supported by the uncancelled exact-SHA CI and equivalent clean baseline/candidate boundary evidence. No timeout was relabelled as a pass.

1. `test_canonical_observation_implementation.py::test_canonical_revision_is_linear_after_0018`: stale canonical-head assertion; approved 0049 lineage now validates.
2. `test_v2_architecture_freeze.py::test_v2_metadata_contains_only_implemented_tables`: stale allowlist assertion; approved receipt relation now validates.
3. Five worker-boundary families—cold `live.cli` import, `provider_preflight` import, automatic post-close dry-run, missing-credentials fail-closed, and provider-failure fail-closed—were reconciled as variable cold-subprocess timeouts, not deterministic release regressions.

Evidence:

- Clean baseline `8894138…`: `3 failed, 11 passed`, 308.81s; failures were `live.cli`, `provider_preflight_cli`, and automatic dry-run.
- Clean candidate equivalent state: `3 failed, 11 passed`, 368.79s; failures were `live.cli`, public-export identity, and missing-credentials. Failure membership varied.
- Current Windows/Chinese-path run after the alert correction: `6 passed, 8 failed`, 389.24s; all failures were 30-second `TimeoutExpired` cold subprocesses, with no assertion-level receipt/publication failure. Additional timed-out nodes were normalizer/history imports and post-close/provider paths.
- The authoritative Linux release checks below passed all required gates, with no deterministic new failure attributable to the alert correction.

## CI, migration, and deployment ledger

- [Canonical exact-SHA CI 37336391864](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37336391864), exact `6fff533…`: Secret scan, backend/migration/OpenAPI, frontend install/test/build, and Docker Compose smoke all SUCCESS.
- [API/Worker protected release 37337936549](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37337936549), exact `6fff533…`: validation and API/Worker trigger SUCCESS; migration and Sites packaging skipped intentionally.
- [Worker activation release 37339550361](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37339550361), exact `6fff533…`: validation and protected Worker trigger SUCCESS; API, migration, and Sites packaging skipped intentionally.
- [Production migration 37316409516](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37316409516) applied `0049_task_daily_formal_publication_receipt` before release. It was additive receipt architecture, not a formal-data rewrite.
- Nonsecret Worker marker `TOPICPILOT_API_RUNTIME_SHA=6fff533…` was provisioned. No secret values were exposed.

## Post-activation readback

API GET-only readbacks:

```json
{"status":"ok","gitSha":"6fff533168b1823052071f6d88d1f266397d327d"}
{"status":"ready","gitSha":"6fff533168b1823052071f6d88d1f266397d327d"}
{"alembicRevision":"0049_task_daily_formal_publication_receipt","readOnly":true}
{"status":"NOT_FOUND","tradingDate":"2026-10-06","receipt":null}
{"tradingDate":"2026-10-06","items":[],"total":0,"limit":50}
```

`GET /api/v1/meta/data-status` remained the existing 404 problem detail, `No completed bundle has been imported`; no legacy bundle was created or relabelled as Daily publication.

Render readback:

- API `topicpilot-api`: Live at `6fff533…`; health/readiness matched.
- Worker `topicpilot-live` (`srv-da6okdpsrm7s73aqbnn0`): Live at `6fff533…`; `topicpilot-worker-revision --json` returned `READY` with the same SHA.
- Worker Docker command: `topicpilot-live`; Auto Deploy: Off.
- Effective config: `Asia/Taipei`, poll `300s`, post-close `13:45`, soft target `14:30`, hard deadline `15:00`, calendar `TW_MARKET`.
- Post-activation logs showed `scheduler_decision` `mode=WAIT` and `scheduler_wait` `reason=MARKET_CLOSED`; no formal updater/publication was observed.

## Competing scheduler audit

`COMPETING_SCHEDULER=NONE_CONFIRMED`:

- Current `.github/workflows` contains no `schedule:`/cron trigger. The historical `relation-weight-bootstrap.yml` registry entry was manual `workflow_dispatch`, unrelated to Daily publication, and its source is absent from current main.
- Render showed exactly two active services: `topicpilot-api` and `topicpilot-live`; no Render Cron or third worker.
- Native Sites automations were empty.
- No new scheduler, cron, or external scheduling authority was created.

The canonical scheduler is the existing Render Background Worker `topicpilot-live`. Software release remains separate from Daily data publication.

## Sites, safety, and receipts

- Sites was not republished. Existing native state: production URL `https://topicpilot-platform.game0962046460.chatgpt.site`, project `appgprj_6a6ce02bd75c81919ab3678ebf013c53`, active v73, native source `771afdcfa5342a9ffd9d90b8c2f5ee0e78a132c0`, archive digest `sha256:06b59b6820ec4e215ac1ec57d3d91cd634d7f40b7c57abd943d75034247f62ae`, deployment `appgdep_6ac2ec2ee1c881919354e712b559227b` succeeded; Sites automations empty.
- Trigger remains eligible `TW_MARKET` trading session plus `DATA_READY`; single-flight, advisory lock, receipt idempotency, and failed-closed boundaries remain in deployed code.
- `FORMAL_DATA_MANUALLY_MUTATED=NO`; `FAKE_LIVE_PUBLICATION_EXECUTED=NO`; no POST_CLOSE, recovery, backfill, correction, replay, clock change, or historical-date test.
- No external notification provider was invented. Operator visibility is the durable receipt/event model plus Render logs; future trust failure is critical/action-required.
- Rollback readiness is bounded by prior successful exact-SHA Render deployments; no rollback was needed or exercised.

Historical local evidence screenshots:

- `C:/Users/acer/.codex/attachments/9c1b0bcf-7a23-4bab-a525-402f8f724157/worker-runtime-readback.jpg`
- `C:/Users/acer/.codex/attachments/9c1b0bcf-7a23-4bab-a525-402f8f724157/worker-safe-hold.jpg`

The only remaining expected observation is the first legitimate unattended Daily run on the next normal eligible trading session plus `DATA_READY`; it must not be manually triggered. If any future provenance/readiness gate fails, the scheduler must fail closed and surface the critical/action-required event.

STOP CONDITION HONOURED: no manual first run, no backfill/recovery/correction/replay, no fake receipt, and no unrelated cleanup.

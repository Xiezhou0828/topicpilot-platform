# Daily formal publication — Production activation evidence

Verification date: 2026-10-06, Asia/Taipei. This report records the bounded production activation and read-only post-activation verification. No formal publication, POST_CLOSE, recovery, backfill, correction, replay, historical-date test, manual receipt, or synthetic DATA_READY event was executed.

```text
TASK=TASK-DAILY-FORMAL-PUBLICATION-ORCHESTRATION-PRODUCTION-ACTIVATION-001
TASK_STATUS=COMPLETE_PRODUCTION_ACTIVATED
TASK_TYPE=release
REQUIRED_TERMINAL_STATE=POST_DEPLOY_VERIFIED
ACHIEVED_TERMINAL_STATE=POST_DEPLOY_VERIFIED
TASK_COMPLETE=YES
OWNER_AUTHORIZATION=GRANTED_FOR_BOUNDED_PRODUCTION_ACTIVATION
FOLLOW_UP_REQUIRED=YES
FOLLOW_UP_REASON=Wait for the next normal eligible trading session plus DATA_READY; do not manually trigger the first live Daily run.
PRODUCTION_ACTIVATION_VERIFIED=YES
FIRST_LIVE_DAILY_RUN_VERIFIED=NO_PENDING_NEXT_TRADING_SESSION
DAILY_FORMAL_PUBLICATION_PRODUCTION_ACTIVE=YES
DAILY_DATA_PUBLICATION_SEPARATE_FROM_SOFTWARE_RELEASE=YES
FIRST_LIVE_DAILY_RUN_PENDING_NORMAL_SCHEDULER=YES
TASK_SCOPE_REGRESSION_FREE=YES
COMPETING_SCHEDULER=NONE_CONFIRMED
```

## Canonical lineage and exact release

- Canonical implementation base: `8894138fc930b4512541cacd5214162cd66b4c8f`.
- Production release SHA: `6fff533168b1823052071f6d88d1f266397d327d`, the ordinary merge commit for [PR 74](https://github.com/Xiezhou0828/topicpilot-platform/pull/74).
- The release preserved merge lineage; no squash, rebase, force push, or branch-protection change was used.
- At activation, `origin/main` was `e47d43d9d5a5b64c86a8b14d6f86c9189016525e`; its intervening change was documentation-only and did not change the deployed API/Worker release tree. The closure report itself is documentation-only.
- The parent legacy checkout and unrelated pre-existing dirty files were preserved and not included in this report commit.

## Runtime provenance trust-failure contract

The minimal contract correction is present in `services/api/src/topicpilot_api/live/receipt.py` and merged in the release SHA:

- `RUNTIME_PROVENANCE_TRUST_FAILURE` is emitted when required Worker, API, or migration provenance is not `READY`.
- The event is machine-readable with `severity=CRITICAL`, `actionRequired=true`, timestamp, and `unverifiedComponents`.
- The event is appended to normal, correction, and operational receipt event collections. Web remains optional for this activation because no Web release was performed.
- Focused receipt, forward-runner, and live-runtime validation passed: `29 passed`; Ruff passed.

## Reconciliation of the original seven failures

`TASK_SCOPE_REGRESSION_FREE=YES` is supported by exact canonical CI plus equivalent clean baseline/candidate boundary evidence. No local timeout was relabelled as a pass.

1. `test_canonical_observation_implementation.py::test_canonical_revision_is_linear_after_0018` was a stale canonical-head assertion; the approved 0049 lineage is now validated.
2. `test_v2_architecture_freeze.py::test_v2_metadata_contains_only_implemented_tables` was a stale allowlist assertion; the approved receipt relation is now validated.
3. The five worker-boundary timeout families were reconciled as environment/cold-subprocess instability rather than a deterministic release regression: cold `live.cli` import, `provider_preflight` import, automatic post-close dry-run, missing-credentials fail-closed, and provider-failure fail-closed.

Evidence for the timeout families:

- Exact clean baseline worktree at `8894138…`: `3 failed, 11 passed`, 308.81 seconds. Failures were `live.cli`, `provider_preflight_cli`, and automatic dry-run.
- Exact clean candidate worktree at the equivalent release-preparation state: `3 failed, 11 passed`, 368.79 seconds. Failures were `live.cli`, public-export identity, and missing-credentials. Failure membership was not stable.
- A current Windows/Chinese-path run after the alert correction was `6 passed, 8 failed`, 389.24 seconds; every failure was a 30-second `TimeoutExpired` cold subprocess, with no assertion-level receipt or publication failure. Additional timed-out nodes were normalizer/history imports and post-close/provider paths.
- The independent baseline/candidate runs therefore show no deterministic new failure introduced by the receipt alert correction. The authoritative exact-SHA Linux CI below passed the complete required gates.

Validation evidence:

- [Canonical exact-SHA CI 37336391864](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37336391864), exact `6fff533…`: Secret scan, backend/migration/OpenAPI, frontend install/test/build, and Docker Compose smoke all SUCCESS.
- [API/Worker protected release 37337936549](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37337936549), exact `6fff533…`: validation and API/Worker trigger jobs SUCCESS; migration and Sites packaging intentionally skipped.
- [Worker activation release 37339550361](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37339550361), exact `6fff533…`: validation and protected Worker trigger SUCCESS; API, migration, and Sites packaging intentionally skipped.
- The earlier cancelled latest-main CI was not reused as proof. The uncancelled exact merge-SHA CI above is the canonical passing evidence.

## Production mutation ledger and runtime proof

| Operation | Exact result |
| --- | --- |
| Production migration | [37316409516](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37316409516), migration 0049 applied before release; no formal data rewrite |
| API + dormant Worker release | [37337936549](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37337936549), exact `6fff533…`; API readback and Worker safe-hold readback completed |
| Provenance marker | Nonsecret Worker variable `TOPICPILOT_API_RUNTIME_SHA=6fff533…` saved; no secret values were exposed |
| Scheduler activation | [37339550361](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37339550361), exact `6fff533…`; Worker command restored to `topicpilot-live`, protected deploy completed |

Final API readbacks were GET-only:

```json
{"status":"ok","gitSha":"6fff533168b1823052071f6d88d1f266397d327d"}
{"status":"ready","gitSha":"6fff533168b1823052071f6d88d1f266397d327d"}
{"alembicRevision":"0049_task_daily_formal_publication_receipt","readOnly":true}
{"status":"NOT_FOUND","tradingDate":"2026-10-06","receipt":null}
{"tradingDate":"2026-10-06","items":[],"total":0,"limit":50}
```

`GET /api/v1/meta/data-status` remained the existing 404 problem detail, `No completed bundle has been imported`; no legacy bundle was created or relabelled as a Daily publication.

Final Render readbacks:

- API service `topicpilot-api` was Live at `6fff533…`; health and readiness matched the release SHA.
- Worker `topicpilot-live` (`srv-da6okdpsrm7s73aqbnn0`) was Live at `6fff533…`; `topicpilot-worker-revision --json` returned `READY` with the same SHA.
- Worker command readback was `topicpilot-live`; Auto Deploy remained Off.
- Effective configuration was `Asia/Taipei`, poll `300` seconds, post-close start `13:45`, soft target `14:30`, hard deadline `15:00`, calendar `TW_MARKET`.
- Post-activation logs showed only `scheduler_decision` with `mode=WAIT` and `scheduler_wait` with `reason=MARKET_CLOSED`. No formal publication or updater invocation was observed.

## Sites / Web provenance

No Web build or publish was needed for this backend/Worker activation. Existing native Sites state remains independently identified, not conflated with the API/Worker SHA:

- Production URL: https://topicpilot-platform.game0962046460.chatgpt.site
- Project: `appgprj_6a6ce02bd75c81919ab3678ebf013c53`.
- Active version: v73; native source commit `771afdcfa5342a9ffd9d90b8c2f5ee0e78a132c0`.
- Version ID: `appgprj_6a6ce02bd75c81919ab3678ebf013c53~appgver_55a6eb8f0f488191b33ff722b4e3d906`.
- Archive digest: `sha256:06b59b6820ec4e215ac1ec57d3d91cd634d7f40b7c57abd943d75034247f62ae`.
- Deployment `appgdep_6ac2ec2ee1c881919354e712b559227b` succeeded; Sites automations were empty.

## Competing scheduler / external authority audit

`COMPETING_SCHEDULER=NONE_CONFIRMED` is based on all available repository and connected-service evidence:

- Current `.github/workflows` has no `schedule:` or cron trigger; workflows are dispatch/push/PR based. The historical `relation-weight-bootstrap.yml` registry entry was manual `workflow_dispatch`, unrelated to Daily publication, and its source is absent from current main.
- Render dashboard showed exactly two active services in the workspace: `topicpilot-api` and `topicpilot-live`; no Render Cron or third worker was present.
- Native Sites automations were empty.
- No new scheduler, cron, GitHub scheduled workflow, or external scheduling authority was created.

The canonical scheduler is the existing Render Background Worker `topicpilot-live`. Daily software release remains separate from Daily data publication.

## Safety, receipts, and rollback

- Trigger remains `DATA_READY` on an eligible `TW_MARKET` trading session; weekday wakeup is not the calendar or readiness authority.
- Single-flight/date-scope identity, PostgreSQL advisory locking, receipt idempotency, and failed-closed publication boundaries remain in the deployed implementation.
- Startup after the normal window cannot call the formal updater; it may only record a genuine operational deadline state. No such receipt was manually created, and receipt/history remained empty.
- `FORMAL_DATA_MANUALLY_MUTATED=NO`; `FAKE_LIVE_PUBLICATION_EXECUTED=NO`; no POST_CLOSE, recovery, backfill, correction, replay, clock change, or historical-date test was used.
- Rollback readiness is bounded and known through prior successful exact-SHA Render deployments; no rollback was needed or exercised during this activation.
- No external notification provider was invented. Operator visibility is the durable receipt/event read model plus Render logs; the new trust-failure event is critical/action-required when encountered.

## Evidence and remaining work

Historical safe-hold and runtime screenshots remain local evidence only:

- `C:/Users/acer/.codex/attachments/9c1b0bcf-7a23-4bab-a525-402f8f724157/worker-runtime-readback.jpg`
- `C:/Users/acer/.codex/attachments/9c1b0bcf-7a23-4bab-a525-402f8f724157/worker-safe-hold.jpg`

The only remaining expected observation is the first legitimate unattended Daily run on the next normal eligible trading session plus `DATA_READY`. It must not be manually triggered. If any future provenance or readiness gate fails, the scheduler must fail closed and surface the critical/action-required event.

STOP CONDITION HONOURED: no manual first run, no backfill/recovery/correction/replay, no fake receipt, and no unrelated cleanup.

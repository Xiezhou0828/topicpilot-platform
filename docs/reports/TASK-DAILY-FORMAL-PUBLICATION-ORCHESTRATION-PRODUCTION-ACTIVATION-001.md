# Daily formal publication — Production activation evidence

Verification date: 2026-10-05, Asia/Taipei. Systems of record: canonical Git/GitHub Actions, Render authenticated dashboard and Worker Web Shell, Production HTTP read models, native Sites deployment metadata. Final scheduler state is a deliberate safe hold, not successful activation.

```text
TASK=TASK-DAILY-FORMAL-PUBLICATION-ORCHESTRATION-PRODUCTION-ACTIVATION-001
TASK_STATUS=BLOCKED_POST_DEPLOY_VERIFICATION
TASK_TYPE=release
REQUIRED_TERMINAL_STATE=POST_DEPLOY_VERIFIED
ACHIEVED_TERMINAL_STATE=PRODUCTION_RELEASED_PARTIAL_SCHEDULER_DISABLED
TASK_COMPLETE=NO
OWNER_AUTHORIZATION=GRANTED_FOR_BOUNDED_PRODUCTION_ACTIVATION
FOLLOW_UP_REQUIRED=YES
FOLLOW_UP_REASON=Canonical implementation lacks the required critical/action-required event for runtime provenance trust failure; latest-main CI was cancelled, not passed. Scheduler must remain disabled until these gates are resolved.
WORKTREE_STATUS=WAITING
PRODUCTION_ACTIVATION_VERIFIED=NO
FIRST_LIVE_DAILY_RUN_VERIFIED=NO_NOT_ACTIVATED
DAILY_FORMAL_PUBLICATION_PRODUCTION_ACTIVE=NO
DAILY_DATA_PUBLICATION_SEPARATE_FROM_SOFTWARE_RELEASE=YES
FIRST_LIVE_DAILY_RUN_PENDING_NORMAL_SCHEDULER=NO_ACTIVATION_BLOCKED
```

## Canonical lineage and exact release

- CANONICAL_BASE: `8894138fc930b4512541cacd5214162cd66b4c8f`.
- Original implementation: `9a97feb98ff6405874747030412b93bc5df519e9`; independently inspected candidate: `8ab5560e50340188ae0727389ef0439dd28697fc`.
- Release preparation commits: `749b6de9025bc718b0e0c46c22854896db7d1781`, `b722bd36461444e989b84822d79d025048fcb0f4`, `1e992e3dc26900777cbbc9b654728dfa385ff168`.
- [PR 72](https://github.com/Xiezhou0828/topicpilot-platform/pull/72) preserved lineage with an ordinary merge: `2651068c202a501566ce7feeaff6b3521fe105ad`.
- A subsequent independent Preview merge advanced main to `dd95fd410d59fcf34cd432ba3852dfeb3a07d3cc`. The diff has nine files: Web preview configuration/proxy, preview runner/tests, README/report, root package command. It does not change `services/api`, `render.yaml`, or `.github/workflows/deploy.yml`.
- CURRENT_ORIGIN_MAIN / RELEASE_CANONICAL_SHA / EXPECTED_ACTIVATION_SHA: `dd95fd410d59fcf34cd432ba3852dfeb3a07d3cc` at the final release/readback. API and dormant Worker were updated to this latest canonical commit; newer Preview work was not overwritten.
- ORIGIN_MAIN_AFTER (closure reread): `e47d43d9d5a5b64c86a8b14d6f86c9189016525e`, merge of PR 73. Independent commit inspection shows only the Preview task report changed; no software/configuration changed and no further deployment was performed. Release identity remains `dd95fd4…`.
- No unpushed local code was deployed. Parent legacy checkout and its unrelated dirty files were not modified. NEXT_TASK was not modified.

Release preparation updated the existing protected release workflow to exact migration 0049 and the receipt relation/append-only trigger precondition, made Web packaging opt-in, explicitly documented frozen Worker timing in the blueprint, regenerated the affected API contracts, and corrected one import-order violation. It did not alter business formulas, authority, calendar decisions, readiness, or formal publication data.

## Validation and previous seven failures

The previous implementation report was independently read. Its full-suite count was 1342 passed / 79 skipped / 7 failed. The independent local full suite after release preparation was **1344 passed / 79 skipped / 5 failed**, 482.08 seconds. Total collected count remains 1428; no tests were removed to make the result green.

| Previous failure family | Independent baseline/candidate evidence | Classification and Production significance |
| --- | --- | --- |
| Migration-head freeze assertion | Explicit 0049 head/allowlist assertions rerun in focused + architecture validation, 32 passed | Stale assertion corrected for approved additive migration; not a production functional failure |
| Receipt-table architecture freeze assertion | Explicit approved receipt relation included in architecture checks; same 32-test rerun passed | Stale assertion corrected for approved additive relation; not a production functional failure |
| Cold `live.cli` interpreter import | Baseline boundary run fails this case; final Windows full suite also times out | Environmental cold-subprocess failure, independently observed before implementation; Linux release backend suite passes |
| Cold `provider_preflight` interpreter import | Both isolated baseline and candidate boundary runs time out | Environmental cold-subprocess failure, not introduced by receipt logic; Linux release backend suite passes |
| Post-close dry-run subprocess | Baseline automatic dry-run times out; candidate automatic case also fails, once with Windows exit 3221227274 | Windows subprocess instability; no deterministic receipt/readiness assertion failure demonstrated; Linux release backend suite passes |
| Missing-credentials subprocess | Candidate isolated/final Windows runs can time out; isolated baseline/candidate failure sets vary | Non-deterministic boundary execution; not silently treated as a local pass; equivalent backend code passes authoritative Linux release checks |
| Provider-failure subprocess | Both isolated baseline and candidate boundary runs time out | Environmental subprocess failure; Linux release backend suite passes |

Equivalent isolated boundary runs: baseline `8894138…`: 10 passed / 4 failed, 331.15 seconds; candidate `8ab5560…`: 10 passed / 4 failed, 253.08 seconds. Failure membership varies. The previous report also mentioned an unrelated market-data import timeout; its original full output was not sufficient to recover a unique seven-node-ID inventory. This table therefore identifies independently verified failure cases/categories rather than inventing original node IDs. No local failing run is labelled PASS.

Current independently inspected test identities are `test_worker_import_boundary.py::test_clean_interpreter_first_import` (parameterized modules), `test_worker_startup_dry_run_never_calls_provider_or_database` (auto/post-close), `test_worker_missing_credentials_still_fail_closed`, `test_worker_provider_failure_is_not_reported_as_startup_success`, and `test_v2_architecture_freeze.py::test_v2_metadata_contains_only_implemented_tables`. Original seven-node-ID reconciliation is PARTIAL rather than falsely exhaustive; this is an additional evidence gap to close before activation.

Validation evidence:

- Focused Daily/scheduler/receipt/correction/provenance/API + architecture validation: 32 passed; corrected freeze assertions independently covered.
- Generated client tests: 4/4 passed. Compile checks, YAML parsing, targeted Ruff and diff checks passed. Linux Ruff initially found an additional correction-module import ordering issue; it was fixed in `1e992e3…`, not suppressed.
- [Candidate CI 37315082040](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37315082040), exact `1e992e3…`: backend/migration/OpenAPI, frontend, secret scan, Docker Compose smoke all SUCCESS.
- [Canonical CI 37316267796](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37316267796), exact `2651068…`: all four jobs SUCCESS after the cancelled Docker job was rerun. Backend: 1277 passed / 3 skipped / 148 deselected, 53.42 seconds; CI explicitly deselects research/governance. Disposable PostgreSQL exercises tests otherwise skipped locally; this explains counts without deleting tests.
- Linux migration graph: one head, exactly 0049; actual disposable PostgreSQL upgrade 0048→0049, rollback 0049→0048, upgrade back passed.
- [Latest-main CI 37316725320](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37316725320), exact `dd95fd4…`: CANCELLED, including its rerun. Do not infer success from completed intermediate steps or from the older backend-equivalent release. No gate was weakened.
- Code regression evidence for this task's unchanged backend is positive, but **overall activation contract validation is NOT PASS**: the required runtime-trust failure notification is missing. TASK_SCOPE_REGRESSION_FREE must not substitute for this unmet activation gate.

## Production mutation ledger and runtime proof

| Operation | Exact scope / result |
| --- | --- |
| Protected Production migration | [37316409516](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37316409516), release `2651068…`, migration only; validation and migration jobs SUCCESS |
| Initial API release | [37316745333](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37316745333), exact `2651068…`; protected hook SUCCESS and independent HTTP SHA readback confirmed |
| Worker safe-start configuration | Saved temporary dormant shell command; Auto Deploy remained Off; this save did not itself deploy |
| Initial Worker attempt | [37317027555](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37317027555), exact `2651068…`; hook SUCCESS but Render deployment `dep-db1qc1p42hec73drsfl0` FAILED, exit 127 because command quoting was not interpreted as intended. Old live instance remained; this was never counted as successful runtime deployment |
| Bounded command repair | Saved `sleep infinity`, a dormant command without nested shell quoting; no formal updater invoked |
| Latest-main API + dormant Worker release | [37318063219](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37318063219), exact `dd95fd4…`; validation, API hook and Worker hook SUCCESS, migration/Web jobs skipped. Independently verified both actual runtimes |

PRODUCTION_MIGRATION_BEFORE / LAST_KNOWN_GOOD_MIGRATION_STATE: `0048_task_checkpoint_provider_metric_applicability`.
TARGET_MIGRATION / MIGRATION_AFTER / DB_MIGRATION_HEAD: `0049_task_daily_formal_publication_receipt`.
MIGRATION_PATH_VALID=YES. PRODUCTION_MIGRATION_EXECUTED=YES. Migration is additive receipt architecture with append-only authority, not a formal-data rewrite. Protected migration job checks relation existence and append-only trigger after upgrade.

API_RUNTIME_BEFORE / WORKER_RUNTIME_BEFORE / LAST_KNOWN_GOOD_API / LAST_KNOWN_GOOD_WORKER: `a687c748e1b7d512449b69884626c58ac7d86d12`. Worker pre-release SHA was independently read using supported Render Web Shell, not inferred from API.

Final independent HTTP readback:

```json
{"status":"ok","gitSha":"dd95fd410d59fcf34cd432ba3852dfeb3a07d3cc"}
{"status":"ready","gitSha":"dd95fd410d59fcf34cd432ba3852dfeb3a07d3cc"}
{"alembicRevision":"0049_task_daily_formal_publication_receipt","readOnly":true}
```

Final independent Worker Web Shell (`topicpilot-worker-revision --json`, read-only):

```json
{"readbackStatus":"READY","runtimeGitSha":"dd95fd410d59fcf34cd432ba3852dfeb3a07d3cc","source":"RENDER_GIT_COMMIT_OR_GIT_SHA"}
```

Thus API_RUNTIME_AFTER=WORKER_RUNTIME_AFTER=`dd95fd410d59fcf34cd432ba3852dfeb3a07d3cc`. API health/readiness PASS. This does **not** claim scheduler activation or receipt-level independent API marker configuration.

## Sites / Web provenance

No Web build/publish was needed for the approved backend/Worker activation; no cosmetic Sites deployment was performed. Preview-only mainline tooling does not require changing the existing Production frontend.

- Production URL: https://topicpilot-platform.game0962046460.chatgpt.site
- Project: `appgprj_6a6ce02bd75c81919ab3678ebf013c53`.
- SITES_VERSION / LAST_KNOWN_GOOD_WEB: v73, active.
- Native version source commit: `771afdcfa5342a9ffd9d90b8c2f5ee0e78a132c0`.
- Version ID: `appgprj_6a6ce02bd75c81919ab3678ebf013c53~appgver_55a6eb8f0f488191b33ff722b4e3d906`.
- Archive digest: `sha256:06b59b6820ec4e215ac1ec57d3d91cd634d7f40b7c57abd943d75034247f62ae`; 11,069,440 bytes, 119 files.
- Deployment: `appgdep_6ac2ec2ee1c881919354e712b559227b`, native status succeeded, type publish, environment revision 2; updated `2026-10-05T00:16:36.884149Z`.
- Sites automations: empty. API SHA was not misrepresented as Web SHA. Native Sites commit and artifact digest are verified; an embedded canonical application SHA sidecar was not independently available (`/__release.json` returned Not Found), so that additional mapping remains UNKNOWN.

## Scheduler and safe hold

SCHEDULER_RESOURCE: existing Render Background Worker `topicpilot-live`, `srv-da6okdpsrm7s73aqbnn0`, Starter/Oregon. This is the single selected canonical V2 Worker, not a newly added competing cron. Dashboard showed existing API + Worker; Sites automations were empty. No competing scheduler was created. A comprehensive proof excluding every other external/manual scheduler is not complete and is not claimed.

SCHEDULER_BEFORE: legacy Worker start command `topicpilot-live`, runtime a687; new Daily receipt orchestrator not active.
SCHEDULER_AFTER / SCHEDULER_ENABLED: **NO — dormant latest-main Worker, Docker Command `sleep infinity`, Auto Deploy Off**. The temporary hold must not be forgotten or represented as normal operation. It also pauses the previous Worker's normal live polling. Restore `topicpilot-live` and deploy the exact approved SHA only after the outstanding gates are resolved; saving configuration alone did not restart the service in this observed configuration.

Actual nonsecret `LiveRuntimeConfig.from_environment()` on deployed Worker:

```json
{"timezone":"Asia/Taipei","earliest":"13:45","softTarget":"14:30","hardDeadline":"15:00","pollSeconds":300,"calendar":"TW_MARKET"}
```

PUBLICATION_TRIGGER=DATA_READY (deployed code, not currently executing).
TRADING_CALENDAR_AUTHORITY=G2_REFERENCE_CALENDAR / TW_MARKET. Weekday wakeup is not the trading-day or readiness authority. MARKET_CLOSED remains successful no-op, publicationAttempted false, not an error, no normal alert; code/test evidence only, no manual closed-market receipt created.

SINGLE_FLIGHT: deterministic date/scope identity, PostgreSQL advisory lock and already-complete/receipt idempotency preserved in deployed implementation. Not demonstrated by a fabricated concurrent Production writer test.
STARTUP_BACKFILL_SAFETY: current hold executes no scheduler/updater at all. Inspected normal runner checks terminal authority and hard deadline before updater execution. After 15:00 it can append a genuine operational DEADLINE_EXCEEDED receipt but cannot call the normal formal updater. Activation was after the normal window; **normal scheduler startup was not invoked**, and no deadline receipt was manually created. No historical/current-date POST_CLOSE, recovery, replay, synthetic readiness/calendar, or clock changes were executed.

## Read-only receipt and legacy surfaces

- `GET /api/v1/operations/live/publication-receipt`: HTTP response `{"status":"NOT_FOUND","tradingDate":"2026-10-05","receipt":null}`. DAILY_RECEIPT_API_AVAILABLE=YES; LATEST_RECEIPT_STATE=NOT_FOUND, truthfully no new Daily receipt.
- `GET /api/v1/operations/live/publication-receipts`: `{"tradingDate":"2026-10-05","items":[],"total":0,"limit":50}`. RECEIPT_HISTORY_READABLE=YES, empty.
- `GET /api/v1/meta/data-status`: existing problem-details 404, `No completed bundle has been imported`. It is the legacy imported-bundle surface, not the new formal Daily receipt. LEGACY_DATA_STATUS_UNCHANGED=YES by unchanged code/contract; its current 404 is recorded, not relabelled as a new Daily publication failure or a successful legacy bundle.
- Readbacks were GET-only. FORMAL_DATA_MANUALLY_MUTATED=NO; FAKE_LIVE_PUBLICATION_EXECUTED=NO. Additive schema migration is explicitly distinguished from formal-data publication.

## Blocking notification finding

NOTIFICATION_EVENT_CONTRACT_ACTIVE=PARTIAL_NOT_ACTIVATION_READY.
EXTERNAL_NOTIFICATION_PROVIDER=NONE_VERIFIED. OPERATOR_VISIBILITY=durable receipt/event read models plus Render logs; no invented email/chat provider.

`services/api/src/topicpilot_api/live/receipt.py` constructs WARNING `SOFT_TARGET_NOT_READY`, CRITICAL `HARD_DEADLINE_EXCEEDED`, and CRITICAL `FORMAL_INTEGRITY_FAILURE` for failed-closed/correction-failed receipt status. Normal complete/market-closed is quiet. However `runtime_provenance()` returns READY based only on Worker + migration, explicitly `blocking=false`, and records independent API/Web markers as UNKNOWN/UNVERIFIED when absent. Receipt construction calls it **after** building its events and does not emit a CRITICAL/action-required runtime-trust failure event. The unit test only asserts UNKNOWN is never verified; it does not establish the missing event behavior.

This is a contract omission in the inherited implementation, not a newly introduced release-preparation regression. Independent HTTP/API/Worker readback proves today's exact deployed SHA but does not prove the required future trust-failure alert semantics. Section 16's explicit requirement is therefore not met. An external notification provider is optional under the task contract; the missing machine-readable critical trust-failure event is not excused by that allowance.

The omission was discovered during post-deploy operational verification, after the additive migration and runtime deployments. It should have been caught earlier; passing structural/CI checks were insufficient to prove every activation contract requirement. No successful-activation flag is asserted. No new trust/blocking semantics were improvised beyond the authorization for deploying the already-approved architecture. Required next authority: Owner decision on a bounded implementation correction for this gap, followed by exact-SHA validation/release and normal activation verification. Latest-main required CI must also be resolved without suppressing checks. Comprehensive competing-scheduler verification remains before activation.

## Separation and rollback

SOFTWARE_RELEASE_SEPARATION=YES. Normal Daily code does not invoke GitHub release, API/Worker deploy, Web build or Sites publish. Protected software workflow remains manual; one-time migration/release is not a daily data publication path.

ROLLBACK_READINESS=KNOWN_BOUNDED_PATH, NOT_EXERCISED. Last-known-good API/Worker a687, Sites v73 unchanged. Existing protected exact-SHA hooks/Render previous successful deployments provide software rollback. Additive Production migration 0049 is retained; no Production downgrade/destructive SQL was executed or proposed as a way to undo formal data. Formal data would require separately authorized supersession/correction/replay. Failed first Worker rollout left its prior live instance intact; successful dormant latest-main rollout then replaced it. Current safest state is the deliberate disabled scheduler, not restoration of an unverified writer.

## Evidence and remaining work

Browser verification used the supported in-app Render interface to independently read actual Worker runtime and settings; it exposed the difference between hook success and failed runtime startup. Local screenshots (not canonical Git artifacts):

- `C:/Users/acer/.codex/attachments/9c1b0bcf-7a23-4bab-a525-402f8f724157/worker-runtime-readback.jpg`
- `C:/Users/acer/.codex/attachments/9c1b0bcf-7a23-4bab-a525-402f8f724157/worker-safe-hold.jpg`

REMAINING_OPERATIONAL_GAPS: critical runtime-trust event behavior, uncancelled required latest-main CI, complete external competing-scheduler audit, receipt-level independent provenance marker provisioning as required by the corrected contract, actual scheduler enablement/post-activation readback, and only then a legitimate future unattended Daily run. Embedded Web canonical-source mapping remains UNKNOWN; native Sites version/digest are verified. External notification delivery is a bounded optional operational follow-up, not invented.

STOP: no manual first run, no backfill/recovery/correction/replay, no fake receipt, no unrelated cleanup. This task remains incomplete at its named activation gate.

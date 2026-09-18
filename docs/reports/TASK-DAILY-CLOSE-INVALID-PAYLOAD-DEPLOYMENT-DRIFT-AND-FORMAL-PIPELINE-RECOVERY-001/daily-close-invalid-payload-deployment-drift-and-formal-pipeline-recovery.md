# Daily Close invalid-payload deployment drift and formal pipeline recovery

Updated: 2026-09-18 (Asia/Taipei)

Responsibility: governed Daily Close / POST_CLOSE recovery evidence

Task: `TASK-DAILY-CLOSE-INVALID-PAYLOAD-DEPLOYMENT-DRIFT-AND-FORMAL-PIPELINE-RECOVERY-001`

# Executive Finding

Development already contains the bounded remediation, so no duplicate program change is justified. The remediation entered the governed lineage at `4cba30bed48ea667f975950126f4c8fa7b128f18` and is contained by the current governed SHA `a41bbe408529708a1157b51374c86ee10419257f` (code head `c7025182349f93869eead2017d395b847744c9c9`). It changes the formal path from per-symbol, collapsed errors to market-day fetches with first-failing-layer classifications, market response coverage metadata, checkpoint-safe failure persistence, and fail-closed downstream gating.

Production API is proven stale at `bf68cc8bf0a4432d7623db43f42e9219c94d7b6b`; its checked-in code lacks the remediation and the live response lacks current configuration fields. The exact Worker SHA remains unavailable, so Worker drift is not asserted as proven. The observed 2026-09-17 failure is consistent with the old code path, but that is inference, not Worker provenance.

The historical `INVALID_PAYLOAD` subtype is unprovable because the failing runtime retained only a deduplicated code list, not the raw response or safe response metadata. A read-only fetch on 2026-09-18 proved that the current canonical adapters can retrieve and parse all six date/market controls, including 2026-09-17 TPE (1,377 rows) and TWO (11,479 rows). This does not prove what the provider returned at the 2026-09-17 runtime.

The furthest safe state is `DEVELOPMENT_READY / RELEASE_COMPOSITION_READY / BLOCKED_OPERATOR_RELEASE_AUTHORITY`. Production is not ready until the exact API and Worker SHA are deployed, DB migration `0042_task_fund_b_stock_institutional_flow_forward` is applied, exact Worker provenance is read back, canaries pass, and the Owner authorizes sequential historical replay.

## Starting Evidence

- Accepted symptom: Today Market stayed at 2026-09-09 because no newer formal publication existed.
- Accepted 2026-09-17 POST_CLOSE result: requested 553, success 0, failed 347, skipped 206; `EXCHANGE_NO_DATA;INVALID_PAYLOAD`.
- Accepted downstream effect: no provable 2026-09-17 A9 formal Topic snapshot, Daily Strength, Score, Grade, or Lifecycle publication.
- Protected parallel reports were read only; their worktrees and branches were not modified.

## Governed Canonical Baseline

| Field | Recovered value |
|---|---|
| Governed base before FUND-C | `b3094cec79c34052131e3bcfe0e8db1a895788a9` |
| Current code head | `c7025182349f93869eead2017d395b847744c9c9` |
| Governance closeout / task base | `a41bbe408529708a1157b51374c86ee10419257f` |
| Daily Close remediation commit | `4cba30bed48ea667f975950126f4c8fa7b128f18` |
| Alembic heads | one: `0042_task_fund_b_stock_institutional_flow_forward` |

`3c212295cbb9f2aae74d2c69753aadfa996dec68` is a later protected Topic/Lifecycle diagnostic descendant, not a newer canonical implementation baseline.

## Production Provenance

| Item | Evidence-backed value |
|---|---|
| API SHA | `bf68cc8bf0a4432d7623db43f42e9219c94d7b6b` from fresh `/healthz` and `/readyz` |
| Worker SHA | `UNKNOWN_EXACT_SHA`; no public Worker revision endpoint or deployment manifest readback |
| Web SHA | `UNKNOWN_EXACT_SHA`; deployed bundle identity is not an exact source SHA |
| DB revision | latest prior evidence `0040_task_a10_recovery_checkpoint_observability`; current `/api/v1/admin/migration` returns 404, so current DB reread is unavailable |
| Provider mode | live configuration exposes official provider runtime fields, but exact Worker environment/provider mode is `UNPROVABLE` |
| Config version | no versioned deployment identifier; live values show poll 300 seconds, session close 13:30, but omit canonical `postCloseStart` |

Fresh read-only runtime checks on 2026-09-18 returned API ready, the same failed run `d7d9017d-4641-4f2c-a557-20e536f065e4`, and Home date 2026-09-09.

## Development Provenance

Current canonical has:

- precise HTTP/auth/rate-limit/transport/empty/JSON/schema/date/no-data classification;
- one market-day request cached and indexed by symbol for TPE and TWO;
- safe market coverage diagnostics (`requestedCount`, `providerRowCount`, `matchedCount`, `missingCount`, request count, provider, adapter version, target date);
- systemic market failures recorded consistently without interpreting invalid payloads as quotes;
- Worker session recovery and retry containment;
- 13:35 Asia/Taipei POST_CLOSE boundary and 300-second poll;
- checkpoint and forward automation gating that block A9/Home publication unless reconciliation is downstream-ready.

## Deployment Drift Matrix

| Component | Production | Development | Drift? |
|---|---|---|---|
| API | `bf68cc8...` | `a41bbe4...` | YES, exact code/content drift |
| Worker | exact SHA unknown | `a41bbe4...` target | UNPROVABLE |
| Web | exact SHA unknown; correct Home renderer | `a41bbe4...` source | UNPROVABLE; no Web defect |
| DB revision | last proven `0040...` | `0042...` | PARTIAL/likely; current DB reread unavailable |
| Daily Close | old per-symbol collapsed path is present at API SHA | market-day classified path | YES for API code; Worker unknown |
| Provider parser | broad `PROVIDER_REQUEST_FAILED` / `INVALID_PAYLOAD` | typed first-failure classification | YES for API code |
| Error taxonomy | deduplicated raw error codes | classified, structured diagnostics | YES for API code |
| POST_CLOSE | no canonical `postCloseStart` field at API response | explicit 13:35 and contained retry | YES for API code |

Code drift is proven. Config drift is partial (observable schema/value difference; exact Worker config unknown). DB/migration drift is partial because only the older revision has prior evidence. Worker drift remains unprovable.

## 2026-09-17 POST_CLOSE Reconstruction

Current flow is `LiveScheduler.run_loop` -> `LiveScheduler.mode_for_now` -> `run_once("POST_CLOSE")` -> `PostCloseUpdater.run_once` -> date-effective universe -> market-day official provider -> normalization/ingestion -> attempt persistence -> daily-market reconciliation -> checkpoint -> `_run_snapshot` -> formal Topic/Home handoff.

The deployed API SHA's historical implementation instead iterated symbols through `ingest_historical`; exceptions incremented `failure_count`, while a successfully returned result without a priced bar or lifecycle-authorized no-trade evidence incremented `skipped_count` as `MISSING_MARKET_DATA`. `_finish` sorted and deduplicated `failure_codes`, used the first as `failure_code`, and joined all with semicolons as `failure_message`.

## 553 Requested / 347 Failed / 206 Skipped

- `failed=347`: 347 per-instrument attempts raised exceptions in the old path. The run-level record does not preserve which code applied to each instrument.
- `skipped=206`: 206 provider calls returned no priced bar and lacked lifecycle-authorized no-trade evidence, so the old path marked them `SKIPPED/MISSING_MARKET_DATA`; these are not proven reference exclusions.
- `success=0`: no attempt produced a persisted accepted priced bar.
- Market split: unavailable. Counts numerically resembling a market split are not sufficient evidence; no instrument-level attempt readback or raw trace was preserved.

## INVALID_PAYLOAD Origin

At deployed SHA `bf68cc8...`, official adapters emit `INVALID_PAYLOAD` for non-object JSON envelopes and malformed/missing arrays/tables/rows. `_json` catches every transport/decode error as `PROVIDER_REQUEST_FAILED`, so the exact observed subtype cannot be recovered from the run summary. Current canonical maps invalid UTF-8/JSON, missing `stat`, non-object envelopes, missing tables, and incomplete rows to schema-aware errors, with `INVALID_PAYLOAD` normalized operationally to `SCHEMA_MISMATCH`.

## EXCHANGE_NO_DATA Origin

At the old official adapters, a provider business response whose `stat` is not OK emitted `EXCHANGE_NO_DATA`. The combined string is not `PRIMARY_ERROR + SUBCAUSE`; it is the sorted, deduplicated set of exception codes observed across failed attempts. `failure_code` is simply the first sorted item. Therefore `EXCHANGE_NO_DATA;INVALID_PAYLOAD` proves at least two recorded failure codes, not their causal relationship.

## Raw Provider Evidence

Historical raw body, status, content type, body length, provider code/message, response hash, schema keys, market-specific attempt mapping, and retry-state detail are unavailable. The old run preserves date, run counts, failure-code set, status/freshness, and timestamps.

`INVALID_PAYLOAD_OBSERVABILITY=PARTIAL` for current canonical: classification, market, target date, adapter/provider, row/match/missing counts and request counts are safely retained; full HTTP status/content type/body length are not carried by the bytes-only transport. No new change was made because the current failing condition was not reproduced and the existing bounded remediation already materially closes the proven collapse without logging sensitive payloads.

## Provider Reproduction

Fetch date: 2026-09-18. All calls were read-only and used explicit value dates.

| Value date | Market | Transport | Parse | Rows | Classification |
|---|---|---:|---:|---:|---|
| 2026-09-15 | TPE | SUCCESS | SUCCESS | 1,379 | SUCCESS |
| 2026-09-15 | TWO | SUCCESS | SUCCESS | 11,358 | SUCCESS |
| 2026-09-16 | TPE | SUCCESS | SUCCESS | 1,379 | SUCCESS |
| 2026-09-16 | TWO | SUCCESS | SUCCESS | 11,415 | SUCCESS |
| 2026-09-17 | TPE | SUCCESS | SUCCESS | 1,377 | SUCCESS |
| 2026-09-17 | TWO | SUCCESS | SUCCESS | 11,479 | SUCCESS |

This proves current historical retrievability and parser compatibility only. `KNOWN_AT_RUNTIME` for 2026-09-17 remains unknown.

## Date / Market / Schema Analysis

Current canonical constructs TWSE dates as `YYYYMMDD`, TPEx dates as `YYYY/MM/DD`, validates returned `YYYYMMDD`, and uses explicit `date` values plus Asia/Taipei scheduler/session semantics. Both market mappings parsed 9/15–9/17 successfully. No current date, mapping, parser, schema, auth, rate-limit, maintenance, or true-no-data defect was reproduced. Their historical 9/17 applicability remains unprovable.

## Error Taxonomy

Current canonical separates `AUTH_FAILED`, `RATE_LIMITED`, `PROVIDER_TIMEOUT`, `PROVIDER_UNAVAILABLE`, `HTTP_ERROR`, `EMPTY_RESPONSE`, `SCHEMA_MISMATCH`, `TRADING_DATE_MISMATCH`, `EXCHANGE_NO_DATA`, `SYMBOL_MAPPING_FAILED`, and `NORMALIZATION_FAILED`. The old deployment collapses several of these boundaries. Failures stay failures and never become market data.

## Worker Session Safety

`LiveScheduler` contains each job failure, rolls back/recover-checks the SQLAlchemy session, schedules a retry, and refuses to continue when the session cannot be proven usable. Focused live/runtime/session tests passed.

## Daily Close Completeness Contract

The expected denominator is the date-effective eligible publication universe. Every member must have an accepted priced observation or explicit lifecycle-authorized no-trade state. Unexplained missing data, systemic provider failures, schema errors, or partial reconciliation make `downstream_ready=false`; a partial run cannot claim a complete checkpoint or publish stale rows as fresh.

## Persistence / Idempotency

Attempts and checkpoints are run/date/scope aware; recovery requires an explicit run date and terminal replay authorization, uses checkpoint identity, and resumes/reconciles bounded work. The code supports idempotent governed replay semantics, but Production idempotency for these missing dates remains `PARTIAL` until an authorized canary/replay readback verifies duplicates and stale-row behavior.

## POST_CLOSE Checkpoint

Development checkpoint behavior is READY by focused tests: partial results remain partial and forward automation is blocked. Production 9/17 checkpoint is NOT_READY for downstream publication because Daily Close failed.

## Today Market Handoff

`/api/v2/home` correctly selects the latest formal published date and returned 2026-09-09. It and the Web date renderer are not defective. A fixed 17:00 job is neither present nor required.

## A9 Topic Snapshot Handoff

A9 requires successful Daily Close reconciliation/checkpoint. No formal A9 snapshot exists publicly for 2026-09-10 through 2026-09-17. A9 9/17 was not ready.

## Root Cause Classification

`PRIMARY_FAILURE_CLASS=MULTIPLE`: API deployment drift is proven; exact Worker/runtime provenance and the historical provider payload subtype are unprovable. The earliest proven broken boundary for 9/17 is the Worker-side official-provider/Daily Close attempt boundary. The first missing formal date is 2026-09-10, whose exact attempt boundary is unknown.

## Implementation Decision

`CODE_CHANGE_REQUIRED=NO`. Current canonical did not reproduce the fault, already contains the generic classification/market-day remediation, and a speculative second parser or observability framework would duplicate governed work without historical payload evidence.

## Implementation Changes

No program, policy, config, schema, migration, Lifecycle, Opportunity, MLCC, FUND-C, PRE_CLOSE, or frontend code changed. Only this evidence report pair was added.

## Validation

| Suite | Result |
|---|---|
| Provider focused | PASS; included in 96 focused tests plus 6 live read-only controls |
| Daily Close focused | PASS; 96 focused aggregate |
| POST_CLOSE focused | PASS; 96 focused aggregate |
| A10/checkpoint | PASS; partial checkpoint remains blocked |
| A9 handoff | PASS; fail-closed handoff tests |
| Worker/session | PASS; focused safety/runtime tests |
| Home API | PASS; tests plus live HTTP 200 / 2026-09-09 truthful readback |
| Today Market | PASS; Web suite 165/165; prior focused diagnostic 14/14 |
| Backend full | BASELINE WITH KNOWN FAILURES: 775 passed, 59 skipped, 9 Lifecycle shadow failures |
| OpenAPI | PASS through Web generated-contract tests; no API schema change |
| API client drift | PASS through generated query/runtime authority tests; no generated files changed |
| Web | PASS: 165 passed, 0 failed, 0 skipped |
| Build | PASS, reproducible `npm ci` then vinext build |
| Ruff | PASS on affected Daily Close/provider files |
| Compile | PASS, API source compileall |
| Alembic | PASS, one head `0042_task_fund_b_stock_institutional_flow_forward` |

The 9 full-suite failures are pre-existing, out-of-scope Lifecycle contract drift on an unchanged baseline (one stage-sequence contract and eight engine tests). PostgreSQL-required tests account for 59 skips because no test database was authorized/configured. Two preliminary command failures were environmental invocation errors (one nonexistent test path; one missing `PYTHONPATH`) and were corrected before the 96-test pass. Task-caused failures: 0.

`npm ci` reported 15 dependency audit findings (2 moderate, 12 high, 1 critical). No automatic dependency mutation was authorized; this is an out-of-scope security/dependency candidate requiring separate governance.

## Development Reconciliation

The task started from the exact governed closeout `a41bbe4...` in a clean isolated E: worktree. With no program correction required, reconciliation consists of a local documentation/evidence commit on that lineage. Owner checkout, parallel worktrees, and `NEXT_TASK` remain untouched.

## Development Readiness

`DEVELOPMENT_READY=YES` for the Daily Close remediation and release/canary composition. This does not override the registered Lifecycle baseline failures or establish Production readiness.

## Production Release Composition

Deploy API and Worker from the same exact governed SHA `a41bbe408529708a1157b51374c86ee10419257f`; verify each independently. Apply migrations through `0042_task_fund_b_stock_institutional_flow_forward` before enabling the target runtime. Web behavior needs no repair; for a coordinated full-stack rebuild the target source SHA is also `a41bbe4...`, otherwise retain the current Web and prove its exact source SHA separately.

## Migration Requirement

YES. Last proven Production revision is `0040...`; target is `0042...`. Operator must freshly read the Production revision before migration and apply only the governed forward chain. This task did not execute any migration.

## Canary Plan

1. Deploy exact API SHA and exact Worker SHA `a41bbe4...`; read `/healthz`, `/readyz`, Worker revision, configuration including `postCloseStart=13:35`, and DB `0042...`.
2. Run read-only provider canary for one known TPE and one TWO symbol/date, then one market-day fetch per market; verify response date, schema, row counts, and sanitized diagnostics.
3. Run a bounded non-Production or explicitly authorized Production Daily Close canary; verify attempts, market-level request count, zero false freshness, checkpoint, reconciliation, and session usability.
4. Do not proceed to replay unless all gates pass and exact provenance is retained.

## Replay / Historical Recovery Plan

| Date | Daily Close | Today snapshot | A9 snapshot | Recovery needed |
|---|---|---|---|---|
| 2026-09-09 | last formally published boundary | PUBLISHED | published/formal boundary exists | NO |
| 2026-09-10 | UNKNOWN | absent | absent | YES; earliest missing |
| 2026-09-11 | UNKNOWN | absent | absent | YES |
| 2026-09-14 | UNKNOWN | absent | absent | YES |
| 2026-09-15 | FAILED/PARTIAL, 0/347/206 | absent | absent | YES |
| 2026-09-16 | UNKNOWN | absent | absent | YES |
| 2026-09-17 | FAILED, 0/347/206 | absent | absent | YES |

After canary and explicit replay authority, recover 9/10, 9/11, 9/14, 9/15, 9/16, 9/17 sequentially. For each date verify Daily Close persistence, completeness/checkpoint, Today publication, A9 snapshot, then Lifecycle state before advancing. Sequential recovery is required because Lifecycle state depends on prior trading-day state. The first downstream readback is the Daily Close attempt/reconciliation/checkpoint, followed by `/api/v2/home` and A9 formal snapshot readback.

## Remaining External Gates

- exact Worker and Web provenance;
- current Production DB revision readback and authorized migration;
- exact-SHA API/Worker deployment;
- Production provider and Daily Close canary;
- date-bound sequential replay authority;
- persisted Today/A9/Lifecycle readback;
- separate dependency-vulnerability triage.

## Required Final Answers

1. `INVALID_PAYLOAD` came from the deployed official exchange adapter/parser layer.
2. It covered non-object envelopes and malformed/missing tables/arrays/rows; the exact historical subtype is unprovable.
3. `EXCHANGE_NO_DATA` came from the old official exchange adapter when provider `stat` was non-OK.
4. The combined string is a sorted unique set of run failure codes, not a proven cause/subcause chain.
5. No, the 9/17 subtype cannot be proven.
6. The 9/17 Worker cannot be proven to have run current canonical code.
7. Worker SHA: `UNKNOWN_EXACT_SHA`.
8. API SHA: `bf68cc8bf0a4432d7623db43f42e9219c94d7b6b`.
9. Remediation SHA: `4cba30bed48ea667f975950126f4c8fa7b128f18`; current governed target `a41bbe4...` contains it.
10. Deployment drift: YES, at least API/code.
11. Worker drift: UNPROVABLE.
12. Current canonical does not reproduce the failure in six provider controls.
13. Yes, it currently returns valid historical 9/17 data for both markets.
14. No, that does not prove contemporaneous 9/17 success.
15–23. Authentication, authorization, rate limit, maintenance, schema drift, parser drift, date mismatch, market mapping, and true no-data are all historically UNPROVABLE; none reproduced currently.
24. All causes in 15–23 remain historically unprovable.
25. 347 old per-symbol attempts raised exceptions; per-instrument subtype mapping was not retained.
26. 206 returned no priced bar and no lifecycle-authorized no-trade evidence; they are not proven exclusions.
27. No attempt produced an accepted persisted priced bar.
28. Whether TPE and TWO failed identically is unprovable.
29. Every date-effective member needs accepted price data or explicit authorized no-trade evidence; otherwise downstream readiness is false.
30. Yes, current canonical remains fail-closed.
31. No, malformed data cannot be published as fresh Daily Close.
32. Replay idempotency is implemented but Production proof is partial pending authorized readback.
33. Yes, A9 requires Daily Close/checkpoint completion.
34. No, A9 9/17 was not ready.
35. Today Market stayed on 9/9 because no newer formal Home publication existed.
36. No, `/api/v2/home` is not defective.
37. No, Web date rendering is not defective.
38. No fixed 17:00 job is required.
39. No, the >=13:35 boundary was not changed.
40. No Lifecycle code change is needed in this task.
41. No Opportunity code change is needed.
42. No MLCC correction is needed.
43. No current-canonical defect was proven.
44. No program code was changed.
45. N/A.
46. Existing canonical already fixes classification, market-day fetch, checkpoint, and session safety; duplication would be speculative.
47. 96 focused passes, six live provider controls, 775 backend passes, 165 Web passes/build, Ruff, compileall, and one Alembic head prove the Development state, subject to registered baseline failures/skips.
48. Task-caused failures: 0.
49. Current Alembic head: `0042_task_fund_b_stock_institutional_flow_forward`.
50. Yes, it is a single head.
51. Exact API/Worker SHA `a41bbe4...`, DB through `0042...`, independently verified provenance; Web may be retained or rebuilt from the same SHA.
52. Yes, based on last proven Production `0040...`; fresh readback is required.
53. First canary: exact-provenance readback, then read-only one-date TPE/TWO market-day provider canary.
54. Recovery candidates: 2026-09-10, 09-11, 09-14, 09-15, 09-16, 09-17.
55. Yes, Topic/Lifecycle recovery must be sequential.
56. Earliest missing formal daily date: 2026-09-10.
57. First readback: Daily Close attempts/reconciliation/checkpoint for the replayed date.
58. Release, migration, canary, replay, and Production readback authority remain.
59. Furthest state: Development and release composition ready; blocked before Production mutation.
60. Next action: operator-authorized exact-SHA API/Worker release plus migration/readback and TPE/TWO canary; only then sequential replay.

## Next Governed Action

`BLOCKED_OPERATOR_RELEASE_AUTHORITY`: deploy and prove API and Worker `a41bbe408529708a1157b51374c86ee10419257f`, migrate/read back `0042_task_fund_b_stock_institutional_flow_forward`, execute the bounded provider/Daily Close canary, then request explicit authority for sequential 2026-09-10 through 2026-09-17 recovery.

```text
TASK:
  TASK-DAILY-CLOSE-INVALID-PAYLOAD-DEPLOYMENT-DRIFT-AND-FORMAL-PIPELINE-RECOVERY-001
RESULT:
  COMPLETE_WITH_LIMITATIONS
FURTHEST_SAFE_GOVERNED_STATE:
  DEVELOPMENT_READY_RELEASE_COMPOSITION_READY_BLOCKED_OPERATOR_RELEASE_AUTHORITY
CURRENT_GOVERNED_BASE:
  a41bbe408529708a1157b51374c86ee10419257f
CURRENT_CODE_HEAD:
  c7025182349f93869eead2017d395b847744c9c9
CURRENT_ALEMBIC_HEAD:
  0042_task_fund_b_stock_institutional_flow_forward
ALEMBIC_SINGLE_HEAD:
  YES
DEPLOYED_API_SHA:
  bf68cc8bf0a4432d7623db43f42e9219c94d7b6b
DEPLOYED_WORKER_SHA:
  UNKNOWN_EXACT_SHA
DEPLOYED_WEB_SHA:
  UNKNOWN_EXACT_SHA
PRODUCTION_DB_REVISION:
  0040_task_a10_recovery_checkpoint_observability_LAST_PROVEN_CURRENT_UNPROVABLE
DEPLOYMENT_DRIFT:
  PARTIAL
API_DEPLOYMENT_DRIFT:
  YES
WORKER_DEPLOYMENT_DRIFT:
  UNPROVABLE
DAILY_CLOSE_REMEDIATION_IN_CANONICAL:
  YES
DAILY_CLOSE_REMEDIATION_IN_PRODUCTION:
  UNPROVABLE
POST_CLOSE_2026_09_17_REQUESTED:
  553
POST_CLOSE_2026_09_17_SUCCESS:
  0
POST_CLOSE_2026_09_17_FAILED:
  347
POST_CLOSE_2026_09_17_SKIPPED:
  206
OBSERVED_ERROR:
  EXCHANGE_NO_DATA;INVALID_PAYLOAD
INVALID_PAYLOAD_ORIGIN:
  OFFICIAL_EXCHANGE_ADAPTER_PARSER
INVALID_PAYLOAD_EXACT_SUBTYPE:
  UNPROVABLE
INVALID_PAYLOAD_OBSERVABILITY:
  PARTIAL
EXCHANGE_NO_DATA_ORIGIN:
  DEPLOYED_OFFICIAL_EXCHANGE_NON_OK_STAT
COMBINED_ERROR_SEMANTICS:
  SORTED_DEDUPLICATED_RUN_FAILURE_CODE_SET
HISTORICAL_2026_09_17_SUBTYPE:
  UNPROVABLE
PROVIDER_HISTORICAL_2026_09_17_FETCH:
  SUCCESS
CONTEMPORANEOUS_2026_09_17_PROVIDER_SUCCESS:
  NOT_PROVEN
REQUEST_DATE_DEFECT:
  UNPROVABLE
MARKET_MAPPING_DEFECT:
  UNPROVABLE
PARSER_DEFECT:
  UNPROVABLE
PROVIDER_SCHEMA_DRIFT:
  UNPROVABLE
AUTH_FAILURE:
  UNPROVABLE
RATE_LIMIT:
  UNPROVABLE
TRUE_NO_DATA:
  UNPROVABLE
PRIMARY_FAILURE_CLASS:
  MULTIPLE
EARLIEST_BROKEN_BOUNDARY:
  2026-09-17_WORKER_OFFICIAL_PROVIDER_DAILY_CLOSE_ATTEMPT
CODE_CHANGE_REQUIRED:
  NO
IMPLEMENTATION_COMMIT:
  NONE_CURRENT_CANONICAL_ALREADY_REMEDIATED_AT_4cba30bed48ea667f975950126f4c8fa7b128f18
GOVERNANCE_CLOSEOUT_COMMIT:
  4d683b097a8dda77a9f18eef9adcf31f49820e4c
OBSERVABILITY_CHANGED:
  NO
FAIL_CLOSED_PRESERVED:
  YES
STALE_DATA_CAN_BE_PUBLISHED_AS_FRESH:
  NO
DAILY_CLOSE_COMPLETENESS_CONTRACT:
  ALL_DATE_EFFECTIVE_MEMBERS_ACCEPTED_PRICE_OR_AUTHORIZED_NO_TRADE_ELSE_DOWNSTREAM_NOT_READY
DAILY_CLOSE_REPLAY_IDEMPOTENT:
  PARTIAL
POST_CLOSE_CHECKPOINT:
  READY
A9_REQUIRES_DAILY_CLOSE_COMPLETE:
  YES
A9_2026_09_17_READY:
  NO
TODAY_MARKET_WEB_DEFECT:
  NO
HOME_API_DEFECT:
  NO
FIXED_17_00_JOB_EXISTS:
  NO
POST_CLOSE_POLL_INTERVAL_SECONDS:
  300
POST_CLOSE_BOUNDARY:
  >=13:35_ASIA_TAIPEI
POST_CLOSE_BOUNDARY_CHANGED:
  NO
LIFECYCLE_CODE_CHANGED:
  NO
OPPORTUNITY_CODE_CHANGED:
  NO
MLCC_CHANGED:
  NO
FUND_C_CHANGED:
  NO
PRE_CLOSE_IMPLEMENTED:
  NO
FOCUSED_TESTS:
  96_PASS
BACKEND_FULL_TESTS:
  775_PASS_9_REGISTERED_LIFECYCLE_FAILURES_59_ENVIRONMENT_SKIPS
WEB_TESTS:
  165_PASS
OPENAPI:
  PASS_NO_SCHEMA_CHANGE
API_CLIENT_DRIFT:
  PASS_NO_DRIFT
RUFF:
  PASS
COMPILE:
  PASS
TASK_CAUSED_FAILURES:
  0
REGISTERED_BASELINE_FAILURES:
  9_LIFECYCLE_SHADOW_CONTRACT_FAILURES
ENVIRONMENT_FAILURES:
  59_POSTGRES_SKIPS_PLUS_2_CORRECTED_INVOCATION_ERRORS
UNKNOWN_FAILURES:
  0
DEVELOPMENT_READY:
  YES
RELEASE_COMPOSITION_READY:
  YES
TARGET_API_SHA:
  a41bbe408529708a1157b51374c86ee10419257f
TARGET_WORKER_SHA:
  a41bbe408529708a1157b51374c86ee10419257f
TARGET_WEB_SHA:
  a41bbe408529708a1157b51374c86ee10419257f_IF_REBUILT_OTHERWISE_PROVE_RETAINED_SHA
MIGRATION_REQUIRED:
  YES
REQUIRED_PRODUCTION_DB_REVISION:
  0042_task_fund_b_stock_institutional_flow_forward
CANARY_READY:
  YES
REPLAY_PLAN_READY:
  YES
EARLIEST_RECOVERY_DATE:
  2026-09-10
RECOVERY_DATES:
  [2026-09-10,2026-09-11,2026-09-14,2026-09-15,2026-09-16,2026-09-17]
SEQUENTIAL_TOPIC_RECOVERY_REQUIRED:
  YES
PRODUCTION_READY:
  NO
BLOCKING_EXTERNAL_GATE:
  OPERATOR_RELEASE_MIGRATION_CANARY_AND_REPLAY_AUTHORITY
PROGRAM_CODE_CHANGED:
  NO
POLICY_CHANGED:
  NO
AUTHORITY_CHANGED:
  NO
TOPIC_MEMBERSHIP_CHANGED:
  NO
CONFIG_CHANGED:
  NO
MIGRATION_CREATED:
  NO
MIGRATION_EXECUTED:
  NO
PRODUCTION_MUTATION:
  NONE
DEPLOYMENT:
  NONE
REPLAY:
  NONE
PUSH:
  NO
C_DRIVE:
  UNTOUCHED
OWNER_DECISION_REQUIRED:
  YES
NEXT_GOVERNED_ACTION:
  EXACT_SHA_API_WORKER_RELEASE_DB_0042_READBACK_TPE_TWO_CANARY_THEN_AUTHORIZED_SEQUENTIAL_REPLAY
```

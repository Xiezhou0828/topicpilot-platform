# TASK-INT-FUND-A-MARKET-FLOW-CANONICAL-RECONCILIATION-001

## 1. Closeout decision

FUND-A is canonically integrated into the governed development series in the isolated integration worktree. The source implementation is preserved from its exact verified provenance, its parent matches the current governed development base, the shared API/OpenAPI/generated-client/Today Market surfaces are reconciled, and the development-series closeout is complete.

The production boundary remains `NOT_RELEASED`. No production database was contacted, no migration was executed, no scheduler or runtime operation was changed, and no push or deployment was performed. PostgreSQL round-trip validation remains an external release/operations gate because no `TEST_DATABASE_URL` or `DATABASE_URL` was available in the validation environment.

Canonical integration worktree:

`E:\topicpilot-worktrees\int-fund-a-market-flow-canonical-reconciliation-20260917`

Canonical integration branch:

`codex/task-int-fund-a-market-flow-canonical-reconciliation-001-20260917`

The protected C-drive owner checkout was used only for read-only baseline evidence and was not mutated.

## 2. Exact source recovery and provenance

The FUND-A source was recovered from the expected dedicated worktree and branch:

| Evidence | Exact value |
|---|---|
| Source task | `TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001` |
| Source worktree | `E:\topicpilot-worktrees\fund-a-market-flow-formal-capability-001` |
| Source branch | `codex/task-fund-a-market-flow-formal-capability-001` |
| Source final closeout SHA | `1cd5af2f55f7abc715e0d23ee09721767ab662d4` |
| Source implementation SHA | `b062df38c6cd0bf6f238b849d2ff2600f5c63411` |
| Source governance closeout SHA | `a5e54a9d73e57a466325417151beb895f55d1229` |
| Source provenance-pin SHA | `ee95deae125c19d9d7c2e9970d18fb07365b70df` |
| Source reported base SHA | `07b7a73e7cfd070aae39a2d61240bf5050e19e4a` |
| Source status before integration | `READY_FOR_INTEGRATION` |
| Source canonicalization before integration | `NOT_CANONICALIZED` |

The source implementation commit has exactly the current governed development base as its parent. This makes the source-to-canonical relationship deterministic: the implementation was replayed with `git cherry-pick -x`, then the source governance closeout and provenance corrections were replayed in order. No unrelated source branch history was merged.

The source-side evidence is retained in the repository at [`TASK-FUND-A` task manifest](docs/governance/tasks/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001.yaml), [`TASK-FUND-A` provenance](docs/governance/provenance/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001.json), and the source [`FUND-A` closeout report](docs/reports/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001/README.md).

## 3. Canonical baseline and concurrent-state audit

The prior governed baseline was `277a49382240503fcd0767e9cfb17e2fd974e8a`. The current governed development head before FUND-A integration was `07b7a73e7cfd070aae39a2d61240bf5050e19e4a`; this is the exact base used by the source task and by the isolated integration branch.

The C-drive owner checkout was separately verified as:

| Evidence | Exact value |
|---|---|
| Checkout | `C:\Users\acer\Desktop\題材領航\topicpilot-platform` |
| Branch | `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` |
| HEAD | `02d3086183d1c582bb6c66c4c316340ccce3fa97` |
| Pre-existing status entries | `152` |
| Mutation performed | `NO` |

The C-drive checkout is protected dirty owner state and is not treated as the integration target. The clean governed owner-closure worktree at the `07b7a73e...` head is the canonical development base for this task.

The concurrent-state audit found no FUND-A collision requiring a wait or a rebase:

| Workstream | Result |
|---|---|
| FUND-B | No branch-only implementation was present at the audited reference; no FUND-A path collision; no wait or integration performed |
| Daily Close / A10 | Concurrent changes are confined to live persistence/post-close/market-data runtime paths and tests; no FUND-A collision; no runtime change made |
| B2 / Topic | No FUND-A collision; no topic authority or lifecycle change made |
| Opportunity | No FUND-A collision; no Opportunity policy or implementation change made |
| C-drive owner checkout | Read-only evidence only; untouched |

The only test-file reconciliation needed after adding migration `0041` was to update the canonical migration-head expectation and the implemented-V2-table freeze list. These are contract-maintenance assertions required by the new migration and do not change product behavior or policy.

## 4. Source diff inventory and path authorization

The source implementation commit changed 22 product, contract, migration, API-client, web, and test paths. Every source path was classified before integration.

### FUND-A implementation paths

- `apps/web/app/components/v2/TodayMarketPage.tsx`
- `apps/web/app/lib/generated-api.d.ts`
- `apps/web/tests/today-market-institutional-flow.test.mjs`
- `packages/api-client/openapi.json`
- `packages/api-client/src/client.d.mts`
- `packages/api-client/src/client.mjs`
- `packages/api-client/src/schema.d.ts`
- `packages/api-client/tests/client.test.mjs`
- `services/api/alembic/versions/0041_task_fund_a_market_flow_formal_capability.py`
- `services/api/src/topicpilot_api/home_v2_publication.py`
- `services/api/src/topicpilot_api/main.py`
- `services/api/src/topicpilot_api/market_data/__init__.py`
- `services/api/src/topicpilot_api/market_data/institutional_flow.py`
- `services/api/src/topicpilot_api/market_data/institutional_flow_persistence.py`
- `services/api/src/topicpilot_api/market_institutional_flow_api.py`
- `services/api/src/topicpilot_api/orm/__init__.py`
- `services/api/src/topicpilot_api/orm/institutional_flow.py`
- `services/api/src/topicpilot_api/schemas.py`
- `services/api/tests/fixtures/institutional_flow/tpex_3insti_summary_valid.json`
- `services/api/tests/fixtures/institutional_flow/twse_bfi82u_valid.json`
- `services/api/tests/test_institutional_flow.py`
- `services/api/tests/test_market_institutional_flow_api.py`

### Governance and integration evidence paths

The source closeout preserved these governance artifacts:

- `docs/governance/provenance/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001.json`
- `docs/governance/tasks/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001.yaml`
- `docs/reports/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001/README.md`
- `docs/reports/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001/canonical-capability-map.md`
- `docs/reports/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001/closeout-report.md`
- `docs/reports/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001/contract-lifecycle-freshness.md`
- `docs/reports/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001/historical-artifact-disposition.md`
- `docs/reports/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001/migration-provenance.md`
- `docs/reports/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001/provider-provenance.md`
- `docs/reports/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001/validation-evidence.md`

This integration added or reconciled:

- `docs/governance/BASELINE_FAILURE_REGISTRY.yaml`
- `services/api/tests/test_canonical_observation_implementation.py`
- `services/api/tests/test_v2_architecture_freeze.py`
- `docs/governance/tasks/TASK-INT-FUND-A-MARKET-FLOW-CANONICAL-RECONCILIATION-001.yaml`
- `docs/governance/provenance/TASK-INT-FUND-A-MARKET-FLOW-CANONICAL-RECONCILIATION-001.json`
- `docs/reports/TASK-INT-FUND-A-MARKET-FLOW-CANONICAL-RECONCILIATION-001-20260917.md`

The source FUND-A task manifest's `dependencies` list was normalized from three prose descriptions to the valid task IDs `GOV-003`, `TASK-OWNER-TOPICPILOT-CANONICAL-PROMOTION-RELEASE-AND-RUNTIME-CLOSURE-001`, and `TASK-INT-A10-A9-REC-002-MANIFEST-AND-0040-RECONCILIATION-001`. The original baseline, migration-chain, and authorization explanations remain in `dependency_notes`; source commit SHAs and product scope are unchanged.

Path partition result:

| Classification | Result |
|---|---|
| FUND-A owned implementation and tests | Authorized and integrated |
| Shared API/schema/OpenAPI/generated-client surfaces | Explicitly reconciled and validated |
| Today Market consumer surfaces | Explicitly reconciled; owner boundary preserved |
| Governance and evidence | Preserved or added under integration ownership |
| Unauthorized paths | `0` |
| Unknown paths | `0` |

No path under `services/api/src/topicpilot_api/live/**`, the B2/topic engine, Opportunity, migration `0040`, production infrastructure, `NEXT_TASK`, project memory, or the protected C-drive owner checkout was changed.

## 5. FUND-A semantics preserved

The integrated capability remains a formal market-level institutional-flow fact, not a stock-level or policy-authority feature.

- TPE uses the official TWSE `fund.BFI82U` source.
- TWO uses the official TPEx `tpex_3insti_summary` source.
- TPE and TWO are kept as distinct market scopes and are not mixed.
- The canonical unit is `TWD` with scale `0`.
- Buy, sell, and net values remain explicit rather than inferred from a display label.
- `source`, `sourceAsOf`, freshness, availability, and `statusReason` remain part of the contract.
- Missing numeric values do not become zero.
- Availability remains explicit through `AVAILABLE`, `NOT_YET_PUBLISHED`, `SOURCE_UNAVAILABLE`, `INGESTION_FAILED`, and `NON_TRADING_DAY`.
- Freshness remains explicit through `CURRENT`, `STALE`, and `UNKNOWN`.
- Provider failures and contract failures remain distinguishable; no generic `NO_DATA` fallback was introduced.
- Persistence remains replayable and idempotent through the daily fact table and source identity.

The source provider and date-semantics evidence remains available in [`provider-provenance.md`](docs/reports/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001/provider-provenance.md), while the migration lineage and execution boundary remain documented in [`migration-provenance.md`](docs/reports/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001/migration-provenance.md).

## 6. Today Market, Today Signals, and authority boundaries

The integrated API exposes `GET /api/v2/market/institutional-flow` and adds the formal nested `marketOverview.institutionFlows` contract consumed by Today Market. Today Market renders the formal flow data as a consumer; it does not become the owner of the underlying fact, source semantics, or persistence.

Today Signals retains its existing `INSTITUTION_PRICE_DIVERGENCE` evidence path. FUND-A evidence is available to that existing evidence integration, but the integration does not add or alter scoring, ranking, thresholds, signal policy, risk policy, or publication authority. `TODAY_SIGNALS_POLICY_CHANGED=NO`.

Daily Close scheduler and live runtime behavior are untouched. B2 retains topic-authority ownership, and Opportunity retains its own policy and implementation boundary. No cross-workstream authority was transferred.

## 7. Migration boundary

Migration `0041_task_fund_a_market_flow_formal_capability.py` is the only new migration in this integration. Its `down_revision` is exactly `0040_task_a10_recovery_checkpoint_observability`. The content of migration `0040_task_a10_recovery_checkpoint_observability.py` was verified unchanged, and no historical `0040` artifact was reintroduced.

No migration was run against any database. No PostgreSQL round-trip was attempted because the environment had no `TEST_DATABASE_URL` or `DATABASE_URL`. The migration remains a release/operations gate, not an action performed by this development canonicalization task.

## 8. Validation evidence

### Focused FUND-A and adjacent API validation

The focused backend suite passed:

`26 passed, 1 warning`

This includes the FUND-A unit/API tests plus Home publication and Home status contract coverage. The warning is the existing Starlette deprecation warning.

### Full backend comparison

The clean `07b7a73e...` baseline was run first, then the composed integration branch was run after the two required canonical contract assertions were reconciled.

| Run | Passed | Registered baseline failures | Skipped |
|---|---:|---:|---:|
| Clean pre-integration baseline | 734 | 14 | 59 |
| Final integrated branch | 744 | 14 | 59 |

The executed-test count therefore moved from `748` to `758`, a delta of `+10` attributable to the FUND-A coverage. The same 14 baseline failures remain and no task-caused failure remains.

The 14 registered baseline failures are:

- 9 pre-existing TOPIC_B2 lifecycle failures already registered in the baseline registry.
- 5 WS3 research-artifact failures registered during this task because the clean baseline lacks the required research JSON artifacts:
  - `test_candidate_freeze_is_deterministic_and_complete`
  - `test_pit_and_outcome_boundaries_are_explicit`
  - `test_raw_cohort_authority_is_preserved`
  - `test_thresholds_and_operators_are_immutable_freeze_values`
  - `test_a1_forward_contract_preserves_exact_seven_candidates`

These are classified as `OTHER_WORKSTREAM` failures owned by WS3, expire `2026-09-30`, and are not masked by changing product logic. The registry is at [`BASELINE_FAILURE_REGISTRY.yaml`](docs/governance/BASELINE_FAILURE_REGISTRY.yaml).

An initial full-suite invocation used a mis-scoped relative `PYTHONPATH` and produced import errors. The command scope was corrected, the clean baseline and final integration suite both completed, and that invocation is classified as environment/command setup rather than a task failure; it is not included in the final failure counts.

### Client, web, contract, and static validation

- API-client `npm run check` and tests: `5 passed`.
- OpenAPI generation/synchronization: `PASS`.
- OpenAPI drift checker: `PASS`.
- Web build: `PASS`.
- Web tests: `165 passed`.
- Web lint: `0 errors`, `2 existing warnings`.
- FUND-A changed-file Ruff check: `PASS`.
- FUND-A new-file Ruff format check: `PASS`.
- Python compileall: `PASS`.
- `git diff --check`: `PASS`.
- Conflict/secret scan: `PASS`.

The two web lint warnings are pre-existing warnings in `apps/web/app/components/FavoriteButton.tsx` and `apps/web/tests/stock-formal-capability-reconciliation.test.mjs`. Repository format checking also reports pre-existing formatting debt in shared baseline files `services/api/src/topicpilot_api/home_v2_publication.py`, `services/api/src/topicpilot_api/schemas.py`, and one existing test line in `services/api/tests/test_canonical_observation_implementation.py`. The shared-file failures reproduce on the clean `07b7a73e...` baseline and are not task-caused regressions; all new FUND-A files pass their focused format check.

Dependency installation for the API client and web package completed without lockfile changes. Package-manager audit advisories are dependency metadata and did not cause a test, build, or drift failure.

### Failure and gate classification

| Classification | Count/result |
|---|---|
| Task-caused failures after reconciliation | `0` |
| Registered baseline failures | `14` |
| Environment skips | `59` |
| Unknown failures | `0` |
| PostgreSQL round-trip | `NOT_RUN` — no database URL available |
| Production contact | `NONE` |

The source integration gate, provenance check, base-parent check, path authorization, semantic reconciliation, OpenAPI/client synchronization, focused tests, lifecycle check, worktree check, ownership check, governance self-test, and repository-wide task-manifest commit check are passing. The source manifest dependency normalization described above was a governance-only correction required by the checker and has no product-semantic effect. The only remaining external gate is a separately authorized PostgreSQL round-trip/release validation.

## 9. Explicit Q1-Q17 answers

| Question | Answer |
|---|---|
| Q1. Was the exact FUND-A source recovered? | **Yes.** The dedicated source worktree, branch, final SHA, implementation SHA, governance SHA, provenance SHA, and base SHA are recorded above and in the integration provenance artifact. |
| Q2. Was the exact FUND-A implementation integrated? | **Yes.** `b062df38c6cd0bf6f238b849d2ff2600f5c63411` was replayed with explicit provenance. |
| Q3. What is the current canonical base? | **`07b7a73e7cfd070aae39a2d61240bf5050e19e4a`.** The prior governed base was `277a49382240503fcd0767e9cfb17e2fd974e8a3`. |
| Q4. Was there a collision with newer canonical work? | **No.** The source parent exactly matches the current governed development base; only two necessary migration/table-freeze test assertions were reconciled. |
| Q5. Was there a FUND-B collision? | **No.** No FUND-B implementation was integrated, and no wait was required. |
| Q6. Were any unauthorized paths changed? | **No.** Unauthorized paths: `0`; unknown paths: `0`. |
| Q7. Is formal FUND-A data consumed by Today Market? | **Yes.** The additive `marketOverview.institutionFlows` contract and render-only Today Market consumer are integrated. |
| Q8. Is the official-source evidence integration preserved? | **Yes.** TWSE/TPEx source identity, date semantics, freshness, availability, and status-reason evidence are preserved. |
| Q9. Did Today Signals policy change? | **No.** Existing `INSTITUTION_PRICE_DIVERGENCE` evidence integration is preserved without scoring, ranking, threshold, or risk-policy changes. |
| Q10. Did Daily Close runtime change? | **No.** Scheduler, live runtime, and post-close behavior are untouched. |
| Q11. Did B2 authority change? | **No.** Topic authority and lifecycle ownership remain unchanged. |
| Q12. Did Opportunity policy change? | **No.** Opportunity implementation and policy remain outside scope and untouched. |
| Q13. Was migration 0040 touched or reintroduced? | **No.** `0040` is untouched, no historical `0040` was reintroduced, and no migration was executed. |
| Q14. Are OpenAPI and generated clients synchronized? | **Yes.** OpenAPI drift and generated-client checks pass; API-client tests pass. |
| Q15. Do the required FUND-A integration gates pass? | **Yes, with the external database gate noted.** Focused, client, web, build, static, provenance, ownership, and governance gates pass; PostgreSQL round-trip was not run because no database URL was available. |
| Q16. Is FUND-A canonically integrated into the development series? | **Yes.** The canonical integration composition is committed at `589d33ed9389a418183f1505e221cd62217e3ef4`, with the final governance record committed afterward. |
| Q17. Was FUND-A released to production? | **No.** Production remains `NOT_RELEASED`; no production mutation, migration, deploy, scheduler activation, or push occurred. |

## 10. Governance artifacts

- [`TASK-INT-FUND-A` task manifest](docs/governance/tasks/TASK-INT-FUND-A-MARKET-FLOW-CANONICAL-RECONCILIATION-001.yaml)
- [`TASK-INT-FUND-A` provenance](docs/governance/provenance/TASK-INT-FUND-A-MARKET-FLOW-CANONICAL-RECONCILIATION-001.json)
- [`BASELINE_FAILURE_REGISTRY.yaml`](docs/governance/BASELINE_FAILURE_REGISTRY.yaml)
- [`FUND-A source closeout report`](docs/reports/TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001/README.md)

The lifecycle is advanced from `READY_FOR_INTEGRATION` to `INTEGRATED`. The next allowed state is `READY_FOR_RELEASE`; no automatic release action is authorized by this task.

TASK:
  TASK-INT-FUND-A-MARKET-FLOW-CANONICAL-RECONCILIATION-001
ROLE:
  INTEGRATION_OWNER
MODE:
  ONE_SHOT_FUND_A_CANONICAL_RECONCILIATION_VALIDATION_AND_CLOSEOUT
RESULT:
  COMPLETE_WITH_EXTERNAL_GATE
STOP_REASON:
  DEVELOPMENT_CANONICALIZATION_COMPLETE; POSTGRES_ROUND_TRIP_AND_PRODUCTION_RELEASE_REMAIN_OUT_OF_SCOPE
SOURCE_TASK:
  TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001
SOURCE_IMPLEMENTATION_SHA:
  b062df38c6cd0bf6f238b849d2ff2600f5c63411
SOURCE_GOVERNANCE_SHA:
  a5e54a9d73e57a466325417151beb895f55d1229
SOURCE_CLOSEOUT_SHA:
  1cd5af2f55f7abc715e0d23ee09721767ab662d4
PREVIOUS_CANONICAL_BASE_SHA:
  277a49382240503fcd0767e9cfb17e2fd974e8a3
CURRENT_CANONICAL_BASE_SHA:
  07b7a73e7cfd070aae39a2d61240bf5050e19e4a
CANONICAL_FUND_A_INTEGRATION_SHA:
  589d33ed9389a418183f1505e221cd62217e3ef4
FUND_A_SOURCE_PROVENANCE:
  VERIFIED
FUND_A_SEMANTIC_RECONCILIATION:
  PASS
FUND_A_MARKET_FLOW:
  INTEGRATED
TODAY_MARKET_INTEGRATION:
  INTEGRATED
TODAY_SIGNALS_EVIDENCE_INTEGRATION:
  INTEGRATED
TODAY_SIGNALS_POLICY_CHANGED:
  NO
FUND_B_CONCURRENCY_COLLISION:
  NONE
DAILY_CLOSE_RUNTIME_CHANGED:
  NO
B2_AUTHORITY_CHANGED:
  NO
OPPORTUNITY_POLICY_CHANGED:
  NO
MIGRATION_0040:
  UNTOUCHED
HISTORICAL_0040_REINTRODUCED:
  NO
UNAUTHORIZED_PATHS:
  0
UNKNOWN_PATHS:
  0
OWNERSHIP_PRESERVED:
  YES
OPENAPI_DRIFT:
  PASS
GENERATED_CLIENT_DRIFT:
  PASS
FOCUSED_TESTS:
  26 passed
BACKEND_TESTS:
  PRE 734 passed / POST 744 passed; 14 registered baseline failures unchanged; 59 environment skips
API_CLIENT_TESTS:
  5 passed
WEB_TESTS:
  165 passed; build PASS; lint 0 errors / 2 existing warnings
STATIC_VALIDATION:
  Ruff check PASS; FUND-A Ruff format PASS; compileall PASS; diff-check PASS; conflict/secret scan PASS; shared pre-existing format debt reproduced at 07b
TASK_CAUSED_FAILURES:
  0
REGISTERED_BASELINE_FAILURES:
  14
ENVIRONMENT_FAILURES:
  59 skips; PostgreSQL round-trip not run (no DB URL)
UNKNOWN_FAILURES:
  0
INTEGRATION_GATE:
  PASS
LIFECYCLE_BEFORE:
  READY_FOR_INTEGRATION
LIFECYCLE_AFTER:
  INTEGRATED
FUND_A_CANONICAL_DEVELOPMENT:
  INTEGRATED
FUND_A_DEVELOPMENT_SERIES:
  CLOSED
FUND_A_PRODUCTION:
  NOT_RELEASED
PRODUCTION_MUTATION:
  NONE
MIGRATION_EXECUTION:
  NONE
C_DRIVE:
  UNTOUCHED
PUSH:
  NO
NEXT_TASK_CHANGED:
  NO
PROJECT_MEMORY_RECOVERY_TEST:
  PASS
OWNER_DECISION_REQUIRED:
  NO
INTEGRATION_OWNER_ACTION_REQUIRED:
  NO
NEXT_GOVERNED_ACTION:
  Separate release/operations task may run approved non-Production 0041 migration and later release gates; no automatic deployment or FUND-B integration

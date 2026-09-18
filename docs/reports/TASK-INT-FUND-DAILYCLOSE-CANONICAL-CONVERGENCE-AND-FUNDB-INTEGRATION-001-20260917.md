# TASK-INT-FUND-DAILYCLOSE-CANONICAL-CONVERGENCE-AND-FUNDB-INTEGRATION-001

## 1. Result

Development canonical convergence is complete in the isolated integration worktree. The unified forward line contains the current FUND-A canonical capability, the Daily Close `EXCHANGE_NO_DATA` engineering remediation, and the FUND-B stock institutional-flow capability.

The protected C-drive owner checkout was not modified. No Production deployment, replay, migration execution, canary, scheduler activation, database mutation, or push was performed. Production release remains an external gate.

Integration worktree:

`E:\topicpilot-worktrees\int-fund-dailyclose-convergence-fundb-20260917`

Integration branch:

`codex/task-int-fund-dailyclose-canonical-convergence-and-fundb-integration-20260917`

Unified development code head before this report's governance commit:

`18a0428af2988ff65becdf14b09f0fede8d81d0c`

## 2. Canonical lineage reconstruction

The repository authority was recovered from ancestry, worktrees, task evidence, and governance records. The current authoritative canonical development base before this task was the FUND-A final governance head `f02ef61e588a8114aea4043128ab207c4f978516`, which descends from the owner-closure baseline and contains the completed FUND-A integration.

The relevant lineage is:

```text
02d3086  C-drive owner HEAD; ancestor of all current governed candidates
    |
    +--> 277a493  previous governed canonical baseline
            |
            +--> 07b7a73  owner canonical closure / current forward base
            |      |
            |      +--> 589d33e  FUND-A canonical composition
            |             |
            |             +--> f02ef61  FUND-A final governance / authoritative base
            |
            +--> 2cfd954  Daily Close remediation candidate
                   |
                   +--> 2e0eec7  Daily Close final task head
```

FUND-A `589d33e...` and Daily Close `2cfd954...` are not ancestor/descendant candidates. Their merge base is `277a49382240503fcd0767e9cfb17e2fd974e8a3`; they were therefore treated as parallel candidates and semantically converged. The latest valid canonical line was retained at `f02ef61...`, then the Daily Close remediation and governance evidence were replayed onto it.

FUND-B source implementation `192ec78...` was created from `02d3086...`, which is an ancestor of the unified line. The source product capability was therefore eligible for forward reconciliation, but its historical migration could not be imported unchanged.

The protected C-drive owner checkout remains:

| Evidence | Value |
|---|---|
| Checkout | `C:\Users\acer\Desktop\題材領航\topicpilot-platform` |
| Branch | `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` |
| HEAD | `02d3086183d1c582bb6c66c4c316340ccce3fa97` |
| Existing status entries | `152` |
| Mutation | `NO` |

## 3. FUND-A provenance and reconciliation

FUND-A was not reimplemented. The exact prior evidence was recovered from the completed FUND-A integration:

| Evidence | SHA / state |
|---|---|
| Source task | `TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001` |
| Canonical integration SHA | `589d33ed9389a418183f1505e221cd62217e3ef4` |
| Final governance SHA | `f02ef61e588a8114aea4043128ab207c4f978516` |
| Reported base | `07b7a73e7cfd070aae39a2d61240bf5050e19e4a` |
| Development state | `CANONICALLY_INTEGRATED` |

The unified candidate still contains:

- official TWSE market-level `fund.BFI82U` and TPEx `tpex_3insti_summary` adapters;
- TWD scale-0 market flow facts with explicit source identity, source-as-of, freshness, availability, and status reason;
- additive `marketOverview.institutionFlows` and render-only Today Market consumption;
- existing Today Signals `INSTITUTION_PRICE_DIVERGENCE` evidence integration without policy change;
- no composite score, recommendation, ranking, threshold, or risk-policy invention.

`FUND_A_POLICY_CHANGED=NO` and `TODAY_SIGNALS_POLICY_CHANGED=NO`.

## 4. Daily Close provenance and convergence

Daily Close source evidence was recovered from:

| Evidence | SHA / state |
|---|---|
| Source task | `TASK-INT-DAILY-CLOSE-CANONICAL-RELEASE-REPLAY-AND-FORMAL-E2E-CLOSURE-001` |
| Source remediation | `3e602119284dd7abe0779a107e5f004052bc0ac1` |
| Reported canonical integration | `2cfd954ee68e8bb53571271870dbc99fabc81360` |
| Final source task head | `2e0eec7f442d092cb6e631c337f65a369e21afeb` |
| Source base | `277a49382240503fcd0767e9cfb17e2fd974e8a3` |
| Source release gate | `BLOCKED` |

The remediation was replayed onto the current FUND-A canonical base as `4cba30bed48ea667f975950126f4c8fa7b128f18`, followed by the Daily Close governance handoff and final provenance corrections as `e10050ffc83b0d341bfc0d98c27a953f3ed984f9` and `048fd8758d9ad072a5daee12b6af4a857f7bd72d`.

The integrated behavior preserves the corrected provider-response diagnostic classification and prior-session rollback containment across `live/persistence.py`, `live/post_close.py`, `market_data/exchange.py`, `market_data/history.py`, and `market_data/ingestion.py`.

Development Daily Close behavior is integrated. Daily Close Production E2E is not claimed as passed: the exact deployment/canary provenance, operator authority, 2026-09-15 replay, and formal production readback remain external gates.

## 5. FUND-B provenance

The exact FUND-B source was recovered from:

`E:\topicpilot-worktrees\fund-b-stock-institutional-flow-formal-capability-001`

| Evidence | SHA / state |
|---|---|
| Source task | `TASK-FUND-B-STOCK-INSTITUTIONAL-FLOW-FORMAL-CAPABILITY-001` |
| Source branch | `codex/task-fund-b-stock-institutional-flow-formal-capability-001` |
| Source base | `02d3086183d1c582bb6c66c4c316340ccce3fa97` |
| Source implementation | `192ec78fd055dc94a167bfa3501f32ccef9576dc` |
| Source governance closeout | `3c73631105090b0ceb439b064520d5fd6dd44567` |
| Source final provenance pin | `73b788db765e48f3d76733a93adf383c1664e80e` |
| Source reported canonical status | `NOT_CANONICALIZED` |
| Source disposition | `READY_FOR_CANONICAL_RECONCILIATION` |

The source capability is preserved as evidence-only architecture:

- TPE official stock institutional flow: `READY`.
- TWO official stock institutional flow: `PARTIAL`.
- Unit: `SHARES`, scale `0`.
- Windows: `1D`, `5D`, `10D`, `20D` trading-session semantics where historical sessions are available.
- Streaks, reversal, price-flow context, deterministic divergence evidence, and positive-denominator liquidity-relative flow are preserved.
- Formal endpoint: `GET /api/v2/stocks/{symbol}/institutional-flow`.
- No composite institutional score, recommendation, Opportunity policy, Today Signals policy, or FUND-E implementation was added.

## 6. FUND-B diff inventory

### FUND-B owned capability

- `services/api/src/topicpilot_api/market_data/stock_institutional_flow.py`
- `services/api/src/topicpilot_api/stock_institutional_flow_persistence.py`
- `services/api/src/topicpilot_api/stock_institutional_flow_api.py`
- `services/api/src/topicpilot_api/orm/stock_institutional_flow.py`
- `services/api/tests/fixtures/tpex_3insti_daily_trading.json`
- `services/api/tests/fixtures/twse_t86_stock_flow.json`
- `services/api/tests/test_stock_institutional_flow.py`

### Stock consumer

- `apps/web/app/lib/stock-api.ts`

The consumer was reconciled with the existing technical stock client surface. Both the technical evidence adapter and stock institutional-flow adapter remain additive and render-only.

### Shared contract and generated surfaces

- `services/api/src/topicpilot_api/schemas.py`
- `services/api/src/topicpilot_api/main.py`
- `services/api/src/topicpilot_api/orm/__init__.py`
- `packages/api-client/openapi.json`
- `packages/api-client/src/client.mjs`
- `packages/api-client/src/schema.d.ts`
- `packages/api-client/tests/client.test.mjs`
- `apps/web/app/lib/generated-api.d.ts`
- `services/api/tests/test_canonical_observation_implementation.py`
- `services/api/tests/test_v2_architecture_freeze.py`

### Daily Close paths

- `services/api/src/topicpilot_api/live/persistence.py`
- `services/api/src/topicpilot_api/live/post_close.py`
- `services/api/src/topicpilot_api/market_data/exchange.py`
- `services/api/src/topicpilot_api/market_data/history.py`
- `services/api/src/topicpilot_api/market_data/ingestion.py`
- `services/api/tests/test_post_close_exchange_failure_recovery.py`

### Governance and evidence

The Daily Close closeout packet and FUND-B source closeout packet are retained under `docs/reports/**`. The new convergence manifest, provenance, and this report are the integration-owner record.

`UNAUTHORIZED_PATHS=0` and `UNKNOWN_PATHS=0`.

No Topic UX, B2 policy, Opportunity policy, FUND-E implementation, `NEXT_TASK`, C-drive owner checkout, or Production path was changed.

## 7. Migration 0033 audit and disposition

The original FUND-B migration was:

| Field | Original value |
|---|---|
| Filename | `0033_task_fund_b_stock_institutional_flow.py` |
| Revision | `0033_task_fund_b_stock_institutional_flow` |
| Down revision | `0032_task_ws1_topic_lifecycle_contract_gap_closure` |
| Branch labels | `None` |
| Depends on | `None` |
| Creation base | `02d3086183d1c582bb6c66c4c316340ccce3fa97` |
| Purpose | Create `topicpilot.stock_institutional_flow_daily` and its indexes/constraints |

This artifact cannot be directly integrated:

1. The current canonical chain is already at `0041_task_fund_a_market_flow_formal_capability`.
2. The source `0033` points backward to obsolete `0032`.
3. The canonical tree already contains a different numeric-0033 revision, `0033_task_ws4_reference_registry_transition_merge`, so reusing the historical revision would create an ambiguous and invalid chain.
4. The stock table is genuinely new; no equivalent stock institutional-flow schema exists in the current canonical ORM/migration chain.

The minimum semantic port is therefore:

`0042_task_fund_b_stock_institutional_flow_forward`

with:

`down_revision = "0041_task_fund_a_market_flow_formal_capability"`

The table, indexes, constraints, unit (`SHARES`), scale (`0`), source fields, freshness/status fields, and idempotent identity are preserved. Historical `0033` is not present in the unified candidate. Migration `0040_task_a10_recovery_checkpoint_observability.py` is byte-for-byte unchanged, and no migration was executed.

Disposition: `REBASE_TO_NEW_FORWARD_REVISION` with semantic port required.

Alembic reports one head only: `0042_task_fund_b_stock_institutional_flow_forward`.

## 8. Semantic reconciliation and TWO partial semantics

| Capability | Current canonical reality | Action |
|---|---|---|
| FUND-A market flow | Identical/present in `f02ef61` | Preserved |
| Daily Close remediation | Missing from `f02ef61`, present in parallel candidate | Replayed and validated |
| FUND-B product capability | Missing from `f02ef61` | Semantically ported from verified source |
| FUND-B historical migration 0033 | Conflicting/obsolete | Superseded by forward 0042 |
| Shared OpenAPI/client/schema | Shared surface | Reconciled additively and regenerated |

TWO is not silently upgraded. The source provider is current-snapshot-only. Available data includes the current snapshot's institutional legs, total buy/sell/net, source identity, source-as-of, freshness, and availability/status reason. Historical `5D/10D/20D` windows and derived streak/reversal values that require missing historical sessions remain unavailable or partial. Missing sessions are not fabricated and missing numbers are not converted to zero.

TPE uses the official TWSE `fund.T86` source and preserves full historical request semantics. TWO uses the official TPEx `tpex_3insti_daily_trading` source and retains its exact current-snapshot limitation.

FUND-C evidence readiness is `READY` as a data-contract readiness statement only. No FUND-C score, ranking, recommendation, selector policy, or weight was implemented.

## 9. Authority boundaries

- `COMPOSITE_INSTITUTIONAL_SCORE_CREATED=NO`.
- `FUND_A_POLICY_CHANGED=NO`.
- `TODAY_SIGNALS_POLICY_CHANGED=NO`.
- `TOPIC_UX_CHANGED=NO`.
- `B2_POLICY_CHANGED=NO`.
- `OPPORTUNITY_POLICY_CHANGED=NO`.
- `FUND_E_IMPLEMENTED=NO`.
- B2 remains `READY_POLICY_ONLY` / evidence-verified but not formally published.
- A9 formal writer and B2 formal publication remain blocked by their independent gates.
- Opportunity Daily Recommendation remains `NO` because Daily Close Production E2E and formal B2/A9 inputs are not complete.
- Daily Close runtime engineering is integrated for development, but Production E2E remains `NOT_VERIFIED`.

## 10. Validation

### Focused and regression tests

- Combined FUND-A + FUND-B + Daily Close/Home backend focus: `39 passed, 1 existing Starlette warning`.
- Targeted Daily Close contract/provider/runtime focus: `63 passed`.
- API client check and tests: `6 passed`; generated client synchronization passed.
- Web build: `PASS`.
- Web tests: `165 passed`.
- Web lint: `0 errors, 2 existing warnings`.
- Full backend on the unified candidate: `762 passed, 14 registered baseline failures, 59 skipped, 1 warning`.
- Prior current-authoritative FUND-A baseline: `744 passed, 14 registered baseline failures, 59 skipped`.
- Full-backend delta: `+18 passed`, with no new failure.

The 14 full-backend failures are unchanged registered baseline failures: 9 existing TOPIC_B2 lifecycle failures and 5 WS3 research-artifact failures already registered in the baseline registry. No task-caused failure and no unknown failure was introduced.

The first full-backend invocation omitted the repository root from `PYTHONPATH` and failed during `infra` test collection. The corrected root-plus-API-source invocation completed and produced the regression counts above; the initial invocation is classified as an environment/command-scope issue.

### Static and contract validation

- OpenAPI drift: `PASS`.
- Generated client drift: `PASS`.
- Alembic single-head check: `PASS`, head `0042_task_fund_b_stock_institutional_flow_forward`.
- Ruff check on changed Python files: `PASS`.
- Ruff format on new/changed FUND-B and Daily Close files: `PASS`.
- Shared baseline `schemas.py` format debt: reproduced from the prior canonical line; not reformatted as unrelated debt.
- Python compileall: `PASS`.
- `git diff --check`: `PASS`.
- Conflict-marker scan: `PASS`.
- PostgreSQL migration/round-trip: `NOT_RUN`; no test database URL was configured.

### Governance

The source provenance, migration lineage, path ownership, lifecycle, worktree, and integration gates are represented in:

- [`convergence task manifest`](../governance/tasks/TASK-INT-FUND-DAILYCLOSE-CANONICAL-CONVERGENCE-AND-FUNDB-INTEGRATION-001.yaml)
- [`convergence provenance`](../governance/provenance/TASK-INT-FUND-DAILYCLOSE-CANONICAL-CONVERGENCE-AND-FUNDB-INTEGRATION-001.json)
- [`FUND-B source evidence`](TASK-FUND-B-STOCK-INSTITUTIONAL-FLOW-FORMAL-CAPABILITY-001/implementation-evidence.json)
- [`Daily Close source evidence`](TASK-INT-DAILY-CLOSE-CANONICAL-RELEASE-REPLAY-AND-FORMAL-E2E-CLOSURE-001-20260916/validation-evidence.json)

The development lifecycle is `READY_FOR_INTEGRATION -> INTEGRATED`. The next allowed state is `READY_FOR_RELEASE`; this task does not authorize release or Production operations.

## 11. Final unified canonical state

The unified forward development line is authoritative for this isolated convergence task and contains:

1. the current FUND-A canonical line;
2. the Daily Close engineering remediation and its governance evidence;
3. the FUND-B stock institutional-flow capability;
4. a valid forward migration chain ending at `0042`;
5. synchronized OpenAPI and generated clients;
6. preserved B2, A9, Topic UX, Today Signals, Opportunity, and FUND-E boundaries.

Production release remains blocked by external exact-SHA deployment/canary/replay/readback authority. This is not a blocker to development canonical integration.

TASK:
  TASK-INT-FUND-DAILYCLOSE-CANONICAL-CONVERGENCE-AND-FUNDB-INTEGRATION-001
ROLE:
  INTEGRATION_OWNER
MODE:
  ONE_SHOT_FORWARD_CANONICAL_CONVERGENCE_FUNDB_RECONCILIATION_AND_CLOSEOUT
RESULT:
  COMPLETE_WITH_EXTERNAL_GATE
STOP_REASON:
  DEVELOPMENT_CANONICAL_CONVERGENCE_COMPLETE; PRODUCTION_DEPLOYMENT_CANARY_REPLAY_READBACK_AND_NON_PRODUCTION_MIGRATION_EXECUTION_REMAIN_EXTERNAL_GATES
PREVIOUS_AUTHORITATIVE_CANONICAL_SHA:
  f02ef61e588a8114aea4043128ab207c4f978516
FUND_A_SOURCE_SHA:
  589d33ed9389a418183f1505e221cd62217e3ef4
DAILY_CLOSE_SOURCE_SHA:
  2cfd954ee68e8bb53571271870dbc99fabc81360
FUND_B_SOURCE_SHA:
  192ec78fd055dc94a167bfa3501f32ccef9576dc
FUND_A_DAILYCLOSE_LINEAGE_RELATION:
  PARALLEL_CANDIDATES_COMMON_ANCESTOR_277A_CONVERGED_ON_F02
UNIFIED_FORWARD_BASE_SHA:
  18a0428af2988ff65becdf14b09f0fede8d81d0c
UNIFIED_CANONICAL_INTEGRATION_SHA:
  18a0428af2988ff65becdf14b09f0fede8d81d0c
FUND_A_CANONICAL:
  INTEGRATED
DAILY_CLOSE_ENGINEERING_CANONICAL:
  INTEGRATED
FUND_B_CANONICAL:
  INTEGRATED
FUND_B_MIGRATION_ORIGINAL:
  0033
FUND_B_MIGRATION_DISPOSITION:
  REBASE_TO_NEW_FORWARD_REVISION
FUND_B_FORWARD_MIGRATION_REVISION:
  0042_task_fund_b_stock_institutional_flow_forward
MIGRATION_LINEAGE:
  PASS
TPE_STOCK_INSTITUTIONAL_FLOW:
  READY
TWO_STOCK_INSTITUTIONAL_FLOW:
  PARTIAL
TWO_PARTIAL_REASON:
  CURRENT_SNAPSHOT_ONLY; HISTORICAL_SESSION_WINDOWS_FAIL_CLOSED
ROLLING_WINDOWS:
  ONE_DAY_READY; FIVE_DAY_TEN_DAY_TWENTY_DAY_COMPLETE_ONLY_WHEN_HISTORICAL_SESSIONS_EXIST
STREAKS:
  READY_WITH_EXPLICIT_SESSION_AVAILABILITY
FLOW_REVERSAL:
  READY_DETERMINISTIC_EVIDENCE_ONLY
PRICE_FLOW_CONTEXT:
  READY_EVIDENCE_ONLY
DIVERGENCE:
  READY_DETERMINISTIC_EVIDENCE_ONLY
LIQUIDITY_RELATIVE_FLOW:
  READY_POSITIVE_VOLUME_DENOMINATOR_ONLY
STOCK_INSTITUTIONAL_FLOW_API:
  GET /api/v2/stocks/{symbol}/institutional-flow
FUND_C_EVIDENCE_READINESS:
  READY
COMPOSITE_INSTITUTIONAL_SCORE_CREATED:
  NO
FUND_A_POLICY_CHANGED:
  NO
TODAY_SIGNALS_POLICY_CHANGED:
  NO
TOPIC_UX_CHANGED:
  NO
B2_POLICY_CHANGED:
  NO
OPPORTUNITY_POLICY_CHANGED:
  NO
FUND_E_IMPLEMENTED:
  NO
OPENAPI_DRIFT:
  PASS
GENERATED_CLIENT_DRIFT:
  PASS
FOCUSED_TESTS:
  39 backend passed; 63 targeted Daily Close passed
BACKEND_TESTS:
  PRE 744 passed / POST 762 passed; 14 registered baseline failures unchanged; 59 skipped
API_CLIENT_TESTS:
  6 passed
WEB_TESTS:
  165 passed; build PASS; lint 0 errors / 2 existing warnings
TASK_CAUSED_FAILURES:
  0
REGISTERED_BASELINE_FAILURES:
  14
ENVIRONMENT_FAILURES:
  59 skips; PostgreSQL round-trip not run; one corrected initial PYTHONPATH collection issue
UNKNOWN_FAILURES:
  0
INTEGRATION_GATE:
  PASS
PRODUCTION_RELEASE_GATE:
  BLOCKED_EXTERNAL
DAILY_CLOSE_PRODUCTION_E2E:
  NOT_VERIFIED
2026_09_15_REPLAY:
  NOT_RUN
B2_FORMAL_PUBLICATION:
  BLOCKED
OPPORTUNITY_DAILY_RECOMMENDATION_READY:
  NO
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
NEXT_GOVERNED_ACTION:
  Separate release/operations task may approve non-Production 0042 migration, exact deployment/canary provenance, Daily Close 2026-09-15 replay, and formal readback; B2/A9 publication and Opportunity readiness remain independently governed

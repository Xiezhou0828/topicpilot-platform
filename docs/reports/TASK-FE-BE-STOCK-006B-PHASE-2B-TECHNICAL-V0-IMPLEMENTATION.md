# TASK-FE-BE-STOCK-006B-PHASE-2B-TECHNICAL-V0-IMPLEMENTATION

**Workstream:** `WS2 / Stock Technical Publication / Phase 2B`
**Task ID:** `TASK-FE-BE-STOCK-006B-PHASE-2B-TECHNICAL-V0-IMPLEMENTATION`
**Review date:** `2026-08-16`
**Final status:** `IMPLEMENTED_AND_VALIDATED / CANONICALIZED`

## 1. Scope and routing

This task implements the Owner-authorized Phase 2B backend Technical V0
capability. It extends the existing foundation route and does not reopen the
canonical D1-D4 decisions in the [Technical V0 policy contract](../architecture/STOCK_TECHNICAL_V0_POLICY_CONTRACT.md).

```text
PHASE_2B_TECHNICAL_V0_IMPLEMENTATION_COMPLETE=YES
TECHNICAL_V0_CANONICALIZED=YES
TECHNICAL_V0_VERSION=stock-technical-publication.v2
TECHNICAL_POLICY_VERSION=stock-technical-v0-policy.v2
PRICE_BASIS=RAW_OBSERVED
CONTINUITY_POLICY=FORMAL_RAW_OBSERVED + BOUNDED_CONTINUITY_ASSURANCE
INDICATOR_LEVEL_CONTINUITY=YES
UNKNOWN_FAIL_CLOSED=YES
SYMBOL_LEVEL_GLOBAL_BLOCK=NO
FORMAL_PUBLICATION_IMPLEMENTED=YES
UNAVAILABLE_SEMANTICS_IMPLEMENTED=YES
PIT_AS_OF_BINDING=YES
SOURCE_LINEAGE_BINDING=YES
```

The implementation is deterministic on-read over the shared canonical
historical reader. It does not add a second technical authority, persistence,
migration, provider call, scheduler path, or browser calculation path.

## 2. Authority and provenance preflight

```text
SOURCE_BASELINE_SHA=20aa8bad1a10fe16725cc59d453e2595631a0f49
CANONICAL_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
SOURCE_BRANCH=codex/task-stock-technical-phase2b-20260816
SOURCE_WORKTREE=C:\Users\acer\Documents\Codex\ws2b-20260816
OWNER_TRACKED_STATUS_LINES=18
OWNER_UNTRACKED_STATUS_LINES=156
OWNER_STATUS_FINGERPRINT=9ffa477e5314757049c4e3e3ae5b873c83642cc87986148ac2dc700d3dac6bef
OWNER_STATE_PRESERVED=YES
PREDECESSOR_PHASE_2A2_CANONICAL_HEAD=0608f176dabe40353cbdcae153eb9fcd3b58563a
SOURCE_IMPLEMENTATION_COMMIT=fb8851e77feb828d3ea4a0f4fa4460483093f849
CANONICAL_PRE_SHA=a26fad00d2861c0ecbf763d3f2428b39343714fd
CANONICAL_PROMOTION_COMMIT=9b8ff5ca65b06af4b0c4c141e0aae86e8e440289
CANONICAL_POST_SHA=663c574c870d225bd93b66216ba98398d69c427c
```

The source baseline was created after a concurrent WS3 promotion advanced the
canonical branch from `2ef58c6` to `20aa8ba`; later concurrent WS1/WS3 work
advanced the canonical branch to `a26fad0` before promotion. Those commits are
not attributed to WS2. Existing worktrees and owner changes were retained.

Canonical evidence consumed:

- [Phase 2A Technical V0 policy closure](TASK-FE-BE-STOCK-006B-PHASE-2A-TECHNICAL-V0-POLICY-CLOSURE.md)
- [Phase 2A2 Owner policy canonical closure](TASK-FE-BE-STOCK-006B-PHASE-2A2-OWNER-TECHNICAL-V0-POLICY-CANONICAL-CLOSURE.md)
- [Phase 2A2 machine-readable readiness audit](../../reports/TASK-FE-BE-STOCK-006B-PHASE-2A2-OWNER-TECHNICAL-V0-POLICY-CANONICAL-CLOSURE/technical-v0-owner-policy-readiness-audit.json)
- [Stock Technical Publication Foundation](../architecture/STOCK_TECHNICAL_PUBLICATION_FOUNDATION.md)
- HIST-002B canonical historical OHLCV authority and Stock-006A read publication
- REC-A1 bounded research-only corporate-action evidence, consumed only through the explicit continuity-evidence boundary

## 3. Implemented indicator contract

The seven families and fourteen outputs are implemented exactly as frozen by
Phase 2A2. All calculations use accepted-session order, raw observed inputs,
Decimal arithmetic without intermediate presentation rounding, and no
calendar-day approximation or synthetic session.

| Family | Outputs | Algorithm/version | Minimum observations |
|---|---|---|---:|
| MA | `MA5`, `MA10`, `MA20`, `MA60` | `SMA_CLOSE_V1` | 5/10/20/60 closes |
| Distance | `DISTANCE_TO_MA20` | `DISTANCE_TO_MA20_V1` | 20 closes; zero denominator unavailable |
| Returns | `RAW_CLOSE_RETURN_5D`, `RAW_CLOSE_RETURN_20D` | `RAW_OBSERVED_CLOSE_RETURN_V1` | 6/21 closes |
| Volume MA | `VOLUME_MA5`, `VOLUME_MA20` | `SMA_VOLUME_QUANTITY_V1` | 5/20 volume sessions |
| Volume ratio | `VOLUME_RATIO_20` | `VOLUME_RATIO_20_V1` | 20 volume sessions; zero denominator unavailable |
| RSI | `RSI14` | `RSI_WILDER_14_V1` | 15 closes; 14-change seed |
| MACD | `MACD_12_26_9`, `MACD_SIGNAL_12_26_9`, `MACD_HISTOGRAM_12_26_9` | `MACD_12_26_9_SMA_SEEDED_EMA_V1` | line 26 closes; signal/histogram 34 |

```text
INDICATOR_FAMILIES_IMPLEMENTED=7
INDICATOR_OUTPUTS_IMPLEMENTED=14
MA5_STATE=IMPLEMENTED_WINDOW_GATED
MA10_STATE=IMPLEMENTED_WINDOW_GATED
MA20_STATE=IMPLEMENTED_WINDOW_GATED
MA60_STATE=IMPLEMENTED_WINDOW_GATED
DISTANCE_TO_MA20_STATE=IMPLEMENTED_WINDOW_GATED
RETURN_5D_STATE=IMPLEMENTED_WINDOW_GATED
RETURN_20D_STATE=IMPLEMENTED_WINDOW_GATED
VOLUME_MA5_STATE=IMPLEMENTED_WINDOW_GATED
VOLUME_MA20_STATE=IMPLEMENTED_WINDOW_GATED
VOLUME_RATIO_STATE=IMPLEMENTED_WINDOW_GATED
RSI14_STATE=IMPLEMENTED_WINDOW_GATED
MACD_STATE=IMPLEMENTED_WINDOW_GATED
MACD_SIGNAL_STATE=IMPLEMENTED_WINDOW_GATED
MACD_HISTOGRAM_STATE=IMPLEMENTED_WINDOW_GATED
```

RSI uses Wilder seed/recurrence with 0/50/100 edge semantics and no NaN.
MACD uses SMA-seeded EMA12/EMA26, EMA9 seeded from the first nine valid MACD
values, and histogram `MACD - Signal`. The accepted-session ordering blocker
does not apply because Stock-006A already supplies deterministic ordering.

## 4. Continuity and publication semantics

`evaluate_bounded_continuity` evaluates the exact
`identity × as_of_session × indicator_id × required_window`. Its executable
states are:

| State | Implementation result |
|---|---|
| `CONTINUITY_PASS_BOUNDED` | Calculation may publish `FORMAL` evidence |
| `CONTINUITY_FAIL` | Value is null with `CONTINUITY_FAIL`; publication is `UNAVAILABLE` |
| `CONTINUITY_UNKNOWN` | Value is null with `CONTINUITY_UNKNOWN`; publication is `UNAVAILABLE` |

An absent continuity-evidence envelope, incomplete coverage, scope mismatch,
material conflict, invalid event record, or unresolved in-window event cannot
pass. An empty event list without completed bounded coverage remains
`CONTINUITY_UNKNOWN`; it is never interpreted as `NO_EVENT`.

The current canonical historical reader does not yet attach a runtime
corporate-action evidence envelope. Therefore a normal production read with
the current input shape remains fail-closed and unavailable until an exact
bounded evidence envelope is supplied. This is intentional bounded authority
behavior, not a symbol-level global block.

Every formal or unavailable record binds:

```text
instrument_identity / symbol / market
indicator_id / family / policy version
session_date / as_of
required_observation_count / actual_observation_count
required_observation_window / actual_observation_window
algorithm_id / version / parameter_set
price_basis
continuity_state / continuity_evidence
source_authority / source_lineage
publication_state
value OR availability_reason
```

## 5. API and frontend boundary

The existing read-only route remains the single backend boundary:

```text
GET /api/v2/stocks/{symbol}/technical?from=...&to=...&market=...&limit=...
```

The response now carries backend-owned `technicalEvidence`, while retaining
the existing foundation provenance fields and generated API contract. No UI
component was added or changed; frontend state is:

```text
FRONTEND_WIRING_STATE=READY_FOR_FRONTEND_WIRING
READY_FOR_STOCK_TECHNICAL_FRONTEND_PUBLICATION=BOUNDED
```

The browser is not allowed to calculate MA, returns, volume, RSI, MACD, or
continuity eligibility. WS3 was not modified. MA60 is consumable by contract
only when its exact window has formal evidence:

```text
WS3_FORMAL_MA60_EVIDENCE_AVAILABLE=BOUNDED
READY_FOR_WS3_MA60_CONSUMPTION=BOUNDED
```

No BUY/SELL/HOLD, recommendation, Opportunity Grade, entry/stop/target,
win-rate, strategy acceptance, walk-forward, A1/A2/A3, Catch-up, or
performance semantics were added. Advanced Technical remains `DEFERRED`.

## 6. Validation and test attribution

The baseline was executed in the clean task worktree with a Python 3.12 venv
created outside the repository from `services/api[dev]` constraints.

```text
APPLICATION_TEST_BASELINE=474 passed, 41 skipped, 1 warning
APPLICATION_TEST_POST=483 passed, 41 skipped, 1 warning
NEW_TEST_DELTA=+9 passed
TEST_COUNT_DELTA_REASON=9 new deterministic tests in test_technical_publication.py; no test removal or discovery reduction
FOCUSED_TESTS=14 passed, 0 failed, 1 warning
BACKEND_FAILED=0
BACKEND_XFAILED=0
BACKEND_DESELECTED=0
RUFF=PASS
PYTHON_COMPILE=PASS (Python 3.12.13)
OPENAPI_DRIFT=PASS
API_CLIENT_TESTS=3 passed, 0 failed
GIT_DIFF_CHECK=PASS
SECRET_PATTERN_SCAN=PASS
```

Focused coverage includes exact MA and return windows, volume denominator
semantics, RSI seed/edge/warm-up behavior, MACD SMA seed/recurrence/signal/
histogram boundaries, accepted ordering, future-bar leakage, PASS/FAIL/
UNKNOWN continuity, empty-event fail-closed behavior, indicator-specific
windows, and formal/unavailable D4 fields.

```text
DB_VALIDATION=NOT_REQUIRED_BY_IMPLEMENTATION; PostgreSQL integration tests NOT_RUN because no test database was provided
MIGRATION_CHANGED=NO
PERSISTENCE_ADDED=NO
G1_G2_G3=NOT_RERUN_PRESERVED_CANONICAL_EVIDENCE
CANARY=NOT_RERUN_PRESERVED_CANONICAL_EVIDENCE
```

The API client package was installed from its lockfile for generation and its
three tests passed. npm reported two high-severity audit findings in the
existing dependency tree; no dependency manifest or lockfile was changed by
this task.

## 7. Exact implementation write set

| Path | Purpose |
|---|---|
| `services/api/src/topicpilot_api/technical_publication.py` | Deterministic V0 algorithms, continuity gate, evidence builder |
| `services/api/src/topicpilot_api/historical_read_model.py` | Preserve identity and accepted ordering fields for PIT evidence |
| `services/api/src/topicpilot_api/schemas.py` | Formal/unavailable Technical Evidence API models |
| `services/api/tests/test_technical_publication.py` | Nine new focused deterministic tests and foundation expectation updates |
| `packages/api-client/openapi.json` | Generated API contract |
| `packages/api-client/src/schema.d.ts` | Generated client schema |
| `apps/web/app/lib/generated-api.d.ts` | Synchronized generated web declaration; no UI behavior |
| `docs/architecture/STOCK_TECHNICAL_PUBLICATION_FOUNDATION.md` | Foundation contract updated for additive V0 implementation |
| `docs/architecture/STOCK_TECHNICAL_V0_POLICY_CONTRACT.md` | Current implementation status link; D1-D4 unchanged |
| `docs/reports/TASK-FE-BE-STOCK-006B-PHASE-2B-TECHNICAL-V0-IMPLEMENTATION.md` | This closure report |
| `reports/TASK-FE-BE-STOCK-006B-PHASE-2B-TECHNICAL-V0-IMPLEMENTATION/technical-v0-implementation-evidence.json` | Machine-readable implementation evidence |
| `docs/architecture/README.md` | Architecture navigation |
| `docs/DOCUMENTATION_INDEX.md` | Cold-start report navigation |

No WS1, WS3, WS4, Opportunity, Recommendation, roadmap, work-order register,
`NEXT_TASK`, migration, database, provider, scheduler, Production, deploy, or
release-candidate surface is in the write set.

## 8. Release and ownership state

```text
CANONICAL_STATUS=CANONICALIZED
RELEASE_STATUS=NOT_RUN
PRODUCTION_VERIFICATION=NOT_RUN
READY_FOR_RELEASE_SCOPE_CONSIDERATION=NO
RELEASE_CANDIDATE_CREATED=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
NEXT_TASK_CHANGED=NO
OWNER_STATE_PRESERVED=YES
TASK_WORKTREE_CLEANED=YES_AFTER_CLOSURE
```

Remaining bounded items are not implementation-policy blockers: the current
historical read model has no runtime continuity-evidence attachment, so actual
canonical data windows remain `UNKNOWN` until that evidence is provided; and
frontend UI wiring remains a separate bounded follow-up. No adjusted-price
engine, synthetic corporate-action adjustment, or Advanced Technical work is
authorized by this closure.

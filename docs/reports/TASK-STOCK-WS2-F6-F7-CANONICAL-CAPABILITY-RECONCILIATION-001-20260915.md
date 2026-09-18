# TASK-STOCK-WS2-F6-F7-CANONICAL-CAPABILITY-RECONCILIATION-001

Date: 2026-09-15 (Asia/Taipei)

## Closeout fields

TASK: `TASK-STOCK-WS2-F6-F7-CANONICAL-CAPABILITY-RECONCILIATION-001`

ROLE: `Stock / WS2 Capability Reconciliation Owner`

MODE: `ONE_SHOT_HISTORICAL_TO_CANONICAL_CAPABILITY_RECONCILIATION`

RESULT: `COMPLETE`

STOP_REASON: `NONE — bounded Stock/WS2 reconciliation completed; release remains separately operator-gated.`

CURRENT_GOVERNED_BASE_SHA: `b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40` (repository baseline recorded by current project state)

TASK_EXECUTION_BASE_SHA: `1f9dc51409626c1bfc439f974668f5ec85802eb1` (isolated E worktree start; retained F1-F9 recovery provenance)

HISTORICAL_F4_F9_AGGREGATE_SHA: `1501468da8b7b4d8338ae1c2da23996126ee918c`

F6_HISTORICAL_EVIDENCE: `docs/reports/TASK-FE-F6-STOCK-FORMAL-READ-VIEW-UNIFICATION-20260909/formal-closure-report.md`, reachable in the aggregate snapshot only.

F7_HISTORICAL_EVIDENCE: `docs/reports/TASK-FE-F7-STOCK-FORMAL-TECHNICAL-EVIDENCE-CONSUMER-20260909/formal-closure-report.md`, reachable in the aggregate snapshot only.

The aggregate SHA is historical evidence, not an individual F6 or F7 implementation SHA. Individual F6/F7 commit identities were not recoverable and were not invented. Historical labels are provenance only; the historical tasks were not reopened and the aggregate was not cherry-picked.

## Current canonical discovery

The current canonical architecture was inspected before using historical code. Stock already had a formal V2 read route, formal EOD projection, canonical daily-bar history route, topic-relation projection, Explorer, Drawer, and a generated Technical route. Technical V0 already had a formal backend publication policy and provider. The discovered gaps were semantic consumer gaps, not a missing historical branch:

- `services/api/src/topicpilot_api/production_read_model.py` had a symbol-only detail helper that selected the first matching market.
- `apps/web/app/lib/stock-api.ts` called that symbol-only detail route and had no formal Technical V0 consumer.
- `StockEncyclopediaDrawer.tsx` could show caller/tile values while formal detail was loading or unavailable and displayed the legacy boolean/MA technical shape.
- `apps/web/app/stocks/[code]/page.tsx` was a separate snapshot/trigger view rather than the shared formal Stock view.
- The Explorer used code-only ordering/keys and presented the first topic relation as a topic label.

Canonical provider/schema/generated classifications:

| Surface | Classification at discovery | Current authority |
|---|---|---|
| Stock identity/EOD/read | `FORMAL_BUT_PARTIAL` | `production_read_model.py` and V2 read route |
| Raw history | `FORMAL_CANONICAL` | `historical_read_model.py` / price-history route |
| Topic relations | `FORMAL_CANONICAL` but publication-gated | canonical relation rows; no inferred main topic |
| Legacy `technicalEvidence` on StockReadModel | `LEGACY_COMPATIBILITY` | retained schema shape, not F7 authority |
| Technical V0 provider/policy | `FORMAL_CANONICAL` | `technical_publication.py`, current generated route |
| Historical F6/F7 frontend implementation | `SHADOW` / provenance | aggregate snapshot only |
| Snapshot/trigger detail | `OBSOLETE` for formal V2 Stock detail | excluded from formal consumer |

## Semantic diff and dispositions

Allowed dispositions used below are the governed vocabulary: `KEEP_CURRENT`, `MERGE_CAPABILITY`, `SUPERSEDE_HISTORICAL`, `DROP_HISTORICAL`, `IMPLEMENT_MISSING`, `WAIT_EXTERNAL_AUTHORITY`, and `OWNER_DECISION_REQUIRED`.

| CAPABILITY | HISTORICAL_F6_F7 | CURRENT_CANONICAL | SEMANTIC_EQUIVALENCE | AUTHORITY | GAP | DISPOSITION | TARGET_OWNER |
|---|---|---|---|---|---|---|---|
| F6 exact `(market, instrument_code)` identity | Required; ambiguous code must not guess | List projection was market-aware, but detail helper was first-match | Not equivalent before reconciliation; current formal provider is authoritative | Stock V2 | Ambiguous symbol-only detail | `MERGE_CAPABILITY` + `IMPLEMENT_MISSING` | Stock / WS2 |
| F6 formal EOD | EOD source, status, observation/retrieval metadata | Already formal and nullable | Equivalent; preserve current fields | Stock V2 | None in reconciled UI | `KEEP_CURRENT` | Stock / WS2 |
| F6 raw history | Raw canonical daily bars, bounded and identity-bound | Already served by shared historical read model | Equivalent after returned identity validation | Historical read model | None | `KEEP_CURRENT` | Stock / WS2 |
| F6 Explorer/Drawer/detail parity | Shared formal view and no legacy/snapshot first paint | Explorer/Drawer existed; standalone detail was legacy | Not equivalent before reconciliation | Stock V2 | Shared formal view and safe loading boundary | `MERGE_CAPABILITY` + `IMPLEMENT_MISSING` | Stock / WS2 |
| F6 topic relation/main-topic behavior | Relations shown; no guessed main topic | Relations formal; main topic may be null | Equivalent after removing first-relation presentation as authority | Topic read contract | B2 publication can gate main topic | `KEEP_CURRENT` + `WAIT_EXTERNAL_AUTHORITY` for gated subfield | Stock / Topic read contract |
| F7 fixed 14-ID output | Exact 14 indicators | Current policy supports the same 14 IDs | Equivalent | WS2 Technical V0 provider | Consumer absent | `MERGE_CAPABILITY` + `IMPLEMENT_MISSING` | WS2 / Stock Technical |
| F7 source/as-of/status/partial semantics | Backend-only formal evidence, explicit unavailable/partial | Current provider publishes these fields | Equivalent after consumer validation | Technical V0 provider | Frontend did not consume it | `MERGE_CAPABILITY` | WS2 / Stock Technical |
| F7 recommendations/selectors/new indicators | Explicitly forbidden | Not part of current provider/consumer | Historical and current boundary agree | Governance | None | `DROP_HISTORICAL` + `SUPERSEDE_HISTORICAL` | WS2 / Governance |

Porting historical code wholesale would have retained its old assumptions and crossed the current collision boundary. Only the bounded semantics above were merged.

## F6 canonical reconciliation

F6_CURRENT_CANONICAL_DISCOVERY: `FORMAL_BUT_PARTIAL` at task start; now reconciled across formal Stock list, detail, Explorer, Drawer, standalone detail, EOD, history, and relations.

F6_SEMANTIC_EQUIVALENCE: `RECONCILED` for exact identity, formal EOD, raw history, source/as-of/freshness, relation display, and shared view behavior. Main-topic publication remains fail-closed and is never inferred.

F6_DISPOSITION: `MERGE_CAPABILITY + IMPLEMENT_MISSING + SUPERSEDE_HISTORICAL`.

F6_CANONICAL_CAPABILITY: `RECONCILED`.

STOCK_FORMAL_IDENTITY: `READY` for supported formal surfaces. `fetchFormalStock` resolves exactly one result through the formal list with optional market; the backend symbol-only route now returns a 409 `Ambiguous instrument` problem for multiple market matches instead of selecting the first row. Explorer keys/order and selected state use `(market, code)`.

STOCK_FORMAL_EOD: `READY`. EOD remains backend-owned, nullable, status-bearing, source-lineage-bearing, and separate from intraday display values.

STOCK_RAW_HISTORY: `READY`. The shared bounded daily-bar consumer validates returned code/market identity, preserves raw observed values and adjustment `UNKNOWN`, and does not substitute snapshot or recomputed values.

STOCK_TOPIC_RELATIONS: `READY_WITH_B2_READ_CONTRACT`. Published relation rows remain backend-owned; missing or unpublished main topic stays null and the Explorer does not promote the first relation to main topic. No B2 policy was changed.

STOCK_SOURCE_ASOF_FRESHNESS: `READY`. Drawer/detail renders formal EOD source, observed/retrieved timestamps, trading date, freshness, status, and raw-history as-of metadata. During formal loading/error/empty states caller/tile values are suppressed.

## F7 / Technical V0 reconciliation

F7_CURRENT_CANONICAL_DISCOVERY: `FORMAL_CANONICAL_PROVIDER + MISSING_CONSUMER` at task start. The backend route and schemas already existed; the Stock frontend was not consuming the formal route.

F7_TECHNICAL_POLICY: `stock-technical-publication.v3` contract, `stock-technical-v0-policy.v4`, raw observed daily-bar input, `RAW_OBSERVED` price basis, backend-only calculation, known-event-aware bounded continuity, and exactly:

`MA5`, `MA10`, `MA20`, `MA60`, `DISTANCE_TO_MA20`, `RAW_CLOSE_RETURN_5D`, `RAW_CLOSE_RETURN_20D`, `VOLUME_MA5`, `VOLUME_MA20`, `VOLUME_RATIO_20`, `RSI14`, `MACD_12_26_9`, `MACD_SIGNAL_12_26_9`, `MACD_HISTOGRAM_12_26_9`.

F7_SEMANTIC_EQUIVALENCE: `RECONCILED`. The frontend now requests Technical V0 only after formal Stock detail is published and has an explicit market plus EOD trading date. It validates code, market, requested date, backend calculation ownership, browser calculation prohibition, source authority, and each evidence identity. It selects only the backend-published latest session for display and does no indicator arithmetic.

F7_DISPOSITION: `MERGE_CAPABILITY + IMPLEMENT_MISSING + SUPERSEDE_HISTORICAL`.

F7_CANONICAL_CAPABILITY: `RECONCILED`.

TECHNICAL_V0_PROVIDER: `READY`. Provider paths are `technical_publication.py`, `technical_v0_evidence_contract.py`, and the formal `/api/v2/stocks/{symbol}/technical` route.

TECHNICAL_V0_CONSUMER: `READY`. `stock-api.ts` provides typed request/state handling; the shared Drawer renders the formal Technical V0 panel; the standalone detail route uses the same shared view; Explorer does not add ranking or selector logic.

TECHNICAL_INDICATOR_POLICY: `EXACT_CURRENT_14_ID_POLICY`; no Liquidity Sweep, Order Flow, Anchored VWAP, Volume Profile, institutional flow, recommendation, selector, or future indicator family was introduced.

TECHNICAL_SOURCE_ASOF_STATUS: `READY_WITH_EXPLICIT_STATES`. Source authority, raw-series semantics, as-of, requested/actual session, publication, eligibility, event authority, partial, empty, unavailable, and transport error states are preserved. Transport errors can retry; semantic unavailable states do not masquerade as retryable data.

## Shared contract and dependency reconciliation

SHARED_CONTRACT_RECONCILIATION: `NO_SHARED_CONTRACT_CHANGE_REQUIRED`. Existing schema/OpenAPI/generated declarations already represented the current provider and route. The implementation stayed within Stock/WS2 consumer/read-model paths; generated files were not manually edited.

OPENAPI_DRIFT: `PASS` (`check_openapi_drift.py --app topicpilot_api.main:app`).

GENERATED_CLIENT_DRIFT: `PASS` (`npm run check --prefix packages/api-client`, generation and diff clean).

B2_DEPENDENCY: `READ_CONTRACT_ONLY`. No Topic/B2 policy or authority was modified. Main-topic values remain null when not published.

A10_A9_DEPENDENCY: `NONE`.

TODAY_DEPENDENCY: `NONE`.

FUND001_OVERLAP: `NONE`; institutional-flow and future capability boundaries remain untouched.

## Implementation, governance, and report identities

IMPLEMENTATION_SHA: `a47a693e407b012243493b585d6a165cd66e7cea`, `f5153cf2d65f7b5deb1a3ffa891340e02429e5f8`.

GOVERNANCE_SHA: `16a00d44a4ce73d655908b7f1639e849b49b5f03` (task registration; final report commit identity is emitted at closeout).

REPORT_SHA: `RESOLVED_AT_CLOSEOUT; final report commit identity is emitted in the final response`.

Machine-readable provenance: `docs/reports/TASK-STOCK-WS2-F6-F7-CANONICAL-CAPABILITY-RECONCILIATION-001-20260915/provenance.json`.

## Validation

FOCUSED_TESTS: `PASS` — web Stock/Technical focused set `44 passed`; backend Stock EOD + Technical V0 set `40 passed`; API client `3 passed`.

WEB_TESTS: `PASS` — `npm test --prefix apps/web`: production build succeeded and `162 passed, 0 failed`.

BACKEND_TESTS: `PASS` for the focused set; broader suite: `599 passed, 6 known baseline failures, 41 skipped` under Python 3.12 with repo-root and API `src` paths configured.

TASK_CAUSED_FAILURES: `0`.

KNOWN_BASELINE_FAILURES:

1. Python 3.10 cannot collect existing tests importing `datetime.UTC`; Python 3.12 is the compatible runtime and all focused tests pass there.
2. Existing TypeScript error at `apps/web/app/components/v2/TopicDetailPage.tsx:191` is outside this task's modified surface.
3. Broader backend `test_canonical_revision_is_linear_after_0018` is the registered A9/B2 migration-head baseline mismatch, outside WS2.
4. Five WS3 confirmatory-validation tests require absent WS3 research report artifacts; they are other-workstream fixtures and were not modified.
5. PostgreSQL integration tests were skipped because no test database URL was provided; no database mutation was attempted.

UNKNOWN_FAILURES: `0`. All observed non-passing checks were classified as environment, registered baseline, other-workstream artifact, or intentionally unavailable external integration.

PROJECT_MEMORY_RECOVERY_TEST: `PASS`. The task, report, manifest, and provenance are searchable by Stock formal read, WS2 Technical V0, F6, F7, and `1501468`; registration is recoverable from the governed task manifest.

INTEGRATION_GATE: `READY` — manifest is `READY_FOR_INTEGRATION`, implementation commits exist, ownership is bounded, no shared conflict was introduced, and no owner decision is required.

READY_FOR_INTEGRATION: `YES`.

PRODUCTION_READY: `NO` — current project state remains `BLOCKED_OPERATOR_READBACK`; this task performed no Production, credential, deploy, or operator mutation.

OWNER_DECISION_REQUIRED: `NO` for this bounded reconciliation.

INTEGRATION_OWNER_ACTION_REQUIRED: `NO` for the current diff; normal integration/release-owner handoff remains required before canonical mainline or release movement.

C_DRIVE: `READ ONLY; unchanged`.

PRODUCTION: `NOT TOUCHED`.

MIGRATION: `NONE; migration 0040 not touched`.

PUSH: `NOT PERFORMED`.

NEXT_GOVERNED_ACTION: `Integration Owner may review the two implementation commits and integrate them through GOV-003; then the separate operator-readback release gate may be evaluated. Do not treat this task as Production release.`

## Explicit capability conclusion

F6 HISTORICAL CAPABILITY: `MERGED / SUPERSEDED`.

F7 HISTORICAL CAPABILITY: `MERGED / SUPERSEDED`.

STOCK FORMAL READ: `RECONCILED; READY_FOR_INTEGRATION`.

WS2 TECHNICAL V0 CONSUMER: `RECONCILED; READY_FOR_INTEGRATION`.

F6/F7 HISTORICAL TASK IDENTITIES: `PROVENANCE ONLY`.

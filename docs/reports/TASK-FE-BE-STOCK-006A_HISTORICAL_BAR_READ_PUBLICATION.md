# TASK-FE-BE-STOCK-006A Historical Bar Read Publication

## Executive Decision

```text
TASK_ID=TASK-FE-BE-STOCK-006A-HISTORICAL-BAR-READ-PUBLICATION
FINAL_STATUS=COMPLETE
TASK_MODE=BOUNDED_READ_PUBLICATION_IMPLEMENTATION
RETRY_REASON=HIST_002B_CANONICAL_PERSISTENCE_AUTHORITY_WAS_PROMOTED_AND_RUNTIME_VERIFIED
CANONICAL_PRE_SHA=f89129a310de7b600aaba6e4bf8535ff518c2df0
IMPLEMENTATION_COMMIT_SHA=1a340860ec9f2ef7cc7019fd0ef5037809b0228e
CANONICAL_POST_SHA=1a340860ec9f2ef7cc7019fd0ef5037809b0228e
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
WORKTREE_CREATED=NO

RAW_HISTORICAL_BAR_PUBLICATION_READY=YES
HISTORICAL_READ_MODEL_EXISTS=YES
HISTORICAL_API_CONTRACT_STATE=FORMAL_BOUNDED_V2_SUBRESOURCE
V1_V2_SHARED_HISTORY_AUTHORITY=YES
RAW_BAR_ADJUSTMENT_DISCLOSURE=RAW_OBSERVED_ADJUSTMENT_UNKNOWN
BASIC_TECHNICAL_PUBLICATION_READY=NO
PRICE_CONTINUITY_INDICATORS_STATE=DEFERRED_CORPORATE_ACTION_POLICY
VOLUME_CONTINUITY_INDICATORS_STATE=DEFERRED_CORPORATE_ACTION_POLICY
ADVANCED_TECHNICAL_STATE=DEFERRED_SEPARATE_FORMAL_ALGORITHMS
EVENT_TIMELINE_PUBLICATION_READY=NO
PRICE_HISTORY_TIMELINE_READY=YES
CORPORATE_ACTION_MARKERS_STATE=DEFERRED_EVENT_AUTHORITY
INSTITUTION_CHIP_STATE=UNAVAILABLE
NARRATIVE_STATE=UNAVAILABLE
OPPORTUNITY_STATE=UNAVAILABLE
RECOMMENDATION_STATE=UNAVAILABLE
BROWSER_TECHNICAL_CALCULATION_ALLOWED=NO

STOCK_005C_BASELINE_CONFIRMED=YES
HIST_002B_BASELINE_CONFIRMED=YES
APPLICATION_CODE_CHANGED=YES
DATABASE_MUTATION=NO
HISTORICAL_DATA_CHANGED=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
DAILY_PROGRESS_UPDATED=NO
G1= PRESERVED PASS
G2= PRESERVED PASS
G3= PRESERVED PASS
POST_CLOSE_CANARY= PRESERVED PASS
```

The retry is closed by publishing a single read-only backend authority over
the promoted canonical observation chain. V1 compatibility and the new V2
bounded subresource call the same read model. The retained
`topicpilot.market_data_ohlcv` relation is not used as a fallback.

This task publishes raw observed daily bars only. It does not publish adjusted
prices, total returns, indicators, corporate-action markers, event timeline
items, chip data, narrative, opportunity, or recommendation semantics.

Frontend history rendering was deliberately not wired in this task because
`StockEncyclopediaDrawer` is shared by the active Topic Detail workstream.
Changing that shared component would create a collision. The existing Stock
technical/timeline placeholders therefore remain explicit unavailable or
not-wired states; no mock data was promoted.

## Canonical State and Retry Predecessor

The canonical repository was used directly:

```text
CANONICAL_REPO=C:\Users\acer\Desktop\題材領航\topicpilot-platform
CURRENT_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
CANONICAL_PRE_SHA=f89129a310de7b600aaba6e4bf8535ff518c2df0
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
WORKTREE_CREATED=NO
```

The prior blocked 006A attempt is not current authority. Its local runtime
observation was superseded by the accepted promotion work:

```text
HIST_002B_PROMOTION_COMMIT=d9c7787
HIST_002B_PROMOTION_REPORT_COMMIT=f89129a
HISTORICAL_PERSISTENCE_RECONCILIATION_COMMIT=6831cf3
```

The promotion report and runtime were reconciled before implementation. The
runtime database now reports:

```text
DATABASE_ALEMBIC_VERSION=0029_task_data_ref_006e_instrument_lifecycle
CANONICAL_OBSERVATIONS=EXISTS
CANONICAL_PRICE_OBSERVATIONS=EXISTS
CANONICAL_VOLUME_OBSERVATIONS=EXISTS
CANONICAL_TRADING_STATUS_OBSERVATIONS=EXISTS
LEGACY_MARKET_DATA_OHLCV=RETAINED_EVIDENCE_ONLY
```

The worktree already contained unrelated dirty changes from concurrent
workstreams. They were preserved; no reset, stash, clean, blanket stage, or
old isolated worktree reuse was performed.

## 005B / 005C Baseline

The accepted Stock 005B/005C baseline remains intact:

- formal EOD is backend/API projected and wired through Explorer and Drawer;
- EOD nulls fail closed;
- API error does not fall back to Preview;
- the browser does not calculate change, changePct, turnover, provider, or
  business semantics;
- Drawer push animation, header offset, sticky/full-height body, internal
  scroll, Escape handling, stale-request protection, and topic filtering were
  not changed by this task.

The new history route is additive and bounded. It does not alter the existing
EOD contract.

## HIST-002B Authority Verification

The selected publication authority is:

```text
topicpilot.canonical_observations
topicpilot.canonical_price_observations
topicpilot.canonical_volume_observations
topicpilot.canonical_trading_status_observations
topicpilot.instruments
topicpilot.markets
topicpilot.market_data_sources
topicpilot.reference_instrument_lifecycles
```

The read model selects accepted, non-superseded `PRICE` observations with
`DAILY_BAR` source semantics. Volume is paired through the same instrument,
source, and `timeline_entry_id`, and is accepted `DAILY_TOTAL` only. No
provider is called and no row is written.

Runtime control results:

| Control | Result |
|---|---:|
| Approved instruments | 507 |
| Accepted canonical PRICE rows | 63,826 |
| Accepted canonical VOLUME rows | 63,826 |
| Accepted canonical TRADING_STATUS rows | 0 |
| Canonical date range | 2026-02-02..2026-08-13 |
| Accepted price rows with null OHLC | 0 |
| Accepted volume rows with null volume | 0 |
| Non-daily volume rows in selected chain | 0 |
| TPE instruments / rows | 314 / 39,523 |
| TWO instruments / rows | 193 / 24,303 |

| Symbol control | Expected | Observed |
|---|---:|---:|
| TPE:2330 rows | 126 | 126 |
| TWO:6488 rows | 126 | 126 |
| TPE:6806 rows before lifecycle cutoff | 88 | 88 |
| TPE:6806 last bar | 2026-06-22 | 2026-06-22 |
| TPE:6806 bars on/after 2026-06-23 | 0 | 0 |
| Unauthorized TPE:3059 rows | 0 | 0 |

The 6806 lifecycle row is `DELISTED`, effective from 2026-06-23, with
evidence `TWSE-DELISTED-6806-20260623`. The query enforces this date-effective
cutoff rather than inferring lifecycle from OHLCV.

## Stock Detail Current UI / API Inventory

Before this task, the V2 stock aggregate was formal for identity, relations,
tracking, and EOD, while historical bars had no V2 formal subresource. The
current UI contains:

| Surface | Current state | Publication decision |
|---|---|---|
| Stock Explorer identity/EOD | FORMAL | Preserved |
| Drawer EOD | FORMAL / fail-closed | Preserved |
| Technical Detail | FORMAL_NOT_WIRED or UNAVAILABLE placeholders | Not promoted |
| Timeline/history block | No independent formal event timeline | Not promoted |
| Institution/chip | UNAVAILABLE | Deferred |
| Narrative | UNAVAILABLE | Deferred |
| Opportunity | UNAVAILABLE | Deferred |
| Recommendation | UNAVAILABLE | Deferred |

The backend now exposes the formal historical contract, but no shared Drawer
component was changed. This is intentional collision control with Topic Detail
and prevents a partially wired surface from looking formal.

## STOCK_DETAIL_FIELD_PUBLICATION_MATRIX

`CURRENT_UI_STATE` and `FORMALITY_STATE` below describe the state after this
task. `SAFE_TO_PUBLISH_NOW` is about a formal publication contract, not about
whether a field could be computed in an experiment.

| Field | CURRENT_UI_STATE | CURRENT_API_FIELD | SOURCE_OF_TRUTH / BACKEND_DERIVATION_REQUIRED | HISTORICAL / CORPORATE-ACTION / PIT DEPENDENCY | FORMALITY_STATE | SAFE_TO_PUBLISH_NOW / BLOCKER / RECOMMENDED_OWNER |
|---|---|---|---|---|---|---|
| historical `date` | not rendered by Drawer | `HistoricalPricePoint.tradingDate` | canonical observed_at converted using `markets.timezone`; backend read only | bar identity / event disclosure / no PIT dependency | FORMAL | YES / none / STOCK-006A |
| historical `open/high/low/close` | EOD only; history not yet rendered | `HistoricalPricePoint.open/high/low/close` | canonical price observations | raw bars ready / adjustment remains unknown / no PIT dependency | FORMAL | YES as raw observed / no adjusted meaning / STOCK-006A |
| historical `volume` | EOD only; history not yet rendered | `HistoricalPricePoint.volume` plus unit/scale/aggregation | canonical volume observations paired by timeline entry | volume comparability across corporate actions remains unknown / no PIT dependency | FORMAL_RAW | YES with unit and disclosure / no normalized comparability / STOCK-006A |
| historical `source/freshness/lineage` | not rendered | source object, observed/retrieved/asOf, version fields | market data source and canonical metadata | lineage is formal / freshness is as-of, not currentness | FORMAL | YES / no source URL column in selected authority / STOCK-006A |
| MA5 | placeholder/unavailable | none | deterministic backend projection required | price continuity and sufficient lookback / event policy / PIT if used for research | DEFERRED | NO / corporate-action policy and contract absent / STOCK-006B |
| MA10 | placeholder/unavailable | none | deterministic backend projection required | same as MA5 | DEFERRED | NO / same blocker / STOCK-006B |
| MA20 | existing evidence shape but not historical publication | `technicalEvidence.ma20` is not a history contract | research/read-model algorithm must be owned by backend | price continuity, lookback, parameter version, PIT/no-look-ahead | FORMAL_NOT_WIRED | NO / no approved production indicator contract / STOCK-006B |
| MA60 | tracking evidence exists but not history publication | `technicalEvidence.ma60` / live tracking evidence | existing tracking field is not a historical series contract | price continuity, 60 observations, corporate-action policy, PIT | FORMAL_NOT_WIRED | NO / do not reuse tracking as chart history / STOCK-006B |
| volume average | unavailable | none | deterministic backend projection required | volume continuity and lookback / event policy / PIT | DEFERRED | NO / volume comparability policy absent / STOCK-006B |
| volume ratio | unavailable | none | deterministic backend projection required | volume continuity and denominator semantics / PIT | DEFERRED | NO / no production contract / STOCK-006B |
| distance-to-MA | unavailable | none | deterministic backend projection required | price continuity, MA policy, return-like interpretation risk / PIT | DEFERRED | NO / no approved algorithm / STOCK-006B |
| 20-day high / resistance distance | unavailable | none | deterministic backend projection required | lookback and corporate-action continuity / PIT | DEFERRED | NO / no production contract / STOCK-006B |
| momentum / returns | unavailable | none | deterministic backend projection required | return semantics and adjustment policy / PIT | DEFERRED | NO / adjusted/total-return ambiguity / REC-A1 plus STOCK-006B |
| ATR / volatility | unavailable | none | deterministic backend projection required | price continuity, range semantics, lookback / PIT | DEFERRED | NO / corporate-action contamination risk / STOCK-006B |
| Liquidity Sweep | unavailable | none | separate formal detector and evidence source required | price/volume continuity, event policy, PIT | DEFERRED | NO / no formal algorithm/source / technical research owner |
| Order Flow | unavailable | none | intraday/order-flow source required | intraday and PIT dependency | UNAVAILABLE | NO / intraday explicitly out of scope / live-data owner |
| Anchored VWAP | unavailable | none | anchor event and deterministic backend projection required | event authority, volume continuity, PIT | DEFERRED | NO / anchor policy absent / technical research owner |
| Volume Profile | unavailable | none | intraday or session aggregation algorithm required | volume continuity and session semantics | UNAVAILABLE | NO / source and algorithm absent / technical research owner |
| FVG | unavailable | none | formal pattern algorithm required | price continuity, lookback, PIT | DEFERRED | NO / no approved detector / technical research owner |
| MACD | unavailable | none | deterministic backend factor required | price continuity, parameter/version/PIT | DEFERRED | NO / no approved contract / STOCK-006B |
| RSI | unavailable | none | deterministic backend factor required | price continuity and return semantics/PIT | DEFERRED | NO / no approved contract / STOCK-006B |
| Fibonacci | unavailable | none | anchor and swing algorithm required | event/anchor and PIT | DEFERRED | NO / no approved contract / technical research owner |
| chart patterns | unavailable | none | formal detector and evidence required | price continuity, lookahead, PIT | DEFERRED | NO / no approved detector / technical research owner |
| `PRICE_HISTORY_TIMELINE` bars | no formal Drawer block added | V2 price-history subresource | canonical daily bars | raw bar ready / corporate-action markers separate / no PIT for observed bars | FORMAL | YES / UI wiring collision deferred / STOCK-006A |
| daily bars | no independent UI | same bounded bar contract | canonical daily `PRICE` + `VOLUME` | market-local session semantics / adjustment unknown | FORMAL | YES / no intraday / STOCK-006A |
| technical events | unavailable | none | separate event/detector authority | indicator and PIT dependencies | DEFERRED | NO / no formal event source / STOCK-006B |
| corporate-action markers | unavailable | none | Corporate Action event authority | mandatory A dependency | DEFERRED | NO / event authority owned elsewhere / Corporate Action closure |
| topic/history events | unavailable | none | Topic history authority | topic lifecycle/PIT | UNAVAILABLE | NO / Topic workstream collision / Topic Detail owner |
| news events | unavailable | none | formal news authority | event timestamp/PIT | UNAVAILABLE | NO / News/Narrative prohibited here / news owner |
| institution/chip fields | unavailable | `institutionFlows` remains null | provider-owned institution/chip dataset | historical provider and PIT | UNAVAILABLE | NO / no collector/source contract / institution owner |
| market/topic narrative | unavailable | `summary` remains null | approved narrative source/model | PIT and source governance | UNAVAILABLE | NO / narrative prohibited here / Today/Topic owners |
| Opportunity fields | unavailable | `opportunity` remains null | opportunity read model | PIT/policy | UNAVAILABLE | NO / recommendation boundary / opportunity owner |
| Recommendation fields | unavailable | none | approved recommendation policy | PIT, adjustment, narrative, chip and risk dependencies | UNAVAILABLE | NO / explicitly out of scope / recommendation owner |

## Historical Bar Readiness

### Canonical table and reusable path

The canonical tables directly support read-only historical bar publication.
The selected path is a new shared service module, not a new persistence
projection:

```text
canonical observations
  -> historical_read_model.read_historical_bars
      -> V1 repository projection
      -> V2 /stocks/{symbol}/price-history
```

The previous V1 repository SQL was replaced by the shared reader, establishing
V1/V2 semantic parity. The legacy `market_data_ohlcv` table is never queried.

### API contract

```text
GET /api/v2/stocks/{symbol}/price-history
required query: from, to
optional query: market, limit
limit: 1..200, default 200
date range: inclusive, market-local date
reversed range: 422; no silent swap
truncation: hasMore=true when limit+1 exists
ordering: trading_date ASC, observed_at ASC, ordering_key ASC, observation_id ASC
```

The endpoint is a bounded historical subresource. It does not overload the
stock aggregate response and does not create a parallel API for the same
history semantics.

### Bar schema and disclosure

Each bar includes date, nullable OHLCV, observedAt, retrievedAt, sourceCode,
qualityState, adjustmentState, volume unit/scale/aggregation, and the source
lineage versions:

```text
adapterVersion
normalizationContractVersion
mappingPolicyVersion
referenceDataVersion
```

The publication boundary forces `adjustmentState=UNKNOWN`. It is therefore
raw observed data with explicit adjustment uncertainty. No adjusted-price,
total-return, performance, or technical calculation is performed.

`asOf` is the latest returned retrieved timestamp and `freshnessState` is
`AS_OF_LATEST_RETRIEVED`; this is an as-of disclosure, not a claim that the
historical series is current.

### Time, bounds, nulls, and lifecycle

- `tradingDate` is derived in the market's configured timezone; the current
  TPE/TWO runtime timezone is Asia/Taipei.
- The API returns at most 200 bars. A broad date range remains explicit and
  bounded by the query limit; it is not silently date-truncated.
- Empty accepted canonical history returns `status=UNAVAILABLE`,
  `coverageState=EMPTY`, an explicit reason, and an empty item list.
- Null OHLCV remains null. No zero, latest-row, provider, or Preview fallback
  is allowed.
- There are currently no accepted trading-status observations, so the reader
  does not infer `OPEN`, `NO_TRADE`, or `SUSPENDED` from OHLCV.
- Date-effective lifecycle authority excludes bars on or after the effective
  `DELISTED`, `SUSPENDED`, or `TERMINATED` date. New-listing or insufficient
  history naturally returns fewer bars; it does not pad or extrapolate.

## Corporate Action Dependency Matrix

| Category | Publication rule in 006A | Current decision |
|---|---|---|
| A. `RAW_HISTORICAL_BAR_PUBLICATION` | Publish canonical raw observed bars only when source, identity, date, quality, and lineage are accepted; disclose adjustment unknown | READY; this is the delivered slice |
| B. `PRICE_CONTINUITY_DEPENDENT_INDICATOR` | MA, momentum, breakout distance, ATR and other cross-event fields require an approved continuity/adjustment policy | BLOCKED/DEFERRED; no indicator publication |
| C. `VOLUME_CONTINUITY_DEPENDENT_INDICATOR` | Volume averages/ratios require split/reduction comparability policy and unit semantics | BLOCKED/DEFERRED; raw volume only |
| D. `EVENT_MARKER_REQUIRED` | Chart markers require the independent corporate-action event authority | DEFERRED; no markers added |
| E. `RETURN_SEMANTICS` | Performance/return-like fields cannot imply adjusted or total-return meaning | DEFERRED; no return fields added |

The raw bar decision is not a declaration that all technical fields are
formal. The Corporate Action authority workstream remains the owner of event
source, event schema, and event policy; no files or dataset ownership from it
were changed.

## Technical Indicator Ownership and Versioning

No new indicator is published. If a future technical slice is approved, its
deterministic implementation must be backend/research/provider-owned and must
define, at minimum:

- parameter and algorithm version;
- lookback and minimum-history rule;
- insufficient-history/null semantics;
- rounding and numeric precision;
- market/session and volume-unit semantics;
- as-of and no-look-ahead rule;
- corporate-action continuity policy;
- source/lineage disclosure.

Research artifacts such as `daily_candidates` or REC-A1 harness fields may be
used as algorithm evidence, but are not production publication contracts and
were not reused as API fields here.

## TECHNICAL_PUBLICATION_TIERS

| Tier | Definition | Current state |
|---|---|---|
| Tier 0 | Raw canonical historical bars with source, lineage, as-of, and adjustment-unknown disclosure | FORMAL / READY |
| Tier 1 | Corporate-action-insensitive or safely bounded backend-derived fields | NOT APPROVED; no current field met the full policy evidence bar |
| Tier 2 | Continuity indicators requiring corporate-action/event-aware policy | DEFERRED |
| Tier 3 | Advanced technical models requiring separate formal algorithms or data | DEFERRED |

## Timeline Split and Roadmap Recommendation

`PRICE_HISTORY_TIMELINE` is now ready as the bounded canonical OHLCV bar
subresource. It can later feed a technical chart without making the browser
the business-logic owner.

`EVENT_TIMELINE` is not ready. Corporate action, news, topic/history, system,
and chip events have different authorities and cannot be inferred from price
bar readiness.

The original order of Technical Detail before Timeline/history remains
reasonable at the capability level, but execution should be split as:

```text
STOCK-006A Historical Bar Read Publication       DONE
    -> STOCK-006B Basic Technical Projection     only after indicator policy
    -> STOCK-007 Event Timeline                  after event authorities close
```

This is a recommendation only. `NEXT_TASK` and roadmap owner documents were
not changed by this task.

## Frontend Formal-State Mapping and Collision Analysis

The inspected Stock Explorer/Drawer continues to map:

```text
formal stock/EOD available       -> FORMAL / AVAILABLE
formal detail request pending    -> LOADING
formal detail API failure        -> UNAVAILABLE
technical evidence absent        -> FORMAL_NOT_WIRED / UNAVAILABLE
timeline absent                  -> UNAVAILABLE
Preview source                   -> explicit Preview, never formal history
```

No fake historical bars were inserted. The Drawer interaction contract and
005C protections remain unchanged. The history UI wiring was intentionally
deferred because the Drawer is shared by Topic Detail, which is an active
parallel workstream. No Topic component, adapter, shared styling, topic
filter, or shared Drawer file was modified.

The safe future frontend boundary is:

```text
fetch bounded V2 bars with exact backend-provided from/to
  -> explicit Loading / Available / Empty / Unavailable / Error state
  -> render backend values and lineage
  -> no MA/ATR/momentum/change/return/turnover calculation in React
```

## Browser Business Logic Boundary

The backend owns identity, timezone conversion, lifecycle cutoff, canonical
selection, volume pairing, ordering, limit/hasMore, as-of and adjustment
disclosure. The browser must remain render-only. It may format numbers and
display state labels, but must not derive business values or fill missing
bars.

## API, Read Model, OpenAPI, and Client Reconciliation

The following were added or updated:

- shared `historical_read_model.py`;
- V1 repository delegation to the shared reader;
- V2 `GET /api/v2/stocks/{symbol}/price-history`;
- additive historical response/source/lifecycle schemas;
- generated OpenAPI JSON and TypeScript schema/client artifacts;
- stock aggregate `historyCoverage` bounds (`availableFrom`, `availableTo`,
  `rowCount`) for a future collision-safe UI slice.

The API route is read-only and does not perform migration, import, scheduler,
provider, or production persistence work.

## Parallel Collision Analysis

| Workstream | Result |
|---|---|
| Corporate Action authority | Parallel-safe. No source files, event schema, event dataset, or policy ownership changed. Dependency is recorded only. |
| Topic Detail Research Workspace | Collision avoided. Shared Drawer and Topic components were inspected but not modified. |
| Favorites | No collision; no Favorites files changed. |
| Today source-use/index/turnover | No collision; no Today files changed. |

## Validation and Impact

Read-only runtime controls and focused tests passed:

```text
ruff focused backend files                  PASS
pytest historical/V1/V2/EOD focused         17 passed
OpenAPI schema validation                    PASS
Frontend existing EOD/Drawer focused tests  8 passed
Frontend TypeScript check                    PASS
Frontend targeted lint                       PASS
Frontend production-like build               PASS
API client tests                              3 passed
git diff --check                              PASS
```

The protected G1/G2/G3/Post-Close Canary results were preserved and not
rerun. No production database mutation, historical row edit, scheduler,
provider, deploy, or remote push occurred.

## Documentation Reconciliation

This report records the runtime promotion reconciliation and the new read
contract. `DAILY_PROGRESS.md`, `WORK_ORDERS.md`, ROADMAP, and
`PROJECT_CONTEXT.md` were not changed by this task because this is a bounded
read-publication implementation and no complete capability milestone beyond
the task was inferred.

## Final Handoff

```text
TASK_ID=TASK-FE-BE-STOCK-006A-HISTORICAL-BAR-READ-PUBLICATION
FINAL_STATUS=COMPLETE
CANONICAL_PRE_SHA=f89129a310de7b600aaba6e4bf8535ff518c2df0
CANONICAL_POST_SHA=1a340860ec9f2ef7cc7019fd0ef5037809b0228e
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
WORKTREE_CREATED=NO
STOCK_005C_BASELINE_CONFIRMED=YES
HIST_002B_BASELINE_CONFIRMED=YES
RAW_HISTORICAL_BAR_PUBLICATION_READY=YES
HISTORICAL_READ_MODEL_EXISTS=YES
HISTORICAL_API_CONTRACT_STATE=FORMAL_BOUNDED_V2_SUBRESOURCE
RAW_BAR_ADJUSTMENT_DISCLOSURE=RAW_OBSERVED_ADJUSTMENT_UNKNOWN
BASIC_TECHNICAL_PUBLICATION_READY=NO
PRICE_CONTINUITY_INDICATORS_STATE=DEFERRED_CORPORATE_ACTION_POLICY
VOLUME_CONTINUITY_INDICATORS_STATE=DEFERRED_CORPORATE_ACTION_POLICY
ADVANCED_TECHNICAL_STATE=DEFERRED_SEPARATE_FORMAL_ALGORITHMS
EVENT_TIMELINE_PUBLICATION_READY=NO
PRICE_HISTORY_TIMELINE_READY=YES
CORPORATE_ACTION_MARKERS_STATE=DEFERRED_EVENT_AUTHORITY
INSTITUTION_CHIP_STATE=UNAVAILABLE
NARRATIVE_STATE=UNAVAILABLE
OPPORTUNITY_STATE=UNAVAILABLE
RECOMMENDATION_STATE=UNAVAILABLE
BROWSER_TECHNICAL_CALCULATION_ALLOWED=NO
TECHNICAL_PUBLICATION_TIERS=Tier0_FORMAL;Tier1_NOT_APPROVED;Tier2_DEFERRED;Tier3_DEFERRED
NEXT_STOCK_EXECUTION_SLICE=STOCK-006B_BASIC_TECHNICAL_PROJECTION_AFTER_POLICY_CLOSURE
PARALLEL_SAFE_WITH_CORPORATE_ACTION_A=YES
PARALLEL_SAFE_WITH_TOPIC_DETAIL_D=YES_SHARED_FILES_UNTOUCHED
REPORT_CREATED=YES
DAILY_PROGRESS_UPDATED=NO
APPLICATION_CODE_CHANGED=YES
DATABASE_MUTATION=NO
HISTORICAL_DATA_CHANGED=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
G1/G2/G3/POST_CLOSE_CANARY=PRESERVED_PASS_NOT_RERUN
```

Stop condition is satisfied. No STOCK implementation or follow-up task is
started automatically.

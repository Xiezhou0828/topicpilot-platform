# TASK-FE-BE-STOCK-006 Technical / Historical Publication Readiness Audit

## Executive Decision

~~~
TASK_ID=TASK-FE-BE-STOCK-006-TECHNICAL-HISTORICAL-PUBLICATION-READINESS-AUDIT
TASK_NAME=Technical / Historical Publication Readiness Audit
AUDIT_MODE=READ_ONLY / AUDIT_ONLY / CONTRACT_PLANNING
FINAL_STATUS=STOCK_006_AUDIT_COMPLETE_WITH_PARTIAL_RAW_BAR_READINESS

RAW_HISTORICAL_BAR_PUBLICATION_READY=PARTIAL
HISTORICAL_READ_MODEL_EXISTS=YES_PARTIAL
HISTORICAL_API_CONTRACT_STATE=EXISTING_V1_BOUNDED_READ_PARTIAL_V2_NOT_WIRED
RAW_BAR_ADJUSTMENT_DISCLOSURE=RAW_OBSERVED_ADJUSTMENT_UNKNOWN_REQUIRED

BASIC_TECHNICAL_PUBLICATION_READY=PARTIAL
PRICE_CONTINUITY_INDICATORS_STATE=DEFERRED_PENDING_CORPORATE_ACTION_POLICY_AND_FORMAL_ALGORITHM_CONTRACT
VOLUME_CONTINUITY_INDICATORS_STATE=DEFERRED_PENDING_VOLUME_COMPARABILITY_AND_FORMAL_ALGORITHM_CONTRACT
ADVANCED_TECHNICAL_STATE=DEFERRED_NO_FORMAL_ALGORITHM_OR_SOURCE_CONTRACT

EVENT_TIMELINE_PUBLICATION_READY=NO
PRICE_HISTORY_TIMELINE_READY=PARTIAL
CORPORATE_ACTION_MARKERS_STATE=NOT_READY_PENDING_A_EVENT_AUTHORITY
INSTITUTION_CHIP_STATE=UNAVAILABLE
NARRATIVE_STATE=UNAVAILABLE_OR_DEFERRED
OPPORTUNITY_STATE=SHADOW_OR_UNAVAILABLE_NOT_PRODUCTION
RECOMMENDATION_STATE=RESEARCH_ONLY_NOT_PRODUCTION

BROWSER_TECHNICAL_CALCULATION_ALLOWED=NO
NEXT_STOCK_EXECUTION_SLICE=TASK-FE-BE-STOCK-006A-HISTORICAL-BAR-READ-PUBLICATION
ROADMAP_ORDER_RECOMMENDATION=006A_HISTORICAL_BAR -> 006B_BASIC_TECHNICAL -> 007_EVENT_TIMELINE
NEXT_TASK_CHANGED=NO
~~~

The canonical repository has enough evidence for a bounded, read-only raw
historical bar projection, but the existing formal path is a V1-compatible
history route and is not yet a complete V2 Stock Detail/Drawer publication
contract. The next smallest safe execution is therefore a historical-bar
read-publication slice that reuses one backend query/read model and makes
source, freshness, lineage, lifecycle, and adjustment disclosure explicit.

Basic technical evidence is not a single blocked/unblocked switch. A
research-only deterministic technical builder exists, and the Stock contract
contains nullable technical placeholders plus a partial 60-day tracking
projection. Neither is a formal Stock technical publication contract. MA,
momentum, breakout-distance, ATR/volatility, and volume-comparability fields
remain deferred until corporate-action/event treatment and a versioned
production algorithm contract are accepted.

The price-history timeline is a separate partial capability. An event timeline
must not be declared ready from OHLCV availability: corporate actions, news,
Topic history, system events, and institution/chip events each require their
own authority and lineage.

## Canonical State

~~~
CANONICAL_REPO=C:\Users\acer\Desktop\題材領航\topicpilot-platform
CANONICAL_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
CANONICAL_PRE_SHA=f2b0784d332917a51eb20ac5e03d9526c4434c4b
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
DIRTY_STATE=YES / 157 pre-existing modified or untracked paths observed before this report
WORKTREE_CREATED=NO
REPORT_WRITE_SET=docs/reports/TASK-FE-BE-STOCK-006_TECHNICAL_HISTORICAL_PUBLICATION_READINESS_AUDIT.md
~~~

The canonical HEAD advanced from 88a4dcc... to f2b0784... during the
read-only audit because the concurrent corporate-action report was committed.
The later HEAD is the provenance boundary for this report. At provenance
capture, refs/remotes/origin/main resolved to 26f635b95d8d88fd7ed7e43949583347f3ab5feb.

The canonical worktree contains unrelated Topic, architecture, research, and
owner-document changes. They were not reset, stashed, staged, overwritten, or
reconciled by this audit. Existing isolated worktrees were inspected as
historical/concurrent evidence only; none is current authority and none was
used for this task. In particular, the old D:/topicpilot-platform-task-repo-006a
worktree was not reused.

## 005B / 005C Baseline

The accepted Stock baseline is preserved:

- TASK-FE-BE-STOCK-005B added the nullable StockEodRead projection to the
  existing V2 Stock list/detail routes. EOD values are backend-owned, accepted
  and non-superseded canonical observations; unknown adjustment state fails
  closed for change semantics; turnover remains null unless a canonical
  turnover observation exists.
- TASK-FE-BE-STOCK-005C wires the EOD projection into the formal Explorer and
  shared Drawer. The browser formats serialized EOD values and never computes
  change, change percentage, previous close, turnover, no-trade, adjustment,
  provider, or business status.
- API errors do not fall back to Preview. Missing formal EOD remains explicit
  unavailable. Preview is visibly separate from formal data.
- The Drawer push/close/reverse animation, 72px header offset, sticky
  full-height shell, internal scroll, Escape handling, stock-switch stale
  response guard, and advanced topic filter are regression-protected.

005B/005C do not publish a historical series, technical indicator series,
Timeline, institution flow, narrative, Opportunity, or Recommendation.

## HIST-002B Authority

The canonical closure report records the approved six-month evidence:

~~~
APPROVED_PHYSICAL_IDENTITIES=507
TPE_IDENTITIES=314
TWO_IDENTITIES=193
OHLCV_ROWS=63826
DATE_FROM=2026-02-02
DATE_TO=2026-08-13
SYMBOL_6806_TERMINATION=2026-06-23
SYMBOL_6806_LAST_BAR=2026-06-22
SYMBOL_6806_POST_TERMINATION_ROWS=0
INVALID_OHLCV=0
DUPLICATE_KEYS=0
MISSING_REQUIRED_LINEAGE=0
UNEXPLAINED_GAPS=0
~~~

The closure also states that the official TWSE/TPEx providers, normalization,
lineage, checkpoint/idempotence, lifecycle, and local-only guard are
canonical. It does not establish historical Topic/System State, a complete
point-in-time universe, or an adjustment-safe return series.

### Schema/name drift that must be reconciled

The HIST-002B closure describes the local reconciled row set as
topicpilot.market_data_ohlcv, while current application code has no
market_data_ohlcv reference. The current V2 read path uses:

~~~
topicpilot.canonical_observations
topicpilot.canonical_price_observations
topicpilot.canonical_volume_observations
topicpilot.canonical_trading_status_observations
topicpilot.market_data_sources
topicpilot.instruments / topicpilot.markets
~~~

This is recorded as authority drift, not as a claim that the HIST-002B rows
are invalid. 006A must reconcile the actual database migration/schema and
the accepted 507/63,826 evidence against the current canonical observation
query before publishing a V2 history contract. No historical row was changed
by this audit.

## Stock Detail Current UI/API Inventory

### Current V2 API/read model

GET /api/v2/stocks and GET /api/v2/stocks/{symbol} return StockReadModel.
The relevant fields are:

| Field | Current meaning | Audit result |
|---|---|---|
| eod | Latest completed-session StockEodRead, nullable | Formal EOD only; not a series |
| historyCoverage | observedDays, requiredDays, tracking state, asOfDate from the live tracking projection | Coverage metadata, not a historical bar read model |
| technicalEvidence | Nullable above20MA, above60MA, ma20, ma60, breakoutState, technicalState | Formal-shaped but currently null/partial; not a published indicator contract |
| institutionFlows | Nullable open dictionary | No formal provider/read model |
| summary | Nullable string | No formal Stock narrative source |
| opportunity | Nullable open dictionary | Shadow/unavailable boundary; not production Recommendation |

The V2 Stock response contains no historical bar array, date-range
parameters, pagination cursor, series freshness, row-level source lineage, or
technical parameter/version metadata.

### Existing historical API

GET /api/v1/stocks/{code}/price-history already provides a bounded read-only
path. Its current contract requires from and to, accepts optional market and
limit (1..200), orders rows ascending by observation timestamp and ordering
key, and returns status, availabilityReason, pointCount, and items containing
date, OHLC, optional volume, source code, observed time, and quality state.

The route is useful evidence and should be reused through a shared read
service. It is not yet sufficient for V2 publication because it omits
retrieved-at, adapter/normalization/mapping/reference versions, adjustment
state, explicit timezone/session disclosure, lifecycle state, and a
source-level freshness/as-of contract. The V2 frontend does not call it.

### Current Drawer state mapping

- EOD section: formal when StockEodRead is present; null/error/Preview states
  remain explicit.
- Technical section: renders technicalEvidence if supplied; otherwise shows
  formal technical data unavailable. It does not show a chart or derive MA,
  ATR, momentum, returns, or volume ratios.
- Institution/chip section: renders only non-null backend dictionary entries;
  current formal Stock API returns null.
- Summary/narrative: renders only summary; current formal value is null.
- Opportunity CTA: enabled only when a backend Opportunity object is present;
  otherwise remains unavailable.
- No Timeline/history section is currently wired into the V2 Drawer.

The explicit Preview snapshot contains legacy/synthetic technical-shaped
values, but fromPreview marks them Preview and does not promote them to formal
Stock data.

## STOCK_DETAIL_FIELD_PUBLICATION_MATRIX

State vocabulary: FORMAL means an accepted source and publication contract;
FORMAL_NOT_WIRED means an accepted-shaped field/path exists but the intended
surface or complete semantics are not connected; PREVIEW is synthetic or
temporary; DEFERRED is intentionally downstream; UNAVAILABLE is a missing
source/read model; CONTRACT_GAP means the product meaning or API contract is
not frozen.

| Field | CURRENT_UI_STATE | CURRENT_API_FIELD | SOURCE_OF_TRUTH | BACKEND_DERIVATION_REQUIRED | HISTORICAL_DEPENDENCY | CORPORATE_ACTION_DEPENDENCY | POINT_IN_TIME_DEPENDENCY | FORMALITY_STATE | SAFE_TO_PUBLISH_NOW | BLOCKER | RECOMMENDED_OWNER/TASK |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Historical date | No chart/history section | V1 items[].tradingDate | Market-local date from canonical observation + market timezone | Yes, timezone/date anchor | Direct | Lifecycle/identity only | Date-effective identity | FORMAL_NOT_WIRED | Partial | V2 bounded contract and drift reconciliation | STOCK-006A |
| Open | EOD only; no historical series | V1 items[].open; V2 eod.open latest only | Accepted canonical PRICE detail | No beyond projection | Direct | Publish as observed; no continuity claim | Session/as-of | FORMAL_NOT_WIRED | Partial | V2 series disclosure missing | STOCK-006A |
| High | EOD only; no historical series | V1 items[].high; V2 eod.high | Accepted canonical PRICE detail | No beyond projection | Direct | Same-bar fact may show event jump | Session/as-of | FORMAL_NOT_WIRED | Partial | V2 series disclosure missing | STOCK-006A |
| Low | EOD only; no historical series | V1 items[].low; V2 eod.low | Accepted canonical PRICE detail | No beyond projection | Direct | Same-bar fact may show event jump | Session/as-of | FORMAL_NOT_WIRED | Partial | V2 series disclosure missing | STOCK-006A |
| Close | EOD only; no historical series | V1 items[].close; V2 eod.close | Accepted canonical PRICE detail | No beyond projection | Direct | RAW/ADJUSTMENT_UNKNOWN disclosure required | Session/as-of | FORMAL_NOT_WIRED | Partial | Adjustment meaning absent from V1 response | STOCK-006A + A dependency |
| Volume | EOD only; no historical series | V1 items[].volume; V2 eod.volume | Accepted canonical VOLUME DAILY_TOTAL | Join by market-local date, not only timestamp | Direct | Share-count comparability unresolved | Session/as-of | FORMAL_NOT_WIRED | Partial | V1 volume join/lineage is incomplete | STOCK-006A |
| Source | EOD lineage only | V1 sourceCode; V2 priceSource/volumeSource | market_data_sources and canonical lineage | No | Direct | Event source separate | Source as-of | FORMAL_NOT_WIRED | Partial | V1 lacks full lineage fields | STOCK-006A |
| Freshness | EOD freshness only | V1 observedAt; V2 EOD observed/retrieved | Observed/retrieved timestamps | Yes, aggregate freshness classification | Direct | Event freshness separate | Retrieval/source finality | CONTRACT_GAP | No | No historical freshness contract | STOCK-006A |
| Lineage | EOD metadata only | V1 qualityState, V2 EOD version fields | Canonical observation/source lineage | No, but serialize all fields | Direct | No CA event lineage in HIST-002B | As-of/revision | FORMAL_NOT_WIRED | Partial | V1 omits adapter/normalizer/mapping/reference/adjustment | STOCK-006A |
| MA5 | No field/section | None | No approved Stock technical source | Yes | 5 valid prior/current bars | Event can contaminate continuity | Close-of-bar as-of | CONTRACT_GAP | No | No algorithm or API field | STOCK-006B |
| MA10 | No field/section | None | No approved Stock technical source | Yes | 10 valid bars | Event can contaminate continuity | Close-of-bar as-of | CONTRACT_GAP | No | No algorithm or API field | STOCK-006B |
| MA20 | Nullable technical field; current value is null | technicalEvidence.ma20 | Research builder only, provisional policy | Yes | 20 valid bars | Continuity indicator; A policy required | Prefix through t | FORMAL_NOT_WIRED | No | Provisional research semantics and no lineage/version | STOCK-006B + A dependency |
| MA60 | Nullable field; partial tracking evidence may show value | technicalEvidence.ma60, ma60State, live tracking | Live tracking projection or research builder; not one Stock contract | Yes | 60 valid bars | Continuity indicator; A policy required | Prefix through t | FORMAL_NOT_WIRED | No | Source/algorithm ownership and semantics differ | STOCK-006B + A dependency |
| Volume average | No field/section | None | No Stock technical contract | Yes | Volume lookback | Split/share-count comparability unresolved | Prefix through t | CONTRACT_GAP | No | Volume baseline policy absent | STOCK-006B + A dependency |
| Volume ratio/trend | Filter only checks nullable technical evidence | None in formal V2 | Research-only provisional evidence pattern | Yes | Volume lookback | Volume continuity unresolved | Prefix through t | DEFERRED | No | No formal source/parameter contract | STOCK-006B |
| Distance to MA | No field/section | None | No approved algorithm | Yes | MA window | Same as price continuity | Prefix through t | CONTRACT_GAP | No | Formula, rounding, null rules absent | STOCK-006B |
| 20-day high/resistance | No field/section | None | REC-A1 research design only | Yes | Prior 20 bars excluding t | Event can manufacture breakout | Prefix through t-1 | DEFERRED | No | Research artifact not production contract | STOCK-006B / REC-A1 boundary |
| Resistance distance | No field/section | None | No approved Stock algorithm | Yes | Prior 20 bars | Event-aware policy required | Prefix through t | CONTRACT_GAP | No | No field/version/threshold contract | STOCK-006B |
| Momentum/returns | No field/section | None | No formal Stock return source | Yes | Prior closes and return window | Return semantics cannot assume adjusted/total return | Prefix through t | DEFERRED | No | RETURN_SEMANTICS unresolved | STOCK-006B + A dependency |
| ATR/volatility | No field/section | None | No formal Stock algorithm; REC-A1 design only | Yes | OHLC and prior close window | Event can create artificial range/volatility | Prefix through t | DEFERRED | No | No algorithm, version, or event policy | STOCK-006B + A dependency |
| Liquidity Sweep | No field/section | None | No formal source/algorithm | Yes | Multi-bar evidence | Event and volume semantics unresolved | Prefix through t | DEFERRED | No | Advanced model absent | STOCK-006B+ |
| Order Flow | No field/section | None | No order-flow source | Yes | Intraday/order data needed | Not resolved | PIT/intraday | DEFERRED | No | Intraday forbidden in this task | Separate future task |
| Anchored VWAP | No field/section | None | No anchor/source contract | Yes | Anchor and volume history | Event/volume continuity | Prefix and anchor as-of | CONTRACT_GAP | No | Anchor policy absent | Separate future task |
| Volume Profile | No field/section | None | No profile source/algorithm | Yes | Distribution window | Volume comparability unresolved | Prefix through t | DEFERRED | No | Algorithm and resolution absent | Separate future task |
| FVG | No field/section | None | No formal pattern algorithm | Yes | Multi-bar OHLC | Event gaps cannot be assumed technical | Prefix through t | DEFERRED | No | Pattern definition absent | Separate future task |
| MACD | No field/section | None | No formal indicator contract | Yes | EMA windows | Price continuity unresolved | Prefix through t | DEFERRED | No | Parameter/version contract absent | Separate future task |
| RSI | No field/section | None | No formal indicator contract | Yes | Return window | Return semantics unresolved | Prefix through t | DEFERRED | No | Parameter/version contract absent | Separate future task |
| Fibonacci | No field/section | None | No swing/anchor authority | Yes | Swing-point history | Event may alter swing geometry | Prefix through t | CONTRACT_GAP | No | Swing/anchor rules absent | Separate future task |
| Patterns | No field/section | None | No pattern registry | Yes | Named pattern window | Event-aware classification required | Prefix through t | DEFERRED | No | No deterministic pattern contract | Separate future task |
| Historical candles | No Timeline section | V1 price-history items only | Canonical PRICE observations | No beyond selection/serialization | Direct | Raw disclosure required | Market-local as-of | FORMAL_NOT_WIRED | Partial | V2 UI/API not wired | STOCK-006A |
| Daily bars | No Timeline section | V1 bounded items | Canonical DAILY_BAR source semantics | No | Direct | Raw disclosure required | Session/date | FORMAL_NOT_WIRED | Partial | Shared read service/version drift | STOCK-006A |
| Technical events | No section | None | No formal technical event authority | Yes | Derived event window | Event contamination must be separate | Prefix through event date | DEFERRED | No | No formal algorithm/event schema | STOCK-006B |
| Corporate-action markers | No section | None | A event authority proposal only | No; source event resolution required | Event history required | Direct dependency on A | Public-by/as-of and effective date | DEFERRED | No | Source-use and normalized event data blocked | A task |
| Topic/history events | No section | Current Topic relations only | No PIT Topic/System State history | Yes only with future authority | Historical Topic state absent | Separate from CA | Topic as-of required | UNAVAILABLE | No | Current state cannot backfill history | Topic history task |
| News events | No section | None | News/Event foundation absent | Yes, event normalization | Historical news source absent | Separate event authority | Publication-time as-of | UNAVAILABLE | No | News authority not implemented | News/Event task |
| Institution flow | Drawer shows unavailable | institutionFlows=null | No approved institution provider/read model | Yes | Historical chip series absent | Corporate-action effects may alter shares | Date/as-of required | UNAVAILABLE | No | No scraper/provider allowed | Separate institution task |
| Foreign/investment-trust/dealer fields | Drawer shows unavailable | None | No formal chip contract | Yes | Historical chip source absent | Volume/share semantics separate | Date/as-of required | UNAVAILABLE | No | No source or schema | Separate institution task |
| Chip score | Filter only checks presence | None | No formal score authority | Yes | PIT inputs absent | Not applicable until source is formal | Date/as-of required | DEFERRED | No | No approved formula/source | Separate institution task |
| Market narrative | No formal section | None | No market narrative read model | Yes | Historical market state absent | Event/news authority separate | As-of required | UNAVAILABLE | No | Today/news workstream owns adjacent contracts | Today/News task |
| Stock summary/narrative | Drawer renders nullable summary | summary=null in current V2 | No formal Stock narrative source | Possibly | Historical narrative absent | Event/news source separate | As-of required | UNAVAILABLE | No | No backend source | Separate narrative task |
| Topic narrative | Topic relation/description only where supplied | Not a Stock historical field | Topic authority; not Stock technical source | No browser derivation | Historical Topic state absent | Separate | Topic as-of required | DEFERRED | No | Do not backfill current Topic state | Topic task |
| Opportunity | CTA unavailable unless object supplied | opportunity=null; separate shadow APIs exist | Opportunity shadow read boundary | Yes, research evidence | Historical policy inputs separate | CA/price policy dependency | As-of/policy version required | DEFERRED | No | Shadow is not production publication | Opportunity task |
| Recommendation | No Stock publication | No formal Stock Recommendation field | Research-only candidate and downstream Recommendation boundary | Yes | PIT/CA/Topic dependencies | Direct dependency | As-of and policy version required | DEFERRED | No | Production Recommendation not authorized | Recommendation gate |
| Recommendation explanation | No section | None | No accepted recommendation artifact | Yes | Historical evidence absent | Policy dependency | Snapshot/version required | CONTRACT_GAP | No | Explainability contract not present | Recommendation gate |

## Historical Bar Readiness

### Can the canonical table support read-only bars?

Yes at the canonical observation-chain level, with a qualification. The
current repository.list_price_history query already:

1. resolves an active TPE/TWO identity and rejects ambiguity;
2. reads accepted PRICE observations and canonical_price_observations;
3. excludes accepted superseded observations;
4. converts observed_at to the market timezone for trading_date;
5. joins accepted volume evidence without zero filling;
6. applies explicit from, to, and limit bounds; and
7. returns an explicit unavailable status when no accepted rows exist.

The query is reusable, but the current API projection is not complete enough
for V2 technical publication. It is missing full lineage/freshness/adjustment
disclosure and does not join volume by an explicitly documented market-local
trading-date contract. 006A should make one shared historical read model the
authority for both the API and chart; it must not duplicate the query inside
React or create a second persistence family.

### Proposed 006A history contract

The preferred architecture is an additive bounded subresource associated with
the existing V2 detail route, for example:

~~~
GET /api/v2/stocks/{symbol}/price-history
~~~

It should reuse the existing V1 historical query semantics through a shared
backend read service. It should not embed an unbounded history array in
GET /api/v2/stocks/{symbol}, and it should not create an independent V2
query while leaving the V1 query with different semantics. If both versions
remain temporarily exposed, they must serialize from the same read model and
share the same focused contract tests.

Recommended bounded contract for the first slice:

| Dimension | Recommended contract |
|---|---|
| Lookback | Maximum 200 accepted DAILY_BAR rows per instrument for the first slice; no claim beyond the reconciled canonical date range. The 60-bar minimum is a technical sufficiency rule, not a permission to shorten windows. |
| Date range | Explicit inclusive market-local from/to; reject reversed dates and an unreasonably wide request before query execution. A wider cap requires index/coverage evidence. |
| Pagination | Preserve limit with a hard maximum and return pointCount plus explicit hasMore or a stable cursor; do not silently truncate. |
| Ordering | Ascending (trading_date, observed_at, ordering_key, observation_id) for chart/replay consumers. |
| Market/session | TPE/TWO, Asia/Taipei, regular market session, one current accepted bar per instrument/trading date, DAILY_BAR only. |
| Null/no-data | Missing numeric values stay null; no zero fill or carry-forward. Empty accepted range returns UNAVAILABLE with reason and empty items. |
| Freshness/as-of | Response and/or each item discloses latest observed/retrieved time, requested range, returned as-of, source finality status, and coverage state. |
| Lineage | Disclose source code, adapter version, normalization contract, mapping policy, reference-data version, quality state, and adjustment state. |
| Adjustment | Explicit RAW_OBSERVED plus ADJUSTMENT_UNKNOWN disclosure until A supplies approved semantics. Never call this adjusted or total return. |
| Lifecycle | Apply effective lifecycle boundaries; known 6806 has no bars on/after 2026-06-23. Missing bars do not imply delisted/no-trade. |

The 200 row cap is a bounded first-slice recommendation, not a new current
authority. It is large enough for the current 126 observed sessions and the
60-bar evidence window while remaining a bounded chart/read request. A later
contract may change it only with coverage/index evidence and a new task.

## Corporate Action Dependency Matrix

The adjustment audit and the corporate-action closure both conclude that
official event/reference-price pages exist, but a complete normalized,
point-in-time, source-approved dataset does not. The closure defines
EVENT_EXCLUDED_RAW_V0 as contract-ready only; source-use approval and
historical event semantics remain blocked. This task does not modify or own
that event source, schema, dataset, or policy.

| Dependency class | What can be published | What cannot be promoted | Current state |
|---|---|---|---|
| RAW_HISTORICAL_BAR_PUBLICATION | Official observed OHLCV rows with identity, date, source, quality, freshness, lineage, and explicit RAW/ADJUSTMENT_UNKNOWN disclosure | Adjusted prices, total return, silent raw-safety claim, or event-free claim | Partial; source chain/read path exists, V2 bounded contract incomplete |
| PRICE_CONTINUITY_DEPENDENT_INDICATOR | At most research-only/provisional evidence with explicit limitation and no formal Stock publication | MA, momentum, breakout distance, resistance continuity, ATR/volatility as accepted cross-event product fields | Blocked/deferred pending A policy plus deterministic technical contract |
| VOLUME_CONTINUITY_DEPENDENT_INDICATOR | Raw daily volume with unit/aggregation/source disclosure | Volume average/ratio/trend, volume profile/order flow as comparable cross-event fields | Deferred; share-count/split/reduction semantics and source contract incomplete |
| EVENT_MARKER_REQUIRED | None in current Stock timeline | Corporate-action markers, event annotations, event-driven chart labels | Not ready; A authority partial and source-use approval pending |
| RETURN_SEMANTICS | Raw price facts and named raw price differences only when explicitly labelled | Any return-like field with implied adjusted/total-return meaning | Blocked; HIST-002B adjustment state/semantic is not sufficient |

The absence of a matched event record is not proof of NO_ACTION. Unknown or
incomplete event authority must remain fail-closed for the affected technical
or outcome claim. A future event-aware implementation may use the A contract
to exclude affected episodes without mutating raw OHLCV.

## Technical Indicator Ownership and Versioning

If a technical field becomes formal, the calculation belongs in backend-owned
deterministic code or a research/provider-owned projection with an explicit
production contract. React may only select, format, and disclose the result.

Every published indicator must carry or be bound to:

~~~
algorithm_id
algorithm_version
parameter_set_id / parameter_version
lookback_rule
minimum_history
observation_window_start / end
as_of_trading_date
market_calendar / timezone / session
source_lineage_ids
adjustment_or_event_policy_id / version
rounding_policy
data_status / null_reason
~~~

Required semantics:

- as_of_trading_date=t means only accepted observations at or before t may
  enter the feature. No future label, current Topic state, future membership,
  or later event correction may flow backward.
- Insufficient history returns null plus an explicit reason such as
  INSUFFICIENT_HISTORY; windows are never shortened silently.
- Duplicate, invalid, superseded, conflicting, or missing required bars fail
  closed at the relevant field/stage.
- Rounding is not currently frozen for Stock technical fields. A future
  contract must state whether calculations remain Decimal through serialization
  and name the exact rounding mode/scale; it must not copy EOD rounding by
  accident.
- The existing opportunity_evidence builder is reusable as a deterministic
  algorithm-pattern reference only. Its policy is
  opportunity-evidence.v1.provisional, with tunable thresholds, and its
  output is Shadow/Research evidence. It is not a Stock technical publication
  authority and cannot be copied as production semantics.

## TECHNICAL_PUBLICATION_TIERS

| Tier | Definition | Evidence-backed scope | Current decision |
|---|---|---|---|
| Tier 0 | Raw historical bars plus source/freshness/lineage and explicit adjustment disclosure | Date, OHLCV, quality, lifecycle/no-data status, source identity; no adjusted/total-return claim | Partial; 006A closes the V2 publication contract |
| Tier 1 | Bounded backend-derived facts insensitive to cross-event continuity, with deterministic coverage/status rules | History sufficiency, observed coverage, accepted-row quality, same-bar raw facts, explicit unavailable/null reasons | Candidate only; no current Stock publication schema beyond partial tracking metadata |
| Tier 2 | Continuity indicators requiring event-aware or explicitly approved raw-series policy | MA5/10/20/60, volume average/ratio, distance-to-MA, 20D resistance/distance, momentum, ATR/volatility, basic breakout structure | Deferred pending A policy and 006B algorithm contract |
| Tier 3 | Advanced technical evidence requiring separate formal algorithms, data, anchors, or event models | Liquidity Sweep, Order Flow, Anchored VWAP, Volume Profile, FVG, MACD, RSI, Fibonacci, patterns | Deferred; no formal source/algorithm contract found |

Tier names do not promote existing research fields. A field moves tiers only
after its owner contract, source, algorithm version, as-of semantics, tests,
and UI formal-state mapping are accepted.

## Timeline Split

### PRICE_HISTORY_TIMELINE

This is the canonical accepted daily-bar series. It can share the historical
read model with a technical chart. The current V1 route is a partial formal
foundation; it is not wired to the V2 Stock Drawer and lacks complete
disclosures. Recommended order:

~~~
006A = bounded historical bar read/publication
006B = basic technical projection after technical/CA policy closure
~~~

### EVENT_TIMELINE

This is a heterogeneous event surface and must remain separate:

~~~
corporate actions -> A event authority
news -> News/Event foundation
Topic/history -> PIT Topic/System State authority
chip/institution -> institution provider/read model
system/lifecycle -> effective lifecycle and runtime event authority
technical events -> approved indicator/event algorithms
~~~

The existence of price bars does not make any of these event families formal.
The current overall EVENT_TIMELINE_PUBLICATION_READY=NO.

### Roadmap sequencing recommendation

The original conceptual order of Technical Detail before Timeline/history is
too coarse for the current evidence. The safer internal order is:

~~~
STOCK-006 audit
  -> STOCK-006A Historical Bar Read Publication
  -> STOCK-006B Basic Technical Projection
  -> STOCK-007 Event Timeline / remaining history domains
~~~

This is a recommendation only. NEXT_TASK and roadmap owner documents were not
changed by this audit.

## Frontend Formal-State Mapping and Regression Boundary

The current Explorer/Drawer implementation is consistent with 005C:

| UI area | Current formal state | Future rule |
|---|---|---|
| EOD | Formal/null/unavailable/Preview as supplied by backend | Preserve existing EOD boundary |
| Technical | FORMAL_NOT_WIRED when API object is null/partial; Preview only in explicit Preview resource | Do not fill from web snapshot or browser calculations |
| Price history | Not wired in V2 | Add a bounded history resource with loading/available/empty/unavailable/error states |
| Technical events | Unavailable/deferred | Do not infer from chart shape or client calculations |
| Corporate markers | Deferred | Render only A-authorized event records and disclosure |
| Institution/chip | Unavailable | Render only formal provider/read-model fields |
| Narrative | Unavailable/deferred | Render source-owned text only |
| Opportunity | Shadow/unavailable | Keep Shadow visible; never call it production Recommendation |
| Recommendation | Deferred/research-only | No Stock promotion |

Future Stock work must preserve:

- Drawer position: sticky, top: 72px, height: calc(100vh - 72px), and
  internal body scroll;
- push/close/reverse animation and Escape close;
- stale-request protection when switching symbols;
- topic filter behavior and backend-owned topic relation semantics;
- formal API errors as unavailable, never Preview;
- null values as unavailable, never zero-filled;
- render-only browser behavior.

apps/web/app/globals.css is a shared dirty file also touched by the Topic
Detail workstream. It is a collision surface for future implementation. This
audit did not edit it or any Topic component/adapter/shared file.

## API / Read-Model Options

Decision: keep GET /api/v2/stocks/{symbol} as a bounded summary/detail
resource and add one bounded historical subresource that reuses the current
historical read service. Do not add a large history array to the base detail
response and do not create parallel independent V1/V2 query semantics.

The 006A implementation plan should:

1. reconcile the actual canonical table/migration state with the HIST-002B
   closure evidence;
2. extract or adapt list_price_history into a shared read model;
3. add the missing freshness/lineage/adjustment/lifecycle fields;
4. make date/session/ordering/limit/null/no-data semantics explicit;
5. expose one V2 bounded subresource and, if V1 remains, serialize it from the
   same backend path;
6. add focused API/schema/OpenAPI/generated-client tests; and
7. wire the Drawer chart/history state only after the backend contract is
   formal, keeping the browser render-only.

No endpoint, schema, generated client, or frontend code was changed by this
audit.

## Lifecycle / Insufficient-History / Null Semantics

- A known terminated identity must have no published bars after its effective
  termination. 6806 is the canonical control: last bar 2026-06-22,
  termination 2026-06-23, zero later rows.
- A new listing or identity without enough prior bars is not backfilled from
  current data. It returns explicit insufficient history/unavailable state.
- NO_TRADE, SUSPENDED, EXCHANGE_CONFIRMED_NO_DATA, and missing/unexplained
  data remain distinct. Absence of a bar is not a lifecycle event.
- Technical minimum history is field-specific: MA5/10/20/60 require their
  named number of valid observations; rolling fields never shrink their
  window to produce a value.
- A right-edge series can publish bars while a technical field is null because
  its lookback or future window is incomplete. Outcome-like fields are not
  created from the right edge.
- Empty historical result is an explicit unavailable/empty read, not a zero
  bar, carried close, or Preview substitution.

## Browser Business Logic Boundary

~~~
BROWSER_TECHNICAL_CALCULATION_ALLOWED=NO
BROWSER_MA_CALCULATION=NO
BROWSER_ATR_CALCULATION=NO
BROWSER_MOMENTUM_OR_RETURN_CALCULATION=NO
BROWSER_BREAKOUT_OR_RESISTANCE_CALCULATION=NO
BROWSER_VOLUME_RATIO_CALCULATION=NO
BROWSER_CHANGE_OR_TURNOVER_CALCULATION=NO
BROWSER_PROVIDER_RECONCILIATION=NO
BROWSER_LIFECYCLE_INFERENCE=NO
~~~

React may render a backend field, select a formal status, format a number/date,
show a loading/error/null state, and apply UI filtering over already-published
backend values. It may not calculate, rank, infer, adjust, reconcile, or
silently choose a business semantic.

## Parallel Collision Analysis

| Workstream | Observed write set / authority | Decision |
|---|---|---|
| Corporate-action closure | docs/reports/TASK-REC-A1-CORPORATE-ACTION-EVENT-EXCLUSION-CLOSURE.md; committed at current HEAD; event schema/policy remains contract-only and source-use blocked | Read as dependency only; no event source/schema/dataset/policy files touched |
| REC-A1 adjustment/PIT/research audits | Report-only evidence under docs/reports/; no production technical ownership | Read-only evidence only; no backtest or research artifact changes |
| Topic Detail research workspace | Topic components/adapters/tests and shared apps/web/app/globals.css; Topic historical/system state remains unavailable | No Topic/shared files touched; future CSS changes require collision coordination |
| Today source-use/index/turnover | Independent Today authority and write set | Not touched |
| Existing Stock 005B/005C | Stock EOD backend/API/frontend files and focused tests | Read-only baseline; no changes |
| This audit | One new report path only | Exact write set isolated |

PARALLEL_SAFE_WITH_CORPORATE_ACTION_A=YES_READ_ONLY_INTERFACE_ONLY.
PARALLEL_SAFE_WITH_TOPIC_DETAIL_D=YES_REPORT_ONLY;SHARED_GLOBALS_CSS_COLLISION_FOR_IMPLEMENTATION.

## Recommended Vertical Slice Order

1. TASK-FE-BE-STOCK-006A-HISTORICAL-BAR-READ-PUBLICATION
   - reconcile HIST-002B table/chain naming and actual migration state;
   - formalize one bounded backend historical read model;
   - publish raw bars with full source/freshness/lineage and
     RAW/ADJUSTMENT_UNKNOWN disclosure;
   - enforce market/session/order/limit/date/lifecycle/null semantics; and
   - add API/OpenAPI/generated-client/focused read tests.
2. TASK-FE-BE-STOCK-006B-BASIC-TECHNICAL-PROJECTION only after the indicator
   contract and A dependency conditions are explicit. Start with a small
   approved subset; do not publish the full list by default.
3. STOCK-007 event timeline after each event family has an authority,
   lineage, as-of, and publication-state contract. Price history may be the
   first timeline panel, but it is not the whole event timeline.

This report does not open or implement any of these slices.

## Remaining Blockers

1. V2 Stock history is not wired to the existing bounded V1 read path.
2. HIST-002B closure table naming and current canonical observation-chain
   schema need exact reconciliation before claiming V2 row coverage.
3. Historical API lacks complete source, adapter, normalizer, mapping,
   reference, retrieved-at, adjustment, lifecycle, and freshness disclosure.
4. TWSE/TPEx historical OHLC adjustment semantics remain unknown in the
   accepted HIST-002B evidence.
5. Corporate-action event authority is partial and source-use approval is
   pending; EVENT_EXCLUDED_RAW_V0 is contract-only.
6. Point-in-time historical universe/membership is partial; survivorship-safe
   claims are not allowed.
7. No accepted Stock technical algorithm/parameter/version/rounding contract
   exists for the requested basic or advanced indicators.
8. Institution/chip provider/read model, News/Event foundation, and historical
   Topic/System State are not available.
9. Opportunity and Recommendation remain shadow/research boundaries, not Stock
   production publication.

## Impact Validation

This was an audit-only read-through. Existing focused-test evidence was read
from the 005B/005C, HIST-002B, and REC-A1 reports; no application suite,
database migration, provider request, or protected gate was rerun.

~~~
READ_ONLY_INSPECTION=PASS
EXISTING_FOCUSED_TEST_EVIDENCE=READ_FROM_ACCEPTED_REPORTS
G1=PRESERVED PASS / NOT RERUN
G2=PRESERVED PASS / NOT RERUN
G3=PRESERVED PASS / NOT RERUN
POST_CLOSE_CANARY=PRESERVED PASS / NOT RERUN
APPLICATION_CODE_CHANGED=NO
DATABASE_MUTATION=NO
HISTORICAL_DATA_CHANGED=NO
PRODUCTION_MUTATION=NO
~~~

The report-only validation after creation is limited to Markdown link/path,
unfinished-token, secret-pattern, and git diff --check review.

## Documentation Reconciliation

This task creates only the formal report. PROJECT_CONTEXT.md,
docs/ROADMAP.md, docs/product/TOPICPILOT_PRODUCT_ROADMAP.md,
docs/DOCUMENTATION_INDEX.md, docs/DAILY_PROGRESS.md, and
docs/WORK_ORDERS.md are current owner documents with pre-existing dirty or
concurrent workstream changes. They were not edited. This audit is not a
capability milestone and therefore:

~~~
REPORT_CREATED=YES
DAILY_PROGRESS_UPDATED=NO
OWNER_DOCUMENTS_UPDATED=NO
NEXT_TASK_CHANGED=NO
~~~

The roadmap sequencing suggestion in this report is advisory only and does not
replace or modify the roadmap's NEXT_TASK.

## Final Handoff

~~~
TASK_ID=TASK-FE-BE-STOCK-006-TECHNICAL-HISTORICAL-PUBLICATION-READINESS-AUDIT
FINAL_STATUS=STOCK_006_AUDIT_COMPLETE_WITH_PARTIAL_RAW_BAR_READINESS
CANONICAL_PRE_SHA=f2b0784d332917a51eb20ac5e03d9526c4434c4b
CANONICAL_POST_SHA=TASK_COMMIT_SHA_REPORTED_AT_HANDOFF
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
WORKTREE_CREATED=NO

STOCK_005C_BASELINE_CONFIRMED=YES
HIST_002B_BASELINE_CONFIRMED=YES / 507 IDENTITIES / 63826 ROWS / 2026-02-02..2026-08-13
RAW_HISTORICAL_BAR_PUBLICATION_READY=PARTIAL
HISTORICAL_READ_MODEL_EXISTS=YES_PARTIAL
HISTORICAL_API_CONTRACT_STATE=EXISTING_V1_BOUNDED_READ_PARTIAL_V2_NOT_WIRED
RAW_BAR_ADJUSTMENT_DISCLOSURE=RAW_OBSERVED_ADJUSTMENT_UNKNOWN_REQUIRED
BASIC_TECHNICAL_PUBLICATION_READY=PARTIAL
PRICE_CONTINUITY_INDICATORS_STATE=DEFERRED_PENDING_CORPORATE_ACTION_POLICY_AND_FORMAL_ALGORITHM_CONTRACT
VOLUME_CONTINUITY_INDICATORS_STATE=DEFERRED_PENDING_VOLUME_COMPARABILITY_AND_FORMAL_ALGORITHM_CONTRACT
ADVANCED_TECHNICAL_STATE=DEFERRED_NO_FORMAL_ALGORITHM_OR_SOURCE_CONTRACT
EVENT_TIMELINE_PUBLICATION_READY=NO
PRICE_HISTORY_TIMELINE_READY=PARTIAL
CORPORATE_ACTION_MARKERS_STATE=NOT_READY_PENDING_A_EVENT_AUTHORITY
INSTITUTION_CHIP_STATE=UNAVAILABLE
NARRATIVE_STATE=UNAVAILABLE_OR_DEFERRED
OPPORTUNITY_STATE=SHADOW_OR_UNAVAILABLE_NOT_PRODUCTION
RECOMMENDATION_STATE=RESEARCH_ONLY_NOT_PRODUCTION

BROWSER_TECHNICAL_CALCULATION_ALLOWED=NO
TECHNICAL_PUBLICATION_TIERS=TIER0_PARTIAL;TIER1_CANDIDATE_ONLY;TIER2_DEFERRED;TIER3_DEFERRED
NEXT_STOCK_EXECUTION_SLICE=TASK-FE-BE-STOCK-006A-HISTORICAL-BAR-READ-PUBLICATION
PARALLEL_SAFE_WITH_CORPORATE_ACTION_A=YES_READ_ONLY_INTERFACE_ONLY
PARALLEL_SAFE_WITH_TOPIC_DETAIL_D=YES_REPORT_ONLY_SHARED_GLOBALS_CSS_COLLISION_FOR_IMPLEMENTATION

REPORT_CREATED=YES
DAILY_PROGRESS_UPDATED=NO
APPLICATION_CODE_CHANGED=NO
DATABASE_MUTATION=NO
HISTORICAL_DATA_CHANGED=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO

G1=PRESERVED PASS / NOT RERUN
G2=PRESERVED PASS / NOT RERUN
G3=PRESERVED PASS / NOT RERUN
POST_CLOSE_CANARY=PRESERVED PASS / NOT RERUN
~~~

Stop at this audit handoff. Do not automatically begin 006A or any Stock
technical runtime implementation.

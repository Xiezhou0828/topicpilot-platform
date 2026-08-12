# TopicPilot Opportunity Engine Product & Architecture Specification

**Status:** `CURRENT PM DECISION / PRODUCT & ARCHITECTURE SPECIFICATION`
**Task:** `TASK-DOC-016`
**Updated:** 2026-08-12
**Owner:** TopicPilot PM
**Scope:** documentation only; no runtime, API, database, frontend, scheduler, or production activation authorization

## Product Positioning

TopicPilot does not provide a black-box AI tip, imperative `Buy / Sell / Strong Buy` instruction, or automatic trading decision. The formal product direction is an **Opportunity Engine**: a topic-first opportunity screening and research-integration layer that helps users decide what deserves further research and whether the current position is reasonable.

The Opportunity Engine is downstream of Topic Intelligence. It does not redefine Topic Score, Grade, Confidence, Lifecycle, or the identity of TopicPilot as a Taiwan Theme Intelligence Platform.

The customer journey remains:

```text
市場 → 題材 → 題材內股票 → Stock Encyclopedia → Opportunity / 查看機會 → 深度研究
```

The Opportunity surface must remain connected to that journey. It is not an isolated AI recommendation page and does not replace Topic Detail or Stock Encyclopedia.

## Core Principles

1. **Topic first:** decide whether a topic deserves research before evaluating its stocks; do not brute-force rank the whole market as one undifferentiated pool.
2. **Gate before rank:** separate disqualifying conditions from ranking factors. A strong positive signal cannot numerically cancel an invalidating risk.
3. **Technical-led V1:** technical structure and entry quality lead the first version; news is catalyst/context only.
4. **Entry quality is core:** a good topic and stock can still be a poor current opportunity when price is too far from valid support.
5. **Evidence first:** every surfaced Opportunity must expose structured reasons, confirmations, risks, and the reason it is not a higher priority.
6. **Deterministic backend authority:** formal semantics come from versioned backend policy and evidence. The browser does not classify or infer them.
7. **No fake precision:** an internal ranking score may order candidates, but the customer experience centers on state and evidence rather than decimal scores, stars, AI confidence, or imperative advice.
8. **History over daily binary flips:** Opportunity state transitions and later outcomes must be traceable for evaluation.
9. **LLM is an explanation adapter only:** a future LLM may verbalize structured evidence; it must not decide qualification, gates, state, or rank.

## Canonical Pipeline

The PM-frozen pipeline order is:

```text
Market Context
  → Topic Qualification
  → Stock Eligibility
  → Technical Structure
  → Risk Gate
  → Entry Quality
  → Chip Confirmation
  → Opportunity State
  → Evidence / Explanation
```

Each stage must preserve its own decision/evidence identity. A later stage must not silently rewrite an earlier semantic. Exact formulas, thresholds, weights, and transition mechanics are open until separately PM-frozen.

## Topic Qualification

Topic Qualification asks whether a topic is currently worthy of research allocation. Topic Grade, Lifecycle, rotation, and warming evidence may be inputs only under an approved policy. Grade is not a buy instruction, and no grade-to-Opportunity shortcut is frozen.

The exact qualifying Grade set and Lifecycle rule are **OPEN / NOT PM-FROZEN**. Any earlier example such as `S/A enter, B only when warming, D excluded` is historical/provisional and must not be treated as the current formal threshold.

## Stock Eligibility

Stock Eligibility determines whether a stock has sufficient identity, data, topic relationship, and baseline technical availability to continue through the pipeline. It is distinct from ranking and from the Stock Encyclopedia: an ineligible stock remains a valid catalog identity even when it is not an Opportunity candidate.

Eligibility must fail closed when required evidence is unavailable. It must distinguish at least `not evaluated`, `insufficient data`, and `evaluated but did not qualify`; final reason codes and payloads remain an implementation contract.

## Hard Gates

Hard Gates represent conditions that may directly exclude or invalidate a candidate instead of merely subtracting points. Candidate categories include:

- required data is incomplete or unavailable;
- price/20MA eligibility fails under the eventual approved rule;
- major support or structure is invalidated;
- abnormal sharp decline or other approved risk event is active;
- the topic is in an approved disqualifying decline state.

These are categories, not frozen formulas. Whether 20MA is the only mandatory technical gate, the exact invalidation pattern, cooldown period, and lifecycle exclusions are **OPEN / NOT PM-FROZEN**.

## Technical Structure

V1 prioritizes the smallest useful, explainable set:

- 20MA and 60MA availability and relative position;
- MA direction/trend;
- price/volume structure;
- breakout and retest behavior;
- support identification and support distance;
- major bearish-break structure, including long bearish candle invalidation;
- high-level consecutive weak-candle structure.

These describe scope only. Pattern definitions, lookback windows, volume normalization, support-selection hierarchy, 20MA/60MA treatment, and any scores remain **OPEN / NOT PM-FROZEN**.

## Risk Gate

Risk Gate prevents positive topic, technical, news, or chip evidence from hiding an invalidating condition. It must emit structured risk/invalidation evidence and distinguish:

- immediate exclusion/invalidation;
- temporary cooldown or re-evaluation required;
- chase/entry risk that should route to `等待回測` rather than invalidate the stock;
- unavailable evidence that prevents a formal decision.

Exact cooldown days, event thresholds, pattern rules, and their mapping to states remain open.

## Entry Quality

Entry Quality answers a different question from stock quality: **is the current location reasonable?** It must consider current price relative to valid support and other approved cost/structure references.

A strong stock whose price is too far from valid support should not remain the highest-priority opportunity. It may become `等待回測` or be marked as do-not-chase according to a future approved rule.

No support-distance bands are frozen. Earlier examples such as `0–5%`, `5–8%`, or `>8%` are explicitly **historical/provisional examples**, not formal rules.

## Chip Confirmation

Chip/institution evidence is a confirmation layer, not a primary gate and never a standalone recommendation trigger. Future inputs may include foreign-investor trend, investment-trust activity, and holdings of investors with 400 or more lots, subject to approved source, freshness, and semantics.

`Institutional net buy = Opportunity` is prohibited. Exact confirmation thresholds and ranking impact remain open.

## Catalyst / News Role

News and Radar may explain why a topic or stock is moving and may provide catalyst or risk context. News volume, heat, sentiment, or recency must not directly raise an Opportunity score unless a future explicit PM decision changes this policy.

News evidence must remain attributable and freshness-aware. It cannot override eligibility, risk, technical structure, or entry-quality decisions.

## Exception / Warming Pipeline

The system retains a second discovery entrance for:

- a topic that suddenly warms;
- a stock that strengthens abnormally relative to its topic.

This entrance can produce `升溫候選`. Exception discovery is not a direct recommendation and does not bypass Stock Eligibility, Risk Gate, or Entry Quality. A candidate can advance only after the formal pipeline confirms it. Exact warming and upgrade thresholds remain open.

## Opportunity States

The current PM-confirmed customer-facing states are:

| State | Product meaning |
|---|---|
| `升溫候選` | Newly detected through normal or exception warming evidence; requires further confirmation. |
| `轉強觀察` | Structure is improving, but the full confirmation needed for highest priority is not yet present. |
| `精選機會` | Topic, eligibility, risk, technical structure, and entry quality meet the future approved policy for a high-priority research opportunity. |
| `等待回測` | The stock/topic may remain attractive, but current entry location or chase risk is not appropriate for highest priority. |
| `失效` | A previously tracked Opportunity has lost eligibility or hit an approved invalidation condition. |

These names and their high-level meanings are **FROZEN**. Their numeric/logic transition thresholds are **OPEN / NOT PM-FROZEN**.

Earlier documents may contain `watch`, `awaiting_confirmation`, `trial_entry_candidate`, `invalidated`, `主線精選`, `龍頭先行`, `題材擴散`, `落後補漲`, or `Recommendation Lifecycle`. They remain historical, internal, migration, or provisional terminology. They must not silently replace the current customer-facing state set. A future mapping requires an explicit backend contract and PM approval.

## Ranking vs Display

Backend policy may compute an internal ranking score for deterministic ordering. That score is not automatically a customer-facing product metric.

The default presentation is:

```text
Opportunity State + structured evidence + principal risk + freshness
```

Avoid customer-facing `87.4 分`, `★★★★★`, `AI 信心 94%`, `強烈買入`, or equivalent fake-precision/imperative language. Exact internal ranking factors and weights are open.

## Evidence Model

Every Opportunity must provide structured evidence sufficient to answer:

1. **Why selected?** Topic context and the facts that admitted it to the pipeline.
2. **What confirms it?** Technical, entry, and optional chip confirmations.
3. **What are the risks?** Active warnings, invalidation evidence, missing data, and freshness limitations.
4. **Why not higher priority?** Missing confirmation, entry distance, chase risk, weaker relative structure, or other approved reason.

Conceptual evidence groups are:

```text
identity
topic_context
eligibility_evidence
technical_evidence
risk_evidence
entry_evidence
chip_confirmation_evidence
catalyst_context
priority_limiters
policy_and_data_lineage
```

Evidence must distinguish observed facts, derived facts, and unavailable inputs; preserve `null`; carry as-of/freshness and policy/model version where applicable; and use stable reason codes in a future formal contract. Natural-language explanation is derived from this structure, never the reverse.

## Backend Authority

The backend is authoritative for:

- Topic qualification and Stock eligibility;
- Hard Gate and Risk Gate outcomes;
- technical classification and support semantics;
- Entry Quality;
- chip confirmation classification;
- internal ranking and formal Opportunity State;
- transition reason and structured evidence;
- leader/relative-strength semantics used by Opportunity policy.

The existing Recommendation read-model/API remains historical implemented infrastructure. This specification does not activate it or claim it currently implements the new Opportunity pipeline.

### Shadow-only implementation boundary

The first executable slice is a pure, non-published shadow evaluator at `services/api/src/topicpilot_api/topic_engine/opportunity_shadow.py`. It accepts explicit upstream facts and composes evidence/state only. Its baseline eligibility check reflects the current execution objective (`sufficient OHLCV`, `20MA available`, and `price >= 20MA`), but this is a shadow observation contract, not production activation or a replacement for the still-open PM policy decisions. Technical pattern facts, Risk Gate outcomes, support validity, chip confirmation, and all thresholds remain caller-supplied until separately approved.

## Frontend Presentation Rules

The frontend consumes formal backend semantics and must not infer or recalculate them. Opportunity cards/lists should show, when supported:

- topic identity/context;
- stock name, symbol, and market identity;
- Opportunity State;
- primary evidence;
- primary risk/limiter;
- freshness/as-of context;
- `查看機會` CTA into the existing research flow.

Presentation is status-first and evidence-first, using the existing **Modern Financial Workspace** language: warm neutral palette, restrained borders/shadows, compact editorial density, and Taiwan price-direction conventions. Opportunity states must not take over the red/green price semantics.

## Opportunity History / State Transition

Opportunity is a lifecycle, not a daily recommendation boolean. The system must eventually preserve timestamped state transitions such as:

```text
升溫候選 → 轉強觀察 → 精選機會 → 等待回測 → 失效
```

Transitions may branch, repeat, or skip states only under a future approved transition policy. History should retain previous/current state, effective/as-of time, reason codes, evidence snapshot/lineage, policy version, and invalidation/closure context. Persistence design and retention are not authorized by this document.

## Performance Evaluation

Future Recommendation/Opportunity Performance Evaluation must evaluate versioned state snapshots and transitions against subsequent outcomes. It should support analysis by topic context, state at observation, horizon, entry-quality band, risk reason, policy version, and data completeness.

Return, MFE, MAE, hit-rate, and transition-quality metrics are research outputs, not live ranking inputs by default. Evaluation must avoid survivorship/look-ahead bias and must not silently promote thresholds or weights to production.

## Shadow Technical Evidence Layer (TASK-BE-020)

The first technical evidence layer is a shadow-only calculation boundary:

```text
canonical accepted DAILY_BAR OHLCV
  → OHLCV sufficiency
  → MA20 / MA60 / MA direction
  → price-volume structure
  → breakout / retest
  → support candidates and primary support
  → Entry Quality
  → bearish-break / weak-candle Risk Evidence
  → OpportunityShadowInput
  → existing Opportunity Shadow Composer
```

`Technical Evidence Builder`, `Risk Evidence Builder`, `Entry Quality Builder`, and
`OpportunityShadowInputBuilder` calculate structured facts; the existing Composer
only composes those facts into a non-published shadow result. Composer and
calculator responsibilities must remain separate. Missing OHLCV, MA, support,
volume, or chip evidence is represented as unavailable/unknown and is never
converted to zero or a passing value.

All builders use trading observations and an explicit `as_of` date. Historical
shadow replay filters every input bar to `trading_date <= as_of`; future/current
full-history hindsight is not allowed. Replay is in-memory/report/test scope and
does not persist lifecycle state, calculate P&L, or activate production evaluation.

The implementation carries an `OpportunityEvidencePolicy` version. Its numeric
parameters are centralized and labelled `PROVISIONAL / TUNABLE`; no threshold,
weight, or formula is PM-frozen by this section. Canonical PostgreSQL remains the
formal upstream data authority; no API, database, scheduler, or frontend contract
is changed by the shadow layer.

## V1 Strategy Architecture (TASK-BE-024)

The first strategy layer is a multi-strategy shadow engine above the technical
evidence layer. It is additive to the existing Recommendation read-model
history and does not rewrite `opportunity_shadow.py` or the legacy strategy
tables.

```text
Theme Context
  → Eligibility
  → Exclusion / Risk
  → Strategy Evidence
  → Strategy-specific Ranking
  → Opportunity Strategy Result
```

V1 contains two implemented shadow strategies:

| Strategy | Meaning | Required evidence | Status |
|---|---|---|---|
| `TREND_CONTINUATION` | strong topic context plus a stock already holding healthy trend structure | Grade/Lifecycle context, price above 20MA, rising MA direction, relative strength, volume, structural risk, extension/entry context | `V1 / SHADOW IMPLEMENTED` |
| `CATCH_UP` | strong topic context plus a lagging stock whose structure remains healthy and relative strength is improving | topic context, lag window, healthy trend, no structural weakness, RS inflection, volume activation | `V1 / SHADOW IMPLEMENTED` |

`EARLY_STRENGTH` and `PULLBACK_ACCEPTANCE` are explicit future strategy
identifiers and return `FUTURE_NOT_IMPLEMENTED`; they do not enter V1 ranking.
The strategies are evaluated and ranked independently. There is no global
cross-strategy ranking, implicit winner, or strategy score fed back into Topic
Score. An internal rank score may exist in the shadow result for calibration,
but confidence is a separate evidence-quality label and is not a probability.

### Theme Context

Strategies consume, rather than recalculate, topic Grade, Lifecycle, Topic
Strength, snapshot/as-of identity, strength evidence, effective membership, and
formal no-trade coverage. Grade/lifecycle eligibility is policy-driven. Current
starting values such as `S/A`, `FERMENTING`, or `MAIN_RISE` are provisional
configuration, not a product-level Grade or Lifecycle freeze. Missing context
defers the strategy result; it is never converted to a weak grade or zero.

### Trend Continuation

Trend Continuation requires a policy-eligible Theme Context and a healthy stock
structure. The evidence builder supplies daily OHLCV-derived price/20MA,
20MA direction, recent return, relative stock-vs-topic performance, volume
behavior, support/entry context, extension context, and structural risk. Price
below 20MA, confirmed breakdown, formal no-trade, invalid/insufficient data, or
unknown required coverage are exclusion/deferred conditions. Extension,
volatility, weak volume, and proximity to resistance remain evidence/penalty
contexts rather than an excuse to bypass a hard exclusion.

### Catch-up Opportunity

Catch-up requires an eligible Theme Context, an explicit relative lag within a
policy window, healthy trend structure, no structural weakness, and relative
strength stabilizing or improving. `LAGGING` is not equivalent to `WEAK`:
lagging stocks outside the configured window, persistent RS deterioration,
price below the trend gate, breakdown, abnormal drawdown, volume-supported
selloff, or formal data failure are excluded. Volume activation is evidence and
cannot create a Catch-up result by itself.

### Policy and Evidence Contract

`OpportunityPolicy` is versioned as `topic-opportunity-policy.provisional.1`.
Thresholds, windows, allowed grades/lifecycles, ranking weights, extension
bands, lag windows, RS inflection lookback, volume activation, confidence
coverage, and future transition semantics are centralized and labelled
`PROVISIONAL / TUNABLE`. No numeric value in a legacy V1 helper or old
Recommendation report is silently promoted into this policy.

Each strategy result retains strategy id, policy version, as-of date, stage
assessments, deterministic reason codes, positive/negative evidence, exclusion
codes, rank availability, rank score (if calculable), confidence and its basis.
The result is `SHADOW_ONLY`; it is not a customer Buy/Sell instruction and is not
persisted by this task.

## Historical Replay and PM Calibration

The V1 strategy module provides deterministic in-memory replay over explicit
`StrategyReplayCase` inputs. For each evaluation date it filters canonical bars
to `trading_date <= evaluation_date`, evaluates Trend/Catch-up independently,
and emits a `StrategyReplayResult` with a no-look-ahead assertion. A
`PMCalibrationReport` presents date, topic, instrument, strategy, theme Grade,
Lifecycle, eligibility, exclusions, relative performance, rank score,
confidence, and reason codes for PM review.

Replay does not write `StrategyRun`, `StrategyCandidate`, `Opportunity`, or
performance tables; it does not calculate P&L, notifications, favorites,
orders, or lifecycle activation. Existing `MAS/MAV/TMC/BB/PB/KD` rows and V1
strategy tables remain compatibility/read-model history. Any future persistence
adapter requires a separate work order and schema/API decision.

## Architecture Reconciliation Labels

The TASK-BE-024 audit uses the following migration labels:

- **KEEP:** canonical Topic/Stock identity, effective instrument-topic
  membership, daily canonical OHLCV, Topic Snapshot/Grade/Lifecycle as upstream
  context, existing evidence primitives, and read-only API boundaries.
- **REUSE:** the current technical evidence builders, structured `Evidence` /
  `StageAssessment`, no-look-ahead replay semantics, and existing Opportunity
  status-first/evidence-first presentation contract.
- **ADAPT:** legacy strategy-candidate concepts, support/trigger/invalidation
  fields, internal ranking metadata, and strategy-specific read-model shapes;
  they may be mapped only through an explicit V1 shadow adapter.
- **DEPRECATE_LATER:** legacy `Recommendation` terminology and old strategy
  presentation when a governed Opportunity read contract exists.
- **HISTORICAL_ONLY:** V1 `MAS/MAV/TMC/BB/PB/KD` strategy identifiers, old
  `Recommendation Score`/rank examples, `補漲候選` formula examples, and any
  private/demo snapshot values. They remain traceable but are not current
  Opportunity policy authority.

## Roadmap

### V1

- topic qualification boundary;
- 20MA/60MA and MA trend;
- price/volume structure;
- breakout/retest/support;
- bearish break/high-level weak-candle risk;
- support distance and Entry Quality;
- state + structured evidence.

### V1.5

- Anchored VWAP;
- Volume Profile;
- approved institution/chip confirmation inputs.

### V2

- Liquidity Sweep;
- Order Flow;
- other high-cost technical modules;
- mature lifecycle/history learning and evaluation only after governance approval.

Roadmap labels describe intended sequencing, not implementation authorization.

## Data Dependencies

The future engine depends on formal, freshness-aware contracts for:

- market/session context;
- Topic identity, membership/role, Grade, Lifecycle, score history, rotation/warming evidence;
- stock identity and topic relations;
- sufficient adjusted daily OHLCV history for MA and pattern evaluation;
- intraday/daily price freshness and session/as-of semantics;
- support/resistance and price/volume evidence under an approved technical policy;
- corporate-action handling and missing-data semantics;
- institution/chip data with source, unit, period, and freshness lineage;
- attributed news/Radar catalyst and risk context;
- versioned policy/model identity;
- Opportunity snapshots, state transitions, and later evaluation observations.

Availability does not imply policy approval. Missing values remain unavailable/null rather than zero.

## Open Business Rules / PM Decisions Needed

All items below are explicitly **OPEN / NOT PM-FROZEN**:

1. Topic Grade qualification threshold.
2. Lifecycle qualification rule.
3. Whether 20MA is the only mandatory gate.
4. Whether 60MA is a gate, bonus, ranking factor, or evidence only.
5. Support-distance threshold/bands and support-selection hierarchy.
6. Risk cooldown days.
7. Formal price/volume pattern definitions and lookbacks.
8. Topic Quality / Technical / Entry / Chip weights or formula.
9. Maximum candidates per topic.
10. Opportunity validity period.
11. Whether and how intraday ranking automatically reorders.
12. Exception/warming upgrade threshold.
13. Institution/chip confirmation threshold.
14. Opportunity state transition thresholds and allowed transition graph.

No historical number, schema placeholder, UI label, workshop example, or V1 rule may be promoted into these rules without explicit PM approval.

## Legacy and Conflict Handling

- V1 `落後補漲_觀察 / 落後補漲_確認`, strategy candidates, and their classification priority remain historical production/migration context.
- Early architecture terms `Candidate Recommendation`, `Recommendation Score (0–100)`, and `Rank` remain historical architecture/read-model concepts. A numeric score may exist internally, but it is no longer the default customer presentation.
- Existing Recommendation read-model/API work remains a deterministic, explainable, fail-closed infrastructure boundary; it does not prove Opportunity policy implementation or production activation.
- Earlier Opportunity group labels in the frontend specification remain provisional taxonomy, not the current formal state model.
- When this specification conflicts with an older Recommendation/Opportunity concept about current product direction, the PM decisions recorded here take priority. Historical documents remain unchanged unless separately governed.

## Non-goals

This specification does not authorize or define:

- production engine activation or customer publication. A separately identified
  shadow-only V1 strategy/replay implementation is documented below; it does
  not change the production boundary;
- API, database, migration, frontend, scheduler, or deployment changes;
- automatic trading, order execution, portfolio sizing, stop loss, target price, or buy/sell advice;
- frozen formulas, weights, thresholds, cooldowns, validity periods, or intraday reorder rules;
- direct news-heat scoring or institution-buy-equals-recommendation logic;
- browser-side business inference;
- a standalone AI recommendation page;
- changes to `AI/NEXT_TASK.md`.

## Shadow Implementation Amendment (TASK-BE-024)

The earlier documentation-only decision remains valid for production: no
Recommendation/Opportunity API, persistence, scheduler, frontend semantic, or
lifecycle activation is authorized. TASK-BE-024 adds an explicitly bounded
shadow implementation for `TREND_CONTINUATION` and `CATCH_UP`, plus deterministic
replay and PM calibration output. It is versioned, in-memory/test/report scoped,
and must not be interpreted as production policy approval.

## Decision Summary

```text
OPPORTUNITY_PRODUCT_POSITIONING = FROZEN
OPPORTUNITY_PIPELINE = FROZEN
OPPORTUNITY_STATES = FROZEN
HARD_GATE_CONCEPT = FROZEN
EVIDENCE_FIRST_PRESENTATION = FROZEN
WEIGHTS_AND_THRESHOLDS = OPEN
SHADOW_STRATEGY_IMPLEMENTATION = YES
PRODUCTION_IMPLEMENTATION_STARTED = NO
IMPLEMENTATION_STARTED = NO (PRODUCTION; SHADOW-ONLY EXCEPTION ABOVE)
```

## TASK-BE-024A — Opportunity Decision Contract & Explainable Ranking

TASK-BE-024A extends the existing V1 shadow strategies with a deterministic
decision boundary and a provider-neutral read projection. It does not activate
the engine, publish an API, write a database row, or alter Topic Score/Grade/
Lifecycle.

### Strategy-specific ranking profiles

Trend Continuation and Catch-up use separate, immutable ranking profiles. Each
profile makes the same conceptual dimensions explicit while allowing the
strategy to emphasize different evidence:

- Trend: Theme Quality, Trend Structure, Relative Strength, Volume
  Confirmation, Entry Quality, and Extension Risk context.
- Catch-up: Theme Quality, Healthy Structure, Lag Quality, Relative Strength
  Inflection, Volume Activation, Entry Quality, and Extension Risk context.

The profile version and every numeric parameter are labelled
`PROVISIONAL_TUNABLE_VERSIONED`. There is no global cross-strategy ranking and
no claim that these provisional weights are optimized or PM-frozen.

### Decision and state contract

After eligibility, exclusion/risk, strategy evidence, and strategy-local
ranking, a deterministic decision maps the result to one of:

`SELECTED`, `WAITING_RETEST`, `WAITING_CONFIRMATION`, `DEFERRED`, or `EXCLUDED`.

`CANDIDATE`/`DEFERRED`/`EXCLUDED` remain engine eligibility statuses for
compatibility. The uppercase Opportunity state is the user-facing semantic;
legacy shadow-composer states remain historical compatibility values. A weak
or missing confirmation layer can produce `WAITING_CONFIRMATION` without
becoming an exclusion; missing required context remains `DEFERRED` and a hard
gate remains `EXCLUDED`.

### Explainability contract

`OpportunityExplanation` is composed only from structured backend evidence.
It includes `summary_code`, positive factors, waiting factors, risk factors,
exclusion factors, entry context, invalidation context, data quality, and a
confidence basis. Each factor carries a stable code/display key, category,
status, structured value, benchmark, source, and evidence status. A future LLM
may verbalize these factors, but it cannot decide state, ranking, or risk.

### Shadow Read Contract

`OpportunityReadModel` is provider-neutral, persistence-neutral, and designed
for a future frontend/API adapter. It carries instrument/topic identity,
strategy, as-of, state, eligibility/status, optional internal rank score,
confidence basis, entry/support/risk contexts, exclusion codes, explanation,
policy/data status, and upstream Topic Grade/Lifecycle/Strength. Production
publication remains `SHADOW_ONLY`; the frontend must consume these formal
semantics and must not infer state, gates, leaders, or technical classes in the
browser.

### Fixtures and calibration boundary

Deterministic fixture payloads cover Trend `SELECTED` and `WAITING_RETEST`,
Catch-up `SELECTED` and `WAITING_CONFIRMATION`, `EXCLUDED`, and `DEFERRED`.
The calibration contract reserves forward 1/3/5/10-day horizons and MFE, MAE,
support-touch, invalidation, and threshold-hit metrics. It is a schema
placeholder only; no outcome evaluation, profitability calculation, or
parameter optimization runs in TASK-BE-024A.

The future `EARLY_STRENGTH` and `PULLBACK_ACCEPTANCE` strategy slots remain
`FUTURE_NOT_IMPLEMENTED`. Replay keeps the existing as-of/no-look-ahead
constraint and all existing A/B shadow behavior.

### 024A decision summary

```text
OPPORTUNITY_DECISION_CONTRACT = FROZEN (SHADOW CONTRACT)
RANKING_PROFILES_INDEPENDENT = FROZEN (SHADOW CONTRACT)
EXPLAINABILITY_CONTRACT = FROZEN (SHADOW CONTRACT)
READ_CONTRACT = FROZEN (SHADOW CONTRACT)
PARAMETERS_PROVISIONAL = YES
GLOBAL_CROSS_STRATEGY_RANKING = DISABLED
PRODUCTION_API_ACTIVATION = NO
PRODUCTION_DB_WRITE = NO
```

## TASK-BE-024B Qualification Policy V1 amendment

This amendment supersedes the earlier 024A statement that Topic Grade,
Lifecycle, 20MA/60MA semantics, and candidate caps were still wholly open for
the V1 shadow policy. The PM semantic order is now frozen while parameters
remain provisional:

```text
S/A -> FORMAL_OPPORTUNITY
B + warming/improving provenance -> EXCEPTION_CANDIDATE
D -> EXCLUDED
DECLINING -> EXCLUDED (new A/B)
CLOSE_GE_20MA -> required hard gate
missing 20MA -> DEFERRED
60MA -> structure/ranking factor, never hard gate
RISK -> evaluated before ranking
A/B -> independent rankings; no global winner
POST_CLOSE -> ranking cadence
INTRADAY -> status-only; no V1 reranking
PRESENTATION -> Trend Top 3 / Catch-up Top 2
```

The five decision states remain `SELECTED`, `WAITING_RETEST`,
`WAITING_CONFIRMATION`, `DEFERRED`, and `EXCLUDED`. All thresholds, weights,
support distances, lag/RS/volume rules, lifecycle multipliers, and maturity
penalties are centralized, versioned, and `PROVISIONAL_TUNABLE_VERSIONED`.
Historical replay/calibration is reserved for point-in-time 1D/3D/5D/10D
outcomes with no look-ahead; no calibration or production activation is part of
024B. `EARLY_STRENGTH` and `PULLBACK_ACCEPTANCE` remain future slots.

## TASK-BE-024B — Opportunity Qualification Policy V1 semantic freeze

The following policy layer is the current PM semantic priority over earlier
illustrative examples in this document. It is a deterministic, shadow-only
qualification boundary above the existing strategy evaluators; it does not
recalculate Topic Score, Grade, or Lifecycle and does not publish a
Recommendation.

### Frozen qualification matrix

| Dimension | Current PM decision |
|---|---|
| Topic Grade | `S`/`A` form the formal Opportunity Universe for Trend and Catch-up. `B` is not formal universe; it may enter only as `EXCEPTION_CANDIDATE` with qualified warming/improving evidence and provenance. `D` is hard excluded. |
| Lifecycle | `SPROUTING`, `FERMENTING`, and `MAIN_RISE` can qualify both strategies. `MATURE` remains eligible for Trend; Catch-up requires stricter confirmation. `DECLINING` hard excludes new opportunities. |
| 20MA | `Close >= 20MA` is the V1 hard technical gate. `<20MA` is `EXCLUDED`; missing 20MA/context is `DEFERRED`. Ranking cannot override it. |
| 60MA | Structure and ranking factor only. Price above 20MA but below 60MA is recovery/improving context, not an automatic exclusion. |
| Risk order | Confirmed support/structural breakdown excludes before ranking. A single weak candle is evidence/context; persistent weakness requires confirmation and is non-selected `WAITING_CONFIRMATION`. |
| Strategy separation | Trend and Catch-up qualify and rank independently. No global A/B winner is produced. |
| Presentation | Trend shows at most Top 3 and Catch-up at most Top 2; backend retains all ranking candidates. |
| Cadence | V1 ranking is post-close. Intraday is status-only; no intraday re-ranking. |

The current user-facing state contract remains `SELECTED`, `WAITING_RETEST`,
`WAITING_CONFIRMATION`, `DEFERRED`, and `EXCLUDED`. The policy's internal
qualification labels (`FORMAL_OPPORTUNITY`, `EXCEPTION_CANDIDATE`, and
qualification statuses) are evidence/provenance fields, not buy/sell advice.

### Provisional parameter boundary

All numeric thresholds, weights, pattern definitions, cooldown periods, and
transition parameters remain `PROVISIONAL / TUNABLE / VERSIONED`. In
particular, no support-distance percentage, lifecycle-grade threshold,
institution/chip threshold, exception upgrade threshold, ranking weight, or
validity window is frozen by TASK-BE-024B. Calibration must use canonical
production daily OHLCV and carry selection provenance; fixtures and synthetic
bars are test inputs only, never calibration evidence.

### Qualification audit trail

Every shadow result carries the policy and parameter version, qualification
status/reason codes, exception provenance, and a `QUALIFICATION_POLICY` stage.
Replay bounds bars, topic snapshots, warming flags, and relative-gap history to
the evaluation date. Future evaluation must retain strategy, horizon, forward
return, MFE/MAE, threshold hits, support hold/fail, invalidation outcome,
Lifecycle/Grade/state at selection, ranking profile version, policy version,
and parameter version without look-ahead.

This TASK-BE-024B section supersedes the earlier **OPEN** examples for the
semantic matrix above while preserving their historical/provisional status for
numeric implementation details.

The following remain explicitly `OPEN / PROVISIONAL / NOT CALIBRATED`: exact
support-distance threshold; risk cooldown days; formal price/volume pattern
definitions; Topic Quality/Technical/Entry/Chip weights; same-topic stock cap;
Opportunity validity period; future intraday auto-reranking thresholds;
institution/chip confirmation thresholds; lifecycle rank multipliers and
maturity penalty magnitudes; and every numeric state-transition threshold.
The semantic decisions above (Grade S/A/B/D classes, Lifecycle x Strategy
ordering, 20MA hard gate, non-hard-gate 60MA, risk-before-ranking, independent
A/B ranking, state vocabulary, caps, and post-close/status-only cadence) are
the current TASK-BE-024B shadow freeze.

## TASK-BE-024C Shadow Read API & Frontend Adapter V1

The first integration surface for the frozen shadow semantics is a
provider-neutral, persistence-free read service. It provides list, topic,
stock, and detail projections through a shadow-only API and preserves the
existing OpportunityReadModel, structured explanation, qualification
provenance, policy/parameter/ranking-profile versions, and strategy-local
Trend Top 3 / Catch-up Top 2 presentation caps. Full backend ranking remains
available for research; A/B are never globally merged.

The fixture provider is deterministic and synthetic, visibly marked
`publicationStatus=SHADOW` and `dataStatus=FIXTURE/SYNTHETIC`. It covers all
five user-facing states plus B warming exception and Mature/Declining context.
The canonical production provider is a future explicit adapter and is not
silently replaced by fixtures.

The frontend adapter is a projection mapper only: it groups sections, follows
backend display order, preserves evidence and versions, and maps
`LOADING/READY/EMPTY/DEFERRED/UNAVAILABLE/ERROR`. It must not infer
eligibility, risk, state, rank, score, technical classification, or exception
qualification. No production API publication, DB persistence, scheduler
activation, replay, calibration, or UI implementation is included.

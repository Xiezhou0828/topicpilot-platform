# TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819

## Closure status

This report continues the canonical WS2 Technical V0 mainline after
`TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818`.
It inventories the implementation that actually exists at canonical HEAD,
measures historical coverage, and records a normalized read-only evidence
surface. It does not add an indicator, change a parameter, add persistence, or
change strategy semantics.

```text
TASK_ID=TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819
SOURCE_CANONICAL_HEAD=2468ee6b5093dd2a37353424c74d9d719c643bb9
TASK_SCOPE=INVENTORY + FORMAL_EVIDENCE_SURFACE + HISTORICAL_COVERAGE + PIT_AUDIT + NEXT_STEP_READINESS
TASK_FINAL_STATUS=COMPLETE_READ_ONLY_INVENTORY_AND_EVIDENCE_SURFACE
READY_FOR_WS2_NEXT_MAINLINE_STEP=YES_WITH_EXPLICIT_INDICATOR_SURFACE
READY_FOR_WS2_PRODUCTION=NO
```

## Authority and provenance

The inventory used the canonical V2 Technical V0 implementation and its
existing read-only route:

- `services/api/src/topicpilot_api/technical_publication.py`
- `services/api/src/topicpilot_api/known_event_aware_publication.py`
- `services/api/src/topicpilot_api/schemas.py`
- `services/api/src/topicpilot_api/production_read_model_api.py`
- `services/api/tests/test_technical_publication.py`
- `docs/architecture/STOCK_TECHNICAL_V0_POLICY_CONTRACT.md`
- `reports/TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818/`

Historical input authority was the V2 canonical observation chain, with the
real TPE/TWO dataset covering 507 instruments and 63,826 accepted rows from
2026-02-02 through 2026-08-13. Event controls used the committed bounded
REC-A1 event evidence dataset; its event evidence hash is
`4d9b4912bd1c4613510e60c5cf4b5a629c367e1c94dd733d3b1dc3f935e0eb5d`.

The rerunnable validator is
[`scripts/ws2_technical_v0_indicator_inventory.py`](../../scripts/ws2_technical_v0_indicator_inventory.py).
It reads canonical history and writes only task-owned analytical artifacts;
it performs no database writes, migration, provider call, scheduler action,
Production mutation, deployment, or push.

## Q1–Q4 — actual inventory and classification

The current canonical V2 Technical V0 runtime exposes exactly these fourteen
formal outputs:

| Family | Formal V0 indicator IDs |
|---|---|
| Moving average | `MA5`, `MA10`, `MA20`, `MA60` |
| Distance | `DISTANCE_TO_MA20` |
| Raw return | `RAW_CLOSE_RETURN_5D`, `RAW_CLOSE_RETURN_20D` |
| Volume | `VOLUME_MA5`, `VOLUME_MA20`, `VOLUME_RATIO_20` |
| Momentum | `RSI14` |
| MACD | `MACD_12_26_9`, `MACD_SIGNAL_12_26_9`, `MACD_HISTOGRAM_12_26_9` |

Classification counts:

```text
TECHNICAL_FIELD_COUNT=31
FORMAL_V0_INDICATOR_COUNT=14
IMPLEMENTED_NOT_FORMAL_COUNT=0
LEGACY_INDICATOR_COUNT=16
RESEARCH_ONLY_INDICATOR_COUNT=0
DEFERRED_INDICATOR_COUNT=8
RAW_OBSERVATION_FIELD_COUNT=2
DERIVED_INDICATOR_COUNT=14
ELIGIBILITY_STATE_COUNT=2
CONTINUITY_STATE_COUNT=1
PUBLICATION_METADATA_FIELD_COUNT=19
AVAILABILITY_METADATA_FIELD_COUNT=7
```

The 16 legacy indicator-like fields are read-only values from
`apps/web/app/lib/snapshot-adapter.ts`; they are not V2 Technical V0
calculation or publication authority. No separate current V2
`IMPLEMENTED_BUT_NOT_FORMAL` calculator was found. Existing WS3 research code
reuses deterministic V0 calculation functions but does not introduce another
formal indicator ID or publication surface.

The legacy indicator-like names are `ma20`, `ma60`, `ma20SlopePct`,
`daysAboveMa20`, `rs5Pct`, `rs20Pct`, `distanceTo20DayHighPct`, `macdDif`,
`macdSignal`, `macdHist`, `kdK`, `kdD`, `rsi14`, `volumeRatio`,
`upVolumeRatio`, and `pullbackVolumeShrinkRatio`. The same adapter also reads
legacy derived states such as `structureState`, `breakout20DayHigh`, and
`volumeStatus`; those are listed separately as `DERIVED_PUBLICATION_FIELD`,
not counted as indicators.

`PRICE_VS_MA20`, Bollinger Bands, ATR, ADX, KD, OBV, VWAP, and similar common
names were not promoted merely because they are common. `PRICE_VS_MA20` is not
present in the current V2 formal implementation and is recorded only as a
future evidence gap candidate where relevant.

The eight deferred families are Liquidity Sweep, Order Flow, Anchored VWAP,
Volume Profile, FVG, Fibonacci, Supply & Demand, and Trading Patterns. Daily
OHLCV is not treated as true Order Flow authority.

## Q5–Q7 — PIT safety and historical coverage

All fourteen formal indicators are bounded-reconstructable from the canonical
63,826-row dataset when their required history and continuity authority pass.
That does not mean every row is publishable: insufficient history and
indicator-window continuity remain explicit availability outcomes.

```text
PIT_SAFE_FORMAL_INDICATOR_COUNT=14
PIT_UNSAFE_FORMAL_INDICATOR_COUNT=0
HISTORICALLY_RECONSTRUCTABLE_FORMAL_INDICATOR_COUNT=14
NONRECONSTRUCTABLE_FORMAL_INDICATOR_COUNT=0
```

Coverage counts below are per indicator across all 63,826 as-of observations.
`AVAILABLE_OBSERVATIONS` includes ordinary `FORMAL` and explicitly limited
`FORMAL_WITH_LIMITATION` values. The counters are intentionally non-exclusive:
an observation may be counted as available-with-limitation while the same
source limitation is also counted in the continuity/source audit columns.

| Indicator | Calculable instruments | Non-calculable instruments | Available observations | Insufficient history | Continuity limited | Continuity blocked | Error | Earliest defensible | Latest defensible |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `MA5` | 500 | 7 | 60,093 | 2,028 | 20,242 | 1,705 | 0 | 2026-02-06 | 2026-08-13 |
| `MA10` | 488 | 19 | 55,899 | 4,563 | 19,412 | 3,364 | 0 | 2026-02-24 | 2026-08-13 |
| `MA20` | 431 | 76 | 47,884 | 9,633 | 17,752 | 6,309 | 0 | 2026-03-11 | 2026-08-13 |
| `MA60` | 212 | 295 | 24,039 | 29,913 | 11,112 | 9,874 | 0 | 2026-05-11 | 2026-08-13 |
| `DISTANCE_TO_MA20` | 431 | 76 | 47,884 | 9,633 | 17,752 | 6,309 | 0 | 2026-03-11 | 2026-08-13 |
| `RAW_CLOSE_RETURN_5D` | 496 | 11 | 59,248 | 2,535 | 20,076 | 2,043 | 0 | 2026-02-09 | 2026-08-13 |
| `RAW_CLOSE_RETURN_20D` | 420 | 87 | 47,111 | 10,140 | 17,586 | 6,575 | 0 | 2026-03-12 | 2026-08-13 |
| `VOLUME_MA5` | 500 | 7 | 60,093 | 2,028 | 20,242 | 1,705 | 0 | 2026-02-06 | 2026-08-13 |
| `VOLUME_MA20` | 431 | 76 | 47,884 | 9,633 | 17,752 | 6,309 | 0 | 2026-03-11 | 2026-08-13 |
| `VOLUME_RATIO_20` | 431 | 76 | 47,884 | 9,633 | 17,752 | 6,309 | 0 | 2026-03-11 | 2026-08-13 |
| `RSI14` | 167 | 340 | 44,276 | 7,098 | 18,582 | 12,452 | 0 | 2026-03-04 | 2026-08-13 |
| `MACD_12_26_9` | 167 | 340 | 38,723 | 12,675 | 16,756 | 12,428 | 0 | 2026-03-19 | 2026-08-13 |
| `MACD_SIGNAL_12_26_9` | 167 | 340 | 34,779 | 16,731 | 15,428 | 12,316 | 0 | 2026-03-31 | 2026-08-13 |
| `MACD_HISTOGRAM_12_26_9` | 167 | 340 | 34,779 | 16,731 | 15,428 | 12,316 | 0 | 2026-03-31 | 2026-08-13 |

| Coverage basis | Result |
|---|---:|
| Historical rows | 63,826 |
| Formal instruments | 507 |
| Normalized latest surface rows | 7,098 = 507 × 14 |
| Normalized latest surface SHA-256 | `c0c804dacf173f50f2980fc530b4e1c40888c33f3323e562f29883e1c38b6d9c` |

## Q8–Q9 — continuity behavior

Every current formal indicator is evaluated at indicator-window scope. The
contract preserves:

- `CONTINUITY_FAIL`: known unresolved continuity-breaking event intersects the
  required window; value unavailable.
- `CONTINUITY_UNKNOWN`: authority or scope is incomplete; ordinary formal
  clearance fails closed.
- `EVENT_LOOKUP_UNAVAILABLE`: never interpreted as `NO_EVENT`. If the raw
  input, algorithm, lineage, and MA60 evaluation are otherwise valid, the
  value may be exposed as `FORMAL_WITH_LIMITATION` with explicit limitation
  reason `EVENT_LOOKUP_UNAVAILABLE`.
- Successful no-match means only
  `NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND` for the configured bounded lookup;
  it is not a universal absence claim.

The event matrix in
[`technical-v0-continuity-behavior-matrix.json`](../../reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819/technical-v0-continuity-behavior-matrix.json)
records this behavior separately for all fourteen indicators. The committed
bounded event authority contains 341 identities and 372 event records across
five observed event types; it is not a complete historical corporate-action
authority.

## Q10 — eligibility is not availability

Yes, valid observations are kept separate from the instrument-level MA60
strategy eligibility result. A stock may have formal MA/return/volume/RSI/MACD
values while `technical_eligibility=INELIGIBLE` because its latest close is
below MA60. The normalized surface carries both fields and marks
`strategy_eligibility_is_separate=true`.

Full-universe instrument-level result:

```text
FULL_UNIVERSE_CLASSIFIED_COUNT=507
TECHNICAL_VALID_ELIGIBLE=85
TECHNICAL_INELIGIBLE=127
TECHNICAL_UNAVAILABLE=295
TECHNICAL_ERROR=0
FORMAL_EVIDENCE_AVAILABLE_COUNT=0
FORMAL_EVIDENCE_AVAILABLE_WITH_LIMITATION_COUNT=85
FORMAL_EVIDENCE_BLOCKED_COUNT=422
FORMAL_EVIDENCE_ERROR_COUNT=0
```

The 7,098-row indicator surface contains 2,684 ordinary available values,
2,324 available-with-limitation values, and 2,090 continuity-blocked values
at the latest as-of snapshot. These are indicator-level counts and must not be
substituted for the 507 instrument-level publication routing counts above.

## Q11 — WS3 consumption readiness

Yes, the current additive read surface is sufficiently explicit for future WS3
consumption without look-ahead. Each normalized row carries identity, session,
indicator/version, parameters, required and actual observation windows,
source authority/lineage, continuity state/evidence, event authority,
publication state, availability/limitation reasons, and the strategy
eligibility separation flag.

No database persistence or migration was added. The artifact is a normalized
read-only evidence surface for the next Owner-authorized consumer-integration
step; it is not a recommendation or strategy API.

## Q12 — implementation defects

```text
TECHNICAL_VALUE_RECONCILIATION_PASS=YES
TECHNICAL_VALUE_MISMATCH_COUNT=0
IMPLEMENTATION_DEFECT_COUNT=0
```

The independent real-data reconciliation covered above-MA60, below-MA60,
known-event, lookup-unavailable, successful no-match, and insufficient-history
controls. An initial checker-only precision mismatch was corrected in the
inventory runner: raw returns now use the same 50-digit Decimal comparison
boundary as the canonical runtime. No canonical Technical V0 algorithm or
parameter was changed.

## Q13–Q14 — future Opportunity evidence gaps

The future gap matrix is informational only and does not define or modify
Opportunity A/B/C/D:

| Consumer | Current evidence | Gap category | Gap |
|---|---|---|---|
| Opportunity A — Trend Continuation | MA, distance, RSI, MACD, volume | `DERIVABLE_FROM_EXISTING_DAILY_OHLCV` | MA20 slope/structure state and stronger continuity authority are not formal |
| Opportunity B — Catch-up | Raw 5D/20D return, volume, RSI | `REQUIRES_EXTERNAL_DATA` | PIT cross-sectional relative strength/benchmark authority is not formal |
| Opportunity C — Early Strength | MA, distance, volume ratio, MACD | `REQUIRES_NEW_TECHNICAL_MODULE` | Breakout, pattern, and volume-expansion definitions are not formal |
| Opportunity D — Bearish-Reversal / Rebound | Return, RSI, MACD, distance | `DEFERRED` | Pattern/FVG/supply-demand/reversal semantics remain deferred |
| Shared continuity authority | Bounded event overlay | `REQUIRES_EXTERNAL_DATA` | Complete adjustment/exhaustive no-event authority is not present |

```text
FUTURE_EVIDENCE_GAP_COUNT=5
IMMEDIATE_IMPLEMENTATION_REQUIRED=NO
```

No indicator optimization, threshold search, score, ranking, recommendation,
entry/exit, target, stop-loss, position-sizing, or strategy acceptance was
performed.

## Q15 — smallest defensible next WS2 step

The smallest next step is an Owner-authorized consumer integration of this
existing normalized Technical V0 evidence surface into the intended read
model/consumer boundary, preserving the current contract and explicit
availability states. It is not a new indicator implementation, migration,
frontend inference, Opportunity Engine change, WS3 research run, or Production
activation.

## Required artifacts

- [Indicator manifest](../../reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819/technical-v0-indicator-manifest.json)
- [Coverage summary](../../reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819/technical-v0-indicator-coverage-summary.json)
- [Full-universe evidence surface](../../reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819/technical-v0-full-universe-evidence-surface.csv)
- [Formal evidence contract](../../reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819/technical-v0-formal-evidence-contract.json)
- [PIT quality audit](../../reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819/technical-v0-pit-quality-audit.json)
- [Continuity behavior matrix](../../reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819/technical-v0-continuity-behavior-matrix.json)
- [Future evidence gap matrix](../../reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819/technical-v0-future-evidence-gap-matrix.json)
- [Next-step readiness](../../reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819/technical-v0-next-step-readiness.json)
- [Rerunnable inventory validator](../../scripts/ws2_technical_v0_indicator_inventory.py)

## Validation and safety ledger

```text
FULL_UNIVERSE_RUN_1=PASS; 507 instruments; 7098 rows; mismatch=0; defects=0
FULL_UNIVERSE_RUN_2=PASS; identical normalized surface SHA-256
PIT_AUDIT=PASS; 14/14 safe; future observation and future event invariance pass
KNOWN_EVENT_AND_LOOKUP_CONTROLS=PASS
JSON_ARTIFACTS=PASS
CSV_ARTIFACT_ROWS=PASS; 7098 rows; 507 unique instruments; 14 indicators each
RUFF_INVENTORY_SCOPE=PASS
PY_COMPILE=PASS
GIT_DIFF_CHECK=PASS
SECRET_SCAN_CHANGED_SCOPE=PASS
MIGRATION_EXECUTED=NO
DATABASE_WRITE_EXECUTED=NO
PROVIDER_SCHEDULER_EXECUTED=NO
G1_G2_G3_EXECUTED=NOT_RUN; preserved prior evidence because scope is read-only inventory/evidence audit
G2R_C_EXECUTED=NO
SHARED_G3_EXECUTED=NO
PRODUCTION_MUTATION_EXECUTED=NO
DEPLOY_EXECUTED=NO
PUSH_EXECUTED=NO
WS1_CHANGED=NO
WS3_CHANGED=NO
WS4_CHANGED=NO
NEXT_TASK_CHANGED=NO
NEW_INDICATOR_CREATED=NO
INDICATOR_PARAMETER_CHANGED=NO
MA60_POLICY_CHANGED=NO
TECHNICAL_V0_STRATEGY_SEMANTICS_CHANGED=NO
RELEASE_STATUS=NOT_RUN
PRODUCTION_VERIFICATION=NOT_RUN
```

Owner dirty/untracked state and concurrent worktrees were preserved. The
isolated result was promoted by conflict-free commit-preserving cherry-pick;
no unrelated file was staged or cleaned.

```text
IMPLEMENTATION_STATE=VALIDATED_READ_ONLY_INVENTORY_AND_EVIDENCE_SURFACE
CANONICAL_STATUS=PROMOTED_TO_CANONICAL; owner dirty state preserved; no conflicts
TASK_SOURCE_COMMIT_SHA=a0d4827c0e8c24be3cd0a022405e0226e6da7b84
CANONICAL_PROMOTION_COMMIT=3b171acbf33c08b8579abfc0600aa3504978ecc4
CANONICAL_HEAD_AT_FIRST_PROMOTION=3b171acbf33c08b8579abfc0600aa3504978ecc4
FINAL_CANONICAL_HEAD=RECORDED_IN_FINAL_HANDOFF_AFTER_PROVENANCE_UPDATE
```

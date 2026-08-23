# TASK-REC-A1-COMPLETE-RESEARCH-WINDOW-COVERAGE-AND-FREEZE-REASSESSMENT

## Executive Decision

The existing owner-bounded exports and normalized research dataset are valid for
the bounded rows they contain, but they do not prove complete identity coverage
for the REC-A1 research window. The prior event-presence count of 353 identities
must not be interpreted as 353 covered identities plus 154 no-event identities.

The reassessed identity × event-family × window model is:

| State | Identities | Meaning |
| --- | ---: | --- |
| `COVERED_EVENT` / `EVENT_IDENTITIES` | 353 | At least one normalized authoritative event row exists for the identity in the window. |
| `COVERED_NO_EVENT` / `NO_EVENT_IDENTITIES` | 0 | A completed authoritative empty-set proof exists for every required family. |
| `UNKNOWN` / `UNKNOWN_IDENTITIES` | 154 | The identity has no event row and the bounded export does not prove a complete empty set. |
| `OUTSIDE_SCOPE` | 1,524 rows / 1,125 source identities | Exact source rows outside the lifecycle-gated 507 universe; retained as audit rows and excluded from the canonical dataset. |

Therefore:

- `DATASET_ROWS=372` remains a row count, not a coverage count.
- `COVERED_IDENTITIES=353` means 353 identities have materialized event coverage;
  it does not mean the other 154 identities are `NO_EVENT`.
- `REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO` remains correct.
- `REC_A1_CORE_V0_WALK_FORWARD_AUTHORIZED=NO` remains correct.
- No dummy corporate-action rows, adjusted OHLC, total-return series, trading
  gates, or production mutations were created.

The bounded implementation is authorized only as a research governance and
coverage-semantics artifact. It is not a claim that the corporate-action source
surface is complete.

## Owner Decision and Scope

`OWNER_APPROVAL_STATUS=APPROVED_INTERNAL_RESEARCH_ONLY`

The Owner approval remains limited to TopicPilot internal research use of
confirmed TWSE/TPEx official sources, including bounded retrieval, normalized
research storage, lineage, hashing, checkpoint/replay, research datasets,
backtest/walk-forward use when separately authorized, and post-hoc
`EVENT_EXCLUDED_RAW_V0` episode exclusion. It does not replace exchange terms,
does not authorize prohibited automation, and does not authorize public raw-data
redistribution.

This task resumes from the predecessor import gate. It does not re-audit source
authority or re-fetch either exchange. Predecessor authority and method closure
were reused from:

- `docs/reports/TASK-REC-A1-CORPORATE-ACTION-SOURCE-USE-APPROVAL-AND-HISTORICAL-EVENT-SEMANTICS-CLOSURE.md`
- `docs/reports/TASK-REC-A1-CORPORATE-ACTION-EVENT-EXCLUSION-CLOSURE.md`
- `docs/reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION.md`
- `docs/reports/TASK-REC-A1-CORPORATE-ACTION-TPEX-BOUNDED-ARTIFACT-COVERAGE-CLOSURE.md`
- `docs/reports/TASK-REC-A1-PIT-UNIVERSE-SURVIVORSHIP-AUDIT.md`

## Canonical State

The canonical repository is `C:\Users\acer\Desktop\題材領航\topicpilot-platform`.

| Field | Value |
| --- | --- |
| Canonical branch | `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` |
| Origin main | `26f635b95d8d88fd7ed7e43949583347f3ab5feb` |
| Task implementation pre-SHA | `aa2bc8e206c62e35b76c3385afa53a7a8aca97a8` |
| Task implementation post-SHA | `9afd0a31aa86294bc271af79716b1610b38b494f` |
| Worktree used | `NO` |
| Active unrelated dirty state | Preserved; no reset, stash, clean, or broad staging was used. |

The implementation post-SHA above is the exact research-module/test/coverage-
artifact commit. The documentation report is reconciled in a separate
documentation-only commit after this report is created; that reconciliation does
not change the research implementation state.

## Prior Closure Baseline

The imported normalized dataset remains:

| Field | Value |
| --- | ---: |
| `DATASET_VERSION` | `REC-A1-CA-EVENTS-V0` |
| `DATASET_ROWS` | 372 |
| TWSE normalized rows | 234, including the retained `6806` lifecycle control |
| TPEx normalized rows | 138 |
| Canonical universe | 314 TPE + 193 TWO = 507 |
| Instrument type | `EQUITY` for all canonical identities |
| Reference version | `tw-reference-v1` |
| Universe policy | `LIFECYCLE_GATED_507` |
| Research window | `2026-02-02` through `2026-08-13` |
| Duplicate stable event keys | 0 |
| Invalid identities | 0 |
| Invalid effective dates | 0 |
| Missing lineage | 0 |
| Semantic-hash collisions | 0 |

The owner raw originals remain external and read-only. The normalized dataset
stores semantic records and lineage, not the raw CSV response.

## Coverage Model Reassessment

The coverage unit is now explicitly:

`Coverage(canonical_identity, event_family, research_window)`

with the following states:

| State | Contract |
| --- | --- |
| `COVERED_EVENT` | The bounded source scope is authoritative for the identity/family/window and contains at least one normalized event row. |
| `COVERED_NO_EVENT` | The bounded source scope is authoritative for the identity/family/window and explicitly proves that the event set is empty. |
| `UNKNOWN` | The source, method, authority, or scope is incomplete for the identity/family/window. Absence of a row is not sufficient to change this state. |
| `OUTSIDE_SCOPE` | The source row is outside the canonical lifecycle-gated 507 or otherwise outside the declared scope. It remains audit data and is not canonical dataset data. |

The aggregate identity rule is deterministic:

- `EVENT_IDENTITIES`: any family cell is `COVERED_EVENT`.
- `NO_EVENT_IDENTITIES`: every required family cell is `COVERED_NO_EVENT` and
  no family cell is `COVERED_EVENT`.
- `UNKNOWN_IDENTITIES`: no event is present and at least one required family cell
  is `UNKNOWN`.
- `COVERED_IDENTITIES = EVENT_IDENTITIES + NO_EVENT_IDENTITIES`.

The implementation does not manufacture a negative row in the event dataset.
`COVERED_NO_EVENT` is metadata-only and can only be produced when the source
coverage metadata explicitly lists a completed authoritative empty-set proof for
the family. The current owner exports contain no such complete-empty proof.

## Current Coverage Results

The new metadata-only artifact is:

`reports/TASK-REC-A1-COMPLETE-RESEARCH-WINDOW-COVERAGE-AND-FREEZE-REASSESSMENT/REC-A1-COVERAGE-MATRIX-V0.json`

It contains 4,056 canonical cells (507 identities × 8 event families), with no
raw CSV content and no OHLCV content.

| Metric | Value |
| --- | ---: |
| Canonical identity cells | 4,056 |
| `COVERED_EVENT` cells | 368 |
| `COVERED_NO_EVENT` cells | 0 |
| `UNKNOWN` cells | 3,688 |
| `EVENT_IDENTITIES` | 353 |
| `COVERED_IDENTITIES` | 353 |
| `NO_EVENT_IDENTITIES` | 0 |
| `UNKNOWN_IDENTITIES` | 154 |
| Outside-scope rows | 1,524 |
| Outside-scope source identities | 1,125 |

The difference between 372 event rows and 368 event cells is expected: more than
one event row can belong to the same identity and event family in the window.
The coverage artifact therefore does not collapse row-level event lineage into a
false one-row-per-identity representation.

### Why the 154 identities are UNKNOWN

The TWSE and TPEx files are bounded event exports containing event rows. For an
identity absent from those rows, the exports do not by themselves prove that all
required event-family queries were completed and returned no event. The current
source metadata also has no `complete_empty_set_families` declaration.

Consequently, the reassessment records:

```text
EVENT_IDENTITIES=353
COVERED_IDENTITIES=353
NO_EVENT_IDENTITIES=0
UNKNOWN_IDENTITIES=154
```

This is deliberately stricter than interpreting the absent set as 154
`PASS_NO_EVENT` identities.

## Owner-Bounded Export State

No raw originals were modified or re-fetched.

| Source | Raw rows | Canonical source rows | Source identities | Outside rows | Outside identities | SHA-256 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| TWSE `TWT49U` | 1,035 | 233 | 224 | 802 | 632 | `ED65E408FCD6223E875549E8CB853139B1379A73682CFB18CCA92E2109C0B90A` |
| TPEx `Exright_1150202_1150813.csv` | 853 | 131 | 128 | 722 | 493 | `566F4ACE3E8FED9E0D89C60D0F2471308B38A00C085A97E151E57BBBAC4DF316` |

The TWSE Downloads copy was previously confirmed equivalent to the Desktop copy
after CP950/UTF-8 BOM decoding normalization. The `/mnt/data` path is absent on
the current Windows mount and was not treated as an additional source.

Outside rows are classified only by exact `(market_code, instrument_code)` lookup
against `tw-reference-v1`. They are retained in the predecessor audit artifact
as `OUTSIDE_CANONICAL_507`; suffixes are not used to infer ETF, bond, preferred,
or other product type.

## Event-Family Coverage

The current statuses remain partial or unknown. `PARTIAL` means bounded event
rows are materialized; it does not mean the family is complete for all 507
identities and the whole window.

| Event family | TWSE | TPEx | V0 interpretation |
| --- | --- | --- | --- |
| Cash dividend / ex-dividend | `PARTIAL`, 214 rows | `PARTIAL`, 123 normalized rows | Event-positive rows only; absent identities remain UNKNOWN. |
| Stock dividend / ex-right | `PARTIAL`, 11 rows | `PARTIAL`, 7 normalized rows | Event-positive rows only; absent identities remain UNKNOWN. |
| Rights issue / capital-increase reference reset | `UNKNOWN` | `PARTIAL`, 8 normalized rows | TPEx explicit component fields support the normalized rows; no complete negative scope is proven. |
| Capital reduction | `UNKNOWN` | `UNKNOWN` | Method gap; not `PASS_NO_EVENT`. |
| Split / reverse split / par-value change | `UNKNOWN` | `UNKNOWN` | Method gap; not `PASS_NO_EVENT`. |
| Merger / share conversion / demerger | `UNKNOWN` | `UNKNOWN` | Method gap; not `PASS_NO_EVENT`. |
| Listing / termination / resumption discontinuity | `PARTIAL`, 1 lifecycle control | `UNKNOWN` | The `6806` control remains valid; this is not full lifecycle coverage. |
| Combined ex-right/ex-dividend semantic partial | `PARTIAL`, 8 retained combined rows | `UNKNOWN` | TWSE combined rows are not split by price inference; TPEx explicit component rows are represented in their component families. |

The known method gaps are materially relevant to raw price continuity, volume
continuity, identity continuity, or episode outcome integrity. The policy remains
conservative fail-closed: unresolved event authority is excluded from any
outcome denominator rather than treated as no event.

## Historical Event-Date and PIT Semantics

The normalized event key is anchored to the official effective trading/date field
that causes the price or identity discontinuity. Announcement/publication date,
record date, ex-right/ex-dividend date, reference-price effective date, and
listing/termination date remain distinct fields where available. Announcement
date is not substituted for effective date.

The following prior authority remains unchanged:

```text
EVENT_DATE_SEMANTICS=DETERMINISTIC_PRIMARY_EFFECTIVE_DATE_REQUIRED
TRADING_DECISION_USE=FORBIDDEN
POST_HOC_OUTCOME_INTEGRITY_EXCLUSION=ALLOWED
UNKNOWN_FAIL_CLOSED=YES
```

Corporate-action rows cannot retroactively change signal-date Gate, Rank, or
Trigger facts in Core V0. After an episode has been formed, an authoritative
effective-date overlap may exclude the episode for outcome-integrity purposes.
An excluded episode is not a loss, no-trigger, or zero-return episode and does
not enter T+5/T+10/MFE/MAE/win-rate/expectancy denominators.

## Identity and Lifecycle Mapping

Canonical mapping remains exact and versioned:

```text
REFERENCE_VERSION=tw-reference-v1
UNIVERSE_POLICY=LIFECYCLE_GATED_507
TPE=314
TWO=193
TOTAL=507
INSTRUMENT_TYPE=EQUITY
IDENTITY_MAPPING_STATE=CANONICAL_507_EXACT_MARKET_CODE_INSTRUMENT_LOOKUP
```

TWSE source rows are mapped to `market_code=TPE`; TPEx source rows are mapped to
`market_code=TWO`. Outside rows are not silently dropped and are not included in
the canonical normalized dataset. Lifecycle controls, including `TPE:6806`, are
retained from the canonical reference evidence.

## Lineage, Hash, and Replay Boundary

The normalized owner import continues to pass its existing manifest, checkpoint,
semantic-hash, duplicate, and idempotent-replay checks. The new coverage artifact
adds only derived metadata:

```text
COVERAGE_ARTIFACT_SHA256=97D12273D1FFD9B733D3C0956AF20F48C0FB6BAB4158037EADCEBC009EA59BA8
COVERAGE_CONTENT_HASH=85daa8de3c14f3e0ba26df8aff5167f67c1fbda52201990e4d1c0991e1bdf04c
LOCAL_RESEARCH_STORAGE_STATUS=DERIVED_NORMALIZED_AND_COVERAGE_METADATA_ONLY
HASH_LINEAGE_REPLAY_STATUS=PASS_BOUNDED_IMPORT_AND_COVERAGE_REBUILD
```

The raw CSV originals remain external, read-only, and not stored in the research
dataset. Raw official reproduction and public redistribution remain unapproved.

## Control Cases

The predecessor control cases were re-verified through the current dataset and
coverage model; no complete A1 backtest or walk-forward was run.

| Control | Result | Boundary checked |
| --- | --- | --- |
| `TPE:2330` | `PASS` | Ex-dividend source record maps to the deterministic effective date `2026-06-11`; source lineage and reason code are retained. |
| `TPE:6806` | `PASS` | Listing-termination effective date `2026-06-23` matches canonical lifecycle evidence and remains separate from ex-dividend semantics. |
| Semantic fixtures | `PASS` (6) | Effective-date mapping, event reason, unknown fail-closed behavior, and post-hoc exclusion mapping remain stable. |

No historical OHLCV was modified, adjusted, reconstructed, or joined into this
task.

## Bounded Implementation Changes

The following research-only changes were made:

- Added explicit coverage-state constants and a deterministic identity × family ×
  window matrix builder in
  `services/api/src/topicpilot_api/research/corporate_action_dataset.py`.
- Added aggregate coverage semantics that keep event identities, covered
  identities, no-event identities, unknown identities, and outside-scope audit
  rows separate.
- Extended the freeze gate to accept the identity coverage summary and refuse
  unknown identity coverage.
- Added focused tests proving that absent export rows remain UNKNOWN and that
  `COVERED_NO_EVENT` requires explicit complete-empty proof.
- Added the metadata-only coverage artifact listed above.

No dataset event rows were fabricated to satisfy the 507 universe. No raw source
bytes, raw OHLCV fields, adjusted OHLC, total-return series, Recommendation
Engine code, frontend, API production surface, scheduler, or database schema were
changed.

## Dataset Implementation Authorization and Freeze Gate

The previous task's bounded dataset implementation authorization remains valid in
the following limited form:

```text
DATASET_IMPLEMENTATION_AUTHORIZED=YES_RESEARCH_ONLY_BOUNDED_V0
AUTHORIZED_INGESTION_MODE=MANUAL_OR_BOUNDED_OFFICIAL_RESEARCH_V0
```

That authorization does not imply protocol Freeze. The current reassessment gate
is:

| Gate | Result |
| --- | --- |
| Owner internal research approval | `YES` |
| At least one source-specific path within known restrictions | `YES`, manual/bounded only |
| Full research-window event/no-event classification | `NO`, 154 identities UNKNOWN |
| Deterministic effective-date semantics for materialized rows | `YES` |
| Canonical 507/lifecycle identity mapping | `YES` for accepted rows and audit boundary |
| Lineage/hash/retrieval metadata | `YES` for normalized bounded rows |
| Raw official data public reproduction/redistribution required | `NO`; not authorized |
| Dataset protocol Freeze | `NO` |
| Core V0 walk-forward | `NO` |

Freeze blockers are precise and minimal:

1. `UNKNOWN_IDENTITIES=154`.
2. `NO_EVENT_IDENTITIES=0`; no authoritative complete-empty identity set has
   been demonstrated.
3. Primary event-family cells remain `PARTIAL` or `UNKNOWN` rather than complete.
4. The complete-empty-set validation gate is not satisfied.

The next recommended work is to obtain or validate authoritative, bounded
event-family coverage sufficient to classify the remaining identities as either
`COVERED_EVENT` or explicitly proven `COVERED_NO_EVENT`, then rerun this freeze
reassessment. It is not yet appropriate to start Core V0 walk-forward.

## Validation and Impact

Validation completed:

```text
FOCUSED_PYTEST=23_PASSED
RUFF=PASS
COMPILEALL=PASS
RAW_ORIGINALS_CHANGED=NO
DATASET_CONTENT_VALIDATION=PASS
DUPLICATE_CHECK=PASS
INVALID_IDENTITY_CHECK=PASS
INVALID_EFFECTIVE_DATE_CHECK=PASS
LINEAGE_CHECK=PASS
COVERAGE_REBUILD_DETERMINISTIC=PASS
FREEZE_GATE=UNAUTHORIZED
```

Preserved validation state from the prior closure:

```text
G1=PRESERVED_PASS
G2=PRESERVED_PASS
G3=PRESERVED_PASS
POST_CLOSE_CANARY=PRESERVED_PASS
```

Documentation reconciliation is intentionally limited to this report and the
new derived coverage artifact. `DAILY_PROGRESS`, `ROADMAP`, `WORK_ORDERS`,
`PROJECT_CONTEXT`, and product capability status were not updated because this
is a governance/authority reassessment, not a production capability milestone.

## Final Handoff

```text
TASK_ID=TASK-REC-A1-COMPLETE-RESEARCH-WINDOW-COVERAGE-AND-FREEZE-REASSESSMENT
FINAL_STATUS=REC_A1_COVERAGE_SEMANTICS_REASSESSED_FREEZE_BLOCKED_BY_UNKNOWN_IDENTITIES
CANONICAL_PRE_SHA=aa2bc8e206c62e35b76c3385afa53a7a8aca97a8
CANONICAL_POST_SHA=9afd0a31aa86294bc271af79716b1610b38b494f
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
WORKTREE_USED=NO

OWNER_DECISION=APPROVED_INTERNAL_RESEARCH_ONLY
OWNER_APPROVAL_STATUS=APPROVED_INTERNAL_RESEARCH_ONLY
TWSE_SOURCE_METHOD_STATUS=TWSE_TWT49U_MANUAL_BOUNDED_VALIDATED_PARTIAL
TPEX_SOURCE_METHOD_STATUS=MANUAL_OR_BOUNDED_QUERY_ONLY_VALIDATED_PARTIAL
AUTOMATED_EXTRACTION_STATUS_TWSE=NOT_AUTHORIZED_BY_DEFAULT_SOURCE_METHOD_REVIEW
AUTOMATED_EXTRACTION_STATUS_TPEX=BLOCKED
MANUAL_BOUNDED_INGESTION_STATUS=VALIDATED_OWNER_EXPORT_RESEARCH_ONLY
LOCAL_RESEARCH_STORAGE_STATUS=DERIVED_NORMALIZED_AND_COVERAGE_METADATA_ONLY
HASH_LINEAGE_REPLAY_STATUS=PASS_BOUNDED_IMPORT_AND_COVERAGE_REBUILD
RAW_REPRODUCTION_STATUS=NOT_APPROVED
PUBLIC_REDISTRIBUTION_STATUS=NOT_APPROVED

COVERAGE_MODEL_PREVIOUS=EVENT_PRESENCE_IMPLIED_COVERED
COVERAGE_MODEL_REASSESSED=IDENTITY_EVENT_FAMILY_WINDOW_WITH_EVENT_NO_EVENT_UNKNOWN_OUTSIDE_SCOPE
EVENT_IDENTITIES=353
COVERED_IDENTITIES=353
NO_EVENT_IDENTITIES=0
UNKNOWN_IDENTITIES=154
OUTSIDE_SCOPE_ROWS=1524
OUTSIDE_SCOPE_IDENTITIES=1125
FULL_507_EVENT_ROW_REQUIREMENT=REQUIRED
TWSE_ZERO_EVENT_SEMANTICS=NOT_PROVEN_FOR_ABSENT_IDENTITIES
TPEX_ZERO_EVENT_SEMANTICS=NOT_PROVEN_FOR_ABSENT_IDENTITIES
METHOD_GAPS_REMAINING=CAPITAL_REDUCTION;SPLIT_PAR_VALUE_CHANGE;MERGER_SHARE_CONVERSION;LISTING_TERMINATION_RESUMPTION_COMPLETENESS
METHOD_GAP_MATERIALITY=CONSERVATIVE_FAIL_CLOSED_OUTCOME_INTEGRITY
CONSERVATIVE_UNKNOWN_EVENT_POLICY=UNKNOWN_EVENT_EXCLUDED

DATASET_VERSION=REC-A1-CA-EVENTS-V0
DATASET_ROWS=372
COVERED_EVENT_FAMILIES=TWSE_CASH;TWSE_STOCK;TWSE_COMBINED_SEMANTIC_PARTIAL;TPEX_CASH;TPEX_STOCK;TPEX_RIGHTS;TPE_6806_LIFECYCLE_CONTROL
HISTORICAL_WINDOW_COVERAGE=PARTIAL_353_EVENT_IDENTITIES_154_UNKNOWN
EVENT_DATE_SEMANTICS=DETERMINISTIC_PRIMARY_EFFECTIVE_DATE_REQUIRED
PIT_SEMANTICS=TRADING_DECISION_USE_FORBIDDEN_POST_HOC_OUTCOME_EXCLUSION_ALLOWED
IDENTITY_MAPPING_STATE=CANONICAL_507_EXACT_MARKET_CODE_INSTRUMENT_LOOKUP
REFERENCE_PRICE_AUTHORITY=OFFICIAL_SOURCE_FIELD_ONLY
CONTROL_CASES=2330_PASS;6806_PASS;SEMANTIC_FIXTURE_6_PASS
UNKNOWN_FAIL_CLOSED=YES
EVENT_EXCLUDED_RAW_POLICY=READY
TRADING_DECISION_USE=FORBIDDEN
POST_HOC_OUTCOME_INTEGRITY_EXCLUSION=ALLOWED

REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO_UNDER_CURRENT_FULL_COVERAGE_GATE
REC_A1_CORE_V0_WALK_FORWARD_AUTHORIZED=NO
FREEZE_BLOCKERS=UNKNOWN_IDENTITIES_154;NO_COMPLETE_EMPTY_SET_PROOF;PARTIAL_OR_UNKNOWN_EVENT_FAMILIES
NEXT_RECOMMENDED_TASK=COMPLETE_507_EVENT_OR_AUTHORITATIVE_NO_EVENT_COVERAGE_AND_REASSESS_FREEZE

REPORT_CREATED=YES
DAILY_PROGRESS_UPDATED=NO
APPLICATION_CODE_CHANGED=YES_RESEARCH_ONLY_COVERAGE_SEMANTICS
DATABASE_MUTATION=NO
HISTORICAL_OHLCV_CHANGED=NO
ADJUSTED_OHLC_CREATED=NO
TOTAL_RETURN_CREATED=NO
RECOMMENDATION_ENGINE_CHANGED=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
G1=PRESERVED_PASS
G2=PRESERVED_PASS
G3=PRESERVED_PASS
POST_CLOSE_CANARY=PRESERVED_PASS
```

The task stops here. Dataset protocol Freeze and Core V0 walk-forward remain
closed until the full research-window coverage is authoritative and validated.

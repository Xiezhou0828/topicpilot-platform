# TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820

## Closure status

```text
TASK_ID=TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820
TASK_FINAL_STATUS=COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS
SOURCE_CANONICAL_HEAD=f93c33b892e03a76542d2a5688b28480fa1a3365
TASK_COMMIT=074c827ac1ff2a4611b1e75623edd78af8f51d8c
FINAL_CANONICAL_HEAD=RECORDED_IN_FINAL_CANONICAL_HANDOFF
IMPLEMENTATION_STATE=IMPLEMENTED
VALIDATION_STATE=VALIDATED
CANONICAL_STATUS=CANONICALIZED
CANONICAL_RECONCILIATION_DISPOSITION=CANONICALIZED
CLOSURE_REPORT_SOURCE_COMMIT=115338e260596f6f21580014baf449c0165447e7
CANONICAL_PROMOTION_SOURCE_COMMITS=074c827ac1ff2a4611b1e75623edd78af8f51d8c,115338e260596f6f21580014baf449c0165447e7
CANONICAL_PROMOTION_METHOD=COMMIT_PRESERVING_CHERRY_PICK
RELEASE_STATUS=NOT_RUN
PRODUCTION_VERIFICATION=NOT_RUN
```

This is WS2-E2 only. It contractifies the already canonicalized WS2-E1
Technical V0 evidence surface and closes the current 603-universe mainline
boundary. It does not rerun E1, create new indicator semantics, create an API
route, add persistence, change UI, alter strategy meaning, or change
`NEXT_TASK`.

## Source and upstream provenance

```text
SOURCE_FOUNDATION_VERSION=sdf-603-ohlcv-2y.v1
SOURCE_FOUNDATION_INSTRUMENT_COUNT=603
SOURCE_FOUNDATION_TPE_COUNT=370
SOURCE_FOUNDATION_TWO_COUNT=233
SOURCE_FOUNDATION_OHLCV_COUNT=288881
SOURCE_FOUNDATION_WINDOW=2024-08-13..2026-08-13
SOURCE_FOUNDATION_SHA256=e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4
SOURCE_FOUNDATION_AUTHORITY_CONTENT_SHA256=fe1a51015d48d64b28007d36e291bed59085e7beacf5599ee5d5a35569747fcf
SOURCE_READ_MODEL=topicpilot_api.historical_read_model.read_historical_bars
SOURCE_PROJECTION=topicpilot.vw_daily_market_observations
SOURCE_ADJUSTMENT_AUTHORITY=UNKNOWN_RAW_ONLY

SOURCE_E1_TASK=TASK-WS2-E1-603-UNIVERSE-TECHNICAL-V0-EXPANDED-QUALIFICATION-RESUME-AFTER-SOURCE-CONTRACT-UNBLOCK-20260820
SOURCE_E1_CANONICAL_HEAD=8d062d564e64a943318b5a124835470e3779a207
SOURCE_E1_FINAL_CANONICAL_HEAD=f93c33b892e03a76542d2a5688b28480fa1a3365
SOURCE_E1_EVIDENCE_ROW_COUNT=4044334
SOURCE_E1_EVIDENCE_ARTIFACT_SHA256=48bdc38b9da4e2ba7e298f5341d04ad5dd11475c6019df1ac80593c9858ec254
SOURCE_E1_EVIDENCE_ARTIFACT_SIZE_BYTES=6726285286
SOURCE_E1_EVIDENCE_ARTIFACT_STORAGE=GIT_LFS
SOURCE_E1_NORMALIZED_AGGREGATE_SHA256=3caca0fb2cd0e05f14603da3fcf2d3febc4e92fb77088b74481256cdf4b38012
SOURCE_E1_STATUS=COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS
```

E1 bounded limitations are preserved: `QUARANTINE=144`, `NO_DATA=142`,
`LIFECYCLE_SKIP=41`, `HARD_ERROR=0`, `PIT_RECONSTRUCTABLE=603/603`, and
`MA60_HISTORICAL_INSTRUMENT_COVERAGE=602/603`. The LFS CSV remains a
validation/reproducibility artifact and is not a runtime provider, API backing
store, or mandatory consumer dependency.

## D1-D4 decisions

### D1 — Event-bounded, indicator-level continuity

Accepted as the provider/consumer rule. Each required window carries one of
the canonical states `CONTINUITY_PASS_BOUNDED`, `CONTINUITY_FAIL`, or
`CONTINUITY_UNKNOWN`. `CONTINUITY_FAIL` and `CONTINUITY_UNKNOWN` fail closed;
the latter is never inferred to be no event. A no-row/no-data event lookup is
not `NO_EVENT`. Explicit bounded lookup limitations remain visible as
`FORMAL_WITH_LIMITATION` only when the canonical event-aware policy allows it;
the new reference provider rejects a missing continuity envelope as ordinary
unknown/unavailable.

### D2 — Frozen Technical V0 contract

The 14 existing IDs are reused exactly: `MA5`, `MA10`, `MA20`, `MA60`,
`DISTANCE_TO_MA20`, `RAW_CLOSE_RETURN_5D`, `RAW_CLOSE_RETURN_20D`,
`VOLUME_MA5`, `VOLUME_MA20`, `VOLUME_RATIO_20`, `RSI14`,
`MACD_12_26_9`, `MACD_SIGNAL_12_26_9`, and `MACD_HISTOGRAM_12_26_9`.
The provider exposes their existing algorithm IDs, parameter sets, minimum
observations, warm-up windows, Decimal/rounding policy, and accepted-session
semantics. No indicator or parameter was created or changed.

### D3 — Product boundary

The closed chain is Observation → Continuity/Eligibility → Technical Evidence.
The provider output contains no strategy acceptance, recommendation, ranking,
opportunity, or trade semantics. Advanced Technical remains deferred, and
daily OHLCV is not Order Flow authority.

### D4 — PIT, as-of, lineage, and publication binding

Every record binds logical identity, version identity, source identity, value
or availability reason, session/as-of, required and actual observation
windows, continuity evidence, publication/availability state, PIT status,
source lineage, and a stable lineage reference. The bounded reference request
filters observations and future event knowledge at the requested session/as-of
boundary. `PIT_SAFE` requires a prefix-bounded request with no future
observation or silent revision backfill.

## Authority audit and readiness matrix

| Requirement | Evidence | Result |
| --- | --- | --- |
| 603 active source identity | E1 source-contract manifest; source SHA and authority SHA above | `PASS` |
| Raw/adjustment semantics | canonical read model and E1 `UNKNOWN_RAW_ONLY` | `PASS_WITH_BOUNDED_LIMITATION` |
| Event continuity | existing bounded continuity evaluator; missing authority is `UNKNOWN` | `PASS` for contract; no universal no-event claim |
| Indicator identity/version | canonical policy `v4` and E1 14-indicator manifest | `PASS` |
| RSI/MACD warm-up | existing implementation and focused tests: RSI 15, MACD line 26, signal/histogram 34 | `PASS` |
| PIT/as-of | E1 PIT audit plus bounded future-prefix provider tests | `PASS` |
| Source lineage | existing V2 canonical observation chain plus compact lineage hash | `PASS` |
| 6.7 GB physical artifact | E1 LFS artifact preserved as validation-only | `OPTIONAL_OPTIMIZATION`, not a gap |

The audit distinguishes `CONTINUITY_UNKNOWN` from “no event authority” and
does not block the whole mainline merely because complete corporate-action
authority is not present for every historical window. The remaining future
storage/scale improvement is not a mandatory Technical V0 gap.

## Required artifacts

Architecture authority:

- `docs/architecture/STOCK_TECHNICAL_V0_FORMAL_EVIDENCE_PROVIDER_CONSUMER_CONTRACT.md`
- `docs/architecture/README.md` navigation link

Machine-readable artifacts:

- `reports/TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820/ws2-e2-provider-contract-manifest.json`
- `reports/TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820/ws2-e2-consumer-contract-manifest.json`
- `reports/TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820/ws2-e2-evidence-identity-version-contract.json`
- `reports/TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820/ws2-e2-availability-publication-contract.json`
- `reports/TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820/ws2-e2-pit-asof-contract.json`
- `reports/TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820/ws2-e2-lineage-contract.json`
- `reports/TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820/ws2-e2-evidence-physical-storage-assessment.json`
- `reports/TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820/ws2-e2-reference-provider-validation.json`
- `reports/TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820/ws2-e2-representative-consumer-validation.json`
- `reports/TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820/ws2-e2-ws3-consumer-compatibility.json`
- `reports/TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820/ws2-e2-future-adapter-readiness.json`
- `reports/TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820/ws2-e2-mainline-closure-readiness.json`

Reference implementation and focused contract tests:

- `services/api/src/topicpilot_api/technical_v0_evidence_contract.py`
- `services/api/tests/test_technical_v0_evidence_contract.py`

## Validation

```text
PROVIDER_CONTRACT_SCHEMA=PASS
CONSUMER_CONTRACT_SCHEMA=PASS
IDENTITY_VERSION=PASS
AVAILABILITY_SEMANTICS=PASS
PIT_ASOF=PASS
LINEAGE=PASS
CONTINUITY=PASS
WARMUP=PASS
TPE_REPRESENTATIVE=PASS
TWO_REPRESENTATIVE=PASS
INELIGIBLE_REPRESENTATIVE=PASS
UNAVAILABLE_REPRESENTATIVE=PASS
PIT_LIMITED_REPRESENTATIVE=PASS
HISTORICAL_LOOKUP=PASS
BATCH_LOOKUP=PASS
FUTURE_LEAKAGE_CONTROL=PASS
EVIDENCE_ONLY_BOUNDARY=PASS
WS3_COMPATIBILITY_PROBE=PASS
FOCUSED_TESTS=33_PASS
COMPILE=PASS
RUFF=PASS
JSON_PARSE=12_FILES_PASS
GIT_DIFF_CHECK=PASS
SECRET_SCAN=PASS
FULL_BACKEND_SUITE=NOT_RUN
FULL_BACKEND_SUITE_REASON=docs_contract_and_bounded_domain_scope; focused affected tests are the validation gate
```

No PostgreSQL mutation, G1/G2/G3, Canary, provider refetch, E1 replay, or
Production check was rerun. Preserved E1 source/PIT/lineage evidence remains
the authority because the E2 write set does not reach those protected
boundaries. These states are `NOT_RUN` / `NOT_RERUN`, not new PASS claims.

## Closure routing

```text
TECHNICAL_V0_PROVIDER_CONTRACT_DEFINED=YES
TECHNICAL_V0_CONSUMER_CONTRACT_DEFINED=YES
TECHNICAL_V0_EVIDENCE_IDENTITY_DEFINED=YES
TECHNICAL_V0_VERSION_CONTRACT_DEFINED=YES
TECHNICAL_V0_AVAILABILITY_CONTRACT_DEFINED=YES
TECHNICAL_V0_PIT_ASOF_CONTRACT_DEFINED=YES
TECHNICAL_V0_LINEAGE_CONTRACT_DEFINED=YES
REFERENCE_PROVIDER_IMPLEMENTED=YES
REFERENCE_PROVIDER_VALIDATED=YES
REPRESENTATIVE_CONSUMER_VALIDATED=YES
WS3_TECHNICAL_V0_CONSUMER_COMPATIBLE=YES
MANDATORY_TECHNICAL_V0_MAINLINE_GAP_COUNT=0
FUTURE_ENGINEERING_OPTIMIZATION_COUNT=1
PHYSICAL_STORAGE_FOLLOWUP_DISPOSITION=OPTIONAL_OPTIMIZATION
ADVANCED_TECHNICAL_DEFERRED=YES

FULL_E1_RECONSTRUCTION_RERUN=NO
FULL_4M_EVIDENCE_REGENERATION=NO
NEW_INDICATOR_CREATED=NO
INDICATOR_PARAMETER_CHANGED=NO
MA60_POLICY_CHANGED=NO
STRATEGY_SEMANTICS_INTRODUCED=NO

DATABASE_MUTATION=NO
API_ROUTE_CREATED=NO
UI_CHANGED=NO
PRODUCTION_MUTATION=NO
DEPLOY=NO
RELEASE=NO
PUSH=NO
WS1_CHANGED=NO
WS3_CHANGED=NO
WS4_CHANGED=NO
NEXT_TASK_CHANGED=NO

WS2_TECHNICAL_V0_MAINLINE_CLOSED=YES
READY_FOR_WS2_POST_V0_ROUTING=YES
TASK_ROUTING_OUTCOME=READY_FOR_WS2_POST_V0_ROUTING
```

The allowed disposition is `COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS`. The
bounded limitations are explicit and consumer-visible; no mandatory
Technical V0 mainline gap remains. This does not mean Production deployed,
API published, UI complete, Technical V1 complete, Advanced Technical
complete, or strategy validated.

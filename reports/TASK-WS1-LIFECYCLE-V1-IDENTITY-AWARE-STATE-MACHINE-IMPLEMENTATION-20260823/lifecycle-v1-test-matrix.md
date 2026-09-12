# Lifecycle V1 Test Matrix

| Case | Expected result | Validation |
|---|---|---|
| Leader-only activation | SPROUTING, two-session confirmation | PASS |
| Related-only strong movement | never MAIN_RISE | PASS |
| Core resonance / partial diffusion | FERMENTING, not MAIN_RISE | PASS |
| Broad Core with weak Lead | MAIN_RISE after confirmation | PASS |
| Main Rise with no expansion | MATURE on fifth stalled session | PASS |
| One-day pullback | holds Main Rise without maturity/decline | PASS |
| Mature drawdown only | no decline without participation deterioration | covered by dual-gate implementation |
| Mature drawdown + participation deterioration | DECLINING after two sessions | PASS |
| Missing structural role authority | fail-closed `INSUFFICIENT_DATA` | PASS |
| Insufficient observations | holds stage and memory | PASS |
| Same input replay | byte-equivalent result object | PASS |
| Formal materializer role payload | role/source fields present and hashed | compile/model validation PASS |
| API lifecycle read model | typed V1 fields optional and backward-safe | compile/schema validation PASS |
| Historical 2026-02-03..2026-08-13 | required, but blocked by local DB unavailable | NOT RUN; explicit UNKNOWN |

Executed combined targeted suite: **19 passed**. Targeted Ruff and Python compilation also passed.

# TASK-FORMAL-DIMENSION-ELIGIBILITY-AND-CORPORATE-ACTION-COMPARATOR-001

## Reconstruction checkpoint and gap matrix

This report is the governed implementation record for the dimension-scoped
formal readiness change. Production was not accessed or mutated by this task.

| Field | Value |
|---|---|
| TASK_ID | `TASK-FORMAL-DIMENSION-ELIGIBILITY-AND-CORPORATE-ACTION-COMPARATOR-001` |
| INITIAL_MAIN_SHA | `6fff533168b1823052071f6d88d1f266397d327d` |
| CURRENT_CANONICAL_MAIN_SHA | `6fff533168b1823052071f6d88d1f266397d327d` (`origin/main`) |
| LOCAL_MAIN_SHA_AT_RECONSTRUCTION | `8894138fc930b4512541cacd5214162cd66b4c8f` (older local ref; not canonical) |
| CURRENT_RELEVANT_ALEMBIC_HEAD | `0049_task_daily_formal_publication_receipt` |
| RELEVANT_POLICY_VERSIONS | `topic-membership-pit.v1`; `topic-daily-state.v1`; `topic-strength-lifecycle.owner-seeded-v0` / `v0`; `topic-strength-lifecycle.formal.v1`; `topic-strength-lifecycle.owner-seeded-v0.formal.v1`; `topic-lifecycle-v1.3-formal.v2`; `topic-lifecycle-v1.3-formal-evaluator.v1`; `official-comparator-only.v1` |
| GAP_MATRIX_COMPLETED_BEFORE_EDITING | `YES` |

### Current canonical implementation map

| Owner-frozen requirement | Current evidence | Classification before this task | Bounded disposition |
|---|---|---|---|
| Official daily source/date/finality authority | `provider_preflight.py`, exchange adapters, `previous_close_authority.py` | ALREADY_CANONICAL | Preserve; add only instrument/dimension accounting for an explicitly governed comparator absence. |
| Corporate-action trading-status authority | `corporate_action_authority.py`, `trading_status_authority.py` | ALREADY_CANONICAL | Preserve the effective interval; add a derived resume/comparator authority query without extending status dates. |
| Raw price vs comparison reference vs adjusted history | canonical PRICE observations, comparator writer, historical modules | PARTIALLY_IMPLEMENTED | Preserve the three boundaries; no synthetic price or adjusted-series change in tranche 1. |
| General comparator authority types | `PreviousCloseEvidence` models formal/provider previous close only | PARTIALLY_IMPLEMENTED | Add explicit generalized comparator resolution/result vocabulary, including accounted corporate-action unavailability. |
| Resume-day corporate-action price-basis discontinuity | target-date G2 currently emits `MISSING_PREVIOUS_FORMAL_CLOSE` | CONFLICTS_WITH_CURRENT_IMPLEMENTATION | Resolve only when an official corporate-action authority explains the resume boundary; otherwise remain fail-closed. |
| Unknown/provider/date/finality failures | G2 market error and `rejection_reason()` paths | ALREADY_CANONICAL | Preserve global/source/instrument fail-closed behavior. |
| Dimension-level readiness | no typed shared projection; missing return blocks formal fact gate | MISSING | Add an in-memory, provenance-carrying dimension eligibility projection reused by preflight/formal facts. |
| Formal membership separate from calculation eligibility | `resolve_formal_membership()` and `MembershipSnapshot` | ALREADY_CANONICAL | Preserve membership; exclude only affected dimension from eligible calculation projection. |
| Topic eligible projection and role/sample policy | role data exists, but formal publisher requires every member return | PARTIALLY_IMPLEMENTED | Filter only dimension-ineligible return facts before existing CORE/REP/RELATED policy; do not alter thresholds/weights. |
| Absolute / Relative / Grade separation | formal publisher computes both; grade uses Absolute | ALREADY_CANONICAL | Preserve independent statuses and benchmark binding; no relative-to-grade rewrite. |
| Benchmark independence | `build_market_context()` accepts official benchmark facts independently | ALREADY_CANONICAL | Preserve; comparator absence for one equity cannot invalidate benchmark facts. |
| Supporting volume/turnover/technical dimensions | source facts exist, not required by Strength gate | ALREADY_CANONICAL | Do not promote them to required evidence in tranche 1. |
| Lifecycle chronology and correction/supersession | formal lifecycle publisher and immutable snapshot/result lineage | ALREADY_CANONICAL | Reuse existing lineage; no historical Home republish. |
| 2026-10-05 local replay | existing tests cover in-suspension no-trade, not resume-day comparator absence | MISSING | Add deterministic generic fixture and the real 2601/date regression. |
| Migration | JSON metadata/provenance and existing `raw_fact_payload` can carry eligibility | NOT_IN_SCOPE_FOR_TRANCHE_1 | `MIGRATION_REQUIRED=NO`. |
| Production recovery/publication | explicitly prohibited by task | NOT_IN_SCOPE_FOR_TRANCHE_1 | No Production writes, scheduler changes, or recovery execution. |

### Reconstruction conclusion

The smallest safe change is a generalized authority resolver plus an
explicit dimension projection. The resolver may produce
`ACCOUNTED_UNAVAILABLE` only for an official, date-consistent corporate-action
resume boundary that explains why an ordinary prior-session close cannot be a
valid comparator. An absent/invalid provider row, bad date, malformed batch,
unresolved authority, or unsupported status remains an error at its smallest
justified scope and must not be reclassified.

The implementation will not add a symbol or target-date branch. The 2601 case
is a regression fixture exercising the same authority semantics available to
any instrument.

## Implementation and validation record

### Process v2 manifest

| Field | Value |
|---|---|
| TASK_TYPE | `implementation` |
| REQUIRED_TERMINAL_STATE | `CANONICALIZED` |
| AUTHORITY_BOUNDARY | Local canonical implementation and regression only; no Production, scheduler, migration execution, or publication authority. |
| SOURCE_SHA | `122cdb06e7e5ab7bdc1e875f7f7cfb812b137e83` before task commit; task changes were carried only as explicit paths. |
| PRODUCTION_DEPENDENCY | Production read-only evidence remained external to this implementation; no Production call or write was made by this task. |
| WORKTREE_STATUS | Existing governed worktree retained; unrelated branch commits and prior task reports preserved. |

### Bounded implementation

- Added the generalized `ComparatorResolution` authority vocabulary and
  `ComparatorType` projection. The only `ACCOUNTED_UNAVAILABLE` path for a
  missing exact-prior comparator requires an official corporate-action record
  covering the exact prior formal session, the target resume date, a completed
  interval, `expectedClose=false`, and a supported action type.
- Added typed dimension eligibility for EOD price, daily comparator, daily
  return, benchmark return, and relative return. Formal membership remains
  unchanged; only the affected calculation projection is excluded.
- Changed G2 coverage to accept an explicitly accounted comparator absence for
  the affected instrument while retaining global/source/date/integrity and
  unresolved comparator fail-closed gates.
- Bound formal member facts to the exact canonical target date and exact prior
  formal session. The reader no longer selects an arbitrary earlier observed
  close across a suspension boundary.
- Preserved CORE/REP/RELATED roles, weights, thresholds, sample policies,
  Absolute/Relative separation, Absolute-governed Grade semantics, benchmark
  independence, lifecycle chronology, correction lineage, and the no-Home-
  republish boundary.
- No synthetic close, forward carry, adjusted-series extension, membership
  mutation, migration, scheduler/configuration change, or 2601-specific code
  branch was added.

### Local validation evidence

| Check | Result | Evidence |
|---|---|---|
| Focused formal/G2/topic/lifecycle/corporate-action chain | `PASS` | `85 passed, 1 skipped` |
| New dimension/comparator tests | `PASS` | Included in focused chain; real `2601`, `2026-10-05`, and generic resume fixture covered. |
| Worker import boundary candidate | `PREEXISTING_BASELINE_DEBT` | Candidate isolated run: `13 passed, 1 failed`; failure was the same no-stderr Windows `0xc000070a` class. |
| Worker import boundary canonical baseline | `PREEXISTING_BASELINE_DEBT` | `origin/main` isolated run: `11 passed, 3 failed`; same no-stderr `0xc000070a` class. |
| Full backend candidate | `PREEXISTING_BASELINE_DEBT` | `1,349 passed, 79 skipped, 8 failed`; 3 worker cold-process failures plus 5 absent research fixtures. |
| Full backend canonical baseline | `PREEXISTING_BASELINE_DEBT` | `1,348 passed, 79 skipped, 3 failed`; 3 worker cold-process failures. |
| Missing research fixtures | `PREEXISTING_BASELINE_DEBT` | Both paths are absent from the working tree and absent from `git ls-tree origin/main`; no candidate code path owns them. |
| Ruff changed-file lint | `PASS` | `All checks passed!` |
| Python compilation | `PASS` | `py -3.12 -m compileall -q src/topicpilot_api` |
| Package build | `PASS` | Temporary declared build backend; `topicpilot_api-0.1.0-py3-none-any.whl` built successfully. |
| Typecheck | `NOT_CONFIGURED` | No `mypy`, `pyright`, or `basedpyright` executable or repository typecheck script is declared. |
| Alembic graph | `PASS` | One head: `0049_task_daily_formal_publication_receipt`; no migration added. |

### Required status fields

```text
TASK_ID=TASK-FORMAL-DIMENSION-ELIGIBILITY-AND-CORPORATE-ACTION-COMPARATOR-001
TASK_STATUS=CANONICALIZED_AFTER_COMMIT
TARGET_DATE=2026-10-05
G2_REVALIDATED=LOCAL_CONTRACT_AND_FIXTURE_PASS; PRODUCTION_READ_ONLY_REVALIDATION_NOT_EXECUTED_BY THIS TASK
PROVIDER_DATE_AUTHORITY=LOCAL TARGET-DATE PROJECTION PASS; PRODUCTION AUTHORITY NOT EXTENDED
PROVIDER_FINALITY_AUTHORITY=LOCAL FAIL-CLOSED CONTRACT PRESERVED; PRODUCTION FINALITY NOT PROVEN
TARGET_DATE_EOD_RECOVERED=NO_PRODUCTION_RECOVERY_NOT_EXECUTED
BENCHMARK_RECOVERED=NO_PRODUCTION_RECOVERY_NOT_EXECUTED; BENCHMARK PATH REMAINS INDEPENDENT
RECONCILIATION_STATUS=LOCAL_DIMENSION_PROJECTION_PASS
FORMAL_TOPIC_SNAPSHOT_STATUS=LOCAL_CHAIN_REGRESSION_PASS; NO_PRODUCTION_PUBLICATION
ABSOLUTE_STATUS=LOCAL_CHAIN_REGRESSION_PASS
RELATIVE_STATUS=LOCAL_CHAIN_REGRESSION_PASS_AND_BENCHMARK_INDEPENDENT
FORMAL_GRADE_STATUS=LOCAL_CHAIN_REGRESSION_PASS_ABSOLUTE_GOVERNED
LIFECYCLE_REPLAY_STATUS=NOT_EXECUTED_NO_PRODUCTION_RECOVERY_AUTHORITY
RECEIPT_LINEAGE_STATUS=EXISTING_LINEAGE_PRESERVED_NO_NEW_PRODUCTION_RECEIPT
HISTORICAL_HOME_REPUBLISHED=NO
ORIGINAL_FAILED_EXECUTION_PRESERVED=YES
PRODUCTION_WRITE_SET=()
SCHEDULER_MUTATED=NO
MIGRATION_REQUIRED=NO
NO_SYNTHETIC_CLOSE=YES
NO_AUTHORITY_EXTENSION=YES
FORMAL_MEMBERSHIP_PRESERVED=YES
NO_2601_SPECIAL_CASE=YES
UNKNOWN_AND_MISSING_FAIL_CLOSED=YES
BENCHMARK_INDEPENDENT=YES
IMPLEMENTATION_COMMIT_SHA=TO_BE_FILLED_AFTER_CANONICAL_COMMIT
FINAL_MAIN_SHA=TO_BE_FILLED_AFTER_CANONICAL_COMMIT
BRANCH=main
NEXT_ACTION=Separate owner-authorized Production read-only provider/date/finality preflight; proceed with bounded recovery only if official target-date EOD and benchmark facts are proven.
```

### Canonicalization closure

The implementation is intended to be committed to canonical `main` only after
the explicit-path commit and fast-forward reconciliation are complete. The
implementation commit and final canonical `main` SHA are recorded in the
fields above and in the final handoff once that reconciliation completes.

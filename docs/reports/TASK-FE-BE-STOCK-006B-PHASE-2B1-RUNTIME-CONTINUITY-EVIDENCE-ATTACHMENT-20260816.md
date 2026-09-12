# TASK-FE-BE-STOCK-006B-PHASE-2B1-RUNTIME-CONTINUITY-EVIDENCE-ATTACHMENT-20260816

**Workstream:** `WS2 / Stock Technical Publication / Phase 2B1`
**Task ID:** `TASK-FE-BE-STOCK-006B-PHASE-2B1-RUNTIME-CONTINUITY-EVIDENCE-ATTACHMENT-20260816`
**Review date:** `2026-08-16`
**Final status:** `IMPLEMENTED_AND_VALIDATED / CANONICALIZED`

## 1. Scope and routing

This task attaches the existing canonical lifecycle reference carrier to the
existing historical read model. It does not redesign Technical V0, alter the
continuity policy, create a second evaluator, or promote REC-A1 research data
to exchange-grade corporate-action authority.

```text
TASK_ID=TASK-FE-BE-STOCK-006B-PHASE-2B1-RUNTIME-CONTINUITY-EVIDENCE-ATTACHMENT-20260816
TECHNICAL_POLICY_VERSION=stock-technical-v0-policy.v2
PHASE_2B_ANCESTOR_VERIFIED=YES
TECHNICAL_V0_IMPLEMENTATION_CHANGED=NO
TECHNICAL_ALGORITHMS_CHANGED=NO
CONTINUITY_POLICY_CHANGED=NO
RUNTIME_CONTINUITY_ATTACHMENT_IMPLEMENTED=YES
RUNTIME_ATTACHMENT_STATE=IMPLEMENTED_LIFECYCLE_FAMILY_BOUNDED
EVIDENCE_CARRIER=topicpilot.reference_instrument_lifecycles
ATTACHMENT_POINT=read_historical_bars -> attach_bounded_continuity_evidence -> existing Technical V0 evaluator
INDICATOR_LEVEL_CONTINUITY=YES
SYMBOL_LEVEL_GLOBAL_BLOCK=NO
EMPTY_EVENT_IMPLIES_NO_EVENT=NO
PASS_BOUNDED_RUNTIME_SUPPORTED=NO_BY_LIFECYCLE_ONLY_CARRIER
FAIL_RUNTIME_SUPPORTED=YES
UNKNOWN_RUNTIME_SUPPORTED=YES
ROUTING_OUTCOME=IMPLEMENTED_BUT_REAL_WINDOWS_REMAIN_AUTHORITY_BOUNDED
```

The runtime carrier is intentionally narrow: it carries canonical
`DELISTED`, `SUSPENDED`, and `TERMINATED` lifecycle discontinuities with their
existing `evidence_id`, effective date, identity, and reference-data lineage.
It marks coverage as partial, so the existing evaluator can fail closed on a
known intersecting event but cannot infer an all-family empty set.

## 2. Phase A provenance and authority audit

```text
SOURCE_BASELINE_SHA=1acac134cebc994fdab350aeeb64fe5e997008bf
CANONICAL_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
SOURCE_BRANCH=codex/task-stock-technical-phase2b1-20260816
SOURCE_WORKTREE=C:\Users\acer\Documents\Codex\ws2b1-20260816
OWNER_TRACKED_STATUS_LINES=18
OWNER_UNTRACKED_STATUS_LINES=156
OWNER_STATUS_FINGERPRINT=36b44bd721b1e4f2bd9dc780acc913ce78ab98639a766eaf8855b67645908033
OWNER_STATE_PRESERVED=YES
PHASE_2B_ANCESTOR=a811ca14293bfb172e3a97b1d1d662f5f1ae6ff1
SOURCE_IMPLEMENTATION_COMMIT=ac174930d966724405dde70d698ed0d84b695417
CANONICAL_PRE_SHA=f936d9f64811d2331c37a8cb85a13b7eca0a40c8
CANONICAL_PROMOTION_COMMIT=d474025d0b21a94010ae2028dbe20856c36c5c62
CANONICAL_POST_SHA=2f384f2b19280148d014c8dd4e98cf215052eeaa
```

The canonical branch advanced after Phase 2B through concurrent WS3 closure
commits. The Phase 2B implementation remains an ancestor of the current
canonical HEAD; no reset or rollback was performed. Existing worktrees and the
owner's dirty/untracked state were preserved.

The NEXT_TASK file is outside this repository at
`C:\Users\acer\Desktop\題材領航\AI\NEXT_TASK.md`. Cold-start hashes match the
previous reconciliation exactly:

```text
NEXT_TASK_RAW_SHA=FF640C735A2CDD4D8238157B287D293D0385B67F673150249A90F49661FFEB70
NEXT_TASK_NORMALIZED_SHA=0E52696AAF6809DDFB7AEE7298F532FEDBD79E16F9B2E584EC6919F15CA417DE
NEXT_TASK_SEMANTIC_CHANGE=NO
NEXT_TASK_CHANGED_BY_THIS_TASK=NO
```

## 3. Existing evidence and carrier decision

The existing canonical carrier is the read-only
`topicpilot.reference_instrument_lifecycles` table already queried by
`read_historical_bars`. It supplies `status_code`, `effective_from`,
`effective_to`, and `evidence_id` for lifecycle discontinuities. The new
attachment helper converts that existing row into the shape already consumed
by `evaluate_bounded_continuity`.

The committed REC-A1 artifacts were audited but are not attached to runtime:

- TWSE bounded export: 224 canonical identities / 233 canonical rows.
- TPEx bounded export: 128 canonical identities / 131 canonical rows.
- REC-A1 matrix: 4,056 identity-family cells; 368 `COVERED_EVENT`, 3,688
  `UNKNOWN`, and zero authoritative `COVERED_NO_EVENT` cells.
- The artifacts are explicitly research-only, partial, method-dependent, and
  retain 154 reviewed UNKNOWN identities. Their absence of rows cannot prove
  an empty event family.

The adjustment reference files only enumerate `ADJUSTED`, `UNADJUSTED`, and
`UNKNOWN` states; they do not carry event records or exact window authority.
No adjusted-price engine, synthetic adjustment, REC-A1 freeze change, or new
corporate-action platform was added.

## 4. Runtime contract and implementation

The existing data flow is now:

```text
canonical historical SQL read
  -> existing lifecycle row, if one exists
  -> attach_bounded_continuity_evidence
  -> existing evaluate_bounded_continuity
  -> existing Technical Evidence publication
```

For a known lifecycle event intersecting an exact MA/RSI/MACD/return/volume
window, the evaluator returns `CONTINUITY_FAIL`, null value, and
`UNAVAILABLE`. For windows outside the known event, the carrier is still
partial and therefore returns `CONTINUITY_UNKNOWN`; it does not claim PASS.
With no lifecycle row, the runtime remains `CONTINUITY_UNKNOWN` as before.

No schema or API change is needed because `technicalEvidence` already exposes
the required D4 continuity and lineage fields. No persistence or migration is
needed because the attachment is deterministic on-read from an existing
canonical carrier.

## 5. Focused and full validation

```text
RELEVANT_BASELINE=41 passed, 5 skipped, 1 warning
RELEVANT_POST=44 passed, 5 skipped, 1 warning
RELEVANT_TEST_DELTA=+3 passed; two lifecycle attachment tests and one runtime evaluator test
FOCUSED_TECHNICAL=15 passed, 1 warning
FULL_BACKEND_BASELINE=492 passed, 41 skipped, 1 warning
FULL_BACKEND_POST=495 passed, 41 skipped, 1 warning
FULL_BACKEND_TEST_DELTA=+3 passed; no unrelated removal or discovery reduction
RUFF=PASS
PYTHON_COMPILE=PASS (Python 3.12.13)
JSON_PARSE=PASS
MACHINE_READABLE_PROSE_CONSISTENCY=PASS
GIT_DIFF_CHECK=PASS
SECRET_SCAN=PASS
OPENAPI_DRIFT=NOT_APPLICABLE_NO_API_SCHEMA_CHANGE
GENERATED_SCHEMA_EQUALITY=NOT_APPLICABLE_NO_GENERATED_SCHEMA_CHANGE
```

PostgreSQL URLs were absent. No historical SQL read was executed for real
bounded validation, so no real window is presented as PASS:

```text
REAL_RUNTIME_VALIDATION=NOT_RUN_ENVIRONMENT_NOT_PROVIDED
REAL_PASS_BOUNDED_WINDOWS=NOT_RUN_ENVIRONMENT_NOT_PROVIDED
REAL_FAIL_WINDOWS=NOT_RUN_ENVIRONMENT_NOT_PROVIDED
REAL_UNKNOWN_WINDOWS=NOT_RUN_ENVIRONMENT_NOT_PROVIDED
REAL_MA60_FORMAL_WINDOWS=NOT_RUN_ENVIRONMENT_NOT_PROVIDED
REAL_MA60_FAIL_WINDOWS=NOT_RUN_ENVIRONMENT_NOT_PROVIDED
REAL_MA60_UNKNOWN_WINDOWS=NOT_RUN_ENVIRONMENT_NOT_PROVIDED
REAL_FORMAL_WINDOW_COUNT=0
```

The committed bounded authority audit is recorded in
[bounded-continuity-coverage-audit.json](../../reports/TASK-FE-BE-STOCK-006B-PHASE-2B1-RUNTIME-CONTINUITY-EVIDENCE-ATTACHMENT-20260816/bounded-continuity-coverage-audit.json).
It distinguishes authority-cell coverage from runtime indicator-window
evaluation and records the exact no-DB blocker.

## 6. WS3 and product boundaries

The existing WS3 MA60 consumer contract remains unchanged. A future MA60 value
is consumable only when the existing Technical Evidence record has 60 accepted
observations, inclusive same-session/as-of binding, `RAW_OBSERVED`, complete
lineage, `CONTINUITY_PASS_BOUNDED`, and `FORMAL`. This task proves the runtime
attachment does not weaken that gate; with the lifecycle-only carrier,
`WS3_FORMAL_MA60_CONSUMABLE=BOUNDED`.

WS3 was not modified. No candidate panel, A1/A2, walk-forward, strategy,
Recommendation, Opportunity, frontend, Advanced Technical, provider,
scheduler, PostgreSQL mutation, Production, release, deploy, push, merge, or
`NEXT_TASK` change occurred.

## 7. Exact write set

| Path | Purpose |
|---|---|
| `services/api/src/topicpilot_api/historical_read_model.py` | Attach the existing lifecycle carrier to the existing historical read result |
| `services/api/tests/test_historical_read_model.py` | Verify partial lifecycle envelope and no-event fail-closed behavior |
| `services/api/tests/test_technical_publication.py` | Verify exact-window lifecycle FAIL and indicator-level non-global gating |
| `docs/reports/TASK-FE-BE-STOCK-006B-PHASE-2B1-RUNTIME-CONTINUITY-EVIDENCE-ATTACHMENT-20260816.md` | This closure report |
| `reports/TASK-FE-BE-STOCK-006B-PHASE-2B1-RUNTIME-CONTINUITY-EVIDENCE-ATTACHMENT-20260816/runtime-continuity-evidence-attachment.json` | Machine-readable implementation and routing evidence |
| `reports/TASK-FE-BE-STOCK-006B-PHASE-2B1-RUNTIME-CONTINUITY-EVIDENCE-ATTACHMENT-20260816/bounded-continuity-coverage-audit.json` | Machine-readable authority and real-validation coverage audit |
| `docs/architecture/README.md` | Architecture navigation link |
| `docs/DOCUMENTATION_INDEX.md` | Cold-start documentation link |

## 8. State and routing

```text
CANONICAL_STATUS=CANONICALIZED
RELEASE_STATUS=NOT_RUN
PRODUCTION_VERIFICATION=NOT_RUN
RUNTIME_CONTINUITY_ATTACHMENT=IMPLEMENTED
PERSISTENCE_ADDED=NO
MIGRATION_ADDED=NO
API_CONTRACT_CHANGED=NO
FRONTEND_CHANGED=NO
ADVANCED_TECHNICAL_CHANGED=NO
BUY_SELL_SEMANTICS_ADDED=NO
RECOMMENDATION_CHANGED=NO
WS1_CHANGED=NO
WS3_CHANGED=NO
WS4_CHANGED=NO
G1_G2_G3=NOT_RERUN_PRESERVED_CANONICAL_EVIDENCE
CANARY=NOT_RERUN_PRESERVED_CANONICAL_EVIDENCE
PRODUCTION_MUTATION=NO
SCHEDULER_ACTIVATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
NEXT_TASK_CHANGED=NO
OWNER_STATE_PRESERVED=YES
TASK_WORKTREE_CLEANED=YES_AFTER_CLOSURE
```

The bounded routing outcome is:

```text
IMPLEMENTED_BUT_REAL_WINDOWS_REMAIN_AUTHORITY_BOUNDED
```

The exact blocker is not an implementation-policy gap: the runtime carrier
currently covers lifecycle discontinuities only, REC-A1 has 3,688 UNKNOWN
identity-family cells and no authoritative empty-set identities, and no
PostgreSQL environment was available for a real historical read. A future
bounded authority task may add an accepted event-family carrier; this task does
not create one or change Owner policy.

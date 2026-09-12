# TASK-REC-A1-CORE-V0-A1-A2-EXECUTABLE-CANDIDATE-PANEL-AND-READINESS-CLOSURE-2026-08-16

**TASK_ID:** `TASK-REC-A1-CORE-V0-A1-A2-EXECUTABLE-CANDIDATE-PANEL-AND-READINESS-CLOSURE-20260816`
**Workstream:** WS3 -> Core V0 Walk-forward Research
**Mode:** Research-only executable panel, availability, and readiness closure
**Canonical pre-SHA:** `5186b2b086774ef9080bbc8767a937c942fec63e`
**Source implementation commit:** `e7565e3a7c118be0ed91d606d486851938ec54e8`
**Canonical promotion commit:** `4f54040b73804d2c9e1284e3aeafffac9e2b4a3c`
**Final canonical content HEAD:** `4f54040b73804d2c9e1284e3aeafffac9e2b4a3c`
**FINAL_STATUS:** `COMPLETE_WITH_BOUNDED_EXECUTION_READINESS`

## Executive result

The frozen A1/A2 formation definitions now have a deterministic, persistence-
free candidate/date panel builder and a separate forward-outcome/readiness
contract. The implementation is research-only and accepts explicit canonical
evidence; it does not fetch, persist, publish, or activate anything.

The builder covers:

- executable candidate identity and deterministic record ID;
- accepted-session timeline and strict as-of `T` validation;
- hard 60-session warm-up;
- prior-20 accepted-High reference and five-session maturity;
- frozen A1 and A2 formation rules;
- WS2 `stock.sma.close.v1` MA60 consumer binding;
- candidate-specific PIT Topic membership/context binding;
- candidate input lineage and `frozenAtT` separation;
- forward T+1/T+3/T+5/T+10 availability states; and
- independent A1/A2 execution-readiness dispositions.

No real canonical candidate/date rows were loaded. Therefore this task does
not claim `READY_FOR_CORE_V0_WALK_FORWARD_EXECUTION`; current A1/A2 execution
readiness remains `READY_AFTER_WS2_MA60_PUBLICATION` until formal WS2 MA60
evidence and downstream outcome/REC-A1 dependencies are available.

## NEXT_TASK provenance reconciliation

`NEXT_TASK.md` is outside the TopicPilot repository, in the parent AI Git
repository. The exact current evidence is:

| Field | Evidence |
|---|---|
| Path | `C:/Users/acer/Desktop/題材領航/AI/NEXT_TASK.md` |
| AI repository | `agent/workspace-cleanup-20260713`, HEAD `473c60ccaf67f933f46b5cdb0d8489bbea41926e` |
| Canonical committed version | tracked `AI/NEXT_TASK.md`, Git blob `425a234b89a9b1382914517978f07d990790923f` |
| Owner checkout state | `M AI/NEXT_TASK.md`, tracked and uncommitted |
| Owner checkout diff | 154 insertions, 750 deletions relative to the committed 750-line version |
| Startup baseline raw SHA-256 | `FF640C735A2CDD4D8238157B287D293D0385B67F673150249A90F49661FFEB70` |
| Current owner checkout raw SHA-256 | `FF640C735A2CDD4D8238157B287D293D0385B67F673150249A90F49661FFEB70` |
| Current owner checkout LF-normalized SHA-256 | `0E52696AAF6809DDFB7AEE7298F532FEDBD79E16F9B2E584EC6919F15CA417DE` |
| Previous observed `0E` hash | Same LF-normalized representation, not independent mutation evidence |
| TopicPilot canonical tracking | `NOT_APPLICABLE_EXTERNAL_AI_REPOSITORY` |

Disposition:

```text
NEXT_TASK_DELTA_ATTRIBUTION=NEXT_TASK_DELTA_EXTERNAL_BUT_NON_BLOCKING_OWNER_STATE
NEXT_TASK_MUTATION_ATTRIBUTION=OWNER_CHECKOUT_UNCOMMITTED_REWRITE; NO_TASK_COMMIT
POSSIBLE_OLD_CHAT_PROMPT_MISUSE=UNKNOWN
NEXT_TASK_USED_AS_TASK_AUTHORITY=NO
NEXT_TASK_CHANGED_BY_THIS_TASK=NO
NEXT_TASK_ROLLBACK_PERFORMED=NO
NEXT_TASK_ADVANCE_PERFORMED=NO
NEXT_TASK_EXTERNAL_DELTA_PRESERVED=YES
```

The raw startup hash and current raw owner hash match. The apparent `FF` to
`0E` delta was a raw-versus-LF-normalized hash-method mismatch. The owner
checkout does differ from its committed AI-repository version, but there is no
canonical, parallel-task, or task-owned commit attribution for that rewrite.
This task neither restores nor accepts the owner rewrite as authority.

## Frozen policy and protocol carried forward

The previous A1/A2 policy remains unchanged:

```text
REFERENCE_POLICY=PRIOR_20_ACCEPTED_SESSION_HIGH
REFERENCE_WINDOW=20 accepted sessions strictly before T
REFERENCE_EXCLUDES_T=YES
MIN_REFERENCE_MATURITY_SESSIONS=5
A1_PROXIMITY=3%
A1_STRUCTURE_IMPROVING_HARD_GATE=NO
A2_CONFIRMATION=CLOSE / SINGLE_SESSION
A2_EXTRA_BREAKOUT_MARGIN=0
GAP_UP_EXCLUDED=NO
VOLUME_HARD_GATE=NO
RSI_HARD_GATE=NO
MACD_HARD_GATE=NO
```

`core-v0-walk-forward.v1` remains unchanged: Development
`2026-02-02..2026-06-30`, Validation `2026-07-01..2026-07-31`, Holdout
`2026-08-01..2026-08-13`, at least 60 prior canonical accepted trading
sessions, and evaluation-only T+1/T+3/T+5/T+10 outcomes. Tuning and
optimization remain forbidden.

## Candidate panel implementation

The implementation contract is
[CORE_V0_A1_A2_EXECUTABLE_CANDIDATE_PANEL_CONTRACT.md](../architecture/CORE_V0_A1_A2_EXECUTABLE_CANDIDATE_PANEL_CONTRACT.md).
The code is under `services/api/src/topicpilot_api/research/` and is not wired
to any runtime boundary.

### Panel identity

Every panel binds candidate ID/version, instrument identity, evaluation session,
date/as-of, calendar version, L1/MA60 evidence, reference window and lineage,
Close/Open, A1 distance or A2 comparison, PIT Topic context, input lineage,
formation reason/state, and `frozenAtT`.

Bars after `T`, bars with `as_of > T`, duplicate accepted sessions, and outcomes
at or before `T` fail closed. Missing values remain explicit availability
states; no zero-fill, calendar substitution, synthetic backfill, or fallback
reference is used.

### Formation and temporal behavior

The builder implements the canonical A1/A2 policy exactly. A1 requires the
valid mature prior-20 reference, L1 pass, Close below reference, and distance
at most 3%. A2 requires the valid mature reference and Close strictly above it;
intraday High alone cannot confirm it, while gap-up Close confirmation is
allowed. The 60-session warm-up is checked per candidate/date.

### WS2, PIT, REC-A1, and outcomes

The builder consumes formal WS2 `stock.sma.close.v1` evidence and does not
recalculate MA60. Current canonical WS2 state remains
`PHASE_2B_IMPLEMENTATION_PENDING_OWNER_AUTHORIZATION`; missing formal evidence,
continuity, publication, or lineage returns a bounded
`WAITING_FOR_FORMAL_WS2_MA60_EVIDENCE` state.

PIT Topic context is bound per candidate/date when required; complete historical
Topic/System State is not a global prerequisite. REC-A1 remains an
evaluation-integrity dependency only:
`BLOCKED_BY_REC_A1_PROVENANCE_LEDGER_ARCHIVE_GAP`. T+1/T+3/T+5/T+10 are built
by a separate outcome panel with `outcomesFlowBackward=false`; they cannot
rewrite the candidate at `T`.

## Candidate-level readiness matrix

| Candidate | Definition authority | Panel | 60-session eligibility | WS2 MA60 | PIT context | REC-A1 | Forward outcomes | Execution readiness | Real date coverage |
|---|---|---|---|---|---|---|---|---|---|
| A1 | `FROZEN_CORE_V0_DEFINITION_AUTHORITY` | `IMPLEMENTED_RESEARCH_ONLY` | `IMPLEMENTED_BOUNDED_CHECK` | `READY_AFTER_WS2_MA60_PUBLICATION` | `IMPLEMENTED_CANDIDATE_SPECIFIC_BINDING` | `READY_AFTER_REC_A1_PROVENANCE_RECONCILIATION` | `READY_AFTER_FORWARD_OUTCOME_PANEL` | `READY_AFTER_WS2_MA60_PUBLICATION` | `NOT_RUN_BY_SCOPE` |
| A2 | `FROZEN_CORE_V0_DEFINITION_AUTHORITY` | `IMPLEMENTED_RESEARCH_ONLY` | `IMPLEMENTED_BOUNDED_CHECK` | `READY_AFTER_WS2_MA60_PUBLICATION` | `IMPLEMENTED_CANDIDATE_SPECIFIC_BINDING` | `READY_AFTER_REC_A1_PROVENANCE_RECONCILIATION` | `READY_AFTER_FORWARD_OUTCOME_PANEL` | `READY_AFTER_WS2_MA60_PUBLICATION` | `NOT_RUN_BY_SCOPE` |
| A3 | preserved | `NOT_IN_SCOPE` | preserved | preserved | preserved | preserved | preserved | `BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY` | `NOT_RUN_BY_SCOPE` |
| Catch-up | preserved | `NOT_IN_SCOPE` | preserved | preserved | preserved | preserved | preserved | `BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY` | `NOT_RUN_BY_SCOPE` |

No global READY/NO state is emitted. A1/A2 remain independently routable; A3
and Catch-up do not block them and were not changed.

## Coverage and synthetic evidence

Real Development/Validation/Holdout candidate-date coverage is
`NOT_RUN_BY_SCOPE`; the coverage artifact reports zero loaded canonical rows,
not zero eligible dates. Synthetic focused tests cover positive and negative
A1/A2 cases, maturity, distance, equality, High-only breakout, gap-up, warm-up,
PIT context, WS2 bounded readiness, forward separation, and no-lookahead.

The synthetic fixture is explicitly non-canonical and contains no performance
values. It cannot enter a production snapshot or performance ledger.

## Validation

| Check | Result |
|---|---|
| Focused panel tests | `9 passed` |
| Ruff on new module/tests | `PASS` |
| JSON parse and policy assertions | `PASS` |
| Frozen policy/protocol unchanged | `PASS` |
| No-lookahead focused checks | `PASS` |
| Coverage artifact consistency | `PASS` |
| `git diff --check` / secret scan / write-set | `PASS` |
| Full application/backend suite | `NOT_RUN_BY_SCOPE` |
| DB/schema/migration/API/UI/provider/scheduler | `NOT_RUN_BY_SCOPE` |
| G1/G2/G3/Canary | `PRESERVED_NOT_RERUN` |
| Walk-forward/performance/Strategy Review | `NOT_RUN_BY_SCOPE` |
| Recommendation/Production/push/deploy | `NOT_RUN_BY_SCOPE` |

The focused test used the repository's existing Python 3.12 environment as a
diagnostic fallback because the default shell Python was 3.10 without pytest;
no dependency files were changed and no release claim is made.

## Closure fields

```text
TASK_ID=TASK-REC-A1-CORE-V0-A1-A2-EXECUTABLE-CANDIDATE-PANEL-AND-READINESS-CLOSURE-20260816
FINAL_STATUS=COMPLETE_WITH_BOUNDED_EXECUTION_READINESS
CANONICAL_PRE_SHA=5186b2b086774ef9080bbc8767a937c942fec63e
CANONICAL_POST_SHA=4f54040b73804d2c9e1284e3aeafffac9e2b4a3c
A1_DEFINITION_AUTHORITY=FROZEN_CORE_V0_DEFINITION_AUTHORITY
A2_DEFINITION_AUTHORITY=FROZEN_CORE_V0_DEFINITION_AUTHORITY
A1_CANDIDATE_PANEL_IMPLEMENTED=YES
A2_CANDIDATE_PANEL_IMPLEMENTED=YES
REFERENCE_POLICY=PRIOR_20_ACCEPTED_SESSION_HIGH
REFERENCE_MATURITY=5
A1_PROXIMITY=3%
A2_CONFIRMATION=SINGLE_SESSION_CLOSE
CORE_V0_L1_MA60=Close(T)>=MA60(T)
WS2_MA60_POLICY_AUTHORITY=stock-technical-v0-policy.v2 / stock.sma.close.v1
WS2_MA60_IMPLEMENTATION_STATE=PHASE_2B_IMPLEMENTATION_PENDING_OWNER_AUTHORIZATION
WS2_FORMAL_MA60_EVIDENCE_CONSUMABLE=BOUNDED
TEMPORAL_60_SESSION_ELIGIBILITY_IMPLEMENTED=YES
PIT_TOPIC_CONTEXT_BINDING=YES
REC_A1_PROVENANCE_STATE=BLOCKED_BY_REC_A1_PROVENANCE_LEDGER_ARCHIVE_GAP_EVALUATION_ONLY
FORWARD_OUTCOME_PANEL_STATE=IMPLEMENTED_CONTRACT_ONLY_NOT_POPULATED
OUTCOMES_FLOW_BACKWARD=NO
DEVELOPMENT_COVERAGE=0_REAL_CANDIDATE_DATES_NOT_RUN
VALIDATION_COVERAGE=0_REAL_CANDIDATE_DATES_NOT_RUN
HOLDOUT_COVERAGE=0_REAL_CANDIDATE_DATES_NOT_RUN
A1_EXECUTION_READINESS=READY_AFTER_WS2_MA60_PUBLICATION
A2_EXECUTION_READINESS=READY_AFTER_WS2_MA60_PUBLICATION
READY_FOR_CORE_V0_WALK_FORWARD_EXECUTION=NO
WALK_FORWARD_EXECUTED=NO
PERFORMANCE_METRICS_GENERATED=NO
STRATEGY_ACCEPTED_OR_REJECTED=NO
A3_CHANGED=NO
CATCH_UP_CHANGED=NO
WS1_CHANGED=NO
WS2_CHANGED=NO
WS4_CHANGED=NO
NEXT_TASK_STARTUP_HASH=FF640C735A2CDD4D8238157B287D293D0385B67F673150249A90F49661FFEB70
NEXT_TASK_FINAL_RAW_HASH=FF640C735A2CDD4D8238157B287D293D0385B67F673150249A90F49661FFEB70
NEXT_TASK_OWNER_LF_NORMALIZED_HASH=0E52696AAF6809DDFB7AEE7298F532FEDBD79E16F9B2E584EC6919F15CA417DE
NEXT_TASK_MUTATION_ATTRIBUTION=NEXT_TASK_DELTA_EXTERNAL_BUT_NON_BLOCKING_OWNER_STATE
POSSIBLE_OLD_CHAT_PROMPT_MISUSE=UNKNOWN
NEXT_TASK_USED_AS_AUTHORITY=NO
NEXT_TASK_CHANGED_BY_THIS_TASK=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
```

The task-owned worktree/branch will be removed only after canonical promotion
and exact artifact verification. The external AI owner checkout, all active
WS1/WS2/WS4 worktrees, owner dirty/untracked state, and `NEXT_TASK` will remain
untouched.

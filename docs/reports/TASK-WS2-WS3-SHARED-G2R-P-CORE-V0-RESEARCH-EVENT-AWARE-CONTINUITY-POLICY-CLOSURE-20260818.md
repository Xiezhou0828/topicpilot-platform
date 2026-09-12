# Core V0 WS3 Research Event-Aware Continuity Policy Closure

Task: `TASK-WS2-WS3-SHARED-G2R-P-CORE-V0-RESEARCH-EVENT-AWARE-CONTINUITY-POLICY-CLOSURE-20260818`

Date: 2026-08-18 (Asia/Taipei)

This task records the Owner's WS3-only research policy decision and applies the smallest bounded adapter needed for a future Core V0 real-coverage rerun. It does not rerun WS3 research, modify WS2 publication policy, execute G2R-C, execute Shared-G3, or change production authority.

## Final report

```text
TASK_FINAL_STATUS=COMPLETE_OWNER_POLICY_CLOSURE_AND_WS3_MINIMAL_ADAPTATION
OWNER_POLICY_RECORDED=YES
WS3_CONTINUITY_POLICY=EVENT_AWARE_RESEARCH
WS3_REQUIRES_AFFIRMATIVE_NO_EVENT=NO
WS3_REQUIRES_COVERED_NO_EVENT=NO
WS3_REQUIRES_CONTINUITY_PASS_BOUNDED=NO
KNOWN_VERIFIED_EVENT_OVERLAY_PRESERVED=YES
CONTINUITY_UNKNOWN_PRESERVED=YES
UNKNOWN_TO_PASS_CONVERSION_COUNT=0
COVERED_NO_EVENT_FABRICATION_COUNT=0
REAL_HISTORICAL_OHLCV_REQUIREMENT_PRESERVED=YES
MA60_POLICY_CHANGED=NO
CORE_V0_STRATEGY_CHANGED=NO
WS2_POLICY_CHANGED=NO
G2R_C_REQUIRED_FOR_WS3=NO
G2R_C_REQUIRED_FOR_WS2=YES_OR_UNRESOLVED
SHARED_G3_STILL_REQUIRED=PARTIAL
READY_FOR_WS3_REAL_COVERAGE_RERUN=YES
READY_FOR_WS3_MAINLINE_CONTINUATION=YES_BOUNDED_OWNER_POLICY_RECORDED
READY_FOR_WS2_MAINLINE_CONTINUATION=NO_SEPARATE_FORMAL_AUTHORITY_GAP
WS3_REAL_COVERAGE_RERUN_EXECUTED=NO
FILES_CHANGED=4 implementation/test files plus 6 task-owned report artifacts
TESTS=33 passed; Ruff passed; py_compile passed; git diff --check passed
TASK_COMMIT_SHA=RECORDED_AFTER_COMMIT
```

The final commit SHA is recorded in the owner handoff after commit because the report itself is part of that commit.

## Provenance and existing evidence

```text
TASK_START_HEAD=397ea52e911f5003d34b563620cbcf6a65d65e17
TASK_START_WORKTREE=C:\Users\acer\Documents\Codex\g2r
TASK_START_WORKTREE_STATUS=CLEAN
BASELINE_REAL_HISTORICAL_ROWS=63826
BASELINE_REAL_HISTORICAL_DISTINCT_INSTRUMENTS=507
BASELINE_REAL_HISTORICAL_WINDOW=2026-02-02..2026-08-13
BASELINE_COVERED_EVENT_CELLS=368
BASELINE_COVERED_NO_EVENT_CELLS=0
BASELINE_UNKNOWN_CELLS=3688
```

The prior G2R-B3 closure was read and preserved. Its source boundary remains valid: official TWSE/TPEx surfaces provide useful observed event evidence but do not prove complete no-event authority. This task does not reopen B3, create B4, or alter the 368/0/3688 counts.

The task worktree was clean at start. The owner canonical/dirty worktree was not modified. No database, OHLCV, lifecycle, `NEXT_TASK`, WS1, WS2, WS4, production, deployment, or promotion state was changed.

## A. Current dependency audit

The audit found two distinct continuity paths:

1. `services/api/src/topicpilot_api/technical_publication.py` formal WS2 publication calls `evaluate_bounded_continuity`; an incomplete or UNKNOWN continuity envelope remains unavailable. This path is intentionally unchanged.
2. `services/api/src/topicpilot_api/research/core_v0_candidate_panel.py` consumed `MA60Evidence` only through `is_formal_consumable`, which required `CONTINUITY_PASS_BOUNDED`. This was the WS3 research dependency that blocked a research-only candidate panel when continuity remained UNKNOWN.

The audit also checked the existing Core V0 contracts: `CORE_V0_CANDIDATE_DEFINITION_AUTHORITY_CONTRACT.md`, `CORE_V0_REAL_COVERAGE_AND_WALK_FORWARD_PREFLIGHT_CONTRACT.md`, and the frozen Core V0 candidate-panel tests. The new policy is recorded as a WS3-scoped research overlay; it does not rewrite the formal WS2 contract, numeric MA60 rule, strategy, signal logic, A-method, or walk-forward protocol.

Exact symbols, locations, baseline hashes, and dependency dispositions are in [ws3-research-continuity-dependency-audit.json](../../reports/TASK-WS2-WS3-SHARED-G2R-P-CORE-V0-RESEARCH-EVENT-AWARE-CONTINUITY-POLICY-CLOSURE-20260818/ws3-research-continuity-dependency-audit.json).

## B. Owner policy implemented

The new policy is `EVENT_AWARE_RESEARCH` (`ws3-event-aware-research.v1`). For WS3 research only:

```text
real observed OHLCV
+ valid instrument identity
+ valid source lineage
+ sufficient technical observations
+ research input may proceed
```

The continuity overlay is explicit:

- `CONTINUITY_UNKNOWN` remains `CONTINUITY_UNKNOWN` and does not block research when the real-input prerequisites pass.
- No known verified breaking event is represented as `NO_KNOWN_VERIFIED_BREAKING_EVENT`; it is not represented as `NO_BREAKING_EVENT_OCCURRED`.
- A verified breaking event is never ignored: it may be `EXCLUDE`, `CORRECT`, or `ANNOTATE` according to existing event semantics.
- `CONTINUITY_FAIL` without a verified correction/annotation overlay remains unavailable; it is never converted to PASS.
- A missing or insufficient OHLCV window remains unavailable for the actual insufficiency reason.

The policy never emits `COVERED_NO_EVENT`, never modifies `AFFIRMATIVE_NO_EVENT_EVIDENCE_READY`, and never maps UNKNOWN to PASS.

## C. Minimal implementation boundary

Added:

- `services/api/src/topicpilot_api/research/ws3_research_policy.py`
  - `ResearchInputEvidence`
  - `VerifiedBreakingEvent`
  - `ResearchEligibility`
  - `evaluate_ws3_research_eligibility`
- Optional `research_eligibility` on `CandidatePanelInput`.
- Additive `MA60Evidence.is_research_consumable()` for WS3-only research mode.
- Candidate-panel output fields for research policy state, event overlay, and preserved continuity state.

Preserved:

- `MA60Evidence.is_formal_consumable()` and its `CONTINUITY_PASS_BOUNDED` requirement.
- `technical_publication.py` and all WS2 formal publication behavior.
- Raw OHLCV, identity, lineage, observation sufficiency, as-of, and numeric `Close(T) >= MA60(T)` requirements.
- Existing event normalization, snapshots, correction detection, supersession handling, and fail-closed formal states.

Research mode is opt-in: when `CandidatePanelInput.research_eligibility` is absent, the existing formal-only behavior remains. A verified `EXCLUDE` event returns `EXCLUDED_BY_VERIFIED_EVENT` and prevents candidate formation; a `CORRECT` or `ANNOTATE` overlay remains visible in the candidate record and does not rewrite OHLCV.

## D. Required cases

| Case | Result |
| --- | --- |
| Normal real historical window, no known verified event | Research eligible; `COVERED_NO_EVENT` not required |
| Known verified breaking event | Exclude/correct/annotate behavior preserved; event is not silently ignored |
| Continuity authority UNKNOWN, no known verified event | Research eligible; UNKNOWN remains UNKNOWN |
| Insufficient OHLCV / technical observations | Research unavailable for `INSUFFICIENT_TECHNICAL_OBSERVATIONS` |
| WS2 isolation | Formal WS2 path still rejects UNKNOWN; existing technical-publication tests pass |

## E. Readiness reassessment

`READY_FOR_WS3_REAL_COVERAGE_RERUN=YES`. The previous `COVERED_NO_EVENT > 0` prerequisite is removed for WS3 research under the Owner policy. This task does not execute the rerun; it only makes the bounded research path ready for a separate Owner/orchestrator task.

`G2R_C_REQUIRED_FOR_WS3=NO` because G2R-C's affirmative no-event authority is no longer a WS3 research prerequisite. `G2R_C_REQUIRED_FOR_WS2=YES_OR_UNRESOLVED` because the formal WS2 publication path remains unchanged and still needs its own continuity authority.

`SHARED_G3_STILL_REQUIRED=PARTIAL`: any G3 work whose only purpose was to make affirmative no-event continuity mandatory for WS3 is obsolete under the Owner policy. Independent WS2/formal/shared requirements remain preserved. G3 was not executed.

## F. Validation

Validation was run in an ephemeral Docker container using a read-only mount of the task worktree. No API process, PostgreSQL service, migration, seed, deployment, or production mutation was performed.

```text
33 passed
Ruff: All checks passed
py_compile: 4 files passed
git diff --check: passed
```

The full test evidence, exact commands, and case mapping are in [test-evidence.json](../../reports/TASK-WS2-WS3-SHARED-G2R-P-CORE-V0-RESEARCH-EVENT-AWARE-CONTINUITY-POLICY-CLOSURE-20260818/test-evidence.json).

## Required artifacts

- [ws3-research-continuity-dependency-audit.json](../../reports/TASK-WS2-WS3-SHARED-G2R-P-CORE-V0-RESEARCH-EVENT-AWARE-CONTINUITY-POLICY-CLOSURE-20260818/ws3-research-continuity-dependency-audit.json)
- [ws3-event-aware-research-policy.json](../../reports/TASK-WS2-WS3-SHARED-G2R-P-CORE-V0-RESEARCH-EVENT-AWARE-CONTINUITY-POLICY-CLOSURE-20260818/ws3-event-aware-research-policy.json)
- [ws3-real-coverage-rerun-readiness.json](../../reports/TASK-WS2-WS3-SHARED-G2R-P-CORE-V0-RESEARCH-EVENT-AWARE-CONTINUITY-POLICY-CLOSURE-20260818/ws3-real-coverage-rerun-readiness.json)
- [g2r-c-g3-routing-reassessment.json](../../reports/TASK-WS2-WS3-SHARED-G2R-P-CORE-V0-RESEARCH-EVENT-AWARE-CONTINUITY-POLICY-CLOSURE-20260818/g2r-c-g3-routing-reassessment.json)
- [test-evidence.json](../../reports/TASK-WS2-WS3-SHARED-G2R-P-CORE-V0-RESEARCH-EVENT-AWARE-CONTINUITY-POLICY-CLOSURE-20260818/test-evidence.json)

## Stop condition

Owner policy closure, minimal WS3 adaptation, required tests, and routing/readiness are complete. No WS3 coverage rerun, WS2 continuation, G2R-C, Shared-G3, promotion, push, deploy, or production action was started.

STOP.

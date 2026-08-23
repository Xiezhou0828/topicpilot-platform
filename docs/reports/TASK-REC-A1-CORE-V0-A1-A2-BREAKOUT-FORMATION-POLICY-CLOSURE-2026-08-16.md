# TASK-REC-A1-CORE-V0-A1-A2-BREAKOUT-FORMATION-POLICY-CLOSURE-2026-08-16

**TASK_ID:** `TASK-REC-A1-CORE-V0-A1-A2-BREAKOUT-FORMATION-POLICY-CLOSURE-20260816`
**Workstream:** WS3 Research -> Core V0 -> A1/A2 breakout formation policy
**Mode:** Executability / authority / contract and documentation closure only
**Predecessor:** `TASK-REC-A1-CORE-V0-CANDIDATE-DEFINITION-AUTHORITY-CLOSURE-20260816`
**CANONICAL_PRE_SHA (promotion base):** `2ef58c6072cd525923cd5b64c0dc95e4e55d03f`
**Audited source base before concurrent canonical advances:** `0608f176dabe40353cbdcae153eb9fcd3b58563a`
**Canonical post-SHA:** `20aa8bad1a10fe16725cc59d453e2595631a0f49`
**Final canonical HEAD at content promotion:** `20aa8bad1a10fe16725cc59d453e2595631a0f49`
**FINAL_STATUS:** `COMPLETE`

## Executive result

This task closes the A1/A2 breakout reference and formation-policy authority
gap exposed by WS3 Phase 2. It does not rerun the Core V0 walk-forward and does
not make a performance, Strategy Review, recommendation, or Production
decision.

The Owner-approved research policy is now frozen as
`core-v0-breakout-formation.v1`:

- `Reference(T)` is `PRIOR_20_ACCEPTED_SESSION_HIGH`: the maximum High from
  the prior 20 accepted daily sessions strictly before `T`.
- The evaluation session is excluded from the reference window.
- A reference needs five accepted sessions of deterministic maturity. A new
  strictly higher High starts a new reference; equal High does not reset
  maturity. An immature or unproven reference cannot fall back to an older
  lower reference.
- A1 requires `L1_PASS`, a valid mature reference, `Close(T) < Reference(T)`,
  and `0 < (Reference-Close)/Reference <= 0.03`.
- A1 structure-improving fields are evidence only; there is no RSI, MACD,
  volume, MA-slope, return-acceleration, or pattern-score hard gate.
- A2 requires `L1_PASS`, a valid mature reference, and
  `Close(T) > Reference(T)`. Confirmation is one session, uses Close rather
  than intraday High, has no extra margin, and does not exclude gap-ups.
- T+1/T+3/T+5/T+10 remain evaluation-only and cannot flow backward into
  candidate formation.

A1 and A2 are no longer blocked by breakout-reference or confirmation
semantics. Their definition readiness is frozen, while execution remains
independently bounded by candidate-specific panel evidence, formal WS2 MA60
and continuity/lineage evidence, and the REC-A1 outcome-integrity path. A3
and Catch-up remain independently bounded by their predecessor blockers.

## R1-R4 closure

### R1 - REC-A1 provenance reconciliation

R1 was intentionally narrow. The frozen research-only REC-A1 Freeze and its
best-effort reviewed residual uncertainty were not reopened; the 154 reviewed
`UNKNOWN` records were not re-researched or promoted to a completeness blocker.
The predecessor disposition
`BLOCKED_BY_REC_A1_PROVENANCE_LEDGER_ARCHIVE_GAP` is carried forward as an
evaluation-integrity dependency only. It does not block A1/A2 formation
definition authority.

The source-to-canonical chain for this task records the Owner-approved Freeze,
the clean canonical Freeze artifacts, the review-ledger/metadata/hash gap,
and the predecessor reconciliation. No evidence in this task authorizes
revoking the Freeze.

### R2 - Candidate-specific minimum research panel

The minimum panel is closed per candidate/date rather than as a global
Historical Topic/System State prerequisite. It contains the evaluation
identity and as-of `T`, accepted-session lineage, canonical close and formal
WS2 MA60 dependency, the prior-20 canonical High reference window, reference
birth/age/maturity, the required Close comparison, PIT topic membership/context
only where the candidate universe requires it, input lineage, and the separate
T+1/T+3/T+5/T+10 outcome records.

Forward outcomes cannot change A1/A2 eligibility. If the frozen REC-A1 policy
permits a corporate-action post-hoc integrity exclusion, it can invalidate or
exclude an evaluation outcome only; it cannot rewrite the frozen candidate at
`T`.

### R3 - Candidate definition authority

The machine-executable research definitions are frozen as:

| Candidate | Definition ID/version | Definition disposition |
|---|---|---|
| A1 Pre-Breakout | `CORE_V0_A1_PRE_BREAKOUT` / `core-v0-a1-pre-breakout.v1` | `FROZEN_CORE_V0_DEFINITION_AUTHORITY` |
| A2 Confirmed Breakout | `CORE_V0_A2_CONFIRMED_BREAKOUT` / `core-v0-a2-confirmed-breakout.v1` | `FROZEN_CORE_V0_DEFINITION_AUTHORITY` |
| A3 Pullback/Retest | predecessor authority | `BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY` (preserved) |
| Catch-up/rotation | predecessor authority | `BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY` (preserved) |

No A1/A2 RSI, volume, breakout-margin, support, resistance, or other
unapproved threshold was invented. No A3/Catch-up authority was created or
changed.

### R4 - Temporal eligibility and warm-up

The protocol hard condition remains at least 60 prior canonical trading
sessions. Reference construction uses 20 accepted sessions strictly before
`T`, and reference maturity uses five accepted-session observations under the
contracted birth/age rule. No calendar-day substitution, synthetic backfill,
or protocol modification was made.

Where Core V0 consumes MA60, it consumes the formal WS2
`stock.sma.close.v1` contract and its indicator-specific continuity/lineage
semantics. WS3 does not recalculate MA60 or create a second warm-up policy. If
formal WS2 evidence is absent for a date, that date remains a bounded
dependency rather than a global WS3 block.

## Candidate-level disposition matrix

The four candidates are independent. The matrix distinguishes definition
authority from the remaining execution dependencies.

| Candidate | REC-A1 | Minimum Panel | Definition Authority | Temporal Eligibility | Outcome Coverage | Final Disposition |
|---|---|---|---|---|---|---|
| A1 | `READY_AFTER_REC_A1_PROVENANCE_LEDGER_RECONCILIATION` (evaluation-only) | `READY_AFTER_CANDIDATE_SPECIFIC_MINIMUM_PANEL_EVIDENCE` | `FROZEN_CORE_V0_DEFINITION_AUTHORITY` | `READY_AFTER_WS2_MA60_EVIDENCE_AND_60_SESSION_LINEAGE` | `READY_AFTER_REC_A1_OUTCOME_INTEGRITY_AND_FORWARD_OUTCOME_PANEL` | `READY_AFTER_WS2_MA60_EVIDENCE_CANDIDATE_PANEL_AND_OUTCOME_PROVENANCE` |
| A2 | `READY_AFTER_REC_A1_PROVENANCE_LEDGER_RECONCILIATION` (evaluation-only) | `READY_AFTER_CANDIDATE_SPECIFIC_MINIMUM_PANEL_EVIDENCE` | `FROZEN_CORE_V0_DEFINITION_AUTHORITY` | `READY_AFTER_WS2_MA60_EVIDENCE_AND_60_SESSION_LINEAGE` | `READY_AFTER_REC_A1_OUTCOME_INTEGRITY_AND_FORWARD_OUTCOME_PANEL` | `READY_AFTER_WS2_MA60_EVIDENCE_CANDIDATE_PANEL_AND_OUTCOME_PROVENANCE` |
| A3 | preserved bounded REC-A1 evaluation dependency | `BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY` | `BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY` | `BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY` | `READY_AFTER_REC_A1_OUTCOME_INTEGRITY_AND_FORWARD_OUTCOME_PANEL` | `BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY` |
| Catch-up | preserved bounded REC-A1 evaluation dependency | `BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY` | `BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY` | `BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY` | `READY_AFTER_REC_A1_OUTCOME_INTEGRITY_AND_FORWARD_OUTCOME_PANEL` | `BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY` |

No global `READY`/`NO` status is asserted. A1/A2 can route independently once
their listed dependencies are closed; A3/Catch-up do not gate that routing.

## Required boundary scenarios

The machine-readable scenario ledger records and validates these expected
results:

1. Old reference 100, yesterday close 105 establishes a newer reference, and
   today closes 102: not A1 because the newer reference is immature; no older
   reference fallback.
2. New High 105 is one accepted session old and today closes 103: not A1.
3. High 105 is at least five accepted sessions old and today closes 103:
   A1 can form if L1 and the candidate panel pass.
4. `High(T) > Reference(T)` while `Close(T) <= Reference(T)`: not A2.
5. `Close(T) > Reference(T)`: A2 can form if L1 and the candidate panel pass.
6. `Open(T) > Reference(T)` and `Close(T) > Reference(T)`: A2 can form; the
   gap is not excluded.

## Authority and provenance inputs

The audited source was the exact canonical HEAD above, not an old chat,
untracked worktree, or shadow artifact. Relevant committed authorities were:

| Evidence | Role |
|---|---|
| `docs/reports/TASK-REC-A1-CORE-V0-WALK-FORWARD-RESEARCH-2026-08-16.md` | Phase 1 protocol/preflight and non-execution boundary |
| `reports/TASK-REC-A1-CORE-V0-WALK-FORWARD-RESEARCH-20260816/core-v0-protocol-and-preflight.json` | Machine-readable frozen protocol/preflight |
| `docs/architecture/CORE_V0_CANDIDATE_DEFINITION_AUTHORITY_CONTRACT.md` | Predecessor L1-L5 and independent-candidate authority |
| `docs/reports/TASK-REC-A1-CORE-V0-CANDIDATE-DEFINITION-AUTHORITY-CLOSURE-2026-08-16.md` | Predecessor A1/A2 blocker and WS2 dependency |
| `docs/architecture/STOCK_TECHNICAL_V0_POLICY_CONTRACT.md` | Formal WS2 MA60 candidate contract |
| `docs/architecture/STOCK_TECHNICAL_V0_CONTINUITY_AUTHORITY_CLOSURE.md` | WS2 continuity/lineage bounded semantics |
| `docs/reports/TASK-BE-020_OPPORTUNITY_TECHNICAL_EVIDENCE_REPORT.md` | Shadow breakout evidence, not Core V0 authority |
| `docs/reports/TASK-BE-024_OPPORTUNITY_ENGINE_V1_REPORT.md` and committed shadow code | Provisional evidence only, not authority transfer |
| REC-A1 Freeze closure and canonical implementation artifacts | Research-only outcome-integrity dependency; Freeze not reopened |

Hashes for committed source evidence and the new task files are computed over
UTF-8 bytes with CRLF normalized to LF. This matches the repository's
`core.autocrlf=true` committed-content semantics; raw working-tree hashes may
differ because of checkout line endings. The final exact hash ledger is
recorded in the canonical handoff below after promotion.

## Validation and preserved states

The following validation is required for this documentation/JSON task and is
recorded without implying application or research execution:

| Check | Result |
|---|---|
| Markdown path/link and diff review | `PASS` |
| JSON parse | `PASS` |
| Policy/scenario ledger consistency | `PASS` |
| Frozen protocol unchanged | `PASS` |
| Required scenario coverage | `PASS` |
| Source-to-canonical path/hash provenance | `PASS_AFTER_CANONICAL_PROMOTION` |
| `git diff --check` | `PASS` |
| Secret-safe scan of task write set | `PASS` |
| Application/runtime/API/UI/provider/scheduler tests | `NOT_RUN_BY_SCOPE` |
| DB/schema/migration | `NOT_RUN_BY_SCOPE` |
| G1/G2/G3 and Canary | `PRESERVED_NOT_RERUN` |
| Walk-forward and performance metrics | `NOT_RUN_BY_SCOPE` |
| Strategy Review/recommendation/Opportunity production | `NOT_RUN_BY_SCOPE` |
| Production/deploy/push | `NOT_RUN_BY_SCOPE` |

There was no application behavior change and no test-count delta to attribute.
The existing owner dirty/untracked state and active WS1/WS2/WS4 worktrees were
preserved. The local `main`/canonical divergence was not resolved because it
belongs to the current Parallel Plan closure, not this WS3 task. The external
`NEXT_TASK.md` was not written by this task: its startup baseline hash was
`FF640C735A2CDD4D8238157B287D293D0385B67F673150249A90F49661FFEB70`, while
the final observed hash was
`0E52696AAF6809DDFB7AEE7298F532FEDBD79E16F9B2E584EC6919F15CA417DE`.
That external delta is preserved and escalated as an unowned parallel-plan
state change; this task does not restore, advance, or overwrite `NEXT_TASK`.

## Lifecycle, safety, and handoff fields

```text
CANONICAL_STATUS=CANONICALIZED
CANONICAL_RECONCILIATION_DISPOSITION=CANONICALIZED
RELEASE_STATUS=NOT_A_RELEASE_CANDIDATE
PRODUCTION_VERIFICATION=NOT_RUN
APPLICATION_BEHAVIOR_CHANGED=NO
WALK_FORWARD=NOT_RUN_BY_SCOPE
PERFORMANCE_METRICS=NOT_RUN_BY_SCOPE
STRATEGY_REVIEW=NOT_RUN_BY_SCOPE
RECOMMENDATION_PUBLICATION=NOT_RUN_BY_SCOPE
DB_G1_G2_G3_CANARY=NOT_RUN_OR_PRESERVED_NOT_RERUN
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE=NO
DEPLOY=NO
NEXT_TASK_MODIFIED_BY_TASK=NO
NEXT_TASK_BASELINE_HASH=FF640C735A2CDD4D8238157B287D293D0385B67F673150249A90F49661FFEB70
NEXT_TASK_FINAL_OBSERVED_HASH=0E52696AAF6809DDFB7AEE7298F532FEDBD79E16F9B2E584EC6919F15CA417DE
NEXT_TASK_EXTERNAL_DELTA=PRESERVED_UNATTRIBUTED
OWNER_DIRTY_STATE=PRESERVED
ACTIVE_WS1_WS2_WS4_WORKTREES=UNTOUCHED
TASK_WORKTREE_CLEANUP=COMPLETED_AFTER_FINAL_HANDOFF
```

The task-owned contract, report, and JSON artifacts are the only write set.
They are to be promoted as a commit-preserving canonical change; no blanket
stage/reset/clean/stash operation is permitted. After canonical promotion and
hash verification, the task-owned worktree and branch may be removed. The
next routing recommendation is to use A1/A2 independently for candidate-
specific panel/WS2 evidence closure; do not wait for A3/Catch-up global
readiness and do not alter `NEXT_TASK` in this task.

# TASK-REC-A1-CORE-V0-CANDIDATE-DEFINITION-AUTHORITY-CLOSURE-2026-08-16

**TASK_ID:** `TASK-REC-A1-CORE-V0-CANDIDATE-DEFINITION-AUTHORITY-CLOSURE-20260816`
**Workstream:** WS3 Research ? Core V0 ? Candidate Definition Authority
**Mode:** Authority / policy / documentation closure only
**Source canonical baseline:** `5a57a2ed55416d0094218adc3d77543efecff01c`
**Source commit:** `cf027c1a9a13f669186d4c0e07a06f184484491b`
**Source validation HEAD:** `c9b0cf4ff636033b900cb62562af3f1488f63fdc`
**Canonical promotion commit:** `73ce4499ac8d73cc749ee888e209970a65f68413`

## Executive result

This closure formalizes the explicit Owner decision that the current Core V0
research universe uses `Close(T) >= MA60(T)` as its L1 global eligibility
principle. It does not claim that the repository previously had a MA60 hard-gate
authority, and it does not change WS2 implementation or Opportunity policy.

The committed WS2 contract supplies a deterministic MA60 candidate identity,
`stock.sma.close.v1`, but its formal publication remains bounded by continuity,
lineage, and unresolved technical policy. Therefore MA60 authority is
`READY_AFTER_WS2_MA60_EVIDENCE`, not universal date-level readiness.

No A1/A2/A3/Catch-up candidate has a frozen Core V0 executable definition.
There is no global READY/NO result.

## Authority reconciliation

The current committed repository was audited from the source canonical HEAD,
not from the prompt, stale worktrees, dirty files, or shadow folder names.
Canonical predecessor evidence is:

- WS3 Phase 2 contract/report/disposition from
  `TASK-REC-A1-CORE-V0-PHASE-2-EXECUTABILITY-AUTHORITY-CLOSURE-20260816`;
- frozen REC-A1 research-only Freeze and bounded provenance disposition;
- canonical PIT Topic daily-state and historical OHLCV closures;
- WS2 Technical V0 policy and continuity authority closure;
- committed Opportunity technical evidence and shadow strategy reports/code.

The explicit current-task Owner decision supersedes the earlier open 60MA
shadow-policy question only for Core V0 L1 research eligibility. The earlier
Opportunity shadow policy remains its own `COMMITTED / SHADOW ONLY` authority
and is not rewritten here.

Key source evidence hashes used by this closure:

| Evidence | SHA256 |
|---|---|
| Phase 1 report | `DB0005B930BEC77C512DD4823AF4ABCC950555E5AE0139B58C13E5FE7E7CDFE0` |
| Phase 1 protocol/preflight JSON | `7B957477CCA04AEC3B0D0BE94D434B5E0229FB391842DABF79971DD8829A0437` |
| REC-A1 Freeze closure | `DD586413F5F3625A66B54A7B6AB9B78B163C6508CA4232E62C04D258B500CEDC` |
| Historical OHLCV closure | `83182A800F933FEA40CCDA6A72824FFE7C19DDDC375295BA2E41B87C2D4FE3CA` |
| PIT Topic closure | `300F1E4C4A6B0B9D4985DF1E43ADE26DA99C4BCFF5D116179B758E15F75EC4F0` |
| WS2 Technical V0 policy | `A951AA565AEE6E5EA6A104EF34F580855C12ED6AEC7EA29FE161BA07CB2AC67F` |
| WS2 continuity closure | `171D718A25DCD65FCF6C12659D357500C08E30A573C9493EECD2D8C0BFD9FD2C` |
| Opportunity technical evidence report | `F93EE2D3F22C99AB50B7810F66DBA3DF2162EC874E85474BE9299E2461A765DD` |
| Opportunity strategy implementation | `A43F931484D4B88CE195210E93A2C2F2C227822EE326E70B2F26DDE1E4355184` |

The complete source-to-canonical evidence list is in
`candidate-definition-disposition.json`.

The evidence SHA256 values above use UTF-8 bytes with CRLF normalized to LF.
This is intentional: the repository checkout has `core.autocrlf=true`, so a
raw working-tree hash can differ while the committed source/canonical content
and Git blob remain identical.

## New Owner decision: MA60 global eligibility

```text
Decision ID: WS3-L1-MA60-001
Decision: Close(T) >= MA60(T)
Scope: Core V0 current research universe, L1 common eligibility
Provenance: explicit NEW OWNER DECISION in this task
```

Repository reconciliation:

- WS2 `stock.sma.close.v1` defines a deterministic candidate algorithm: accepted
  daily close, period 60, arithmetic mean of the last 60 accepted observations,
  inclusive window ending at `T`.
- WS2 continuity closure says general `CONTINUITY_PASS` authority is not yet
  established; `FAIL`/`UNKNOWN` must fail closed.
- Opportunity evidence implements MA60 as shadow evidence, while its shadow
  qualification policy previously treated 60MA as a factor rather than a hard
  gate and left the gate open.

Formal Core V0 interpretation:

```text
L1_PASS(T) iff
  common session/identity/history prerequisites pass
  AND canonical Close(T) is available
  AND formal-as-of MA60(T) is available
  AND the 60-observation window has valid lineage
  AND continuity = CONTINUITY_PASS
  AND Close(T) >= MA60(T)
```

An unavailable MA60 is not a below-MA60 result. It remains unavailable or
blocked by the WS2 dependency. The Owner decision is not a request to implement
WS2 in this task.

## L1-L5 separation

| Layer | Authority result |
|---|---|
| L1 Common eligibility | Owner-approved Core V0 policy `Close(T) >= MA60(T)`; technical evaluation depends on WS2 MA60 evidence and continuity semantics |
| L2 Candidate formation | A1/A2/A3/Catch-up concepts remain separate and frozen at `T`; no future information |
| L3 Technical/topic evidence | RSI/MACD/volume/MA slope/return/topic fields remain evidence unless a future frozen definition promotes one |
| L4 Entry/risk | Support distance, structural failure, stop/risk and similar conditions remain separate from candidate identity unless explicitly frozen |
| L5 Evaluation outcome | T+1/3/5/10 only; no backward flow to L1-L4 |

## Breakout Reference Authority audit

| Candidate reference | Evidence | Classification | PIT/determinism result | Owner decision |
|---|---|---|---|---|
| Prior-high / rolling-high / swing-high | No Core V0 authority found; related range/support code is generic or shadow | `UNKNOWN / OWNER INTENT` | A reference could be computed deterministically only after an approved definition and window; no current authority | Required |
| Resistance / consolidation range | `range_detector.py`, detector docs, and Opportunity technical evidence | `COMMITTED PROVISIONAL / SHADOW` | Parameters and meaning are not PM-frozen for Core V0; no automatic authority transfer | Required |
| Breakout level / confirmation | Opportunity evidence and shadow composer | `COMMITTED PROVISIONAL / SHADOW` | High/close, margin, gap, one/multi-session and volume roles unresolved | Required |
| Legacy V1/fixture reference values | Historical/synthetic traceability | `HISTORICAL_ONLY` | Not a current PIT-safe authority | Not applicable |

Conclusion: A1 and A2 remain blocked by
`BLOCKED_BY_BREAKOUT_REFERENCE_AUTHORITY`; A2 additionally has unresolved
confirmation semantics. No threshold was selected.

## Candidate conclusions

### A1 ? Pre-Breakout

- Current semantic: `NOT_YET_BREAKOUT + STRUCTURE_IMPROVING + NEAR_VALID_REFERENCE`.
- Canonical: research label, common PIT/OHLCV envelope, and shadow technical
  evidence primitives.
- Owner intent only: the conceptual identity above.
- Unresolved: reference type and version, PIT reference construction,
  near-reference semantics, structure-improving semantics, exact formation
  fields, and thresholds.
- Owner decisions required: breakout reference, proximity, structure-improving
  meaning, evidence-versus-formation role.
- Final: `BLOCKED_BY_BREAKOUT_REFERENCE_AUTHORITY`.

### A2 ? Confirmed Breakout

- Current semantic: `VALID_PREEXISTING_REFERENCE + BREAKOUT_AT_T +
  CONFIRMATION_REQUIREMENT`.
- Canonical: research label and shadow breakout evidence only.
- Owner intent only: the conceptual identity above.
- Unresolved: reference, high-versus-close, confirmation, margin, gap,
  one-versus-multi-session, extended-breakout placement, volume role, and
  RSI/MACD role.
- Owner decisions required: reference and confirmation policy.
- Final: `BLOCKED_BY_BREAKOUT_REFERENCE_AUTHORITY`.

### A3 ? Pullback / Retest

- Current semantic: prior strength/breakout/structure improvement followed by a
  valid support retest without structural failure.
- Canonical: shadow support/retest evidence and future
  `PULLBACK_ACCEPTANCE` slot; no frozen support/retest authority.
- Owner intent only: support/retest concept and failure distinction.
- Unresolved: support authority, conversion of breakout reference to support,
  acceptance sessions, ?5% historical-design meaning, failure semantics, and
  risk-versus-formation placement.
- Owner decisions required: support, acceptance, failure, and layer placement.
- Final: `BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY`.

### Catch-up ? intra-topic only

- Current semantic: `STRONG-TOPIC-RELATIVE LAGGARD BECOMING STRONGER`.
- Canonical: provisional `CATCH_UP` shadow input shape and relative-gap
  evidence; current shadow policy is not a Core V0 frozen definition.
- Owner intent only: intra-topic catch-up.
- Unresolved: strong-topic authority, laggard identity, improvement semantics,
  required historical Topic context, and threshold policy.
- Owner decisions required: strong-topic, laggard, improving, and Topic-field
  roles.
- Cross-topic Rotation: deferred/separate research concept.
- Final: `BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY`.

## Candidate-level disposition

| Candidate | Global eligibility | Reference | Formation | Technical dependency | Topic dependency | Temporal | Minimum panel | Forward outcomes | Owner decisions | Final |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | `READY_AFTER_WS2_MA60_EVIDENCE` | `BLOCKED_BY_BREAKOUT_REFERENCE_AUTHORITY` | `BLOCKED_BY_STRUCTURE_IMPROVING_AUTHORITY` | MA60 required for L1; other technical fields not promoted | PIT membership/context as required; Score/Grade/Lifecycle not required by current intent | `BLOCKED_BY_CANDIDATE_DATE_PANEL` | `BLOCKED_BY_BREAKOUT_REFERENCE_AUTHORITY` | `BLOCKED_BY_FORWARD_OUTCOME_PANEL` | reference, proximity, structure-improving | `BLOCKED_BY_BREAKOUT_REFERENCE_AUTHORITY` |
| A2 | `READY_AFTER_WS2_MA60_EVIDENCE` | `BLOCKED_BY_BREAKOUT_REFERENCE_AUTHORITY` | `BLOCKED_BY_CONFIRMATION_AUTHORITY` | MA60 required for L1; breakout technical evidence remains shadow | PIT membership/context as required; Score/Grade/Lifecycle not required by current intent | `BLOCKED_BY_CANDIDATE_DATE_PANEL` | `BLOCKED_BY_BREAKOUT_REFERENCE_AUTHORITY` | `BLOCKED_BY_FORWARD_OUTCOME_PANEL` | reference, confirmation, margin/gap/session/volume roles | `BLOCKED_BY_BREAKOUT_REFERENCE_AUTHORITY` |
| A3 | `READY_AFTER_WS2_MA60_EVIDENCE` | Prior reference/support unresolved | `BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY` | MA60 required for L1; support/retest evidence remains shadow | PIT membership/context; no global Historical Topic prerequisite | `BLOCKED_BY_CANDIDATE_DATE_PANEL` | `BLOCKED_BY_SUPPORT_AUTHORITY` | `BLOCKED_BY_FORWARD_OUTCOME_PANEL` | support, acceptance, failure, layer placement | `BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY` |
| Catch-up | `READY_AFTER_WS2_MA60_EVIDENCE` | Not applicable to current intra-topic identity | `BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY` | MA60 required for L1; relative strength remains shadow evidence | `BLOCKED_BY_HISTORICAL_TOPIC_CONTEXT` | `BLOCKED_BY_CANDIDATE_SPECIFIC_WARMUP_LINEAGE` | `BLOCKED_BY_HISTORICAL_TOPIC_CONTEXT` | `BLOCKED_BY_FORWARD_OUTCOME_PANEL` | strong topic, laggard, improving, Topic fields | `BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY` |

The four candidates are independent. A1/A2 do not wait for Catch-up's Topic
context, and A3 does not become ready merely because A1/A2 are resolved.

## Reverse dependency summary

| Dependency | A1 | A2 | A3 | Catch-up | Classification |
|---|---|---|---|---|---|
| Canonical OHLCV through T | Required | Required | Required | Required | `REQUIRED_FOR_ELIGIBILITY` and candidate-specific formation inputs |
| PIT membership/context | Minimum context if the candidate universe requires it | Minimum context if required | Minimum context if required | Topic context required | `REQUIRED_FOR_FORMATION` only where definition assigns it |
| REC-A1 Freeze | Outcome integrity exclusion under frozen policy | Same | Same | Same | Not a candidate-formation dependency; R1 gap carried forward |
| WS2 MA60 evidence | Required for L1 | Required for L1 | Required for L1 | Required for L1 | `REQUIRED_FOR_ELIGIBILITY`, bounded WS2 dependency |
| WS2 RSI/MACD/volume/MA slope/return | Not required by current intent | Not required by current intent | Not required by current intent | Optional evidence only | `OPTIONAL_EVIDENCE` until a frozen definition says otherwise |
| Breakout/reference authority | Required | Required | Prior reference may be required | Not required for current intra-topic identity | `REQUIRED_FOR_FORMATION` where applicable; currently blocked |
| Support/pullback acceptance | Not required | Not required | Required | Not required | `REQUIRED_FOR_FORMATION` for A3; authority missing |
| Historical Topic Score/Grade/Lifecycle | Not required by current intent | Not required by current intent | Not required globally | Required to prove strong-topic context if chosen by definition | `REQUIRED_FOR_FORMATION` only for Catch-up; currently unavailable/formal publication deferred |
| T+1/T+3/T+5/T+10 | Evaluation only | Evaluation only | Evaluation only | Evaluation only | `REQUIRED_FOR_EVALUATION`, never formation |

The complete machine-readable matrix is in
`reports/TASK-REC-A1-CORE-V0-CANDIDATE-DEFINITION-AUTHORITY-CLOSURE-20260816/candidate-dependency-matrix.json`.

## Human-readable Owner Decision Table

The full field-level table is machine-readable in
`candidate-owner-decision-table.json`. The bounded human-readable summary is:

| Decision ID | Candidate / layer | Question | Evidence-supported disposition | Blocks | Does not block | Owner approval |
|---|---|---|---|---|---|---|
| `WS3-L1-MA60-001` | All / L1 | What is current Core V0 universe eligibility? | Formalize explicit Owner decision `Close(T) >= MA60(T)` for Core V0 L1 only | Date-level eligibility where formal MA60 evidence is unavailable | WS1, candidate authority audit, shadow policy unchanged | No; explicit task decision |
| `WS3-L1-MA60-002` | All / L1 | Which authority computes MA60? | Consume WS2 `stock.sma.close.v1`; no WS3 duplicate | L1 date-level execution until WS2 evidence/continuity is available | Candidate-definition closure | Yes for downstream technical publication/acceptance |
| `WS3-A1-REF-001` | A1 / L2 | Which reference defines near-breakout? | `OWNER_POLICY_DECISION_REQUIRED` | A1 formation | A2/A3/Catch-up audit | Yes |
| `WS3-A1-FORM-002` | A1 / L2 | What means near-reference and structure-improving? | `OWNER_POLICY_DECISION_REQUIRED`; no RSI/MACD/volume threshold invented | A1 definition freeze | L1 MA60 policy and evidence classification | Yes |
| `WS3-A2-REF-003` | A2 / L2 | What reference and confirmation define breakout at T? | `OWNER_POLICY_DECISION_REQUIRED` | A2 formation | A1/A3/Catch-up audit | Yes |
| `WS3-A2-EVID-004` | A2 / L3 | Are volume/RSI/MACD formation or evidence? | Evidence only unless explicitly frozen | Only a future definition that promotes them | Current closure | Yes for promotion |
| `WS3-A3-SUPPORT-005` | A3 / L2 | What is valid support, acceptance, and failure? | `OWNER_POLICY_DECISION_REQUIRED` | A3 definition freeze | A1/A2 and L1 audit | Yes |
| `WS3-CATCHUP-006` | Catch-up / L2 | What is strong-topic, laggard, and improving? | `OWNER_POLICY_DECISION_REQUIRED`; intra-topic only | Catch-up formation | A1/A2/A3 audit | Yes |
| `WS3-FUTURE-007` | All / L2-L3 | Should MA60 B-path or cross-topic Rotation enter current Core V0? | `DEFERRED_FUTURE_RESEARCH` | None in current A-path | Current bounded closure | No new current-path approval |

## Deferred future research

- MA60 ABOVE/BELOW/CROSSING feature/B-path and A/B replay: `DEFERRED_FUTURE_RESEARCH`.
- Cross-topic Rotation: `DEFERRED / SEPARATE_RESEARCH_CONCEPT`.
- Advanced Technical: deferred; no OHLCV proxy may be labelled Order Flow.

## Validation and execution boundaries

This is a documentation/policy/machine-readable authority task. Application
tests, DB/PostgreSQL, migration, API, frontend, candidate panel generation,
forward-outcome generation, walk-forward, performance metrics, Strategy Review,
recommendation, Production, scheduler, G1/G2/G3, and Canary are
`NOT_RUN_BY_SCOPE` or `PRESERVED / NOT_RERUN`; no fresh PASS is claimed.

Validation includes Markdown/path checks, JSON parsing, matrix consistency,
Owner Decision Table/report consistency, dependency consistency, frozen-protocol
unchanged check, REC-A1 identity check, NEXT_TASK hash check, `git diff --check`,
scope/write-set audit, secret scan, and source-to-canonical provenance.

```text
CANONICAL_STATUS=CANONICALIZED
CANONICAL_RECONCILIATION_DISPOSITION=CANONICALIZED
RELEASE_STATUS=NOT_A_RELEASE_CANDIDATE
PRODUCTION_VERIFICATION=NOT_RUN
CLEAN_SOURCE_STATE=PASS
REPRODUCIBLE_DEPENDENCY_STATE=NOT_REQUIRED_BY_SCOPE
SOURCE_COMMIT_SHA=cf027c1a9a13f669186d4c0e07a06f184484491b
SOURCE_VALIDATION_HEAD=c9b0cf4ff636033b900cb62562af3f1488f63fdc
CANONICAL_PROMOTION_SOURCE_COMMIT=c9b0cf4ff636033b900cb62562af3f1488f63fdc
CANONICAL_PROMOTION_COMMIT=73ce4499ac8d73cc749ee888e209970a65f68413
FINAL_CANONICAL_HEAD_AT_PROMOTION=73ce4499ac8d73cc749ee888e209970a65f68413
CANONICAL_PROMOTION_METHOD=EXPLICIT_GIT_PATCH_SOURCE_BLOB_ALIGNMENT_AND_COMMIT_ONLY
HUNK_LEVEL_RECONCILIATION_USED=NO
HEAD_INDEX_WORKTREE_AUDIT=PASS_FOR_TASK_WRITE_SET
POST_RECONCILIATION_CLEAN_CANDIDATE=PASS_FOR_TASK_WRITE_SET
OWNER_DIRTY_STATE=PRESERVED
WALK_FORWARD_EXECUTED=NO
PERFORMANCE_METRICS_GENERATED=NO
STRATEGY_ACCEPTED_OR_REJECTED=NO
PRODUCTION_MUTATION=NO
NEXT_TASK_CHANGED=NO
```

The final observed canonical HEAD may advance with unrelated parallel owner
commits; the promotion-time HEAD above is the exact SHA containing this task's
accepted write-set. Cleanup and final observed owner/worktree state are
recorded in the completion handoff.

# WS1/L3 — Topic Lifecycle Strength Evidence Contract Research

## Closure identity

| Field | Result |
|---|---|
| `TASK_ID` | `WS1-L3-TOPIC-LIFECYCLE-STRENGTH-EVIDENCE-CONTRACT-RESEARCH-20260822` |
| `WORKSTREAM` | `WS1_ONLY` |
| `SCOPE` | Research / contract-only; no production Strength rule |
| `SOURCE_REPO` | `C:\\Users\\acer\\Desktop\\題材領航\\topicpilot-platform` |
| `SOURCE_HEAD_AT_READ` | `b569430d2a358cab6a5915aeaacff2810df4913c` |
| `SOURCE_BRANCH_AT_READ` | `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` |
| `BASELINE_WORKTREE` | Dirty/untracked Owner state preserved; 184 status entries at baseline read |
| `WRITE_SET` | This report directory only |
| `L2_DEPENDENCY` | `NOT_USED`; no conclusion depends on the parallel L2 result |
| `LIFECYCLE_POLICY_CHANGED` | `NO` |
| `STRENGTH_PRODUCTION_RULE` | `NO` |
| `TOTAL_SCORE_CREATED` | `NO` |
| `HISTORICAL_RECONSTRUCTION` | `NO` |
| `DB_MUTATION` | `NO` |
| `PRODUCTION_PUBLICATION` | `NO` |
| `DEPLOY` | `NO` |
| `PUSH` | `NO` |
| `NEXT_TASK_CHANGED` | `NO` |

## Executive conclusion

Strength V0 is definable now only as a **research/read-model evidence
contract**, not as a production strength classifier. The safe candidate is:

> `Topic Strength Evidence Contract V0 = grouped raw evidence vector with
> explicit availability, provenance, and quality metadata; no overall level,
> no 0–100 score, and no browser inference.`

The recommended form is **A — Raw evidence vector only**, with dimension
grouping for Participation, Intensity, and Persistence. Dimension grouping is
for discoverability and downstream research; it does not imply that every
dimension has a valid strength label. Participation and Intensity have usable
current raw evidence. Persistence has only lifecycle-state persistence context
today, not enough evidence to call market strength persistent.

This is intentionally independent from Lifecycle. Lifecycle remains the
backend-owned five-stage state machine (`SPROUTING`, `FERMENTING`,
`MAIN_RISE`, `MATURE`, `DECLINING`) governed by
`topic-lifecycle-policy.provisional.1`. Strength does not reclassify a stage,
change persistence/hysteresis, change confidence, or replace the existing
leader-proxy behavior.

## Evidence basis and boundary

The current engine already exposes the relevant raw evidence groups:

- Participation/diffusion: `positiveBreadth`, observed/expected member counts,
  and `coveragePct`.
- Intensity/group strength: `averageChangePct`, `strongBreadth`, and
  `weakRatio`.
- Leadership: `leaderChangePct`, leader identity/role, semantic availability,
  and `positiveContributionShare`.
- Persistence/process: previous stage, previous candidate, candidate streak,
  stage entry date, and stage trading days.
- Quality: confidence, sample confidence, coverage confidence, valid/observed
  counts, small-sample flag, data/evaluation status, and version lineage.

Evidence is present in the shadow lifecycle result, not as a new production
Strength authority. The product and WS1 navigation documents explicitly keep
Lifecycle separate from Score/Grade and keep the frontend consumer-only. The
formal API currently carries lifecycle evidence/confidence as backend fields,
while the current Topic read model still marks Lifecycle as
`SHADOW_AVAILABLE`/`FORMAL_NOT_WIRED` or unavailable. This task does not alter
that boundary.

## Final answers to the required questions

1. **Can Strength V0 be defined now?** Yes, as an evidence-vector/read-model
   contract. No, as a production classifier or market-strength policy.
2. **A/B/C recommendation?** A. Raw evidence vector only, grouped by the three
   dimensions. It has the lowest semantic and overfitting risk and is the most
   reconstructable with current inputs.
3. **Participation / Intensity / Persistence evidence?** Participation uses
   positive breadth as the primary participation fact, with strong breadth and
   weak ratio retained as related/counter evidence. Intensity uses average
   member change as primary and leader-change proxy as supplemental shadow
   evidence. Persistence exposes stage age and candidate streak as lifecycle
   process context; recent rolling breadth persistence is unavailable.
4. **Quality metadata?** Coverage, expected/observed/valid counts, sample and
   coverage confidence, overall confidence, small-sample state, data status,
   evaluation status, policy/calculation version, evaluation mode, and
   lineage/finality are quality/provenance, not Strength components.
5. **Overall Strength level?** No for V0. Keep `overallLevel = null` and make
   any future ordinal level a separately approved version.
6. **0–100 score?** No. `TOTAL_SCORE_CREATED=NO`; a fixed weighted score is
   rejected/deferred.
7. **Leader proxy limitation?** It is a labelled `maxObservedChange` proxy
   when no approved role semantics exist. It can be shown as supplemental
   evidence with `leaderSemanticAvailable=false`; it cannot be called a formal
   Leader, define Strength alone, select a Lifecycle stage, or become an
   authority for WS3.
8. **What can canonical runtime provide now?** The existing shadow evidence
   groups, lifecycle state/transition context, stage age, candidate streak,
   raw breadth/intensity values, confidence and quality metadata, subject to
   existing SHADOW/unavailable status.
9. **What waits for historical reconstruction/future evidence?** Rolling
   breadth persistence, stable within-stage strength labels, future outcome
   validation, PIT-safe date coverage before the formal membership boundary,
   formal role/Leader authority, and any overall ordinal level.
10. **What can frontend safely display now?** Backend-provided raw evidence
    with its publication/data status; explicit Participation/Intensity values
    where present; `Persistence unavailable/provisional`; quality metadata as
    a data-quality disclosure; and the existing Lifecycle stage only under its
    current backend publication guard. It must not display a new strength
    grade, score, inferred label, or proxy as a formal leader.
11. **How can WS3 use it?** As a versioned exogenous research feature/vector
    for within-stage stratification, conditional expectancy, interaction tests,
    and missingness/quality controls. It must not rewrite A2, Legacy-5, or
    BOTH strategy definitions, eligibility, entry/exit rules, or production
    policy.
12. **Owner decision required?** Yes, before implementation/publication:
    accept A as the V0 contract; confirm that stage age/candidate streak are
    context rather than market-strength labels; approve the denominator and
    classifier lineage when a future read model is built; and approve a
    pre-registered historical validation protocol. No Owner decision is needed
    to keep the current proxy shadow-only or to preserve the existing
    Lifecycle semantics.

## Candidate contract shape

```text
strength.contractVersion = "topic-strength-evidence.v0"
strength.mode = "EVIDENCE_VECTOR"
strength.overallLevel = null
strength.score = null
strength.dimensions.participation = raw values + availability status
strength.dimensions.intensity = raw values + proxy limitations
strength.dimensions.persistence = lifecycle-context values + unavailable rolling fields
quality = data/replay/lineage quality only
lifecycle = existing backend Lifecycle object, unchanged
```

Dimension labels such as `WEAK/NORMAL/STRONG` are deferred. They require a
separate strength policy, frozen cut points, missing-data behavior, and
historical validation. They must not reuse Lifecycle thresholds merely because
the same raw metric appears in both domains.

## Validation performed and stop boundary

The repository, current HEAD, dirty state, WS1 series document, lifecycle
spec/engine, reports, schemas, read model, API adapter, and Topic List/Detail
consumer boundary were inspected read-only. The parallel L2 line was isolated
by scope and no L2 result was used. No application tests, database queries that
mutate state, migrations, backfill, reconstruction, deploy, push, publication,
or `NEXT_TASK` mutation was performed.

The nine files in this directory are the only task-owned writes. Existing
Owner dirty/untracked paths remain outside the write set. This closure stops
at contract research and returns the Owner decision surface above.

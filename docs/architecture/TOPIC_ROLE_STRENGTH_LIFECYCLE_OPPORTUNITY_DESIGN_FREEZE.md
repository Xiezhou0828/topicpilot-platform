# Topic Role / Strength / Lifecycle / Opportunity Design Freeze

Status: `DESIGN_FREEZE_RECONCILIATION`
Contract: `topic-strength-role-based.v2`
Lifecycle evidence contract: `topic-lifecycle-role-diffusion.v2`

This document is the canonical semantic boundary for the TopicPilot role,
strength, lifecycle, and opportunity chain. It is authoritative over the
legacy Breadth/Leadership implementation. It does not approve historical
calibration values or production activation.

## Frozen model

```text
REPRESENTATIVE / CORE / RELATED
              ↓
      shared daily role evidence
          ↙             ↘
 Absolute Strength   Relative Strength
              ↓
       role diffusion evidence
              ↓
          Lifecycle
              ↓
         Opportunity
```

The only formal Structural Roles are `REPRESENTATIVE`, `CORE`, and `RELATED`.
Structural Role answers the stock's structural function inside a Topic. It is
not Membership Type and it is not Relation Weight.

`REPRESENTATIVE` is Owner-governed Topic-facing authority. It is never chosen
from daily return, volume, rank, score, Relative Strength, or Opportunity
selection. `CORE` is the principal body and the dominant Daily Strength
allocation. `RELATED` is the peripheral diffusion layer and participates in
both Daily Strength and Lifecycle evidence.

Daily Strength has the frozen structural allocation `REPRESENTATIVE ≈ 30`,
`CORE ≈ 60`, `RELATED ≈ 10`, bounded to `0..100`. Members are transformed by a
role-specific response function, bounded before role aggregation, and then
combined by role. A broad coordinated CORE move must outrank one extreme CORE
outlier. RELATED is a bounded breadth/magnitude diffusion contribution and has
no per-member Score Importance.

Score Importance is separate from Relation Weight. Its legal current domains
are `REPRESENTATIVE {1.25, 1.50, 1.75}` and `CORE {0.50, 0.75, 1.00}`. It only
weights members inside its own role bucket and never creates bonus points or
changes Lifecycle/Opportunity evidence.

Absolute Strength uses actual member return. Relative Strength uses member
return minus the member's own market benchmark: TWSE → TAIEX and TPEx → TPEx
Index. There is no Topic-level blended benchmark. Absolute and Relative use
separate response curves and each has an explicit Grade.

Grade meanings are fixed: `D` confirmed weakness, `B` neutral/ordinary, `A`
clear coordinated strength, and `S` exceptional coordinated strength. `D`
requires directional negative evidence; a low numeric value alone is not D.
Exact curves, neutral bands, and Grade thresholds remain calibration inputs.

## Lifecycle boundary

Lifecycle stages remain exactly:

`BASE → SPROUTING → FERMENTING → MAIN_RISE → MATURE → DECLINING`

Lifecycle is role diffusion/expansion/decay evidence, not another Strength
score. Absolute evidence is primary. Relative evidence is confirmation or
early warning only and cannot transition a stage by itself. A max-gainer is
not a leader. A 70/30 CORE/RELATED blend is not a stage authority. REP may
support SPROUTING; FERMENTING is driven by CORE diffusion; MAIN_RISE requires
broad CORE plus substantive RELATED diffusion; CORE weakness with RELATED
strength is deterioration/MATURE evidence, not RELATED rescue. Hysteresis,
illegal backward-transition protection, and explicit reset remain required.

## Opportunity boundary

Opportunity consumes upstream outputs and never recomputes them. Absolute Grade
is the qualification baseline: S/A enter the formal universe, B may enter only
through governed warming/improving exception provenance, and D follows the
current exclusion policy. Relative A/S may support a B-grade exception but
cannot rewrite Absolute B to A. Relative D is context/ranking deterioration,
not an automatic hard exclusion. Existing technical responsibilities remain:
Close ≥ 20MA is a hard gate, missing 20MA defers, 60MA is structure/ranking
context, risk precedes ranking, and Trend/Catch-up remain independent.

## DO NOT INFER

- Do not add Dynamic Leader, Leader, Primary Leader, Hot Stock, or Momentum Member.
- Do not infer or rewrite Structural Role from price, score, rank, volume, or Opportunity.
- Do not map PRIMARY to REPRESENTATIVE or SECONDARY to RELATED.
- Do not inject Relation Weight into Strength, Grade, Lifecycle, or Opportunity.
- Do not use Breadth + Leadership as the new conceptual architecture.
- Do not use one max return as Lifecycle authority.
- Do not use Relative Strength alone to transition Lifecycle.
- Do not let RELATED rescue weak REP/CORE evidence.
- Do not let Relative Grade rewrite Absolute Grade.
- Do not calculate Strength, Grade, Lifecycle, or Opportunity in the frontend.
- Do not hard-code illustrative market-feel percentages as approved production knots.
- Do not treat provisional fixtures or descriptive calibration distributions as approval.
- Do not rewrite historical rows produced by prior policy/calculation versions.
- Do not deploy, migrate Production, or push without separate authorization.

## Version and readiness rules

Legacy Breadth/Leadership rows remain attributable to their original policy and
calculation versions. The new role-based contract returns
`CALIBRATION_REQUIRED` when explicit curves are absent and remains
`PROVISIONAL` until empirical calibration and Owner approval exist. Production
readiness is therefore `NO` for this reconciliation.

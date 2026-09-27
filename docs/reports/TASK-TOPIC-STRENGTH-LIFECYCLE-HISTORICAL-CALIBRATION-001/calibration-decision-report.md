# Historical Calibration Decision Report

Status: `COMPLETE_WITH_BOUNDED_DATA_LIMITATION`

This task preserved the Design Freeze and built the read-only calibration
pipeline, but it did not fit numeric values because the available committed
evidence cannot establish a strict point-in-time calibration dataset.

## Evidence decision

The repository contains:

- canonical price-only evidence for 507 instruments and 63,826 rows from
  2026-02-02 through 2026-08-13;
- a separate non-Production 603-instrument bootstrap report covering
  2024-08-13 through 2026-08-13;
- 460 bounded formal PIT topic-day cells from 2026-08-07 through 2026-08-13.

The 460 formal cells are fail-closed for strict calibration because the prior
audit records a current-only historical membership adapter, adjustment and
corporate-action continuity as unknown, a 4,240-versus-4,236 member-fact
reconciliation gap, and no committed same-date TAIEX/TPEx Index benchmark
export. The broader 130-topic reconstruction is explicitly current-taxonomy,
unknown-lineage research output and is not calibration truth.

Therefore the strict calibration dataset has:

```text
PIT_APPROVED_ROLE_ROWS=0
ELIGIBLE_TOPIC_DAY_COUNT=0
BENCHMARK_ELIGIBLE_ROWS=0
```

No curve knots, grade bands, D guards, lifecycle thresholds, or confirmation
periods were guessed. All candidate values remain `null` with status
`INSUFFICIENT_DATA`.

## Current versus calibrated candidate

| Area | FROZEN_PRODUCT_SEMANTIC | CURRENT_REPO_POLICY | CALIBRATED_CANDIDATE | EVIDENCE | REMAINING_GAP | OWNER_DECISION_REQUIRED |
|---|---|---|---|---|---|---|
| Absolute REP | Bounded, monotonic, nonlinear, earlier/smoother than CORE, saturating. | Boundary contract only; no formal knots. | No knots; `INSUFFICIENT_DATA`. | 0 strict PIT REP rows. | Approved role authority and member returns. | No semantic decision; data export authority required. |
| Absolute CORE | Primary group curve; broad coordinated strength dominates outliers. | Boundary contract only; no formal knots. | No knots; `INSUFFICIENT_DATA`. | 0 strict PIT CORE rows. | Approved role authority and member returns. | No semantic decision; data export authority required. |
| Absolute RELATED | 0–10 breadth plus magnitude quality, no negative daily points. | Boundary contract only; mapping open. | No mapping; `INSUFFICIENT_DATA`. | 0 strict PIT RELATED rows. | Approved related rows and a transparent magnitude calibration sample. | No semantic decision; data export authority required. |
| Absolute Grade | S/A/B/D; B neutral, D confirmed weakness. | Provisional fixture exists but is not calibration truth. | No bands or D guard; `INSUFFICIENT_DATA`. | No strict score distribution. | Calibrated role scores plus negative-direction evidence. | Later Owner policy approval. |
| Relative | Member-level excess return; TWSE→TAIEX, TPEx→TPEx Index; separate curve. | Contract exists; no benchmark-backed candidate. | No neutral band, curves, grades, or D guard; `INSUFFICIENT_DATA`. | 0 benchmark-eligible rows. | Same-date official benchmark export and PIT member rows. | No semantic decision; data export authority required. |
| Lifecycle | Role diffusion; Absolute primary; Relative confirmation only; hysteresis retained. | Provisional thresholds remain non-active. | No thresholds or persistence values; `INSUFFICIENT_DATA`. | 0 strictly reconstructable topic-day cells. | Multi-session PIT role evidence with lineage. | Later Owner policy approval. |

## Replay and diagnostics

The deterministic PM review CSV contains the required columns and blank Owner
judgment fields, but no rows were populated. All required replay scenarios and
diagnostics are explicitly marked `NOT_RUN_INSUFFICIENT_DATA`; no flattering
subset was selected.

No Opportunity recalibration was attempted. Existing Opportunity semantics were
only retained as a downstream compatibility boundary.

## Decision

`COMPLETE_WITH_BOUNDED_DATA_LIMITATION` is the accurate result. This is not a
product conflict and does not justify changing the frozen model. The next
bounded action is an owner-approved read-only export of PIT role authority,
formal membership, member returns, score-importance lineage, and same-date
TAIEX/TPEx Index observations from a non-Production canonical database.

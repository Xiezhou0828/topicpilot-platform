# Historical Calibration Disposition

```text
TASK_ID=TASK-TOPIC-CALIBRATION-DATA-FOUNDATION-CLOSURE-002
HISTORICAL_CALIBRATION_STATUS=HISTORICAL_CALIBRATION_NOT_FEASIBLE
OPERATING_MODE=OWNER_SEEDED_V0
OWNER_SEED_STATUS=PENDING_OWNER_INPUT
STRICT_PIT_CALIBRATABLE_TOPIC_DAY_COUNT=0
STRICT_PIT_CALIBRATABLE_MEMBER_DAY_COUNT=0
PRODUCTION_ACTIVE=NO
MIGRATION_APPLIED=NO
DEPLOYED=NO
PUSHED=NO
```

## Decision

Canonical repository, database-boundary, benchmark, and authority-lineage audit
did not produce a strictly reconstructable PIT Topic-day dataset. The formal
authority artifact begins on `2026-08-24`, while committed price evidence ends
on `2026-08-13`. The official TAIEX and TPEx Index history is ready, but it
cannot create missing historical membership or role authority.

Historical calibration is therefore declared `HISTORICAL_CALIBRATION_NOT_FEASIBLE`
for the audited window.

## Prohibited actions now closed

- No manual historical authority assembly.
- No current Structural Role retrofill into earlier dates.
- No relaxation of PIT eligibility or no-look-ahead requirements.
- No reduction of minimum-member or role-coverage standards to increase sample size.
- No numeric curve, grade, guard, lifecycle, or confirmation parameter selection.

## OWNER_SEEDED_V0 boundary

The workflow enters `OWNER_SEEDED_V0` as an owner-input mode only. No seed
values are supplied by this transition, and no parameter is activated. Any
future seed must be explicitly provided and approved by Owner, preserve the
REP/CORE/RELATED and Absolute/Relative/ lifecycle design freeze, and remain
non-production until separately authorized.

The original foundation evidence remains immutable evidence of the audit; this
disposition does not promote the prior runtime snapshots to PIT authority.

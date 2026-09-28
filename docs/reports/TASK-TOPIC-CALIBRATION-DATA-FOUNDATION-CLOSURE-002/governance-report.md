# Calibration Data Foundation Closure Report

```text
TASK_ID=TASK-TOPIC-CALIBRATION-DATA-FOUNDATION-CLOSURE-002
TASK_STATUS=COMPLETE_WITH_BOUNDED_AUTHORITY_LIMITATION
CANONICAL_BASE_SHA=c3542a900d6c46e07bc4243804e9705475023316
PRODUCTION_DB_MUTATED=NO
MIGRATION_APPLIED=NO
DEPLOYED=NO
PUSHED=NO
```

## Decision

Official TAIEX and TPEx Index history is exported with same-session dates, previous-close lineage, response hashes, and adapter versions. Strict calibration remains empty because the committed formal role artifact begins on 2026-08-24, after the committed price window.

The prior 460 bounded runtime snapshot cells and 4,235 closure member facts remain evidence-only. They are not silently promoted to PIT authority because the source reports a 4,235 vs 4,236 reconciliation mismatch and current-only lineage gaps.

## Readiness

- Price window: `2026-02-02..2026-08-13`
- Formal authority window: `2026-08-24..open`
- TAIEX sessions: `126`
- TPEx Index sessions: `126`
- Strict Topic-day rows: `0`
- Strict member-day rows: `0`
- Coverage metrics: membership `0/126`; structural role `0/126`; benchmark pair `126/126`; price `63826/63826`; strict topic-day `0/460`; strict member-day `0/4235`.
- Benchmark fetch errors: `0`

## Boundary

No curve knot, grade threshold, D guard, lifecycle threshold, confirmation day, score importance, or production policy was selected or activated. Migration 0047 remains ADDED_NOT_APPLIED.

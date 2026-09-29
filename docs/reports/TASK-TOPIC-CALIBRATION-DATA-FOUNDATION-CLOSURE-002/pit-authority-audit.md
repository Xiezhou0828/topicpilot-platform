# PIT Topic / Structural Role Authority Audit

- Status: `READY_BOUNDED_AFTER_PRICE_WINDOW`
- Authority version: `structural-role-authority-20260912.v4`
- Formal authority rows: `1160`
- Formal authority topics: `107`
- Effective from: `2026-08-24`
- Effective-to semantics: open-ended until a formally approved superseding row is visible.
- Query semantics: effective date is inclusive; future authority rows are rejected for an as-of date.
- Current-vs-historical rule: the current formal artifact is not backfilled into earlier price sessions.

## Resolution

The current formal artifact is internally deterministic: rows are approved, role values are constrained to REP/CORE/RELATED, and no supersession conflict is present. It begins after the committed price window, so strict historical topic-day reconstruction remains empty.

## Bounded limitations

- Pre-effective-date membership and structural-role history is not committed.
- Prior bounded runtime snapshots remain evidence-only and are not promoted to PIT authority.
- Historical correction lineage and Score Importance authority remain unavailable.
- The prior runtime evidence retains a 4,235 versus 4,236 reconciliation mismatch.

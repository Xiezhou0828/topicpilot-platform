# Lifecycle V1 Contract Reconciliation

## Preserved contract

- Stage vocabulary remains exactly `SPROUTING`, `FERMENTING`, `MAIN_RISE`, `MATURE`, `DECLINING`.
- Multi-topic stock membership remains Topic×Instrument aware; one accepted canonical price observation may support multiple topics without being treated as a duplicate.
- Lifecycle remains a backend/shadow read model. The frontend does not calculate stages.
- Strength remains raw structured evidence: Participation, Intensity, Progression, and Trajectory evidence fields. No score, grade, level, or new Strength label was created.
- `topic-lifecycle-policy.provisional.1` was not edited. The new `topic-lifecycle-policy.v1` carries the V1 topology/state semantics and retains the prior numeric boundaries.

## V1 additions

- Formal structural roles are carried from relation authority into member facts: `REPRESENTATIVE` (Lead), `CORE`, or `RELATED`, with `role_source`.
- Authority evidence is explicitly separated into Lead/Core and Related groups with conceptual 70/30 weighting.
- Related-only and Leader-only evidence cannot satisfy the Main Rise Core gate.
- Core breadth can compensate for weak Lead evidence when the Lead/Core gate, participation, and intensity conditions all hold.
- Lifecycle results persist `main_rise_segment`, `segment_entry_date`, `segment_anchor_date`, `days_since_meaningful_expansion`, `drawdown_from_peak_pct`, and JSON state memory.
- Migration 0033 adds the role-bearing fact columns and state-memory columns. It is schema-only and was not run against production.

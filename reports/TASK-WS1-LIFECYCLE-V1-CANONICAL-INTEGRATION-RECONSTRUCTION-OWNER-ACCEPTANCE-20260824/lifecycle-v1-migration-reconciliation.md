# Lifecycle V1 migration reconciliation

The actual canonical graph was:

```text
WS4 0033_task_ws4_reference_registry_transition_merge
  -> WS1 0034_task_ws1_lifecycle_v1_identity_state_machine (head)
```

The reconciled migration is additive and preserves the WS1 schema contract:

- `topic_snapshot_member_facts.structural_role`
- `topic_snapshot_member_facts.role_source`
- `topic_lifecycle_results.main_rise_segment`
- `segment_entry_date`
- `segment_anchor_date`
- `days_since_meaningful_expansion`
- `drawdown_from_peak_pct`
- `state_memory` JSONB

Disposable PostgreSQL qualification passed for clean bootstrap, existing release-head `0033` to `0034` upgrade, and the data-bearing `0032` source snapshot upgraded through `0033` to `0034`. The final graph has one intentional head and did not require a destructive reset. No production database was contacted or mutated.

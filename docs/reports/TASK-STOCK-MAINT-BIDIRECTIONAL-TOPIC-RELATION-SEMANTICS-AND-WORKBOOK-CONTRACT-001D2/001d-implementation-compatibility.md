# 001D implementation compatibility

| Surface | Change required? | Decision and reason |
|---|---|---|
| 001D proposal parser | YES | Accept `primary_topics/primary_weights` 0..N, empty lists, positional counts, representative_topic reservation, and compatibility aliases. |
| 001D workbook generator/exporter | YES | Emit plural fields and `|` pairs; remove the exactly-one-PRIMARY guard; preserve all PRIMARY rows. |
| Workbook validator | YES | Validate both positional pairs, 0..N cardinality, cross-role duplicates, exact identities, ranges, and optional representative_topic. |
| Authority table | NO | `relation_weight_authorities` is already one row/revision per exact relation and has no one-PRIMARY-per-stock constraint. |
| Formal reader | NO | Approved Relation Weight resolution remains exact relation-id/identity and APPROVED-only. |
| Staging model | NO schema change | Existing proposal objects already carry one `RelationWeightProposal` per relation; grouping is only a workbook serialization concern. |
| Canonical relation storage | NO | Existing `InstrumentTopicRelation` already stores multiple Topic rows and relation types. |
| Database migration | NO | Workbook shape changes do not require a database schema change; no migration was created or applied. |
| Topic Score / Leader / Structural Role consumers | NO | All remain separate authority and consumer boundaries. |
| Production / canonical data | NO | No rows, approvals, or canonical business values were changed. |

## Compatibility conclusion

`001D_DATABASE_MIGRATION_REQUIRED=NO` is evidence-backed. The required change
is a bounded admin/workbook serialization change. The candidate deliberately
does not add a runtime `representative_topic` reader or any Relation Weight
consumer.

## Verification

- `services/api/tests/test_relation_weight_authority.py`
- `services/api/tests/test_relation_weight_read_boundary.py`
- `services/api/tests/test_relation_weight_workbook.py`
- Python compile check for the changed module/test.
- Node `--check` for `build_stock_maintenance_workbook.mjs`.

All focused checks passed. PostgreSQL execution was not run and no Production
database was touched.

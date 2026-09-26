# Database maintenance Excel workflow

The canonical implementation lives in `E:\TopicPilot\topicpilot-platform` on `main`. The workbook is an Owner-facing input surface; it does not write PostgreSQL.

## Refresh

Run the read-only refresh command from the repository root:

```text
python scripts/admin/export_database_maintenance_workbook.py
```

Outputs are written to `E:\topicpilot-artifacts\database-maintenance-excel` and the read-only probe snapshot plus renders are written to `E:\topicpilot-temp\database-maintenance-excel`. If no database/API endpoint is available, the workbook explicitly records `UNAVAILABLE` and zero exported rows; it is still a valid contract artifact.

## Owner flow

1. Open `Maintenance_Input` and enter one operation per row.
2. Use `|` for topic and weight lists. Topic position N maps to weight position N.
3. Use `0..N` PRIMARY and `0..N` SECONDARY topics. Each relation has its own membership-importance weight.
4. Export normalized UTF-8 CSV/TSV and run `--validate-only`.
5. Review the normalized operation plan and validation errors, then run `--dry-run`.
6. Apply only in a separately authorized non-Production environment. The importer requires `TOPICPILOT_ALLOW_MAINTENANCE_APPLY=1`; formal weight rows are written as `PROPOSED`, never auto-approved.

## Canonical rules

- PRIMARY weight: inclusive `0.5..2.0`.
- SECONDARY weight: inclusive `0.3..0.8`.
- Topics must already exist, be formal active (`ACTIVE`, `ENABLED`, or `PUBLISHED`), and be effective on `AS_OF_DATE`.
- Unknown or disabled topics, duplicate/cross-role topics, misaligned lists, and out-of-range weights fail the whole batch.
- `REPLACE_RELATIONS` soft-deactivates omitted relations; it never hard-deletes.
- Representative Topic is optional and explicit. It is not inferred.
- Relation Weight means `TOPIC_MEMBERSHIP_IMPORTANCE` only and is not automatically Score, Heating/Cooling, Grade, Lifecycle, Leader, Today, or Opportunity.

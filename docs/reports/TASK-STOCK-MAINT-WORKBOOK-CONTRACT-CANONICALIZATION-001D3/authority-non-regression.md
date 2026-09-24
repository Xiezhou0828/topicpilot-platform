# Authority non-regression

001D3 changed only workbook validation and added round-trip fixtures. The
existing 001D authority implementation and migration lineage were not edited.

```text
AUTHORITY_TABLE_CHANGED=NO
FORMAL_READER_CHANGED=NO
DATABASE_SCHEMA_CHANGED=NO
MIGRATION_ADDED=NO
```

The formal Relation Weight reader remains APPROVED-only. Proposal values do not
fall back into formal reads. Structural Role, Leader, Score Importance,
Lifecycle, Today heating/cooling, Grade, and Opportunity semantics remain
unchanged.

Safety:

```text
PRODUCTION_MUTATION=NO
PRODUCTION_DATABASE_MUTATION=NO
PRODUCTION_MIGRATION_APPLIED=NO
DEPLOYMENT=NO
CANONICAL_DATA_MUTATION=NO
RELATION_WEIGHT_APPROVAL_EXECUTED=NO
001E_STARTED=NO
REMOTE_PUSH_EXECUTED=NO
MAIN_MERGE_EXECUTED=NO
LEGACY_SOURCE_MODIFIED=NO
```


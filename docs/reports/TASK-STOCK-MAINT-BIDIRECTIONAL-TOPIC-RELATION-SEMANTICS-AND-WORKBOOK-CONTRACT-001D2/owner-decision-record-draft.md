# Owner Decision Record draft — 001D2

`TASK_STATUS=COMPLETE_BIDIRECTIONAL_SEMANTIC_RECONCILIATION_WITH_WORKBOOK_CANDIDATE`

## Frozen decisions carried forward

```text
PRIMARY_RELATION_CARDINALITY=0..N
SECONDARY_RELATION_CARDINALITY=0..N
REPRESENTATIVE_TOPIC_CARDINALITY=0..1
REPRESENTATIVE_TOPIC_OPTIONAL=YES
REPRESENTATIVE_TOPIC_AUTO_DERIVATION=NO
```

## Directional models

`TOPIC_TO_STOCK_IMPORTANCE_MODEL=`

> Formal Structural Role Authority answers categorical Topic-to-Stock
> membership position (`REPRESENTATIVE`, `CORE`, `RELATED`). An explicit
> approved Topic Score Leader Set and projection-specific Score Importance may
> overlay that relation for the Score consumer only. No universal scalar or
> Leader/Representative equivalence is authorized.

`STOCK_TO_TOPIC_IMPORTANCE_MODEL=`

> A stock may have 0..N PRIMARY and 0..N SECONDARY Topic relations. Each exact
> stock–Topic–relation-type relation may have one separately governed Relation
> Weight representing Topic membership importance. Relation Weight is not
> Structural Role, Score Importance, ranking, Topic Score multiplier, or a
> representative-topic selector.

## Concept separation

| Concept | Decision |
|---|---|
| Structural Role | Topic → Stock categorical formal authority. |
| Leader | Explicit Topic Score consumer set; current approved production artifact remains unproven. |
| Score Importance | Projection-specific `1.00/0.75/0.50` weighted Leadership input. |
| Relation Role | Stock → Topic `PRIMARY`/`SECONDARY`, independently multi-valued. |
| Relation Weight | Stock → Topic membership-importance scalar, approved-only authority. |
| 題材順序 | Legacy/display priority only; never automatic representative authority. |
| 大族群內權重 | Parent/group hierarchy dimension; never a stock–Topic Relation Weight substitute. |
| Representative Topic | Optional Owner-curated display/identity candidate; reserved only, no runtime effect. |

## Contract and implementation decision

- Approve the plural workbook fields `primary_topics`, `primary_weights`,
  `secondary_topics`, and `secondary_weights` with `|` positional mapping.
- Preserve zero-topic rows and all multi-primary rows.
- Keep `representative_topic` optional and independent of PRIMARY membership.
- Keep exact relation identity validation and approved weight ranges.
- Keep workbook values as proposals/input; no automatic approval or canonical
  write is part of 001D2.

`001E_CAN_START_AFTER_THIS_TASK=YES`

This means the prerequisite workbook contract reconciliation is complete. It
does not mean 001E approval/apply was started here; the next task remains
Owner review and explicit canonical apply.

## Safety record

```text
PRODUCTION_MUTATION=NO
PRODUCTION_DATABASE_MUTATION=NO
PRODUCTION_MIGRATION_APPLIED=NO
DEPLOYMENT=NO
CANONICAL_DATA_MUTATION=NO
001E_STARTED=NO
LEGACY_SOURCE_MODIFIED=NO
```

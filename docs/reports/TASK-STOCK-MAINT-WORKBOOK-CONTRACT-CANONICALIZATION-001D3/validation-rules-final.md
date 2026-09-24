# Final validation rules

```text
PRIMARY_POSITIONAL_VALIDATION=PASS
SECONDARY_POSITIONAL_VALIDATION=PASS
PRIMARY_WEIGHT_RANGE_VALIDATION=PASS
SECONDARY_WEIGHT_RANGE_VALIDATION=PASS
DUPLICATE_TOPIC_VALIDATION=PASS
CROSS_ROLE_DUPLICATE_VALIDATION=PASS
ZERO_TOPIC_ROW_VALIDATION=PASS
```

Rules verified:

- `len(primary_topics) == len(primary_weights)`.
- `len(secondary_topics) == len(secondary_weights)`.
- PRIMARY weights are inclusive `0.5..2.0`.
- SECONDARY weights are inclusive `0.3..0.8`.
- Duplicate Topic tokens within one role are rejected.
- A Topic cannot be both PRIMARY and SECONDARY in one row.
- Duplicate numeric weights are allowed because they are positional values, not
  Topic identities.
- Empty PRIMARY and SECONDARY lists are valid.
- Optional `representative_topic` is validated against vocabulary only when a
  vocabulary is supplied; it is never auto-filled.
- Exact stock/Topic/relation identity must exist in the relation universe.
- Duplicate relation identities across workbook rows are rejected.


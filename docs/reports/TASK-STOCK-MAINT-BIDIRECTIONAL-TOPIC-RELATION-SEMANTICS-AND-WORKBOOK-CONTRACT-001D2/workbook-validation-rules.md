# Workbook validation rules

`WORKBOOK_VALIDATION_RULES_STATUS=PASS_DESIGN_AND_FOCUSED_TESTS`

The validator is fail-closed for values supplied by the Owner. It does not
fill missing values, infer representative Topics, or auto-approve authority.

## Rules

1. `market` and `symbol` are required trimmed identity values. `name` is
   display-only and may be empty when the relation authority has no name.
2. `primary_topics` count is `>= 0`; an empty list is valid.
3. `secondary_topics` count is `>= 0`; an empty list is valid.
4. `primary_topics` and `primary_weights` must have the same positional count.
5. `secondary_topics` and `secondary_weights` must have the same positional
   count.
6. Canonical list separator is `|`. The legacy 001D `;` separator is accepted
   only as a compatibility input; mixed separators and comma-separated values
   are rejected.
7. No duplicate Topic may occur within `primary_topics` or within
   `secondary_topics`.
8. The same Topic may not be both PRIMARY and SECONDARY in one stock row. No
   legacy evidence was found that requires cross-role duplication.
9. Every PRIMARY weight is finite and inclusive `0.5–2.0`.
10. Every SECONDARY weight is finite and inclusive `0.3–0.8`.
11. Every submitted relation identity must exactly match the supplied
    market + symbol + Topic + relation-type universe. Name-only joins are not
    accepted.
12. `representative_topic` is optional. It does not have to occur in
    `primary_topics`; if a formal/enabled Topic vocabulary is supplied, the
    validator may check membership in that vocabulary.
13. No automatic representative inference is allowed from order, first
    PRIMARY, highest Relation Weight, Structural Role, Leader, or Score
    Importance.
14. `effective_date`, `reason`, and `evidence_note` are proposal metadata;
    they do not create an APPROVED authority row.
15. Across multiple workbook rows, the same exact relation identity may appear
    only once.
16. Empty relation lists do not synthesize placeholder Topics and do not force
    a non-null PRIMARY.
17. Only enabled/formal Topic vocabulary should be supplied by the caller for
    strict vocabulary checking. The workbook parser never invents a Topic.

## Test evidence

`services/api/tests/test_relation_weight_workbook.py` covers:

- strict positional pairs;
- primary/secondary count mismatch;
- duplicate and unknown relation rejection;
- multi-primary preservation;
- zero-relation rows;
- optional representative_topic without automatic membership inference;
- cross-role duplicate rejection; and
- plural export with `|` pairs.

Focused result after the candidate change: **26/26** Relation Weight and
workbook tests passed, including **6/6** workbook tests. Python compile and
the maintenance generator Node syntax check also passed.

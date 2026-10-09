# Topics API remediation

## Bounded change delivered

The isolated remediation added a fixed, allowlisted forensic command named TOPICS_API_READ_MODEL_DIAGNOSTIC. It:

1. records sanitized read-only database identity;
2. reads migration metadata inside a nested savepoint so missing metadata privilege does not abort the diagnostic;
3. executes the same bounded formal Topic read-model query;
4. runs the same lifecycle, strength, item, and page validators;
5. emits bounded, secret-free failure layers and a root-cause classification;
6. has a workflow schema gate preventing arbitrary run IDs or trading dates.

Files are limited to:

- services/api/src/topicpilot_api/production_forensic_readback.py
- .github/workflows/production-forensic-readback.yml
- services/api/tests/test_production_forensic_readback.py

## Result

The change is a diagnostic/resilience improvement, not a fix for the live API route. Production has not been deployed with it, and the current API remains HTTP 500.

TOPICS_500_REGRESSION_TEST=PASS
TOPICS_API_FORMAL_INTEGRITY=NOT_VERIFIED
TOPICS_API_REMEDIATION=CANDIDATE_VALIDATED_NOT_DEPLOYED

## Confirmed minimal repair candidate

Render identified `ownerSeededV0.asOfDate` receiving a `datetime.date` from the persisted `snapshot_date` column while the public schema requires `str | None`. The isolated candidate converts only that field with `date.isoformat()` at the read-model boundary and adds a focused Pydantic contract test. It does not change the schema, query, formal authority, publication semantics, or database.

The candidate is validated locally but is not deployed to Production. The live API remains on 9703c956... and therefore remains HTTP 500 until an Owner-approved release is made.

Granting privileges, changing database objects, applying migrations, or deploying to Production was not performed.

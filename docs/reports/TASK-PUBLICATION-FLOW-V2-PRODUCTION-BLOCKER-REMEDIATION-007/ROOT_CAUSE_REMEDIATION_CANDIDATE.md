# Task 007 root-cause remediation candidate

## Confirmed Production evidence

Render API logs for live commit `9703c956....` show `/api/v2/topics` returning HTTP 500 with `fastapi.exceptions.ResponseValidationError`. The representative path is:

```text
response.items[20].ownerSeededV0.asOfDate
```

The input is `datetime.date(2026, 10, 7)`, while `TopicOwnerSeededV0Read.as_of_date` is `str | None`. The same error occurs across 45 collection items and as a single-item error for affected Topic slugs. The Render correlation group is `[ghnfx]`; no explicit request ID or SQLSTATE is present for this post-handler validation failure.

## Minimal isolated repair

`_strength_read` now converts a date-valued `snapshot_date` with `isoformat()` before it enters the public response model. A focused contract test proves that a PostgreSQL `date` becomes `2026-10-07` and validates through `TopicOwnerSeededV0Read`.

Candidate scope:

- one API read-model file;
- one focused API test;
- no schema change;
- no migration;
- no database write or privilege change;
- no frontend, Preview, scheduler, formal authority, Selection, or `NEXT_TASK` change.

## Validation

```ini
FOCUSED_TESTS=10 passed
FULL_API_REGRESSION=1392 passed, 79 skipped, 0 failed
RUFF=PASS
COMPILEALL=PASS
DIFF_CHECK=PASS
POSTGRESQL_COMPATIBILITY=BLOCKED_NO_AUTHORIZED_TEST_DATABASE
```

The candidate is not deployed. The live API remains on `9703c956...` and must not be treated as repaired until an Owner-approved release and Production readback show `/api/v2/topics` success.

## Separate unresolved Worker blocker

Worker logs still show `REFERENCE_PREFLIGHT_PendingRollbackError` every five minutes for 2026-10-08 after the provider wait. The compact Worker stream does not expose the first PostgreSQL exception or SQLSTATE. This remains a separate gate and is not remediated by the API serialization candidate.

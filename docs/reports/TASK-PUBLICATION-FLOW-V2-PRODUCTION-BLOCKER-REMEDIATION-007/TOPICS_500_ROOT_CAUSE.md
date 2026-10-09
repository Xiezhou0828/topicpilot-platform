# Topics API HTTP 500 root-cause status

## Reproduction and correlation

Production origin: https://topicpilot-api.onrender.com

Render API logs on 2026-10-09 contain repeated:

- GET /api/v2/topics?limit=1&offset=0 -> 500
- GET /api/v2/topics?limit=200&offset=0 -> 500
- GET /api/v2/topics/{slug} for 12 吋矽晶圓, ABF載板, IGBT／功率模組, MLCC, RISC-V and other deferred topics -> 500
- AI PCB slug -> 200
- some other slugs -> 200 or 404

Render's application-log stream exposes the traceback. For the representative request at 2026-10-09 04:39:48 GMT+8:

- correlation group: `[ghnfx]`;
- request: `10.26.146.221:57260 - "GET /api/v2/topics HTTP/1.1" 500 Internal Server Error`;
- route frame: `topicpilot_api/production_read_model_api.py`, line 147, `topics`;
- raw exception class: `fastapi.exceptions.ResponseValidationError`;
- collection response: 45 validation errors; single deferred Topic reads showed one validation error;
- representative detail: `('response', 'items', 20, 'ownerSeededV0', 'asOfDate')`, message `Input should be a valid string`, input `datetime.date(2026, 10, 7)`.

No explicit application request ID is emitted in the visible Render line; `[ghnfx]` is the available log correlation group. No SQLSTATE is present because this failure occurs during FastAPI response validation after the handler returns.

## Diagnostic result

The new fixed diagnostic uses the production route's bounded read-model query and response validators. Its current artifact reports:

- rootCause=READ_MODEL_DATA_OR_QUERY_FAILURE
- failure layer=READ_MODEL_QUERY
- PostgreSQL InsufficientPrivilege on topicpilot.topics
- metadata failure on public.alembic_version
- topicRowCount=0
- pageValidation=NOT_ATTEMPTED

This proves that the forensic role cannot inspect the tables. It does not prove that the API's own runtime role has the same permission failure. The Render traceback independently establishes the live route root cause: `_strength_read` copied a PostgreSQL `date` from `snapshot_date` into `ownerSeededV0.asOfDate`, while `TopicOwnerSeededV0Read.as_of_date` requires a string.

TOPICS_500_ROOT_CAUSE=CONFIRMED_SCHEMA_SERIALIZATION_DEFECT

The separate Worker `REFERENCE_PREFLIGHT_PendingRollbackError` remains unresolved at the database-transaction layer: the Worker log stream still exposes only the mapped reason and no earlier PostgreSQL exception or SQLSTATE. That is a separate blocker and is not used to explain the API 500.

No synthetic rows, empty-success fallback, authority change, database grant, migration, or speculative query change was made.

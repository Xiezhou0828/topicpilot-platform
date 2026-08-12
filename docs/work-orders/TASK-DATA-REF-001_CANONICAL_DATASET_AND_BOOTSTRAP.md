# TASK-DATA-REF-001 — `tw-reference-v1` canonical dataset and reference-only bootstrap

## Scope

Implement the reproducible canonical bundle and a separate PostgreSQL
reference-only bootstrap path after `TASK-DATA-REF-PROD-001` found that the
runtime contract had no production writer. This work does not run against
Production and does not alter OpenAPI.

## Implemented contract

- Offline `topicpilot-reference-bundle generate|validate` commands;
- committed `tw-reference-v1` bundle with source and file hashes;
- exact current derived universe: 2 markets, TPE 314, TWO 193, total 507;
- TWD, Asia/Taipei, REGULAR/TW_MARKET context;
- 23 holiday dates plus one suspended date from the supplied TWSE calendar
  authority;
- seven explicit trading-status codes, including `DELISTED` for the supplied
  6806 evidence;
- three explicit adjustment codes from the repository governance input;
- `reference_calendar_dates` migration and ORM model;
- explicit DRAFT/VALIDATED/ACTIVE/RETIRED lifecycle with a single ACTIVE
  partial unique index;
- atomic and idempotent
  `topicpilot-reference-bootstrap --dry-run|--activate`;
- existing `topicpilot-reference-check` extended to require persisted calendar
  dates while remaining SELECT-only;
- unit, contract, and PostgreSQL integration tests.

## Production boundary

`PRODUCTION_MUTATION = NO` for this repository task. Production execution,
deployment, Canary, Scheduler, G2, and G3 remain operator-authorized follow-up
work and must use `docs/operations/reference-bootstrap.md`.

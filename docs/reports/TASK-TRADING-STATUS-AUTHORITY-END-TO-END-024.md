# TASK-TRADING-STATUS-AUTHORITY-END-TO-END-024

Status: `CANDIDATE_COMMIT_READY`

This task stops at a local candidate commit. No merge, push, Production
deployment, Production database mutation, recovery run, or migration execution
was performed.

## Scope and baseline

- Initial main SHA: `3f012dda6f40a57fedd4cf47b7a5a62a1562d4b9`
- Worktree: `C:\Users\acer\Desktop\topicpilot-platform-TASK-020`
- Branch: `codex/task-024-trading-status-authority`
- Owner schedule context remains unchanged: `POST_CLOSE_START=13:45`
- The 2026-09-30 recovery is not performed by this task.

## Repository archaeology

- `EXISTING_STATUS_AUTHORITY`: canonical trading-status observations plus
  date-effective `ReferenceInstrumentLifecycle`; TASK-023 also supplied the
  availability taxonomy and read model.
- `EXISTING_EFFECTIVE_DATE_MODEL`: instrument and market `valid_from` /
  `valid_to`, lifecycle `effective_from` / `effective_to`, and canonical
  observations bound to a market-timezone `trading_date`.
- `EXISTING_EVENT_MODEL`: `RawMarketObservation` and
  `ObservationTimelineEntry` with canonical `supersedes_id`; there is no
  separate exchange-event table.
- `EXISTING_OPERATOR_SURFACE`: existing `/api/v1/admin` read-only dashboard,
  schema, instrument, relation, and authority-audit routes.
- `REUSE_DECISION`: reuse canonical observations, lifecycle evidence, raw /
  timeline lineage, existing availability classification, admin boundary,
  checkpoints, and publication readback. Add a typed resolver, bounded status
  service, operator read endpoint, and tests. Do not create a duplicate
  authority table.

## Authority and data model

The supported source boundary is the explicit status carried by the proven
official daily provider contracts:

- `TWSE_OFFICIAL_DAILY`: supported for explicit status tokens when present;
  no independent TWSE status-endpoint contract was proven in this repository.
- `TPEX_OFFICIAL_DAILY`: supported for explicit status tokens when present;
  no independent TPEx status-endpoint contract was proven in this repository.

News is not used as authority. Unsupported sources and unproven endpoint
contracts fail closed.

`TradingStatusAuthorityRecord` is a typed, date-effective service boundary over
the existing canonical evidence. It carries status, effective interval,
source, source reference, observation and publication timestamps, reason,
authority class, manual flag, supersession references, and expiry. Existing
canonical observations and lifecycle rows remain the persistence authority;
the implementation does not add a duplicate table or migration.

Normalization is exact and contract-backed. The supported canonical taxonomy
remains `AVAILABLE`, `NO_TRADE`, `SUSPENDED`,
`EXCHANGE_CONFIRMED_NO_DATA`, `HALTED`, `DELISTED`, `TERMINATED`,
`MISSING_MARKET_DATA`, `PROVIDER_ERROR`, `DATE_MISMATCH`, and `UNKNOWN`.
Unknown source values normalize to `UNKNOWN`; missing price alone never creates
`SUSPENDED`, `HALTED`, `NO_TRADE`, `DELISTED`, or `TERMINATED`.

## Effective daily resolver and precedence

`resolve_effective_trading_status(instrument, trading_date)` is implemented and
returns a typed result containing status, authority source, reason, effective
dates, source reference, resolution state, publication blocking, legitimate
unavailability, authority class, manual flag, and preserved event metadata.

Frozen precedence:

1. A valid same-session close resolves price availability first. A temporary
   halt event is preserved in the result and does not make the daily session
   unavailable when the close is valid.
2. Official exchange or existing date-effective lifecycle authority resolves a
   no-price session. Legitimate unavailable states are non-blocking for
   unrelated publication scopes.
3. A governed manual override is considered only when official authority is
   absent; it cannot overwrite or delete official evidence.
4. Missing or ambiguous authority remains `MISSING_MARKET_DATA` or `UNKNOWN`
   and blocks the affected dependency scope.
5. Provider failure is `PROVIDER_ERROR` and remains fail-closed.

Duplicate source/reference delivery is idempotent. Conflicting active
authority remains unresolved rather than being guessed. Effective-date,
expiry, and supersession boundaries are evaluated before selection.

## POST_CLOSE bounded resolution

POST_CLOSE invokes status resolution only for instruments whose same-session
price is missing or whose collection outcome requires classification. Normal
priced instruments do not enter the status-resolution window.

The status window is separate from historical price/network readiness retries:

- `STATUS_RESOLUTION_MAX_ATTEMPTS=3`
- `STATUS_RESOLUTION_MAX_TOTAL_WAIT=90` seconds
- `STATUS_RESOLUTION_BACKOFF=30` seconds

Environment overrides are available through
`TOPICPILOT_STATUS_RESOLUTION_MAX_ATTEMPTS`,
`TOPICPILOT_STATUS_RESOLUTION_MAX_TOTAL_WAIT_SECONDS`, and
`TOPICPILOT_STATUS_RESOLUTION_BACKOFF_SECONDS`. Empty or short operator lookup
responses are padded with unresolved fail-closed results; they cannot be
mistaken for a successful empty resolution.

The run records a `STATUS_RESOLUTION` checkpoint and structured metrics in run
metadata and the returned result. It does not replace or merge with the
existing price-provider readiness retry counters.

## Manual authority path

`ManualTradingStatusOverride` implements the validated service boundary for a
future governed write: operator identity, reason, source reference,
effective-date range, expiry, and supersession metadata are required as
applicable. It cannot carry or modify a price.

The repository does not currently provide a secure audited authority-write
infrastructure. Therefore the mutation surface is deliberately
`BOUNDED_DESIGN_ONLY`: there is no unsafe admin write endpoint and no manual
patch table. A separately governed, authenticated, audited write path is an
activation requirement.

## Operator surface and public boundary

Added read-only:

`GET /api/v1/admin/trading-status-authority`

It returns the effective daily operator read model with trading date, symbol,
name, market, resolved status, reason, authority provenance, effective dates,
last valid price, resolution state, legitimate-unavailable and blocking flags,
and affected Topic counts/slugs. It supports trading-date, market, status,
resolved/unresolved, blocking/non-blocking, limit, and offset filters. There is
no write operation.

TASK-023's detailed public Today/Home unavailable-instrument disclosure and
engineering coverage diagnostics were removed from the public API contract and
frontend. The internal unavailable/read model, fail-closed section behavior,
and normal product breadth semantics remain. No customer-facing navigation was
added.

Topic Strength, Daily Grade, lifecycle, Structural Role, Relation Weight,
Leader authority, and formal Topic-universe rules were not changed. Trading
status only affects price eligibility, typed exclusion, coverage/readiness, and
the affected dependency scope. No zero-fill, forward-fill, or fabricated close
was added.

## Migration disposition

- `MIGRATION_REQUIRED=NO`
- `MIGRATION_ID=NONE`
- Reason: existing canonical status observations, lifecycle rows, lineage, and
  read models support the authority cleanly; the new authority record is a
  typed resolver contract, not a second persistence model.
- Alembic graph: one existing head,
  `0047_task_topic_role_strength_design_freeze`.
- No development or Production migration was run.

## Validation evidence

- Focused trading-status, market availability, config, admin, and POST_CLOSE
  contract matrix: `77 passed`.
- Home/runtime regression scope: `80 passed, 1 skipped` (the skip requires a
  disposable PostgreSQL URL).
- Frontend build and regression scope: `184 passed`.
- API client generation completed; OpenAPI and generated declarations were
  updated from the canonical schema.
- OpenAPI drift check: passed.
- Ruff on all touched Python implementation and test files: passed.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.
- Full backend scope: `980 passed, 60 skipped, 5 failed`. The five failures
  are pre-existing WS3 confirmatory-validation tests whose required
  `reports/TASK-WS3-CORE-V0-A1-...` JSON artifacts are absent from this
  worktree; their stack traces do not touch this task's implementation. They
  were not repaired as unrelated work.

## Activation requirements after this candidate

Hold this candidate for multi-workstream canonical reconciliation and explicit
Owner authorization. A later task may independently prove or wire standalone
official status endpoints, add governed manual persistence/authentication,
promote the exact candidate SHA, verify runtime schedule `13:45`, and perform
the separately authorized terminal recovery. This task performs none of those
actions.

## Terminal invariants

- `PRODUCTION_DB_MUTATED=NO`
- `PRODUCTION_DEPLOYED=NO`
- `POST_CLOSE_RETRIED=NO`
- `PUSH_PERFORMED=NO`
- `MERGE_PERFORMED=NO`
- `TASK_TERMINAL_STATE=CANDIDATE_COMMIT_READY`

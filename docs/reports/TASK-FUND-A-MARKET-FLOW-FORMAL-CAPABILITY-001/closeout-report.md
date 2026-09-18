# TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001 closeout

## Result

`FUND_A_MARKET_FLOW: CANONICAL_CAPABILITY_READY`

The isolated E branch contains a formal, provider-backed, market-level daily
institutional-flow capability for TPE and TWO. The implementation commit is
`b062df38c6cd0bf6f238b849d2ff2600f5c63411`. The canonical repository head
remains `07b7a73e7cfd070aae39a2d61240bf5050e19e4a`; this branch is ready for
serial canonical reconciliation and is not yet canonicalized.

The governance packet commit is
`a5e54a9d73e57a466325417151beb895f55d1229`.

## What is ready

- Official TWSE `fund.BFI82U` and TPEx `tpex_3insti_summary` adapters with
  source identity, dataset, endpoint, unit, scale, source-as-of, retrieval
  time, response hash, and lineage.
- Typed buy/sell/net facts with total reconciliation and explicit availability:
  no missing field is converted to zero.
- Replayable `topicpilot.market_institutional_flow_daily` persistence with
  idempotent upsert and stale/conflict protection, migration `0041`.
- Read-only `GET /api/v2/market/institutional-flow` with current/previous,
  complete-only 5/20-session windows, streaks, acceleration, and evidence-only
  price/flow relation.
- Additive Home `marketOverview.institutionFlows` materialization and
  render-only Today Market display. Existing Today Signals label policy is
  unchanged; it can consume the formal nested evidence shape.
- OpenAPI, API client, generated schema, web declarations, fixtures, and tests.

## Boundaries and handoff

FUND-B, FUND-C, FUND-E implementation, Today Signals redesign, A10/A9, B2,
scheduler activation, deployment, canary, Production verification, and
Production migration execution were not performed. The existing post-close
job was not changed because provider publication is modeled as a separate
after-close asynchronous lifecycle.

The owner/integration step is to review shared surfaces, run migration `0041`
only in the approved non-Production environment, activate a separate FUND-A
capture schedule, and then perform serial canonical reconciliation. C-drive
owner checkout state was left untouched; no push was performed.

## Validation summary

Focused backend/API/Home checks passed 21 tests; API client tests passed 5;
Web build and tests passed 165. OpenAPI generation, Ruff, compileall, and
`git diff --check` passed. PostgreSQL round trip and Production verification
were not run because no database URL was configured and Production mutation was
out of scope. The bundled Alembic CLI exited with Windows native code
`-1073740022`; migration structure was independently validated as `0041 ->
0040` without contacting a database.

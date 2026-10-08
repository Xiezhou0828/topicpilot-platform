# TopicPilot Publication Flow V2 — Market-Staged EOD Design

Task: `TASK-PUBLICATION-FLOW-V2-MARKET-STAGED-REDESIGN-001`
Canonical reconciliation base: `b17355eaba3573ed43e48e25d98ffa89506327c1`
Timezone: `Asia/Taipei`

## Decision summary

The existing persistent Render worker and five-minute heartbeat remain. The
worker now treats the post-close path as a market-staged state machine:

```text
POST_CLOSE_PREFLIGHT
  -> WAITING_TWSE_WINDOW
  -> TWSE_INGESTING -> TWSE_SOURCE_READY
       -> TWSE_SAFE_COMPUTATION (NOT_FORMAL)
       -> TPEX_INGESTING -> TPEX_SOURCE_READY
  -> COMBINED_RECONCILIATION
  -> FORMAL_TOPIC / PIT -> STRENGTH / GRADE -> LIFECYCLE -> HOME
  -> PRICE_BASED_FINAL
  -> LATE_DATA_ENRICHMENT
  -> DAY_COMPLETE
```

The formal chain still has one authoritative full-market gate. A successful
TWSE-only computation is stored as operational/tracking output and cannot be
read as a published Formal Topic result.

## Current versus V2 behavior

| Area | Current baseline | V2 behavior |
|---|---|---|
| Worker | `topicpilot-live`, persistent worker | unchanged |
| Polling | 300 seconds | unchanged; times are eligibility windows, not exact triggers |
| 13:45 | POST_CLOSE starts the full provider path | session/reference/provider preflight only |
| EOD markets | TPE then TWO in one sequential list | TPE eligible at 15:37; TWO independently eligible at 15:42 |
| Retry | completed checkpoints can be reused, but both markets were attempted in the same pass | market-specific checkpoints; a pending TWO pass does not re-fetch completed TPE batches |
| Early work | downstream work waited for full collection | TWSE-only tracking/60MA refresh is explicitly `NOT_FORMAL` |
| Formal gate | daily reconciliation plus existing publishers | unchanged authority; requires combined accepted evidence and existing Formal readbacks |
| Institutional flow | fetched before Formal | separate `LATE_DATA_ENRICHMENT` lane from 18:33 |
| Deadline | 14:30 soft / 15:00 hard | 16:07 combined target / 17:00 price hard / 20:10 late-data hard |

## Operational timeline

All times are Taiwan local time. The worker may execute on the first poll at or
after a target, so actual checkpoint timestamps must be read from the run and
checkpoint authorities.

| Time/window | Eligibility and expected behavior |
|---|---|
| 13:45 | `POST_CLOSE_PREFLIGHT`: validate session, date, G2/reference/PIT context, provider registry inputs, run identity and prior checkpoints. No official EOD request. |
| before 15:37 | `WAITING_TWSE_WINDOW`; normal retryable wait. |
| 15:37 onward | TPE/TWSE batches become eligible. Date, source identity, coverage, OHLCV and status evidence remain provider-contract checks. |
| after TWSE checkpoints | `TWSE_SAFE_COMPUTATION` refreshes only TPE tracking/60MA data and is explicitly not Formal publication. |
| 15:42 onward | TWO/TPEx batches become independently eligible, even if TPE is still waiting. |
| 15:52 target retry | The bounded early retry window opens for incomplete TWO checkpoints. The next five-minute polling cycles retry only incomplete market checkpoints. |
| 16:07 | Combined reconciliation target. Proceed earlier when both markets are already ready; do not infer readiness from the clock. |
| 16:15 onward | Full Formal chain runs as soon as combined reconciliation and all existing Formal evidence gates pass. |
| 17:00 | Price-based hard deadline. A missing price market remains fail-closed and yields an explicit deadline receipt. |
| 18:33 onward | Institutional-flow late lane becomes eligible. Existing canonical facts are reused before another provider request. |
| 20:10 | Late-data deadline. Price Formal output is retained as authoritative, while the day remains explicitly late-data incomplete and the receipt is `DEADLINE_EXCEEDED`. |

## State and checkpoint contract

No new database enum or migration is required. Stage state is carried in the
existing `LiveCollectorRun.metadata_payload` and append-only
`LiveCollectorCheckpoint` stream.

Important checkpoint keys:

- `SESSION_VALIDATION`, `INPUT_READINESS`: preflight.
- `FORMAL_MARKET_FACTS:TPE:<n>`: TWSE market-local ingestion.
- `FORMAL_MARKET_FACTS:TWO:<n>`: TPEx market-local ingestion.
- `TWSE_SAFE_COMPUTATION`: TPE-only tracking/60MA computation; never Formal.
- `A9_B2_FORMAL_PROCESSING`, `FINAL_PUBLICATION`: existing Formal authority.
- `LATE_DATA_ENRICHMENT`: institutional-flow late lane.
- `COMPLETION`: run-level outcome.

`publicationStages` in run metadata exposes `preflight`, `twse`, `tpex`,
`twseSafeComputation`, `combined`, `formal` and `lateData`, including status,
target/next-eligible time, reason codes and selected readbacks. Receipt payloads
include this stage projection and `dayCompletionState`.

The TPE/TWO stage readback includes source identity, source data date, the
latest provider observation time when the provider contract emits one,
expected instrument count, accepted priced count, accepted trading-status
count, accepted coverage count (priced plus canonical covered no-trade
evidence), unavailable count, validation-failure count, skipped and retry
counts, last/next retry timestamps, error categories, batch progress and
checkpoint identity. If the provider contract does not emit an observation
timestamp, the field remains `null` with an explicit provenance reason; the
readback never substitutes retrieval time for source observation time. The
accepted trading-status count is derived from the existing canonical
no-trade/status authority rather than inferred from a missing price.

The state meanings remain deliberately distinct:

- `WAITING_TWSE_WINDOW` / `WAITING_TPEX_WINDOW`: clock eligibility wait;
- `*_WAITING` / `*_DATA_NOT_READY`: source publication or coverage wait;
- provider exception codes: actual provider failure evidence;
- reconciliation/formal readback failure: data or authority gate failure;
- `LATE_DATA_DEADLINE_EXCEEDED`: late lane terminal incompleteness.

## Concurrency boundary

The worker does not need a second worker or a new scheduler. Within one
polling cycle, TPE batches are processed before newly eligible TWO batches, but
TWO eligibility is not conditioned on completion of TWSE-safe computation. On
the next cycle, completed TPE checkpoints are skipped and only incomplete TWO
checkpoints are requested. A worker restart resumes the same deterministic run
identity and checkpoint namespace.

## Formal dependencies

The existing publisher chain is reused:

1. `TopicSnapshotEngine` reads canonical accepted price evidence and the
   effective PIT topic/member authority.
2. `materialize_bounded_formal_dates` creates the bounded Formal state only
   after the combined reconciliation gate.
3. `FormalStrengthPublisher` evaluates absolute and relative strength from
   published Formal snapshots, canonical member facts and market benchmark
   facts. Its persisted score/grade semantics are unchanged.
4. `FormalLifecyclePublisher` consumes Formal strength/grade derivatives,
   prior Formal state and candidate-streak history. Lifecycle semantics are
   unchanged.
5. Home and the existing receipt/readback remain downstream of those gates.

TWSE-only tracking data do not enter the Formal Topic snapshot, Formal
Strength, Formal Grade or Lifecycle publishers. No topic universe, manual
structural role, score formula, grade threshold, lineage or supersession rule
was changed.

## Late-data boundary

The current live path consumes official institutional flow rows. Those rows are
now fetched and read back by `LATE_DATA_ENRICHMENT`, separately from the
price-based Formal chain. Market index and aggregate facts remain part of the
price-based Formal/Home input because the current Strength and Home contracts
consume them. Margin financing/securities lending is not currently consumed by
the inspected live Formal path; this implementation does not invent a new
dataset or pretend it is complete. A separate owner decision is required if
those fields become a publication dependency.

Late data never overwrites or re-computes a finalized Formal result. If late
data are still pending, the receipt exposes `LATE_DATA_ENRICHMENT` and the day
is not reported as complete. After 20:10 the receipt is explicitly
`DEADLINE_EXCEEDED` while the already-authoritative price Formal output is
retained.

The non-Production E2E fixture in
`services/api/tests/test_publication_flow_v2_market_staged.py` drives the real
`PostCloseUpdater` TWSE-safe and late-data helpers against an in-memory
checkpoint ledger. It covers source wait, TWSE arrival, TPEx pending/arrival,
combined Formal authorization, late-window wait and late-data completion; it
does not contact an exchange or write a database.

## Recovery, idempotency and rollback

- A run stays retryable while source windows or late data are pending.
- Completed market checkpoints are reused; successful TPE batches are not
  re-fetched because TWO is pending.
- Formal re-entry first performs authoritative readback and does not invoke
  writers again when the existing Formal phase/readback already passes.
- Existing daily reconciliation, no-trade handling, source-date validation,
  canonical observation lineage, PIT membership, Formal uniqueness and
  fail-closed checks remain the acceptance boundary.
- Rollback is a code/config rollback to the prior worker image and
  configuration. Because this development change adds no migration, there is
  no schema rollback step. Existing append-only run/checkpoint/receipt rows are
  retained for audit; a rollback must not delete them.

## Compatibility and deployment prerequisites

The new environment variables are optional because `LiveRuntimeConfig` has the
V2 defaults:

- `TOPICPILOT_LIVE_TWSE_INGESTION_START=15:37`
- `TOPICPILOT_LIVE_TPEX_INGESTION_START=15:42`
- `TOPICPILOT_LIVE_TPEX_RETRY_START=15:52`
- `TOPICPILOT_LIVE_SOFT_TARGET=16:07`
- `TOPICPILOT_LIVE_HARD_DEADLINE=17:00`
- `TOPICPILOT_LIVE_LATE_DATA_TARGET=18:33`
- `TOPICPILOT_LIVE_LATE_DATA_HARD_DEADLINE=20:10`

Production remains unchanged in this task. Owner authorization is still
required for canonical reconciliation, deployment and any future migration or
authority change.

# TWO scheduler liveness root cause

## Root cause

The 2026-10-07 natural worker path invoked `DailyForwardRunner` in `SCHEDULED` mode but called `PostCloseUpdater.run_once` without terminal recovery permission. Once the deterministic current-day run had an incomplete terminal state, the scheduler could observe the same run without reopening its pending checkpoints. The provider-date mismatch then remained a permanent wait/failure loop from the scheduler's perspective.

A second boundary issue converted the 15:00 operational deadline into a terminal receipt status. That prevented a still-retryable same-day wait from remaining eligible for the next scheduler cadence.

## Repair

- `DailyForwardRunner` passes `allow_terminal_recovery=True` only for `execution_mode="SCHEDULED"`.
- `PostCloseUpdater` therefore resumes the same current-day run identity and reuses completed checkpoints; it does not create a historical replay.
- `_receipt_status` remains `WAITING_FOR_DATA` when data is not ready after the hard deadline. The hard deadline remains an alert boundary through the existing critical operational event.

## Non-goals and safety boundaries

- No replay of 2026-10-05 or 2026-10-06.
- No synthetic prices, manual formal snapshots, or fabricated publication receipts.
- No hard-coded current catalog/universe size.
- No change to manual recovery authorization or historical replay policy.

## Verification target

After release, the natural worker must produce a fresh readback for 2026-10-07 showing the same deterministic run identity, a fresh official TPEx target-date response, protected expected-scope coverage, formal snapshot publication, and downstream readiness. Until then, the repair is code-verified but the business outcome remains unpublished.

## Final production readback

Release `646deea23ebfd7afb415201d0f9b2f11ab6fd099` restarted the Worker and the
natural scheduler continued the same `e3892200-f46d-5029-854b-77f05cd5dd29`
session. The final run completed at 16:59:35 Asia/Taipei. After the 6173
corporate-action authority was available, the run reached `DATA_READY`,
`DailyMarketReconciliation=READY`, and covered all 553 instruments without a
historical replay. The receipt remained `FAILED_CLOSED` only because Formal
Strength and Formal Lifecycle lacked publishable formal observations; no fake
receipt or manual formal insertion was used.


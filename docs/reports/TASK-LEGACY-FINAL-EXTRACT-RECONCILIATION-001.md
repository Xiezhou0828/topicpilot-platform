# Legacy final extract reconciliation

## Disposition

The archive at `E:\\topicpilot-archive\\legacy-final-extract-20260926` is a
historical extraction, not a runtime dependency or a second source of truth.
No legacy EOD script or patch is imported wholesale into the platform.

## EOD publication comparison

The archived `ws4_bounded_eod_catchup.py` and
`ws4_formal_eod_publication.py` are pinned to the August 2026 A7/WS4 recovery
window, historical report paths, and a local-only publication adapter. Their
responsibilities are already represented by the current
`services/api/src/topicpilot_api/live/post_close.py` flow:

- official market facts and input readiness;
- formal Topic Snapshot processing;
- Lifecycle and Home publication boundaries;
- formal publication readback and completion checkpoints.

The old files remain useful only as historical design evidence for edge cases
such as lineage, idempotency, and readback. They are not safe production
inputs because their dates, report paths, and candidate assumptions are fixed
to the old recovery task.

## Topic Snapshot consumer

The useful frontend boundary from the archive has been reimplemented against
the current contract in `apps/web/app/lib/formal-topic-snapshot.ts`:

- consumes `/api/v2/topic-catalog/{slug}/snapshot`;
- uses the current nested `source` and `publication` envelope;
- requires `FORMAL`, `PUBLISHED`, `PIT_FORMAL`, `FINAL`, identity, and lineage;
- returns an explicit unavailable/error state instead of filling values in the
  browser;
- is used by the current Topic API when projecting catalog snapshot fields.

## Opportunity boundary

The archived formal Opportunity prototype is intentionally not migrated. The
current product contract keeps Opportunity downstream and shadow/deferred
until the required upstream authority and policy approvals are complete.

## Archive retirement

After this reconciliation and the corresponding GitHub change are preserved,
the legacy extraction can be deleted locally. It is not required for runtime,
database maintenance, or future workbook operations.

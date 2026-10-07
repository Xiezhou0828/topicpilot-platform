# TASK-TWO-EOD-PROVIDER-RECOVERY-SCHEDULER-REPAIR-AND-NATURAL-PUBLICATION-20261007

## Terminal status

- Scope: current-session TPEx provider recovery and natural post-close publication on 2026-10-07 (Asia/Taipei).
- Historical replay: **not performed**. The failed 2026-10-05 and 2026-10-06 runs remain historical evidence only.
- Runtime baseline at investigation: production worker/API health reported `af3c26543ce1da9b4b2988a19b01026cfd1b7c97`; production migration was `0049_task_daily_formal_publication_receipt`.
- Current code result: **repair implemented and locally verified; release/publication gate remains explicit until the repaired commit is released and a fresh natural run is observed**.

## Provider decision

Decision: `SWITCH_PRIMARY_TO_EXISTING_OFFICIAL_PROVIDER`.

The formal TPEx primary now uses the existing `TpexOfficialDailyProvider` and its date-addressable `dailyQuotes` endpoint (`tpex-official-daily.v2`). The latest-snapshot OpenAPI adapter remains available for bounded diagnostics only and is not selected for formal post-close ingestion.

Read-only source probes at 2026-10-07 15:53 Asia/Taipei established the reason:

- The OpenAPI endpoint returned HTTP 200 but every row was dated 2026-10-06 (`Date=1151006`), with zero rows for 2026-10-07. Payload SHA-256: `38cc9feff84511ec122547c981e6c6f5dd730d1f183c916e3f770b5590cbd61f`.
- The existing date-addressable `dailyQuotes?date=2026/10/07&response=json` endpoint returned HTTP 200, `stat=ok`, date `20261007`, and 12,245 unique main-board rows. Payload SHA-256: `3a4efef0e8f507ff4fd567ab8a9c4f7e66c729fd954d931a86e5406aaf653e0a`.
- The official endpoint's row shape already matches the production parser's OHLCV and volume contract; no schema or migration change is required.

The current catalog count observed through the API was treated as readback evidence only. It was not copied into code or used as a fixed expected universe. The provider decision also does not infer a complete formal TWO gate from the public endpoint alone: protected production readback must still prove the full expected current-day scope before publication is considered complete.

## Scheduler and publication repair

Two related runtime defects were repaired:

1. A natural `SCHEDULED` worker retry now passes `allow_terminal_recovery=True` into the same deterministic post-close run. It can resume an incomplete current-day run and reuse completed checkpoints without creating a historical replay or a second run identity.
2. A post-close receipt that is still data-unready after 15:00 remains `WAITING_FOR_DATA`, so the scheduler can continue its configured cadence. The hard deadline still emits an operational alert event; it is no longer a permanent publication terminal state.

The repair is intentionally limited to the natural current-day scheduled path. Manual recovery semantics and historical replay boundaries remain unchanged.

## Production readback before repair

The natural 2026-10-07 run was `e3892200-f46d-5029-854b-77f05cd5dd29`. It started at 13:48:18 and ended at 14:20:56 Asia/Taipei with 347 successes and 206 failures. Its receipt was `WAITING_FOR_DATA`, with TPE complete and TWO unavailable because the selected OpenAPI source had not published the requested date. No formal snapshots or formal publication identifiers existed, so no publication claim was made.

The TPEx tracking readback contained 207 TWO rows, while the formal receipt expected 206. The public date-addressable endpoint matched 205 of those tracking codes; `5371` and `6173` were stale/unknown tracking entries absent from the official daily table. This is diagnostic evidence only; the protected lifecycle/universe readback remains authoritative for the final expected scope.

The receipt also exposed an API runtime marker different from the API health SHA (`6fff533168b1823052071f6d88d1f266397d327d` versus `af3c26543ce1da9b4b2988a19b01026cfd1b7c97`). This is recorded as a stale or externally managed API environment marker, not as the TPEx root cause. Provenance must be re-read after release before declaring the run clean.

## Verification

The following bounded suite passed with the bundled runtime:

`68 passed, 1 skipped`

Covered tests include TPEx adapter selection and parsing, deployment preflight, natural scheduled forwarding, post-close receipt semantics, and provider preflight. The skipped test requires `TEST_DATABASE_URL` or `DATABASE_URL` and was not converted into a fabricated result.

## Release and natural-publication gate

The repaired code must be released as one immutable commit to both API and worker. After release, observe the next natural scheduler attempt and verify, in order:

1. runtime health SHA and API/worker provenance agree;
2. the run stays on the current 2026-10-07 deterministic run identity;
3. the official TPEx date-addressable response is fresh for the target date;
4. provider coverage and formal snapshot readback pass the protected expected-scope gate;
5. the receipt contains formal publication identifiers and downstream readiness.

Until all five checks pass, the terminal state is `FIX_IMPLEMENTED_NOT_YET_NATURALLY_PUBLISHED`, not `SUCCESS`.


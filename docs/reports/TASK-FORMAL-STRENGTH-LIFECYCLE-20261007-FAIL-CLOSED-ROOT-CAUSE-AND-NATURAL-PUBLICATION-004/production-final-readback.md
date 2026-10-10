# Production final readback

Readback time: 2026-10-07, Asia/Taipei.

## Runtime and receipt

- API `/healthz`: `646deea23ebfd7afb415201d0f9b2f11ab6fd099`.
- API `/readyz`: ready, same actual runtime SHA.
- Worker provenance: `646deea23ebfd7afb415201d0f9b2f11ab6fd099`.
- Exact API/Worker SHA match: YES.
- Stale external API marker in the receipt: `6fff533168b1823052071f6d88d1f266397d327d`; classified as stale metadata, not actual runtime health.
- Migration head: `0049_task_daily_formal_publication_receipt`.
- Natural run: `e3892200-f46d-5029-854b-77f05cd5dd29`.
- Receipt revision: 4; status `FAILED_CLOSED`; publicationAt `null`.

## Current-day outcome

- Daily Market: `READY`; 553 expected, 553 covered, 552 priced, one legitimate unavailable instrument.
- TPE: 347/347 complete.
- TWO: 206/206 covered, 205 priced, 6173 legitimately unavailable.
- Formal Topic: `PASS` under its row-presence readback, 45 exact-date published snapshots.
- Formal Strength: `FAIL_CLOSED`, 107 evaluated, zero published.
- Formal Grade: `NOT_PUBLISHED`, zero published.
- Formal Lifecycle: `FAIL_CLOSED`, 107 evaluated, zero published.
- Formal D0: `NOT_YET_ESTABLISHED`.

The exact-date snapshot counts for 2026-10-05 and 2026-10-06 are zero in the public Formal snapshot readback. They were not replayed, repaired, rewritten, or used as synthetic history.

## 6173

6173 is a formal member in MLCC and 其他被動元件. Its official TWO status is `SUSPENDED` from 2026-10-07 through 2026-10-16 for `CAPITAL_REDUCTION_TRADING_SUSPENSION`, with resume date 2026-10-19 and `expectedClose=false`. The last valid close is 303 on 2026-10-02. No 2026-10-07 close was invented. Before the local fix, the formal reader did not consume this file-backed authority; the fix now projects it as dimension-scoped accounted unavailability.

## Release boundary

The fixed local SHA was not pushed because repeated GitHub push attempts returned HTTP 500. Therefore this is a genuine Production readback of the pre-fix release, not a claim that the local fix has reached Production.

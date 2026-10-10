# TWO provider authority and readiness decision

## Decision

`SWITCH_PRIMARY_TO_EXISTING_OFFICIAL_PROVIDER`

Use `TpexOfficialDailyProvider` (`tpex-official-daily.v2`) as the normal TPEx formal provider. It calls the existing date-addressable official daily endpoint with the requested trading date. Keep `TpexOpenApiDailyProvider` (`tpex-official-openapi-daily.v1`) only as a diagnostic adapter; do not use it as a fallback after a formal provider failure.

## Evidence

At 15:53 Asia/Taipei on 2026-10-07:

| Surface | HTTP | Target-date result | Readiness conclusion |
|---|---:|---|---|
| TPEx OpenAPI latest snapshot | 200 | 12,194 unique rows, all dated 2026-10-06 | Not target-date ready |
| TPEx official `dailyQuotes` with `date=2026/10/07` | 200 | `stat=ok`, `date=20261007`, 12,245 unique main rows | Target-date source ready |

The date-addressable response contains the fields already consumed by the official parser for code, close, OHLC, and trading shares. No new parser or database migration is needed.

The source probe was read-only and retained only as evidence: OpenAPI SHA-256 `38cc9feff84511ec122547c981e6c6f5dd730d1f183c916e3f770b5590cbd61f`; date-addressable SHA-256 `3a4efef0e8f507ff4fd567ab8a9c4f7e66c729fd954d931a86e5406aaf653e0a`.

## Gate boundary

The public endpoint proves source freshness, not formal publication completeness. The protected lifecycle/universe readback must still determine the expected target scope, reject stale tracking rows, and prove formal snapshot coverage. No static universe count is embedded in the implementation.

## Final production outcome

The official corporate-action authority for 6173 was added without changing
authority semantics or introducing a fallback provider. The natural retry then
resolved the only missing TWO row as `SUSPENDED` with
`CAPITAL_REDUCTION_TRADING_SUSPENSION`; it did not create a price and did not
forward-fill 2026-10-07. Final coverage was 206/206 covered (205 priced plus
one legitimate unavailable), while formal downstream publication remained
blocked later by the existing Formal Strength/Lifecycle input gates.


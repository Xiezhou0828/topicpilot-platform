# G3 Market Semantics Check

`topicpilot-market-semantics-check` is the read-only G3 gate after G2 has
passed. It validates the authorized run date against the active reference
calendar, derives the date-effective expected `EQUITY` universe from the
reference lifecycle rows, and checks the canonical official market-batch
payloads.

Run it only after the already-approved G0/G1/G2 checkpoints are preserved:

```console
topicpilot-market-semantics-check \
  --run-date 2026-08-13 \
  --reference-version tw-reference-v1-rollover-daf19e9eb051255c
```

The command is SELECT-only for the database and performs read-only official
provider requests. Its declared production write set is always `[]`. It does
not invoke `topicpilot-live`, persist daily observations, activate a registry,
write snapshots, run Opportunity/Lifecycle persistence, enable a Scheduler, or
start a Canary.

## Pass/fail contract

G3 passes only when all of the following hold for both `TPE` and `TWO`:

- provider authority/version is `TWSE_OFFICIAL_DAILY /
  twse-official-daily.v2` and `TPEX_OFFICIAL_DAILY /
  tpex-official-daily.v2` respectively;
- provider `dataDate` equals the authorized run date;
- every date-effective expected `EQUITY` identity is present;
- lifecycle data is valid and does not produce duplicate expected identities;
- the provider market mapping is correct; and
- no fallback provider is used.

Delisted or otherwise lifecycle-ineligible physical identities remain in the
database but are excluded from that date's expected universe. For the approved
regression, `TPE:6806` is eligible on `2026-06-22` and not eligible on
`2026-06-23` or `2026-08-13`; its physical identity is never deleted.

Provider securities outside the expected `EQUITY` universe (for example ETFs,
warrants, or other exchange products) are retained as diagnostic
`outOfScopeProviderIdentityCount` values and do not fail G3 when expected
coverage is complete.

The output is deterministic JSON with `status=PASS|FAIL`, per-market expected
and semantically covered counts, missing identities, invalid lifecycle
identities, out-of-scope counts, `failureReasons`, `fallbackUsed`, and
`productionWriteSet`.

On `FAIL`, preserve the raw JSON and stop. Do not substitute a date, use a
fallback, run `topicpilot-live`, or proceed to Canary/Scheduler.

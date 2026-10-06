# G2 Official Provider Read-Only Preflight

## Purpose and authority

This document is the canonical operational authority for the TASK-DATA-REF-006A
G2 gate. G2 means official provider/data readiness only. It is upstream of
daily persistence, reconciliation, Topic Snapshot, Lifecycle, Opportunity,
Canary, and Scheduler activation.

The authoritative providers are fixed by the provider registry:

- TPE: TWSE_OFFICIAL_DAILY, adapter twse-official-daily.v2
- TWO: TPEX_OFFICIAL_DAILY, adapter tpex-official-openapi-daily.v1
- marketBatch: true
- Yahoo daily: VERIFICATION_ONLY
- Taishin: INTRADAY_ONLY

No verification or fallback provider can turn an official-provider failure
into G2 PASS.

## Operator command

Run this command in the same authenticated protected Production runtime used
for the runtime SHA and provider-lineage evidence:

    topicpilot-provider-preflight \
      --run-date YYYY-MM-DD \
      --reference-version tw-reference-v1

The target date is required. The command never derives a target date from the
browser, local system date, or a hardcoded trading date. It validates the
explicit date against the active tw-reference-v1 reference/session/calendar
context. A weekend, HOLIDAY, or SUSPENDED date fails closed.

The command is read-only. It uses the application DATABASE_URL only for
SELECT-only reference, calendar, market, and active EQUITY identity context.
It does not call the live collector, PostCloseUpdater, historical ingestion,
tracking repository, Topic Snapshot engine, Lifecycle engine, Opportunity
engine, or Scheduler.

## Read-only boundary

    readOnly = true
    productionWriteSet = []
    nonReferenceWriteSet = []
    fallbackAllowed = false

The following are prohibited and are not touched:

- raw_market_observations
- observation_timeline_batches
- observation_timeline_entries
- observation_timeline_quality_events
- canonical_observations and canonical detail tables
- live_collector_runs
- live_collector_attempts
- live_tracking_universe
- topic snapshots
- Lifecycle results
- Opportunity state
- reference tables
- markets and instruments
- Scheduler state or configuration

A SQLAlchemy session may open a read transaction for SELECT statements. The
preflight does not call add, flush, commit, update, delete, or migration
operations. Closing the session rolls back only the database driver's
read-transaction state; there is no application mutation.

## Evaluation sequence

1. Load the requested reference version through the existing
   topicpilot-reference-check evaluator.
2. Require referenceLoadStatus=READY, one active registry, complete
   currency/timezone/session/calendar/status/adjustment context, active TPE/TWO
   markets, and no missing or duplicate formal identities.
3. Validate the explicit target date against TW_MARKET. Weekends and persisted
   HOLIDAY/SUSPENDED dates fail before an exchange request.
4. Build the existing historical provider registry for exactly one date with
   marketBatch=true.
5. Require exactly one non-verification registration per market and require
   the expected official source code and adapter version.
6. Call each official market-level endpoint once through the adapter's
   validated market-batch capability. No instrument/month fallback is used.
7. Build the date-effective expected universe through the shared
   build_date_effective_instrument_universe contract. It applies instrument
   and market validity windows plus reference-versioned lifecycle evidence to
   the explicit run date. The formal reference identity count remains 507;
   the G2 expected universe is date-effective and is therefore allowed to be
   smaller without deleting a historical physical identity.
8. Require a parsed payload, target-date match, non-empty market data, and
   complete coverage of that date-effective expected universe. The identity
   count is derived at runtime; 507, 314, 313, and 193 are not loader business
   rules. An explicit exchange finality/no-revision promise is not a required
   G2 input; later source correction remains covered by the immutable
   correction/supersession path.
9. Return one deterministic JSON result. The top-level `status` remains
   `PASS | WAIT | FAIL` for compatibility, while `readinessState` is the
   canonical `READY | WAIT | BLOCKED` decision. Exit code 0 means PASS or WAIT;
   exit code 1 means FAIL/BLOCKED.

## Result contract

The command emits one JSON object with this shape:

    {
      "gate": "G2",
      "status": "PASS | WAIT | FAIL",
      "readinessState": "READY | WAIT | BLOCKED",
      "referenceVersion": "tw-reference-v1",
      "targetDate": "YYYY-MM-DD",
      "targetDateIsSession": true,
      "targetDateReason": null,
      "eligibilityError": null,
      "readOnly": true,
      "productionWriteSet": [],
      "nonReferenceWriteSet": [],
      "fallbackAllowed": false,
      "reference": {
        "referenceVersion": "...",
        "referenceActive": "YES | NO",
        "referenceLoadStatus": "READY | NOT_READY",
        "marketCount": 2,
        "instrumentCount": "...",
        "missingMarkets": [],
        "missingInstruments": [],
        "duplicateIdentities": [],
        "missingReferenceContexts": [],
        "calendarDateCount": "..."
      },
      "markets": [
        {
          "marketCode": "TPE",
          "providerAuthority": "TWSE_OFFICIAL_DAILY",
          "providerVersion": "twse-official-daily.v2",
          "expectedAdapterVersion": "twse-official-daily.v2",
          "reachable": true,
          "payloadParsed": true,
          "targetDateMatched": true,
          "dataAvailable": true,
          "recordCount": "...",
          "expectedInstrumentCount": "...",
          "coveredInstrumentCount": "...",
          "missingInstrumentCount": 0,
          "missingIdentityCodes": [],
          "extraIdentityCodes": [],
          "extraInstrumentCount": 0,
          "coverageComplete": true,
          "status": "PASS",
          "readinessState": "READY",
          "readinessReasonCode": "OPERATIONAL_EOD_READY",
          "errorCode": null
        }
      ]
    }

The TWO entry uses TPEX_OFFICIAL_DAILY and
tpex-official-openapi-daily.v1, backed by the official TPEx OpenAPI daily
close-quotes endpoint. The date-addressable TPEx dailyQuotes path remains an
official comparator/history authority where its contract is required; it does
not silently replace the formal market-batch registration. Error
messages are not emitted into the contract; errorCode is sanitized and no
DATABASE_URL, credentials, headers, cookies, tokens, or secret query
parameters are printed.

## Operational readiness semantics

The minimum sufficient EOD contract is `OPERATIONAL_EOD_READINESS`; an
exchange-level guarantee that the response can never be revised is not
required for the normal publication attempt. The state is evaluated only from
official evidence and the explicit target session:

- `READY`: official source, requested session, valid payload, required rows and
  OHLCV, minimum coverage, and no material authority conflict.
- `WAIT`: `EXCHANGE_NOT_READY`, an empty publication payload, a bounded
  temporary retrieval failure, or a response serving the previous valid
  session while the target session is in publication lag. No formal write is
  performed while waiting, and the existing scheduler cadence may retry.
- `BLOCKED`: an unexplained, future, or nonsensical date mismatch; malformed
  required data; insufficient required coverage; authority conflict; or
  unresolved Corporate Action comparator authority. The path stops
  fail-closed.

`previous_traded_close` and `daily_comparison_reference` remain distinct
Corporate Action Price Authority v1 concepts. Neither may be synthesized,
inferred from price movement, or replaced by an unofficial source. Missing
facts remain null/unavailable. G2 readiness also does not authorize historical
recovery, Lifecycle replay, historical Home republish, scheduler mutation, or
Production writes.

## Comparator and dimension scope

G2 keeps source, target-date, formal-universe, and payload integrity gates
global. A valid current official close with a missing exact-prior formal close
is not automatically a market failure, however. The comparator resolver may
return `ACCOUNTED_UNAVAILABLE` only when one official corporate-action
authority record:

- covers the exact prior formal session;
- names the requested target date as its resume date;
- ends before that resume date and does not expect a close; and
- maps to a supported corporate-action comparator type.

This decision carries the official source/reference and the action interval;
it never creates a close, carries a prior close forward, or changes trading
status authority. The instrument remains in formal Topic membership but is
excluded from only the affected daily-comparator, daily-return, and
relative-return calculation projection. Benchmark facts remain independently
authoritative. An invalid, unknown, provider, date, lineage, or unsupported
authority condition remains `ERROR`/fail-closed at its smallest justified
scope.

The market evidence exposes `comparatorAccountedUnavailableCount`, and each
instrument decision exposes `comparatorStatus` and `dimensionEligibility` so
downstream formal snapshot/Strength readers can preserve the distinction
between READY, ACCOUNTED_UNAVAILABLE, and unresolved failure.

## PASS criteria

G2 PASS requires all of the following:

- referenceLoadStatus=READY for tw-reference-v1;
- targetDateIsSession=true;
- the TPE registration is exactly TWSE_OFFICIAL_DAILY /
  twse-official-daily.v2 with marketBatch=true;
- the TWO registration is exactly TPEX_OFFICIAL_DAILY /
  tpex-official-openapi-daily.v1 with marketBatch=true;
- both official requests are reachable and payloads parse;
- both payloads match the requested target date;
- both payloads contain data;
- all date-effective eligible EQUITY identities derived for each market are
  present, with no extra provider identities;
- fallbackAllowed=false;
- productionWriteSet=[] and nonReferenceWriteSet=[].

G2 PASS does not mean that canonical observations were persisted,
dailyMarketReconciliation is READY, downstreamReady is true, a Topic Snapshot
exists, Lifecycle ran, Opportunity activated, or a Canary ran. Those belong
to later explicitly authorized gates.

## FAIL criteria and stop rules

G2 FAIL/BLOCKED is returned for any of:

- reference context not READY;
- invalid/non-session target date;
- missing or conflicting market context;
- provider registration or adapter-version mismatch;
- official endpoint request failure;
- payload parse/validation failure;
- provider response date mismatch;
- empty market payload;
- partial identity coverage;
- extra provider identities or a missing/extra identity-set mismatch;
- malformed or unknown instrument lifecycle evidence;
- any fallback or verification provider being used.

Publication lag and temporary official unavailability are `WAIT`, not
permanent G2 failure. A `WAIT` result preserves the read-only boundary and
returns cleanly so the bounded scheduler cadence can retry. A `BLOCKED` result
must stop the downstream formal path.

On FAIL/BLOCKED, preserve the JSON evidence and stop. Do not run
topicpilot-live --mode post-close, --apply, --activate, Topic Snapshot,
Lifecycle, Opportunity, Canary, or Scheduler commands.

## G1 and G3 boundary

Before running this command, the operator must verify the runtime SHA and
provider-lineage build SHA in the same protected runtime. The SELECT-only
topicpilot-reference-check result embedded in the preflight is the G1
preservation prerequisite.

G2 does not run daily reconciliation or claim downstreamReady. G3 remains the
separate 6806/no-trade semantics gate. A G2 PASS stops for the next explicit
authorization review; it does not authorize G3, Canary #2, or Scheduler.

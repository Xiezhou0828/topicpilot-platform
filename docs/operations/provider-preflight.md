# G2 Official Provider Read-Only Preflight

## Purpose and authority

This document is the canonical operational authority for the TASK-DATA-REF-006A
G2 gate. G2 means official provider/data readiness only. It is upstream of
daily persistence, reconciliation, Topic Snapshot, Lifecycle, Opportunity,
Canary, and Scheduler activation.

The authoritative providers are fixed by the provider registry:

- TPE: TWSE_OFFICIAL_DAILY, adapter twse-official-daily.v2
- TWO: TPEX_OFFICIAL_DAILY, adapter tpex-official-daily.v2
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
7. Require a parsed payload, target-date match, non-empty market data, and
   complete coverage of the active EQUITY identity codes derived from the
   database. The identity count is derived at runtime; 507 is not a
   business-rule constant.
8. Return one deterministic JSON result. Exit code 0 means PASS; exit code 1
   means FAIL.

## Result contract

The command emits one JSON object with this shape:

    {
      "gate": "G2",
      "status": "PASS | FAIL",
      "referenceVersion": "tw-reference-v1",
      "targetDate": "YYYY-MM-DD",
      "targetDateIsSession": true,
      "targetDateReason": null,
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
          "coverageComplete": true,
          "status": "PASS",
          "errorCode": null
        }
      ]
    }

The TWO entry uses TPEX_OFFICIAL_DAILY and tpex-official-daily.v2. Error
messages are not emitted into the contract; errorCode is sanitized and no
DATABASE_URL, credentials, headers, cookies, tokens, or secret query
parameters are printed.

## PASS criteria

G2 PASS requires all of the following:

- referenceLoadStatus=READY for tw-reference-v1;
- targetDateIsSession=true;
- the TPE registration is exactly TWSE_OFFICIAL_DAILY /
  twse-official-daily.v2 with marketBatch=true;
- the TWO registration is exactly TPEX_OFFICIAL_DAILY /
  tpex-official-daily.v2 with marketBatch=true;
- both official requests are reachable and payloads parse;
- both payloads match the requested target date;
- both payloads contain data;
- all active EQUITY identities derived for each market are present;
- fallbackAllowed=false;
- productionWriteSet=[] and nonReferenceWriteSet=[].

G2 PASS does not mean that canonical observations were persisted,
dailyMarketReconciliation is READY, downstreamReady is true, a Topic Snapshot
exists, Lifecycle ran, Opportunity activated, or a Canary ran. Those belong
to later explicitly authorized gates.

## FAIL criteria and stop rules

G2 FAIL is returned for any of:

- reference context not READY;
- invalid/non-session target date;
- missing or conflicting market context;
- provider registration or adapter-version mismatch;
- official endpoint request failure;
- payload parse/validation failure;
- provider response date mismatch;
- empty market payload;
- partial identity coverage;
- any fallback or verification provider being used.

On FAIL, preserve the JSON evidence and stop. Do not run
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

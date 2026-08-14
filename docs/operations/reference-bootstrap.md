# `tw-reference-v1` reference-only bootstrap runbook

This runbook is for the explicit `TASK-DATA-REF-001` production review. It
does not authorize Production mutation, deployment, Canary, Scheduler, G2, or
G3. The only mutating command below is the final operator-authorized
`topicpilot-reference-bootstrap --activate` invocation.

## Artifact and authority

The committed canonical bundle is:

`services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1/`

It is `GENERATED_WITH_CURATED_GOVERNANCE_INPUTS`. `manifest.json` records the
bundle hash and the SHA-256 of every source/data file. The bundle is derived
from:

- the approved UTF-8 TSV instrument source (`股票總覽.tsv`): 539 input rows,
  507 accepted identities, with no duplicate accepted composite keys;
- `twse_market_calendar.json`: 23 holiday dates and one suspended date;
- `quote_suspension_evidence.json`: TPE `6806` with `DELISTED` evidence;
- `reference_data/governance/adjustment_catalogue.json`: the explicit
  `ADJUSTED`, `UNADJUSTED`, and `UNKNOWN` governance catalogue.

The trading-status catalogue is derived from the repository's
`DAILY_TRADING_STATUS_CODES` contract and the explicit delisting evidence. The
bundle contains seven codes, including `DELISTED`; no status or adjustment is
silently inserted by the database loader.

## Offline validation

Run from the repository root with the approved source files available:

```console
python -m topicpilot_api.reference_bundle_cli validate \
  --bundle-dir services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1
```

To regenerate a bundle from source, use the separate offline command. The
output directory must be reviewed before it is promoted as the canonical
artifact:

```console
python -m topicpilot_api.reference_bundle_cli generate \
  --stock-source <approved-stock-export.tsv> \
  --calendar-source <twse-market-calendar.json> \
  --evidence-source <quote-suspension-evidence.json> \
  --output-dir services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1
```

The generator derives market and instrument totals from records. `507` is a
current artifact result, not a loader business rule.

## Production gate order

Use the protected Production runtime only after the revision, migration head,
bundle hash, and operator authorization have been independently reviewed.
Neither command prints `DATABASE_URL` or any secret.

1. Validate the committed bundle offline.
2. Run the SELECT-only market-context precheck documented in
   `docs/operations/market-calendar-remediation.md`. If an expected market has
   `calendar_code=NULL`, stop the bootstrap flow and complete the separately
   reviewed calendar-remediation dry-run/apply/postcheck sequence first.
3. Run the no-mutation bootstrap precheck:

   ```console
   topicpilot-reference-bootstrap \
     --bundle-dir services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1 \
     --dry-run
   ```

   The result must show `dryRun=true`, `transactional=true`, the expected
   reference-only write set, and `nonReferenceWriteSet=[]`. Dry-run validates
   existing market code, name, exchange code, timezone, and calendar code with
   the same shared validator used by activation; a mismatch is a STOP condition.

4. After one-shot authorization, run the atomic bootstrap and activation:

   ```console
   topicpilot-reference-bootstrap \
     --bundle-dir services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1 \
     --activate
   ```

5. Run the existing SELECT-only postcheck:

   ```console
   topicpilot-reference-check --reference-version tw-reference-v1
   ```

   It must return `REFERENCE_LOAD_STATUS=READY`, active TPE/TWO, no missing
   or duplicate identities, complete context, and a persisted calendar date
   count of 24. The current bundle-derived identity result is TPE 314, TWO
   193, total 507; these values are checked against the bundle/data, not
   hard-coded into the loader.

## Write and transaction contract

The only permitted write set is:

- `markets`, `instruments`;
- `reference_registry_sets`;
- `reference_currencies`, `reference_timezones`, `reference_sessions`;
- `reference_trading_statuses`, `reference_adjustments`;
- `reference_calendar_dates`.

`topics`, `topic_hierarchy`, `instrument_topic_relations`, raw/timeline/
canonical observations, Lifecycle, Opportunity, and audit tables are outside
the loader and must remain untouched. The loader has no FastAPI endpoint.

One `--activate` invocation owns one SQLAlchemy transaction. It validates the
bundle, reconciles all rows, verifies the final identity/catalogue/calendar
state, retires any previous ACTIVE registry set, and only then changes the
new set to `ACTIVE`. The partial unique index permits at most one ACTIVE set.
Any exception rolls back the registry, identity, context, calendar, and
activation changes together; a partial set must never become ACTIVE.

Rerunning the same bundle hash/version against a complete ACTIVE set returns
`operation=NOOP` and performs no writes. A version collision with a different
bundle hash, duplicate identity, missing catalogue, conflicting existing row,
or failed post-write validation is a STOP condition.

## STOP and rollback criteria

Stop immediately and do not proceed to Canary/G2/G3 when:

- any source or bundle SHA-256 differs from the reviewed manifest;
- any market/instrument is missing, duplicated, unsupported, or conflicts with
  existing identity state;
- the calendar, status, adjustment, currency, timezone, or session catalogue
  is incomplete or not explicitly present in the bundle;
- active-version uniqueness fails;
- the dry-run names any non-reference table;
- the bootstrap exits non-zero or the postcheck is not `READY`;
- 6806 is absent from the bundle evidence or is converted into a fake price.

Do not manually delete, truncate, repair, or rerun a partial command. Preserve
the failed transaction output, verify the postcheck remains unchanged, and
return the task to review. This runbook does not include a production rollback
mutation; database rollback is the transaction failure behavior above, while
an already-active prior registry remains the operator's protected rollback
target.

## Date-effective lifecycle integration

The canonical bundle also contains `instrument_lifecycles.json`, generated
from the approved status-evidence input. Bootstrap writes these rows to
`reference_instrument_lifecycles` in the same atomic reference-only
transaction. Lifecycle evidence never deletes a physical instrument identity.

The G2 preflight uses the shared date-effective eligibility contract after
loading the active registry. It applies instrument/market validity windows and
the latest applicable lifecycle event for the explicit run date. For the
regression boundary, a delisting effective on 2026-06-23 is eligible on
2026-06-22 and not eligible on or after 2026-06-23. The formal G1 identity
count remains data-derived at 507; on 2026-08-13 the date-effective G2
expected universe is derived as TPE 313 and TWO 193.

## Bundle hash rollover

The ordinary bootstrap is immutable for an existing reference version: a
different non-null bundle hash is a STOP condition. When a reviewed bundle
must supersede an ACTIVE registry, use the dedicated
[reference registry transition runbook](reference-registry-transition.md).
It derives a new registry version, preserves the retired registry and its
provenance, and atomically activates the lifecycle-bearing target. Do not edit
the old row or overwrite its bundle hash.

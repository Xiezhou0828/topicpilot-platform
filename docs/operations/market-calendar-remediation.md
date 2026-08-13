# TPE/TWO market calendar context remediation runbook

This runbook defines the reviewed operator flow for a future Production task.
TASK-DATA-REF-005G implements and validates the command only; it does not
authorize Production access, remediation, bootstrap, activation, deployment,
G1/G2/G3, Canary, or Scheduler changes.

## Authority and exact scope

The validated `tw-reference-v1` bundle is the sole target authority. Its two
market records derive `calendar_code=TW_MARKET`; the remediation contains no
TPE/TWO-to-calendar hardcode. It accepts only the known compatible drift:

| Market | Required existing identity/context | Permitted change |
| --- | --- | --- |
| TPE | `TWSE Listed`, `TWSE`, `Asia/Taipei` | `NULL` to `TW_MARKET` |
| TWO | `TPEx OTC`, `TPEx`, `Asia/Taipei` | `NULL` to `TW_MARKET` |

The exact write set is `markets.calendar_code`. Market primary keys, internal
codes, names, exchange codes, timezones, instruments, reference tables, topics,
observations, provider state, and Scheduler state are outside the write set.
Any unexpected market, inactive market, incompatible instrument identity or
metadata, non-empty reference registry, or conflicting non-null calendar fails
closed.

## Future reviewed operator sequence

All commands must run in the same exact-SHA protected runtime. Do not print or
paste `DATABASE_URL` or other secrets.

1. Verify runtime SHA and provider lineage, then run the existing SELECT-only
   database diagnostic approved by the execution task. It must prove exactly
   TPE/TWO, canonical identity metadata, `Asia/Taipei`, `calendar_code=NULL`,
   507 bundle-compatible instrument rows, and zero reference registry sets.
2. Run the zero-mutation plan:

   ```console
   topicpilot-market-calendar-remediation \
     --bundle-dir /app/src/topicpilot_api/reference_data/bundles/tw-reference-v1 \
     --dry-run
   ```

   Require `operation=PLAN`, `status=VALIDATED`, `dryRun=true`,
   `semanticCompatibility=BUNDLE_COMPATIBLE_NULL_CALENDAR`, changes only from
   NULL to bundle-derived `TW_MARKET`, `writeSet=["markets.calendar_code"]`,
   empty non-calendar/instrument write sets, and preservation flags true.
3. Only after separate one-shot authorization, run:

   ```console
   topicpilot-market-calendar-remediation \
     --bundle-dir /app/src/topicpilot_api/reference_data/bundles/tw-reference-v1 \
     --apply
   ```

4. Immediately repeat the SELECT-only market/instrument fingerprint diagnostic.
   Require both calendars `TW_MARKET`, unchanged market IDs/codes/identity fields,
   and unchanged instrument count, assignments, and fingerprint.
5. Repeat the remediation with `--dry-run`; require `operation=NOOP` and
   `status=CANONICAL`.
6. Run reference bootstrap `--dry-run`. Only a `PLAN`/`VALIDATED` result with
   the reviewed reference-only write set may proceed to a separately authorized
   bootstrap/activation task.

## Transaction, rollback, and STOP rules

`--apply` requires a fresh session and owns one transaction. It validates the
bundle, complete market topology, exact non-calendar context, all bundle-derived
instrument identities/metadata, and empty registry state before assignment. It
then updates only `calendar_code`, flushes, and repeats the checks plus full
instrument and immutable-market snapshots before commit. Any exception rolls
back both calendar updates. An already canonical state is an idempotent NOOP.

STOP without manual SQL or retry if any value differs, a non-null calendar is
not the bundle target, the command returns `BLOCKED`, preservation evidence
changes, bootstrap dry-run blocks, or any non-calendar write is reported.
Preserve the evidence and return to review. Never use this command as a generic
market repair or combine it with identity remediation.

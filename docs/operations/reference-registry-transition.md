# Reference registry version transition runbook

This runbook defines the only supported rollover path when an existing
reference version is ACTIVE but a reviewed canonical bundle has a different
SHA-256. It is the TASK-DATA-REF-006G contract. It does not authorize a
Production run by itself.

## Why this path exists

`reference_data_version` is immutable. The ordinary
`topicpilot-reference-bootstrap` command is intentionally fail-closed when
the requested version already exists with a different non-null bundle hash.
It must not overwrite the old registry or its provenance.

The transition command therefore creates a new registry version derived from
the source version and the full new bundle digest:

```text
<source-version>-rollover-<first-16-lowercase-hex-digest>
```

For the reviewed 006G bundle:

```text
source version = tw-reference-v1
source bundle SHA-256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
new bundle SHA-256 = daf19e9eb051255c631d0fff6d8fecf1273aecf52f9e958a62c778dfb6906295
target version = tw-reference-v1-rollover-daf19e9eb051255c
```

The complete digest remains in both the target registry and the transition
provenance row. A target-version prefix collision with a different full digest
is a STOP condition; the command never overwrites a registry row.

## Exact entrypoint

The entrypoint is deliberately distinct from the ordinary bootstrap and the
read-only reference check:

```console
topicpilot-reference-transition \
  --from-reference-version tw-reference-v1 \
  --expected-from-bundle-sha256 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6 \
  --bundle-dir /app/src/topicpilot_api/reference_data/bundles/tw-reference-v1 \
  --dry-run
```

The command validates the source registry, exact source hash, canonical bundle,
market/instrument identity compatibility, all reference catalogues, calendar,
and lifecycle evidence. It does not write during `--dry-run`.

Only after a separately recorded one-shot authorization may the operator use:

```console
topicpilot-reference-transition \
  --from-reference-version tw-reference-v1 \
  --expected-from-bundle-sha256 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6 \
  --bundle-dir /app/src/topicpilot_api/reference_data/bundles/tw-reference-v1 \
  --activate
```

The command output must contain the derived target version, the reviewed new
bundle digest, `transactional=true`, `singleActiveRegistry=true`,
`sameVersionHashOverwrite=false`, and `nonReferenceWriteSet=[]`.

## Atomic transition contract

One activation owns one SQLAlchemy transaction. Within that transaction it:

1. locks and revalidates the ACTIVE source registry and expected old hash;
2. creates or reconciles the derived target registry and every reference-only
   context row, including `reference_instrument_lifecycles`;
3. validates the complete target identity/catalogue/calendar/lifecycle state;
4. retires the prior ACTIVE registry and flushes that retirement;
5. promotes the validated target to ACTIVE;
6. appends one `reference_registry_transitions` provenance row linking both
   registry IDs, versions, and full bundle hashes.

The existing partial unique ACTIVE index guarantees one ACTIVE registry. Any
exception rolls back the new registry, all target rows, retirement, activation,
and transition provenance together. The old registry and all of its rows remain
available as the protected historical record. There is no manual SQL rollback,
delete, truncate, or bundle-hash edit path.

The only permitted transition write set is:

- `markets`, `instruments`;
- `reference_registry_sets`;
- `reference_registry_transitions`;
- `reference_currencies`, `reference_timezones`, `reference_sessions`;
- `reference_trading_statuses`, `reference_adjustments`;
- `reference_calendar_dates`;
- `reference_instrument_lifecycles`.

The non-reference write set is empty. Topics, relations, raw/timeline/
canonical observations, Lifecycle, Opportunity, audit tables, and Scheduler
state are outside this path.

## Idempotence and STOP rules

Rerunning the exact transition after successful activation returns `operation=NOOP`
after validating the target rows and transition provenance. It does not retire
or write anything again.

Stop immediately if:

- the source version is absent, duplicated, not ACTIVE, or has a different
  bundle hash than `--expected-from-bundle-sha256`;
- the bundle source version does not match `--from-reference-version`;
- the target derived version exists with another full bundle hash;
- target transition provenance already exists in an incompatible state;
- any identity, market context, catalogue, calendar, or lifecycle row conflicts;
- the target cannot produce the date-effective 2026-08-13 universe TPE 313 / TWO
  193 with 6806 physically retained and not eligible;
- any output names a non-reference table;
- any exception occurs before the transaction commits.

Do not substitute a date, lower G2 coverage, delete 6806, overwrite the old
hash, activate the old version again, or proceed to G2/G3/Canary/Scheduler
after a failed transition.

## Post-transition read-only checks

The active target version must be passed explicitly until a separately reviewed
runtime configuration release changes the default reference version:

```console
topicpilot-reference-check \
  --reference-version tw-reference-v1-rollover-daf19e9eb051255c

topicpilot-provider-preflight \
  --run-date 2026-08-13 \
  --reference-version tw-reference-v1-rollover-daf19e9eb051255c
```

The reference check must report ACTIVE/READY, 2 markets, 507 physical/formal
identities, complete contexts, no missing or duplicate identities, and 24
calendar dates. The G2 preflight must use the unchanged official authorities:
TPE `TWSE_OFFICIAL_DAILY` / `twse-official-daily.v2`, TWO
`TPEX_OFFICIAL_DAILY` / `tpex-official-daily.v2`, market-batch true, no fallback,
and 313 / 193 date-effective coverage for 2026-08-13.

This task does not execute these Production commands. It establishes the
contract and disposable-PostgreSQL evidence only.

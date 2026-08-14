# TPE/TWO market identity remediation runbook

This runbook defines the local/disposable validation and the future reviewed
Production boundary for TASK-DATA-REF-005B through TASK-DATA-REF-005D. It
does not authorize a Production mutation. TASK-DATA-REF-005D corrects the
existing-instrument safety contract after the Production dry-run proved that
the reference check and remediation command had used different instrument
metrics.

## Canonical identity decision

The approved `tw-reference-v1` bundle at release SHA
`a5fba9319a177a5da9fb8123b265ed05e7ff9f6c` is the canonical metadata
authority:

| Internal code | Canonical name | Canonical exchange code |
| --- | --- | --- |
| `TPE` | `TWSE Listed` | `TWSE` |
| `TWO` | `TPEx OTC` | `TPEx` |

`market.code` is the stable TopicPilot internal identity and remains
unchanged. It is used by the instrument composite key, provider routing,
reference checks, API filters, importers, and frontend/domain projections.
`market.name` is mutable canonical/display metadata. `market.exchange_code`
is mutable exchange metadata used by identity and API contracts; its change is
governed and exact, not an alias or fuzzy normalization.

The known Production legacy state is:

| Internal code | Legacy name | Legacy exchange code |
| --- | --- | --- |
| `TPE` | `Taiwan Stock Exchange` | `TPE` |
| `TWO` | `Taipei Exchange` | `TWO` |

The values differ in both name and exchange code. They are conflict evidence,
not an authority override.

## Dedicated entrypoint

The only remediation entrypoint is:

```console
topicpilot-market-identity-remediation \
  --bundle-dir services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1 \
  --dry-run
```

The command accepts exactly one of `--dry-run` or `--apply`. It is not the
reference bootstrap command and has no generic table, SQL, delete, insert,
re-key, migration, seed, or repair mode.

The declared write set is exactly:

- `markets.name`
- `markets.exchange_code`

`market.id` and `market.code` are never assigned. The non-market write set is
empty. Instruments, security identities, topic relations, observations,
reference registry rows, Lifecycle, Opportunity, audit rows, and provider
configuration are not written.

## Fail-closed preconditions

Before planning or applying, the command validates the committed
`tw-reference-v1` bundle and requires exactly two active market rows with
codes `TPE` and `TWO`.

For the legacy-to-canonical apply path, all of the following must be true:

- TPE is exactly `Taiwan Stock Exchange` / `TPE`.
- TWO is exactly `Taipei Exchange` / `TWO`.
- Existing instruments are either empty or exactly compatible with the
  committed bundle by `(market.code, instrument_code)` identity and canonical
  `name`, `instrument_type`, and `currency` metadata.
- Every existing instrument resolves through `instruments.market_id` to one
  of the expected TPE/TWO market rows; orphan, missing, extra, duplicate, or
  reassigned identities are rejected.
- Total reference registry-set count is exactly zero.
- No third market, duplicate code, inactive expected market, mixed state, or
  unexpected field is present.

Instrument row count alone is never a safety gate, and `507` is not hardcoded
as a business rule. The expected identity set is derived from the validated
bundle. Existing inactive bundle-compatible instruments are accepted because
the formal reference bootstrap validates the same identities and activates
them; this remediation never activates or otherwise changes instruments.

Any semantic mismatch returns `BLOCKED` before the market metadata update.
The machine-readable result reports `existingInstrumentCount` for evidence
and `instrumentCompatibility` as `EMPTY` or
`CANONICAL_BUNDLE_COMPATIBLE`. A fully canonical market state returns `NOOP`,
which makes an already-remediated disposable or reviewed state idempotent. A
partially canonical/mixed state is blocked.

## Transaction and postcondition contract

`--apply` requires a fresh SQLAlchemy session and owns one transaction. It
updates the two existing rows in place, flushes, verifies that both rows have
the canonical names/exchange codes, verifies that the complete instrument row
snapshot and reference registry count did not change, and commits only after
those checks pass. Any exception rolls back both market metadata updates
together. Primary keys, market codes, foreign-key targets, instrument fields,
and non-market tables remain unchanged.

The failed-Production conflict from TASK-DATA-REF-005A is not repaired by
this command. It remains the exact precondition that the disposable tests
reproduce.

## Disposable PostgreSQL validation

Use a disposable PostgreSQL 16 instance or an explicitly isolated
`TEST_DATABASE_URL`. Never use Production `DATABASE_URL` for these tests.
After migrations, the primary Production-like fixture seeds the two legacy
market rows plus the 507 bundle-derived instruments as inactive and leaves
reference registry rows empty. This intentionally reproduces the metric
split: reference check reports 0 active canonical instruments and `NOT_READY`,
while remediation inspects all 507 existing rows. Then run:

```console
python -m pytest services/api/tests/test_market_identity_remediation_postgres.py -q
```

The required results are:

- legacy state dry-run plans two metadata changes and leaves rows unchanged;
- dry-run accepts all 507 rows only when their identity topology and canonical
  metadata match the validated bundle;
- apply changes names/exchange codes in place;
- primary keys, market codes, and every instrument row remain unchanged;
- a canonical rerun is `NOOP`;
- mixed state is `BLOCKED` with no mutation;
- missing, extra, reassigned, orphan, duplicate, or metadata-conflicting
  instruments are `BLOCKED` before market mutation;
- post-remediation `topicpilot-reference-bootstrap --dry-run` validates;
- post-remediation isolated bootstrap activation reaches 2 markets / 507
  derived instruments (`TPE=314`, `TWO=193`) /
  `REFERENCE_LOAD_STATUS=READY`.

The PostgreSQL integration test in this task must clean up its own disposable
rows and must not point at a shared or Production database.

## Future Production gate (not authorized by TASK-DATA-REF-005D)

No Production retry is authorized by this task. Only after this correction is
integrated, deployed at an exact verified SHA, and separately authorized may
an operator run the following sequence against the protected Production
runtime:

1. exact runtime SHA and G0 recheck;
2. SELECT-only market identity precheck matching the exact legacy state;
3. remediation dry-run and zero-mutation check;
4. separately authorized one-shot remediation apply;
5. immediate SELECT-only market postcheck;
6. reference bootstrap dry-run;
7. separately authorized reference bootstrap activation;
8. G1 reference postcheck.

STOP on any code, legacy name, legacy exchange code, active-state, semantic
instrument compatibility, registry, bundle, or postcondition drift. A raw
instrument count is evidence, not authorization. Never repair by manual SQL,
delete/reinsert, market re-key, legacy importer, live bootstrap, migration, or
bundle regeneration.

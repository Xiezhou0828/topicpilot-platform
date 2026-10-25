# Protected Production stock-add authority readback

## Purpose and boundary

`stock-add-authority-readback.yml` is a manually dispatched, Owner-approved,
read-only path for the live `topicpilot.instruments` and Topic catalog. It
exists because the public Render API identifies its public dataset as
synthetic, while the maintenance workbook is a timestamped review bridge and
not a live authority. This is only the first authority-readback step: it does
not add a stock, create a relation, activate a reference bundle, run a market
data job, load a research package, or generate the final `/add` approval plan.

The local `topicpilot-stock-add-plan` command continues to reject a public API
that declares synthetic data. The protected database mode is accepted only
inside this repository's manually dispatched GitHub workflow from canonical
`main`, and only when the exact dedicated read-only role, expected database
host/name, read-only transaction, repeatable-read isolation, table privileges,
migration head, and complete catalog contents are verified.

## Owner provisioning prerequisites

Before dispatching the workflow, an authorized Production database owner must
create a dedicated login named `topicpilot_catalog_readonly`. It must not be a
member of any other role, must be `NOSUPERUSER NOCREATEDB NOCREATEROLE
NOREPLICATION NOBYPASSRLS NOINHERIT`, and must receive only `CONNECT`, schema
`USAGE`, and `SELECT` on these exact tables:

```text
public.alembic_version
topicpilot.markets
topicpilot.instruments
topicpilot.topics
topicpilot.topic_hierarchy
```

The role must have no table mutation privileges, no `CREATE` privilege on the
`public` or `topicpilot` schemas, and no privileges on other relations or
sequences in those schemas, no column-level `INSERT`/`UPDATE`/`REFERENCES`
grants, and no directly granted database `CREATE` or `TEMPORARY` privilege.
PostgreSQL may expose its default `TEMPORARY` grant through `PUBLIC`; the reader
reports that effective state separately and starts every catalog read in a
`READ ONLY` transaction. Do not revoke a database-wide `PUBLIC` grant just for
this workflow. Do not reuse
`DATABASE_URL`, `MIGRATION_DATABASE_URL`, `TOPICPILOT_PRODUCTION_DATABASE_URL`,
the workbook import role, or the narrow forensic-readback role. Store the
connection URL only as the protected GitHub
Environment secret
`production-catalog-readonly / TOPICPILOT_PRODUCTION_CATALOG_READONLY_DATABASE_URL`.
Set these non-secret Environment variables:

```text
TOPICPILOT_PRODUCTION_CATALOG_READONLY_ROLE=topicpilot_catalog_readonly
TOPICPILOT_PRODUCTION_CATALOG_READONLY_EXPECTED_HOST=<exact PostgreSQL host>
TOPICPILOT_PRODUCTION_CATALOG_READONLY_EXPECTED_DATABASE=<exact database name>
```

The reader checks the URL's PostgreSQL host/database and `current_database()`
against those expected values before reading the catalog. Missing or mismatched
target identity fails closed. These expected values and the connection secret
must be provisioned from the authorized Production database configuration; do
not copy them from a local/test connection.

Create the `production-catalog-readonly` Environment with the Owner as a
required reviewer, self-review allowed for a solo creator, and an explicit custom
deployment branch allow-list containing only canonical `main`. The workflow verifies that exact setting and
also allows dispatch from `main` only. Its first job checks that this
Environment already exists and has the required safeguards without referencing
the Environment itself. Only a dependent second job references it. Therefore a
missing or misconfigured Environment fails before GitHub Actions can implicitly
create an unprotected Environment with that name.
The reviewed source SHA must be exactly the dispatch commit and an ancestor of
`origin/main`.

## Readback behavior

Dispatch the workflow from canonical `main` with a four- or six-digit stock
code, market (`TPE` or `TWO`), and the exact dispatch commit SHA. It uses one
PostgreSQL `REPEATABLE READ, READ ONLY` transaction to read the complete
TPE/TWO equity identity set, all Topics, and the effective hierarchy as of the
Taiwan date. It verifies role flags and membership, table/schema/database
privileges, active market coverage, migration head, identity fields, duplicate
keys, row counts, and stable digests.

The workflow does not print or upload catalog rows or identifiers. This
repository is public, so it deliberately avoids describing its job output as a
private artifact. The job summary keeps only the requested stock's
`MATCH_FOUND` / `NO_MATCH_CONFIRMED` result, Topic-catalog readiness/effective
date, source revision, and an aggregate readback SHA-256. The detailed report
exists only in the runner's temporary directory and is discarded at job end.

The check uses `(market, stock_code)` as the stock identity. A proven absence
is `NO_MATCH_CONFIRMED` and a normal `ADD_INSTRUMENT` starting point; a partial
or unsafe query is blocked rather than converted to absence. This step does
not expose the complete Topic list to the public job log and does not perform
business-evidence-to-Topic matching; that remains a separate reviewed stage.
Relation candidates remain separately evidence-reviewed, and relation weights
do not become structural roles.

## Gates that remain separate

- A successful readback does not authorize Production writes. A dedicated,
  audited, idempotent write workflow and its operation journal are still
  required, followed by the Owner's exact hash confirmation.
- A successful stock-master write would not add the stock to the active
  reference universe. A new immutable reference bundle must pass the existing
  G1 and date-effective G2 checks.
- G1/G2 readiness does not prove a closing quote. The official post-close run
  must cover the stock, reconcile completely, and pass downstream readback.
- The deployed scheduler is still unverified; no next-day automatic capture
  may be promised until the existing scheduler is actually provisioned and
  verified.

No Production readback workflow, role, secret, expected endpoint, data,
reference version, migration, deployment, or scheduler was provisioned or
changed by this local implementation.

# Controlled stock-master and research publication

## Purpose

After a v4 research package has passed its publication authorization, the protected writer checks
the current Production stock master again and routes the package:

- `MATCH_FOUND`: confirm that the existing instrument identity matches. Leave
  the stock-master row unchanged and publish a new immutable frontend research
  version.
- `NO_MATCH_CONFIRMED`: confirm that the instrument is still absent, then add
  the verified instrument and publish its frontend research version in one
  transaction.
- `RETRIEVAL_BLOCKED`, stale, incomplete, or ambiguous readback: stop before
  any write.

An existing stock is not a reason to reject an `add` request. It selects the
research-update path. This writer does not mutate Topic records or stock-Topic
relations, does not activate a reference-universe version, and does not change
the post-close scheduler. Those remain separately governed steps.

## Package and plan

The sealed plan uses schema `topicpilot-stock-add-master-plan.v1` and includes
the authorized frontend v4 projection, official stock identity, fresh Production
master readback, and a canonical `planSha256`. The plan is not a database
credential, but its research projection must not be placed in public workflow
inputs, issue text, logs, or artifacts. Keep it in the protected
`production-db-maintenance` Environment secret described below. The research
package must have a valid frontend contract, official instrument identity, a
traceable HTTPS source register, `blockingIssues=[]`, and
`sourceRightsStatus=APPROVED`. Packages
with `dataCompletenessScore > 0.70` use the Owner's standing policy
`RESEARCH_COMPLETENESS_GT_0_70_V1`: the plan records the strict threshold,
score, authorization time, and package-content SHA-256 in
`authorizationEvidence`. This is policy authorization, not a claim of human
review; `ownerReviewStatus` remains `PENDING`. A score of exactly 0.70 does not
qualify. Explicit `BLOCKED`/`REJECTED` states, a bad identity, invalid v4
contract, missing source lineage, or non-approved source rights still stop
publication. Existing valid Owner approval evidence remains accepted. The
writer requires the policy attestation to be present inside the hash-sealed
plan, so the authorization and content cannot change after dry-run. The API
writer derives the public field allowlist itself; it never stores the source
register, evidence IDs, policy evidence, or other private review fields in the
public projection. The audit journal records the authorization mode, policy
ID (when applicable), score, and package hash.

The master readback must be complete, Production-only, and no more than
15 minutes old. `MATCH_FOUND` and `NO_MATCH_CONFIRMED` are both valid results;
the current database identity is rechecked inside the write transaction. A
new instrument additionally requires an officially evidenced effective date.

The exact final confirmation is:

```text
APPLY STOCK ADD <MARKET> <CODE> <PLAN_SHA256>
```

Any package, identity, date, or readback change invalidates the plan hash and
requires a new dry-run and confirmation.

## Schema and runtime read path

Migrations `0051_stock_add_operation_journal` and
`0052_company_research_publications` add append-only operation history and
versioned public research projections. The API keeps the existing
`GET /api/v2/stocks/{symbol}/research-v4` contract and reads the latest
publication from the database when no explicit file read-model path is
configured. A configured file read model remains a local/legacy read adapter.

After migration, grant the deployed API database role `USAGE` on schema
`topicpilot` and `SELECT` on `topicpilot.company_research_publications` if those
permissions are not already inherited from its existing role. The writer
credential is separate and must never be used by the API process.

## Dedicated Production writer credential

Keep the ordinary importer restricted to Development and Test. Create a
dedicated login role after schema migration. It must be
`LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT`,
have no memberships, and have no schema `CREATE` privilege. Use a hidden
password prompt; never put a password in SQL history, plan JSON, logs, or this
document.

Grant only:

```sql
GRANT CONNECT ON DATABASE neondb TO topicpilot_stock_add_writer;
GRANT USAGE ON SCHEMA public, topicpilot TO topicpilot_stock_add_writer;
GRANT SELECT ON public.alembic_version, topicpilot.markets,
  topicpilot.instruments, topicpilot.stock_add_operations,
  topicpilot.stock_add_operation_events,
  topicpilot.company_research_publications TO topicpilot_stock_add_writer;
GRANT INSERT ON topicpilot.instruments, topicpilot.stock_add_operations,
  topicpilot.stock_add_operation_events,
  topicpilot.company_research_publications TO topicpilot_stock_add_writer;
```

Do not grant `UPDATE`, `DELETE`, `TRUNCATE`, `CREATE`, ownership, membership,
or access to Topics or stock-Topic relations. The writer checks the Production
host, database, current role and flags, membership, exact table/schema
privileges, and migration head before doing a dry-run or write.

In the existing protected `production-db-maintenance` GitHub Environment,
configure:

- Secret `TOPICPILOT_PRODUCTION_STOCK_ADD_DATABASE_URL` for the dedicated role.
- Secret `TOPICPILOT_PRODUCTION_STOCK_ADD_PLAN_JSON` for the current sealed,
  Owner-reviewed plan. Update it to the latest approved plan before each
  dispatch; the public workflow input accepts only the plan's lowercase
  `planSha256`, which the runner verifies against both the declared and
  recomputed canonical digest before staging it.
- Variable `TOPICPILOT_PRODUCTION_STOCK_ADD_EXPECTED_HOST` with the exact host.
- Variable `TOPICPILOT_PRODUCTION_STOCK_ADD_EXPECTED_DATABASE` as `neondb`.
- Variable `TOPICPILOT_PRODUCTION_STOCK_ADD_EXPECTED_ROLE` as
  `topicpilot_stock_add_writer`.

Retain the Owner approval rule and the `main`-only deployment branch rule.
The existing owner migration credential is used only by the protected schema
migration workflow.

## Deployment and execution order

1. Merge the reviewed implementation to canonical `main`.
2. Run **Production stock-add schema migration** from `main` with the exact
   input `APPLY STOCK ADD SCHEMA 0052`. It accepts only Production migration
   head 0050, applies through 0052, and verifies the three tables and
   append-only triggers.
3. Grant the deployed API role `SELECT` on the publication table, then deploy
   the API from the exact reviewed `main` SHA. Confirm `/readyz`, the migration
   endpoint, and the research-v4 route.
4. Provision the restricted writer role and the five GitHub Environment
   settings above.
5. Produce a fresh authority readback and prepare the publication authorization
   in the plan. Run `topicpilot-stock-add-master-plan` on the reviewed plan
   before sealing it; this embeds the standing-policy attestation for eligible
   scores and computes the canonical plan hash. Keep the sealed plan in the
   protected plan secret, then run **Production stock-add master writer** in
   `dry-run` mode using only the plan SHA-256 as a dispatch input.
6. Review the dry-run action, stock identity, research date, plan SHA, and
   publication version. Run the same plan in `apply` mode with the exact hash
   confirmation and approve the protected Environment gate.
7. Read the master, operation journal, publication version, and frontend API
   response back. Mark master/research publication complete only after all
   readbacks agree.
8. For a genuinely new stock, separately complete Topic relation review,
   reference-universe versioning, G1/G2, and post-close verification before
   claiming that daily price collection is ready.

The operation ID is deterministic from market, code, and plan hash. Repeating
the same completed plan is a no-op after verifying its journal and publication.
A different hash, stale authority, unexpected existing row, or incomplete prior
operation is rejected. Research versions and operation records are immutable.

## Current 2468 readiness

The Production API currently returns 2468's v4 research publication with
`researchAsOf=2026-10-25` and `dataCompletenessScore=0.72`. This means research
content is readable under the standing completeness policy. The Production
API also returned an accepted official 2026-10-30 close of 53.20, open 49.70,
high 55.40, low 49.60, and volume 26,677,129 (`TWSE_OFFICIAL_DAILY`; collector
run `08e77acc-8499-56c2-b734-e684320b745b`). The record's corporate-action
adjustment state is `UNKNOWN`, so previous close, change, change percent, and
turnover are intentionally not inferred. The targeted one-symbol run confirms
that this close was collected; it does not by itself prove the next scheduled
full-universe run or scheduler readiness. Keep reference-universe and
full-scheduler verification statuses separate from the accepted daily bar.

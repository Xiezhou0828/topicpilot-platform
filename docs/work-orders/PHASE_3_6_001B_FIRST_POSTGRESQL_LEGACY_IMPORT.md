# PHASE-3.6-001B — First PostgreSQL Legacy Import

**Status:** `COMPLETED / POSTGRESQL IMPORT VERIFIED`
**Generation:** `NEXT / V2`; V1 is read-only

## Objective

Run the first real, transactional V1 master-data migration for markets,
instruments, topics, hierarchy, and authoritative instrument-topic relations.
The runtime metrics in `族群資料庫.tsv` are reference-only and are excluded.

## Resolved source artifacts

The requested `/mnt/data` paths are not mounted in this Windows workspace. The
same four source artifacts were resolved under `C:\Users\acer\Desktop\題材領航\input\`:

| Artifact | SHA-256 |
|---|---|
| `股票總覽.tsv` | `25D0B40CC2D5FF58112456C4A307E28309E83C8FCAA266750C7169221031B28F` |
| `題材階層表.tsv` | `2AEEE450748695A89F7058EE44CB53B8385D5F9A2786AD0BF6B1ABC7F5FB525B` |
| `股票題材關聯.tsv` | `DFBE9AEC146939349740D257D0E06CA490445C64D597E1C340119925CB5C978A` |
| `族群資料庫.tsv` (reference-only) | `A0DEEA0902CD68080A767252710AF378B57FDB1F78DA81651DAEDCAFC526B35C` |

These files are read-only inputs; no V1 file is modified.

## Frozen mapping and controls

- `股票總覽.tsv` maps to `Market`, `Instrument`, and only approved source metadata.
- `題材階層表.tsv` maps to `Topic` and `TopicHierarchy`.
- `股票題材關聯.tsv` is the sole relation source; overview topic columns are not parsed.
- Stable instrument identity is `(TPE|TWO, instrument_code)`.
- Missing historical effective dates use migration baseline `2026-08-07` and are marked as migration-default lineage.
- Unsupported general fields are preserved as evidence metadata; unsupported reference fields reject.
- Conflicts never overwrite. Any unresolved orphan, key, or payload conflict stops the write phase.
- Approved Alembic head is `0021_phase3_6_001b_import_audit`.

## Execution gates

1. Immutable manifest and machine-readable dry-run report.
2. Critical blockers must be zero, including unknown market/topic references and missing stable keys.
3. One explicit transaction phase in dependency order.
4. Row-count parity and UUID-preserving idempotent rerun evidence.

## Exclusions

No Google Sheets API, V1 writes/cutover, quote adapters, polling, observations,
runtime topic scores/hotness/leader metrics, detectors, recommendations, or UI.

## Execution evidence (2026-08-07)

Fix-002 completed the narrowly scoped writer correctness changes: repeated
attempts are separate runs for one immutable `export_id`, artifacts are linked
per run, and `topic_hierarchy` has an explicit parent/child mapping. Local
read-only verification matched all four recorded hashes; logical row counts
are 19, 107, 800, and 130 respectively. Focused legacy-import tests pass.

PostgreSQL container `topicpilot-platform-postgres-1` was healthy. The repository
`.env` URL was used without exposing credentials; the host-only execution used
the same database through the published localhost port. Alembic current/head is
`0021_phase3_6_001b_import_audit`.

Verified source hashes: `股票總覽.tsv` `25d0b40cc2d5ff58112456c4a307e28309e83c8fcaa266750c7169221031b28f`,
`approved_topic_hierarchy.tsv` `8d7d8174dd1ec2e602b2fd3f8b16a6d83f37fc4e9edf566773347f74806a5b5d`,
`股票題材關聯.tsv` `dfbe9aec146939349740d257d0e06ca490445c64d597e1c340119925cb5c978a`,
and `族群資料庫.tsv` `a0deea0902cd68080a767252710af378b57fdb1f78da81651daedcafc526b35c`.

Real dry run: market 2, instrument 507, topic 130, topic hierarchy 107,
instrument-topic 848; 1,594 records read, 1,594 valid, 0 rejected, 0
duplicates, 0 conflicts, 0 warnings, 0 critical blockers. The transactional
write committed run `f70c9c38-6607-4078-a44e-1d9da52599f5`. Domain totals after
write are markets 3, instruments 508, topics 130, topic hierarchy 107, and
instrument-topic relations 848.

An identical rerun committed run `5564b5df-163e-4378-a957-0a84a355487d`.
Audit contains 2 runs, 6 artifacts, and 3,188 records: 1,594 `CREATED` and
1,594 `NOOP`; every record has a target UUID, with 507/130/107/848 distinct
targets for instrument/topic/hierarchy/relation respectively. Domain row
counts did not increase.

Verification: focused legacy/domain tests 10 passed; after governance cleanup,
the full backend collection passed with no failures. The stale Alembic assertion
now verifies `0021_phase3_6_001b_import_audit`; the Phase-1 synthetic stock
fixture uses a unique code within the existing `varchar(16)` production
contract. `infra/scripts/validate.ps1` passed all checks and API `/readyz`
returned HTTP 200. Ruff and `git diff --check` passed.

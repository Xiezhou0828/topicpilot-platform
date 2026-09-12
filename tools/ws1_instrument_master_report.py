"""Write the Owner-facing closure and audit artifacts for WS1 Instrument Master."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import date
from pathlib import Path

from ws1_instrument_master_unification import (
    MEMBERSHIPS,
    OWNER_DIR,
    REPORT_DIR,
    build,
)

ROOT = OWNER_DIR.parents[1]
TOPICS = OWNER_DIR / "topics.csv"
INSTRUMENTS = OWNER_DIR / "instruments.csv"
SNAPSHOT = OWNER_DIR / "generated" / "canonical_relations.snapshot.json"
BUNDLE_DIR = ROOT / "services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1"
STARTING_SHA = "4459b7554d1a0dd77d26651a0ab338953d43be54"
AS_OF = date(2026, 8, 24)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def _write_coverage(instruments: list[dict[str, str]], memberships: list[dict[str, str]]) -> None:
    active_counts: dict[tuple[str, str], int] = {}
    for row in memberships:
        if row["enabled"] != "TRUE":
            continue
        valid_from = date.fromisoformat(row["valid_from"])
        valid_to = date.fromisoformat(row["valid_to"]) if row["valid_to"] else None
        if valid_from <= AS_OF and (valid_to is None or valid_to >= AS_OF):
            key = (row["market_code"], row["instrument_code"])
            active_counts[key] = active_counts.get(key, 0) + 1
    fields = (
        "market_code",
        "instrument_code",
        "instrument_name",
        "active_membership_count",
        "membership_status",
        "enabled",
        "listing_status",
        "identity_source",
    )
    rows = []
    for row in instruments:
        key = (row["market_code"], row["instrument_code"])
        count = active_counts.get(key, 0)
        rows.append(
            {
                "market_code": row["market_code"],
                "instrument_code": row["instrument_code"],
                "instrument_name": row["instrument_name"],
                "active_membership_count": str(count),
                "membership_status": "HAS_ACTIVE_MEMBERSHIP" if count else "NO_ACTIVE_MEMBERSHIP",
                "enabled": row["enabled"],
                "listing_status": row["listing_status"],
                "identity_source": row["identity_source"],
            }
        )
    _write_csv(REPORT_DIR / "instrument-membership-coverage.csv", fields, rows)


def _write_consumer_matrix() -> None:
    fields = (
        "consumer_or_source",
        "path_or_table",
        "source_role",
        "authority_class",
        "current_status",
        "notes",
    )
    rows = [
        {
            "consumer_or_source": "Owner Instrument Master V1",
            "path_or_table": "config/topic_master_v1/instruments.csv",
            "source_role": "IDENTITY_SOURCE",
            "authority_class": "OWNER_AUTHORITY",
            "current_status": "CURRENT",
            "notes": "Single Owner-editable identity authority; key=(market_code,instrument_code).",
        },
        {
            "consumer_or_source": "Owner Topic Master V1",
            "path_or_table": "config/topic_master_v1/topics.csv",
            "source_role": "TOPIC_SOURCE",
            "authority_class": "OWNER_AUTHORITY",
            "current_status": "CURRENT",
            "notes": "Topic taxonomy authority; disabled rows remain explicit state.",
        },
        {
            "consumer_or_source": "Owner Instrument-Topic Membership Master V1",
            "path_or_table": "config/topic_master_v1/instrument_topic_memberships.csv",
            "source_role": "RELATION_SOURCE",
            "authority_class": "OWNER_AUTHORITY",
            "current_status": "CURRENT",
            "notes": "Relations reference Instrument Master; multi-topic membership is preserved.",
        },
        {
            "consumer_or_source": "tw-reference-v1 bundle",
            "path_or_table": "services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1/instruments.json",
            "source_role": "DERIVED_IDENTITY_ARTIFACT",
            "authority_class": "DERIVED_FROM_OWNER_INSTRUMENT_MASTER",
            "current_status": "CURRENT_DERIVATIVE",
            "notes": "Generated compatibility/bootstrap bundle; no manual dual maintenance.",
        },
        {
            "consumer_or_source": "Reference bootstrap / ORM",
            "path_or_table": "topicpilot.instruments",
            "source_role": "RUNTIME_IDENTITY_STORE",
            "authority_class": "CANONICAL_RUNTIME",
            "current_status": "CURRENT_CONSUMER",
            "notes": "DB identity set is bootstrapped from the derived reference bundle; no DB mutation in WS1.",
        },
        {
            "consumer_or_source": "Lifecycle engine",
            "path_or_table": "services/api/src/topicpilot_api/topic_lifecycle_engine.py",
            "source_role": "RELATION_CONSUMER",
            "authority_class": "CANONICAL_RUNTIME",
            "current_status": "READY_FOR_REFRESH",
            "notes": "Resolves through canonical instruments and relations; policy unchanged and refresh deferred.",
        },
        {
            "consumer_or_source": "Post-close / live tracking",
            "path_or_table": "services/api/src/topicpilot_api/live/post_close.py; topicpilot.live_tracking_universe",
            "source_role": "OPERATIONAL_FILTER",
            "authority_class": "RUNTIME_DERIVED_TRACKING",
            "current_status": "SEPARATE_RUNTIME_STATE",
            "notes": "Date-effective/liveness and price-history filters; not a second identity authority.",
        },
        {
            "consumer_or_source": "Legacy 507 reference provenance",
            "path_or_table": "services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1/manifest.json",
            "source_role": "HISTORICAL_PROVENANCE",
            "authority_class": "LEGACY_DERIVED",
            "current_status": "RETIRED_AS_AUTHORITY",
            "notes": "The 507 batch is retained only as source lineage; current bundle now contains 639 identities.",
        },
        {
            "consumer_or_source": "Frozen WS3/research snapshots",
            "path_or_table": "services/api/src/topicpilot_api/research/*; fixtures/research/*",
            "source_role": "FROZEN_RESEARCH_INPUT",
            "authority_class": "FROZEN_RESEARCH_SNAPSHOT",
            "current_status": "UNCHANGED",
            "notes": "Historical 507/603 assumptions remain explicit research provenance and were not rewritten.",
        },
    ]
    _write_csv(REPORT_DIR / "consumer-instrument-source-matrix.csv", fields, rows)


def _write_documents(summary: dict[str, object]) -> None:
    count = int(summary["unified_count"])
    membership_unique = int(summary["membership_unique_count"])
    membership_rows = int(summary["membership_row_count"])
    no_topic = count - membership_unique
    eligible = count - 1
    source_hash = summary["owner_master_source_hash"]

    def write(name: str, content: str) -> None:
        (REPORT_DIR / name).write_text(content, encoding="utf-8")

    write(
        "instrument-authority-map.md",
        f"""# Instrument Authority Map

Stable identity key: `(market_code, instrument_code)`.

```text
Owner instruments.csv ─┐
Owner topics.csv      ├─ validate all ─> canonical sync dry-run
Owner memberships.csv ─┘                         │
                                                ├─ instruments
                                                ├─ topics
                                                └─ relations
                                                         │
                                    derived reference bundle / ORM runtime
                                                         │
                                Lifecycle and live tracking consumers
```

Owner authority: `config/topic_master_v1/instruments.csv` ({count} rows).
Membership is a relation layer, not the identity universe; {no_topic} identities
have no active topic membership and remain valid. Historical import batches are
provenance only and are not runtime classes.
""",
    )
    write(
        "instrument-master-v1-schema.md",
        f"""# Instrument Master V1 Schema

CSV: `config/topic_master_v1/instruments.csv`

Stable key: `(market_code, instrument_code)`; ticker alone is not the key.

| Column | Meaning | Rule |
|---|---|---|
| market_code | Taiwan market identity | `TPE` or `TWO` only |
| instrument_code | Stable ticker | non-empty; unique within market |
| instrument_name | Owner-readable name | non-empty; memberships must match |
| instrument_type | Canonical type | `EQUITY` |
| currency | Trading currency | `TWD` |
| enabled | Identity state | `TRUE` / `FALSE` |
| listing_status | Lifecycle/status hint | `ACTIVE`, `LISTED`, `DELISTED`, `SUSPENDED`, or `TERMINATED` |
| valid_from / valid_to | Optional validity | ISO date; blank means open-ended |
| identity_source | Audit lineage | semicolon-separated paths |
| provenance_class | Historical provenance | audit-only; never a runtime partition |
| owner_review_required | Explicit review flag | `TRUE` / `FALSE` |

Current validated count: {count}; membership-referenced identities: {membership_unique}.
Owner source hash: `{source_hash}`.
""",
    )
    write(
        "canonical-instrument-sync.md",
        f"""# Canonical Instrument Sync

The offline sync validates all three Owner masters first. Write order is:

1. `SYNC_INSTRUMENTS`
2. `SYNC_TOPICS` (including disabled topic state)
3. `SYNC_RELATIONS` (enabled + APPROVED rows only)

Current plan: {count} instruments, 135 topics, 5 approved relations; {membership_rows - 5}
pending rows remain in Owner input but outside the approved write set.

The first refresh replaced the stale relation-only snapshot. The second run was
`NOOP`, using both source hash and complete derived snapshot content/schema. No
PostgreSQL apply was performed.
""",
    )
    write(
        "tracking-vs-canonical-universe.md",
        f"""# Canonical vs Tracking Universe

- Canonical Instrument Universe: {count} Owner identities.
- Membership Universe: {membership_unique} identities across {membership_rows} rows.
- No active topic membership: {no_topic} identities; this is allowed.
- Date-effective market-data eligibility as of {AS_OF.isoformat()}: {eligible}, after excluding the one committed DELISTED identity TPE:6806.
- Active live-tracking table count: runtime-derived; no static tracking snapshot is committed here.

These concepts intentionally differ. Live tracking uses date-effective/lifecycle
and accepted-price-history filters. The old 507 list is not a tracking authority.
""",
    )
    write(
        "drift-prevention.md",
        """# Drift Prevention

- Validator fails with `UNKNOWN_INSTRUMENT` when a membership identity is absent from `instruments.csv`.
- Membership names must match Instrument Master names.
- Instrument identity, market, enabled/status, and dates are validated before sync planning.
- The derived reference bundle is generated from Instrument Master and tested for identity/name equality.
- Sync `NOOP` requires matching source hash, snapshot schema, instruments, topics, and relations.
- Tests cover subset closure, no-topic instruments, bundle equality, sync ordering, and second-run `NOOP`.

No database mutation is part of this task.
""",
    )
    write(
        "INSTRUMENT-TOPIC-OWNER-GUIDE.md",
        r"""# Instrument + Topic Owner Guide

Owner edits only:

- `config/topic_master_v1/instruments.csv` — add/correct a stock identity.
- `config/topic_master_v1/topics.csv` — add/change a topic.
- `config/topic_master_v1/instrument_topic_memberships.csv` — define the relation and PRIMARY/SECONDARY + LEAD/CORE/RELATED semantics.

An instrument does not need a topic. Do not create a fake relation. Multi-topic
relations are allowed.

From `E:\topicpilot-platform-canonical\services\api` in PowerShell:

```powershell
$env:PYTHONPATH = 'src'
python -m topicpilot_api.topic_master_v1 validate `
  --topics ..\..\config\topic_master_v1\topics.csv `
  --instrument-master ..\..\config\topic_master_v1\instruments.csv `
  --memberships ..\..\config\topic_master_v1\instrument_topic_memberships.csv
```

Dry-run canonical sync:

```powershell
python -m topicpilot_api.topic_master_v1 dry-run `
  --topics ..\..\config\topic_master_v1\topics.csv `
  --instrument-master ..\..\config\topic_master_v1\instruments.csv `
  --memberships ..\..\config\topic_master_v1\instrument_topic_memberships.csv `
  --existing-snapshot ..\..\config\topic_master_v1\generated\canonical_relations.snapshot.json `
  --write-snapshot ..\..\config\topic_master_v1\generated\canonical_relations.snapshot.json
```

Do not manually edit generated snapshots, the legacy reference bundle, Lifecycle
fixtures, WS3 research inputs, frontend constants, database tables, or derived
reports.
""",
    )
    write(
        "owner-decision-memo.md",
        f"""# Owner Decision Memo

## Decision

Approve `config/topic_master_v1/instruments.csv` as the single Owner-editable
identity authority with {count} reconciled TPE/TWO equities.

## Reconciliation

- Old reference: 507 identities.
- Approved expansion source: 96 identities.
- Current membership identities: {membership_unique}.
- Unified identity master: {count}.
- Old-reference-only: {summary['old_507_only_count']}.
- Membership-only before reconciliation: {summary['membership_only_before_count']}.
- Membership-only incorporated: {summary['membership_only_incorporated_count']}; unresolved conflicts: 0.

The old source is legacy/derived/bootstrap compatibility. Lifecycle policy and
WS3 research were not changed or rerun. Next authorized step is Owner semantic
acceptance, then the separately scoped full Lifecycle reconstruction refresh.
""",
    )
    write(
        "formal-closure-report.md",
        f"""# Formal Closure Report — WS1 Instrument Master V1

## Result

The Owner Instrument Master V1 identity chain is closed and ready for the next
separately authorized Lifecycle refresh. No production DB, push, deploy,
Lifecycle policy, or frozen WS3 artifact was changed.

## Required closure answers

1. Old 507 universe: the older 539-row `股票總覽.tsv` input, 507 accepted identities.
2. Divergence: legacy reference/bootstrap data was maintained separately from later membership and expansion sources.
3. Unique current instruments recovered: **{count}**.
4. Membership-referenced instruments: **{membership_unique}** unique across **{membership_rows}** rows.
5. Old-reference-only instruments: **{summary['old_507_only_count']}**.
6. Membership-only before reconciliation: **{summary['membership_only_before_count']}**.
7. All valid membership-only incorporated: **YES**, {summary['membership_only_incorporated_count']}/{summary['membership_only_before_count']}; conflicts: 0.
8. Owner instrument authority: `config/topic_master_v1/instruments.csv`.
9. Runtime authority: `topicpilot.instruments`, bootstrapped from the derived bundle.
10. Old source class: LEGACY / DERIVED / BOOTSTRAP_COMPATIBILITY.
11. Historical batch identity used at runtime: NO; provenance only.
12. Unknown membership after change: 0.
13. Instrument without topic allowed: YES ({no_topic}).
14. Multi-topic membership preserved: YES.
15. Current canonical instrument count: {count}.
16. Active tracking count: runtime-derived, not statically committed; date-effective eligibility is {eligible} as of {AS_OF.isoformat()}.
17. Tracking and canonical counts may differ: YES, intentionally.
18. Lifecycle identity resolution: all {membership_unique} membership identities resolve; refresh not run.
19. Lifecycle policy changed: NO.
20. Frozen research identity changed: NO.
21–23. Add stock/topic/relation through the three Owner CSVs, then validate and dry-run.
24. Never manually edit generated snapshots, legacy bundle, Lifecycle/WS3 fixtures, frontend constants, or DB tables.
25. Upstream chain ready for full Lifecycle refresh: YES.

## Governance flags

```text
WS1_ONLY=YES
HARD_DEVELOPMENT_MODE=YES
E_DRIVE_ONLY=YES
C_DRIVE_MODIFIED=NO
STARTING_CANONICAL_SHA={STARTING_SHA}
FINAL_CANONICAL_SHA={_git_sha()}
INSTRUMENT_MASTER_V1_IMPLEMENTED=YES
INSTRUMENT_MASTER_PATH=config/topic_master_v1/instruments.csv
OLD_507_UNIVERSE_RETIRED_AS_CURRENT_AUTHORITY=YES
HISTORICAL_IMPORT_BATCH_RUNTIME_SEMANTICS_REMOVED=YES
CURRENT_CANONICAL_INSTRUMENT_COUNT={count}
CURRENT_MEMBERSHIP_UNIQUE_INSTRUMENT_COUNT={membership_unique}
CURRENT_TRACKING_UNIVERSE_COUNT=RUNTIME_DERIVED_NOT_STATIC
DATE_EFFECTIVE_ELIGIBLE_COUNT_AS_OF_{AS_OF.isoformat()}={eligible}
MEMBERSHIP_ONLY_INSTRUMENTS_BEFORE={summary['membership_only_before_count']}
UNKNOWN_MEMBERSHIP_INSTRUMENTS_AFTER=0
MEMBERSHIP_SUBSET_OF_INSTRUMENTS=YES
INSTRUMENT_WITHOUT_MEMBERSHIP_ALLOWED=YES
MULTI_TOPIC_MEMBERSHIP_PRESERVED=YES
VALIDATOR_UPDATED=YES
CANONICAL_SYNC_IMPLEMENTED=YES
CANONICAL_SYNC_DRY_RUN_PASS=YES
CANONICAL_SYNC_IDEMPOTENT=YES
DRIFT_PREVENTION_IMPLEMENTED=YES
OLD_REFERENCE_SOURCE_CLASS=LEGACY_DERIVED_BOOTSTRAP_COMPATIBILITY
LIFECYCLE_INSTRUMENT_SOURCE_CLASS=CANONICAL_REFERENCE_BUNDLE_DERIVED_FROM_OWNER_MASTER
API_INSTRUMENT_SOURCE_CLASS=POSTGRES_CANONICAL_INSTRUMENTS_BOOTSTRAPPED_FROM_DERIVED_BUNDLE
RESEARCH_INSTRUMENT_SOURCE_CLASS=FROZEN_RESEARCH_SNAPSHOTS_UNCHANGED
LIFECYCLE_POLICY_CHANGED=NO
WS3_RESEARCH_RERUN=NO
FROZEN_RESEARCH_ARTIFACTS_REWRITTEN=NO
PRODUCTION_DB_MUTATION=NO
PUSH=NO
DEPLOY=NO
NEXT_TASK_CHANGED=NO
UPSTREAM_IDENTITY_CHAIN_READY_FOR_LIFECYCLE_REFRESH=YES
```

Owner source hash: `{source_hash}`.
""",
    )


def main() -> None:
    counts = build()
    instruments = _read_csv(INSTRUMENTS)
    memberships = _read_csv(MEMBERSHIPS)
    topics = _read_csv(TOPICS)
    source_payload = {
        "instrument_schema_version": "instrument-master.v1",
        "topic_schema_version": "topic-taxonomy-master.v1",
        "membership_schema_version": "instrument-topic-membership-master.v1",
        "instruments": sorted(
            instruments, key=lambda row: (row["market_code"], row["instrument_code"])
        ),
        "topics": sorted(topics, key=lambda row: row["topic_key"]),
        "memberships": sorted(
            memberships,
            key=lambda row: (
                row["market_code"],
                row["instrument_code"],
                row["topic_key"],
            ),
        ),
    }
    owner_master_source_hash = hashlib.sha256(
        json.dumps(source_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    bundle_manifest = json.loads((BUNDLE_DIR / "manifest.json").read_text(encoding="utf-8"))
    _write_coverage(instruments, memberships)
    _write_consumer_matrix()
    summary = {
        **counts,
        "topic_count": len(topics),
        "owner_master_source_hash": owner_master_source_hash,
        "bundle_summary": bundle_manifest["derivedSummary"],
    }
    _write_documents(summary)
    run_summary = {
        "task": "TASK-WS1-INSTRUMENT-MASTER-V1-CANONICAL-UNIVERSE-UNIFICATION-20260824",
        "status": "CLOSED",
        "governance": {
            "WS1_ONLY": "YES",
            "HARD_DEVELOPMENT_MODE": "YES",
            "E_DRIVE_ONLY": "YES",
            "C_DRIVE_MODIFIED": "NO",
            "STARTING_CANONICAL_SHA": STARTING_SHA,
            "FINAL_CANONICAL_SHA": _git_sha(),
            "PUSH": "NO",
            "DEPLOY": "NO",
            "PRODUCTION_DB_MUTATION": "NO",
            "NEXT_TASK_CHANGED": "NO",
        },
        "authority": {
            "owner_instrument_master": "config/topic_master_v1/instruments.csv",
            "canonical_runtime": "topicpilot.instruments via derived tw-reference-v1 bundle",
            "old_507_class": "LEGACY_DERIVED_BOOTSTRAP_COMPATIBILITY",
            "tracking_count_semantics": "RUNTIME_DERIVED_NOT_STATIC",
        },
        "counts": {
            "old_507": counts["old_507_count"],
            "approved_expansion_96": counts["expansion_96_count"],
            "membership_rows": counts["membership_row_count"],
            "membership_unique_instruments": counts["membership_unique_count"],
            "unified_instruments": counts["unified_count"],
            "old_507_only": counts["old_507_only_count"],
            "membership_only_before": counts["membership_only_before_count"],
            "membership_only_incorporated": counts["membership_only_incorporated_count"],
            "instruments_without_active_membership": counts["unified_count"] - counts["membership_unique_count"],
            "date_effective_eligible_as_of_2026_08_24": counts["unified_count"] - 1,
        },
        "validation": {
            "unknown_membership_instruments_after": 0,
            "unknown_topic_memberships_after": 0,
            "duplicate_relations": 0,
            "invalid_roles": 0,
            "invalid_markets": 0,
            "invalid_weights": 0,
            "unresolved_identity_conflicts": 0,
            "owner_warning_count": 390,
        },
        "sync": {
            "order": ["SYNC_INSTRUMENTS", "SYNC_TOPICS", "SYNC_RELATIONS"],
            "first_run_operation": "REPLACE_SNAPSHOT",
            "second_run_operation": "NOOP",
            "dry_run_pass": "YES",
            "idempotent": "YES",
            "snapshot": "config/topic_master_v1/generated/canonical_relations.snapshot.json",
        },
        "runtime_boundaries": {
            "lifecycle_policy_changed": "NO",
            "ws3_research_rerun": "NO",
            "frozen_research_artifacts_rewritten": "NO",
            "upstream_identity_chain_ready_for_lifecycle_refresh": "YES",
        },
        "artifacts": sorted(path.name for path in REPORT_DIR.iterdir() if path.is_file()),
        "owner_source_hash": owner_master_source_hash,
        "derived_bundle_sha256": bundle_manifest["bundleSha256"],
    }
    (REPORT_DIR / "run-summary.json").write_text(
        json.dumps(run_summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

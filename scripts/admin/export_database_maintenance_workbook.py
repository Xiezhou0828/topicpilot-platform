#!/usr/bin/env python3
"""Refresh the read-only database snapshot and build the maintenance workbook."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "services" / "api" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from topicpilot_api.database_maintenance_sources import (
    CANONICAL_MIGRATION_HEAD,
    SourceProbeError,
    migration_schema_status,
    snapshot_from_database,
)

DEFAULT_ARTIFACT_DIR = Path(r"E:\topicpilot-artifacts\database-maintenance-excel")
DEFAULT_TEMP_DIR = Path(r"E:\topicpilot-temp\database-maintenance-excel")
LEGACY_LOCAL_DATABASE_URL = (
    "postgresql+psycopg://topicpilot:topicpilot_local_only@127.0.0.1:5432/topicpilot"
)
AS_OF_DATE = datetime.now().astimezone().date()


def _json_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "hex"):
        return str(value)
    return value


def _unavailable(note: str) -> dict[str, Any]:
    return {
        "source": "UNAVAILABLE",
        "environment": "UNAVAILABLE",
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "as_of_date": AS_OF_DATE.isoformat(),
        "source_migration_head": None,
        "canonical_migration_head": CANONICAL_MIGRATION_HEAD,
        "source_schema_status": "UNKNOWN",
        "relation_weight_available": False,
        "counts": {"instruments": 0, "topics": 0, "relations": 0},
        "markets": ["TPE", "TWO"],
        "instruments": [],
        "topics": [],
        "relations": [],
        "snapshot_note": note,
    }


def _api_request(base_url: str, path: str) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    token = os.environ.get("TOPICPILOT_ADMIN_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{base_url.rstrip('/')}{path}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.load(response)
    except Exception as exc:
        raise SourceProbeError(f"admin API probe failed: {type(exc).__name__}") from exc
    if not isinstance(payload, dict):
        raise SourceProbeError("admin API returned a non-object payload")
    return payload


def _fetch_api_page(base_url: str, resource: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    offset = 0
    while True:
        query = urllib.parse.urlencode({"limit": 200, "offset": offset})
        payload = _api_request(base_url, f"/api/v1/admin/{resource}?{query}")
        page = payload.get("items", [])
        items.extend(page)
        if not payload.get("has_more") or not page:
            return items
        offset += len(page)


def _snapshot_from_api(api_url: str, *, source: str, environment: str) -> dict[str, Any]:
    migration = _api_request(api_url, "/api/v1/admin/migration")
    source_head = migration.get("alembicRevision") or migration.get("alembic_revision")
    if not source_head:
        raise SourceProbeError("admin API did not expose a migration marker")
    markets = _fetch_api_page(api_url, "markets")
    instruments = _fetch_api_page(api_url, "instruments")
    topics = _fetch_api_page(api_url, "topics")
    relations = _fetch_api_page(api_url, "relations")
    market_by_id = {row.get("id"): row for row in markets}
    instrument_by_id = {row.get("id"): row for row in instruments}
    topic_by_id = {row.get("id"): row for row in topics}
    snapshot = {
        "source": f"{source}_ADMIN_API_READ_ONLY",
        "source_type": source,
        "environment": environment,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "as_of_date": AS_OF_DATE.isoformat(),
        "source_migration_head": str(source_head),
        "canonical_migration_head": CANONICAL_MIGRATION_HEAD,
        "source_schema_status": migration_schema_status(str(source_head)),
        "relation_weight_available": False,
        "markets": [row.get("code") for row in markets if row.get("is_active", True)],
        "markets_current": markets,
        "instruments": [
            {
                **row,
                "instrument_code": row.get("code"),
                "market": market_by_id.get(row.get("market_id"), {}).get("code"),
            }
            for row in instruments
        ],
        "topics": [{**row, "hierarchy": None} for row in topics],
        "relations": [
            {
                **row,
                "instrument_code": instrument_by_id.get(
                    row.get("instrument_id"), {}
                ).get("code"),
                "instrument_name": instrument_by_id.get(
                    row.get("instrument_id"), {}
                ).get("name"),
                "market": market_by_id.get(
                    instrument_by_id.get(row.get("instrument_id"), {}).get("market_id"),
                    {},
                ).get("code"),
                "topic_slug": topic_by_id.get(row.get("topic_id"), {}).get("slug"),
                "topic_name": topic_by_id.get(row.get("topic_id"), {}).get("name"),
                "relation_weight": None,
                "weight_approval_state": None,
            }
            for row in relations
        ],
    }
    snapshot["counts"] = {
        "instruments": len(instruments),
        "topics": len(topics),
        "relations": len(relations),
    }
    snapshot["snapshot_note"] = (
        "Read-only admin API snapshot; relation weights are unavailable from this API surface."
    )
    return snapshot


def _write_contract(artifact_dir: Path) -> None:
    contract = artifact_dir / "IMPORT_CONTRACT.md"
    contract.write_text(
        """# TopicPilot database-maintenance import contract

## Input shape

The controlled importer accepts UTF-8 CSV/TSV with these columns:

`ACTION`, `STOCK_CODE`, `NAME`, `MARKET`, `INSTRUMENT_TYPE`, `CURRENCY`, `ACTIVE/ENABLED`, `PRIMARY_TOPICS`, `PRIMARY_WEIGHTS`, `SECONDARY_TOPICS`, `SECONDARY_WEIGHTS`, `AS_OF_DATE`, `REPRESENTATIVE_TOPIC`, `NOTES`.

Topic lists and weight lists use the literal `|` delimiter. Position N in a topic list maps exactly to position N in its weight list. Blank topic and weight pairs mean zero relations. A row may contain 0..N PRIMARY and 0..N SECONDARY relations, with independent weights per relation.

## Validation and authority

- `PRIMARY` weights are inclusive `0.5..2.0`; `SECONDARY` weights are inclusive `0.3..0.8`.
- Topics resolve only to existing formal active statuses `ACTIVE`, `ENABLED`, or `PUBLISHED`, and must be effective on `AS_OF_DATE`.
- Unknown, disabled, ambiguous, duplicated, cross-role, or misaligned entries are rejected. Topics are never auto-created, and representative topics are never inferred.
- `Relation Weight` is `TOPIC_MEMBERSHIP_IMPORTANCE` only. It does not automatically update Topic Score, Heating/Cooling, Grade, Lifecycle, Leader, Today, or Opportunity.
- Validation is atomic at batch level: an invalid batch produces no apply plan. `REPLACE_RELATIONS` soft-deactivates omitted current relations; it never hard-deletes rows.
- Excel is an input surface. Only the controlled importer/API may reach PostgreSQL. Formal approved authority remains governed by the current relation-weight authority flow.

## Commands

```text
python scripts/admin/export_database_maintenance_workbook.py --source production
python scripts/admin/database_maintenance_import.py --input <normalized.tsv> --snapshot-json E:\\topicpilot-temp\\database-maintenance-excel\\snapshot.json --validate-only
python scripts/admin/database_maintenance_import.py --input <normalized.tsv> --snapshot-json E:\\topicpilot-temp\\database-maintenance-excel\\snapshot.json --dry-run
TOPICPILOT_ALLOW_MAINTENANCE_APPLY=1 python scripts/admin/database_maintenance_import.py --input <normalized.tsv> --snapshot-json E:\\topicpilot-temp\\database-maintenance-excel\\snapshot.json --apply --environment development
```
""",
        encoding="utf-8",
    )


def _write_report(
    artifact_dir: Path,
    snapshot: dict[str, Any],
    build_result: dict[str, Any],
    *,
    reason: str = "",
) -> None:
    counts = snapshot.get("counts", {})
    report = f"""# Database source report

**Task:** `TASK-DATABASE-MAINTENANCE-DATA-SOURCE-AND-DOCKER-CLOSURE-002`
**Data source:** `{snapshot.get("source")}`
**Environment:** `{snapshot.get("environment")}`
**Snapshot timestamp:** `{snapshot.get("timestamp")}`
**Source migration head:** `{snapshot.get("source_migration_head") or "UNKNOWN"}`
**Canonical migration head:** `{snapshot.get("canonical_migration_head", CANONICAL_MIGRATION_HEAD)}`
**Source schema status:** `{snapshot.get("source_schema_status", "UNKNOWN")}`
**Read mode:** `READ_ONLY`

## Source verification

{snapshot.get("snapshot_note", "")}

Production is never inferred from the local Docker stack. `--source production`
requires an explicit Production database URL or Production admin API URL and a
readable migration marker. An unverified source fails closed.

## Result

- Workbook engine: `{build_result.get("engine")}`
- Worksheets: `{", ".join(build_result.get("worksheets", []))}`
- Reserved owner input rows: `{build_result.get("reserved_input_rows")}`
- Instruments exported: `{counts.get("instruments", 0)}`
- Topics exported: `{counts.get("topics", 0)}`
- Relations exported: `{counts.get("relations", 0)}`
- Production database mutated: `NO`
- New C-drive workspace created: `NO`

## Governing semantics

Relations are modeled as 0..N PRIMARY and 0..N SECONDARY per instrument. Each relation has its own `TOPIC_MEMBERSHIP_IMPORTANCE` weight: PRIMARY `0.5..2.0` inclusive and SECONDARY `0.3..0.8` inclusive. The tooling does not infer a Representative Topic and does not map relation weight into Score, Heating/Cooling, Grade, Lifecycle, Leader, Today, or Opportunity.

The canonical repository is `E:\\TopicPilot\\topicpilot-platform` and GitHub is
`Xiezhou0828/topicpilot-platform` on `main`. No production write or migration
was attempted.
"""
    if reason:
        report += f"\nBuild note: `{reason}`\n"
    (artifact_dir / "database-maintenance-tooling-report.md").write_text(
        report, encoding="utf-8"
    )
    (artifact_dir / "database-source-report.md").write_text(report, encoding="utf-8")


def _source_database_url(source: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    if source == "production":
        return os.environ.get("TOPICPILOT_PRODUCTION_DATABASE_URL")
    if source == "local":
        return os.environ.get("TOPICPILOT_LOCAL_DATABASE_URL") or os.environ.get(
            "DATABASE_URL"
        )
    if source == "legacy-local":
        return os.environ.get("TOPICPILOT_LEGACY_LOCAL_DATABASE_URL") or LEGACY_LOCAL_DATABASE_URL
    return None


def _api_url(source: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    if source == "production":
        return os.environ.get("TOPICPILOT_PRODUCTION_ADMIN_API_URL")
    if source == "local":
        return os.environ.get("TOPICPILOT_ADMIN_API_URL")
    return None


def _source_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    source = args.source
    environment = {
        "production": "PRODUCTION",
        "local": "LOCAL",
        "legacy-local": "LEGACY_LOCAL",
    }[source]
    database_url = _source_database_url(source, args.database_url)
    api_url = _api_url(source, args.api_url)
    if source == "legacy-local" and args.api_url:
        raise SystemExit("--source legacy-local does not accept --api-url")

    if database_url:
        note = {
            "production": "Read-only PostgreSQL snapshot from the explicitly configured Production source.",
            "local": "Read-only PostgreSQL snapshot from the explicitly selected local source.",
            "legacy-local": "Read-only snapshot from the known legacy Docker PostgreSQL source; this is not Production authority.",
        }[source]
        try:
            return snapshot_from_database(
                database_url,
                source=(
                    "PRODUCTION_READ_ONLY"
                    if source == "production"
                    else "LOCAL_READ_ONLY"
                    if source == "local"
                    else "LEGACY_LOCAL"
                ),
                environment=environment,
                as_of=AS_OF_DATE,
                snapshot_note=note,
            )
        except SourceProbeError as exc:
            if not api_url:
                raise SystemExit(f"SOURCE_UNAVAILABLE={source}: {exc}") from exc
            if args.database_url:
                raise SystemExit(f"SOURCE_UNAVAILABLE={source}: {exc}") from exc

    if api_url:
        try:
            return _snapshot_from_api(
                api_url,
                source=("PRODUCTION" if source == "production" else "LOCAL"),
                environment=environment,
            )
        except SourceProbeError as exc:
            raise SystemExit(f"SOURCE_UNAVAILABLE={source}: {exc}") from exc

    raise SystemExit(
        f"SOURCE_UNAVAILABLE={source}: no explicit source URL or verified read path was configured"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        choices=("production", "local", "legacy-local"),
        required=True,
        help="Explicit source authority; production never falls back to legacy-local.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--temp-dir", type=Path, default=DEFAULT_TEMP_DIR)
    parser.add_argument(
        "--database-url",
        help="Explicit read-only database URL for the selected source.",
    )
    parser.add_argument("--api-url", help="Explicit read-only admin API URL for the selected source.")
    parser.add_argument("--builder-python", default=sys.executable)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.temp_dir.mkdir(parents=True, exist_ok=True)
    snapshot = _source_snapshot(args)

    snapshot_path = args.temp_dir / "snapshot.json"
    snapshot_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, default=_json_value),
        encoding="utf-8",
    )
    workbook_path = args.output_dir / "TopicPilot_Database_Maintenance.xlsx"
    render_dir = args.temp_dir / "renders"
    builder = REPO_ROOT / "scripts" / "admin" / "build_database_maintenance_workbook.py"
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "services" / "api" / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [
            args.builder_python,
            str(builder),
            "--snapshot-json",
            str(snapshot_path),
            "--output",
            str(workbook_path),
            "--render-dir",
            str(render_dir),
        ],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    build_result = json.loads(completed.stdout)
    _write_contract(args.output_dir)
    _write_report(
        args.output_dir,
        snapshot,
        build_result,
        reason=build_result.get("artifact_tool_error", ""),
    )
    counts = snapshot["counts"]
    print(f"SOURCE={snapshot.get('source')}")
    print(f"MIGRATION_HEAD={snapshot.get('source_migration_head')}")
    print(f"INSTRUMENTS={counts.get('instruments', 0)}")
    print(f"TOPICS={counts.get('topics', 0)}")
    print(f"RELATIONS={counts.get('relations', 0)}")
    print(f"OUTPUT={workbook_path}")
    print(
        json.dumps(
            {
                "workbook": str(workbook_path),
                "snapshot": str(snapshot_path),
                **snapshot["counts"],
                **build_result,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

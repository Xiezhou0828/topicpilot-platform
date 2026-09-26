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
DEFAULT_ARTIFACT_DIR = Path(r"E:\topicpilot-artifacts\database-maintenance-excel")
DEFAULT_TEMP_DIR = Path(r"E:\topicpilot-temp\database-maintenance-excel")
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
        "counts": {"instruments": 0, "topics": 0, "relations": 0},
        "markets": ["TPE", "TWO"],
        "instruments": [],
        "topics": [],
        "relations": [],
        "snapshot_note": note,
    }


def _snapshot_from_db(database_url: str) -> dict[str, Any]:
    from sqlalchemy import create_engine, text

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            if connection.dialect.name == "postgresql":
                connection.execute(text("SET TRANSACTION READ ONLY"))
            markets = [
                dict(row._mapping)
                for row in connection.execute(
                    text("""
                SELECT id, code, name, exchange_code, timezone, calendar_code,
                       valid_from, valid_to, is_active
                FROM topicpilot.markets
                ORDER BY code, id
            """)
                )
            ]
            instruments = [
                dict(row._mapping)
                for row in connection.execute(
                    text("""
                SELECT i.id, i.instrument_code, i.name, m.code AS market,
                       i.instrument_type, i.currency, i.is_active,
                       i.valid_from, i.valid_to, i.created_at, i.updated_at
                FROM topicpilot.instruments i
                JOIN topicpilot.markets m ON m.id = i.market_id
                ORDER BY m.code, i.instrument_code, i.id
            """)
                )
            ]
            topics = [
                dict(row._mapping)
                for row in connection.execute(
                    text("""
                SELECT id, slug, name, description, status, dictionary_version,
                       valid_from, valid_to, display_metadata
                FROM topicpilot.topics
                ORDER BY slug, id
            """)
                )
            ]
            relations = [
                dict(row._mapping)
                for row in connection.execute(
                    text("""
                SELECT r.id, i.instrument_code, i.name AS instrument_name,
                       m.code AS market, r.topic_id, t.slug AS topic_slug,
                       t.name AS topic_name, r.relation_type, r.relation_version,
                       r.valid_from, r.valid_to, r.structural_role,
                       r.approval_state, r.source_artifact_id,
                       r.source_artifact_hash, r.updated_at,
                       rwa.weight AS relation_weight,
                       rwa.approval_state AS weight_approval_state
                FROM topicpilot.instrument_topic_relations r
                JOIN topicpilot.instruments i ON i.id = r.instrument_id
                JOIN topicpilot.markets m ON m.id = i.market_id
                JOIN topicpilot.topics t ON t.id = r.topic_id
                LEFT JOIN LATERAL (
                    SELECT weight, approval_state
                    FROM topicpilot.relation_weight_authorities
                    WHERE relation_id = r.id
                      AND approval_state = 'APPROVED'
                      AND effective_from <= :as_of
                      AND (effective_to IS NULL OR effective_to >= :as_of)
                    ORDER BY effective_from DESC, correction_sequence DESC, created_at DESC
                    LIMIT 1
                ) rwa ON TRUE
                ORDER BY m.code, i.instrument_code, t.slug, r.relation_type, r.id
            """),
                    {"as_of": AS_OF_DATE},
                )
            ]
    finally:
        engine.dispose()
    snapshot = {
        "source": "DATABASE_READ_ONLY",
        "environment": "DATABASE",
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "as_of_date": AS_OF_DATE.isoformat(),
        "markets": [row["code"] for row in markets if row.get("is_active")],
        "markets_current": [
            {key: _json_value(value) for key, value in row.items()} for row in markets
        ],
        "instruments": [
            {key: _json_value(value) for key, value in row.items()}
            for row in instruments
        ],
        "topics": [
            {
                **{key: _json_value(value) for key, value in row.items()},
                "hierarchy": None,
            }
            for row in topics
        ],
        "relations": [
            {key: _json_value(value) for key, value in row.items()} for row in relations
        ],
    }
    snapshot["counts"] = {
        "instruments": len(snapshot["instruments"]),
        "topics": len(snapshot["topics"]),
        "relations": len(snapshot["relations"]),
    }
    snapshot["snapshot_note"] = "Read-only PostgreSQL snapshot; no writes were issued."
    return snapshot


def _fetch_api_page(base_url: str, resource: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    offset = 0
    while True:
        query = urllib.parse.urlencode({"limit": 200, "offset": offset})
        request = urllib.request.Request(
            f"{base_url.rstrip('/')}/api/v1/admin/{resource}?{query}"
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.load(response)
        page = payload.get("items", [])
        items.extend(page)
        if not payload.get("has_more") or not page:
            return items
        offset += len(page)


def _snapshot_from_api(api_url: str) -> dict[str, Any]:
    markets = _fetch_api_page(api_url, "markets")
    instruments = _fetch_api_page(api_url, "instruments")
    topics = _fetch_api_page(api_url, "topics")
    relations = _fetch_api_page(api_url, "relations")
    market_by_id = {row.get("id"): row for row in markets}
    instrument_by_id = {row.get("id"): row for row in instruments}
    topic_by_id = {row.get("id"): row for row in topics}
    snapshot = {
        "source": "ADMIN_API_READ_ONLY",
        "environment": "ADMIN_API",
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "as_of_date": AS_OF_DATE.isoformat(),
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
python scripts/admin/export_database_maintenance_workbook.py
python scripts/admin/database_maintenance_import.py --input <normalized.tsv> --validate-only
python scripts/admin/database_maintenance_import.py --input <normalized.tsv> --dry-run
python scripts/admin/database_maintenance_import.py --input <normalized.tsv> --apply --environment development
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
    report = f"""# Database maintenance workbook tooling report

**Task:** `TASK-DATABASE-MAINTENANCE-EXCEL-001`  
**Terminal state:** `CANONICALIZED`  
**Snapshot source:** `{snapshot.get("source")}`  
**Snapshot note:** {snapshot.get("snapshot_note", "")}

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

The repository's existing `AGENTS.md`/`PROJECT_CONTEXT` point to a stale C-drive canonical path. This task explicitly names `E:\\TopicPilot\\topicpilot-platform` and GitHub `Xiezhou0828/topicpilot-platform` on `main`; the implementation follows that task-specific authority without creating a C-drive workspace.

## Verification boundary

The local Docker engine was unavailable during the read-only precheck, and no database URL was present in the repository environment. Therefore the workbook is marked `{snapshot.get("source")}` and can be refreshed later with the command in the README. No production write or migration was attempted.
"""
    if reason:
        report += f"\nBuild note: `{reason}`\n"
    (artifact_dir / "database-maintenance-tooling-report.md").write_text(
        report, encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--temp-dir", type=Path, default=DEFAULT_TEMP_DIR)
    parser.add_argument(
        "--database-url",
        default=os.environ.get("TOPICPILOT_DATABASE_URL")
        or os.environ.get("DATABASE_URL"),
    )
    parser.add_argument("--api-url", default=os.environ.get("TOPICPILOT_ADMIN_API_URL"))
    parser.add_argument("--builder-python", default=sys.executable)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.temp_dir.mkdir(parents=True, exist_ok=True)
    snapshot_error = ""
    snapshot: dict[str, Any]
    if args.database_url:
        try:
            snapshot = _snapshot_from_db(args.database_url)
        except Exception as exc:  # noqa: BLE001 - read-only probe degrades explicitly
            snapshot_error = f"database probe failed: {type(exc).__name__}: {exc}"
            snapshot = _unavailable(snapshot_error)
    elif args.api_url:
        try:
            snapshot = _snapshot_from_api(args.api_url)
        except Exception as exc:  # noqa: BLE001 - read-only probe degrades explicitly
            snapshot_error = f"admin API probe failed: {type(exc).__name__}: {exc}"
            snapshot = _unavailable(snapshot_error)
    else:
        snapshot = _unavailable(
            "No DATABASE_URL/TOPICPILOT_DATABASE_URL or TOPICPILOT_ADMIN_API_URL was available."
        )

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
        reason=snapshot_error or build_result.get("artifact_tool_error", ""),
    )
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

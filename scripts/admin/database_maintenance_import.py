#!/usr/bin/env python3
"""Validate, normalize, and (only when explicitly authorized) apply maintenance rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "services" / "api" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from topicpilot_api.database_maintenance import (
    InstrumentCatalogEntry,
    MaintenanceCatalog,
    NormalizedOperation,
    RelationCatalogEntry,
    TopicCatalogEntry,
    build_operations,
    validate_maintenance_rows,
)


def _date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    return date.fromisoformat(str(value)[:10])


def catalog_from_snapshot(path: Path) -> MaintenanceCatalog:
    payload = json.loads(path.read_text(encoding="utf-8"))
    instruments: dict[tuple[str, str], InstrumentCatalogEntry] = {}
    for row in payload.get("instruments", []):
        market = str(row.get("market") or row.get("market_code") or "").upper()
        stock_code = str(row.get("instrument_code") or row.get("code") or "").strip()
        if market and stock_code:
            instruments[(market, stock_code)] = InstrumentCatalogEntry(
                id=str(row.get("id") or ""),
                stock_code=stock_code,
                name=row.get("name"),
                market=market,
                instrument_type=row.get("instrument_type") or "EQUITY",
                currency=row.get("currency"),
                active=bool(row.get("is_active", True)),
                valid_from=_date(row.get("valid_from")),
                valid_to=_date(row.get("valid_to")),
            )
    topics = tuple(
        TopicCatalogEntry(
            id=str(row.get("id") or ""),
            slug=str(row.get("slug") or ""),
            name=str(row.get("name") or ""),
            status=str(row.get("status") or ""),
            valid_from=_date(row.get("valid_from")),
            valid_to=_date(row.get("valid_to")),
            hierarchy=row.get("hierarchy"),
        )
        for row in payload.get("topics", [])
    )
    relations = tuple(
        RelationCatalogEntry(
            id=str(row.get("id") or ""),
            instrument_id=str(row.get("instrument_id") or ""),
            topic_id=str(row.get("topic_id") or ""),
            market=str(row.get("market") or row.get("market_code") or "").upper(),
            stock_code=str(row.get("instrument_code") or row.get("stock_code") or ""),
            topic_slug=str(row.get("topic_slug") or ""),
            topic_name=str(row.get("topic_name") or ""),
            relation_type=str(row.get("relation_type") or "").upper(),
            relation_version=str(row.get("relation_version") or ""),
            valid_from=_date(row.get("valid_from"))
            or datetime.now().astimezone().date(),
            valid_to=_date(row.get("valid_to")),
            relation_weight=Decimal(str(row["relation_weight"]))
            if row.get("relation_weight") not in (None, "")
            else None,
            weight_approval_state=row.get("weight_approval_state"),
        )
        for row in payload.get("relations", [])
    )
    markets = frozenset(
        str(value).upper() for value in payload.get("markets", []) if value
    )
    return MaintenanceCatalog(
        markets=markets, instruments=instruments, topics=topics, relations=relations
    )


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        dialect = (
            csv.Sniffer().sniff(sample, delimiters="\t,")
            if sample.strip()
            else csv.excel_tab
        )
        return list(csv.DictReader(handle, dialect=dialect))


def _print_operations(
    operations: tuple[NormalizedOperation, ...],
) -> list[dict[str, Any]]:
    payload = [item.as_dict() for item in operations]
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return payload


def _apply_guard(environment: str | None) -> None:
    if environment not in {"development", "test"}:
        raise SystemExit(
            "--apply requires --environment development or test; Production is rejected"
        )
    if os.environ.get("TOPICPILOT_ALLOW_MAINTENANCE_APPLY") != "1":
        raise SystemExit("--apply requires TOPICPILOT_ALLOW_MAINTENANCE_APPLY=1")


def _apply_operations(
    database_url: str, operations: tuple[NormalizedOperation, ...]
) -> None:
    """Apply base rows and PROPOSED weights in one transaction; never auto-approve authority."""

    from sqlalchemy import create_engine, text

    engine = create_engine(database_url, pool_pre_ping=True)
    relation_ids: dict[tuple[str, str, str, str], str] = {}
    try:
        with engine.begin() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM public.alembic_version LIMIT 1")
            ).scalar()
            if (
                revision
                and not str(revision).startswith("0046")
                and str(revision) < "0046"
            ):
                raise RuntimeError(
                    f"database migration head is before relation-weight authority: {revision}"
                )
            for operation in operations:
                if operation.record_type == "INSTRUMENT":
                    if operation.operation == "ADD_INSTRUMENT":
                        market_id = connection.execute(
                            text(
                                "SELECT id FROM topicpilot.markets WHERE code=:market"
                            ),
                            {"market": operation.market},
                        ).scalar_one()
                        instrument_id = str(uuid.uuid4())
                        connection.execute(
                            text("""
                            INSERT INTO topicpilot.instruments
                                (id, market_id, instrument_code, name, instrument_type, is_active, valid_from)
                            VALUES (:id, :market_id, :code, :name, :type, :active, :valid_from)
                        """),
                            {
                                "id": instrument_id,
                                "market_id": market_id,
                                "code": operation.stock_code,
                                "name": operation.name,
                                "type": operation.instrument_type or "EQUITY",
                                "active": operation.active
                                if operation.active is not None
                                else True,
                                "valid_from": operation.effective_from,
                            },
                        )
                    else:
                        instrument_id = connection.execute(
                            text("""
                            SELECT i.id FROM topicpilot.instruments i
                            JOIN topicpilot.markets m ON m.id=i.market_id
                            WHERE m.code=:market AND i.instrument_code=:code
                        """),
                            {"market": operation.market, "code": operation.stock_code},
                        ).scalar_one()
                        updates = (
                            ["is_active=:active"]
                            if operation.active is not None
                            else []
                        )
                        params: dict[str, Any] = {
                            "id": instrument_id,
                            "active": operation.active,
                        }
                        if operation.name is not None:
                            updates.append("name=:name")
                            params["name"] = operation.name
                        if operation.instrument_type is not None:
                            updates.append("instrument_type=:instrument_type")
                            params["instrument_type"] = operation.instrument_type
                        if updates:
                            connection.execute(
                                text(
                                    f"UPDATE topicpilot.instruments SET {', '.join(updates)} WHERE id=:id"
                                ),
                                params,
                            )
                    continue
                if operation.record_type != "RELATION":
                    continue
                instrument_id = (
                    operation.instrument_id
                    or connection.execute(
                        text("""
                    SELECT i.id FROM topicpilot.instruments i JOIN topicpilot.markets m ON m.id=i.market_id
                    WHERE m.code=:market AND i.instrument_code=:code
                """),
                        {"market": operation.market, "code": operation.stock_code},
                    ).scalar_one()
                )
                if not operation.topic_id:
                    continue
                if operation.operation == "DEACTIVATE":
                    connection.execute(
                        text("""
                        UPDATE topicpilot.instrument_topic_relations
                        SET valid_to=:valid_to
                        WHERE id = (
                            SELECT r.id FROM topicpilot.instrument_topic_relations r
                            WHERE r.instrument_id=:instrument_id AND r.topic_id=:topic_id
                              AND r.relation_type=:relation_type
                              AND (r.valid_to IS NULL OR r.valid_to >= :valid_to)
                            ORDER BY r.valid_from DESC LIMIT 1
                        )
                    """),
                        {
                            "instrument_id": instrument_id,
                            "topic_id": operation.topic_id,
                            "relation_type": operation.relation_type,
                            "valid_to": operation.effective_from,
                        },
                    )
                    continue
                existing = connection.execute(
                    text("""
                    SELECT r.id FROM topicpilot.instrument_topic_relations r
                    WHERE r.instrument_id=:instrument_id AND r.topic_id=:topic_id
                      AND r.relation_type=:relation_type
                      AND (r.valid_to IS NULL OR r.valid_to >= :effective_from)
                    ORDER BY r.valid_from DESC LIMIT 1
                """),
                    {
                        "instrument_id": instrument_id,
                        "topic_id": operation.topic_id,
                        "relation_type": operation.relation_type,
                        "effective_from": operation.effective_from,
                    },
                ).scalar()
                relation_id = str(existing or uuid.uuid4())
                if existing:
                    connection.execute(
                        text("""
                        UPDATE topicpilot.instrument_topic_relations
                        SET valid_to=NULL, relation_version=:version
                        WHERE id=:id
                    """),
                        {"id": relation_id, "version": "database-maintenance-excel.v1"},
                    )
                else:
                    connection.execute(
                        text("""
                        INSERT INTO topicpilot.instrument_topic_relations
                            (id, instrument_id, topic_id, relation_type, relation_version, valid_from)
                        VALUES (:id, :instrument_id, :topic_id, :relation_type, :version, :valid_from)
                    """),
                        {
                            "id": relation_id,
                            "instrument_id": instrument_id,
                            "topic_id": operation.topic_id,
                            "relation_type": operation.relation_type,
                            "version": "database-maintenance-excel.v1",
                            "valid_from": operation.effective_from,
                        },
                    )
                relation_ids[
                    (
                        operation.market,
                        operation.stock_code,
                        operation.topic_id,
                        operation.relation_type or "",
                    )
                ] = relation_id
                if operation.relation_weight is not None:
                    connection.execute(
                        text("""
                        INSERT INTO topicpilot.relation_weight_authorities
                            (id, relation_id, instrument_id, topic_id, relation_type, weight,
                             approval_state, effective_from, authority_version, source_kind,
                             source_artifact_id, lineage_hash)
                        VALUES (:id, :relation_id, :instrument_id, :topic_id, :relation_type, :weight,
                                'PROPOSED', :effective_from, :authority_version, 'DATABASE_MAINTENANCE_EXCEL',
                                :source_artifact_id, :lineage_hash)
                    """),
                        {
                            "id": str(uuid.uuid4()),
                            "relation_id": relation_id,
                            "instrument_id": instrument_id,
                            "topic_id": operation.topic_id,
                            "relation_type": operation.relation_type,
                            "weight": operation.relation_weight,
                            "effective_from": operation.effective_from,
                            "authority_version": "relation-weight-authority-20260924.v1",
                            "source_artifact_id": f"maintenance-row-{operation.row_number}",
                            "lineage_hash": hashlib.sha256(
                                f"{relation_id}:{operation.relation_weight}".encode()
                            ).hexdigest(),
                        },
                    )
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--snapshot-json", type=Path)
    parser.add_argument(
        "--database-url",
        default=os.environ.get("TOPICPILOT_DATABASE_URL")
        or os.environ.get("DATABASE_URL"),
    )
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--environment")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if sum((args.validate_only, args.dry_run, args.apply)) > 1:
        parser.error("choose only one of --validate-only, --dry-run, or --apply")
    if not any((args.validate_only, args.dry_run, args.apply)):
        args.validate_only = True
    if args.apply:
        _apply_guard(args.environment)
        if not args.database_url:
            raise SystemExit(
                "--apply requires TOPICPILOT_DATABASE_URL or --database-url"
            )

    if not args.snapshot_json:
        raise SystemExit(
            "--snapshot-json is required so validation is deterministic and read-only"
        )
    catalog = catalog_from_snapshot(args.snapshot_json)
    rows = _read_rows(args.input)
    validated, errors = validate_maintenance_rows(rows, catalog=catalog)
    error_payload = [item.as_dict() for item in errors]
    if error_payload:
        print(
            json.dumps(
                {"status": "INVALID", "errors": error_payload},
                ensure_ascii=False,
                indent=2,
            )
        )
        if args.report:
            args.report.write_text(
                json.dumps(
                    {"status": "INVALID", "errors": error_payload},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        raise SystemExit(2)
    operations = build_operations(validated, catalog=catalog)
    operation_payload = _print_operations(operations)
    if args.apply:
        _apply_operations(args.database_url, operations)
        status = "APPLIED_NON_PRODUCTION_PROPOSED_AUTHORITY"
    elif args.dry_run:
        status = "DRY_RUN"
    else:
        status = "VALID"
    summary = {
        "status": status,
        "input_rows": len(rows),
        "validated_rows": len(validated),
        "operation_count": len(operations),
        "operations": operation_payload,
    }
    if args.report:
        args.report.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    if not args.apply:
        print(
            json.dumps(
                {
                    "status": status,
                    "validated_rows": len(validated),
                    "operation_count": len(operations),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()

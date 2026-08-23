from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from topicpilot_api.legacy_import import (
    DEFAULT_MAPPING_POLICY,
    ImportBatch,
    ImportEntity,
    ImportSource,
    validate_dry_run,
)
from topicpilot_api.legacy_import.writer import TransactionalV2Writer
from topicpilot_api.orm.models import (
    Instrument,
    InstrumentTopicRelation,
    Market,
    Topic,
    TopicHierarchy,
)

BASELINE = "0021_phase3_6_001b_import_audit"
TODAY = date(2026, 8, 7).isoformat()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle, delimiter="\t") if any(row.values())]


def source(path: Path, contract: str = "3.6-001B.v1") -> ImportSource:
    return ImportSource(
        artifact_name=path.name,
        artifact_hash=hashlib.sha256(path.read_bytes()).hexdigest(),
        contract_version=contract,
    )


def build_batches(root: Path) -> tuple[list[ImportBatch], dict[str, dict[str, object]]]:
    overview = root / "股票總覽.tsv"
    relation = root / "股票題材關聯.tsv"
    hierarchy = root / "approved_topic_hierarchy.tsv"
    overview_rows = read_tsv(overview)
    relation_rows = read_tsv(relation)
    hierarchy_rows = read_tsv(hierarchy)
    markets = sorted({r["市場代碼"] for r in overview_rows if r["市場代碼"]})
    market_rows = [
        {
            "code": code,
            "name": {"TPE": "Taiwan Stock Exchange", "TWO": "Taipei Exchange"}.get(code, code),
            "timezone": "Asia/Taipei",
            "exchange": code,
        }
        for code in markets
    ]
    instruments = [
        {"market": r["市場代碼"], "code": r["股號"], "name": r["名稱"], "currency": "TWD"}
        for r in overview_rows
        if r["市場代碼"] and r["股號"]
    ]
    topic_names = sorted(
        {r["主大族群"] for r in hierarchy_rows} | {r["細題材"] for r in hierarchy_rows}
    )
    topics = [{"slug": n, "name": n, "enabled": True} for n in topic_names if n]
    topic_hierarchy = [
        {
            "parent": r["主大族群"],
            "child": r["細題材"],
            "relationship_type": "PARENT",
            "hierarchy_version": "V1",
            "valid_from": TODAY,
            "valid_to": None,
            "display_order": i + 1,
        }
        for i, r in enumerate(hierarchy_rows)
        if r["主大族群"] and r["細題材"] and r["主大族群"] != r["細題材"]
    ]
    relations = [
        {
            "market": "TPE"
            if r["股號"] in {x["股號"] for x in overview_rows if x["市場代碼"] == "TPE"}
            else "TWO",
            "instrument": r["股號"],
            "topic": r["細題材"],
            "relation_type": "PRIMARY" if r["題材角色"] in {"核心", "主題"} else "SECONDARY",
            "valid_from": (r["來源更新時間"] or TODAY)[:10],
        }
        for r in relation_rows
        if r["股號"] and r["細題材"]
    ]
    batches = [
        ImportBatch(ImportEntity.MARKET, tuple(market_rows), (), source(overview)),
        ImportBatch(ImportEntity.INSTRUMENT, tuple(instruments), (), source(overview)),
        ImportBatch(ImportEntity.TOPIC, tuple(topics), (), source(hierarchy)),
        ImportBatch(ImportEntity.TOPIC_HIERARCHY, tuple(topic_hierarchy), (), source(hierarchy)),
        ImportBatch(ImportEntity.INSTRUMENT_TOPIC, tuple(relations), (), source(relation)),
    ]
    artifacts = {
        p.name: {
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "logical_rows": len(read_tsv(p)),
        }
        for p in (overview, hierarchy, relation, root / "族群資料庫.tsv")
    }
    return batches, artifacts


def counts(session: Session) -> dict[str, int]:
    return {
        name: session.scalar(select(model).count())
        if False
        else session.execute(text(f"select count(*) from topicpilot.{table}")).scalar_one()
        for name, table, model in [
            ("markets", "markets", Market),
            ("instruments", "instruments", Instrument),
            ("topics", "topics", Topic),
            ("topic_hierarchy", "topic_hierarchy", TopicHierarchy),
            ("instrument_topic_relations", "instrument_topic_relations", InstrumentTopicRelation),
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    batches, artifacts = build_batches(args.input)
    report = validate_dry_run(
        batches,
        DEFAULT_MAPPING_POLICY,
        known_markets={"TPE", "TWO"},
        known_topics={r["slug"] for r in batches[2].records},
    )
    result = {
        "artifacts": artifacts,
        "entities": {b.entity.value: len(b.records) for b in batches},
        "dry_run": report.to_dict(),
        "critical_blockers": sum(i["severity"] == "ERROR" for i in report.to_dict()["issues"]),
    }
    if args.apply and result["critical_blockers"] == 0:
        engine = create_engine(args.database_url)
        with Session(engine) as session:
            run_id = TransactionalV2Writer(session, BASELINE).apply_all(
                batches, DEFAULT_MAPPING_POLICY, export_id="topicpilot-v1-20260807"
            )
            result["run_id"] = str(run_id)
            result["domain_counts"] = counts(session)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["critical_blockers"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Validate the Phase 1 source bundle without writing to PostgreSQL.

This report is intentionally source-only. It proves that the versioned bundle can be
used as the first migration input, while keeping formal Google Sheets data out of the
public repository.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from topicpilot_api.bundle import LoadedBundle, load_bundle


def build_report(bundle: LoadedBundle) -> dict[str, Any]:
    data = bundle.data
    stocks = data["stocks"]
    topics = data["topics"]
    hierarchy = data["topicHierarchy"]
    relations = data["stockTopicRelations"]
    stock_codes = {row["code"] for row in stocks}
    topic_slugs = {row["slug"] for row in topics}

    relation_keys = [
        (row["stockCode"], row["topicSlug"], row["relationType"])
        for row in relations
    ]
    hierarchy_keys = [(row["parentSlug"], row["childSlug"]) for row in hierarchy]
    relation_stock_refs = sorted({key[0] for key in relation_keys} - stock_codes)
    relation_topic_refs = sorted({key[1] for key in relation_keys} - topic_slugs)
    hierarchy_refs = sorted(
        {slug for key in hierarchy_keys for slug in key} - topic_slugs
    )

    checks = {
        "duplicateStockCodes": len({row["code"] for row in stocks}) != len(stocks),
        "duplicateTopicSlugs": len({row["slug"] for row in topics}) != len(topics),
        "duplicateRelations": len(set(relation_keys)) != len(relation_keys),
        "duplicateHierarchyEdges": len(set(hierarchy_keys)) != len(hierarchy_keys),
        "unresolvedRelationStockRefs": relation_stock_refs,
        "unresolvedRelationTopicRefs": relation_topic_refs,
        "unresolvedHierarchyTopicRefs": hierarchy_refs,
        "leadingZeroCodesPreserved": all(
            isinstance(row["code"], str) and row["code"] == row["code"].strip()
            for row in stocks
        ),
        "formalDataImported": False,
        "newsEntitiesInV1Contract": False,
    }
    checks["allForeignKeysValid"] = not any(
        (
            checks["duplicateStockCodes"],
            checks["duplicateTopicSlugs"],
            checks["duplicateRelations"],
            checks["duplicateHierarchyEdges"],
            relation_stock_refs,
            relation_topic_refs,
            hierarchy_refs,
        )
    )
    return {
        "contractVersion": bundle.manifest["contractVersion"],
        "bundleVersion": bundle.manifest["bundleVersion"],
        "source": {
            "kind": bundle.manifest["source"]["kind"],
            "classification": bundle.manifest["source"]["classification"],
            "formalDataImported": False,
        },
        "counts": bundle.row_counts,
        "phase1": {
            "coreMasterData": "READY_FOR_SYNTHETIC_IMPORT",
            "newsEntities": "SCHEMA_ONLY_UNTIL_CONTRACT_EXTENSION",
        },
        "checks": checks,
        "bundleHash": bundle.bundle_hash,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = build_report(load_bundle(args.bundle))
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["checks"]["allForeignKeysValid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

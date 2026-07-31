from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from conftest import DEMO_BUNDLE, SCHEMA_PATH

from topicpilot_api.bundle import (
    BundleParseError,
    BundleReferenceError,
    BundleSchemaError,
    BundleSemanticError,
    load_bundle,
    load_private_snapshot_json,
)


def copy_bundle(tmp_path: Path) -> Path:
    target = tmp_path / "bundle"
    shutil.copytree(DEMO_BUNDLE, target)
    return target


def update_json(path: Path, transform) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    transform(payload)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_demo_bundle_matches_contract_and_preserves_nulls() -> None:
    bundle = load_bundle(DEMO_BUNDLE, SCHEMA_PATH)

    assert bundle.manifest["contractVersion"] == "enterprise_bundle.v1"
    assert bundle.manifest["source"]["classification"] == "PUBLIC_SYNTHETIC"
    assert bundle.row_counts["stocks"] == 4
    assert bundle.row_counts["topicSnapshots"] == 42
    assert len(bundle.bundle_hash) == 64

    null_stock = next(
        row
        for row in bundle.data["dailySnapshots"]["stockSnapshots"]
        if row["stockCode"] == "DEMO-D4" and row["dataDate"] == "2026-07-31"
    )
    assert null_stock["price"] is None
    assert null_stock["volume"] is None


def test_bundle_rejects_unknown_references(tmp_path: Path) -> None:
    bundle_dir = copy_bundle(tmp_path)
    update_json(
        bundle_dir / "stock_topic_relations.json",
        lambda payload: payload[0].update({"topicSlug": "not-in-topic-dimension"}),
    )

    with pytest.raises(BundleReferenceError, match="unresolved references"):
        load_bundle(bundle_dir, SCHEMA_PATH)


def test_public_bundle_rejects_private_keys_inside_metadata(tmp_path: Path) -> None:
    bundle_dir = copy_bundle(tmp_path)
    update_json(
        bundle_dir / "stocks.json",
        lambda payload: payload[0]["metadata"].update({"holdings": ["PRIVATE"]}),
    )

    with pytest.raises(BundleSemanticError, match="forbidden keys"):
        load_bundle(bundle_dir, SCHEMA_PATH)


def test_bundle_rejects_invalid_utf8_without_repair(tmp_path: Path) -> None:
    bundle_dir = copy_bundle(tmp_path)
    (bundle_dir / "stocks.json").write_bytes(b"[\xff]")

    with pytest.raises(BundleParseError, match="not valid UTF-8"):
        load_bundle(bundle_dir, SCHEMA_PATH)


def test_private_snapshot_guard_rejects_incomplete_or_wrong_containers(tmp_path: Path) -> None:
    incomplete = tmp_path / "incomplete.json"
    incomplete.write_text("{}", encoding="utf-8")
    with pytest.raises(BundleSchemaError, match="missing roots"):
        load_private_snapshot_json(incomplete)

    wrong = tmp_path / "wrong.json"
    wrong.write_text(
        json.dumps(
            {
                "snapshotVersion": "x",
                "generatedAt": "2026-07-31T08:00:00Z",
                "dataDate": "2026-07-31",
                "quoteMeta": {},
                "marketSession": {},
                "topics": {},
                "stocks": [],
                "strategyRegistry": {},
                "strategyCandidates": [],
                "strategyPerformance": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(BundleSchemaError, match="incompatible stocks/topics"):
        load_private_snapshot_json(wrong)

from __future__ import annotations

import json
from pathlib import Path

from topicpilot_api.reference_data import load_bundle
from topicpilot_api.topic_master_v1 import (
    canonical_sync_plan,
    load_master,
    validate_master,
)

ROOT = Path(__file__).parents[3]
OWNER_DIR = ROOT / "config/topic_master_v1"
TOPIC_SOURCE = OWNER_DIR / "topics.csv"
MEMBERSHIP_SOURCE = OWNER_DIR / "instrument_topic_memberships.csv"
INSTRUMENT_SOURCE = OWNER_DIR / "instruments.csv"
BUNDLE_SOURCE = ROOT / "services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1"
SNAPSHOT_SOURCE = OWNER_DIR / "generated/canonical_relations.snapshot.json"


def _master():
    return load_master(TOPIC_SOURCE, MEMBERSHIP_SOURCE, INSTRUMENT_SOURCE)


def test_owner_instrument_identity_chain_is_closed_and_allows_no_topic():
    master = _master()
    report = validate_master(master)
    instrument_ids = {(row["market_code"], row["instrument_code"]) for row in master.instruments}
    membership_ids = {(row["market_code"], row["instrument_code"]) for row in master.memberships}

    assert report.valid
    assert len(instrument_ids) == 639
    assert len(membership_ids) == 522
    assert membership_ids <= instrument_ids
    assert len(instrument_ids - membership_ids) == 117


def test_derived_reference_bundle_has_no_identity_drift():
    master = _master()
    bundle = load_bundle(BUNDLE_SOURCE)
    owner_ids = {
        (row["market_code"], row["instrument_code"], row["instrument_name"])
        for row in master.instruments
    }
    bundle_ids = {
        (row["market_code"], row["instrument_code"], row["name"])
        for row in bundle.instruments
    }
    assert bundle_ids == owner_ids


def test_canonical_sync_second_run_is_noop_and_preserves_order():
    master = _master()
    report = validate_master(master)
    snapshot = json.loads(SNAPSHOT_SOURCE.read_text(encoding="utf-8"))
    plan = canonical_sync_plan(master, report, existing_snapshot=snapshot)

    assert plan["operation"] == "NOOP"
    assert plan["operations"] == ["SYNC_INSTRUMENTS", "SYNC_TOPICS", "SYNC_RELATIONS"]
    assert plan["canonical_instrument_count"] == 639
    assert plan["canonical_topic_count"] == 135
    assert plan["canonical_relation_count"] == 5

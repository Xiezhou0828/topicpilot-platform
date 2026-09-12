from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from topicpilot_api.topic_master_v1 import (
    CANONICAL_ROLE_MAP,
    MEMBERSHIP_FIELDS,
    TOPIC_FIELDS,
    MasterData,
    canonical_sync_plan,
    load_master,
    validate_master,
)

ROOT = Path(__file__).parents[3]
TOPIC_SOURCE = ROOT / "config/topic_master_v1/topics.csv"
MEMBERSHIP_SOURCE = ROOT / "config/topic_master_v1/instrument_topic_memberships.csv"
INSTRUMENT_SOURCE = (
    ROOT / "config/topic_master_v1/instruments.csv"
)


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _master(tmp_path: Path, *, topic_rows=None, membership_rows=None) -> MasterData:
    topics = topic_rows or [
        {
            "topic_key": "MLCC",
            "topic_name": "MLCC",
            "parent_topic": "PASSIVE",
            "enabled": "TRUE",
            "description": "",
            "governance_state": "OWNER_APPROVED_CURRENT",
        },
        {
            "topic_key": "PASSIVE",
            "topic_name": "Passive",
            "parent_topic": "",
            "enabled": "TRUE",
            "description": "",
            "governance_state": "OWNER_APPROVED_CURRENT",
        },
    ]
    memberships = membership_rows or [
        {
            "market_code": "TPE",
            "instrument_code": "2327",
            "instrument_name": "國巨",
            "topic_key": "MLCC",
            "topic_relation_type": "SECONDARY",
            "structural_role": "CORE",
            "topic_weight": "1.4",
            "enabled": "TRUE",
            "review_state": "APPROVED",
            "valid_from": "2026-08-24",
            "valid_to": "",
            "source_reference": "test",
        },
        {
            "market_code": "TPE",
            "instrument_code": "2327",
            "instrument_name": "國巨",
            "topic_key": "PASSIVE",
            "topic_relation_type": "PRIMARY",
            "structural_role": "LEAD",
            "topic_weight": "0.8",
            "enabled": "TRUE",
            "review_state": "APPROVED",
            "valid_from": "2026-08-24",
            "valid_to": "",
            "source_reference": "test",
        },
    ]
    topic_path = tmp_path / "topics.csv"
    membership_path = tmp_path / "memberships.csv"
    _write_csv(topic_path, TOPIC_FIELDS, topics)
    _write_csv(membership_path, MEMBERSHIP_FIELDS, memberships)
    return load_master(topic_path, membership_path)


def test_topic_and_membership_master_parse_with_reference_universe():
    master = load_master(TOPIC_SOURCE, MEMBERSHIP_SOURCE, INSTRUMENT_SOURCE)
    report = validate_master(master)
    assert report.valid
    assert report.instrument_count == 639
    assert report.topic_count == 135
    assert report.membership_count == 1214
    assert report.membership_unique_instrument_count == 522


def test_mlcc_proof_preserves_six_current_roles_and_independent_relation_type():
    master = load_master(TOPIC_SOURCE, MEMBERSHIP_SOURCE, INSTRUMENT_SOURCE)
    rows = {
        row["instrument_code"]: row
        for row in master.memberships
        if row["topic_key"] == "MLCC" and row["structural_role"]
    }
    assert {
        code: rows[code]["structural_role"]
        for code in ("2327", "8043", "2492", "3026", "6173", "4716")
    } == {
        "2327": "LEAD",
        "8043": "LEAD",
        "2492": "LEAD",
        "3026": "CORE",
        "6173": "CORE",
        "4716": "RELATED",
    }
    assert rows["2327"]["topic_relation_type"] == "PRIMARY"
    assert rows["2327"]["structural_role"] == "LEAD"
    assert rows["8043"]["topic_relation_type"] == "PRIMARY"
    assert rows["8043"]["structural_role"] == "LEAD"


def test_duplicate_topic_is_rejected(tmp_path):
    master = _master(
        tmp_path,
        topic_rows=[
            {
                "topic_key": "MLCC",
                "topic_name": "MLCC",
                "parent_topic": "",
                "enabled": "TRUE",
                "description": "",
                "governance_state": "X",
            },
            {
                "topic_key": "MLCC",
                "topic_name": "MLCC duplicate",
                "parent_topic": "",
                "enabled": "TRUE",
                "description": "",
                "governance_state": "X",
            },
        ],
    )
    report = validate_master(master, known_instruments={("TPE", "2327")})
    assert any(issue.code == "DUPLICATE_TOPIC" for issue in report.errors)


def test_duplicate_membership_is_rejected(tmp_path):
    base = {
        "market_code": "TPE",
        "instrument_code": "2327",
        "instrument_name": "國巨",
        "topic_key": "MLCC",
        "topic_relation_type": "PRIMARY",
        "structural_role": "CORE",
        "topic_weight": "1",
        "enabled": "TRUE",
        "review_state": "APPROVED",
        "valid_from": "2026-08-24",
        "valid_to": "",
        "source_reference": "test",
    }
    master = _master(tmp_path, membership_rows=[base, dict(base)])
    report = validate_master(master, known_instruments={("TPE", "2327")})
    assert any(issue.code == "DUPLICATE_MEMBERSHIP" for issue in report.errors)


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("instrument_code", "9999", "UNKNOWN_INSTRUMENT"),
        ("topic_key", "UNKNOWN", "UNKNOWN_TOPIC"),
        ("structural_role", "LEADER", "INVALID_STRUCTURAL_ROLE"),
        ("topic_relation_type", "RELATED", "INVALID_RELATION_TYPE"),
    ],
)
def test_invalid_membership_values_fail_closed(tmp_path, field, value, code):
    row = dict(_master(tmp_path).memberships[0])
    row[field] = value
    master = _master(tmp_path, membership_rows=[row])
    report = validate_master(master, known_instruments={("TPE", "2327")})
    assert any(issue.code == code for issue in report.errors)


def test_multi_topic_and_primary_role_independence_are_legal(tmp_path):
    master = _master(tmp_path)
    report = validate_master(master, known_instruments={("TPE", "2327")})
    assert report.valid
    rows = [row for row in master.memberships if row["instrument_code"] == "2327"]
    assert {row["topic_key"] for row in rows} == {"MLCC", "PASSIVE"}
    assert rows[0]["topic_relation_type"] == "SECONDARY" and rows[0]["structural_role"] == "CORE"


def test_related_only_is_warning_not_hard_failure(tmp_path):
    row = dict(_master(tmp_path).memberships[0])
    row["structural_role"] = "RELATED"
    master = _master(tmp_path, membership_rows=[row])
    report = validate_master(master, known_instruments={("TPE", "2327")})
    assert report.valid
    assert any(issue.code == "ONLY_RELATED" for issue in report.warnings)


def test_deterministic_order_and_hash(tmp_path):
    first = _master(tmp_path / "one")
    second = _master(
        tmp_path / "two",
        topic_rows=list(reversed(first.topics)),
        membership_rows=list(reversed(first.memberships)),
    )
    assert first.source_hash == second.source_hash
    assert first.topics == second.topics
    assert first.memberships == second.memberships


def test_sync_dry_run_is_deterministic_and_maps_owner_lead_explicitly(tmp_path):
    master = _master(tmp_path)
    report = validate_master(master, known_instruments={("TPE", "2327")})
    first = canonical_sync_plan(master, report)
    second = canonical_sync_plan(master, report)
    assert first == second
    assert first["status"] == "DRY_RUN_PASS"
    assert first["operation"] == "CREATE_SNAPSHOT"
    assert (
        first["rows"][1]["structural_role"] == CANONICAL_ROLE_MAP["LEAD"]
        or first["rows"][0]["structural_role"] == CANONICAL_ROLE_MAP["LEAD"]
    )


def test_drift_detection_changes_operation(tmp_path):
    master = _master(tmp_path)
    report = validate_master(master, known_instruments={("TPE", "2327")})
    stale = {"owner_master_hash": "stale"}
    plan = canonical_sync_plan(master, report, existing_snapshot=stale)
    assert plan["operation"] == "REPLACE_SNAPSHOT"


def test_invalid_master_cannot_sync(tmp_path):
    row = dict(_master(tmp_path).memberships[0])
    row["structural_role"] = "BAD"
    master = _master(tmp_path, membership_rows=[row])
    report = validate_master(master, known_instruments={("TPE", "2327")})
    plan = canonical_sync_plan(master, report)
    assert plan["status"] == "REJECTED"


def test_research_snapshot_provenance_is_explicit_and_traceable():
    master = load_master(TOPIC_SOURCE, MEMBERSHIP_SOURCE, INSTRUMENT_SOURCE)
    research_rows = [
        row
        for row in master.memberships
        if row["source_reference"].startswith("fixtures/research/topic_universe_mapping")
    ]
    assert research_rows
    assert all(
        row["source_reference"].startswith("fixtures/research/topic_universe_mapping")
        for row in research_rows
    )
    snapshot = json.loads(
        (ROOT / "config/topic_master_v1/generated/canonical_relations.snapshot.json").read_text(
            encoding="utf-8"
        )
    )
    assert snapshot["authority_class"] == "DERIVED_FROM_OWNER_MASTER"


def test_current_instrument_master_supports_no_topic_and_preserves_sync_order():
    master = load_master(TOPIC_SOURCE, MEMBERSHIP_SOURCE, INSTRUMENT_SOURCE)
    report = validate_master(master)
    assert report.valid
    plan = canonical_sync_plan(master, report)
    assert plan["operations"] == ["SYNC_INSTRUMENTS", "SYNC_TOPICS", "SYNC_RELATIONS"]
    assert len(plan["instrument_rows"]) == 639
    assert len(plan["topic_rows"]) == 135
    assert plan["canonical_relation_count"] == 5
    assert plan["canonical_instrument_count"] > report.membership_unique_instrument_count


def test_frozen_research_document_remains_a_snapshot_not_authority():
    research_doc = (ROOT / "docs/research/topic-universe-mapping.v1.md").read_text(encoding="utf-8")
    assert "RESEARCH DATASET / NOT APPROVED" in research_doc
    assert "topic-universe-mapping.v1" in research_doc


def test_lifecycle_policy_contract_is_not_changed_by_master_module():
    from topicpilot_api.topic_lifecycle_v1 import LIFECYCLE_POLICY_VERSION, LifecyclePolicy

    policy = LifecyclePolicy()
    assert LIFECYCLE_POLICY_VERSION == "topic-lifecycle-policy.v1"
    assert policy.lead_core_authority_weight == 0.70
    assert policy.related_authority_weight == 0.30

from types import SimpleNamespace
from uuid import uuid4

from topicpilot_api import lifecycle_formal_publication
from topicpilot_api.formal_strength_publication import _gate as strength_gate


def _snapshot() -> SimpleNamespace:
    return SimpleNamespace(
        snapshot_identity="formal:topic:2026-10-12:hash",
        membership_snapshot_id="membership:hash",
        membership_snapshot_hash="membership-hash",
        relation_version="relation-v1",
        source_artifact_hash="artifact-hash",
        lineage_hash="lineage-hash",
        correction_sequence=0,
        data_status="COMPLETE",
        stock_count=2,
        observed_stock_count=2,
    )


def _facts() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            instrument_id=uuid4(),
            fact_hash="observed-hash",
            fact_state="OBSERVED",
            change_pct=1.0,
            structural_role="CORE",
            role_source="owner",
            raw_fact_payload={"dimensionEligibility": {"DAILY_RETURN": {"status": "READY"}}},
        ),
        SimpleNamespace(
            instrument_id=uuid4(),
            fact_hash="missing-hash",
            fact_state="UNKNOWN",
            change_pct=None,
            structural_role="CORE",
            role_source="owner",
            raw_fact_payload={},
        ),
    ]


def test_strength_gate_requires_explicit_bounded_budget_for_partial_members():
    snapshot = _snapshot()
    facts = _facts()

    assert not strength_gate(snapshot, facts).passed
    assert strength_gate(snapshot, facts, allowed_non_observed_members=1).passed
    assert not strength_gate(snapshot, facts, allowed_non_observed_members=0).passed


def test_lifecycle_gate_requires_explicit_bounded_budget_for_partial_members(monkeypatch):
    monkeypatch.setattr(
        lifecycle_formal_publication,
        "_formal_snapshot_lineage",
        lambda snapshot, facts: ({"snapshotIdentity": snapshot.snapshot_identity}, None),
    )
    snapshot = _snapshot()
    facts = _facts()

    assert not lifecycle_formal_publication._formal_gate(snapshot, facts).passed
    assert lifecycle_formal_publication._formal_gate(
        snapshot,
        facts,
        allowed_non_observed_members=1,
    ).passed

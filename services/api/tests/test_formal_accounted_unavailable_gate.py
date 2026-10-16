from types import SimpleNamespace
from uuid import uuid4

from topicpilot_api.formal_eligibility import (
    DimensionStatus,
    is_authorized_accounted_unavailable_fact,
)
from topicpilot_api.formal_strength_publication import _gate as strength_gate
from topicpilot_api.lifecycle_formal_publication import _formal_gate as lifecycle_gate
from topicpilot_api.previous_close_authority import (
    AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE,
)


def _fact(*, state: str, authorized_unavailable: bool = False):
    return SimpleNamespace(
        instrument_id=uuid4(),
        fact_identity="fact-identity",
        fact_hash="fact-hash",
        fact_state=state,
        change_pct=None if state != "OBSERVED" else 1.0,
        structural_role="CORE",
        role_source="FORMAL_ROLE_AUTHORITY",
        raw_fact_payload=(
            {
                "dimensionEligibility": {
                    "DAILY_RETURN": {
                        "status": DimensionStatus.ACCOUNTED_UNAVAILABLE.value,
                        "reasonCode": AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE,
                    }
                }
            }
            if authorized_unavailable
            else {}
        ),
    )


def _snapshot(*, observed_stock_count: int = 1):
    return SimpleNamespace(
        id=uuid4(),
        snapshot_identity="formal:topic:2026-10-15:artifact",
        membership_snapshot_id="membership:2026-10-15",
        membership_snapshot_hash="membership-hash",
        relation_version="relations:v1",
        source_artifact_id="artifact:2026-10-15",
        source_artifact_hash="artifact-hash",
        lineage_hash="lineage-hash",
        correction_sequence=0,
        supersedes_snapshot_id=None,
        superseded_by_snapshot_id=None,
        data_status="COMPLETE",
        stock_count=2,
        observed_stock_count=observed_stock_count,
    )


def test_authorized_no_trade_fact_is_the_only_accounted_unavailable_exception():
    allowed = _fact(state="NO_TRADE", authorized_unavailable=True)
    unknown = _fact(state="UNKNOWN", authorized_unavailable=True)

    assert is_authorized_accounted_unavailable_fact(allowed) is True
    assert is_authorized_accounted_unavailable_fact(unknown) is False


def test_formal_strength_and_lifecycle_gates_accept_authorized_no_trade_member():
    snapshot = _snapshot()
    facts = [_fact(state="OBSERVED"), _fact(state="NO_TRADE", authorized_unavailable=True)]

    assert strength_gate(snapshot, facts).passed is True
    assert lifecycle_gate(snapshot, facts).passed is True


def test_formal_gates_still_reject_unexplained_unknown_member():
    snapshot = _snapshot()
    facts = [_fact(state="OBSERVED"), _fact(state="UNKNOWN")]

    assert strength_gate(snapshot, facts).passed is False
    assert lifecycle_gate(snapshot, facts).passed is False

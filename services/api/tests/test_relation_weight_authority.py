from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from topicpilot_api.orm import RelationWeightAuthority
from topicpilot_api.relation_weight_authority import (
    APPROVAL_PROPOSED,
    PRIMARY_DEFAULT,
    RelationIdentity,
    RelationWeightApprovalError,
    RelationWeightError,
    RelationWeightIdentityError,
    RelationWeightProposal,
    RelationWeightRangeError,
    RelationWeightReadModel,
    apply_owner_approved_proposal,
    assert_formal_weight,
    generate_proposals,
    parse_weight,
)


def _current():
    return [
        {"market": "TPE", "symbol": "5371", "topic": "topic-a", "relation_type": "PRIMARY"},
        {"market": "TPE", "symbol": "3718", "topic": "topic-a", "relation_type": "PRIMARY"},
        {"market": "TWO", "symbol": "6806", "topic": "topic-b", "relation_type": "SECONDARY"},
    ]


def _evidence():
    return [
        {
            "market": "TPE",
            "symbol": "5371",
            "topic": "topic-a",
            "relation_type": "PRIMARY",
            "recovery_status": "RECOVERABLE_WITH_OWNER_CONFIRMATION",
            "historical_weight": "1.25",
        },
        {
            "market": "TPE",
            "symbol": "3718",
            "topic": "topic-a",
            "relation_type": "PRIMARY",
            "recovery_status": "RELATIONS_WITH_AMBIGUOUS_SOURCE",
            "historical_weight": "9.99",
        },
        {
            "market": "TWO",
            "symbol": "6806",
            "topic": "topic-b",
            "relation_type": "SECONDARY",
            "recovery_status": "NO_HISTORICAL_WEIGHT",
        },
    ]


@pytest.mark.parametrize("value", ["0.5", "2.0"])
def test_primary_range_accepts_boundaries(value):
    assert parse_weight(value, relation_type="PRIMARY") == Decimal(value)


@pytest.mark.parametrize("value", ["0.49", "2.01", "", "NaN"])
def test_primary_range_rejects_invalid_values(value):
    with pytest.raises(RelationWeightRangeError):
        parse_weight(value, relation_type="PRIMARY")


@pytest.mark.parametrize("value", ["0.3", "0.8"])
def test_secondary_range_accepts_boundaries(value):
    assert parse_weight(value, relation_type="SECONDARY") == Decimal(value)


@pytest.mark.parametrize("value", ["0.29", "0.81"])
def test_secondary_range_rejects_invalid_values(value):
    with pytest.raises(RelationWeightRangeError):
        parse_weight(value, relation_type="SECONDARY")


def test_proposal_generation_is_exact_and_defaults_are_not_history():
    result = generate_proposals(_current(), _evidence())

    assert result.current_relation_count == 3
    assert result.primary_relation_count == 2
    assert result.secondary_relation_count == 1
    assert result.legacy_recovered_count == 1
    assert result.invalid_legacy_defaulted_count == 0
    assert result.ambiguous_history_count == 1
    assert result.missing_history_count == 1
    assert all(proposal.approval_state == APPROVAL_PROPOSED for proposal in result.proposals)
    by_symbol = {proposal.identity.instrument: proposal for proposal in result.proposals}
    assert by_symbol["3718"].weight == PRIMARY_DEFAULT
    assert by_symbol["3718"].source_kind == "DEFAULT_INITIALIZATION"
    assert "DO_NOT_RECONSTRUCT" in by_symbol["3718"].proposal_reason
    assert by_symbol["6806"].weight == Decimal("0.5")
    assert all(proposal.effective_from == date(2026, 9, 24) for proposal in result.proposals)


def test_invalid_recoverable_legacy_value_is_preserved_but_defaulted():
    current = [
        {"market": "TPE", "symbol": "2301", "topic": "topic-a", "relation_type": "SECONDARY"}
    ]
    evidence = [
        {
            **current[0],
            "recovery_status": "RECOVERABLE_WITH_OWNER_CONFIRMATION",
            "historical_weight": "1.0",
            "historical_source": "legacy.tsv",
            "source_rows": "12",
        }
    ]
    result = generate_proposals(current, evidence)
    proposal = result.proposals[0]

    assert result.legacy_recovered_count == 0
    assert result.invalid_legacy_defaulted_count == 1
    assert proposal.weight == Decimal("0.5")
    assert proposal.legacy_original_value == Decimal("1.0")
    assert proposal.approval_state == APPROVAL_PROPOSED
    assert proposal.source_kind == "INVALID_LEGACY_DEFAULT_INITIALIZATION"
    assert "LEGACY_VALUE_INVALID_UNDER_CURRENT_POLICY" in proposal.proposal_reason
    assert proposal.legacy_recovery_evidence["historicalSource"] == "legacy.tsv"


def test_exact_identity_resolution_rejects_missing_or_extra_rows():
    evidence = _evidence()[:-1]
    with pytest.raises(RelationWeightIdentityError, match="unresolved=1"):
        generate_proposals(_current(), evidence)


def test_successor_identities_never_inherit_weight():
    result = generate_proposals(_current(), _evidence())
    by_symbol = {p.identity.instrument: p for p in result.proposals}
    assert by_symbol["5371"].weight == Decimal("1.25")
    assert by_symbol["3718"].weight == PRIMARY_DEFAULT
    assert by_symbol["5371"].identity != by_symbol["3718"].identity


def _proposal(state: str) -> RelationWeightProposal:
    return RelationWeightProposal(
        id=uuid4(),
        identity=RelationIdentity("TPE", "2301", "topic-a", "PRIMARY"),
        relation_id="relation-1",
        instrument_id="instrument-1",
        topic_id="topic-1",
        weight=Decimal("1.0"),
        legacy_original_value=None,
        legacy_recovery_evidence=None,
        approval_state=state,
        effective_from=date(2026, 9, 24),
        effective_to=None,
        authority_version="relation-weight-authority-20260924.v1",
        approval_reference="owner-approval" if state == "APPROVED" else None,
        source_kind="DEFAULT_INITIALIZATION",
        source_artifact_id="artifact-1",
        source_artifact_hash="a" * 64,
        source_location=None,
        proposal_reason="test",
        correction_sequence=0,
        supersedes_id=None,
        lineage_hash="b" * 64,
    )


def test_proposed_is_not_formal_and_approved_is_formal():
    proposed = RelationWeightReadModel("relation-1", _proposal("PROPOSED"), None)
    assert proposed.formal_weight is None
    with pytest.raises(RelationWeightApprovalError, match="unavailable"):
        assert_formal_weight(proposed.formal_weight, approval_state="PROPOSED")

    approved = _proposal("APPROVED")
    formal = RelationWeightReadModel("relation-1", None, approved)
    assert formal.formal_weight == Decimal("1.0")
    assert assert_formal_weight(formal.formal_weight, approval_state="APPROVED") == Decimal("1.0")


def test_effective_date_cannot_be_backdated():
    with pytest.raises(RelationWeightError, match="backdated"):
        generate_proposals(_current(), _evidence(), effective_from=date(2026, 9, 23))


def test_owner_apply_boundary_is_disabled_in_001d():
    with pytest.raises(RelationWeightApprovalError, match="disabled"):
        apply_owner_approved_proposal(
            None,  # type: ignore[arg-type]
            "proposal-1",
            approval_reference="owner-review-1",
        )


def test_authority_model_is_separate_from_relation_and_score_models():
    columns = {column.name for column in RelationWeightAuthority.__table__.columns}
    assert {
        "relation_id",
        "instrument_id",
        "topic_id",
        "relation_type",
        "weight",
        "legacy_original_value",
        "legacy_recovery_evidence",
        "approval_state",
        "effective_from",
        "effective_to",
        "authority_version",
        "approval_reference",
        "source_kind",
        "source_artifact_id",
        "source_artifact_hash",
        "proposal_reason",
        "correction_sequence",
        "supersedes_id",
        "lineage_hash",
        "created_at",
        "updated_at",
    } <= columns

from __future__ import annotations

from datetime import date, timedelta

import pytest

from topicpilot_api.structural_role_read_boundary import (
    StructuralRoleAuthorityCandidate,
    StructuralRoleAuthorityReadError,
    resolve_current_structural_role_authority,
)

AS_OF = date(2026, 9, 27)


def make_row(
    relation_type: str,
    structural_role: str | None,
    *,
    relation_id: str = "relation-1",
    instrument_id: str = "instrument-1",
    topic_id: str = "topic-1",
    **overrides: object,
) -> StructuralRoleAuthorityCandidate:
    values: dict[str, object] = {
        "relation_id": relation_id,
        "instrument_id": instrument_id,
        "instrument_code": "1101",
        "market_code": "TPE",
        "topic_id": topic_id,
        "topic_slug": "topic-1",
        "relation_type": relation_type,
        "structural_role": structural_role,
        "approval_state": "APPROVED",
        "authority_version": "structural-role-authority-test.v1",
        "effective_from": date(2026, 1, 1),
        "effective_to": None,
        "source_artifact_id": "artifact:test",
        "source_artifact_hash": "hash:test",
        "approval_reference": "OWNER_TEST",
        "correction_sequence": 0,
        "supersedes_authority_id": None,
        "superseded_by_authority_id": None,
        "lineage_hash": "lineage:test",
    }
    values.update(overrides)
    return StructuralRoleAuthorityCandidate(**values)


@pytest.mark.parametrize(
    ("relation_type", "structural_role"),
    [
        ("PRIMARY", "REPRESENTATIVE"),
        ("PRIMARY", "CORE"),
        ("SECONDARY", "REPRESENTATIVE"),
        ("SECONDARY", "CORE"),
        ("SECONDARY", "RELATED"),
    ],
)
def test_current_authority_preserves_independent_relation_type_and_role(
    relation_type: str, structural_role: str
) -> None:
    resolved = resolve_current_structural_role_authority(
        (make_row(relation_type, structural_role),), AS_OF
    )
    assert [(row.relation_type, row.structural_role) for row in resolved] == [
        (relation_type, structural_role)
    ]


def test_topic_role_is_not_a_structural_role_fallback() -> None:
    row = make_row("SECONDARY", None)
    with pytest.raises(StructuralRoleAuthorityReadError, match="INVALID_ROLE"):
        resolve_current_structural_role_authority((row,), AS_OF)


def test_duplicate_active_authority_fails_closed() -> None:
    rows = (
        make_row("PRIMARY", "REPRESENTATIVE", relation_id="relation-1"),
        make_row("PRIMARY", "CORE", relation_id="relation-2"),
    )
    with pytest.raises(StructuralRoleAuthorityReadError, match="CONFLICT"):
        resolve_current_structural_role_authority(rows, AS_OF)


def test_valid_supersession_resolves_one_current_authority() -> None:
    previous = make_row(
        "SECONDARY",
        "CORE",
        relation_id="relation-old",
        superseded_by_authority_id="relation-new",
    )
    current = make_row(
        "SECONDARY",
        "RELATED",
        relation_id="relation-new",
        supersedes_authority_id="relation-old",
    )
    resolved = resolve_current_structural_role_authority((previous, current), AS_OF)
    assert [row.relation_id for row in resolved] == ["relation-new"]
    assert resolved[0].structural_role == "RELATED"


def test_missing_required_lineage_fails_closed() -> None:
    row = make_row("PRIMARY", "REPRESENTATIVE", lineage_hash=None)
    with pytest.raises(StructuralRoleAuthorityReadError, match="lineage_hash"):
        resolve_current_structural_role_authority((row,), AS_OF)


def test_malformed_effective_date_fails_closed() -> None:
    row = make_row(
        "PRIMARY",
        "REPRESENTATIVE",
        effective_from=AS_OF,
        effective_to=AS_OF - timedelta(days=1),
    )
    with pytest.raises(StructuralRoleAuthorityReadError, match="EFFECTIVE_RANGE"):
        resolve_current_structural_role_authority((row,), AS_OF)


def test_missing_supersession_target_fails_closed() -> None:
    row = make_row(
        "SECONDARY",
        "RELATED",
        supersedes_authority_id="missing-target",
    )
    with pytest.raises(StructuralRoleAuthorityReadError, match="MISSING_SUPERSESSION_TARGET"):
        resolve_current_structural_role_authority((row,), AS_OF)

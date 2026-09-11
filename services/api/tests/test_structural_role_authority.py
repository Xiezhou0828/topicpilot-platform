import copy
import json
from pathlib import Path

import pytest

from topicpilot_api.structural_role_authority import (
    StructuralRoleAuthorityError,
    parse_artifact,
)

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = (
    ROOT
    / "config/topic_structural_role_authority/structural-role-authority-20260911.v2.json"
)
CORRECTED_ARTIFACT = (
    ROOT
    / "config/topic_structural_role_authority/structural-role-authority-20260911.v3.json"
)
REFERENCE_CORRECTED_ARTIFACT = (
    ROOT
    / "config/topic_structural_role_authority/structural-role-authority-20260912.v4.json"
)


def _payload():
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_owner_approved_artifact_is_exact_and_complete():
    artifact = parse_artifact(_payload())
    assert artifact.authority_version == "structural-role-authority-20260911.v2"
    assert artifact.artifact_sha256 == (
        "cd6b15f0ac7ac747731a2cc1e3ee38bca9a7bed5dc69be60efeb760b11752c39"
    )
    assert len(artifact.rows) == 1218
    assert len({row["topicId"] for row in artifact.rows}) == 107
    assert {row["structuralRole"] for row in artifact.rows} <= {
        "REPRESENTATIVE", "CORE", "RELATED"
    }


def test_owner_secondary_preservation_correction_is_versioned_and_exact():
    payload = json.loads(CORRECTED_ARTIFACT.read_text(encoding="utf-8"))
    artifact = parse_artifact(payload)
    assert artifact.authority_version == "structural-role-authority-20260911.v3"
    assert artifact.artifact_sha256 == (
        "8b7493199fd30ae2572b1ffde669204b40a48623ef15e93181117fcb086201a3"
    )
    assert payload["correctionLineage"] == {
        "correctionVersion": "production-secondary-preservation-20260911.v1",
        "previousAuthorityVersion": "structural-role-authority-20260911.v2",
        "previousArtifactSha256": (
            "cd6b15f0ac7ac747731a2cc1e3ee38bca9a7bed5dc69be60efeb760b11752c39"
        ),
        "ownerDecision": "KEEP_PRODUCTION_SECONDARY",
        "correctedRelationCount": 375,
        "correctionReason": "OWNER_APPROVED_EXISTING_PRODUCTION_ROLE_PRESERVATION",
    }
    corrections = [row for row in artifact.rows if "relationTypeCorrection" in row]
    assert len(corrections) == 375
    assert all(row["relationType"] == "SECONDARY" for row in corrections)
    assert all(
        row["relationTypeCorrection"]["previousArtifactRelationType"] == "PRIMARY"
        and row["relationTypeCorrection"]["correctedRelationType"] == "SECONDARY"
        for row in corrections
    )


def test_reference_exclusions_are_versioned_and_keep_existing_relations_immutable():
    payload = json.loads(REFERENCE_CORRECTED_ARTIFACT.read_text(encoding="utf-8"))
    artifact = parse_artifact(payload)
    assert artifact.authority_version == "structural-role-authority-20260912.v4"
    assert len(artifact.rows) == 1160
    assert payload["expectedExistingProductionCount"] == 440
    assert payload["expectedMissingProductionCount"] == 720
    assert payload["instrumentReferenceAuthority"][
        "dateEffectiveExcludedInstrumentIdentities"
    ] == 1
    excluded = payload["exclusionLineage"]["excludedRows"]
    assert len(excluded) == 58
    assert len([
        row for row in excluded
        if row["exclusionReason"]
        == "DATE_EFFECTIVE_RELATION_OUTSIDE_INSTRUMENT_VALIDITY"
    ]) == 2
    assert payload["instrumentReferenceAuthority"]["canonicalApproved"] == 49
    assert payload["instrumentReferenceAuthority"]["formallyExcludedInstrumentIdentities"] == 30
    assert all(
        not (row["marketCode"] == "TWO" and row["instrumentCode"] == "6457")
        for row in artifact.rows
    )


@pytest.mark.parametrize("field", ["artifactSha256", "targetEnvironment"])
def test_artifact_tamper_or_wrong_target_fails_closed(field):
    payload = copy.deepcopy(_payload())
    payload[field] = "wrong"
    with pytest.raises(StructuralRoleAuthorityError):
        parse_artifact(payload)


def test_duplicate_relation_identity_fails_closed():
    payload = _payload()
    payload["rows"][1] = copy.deepcopy(payload["rows"][0])
    canonical = dict(payload)
    canonical.pop("artifactSha256")
    from topicpilot_api.structural_role_authority import _hash
    payload["artifactSha256"] = _hash(canonical)
    with pytest.raises(StructuralRoleAuthorityError, match="duplicate"):
        parse_artifact(payload)


def test_relation_reconciliation_contract_allows_initial_and_idempotent_states():
    approved_states = {(440, 778), (1218, 0)}
    assert (440, 778) in approved_states
    assert (1218, 0) in approved_states
    assert (1217, 1) not in approved_states

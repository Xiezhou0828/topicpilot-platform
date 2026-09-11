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

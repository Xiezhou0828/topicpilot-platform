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
    / "config/topic_structural_role_authority/structural-role-authority-20260911.v1.json"
)


def _payload():
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_owner_approved_artifact_is_exact_and_complete():
    artifact = parse_artifact(_payload())
    assert artifact.authority_version == "structural-role-authority-20260911.v1"
    assert artifact.artifact_sha256 == (
        "a168dc51b722da04fe86e151820e7ec49d77f2a015f4a426b8da288ed14b069d"
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

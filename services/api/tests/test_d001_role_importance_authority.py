import copy
import json
from decimal import Decimal
from pathlib import Path

import pytest

from topicpilot_api.d001_role_importance_authority import (
    ROLE_IMPORTANCE,
    D001RoleImportanceAuthorityError,
    _hash,
    load_artifact,
    parse_artifact,
)
from topicpilot_api.d001_role_importance_cli import main

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = ROOT / (
    "config/topic_d001_role_importance_authority/"
    "d001-role-importance-authority-20260920.v1.json"
)


def test_dec04_artifact_is_hash_valid_and_covers_all_formal_members():
    artifact = load_artifact(ARTIFACT)

    assert artifact.authority_version == "d001-role-importance-authority-20260920.v1"
    assert artifact.payload["expectedTopicCount"] == 107
    assert artifact.payload["expectedMemberCount"] == 1160
    assert artifact.payload["importancePolicy"]["roleToImportance"] == {
        "CORE": "1.00",
        "REPRESENTATIVE": "0.75",
        "RELATED": "0.25",
    }
    assert artifact.payload["historicalRoleRecoverySource"]["proposalState"] == (
        "PROPOSAL_ONLY_NON_AUTHORITY"
    )
    assert {member.importance for member in artifact.members} == {
        Decimal("1.00"),
        Decimal("0.75"),
        Decimal("0.25"),
    }
    assert ROLE_IMPORTANCE["RELATED"] == Decimal("0.25")


def test_legacy_050_member_value_is_rejected_without_rewrite():
    payload = copy.deepcopy(json.loads(ARTIFACT.read_text(encoding="utf-8")))
    payload["topics"][0]["members"][0]["importance"] = "0.50"
    payload_without_hash = dict(payload)
    payload_without_hash.pop("artifactSha256")
    payload["artifactSha256"] = _hash(payload_without_hash)

    with pytest.raises(D001RoleImportanceAuthorityError, match="outside DEC-04 mapping"):
        parse_artifact(payload)


def test_d001_operator_validation_is_available_without_database():
    assert main(["--artifact", str(ARTIFACT), "--validate-only"]) == 0

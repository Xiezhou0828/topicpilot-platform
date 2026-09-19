from decimal import Decimal
from pathlib import Path

from topicpilot_api.d001_role_importance_authority import (
    ROLE_IMPORTANCE,
    load_artifact,
)

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

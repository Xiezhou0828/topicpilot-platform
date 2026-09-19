"""Generate the DEC-04 D001 role-based importance authority artifact."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROLE_IMPORTANCE = {"CORE": "1.00", "REPRESENTATIVE": "0.75", "RELATED": "0.25"}
ROLE_ARTIFACT = Path("config/topic_structural_role_authority/structural-role-authority-20260912.v4.json")
OUTPUT = Path(
    "config/topic_d001_role_importance_authority/"
    "d001-role-importance-authority-20260920.v1.json"
)
DEFAULT_HISTORY = Path(
    "C:/Users/acer/.codex/worktrees/c3a0/題材領航/reports/WS1-AUX-507-STOCK-STRUCTURAL-ROLE/"
    "final_owner_approved_structural_role_authority_candidate_post_c2_20260819.tsv"
)


def canonical_hash(value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def history_summary(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    proposal_states = sorted({row.get("proposal_state", "") for row in rows})
    return {
        "logicalFileName": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "proposalState": proposal_states[0] if len(proposal_states) == 1 else "MIXED",
        "proposalStateValues": proposal_states,
        "rowCount": len(rows),
        "ownerReviewedCounts": dict(sorted(Counter(row.get("owner_reviewed", "") for row in rows).items())),
        "roleCounts": dict(sorted(Counter(row.get("final_structural_role", "") for row in rows).items())),
        "historicalImportanceCounts": dict(
            sorted(Counter(row.get("final_importance", "") for row in rows).items())
        ),
        "usage": "HISTORICAL_DESIGN_EVIDENCE_ONLY; NOT_CURRENT_AUTHORITY",
    }


def build(role_path: Path, history_path: Path) -> dict[str, Any]:
    role_payload = json.loads(role_path.read_text(encoding="utf-8"))
    rows = list(role_payload["rows"])
    if len(rows) != int(role_payload["expectedRelationCount"]):
        raise ValueError("structural role artifact row count mismatch")
    if len({row["topicId"] for row in rows}) != int(role_payload["expectedLeafCount"]):
        raise ValueError("structural role artifact topic count mismatch")
    if any(row["structuralRole"] not in ROLE_IMPORTANCE for row in rows):
        raise ValueError("structural role artifact contains an unknown role")

    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        topic_id = str(row["topicId"])
        group = grouped.setdefault(
            topic_id,
            {"topicId": topic_id, "topicKey": row["topicKey"], "members": []},
        )
        group["members"].append(
            {
                "marketCode": str(row["marketCode"]),
                "instrumentCode": str(row["instrumentCode"]),
                "relationId": str(row["relationId"]),
                "structuralRole": str(row["structuralRole"]),
                "importance": ROLE_IMPORTANCE[str(row["structuralRole"])],
                "roleAuthorityVersion": str(role_payload["authorityVersion"]),
            }
        )
    topics = sorted(grouped.values(), key=lambda item: item["topicId"])
    for topic in topics:
        topic["members"].sort(
            key=lambda item: (item["marketCode"], item["instrumentCode"], item["relationId"])
        )

    payload: dict[str, Any] = {
        "schemaVersion": "topic-d001-role-importance-authority.v1",
        "authorityVersion": "d001-role-importance-authority-20260920.v1",
        "effectiveDate": "2026-09-20",
        "targetEnvironment": "production",
        "approvalReference": "DEC-04=APPROVED_ROLE_BASED_IMPORTANCE_V1",
        "sourceStructuralRoleAuthority": {
            "authorityVersion": role_payload["authorityVersion"],
            "artifactSha256": role_payload["artifactSha256"],
            "file": str(role_path).replace("\\", "/"),
            "effectiveDate": role_payload["effectiveDate"],
        },
        "historicalRoleRecoverySource": history_summary(history_path),
        "importancePolicy": {
            "roleToImportance": ROLE_IMPORTANCE,
            "importanceIsRoleProjection": True,
            "orderAffectsScore": False,
            "orderingRule": "stable Topic/instrument/relation identifier only",
            "fixedMinRequiredByFormula": False,
            "fixedMaxRequiredByFormula": False,
            "topN": None,
        },
        "memberUniverse": {
            "mode": "ALL_FORMAL_TOPIC_MEMBERS",
            "source": "APPROVED_STRUCTURAL_ROLE_AUTHORITY",
            "manualCoreSubset": False,
        },
        "expectedTopicCount": len(topics),
        "expectedMemberCount": len(rows),
        "topics": topics,
    }
    payload["artifactSha256"] = canonical_hash(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--role-artifact", type=Path, default=ROLE_ARTIFACT)
    parser.add_argument("--historical-tsv", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    payload = build(args.role_artifact, args.historical_tsv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(args.output), "artifactSha256": payload["artifactSha256"], "topicCount": payload["expectedTopicCount"], "memberCount": payload["expectedMemberCount"]}))


if __name__ == "__main__":
    main()

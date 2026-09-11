"""Build the exact Owner-approved 107-Leaf structural-role artifact."""

from __future__ import annotations

import csv
import hashlib
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(r"E:\topicpilot-platform-canonical")
SOURCE = SOURCE_ROOT / "config/topic_master_v1/instrument_topic_memberships.csv"
TOPICS = SOURCE_ROOT / "config/topic_master_v1/topics.csv"
ONTOLOGY = ROOT / "config/topic_authority_v1/lifecycle-formal-scope-20260911.v2.json"
OUTPUT = ROOT / "config/topic_structural_role_authority/structural-role-authority-20260911.v2.json"
SOURCE_SHA256 = "641a1c1dbd1849d70ffd7efa775f24d0bc5f7e35610179e27f0a587834bce188"
RELATION_NAMESPACE = uuid.UUID("da995966-4275-5fe0-9c45-8dc84ad2c3c1")
RELATION_VERSION = "owner-topic-membership-20260824.v1"


def digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def main() -> None:
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise SystemExit("Owner source hash mismatch")
    with TOPICS.open(encoding="utf-8-sig", newline="") as handle:
        topic_rows = list(csv.DictReader(handle))
    parents = {row["parent_topic"] for row in topic_rows if row["parent_topic"]}
    leaves = {row["topic_key"] for row in topic_rows if row["topic_key"] not in parents}
    ontology = json.loads(ONTOLOGY.read_text(encoding="utf-8"))
    topic_ids = {
        row["name"]: row["topicId"] for row in ontology["topics"]
        if row["level"] == "LEAF" and row["status"] in {"ACTIVE", "ENABLED", "PUBLISHED"}
    }
    rows: list[dict[str, str]] = []
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["enabled"].upper() != "TRUE" or row["topic_key"] not in leaves:
                continue
            role = "REPRESENTATIVE" if row["structural_role"] == "LEAD" else row["structural_role"]
            identity = (
                f"{SOURCE_SHA256}:{row['market_code']}:{row['instrument_code']}:"
                f"{topic_ids[row['topic_key']]}:{row['topic_relation_type']}:2026-08-24"
            )
            rows.append({
                "relationId": str(uuid.uuid5(RELATION_NAMESPACE, identity)),
                "relationVersion": RELATION_VERSION,
                "marketCode": row["market_code"],
                "instrumentCode": row["instrument_code"],
                "topicId": topic_ids[row["topic_key"]],
                "topicKey": row["topic_key"],
                "relationType": row["topic_relation_type"],
                "structuralRole": role,
                "approvalState": "APPROVED",
                "sourceReference": row["source_reference"],
            })
    rows.sort(key=lambda item: (item["topicId"], item["marketCode"], item["instrumentCode"]))
    payload: dict[str, object] = {
        "schemaVersion": "topic-structural-role-authority.v1",
        "authorityVersion": "structural-role-authority-20260911.v2",
        "artifactSha256": "",
        "sourceMasterSha256": SOURCE_SHA256,
        "targetEnvironment": "production",
        "targetDatabase": "neondb",
        "approvalReference": "OWNER_APPROVAL_2026-09-11_A9_B2_FORMAL_CORRECTION",
        "effectiveDate": "2026-08-24",
        "expectedRelationCount": 1218,
        "expectedLeafCount": 107,
        "rows": rows,
    }
    payload["artifactSha256"] = digest(
        {key: value for key, value in payload.items() if key != "artifactSha256"}
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "rows": len(rows),
        "leaves": len({row["topicId"] for row in rows}),
        "sha256": payload["artifactSha256"],
    }))


if __name__ == "__main__":
    main()

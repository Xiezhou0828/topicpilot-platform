"""Build the governed B2 Topic authority activation artifact.

This builder reconciles the Owner Topic Master against one explicit Production
Topic Catalog readback.  It preserves exact UUIDs, applies only the documented
Owner-approved renames, retires Production identities absent from the active
Owner authority, and assigns deterministic UUIDv5 values only to explicitly
authorized CREATE rows in the resulting artifact.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
import uuid
from pathlib import Path

from topicpilot_api.topic_authority_activation import artifact_hash
from topicpilot_api.topic_master_v1 import load_master, validate_master

SCHEMA_VERSION = "topic-authority-activation.v1"
ACTIVATION_VERSION = "topic-authority-lifecycle-formal-scope.20260911.v1"
APPROVAL_REFERENCE = "OWNER-AUTHORIZED-B2-PROTECTED-TOPIC-AUTHORITY-20260910"
CREATE_NAMESPACE = uuid.UUID("da995966-4275-5fe0-9c45-8dc84ad2c3c1")

OWNER_APPROVED_RENAMES = {
    "CCL": "銅箔基板CCL",
    "其他高頻材料": "製程耗材與特料",
    "其他連接器": "特用與精密線束",
    "半導體原料": "利基型光電磊晶",
    "高頻電子材料": "PCB供應鏈",
    "半導體設備與製程": "半導體設備與權值",
}


def _read_catalog(url: str) -> list[dict]:
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = json.load(response)
    rows = payload.get("items")
    if not isinstance(rows, list) or payload.get("total") != len(rows):
        raise ValueError("Production Topic Catalog readback is incomplete")
    return rows


def _deterministic_topic_id(source_hash: str, topic_key: str) -> uuid.UUID:
    return uuid.uuid5(CREATE_NAMESPACE, f"{source_hash}:{topic_key}")


def build_artifact(
    *,
    source_root: Path,
    production_catalog: list[dict],
    target_database: str,
    source_revision: str,
) -> dict:
    master = load_master(
        source_root / "topics.csv",
        source_root / "instrument_topic_memberships.csv",
        source_root / "instruments.csv",
    )
    validation = validate_master(master)
    if not validation.valid:
        raise ValueError("Owner Topic Master validation failed")

    active_source = {
        row["topic_key"]: row for row in master.topics if row["enabled"] == "TRUE"
    }
    source_parents = {
        key for key, row in active_source.items() if not row["parent_topic"]
    }
    source_leaves = {
        key for key, row in active_source.items() if row["parent_topic"]
    }
    if len(source_parents) != 25 or len(source_leaves) != 107:
        raise ValueError("Owner authority is not the frozen 25 Parent / 107 Leaf scope")

    production_by_slug = {str(row["slug"]): row for row in production_catalog}
    if len(production_by_slug) != len(production_catalog):
        raise ValueError("Production Topic Catalog contains duplicate slugs")
    inverse_renames = {new: old for old, new in OWNER_APPROVED_RENAMES.items()}
    used_production_ids: set[str] = set()
    active_rows: list[dict] = []
    id_by_source_key: dict[str, str] = {}

    for key in sorted(active_source):
        source = active_source[key]
        production = production_by_slug.get(key)
        action = "PRESERVE"
        expected_current_slug = key
        mapping_reason = "EXACT_CURRENT_CANONICAL_IDENTITY"
        if production is None and key in inverse_renames:
            expected_current_slug = inverse_renames[key]
            production = production_by_slug.get(expected_current_slug)
            action = "RENAME"
            mapping_reason = "OWNER_APPROVED_RENAME_PRESERVE_UUID"
        if production is None:
            topic_id = str(_deterministic_topic_id(master.source_hash, key))
            action = "CREATE"
            mapping_reason = "OWNER_AUTHORITY_EXPLICIT_CREATE_DETERMINISTIC_UUIDV5"
        else:
            topic_id = str(production["topicId"])
            used_production_ids.add(topic_id)
        level = "PARENT" if key in source_parents else "LEAF"
        row = {
            "topicId": topic_id,
            "slug": key,
            "name": source["topic_name"],
            "description": source["description"] or None,
            "level": level,
            "status": "ENABLED",
            "action": action,
            "mappingReason": mapping_reason,
        }
        if action == "CREATE":
            row["creationAuthorized"] = True
        else:
            row["expectedCurrentSlug"] = expected_current_slug
        active_rows.append(row)
        id_by_source_key[key] = topic_id

    retired_rows: list[dict] = []
    for production in sorted(production_catalog, key=lambda row: row["slug"]):
        topic_id = str(production["topicId"])
        if topic_id in used_production_ids:
            continue
        retired_rows.append(
            {
                "topicId": topic_id,
                "slug": production["slug"],
                "name": production["name"],
                "description": None,
                "level": production["kind"],
                "status": "RETIRED",
                "action": "RETIRE",
                "expectedCurrentSlug": production["slug"],
                "mappingReason": "ABSENT_FROM_ACTIVE_OWNER_TOPIC_AUTHORITY",
            }
        )

    hierarchy = [
        {
            "parentTopicId": id_by_source_key[row["parent_topic"]],
            "childTopicId": id_by_source_key[row["topic_key"]],
        }
        for row in master.topics
        if row["enabled"] == "TRUE" and row["parent_topic"]
    ]
    lifecycle_scope = [
        {
            "researchIdentity": key,
            "canonicalIdentity": key,
            "canonicalTopicId": id_by_source_key[key],
            "mappingReason": next(
                row["mappingReason"] for row in active_rows if row["slug"] == key
            ),
            "status": "RESOLVED",
        }
        for key in sorted(source_leaves)
    ]
    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "activationVersion": ACTIVATION_VERSION,
        "artifactSha256": "",
        "sourceMasterSha256": master.source_hash,
        "sourceRevision": source_revision,
        "targetEnvironment": "production",
        "targetDatabase": target_database,
        "approvalReference": APPROVAL_REFERENCE,
        "effectiveDate": "2026-09-11",
        "expectedParentCount": 25,
        "expectedLeafCount": 107,
        "topics": sorted(active_rows + retired_rows, key=lambda row: row["slug"]),
        "hierarchy": sorted(
            hierarchy, key=lambda row: (row["parentTopicId"], row["childTopicId"])
        ),
        "lifecycleScope": lifecycle_scope,
    }
    payload["artifactSha256"] = artifact_hash(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--catalog-url", required=True)
    parser.add_argument("--target-database", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_artifact(
        source_root=args.source_root,
        production_catalog=_read_catalog(args.catalog_url),
        target_database=args.target_database,
        source_revision=args.source_revision,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "artifactSha256": payload["artifactSha256"],
                "topics": len(payload["topics"]),
                "hierarchy": len(payload["hierarchy"]),
                "lifecycleScope": len(payload["lifecycleScope"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

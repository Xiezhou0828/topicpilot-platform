"""One-time deterministic seed for the Owner Master V1 source files.

This tool copies taxonomy and membership facts from the explicitly research-
classified mapping only to establish a reviewable starting point.  It does
not infer structural roles.  Run it once for the task artifact; Owners edit
the resulting CSV files directly afterwards.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

MLCC_ROLES = {
    "2327": "LEAD",
    "8043": "LEAD",
    "2492": "CORE",
    "3026": "CORE",
    "6173": "CORE",
    "4716": "RELATED",
}
MLCC_MARKETS = {
    "2327": "TPE",
    "8043": "TWO",
    "2492": "TPE",
    "3026": "TPE",
    "6173": "TWO",
    "4716": "TWO",
}


def _write(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build(source: Path, destination: Path) -> None:
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    by_topic: dict[str, dict[str, str]] = {}
    for row in source_rows:
        topic = row["topic_name"].strip()
        by_topic.setdefault(
            topic,
            {
                "topic_key": topic,
                "topic_name": topic,
                "parent_topic": row["topic_parent"].strip(),
                "enabled": "TRUE" if row["topic_enabled"].strip().upper() == "Y" else "FALSE",
                "description": row["topic_description"].strip(),
                "governance_state": "RESEARCH_BOOTSTRAP_PENDING_OWNER_REVIEW",
            },
        )
        parent = row["topic_parent"].strip()
        if parent and parent not in by_topic:
            by_topic[parent] = {
                "topic_key": parent,
                "topic_name": parent,
                "parent_topic": "",
                "enabled": "TRUE",
                "description": "",
                "governance_state": "RESEARCH_BOOTSTRAP_PARENT_PENDING_OWNER_REVIEW",
            }
    topic_rows = [by_topic[key] for key in sorted(by_topic)]

    memberships: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in source_rows:
        market = row["market_code"].strip().upper()
        code = row["instrument_code"].strip()
        topic = row["topic_name"].strip()
        key = (market, code, topic)
        memberships[key] = {
            "market_code": market,
            "instrument_code": code,
            "instrument_name": row["instrument_name"].strip(),
            "topic_key": topic,
            "topic_relation_type": row["topic_role"].strip(),
            "structural_role": "",
            "topic_weight": row["stock_topic_weight"].strip(),
            "enabled": "TRUE",
            "review_state": "PENDING_REVIEW",
            "valid_from": "2026-08-24",
            "valid_to": "",
            "source_reference": (
                "fixtures/research/topic_universe_mapping.v1.csv;NOT_PRODUCT_AUTHORITY"
            ),
        }

    for code, role in MLCC_ROLES.items():
        key = (MLCC_MARKETS[code], code, "MLCC")
        if key in memberships:
            memberships[key]["structural_role"] = role
            memberships[key]["review_state"] = "APPROVED"
            memberships[key]["source_reference"] = "CURRENT_TAXONOMY_RELATION_STRUCTURAL_ROLE"
        else:
            memberships[key] = {
                "market_code": MLCC_MARKETS[code],
                "instrument_code": code,
                "instrument_name": {
                    "2327": "國巨",
                    "8043": "蜜望實",
                    "2492": "華新科",
                    "3026": "禾伸堂",
                    "6173": "信昌電",
                    "4716": "大立",
                }[code],
                "topic_key": "MLCC",
                "topic_relation_type": "",
                "structural_role": role,
                "topic_weight": "",
                "enabled": "TRUE",
                "review_state": "PENDING_REVIEW",
                "valid_from": "2026-08-24",
                "valid_to": "",
                "source_reference": (
                    "CURRENT_TAXONOMY_RELATION_STRUCTURAL_ROLE;RELATION_TYPE_REVIEW_REQUIRED"
                ),
            }
    membership_rows = [memberships[key] for key in sorted(memberships)]

    _write(
        destination / "topics.csv",
        ["topic_key", "topic_name", "parent_topic", "enabled", "description", "governance_state"],
        topic_rows,
    )
    _write(
        destination / "instrument_topic_memberships.csv",
        [
            "market_code",
            "instrument_code",
            "instrument_name",
            "topic_key",
            "topic_relation_type",
            "structural_role",
            "topic_weight",
            "enabled",
            "review_state",
            "valid_from",
            "valid_to",
            "source_reference",
        ],
        membership_rows,
    )
    (destination / "README.md").write_text(
        "# Topic Taxonomy + Membership Master V1\n\n"
        "These CSVs are the Owner-editable source. The initial seed preserves the\n"
        "research mapping as pending review and carries the six currently known\n"
        "MLCC role rows without changing them. Run the validator before review or\n"
        "canonical synchronization. Do not edit generated snapshots.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    if (args.destination / "topics.csv").exists() or (
        args.destination / "instrument_topic_memberships.csv"
    ).exists():
        raise SystemExit("destination already contains Owner source; refuse to overwrite")
    build(args.source, args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

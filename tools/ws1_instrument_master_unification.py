"""Build the Owner Instrument Master V1 from all audited identity sources.

This tool is intentionally offline and deterministic.  It only writes the
Owner CSV and reconciliation CSVs; it never writes to a database or external
service.  Runtime provenance is retained for auditability, but is not used as
an operational universe partition.
"""

from __future__ import annotations

import csv
import json
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER_DIR = ROOT / "config" / "topic_master_v1"
REPORT_DIR = ROOT / "reports" / "TASK-WS1-INSTRUMENT-MASTER-V1-CANONICAL-UNIVERSE-UNIFICATION-20260824"
OLD_REFERENCE = (
    ROOT
    / "services"
    / "api"
    / "src"
    / "topicpilot_api"
    / "reference_data"
    / "bundles"
    / "tw-reference-v1"
    / "instruments.json"
)
LEGACY_REFERENCE_SNAPSHOT = REPORT_DIR / "legacy-507-instruments.json"
EXPANSION = (
    ROOT
    / "reports"
    / "TASK-INSTRUMENT-UNIVERSE-96-STOCK-EXPANSION-REFERENCE-PACK-AND-RUNTIME-HANDOFF-20260819"
    / "expansion-reference-normalized-candidates.csv"
)
MEMBERSHIPS = OWNER_DIR / "instrument_topic_memberships.csv"

INSTRUMENT_FIELDS = (
    "market_code",
    "instrument_code",
    "instrument_name",
    "instrument_type",
    "currency",
    "enabled",
    "listing_status",
    "valid_from",
    "valid_to",
    "identity_source",
    "provenance_class",
    "owner_review_required",
)

SUPERSET_FIELDS = (
    "market_code",
    "instrument_code",
    "instrument_name",
    "enabled",
    "listing_status",
    "current_reference_present",
    "membership_present",
    "legacy_present",
    "other_source_present",
    "identity_conflict",
    "name_conflict",
    "market_conflict",
    "source_authority",
    "owner_review_required",
    "identity_sources",
)

COMPARISON_FIELDS = (
    "market_code",
    "instrument_code",
    "instrument_name",
    "old_507_present",
    "unified_present",
    "membership_present",
    "expansion_96_present",
    "active_membership_count",
    "status_in_unified_master",
    "source_authority",
)

RECONCILIATION_FIELDS = (
    "market_code",
    "instrument_code",
    "instrument_name",
    "membership_row_count",
    "old_507_present",
    "expansion_96_present",
    "identity_conflict",
    "name_conflict",
    "market_conflict",
    "reconciliation_status",
    "source_evidence",
    "owner_review_required",
    "notes",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def _bool(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def _load_sources() -> tuple[dict[tuple[str, str], dict[str, object]], dict[str, int]]:
    source_rows: dict[str, dict[tuple[str, str], dict[str, str]]] = {
        "tw-reference-v1": {},
        "expansion-reference-normalized-candidates.csv": {},
        "instrument_topic_memberships.csv": {},
    }

    if not LEGACY_REFERENCE_SNAPSHOT.exists():
        try:
            legacy_payload = subprocess.check_output(
                [
                    "git",
                    "show",
                    "HEAD:services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1/instruments.json",
                ],
                cwd=ROOT,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise RuntimeError("cannot recover the original 507 reference source from Git HEAD") from exc
        LEGACY_REFERENCE_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        LEGACY_REFERENCE_SNAPSHOT.write_bytes(legacy_payload)

    for row in json.loads(LEGACY_REFERENCE_SNAPSHOT.read_text(encoding="utf-8")):
        identity = (row["market_code"].strip().upper(), str(row["instrument_code"]).strip())
        source_rows["tw-reference-v1"][identity] = {
            "instrument_name": row["name"].strip(),
            "listing_status": "ACTIVE",
        }

    for row in _read_csv(EXPANSION):
        identity = (row["market"].upper(), row["stock_code"])
        source_rows["expansion-reference-normalized-candidates.csv"][identity] = {
            "instrument_name": row["stock_name"],
            "listing_status": row.get("listing_status", "active").upper(),
        }

    membership_names: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in _read_csv(MEMBERSHIPS):
        identity = (row["market_code"].upper(), row["instrument_code"])
        membership_names[identity].add(row["instrument_name"])
    for identity, names in membership_names.items():
        if len(names) != 1:
            raise RuntimeError(f"membership identity has conflicting names: {identity}: {sorted(names)}")
        source_rows["instrument_topic_memberships.csv"][identity] = {
            "instrument_name": next(iter(names)),
            "listing_status": "ACTIVE",
        }

    identities = sorted(set().union(*(set(rows) for rows in source_rows.values())))
    records: dict[tuple[str, str], dict[str, object]] = {}
    for identity in identities:
        names_by_source = {
            source: rows[identity]["instrument_name"]
            for source, rows in source_rows.items()
            if identity in rows
        }
        names = set(names_by_source.values())
        if len(names) != 1:
            raise RuntimeError(f"identity name conflict requires Owner review: {identity}: {names_by_source}")
        present = set(names_by_source)
        legacy_present = "tw-reference-v1" in present
        membership_present = "instrument_topic_memberships.csv" in present
        expansion_present = "expansion-reference-normalized-candidates.csv" in present
        if legacy_present and expansion_present and membership_present:
            provenance = "LEGACY_REFERENCE_AND_OWNER_EXPANSION_AND_MEMBERSHIP"
        elif legacy_present and membership_present:
            provenance = "LEGACY_REFERENCE_AND_OWNER_MEMBERSHIP"
        elif legacy_present and expansion_present:
            provenance = "LEGACY_REFERENCE_AND_OWNER_EXPANSION"
        elif expansion_present and membership_present:
            provenance = "OWNER_EXPANSION_AND_MEMBERSHIP"
        elif legacy_present:
            provenance = "LEGACY_REFERENCE_ONLY"
        elif expansion_present:
            provenance = "OWNER_APPROVED_EXPANSION_ONLY"
        else:
            provenance = "OWNER_MEMBERSHIP_IDENTITY_ONLY"
        records[identity] = {
            "instrument_name": next(iter(names)),
            "sources": present,
            "legacy_present": legacy_present,
            "membership_present": membership_present,
            "expansion_present": expansion_present,
            "provenance": provenance,
            "name_conflict": False,
            "market_conflict": False,
        }

    counts = {
        "old_507_count": len(source_rows["tw-reference-v1"]),
        "expansion_96_count": len(source_rows["expansion-reference-normalized-candidates.csv"]),
        "membership_unique_count": len(source_rows["instrument_topic_memberships.csv"]),
        "unified_count": len(records),
        "old_507_only_count": len(
            set(source_rows["tw-reference-v1"]) - set(source_rows["instrument_topic_memberships.csv"])
        ),
        "membership_only_before_count": len(
            set(source_rows["instrument_topic_memberships.csv"])
            - set(source_rows["tw-reference-v1"])
        ),
        "membership_only_after_expansion_count": len(
            set(source_rows["instrument_topic_memberships.csv"])
            - set(source_rows["tw-reference-v1"])
            - set(source_rows["expansion-reference-normalized-candidates.csv"])
        ),
    }
    return records, counts


def build() -> dict[str, object]:
    records, counts = _load_sources()
    memberships = _read_csv(MEMBERSHIPS)
    membership_counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in memberships:
        membership_counts[(row["market_code"].upper(), row["instrument_code"])] += 1

    instrument_rows: list[dict[str, str]] = []
    superset_rows: list[dict[str, str]] = []
    comparison_rows: list[dict[str, str]] = []
    reconciliation_rows: list[dict[str, str]] = []
    for (market, code), record in sorted(records.items()):
        status = "DELISTED" if (market, code) == ("TPE", "6806") else "ACTIVE"
        membership_present = bool(record["membership_present"])
        expansion_present = bool(record["expansion_present"])
        legacy_present = bool(record["legacy_present"])
        source_names = []
        if legacy_present:
            source_names.append(
                "reports/TASK-WS1-INSTRUMENT-MASTER-V1-CANONICAL-UNIVERSE-UNIFICATION-20260824/legacy-507-instruments.json"
            )
        if expansion_present:
            source_names.append("expansion-reference-normalized-candidates.csv")
        if membership_present:
            source_names.append("instrument_topic_memberships.csv")
        source_names_text = ";".join(source_names)
        authority = "OWNER_INSTRUMENT_MASTER_V1"
        instrument_rows.append(
            {
                "market_code": market,
                "instrument_code": code,
                "instrument_name": str(record["instrument_name"]),
                "instrument_type": "EQUITY",
                "currency": "TWD",
                "enabled": "TRUE",
                "listing_status": status,
                "valid_from": "",
                "valid_to": "",
                "identity_source": source_names_text,
                "provenance_class": str(record["provenance"]),
                "owner_review_required": "FALSE",
            }
        )
        superset_rows.append(
            {
                "market_code": market,
                "instrument_code": code,
                "instrument_name": str(record["instrument_name"]),
                "enabled": "TRUE",
                "listing_status": status,
                "current_reference_present": _bool(legacy_present),
                "membership_present": _bool(membership_present),
                "legacy_present": _bool(legacy_present),
                "other_source_present": _bool(expansion_present),
                "identity_conflict": "FALSE",
                "name_conflict": "FALSE",
                "market_conflict": "FALSE",
                "source_authority": authority,
                "owner_review_required": "FALSE",
                "identity_sources": source_names_text,
            }
        )
        comparison_rows.append(
            {
                "market_code": market,
                "instrument_code": code,
                "instrument_name": str(record["instrument_name"]),
                "old_507_present": _bool(legacy_present),
                "unified_present": "TRUE",
                "membership_present": _bool(membership_present),
                "expansion_96_present": _bool(expansion_present),
                "active_membership_count": str(membership_counts.get((market, code), 0)),
                "status_in_unified_master": status,
                "source_authority": authority,
            }
        )
        if membership_present and not legacy_present:
            reconciliation_rows.append(
                {
                    "market_code": market,
                    "instrument_code": code,
                    "instrument_name": str(record["instrument_name"]),
                    "membership_row_count": str(membership_counts[(market, code)]),
                    "old_507_present": "FALSE",
                    "expansion_96_present": _bool(expansion_present),
                    "identity_conflict": "FALSE",
                    "name_conflict": "FALSE",
                    "market_conflict": "FALSE",
                    "reconciliation_status": "INCORPORATED_IN_INSTRUMENT_MASTER",
                    "source_evidence": source_names_text,
                    "owner_review_required": "FALSE",
                    "notes": (
                        "Identity is unambiguous from current Owner membership and/or approved expansion source; "
                        "included without inventing a topic membership."
                    ),
                }
            )

    _write_csv(OWNER_DIR / "instruments.csv", INSTRUMENT_FIELDS, instrument_rows)
    _write_csv(REPORT_DIR / "full-recovered-instrument-superset.csv", SUPERSET_FIELDS, superset_rows)
    _write_csv(REPORT_DIR / "old-507-vs-unified-universe.csv", COMPARISON_FIELDS, comparison_rows)
    _write_csv(REPORT_DIR / "membership-only-instrument-reconciliation.csv", RECONCILIATION_FIELDS, reconciliation_rows)

    return {**counts, "membership_row_count": len(memberships), "membership_only_incorporated_count": len(reconciliation_rows)}


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, sort_keys=True, indent=2))

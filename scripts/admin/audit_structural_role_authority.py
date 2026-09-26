"""Run the complete read-only Production structural-role authority audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT = Path(
    r"E:\topicpilot-artifacts\structural-role-authority-drift-reconciliation-003\pre-correction"
)
CSV_FIELDS = [
    "relation_id",
    "instrument_id",
    "instrument_code",
    "instrument_type",
    "instrument_active",
    "instrument_valid_from",
    "instrument_valid_to",
    "market_code",
    "market_active",
    "topic_id",
    "topic_slug",
    "topic_status",
    "topic_valid_from",
    "topic_valid_to",
    "relation_type",
    "structural_role",
    "role_status",
    "invalid_role_value",
    "invalid_role_category",
    "root_cause",
    "approval_state",
    "authority_version",
    "effective_from",
    "effective_to",
    "authority_status_bucket",
    "current_effective",
    "supersedes_authority_id",
    "superseded_by_authority_id",
    "source_artifact_id",
    "source_artifact_hash",
    "approval_reference",
    "correction_sequence",
    "lineage_hash",
    "supersession_issue",
    "lineage_issue",
]
OWNER_FIELDS = [
    "relation_id",
    "instrument",
    "topic",
    "current_role",
    "candidate_roles",
    "authority_versions",
    "source_artifacts",
    "reason_for_ambiguity",
]
PLAN_FIELDS = [
    "relation_id",
    "instrument",
    "topic",
    "current_role",
    "target_role",
    "authority_version",
    "source_artifact",
    "effective_from",
    "correction_reason",
    "operation",
    "confidence",
]


def fetch(base_url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/v1/admin/relations/structural-role-authority/audit?limit=10000&offset=0",
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: "" if row.get(field) is None else row.get(field) for field in fields})


def write_manifest(output_dir: Path) -> None:
    lines = []
    for path in sorted(output_dir.iterdir()):
        if path.name == "SHA256SUMS.txt" or not path.is_file():
            continue
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    (output_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_artifacts(payload: dict[str, Any], output_dir: Path, base_url: str) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = payload.get("items", [])
    summary = payload.get("summary", {})
    write_csv(output_dir / "all-structural-role-authority.csv", rows, CSV_FIELDS)
    write_csv(
        output_dir / "invalid-structural-role-authority.csv",
        [
            row
            for row in rows
            if row.get("role_status") != "VALID"
            or row.get("supersession_issue")
            or row.get("lineage_issue")
        ],
        CSV_FIELDS,
    )
    write_csv(
        output_dir / "authority-lineage-map.csv",
        rows,
        [
            "relation_id",
            "instrument_id",
            "topic_id",
            "structural_role",
            "approval_state",
            "authority_version",
            "effective_from",
            "effective_to",
            "source_artifact_id",
            "source_artifact_hash",
            "approval_reference",
            "correction_sequence",
            "supersedes_authority_id",
            "superseded_by_authority_id",
            "lineage_hash",
            "supersession_issue",
            "lineage_issue",
        ],
    )
    write_csv(output_dir / "pre-correction-readback.csv", rows, CSV_FIELDS)
    write_csv(output_dir / "owner-decision-required.csv", [], OWNER_FIELDS)
    write_csv(output_dir / "correction-plan.csv", [], PLAN_FIELDS)

    audit_summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": base_url,
        "read_path": "/api/v1/admin/relations/structural-role-authority/audit",
        "read_only": True,
        "summary": summary,
        "page_total": payload.get("total"),
        "items_returned": len(rows),
    }
    (output_dir / "audit-summary.json").write_text(
        json.dumps(audit_summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "root-cause-analysis.md").write_text(
        "# Root-cause analysis\n\n"
        "This report is generated from the complete read-only operator audit. "
        "It does not infer a structural role from relation type, topicRole, score projection, "
        "market behavior, or relation weight. Rows without direct formal evidence remain "
        "`UNKNOWN_ROOT_CAUSE` and are not eligible for automatic correction.\n\n"
        f"- Total rows scanned: `{summary.get('total_rows_scanned')}`\n"
        f"- Invalid non-null role rows: `{summary.get('invalid_role_rows')}`\n"
        f"- NULL role rows: `{summary.get('null_role_rows')}`\n"
        f"- Unknown role rows: `{summary.get('unknown_role_rows')}`\n"
        f"- Supersession conflicts: `{summary.get('supersession_conflict_rows')}`\n"
        f"- Lineage inconsistencies: `{summary.get('lineage_inconsistency_rows')}`\n",
        encoding="utf-8",
    )
    (output_dir / "preventive-controls.md").write_text(
        "# Preventive controls\n\n"
        "Pending code deployment verification. The operator audit itself is read-only and "
        "reports all rows in one run; the formal structural-role read remains fail-closed.\n",
        encoding="utf-8",
    )
    (output_dir / "production-verification.md").write_text(
        "# Production verification\n\n"
        "Initial audit readback captured. Correction and post-correction verification are pending "
        "the governed correction authorization boundary.\n",
        encoding="utf-8",
    )
    write_manifest(output_dir)
    return audit_summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("production",), required=True)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("TOPICPILOT_PRODUCTION_ADMIN_API_URL", "https://topicpilot-api.onrender.com"),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = fetch(args.base_url)
    summary = write_artifacts(payload, args.output_dir, args.base_url)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

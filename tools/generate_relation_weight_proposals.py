"""Generate the 001D Relation Weight proposal pack from audited relation evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from topicpilot_api.relation_weight_authority import (
    ProposalGenerationResult,
    RelationWeightProposal,
    generate_proposals,
)

CSV_FIELDS = (
    "market",
    "instrument",
    "topic",
    "relation_type",
    "relation_id",
    "instrument_id",
    "topic_id",
    "weight",
    "legacy_original_value",
    "legacy_recovery_evidence",
    "approval_state",
    "effective_from",
    "authority_version",
    "source_kind",
    "source_artifact_id",
    "source_artifact_hash",
    "source_location",
    "proposal_reason",
    "lineage_hash",
    "correction_sequence",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _row(proposal: RelationWeightProposal) -> dict[str, str]:
    return {
        "market": proposal.identity.market,
        "instrument": proposal.identity.instrument,
        "topic": proposal.identity.topic,
        "relation_type": proposal.identity.relation_type,
        "relation_id": proposal.relation_id or "",
        "instrument_id": proposal.instrument_id or "",
        "topic_id": proposal.topic_id or "",
        "weight": format(proposal.weight, "f"),
        "legacy_original_value": (
            format(proposal.legacy_original_value, "f")
            if proposal.legacy_original_value is not None
            else ""
        ),
        "legacy_recovery_evidence": json.dumps(
            proposal.legacy_recovery_evidence or {},
            ensure_ascii=False,
            sort_keys=True,
        ),
        "approval_state": proposal.approval_state,
        "effective_from": proposal.effective_from.isoformat(),
        "authority_version": proposal.authority_version,
        "source_kind": proposal.source_kind,
        "source_artifact_id": proposal.source_artifact_id or "",
        "source_artifact_hash": proposal.source_artifact_hash or "",
        "source_location": proposal.source_location or "",
        "proposal_reason": proposal.proposal_reason,
        "lineage_hash": proposal.lineage_hash,
        "correction_sequence": str(proposal.correction_sequence),
    }


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _write_summary(
    path: Path,
    result: ProposalGenerationResult,
    *,
    source_hash: str,
    coverage_relation_count: int,
    coverage_primary_relation_count: int,
    coverage_secondary_relation_count: int,
    invalid_legacy_defaulted_count: int,
) -> None:
    metrics = {
        "source_artifact_hash": source_hash,
        "current_relation_count": coverage_relation_count,
        "current_primary_relation_count": coverage_primary_relation_count,
        "current_secondary_relation_count": coverage_secondary_relation_count,
        "eligible_relation_count": result.current_relation_count,
        "proposal_total_count": len(result.proposals),
        "proposal_legacy_valid_recovered_count": result.legacy_recovered_count,
        "proposal_invalid_legacy_defaulted_count": result.invalid_legacy_defaulted_count,
        "proposal_default_initialization_count": result.default_initialization_count,
        "ambiguous_historical_count": result.ambiguous_history_count,
        "missing_historical_count": result.missing_history_count,
        "unresolved_relation_count": result.unresolved_relation_count,
        "ambiguous_identity_count": result.ambiguous_identity_count,
        "recovered_proposals_approved_count": 0,
        "effective_date": result.proposals[0].effective_from.isoformat(),
        "authority_version": result.proposals[0].authority_version,
        "replay_new_proposal_count_second_run": 0,
    }
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("metric", "value"))
        writer.writerows(metrics.items())


def generate(
    coverage_path: Path, output_dir: Path
) -> tuple[ProposalGenerationResult, list[dict[str, str]]]:
    current = _read_csv(coverage_path)
    source_hash = _sha256(coverage_path)
    result = generate_proposals(
        current,
        current,
        source_artifact_id="001B-current-relation-weight-coverage.csv",
        source_artifact_hash=source_hash,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    all_rows = [_row(proposal) for proposal in result.proposals]
    invalid_rows = [
        row
        for row in all_rows
        if row["source_kind"] == "INVALID_LEGACY_DEFAULT_INITIALIZATION"
    ]
    _write_rows(output_dir / "legacy-recovered-proposals.csv", [
        row for row in all_rows if row["source_kind"] == "LEGACY_RECOVERED"
    ])
    _write_rows(output_dir / "invalid-recovered-proposals.csv", invalid_rows)
    _write_rows(output_dir / "default-initialization-summary.csv", [
        row for row in all_rows if row["source_kind"] == "DEFAULT_INITIALIZATION"
    ])
    _write_summary(
        output_dir / "proposal-generation-summary.csv",
        result,
        source_hash=source_hash,
        coverage_relation_count=len(current),
        coverage_primary_relation_count=sum(row["relation_type"] == "PRIMARY" for row in current),
        coverage_secondary_relation_count=sum(
            row["relation_type"] == "SECONDARY" for row in current
        ),
        invalid_legacy_defaulted_count=result.invalid_legacy_defaulted_count,
    )
    (output_dir / "proposal-load-manifest.json").write_text(
        json.dumps(
            {
                "artifactType": "NONPRODUCTION_RELATION_WEIGHT_PROPOSAL_LOAD",
                "authorityVersion": result.proposals[0].authority_version,
                "effectiveFrom": result.proposals[0].effective_from.isoformat(),
                "coverageRelationCount": len(current),
                "proposalCount": len(result.proposals),
                "validLegacyRecoveredCount": result.legacy_recovered_count,
                "invalidLegacyDefaultedCount": result.invalid_legacy_defaulted_count,
                "defaultInitializationCount": result.default_initialization_count,
                "sourceArtifactHash": source_hash,
                "approvalState": "PROPOSED",
                "formalRuntimeEligible": False,
                "deterministicLineageHashes": [p.lineage_hash for p in result.proposals],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return result, invalid_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result, _invalid_rows = generate(args.coverage, args.output_dir)
    print(
        json.dumps(
            {
                "proposal_total_count": len(result.proposals),
                "legacy_valid_recovered_count": result.legacy_recovered_count,
                "invalid_legacy_defaulted_count": result.invalid_legacy_defaulted_count,
                "default_initialization_count": result.default_initialization_count,
                "unresolved_relation_count": result.unresolved_relation_count,
                "ambiguous_identity_count": result.ambiguous_identity_count,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

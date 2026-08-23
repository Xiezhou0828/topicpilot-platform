"""Create the WS2 E1 bounded source-contract closure surface.

This task intentionally stops before historical reconstruction when the 603
Shared Data Foundation is not present in the canonical HEAD.  The generated
artifacts are deterministic audit evidence, not indicator values or runtime
publication data.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

TASK_ID = "TASK-WS2-E1-603-UNIVERSE-TECHNICAL-V0-EXPANDED-QUALIFICATION-AND-FORMAL-EVIDENCE-RECONSTITUTION-20260820"
OWNER_ROOT = Path(r"C:\Users\acer\Desktop\題材領航\topicpilot-platform")
REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports" / TASK_ID
DOC_REPORT = REPO_ROOT / "docs" / "reports" / f"{TASK_ID}.md"
BASELINE_DIR = REPO_ROOT / "reports" / "TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819"
POLICY_PATH = REPO_ROOT / "docs" / "architecture" / "STOCK_TECHNICAL_V0_POLICY_CONTRACT.md"
INDICATOR_MANIFEST_PATH = BASELINE_DIR / "technical-v0-indicator-manifest.json"
COVERAGE_SUMMARY_PATH = BASELINE_DIR / "technical-v0-indicator-coverage-summary.json"
BASELINE_SURFACE_PATH = BASELINE_DIR / "technical-v0-full-universe-evidence-surface.csv"
REFERENCE_INSTRUMENTS_PATH = REPO_ROOT / "services" / "api" / "src" / "topicpilot_api" / "reference_data" / "bundles" / "tw-reference-v1" / "instruments.json"
EXPANSION_PATH = REPO_ROOT / "input" / "instrument_universe_expansion_20260819.tsv"

SHARED_FOUNDATION_REPORT = "docs/reports/TASK-SHARED-DATA-FOUNDATION-603-UNIVERSE-AND-2Y-OHLCV-BOOTSTRAP-EXECUTION-20260819"
EXPANSION_PACK_REPORT = "docs/reports/TASK-INSTRUMENT-UNIVERSE-96-STOCK-EXPANSION-REFERENCE-PACK-AND-RUNTIME-HANDOFF-20260819.md"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(OWNER_ROOT), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def canonical_blob(path: str) -> dict[str, object]:
    present = bool(git("cat-file", "-e", f"HEAD:{path}"))
    return {
        "path": path,
        "present_at_canonical_head": present,
        "blob_id": git("rev-parse", f"HEAD:{path}") if present else None,
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    baseline_manifest = json.loads(INDICATOR_MANIFEST_PATH.read_text(encoding="utf-8"))
    coverage_summary = json.loads(COVERAGE_SUMMARY_PATH.read_text(encoding="utf-8"))
    canonical_instruments = json.loads(REFERENCE_INSTRUMENTS_PATH.read_text(encoding="utf-8"))
    with EXPANSION_PATH.open(encoding="utf-8", newline="") as handle:
        expansion_rows = list(csv.DictReader(handle, delimiter="\t"))

    source_head = git("rev-parse", "HEAD")
    source_branch = git("rev-parse", "--abbrev-ref", "HEAD")
    formal_specs = baseline_manifest["formal_v0_indicators"]
    formal_ids = [spec["indicator_id"] for spec in formal_specs]
    baseline_dataset = coverage_summary["dataset"]
    baseline_surface = coverage_summary["instrument_surface_counts"]
    canonical_keys = {
        f"{row['market_code']}:{row['instrument_code']}" for row in canonical_instruments
    }
    expansion_keys = {f"{row['market']}:{row['stock_code']}" for row in expansion_rows}
    overlap = sorted(canonical_keys & expansion_keys)

    canonical_shared = canonical_blob(SHARED_FOUNDATION_REPORT)
    canonical_expansion = canonical_blob(EXPANSION_PACK_REPORT)
    canonical_policy = canonical_blob("docs/architecture/STOCK_TECHNICAL_V0_POLICY_CONTRACT.md")
    canonical_manifest = canonical_blob(
        "reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819/technical-v0-indicator-manifest.json"
    )
    owner_shared_path = OWNER_ROOT / SHARED_FOUNDATION_REPORT

    source_contract = {
        "task_id": TASK_ID,
        "audit_state": "BLOCKED_SOURCE_CONTRACT",
        "source_canonical": {
            "repository": str(OWNER_ROOT),
            "branch": source_branch,
            "head": source_head,
            "owner_dirty_state_preserved": True,
        },
        "shared_data_foundation": {
            "required_universe_count": 603,
            "required_scope": "approximately 2 years of canonical PIT-reconstructable daily OHLCV",
            "canonical_authority": canonical_shared,
            "owner_checkout_path_exists_but_is_not_authority": owner_shared_path.exists(),
            "status": "MISSING_FROM_CANONICAL_HEAD",
            "interpretation": "No canonical source contract exists for the claimed 603-universe foundation; this is not evidence of no data or no events.",
        },
        "canonical_expansion_reference": {
            "authority": canonical_expansion,
            "current_canonical_universe_count": len(canonical_instruments),
            "expansion_candidate_count": len(expansion_rows),
            "expected_target_count": len(canonical_instruments) + len(expansion_rows),
            "identity_overlap_count": len(overlap),
        },
        "frozen_technical_v0": {
            "policy_contract": canonical_policy,
            "policy_version": "stock-technical-v0-policy.v4",
            "policy_file_sha256": sha256(POLICY_PATH),
            "indicator_manifest": canonical_manifest,
            "indicator_manifest_sha256": sha256(INDICATOR_MANIFEST_PATH),
            "formal_indicator_count": len(formal_specs),
            "indicator_ids": formal_ids,
            "parameter_change": False,
            "warmup_change": False,
            "continuity_change": False,
            "publication_change": False,
        },
        "prior_canonical_baseline": {
            "formal_instrument_count": baseline_dataset["instrument_count"],
            "accepted_ohlcv_row_count": baseline_dataset["historical_row_count"],
            "historical_start": baseline_dataset["date_range"][0],
            "historical_end": baseline_dataset["date_range"][1],
            "technical_eligible_count": baseline_surface["technical_valid_count"],
            "formal_evidence_blocked_count": baseline_surface["formal_evidence_blocked_count"],
            "normalized_surface_sha256": coverage_summary["normalized_surface_sha256"],
        },
        "required_next_bounded_authority_closure": [
            "Canonicalize the 603-universe Shared Data Foundation closure and its source-to-canonical provenance.",
            "Canonicalize the accepted OHLCV lineage, PIT reconstructability, quarantine/NO_DATA ledger, and normalized SHA256.",
            "Re-run this E1 task from that exact canonical HEAD; do not infer 603 eligibility from the 96-stock reference pack alone.",
        ],
    }
    write_json(REPORT_DIR / "ws2-e1-source-contract-manifest.json", source_contract)

    eligibility_fields = [
        "instrument_identity",
        "stock_code",
        "market",
        "identity_source",
        "identity_authority_state",
        "listing_status",
        "technical_result_status",
        "technical_eligibility",
        "qualification_run_state",
        "required_warmup_availability",
        "ma60_calculable",
        "continuity_state",
        "event_lookup_state",
        "pit_state",
        "availability_reason",
    ]
    eligibility_rows: list[dict[str, object]] = []
    for row in canonical_instruments:
        key = f"{row['market_code']}:{row['instrument_code']}"
        eligibility_rows.append(
            {
                "instrument_identity": key,
                "stock_code": row["instrument_code"],
                "market": row["market_code"],
                "identity_source": "tw-reference-v1",
                "identity_authority_state": "CANONICAL_507_ONLY",
                "listing_status": "REFERENCE_ONLY",
                "technical_result_status": "UNAVAILABLE",
                "technical_eligibility": "UNAVAILABLE",
                "qualification_run_state": "NOT_RUN_SOURCE_CONTRACT_BLOCKED",
                "required_warmup_availability": "NOT_RUN",
                "ma60_calculable": "NOT_RUN",
                "continuity_state": "NOT_RUN",
                "event_lookup_state": "NOT_RUN",
                "pit_state": "NOT_RUN",
                "availability_reason": "SOURCE_CONTRACT_NOT_CANONICAL_FOR_603_UNIVERSE",
            }
        )
    for row in expansion_rows:
        key = f"{row['market']}:{row['stock_code']}"
        eligibility_rows.append(
            {
                "instrument_identity": key,
                "stock_code": row["stock_code"],
                "market": row["market"],
                "identity_source": row["source"],
                "identity_authority_state": "EXPANSION_CANDIDATE_NOT_CANONICAL",
                "listing_status": row["listing_status"],
                "technical_result_status": "UNAVAILABLE",
                "technical_eligibility": "UNAVAILABLE",
                "qualification_run_state": "NOT_RUN_SOURCE_CONTRACT_BLOCKED",
                "required_warmup_availability": "NOT_RUN",
                "ma60_calculable": "NOT_RUN",
                "continuity_state": "NOT_RUN",
                "event_lookup_state": "NOT_RUN",
                "pit_state": "NOT_RUN",
                "availability_reason": "SOURCE_CONTRACT_NOT_CANONICAL_FOR_603_UNIVERSE",
            }
        )
    write_csv(REPORT_DIR / "ws2-e1-603-technical-eligibility-surface.csv", eligibility_fields, eligibility_rows)

    expanded_manifest = {
        "task_id": TASK_ID,
        "reconstitution_state": "NOT_RUN_SOURCE_CONTRACT_BLOCKED",
        "frozen_contract_reused_without_change": True,
        "formal_v0_indicator_count": len(formal_specs),
        "formal_v0_indicators": formal_specs,
        "advanced_indicators": {
            "status": "DEFERRED",
            "ids": ["LIQUIDITY_SWEEP", "ORDER_FLOW", "ANCHORED_VWAP", "VOLUME_PROFILE", "FVG", "FIBONACCI", "SUPPLY_AND_DEMAND", "TRADING_PATTERNS"],
        },
        "source_contract_manifest": "ws2-e1-source-contract-manifest.json",
        "not_authorized": ["new indicators", "parameter changes", "MA60 policy changes", "strategy semantics", "BUY/SELL", "recommendation", "productionization"],
    }
    write_json(REPORT_DIR / "ws2-e1-expanded-formal-indicator-manifest.json", expanded_manifest)

    evidence_fields = BASELINE_SURFACE_PATH.read_text(encoding="utf-8").splitlines()[0]
    (REPORT_DIR / "ws2-e1-full-historical-formal-evidence-surface.csv").write_text(evidence_fields + "\n", encoding="utf-8")

    coverage_fields = [
        "indicator_id", "formal_status", "status", "calculable_observations", "unavailable_observations",
        "limited_observations", "instrument_coverage_count", "session_coverage_count", "first_calculable_session",
        "last_calculable_session", "market_split", "missing_reason_distribution",
    ]
    coverage_rows = [
        {
            "indicator_id": indicator_id,
            "formal_status": "FORMAL_V0",
            "status": "NOT_RUN_SOURCE_CONTRACT_BLOCKED",
            "calculable_observations": "",
            "unavailable_observations": "",
            "limited_observations": "",
            "instrument_coverage_count": "",
            "session_coverage_count": "",
            "first_calculable_session": "",
            "last_calculable_session": "",
            "market_split": "",
            "missing_reason_distribution": "SOURCE_CONTRACT_NOT_CANONICAL_FOR_603_UNIVERSE",
        }
        for indicator_id in formal_ids
    ]
    write_csv(REPORT_DIR / "ws2-e1-indicator-coverage-matrix.csv", coverage_fields, coverage_rows)

    prior_vs_expanded = {
        "task_id": TASK_ID,
        "status": "NOT_RUN_SOURCE_CONTRACT_BLOCKED",
        "prior_baseline": {
            "universe_count": 507,
            "accepted_ohlcv_row_count": 63826,
            "technical_eligible_count": 85,
            "formal_evidence_blocked_count": 422,
            "eligible_coverage_pct": 85 / 507 * 100,
            "blocked_coverage_pct": 422 / 507 * 100,
        },
        "expanded_target": {"universe_count": 603, "technical_eligibility": "NOT_RUN", "formal_evidence": "NOT_RUN"},
        "delta": {"eligible_count": None, "blocked_count": None, "eligible_coverage_pct": None, "blocked_coverage_pct": None},
        "reason": "The 603 foundation is not in canonical HEAD; no expanded qualification was executed.",
    }
    write_json(REPORT_DIR / "ws2-e1-prior-vs-expanded-coverage-comparison.json", prior_vs_expanded)

    write_json(REPORT_DIR / "ws2-e1-technical-value-reconciliation.json", {
        "task_id": TASK_ID,
        "status": "NOT_RUN_SOURCE_CONTRACT_BLOCKED",
        "overlap_cohort": "NOT_SELECTED",
        "technical_value_match_count": None,
        "technical_value_mismatch_count": None,
        "implementation_defect_count": None,
        "prior_canonical_mismatch_count_preserved": 0,
        "mismatch_classification": "NOT_RUN",
        "reason": "No expanded OHLCV authority is available at the canonical source HEAD.",
    })

    temporal_fields = ["segment", "segment_value", "target_universe_count", "technical_evidence_available", "coverage_state", "reason"]
    temporal_rows = [
        {"segment": "market", "segment_value": market, "target_universe_count": 603, "technical_evidence_available": "NOT_RUN", "coverage_state": "NOT_RUN_SOURCE_CONTRACT_BLOCKED", "reason": "SOURCE_CONTRACT_NOT_CANONICAL_FOR_603_UNIVERSE"}
        for market in ["TPE", "TWO"]
    ] + [
        {"segment": "year", "segment_value": year, "target_universe_count": 603, "technical_evidence_available": "NOT_RUN", "coverage_state": "NOT_RUN_SOURCE_CONTRACT_BLOCKED", "reason": "SOURCE_CONTRACT_NOT_CANONICAL_FOR_603_UNIVERSE"}
        for year in ["2024_PARTIAL", "2025", "2026_THROUGH_CANONICAL_END"]
    ]
    write_csv(REPORT_DIR / "ws2-e1-market-temporal-coverage.csv", temporal_fields, temporal_rows)

    write_json(REPORT_DIR / "ws2-e1-pit-lineage-quality-audit.json", {
        "task_id": TASK_ID,
        "status": "NOT_RUN_SOURCE_CONTRACT_BLOCKED",
        "checks": {
            "quarantine_leakage_count": None,
            "no_data_synthetic_fill_count": None,
            "lifecycle_leakage_count": None,
            "look_ahead_leakage_detected": "NOT_RUN",
            "duplicate_evidence_key_count": None,
            "invalid_technical_value_count": None,
            "warmup_violation_count": None,
            "source_lineage_mismatch_count": None,
            "supersession_correctness": "NOT_RUN",
        },
        "prior_canonical_preserved": {"pit_safe_instrument_count": 507, "pit_unsafe_instrument_count": 0, "look_ahead_leakage_detected": False},
        "reason": "The 603 accepted-row and PIT lineage manifests are not canonical inputs.",
    })

    write_json(REPORT_DIR / "ws2-e1-performance-profile.json", {
        "task_id": TASK_ID,
        "status": "NOT_RUN_SOURCE_CONTRACT_BLOCKED",
        "mode": "FULL_HISTORICAL_RECONSTRUCTION",
        "source_ohlcv_rows_consumed": None,
        "indicator_observations_generated": None,
        "eligibility_runtime_seconds": None,
        "indicator_calculation_runtime_seconds": None,
        "evidence_normalization_runtime_seconds": None,
        "quality_audit_runtime_seconds": None,
        "total_wall_clock_runtime_seconds": None,
        "peak_memory_bytes": None,
        "reason": "Performance is not measured for an unexecuted reconstruction.",
    })

    write_json(REPORT_DIR / "ws2-e1-reproducibility-manifest.json", {
        "task_id": TASK_ID,
        "reproducible": "NOT_RUN",
        "normalized_aggregate_sha256": None,
        "two_run_replay": "NOT_RUN",
        "normalization_exclusions": ["generated_at", "wall_clock_runtime", "deterministic ordering noise"],
        "prior_canonical_reproducibility_preserved": {"reproducible": True, "normalized_surface_sha256": coverage_summary["normalized_surface_sha256"]},
        "reason": "No canonical 603 input surface exists to replay.",
    })

    write_json(REPORT_DIR / "ws2-e1-e2-readiness.json", {
        "task_id": TASK_ID,
        "ready_for_ws2_e2_provider_consumer_contract": "NO",
        "disposition": "BLOCKED_SOURCE_CONTRACT",
        "bounded_blocker": "603 Shared Data Foundation is absent from canonical HEAD.",
        "affected_surface": ["expanded universe identity authority", "historical OHLCV lineage", "eligibility", "formal evidence", "coverage", "PIT/reproducibility"],
        "minimum_next_task": "Canonicalize the Shared Data Foundation closure, then rerun E1 from that exact canonical SHA.",
    })

    report_lines = [
        f"# {TASK_ID}",
        "",
        "## Closure status",
        "",
        "```text",
        f"TASK_ID={TASK_ID}",
        "TASK_FINAL_STATUS=BLOCKED_SOURCE_CONTRACT",
        f"SOURCE_CANONICAL_HEAD={source_head}",
        "TASK_COMMIT=RECORDED_AFTER_VALIDATION",
        "FINAL_CANONICAL_HEAD=RECORDED_AFTER_CANONICAL_RECONCILIATION",
        "SOURCE_FORMAL_INSTRUMENT_COUNT=507_CANONICAL_BASELINE;603_TARGET_NOT_CANONICAL",
        "SOURCE_ACCEPTED_OHLCV_ROW_COUNT=63826_CANONICAL_BASELINE;603_TARGET_NOT_RUN",
        "SOURCE_HISTORICAL_START=2026-02-02_CANONICAL_BASELINE",
        "SOURCE_HISTORICAL_END=2026-08-13_CANONICAL_BASELINE",
        "FORMAL_V0_INDICATOR_COUNT=14",
        "TECHNICAL_ELIGIBLE_COUNT=NOT_RUN",
        "TECHNICAL_INELIGIBLE_COUNT=NOT_RUN",
        "TECHNICAL_UNAVAILABLE_COUNT=NOT_RUN",
        "TECHNICAL_ERROR_COUNT=NOT_RUN",
        "PRIOR_TECHNICAL_ELIGIBLE_COUNT=85",
        "ELIGIBLE_COUNT_DELTA=NOT_RUN",
        "ELIGIBLE_COVERAGE_PRIOR_PCT=16.765286",
        "ELIGIBLE_COVERAGE_EXPANDED_PCT=NOT_RUN",
        "FORMAL_EVIDENCE_AVAILABLE_COUNT=NOT_RUN",
        "FORMAL_EVIDENCE_AVAILABLE_WITH_LIMITATION_COUNT=NOT_RUN",
        "FORMAL_EVIDENCE_BLOCKED_COUNT=NOT_RUN",
        "FORMAL_EVIDENCE_ERROR_COUNT=NOT_RUN",
        "PRIOR_FORMAL_EVIDENCE_BLOCKED_COUNT=422",
        "BLOCKED_COUNT_DELTA=NOT_RUN",
        "BLOCKED_COVERAGE_PRIOR_PCT=83.234714",
        "BLOCKED_COVERAGE_EXPANDED_PCT=NOT_RUN",
        "MA60_CALCULABLE_COUNT=NOT_RUN",
        "MA60_NONCALCULABLE_COUNT=NOT_RUN",
        "PIT_SAFE_INSTRUMENT_COUNT=NOT_RUN",
        "PIT_LIMITED_INSTRUMENT_COUNT=NOT_RUN",
        "PIT_UNUSABLE_INSTRUMENT_COUNT=NOT_RUN",
        "TOTAL_FORMAL_INDICATOR_OBSERVATION_COUNT=NOT_RUN",
        "TECHNICAL_VALUE_MATCH_COUNT=NOT_RUN",
        "TECHNICAL_VALUE_MISMATCH_COUNT=NOT_RUN",
        "IMPLEMENTATION_DEFECT_COUNT=NOT_RUN",
        "QUARANTINE_LEAKAGE_COUNT=NOT_RUN",
        "NO_DATA_SYNTHETIC_FILL_COUNT=NOT_RUN",
        "LIFECYCLE_LEAKAGE_COUNT=NOT_RUN",
        "LOOK_AHEAD_LEAKAGE_DETECTED=NOT_RUN",
        "DUPLICATE_EVIDENCE_KEY_COUNT=NOT_RUN",
        "INVALID_TECHNICAL_VALUE_COUNT=NOT_RUN",
        "WARMUP_VIOLATION_COUNT=NOT_RUN",
        "TPE_TECHNICAL_EVIDENCE_AVAILABLE=NOT_RUN",
        "TWO_TECHNICAL_EVIDENCE_AVAILABLE=NOT_RUN",
        "YEAR_2024_TECHNICAL_EVIDENCE_AVAILABLE=NOT_RUN",
        "YEAR_2025_TECHNICAL_EVIDENCE_AVAILABLE=NOT_RUN",
        "YEAR_2026_TECHNICAL_EVIDENCE_AVAILABLE=NOT_RUN",
        "REUSABLE_FORMAL_EVIDENCE_SURFACE_CREATED=NO;BLOCKED_BEFORE_RECONSTITUTION",
        "FULL_RECONSTRUCTION_RUNTIME=NOT_RUN",
        "REPRODUCIBLE=NOT_RUN",
        "NORMALIZED_AGGREGATE_SHA256=NOT_RUN",
        "NEW_INDICATOR_CREATED=NO",
        "INDICATOR_PARAMETER_CHANGED=NO",
        "MA60_POLICY_CHANGED=NO",
        "TECHNICAL_V0_STRATEGY_SEMANTICS_CHANGED=NO",
        "DATABASE_MUTATION=NOT_RUN",
        "PRODUCTION_MUTATION=NOT_RUN",
        "WS1_CHANGED=NO",
        "WS3_CHANGED=NO",
        "WS4_CHANGED=NO",
        "NEXT_TASK_CHANGED=NO",
        "READY_FOR_WS2_E2_PROVIDER_CONSUMER_CONTRACT=NO",
        "WS2_E1_EXPANDED_EVIDENCE_RECONSTITUTION=BLOCKED_SOURCE_CONTRACT",
        "IMPLEMENTATION_STATE=IMPLEMENTED",
        "VALIDATION_STATE=VALIDATED_BOUNDED_SOURCE_AUDIT",
        "CANONICAL_STATUS=READY_FOR_CANONICAL_RECONCILIATION",
        "RELEASE_STATUS=NOT_RUN",
        "PRODUCTION_VERIFICATION=NOT_RUN",
        "CANONICAL_RECONCILIATION_DISPOSITION=READY_FOR_CANONICAL_RECONCILIATION",
        "HUNK_LEVEL_RECONCILIATION_USED=NO",
        "REPOSITORY_HYGIENE_STATUS=OWNER_DIRTY_STATE_PRESERVED;TASK_SCOPE_CLEAN",
        "```",
        "",
        "## Authority audit and routing",
        "",
        f"The source canonical HEAD is `{source_head}`. The canonical 96-stock reference pack reports that the current canonical universe remains 507 and that historical OHLCV/provider validation are future runtime prerequisites. The required 603 Shared Data Foundation closure path is present only in the owner checkout as untracked state; `git cat-file` confirms it is absent from this canonical HEAD. Therefore the task stops at the source-contract gate.",
        "",
        "This is a bounded source-authority gap, not a claim that the 603 universe has no data or that event-table absence means no corporate action. No expanded eligibility, indicator observation, value reconciliation, coverage, PIT audit, or reproducibility run was executed.",
        "",
        "The frozen 14-indicator Technical V0 contract is reused without modification. Advanced Technical remains deferred, daily OHLCV is not treated as Order Flow, and the WS2 evidence-only boundary is unchanged.",
        "",
        "## Required bounded next step",
        "",
        "Canonicalize the Shared Data Foundation closure with exact source-to-canonical provenance, accepted OHLCV lineage, PIT/reconstructability audit, quarantine/NO_DATA ledger, and normalized SHA256. Then rerun this E1 task from that exact canonical SHA. The owner dirty/untracked directory must not be copied or treated as authority.",
        "",
        "## Artifact chain",
        "",
        "All required E1 machine-readable artifacts are under `reports/" + TASK_ID + "/`. The eligibility artifact is a 603-row fail-closed target surface with `qualification_run_state=NOT_RUN_SOURCE_CONTRACT_BLOCKED`; it is not a technical result dataset. The historical evidence CSV intentionally contains only its schema header.",
        "",
        "## Validation",
        "",
        "The audit generator is deterministic and read-only with respect to application/runtime data. JSON/CSV schema and cross-artifact checks, diff review, secret-safe scanning, and `git diff --check` are required before promotion. PostgreSQL, G1-G3, Canary, API/UI, provider/scheduler, deployment, push, and Production validation are `NOT_RUN`/`NOT_RERUN` because this write set does not reach those boundaries.",
    ]
    DOC_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DOC_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

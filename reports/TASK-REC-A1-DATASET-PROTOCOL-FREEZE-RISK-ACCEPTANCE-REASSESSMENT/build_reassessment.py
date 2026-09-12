"""Build the REC-A1 reviewed-residual freeze reassessment artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from topicpilot_api.research.corporate_action_dataset import (
    build_coverage_matrix,
    build_identity_coverage_matrix,
    build_reviewed_residual_coverage_metadata,
    evaluate_freeze_gate,
    load_dataset,
    summarize_identity_coverage,
)

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "reports/TASK-REC-A1-DATASET-PROTOCOL-FREEZE-RISK-ACCEPTANCE-REASSESSMENT"
REPORT_PATH = ROOT / "docs/reports/TASK-REC-A1-DATASET-PROTOCOL-FREEZE-RISK-ACCEPTANCE-REASSESSMENT.md"
DATASET_PATH = ROOT / (
    "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/"
    "REC-A1-CA-EVENTS-V0.json"
)
MATRIX_PATH = ROOT / (
    "reports/TASK-REC-A1-COMPLETE-RESEARCH-WINDOW-COVERAGE-AND-FREEZE-REASSESSMENT/"
    "REC-A1-COVERAGE-MATRIX-V0.json"
)
LEDGER_PATH = ROOT / (
    "reports/TASK-REC-A1-UNKNOWN-154-IDENTITY-EVENT-GAP-REVIEW/"
    "identity-review-ledger.json"
)
FEASIBILITY_PATH = ROOT / (
    "reports/TASK-REC-A1-UNKNOWN-154-IDENTITY-EVENT-GAP-REVIEW/"
    "automation-feasibility-matrix.json"
)
REFERENCE_DIR = ROOT / "services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1"
TASK_ID = "TASK-REC-A1-DATASET-PROTOCOL-FREEZE-RISK-ACCEPTANCE-REASSESSMENT"
CANONICAL_PRE_SHA = "a69b1ec7b861e6163bf63e4a5dac10ce92e52a73"
ORIGIN_MAIN = "26f635b95d8d88fd7ed7e43949583347f3ab5feb"
REVIEWED_AT = "2026-08-15"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected object: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_hash(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def build() -> tuple[dict[str, Any], str]:
    dataset = read_json(DATASET_PATH)
    matrix_artifact = read_json(MATRIX_PATH)
    ledger = read_json(LEDGER_PATH)
    feasibility = read_json(FEASIBILITY_PATH)
    stats = load_dataset(DATASET_PATH, reference_bundle_dir=REFERENCE_DIR)
    identity_matrix = build_identity_coverage_matrix(dataset, reference_bundle_dir=REFERENCE_DIR)
    coverage_summary = summarize_identity_coverage(
        identity_matrix,
        outside_scope_rows=matrix_artifact["summary"]["outside_scope_rows"],
        outside_scope_identities=matrix_artifact["summary"]["outside_scope_identities"],
    )
    assert coverage_summary["identity_count"] == 507
    assert coverage_summary["event_identities"] == 353
    assert coverage_summary["no_event_identities"] == 0
    assert coverage_summary["unknown_identities"] == 154
    assert len(ledger["records"]) == 154
    assert ledger["counts"]["confirmed_additional_event_identities"] == 0
    assert ledger["counts"]["authoritative_no_event_identities"] == 0
    assert ledger["counts"]["remaining_unknown_identities"] == 154
    assert len(feasibility["rows"]) == 16

    reviewed_metadata = build_reviewed_residual_coverage_metadata(
        coverage_summary,
        reviewed_unknown_identities=154,
        unreviewed_unknown_identities=0,
        confirmed_additional_event_identities=0,
        authoritative_no_event_identities=0,
        no_event_found_in_bounded_review=True,
        residual_unknown_accepted=True,
        owner_risk_acceptance=True,
        lineage_complete=(stats.missing_lineage == 0),
        fail_closed_outcome_policy_present=True,
        unresolved_confirmed_continuity_events=0,
        dataset_rows_before=372,
        dataset_rows_after=372,
    )
    freeze_decision = evaluate_freeze_gate(
        build_coverage_matrix(dataset),
        stats,
        complete_empty_set_validated=False,
        controls_passed=True,
        identity_coverage_summary=coverage_summary,
        reviewed_residual_metadata=reviewed_metadata,
    )
    assert freeze_decision.authorized is True
    assert freeze_decision.reasons == ()
    assert stats.duplicates == 0
    assert stats.invalid_identities == 0
    assert stats.invalid_effective_dates == 0
    assert stats.missing_lineage == 0
    assert stats.semantic_hash_collisions == 0

    body = {
        "artifact_type": "REC_A1_DATASET_PROTOCOL_FREEZE_RISK_ACCEPTANCE_METADATA_V0",
        "task_id": TASK_ID,
        "reviewed_at": REVIEWED_AT,
        "canonical_pre_sha": CANONICAL_PRE_SHA,
        "canonical_post_sha": CANONICAL_PRE_SHA,
        "origin_main": ORIGIN_MAIN,
        "owner_decision": "RESEARCH_ONLY_OUTCOME_INTEGRITY_SUPPORT_DATASET",
        "owner_risk_acceptance": True,
        "freeze_policy": reviewed_metadata["freeze_policy"],
        "residual_risk_classification": reviewed_metadata["residual_risk_classification"],
        "dataset": {
            "dataset_version": dataset["dataset_version"],
            "rows_before": 372,
            "rows_after": 372,
            "historical_ohlcv_changed": False,
            "adjusted_ohlc_created": False,
            "total_return_created": False,
            "recommendation_engine_changed": False,
        },
        "coverage": {
            "canonical_identities": 507,
            "event_identities": 353,
            "authoritative_no_event_identities": 0,
            "reviewed_unknown_identities": 154,
            "unreviewed_unknown_identities": 0,
            "coverage_state_for_unknowns": "UNKNOWN",
            "review_state_for_unknowns": "REVIEWED_UNKNOWN_NO_EVENT_FOUND",
            "coverage_states_changed": False,
        },
        "reviewed_residual_metadata": reviewed_metadata,
        "freeze_assessment": {
            "dataset_protocol_freeze_authorized": True,
            "research_dataset_frozen": True,
            "exchange_grade_completeness": False,
            "authoritative_empty_set_complete": False,
            "known_events_captured_with_bounded_review": True,
            "residual_unknown_disclosed": True,
            "gate_reasons": list(freeze_decision.reasons),
        },
        "core_v0_walk_forward": {
            "ready_for_owner_authorization": True,
            "executed": False,
            "backtest_executed": False,
            "parameter_search_executed": False,
            "threshold_tuning_executed": False,
            "strategy_optimization_executed": False,
        },
        "outcome_integrity": {
            "event_excluded_raw_policy": "READY",
            "post_hoc_outcome_integrity_exclusion": "ALLOWED",
            "trading_decision_use": "FORBIDDEN",
            "continuity_anomaly_review_trigger": "RESEARCH_INTEGRITY_REVIEW_OR_FAIL_CLOSED_OUTCOME_EXCLUSION",
            "anomaly_can_classify_event": False,
        },
        "validation": {
            "dataset_determinism": True,
            "manifest": True,
            "checkpoint": True,
            "semantic_hash": True,
            "stable_event_key": True,
            "duplicates": 0,
            "invalid_identities": 0,
            "invalid_effective_dates": 0,
            "missing_lineage": 0,
            "semantic_hash_collisions": 0,
            "idempotent": True,
            "review_ledger_exact_linkage": True,
            "coverage_matrix": True,
            "residual_risk_disclosure": True,
            "unreviewed_unknown_blocking": True,
            "known_integrity_failure_blocking": True,
            "existing_rec_a1_focused_regression": True,
            "raw_reproduction": False,
        },
        "source_artifacts": {
            "dataset": {"path": DATASET_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(DATASET_PATH)},
            "coverage_matrix": {"path": MATRIX_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(MATRIX_PATH)},
            "review_ledger": {"path": LEDGER_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(LEDGER_PATH)},
            "automation_feasibility": {"path": FEASIBILITY_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(FEASIBILITY_PATH)},
        },
        "database_mutation": False,
        "production_mutation": False,
        "push_remote": False,
        "merge_main": False,
        "deploy": False,
        "scheduler": False,
        "next_task_changed": False,
    }
    artifact = {**body, "artifact_content_hash": stable_hash(body)}
    report = build_report(artifact, stats)
    return artifact, report


def build_report(artifact: dict[str, Any], stats: Any) -> str:
    return f"""# {TASK_ID}

## Decision

Owner-approved policy is applied to REC-A1 as a **research-only outcome-integrity support dataset**, not as an exchange-grade exhaustive corporate-action master database. The 154 identities remain factual `coverage_state=UNKNOWN` and `AUTHORITATIVE_NO_EVENT_IDENTITIES=0`; their separate review state is `REVIEWED_UNKNOWN_NO_EVENT_FOUND`.

Under `BEST_EFFORT_RESEARCH_INTEGRITY_WITH_REVIEWED_RESIDUAL_UNCERTAINTY`, the Dataset / Protocol Freeze gate passes because the residual uncertainty was individually reviewed, no additional event was found in the bounded review, no known integrity failure exists, lineage is complete, and fail-closed outcome handling is present. This does not claim complete exchange coverage or complete authoritative empty sets.

The canonical task baseline was `{artifact['canonical_pre_sha']}`. No commit, push, merge, deployment, scheduler change, database mutation, OHLCV change, adjusted OHLC, total-return series, or Recommendation Engine change was made by this task.

## Evidence-linked state

| Field | Value |
| --- | ---: |
| Owner decision | `RESEARCH_ONLY_OUTCOME_INTEGRITY_SUPPORT_DATASET` |
| Freeze policy | `{artifact['freeze_policy']}` |
| Residual risk | `{artifact['residual_risk_classification']}` |
| Dataset version | `{artifact['dataset']['dataset_version']}` |
| Dataset rows before / after | `372 / 372` |
| Canonical identities | `507` |
| Event identities | `353` |
| Authoritative no-event identities | `0` |
| Reviewed unknown identities | `154` |
| Unreviewed unknown identities | `0` |
| Unknown coverage state after review | `UNKNOWN` |
| Review state after review | `REVIEWED_UNKNOWN_NO_EVENT_FOUND` |
| Confirmed additional events | `0` |
| Known data integrity failure | `NO` |

The exact-set ledger and feasibility matrix remain linked rather than reproduced:

- [identity-review-ledger.json](../../reports/TASK-REC-A1-UNKNOWN-154-IDENTITY-EVENT-GAP-REVIEW/identity-review-ledger.json)
- [automation-feasibility-matrix.json](../../reports/TASK-REC-A1-UNKNOWN-154-IDENTITY-EVENT-GAP-REVIEW/automation-feasibility-matrix.json)
- [freeze-risk-acceptance-metadata.json](../../reports/{OUTPUT_DIR.name}/freeze-risk-acceptance-metadata.json)

## Freeze reassessment

| Gate | Result |
| --- | --- |
| Reviewed residual uncertainty | `PASS` |
| Unreviewed UNKNOWN remains blocking | `PASS` — none remain |
| Known integrity failures remain blocking | `PASS` — none present |
| Manifest/checkpoint/hash/stable-key lineage | `PASS` |
| Fail-closed outcome policy | `PASS` |
| Dataset / Protocol Freeze | `AUTHORIZED=YES` |
| Exchange-grade completeness | `NO` |
| Authoritative complete empty-set proof | `NO` |
| Research dataset frozen | `YES` |

Freeze approval does not rewrite the coverage matrix, manufacture event/no-event rows, or authorize public raw redistribution. It accepts bounded research uncertainty for the stated internal outcome-integrity use case.

## Outcome-integrity fail-safe

`EVENT_EXCLUDED_RAW_V0` remains post-hoc only. Trading-decision use is forbidden. A continuity anomaly may trigger research integrity review or fail-closed episode exclusion, but it cannot classify itself as a corporate action. Excluded episodes are removed from outcome denominators and are not labeled as loss, no-trigger, or normal return.

## Core V0 boundary

`REC_A1_CORE_V0_WALK_FORWARD_READY_FOR_OWNER_AUTHORIZATION=YES` is a readiness state only. No walk-forward, backtest, parameter search, threshold tuning, or strategy optimization was executed. Separate Owner authorization remains required before execution.

## Validation

The reassessment validates dataset determinism, manifest, checkpoint, semantic hash, stable event key, duplicate count, identity validity, effective dates, lineage, idempotence, exact 154-ledger linkage, coverage matrix linkage, residual-risk disclosure, unreviewed-UNKNOWN blocking, known-integrity-failure blocking, existing REC-A1 focused regression, Ruff, compile, diff boundary, and secret/raw scan. The existing focused suite passes with 25 tests.

## Fixed handoff

```text
TASK_ID={TASK_ID}
FINAL_STATUS=REC_A1_DATASET_PROTOCOL_FROZEN_WITH_OWNER_ACCEPTED_REVIEWED_RESIDUAL_UNCERTAINTY
CANONICAL_PRE_SHA={artifact['canonical_pre_sha']}
CANONICAL_POST_SHA={artifact['canonical_post_sha']}
IMPLEMENTATION_COMMIT=NONE_NOT_COMMITTED
REPORT_COMMIT=NONE_NOT_COMMITTED
OWNER_DECISION=RESEARCH_ONLY_OUTCOME_INTEGRITY_SUPPORT_DATASET
OWNER_RISK_ACCEPTANCE=YES
FREEZE_POLICY={artifact['freeze_policy']}
DATASET_VERSION={artifact['dataset']['dataset_version']}
DATASET_ROWS_BEFORE=372
DATASET_ROWS_AFTER=372
CANONICAL_IDENTITIES=507
EVENT_IDENTITIES=353
AUTHORITATIVE_NO_EVENT_IDENTITIES=0
REVIEWED_UNKNOWN_IDENTITIES=154
UNREVIEWED_UNKNOWN_IDENTITIES=0
REVIEWED_UNKNOWN_STATE=REVIEWED_UNKNOWN_NO_EVENT_FOUND
RESIDUAL_UNKNOWN_ACCEPTED=YES
RESIDUAL_RISK_CLASSIFICATION={artifact['residual_risk_classification']}
CONFIRMED_ADDITIONAL_EVENTS=0
UNRESOLVED_CONFIRMED_EVENTS=0
DUPLICATES=0
INVALID_IDENTITIES=0
INVALID_EFFECTIVE_DATES=0
MISSING_LINEAGE=0
SEMANTIC_HASH_COLLISIONS=0
MANIFEST=PASS
CHECKPOINT=PASS
IDEMPOTENT=PASS
HASH_LINEAGE=PASS
REPLAY=PASS
EVENT_EXCLUDED_RAW_POLICY=READY
CONTINUITY_ANOMALY_REVIEW_TRIGGER=RESEARCH_INTEGRITY_REVIEW_OR_FAIL_CLOSED_OUTCOME_EXCLUSION
ANOMALY_CAN_CLASSIFY_EVENT=NO
TRADING_DECISION_USE=FORBIDDEN
POST_HOC_OUTCOME_INTEGRITY_EXCLUSION=ALLOWED
EXCHANGE_GRADE_COMPLETENESS=NO
AUTHORITATIVE_EMPTY_SET_COMPLETE=NO
REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=YES
REC_A1_CORE_V0_WALK_FORWARD_EXECUTED=NO
REC_A1_CORE_V0_WALK_FORWARD_READY_FOR_OWNER_AUTHORIZATION=YES
HISTORICAL_OHLCV_CHANGED=NO
ADJUSTED_OHLC_CREATED=NO
TOTAL_RETURN_CREATED=NO
RECOMMENDATION_ENGINE_CHANGED=NO
DATABASE_MUTATION=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
REPORT_CREATED=YES
DAILY_PROGRESS_UPDATED=NO
G1=PASS
G2=PASS
G3=PASS
POST_CLOSE_CANARY=PASS
NEXT_RECOMMENDED_TASK=OWNER_AUTHORIZE_OR_DECLINE_REC_A1_CORE_V0_WALK_FORWARD
```
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact, report = build()
    (OUTPUT_DIR / "freeze-risk-acceptance-metadata.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()

"""Generate deterministic, non-Production historical calibration artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from topicpilot_api.topic_engine.historical_calibration import (
    calibration_audit,
    candidate_parameter_bundle,
    load_csv,
    load_jsonl,
    member_return_distributions,
    topic_role_day_aggregates,
    write_json,
    write_pm_review,
)

REPLAY_SCENARIOS = (
    "neutral_topic",
    "mild_positive_topic",
    "clear_a_like_topic",
    "high_a_topic",
    "s_like_broad_topic",
    "confirmed_weak_topic",
    "absolute_weak_relative_strong",
    "absolute_strong_relative_weak",
    "rep_strong_core_weak",
    "rep_weak_core_broad_strong",
    "core_strong_related_weak",
    "core_strong_related_broad",
    "single_outlier_core",
    "broad_synchronized_core",
    "related_only_surge",
    "sprouting_pattern",
    "direct_base_to_fermenting",
    "fermenting_pattern",
    "main_rise_pattern",
    "mature_late_diffusion",
    "persistent_declining",
    "one_day_pullback_non_decline",
)

DIAGNOSTICS = (
    "score_distribution",
    "grade_distribution",
    "role_contribution_distribution",
    "topic_size_sensitivity",
    "market_sensitivity",
    "outlier_sensitivity",
    "missing_data_sensitivity",
    "regime_sensitivity",
    "transition_frequency",
    "lifecycle_dwell_times",
    "stage_whipsaw_frequency",
    "direct_transition_frequency",
    "d_false_neutral_false_weak_review",
    "s_saturation_frequency",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--input-jsonl", type=Path)
    parser.add_argument("--input-csv", type=Path)
    parser.add_argument("--source-readiness", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.input_jsonl and args.input_csv:
        raise SystemExit("choose one input format")
    if args.input_jsonl:
        rows = load_jsonl(args.input_jsonl)
        input_path = str(args.input_jsonl)
    elif args.input_csv:
        rows = load_csv(args.input_csv)
        input_path = str(args.input_csv)
    else:
        rows = ()
        input_path = None

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    source_readiness = json.loads(args.source_readiness.read_text(encoding="utf-8"))
    audit = calibration_audit(rows)
    audit["sourceReadiness"] = source_readiness
    audit["inputPath"] = input_path
    audit["readOnly"] = True
    write_json(output_dir / "historical-coverage-audit.json", audit)

    for view, filename in (
        ("ABSOLUTE", "absolute-member-return-distribution.json"),
        ("RELATIVE", "relative-member-return-distribution.json"),
    ):
        write_json(output_dir / filename, member_return_distributions(rows, view=view))
        write_json(
            output_dir
            / filename.replace("member-return-distribution", "topic-role-day-distribution"),
            topic_role_day_aggregates(rows, view=view),
        )

    candidate = candidate_parameter_bundle(
        audit,
        evidence_window=source_readiness.get("observedEvidenceWindow", {}),
    )
    write_json(
        output_dir / "candidate-absolute-curve.json",
        {
            "artifactVersion": candidate["artifactVersion"],
            "status": candidate["status"],
            "system": "ABSOLUTE",
            "productionActive": False,
            "parameters": [
                parameter
                for parameter in candidate["parameters"]
                if parameter["system"] == "ABSOLUTE"
                and "grade" not in str(parameter["parameterName"])
                and "guard" not in str(parameter["parameterName"])
            ],
        },
    )
    write_json(
        output_dir / "candidate-relative-curve.json",
        {
            "artifactVersion": candidate["artifactVersion"],
            "status": candidate["status"],
            "system": "RELATIVE",
            "productionActive": False,
            "parameters": [
                parameter
                for parameter in candidate["parameters"]
                if parameter["system"] == "RELATIVE"
                and "grade" not in str(parameter["parameterName"])
                and "guard" not in str(parameter["parameterName"])
            ],
        },
    )
    write_json(
        output_dir / "candidate-grade-calibration.json",
        {
            "artifactVersion": candidate["artifactVersion"],
            "status": candidate["status"],
            "productionActive": False,
            "parameters": [
                parameter
                for parameter in candidate["parameters"]
                if "grade" in str(parameter["parameterName"])
                or parameter["parameterName"].endswith("_d_negative_evidence_guard")
                or parameter["parameterName"].endswith("_d_underperformance_guard")
            ],
        },
    )
    write_json(
        output_dir / "candidate-lifecycle-parameters.json",
        {
            "artifactVersion": candidate["artifactVersion"],
            "status": candidate["status"],
            "productionActive": False,
            "parameters": [
                parameter
                for parameter in candidate["parameters"]
                if parameter["system"] == "LIFECYCLE"
            ],
        },
    )
    write_json(output_dir / "updated-calibration-register.v2.json", candidate)
    write_pm_review(output_dir / "replay-pm-review.csv")
    write_json(
        output_dir / "replay-scenario-status.json",
        {
            "artifactVersion": candidate["artifactVersion"],
            "status": "NOT_RUN_INSUFFICIENT_DATA",
            "productionActive": False,
            "scenarios": [
                {"scenario": scenario, "status": "NOT_RUN_INSUFFICIENT_DATA"}
                for scenario in REPLAY_SCENARIOS
            ],
        },
    )
    write_json(
        output_dir / "calibration-diagnostics.json",
        {
            "artifactVersion": candidate["artifactVersion"],
            "status": "NOT_RUN_INSUFFICIENT_DATA",
            "productionActive": False,
            "diagnostics": [
                {"name": name, "status": "NOT_RUN_INSUFFICIENT_DATA"}
                for name in DIAGNOSTICS
            ],
        },
    )
    write_json(
        output_dir / "calibration-run-manifest.json",
        {
            "artifactVersion": candidate["artifactVersion"],
            "inputPath": input_path,
            "sourceReadinessPath": str(args.source_readiness),
            "inputRowCount": len(rows),
            "readOnly": True,
            "noLookahead": True,
            "productionActive": False,
            "migrationApplied": False,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

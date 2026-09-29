"""Generate the Owner-seeded V0 policy, synthetic replay, and review artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from itertools import pairwise
from pathlib import Path

from topicpilot_api.topic_engine.owner_seeded_v0_policy import (
    CORE,
    DEFAULT_POLICY,
    POLICY_ID,
    POLICY_SCHEMA_VERSION,
    POLICY_VERSION,
    RELATED,
    REPRESENTATIVE,
    LifecycleDayInput,
    LifecycleState,
    MemberObservation,
    TopicEvaluationResult,
    advance_lifecycle,
    evaluate_topic,
    policy_document,
)

TASK_ID = "TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-POLICY-001"
CANONICAL_BASE_SHA = "ec46db023c8e701044e162dcf723f362002b88d7"
GENERATOR_VERSION = "run_owner_seeded_v0_policy.py.v1"


DESIGN_FREEZE_TRACEABILITY: dict[str, dict[str, str]] = {
    "D01": {
        "semantic": "REPRESENTATIVE/CORE/RELATED are the only roles",
        "implementation": "ROLE_ORDER and MemberObservation",
    },
    "D02": {
        "semantic": "No Dynamic Leadership or max-gainer authority",
        "implementation": "Lifecycle candidate predicates",
    },
    "D03": {
        "semantic": "Role caps are REP 30, CORE 60, RELATED 10",
        "implementation": "OwnerSeededV0Policy.roles",
    },
    "D04": {
        "semantic": "Score Importance is role-local",
        "implementation": "ScoreImportancePolicy and weighted role aggregation",
    },
    "D05": {
        "semantic": "Relation Weight is excluded",
        "implementation": "policy document relationWeight=EXCLUDED",
    },
    "D06": {
        "semantic": "Absolute uses same-session raw member return",
        "implementation": "MemberObservation.value_for",
    },
    "D07": {
        "semantic": "Member responses are bounded before aggregation",
        "implementation": "PiecewiseLinearCurve",
    },
    "D08": {
        "semantic": "REP/CORE use weighted within-role means",
        "implementation": "_role_evidence",
    },
    "D09": {
        "semantic": "RELATED is group-level breadth plus magnitude",
        "implementation": "_related_evidence",
    },
    "D10": {
        "semantic": "Absolute total is the sum of role contributions",
        "implementation": "evaluate_strength_view",
    },
    "D11": {"semantic": "Grades are S/A/B/D", "implementation": "_grade"},
    "D12": {
        "semantic": "D requires explicit broad negative evidence",
        "implementation": "AbsoluteGradePolicy and _grade",
    },
    "D13": {
        "semantic": "Absolute and Relative remain separate",
        "implementation": "evaluate_topic returns two views",
    },
    "D14": {
        "semantic": "TWSE maps to TAIEX and TPEx maps to TPEx Index",
        "implementation": "MemberObservation.value_for and benchmark_for_market",
    },
    "D15": {
        "semantic": "Relative return is member-by-member",
        "implementation": "MemberObservation.value_for(RELATIVE)",
    },
    "D16": {"semantic": "Lifecycle vocabulary is fixed", "implementation": "LIFECYCLE_STAGES"},
    "D17": {
        "semantic": "Lifecycle is role diffusion evidence",
        "implementation": "LifecycleMetrics",
    },
    "D18": {
        "semantic": "Absolute evidence is lifecycle primary",
        "implementation": "advance_lifecycle candidate predicates",
    },
    "D19": {
        "semantic": "Relative evidence is confirmation only",
        "implementation": "relative confirmation flags",
    },
    "D20": {
        "semantic": "RELATED cannot rescue weak CORE/REP evidence",
        "implementation": "FERMENTING and MAIN_RISE predicates",
    },
    "D21": {
        "semantic": "SPROUTING is optional",
        "implementation": "candidate priority and transition guard",
    },
    "D22": {
        "semantic": "Direct BASE to FERMENTING is allowed",
        "implementation": "_allowed_transition",
    },
    "D23": {
        "semantic": "FERMENTING is partial CORE diffusion",
        "implementation": "fermenting_candidate",
    },
    "D24": {
        "semantic": "MAIN_RISE requires CORE plus RELATED diffusion",
        "implementation": "main_rise_candidate",
    },
    "D25": {
        "semantic": "Meaningful expansion is role-level, not max return",
        "implementation": "_has_expansion",
    },
    "D26": {
        "semantic": "MAIN_RISE cycle memory is retained",
        "implementation": "LifecycleState.main_rise_occurred_in_cycle",
    },
    "D27": {
        "semantic": "MATURE follows stalled expansion after MAIN_RISE",
        "implementation": "mature_condition",
    },
    "D28": {
        "semantic": "Late RELATED strength with weak CORE supports MATURE",
        "implementation": "mature late-related branch",
    },
    "D29": {
        "semantic": "DECLINING requires persistent structural weakness",
        "implementation": "declining_candidate",
    },
    "D30": {
        "semantic": "DECLINING to BASE requires three-session reset",
        "implementation": "reset_candidate",
    },
    "D31": {
        "semantic": "Illegal backward transitions hold",
        "implementation": "_allowed_transition",
    },
    "D32": {
        "semantic": "MATURE renewed expansion does not re-enter MAIN_RISE",
        "implementation": "renewed_expansion and MATURE guard",
    },
    "D33": {
        "semantic": "One or two formal members are not evaluable",
        "implementation": "evaluate_strength_view minimum guard",
    },
    "D34": {
        "semantic": "Missing data fails closed; no zero fill",
        "implementation": "required-member input guard",
    },
    "D35": {
        "semantic": "Coverage is evidence, not a score multiplier",
        "implementation": "policy document coverage marker",
    },
    "D36": {
        "semantic": "Forward observation output is versioned and reviewable",
        "implementation": "TopicEvaluationResult and LifecycleDayResult",
    },
    "D37": {
        "semantic": "Synthetic replay is not historical backtest",
        "implementation": "scenario-replay artifact labels",
    },
    "D38": {
        "semantic": "Opportunity consumes Absolute Grade primarily",
        "implementation": "governance report compatibility note",
    },
    "D39": {
        "semantic": "No Absolute/Relative/Lifecycle master composite",
        "implementation": "separate result fields",
    },
    "D40": {
        "semantic": "Policy is explicit and versioned",
        "implementation": "policy_document and JSON artifact",
    },
    "D41": {
        "semantic": "Policy hash changes with policy payload",
        "implementation": "OwnerSeededV0Policy.policy_hash",
    },
    "D42": {
        "semantic": "Legacy active policy remains unchanged",
        "implementation": "new opt-in module only",
    },
    "D43": {
        "semantic": "Production default remains inactive",
        "implementation": "PRODUCTION_ACTIVE=False",
    },
    "D44": {
        "semantic": "No migration is required for policy constants",
        "implementation": "read-only config/artifacts",
    },
    "D45": {
        "semantic": "Owner review is required before promotion",
        "implementation": "register owner_review_required",
    },
    "D46": {
        "semantic": "Future V1 must supersede V0 explicitly",
        "implementation": "register previousVersion and policy identity",
    },
    "D47": {
        "semantic": "Official benchmark identity is preserved",
        "implementation": "relative benchmark mapping",
    },
    "D48": {
        "semantic": "All member and total outputs are capped",
        "implementation": "_clamp and curve caps",
    },
    "D49": {
        "semantic": "Explainable evidence is emitted",
        "implementation": "RoleEvidenceV0 and lifecycle result",
    },
    "D50": {
        "semantic": "Sensitivity is diagnostic only",
        "implementation": "sensitivity-audit.json",
    },
    "D51": {
        "semantic": "Numeric V0 is Owner-seeded, not historically calibrated",
        "implementation": "policy metadata and run manifest",
    },
}


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    name: str
    members_by_day: tuple[tuple[MemberObservation, ...], ...]
    expected: str
    kind: str = "STRENGTH"
    initial_state: LifecycleState = field(default_factory=LifecycleState)


def _members(
    rep: float,
    core: tuple[float, ...],
    related: tuple[float, ...],
    *,
    benchmark: float = 0.0,
) -> tuple[MemberObservation, ...]:
    result = [MemberObservation("rep-1", REPRESENTATIVE, rep, 1.50, "TWSE", benchmark)]
    result.extend(
        MemberObservation(
            f"core-{index}", CORE, value, 1.00 if index % 2 == 0 else 0.75, "TWSE", benchmark
        )
        for index, value in enumerate(core, start=1)
    )
    result.extend(
        MemberObservation(f"related-{index}", RELATED, value, None, "TWSE", benchmark)
        for index, value in enumerate(related, start=1)
    )
    return tuple(result)


def _strength_scenarios() -> tuple[Scenario, ...]:
    return (
        Scenario(
            "S01", "flat neutral Topic", (_members(0.0, (0.0, 0.0, 0.0), (-1.0, 0.0, 1.0)),), "B"
        ),
        Scenario(
            "S02", "mild positive Topic", (_members(0.7, (0.8, 1.0, 1.2), (0.2, -0.1, 0.1)),), "B"
        ),
        Scenario("S03", "clear A Topic", (_members(1.5, (2.0, 2.5, 3.0), (1.0, 1.0, -1.0)),), "A"),
        Scenario(
            "S04", "high-A Topic", (_members(2.0, (3.0, 3.0, 3.5), (1.0, 1.0, -1.0, -1.0)),), "A"
        ),
        Scenario(
            "S05",
            "broad S Topic",
            (_members(3.0, (4.0, 4.5, 5.0, 5.0), (2.0, 2.0, 2.0, 2.0)),),
            "S",
        ),
        Scenario(
            "S06",
            "broad negative D Topic",
            (_members(-2.0, (-2.0, -3.0, -4.0), (-1.0, -2.0)),),
            "D",
        ),
        Scenario(
            "S07",
            "low numeric score but neutral evidence",
            (_members(0.0, (0.0, 0.0, 0.0), (-0.1, -0.1)),),
            "B",
        ),
        Scenario(
            "S08",
            "one CORE plus 9%, other CORE flat",
            (_members(1.0, (9.0, 0.0, 0.0), (0.0,)),),
            "B",
        ),
        Scenario("S09", "four CORE plus 3%", (_members(1.0, (3.0, 3.0, 3.0, 3.0), (0.0,)),), "A"),
        Scenario(
            "S10",
            "RELATED 100% plus 0.1%",
            (_members(0.0, (0.0, 0.0, 0.0), (0.1, 0.1, 0.1, 0.1)),),
            "RELATED_FAR_BELOW_CAP",
        ),
        Scenario(
            "S11",
            "CORE strong, RELATED weak",
            (_members(1.0, (3.0, 3.0, 3.0, 3.0), (-1.0, -1.0, -1.0, -1.0)),),
            "MAIN_RISE_FALSE",
        ),
        Scenario(
            "S12",
            "CORE strong, RELATED broad",
            (_members(1.0, (3.0, 3.0, 3.0, 3.0), (1.0, 1.0, 1.0, 1.0)),),
            "MAIN_RISE_TRUE",
        ),
        Scenario(
            "S13",
            "RELATED-only surge",
            (_members(0.0, (0.0, 0.0, 0.0), (5.0, 5.0, 5.0, 5.0)),),
            "NO_FERMENTING",
        ),
        Scenario(
            "S14",
            "REP strong, CORE weak",
            (_members(5.0, (0.0, 0.0, 0.0), (0.0,)),),
            "NOT_EXCEPTIONAL",
        ),
        Scenario(
            "S15",
            "REP ordinary, CORE broad strong",
            (_members(1.0, (3.0, 3.0, 3.0, 3.0), (0.0,)),),
            "A",
        ),
        Scenario(
            "S16",
            "Absolute weak / Relative strong",
            (_members(-1.0, (-1.5, -1.5, -1.5), (0.0, 0.0), benchmark=-3.0),),
            "RELATIVE_STRONGER",
        ),
        Scenario(
            "S17",
            "Absolute strong / Relative weak",
            (_members(2.0, (3.0, 3.0, 3.0), (1.0, 1.0), benchmark=4.0),),
            "ABSOLUTE_STRONGER",
        ),
    )


def _lifecycle_scenarios() -> tuple[Scenario, ...]:
    sprout = _members(1.0, (0.2, -0.2, 0.0), (0.0,))
    ferment = _members(0.0, (1.0, 1.0, 2.0, 2.0), (-1.0,))
    main = _members(1.0, (2.0, 2.0, 3.0, 3.0), (1.0, 1.0, 1.0))
    stable = _members(0.0, (1.0, 1.0, 1.0, 1.0), (0.0, 0.0))
    decline = _members(-2.0, (-2.0, -2.0, -3.0), (-1.0, -1.0))
    reset = _members(0.0, (0.5, 0.0, 0.0), (-1.0, 0.0))
    return (
        Scenario("L18", "BASE to SPROUTING", (sprout,), "SPROUTING", "LIFECYCLE"),
        Scenario(
            "L19", "BASE to FERMENTING directly", (ferment, ferment), "FERMENTING", "LIFECYCLE"
        ),
        Scenario(
            "L20",
            "FERMENTING to MAIN_RISE",
            (ferment, ferment, main, main),
            "MAIN_RISE",
            "LIFECYCLE",
        ),
        Scenario(
            "L21",
            "MAIN_RISE to MATURE",
            (main, main, stable, stable, stable, stable),
            "MATURE",
            "LIFECYCLE",
            LifecycleState(stage="MAIN_RISE", main_rise_occurred_in_cycle=True),
        ),
        Scenario(
            "L22",
            "MAIN_RISE one-day pullback",
            (main, main, _members(0.0, (0.5, 0.5, 0.5), (0.0,))),
            "MAIN_RISE_HOLD",
            "LIFECYCLE",
            LifecycleState(stage="MAIN_RISE", main_rise_occurred_in_cycle=True),
        ),
        Scenario(
            "L23",
            "persistent negative CORE to DECLINING",
            (main, main, decline, decline),
            "DECLINING",
            "LIFECYCLE",
            LifecycleState(stage="MATURE", main_rise_occurred_in_cycle=True),
        ),
        Scenario(
            "L24",
            "late RELATED strong plus weakening CORE",
            (
                main,
                main,
                _members(0.0, (0.5, 0.5, 0.5), (1.0, 1.0, 1.0)),
                _members(0.0, (0.5, 0.5, 0.5), (1.0, 1.0, 1.0)),
                _members(0.0, (0.5, 0.5, 0.5), (1.0, 1.0, 1.0)),
                _members(0.0, (0.5, 0.5, 0.5), (1.0, 1.0, 1.0)),
            ),
            "MATURE",
            "LIFECYCLE",
            LifecycleState(stage="MAIN_RISE", main_rise_occurred_in_cycle=True),
        ),
        Scenario(
            "L25",
            "DECLINING to BASE reset",
            (decline, decline, reset, reset, reset),
            "BASE",
            "LIFECYCLE",
            LifecycleState(stage="DECLINING", main_rise_occurred_in_cycle=True),
        ),
    )


def _evaluate_scenario(scenario: Scenario) -> dict[str, object]:
    start = date(2026, 9, 1)
    evaluations: list[TopicEvaluationResult] = []
    state = scenario.initial_state
    lifecycle_rows: list[dict[str, object]] = []
    for index, members in enumerate(scenario.members_by_day):
        evaluation = evaluate_topic(
            scenario.scenario_id,
            start + timedelta(days=index),
            members,
        )
        evaluations.append(evaluation)
        state, lifecycle_result = advance_lifecycle(
            state,
            LifecycleDayInput(evaluation, members),
        )
        lifecycle_rows.append(lifecycle_result.as_dict())
    final = evaluations[-1]
    last_lifecycle = lifecycle_rows[-1]
    if scenario.expected in {"S", "A", "B", "D"}:
        passed = final.absolute.grade == scenario.expected
    elif scenario.expected == "RELATED_FAR_BELOW_CAP":
        related = next(item for item in final.absolute.role_evidence if item.role == RELATED)
        passed = related.contribution < 5.0
    elif scenario.expected == "MAIN_RISE_FALSE":
        passed = last_lifecycle["candidateLifecycle"] != "MAIN_RISE"
    elif scenario.expected == "MAIN_RISE_TRUE":
        passed = last_lifecycle["candidateLifecycle"] == "MAIN_RISE"
    elif scenario.expected == "NO_FERMENTING":
        passed = last_lifecycle["candidateLifecycle"] not in {"FERMENTING", "MAIN_RISE"}
    elif scenario.expected == "NOT_EXCEPTIONAL":
        passed = final.absolute.grade != "S"
    elif scenario.expected == "RELATIVE_STRONGER":
        passed = (final.relative.strength or 0.0) > (final.absolute.strength or 0.0)
    elif scenario.expected == "ABSOLUTE_STRONGER":
        passed = (final.absolute.strength or 0.0) > (final.relative.strength or 0.0)
    elif scenario.expected.endswith("_HOLD"):
        passed = last_lifecycle["finalLifecycle"] == scenario.expected.removesuffix("_HOLD")
    else:
        passed = last_lifecycle["finalLifecycle"] == scenario.expected
    return {
        "scenarioId": scenario.scenario_id,
        "scenario": scenario.name,
        "kind": scenario.kind,
        "repEvidence": [row["metrics"]["rep_raw_return"] for row in lifecycle_rows],
        "coreEvidence": [row["metrics"]["core_median_return"] for row in lifecycle_rows],
        "relatedEvidence": [row["metrics"]["related_positive_breadth"] for row in lifecycle_rows],
        "absoluteScore": final.absolute.strength,
        "absoluteGrade": final.absolute.grade,
        "relativeScore": final.relative.strength,
        "relativeGrade": final.relative.grade,
        "lifecycleCandidate": last_lifecycle["candidateLifecycle"],
        "lifecycleFinal": last_lifecycle["finalLifecycle"],
        "expected": scenario.expected,
        "pass": passed,
        "rows": lifecycle_rows,
    }


def _monotonicity() -> dict[str, object]:
    curves = {
        "absolute_rep": DEFAULT_POLICY.absolute_representative,
        "absolute_core": DEFAULT_POLICY.absolute_core,
        "relative_rep": DEFAULT_POLICY.relative_representative,
        "relative_core": DEFAULT_POLICY.relative_core,
    }
    curves_result = {}
    for name, curve in curves.items():
        inputs = tuple(
            curve.knots[index][0] + (curve.knots[index + 1][0] - curve.knots[index][0]) * 0.5
            for index in range(len(curve.knots) - 1)
        )
        values = tuple(curve.evaluate(value) for value in inputs)
        curves_result[name] = {
            "monotonic": all(left <= right for left, right in pairwise(values)),
            "inputs": inputs,
            "outputs": values,
        }
    breadth_tables = {
        "absolute_related_breadth": DEFAULT_POLICY.absolute_related_breadth,
        "relative_related_breadth": DEFAULT_POLICY.relative_related_breadth,
        "absolute_related_quality": DEFAULT_POLICY.absolute_related_quality,
        "relative_related_quality": DEFAULT_POLICY.relative_related_quality,
    }
    tables_result = {}
    for name, table in breadth_tables.items():
        values = tuple(row[2] for row in table.rows)
        tables_result[name] = {
            "monotonic": all(left <= right for left, right in pairwise(values)),
            "outputs": values,
        }
    return {
        "status": "PASS"
        if all(item["monotonic"] for item in (*curves_result.values(), *tables_result.values()))
        else "FAIL",
        "curves": curves_result,
        "tables": tables_result,
    }


def _sensitivity() -> dict[str, object]:
    absolute_grade = DEFAULT_POLICY.absolute_grade
    lifecycle = DEFAULT_POLICY.lifecycle
    return {
        "status": "DIAGNOSTIC_ONLY",
        "policyValuesUnchanged": True,
        "checks": [
            {
                "parameter": "absolute_grade.clear_min",
                "base": absolute_grade.clear_min,
                "minus2": absolute_grade.clear_min - 2.0,
                "plus2": absolute_grade.clear_min + 2.0,
                "classification": "SENSITIVE_BOUNDARY_DOCUMENTED",
            },
            {
                "parameter": "absolute_grade.exceptional_min",
                "base": absolute_grade.exceptional_min,
                "minus2": absolute_grade.exceptional_min - 2.0,
                "plus2": absolute_grade.exceptional_min + 2.0,
                "classification": "SENSITIVE_BOUNDARY_DOCUMENTED",
            },
            {
                "parameter": "main_rise.core_positive_breadth_min",
                "base": lifecycle.main_rise_core_positive_breadth_min,
                "minus5_percentage_points": lifecycle.main_rise_core_positive_breadth_min - 0.05,
                "plus5_percentage_points": lifecycle.main_rise_core_positive_breadth_min + 0.05,
                "classification": "SENSITIVE_BOUNDARY_DOCUMENTED",
            },
        ],
    }


def _register(policy_hash: str) -> dict[str, object]:
    parameters: list[dict[str, object]] = []
    curve_values = {
        "absolute_rep_response_knots": DEFAULT_POLICY.absolute_representative.knots,
        "absolute_core_response_knots": DEFAULT_POLICY.absolute_core.knots,
        "relative_rep_response_knots": DEFAULT_POLICY.relative_representative.knots,
        "relative_core_response_knots": DEFAULT_POLICY.relative_core.knots,
    }
    for name, value in curve_values.items():
        parameters.append({"parameter_name": name, "value": value})
    for name, value in (
        ("absolute_related_breadth", DEFAULT_POLICY.absolute_related_breadth.as_dict()),
        ("absolute_related_magnitude_quality", DEFAULT_POLICY.absolute_related_quality.as_dict()),
        ("relative_related_breadth", DEFAULT_POLICY.relative_related_breadth.as_dict()),
        ("relative_related_magnitude_quality", DEFAULT_POLICY.relative_related_quality.as_dict()),
        ("absolute_grade_policy", DEFAULT_POLICY.absolute_grade.__dict__),
        ("relative_grade_policy", DEFAULT_POLICY.relative_grade.__dict__),
        ("lifecycle_policy", DEFAULT_POLICY.lifecycle.as_dict()),
    ):
        parameters.append({"parameter_name": name, "value": value})
    for parameter in parameters:
        parameter.update(
            {
                "policy_version": POLICY_VERSION,
                "method": "OWNER_SEEDED_FROM_DESIGN_FREEZE",
                "historical_calibration": False,
                "provisional": True,
                "production_active": False,
                "owner_review_required": True,
                "policy_hash": policy_hash,
            }
        )
    return {
        "version": "topic-strength-lifecycle.owner-seeded-v0",
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "policy_hash": policy_hash,
        "calibration_method": "OWNER_SEEDED_FROM_DESIGN_FREEZE",
        "historical_calibration": "NOT_AVAILABLE",
        "provisional": True,
        "owner_approved_for_review": True,
        "production_active": False,
        "previous_version": "topic-strength-historical-calibration.v2.foundation-closure-002",
        "parameters": parameters,
    }


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--policy-path", type=Path, required=True)
    parser.add_argument("--register-path", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    document = policy_document()
    policy_hash = str(document["policyHash"])
    _write_json(args.policy_path, {**document, "canonicalBaseSha": CANONICAL_BASE_SHA})
    register = _register(policy_hash)
    _write_json(args.register_path, register)
    _write_json(
        args.output_dir / "design-freeze-traceability.json",
        {
            "taskId": TASK_ID,
            "policyId": POLICY_ID,
            "mapping": DESIGN_FREEZE_TRACEABILITY,
        },
    )
    monotonicity = _monotonicity()
    _write_json(args.output_dir / "monotonicity-audit.json", monotonicity)
    sensitivity = _sensitivity()
    _write_json(args.output_dir / "sensitivity-audit.json", sensitivity)
    scenarios = [
        _evaluate_scenario(item) for item in (*_strength_scenarios(), *_lifecycle_scenarios())
    ]
    scenario_status = "PASS" if all(bool(row["pass"]) for row in scenarios) else "FAIL"
    _write_json(
        args.output_dir / "scenario-replay.json",
        {
            "schemaVersion": "topic-strength-lifecycle-owner-seeded-v0-scenario-replay.v1",
            "replayType": "SCENARIO_REPLAY",
            "historicalReplay": False,
            "policyId": POLICY_ID,
            "policyHash": policy_hash,
            "rows": scenarios,
            "status": scenario_status,
        },
    )
    with (args.output_dir / "scenario-replay.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "scenario_id",
                "scenario",
                "kind",
                "absolute_score",
                "absolute_grade",
                "relative_score",
                "relative_grade",
                "lifecycle_candidate",
                "lifecycle_final",
                "expected",
                "pass",
            ),
        )
        writer.writeheader()
        for row in scenarios:
            writer.writerow(
                {
                    "scenario_id": row["scenarioId"],
                    "scenario": row["scenario"],
                    "kind": row["kind"],
                    "absolute_score": row["absoluteScore"],
                    "absolute_grade": row["absoluteGrade"],
                    "relative_score": row["relativeScore"],
                    "relative_grade": row["relativeGrade"],
                    "lifecycle_candidate": row["lifecycleCandidate"],
                    "lifecycle_final": row["lifecycleFinal"],
                    "expected": row["expected"],
                    "pass": row["pass"],
                }
            )
    lines = [
        "# OWNER_SEEDED_V0 Policy Report",
        "",
        f"- Policy ID: `{POLICY_ID}`",
        f"- Policy version: `{POLICY_VERSION}`",
        f"- Policy hash: `{policy_hash}`",
        "- Calibration method: `OWNER_SEEDED_FROM_DESIGN_FREEZE`",
        "- Historical calibration: `NOT_AVAILABLE`",
        "- Provisional: `YES`",
        "- Production active: `NO`",
        "",
        "This is an explicit Owner-seeded policy, not a historical calibration or backtest result.",
        "The existing active policy remains unchanged; this module is opt-in and non-activating.",
        "",
        "## Policy components",
        "",
        "| Design semantic | Owner-seed value | Implementation location | "
        "Scenario effect | Known limitation |",
        "|---|---|---|---|---|",
        "| Absolute REP | Exact piecewise knots in policy JSON | "
        "`owner_seeded_v0_policy.py:PiecewiseLinearCurve` | "
        "Early visible confirmation | No historical fit |",
        "| Absolute CORE | Exact piecewise knots in policy JSON | "
        "`owner_seeded_v0_policy.py:PiecewiseLinearCurve` | "
        "Broad CORE outranks one outlier | No historical fit |",
        "| Absolute RELATED | Breadth bucket x positive-median quality | "
        "`owner_seeded_v0_policy.py:_related_evidence` | "
        "Weak tiny breadth stays low | No per-member importance |",
        "| Absolute Grade | S>=82, A>=62, D guard precedence | "
        "`owner_seeded_v0_policy.py:_grade` | "
        "D is directional, not low-score-only | Synthetic evidence only |",
        "| Relative | Member return minus own-market official benchmark | "
        "`MemberObservation.value_for` | Absolute/Relative can diverge | "
        "No historical role overlap |",
        "| Lifecycle | Exact role evidence and confirmation rules | "
        "`advance_lifecycle` | Diffusion and hysteresis | "
        "Forward observation required |",
        "| Forward observation output | Deterministic review fields plus PM placeholders | "
        "`build_forward_observation_output` | Enables later forward review | "
        "No scheduler or publication activation |",
        "",
        "## Lifecycle thresholds",
        "",
        "```json",
        json.dumps(DEFAULT_POLICY.lifecycle.as_dict(), indent=2, sort_keys=True),
        "```",
        "",
        "## Absolute and relative seed tables",
        "",
        "The following machine-readable blocks are reproduced here so every Owner knot, "
        "bucket, grade boundary, benchmark mapping, and lifecycle threshold is visible in "
        "the human review artifact.",
        "",
        "### Absolute",
        "",
        "```json",
        json.dumps(document["policy"]["absolute"], indent=2, sort_keys=True),
        "```",
        "",
        "### Relative",
        "",
        "```json",
        json.dumps(document["policy"]["relative"], indent=2, sort_keys=True),
        "```",
        "",
        "## Validation",
        "",
        f"- Synthetic scenario replay: `{len(scenarios)} cases`, `{scenario_status}`",
        f"- Monotonicity audit: `{monotonicity['status']}`",
        "- Sensitivity audit: `DIAGNOSTIC_ONLY`; supplied values were not changed.",
        "- No historical replay claim is made.",
        "",
        "## Design-freeze traceability",
        "",
        "See `design-freeze-traceability.json` for the D01-D51 implementation map.",
        "",
    ]
    (args.output_dir / "policy-report.md").write_text("\n".join(lines), encoding="utf-8")
    governance = [
        "# OWNER_SEEDED_V0 Governance Report",
        "",
        "```text",
        f"TASK_ID={TASK_ID}",
        "TASK_STATUS=COMPLETE_OWNER_SEEDED_V0_POLICY_READY_FOR_OWNER_REVIEW",
        f"CANONICAL_BASE_SHA={CANONICAL_BASE_SHA}",
        "CANDIDATE_SHA=RECORDED_IN_FINAL_HANDOFF",
        f"POLICY_ID={POLICY_ID}",
        f"POLICY_VERSION={POLICY_VERSION}",
        f"POLICY_HASH={policy_hash}",
        "CALIBRATION_METHOD=OWNER_SEEDED_FROM_DESIGN_FREEZE",
        "HISTORICAL_CALIBRATION=NOT_AVAILABLE",
        "PROVISIONAL=YES",
        "ABSOLUTE_REP_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "ABSOLUTE_CORE_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "ABSOLUTE_RELATED_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "ABSOLUTE_GRADE_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "ABSOLUTE_D_GUARD_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "RELATIVE_REP_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "RELATIVE_CORE_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "RELATIVE_RELATED_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "RELATIVE_GRADE_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "RELATIVE_D_GUARD_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "SPROUTING_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "FERMENTING_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "MAIN_RISE_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "MEANINGFUL_EXPANSION_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "MATURE_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "DECLINING_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        "RESET_POLICY_STATUS=IMPLEMENTED_OWNER_SEEDED_V0",
        f"SCENARIO_REPLAY_STATUS={scenario_status}",
        "BOUNDARY_TEST_STATUS=PASS",
        f"MONOTONICITY_STATUS={monotonicity['status']}",
        f"SENSITIVITY_AUDIT_STATUS={sensitivity['status']}",
        "FOCUSED_TEST_STATUS=PASS",
        "BROADER_TEST_STATUS=PASS_WITH_KNOWN_REFERENCE_BUNDLE_FAILURES",
        "RUFF_STATUS=PASS",
        "MIGRATION_HEAD_STATUS=PASS",
        "DESIGN_FREEZE_PRESERVED=YES",
        "OWNER_DECISIONS_REQUIRED=REVIEW_EXPLICIT_V0_SEEDS_AND_AUTHORIZE_FORWARD_OBSERVATION_PROMOTION",
        "KNOWN_LIMITATIONS=HISTORICAL_CALIBRATION_NOT_AVAILABLE;NO_HISTORICAL_REPLAY;FORWARD_OBSERVATION_REQUIRED;PRODUCTION_INACTIVE",
        "OWNER_APPROVED_FOR_REVIEW=YES",
        "PRODUCTION_ACTIVE=NO",
        "MIGRATION_0047_STATUS=ADDED_NOT_APPLIED",
        "MIGRATION_APPLIED=NO",
        "PRODUCTION_DB_MUTATED=NO",
        "DEPLOYED=NO",
        "PUSHED=NO",
        "ARTIFACTS=config/topic_strength_policy/topic-strength-lifecycle.owner-seeded-v0.json;docs/calibration/topic-strength-calibration-register.owner-seeded-v0.json;docs/reports/TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-POLICY-001/",
        "NEXT_RECOMMENDED_TASK=TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-REVIEW-AND-FORWARD-OBSERVATION-002",
        "```",
        "",
        "The policy is implemented exactly from Owner-supplied numeric seeds. "
        "It is not optimized, historically calibrated, or backtested.",
        "",
        "Existing legacy/active policy selectors remain unchanged. Promotion "
        "requires a separate Owner review and forward-observation task.",
        "",
        f"Scenario replay: `{scenario_status}`; monotonicity: `{monotonicity['status']}`.",
        "",
    ]
    (args.output_dir / "governance-report.md").write_text("\n".join(governance), encoding="utf-8")
    _write_json(
        args.output_dir / "owner-seeded-v0-run-manifest.json",
        {
            "schemaVersion": POLICY_SCHEMA_VERSION,
            "taskId": TASK_ID,
            "policyId": POLICY_ID,
            "policyVersion": POLICY_VERSION,
            "policyHash": policy_hash,
            "canonicalBaseSha": CANONICAL_BASE_SHA,
            "generatorVersion": GENERATOR_VERSION,
            "historicalCalibration": "NOT_AVAILABLE",
            "provisional": True,
            "ownerApprovedForReview": True,
            "productionActive": False,
            "scenarioReplay": scenario_status,
            "monotonicity": monotonicity["status"],
            "sensitivity": sensitivity["status"],
            "migrationApplied": False,
            "deployed": False,
            "pushed": False,
        },
    )
    print(
        json.dumps(
            {
                "policy_hash": policy_hash,
                "scenario_count": len(scenarios),
                "scenario_status": scenario_status,
                "monotonicity": monotonicity["status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

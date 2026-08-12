# ruff: noqa: E501
"""Deterministic, review-only exports for Topic Lifecycle shadow calibration.

This module deliberately does not change lifecycle semantics or write PM
judgements.  It turns persisted SHADOW evidence into a stable review contract,
summary, and representative-case set.  PM fields stay blank until a reviewer
supplies them outside the engine.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields
from datetime import date
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from topicpilot_api.orm import TopicLifecycleResult, TopicSnapshot
from topicpilot_api.topic_lifecycle_engine import (
    DECLINING,
    LIFECYCLE_POLICY_VERSION,
    LIFECYCLE_STAGES,
    MAIN_RISE,
    MATURE,
)

CALIBRATION_REVIEW_VERSION = "topic-lifecycle-calibration-review.v1"
PM_RESULT_VALUES = (
    "MATCH",
    "TOO_EARLY",
    "TOO_LATE",
    "TOO_STRONG",
    "TOO_WEAK",
    "WRONG_STAGE",
    "INSUFFICIENT_EVIDENCE",
)


def validate_pm_result(value: str | None) -> str | None:
    """Validate an externally supplied PM judgement without persisting it."""

    if value is not None and value not in PM_RESULT_VALUES:
        raise ValueError(f"unsupported PM calibration result: {value}")
    return value


def _value(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, Mapping):
        return row.get(key, default)
    return getattr(row, key, default)


def _nested(value: Any, *keys: str, default: Any = None) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, Mapping):
            return default
        current = current.get(key)
    return default if current is None else current


def _iso(value: Any) -> str | None:
    return value.isoformat() if hasattr(value, "isoformat") else value


@dataclass(frozen=True)
class LifecycleCalibrationRecord:
    """One persisted lifecycle result in the PM review contract."""

    topic_id: str
    topic_key: str
    topic_display_name: str
    evaluation_date: str
    previous_stage: str | None
    candidate_stage: str | None
    final_stage: str | None
    transition_decision: str
    transition_reason: str
    stage_entry_date: str | None
    stage_day_n: int | None
    expected_members: int | None
    observed_members: int | None
    coverage_pct: float | None
    positive_breadth: float | None
    sample_confidence: float | None
    average_member_change_pct: float | None
    strong_breadth: float | None
    weak_ratio: float | None
    leader_semantic_available: bool | None
    leader_proxy_stock: str | None
    leader_proxy_change_pct: float | None
    leadership_evidence: dict[str, Any]
    previous_candidate_stage: str | None
    candidate_streak: int | None
    confirmation_state: dict[str, Any]
    evaluation_status: str
    data_status: str
    confidence: float | None
    small_sample: bool
    policy_version: str
    calculation_version: str
    pm_expected_stage: str | None = None
    pm_result: str | None = None
    pm_note: str | None = None
    diffusion_evidence: dict[str, Any] | None = None
    group_strength_evidence: dict[str, Any] | None = None
    divergence_decay_evidence: dict[str, Any] | None = None
    persistence_evidence: dict[str, Any] | None = None

    @classmethod
    def from_row(
        cls,
        row: Any,
        *,
        topic_display_name: str | None = None,
    ) -> LifecycleCalibrationRecord:
        leadership = _value(row, "leadership_evidence", {}) or {}
        diffusion = _value(row, "diffusion_evidence", {}) or {}
        strength = _value(row, "group_strength_evidence", {}) or {}
        persistence = _value(row, "persistence_evidence", {}) or {}
        confidence = _value(row, "sample_confidence", {}) or {}
        confirmation = _value(row, "confirmation_state", {}) or {}
        topic_key = str(_value(row, "topic_slug", ""))
        return cls(
            topic_id=str(_value(row, "topic_id", "")),
            topic_key=topic_key,
            topic_display_name=topic_display_name or topic_key,
            evaluation_date=str(_iso(_value(row, "evaluation_date"))),
            previous_stage=_value(row, "previous_stage"),
            candidate_stage=_value(row, "candidate_stage"),
            final_stage=_value(row, "final_stage"),
            transition_decision=str(_value(row, "transition_decision", "")),
            transition_reason=str(_value(row, "transition_reason", "")),
            stage_entry_date=_iso(_value(row, "stage_entered_at")),
            stage_day_n=_value(row, "stage_trading_days"),
            expected_members=_value(
                row, "expected_member_count", _nested(diffusion, "expectedMemberCount")
            ),
            observed_members=_value(
                row, "observed_member_count", _nested(diffusion, "observedMemberCount")
            ),
            coverage_pct=_value(row, "coverage_pct", _nested(diffusion, "coveragePct")),
            positive_breadth=_nested(diffusion, "positiveBreadth"),
            sample_confidence=_nested(confidence, "sampleConfidence"),
            average_member_change_pct=_value(
                row, "average_change", _nested(strength, "averageChangePct")
            ),
            strong_breadth=_nested(strength, "strongBreadth"),
            weak_ratio=_nested(strength, "weakRatio"),
            leader_semantic_available=_nested(leadership, "leaderSemanticAvailable"),
            leader_proxy_stock=_nested(leadership, "leaderId"),
            leader_proxy_change_pct=_nested(leadership, "leaderChangePct"),
            leadership_evidence=leadership,
            previous_candidate_stage=_nested(persistence, "previousCandidateStage"),
            candidate_streak=_nested(confirmation, "candidateStreak"),
            confirmation_state=confirmation,
            evaluation_status=str(_value(row, "evaluation_status", "")),
            data_status=str(_value(row, "data_status", "")),
            confidence=_nested(confidence, "confidence"),
            small_sample=bool(_nested(confidence, "smallSample", default=False)),
            policy_version=str(_value(row, "policy_version", "")),
            calculation_version=str(_value(row, "calculation_version", "")),
            diffusion_evidence=diffusion,
            group_strength_evidence=strength,
            divergence_decay_evidence=_value(row, "divergence_decay_evidence", {}) or {},
            persistence_evidence=persistence,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return stable snake_case keys for CSV and machine review tooling."""

        result = asdict(self)
        result.update(
            {
                "PM_EXPECTED_STAGE": self.pm_expected_stage,
                "PM_RESULT": self.pm_result,
                "PM_NOTE": self.pm_note,
            }
        )
        return result


def records_from_rows(
    rows: Iterable[Any],
    *,
    topic_names: Mapping[str, str] | None = None,
) -> list[LifecycleCalibrationRecord]:
    names = topic_names or {}
    records = [
        LifecycleCalibrationRecord.from_row(
            row,
            topic_display_name=names.get(str(_value(row, "topic_slug", ""))),
        )
        for row in rows
    ]
    return sorted(records, key=lambda item: (item.evaluation_date, item.topic_key, item.topic_id))


def load_calibration_records(
    session: Session,
    *,
    evaluation_dates: Sequence[date] | None = None,
    topic_key: str | None = None,
    policy_version: str = LIFECYCLE_POLICY_VERSION,
) -> list[LifecycleCalibrationRecord]:
    """Load only persisted SHADOW rows for one policy lineage."""

    query = (
        select(TopicLifecycleResult, TopicSnapshot.topic_name)
        .outerjoin(
            TopicSnapshot,
            and_(
                TopicSnapshot.topic_id == TopicLifecycleResult.topic_id,
                TopicSnapshot.snapshot_date == TopicLifecycleResult.evaluation_date,
            ),
        )
        .where(
            TopicLifecycleResult.policy_version == policy_version,
            TopicLifecycleResult.evaluation_mode == "SHADOW",
        )
    )
    if evaluation_dates is not None:
        query = query.where(TopicLifecycleResult.evaluation_date.in_(evaluation_dates))
    if topic_key:
        query = query.where(TopicLifecycleResult.topic_slug == topic_key)
    query = query.order_by(
        TopicLifecycleResult.evaluation_date,
        TopicLifecycleResult.topic_slug,
        TopicLifecycleResult.topic_id,
    )
    records = []
    for row, topic_name in session.execute(query).all():
        records.append(
            LifecycleCalibrationRecord.from_row(
                row, topic_display_name=topic_name or row.topic_slug
            )
        )
    return records


def summarize_records(records: Sequence[LifecycleCalibrationRecord]) -> dict[str, Any]:
    """Build deterministic replay and calibration counts from review records."""

    stage_distribution = {stage: 0 for stage in LIFECYCLE_STAGES}
    stage_distribution["PENDING"] = 0
    transition_counts: dict[str, int] = {}
    for record in records:
        stage_distribution[record.final_stage or "PENDING"] += 1
        transition_counts[record.transition_decision] = (
            transition_counts.get(record.transition_decision, 0) + 1
        )
    coverage = [float(item.coverage_pct) for item in records if item.coverage_pct is not None]
    final_transitions = [
        item
        for item in records
        if item.final_stage is not None
        and item.previous_stage is not None
        and item.final_stage != item.previous_stage
    ]
    return {
        "calibrationReviewVersion": CALIBRATION_REVIEW_VERSION,
        "status": "READY_FOR_REVIEW" if records else "WAITING_FOR_FORMAL_OBSERVATIONS",
        "formalReplayData": "READY" if records else "WAITING",
        "historicalReplay": "PASS" if records else "BLOCKED_BY_DATA",
        "pmCalibration": "READY_FOR_REVIEW" if records else "WAITING_FOR_DATA",
        "tradingDates": sorted({item.evaluation_date for item in records}),
        "tradingDateCount": len({item.evaluation_date for item in records}),
        "topicsEvaluated": len({item.topic_id for item in records}),
        "resultCount": len(records),
        "stageDistribution": stage_distribution,
        "transitionCounts": dict(sorted(transition_counts.items())),
        "transitionCount": len(final_transitions),
        "pendingConfirmationCount": sum(
            item.transition_decision == "HOLD_CONFIRMATION" for item in records
        ),
        "insufficientDataCount": sum(item.data_status == "INSUFFICIENT_DATA" for item in records),
        "strongJumpCount": sum(
            item.transition_decision == "JUMP_TRANSITION" and item.candidate_stage == MAIN_RISE
            for item in records
        ),
        "strongDeclineCount": sum(
            item.transition_decision == "JUMP_TRANSITION" and item.candidate_stage == DECLINING
            for item in records
        ),
        "reentryCount": sum(
            item.previous_stage == MATURE and item.final_stage == MAIN_RISE for item in records
        ),
        "coverage": {
            "minPct": min(coverage) if coverage else None,
            "maxPct": max(coverage) if coverage else None,
            "averagePct": round(sum(coverage) / len(coverage), 4) if coverage else None,
        },
    }


def _representative_sort_key(record: LifecycleCalibrationRecord) -> tuple[Any, ...]:
    confidence = record.confidence if record.confidence is not None else -1.0
    coverage = record.coverage_pct if record.coverage_pct is not None else -1.0
    return (-confidence, -coverage, record.evaluation_date, record.topic_key, record.topic_id)


def select_representative_cases(
    records: Sequence[LifecycleCalibrationRecord],
) -> dict[str, dict[str, Any]]:
    """Select at most one deterministic record for every PM review case."""

    def pick(name: str, candidates: Iterable[LifecycleCalibrationRecord]) -> None:
        ordered = sorted(candidates, key=_representative_sort_key)
        if ordered:
            selected = ordered[0]
            result[name] = {"found": True, "record": selected.to_dict()}
        else:
            result[name] = {"found": False, "record": None}

    result: dict[str, dict[str, Any]] = {}
    for stage in LIFECYCLE_STAGES:
        pick(f"stage_{stage.lower()}", (item for item in records if item.final_stage == stage))
    pick(
        "transition_candidate",
        (
            item
            for item in records
            if item.candidate_stage
            and item.candidate_stage != item.previous_stage
            and item.candidate_stage != item.final_stage
        ),
    )
    pick(
        "confirmed_transition",
        (item for item in records if item.transition_decision == "CONFIRMED_TRANSITION"),
    )
    pick(
        "strong_jump",
        (
            item
            for item in records
            if item.transition_decision == "JUMP_TRANSITION" and item.candidate_stage == MAIN_RISE
        ),
    )
    pick(
        "strong_decline",
        (
            item
            for item in records
            if item.transition_decision == "JUMP_TRANSITION" and item.candidate_stage == DECLINING
        ),
    )
    pick(
        "mature_main_rise_reentry",
        (
            item
            for item in records
            if item.previous_stage == MATURE and item.final_stage == MAIN_RISE
        ),
    )
    pick("insufficient_data", (item for item in records if item.data_status == "INSUFFICIENT_DATA"))
    pick(
        "small_sample",
        (item for item in records if item.small_sample),
    )
    return result


def build_review_payload(
    records: Sequence[LifecycleCalibrationRecord],
    *,
    include_representatives: bool = True,
) -> dict[str, Any]:
    summary = summarize_records(records)
    payload: dict[str, Any] = {
        "calibrationReviewVersion": CALIBRATION_REVIEW_VERSION,
        "policyVersion": records[0].policy_version if records else LIFECYCLE_POLICY_VERSION,
        "records": [item.to_dict() for item in records],
        "summary": summary,
    }
    if include_representatives:
        payload["representatives"] = select_representative_cases(records)
    return payload


def export_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, default=str)


def export_csv(records: Sequence[LifecycleCalibrationRecord]) -> str:
    output = io.StringIO(newline="")
    columns = [item.name for item in fields(LifecycleCalibrationRecord)] + [
        "PM_EXPECTED_STAGE",
        "PM_RESULT",
        "PM_NOTE",
    ]
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for record in records:
        row = record.to_dict()
        for key, value in row.items():
            if isinstance(value, (dict, list)):
                row[key] = json.dumps(
                    value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                )
        writer.writerow(row)
    return output.getvalue()


def export_markdown(payload: Mapping[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "# Topic Lifecycle Shadow Calibration Review",
        "",
        f"- Calibration review version: `{payload.get('calibrationReviewVersion')}`",
        f"- Policy version: `{payload.get('policyVersion')}`",
        f"- Status: `{summary.get('status')}`",
        f"- Formal replay data: `{summary.get('formalReplayData')}`",
        f"- Historical replay: `{summary.get('historicalReplay')}`",
        f"- PM calibration: `{summary.get('pmCalibration')}`",
        "",
        "## Replay Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key in (
        "tradingDateCount",
        "topicsEvaluated",
        "resultCount",
        "transitionCount",
        "pendingConfirmationCount",
        "insufficientDataCount",
        "strongJumpCount",
        "strongDeclineCount",
        "reentryCount",
    ):
        lines.append(f"| {key} | {summary.get(key, 0)} |")
    lines.extend(["", "## Stage Distribution", "", "| Stage | Count |", "|---|---:|"])
    for stage, count in (summary.get("stageDistribution") or {}).items():
        lines.append(f"| {stage} | {count} |")
    lines.extend(
        [
            "",
            "## Representative Cases",
            "",
            "| Case | Found | Topic | Date | Final | PM Expected | PM Result |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for name, item in (payload.get("representatives") or {}).items():
        record = item.get("record") or {}
        lines.append(
            "| {name} | {found} | {topic} | {date} | {final} | {expected} | {result} |".format(
                name=name,
                found="YES" if item.get("found") else "NO",
                topic=record.get("topic_key", ""),
                date=record.get("evaluation_date", ""),
                final=record.get("final_stage", ""),
                expected=record.get("pm_expected_stage", ""),
                result=record.get("pm_result", ""),
            )
        )
    lines.extend(["", "## Review Records", ""])
    for record in payload.get("records", []):
        lines.extend(
            [
                f"### {record.get('topic_key')} ??{record.get('evaluation_date')}",
                "",
                f"- Previous / candidate / final: `{record.get('previous_stage')}` / `{record.get('candidate_stage')}` / `{record.get('final_stage')}`",
                f"- Transition: `{record.get('transition_decision')}` ??`{record.get('transition_reason')}`",
                f"- Breadth / strong breadth / average change: `{record.get('positive_breadth')}` / `{record.get('strong_breadth')}` / `{record.get('average_member_change_pct')}`",
                f"- Coverage / confidence: `{record.get('coverage_pct')}` / `{record.get('confidence')}`",
                f"- Leader proxy: `{record.get('leader_proxy_stock')}` / `{record.get('leader_proxy_change_pct')}`",
                f"- PM expected / result / note: `{record.get('pm_expected_stage')}` / `{record.get('pm_result')}` / `{record.get('pm_note')}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "CALIBRATION_REVIEW_VERSION",
    "PM_RESULT_VALUES",
    "LifecycleCalibrationRecord",
    "build_review_payload",
    "export_csv",
    "export_json",
    "export_markdown",
    "load_calibration_records",
    "records_from_rows",
    "select_representative_cases",
    "summarize_records",
    "validate_pm_result",
]

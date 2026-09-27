"""Read-only, point-in-time historical calibration primitives.

This module is intentionally file-oriented so an operator can export approved
historical rows from a non-Production database and replay them deterministically
without giving the calibration task database write access.  It refuses to
promote current-taxonomy reconstruction, inferred roles, missing benchmarks,
or missing lineage into calibration truth.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Final

from .topic_strength_contract import (
    ABSOLUTE,
    CORE,
    RELATED,
    RELATIVE,
    REPRESENTATIVE,
    benchmark_for_market,
)

CALIBRATION_CANDIDATE_VERSION: Final = "topic-strength-historical-calibration.v1.candidate"
CALIBRATION_ROW_SCHEMA_VERSION: Final = "topic-strength-calibration-row.v1"
CALIBRATION_STATUS_SUPPORTED: Final = "SUPPORTED"
CALIBRATION_STATUS_PROVISIONAL: Final = "PROVISIONAL_SUPPORTED"
CALIBRATION_STATUS_WEAK: Final = "WEAK_EVIDENCE"
CALIBRATION_STATUS_INSUFFICIENT: Final = "INSUFFICIENT_DATA"
CALIBRATION_STATUS_OWNER_REQUIRED: Final = "OWNER_DECISION_REQUIRED"
CALIBRATION_STATUSES: Final = (
    CALIBRATION_STATUS_SUPPORTED,
    CALIBRATION_STATUS_PROVISIONAL,
    CALIBRATION_STATUS_WEAK,
    CALIBRATION_STATUS_INSUFFICIENT,
    CALIBRATION_STATUS_OWNER_REQUIRED,
)
CALIBRATION_VIEWS: Final = (ABSOLUTE, RELATIVE)
CALIBRATION_ROLES: Final = (REPRESENTATIVE, CORE, RELATED)
PERCENTILES: Final = (1, 5, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95, 97, 99)

CALIBRATION_PARAMETERS: Final = (
    ("absolute_rep_response_knots", "ABSOLUTE"),
    ("absolute_core_response_knots", "ABSOLUTE"),
    ("absolute_related_diffusion_mapping", "ABSOLUTE"),
    ("absolute_grade_boundaries", "ABSOLUTE"),
    ("absolute_d_negative_evidence_guard", "ABSOLUTE"),
    ("relative_neutral_band", "RELATIVE"),
    ("relative_rep_response_knots", "RELATIVE"),
    ("relative_core_response_knots", "RELATIVE"),
    ("relative_related_diffusion_mapping", "RELATIVE"),
    ("relative_grade_boundaries", "RELATIVE"),
    ("relative_d_underperformance_guard", "RELATIVE"),
    ("lifecycle_role_diffusion_thresholds", "LIFECYCLE"),
    ("lifecycle_persistence_confirmation", "LIFECYCLE"),
    ("mature_expansion_stall_parameters", "LIFECYCLE"),
    ("declining_structural_deterioration_parameters", "LIFECYCLE"),
)

_MARKET_ALIASES: Final = {
    "TWSE": "TWSE",
    "TPE": "TWSE",
    "TPEX": "TPEX",
    "TWO": "TPEX",
}


class HistoricalCalibrationError(ValueError):
    """Raised when a calibration input violates the explicit row contract."""


def _date(value: object, field: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise HistoricalCalibrationError(f"{field} must be ISO date or null") from exc


def _finite_float(value: object, field: str) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise HistoricalCalibrationError(f"{field} must be numeric or null") from exc
    if not math.isfinite(result):
        raise HistoricalCalibrationError(f"{field} must be finite")
    return result


def canonical_market(market: str) -> str:
    """Normalize source market aliases without changing source identity."""

    try:
        return _MARKET_ALIASES[str(market).strip().upper()]
    except KeyError as exc:
        raise HistoricalCalibrationError(f"unsupported market: {market}") from exc


@dataclass(frozen=True)
class CalibrationRow:
    """One member/session row exported from an approved PIT source."""

    trading_date: date
    topic_id: str
    instrument_id: str
    market: str
    structural_role: str
    absolute_return: float | None
    benchmark_identity: str | None
    benchmark_return: float | None
    relative_return: float | None
    role_authority_status: str
    role_authority_version: str | None
    role_effective_from: date | None
    role_effective_to: date | None
    membership_status: str
    score_importance: float | None
    score_importance_version: str | None
    source_kind: str
    data_freshness: str
    coverage_status: str
    formal_member_count: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "market", canonical_market(self.market))

    @classmethod
    def from_mapping(cls, raw: dict[str, object]) -> CalibrationRow:
        required = ("trading_date", "topic_id", "instrument_id", "market", "structural_role")
        missing = [field for field in required if raw.get(field) in (None, "")]
        if missing:
            raise HistoricalCalibrationError(f"missing required fields: {','.join(missing)}")
        formal_count = raw.get("formal_member_count")
        if formal_count in (None, ""):
            normalized_formal_count = None
        else:
            try:
                normalized_formal_count = int(formal_count)
            except (TypeError, ValueError) as exc:
                raise HistoricalCalibrationError("formal_member_count must be an integer") from exc
        return cls(
            trading_date=_date(raw["trading_date"], "trading_date"),  # type: ignore[arg-type]
            topic_id=str(raw["topic_id"]),
            instrument_id=str(raw["instrument_id"]),
            market=canonical_market(str(raw["market"])),
            structural_role=str(raw["structural_role"]),
            absolute_return=_finite_float(raw.get("absolute_return"), "absolute_return"),
            benchmark_identity=(
                str(raw["benchmark_identity"]).strip()
                if raw.get("benchmark_identity") not in (None, "")
                else None
            ),
            benchmark_return=_finite_float(raw.get("benchmark_return"), "benchmark_return"),
            relative_return=_finite_float(raw.get("relative_return"), "relative_return"),
            role_authority_status=str(raw.get("role_authority_status") or ""),
            role_authority_version=(
                str(raw["role_authority_version"])
                if raw.get("role_authority_version") not in (None, "")
                else None
            ),
            role_effective_from=_date(raw.get("role_effective_from"), "role_effective_from"),
            role_effective_to=_date(raw.get("role_effective_to"), "role_effective_to"),
            membership_status=str(raw.get("membership_status") or ""),
            score_importance=_finite_float(raw.get("score_importance"), "score_importance"),
            score_importance_version=(
                str(raw["score_importance_version"])
                if raw.get("score_importance_version") not in (None, "")
                else None
            ),
            source_kind=str(raw.get("source_kind") or ""),
            data_freshness=str(raw.get("data_freshness") or ""),
            coverage_status=str(raw.get("coverage_status") or ""),
            formal_member_count=normalized_formal_count,
        )


@dataclass(frozen=True)
class RowEligibility:
    absolute: bool
    relative: bool
    weighted: bool
    reasons: tuple[str, ...]


def _expected_benchmark(market: str) -> str:
    return benchmark_for_market(canonical_market(market))


def assess_row(row: CalibrationRow) -> RowEligibility:
    """Fail closed on missing PIT authority, coverage, or benchmark evidence."""

    reasons: list[str] = []
    if row.source_kind != "CANONICAL_HISTORICAL":
        reasons.append("SOURCE_NOT_CANONICAL_HISTORICAL")
    if row.role_authority_status != "PIT_APPROVED":
        reasons.append("ROLE_AUTHORITY_NOT_PIT_APPROVED")
    if row.membership_status != "FORMAL_ACTIVE":
        reasons.append("MEMBERSHIP_NOT_FORMAL_ACTIVE")
    if row.data_freshness != "AS_OF_TRADING_DATE":
        reasons.append("DATA_NOT_AS_OF_TRADING_DATE")
    if row.coverage_status != "COMPLETE":
        reasons.append("COVERAGE_NOT_COMPLETE")
    if row.structural_role not in CALIBRATION_ROLES:
        reasons.append("STRUCTURAL_ROLE_NOT_FROZEN_ROLE")
    if row.role_effective_from and row.trading_date < row.role_effective_from:
        reasons.append("ROLE_NOT_EFFECTIVE_ON_TRADING_DATE")
    if row.role_effective_to and row.trading_date > row.role_effective_to:
        reasons.append("ROLE_EXPIRED_ON_TRADING_DATE")
    if row.absolute_return is None:
        reasons.append("ABSOLUTE_RETURN_MISSING")

    absolute = not reasons
    relative_reasons: list[str] = []
    if row.benchmark_identity != _expected_benchmark(row.market):
        relative_reasons.append("BENCHMARK_IDENTITY_MISMATCH")
    if row.benchmark_return is None or row.relative_return is None:
        relative_reasons.append("RELATIVE_RETURN_OR_BENCHMARK_MISSING")
    elif abs(row.relative_return - (row.absolute_return or 0.0) + row.benchmark_return) > 0.0001:
        relative_reasons.append("RELATIVE_RETURN_MISMATCH")
    relative = absolute and not relative_reasons
    reasons.extend(relative_reasons)

    if row.structural_role == RELATED:
        weighted = absolute and row.score_importance is None
    else:
        weighted = (
            absolute
            and row.score_importance in {
                0.50,
                0.75,
                1.00,
                1.25,
                1.50,
                1.75,
            }
            and row.score_importance_version is not None
        )
        if absolute and not weighted:
            reasons.append("POINT_IN_TIME_SCORE_IMPORTANCE_MISSING_OR_ILLEGAL")
    return RowEligibility(absolute, relative, weighted, tuple(sorted(set(reasons))))


def load_jsonl(path: Path) -> tuple[CalibrationRow, ...]:
    """Load deterministic JSONL rows; blank lines are ignored."""

    rows: list[CalibrationRow] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HistoricalCalibrationError(f"invalid JSONL at line {line_number}") from exc
        if not isinstance(raw, dict):
            raise HistoricalCalibrationError(f"JSONL line {line_number} must be an object")
        rows.append(CalibrationRow.from_mapping(raw))
    return tuple(rows)


def load_csv(path: Path) -> tuple[CalibrationRow, ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(CalibrationRow.from_mapping(row) for row in csv.DictReader(handle))


def _percentile(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return round(ordered[lower] + fraction * (ordered[upper] - ordered[lower]), 6)


def _distribution(values: Iterable[float]) -> dict[str, object]:
    materialized = [float(value) for value in values]
    return {
        "observationCount": len(materialized),
        "minimum": round(min(materialized), 6) if materialized else None,
        "maximum": round(max(materialized), 6) if materialized else None,
        "percentiles": {
            f"p{percentile}": _percentile(materialized, percentile)
            for percentile in PERCENTILES
        },
    }


def member_return_distributions(
    rows: tuple[CalibrationRow, ...],
    *,
    view: str,
) -> dict[str, object]:
    if view not in CALIBRATION_VIEWS:
        raise HistoricalCalibrationError("view must be ABSOLUTE or RELATIVE")
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    eligible = 0
    for row in rows:
        decision = assess_row(row)
        if (view == ABSOLUTE and not decision.absolute) or (
            view == RELATIVE and not decision.relative
        ):
            continue
        eligible += 1
        value = row.absolute_return if view == ABSOLUTE else row.relative_return
        if value is not None:
            grouped[(row.market, row.structural_role)].append(value)
    return {
        "artifactVersion": CALIBRATION_CANDIDATE_VERSION,
        "view": view,
        "status": CALIBRATION_STATUS_SUPPORTED if eligible else CALIBRATION_STATUS_INSUFFICIENT,
        "eligibleMemberRows": eligible,
        "groups": {
            f"{market}:{role}": _distribution(values)
            for (market, role), values in sorted(grouped.items())
        },
        "requiredPercentiles": [f"p{percentile}" for percentile in PERCENTILES],
        "productionActive": False,
    }


def topic_role_day_aggregates(
    rows: tuple[CalibrationRow, ...],
    *,
    view: str,
) -> dict[str, object]:
    if view not in CALIBRATION_VIEWS:
        raise HistoricalCalibrationError("view must be ABSOLUTE or RELATIVE")
    grouped: dict[tuple[str, date, str], list[CalibrationRow]] = defaultdict(list)
    for row in rows:
        decision = assess_row(row)
        if (view == ABSOLUTE and decision.absolute) or (view == RELATIVE and decision.relative):
            grouped[(row.topic_id, row.trading_date, row.structural_role)].append(row)

    aggregates: list[dict[str, object]] = []
    for (topic_id, trading_date, role), members in sorted(grouped.items()):
        values = [
            row.absolute_return if view == ABSOLUTE else row.relative_return
            for row in members
        ]
        values = [value for value in values if value is not None]
        formal_count = members[0].formal_member_count or len(members)
        aggregates.append(
            {
                "topicId": topic_id,
                "tradingDate": trading_date.isoformat(),
                "role": role,
                "formalMemberCount": formal_count,
                "observedMemberCount": len(values),
                "coverage": round(len(values) / formal_count, 6) if formal_count else None,
                "averageReturn": round(sum(values) / len(values), 6) if values else None,
                "medianReturn": _percentile(values, 50),
                "positiveBreadth": (
                    round(sum(value > 0 for value in values) / len(values), 6)
                    if values
                    else None
                ),
                "weakRatio": (
                    round(sum(value < 0 for value in values) / len(values), 6)
                    if values
                    else None
                ),
                "returnDispersion": (
                    round(max(values) - min(values), 6) if values else None
                ),
                "strongBreadth": None,
                "strongBreadthStatus": "CALIBRATION_PARAMETER_OPEN",
                "memberContributions": None,
                "weightedContribution": None,
                "calibrationEligibility": "PIT_APPROVED_ROWS_ONLY",
            }
        )
    return {
        "artifactVersion": CALIBRATION_CANDIDATE_VERSION,
        "view": view,
        "status": CALIBRATION_STATUS_SUPPORTED
        if aggregates
        else CALIBRATION_STATUS_INSUFFICIENT,
        "aggregateCount": len(aggregates),
        "aggregates": aggregates,
        "productionActive": False,
    }


def calibration_audit(rows: tuple[CalibrationRow, ...]) -> dict[str, object]:
    decisions = [assess_row(row) for row in rows]
    reasons = Counter(reason for decision in decisions for reason in decision.reasons)
    absolute_rows = [
        row for row, decision in zip(rows, decisions, strict=True) if decision.absolute
    ]
    relative_rows = [
        row for row, decision in zip(rows, decisions, strict=True) if decision.relative
    ]
    weighted_rows = [
        row for row, decision in zip(rows, decisions, strict=True) if decision.weighted
    ]
    dates = sorted({row.trading_date for row in rows})
    topic_days = {(row.topic_id, row.trading_date) for row in absolute_rows}
    return {
        "artifactVersion": CALIBRATION_CANDIDATE_VERSION,
        "rowSchemaVersion": CALIBRATION_ROW_SCHEMA_VERSION,
        "inputRowCount": len(rows),
        "historicalDateRange": {
            "start": dates[0].isoformat() if dates else None,
            "end": dates[-1].isoformat() if dates else None,
        },
        "instrumentCount": len({row.instrument_id for row in rows}),
        "eligibleInstrumentCount": len({row.instrument_id for row in absolute_rows}),
        "eligibleTopicDayCount": len(topic_days),
        "absoluteEligibleMemberRows": len(absolute_rows),
        "relativeEligibleMemberRows": len(relative_rows),
        "weightedEligibleMemberRows": len(weighted_rows),
        "roleAuthorityCoverage": round(len(absolute_rows) / len(rows), 6) if rows else 0.0,
        "benchmarkCoverage": round(len(relative_rows) / len(absolute_rows), 6)
        if absolute_rows
        else 0.0,
        "exclusionReasons": dict(sorted(reasons.items())),
        "status": CALIBRATION_STATUS_SUPPORTED
        if absolute_rows and relative_rows
        else CALIBRATION_STATUS_INSUFFICIENT,
        "noLookahead": True,
        "productionActive": False,
    }


def candidate_parameter_bundle(
    audit: dict[str, object],
    *,
    evidence_window: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return candidate slots without inventing values or activating policy."""

    eligible = int(audit.get("absoluteEligibleMemberRows") or 0)
    status = CALIBRATION_STATUS_PROVISIONAL if eligible else CALIBRATION_STATUS_INSUFFICIENT
    limitation = (
        "Candidate fitting is blocked until strict PIT rows are available."
        if not eligible
        else "Candidate values require Owner review and replay diagnostics."
    )
    return {
        "artifactVersion": CALIBRATION_CANDIDATE_VERSION,
        "status": status,
        "productionActive": False,
        "evidenceWindow": evidence_window or {},
        "parameters": [
            {
                "parameterName": name,
                "system": system,
                "status": status,
                "candidateValue": None,
                "sampleCount": eligible,
                "method": "DESCRIPTIVE_PIT_NO_LOOKAHEAD_PENDING",
                "limitations": [limitation],
                "ownerApprovalRequired": True,
                "productionActive": False,
            }
            for name, system in CALIBRATION_PARAMETERS
        ],
    }


def pm_review_header() -> tuple[str, ...]:
    return (
        "date",
        "topic",
        "formal_member_count",
        "REP_evidence",
        "CORE_evidence",
        "RELATED_evidence",
        "absolute_strength",
        "absolute_grade",
        "relative_strength",
        "relative_grade",
        "previous_lifecycle",
        "candidate_lifecycle",
        "final_lifecycle",
        "transition_reason",
        "coverage",
        "policy_version",
        "calibration_version",
        "PM_EXPECTED_ABSOLUTE_GRADE",
        "PM_EXPECTED_RELATIVE_GRADE",
        "PM_EXPECTED_LIFECYCLE",
        "PM_RESULT",
        "PM_NOTE",
    )


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_pm_review(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerow(pm_review_header())


__all__ = [
    "CALIBRATION_CANDIDATE_VERSION",
    "CALIBRATION_PARAMETERS",
    "CALIBRATION_ROW_SCHEMA_VERSION",
    "CALIBRATION_STATUS_INSUFFICIENT",
    "CALIBRATION_STATUS_OWNER_REQUIRED",
    "CALIBRATION_STATUS_PROVISIONAL",
    "CALIBRATION_STATUS_SUPPORTED",
    "CALIBRATION_STATUS_WEAK",
    "CalibrationRow",
    "HistoricalCalibrationError",
    "RowEligibility",
    "assess_row",
    "calibration_audit",
    "candidate_parameter_bundle",
    "canonical_market",
    "load_csv",
    "load_jsonl",
    "member_return_distributions",
    "pm_review_header",
    "topic_role_day_aggregates",
    "write_json",
    "write_pm_review",
]

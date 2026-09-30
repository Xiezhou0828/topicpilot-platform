# ruff: noqa: RUF001, E501
"""Deterministic V2 Today/Home materialization and publication policy.

The request path reads the persisted envelope produced here.  This module is
deliberately provider-neutral: official index/aggregate adapters hand in
typed facts, while canonical daily observations remain a compatibility
fallback only when the established post-close path has not supplied an
official whole-market aggregate result.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from topicpilot_api.daily_market import (
    build_unavailable_instruments,
    read_daily_market_rows,
)
from topicpilot_api.market_data.availability import LEGITIMATE_UNAVAILABLE_CODES
from topicpilot_api.market_signals import build_market_signals as build_v1_market_signals
from topicpilot_api.market_signals import catalog_payload, evaluate_v1_signals
from topicpilot_api.orm import HomeMarketFact, HomePublication, HomePublicationSection
from topicpilot_api.today_topic_lower_half import (
    build_topic_pulse,
    calculate_fast_rotation,
    rank_formal_topics,
)

HOME_PUBLICATION_VERSION = "home-v2.formal.v1"
HOME_SOURCE = "HOME_V2_FORMAL_PUBLICATION"
DAILY_FOCUS_SOURCE = "HOME_V2_DAILY_FOCUS_RULE_V1"
MAIN_TOPICS_SOURCE = "HOME_V2_FORMAL_TOPIC_PUBLICATION"
TOPIC_PULSE_SOURCE = "HOME_V2_FORMAL_TOPIC_PULSE"
ROTATION_SOURCE = "HOME_V2_ROTATION_5_SESSION_ABSOLUTE_STRENGTH"
SECTION_KEYS = (
    "marketOverview",
    "dailyFocus",
    "mainTopics",
    "heatingTopics",
    "coolingTopics",
    "marketEvents",
    "opportunities",
)

MARKET_DISTRIBUTION_SOURCE = "topicpilot.vw_daily_market_observations"
_NO_TRADE_STATUS_CODES = frozenset(
    LEGITIMATE_UNAVAILABLE_CODES
)
MARKET_DISTRIBUTION_BUCKETS = (
    ("PCT_GE_10", "漲幅 ≥10%（未確認漲停）"),
    ("PCT_7_TO_10", "漲幅 7% 至未滿 10%"),
    ("PCT_3_TO_7", "漲幅 3% 至未滿 7%"),
    ("PCT_0_TO_3", "漲幅 0% 至未滿 3%"),
    ("FLAT", "平盤"),
    ("PCT_NEG_0_TO_3", "跌幅 0% 至未滿 3%"),
    ("PCT_NEG_3_TO_7", "跌幅 3% 至未滿 7%"),
    ("PCT_NEG_7_TO_10", "跌幅 7% 至未滿 10%"),
    ("PCT_LE_NEG_10", "跌幅 ≥10%（未確認跌停）"),
)

MARKET_SIGNAL_CATALOG = tuple(catalog_payload())
build_market_signals = build_v1_market_signals

USER_MESSAGES = {
    "NO_PUBLISHED_MARKET_FACTS": "市場資料尚未完整。",
    "NO_FORMAL_TOPIC_PUBLICATION": "題材資料尚未完成發布。",
    "INSUFFICIENT_FORMAL_STRENGTH_HISTORY": "目前正式 Topic Strength 歷史不足 5 個交易日，暫無法計算快速升溫／退潮。",
    "NO_FORMAL_STRENGTH_SCORE": "正式 Topic Strength 分數目前無法提供。",
    "DAILY_FOCUS_EVIDENCE_INCOMPLETE": "今日市場重點尚未完成。",
    "UPSTREAM_SOURCE_UNAVAILABLE": "這項市場資料目前無法提供。",
    "NO_FORMAL_MARKET_BREADTH": "市場廣度資料目前無法提供。",
    "PARTIAL_MARKET_FACTS": "部分市場資料目前無法提供。",
    "OPTIONAL_SECTION_NOT_FORMAL": "此區塊目前尚未建立正式資料來源。",
}


@dataclass(frozen=True)
class MarketTurnoverFact:
    market: str
    trading_date: date
    value: Decimal | None
    currency: str | None
    unit: str | None
    scale: int | None
    as_of: datetime | None
    source: str
    lineage: str
    status: str = "AVAILABLE"
    reason_code: str | None = None


@dataclass(frozen=True)
class SectionResult:
    status: str
    data_date: date | None
    as_of: datetime | None
    source: str | None
    reason_code: str | None
    user_message: str | None
    payload: Any
    diagnostic_detail: str | None = None

    def status_payload(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "dataDate": self.data_date,
            "asOf": self.as_of,
            "source": self.source,
            "reasonCode": self.reason_code,
            "userMessage": self.user_message,
        }


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value) if value.is_finite() else None
    return value


def _hash(value: Any) -> str:
    encoded = json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _number(value: Any) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _reason(code: str | None) -> str | None:
    return USER_MESSAGES.get(code) if code else None


def _status(
    status: str,
    *,
    data_date: date | None,
    as_of: datetime | None,
    source: str | None,
    reason_code: str | None = None,
    detail: str | None = None,
    payload: Any,
) -> SectionResult:
    return SectionResult(
        status=status,
        data_date=data_date,
        as_of=as_of,
        source=source,
        reason_code=reason_code,
        user_message=_reason(reason_code),
        payload=payload,
        diagnostic_detail=detail,
    )


def _signal_change_text(item: Mapping[str, Any], label: str) -> str:
    change = item.get("change")
    if not isinstance(change, (int, float)) or isinstance(change, bool):
        return f"{label}漲跌點尚未提供"
    change_text = f"{change:+g} 點"
    change_pct = item.get("changePct")
    if isinstance(change_pct, (int, float)) and not isinstance(change_pct, bool):
        change_text += f"（{change_pct:+g}%）"
    return f"{label} {change_text}"


def build_daily_focus(
    *,
    market_overview: Mapping[str, Any],
    main_topics: Sequence[Mapping[str, Any]],
    heating_topics: Sequence[Mapping[str, Any]],
    cooling_topics: Sequence[Mapping[str, Any]],
    data_date: date | None,
    as_of: datetime | None,
    history: Sequence[Mapping[str, Any]] = (),
    topic_observations: Sequence[Mapping[str, Any]] = (),
) -> SectionResult:
    """Build formal market signals from published facts only."""

    has_market_evidence = bool(
        (market_overview.get("indices") or [])
        or (market_overview.get("turnover") or [])
        or (market_overview.get("breadth") or [])
        or (market_overview.get("marketHealth") or {}).get("breadthEligible")
    )
    signal_catalog = [dict(item) for item in MARKET_SIGNAL_CATALOG]
    signals = (
        evaluate_v1_signals(
            market_overview,
            history=history,
            topic_observations=topic_observations,
            trading_date=data_date,
        )
        if has_market_evidence
        else []
    )
    active_signals = [item for item in signals if item.get("isActive")]
    if not has_market_evidence:
        return _status(
            "UNAVAILABLE",
            data_date=data_date,
            as_of=as_of,
            source=DAILY_FOCUS_SOURCE,
            reason_code="DAILY_FOCUS_EVIDENCE_INCOMPLETE",
            detail="formal Home inputs did not contain a meaningful market fact",
            payload={
                "mode": "RULE_BASED_V1",
                "temporary": False,
                "headline": "今日市場訊號尚未完成",
                "bullets": [],
                "signals": [],
                "signalCatalog": signal_catalog,
                "dataDate": data_date,
                "source": DAILY_FOCUS_SOURCE,
                "reasonCode": "DAILY_FOCUS_EVIDENCE_INCOMPLETE",
                "userMessage": USER_MESSAGES["DAILY_FOCUS_EVIDENCE_INCOMPLETE"],
            },
        )
    headline = active_signals[0]["title"] if active_signals else "今日無異常訊號"
    return _status(
        "AVAILABLE",
        data_date=data_date,
        as_of=as_of,
        source=DAILY_FOCUS_SOURCE,
        payload={
            "mode": "RULE_BASED_V1",
            "temporary": False,
            "headline": headline,
            "bullets": [item["summary"] for item in active_signals[:4]] or ["目前沒有符合正式規則的市場訊號。"],
            "signals": signals,
            "signalCatalog": signal_catalog,
            "dataDate": data_date,
            "source": DAILY_FOCUS_SOURCE,
        },
    )


def validate_home_gate(
    *, market_overview: SectionResult, main_topics: SectionResult, daily_focus: SectionResult
) -> tuple[str, str | None]:
    """Return the core Home finality gate.

    Market/session authority is the only section-level data requirement for a
    publishable envelope.  Main Topics and Daily Focus are independently
    typed sections: they are published when evidence exists and remain
    unavailable when it does not, without poisoning the whole Home envelope.
    """

    market_payload = market_overview.payload if isinstance(market_overview.payload, Mapping) else {}
    health = market_payload.get("marketHealth") or {}
    breadth = market_payload.get("breadth") or []
    coverage = market_payload.get("coverage") or {}
    if int(coverage.get("pipelineFailureCount") or 0) or int(
        coverage.get("unknownCount") or 0
    ):
        return "UNAVAILABLE", "NO_PUBLISHED_MARKET_FACTS"
    market_minimum = bool(
        any(int(item.get("observed") or 0) > 0 for item in breadth)
        or health.get("advance") is not None
        or any(item.get("value") is not None for item in market_payload.get("indices", []))
    )
    if market_minimum and market_overview.status in {"AVAILABLE", "PARTIAL"}:
        return "PUBLISHED", None
    if not market_minimum:
        return "UNAVAILABLE", "NO_PUBLISHED_MARKET_FACTS"
    return "UNAVAILABLE", "NO_PUBLISHED_MARKET_FACTS"


def _latest_canonical_date(session: Session) -> date | None:
    return session.execute(
        text(
            """
            SELECT max((co.observed_at AT TIME ZONE m.timezone)::date)
            FROM topicpilot.canonical_observations co
            JOIN topicpilot.canonical_price_observations cp
              ON cp.canonical_observation_id = co.id
            JOIN topicpilot.instruments i ON i.id = co.instrument_id
            JOIN topicpilot.markets m ON m.id = i.market_id
            JOIN topicpilot.market_data_sources source ON source.id = co.source_id
            WHERE co.family_code = 'PRICE'
              AND co.quality_state = 'ACCEPTED'
              AND source.observation_semantics = 'DAILY_BAR'
              AND cp.close IS NOT NULL
            """
        )
    ).scalar_one_or_none()


def _distribution_bucket(change_pct: Decimal) -> str:
    if change_pct >= Decimal("10"):
        return "PCT_GE_10"
    if change_pct >= Decimal("7"):
        return "PCT_7_TO_10"
    if change_pct >= Decimal("3"):
        return "PCT_3_TO_7"
    if change_pct > 0:
        return "PCT_0_TO_3"
    if change_pct == 0:
        return "FLAT"
    if change_pct > Decimal("-3"):
        return "PCT_NEG_0_TO_3"
    if change_pct > Decimal("-7"):
        return "PCT_NEG_3_TO_7"
    if change_pct > Decimal("-10"):
        return "PCT_NEG_7_TO_10"
    return "PCT_LE_NEG_10"


def build_market_distribution(
    observations: Iterable[Mapping[str, Any]],
    *,
    eligible_count: int,
    as_of: datetime | None,
    source: str = MARKET_DISTRIBUTION_SOURCE,
) -> dict[str, Any]:
    """Aggregate canonical EOD observations without turning missing data into 0%."""

    counts = {key: 0 for key, _label in MARKET_DISTRIBUTION_BUCKETS}
    for row in observations:
        if row.get("instrument_id") is None:
            continue
        if str(row.get("status_code") or "UNKNOWN").upper() in _NO_TRADE_STATUS_CODES:
            continue
        try:
            close = Decimal(str(row.get("close")))
            previous_close = Decimal(str(row.get("previous_close")))
        except (InvalidOperation, TypeError, ValueError):
            continue
        if not close.is_finite() or not previous_close.is_finite() or previous_close <= 0:
            continue
        change_pct = (close - previous_close) / previous_close * Decimal("100")
        counts[_distribution_bucket(change_pct)] += 1

    eligible = sum(counts.values())
    return {
        "market": "TPE+TWO",
        "status": "AVAILABLE" if eligible else "UNAVAILABLE",
        "eligible": eligible,
        "excluded": max(0, int(eligible_count) - eligible),
        "buckets": [
            {
                "key": key,
                "label": label,
                "count": counts[key],
                "percentage": round(counts[key] / eligible * 100, 4) if eligible else None,
            }
            for key, label in MARKET_DISTRIBUTION_BUCKETS
        ],
        "coverage": {
            "denominator": "active date-effective EQUITY instruments in TPE/TWO",
            "universeLabel": (
                "上市＋上櫃活躍、具日期效力的 EQUITY；分布僅納入正式收盤與前收完整者"
            ),
            "eligibleUniverse": int(eligible_count),
            "percentageEligible": round(eligible / int(eligible_count) * 100, 4)
            if int(eligible_count)
            else 0,
            "breadthEligible": eligible,
            "distributionTotal": eligible,
            "reconciliationStatus": "PASS" if eligible else "UNAVAILABLE",
            "exclusionCount": max(0, int(eligible_count) - eligible),
            "exclusionReason": (
                "NO_TRADE_OR_MISSING_CLOSE_OR_PREVIOUS_CLOSE"
                if int(eligible_count) > eligible
                else None
            ),
        },
        "asOf": as_of,
        "source": source,
        "reasonCode": None if eligible else "NO_PERCENT_CHANGE_OBSERVATIONS",
    }


def _breadth(
    session: Session, trading_date: date
) -> tuple[list[dict[str, Any]], datetime | None, list[dict[str, Any]]]:
    raw_rows = read_daily_market_rows(session, trading_date)
    unavailable = build_unavailable_instruments(raw_rows, trade_date=trading_date)
    observations: list[dict[str, Any]] = []
    for row in raw_rows:
        current_observed_at = row.get("observed_at") or row.get("status_observed_at")
        status_code = str(
            row.get("status_code") or row.get("price_status_code") or "UNKNOWN"
        ).upper()
        observations.append(
            {
                **row,
                "universe_instrument_id": row.get("instrument_id"),
                "instrument_id": row.get("instrument_id"),
                "status_code": status_code,
                "observed_at": current_observed_at,
            }
        )
    aggregate: dict[str, dict[str, Any]] = {}
    for row in observations:
        market = str(row["market"])
        item = aggregate.setdefault(
            market,
            {
                "market": market,
                "eligible": 0,
                "observed": 0,
                "priced": 0,
                "advance": 0,
                "decline": 0,
                "flat": 0,
                "unavailable": 0,
                "pipeline_failure": 0,
                "unknown": 0,
                "as_of": None,
            },
        )
        item["eligible"] += 1
        current_has_evidence = row.get("observed_at") is not None or row.get(
            "status_observation_id"
        ) is not None
        if current_has_evidence:
            item["observed"] += 1
        if row["observed_at"] is not None and (
            item["as_of"] is None or row["observed_at"] > item["as_of"]
        ):
            item["as_of"] = row["observed_at"]
        if row.get("close") is None:
            item["unavailable"] += 1
            item["pipeline_failure"] += sum(
                unavailable_item.market == market
                and unavailable_item.symbol == row.get("symbol")
                and unavailable_item.reason_code
                in {"MISSING_MARKET_DATA", "PROVIDER_ERROR", "DATE_MISMATCH"}
                for unavailable_item in unavailable
            )
            item["unknown"] += sum(
                unavailable_item.market == market
                and unavailable_item.symbol == row.get("symbol")
                and unavailable_item.status == "UNKNOWN"
                and unavailable_item.reason_code
                not in {"MISSING_MARKET_DATA", "PROVIDER_ERROR", "DATE_MISMATCH"}
                for unavailable_item in unavailable
            )
            continue
        if row["close"] is not None and row["close"] > 0:
            item["priced"] += 1
        if row["close"] is not None and row["previous_close"] is not None:
            if row["close"] > row["previous_close"]:
                item["advance"] += 1
            elif row["close"] < row["previous_close"]:
                item["decline"] += 1
            else:
                item["flat"] += 1
    as_of = max(
        (row["as_of"] for row in aggregate.values() if row["as_of"] is not None),
        default=None,
    )
    return [aggregate[key] for key in sorted(aggregate)], as_of, observations


def _formal_topic_rows(session: Session, trading_date: date) -> list[dict[str, Any]]:
    return _formal_topic_state_rows(session, trading_date=trading_date, current_only=True)


def _formal_topic_history(session: Session, trading_date: date) -> list[dict[str, Any]]:
    return _formal_topic_state_rows(session, trading_date=trading_date, current_only=False)


def _json_metric(payload: Any, names: Sequence[str]) -> float | None:
    """Read a named metric from either object-shaped or component-list JSON."""

    if isinstance(payload, Mapping):
        for name in names:
            value = payload.get(name)
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, Mapping):
                continue
            name = item.get("name") or item.get("key")
            if name in names:
                try:
                    return float(item.get("value"))
                except (TypeError, ValueError):
                    continue
    return None


def _json_value(payload: Any, names: Sequence[str]) -> Any:
    if isinstance(payload, Mapping):
        for name in names:
            value = payload.get(name)
            if value is not None:
                return value
    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, Mapping):
                continue
            name = item.get("name") or item.get("key")
            if name in names:
                return item.get("value")
    return None


def _formal_topic_state_rows(
    session: Session, *, trading_date: date, current_only: bool
) -> list[dict[str, Any]]:
    """Read the dynamic formal Topic universe plus formal Score/Lifecycle facts."""

    date_filter = "s.snapshot_date = :trading_date" if current_only else "s.snapshot_date <= :trading_date"
    rows = session.execute(
        text(
            f"""
            WITH current_snapshots AS (
                SELECT DISTINCT ON (s.topic_id, s.snapshot_date)
                    s.*
                FROM topicpilot.topic_snapshots s
                JOIN topicpilot.topics t ON t.id = s.topic_id
                WHERE {date_filter}
                  AND s.publication_mode = 'FORMAL'
                  AND s.membership_mode = 'PIT_FORMAL'
                  AND s.publication_state = 'PUBLISHED'
                  AND s.finality_state = 'FINAL'
                  AND t.status NOT IN ('DISABLED', 'RETIRED')
                  AND (t.valid_from IS NULL OR t.valid_from <= s.snapshot_date)
                  AND (t.valid_to IS NULL OR t.valid_to >= s.snapshot_date)
                  AND NOT EXISTS (
                      SELECT 1 FROM topicpilot.topic_snapshots successor
                      WHERE successor.supersedes_snapshot_id = s.id
                  )
                ORDER BY s.topic_id, s.snapshot_date, s.correction_sequence DESC,
                         s.published_at DESC NULLS LAST, s.id DESC
            ), formal_scores AS (
                SELECT DISTINCT ON (r.topic_id, r.evaluation_date)
                    r.topic_id, r.evaluation_date, r.score AS formal_score,
                    r.grade AS formal_grade, r.eligibility AS score_eligibility,
                    r.evaluation_status AS score_evaluation_status,
                    r.publication_status AS score_publication_status,
                    r.components AS score_components,
                    r.quality_flags AS score_quality_flags,
                    r.policy_id AS score_policy_id,
                    r.as_of_at AS score_as_of_at
                FROM topicpilot.topic_score_formal_results r
                WHERE r.publication_mode = 'FORMAL'
                  AND r.publication_status = 'PUBLISHED'
                  AND r.supersession_state = 'ACTIVE'
                ORDER BY r.topic_id, r.evaluation_date, r.decision_revision DESC,
                         r.published_at DESC NULLS LAST, r.id DESC
            ), formal_lifecycle AS (
                SELECT DISTINCT ON (r.topic_id, r.evaluation_date)
                    r.topic_id, r.evaluation_date, r.previous_stage,
                    r.candidate_stage, r.final_stage, r.stage_trading_days,
                    r.evaluation_status AS lifecycle_evaluation_status,
                    r.data_status AS lifecycle_data_status,
                    r.transition_reason, r.confirmation_state,
                    r.state_memory, r.persistence_evidence,
                    r.sample_confidence, r.publication_status AS lifecycle_publication_status,
                    r.as_of_at AS lifecycle_as_of_at
                FROM topicpilot.topic_lifecycle_formal_results r
                WHERE r.evaluation_mode = 'FORMAL'
                  AND r.publication_status = 'PUBLISHED'
                  AND r.supersession_state = 'ACTIVE'
                ORDER BY r.topic_id, r.evaluation_date, r.decision_revision DESC,
                         r.published_at DESC NULLS LAST, r.id DESC
            )
            SELECT s.topic_id, s.topic_slug, s.topic_name, s.snapshot_date,
                   s.stock_count, s.eligible_count, s.observed_stock_count,
                   s.coverage_pct, s.data_status, s.as_of_at, s.published_at,
                   s.source_artifact_hash,
                   f.formal_score, f.formal_grade, f.score_eligibility,
                   f.score_evaluation_status, f.score_publication_status,
                   f.score_components, f.score_quality_flags, f.score_policy_id,
                   f.score_as_of_at,
                   l.previous_stage, l.candidate_stage, l.final_stage,
                   l.stage_trading_days, l.lifecycle_evaluation_status,
                   l.lifecycle_data_status, l.transition_reason,
                   l.confirmation_state, l.state_memory, l.persistence_evidence,
                   l.sample_confidence, l.lifecycle_publication_status,
                   l.lifecycle_as_of_at
            FROM current_snapshots s
            LEFT JOIN formal_scores f
              ON f.topic_id = s.topic_id AND f.evaluation_date = s.snapshot_date
            LEFT JOIN formal_lifecycle l
              ON l.topic_id = s.topic_id AND l.evaluation_date = s.snapshot_date
            ORDER BY s.snapshot_date, s.topic_slug
            """
        ),
        {"trading_date": trading_date},
    ).mappings()

    result: list[dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        components = row.get("score_components")
        absolute = _json_metric(components, ("absolute_score", "absoluteScore", "absolute_total"))
        relative = _json_metric(components, ("relative_score", "relativeScore", "relative_total"))
        absolute_block = _json_value(components, ("absolute", "ABSOLUTE"))
        relative_block = _json_value(components, ("relative", "RELATIVE"))
        if absolute is None:
            absolute = _json_metric(
                absolute_block, ("score", "absolute_score", "absoluteScore")
            )
        if relative is None:
            relative = _json_metric(
                relative_block, ("score", "relative_score", "relativeScore")
            )
        absolute_grade = _json_value(components, ("absolute_grade", "absoluteGrade"))
        relative_grade = _json_value(components, ("relative_grade", "relativeGrade"))
        if absolute_grade is None:
            absolute_grade = _json_value(
                absolute_block, ("grade", "absolute_grade", "absoluteGrade")
            )
        if relative_grade is None:
            relative_grade = _json_value(
                relative_block, ("grade", "relative_grade", "relativeGrade")
            )
        quality_flags = row.get("score_quality_flags") or {}
        confirmation = row.get("confirmation_state") or {}
        persistence = row.get("persistence_evidence") or {}
        state_memory = row.get("state_memory") or {}
        observation_flags = []
        if isinstance(quality_flags, Mapping):
            observation_flags = quality_flags.get("observationFlags") or quality_flags.get(
                "observation_flags"
            ) or []
        meaningful_expansion = _json_value(
            persistence, ("meaningfulExpansion", "meaningful_expansion")
        )
        renewed_expansion = _json_value(
            persistence, ("renewedExpansion", "renewed_expansion")
        )
        if meaningful_expansion is None:
            meaningful_expansion = _json_value(
                state_memory, ("meaningfulExpansion", "meaningful_expansion")
            )
        if renewed_expansion is None:
            renewed_expansion = _json_value(
                state_memory, ("renewedExpansion", "renewed_expansion")
            )
        persistence_days = row.get("stage_trading_days")
        if persistence_days is None and isinstance(persistence, Mapping):
            persistence_days = persistence.get("tradingDays")
        authority_valid = bool(
            row.get("score_publication_status") == "PUBLISHED"
            and row.get("lifecycle_publication_status") == "PUBLISHED"
            and row.get("score_evaluation_status") not in {None, "UNAVAILABLE"}
            and row.get("lifecycle_evaluation_status") not in {None, "UNAVAILABLE"}
            and row.get("formal_grade") in {"S", "A", "B", "D"}
            and row.get("final_stage")
            and absolute is not None
            and row.get("eligible_count", row.get("stock_count")) is not None
        )
        row.update(
            {
                "formal_member_count": row.get("eligible_count") or row.get("stock_count"),
                "formal_daily_grade": row.get("formal_grade"),
                "absolute_score": absolute,
                "relative_score": relative,
                "absolute_grade": absolute_grade,
                "relative_grade": relative_grade,
                "formal_lifecycle": row.get("final_stage"),
                "lifecycle_candidate": row.get("candidate_stage"),
                "candidate_confirmation_current": confirmation.get("current") if isinstance(confirmation, Mapping) else None,
                "candidate_confirmation_required": confirmation.get("required") if isinstance(confirmation, Mapping) else None,
                "confirmation_progress": confirmation if isinstance(confirmation, Mapping) else None,
                "persistence_days": persistence_days,
                "renewed_expansion": renewed_expansion if isinstance(renewed_expansion, bool) else None,
                "meaningful_expansion": meaningful_expansion if isinstance(meaningful_expansion, bool) else None,
                "observation_flags": observation_flags,
                "transition_reason": row.get("transition_reason"),
                "evaluation_status": row.get("lifecycle_evaluation_status") or row.get("score_evaluation_status"),
                "authority_status": "VALID" if authority_valid else "NOT_EVALUABLE",
                "authority_quality_valid": authority_valid,
                "as_of_at": max(
                    (value for value in (row.get("as_of_at"), row.get("score_as_of_at"), row.get("lifecycle_as_of_at")) if value is not None),
                    default=None,
                ),
            }
        )
        result.append(row)
    return result


def _market_index_payload(fact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "market": fact.get("market"),
        "indexCode": fact.get("indexCode"),
        "indexName": fact.get("indexName"),
        "tradingDate": fact.get("tradingDate"),
        "session": fact.get("session"),
        "value": _number(fact.get("value")),
        "open": _number(fact.get("open")),
        "high": _number(fact.get("high")),
        "low": _number(fact.get("low")),
        "previousClose": _number(fact.get("previousClose")),
        "change": _number(fact.get("change")),
        "changePct": _number(fact.get("changePct")),
        "asOf": fact.get("asOf"),
        "source": fact.get("source"),
        "sourceDataset": fact.get("sourceDataset"),
        "sourceEndpoint": fact.get("sourceEndpoint"),
        "lineage": fact.get("lineage"),
        "status": fact.get("status", "AVAILABLE"),
        "reasonCode": fact.get("reasonCode"),
    }


def _index_fact_input(item: Any) -> dict[str, Any]:
    if hasattr(item, "to_dict"):
        # Keep typed date/time/numeric values for SQLAlchemy persistence.  The
        # public ``to_dict`` shape is intentionally JSON-safe and therefore
        # contains ISO strings, which are not suitable for DateTime columns.
        status = getattr(item, "data_status", "UNAVAILABLE")
        status = getattr(status, "value", status)
        return {
            "market": getattr(item, "market", None),
            "indexCode": getattr(item, "index_identity", None),
            "indexName": getattr(item, "display_name", None),
            "tradingDate": getattr(item, "trading_date", None),
            "session": "CLOSE",
            "value": getattr(item, "value", None),
            "open": getattr(item, "open", None),
            "high": getattr(item, "high", None),
            "low": getattr(item, "low", None),
            "previousClose": getattr(item, "previous_close", None),
            "change": getattr(item, "change", None),
            "changePct": getattr(item, "change_pct", None),
            "asOf": getattr(item, "as_of", None),
            "source": getattr(item, "source_identity", None),
            "sourceDataset": getattr(item, "source_dataset", None),
            "sourceEndpoint": getattr(item, "source_endpoint", None),
            "lineage": getattr(item, "lineage", None),
            "status": status,
            "reasonCode": getattr(item, "status_reason", None),
        }
    return dict(item)


def _turnover_payload(item: MarketTurnoverFact | Mapping[str, Any]) -> dict[str, Any]:
    raw = item if isinstance(item, Mapping) else item.__dict__
    return {
        "market": raw.get("market"),
        "tradingDate": raw.get("trading_date", raw.get("tradingDate")),
        "session": raw.get("session", "CLOSE"),
        "value": _number(raw.get("value")),
        "currency": raw.get("currency"),
        "unit": raw.get("unit"),
        "scale": raw.get("scale"),
        "asOf": raw.get("as_of", raw.get("asOf")),
        "source": raw.get("source"),
        "sourceDataset": raw.get("source_dataset", raw.get("sourceDataset")),
        "sourceEndpoint": raw.get("source_endpoint", raw.get("sourceEndpoint")),
        "lineage": raw.get("lineage"),
        "status": raw.get("status", "AVAILABLE"),
        "reasonCode": raw.get("reason_code", raw.get("reasonCode")),
    }


def _derived_total_turnover(
    turnover: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Derive a total only from two matching formal TWD close facts."""

    by_market = {str(item.get("market")): item for item in turnover}
    records = [by_market.get("TPE"), by_market.get("TWO")]
    if any(item is None for item in records):
        return None
    if any(
        str(item.get("status") or "").upper() not in {"AVAILABLE", "PUBLISHED", "FORMAL"}
        for item in records
    ):
        return None
    if {str(item.get("currency") or "").strip().upper() for item in records} != {"TWD"}:
        return None
    if {str(item.get("unit") or "").strip().upper() for item in records} != {"TWD"}:
        return None
    if {item.get("scale") for item in records} != {0}:
        return None
    try:
        values = [Decimal(str(item["value"])) for item in records]
    except (KeyError, InvalidOperation, TypeError, ValueError):
        return None
    if any(not value.is_finite() for value in values):
        return None
    first = records[0]
    return {
        "market": "TOTAL",
        "tradingDate": first.get("tradingDate"),
        "session": first.get("session", "CLOSE"),
        "value": _number(values[0] + values[1]),
        "currency": "TWD",
        "unit": "TWD",
        "scale": 0,
        "asOf": max((item.get("asOf") for item in records if item.get("asOf")), default=None),
        "source": "HOME_V2_FORMAL_TURNOVER_TOTAL",
        "lineage": "deterministic sum of matching TPE/TWO formal close facts",
        "status": "AVAILABLE",
        "reasonCode": None,
    }


def _read_previous_session_turnover(
    session: Session, trading_date: date | None
) -> dict[str, Any] | None:
    """Read the latest prior formal close session without using calendar dates."""

    if trading_date is None:
        return None
    try:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT f.market, f.trading_date AS "tradingDate",
                           f.session, f.value, f.currency, f.unit, f.scale,
                           f.as_of_at AS "asOf", f.source, f.lineage,
                           f.publication_state AS status, f.reason_code AS "reasonCode",
                           p.published_at AS "publishedAt"
                    FROM topicpilot.home_market_facts f
                    JOIN topicpilot.home_publications p ON p.id = f.publication_id
                    WHERE f.fact_type = 'TURNOVER'
                      AND f.market IN ('TPE', 'TWO')
                      AND f.trading_date < :trading_date
                      AND p.publication_state = 'PUBLISHED'
                      AND f.publication_state IN ('MATERIALIZED', 'VALIDATED', 'PUBLISHED')
                    ORDER BY f.trading_date DESC, p.published_at DESC NULLS LAST,
                             f.created_at DESC, f.market
                    """
                ),
                {"trading_date": trading_date},
            ).mappings()
        ]
    except SQLAlchemyError:
        session.rollback()
        return None

    by_date: dict[date, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        row_date = _as_date(row.get("tradingDate"))
        if row_date is not None:
            by_date[row_date].append(row)
    for candidate_date in sorted(by_date, reverse=True):
        total = _derived_total_turnover(by_date[candidate_date])
        if total is not None:
            return total
    return None


def _turnover_comparison(
    current: Mapping[str, Any], previous: Mapping[str, Any] | None
) -> dict[str, Any] | None:
    """Build a formal current-vs-prior-session comparison, or stay unavailable."""

    if previous is None:
        return None
    try:
        current_value = Decimal(str(current.get("value")))
        previous_value = Decimal(str(previous.get("value")))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if (
        not current_value.is_finite()
        or not previous_value.is_finite()
        or previous_value <= 0
        or str(current.get("status") or "").upper()
        not in {"AVAILABLE", "PUBLISHED", "FORMAL"}
        or str(previous.get("status") or "").upper()
        not in {"AVAILABLE", "PUBLISHED", "FORMAL"}
        or str(current.get("currency") or "").upper() != "TWD"
        or str(previous.get("currency") or "").upper() != "TWD"
        or str(current.get("unit") or "").upper() != "TWD"
        or str(previous.get("unit") or "").upper() != "TWD"
        or current.get("scale") != 0
        or previous.get("scale") != 0
    ):
        return None
    absolute_change = current_value - previous_value
    return {
        "tradingDate": previous.get("tradingDate"),
        "session": previous.get("session", "CLOSE"),
        "value": _number(previous_value),
        "absoluteChange": _number(absolute_change),
        "changePct": _number(absolute_change / previous_value * Decimal("100")),
        "currency": "TWD",
        "unit": "TWD",
        "scale": 0,
        "asOf": previous.get("asOf"),
        "source": previous.get("source"),
        "lineage": "formal prior published trading session; deterministic TPE/TWO total",
        "status": "AVAILABLE",
        "reasonCode": None,
    }


def _attach_turnover_comparison(
    turnover: Sequence[Mapping[str, Any]], previous: Mapping[str, Any] | None
) -> list[dict[str, Any]]:
    """Attach prior-session comparison to the formal TOTAL row only."""

    result = [dict(item) for item in turnover]
    for index, item in enumerate(result):
        if item.get("market") == "TOTAL":
            result[index] = {
                **item,
                "previousSession": _turnover_comparison(item, previous),
            }
            break
    return result


def _as_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def normalize_home_publication_for_read(
    payload: Mapping[str, Any],
    *,
    history: Sequence[Mapping[str, Any]] = (),
    topic_observations: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Rebuild persisted Daily Focus from the current formal market facts."""

    result = dict(payload)
    market_overview = result.get("marketOverview")
    if not isinstance(market_overview, Mapping):
        return result
    overview = dict(market_overview)
    health = overview.get("marketHealth")
    if isinstance(health, Mapping):
        health_copy = dict(health)
        advance = health_copy.get("advance")
        decline = health_copy.get("decline")
        flat = health_copy.get("flat")
        if (
            isinstance(advance, (int, float))
            and not isinstance(advance, bool)
            and isinstance(decline, (int, float))
            and not isinstance(decline, bool)
        ):
            health_copy["net"] = advance - decline
            if (
                isinstance(flat, (int, float))
                and not isinstance(flat, bool)
                and health_copy.get("breadthEligible") is None
            ):
                health_copy["breadthEligible"] = advance + decline + flat
            overview["marketHealth"] = health_copy
    breadth = overview.get("breadth")
    if isinstance(breadth, list):
        overview["breadth"] = [
            {
                **item,
                "coverage": {
                    **(item.get("coverage") or {}),
                    "universeLabel": (
                        item.get("coverage", {}).get("universeLabel")
                        if isinstance(item.get("coverage"), Mapping)
                        and item.get("coverage", {}).get("universeLabel")
                        else "TWSE／TPEx 官方全市場股票彙總的正式廣度觀測"
                    ),
                },
            }
            for item in breadth
            if isinstance(item, Mapping)
        ]
    turnover = overview.get("turnover")
    if isinstance(turnover, list) and not any(
        isinstance(item, Mapping) and item.get("market") == "TOTAL" for item in turnover
    ):
        total_turnover = _derived_total_turnover(
            [item for item in turnover if isinstance(item, Mapping)]
        )
        if total_turnover is not None:
            overview["turnover"] = [*turnover, total_turnover]
    result["marketOverview"] = overview

    data_date = _as_date(
        overview.get("dataDate")
        or (result.get("publication") or {}).get("tradingDate")
        or result.get("asOf")
    )
    as_of = _as_datetime(
        overview.get("updatedAt")
        or overview.get("latestSnapshotTime")
        or (result.get("publication") or {}).get("asOf")
    )
    normalized = build_daily_focus(
        market_overview=overview,
        main_topics=(),
        heating_topics=(),
        cooling_topics=(),
        data_date=data_date,
        as_of=as_of,
        history=history,
        topic_observations=topic_observations,
    )
    result["dailyFocus"] = normalized.payload
    statuses = result.get("sectionStatuses")
    if isinstance(statuses, Mapping):
        result["sectionStatuses"] = {
            **statuses,
            "dailyFocus": normalized.status_payload(),
        }
    publication = result.get("publication")
    if isinstance(publication, Mapping) and isinstance(publication.get("completeness"), Mapping):
        publication_copy = dict(publication)
        publication_copy["completeness"] = {
            **publication["completeness"],
            "sectionStatuses": result.get("sectionStatuses", statuses),
        }
        result["publication"] = publication_copy
    return result


def _flow_leg(row: Mapping[str, Any], prefix: str) -> dict[str, Any] | None:
    net = row.get(f"{prefix}_net")
    if net is None:
        return None
    return {
        "buy": _number(row.get(f"{prefix}_buy")),
        "sell": _number(row.get(f"{prefix}_sell")),
        "net": _number(net),
        "value": _number(net),
        "unit": row.get("unit") or "TWD",
        "scale": int(row.get("scale") or 0),
        "status": row.get("availability") or "UNKNOWN",
    }


def _flow_daily_payload(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "market": row.get("market"),
        "tradingDate": row.get("trading_date"),
        "foreign": _flow_leg(row, "foreign"),
        "investmentTrust": _flow_leg(row, "investment_trust"),
        "dealer": _flow_leg(row, "dealer"),
        "total": _flow_leg(row, "total"),
        "sourceProvider": row.get("source_provider"),
        "sourceIdentity": row.get("source_identity"),
        "sourceDataset": row.get("source_dataset"),
        "sourceEndpoint": row.get("source_endpoint"),
        "adapterVersion": row.get("adapter_version"),
        "sourceAsOf": row.get("source_as_of"),
        "publishedAt": row.get("published_at"),
        "retrievedAt": row.get("retrieved_at"),
        "availability": row.get("availability") or "UNKNOWN",
        "freshness": row.get("freshness") or "UNKNOWN",
        "statusReason": row.get("status_reason"),
        "lineage": row.get("lineage") or "formal market institutional flow table",
        "responseContentHash": row.get("response_content_hash"),
    }


def _flow_window(rows: Sequence[Mapping[str, Any]], required_sessions: int) -> dict[str, Any]:
    """Sum the latest complete official sessions, preserving partial coverage."""

    available = [
        row
        for row in rows
        if str(row.get("availability") or "").upper() == "AVAILABLE"
        and all(row.get(f"{prefix}_net") is not None for prefix in (
            "foreign",
            "investment_trust",
            "dealer",
            "total",
        ))
    ][:required_sessions]
    unit = rows[0].get("unit") if rows else "TWD"
    scale = int(rows[0].get("scale") or 0) if rows else 0
    complete = len(available) == required_sessions
    return {
        "requiredSessions": required_sessions,
        "observedSessions": len(available),
        "complete": complete,
        "foreignNet": _number(sum(row["foreign_net"] for row in available)) if complete else None,
        "investmentTrustNet": (
            _number(sum(row["investment_trust_net"] for row in available)) if complete else None
        ),
        "dealerNet": _number(sum(row["dealer_net"] for row in available)) if complete else None,
        "totalNet": _number(sum(row["total_net"] for row in available)) if complete else None,
        "unit": unit or "TWD",
        "scale": scale,
    }


def _aggregate_home_institutional_flow(
    markets: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Expose a whole-market total only when both exchange facts align."""

    if len(markets) < 2:
        return None
    if {item.get("asOfDate") for item in markets} != {markets[0].get("asOfDate")}:
        return None
    current_rows = [item.get("current") for item in markets]
    if not all(isinstance(item, Mapping) for item in current_rows):
        return None
    if any(item.get("availability") != "AVAILABLE" for item in current_rows):
        return None

    combined: dict[str, Any] = {
        "market": "TPE+TWO",
        "tradingDate": current_rows[0].get("tradingDate"),
        "sourceProvider": "TWSE+TPEX",
        "sourceIdentity": "+".join(
            sorted({str(item.get("sourceIdentity")) for item in current_rows})
        ),
        "sourceDataset": "+".join(
            sorted({str(item.get("sourceDataset")) for item in current_rows})
        ),
        "sourceEndpoint": "+".join(
            sorted({str(item.get("sourceEndpoint")) for item in current_rows})
        ),
        "adapterVersion": "+".join(
            sorted({str(item.get("adapterVersion")) for item in current_rows})
        ),
        "sourceAsOf": max(
            (item.get("sourceAsOf") for item in current_rows if item.get("sourceAsOf")),
            default=None,
        ),
        "publishedAt": max(
            (item.get("publishedAt") for item in current_rows if item.get("publishedAt")),
            default=None,
        ),
        "retrievedAt": max(
            (item.get("retrievedAt") for item in current_rows if item.get("retrievedAt")),
            default=None,
        ),
        "availability": "AVAILABLE",
        "freshness": "CURRENT"
        if all(item.get("freshness") == "CURRENT" for item in current_rows)
        else "STALE",
        "statusReason": None,
        "lineage": "deterministic sum of matching TPE/TWO formal institutional-flow facts",
        "responseContentHash": None,
    }
    for leg in ("foreign", "investmentTrust", "dealer", "total"):
        leg_rows = [item.get(leg) for item in current_rows]
        if not all(isinstance(item, Mapping) for item in leg_rows):
            return None
        if any(
            item.get("net") is None or item.get("buy") is None or item.get("sell") is None
            for item in leg_rows
        ):
            return None
        if len({item.get("unit") for item in leg_rows}) != 1:
            return None
        if len({item.get("scale") for item in leg_rows}) != 1:
            return None
        combined[leg] = {
            "buy": _number(sum(item["buy"] for item in leg_rows)),
            "sell": _number(sum(item["sell"] for item in leg_rows)),
            "net": _number(sum(item["net"] for item in leg_rows)),
            "value": _number(sum(item["value"] for item in leg_rows)),
            "unit": current_rows[0].get("unit"),
            "scale": current_rows[0].get("scale"),
            "status": "AVAILABLE",
        }
    return combined


def _read_home_institutional_flow(
    session: Session, trading_date: date | None
) -> dict[str, Any] | None:
    if trading_date is None:
        return None
    try:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT market, trading_date, source_provider, source_identity,
                           source_dataset, source_endpoint, adapter_version,
                           source_as_of, published_at, retrieved_at, unit, scale,
                           foreign_buy, foreign_sell, foreign_net,
                           investment_trust_buy, investment_trust_sell, investment_trust_net,
                           dealer_buy, dealer_sell, dealer_net,
                           total_buy, total_sell, total_net,
                           availability, freshness, status_reason, lineage,
                           response_content_hash
                    FROM topicpilot.market_institutional_flow_daily
                    WHERE trading_date <= :trading_date
                    ORDER BY market, trading_date DESC, source_as_of DESC NULLS LAST,
                             published_at DESC NULLS LAST, id DESC
                    """
                ),
                {"trading_date": trading_date},
            ).mappings()
        ]
    except SQLAlchemyError:
        session.rollback()
        return None
    if not rows:
        return None

    rows_by_market: dict[str, dict[date, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        market = str(row.get("market") or "")
        row_date = _as_date(row.get("trading_date"))
        if market and row_date is not None:
            rows_by_market[market].setdefault(row_date, row)

    # The visible Today card is a same-date whole-market fact.  Historical
    # rows remain available for rolling windows, but they must never be used
    # as a silent carry-forward when either exchange has no current session.
    current_rows = [
        rows_by_market.get(market, {}).get(trading_date)
        for market in ("TPE", "TWO")
    ]
    if any(
        row is None or row.get("availability") != "AVAILABLE"
        for row in current_rows
    ):
        return None

    markets: list[dict[str, Any]] = []
    for market in ("TPE", "TWO"):
        ordered_rows = [
            rows_by_market[market][row_date]
            for row_date in sorted(rows_by_market[market], reverse=True)
        ]
        row = ordered_rows[0]
        current = _flow_daily_payload(row)
        previous = _flow_daily_payload(ordered_rows[1]) if len(ordered_rows) > 1 else None
        availability = str(row.get("availability") or "UNKNOWN")
        markets.append(
            {
                "market": market,
                "asOfDate": row.get("trading_date"),
                "availability": availability,
                "freshness": row.get("freshness") or "UNKNOWN",
                "current": current,
                "previous": previous,
                "rolling5Session": _flow_window(ordered_rows, 5),
                "rolling20Session": _flow_window(ordered_rows, 20),
                "streaks": {},
                "acceleration": {},
                "priceFlowRelation": {
                    "market": market,
                    "indexChange": None,
                    "flowNet": _number(row.get("total_net")),
                    "marketDirection": "UNKNOWN",
                    "flowDirection": "UNKNOWN",
                    "directionRelation": "UNKNOWN",
                    "availability": availability,
                },
                "sourceAsOf": row.get("source_as_of"),
                "source": row.get("source_provider"),
                "statusReason": row.get("status_reason"),
            }
        )
    available = [item for item in markets if item["availability"] == "AVAILABLE"]
    status = "AVAILABLE" if len(available) == len(markets) else "PARTIAL" if available else "UNAVAILABLE"
    freshness_values = {str(item.get("freshness") or "UNKNOWN") for item in markets}
    freshness = "CURRENT" if freshness_values == {"CURRENT"} else "STALE" if "STALE" in freshness_values else "UNKNOWN"
    return {
        "contractVersion": "market-institutional-flow.formal.v1",
        "asOfDate": max((item.get("asOfDate") for item in markets if item.get("asOfDate")), default=None),
        "status": status,
        "freshness": freshness,
        "markets": markets,
        "aggregate": _aggregate_home_institutional_flow(markets),
        "sourceAsOf": max((item.get("sourceAsOf") for item in markets if item.get("sourceAsOf")), default=None),
        "source": ";".join(sorted({str(row.get("source_provider")) for row in rows if row.get("source_provider")})) or None,
        "unit": rows[0].get("unit") or "TWD",
        "scale": int(rows[0].get("scale") or 0),
    }


def _read_signal_home_history(
    session: Session, trading_date: date | None, *, limit: int = 21
) -> list[dict[str, Any]]:
    """Read prior governed Home publications for signal temporal state."""

    if trading_date is None:
        return []
    try:
        rows = session.execute(
            text(
                """
                SELECT trading_date, payload
                FROM topicpilot.home_publications
                WHERE trading_date < :trading_date
                  AND publication_state = 'PUBLISHED'
                ORDER BY trading_date DESC, published_at DESC NULLS LAST,
                         generated_at DESC, id DESC
                LIMIT :limit
                """
            ),
            {"trading_date": trading_date, "limit": limit},
        ).mappings()
    except SQLAlchemyError:
        session.rollback()
        return []
    result: list[dict[str, Any]] = []
    seen: set[date] = set()
    for row in rows:
        row_date = _as_date(row.get("trading_date"))
        payload = row.get("payload")
        if row_date is None or row_date in seen or not isinstance(payload, Mapping):
            continue
        overview = payload.get("marketOverview")
        if not isinstance(overview, Mapping):
            continue
        seen.add(row_date)
        result.append({"tradingDate": row_date, "marketOverview": dict(overview)})
    return result


def _read_signal_institutional_history(
    session: Session, trading_date: date | None
) -> dict[date, dict[str, Any]]:
    """Read same-date TWSE+TPEx official flow facts for signal history."""

    if trading_date is None:
        return {}
    try:
        rows = session.execute(
            text(
                """
                SELECT market, trading_date, unit, scale, availability,
                       foreign_net, investment_trust_net,
                       source_as_of, published_at
                FROM topicpilot.market_institutional_flow_daily
                WHERE trading_date <= :trading_date
                ORDER BY trading_date DESC, market, source_as_of DESC NULLS LAST,
                         published_at DESC NULLS LAST, id DESC
                """
            ),
            {"trading_date": trading_date},
        ).mappings()
    except SQLAlchemyError:
        session.rollback()
        return {}

    grouped: dict[date, dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in rows:
        row_date = _as_date(row.get("trading_date"))
        market = str(row.get("market") or "")
        if row_date is not None and market in {"TPE", "TWO"}:
            grouped[row_date].setdefault(market, row)

    result: dict[date, dict[str, Any]] = {}
    for row_date, by_market in grouped.items():
        if set(by_market) != {"TPE", "TWO"}:
            continue
        markets: list[dict[str, Any]] = []
        for market in ("TPE", "TWO"):
            row = by_market[market]
            availability = str(row.get("availability") or "UNKNOWN")
            current = {
                "tradingDate": row_date,
                "foreign": {
                    "net": _number(row.get("foreign_net")),
                    "status": availability,
                    "unit": row.get("unit") or "TWD",
                    "scale": int(row.get("scale") or 0),
                },
                "investmentTrust": {
                    "net": _number(row.get("investment_trust_net")),
                    "status": availability,
                    "unit": row.get("unit") or "TWD",
                    "scale": int(row.get("scale") or 0),
                },
            }
            markets.append(
                {
                    "market": market,
                    "asOfDate": row_date,
                    "availability": availability,
                    "current": current,
                }
            )
        result[row_date] = {
            "contractVersion": "market-institutional-flow.formal.v1",
            "asOfDate": row_date,
            "status": "AVAILABLE"
            if all(item["availability"] == "AVAILABLE" for item in markets)
            else "UNAVAILABLE",
            "markets": markets,
            "source": "TWSE+TPEX",
        }
    return result


def _read_formal_topic_signal_rows(
    session: Session, trading_date: date | None
) -> list[dict[str, Any]]:
    """Read date-effective formal CORE member facts without score/grade inputs."""

    if trading_date is None:
        return []
    try:
        rows = session.execute(
            text(
                """
                SELECT ts.snapshot_date, ts.topic_id, ts.topic_slug, ts.topic_name,
                       ts.stock_count AS formal_member_count,
                       mf.structural_role, mf.fact_state, mf.change_pct
                FROM topicpilot.topic_snapshots ts
                JOIN topicpilot.topic_snapshot_member_facts mf
                  ON mf.snapshot_id = ts.id
                WHERE ts.snapshot_date <= :trading_date
                  AND ts.publication_mode = 'FORMAL'
                  AND ts.publication_state = 'PUBLISHED'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM topicpilot.topic_snapshots successor
                      WHERE successor.supersedes_snapshot_id = ts.id
                  )
                ORDER BY ts.snapshot_date DESC, ts.topic_slug, mf.membership_order
                """
            ),
            {"trading_date": trading_date},
        ).mappings()
    except SQLAlchemyError:
        session.rollback()
        return []
    return [dict(row) for row in rows]


def _signal_history_with_authority(
    session: Session,
    *,
    trading_date: date | None,
    topic_rows: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Join existing Home, Topic, and institutional history for evaluation."""

    history = _read_signal_home_history(session, trading_date)
    institution_by_date = _read_signal_institutional_history(session, trading_date)
    topic_by_date: dict[date, list[Mapping[str, Any]]] = defaultdict(list)
    for row in topic_rows:
        row_date = _as_date(row.get("snapshot_date") or row.get("snapshotDate"))
        if row_date is not None:
            topic_by_date[row_date].append(row)
    for item in history:
        item_date = _as_date(item.get("tradingDate"))
        overview = item.get("marketOverview")
        if not isinstance(overview, Mapping):
            continue
        enriched = dict(overview)
        if item_date in institution_by_date and not enriched.get("institutionFlows"):
            enriched["institutionFlows"] = institution_by_date[item_date]
        item["marketOverview"] = enriched
        item["topicObservations"] = topic_by_date.get(item_date, [])
    return history


def _aggregate_fact_input(item: Any) -> dict[str, Any]:
    """Map a typed official aggregate result without losing NULL evidence."""

    if hasattr(item, "to_dict"):
        status = getattr(item, "data_status", "UNAVAILABLE")
        status = getattr(status, "value", status)
        return {
            "market": getattr(item, "market", None),
            "tradingDate": getattr(item, "trading_date", None),
            "turnover": getattr(item, "turnover", None),
            "currency": getattr(item, "currency", None),
            "turnoverUnit": getattr(item, "turnover_unit", None),
            "turnoverScale": getattr(item, "turnover_scale", None),
            "eligible": getattr(item, "eligible", None),
            "observed": getattr(item, "observed", None),
            "advancers": getattr(item, "advancers", None),
            "decliners": getattr(item, "decliners", None),
            "unchanged": getattr(item, "unchanged", None),
            "unavailable": getattr(item, "unavailable", None),
            "limitUpCount": getattr(item, "limit_up_count", None),
            "limitDownCount": getattr(item, "limit_down_count", None),
            "source": getattr(item, "source", None),
            "sourceEndpoint": getattr(item, "source_endpoint", None),
            "lineage": getattr(item, "lineage", None),
            "asOf": getattr(item, "as_of", None),
            "status": status,
            "reasonCode": getattr(item, "status_reason", None),
        }
    raw = dict(item)
    return {
        "market": raw.get("market"),
        "tradingDate": raw.get("trading_date", raw.get("tradingDate")),
        "turnover": raw.get("turnover", raw.get("value")),
        "currency": raw.get("currency", "TWD"),
        "turnoverUnit": raw.get("turnover_unit", raw.get("turnoverUnit", raw.get("unit", "TWD"))),
        "turnoverScale": raw.get("turnover_scale", raw.get("turnoverScale", raw.get("scale", 0))),
        "eligible": raw.get("eligible"),
        "observed": raw.get("observed"),
        "advancers": raw.get("advancers", raw.get("advance")),
        "decliners": raw.get("decliners", raw.get("decline")),
        "unchanged": raw.get("unchanged", raw.get("flat")),
        "unavailable": raw.get("unavailable"),
        "limitUpCount": raw.get("limit_up_count", raw.get("limitUpCount", raw.get("limitUp"))),
        "limitDownCount": raw.get("limit_down_count", raw.get("limitDownCount", raw.get("limitDown"))),
        "source": raw.get("source"),
        "sourceEndpoint": raw.get("source_endpoint", raw.get("sourceEndpoint")),
        "lineage": raw.get("lineage"),
        "asOf": raw.get("as_of", raw.get("asOf")),
        "status": raw.get("status", raw.get("dataStatus", "UNAVAILABLE")),
        "reasonCode": raw.get("reason_code", raw.get("reasonCode", raw.get("statusReason"))),
    }


def materialize_home_v2(
    session: Session,
    *,
    trading_date: date | None = None,
    source_run_id: str | None = None,
    market_index_facts: Sequence[Any] = (),
    turnover_facts: Sequence[MarketTurnoverFact | Mapping[str, Any]] = (),
    market_aggregate_facts: Sequence[Any] = (),
    now: datetime | None = None,
) -> dict[str, Any]:
    """Materialize and persist one deterministic Home envelope."""

    generated_at = (now or datetime.now(UTC)).astimezone(UTC)
    trading_date = trading_date or _latest_canonical_date(session)
    if trading_date is None:
        raise ValueError("HOME_SOURCE_DATE_UNAVAILABLE")
    index_inputs = [_index_fact_input(item) for item in market_index_facts]
    turnover_inputs = [_turnover_payload(item) for item in turnover_facts]
    aggregate_inputs = [_aggregate_fact_input(item) for item in market_aggregate_facts]
    aggregate_by_market = {item.get("market"): item for item in aggregate_inputs}
    breadth_observations: list[dict[str, Any]] = []
    distribution_as_of: datetime | None = None
    if aggregate_inputs:
        breadth_payload = []
        for market in ("TPE", "TWO"):
            fact = aggregate_by_market.get(market) or {}
            available = fact.get("status") == "AVAILABLE"
            breadth_payload.append(
                {
                    "market": market,
                    "eligible": int(fact["eligible"] or 0) if available else 0,
                    "observed": int(fact["observed"] or 0) if available else 0,
                    "advance": int(fact["advancers"]) if available and fact.get("advancers") is not None else None,
                    "decline": int(fact["decliners"]) if available and fact.get("decliners") is not None else None,
                    "flat": int(fact["unchanged"]) if available and fact.get("unchanged") is not None else None,
                    "unavailable": int(fact["unavailable"] or 0) if available else 0,
                    "coverage": {
                        "denominator": "official whole-market stock aggregate",
                        "universeLabel": "TWSE／TPEx 官方全市場股票彙總的正式廣度觀測",
                        "eligible": fact.get("eligible"),
                        "observed": fact.get("observed"),
                        "authority": fact.get("source"),
                        "endpoint": fact.get("sourceEndpoint"),
                        "status": fact.get("status", "UNAVAILABLE"),
                        "reasonCode": fact.get("reasonCode"),
                    },
                    "asOf": fact.get("asOf"),
                    "source": fact.get("source") or "official market aggregate provider",
                }
            )
        breadth_as_of = max(
            (item["asOf"] for item in breadth_payload if item.get("asOf")),
            default=None,
        )
        breadth_rows = []
        try:
            _canonical_rows, distribution_as_of, breadth_observations = _breadth(session, trading_date)
        except SQLAlchemyError:
            session.rollback()
    else:
        breadth_rows, breadth_as_of, breadth_observations = _breadth(session, trading_date)
        distribution_as_of = breadth_as_of
        breadth_payload = [
            {
                "market": row["market"],
                "eligible": int(row["eligible"] or 0),
                "observed": int(row["observed"] or 0),
                "advance": int(row["advance"] or 0),
                "decline": int(row["decline"] or 0),
                "flat": int(row["flat"] or 0),
                "unavailable": int(row["unavailable"] or 0),
                "coverage": {
                    "denominator": "active date-effective EQUITY instruments in TPE/TWO",
                    "universeLabel": (
                        "上市＋上櫃活躍、具日期效力的 EQUITY 之正式日線觀測"
                    ),
                    "eligible": int(row["eligible"] or 0),
                    "observed": int(row["observed"] or 0),
                },
                "asOf": row["as_of"],
                "source": "topicpilot.vw_daily_market_observations",
            }
            for row in breadth_rows
        ]
        for item, row in zip(breadth_payload, breadth_rows, strict=True):
            item["advance"] = int(row["advance"] or 0)
            item["decline"] = int(row["decline"] or 0)
            item["flat"] = int(row["flat"] or 0)
            item["unavailable"] = int(row["unavailable"] or 0)
            item["coverage"]["priceObserved"] = int(row["priced"] or 0)

    unavailable_instruments = build_unavailable_instruments(
        breadth_observations, trade_date=trading_date
    )
    unavailable_by_market: dict[str, list[Any]] = defaultdict(list)
    for unavailable_item in unavailable_instruments:
        unavailable_by_market[unavailable_item.market].append(unavailable_item)
    for item in breadth_payload:
        market = str(item["market"])
        market_unavailable = unavailable_by_market.get(market, [])
        eligible = int(item.get("eligible") or 0)
        priced = int(item.get("coverage", {}).get("priceObserved") or item.get("priced") or 0)
        legitimate = sum(1 for unavailable_item in market_unavailable if unavailable_item.is_legitimate_unavailable)
        pipeline_failure = sum(1 for unavailable_item in market_unavailable if unavailable_item.reason_code in {"MISSING_MARKET_DATA", "PROVIDER_ERROR", "DATE_MISMATCH"} and unavailable_item.blocks_formal_publication)
        unknown = sum(1 for unavailable_item in market_unavailable if unavailable_item.status == "UNKNOWN" and unavailable_item.blocks_formal_publication and unavailable_item.reason_code not in {"MISSING_MARKET_DATA", "PROVIDER_ERROR", "DATE_MISMATCH"})
        item["coverage"].update(
            {
                "eligibleUniverse": eligible,
                "pricedCount": priced,
                "coveredCount": priced + legitimate,
                "unavailableCount": len(market_unavailable),
                "pipelineFailureCount": pipeline_failure,
                "unknownCount": unknown,
                "coveragePct": round(priced / eligible * 100, 4) if eligible else 0,
                "coveredCoveragePct": round((priced + legitimate) / eligible * 100, 4) if eligible else 0,
            }
        )

    read_model_eligible = len(breadth_observations)
    read_model_priced = sum(row.get("close") is not None for row in breadth_observations)
    read_model_covered = read_model_priced + sum(
        item.is_legitimate_unavailable for item in unavailable_instruments
    )
    market_coverage = {
        "denominator": "active date-effective EQUITY instruments in TPE/TWO",
        "eligibleUniverse": read_model_eligible,
        "pricedCount": read_model_priced,
        "coveredCount": read_model_covered,
        "unavailableCount": len(unavailable_instruments),
        "pipelineFailureCount": sum(
            item.reason_code in {"MISSING_MARKET_DATA", "PROVIDER_ERROR", "DATE_MISMATCH"}
            and item.blocks_formal_publication
            for item in unavailable_instruments
        ),
        "unknownCount": sum(
            item.status == "UNKNOWN"
            and item.blocks_formal_publication
            and item.reason_code not in {"MISSING_MARKET_DATA", "PROVIDER_ERROR", "DATE_MISMATCH"}
            for item in unavailable_instruments
        ),
        "coveragePct": round(read_model_priced / read_model_eligible * 100, 4) if read_model_eligible else 0,
        "coveredCoveragePct": round(read_model_covered / read_model_eligible * 100, 4) if read_model_eligible else 0,
        "source": "topicpilot.canonical_daily_market_read_model",
    }

    total_eligible = sum(item["eligible"] for item in breadth_payload)
    total_observed = sum(item["observed"] for item in breadth_payload)
    total_unavailable = sum(item["unavailable"] for item in breadth_payload)
    advance = sum(int(item.get("advance") or 0) for item in breadth_payload)
    decline = sum(int(item.get("decline") or 0) for item in breadth_payload)
    flat = sum(int(item.get("flat") or 0) for item in breadth_payload)
    breadth_eligible = advance + decline + flat

    def _percentage(value: int) -> float | None:
        return round(value / breadth_eligible * 100, 4) if breadth_eligible else None

    distribution_payload = build_market_distribution(
        breadth_observations,
        eligible_count=total_eligible,
        as_of=distribution_as_of,
    )
    market_health = {
        "market": "TPE+TWO",
        "status": "AVAILABLE" if total_observed else "UNAVAILABLE",
        "totalStocks": total_eligible,
        "observed": total_observed,
        "breadthEligible": breadth_eligible,
        "advance": advance,
        "decline": decline,
        "flat": flat,
        "net": advance - decline if breadth_eligible else None,
        "advancePct": _percentage(advance),
        "declinePct": _percentage(decline),
        "flatPct": _percentage(flat),
        "unavailable": total_unavailable,
        "pricedCount": read_model_priced,
        "coveredCount": read_model_covered,
        "coveragePct": market_coverage["coveragePct"],
        "pipelineFailureCount": market_coverage["pipelineFailureCount"],
        "unknownCount": market_coverage["unknownCount"],
    }
    indices = [_market_index_payload(item) for item in index_inputs]
    by_market_index = {item.get("market"): item for item in indices}
    for market, code, name in (
        ("TPE", "TWSE:TAIEX", "TWSE 加權指數"),
        ("TWO", "TPEX:TPEx", "TPEx 櫃買指數"),
    ):
        by_market_index.setdefault(
            market,
            {
                "market": market,
                "indexCode": code,
                "indexName": name,
                "tradingDate": trading_date,
                "session": "CLOSE",
                "value": None,
                "previousClose": None,
                "change": None,
                "changePct": None,
                "asOf": breadth_as_of,
                "source": "official market aggregate provider",
                "lineage": "awaiting typed official market-index fact",
                "status": "UNAVAILABLE",
                "reasonCode": "UPSTREAM_SOURCE_UNAVAILABLE",
            },
        )
    indices = [by_market_index[market] for market in ("TPE", "TWO")]
    if market_coverage["pipelineFailureCount"] or market_coverage["unknownCount"]:
        market_data_status = "UNAVAILABLE"
    elif aggregate_inputs:
        turnover_inputs = [
            {
                "market": item.get("market"),
                "tradingDate": item.get("tradingDate"),
                "session": "CLOSE",
                "value": _number(item.get("turnover")),
                "currency": item.get("currency"),
                "unit": item.get("turnoverUnit"),
                "scale": item.get("turnoverScale"),
                "asOf": item.get("asOf"),
                "source": item.get("source"),
                "lineage": item.get("lineage"),
                "status": item.get("status", "UNAVAILABLE"),
                "reasonCode": item.get("reasonCode"),
            }
            for item in aggregate_inputs
        ]
    turnover = [_turnover_payload(item) for item in turnover_inputs]
    turnover_by_market = {item.get("market"): item for item in turnover}
    for market in ("TPE", "TWO"):
        turnover_by_market.setdefault(
            market,
            {
                "market": market,
                "tradingDate": trading_date,
                "session": "CLOSE",
                "value": None,
                "currency": "TWD",
                "unit": None,
                "scale": None,
                "asOf": breadth_as_of,
                "source": "official market aggregate provider",
                "lineage": "turnover source/units not supplied to Home materializer",
                "status": "UNAVAILABLE",
                "reasonCode": "UPSTREAM_SOURCE_UNAVAILABLE",
            },
        )
    turnover = [turnover_by_market[market] for market in ("TPE", "TWO")]
    total_turnover = _derived_total_turnover(turnover)
    if total_turnover is not None:
        turnover.append(total_turnover)
    turnover = _attach_turnover_comparison(
        turnover, _read_previous_session_turnover(session, trading_date)
    )
    available_indices = [item for item in indices if item.get("status") == "AVAILABLE" and item.get("value") is not None]
    available_turnover = [item for item in turnover if item.get("status") == "AVAILABLE" and item.get("value") is not None]
    if aggregate_inputs:
        market_data_status = (
            "AVAILABLE"
            if all(aggregate_by_market.get(market, {}).get("status") == "AVAILABLE" for market in ("TPE", "TWO"))
            else "PARTIAL"
            if aggregate_inputs and (available_indices or available_turnover or total_observed)
            else "UNAVAILABLE"
        )
    else:
        market_data_status = "AVAILABLE" if total_observed else "UNAVAILABLE"
    aggregate_limits = [item for item in aggregate_inputs if item.get("status") == "AVAILABLE"]
    limit_up_values = [item.get("limitUpCount") for item in aggregate_limits]
    limit_down_values = [item.get("limitDownCount") for item in aggregate_limits]
    limits_complete = len(aggregate_limits) == 2 and all(value is not None for value in limit_up_values + limit_down_values)
    limits_payload = {
        "limitUp": sum(int(value) for value in limit_up_values) if limits_complete else None,
        "limitDown": sum(int(value) for value in limit_down_values) if limits_complete else None,
        "reasonCode": None if limits_complete else "PARTIAL_LIMIT_AUTHORITY" if aggregate_limits else "UPSTREAM_SOURCE_UNAVAILABLE",
        "source": ";".join(sorted({str(item.get("source")) for item in aggregate_inputs if item.get("source")})) or "official market aggregate provider",
    }
    market_overview_payload = {
        "dataDate": trading_date,
        "updatedAt": breadth_as_of,
        "dataStatus": market_data_status,
        "trackedStockCount": sum(int(item.get("eligible") or 0) for item in breadth_payload) if aggregate_inputs else total_eligible,
        "trackedTopicCount": 0,
        "latestSnapshotTime": breadth_as_of,
        "marketHealth": market_health,
        "coverage": market_coverage,
        "unavailableInstruments": [item.to_dict() for item in unavailable_instruments],
        "institutionFlows": None,
        "breadth": breadth_payload,
        "distribution": distribution_payload,
        "indices": indices,
        "turnover": turnover,
        "limits": limits_payload,
        "source": HOME_SOURCE,
    }
    market_status = market_data_status
    market_reason = None if market_status == "AVAILABLE" else "PARTIAL_MARKET_FACTS" if market_status == "PARTIAL" else "NO_PUBLISHED_MARKET_FACTS"
    market_section = _status(
        market_status,
        data_date=trading_date,
        as_of=breadth_as_of,
        source=HOME_SOURCE,
        reason_code=market_reason,
        detail=("official whole-market aggregate facts are available" if aggregate_inputs and market_status == "AVAILABLE" else "official whole-market aggregate facts are partial" if aggregate_inputs else "canonical breadth is available" if total_observed else "no canonical daily breadth rows"),
        payload=market_overview_payload,
    )

    topic_rows = _formal_topic_rows(session, trading_date)
    formal_topic_history = _formal_topic_history(session, trading_date)
    main_topics_payload = rank_formal_topics(topic_rows)
    main_section = _status(
        "AVAILABLE" if main_topics_payload else "UNAVAILABLE",
        data_date=trading_date,
        as_of=max((row["as_of_at"] for row in topic_rows if row.get("as_of_at")), default=None),
        source=MAIN_TOPICS_SOURCE,
        reason_code=None if main_topics_payload else "NO_FORMAL_TOPIC_PUBLICATION",
        detail=f"formal topic universe rows: {len(topic_rows)}; eligible mainline rows: {len(main_topics_payload)}",
        payload=main_topics_payload,
    )
    market_overview_payload["trackedTopicCount"] = len(topic_rows)

    current_institutional_flow = _read_home_institutional_flow(session, trading_date)
    if current_institutional_flow is not None:
        market_overview_payload["institutionFlows"] = current_institutional_flow
    topic_signal_rows = _read_formal_topic_signal_rows(session, trading_date)
    signal_history = _signal_history_with_authority(
        session,
        trading_date=trading_date,
        topic_rows=topic_signal_rows,
    )

    topic_pulse_payload = build_topic_pulse(
        topic_rows,
        formal_topic_history,
        target_date=trading_date,
    )
    topic_pulse_section = _status(
        "AVAILABLE" if topic_pulse_payload else "UNAVAILABLE",
        data_date=trading_date,
        as_of=max((row["as_of_at"] for row in topic_rows if row.get("as_of_at")), default=None),
        source=TOPIC_PULSE_SOURCE,
        reason_code=None if topic_pulse_payload else "NO_FORMAL_TOPIC_PUBLICATION",
        detail=f"all current effective formal Topics returned: {len(topic_pulse_payload)}",
        payload=topic_pulse_payload,
    )
    heating, cooling, rotation_reason = calculate_fast_rotation(
        formal_topic_history,
        target_date=trading_date,
    )
    rotation_as_of = max((row["as_of_at"] for row in formal_topic_history if row.get("as_of_at")), default=None)
    heating_section = _status(
        "AVAILABLE" if heating else "UNAVAILABLE",
        data_date=trading_date,
        as_of=rotation_as_of,
        source=ROTATION_SOURCE,
        reason_code=None if heating else rotation_reason or "INSUFFICIENT_FORMAL_STRENGTH_HISTORY",
        detail=f"formal Topic Strength sessions available: {len({row['snapshot_date'] for row in formal_topic_history})}",
        payload=heating,
    )
    cooling_section = _status(
        "AVAILABLE" if cooling else "UNAVAILABLE",
        data_date=trading_date,
        as_of=rotation_as_of,
        source=ROTATION_SOURCE,
        reason_code=None if cooling else rotation_reason or "INSUFFICIENT_FORMAL_STRENGTH_HISTORY",
        detail=f"formal Topic Strength sessions available: {len({row['snapshot_date'] for row in formal_topic_history})}",
        payload=cooling,
    )
    daily_section = build_daily_focus(
        market_overview=market_overview_payload,
        main_topics=main_topics_payload,
        heating_topics=heating,
        cooling_topics=cooling,
        data_date=trading_date,
        as_of=max((item for item in (breadth_as_of, rotation_as_of) if item), default=None),
        history=signal_history,
        topic_observations=topic_signal_rows,
    )
    events_section = topic_pulse_section
    opportunities_section = _status(
        "UNAVAILABLE",
        data_date=trading_date,
        as_of=None,
        source="HOME_V2_FORMAL_OPPORTUNITY_AUTHORITY",
        reason_code="OPTIONAL_SECTION_NOT_FORMAL",
        detail="temporary opportunity bridge does not participate in the formal gate",
        payload=[],
    )
    sections = {
        "marketOverview": market_section,
        "dailyFocus": daily_section,
        "mainTopics": main_section,
        "heatingTopics": heating_section,
        "coolingTopics": cooling_section,
        "marketEvents": events_section,
        "opportunities": opportunities_section,
    }
    publication_state, gate_reason = validate_home_gate(
        market_overview=market_section,
        main_topics=main_section,
        daily_focus=daily_section,
    )
    section_statuses = {key: sections[key].status_payload() for key in SECTION_KEYS}
    generated_at = generated_at
    published_at = generated_at if publication_state == "PUBLISHED" else None
    publication_input = {
        "tradingDate": trading_date,
        "sourceRunId": source_run_id,
        "marketOverview": market_overview_payload,
        "dailyFocus": daily_section.payload,
        "mainTopics": main_topics_payload,
        "heatingTopics": heating,
        "coolingTopics": cooling,
        "sectionStatuses": section_statuses,
    }
    source_dataset_id = f"home-input:{trading_date.isoformat()}:{_hash(publication_input)}"
    publication_payload = {
        "contractVersion": "v2.home-read-model.v2",
        # Preserve the existing HomeResponse top-level date contract.  The
        # publication envelope and section statuses carry timestamp-level
        # ``asOf`` values for freshness/provenance.
        "asOf": trading_date,
        "generatedAt": generated_at,
        "publication": {
            "tradingDate": trading_date,
            "asOf": max((item for item in (breadth_as_of, rotation_as_of) if item), default=None),
            "generatedAt": generated_at,
            "publishedAt": published_at,
            "state": publication_state,
            "version": HOME_PUBLICATION_VERSION,
            "sourceRunId": source_run_id,
            "sourceDatasetId": source_dataset_id,
            "lineage": {
                "canonicalDailyMarket": "topicpilot.vw_daily_market_observations",
                "formalTopics": "topicpilot.topic_snapshots + formal Topic Strength/Lifecycle results",
            },
            "completeness": {
                "required": ["marketOverview"],
                "sectionAvailableWhenEvidenceExists": ["dailyFocus", "mainTopics", "marketEvents"],
                "optional": ["heatingTopics", "coolingTopics", "opportunities"],
                "sectionStatuses": section_statuses,
            },
        },
        "marketOverview": market_overview_payload,
        "dailyFocus": daily_section.payload,
        "mainTopics": main_topics_payload,
        "marketPulse": topic_pulse_payload,
        "heatingTopics": heating,
        "coolingTopics": cooling,
        "opportunities": [],
        "sectionStatuses": section_statuses,
        "dataQuality": {
            "status": "AVAILABLE" if publication_state == "PUBLISHED" and market_section.status == "AVAILABLE" and all(
                item.status != "UNAVAILABLE" for key, item in sections.items() if key in {"marketOverview"}
            ) else "PARTIAL" if publication_state == "PUBLISHED" else "UNAVAILABLE",
            "source": HOME_SOURCE,
            "classification": "FORMAL",
            "temporarySections": ["opportunities"],
            "missingSections": [key for key, item in sections.items() if item.status == "UNAVAILABLE"],
            "notes": ["題材動態快訊由正式 Topic state comparison 提供；Opportunities 不參與 Today V1 正式發布 gate。"],
            "diagnosticCodes": {
                key: item.reason_code for key, item in sections.items() if item.reason_code
            },
        },
    }
    lineage_hash = _hash(
        {
            "publicationVersion": HOME_PUBLICATION_VERSION,
            "sourceDatasetId": source_dataset_id,
            "sectionStatuses": section_statuses,
        }
    )
    existing = session.scalar(
        text(
            """
            SELECT id FROM topicpilot.home_publications
            WHERE trading_date = :trading_date
              AND source_dataset_id = :source_dataset_id
              AND publication_version = :publication_version
            """
        ),
        {
            "trading_date": trading_date,
            "source_dataset_id": source_dataset_id,
            "publication_version": HOME_PUBLICATION_VERSION,
        },
    )
    if existing is not None:
        return {
            "status": "IDEMPOTENT",
            "publicationId": str(existing),
            "tradingDate": trading_date.isoformat(),
            "publicationState": publication_state,
            "sourceDatasetId": source_dataset_id,
            "sectionStatuses": section_statuses,
        }
    publication = HomePublication(
        trading_date=trading_date,
        as_of_at=max((item for item in (breadth_as_of, rotation_as_of) if item), default=None),
        generated_at=generated_at,
        published_at=published_at,
        publication_state=publication_state,
        publication_version=HOME_PUBLICATION_VERSION,
        source_run_id=source_run_id,
        source_dataset_id=source_dataset_id,
        lineage_hash=lineage_hash,
        completeness=_json_safe(publication_payload["publication"]["completeness"]),
        payload=_json_safe(publication_payload),
        diagnostic_reason=gate_reason,
    )
    session.add(publication)
    session.flush()
    for key in SECTION_KEYS:
        item = sections[key]
        session.add(
            HomePublicationSection(
                publication_id=publication.id,
                section_key=key,
                status=item.status,
                data_date=item.data_date,
                as_of_at=item.as_of,
                source=item.source,
                reason_code=item.reason_code,
                user_message=item.user_message,
                diagnostic_detail=item.diagnostic_detail,
                payload=_json_safe(item.payload) if isinstance(item.payload, Mapping) else {"items": _json_safe(item.payload)},
            )
        )
    for item in indices:
        session.add(
            HomeMarketFact(
                publication_id=publication.id,
                fact_type="INDEX",
                market=item["market"],
                index_code=item["indexCode"],
                index_name=item["indexName"],
                trading_date=trading_date,
                session=item.get("session"),
                value=item.get("value"),
                previous_close=item.get("previousClose"),
                change=item.get("change"),
                change_pct=item.get("changePct"),
                as_of_at=item.get("asOf"),
                source=item.get("source") or "official market aggregate provider",
                lineage=item.get("lineage") or "typed market index input",
                publication_state="PUBLISHED" if item.get("value") is not None else "UNAVAILABLE",
                reason_code=item.get("reasonCode"),
                coverage={
                    "open": _number(item.get("open")),
                    "high": _number(item.get("high")),
                    "low": _number(item.get("low")),
                    "sourceDataset": item.get("sourceDataset"),
                    "sourceEndpoint": item.get("sourceEndpoint"),
                },
            )
        )
    for item in turnover:
        session.add(
            HomeMarketFact(
                publication_id=publication.id,
                fact_type="TURNOVER",
                market=item["market"],
                index_code=None,
                index_name=None,
                trading_date=trading_date,
                session=item.get("session"),
                value=item.get("value"),
                currency=item.get("currency"),
                unit=item.get("unit"),
                scale=item.get("scale"),
                as_of_at=item.get("asOf"),
                source=item.get("source") or "official market aggregate provider",
                lineage=item.get("lineage") or "typed market turnover input",
                publication_state="PUBLISHED" if item.get("value") is not None else "UNAVAILABLE",
                reason_code=item.get("reasonCode"),
            )
        )
    for item in breadth_payload:
        session.add(
            HomeMarketFact(
                publication_id=publication.id,
                fact_type="BREADTH",
                market=item["market"],
                index_code=None,
                index_name=None,
                trading_date=trading_date,
                session="CLOSE",
                as_of_at=item.get("asOf"),
                source=item["source"],
                lineage="active date-effective equity denominator; accepted canonical daily observations",
                publication_state="PUBLISHED" if item["observed"] else "UNAVAILABLE",
                reason_code=None if item["observed"] else "NO_FORMAL_MARKET_BREADTH",
                coverage=item["coverage"],
            )
        )
    session.add(
        HomeMarketFact(
            publication_id=publication.id,
            fact_type="LIMITS",
            market="TPE+TWO",
            index_code=None,
            index_name=None,
            trading_date=trading_date,
            session="CLOSE",
            as_of_at=breadth_as_of,
            source=limits_payload["source"],
            lineage="official whole-market limit-count authority; missing market values remain NULL",
            publication_state="PUBLISHED"
            if limits_payload["limitUp"] is not None or limits_payload["limitDown"] is not None
            else "UNAVAILABLE",
            reason_code=limits_payload["reasonCode"],
            coverage={
                "limitUp": limits_payload["limitUp"],
                "limitDown": limits_payload["limitDown"],
                "markets": [
                    {
                        "market": item.get("market"),
                        "limitUp": item.get("limitUpCount"),
                        "limitDown": item.get("limitDownCount"),
                        "source": item.get("source"),
                        "reasonCode": item.get("reasonCode"),
                    }
                    for item in aggregate_inputs
                ],
            },
        )
    )
    session.commit()
    return {
        "status": "SUCCESS",
        "publicationId": str(publication.id),
        "tradingDate": trading_date.isoformat(),
        "publicationState": publication_state,
        "sourceDatasetId": source_dataset_id,
        "sectionStatuses": section_statuses,
    }


def read_latest_home_publication(session: Session) -> dict[str, Any] | None:
    """Read the latest V2 envelope; no legacy completed-run gate is used."""

    try:
        row = session.execute(
            text(
                """
                SELECT payload
                FROM topicpilot.home_publications
                WHERE publication_state IN ('PUBLISHED', 'UNAVAILABLE')
                ORDER BY trading_date DESC, published_at DESC NULLS LAST, generated_at DESC, id DESC
                LIMIT 1
                """
            )
        ).mappings().one_or_none()
    except SQLAlchemyError:
        return None
    if not row:
        return None
    payload = dict(row["payload"])
    market_overview = payload.get("marketOverview")
    if isinstance(market_overview, Mapping):
        enriched_overview = dict(market_overview)
        trading_date = _as_date(enriched_overview.get("dataDate"))
        if not enriched_overview.get("institutionFlows"):
            flow_payload = _read_home_institutional_flow(session, trading_date)
            if flow_payload is not None:
                enriched_overview["institutionFlows"] = flow_payload
        if not enriched_overview.get("distribution") and trading_date is not None:
            try:
                breadth_rows, breadth_as_of, observations = _breadth(session, trading_date)
                eligible_count = sum(int(item.get("eligible") or 0) for item in breadth_rows)
                enriched_overview["distribution"] = build_market_distribution(
                    observations,
                    eligible_count=eligible_count,
                    as_of=breadth_as_of,
                )
            except SQLAlchemyError:
                session.rollback()
        turnover = enriched_overview.get("turnover")
        if isinstance(turnover, list):
            if not any(
                isinstance(item, Mapping) and item.get("market") == "TOTAL"
                for item in turnover
            ):
                total_turnover = _derived_total_turnover(
                    [item for item in turnover if isinstance(item, Mapping)]
                )
                if total_turnover is not None:
                    turnover = [*turnover, total_turnover]
            enriched_overview["turnover"] = _attach_turnover_comparison(
                [item for item in turnover if isinstance(item, Mapping)],
                _read_previous_session_turnover(session, trading_date),
            )
        payload["marketOverview"] = enriched_overview
        topic_rows = _read_formal_topic_signal_rows(session, trading_date)
        payload_history = _signal_history_with_authority(
            session,
            trading_date=trading_date,
            topic_rows=topic_rows,
        )
        return normalize_home_publication_for_read(
            payload,
            history=payload_history,
            topic_observations=topic_rows,
        )
    return normalize_home_publication_for_read(payload)


def empty_home_v2(now: datetime, *, tracked_stock_count: int = 0) -> dict[str, Any]:
    """Return a typed, product-safe fail-closed envelope before first publish."""

    statuses = {
        key: {
            "status": "UNAVAILABLE",
            "dataDate": None,
            "asOf": None,
            "source": HOME_SOURCE,
            "reasonCode": "NO_PUBLISHED_MARKET_FACTS"
            if key == "marketOverview"
            else "NO_FORMAL_TOPIC_PUBLICATION"
            if key == "mainTopics"
            else "DAILY_FOCUS_EVIDENCE_INCOMPLETE"
            if key == "dailyFocus"
            else "INSUFFICIENT_FORMAL_STRENGTH_HISTORY"
            if key in {"heatingTopics", "coolingTopics"}
            else "OPTIONAL_SECTION_NOT_FORMAL",
            "userMessage": USER_MESSAGES["NO_PUBLISHED_MARKET_FACTS"]
            if key == "marketOverview"
            else USER_MESSAGES["NO_FORMAL_TOPIC_PUBLICATION"]
            if key == "mainTopics"
            else USER_MESSAGES["DAILY_FOCUS_EVIDENCE_INCOMPLETE"]
            if key == "dailyFocus"
            else USER_MESSAGES["INSUFFICIENT_FORMAL_STRENGTH_HISTORY"]
            if key in {"heatingTopics", "coolingTopics"}
            else USER_MESSAGES["OPTIONAL_SECTION_NOT_FORMAL"],
        }
        for key in SECTION_KEYS
    }
    return {
        "contractVersion": "v2.home-read-model.v2",
        "asOf": None,
        "generatedAt": now,
        "publication": {
            "tradingDate": None,
            "asOf": None,
            "generatedAt": now,
            "publishedAt": None,
            "state": "UNAVAILABLE",
            "version": HOME_PUBLICATION_VERSION,
            "sourceRunId": None,
            "sourceDatasetId": None,
            "lineage": {},
            "completeness": {"sectionStatuses": statuses},
        },
        "marketOverview": {
            "dataDate": None,
            "updatedAt": None,
            "dataStatus": "UNAVAILABLE",
            "trackedStockCount": tracked_stock_count,
            "trackedTopicCount": 0,
            "latestSnapshotTime": None,
            "marketHealth": None,
            "institutionFlows": None,
            "breadth": [],
            "distribution": None,
            "indices": [],
            "turnover": [],
            "limits": None,
            "source": HOME_SOURCE,
        },
        "dailyFocus": {
            "mode": "RULE_BASED_V1",
            "temporary": False,
            "headline": "今日市場重點尚未完成",
            "bullets": [],
            "dataDate": None,
            "source": DAILY_FOCUS_SOURCE,
            "reasonCode": "DAILY_FOCUS_EVIDENCE_INCOMPLETE",
            "userMessage": USER_MESSAGES["DAILY_FOCUS_EVIDENCE_INCOMPLETE"],
        },
        "mainTopics": [],
        "marketPulse": [],
        "heatingTopics": [],
        "coolingTopics": [],
        "opportunities": [],
        "sectionStatuses": statuses,
        "dataQuality": {
            "status": "UNAVAILABLE",
            "source": HOME_SOURCE,
            "classification": "FORMAL",
            "temporarySections": ["marketEvents", "opportunities"],
            "missingSections": [key for key in SECTION_KEYS if statuses[key]["status"] == "UNAVAILABLE"],
            "notes": [],
            "diagnosticCodes": {
                key: statuses[key]["reasonCode"] for key in SECTION_KEYS
            },
        },
    }


__all__ = [
    "DAILY_FOCUS_SOURCE",
    "HOME_PUBLICATION_VERSION",
    "MARKET_DISTRIBUTION_BUCKETS",
    "MARKET_DISTRIBUTION_SOURCE",
    "MARKET_SIGNAL_CATALOG",
    "MarketTurnoverFact",
    "build_daily_focus",
    "build_market_distribution",
    "build_market_signals",
    "calculate_fast_rotation",
    "empty_home_v2",
    "materialize_home_v2",
    "normalize_home_publication_for_read",
    "rank_formal_topics",
    "read_latest_home_publication",
    "validate_home_gate",
]

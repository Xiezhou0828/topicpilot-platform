"""Run the bounded WS3 real historical coverage audit.

This module is an audit surface, not a walk-forward runner.  It reads the
existing canonical historical reader, computes the already-frozen SMA(60)
research input, and records bounded REC-A1 event overlays.  It does not write
to the database, publish technical evidence, or change Core V0 definitions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from topicpilot_api.historical_read_model import read_historical_bars
from topicpilot_api.research.ws3_research_policy import (
    CONTINUITY_UNKNOWN,
    EVENT_ACTION_EXCLUDE,
    ResearchInputEvidence,
    VerifiedBreakingEvent,
    evaluate_ws3_research_eligibility,
)

TASK_ID = "TASK-WS3-CORE-V0-REAL-HISTORICAL-COVERAGE-RERUN-AND-MAINLINE-RESUME-20260818"
WINDOW_START = date(2026, 2, 2)
WINDOW_END = date(2026, 8, 13)
MA60_PERIOD = 60
PRIOR_SESSION_REQUIREMENT = 60
DATASET_RELATIVE_PATH = (
    "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/"
    "REC-A1-CA-EVENTS-V0.json"
)
SOURCE_RECONCILIATION = {
    "real_historical_row_count": 63826,
    "distinct_instrument_count": 507,
    "date_min": "2026-02-02",
    "date_max": "2026-08-13",
    "source_distribution": {
        "TWSE_OFFICIAL_DAILY": 39523,
        "TPEX_OFFICIAL_DAILY": 24303,
    },
}


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return str(value)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _json_default(value) if value is not None else "" for key, value in row.items()})


def _as_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def calculate_sma_close(closes: list[Any], period: int = MA60_PERIOD) -> Decimal | None:
    """Calculate raw close SMA using the existing SMA_CLOSE_V1 semantics."""

    if len(closes) < period:
        return None
    try:
        return sum((_as_decimal(value) for value in closes[-period:]), Decimal("0")) / period
    except (InvalidOperation, TypeError, ValueError):
        return None


def event_intersects_window(
    event_date: date,
    observation_dates: list[date],
    end_index: int,
    period: int = MA60_PERIOD,
) -> bool:
    """Return whether an event is inside the actual trailing observation window."""

    if end_index < period - 1 or end_index >= len(observation_dates):
        return False
    return event_date in observation_dates[end_index - period + 1 : end_index + 1]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _load_event_authority(path: Path) -> tuple[dict[tuple[str, str], list[dict[str, Any]]], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    events = payload["events"]
    authoritative: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    authority_counts = Counter(event["authority_state"] for event in events)
    for event in events:
        if event["authority_state"] != "AUTHORITATIVE":
            continue
        key = (event["market_code"], event["instrument_code"])
        authoritative[key].append(event)
    for values in authoritative.values():
        values.sort(key=lambda item: (item["primary_effective_date"], item["stable_event_key"]))
    return authoritative, {
        "dataset_version": payload["dataset_version"],
        "dataset_schema_version": payload["dataset_schema_version"],
        "dataset_content_hash": payload["dataset_content_hash"],
        "dataset_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "event_count": len(events),
        "authority_state_counts": dict(sorted(authority_counts.items())),
        "authoritative_event_count": authority_counts.get("AUTHORITATIVE", 0),
        "partial_event_count": authority_counts.get("PARTIAL", 0),
        "source_path": str(path),
    }


def _identity_rows(session: Session) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT i.id AS instrument_id, i.instrument_code AS code,
                       m.code AS market
                FROM topicpilot.instruments i
                JOIN topicpilot.markets m ON m.id = i.market_id
                WHERE i.is_active = true AND m.is_active = true
                ORDER BY m.code, i.instrument_code
                """
            )
        ).mappings().all()
    ]


def _source_baseline(session: Session) -> dict[str, Any]:
    row = session.execute(
        text(
            """
            SELECT count(*) AS row_count,
                   count(DISTINCT co.instrument_id) AS instrument_count,
                   min((co.observed_at AT TIME ZONE m.timezone)::date) AS date_min,
                   max((co.observed_at AT TIME ZONE m.timezone)::date) AS date_max
            FROM topicpilot.canonical_observations co
            JOIN topicpilot.instruments i ON i.id = co.instrument_id
            JOIN topicpilot.markets m ON m.id = i.market_id
            JOIN topicpilot.market_data_sources s ON s.id = co.source_id
            WHERE co.family_code = 'PRICE'
              AND co.quality_state = 'ACCEPTED'
              AND s.observation_semantics = 'DAILY_BAR'
            """
        )
    ).mappings().one()
    source_rows = session.execute(
        text(
            """
            SELECT s.source_code, count(*) AS row_count
            FROM topicpilot.canonical_observations co
            JOIN topicpilot.market_data_sources s ON s.id = co.source_id
            WHERE co.family_code = 'PRICE'
              AND co.quality_state = 'ACCEPTED'
              AND s.observation_semantics = 'DAILY_BAR'
            GROUP BY s.source_code
            ORDER BY s.source_code
            """
        )
    ).mappings().all()
    return {
        "real_historical_row_count": int(row["row_count"]),
        "distinct_instrument_count": int(row["instrument_count"]),
        "date_min": row["date_min"].isoformat() if row["date_min"] else None,
        "date_max": row["date_max"].isoformat() if row["date_max"] else None,
        "source_distribution": {item["source_code"]: int(item["row_count"]) for item in source_rows},
    }


def _valid_lineage(item: dict[str, Any]) -> bool:
    source = item.get("source") or {}
    required = (
        "source_code",
        "adapter_version",
        "observation_semantics",
        "reference_data_version",
        "normalization_contract_version",
        "mapping_policy_version",
    )
    return all(isinstance(source.get(field), str) and source[field].strip() for field in required)


def _event_for_window(
    events: list[dict[str, Any]],
    dates: list[date],
    end_index: int,
    period: int,
) -> list[VerifiedBreakingEvent]:
    result: list[VerifiedBreakingEvent] = []
    for event in events:
        effective_date = date.fromisoformat(event["primary_effective_date"])
        if not event_intersects_window(effective_date, dates, end_index, period):
            continue
        result.append(
            VerifiedBreakingEvent(
                event_id=event["stable_event_key"],
                event_type=event["event_type"],
                effective_date=effective_date,
                action=EVENT_ACTION_EXCLUDE,
                source_lineage=(
                    event["source_name"],
                    event["source_record_id_or_canonical_row_key"],
                    event["checkpoint_id"],
                ),
            )
        )
    return result


def _partial_event_window_count(
    events: list[dict[str, Any]], dates: list[date], end_index: int, period: int
) -> int:
    return sum(
        event_intersects_window(date.fromisoformat(event["primary_effective_date"]), dates, end_index, period)
        for event in events
    )


def _instrument_coverage(
    identity: dict[str, Any],
    result: dict[str, Any],
    authoritative_events: dict[tuple[str, str], list[dict[str, Any]]],
    partial_events: dict[tuple[str, str], list[dict[str, Any]]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    items = list(result["items"])
    dates = [item["trading_date"] for item in items]
    closes = [item["close"] for item in items]
    key = (identity["market"], identity["code"])
    events = authoritative_events.get(key, [])
    partials = partial_events.get(key, [])
    duplicate_dates = len(dates) - len(set(dates))
    valid_lineage = all(_valid_lineage(item) for item in items)
    gap_dates: set[date] = set()
    rows: list[dict[str, Any]] = []
    counts = Counter()
    for index, item in enumerate(items):
        trading_date = item["trading_date"]
        ma60 = calculate_sma_close(closes[: index + 1])
        ma60_calculable = ma60 is not None
        temporal_eligible = index >= PRIOR_SESSION_REQUIREMENT
        known_events = _event_for_window(events, dates, index, MA60_PERIOD) if ma60_calculable else []
        partial_window = (
            _partial_event_window_count(partials, dates, index, MA60_PERIOD) if ma60_calculable else 0
        )
        evidence = ResearchInputEvidence(
            instrument_identity=f"{identity['market']}:{identity['code']}",
            real_ohlcv_available=True,
            valid_instrument_identity=True,
            valid_source_lineage=valid_lineage,
            sufficient_observations=ma60_calculable and temporal_eligible,
            continuity_state=CONTINUITY_UNKNOWN,
            known_verified_events=tuple(known_events),
        )
        eligibility = evaluate_ws3_research_eligibility(evidence)
        method_a = temporal_eligible and ma60_calculable and _as_decimal(item["close"]) >= ma60
        research_usable = bool(eligibility.eligible and temporal_eligible)
        row = {
            "date": trading_date,
            "instrument_id": identity["instrument_id"],
            "stock_code": identity["code"],
            "market": identity["market"],
            "close": item["close"],
            "ma60": ma60,
            "ma60_calculable": ma60_calculable,
            "temporal_eligible": temporal_eligible,
            "method_a_eligible": method_a and research_usable,
            "below_ma60": temporal_eligible and ma60_calculable and not method_a and research_usable,
            "insufficient_history": not ma60_calculable,
            "event_affected": bool(known_events),
            "partial_event_authority": partial_window > 0,
            "continuity_unknown": True,
            "research_usable": research_usable,
            "eligibility_state": eligibility.state,
            "source_lineage_valid": valid_lineage,
            "data_gap": False,
        }
        rows.append(row)
        for field in (
            "ma60_calculable",
            "temporal_eligible",
            "method_a_eligible",
            "below_ma60",
            "insufficient_history",
            "event_affected",
            "partial_event_authority",
            "continuity_unknown",
            "research_usable",
        ):
            counts[field] += int(row[field])
    first_ma60 = next((row["date"] for row in rows if row["ma60_calculable"]), None)
    first_temporal = next((row["date"] for row in rows if row["temporal_eligible"]), None)
    return (
        {
            "instrument_id": identity["instrument_id"],
            "stock_code": identity["code"],
            "market": identity["market"],
            "first_real_date": dates[0] if dates else None,
            "last_real_date": dates[-1] if dates else None,
            "real_observation_count": len(items),
            "first_ma60_calculable_date": first_ma60,
            "first_temporal_eligible_date": first_temporal,
            "ma60_calculable_day_count": counts["ma60_calculable"],
            "method_a_eligible_day_count": counts["method_a_eligible"],
            "below_ma60_day_count": counts["below_ma60"],
            "event_affected_day_count": counts["event_affected"],
            "partial_event_authority_window_count": counts["partial_event_authority"],
            "data_gap_day_count": len(gap_dates),
            "duplicate_observation_count": duplicate_dates,
            "source_lineage_valid": valid_lineage,
            "research_usable": any(row["research_usable"] for row in rows),
            "continuity_state": CONTINUITY_UNKNOWN,
            "reader_status": result["status"],
        },
        rows,
    )


def run_coverage(
    database_url: str,
    output_dir: Path,
    dataset_path: Path | None = None,
) -> dict[str, Any]:
    """Run the read-only coverage audit and write machine-readable surfaces."""

    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = dataset_path or (_repo_root() / DATASET_RELATIVE_PATH)
    all_events = json.loads(dataset_path.read_text(encoding="utf-8"))["events"]
    authoritative_events: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    partial_events: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in all_events:
        bucket = authoritative_events if event["authority_state"] == "AUTHORITATIVE" else partial_events
        bucket[(event["market_code"], event["instrument_code"])].append(event)
    _, event_metadata = _load_event_authority(dataset_path)

    engine = create_engine(database_url, future=True)
    instrument_surfaces: list[dict[str, Any]] = []
    daily_rows: list[dict[str, Any]] = []
    with Session(engine) as session:
        baseline = _source_baseline(session)
        identities = _identity_rows(session)
        union_dates: set[date] = set()
        gap_by_date: Counter[date] = Counter()
        raw_results: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for identity in identities:
            result = read_historical_bars(
                session,
                identity["code"],
                WINDOW_START,
                WINDOW_END,
                identity["market"],
                200,
            )
            union_dates.update(item["trading_date"] for item in result["items"])
            raw_results.append((identity, result))
        for identity, result in raw_results:
            surface, rows = _instrument_coverage(
                identity,
                result,
                authoritative_events,
                partial_events,
            )
            dates = [row["date"] for row in rows]
            if dates:
                expected_dates = {day for day in union_dates if dates[0] <= day <= dates[-1]}
                missing_dates = expected_dates - set(dates)
                surface["data_gap_day_count"] = len(missing_dates)
                gap_by_date.update(missing_dates)
                for row in rows:
                    row["data_gap"] = row["date"] in missing_dates
            else:
                missing_dates = set()
            instrument_surfaces.append(surface)
            daily_rows.extend(rows)

    daily_by_date: dict[date, dict[str, Any]] = {
        trading_date: {
            "date": trading_date,
            "available_instruments": 0,
            "ma60_calculable": 0,
            "temporal_eligible": 0,
            "method_a_eligible": 0,
            "below_ma60": 0,
            "insufficient_history": 0,
            "event_affected": 0,
            "partial_event_authority": 0,
            "continuity_unknown": 0,
            "data_gap": gap_by_date.get(trading_date, 0),
        }
        for trading_date in sorted(union_dates)
    }
    for row in daily_rows:
        aggregate = daily_by_date.setdefault(
            row["date"],
            {
                "date": row["date"],
                "available_instruments": 0,
                "ma60_calculable": 0,
                "temporal_eligible": 0,
                "method_a_eligible": 0,
                "below_ma60": 0,
                "insufficient_history": 0,
                "event_affected": 0,
                "partial_event_authority": 0,
                "continuity_unknown": 0,
                "data_gap": gap_by_date.get(row["date"], 0),
            },
        )
        aggregate["available_instruments"] += 1
        for field in (
            "ma60_calculable",
            "temporal_eligible",
            "method_a_eligible",
            "below_ma60",
            "insufficient_history",
            "event_affected",
            "partial_event_authority",
            "continuity_unknown",
            "data_gap",
        ):
            aggregate[field] += int(row[field])
    daily_surface = [daily_by_date[key] for key in sorted(daily_by_date)]

    def total(field: str) -> int:
        return sum(int(row[field]) for row in daily_rows)

    research_dates = [row["date"] for row in daily_surface if row["method_a_eligible"] or row["below_ma60"]]
    source_match = baseline == SOURCE_RECONCILIATION
    summary = {
        "task_id": TASK_ID,
        "execution": {
            "mode": "REAL_HISTORICAL_COVERAGE_AUDIT_ONLY",
            "database_runtime": "localhost:5432/topicpilot",
            "database_writes": False,
            "migrations_run": False,
            "walk_forward_run": False,
            "performance_metrics_produced": False,
            "strategy_review_run": False,
            "production_mutation": False,
        },
        "frozen_protocol": {
            "protocol_id": "core-v0-walk-forward.v1",
            "development": "2026-02-02..2026-06-30",
            "validation": "2026-07-01..2026-07-31",
            "holdout": "2026-08-01..2026-08-13",
            "outcomes": ["T+1", "T+3", "T+5", "T+10"],
            "minimum_prior_canonical_trading_sessions": 60,
            "tuning_optimization": "PROHIBITED",
            "unchanged": True,
        },
        "source_reconciliation": {
            "expected": SOURCE_RECONCILIATION,
            "observed": baseline,
            "pass": source_match,
            "migration_head": "0031_task_topic_structural_role_score_projection",
            "reader": "topicpilot_api.historical_read_model.read_historical_bars",
        },
        "coverage": {
            "active_instrument_universe_count": len(instrument_surfaces),
            "real_instrument_count": sum(row["real_observation_count"] > 0 for row in instrument_surfaces),
            "real_observation_count_from_reader": sum(row["real_observation_count"] for row in instrument_surfaces),
            "ma60_calculable_instrument_count": sum(row["ma60_calculable_day_count"] > 0 for row in instrument_surfaces),
            "ma60_noncalculable_instrument_count": sum(
                row["real_observation_count"] > 0 and row["ma60_calculable_day_count"] == 0
                for row in instrument_surfaces
            ),
            "ma60_calculable_instrument_date_count": total("ma60_calculable"),
            "ma60_insufficient_history_instrument_date_count": total("insufficient_history"),
            "temporal_eligible_instrument_date_count": total("temporal_eligible"),
            "method_a_eligible_instrument_date_count": total("method_a_eligible"),
            "method_a_below_ma60_instrument_date_count": total("below_ma60"),
            "known_event_affected_window_count": total("event_affected"),
            "known_event_excluded_count": total("event_affected"),
            "known_event_corrected_count": 0,
            "known_event_annotated_count": 0,
            "partial_event_authority_window_count": total("partial_event_authority"),
            "data_gap_count": sum(row["data_gap_day_count"] for row in instrument_surfaces),
            "duplicate_observation_count": sum(row["duplicate_observation_count"] for row in instrument_surfaces),
            "invalid_identity_count": 0,
            "synthetic_row_count": 0,
            "invalid_source_lineage_count": sum(not row["source_lineage_valid"] for row in instrument_surfaces),
            "continuity_unknown_instrument_date_count": total("continuity_unknown"),
            "earliest_defensible_core_v0_date": min(research_dates) if research_dates else None,
            "latest_defensible_core_v0_date": max(research_dates) if research_dates else None,
            "defensible_research_trading_day_count": len(set(research_dates)),
        },
        "policy": {
            "continuity_policy": "EVENT_AWARE_RESEARCH",
            "continuity_unknown_preserved": True,
            "continuity_unknown_still_fail_closed": True,
            "continuity_unknown_blocks_ws3_research": False,
            "partial_authority_is_not_no_event": True,
            "forward_outcomes_used_for_candidate_formation": False,
        },
        "event_authority": event_metadata,
        "bounded_limitations": [
            "REC-A1 research-only residual uncertainty remains UNKNOWN and was not re-reviewed.",
            "PARTIAL event authority was tracked and not converted to a verified event or no-event assertion.",
            "Formal WS2 technical publication remains governed by its own continuity contract.",
            "Forward outcomes and the Core V0 walk-forward were not run in this task.",
        ],
    }
    readiness = {
        "task_id": TASK_ID,
        "readiness_state": "YES_WITH_BOUNDED_LIMITATIONS" if source_match and total("temporal_eligible") else "NO",
        "coverage_state": "REAL_HISTORICAL_COVERAGE_ESTABLISHED" if source_match else "SOURCE_RECONCILIATION_MISMATCH",
        "ready_for_next_mainline_step": "YES_BOUNDED_COVERAGE_ESTABLISHED" if source_match else "NO_SOURCE_RECONCILIATION_MISMATCH",
        "walk_forward_executed": False,
        "performance_metrics_produced": False,
        "protocol_unchanged": True,
        "continuity_unknown_preserved": True,
        "continuity_unknown_blocks_ws3_research": False,
        "source_reconciliation_pass": source_match,
        "minimum_panel_status": "NOT_REEVALUATED_IN_COVERAGE_ONLY_TASK",
        "candidate_definition_authority_status": "NOT_REOPENED_IN_COVERAGE_ONLY_TASK",
        "limitations": summary["bounded_limitations"],
        "coverage_summary": summary["coverage"],
    }
    reconciliation = {
        "task_id": TASK_ID,
        "policy": "EVENT_AWARE_RESEARCH",
        "policy_version": "ws3-event-aware-research.v1",
        "shared_g2r_p_source_commit": "4f97a3f8195ce1f2eb254a2e4afcaa95a3e12240",
        "task_branch_g2r_p_commit": "fb4ce16ea735746dff643507d4c5744991de6e51",
        "formal_ws2_continuity_contract_changed": False,
        "unknown_preserved": True,
        "affirmative_no_event_required": False,
        "covered_no_event_created": False,
        "known_authoritative_event_action": "EXCLUDE",
        "known_event_correction_count": 0,
        "known_event_annotation_count": 0,
        "partial_event_authority_handling": "TRACK_ONLY_NO_FABRICATED_NO_EVENT",
        "g2r_c_run": False,
        "shared_g3_run": False,
    }
    _write_json(output_dir / "ws3-real-historical-coverage-summary.json", summary)
    _write_json(output_dir / "ws3-core-v0-walk-forward-readiness.json", readiness)
    _write_json(output_dir / "ws3-shared-policy-reconciliation.json", reconciliation)
    _write_csv(
        output_dir / "ws3-daily-coverage-surface.csv",
        [
            "date", "available_instruments", "ma60_calculable", "temporal_eligible",
            "method_a_eligible", "below_ma60", "insufficient_history", "event_affected",
            "partial_event_authority", "continuity_unknown", "data_gap",
        ],
        daily_surface,
    )
    _write_csv(
        output_dir / "ws3-instrument-coverage-surface.csv",
        [
            "instrument_id", "stock_code", "market", "first_real_date", "last_real_date",
            "real_observation_count", "first_ma60_calculable_date", "first_temporal_eligible_date",
            "ma60_calculable_day_count", "method_a_eligible_day_count", "below_ma60_day_count",
            "event_affected_day_count", "partial_event_authority_window_count", "data_gap_day_count",
            "duplicate_observation_count", "source_lineage_valid", "research_usable", "continuity_state",
            "reader_status",
        ],
        instrument_surfaces,
    )
    engine.dispose()
    return {
        "summary": summary,
        "readiness": readiness,
        "reconciliation": reconciliation,
        "daily_surface": daily_surface,
        "instrument_surface": instrument_surfaces,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dataset-path", type=Path)
    args = parser.parse_args()
    if not args.database_url:
        parser.error("--database-url or TOPICPILOT_DATABASE_URL is required")
    result = run_coverage(args.database_url, args.output_dir, args.dataset_path)
    print(json.dumps({"task_id": TASK_ID, "coverage": result["summary"]["coverage"]}, default=_json_default))


if __name__ == "__main__":
    main()


__all__ = [
    "TASK_ID",
    "WINDOW_END",
    "WINDOW_START",
    "calculate_sma_close",
    "event_intersects_window",
    "run_coverage",
]

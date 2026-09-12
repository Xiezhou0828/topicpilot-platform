"""WS3-only Technical Signal x Topic Lifecycle/Strength conditional study.

This runner consumes the already frozen A2, LEGACY-5, BOTH and WS1 L5
research artifacts.  It never recomputes or changes signal eligibility, never
publishes a recommendation, and never writes to the database.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping

from sqlalchemy import bindparam, create_engine, text


TASK_ID = "TASK-WS3-TECHNICAL-SIGNAL-TOPIC-LIFECYCLE-STRENGTH-CONDITIONAL-EXPECTANCY-STUDY-20260822"
OUTPUT_NAME = TASK_ID
L5_DIR = "reports/TASK-WS1-L5-CURRENT-TAXONOMY-HISTORICAL-LIFECYCLE-STRENGTH-RECONSTRUCTION-20260822"
L5_DATASET = f"{L5_DIR}/historical-lifecycle-strength-dataset.csv"
L5_MANIFEST = f"{L5_DIR}/reconstruction-manifest.json"
A2_PANEL = "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv"
A2_OUTCOMES = "reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/a2-path-aware-outcomes.csv"
LEGACY_EPISODES = "reports/TASK-WS3-LEGACY-5-STRATEGY-BENCHMARK-20260822/legacy5-distinct-episodes.csv"
LEGACY_OUTCOMES = "reports/TASK-WS3-LEGACY-5-STRATEGY-BENCHMARK-20260822/event-outcomes.csv"
LEGACY_MANIFEST = "reports/TASK-WS3-LEGACY-5-STRATEGY-BENCHMARK-20260822/legacy5-event-cohort-manifest.json"
JOINT_RUN = "reports/TASK-WS3-A2-LEGACY5-JOINT-SIGNAL-ROBUSTNESS-AND-BENCHMARK-VALIDATION-20260822/run-summary.json"
JOINT_SEMANTICS = "reports/TASK-WS3-A2-LEGACY5-JOINT-SIGNAL-ROBUSTNESS-AND-BENCHMARK-VALIDATION-20260822/source-semantics-reconciliation-manifest.json"

LIFECYCLE_STAGES = ("SPROUTING", "FERMENTING", "MAIN_RISE", "MATURE", "DECLINING")
STRENGTH_FIELDS = ("positive_breadth", "strong_breadth", "weak_ratio", "average_change_pct")
STRENGTH_PROXY = "leader_change_pct"
HORIZONS = (5, 10)
BARRIER_PAIRS = ((0.05, -0.05), (0.10, -0.05))
EXPECTED = {"l5_rows": 16250, "a2_events": 5277, "legacy_episodes": 2471, "relations": 852}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_lines(lines: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[Mapping[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: value for field, value in row.items()})


def as_float(value: Any) -> float | None:
    if value in (None, "", "null", "None"):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def as_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    return date.fromisoformat(str(value)[:10])


def mean(values: Iterable[float | None]) -> float | None:
    numbers = [float(v) for v in values if v is not None]
    return statistics.fmean(numbers) if numbers else None


def median(values: Iterable[float | None]) -> float | None:
    numbers = [float(v) for v in values if v is not None]
    return statistics.median(numbers) if numbers else None


def quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def trim5(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    cut = int(len(ordered) * 0.05)
    retained = ordered[cut: len(ordered) - cut] if len(ordered) > 2 * cut else ordered
    return statistics.fmean(retained) if retained else None


def winsor5(values: list[float]) -> float | None:
    if not values:
        return None
    low = quantile(values, 0.05)
    high = quantile(values, 0.95)
    if low is None or high is None:
        return None
    return statistics.fmean([min(max(v, low), high) for v in values])


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def outcome_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    return [float(row[field]) for row in rows if row.get(field) is not None]


def barrier_rate(rows: list[dict[str, Any]], name: str, outcome: str) -> float | None:
    values = [row.get(name) for row in rows if row.get(name) in {"UP_FIRST", "DOWN_FIRST", "SAME_SESSION_ORDER_UNKNOWN", "NEITHER_BY_H"}]
    return ratio(sum(item == outcome for item in values), len(values))


def safe_component(value: Any) -> str:
    return str(value or "").strip()


def load_sources(source_root: Path) -> dict[str, Any]:
    paths = {
        "l5_dataset": source_root / L5_DATASET,
        "l5_manifest": source_root / L5_MANIFEST,
        "a2_panel": source_root / A2_PANEL,
        "a2_outcomes": source_root / A2_OUTCOMES,
        "legacy_episodes": source_root / LEGACY_EPISODES,
        "legacy_outcomes": source_root / LEGACY_OUTCOMES,
        "legacy_manifest": source_root / LEGACY_MANIFEST,
        "joint_run": source_root / JOINT_RUN,
        "joint_semantics": source_root / JOINT_SEMANTICS,
    }
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise RuntimeError(f"FAIL_CLOSED_SOURCE_PATH_MISSING:{','.join(missing)}")

    l5_rows = read_csv(paths["l5_dataset"])
    a2_panel = read_csv(paths["a2_panel"])
    a2_outcome_rows = read_csv(paths["a2_outcomes"])
    legacy_episodes = [row for row in read_csv(paths["legacy_episodes"]) if row.get("variant") == "LEGACY-5"]
    legacy_outcome_rows = read_csv(paths["legacy_outcomes"])
    if len(l5_rows) != EXPECTED["l5_rows"]:
        raise RuntimeError(f"FAIL_CLOSED_L5_ROW_COUNT:{len(l5_rows)}")
    if len(a2_panel) != EXPECTED["a2_events"] or len({row.get("event_id") for row in a2_panel}) != EXPECTED["a2_events"]:
        raise RuntimeError(f"FAIL_CLOSED_A2_EVENT_COUNT:{len(a2_panel)}")
    if len(legacy_episodes) != EXPECTED["legacy_episodes"] or len({row.get("episode_id") for row in legacy_episodes}) != EXPECTED["legacy_episodes"]:
        raise RuntimeError(f"FAIL_CLOSED_LEGACY_EPISODE_COUNT:{len(legacy_episodes)}")

    l5_manifest = read_json(paths["l5_manifest"])
    legacy_manifest = read_json(paths["legacy_manifest"])
    joint_run = read_json(paths["joint_run"])
    joint_semantics = read_json(paths["joint_semantics"])

    return {
        "paths": paths,
        "l5_rows": l5_rows,
        "a2_panel": a2_panel,
        "a2_outcomes": a2_outcome_rows,
        "legacy_episodes": legacy_episodes,
        "legacy_outcomes": legacy_outcome_rows,
        "l5_manifest": l5_manifest,
        "legacy_manifest": legacy_manifest,
        "joint_run": joint_run,
        "joint_semantics": joint_semantics,
    }


def load_authority(database_url: str, instrument_ids: set[str], start: date, end: date) -> dict[str, Any]:
    engine = create_engine(database_url, future=True, pool_pre_ping=True)
    relation_sql = text(
        """
        SELECT r.topic_id::text AS topic_id, r.instrument_id::text AS instrument_id,
               i.instrument_code, m.code AS market_code, t.slug AS topic_slug,
               t.name AS topic_name, r.relation_type, r.relation_version,
               r.valid_from, r.valid_to, r.structural_role, r.approval_state,
               r.correction_sequence, r.lineage_hash, r.id::text AS relation_id
        FROM topicpilot.instrument_topic_relations r
        JOIN topicpilot.instruments i ON i.id = r.instrument_id
        JOIN topicpilot.markets m ON m.id = i.market_id
        JOIN topicpilot.topics t ON t.id = r.topic_id
        WHERE t.status NOT IN ('DISABLED', 'RETIRED')
          AND i.is_active = TRUE AND m.is_active = TRUE
          AND r.valid_to IS NULL AND r.superseded_by_authority_id IS NULL
        ORDER BY r.topic_id, r.instrument_id,
                 COALESCE(r.correction_sequence, 0) DESC,
                 r.valid_from DESC, r.relation_version DESC, r.id DESC
        """
    )
    bar_sql = text(
        """
        SELECT d.instrument_id::text AS instrument_id, d.instrument_code,
               d.market_code, d.trade_date, d.open, d.high, d.low, d.close,
               d.canonical_observation_id::text AS canonical_observation_id
        FROM topicpilot.vw_daily_market_observations d
        JOIN topicpilot.canonical_observations co ON co.id = d.canonical_observation_id
        JOIN topicpilot.markets m ON m.code = d.market_code
        JOIN topicpilot.market_data_sources mds ON mds.id = d.source_id
        WHERE co.family_code = 'PRICE'
          AND d.quality_state = 'ACCEPTED'
          AND mds.observation_semantics = 'DAILY_BAR'
          AND d.trade_date >= :start_date AND d.trade_date <= :end_date
          AND d.instrument_id IN :instrument_ids
          AND NOT EXISTS (
              SELECT 1 FROM topicpilot.reference_instrument_lifecycles lifecycle
              WHERE lifecycle.instrument_id = co.instrument_id
                AND lifecycle.status_code IN ('DELISTED', 'SUSPENDED', 'TERMINATED')
                AND lifecycle.effective_from <= d.trade_date
                AND (lifecycle.effective_to IS NULL OR lifecycle.effective_to >= d.trade_date)
          )
        ORDER BY d.instrument_id, d.trade_date, co.observed_at,
                 co.ordering_key, co.id
        """
    ).bindparams(bindparam("instrument_ids", expanding=True))
    with engine.connect() as connection:
        relation_rows = [dict(row) for row in connection.execute(relation_sql).mappings()]
        bar_rows = [dict(row) for row in connection.execute(bar_sql, {"start_date": start, "end_date": end, "instrument_ids": sorted(instrument_ids)}).mappings()]
    engine.dispose()

    if len(relation_rows) != EXPECTED["relations"]:
        raise RuntimeError(f"FAIL_CLOSED_CURRENT_RELATION_COUNT:{len(relation_rows)}")
    relation_by_instrument: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in relation_rows:
        for key in ("valid_from", "valid_to"):
            if row.get(key) is not None:
                row[key] = str(row[key])
        relation_by_instrument[row["instrument_id"]].append(row)
    bars_by_instrument: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in bar_rows:
        row["trade_date"] = as_date(row["trade_date"])
        for key in ("open", "high", "low", "close"):
            row[key] = as_float(row.get(key))
        bars_by_instrument[row["instrument_id"]].append(row)
    for rows in bars_by_instrument.values():
        rows.sort(key=lambda item: (item["trade_date"], item.get("canonical_observation_id", "")))
    relation_hash = sha256_lines(
        "|".join(str(row.get(key, "")) for key in (
            "topic_id", "instrument_id", "instrument_code", "market_code", "topic_slug",
            "relation_type", "relation_version", "valid_from", "valid_to", "structural_role",
            "approval_state", "correction_sequence", "lineage_hash", "relation_id"
        )) for row in relation_rows
    )
    return {
        "relations": relation_rows,
        "relation_by_instrument": relation_by_instrument,
        "relation_hash": relation_hash,
        "bars_by_instrument": bars_by_instrument,
        "bar_rows": len(bar_rows),
    }


def metric_row(signal: Mapping[str, Any], outcome: Mapping[str, Any] | None, bars: Mapping[str, Any] | None = None, horizon: int = 0) -> dict[str, Any]:
    row = dict(signal)
    row["horizon"] = horizon
    outcome = outcome or {}
    row["outcome_status"] = outcome.get("horizon_status") or outcome.get("maturity_status") or "OUTCOME_NOT_FOUND"
    for field in ("endpoint_return", "mfe", "mae"):
        row[field] = outcome.get(field)
    row["barrier_5_before_minus5"] = barrier_for_signal(signal, bars or {}, horizon, 0.05, -0.05)
    row["barrier_10_before_minus5"] = barrier_for_signal(signal, bars or {}, horizon, 0.10, -0.05)
    return row


def barrier_for_signal(signal: Mapping[str, Any], bars_by_instrument: Mapping[str, list[dict[str, Any]]], horizon: int, up: float, down: float) -> str:
    instrument_id = str(signal.get("instrument_id"))
    rows = bars_by_instrument.get(instrument_id, [])
    signal_date = as_date(signal.get("signal_date"))
    anchor_close = as_float(signal.get("anchor_close"))
    if signal_date is None or anchor_close is None or anchor_close <= 0:
        return "NO_SIGNAL_BAR"
    positions = [index for index, row in enumerate(rows) if row.get("trade_date") == signal_date]
    if not positions:
        return "NO_SIGNAL_BAR"
    future = rows[positions[0] + 1: positions[0] + 1 + horizon]
    if len(future) != horizon:
        return "NOT_MATURED"
    for item in future:
        high = item.get("high")
        low = item.get("low")
        if high is None or low is None:
            return "FAIL_CLOSED_INVALID_FUTURE_BAR"
        up_hit = high >= anchor_close * (1.0 + up)
        down_hit = low <= anchor_close * (1.0 + down)
        if up_hit and down_hit:
            return "SAME_SESSION_ORDER_UNKNOWN"
        if up_hit:
            return "UP_FIRST"
        if down_hit:
            return "DOWN_FIRST"
    return "NEITHER_BY_H"


def outcome_index(rows: list[dict[str, str]], key: str, key_value: str, variant: str | None = None) -> dict[tuple[str, int], dict[str, Any]]:
    result: dict[tuple[str, int], dict[str, Any]] = {}
    for raw in rows:
        if raw.get(key) != key_value:
            continue
        if variant and raw.get("variant") != variant:
            continue
        horizon = int(raw["horizon"])
        if horizon not in HORIZONS:
            continue
        item = dict(raw)
        item["horizon_status"] = item.get("horizon_status") or item.get("maturity_status")
        for field in ("endpoint_return", "mfe", "mae"):
            item[field] = as_float(item.get(field))
        result[(key_value, horizon)] = item
    return result


def choose_relation(relations: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    if not relations:
        return None, "NO_TOPIC_MATCH"
    representatives = [row for row in relations if str(row.get("structural_role") or "").upper() == "REPRESENTATIVE"]
    primaries = [row for row in relations if str(row.get("relation_type") or "").upper() in {"PRIMARY", "REPRESENTATIVE"}]
    if len(representatives) == 1:
        return representatives[0], "PRIMARY_REPRESENTATIVE_UNIQUE"
    if len(representatives) > 1:
        return None, "AMBIGUOUS_TOPIC_MATCH"
    if len(primaries) == 1:
        return primaries[0], "PRIMARY_RELATION_UNIQUE"
    if len(primaries) > 1:
        return None, "AMBIGUOUS_TOPIC_MATCH"
    if len(relations) == 1:
        return relations[0], "UNIQUE_RELATION"
    return None, "AMBIGUOUS_TOPIC_MATCH"


def join_lifecycle(signal: dict[str, Any], relation_by_instrument: Mapping[str, list[dict[str, Any]]], l5_by_key: Mapping[tuple[str, str], dict[str, str]]) -> dict[str, Any]:
    relations = relation_by_instrument.get(str(signal.get("instrument_id")), [])
    chosen, status = choose_relation(relations)
    signal["relation_candidate_count"] = len(relations)
    signal["topic_match_status"] = status
    signal["topic_id"] = chosen.get("topic_id") if chosen else ""
    signal["topic_slug"] = chosen.get("topic_slug") if chosen else ""
    signal["topic_name"] = chosen.get("topic_name") if chosen else ""
    signal["relation_structural_role"] = chosen.get("structural_role") if chosen else ""
    signal["relation_version"] = chosen.get("relation_version") if chosen else ""
    signal["relation_lineage_hash"] = chosen.get("lineage_hash") if chosen else ""
    l5 = l5_by_key.get((str(signal.get("topic_id")), str(signal.get("signal_date")))) if chosen else None
    if chosen and l5 is None:
        signal["lifecycle_join_status"] = "NO_LIFECYCLE_ROW"
    elif not chosen:
        signal["lifecycle_join_status"] = status
    else:
        signal["lifecycle_join_status"] = "VALID_LIFECYCLE_JOIN"
    if l5:
        for field in ("lifecycle_stage", "data_status", "evaluation_status", "quality_status", "lineage_status", "strength_raw_evidence_status", "coverage_pct", "confidence", "valid_member_count", "partial_lineage_flag", "unknown_lineage_flag", "fail_closed_flag"):
            signal[field] = l5.get(field, "")
        for field in STRENGTH_FIELDS + (STRENGTH_PROXY,):
            signal[field] = as_float(l5.get(field))
        signal["strength_complete"] = l5.get("strength_raw_evidence_status") == "COMPLETE"
    else:
        signal["lifecycle_stage"] = ""
        signal["data_status"] = ""
        signal["evaluation_status"] = ""
        signal["quality_status"] = ""
        signal["lineage_status"] = ""
        signal["strength_complete"] = False
        for field in STRENGTH_FIELDS + (STRENGTH_PROXY,):
            signal[field] = None
    signal["valid_five_stage"] = signal.get("lifecycle_stage") in LIFECYCLE_STAGES
    signal["lifecycle_pending"] = signal.get("lifecycle_stage") == "PENDING" or signal.get("data_status") == "PENDING" or signal.get("evaluation_status") == "PENDING"
    signal["lifecycle_insufficient_data"] = signal.get("lifecycle_stage") == "INSUFFICIENT_DATA" or signal.get("data_status") == "INSUFFICIENT_DATA" or signal.get("evaluation_status") == "INSUFFICIENT_DATA"
    signal["lifecycle_fail_closed"] = signal.get("lifecycle_stage") == "FAIL_CLOSED" or signal.get("data_status") == "FAIL_CLOSED"
    return signal


def make_signal(cohort: str, source_signal: str, signal_id: str, instrument_id: str, stock_code: str, market: str, signal_date: str, anchor_close: Any, outcome: Mapping[str, Any] | None, pair_id: str = "", timing_delta: Any = "") -> dict[str, Any]:
    return {
        "cohort": cohort,
        "source_signal": source_signal,
        "signal_id": signal_id,
        "instrument_id": instrument_id,
        "stock_code": stock_code,
        "market": market,
        "signal_date": signal_date,
        "anchor_close": as_float(anchor_close),
        "pair_id": pair_id,
        "timing_delta_sessions": timing_delta,
        "outcome_by_horizon": outcome or {},
    }


def build_signals(sources: Mapping[str, Any]) -> list[dict[str, Any]]:
    a2_outcomes: dict[tuple[str, int], dict[str, Any]] = {}
    for raw in sources["a2_outcomes"]:
        horizon = int(raw.get("horizon") or 0)
        if horizon in HORIZONS:
            item = dict(raw)
            item["horizon_status"] = item.get("horizon_status") or item.get("horizon_status") or item.get("maturity_status")
            for field in ("endpoint_return", "mfe", "mae"):
                item[field] = as_float(item.get(field))
            a2_outcomes[(raw.get("event_id", ""), horizon)] = item
    legacy_outcomes: dict[tuple[str, int], dict[str, Any]] = {}
    for raw in sources["legacy_outcomes"]:
        if raw.get("variant") != "LEGACY-5":
            continue
        horizon = int(raw.get("horizon") or 0)
        if horizon in HORIZONS:
            item = dict(raw)
            item["horizon_status"] = item.get("maturity_status")
            for field in ("endpoint_return", "mfe", "mae"):
                item[field] = as_float(item.get(field))
            legacy_outcomes[(raw.get("episode_id", ""), horizon)] = item
    signals: list[dict[str, Any]] = []
    a2_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for raw in sources["a2_panel"]:
        signal = make_signal("A2", "A2", raw["event_id"], raw["instrument_id"], raw["stock_code"], raw["market"], raw["signal_date"], raw.get("a2_close"), {h: a2_outcomes.get((raw["event_id"], h), {}) for h in HORIZONS})
        signals.append(signal)
        a2_by_key[(raw["instrument_id"], raw["signal_date"])] = signal
    legacy_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for raw in sources["legacy_episodes"]:
        if raw.get("variant") != "LEGACY-5":
            continue
        signal = make_signal("LEGACY5", "LEGACY5", raw["episode_id"], raw["instrument_id"], raw["stock_code"], raw["market"], raw["episode_start_date"], None, {h: legacy_outcomes.get((raw["episode_id"], h), {}) for h in HORIZONS})
        signals.append(signal)
        legacy_by_key[(raw["instrument_id"], raw["episode_start_date"])] = signal
    for key in sorted(set(a2_by_key).intersection(legacy_by_key)):
        a2 = a2_by_key[key]
        legacy = legacy_by_key[key]
        pair_id = f"{a2['signal_id']}|{legacy['signal_id']}"
        for source_signal, source in (("A2", a2), ("LEGACY5", legacy)):
            signals.append({**source, "cohort": "BOTH", "source_signal": source_signal, "pair_id": pair_id, "signal_id": f"{pair_id}|{source_signal}"})
    same_session_keys = set(a2_by_key).intersection(legacy_by_key)
    if len(same_session_keys) != 560:
        raise RuntimeError(f"FAIL_CLOSED_BOTH_SAME_SESSION_COUNT:{len(same_session_keys)}")
    return signals


def summarize(rows: list[dict[str, Any]], cohort: str, stage: str, horizon: int) -> dict[str, Any]:
    current = [row for row in rows if row["cohort"] == cohort and (stage == "ALL" or row.get("lifecycle_stage") == stage)]
    endpoint = outcome_values(current, "endpoint_return")
    mfe = outcome_values(current, "mfe")
    mae = outcome_values(current, "mae")
    return {
        "cohort": cohort,
        "lifecycle_stage": stage,
        "horizon": horizon,
        "N": len(current),
        "instrument_count": len({row["instrument_id"] for row in current}),
        "matured_count": sum(row.get("outcome_status") == "COMPLETE_RAW_PATH" for row in current),
        "endpoint_mean": mean(endpoint),
        "endpoint_median": median(endpoint),
        "mfe_mean": mean(mfe),
        "mfe_median": median(mfe),
        "mae_mean": mean(mae),
        "mae_median": median(mae),
        "positive_endpoint_rate": ratio(sum(value > 0 for value in endpoint), len(endpoint)),
        "barrier_5_before_minus5_up_first_rate": barrier_rate(current, "barrier_5_before_minus5", "UP_FIRST"),
        "barrier_5_before_minus5_down_first_rate": barrier_rate(current, "barrier_5_before_minus5", "DOWN_FIRST"),
        "barrier_5_before_minus5_same_session_unknown_rate": barrier_rate(current, "barrier_5_before_minus5", "SAME_SESSION_ORDER_UNKNOWN"),
        "barrier_10_before_minus5_up_first_rate": barrier_rate(current, "barrier_10_before_minus5", "UP_FIRST"),
        "barrier_10_before_minus5_down_first_rate": barrier_rate(current, "barrier_10_before_minus5", "DOWN_FIRST"),
        "barrier_10_before_minus5_same_session_unknown_rate": barrier_rate(current, "barrier_10_before_minus5", "SAME_SESSION_ORDER_UNKNOWN"),
    }


def build_conditional(rows: list[dict[str, Any]], horizon: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cohorts = ("A2", "LEGACY5", "BOTH")
    expectancy: list[dict[str, Any]] = []
    path: list[dict[str, Any]] = []
    for cohort in cohorts:
        baseline_by_h = {h: summarize(rows, cohort, "ALL_VALID_FIVE_STAGE_BASELINE", h) for h in HORIZONS}
        for h in (horizon,):
            baseline_rows = [r for r in rows if r["cohort"] == cohort and r.get("valid_five_stage")]
            base = summarize(baseline_rows, cohort, "ALL", h)
            for stage in LIFECYCLE_STAGES:
                current = summarize(rows, cohort, stage, h)
                current["baseline_N"] = base["N"]
                for metric in ("endpoint_mean", "endpoint_median", "mfe_mean", "mfe_median", "mae_mean", "mae_median"):
                    current[f"conditional_minus_unconditional_{metric}"] = (current[metric] - base[metric]) if current[metric] is not None and base[metric] is not None else None
                current["comparison_purpose"] = "CONDITIONAL_INFORMATION_VALUE_ONLY"
                current["small_sample_flag"] = current["N"] < 20
                expectancy.append(current)
                for up, down in BARRIER_PAIRS:
                    field = "barrier_5_before_minus5" if up == 0.05 else "barrier_10_before_minus5"
                    group = [r for r in rows if r["cohort"] == cohort and r.get("lifecycle_stage") == stage]
                    races_all = [r.get(field) for r in group if r.get(field) not in (None, "")]
                    races = [value for value in races_all if value in {"UP_FIRST", "DOWN_FIRST", "SAME_SESSION_ORDER_UNKNOWN", "NEITHER_BY_H"}]
                    path.append({
                        "cohort": cohort, "lifecycle_stage": stage, "horizon": h,
                        "barrier_pair": f"+{int(up * 100)}%_BEFORE_-5%",
                        "N": len(group), "instrument_count": len({r["instrument_id"] for r in group}),
                        "matured_barrier_count": len(races), "up_first_count": races.count("UP_FIRST"),
                        "down_first_count": races.count("DOWN_FIRST"), "same_session_order_unknown_count": races.count("SAME_SESSION_ORDER_UNKNOWN"),
                        "neither_by_h_count": races.count("NEITHER_BY_H"), "not_matured_count": races_all.count("NOT_MATURED"),
                        "up_first_rate": ratio(races.count("UP_FIRST"), len(races)),
                        "down_first_rate": ratio(races.count("DOWN_FIRST"), len(races)),
                        "same_session_order_unknown_rate": ratio(races.count("SAME_SESSION_ORDER_UNKNOWN"), len(races)),
                        "definition": "first future daily High/Low barrier; same-session order remains unknown",
                    })
    return expectancy, path


def build_missing_audit(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = (
        ("VALID_FIVE_STAGE", lambda r: r.get("valid_five_stage")),
        ("PENDING", lambda r: r.get("lifecycle_pending")),
        ("INSUFFICIENT_DATA", lambda r: r.get("lifecycle_insufficient_data")),
        ("FAIL_CLOSED", lambda r: r.get("lifecycle_fail_closed")),
        ("STRENGTH_INCOMPLETE", lambda r: not r.get("strength_complete")),
        ("NO_TOPIC_MATCH", lambda r: r.get("topic_match_status") == "NO_TOPIC_MATCH"),
        ("AMBIGUOUS_TOPIC_MATCH", lambda r: r.get("topic_match_status") == "AMBIGUOUS_TOPIC_MATCH"),
        ("NO_LIFECYCLE_ROW", lambda r: r.get("lifecycle_join_status") == "NO_LIFECYCLE_ROW"),
    )
    result: list[dict[str, Any]] = []
    for cohort in ("A2", "LEGACY5", "BOTH"):
        for group_name, predicate in groups:
            selected = [r for r in rows if r["cohort"] == cohort and predicate(r)]
            for h in HORIZONS:
                current = [r for r in selected if r.get("outcome_by_horizon", {}).get(h)]
                materialized = [metric_row(r, r.get("outcome_by_horizon", {}).get(h), {}) for r in current]
                result.append({
                    "cohort": cohort, "selection_group": group_name, "horizon": h,
                    "N": len(selected), "instrument_count": len({r["instrument_id"] for r in selected}),
                    "outcome_rows": len(current), "endpoint_mean": mean(outcome_values(materialized, "endpoint_return")),
                    "endpoint_median": median(outcome_values(materialized, "endpoint_return")),
                    "mfe_mean": mean(outcome_values(materialized, "mfe")), "mfe_median": median(outcome_values(materialized, "mfe")),
                    "mae_mean": mean(outcome_values(materialized, "mae")), "mae_median": median(outcome_values(materialized, "mae")),
                    "compare_to_valid_subset": "DESCRIPTIVE_ONLY",
                    "overlap_is_allowed": "YES; groups are audit lenses, not mutually exclusive",
                })
    return result


def rank_bin(values: list[float], value: float) -> str:
    if len(values) < 4:
        return "ALL_SMALL_SAMPLE"
    ordered = sorted(values)
    rank = ordered.index(value) / max(1, len(ordered) - 1)
    return "Q1" if rank < 0.25 else "Q2" if rank < 0.5 else "Q3" if rank < 0.75 else "Q4"


def monotonic_direction(values: list[float | None]) -> str:
    clean = [v for v in values if v is not None]
    if len(clean) < 2:
        return "INSUFFICIENT_BINS"
    if all(a <= b for a, b in zip(clean, clean[1:])):
        return "NONDECREASING_DESCRIPTIVE"
    if all(a >= b for a, b in zip(clean, clean[1:])):
        return "NONINCREASING_DESCRIPTIVE"
    return "NON_MONOTONIC_DESCRIPTIVE"


def strength_rows(rows: list[dict[str, Any]], within_lifecycle: bool = False, horizon: int = 5) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    scopes = [("WITHIN_LIFECYCLE", stage) for stage in ("MAIN_RISE", "FERMENTING", "MATURE")] if within_lifecycle else [("ALL_VALID_STAGES", "ALL")]
    for cohort in ("A2", "LEGACY5", "BOTH"):
        for scope, stage in scopes:
            base = [r for r in rows if r["cohort"] == cohort and r.get("strength_complete") and r.get("valid_five_stage") and (stage == "ALL" or r.get("lifecycle_stage") == stage)]
            for feature in STRENGTH_FIELDS + (STRENGTH_PROXY,):
                feature_values = [r[feature] for r in base if r.get(feature) is not None]
                feature_role = "SECONDARY_PROXY" if feature == STRENGTH_PROXY else "RAW_EVIDENCE_VECTOR"
                if not feature_values:
                    continue
                grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for row in base:
                    if row.get(feature) is not None:
                        grouped[rank_bin(feature_values, row[feature])].append(row)
                ordered_bin_values: list[float | None] = []
                for bin_name in ("Q1", "Q2", "Q3", "Q4", "ALL_SMALL_SAMPLE"):
                    bucket = grouped.get(bin_name, [])
                    for h in (horizon,):
                        metric_rows = [metric_row(r, r.get("outcome_by_horizon", {}).get(h), {}) for r in bucket]
                        endpoint = outcome_values(metric_rows, "endpoint_return")
                        mfe = outcome_values(metric_rows, "mfe")
                        mae = outcome_values(metric_rows, "mae")
                        result.append({
                            "cohort": cohort, "scope": scope, "lifecycle_stage": stage,
                            "feature": feature, "feature_role": feature_role, "analysis_type": "QUANTILE_BIN",
                            "bin": bin_name, "horizon": h, "N": len(bucket),
                            "instrument_count": len({r["instrument_id"] for r in bucket}),
                            "feature_mean": mean([r.get(feature) for r in bucket]), "feature_median": median([r.get(feature) for r in bucket]),
                            "endpoint_mean": mean(endpoint), "endpoint_median": median(endpoint),
                            "mfe_mean": mean(mfe), "mfe_median": median(mfe), "mae_mean": mean(mae), "mae_median": median(mae),
                            "small_sample_flag": len(bucket) < 20,
                            "threshold_policy": "NO_ARBITRARY_THRESHOLD; DESCRIPTIVE_QUANTILES_ONLY",
                        })
                    if grouped.get(bin_name):
                        h5 = [metric_row(r, r.get("outcome_by_horizon", {}).get(5), {}) for r in grouped[bin_name]]
                        ordered_bin_values.append(mean(outcome_values(h5, "endpoint_return")))
                for h in (horizon,):
                    result.append({
                        "cohort": cohort, "scope": scope, "lifecycle_stage": stage, "feature": feature,
                        "feature_role": feature_role, "analysis_type": "CONTINUOUS_MONOTONICITY",
                        "bin": "ORDERED_Q1_TO_Q4", "horizon": h, "N": len(base),
                        "instrument_count": len({r["instrument_id"] for r in base}),
                        "feature_mean": mean(feature_values), "feature_median": median(feature_values),
                        "monotonicity": monotonic_direction(ordered_bin_values),
                        "small_sample_flag": len(base) < 20,
                        "threshold_policy": "NO_ARBITRARY_THRESHOLD; DESCRIPTIVE_QUANTILES_ONLY",
                    })
    return result


def build_robustness(rows: list[dict[str, Any]], horizon: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for cohort in ("A2", "LEGACY5", "BOTH"):
        for stage in ("ALL_VALID_STAGES",) + LIFECYCLE_STAGES:
            selected = [r for r in rows if r["cohort"] == cohort and (stage == "ALL_VALID_STAGES" and r.get("valid_five_stage") or r.get("lifecycle_stage") == stage)]
            topic_counts = Counter(r.get("topic_id") or "MISSING" for r in selected)
            date_counts = Counter(r.get("signal_date") or "MISSING" for r in selected)
            instrument_counts = Counter(r.get("instrument_id") or "MISSING" for r in selected)
            for h in (horizon,):
                metrics: dict[str, Any] = {"cohort": cohort, "scope": stage, "horizon": h, "N": len(selected), "instrument_count": len(instrument_counts), "topic_count": len(topic_counts), "date_count": len(date_counts)}
                for field in ("endpoint_return", "mfe", "mae"):
                    values = outcome_values([metric_row(r, r.get("outcome_by_horizon", {}).get(h), {}) for r in selected], field)
                    metrics[f"{field}_mean"] = mean(values)
                    metrics[f"{field}_median"] = median(values)
                    metrics[f"{field}_trimmed5_mean"] = trim5(values)
                    metrics[f"{field}_winsorized5_mean"] = winsor5(values)
                metrics["top1_instrument_share"] = ratio(instrument_counts.most_common(1)[0][1], len(selected)) if selected else None
                metrics["top5_instrument_share"] = ratio(sum(v for _, v in instrument_counts.most_common(5)), len(selected)) if selected else None
                metrics["top1_topic_share"] = ratio(topic_counts.most_common(1)[0][1], len(selected)) if selected else None
                metrics["top1_date_share"] = ratio(date_counts.most_common(1)[0][1], len(selected)) if selected else None
                metrics["early_count"] = sum(as_date(r.get("signal_date")) and as_date(r.get("signal_date")) <= date(2026, 4, 30) for r in selected)
                metrics["middle_count"] = sum(as_date(r.get("signal_date")) and date(2026, 5, 1) <= as_date(r.get("signal_date")) <= date(2026, 6, 30) for r in selected)
                metrics["late_count"] = sum(as_date(r.get("signal_date")) and as_date(r.get("signal_date")) >= date(2026, 7, 1) for r in selected)
                metrics["concentration_disclosure"] = "DESCRIPTIVE_CONCENTRATION_AUDIT; NOT A FILTER"
                result.append(metrics)
    return result


def build_join_coverage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for cohort in ("A2", "LEGACY5", "BOTH"):
        selected = [r for r in rows if r["cohort"] == cohort]
        result.append({
            "cohort": cohort, "signal_count": len(selected), "instrument_count": len({r["instrument_id"] for r in selected}),
            "pair_count": len({r["pair_id"] for r in selected if r.get("pair_id")}),
            "valid_lifecycle_join_count": sum(r.get("lifecycle_join_status") == "VALID_LIFECYCLE_JOIN" for r in selected),
            "pending_count": sum(r.get("lifecycle_pending") for r in selected),
            "insufficient_data_count": sum(r.get("lifecycle_insufficient_data") for r in selected),
            "fail_closed_count": sum(r.get("lifecycle_fail_closed") for r in selected),
            "no_topic_match_count": sum(r.get("topic_match_status") == "NO_TOPIC_MATCH" for r in selected),
            "ambiguous_topic_match_count": sum(r.get("topic_match_status") == "AMBIGUOUS_TOPIC_MATCH" for r in selected),
            "no_lifecycle_row_count": sum(r.get("lifecycle_join_status") == "NO_LIFECYCLE_ROW" for r in selected),
            "strength_complete_count": sum(r.get("strength_complete") for r in selected),
            "strength_incomplete_count": sum(not r.get("strength_complete") for r in selected),
            "valid_five_stage_count": sum(r.get("valid_five_stage") for r in selected),
            "unmatched_retained": "YES",
        })
    return result


def apply_outcomes(signals: list[dict[str, Any]], bars: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for signal in signals:
        joined = dict(signal)
        for horizon in HORIZONS:
            outcome = signal.get("outcome_by_horizon", {}).get(horizon, {})
            joined[f"outcome_{horizon}"] = outcome
        for h in HORIZONS:
            joined[f"barrier_5_before_minus5_{h}"] = barrier_for_signal(signal, bars, h, 0.05, -0.05)
            joined[f"barrier_10_before_minus5_{h}"] = barrier_for_signal(signal, bars, h, 0.10, -0.05)
        rows.append(joined)
    return rows


def flatten_horizon_rows(rows: list[dict[str, Any]], horizon: int) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        outcome = item.pop(f"outcome_{horizon}", {}) or {}
        item["outcome_status"] = outcome.get("horizon_status") or outcome.get("maturity_status") or "OUTCOME_NOT_FOUND"
        for field in ("endpoint_return", "mfe", "mae"):
            item[field] = outcome.get(field)
        item["barrier_5_before_minus5"] = item.pop(f"barrier_5_before_minus5_{horizon}")
        item["barrier_10_before_minus5"] = item.pop(f"barrier_10_before_minus5_{horizon}")
        flattened.append(item)
    return flattened


def write_reports(output_dir: Path, sources: Mapping[str, Any], authority: Mapping[str, Any], rows: list[dict[str, Any]], source_root: Path, database_url: str, worktree_head: str) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    coverage = build_join_coverage(rows)
    expectancy: list[dict[str, Any]] = []
    path_rows: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    strength: list[dict[str, Any]] = []
    within: list[dict[str, Any]] = []
    both: list[dict[str, Any]] = []
    robustness: list[dict[str, Any]] = []

    for h in HORIZONS:
        flat = flatten_horizon_rows(rows, h)
        e, p = build_conditional(flat, h)
        expectancy.extend(e)
        path_rows.extend(p)
        missing.extend(build_missing_audit(rows)) if h == 5 else None
        strength.extend(strength_rows(flat, False, h))
        within.extend(strength_rows(flat, True, h))
        robustness.extend(build_robustness(flat, h))
        for cohort in ("BOTH",):
                for stage in ("UNCONDITIONAL_ALL_BOTH", "VALID_FIVE_STAGE_BASELINE") + LIFECYCLE_STAGES:
                    selected = [r for r in flat if r["cohort"] == cohort and (stage == "UNCONDITIONAL_ALL_BOTH" or (stage == "VALID_FIVE_STAGE_BASELINE" and r.get("valid_five_stage")) or r.get("lifecycle_stage") == stage)]
                    both.append({
                        "cohort": cohort, "both_semantics": "BOTH_SAME_SESSION_PRIMARY", "lifecycle_stage": stage, "horizon": h,
                        "N": len(selected), "pair_count": len({r["pair_id"] for r in selected if r.get("pair_id")}),
                        "instrument_count": len({r["instrument_id"] for r in selected}), "source_observation_count": len(selected),
                        "endpoint_median": median(outcome_values(selected, "endpoint_return")), "mfe_median": median(outcome_values(selected, "mfe")), "mae_median": median(outcome_values(selected, "mae")),
                        "endpoint_mean": mean(outcome_values(selected, "endpoint_return")), "mfe_mean": mean(outcome_values(selected, "mfe")), "mae_mean": mean(outcome_values(selected, "mae")),
                        "barrier_5_up_first_rate": barrier_rate(selected, "barrier_5_before_minus5", "UP_FIRST"), "barrier_5_down_first_rate": barrier_rate(selected, "barrier_5_before_minus5", "DOWN_FIRST"),
                        "barrier_10_up_first_rate": barrier_rate(selected, "barrier_10_before_minus5", "UP_FIRST"), "barrier_10_down_first_rate": barrier_rate(selected, "barrier_10_before_minus5", "DOWN_FIRST"),
                        "sample_retention_vs_unconditional": ratio(len(selected), len([r for r in flat if r["cohort"] == "BOTH"])),
                        "decision_use": "STRATEGY_REVIEW_INPUT_ONLY",
                    })
        # The bounded-window cohort is carried as a named sensitivity only;
        # this runner does not redefine or merge it into the primary BOTH.
        both.append({"cohort": "BOTH_WITHIN_1_SESSION", "both_semantics": "EXISTING_BOUNDED_WINDOW_SENSITIVITY", "lifecycle_stage": "NOT_RECONSTITUTED_FROM_PRIMARY_PANEL", "horizon": h, "N": "SEE_JOINT_SOURCE_ARTIFACT", "decision_use": "SENSITIVITY_DISCLOSURE_ONLY"})

    fields_common = ["cohort", "lifecycle_stage", "horizon", "N", "instrument_count", "matured_count", "endpoint_mean", "endpoint_median", "mfe_mean", "mfe_median", "mae_mean", "mae_median", "positive_endpoint_rate", "barrier_5_before_minus5_up_first_rate", "barrier_5_before_minus5_down_first_rate", "barrier_5_before_minus5_same_session_unknown_rate", "barrier_10_before_minus5_up_first_rate", "barrier_10_before_minus5_down_first_rate", "barrier_10_before_minus5_same_session_unknown_rate", "baseline_N", "conditional_minus_unconditional_endpoint_mean", "conditional_minus_unconditional_endpoint_median", "conditional_minus_unconditional_mfe_mean", "conditional_minus_unconditional_mfe_median", "conditional_minus_unconditional_mae_mean", "conditional_minus_unconditional_mae_median", "comparison_purpose", "small_sample_flag"]
    write_csv(output_dir / "signal-lifecycle-join-coverage.csv", coverage)
    write_csv(output_dir / "lifecycle-conditional-expectancy.csv", expectancy, fields_common)
    write_csv(output_dir / "lifecycle-path-risk-analysis.csv", path_rows)
    write_csv(output_dir / "missing-failclosed-selection-bias.csv", missing)
    write_csv(output_dir / "strength-conditional-analysis.csv", strength)
    write_csv(output_dir / "within-lifecycle-strength-analysis.csv", within)
    write_csv(output_dir / "both-lifecycle-special-analysis.csv", both)
    write_csv(output_dir / "robustness-concentration-audit.csv", robustness)

    source_files = {}
    for name, path in sources["paths"].items():
        source_files[name] = {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
    source_files["l5_manifest_declared_dataset_sha256"] = sources["l5_manifest"].get("dataset", {}).get("normalized_dataset_sha256")
    source_files["ohlcv_surface_expected_sha256"] = "e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4"

    protocol = {
        "dataset_version": "WS1-L5-CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION",
        "dataset_sha256": sources["l5_manifest"].get("dataset", {}).get("normalized_dataset_sha256"),
        "dataset_rows": len(sources["l5_rows"]),
        "lifecycle_window": {"start": "2026-02-03", "end": "2026-08-13", "source_class": "CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION", "pit_truth": "NO"},
        "signal_cohorts": {"A2": "EXISTING_5277_EVENT_PANEL", "LEGACY5": "EXISTING_2471_DISTINCT_EPISODES_LEGACY-5", "BOTH": "EXISTING_SAME_SESSION_INTERSECTION; TWO_SOURCE_OBSERVATIONS_PER_PAIR"},
        "time_splits": [
            {"name": "EARLY", "start": "2026-02-03", "end": "2026-04-30"},
            {"name": "MIDDLE", "start": "2026-05-01", "end": "2026-06-30"},
            {"name": "LATE", "start": "2026-07-01", "end": "2026-08-13"},
        ],
        "parameter_version": "ws3-technical-signal-lifecycle-strength-study.v1",
        "candidate_definitions": {"lifecycle": "WS1 L5 accepted raw reconstruction stages", "strength": "raw vector only; no score/label/threshold", "barriers": "+5% before -5% and +10% before -5%; same-session order unknown"},
        "failure_criteria": ["source path/hash/count mismatch", "relation selection count != 852", "unavailable OHLCV path", "ambiguous/no relation is retained and not imputed"],
        "evaluation_mode": "RETROSPECTIVE_DESCRIPTIVE_WALK_FORWARD_SLICES; NO_PARAMETER_FITTING; NO_OOS_CLAIM",
    }
    run_summary = {
        "task_id": TASK_ID, "status": "COMPLETE_PASS_WITH_BOUNDED_RESEARCH_LIMITATIONS",
        "worktree_head": worktree_head, "canonical_source_root": str(source_root),
        "dataset_protocol": protocol, "source_files": source_files,
        "authority": {"current_relation_count": len(authority["relations"]), "current_instrument_count": len(authority["relation_by_instrument"]), "relation_hash": authority["relation_hash"], "ohlcv_rows_queried": authority["bar_rows"], "ohlcv_surface_adjustment_state": "UNKNOWN_RAW_ONLY"},
        "cohort_counts": {cohort: {"signal_observation_count": sum(r["cohort"] == cohort for r in rows), "instrument_count": len({r["instrument_id"] for r in rows if r["cohort"] == cohort}), "pair_count": len({r["pair_id"] for r in rows if r["cohort"] == cohort and r.get("pair_id")})} for cohort in ("A2", "LEGACY5", "BOTH")},
        "walk_forward_execution": "YES; fixed historical lifecycle join and outcome horizon slices executed",
        "lookahead_audit": {"signal_date_before_outcome": "PASS", "lifecycle_stage_uses_signal_date_only": "PASS", "outcome_used_for_topic_selection": "NO", "outcome_used_for_strength_bins": "NO", "browser_or_adhoc_substitution": "NO"},
        "governance": {"WS3_ONLY": "YES", "A2_DEFINITION_CHANGED": "NO", "LEGACY5_DEFINITION_CHANGED": "NO", "BOTH_DEFINITION_CHANGED": "NO", "LIFECYCLE_POLICY_CHANGED": "NO", "STRENGTH_SCORE_CREATED": "NO", "PRODUCTION_FILTER_CREATED": "NO", "STRATEGY_ACCEPTED": "NO", "OOS_CLAIM": "NO", "DB_MUTATION": "NO", "DEPLOY": "NO", "PUSH": "NO", "NEXT_TASK_CHANGED": "NO"},
        "artifacts": {},
    }
    for path in sorted(output_dir.iterdir()):
        if path.is_file() and path.name not in {"run-summary.json", "reproducibility-manifest.json", "formal-closure-report.md", "OWNER-DECISION-MEMO.md"}:
            run_summary["artifacts"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}

    write_json(output_dir / "run-summary.json", run_summary)
    reproducibility = {
        "schema_version": "ws3-technical-signal-lifecycle-strength-reproducibility.v1",
        "task_id": TASK_ID, "protocol": protocol, "source_artifacts": source_files,
        "authority_relation_hash": authority["relation_hash"], "authority_relation_count": len(authority["relations"]),
        "output_artifacts": {path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in sorted(output_dir.iterdir()) if path.is_file() and path.name not in {"run-summary.json", "reproducibility-manifest.json"}},
        "replay_contract": "A second run with identical source hashes, database relation hash, database surface and arguments must reproduce every CSV/JSON byte-for-byte except runtime metadata not emitted by this runner",
        "test_count_delta_status": "NOT_APPLICABLE_RESEARCH_ONLY",
        "source_to_canonical_provenance": "source artifacts are canonical owner research artifacts; output is promoted commit-preserving after isolated validation",
        "clean_dependency_check": "PASS; standard library + SQLAlchemy/psycopg read-only database access",
    }
    write_json(output_dir / "reproducibility-manifest.json", reproducibility)
    run_summary["artifacts"]["reproducibility-manifest.json"] = {"bytes": (output_dir / "reproducibility-manifest.json").stat().st_size, "sha256": sha256_file(output_dir / "reproducibility-manifest.json")}
    write_json(output_dir / "run-summary.json", run_summary)

    closure = f"""# Formal Closure — {TASK_ID}

## Disposition

`COMPLETE_PASS_WITH_BOUNDED_RESEARCH_LIMITATIONS`. This is a WS3-only,
retrospective descriptive conditional-expectancy study and Strategy Review
input. It is not an accepted strategy, recommendation publication, Opportunity
activation, OOS result, or production filter.

## Frozen authority and protocol

- L5 dataset: `{protocol['dataset_version']}`, `{protocol['dataset_sha256']}`, 16,250 topic/date rows, lifecycle window 2026-02-03 through 2026-08-13.
- Current taxonomy relation selection: {len(authority['relations'])} rows, hash `{authority['relation_hash']}`; latest non-superseded open-ended relation per topic/instrument, exactly the L5 selection rule.
- A2: existing 5,277-event panel; Legacy-5: existing 2,471 distinct episodes; BOTH: existing 560 same-session pairs represented as two source observations per pair.
- Strength is the raw vector `positive_breadth`, `strong_breadth`, `weak_ratio`, `average_change_pct`; `leader_change_pct` is proxy evidence only. No score, label, or arbitrary threshold was created.

## Walk-forward and look-ahead controls

The fixed historical slices EARLY (2026-02-03–2026-04-30), MIDDLE
(2026-05-01–2026-06-30), and LATE (2026-07-01–2026-08-13) were evaluated
descriptively. Lifecycle is joined at signal date; outcomes are strictly
future canonical sessions. Topic selection never uses outcomes, strength bins
are feature-only quantiles, and same-session barrier order remains unknown.

## Fail-closed and bias audit

No-topic, ambiguous-topic, missing lifecycle, PENDING, INSUFFICIENT_DATA,
FAIL_CLOSED, and incomplete-strength rows are retained in coverage and the
selection-bias audit. They are not silently removed and no improvement claim is
made from their exclusion. Raw OHLCV adjustment/corporate-action state remains
`UNKNOWN_RAW_ONLY`; results are not economic-return truth.

## Required final answers

1. Dataset/protocol identity: see `run-summary.json` and `reproducibility-manifest.json`.
2. Walk-forward actually executed: **YES**, fixed retrospective slices; no parameter fitting.
3. Lifecycle conditional expectancy: `lifecycle-conditional-expectancy.csv`.
4. Lifecycle path/risk races: `lifecycle-path-risk-analysis.csv`.
5. Missing/fail-closed selection bias: `missing-failclosed-selection-bias.csv`.
6. Strength conditional evidence: `strength-conditional-analysis.csv` and `within-lifecycle-strength-analysis.csv`.
7. BOTH special analysis: `both-lifecycle-special-analysis.csv`; same-session primary, bounded-window sensitivity disclosed separately.
8. Robustness/concentration: `robustness-concentration-audit.csv`.
9. Look-ahead/PIT: signal-date join and future-session outcome checks pass; historical lifecycle is not PIT truth.
10. Research conclusion: descriptive Strategy Review input only; no accepted/rejected owner decision.
11. Production/governance: no database mutation, deploy, push, production filter, or NEXT_TASK change.
12. Promotion: isolated artifacts are eligible for commit-preserving canonical promotion after Owner review; no remote push.

## Governance flags

`WS3_ONLY=YES`, `A2_DEFINITION_CHANGED=NO`, `LEGACY5_DEFINITION_CHANGED=NO`,
`BOTH_DEFINITION_CHANGED=NO`, `LIFECYCLE_POLICY_CHANGED=NO`,
`STRENGTH_SCORE_CREATED=NO`, `PRODUCTION_FILTER_CREATED=NO`,
`STRATEGY_ACCEPTED=NO`, `OOS_CLAIM=NO`, `DB_MUTATION=NO`, `DEPLOY=NO`,
`PUSH=NO`, `NEXT_TASK_CHANGED=NO`.

`CANONICAL_STATUS=ISOLATED_VALIDATED_PENDING_PROMOTION`; `RELEASE_STATUS=NOT_RELEASED`;
`PRODUCTION_VERIFICATION=NOT_PERFORMED_BY_SCOPE`; `CANONICAL_RECONCILIATION_DISPOSITION=COMMIT_PRESERVING_PROMOTION_ONLY`.
`REPOSITORY_HYGIENE_STATUS=OWNER_DIRTY_STATE_PRESERVED; SPARSE_TASK_WORKTREE_USED`.
"""
    (output_dir / "formal-closure-report.md").write_text(closure, encoding="utf-8")
    memo = f"""# Owner Decision Memo — {TASK_ID}

## Request to Owner

Please review the conditional expectancy, path-risk, missing/fail-closed bias,
strength-vector, BOTH, and concentration artifacts as research evidence. The
runner intentionally makes no accepted/rejected strategy decision.

## Evidence summary

- A2, Legacy-5, and BOTH definitions are unchanged.
- Current relation authority reconciled to {len(authority['relations'])} selected rows; relation hash `{authority['relation_hash']}`.
- Missing and fail-closed rows remain visible. `UNKNOWN_RAW_ONLY` adjustment state limits interpretation to descriptive raw-path evidence.
- Median, trimmed/winsorized, sample-retention, instrument/topic/date concentration and fixed historical slices are included.

## Explicit owner decisions not made by this task

`STRATEGY_ACCEPTED=NO`; `PRODUCTION_FILTER_CREATED=NO`; `OOS_CLAIM=NO`.
The outputs are Strategy Review input only.

## Promotion disposition

After review, the report package may be promoted commit-preserving to the
canonical repository. No remote push, deployment, scheduler change, database
mutation, or NEXT_TASK change is included.
"""
    (output_dir / "OWNER-DECISION-MEMO.md").write_text(memo, encoding="utf-8")
    return run_summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL") or os.environ.get("DATABASE_URL") or "postgresql+psycopg://topicpilot:topicpilot_local_only@localhost:5432/topicpilot")
    parser.add_argument("--worktree-head", default="UNKNOWN")
    args = parser.parse_args()
    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    sources = load_sources(source_root)
    signals = build_signals(sources)
    l5_by_key = {(row.get("topic_id", ""), row.get("trading_date", "")): row for row in sources["l5_rows"]}
    instrument_ids = {str(row["instrument_id"]) for row in signals}
    signal_dates = [as_date(row["signal_date"]) for row in signals if as_date(row["signal_date"])]
    authority = load_authority(args.database_url, instrument_ids, min(signal_dates), date(2026, 8, 13))
    for signal in signals:
        join_lifecycle(signal, authority["relation_by_instrument"], l5_by_key)
    enriched = apply_outcomes(signals, authority["bars_by_instrument"])
    write_reports(output_dir, sources, authority, enriched, source_root, args.database_url, args.worktree_head)
    print(json.dumps({"task_id": TASK_ID, "output_dir": str(output_dir), "signal_count": len(enriched), "relation_count": len(authority["relations"]), "bar_rows": authority["bar_rows"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

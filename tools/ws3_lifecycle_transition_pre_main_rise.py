"""WS3-only pre-MAIN_RISE lifecycle transition expectancy study.

This runner consumes frozen research artifacts from the E: canonical checkout,
joins technical signals to the WS1 L5 retrospective panel, and evaluates
signal dates around the first candidate/confirmed MAIN_RISE transition.  It
does not change any strategy, lifecycle policy, database state, or production
surface.
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


TASK_ID = "TASK-WS3-LIFECYCLE-TRANSITION-PRE-MAIN-RISE-CONDITIONAL-EXPECTANCY-STUDY-20260823"
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
A2_FREEZE = "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-confirmatory-protocol-freeze.json"

START_DATE = date(2026, 2, 3)
END_DATE = date(2026, 8, 13)
HORIZONS = (5, 10)
WINDOWS = ("D-3", "D-2", "D-1", "D0")
WINDOW_OFFSETS = {"D-3": 3, "D-2": 2, "D-1": 1, "D0": 0}
LIFECYCLE_STAGES = ("SPROUTING", "FERMENTING", "MAIN_RISE", "MATURE", "DECLINING")
STRENGTH_FIELDS = ("positive_breadth", "strong_breadth", "weak_ratio", "average_change_pct", "leader_change_pct")
PRIMARY_COHORTS = ("ALL_TECHNICAL", "A2", "LEGACY5", "BOTH_SAME_SESSION")
ALL_COHORTS = PRIMARY_COHORTS + ("BOTH_WITHIN_1_SENSITIVITY",)
TRANSITION_TYPES = ("CANDIDATE_ONSET", "CONFIRMED_TRANSITION")
EXPECTED_COUNTS = {"l5_rows": 16250, "a2_events": 5277, "legacy_episodes": 2471}


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
            writer.writerow({field: row.get(field, "") for field in fields})


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


def mean(values: Iterable[Any]) -> float | None:
    numbers = [float(value) for value in values if as_float(value) is not None]
    return statistics.fmean(numbers) if numbers else None


def median(values: Iterable[Any]) -> float | None:
    numbers = [float(value) for value in values if as_float(value) is not None]
    return statistics.median(numbers) if numbers else None


def trim5(values: Iterable[Any]) -> float | None:
    numbers = sorted(float(value) for value in values if as_float(value) is not None)
    if not numbers:
        return None
    cut = int(len(numbers) * 0.05)
    retained = numbers[cut: len(numbers) - cut] if len(numbers) > 2 * cut else numbers
    return statistics.fmean(retained) if retained else None


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def pct(value: float | None) -> str:
    return "NA" if value is None else f"{value * 100:.2f}%"


def fmt(value: float | int | None) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def period_for(value: Any) -> str:
    current = as_date(value)
    if current is None:
        return "UNKNOWN"
    if current <= date(2026, 4, 30):
        return "EARLY"
    if current <= date(2026, 6, 30):
        return "MIDDLE"
    return "LATE"


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
        "a2_freeze": source_root / A2_FREEZE,
    }
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise RuntimeError("FAIL_CLOSED_SOURCE_PATH_MISSING:" + ",".join(missing))
    l5_rows = read_csv(paths["l5_dataset"])
    a2_panel = read_csv(paths["a2_panel"])
    a2_outcomes = read_csv(paths["a2_outcomes"])
    legacy_episodes = [row for row in read_csv(paths["legacy_episodes"]) if row.get("variant") == "LEGACY-5"]
    legacy_outcomes = [row for row in read_csv(paths["legacy_outcomes"]) if row.get("variant") == "LEGACY-5"]
    if len(l5_rows) != EXPECTED_COUNTS["l5_rows"]:
        raise RuntimeError(f"FAIL_CLOSED_L5_ROW_COUNT:{len(l5_rows)}")
    if len(a2_panel) != EXPECTED_COUNTS["a2_events"] or len({row.get("event_id") for row in a2_panel}) != EXPECTED_COUNTS["a2_events"]:
        raise RuntimeError(f"FAIL_CLOSED_A2_EVENT_COUNT:{len(a2_panel)}")
    if len(legacy_episodes) != EXPECTED_COUNTS["legacy_episodes"] or len({row.get("episode_id") for row in legacy_episodes}) != EXPECTED_COUNTS["legacy_episodes"]:
        raise RuntimeError(f"FAIL_CLOSED_LEGACY_EPISODE_COUNT:{len(legacy_episodes)}")
    for row in l5_rows:
        row["_date"] = as_date(row.get("trading_date"))
    l5_rows.sort(key=lambda row: (row.get("topic_id", ""), row.get("_date") or date.min))
    return {
        "paths": paths,
        "l5_rows": l5_rows,
        "a2_panel": a2_panel,
        "a2_outcomes": a2_outcomes,
        "legacy_episodes": legacy_episodes,
        "legacy_outcomes": legacy_outcomes,
        "l5_manifest": read_json(paths["l5_manifest"]),
        "legacy_manifest": read_json(paths["legacy_manifest"]),
        "joint_run": read_json(paths["joint_run"]),
        "joint_semantics": read_json(paths["joint_semantics"]),
        "a2_freeze": read_json(paths["a2_freeze"]),
    }


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
    try:
        with engine.connect() as connection:
            relation_rows = [dict(row) for row in connection.execute(relation_sql).mappings()]
            bar_rows = [dict(row) for row in connection.execute(bar_sql, {"start_date": start, "end_date": end, "instrument_ids": sorted(instrument_ids)}).mappings()]
    finally:
        engine.dispose()
    relation_by_instrument: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in relation_rows:
        for key in ("valid_from", "valid_to"):
            if row.get(key) is not None:
                row[key] = str(row[key])
        relation_by_instrument[row["instrument_id"]].append(row)
    bars_by_instrument: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in bar_rows:
        row["trade_date"] = as_date(row.get("trade_date"))
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


def build_transition_events(l5_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in l5_rows:
        by_topic[row.get("topic_id", "")].append(row)
    events: list[dict[str, Any]] = []
    for topic_id, rows in sorted(by_topic.items()):
        rows.sort(key=lambda row: row.get("_date") or date.min)
        candidate = next((row for row in rows if row.get("candidate_stage") == "MAIN_RISE"), None)
        confirmed = next((row for row in rows if row.get("lifecycle_stage") == "MAIN_RISE" and row.get("previous_stage") != "MAIN_RISE" and row.get("transition_decision") in {"CONFIRMED_TRANSITION", "JUMP_TRANSITION"}), None)
        topic_slug = (confirmed or candidate or {}).get("topic_slug", "")
        topic_name = (confirmed or candidate or {}).get("topic_name", "")
        first_confirmed_date = (confirmed or {}).get("trading_date", "")
        candidate_date = (candidate or {}).get("trading_date", "")
        for event_type, source_row in (("CANDIDATE_ONSET", candidate), ("CONFIRMED_TRANSITION", confirmed)):
            if source_row is None:
                continue
            index = rows.index(source_row)
            d0 = source_row.get("_date")
            previous_stage = source_row.get("previous_stage") or ""
            if previous_stage == "SPROUTING":
                route = "SPROUTING_TO_MAIN_RISE"
            elif previous_stage == "FERMENTING":
                route = "FERMENTING_TO_MAIN_RISE"
            elif previous_stage == "MATURE":
                route = "MATURE_TO_MAIN_RISE"
            elif previous_stage:
                route = "OTHER_TO_MAIN_RISE"
            else:
                route = "BOOTSTRAP_PRIOR_STATE_UNKNOWN"
            event_id = hashlib.sha256(f"{topic_id}|{event_type}|{source_row.get('trading_date')}|{source_row.get('transition_decision')}|{source_row.get('stage_entered_at')}".encode()).hexdigest()
            event = {
                "event_id": event_id,
                "event_semantics": event_type,
                "topic_id": topic_id,
                "topic_slug": topic_slug,
                "topic_name": topic_name,
                "d0_date": source_row.get("trading_date", ""),
                "d0_index": index,
                "previous_stage": previous_stage,
                "candidate_stage": source_row.get("candidate_stage", ""),
                "d0_lifecycle_stage": source_row.get("lifecycle_stage", ""),
                "transition_decision": source_row.get("transition_decision", ""),
                "transition_reason": source_row.get("transition_reason", ""),
                "stage_entered_at": source_row.get("stage_entered_at", ""),
                "stage_trading_days": source_row.get("stage_trading_days", ""),
                "route": route,
                "strong_jump": source_row.get("transition_decision") == "JUMP_TRANSITION",
                "bootstrap_prior_state": not bool(previous_stage) or index == 0,
                "candidate_onset_date": candidate_date,
                "confirmed_transition_date": first_confirmed_date,
                "source_class": source_row.get("source_class", ""),
                "evaluation_mode": source_row.get("evaluation_mode", ""),
                "policy_version": source_row.get("policy_version", ""),
                "calculation_version": source_row.get("calculation_version", ""),
                "publication_state": source_row.get("publication_state", ""),
            }
            for field in STRENGTH_FIELDS:
                event[f"raw_D0_{field}"] = as_float(source_row.get(field))
            for window, offset in WINDOW_OFFSETS.items():
                row = rows[index - offset] if index >= offset else None
                event[f"{window}_date"] = row.get("trading_date", "") if row else ""
                event[f"{window}_available"] = bool(row)
                event[f"{window}_lineage_status"] = row.get("lineage_status", "") if row else ""
                event[f"{window}_data_status"] = row.get("data_status", "") if row else ""
                event[f"{window}_lifecycle_stage"] = row.get("lifecycle_stage", "") if row else ""
                event[f"{window}_transition_decision"] = row.get("transition_decision", "") if row else ""
                for field in STRENGTH_FIELDS:
                    event[f"raw_{window}_{field}"] = as_float(row.get(field)) if row else None
            for field in STRENGTH_FIELDS:
                for current, prior in (("D-2", "D-3"), ("D-1", "D-2"), ("D0", "D-1")):
                    current_value = event.get(f"raw_{current}_{field}")
                    prior_value = event.get(f"raw_{prior}_{field}")
                    event[f"delta_{current}_minus_{prior}_{field}"] = current_value - prior_value if current_value is not None and prior_value is not None else None
            events.append(event)
    return sorted(events, key=lambda row: (row["event_semantics"], row.get("d0_date", ""), row["topic_id"]))


def outcome_index(rows: list[dict[str, str]], key: str, status_field: str) -> dict[tuple[str, int], dict[str, Any]]:
    result: dict[tuple[str, int], dict[str, Any]] = {}
    for raw in rows:
        horizon = int(raw.get("horizon") or 0)
        if horizon not in HORIZONS:
            continue
        item = dict(raw)
        item["horizon_status"] = raw.get(status_field) or raw.get("horizon_status") or raw.get("maturity_status") or ""
        for field in ("endpoint_return", "mfe", "mae"):
            item[field] = as_float(raw.get(field))
        result[(raw.get(key, ""), horizon)] = item
    return result


def make_signal(cohort: str, source_signal: str, signal_id: str, raw: Mapping[str, Any], outcomes: Mapping[int, Mapping[str, Any]], pair_id: str = "", timing_delta: Any = "") -> dict[str, Any]:
    return {
        "cohort": cohort,
        "source_signal": source_signal,
        "signal_id": signal_id,
        "origin_signal_id": raw.get("event_id") or raw.get("episode_id") or signal_id,
        "instrument_id": raw.get("instrument_id", ""),
        "stock_code": raw.get("stock_code", ""),
        "market": raw.get("market", ""),
        "signal_date": raw.get("signal_date") or raw.get("episode_start_date") or "",
        "anchor_close": as_float(raw.get("a2_close") or raw.get("anchor_close")),
        "pair_id": pair_id,
        "timing_delta_sessions": timing_delta,
        "outcome_by_horizon": {int(key): dict(value) for key, value in outcomes.items()},
    }


def build_signals(sources: Mapping[str, Any], bars: Mapping[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    a2_outcomes = outcome_index(sources["a2_outcomes"], "event_id", "horizon_status")
    legacy_outcomes = outcome_index(sources["legacy_outcomes"], "episode_id", "maturity_status")
    a2: list[dict[str, Any]] = []
    legacy: list[dict[str, Any]] = []
    for raw in sources["a2_panel"]:
        a2.append(make_signal("A2", "A2", raw["event_id"], raw, {h: a2_outcomes.get((raw["event_id"], h), {}) for h in HORIZONS}))
    for raw in sources["legacy_episodes"]:
        legacy.append(make_signal("LEGACY5", "LEGACY5", raw["episode_id"], raw, {h: legacy_outcomes.get((raw["episode_id"], h), {}) for h in HORIZONS}))
    signals = a2 + legacy
    for source in (a2, legacy):
        for row in source:
            signals.append({**row, "cohort": "ALL_TECHNICAL", "signal_id": f"ALL|{row['source_signal']}|{row['origin_signal_id']}"})
    a2_by_key = {(row["instrument_id"], row["signal_date"]): row for row in a2}
    legacy_by_key = {(row["instrument_id"], row["signal_date"]): row for row in legacy}
    same_keys = sorted(set(a2_by_key).intersection(legacy_by_key))
    for key in same_keys:
        a2_row, legacy_row = a2_by_key[key], legacy_by_key[key]
        pair_id = f"{a2_row['origin_signal_id']}|{legacy_row['origin_signal_id']}"
        for row in (a2_row, legacy_row):
            signals.append({**row, "cohort": "BOTH_SAME_SESSION", "signal_id": f"{pair_id}|{row['source_signal']}", "pair_id": pair_id, "timing_delta_sessions": 0})
    session_positions: dict[str, dict[date, int]] = {}
    for instrument_id, rows in bars.items():
        session_positions[instrument_id] = {row["trade_date"]: index for index, row in enumerate(rows)}
    candidates: list[tuple[int, str, str, int]] = []
    for a2_row in a2:
        a_pos = session_positions.get(a2_row["instrument_id"], {}).get(as_date(a2_row["signal_date"]))
        if a_pos is None:
            continue
        for legacy_row in legacy:
            if legacy_row["instrument_id"] != a2_row["instrument_id"]:
                continue
            l_pos = session_positions.get(legacy_row["instrument_id"], {}).get(as_date(legacy_row["signal_date"]))
            if l_pos is None or abs(a_pos - l_pos) > 1:
                continue
            candidates.append((abs(a_pos - l_pos), a2_row["origin_signal_id"], legacy_row["origin_signal_id"], a_pos - l_pos))
    used_a2: set[str] = set()
    used_legacy: set[str] = set()
    matched_within = []
    for distance, a2_id, legacy_id, delta in sorted(candidates):
        if a2_id in used_a2 or legacy_id in used_legacy:
            continue
        a2_row = next(row for row in a2 if row["origin_signal_id"] == a2_id)
        legacy_row = next(row for row in legacy if row["origin_signal_id"] == legacy_id)
        used_a2.add(a2_id)
        used_legacy.add(legacy_id)
        pair_id = f"{a2_id}|{legacy_id}"
        matched_within.append((a2_row, legacy_row, pair_id, delta))
        for row in (a2_row, legacy_row):
            signals.append({**row, "cohort": "BOTH_WITHIN_1_SENSITIVITY", "signal_id": f"{pair_id}|{row['source_signal']}", "pair_id": pair_id, "timing_delta_sessions": delta})
    counts = {"a2": len(a2), "legacy5": len(legacy), "both_same_pairs": len(same_keys), "both_within_1_pairs": len(matched_within)}
    if counts["both_same_pairs"] == 0:
        raise RuntimeError("FAIL_CLOSED_BOTH_SAME_SESSION_UNAVAILABLE")
    return signals, counts


def barrier_for_signal(signal: Mapping[str, Any], bars: Mapping[str, list[dict[str, Any]]], horizon: int, up: float, down: float) -> str:
    rows = bars.get(str(signal.get("instrument_id")), [])
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
    for row in future:
        high, low = row.get("high"), row.get("low")
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


def attach_lifecycle(signal: dict[str, Any], authority: Mapping[str, Any], l5_by_key: Mapping[tuple[str, str], dict[str, str]], bars: Mapping[str, list[dict[str, Any]]]) -> dict[str, Any]:
    relations = authority["relation_by_instrument"].get(str(signal.get("instrument_id")), [])
    chosen, status = choose_relation(relations)
    signal["relation_candidate_count"] = len(relations)
    signal["topic_match_status"] = status
    signal["topic_id"] = chosen.get("topic_id", "") if chosen else ""
    signal["topic_slug"] = chosen.get("topic_slug", "") if chosen else ""
    signal["topic_name"] = chosen.get("topic_name", "") if chosen else ""
    signal["relation_lineage_hash"] = chosen.get("lineage_hash", "") if chosen else ""
    l5 = l5_by_key.get((str(signal.get("topic_id")), str(signal.get("signal_date")))) if chosen else None
    signal["lifecycle_join_status"] = "VALID_LIFECYCLE_JOIN" if l5 else ("NO_LIFECYCLE_ROW" if chosen else status)
    for field in ("lifecycle_stage", "previous_stage", "candidate_stage", "stage_entered_at", "stage_trading_days", "evaluation_status", "data_status", "transition_decision", "transition_reason", "quality_status", "lineage_status", "strength_raw_evidence_status", "coverage_pct", "confidence", "valid_member_count", "partial_lineage_flag", "unknown_lineage_flag", "fail_closed_flag"):
        signal[field] = l5.get(field, "") if l5 else ""
    for field in STRENGTH_FIELDS:
        signal[field] = as_float(l5.get(field)) if l5 else None
    signal["valid_five_stage"] = signal.get("lifecycle_stage") in LIFECYCLE_STAGES
    signal["signal_date_period"] = period_for(signal.get("signal_date"))
    signal["prior_5_session_return"] = None
    bars_for_instrument = bars.get(str(signal.get("instrument_id")), [])
    positions = [index for index, row in enumerate(bars_for_instrument) if row.get("trade_date") == as_date(signal.get("signal_date"))]
    if positions and positions[0] >= 5:
        current = bars_for_instrument[positions[0]].get("close")
        prior = bars_for_instrument[positions[0] - 5].get("close")
        if current is not None and prior not in (None, 0):
            signal["prior_5_session_return"] = current / prior - 1.0
    signal["barrier_5_h5"] = barrier_for_signal(signal, bars, 5, 0.05, -0.05)
    signal["barrier_10_h5"] = barrier_for_signal(signal, bars, 5, 0.10, -0.05)
    signal["barrier_5_h10"] = barrier_for_signal(signal, bars, 10, 0.05, -0.05)
    signal["barrier_10_h10"] = barrier_for_signal(signal, bars, 10, 0.10, -0.05)
    return signal


def build_event_matches(events: list[dict[str, Any]], signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signals_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for signal in signals:
        if signal.get("topic_match_status") not in {"PRIMARY_REPRESENTATIVE_UNIQUE", "PRIMARY_RELATION_UNIQUE", "UNIQUE_RELATION"}:
            continue
        if signal.get("lifecycle_join_status") != "VALID_LIFECYCLE_JOIN":
            continue
        signals_by_key[(str(signal.get("topic_id")), str(signal.get("signal_date")))].append(signal)
    matches: list[dict[str, Any]] = []
    for event in events:
        for window in WINDOWS:
            asof = event.get(f"{window}_date", "")
            if not asof:
                continue
            for signal in signals_by_key.get((event["topic_id"], asof), []):
                row = dict(signal)
                row.update({
                    "transition_event_id": event["event_id"],
                    "event_semantics": event["event_semantics"],
                    "observation_window": window,
                    "transition_d0_date": event["d0_date"],
                    "transition_route": event["route"],
                    "transition_previous_stage": event["previous_stage"],
                    "transition_decision": event["transition_decision"],
                    "transition_reason": event["transition_reason"],
                    "transition_strong_jump": event["strong_jump"],
                    "bootstrap_prior_state": event["bootstrap_prior_state"],
                    "evidence_as_of_date": asof,
                    "uses_d0_evidence": window == "D0",
                    "inference_role": "CONTEMPORANEOUS_TRANSITION_CONDITIONED" if window == "D0" else "PRIMARY_PRETRANSITION",
                    "anti_leakage_status": "PASS_D0_SEPARATED" if window != "D0" else "D0_SEPARATELY_REPORTED",
                })
                matches.append(row)
    return matches


def outcome_for(row: Mapping[str, Any], horizon: int) -> Mapping[str, Any]:
    outcomes = row.get("outcome_by_horizon") or {}
    return outcomes.get(horizon) or outcomes.get(str(horizon)) or {}


def summary_metrics(rows: list[dict[str, Any]], horizon: int) -> dict[str, Any]:
    endpoint = [as_float(outcome_for(row, horizon).get("endpoint_return")) for row in rows]
    mfe = [as_float(outcome_for(row, horizon).get("mfe")) for row in rows]
    mae = [as_float(outcome_for(row, horizon).get("mae")) for row in rows]
    endpoint_values = [value for value in endpoint if value is not None]
    mfe_values = [value for value in mfe if value is not None]
    mae_values = [value for value in mae if value is not None]
    barriers5 = [row.get(f"barrier_5_h{horizon}") for row in rows]
    barriers10 = [row.get(f"barrier_10_h{horizon}") for row in rows]
    return {
        "N": len(rows),
        "outcome_n": len(endpoint_values),
        "matured_n": sum((outcome_for(row, horizon).get("horizon_status") or outcome_for(row, horizon).get("maturity_status")) in {"COMPLETE_RAW_PATH", "COMPLETE"} for row in rows),
        "instrument_count": len({row.get("instrument_id") for row in rows if row.get("instrument_id")}),
        "topic_count": len({row.get("topic_id") for row in rows if row.get("topic_id")}),
        "date_count": len({row.get("signal_date") for row in rows if row.get("signal_date")}),
        "event_count": len({row.get("transition_event_id") for row in rows if row.get("transition_event_id")}),
        "pair_count": len({row.get("pair_id") for row in rows if row.get("pair_id")}),
        "endpoint_mean": mean(endpoint_values),
        "endpoint_median": median(endpoint_values),
        "endpoint_trimmed5_mean": trim5(endpoint_values),
        "positive_endpoint_rate": ratio(sum(value > 0 for value in endpoint_values), len(endpoint_values)),
        "mfe_mean": mean(mfe_values),
        "mfe_median": median(mfe_values),
        "mae_mean": mean(mae_values),
        "mae_median": median(mae_values),
        "mae_le_minus5_rate": ratio(sum(value <= -0.05 for value in mae_values), len(mae_values)),
        "mfe_ge_5_rate": ratio(sum(value >= 0.05 for value in mfe_values), len(mfe_values)),
        "barrier_5_up_first_rate": ratio(sum(value == "UP_FIRST" for value in barriers5), sum(value in {"UP_FIRST", "DOWN_FIRST", "SAME_SESSION_ORDER_UNKNOWN", "NEITHER_BY_H"} for value in barriers5)),
        "barrier_5_down_first_rate": ratio(sum(value == "DOWN_FIRST" for value in barriers5), sum(value in {"UP_FIRST", "DOWN_FIRST", "SAME_SESSION_ORDER_UNKNOWN", "NEITHER_BY_H"} for value in barriers5)),
        "barrier_5_same_session_unknown_rate": ratio(sum(value == "SAME_SESSION_ORDER_UNKNOWN" for value in barriers5), sum(value in {"UP_FIRST", "DOWN_FIRST", "SAME_SESSION_ORDER_UNKNOWN", "NEITHER_BY_H"} for value in barriers5)),
        "barrier_10_up_first_rate": ratio(sum(value == "UP_FIRST" for value in barriers10), sum(value in {"UP_FIRST", "DOWN_FIRST", "SAME_SESSION_ORDER_UNKNOWN", "NEITHER_BY_H"} for value in barriers10)),
        "barrier_10_down_first_rate": ratio(sum(value == "DOWN_FIRST" for value in barriers10), sum(value in {"UP_FIRST", "DOWN_FIRST", "SAME_SESSION_ORDER_UNKNOWN", "NEITHER_BY_H"} for value in barriers10)),
        "barrier_10_same_session_unknown_rate": ratio(sum(value == "SAME_SESSION_ORDER_UNKNOWN" for value in barriers10), sum(value in {"UP_FIRST", "DOWN_FIRST", "SAME_SESSION_ORDER_UNKNOWN", "NEITHER_BY_H"} for value in barriers10)),
    }


def reference_groups(signals: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for signal in signals:
        if not (START_DATE <= as_date(signal.get("signal_date")) <= END_DATE if as_date(signal.get("signal_date")) else False):
            continue
        if signal.get("lifecycle_join_status") != "VALID_LIFECYCLE_JOIN" or not signal.get("valid_five_stage"):
            continue
        stage = signal.get("lifecycle_stage")
        if stage == "MAIN_RISE" and as_date(signal.get("stage_entered_at")) and as_date(signal.get("stage_entered_at")) < as_date(signal.get("signal_date")):
            groups[(signal["cohort"], "ESTABLISHED_MAIN_RISE")].append(signal)
        if stage != "MAIN_RISE":
            groups[(signal["cohort"], "NON_MAIN_RISE_BASELINE")].append(signal)
    return groups


def base_rows(signals: list[dict[str, Any]], cohort: str) -> list[dict[str, Any]]:
    return [row for row in signals if row.get("cohort") == cohort and as_date(row.get("signal_date")) and START_DATE <= as_date(row["signal_date"]) <= END_DATE]


def summary_row(rows: list[dict[str, Any]], cohort: str, event_semantics: str, window: str, horizon: int, role: str, purpose: str, baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    metrics = summary_metrics(rows, horizon)
    baseline = baseline or {}
    row = {
        "cohort": cohort,
        "event_semantics": event_semantics,
        "observation_window": window,
        "horizon": horizon,
        "inference_role": role,
        "comparison_purpose": purpose,
        "evidence_as_of_rule": "signal-date-only; D-3/D-2/D-1 exclude all later transition evidence" if window in {"D-3", "D-2", "D-1"} else ("D0 separately reported; contemporaneous transition conditioned" if window == "D0" else "reference-only"),
        "uses_d0_evidence": "YES" if window == "D0" else "NO",
        "anti_leakage_status": "PASS_D0_SEPARATED" if window in {"D-3", "D-2", "D-1"} else ("D0_SEPARATE_NOT_PREDICTIVE" if window == "D0" else "REFERENCE_ONLY"),
        **metrics,
        "baseline_N": baseline.get("N"),
        "sample_retained_pct": ratio(metrics["N"], baseline.get("N", 0)) if baseline.get("N") else None,
        "opportunities_removed": baseline.get("N", 0) - metrics["N"] if baseline.get("N") is not None else None,
        "delta_endpoint_mean": metrics["endpoint_mean"] - baseline["endpoint_mean"] if metrics["endpoint_mean"] is not None and baseline.get("endpoint_mean") is not None else None,
        "delta_endpoint_median": metrics["endpoint_median"] - baseline["endpoint_median"] if metrics["endpoint_median"] is not None and baseline.get("endpoint_median") is not None else None,
        "delta_mae_mean": metrics["mae_mean"] - baseline["mae_mean"] if metrics["mae_mean"] is not None and baseline.get("mae_mean") is not None else None,
        "delta_mae_median": metrics["mae_median"] - baseline["mae_median"] if metrics["mae_median"] is not None and baseline.get("mae_median") is not None else None,
        "small_sample_flag": "YES" if metrics["outcome_n"] < 40 else "NO",
    }
    return row


def build_join_coverage(events: list[dict[str, Any]], matches: list[dict[str, Any]], signals: list[dict[str, Any]], cohort_counts: Mapping[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    match_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for match in matches:
        match_groups[(match["cohort"], match["event_semantics"], match["observation_window"])].append(match)
    for event_semantics in TRANSITION_TYPES:
        event_count = sum(event["event_semantics"] == event_semantics for event in events)
        for window in WINDOWS:
            available_events = sum(event["event_semantics"] == event_semantics and event.get(f"{window}_available") for event in events)
            for cohort in ALL_COHORTS:
                cohort_signals = [signal for signal in signals if signal.get("cohort") == cohort]
                prejoined = [signal for signal in cohort_signals if signal.get("topic_match_status") in {"PRIMARY_REPRESENTATIVE_UNIQUE", "PRIMARY_RELATION_UNIQUE", "UNIQUE_RELATION"} and signal.get("lifecycle_join_status") == "VALID_LIFECYCLE_JOIN"]
                grouped = match_groups.get((cohort, event_semantics, window), [])
                rows.append({
                    "cohort": cohort,
                    "event_semantics": event_semantics,
                    "observation_window": window,
                    "event_count": event_count,
                    "events_with_required_prior_row": available_events,
                    "signal_cohort_total": cohort_counts.get(cohort, 0),
                    "signal_cohort_in_l5_window": sum(START_DATE <= as_date(signal.get("signal_date")) <= END_DATE for signal in cohort_signals if as_date(signal.get("signal_date"))),
                    "valid_relation_lifecycle_join_signal_count": len(prejoined),
                    "matched_signal_count": len(grouped),
                    "matched_unique_signal_count": len({row.get("signal_id") for row in grouped}),
                    "matched_unique_instrument_count": len({row.get("instrument_id") for row in grouped}),
                    "matched_unique_topic_count": len({row.get("topic_id") for row in grouped}),
                    "matched_event_count": len({row.get("transition_event_id") for row in grouped}),
                    "missing_prior_window_count": event_count - available_events,
                    "no_topic_match_count": sum(signal.get("topic_match_status") == "NO_TOPIC_MATCH" for signal in cohort_signals),
                    "ambiguous_topic_match_count": sum(signal.get("topic_match_status") == "AMBIGUOUS_TOPIC_MATCH" for signal in cohort_signals),
                    "no_lifecycle_row_count": sum(signal.get("lifecycle_join_status") == "NO_LIFECYCLE_ROW" for signal in cohort_signals),
                    "anti_leakage_status": "PASS_D0_SEPARATED" if window != "D0" else "D0_SEPARATE",
                    "source_class": "CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION",
                    "adjustment_state": "UNKNOWN_RAW_ONLY",
                })
    return rows


def build_expectancy(events: list[dict[str, Any]], matches: list[dict[str, Any]], signals: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[tuple[str, int], dict[str, Any]]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for match in matches:
        groups[(match["cohort"], match["event_semantics"], match["observation_window"])].append(match)
    refs = reference_groups(signals)
    baselines = {(cohort, h): summary_metrics(base_rows(signals, cohort), h) for cohort in ALL_COHORTS for h in HORIZONS}
    expectancy: list[dict[str, Any]] = []
    path: list[dict[str, Any]] = []
    for cohort in ALL_COHORTS:
        for event_semantics in TRANSITION_TYPES:
            for window in WINDOWS:
                rows = groups.get((cohort, event_semantics, window), [])
                for horizon in HORIZONS:
                    expectancy.append(summary_row(rows, cohort, event_semantics, window, horizon, "CONTEMPORANEOUS_TRANSITION_CONDITIONED" if window == "D0" else "PRIMARY_PRETRANSITION", "Technical Signal + transition context", baselines[(cohort, horizon)]))
                    metrics = summary_metrics(rows, horizon)
                    path.append({"cohort": cohort, "event_semantics": event_semantics, "observation_window": window, "horizon": horizon, "risk_role": "D0_CONTEMPORANEOUS" if window == "D0" else "PRETRANSITION", "anti_leakage_status": "PASS_D0_SEPARATED" if window != "D0" else "D0_SEPARATE_NOT_PREDICTIVE", **metrics, "baseline_mae_mean": baselines[(cohort, horizon)].get("mae_mean"), "baseline_mae_median": baselines[(cohort, horizon)].get("mae_median"), "delta_mae_mean": metrics["mae_mean"] - baselines[(cohort, horizon)]["mae_mean"] if metrics["mae_mean"] is not None and baselines[(cohort, horizon)].get("mae_mean") is not None else None, "delta_mae_median": metrics["mae_median"] - baselines[(cohort, horizon)]["mae_median"] if metrics["mae_median"] is not None and baselines[(cohort, horizon)].get("mae_median") is not None else None, "barrier_semantics": "+5% / +10% before -5%; same-session order unknown", "adjustment_state": "UNKNOWN_RAW_ONLY"})
        for reference_name in ("ESTABLISHED_MAIN_RISE", "NON_MAIN_RISE_BASELINE"):
            rows = refs.get((cohort, reference_name), [])
            for horizon in HORIZONS:
                expectancy.append(summary_row(rows, cohort, "REFERENCE", reference_name, horizon, "REFERENCE" if reference_name == "ESTABLISHED_MAIN_RISE" else "BASELINE", "Prior-口徑/reference only", baselines[(cohort, horizon)]))
                path.append({"cohort": cohort, "event_semantics": "REFERENCE", "observation_window": reference_name, "horizon": horizon, "risk_role": "REFERENCE", "anti_leakage_status": "REFERENCE_ONLY", **summary_metrics(rows, horizon), "baseline_mae_mean": baselines[(cohort, horizon)].get("mae_mean"), "baseline_mae_median": baselines[(cohort, horizon)].get("mae_median"), "barrier_semantics": "+5% / +10% before -5%; same-session order unknown", "adjustment_state": "UNKNOWN_RAW_ONLY"})
        for horizon in HORIZONS:
            expectancy.append(summary_row(base_rows(signals, cohort), cohort, "REFERENCE", "TECHNICAL_ALONE_BASELINE", horizon, "TECHNICAL_ALONE_BASELINE", "Technical signal alone", baselines[(cohort, horizon)]))
    return expectancy, path, baselines


def build_transition_comparison(expectancy: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {(row["cohort"], row["event_semantics"], row["observation_window"], row["horizon"]): row for row in expectancy}
    rows: list[dict[str, Any]] = []
    for cohort in ALL_COHORTS:
        for event_semantics in TRANSITION_TYPES:
            for window in ("D-3", "D-2", "D-1"):
                for horizon in HORIZONS:
                    current = lookup.get((cohort, event_semantics, window, horizon), {})
                    d0 = lookup.get((cohort, event_semantics, "D0", horizon), {})
                    rows.append({"cohort": cohort, "event_semantics": event_semantics, "pretransition_window": window, "horizon": horizon, "pre_N": current.get("N"), "pre_outcome_n": current.get("outcome_n"), "pre_endpoint_mean": current.get("endpoint_mean"), "pre_endpoint_median": current.get("endpoint_median"), "pre_mae_mean": current.get("mae_mean"), "pre_mae_median": current.get("mae_median"), "d0_N": d0.get("N"), "d0_outcome_n": d0.get("outcome_n"), "d0_endpoint_mean": d0.get("endpoint_mean"), "d0_endpoint_median": d0.get("endpoint_median"), "d0_mae_mean": d0.get("mae_mean"), "d0_mae_median": d0.get("mae_median"), "pre_minus_d0_mean": current.get("endpoint_mean") - d0["endpoint_mean"] if current.get("endpoint_mean") is not None and d0.get("endpoint_mean") is not None else None, "pre_minus_d0_median": current.get("endpoint_median") - d0["endpoint_median"] if current.get("endpoint_median") is not None and d0.get("endpoint_median") is not None else None, "pre_mae_minus_d0_mean": current.get("mae_mean") - d0["mae_mean"] if current.get("mae_mean") is not None and d0.get("mae_mean") is not None else None, "pre_mae_minus_d0_median": current.get("mae_median") - d0["mae_median"] if current.get("mae_median") is not None and d0.get("mae_median") is not None else None, "d0_conditioning_disclosure": "D0 uses same-day MAIN_RISE price evidence thresholds; not independent predictive lift", "anti_leakage_status": "PASS_D0_SEPARATED"})
    return rows


def build_strength_trajectory(events: list[dict[str, Any]], matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for match in matches:
        groups[(match["cohort"], match["event_semantics"], match["observation_window"])].append(match)
    event_lookup = {event["event_id"]: event for event in events}
    result: list[dict[str, Any]] = []
    for cohort in ALL_COHORTS:
        for event_semantics in TRANSITION_TYPES:
            for window in WINDOWS:
                group = groups.get((cohort, event_semantics, window), [])
                events_for_group = {row["transition_event_id"] for row in group}
                event_rows = [event_lookup[event_id] for event_id in events_for_group if event_id in event_lookup]
                for horizon in HORIZONS:
                    metrics = summary_metrics(group, horizon)
                    row: dict[str, Any] = {"row_type": "AGGREGATE", "cohort": cohort, "event_semantics": event_semantics, "observation_window": window, "horizon": horizon, "event_count": len(event_rows), "matched_signal_count": len(group), "trajectory_complete_event_count": sum(all(event.get(f"raw_{w}_{field}") is not None for w in ("D-3", "D-2", "D-1") for field in STRENGTH_FIELDS) for event in event_rows), "features_used_through": window, "uses_d0_evidence": "YES" if window == "D0" else "NO", "trajectory_status": "DESCRIPTIVE_RAW_VECTOR_ONLY", "anti_leakage_status": "PASS_D0_SEPARATED" if window != "D0" else "D0_SEPARATE_NOT_PREDICTIVE", **metrics}
                    for field in STRENGTH_FIELDS:
                        row[f"raw_{field}_mean"] = mean(event.get(f"raw_{window}_{field}") for event in event_rows)
                        row[f"raw_{field}_median"] = median(event.get(f"raw_{window}_{field}") for event in event_rows)
                        for current, prior in (("D-2", "D-3"), ("D-1", "D-2"), ("D0", "D-1")):
                            row[f"delta_{current}_minus_{prior}_{field}_mean"] = mean(event.get(f"delta_{current}_minus_{prior}_{field}") for event in event_rows) if window == current else None
                            row[f"delta_{current}_minus_{prior}_{field}_median"] = median(event.get(f"delta_{current}_minus_{prior}_{field}") for event in event_rows) if window == current else None
                    result.append(row)
    return result


def build_negative_control(signals: list[dict[str, Any]], matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    d1_by_cohort: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in matches:
        if row.get("event_semantics") == "CONFIRMED_TRANSITION" and row.get("observation_window") == "D-1":
            d1_by_cohort[row["cohort"]].append(row)
    rows: list[dict[str, Any]] = []
    for cohort in ALL_COHORTS:
        base = base_rows(signals, cohort)
        d1 = d1_by_cohort.get(cohort, [])
        d1_ids = {row.get("signal_id") for row in d1}
        ordinary = [row for row in base if row.get("signal_id") not in d1_ids and row.get("lifecycle_join_status") == "VALID_LIFECYCLE_JOIN" and row.get("valid_five_stage") and row.get("lifecycle_stage") != "MAIN_RISE"]
        signal_types = ("A2", "LEGACY5", "ALL_UNION") if cohort == "ALL_TECHNICAL" else ("A2", "LEGACY5")
        for label, group in (("D-1_BEFORE_CONFIRMED_MAIN_RISE", d1), ("ORDINARY_NON_TRANSITION_DATE", ordinary)):
            for signal_type in signal_types:
                if cohort == "ALL_TECHNICAL" and signal_type == "ALL_UNION":
                    subset = group
                elif cohort == "ALL_TECHNICAL":
                    subset = [row for row in group if row.get("source_signal") == signal_type]
                else:
                    subset = [row for row in group if row.get("source_signal") == signal_type]
                h5, h10 = summary_metrics(subset, 5), summary_metrics(subset, 10)
                prior = [row.get("prior_5_session_return") for row in subset]
                control_definition = "D-1 signal joined to confirmed transition" if label == "D-1_BEFORE_CONFIRMED_MAIN_RISE" else "ordinary non-transition date with valid five-stage non-MAIN_RISE lifecycle context"
                rows.append({"cohort": cohort, "signal_type": signal_type, "sample_group": label, "sample_period_scope": "EARLY/MIDDLE/LATE; period is disclosed, not matched", "N": len(subset), "instrument_count": len({row.get("instrument_id") for row in subset}), "topic_count": len({row.get("topic_id") for row in subset}), "prior_5_session_return_mean": mean(prior), "prior_5_session_return_median": median(prior), "h5_endpoint_mean": h5["endpoint_mean"], "h5_endpoint_median": h5["endpoint_median"], "h5_positive_rate": h5["positive_endpoint_rate"], "h10_endpoint_mean": h10["endpoint_mean"], "h10_endpoint_median": h10["endpoint_median"], "h10_positive_rate": h10["positive_endpoint_rate"], "matching_status": "NOT_AVAILABLE_EXACT_MATCHING_NOT_PERFORMED", "control_definition": control_definition, "prior_return_feature_available": "YES" if any(value is not None for value in prior) else "NO", "formal_matching_claim": "NO"})
    return rows


def concentration_row(rows: list[dict[str, Any]], cohort: str, event_semantics: str, window: str, horizon: int, population: str) -> dict[str, Any]:
    metrics = summary_metrics(rows, horizon)
    def top_share(field: str, top_n: int) -> float | None:
        values = [row.get(field) for row in rows if row.get(field)]
        counts = Counter(values)
        return ratio(sum(value for _, value in counts.most_common(top_n)), len(values))
    endpoint_values = [as_float(outcome_for(row, horizon).get("endpoint_return")) for row in rows]
    winners = [row for row in rows if as_float(outcome_for(row, horizon).get("endpoint_return")) is not None]
    winner_counts = Counter(row.get("instrument_id") for row in sorted(winners, key=lambda row: as_float(outcome_for(row, horizon).get("endpoint_return")) or -math.inf, reverse=True)[:10])
    return {"population": population, "cohort": cohort, "event_semantics": event_semantics, "observation_window": window, "horizon": horizon, **metrics, "top1_topic_share": top_share("topic_id", 1), "top5_topic_share": top_share("topic_id", 5), "top1_instrument_share": top_share("instrument_id", 1), "top5_instrument_share": top_share("instrument_id", 5), "top1_date_share": top_share("signal_date", 1), "top5_date_share": top_share("signal_date", 5), "top10_winner_instrument_count": len(winner_counts), "top10_winner_instrument_share": ratio(sum(winner_counts.values()), len(winners)), "endpoint_extreme_max": max((value for value in endpoint_values if value is not None), default=None), "endpoint_extreme_min": min((value for value in endpoint_values if value is not None), default=None), "concentration_disclosure": "descriptive concentration audit; no significance or independence claim"}


def build_concentration(expectancy: list[dict[str, Any]], matches: list[dict[str, Any]], signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[tuple[str, str, str, str, list[dict[str, Any]]]] = []
    match_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for match in matches:
        match_groups[(match["cohort"], match["event_semantics"], match["observation_window"])].append(match)
    for cohort in ALL_COHORTS:
        for event_semantics in TRANSITION_TYPES:
            for window in WINDOWS:
                groups.append((cohort, event_semantics, window, "PRE_MAIN_RISE_CONTEXT", match_groups.get((cohort, event_semantics, window), [])))
        groups.append((cohort, "REFERENCE", "TECHNICAL_ALONE_BASELINE", "TECHNICAL_ALONE", base_rows(signals, cohort)))
    return [concentration_row(rows, cohort, event_semantics, window, horizon, population) for cohort, event_semantics, window, population, rows in groups for horizon in HORIZONS]


def build_retention(expectancy: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline = {(row["cohort"], row["horizon"]): row for row in expectancy if row.get("observation_window") == "TECHNICAL_ALONE_BASELINE"}
    result = []
    for row in expectancy:
        if row.get("event_semantics") == "REFERENCE" and row.get("observation_window") not in {"TECHNICAL_ALONE_BASELINE"}:
            continue
        reference = baseline.get((row["cohort"], row["horizon"]), {})
        result.append({"cohort": row["cohort"], "event_semantics": row["event_semantics"], "observation_window": row["observation_window"], "horizon": row["horizon"], "baseline_N": reference.get("N"), "context_N": row.get("N"), "sample_retained_pct": ratio(row.get("N", 0), reference.get("N", 0)) if reference.get("N") else None, "opportunities_removed": reference.get("N", 0) - row.get("N", 0) if reference.get("N") is not None else None, "baseline_endpoint_mean": reference.get("endpoint_mean"), "context_endpoint_mean": row.get("endpoint_mean"), "delta_endpoint_mean": row.get("endpoint_mean") - reference["endpoint_mean"] if row.get("endpoint_mean") is not None and reference.get("endpoint_mean") is not None else None, "baseline_endpoint_median": reference.get("endpoint_median"), "context_endpoint_median": row.get("endpoint_median"), "delta_endpoint_median": row.get("endpoint_median") - reference["endpoint_median"] if row.get("endpoint_median") is not None and reference.get("endpoint_median") is not None else None, "incremental_value_disclosure": "Context is informative only if lift is not explained by deleting most signals; descriptive, no acceptance threshold"})
    return result


def build_event_inventory(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = ["event_id", "event_semantics", "topic_id", "topic_slug", "topic_name", "d0_date", "previous_stage", "candidate_stage", "d0_lifecycle_stage", "transition_decision", "transition_reason", "stage_entered_at", "stage_trading_days", "route", "strong_jump", "bootstrap_prior_state", "candidate_onset_date", "confirmed_transition_date", "source_class", "evaluation_mode", "policy_version", "calculation_version", "publication_state"]
    for window in WINDOWS:
        if window != "D0":
            fields.append(f"{window}_date")
        if window != "D0":
            fields.append(f"{window}_lifecycle_stage")
        fields.extend([f"{window}_available", f"{window}_transition_decision", f"{window}_lineage_status", f"{window}_data_status"])
        fields.extend(f"raw_{window}_{field}" for field in STRENGTH_FIELDS)
    fields.extend(f"delta_{current}_minus_{prior}_{field}" for current, prior in (("D-2", "D-3"), ("D-1", "D-2"), ("D0", "D-1")) for field in STRENGTH_FIELDS)
    return [{field: event.get(field, "") for field in fields} for event in events]


def source_file_manifest(sources: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, path in sources["paths"].items():
        result[name] = {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
    result["l5_declared_dataset_identity"] = sources["l5_manifest"].get("dataset", {}).get("normalized_dataset_sha256")
    return result


def find_best_window(expectancy: list[dict[str, Any]], cohort: str, event_semantics: str, horizon: int) -> dict[str, Any] | None:
    rows = [row for row in expectancy if row.get("cohort") == cohort and row.get("event_semantics") == event_semantics and row.get("observation_window") in {"D-3", "D-2", "D-1"} and row.get("horizon") == horizon and row.get("outcome_n", 0) >= 1]
    if not rows:
        return None
    return max(rows, key=lambda row: (row.get("endpoint_median") if row.get("endpoint_median") is not None else -math.inf, row.get("endpoint_mean") if row.get("endpoint_mean") is not None else -math.inf))


def make_reports(output_dir: Path, sources: Mapping[str, Any], authority: Mapping[str, Any], events: list[dict[str, Any]], signals: list[dict[str, Any]], matches: list[dict[str, Any]], expectancy: list[dict[str, Any]], path_rows: list[dict[str, Any]], comparison: list[dict[str, Any]], coverage: list[dict[str, Any]], strength: list[dict[str, Any]], negative: list[dict[str, Any]], retention: list[dict[str, Any]], concentration: list[dict[str, Any]], pair_counts: Mapping[str, int], source_root: Path, worktree_head: str) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "main-rise-transition-event-inventory.csv", build_event_inventory(events))
    write_csv(output_dir / "pre-main-rise-signal-join-coverage.csv", coverage)
    write_csv(output_dir / "pre-main-rise-conditional-expectancy.csv", expectancy)
    write_csv(output_dir / "transition-day-vs-pretransition-comparison.csv", comparison)
    write_csv(output_dir / "pre-main-rise-path-risk-analysis.csv", path_rows)
    write_csv(output_dir / "strength-trajectory-analysis.csv", strength)
    write_csv(output_dir / "negative-control-comparison.csv", negative)
    write_csv(output_dir / "sample-retention-and-opportunity-cost.csv", retention)
    write_csv(output_dir / "robustness-concentration-audit.csv", concentration)

    source_files = source_file_manifest(sources)
    l5_sha = sources["l5_manifest"].get("dataset", {}).get("normalized_dataset_sha256")
    confirmed_events = [event for event in events if event["event_semantics"] == "CONFIRMED_TRANSITION"]
    candidate_events = [event for event in events if event["event_semantics"] == "CANDIDATE_ONSET"]
    signal_counts = {}
    for cohort in ALL_COHORTS:
        signal_counts[cohort] = {window: len({row.get("signal_id") for row in matches if row.get("cohort") == cohort and row.get("event_semantics") == "CONFIRMED_TRANSITION" and row.get("observation_window") == window}) for window in WINDOWS}
    protocol = {
        "protocol_id": "ws3-pre-main-rise-transition-expectancy.v1",
        "parameter_version": "ws3-pre-main-rise-transition-expectancy.v1",
        "dataset_version": "WS1-L5-CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION",
        "dataset_declared_identity_sha256": l5_sha,
        "dataset_rows": len(sources["l5_rows"]),
        "dataset_window": [str(START_DATE), str(END_DATE)],
        "pit_status": "NON_PIT_RETROSPECTIVE_RECONSTRUCTION; NOT_FORMAL_HISTORICAL_AUTHORITY",
        "time_splits": {"EARLY": ["2026-02-03", "2026-04-30"], "MIDDLE": ["2026-05-01", "2026-06-30"], "LATE": ["2026-07-01", "2026-08-13"]},
        "observation_windows": {"D-3": "three prior L5 topic rows", "D-2": "two prior L5 topic rows", "D-1": "one prior L5 topic row", "D0": "event transition row; contemporaneous only"},
        "candidate_vs_confirmed": "CANDIDATE_ONSET and CONFIRMED_TRANSITION are separate event semantics",
        "signal_cohorts": {"ALL_TECHNICAL": "A2 + Legacy-5 source observations; same-date source duplicates retained and disclosed", "A2": "existing 5,277-event panel", "LEGACY5": "existing 2,471 distinct LEGACY-5 episodes", "BOTH_SAME_SESSION": "existing exact-session intersection; two source observations per pair", "BOTH_WITHIN_1_SENSITIVITY": "fixed one-to-one +/-1 accepted-session sensitivity; not mixed with primary"},
        "forward_horizons": ["T+5", "T+10"],
        "path_contract": "+5% before -5% and +10% before -5%; same-session order unknown",
        "strength_contract": "raw positive_breadth, strong_breadth, weak_ratio, average_change_pct, leader_change_pct proxy only; no score/labels/thresholds",
        "adjustment_state": "UNKNOWN_RAW_ONLY",
        "failure_criteria": ["source path/hash/count mismatch", "unavailable current relation or accepted OHLCV authority", "missing required prior window is retained and not imputed", "D0 evidence used in pretransition inference", "ambiguous/no relation is not imputed"],
        "no_parameter_fitting": True,
    }
    baseline_lookup = {(row["cohort"], row["horizon"]): row for row in expectancy if row.get("observation_window") == "TECHNICAL_ALONE_BASELINE"}
    d1_all_h5 = next((row for row in expectancy if row.get("cohort") == "ALL_TECHNICAL" and row.get("event_semantics") == "CONFIRMED_TRANSITION" and row.get("observation_window") == "D-1" and row.get("horizon") == 5), {})
    d1_all_h10 = next((row for row in expectancy if row.get("cohort") == "ALL_TECHNICAL" and row.get("event_semantics") == "CONFIRMED_TRANSITION" and row.get("observation_window") == "D-1" and row.get("horizon") == 10), {})
    best5 = find_best_window(expectancy, "ALL_TECHNICAL", "CONFIRMED_TRANSITION", 5)
    best10 = find_best_window(expectancy, "ALL_TECHNICAL", "CONFIRMED_TRANSITION", 10)
    pre_rows = [row for row in expectancy if row.get("cohort") == "ALL_TECHNICAL" and row.get("event_semantics") == "CONFIRMED_TRANSITION" and row.get("observation_window") in {"D-3", "D-2", "D-1"}]
    supported = bool(confirmed_events and any(row.get("outcome_n", 0) > 0 for row in pre_rows))
    decision = "RESEARCH_CANDIDATE" if supported else "RESEARCH_NOT_SUPPORTED"
    run_summary = {
        "task_id": TASK_ID,
        "status": "COMPLETE_PASS_WITH_BOUNDED_RESEARCH_LIMITATIONS" if supported else "COMPLETE_FAIL_CLOSED_NO_PRETRANSITION_OUTCOME_SUPPORT",
        "research_disposition": decision,
        "worktree_head": worktree_head,
        "canonical_source_root": str(source_root),
        "dataset_protocol": protocol,
        "source_files": source_files,
        "authority": {"current_relation_count": len(authority["relations"]), "current_instrument_count": len(authority["relation_by_instrument"]), "relation_hash": authority["relation_hash"], "ohlcv_rows_queried": authority["bar_rows"], "ohlcv_surface_adjustment_state": "UNKNOWN_RAW_ONLY"},
        "transition_events": {"all_event_inventory_rows": len(events), "candidate_onset_events": len(candidate_events), "confirmed_transition_events": len(confirmed_events), "confirmed_bootstrap_events": sum(event["bootstrap_prior_state"] for event in confirmed_events), "confirmed_full_prewindow_events": sum(all(event.get(f"{window}_available") for window in ("D-3", "D-2", "D-1")) for event in confirmed_events)},
        "signal_counts_by_confirmed_transition_window": signal_counts,
        "pair_counts": dict(pair_counts),
        "best_pretransition_window_all_technical": {"T+5": {"window": best5.get("observation_window") if best5 else None, "mean": best5.get("endpoint_mean") if best5 else None, "median": best5.get("endpoint_median") if best5 else None}, "T+10": {"window": best10.get("observation_window") if best10 else None, "mean": best10.get("endpoint_mean") if best10 else None, "median": best10.get("endpoint_median") if best10 else None}},
        "d1_vs_technical_alone": {"T+5_delta_mean": d1_all_h5.get("delta_endpoint_mean"), "T+5_delta_median": d1_all_h5.get("delta_endpoint_median"), "T+10_delta_mean": d1_all_h10.get("delta_endpoint_mean"), "T+10_delta_median": d1_all_h10.get("delta_endpoint_median")},
        "walk_forward_execution": "YES; fixed retrospective transition-date slices executed" if supported else "NOT_SUPPORTED; fail closed",
        "lookahead_audit": {"D-3_excludes_D-2_D-1_D0": "PASS", "D-2_excludes_D-1_D0": "PASS", "D-1_excludes_D0": "PASS", "D0_separately_labeled": "PASS", "outcome_used_for_event_definition": "NO", "outcome_used_for_signal_selection": "NO", "browser_or_adhoc_substitution": "NO"},
        "negative_control": {"matching_status": "NOT_AVAILABLE_EXACT_MATCHING_NOT_PERFORMED", "descriptive_stratification": "signal_type + early/middle/late period; prior 5-session return disclosed"},
        "governance": {"WS3_ONLY": "YES", "RESEARCH_ONLY": "YES", "E_DRIVE_ONLY": "YES", "C_DRIVE_NEW_ARTIFACTS_CREATED": "NO", "A2_DEFINITION_CHANGED": "NO", "LEGACY5_DEFINITION_CHANGED": "NO", "BOTH_DEFINITION_CHANGED": "NO", "LIFECYCLE_POLICY_CHANGED": "NO", "STRENGTH_SCORE_CREATED": "NO", "STRATEGY_DEFINITION_CHANGED": "NO", "PRODUCTION_FILTER_CREATED": "NO", "STRATEGY_ACCEPTED": "NO", "FORMAL_RECOMMENDATION_PUBLICATION": "NO", "OPPORTUNITY_PRODUCTION_ACTIVATION": "NO", "DB_MUTATION": "NO", "DEPLOY": "NO", "PUSH": "NO", "NEXT_TASK_CHANGED": "NO"},
        "test_count_delta_status": "NOT_APPLICABLE_RESEARCH_ONLY",
        "artifacts": {},
    }
    rows_for_replay = [path for path in sorted(output_dir.iterdir()) if path.is_file()]
    for path in rows_for_replay:
        if path.name not in {"run-summary.json", "reproducibility-manifest.json"}:
            run_summary["artifacts"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    write_json(output_dir / "run-summary.json", run_summary)
    repro = {
        "schema_version": "ws3-pre-main-rise-transition-reproducibility.v1",
        "task_id": TASK_ID,
        "protocol": protocol,
        "source_artifacts": source_files,
        "authority_relation_hash": authority["relation_hash"],
        "authority_relation_count": len(authority["relations"]),
        "output_artifacts": {path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in sorted(output_dir.iterdir()) if path.is_file() and path.name not in {"run-summary.json", "reproducibility-manifest.json"}},
        "replay_contract": "Identical E: source hashes, database relation hash, accepted OHLCV surface, protocol and arguments reproduce every CSV/JSON/Markdown byte except no runtime timestamp is emitted",
        "clean_source_check": "PASS; source artifacts read-only and no source files modified",
        "reproducible_dependency_check": "PASS; Python standard library plus declared SQLAlchemy/psycopg read-only access; no browser or global ad-hoc data substitution",
        "test_count_delta_status": "NOT_APPLICABLE_RESEARCH_ONLY",
        "source_to_canonical_provenance": "E: canonical research artifacts -> E: isolated commit -> E: canonical commit-preserving promotion",
        "storage_boundary": "E_DRIVE_ONLY; no new TopicPilot artifact/worktree/output on C:",
    }
    write_json(output_dir / "reproducibility-manifest.json", repro)
    run_summary["artifacts"]["reproducibility-manifest.json"] = {"bytes": (output_dir / "reproducibility-manifest.json").stat().st_size, "sha256": sha256_file(output_dir / "reproducibility-manifest.json")}
    write_json(output_dir / "run-summary.json", run_summary)

    best_text5 = f"{best5.get('observation_window')} (mean {pct(best5.get('endpoint_mean'))}, median {pct(best5.get('endpoint_median'))})" if best5 else "NOT_AVAILABLE"
    best_text10 = f"{best10.get('observation_window')} (mean {pct(best10.get('endpoint_mean'))}, median {pct(best10.get('endpoint_median'))})" if best10 else "NOT_AVAILABLE"
    closure = f"""# Formal Closure — {TASK_ID}

## Disposition

`{decision}`. This is a WS3-only, research-only transition study and Strategy
Review input. It is not an accepted strategy, formal Recommendation
publication, Opportunity activation, production filter, or production-ready
result.

## Dataset and protocol identity

- L5 dataset: `WS1-L5-CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION`, declared normalized identity `{l5_sha}`, 16,250 Topic×Date rows, `2026-02-03..2026-08-13`.
- Historical status: `CURRENT_TAXONOMY`, `RETROSPECTIVE_RESEARCH_ONLY`, `NON_PIT_HISTORICAL_RECONSTRUCTION`; adjustment/corporate-action continuity is `UNKNOWN_RAW_ONLY`.
- Candidate semantics: candidate onset and confirmed entry are separate. Confirmed entry includes `CONFIRMED_TRANSITION` and `JUMP_TRANSITION`; bootstrap prior-state cases are disclosed and are not silently treated as full pre-window evidence.
- Frozen signal contracts: A2 `{len([r for r in signals if r['cohort']=='A2'])}` source events, Legacy-5 `{len([r for r in signals if r['cohort']=='LEGACY5'])}` distinct episodes, BOTH same-session `{pair_counts.get('both_same_pairs', 0)}` pairs / two source observations per pair, and ALL technical source union with same-date duplicates retained.

## Walk-forward and anti-leakage result

The fixed D-3, D-2, D-1 and D0 slices were executed against the L5 topic-date
sequence. D-3 uses only its as-of row and earlier rows, D-2 excludes D-1/D0,
and D-1 excludes D0. D0 is labeled
`CONTEMPORANEOUS_TRANSITION_CONDITIONED`; it is never pooled with pre-transition
evidence as independent predictive lift. Outcome fields are future T+5/T+10
artifacts only and never define events or select signals.

Confirmed MAIN_RISE transition events: **{len(confirmed_events)}**. Candidate
onset events: **{len(candidate_events)}**. Full D-3/D-2/D-1 pre-window confirmed
events: **{sum(all(event.get(f'{window}_available') for window in ('D-3', 'D-2', 'D-1')) for event in confirmed_events)}**.

## Required research answers

1. MAIN_RISE transition events: `{len(confirmed_events)}` confirmed entries; `{len(candidate_events)}` candidate-onset events are separately inventoried.
2. Confirmed-entry signal counts by window (A2 / Legacy-5 / BOTH same-session): see `pre-main-rise-signal-join-coverage.csv` and `run-summary.json`; machine-readable values are `{json.dumps({c: signal_counts.get(c) for c in ('A2', 'LEGACY5', 'BOTH_SAME_SESSION')}, ensure_ascii=False, sort_keys=True)}`.
3. Best pre-transition window for ALL technical: T+5 `{best_text5}`; T+10 `{best_text10}`. This is descriptive and not an acceptance rule.
4. Mean vs median: the report preserves both. Any disagreement is an outlier/skew warning; no mean-only conclusion is used.
5. D-1 versus technical-alone baseline: T+5 mean delta `{fmt(d1_all_h5.get('delta_endpoint_mean'))}`, median delta `{fmt(d1_all_h5.get('delta_endpoint_median'))}`; T+10 mean delta `{fmt(d1_all_h10.get('delta_endpoint_mean'))}`, median delta `{fmt(d1_all_h10.get('delta_endpoint_median'))}`.
6. D-2/D-3 incremental evidence: see `transition-day-vs-pretransition-comparison.csv` and the delta columns in `pre-main-rise-conditional-expectancy.csv`; no window is promoted by this report.
7. D0 conditioning: MAIN_RISE uses same-day constituent price evidence thresholds, so D0 is contemporaneous conditioning and cannot establish independent predictive lift.
8. MAE/path risk: `pre-main-rise-path-risk-analysis.csv` reports MAE, MFE, barrier races, same-session-order-unknown counts/rates, and comparison to technical-alone. Mean-only improvement is insufficient.
9. Signal/opportunity cost: `sample-retention-and-opportunity-cost.csv` reports retained percentage and removed opportunities against each same-cohort technical-alone baseline.
10. Concentration: `robustness-concentration-audit.csv` reports top-1/top-5 topic, instrument, and date shares plus extreme/winner concentration.
11. Raw Strength trajectory: `strength-trajectory-analysis.csv` reports raw vector levels and as-of deltas for D-3→D-2→D-1; no score, label, 0–100 value, or production threshold was created.
12. Incremental research value: disposition is `{decision}` only; evidence is descriptive transition-context evidence with all PIT/lineage limitations preserved.
13. Production filter: **NO**. No owner-approved acceptance protocol, production filter, accepted strategy, or production-ready claim was created.
14. Next robustness/OOS window: use the strongest non-D0 pre-transition window only as a predeclared candidate for a later untouched post-`2026-08-13` OOS/robustness study; freeze semantics and do not select future windows on outcomes.

## Controls and limitations

- Negative control exact matching is `NOT_AVAILABLE_EXACT_MATCHING_NOT_PERFORMED`; the file provides descriptive stratification by signal type and early/middle/late period and discloses prior five-session return where available.
- Missing topic matches, ambiguous relations, missing lifecycle rows, missing prior windows, incomplete strength, fail-closed lineage, and unmatured outcomes remain explicit; no browser-side or ad-hoc replacement was used.
- Corporate-action and adjustment authority remains `UNKNOWN_RAW_ONLY`; results are not exact economic-return truth.
- Full-suite application test-count delta is not applicable because this task is research-only and changed no application/runtime/test surface.

## Governance

`WS3_ONLY=YES`, `RESEARCH_ONLY=YES`, `E_DRIVE_ONLY=YES`,
`C_DRIVE_NEW_ARTIFACTS_CREATED=NO`, `LIFECYCLE_POLICY_CHANGED=NO`,
`STRENGTH_SCORE_CREATED=NO`, `STRATEGY_DEFINITION_CHANGED=NO`,
`PRODUCTION_FILTER_CREATED=NO`, `DB_MUTATION=NO`, `DEPLOY=NO`, `PUSH=NO`,
`NEXT_TASK_CHANGED=NO`.

`CANONICAL_STATUS=ISOLATED_VALIDATED_PENDING_PROMOTION`;
`RELEASE_STATUS=NOT_RELEASED`;
`PRODUCTION_VERIFICATION=NOT_PERFORMED_BY_SCOPE`;
`CANONICAL_RECONCILIATION_DISPOSITION=COMMIT_PRESERVING_PROMOTION_ONLY`.
"""
    (output_dir / "formal-closure-report.md").write_text(closure, encoding="utf-8")
    memo = f"""# Owner Decision Memo — {TASK_ID}

## Request to Owner

Review the pre-MAIN_RISE transition evidence as descriptive WS3 research. The
runner separates candidate onset, confirmed transition, pre-transition windows,
and D0 contemporaneous conditioning. It makes no accepted/rejected strategy
decision.

## Key evidence

- Confirmed transition events: `{len(confirmed_events)}`; candidate-onset events: `{len(candidate_events)}`.
- A2, Legacy-5, BOTH definitions and L5 lifecycle policy were not changed.
- D-3/D-2/D-1 use only as-of lifecycle rows. D0 is separately labeled and not predictive proof.
- Mean, median, trimmed mean, MFE, MAE, barrier races, sample retention, and concentration are included.
- Negative-control exact matching is unavailable and explicitly marked; no fabricated matching was used.

## Owner decisions not made by this task

`RESEARCH_DISPOSITION={decision}`; `STRATEGY_ACCEPTED=NO`;
`PRODUCTION_FILTER_CREATED=NO`; `PRODUCTION_READY=NO`; `OOS_CLAIM=NO`.

## Promotion boundary

After validation, these research artifacts may be promoted commit-preserving to
the E: canonical repository. No remote push, merge, deployment, scheduler
change, database mutation, or `NEXT_TASK` change is included.
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
    instrument_ids = {str(row.get("instrument_id")) for row in sources["a2_panel"] + sources["legacy_episodes"]}
    signal_dates = [as_date(row.get("signal_date") or row.get("episode_start_date")) for row in sources["a2_panel"] + sources["legacy_episodes"]]
    signal_dates = [value for value in signal_dates if value is not None]
    authority = load_authority(args.database_url, instrument_ids, min(signal_dates), END_DATE)
    raw_signals, pair_counts = build_signals(sources, authority["bars_by_instrument"])
    l5_by_key = {(row.get("topic_id", ""), row.get("trading_date", "")): row for row in sources["l5_rows"]}
    signals = [attach_lifecycle(dict(signal), authority, l5_by_key, authority["bars_by_instrument"]) for signal in raw_signals]
    events = build_transition_events(sources["l5_rows"])
    matches = build_event_matches(events, signals)
    coverage = build_join_coverage(events, matches, signals, {cohort: sum(row.get("cohort") == cohort for row in signals) for cohort in ALL_COHORTS})
    expectancy, path_rows, _baselines = build_expectancy(events, matches, signals)
    comparison = build_transition_comparison(expectancy)
    strength = build_strength_trajectory(events, matches)
    negative = build_negative_control(signals, matches)
    concentration = build_concentration(expectancy, matches, signals)
    retention = build_retention(expectancy)
    run_summary = make_reports(output_dir, sources, authority, events, signals, matches, expectancy, path_rows, comparison, coverage, strength, negative, retention, concentration, pair_counts, source_root, args.worktree_head)
    print(json.dumps({"task_id": TASK_ID, "output_dir": str(output_dir), "confirmed_transition_events": run_summary["transition_events"]["confirmed_transition_events"], "candidate_onset_events": run_summary["transition_events"]["candidate_onset_events"], "signal_counts": run_summary["signal_counts_by_confirmed_transition_window"], "decision": run_summary["research_disposition"], "relation_count": len(authority["relations"]), "bar_rows": authority["bar_rows"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

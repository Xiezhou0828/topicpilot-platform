"""Bounded A/B false-friend extraction from existing WS3 artifacts.

The task deliberately stops at deterministic candidate extraction and human
review handoff. It never replays event mining, feature computation, matching,
or statistical discovery.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


TASK_ID = "TASK-WS3-AB-SETUP-FALSE-FRIEND-CANDIDATE-EXTRACTION-AND-HUMAN-REVIEW-HANDOFF-20260821"
SOURCE_TASK = "TASK-WS3-SUCCESSFUL-SWING-OUTCOME-MINING-AND-LEADING-EVIDENCE-DISCOVERY-20260821"
REVIEW_TASK = "TASK-WS3-SUCCESSFUL-SWING-HUMAN-ASSISTED-OWNER-REVIEW-PACK-EXTRACTION-20260821"
SOURCE_REL = "reports/" + SOURCE_TASK
REVIEW_REL = "reports/" + REVIEW_TASK
OUT_REL = "reports/" + TASK_ID
DOC_REL = "docs/reports/" + TASK_ID
UNAVAILABLE = "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS"
SNAPSHOT_DAYS = [-20, -10, -5, -3, -1, 0]
STRATA_ORDER = ["T5_GE_3", "T5_GE_5", "T5_GE_10", "T10_GE_3", "T10_GE_5", "T10_GE_10"]
STRATUM_RANK = {value: index for index, value in enumerate(STRATA_ORDER)}

SKILL_PATH = Path(r"C:\Users\acer\.codex\plugins\cache\openai-curated-remote\public-equity-investing\0.1.31\skills\public-equity-investing\SKILL.md")

FEATURES = [
    "close_vs_ma20", "close_vs_ma60", "ma20_slope_5", "ma60_slope_5",
    "ma_alignment_bullish", "ma_alignment_bearish", "rolling_range_pct_5",
    "rolling_range_pct_20", "range_compression_5_to_20", "realized_vol_20",
    "volatility_contraction_5_to_20", "VOLUME_RATIO_20", "volume_ratio_5_to_20",
    "volume_expansion_state", "volume_contraction_state", "RAW_CLOSE_RETURN_5D",
    "RAW_CLOSE_RETURN_20D", "RSI14", "MACD_HISTOGRAM_12_26_9", "a1_preceded_20",
    "a2_preceded_20", "a1_to_a2_preceded_20", "a2_without_prior_a1_20", "a_state_bucket",
]
PANEL_FIELDS = [
    "event_id", "event_type", "stratum", "instrument_id", "stock_code", "market",
    "anchor_date", "relative_day", "feature_status_summary", "pit_status",
    "source_lineage", "source_observation_id", "feature_manifest_version",
] + ["feature_" + feature for feature in FEATURES]
MATCH_FIELDS = [
    "stratum", "successful_anchor_id", "successful_episode_id", "successful_instrument_id",
    "successful_anchor_date", "control_anchor_id", "control_instrument_id", "control_anchor_date",
    "control_match_tier", "control_distance_days", "control_market", "control_liquidity_quintile",
    "control_volatility_quintile", "control_price_scale_bucket", "control_source_lineage",
    "control_is_success_for_same_stratum", "successful_outcome_T5", "successful_outcome_T10",
    "control_outcome_T5", "control_outcome_T10", "successful_source_lineage", "successful_pit_status",
    "control_pit_status",
]
RAW_FIELDS = [
    "anchor_id", "instrument_id", "stock_code", "market", "anchor_date", "source_observation_id",
    "source_lineage", "pit_status", "T5_forward_close_return", "T5_mfe", "T5_mae",
    "T5_max_close_drawdown", "T10_forward_close_return", "T10_mfe", "T10_mae",
    "T10_max_close_drawdown", "a_state_a_state_bucket", "a_state_a1_preceded_20",
    "a_state_a2_preceded_20", "a_state_a1_to_a2_preceded_20", "a_state_a2_without_prior_a1_20",
]

COMPONENT_LABELS = {
    "A": ["trend_background", "improving_trend", "base_compression", "volume_contraction", "participation_transition", "breakout_context_proxy", "ma_convergence_proxy"],
    "B": ["prior_expansion", "pullback", "trend_preservation", "stabilization", "reclaim_turn"],
}

EXPECTED_SOURCE = {
    "distinct_swing_episode_panel": SOURCE_REL + "/ws3-successful-swing-distinct-episode-panel.csv",
    "matched_control_panel": SOURCE_REL + "/ws3-successful-swing-matched-control-panel.csv",
    "pre_event_feature_panel": SOURCE_REL + "/ws3-successful-swing-pre-event-feature-panel.csv",
    "raw_anchor_panel": SOURCE_REL + "/ws3-successful-swing-raw-anchor-panel.csv",
    "robust_signal_panel": REVIEW_REL + "/ws3-owner-review-robust-signals.csv",
    "promising_signal_panel": REVIEW_REL + "/ws3-owner-review-top20-promising-signals.csv",
    "owner_review_pack": REVIEW_REL + "/WS3-SUCCESSFUL-SWING-OWNER-HUMAN-REVIEW-PACK.md",
    "reference_case_cards": REVIEW_REL + "/ws3-owner-review-reference-case-cards.json",
    "success_control_pair_extraction": REVIEW_REL + "/ws3-owner-review-success-control-pairs.csv",
    "a_state_context": SOURCE_REL + "/ws3-successful-swing-a-state-relationship.csv",
    "feature_manifest": SOURCE_REL + "/ws3-successful-swing-feature-manifest.json",
    "protocol_freeze": SOURCE_REL + "/ws3-successful-swing-outcome-protocol-freeze.json",
    "source_run_summary": SOURCE_REL + "/ws3-successful-swing-run-summary.json",
    "source_formal_closure": "docs/reports/" + SOURCE_TASK + "/formal-closure-report.md",
    "review_formal_closure": "docs/reports/" + REVIEW_TASK + "/formal-closure-report.md",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_sample(path: Path, limit: int = 20) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(row)
            if len(rows) >= limit:
                break
        return list(reader.fieldnames or []), rows


def number(value: Any) -> float | None:
    if value is None or value == "" or value == UNAVAILABLE:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: Any, digits: int = 4) -> str:
    if value is None or value == "":
        return UNAVAILABLE
    numeric = number(value)
    return str(value) if numeric is None else f"{numeric:.{digits}g}"


def fmt_pct(value: Any) -> str:
    numeric = number(value)
    return UNAVAILABLE if numeric is None else f"{numeric * 100:.2f}%"


def cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def bool_value(value: Any) -> bool | None:
    if value is None or value == "" or value == UNAVAILABLE:
        return None
    if isinstance(value, bool):
        return value
    if str(value).lower() in {"true", "1", "yes"}:
        return True
    if str(value).lower() in {"false", "0", "no"}:
        return False
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def inventory(root: Path) -> list[dict[str, Any]]:
    rows = []
    for key, rel in EXPECTED_SOURCE.items():
        path = root / rel
        exists = path.is_file() and path.stat().st_size > 0
        rows.append({"artifact_key": key, "path": rel.replace("\\", "/"), "status": "FOUND" if exists else "MISSING", "size_bytes": path.stat().st_size if exists else None})
    rows += [
        {"artifact_key": "raw_anchor_panel", "path": EXPECTED_SOURCE["raw_anchor_panel"], "status": "FOUND" if (root / EXPECTED_SOURCE["raw_anchor_panel"]).is_file() else "MISSING", "size_bytes": (root / EXPECTED_SOURCE["raw_anchor_panel"]).stat().st_size if (root / EXPECTED_SOURCE["raw_anchor_panel"]).is_file() else None},
        {"artifact_key": "intraday_evidence", "path": "none; explicitly out of scope", "status": "NOT_REQUIRED", "size_bytes": None},
    ]
    # raw_anchor_panel is listed above for explicit user-facing inventory even
    # though it is already part of EXPECTED_SOURCE; retain one deterministic row.
    deduped = {}
    for row in rows:
        deduped[(row["artifact_key"], row["path"])] = row
    return sorted(deduped.values(), key=lambda row: (row["artifact_key"], row["path"]))


def raw_metrics(row: dict[str, str] | None, horizon: int) -> dict[str, Any]:
    if not row:
        return {"forward_return": UNAVAILABLE, "MFE": UNAVAILABLE, "MAE": UNAVAILABLE, "max_close_drawdown": UNAVAILABLE}
    prefix = f"T{horizon}_"
    return {
        "forward_return": row.get(prefix + "forward_close_return", UNAVAILABLE),
        "MFE": row.get(prefix + "mfe", UNAVAILABLE),
        "MAE": row.get(prefix + "mae", UNAVAILABLE),
        "max_close_drawdown": row.get(prefix + "max_close_drawdown", UNAVAILABLE),
    }


def snapshot_values(features: dict[str, dict[int, dict[str, Any]]], anchor_id: str) -> dict[str, dict[str, Any]]:
    result = {}
    for rel in SNAPSHOT_DAYS:
        row = features.get(anchor_id, {}).get(rel)
        if row is None:
            result[str(rel)] = {"status": UNAVAILABLE}
            continue
        result[str(rel)] = {key: row.get(key, UNAVAILABLE) for key in ["stock_code", "market", "anchor_date", "stratum", "event_type", "pit_status", "source_lineage", "source_observation_id", "feature_status_summary", *FEATURES]}
    return result


def at(snapshots: dict[str, dict[str, Any]], rel: int, feature: str) -> Any:
    return snapshots.get(str(rel), {}).get(feature)


def any_predicate(snapshots: dict[str, dict[str, Any]], rels: Iterable[int], feature: str, predicate) -> bool:
    return any(predicate(at(snapshots, rel, feature)) for rel in rels)


def positive(value: Any) -> bool:
    numeric = number(value)
    return numeric is not None and numeric > 0


def nonnegative(value: Any) -> bool:
    numeric = number(value)
    return numeric is not None and numeric >= 0


def negative(value: Any) -> bool:
    numeric = number(value)
    return numeric is not None and numeric < 0


def below_one(value: Any) -> bool:
    numeric = number(value)
    return numeric is not None and numeric < 1


def above_one(value: Any) -> bool:
    numeric = number(value)
    return numeric is not None and numeric > 1


def calculate_components(snapshots: dict[str, dict[str, Any]]) -> dict[str, Any]:
    a = {
        "trend_background": any_predicate(snapshots, [-20, -10], "close_vs_ma20", positive) or any_predicate(snapshots, [-20, -10], "ma_alignment_bullish", lambda value: bool_value(value) is True),
        "improving_trend": any_predicate(snapshots, [-20, -10], "ma20_slope_5", positive) or any_predicate(snapshots, [-20, -10], "ma60_slope_5", positive),
        "base_compression": any_predicate(snapshots, [-5, -3, -1], "range_compression_5_to_20", below_one) or any_predicate(snapshots, [-5, -3, -1], "volatility_contraction_5_to_20", below_one),
        "volume_contraction": any_predicate(snapshots, [-5, -3, -1], "volume_contraction_state", lambda value: bool_value(value) is True) or any_predicate(snapshots, [-5, -3, -1], "VOLUME_RATIO_20", below_one),
        "participation_transition": any_predicate(snapshots, [-1, 0], "volume_expansion_state", lambda value: bool_value(value) is True) or any_predicate(snapshots, [-1, 0], "VOLUME_RATIO_20", above_one),
        "breakout_context_proxy": None,
        "ma_convergence_proxy": None,
    }
    b = {
        "prior_expansion": any_predicate(snapshots, [-20, -10], "RAW_CLOSE_RETURN_20D", positive) or any_predicate(snapshots, [-20, -10], "RAW_CLOSE_RETURN_5D", positive),
        "pullback": any_predicate(snapshots, [-5, -3], "RAW_CLOSE_RETURN_5D", negative) or any_predicate(snapshots, [-5, -3], "close_vs_ma20", negative) or any_predicate(snapshots, [-5, -3], "ma_alignment_bearish", lambda value: bool_value(value) is True),
        "trend_preservation": any_predicate(snapshots, [-10, -5, -3], "close_vs_ma60", nonnegative) or any_predicate(snapshots, [-10, -5, -3], "ma60_slope_5", nonnegative),
        "stabilization": any_predicate(snapshots, [-3, -1], "range_compression_5_to_20", below_one) or any_predicate(snapshots, [-3, -1], "volatility_contraction_5_to_20", below_one) or any_predicate(snapshots, [-3, -1], "volume_contraction_state", lambda value: bool_value(value) is True),
        "reclaim_turn": any_predicate(snapshots, [-1, 0], "RAW_CLOSE_RETURN_5D", positive) or any_predicate(snapshots, [-1, 0], "close_vs_ma20", positive) or any_predicate(snapshots, [-1, 0], "volume_expansion_state", lambda value: bool_value(value) is True),
    }
    return {
        "A": {"components": a, "component_count": sum(value is True for value in a.values()), "available_component_count": sum(value is not None for value in a.values()), "pool_rule": "component_count>=2; no optimized threshold"},
        "B": {"components": b, "component_count": sum(value is True for value in b.values()), "available_component_count": sum(value is not None for value in b.values()), "pool_rule": "component_count>=2; no optimized threshold"},
        "definitions_note": "Components use existing PIT-safe feature semantics and natural sign/state boundaries only; they are extraction labels, not strategy rules.",
    }


def failure_labels(match: dict[str, str], raw: dict[str, str] | None) -> dict[str, Any]:
    t5 = number(match.get("control_outcome_T5"))
    t10 = number(match.get("control_outcome_T10"))
    labels = []
    if t5 is not None and t5 < 0:
        labels.append("FAIL_T5_NEGATIVE")
    if t10 is not None and t10 < 0:
        labels.append("FAIL_T10_NEGATIVE")
    if str(match.get("control_is_success_for_same_stratum", "")).lower() == "false" and t5 is not None and t10 is not None and max(t5, t10) <= 0:
        labels.append("FAIL_NO_EXPANSION")
    # The canonical raw panel exposes MAE values but does not expose a frozen
    # large-MAE label. We retain the metrics for review and do not add a new
    # reporting threshold here.
    return {
        "labels": labels,
        "FAIL_T5_NEGATIVE": "FAIL_T5_NEGATIVE" in labels,
        "FAIL_T10_NEGATIVE": "FAIL_T10_NEGATIVE" in labels,
        "FAIL_NO_EXPANSION": "FAIL_NO_EXPANSION" in labels,
        "FAIL_LARGE_MAE": UNAVAILABLE,
        "FAIL_BREAKOUT_REVERSAL": UNAVAILABLE,
        "label_limitations": "FAIL_LARGE_MAE and FAIL_BREAKOUT_REVERSAL have no frozen canonical boolean label; no new threshold or reversal rule was invented.",
    }


def outcomes(match: dict[str, str], role: str, raw: dict[str, str] | None) -> dict[str, Any]:
    if role == "CONTROL":
        t5 = match.get("control_outcome_T5", UNAVAILABLE)
        t10 = match.get("control_outcome_T10", UNAVAILABLE)
    else:
        t5 = match.get("successful_outcome_T5", UNAVAILABLE)
        t10 = match.get("successful_outcome_T10", UNAVAILABLE)
    return {"T5": {"forward_return": t5, **raw_metrics(raw, 5)}, "T10": {"forward_return": t10, **raw_metrics(raw, 10)}}


def source_lineage(row: dict[str, Any], match: dict[str, str], role: str) -> str:
    if row.get("source_lineage") and row.get("source_lineage") != UNAVAILABLE:
        return str(row["source_lineage"])
    return match.get("control_source_lineage" if role == "CONTROL" else "successful_source_lineage", UNAVAILABLE)


def anchor_record(anchor_id: str, role: str, match: dict[str, str], features: dict[str, dict[int, dict[str, Any]]], raw_lookup: dict[str, dict[str, str]]) -> dict[str, Any]:
    snaps = snapshot_values(features, anchor_id)
    row0 = features.get(anchor_id, {}).get(0, {})
    raw = raw_lookup.get(anchor_id)
    return {
        "anchor_id": anchor_id,
        "role": role,
        "instrument_id": row0.get("instrument_id", match.get("successful_instrument_id" if role == "SUCCESS" else "control_instrument_id", UNAVAILABLE)),
        "stock_code": row0.get("stock_code", UNAVAILABLE),
        "stock_name": UNAVAILABLE,
        "market": row0.get("market", match.get("control_market", UNAVAILABLE)),
        "anchor_date": row0.get("anchor_date", match.get("successful_anchor_date" if role == "SUCCESS" else "control_anchor_date", UNAVAILABLE)),
        "source_lineage": source_lineage(row0, match, role),
        "source_observation_id": row0.get("source_observation_id", UNAVAILABLE),
        "pit_status": row0.get("pit_status", match.get("successful_pit_status" if role == "SUCCESS" else "control_pit_status", UNAVAILABLE)),
        "snapshots": snaps,
        "components": calculate_components(snaps),
        "outcomes": outcomes(match, role, raw),
        "a_state": {key: (raw.get(key) if raw else UNAVAILABLE) for key in ["a_state_a_state_bucket", "a_state_a1_preceded_20", "a_state_a2_preceded_20", "a_state_a1_to_a2_preceded_20", "a_state_a2_without_prior_a1_20"]},
        "liquidity_quintile": match.get("control_liquidity_quintile" if role == "CONTROL" else "", UNAVAILABLE),
        "volatility_quintile": match.get("control_volatility_quintile" if role == "CONTROL" else "", UNAVAILABLE),
        "price_scale_bucket": match.get("control_price_scale_bucket" if role == "CONTROL" else "", UNAVAILABLE),
        "source_match_stratum": match.get("stratum", UNAVAILABLE),
        "source_episode_id": match.get("successful_episode_id", UNAVAILABLE),
        "source_successful_anchor_id": match.get("successful_anchor_id", UNAVAILABLE),
    }


def candidate_payload(setup: str, control: dict[str, Any], match: dict[str, str], comparator: dict[str, Any] | None, selection_rank: int, selection_note: str) -> dict[str, Any]:
    failures = failure_labels(match, None)
    candidate_id = f"{setup}|{control['anchor_id']}|{match.get('stratum', UNAVAILABLE)}"
    return {
        "candidate_id": candidate_id,
        "setup_hypothesis": setup + "_LIKE",
        "success_status": "FAILURE_CANDIDATE",
        "candidate": control,
        "source_match": {key: match.get(key, UNAVAILABLE) for key in MATCH_FIELDS},
        "failure_labels": failures,
        "comparator": comparator,
        "selection_rank": selection_rank,
        "selection_note": selection_note,
        "human_boundary": "Human hypothesis similarity only; no causal explanation, rule, threshold, or strategy acceptance.",
    }


def even_indices(length: int, count: int) -> list[int]:
    if length <= count:
        return list(range(length))
    if count <= 1:
        return [0]
    return [round(index * (length - 1) / (count - 1)) for index in range(count)]


def spread_select(candidates: list[tuple[dict[str, Any], dict[str, str]]], target: int, excluded: set[str] | None = None, setup_letter: str = "A") -> list[tuple[dict[str, Any], dict[str, str]]]:
    excluded = excluded or set()
    eligible = [item for item in candidates if item[0]["anchor_id"] not in excluded]
    by_market: dict[str, list[tuple[dict[str, Any], dict[str, str]]]] = defaultdict(list)
    for item in eligible:
        by_market[str(item[0].get("market", UNAVAILABLE))].append(item)
    for rows in by_market.values():
        rows.sort(key=lambda item: (-int(item[0]["components"][setup_letter]["component_count"]), item[0].get("anchor_date", ""), item[0].get("instrument_id", ""), item[0]["anchor_id"]))
    selected: list[tuple[dict[str, Any], dict[str, str]]] = []
    used_instruments: set[str] = set()
    market_order = sorted(by_market, key=lambda market: (-len(by_market[market]), market))
    quota = {market: max(1, round(target * len(by_market[market]) / max(len(eligible), 1))) for market in market_order}
    for market in market_order:
        rows = by_market[market]
        for index in even_indices(len(rows), min(quota[market], target - len(selected))):
            item = rows[index]
            instrument = str(item[0].get("instrument_id", ""))
            if instrument in used_instruments:
                continue
            selected.append(item)
            used_instruments.add(instrument)
            if len(selected) >= target:
                return selected
    remaining = sorted(eligible, key=lambda item: (-int(item[0]["components"][setup_letter]["component_count"]), item[0].get("anchor_date", ""), item[0].get("instrument_id", ""), item[0]["anchor_id"]))
    for item in remaining:
        if len(selected) >= target:
            break
        if item[0]["anchor_id"] in {row[0]["anchor_id"] for row in selected}:
            continue
        selected.append(item)
    return selected[:target]


def choose_comparator(setup: str, candidate: dict[str, Any], match: dict[str, str], success_records: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    direct_id = match.get("successful_anchor_id", "")
    direct = success_records.get(direct_id)
    if direct and direct["components"][setup]["component_count"] >= 2:
        return direct
    pool = [record for record in success_records.values() if record["components"][setup]["component_count"] >= 2]
    if not pool:
        return None
    target_date = candidate.get("anchor_date", "")
    target_date_num = target_date
    def key(record: dict[str, Any]) -> tuple[Any, ...]:
        market_penalty = 0 if record.get("market") == candidate.get("market") else 1
        stratum_penalty = 0 if record.get("source_match_stratum") == match.get("stratum") else 1
        score_gap = abs(record["components"][setup]["component_count"] - candidate["components"][setup]["component_count"])
        return (score_gap, market_penalty, stratum_penalty, abs(len(str(record.get("anchor_date", ""))) - len(str(target_date_num))), record.get("anchor_date", ""), record.get("instrument_id", ""), record["anchor_id"])
    return sorted(pool, key=key)[0]


def jsonl_write(path: Path, rows: list[dict[str, Any]]) -> str:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return sha256_file(path)


def jsonl_read(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def compact_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    snapshots = record.get("snapshots", {})
    output = {}
    for rel in SNAPSHOT_DAYS:
        snap = snapshots.get(str(rel), {})
        output[str(rel)] = {feature: snap.get(feature, UNAVAILABLE) for feature in ["close_vs_ma20", "close_vs_ma60", "ma20_slope_5", "ma60_slope_5", "ma_alignment_bullish", "ma_alignment_bearish", "rolling_range_pct_20", "range_compression_5_to_20", "realized_vol_20", "volatility_contraction_5_to_20", "VOLUME_RATIO_20", "volume_contraction_state", "volume_expansion_state", "RAW_CLOSE_RETURN_5D", "RAW_CLOSE_RETURN_20D", "RSI14", "MACD_HISTOGRAM_12_26_9", "a_state_bucket"]}
    return output


CANDIDATE_FIELDS = [
    "candidate_id", "setup_hypothesis", "selection_rank", "instrument_id", "stock_code", "stock_name", "market", "anchor_date", "source_match_stratum", "source_episode_id", "source_successful_anchor_id", "component_count", "available_component_count", "component_checklist", "failure_labels", "FAIL_T5_NEGATIVE", "FAIL_T10_NEGATIVE", "FAIL_NO_EXPANSION", "FAIL_LARGE_MAE", "FAIL_BREAKOUT_REVERSAL", "T5_forward_return", "T10_forward_return", "T5_MFE", "T5_MAE", "T10_MFE", "T10_MAE", "a_state_bucket", "pit_status", "source_lineage", "comparator_anchor_id", "comparator_stock_code", "comparator_date", "comparator_component_count", "selection_note",
]


def candidate_csv_row(payload: dict[str, Any]) -> dict[str, Any]:
    candidate = payload["candidate"]
    comp = payload.get("comparator") or {}
    failures = payload["failure_labels"]
    outcomes_value = candidate["outcomes"]
    setup_letter = payload["setup_hypothesis"][0]
    checklist = candidate["components"][setup_letter]["components"]
    return {
        "candidate_id": payload["candidate_id"],
        "setup_hypothesis": payload["setup_hypothesis"],
        "selection_rank": payload["selection_rank"],
        "instrument_id": candidate.get("instrument_id", UNAVAILABLE),
        "stock_code": candidate.get("stock_code", UNAVAILABLE),
        "stock_name": candidate.get("stock_name", UNAVAILABLE),
        "market": candidate.get("market", UNAVAILABLE),
        "anchor_date": candidate.get("anchor_date", UNAVAILABLE),
        "source_match_stratum": candidate.get("source_match_stratum", UNAVAILABLE),
        "source_episode_id": candidate.get("source_episode_id", UNAVAILABLE),
        "source_successful_anchor_id": candidate.get("source_successful_anchor_id", UNAVAILABLE),
        "component_count": candidate["components"][setup_letter]["component_count"],
        "available_component_count": candidate["components"][setup_letter]["available_component_count"],
        "component_checklist": json.dumps(checklist, ensure_ascii=False, sort_keys=True),
        "failure_labels": ",".join(failures["labels"]),
        "FAIL_T5_NEGATIVE": failures["FAIL_T5_NEGATIVE"],
        "FAIL_T10_NEGATIVE": failures["FAIL_T10_NEGATIVE"],
        "FAIL_NO_EXPANSION": failures["FAIL_NO_EXPANSION"],
        "FAIL_LARGE_MAE": failures["FAIL_LARGE_MAE"],
        "FAIL_BREAKOUT_REVERSAL": failures["FAIL_BREAKOUT_REVERSAL"],
        "T5_forward_return": outcomes_value["T5"]["forward_return"],
        "T10_forward_return": outcomes_value["T10"]["forward_return"],
        "T5_MFE": outcomes_value["T5"]["MFE"],
        "T5_MAE": outcomes_value["T5"]["MAE"],
        "T10_MFE": outcomes_value["T10"]["MFE"],
        "T10_MAE": outcomes_value["T10"]["MAE"],
        "a_state_bucket": candidate.get("a_state", {}).get("a_state_a_state_bucket", UNAVAILABLE),
        "pit_status": candidate.get("pit_status", UNAVAILABLE),
        "source_lineage": candidate.get("source_lineage", UNAVAILABLE),
        "comparator_anchor_id": comp.get("anchor_id", UNAVAILABLE),
        "comparator_stock_code": comp.get("stock_code", UNAVAILABLE),
        "comparator_date": comp.get("anchor_date", UNAVAILABLE),
        "comparator_component_count": comp.get("components", {}).get(payload["setup_hypothesis"][0], {}).get("component_count", UNAVAILABLE),
        "selection_note": payload["selection_note"],
    }


def same_different(candidate: dict[str, Any], comparator: dict[str, Any], setup_letter: str) -> tuple[list[str], list[str]]:
    c = candidate["components"][setup_letter]["components"]
    s = comparator["components"][setup_letter]["components"]
    same, different = [], []
    for label in COMPONENT_LABELS[setup_letter]:
        if c.get(label) == s.get(label):
            same.append(label)
        else:
            different.append(label)
    return same, different


def snapshot_line(record: dict[str, Any], rel: int) -> str:
    snap = record.get("snapshots", {}).get(str(rel), {})
    if not snap or snap.get("status") == UNAVAILABLE:
        return UNAVAILABLE
    return "trend close/MA20={} MA20slope={}; compression range20={} ratio={}; volume ratio20={} contraction={} expansion={}; momentum raw5={} RSI={} MACD={}; A-state={}".format(
        fmt(snap.get("close_vs_ma20")), fmt(snap.get("ma20_slope_5")), fmt(snap.get("rolling_range_pct_20")), fmt(snap.get("range_compression_5_to_20")), fmt(snap.get("VOLUME_RATIO_20")), fmt(snap.get("volume_contraction_state")), fmt(snap.get("volume_expansion_state")), fmt(snap.get("RAW_CLOSE_RETURN_5D")), fmt(snap.get("RSI14")), fmt(snap.get("MACD_HISTOGRAM_12_26_9")), cell(snap.get("a_state_bucket", UNAVAILABLE)))


def pair_markdown(setup_letter: str, rows: list[dict[str, Any]]) -> str:
    lines = [f"# WS3 {setup_letter}-like success vs false-friend comparisons", "", "These comparisons use only the deterministic intermediate manifest. Same-looking and different-looking components are descriptive checklists for Owner review; they are not ranked discriminators, causal explanations, thresholds, or strategy rules.", ""]
    for index, row in enumerate(rows, 1):
        candidate = row["candidate"]
        comparator = row.get("comparator")
        lines += [f"## {index}. `{row['candidate_id']}`", "", f"- False friend: `{candidate.get('stock_code', UNAVAILABLE)}` / `{candidate.get('instrument_id', UNAVAILABLE)}` on `{candidate.get('anchor_date', UNAVAILABLE)}`; market `{candidate.get('market', UNAVAILABLE)}`; stratum `{candidate.get('source_match_stratum', UNAVAILABLE)}`.", f"- Comparator: `{comparator.get('stock_code', UNAVAILABLE) if comparator else UNAVAILABLE}` / `{comparator.get('instrument_id', UNAVAILABLE) if comparator else UNAVAILABLE}` on `{comparator.get('anchor_date', UNAVAILABLE) if comparator else UNAVAILABLE}`; comparator source `{row.get('comparator_source', UNAVAILABLE)}`.", f"- False friend outcome: T+5 `{fmt_pct(candidate.get('outcomes', {}).get('T5', {}).get('forward_return'))}`, T+10 `{fmt_pct(candidate.get('outcomes', {}).get('T10', {}).get('forward_return'))}`, MFE/MAE T5 `{fmt_pct(candidate.get('outcomes', {}).get('T5', {}).get('MFE'))}`/`{fmt_pct(candidate.get('outcomes', {}).get('T5', {}).get('MAE'))}`.", f"- Comparator outcome: T+5 `{fmt_pct(comparator.get('outcomes', {}).get('T5', {}).get('forward_return') if comparator else None)}`, T+10 `{fmt_pct(comparator.get('outcomes', {}).get('T10', {}).get('forward_return') if comparator else None)}`, MFE/MAE T5 `{fmt_pct(comparator.get('outcomes', {}).get('T5', {}).get('MFE') if comparator else None)}`/`{fmt_pct(comparator.get('outcomes', {}).get('T5', {}).get('MAE') if comparator else None)}`.", f"- Failure labels: `{','.join(row['failure_labels']['labels']) or UNAVAILABLE}`; A-state false friend `{candidate.get('a_state', {}).get('a_state_a_state_bucket', UNAVAILABLE)}`; comparator `{comparator.get('a_state', {}).get('a_state_a_state_bucket', UNAVAILABLE) if comparator else UNAVAILABLE}`.", "", "### Component checklist", "", f"- False friend: `{json.dumps(candidate['components'][setup_letter]['components'], ensure_ascii=False, sort_keys=True)}`", f"- Comparator: `{json.dumps(comparator['components'][setup_letter]['components'], ensure_ascii=False, sort_keys=True) if comparator else UNAVAILABLE}`"]
        if comparator:
            same, different = same_different(candidate, comparator, setup_letter)
            lines += [f"- Same-looking components: `{', '.join(same) or 'none observed'}`", f"- Different-looking components: `{', '.join(different) or 'none observed'}`"]
        else:
            lines.append(f"- Same/different component comparison: `{UNAVAILABLE}`")
        lines += ["", "### PIT snapshots", "", "| Day | False friend | Success comparator |", "|---:|---|---|"]
        for rel in SNAPSHOT_DAYS:
            label = "D0" if rel == 0 else f"D{rel}"
            lines.append(f"| {label} | {snapshot_line(candidate, rel)} | {snapshot_line(comparator, rel) if comparator else UNAVAILABLE} |")
        lines += ["", "No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.", ""]
    return "\n".join(lines)


def case_cards(rows: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    machine = []
    lines = ["# WS3 A/B false-friend case cards", "", "Each card is a bounded human-review candidate extracted from existing PIT-safe artifacts. The setup labels are HUMAN_DISCOVERY_HYPOTHESES only.", ""]
    for index, row in enumerate(rows, 1):
        candidate = row["candidate"]
        comparator = row.get("comparator")
        card = {
            "case_index": index,
            "candidate_id": row["candidate_id"],
            "setup_hypothesis": row["setup_hypothesis"],
            "false_friend": candidate,
            "comparator": comparator,
            "failure_labels": row["failure_labels"],
            "selection_rank": row["selection_rank"],
            "selection_note": row["selection_note"],
            "source_match": row["source_match"],
        }
        machine.append(card)
        lines += [f"## Case {index} — `{row['setup_hypothesis']}` — `{candidate.get('stock_code', UNAVAILABLE)}`", "", f"- Anchor: `{candidate.get('anchor_date', UNAVAILABLE)}`; instrument `{candidate.get('instrument_id', UNAVAILABLE)}`; market `{candidate.get('market', UNAVAILABLE)}`.", f"- Setup hypothesis: `{row['setup_hypothesis']}`; status `FAILURE_CANDIDATE`.", f"- Comparator: `{comparator.get('stock_code', UNAVAILABLE) if comparator else UNAVAILABLE}` on `{comparator.get('anchor_date', UNAVAILABLE) if comparator else UNAVAILABLE}`.", f"- T+5/T+10: `{fmt_pct(candidate.get('outcomes', {}).get('T5', {}).get('forward_return'))}` / `{fmt_pct(candidate.get('outcomes', {}).get('T10', {}).get('forward_return'))}`; MFE/MAE T5 `{fmt_pct(candidate.get('outcomes', {}).get('T5', {}).get('MFE'))}` / `{fmt_pct(candidate.get('outcomes', {}).get('T5', {}).get('MAE'))}`.", f"- A-state: `{candidate.get('a_state', {}).get('a_state_a_state_bucket', UNAVAILABLE)}`; failure labels `{','.join(row['failure_labels']['labels']) or UNAVAILABLE}`.", f"- Component checklist: `{json.dumps(candidate['components'][row['setup_hypothesis'][0]]['components'], ensure_ascii=False, sort_keys=True)}`", "", "| Day | Trend | Compression | Volume | Momentum | A-state |", "|---:|---|---|---|---|---|"]
        for rel in SNAPSHOT_DAYS:
            snap = candidate.get("snapshots", {}).get(str(rel), {})
            lines.append("| " + " | ".join([
                "D0" if rel == 0 else f"D{rel}",
                f"close/MA20={fmt(snap.get('close_vs_ma20'))}; MA20 slope={fmt(snap.get('ma20_slope_5'))}; MA60={fmt(snap.get('close_vs_ma60'))}",
                f"range20={fmt(snap.get('rolling_range_pct_20'))}; compression={fmt(snap.get('range_compression_5_to_20'))}; vol contraction={fmt(snap.get('volatility_contraction_5_to_20'))}",
                f"ratio20={fmt(snap.get('VOLUME_RATIO_20'))}; contraction={fmt(snap.get('volume_contraction_state'))}; expansion={fmt(snap.get('volume_expansion_state'))}",
                f"raw5={fmt(snap.get('RAW_CLOSE_RETURN_5D'))}; raw20={fmt(snap.get('RAW_CLOSE_RETURN_20D'))}; RSI={fmt(snap.get('RSI14'))}; MACD={fmt(snap.get('MACD_HISTOGRAM_12_26_9'))}",
                cell(snap.get('a_state_bucket', UNAVAILABLE)),
            ]) + " |")
        lines += ["", "Owner review boundary: do not infer why this case failed from this card alone.", ""]
    return "\n".join(lines), machine


def question_sheet() -> str:
    return """# WS3 A/B false-friend human review questions

These questions are intentionally unanswered. They are for Owner + ChatGPT manual review only.

## A setup

1. Which failed A cases had apparently healthy MA60/trend background?
2. Which failed A cases had compression but no sustained volume transition?
3. Which failed A breakouts occurred after already-extended price structures?
4. Does MA convergence look different between success/failure?
5. Are failed A cases more often post-climax consolidations rather than genuine bases?

## B setup

6. Which failed B cases looked like healthy pullbacks?
7. Which were actually trend deterioration?
8. Does MA60 slope/persistence differ?
9. Does reclaim happen too late / too weak?
10. Does volume recover differently?
11. Does pullback depth/path matter?
12. Is prior expansion quality materially different?

## Cross-setup

13. Which pre-event differences appear repeatedly visible to a human?
14. Which differences are likely hindsight artifacts?
15. Which candidate discriminators deserve later frozen confirmatory research?

Boundary: no answer here is an accepted setup, Core V0 rule, score, production rule, or confirmatory conclusion.
"""


def source_inventory_markdown(rows: list[dict[str, Any]]) -> str:
    lines = ["# WS3 AB false-friend source artifact inventory", "", "| Artifact | Status | Size (bytes) | Path |", "|---|---|---:|---|"]
    for row in rows:
        lines.append(f"| `{row['artifact_key']}` | {row['status']} | {row.get('size_bytes') or UNAVAILABLE} | `{row['path']}` |")
    return "\n".join(lines)


def master_markdown(summary: dict[str, Any], files: list[str], a_rows: list[dict[str, Any]], b_rows: list[dict[str, Any]]) -> str:
    def table(rows: list[dict[str, Any]]) -> list[str]:
        result = ["| Rank | Stock | Date | Market | Components | Failures | T+5 | T+10 | Comparator |", "|---:|---|---|---|---:|---|---:|---:|---|"]
        for row in rows:
            c = row["candidate"]
            comp = row.get("comparator") or {}
            result.append(f"| {row['selection_rank']} | {cell(c.get('stock_code', UNAVAILABLE))} | {c.get('anchor_date', UNAVAILABLE)} | {c.get('market', UNAVAILABLE)} | {c['components'][row['setup_hypothesis'][0]]['component_count']} | {cell(','.join(row['failure_labels']['labels']) or UNAVAILABLE)} | {fmt_pct(c['outcomes']['T5']['forward_return'])} | {fmt_pct(c['outcomes']['T10']['forward_return'])} | {cell(comp.get('stock_code', UNAVAILABLE))} |")
        return result
    lines = [
        "# WS3 AB False-Friend Owner Review Pack", "", "This is an extraction-only human handoff from existing canonical Successful Swing artifacts. A/B are provisional human hypotheses, not frozen setups, Core V0, strategy rules, scores, recommendations, or production policy.", "",
        "## Section 1 — Task context and human hypothesis boundary", "", f"- Task: `{TASK_ID}`; source task: `{SOURCE_TASK}`; source review pack: `{REVIEW_TASK}`.", f"- Dataset: `{summary.get('SOURCE_INSTRUMENT_COUNT', UNAVAILABLE)}` instruments; `{summary.get('SOURCE_OHLCV_ROW_COUNT', UNAVAILABLE)}` accepted rows; SHA `{summary.get('SOURCE_SHA256', UNAVAILABLE)}`; adjustment `{summary.get('ADJUSTMENT_STATE', 'UNKNOWN_RAW_ONLY')}`.", f"- Existing episodes/controls: `{summary.get('DISTINCT_SWING_EPISODES', UNAVAILABLE)}` / `{summary.get('MATCHED_CONTROLS', UNAVAILABLE)}`. Full replay, event mining, feature recomputation, and matching rebuild were not executed.", "- A = Base / Box Breakout hypothesis. B = Pullback / Reclaim hypothesis. C = Trend Birth / Long-Base Escape was explicitly excluded.", "",
        "## Section 2 — A hypothesis summary", "", "A-like components are descriptive: trend/background, improving trend, base compression, volume contraction, and participation transition. Breakout-context and MA-convergence proxies were unavailable in the frozen panel and were not invented. Inclusion used component count >=2 with existing sign/state semantics; no threshold search occurred.", "", f"- A-like candidate pool: `{summary.get('A_LIKE_CANDIDATE_POOL_COUNT', UNAVAILABLE)}`; selected false friends: `{summary.get('A_FALSE_FRIEND_COUNT', UNAVAILABLE)}`; comparators: `{summary.get('A_SUCCESS_COMPARATOR_COUNT', UNAVAILABLE)}`.", "",
        "## Section 3 — 15 A-like false friends", "", *table(a_rows), "", "Full candidate fields: [ws3-a-like-false-friend-candidates.csv](ws3-a-like-false-friend-candidates.csv).", "",
        "## Section 4 — A success vs false-friend comparisons", "", "See [ws3-a-success-vs-false-friend-pairs.md](ws3-a-success-vs-false-friend-pairs.md). Same/different checklists are not ranked and do not explain causality.", "",
        "## Section 5 — B hypothesis summary", "", "B-like components are descriptive: prior expansion, pullback, trend preservation, stabilization, and reclaim/turn. The component count uses existing PIT-safe signs/states only and is not a strategy score.", "", f"- B-like candidate pool: `{summary.get('B_LIKE_CANDIDATE_POOL_COUNT', UNAVAILABLE)}`; selected false friends: `{summary.get('B_FALSE_FRIEND_COUNT', UNAVAILABLE)}`; comparators: `{summary.get('B_SUCCESS_COMPARATOR_COUNT', UNAVAILABLE)}`.", "",
        "## Section 6 — 15 B-like false friends", "", *table(b_rows), "", "Full candidate fields: [ws3-b-like-false-friend-candidates.csv](ws3-b-like-false-friend-candidates.csv).", "",
        "## Section 7 — B success vs false-friend comparisons", "", "See [ws3-b-success-vs-false-friend-pairs.md](ws3-b-success-vs-false-friend-pairs.md).", "",
        "## Section 8 — Cross-setup observations without conclusions", "", f"- Selected false friends by market: TPE `{summary.get('TPE_FALSE_FRIEND_COUNT', UNAVAILABLE)}`, TWO `{summary.get('TWO_FALSE_FRIEND_COUNT', UNAVAILABLE)}`.", "- MAE and reversal metrics are shown when present in the existing raw anchor panel; no new large-MAE or breakout-reversal threshold was created.", "- Relative Strength remains unavailable from the upstream canonical benchmark posture and was not added here.", "- These observations are for manual inspection. No A/B acceptance or discriminator ranking is made.", "",
        "## Section 9 — Human review questions", "", "See [ws3-ab-human-review-question-sheet.md](ws3-ab-human-review-question-sheet.md).", "",
        "## Section 10 — Source artifact index", "", "| Artifact | Purpose |", "|---|---|", *[f"| [{name}]({name}) | Supporting extraction/review artifact |" for name in files], "", "Stop boundary: Owner + ChatGPT must perform manual review before any future frozen confirmatory research. This task does not create a formal A/B strategy specification.",
    ]
    return "\n".join(lines)


def run_preflight(root: Path, source_paths: dict[str, Path], out: Path) -> dict[str, Any]:
    required_headers = {
        "matched_control_panel": MATCH_FIELDS,
        "pre_event_feature_panel": PANEL_FIELDS,
        "raw_anchor_panel": RAW_FIELDS,
        "robust_signal_panel": ["feature_family", "feature_id", "classification"],
        "promising_signal_panel": ["feature_family", "feature_id", "classification"],
    }
    header_results = {}
    for key, required in required_headers.items():
        fields, _ = read_sample(source_paths[key], 1)
        header_results[key] = {"required": required, "missing": [field for field in required if field not in fields], "pass": all(field in fields for field in required)}
    fixture_panel_fields, fixture_panel = read_sample(source_paths["pre_event_feature_panel"], 20)
    fixture_match_fields, fixture_matches = read_sample(source_paths["matched_control_panel"], 2)
    if not fixture_panel or not fixture_matches:
        raise RuntimeError("BLOCKED_PRELIGHT_ASSERTION: fixture source rows unavailable")
    panel_row = fixture_panel[0]
    match = fixture_matches[0]
    fixture_success = match["successful_anchor_id"]
    fixture_control = match["control_anchor_id"]
    fake_snapshots = {str(rel): {feature: panel_row.get("feature_" + feature, UNAVAILABLE) for feature in FEATURES} | {"pit_status": "PIT_SAFE", "source_lineage": panel_row.get("source_lineage", UNAVAILABLE), "stock_code": panel_row.get("stock_code", UNAVAILABLE), "market": panel_row.get("market", UNAVAILABLE), "anchor_date": panel_row.get("anchor_date", UNAVAILABLE)} for rel in SNAPSHOT_DAYS}
    fixture_features = {fixture_success: {rel: dict(fake_snapshots[str(rel)]) for rel in SNAPSHOT_DAYS}, fixture_control: {rel: dict(fake_snapshots[str(rel)]) for rel in SNAPSHOT_DAYS}}
    fixture_raw = {fixture_success: {"anchor_id": fixture_success, "T5_mfe": "0.1", "T5_mae": "-0.02", "T10_mfe": "0.12", "T10_mae": "-0.03", "a_state_a_state_bucket": "NEITHER"}, fixture_control: {"anchor_id": fixture_control, "T5_mfe": "0.0", "T5_mae": "-0.02", "T10_mfe": "0.0", "T10_mae": "-0.03", "a_state_a_state_bucket": "NEITHER"}}
    success_record = anchor_record(fixture_success, "SUCCESS", match, fixture_features, fixture_raw)
    control_record = anchor_record(fixture_control, "CONTROL", match, fixture_features, fixture_raw)
    component_pass = isinstance(calculate_components(fake_snapshots), dict)
    join_pass = success_record["anchor_id"] == match["successful_anchor_id"] and control_record["anchor_id"] == match["control_anchor_id"] and len(success_record["snapshots"]) == 6
    fixture_failure = failure_labels(match, fixture_raw[fixture_control])
    fixture_payload = candidate_payload("A", control_record, match, success_record, 1, "fixture")
    fixture_payload["failure_labels"] = fixture_failure
    selection_pass = len(spread_select([(control_record, match)], 1, setup_letter="A")) == 1
    schema_pass = all(field in candidate_csv_row(fixture_payload) for field in CANDIDATE_FIELDS)
    with tempfile.TemporaryDirectory(prefix="ws3-ab-preflight-") as temp:
        temp_path = Path(temp)
        manifest_path = temp_path / "fixture.jsonl"
        manifest_hash = jsonl_write(manifest_path, [fixture_payload])
        roundtrip = jsonl_read(manifest_path)
        write_csv(temp_path / "fixture.csv", [candidate_csv_row(fixture_payload)], CANDIDATE_FIELDS)
        markdown = pair_markdown("A", [fixture_payload])
        case_md, case_json = case_cards([fixture_payload])
        master = master_markdown({"A_LIKE_CANDIDATE_POOL_COUNT": 1, "A_FALSE_FRIEND_COUNT": 1, "A_SUCCESS_COMPARATOR_COUNT": 1, "B_LIKE_CANDIDATE_POOL_COUNT": 0, "B_FALSE_FRIEND_COUNT": 0, "B_SUCCESS_COMPARATOR_COUNT": 0}, ["fixture.csv"], [fixture_payload], [])
        formatter_pass = all(text for text in [markdown, case_md, master]) and len(roundtrip) == 1 and len(case_json) == 1 and bool(manifest_hash)
    result = {
        "TASK_ID": TASK_ID,
        "FIXTURE_DRY_RUN_PASS": "YES" if fixture_panel and fixture_matches else "NO",
        "OUTPUT_SCHEMA_ASSERTION_PASS": "YES" if schema_pass and all(item["pass"] for item in header_results.values()) else "NO",
        "JOIN_ASSERTION_PASS": "YES" if join_pass else "NO",
        "FORMATTER_ASSERTION_PASS": "YES" if formatter_pass else "NO",
        "SELECTION_ASSERTION_PASS": "YES" if selection_pass else "NO",
        "SMALL_FIXTURE_PANEL_ROWS": len(fixture_panel),
        "SMALL_FIXTURE_MATCH_ROWS": len(fixture_matches),
        "HEADER_RESULTS": header_results,
        "JOIN_KEYS": {"success_anchor_id": fixture_success, "control_anchor_id": fixture_control},
        "LARGE_SCAN_STARTED": "NO",
        "SKILL_PATH_RESOLVED": str(SKILL_PATH),
        "SOURCE_CANONICAL_HEAD": git_head(root),
    }
    write_json(out / "ws3-ab-false-friend-preflight.json", result)
    if not all(result[key] == "YES" for key in ["FIXTURE_DRY_RUN_PASS", "OUTPUT_SCHEMA_ASSERTION_PASS", "JOIN_ASSERTION_PASS", "FORMATTER_ASSERTION_PASS", "SELECTION_ASSERTION_PASS"]):
        raise RuntimeError("BLOCKED_PRELIGHT_ASSERTION")
    return result


def build_summary(source_summary: dict[str, Any], inventory_rows: list[dict[str, Any]], a_pool: list[Any], b_pool: list[Any], a_selected: list[dict[str, Any]], b_selected: list[dict[str, Any]], a_pairs: list[dict[str, Any]], b_pairs: list[dict[str, Any]], manifest_hash: str, runtime: float, source_head: str) -> dict[str, Any]:
    selected = a_selected + b_selected
    fail_counts = Counter(label for row in selected for label in row["failure_labels"]["labels"])
    markets = Counter(row["candidate"].get("market", UNAVAILABLE) for row in selected)
    return {
        "TASK_ID": TASK_ID,
        "TASK_FINAL_STATUS": "COMPLETE_PASS" if len(a_selected) > 0 and len(b_selected) > 0 else "COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS",
        "SOURCE_SUCCESSFUL_SWING_TASK": SOURCE_TASK,
        "SOURCE_OWNER_REVIEW_TASK": REVIEW_TASK,
        "SOURCE_CANONICAL_HEAD": source_head,
        "TASK_COMMIT": "PENDING_ISOLATED_TASK_COMMIT",
        "FINAL_CANONICAL_HEAD": "PENDING_CANONICAL_PROMOTION",
        "FIXTURE_DRY_RUN_PASS": "YES",
        "OUTPUT_SCHEMA_ASSERTION_PASS": "YES",
        "JOIN_ASSERTION_PASS": "YES",
        "FORMATTER_ASSERTION_PASS": "YES",
        "SOURCE_ARTIFACTS_FOUND": sum(row["status"] == "FOUND" for row in inventory_rows),
        "SOURCE_ARTIFACTS_MISSING": [row["artifact_key"] for row in inventory_rows if row["status"] == "MISSING"],
        "FULL_WS3_REPLAY": "NO",
        "FULL_EVENT_MINING_RERUN": "NO",
        "FULL_MATCHING_RERUN": "NO",
        "FULL_FEATURE_RECOMPUTE": "NO",
        "LARGE_PANEL_SCAN_COUNT": 2,
        "LARGE_PANEL_SCANS": ["ws3-successful-swing-raw-anchor-panel.csv", "ws3-successful-swing-pre-event-feature-panel.csv"],
        "INTERMEDIATE_MANIFEST_CREATED": "YES",
        "INTERMEDIATE_MANIFEST_SHA256": manifest_hash,
        "REPORT_GENERATION_USED_INTERMEDIATE_MANIFEST": "YES",
        "A_LIKE_CANDIDATE_POOL_COUNT": len(a_pool),
        "A_FALSE_FRIEND_COUNT": len(a_selected),
        "A_SUCCESS_COMPARATOR_COUNT": len(a_pairs),
        "B_LIKE_CANDIDATE_POOL_COUNT": len(b_pool),
        "B_FALSE_FRIEND_COUNT": len(b_selected),
        "B_SUCCESS_COMPARATOR_COUNT": len(b_pairs),
        "TPE_FALSE_FRIEND_COUNT": markets.get("TPE", 0),
        "TWO_FALSE_FRIEND_COUNT": markets.get("TWO", 0),
        "FAIL_T5_NEGATIVE_COUNT": fail_counts.get("FAIL_T5_NEGATIVE", 0),
        "FAIL_T10_NEGATIVE_COUNT": fail_counts.get("FAIL_T10_NEGATIVE", 0),
        "FAIL_NO_EXPANSION_COUNT": fail_counts.get("FAIL_NO_EXPANSION", 0),
        "FAIL_LARGE_MAE_COUNT": 0,
        "FAIL_BREAKOUT_REVERSAL_COUNT": 0,
        "A_OWNER_REVIEW_PACK_CREATED": "YES",
        "B_OWNER_REVIEW_PACK_CREATED": "YES",
        "MASTER_OWNER_REVIEW_PACK_CREATED": "YES",
        "NEW_FEATURE_DISCOVERY_EXECUTED": "NO",
        "NEW_THRESHOLD_SEARCH_EXECUTED": "NO",
        "MULTIVARIATE_MODEL_EXECUTED": "NO",
        "STRATEGY_RULE_CREATED": "NO",
        "A_SETUP_ACCEPTED": "NO",
        "B_SETUP_ACCEPTED": "NO",
        "A1_CHANGED": "NO",
        "A2_CHANGED": "NO",
        "DATABASE_MUTATION": "NO",
        "PRODUCTION_MUTATION": "NO",
        "WS1_CHANGED": "NO",
        "WS2_CHANGED": "NO",
        "WS4_CHANGED": "NO",
        "NEXT_TASK_CHANGED": "NO",
        "PUSH": "NO",
        "DEPLOY": "NO",
        "RELEASE": "NO",
        "READY_FOR_OWNER_HUMAN_FALSE_FRIEND_REVIEW": "YES_WITH_BOUNDED_LIMITATIONS",
        "TOTAL_WALL_CLOCK_RUNTIME_SECONDS": round(runtime, 3),
        "FAILURE_LIMITATIONS": ["FAIL_LARGE_MAE and FAIL_BREAKOUT_REVERSAL have no frozen canonical boolean labels; MAE/path metrics are retained where available without introducing new thresholds."],
        "ADJUSTMENT_STATE": "UNKNOWN_RAW_ONLY",
        "SOURCE_INSTRUMENT_COUNT": source_summary.get("SOURCE_INSTRUMENT_COUNT", 603),
        "SOURCE_OHLCV_ROW_COUNT": source_summary.get("SOURCE_OHLCV_ROW_COUNT", 288881),
        "SOURCE_SHA256": source_summary.get("SOURCE_SHA256", UNAVAILABLE),
        "DISTINCT_SWING_EPISODES": source_summary.get("DISTINCT_SWING_EPISODE_COUNT", UNAVAILABLE),
        "MATCHED_CONTROLS": source_summary.get("MATCHED_CONTROL_COUNT", UNAVAILABLE),
    }


def formal_report(summary: dict[str, Any], files: list[str]) -> str:
    lines = [
        f"# {TASK_ID}", "", f"TASK_ID={TASK_ID}", f"TASK_FINAL_STATUS={summary['TASK_FINAL_STATUS']}", f"SOURCE_CANONICAL_HEAD={summary['SOURCE_CANONICAL_HEAD']}", f"TASK_COMMIT={summary['TASK_COMMIT']}", f"FINAL_CANONICAL_HEAD={summary['FINAL_CANONICAL_HEAD']}", "", "## Preflight", "", f"FIXTURE_DRY_RUN_PASS={summary['FIXTURE_DRY_RUN_PASS']}", f"OUTPUT_SCHEMA_ASSERTION_PASS={summary['OUTPUT_SCHEMA_ASSERTION_PASS']}", f"JOIN_ASSERTION_PASS={summary['JOIN_ASSERTION_PASS']}", f"FORMATTER_ASSERTION_PASS={summary['FORMATTER_ASSERTION_PASS']}", "", "## Source artifacts", "", f"SOURCE_ARTIFACTS_FOUND={summary['SOURCE_ARTIFACTS_FOUND']}", f"SOURCE_ARTIFACTS_MISSING={','.join(summary['SOURCE_ARTIFACTS_MISSING']) if summary['SOURCE_ARTIFACTS_MISSING'] else 'NONE'}", "", "## Research boundary", "", "FULL_WS3_REPLAY=NO", "FULL_EVENT_MINING_RERUN=NO", "FULL_MATCHING_RERUN=NO", "FULL_FEATURE_RECOMPUTE=NO", f"LARGE_PANEL_SCAN_COUNT={summary['LARGE_PANEL_SCAN_COUNT']}", "INTERMEDIATE_MANIFEST_CREATED=YES", "REPORT_GENERATION_USED_INTERMEDIATE_MANIFEST=YES", "", "## Candidate and failure counts", "", f"A_LIKE_CANDIDATE_POOL_COUNT={summary['A_LIKE_CANDIDATE_POOL_COUNT']}", f"A_FALSE_FRIEND_COUNT={summary['A_FALSE_FRIEND_COUNT']}", f"A_SUCCESS_COMPARATOR_COUNT={summary['A_SUCCESS_COMPARATOR_COUNT']}", f"B_LIKE_CANDIDATE_POOL_COUNT={summary['B_LIKE_CANDIDATE_POOL_COUNT']}", f"B_FALSE_FRIEND_COUNT={summary['B_FALSE_FRIEND_COUNT']}", f"B_SUCCESS_COMPARATOR_COUNT={summary['B_SUCCESS_COMPARATOR_COUNT']}", f"TPE_FALSE_FRIEND_COUNT={summary['TPE_FALSE_FRIEND_COUNT']}", f"TWO_FALSE_FRIEND_COUNT={summary['TWO_FALSE_FRIEND_COUNT']}", f"FAIL_T5_NEGATIVE_COUNT={summary['FAIL_T5_NEGATIVE_COUNT']}", f"FAIL_T10_NEGATIVE_COUNT={summary['FAIL_T10_NEGATIVE_COUNT']}", f"FAIL_NO_EXPANSION_COUNT={summary['FAIL_NO_EXPANSION_COUNT']}", f"FAIL_LARGE_MAE_COUNT={summary['FAIL_LARGE_MAE_COUNT']}", f"FAIL_BREAKOUT_REVERSAL_COUNT={summary['FAIL_BREAKOUT_REVERSAL_COUNT']}", "", "## Safety and acceptance boundary", "", "A_OWNER_REVIEW_PACK_CREATED=YES", "B_OWNER_REVIEW_PACK_CREATED=YES", "MASTER_OWNER_REVIEW_PACK_CREATED=YES", "NEW_FEATURE_DISCOVERY_EXECUTED=NO", "NEW_THRESHOLD_SEARCH_EXECUTED=NO", "MULTIVARIATE_MODEL_EXECUTED=NO", "STRATEGY_RULE_CREATED=NO", "A_SETUP_ACCEPTED=NO", "B_SETUP_ACCEPTED=NO", "A1_CHANGED=NO", "A2_CHANGED=NO", "DATABASE_MUTATION=NO", "PRODUCTION_MUTATION=NO", "WS1_CHANGED=NO", "WS2_CHANGED=NO", "WS4_CHANGED=NO", "NEXT_TASK_CHANGED=NO", "PUSH=NO", "DEPLOY=NO", "RELEASE=NO", "READY_FOR_OWNER_HUMAN_FALSE_FRIEND_REVIEW=YES_WITH_BOUNDED_LIMITATIONS", "", "## Canonical lifecycle", "", "CANONICAL_STATUS=READY_FOR_CANONICAL_RECONCILIATION", "RELEASE_STATUS=NOT_APPLICABLE_RESEARCH_ONLY", "PRODUCTION_VERIFICATION=NOT_RUN_NOT_APPLICABLE", "CANONICAL_RECONCILIATION_DISPOSITION=READY_FOR_CANONICAL_RECONCILIATION", "REPOSITORY_HYGIENE_STATUS=ACTION_REQUIRED_OWNER_DIRTY_STATE_PRESERVED", "TEST_COUNT_DELTA_STATUS=NOT_APPLICABLE_DOC_RESEARCH_ONLY", "", "## Created artifacts", "", *[f"- `{file}`" for file in files], "", "This is a human review handoff only. It does not answer the A/B hypothesis, freeze a setup, create Core V0, or start another research task."]
    return "\n".join(lines)


def main() -> None:
    started = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-canonical-head", default=None)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source_paths = {key: root / rel for key, rel in EXPECTED_SOURCE.items()}
    out = root / OUT_REL
    docs = root / DOC_REL
    out.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)

    required_resolution = {"root": root.is_dir(), "skill_path": SKILL_PATH.is_file(), **{key: path.is_file() and path.stat().st_size > 0 for key, path in source_paths.items()}}
    missing = [key for key, ok in required_resolution.items() if not ok]
    if missing:
        raise SystemExit("BLOCKED_EXISTING_ARTIFACT_INSUFFICIENT:" + ",".join(missing))
    source_head = args.source_canonical_head or git_head(root)
    source_summary = read_json(source_paths["source_run_summary"])
    inventory_rows = inventory(root)
    write_json(out / "ws3-ab-false-friend-source-artifact-inventory.json", {"TASK_ID": TASK_ID, "source_task": SOURCE_TASK, "artifacts": inventory_rows, "SOURCE_ARTIFACTS_SUFFICIENT": all(row["status"] in {"FOUND", "NOT_REQUIRED"} for row in inventory_rows)})
    write_text(out / "ws3-ab-false-friend-source-artifact-inventory.md", source_inventory_markdown(inventory_rows))
    preflight = run_preflight(root, source_paths, out)
    if args.preflight_only:
        return

    matched_rows = read_csv(source_paths["matched_control_panel"])
    target_ids = {row["successful_anchor_id"] for row in matched_rows} | {row["control_anchor_id"] for row in matched_rows}
    raw_lookup: dict[str, dict[str, str]] = {}
    with source_paths["raw_anchor_panel"].open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("anchor_id") in target_ids:
                raw_lookup[row["anchor_id"]] = row
    feature_lookup: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
    priority = STRATUM_RANK
    with source_paths["pre_event_feature_panel"].open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            event_id = row.get("event_id", "")
            anchor_id = event_id.rsplit(":", 1)[-1]
            if anchor_id not in target_ids:
                continue
            relative_day = int(number(row.get("relative_day")) or 0)
            compact = {key: row.get(key, UNAVAILABLE) for key in ["instrument_id", "stock_code", "market", "anchor_date", "stratum", "event_type", "pit_status", "source_lineage", "source_observation_id", "feature_status_summary", *["feature_" + feature for feature in FEATURES]]}
            compact = {key.removeprefix("feature_"): value for key, value in compact.items()}
            existing = feature_lookup[anchor_id].get(relative_day)
            if existing is None or priority.get(row.get("stratum", ""), 99) < priority.get(existing.get("stratum", ""), 99):
                feature_lookup[anchor_id][relative_day] = compact

    success_source: dict[str, dict[str, str]] = {}
    control_source: dict[str, dict[str, str]] = {}
    for row in sorted(matched_rows, key=lambda item: (STRATUM_RANK.get(item.get("stratum", ""), 99), item.get("successful_anchor_date", ""), item.get("successful_anchor_id", ""))):
        success_source.setdefault(row["successful_anchor_id"], row)
        control_source.setdefault(row["control_anchor_id"], row)
    success_records = {aid: anchor_record(aid, "SUCCESS", row, feature_lookup, raw_lookup) for aid, row in success_source.items()}
    control_records = {aid: anchor_record(aid, "CONTROL", row, feature_lookup, raw_lookup) for aid, row in control_source.items()}

    a_pool: list[tuple[dict[str, Any], dict[str, str]]] = []
    b_pool: list[tuple[dict[str, Any], dict[str, str]]] = []
    for aid, record in control_records.items():
        match = control_source[aid]
        failure = failure_labels(match, raw_lookup.get(aid))
        if not failure["labels"] or record.get("pit_status") not in {"PIT_SAFE", UNAVAILABLE}:
            continue
        if record["components"]["A"]["component_count"] >= 2:
            a_pool.append((record, match))
        if record["components"]["B"]["component_count"] >= 2:
            b_pool.append((record, match))
    a_selected_base = spread_select(a_pool, 15, setup_letter="A")
    a_selected_ids = {item[0]["anchor_id"] for item in a_selected_base}
    b_selected_base = spread_select(b_pool, 15, a_selected_ids, setup_letter="B")
    if len(b_selected_base) < 15:
        b_selected_base = spread_select(b_pool, 15, setup_letter="B")

    def make_payloads(setup: str, selected: list[tuple[dict[str, Any], dict[str, str]]]) -> list[dict[str, Any]]:
        payloads = []
        for rank, (candidate, match) in enumerate(selected, 1):
            comparator = choose_comparator(setup, candidate, match, success_records)
            payloads.append(candidate_payload(setup, candidate, match, comparator, rank, "Deterministic component-count descending order with market/date/instrument spread; no future-outcome optimization or rematching."))
        return payloads

    a_payloads = make_payloads("A", a_selected_base)
    b_payloads = make_payloads("B", b_selected_base)
    all_payloads = a_payloads + b_payloads
    manifest_records = []
    for payload in all_payloads:
        manifest_records.append(payload)
    manifest_path = out / "ws3-ab-false-friend-intermediate-manifest.jsonl"
    manifest_hash = jsonl_write(manifest_path, manifest_records)
    manifest_meta = {
        "TASK_ID": TASK_ID,
        "architecture_equivalent": "deterministic JSONL intermediate manifest",
        "source_task": SOURCE_TASK,
        "source_review_task": REVIEW_TASK,
        "schema_version": "ws3-ab-false-friend-intermediate-manifest.v1",
        "record_count": len(manifest_records),
        "sha256": manifest_hash,
        "fields": ["candidate_id", "setup_hypothesis", "candidate", "source_match", "failure_labels", "comparator", "selection_rank", "selection_note"],
        "contains_only_selected_cases_and_comparators": True,
        "report_generation_must_consume_this_manifest": True,
        "large_source_panels_rescanned_after_manifest": False,
    }
    write_json(out / "ws3-ab-false-friend-intermediate-manifest-meta.json", manifest_meta)
    # From this point forward, report generation consumes only the intermediate manifest.
    report_rows = jsonl_read(manifest_path)
    a_rows = [row for row in report_rows if row["setup_hypothesis"] == "A_LIKE"]
    b_rows = [row for row in report_rows if row["setup_hypothesis"] == "B_LIKE"]
    write_csv(out / "ws3-a-like-false-friend-candidates.csv", [candidate_csv_row(row) for row in a_rows], CANDIDATE_FIELDS)
    write_csv(out / "ws3-b-like-false-friend-candidates.csv", [candidate_csv_row(row) for row in b_rows], CANDIDATE_FIELDS)
    write_text(out / "ws3-a-success-vs-false-friend-pairs.md", pair_markdown("A", a_rows))
    write_text(out / "ws3-b-success-vs-false-friend-pairs.md", pair_markdown("B", b_rows))
    cards_md, cards_json = case_cards(report_rows)
    write_text(out / "ws3-ab-false-friend-case-cards.md", cards_md)
    write_json(out / "ws3-ab-false-friend-case-cards.json", {"schema_version": "ws3-ab-false-friend-case-cards.v1", "source_task": SOURCE_TASK, "cases": cards_json})
    write_text(out / "ws3-ab-human-review-question-sheet.md", question_sheet())

    a_comparators = [row for row in a_rows if row.get("comparator")]
    b_comparators = [row for row in b_rows if row.get("comparator")]
    summary = build_summary(source_summary, inventory_rows, a_pool, b_pool, a_rows, b_rows, a_comparators, b_comparators, manifest_hash, time.perf_counter() - started, source_head)
    write_json(out / "ws3-ab-false-friend-summary.json", summary)
    supporting_files = sorted(path.name for path in out.iterdir() if path.is_file() and path.name != "WS3-AB-FALSE-FRIEND-OWNER-REVIEW-PACK.md")
    write_text(out / "WS3-AB-FALSE-FRIEND-OWNER-REVIEW-PACK.md", master_markdown(summary, supporting_files, a_rows, b_rows))
    report_files = sorted(path.name for path in out.iterdir() if path.is_file())
    write_text(docs / "formal-closure-report.md", formal_report(summary, report_files))
    summary["TASK_FINAL_STATUS"] = "COMPLETE_PASS" if summary["A_FALSE_FRIEND_COUNT"] > 0 and summary["B_FALSE_FRIEND_COUNT"] > 0 else "COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS"
    write_json(out / "ws3-ab-false-friend-summary.json", summary)
    write_text(docs / "formal-closure-report.md", formal_report(summary, report_files))


if __name__ == "__main__":
    main()

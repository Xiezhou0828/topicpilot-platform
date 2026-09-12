"""WS3 A2 outcome reconstruction and failure-attribution audit.

This is a research-only, read-only consumer of the frozen A2 event surface and
the accepted daily OHLCV surface.  It deliberately keeps the MA60-above
eligibility boundary, does not fit thresholds, does not train a model, and
never mutates production or the A2 strategy contract.

The script is intentionally fail-closed around corporate actions.  The shared
data foundation is marked UNKNOWN_RAW_ONLY; a discontinuity or a covered
corporate-action event suppresses path metrics for that event instead of
interpreting a potentially artificial loss or excursion.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from datetime import date
from pathlib import Path
from typing import Any

import psycopg

TASK_ID = "TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821"
SOURCE_A2_TASK = "TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820"
OWNER_AUDIT_TASK = "TASK-WS3-A2-HISTORICAL-LABEL-AUDIT-AND-OWNER-REVIEW-HANDOFF-20260821"
STRUCTURAL_TASK = "TASK-WS3-A-STRUCTURAL-ELIGIBILITY-RECONSTRUCTION-AND-FALSE-POSITIVE-SEPARATION-20260821"
SOURCE_START = date(2024, 8, 13)
SOURCE_END = date(2026, 8, 13)
HORIZONS = tuple(range(1, 11))
SUMMARY_HORIZONS = (1, 3, 5, 10)
PRICE_FLOOR = 20.0
VOLUME_FLOOR_LOTS = 500.0
VOLUME_FLOOR_SHARES = VOLUME_FLOOR_LOTS * 1000.0
DISCONTINUITY_THRESHOLD = 0.20
DEFAULT_DATABASE_URL = "postgresql+psycopg://topicpilot:topicpilot_local_only@localhost:5432/topicpilot"

PANEL_REL = Path(
    "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/"
    "ws3-p2e-a2-expanded-event-panel.csv"
)
OWNER_DIR_REL = Path("reports/TASK-WS3-A2-HISTORICAL-LABEL-AUDIT-AND-OWNER-REVIEW-HANDOFF-20260821")
OWNER_MASTER_REL = OWNER_DIR_REL / "ws3-a2-historical-label-audit-master.csv"
OWNER_PACK_REL = OWNER_DIR_REL / "WS3-A2-HISTORICAL-LABEL-OWNER-REVIEW-PACK.md"
OWNER_FORMAL_REL = OWNER_DIR_REL / "formal-closure-report.md"
STRUCTURAL_FORMAL_REL = Path(
    "docs/reports/TASK-WS3-A-STRUCTURAL-ELIGIBILITY-RECONSTRUCTION-AND-FALSE-POSITIVE-SEPARATION-20260821/"
    "formal-closure-report.md"
)
STRUCTURAL_SUMMARY_REL = Path(
    "reports/TASK-WS3-A-STRUCTURAL-ELIGIBILITY-RECONSTRUCTION-AND-FALSE-POSITIVE-SEPARATION-20260821/"
    "ws3-a-structural-eligibility-run-summary.json"
)
SOURCE_RUN_SUMMARY_REL = Path(
    "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/"
    "ws3-p2e-a2-run-summary.json"
)
MARKET_STABILITY_REL = Path(
    "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/"
    "ws3-p2e-a2-market-stability.csv"
)
CA_DATASET_REL = Path(
    "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/REC-A1-CA-EVENTS-V0.json"
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk.replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def _sha_payload(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _day(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if str(value).lower() in {"true", "1", "yes", "pass"}:
        return True
    if str(value).lower() in {"false", "0", "no", "fail"}:
        return False
    return None


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (date,)):
        return value.isoformat()
    if isinstance(value, (list, tuple, set, frozenset)):
        return "|".join(str(_csv_value(item)) for item in value)
    return value


def _write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    materialised = list(rows)
    fields: list[str] = []
    for row in materialised:
        for field in row:
            if field not in fields:
                fields.append(field)
    if not fields:
        fields = ["status"]
        materialised = [{"status": "NO_ROWS"}]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in materialised:
            writer.writerow({field: _csv_value(row.get(field)) for field in fields})
    return len(materialised)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _median(values: Iterable[float]) -> float | None:
    cleaned = sorted(value for value in values if value is not None and math.isfinite(value))
    return statistics.median(cleaned) if cleaned else None


def _stats(values: Iterable[float]) -> dict[str, Any]:
    cleaned = sorted(value for value in values if value is not None and math.isfinite(value))
    if not cleaned:
        return {"n": 0, "mean": None, "median": None, "p25": None, "p75": None, "positive_rate": None}
    return {
        "n": len(cleaned),
        "mean": statistics.fmean(cleaned),
        "median": statistics.median(cleaned),
        "p25": cleaned[int((len(cleaned) - 1) * 0.25)],
        "p75": cleaned[int((len(cleaned) - 1) * 0.75)],
        "positive_rate": sum(value > 0 for value in cleaned) / len(cleaned),
    }


def _root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def _git_head(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _safe_path(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _load_source_artifacts(source_root: Path) -> dict[str, Any]:
    paths = {
        "owner_review_pack": OWNER_PACK_REL,
        "owner_master_csv": OWNER_MASTER_REL,
        "owner_formal_closure": OWNER_FORMAL_REL,
        "structural_formal_closure": STRUCTURAL_FORMAL_REL,
        "structural_run_summary": STRUCTURAL_SUMMARY_REL,
        "a2_source_run_summary": SOURCE_RUN_SUMMARY_REL,
        "a2_event_panel": PANEL_REL,
        "market_stability": MARKET_STABILITY_REL,
        "corporate_action_dataset": CA_DATASET_REL,
    }
    result: dict[str, Any] = {}
    for key, relative in paths.items():
        path = _safe_path(source_root, relative)
        result[key] = {
            "path": str(path),
            "relative_path": str(relative).replace("\\", "/"),
            "exists": path.exists(),
            "sha256": _sha(path) if path.exists() else None,
        }
    return result


def _panel_rows(path: Path) -> list[dict[str, str]]:
    rows = _read_csv(path)
    required = {"event_id", "instrument_id", "stock_code", "market", "signal_date", "a2_close", "volume"}
    missing = sorted(required - set(rows[0]) if rows else required)
    if missing:
        raise ValueError(f"A2 panel missing required headers: {missing}")
    return rows


def _owner_key(row: Mapping[str, Any]) -> tuple[str, str] | None:
    code = None
    for key in ("ticker", "stock_code", "stock", "code", "instrument_code"):
        if row.get(key):
            code = str(row[key]).strip()
            break
    day = None
    for key in ("anchor_date", "signal_date", "a2_date", "date"):
        if row.get(key):
            day = str(row[key]).strip()[:10]
            break
    return (code, day) if code and day else None


def _load_owner_cases(source_root: Path, panel_by_key: Mapping[tuple[str, str], Mapping[str, str]]) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    path = _safe_path(source_root, OWNER_MASTER_REL)
    rows = _read_csv(path)
    cases: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for index, row in enumerate(rows, start=1):
        key = _owner_key(row)
        owner_headers = [
            header for header in row if "owner" in header.lower() and "sha" not in header.lower()
        ]
        owner_values = {header: row.get(header, "") for header in owner_headers if row.get(header, "")}
        panel = panel_by_key.get(key or ("", ""), {})
        record = {
            "review_order": index,
            "case_id": row.get("case_id") or f"OWNER_CASE_{index:02d}",
            "stock_code": key[0] if key else "",
            "anchor_date": key[1] if key else "",
            "sample_stratum": row.get("sample_stratum", ""),
            "historical_outcome_label_or_proxy": row.get("historical_outcome_label_or_proxy", ""),
            "owner_label": "|".join(f"{key}={value}" for key, value in owner_values.items()) or None,
            "owner_label_source": "OWNER_ARTIFACT" if owner_values else "NOT_AVAILABLE_IN_REPOSITORY_ARTIFACT",
            "owner_fields_blank": not bool(owner_values),
            "panel_event_id": panel.get("event_id"),
            "panel_match": bool(panel),
            "reconciliation_status": "RECONCILED_SOURCE_ROW_OWNER_LABEL_MISSING" if panel and not owner_values else ("RECONCILED_OWNER_LABEL_PRESENT" if panel else "OWNER_CASE_NOT_FOUND_IN_A2_PANEL"),
        }
        cases.append(record)
        if key:
            by_key[key] = record
    return cases, by_key


def _query_daily_surface(database_url: str) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    query_base = """
        SELECT d.instrument_id, d.instrument_code, d.market_code, d.trade_date,
               d.open, d.high, d.low, d.close, d.canonical_observation_id
        FROM topicpilot.vw_daily_market_observations d
        JOIN topicpilot.canonical_observations co ON co.id = d.canonical_observation_id
        JOIN topicpilot.instruments i ON i.id = d.instrument_id
        JOIN topicpilot.markets m ON m.id = i.market_id
        JOIN topicpilot.market_data_sources mds ON mds.id = d.source_id
        WHERE co.family_code = 'PRICE'
          AND d.quality_state = 'ACCEPTED'
          AND mds.observation_semantics = 'DAILY_BAR'
          AND d.trade_date >= %s AND d.trade_date <= %s
          AND NOT EXISTS (
              SELECT 1 FROM topicpilot.reference_instrument_lifecycles lifecycle
              WHERE lifecycle.instrument_id = co.instrument_id
                AND lifecycle.status_code IN ('DELISTED', 'SUSPENDED', 'TERMINATED')
                AND lifecycle.effective_from <= d.trade_date
                AND (lifecycle.effective_to IS NULL OR lifecycle.effective_to >= d.trade_date)
          )
        ORDER BY d.instrument_id, d.trade_date, co.observed_at, co.ordering_key, co.id
    """
    dsn = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(query_base, (SOURCE_START, SOURCE_END))
        for row in cursor:
            grouped[str(row[0])].append(
                {
                    "instrument_id": str(row[0]),
                    "stock_code": str(row[1]),
                    "market": str(row[2]),
                    "trade_date": _day(row[3]),
                    "open": _num(row[4]),
                    "high": _num(row[5]),
                    "low": _num(row[6]),
                    "close": _num(row[7]),
                    "observation_id": str(row[8]),
                    "volume": None,
                }
            )
    for rows in grouped.values():
        rows.sort(key=lambda item: item["trade_date"] or date.min)
    return grouped, {
        "source": "topicpilot.vw_daily_market_observations",
        "accepted_price_rows": sum(len(rows) for rows in grouped.values()),
        "instrument_count": len(grouped),
        "volume_query_status": "NOT_SELECTED_FROM_PRICE_VIEW;ANCHOR_VOLUME_FROM_FROZEN_A2_PANEL",
        "volume_unit_status": "SHARES_INFERRED_FROM_CANONICAL_PROVIDER_CONTRACT",
    }


def _load_ca_index(path: Path) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    if not path.exists():
        return {}
    payload = _read_json(path)
    index: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            code = value.get("instrument_code")
            market = value.get("market_code")
            effective = value.get("primary_effective_date")
            if code and market and effective:
                index[(str(market), str(code), str(effective)[:10])].append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return index


def _bars_by_date(rows: list[dict[str, Any]]) -> dict[date, dict[str, Any]]:
    return {row["trade_date"]: row for row in rows if row.get("trade_date")}


def _discontinuity_reasons(rows: list[dict[str, Any]], index: int) -> list[str]:
    reasons: list[str] = []
    start = max(1, index)
    end = min(len(rows) - 1, index + 10)
    for current_index in range(start, end + 1):
        previous = rows[current_index - 1]
        current = rows[current_index]
        previous_close = _num(previous.get("close"))
        current_close = _num(current.get("close"))
        current_open = _num(current.get("open"))
        if previous_close and current_close and previous_close > 0:
            close_gap = current_close / previous_close - 1.0
            if abs(close_gap) >= DISCONTINUITY_THRESHOLD:
                reasons.append(
                    f"CLOSE_JUMP:{previous['trade_date']}->{current['trade_date']}:{close_gap:.6f}"
                )
            if current_open is not None:
                open_gap = current_open / previous_close - 1.0
                if abs(open_gap) >= DISCONTINUITY_THRESHOLD:
                    reasons.append(
                        f"OPEN_GAP:{previous['trade_date']}->{current['trade_date']}:{open_gap:.6f}"
                    )
    return reasons


def _path_metrics(rows: list[dict[str, Any]], index: int, horizon: int, anchor_close: float) -> dict[str, Any]:
    future = rows[index + 1 : index + horizon + 1]
    if len(future) < horizon:
        return {"status": "UNAVAILABLE_NOT_MATURED", "target_date": None, "endpoint_return": None, "mfe": None, "mae": None, "mfe_timing_session": None, "mae_timing_session": None, "path_ordering": None, "mfe_before_mae": None}
    if not anchor_close or anchor_close <= 0:
        return {"status": "INVALID_ANCHOR_PRICE", "target_date": None, "endpoint_return": None, "mfe": None, "mae": None, "mfe_timing_session": None, "mae_timing_session": None, "path_ordering": None, "mfe_before_mae": None}
    closes = [_num(item.get("close")) for item in future]
    highs = [_num(item.get("high")) for item in future]
    lows = [_num(item.get("low")) for item in future]
    if any(value is None for value in closes + highs + lows):
        return {"status": "INCOMPLETE_OHLC_PATH", "target_date": future[-1].get("trade_date"), "endpoint_return": None, "mfe": None, "mae": None, "mfe_timing_session": None, "mae_timing_session": None, "path_ordering": None, "mfe_before_mae": None}
    assert all(value is not None for value in closes + highs + lows)
    max_high = max(highs)
    min_low = min(lows)
    mfe_index = highs.index(max_high) + 1
    mae_index = lows.index(min_low) + 1
    if mfe_index < mae_index:
        ordering = "MFE_BEFORE_MAE"
    elif mae_index < mfe_index:
        ordering = "MAE_BEFORE_MFE"
    else:
        ordering = "SAME_SESSION"
    return {
        "status": "COMPLETE_RAW_PATH",
        "target_date": future[-1].get("trade_date"),
        "endpoint_return": closes[-1] / anchor_close - 1.0,
        "mfe": max_high / anchor_close - 1.0,
        "mae": min_low / anchor_close - 1.0,
        "mfe_timing_session": mfe_index,
        "mae_timing_session": mae_index,
        "path_ordering": ordering,
        "mfe_before_mae": ordering == "MFE_BEFORE_MAE",
    }


def _preanchor_features(rows: list[dict[str, Any]], index: int, anchor_close: float, extension_pct: float | None) -> dict[str, Any]:
    closes = [_num(item.get("close")) for item in rows[: index + 1]]
    valid = [value for value in closes if value is not None and value > 0]

    def ma(window: int) -> float | None:
        window_values = closes[max(0, len(closes) - window) :]
        clean = [value for value in window_values if value is not None]
        return statistics.fmean(clean) if len(clean) == window else None

    def prior_return(window: int) -> float | None:
        if index < window:
            return None
        prior = _num(rows[index - window].get("close"))
        return anchor_close / prior - 1.0 if prior and prior > 0 else None

    ma20 = ma(20)
    ma60 = ma(60)
    pre5 = prior_return(5)
    pre10 = prior_return(10)
    pre20 = prior_return(20)
    pre40 = prior_return(40)
    return {
        "close_vs_ma20": anchor_close / ma20 - 1.0 if ma20 else None,
        "close_vs_ma60_recomputed": anchor_close / ma60 - 1.0 if ma60 else None,
        "prior_5d_return": pre5,
        "prior_10d_return": pre10,
        "prior_20d_return": pre20,
        "prior_40d_return": pre40,
        "pre_trigger_acceleration_proxy": pre5 - (pre20 / 4.0) if pre5 is not None and pre20 is not None else None,
        "distance_from_consolidation_base": None,
        "trigger_acceleration_status": "DESCRIPTIVE_PRETRIGGER_PROXY_ONLY",
        "base_distance_status": "UNAVAILABLE_NO_FROZEN_BASE_DEFINITION",
        "preanchor_observation_count": len(valid),
        "extension_pct_from_frozen_reference": extension_pct,
    }


def _panel_outcome_value(row: Mapping[str, str], horizon: int, metric: str) -> float | None:
    return _num(row.get(f"observable_t{horizon}_{metric}"))


def _reconstruct_events(
    panel: list[dict[str, str]],
    bars: Mapping[str, list[dict[str, Any]]],
    ca_index: Mapping[tuple[str, str, str], list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    reconciliation: list[dict[str, Any]] = []
    panel_mismatches: Counter[str] = Counter()
    missing_instrument = 0
    missing_anchor = 0
    raw_path_complete_events = 0
    suppressed_events = 0

    for row in panel:
        event_id = row.get("event_id", "")
        instrument_id = row.get("instrument_id", "")
        signal_date = _day(row.get("signal_date"))
        raw_rows = list(bars.get(instrument_id, []))
        if not raw_rows:
            missing_instrument += 1
        index = next((i for i, item in enumerate(raw_rows) if item.get("trade_date") == signal_date), None)
        if index is None:
            missing_anchor += 1
        panel_close = _num(row.get("a2_close"))
        anchor_close = raw_rows[index].get("close") if index is not None else panel_close
        if anchor_close is None or anchor_close <= 0:
            anchor_close = panel_close
        extension_pct = _num(row.get("extension_pct"))
        if extension_pct is None:
            reference = _num(row.get("reference"))
            extension_pct = panel_close / reference - 1.0 if panel_close and reference else None
        discontinuity_reasons = _discontinuity_reasons(raw_rows, index) if index is not None else ["MISSING_RAW_ANCHOR"]
        ca_dates = []
        if signal_date:
            for candidate in [signal_date] + [item.get("trade_date") for item in raw_rows[index + 1 : index + 11]] if index is not None else [signal_date]:
                if candidate is None:
                    continue
                key = (str(row.get("market", "")), str(row.get("stock_code", "")), candidate.isoformat())
                if key in ca_index:
                    ca_dates.append(candidate.isoformat())
        target_case = str(row.get("stock_code")) == "2327" and str(row.get("signal_date"))[:10] == "2025-08-05"
        suppression_reasons = list(discontinuity_reasons)
        if ca_dates:
            suppression_reasons.append("CORPORATE_ACTION_CATALOG_MATCH")
        if target_case:
            suppression_reasons.append("TARGET_CASE_2327_ADJUSTMENT_UNCONFIRMED")
        suppress = bool(suppression_reasons)
        if suppress:
            suppressed_events += 1
        if index is not None and len(raw_rows) >= index + 11:
            raw_path_complete_events += 1
        raw_feature_values = _preanchor_features(raw_rows, index, anchor_close, extension_pct) if index is not None and anchor_close else {}
        event_outcomes: dict[int, dict[str, Any]] = {}
        for horizon in HORIZONS:
            metrics = _path_metrics(raw_rows, index, horizon, anchor_close) if index is not None and anchor_close else {"status": "UNAVAILABLE_RAW_ANCHOR", "target_date": None, "endpoint_return": None, "mfe": None, "mae": None, "mfe_timing_session": None, "mae_timing_session": None, "path_ordering": None, "mfe_before_mae": None}
            if suppress and metrics["status"] == "COMPLETE_RAW_PATH":
                metrics = {**metrics, "status": "SUPPRESSED_CORPORATE_ACTION_OR_DISCONTINUITY", "endpoint_return": None, "mfe": None, "mae": None, "mfe_timing_session": None, "mae_timing_session": None, "path_ordering": None, "mfe_before_mae": None}
            event_outcomes[horizon] = metrics
            panel_forward = _panel_outcome_value(row, horizon, "forward_return") if horizon in SUMMARY_HORIZONS else None
            panel_mfe = _panel_outcome_value(row, horizon, "mfe") if horizon in SUMMARY_HORIZONS else None
            panel_mae = _panel_outcome_value(row, horizon, "mae") if horizon in SUMMARY_HORIZONS else None
            if horizon in SUMMARY_HORIZONS and metrics["status"] == "COMPLETE_RAW_PATH":
                for metric, panel_value, raw_value in (("forward_return", panel_forward, metrics["endpoint_return"]), ("mfe", panel_mfe, metrics["mfe"]), ("mae", panel_mae, metrics["mae"])):
                    if panel_value is not None and raw_value is not None and abs(panel_value - raw_value) > 1e-8:
                        panel_mismatches[metric] += 1
            outcomes.append(
                {
                    "event_id": event_id,
                    "instrument_id": instrument_id,
                    "stock_code": row.get("stock_code"),
                    "market": row.get("market"),
                    "signal_date": signal_date,
                    "a2_close": panel_close,
                    "volume_shares": _num(row.get("volume")),
                    "volume_lots": _num(row.get("volume")) / 1000.0 if _num(row.get("volume")) is not None else None,
                    "volume_unit_status": "SHARES_CANONICAL_PROVIDER_CONTRACT" if _num(row.get("volume")) is not None else "MISSING",
                    "extension_pct": extension_pct,
                    "entry_extension_band": row.get("entry_extension_band"),
                    "horizon": horizon,
                    "horizon_status": metrics["status"],
                    "target_date": metrics["target_date"],
                    "endpoint_return": metrics["endpoint_return"],
                    "mfe": metrics["mfe"],
                    "mae": metrics["mae"],
                    "mfe_timing_session": metrics["mfe_timing_session"],
                    "mae_timing_session": metrics["mae_timing_session"],
                    "path_ordering": metrics["path_ordering"],
                    "mfe_before_mae": metrics["mfe_before_mae"],
                    "source_panel_endpoint_return": panel_forward,
                    "source_panel_mfe": panel_mfe,
                    "source_panel_mae": panel_mae,
                    "source_semantics": "RAW_DAILY_PATH_RECONSTRUCTION" if metrics["status"] == "COMPLETE_RAW_PATH" else "FAIL_CLOSED",
                    "adjustment_state": "UNKNOWN_RAW_ONLY",
                    "suppression_reasons": "|".join(suppression_reasons),
                    "source_lineage_sha256": row.get("source_lineage_sha256"),
                }
            )
        t10 = event_outcomes[10]
        t5 = event_outcomes[5]
        endpoint_t10 = t10.get("endpoint_return")
        source_failure_like = _bool(row.get("descriptive_failure_like_path")) is True
        low_price = _num(row.get("a2_close")) is not None and _num(row.get("a2_close")) < PRICE_FLOOR
        volume_shares = _num(row.get("volume"))
        low_liquidity = volume_shares is not None and volume_shares < VOLUME_FLOOR_SHARES
        late_candidate = row.get("entry_extension_band") in {"GT_3_TO_5PCT", "GT_5PCT"}
        if suppress:
            source_class = "CORPORATE_ACTION_OR_PRICE_DATA_QUALITY_SUPPRESSED"
        elif late_candidate:
            source_class = "LATE_EXTENDED_CANDIDATE_SOURCE_DESCRIPTIVE"
        elif source_failure_like:
            source_class = "GENUINE_CLEAN_FALSE_BREAKOUT_CANDIDATE_SOURCE_DESCRIPTIVE"
        elif t10.get("mfe") is not None and t10.get("mfe") > 0:
            source_class = "SUCCESSFUL_TRADABLE_POSITIVE_EXCURSION_CANDIDATE_SOURCE_DESCRIPTIVE"
        else:
            source_class = "AMBIGUOUS_SOURCE_ONLY"
        event = {
            "event_id": event_id,
            "instrument_id": instrument_id,
            "stock_code": row.get("stock_code"),
            "market": row.get("market"),
            "signal_date": signal_date,
            "a2_close": _num(row.get("a2_close")),
            "volume_shares": volume_shares,
            "volume_lots": volume_shares / 1000.0 if volume_shares is not None else None,
            "volume_unit_status": "SHARES_CANONICAL_PROVIDER_CONTRACT" if volume_shares is not None else "MISSING",
            "ma60": _num(row.get("ma60")),
            "distance_from_ma60": _num(row.get("distance_from_ma60")),
            "reference": _num(row.get("reference")),
            "extension_pct": extension_pct,
            "entry_extension_band": row.get("entry_extension_band"),
            "path_category": row.get("path_category"),
            "source_failure_like_path": source_failure_like,
            "late_extended_candidate_source_descriptive": late_candidate,
            "low_price_candidate": low_price,
            "low_liquidity_candidate": low_liquidity,
            "corporate_action_state": "SUPPRESSED_UNRESOLVED" if suppress else "NO_MATCH_BUT_ADJUSTMENT_UNKNOWN",
            "corporate_action_match_dates": "|".join(ca_dates),
            "discontinuity_reasons": "|".join(discontinuity_reasons),
            "target_case_2327": target_case,
            "outcome_suppressed": suppress,
            "source_only_attribution": source_class,
            "endpoint_t5": t5.get("endpoint_return"),
            "mfe_t5": t5.get("mfe"),
            "mae_t5": t5.get("mae"),
            "endpoint_t10": endpoint_t10,
            "mfe_t10": t10.get("mfe"),
            "mae_t10": t10.get("mae"),
            "path_ordering_t10": t10.get("path_ordering"),
            "mfe_before_mae_t10": t10.get("mfe_before_mae"),
            **raw_feature_values,
        }
        events.append(event)
        reconciliation.append(
            {
                "event_id": event_id,
                "stock_code": row.get("stock_code"),
                "signal_date": signal_date,
                "source_panel_row": True,
                "raw_instrument_found": bool(raw_rows),
                "raw_anchor_found": index is not None,
                "raw_path_complete_h10": index is not None and len(raw_rows) >= index + 11,
                "panel_to_raw_anchor_close_match": panel_close is not None and anchor_close is not None and abs(panel_close - anchor_close) <= 1e-8,
                "panel_summary_mismatch_count": sum(panel_mismatches.values()),
            }
        )
    return events, outcomes, reconciliation, {
        "panel_rows": len(panel),
        "missing_raw_instrument_count": missing_instrument,
        "missing_raw_anchor_count": missing_anchor,
        "raw_path_complete_h10_event_count": raw_path_complete_events,
        "suppressed_event_count": suppressed_events,
        "panel_summary_mismatch_counts": dict(panel_mismatches),
        "discontinuity_threshold": DISCONTINUITY_THRESHOLD,
    }


def _attribution_rows(events: list[dict[str, Any]], owner_by_key: Mapping[tuple[str, str], Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        key = (str(event.get("stock_code", "")), str(event.get("signal_date", "")))
        owner = owner_by_key.get(key, {})
        owner_label = owner.get("owner_label")
        owner_status = "OWNER_LABEL_AVAILABLE" if owner_label else "OWNER_LABEL_UNAVAILABLE"
        if event.get("outcome_suppressed"):
            primary = "CORPORATE_ACTION_OR_PRICE_ADJUSTMENT_DATA_QUALITY"
        elif event.get("late_extended_candidate_source_descriptive"):
            primary = "LATE_EXTENDED_FAILURE_CANDIDATE"
        elif event.get("low_price_candidate") or event.get("low_liquidity_candidate"):
            primary = "UNIVERSE_QUALITY_CANDIDATE"
        elif event.get("source_failure_like_path"):
            primary = "GENUINE_CLEAN_FALSE_BREAKOUT_CANDIDATE"
        elif event.get("mfe_t10") is not None and event.get("mfe_t10") > 0:
            primary = "SUCCESSFUL_TRADABLE_POSITIVE_EXCURSION_CANDIDATE"
        else:
            primary = "AMBIGUOUS"
        rows.append(
            {
                "event_id": event.get("event_id"),
                "stock_code": event.get("stock_code"),
                "signal_date": event.get("signal_date"),
                "owner_label": owner_label,
                "owner_label_source": owner.get("owner_label_source", "NOT_AVAILABLE_IN_REPOSITORY_ARTIFACT"),
                "owner_status": owner_status,
                "primary_attribution": primary,
                "source_only_attribution": event.get("source_only_attribution"),
                "market_regime_shock_candidate": "UNKNOWN_NO_PIT_SAFE_EVIDENCE",
                "low_price_candidate": event.get("low_price_candidate"),
                "low_liquidity_candidate": event.get("low_liquidity_candidate"),
                "late_extended_candidate": event.get("late_extended_candidate_source_descriptive"),
                "source_failure_like_path": event.get("source_failure_like_path"),
                "corporate_action_state": event.get("corporate_action_state"),
                "regime_attribution": "UNKNOWN_NO_PIT_SAFE_INDEX_BREADTH_PEER_DATA",
                "performance_included": "NO" if event.get("outcome_suppressed") else "YES",
                "pattern_learning_negative_evidence": "DO_NOT_MARK_UNTIL_OWNER_AND_REGIME_REVIEW" if event.get("outcome_suppressed") else "UNRESOLVED_REGIME_ATTRIBUTION",
                "endpoint_t10": event.get("endpoint_t10"),
                "mfe_t10": event.get("mfe_t10"),
                "mae_t10": event.get("mae_t10"),
            }
        )
    return rows


def _filter_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    definitions = [
        ("ALL_A2_COHORT", lambda event: True),
        ("PRICE_FLOOR_GE_20", lambda event: event.get("a2_close") is not None and event["a2_close"] >= PRICE_FLOOR),
        ("VOLUME_FLOOR_GE_500_LOTS", lambda event: event.get("volume_shares") is not None and event["volume_shares"] >= VOLUME_FLOOR_SHARES),
        ("PRICE_GE_20_AND_VOLUME_GE_500_LOTS", lambda event: event.get("a2_close") is not None and event["a2_close"] >= PRICE_FLOOR and event.get("volume_shares") is not None and event["volume_shares"] >= VOLUME_FLOOR_SHARES),
    ]
    baseline = events
    rows: list[dict[str, Any]] = []
    for name, predicate in definitions:
        selected = [event for event in events if predicate(event)]
        excluded = [event for event in events if event not in selected]
        t10 = [event.get("endpoint_t10") for event in selected]
        t5 = [event.get("endpoint_t5") for event in selected]
        excluded_t10 = [event.get("endpoint_t10") for event in excluded]
        rows.append(
            {
                "filter_id": name,
                "filter_status": "ABLATION_ONLY_NOT_PRODUCTION_RULE",
                "price_floor": PRICE_FLOOR,
                "volume_floor_lots": VOLUME_FLOOR_LOTS,
                "volume_floor_shares": VOLUME_FLOOR_SHARES,
                "volume_unit_status": "SHARES;TPEx_RAW_LOTS_CONVERTED_TO_SHARES_BY_PROVIDER",
                "retained_event_count": len(selected),
                "excluded_event_count": len(excluded),
                "retained_success_proxy_t10_count": sum(value is not None and value > 0 for value in t10),
                "retained_failure_proxy_t10_count": sum(value is not None and value <= 0 for value in t10),
                "retained_unknown_t10_count": sum(value is None for value in t10),
                "retained_positive_mfe_t10_count": sum(event.get("mfe_t10") is not None and event.get("mfe_t10") > 0 for event in selected),
                "retained_mfe_before_mae_t10_count": sum(event.get("mfe_before_mae_t10") is True for event in selected),
                "retained_source_clean_failure_candidate_count": sum(event.get("source_failure_like_path") is True for event in selected),
                "retained_late_extended_candidate_count": sum(event.get("late_extended_candidate_source_descriptive") is True for event in selected),
                "retained_t10_endpoint_return_mean": _stats(t10).get("mean"),
                "retained_t10_mfe_mean": _stats([event.get("mfe_t10") for event in selected]).get("mean"),
                "retained_t10_mae_mean": _stats([event.get("mae_t10") for event in selected]).get("mean"),
                "retained_t5_endpoint_return_mean": _stats(t5).get("mean"),
                "expectancy_proxy_t10": _stats(t10).get("mean"),
                "excluded_success_proxy_t10_count": sum(value is not None and value > 0 for value in excluded_t10),
                "excluded_failure_proxy_t10_count": sum(value is not None and value <= 0 for value in excluded_t10),
                "excluded_unknown_t10_count": sum(value is None for value in excluded_t10),
                "incremental_excluded_success_cost_vs_all": sum(value is not None and value > 0 for value in excluded_t10) if name != "ALL_A2_COHORT" else 0,
                "incremental_excluded_failure_benefit_vs_all": sum(value is not None and value <= 0 for value in excluded_t10) if name != "ALL_A2_COHORT" else 0,
                "low_price_in_retained": sum(bool(event.get("low_price_candidate")) for event in selected),
                "low_liquidity_in_retained": sum(bool(event.get("low_liquidity_candidate")) for event in selected),
                "corporate_action_suppressed_in_retained": sum(bool(event.get("outcome_suppressed")) for event in selected),
            }
        )
    assert len(baseline) == rows[0]["retained_event_count"]
    return rows


def _extension_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feature_values: dict[str, list[tuple[str, float | None]]] = {
        "close_vs_ma20": [("value", event.get("close_vs_ma20")) for event in events],
        "close_vs_ma60_recomputed": [("value", event.get("close_vs_ma60_recomputed")) for event in events],
        "prior_10d_return": [("value", event.get("prior_10d_return")) for event in events],
        "prior_20d_return": [("value", event.get("prior_20d_return")) for event in events],
        "prior_40d_return": [("value", event.get("prior_40d_return")) for event in events],
        "pre_trigger_acceleration_proxy": [("value", event.get("pre_trigger_acceleration_proxy")) for event in events],
        "extension_pct_from_frozen_reference": [("value", event.get("extension_pct")) for event in events],
    }
    rows: list[dict[str, Any]] = []
    for feature, values in feature_values.items():
        all_values = [value for _, value in values if value is not None]
        positive_values = [event.get(feature) for event in events if event.get("endpoint_t10") is not None and event.get("endpoint_t10") > 0]
        nonpositive_values = [event.get(feature) for event in events if event.get("endpoint_t10") is not None and event.get("endpoint_t10") <= 0]
        rows.append({"feature": feature, "feature_status": "PIT_SAFE_DESCRIPTIVE_NO_THRESHOLD_FIT", "group": "ALL_EVENTS", "n": len(all_values), "missing_count": len(events) - len(all_values), **_stats(all_values)})
        rows.append({"feature": feature, "feature_status": "PIT_SAFE_DESCRIPTIVE_NO_THRESHOLD_FIT", "group": "RAW_T10_POSITIVE_PROXY", "n": len([v for v in positive_values if v is not None]), "missing_count": len(positive_values) - len([v for v in positive_values if v is not None]), **_stats(positive_values)})
        rows.append({"feature": feature, "feature_status": "PIT_SAFE_DESCRIPTIVE_NO_THRESHOLD_FIT", "group": "RAW_T10_NONPOSITIVE_PROXY", "n": len([v for v in nonpositive_values if v is not None]), "missing_count": len(nonpositive_values) - len([v for v in nonpositive_values if v is not None]), **_stats(nonpositive_values)})
    rows.extend(
        [
            {"feature": "distance_from_consolidation_base", "feature_status": "UNAVAILABLE_NO_FROZEN_BASE_DEFINITION", "group": "ALL_EVENTS", "n": 0, "missing_count": len(events), "mean": None, "median": None, "p25": None, "p75": None, "positive_rate": None},
            {"feature": "trigger_acceleration_full_definition", "feature_status": "UNAVAILABLE_AS_FROZEN_FEATURE;PRE_TRIGGER_PROXY_REPORTED_SEPARATELY", "group": "ALL_EVENTS", "n": 0, "missing_count": len(events), "mean": None, "median": None, "p25": None, "p75": None, "positive_rate": None},
        ]
    )
    band_counts: Counter[str] = Counter(str(event.get("entry_extension_band") or "UNAVAILABLE") for event in events)
    for band, count in sorted(band_counts.items()):
        selected = [event for event in events if (event.get("entry_extension_band") or "UNAVAILABLE") == band]
        rows.append({"feature": "entry_extension_band", "feature_status": "SOURCE_BUCKET_COMPARISON_ONLY_NO_THRESHOLD_SELECTION", "group": band, "n": count, "missing_count": 0, "t10_positive_proxy_count": sum(event.get("endpoint_t10") is not None and event.get("endpoint_t10") > 0 for event in selected), "t10_nonpositive_proxy_count": sum(event.get("endpoint_t10") is not None and event.get("endpoint_t10") <= 0 for event in selected), "t10_endpoint_return_mean": _stats([event.get("endpoint_t10") for event in selected]).get("mean"), "t10_mfe_mean": _stats([event.get("mfe_t10") for event in selected]).get("mean"), "t10_mae_mean": _stats([event.get("mae_t10") for event in selected]).get("mean")})
    return rows


def _corporate_action_rows(events: list[dict[str, Any]], source_artifacts: Mapping[str, Any], ca_index: Mapping[tuple[str, str, str], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        if event.get("target_case_2327") or event.get("outcome_suppressed") or event.get("discontinuity_reasons"):
            rows.append(
                {
                    "event_id": event.get("event_id"),
                    "stock_code": event.get("stock_code"),
                    "signal_date": event.get("signal_date"),
                    "target_case_2327": event.get("target_case_2327"),
                    "discontinuity_reasons": event.get("discontinuity_reasons"),
                    "corporate_action_match_dates": event.get("corporate_action_match_dates"),
                    "corporate_action_state": event.get("corporate_action_state"),
                    "outcome_metrics_suppressed": event.get("outcome_suppressed"),
                    "interpretation": "FAIL_CLOSED_NOT_INTERPRETABLE" if event.get("outcome_suppressed") else "NO_SUPPRESSION_BUT_ADJUSTMENT_UNKNOWN",
                }
            )
    rows.insert(
        0,
        {
            "audit_scope": "SUMMARY",
            "source_panel_adjustment_state": "UNKNOWN_RAW_ONLY",
            "raw_ohlcv_not_adjusted_truth": True,
            "corporate_action_catalog_status": "PARTIAL_BOUNDED_OWNER_DATASET",
            "corporate_action_catalog_event_key_count": len(ca_index),
            "catalog_coverage_window": "2026-02-02..2026-08-13; 2327/2025-08-05 outside coverage",
            "discontinuity_threshold": DISCONTINUITY_THRESHOLD,
            "suppressed_event_count": sum(bool(event.get("outcome_suppressed")) for event in events),
            "target_2327_found": sum(bool(event.get("target_case_2327")) for event in events),
            "target_2327_suppressed": sum(bool(event.get("target_case_2327") and event.get("outcome_suppressed")) for event in events),
            "fail_closed_rule": "Do not compute or interpret MFE/MAE/endpoint for unresolved adjustment/discontinuity cases",
            "source_artifact_sha256": source_artifacts.get("corporate_action_dataset", {}).get("sha256"),
        },
    )
    return rows


def _regime_rows(events: list[dict[str, Any]], source_artifacts: Mapping[str, Any]) -> list[dict[str, Any]]:
    focus = [event for event in events if event.get("stock_code") == "3675" and str(event.get("signal_date"))[:10] == "2026-07-06"]
    return [
        {
            "audit_scope": "SUMMARY",
            "event_count": len(events),
            "pit_safe_taiex_index_data": "NOT_AVAILABLE_IN_CURRENT_ARTIFACTS",
            "pit_safe_market_breadth_data": "NOT_AVAILABLE_IN_CURRENT_ARTIFACTS",
            "pit_safe_same_theme_or_industry_panel": "NOT_AVAILABLE_IN_CURRENT_ARTIFACTS",
            "market_stability_artifact_present": source_artifacts.get("market_stability", {}).get("exists"),
            "market_stability_artifact_scope": "aggregate TPE/TWO and temporal summaries; not event-level breadth or peer drawdown",
            "regime_attribution_status": "UNKNOWN",
            "performance_treatment": "INCLUDE_IN_RAW_PERFORMANCE_WHEN_NOT_SUPPRESSED",
            "pattern_learning_treatment": "DO_NOT_MARK_SYSTEMATIC_SHOCK_WITHOUT_PIT_SAFE_EVIDENCE",
        },
        {
            "stock_code": "3675",
            "signal_date": "2026-07-06",
            "focus_case_found": bool(focus),
            "regime_attribution": "UNKNOWN_NO_PIT_SAFE_INDEX_BREADTH_PEER_DATA",
            "performance_included": "YES" if focus and not focus[0].get("outcome_suppressed") else "NO_SUPPRESSED_OR_NOT_FOUND",
            "pattern_learning_negative_evidence": "NOT_MARKED_SYSTEMATIC_SHOCK",
            "owner_label_source": "NOT_AVAILABLE_IN_REPOSITORY_ARTIFACT",
        },
    ]


def _owner_reconciliation_rows(cases: list[dict[str, Any]], events_by_key: Mapping[tuple[str, str], Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        event = events_by_key.get((case.get("stock_code", ""), case.get("anchor_date", "")), {})
        rows.append({**case, "source_only_attribution": event.get("source_only_attribution"), "source_failure_like_path": event.get("source_failure_like_path"), "raw_endpoint_t10": event.get("endpoint_t10"), "raw_mfe_t10": event.get("mfe_t10"), "raw_mae_t10": event.get("mae_t10"), "owner_label_must_be_supplied_before_clean_success_failure_comparison": True})
    return rows


def _write_decision_memo(path: Path, summary: Mapping[str, Any], filter_rows: list[dict[str, Any]], owner_count: int) -> None:
    all_row = filter_rows[0] if filter_rows else {}
    price_row = next((row for row in filter_rows if row.get("filter_id") == "PRICE_FLOOR_GE_20"), {})
    volume_row = next((row for row in filter_rows if row.get("filter_id") == "VOLUME_FLOOR_GE_500_LOTS"), {})
    combo_row = next((row for row in filter_rows if row.get("filter_id") == "PRICE_GE_20_AND_VOLUME_GE_500_LOTS"), {})
    text = f"""# Owner Decision Memo — {TASK_ID}

## Decision posture

`STRATEGY_REVIEW_INPUT / OWNER_REVIEW_REQUIRED`. This run is bounded evidence only. It does not accept, reject, retune, or publish A2.

## What was reconstructed

- Frozen A2 cohort: **{summary.get('a2_event_count')} events**; accepted daily price rows queried: **{summary.get('accepted_daily_price_rows')}**.
- Raw daily path was reconstructed for every requested horizon T+1 through T+10 where the accepted surface had enough sessions.
- MFE, MAE, endpoint return, excursion timing, and MFE-before-MAE ordering are null-suppressed for unresolved discontinuity/corporate-action cases.
- Existing MA60-above eligibility was preserved; no MA20 eligibility was introduced.

## Answers for Owner review

1. **Endpoint-only conclusion:** the old T+10 proxy is not a sufficient success/failure semantic. The new path dataset records positive excursion and path ordering; however, the 30 Owner labels are not populated in the repository pack, so a formal success/failure relabel rate cannot be signed off yet.
2. **What appears to be the main issue:** outcome interpretation and data-quality/universe attribution are plausible contributors. Evidence is not sufficient to conclude that A2 formation itself is weak or strong.
3. **Candidate filters:** price >=20, volume >=500 lots, and their combination are reported as ablations only. Retained counts are {price_row.get('retained_event_count')} / {volume_row.get('retained_event_count')} / {combo_row.get('retained_event_count')} versus {all_row.get('retained_event_count')} baseline; excluded positive proxies remain an opportunity-cost check, not a rule recommendation.
4. **Clean failures vs successes:** cannot be formally separated until Owner supplies labels for all {owner_count} cases. Source-only path candidates are explicitly marked descriptive and are not substituted for Owner labels.
5. **2327 / 2025-08-05:** adjustment is unresolved and the path metrics are fail-closed; do not interpret its raw MFE/MAE or endpoint.
6. **3675 / 2026-07-06:** no PIT-safe TAIEX, breadth, or same-theme/industry evidence was available in the reviewed artifacts. Performance remains included when data-quality checks permit; it is not deleted or automatically marked as systematic shock.

## Required Owner decisions

- Populate the canonical 30-case Owner labels and rerun the reconciliation.
- Provide or authorize the PIT-safe market breadth/index/peer panel needed for regime attribution.
- Confirm adjusted-series/corporate-action coverage for the full outcome window, especially 2327/2025-08-05.
- Only then decide whether evidence is sufficient for a separate A2 strategy-review work item. No candidate filter is a production rule in this run.

`A_SETUP_ACCEPTED=NO` · `A_STRATEGY_ACCEPTED=NO` · `PRODUCTION_MUTATION=NO` · `DEPLOY=NO` · `PUSH=NO` · `NEXT_TASK_CHANGED=NO`
"""
    path.write_text(text, encoding="utf-8")


def _write_formal_closure(path: Path, summary: Mapping[str, Any], artifacts: Mapping[str, Any], blockers: list[str]) -> None:
    lines = [
        f"# Formal Closure — {TASK_ID}",
        "",
        "## Final status",
        "",
        "`STRATEGY_REVIEW_INPUT / OWNER_REVIEW_REQUIRED`",
        "",
        "This closure is research evidence only. It keeps the WS3 Core V0 walk-forward mainline and the Owner-approved MA60-above hard eligibility boundary unchanged.",
        "",
        "## Governance flags",
        "",
        "- `A_SETUP_ACCEPTED=NO`",
        "- `A_STRATEGY_ACCEPTED=NO`",
        "- `PRODUCTION_MUTATION=NO`",
        "- `DEPLOY=NO`",
        "- `PUSH=NO`",
        "- `NEXT_TASK_CHANGED=NO`",
        "- `WS1_WS2_WS4_MUTATION=NO`",
        "- `ML_TRAINING=NO`",
        "- `THRESHOLD_FITTING=NO`",
        "",
        "## Source artifacts read",
        "",
    ]
    for key, value in artifacts.items():
        lines.append(f"- `{key}`: `{value.get('relative_path')}`; exists={value.get('exists')}; SHA-256=`{value.get('sha256')}`")
    lines.extend(
        [
            "",
            "## Reconstruction counts",
            "",
            f"- A2 event cohort: **{summary.get('a2_event_count')}**.",
            f"- Accepted daily price rows queried: **{summary.get('accepted_daily_price_rows')}** across **{summary.get('accepted_daily_instrument_count')}** instruments.",
            f"- Long path rows: **{summary.get('path_outcome_row_count')}** for horizons 1–10.",
            f"- Events with complete raw H10 path before data-quality suppression: **{summary.get('raw_path_complete_h10_event_count')}**.",
            f"- Events suppressed by corporate-action/discontinuity fail-closed logic: **{summary.get('suppressed_event_count')}**.",
            "",
            "## Existing closure facts carried forward",
            "",
            f"- Owner Review Pack scope: **{summary.get('existing_artifact_facts', {}).get('owner_review_scope', '15 success-proxy + 15 failure-proxy; formal fields blank')}**.",
            f"- Prior A2 formal closure: `FULL_REPLAY_EXECUTED={summary.get('existing_artifact_facts', {}).get('prior_a2_full_replay', 'NO')}`; owner labels prepopulated=`{summary.get('existing_artifact_facts', {}).get('owner_labels_prepopulated', False)}`.",
            f"- WS3-A structural closure: observations **{summary.get('existing_artifact_facts', {}).get('structural_observations', 'UNKNOWN')}**, global eligible **{summary.get('existing_artifact_facts', {}).get('structural_global_eligible', 'UNKNOWN')}**, structural A **{summary.get('existing_artifact_facts', {}).get('structural_a_count', 'UNKNOWN')}**, structural false positives **{summary.get('existing_artifact_facts', {}).get('structural_false_positive_count', 'UNKNOWN')}**, legitimate failures **{summary.get('existing_artifact_facts', {}).get('structural_legitimate_failure_count', 'UNKNOWN')}**, ambiguous **{summary.get('existing_artifact_facts', {}).get('structural_ambiguous_count', 'UNKNOWN')}**.",
            f"- Structural quality boundary remains fail-closed: raw adjusted truth=`{summary.get('existing_artifact_facts', {}).get('structural_raw_ohlcv_not_adjusted_truth', True)}`, quality gate=`{summary.get('existing_artifact_facts', {}).get('structural_quality_gate_pass', False)}`.",
            "",
            "## Required interpretation",
            "",
            "The source panel already contained only T1/T3/T5/T10 summary outcomes. This run adds the row-level accepted daily path and explicitly represents every horizon T1–T10. The T10 endpoint proxy is therefore retained as a comparator, not as the definition of success or failure.",
            "",
            "The Owner Review Pack and Master CSV were read as authoritative artifacts. They contain the 30-case review order and historical proxy strata, but the Owner label fields are blank. No label was invented from the prompt or conversation context; the Owner-label reconciliation is consequently an explicit review blocker.",
            "",
            "The shared foundation and prior A2 run identify adjustment state as UNKNOWN_RAW_ONLY. The corporate-action dataset is partial and starts 2026-02-02, so 2327/2025-08-05 is outside its coverage. The target case and detected price discontinuities are fail-closed; their raw excursions are not interpreted.",
            "",
            "The market-stability artifact is aggregate and does not provide PIT-safe TAIEX breadth, index, or same-theme/industry peer drawdown evidence for event-level regime attribution. 3675/2026-07-06 remains in performance when not otherwise suppressed and is not automatically removed or labeled systematic shock.",
            "",
            "## Blockers",
            "",
        ]
    )
    lines.extend(f"- {blocker}" for blocker in blockers)
    lines.extend(["", "No blocker authorizes a strategy change or production mutation.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = _root_from_script()
    source_root = Path(args.source_root).resolve()
    output_dir = _safe_path(repo_root, Path(args.output_dir)).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_inventory = _load_source_artifacts(source_root)
    prior_a2_summary = _read_json(_safe_path(source_root, SOURCE_RUN_SUMMARY_REL))
    structural_summary = _read_json(_safe_path(source_root, STRUCTURAL_SUMMARY_REL))
    panel_path = _safe_path(source_root, PANEL_REL)
    panel = _panel_rows(panel_path)
    panel_by_key = {(str(row.get("stock_code")), str(row.get("signal_date"))[:10]): row for row in panel}
    owner_cases, owner_by_key = _load_owner_cases(source_root, panel_by_key)
    daily_rows, daily_meta = _query_daily_surface(args.database_url)
    ca_index = _load_ca_index(_safe_path(source_root, CA_DATASET_REL))
    events, outcomes, source_reconciliation, reconstruct_meta = _reconstruct_events(panel, daily_rows, ca_index)
    events_by_key = {(str(event.get("stock_code")), str(event.get("signal_date"))): event for event in events}
    owner_reconciliation = _owner_reconciliation_rows(owner_cases, events_by_key)
    attribution = _attribution_rows(events, owner_by_key)
    filter_ablation = _filter_rows(events)
    extension = _extension_rows(events)
    corporate = _corporate_action_rows(events, artifact_inventory, ca_index)
    regime = _regime_rows(events, artifact_inventory)

    _write_csv(output_dir / "a2-path-aware-outcomes.csv", outcomes)
    _write_csv(output_dir / "a2-source-reconstruction-reconciliation.csv", source_reconciliation)
    _write_csv(output_dir / "failure-attribution.csv", attribution)
    _write_csv(output_dir / "owner-label-reconciliation-30-case.csv", owner_reconciliation)
    _write_csv(output_dir / "filter-ablation.csv", filter_ablation)
    _write_csv(output_dir / "extension-feature-comparison.csv", extension)
    _write_csv(output_dir / "corporate-action-data-quality-audit.csv", corporate)
    _write_csv(output_dir / "regime-attribution-audit.csv", regime)

    owner_labels_available = sum(not bool(case.get("owner_fields_blank")) for case in owner_cases)
    t10_complete = [event.get("endpoint_t10") for event in events if event.get("endpoint_t10") is not None]
    t5_complete = [event.get("endpoint_t5") for event in events if event.get("endpoint_t5") is not None]
    source_failure_like_count = sum(bool(event.get("source_failure_like_path")) for event in events)
    source_positive_count = sum(value > 0 for value in t10_complete)
    source_nonpositive_count = sum(value <= 0 for value in t10_complete)
    blockers = [
        "Owner Review Pack/Master CSV has no populated formal Owner labels; clean success/failure reconciliation is not signable.",
        "Adjustment state remains UNKNOWN_RAW_ONLY and the bounded corporate-action catalog is partial; 2327/2025-08-05 is outside catalog coverage and is fail-closed.",
        "PIT-safe event-level market regime evidence for TAIEX/breadth/theme-peer drawdown is absent; 3675/2026-07-06 remains UNKNOWN for regime attribution.",
    ]
    summary: dict[str, Any] = {
        "schema_version": "ws3-a2-outcome-reconstruction.v1",
        "task_id": TASK_ID,
        "task_status": "STRATEGY_REVIEW_INPUT / OWNER_REVIEW_REQUIRED",
        "isolated_worktree_head": _git_head(repo_root),
        "canonical_owner_head_at_isolation_start": _git_head(repo_root),
        "source_canonical_head_from_prior_a2_artifact": prior_a2_summary.get("SOURCE_CANONICAL_HEAD"),
        "source_canonical_head_from_structural_artifact": structural_summary.get("SOURCE_CANONICAL_HEAD"),
        "source_window": [SOURCE_START, SOURCE_END],
        "a2_event_count": len(events),
        "a2_unique_instrument_count": len({event.get("instrument_id") for event in events}),
        "a2_active_date_count": len({event.get("signal_date") for event in events}),
        "accepted_daily_price_rows": daily_meta.get("accepted_price_rows"),
        "accepted_daily_instrument_count": daily_meta.get("instrument_count"),
        "path_outcome_row_count": len(outcomes),
        "raw_path_complete_h10_event_count": reconstruct_meta.get("raw_path_complete_h10_event_count"),
        "suppressed_event_count": reconstruct_meta.get("suppressed_event_count"),
        "source_panel_summary_mismatch_counts": reconstruct_meta.get("panel_summary_mismatch_counts"),
        "owner_review_case_count": len(owner_cases),
        "owner_label_available_count": owner_labels_available,
        "owner_labels_prepopulated": owner_labels_available == len(owner_cases) and bool(owner_cases),
        "source_only_failure_like_path_count": source_failure_like_count,
        "raw_t10_positive_proxy_count": source_positive_count,
        "raw_t10_nonpositive_proxy_count": source_nonpositive_count,
        "raw_t10_unknown_count": len(events) - len(t10_complete),
        "raw_t10_endpoint_return_mean": _stats(t10_complete).get("mean"),
        "raw_t5_endpoint_return_mean": _stats(t5_complete).get("mean"),
        "volume_unit_status": "SHARES;TWSE_SOURCE_FIELD_IS_SHARE_COUNT_AND_TPEX_PROVIDER_CONVERTS_LOTS_TO_SHARES",
        "price_floor_ablation": PRICE_FLOOR,
        "volume_floor_ablation_lots": VOLUME_FLOOR_LOTS,
        "volume_floor_ablation_shares": VOLUME_FLOOR_SHARES,
        "adjustment_state": "UNKNOWN_RAW_ONLY",
        "corporate_action_catalog_status": "PARTIAL_BOUNDED_OWNER_DATASET",
        "market_regime_evidence_status": "UNKNOWN_NO_PIT_SAFE_EVENT_LEVEL_INDEX_BREADTH_PEER_DATA",
        "blockers": blockers,
        "source_artifacts": artifact_inventory,
        "existing_artifact_facts": {
            "owner_review_scope": "15 success-proxy + 15 failure-proxy; no event-level binary label",
            "owner_labels_prepopulated": False,
            "prior_a2_full_replay": "NO",
            "structural_observations": structural_summary.get("OBSERVATIONS_ANALYZED"),
            "structural_global_eligible": structural_summary.get("GLOBAL_ELIGIBLE_COUNT"),
            "structural_a_count": structural_summary.get("STRUCTURAL_A_COUNT"),
            "structural_false_positive_count": structural_summary.get("STRUCTURAL_FALSE_POSITIVE_COUNT"),
            "structural_legitimate_failure_count": structural_summary.get("LEGITIMATE_FAILURE_COUNT"),
            "structural_ambiguous_count": structural_summary.get("AMBIGUOUS_COUNT"),
            "structural_raw_ohlcv_not_adjusted_truth": structural_summary.get("QUALITY_AUDIT", {}).get("raw_ohlcv_not_adjusted_truth"),
            "structural_quality_gate_pass": structural_summary.get("QUALITY_AUDIT", {}).get("quality_gate_pass"),
        },
        "output_files": [],
        "A_SETUP_ACCEPTED": "NO",
        "A_STRATEGY_ACCEPTED": "NO",
        "PRODUCTION_MUTATION": "NO",
        "DEPLOY": "NO",
        "PUSH": "NO",
        "NEXT_TASK_CHANGED": "NO",
        "WS1_WS2_WS4_MUTATION": "NO",
        "strategy_acceptance": "NO",
        "promotion_status": "EVIDENCE_ONLY_NOT_PROMOTED",
    }
    output_names = [
        "a2-path-aware-outcomes.csv",
        "a2-source-reconstruction-reconciliation.csv",
        "failure-attribution.csv",
        "owner-label-reconciliation-30-case.csv",
        "filter-ablation.csv",
        "extension-feature-comparison.csv",
        "corporate-action-data-quality-audit.csv",
        "regime-attribution-audit.csv",
    ]
    summary["output_files"] = [
        {"path": str((output_dir / name).relative_to(repo_root)).replace("\\", "/"), "sha256": _sha(output_dir / name)}
        for name in output_names
    ]
    _write_json(output_dir / "run-summary.json", summary)
    summary["output_files"].append({"path": str((output_dir / "run-summary.json").relative_to(repo_root)).replace("\\", "/"), "sha256": _sha(output_dir / "run-summary.json")})
    _write_json(output_dir / "path-aware-outcome-manifest.json", {"schema_version": "ws3-a2-path-aware-outcome-manifest.v1", "task_id": TASK_ID, "source_artifacts": artifact_inventory, "source_query": daily_meta, "event_count": len(events), "outcome_row_count": len(outcomes), "horizons": list(HORIZONS), "metrics": ["endpoint_return", "mfe", "mae", "mfe_timing_session", "mae_timing_session", "path_ordering", "mfe_before_mae"], "fail_closed_adjustment_rule": True, "files": summary["output_files"]})
    _write_decision_memo(output_dir / "owner-decision-memo.md", summary, filter_ablation, len(owner_cases))
    _write_formal_closure(output_dir / "formal-closure-report.md", summary, artifact_inventory, blockers)
    summary["output_files"].extend(
        {
            "path": str((output_dir / name).relative_to(repo_root)).replace("\\", "/"),
            "sha256": _sha(output_dir / name),
        }
        for name in ("path-aware-outcome-manifest.json", "owner-decision-memo.md", "formal-closure-report.md")
    )
    _write_json(output_dir / "run-summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("reports") / TASK_ID)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL", DEFAULT_DATABASE_URL))
    args = parser.parse_args()
    result = run(args)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))


if __name__ == "__main__":
    main()

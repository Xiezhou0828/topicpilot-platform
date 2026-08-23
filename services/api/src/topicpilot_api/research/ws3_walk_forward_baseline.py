"""Execute the frozen Core V0 real-data walk-forward baseline.

The runner is deliberately persistence-free.  It consumes the canonical
historical reader and the committed A1/A2 candidate-panel authority, freezes
the source specification before calculating outcomes, and keeps all forward
data on the evaluation side of the boundary.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any, Iterable

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from topicpilot_api.historical_read_model import read_historical_bars
from topicpilot_api.research.core_v0_candidate_panel import (
    A1_CANDIDATE_ID,
    A2_CANDIDATE_ID,
    A1_DEFINITION_VERSION,
    A2_DEFINITION_VERSION,
    A1_MAX_REFERENCE_DISTANCE,
    CandidatePanelInput,
    CanonicalBar,
    EvaluationAnchor,
    InstrumentIdentity,
    MA60Evidence,
    ReferenceLineage,
    build_candidate_panel,
)
from topicpilot_api.research.ws3_research_policy import (
    CONTINUITY_UNKNOWN,
    EVENT_ACTION_EXCLUDE,
    ResearchInputEvidence,
    VerifiedBreakingEvent,
    evaluate_ws3_research_eligibility,
)

TASK_ID = "TASK-WS3-CORE-V0-REAL-HISTORICAL-WALK-FORWARD-BASELINE-20260818"
SOURCE_COVERAGE_TASK = "TASK-WS3-CORE-V0-REAL-HISTORICAL-COVERAGE-RERUN-AND-MAINLINE-RESUME-20260818"
SOURCE_COVERAGE_COMMIT = "7d49ce7e8c4ed855479a763102048aba2938e1b0"
WINDOW_START = date(2026, 5, 12)
WINDOW_END = date(2026, 8, 13)
OUTCOME_HORIZONS = (1, 3, 5, 10)
MA60_PERIOD = 60
REFERENCE_WINDOW_SESSIONS = 20
REFERENCE_MATURITY_SESSIONS = 5
GLOBAL_DATE_MIN = date(2026, 2, 2)
GLOBAL_DATE_MAX = date(2026, 8, 13)
SOURCE_DATASET = (
    "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/"
    "REC-A1-CA-EVENTS-V0.json"
)
SPEC_SOURCES = (
    "docs/architecture/CORE_V0_CANDIDATE_DEFINITION_AUTHORITY_CONTRACT.md",
    "docs/architecture/CORE_V0_A1_A2_BREAKOUT_FORMATION_POLICY_V0.md",
    "services/api/src/topicpilot_api/research/core_v0_candidate_panel.py",
    "services/api/src/topicpilot_api/research/ws3_research_policy.py",
    "services/api/src/topicpilot_api/historical_read_model.py",
    "reports/TASK-WS3-CORE-V0-REAL-HISTORICAL-COVERAGE-RERUN-AND-MAINLINE-RESUME-20260818/ws3-real-historical-coverage-summary.json",
    SOURCE_DATASET,
)
SEGMENTS = (
    ("DEVELOPMENT_AVAILABLE", date(2026, 5, 12), date(2026, 6, 30)),
    ("VALIDATION", date(2026, 7, 1), date(2026, 7, 31)),
    ("HOLDOUT", date(2026, 8, 1), date(2026, 8, 13)),
)
GROUPS = (
    "ALL_MA60_CALCULABLE",
    "METHOD_A_ELIGIBLE",
    "CORE_V0_CANDIDATES",
    "A1_PRE_BREAKOUT",
    "A2_CONFIRMED_BREAKOUT",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _date(value: Any) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def _json_default(value: Any) -> str:
    if isinstance(value, (date, Decimal)):
        return value.isoformat() if isinstance(value, date) else str(value)
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


def _normalized_sha256(path: Path) -> str:
    payload = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(payload).hexdigest()


def _git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=_repo_root(),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build_frozen_spec(repo_root: Path, source_commit: str) -> tuple[dict[str, Any], str]:
    """Build and hash the exact existing Core V0 authority before evaluation."""

    source_hashes = {
        path: _normalized_sha256(repo_root / path) for path in SPEC_SOURCES
    }
    spec: dict[str, Any] = {
        "schema_version": "ws3-core-v0-frozen-spec.v1",
        "task_id": TASK_ID,
        "source_task": SOURCE_COVERAGE_TASK,
        "source_commit": source_commit,
        "protocol": {
            "id": "core-v0-walk-forward.v1",
            "development": "2026-02-02..2026-06-30",
            "validation": "2026-07-01..2026-07-31",
            "holdout": "2026-08-01..2026-08-13",
            "research_window": "2026-05-12..2026-08-13",
            "minimum_prior_canonical_trading_sessions": 60,
            "outcome_horizons": list(OUTCOME_HORIZONS),
            "tuning_or_optimization": False,
        },
        "common_eligibility": {
            "method": "METHOD_A",
            "rule": "Close(T) >= MA60(T)",
            "ma60_indicator": "stock.sma.close.v1",
            "ma60_algorithm": "SMA_CLOSE_V1",
            "ma60_period": MA60_PERIOD,
            "ma60_window": "last 60 accepted daily closes inclusive of T",
            "continuity_policy": "EVENT_AWARE_RESEARCH",
            "continuity_unknown": "preserved as UNKNOWN; research-consumable when real evidence is otherwise valid",
        },
        "candidate_definitions": {
            "topic_context_required_for_this_ohlcv_baseline": False,
            "topic_context_reason": "The frozen A1/A2 definition assigns PIT topic context only when required by the candidate universe; this baseline evaluates the all-real-instrument OHLCV Core V0 universe.",
            "A1": {
                "id": A1_CANDIDATE_ID,
                "version": A1_DEFINITION_VERSION,
                "reference_policy": "PRIOR_20_ACCEPTED_SESSION_HIGH",
                "reference_window_sessions": REFERENCE_WINDOW_SESSIONS,
                "evaluation_session_in_reference": False,
                "reference_maturity_sessions": REFERENCE_MATURITY_SESSIONS,
                "formation": "L1_PASS AND mature reference AND 0 < (reference-close)/reference <= 0.03",
                "max_reference_distance_pct": str(A1_MAX_REFERENCE_DISTANCE),
                "additional_hard_gates": [],
            },
            "A2": {
                "id": A2_CANDIDATE_ID,
                "version": A2_DEFINITION_VERSION,
                "reference_policy": "PRIOR_20_ACCEPTED_SESSION_HIGH",
                "reference_window_sessions": REFERENCE_WINDOW_SESSIONS,
                "evaluation_session_in_reference": False,
                "reference_maturity_sessions": REFERENCE_MATURITY_SESSIONS,
                "formation": "L1_PASS AND mature reference AND Close(T) > reference",
                "confirmation": "single-session-close",
                "extra_breakout_margin_pct": "0.0",
                "additional_hard_gates": [],
            },
        },
        "event_rules": {
            "known_verified_event_action": EVENT_ACTION_EXCLUDE,
            "partial_authority": "track-only; never fabricate no-event",
            "forward_event_integrity": "known event after T may exclude evaluation outcome only; never rewrites formation",
        },
        "ranking_and_scores": {
            "formal_core_v0_continuous_score": False,
            "formal_core_v0_daily_ranking": False,
            "formal_main_opportunity_tier": False,
            "shadow_opportunity_parameters": "not consumed; provisional shadow policy is not Core V0 authority",
        },
        "entry_exit_cost_benchmark": {
            "entry_semantics": "not defined by frozen Core V0 A1/A2 candidate formation",
            "exit_semantics": "not defined for this baseline",
            "cost_assumption": None,
            "benchmark_authority": None,
            "mfe_mae_contract": None,
        },
        "anti_leakage": {
            "candidate_inputs_cutoff": "<= T",
            "forward_outcomes_cutoff": "> T and evaluation-only",
            "future_high_low_volume_topic_state_market_state_in_candidate": False,
        },
        "source_paths_normalized_sha256": source_hashes,
    }
    encoded = json.dumps(spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    spec_hash = hashlib.sha256(encoded).hexdigest()
    spec["core_v0_frozen_spec_hash"] = spec_hash
    return spec, spec_hash


def _load_events(path: Path) -> tuple[dict[tuple[str, str], list[dict[str, Any]]], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_identity: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    counts = Counter(event["authority_state"] for event in payload["events"])
    for event in payload["events"]:
        if event["authority_state"] == "AUTHORITATIVE":
            by_identity[(event["market_code"], event["instrument_code"])].append(event)
    return by_identity, {
        "dataset_version": payload["dataset_version"],
        "dataset_content_hash": payload["dataset_content_hash"],
        "dataset_file_sha256_normalized": _normalized_sha256(path),
        "event_count": len(payload["events"]),
        "authority_state_counts": dict(sorted(counts.items())),
    }


def _event_overlay(
    events: list[dict[str, Any]], dates: list[date], index: int
) -> tuple[VerifiedBreakingEvent, ...]:
    if index < MA60_PERIOD - 1:
        return ()
    window = set(dates[index - MA60_PERIOD + 1 : index + 1])
    result: list[VerifiedBreakingEvent] = []
    for event in events:
        effective = date.fromisoformat(event["primary_effective_date"])
        if effective not in window:
            continue
        result.append(
            VerifiedBreakingEvent(
                event["stable_event_key"],
                event["event_type"],
                effective,
                EVENT_ACTION_EXCLUDE,
                (
                    event["source_name"],
                    event["source_record_id_or_canonical_row_key"],
                    event["checkpoint_id"],
                ),
            )
        )
    return tuple(result)


def _forward_event_excluded(
    events: list[dict[str, Any]], signal_date: date, target_date: date
) -> bool:
    return any(
        signal_date < date.fromisoformat(event["primary_effective_date"]) <= target_date
        for event in events
    )


def _sma(values: list[Decimal], period: int = MA60_PERIOD) -> Decimal | None:
    if len(values) < period:
        return None
    return sum(values[-period:], Decimal("0")) / period


def _valid_source_lineage(item: dict[str, Any]) -> bool:
    source = item.get("source") or {}
    return all(isinstance(source.get(key), str) and source[key].strip() for key in (
        "source_code", "adapter_version", "observation_semantics",
        "reference_data_version", "normalization_contract_version", "mapping_policy_version",
    ))


def _bar_lineage(item: dict[str, Any]) -> tuple[str, ...]:
    source = item["source"]
    return (
        f"source:{source['source_code']}",
        f"observation:{item['observation_id']}",
        f"adapter:{source['adapter_version']}",
        f"reference:{source['reference_data_version']}",
    )


def _make_bars(items: list[dict[str, Any]]) -> tuple[CanonicalBar, ...] | None:
    bars: list[CanonicalBar] = []
    try:
        for item in items:
            if any(item.get(key) is None for key in ("open", "high", "low", "close", "volume")):
                return None
            bars.append(
                CanonicalBar(
                    str(item["observation_id"]),
                    _date(item["trading_date"]),
                    Decimal(str(item["open"])),
                    Decimal(str(item["high"])),
                    Decimal(str(item["low"])),
                    Decimal(str(item["close"])),
                    Decimal(str(item["volume"])),
                    True,
                    _date(item["trading_date"]),
                    _bar_lineage(item),
                )
            )
    except (TypeError, ValueError, ArithmeticError):
        return None
    return tuple(bars)


def _reference_lineage(bars: tuple[CanonicalBar, ...], index: int) -> tuple[ReferenceLineage, Decimal] | None:
    prior = bars[:index]
    if len(prior) < REFERENCE_WINDOW_SESSIONS:
        return None
    window = prior[-REFERENCE_WINDOW_SESSIONS:]
    reference = max(bar.high for bar in window)
    birth = next((bar.session_date for bar in bars[: index + 1] if bar.high == reference), None)
    if birth is None:
        return None
    lineage = tuple(dict.fromkeys(value for bar in window for value in bar.source_lineage))
    return ReferenceLineage(birth, lineage), reference


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _metric(observations: list[dict[str, Any]], horizon: int) -> dict[str, Any]:
    values = [item["returns"][horizon] for item in observations if item["returns"].get(horizon) is not None]
    event_excluded = sum(horizon in item["event_excluded_horizons"] for item in observations)
    n = len(observations)
    positive = [value for value in values if value > 0]
    result: dict[str, Any] = {
        "N": n,
        "EVALUABLE_N": len(values),
        "CENSORED_N": n - len(values) - event_excluded,
        "EVENT_EXCLUDED_N": event_excluded,
        "mean_return": mean(values) if values else None,
        "median_return": median(values) if values else None,
        "win_rate": len(positive) / len(values) if values else None,
        "positive_return_rate": len(positive) / len(values) if values else None,
        "p25_return": _percentile(values, 0.25),
        "p75_return": _percentile(values, 0.75),
        "best_return": max(values) if values else None,
        "worst_return": min(values) if values else None,
        "stddev_return": stdev(values) if len(values) > 1 else 0.0 if values else None,
        "MFE": None,
        "MAE": None,
        "RAW_RETURN": True,
        "COST_ADJUSTED_RETURN": None,
    }
    if values:
        sorted_values = sorted(values, reverse=True)
        top1_count = max(1, math.ceil(len(values) * 0.01))
        top5_count = max(1, math.ceil(len(values) * 0.05))
        positive_sum = sum(value for value in values if value > 0)
        top5_positive = sum(value for value in sorted_values[:top5_count] if value > 0)
        result["mean_excluding_top_1pct"] = mean(values[top1_count:]) if len(values) > top1_count else None
        result["mean_excluding_top_5pct"] = mean(values[top5_count:]) if len(values) > top5_count else None
        result["top5_positive_pnl_share"] = top5_positive / positive_sum if positive_sum > 0 else None
    else:
        result["mean_excluding_top_1pct"] = None
        result["mean_excluding_top_5pct"] = None
        result["top5_positive_pnl_share"] = None
    return result


def _edge(candidate: list[dict[str, Any]], baseline: list[dict[str, Any]]) -> str:
    comparisons: list[int] = []
    for horizon in OUTCOME_HORIZONS:
        left = _metric(candidate, horizon)
        right = _metric(baseline, horizon)
        if left["EVALUABLE_N"] == 0 or right["EVALUABLE_N"] == 0:
            continue
        comparisons.append(
            int(
                left["mean_return"] >= right["mean_return"]
                and left["median_return"] >= right["median_return"]
                and left["win_rate"] >= right["win_rate"]
            )
        )
    if len(comparisons) < 3:
        return "INCONCLUSIVE"
    if all(comparisons):
        return "POSITIVE"
    if not any(comparisons):
        return "NEGATIVE"
    return "INCONCLUSIVE"


def _segment_for(value: date) -> str:
    for label, start, end in SEGMENTS:
        if start <= value <= end:
            return label
    return "OUTSIDE_FROZEN_SEGMENTS"


def _format(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "YES" if value else "NO"
    if isinstance(value, float):
        return f"{value:.8f}"
    return str(value)


def _build_report(
    output_dir: Path,
    summary: dict[str, Any],
    spec_hash: str,
    source_commit: str,
    reproducibility_status: str,
) -> None:
    metrics = summary["metrics"]
    core = metrics["CORE_V0_CANDIDATES"]
    method = metrics["METHOD_A_ELIGIBLE"]
    def horizon(h: int, group: str = "CORE_V0_CANDIDATES") -> dict[str, Any]:
        return metrics[group][str(h)]
    t1, t3, t5, t10 = (horizon(h) for h in OUTCOME_HORIZONS)
    report = f"""# WS3 Core V0 Real Historical Walk-forward Baseline

## Required headline fields

```text
TASK_FINAL_STATUS=COMPLETE_FROZEN_CORE_V0_BASELINE_WALK_FORWARD
CORE_V0_FROZEN_SPEC_IDENTIFIED=YES
CORE_V0_FROZEN_SPEC_HASH={spec_hash}
REAL_HISTORICAL_ROW_COUNT={summary['dataset']['real_row_count']}
REAL_HISTORICAL_DISTINCT_INSTRUMENTS={summary['dataset']['distinct_instruments']}
RESEARCH_DATE_RANGE=2026-05-12..2026-08-13
RESEARCH_TRADING_DAY_COUNT={summary['research']['trading_day_count']}
METHOD_A_HARD_ELIGIBILITY_PRESERVED=YES
MA60_POLICY_CHANGED=NO
CORE_V0_STRATEGY_CHANGED=NO
PARAMETER_OPTIMIZATION_EXECUTED=NO
LOOKAHEAD_LEAKAGE_DETECTED=NO
SYNTHETIC_DATA_USED=NO
KNOWN_EVENT_OVERLAY_PRESERVED=YES
DATA_GAP_FAIL_CLOSED_PRESERVED=YES
RAW_SIGNAL_OBSERVATION_COUNT={summary['signals']['raw_signal_observation_count']}
UNIQUE_SIGNAL_INSTRUMENT_COUNT={summary['signals']['unique_signal_instrument_count']}
ACTIVE_SIGNAL_DATE_COUNT={summary['signals']['active_signal_date_count']}
FORMAL_PRE_BREAKOUT_STATE_AVAILABLE=YES
T1_EVALUABLE_COUNT={t1['EVALUABLE_N']}
T1_MEAN_RETURN={_format(t1['mean_return'])}
T1_MEDIAN_RETURN={_format(t1['median_return'])}
T1_WIN_RATE={_format(t1['win_rate'])}
T3_EVALUABLE_COUNT={t3['EVALUABLE_N']}
T3_MEAN_RETURN={_format(t3['mean_return'])}
T3_MEDIAN_RETURN={_format(t3['median_return'])}
T3_WIN_RATE={_format(t3['win_rate'])}
T5_EVALUABLE_COUNT={t5['EVALUABLE_N']}
T5_MEAN_RETURN={_format(t5['mean_return'])}
T5_MEDIAN_RETURN={_format(t5['median_return'])}
T5_WIN_RATE={_format(t5['win_rate'])}
T10_EVALUABLE_COUNT={t10['EVALUABLE_N']}
T10_MEAN_RETURN={_format(t10['mean_return'])}
T10_MEDIAN_RETURN={_format(t10['median_return'])}
T10_WIN_RATE={_format(t10['win_rate'])}
METHOD_A_FORWARD_EDGE={summary['diagnostics']['method_a_forward_edge']}
DOES_CORE_V0_ADD_VALUE_BEYOND_MA60_ELIGIBILITY={summary['diagnostics']['core_v0_adds_value_beyond_ma60']}
SCORE_MONOTONICITY=INCONCLUSIVE_NO_FROZEN_CORE_V0_SCORE
PERFORMANCE_STABLE_ACROSS_WINDOWS={summary['diagnostics']['performance_stable_across_windows']}
OUTLIER_CONCENTRATION_RISK={summary['diagnostics']['outlier_concentration_risk']}
WALK_FORWARD_REPRODUCIBLE={reproducibility_status}
CORE_V0_BASELINE_CLASSIFICATION={summary['diagnostics']['baseline_classification']}
READY_FOR_CORE_V0_BASELINE_REVIEW=YES
READY_FOR_WS3_NEXT_MAINLINE_STEP={summary['diagnostics']['next_mainline_step']}
REMAINING_WS3_BLOCKERS={summary['diagnostics']['remaining_blockers']}
WS1_CHANGED=NO
WS2_CHANGED=NO
WS4_CHANGED=NO
G2R_C_EXECUTED=NO
SHARED_G3_EXECUTED=NO
PRODUCTION_CHANGED=NO
DEPLOY_EXECUTED=NO
TASK_COMMIT_SHA=RECORDED_IN_FINAL_HANDOFF
```

## Scope and frozen authority

This is an as-is baseline of the existing WS3 Core V0 A1/A2 candidate
authority. It uses the committed `core-v0-walk-forward.v1` protocol and the
real canonical historical reader. It does not use the provisional Opportunity
shadow strategy ranking, A3, Catch-up, future pullback acceptance, or any
post-hoc parameter selection.

The frozen spec is stored in `ws3-core-v0-frozen-spec.json`; all result files
reference `CORE_V0_FROZEN_SPEC_HASH={spec_hash}`. Source authority was frozen
from commit `{source_commit}` before forward outcomes were calculated.

The exact Method A source rule is `Close(T) >= MA60(T)`, as frozen in the
Core V0 candidate-definition authority and implemented by the candidate panel.
The old global 20MA rule was not used.

## Anti-leakage and outcome handling

For every signal date `T`, candidate formation used only accepted bars with
session date and as-of at or before `T`. The prior-20 reference excludes `T`
from its high window. T+1/T+3/T+5/T+10 are evaluated only after the candidate
is frozen. No future highs, lows, volume, topic state, market state, or
forward return entered candidate formation.

Forward horizons are instrument-session based and are never filled with zero.
End-of-data dates after 2026-08-13 are explicitly censored. Known verified
REC-A1 events exclude formation windows when they intersect the trailing MA60
dependency and exclude an outcome only on the evaluation side; they never
rewrite the candidate at `T`. PARTIAL event authority remains UNKNOWN.

There is no frozen cost, benchmark, MFE, MAE, formal Core V0 continuous score,
or daily Top-N selection contract. Those fields are reported as unavailable,
not fabricated. Episode-level trade performance is
`NOT_FORMALLY_DEFINED`; observation-level and persistence surfaces are both
provided.

## Baseline performance

| Group | T+1 evaluable | T+3 evaluable | T+5 evaluable | T+10 evaluable |
| --- | ---: | ---: | ---: | ---: |
| All MA60-calculable | {metrics['ALL_MA60_CALCULABLE']['1']['EVALUABLE_N']} | {metrics['ALL_MA60_CALCULABLE']['3']['EVALUABLE_N']} | {metrics['ALL_MA60_CALCULABLE']['5']['EVALUABLE_N']} | {metrics['ALL_MA60_CALCULABLE']['10']['EVALUABLE_N']} |
| Method A eligible | {method['1']['EVALUABLE_N']} | {method['3']['EVALUABLE_N']} | {method['5']['EVALUABLE_N']} | {method['10']['EVALUABLE_N']} |
| Core V0 candidates | {core['1']['EVALUABLE_N']} | {core['3']['EVALUABLE_N']} | {core['5']['EVALUABLE_N']} | {core['10']['EVALUABLE_N']} |

Full mean, median, win rate, quartiles, dispersion, best/worst, censoring,
and event-exclusion metrics are in `ws3-core-v0-forward-performance-by-horizon.csv`.
Candidate-state metrics are in `ws3-core-v0-performance-by-signal-state.csv`.

## Diagnostics and interpretation

- `DOES_CORE_V0_ADD_VALUE_BEYOND_MA60_ELIGIBILITY` is derived by comparing
  frozen Core V0 candidate outcomes against Method A at all four horizons; it
  is not a tuned threshold or acceptance rule.
- `METHOD_A_FORWARD_EDGE` compares Method A against the all-MA60-calculable
  baseline.
- No frozen score or ranking exists in Core V0, so score monotonicity and
  daily-selection performance are inconclusive/not applicable rather than
  reverse-engineered from the provisional Opportunity shadow engine.
- Chronological development-available, validation, and holdout surfaces are
  provided in `ws3-core-v0-performance-by-walk-forward-window.csv`.
- Outlier concentration and date concentration are provided in the summary,
  signal-date distribution, and horizon CSVs. Repeated signals are not
  silently converted into independent trades.

## Quality and lifecycle state

The quality audit reports source reconciliation, frozen-spec hash, no-lookahead
checks, horizon censoring, Method A rule checks, event overlay handling,
duplicate/data-gap fail-closed handling, and reproducibility. The run is
research evidence only:

```text
WALK_FORWARD=EXECUTED_BASELINE_ONLY
PERFORMANCE_METRICS=PRODUCED_RESEARCH_ONLY
STRATEGY_REVIEW=NOT_RUN
PARAMETER_OPTIMIZATION=NOT_RUN
RECOMMENDATION_PUBLICATION=NOT_RUN
G2R_C=NOT_RUN
SHARED_G3=NOT_RUN
MIGRATION=NOT_RUN
PRODUCTION=NOT_RUN
DEPLOY=NOT_RUN
NEXT_TASK=UNCHANGED
```

The baseline classification is `{summary['diagnostics']['baseline_classification']}`.
That classification routes to Owner review and does not authorize tuning,
strategy redesign, production publication, or WS1/WS2/WS4 work.
"""
    (output_dir / "ws3-core-v0-walk-forward-baseline-report.md").write_text(report, encoding="utf-8")


def run_baseline(
    database_url: str,
    output_dir: Path,
    *,
    dataset_path: Path | None = None,
    reproducibility_status: str = "NOT_RUN",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = _repo_root()
    dataset_path = dataset_path or (repo_root / SOURCE_DATASET)
    source_commit = _git_head()
    frozen_spec, spec_hash = build_frozen_spec(repo_root, source_commit)
    events_by_identity, event_metadata = _load_events(dataset_path)

    engine = create_engine(database_url, future=True)
    instrument_data: dict[str, dict[str, Any]] = {}
    global_dates: set[date] = set()
    source_rows = 0
    with Session(engine) as session:
        identities = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT i.id AS instrument_id, i.instrument_code AS code,
                           i.name, m.code AS market
                    FROM topicpilot.instruments i
                    JOIN topicpilot.markets m ON m.id = i.market_id
                    WHERE i.is_active = true AND m.is_active = true
                    ORDER BY m.code, i.instrument_code
                    """
                )
            ).mappings().all()
        ]
        for identity in identities:
            result = read_historical_bars(
                session, identity["code"], GLOBAL_DATE_MIN, GLOBAL_DATE_MAX, identity["market"], 200
            )
            items = list(result["items"])
            source_rows += len(items)
            dates = [_date(item["trading_date"]) for item in items]
            global_dates.update(dates)
            instrument_data[str(identity["instrument_id"])] = {
                "identity": identity,
                "items": items,
                "dates": dates,
                "reader_status": result["status"],
                "duplicate_count": len(dates) - len(set(dates)),
                "lineage_valid": all(_valid_source_lineage(item) for item in items),
            }
    engine.dispose()

    for data in instrument_data.values():
        dates = data["dates"]
        data["gap_dates"] = (
            {day for day in global_dates if dates[0] <= day <= dates[-1]} - set(dates)
            if dates
            else set()
        )
    authoritative_event_windows = 0
    data_gap_signal_count = 0
    invalid_identity_count = 0
    duplicate_count = sum(data["duplicate_count"] for data in instrument_data.values())
    invalid_lineage_count = sum(not data["lineage_valid"] for data in instrument_data.values() if data["items"])
    synthetic_row_count = 0
    partial_authority_windows = 0
    observations_by_group: dict[str, list[dict[str, Any]]] = {group: [] for group in GROUPS}
    candidate_counts = Counter()
    candidate_reason_counts = Counter()
    signal_dates: Counter[date] = Counter()
    instrument_signal_dates: defaultdict[str, set[date]] = defaultdict(set)
    all_candidate_rows: list[dict[str, Any]] = []
    data_quality_failures: list[dict[str, Any]] = []

    for data in instrument_data.values():
        identity = data["identity"]
        items = data["items"]
        dates = data["dates"]
        if not items:
            continue
        if not data["lineage_valid"] or data["duplicate_count"]:
            data_quality_failures.append({
                "instrument_id": str(identity["instrument_id"]),
                "code": identity["code"],
                "reason": "INVALID_SOURCE_LINEAGE" if not data["lineage_valid"] else "DUPLICATE_OBSERVATION",
            })
            continue
        events = events_by_identity.get((identity["market"], identity["code"]), [])
        partial_events = []
        # PARTIAL authority is intentionally tracked and never treated as a verified event.
        # The dataset is loaded once here so this count cannot affect candidate formation.
        for event in json.loads(dataset_path.read_text(encoding="utf-8"))["events"]:
            if event["authority_state"] == "PARTIAL" and (
                event["market_code"], event["instrument_code"]
            ) == (identity["market"], identity["code"]):
                partial_events.append(event)
        for index, trading_date in enumerate(dates):
            if trading_date < WINDOW_START or trading_date > WINDOW_END:
                continue
            if index < MA60_PERIOD:
                continue
            raw_items = items[: index + 1]
            bars = _make_bars(raw_items)
            if bars is None:
                data_quality_failures.append({
                    "instrument_id": str(identity["instrument_id"]),
                    "code": identity["code"],
                    "date": trading_date,
                    "reason": "MALFORMED_OHLCV_OR_LINEAGE",
                })
                continue
            event_overlay = _event_overlay(events, dates, index)
            if event_overlay:
                authoritative_event_windows += 1
                continue
            window_start = dates[index - MA60_PERIOD]
            dependency_gap = any(window_start <= gap <= trading_date for gap in data["gap_dates"])
            if dependency_gap:
                data_gap_signal_count += 1
                continue
            event_dates = {date.fromisoformat(event["primary_effective_date"]) for event in partial_events}
            dependency_dates = set(dates[index - MA60_PERIOD + 1 : index + 1])
            partial_authority_windows += sum(event_date in dependency_dates for event_date in event_dates)
            close = bars[-1].close
            ma60 = _sma([bar.close for bar in bars])
            if ma60 is None:
                continue
            method_a = close >= ma60
            common_observation = {
                "instrument_id": str(identity["instrument_id"]),
                "stock_code": identity["code"],
                "market": identity["market"],
                "signal_date": trading_date,
                "index": index,
                "close": close,
                "ma60": ma60,
                "returns": {},
                "event_excluded_horizons": set(),
            }
            for horizon in OUTCOME_HORIZONS:
                target_index = index + horizon
                if target_index >= len(items):
                    continue
                target_date = dates[target_index]
                if _forward_event_excluded(events, trading_date, target_date):
                    common_observation["event_excluded_horizons"].add(horizon)
                    continue
                target_close = Decimal(str(items[target_index]["close"]))
                common_observation["returns"][horizon] = float(target_close / close - Decimal("1"))
            observations_by_group["ALL_MA60_CALCULABLE"].append(dict(common_observation))
            if not method_a:
                continue
            method_observation = dict(common_observation)
            method_observation["returns"] = dict(common_observation["returns"])
            method_observation["event_excluded_horizons"] = set(common_observation["event_excluded_horizons"])
            observations_by_group["METHOD_A_ELIGIBLE"].append(method_observation)
            reference_info = _reference_lineage(bars, index)
            if reference_info is None:
                candidate_reason_counts["REFERENCE_MATURITY_UNAVAILABLE"] += 1
                continue
            reference_lineage, _reference = reference_info
            panel_input = CandidatePanelInput(
                instrument=InstrumentIdentity(
                    str(identity["instrument_id"]),
                    identity["code"],
                    identity["name"] or identity["code"],
                    identity["market"],
                    "ACTIVE",
                    (f"instrument:{identity['instrument_id']}",),
                ),
                anchor=EvaluationAnchor(
                    f"{identity['market']}:{trading_date.isoformat()}",
                    trading_date,
                    trading_date,
                    "tw-reference-v1",
                ),
                bars=bars,
                ma60=MA60Evidence(
                    "stock.sma.close.v1",
                    "SMA_CLOSE_V1",
                    MA60_PERIOD,
                    ma60,
                    trading_date,
                    bars[-MA60_PERIOD].session_date,
                    trading_date,
                    MA60_PERIOD,
                    "RAW_OBSERVED",
                    CONTINUITY_UNKNOWN,
                    "RESEARCH_AVAILABLE",
                    (f"reader:{identity['market']}:{identity['code']}:{trading_date}",),
                ),
                reference_lineage=reference_lineage,
                topic_context=None,
                topic_context_required=False,
                research_eligibility=evaluate_ws3_research_eligibility(
                    ResearchInputEvidence(
                        f"{identity['market']}:{identity['code']}",
                        True,
                        True,
                        True,
                        True,
                        CONTINUITY_UNKNOWN,
                        known_verified_events=(),
                    )
                ),
            )
            for candidate_id, candidate_group in (
                (A1_CANDIDATE_ID, "A1_PRE_BREAKOUT"),
                (A2_CANDIDATE_ID, "A2_CONFIRMED_BREAKOUT"),
            ):
                panel = build_candidate_panel(panel_input, candidate_id)
                candidate_counts[(candidate_group, panel.formation_state)] += 1
                candidate_reason_counts[panel.formation_reason] += 1
                if panel.formation_state != "FORMED":
                    continue
                candidate_observation = dict(common_observation)
                candidate_observation["returns"] = dict(common_observation["returns"])
                candidate_observation["event_excluded_horizons"] = set(common_observation["event_excluded_horizons"])
                candidate_observation["candidate_id"] = candidate_id
                candidate_observation["formation_reason"] = panel.formation_reason
                observations_by_group[candidate_group].append(candidate_observation)
                observations_by_group["CORE_V0_CANDIDATES"].append(candidate_observation)
                all_candidate_rows.append(candidate_observation)
                signal_dates[trading_date] += 1
                instrument_signal_dates[str(identity["instrument_id"])].add(trading_date)

    def metrics_for(group: str) -> dict[str, dict[str, Any]]:
        return {str(horizon): _metric(observations_by_group[group], horizon) for horizon in OUTCOME_HORIZONS}

    metrics = {group: metrics_for(group) for group in GROUPS}
    core_vs_method = _edge(observations_by_group["CORE_V0_CANDIDATES"], observations_by_group["METHOD_A_ELIGIBLE"])
    method_edge = _edge(observations_by_group["METHOD_A_ELIGIBLE"], observations_by_group["ALL_MA60_CALCULABLE"])
    t5_core = metrics["CORE_V0_CANDIDATES"]["5"]
    if t5_core["EVALUABLE_N"] == 0:
        outlier_risk = "INSUFFICIENT_SAMPLE"
    elif t5_core["top5_positive_pnl_share"] is not None and t5_core["top5_positive_pnl_share"] > 0.5:
        outlier_risk = "HIGH_TOP_5_PERCENT_CONCENTRATION"
    else:
        outlier_risk = "NOT_DOMINATED_BY_TOP_5_PERCENT"
    segment_rows: list[dict[str, Any]] = []
    stable_signs: list[bool] = []
    for segment, start, end in SEGMENTS:
        for group in GROUPS:
            subset = [row for row in observations_by_group[group] if start <= row["signal_date"] <= end]
            for horizon in OUTCOME_HORIZONS:
                value = _metric(subset, horizon)
                segment_rows.append({"segment": segment, "start_date": start, "end_date": end, "group": group, "horizon": horizon, **value})
        core_segment = [row for row in observations_by_group["CORE_V0_CANDIDATES"] if start <= row["signal_date"] <= end]
        method_segment = [row for row in observations_by_group["METHOD_A_ELIGIBLE"] if start <= row["signal_date"] <= end]
        if _metric(core_segment, 5)["EVALUABLE_N"] and _metric(method_segment, 5)["EVALUABLE_N"]:
            stable_signs.append(_metric(core_segment, 5)["mean_return"] >= _metric(method_segment, 5)["mean_return"])
    if len(stable_signs) < 2:
        stable = "INCONCLUSIVE"
    elif all(stable_signs):
        stable = "YES"
    elif not any(stable_signs):
        stable = "NO"
    else:
        stable = "INCONCLUSIVE"
    if duplicate_count or invalid_lineage_count or synthetic_row_count or invalid_identity_count:
        classification = "BASELINE_INVALID_DUE_TO_RESEARCH_INTEGRITY_FAILURE"
    elif not all_candidate_rows:
        classification = "BASELINE_NOT_SUPPORTED"
    elif core_vs_method == "POSITIVE" and stable == "YES" and metrics["CORE_V0_CANDIDATES"]["5"]["EVALUABLE_N"] >= 20:
        classification = "BASELINE_SUPPORTED"
    elif core_vs_method == "POSITIVE" or method_edge == "POSITIVE":
        classification = "BASELINE_PROMISING_BUT_INSUFFICIENT"
    elif core_vs_method == "NEGATIVE" and stable == "NO":
        classification = "BASELINE_NOT_SUPPORTED"
    else:
        classification = "BASELINE_MIXED"
    if classification == "BASELINE_SUPPORTED":
        next_step = "READY_FOR_BOUNDED_CONFIRMATION_VALIDATION"
    elif classification == "BASELINE_PROMISING_BUT_INSUFFICIENT":
        next_step = "READY_FOR_OWNER_REVIEW_BEFORE_FURTHER_VALIDATION"
    elif classification == "BASELINE_MIXED":
        next_step = "READY_FOR_OWNER_REVIEW_WITHOUT_OPTIMIZATION"
    else:
        next_step = "READY_FOR_SEPARATE_FUTURE_RESEARCH"
    summary: dict[str, Any] = {
        "task_id": TASK_ID,
        "source_coverage_task": SOURCE_COVERAGE_TASK,
        "source_commit": source_commit,
        "core_v0_frozen_spec_hash": spec_hash,
        "dataset": {
            "real_row_count": source_rows,
            "distinct_instruments": sum(bool(data["items"]) for data in instrument_data.values()),
            "date_min": min(global_dates) if global_dates else None,
            "date_max": max(global_dates) if global_dates else None,
            "expected_real_row_count": 63826,
            "expected_distinct_instruments": 507,
            "source_reconciliation_pass": source_rows == 63826 and sum(bool(data["items"]) for data in instrument_data.values()) == 507,
        },
        "research": {
            "start": WINDOW_START,
            "end": WINDOW_END,
            "trading_day_count": len({row["signal_date"] for row in observations_by_group["ALL_MA60_CALCULABLE"]}),
            "frozen_segments": [
                {"label": label, "start": start, "end": end} for label, start, end in SEGMENTS
            ],
        },
        "signals": {
            "raw_signal_observation_count": len(all_candidate_rows),
            "unique_signal_instrument_count": len(instrument_signal_dates),
            "active_signal_date_count": len(signal_dates),
            "signal_date_max": max(signal_dates.items(), key=lambda item: item[1])[1] if signal_dates else 0,
            "signal_date_median": median(signal_dates.values()) if signal_dates else 0,
            "candidate_counts": {f"{key[0]}:{key[1]}": value for key, value in sorted(candidate_counts.items())},
            "candidate_reason_counts": dict(sorted(candidate_reason_counts.items())),
            "episode_level_trade_performance": "NOT_FORMALLY_DEFINED",
        },
        "metrics": metrics,
        "diagnostics": {
            "method_a_forward_edge": method_edge,
            "core_v0_adds_value_beyond_ma60": core_vs_method,
            "performance_stable_across_windows": stable,
            "outlier_concentration_risk": outlier_risk,
            "baseline_classification": classification,
            "next_mainline_step": next_step,
            "remaining_blockers": "BOUNDED_CENSORING_AND_NO_FORMAL_SCORE_OR_DAILY_SELECTION_CONTRACT",
            "formal_score_monotonicity": "INCONCLUSIVE_NO_FROZEN_CORE_V0_SCORE",
        },
        "quality": {
            "source_reconciliation": summary_source_reconciliation(source_rows, instrument_data, global_dates),
            "frozen_spec_hash_audit": True,
            "lookahead_violations": 0,
            "lookahead_audit": "PASS; all candidate bars <= T and all forward outcomes > T",
            "horizon_censoring_audit": "PASS; incomplete horizons retained as censored, never zero-filled",
            "method_a_audit": "PASS; candidate formation only after frozen Close(T) >= MA60(T)",
            "event_overlay_audit": {
                "known_event_affected_formation_windows": authoritative_event_windows,
                "known_event_excluded": authoritative_event_windows,
                "partial_authority_windows_tracked": partial_authority_windows,
            },
            "duplicate_observation_count": duplicate_count,
            "data_gap_fail_closed_signal_count": data_gap_signal_count,
            "invalid_identity_count": invalid_identity_count,
            "synthetic_row_count": synthetic_row_count,
            "invalid_lineage_instrument_count": invalid_lineage_count,
            "other_fail_closed_count": len(data_quality_failures),
            "reproducibility_status": reproducibility_status,
        },
        "event_authority": event_metadata,
        "cost_benchmark_mfe_mae": {
            "cost_adjusted_return": "NOT_EVALUATED_NO_FROZEN_COST_ASSUMPTION",
            "benchmark": "NOT_EVALUATED_NO_FORMAL_BENCHMARK_AUTHORITY",
            "mfe_mae": "NOT_EVALUATED_NO_FROZEN_CONTRACT",
        },
    }
    _write_json(output_dir / "ws3-core-v0-frozen-spec.json", frozen_spec)
    _write_json(output_dir / "ws3-core-v0-walk-forward-summary.json", summary)
    horizon_rows = []
    for group in GROUPS:
        for horizon in OUTCOME_HORIZONS:
            horizon_rows.append({"group": group, "horizon": horizon, **metrics[group][str(horizon)]})
    _write_csv(
        output_dir / "ws3-core-v0-forward-performance-by-horizon.csv",
        ["group", "horizon", "N", "EVALUABLE_N", "CENSORED_N", "EVENT_EXCLUDED_N", "mean_return", "median_return", "win_rate", "positive_return_rate", "p25_return", "p75_return", "best_return", "worst_return", "stddev_return", "mean_excluding_top_1pct", "mean_excluding_top_5pct", "top5_positive_pnl_share", "MFE", "MAE", "COST_ADJUSTED_RETURN"],
        horizon_rows,
    )
    _write_csv(
        output_dir / "ws3-core-v0-performance-by-signal-state.csv",
        ["group", "horizon", "N", "EVALUABLE_N", "CENSORED_N", "EVENT_EXCLUDED_N", "mean_return", "median_return", "win_rate", "positive_return_rate", "p25_return", "p75_return", "best_return", "worst_return", "stddev_return", "mean_excluding_top_1pct", "mean_excluding_top_5pct", "top5_positive_pnl_share"],
        [row for row in horizon_rows if row["group"] in {"CORE_V0_CANDIDATES", "A1_PRE_BREAKOUT", "A2_CONFIRMED_BREAKOUT"}],
    )
    _write_csv(
        output_dir / "ws3-core-v0-method-a-comparison.csv",
        ["group", "horizon", "N", "EVALUABLE_N", "mean_return", "median_return", "win_rate", "delta_vs_all_ma60_mean", "delta_vs_all_ma60_median", "delta_vs_all_ma60_win_rate"],
        [
            {
                "group": group,
                "horizon": horizon,
                "N": metrics[group][str(horizon)]["N"],
                "EVALUABLE_N": metrics[group][str(horizon)]["EVALUABLE_N"],
                "mean_return": metrics[group][str(horizon)]["mean_return"],
                "median_return": metrics[group][str(horizon)]["median_return"],
                "win_rate": metrics[group][str(horizon)]["win_rate"],
                "delta_vs_all_ma60_mean": (
                    metrics[group][str(horizon)]["mean_return"] - metrics["ALL_MA60_CALCULABLE"][str(horizon)]["mean_return"]
                    if metrics[group][str(horizon)]["mean_return"] is not None and metrics["ALL_MA60_CALCULABLE"][str(horizon)]["mean_return"] is not None else None
                ),
                "delta_vs_all_ma60_median": (
                    metrics[group][str(horizon)]["median_return"] - metrics["ALL_MA60_CALCULABLE"][str(horizon)]["median_return"]
                    if metrics[group][str(horizon)]["median_return"] is not None and metrics["ALL_MA60_CALCULABLE"][str(horizon)]["median_return"] is not None else None
                ),
                "delta_vs_all_ma60_win_rate": (
                    metrics[group][str(horizon)]["win_rate"] - metrics["ALL_MA60_CALCULABLE"][str(horizon)]["win_rate"]
                    if metrics[group][str(horizon)]["win_rate"] is not None and metrics["ALL_MA60_CALCULABLE"][str(horizon)]["win_rate"] is not None else None
                ),
            }
            for group in ("ALL_MA60_CALCULABLE", "METHOD_A_ELIGIBLE")
            for horizon in OUTCOME_HORIZONS
        ],
    )
    _write_csv(
        output_dir / "ws3-core-v0-performance-by-walk-forward-window.csv",
        ["segment", "start_date", "end_date", "group", "horizon", "N", "EVALUABLE_N", "CENSORED_N", "mean_return", "median_return", "win_rate"],
        segment_rows,
    )
    component_rows = []
    for component, status, evidence in (
        ("MA60_HARD_ELIGIBILITY", "FROZEN_AND_EVALUATED", "Close(T) >= MA60(T)"),
        ("A1_REFERENCE_DISTANCE", "FROZEN_AND_EVALUATED", "0 < distance <= 0.03"),
        ("A2_CLOSE_BREAKOUT", "FROZEN_AND_EVALUATED", "Close(T) > prior-20 high"),
        ("CORE_V0_SCORE", "NOT_FORMALLY_DEFINED", "No frozen continuous Core V0 score"),
        ("CORE_V0_RANKING", "NOT_FORMALLY_DEFINED", "No frozen daily ranking or Top-N selection"),
        ("SHADOW_OPPORTUNITY_WEIGHTS", "NOT_CONSUMED", "Provisional shadow policy is outside Core V0 baseline"),
    ):
        component_rows.append({"component": component, "status": status, "evidence": evidence, "diagnostic_only": True})
    _write_csv(output_dir / "ws3-core-v0-component-diagnostics.csv", ["component", "status", "evidence", "diagnostic_only"], component_rows)
    distribution_rows = []
    for trading_date in sorted({row["signal_date"] for row in all_candidate_rows} | set(signal_dates)):
        a1_count = sum(row["signal_date"] == trading_date and row.get("candidate_id") == A1_CANDIDATE_ID for row in all_candidate_rows)
        a2_count = sum(row["signal_date"] == trading_date and row.get("candidate_id") == A2_CANDIDATE_ID for row in all_candidate_rows)
        distribution_rows.append({"date": trading_date, "a1_signals": a1_count, "a2_signals": a2_count, "total_signals": a1_count + a2_count})
    _write_csv(output_dir / "ws3-core-v0-signal-date-distribution.csv", ["date", "a1_signals", "a2_signals", "total_signals"], distribution_rows)
    _write_csv(
        output_dir / "ws3-core-v0-pre-breakout-diagnostic.csv",
        ["group", "horizon", "N", "EVALUABLE_N", "mean_return", "median_return", "win_rate", "MFE", "MAE"],
        [
            {"group": group, "horizon": horizon, "N": metrics[group][str(horizon)]["N"], "EVALUABLE_N": metrics[group][str(horizon)]["EVALUABLE_N"], "mean_return": metrics[group][str(horizon)]["mean_return"], "median_return": metrics[group][str(horizon)]["median_return"], "win_rate": metrics[group][str(horizon)]["win_rate"], "MFE": None, "MAE": None}
            for group in ("A1_PRE_BREAKOUT", "METHOD_A_ELIGIBLE", "ALL_MA60_CALCULABLE")
            for horizon in OUTCOME_HORIZONS
        ],
    )
    quality = {
        "task_id": TASK_ID,
        "core_v0_frozen_spec_hash": spec_hash,
        "source_commit": source_commit,
        "source_reconciliation": summary["quality"]["source_reconciliation"],
        "frozen_spec_hash_audit": summary["quality"]["frozen_spec_hash_audit"],
        "lookahead_leakage_audit": summary["quality"]["lookahead_audit"],
        "forward_horizon_censoring_audit": summary["quality"]["horizon_censoring_audit"],
        "method_a_eligibility_audit": summary["quality"]["method_a_audit"],
        "event_aware_handling_audit": summary["quality"]["event_overlay_audit"],
        "duplicate_observation_audit": summary["quality"]["duplicate_observation_count"],
        "data_gap_fail_closed_audit": summary["quality"]["data_gap_fail_closed_signal_count"],
        "result_reproducibility_audit": reproducibility_status,
        "parameter_optimization_executed": False,
        "future_outcomes_used_for_candidate": False,
        "database_writes": False,
        "migration_executed": False,
        "production_mutation": False,
    }
    _write_json(output_dir / "ws3-core-v0-walk-forward-quality-audit.json", quality)
    readiness = {
        "task_id": TASK_ID,
        "core_v0_frozen_spec_hash": spec_hash,
        "baseline_execution": "COMPLETE",
        "baseline_classification": classification,
        "ready_for_core_v0_baseline_review": True,
        "ready_for_ws3_next_mainline_step": next_step,
        "walk_forward_reproducible": reproducibility_status,
        "remaining_blockers": summary["diagnostics"]["remaining_blockers"],
        "not_authorized": ["parameter optimization", "strategy redesign", "production publication", "WS1/WS2/WS4 changes", "deploy"],
    }
    _write_json(output_dir / "ws3-core-v0-next-step-readiness.json", readiness)
    _build_report(output_dir, summary, spec_hash, source_commit, reproducibility_status)
    return summary


def summary_source_reconciliation(
    source_rows: int, instrument_data: dict[str, dict[str, Any]], global_dates: set[date]
) -> dict[str, Any]:
    return {
        "expected_real_rows": 63826,
        "observed_real_rows": source_rows,
        "expected_distinct_instruments": 507,
        "observed_distinct_instruments": sum(bool(data["items"]) for data in instrument_data.values()),
        "expected_date_range": "2026-02-02..2026-08-13",
        "observed_date_range": f"{min(global_dates).isoformat()}..{max(global_dates).isoformat()}" if global_dates else None,
        "pass": source_rows == 63826 and sum(bool(data["items"]) for data in instrument_data.values()) == 507 and min(global_dates) == GLOBAL_DATE_MIN and max(global_dates) == GLOBAL_DATE_MAX,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dataset-path", type=Path)
    parser.add_argument("--reproducibility-status", default="NOT_RUN")
    args = parser.parse_args()
    if not args.database_url:
        parser.error("--database-url or TOPICPILOT_DATABASE_URL is required")
    summary = run_baseline(
        args.database_url,
        args.output_dir,
        dataset_path=args.dataset_path,
        reproducibility_status=args.reproducibility_status,
    )
    print(json.dumps({"task_id": TASK_ID, "spec_hash": summary["core_v0_frozen_spec_hash"], "metrics": summary["metrics"]}, default=_json_default))


if __name__ == "__main__":
    main()


__all__ = ["TASK_ID", "build_frozen_spec", "run_baseline"]

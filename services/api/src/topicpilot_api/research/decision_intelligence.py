# ruff: noqa: E501

"""C1 Decision Intelligence research foundation.

This module is a deterministic, research-only adapter over evidence already
committed on canonical ``main``.  It intentionally keeps research history
separate from formal history and does not read or write production tables.

The first C1 slice is descriptive and conditional rather than predictive:
it joins the current-taxonomy retrospective lifecycle reconstruction to the
existing A2 event panel, reports coverage and missingness, and computes
interpretable lifecycle x technical-state expectancy tables.  Grade, market
regime, institutional flow, and date-valid Structural Role/Leader are reported
as unavailable when the canonical evidence does not support them.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

TASK_ID = "TASK-C1-DECISION-INTELLIGENCE-RESEARCH-FOUNDATION-001"
CANONICAL_REPOSITORY = "Xiezhou0828/topicpilot-platform"
CANONICAL_BASE_SHA = "4a35867a61d7a51051261f1706604fb42d3f5b24"
SOURCE_CLASS = "HISTORICAL_RECONSTRUCTED_RESEARCH"
RESEARCH_AUTHORITY = "EVIDENCE_ONLY"
DATASET_START = date(2026, 2, 3)
DATASET_END = date(2026, 8, 13)
HORIZONS = (1, 3, 5, 10)
LIFECYCLE_STAGES = ("SPROUTING", "FERMENTING", "MAIN_RISE", "MATURE", "DECLINING")
TECHNICAL_STATES = ("ABOVE_MA60", "AT_MA60", "BELOW_MA60", "UNKNOWN")

L5_DATASET = Path(
    "reports/TASK-WS1-L5-CURRENT-TAXONOMY-HISTORICAL-LIFECYCLE-STRENGTH-RECONSTRUCTION-20260822"
) / "historical-lifecycle-strength-dataset.csv"
MAPPING_DATASET = Path("fixtures/research/topic_universe_mapping.v1.csv")
A2_PANEL = Path(
    "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820"
) / "ws3-p2e-a2-expanded-event-panel.csv"
REGIME_NOT_AVAILABLE = Path(
    "reports/TASK-WS3-A2-LEGACY5-JOINT-SIGNAL-ROBUSTNESS-AND-BENCHMARK-VALIDATION-20260822"
) / "regime-not-available.csv"
BENCHMARK_NOT_AVAILABLE = Path(
    "reports/TASK-WS3-A2-LEGACY5-JOINT-SIGNAL-ROBUSTNESS-AND-BENCHMARK-VALIDATION-20260822"
) / "benchmark-not-available.csv"
INSTITUTIONAL_SCOPE = Path(
    "reports/TASK-WS1-TOPIC-LIFECYCLE-STRENGTH-EVIDENCE-CONTRACT-RESEARCH-20260822"
) / "topic-strength-evidence-inventory.csv"

OUTPUT_FILES = (
    "c1-feature-inventory.csv",
    "c1-outcome-label-inventory.csv",
    "c1-dataset-coverage-summary.csv",
    "c1-grade-lifecycle-expectancy.csv",
    "c1-lifecycle-technical-expectancy.csv",
    "c1-market-regime-conditional-expectancy.csv",
    "c1-robustness-summary.csv",
    "c1-research-dataset.csv",
    "c1-decision-intelligence-research-report.md",
    "c1-research-manifest.json",
)


class C1ResearchError(ValueError):
    """Raised when a C1 source or contract is not safe to use."""


@dataclass(frozen=True)
class ResearchFeatureVector:
    """Model-agnostic, as-of feature carrier for later C2/Jev consumers."""

    event_id: str
    as_of: date
    topic_id: str | None
    topic_name: str
    instrument_id: str
    instrument_code: str
    market: str
    lifecycle_stage: str | None
    grade: str | None
    positive_breadth: float | None
    strong_breadth: float | None
    weak_ratio: float | None
    average_change_pct: float | None
    technical_state: str
    close: float | None
    ma60: float | None
    distance_from_ma60: float | None
    gap_up: bool | None
    research_role: str | None
    source_class: str = SOURCE_CLASS
    research_authority: str = RESEARCH_AUTHORITY
    taxonomy_pit_safe: bool = False


@dataclass(frozen=True)
class ResearchOutcomeLabel:
    """Explicit forward label with unavailable windows preserved."""

    event_id: str
    topic_id: str | None
    topic_name: str
    instrument_id: str
    signal_date: date
    horizon: int
    status: str
    target_date: date | None
    forward_return: float | None
    market_relative_return: float | None
    topic_relative_return: float | None
    mfe: float | None
    mae: float | None
    source_lineage: str
    source_class: str = SOURCE_CLASS
    research_authority: str = RESEARCH_AUTHORITY


@dataclass(frozen=True)
class ResearchDataset:
    """Joined research panel plus immutable source metadata."""

    feature_vectors: tuple[ResearchFeatureVector, ...]
    outcome_labels: tuple[ResearchOutcomeLabel, ...]
    source_metadata: dict[str, Any]


@dataclass(frozen=True)
class ResearchExperimentResult:
    """C1 output surfaces, independent of any production decision layer."""

    feature_inventory: tuple[dict[str, Any], ...]
    outcome_inventory: tuple[dict[str, Any], ...]
    coverage_summary: tuple[dict[str, Any], ...]
    grade_lifecycle: tuple[dict[str, Any], ...]
    lifecycle_technical: tuple[dict[str, Any], ...]
    market_regime: tuple[dict[str, Any], ...]
    robustness: tuple[dict[str, Any], ...]
    panel_rows: tuple[dict[str, Any], ...]
    report: str
    manifest: dict[str, Any]


def _repo_root() -> Path:
    # .../services/api/src/topicpilot_api/research/decision_intelligence.py
    return Path(__file__).resolve().parents[5]


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _as_date(value: Any) -> date | None:
    raw = _clean(value)
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _as_float(value: Any) -> float | None:
    raw = _clean(value)
    if not raw or raw.lower() in {"none", "null", "na", "nan"}:
        return None
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _as_bool(value: Any) -> bool | None:
    raw = _clean(value).upper()
    if raw in {"TRUE", "YES", "Y", "1"}:
        return True
    if raw in {"FALSE", "NO", "N", "0"}:
        return False
    return None


def _csv_value(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return "YES" if value else "NO"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if isinstance(value, float):
        return f"{value:.12g}"
    return "" if value is None else value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in fields})


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=_csv_value) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _require_files(root: Path) -> dict[str, Path]:
    paths = {
        "l5_dataset": root / L5_DATASET,
        "mapping_dataset": root / MAPPING_DATASET,
        "a2_panel": root / A2_PANEL,
        "regime_not_available": root / REGIME_NOT_AVAILABLE,
        "benchmark_not_available": root / BENCHMARK_NOT_AVAILABLE,
        "institutional_scope": root / INSTITUTIONAL_SCOPE,
    }
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise C1ResearchError("FAIL_CLOSED_SOURCE_PATH_MISSING:" + ",".join(missing))
    return paths


def _technical_state(distance: float | None) -> str:
    if distance is None:
        return "UNKNOWN"
    if distance > 0:
        return "ABOVE_MA60"
    if distance < 0:
        return "BELOW_MA60"
    return "AT_MA60"


def _load_l5(path: Path) -> tuple[list[dict[str, str]], dict[tuple[str, date], dict[str, str]], list[date]]:
    rows = _read_csv(path)
    if len(rows) != 16_250:
        raise C1ResearchError(f"FAIL_CLOSED_L5_ROW_COUNT:{len(rows)}")
    by_key: dict[tuple[str, date], dict[str, str]] = {}
    for row in rows:
        key = (_clean(row.get("topic_name")), _as_date(row.get("trading_date")))
        if not key[0] or key[1] is None:
            raise C1ResearchError("FAIL_CLOSED_L5_INVALID_TOPIC_DATE")
        if key in by_key:
            raise C1ResearchError(f"FAIL_CLOSED_L5_DUPLICATE_KEY:{key[0]}:{key[1]}")
        by_key[key] = row
    dates = sorted({key[1] for key in by_key})
    if dates != sorted(dates) or dates[0] != DATASET_START or dates[-1] != DATASET_END:
        raise C1ResearchError("FAIL_CLOSED_L5_DATE_BOUNDARY")
    return rows, by_key, dates


def _load_mapping(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    rows = _read_csv(path)
    selected: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        code = _clean(row.get("instrument_code"))
        topic = _clean(row.get("topic_name"))
        if not code or not topic:
            continue
        key = (code, topic)
        current = selected.get(key)
        if current is None:
            selected[key] = row
            continue
        # Deterministic exposure de-duplication only; this is not a Leader
        # inference and does not promote the research mapping to formal role.
        rank = {"PRIMARY": 0, "SECONDARY": 1}
        if rank.get(_clean(row.get("topic_role")).upper(), 9) < rank.get(
            _clean(current.get("topic_role")).upper(), 9
        ):
            selected[key] = row
    return selected


def _load_a2(path: Path) -> list[dict[str, str]]:
    rows = _read_csv(path)
    if len(rows) != 5_277:
        raise C1ResearchError(f"FAIL_CLOSED_A2_ROW_COUNT:{len(rows)}")
    return rows


def _future_topic_return(
    topic_name: str,
    signal_date: date,
    horizon: int,
    topic_by_key: Mapping[tuple[str, date], Mapping[str, str]],
    dates: Sequence[date],
) -> tuple[float | None, date | None]:
    try:
        index = dates.index(signal_date)
    except ValueError:
        return None, None
    future_dates = dates[index + 1 : index + horizon + 1]
    if len(future_dates) != horizon:
        return None, None
    compounded = 1.0
    for future_date in future_dates:
        change = _as_float(topic_by_key.get((topic_name, future_date), {}).get("average_change_pct"))
        if change is None:
            return None, None
        compounded *= 1.0 + change / 100.0
    return compounded - 1.0, future_dates[-1]


def build_dataset(root: Path | None = None) -> ResearchDataset:
    """Load committed research artifacts and build the bounded C1 panel."""

    source_root = root or _repo_root()
    paths = _require_files(source_root)
    l5_rows, topic_by_key, dates = _load_l5(paths["l5_dataset"])
    mapping = _load_mapping(paths["mapping_dataset"])
    a2_rows = _load_a2(paths["a2_panel"])

    exposure_rows: list[tuple[ResearchFeatureVector, dict[str, str], dict[str, str]]] = []
    counts = Counter()
    seen_exposures: set[tuple[str, str]] = set()
    for event in a2_rows:
        signal_date = _as_date(event.get("signal_date"))
        if signal_date is None or not (DATASET_START <= signal_date <= DATASET_END):
            counts["a2_outside_window"] += 1
            continue
        stock_code = _clean(event.get("stock_code"))
        matching = [item for (code, _), item in mapping.items() if code == stock_code]
        if not matching:
            counts["a2_without_current_mapping"] += 1
            continue
        for relation in sorted(matching, key=lambda item: (_clean(item.get("topic_name")), _clean(item.get("topic_role")))):
            topic_name = _clean(relation.get("topic_name"))
            topic_row = topic_by_key.get((topic_name, signal_date))
            if topic_row is None:
                counts["a2_without_l5_topic_date"] += 1
                continue
            exposure_key = (_clean(event.get("event_id")), _clean(topic_row.get("topic_id")))
            if exposure_key in seen_exposures:
                counts["duplicate_exposure_suppressed"] += 1
                continue
            seen_exposures.add(exposure_key)
            distance = _as_float(event.get("distance_from_ma60"))
            vector = ResearchFeatureVector(
                event_id=exposure_key[0],
                as_of=signal_date,
                topic_id=_clean(topic_row.get("topic_id")) or None,
                topic_name=topic_name,
                instrument_id=_clean(event.get("instrument_id")),
                instrument_code=stock_code,
                market=_clean(event.get("market")),
                lifecycle_stage=_clean(topic_row.get("lifecycle_stage")) or None,
                grade=None,
                positive_breadth=_as_float(topic_row.get("positive_breadth")),
                strong_breadth=_as_float(topic_row.get("strong_breadth")),
                weak_ratio=_as_float(topic_row.get("weak_ratio")),
                average_change_pct=_as_float(topic_row.get("average_change_pct")),
                technical_state=_technical_state(distance),
                close=_as_float(event.get("a2_close")),
                ma60=_as_float(event.get("ma60")),
                distance_from_ma60=distance,
                gap_up=_as_bool(event.get("gap_up")),
                research_role=_clean(relation.get("topic_role")) or None,
            )
            exposure_rows.append((vector, event, relation))
            counts["joined_exposure_count"] += 1

    labels: list[ResearchOutcomeLabel] = []
    panel_rows: list[dict[str, Any]] = []
    for vector, event, _relation in exposure_rows:
        for horizon in HORIZONS:
            prefix = f"observable_t{horizon}_"
            status = _clean(event.get(prefix + "status")) or "UNAVAILABLE_STATUS_MISSING"
            target_date = _as_date(event.get(prefix + "target_date"))
            forward_return = _as_float(event.get(prefix + "forward_return"))
            mfe = _as_float(event.get(prefix + "mfe"))
            mae = _as_float(event.get(prefix + "mae"))
            topic_return, topic_target_date = _future_topic_return(
                vector.topic_name, vector.as_of, horizon, topic_by_key, dates
            )
            topic_relative = None
            if status == "AVAILABLE" and forward_return is not None and topic_return is not None:
                if topic_target_date == target_date:
                    topic_relative = forward_return - topic_return
                else:
                    counts["topic_relative_target_mismatch"] += 1
            if status != "AVAILABLE":
                counts[f"outcome_{horizon}_unavailable"] += 1
            elif target_date is None or target_date <= vector.as_of:
                raise C1ResearchError(f"FAIL_CLOSED_OUTCOME_DATE:{vector.event_id}:{horizon}")
            else:
                counts[f"outcome_{horizon}_available"] += 1
            label = ResearchOutcomeLabel(
                event_id=vector.event_id,
                topic_id=vector.topic_id,
                topic_name=vector.topic_name,
                instrument_id=vector.instrument_id,
                signal_date=vector.as_of,
                horizon=horizon,
                status=status,
                target_date=target_date,
                forward_return=forward_return if status == "AVAILABLE" else None,
                market_relative_return=None,
                topic_relative_return=topic_relative,
                mfe=mfe if status == "AVAILABLE" else None,
                mae=mae if status == "AVAILABLE" else None,
                source_lineage=_clean(event.get("source_lineage_sha256")),
            )
            labels.append(label)
            panel_rows.append({**asdict(vector), **asdict(label), "research_role": vector.research_role})

    if len({(row.event_id, row.topic_id) for row in labels}) != len(seen_exposures):
        raise C1ResearchError("FAIL_CLOSED_EXPOSURE_KEY_RECONCILIATION")
    if len(labels) != len(exposure_rows) * len(HORIZONS):
        raise C1ResearchError("FAIL_CLOSED_OUTCOME_HORIZON_CARDINALITY")

    source_metadata = {
        "canonical_repository": CANONICAL_REPOSITORY,
        "canonical_base_sha": CANONICAL_BASE_SHA,
        "source_class": SOURCE_CLASS,
        "research_authority": RESEARCH_AUTHORITY,
        "dataset_start": DATASET_START.isoformat(),
        "dataset_end": DATASET_END.isoformat(),
        "trading_session_count": len(dates),
        "topic_count": len({row["topic_id"] for row in l5_rows}),
        "l5_row_count": len(l5_rows),
        "a2_row_count": len(a2_rows),
        "mapping_row_count": len(mapping),
        "joined_exposure_count": len(exposure_rows),
        "outcome_label_count": len(labels),
        "join_counts": dict(sorted(counts.items())),
        "source_files": {
            name: {"path": str(path.relative_to(source_root)), "sha256": _sha256(path)}
            for name, path in paths.items()
        },
        "pit_semantics": {
            "taxonomy": "CURRENT_TAXONOMY_FROZEN_RECONSTRUCTION",
            "taxonomy_pit_safe": False,
            "future_features_used": False,
            "formal_history_backfilled": False,
            "missing_values_inferred_as_zero": False,
        },
    }
    return ResearchDataset(tuple(vector for vector, _, _ in exposure_rows), tuple(labels), source_metadata)


def _available_labels(dataset: ResearchDataset, horizon: int) -> list[ResearchOutcomeLabel]:
    return [
        label
        for label in dataset.outcome_labels
        if label.horizon == horizon and label.status == "AVAILABLE" and label.forward_return is not None
    ]


def _mean(values: Iterable[float | None]) -> float | None:
    numbers = [value for value in values if value is not None and math.isfinite(value)]
    return statistics.fmean(numbers) if numbers else None


def _median(values: Iterable[float | None]) -> float | None:
    numbers = sorted(value for value in values if value is not None and math.isfinite(value))
    return statistics.median(numbers) if numbers else None


def _stdev(values: Iterable[float | None]) -> float | None:
    numbers = [value for value in values if value is not None and math.isfinite(value)]
    return statistics.stdev(numbers) if len(numbers) > 1 else None


def _quantile(values: Iterable[float | None], fraction: float) -> float | None:
    numbers = sorted(value for value in values if value is not None and math.isfinite(value))
    if not numbers:
        return None
    if len(numbers) == 1:
        return numbers[0]
    position = (len(numbers) - 1) * fraction
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return numbers[low]
    return numbers[low] + (numbers[high] - numbers[low]) * (position - low)


def _summary_row(
    *,
    group: Mapping[str, Any],
    labels: list[ResearchOutcomeLabel],
    total_rows: int,
    horizon: int,
    analysis: str,
) -> dict[str, Any]:
    returns = [label.forward_return for label in labels]
    mfes = [label.mfe for label in labels]
    maes = [label.mae for label in labels]
    topic_relative = [label.topic_relative_return for label in labels]
    n = len(labels)
    warnings: list[str] = []
    if n < 30:
        warnings.append("SMALL_SAMPLE_N_LT_30")
    if n < 100:
        warnings.append("SAMPLE_SIZE_WARNING_N_LT_100")
    if total_rows and n / total_rows < 0.8:
        warnings.append("OUTCOME_MISSINGNESS_OVER_20PCT")
    return {
        "analysis": analysis,
        **group,
        "horizon": horizon,
        "sample_size": n,
        "total_feature_rows": total_rows,
        "coverage": n / total_rows if total_rows else None,
        "missingness": 1 - n / total_rows if total_rows else None,
        "instrument_count": len({label.instrument_id for label in labels}),
        "topic_count": len({label.topic_name for label in labels}),
        "date_count": len({label.signal_date for label in labels}),
        "mean_forward_return": _mean(returns),
        "median_forward_return": _median(returns),
        "stdev_forward_return": _stdev(returns),
        "positive_outcome_rate": sum(value > 0 for value in returns) / n if n else None,
        "p10_forward_return": _quantile(returns, 0.10),
        "p25_forward_return": _quantile(returns, 0.25),
        "p75_forward_return": _quantile(returns, 0.75),
        "p90_forward_return": _quantile(returns, 0.90),
        "mean_topic_relative_return": _mean(topic_relative),
        "mean_mfe": _mean(mfes),
        "median_mfe": _median(mfes),
        "mean_mae": _mean(maes),
        "median_mae": _median(maes),
        "sample_warning": ";".join(warnings) if warnings else "NONE",
        "research_only": "YES",
    }


def _joined_rows(dataset: ResearchDataset, horizon: int) -> list[tuple[ResearchFeatureVector, ResearchOutcomeLabel]]:
    vectors = {(vector.event_id, vector.topic_id): vector for vector in dataset.feature_vectors}
    return [
        (vectors[(label.event_id, label.topic_id)], label)
        for label in dataset.outcome_labels
        if label.horizon == horizon
    ]


def _expectancy_tables(dataset: ResearchDataset) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lifecycle_technical: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        pairs = _joined_rows(dataset, horizon)
        for lifecycle in LIFECYCLE_STAGES:
            for technical_state in TECHNICAL_STATES:
                feature_rows = [
                    (vector, label)
                    for vector, label in pairs
                    if vector.lifecycle_stage == lifecycle and vector.technical_state == technical_state
                ]
                labels = [label for _, label in feature_rows if label.status == "AVAILABLE" and label.forward_return is not None]
                lifecycle_technical.append(
                    _summary_row(
                        group={"lifecycle_stage": lifecycle, "technical_state": technical_state},
                        labels=labels,
                        total_rows=len(feature_rows),
                        horizon=horizon,
                        analysis="LIFECYCLE_X_TECHNICAL_EXPECTANCY",
                    )
                )

    # The grade field is deliberately not imputed from lifecycle, raw breadth,
    # mapping role, or any other proxy.  Emit a stable schema row per horizon.
    grade_lifecycle = [
        {
            "analysis": "GRADE_X_LIFECYCLE_EXPECTANCY",
            "grade": "UNKNOWN",
            "lifecycle_stage": "UNKNOWN",
            "horizon": horizon,
            "status": "INSUFFICIENT_HISTORICAL_GRADE",
            "sample_size": 0,
            "mean_forward_return": None,
            "median_forward_return": None,
            "positive_outcome_rate": None,
            "mean_mfe": None,
            "mean_mae": None,
            "coverage": 0.0,
            "missingness": 1.0,
            "sample_warning": "NO_PIT_GRADE_SOURCE_ON_CANONICAL_MAIN",
            "research_only": "YES",
        }
        for horizon in HORIZONS
    ]
    return grade_lifecycle, lifecycle_technical


def _feature_inventory(dataset: ResearchDataset) -> list[dict[str, Any]]:
    vectors = list(dataset.feature_vectors)
    labels = list(dataset.outcome_labels)
    vector_count = len(vectors)
    def count_non_null(values: Iterable[Any]) -> int:
        return sum(value not in (None, "") for value in values)

    def row(feature_id: str, layer: str, definition: str, values: Iterable[Any], status: str, decision: str, note: str) -> dict[str, Any]:
        available = count_non_null(values)
        return {
            "feature_id": feature_id,
            "layer": layer,
            "definition": definition,
            "source_class": SOURCE_CLASS,
            "row_count": vector_count,
            "available_count": available,
            "coverage": available / vector_count if vector_count else 0.0,
            "as_of_safe": "YES" if status == "AVAILABLE" else "UNKNOWN",
            "historical_semantics": "RESEARCH_ONLY_CURRENT_TAXONOMY_RECONSTRUCTION",
            "status": status,
            "decision": decision,
            "note": note,
            "research_authority": RESEARCH_AUTHORITY,
        }

    return [
        row("topic.lifecycle", "TOPIC", "Lifecycle stage from L5 retrospective reconstruction", (v.lifecycle_stage for v in vectors), "AVAILABLE", "C2_CANDIDATE", "Not PIT formal history"),
        row("topic.positive_breadth", "TOPIC", "Positive breadth at as_of", (v.positive_breadth for v in vectors), "AVAILABLE", "C2_CANDIDATE", "Existing WS1/L5 raw evidence"),
        row("topic.strong_breadth", "TOPIC", "Strong breadth at as_of", (v.strong_breadth for v in vectors), "AVAILABLE", "C2_CANDIDATE", "Existing WS1/L5 raw evidence"),
        row("topic.weak_ratio", "TOPIC", "Weak ratio at as_of", (v.weak_ratio for v in vectors), "AVAILABLE", "DEFER_PENDING_ROBUSTNESS", "Existing WS1/L5 raw evidence"),
        row("topic.average_change_pct", "TOPIC", "Average topic member change at as_of", (v.average_change_pct for v in vectors), "AVAILABLE", "C2_CANDIDATE", "Existing WS1/L5 raw evidence"),
        row("topic.daily_grade", "TOPIC", "Formal Daily Grade at as_of", (v.grade for v in vectors), "INSUFFICIENT", "DEFER", "No PIT Grade history is committed on canonical main"),
        row("stock.ma60_state", "TECHNICAL", "Close relative to existing MA60 research input", (v.technical_state for v in vectors), "AVAILABLE", "C2_CANDIDATE", "Existing A2 panel; descriptive only"),
        row("stock.distance_from_ma60", "TECHNICAL", "A2 distance from MA60", (v.distance_from_ma60 for v in vectors), "AVAILABLE", "DEFER_PENDING_ROBUSTNESS", "Research feature, not formal publication"),
        row("stock.gap_up", "TECHNICAL", "A2 gap-up flag", (v.gap_up for v in vectors), "AVAILABLE", "DEFER_PENDING_ROBUSTNESS", "Not used for group selection in C1"),
        row("market.regime", "MARKET", "Versioned PIT market regime", (None for _ in vectors), "INSUFFICIENT", "DEFER", "Canonical report records no PIT-safe regime source"),
        row("institutional.flow", "FLOW", "Historical foreign/trust/dealer flow", (None for _ in vectors), "INSUFFICIENT", "DEFER", "Historical lineage/source is unavailable"),
        row("structural_role.leader", "AUTHORITY", "Date-valid owner-curated Structural Role/Leader", (None for _ in vectors), "UNKNOWN", "DEFER", "Research mapping role is not formal Structural Role/Leader"),
        row("mapping.current_taxonomy", "LINEAGE", "Current taxonomy exposure mapping", (v.topic_name for v in vectors), "AVAILABLE", "USE_WITH_LIMITATION", "Not PIT truth; never promoted to formal history"),
        row("outcome.market_relative_return", "OUTCOME", "Forward return relative to market benchmark", (label.market_relative_return for label in labels), "INSUFFICIENT", "DEFER", "No committed PIT-safe market series"),
    ]


def _outcome_inventory(dataset: ResearchDataset) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        labels = [label for label in dataset.outcome_labels if label.horizon == horizon]
        for name, values, status, note in (
            ("forward_return", [label.forward_return for label in labels], "AVAILABLE", "A2 observable endpoint"),
            ("market_relative_return", [label.market_relative_return for label in labels], "INSUFFICIENT", "No PIT-safe market benchmark"),
            ("topic_relative_return", [label.topic_relative_return for label in labels], "AVAILABLE_WHERE_TOPIC_WINDOW_MATCHES", "Current-taxonomy reconstructed topic return"),
            ("mfe", [label.mfe for label in labels], "AVAILABLE", "A2 path-aware MFE"),
            ("mae", [label.mae for label in labels], "AVAILABLE", "A2 path-aware MAE"),
        ):
            count = sum(value is not None for value in values)
            rows.append({
                "label_id": f"{name}_t{horizon}",
                "horizon": horizon,
                "label": name,
                "total_rows": len(labels),
                "available_rows": count,
                "coverage": count / len(labels) if labels else 0.0,
                "status": status if count else "INSUFFICIENT",
                "as_of_safe": "YES" if name != "market_relative_return" else "NO",
                "target_arithmetic": "TRADING_SESSION_OFFSET",
                "note": note,
                "source_class": SOURCE_CLASS,
                "research_authority": RESEARCH_AUTHORITY,
            })
    return rows


def _coverage_summary(dataset: ResearchDataset, feature_inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    meta = dataset.source_metadata
    vector_count = len(dataset.feature_vectors)
    complete_labels = {
        horizon: len(_available_labels(dataset, horizon)) for horizon in HORIZONS
    }
    return [
        {
            "dataset_id": "L5_TOPIC_FEATURES",
            "source_path": str(L5_DATASET),
            "source_class": SOURCE_CLASS,
            "row_count": meta["l5_row_count"],
            "session_count": meta["trading_session_count"],
            "topic_count": meta["topic_count"],
            "instrument_count": "UNKNOWN_TOPIC_AGGREGATE",
            "date_start": meta["dataset_start"],
            "date_end": meta["dataset_end"],
            "coverage_status": "AVAILABLE_RESEARCH_ONLY",
            "lineage_status": "PARTIAL_CURRENT_TAXONOMY_NOT_PIT",
            "note": "Reuse existing WS1/L5 reconstruction; formal history not backfilled",
        },
        {
            "dataset_id": "A2_TECHNICAL_OUTCOMES",
            "source_path": str(A2_PANEL),
            "source_class": SOURCE_CLASS,
            "row_count": meta["a2_row_count"],
            "session_count": "WINDOW_FILTERED",
            "topic_count": "JOINED_BELOW",
            "instrument_count": "A2_EVENT_INSTRUMENTS",
            "date_start": meta["dataset_start"],
            "date_end": meta["dataset_end"],
            "coverage_status": "AVAILABLE_BOUNDED",
            "lineage_status": "RAW_PATH_RECONSTRUCTION",
            "note": "Existing A2 panel supplies T+1/3/5/10, MA60, MFE and MAE",
        },
        {
            "dataset_id": "C1_JOINED_PANEL",
            "source_path": "generated_from_committed_sources",
            "source_class": SOURCE_CLASS,
            "row_count": vector_count,
            "session_count": meta["trading_session_count"],
            "topic_count": len({vector.topic_id for vector in dataset.feature_vectors}),
            "instrument_count": len({vector.instrument_id for vector in dataset.feature_vectors}),
            "date_start": meta["dataset_start"],
            "date_end": meta["dataset_end"],
            "coverage_status": "AVAILABLE_WITH_EXPLICIT_MISSINGNESS",
            "lineage_status": "RESEARCH_ONLY_NOT_PIT",
            "note": json.dumps({"complete_outcomes_by_horizon": complete_labels, "feature_inventory": len(feature_inventory)}, sort_keys=True),
        },
        {
            "dataset_id": "MARKET_REGIME",
            "source_path": str(REGIME_NOT_AVAILABLE),
            "source_class": SOURCE_CLASS,
            "row_count": 0,
            "session_count": 0,
            "topic_count": 0,
            "instrument_count": 0,
            "date_start": None,
            "date_end": None,
            "coverage_status": "INSUFFICIENT_FOR_RESEARCH",
            "lineage_status": "NO_PIT_SAFE_SOURCE",
            "note": "Existing WS3 artifact explicitly records missing regime source",
        },
        {
            "dataset_id": "INSTITUTIONAL_FLOW",
            "source_path": str(INSTITUTIONAL_SCOPE),
            "source_class": SOURCE_CLASS,
            "row_count": 0,
            "session_count": 0,
            "topic_count": 0,
            "instrument_count": 0,
            "date_start": None,
            "date_end": None,
            "coverage_status": "INSUFFICIENT_FOR_RESEARCH",
            "lineage_status": "NO_HISTORICAL_LINEAGE",
            "note": "Existing lifecycle evidence inventory excludes institutional flow",
        },
    ]


def _trimmed_mean(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    cut = int(len(ordered) * 0.05)
    retained = ordered[cut: len(ordered) - cut] if len(ordered) > 2 * cut else ordered
    return statistics.fmean(retained) if retained else None


def _concentration(labels: list[ResearchOutcomeLabel], field: str) -> float | None:
    if not labels:
        return None
    counts = Counter(getattr(label, field) for label in labels)
    return max(counts.values()) / len(labels) if counts else None


def _robustness(dataset: ResearchDataset) -> list[dict[str, Any]]:
    vectors = {(vector.event_id, vector.topic_id): vector for vector in dataset.feature_vectors}
    unique_dates = sorted({vector.as_of for vector in dataset.feature_vectors})
    split_index = max(1, len(unique_dates) // 2)
    split_cut = unique_dates[split_index - 1] if unique_dates else DATASET_START
    rows: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        labels = [label for label in dataset.outcome_labels if label.horizon == horizon and label.status == "AVAILABLE" and label.forward_return is not None]
        groups: list[tuple[str, list[ResearchOutcomeLabel]]] = [("UNCONDITIONAL", labels)]
        for lifecycle in LIFECYCLE_STAGES:
            selected = [label for label in labels if vectors[(label.event_id, label.topic_id)].lifecycle_stage == lifecycle]
            groups.append((f"LIFECYCLE:{lifecycle}", selected))
        for technical_state in TECHNICAL_STATES:
            selected = [label for label in labels if vectors[(label.event_id, label.topic_id)].technical_state == technical_state]
            groups.append((f"TECHNICAL:{technical_state}", selected))
        for group_name, selected in groups:
            values = [label.forward_return for label in selected if label.forward_return is not None]
            earlier = [value for label, value in ((label, label.forward_return) for label in selected) if value is not None and label.signal_date <= split_cut]
            later = [value for label, value in ((label, label.forward_return) for label in selected) if value is not None and label.signal_date > split_cut]
            warnings: list[str] = []
            if len(selected) < 30:
                warnings.append("SMALL_SAMPLE")
            if _concentration(selected, "instrument_id") is not None and _concentration(selected, "instrument_id") > 0.25:
                warnings.append("INSTRUMENT_CONCENTRATION_OVER_25PCT")
            if _concentration(selected, "signal_date") is not None and _concentration(selected, "signal_date") > 0.25:
                warnings.append("DATE_CONCENTRATION_OVER_25PCT")
            if len(earlier) < 10 or len(later) < 10:
                warnings.append("TIME_SPLIT_SAMPLE_WARNING")
            rows.append({
                "study": "ROBUSTNESS_AND_BASELINES",
                "horizon": horizon,
                "group": group_name,
                "sample_size": len(selected),
                "instrument_count": len({label.instrument_id for label in selected}),
                "topic_count": len({label.topic_name for label in selected}),
                "date_count": len({label.signal_date for label in selected}),
                "mean_forward_return": _mean(values),
                "trimmed5_mean_forward_return": _trimmed_mean(values),
                "earlier_sample_size": len(earlier),
                "later_sample_size": len(later),
                "earlier_mean_forward_return": _mean(earlier),
                "later_mean_forward_return": _mean(later),
                "later_minus_earlier": (_mean(later) - _mean(earlier)) if earlier and later else None,
                "top1_instrument_share": _concentration(selected, "instrument_id"),
                "top1_topic_share": _concentration(selected, "topic_name"),
                "top1_date_share": _concentration(selected, "signal_date"),
                "status": "DESCRIPTIVE_ONLY",
                "sample_warning": ";".join(warnings) if warnings else "NONE",
                "promotion_decision": "DEFER_TO_C2",
            })
    # Explicit baseline inventory required by the task.  Grade-dependent and
    # adjusted-market candidates remain deferred rather than simulated.
    for name, status, note in (
        ("GRADE_ONLY", "DEFERRED", "PIT Grade history unavailable"),
        ("GRADE_LIFECYCLE", "DEFERRED", "PIT Grade history unavailable"),
        ("SIMPLE_LOGISTIC", "DEFERRED", "No Grade/regime feature contract; do not fit a proxy"),
        ("SIMPLE_LINEAR", "DEFERRED", "C1 remains descriptive until full feature contract is available"),
    ):
        for horizon in HORIZONS:
            rows.append({
                "study": "BASELINE_CANDIDATE",
                "horizon": horizon,
                "group": name,
                "sample_size": 0,
                "instrument_count": 0,
                "topic_count": 0,
                "date_count": 0,
                "mean_forward_return": None,
                "trimmed5_mean_forward_return": None,
                "earlier_sample_size": 0,
                "later_sample_size": 0,
                "earlier_mean_forward_return": None,
                "later_mean_forward_return": None,
                "later_minus_earlier": None,
                "top1_instrument_share": None,
                "top1_topic_share": None,
                "top1_date_share": None,
                "status": status,
                "sample_warning": note,
                "promotion_decision": "DEFER",
            })
    return rows


def _market_regime_rows() -> list[dict[str, Any]]:
    return [
        {
            "analysis": "MARKET_REGIME_X_GRADE_X_LIFECYCLE",
            "market_regime": "UNKNOWN",
            "grade": "UNKNOWN",
            "lifecycle_stage": "UNKNOWN",
            "horizon": horizon,
            "status": "INSUFFICIENT_MARKET_REGIME_HISTORY",
            "sample_size": 0,
            "coverage": 0.0,
            "missingness": 1.0,
            "mean_forward_return": None,
            "positive_outcome_rate": None,
            "sample_warning": "NO_PIT_SAFE_INDEX_BREADTH_OR_TURNOVER_SOURCE",
            "research_only": "YES",
        }
        for horizon in HORIZONS
    ]


def _research_dataset_fields() -> list[str]:
    return [
        "event_id", "as_of", "topic_id", "topic_name", "instrument_id", "instrument_code", "market",
        "lifecycle_stage", "grade", "positive_breadth", "strong_breadth", "weak_ratio",
        "average_change_pct", "technical_state", "close", "ma60", "distance_from_ma60", "gap_up",
        "research_role", "signal_date", "horizon", "status", "target_date", "forward_return",
        "market_relative_return", "topic_relative_return", "mfe", "mae", "source_lineage",
        "source_class", "research_authority",
    ]


def _render_report(
    dataset: ResearchDataset,
    feature_inventory: list[dict[str, Any]],
    outcome_inventory: list[dict[str, Any]],
    coverage: list[dict[str, Any]],
    grade_lifecycle: list[dict[str, Any]],
    lifecycle_technical: list[dict[str, Any]],
    market_regime: list[dict[str, Any]],
    robustness: list[dict[str, Any]],
) -> str:
    available = {h: len(_available_labels(dataset, h)) for h in HORIZONS}
    lifecycle_candidates = [
        row for row in lifecycle_technical
        if row["sample_size"] >= 30 and row["sample_warning"] in {"NONE", "OUTCOME_MISSINGNESS_OVER_20PCT"}
    ]
    candidate_names = sorted({f"{row['lifecycle_stage']} x {row['technical_state']}" for row in lifecycle_candidates})
    return f"""# C1 Decision Intelligence Research Foundation

**Task:** `{TASK_ID}`
**Canonical base:** `{CANONICAL_REPOSITORY}@{CANONICAL_BASE_SHA}`
**Authority:** `{RESEARCH_AUTHORITY}`
**Mode:** deterministic, research-only, no production mutation

## Final status

`C1_RESEARCH_FOUNDATION_STATUS=PARTIAL_RESEARCH_FOUNDATION_WITH_EXPLICIT_DATA_GAPS`

The foundation is replayable for the committed L5 current-taxonomy
reconstruction and A2 technical/outcome panel. It is not formal historical
truth and cannot affect Score, Grade, Lifecycle, eligibility, ranking, or any
decision layer until owner review, C2 validation, formal contract creation,
and integration into canonical `main`.

## Existing research archaeology

`EXISTING_RESEARCH_REUSABLE=WS1/L5 lifecycle-strength reconstruction; WS3 technical x lifecycle conditional expectancy; WS3 A2 outcome/MFE/MAE panel; WS3 regime-not-available and benchmark-not-available disclosures`

`EXISTING_RESEARCH_GAPS=PIT Daily Grade history; PIT market regime series; historical institutional flow lineage; date-valid Structural Role/Leader history; market-relative benchmark`

`DUPLICATE_RESEARCH_AVOIDED=YES`

The implementation reuses committed evidence rather than recreating the WS1
or WS3 pipelines. The current taxonomy mapping is retained only as an
explicit research join and is marked `taxonomy_pit_safe=false`.

## Dataset design

- L5 source: 16,250 topic/date rows, {dataset.source_metadata['trading_session_count']} sessions, {dataset.source_metadata['topic_count']} topics, bounded to `{DATASET_START}`-`{DATASET_END}`.
- A2 source: 5,277 event rows; only signal dates inside the L5 window are joined.
- Joined C1 feature exposures: {len(dataset.feature_vectors)}; outcome labels: {len(dataset.outcome_labels)}.
- Every label uses trading-session horizon arithmetic from the committed A2 panel. A target date is never used to form the same-date feature group.
- Missing values remain unavailable; no value is inferred as zero.

## Feature coverage

| Feature family | Status | Interpretation |
|---|---|---|
| Lifecycle / breadth / structure | AVAILABLE_RESEARCH_ONLY | Reused L5 raw evidence; current taxonomy retrospective, not PIT |
| Technical MA60 state | AVAILABLE_RESEARCH_ONLY | Existing A2 research input; descriptive grouping only |
| Daily Grade | INSUFFICIENT | No canonical PIT Grade history; no proxy imputation |
| Market Regime | INSUFFICIENT | Canonical WS3 artifact explicitly records missing PIT-safe source |
| Institutional Flow | INSUFFICIENT | Historical lineage unavailable; no fabricated flow |
| Structural Role / Leader | UNKNOWN | Owner-curated authority unavailable for the historical window |

## Outcome coverage

| Horizon | Available forward labels | MFE/MAE source |
|---:|---:|---|
{chr(10).join(f"| T+{h} | {available[h]} | A2 path-aware panel; status preserved |" for h in HORIZONS)}

`market_relative_return` is unavailable because the canonical repository does
not contain a PIT-safe market benchmark for this study. `topic_relative_return`
is only populated when the current-taxonomy topic window and A2 target session
match exactly; it is not formal topic history.

## Conditional expectancy results

The generated `c1-lifecycle-technical-expectancy.csv` contains sample size,
coverage, missingness, mean/median, standard deviation, win rate, quantiles,
MFE, MAE, and sample warnings for each Lifecycle x MA60 state x horizon.
{len(lifecycle_candidates)} cells meet the descriptive minimum of 30 complete
labels without a flagged small-sample warning. Candidate cells are:
`{', '.join(candidate_names) if candidate_names else 'NONE'}`.

The Grade x Lifecycle and Market Regime x Grade x Lifecycle tables are emitted
with explicit unavailable status, not fabricated combinations.

## Robustness analysis

The robustness surface includes earlier/later time splits, instrument/topic/date
concentration, trimmed means, missingness, and sample-size warnings. These are
descriptive diagnostics only. No group is called good or bad, and no threshold
is promoted into product policy.

Baseline status:

- unconditional, Lifecycle-only, and Technical-only descriptive baselines are available;
- Grade-only and Grade x Lifecycle are deferred for missing PIT Grade history;
- simple logistic and linear baselines are deferred until the feature contract is complete, so no proxy model is silently introduced.

## C2 disposition

`C2_PROMOTION_CANDIDATES={'; '.join(candidate_names) if candidate_names else 'NONE_PENDING_REVIEW'}`

`DEFERRED_FEATURES=Daily Grade; Market Regime; Institutional Flow; Structural Role/Leader; market-relative return; logistic/linear model baselines`

`REJECTED_FEATURES=none; no feature was rejected from evidence, but no unavailable feature was synthesized`

Lifecycle and MA60 state are candidates for C2 validation only. They remain
research evidence and are not production policy.

## Governance and replay checks

- `NO_LOOKAHEAD_VALIDATION=PASS`: only as-of L5/A2 feature columns form groups; future columns are consumed as labels only.
- `DUPLICATE_KEY_CHECK=PASS`: one `(event_id, topic_id, horizon)` label per joined exposure.
- `FUTURE_WINDOW_BOUNDARY_CHECK=PASS`: available targets are strictly later than signal dates; incomplete windows retain unavailable status.
- `RESEARCH_FORMAL_AUTHORITY_SEPARATION=PASS`: source class is `{SOURCE_CLASS}` and output authority is `{RESEARCH_AUTHORITY}`.
- `JEV_INTEGRATION_READY=YES`; `JEV_INTEGRATION_IMPLEMENTED=NO`.
- `FORMAL_POLICY_CHANGED=NO`; `PRODUCTION_MUTATION=NO`; `DEPLOYMENT=NO`; `MIGRATION=NO`.

## Canonical provenance and CI

This candidate was built from a clean isolated worktree based on
`{CANONICAL_REPOSITORY}@{CANONICAL_BASE_SHA}`. It is not canonical until the
accepted implementation and artifacts are integrated into `main` and re-run at
the exact integration SHA.

The GitHub Actions CI run `35684511356` for canonical `main` at
`{CANONICAL_BASE_SHA}` was completed with `failure`: the backend Ruff no-new-debt
gate passed, but the changed-scope gate reported the pre-existing import-order
finding `I001` in
`services/api/alembic/versions/0037_task_b2_lifecycle_v1_3_formal_publication.py`;
the frontend job and secret scan passed. This task does not treat local focused
tests as a replacement for that remote CI evidence.

## Files and limitations

The artifact directory contains the feature inventory, outcome inventory,
coverage summary, conditional expectancy tables, robustness summary, joined
research dataset, manifest, and this report. Institutional flow is not emitted
as an expectancy table because its canonical status is
`INSUFFICIENT_FOR_RESEARCH`.

Remaining blockers are PIT historical Topic/Grade/Lifecycle authority, a
versioned market regime source, institutional history with lineage, date-valid
Structural Role/Leader authority, and a clean CI baseline. The next action is
to review this evidence and either provide those authorities for C2 or formally
defer the missing feature families.
"""


def run_c1(
    output_dir: Path,
    *,
    source_root: Path | None = None,
    implementation_head: str = "WORKTREE_PENDING_INTEGRATION",
) -> ResearchExperimentResult:
    """Run C1 and write all required evidence-only artifacts."""

    dataset = build_dataset(source_root)
    feature_inventory = _feature_inventory(dataset)
    outcome_inventory = _outcome_inventory(dataset)
    coverage = _coverage_summary(dataset, feature_inventory)
    grade_lifecycle, lifecycle_technical = _expectancy_tables(dataset)
    market_regime = _market_regime_rows()
    robustness = _robustness(dataset)
    report = _render_report(
        dataset,
        feature_inventory,
        outcome_inventory,
        coverage,
        grade_lifecycle,
        lifecycle_technical,
        market_regime,
        robustness,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "c1-feature-inventory.csv", feature_inventory, list(feature_inventory[0]))
    _write_csv(output_dir / "c1-outcome-label-inventory.csv", outcome_inventory, list(outcome_inventory[0]))
    _write_csv(output_dir / "c1-dataset-coverage-summary.csv", coverage, list(coverage[0]))
    _write_csv(output_dir / "c1-grade-lifecycle-expectancy.csv", grade_lifecycle, list(grade_lifecycle[0]))
    _write_csv(output_dir / "c1-lifecycle-technical-expectancy.csv", lifecycle_technical, list(lifecycle_technical[0]))
    _write_csv(output_dir / "c1-market-regime-conditional-expectancy.csv", market_regime, list(market_regime[0]))
    _write_csv(output_dir / "c1-robustness-summary.csv", robustness, list(robustness[0]))
    _write_csv(output_dir / "c1-research-dataset.csv", dataset_panel_rows(dataset), _research_dataset_fields())
    (output_dir / "c1-decision-intelligence-research-report.md").write_text(
        report,
        encoding="utf-8",
        newline="\n",
    )

    artifact_hashes = {
        name: _sha256(output_dir / name)
        for name in OUTPUT_FILES
        if name != "c1-research-manifest.json"
    }
    manifest = {
        "task_id": TASK_ID,
        "canonical_repository": CANONICAL_REPOSITORY,
        "canonical_base": CANONICAL_BASE_SHA,
        "implementation_head": implementation_head,
        "main_integration_commit": None,
        "canonical_adoption": "NOT_CANONICAL_UNTIL_MAIN_INTEGRATION",
        "source_class": SOURCE_CLASS,
        "research_authority": RESEARCH_AUTHORITY,
        "dataset": dataset.source_metadata,
        "required_outputs": list(OUTPUT_FILES),
        "artifact_sha256": artifact_hashes,
        "contracts": {
            "no_lookahead": "PASS",
            "duplicate_key": "PASS",
            "future_window_boundary": "PASS",
            "formal_research_separation": "PASS",
            "formal_policy_changed": False,
            "production_mutation": False,
            "deployment": False,
            "migration": False,
            "jev_integration_ready": True,
            "jev_integration_implemented": False,
        },
        "feature_status": {
            "grade": "INSUFFICIENT_FOR_RESEARCH",
            "market_regime": "INSUFFICIENT_FOR_RESEARCH",
            "institutional_flow": "INSUFFICIENT_FOR_RESEARCH",
            "structural_role_leader": "UNKNOWN_FOR_HISTORICAL_WINDOW",
            "market_relative_return": "INSUFFICIENT_FOR_RESEARCH",
        },
        "remote_ci_evidence": {
            "main_sha": CANONICAL_BASE_SHA,
            "workflow_run_id": 35684511356,
            "run_state": "COMPLETED_FAILURE",
            "backend": "FAIL_RUFF_CHANGED_SCOPE_PRE_EXISTING_MIGRATION_I001",
            "frontend": "PASS",
            "secret_scan": "PASS",
            "canonical_evidence_only": True,
        },
    }
    _write_json(output_dir / "c1-research-manifest.json", manifest)
    return ResearchExperimentResult(
        tuple(feature_inventory),
        tuple(outcome_inventory),
        tuple(coverage),
        tuple(grade_lifecycle),
        tuple(lifecycle_technical),
        tuple(market_regime),
        tuple(robustness),
        tuple(dataset_panel_rows(dataset)),
        report,
        manifest,
    )


def dataset_panel_rows(dataset: ResearchDataset) -> list[dict[str, Any]]:
    vectors = {(vector.event_id, vector.topic_id): vector for vector in dataset.feature_vectors}
    rows: list[dict[str, Any]] = []
    for label in dataset.outcome_labels:
        vector = vectors[(label.event_id, label.topic_id)]
        row = {**asdict(vector), **asdict(label)}
        row["research_role"] = vector.research_role
        rows.append(row)
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--implementation-head", default="WORKTREE_PENDING_INTEGRATION")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_c1(
        args.output_dir,
        source_root=args.source_root,
        implementation_head=args.implementation_head,
    )
    print(json.dumps({
        "task_id": TASK_ID,
        "canonical_base": CANONICAL_BASE_SHA,
        "joined_exposures": len(result.panel_rows) // len(HORIZONS),
        "outcome_labels": len(result.panel_rows),
        "canonical_adoption": result.manifest["canonical_adoption"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CANONICAL_BASE_SHA",
    "CANONICAL_REPOSITORY",
    "C1ResearchError",
    "ResearchDataset",
    "ResearchExperimentResult",
    "ResearchFeatureVector",
    "ResearchOutcomeLabel",
    "build_dataset",
    "dataset_panel_rows",
    "run_c1",
]

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from math import isfinite
from typing import Any

from .config import DetectorConfig
from .context import DetectorContext
from .contracts import Result, Status
from .registry import DetectorEntry, DetectorRegistry
from .result import DetectorResult, Diagnostics, Evidence

DETECTOR_ID = "DET_RANGE_V1"
DETECTOR_VERSION = "1.0"
CONTRACT_VERSION = "1"
DEFAULT_CONFIG = {
    "lookback": 20,
    "boundary_tolerance": 0.02,
    "minimum_touches": 2,
    "minimum_duration": 10,
    "max_directional_expansion_ratio": 0.75,
}


def register_range_detector(registry: DetectorRegistry) -> None:
    """Register the versioned range detector explicitly."""
    detector = RangeDetector()
    registry.register(
        DetectorEntry(
            DETECTOR_ID,
            DETECTOR_VERSION,
            detector,
            input_profiles=frozenset({"synthetic", "market_ohlc_v1"}),
            timeframes=frozenset({"DAILY", "1d"}),
        )
    )


class RangeDetector:
    detector_id = DETECTOR_ID
    detector_version = DETECTOR_VERSION
    contract_version = CONTRACT_VERSION

    def evaluate(self, context: DetectorContext, config: DetectorConfig) -> DetectorResult:
        values = {**DEFAULT_CONFIG, **dict(config.values)}
        invalid = _validate_config(values)
        if invalid:
            return _invalid(context, config, invalid)
        payload = context.input_payload
        candles = payload.get("candles") if isinstance(payload, Mapping) else None
        if not isinstance(candles, (list, tuple)):
            return _invalid(context, config, "candles must be a list")
        parsed: list[tuple[str, float, float, float]] = []
        previous = None
        try:
            for candle in candles:
                if not isinstance(candle, Mapping):
                    raise ValueError("candle must be an object")
                day = str(candle["date"])
                date.fromisoformat(day)
                open_, high, low, close = (
                    float(candle[k]) for k in ("open", "high", "low", "close")
                )
                if not all(isfinite(x) for x in (open_, high, low, close)) or not (
                    low <= open_ <= high and low <= close <= high
                ):
                    raise ValueError("invalid OHLC relationship")
                if previous is not None and day <= previous:
                    raise ValueError("dates must be strictly increasing")
                previous = day
                parsed.append((day, low, high, close))
        except (KeyError, TypeError, ValueError) as exc:
            return _invalid(context, config, str(exc))
        lookback = int(values["lookback"])
        if len(parsed) < lookback:
            return _unknown(context, config, "INSUFFICIENT_HISTORY", "insufficient lookback")
        window = parsed[-lookback:]
        support = min(row[1] for row in window)
        resistance = max(row[2] for row in window)
        tolerance = float(values["boundary_tolerance"])
        support_touches = sum(
            abs(low - support) / max(abs(support), 1e-12) <= tolerance
            for _, low, _, _ in window
        )
        resistance_touches = sum(
            abs(high - resistance) / max(abs(resistance), 1e-12) <= tolerance
            for _, _, high, _ in window
        )
        duration = len(window)
        width = resistance - support
        directional_expansion_ratio = (
            abs(window[-1][3] - window[0][3]) / width if width > 0 else float("inf")
        )
        minimum_touches = int(values["minimum_touches"])
        minimum_duration = int(values["minimum_duration"])
        maximum_expansion = float(values["max_directional_expansion_ratio"])
        touch_score = min(
            1.0,
            (support_touches + resistance_touches) / (2 * minimum_touches),
        )
        duration_score = min(1.0, duration / minimum_duration)
        compression_score = (
            max(0.0, 1.0 - directional_expansion_ratio / maximum_expansion)
            if maximum_expansion > 0 and isfinite(directional_expansion_ratio)
            else 0.0
        )
        confidence = round(
            0.4 * touch_score + 0.3 * duration_score + 0.3 * compression_score,
            6,
        )
        qualifies = (
            support_touches >= minimum_touches
            and resistance_touches >= minimum_touches
            and duration >= minimum_duration
            and width > 0
            and directional_expansion_ratio <= maximum_expansion
        )
        evidence = Evidence(
            summary="stable trading range" if qualifies else "no qualifying trading range",
            facts={
                "support": support,
                "resistance": resistance,
                "support_touch_count": support_touches,
                "resistance_touch_count": resistance_touches,
                "range_width": width,
                "range_width_unit": "price",
                "timeframe": context.timeframe,
                "directional_expansion_ratio": directional_expansion_ratio,
                "touch_score": touch_score,
                "duration_score": duration_score,
                "compression_score": compression_score,
                "confidence_method": "weighted_average(touch=0.4,duration=0.3,compression=0.3)",
                "stability": "STABLE" if qualifies else "UNSTABLE",
                "lookback": lookback,
            },
            observation_window=f"{window[0][0]}/{window[-1][0]}",
            lineage_reference=context.lineage.input_hash,
        )
        return _result(
            context,
            config,
            Result.PASS if qualifies else Result.FAIL,
            evidence,
            confidence,
            "EVALUATED",
        )


def _validate_config(v: dict[str, Any]) -> str | None:
    try:
        if (
            int(v["lookback"]) < 1
            or int(v["minimum_touches"]) < 1
            or int(v["minimum_duration"]) < 1
        ):
            return "configuration values must be positive"
        if not 0 <= float(v["boundary_tolerance"]) <= 1:
            return "boundary_tolerance must be between 0 and 1"
        if not 0 <= float(v["max_directional_expansion_ratio"]) <= 1:
            return "max_directional_expansion_ratio must be between 0 and 1"
    except (KeyError, TypeError, ValueError):
        return "invalid range configuration"
    return None


def _result(c, cfg, result, evidence, confidence, code):
    return DetectorResult(
        DETECTOR_ID,
        DETECTOR_VERSION,
        result,
        Status.COMPLETED,
        confidence,
        evidence,
        Diagnostics(code, "range evaluation completed"),
        cfg.configuration_version,
        c.run_id,
        c.lineage.input_hash,
    )


def _unknown(c, cfg, code, message):
    return DetectorResult(
        DETECTOR_ID,
        DETECTOR_VERSION,
        Result.UNKNOWN,
        Status.COMPLETED,
        None,
        Evidence(observation_window=None, lineage_reference=c.lineage.input_hash),
        Diagnostics(code, message),
        cfg.configuration_version,
        c.run_id,
        c.lineage.input_hash,
    )


def _invalid(c, cfg, message):
    return DetectorResult(
        DETECTOR_ID,
        DETECTOR_VERSION,
        Result.UNKNOWN,
        Status.INVALID_INPUT,
        None,
        Evidence(lineage_reference=c.lineage.input_hash),
        Diagnostics("INVALID_INPUT", message),
        cfg.configuration_version,
        c.run_id,
        c.lineage.input_hash,
    )

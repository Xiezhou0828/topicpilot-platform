"""Deterministic, fail-closed Technical V0 publication over canonical history.

The module owns the backend calculation and publication boundary.  It accepts
only the shared historical read-model observations and an optional bounded
continuity-evidence envelope.  Missing continuity evidence is UNKNOWN; it is
never inferred from an empty event result or from visually continuous prices.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any

from topicpilot_api.known_event_aware_publication import (
    EVENT_LOOKUP_UNAVAILABLE,
    KNOWN_EVENT_AWARE_PUBLICATION_POLICY,
    KNOWN_EVENT_AWARE_PUBLICATION_POLICY_VERSION,
    NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND,
    evaluate_known_event_lookup,
)

TECHNICAL_CONTRACT_VERSION = "stock-technical-publication.v3"
TECHNICAL_POLICY_VERSION = "stock-technical-v0-policy.v4"
TECHNICAL_INPUT_AUTHORITY = "V2_CANONICAL_OBSERVATION_CHAIN"
RAW_SERIES_SEMANTICS = "RAW_OBSERVED_DAILY_BAR"
PRICE_BASIS = "RAW_OBSERVED"
CONTINUITY_POLICY = "FORMAL_RAW_OBSERVED + KNOWN_EVENT_AWARE_OFFICIAL_OVERLAY"
CONTINUITY_STATES = (
    "CONTINUITY_PASS_BOUNDED",
    "CONTINUITY_FAIL",
    "CONTINUITY_UNKNOWN",
)
TECHNICAL_RESULT_STATUSES = ("VALID", "INELIGIBLE", "UNAVAILABLE", "ERROR")
EVENT_AUTHORITY_STATUSES = (
    "KNOWN_EVENT",
    "NO_KNOWN_EVENT_EVIDENCE",
    "LOOKUP_UNAVAILABLE",
    "NOT_APPLICABLE",
    "ERROR",
)
PUBLICATION_STATUSES = (
    "AVAILABLE",
    "AVAILABLE_WITH_LIMITATION",
    "BLOCKED",
    "UNAVAILABLE",
    "ERROR",
)
LIMITED_PUBLICATION_STATE = "FORMAL_WITH_LIMITATION"
DEFERRED_INDICATOR_FAMILIES = [
    "LIQUIDITY_SWEEP",
    "ORDER_FLOW",
    "ANCHORED_VWAP",
    "VOLUME_PROFILE",
    "FVG",
    "FIBONACCI",
    "SUPPLY_AND_DEMAND",
    "TRADING_PATTERNS",
]


def _unique(values: Iterable[Any]) -> list[str]:
    return sorted({str(value) for value in values if value is not None and str(value)})


def _event_authority_status(event_lookup: Mapping[str, Any]) -> str:
    state = event_lookup.get("state")
    if state == "KNOWN_VERIFIED_BREAKING_EVENT_FOUND":
        return "KNOWN_EVENT"
    if state == NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND:
        return "NO_KNOWN_EVENT_EVIDENCE"
    if state == EVENT_LOOKUP_UNAVAILABLE:
        return (
            "LOOKUP_UNAVAILABLE"
            if event_lookup.get("bounded_limitation_allowed") is True
            else "ERROR"
        )
    return "ERROR"


def _item_value(item: Mapping[str, Any], source: Mapping[str, Any], key: str) -> Any:
    return source.get(key) if source.get(key) is not None else item.get(key)


def _provenance(history: Mapping[str, Any], items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    sources = [item.get("source") or {} for item in items]
    source_codes = _unique(
        _item_value(item, source, "source_code")
        for item, source in zip(items, sources, strict=True)
    )
    adapter_versions = _unique(
        _item_value(item, source, "adapter_version")
        for item, source in zip(items, sources, strict=True)
    )
    normalization_versions = _unique(
        _item_value(item, source, "normalization_contract_version")
        for item, source in zip(items, sources, strict=True)
    )
    mapping_versions = _unique(
        _item_value(item, source, "mapping_policy_version")
        for item, source in zip(items, sources, strict=True)
    )
    reference_versions = _unique(
        _item_value(item, source, "reference_data_version")
        for item, source in zip(items, sources, strict=True)
    )
    observation_semantics = _unique(
        _item_value(item, source, "observation_semantics")
        for item, source in zip(items, sources, strict=True)
    )
    quality_states = _unique(item.get("quality_state") for item in items)
    adjustment_states = _unique((item.get("adjustment_state") or "UNKNOWN") for item in items)

    lineage_sets = (
        source_codes,
        adapter_versions,
        normalization_versions,
        mapping_versions,
        reference_versions,
        observation_semantics,
    )
    if any(not values for values in lineage_sets):
        lineage_state = "INCOMPLETE"
    elif any(len(values) > 1 for values in lineage_sets):
        lineage_state = "MIXED"
    else:
        lineage_state = "VERSIONED"

    adjustment_state = adjustment_states[0] if len(adjustment_states) == 1 else "CONFLICT"
    return {
        "authority": TECHNICAL_INPUT_AUTHORITY,
        "series_semantics": RAW_SERIES_SEMANTICS,
        "adjustment_state": (
            adjustment_state
            if adjustment_state in {"ADJUSTED", "UNADJUSTED", "UNKNOWN", "CONFLICT"}
            else "UNKNOWN"
        ),
        "quality_states": quality_states,
        "observation_semantics": observation_semantics,
        "source_codes": source_codes,
        "adapter_versions": adapter_versions,
        "normalization_contract_versions": normalization_versions,
        "mapping_policy_versions": mapping_versions,
        "reference_data_versions": reference_versions,
        "lineage_state": lineage_state,
        "observation_count": len(items),
        "returned_from": history.get("returned_from"),
        "returned_to": history.get("returned_to"),
        "latest_trading_date": history.get("latest_trading_date"),
        "latest_observed_at": history.get("latest_observed_at"),
        "latest_retrieved_at": history.get("latest_retrieved_at"),
        "instrument_identity": _identity(history),
    }


def _identity(history: Mapping[str, Any]) -> str:
    value = history.get("instrument_id") or history.get("identity_id")
    fallback = f"{history.get('market', '')}:{history.get('code', '')}"
    return str(value) if value is not None else fallback


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def _session_date(item: Mapping[str, Any]) -> date:
    value = item.get("trading_date")
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _sort_items(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    indexed = list(enumerate(items))

    def key(entry: tuple[int, Mapping[str, Any]]) -> tuple[Any, ...]:
        index, item = entry
        observed_at = item.get("observed_at")
        ordering_key = item.get("ordering_key")
        observation_id = item.get("observation_id")
        return (
            _session_date(item),
            (
                observed_at.isoformat()
                if isinstance(observed_at, datetime)
                else str(observed_at or "")
            ),
            str(ordering_key or ""),
            str(observation_id or ""),
            index,
        )

    return [dict(item) for _, item in sorted(indexed, key=key)]


def _window(items: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    if not items:
        return None
    return {
        "start_session": _session_date(items[0]),
        "end_session": _session_date(items[-1]),
        "observation_count": len(items),
    }


def _lineage(items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    history = {"items": list(items)}
    provenance = _provenance(history, items)
    return {
        "authority": provenance["authority"],
        "series_semantics": provenance["series_semantics"],
        "source_codes": provenance["source_codes"],
        "adapter_versions": provenance["adapter_versions"],
        "normalization_contract_versions": provenance["normalization_contract_versions"],
        "mapping_policy_versions": provenance["mapping_policy_versions"],
        "reference_data_versions": provenance["reference_data_versions"],
        "observation_semantics": provenance["observation_semantics"],
        "lineage_state": provenance["lineage_state"],
    }


def _valid_observations(items: Sequence[Mapping[str, Any]], *, volume: bool = False) -> bool:
    if not items:
        return False
    required = ("close", "volume") if volume else ("close",)
    return all(
        item.get("quality_state") == "ACCEPTED"
        and all(_decimal(item.get(field)) is not None for field in required)
        for item in items
    ) and _lineage(items)["lineage_state"] == "VERSIONED"


def _evidence_for(
    history: Mapping[str, Any],
    indicator_id: str,
    *,
    as_of_session: date,
    required_window: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    envelope = history.get("continuity_evidence")
    if isinstance(envelope, Mapping):
        candidate = envelope.get(indicator_id, envelope.get("default"))
        return candidate if isinstance(candidate, Mapping) else None
    if isinstance(envelope, Sequence) and not isinstance(envelope, (str, bytes)):
        for candidate in envelope:
            if not isinstance(candidate, Mapping):
                continue
            if candidate.get("indicator_id") in {None, indicator_id}:
                return candidate
    return None


def evaluate_bounded_continuity(
    history: Mapping[str, Any],
    indicator_id: str,
    *,
    as_of_session: date,
    required_window: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Evaluate an exact indicator window without treating absence as PASS."""

    evidence = _evidence_for(
        history,
        indicator_id,
        as_of_session=as_of_session,
        required_window=required_window,
    )
    base = {
        "indicator_id": indicator_id,
        "canonical_identity": _identity(history),
        "as_of_session": as_of_session,
        "required_observation_window": required_window,
        "evidence_id": evidence.get("evidence_id") if evidence else None,
        "method": evidence.get("method") if evidence else None,
        "authority": evidence.get("authority") if evidence else None,
    }
    if evidence is None:
        return {
            **base,
            "state": "CONTINUITY_UNKNOWN",
            "reason": "CONTINUITY_AUTHORITY_UNAVAILABLE",
        }

    expected_identity = evidence.get("canonical_identity", evidence.get("identity"))
    expected_window = evidence.get("required_observation_window")
    if (
        (expected_identity is not None and expected_identity != _identity(history))
        or evidence.get("as_of_session") not in {None, as_of_session, as_of_session.isoformat()}
        or evidence.get("indicator_id") not in {None, indicator_id}
        or (expected_window is not None and expected_window != required_window)
    ):
        return {
            **base,
            "state": "CONTINUITY_UNKNOWN",
            "reason": "CONTINUITY_EVIDENCE_SCOPE_MISMATCH",
        }
    if evidence.get("material_conflict") or evidence.get("state") == "CONTINUITY_UNKNOWN":
        return {**base, "state": "CONTINUITY_UNKNOWN", "reason": "CONTINUITY_EVIDENCE_CONFLICT"}

    events = evidence.get("known_events")
    if events is None or not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
        return {**base, "state": "CONTINUITY_UNKNOWN", "reason": "CONTINUITY_EVENT_SCOPE_UNKNOWN"}
    start = required_window.get("start_session") if required_window else None
    end = required_window.get("end_session") if required_window else None
    if isinstance(start, str):
        start = date.fromisoformat(start)
    if isinstance(end, str):
        end = date.fromisoformat(end)
    for event in events:
        if not isinstance(event, Mapping):
            return {
                **base,
                "state": "CONTINUITY_UNKNOWN",
                "reason": "CONTINUITY_EVENT_RECORD_INVALID",
            }
        event_date = event.get("primary_effective_date", event.get("effective_date"))
        if isinstance(event_date, str):
            event_date = date.fromisoformat(event_date)
        if (
            isinstance(event_date, date)
            and start
            and end
            and start <= event_date <= end
            and not event.get("continuity_resolved", False)
        ):
            return {
                **base,
                "state": "CONTINUITY_FAIL",
                "reason": "CONTINUITY_BREAKING_EVENT_UNRESOLVED",
                "event_type": event.get("event_type"),
                "event_effective_date": event_date,
            }

    coverage_state = evidence.get("coverage_state")
    coverage_complete = bool(evidence.get("coverage_complete", False))
    if coverage_complete and coverage_state in {"COVERED_NO_EVENT", "COVERED_EVENT"}:
        return {**base, "state": "CONTINUITY_PASS_BOUNDED", "reason": "BOUNDED_EVENT_SCOPE_PASSED"}
    return {**base, "state": "CONTINUITY_UNKNOWN", "reason": "CONTINUITY_AUTHORITY_INCOMPLETE"}


def _bounded_limitation_allowed(
    continuity: Mapping[str, Any], event_lookup: Mapping[str, Any]
) -> bool:
    return bool(
        event_lookup.get("bounded_limitation_allowed") is True
        and continuity.get("reason")
        in {
            "CONTINUITY_AUTHORITY_UNAVAILABLE",
            "BOUNDED_EVENT_SCOPE_PASSED",
        }
    )


def _sma(values: Sequence[Decimal | None], period: int) -> list[Decimal | None]:
    output: list[Decimal | None] = [None] * len(values)
    for index in range(period - 1, len(values)):
        window = values[index - period + 1 : index + 1]
        if all(value is not None for value in window):
            with localcontext() as context:
                context.prec = 50
                output[index] = sum(window, Decimal(0)) / Decimal(period)
    return output


def _raw_returns(values: Sequence[Decimal | None], period: int) -> list[Decimal | None]:
    output: list[Decimal | None] = [None] * len(values)
    for index in range(period, len(values)):
        current = values[index]
        anchor = values[index - period]
        if current is not None and anchor not in (None, Decimal(0)):
            with localcontext() as context:
                context.prec = 50
                output[index] = current / anchor - Decimal(1)
    return output


def _rsi_wilder(values: Sequence[Decimal | None], period: int = 14) -> list[Decimal | None]:
    output: list[Decimal | None] = [None] * len(values)
    if len(values) <= period or any(value is None for value in values):
        return output
    gains = [max(values[index] - values[index - 1], Decimal(0)) for index in range(1, len(values))]
    losses = [max(values[index - 1] - values[index], Decimal(0)) for index in range(1, len(values))]
    with localcontext() as context:
        context.prec = 50
        average_gain = sum(gains[:period], Decimal(0)) / Decimal(period)
        average_loss = sum(losses[:period], Decimal(0)) / Decimal(period)

        def value() -> Decimal:
            if average_loss == 0 and average_gain > 0:
                return Decimal(100)
            if average_gain == 0 and average_loss > 0:
                return Decimal(0)
            if average_gain == 0 and average_loss == 0:
                return Decimal(50)
            return Decimal(100) - (Decimal(100) / (Decimal(1) + average_gain / average_loss))

        output[period] = value()
        for index in range(period + 1, len(values)):
            average_gain = (average_gain * Decimal(period - 1) + gains[index - 1]) / Decimal(period)
            average_loss = (
                average_loss * Decimal(period - 1) + losses[index - 1]
            ) / Decimal(period)
            output[index] = value()
    return output


def _ema_seeded(values: Sequence[Decimal | None], period: int) -> list[Decimal | None]:
    output: list[Decimal | None] = [None] * len(values)
    if len(values) < period or any(value is None for value in values):
        return output
    with localcontext() as context:
        context.prec = 50
        alpha = Decimal(2) / Decimal(period + 1)
        output[period - 1] = sum(values[:period], Decimal(0)) / Decimal(period)
        for index in range(period, len(values)):
            output[index] = alpha * values[index] + (Decimal(1) - alpha) * output[index - 1]
    return output


def _macd(values: Sequence[Decimal | None]) -> dict[str, list[Decimal | None]]:
    fast = _ema_seeded(values, 12)
    slow = _ema_seeded(values, 26)
    line: list[Decimal | None] = [None] * len(values)
    for index in range(len(values)):
        if fast[index] is not None and slow[index] is not None:
            line[index] = fast[index] - slow[index]

    signal: list[Decimal | None] = [None] * len(values)
    valid_line_indexes = [index for index, value in enumerate(line) if value is not None]
    if len(valid_line_indexes) >= 9:
        with localcontext() as context:
            context.prec = 50
            first_signal_index = valid_line_indexes[8]
            signal[first_signal_index] = sum(
                (line[index] for index in valid_line_indexes[:9]), Decimal(0)
            ) / Decimal(9)
            alpha = Decimal(2) / Decimal(10)
            for index in valid_line_indexes[9:]:
                signal[index] = alpha * line[index] + (Decimal(1) - alpha) * signal[index - 1]
    histogram = [
        line[index] - signal[index]
        if line[index] is not None and signal[index] is not None
        else None
        for index in range(len(values))
    ]
    return {
        "MACD_12_26_9": line,
        "MACD_SIGNAL_12_26_9": signal,
        "MACD_HISTOGRAM_12_26_9": histogram,
    }


def _technical_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for period in (5, 10, 20, 60):
        specs.append(
            {
                "indicator_id": f"MA{period}",
                "family": "MA",
                "algorithm_id": "SMA_CLOSE_V1",
                "parameters": {"period": period, "input": "accepted_raw_close"},
                "minimum": period,
                "mode": "rolling_close",
                "price_basis": PRICE_BASIS,
            }
        )
    specs.append(
        {
            "indicator_id": "DISTANCE_TO_MA20",
            "family": "DISTANCE_TO_MA20",
            "algorithm_id": "DISTANCE_TO_MA20_V1",
            "parameters": {"ma_period": 20, "formula": "(close_t - MA20_t) / MA20_t"},
            "minimum": 20,
            "mode": "rolling_close",
            "price_basis": PRICE_BASIS,
        }
    )
    for period in (5, 20):
        specs.append(
            {
                "indicator_id": f"RAW_CLOSE_RETURN_{period}D",
                "family": "RAW_CLOSE_RETURN",
                "algorithm_id": "RAW_OBSERVED_CLOSE_RETURN_V1",
                "parameters": {"period": period, "formula": "close_t / close_(t-N) - 1"},
                "minimum": period + 1,
                "mode": "rolling_close",
                "price_basis": PRICE_BASIS,
            }
        )
    for period in (5, 20):
        specs.append(
            {
                "indicator_id": f"VOLUME_MA{period}",
                "family": "VOLUME_MA",
                "algorithm_id": "SMA_VOLUME_QUANTITY_V1",
                "parameters": {"period": period, "input": "canonical_volume_quantity"},
                "minimum": period,
                "mode": "rolling_volume",
                "price_basis": "NOT_PRICE_BASED",
            }
        )
    specs.append(
        {
            "indicator_id": "VOLUME_RATIO_20",
            "family": "VOLUME_RATIO",
            "algorithm_id": "VOLUME_RATIO_20_V1",
            "parameters": {"period": 20, "formula": "current_volume / VOLUME_MA20"},
            "minimum": 20,
            "mode": "rolling_volume",
            "price_basis": "NOT_PRICE_BASED",
        }
    )
    specs.append(
        {
            "indicator_id": "RSI14",
            "family": "RSI",
            "algorithm_id": "RSI_WILDER_14_V1",
            "parameters": {"period": 14, "seed": "arithmetic_mean_of_first_14_changes"},
            "minimum": 15,
            "mode": "recursive_close",
            "price_basis": PRICE_BASIS,
        }
    )
    for indicator_id in ("MACD_12_26_9", "MACD_SIGNAL_12_26_9", "MACD_HISTOGRAM_12_26_9"):
        minimum = 26 if indicator_id == "MACD_12_26_9" else 34
        specs.append(
            {
                "indicator_id": indicator_id,
                "family": "MACD",
                "algorithm_id": "MACD_12_26_9_SMA_SEEDED_EMA_V1",
                "parameters": {
                    "fast": 12,
                    "slow": 26,
                    "signal": 9,
                    "alpha": "2/(N+1)",
                    "ema_seed": "SMA",
                    "signal_seed": "first_9_valid_macd_values",
                },
                "minimum": minimum,
                "mode": "recursive_close",
                "price_basis": PRICE_BASIS,
            }
        )
    return specs


TECHNICAL_SPECS = _technical_specs()


def _required_items(
    items: Sequence[Mapping[str, Any]], index: int, spec: Mapping[str, Any]
) -> list[dict[str, Any]]:
    if spec["mode"] in {"recursive_close"}:
        return [dict(item) for item in items[: index + 1]]
    period = int(spec["minimum"])
    return [dict(item) for item in items[max(0, index - period + 1) : index + 1]]


def _algorithm_version(spec: Mapping[str, Any]) -> str:
    return str(spec["algorithm_id"])


def _value_reason(
    *,
    spec: Mapping[str, Any],
    index: int,
    required_items: Sequence[Mapping[str, Any]],
    value: Decimal | None,
    continuity: Mapping[str, Any],
    event_lookup: Mapping[str, Any],
) -> str | None:
    if len(required_items) < int(spec["minimum"]):
        return "UNAVAILABLE_INSUFFICIENT_HISTORY"
    if not _valid_observations(required_items, volume=spec["mode"] == "rolling_volume"):
        return "UNAVAILABLE_INVALID_OBSERVATION"
    if continuity["state"] == "CONTINUITY_FAIL":
        return "CONTINUITY_FAIL"
    if continuity["state"] == "CONTINUITY_UNKNOWN":
        if (
            event_lookup["state"] == EVENT_LOOKUP_UNAVAILABLE
            and not _bounded_limitation_allowed(continuity, event_lookup)
        ):
            return str(event_lookup["reason"])
        if (
            not event_lookup["publication_allowed"]
            and not _bounded_limitation_allowed(continuity, event_lookup)
        ):
            return str(event_lookup["reason"])
    if continuity["state"] == "CONTINUITY_PASS_BOUNDED":
        if (
            event_lookup["state"] == EVENT_LOOKUP_UNAVAILABLE
            and not _bounded_limitation_allowed(continuity, event_lookup)
        ):
            return str(event_lookup["reason"])
        if (
            not event_lookup["publication_allowed"]
            and not _bounded_limitation_allowed(continuity, event_lookup)
        ):
            return str(event_lookup["reason"])
    if value is None:
        if spec["indicator_id"] in {"DISTANCE_TO_MA20", "VOLUME_RATIO_20"}:
            return "UNAVAILABLE_ZERO_DENOMINATOR"
        return "UNAVAILABLE_ALGORITHM_INPUT"
    return None


def _calculate_series(items: Sequence[Mapping[str, Any]]) -> dict[str, list[Decimal | None]]:
    closes = [_decimal(item.get("close")) for item in items]
    volumes = [_decimal(item.get("volume")) for item in items]
    series: dict[str, list[Decimal | None]] = {}
    for period in (5, 10, 20, 60):
        series[f"MA{period}"] = _sma(closes, period)
    series["DISTANCE_TO_MA20"] = [
        (closes[index] - series["MA20"][index]) / series["MA20"][index]
        if closes[index] is not None
        and series["MA20"][index] not in (None, Decimal(0))
        else None
        for index in range(len(items))
    ]
    series["RAW_CLOSE_RETURN_5D"] = _raw_returns(closes, 5)
    series["RAW_CLOSE_RETURN_20D"] = _raw_returns(closes, 20)
    series["VOLUME_MA5"] = _sma(volumes, 5)
    series["VOLUME_MA20"] = _sma(volumes, 20)
    series["VOLUME_RATIO_20"] = [
        volumes[index] / series["VOLUME_MA20"][index]
        if volumes[index] is not None and series["VOLUME_MA20"][index] not in (None, Decimal(0))
        else None
        for index in range(len(items))
    ]
    series["RSI14"] = _rsi_wilder(closes)
    series.update(_macd(closes))
    return series


def _technical_evidence(
    history: Mapping[str, Any],
    items: Sequence[Mapping[str, Any]],
    index: int,
    spec: Mapping[str, Any],
    series: Mapping[str, Sequence[Decimal | None]],
) -> dict[str, Any]:
    indicator_id = str(spec["indicator_id"])
    required_items = _required_items(items, index, spec)
    required_window = _window(required_items)
    as_of_item = items[index]
    as_of_session = _session_date(as_of_item)
    actual_window = _window(required_items)
    raw_continuity_evidence = _evidence_for(
        history,
        indicator_id,
        as_of_session=as_of_session,
        required_window=required_window,
    )
    continuity = evaluate_bounded_continuity(
        history,
        indicator_id,
        as_of_session=as_of_session,
        required_window=required_window,
    )
    event_lookup = evaluate_known_event_lookup(
        history,
        continuity_evidence=raw_continuity_evidence,
        required_window=required_window,
    )
    if (
        event_lookup["state"] == EVENT_LOOKUP_UNAVAILABLE
        and raw_continuity_evidence is not None
        and "known_event_lookup" not in history
        and continuity["state"] == "CONTINUITY_UNKNOWN"
    ):
        event_lookup = {**event_lookup, "reason": "CONTINUITY_UNKNOWN"}
    value = series[indicator_id][index]
    reason = _value_reason(
        spec=spec,
        index=index,
        required_items=required_items,
        value=value,
        continuity=continuity,
        event_lookup=event_lookup,
    )
    if reason is not None:
        value = None
    source_lineage = _lineage(required_items)
    limited_publication = (
        reason is None and _bounded_limitation_allowed(continuity, event_lookup)
    )
    publication_state = (
        LIMITED_PUBLICATION_STATE
        if limited_publication
        else "FORMAL"
        if reason is None
        else "UNAVAILABLE"
    )
    return {
        "instrument_identity": _identity(history),
        "symbol": history.get("code"),
        "market": history.get("market"),
        "indicator_id": indicator_id,
        "indicator_family": spec["family"],
        "indicator_version": TECHNICAL_POLICY_VERSION,
        "value": value,
        "session_date": as_of_session,
        "as_of": (
            as_of_item.get("retrieved_at")
            or as_of_item.get("observed_at")
            or history.get("as_of")
        ),
        "required_observation_count": int(spec["minimum"]),
        "actual_observation_count": len(required_items),
        "required_observation_window": required_window,
        "actual_observation_window": actual_window,
        "algorithm_id": spec["algorithm_id"],
        "algorithm_version": _algorithm_version(spec),
        "parameter_set": spec["parameters"],
        "price_basis": spec["price_basis"],
        "continuity_state": continuity["state"],
        "continuity_evidence": continuity,
        "event_authority_status": _event_authority_status(event_lookup),
        "event_lookup_state": event_lookup["state"],
        "event_lookup_evidence": event_lookup,
        "known_event_handling": event_lookup["known_events"],
        "source_authority": TECHNICAL_INPUT_AUTHORITY,
        "source_lineage": source_lineage,
        "publication_state": publication_state,
        "availability_reason": reason,
        "limitation_reasons": ["EVENT_LOOKUP_UNAVAILABLE"] if limited_publication else [],
    }


def _latest_evidence(
    evidence: Sequence[Mapping[str, Any]], indicator_id: str
) -> Mapping[str, Any] | None:
    candidates = [item for item in evidence if item.get("indicator_id") == indicator_id]
    return candidates[-1] if candidates else None


def _latest_event_authority_status(evidence: Sequence[Mapping[str, Any]]) -> str:
    if not evidence:
        return "NOT_APPLICABLE"
    latest_session = max(item.get("session_date") for item in evidence)
    latest = [item for item in evidence if item.get("session_date") == latest_session]
    statuses = {str(item.get("event_authority_status")) for item in latest}
    if "KNOWN_EVENT" in statuses:
        return "KNOWN_EVENT"
    if "ERROR" in statuses:
        return "ERROR"
    if "LOOKUP_UNAVAILABLE" in statuses:
        return "LOOKUP_UNAVAILABLE"
    if "NO_KNOWN_EVENT_EVIDENCE" in statuses:
        return "NO_KNOWN_EVENT_EVIDENCE"
    return "NOT_APPLICABLE"


def _technical_surface_status(
    history: Mapping[str, Any],
    items: Sequence[Mapping[str, Any]],
    evidence: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if not items:
        return {
            "technical_result_status": "UNAVAILABLE",
            "technical_eligibility": "UNAVAILABLE",
            "event_authority_status": "NOT_APPLICABLE",
            "publication_status": "UNAVAILABLE",
            "reason_codes": ["DATA_GAP"],
            "limitation_reasons": [],
        }
    if not history.get("code") or str(history.get("market", "")).upper() not in {"TPE", "TWO"}:
        return {
            "technical_result_status": "ERROR",
            "technical_eligibility": "ERROR",
            "event_authority_status": "ERROR",
            "publication_status": "ERROR",
            "reason_codes": ["IDENTITY_FAILURE"],
            "limitation_reasons": [],
        }

    event_authority_status = _latest_event_authority_status(evidence)
    ma60 = _latest_evidence(evidence, "MA60")
    ma60_value = _decimal(ma60.get("value")) if ma60 else None
    latest_close = _decimal(items[-1].get("close"))
    latest_evidence = [
        item for item in evidence if item.get("session_date") == _session_date(items[-1])
    ]
    limitation_reasons = _unique(
        reason
        for item in latest_evidence
        for reason in item.get("limitation_reasons", [])
    )
    known_event_on_surface = any(
        item.get("event_authority_status") == "KNOWN_EVENT" for item in latest_evidence
    )

    if ma60_value is None or not ma60 or ma60.get("publication_state") not in {
        "FORMAL",
        LIMITED_PUBLICATION_STATE,
    }:
        ma60_reason = str((ma60 or {}).get("availability_reason") or "UNAVAILABLE_MA60")
        known_event_block = (
            ma60_reason in {
                "CONTINUITY_FAIL",
                "KNOWN_VERIFIED_EVENT_REQUIRES_EVENT_AWARE_HANDLING",
            }
            or (ma60 or {}).get("event_authority_status") == "KNOWN_EVENT"
        )
        if known_event_block:
            reason_codes = ["KNOWN_CONTINUITY_EVENT", ma60_reason]
            publication_status = "BLOCKED"
        elif event_authority_status == "ERROR":
            reason_codes = ["TECHNICAL_CALCULATION_ERROR", ma60_reason]
            publication_status = "ERROR"
        else:
            reason_codes = ["UNAVAILABLE", ma60_reason]
            publication_status = "UNAVAILABLE"
        return {
            "technical_result_status": "UNAVAILABLE",
            "technical_eligibility": "UNAVAILABLE",
            "event_authority_status": event_authority_status,
            "publication_status": publication_status,
            "reason_codes": _unique(reason_codes),
            "limitation_reasons": limitation_reasons,
        }

    if latest_close is None:
        return {
            "technical_result_status": "UNAVAILABLE",
            "technical_eligibility": "UNAVAILABLE",
            "event_authority_status": event_authority_status,
            "publication_status": "UNAVAILABLE",
            "reason_codes": ["INVALID_NUMERIC"],
            "limitation_reasons": limitation_reasons,
        }

    if latest_close < ma60_value:
        return {
            "technical_result_status": "INELIGIBLE",
            "technical_eligibility": "INELIGIBLE",
            "event_authority_status": event_authority_status,
            "publication_status": "BLOCKED",
            "reason_codes": ["BELOW_MA60", "TECHNICAL_V0_INELIGIBLE"],
            "limitation_reasons": limitation_reasons,
        }

    if known_event_on_surface:
        limitation_reasons = _unique([*limitation_reasons, "KNOWN_EVENT_HANDLED"])
    if event_authority_status == "LOOKUP_UNAVAILABLE":
        limitation_reasons = _unique([*limitation_reasons, "EVENT_LOOKUP_UNAVAILABLE"])
    limited = bool(limitation_reasons)
    return {
        "technical_result_status": "VALID",
        "technical_eligibility": "ELIGIBLE",
        "event_authority_status": event_authority_status,
        "publication_status": (
            "AVAILABLE_WITH_LIMITATION" if limited else "AVAILABLE"
        ),
        "reason_codes": limitation_reasons,
        "limitation_reasons": limitation_reasons,
    }


def build_technical_publication(history: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic Technical V0 evidence over canonical history."""

    raw_items = [item for item in (history.get("items") or []) if isinstance(item, Mapping)]
    items = _sort_items(raw_items)
    common = {
        "code": history.get("code"),
        "market": history.get("market"),
        "technical_contract_version": TECHNICAL_CONTRACT_VERSION,
        "technical_policy_version": TECHNICAL_POLICY_VERSION,
        "requested_from": history.get("requested_from"),
        "requested_to": history.get("requested_to"),
        "as_of": history.get("as_of") or history.get("latest_retrieved_at"),
        "calculation_owner": "BACKEND_ONLY",
        "browser_calculation_allowed": "NO",
        "price_basis": PRICE_BASIS,
        "continuity_policy": CONTINUITY_POLICY,
        "publication_policy": KNOWN_EVENT_AWARE_PUBLICATION_POLICY,
        "publication_policy_version": KNOWN_EVENT_AWARE_PUBLICATION_POLICY_VERSION,
        "deferred_indicator_families": DEFERRED_INDICATOR_FAMILIES,
        "published_indicators": [],
        "technical_evidence": [],
        "algorithm_id": None,
        "algorithm_version": None,
        "parameter_set_id": None,
        "adjustment_policy_id": None,
        "technical_result_status": "UNAVAILABLE",
        "technical_eligibility": "UNAVAILABLE",
        "event_authority_status": "NOT_APPLICABLE",
        "publication_status": "UNAVAILABLE",
        "reason_codes": [],
        "limitation_reasons": [],
    }
    if not items:
        return {
            **common,
            "status": "UNAVAILABLE",
            "publication_state": "NOT_PUBLISHED",
            "input_state": "UNAVAILABLE",
            "availability_reasons": ["NO_ACCEPTED_CANONICAL_PRICE_OBSERVATIONS"],
            "reason_codes": ["DATA_GAP", "NO_ACCEPTED_CANONICAL_PRICE_OBSERVATIONS"],
            "provenance": None,
        }

    series = _calculate_series(items)
    evidence = [
        _technical_evidence(history, items, index, spec, series)
        for index in range(len(items))
        for spec in TECHNICAL_SPECS
    ]
    formal_id_set = {
        item["indicator_id"]
        for item in evidence
        if item["publication_state"] in {"FORMAL", LIMITED_PUBLICATION_STATE}
    }
    formal_ids = [
        spec["indicator_id"] for spec in TECHNICAL_SPECS if spec["indicator_id"] in formal_id_set
    ]
    reasons = _unique(
        item["availability_reason"]
        for item in evidence
        if item["availability_reason"] is not None
    )
    provenance = _provenance(history, items)
    event_lookup_states = _unique(item["event_lookup_state"] for item in evidence)
    known_event_handling = [
        event
        for item in evidence
        for event in item["known_event_handling"]
    ]
    if (
        not history.get("continuity_evidence")
        and NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND not in event_lookup_states
    ):
        reasons.append("CONTINUITY_AUTHORITY_UNAVAILABLE")
    if provenance["adjustment_state"] == "UNKNOWN":
        reasons.append("ADJUSTMENT_AUTHORITY_UNKNOWN")
    if provenance["lineage_state"] != "VERSIONED":
        reasons.append(f"SOURCE_LINEAGE_{provenance['lineage_state']}")
    reasons = _unique(reasons)
    surface = _technical_surface_status(history, items, evidence)
    has_formal = bool(formal_ids)
    publication_state = {
        "AVAILABLE": "FORMAL",
        "AVAILABLE_WITH_LIMITATION": LIMITED_PUBLICATION_STATE,
    }.get(surface["publication_status"], "UNAVAILABLE")
    return {
        **common,
        "status": "FORMAL" if has_formal else "UNAVAILABLE",
        "publication_state": publication_state,
        "input_state": "RAW_OBSERVED",
        "availability_reasons": _unique([*reasons, *surface["reason_codes"]]),
        "published_indicators": formal_ids,
        "technical_evidence": evidence,
        "event_lookup_states": event_lookup_states,
        "known_event_handling": known_event_handling,
        **surface,
        "provenance": provenance,
    }


__all__ = [
    "CONTINUITY_POLICY",
    "CONTINUITY_STATES",
    "DEFERRED_INDICATOR_FAMILIES",
    "EVENT_AUTHORITY_STATUSES",
    "LIMITED_PUBLICATION_STATE",
    "PRICE_BASIS",
    "PUBLICATION_STATUSES",
    "RAW_SERIES_SEMANTICS",
    "TECHNICAL_CONTRACT_VERSION",
    "TECHNICAL_INPUT_AUTHORITY",
    "TECHNICAL_POLICY_VERSION",
    "TECHNICAL_RESULT_STATUSES",
    "TECHNICAL_SPECS",
    "build_technical_publication",
    "evaluate_bounded_continuity",
]

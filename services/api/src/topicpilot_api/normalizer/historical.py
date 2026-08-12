"""Pure mapper for provider-neutral historical daily bars."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .contracts import (
    NormalizationCandidate,
    NormalizationFailure,
    NormalizationResult,
    decimal,
    ensure_utc,
    json_pointer,
)

HISTORICAL_MAPPING_POLICY_VERSION = "historical-daily-mapping-v1"


def _number(payload: dict[str, Any], key: str) -> Decimal | None:
    value = payload.get(key)
    return None if value is None else decimal(value)


class HistoricalDailyBarNormalizer:
    """Map a normalized daily OHLCV payload into canonical families.

    A partially populated bar is persisted as ``INCOMPLETE`` evidence.  It is
    never upgraded to an accepted value by filling a missing field with zero.
    """

    def __call__(self, envelope, reference, policy) -> NormalizationResult:
        try:
            observed = ensure_utc(envelope.observed_at)
            payload = envelope.payload
            values = {
                "open": _number(payload, "open"),
                "high": _number(payload, "high"),
                "low": _number(payload, "low"),
                "close": _number(payload, "close"),
            }
            volume = _number(payload, "volume")
        except (TypeError, ValueError, ArithmeticError) as exc:
            return NormalizationResult(
                (), (NormalizationFailure("REJECTED", "INVALID_HISTORICAL_BAR", str(exc)),)
            )

        if not envelope.instrument_id or not envelope.source_id:
            return NormalizationResult((), (NormalizationFailure("REJECTED", "INVALID_LINEAGE"),))

        failures: list[NormalizationFailure] = []
        numbers = tuple(values.values())
        if all(value is not None for value in numbers):
            assert all(value is not None for value in numbers)
            if values["low"] > min(numbers) or values["high"] < max(numbers) or values["low"] < 0:
                failures.append(
                    NormalizationFailure(
                        "REJECTED",
                        "INVALID_OHLC",
                        evidence={"observed_at": observed.isoformat()},
                    )
                )
        if volume is not None and volume < 0:
            failures.append(
                NormalizationFailure(
                    "REJECTED",
                    "INVALID_VOLUME",
                    evidence={"observed_at": observed.isoformat()},
                )
            )
        if failures:
            return NormalizationResult((), tuple(failures))

        price_paths = tuple(json_pointer(key) for key in ("open", "high", "low", "close"))
        price_quality = "ACCEPTED" if all(value is not None for value in numbers) else "INCOMPLETE"
        warnings = () if price_quality == "ACCEPTED" else ("MISSING_OHLC_FIELD",)
        price_values = {
            **values,
            "last": values["close"],
            "vwap": None,
            "price_currency_code": reference.currency_code,
            "price_scale": reference.currency_scale,
            "adjustment_state": str(payload.get("adjustment_state") or "UNKNOWN"),
            "price_context": {
                "source_semantics": "DAILY_BAR",
                "timestamp_policy": "MARKET_DATE_ANCHOR",
            },
        }
        candidates = [
            NormalizationCandidate(
                "PRICE",
                price_values,
                price_paths,
                price_quality,
                warnings,
                {
                    "source_paths": list(price_paths),
                    "observed_at": observed.isoformat(),
                    "missing_fields": [key for key, value in values.items() if value is None],
                },
            )
        ]
        if volume is not None:
            candidates.append(
                NormalizationCandidate(
                    "VOLUME",
                    {
                        "volume_quantity": volume,
                        "volume_unit_code": "UNIT",
                        "volume_scale": 0,
                        "aggregation_code": "DAILY_TOTAL",
                        "volume_context": {"source_semantics": "DAILY_BAR"},
                    },
                    (json_pointer("volume"),),
                    "ACCEPTED",
                    (),
                    {"source_paths": [json_pointer("volume")], "observed_at": observed.isoformat()},
                )
            )
        return NormalizationResult(tuple(candidates))

"""Live-only mapper for already collected intraday observations."""

from __future__ import annotations

from topicpilot_api.normalizer.contracts import (
    NormalizationCandidate,
    NormalizationFailure,
    NormalizationResult,
    decimal,
    ensure_utc,
    json_pointer,
)


class LiveIntradayNormalizer:
    """Map a live payload without changing the historical mapper."""

    def __call__(self, envelope, reference, policy):
        try:
            observed = ensure_utc(envelope.observed_at)
        except ValueError as exc:
            return NormalizationResult(
                (), (NormalizationFailure("REJECTED", "INVALID_OBSERVED_TIME", str(exc)),)
            )

        payload = envelope.payload
        candidates = []
        failures = []

        def value(key: str):
            raw = payload.get(key)
            return decimal(raw) if raw is not None else None

        close = value("close")
        last = value("last")
        price = last if last is not None else close
        price_state = "ACCEPTED" if price is not None else "INCOMPLETE"
        price_paths = tuple(
            json_pointer(key) for key in ("open", "high", "low", "close", "last") if key in payload
        )
        candidates.append(
            NormalizationCandidate(
                "PRICE",
                {
                    "open": value("open"),
                    "high": value("high"),
                    "low": value("low"),
                    "close": close,
                    "last": last,
                    "price_currency_code": reference.currency_code,
                    "price_scale": reference.currency_scale,
                    "adjustment_state": "UNKNOWN",
                    "price_context": {
                        "source_semantics": "INTRADAY_BAR",
                        "timeframe": payload.get("interval", "intraday"),
                    },
                },
                price_paths,
                price_state,
                ("MISSING_LAST",) if price is None else (),
                {"observed_at": observed.isoformat(), "timeframe": payload.get("interval")},
            )
        )

        if "volume" in payload:
            volume = value("volume")
            candidates.append(
                NormalizationCandidate(
                    "VOLUME",
                    {
                        "volume_quantity": volume,
                        "volume_unit_code": "UNIT",
                        "volume_scale": 0,
                        "aggregation_code": "OBSERVED",
                        "volume_context": {"timeframe": payload.get("interval", "intraday")},
                    },
                    (json_pointer("volume"),),
                    "ACCEPTED" if volume is not None else "INCOMPLETE",
                    ("MISSING_VOLUME",) if volume is None else (),
                    {"observed_at": observed.isoformat()},
                )
            )

        quote = payload.get("quote")
        if isinstance(quote, dict) and any(key in quote for key in ("bid", "ask")):
            vals = {
                "quote_currency_code": reference.currency_code,
                "price_scale": reference.currency_scale,
                "adjustment_state": "UNKNOWN",
                "bid_price": decimal(quote["bid"]) if quote.get("bid") is not None else None,
                "ask_price": decimal(quote["ask"]) if quote.get("ask") is not None else None,
                "bid_size": decimal(quote["bid_size"])
                if quote.get("bid_size") is not None
                else None,
                "ask_size": decimal(quote["ask_size"])
                if quote.get("ask_size") is not None
                else None,
            }
            if vals["bid_size"] is not None or vals["ask_size"] is not None:
                vals.update(size_unit_code="UNIT", size_scale=0)
            candidates.append(
                NormalizationCandidate(
                    "QUOTE",
                    vals,
                    tuple(json_pointer("quote", key) for key in quote),
                    "ACCEPTED",
                    (),
                    {"observed_at": observed.isoformat()},
                )
            )

        return NormalizationResult(tuple(candidates), tuple(failures))


__all__ = ["LiveIntradayNormalizer"]

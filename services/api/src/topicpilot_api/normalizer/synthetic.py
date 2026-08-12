from .contracts import (
    NormalizationCandidate,
    NormalizationFailure,
    NormalizationResult,
    decimal,
    ensure_utc,
    json_pointer,
)


class SyntheticReferenceNormalizer:
    """Pure synthetic mapper; all registry resolution is supplied by caller."""

    def __call__(self, e, r, p):
        failures = []
        out = []
        try:
            observed = ensure_utc(e.observed_at)
        except ValueError as ex:
            return NormalizationResult(
                (), (NormalizationFailure("REJECTED", "INVALID_OBSERVED_TIME", str(ex)),)
            )
        if not e.instrument_id or not e.source_id:
            return NormalizationResult((), (NormalizationFailure("REJECTED", "INVALID_LINEAGE"),))
        payload = e.payload

        def candidate(family, values, paths, state="ACCEPTED", warnings=()):
            out.append(
                NormalizationCandidate(
                    family,
                    values,
                    tuple(paths),
                    state,
                    tuple(warnings),
                    {"source_paths": list(paths), "observed_at": observed.isoformat()},
                )
            )

        if "last" in payload or "price" in payload:
            value = payload.get("last", payload.get("price"))
            candidate(
                "PRICE",
                {
                    "last": decimal(value),
                    "price_currency_code": r.currency_code,
                    "price_scale": r.currency_scale,
                    "adjustment_state": "UNKNOWN",
                },
                [json_pointer("last" if "last" in payload else "price")],
            )
        if "volume" in payload or "quantity" in payload:
            key = "volume" if "volume" in payload else "quantity"
            candidate(
                "VOLUME",
                {
                    "volume_quantity": decimal(payload[key]),
                    "volume_unit_code": "UNIT",
                    "volume_scale": 0,
                    "aggregation_code": "OBSERVED",
                },
                [json_pointer(key)],
            )
        quote_payload = payload.get("quote", payload)
        if "bid" in quote_payload or "ask" in quote_payload:
            paths = []
            vals = {
                "quote_currency_code": r.currency_code,
                "price_scale": r.currency_scale,
                "adjustment_state": "UNKNOWN",
            }
            for key, dest in (
                ("bid", "bid_price"),
                ("ask", "ask_price"),
                ("bid_size", "bid_size"),
                ("ask_size", "ask_size"),
            ):
                if key in quote_payload:
                    vals[dest] = decimal(quote_payload[key])
                    paths.append(
                        json_pointer("quote", key) if "quote" in payload else json_pointer(key)
                    )
            if any(k in quote_payload for k in ("bid_size", "ask_size")):
                vals.update(size_unit_code="UNIT", size_scale=0)
            candidate("QUOTE", vals, paths)
        if "trading_status" in payload:
            status = payload["trading_status"]
            if r.statuses and status not in r.statuses:
                failures.append(
                    NormalizationFailure(
                        "REJECTED", "UNKNOWN_TRADING_STATUS", evidence={"value": status}
                    )
                )
            else:
                candidate(
                    "TRADING_STATUS",
                    {
                        "status_code": status,
                        "session_code": r.session_code,
                        "calendar_code": r.calendar_code,
                        "status_catalogue_version": r.status_catalogue_version,
                    },
                    ["/trading_status"],
                )
        return NormalizationResult(tuple(out), tuple(failures))

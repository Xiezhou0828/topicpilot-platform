"""Read-only provider lineage exposed to deployment operators."""

from __future__ import annotations

import os
from datetime import date
from typing import Any

from topicpilot_api import __version__

from .exchange import TPEX_DAILY_ADAPTER_VERSION, TWSE_DAILY_ADAPTER_VERSION
from .registry import build_historical_provider_registry
from .taishin import TAISHIN_INTRADAY_ADAPTER_VERSION, TAISHIN_INTRADAY_SOURCE_CODE
from .yahoo_quote import YAHOO_QUOTE_ADAPTER_VERSION, YAHOO_QUOTE_SOURCE_CODE

EXPECTED_TWSE_ADAPTER_VERSION = TWSE_DAILY_ADAPTER_VERSION
EXPECTED_TPEX_ADAPTER_VERSION = TPEX_DAILY_ADAPTER_VERSION


def build_provider_lineage() -> dict[str, Any]:
    """Build a deterministic, secret-free runtime provenance payload.

    Constructing the historical registry is local-only; it does not call an
    exchange.  ``market_batch=True`` mirrors the formal single-date
    post-close wiring and therefore verifies the code path shipped in an
    image, rather than only checking constants.
    """

    registry = build_historical_provider_registry(
        start_date=date.today(), end_date=date.today(), market_batch=True
    )
    providers: list[dict[str, Any]] = []
    for registration in registry.all():
        adapter = registration.adapter
        providers.append(
            {
                "sourceCode": registration.code,
                "adapterVersion": adapter.adapter_version,
                "markets": sorted(registration.supported_markets),
                "role": (
                    "VERIFICATION_ONLY" if registration.verification_only else "CANONICAL_DAILY"
                ),
                "marketBatch": bool(getattr(adapter, "market_batch", False)),
                "historicalFallback": (
                    "instrument/month"
                    if registration.code in {"TWSE_OFFICIAL_DAILY", "TPEX_OFFICIAL_DAILY"}
                    else None
                ),
            }
        )
    providers.extend(
        [
            {
                "sourceCode": YAHOO_QUOTE_SOURCE_CODE,
                "adapterVersion": YAHOO_QUOTE_ADAPTER_VERSION,
                "markets": ["TPE", "TWO"],
                "role": "INTRADAY_VERIFICATION_ONLY",
                "marketBatch": False,
                "historicalFallback": None,
            },
            {
                "sourceCode": TAISHIN_INTRADAY_SOURCE_CODE,
                "adapterVersion": TAISHIN_INTRADAY_ADAPTER_VERSION,
                "markets": ["TPE", "TWO"],
                "role": "INTRADAY_ONLY",
                "marketBatch": False,
                "historicalFallback": None,
            },
        ]
    )
    official = {
        item["sourceCode"]: item["adapterVersion"]
        for item in providers
        if item["sourceCode"] in {"TWSE_OFFICIAL_DAILY", "TPEX_OFFICIAL_DAILY"}
    }
    ready = official == {
        "TWSE_OFFICIAL_DAILY": EXPECTED_TWSE_ADAPTER_VERSION,
        "TPEX_OFFICIAL_DAILY": EXPECTED_TPEX_ADAPTER_VERSION,
    } and all(
        item["marketBatch"]
        for item in providers
        if item["sourceCode"] in {"TWSE_OFFICIAL_DAILY", "TPEX_OFFICIAL_DAILY"}
    )
    return {
        "status": "READY" if ready else "NOT_READY",
        "packageVersion": __version__,
        "buildSha": os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_SHA"),
        "postClose": {
            "marketBatch": True,
            "sourceAuthority": {
                "TPE": "TWSE_OFFICIAL_DAILY",
                "TWO": "TPEX_OFFICIAL_DAILY",
            },
        },
        "providers": providers,
    }


__all__ = [
    "EXPECTED_TPEX_ADAPTER_VERSION",
    "EXPECTED_TWSE_ADAPTER_VERSION",
    "build_provider_lineage",
]

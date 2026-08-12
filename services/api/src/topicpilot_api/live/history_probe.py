"""Bounded historical-window capability probe for missing-data recovery."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from topicpilot_api.market_data.history import HistoricalProvider, HistoricalProviderError
from topicpilot_api.market_data.taishin import (
    TAISHIN_PASSWORD_ENV,
    TAISHIN_TIMEOUT_ENV,
    TAISHIN_USER_ENV,
    TaishinTechnicalAnalysisProvider,
)


@dataclass(frozen=True)
class HistoricalWindowEvidence:
    instrument_code: str
    market_code: str
    requested_from: date
    requested_to: date
    status: str
    raw_point_count: int
    returned_point_count: int
    available_close_count: int
    missing_close_count: int
    date_from: date | None
    date_to: date | None
    source_code: str
    adapter_version: str
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrumentCode": self.instrument_code,
            "marketCode": self.market_code,
            "requestedFrom": self.requested_from.isoformat(),
            "requestedTo": self.requested_to.isoformat(),
            "status": self.status,
            "rawPointCount": self.raw_point_count,
            "returnedPointCount": self.returned_point_count,
            "availableCloseCount": self.available_close_count,
            "missingCloseCount": self.missing_close_count,
            "dateFrom": self.date_from.isoformat() if self.date_from else None,
            "dateTo": self.date_to.isoformat() if self.date_to else None,
            "sourceCode": self.source_code,
            "adapterVersion": self.adapter_version,
            "errorCode": self.error_code,
        }


def probe_historical_window(
    provider: HistoricalProvider,
    instruments: list[tuple[str, str]],
    *,
    requested_from: date,
    requested_to: date,
) -> tuple[HistoricalWindowEvidence, ...]:
    """Probe a bounded date window without writing or zero-filling observations."""

    if requested_to < requested_from:
        raise ValueError("requested_to must not precede requested_from")
    results: list[HistoricalWindowEvidence] = []
    for instrument_code, market_code in instruments:
        try:
            fetched = provider.fetch_daily(instrument_code, market_code)
            selected = tuple(
                bar for bar in fetched.bars if requested_from <= bar.trading_date <= requested_to
            )
            available = sum(bar.close is not None for bar in selected)
            missing = sum(bar.close is None for bar in selected)
            results.append(
                HistoricalWindowEvidence(
                    instrument_code=fetched.instrument_code,
                    market_code=fetched.market_code,
                    requested_from=requested_from,
                    requested_to=requested_to,
                    status="AVAILABLE" if available else "NO_DATA",
                    raw_point_count=fetched.raw_point_count,
                    returned_point_count=len(selected),
                    available_close_count=available,
                    missing_close_count=missing,
                    date_from=selected[0].trading_date if selected else None,
                    date_to=selected[-1].trading_date if selected else None,
                    source_code=fetched.source_code,
                    adapter_version=fetched.adapter_version,
                )
            )
        except HistoricalProviderError as exc:
            results.append(
                HistoricalWindowEvidence(
                    instrument_code=instrument_code,
                    market_code=market_code,
                    requested_from=requested_from,
                    requested_to=requested_to,
                    status="PROVIDER_ERROR",
                    raw_point_count=0,
                    returned_point_count=0,
                    available_close_count=0,
                    missing_close_count=0,
                    date_from=None,
                    date_to=None,
                    source_code=provider.source_code,
                    adapter_version=provider.adapter_version,
                    error_code=exc.code,
                )
            )
    return tuple(results)


def _symbols(value: str) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []
    for item in value.split(","):
        code, separator, market = item.strip().partition(":")
        if not separator or not code or not market:
            raise ValueError(f"invalid symbol: {item}")
        parsed.append((code, market))
    if not parsed:
        raise ValueError("at least one symbol is required")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--symbols",
        default="2330:TPE,2317:TPE",
        help="comma-separated instrumentCode:marketCode values",
    )
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.days < 1:
        raise SystemExit("--days must be positive")
    requested_to = args.as_of
    requested_from = requested_to - timedelta(days=args.days - 1)
    username = os.getenv(TAISHIN_USER_ENV, "").strip()
    password = os.getenv(TAISHIN_PASSWORD_ENV, "")
    if not username or not password:
        raise SystemExit("Taishin credentials are not configured")
    try:
        timeout = float(os.getenv(TAISHIN_TIMEOUT_ENV, "30"))
    except ValueError as exc:
        raise SystemExit("Taishin timeout configuration is invalid") from exc
    provider = TaishinTechnicalAnalysisProvider(
        username=username,
        password=password,
        start_date=requested_from,
        timeout=timeout,
    )
    evidence = probe_historical_window(
        provider,
        _symbols(args.symbols),
        requested_from=requested_from,
        requested_to=requested_to,
    )
    print(json.dumps([item.to_dict() for item in evidence], ensure_ascii=False))
    return 0 if all(item.status == "AVAILABLE" for item in evidence) else 1


__all__ = ["HistoricalWindowEvidence", "main", "probe_historical_window"]


if __name__ == "__main__":
    raise SystemExit(main())

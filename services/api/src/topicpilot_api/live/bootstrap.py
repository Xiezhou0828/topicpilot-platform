"""Bounded V2 bootstrap from the read-only V1 stock master.

The bootstrap is deliberately an operator command, not a FastAPI request
path.  It reads the V1 prepared stock file without changing it, creates or
refreshes the V2 instrument identity, and optionally backfills official daily
history through the exchange-specific provider.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.market_data.ingestion import (
    HistoricalSourceRegistration,
    ingest_historical,
)
from topicpilot_api.market_data.rate_limit import RateLimitedTransport
from topicpilot_api.market_data.registry import build_historical_provider_registry
from topicpilot_api.normalizer import HISTORICAL_MAPPING_POLICY_VERSION, MappingPolicy
from topicpilot_api.orm import Instrument, Market


@dataclass(frozen=True)
class StockMasterRecord:
    code: str
    name: str
    market_code: str


@dataclass(frozen=True)
class StockMasterAudit:
    input_count: int
    accepted_count: int
    tpe_count: int
    two_count: int
    skipped_count: int
    invalid_count: int
    duplicate_count: int
    records: tuple[StockMasterRecord, ...]
    issues: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "inputCount": self.input_count,
            "acceptedCount": self.accepted_count,
            "tpeCount": self.tpe_count,
            "twoCount": self.two_count,
            "skippedCount": self.skipped_count,
            "invalidCount": self.invalid_count,
            "duplicateCount": self.duplicate_count,
            "issues": list(self.issues),
        }


_CODE_KEYS = ("股號", "code", "instrumentCode", "instrument_code")
_NAME_KEYS = ("名稱", "name", "instrumentName", "instrument_name")
_MARKET_KEYS = ("市場代碼", "market", "marketCode", "market_code")
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _first(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def audit_v1_stock_master(
    path: Path, *, limit: int | None = None, offset: int = 0
) -> StockMasterAudit:
    """Audit the V1 master without changing it and retain every exclusion reason."""

    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("V1 stock master must be a JSON array")
    records: list[StockMasterRecord] = []
    issues: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    duplicate_count = 0
    invalid_count = 0
    skipped_count = 0
    for row_number, row in enumerate(payload, start=1):
        if not isinstance(row, dict):
            invalid_count += 1
            issues.append({"row": row_number, "status": "INVALID", "reason": "ROW_NOT_OBJECT"})
            continue
        code = str(_first(row, _CODE_KEYS) or "").strip()
        name = str(_first(row, _NAME_KEYS) or "").strip()
        market_code = str(_first(row, _MARKET_KEYS) or "").strip().upper()
        if not code:
            invalid_count += 1
            issues.append({"row": row_number, "status": "INVALID", "reason": "MISSING_CODE"})
            continue
        if not _SYMBOL_RE.fullmatch(code):
            invalid_count += 1
            issues.append(
                {"row": row_number, "code": code, "status": "INVALID", "reason": "INVALID_SYMBOL"}
            )
            continue
        if not name:
            invalid_count += 1
            issues.append(
                {"row": row_number, "code": code, "status": "INVALID", "reason": "MISSING_NAME"}
            )
            continue
        if market_code not in {"TPE", "TWO"}:
            invalid_count += 1
            issues.append(
                {
                    "row": row_number,
                    "code": code,
                    "market": market_code,
                    "status": "INVALID",
                    "reason": "UNSUPPORTED_MARKET",
                }
            )
            continue
        identity = (market_code, code)
        if identity in seen:
            duplicate_count += 1
            skipped_count += 1
            issues.append(
                {
                    "row": row_number,
                    "code": code,
                    "market": market_code,
                    "status": "SKIPPED",
                    "reason": "DUPLICATE_IDENTITY",
                }
            )
            continue
        seen.add(identity)
        records.append(StockMasterRecord(code, name, market_code))
    if offset < 0:
        raise ValueError("offset must not be negative")
    if offset:
        for record in records[:offset]:
            skipped_count += 1
            issues.append(
                {
                    "code": record.code,
                    "market": record.market_code,
                    "status": "SKIPPED",
                    "reason": "OFFSET_NOT_SELECTED",
                }
            )
        records = records[offset:]
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be positive")
        for record in records[limit:]:
            skipped_count += 1
            issues.append(
                {
                    "code": record.code,
                    "market": record.market_code,
                    "status": "SKIPPED",
                    "reason": "LIMIT_NOT_SELECTED",
                }
            )
        records = records[:limit]
    return StockMasterAudit(
        input_count=len(payload),
        accepted_count=len(records),
        tpe_count=sum(record.market_code == "TPE" for record in records),
        two_count=sum(record.market_code == "TWO" for record in records),
        skipped_count=skipped_count,
        invalid_count=invalid_count,
        duplicate_count=duplicate_count,
        records=tuple(records),
        issues=tuple(issues),
    )


def load_v1_stock_master(
    path: Path, *, limit: int | None = None, offset: int = 0
) -> tuple[StockMasterRecord, ...]:
    """Load a V1 JSON stock master as a validated, de-duplicated read-only view."""

    return audit_v1_stock_master(path, limit=limit, offset=offset).records


def ensure_instrument_master(
    session: Session, records: tuple[StockMasterRecord, ...]
) -> dict[str, int]:
    """Upsert only the V2 identity rows needed by the selected sample."""

    market_defaults = {
        "TPE": ("TWSE Listed", "TWSE"),
        "TWO": ("TPEx OTC", "TPEx"),
    }
    markets: dict[str, Market] = {}
    market_created = 0
    instrument_created = 0
    for market_code, (name, exchange) in market_defaults.items():
        market = session.scalar(select(Market).where(Market.code == market_code))
        if market is None:
            market = Market(
                code=market_code,
                name=name,
                exchange_code=exchange,
                timezone="Asia/Taipei",
                calendar_code="TW_MARKET",
                is_active=True,
            )
            session.add(market)
            session.flush()
            market_created += 1
        else:
            market.name = name
            market.exchange_code = exchange
            market.timezone = "Asia/Taipei"
            market.calendar_code = "TW_MARKET"
            market.is_active = True
        markets[market_code] = market

    for record in records:
        market = markets[record.market_code]
        instrument = session.scalar(
            select(Instrument).where(
                Instrument.market_id == market.id,
                Instrument.instrument_code == record.code,
            )
        )
        if instrument is None:
            instrument = Instrument(
                market_id=market.id,
                instrument_code=record.code,
                name=record.name,
                instrument_type="EQUITY",
                currency="TWD",
                is_active=True,
            )
            session.add(instrument)
            instrument_created += 1
        else:
            instrument.name = record.name
            instrument.instrument_type = "EQUITY"
            instrument.currency = "TWD"
            instrument.is_active = True
    session.flush()
    return {
        "selected": len(records),
        "marketCreated": market_created,
        "instrumentCreated": instrument_created,
    }


def bootstrap_official_history(
    session: Session,
    records: tuple[StockMasterRecord, ...],
    *,
    start_date: date,
    end_date: date,
    reference_data_version: str,
    calendar_code: str = "TW_MARKET",
    batch_size: int = 20,
    requests_per_minute: int = 120,
    min_request_interval_seconds: float = 0.05,
    max_provider_retries: int = 2,
    retry_backoff_seconds: float = 1.0,
) -> tuple[dict[str, Any], ...]:
    """Backfill selected symbols in bounded batches with explicit outcomes."""

    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    transport = RateLimitedTransport(
        _exchange_transport,
        requests_per_minute=requests_per_minute,
        min_interval_seconds=min_request_interval_seconds,
        max_retries=max_provider_retries,
        retry_backoff_seconds=retry_backoff_seconds,
    )

    registry = build_historical_provider_registry(
        start_date=start_date, end_date=end_date, exchange_transport=transport
    )
    policy = MappingPolicy(
        mapping_policy_version=HISTORICAL_MAPPING_POLICY_VERSION,
        session_code="REGULAR",
        calendar_code=calendar_code,
    )
    outcomes: list[dict[str, Any]] = []
    for batch_number, offset in enumerate(range(0, len(records), batch_size), start=1):
        batch = records[offset : offset + batch_size]
        for record in batch:
            registration = registry.for_market(record.market_code)[0]
            try:
                result = ingest_historical(
                    session,
                    registration.adapter,
                    [(record.code, record.market_code)],
                    reference_data_version=reference_data_version,
                    requested_from=start_date,
                    requested_to=end_date,
                    policy=policy,
                    registration=HistoricalSourceRegistration(
                        registration.code,
                        registration.adapter.adapter_version,
                        licensing_classification="OFFICIAL_PUBLIC",
                    ),
                )
                session.commit()
                outcomes.append(
                    {
                        "batchNumber": batch_number,
                        "instrumentCode": record.code,
                        "market": record.market_code,
                        "provider": registration.code,
                        "status": "COMPLETED",
                        **result.to_dict(),
                    }
                )
            except Exception as exc:
                session.rollback()
                error_code = getattr(exc, "code", type(exc).__name__)
                status = (
                    "SKIPPED"
                    if error_code in {"EXCHANGE_NO_DATA", "INSTRUMENT_NOT_FOUND"}
                    else "FAILED"
                )
                outcomes.append(
                    {
                        "batchNumber": batch_number,
                        "instrumentCode": record.code,
                        "market": record.market_code,
                        "provider": registration.code,
                        "status": status,
                        "errorCode": error_code,
                        "reason": str(exc),
                    }
                )
    return tuple(outcomes)


def _exchange_transport(url: str, timeout: float) -> bytes:
    from urllib.request import Request, urlopen

    request = Request(url, headers={"User-Agent": "TopicPilot-V2/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _parse_codes(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {item.strip() for item in value.split(",") if item.strip()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stock-master",
        default=os.getenv("TOPICPILOT_V1_STOCK_MASTER_PATH"),
        help="read-only V1 JSON stock master path",
    )
    parser.add_argument(
        "--codes", help="comma-separated bounded sample, for example 2317,2330,6488"
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--history-from", type=date.fromisoformat)
    parser.add_argument("--history-to", type=date.fromisoformat)
    parser.add_argument("--skip-history", action="store_true")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--requests-per-minute", type=int, default=120)
    parser.add_argument("--min-request-interval-seconds", type=float, default=0.05)
    parser.add_argument("--max-provider-retries", type=int, default=2)
    parser.add_argument("--retry-backoff-seconds", type=float, default=1.0)
    parser.add_argument("--report-path", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.stock_master:
        raise SystemExit("--stock-master or TOPICPILOT_V1_STOCK_MASTER_PATH is required")
    audit = audit_v1_stock_master(Path(args.stock_master), limit=args.limit, offset=args.offset)
    records = audit.records
    codes = _parse_codes(args.codes)
    if codes is not None:
        records = tuple(record for record in records if record.code in codes)
    if not records:
        raise SystemExit("selected V1 stock master sample is empty")
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    with Session(engine, expire_on_commit=False) as session:
        master_result = ensure_instrument_master(session, records)
        session.commit()
        output: dict[str, Any] = {
            "stockMaster": str(Path(args.stock_master).resolve()),
            "readOnlyInput": True,
            "master": {**audit.to_dict(), **master_result, "failedCount": 0},
        }
        if not args.skip_history:
            end_date = args.history_to or (date.today() - timedelta(days=1))
            start_date = args.history_from or (end_date - timedelta(days=90))
            if end_date < start_date:
                raise SystemExit("--history-to must not precede --history-from")
            output["history"] = list(
                bootstrap_official_history(
                    session,
                    records,
                    start_date=start_date,
                    end_date=end_date,
                    reference_data_version=LiveRuntimeConfig.reference_data_version,
                    batch_size=args.batch_size,
                    requests_per_minute=args.requests_per_minute,
                    min_request_interval_seconds=args.min_request_interval_seconds,
                    max_provider_retries=args.max_provider_retries,
                    retry_backoff_seconds=args.retry_backoff_seconds,
                )
            )
            output["historyWindow"] = {
                "from": start_date.isoformat(),
                "to": end_date.isoformat(),
            }
        serialized = json.dumps(output, ensure_ascii=False, indent=2, default=str)
        if args.report_path:
            args.report_path.parent.mkdir(parents=True, exist_ok=True)
            args.report_path.write_text(serialized + "\n", encoding="utf-8")
        print(serialized)
    return 0


__all__ = [
    "StockMasterAudit",
    "StockMasterRecord",
    "audit_v1_stock_master",
    "bootstrap_official_history",
    "ensure_instrument_master",
    "load_v1_stock_master",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())

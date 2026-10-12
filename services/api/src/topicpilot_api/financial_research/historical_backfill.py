from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .contract import RawFinancialRecord, SourceAdapterResult


@dataclass(frozen=True)
class HistoricalPeriodRequest:
    ticker: str
    roc_year: int
    quarter: int

    @property
    def key(self) -> str:
        return f"{self.ticker}:{self.roc_year}:Q{self.quarter}"


@dataclass
class HistoricalBackfillCheckpoint:
    key: str
    status: str = "PENDING"
    attempts: int = 0
    record_count: int = 0
    raw_artifact_hash: str | None = None
    error_reason: str | None = None


@dataclass
class HistoricalBackfillRun:
    checkpoints: dict[str, HistoricalBackfillCheckpoint] = field(default_factory=dict)
    records: list[RawFinancialRecord] = field(default_factory=list)


class HistoricalBackfillRunner:
    """Resumable, idempotent non-persistence runner for official periods."""

    def __init__(
        self,
        retrieve: Callable[[str, int, int], SourceAdapterResult],
        *,
        max_attempts: int = 2,
    ) -> None:
        self.retrieve = retrieve
        self.max_attempts = max_attempts

    def run(
        self,
        requests: list[HistoricalPeriodRequest],
        *,
        existing: HistoricalBackfillRun | None = None,
    ) -> HistoricalBackfillRun:
        run = existing or HistoricalBackfillRun()
        seen: set[tuple[str, str, str]] = {
            (record.ticker, record.filing_id, record.line_item_standard)
            for record in run.records
        }
        for request in requests:
            checkpoint = run.checkpoints.setdefault(
                request.key,
                HistoricalBackfillCheckpoint(key=request.key),
            )
            if checkpoint.status == "SUCCESS":
                continue
            result: SourceAdapterResult | None = None
            while checkpoint.attempts < self.max_attempts:
                checkpoint.attempts += 1
                result = self.retrieve(request.ticker, request.roc_year, request.quarter)
                if result.status not in {"SOURCE_UNAVAILABLE", "RATE_LIMITED"}:
                    break
            if result is None:
                checkpoint.status = "FAILED"
                checkpoint.error_reason = "未執行 retrieve。"
                continue
            checkpoint.raw_artifact_hash = result.raw_artifact_hash
            checkpoint.record_count = len(result.records)
            checkpoint.error_reason = result.error_reason
            checkpoint.status = "SUCCESS" if result.records else result.status
            for record in result.records:
                identity = (record.ticker, record.filing_id, record.line_item_standard)
                if identity not in seen:
                    run.records.append(record)
                    seen.add(identity)
        return run

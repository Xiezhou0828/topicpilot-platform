# ruff: noqa: RUF001

"""Small, auditable reconciliation helpers for known Preview discrepancies."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReconciliationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str
    period_label: str
    line_item: str
    statement_value: Decimal | None
    reported_value: Decimal | None
    variance: Decimal | None
    status: Literal["PASS", "UNRESOLVED", "MISSING_INPUT"]
    note: str


def reconcile_reported_line(
    *,
    ticker: str,
    period_label: str,
    line_item: str,
    statement_value: Decimal | None,
    reported_value: Decimal | None,
) -> ReconciliationResult:
    if statement_value is None or reported_value is None:
        return ReconciliationResult(
            ticker=ticker,
            period_label=period_label,
            line_item=line_item,
            statement_value=statement_value,
            reported_value=reported_value,
            variance=None,
            status="MISSING_INPUT",
            note="缺少同一期間可比數值，未進行補值。",
        )
    variance = statement_value - reported_value
    status = "PASS" if variance == 0 else "UNRESOLVED"
    return ReconciliationResult(
        ticker=ticker,
        period_label=period_label,
        line_item=line_item,
        statement_value=statement_value,
        reported_value=reported_value,
        variance=variance,
        status=status,
        note=(
            "同期間數值相符。"
            if status == "PASS"
            else "數值差異已保留；尚未找到足以解釋差異的官方更正或科目對應證據。"
        ),
    )


__all__ = ["ReconciliationResult", "reconcile_reported_line"]

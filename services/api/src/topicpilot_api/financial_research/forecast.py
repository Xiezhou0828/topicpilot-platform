# ruff: noqa: RUF001

"""Non-publishing, deterministic forecast calculation contract.

The engine accepts only explicit assumptions. It creates reviewable output but
never advances a run to APPROVED and is not wired to a public endpoint.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from hashlib import sha256

from .contract import ForecastAssumption, ForecastOutput, ForecastRun

REQUIRED = (
    "base_revenue",
    "revenue_growth",
    "gross_margin",
    "operating_margin",
    "tax_rate",
    "weighted_average_shares",
)


def _run_id(ticker: str, assumptions: Mapping[str, Decimal]) -> str:
    material = "|".join(f"{key}={assumptions[key]}" for key in sorted(assumptions))
    return f"FCST-{sha256(f'{ticker}|{material}'.encode()).hexdigest()[:16]}"


def build_forecast_run(
    ticker: str,
    assumptions: Mapping[str, Decimal],
    *,
    scenario: str = "BASE",
    quarters: int = 4,
    fiscal_years: int = 3,
) -> ForecastRun:
    missing = [key for key in REQUIRED if key not in assumptions]
    source_assumptions = [
        ForecastAssumption(
            key=key,
            value=assumptions.get(key),
            unit=(
                "TWD_1000"
                if key == "base_revenue"
                else "%"
                if key.endswith("margin") or key.endswith("rate") or key == "revenue_growth"
                else "SHARES_1000"
            ),
            source="owner_input",
            status="AVAILABLE" if key in assumptions else "BLOCKED",
        )
        for key in REQUIRED
    ]
    if missing:
        return ForecastRun(
            run_id=_run_id(ticker, assumptions),
            ticker=ticker,
            state="DRAFT",
            assumptions=source_assumptions,
            missing_prerequisites=[f"缺少明確假設：{key}" for key in missing],
        )
    if scenario not in {"BASE", "BEAR", "BULL"}:
        raise ValueError("scenario must be BASE, BEAR, or BULL")
    growth = assumptions["revenue_growth"]
    if scenario == "BEAR":
        growth -= Decimal("0.05")
    elif scenario == "BULL":
        growth += Decimal("0.05")
    revenue = assumptions["base_revenue"]
    outputs: list[ForecastOutput] = []
    for index in range(1, quarters + fiscal_years + 1):
        revenue *= Decimal("1") + growth
        gross = revenue * assumptions["gross_margin"]
        operating = revenue * assumptions["operating_margin"]
        net = operating * (Decimal("1") - assumptions["tax_rate"])
        eps = net / assumptions["weighted_average_shares"]
        period = f"Q{index}" if index <= quarters else f"FY+{index - quarters}"
        outputs.append(
            ForecastOutput(
                ticker=ticker,
                scenario=scenario,
                period_label=period,
                revenue=revenue,
                gross_profit=gross,
                operating_income=operating,
                net_income=net,
                basic_eps=eps,
                status="AVAILABLE",
                note="由明確輸入假設計算；尚未完成管理層審查與發布。",
            )
        )
    return ForecastRun(
        run_id=_run_id(ticker, assumptions),
        ticker=ticker,
        state="CALCULATED",
        assumptions=source_assumptions,
        outputs=outputs,
    )


def advance_forecast_state(run: ForecastRun, target: str) -> ForecastRun:
    """Advance only through the controlled state machine; APPROVED is gated."""

    allowed = {
        "DRAFT": {"CALCULATED"},
        "CALCULATED": {"VALIDATED"},
        "VALIDATED": {"REVIEW_PENDING"},
        "REVIEW_PENDING": set(),
        "APPROVED": set(),
    }
    if target not in allowed[run.state]:
        raise ValueError(f"invalid forecast transition {run.state} -> {target}")
    return run.model_copy(update={"state": target})


__all__ = ["advance_forecast_state", "build_forecast_run"]

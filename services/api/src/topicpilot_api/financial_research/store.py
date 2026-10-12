# ruff: noqa: RUF001

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from typing import Protocol

from .contract import (
    EpsNoteExtractionResult,
    FinancialCoverageResponse,
    FinancialEpsBridgeResponse,
    FinancialFact,
    FinancialPeriodCoverage,
    FinancialResearchStatusResponse,
    FinancialSource,
    FinancialStatementLine,
    FinancialStatementResponse,
    FinancialSummaryMetric,
    FinancialSummaryResponse,
)
from .eps_bridge import build_eps_bridge

# User-facing Chinese provenance and limitation strings intentionally use
# full-width punctuation.


class FinancialResearchReadStore(Protocol):
    def coverage(self, ticker: str) -> FinancialCoverageResponse: ...

    def summary(self, ticker: str) -> FinancialSummaryResponse: ...

    def statements(self, ticker: str) -> FinancialStatementResponse: ...

    def status(self, ticker: str) -> FinancialResearchStatusResponse: ...

    def eps_bridge(self, ticker: str) -> FinancialEpsBridgeResponse: ...


class EmptyFinancialResearchStore:
    """Default public store: exposes readiness only, never fabricated facts."""

    def coverage(self, ticker: str) -> FinancialCoverageResponse:
        return FinancialCoverageResponse(
            ticker=ticker,
            status="MISSING",
            missing_fields=[
                "金融事實資料尚未接入正式 read model。",
                "最近五年與後續季度覆蓋尚未完成。",
                "來源權利尚未完成公開再分發確認。",
            ],
            source_rights_status="UNVERIFIED",
        )

    def summary(self, ticker: str) -> FinancialSummaryResponse:
        return FinancialSummaryResponse(
            ticker=ticker,
            status="MISSING",
            missing_fields=["目前沒有可公開讀取的正規化財務事實。"],
            source_rights_status="UNVERIFIED",
        )

    def statements(self, ticker: str) -> FinancialStatementResponse:
        return FinancialStatementResponse(
            ticker=ticker,
            status="MISSING",
            missing_fields=["三大財務報表尚未接入正式 read model。"],
            source_rights_status="UNVERIFIED",
        )

    def status(self, ticker: str) -> FinancialResearchStatusResponse:
        return FinancialResearchStatusResponse(
            ticker=ticker,
            historical_data_readiness="BLOCKED",
            model_readiness="BLOCKED",
            forecast_available=False,
            publication_status="NOT_PUBLISHED",
            source_rights_status="UNVERIFIED",
            quality_status="NOT_CONNECTED",
            missing_prerequisites=[
                "Financial Facts schema/persistence 尚未 canonicalized。",
                "來源權利尚未確認。",
                "歷史三表與股數橋接尚未完成。",
                "尚無可發布的 forecast model。",
            ],
        )

    def eps_bridge(self, ticker: str) -> FinancialEpsBridgeResponse:
        return FinancialEpsBridgeResponse(
            ticker=ticker,
            status="MISSING",
            missing_fields=["尚未接入同期間母公司淨利與加權平均股數橋接。"],
            source_rights_status="UNVERIFIED",
        )


class InMemoryFinancialResearchStore:
    """Non-production, deterministic store used by contract/API tests."""

    def __init__(
        self,
        facts: Iterable[FinancialFact] = (),
        sources: Iterable[FinancialSource] = (),
        eps_note_results: Iterable[EpsNoteExtractionResult] = (),
        *,
        allow_public_values: bool = False,
        preview_only: bool = False,
    ) -> None:
        self.facts = list(facts)
        self.sources = {source.source_id: source for source in sources}
        self.eps_note_results = list(eps_note_results)
        self.allow_public_values = allow_public_values
        self.preview_only = preview_only

    def _facts(self, ticker: str) -> list[FinancialFact]:
        return [fact for fact in self.facts if fact.ticker == ticker]

    def _rights(self, facts: list[FinancialFact]) -> str:
        if not facts:
            return "UNVERIFIED"
        statuses = {
            self.sources.get(
                fact.source_id,
                FinancialSource(
                    source_id=fact.source_id, source_type="unknown", owner_or_provider="unknown"
                ),
            ).redistribution_rights
            for fact in facts
        }
        if statuses and statuses <= {"APPROVED", "PUBLIC_ALLOWED"}:
            return "APPROVED"
        return "UNVERIFIED"

    def coverage(self, ticker: str) -> FinancialCoverageResponse:
        facts = self._facts(ticker)
        rights = self._rights(facts)
        grouped: dict[tuple[str, date | None, str], set[str]] = defaultdict(set)
        statement_coverage: dict[str, set[str]] = defaultdict(set)
        eps: set[str] = set()
        shares: set[str] = set()
        for fact in facts:
            if fact.normalized_value is None:
                continue
            grouped[(fact.period_label, fact.period_end, fact.period_type)].add(fact.statement)
            statement_coverage[fact.statement].add(fact.period_label)
            if fact.line_item_standard in {"basic_eps", "diluted_eps"}:
                eps.add(fact.period_label)
            if fact.statement == "share_count":
                shares.add(fact.period_label)
        periods = [
            FinancialPeriodCoverage(
                period_label=label,
                period_end=end,
                period_type=period_type,
                statements=sorted(statements),
            )
            for (label, end, period_type), statements in sorted(grouped.items())
        ]
        status = (
            "AVAILABLE"
            if facts and rights == "APPROVED"
            else ("BLOCKED_RIGHTS" if facts else "MISSING")
        )
        return FinancialCoverageResponse(
            ticker=ticker,
            status=status,
            available_periods=periods if rights == "APPROVED" or self.allow_public_values else [],
            statement_coverage={key: sorted(values) for key, values in statement_coverage.items()}
            if rights == "APPROVED" or self.allow_public_values
            else {},
            eps_coverage=sorted(eps) if rights == "APPROVED" or self.allow_public_values else [],
            share_count_coverage=sorted(shares)
            if rights == "APPROVED" or self.allow_public_values
            else [],
            missing_fields=(
                []
                if rights == "APPROVED"
                else [
                    "目前為受控 non-Production Preview；來源權利尚未核准公開再分發。",
                    "目前 read model 僅涵蓋已驗證的 2025 全年與 2026 Q1/Q2。",
                ]
            )
            if facts
            else ["尚無可用財務事實。"],
            source_rights_status=rights,
            source_ids=sorted({fact.source_id for fact in facts})
            if rights == "APPROVED" or self.allow_public_values
            else [],
        )

    def summary(self, ticker: str) -> FinancialSummaryResponse:
        facts = self._facts(ticker)
        rights = self._rights(facts)
        if not facts or (rights != "APPROVED" and not self.allow_public_values):
            return FinancialSummaryResponse(
                ticker=ticker,
                status="BLOCKED_RIGHTS" if facts else "MISSING",
                missing_fields=["資料權利未允許公開數值。"],
                source_rights_status=rights,
            )
        target_lines = {
            "revenue",
            "gross_profit",
            "gross_profit_reported",
            "cost_of_revenue",
            "operating_expenses",
            "operating_income",
            "pretax_income",
            "net_income",
            "parent_net_income",
            "basic_eps",
            "diluted_eps",
            "assets",
            "current_assets",
            "non_current_assets",
            "current_liabilities",
            "non_current_liabilities",
            "parent_equity",
            "noncontrolling_interest",
            "cash_and_equivalents",
            "cash_from_operations",
            "cash_from_investing",
            "cash_from_financing",
            "cash_at_beginning",
            "cash_at_end",
            "fx_effect_on_cash",
            "net_change_in_cash",
        }
        metrics = [
            FinancialSummaryMetric(
                metric=fact.line_item_standard,
                statement=fact.statement,
                period_label=fact.period_label,
                period_type=fact.period_type,
                period_end=fact.period_end,
                value=fact.normalized_value,
                unit=fact.normalized_unit,
                currency=fact.currency,
                source_id=fact.source_id,
                source_location=fact.source_location,
                evidence_label=fact.evidence_label,
                status=fact.data_quality_status,
                validation_status=self._validation_status(fact),
                validation_note=self._validation_note(fact),
            )
            for fact in facts
            if fact.line_item_standard in target_lines and fact.normalized_value is not None
        ]
        metrics.extend(self._derived_margin_metrics(facts))
        return FinancialSummaryResponse(
            ticker=ticker,
            status="AVAILABLE" if metrics else "MISSING",
            metrics=metrics,
            missing_fields=(
                ["受控 Preview 數值；來源權利尚未核准公開再分發。"]
                if rights != "APPROVED"
                else []
            )
            if metrics
            else ["摘要科目尚未具備可用數值。"],
            source_rights_status=rights,
        )

    def statements(self, ticker: str) -> FinancialStatementResponse:
        facts = self._facts(ticker)
        rights = self._rights(facts)
        if not facts or (rights != "APPROVED" and not self.allow_public_values):
            return FinancialStatementResponse(
                ticker=ticker,
                status="BLOCKED_RIGHTS" if facts else "MISSING",
                missing_fields=["資料權利未允許公開完整報表。"],
                source_rights_status=rights,
            )
        lines = [
            FinancialStatementLine(
                line_item=fact.line_item_standard,
                period_label=fact.period_label,
                period_type=fact.period_type,
                period_end=fact.period_end,
                value=fact.normalized_value,
                unit=fact.normalized_unit,
                currency=fact.currency,
                source_id=fact.source_id,
                source_location=fact.source_location,
                status=fact.data_quality_status,
                validation_status=self._validation_status(fact),
                validation_note=self._validation_note(fact),
            )
            for fact in facts
            if fact.statement in {"income_statement", "balance_sheet", "cash_flow"}
            and fact.normalized_value is not None
        ]
        return FinancialStatementResponse(
            ticker=ticker,
            status="AVAILABLE" if lines else "MISSING",
            annual=[line for line in lines if line.period_label.upper().startswith("FY")],
            quarterly=[line for line in lines if line.period_label.upper().startswith("Q")],
            ytd=[
                line
                for line in lines
                if "H1" in line.period_label.upper()
                or "9M" in line.period_label.upper()
                or line.period_label.upper().endswith("_YTD")
            ],
            source_rights_status=rights,
            missing_fields=(
                ["受控 Preview 數值；來源權利尚未核准公開再分發。"]
                if rights != "APPROVED"
                else []
            )
            if lines
            else ["尚無可用三表科目。"],
        )

    def eps_bridge(self, ticker: str) -> FinancialEpsBridgeResponse:
        facts = self._facts(ticker)
        rights = self._rights(facts)
        records = build_eps_bridge(self.facts, ticker, self.eps_note_results)
        if not records:
            return FinancialEpsBridgeResponse(
                ticker=ticker,
                status="MISSING",
                missing_fields=["沒有同期間公告 EPS 可供橋接。"],
                source_rights_status=rights,
            )
        if rights != "APPROVED" and not self.allow_public_values:
            return FinancialEpsBridgeResponse(
                ticker=ticker,
                status="BLOCKED_RIGHTS",
                missing_fields=["來源權利未允許公開橋接數值。"],
                source_rights_status=rights,
            )
        complete = [record for record in records if record.status == "RECOMPUTED_MATCH"]
        return FinancialEpsBridgeResponse(
            ticker=ticker,
            status="AVAILABLE" if complete else "PENDING_REVIEW",
            records=records,
            missing_fields=(
                []
                if complete
                else ["部分期間缺少可配對的加權平均股數或存在待釐清差異。"]
            ),
            source_rights_status=rights,
        )

    def _validation_status(self, fact: FinancialFact) -> str:
        if fact.line_item_standard in {"basic_eps", "diluted_eps"}:
            bridge = self.eps_bridge(fact.ticker)
            record = next(
                (item for item in bridge.records if item.period_label == fact.period_label),
                None,
            )
            if record and record.status == "RECOMPUTED_MATCH":
                return "PASS"
            return "PARTIAL"
        if (
            fact.ticker == "1314"
            and fact.period_label == "2026Q2_YTD"
            and fact.line_item_standard == "net_income"
        ):
            return "PARTIAL"
        return "PASS"

    def _validation_note(self, fact: FinancialFact) -> str | None:
        if fact.line_item_standard in {"basic_eps", "diluted_eps"}:
            bridge = self.eps_bridge(fact.ticker)
            record = next(
                (item for item in bridge.records if item.period_label == fact.period_label),
                None,
            )
            if record and record.status == "RECOMPUTED_MATCH":
                return "同期間母公司業主淨利與加權平均股數重算後，與公告 EPS 相符。"
            return "公告 EPS 已取得，但同期間加權平均股數尚未完成橋接。"
        if (
            fact.ticker == "1314"
            and fact.period_label == "2026Q2_YTD"
            and fact.line_item_standard == "net_income"
        ):
            return "稅前淨利減所得稅與公告淨利差異 8,426,000 元，保留為待釐清。"
        return "同一期間官方財報科目；已通過本次 Preview read-model validation。"

    def _derived_margin_metrics(self, facts: list[FinancialFact]) -> list[FinancialSummaryMetric]:
        by_key = {
            (fact.period_label, fact.statement, fact.line_item_standard): fact
            for fact in facts
            if fact.normalized_value is not None
        }
        results: list[FinancialSummaryMetric] = []
        for period in sorted({fact.period_label for fact in facts}):
            revenue = by_key.get((period, "income_statement", "revenue"))
            if revenue is None or revenue.normalized_value in {None, 0}:
                continue
            for source_line, metric in (
                ("gross_profit", "gross_margin"),
                ("operating_income", "operating_margin"),
                ("net_income", "net_margin"),
            ):
                source = by_key.get((period, "income_statement", source_line))
                if source is None or source.normalized_value is None:
                    continue
                value = source.normalized_value / revenue.normalized_value * Decimal("100")
                partial = self._validation_status(source) == "PARTIAL"
                results.append(
                    FinancialSummaryMetric(
                        metric=metric,
                        statement="derived_income_statement",
                        period_label=period,
                        period_type=source.period_type,
                        period_end=source.period_end,
                        value=value,
                        unit="%",
                        currency="TWD",
                        source_id=source.source_id,
                        source_location=source.source_location,
                        evidence_label="derived_calculation",
                        status="AVAILABLE",
                        validation_status="PARTIAL" if partial else "PASS",
                        validation_note=(
                            "由同一期間官方營收與財報科目計算；1314 淨利率受待釐清差異影響。"
                            if partial
                            else "由同一期間官方營收與財報科目計算。"
                        ),
                    )
                )
        return results

    def status(self, ticker: str) -> FinancialResearchStatusResponse:
        facts = self._facts(ticker)
        rights = self._rights(facts)
        coverage = self.coverage(ticker)
        history = "READY" if coverage.status == "AVAILABLE" else ("PARTIAL" if facts else "BLOCKED")
        missing = (
            []
            if facts and rights == "APPROVED"
            else ["來源權利未完成公開確認。", "三表與股數橋接尚未形成決策級模型輸入。"]
        )
        return FinancialResearchStatusResponse(
            ticker=ticker,
            historical_data_readiness=history,
            model_readiness="BLOCKED",
            forecast_available=False,
            publication_status="NOT_PUBLISHED",
            source_rights_status=rights,
            missing_prerequisites=missing,
            quality_status="PARTIAL" if facts else "NOT_CONNECTED",
            as_of=max(
                (fact.period_end for fact in facts if fact.period_end is not None), default=None
            ),
        )

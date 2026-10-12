# ruff: noqa: RUF001

from __future__ import annotations

from topicpilot_api.financial_research.historical_backfill import (
    HistoricalBackfillRunner,
    HistoricalPeriodRequest,
)
from topicpilot_api.financial_research.normalization import normalize_records
from topicpilot_api.financial_research.source_adapter import MopsLegacyHistoricalAdapter


def _html(statement: str) -> bytes:
    rows = {
        "ajax_t164sb03": """
          <table><tr><th>會計項目</th><th>2025年06月30日</th></tr>
          <tr><td>資產總計</td><td>100,000</td></tr>
          <tr><td>負債總計</td><td>40,000</td></tr>
          <tr><td>權益總計</td><td>60,000</td></tr></table>
        """,
        "ajax_t164sb04": """
          <table><tr><th>民國114年第2季</th></tr>
          <tr><th>會計項目</th><th>114年第2季</th><th>%</th><th>113年第2季</th><th>%</th>
          <th>114年01月01日至114年06月30日</th><th>%</th></tr>
          <tr><th></th><th>金額</th><th>%</th><th>金額</th><th>%</th><th>金額</th><th>%</th></tr>
          <tr><td>營業收入合計</td><td>10,000</td><td>100</td><td>9,000</td><td>100</td><td>20,000</td><td>100</td></tr>
          <tr><td>基本每股盈餘</td><td>1.20</td><td></td><td>1.00</td><td></td><td>2.40</td><td></td></tr></table>
        """,
        "ajax_t164sb05": """
          <table><tr><th>會計項目</th><th>金額</th></tr>
          <tr><td>營業活動之淨現金流入（流出）</td><td>3,000</td></tr>
          <tr><td>期末現金及約當現金餘額</td><td>8,000</td></tr></table>
        """,
        "ajax_t164sb06": """
          <table><tr><th>會計項目</th><th>金額</th></tr>
          <tr><td>權益總額</td><td>60,000</td></tr></table>
        """,
    }
    return rows[statement].encode("utf-8")


def test_mops_legacy_adapter_keeps_ytd_and_standalone_distinct() -> None:
    def fetcher(url: str, params: dict[str, str]) -> bytes:
        return _html(url.rsplit("/", 1)[-1])

    result = MopsLegacyHistoricalAdapter(fetcher).retrieve("1303", 114, 2)

    assert result.status == "RIGHTS_UNVERIFIED"
    assert result.filing is not None
    assert result.filing.reporting_period_end is not None
    labels = {(record.line_item_standard, record.period_label) for record in result.records}
    assert ("revenue", "2025Q2") in labels
    assert ("revenue", "2025Q2_YTD") in labels
    assert ("basic_eps", "2025Q2_YTD") in labels
    cash_flow_labels = {
        record.period_label for record in result.records if record.statement == "cash_flow"
    }
    assert cash_flow_labels == {"2025Q2_YTD"}
    assert all(record.source_id == "SRC-MOPS-LEGACY-HTML-T164" for record in result.records)


def test_historical_runner_is_resumable_and_idempotent() -> None:
    calls = 0

    def retrieve(ticker: str, year: int, quarter: int):
        nonlocal calls
        calls += 1
        return MopsLegacyHistoricalAdapter(lambda *_: _html("ajax_t164sb03")).retrieve(
            ticker, year, quarter
        )

    request = HistoricalPeriodRequest("1303", 114, 2)
    runner = HistoricalBackfillRunner(retrieve)
    first = runner.run([request])
    second = runner.run([request], existing=first)

    assert calls == 1
    assert len(second.records) == len(first.records)
    assert second.checkpoints[request.key].status == "SUCCESS"


def test_mops_twd_1000_records_normalize_without_unknown_unit() -> None:
    def fetcher(url: str, params: dict[str, str]) -> bytes:
        return _html(url.rsplit("/", 1)[-1])

    result = MopsLegacyHistoricalAdapter(fetcher).retrieve("1303", 114, 2)
    normalized = normalize_records(result.records)

    assert not [issue for issue in normalized.issues if issue.issue_type == "UNKNOWN_UNIT"]
    monetary = [fact for fact in normalized.facts if fact.source_unit == "TWD_1000"]
    assert monetary
    assert all(fact.normalized_unit == "BASE_CURRENCY" for fact in monetary)
    assert all(fact.data_quality_status == "AVAILABLE" for fact in monetary)

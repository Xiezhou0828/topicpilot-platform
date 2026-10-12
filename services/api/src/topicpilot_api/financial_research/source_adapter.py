from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from datetime import date
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from typing import ClassVar

from .contract import (
    FinancialFiling,
    FinancialSource,
    RawFinancialRecord,
    SourceAdapterResult,
)


class LocalJsonFilingAdapter:
    """Safe POC adapter for an explicitly supplied local JSON artifact.

    It does not claim live MOPS access.  A future official provider adapter can
    reuse the same result contract without writing directly to Financial Facts.
    """

    adapter_id = "local-json-filing-poc.v1"

    def __init__(self, path: Path):
        self.path = path

    def retrieve(self) -> SourceAdapterResult:
        if not self.path.exists():
            return SourceAdapterResult(
                adapter_id=self.adapter_id,
                status="SOURCE_UNAVAILABLE",
                error_reason=f"找不到固定測試樣本: {self.path}",
            )
        try:
            raw = self.path.read_bytes()
            payload = json.loads(raw.decode("utf-8"))
            source = FinancialSource.model_validate(payload["source"])
            filing = FinancialFiling.model_validate(payload["filing"])
            records = [RawFinancialRecord.model_validate(item) for item in payload["facts"]]
        except KeyError as exc:
            return SourceAdapterResult(
                adapter_id=self.adapter_id,
                status="SCHEMA_CHANGED",
                error_reason=f"固定樣本缺少必要節點: {exc}",
            )
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return SourceAdapterResult(
                adapter_id=self.adapter_id,
                status="PARSER_FAILED",
                error_reason=str(exc),
            )
        if not records:
            return SourceAdapterResult(
                adapter_id=self.adapter_id,
                status="EMPTY_RESULT",
                source=source,
                filing=filing,
                raw_artifact_hash=hashlib.sha256(raw).hexdigest(),
                rights_checked=True,
            )
        return SourceAdapterResult(
            adapter_id=self.adapter_id,
            status="SUCCESS"
            if source.license_review_status == "TEST_ONLY"
            else "RIGHTS_UNVERIFIED",
            source=source,
            filing=filing,
            raw_artifact_hash=hashlib.sha256(raw).hexdigest(),
            records=records,
            live_intake=False,
            rights_checked=True,
            error_reason=None
            if source.license_review_status == "TEST_ONLY"
            else "來源使用權尚未完成確認。",
        )


class MopsSourceAdapter:
    """Provider boundary for future MOPS intake; network access is injected.

    The default is intentionally fail-closed.  No hidden HTTP call is made and
    no response is persisted without a caller-supplied fetcher and rights
    decision.
    """

    adapter_id = "mops-financial-poc.v1"

    def __init__(self, fetcher: Callable[[str], bytes] | None = None):
        self.fetcher = fetcher

    def retrieve(self, source_url: str) -> SourceAdapterResult:
        if self.fetcher is None:
            return SourceAdapterResult(
                adapter_id=self.adapter_id,
                status="SOURCE_UNAVAILABLE",
                error_reason=(
                    "Live MOPS fetcher 未設定; 本次只完成 provider boundary, 未宣稱 live intake。"
                ),
                live_intake=False,
                rights_checked=False,
            )
        try:
            raw = self.fetcher(source_url)
            payload = json.loads(raw.decode("utf-8"))
            source = FinancialSource.model_validate(payload["source"])
            filing = FinancialFiling.model_validate(payload["filing"])
            records = [RawFinancialRecord.model_validate(item) for item in payload["facts"]]
        except PermissionError as exc:
            return SourceAdapterResult(
                adapter_id=self.adapter_id,
                status="ACCESS_DENIED",
                error_reason=str(exc),
                live_intake=True,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            return SourceAdapterResult(
                adapter_id=self.adapter_id,
                status="PARSER_FAILED",
                error_reason=str(exc),
                live_intake=True,
            )
        if source.redistribution_rights not in {"APPROVED", "PUBLIC_ALLOWED"}:
            return SourceAdapterResult(
                adapter_id=self.adapter_id,
                status="RIGHTS_UNVERIFIED",
                source=source,
                filing=filing,
                raw_artifact_hash=hashlib.sha256(raw).hexdigest(),
                records=records,
                live_intake=True,
                rights_checked=True,
                error_reason="來源可讀, 但再分發權利尚未確認; 不可進入公開 Financial Facts。",
            )
        return SourceAdapterResult(
            adapter_id=self.adapter_id,
            status="SUCCESS",
            source=source,
            filing=filing,
            raw_artifact_hash=hashlib.sha256(raw).hexdigest(),
            records=records,
            live_intake=True,
            rights_checked=True,
        )


# ruff: noqa: RUF001


class TwseOpenApiSnapshotAdapter:
    """Read-only adapter for the official TWSE OpenAPI financial snapshots.

    The OpenAPI publishes a current listed-company snapshot rather than a
    queryable five-year filing archive.  This adapter therefore deliberately
    returns the reported period as-is (income statement YTD and balance-sheet
    instant data), preserves the official Chinese line-item labels, and marks
    redistribution rights as unverified until the owner's rights review is
    complete.  It never writes to a database and never treats a missing field
    as zero.
    """

    adapter_id = "twse-openapi-financial-snapshot.v1"
    income_url = "https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci"
    balance_url = "https://openapi.twse.com.tw/v1/opendata/t187ap07_L_ci"

    _income_map: ClassVar[dict[str, str]] = {
        "營業收入": "revenue",
        "營業成本": "cost_of_revenue",
        "營業毛利（毛損）": "gross_profit",
        "營業毛利（毛損）淨額": "gross_profit_net",
        "營業費用": "operating_expenses",
        "營業利益（損失）": "operating_income",
        "營業外收入及支出": "non_operating_income",
        "稅前淨利（淨損）": "pretax_income",
        "所得稅費用（利益）": "income_tax",
        "本期淨利（淨損）": "net_income",
        "淨利（淨損）歸屬於母公司業主": "parent_net_income",
        "淨利（淨損）歸屬於非控制權益": "noncontrolling_interest",
        "基本每股盈餘（元）": "basic_eps",
    }
    _balance_map: ClassVar[dict[str, str]] = {
        "流動資產": "current_assets",
        "非流動資產": "non_current_assets",
        "資產總計": "assets",
        "流動負債": "current_liabilities",
        "非流動負債": "non_current_liabilities",
        "負債總計": "liabilities",
        "股本": "share_capital",
        "資本公積": "capital_surplus",
        "保留盈餘": "retained_earnings",
        "其他權益": "other_equity",
        "歸屬於母公司業主之權益合計": "parent_equity",
        "非控制權益": "noncontrolling_interest",
        "權益總計": "equity",
        "每股參考淨值": "book_value_per_share",
    }

    def __init__(self, fetcher: Callable[[str], bytes] | None = None):
        self.fetcher = fetcher

    @staticmethod
    def _decimal(value: object) -> Decimal | None:
        if value is None:
            return None
        text = str(value).strip().replace(",", "")
        if not text or text in {"-", "--", "－", "—"}:
            return None
        try:
            return Decimal(text)
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _roc_year(value: object) -> int | None:
        try:
            year = int(str(value).strip())
        except (TypeError, ValueError):
            return None
        return year + 1911 if year < 1911 else year

    @classmethod
    def _period(cls, row: dict[str, object]) -> tuple[int | None, int | None, date | None, str]:
        year = cls._roc_year(row.get("年度"))
        try:
            quarter = int(str(row.get("季別", "")).strip())
        except (TypeError, ValueError):
            quarter = None
        if year is None or quarter not in {1, 2, 3, 4}:
            return year, quarter, None, "UNKNOWN"
        month = quarter * 3
        if month == 12:
            end = date(year, 12, 31)
        elif month in {3, 6}:
            end = date(year, month, 30)
        else:
            end = date(year, month, 30)
        return year, quarter, end, f"{year}Q{quarter}"

    def _source(self) -> FinancialSource:
        return FinancialSource(
            source_id="SRC-TWSE-OPENAPI-FINANCIAL-SNAPSHOT",
            source_type="TWSE_OPENAPI",
            owner_or_provider="臺灣證券交易所",
            source_url=self.income_url,
            data_usage_rights="TWSE OpenAPI terms; owner review pending",
            redistribution_rights="UNVERIFIED",
            license_review_status="PENDING_REVIEW",
        )

    def _records_for_row(
        self,
        row: dict[str, object],
        ticker: str,
        *,
        statement: str,
        line_map: dict[str, str],
        source_url: str,
    ) -> list[RawFinancialRecord]:
        year, quarter, period_end, period_label = self._period(row)
        if year is None or quarter is None or period_end is None:
            return []
        is_income = statement == "income_statement"
        filing_id = f"TWSE-{ticker}-{year}-Q{quarter}-CONSOLIDATED"
        result: list[RawFinancialRecord] = []
        for original, standard in line_map.items():
            numeric_value = self._decimal(row.get(original))
            if numeric_value is None:
                continue
            result.append(
                RawFinancialRecord(
                    company_id=ticker,
                    ticker=ticker,
                    source_id="SRC-TWSE-OPENAPI-FINANCIAL-SNAPSHOT",
                    filing_id=filing_id,
                    period_end=period_end,
                    period_label=f"{period_label}_YTD" if is_income else period_label,
                    period_type="ytd" if is_income else "quarterly",
                    fiscal_year=year,
                    fiscal_quarter=quarter,
                    statement=statement,
                    line_item_original=original,
                    line_item_standard=standard,
                    numeric_value=numeric_value,
                    unit=(
                        "TWD_PER_SHARE"
                        if "per_share" in standard or standard == "basic_eps"
                        else "TWD_1000"
                    ),
                    currency="TWD",
                    duration_or_instant="DURATION" if is_income else "INSTANT",
                    ytd_or_standalone="YTD" if is_income else "NOT_APPLICABLE",
                    consolidation_scope="consolidated",
                    source_location=f"{source_url}#公司代號={ticker}&期間={period_label}",
                    evidence_label="fact_source_reported",
                    confidence="high",
                )
            )
        return result

    def retrieve(self, ticker: str) -> SourceAdapterResult:
        ticker = ticker.strip()
        if self.fetcher is None:
            return SourceAdapterResult(
                adapter_id=self.adapter_id,
                status="SOURCE_UNAVAILABLE",
                error_reason="TWSE OpenAPI fetcher 未設定; adapter 只允許顯式注入網路來源。",
                live_intake=False,
                rights_checked=False,
            )
        raw_parts: list[bytes] = []
        rows: list[tuple[dict[str, object], str, dict[str, str], str]] = []
        for url, statement, line_map in (
            (self.income_url, "income_statement", self._income_map),
            (self.balance_url, "balance_sheet", self._balance_map),
        ):
            try:
                raw = self.fetcher(url)
                raw_parts.append(raw)
                payload = json.loads(raw.decode("utf-8-sig"))
            except PermissionError as exc:
                return SourceAdapterResult(
                    adapter_id=self.adapter_id,
                    status="ACCESS_DENIED",
                    error_reason=str(exc),
                    live_intake=True,
                    rights_checked=False,
                )
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
                return SourceAdapterResult(
                    adapter_id=self.adapter_id,
                    status="PARSER_FAILED",
                    error_reason=f"{url} 回應不是可解析 JSON: {exc}",
                    live_intake=True,
                    rights_checked=False,
                )
            if not isinstance(payload, list):
                return SourceAdapterResult(
                    adapter_id=self.adapter_id,
                    status="SCHEMA_CHANGED",
                    error_reason=f"{url} 回應不是資料列陣列。",
                    live_intake=True,
                    rights_checked=False,
                )
            row = next(
                (
                    item
                    for item in payload
                    if isinstance(item, dict) and str(item.get("公司代號", "")).strip() == ticker
                ),
                None,
            )
            if row is not None:
                rows.append((row, statement, line_map, url))
        if not rows:
            return SourceAdapterResult(
                adapter_id=self.adapter_id,
                status="EMPTY_RESULT",
                error_reason=f"官方 TWSE OpenAPI 沒有代號 {ticker} 的損益／資產負債快照。",
                live_intake=True,
                rights_checked=True,
            )

        source = self._source()
        year, quarter, period_end, _ = self._period(rows[0][0])
        filing = FinancialFiling(
            filing_id=f"TWSE-{ticker}-{year}-Q{quarter}-CONSOLIDATED",
            company_id=ticker,
            ticker=ticker,
            fiscal_year=year,
            fiscal_quarter=quarter,
            reporting_period_start=date(year, 1, 1) if year else None,
            reporting_period_end=period_end,
            report_type="TWSE_OPENAPI_FINANCIAL_SNAPSHOT",
            consolidation_scope="consolidated",
            source_id=source.source_id,
        )
        records = [
            record
            for row, statement, line_map, source_url in rows
            for record in self._records_for_row(
                row,
                ticker,
                statement=statement,
                line_map=line_map,
                source_url=source_url,
            )
        ]
        return SourceAdapterResult(
            adapter_id=self.adapter_id,
            status="RIGHTS_UNVERIFIED",
            source=source,
            filing=filing,
            raw_artifact_hash=hashlib.sha256(b"".join(raw_parts)).hexdigest(),
            records=records,
            error_reason="官方快照已讀取；公開再分發權利尚未完成 owner review。",
            live_intake=True,
            rights_checked=True,
        )


class _MopsTableParser(HTMLParser):
    """Small dependency-free table parser for the official legacy MOPS HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            text = re.sub(r"\s+", " ", "".join(self._cell).replace("\u3000", " ")).strip()
            self._row.append(text)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None


class MopsLegacyHistoricalAdapter:
    """Parse explicitly fetched official MOPS legacy financial statements.

    The legacy ``mopsov.twse.com.tw`` endpoints return HTML and are therefore
    kept behind an injected fetcher.  This class never performs hidden HTTP,
    never writes a database, and never upgrades source accessibility into
    redistribution permission.  It emits reported values only; cumulative
    values remain YTD and standalone income values are separate records.
    """

    adapter_id = "mops-legacy-html-historical.v1"
    base_url = "https://mopsov.twse.com.tw/mops/web"
    _endpoint_map: ClassVar[dict[str, tuple[str, str]]] = {
        "ajax_t164sb03": ("balance_sheet", "instant"),
        "ajax_t164sb04": ("income_statement", "flow"),
        "ajax_t164sb05": ("cash_flow", "flow"),
        "ajax_t164sb06": ("equity_statement", "flow"),
    }
    _line_map: ClassVar[dict[str, dict[str, str]]] = {
        "balance_sheet": {
            "資產總計": "assets",
        # Some current MOPS tables present the same balance-sheet total as
        # 「負債及權益總計」 rather than a separate 「資產總計」 row.
        "負債及權益總計": "assets",
            "負債總計": "liabilities",
            "權益總計": "equity",
            "歸屬於母公司業主之權益合計": "parent_equity",
            "非控制權益": "noncontrolling_interest",
            "現金及約當現金": "cash_and_equivalents",
            "採用權益法之投資": "equity_method_investments",
            "不動產、廠房及設備": "property_plant_equipment",
            "流動資產合計": "current_assets",
            "非流動資產合計": "non_current_assets",
            "流動負債合計": "current_liabilities",
            "非流動負債合計": "non_current_liabilities",
        },
        "income_statement": {
            "營業收入合計": "revenue",
            "營業成本合計": "cost_of_revenue",
            "營業毛利（毛損）": "gross_profit_reported",
            "營業毛利（毛損）淨額": "gross_profit",
            "營業費用合計": "operating_expenses",
            "營業利益（損失）": "operating_income",
            "營業外收入及支出": "non_operating_income",
            "稅前淨利（淨損）": "pretax_income",
            "所得稅費用（利益）": "income_tax",
        "繼續營業單位本期": "continuing_net_income",
            "本期淨利（淨損）": "net_income",
            "淨利（淨損）歸屬於母公司業主": "parent_net_income",
            "淨利（淨損）歸屬於非控制權益": "noncontrolling_interest",
            "基本每股盈餘": "basic_eps",
            "稀釋每股盈餘": "diluted_eps",
        },
        "cash_flow": {
            "營業活動之淨現金流入（流出）": "cash_from_operations",
            "投資活動之淨現金流入（流出）": "cash_from_investing",
            "籌資活動之淨現金流入（流出）": "cash_from_financing",
            "匯率變動對現金及約當現金之影響": "fx_effect_on_cash",
            "本期現金及約當現金增加（減少）數": "net_change_in_cash",
            "期初現金及約當現金餘額": "cash_at_beginning",
            "期末現金及約當現金餘額": "cash_at_end",
            "資產負債表帳列之現金及約當現金": "cash_per_balance_sheet",
        },
        "equity_statement": {
            "權益總額": "equity",
            "歸屬於母公司業主之權益合計": "parent_equity",
            "非控制權益": "noncontrolling_interest",
            "本期淨利（淨損）": "net_income",
            "發放現金股利": "cash_dividends",
        },
    }

    def __init__(
        self,
        fetcher: Callable[[str, Mapping[str, str]], bytes] | None = None,
    ) -> None:
        self.fetcher = fetcher

    @staticmethod
    def _decode(raw: bytes) -> str:
        try:
            return raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            return raw.decode("big5", errors="replace")

    @staticmethod
    def _roc_date(value: str) -> date | None:
        match = re.search(r"(\d{3,4})年(\d{1,2})月(\d{1,2})日", value)
        if match is None:
            return None
        year = int(match.group(1))
        if year < 1911:
            year += 1911
        return date(year, int(match.group(2)), int(match.group(3)))

    @staticmethod
    def _decimal(value: str) -> Decimal | None:
        text = value.strip().replace(",", "")
        if not text or text in {"-", "--", "－", "—"}:
            return None
        negative = text.startswith("(") and text.endswith(")")
        text = text.strip("()")
        try:
            parsed = Decimal(text)
        except InvalidOperation:
            return None
        return -parsed if negative else parsed

    @classmethod
    def _rows(cls, raw: bytes) -> list[list[str]]:
        parser = _MopsTableParser()
        parser.feed(cls._decode(raw))
        return parser.rows

    @classmethod
    def _amount_positions(cls, rows: list[list[str]]) -> list[int]:
        for row in rows[:20]:
            positions = [
                index
                for index, value in enumerate(row)
                if value in {"金額", "金額(仟元)"}
            ]
            if positions:
                return positions
        return [1]

    @classmethod
    def _period_end(cls, rows: list[list[str]]) -> date | None:
        dates = [cls._roc_date(value) for row in rows[:20] for value in row]
        valid_dates = [value for value in dates if value is not None]
        return max(valid_dates) if valid_dates else None

    @staticmethod
    def _unit(rows: list[list[str]]) -> str:
        header = " ".join(" ".join(row) for row in rows[:12])
        if "每股" in header:
            return "TWD_1000"
        if "百萬元" in header:
            return "TWD_MILLION"
        if "億元" in header:
            return "TWD_100_MILLION"
        return "TWD_1000"

    @classmethod
    def _row_values(
        cls,
        row: list[str],
        amount_positions: list[int],
    ) -> list[tuple[int, Decimal]]:
        values: list[tuple[int, Decimal]] = []
        for position in amount_positions:
            if position >= len(row):
                continue
            value = cls._decimal(row[position])
            if value is not None:
                values.append((position, value))
        return values

    @classmethod
    def _records(
        cls,
        rows: list[list[str]],
        ticker: str,
        roc_year: int,
        quarter: int,
        endpoint: str,
        statement: str,
        mode: str,
        source_id: str,
    ) -> list[RawFinancialRecord]:
        amount_positions = cls._amount_positions(rows)
        period_end = cls._period_end(rows)
        unit = cls._unit(rows)
        line_map = cls._line_map[statement]
        records: list[RawFinancialRecord] = []
        filing_id = f"MOPS-{ticker}-{roc_year + 1911}-Q{quarter}-CONSOLIDATED"
        source_url = f"{cls.base_url}/{endpoint}"
        for row in rows:
            if not row:
                continue
            label = row[0].strip()
            standard = next(
                (
                    canonical
                    for original, canonical in sorted(
                        line_map.items(), key=lambda item: len(item[0]), reverse=True
                    )
                    if original in label
                ),
                None,
            )
            if standard is None:
                continue
            values = cls._row_values(row, amount_positions)
            if not values:
                continue
            first_position, _ = values[0]
            period_specs: list[tuple[str, str, str, int]] = []
            if mode == "instant":
                period_specs.append((
                    f"FY{roc_year + 1911}" if quarter == 4 else f"{roc_year + 1911}Q{quarter}",
                    "annual" if quarter == 4 else "quarterly",
                    "NOT_APPLICABLE",
                    first_position,
                ))
            elif quarter == 4:
                period_specs.append((f"FY{roc_year + 1911}", "annual", "YTD", first_position))
            elif statement in {"cash_flow", "equity_statement"}:
                # MOPS presents cash-flow and statement-of-changes-in-equity
                # amounts cumulatively for interim filings. Do not label them
                # as standalone quarters merely because the endpoint is a
                # flow statement.
                period_specs.append(
                    (f"{roc_year + 1911}Q{quarter}_YTD", "ytd", "YTD", first_position)
                )
            else:
                period_specs.append(
                    (f"{roc_year + 1911}Q{quarter}", "quarterly", "STANDALONE", first_position)
                )
                if len(values) >= 3:
                    ytd_position, _ = values[2]
                    period_specs.append(
                        (f"{roc_year + 1911}Q{quarter}_YTD", "ytd", "YTD", ytd_position)
                    )
            for period_label, period_type, ytd_or_standalone, position in period_specs:
                selected = next((value for column, value in values if column == position), None)
                if selected is None:
                    continue
                records.append(
                    RawFinancialRecord(
                        company_id=ticker,
                        ticker=ticker,
                        source_id=source_id,
                        filing_id=filing_id,
                        period_end=period_end,
                        period_label=period_label,
                        period_type=period_type,
                        fiscal_year=roc_year + 1911,
                        fiscal_quarter=quarter,
                        statement=statement,
                        line_item_original=label,
                        line_item_standard=standard,
                        numeric_value=selected,
                        unit="TWD_PER_SHARE" if "eps" in standard else unit,
                        currency="TWD",
                        duration_or_instant="INSTANT" if mode == "instant" else "DURATION",
                        ytd_or_standalone=ytd_or_standalone,
                        consolidation_scope="consolidated",
                        source_location=(
                            f"{source_url}?co_id={ticker}&year={roc_year}&season={quarter}"
                        ),
                        evidence_label="fact_source_reported",
                        confidence="high",
                    )
                )
        return records

    def retrieve(self, ticker: str, roc_year: int, quarter: int) -> SourceAdapterResult:
        ticker = ticker.strip()
        if self.fetcher is None:
            return SourceAdapterResult(
                adapter_id=self.adapter_id,
                status="SOURCE_UNAVAILABLE",
                error_reason="MOPS legacy fetcher 未設定；只允許顯式注入官方回應。",
                live_intake=False,
                rights_checked=False,
            )
        if not ticker or not 1 <= quarter <= 4:
            return SourceAdapterResult(
                adapter_id=self.adapter_id,
                status="PERIOD_MISMATCH",
                error_reason="ticker 或 quarter 不符合歷史財報查詢格式。",
            )
        source_id = "SRC-MOPS-LEGACY-HTML-T164"
        source = FinancialSource(
            source_id=source_id,
            source_type="MOPS_LEGACY_HTML",
            owner_or_provider="公開資訊觀測站／臺灣證券交易所",
            source_url=f"{self.base_url}/ajax_t164sb04",
            data_usage_rights="官方公開查詢；產品再分發權待 owner review",
            redistribution_rights="UNVERIFIED",
            license_review_status="PENDING_REVIEW",
        )
        all_records: list[RawFinancialRecord] = []
        raw_parts: list[bytes] = []
        errors: list[str] = []
        period_end: date | None = None
        for endpoint, (statement, mode) in self._endpoint_map.items():
            url = f"{self.base_url}/{endpoint}"
            params = {
                "encodeURIComponent": "1",
                "step": "1",
                "firstin": "1",
                "off": "1",
                "co_id": ticker,
                "year": str(roc_year),
                "season": str(quarter),
            }
            try:
                raw = self.fetcher(url, params)
            except PermissionError as exc:
                return SourceAdapterResult(
                    adapter_id=self.adapter_id,
                    status="ACCESS_DENIED",
                    error_reason=str(exc),
                    source=source,
                    live_intake=True,
                )
            raw_parts.append(raw)
            text = self._decode(raw)
            if "FOR SECURITY REASONS" in text or "安全性考量" in text:
                return SourceAdapterResult(
                    adapter_id=self.adapter_id,
                    status="ACCESS_DENIED",
                    error_reason=f"官方端點安全頁阻擋：{url}",
                    source=source,
                    raw_artifact_hash=hashlib.sha256(b"".join(raw_parts)).hexdigest(),
                    live_intake=True,
                    rights_checked=False,
                )
            rows = self._rows(raw)
            statement_records = self._records(
                rows,
                ticker,
                roc_year,
                quarter,
                endpoint,
                statement,
                mode,
                source_id,
            )
            if statement_records:
                all_records.extend(statement_records)
                period_end = period_end or self._period_end(rows)
            else:
                errors.append(f"{statement}=EMPTY_OR_UNMAPPED")
        if not all_records:
            return SourceAdapterResult(
                adapter_id=self.adapter_id,
                status="EMPTY_RESULT",
                error_reason="；".join(errors) or "官方 HTML 沒有可映射財務列。",
                source=source,
                raw_artifact_hash=hashlib.sha256(b"".join(raw_parts)).hexdigest(),
                live_intake=True,
                rights_checked=True,
            )
        filing = FinancialFiling(
            filing_id=f"MOPS-{ticker}-{roc_year + 1911}-Q{quarter}-CONSOLIDATED",
            company_id=ticker,
            ticker=ticker,
            fiscal_year=roc_year + 1911,
            fiscal_quarter=quarter,
            reporting_period_end=period_end,
            report_type="MOPS_LEGACY_HTML_T164",
            consolidation_scope="consolidated",
            raw_artifact_hash=hashlib.sha256(b"".join(raw_parts)).hexdigest(),
            source_id=source_id,
        )
        return SourceAdapterResult(
            adapter_id=self.adapter_id,
            status="RIGHTS_UNVERIFIED",
            source=source,
            filing=filing,
            raw_artifact_hash=filing.raw_artifact_hash,
            records=all_records,
            error_reason="官方歷史 HTML 已解析；再分發權尚未確認。"
            + (f" 部分表別缺漏：{', '.join(errors)}" if errors else ""),
            live_intake=True,
            rights_checked=True,
        )

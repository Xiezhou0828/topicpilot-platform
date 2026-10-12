# ruff: noqa: RUF001

"""Shared, fail-closed ingestion helpers for official EPS notes.

The adapter accepts PDF text/table rows or already structured official rows.
It deliberately does not fetch documents, OCR scans, infer shares from an
EPS value, or turn an issued-share count into a weighted-average count.
Those actions belong to a separately reviewed intake step.  PDF text may split
table headers and values across lines, so the text path includes a generic
table-row pass while retaining the original line as evidence.
"""

from __future__ import annotations

import html
import re
from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256

from .contract import (
    EpsExtractionMethod,
    EpsFieldDataStatus,
    EpsNoteExtractionResult,
    EpsNoteField,
    EpsPeriodContract,
)

PARSER_ID = "eps-note-adapter-v1"

_UNIT_SCALE: dict[str, tuple[Decimal, str, str | None]] = {
    "TWD": (Decimal("1"), "TWD", "TWD"),
    "TWD_1000": (Decimal("1000"), "TWD", "TWD"),
    "TWD_THOUSANDS": (Decimal("1000"), "TWD", "TWD"),
    "千元": (Decimal("1000"), "TWD", "TWD"),
    "SHARES": (Decimal("1"), "SHARES", None),
    "SHARES_1000": (Decimal("1000"), "SHARES", None),
    "千股": (Decimal("1000"), "SHARES", None),
    "仟股": (Decimal("1000"), "SHARES", None),
    "TWD_PER_SHARE": (Decimal("1"), "TWD_PER_SHARE", "TWD"),
    "元/股": (Decimal("1"), "TWD_PER_SHARE", "TWD"),
}

_FIELD_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "weighted_average_diluted_shares",
        (
            r"稀釋(?:效果後)?之普通股加權平均(?:流通在外)?股數",
            r"weighted\s+average\s+(?:common\s+)?shares.*dilut",
        ),
    ),
    (
        "weighted_average_basic_shares",
        (
            r"基本每股盈餘(?:之)?普通股加權平均(?:流通在外)?股數",
            r"weighted\s+average\s+(?:common\s+)?shares.*basic",
        ),
    ),
    (
        "diluted_eps",
        (r"稀釋每股盈餘", r"diluted\s+earnings\s+per\s+share", r"diluted\s+eps"),
    ),
    (
        "basic_eps",
        (r"基本每股盈餘", r"basic\s+earnings\s+per\s+share", r"basic\s+eps"),
    ),
    (
        "parent_net_income",
        (
            r"歸屬於母公司普通股持有人之淨利",
            r"歸屬於母公司業主之淨利",
            r"歸屬於母公司股東之淨利",
            r"net\s+income\s+attributable\s+to\s+owners\s+of\s+parent",
            r"profit\s+attributable\s+to\s+owners\s+of\s+parent",
        ),
    ),
)

_NUMBER_RE = re.compile(
    r"(?:\(\s*\$?\s*[\d,]+(?:\.\d+)?\s*\)|[-+]?\s*\$?\s*\d[\d,]*(?:\.\d+)?)"
)
_PAGE_RE = re.compile(
    r"(?:page|頁)\s*[:：]?\s*(\d+)|第\s*(\d+)\s*頁", re.IGNORECASE
)
_DATE_RE = re.compile(
    r"(?P<year>\d{2,4})\s*[./年-]\s*(?P<month>\d{1,2})\s*[./月-]\s*(?P<day>\d{1,2})"
)


def _clean_text(value: object) -> str:
    text = html.unescape(str(value or "")).replace("　", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_number(value: object) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int | float):
        return Decimal(str(value))
    text = _clean_text(value)
    match = _NUMBER_RE.search(text)
    if not match:
        return None
    token = match.group(0).replace(",", "").replace(" ", "").replace("$", "")
    negative = token.startswith("(") and token.endswith(")")
    token = token.strip("()")
    try:
        number = Decimal(token)
    except InvalidOperation:
        return None
    return -number if negative else number


def _unit_info(unit: str | None, line: str) -> tuple[str, Decimal, str, str | None]:
    source_unit = (unit or "").strip()
    if not source_unit:
        if "股" in line or "share" in line.lower():
            source_unit = "SHARES_1000" if any(
                token in line for token in ("千股", "仟股", "thousand")
            ) else "SHARES"
        elif "每股" in line or "per share" in line.lower() or "eps" in line.lower():
            source_unit = "TWD_PER_SHARE"
        else:
            source_unit = (
                "TWD_1000"
                if "仟元" in line or "千元" in line or "thousand" in line.lower()
                else "TWD"
            )
    scale, normalized_unit, currency = _UNIT_SCALE.get(
        source_unit, (Decimal("1"), source_unit, None)
    )
    return source_unit, scale, normalized_unit, currency


def _parse_year(raw: int) -> int:
    return raw + 1911 if raw < 1911 else raw


def _parse_date(value: str | date | None) -> date | None:
    if value is None or isinstance(value, date):
        return value
    match = _DATE_RE.search(value.replace("民國", ""))
    if not match:
        return None
    return date(
        _parse_year(int(match.group("year"))), int(match.group("month")), int(match.group("day"))
    )


def normalize_period_contract(
    *,
    period_label: str,
    period_start: str | date | None = None,
    period_end: str | date | None = None,
    period_type: str | None = None,
    fiscal_year: int | None = None,
    fiscal_quarter: int | None = None,
    ytd_or_standalone: str | None = None,
    comparative_of: str | None = None,
    retrospective_adjustment: str | None = None,
) -> EpsPeriodContract:
    """Normalize common annual, quarterly, half-year and nine-month labels."""

    label = period_label.strip()
    upper = label.upper().replace("-", "_").replace(" ", "")
    parsed_year = fiscal_year
    if parsed_year is None:
        year_match = re.search(r"(?:FY|Q|H|9M|Y)?(\d{4})", upper)
        if year_match:
            parsed_year = int(year_match.group(1))
    if parsed_year is None:
        roc_match = re.search(r"(?:FY|Q|H|9M|Y)?(\d{2,3})", upper)
        if roc_match:
            parsed_year = _parse_year(int(roc_match.group(1)))

    quarter = fiscal_quarter
    if quarter is None:
        quarter_match = re.search(r"Q([1-4])", upper)
        quarter = int(quarter_match.group(1)) if quarter_match else None

    normalized_type = period_type
    if normalized_type is None:
        if upper.startswith("FY") or re.search(r"年度$", label):
            normalized_type = "annual"
        elif upper.startswith("H1") or "半年" in label:
            normalized_type = "half_year"
        elif upper.startswith("9M") or "九個月" in label:
            normalized_type = "nine_month"
        elif "Q" in upper or "季度" in label:
            normalized_type = "quarterly"
        else:
            normalized_type = "ytd"
    if normalized_type not in {"annual", "quarterly", "half_year", "nine_month", "ytd"}:
        raise ValueError(f"unsupported EPS period type: {normalized_type}")

    normalized_ytd = ytd_or_standalone
    if normalized_ytd is None:
        normalized_ytd = "STANDALONE" if "STANDALONE" in upper else "YTD"
        if normalized_type == "annual":
            normalized_ytd = "NOT_APPLICABLE"
    if normalized_ytd not in {"YTD", "STANDALONE", "NOT_APPLICABLE"}:
        raise ValueError(f"unsupported EPS duration flag: {normalized_ytd}")
    return EpsPeriodContract(
        period_label=label,
        period_start=_parse_date(period_start),
        period_end=_parse_date(period_end),
        period_type=normalized_type,
        fiscal_year=parsed_year,
        fiscal_quarter=quarter,
        ytd_or_standalone=normalized_ytd,
        comparative_of=comparative_of,
        retrospective_adjustment=retrospective_adjustment,
    )


def _field_from_value(
    *,
    ticker: str,
    period: EpsPeriodContract,
    line_item: str,
    value: object,
    source_id: str,
    source_url: str | None,
    source_page: str | None,
    raw_field: str,
    raw_text: str,
    source_unit: str | None,
    extraction_method: EpsExtractionMethod,
    data_status: EpsFieldDataStatus = "DIRECT",
) -> EpsNoteField | None:
    parsed = _parse_number(value)
    if parsed is None:
        return None
    resolved_unit, scale, normalized_unit, currency = _unit_info(
        source_unit, f"{raw_field} {raw_text}"
    )
    return EpsNoteField(
        ticker=ticker,
        period=period,
        line_item_standard=line_item,
        value=parsed,
        source_value=parsed,
        source_unit=resolved_unit,
        normalized_value=parsed * scale,
        normalized_unit=normalized_unit,
        currency=currency,
        source_id=source_id,
        source_url=source_url,
        source_page=source_page,
        raw_field=raw_field,
        raw_text=raw_text,
        extraction_method=extraction_method,
        data_status=data_status,
    )


def _matching_line_item(text: str) -> str | None:
    for line_item, patterns in _FIELD_PATTERNS:
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
            return line_item
    return None


def parse_eps_note_text(
    text: str | None,
    *,
    ticker: str,
    source_id: str,
    source_url: str | None,
    period: EpsPeriodContract,
    source_page: str | None = None,
    extraction_method: EpsExtractionMethod = "PDF_TEXT",
) -> EpsNoteExtractionResult:
    """Parse text extracted from an official EPS note without OCR guessing."""

    if not text:
        return EpsNoteExtractionResult(
            ticker=ticker,
            source_id=source_id,
            source_url=source_url,
            status="SOURCE_UNAVAILABLE",
            parser_id=PARSER_ID,
            periods=[period],
            limitations=["來源文字未提供；掃描影像不得以臆測替代。"],
        )
    fields: list[EpsNoteField] = []
    seen: set[str] = set()
    lines = re.split(r"[\r\n]+", html.unescape(text))

    def append_field(
        *,
        line_item: str,
        value: object,
        raw_text: str,
        page: str | None,
        source_unit: str | None,
    ) -> None:
        if line_item in seen:
            return
        field = _field_from_value(
            ticker=ticker,
            period=period,
            line_item=line_item,
            value=value,
            source_id=source_id,
            source_url=source_url,
            source_page=page,
            raw_field=line_item,
            raw_text=raw_text,
            source_unit=source_unit,
            extraction_method=extraction_method,
        )
        if field is not None:
            fields.append(field)
            seen.add(line_item)

    def context_has_thousands(index: int) -> bool:
        context = " ".join(_clean_text(item) for item in lines[max(0, index - 12) : index + 1])
        return any(
            token in context.lower()
            for token in ("千元", "仟元", "千股", "仟股", "thousand", "in thousands")
        )

    current_page = source_page
    for index, raw_line in enumerate(lines):
        line = _clean_text(raw_line)
        if not line:
            continue
        page_match = _PAGE_RE.search(line)
        if page_match:
            current_page = f"p.{page_match.group(1) or page_match.group(2)}"
        line_item = _matching_line_item(line)
        if line_item is None or line_item in seen:
            continue
        numeric = _NUMBER_RE.search(line)
        if numeric is None:
            continue
        page = current_page
        unit = None
        if line_item.endswith("shares"):
            unit = "SHARES_1000" if context_has_thousands(index) else "SHARES"
        elif line_item.endswith("eps"):
            unit = "TWD_PER_SHARE"
        elif line_item == "parent_net_income":
            # Do not infer a currency unit from the word ``shareholders``.
            unit = "TWD_1000" if context_has_thousands(index) else "TWD"
        append_field(
            line_item=line_item,
            value=numeric.group(0),
            raw_text=line,
            page=page,
            source_unit=unit,
        )

    # Many issuer PDFs put the table heading on one line and the numeric row
    # several lines later.  Parse only explicit EPS table rows; never derive a
    # share count from EPS or from an issued-share balance.
    table_section: str | None = None
    table_page = source_page
    table_share_unit = "SHARES_1000" if context_has_thousands(0) else "SHARES"
    pending_parent_row = False
    for index, raw_line in enumerate(lines):
        line = _clean_text(raw_line)
        if not line:
            continue
        if any(
            token in line.lower()
            for token in ("千股", "仟股", "in thousands", "thousand")
        ):
            table_share_unit = "SHARES_1000"
        page_match = _PAGE_RE.search(line)
        if page_match:
            table_page = f"p.{page_match.group(1) or page_match.group(2)}"
        page = table_page
        if re.search(r"基本每股盈餘|basic\s+earnings\s+per\s+share|basic\s+eps", line, re.I):
            table_section = "basic"
            pending_parent_row = False
            continue
        if re.search(r"稀釋每股盈餘|diluted\s+earnings\s+per\s+share|diluted\s+eps", line, re.I):
            table_section = "diluted"
            pending_parent_row = False
            continue
        if re.search(r"(?:第\s*\d+\s*節|changes in liabilities|融資活動負債)", line, re.I):
            table_section = None
            pending_parent_row = False
            continue
        if table_section is None:
            continue
        numbers = [match.group(0) for match in _NUMBER_RE.finditer(line)]
        if re.search(r"繼續營業單位|continuing\s+operations", line, re.I) and len(numbers) >= 3:
            # EPS note row order is amount-after-tax, weighted shares, EPS.
            append_field(
                line_item=(
                    "weighted_average_basic_shares"
                    if table_section == "basic"
                    else "weighted_average_diluted_shares"
                ),
                value=numbers[1],
                raw_text=line,
                page=page,
                source_unit=table_share_unit,
            )
            append_field(
                line_item="basic_eps" if table_section == "basic" else "diluted_eps",
                value=numbers[-1],
                raw_text=line,
                page=page,
                source_unit="TWD_PER_SHARE",
            )
        has_parent_label = bool(
            re.search(r"歸屬於母公司|parent\s+company|ordinary\s+shareholders", line, re.I)
        )
        if table_section == "basic" and has_parent_label:
            pending_parent_row = True
        if table_section == "basic" and (has_parent_label or pending_parent_row) and numbers:
            append_field(
                    line_item="parent_net_income",
                    value=numbers[0],
                    raw_text=line,
                    page=page,
                    source_unit="TWD_1000" if context_has_thousands(index) else "TWD",
                )
            if len(numbers) >= 2:
                append_field(
                    line_item="basic_eps",
                    value=numbers[-1],
                    raw_text=line,
                    page=page,
                    source_unit="TWD_PER_SHARE",
                )
                pending_parent_row = False
    status = "EXTRACTED" if fields else "NO_EPS_NOTE"
    limitations = [] if fields else ["文字內容未找到可驗證的 EPS 附註欄位。"]
    return EpsNoteExtractionResult(
        ticker=ticker,
        source_id=source_id,
        source_url=source_url,
        status=status,
        parser_id=PARSER_ID,
        periods=[period],
        fields=fields,
        limitations=limitations,
        raw_artifact_hash=sha256(text.encode("utf-8")).hexdigest(),
    )


def parse_eps_note_rows(
    rows: Iterable[Mapping[str, object]],
    *,
    ticker: str,
    source_id: str,
    source_url: str | None,
    period: EpsPeriodContract,
    extraction_method: EpsExtractionMethod = "PDF_TABLE",
) -> EpsNoteExtractionResult:
    """Parse normalized PDF-table or structured rows using the same field map."""

    fields: list[EpsNoteField] = []
    for row in rows:
        raw_field = _clean_text(row.get("line_item") or row.get("label") or row.get("field"))
        line_item = _matching_line_item(raw_field)
        if line_item is None:
            canonical = str(row.get("line_item_standard") or raw_field).strip()
            line_item = canonical or None
            raw_field = raw_field or canonical
        if line_item is None:
            continue
        raw_text = _clean_text(row.get("raw_text") or raw_field)
        field = _field_from_value(
            ticker=ticker,
            period=period,
            line_item=line_item,
            value=row.get("value"),
            source_id=source_id,
            source_url=source_url,
            source_page=_clean_text(row.get("page")) or None,
            raw_field=raw_field,
            raw_text=raw_text,
            source_unit=_clean_text(row.get("unit")) or None,
            extraction_method=extraction_method,
            data_status=str(row.get("data_status") or "DIRECT"),
        )
        if field is not None:
            fields.append(field)
    status = "EXTRACTED" if fields else "NO_EPS_NOTE"
    return EpsNoteExtractionResult(
        ticker=ticker,
        source_id=source_id,
        source_url=source_url,
        status=status,
        parser_id=PARSER_ID,
        periods=[period],
        fields=fields,
        limitations=[] if fields else ["表格／結構化資料沒有可驗證的 EPS 附註列。"],
    )


def derive_standalone_flow_fields(
    current: EpsNoteField, previous: EpsNoteField
) -> EpsNoteField | None:
    """Derive a standalone flow value from same-year YTD values only.

    Weighted-average shares are intentionally excluded.  Their derivation
    requires dated share-change events and therefore remains pending review.
    """

    if current.line_item_standard != previous.line_item_standard:
        return None
    if current.line_item_standard.endswith("shares"):
        return None
    if current.period.ytd_or_standalone != "YTD" or previous.period.ytd_or_standalone != "YTD":
        return None
    if current.period.fiscal_year != previous.period.fiscal_year:
        return None
    if current.period.fiscal_quarter is None or previous.period.fiscal_quarter is None:
        return None
    if current.period.fiscal_quarter != previous.period.fiscal_quarter + 1:
        return None
    period = normalize_period_contract(
        period_label=f"{current.period.fiscal_year}Q{current.period.fiscal_quarter}_STANDALONE",
        period_end=current.period.period_end,
        period_type="quarterly",
        fiscal_year=current.period.fiscal_year,
        fiscal_quarter=current.period.fiscal_quarter,
        ytd_or_standalone="STANDALONE",
    )
    value = current.normalized_value - previous.normalized_value
    return current.model_copy(
        update={
            "period": period,
            "value": value,
            "source_value": value,
            "source_unit": current.normalized_unit,
            "normalized_value": value,
            "normalized_unit": current.normalized_unit,
            "data_status": "DERIVED",
            "raw_field": current.raw_field,
            "raw_text": f"{current.raw_text} − {previous.raw_text}（同口徑 YTD 差分）",
        }
    )


def mark_weighted_shares_pending_validation(fields: Iterable[EpsNoteField]) -> list[EpsNoteField]:
    """Keep share fields visible while preventing them from being used as facts."""

    return [
        field.model_copy(update={"data_status": "PENDING_VALIDATION"})
        for field in fields
        if field.line_item_standard.endswith("shares")
    ]


__all__ = [
    "PARSER_ID",
    "derive_standalone_flow_fields",
    "mark_weighted_shares_pending_validation",
    "normalize_period_contract",
    "parse_eps_note_rows",
    "parse_eps_note_text",
]

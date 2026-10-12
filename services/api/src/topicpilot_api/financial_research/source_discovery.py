"""Fail-closed classification gates for official financial documents.

The gate distinguishes an issuer's material announcement from the full report
that contains the EPS note.  URL and filename are provenance hints only; the
document title, statements, notes, consolidation scope and period evidence
are required for an upgrade.
"""

# User-facing Chinese provenance strings intentionally use full-width punctuation.
# ruff: noqa: RUF001

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import urlparse

DocumentType = Literal[
    "MATERIAL_ANNOUNCEMENT",
    "FULL_FINANCIAL_STATEMENT",
    "EPS_DISCLOSURE_NOTE",
    "ANNUAL_REPORT",
    "INVESTOR_PRESENTATION",
    "OTHER_OFFICIAL_DOCUMENT",
]

SourceDiscoveryStatus = Literal[
    "PASS",
    "OFFICIAL_SOURCE_NOT_FOUND",
    "OFFICIAL_SOURCE_ACCESS_BLOCKED",
    "WRONG_DOCUMENT_TYPE",
    "FULL_REPORT_FOUND_NOTE_NOT_LOCATED",
    "NOTE_FOUND_PARSE_FAILED",
    "PERIOD_MAPPING_FAILED",
    "UNIT_NORMALIZATION_FAILED",
    "EPS_BRIDGE_MISMATCH",
    "OFFICIAL_DISCLOSURE_NOT_YET_AVAILABLE",
]


_OFFICIAL_HOSTS = {
    "doc.twse.com.tw",
    "mops.twse.com.tw",
    "mopsov.twse.com.tw",
    "twse.com.tw",
}
_MATERIAL_MARKERS = (
    "重大訊息",
    "公告本公司董事會決議通過",
    "財務報告或年度自結財務資訊報導期間",
    "material information",
)
_FULL_REPORT_MARKERS = (
    "合併財務報告",
    "合併財務季報告",
    "ifrss合併財報",
    "consolidated financial statements",
    "consolidated interim financial statements",
)
_STATEMENT_MARKERS = (
    "合併資產負債表",
    "合併綜合損益表",
    "合併現金流量表",
    "consolidated balance sheets",
    "consolidated statements of comprehensive income",
    "consolidated statements of cash flows",
)
_EPS_MARKERS = (
    "每股盈餘",
    "每股損失",
    "earnings per share",
    "loss per share",
)
_SHARE_MARKERS = (
    "加權平均",
    "流通在外股數",
    "weighted average",
    "ordinary shares outstanding",
)
_ANNUAL_MARKERS = ("股東會年報", "年報", "annual report")
_PRESENTATION_MARKERS = ("法說會", "法人說明會", "investor presentation", "earnings presentation")


@dataclass(frozen=True)
class DocumentClassification:
    """Evidence-based document classification, separate from retrieval."""

    document_type: DocumentType
    official_source: bool
    is_full_financial_statement: bool
    is_consolidated: bool | None
    has_eps_note: bool
    has_weighted_average_shares: bool
    period_evidence: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceGateDecision:
    status: SourceDiscoveryStatus
    classification: DocumentClassification
    reasons: tuple[str, ...] = field(default_factory=tuple)


def _normalized(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").replace("　", " ")).strip().lower()


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker.lower() in text for marker in markers)


def _official_source(url: str | None, declared_official: bool | None) -> bool:
    if declared_official is not None:
        return declared_official
    host = (urlparse(url or "").hostname or "").lower()
    return host in _OFFICIAL_HOSTS or host.endswith(".gov.tw")


def _period_evidence(text: str) -> tuple[str, ...]:
    patterns = (
        r"(?:民國|民国)?\s*\d{2,3}\s*年\s*(?:第\s*)?[一二三四1-4]\s*季",
        r"\b20\d{2}\s*(?:q[1-4]|h1|q[1-4]\s*ytd)\b",
        r"(?:march|june|september|december)\s+31,?\s+20\d{2}",
    )
    found: list[str] = []
    for pattern in patterns:
        found.extend(match.group(0) for match in re.finditer(pattern, text, re.I))
    for match in re.finditer(
        r"\b(january|march|june|september|december)\s+\d{1,2},?\s+(20\d{2})\b",
        text,
        re.I,
    ):
        month = match.group(1).lower()
        quarter = {"january": 1, "march": 1, "june": 2, "september": 3, "december": 4}[month]
        found.append(f"{match.group(2)}Q{quarter}")
    return tuple(dict.fromkeys(found))


def classify_financial_document(
    *,
    text: str,
    title: str | None = None,
    filename: str | None = None,
    source_url: str | None = None,
    declared_official: bool | None = None,
) -> DocumentClassification:
    """Classify a candidate using document content, not its filename alone."""

    content = _normalized(" ".join(value for value in (title, filename, text) if value))
    official = _official_source(source_url, declared_official)
    has_full_markers = _contains_any(content, _FULL_REPORT_MARKERS)
    has_statement_markers = _contains_any(content, _STATEMENT_MARKERS)
    has_eps_note = _contains_any(content, _EPS_MARKERS)
    has_shares = has_eps_note and _contains_any(content, _SHARE_MARKERS)
    is_consolidated = (
        True
        if _contains_any(content, ("合併", "consolidated"))
        else False
        if _contains_any(content, ("個別", "個體", "separate financial statements"))
        else None
    )

    if _contains_any(content, _PRESENTATION_MARKERS):
        document_type: DocumentType = "INVESTOR_PRESENTATION"
    elif _contains_any(content, _ANNUAL_MARKERS) and not has_full_markers:
        document_type = "ANNUAL_REPORT"
    elif _contains_any(content, _MATERIAL_MARKERS) and not has_statement_markers:
        document_type = "MATERIAL_ANNOUNCEMENT"
    elif has_statement_markers or has_full_markers:
        document_type = "FULL_FINANCIAL_STATEMENT"
    elif has_eps_note and has_shares:
        document_type = "EPS_DISCLOSURE_NOTE"
    elif _contains_any(content, _MATERIAL_MARKERS):
        document_type = "MATERIAL_ANNOUNCEMENT"
    else:
        document_type = "OTHER_OFFICIAL_DOCUMENT"

    reasons = [f"文件類型由內容訊號判定：{document_type}"]
    if has_full_markers and not has_statement_markers:
        reasons.append("包含完整財報標題，但尚未看到主表標記")
    if has_eps_note:
        reasons.append("找到 EPS 附註關鍵字")
    if has_shares:
        reasons.append("找到加權平均股數／流通在外股數關鍵字")
    limitations: list[str] = []
    if not official:
        limitations.append("來源尚未證明為官方來源")
    if document_type == "MATERIAL_ANNOUNCEMENT":
        limitations.append("重大訊息公告不能取代完整財報 EPS 附註")

    return DocumentClassification(
        document_type=document_type,
        official_source=official,
        is_full_financial_statement=(document_type == "FULL_FINANCIAL_STATEMENT"),
        is_consolidated=is_consolidated,
        has_eps_note=has_eps_note,
        has_weighted_average_shares=has_shares,
        period_evidence=_period_evidence(content),
        reasons=tuple(reasons),
        limitations=tuple(limitations),
    )


def validate_source_gate(
    classification: DocumentClassification,
    *,
    expected_period: str | None = None,
    expected_consolidated: bool = True,
    require_eps_note: bool = True,
    require_weighted_average_shares: bool = True,
    parse_failed: bool = False,
    unit_normalization_failed: bool = False,
    bridge_mismatch: bool = False,
    disclosure_not_yet_available: bool = False,
) -> SourceGateDecision:
    """Return the narrowest fail-closed status for a source candidate."""

    if disclosure_not_yet_available:
        status: SourceDiscoveryStatus = "OFFICIAL_DISCLOSURE_NOT_YET_AVAILABLE"
        return SourceGateDecision(status, classification, ("官方申報尚未提供可核驗原件",))
    if not classification.official_source:
        status = "OFFICIAL_SOURCE_NOT_FOUND"
        return SourceGateDecision(status, classification, ("未確認官方來源",))
    if classification.document_type == "MATERIAL_ANNOUNCEMENT":
        return SourceGateDecision(
            "WRONG_DOCUMENT_TYPE",
            classification,
            ("候選文件是重大訊息公告，不是完整財報",),
        )
    if not classification.is_full_financial_statement:
        return SourceGateDecision(
            "WRONG_DOCUMENT_TYPE",
            classification,
            ("候選文件沒有通過完整合併財報文件類型 Gate",),
        )
    if expected_consolidated and classification.is_consolidated is not True:
        return SourceGateDecision(
            "WRONG_DOCUMENT_TYPE",
            classification,
            ("未確認為合併財報",),
        )
    if expected_period:
        expected = re.sub(r"\s+", "", expected_period.lower())
        period_matches = any(
            expected in re.sub(r"\s+", "", item.lower())
            for item in classification.period_evidence
        )
    else:
        period_matches = True
    if expected_period and not period_matches:
        return SourceGateDecision(
            "PERIOD_MAPPING_FAILED",
            classification,
            (f"文件期間證據未對應 {expected_period}",),
        )
    if require_eps_note and not classification.has_eps_note:
        return SourceGateDecision(
            "FULL_REPORT_FOUND_NOTE_NOT_LOCATED",
            classification,
            ("已找到完整財報，但尚未定位 EPS 附註",),
        )
    if parse_failed:
        return SourceGateDecision(
            "NOTE_FOUND_PARSE_FAILED",
            classification,
            ("已定位 EPS 附註，但解析失敗；不得升級股數資料",),
        )
    if require_weighted_average_shares and not classification.has_weighted_average_shares:
        return SourceGateDecision(
            "FULL_REPORT_FOUND_NOTE_NOT_LOCATED",
            classification,
            ("已找到 EPS 附註，但未定位同期間加權平均股數欄位",),
        )
    if unit_normalization_failed:
        return SourceGateDecision(
            "UNIT_NORMALIZATION_FAILED",
            classification,
            ("股數單位尚未能安全正規化",),
        )
    if bridge_mismatch:
        return SourceGateDecision(
            "EPS_BRIDGE_MISMATCH",
            classification,
            ("股數與損益可取得，但重算 EPS 與公告值不一致",),
        )
    return SourceGateDecision(
        "PASS",
        classification,
        ("來源、文件類型、期間與 EPS 股數 Gate 通過",),
    )


__all__ = [
    "DocumentClassification",
    "SourceDiscoveryStatus",
    "SourceGateDecision",
    "classify_financial_document",
    "validate_source_gate",
]

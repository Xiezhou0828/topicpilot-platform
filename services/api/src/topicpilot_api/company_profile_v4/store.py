from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .contract import CompanyResearchV4PublicResponse


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _number(value: Any) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return value


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _approval_content_sha256(package: dict[str, Any]) -> str:
    content = deepcopy(package)
    frontend = content.get("frontendProjection")
    governance = frontend.get("researchGovernance") if isinstance(frontend, dict) else None
    publication = governance.get("publication") if isinstance(governance, dict) else None
    if isinstance(publication, dict):
        publication.pop("approvalEvidence", None)
    canonical = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _metric(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    result = {
        "value": _number(value.get("value")),
        "unit": _text(value.get("unit")),
        "period": _text(value.get("period")),
        "statusNote": _text(value.get("statusNote")),
    }
    if "share" in value:
        result["share"] = _number(value.get("share"))
    return result


def _themes(value: Any) -> list[dict[str, Any]]:
    rows = []
    for item in _list(value):
        if not isinstance(item, dict) or not _text(item.get("themeTitle")):
            continue
        projected = {
            "themeTitle": _text(item.get("themeTitle")),
            "timeHorizon": _text(item.get("timeHorizon")),
            "impactLevel": _text(item.get("impactLevel")),
            "probability": _text(item.get("probability")),
        }
        for side in ("opportunity", "risk"):
            content = item.get(side)
            if isinstance(content, dict):
                projected[side] = {
                    "summary": _text(content.get("summary")),
                    "metrics": _strings(content.get("metrics")),
                }
        pricing = item.get("pricingPower")
        if isinstance(pricing, dict):
            projected["pricingPower"] = {
                key: _text(pricing.get(key))
                for key in ("assessment", "costPassThrough", "spreadRisk")
            }
        rows.append(projected)
    return rows


def _operating_matrix(value: Any) -> list[dict[str, Any]]:
    rows = []
    for item in _list(value):
        if not isinstance(item, dict) or not _text(item.get("name")):
            continue
        projected: dict[str, Any] = {"name": _text(item.get("name"))}
        for key in ("revenue", "profit"):
            metric = _metric(item.get(key))
            if metric is not None:
                projected[key] = metric
        products = []
        for product in _list(item.get("products")):
            if isinstance(product, str) and product.strip():
                products.append({"name": product.strip()})
            elif isinstance(product, dict) and _text(product.get("name")):
                products.append(
                    {
                        "name": _text(product.get("name")),
                        "lifecycle": _text(product.get("lifecycle")),
                        "specification": _text(product.get("specification")),
                        "generation": _text(product.get("generation")),
                        "qualificationStatus": _text(product.get("qualificationStatus")),
                        "contributionTimeline": _text(product.get("contributionTimeline")),
                        "applications": _strings(product.get("applications")),
                    }
                )
        if "products" in item:
            projected["products"] = products
        projected["applications"] = _strings(item.get("applications"))
        links = []
        for link in _list(item.get("investmentLinks")):
            if isinstance(link, dict) and _text(link.get("name")):
                links.append(
                    {
                        "name": _text(link.get("name")),
                        "relationshipType": _text(link.get("relationshipType")),
                        "financialImpact": _text(link.get("financialImpact")),
                        "strategicImpact": _text(link.get("strategicImpact")),
                        "holdingPercent": _number(link.get("holdingPercent")),
                    }
                )
        if "investmentLinks" in item:
            projected["investmentLinks"] = links
        rows.append(projected)
    return rows


def _finance(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    result: dict[str, Any] = {}
    forecast = value.get("forecast")
    if isinstance(forecast, dict):
        result["forecast"] = {
            "forwardEps": _number(forecast.get("forwardEps")),
            "unit": _text(forecast.get("unit")),
            "epsTrend": _text(forecast.get("epsTrend")),
            "forecastStatus": _text(forecast.get("forecastStatus")),
            "modelMethod": _text(forecast.get("modelMethod")),
            "statusNote": _text(forecast.get("statusNote")),
            "quarterlyEps": [
                {
                    key: _number(item.get(key)) if key == "value" else _text(item.get(key))
                    for key in ("periodKey", "value", "unit", "statusNote")
                }
                for item in _list(forecast.get("quarterlyEps"))
                if isinstance(item, dict)
            ],
            "assumptions": [
                {
                    key: _number(item.get(key)) if key == "value" else _text(item.get(key))
                    for key in ("label", "value", "unit", "statusNote")
                }
                for item in _list(forecast.get("assumptions"))
                if isinstance(item, dict)
            ],
        }
    valuation = value.get("valuation")
    if isinstance(valuation, dict):
        bands = valuation.get("peBands") if isinstance(valuation.get("peBands"), dict) else {}
        result["valuation"] = {
            "valuationMethod": _text(valuation.get("valuationMethod")),
            "currentPrice": _number(valuation.get("currentPrice")),
            "valuationStatus": _text(valuation.get("valuationStatus")),
            "valuationDisplay": _text(valuation.get("valuationDisplay")),
            "peBands": {key: _number(bands.get(key)) for key in ("cheap", "fair", "expensive")},
            "statusNote": _text(valuation.get("statusNote")),
        }
    historical = value.get("historicalTable")
    if isinstance(historical, dict):
        result["historicalTable"] = {
            "unitNote": _text(historical.get("unitNote")),
            "headers": [
                {"key": _text(item.get("key")), "label": _text(item.get("label"))}
                for item in _list(historical.get("headers"))
                if isinstance(item, dict)
            ],
            "rows": [
                {
                    "metricKey": _text(item.get("metricKey")),
                    "label": _text(item.get("label")),
                    "unit": _text(item.get("unit")),
                    "isAdjusted": item.get("isAdjusted") is True,
                    "adjustmentNote": _text(item.get("adjustmentNote")),
                    "statusNote": _text(item.get("statusNote")),
                    "values": {
                        key: _number((item.get("values") or {}).get(key))
                        if isinstance(item.get("values"), dict)
                        else None
                        for key in ("current_q", "previous_q", "prior_year")
                    },
                }
                for item in _list(historical.get("rows"))
                if isinstance(item, dict)
            ],
        }
    segment = value.get("segmentPerformanceTable")
    if isinstance(segment, dict):
        result["segmentPerformanceTable"] = {
            "period": _text(segment.get("period")),
            "basis": _text(segment.get("basis")),
            "statusNote": _text(segment.get("statusNote")),
            "rows": [
                {
                    "segmentName": _text(item.get("segmentName")),
                    "metricValue": _number(item.get("metricValue")),
                    "unit": _text(item.get("unit")),
                    "isNegative": item.get("isNegative") is True,
                    "statusNote": _text(item.get("statusNote")),
                }
                for item in _list(segment.get("rows"))
                if isinstance(item, dict) and _text(item.get("segmentName"))
            ],
        }
    return result


def _project_published(package: dict[str, Any]) -> CompanyResearchV4PublicResponse:
    frontend = package["frontendProjection"]
    governance = frontend.get("researchGovernance")
    governance = governance if isinstance(governance, dict) else {}
    metadata = package.get("researchMetadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    overview = package.get("overviewData")
    overview = overview if isinstance(overview, dict) else {}
    overview_data = {
        key: {"shortDesc": _text(overview[key].get("shortDesc"))}
        for key in ("businessModel", "coreBusiness", "mainProducts", "industryRole")
        if isinstance(overview.get(key), dict) and _text(overview[key].get("shortDesc"))
    }
    sections = package.get("sections")
    sections = sections if isinstance(sections, dict) else {}
    public_sections: dict[str, Any] = {}
    summary_keys = (
        "companyAndBusiness",
        "customersAndChannels",
        "competitionAndPosition",
        "capacityAndSupply",
        "financialPerformance",
        "contractsAndBacklog",
    )
    for key in summary_keys:
        section = sections.get(key)
        if isinstance(section, dict) and _text(section.get("summary")):
            public_sections[key] = {"summary": _text(section.get("summary"))}
        if isinstance(section, dict) and key == "customersAndChannels":
            concentration = section.get("customerConcentration")
            if isinstance(concentration, dict):
                public_sections.setdefault(key, {})["customerConcentration"] = {
                    "period": _text(concentration.get("period")),
                    "largestCustomerRevenueShare": _number(
                        concentration.get("largestCustomerRevenueShare")
                    ),
                    "unit": _text(concentration.get("unit")),
                    "statusNote": _text(concentration.get("statusNote")),
                }
        if isinstance(section, dict) and key == "financialPerformance":
            snapshot = section.get("annualSnapshot")
            if isinstance(snapshot, dict):
                public_sections.setdefault(key, {})["annualSnapshot"] = {
                    field: _number(snapshot.get(field))
                    for field in (
                        "revenue",
                        "operatingIncome",
                        "pretaxIncome",
                        "netIncome",
                        "operatingCashFlow",
                    )
                } | {
                    "period": _text(snapshot.get("period")),
                    "unit": _text(snapshot.get("unit")),
                    "statusNote": _text(snapshot.get("statusNote")),
                }
    product = sections.get("productsAndMarket")
    if isinstance(product, dict):
        public_sections["productsAndMarket"] = {
            "summary": _text(product.get("summary")),
            "revenueMixPeriod": _text(product.get("revenueMixPeriod")),
            "revenueMix": [
                {
                    "category": _text(row.get("category")),
                    "value": _number(row.get("value")),
                    "unit": _text(row.get("unit")),
                    "share": _number(row.get("share")),
                    "statusNote": _text(row.get("statusNote")),
                }
                for row in _list(product.get("revenueMix"))
                if isinstance(row, dict) and _text(row.get("category"))
            ],
            "annualRevenueMixPeriod": _text(product.get("annualRevenueMixPeriod")),
            "annualRevenueMix": [
                {
                    "category": _text(row.get("category")),
                    "value": _number(row.get("value")),
                    "unit": _text(row.get("unit")),
                    "share": _number(row.get("share")),
                    "statusNote": _text(row.get("statusNote")),
                }
                for row in _list(product.get("annualRevenueMix"))
                if isinstance(row, dict) and _text(row.get("category"))
            ],
            "currentProductsAndServices": _strings(product.get("currentProductsAndServices")),
        }
    public_governance = {
        "dataCompletenessScore": _number(governance.get("dataCompletenessScore")),
        "confidenceLevel": _text(governance.get("confidenceLevel")),
        "hasUnresolvedGaps": governance.get("hasUnresolvedGaps") is True,
    }
    return CompanyResearchV4PublicResponse(
        stockCode=str(package["company"]["stockCode"]),
        displayName=_text(package["company"].get("displayName")),
        packageVersion=_text(package.get("packageVersion")),
        contractVersion=_text(frontend.get("contractVersion")),
        researchAsOf=_text(metadata.get("researchAsOf")),
        publicationStatus="PUBLISHED",
        researchGovernance=public_governance,
        overviewData=overview_data,
        sections=public_sections,
        investmentThemes=_themes(frontend.get("investmentThemes")),
        operatingMatrix=_operating_matrix(frontend.get("operatingMatrix")),
        finance=_finance(frontend.get("finance")),
        limitationsZhTw=_strings(frontend.get("limitationsZhTw")),
    )


def _minimal(code: str, status: str, note: str) -> CompanyResearchV4PublicResponse:
    return CompanyResearchV4PublicResponse(
        stockCode=code, publicationStatus=status, limitationsZhTw=[note]
    )  # type: ignore[arg-type]


class FileCompanyProfileV4ReadStore:
    """Read-only adapter for owner-approved V4 files; never mutates source files."""

    def __init__(self, path: str | None) -> None:
        self.path = Path(path) if path else None

    def _packages(self) -> list[dict[str, Any]]:
        if self.path is None:
            return []
        files = (
            [self.path]
            if self.path.is_file()
            else sorted(self.path.glob("**/research_package.json"))
            if self.path.is_dir()
            else []
        )
        packages: list[dict[str, Any]] = []
        for file in files:
            try:
                raw = json.loads(file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            items = raw.get("records", []) if isinstance(raw, dict) and "records" in raw else [raw]
            if isinstance(items, list):
                packages.extend(item for item in items if isinstance(item, dict))
        return packages

    def get_public(self, stock_code: str) -> CompanyResearchV4PublicResponse:
        code = stock_code.strip()
        matches = [
            item
            for item in self._packages()
            if isinstance(item.get("company"), dict)
            and str(item["company"].get("stockCode", "")).strip() == code
        ]
        if not matches:
            return _minimal(code, "NOT_CONNECTED", "目前沒有可公開的公司研究資料。")
        if len(matches) != 1:
            return _minimal(code, "BLOCKED", "研究資料存在重複版本; 暫不公開。")
        package = matches[0]
        frontend = package.get("frontendProjection")
        governance = frontend.get("researchGovernance") if isinstance(frontend, dict) else None
        publication = governance.get("publication") if isinstance(governance, dict) else None
        if (
            package.get("packageVersion") != "topicpilot-stock-research.v4"
            or not isinstance(frontend, dict)
            or frontend.get("contractVersion") != "company-research-frontend.v4"
            or not isinstance(publication, dict)
        ):
            return _minimal(code, "UNPUBLISHED", "研究資料尚未完成 V4 發布審核。")
        approval = publication.get("approvalEvidence")
        approved = (
            publication.get("publicationStatus") == "PUBLISHED"
            and publication.get("ownerReviewStatus") == "APPROVED"
            and publication.get("sourceRightsStatus") == "APPROVED"
            and isinstance(approval, dict)
            and all(
                _text(approval.get(key))
                for key in ("decisionId", "reviewer", "approvedAt", "packageSha256")
            )
            and bool(re.fullmatch(r"[0-9a-f]{64}", str(approval.get("packageSha256", ""))))
            and approval.get("packageSha256") == _approval_content_sha256(package)
        )
        if not approved:
            blocked = (
                publication.get("sourceRightsStatus") == "BLOCKED"
                or publication.get("ownerReviewStatus") == "REJECTED"
                or (
                    isinstance(approval, dict)
                    and bool(_text(approval.get("packageSha256")))
                    and approval.get("packageSha256") != _approval_content_sha256(package)
                )
            )
            status = "BLOCKED" if blocked else "UNPUBLISHED"
            return _minimal(code, status, "研究內容尚未通過正式發布審核; 暫不公開。")
        try:
            return _project_published(package)
        except (KeyError, TypeError, ValueError, ValidationError):
            return _minimal(code, "BLOCKED", "研究資料欄位未符合公開契約; 暫不公開。")


__all__ = ["FileCompanyProfileV4ReadStore"]

# ruff: noqa: RUF001

"""Deterministic reported-EPS to weighted-share bridge.

The bridge deliberately operates only on facts from the same ticker, period,
and consolidation scope. It never fills a missing share count from an
assumption and never replaces the issuer-reported EPS.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal

from .contract import (
    EpsNoteExtractionResult,
    FinancialEpsBridgeEvidence,
    FinancialEpsBridgeRecord,
    FinancialFact,
)

_EPS_QUANTUM = Decimal("0.01")


def _round_eps(value: Decimal) -> Decimal:
    return value.quantize(_EPS_QUANTUM, rounding=ROUND_HALF_UP)


def _fact_map(facts: Iterable[FinancialFact]) -> dict[tuple[str, str, str], FinancialFact]:
    return {
        (fact.period_label, fact.line_item_standard, fact.statement): fact
        for fact in facts
        if fact.normalized_value is not None
    }


def _note_for_period(
    note_results: Iterable[EpsNoteExtractionResult], ticker: str, period: str
) -> EpsNoteExtractionResult | None:
    for result in note_results:
        if result.ticker != ticker:
            continue
        labels = {item.period_label for item in result.periods}
        labels.update(field.period.period_label for field in result.fields)
        if period in labels:
            return result
    return None


def _note_fields_for_period(
    result: EpsNoteExtractionResult | None, period: str
) -> list[object]:
    if result is None:
        return []
    return [field for field in result.fields if field.period.period_label == period]


def _source_note_status(
    result: EpsNoteExtractionResult | None, *, has_parent_and_eps: bool
) -> str | None:
    if result is None:
        return None
    if result.status in {"EXTRACTED", "MANUAL_REVIEW_REQUIRED"}:
        return result.status
    if not has_parent_and_eps:
        return result.status
    return result.status


def build_eps_bridge(
    facts: Iterable[FinancialFact],
    ticker: str,
    note_results: Iterable[EpsNoteExtractionResult] = (),
) -> list[FinancialEpsBridgeRecord]:
    all_facts = list(facts)
    scoped = [fact for fact in all_facts if fact.ticker == ticker]
    note_results = list(note_results)
    by_key = _fact_map(scoped)
    periods = sorted(
        {
            fact.period_label
            for fact in scoped
            if fact.statement == "income_statement"
            and fact.line_item_standard in {"basic_eps", "diluted_eps", "parent_net_income"}
        }
    )
    records: list[FinancialEpsBridgeRecord] = []
    for period in periods:
        parent = by_key.get((period, "parent_net_income", "income_statement"))
        # A legacy preview can contain only consolidated net income. It is not
        # substituted for parent earnings because that would change the bridge.
        basic_eps = by_key.get((period, "basic_eps", "income_statement"))
        diluted_eps = by_key.get((period, "diluted_eps", "income_statement"))
        basic_shares = by_key.get((period, "weighted_average_basic_shares", "share_count"))
        diluted_shares = by_key.get((period, "weighted_average_diluted_shares", "share_count"))
        note_result = _note_for_period(note_results, ticker, period)
        note_fields = _note_fields_for_period(note_result, period)
        sources = {
            fact.source_id
            for fact in (parent, basic_eps, diluted_eps, basic_shares, diluted_shares)
            if fact is not None
        }
        locations = {
            fact.source_location
            for fact in (parent, basic_eps, diluted_eps, basic_shares, diluted_shares)
            if fact is not None and fact.source_location
        }
        if note_result is not None:
            sources.add(note_result.source_id)
        evidence = [
            FinancialEpsBridgeEvidence(
                source_id=fact.source_id,
                source_url=(
                    fact.source_location.split("#", 1)[0] if fact.source_location else None
                ),
                source_page=None,
                raw_field=fact.line_item_original,
                raw_text=None,
                extraction_method="STRUCTURED_FACT",
                data_status="DIRECT",
            )
            for fact in (parent, basic_eps, diluted_eps, basic_shares, diluted_shares)
            if fact is not None
        ]
        evidence.extend(
            FinancialEpsBridgeEvidence(
                source_id=field.source_id,
                source_url=field.source_url,
                source_page=field.source_page,
                raw_field=field.raw_field,
                raw_text=field.raw_text,
                extraction_method=field.extraction_method,
                data_status=field.data_status,
            )
            for field in note_fields
        )
        source_pages = sorted(
            {
                field.source_page
                for field in note_fields
                if field.source_page is not None
            }
        )
        raw_fields = sorted({field.raw_field for field in note_fields})
        period_type = next(
            (field.period.period_type for field in note_fields),
            None,
        )
        if period_type is None:
            period_type = next(
                (
                    fact.period_type
                    for fact in (parent, basic_eps, diluted_eps, basic_shares, diluted_shares)
                    if fact is not None
                ),
                None,
            )
        period_end = next(
            (
                fact.period_end
                for fact in (parent, basic_eps, diluted_eps, basic_shares, diluted_shares)
                if fact is not None
            ),
            None,
        )
        if parent is None or basic_eps is None:
            status = "BRIDGE_INPUT_INCOMPLETE"
            note = "缺少同期間母公司業主淨利或公告基本 EPS，無法建立橋接。"
        elif basic_shares is None:
            if note_result is None:
                status = "BRIDGE_INPUT_INCOMPLETE"
                note = "公告 EPS 已取得，但尚未建立同期間 EPS 附註來源紀錄；未進行臆測重算。"
            elif note_result.status in {"EXTRACTED", "MANUAL_REVIEW_REQUIRED"}:
                has_share_field = any(
                    field.line_item_standard.endswith("shares") for field in note_fields
                )
                status = (
                    "SOURCE_NOTE_AVAILABLE_NOT_INGESTED"
                    if has_share_field or note_result.status == "MANUAL_REVIEW_REQUIRED"
                    else "SOURCE_NOTE_NOT_FOUND"
                )
                note = (
                    "官方 EPS 附註來源已定位，但加權平均股數尚未接入 read model；未進行臆測重算。"
                    if status == "SOURCE_NOTE_AVAILABLE_NOT_INGESTED"
                    else "已解析官方文件，但未找到同期間加權平均股數欄位；未進行臆測重算。"
                )
            elif note_result.status in {
                "NO_EPS_NOTE",
                "SOURCE_UNAVAILABLE",
                "RETRIEVAL_BLOCKED",
                "PARSE_FAILED",
            }:
                status = "SOURCE_NOTE_NOT_FOUND"
                note = "官方文件目前未提供可驗證的同期間加權平均股數；未進行臆測重算。"
            else:
                status = "SOURCE_NOTE_NOT_FOUND"
                note = "官方 EPS 附註尚未形成可驗證的同期間股數欄位；未進行臆測重算。"
        elif basic_shares.evidence_label == "derived_calculation":
            status = "DERIVED_SHARES_PENDING_VALIDATION"
            note = "加權平均股數是推導值，尚未完成股本變動與實際期間天數驗證；不作為正式橋接結果。"
        elif basic_shares.normalized_unit != "SHARES":
            status = "SHARE_UNIT_MISMATCH"
            note = "加權平均股數的正規化單位不是股數；停止 EPS 重算。"
        else:
            computed = _round_eps(parent.normalized_value / basic_shares.normalized_value)
            difference = computed - basic_eps.normalized_value
            status = "RECOMPUTED_MATCH" if difference == 0 else "RECOMPUTED_MISMATCH"
            note = (
                "同期間母公司業主淨利 ÷ 加權平均普通股數，四捨五入至小數點後兩位後與公告 EPS 相符。"
                if status == "RECOMPUTED_MATCH"
                else "重算 EPS 與公告 EPS 不一致，保留原始數值並要求人工釐清。"
            )
        computed_basic = None
        basic_difference = None
        if parent is not None and basic_shares is not None and basic_shares.normalized_value:
            computed_basic = _round_eps(parent.normalized_value / basic_shares.normalized_value)
            if basic_eps is not None:
                basic_difference = computed_basic - basic_eps.normalized_value
        computed_diluted = None
        diluted_difference = None
        if parent is not None and diluted_shares is not None and diluted_shares.normalized_value:
            computed_diluted = _round_eps(parent.normalized_value / diluted_shares.normalized_value)
            if diluted_eps is not None:
                diluted_difference = computed_diluted - diluted_eps.normalized_value
        records.append(
            FinancialEpsBridgeRecord(
                ticker=ticker,
                period_label=period,
                period_type=period_type,
                period_end=period_end,
                parent_net_income=parent.normalized_value if parent else None,
                weighted_average_basic_shares=(
                    basic_shares.normalized_value if basic_shares else None
                ),
                weighted_average_diluted_shares=(
                    diluted_shares.normalized_value if diluted_shares else None
                ),
                reported_basic_eps=basic_eps.normalized_value if basic_eps else None,
                reported_diluted_eps=diluted_eps.normalized_value if diluted_eps else None,
                recomputed_basic_eps=computed_basic,
                recomputed_diluted_eps=computed_diluted,
                basic_difference=basic_difference,
                diluted_difference=diluted_difference,
                status=status,
                source_ids=sorted(sources),
                source_locations=sorted(locations),
                evidence=evidence,
                source_note_status=_source_note_status(
                    note_result, has_parent_and_eps=parent is not None and basic_eps is not None
                ),
                source_pages=source_pages,
                raw_fields=raw_fields,
                note=note,
            )
        )
    return records


__all__ = ["build_eps_bridge"]

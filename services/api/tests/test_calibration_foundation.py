from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from topicpilot_api.topic_engine.calibration_foundation import (
    BenchmarkFact,
    CalibrationFoundationError,
    PITAuthorityRow,
    build_benchmark_facts,
    parse_tpex_month_payload,
    parse_twse_month_payload,
    resolve_pit_authority,
    strict_join_member_day,
)

RETRIEVED_AT = datetime(2026, 9, 29, 16, 0)


def _authority(
    *,
    effective_from: date = date(2026, 8, 7),
    role: str = "CORE",
    authority_id: str = "authority-1",
    superseded_by: str | None = None,
) -> PITAuthorityRow:
    return PITAuthorityRow(
        authority_id=authority_id,
        topic_id="topic-1",
        instrument_code="2330",
        market="TPE",
        relation_type="PRIMARY",
        structural_role=role,
        approval_state="APPROVED",
        effective_from=effective_from,
        effective_to=None,
        authority_version="roles.v1",
        source_artifact_id="artifact-1",
        source_artifact_hash="a" * 64,
        approval_reference="owner-approval",
        supersedes_authority_id=None,
        superseded_by_authority_id=superseded_by,
        reconstruction_status="DIRECT_FORMAL_ARTIFACT",
        lineage="fixture",
    )


def _benchmark(
    *,
    market: str = "TPE",
    identity: str = "TAIEX",
    trading_date: date = date(2026, 8, 7),
) -> BenchmarkFact:
    return BenchmarkFact(
        trading_date=trading_date,
        market=market,
        benchmark_identity=identity,
        close=Decimal("110"),
        previous_close=Decimal("100"),
        return_pct=Decimal("10"),
        source_provider="fixture",
        source_dataset="fixture",
        source_endpoint="fixture",
        source_content_hash="b" * 64,
        retrieved_at=RETRIEVED_AT,
        data_status="AVAILABLE",
        previous_close_basis="FIXTURE",
        adapter_version="fixture.v1",
        lineage="fixture",
    )


def test_effective_from_is_inclusive_and_future_authority_is_not_visible():
    row = _authority(effective_from=date(2026, 8, 7))

    assert resolve_pit_authority((row,), date(2026, 8, 7)) == (row,)
    assert resolve_pit_authority((row,), date(2026, 8, 6)) == ()


def test_superseded_authority_is_excluded_and_successor_is_selected():
    old = _authority(authority_id="authority-old", superseded_by="authority-new")
    new = _authority(authority_id="authority-new", role="REPRESENTATIVE")

    assert resolve_pit_authority((old, new), date(2026, 8, 7)) == (new,)


def test_multiple_effective_current_rows_fail_closed():
    first = _authority(authority_id="authority-1")
    second = _authority(authority_id="authority-2", role="RELATED")

    with pytest.raises(CalibrationFoundationError, match="PIT_AUTHORITY_CONFLICT"):
        resolve_pit_authority((first, second), date(2026, 8, 7))


def test_missing_role_is_unavailable_in_strict_join():
    result = strict_join_member_day(
        trading_date=date(2026, 8, 7),
        topic_id="topic-1",
        market="TPE",
        instrument_code="2330",
        close=Decimal("105"),
        previous_close=Decimal("100"),
        authority_rows=(),
        benchmark_facts=(_benchmark(),),
    )

    assert result["status"] == "ROLE_OR_MEMBERSHIP_MISSING"
    assert "ROLE_OR_MEMBERSHIP_MISSING" in result["blockers"]


def test_price_and_role_without_benchmark_is_not_strict_ready():
    result = strict_join_member_day(
        trading_date=date(2026, 8, 7),
        topic_id="topic-1",
        market="TPE",
        instrument_code="2330",
        close=Decimal("105"),
        previous_close=Decimal("100"),
        authority_rows=(_authority(),),
        benchmark_facts=(),
    )

    assert result["status"] == "MISSING_BENCHMARK"


def test_wrong_market_benchmark_is_not_accepted():
    result = strict_join_member_day(
        trading_date=date(2026, 8, 7),
        topic_id="topic-1",
        market="TPE",
        instrument_code="2330",
        close=Decimal("105"),
        previous_close=Decimal("100"),
        authority_rows=(_authority(),),
        benchmark_facts=(_benchmark(market="TWO", identity="TAIEX"),),
    )

    assert result["status"] == "WRONG_MARKET_BENCHMARK"


def test_strict_member_join_uses_own_market_benchmark():
    result = strict_join_member_day(
        trading_date=date(2026, 8, 7),
        topic_id="topic-1",
        market="TPE",
        instrument_code="2330",
        close=Decimal("105"),
        previous_close=Decimal("100"),
        authority_rows=(_authority(),),
        benchmark_facts=(_benchmark(),),
    )

    assert result["status"] == "STRICT_READY"
    assert result["benchmark_identity"] == "TAIEX"
    assert result["structural_role"] == "CORE"


def test_twse_month_parser_and_previous_close_derivation():
    payload_a = {
        "stat": "OK",
        "data": [["115/08/03", "100", "105", "99", "104"]],
    }
    payload_b = {
        "stat": "OK",
        "data": [["115/08/04", "104", "106", "103", "105"]],
    }
    bars = parse_twse_month_payload(
        payload_a,
        source_endpoint="twse/a",
        retrieved_at=RETRIEVED_AT,
    ) + parse_twse_month_payload(
        payload_b,
        source_endpoint="twse/b",
        retrieved_at=RETRIEVED_AT,
    )
    facts = build_benchmark_facts(
        bars,
        market="TPE",
        from_date=date(2026, 8, 3),
        to_date=date(2026, 8, 4),
    )

    assert facts[0].previous_close is None
    assert facts[0].data_status == "MISSING_PREVIOUS_CLOSE"
    assert facts[1].previous_close == Decimal("104")
    assert abs(facts[1].return_pct - Decimal(100) / Decimal(104)) < Decimal("1e-20")


def test_tpex_month_parser_derives_previous_close_from_official_change():
    payload = {
        "date": "20260801",
        "tables": [{
            "fields": ["日期", "開市", "最高", "最低", "收市", "漲/跌"],
            "data": [["2026/08/03", "100", "105", "99", "104", "4"]],
        }],
    }
    bars = parse_tpex_month_payload(
        payload,
        source_endpoint="tpex/month",
        retrieved_at=RETRIEVED_AT,
    )
    facts = build_benchmark_facts(
        bars,
        market="TWO",
        from_date=date(2026, 8, 3),
        to_date=date(2026, 8, 3),
    )

    assert facts[0].previous_close == Decimal("100")
    assert facts[0].return_pct == Decimal("4")
    assert facts[0].previous_close_basis == "DERIVED_FROM_OFFICIAL_CLOSE_AND_CHANGE"


def test_duplicate_benchmark_date_fails_closed():
    payload = {
        "stat": "OK",
        "data": [
            ["115/08/03", "100", "105", "99", "104"],
            ["115/08/03", "100", "105", "99", "104"],
        ],
    }

    with pytest.raises(CalibrationFoundationError, match="DUPLICATE_DATE"):
        parse_twse_month_payload(
            payload,
            source_endpoint="twse/duplicate",
            retrieved_at=RETRIEVED_AT,
        )

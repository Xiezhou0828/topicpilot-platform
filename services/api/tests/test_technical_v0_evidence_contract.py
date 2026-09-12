from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from topicpilot_api.schemas import StockTechnicalPublicationRead
from topicpilot_api.technical_publication import build_technical_publication
from topicpilot_api.technical_v0_evidence_contract import (
    E1_ARTIFACT_RUNTIME_DEPENDENCY,
    FORMAL_INDICATOR_IDS,
    SOURCE_FOUNDATION_SHA256,
    SOURCE_FOUNDATION_VERSION,
    EvidenceUnavailable,
    TechnicalV0ContractError,
    TechnicalV0EvidenceConsumer,
    TechnicalV0EvidenceProvider,
    TechnicalV0Request,
)


def _history(
    closes: list[int],
    *,
    market: str = "TPE",
    code: str = "2330",
    continuity: dict | None = None,
    known_event_lookup: dict | None = None,
) -> dict:
    items = []
    start = date(2026, 1, 2)
    for index, close in enumerate(closes):
        session = start + timedelta(days=index)
        items.append(
            {
                "trading_date": session,
                "observed_at": datetime(2026, 1, 2, tzinfo=UTC) + timedelta(days=index),
                "retrieved_at": datetime(2026, 1, 2, tzinfo=UTC) + timedelta(days=index),
                "ordering_key": f"{index:04d}",
                "observation_id": f"fixture-{market}-{code}-{index:04d}",
                "open": Decimal(close),
                "high": Decimal(close + 1),
                "low": Decimal(close - 1),
                "close": Decimal(close),
                "volume": Decimal(1_000 + index),
                "quality_state": "ACCEPTED",
                "adjustment_state": "UNKNOWN",
                "source": {
                    "source_code": "SYNTHETIC_CANONICAL_FIXTURE",
                    "adapter_version": "fixture-adapter.v1",
                    "observation_semantics": "DAILY_BAR",
                    "reference_data_version": "fixture-reference.v1",
                    "normalization_contract_version": "fixture-normalization.v1",
                    "mapping_policy_version": "fixture-mapping.v1",
                },
            }
        )
    result = {
        "code": code,
        "market": market,
        "instrument_id": f"{market}:{code}",
        "requested_from": start,
        "requested_to": start + timedelta(days=max(len(closes) - 1, 0)),
        "items": items,
        "continuity_evidence": continuity or {
            "default": {
                "coverage_state": "COVERED_NO_EVENT",
                "coverage_complete": True,
                "known_events": [],
                "evidence_id": "fixture-continuity.v1",
                "method": "SYNTHETIC_BOUNDED_FIXTURE",
                "authority": "SYNTHETIC_CANONICAL_FIXTURE",
            }
        },
    }
    if known_event_lookup is not None:
        result["known_event_lookup"] = known_event_lookup
    return result


def _latest(count: int = 70, *, market: str = "TPE", code: str = "2330") -> tuple[dict, date]:
    history = _history([100 + index for index in range(count)], market=market, code=code)
    return history, date(2026, 1, 2) + timedelta(days=count - 1)


def test_contract_identity_version_source_and_single_lookup_are_explicit():
    history, session = _latest()
    provider = TechnicalV0EvidenceProvider(history)
    evidence = provider.get_evidence(indicator_id="MA20", session_date=session)

    assert evidence["evidence_logical_identity"] == {
        "instrument_identity": "TPE:2330",
        "market": "TPE",
        "session_date": session,
        "indicator_id": "MA20",
    }
    assert evidence["evidence_version_identity"]["technical_policy_version"] == (
        "stock-technical-v0-policy.v4"
    )
    assert evidence["source_identity"]["source_foundation_version"] == SOURCE_FOUNDATION_VERSION
    assert evidence["source_identity"]["source_foundation_sha256"] == SOURCE_FOUNDATION_SHA256
    assert evidence["lineage_reference"].startswith("sha256:")
    assert evidence["pit"]["pit_status"] == "PIT_SAFE"
    assert evidence["availability"]["state"] == "AVAILABLE"
    assert evidence["value"] == Decimal("159.5")


def test_tpe_and_two_representatives_and_batch_lookup_preserve_versions():
    tpe_history, session = _latest(market="TPE", code="2330")
    two_history, two_session = _latest(market="TWO", code="6488")

    tpe = TechnicalV0EvidenceProvider(tpe_history).get_evidence(
        indicator_id="RSI14", session_date=session
    )
    two_provider = TechnicalV0EvidenceProvider(two_history)
    two = two_provider.get_evidence(indicator_id="MACD_SIGNAL_12_26_9", session_date=two_session)
    batch = two_provider.get_batch(
        indicator_ids=["MA5", "MA20", "RSI14", "MACD_HISTOGRAM_12_26_9"],
        session_date=two_session,
    )

    assert tpe["market"] == "TPE"
    assert two["market"] == "TWO"
    assert all(item["indicator_id"] in FORMAL_INDICATOR_IDS for item in batch)
    assert len(batch) == 4
    assert all(item["evidence_version_identity"]["algorithm_version"] for item in batch)


def test_ineligible_surface_is_not_coerced_into_unavailable_or_strategy_meaning():
    history, session = _latest()
    history = _history([200 - index for index in range(70)])
    evidence = TechnicalV0EvidenceProvider(history).get_evidence(
        indicator_id="MA20", session_date=session
    )

    assert evidence["publication_state"] == "FORMAL"
    assert evidence["technical_surface"]["technical_eligibility"] == "INELIGIBLE"
    assert evidence["technical_surface"]["publication_status"] == "BLOCKED"
    assert evidence["value"] is not None


def test_empty_history_returns_explicit_unavailable_and_consumer_does_not_coerce():
    history = _history([])
    evidence = TechnicalV0EvidenceProvider(history).get_evidence(
        indicator_id="MA20", session_date=date(2026, 1, 2)
    )
    assert evidence["publication_state"] == "UNAVAILABLE"
    assert evidence["availability"]["state"] == "UNAVAILABLE"
    assert evidence["availability_reason"] == "NO_ACCEPTED_CANONICAL_PRICE_OBSERVATIONS"
    with pytest.raises(EvidenceUnavailable):
        TechnicalV0EvidenceConsumer.value(evidence)


def test_pit_limited_lookup_preserves_limitation_without_future_data():
    history, session = _latest()
    history["known_event_lookup"] = {"lookup_state": "TIMEOUT"}
    provider = TechnicalV0EvidenceProvider(history)
    evidence = provider.get_evidence(indicator_id="MA60", session_date=session)

    assert evidence["publication_state"] == "FORMAL_WITH_LIMITATION"
    assert evidence["availability"]["state"] == "AVAILABLE_WITH_LIMITATION"
    assert evidence["limitation_reasons"] == ["EVENT_LOOKUP_UNAVAILABLE"]
    assert evidence["pit"]["future_observations_consumed"] is False


def test_ma60_and_indicator_specific_warmup_boundaries_are_contract_visible():
    history, session = _latest()
    provider = TechnicalV0EvidenceProvider(history)
    ma60 = provider.get_evidence(indicator_id="MA60", session_date=session)

    short_history, short_session = _latest(34)
    short_provider = TechnicalV0EvidenceProvider(short_history)
    rsi = short_provider.get_evidence(
        indicator_id="RSI14", session_date=date(2026, 1, 2) + timedelta(days=14)
    )
    macd = short_provider.get_evidence(
        indicator_id="MACD_12_26_9", session_date=date(2026, 1, 2) + timedelta(days=25)
    )
    signal_warmup = short_provider.get_evidence(
        indicator_id="MACD_SIGNAL_12_26_9", session_date=date(2026, 1, 2) + timedelta(days=32)
    )
    signal_ready = short_provider.get_evidence(
        indicator_id="MACD_SIGNAL_12_26_9", session_date=short_session
    )

    assert ma60["publication_state"] == "FORMAL"
    assert ma60["required_observation_count"] == 60
    assert rsi["publication_state"] == "FORMAL"
    assert rsi["required_observation_count"] == 15
    assert macd["publication_state"] == "FORMAL"
    assert macd["required_observation_count"] == 26
    assert signal_warmup["publication_state"] == "UNAVAILABLE"
    assert signal_warmup["availability_reason"] == "UNAVAILABLE_INSUFFICIENT_HISTORY"
    assert signal_ready["publication_state"] == "FORMAL"
    assert signal_ready["required_observation_count"] == 34


def test_unknown_and_fail_continuity_are_fail_closed_per_indicator_window():
    unknown = _history([100 + index for index in range(20)], continuity=None)
    unknown.pop("continuity_evidence")
    unknown_evidence = TechnicalV0EvidenceProvider(unknown).get_evidence(
        indicator_id="MA20", session_date=date(2026, 1, 2) + timedelta(days=19)
    )
    fail = _history(
        [100 + index for index in range(20)],
        continuity={
            "default": {
                "coverage_state": "COVERED_NO_EVENT",
                "coverage_complete": True,
                "known_events": [],
            },
            "MA5": {
                "coverage_state": "COVERED_EVENT",
                "coverage_complete": True,
                "known_events": [{"event_type": "SPLIT", "effective_date": "2026-01-20"}],
            },
        },
    )
    fail_evidence = TechnicalV0EvidenceProvider(fail).get_evidence(
        indicator_id="MA5", session_date=date(2026, 1, 2) + timedelta(days=19)
    )

    assert unknown_evidence["continuity_state"] == "CONTINUITY_UNKNOWN"
    assert unknown_evidence["availability"]["state"] == "BLOCKED"
    assert fail_evidence["continuity_state"] == "CONTINUITY_FAIL"
    assert fail_evidence["availability_reason"] == "CONTINUITY_FAIL"


def test_future_observations_cannot_change_prior_as_of_or_lineage():
    base_history, session = _latest(40)
    future_history, _ = _latest(41)
    base = TechnicalV0EvidenceProvider(base_history).get_evidence(
        indicator_id="MA20", session_date=session
    )
    future = TechnicalV0EvidenceProvider(future_history).get_evidence(
        indicator_id="MA20", session_date=session
    )

    assert future["value"] == base["value"]
    assert future["pit"] == base["pit"]
    assert future["lineage_reference"] == base["lineage_reference"]


def test_bounded_historical_lookup_and_consumer_request_facade():
    history, session = _latest()
    consumer = TechnicalV0EvidenceConsumer(TechnicalV0EvidenceProvider(history))
    one = consumer.request_one(TechnicalV0Request("TPE:2330", "MA5", session))
    many = consumer.request_many(
        indicator_ids=["MA5", "MA10", "MA20"], session_date=session
    )
    historical = consumer.request_history(
        indicator_ids=["MA20", "RSI14"],
        from_session=date(2026, 1, 2) + timedelta(days=19),
        to_session=session,
        limit=100,
    )

    assert one["evidence_key"] == f"TPE:2330|{session.isoformat()}|MA5"
    assert len(many) == 3
    assert historical
    assert {item["indicator_id"] for item in historical} == {"MA20", "RSI14"}
    assert all(item["pit"]["pit_status"] == "PIT_SAFE" for item in historical)


def test_api_model_can_validate_reference_publication_without_new_route():
    history, _ = _latest()
    publication = build_technical_publication(history)
    model = StockTechnicalPublicationRead.model_validate(
        {
            **publication,
            "requested_from": history["requested_from"],
            "requested_to": history["requested_to"],
        }
    )
    assert model.technical_contract_version == "stock-technical-publication.v3"
    assert model.technical_evidence
    assert E1_ARTIFACT_RUNTIME_DEPENDENCY == "NO"


def test_evidence_only_boundary_and_unknown_indicator_are_machine_testable():
    history, session = _latest()
    provider = TechnicalV0EvidenceProvider(history)
    evidence = provider.get_evidence(indicator_id="MA5", session_date=session)
    forbidden_keys = {
        "buy",
        "sell",
        "entry",
        "exit",
        "target",
        "stop_loss",
        "position_size",
        "expected_return",
        "win_rate",
        "trade_rank",
        "recommendation",
        "opportunity",
    }
    assert not forbidden_keys.intersection(evidence)
    with pytest.raises(TechnicalV0ContractError):
        provider.get_evidence(indicator_id="ADVANCED_PATTERN", session_date=session)

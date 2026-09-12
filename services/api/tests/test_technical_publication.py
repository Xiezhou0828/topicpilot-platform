from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

import topicpilot_api.production_read_model_api as production_read_model_api
from topicpilot_api.config import Settings
from topicpilot_api.database import get_db
from topicpilot_api.historical_read_model import attach_bounded_continuity_evidence
from topicpilot_api.main import create_app
from topicpilot_api.technical_publication import build_technical_publication


def _history(*, items: list[dict]) -> dict:
    return {
        "code": "2330",
        "market": "TPE",
        "requested_from": date(2026, 8, 1),
        "requested_to": date(2026, 8, 14),
        "returned_from": date(2026, 8, 13) if items else None,
        "returned_to": date(2026, 8, 13) if items else None,
        "latest_trading_date": date(2026, 8, 13) if items else None,
        "latest_observed_at": datetime(2026, 8, 13, tzinfo=UTC) if items else None,
        "latest_retrieved_at": datetime(2026, 8, 13, tzinfo=UTC) if items else None,
        "items": items,
    }


def _raw_item(**overrides) -> dict:
    item = {
        "trading_date": date(2026, 8, 13),
        "observed_at": datetime(2026, 8, 13, tzinfo=UTC),
        "retrieved_at": datetime(2026, 8, 13, tzinfo=UTC),
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.5,
        "volume": 1000.0,
        "source_code": "TWSE_OFFICIAL_DAILY",
        "quality_state": "ACCEPTED",
        "adjustment_state": "UNKNOWN",
        "source": {
            "source_code": "TWSE_OFFICIAL_DAILY",
            "adapter_version": "twse-official-daily.v2",
            "observation_semantics": "DAILY_BAR",
            "reference_data_version": "tw-reference-v1",
            "normalization_contract_version": "historical-daily.v1",
            "mapping_policy_version": "historical-daily-mapping.v1",
        },
    }
    item.update(overrides)
    return item


def test_technical_foundation_preserves_raw_input_and_fails_closed_for_unknown_adjustment():
    result = build_technical_publication(_history(items=[_raw_item()]))

    assert result["status"] == "UNAVAILABLE"
    assert result["publication_state"] == "UNAVAILABLE"
    assert result["input_state"] == "RAW_OBSERVED"
    assert result["published_indicators"] == []
    assert result["browser_calculation_allowed"] == "NO"
    assert result["provenance"]["authority"] == "V2_CANONICAL_OBSERVATION_CHAIN"
    assert result["provenance"]["series_semantics"] == "RAW_OBSERVED_DAILY_BAR"
    assert result["provenance"]["adjustment_state"] == "UNKNOWN"
    assert "ADJUSTMENT_AUTHORITY_UNKNOWN" in result["availability_reasons"]
    assert "CONTINUITY_AUTHORITY_UNAVAILABLE" in result["availability_reasons"]


def test_technical_foundation_reports_empty_history_without_zero_or_indicator_fallback():
    result = build_technical_publication(_history(items=[]))

    assert result["status"] == "UNAVAILABLE"
    assert result["publication_state"] == "NOT_PUBLISHED"
    assert result["input_state"] == "UNAVAILABLE"
    assert result["provenance"] is None
    assert result["published_indicators"] == []
    assert result["availability_reasons"] == ["NO_ACCEPTED_CANONICAL_PRICE_OBSERVATIONS"]


def test_technical_route_uses_shared_history_authority_and_exposes_deferred_contract(monkeypatch):
    calls: list[tuple] = []

    def fake_read_historical_bars(session, symbol, from_date, to_date, market_code, limit):
        calls.append((session, symbol, from_date, to_date, market_code, limit))
        return _history(items=[_raw_item()])

    monkeypatch.setattr(
        production_read_model_api,
        "read_historical_bars",
        fake_read_historical_bars,
    )
    app = create_app(Settings(DATABASE_URL="postgresql+psycopg://unused/unused"))

    def override_db():
        yield object()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        response = client.get(
            "/api/v2/stocks/2330/technical",
            params={"from": "2026-08-01", "to": "2026-08-14", "market": "TPE"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "UNAVAILABLE"
    assert payload["publicationState"] == "UNAVAILABLE"
    assert payload["publishedIndicators"] == []
    assert payload["technicalResultStatus"] == "UNAVAILABLE"
    assert payload["technicalEligibility"] == "UNAVAILABLE"
    assert payload["eventAuthorityStatus"] == "LOOKUP_UNAVAILABLE"
    assert payload["publicationStatus"] == "UNAVAILABLE"
    assert payload["provenance"]["adjustmentState"] == "UNKNOWN"
    assert calls[0][1:] == (
        "2330",
        date(2026, 8, 1),
        date(2026, 8, 14),
        "TPE",
        200,
    )


def _continuity_pass() -> dict:
    return {
        "coverage_state": "COVERED_NO_EVENT",
        "coverage_complete": True,
        "known_events": [],
        "evidence_id": "test-bounded-continuity-v1",
        "method": "TEST_OWNER_APPROVED_BOUNDED_METHOD",
        "authority": "TEST_BOUNDED_AUTHORITY",
    }


def _series_history(
    closes: list[float],
    *,
    volumes: list[float] | None = None,
    continuity_evidence: dict | None = None,
) -> dict:
    volumes = volumes or [1000 + index for index in range(len(closes))]
    items = []
    for index, (close, volume) in enumerate(zip(closes, volumes, strict=True)):
        trading_date = date(2026, 1, 2) + timedelta(days=index)
        items.append(
            _raw_item(
                trading_date=trading_date,
                observed_at=datetime(2026, 1, 2, tzinfo=UTC) + timedelta(days=index),
                retrieved_at=datetime(2026, 1, 2, tzinfo=UTC) + timedelta(days=index),
                open=close,
                high=close + 1,
                low=close - 1,
                close=close,
                volume=volume,
                ordering_key=f"{index:04d}",
                observation_id=f"obs-{index:04d}",
            )
        )
    return _history(items=items) | {
        "instrument_id": "instrument-2330",
        "continuity_evidence": continuity_evidence or {"default": _continuity_pass()},
    }


def _evidence(result: dict, indicator_id: str, session_date: date) -> dict:
    return next(
        item
        for item in result["technical_evidence"]
        if item["indicator_id"] == indicator_id and item["session_date"] == session_date
    )


def test_technical_v0_publishes_all_fourteen_outputs_only_after_bounded_pass():
    result = build_technical_publication(_series_history([100 + index for index in range(70)]))

    assert result["status"] == "FORMAL"
    assert result["price_basis"] == "RAW_OBSERVED"
    assert result["continuity_policy"] == "FORMAL_RAW_OBSERVED + KNOWN_EVENT_AWARE_OFFICIAL_OVERLAY"
    assert result["published_indicators"] == [
        "MA5",
        "MA10",
        "MA20",
        "MA60",
        "DISTANCE_TO_MA20",
        "RAW_CLOSE_RETURN_5D",
        "RAW_CLOSE_RETURN_20D",
        "VOLUME_MA5",
        "VOLUME_MA20",
        "VOLUME_RATIO_20",
        "RSI14",
        "MACD_12_26_9",
        "MACD_SIGNAL_12_26_9",
        "MACD_HISTOGRAM_12_26_9",
    ]
    latest = date(2026, 1, 2) + timedelta(days=69)
    ma5 = _evidence(result, "MA5", latest)
    assert ma5["value"] == Decimal("167")
    assert ma5["publication_state"] == "FORMAL"
    assert ma5["continuity_state"] == "CONTINUITY_PASS_BOUNDED"
    for record in result["technical_evidence"]:
        assert record["instrument_identity"] == "instrument-2330"
        assert record["algorithm_id"]
        assert record["required_observation_window"]
        assert record["actual_observation_window"]
        assert record["source_lineage"]["lineage_state"] == "VERSIONED"


def test_technical_v0_warmup_boundaries_are_indicator_specific():
    result = build_technical_publication(_series_history([100 + index for index in range(34)]))
    first = date(2026, 1, 2)
    rsi_at_14 = _evidence(result, "RSI14", first + timedelta(days=14))
    macd_at_25 = _evidence(result, "MACD_12_26_9", first + timedelta(days=25))
    signal_at_32 = _evidence(
        result, "MACD_SIGNAL_12_26_9", first + timedelta(days=32)
    )
    signal_at_33 = _evidence(
        result, "MACD_SIGNAL_12_26_9", first + timedelta(days=33)
    )
    ma60_at_33 = _evidence(result, "MA60", first + timedelta(days=33))
    assert rsi_at_14["publication_state"] == "FORMAL"
    assert macd_at_25["publication_state"] == "FORMAL"
    assert signal_at_32["publication_state"] == "UNAVAILABLE"
    assert signal_at_32["availability_reason"] == "UNAVAILABLE_INSUFFICIENT_HISTORY"
    assert signal_at_33["publication_state"] == "FORMAL"
    assert ma60_at_33["availability_reason"] == "UNAVAILABLE_INSUFFICIENT_HISTORY"


def test_rsi_wilder_edge_cases_are_canonical():
    for closes, expected in (
        ([100 + index for index in range(20)], Decimal("100")),
        ([100 - index for index in range(20)], Decimal("0")),
        ([100 for _ in range(20)], Decimal("50")),
    ):
        result = build_technical_publication(_series_history(closes))
        session = date(2026, 1, 2) + timedelta(days=19)
        record = _evidence(result, "RSI14", session)
        assert record["value"] == expected
        assert record["publication_state"] == "FORMAL"


def test_macd_seed_signal_and_histogram_are_deterministic():
    history = _series_history([100 + index * 2 for index in range(40)])
    first = build_technical_publication(history)
    second = build_technical_publication(history)
    session = date(2026, 1, 2) + timedelta(days=39)
    macd = _evidence(first, "MACD_12_26_9", session)
    signal = _evidence(first, "MACD_SIGNAL_12_26_9", session)
    histogram = _evidence(first, "MACD_HISTOGRAM_12_26_9", session)
    assert macd["value"] == _evidence(second, "MACD_12_26_9", session)["value"]
    assert signal["value"] == _evidence(second, "MACD_SIGNAL_12_26_9", session)["value"]
    assert histogram["value"] == macd["value"] - signal["value"]
    assert histogram["required_observation_count"] == 34


def test_continuity_is_indicator_level_and_unknown_fails_closed():
    result = build_technical_publication(
        _series_history(
            [100 + index for index in range(70)],
            continuity_evidence={
                "default": _continuity_pass(),
                "MA60": {
                    "coverage_state": "UNKNOWN",
                    "coverage_complete": False,
                    "known_events": [],
                    "method": "TEST_BOUNDED_METHOD",
                },
            },
        )
    )
    session = date(2026, 1, 2) + timedelta(days=69)
    assert _evidence(result, "MA5", session)["publication_state"] == "FORMAL"
    ma60 = _evidence(result, "MA60", session)
    assert ma60["publication_state"] == "UNAVAILABLE"
    assert ma60["continuity_state"] == "CONTINUITY_UNKNOWN"
    assert ma60["availability_reason"] == "CONTINUITY_UNKNOWN"


def test_continuity_empty_event_result_is_not_automatic_pass():
    result = build_technical_publication(
        _series_history(
            [100 + index for index in range(20)],
            continuity_evidence={
                "default": {
                    "coverage_state": "UNKNOWN",
                    "coverage_complete": False,
                    "known_events": [],
                    "method": "EMPTY_EVENT_RESULT",
                }
            },
        )
    )
    session = date(2026, 1, 2) + timedelta(days=19)
    record = _evidence(result, "MA5", session)
    assert record["continuity_state"] == "CONTINUITY_UNKNOWN"
    assert record["publication_state"] == "UNAVAILABLE"


def _successful_event_lookup(*, events: list[dict]) -> dict:
    return {
        "lookup_state": "SUCCESS",
        "query_completed": True,
        "response_parsed": True,
        "identity_binding_valid": True,
        "normalization_valid": True,
        "known_events": events,
        "source_lineage": {
            "lineage_state": "VERSIONED",
            "source": "TEST_OFFICIAL_EVENT_LOOKUP",
            "version": "test-events-v1",
        },
    }


def test_known_event_successful_no_match_allows_unknown_continuity_to_publish():
    history = _series_history([100 + index for index in range(70)]) | {
        "continuity_evidence": {
            "default": {
                "coverage_state": "PARTIAL_UNKNOWN",
                "coverage_complete": False,
                "known_events": [],
            }
        },
        "known_event_lookup": _successful_event_lookup(events=[]),
    }
    result = build_technical_publication(history)
    session = date(2026, 1, 2) + timedelta(days=69)
    ma60 = _evidence(result, "MA60", session)

    assert result["status"] == "FORMAL"
    assert ma60["publication_state"] == "FORMAL"
    assert ma60["continuity_state"] == "CONTINUITY_UNKNOWN"
    assert ma60["event_lookup_state"] == "NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND"
    assert ma60["event_lookup_evidence"]["publication_allowed"] is True


def test_known_event_intersection_blocks_only_the_affected_window():
    history = _series_history([100 + index for index in range(70)]) | {
        "known_event_lookup": _successful_event_lookup(
            events=[
                {
                    "canonical_identity": "TPE:2330",
                    "effective_date": "2026-01-20",
                    "event_type": "CAPITAL_REDUCTION",
                    "verified": True,
                    "handling": "EXCLUDE",
                }
            ]
        ),
    }
    result = build_technical_publication(history)
    session = date(2026, 1, 2) + timedelta(days=69)
    ma5 = _evidence(result, "MA5", session)
    ma60 = _evidence(result, "MA60", session)

    assert ma5["publication_state"] == "FORMAL"
    assert ma5["event_lookup_state"] == "NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND"
    assert ma60["publication_state"] == "UNAVAILABLE"
    assert ma60["availability_reason"] == "KNOWN_VERIFIED_EVENT_REQUIRES_EVENT_AWARE_HANDLING"
    assert ma60["event_lookup_state"] == "KNOWN_VERIFIED_BREAKING_EVENT_FOUND"


def test_known_event_lookup_failure_is_visible_with_bounded_limitation():
    history = _series_history([100 + index for index in range(70)]) | {
        "known_event_lookup": {"lookup_state": "TIMEOUT"},
    }
    result = build_technical_publication(history)
    session = date(2026, 1, 2) + timedelta(days=69)
    ma60 = _evidence(result, "MA60", session)

    assert ma60["publication_state"] == "FORMAL_WITH_LIMITATION"
    assert ma60["value"] is not None
    assert ma60["availability_reason"] is None
    assert ma60["limitation_reasons"] == ["EVENT_LOOKUP_UNAVAILABLE"]
    assert result["technical_result_status"] == "VALID"
    assert result["technical_eligibility"] == "ELIGIBLE"
    assert result["event_authority_status"] == "LOOKUP_UNAVAILABLE"
    assert result["publication_status"] == "AVAILABLE_WITH_LIMITATION"
    assert result["publication_state"] == "FORMAL_WITH_LIMITATION"
    assert result["limitation_reasons"] == ["EVENT_LOOKUP_UNAVAILABLE"]
    assert result["status"] == "FORMAL"


def test_successful_known_event_outside_ma60_is_handled_with_limitation():
    history = _series_history([100 + index for index in range(70)]) | {
        "known_event_lookup": _successful_event_lookup(
            events=[
                {
                    "canonical_identity": "TPE:2330",
                    "effective_date": "2026-01-03",
                    "event_type": "CASH_DIVIDEND_EX_DIVIDEND",
                    "verified": True,
                    "handling": "EXCLUDE",
                }
            ]
        ),
    }
    result = build_technical_publication(history)

    assert result["technical_result_status"] == "VALID"
    assert result["event_authority_status"] == "KNOWN_EVENT"
    assert result["publication_status"] == "AVAILABLE_WITH_LIMITATION"
    assert result["limitation_reasons"] == ["KNOWN_EVENT_HANDLED"]
    latest = date(2026, 1, 2) + timedelta(days=69)
    assert _evidence(result, "MA60", latest)["publication_state"] == "FORMAL"


def test_below_ma60_is_ineligible_and_not_an_error():
    result = build_technical_publication(_series_history([200 - index for index in range(70)]))

    assert result["technical_result_status"] == "INELIGIBLE"
    assert result["technical_eligibility"] == "INELIGIBLE"
    assert result["publication_status"] == "BLOCKED"
    assert result["reason_codes"] == ["BELOW_MA60", "TECHNICAL_V0_INELIGIBLE"]


def test_known_event_intersecting_ma60_is_a_hard_publication_block():
    history = _series_history([100 + index for index in range(70)]) | {
        "known_event_lookup": _successful_event_lookup(
            events=[
                {
                    "canonical_identity": "TPE:2330",
                    "effective_date": "2026-01-20",
                    "event_type": "CAPITAL_REDUCTION",
                    "verified": True,
                    "handling": "EXCLUDE",
                }
            ]
        ),
    }
    result = build_technical_publication(history)

    assert result["technical_result_status"] == "UNAVAILABLE"
    assert result["event_authority_status"] == "KNOWN_EVENT"
    assert result["publication_status"] == "BLOCKED"
    assert "KNOWN_CONTINUITY_EVENT" in result["reason_codes"]


def test_publication_surface_fields_are_serializable_through_api_model():
    from topicpilot_api.schemas import StockTechnicalPublicationRead

    result = build_technical_publication(
        _series_history([100 + index for index in range(70)])
        | {"known_event_lookup": {"lookup_state": "TIMEOUT"}}
    )
    model = StockTechnicalPublicationRead.model_validate(result)
    payload = model.model_dump(by_alias=True)

    assert payload["technicalResultStatus"] == "VALID"
    assert payload["eventAuthorityStatus"] == "LOOKUP_UNAVAILABLE"
    assert payload["publicationStatus"] == "AVAILABLE_WITH_LIMITATION"
    assert payload["publicationState"] == "FORMAL_WITH_LIMITATION"
    assert payload["technicalEvidence"][0]["eventAuthorityStatus"]


def test_continuity_fail_marks_only_intersecting_indicator_window_unavailable():
    result = build_technical_publication(
        _series_history(
            [100 + index for index in range(20)],
            continuity_evidence={
                "default": _continuity_pass(),
                "MA5": {
                    "coverage_state": "COVERED_EVENT",
                    "coverage_complete": True,
                    "known_events": [
                        {
                            "event_type": "CAPITAL_REDUCTION",
                            "primary_effective_date": "2026-01-20",
                        }
                    ],
                    "method": "TEST_BOUNDED_METHOD",
                },
            },
        )
    )
    session = date(2026, 1, 2) + timedelta(days=19)
    ma5 = _evidence(result, "MA5", session)
    ma20 = _evidence(result, "MA20", session)
    assert ma5["continuity_state"] == "CONTINUITY_FAIL"
    assert ma5["publication_state"] == "UNAVAILABLE"
    assert ma20["publication_state"] == "FORMAL"


def test_runtime_lifecycle_attachment_fails_only_an_intersecting_window():
    history = _series_history([100 + index for index in range(70)]) | {
        "lifecycle": {
            "status_code": "DELISTED",
            "effective_from": date(2026, 1, 20),
            "effective_to": None,
            "evidence_id": "lifecycle-2330-20260120",
        }
    }
    history = attach_bounded_continuity_evidence(history)
    result = build_technical_publication(history)
    session = date(2026, 1, 2) + timedelta(days=69)

    ma5 = _evidence(result, "MA5", session)
    ma60 = _evidence(result, "MA60", session)
    assert ma5["continuity_state"] == "CONTINUITY_UNKNOWN"
    assert ma5["publication_state"] == "UNAVAILABLE"
    assert ma60["continuity_state"] == "CONTINUITY_FAIL"
    assert ma60["publication_state"] == "UNAVAILABLE"
    assert ma60["availability_reason"] == "CONTINUITY_FAIL"


def test_future_observations_do_not_change_prior_as_of_evidence():
    base_history = _series_history([100 + index for index in range(40)])
    future_history = _series_history([100 + index for index in range(41)])
    session = date(2026, 1, 2) + timedelta(days=39)
    base = _evidence(build_technical_publication(base_history), "MA20", session)
    future = _evidence(build_technical_publication(future_history), "MA20", session)
    assert future["value"] == base["value"]
    assert future["actual_observation_window"] == base["actual_observation_window"]


def test_volume_ratio_zero_denominator_is_unavailable_with_reason():
    result = build_technical_publication(
        _series_history([100 + index for index in range(20)], volumes=[0] * 20)
    )
    session = date(2026, 1, 2) + timedelta(days=19)
    volume_ma = _evidence(result, "VOLUME_MA20", session)
    ratio = _evidence(result, "VOLUME_RATIO_20", session)
    assert volume_ma["publication_state"] == "FORMAL"
    assert volume_ma["value"] == Decimal("0")
    assert ratio["publication_state"] == "UNAVAILABLE"
    assert ratio["availability_reason"] == "UNAVAILABLE_ZERO_DENOMINATOR"


def test_technical_route_rejects_reversed_window_before_history_read(monkeypatch):
    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("shared history reader must not run for an invalid window")

    monkeypatch.setattr(production_read_model_api, "read_historical_bars", fail_if_called)
    app = create_app(Settings(DATABASE_URL="postgresql+psycopg://unused/unused"))

    def override_db():
        yield object()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        response = client.get(
            "/api/v2/stocks/2330/technical",
            params={"from": "2026-08-14", "to": "2026-08-01"},
        )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")


def test_technical_route_openapi_is_additive_and_read_only():
    openapi = create_app().openapi()
    operation = openapi["paths"]["/api/v2/stocks/{symbol}/technical"]["get"]

    assert operation["summary"] == "Read Stock Technical V0 evidence and bounded publication status"
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/StockTechnicalPublicationRead"
    )
    assert "post" not in openapi["paths"]["/api/v2/stocks/{symbol}/technical"]

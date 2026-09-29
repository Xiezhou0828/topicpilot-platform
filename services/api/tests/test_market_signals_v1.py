# ruff: noqa: E501

from __future__ import annotations

from datetime import date, timedelta

from topicpilot_api.market_signals import (
    SIGNAL_CATALOG,
    _frequency,
    catalog_payload,
    evaluate_v1_signals,
)

TARGET = date(2026, 9, 29)


def index_overview(tpe: float, two: float, *, positive: int = 50, negative: int = 40, flat: int = 10, turnover: float | None = None) -> dict:
    rows = [
        {"market": "TPE", "status": "AVAILABLE", "changePct": tpe},
        {"market": "TWO", "status": "AVAILABLE", "changePct": two},
    ]
    if turnover is None:
        turnover_rows = []
    else:
        turnover_rows = [
            {"market": "TPE", "status": "AVAILABLE", "value": turnover * 0.6},
            {"market": "TWO", "status": "AVAILABLE", "value": turnover * 0.4},
            {"market": "TOTAL", "status": "AVAILABLE", "value": turnover},
        ]
    return {
        "dataDate": TARGET,
        "indices": rows,
        "turnover": turnover_rows,
        "marketHealth": {
            "status": "AVAILABLE",
            "breadthEligible": positive + negative + flat,
            "advance": positive,
            "decline": negative,
            "flat": flat,
        },
    }


def signal(result: list[dict], signal_id: str) -> dict:
    return next(item for item in result if item["signalId"] == signal_id)


def prior_sessions(overviews: list[dict]) -> list[dict]:
    return [
        {"tradingDate": TARGET - timedelta(days=index + 1), "marketOverview": overview}
        for index, overview in enumerate(overviews)
    ]


def test_frozen_catalog_has_sixteen_signals_and_no_legacy_otc_signal():
    assert len(SIGNAL_CATALOG) == 16
    assert len(catalog_payload()) == 16
    assert "OTC_VOLUME_PRICE_DIVERGENCE" not in {item["signalId"] for item in SIGNAL_CATALOG}


def test_every_signal_has_signal_specific_frequency_band_templates():
    for item in catalog_payload():
        signal_id = item["signalId"]
        bands = item["frequencyBands"]
        for index, band_spec in enumerate(bands):
            count = band_spec["minimum"]
            band, message = _frequency(count, signal_id)
            assert band == band_spec["band"]
            assert f"{count}" in message
            assert message.startswith("近20日")
            if band_spec["maximum"] is not None and index + 1 < len(bands):
                next_count = band_spec["maximum"] + 1
                next_band, next_message = _frequency(next_count, signal_id)
                assert next_band == bands[index + 1]["band"]
                assert f"{next_count}" in next_message


def test_index_precedence_and_boundaries():
    divergence = evaluate_v1_signals(index_overview(0.6, -0.6), trading_date=TARGET)
    assert signal(divergence, "INDEX_MARKET_DIVERGENCE")["isActive"] is True
    assert signal(divergence, "INDEX_BOTH_STRONG")["isActive"] is False
    assert signal(divergence, "INDEX_BOTH_WEAK")["isActive"] is False

    exact_spread = evaluate_v1_signals(index_overview(1.5, 0.5), trading_date=TARGET)
    assert signal(exact_spread, "INDEX_MARKET_DIVERGENCE")["isActive"] is True

    strong = evaluate_v1_signals(index_overview(0.6, 0.5), trading_date=TARGET)
    assert signal(strong, "INDEX_BOTH_STRONG")["isActive"] is True

    weak = evaluate_v1_signals(index_overview(-0.5, -0.5), trading_date=TARGET)
    assert signal(weak, "INDEX_BOTH_WEAK")["isActive"] is True

    quiet = evaluate_v1_signals(index_overview(0.1, 0.1), trading_date=TARGET)
    assert not any(signal(quiet, key)["isActive"] for key in ("INDEX_MARKET_DIVERGENCE", "INDEX_BOTH_STRONG", "INDEX_BOTH_WEAK"))


def test_breadth_boundaries_and_overlap():
    broad = evaluate_v1_signals(index_overview(0.0, 0.0, positive=70, negative=20, flat=10), trading_date=TARGET)
    assert signal(broad, "BREADTH_BROAD_ADVANCE")["isActive"] is True

    declining = evaluate_v1_signals(index_overview(0.0, 0.0, positive=30, negative=60, flat=10), trading_date=TARGET)
    assert signal(declining, "BREADTH_DECLINERS_DOMINATE")["isActive"] is True

    disconnect = evaluate_v1_signals(index_overview(0.3, 0.0, positive=40, negative=60, flat=0), trading_date=TARGET)
    assert signal(disconnect, "BREADTH_RED_INDEX_DISCONNECT")["isActive"] is True
    assert signal(disconnect, "BREADTH_DECLINERS_DOMINATE")["isActive"] is True

    previous = index_overview(0.0, 0.0, positive=35, negative=35, flat=30)
    expanded = evaluate_v1_signals(
        index_overview(0.0, 0.0, positive=50, negative=50, flat=0),
        history=prior_sessions([previous]),
        trading_date=TARGET,
    )
    assert signal(expanded, "BREADTH_UPSIDE_EXPANSION")["isActive"] is True
    assert signal(expanded, "BREADTH_DOWNSIDE_EXPANSION")["isActive"] is True


def topic_rows(values: list[float], *, member_count: int = 4) -> list[dict]:
    rows = []
    for topic_index, value in enumerate(values):
        for _member_index in range(member_count):
            rows.append(
                {
                    "topic_id": f"topic-{topic_index}",
                    "topic_slug": f"topic-{topic_index}",
                    "snapshot_date": TARGET,
                    "formal_member_count": member_count,
                    "structural_role": "CORE",
                    "fact_state": "OBSERVED",
                    "change_pct": value,
                }
            )
    return rows


def test_topic_signal_boundaries_exclude_small_samples_and_are_not_score_driven():
    exact_share = evaluate_v1_signals(
        index_overview(0.0, 0.0), topic_observations=topic_rows([1.0, 1.0, 1.0, 1.0, 1.7142857143]), trading_date=TARGET
    )
    assert signal(exact_share, "TOPIC_CONCENTRATION")["isActive"] is True

    ratio = evaluate_v1_signals(
        index_overview(0.0, 0.0), topic_observations=topic_rows([1.0, 1.0, 1.0, 0.5, 0.5]), trading_date=TARGET
    )
    assert signal(ratio, "TOPIC_EXPANSION")["isActive"] is True

    not_evaluable = evaluate_v1_signals(
        index_overview(0.0, 0.0), topic_observations=topic_rows([1.0, 1.0, 1.0, 1.0, 1.0], member_count=2), trading_date=TARGET
    )
    assert signal(not_evaluable, "TOPIC_CONCENTRATION")["signalStatus"] == "NOT_EVALUABLE"

    dispersion = evaluate_v1_signals(
        index_overview(0.0, 0.0),
        topic_observations=topic_rows([-1.0, -1.0, -1.0, 0.0, 0.0, 1.0, 1.0, 1.5, 1.5]),
        trading_date=TARGET,
    )
    dispersion_signal = signal(dispersion, "TOPIC_DISPERSION")
    assert dispersion_signal["isActive"] is True
    assert dispersion_signal["evidenceDetail"]["topicDispersionIqr"] == 2.0


def test_turnover_uses_twenty_prior_sessions_and_excludes_current_day():
    history = [
        {"tradingDate": TARGET - timedelta(days=index + 1), "marketOverview": index_overview(0.6, 0.6, turnover=100.0)}
        for index in range(20)
    ]
    result = evaluate_v1_signals(index_overview(0.6, 0.6, turnover=115.0), history=history, trading_date=TARGET)
    assert signal(result, "MARKET_VOLUME_PRICE_ADVANCE")["isActive"] is True

    short = evaluate_v1_signals(index_overview(0.6, 0.6, turnover=115.0), history=history[:19], trading_date=TARGET)
    assert signal(short, "MARKET_VOLUME_PRICE_ADVANCE")["signalStatus"] == "NOT_EVALUABLE"

    divergent = evaluate_v1_signals(index_overview(0.6, -0.6, turnover=115.0), history=history, trading_date=TARGET)
    assert signal(divergent, "MARKET_VOLUME_PRICE_ADVANCE")["isActive"] is False
    assert signal(divergent, "MARKET_VOLUME_PRICE_DECLINE")["isActive"] is False

    tpe_only = index_overview(0.6, 0.6, turnover=115.0)
    tpe_only["turnover"] = [
        {"market": "TPE", "status": "AVAILABLE", "value": 115.0},
        {"market": "TOTAL", "status": "AVAILABLE", "value": 115.0},
    ]
    assert signal(evaluate_v1_signals(tpe_only, history=history, trading_date=TARGET), "MARKET_VOLUME_PRICE_ADVANCE")["signalStatus"] == "NOT_EVALUABLE"


def institutional_overview(foreign: float, trust: float) -> dict:
    overview = index_overview(0.0, 0.0, turnover=10_000)
    overview["institutionFlows"] = {
        "status": "AVAILABLE",
        "markets": [
            {"market": market, "asOfDate": TARGET, "availability": "AVAILABLE", "current": {"foreign": {"net": foreign / 2}, "investmentTrust": {"net": trust / 2}}}
            for market in ("TPE", "TWO")
        ],
    }
    return overview


def test_institutional_ratio_boundaries_and_fail_closed_exchange_authority():
    support = evaluate_v1_signals(institutional_overview(20, 20), trading_date=TARGET)
    assert signal(support, "INSTITUTIONAL_SUPPORT")["isActive"] is True

    headwind = evaluate_v1_signals(institutional_overview(-20, -20), trading_date=TARGET)
    assert signal(headwind, "INSTITUTIONAL_HEADWIND")["isActive"] is True

    divergence = evaluate_v1_signals(institutional_overview(20, -5), trading_date=TARGET)
    assert signal(divergence, "INSTITUTIONAL_DIVERGENCE")["isActive"] is True

    quiet = evaluate_v1_signals(institutional_overview(5, -5), trading_date=TARGET)
    assert signal(quiet, "INSTITUTIONAL_DIVERGENCE")["isActive"] is False

    missing = institutional_overview(20, 20)
    missing["institutionFlows"]["markets"] = missing["institutionFlows"]["markets"][:1]
    result = evaluate_v1_signals(missing, trading_date=TARGET)
    assert signal(result, "INSTITUTIONAL_SUPPORT")["signalStatus"] == "NOT_EVALUABLE"


def test_temporal_state_and_twenty_session_occurrence_are_explicit():
    active = index_overview(0.6, 0.6)
    inactive = index_overview(0.0, 0.0)
    new = evaluate_v1_signals(active, history=prior_sessions([inactive]), trading_date=TARGET)
    assert signal(new, "INDEX_BOTH_STRONG")["signalTemporalStatus"] == "NEW"
    assert signal(new, "INDEX_BOTH_STRONG")["streakDays"] == 1

    persisting = evaluate_v1_signals(active, history=prior_sessions([active]), trading_date=TARGET)
    assert signal(persisting, "INDEX_BOTH_STRONG")["signalTemporalStatus"] == "PERSISTING"
    assert signal(persisting, "INDEX_BOTH_STRONG")["streakDays"] == 2

    long_history = [
        {"tradingDate": TARGET - timedelta(days=index + 1), "marketOverview": active if index % 2 == 0 else inactive}
        for index in range(19)
    ]
    occurrence = evaluate_v1_signals(active, history=long_history, trading_date=TARGET)
    both_strong = signal(occurrence, "INDEX_BOTH_STRONG")
    assert both_strong["frequencyStatus"] == "AVAILABLE"
    assert both_strong["occurrenceDays20d"] == 11
    assert both_strong["frequencyMessage"].startswith("近20日發生 11 日")

    no_prior = evaluate_v1_signals(active, trading_date=TARGET)
    assert signal(no_prior, "INDEX_BOTH_STRONG")["signalTemporalStatus"] == "INSUFFICIENT_HISTORY"
    assert signal(no_prior, "INDEX_BOTH_STRONG")["signalTemporalStatus"] != "NEW"

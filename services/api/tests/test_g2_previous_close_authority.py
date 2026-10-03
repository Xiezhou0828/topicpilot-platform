"""Synthetic prices only; readiness is not a production execution claim."""

import json
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal

import pytest
from infra.scripts.replay_target_universe_readiness import replay_market

from topicpilot_api import home_read_model
from topicpilot_api.corporate_action_authority import corporate_action_authorities_for
from topicpilot_api.previous_close_authority import (
    G2PriceEvidence,
    PreviousCloseEvidence,
    previous_session_date,
)
from topicpilot_api.provider_preflight import (
    G2MarketContext,
    G2MarketFetch,
    G2PreflightContext,
    evaluate_provider_preflight,
)
from topicpilot_api.trading_status_authority import resolve_effective_trading_status

DAY = date(2026, 10, 2)
PRIOR = date(2026, 10, 1)


def comparator(market="TPE", code="2330", **changes):
    return replace(
        PreviousCloseEvidence(
            f"{market}:{code}",
            market,
            code,
            PRIOR,
            Decimal("9"),
            "TWSE_OFFICIAL_DAILY" if market == "TPE" else "TPEX_OFFICIAL_DAILY",
            "FORMAL_CANONICAL_CLOSE",
            "fabricated-test-canonical-lineage",
        ),
        **changes,
    )


def gate(*, markets=None, prices=None, statuses=None, prior=PRIOR):
    codes_by_market = markets or {"TPE": ("2330",)}
    contexts, results = [], {}
    for market, codes in codes_by_market.items():
        source = "TWSE_OFFICIAL_DAILY" if market == "TPE" else "TPEX_OFFICIAL_DAILY"
        version = "twse-official-daily.v2" if market == "TPE" else "tpex-official-daily.v2"
        contexts.append(
            G2MarketContext(
                market,
                source,
                version,
                "TWSE" if market == "TPE" else "TPEx",
                "Asia/Taipei",
                "TW_MARKET",
                codes,
                {c: f"{market}:{c}" for c in codes},
            )
        )
        selected = {
            c: G2PriceEvidence(
                f"{market}:{c}", market, c, DAY, 10, "a" * 64, formal_previous=comparator(market, c)
            )
            for c in codes
        }
        if prices is not None:
            selected = {c: p for c, p in prices.items() if p.market_code == market}
        results[market] = G2MarketFetch(
            market,
            source,
            version,
            DAY,
            frozenset(selected),
            len(selected),
            prices=selected,
            statuses={f"{market}:{c}": status for c, status in (statuses or {}).items()},
        )
    context = G2PreflightContext(
        {"referenceLoadStatus": "READY"}, DAY, True, None, tuple(contexts), previous_session=prior
    )
    return evaluate_provider_preflight(context, results)


def test_prior_formal_close_retains_price_free_complete_lineage():
    result = gate()
    assert result["status"] == "PASS"
    decision = result["markets"][0]["instrumentDecisions"][0]
    assert decision["closeValid"] and decision["previousCloseValid"]
    assert decision["previousClose"] == comparator().price_free_metadata()
    assert "value" not in decision["previousClose"]
    assert not decision["syntheticOrFillUsed"]


def test_explicit_same_day_provider_previous_close_without_formal_history():
    proof = comparator(
        authority="PROVIDER_EXPLICIT_PREVIOUS_CLOSE", payload_date=DAY, lineage="a" * 64
    )
    price = G2PriceEvidence("TPE:2330", "TPE", "2330", DAY, 10, "a" * 64, proof)
    assert gate(prices={"2330": price})["status"] == "PASS"


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"value": 0}, "PREVIOUS_CLOSE_INVALID"),
        ({"value": None}, "PREVIOUS_CLOSE_INVALID"),
        ({"value": ""}, "PREVIOUS_CLOSE_INVALID"),
        ({"value": Decimal("NaN")}, "PREVIOUS_CLOSE_INVALID"),
        ({"value": float("inf")}, "PREVIOUS_CLOSE_INVALID"),
        ({"instrument_id": "TPE:OTHER"}, "PREVIOUS_CLOSE_IDENTITY_MISMATCH"),
        ({"instrument_code": "OTHER"}, "PREVIOUS_CLOSE_IDENTITY_MISMATCH"),
        ({"market_code": "TWO"}, "PREVIOUS_CLOSE_IDENTITY_MISMATCH"),
        ({"as_of_date": date(2026, 9, 30)}, "PREVIOUS_CLOSE_DATE_MISMATCH"),
        ({"as_of_date": DAY}, "PREVIOUS_CLOSE_DATE_MISMATCH"),
        ({"source": "SHADOW"}, "PREVIOUS_CLOSE_AUTHORITY_INVALID"),
        ({"source": "RESEARCH"}, "PREVIOUS_CLOSE_AUTHORITY_INVALID"),
        ({"authority": "SYNTHETIC"}, "PREVIOUS_CLOSE_AUTHORITY_INVALID"),
        ({"quality_state": "INCOMPLETE"}, "PREVIOUS_CLOSE_AUTHORITY_INVALID"),
        ({"lineage": ""}, "PREVIOUS_CLOSE_AUTHORITY_INVALID"),
        (
            {"authority": "PROVIDER_EXPLICIT_PREVIOUS_CLOSE", "payload_date": PRIOR},
            "PREVIOUS_CLOSE_PAYLOAD_DATE_MISMATCH",
        ),
    ],
)
def test_invalid_comparator_is_rejected_without_filling(changes, reason):
    price = G2PriceEvidence(
        "TPE:2330", "TPE", "2330", DAY, 10, "a" * 64, formal_previous=comparator(**changes)
    )
    result = gate(prices={"2330": price})
    assert result["status"] == "FAIL"
    assert result["markets"][0]["instrumentDecisions"][0]["errorCode"] == reason


def test_missing_prior_formal_close_and_invalid_explicit_value_fail_closed():
    price = G2PriceEvidence("TPE:2330", "TPE", "2330", DAY, 10, "a" * 64)
    assert gate(prices={"2330": price})["status"] == "FAIL"
    invalid_explicit = comparator(
        value=0, authority="PROVIDER_EXPLICIT_PREVIOUS_CLOSE", payload_date=DAY
    )
    price = replace(price, provider_previous=invalid_explicit, formal_previous=comparator())
    assert gate(prices={"2330": price})["status"] == "FAIL"


@pytest.mark.parametrize(
    "changes",
    [
        {"close": 0},
        {"close": None},
        {"close": ""},
        {"close": Decimal("NaN")},
        {"trading_date": PRIOR},
        {"instrument_id": "wrong"},
        {"response_hash": ""},
    ],
)
def test_invalid_current_close_cannot_borrow_a_previous_price(changes):
    price = G2PriceEvidence(
        "TPE:2330", "TPE", "2330", DAY, 10, "a" * 64, formal_previous=comparator()
    )
    result = gate(prices={"2330": replace(price, **changes)})
    assert result["status"] == "FAIL"
    assert result["markets"][0]["priceCandidateCount"] == 0


def suspension():
    records = tuple(
        a.to_trading_status_record()
        for a in corporate_action_authorities_for(symbol="2601", market="TPE", trading_date=DAY)
    )
    return resolve_effective_trading_status("TPE:2601", DAY, official_authority=records)


def test_tpe_two_552_prices_plus_one_official_unavailable_accounts_for_553():
    # Explicit synthetic counts; actual persisted identities remain in the retained audit.
    markets = {
        "TPE": tuple([f"T{i}" for i in range(346)] + ["2601"]),
        "TWO": tuple(f"O{i}" for i in range(206)),
    }
    prices = {
        c: G2PriceEvidence(f"{m}:{c}", m, c, DAY, 10, "a" * 64, formal_previous=comparator(m, c))
        for m, codes in markets.items()
        for c in codes
        if c != "2601"
    }
    resolution = suspension()
    assert resolution.status == "SUSPENDED" and resolution.is_legitimate_unavailable
    assert resolution.authority_source == "TWSE_OFFICIAL_REDUCTION"
    result = gate(markets=markets, prices=prices, statuses={"2601": resolution})
    assert result["status"] == "PASS"
    tpe, two = result["markets"]
    assert (
        tpe["priceCandidateCount"],
        tpe["legitimateUnavailableCount"],
        tpe["accountedTargetCount"],
    ) == (346, 1, 347)
    assert (two["priceCandidateCount"], two["previousCloseCoveredCount"]) == (206, 206)
    assert sum(m["accountedTargetCount"] for m in result["markets"]) == 553
    assert tpe["previousCloseCoveredCount"] == 346


@pytest.mark.parametrize("kind", ["missing", "unknown", "provider", "ungoverned", "expired"])
def test_unresolved_or_invalid_unavailable_status_stays_blocking(kind):
    status = suspension()
    if kind == "missing":
        status = resolve_effective_trading_status("TPE:2601", DAY)
    elif kind == "unknown":
        status = replace(
            status, status="UNKNOWN", blocks_publication=True, is_legitimate_unavailable=False
        )
    elif kind == "provider":
        status = resolve_effective_trading_status("TPE:2601", DAY, provider_failure=True)
    elif kind == "ungoverned":
        status = replace(status, authority_class="MANUAL_GOVERNED")
    else:
        status = replace(status, effective_to=PRIOR)
    result = gate(markets={"TPE": ("2601",)}, prices={}, statuses={"2601": status})
    assert result["status"] == "FAIL"
    assert result["markets"][0]["legitimateUnavailableCount"] == 0


def test_calendar_uses_exact_official_prior_session_not_last_observed_price():
    assert previous_session_date(DAY, ()) == PRIOR
    assert previous_session_date(date(2026, 10, 5), ()) == DAY
    assert previous_session_date(DAY, {PRIOR}) == date(2026, 9, 30)
    with pytest.raises(ValueError):
        previous_session_date(DAY, {DAY.fromordinal(DAY.toordinal() - n) for n in range(1, 367)})


@pytest.mark.parametrize("market", ["TPE", "TWO"])
def test_explicit_provider_field_reaches_g2_with_response_hash_and_date(market):
    from uuid import NAMESPACE_URL, uuid5

    code = "2330" if market == "TPE" else "6510"
    identity = str(uuid5(NAMESPACE_URL, f"synthetic-test:{market}:{code}"))
    source = "TWSE_OFFICIAL_DAILY" if market == "TPE" else "TPEX_OFFICIAL_DAILY"
    version = "twse-official-daily.v2" if market == "TPE" else "tpex-official-daily.v2"
    row = (
        [code, "Synthetic", "1000", "0", "10000", "10", "11", "9", "10"]
        if market == "TPE"
        else [code, "Synthetic", "10", "0", "10", "11", "9", "10000", "1000"]
    )
    fields = ["證券代號" if market == "TPE" else "代號", *["unused"] * 8, "previousClose"]
    raw = json.dumps(
        {
            "stat": "OK" if market == "TPE" else "ok",
            "date": "20261002",
            "tables": [
                {
                    "title": "上櫃股票行情" if market == "TWO" else "synthetic",
                    "fields": fields,
                    "data": [[*row, "9"]],
                }
            ],
        }
    ).encode()
    targets = [[market, code, identity, None, "ELIGIBLE", source, version, False, None, False]]
    result = replay_market(raw, targets, market, DAY)
    assert result["g2ProviderRowGateStatus"] == "PASS"
    proof = result["g2AuthorityEvidence"]["instrumentDecisions"][0]["previousClose"]
    assert proof["authority"] == "PROVIDER_EXPLICIT_PREVIOUS_CLOSE"
    assert proof["asOfDate"] == "2026-10-01"
    assert proof["payloadDate"] == "2026-10-02"
    assert proof["lineage"] == result["payloadSha256"]


def test_explicit_previous_close_must_belong_to_same_response():
    proof = comparator(
        authority="PROVIDER_EXPLICIT_PREVIOUS_CLOSE", payload_date=DAY, lineage="b" * 64
    )
    price = G2PriceEvidence("TPE:2330", "TPE", "2330", DAY, 10, "a" * 64, proof)
    result = gate(prices={"2330": price})
    assert result["status"] == "FAIL"
    assert result["markets"][0]["instrumentDecisions"][0]["errorCode"] == (
        "PREVIOUS_CLOSE_PAYLOAD_LINEAGE_MISMATCH"
    )


def test_daily_comparator_sql_is_exact_date_authority_bound_and_select_only():
    from topicpilot_api.daily_market import read_daily_market_rows

    class Rows:
        def mappings(self):
            return self

        def all(self):
            return []

    class Session:
        def execute(self, query, params):
            self.query, self.params = str(query), params
            return Rows()

    session = Session()
    assert read_daily_market_rows(session, DAY) == []
    assert "prior.trade_date = (SELECT trade_date FROM previous_session)" in session.query
    assert "prior.close > 0 AND prior.quality_state = 'ACCEPTED'" in session.query
    assert "reference_calendar_dates" in session.query
    assert "previous.canonical_observation_id AS previous_close_lineage" in session.query
    assert "LEFT JOIN prior_price previous ON previous.instrument_id = u.id" in session.query
    assert "prior.trade_date < d.trade_date" not in session.query
    assert session.params["trade_date"] == DAY
    assert not any(word in session.query for word in ("INSERT ", "UPDATE ", "DELETE "))


@pytest.mark.parametrize(
    "prior_date,expected", [(PRIOR, "PASS"), (date(2026, 9, 30), "FAIL"), (None, "FAIL")]
)
def test_runtime_preflight_uses_formal_prior_before_any_current_row_exists(
    monkeypatch, prior_date, expected
):
    from uuid import uuid4

    import topicpilot_api.daily_market as daily
    import topicpilot_api.provider_preflight as module
    import topicpilot_api.trading_status_authority as authority

    identity = str(uuid4())
    market = G2MarketContext(
        "TPE",
        "TWSE_OFFICIAL_DAILY",
        "twse-official-daily.v2",
        "TWSE",
        "Asia/Taipei",
        "TW_MARKET",
        ("2330",),
        {"2330": identity},
    )
    context = G2PreflightContext(
        {"referenceLoadStatus": "READY"}, DAY, True, None, (market,), previous_session=PRIOR
    )
    monkeypatch.setattr(module, "load_g2_preflight_context", lambda *_a, **_kw: context)
    rows = [
        {
            "market": "TPE",
            "symbol": "2330",
            "instrument_id": identity,
            "close": None,
            "previous_close_instrument_id": identity,
            "previous_close_date": prior_date,
            "previous_close": Decimal("9"),
            "previous_close_source": "TWSE_OFFICIAL_DAILY",
            "previous_close_lineage": "test-prior-canonical-row" if prior_date else None,
            "previous_close_quality": "ACCEPTED",
        }
    ]
    monkeypatch.setattr(daily, "read_daily_market_rows", lambda *_a, **_kw: rows)
    monkeypatch.setattr(authority, "read_effective_trading_status_authority", lambda *_a, **_kw: [])
    calls = []

    def transport(url, _timeout):
        calls.append(url)
        return json.dumps(
            {
                "stat": "OK",
                "date": "20261002",
                "tables": [
                    {
                        "fields": ["證券代號"],
                        "data": [
                            ["2330", "Synthetic", "1000", "0", "10000", "10", "11", "9", "10"]
                        ],
                    }
                ],
            }
        ).encode()

    result = module.run_provider_preflight(object(), target_date=DAY, transport=transport)
    assert result["status"] == expected and len(calls) == 1
    assert result["readOnly"] and result["productionWriteSet"] == []
    decision = result["markets"][0]["instrumentDecisions"][0]
    assert decision["closeValid"]
    assert decision["previousCloseValid"] is (expected == "PASS")


@pytest.mark.parametrize(
    "now,completed",
    [
        ("2026-10-02T18:00:00+08:00", DAY),
        ("2026-10-03T12:00:00+08:00", DAY),
        ("2026-10-04T12:00:00+08:00", DAY),
        ("2026-10-05T08:00:00+08:00", DAY),
        ("2026-10-05T12:00:00+08:00", DAY),
        ("2026-10-05T18:00:00+08:00", date(2026, 10, 5)),
    ],
)
def test_home_date_stays_on_latest_completed_publication_not_comparator(
    monkeypatch, now, completed
):
    # Publication completion is an input; no writer or clock-triggered Home is created here.
    seen = []
    payload = {
        "publication": {"tradingDate": completed},
        "marketOverview": {"dataDate": completed, "indices": [{"value": 10, "previousClose": 9}]},
    }
    monkeypatch.setattr(home_read_model, "latest_canonical_trading_date", lambda _: completed)

    def read(_, *, trading_date):
        seen.append(trading_date)
        return payload

    monkeypatch.setattr(home_read_model, "read_latest_home_publication", read)

    class Session:
        def execute(self, _):
            return None

    result = home_read_model.build_home_read_model(Session(), datetime.fromisoformat(now))
    assert result is payload and seen == [completed]
    assert result["publication"]["tradingDate"] != previous_session_date(completed, ())

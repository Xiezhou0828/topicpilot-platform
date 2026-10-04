"""Owner-accepted scope reconstruction; fixtures/fake sessions are synthetic only."""

import hashlib
import json
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from topicpilot_api import home_v2_publication as home
from topicpilot_api.market_data.index_contract import (
    TWSE_MARKET_INDEX_ADAPTER_VERSION,
    TWSE_MARKET_INDEX_ENDPOINT,
    IndexDataStatus,
    fetch_official_market_indexes,
    parse_twse_target_date_market_index,
)
from topicpilot_api.orm import HomeMarketFact, HomePublication
from topicpilot_api.schemas import HomeResponse

DAY = date(2026, 10, 2)
NOW = datetime(2026, 10, 2, 10, tzinfo=UTC)
FIXTURE = Path(__file__).parent / "fixtures/market_index/task025_twse_target_date_synthetic.json"


def payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def fetch(close_payload=None, *, ohlc=True):
    """Inject every response; never send HTTP requests or call the run orchestrator."""
    raw_close = json.dumps(payload() if close_payload is None else close_payload).encode()
    raw_ohlc = json.dumps(
        {
            "fixtureClassification": "TEST_ONLY_SYNTHETIC_NOT_MARKET_DATA",
            "data": [["115/10/02", "100", "105", "95", "100"]] if ohlc else [],
        }
    ).encode()
    calls = []

    def transport(url, _timeout):
        calls.append(url)
        if "afterTrading/MI_INDEX" in url:
            return raw_close
        if "MI_5MINS_HIST" in url:
            return raw_ohlc
        if "tpex_index" in url:
            return b"[]"
        raise AssertionError("UNAPPROVED_ENDPOINT")

    result = fetch_official_market_indexes(
        target_date=DAY,
        retrieved_at=NOW,
        as_of=NOW,
        transport=transport,
    )[0]
    return result, calls, raw_close, raw_ohlc


@pytest.mark.parametrize(
    "sign,magnitude,previous", [("+", "2", "98"), ("-", "2", "102"), ("", "0", "100")]
)
def test_target_date_fixture_retains_signed_change_derivation(sign, magnitude, previous):
    body = payload()
    body["tables"][0]["data"][0][2:4] = [sign, magnitude]
    result = parse_twse_target_date_market_index(
        body,
        target_date=DAY,
        retrieved_at=NOW,
        as_of=NOW,
    )
    assert result.data_status is IndexDataStatus.AVAILABLE
    assert result.trading_date == result.target_date == result.response_date == DAY
    assert result.previous_close == Decimal(previous)
    assert (result.open, result.high, result.low) == (None, None, None)


@pytest.mark.parametrize("response_date", ["20261001", "20261005"])
def test_mismatch_is_not_rescued_by_matching_ohlc_or_undated_fallback(response_date):
    body = payload()
    body["date"] = response_date
    fact, calls, raw, _ = fetch(body)
    assert fact.data_status is IndexDataStatus.UNAVAILABLE
    assert fact.status_reason == "PROVIDER_DATE_MISMATCH"
    assert all(
        getattr(fact, key) is None for key in ("value", "previous_close", "open", "high", "low")
    )
    assert fact.target_date == DAY
    assert fact.response_date == date.fromisoformat(
        f"{response_date[:4]}-{response_date[4:6]}-{response_date[6:]}"
    )
    assert fact.response_content_hash == hashlib.sha256(raw).hexdigest()
    assert len(calls) == 3 and len(set(calls)) == 3
    assert not any("openapi.twse.com.tw" in url for url in calls)


@pytest.mark.parametrize("response_date", [None, "", "not-a-date"])
def test_missing_or_malformed_response_date_fails_closed(response_date):
    body = payload()
    body["date"] = response_date
    fact, *_ = fetch(body)
    assert fact.data_status is IndexDataStatus.UNAVAILABLE
    assert fact.target_date == DAY and fact.response_date is None
    assert fact.value is None and fact.previous_close is None


def test_fetch_retains_dated_endpoints_raw_response_hashes_and_adapter_versions():
    fact, calls, raw_close, raw_ohlc = fetch()
    assert fact.data_status is IndexDataStatus.AVAILABLE
    assert fact.previous_close == Decimal("98")
    assert (fact.open, fact.high, fact.low) == (100, 105, 95)
    assert calls[0] == f"{TWSE_MARKET_INDEX_ENDPOINT}?date=20261002&type=IND&response=json"
    assert "date=20261002" in calls[1]
    first, second = fact.to_dict()["providerResponses"]
    assert first == {
        "endpoint": calls[0],
        "targetDate": "2026-10-02",
        "responseDate": "2026-10-02",
        "rawProviderDate": "20261002",
        "responseHash": hashlib.sha256(raw_close).hexdigest(),
        "adapterVersion": TWSE_MARKET_INDEX_ADAPTER_VERSION,
    }
    assert second["endpoint"] == calls[1]
    assert second["responseDate"] == "2026-10-02"
    assert second["responseHash"] == hashlib.sha256(raw_ohlc).hexdigest()
    expected = hashlib.sha256(
        f"{first['responseHash']}:{second['responseHash']}".encode()
    ).hexdigest()
    assert fact.response_content_hash == expected


def test_missing_ohlc_stays_null_with_official_close_and_provenance():
    fact, _, raw, _ = fetch(ohlc=False)
    assert fact.data_status is IndexDataStatus.AVAILABLE
    assert (fact.value, fact.previous_close) == (100, 98)
    assert (fact.open, fact.high, fact.low) == (None, None, None)
    assert fact.response_content_hash == hashlib.sha256(raw).hexdigest()
    assert len(fact.provider_responses) == 2


@pytest.mark.parametrize("invalid", [None, 0, -1, "", Decimal("NaN"), Decimal("Infinity")])
def test_distribution_never_invents_a_missing_current_or_previous_price(invalid):
    rows = [
        {"instrument_id": "valid", "status_code": "NORMAL", "close": 10, "previous_close": 9},
        {
            "instrument_id": "bad-close",
            "status_code": "NORMAL",
            "close": invalid,
            "previous_close": 9,
        },
        {
            "instrument_id": "bad-prior",
            "status_code": "NORMAL",
            "close": 10,
            "previous_close": invalid,
        },
        {
            "instrument_id": "suspended",
            "status_code": "SUSPENDED",
            "close": None,
            "previous_close": 9,
        },
    ]
    before = repr(rows)
    result = home.build_market_distribution(rows, eligible_count=4, as_of=NOW)
    assert repr(rows) == before
    assert result["eligible"] == 1 and result["excluded"] == 3
    assert result["coverage"]["scope"] == "COVERED_STOCKS"
    assert result["coverage"]["distributionDenominator"] == "COMPLETE_CLOSE_PREVIOUS_CLOSE"
    assert result["coverage"]["eligibleUniverse"] == 4
    assert result["coverage"]["coveragePct"] == 25
    assert sum(bucket["count"] for bucket in result["buckets"]) == 1


class CaptureSession:
    """In-memory object sink, not a SQL/DB/session connection."""

    def __init__(self):
        self.items = []

    def scalar(self, *_a, **_kw):
        return None

    def add(self, item):
        item.id = uuid4()
        self.items.append(item)

    def flush(self):
        pass

    def commit(self):
        pass

    def execute(self, *_a, **_kw):
        raise AssertionError("SQL_FORBIDDEN_IN_THIS_TEST")


def capture_home(monkeypatch, *, fact=None):
    observations = [
        {
            "instrument_id": "synthetic-price",
            "symbol": "SYNTH",
            "market": "TPE",
            "status_code": "NORMAL",
            "close": Decimal("10"),
            "previous_close": Decimal("9"),
        },
        {
            "instrument_id": "synthetic-unavailable",
            "symbol": "2601",
            "market": "TPE",
            "status_code": "SUSPENDED",
            "close": None,
            "previous_close": None,
        },
    ]
    monkeypatch.setattr(home, "_breadth", lambda *_: ([], NOW, observations))
    for name in ("_formal_topic_rows", "_formal_topic_history", "_read_formal_topic_signal_rows"):
        monkeypatch.setattr(home, name, lambda *_: [])
    monkeypatch.setattr(home, "_signal_history_with_authority", lambda *_a, **_kw: [])
    monkeypatch.setattr(home, "_read_home_institutional_flow", lambda *_: None)
    monkeypatch.setattr(home, "_read_previous_session_turnover", lambda *_: None)
    aggregates = [
        {
            "market": market,
            "status": "AVAILABLE",
            "eligible": 1000,
            "observed": 1000,
            "advancers": 600,
            "decliners": 300,
            "unchanged": 100,
            "unavailable": 0,
            "asOf": NOW,
            "tradingDate": DAY,
            "turnover": 100,
            "currency": "TWD",
            "turnoverUnit": "TWD",
            "turnoverScale": 1,
        }
        for market in ("TPE", "TWO")
    ]
    session = CaptureSession()
    home.materialize_home_v2(
        session,
        trading_date=DAY,
        now=NOW,
        market_aggregate_facts=aggregates,
        market_index_facts=[fact] if fact else [],
    )
    publication = next(item for item in session.items if isinstance(item, HomePublication))
    return session, publication


def test_distribution_population_never_borrows_official_whole_market_breadth(monkeypatch):
    _, publication = capture_home(monkeypatch)
    overview = publication.payload["marketOverview"]
    assert overview["marketHealth"]["totalStocks"] == 2000
    distribution = overview["distribution"]
    assert distribution["coverage"]["eligibleUniverse"] == 2
    assert distribution["coverage"]["observedComplete"] == 1
    assert distribution["coverage"]["coveragePct"] == 50
    assert distribution["coverage"]["excludedCount"] == 1
    assert publication.trading_date == DAY
    HomeResponse.model_validate(publication.payload)


def test_index_provenance_survives_existing_json_persistence_and_affects_identity(monkeypatch):
    fact, *_ = fetch()
    session, publication = capture_home(monkeypatch, fact=fact)
    stored = next(
        item
        for item in session.items
        if isinstance(item, HomeMarketFact) and item.index_code == "TWSE:TAIEX"
    )
    proof = stored.coverage["providerProvenance"]
    assert proof["targetDate"] == proof["responseDate"] == "2026-10-02"
    assert proof["responseHash"] == fact.response_content_hash
    assert proof["adapterVersion"] == TWSE_MARKET_INDEX_ADAPTER_VERSION
    assert proof["providerResponses"] == fact.to_dict()["providerResponses"]
    assert stored.coverage["sourceEndpoint"] == fact.source_endpoint
    assert publication.payload["marketOverview"]["dataDate"] == "2026-10-02"
    assert publication.payload["marketOverview"]["indices"][0]["previousClose"] == 98
    _, changed = capture_home(monkeypatch, fact=replace(fact, response_content_hash="f" * 64))
    assert publication.source_dataset_id != changed.source_dataset_id

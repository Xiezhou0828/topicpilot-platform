from __future__ import annotations

import json
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from topicpilot_api.live.post_close import PostCloseUpdater
from topicpilot_api.market_data.institutional_flow_contract import (
    fetch_official_market_institutional_flows,
    persist_market_institutional_flows,
)

TARGET = date(2026, 10, 2)
AS_OF = datetime(2026, 10, 2, 8, tzinfo=UTC)


def _parsed_facts(*, invalid_market=None, failure=None):
    """Synthetic amounts through real official adapters; never fetch the network."""

    def transport(endpoint, _timeout):
        market = "TPE" if "twse.com.tw" in endpoint else "TWO"
        if market == invalid_market and failure == "transport":
            raise OSError("controlled provider failure")
        payload_date = "20261001" if market == invalid_market and failure == "date" else "20261002"
        if market == "TPE":
            payload = {
                "date": payload_date,
                "data": [
                    ["外資及陸資(不含外資自營商)", "100", "40", "60"],
                    ["投信", "20", "10", "10"],
                    ["自營商(自行買賣)", "30", "10", "20"],
                    ["自營商(避險)", "10", "20", "-10"],
                    ["合計", "160", "80", "80"],
                ],
            }
        else:
            payload = {
                "date": payload_date,
                "tables": [
                    {
                        "data": [
                            ["外資及陸資合計", "100", "40", "60"],
                            ["投信", "20", "10", "10"],
                            ["自營商合計", "40", "30", "10"],
                            ["三大法人合計", "160", "80", "80"],
                        ]
                    }
                ],
            }
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")

    return fetch_official_market_institutional_flows(
        target_date=TARGET,
        retrieved_at=AS_OF,
        as_of=AS_OF,
        transport=transport,
    )


def _rows(facts):
    return [
        {
            "market": fact.market,
            "trading_date": fact.trading_date,
            "availability": fact.availability,
            "source_identity": fact.source_identity,
        }
        for fact in facts
    ]


class _ReadbackSession:
    def __init__(self, rows):
        self.rows = rows
        self.rolled_back = False

    def execute(self, *_args, **_kwargs):
        return self

    def mappings(self):
        return self

    def all(self):
        return self.rows

    def scalar(self, _query):
        return SimpleNamespace(id="test-home", publication_state="PUBLISHED")

    def rollback(self):
        self.rolled_back = True


def _updater(session):
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = session
    updater._formal_snapshot_readback = lambda _date: {"status": "PASS", "rowCount": 2}
    return updater


def test_real_official_parsers_pass_flow_and_formal_publication_readback():
    facts = _parsed_facts()
    assert [(fact.market, fact.source_identity, fact.availability) for fact in facts] == [
        ("TPE", "TWSE_BFI82U", "AVAILABLE"),
        ("TWO", "TPEX_INSTI_SUMMARY", "AVAILABLE"),
    ]
    updater = _updater(_ReadbackSession(_rows(facts)))
    assert updater._institutional_flow_readback(TARGET)["status"] == "PASS"
    assert updater._formal_publication_readback(TARGET, run_id="test-run")["status"] == "PASS"


@pytest.mark.parametrize(
    "invalid",
    [
        "swapped",
        "missing_tpe",
        "missing_two",
        "date_tpe",
        "date_two",
        "unavailable_tpe",
        "unavailable_two",
        "unknown_tpe",
        "unknown_two",
    ],
)
def test_flow_source_alignment_preserves_fail_closed_publication_gate(invalid):
    rows = _rows(_parsed_facts())
    if invalid == "swapped":
        rows[0]["source_identity"], rows[1]["source_identity"] = (
            rows[1]["source_identity"],
            rows[0]["source_identity"],
        )
    else:
        action, market = invalid.split("_")
        index = 0 if market == "tpe" else 1
        if action == "missing":
            rows.pop(index)
        elif action == "date":
            rows[index]["trading_date"] = date(2026, 10, 1)
        elif action == "unavailable":
            rows[index]["availability"] = "SOURCE_UNAVAILABLE"
        else:
            rows[index]["source_identity"] = "UNKNOWN_SOURCE"
    updater = _updater(_ReadbackSession(rows))
    readback = updater._institutional_flow_readback(TARGET)
    assert readback["status"] == "FAIL"
    assert readback["reasonCode"] == "WHOLE_MARKET_INSTITUTIONAL_FLOW_NOT_READY"
    assert updater._formal_publication_readback(TARGET, run_id="test-run")["status"] == "FAIL"


@pytest.mark.parametrize("market", ["TPE", "TWO"])
@pytest.mark.parametrize("failure", ["date", "transport"])
def test_real_provider_failure_and_date_mismatch_remain_publication_blocking(market, failure):
    facts = _parsed_facts(invalid_market=market, failure=failure)
    invalid = next(fact for fact in facts if fact.market == market)
    assert invalid.availability == "SOURCE_UNAVAILABLE"
    assert invalid.status_reason == (
        "PROVIDER_DATE_MISMATCH" if failure == "date" else "PROVIDER_REQUEST_FAILED"
    )
    updater = _updater(_ReadbackSession(_rows(facts)))
    assert updater._institutional_flow_readback(TARGET)["status"] == "FAIL"
    assert updater._formal_publication_readback(TARGET, run_id="test-run")["status"] == "FAIL"


def test_flow_database_read_failure_keeps_distinct_classification():
    class BrokenSession(_ReadbackSession):
        def execute(self, *_args, **_kwargs):
            raise RuntimeError("controlled readback failure")

    session = BrokenSession([])
    readback = _updater(session)._institutional_flow_readback(TARGET)
    assert readback["status"] == "FAIL"
    assert readback["reasonCode"] == "INSTITUTIONAL_FLOW_READBACK_UNAVAILABLE"
    assert readback["error"] == "RuntimeError"
    assert session.rolled_back


def test_real_official_parser_persistence_and_postgres_readback(db_session):
    facts = _parsed_facts()
    result = persist_market_institutional_flows(db_session, facts, ingested_at=AS_OF)
    assert result == {"status": "SUCCESS", "persisted": 2, "available": 2}
    readback = _updater(db_session)._institutional_flow_readback(TARGET)
    assert readback["status"] == "PASS"
    assert readback["availableMarkets"] == ["TPE", "TWO"]
    assert [row["sourceIdentity"] for row in readback["markets"]] == [
        "TWSE_BFI82U",
        "TPEX_INSTI_SUMMARY",
    ]

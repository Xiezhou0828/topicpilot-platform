"""Synthetic parser inputs only; no real prices, sessions, or recovery execution."""

from __future__ import annotations

import inspect
import json
from datetime import date
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pytest
from infra.scripts.replay_target_universe_readiness import replay_market as offline_replay

from topicpilot_api.instrument_universe import (
    InstrumentLifecycle,
    InstrumentUniverseRow,
    build_date_effective_instrument_universe,
)
from topicpilot_api.previous_close_authority import PreviousCloseEvidence
from topicpilot_api.reference_data import load_bundle

DAY = date(2026, 10, 2)
ROOT = Path(__file__).resolve().parents[3]


def replay_market(raw, targets, market, day):
    # Only fabricated test comparators. Actual replay must supply governed evidence.
    previous = {r[1]: PreviousCloseEvidence(r[2], market, r[1], date.fromisoformat(r[8]),
        9, r[5], "FORMAL_CANONICAL_CLOSE", "synthetic-unit-test-canonical-row")
        for r in targets if r[7] and r[8]}
    return offline_replay(raw, targets, market, day, previous_closes=previous)


def target(market, code, *, prior=True, prior_date="2026-10-01"):
    return [
        market,
        code,
        str(uuid5(NAMESPACE_URL, f"synthetic-target:{market}:{code}")),
        None,
        "ELIGIBLE",
        "TWSE_OFFICIAL_DAILY" if market == "TPE" else "TPEX_OFFICIAL_DAILY",
        "twse-official-daily.v2" if market == "TPE" else "tpex-official-daily.v2",
        prior,
        prior_date if prior else None,
        False,
    ]


def payload(market, codes, *, null_close=(), stat=None, response_date="20261002"):
    """Deliberately fabricated unit-test OHLCV; never an official payload fixture."""
    rows = []
    for code in codes:
        close = "--" if code in null_close else "10"
        rows.append(
            [code, "Synthetic test only", "1000", "0", "10000", "10", "11", "9", close]
            if market == "TPE"
            else [code, "Synthetic test only", close, "0", "10", "11", "9", "10000", "1000"]
        )
    return json.dumps(
        {
            "stat": stat if stat is not None else "OK" if market == "TPE" else "ok",
            "date": response_date,
            "tables": [
                {
                    "title": "上櫃股票行情" if market == "TWO" else "Synthetic test",
                    "fields": ["證券代號" if market == "TPE" else "代號"],
                    "data": rows,
                }
            ],
        }
    ).encode()


@pytest.mark.parametrize("market", ["TPE", "TWO"])
def test_valid_target_coverage_uses_existing_parser_mapper_and_formal_model(market):
    result = replay_market(payload(market, ["2330"]), [target(market, "2330")], market, DAY)
    assert result["matchedTargets"] == result["targetCloseCount"] == 1
    assert result["acceptedPriceCandidates"] == 1
    assert result["formalCoverageModelReady"] is True
    assert result["productionReadinessProven"] is False
    assert result["canonicalObservationCreated"] is False
    assert len(result["stages"]) == 16
    assert result["stages"][14]["outputCount"] is None
    assert result["stages"][14]["status"] == "NOT_EXECUTED"
    assert result["stages"][0]["outputCount"] is None
    assert result["productionWriteSet"] == []


def test_non_ok_stat_with_valid_target_rows_remains_fail_closed_not_silently_bypassed():
    result = replay_market(
        payload("TPE", ["2330"], stat="not-ready"), [target("TPE", "2330")], "TPE", DAY
    )
    assert result["providerRawStat"] == "not-ready"
    assert result["error"] == "EXCHANGE_NOT_READY"
    assert result["normalizationExecuted"] is False
    assert result["retryCount"] == 0


def test_two_partial_raw_close_coverage_does_not_discard_valid_targets():
    result = replay_market(
        payload("TWO", ["6510", "EXTRA"], null_close=["EXTRA"]), [target("TWO", "6510")], "TWO", DAY
    )
    assert (result["rawRows"], result["rawCloseRows"], result["rawNullCloseRows"]) == (2, 1, 1)
    assert result["targetCloseCount"] == 1
    assert result["g2ProviderRowGateStatus"] == "PASS"
    assert result["formalCoverageModelReady"] is True


@pytest.mark.parametrize("market", ["TPE", "TWO"])
def test_parser_zero_rows_is_not_legitimate_unavailable(market):
    result = replay_market(payload(market, []), [target(market, "2330")], market, DAY)
    assert result["error"] == "EXCHANGE_EMPTY_PAYLOAD"
    assert result["normalizationExecuted"] is False


def test_mapping_failure_cannot_borrow_non_target_price_or_promote_absence():
    result = replay_market(payload("TPE", ["EXTRA"]), [target("TPE", "2330")], "TPE", DAY)
    assert result["matchedTargets"] == result["targetCloseCount"] == 0
    assert result["missingTargets"] == ["2330"]
    assert result["legitimateUnavailableCount"] == 0
    assert result["formalCoverageModelReady"] is False
    assert result["decisions"][0]["status"] == "MISSING_MARKET_DATA"


@pytest.mark.parametrize("market", ["TPE", "TWO"])
def test_date_mismatch_is_rejected_without_normalization(market):
    result = replay_market(
        payload(market, ["2330"], response_date="20261001"), [target(market, "2330")], market, DAY
    )
    assert result["error"] == "PROVIDER_DATE_MISMATCH"
    assert result["normalizationExecuted"] is False


def test_missing_close_remains_null_incomplete_and_blocking_despite_prior_history():
    result = replay_market(
        payload("TWO", ["6510"], null_close=["6510"]), [target("TWO", "6510")], "TWO", DAY
    )
    assert result["targetCloseCount"] == result["acceptedPriceCandidates"] == 0
    assert result["normalizationPriceQualities"] == {"INCOMPLETE": 1}
    assert result["priorCanonicalCloseCount"] == 1
    assert result["formalCoverageModelReady"] is False
    assert result["decisions"][0]["closePresent"] is False
    assert result["decisions"][0]["legitimateUnavailable"] is False


def test_missing_previous_close_is_not_invented_or_reported_as_current_previous_close():
    result = replay_market(
        payload("TPE", ["2330"]), [target("TPE", "2330", prior=False)], "TPE", DAY
    )
    assert result["priorCanonicalCloseCount"] == result["currentPreviousCloseCount"] == 0
    assert result["priorComparatorPresenceComplete"] is False
    assert result["stages"][11]["rejectionReason"] == "PREVIOUS_CLOSE_AUTHORITY_NOT_READY"
    assert result["productionReadinessProven"] is False


def test_non_prior_date_cannot_be_used_for_previous_close():
    result = replay_market(
        payload("TPE", ["2330"]), [target("TPE", "2330", prior_date="2026-10-02")], "TPE", DAY
    )
    assert result["priorCanonicalCloseCount"] == 0
    assert result["priorComparatorPresenceComplete"] is False


def test_2601_existing_corporate_action_authority_is_not_a_synthetic_price():
    result = replay_market(
        payload("TPE", ["2330"]), [target("TPE", "2330"), target("TPE", "2601")], "TPE", DAY
    )
    suspended = next(d for d in result["decisions"] if d["symbol"] == "2601")
    assert suspended["status"] == "SUSPENDED"
    assert suspended["reasonCode"] == "CAPITAL_REDUCTION_TRADING_SUSPENSION"
    assert suspended["authoritySource"] == "TWSE_OFFICIAL_REDUCTION"
    assert suspended["closePresent"] is False
    assert suspended["normalizationPriceQuality"] == "INCOMPLETE"
    assert result["legitimateUnavailableCount"] == 1
    assert result["acceptedPriceCandidates"] == 1
    assert result["formalCoveredCount"] == 2
    assert result["formalCoverageModelReady"] is True
    assert result["g2ProviderRowGateStatus"] == "PASS"
    assert result["g2MissingCodes"] == []


@pytest.mark.parametrize("bad_value", ["-1", "NaN", "Infinity", "garbage", "12"])
def test_invalid_price_values_fail_closed(bad_value):
    data = json.loads(payload("TPE", ["2330"]))
    data["tables"][0]["data"][0][8] = bad_value
    result = replay_market(json.dumps(data).encode(), [target("TPE", "2330")], "TPE", DAY)
    assert result["error"] in {"INVALID_NUMBER", "INVALID_OHLC"}
    assert result["normalizationExecuted"] is False


def test_actual_date_effective_bundle_accounting_is_553_not_total_registry_or_555_missing():
    bundle = load_bundle(
        ROOT
        / "services/api/src/topicpilot_api/reference_data/bundles"
        / "tw-reference-v1-expansion-20260912"
    )
    rows = []
    for item in bundle.instruments:
        events = tuple(
            InstrumentLifecycle(
                e["status_code"],
                date.fromisoformat(e["effective_from"]),
                date.fromisoformat(e["effective_to"]) if e.get("effective_to") else None,
                e.get("evidence_id"),
            )
            for e in bundle.instrument_lifecycles
            if (e["market_code"], e["instrument_code"])
            == (item["market_code"], item["instrument_code"])
        )
        rows.append(
            InstrumentUniverseRow(
                item["market_code"],
                item["instrument_code"],
                item["instrument_type"],
                item.get("is_active", True),
                date.fromisoformat(item["valid_from"]) if item.get("valid_from") else None,
                date.fromisoformat(item["valid_to"]) if item.get("valid_to") else None,
                lifecycle_events=events,
            )
        )
    universe = build_date_effective_instrument_universe(rows, DAY)
    assert len(bundle.instruments) == 556
    assert {m: len(codes) for m, codes in universe.items()} == {"TPE": 347, "TWO": 206}
    results = [
        replay_market(payload(m, [c for c in codes if c != "2601"]),
            [target(m, c) for c in codes], m, DAY)
        for m, codes in universe.items()
    ]
    assert sum(r["targets"] for r in results) == 553
    assert sum(r["matchedTargets"] for r in results) == 552
    assert sum(r["acceptedPriceCandidates"] for r in results) == 552
    assert sum(r["legitimateUnavailableCount"] for r in results) == 1
    assert sum(r["formalCoveredCount"] for r in results) == 553
    assert all(r["g2ProviderRowGateStatus"] == "PASS" for r in results)
    assert [r["g2AuthorityEvidence"]["previousCloseCoveredCount"] for r in results] == [346, 206]
    assert all(r["formalCoverageModelReady"] for r in results)
    # Synthetic parser coverage is not a production observation or persisted identity proof.
    assert all(not r["productionReadinessProven"] for r in results)


def test_unknown_or_ineligible_identity_and_wrong_provider_fail_before_replay():
    row = target("TPE", "2330")
    row[4] = "LIFECYCLE_DELISTED"
    with pytest.raises(ValueError, match="INVALID_TARGET_ELIGIBILITY"):
        replay_market(payload("TPE", ["2330"]), [row], "TPE", DAY)
    row = target("TPE", "2330")
    row[5] = "SHADOW"
    with pytest.raises(ValueError, match="PROVIDER_IDENTITY_MISMATCH"):
        replay_market(payload("TPE", ["2330"]), [row], "TPE", DAY)


def test_duplicate_replay_identity_is_rejected():
    row = target("TPE", "2330")
    with pytest.raises(ValueError, match="INVALID_TARGET_IDENTITIES"):
        replay_market(payload("TPE", ["2330"]), [row, row], "TPE", DAY)


def test_replay_has_no_network_database_runner_or_home_write_surface():
    from infra.scripts import replay_target_universe_readiness as module

    source = inspect.getsource(module)
    for forbidden in (
        "create_engine(",
        "Session(",
        "PostCloseUpdater(",
        "urlopen(",
        "ingest_historical_daily(",
        ".commit(",
        ".flush(",
        "session.add(",
        "materialize_home_v2(",
    ):
        assert forbidden not in source

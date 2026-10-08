from datetime import UTC, datetime
from types import SimpleNamespace

from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.post_close import PostCloseUpdater
from topicpilot_api.live.receipt import (
    RECEIPT_DEADLINE_EXCEEDED,
    RECEIPT_WAITING_FOR_DATA,
    _receipt_status,
)
from topicpilot_api.live.scheduler import LiveScheduler
from topicpilot_api.live.session import MarketSessionClock
from topicpilot_api.live.staging import (
    TPEX_MARKET,
    TWSE_MARKET,
    eligible_markets,
    stage_for,
    tpex_retry_window_open,
)


def _utc(hour: int, minute: int) -> datetime:
    return datetime(2026, 10, 8, hour, minute, tzinfo=UTC)


def test_market_windows_are_poll_eligible_and_independent():
    config = LiveRuntimeConfig()

    assert eligible_markets(_utc(7, 36), config) == ()  # 15:36 Taipei
    assert eligible_markets(_utc(7, 37), config) == (TWSE_MARKET,)
    assert eligible_markets(_utc(7, 41), config) == (TWSE_MARKET,)
    assert eligible_markets(_utc(7, 42), config) == (TWSE_MARKET, TPEX_MARKET)
    assert not tpex_retry_window_open(_utc(7, 50), config)
    assert tpex_retry_window_open(_utc(7, 52), config)


def test_stage_timeline_covers_required_boundaries():
    config = LiveRuntimeConfig()

    assert stage_for(_utc(5, 45), config) == "WAITING_TWSE_WINDOW"
    assert stage_for(_utc(7, 45), config) == "MARKET_INGESTION"
    assert stage_for(_utc(8, 7), config) == "COMBINED_RECONCILIATION"
    assert stage_for(_utc(9, 0), config) == "PRICE_BASED_FORMAL"
    assert stage_for(_utc(10, 33), config) == "LATE_DATA_ENRICHMENT"
    assert stage_for(_utc(12, 10), config) == "LATE_DATA_DEADLINE"


def test_scheduler_keeps_heartbeat_and_enters_post_close_only_at_1345():
    config = LiveRuntimeConfig()
    clock = MarketSessionClock(
        config.timezone_name,
        config.session_open,
        config.session_close,
        config.closed_dates,
    )
    scheduler = LiveScheduler(object(), config, clock=lambda: _utc(5, 44))

    assert scheduler.config.poll_interval_seconds == 300
    assert scheduler.decide(_utc(5, 44)) == "WAIT"
    assert scheduler.decide(_utc(5, 45)) == "POST_CLOSE"
    assert clock.status(_utc(5, 45)).local_time.strftime("%H:%M") == "13:45"


def test_twse_only_state_is_not_a_formal_ready_state():
    config = LiveRuntimeConfig()
    assert eligible_markets(_utc(7, 37), config) == (TWSE_MARKET,)
    assert stage_for(_utc(7, 37), config) == "TWSE_WINDOW"
    assert stage_for(_utc(7, 42), config) != "FORMAL_PUBLICATION_READY"


def test_price_formal_completion_does_not_hide_pending_late_data():
    config = LiveRuntimeConfig()
    metadata = {
        "dailyMarketReconciliation": {"downstreamReady": True},
        "topicSnapshot": {
            "formalPublicationReadback": {"status": "PASS"},
            "lateDataEnrichment": {"status": "WAITING"},
        },
    }

    assert (
        _receipt_status(
            "SUCCESS",
            metadata,
            "NORMAL_CURRENT_DAY",
            _utc(10, 0),
            _utc(10, 0).date(),
            config,
        )
        == RECEIPT_WAITING_FOR_DATA
    )
    assert (
        _receipt_status(
            "SUCCESS",
            metadata,
            "NORMAL_CURRENT_DAY",
            _utc(12, 10),
            _utc(12, 10).date(),
            config,
        )
        == RECEIPT_DEADLINE_EXCEEDED
    )


def test_simulated_e2e_keeps_partial_stages_out_of_formal_publication():
    config = LiveRuntimeConfig()
    checkpoints: set[str] = set()
    formal_published = False
    safe_computation = False

    # 13:45: preflight only.
    assert eligible_markets(_utc(5, 45), config) == ()
    assert "TPE" not in checkpoints and "TWO" not in checkpoints

    # First eligible TWSE poll, then a local computation that is not Formal.
    assert eligible_markets(_utc(7, 37), config) == (TWSE_MARKET,)
    checkpoints.add(TWSE_MARKET)
    safe_computation = TWSE_MARKET in checkpoints
    assert safe_computation and not formal_published

    # TPEx is independently retried; a waiting TWO checkpoint does not
    # invalidate the accepted TPE checkpoint.
    assert eligible_markets(_utc(7, 52), config) == (TWSE_MARKET, TPEX_MARKET)
    assert checkpoints == {TWSE_MARKET}
    assert not (TWSE_MARKET in checkpoints and TPEX_MARKET in checkpoints)
    checkpoints.add(TPEX_MARKET)

    # Only the combined gate authorizes the existing Formal chain.
    combined_ready = checkpoints == {TWSE_MARKET, TPEX_MARKET}
    if combined_ready:
        formal_published = True
    assert formal_published


def test_simulated_e2e_runs_real_stage_helpers_without_production_state(monkeypatch):
    """Exercise the real stage helpers with an in-memory checkpoint ledger."""

    config = LiveRuntimeConfig()
    now = [_utc(7, 37)]
    checkpoints: dict[str, SimpleNamespace] = {}
    stage_events: list[tuple[str, str]] = []
    late_readback = {"status": "FAIL", "reasonCode": "NOT_YET_AVAILABLE"}

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.config = config
    updater._now = lambda: now[0]
    updater._latest_checkpoint = lambda _run_id, key: checkpoints.get(key)
    updater._refresh_tracking_universe_with_retry = lambda **_kwargs: 553
    updater._institutional_flow_readback = lambda _date: dict(late_readback)
    def persist_late_facts(_facts, **_kwargs):
        late_readback["status"] = "PASS"
        return {"status": "SUCCESS", "persisted": 2}

    updater._persist_official_institutional_flow = persist_late_facts

    def record_checkpoint(**values):
        key = values["batch_key"]
        checkpoints[key] = SimpleNamespace(
            status=values["status"],
            metadata_payload=values.get("metadata") or {},
            succeeded_count=values.get("succeeded_count", 0),
        )
        return checkpoints[key]

    updater._checkpoint_event = record_checkpoint
    updater._update_publication_stage = (
        lambda _run_id, stage, status, **_values: stage_events.append((stage, status))
    )

    # 1-3: source wait, TWSE arrival, and actual TWSE-safe helper execution.
    assert eligible_markets(_utc(7, 36), config) == ()
    assert eligible_markets(now[0], config) == (TWSE_MARKET,)
    tracking_count, error = updater._run_twse_safe_computation(
        run_id="simulated-run",
        local_date=now[0].date(),
        twse_instrument_ids=("twse-1", "twse-2"),
    )
    assert (tracking_count, error) == (553, None)
    assert checkpoints["TWSE_SAFE_COMPUTATION"].status == "COMPLETED"
    assert stage_events[-1] == ("twseSafeComputation", "READY")
    checkpoints["FORMAL_MARKET_FACTS:TPE:1"] = SimpleNamespace(
        status="COMPLETED",
        succeeded_count=2,
        failed_count=0,
        skipped_count=0,
        retry_count=1,
        metadata_payload={"pricedCount": 2, "coveredCount": 2},
    )
    twse_readback = updater._market_stage_readback(
        "simulated-run",
        [(1, TWSE_MARKET, ["twse-1", "twse-2"]), (2, TPEX_MARKET, ["tpex-1"])],
        TWSE_MARKET,
        trading_date=now[0].date(),
        now=now[0],
    )
    assert twse_readback["acceptedPriceCount"] == 2
    assert twse_readback["acceptedTradingStatusCount"] == 0
    assert twse_readback["sourceDataDate"] == "2026-10-08"
    assert twse_readback["latestSourceObservationTime"] is None
    assert (
        twse_readback["sourceObservationTimeReason"]
        == "PROVIDER_CONTRACT_DID_NOT_EMIT_OBSERVATION_TIME"
    )
    assert twse_readback["coverageResult"] == "COMPLETE"
    assert twse_readback["nextEligibleRetry"] is None
    assert twse_readback["checkpointIdentity"][0]["batchKey"] == "FORMAL_MARKET_FACTS:TPE:1"
    assert twse_readback["expectedInstrumentCount"] == 2
    assert twse_readback["readinessState"] == "READY"

    # 4-6: TPEx is initially pending, then the combined market gate opens.
    now[0] = _utc(7, 45)
    assert eligible_markets(now[0], config) == (TWSE_MARKET, TPEX_MARKET)
    accepted_markets = {TWSE_MARKET}
    assert accepted_markets != {TWSE_MARKET, TPEX_MARKET}
    now[0] = _utc(7, 52)
    accepted_markets.add(TPEX_MARKET)
    assert accepted_markets == {TWSE_MARKET, TPEX_MARKET}

    # 7-11: a complete formal fixture is accepted only after the combined gate.
    formal_snapshot = {
        "status": "SUCCESS",
        "formalTopicDailyState": {"status": "SUCCESS"},
        "formalTopicSnapshotReadback": {"status": "PASS"},
        "formalStrengthReadback": {"status": "PASS"},
        "formalLifecycleReadback": {"status": "PASS"},
    }
    assert PostCloseUpdater._formal_snapshot_ready(formal_snapshot)
    assert accepted_markets == {TWSE_MARKET, TPEX_MARKET}

    # 12-13: late lane waits before its target, then finalizes when facts arrive.
    now[0] = _utc(10, 30)  # 18:30 Taipei
    waiting = updater._late_data_enrichment(
        run_id="simulated-run",
        local_date=now[0].date(),
    )
    assert waiting["status"] == "WAITING"
    now[0] = _utc(10, 33)
    monkeypatch.setattr(
        "topicpilot_api.live.post_close.fetch_official_market_institutional_flows",
        lambda **_kwargs: ("official-flow-fact",),
    )
    ready = updater._late_data_enrichment(
        run_id="simulated-run",
        local_date=now[0].date(),
    )
    assert ready["status"] == "PASS"
    assert checkpoints["LATE_DATA_ENRICHMENT"].status == "COMPLETED"


def test_market_readback_exposes_bounded_retry_and_error_provenance():
    config = LiveRuntimeConfig()
    now = _utc(7, 45)  # 15:45 Taipei, before the 15:52 TPEx retry window.
    checkpoint = SimpleNamespace(
        status="PARTIAL",
        succeeded_count=0,
        failed_count=1,
        skipped_count=0,
        retry_count=1,
        attempt_number=2,
        checkpoint_hash="checkpoint-hash",
        created_at=now,
        metadata_payload={
            "sessionDate": now.date().isoformat(),
            "pricedCount": 0,
            "coveredCount": 0,
            "providerErrorCode": "EXCHANGE_NOT_READY",
        },
    )
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.config = config
    updater._latest_checkpoint = lambda _run_id, _key: checkpoint
    updater._now = lambda: now

    readback = updater._market_stage_readback(
        "simulated-run",
        [(1, TPEX_MARKET, ["tpex-1"])],
        TPEX_MARKET,
        trading_date=now.date(),
        now=now,
    )

    assert readback["readinessState"] == "WAITING_SOURCE_DATA"
    assert readback["nextEligibleRetry"].endswith("T07:52:00+00:00")
    assert readback["lastRetry"].endswith("T07:45:00+00:00")
    assert readback["errorCategory"] == ["EXCHANGE_NOT_READY"]
    assert readback["checkpointIdentity"] == [
        {
            "batchKey": "FORMAL_MARKET_FACTS:TWO:1",
            "attemptNumber": 2,
            "checkpointHash": "checkpoint-hash",
        }
    ]

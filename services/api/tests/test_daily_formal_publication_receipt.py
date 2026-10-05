from datetime import UTC, date, datetime

from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.receipt import (
    RECEIPT_DEADLINE_EXCEEDED,
    RECEIPT_MARKET_CLOSED,
    RECEIPT_WAITING_FOR_DATA,
    _receipt_status,
    hard_deadline_at,
    operational_phase,
    runtime_provenance,
    soft_target_at,
)


def test_frozen_daily_publication_timing_is_exposed_and_ordered():
    config = LiveRuntimeConfig()

    assert config.post_close_start == "13:45"
    assert config.soft_target == "14:30"
    assert config.hard_deadline == "15:00"
    assert config.as_dict()["softTarget"] == "14:30"
    assert config.as_dict()["hardDeadline"] == "15:00"
    assert soft_target_at(date(2026, 10, 5), config) < hard_deadline_at(
        date(2026, 10, 5), config
    )


def test_operational_phase_does_not_turn_clock_into_data_ready():
    config = LiveRuntimeConfig()
    trading_date = date(2026, 10, 5)

    assert (
        operational_phase(
            datetime(2026, 10, 5, 6, 0, tzinfo=UTC),
            trading_date,
            config,
            data_ready=False,
        )
        == RECEIPT_WAITING_FOR_DATA
    )
    assert (
        operational_phase(
            datetime(2026, 10, 5, 6, 31, tzinfo=UTC),
            trading_date,
            config,
            data_ready=False,
        )
        == "SOFT_TARGET_NOT_READY"
    )
    assert (
        operational_phase(
            datetime(2026, 10, 5, 7, 0, tzinfo=UTC),
            trading_date,
            config,
            data_ready=False,
        )
        == RECEIPT_DEADLINE_EXCEEDED
    )
    assert (
        operational_phase(
            datetime(2026, 10, 5, 7, 0, tzinfo=UTC),
            trading_date,
            config,
            data_ready=True,
        )
        == "DATA_READY"
    )
    assert (
        operational_phase(
            datetime(2026, 10, 5, 7, 0, tzinfo=UTC),
            trading_date,
            config,
            data_ready=False,
            market_closed=True,
        )
        == RECEIPT_MARKET_CLOSED
    )


def test_receipt_status_requires_reconciliation_and_formal_readback():
    config = LiveRuntimeConfig()
    now = datetime(2026, 10, 5, 6, 0, tzinfo=UTC)
    metadata = {
        "dailyMarketReconciliation": {"downstreamReady": True},
        "topicSnapshot": {"formalPublicationReadback": {"status": "PASS"}},
    }

    assert (
        _receipt_status(
            "SUCCESS",
            metadata,
            "NORMAL_CURRENT_DAY",
            now,
            date(2026, 10, 5),
            config,
        )
        == "COMPLETE"
    )
    metadata["topicSnapshot"]["formalPublicationReadback"]["status"] = "FAIL"
    assert (
        _receipt_status(
            "SUCCESS",
            metadata,
            "NORMAL_CURRENT_DAY",
            now,
            date(2026, 10, 5),
            config,
        )
        == "FAILED_CLOSED"
    )


def test_unknown_runtime_provenance_is_never_verified(monkeypatch):
    monkeypatch.delenv("TOPICPILOT_API_RUNTIME_SHA", raising=False)
    monkeypatch.delenv("TOPICPILOT_WEB_ARTIFACT_SHA", raising=False)

    class Session:
        def execute(self, _statement):
            raise RuntimeError("no database in unit test")

    provenance = runtime_provenance(Session())

    assert provenance["status"] == "DEGRADED"
    assert provenance["unknownIsVerified"] is False
    assert provenance["api"]["readbackStatus"] == "UNVERIFIED"
    assert provenance["web"]["readbackStatus"] == "UNVERIFIED"
    assert provenance["migration"]["readbackStatus"] == "UNVERIFIED"

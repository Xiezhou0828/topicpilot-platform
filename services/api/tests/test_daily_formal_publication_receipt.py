import math
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from topicpilot_api.daily_market import assess_daily_coverage
from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.receipt import (
    RECEIPT_MARKET_CLOSED,
    RECEIPT_WAITING_FOR_DATA,
    RUNTIME_PROVENANCE_TRUST_FAILURE,
    _receipt_stable_hash,
    _receipt_status,
    append_receipt_for_run,
    hard_deadline_at,
    operational_phase,
    runtime_provenance,
    runtime_provenance_event,
    soft_target_at,
)
from topicpilot_api.normalizer.contracts import stable_hash


def test_receipt_hash_canonicalizes_finite_reconciliation_floats_at_boundary():
    reconciliation = assess_daily_coverage(
        trade_date=date(2026, 10, 6),
        expected_by_market={"TPE": 500, "TWO": 53},
        observed_by_market={"TPE": 500, "TWO": 53},
        priced_by_market={"TPE": 499, "TWO": 53},
        covered_by_market={"TPE": 499, "TWO": 53},
    ).to_dict()

    assert isinstance(reconciliation["coveragePct"], float)
    assert isinstance(reconciliation["coveredCoveragePct"], float)
    assert _receipt_stable_hash({"reconciliation": reconciliation}) == _receipt_stable_hash(
        {
            "reconciliation": {
                **reconciliation,
                "coveragePct": Decimal(str(reconciliation["coveragePct"])),
                "coveredCoveragePct": Decimal(str(reconciliation["coveredCoveragePct"])),
            }
        }
    )


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_receipt_hash_rejects_non_finite_float(value):
    with pytest.raises(ValueError, match="finite numeric values"):
        _receipt_stable_hash({"value": value})


def test_receipt_float_boundary_is_not_a_global_float_coercion():
    with pytest.raises(TypeError, match="unsupported canonical value: float"):
        stable_hash({"coveragePct": 99.8192})

    assert _receipt_stable_hash({"value": 0.1}) == _receipt_stable_hash(
        {"value": Decimal("0.1")}
    )
    assert _receipt_stable_hash({"value": 0.1}) == _receipt_stable_hash({"value": "0.1"})


def test_post_close_receipt_boundary_accepts_reconciliation_float(monkeypatch):
    reconciliation = assess_daily_coverage(
        trade_date=date(2026, 10, 6),
        expected_by_market={"TPE": 500, "TWO": 53},
        observed_by_market={"TPE": 500, "TWO": 53},
        priced_by_market={"TPE": 499, "TWO": 53},
        covered_by_market={"TPE": 499, "TWO": 53},
    ).to_dict()
    now = datetime(2026, 10, 6, 8, 0, tzinfo=UTC)
    run = SimpleNamespace(
        id=uuid4(),
        status="PARTIAL",
        started_at=now,
        completed_at=now,
        metadata_payload={
            "runDate": "2026-10-06",
            "executionKey": "post-close:test:2026-10-06:FULL",
            "dailyMarketReconciliation": reconciliation,
            "topicSnapshot": {"formalPublicationReadback": {"status": "FAIL"}},
        },
    )

    class Session:
        def scalar(self, _statement):
            return None

        def add(self, value):
            self.added = value

    monkeypatch.setattr(
        "topicpilot_api.live.receipt.runtime_provenance",
        lambda _session: {},
    )

    receipt = append_receipt_for_run(
        Session(),
        run,
        LiveRuntimeConfig(),
        now=now,
    )

    assert receipt.receipt_hash


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
        == RECEIPT_WAITING_FOR_DATA
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


def test_receipt_wait_remains_retryable_after_operational_deadline():
    config = LiveRuntimeConfig()
    metadata = {
        "dailyMarketReconciliation": {"downstreamReady": False},
        "topicSnapshot": {"formalPublicationReadback": {"status": "WAIT"}},
    }

    assert (
        _receipt_status(
            "PARTIAL",
            metadata,
            "NORMAL_CURRENT_DAY",
            datetime(2026, 10, 5, 7, 1, tzinfo=UTC),
            date(2026, 10, 5),
            config,
        )
        == RECEIPT_WAITING_FOR_DATA
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


def test_runtime_provenance_trust_failure_is_critical_and_actionable(monkeypatch):
    monkeypatch.setattr(
        "topicpilot_api.live.receipt.runtime_git_sha", lambda: "a" * 40
    )
    monkeypatch.delenv("TOPICPILOT_API_RUNTIME_SHA", raising=False)
    monkeypatch.delenv("TOPICPILOT_WEB_ARTIFACT_SHA", raising=False)

    class Result:
        def scalar_one_or_none(self):
            return "0049_task_daily_formal_publication_receipt"

    class Session:
        def execute(self, _statement):
            return Result()

    now = datetime(2026, 10, 5, 7, 0, tzinfo=UTC)
    provenance = runtime_provenance(Session())
    event = runtime_provenance_event(provenance, now)

    assert provenance["status"] == "DEGRADED"
    assert event == {
        "code": RUNTIME_PROVENANCE_TRUST_FAILURE,
        "severity": "CRITICAL",
        "actionRequired": True,
        "at": now.isoformat(),
        "unverifiedComponents": ["api"],
    }


def test_runtime_provenance_event_is_absent_when_required_sources_are_ready(
    monkeypatch,
):
    monkeypatch.setattr(
        "topicpilot_api.live.receipt.runtime_git_sha", lambda: "a" * 40
    )
    monkeypatch.setenv("TOPICPILOT_API_RUNTIME_SHA", "b" * 40)

    class Result:
        def scalar_one_or_none(self):
            return "0049_task_daily_formal_publication_receipt"

    class Session:
        def execute(self, _statement):
            return Result()

    provenance = runtime_provenance(Session())
    assert provenance["status"] == "READY"
    assert runtime_provenance_event(
        provenance, datetime(2026, 10, 5, 7, 0, tzinfo=UTC)
    ) is None

from __future__ import annotations

import argparse
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from topicpilot_api.instrument_universe import InstrumentLifecycle, InstrumentUniverseRow
from topicpilot_api.live.cli import _symbols_argument, build_parser
from topicpilot_api.live.post_close import (
    HISTORY_RECOVERY,
    NORMAL_CURRENT_DAY,
    PostClosePreconditionError,
    PostCloseUpdater,
    _json_safe,
    resolve_post_close_run_date,
)
from topicpilot_api.market_data.history import HistoricalProviderError
from topicpilot_api.market_data.ingestion import HistoricalInstrumentResult


def _identity(market: str, code: str, identifier: int):
    return (
        SimpleNamespace(id=identifier, instrument_code=code),
        SimpleNamespace(code=market),
    )


def test_post_close_universe_validation_is_exact_and_duplicate_safe():
    expected = {
        "TPE": ("2330", "2317"),
        "TWO": ("4979",),
    }
    instruments = [
        _identity("TPE", "2317", 1),
        _identity("TPE", "2330", 2),
        _identity("TWO", "4979", 3),
    ]

    PostCloseUpdater._validate_instruments(instruments, expected)


@pytest.mark.parametrize(
    "instruments",
    [
        [_identity("TPE", "2330", 1), _identity("TWO", "4979", 2)],
        [
            _identity("TPE", "2330", 1),
            _identity("TPE", "2330", 2),
            _identity("TWO", "4979", 3),
        ],
        [
            _identity("TPE", "2330", 1),
            _identity("TPE", "6806", 2),
            _identity("TWO", "4979", 3),
        ],
    ],
)
def test_post_close_universe_validation_fails_closed_for_missing_duplicate_or_delisted(
    instruments,
):
    with pytest.raises(PostClosePreconditionError) as exc_info:
        PostCloseUpdater._validate_instruments(
            instruments,
            {"TPE": ("2330", "2317"), "TWO": ("4979",)},
        )

    assert exc_info.value.code == "DATE_EFFECTIVE_UNIVERSE_MISMATCH"


def test_targeted_symbol_argument_accepts_codes_and_market_qualified_codes():
    assert _symbols_argument("1584, TWO:6129") == ("1584", "TWO:6129")
    args = build_parser().parse_args(
        [
            "--mode",
            "post-close",
            "--once",
            "--run-date",
            "2026-09-03",
            "--symbols",
            "1584,TWO:6129",
        ]
    )
    assert args.symbols == ("1584", "TWO:6129")


@pytest.mark.parametrize("value", ["", ":1584", "TWO:", "TWO:15:84"])
def test_targeted_symbol_argument_rejects_malformed_values(value):
    with pytest.raises(argparse.ArgumentTypeError):
        _symbols_argument(value)


def test_targeted_symbols_resolve_against_date_effective_universe():
    selected, normalized = PostCloseUpdater._resolve_target_symbols(
        {"TPE": ("2330",), "TWO": ("1584", "6129")},
        ("1584", "TWO:6129"),
    )

    assert selected == {"TWO": ("1584", "6129")}
    assert normalized == ("TWO:1584", "TWO:6129")


def test_targeted_symbols_fail_closed_when_not_in_date_effective_universe():
    with pytest.raises(PostClosePreconditionError) as exc_info:
        PostCloseUpdater._resolve_target_symbols(
            {"TPE": ("2330",), "TWO": ("1584",)},
            ("6129",),
        )

    assert exc_info.value.code == "TARGET_SYMBOL_NOT_IN_DATE_EFFECTIVE_UNIVERSE"


def test_targeted_symbols_can_reach_lifecycle_authorized_no_trade_identity():
    context = SimpleNamespace(
        universe_rows=(
            InstrumentUniverseRow(
                market_code="TWO",
                instrument_code="6129",
                instrument_type="EQUITY",
                is_active=True,
                lifecycle_events=(
                    InstrumentLifecycle(
                        status_code="SUSPENDED",
                        effective_from=date(2026, 9, 3),
                        effective_to=date(2026, 9, 11),
                        evidence_id="MOPS-TWO-6129-SUSPENDED-20260903",
                    ),
                ),
            ),
        )
    )

    targetable = PostCloseUpdater._targetable_universe(
        context,
        date(2026, 9, 4),
        {"TPE": ("2330",), "TWO": ()},
    )
    selected, normalized = PostCloseUpdater._resolve_target_symbols(
        targetable,
        ("TWO:6129",),
    )

    assert selected == {"TWO": ("6129",)}
    assert normalized == ("TWO:6129",)


def test_targeted_finalization_does_not_promote_full_snapshot():
    captured: dict[str, object] = {}
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater._finish_with_retry = lambda run_id, **values: captured.update(values)
    updater._now = lambda: datetime(2026, 9, 3, 8, 0, tzinfo=UTC)

    result = updater._finalize_targeted_run(
        run_id="targeted-run",
        local_date=date(2026, 9, 3),
        requested_count=2,
        success_count=2,
        failure_count=0,
        skipped_count=0,
        retry_count=0,
        point_count=2,
        failure_codes=(),
    )

    assert result.status == "SUCCESS"
    assert result.requested_count == 2
    assert captured["reconciliation"] is None
    assert captured["snapshot_result"] == {
        "snapshotDate": "2026-09-03",
        "topicCount": 0,
        "status": "NOT_RUN_TARGETED",
    }


def test_post_close_cli_defers_tracking_mutation_until_after_reference_precondition():
    source = Path(__file__).parents[1] / "src/topicpilot_api/live/cli.py"
    text = source.read_text(encoding="utf-8")

    assert 'if decision != "POST_CLOSE":' in text
    assert "repository.refresh_tracking_universe()" in text
    refresh = text.index("repository.refresh_tracking_universe()")
    assert text.index("session.commit()", refresh) < text.index("collector =", refresh)
    assert "load_g2_preflight_context" in (
        Path(__file__).parents[1]
        / "src/topicpilot_api/live/post_close.py"
    ).read_text(encoding="utf-8")


def test_post_close_explicit_recovery_is_date_bound_and_auditable():
    cli_source = (Path(__file__).parents[1] / "src/topicpilot_api/live/cli.py").read_text(
        encoding="utf-8"
    )
    post_close_source = (
        Path(__file__).parents[1] / "src/topicpilot_api/live/post_close.py"
    ).read_text(encoding="utf-8")

    assert '"--recover"' in cli_source
    assert '"--recover requires --run-date YYYY-MM-DD"' in cli_source
    assert "allow_terminal_recovery=args.recover" in cli_source
    assert "allow_terminal_recovery: bool = False" in post_close_source
    assert '"recoveryOfRunId"' in post_close_source
    assert "if recovery_of_run_id is None:" in post_close_source
    assert 'metadata_payload["runDate"]' in post_close_source
    assert 'existing_run.failure_code == "POST_CLOSE_FINALIZATION_FAILED"' in post_close_source
    assert "_completed_attempt_summary" in post_close_source
    assert "target_symbols: Collection[str] | None = None" in post_close_source
    assert "--symbols" in cli_source
    assert "TARGETED" in post_close_source


def test_post_close_finalization_metadata_is_json_safe():
    value = _json_safe(
        {
            "tradeDate": date(2026, 8, 28),
            "nested": [datetime(2026, 8, 30, 1, 2, tzinfo=UTC)],
        }
    )

    assert value == {
        "tradeDate": "2026-08-28",
        "nested": ["2026-08-30T01:02:00+00:00"],
    }


def test_post_close_materializes_formal_pit_state_before_formal_publication():
    source = (
        Path(__file__).parents[1] / "src/topicpilot_api/live/post_close.py"
    ).read_text(encoding="utf-8")

    assert "materialize_bounded_formal_dates" in source
    assert 'dates=(snapshot_date,)' in source
    assert "FormalStrengthPublisher(self.session).run_once" in source
    assert "FormalLifecyclePublisher(self.session).run_once" in source
    assert 'result["formalTopicDailyState"]' in source


def test_post_close_completed_attempt_summary_is_recovery_safe():
    instrument_ids = [uuid4(), uuid4()]
    attempts = [
        SimpleNamespace(
            instrument_id=instrument_ids[0],
            updated_at=datetime(2026, 8, 30, 1, 0, tzinfo=UTC),
            id=uuid4(),
            status="SUCCESS",
            retry_count=1,
            error_code=None,
        ),
        SimpleNamespace(
            instrument_id=instrument_ids[1],
            updated_at=datetime(2026, 8, 30, 1, 1, tzinfo=UTC),
            id=uuid4(),
            status="SKIPPED",
            retry_count=0,
            error_code="MISSING_MARKET_DATA",
        ),
    ]

    class ScalarResult:
        def all(self):
            return attempts

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = SimpleNamespace(scalars=lambda _query: ScalarResult())

    summary = updater._completed_attempt_summary("run-id", instrument_ids)

    assert summary == {
        "success_count": 1,
        "failure_count": 0,
        "skipped_count": 1,
        "retry_count": 1,
        "failure_codes": ("MISSING_MARKET_DATA",),
    }


def test_post_close_recent_run_is_not_considered_stale():
    run = SimpleNamespace(
        heartbeat_at=datetime(2026, 8, 30, 1, 0, 30, tzinfo=UTC),
    )

    assert PostCloseUpdater._is_recent_run(
        run,
        datetime(2026, 8, 30, 1, 1, tzinfo=UTC),
        stale_after=60,
    )


def test_post_close_batched_outcome_keeps_unknown_missing_data_uncovered():
    missing = HistoricalInstrumentResult(
        instrument_code="6752",
        market_code="TWO",
        provider_point_count=1,
        observed_count=1,
        priced_count=0,
        covered_count=0,
        unexplained_missing_count=1,
        instrument_status="UNKNOWN",
        status_reason="missing priced bar",
    )
    approved = HistoricalInstrumentResult(
        instrument_code="6806",
        market_code="TWO",
        provider_point_count=0,
        observed_count=1,
        priced_count=0,
        covered_count=1,
        unexplained_missing_count=0,
        instrument_status="EXCHANGE_CONFIRMED_NO_DATA",
    )

    assert PostCloseUpdater._history_attempt_outcome(missing) == (
        "SKIPPED",
        "MISSING_MARKET_DATA",
        "missing priced bar",
    )
    assert PostCloseUpdater._history_attempt_outcome(approved) == (
        "SUCCESS",
        "APPROVED_NO_TRADE",
        None,
    )

    halted = approved.__class__(
        instrument_code="6807",
        market_code="TWO",
        provider_point_count=0,
        observed_count=1,
        priced_count=0,
        covered_count=1,
        unexplained_missing_count=0,
        instrument_status="HALTED",
    )
    assert PostCloseUpdater._history_attempt_outcome(halted) == (
        "SUCCESS",
        "APPROVED_NO_TRADE",
        None,
    )


def test_post_close_execution_key_is_session_and_scope_bound():
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.config = SimpleNamespace(
        reference_data_version="tw-reference-v1",
        calendar_code="TW_MARKET",
    )

    full = updater._execution_key(date(2026, 9, 3))
    targeted = updater._execution_key(
        date(2026, 9, 3), target_symbols=("TPE:2330", "TWO:6129")
    )

    assert full == "post-close:tw-reference-v1:TW_MARKET:2026-09-03:NORMAL_CURRENT_DAY:FULL"
    assert targeted != full
    assert targeted == updater._execution_key(
        date(2026, 9, 3), target_symbols=("TPE:2330", "TWO:6129")
    )
    recovery = updater._execution_key(date(2026, 9, 3), execution_mode="RECOVERY")
    assert recovery == (
        "history-recovery:tw-reference-v1:TW_MARKET:2026-09-03:"
        "HISTORY_RECOVERY:FULL"
    )
    assert recovery != full


def test_history_recovery_checkpoint_namespace_is_distinct_without_schema_change():
    captured = []

    class FakeSession:
        def scalar(self, _query):
            return None

        def add(self, value):
            captured.append(value)

        def commit(self):
            return None

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = FakeSession()
    updater._active_execution_scope = HISTORY_RECOVERY
    updater._active_execution_key = (
        "history-recovery:tw-reference-v1:TW_MARKET:2026-09-30:HISTORY_RECOVERY:FULL"
    )

    updater._checkpoint_event(
        run_id="history-run",
        batch_key="A9_B2_FORMAL_PROCESSING",
        status="COMPLETED",
    )

    metadata = captured[0].metadata_payload
    assert metadata["executionScope"] == HISTORY_RECOVERY
    assert metadata["executionKey"].startswith("history-recovery:")
    assert metadata["checkpointNamespace"].startswith("HISTORY_RECOVERY:")


def test_history_recovery_does_not_call_home_materializer(monkeypatch):
    called = []
    monkeypatch.setattr(
        "topicpilot_api.live.post_close.materialize_home_v2",
        lambda *_args, **_kwargs: called.append(True),
    )
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = SimpleNamespace()
    updater._active_execution_scope = HISTORY_RECOVERY
    updater._active_run_date = date(2026, 9, 30)
    updater._now = lambda: datetime(2026, 10, 2, 1, 0, tzinfo=UTC)

    result = updater._publish_market_facts_only(
        date(2026, 9, 30),
        source_run_id="history-run",
        market_index_facts=(),
        market_aggregate_facts=(),
        market_institutional_flow_facts=(),
        market_institutional_flow_result={"status": "SUCCESS"},
        execution_scope=HISTORY_RECOVERY,
    )

    assert called == []
    assert result["homePublication"] == {
        "status": "FORBIDDEN",
        "reasonCode": "HISTORY_RECOVERY_HOME_PUBLICATION_FORBIDDEN",
        "publicationScope": HISTORY_RECOVERY,
    }


def test_history_recovery_snapshot_does_not_materialize_home(monkeypatch):
    called = []

    class FakeSnapshotEngine:
        def __init__(self, _session):
            pass

        def run_once(self, **_kwargs):
            return {"status": "SUCCESS", "topicCount": 2}

    class FakeFormalRun:
        def as_dict(self):
            return {"status": "SUCCESS"}

    class FakeFormalPublisher:
        def __init__(self, _session):
            pass

        def run_once(self, **_kwargs):
            return FakeFormalRun()

    monkeypatch.setattr(
        "topicpilot_api.live.post_close.TopicSnapshotEngine", FakeSnapshotEngine
    )
    monkeypatch.setattr(
        "topicpilot_api.live.post_close.FormalStrengthPublisher", FakeFormalPublisher
    )
    monkeypatch.setattr(
        "topicpilot_api.live.post_close.FormalLifecyclePublisher", FakeFormalPublisher
    )
    monkeypatch.setattr(
        "topicpilot_api.live.post_close.materialize_bounded_formal_dates",
        lambda *_args, **_kwargs: {
            "rowsBefore": 0,
            "rowsAfter": 2,
            "writes": 2,
            "preBoundaryBackfill": False,
        },
    )
    monkeypatch.setattr(
        "topicpilot_api.live.post_close.materialize_home_v2",
        lambda *_args, **_kwargs: called.append(True),
    )

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = SimpleNamespace(rollback=lambda: None)
    updater._active_execution_scope = HISTORY_RECOVERY
    updater._active_run_date = date(2026, 9, 30)
    updater._formal_snapshot_readback = lambda _date: {"status": "PASS", "rowCount": 2}

    result = updater._run_snapshot(
        date(2026, 9, 30),
        source_run_id="history-run",
        execution_scope=HISTORY_RECOVERY,
    )

    assert called == []
    assert result["homePublication"]["status"] == "FORBIDDEN"


def test_normal_current_day_blocks_home_date_mismatch(monkeypatch):
    called = []
    monkeypatch.setattr(
        "topicpilot_api.live.post_close.materialize_home_v2",
        lambda *_args, **_kwargs: called.append(True),
    )
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = SimpleNamespace()
    updater._active_execution_scope = NORMAL_CURRENT_DAY
    updater._active_run_date = date(2026, 10, 2)
    updater._now = lambda: datetime(2026, 10, 2, 1, 0, tzinfo=UTC)

    result = updater._publish_market_facts_only(
        date(2026, 9, 30),
        source_run_id="normal-run",
        market_index_facts=(),
        market_aggregate_facts=(),
        market_institutional_flow_facts=(),
        market_institutional_flow_result={"status": "SUCCESS"},
        execution_scope=NORMAL_CURRENT_DAY,
    )

    assert called == []
    assert result["homePublication"]["reasonCode"] == "NORMAL_CURRENT_DAY_HOME_DATE_MISMATCH"


def test_history_formal_readback_does_not_query_home():
    class NoHomeQuerySession:
        def scalar(self, _query):
            raise AssertionError("history recovery must not query HomePublication")

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = NoHomeQuerySession()
    updater._formal_snapshot_readback = lambda _date: {"status": "PASS", "rowCount": 2}
    updater._institutional_flow_readback = lambda _date: {"status": "PASS"}

    result = updater._formal_publication_readback(
        date(2026, 9, 30),
        run_id="history-run",
        execution_scope=HISTORY_RECOVERY,
    )

    assert result["status"] == "PASS"
    assert result["homePublication"]["status"] == "FORBIDDEN"
    assert result["homePublication"]["publicationScope"] == HISTORY_RECOVERY


def test_legacy_mixed_run_is_not_reused_for_history_recovery():
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.config = SimpleNamespace(
        reference_data_version="tw-reference-v1",
        calendar_code="TW_MARKET",
    )
    legacy_run = SimpleNamespace(
        metadata_payload={
            "executionKey": "post-close:tw-reference-v1:TW_MARKET:2026-09-30:FULL",
            "scope": "FULL",
            "executionMode": "RECOVERY",
        }
    )
    updater._runs_for_date = lambda _date: [legacy_run]

    assert updater._find_existing_run(
        date(2026, 9, 30), execution_mode="RECOVERY"
    ) is None
    assert updater._find_existing_run(
        date(2026, 9, 30), execution_mode="MANUAL"
    ) is None


def test_history_recovery_key_converges_on_one_run_identity():
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.config = SimpleNamespace(
        reference_data_version="tw-reference-v1",
        calendar_code="TW_MARKET",
    )
    execution_key = updater._execution_key(
        date(2026, 9, 30), execution_mode="RECOVERY"
    )
    history_run = SimpleNamespace(
        metadata_payload={
            "executionKey": execution_key,
            "executionScope": HISTORY_RECOVERY,
            "scope": "FULL",
        }
    )
    updater._runs_for_date = lambda _date: [history_run]

    assert (
        updater._find_existing_run(
            date(2026, 9, 30), execution_mode="RECOVERY"
        )
        is history_run
    )


@pytest.mark.parametrize(
    ("run_at", "expected"),
    [
        (datetime(2026, 9, 29, 5, 35, tzinfo=UTC), date(2026, 9, 29)),
        (datetime(2026, 9, 30, 5, 35, tzinfo=UTC), date(2026, 9, 30)),
    ],
)
def test_post_close_run_date_binding_uses_asia_taipei_session_date(run_at, expected):
    assert resolve_post_close_run_date(run_at, "Asia/Taipei") == expected


def test_explicit_post_close_run_date_overrides_clock_date():
    assert resolve_post_close_run_date(
        datetime(2026, 9, 30, 5, 35, tzinfo=UTC),
        "Asia/Taipei",
        date(2026, 9, 29),
    ) == date(2026, 9, 29)


def test_market_batch_provider_failure_does_not_enter_per_symbol_fallback():
    provider_error = HistoricalProviderError("EXCHANGE_NOT_READY", "not ready")

    assert PostCloseUpdater._is_market_batch_provider_failure(
        provider_error,
        SimpleNamespace(market_batch=True),
    ) is True
    assert PostCloseUpdater._is_market_batch_provider_failure(
        ValueError("reference failure"),
        SimpleNamespace(market_batch=True),
    ) is False
    assert PostCloseUpdater._is_market_batch_provider_failure(
        provider_error,
        SimpleNamespace(market_batch=False),
    ) is False


def test_checkpoint_events_are_append_only_and_increment_attempt_number():
    class FakeSession:
        latest = None

        def scalar(self, _query):
            return self.latest

        def add(self, value):
            self.added = value

        def commit(self):
            return None

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = FakeSession()
    first = updater._checkpoint_event(
        run_id=uuid4(),
        batch_key="FORMAL_MARKET_FACTS:TPE:1",
        batch_number=101,
        status="IN_PROGRESS",
        metadata={"sessionDate": date(2026, 9, 3)},
    )
    assert first.attempt_number == 1
    assert first.status == "IN_PROGRESS"
    assert first.checkpoint_hash
    assert first.provider_request_count == 0
    assert first.provider_failure_count == 0

    updater.session.latest = SimpleNamespace(attempt_number=first.attempt_number)
    second = updater._checkpoint_event(
        run_id=first.run_id,
        batch_key=first.batch_key,
        batch_number=first.batch_number,
        status="FAILED",
        processed_count=20,
        failed_count=20,
        provider_failure_count=1,
        metadata={"providerErrorCode": "EXCHANGE_NOT_READY"},
    )
    assert second.attempt_number == 2
    assert second.status == "FAILED"
    assert second.provider_failure_count == 1
    assert second.metadata_payload["providerErrorCode"] == "EXCHANGE_NOT_READY"
    assert second.metadata_payload["checkpointSemantic"] == "PROVIDER_INGESTION"
    assert second.metadata_payload["providerMetricsApplicability"] == "ACTUAL"


def test_non_provider_checkpoint_persists_null_provider_counters() -> None:
    class FakeSession:
        latest = None

        def scalar(self, _query):
            return self.latest

        def add(self, value):
            self.added = value

        def commit(self):
            return None

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = FakeSession()
    checkpoint = updater._checkpoint_event(
        run_id=uuid4(),
        batch_key="FORMAL_MARKET_FACTS:OFFICIAL",
        batch_number=150,
        status="FAILED",
        failed_count=1,
        provider_request_count=7,
        provider_failure_count=2,
    )

    assert checkpoint.provider_request_count is None
    assert checkpoint.provider_failure_count is None
    assert checkpoint.metadata_payload["checkpointSemantic"] == (
        "INSTITUTIONAL_FLOW_PUBLICATION_READBACK"
    )
    assert checkpoint.metadata_payload["providerMetricsApplicability"] == "NOT_APPLICABLE"


def test_checkpoint_hash_accepts_runtime_float_metadata_at_checkpoint_boundary():
    class FakeSession:
        def scalar(self, _query):
            return None

        def add(self, value):
            self.added = value

        def commit(self):
            return None

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = FakeSession()
    checkpoint = updater._checkpoint_event(
        run_id=uuid4(),
        batch_key="STATUS_RESOLUTION",
        status="IN_PROGRESS",
        metadata={"backoffSeconds": 30.0},
    )

    assert checkpoint.checkpoint_hash
    assert checkpoint.metadata_payload["backoffSeconds"] == 30.0
    assert checkpoint.metadata_payload["providerMetricsApplicability"] == "NOT_APPLICABLE"


def test_orchestration_failure_closes_running_run_and_is_idempotent():
    class FakeSession:
        def __init__(self, run):
            self.run = run
            self.commit_count = 0

        def rollback(self):
            return None

        def get(self, _model, _run_id):
            return self.run

        def commit(self):
            self.commit_count += 1

    run = SimpleNamespace(
        id=uuid4(),
        status="RUNNING",
        metadata_payload={"executionKey": "post-close:2026-09-30:FULL", "resumeCount": 2},
        completed_at=None,
        heartbeat_at=None,
        updated_at=None,
        provider_status="CONNECTING",
        freshness_state="UNKNOWN",
        failure_code=None,
        failure_message=None,
    )
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = FakeSession(run)
    updater.clock = lambda: datetime(2026, 10, 1, 1, 0, tzinfo=UTC)
    updater._active_failure_stage = "STATUS_RESOLUTION_CHECKPOINT_CANONICALIZATION"

    error = TypeError("unsupported canonical value: float")
    updater._close_orchestration_failure(run.id, error)
    updater._close_orchestration_failure(run.id, error)

    assert run.status == "FAILED"
    assert run.failure_code == "POST_CLOSE_CHECKPOINT_CANONICALIZATION_FAILED"
    assert run.provider_status == "ERROR"
    assert run.metadata_payload["orchestrationFailure"] == {
        "status": "FAILED",
        "failureClassification": "POST_CLOSE_ORCHESTRATION_FAILURE",
        "failureCode": "POST_CLOSE_CHECKPOINT_CANONICALIZATION_FAILED",
        "failureStage": "STATUS_RESOLUTION_CHECKPOINT_CANONICALIZATION",
        "exceptionClass": "TypeError",
        "exceptionMessage": "unsupported canonical value: float",
        "runId": str(run.id),
        "previousState": "RUNNING",
        "resumeCount": 2,
        "retryReentryEligibility": "OWNER_REAUTH_REQUIRED",
        "operatorActionRequired": True,
    }
    assert run.metadata_payload["reentryContract"]["eligible"] is False
    assert updater.session.commit_count == 1


def test_run_wrapper_closes_exception_after_run_resume_claim():
    class FakeSession:
        def __init__(self, run):
            self.run = run

        def rollback(self):
            return None

        def get(self, _model, _run_id):
            return self.run

        def commit(self):
            return None

    run = SimpleNamespace(
        id=uuid4(),
        status="RUNNING",
        metadata_payload={"executionKey": "post-close:2026-09-30:FULL"},
        completed_at=None,
        heartbeat_at=None,
        updated_at=None,
        provider_status="CONNECTING",
        freshness_state="UNKNOWN",
        failure_code=None,
        failure_message=None,
    )
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = FakeSession(run)
    updater.clock = lambda: datetime(2026, 10, 1, 1, 0, tzinfo=UTC)

    def fail_after_resume_claim(**_kwargs):
        updater._set_active_run(run.id, "RUN_RESUME")
        raise RuntimeError("resume commit boundary failed")

    updater._run_once = fail_after_resume_claim
    with pytest.raises(RuntimeError, match="resume commit boundary failed"):
        updater.run_once(run_date=date(2026, 9, 30), execution_mode="RECOVERY")

    assert run.status == "FAILED"
    assert run.failure_code == "POST_CLOSE_RUN_RESUME_FAILED"
    assert run.metadata_payload["orchestrationFailure"]["previousState"] == "RUNNING"


def test_reentry_contract_blocks_missing_or_failed_recovery_authorization():
    assert (
        PostCloseUpdater._reentry_block_reason(
            {"executionKey": "key"},
            allow_terminal_recovery=True,
            execution_mode="RECOVERY",
        )
        == "POST_CLOSE_REENTRY_REQUIRES_OWNER_REAUTH"
    )
    assert (
        PostCloseUpdater._reentry_block_reason(
            {
                "executionKey": "key",
                "orchestrationFailure": {"failureCode": "POST_CLOSE_RUN_RESUME_FAILED"},
                "reentryContract": {
                    "status": "OWNER_REAUTH_REQUIRED",
                    "eligible": False,
                    "idempotencyKey": "key",
                },
            },
            allow_terminal_recovery=True,
            execution_mode="RECOVERY",
        )
        == "POST_CLOSE_REENTRY_REQUIRES_OWNER_REAUTH"
    )
    assert (
        PostCloseUpdater._reentry_block_reason(
            {
                "executionKey": "key",
                "reentryContract": {
                    "status": "OWNER_REAUTH_APPROVED",
                    "eligible": True,
                    "idempotencyKey": "key",
                },
            },
            allow_terminal_recovery=True,
            execution_mode="RECOVERY",
        )
        is None
    )


def test_status_resolution_result_is_carried_into_final_reconciliation_overlay(monkeypatch):
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = SimpleNamespace()
    updater.config = SimpleNamespace(
        status_resolution_max_attempts=1,
        status_resolution_max_total_wait_seconds=0,
        status_resolution_backoff_seconds=0,
    )
    updater.sleep = lambda _seconds: None
    updater._checkpoint_event = lambda **_kwargs: None
    monkeypatch.setattr(
        "topicpilot_api.live.post_close.read_effective_trading_status_authority",
        lambda *_args, **_kwargs: [
            {
                "instrumentId": "instrument-2601",
                "resolvedStatus": "SUSPENDED",
                "reasonCode": "CAPITAL_REDUCTION_TRADING_SUSPENSION",
                "authoritySource": "TWSE_OFFICIAL_REDUCTION",
                "sourceReference": "https://www.twse.com.tw/official",
                "effectiveFrom": date(2026, 9, 23),
                "effectiveTo": date(2026, 10, 3),
                "resolutionState": "RESOLVED",
                "blocksPublication": False,
                "isLegitimateUnavailable": True,
                "authorityClass": "CORPORATE_ACTION",
            }
        ],
    )

    bounded = updater._resolve_missing_statuses(
        run_id="run-1",
        trading_date=date(2026, 9, 30),
        candidates={"instrument-2601": True},
    )

    assert bounded.metrics.legitimate_unavailable_count == 1
    assert updater._status_resolution_by_instrument_id["instrument-2601"].status == "SUSPENDED"


def test_status_authority_is_reached_after_checkpoint_canonicalization(monkeypatch):
    class FakeSession:
        def scalar(self, _query):
            return None

        def add(self, value):
            self.added = value

        def commit(self):
            return None

    authority_calls = []
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = FakeSession()
    updater.config = SimpleNamespace(
        status_resolution_max_attempts=1,
        status_resolution_max_total_wait_seconds=0,
        status_resolution_backoff_seconds=30.0,
    )
    updater.sleep = lambda _seconds: None
    monkeypatch.setattr(
        "topicpilot_api.live.post_close.read_effective_trading_status_authority",
        lambda *_args, **_kwargs: authority_calls.append(True)
        or [
            {
                "instrumentId": "instrument-2601",
                "resolvedStatus": "SUSPENDED",
                "reasonCode": "CAPITAL_REDUCTION_TRADING_SUSPENSION",
                "authoritySource": "TWSE_OFFICIAL_REDUCTION",
                "sourceReference": "https://www.twse.com.tw/official",
                "effectiveFrom": date(2026, 9, 23),
                "effectiveTo": date(2026, 10, 3),
                "resolutionState": "RESOLVED",
                "blocksPublication": False,
                "isLegitimateUnavailable": True,
                "authorityClass": "CORPORATE_ACTION",
            }
        ],
    )

    bounded = updater._resolve_missing_statuses(
        run_id="run-1",
        trading_date=date(2026, 9, 30),
        candidates={"instrument-2601": True},
    )

    assert authority_calls == [True]
    assert bounded.metrics.legitimate_unavailable_count == 1
    assert updater.session.added.metadata_payload["checkpointSemantic"] == (
        "TRADING_STATUS_AUTHORITY_RESOLUTION"
    )
    assert (
        updater._status_resolution_by_instrument_id["instrument-2601"].authority_class
        == "CORPORATE_ACTION"
    )


def test_institutional_flow_readback_requires_both_same_date_official_markets():
    class Result:
        def __init__(self, rows):
            self.rows = rows

        def mappings(self):
            return self

        def all(self):
            return self.rows

    class FakeSession:
        def __init__(self, rows):
            self.rows = rows

        def execute(self, *_args, **_kwargs):
            return Result(self.rows)

    target = date(2026, 9, 3)
    rows = [
        {
            "market": "TPE",
            "trading_date": target,
            "availability": "AVAILABLE",
            "source_identity": "TWSE_BFI82U",
        },
        {
            "market": "TWO",
            "trading_date": target,
            "availability": "AVAILABLE",
            "source_identity": "TPEX_INSTI_SUMMARY",
        },
    ]
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = FakeSession(rows)

    assert updater._institutional_flow_readback(target)["status"] == "PASS"

    updater.session.rows = rows[:1]
    partial = updater._institutional_flow_readback(target)
    assert partial["status"] == "FAIL"
    assert partial["reasonCode"] == "WHOLE_MARKET_INSTITUTIONAL_FLOW_NOT_READY"


def test_formal_publication_readback_requires_published_home_and_flow():
    class Result:
        def mappings(self):
            return self

        def all(self):
            return [
                {
                    "market": "TPE",
                    "trading_date": date(2026, 9, 3),
                    "availability": "AVAILABLE",
                    "source_identity": "TWSE_BFI82U",
                },
                {
                    "market": "TWO",
                    "trading_date": date(2026, 9, 3),
                    "availability": "AVAILABLE",
                    "source_identity": "TPEX_INSTI_SUMMARY",
                },
            ]

    class FakeSession:
        def __init__(self):
            self.home = SimpleNamespace(
                id=uuid4(),
                publication_state="PUBLISHED",
            )

        def scalar(self, _query):
            return self.home

        def execute(self, *_args, **_kwargs):
            return Result()

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = FakeSession()
    updater._formal_snapshot_readback = lambda _date: {
        "status": "PASS",
        "rowCount": 2,
    }

    assert updater._formal_publication_readback(
        date(2026, 9, 3), run_id="run-1"
    )["status"] == "PASS"

    updater.session.home.publication_state = "UNAVAILABLE"
    assert updater._formal_publication_readback(
        date(2026, 9, 3), run_id="run-1"
    )["status"] == "FAIL"


def test_official_flow_persistence_skips_a_second_write_after_readback(monkeypatch):
    calls = []

    class FakeSession:
        commits = 0

        def commit(self):
            self.commits += 1

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = FakeSession()
    updater._now = lambda: datetime(2026, 9, 3, 8, 0, tzinfo=UTC)
    monkeypatch.setattr(
        "topicpilot_api.live.post_close.persist_market_institutional_flows",
        lambda *_args, **_kwargs: calls.append("persist")
        or {"status": "SUCCESS", "persisted": 2, "available": 2},
    )

    facts = (SimpleNamespace(market="TPE"), SimpleNamespace(market="TWO"))
    first = updater._persist_official_institutional_flow(
        facts,
        existing_readback={"status": "FAIL"},
    )
    second = updater._persist_official_institutional_flow(
        facts,
        existing_readback={"status": "PASS", "availableMarkets": ["TPE", "TWO"]},
    )

    assert first["status"] == "SUCCESS"
    assert second["status"] == "IDEMPOTENT_READBACK"
    assert calls == ["persist"]
    assert updater.session.commits == 1


def test_publication_readback_reuses_committed_output_after_checkpoint_interrupt(monkeypatch):
    monkeypatch.setattr(
        "topicpilot_api.live.post_close.reconcile_daily_market",
        lambda *_args, **_kwargs: SimpleNamespace(
            downstream_ready=True,
            reason_codes=(),
        ),
    )
    captured: dict[str, object] = {}
    snapshot = {
        "snapshotDate": "2026-09-03",
        "topicCount": 2,
        "status": "SUCCESS",
        "formalTopicDailyState": {"status": "SUCCESS"},
        "formalTopicSnapshotReadback": {"status": "PASS"},
    }

    class FakeSession:
        def get(self, _model, _run_id):
            return SimpleNamespace(metadata_payload={"topicSnapshot": snapshot})

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = FakeSession()
    updater._refresh_tracking_universe_with_retry = lambda **_kwargs: 0
    updater._now = lambda: datetime(2026, 9, 3, 8, 0, tzinfo=UTC)
    updater._latest_checkpoint = lambda _run_id, key: (
        SimpleNamespace(status="IN_PROGRESS")
        if key == "A9_B2_FORMAL_PROCESSING"
        else None
    )
    updater._formal_publication_readback = lambda *_args, **_kwargs: {
        "status": "PASS",
        "topicSnapshot": {"status": "PASS", "rowCount": 2},
        "homePublication": {"status": "PASS"},
    }
    updater._finish_with_retry = lambda _run_id, **values: captured.update(values)
    updater._ensure_completed_checkpoint = lambda **kwargs: captured.setdefault(
        "completed_checkpoints", []
    ).append(kwargs)
    updater._checkpoint_event = lambda **kwargs: captured.setdefault(
        "events", []
    ).append(kwargs)

    def should_not_republish(*_args, **_kwargs):
        raise AssertionError("formal writer was re-entered after a passing readback")

    updater._run_snapshot = should_not_republish
    result = updater._finalize_collected_run(
        run_id="run-1",
        local_date=date(2026, 9, 3),
        eligible_instrument_ids=(uuid4(),),
        success_count=1,
        failure_count=0,
        skipped_count=0,
        retry_count=0,
        point_count=1,
        failure_codes=(),
    )

    assert result.status == "SUCCESS"
    assert captured["snapshot_result"]["formalPublicationReadback"]["status"] == "PASS"


def test_completed_checkpoint_with_missing_publication_fails_closed(monkeypatch):
    monkeypatch.setattr(
        "topicpilot_api.live.post_close.reconcile_daily_market",
        lambda *_args, **_kwargs: SimpleNamespace(
            downstream_ready=True,
            reason_codes=(),
        ),
    )
    captured: dict[str, object] = {}
    readbacks = iter(
        [
            {
                "status": "FAIL",
                "topicSnapshot": {"status": "FAIL", "rowCount": 0},
                "homePublication": {"status": "NOT_FOUND"},
            },
            {
                "status": "FAIL",
                "topicSnapshot": {"status": "FAIL", "rowCount": 0},
                "homePublication": {"status": "NOT_FOUND"},
            },
        ]
    )

    class FakeSession:
        def get(self, _model, _run_id):
            return SimpleNamespace(metadata_payload={})

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = FakeSession()
    updater._refresh_tracking_universe_with_retry = lambda **_kwargs: 0
    updater._now = lambda: datetime(2026, 9, 3, 8, 0, tzinfo=UTC)
    updater._latest_checkpoint = lambda _run_id, key: (
        SimpleNamespace(status="COMPLETED")
        if key == "A9_B2_FORMAL_PROCESSING"
        else None
    )
    updater._formal_publication_readback = lambda *_args, **_kwargs: next(readbacks)
    updater._run_snapshot = lambda *_args, **_kwargs: {
        "snapshotDate": "2026-09-03",
        "topicCount": 0,
        "status": "SUCCESS",
        "formalTopicDailyState": {"status": "SUCCESS"},
        "formalTopicSnapshotReadback": {"status": "FAIL"},
    }
    updater._finish_with_retry = lambda _run_id, **values: captured.update(values)
    updater._checkpoint_event = lambda **kwargs: captured.setdefault(
        "events", []
    ).append(kwargs)
    updater._ensure_completed_checkpoint = lambda **_kwargs: None

    result = updater._finalize_collected_run(
        run_id="run-2",
        local_date=date(2026, 9, 3),
        eligible_instrument_ids=(uuid4(),),
        success_count=1,
        failure_count=0,
        skipped_count=0,
        retry_count=0,
        point_count=1,
        failure_codes=(),
    )

    assert result.status == "PARTIAL"
    assert "FORMAL_TOPIC_SNAPSHOT_NOT_READY" in result.failure_codes
    assert any(
        event.get("metadata", {}).get("errorCode") == "CHECKPOINT_PUBLICATION_MISMATCH"
        for event in captured["events"]
    )

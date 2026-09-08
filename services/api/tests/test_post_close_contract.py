from __future__ import annotations

import argparse
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from topicpilot_api.live.cli import _symbols_argument, build_parser
from topicpilot_api.live.post_close import (
    PostClosePreconditionError,
    PostCloseUpdater,
    _json_safe,
)
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


def test_post_close_materializes_formal_pit_state_before_shadow_lifecycle():
    source = (
        Path(__file__).parents[1] / "src/topicpilot_api/live/post_close.py"
    ).read_text(encoding="utf-8")

    assert "materialize_bounded_formal_dates" in source
    assert 'dates=(snapshot_date,)' in source
    assert "TopicLifecycleEngine(self.session).run_once" in source
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
